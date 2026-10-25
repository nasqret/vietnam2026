"""Scripted Transformers-4.53.3 callback fixtures: no tensors, weights or native engine.

The real beam API checks an overselected candidate pool before retaining its
live beams. These fixtures drive the real Hydra session with that API shape;
they do not claim to execute Transformers or evaluate a model.
Source: https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/generation/utils.py#L3998-L4003
Source: https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/generation/utils.py#L4144-L4151
"""
from contextlib import nullcontext
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import experimental_model as subject


class FakeTensor:
    def __init__(self, rows):
        self.rows = [list(row) for row in rows]
        self.shape = (len(rows), len(rows[0]))

    def tolist(self):
        return [list(row) for row in self.rows]


class ScriptedModel:
    """Only issue documented callback shapes and a constructed return value."""
    def __init__(self, *, iterations=3, callback_rows=None, returned_steps=None,
                 duplicate=False, mutate_prefix=False, before_observe=None):
        self.iterations, self.callback_rows = iterations, callback_rows
        self.returned_steps = returned_steps
        self.duplicate, self.mutate_prefix = duplicate, mutate_prefix
        self.before_observe = before_observe
        self.hook = None
        self.removed = 0
        self.kwargs = None

    def register_forward_pre_hook(self, callback):
        self.hook = callback
        def remove():
            self.removed += 1
            self.hook = None
        return SimpleNamespace(remove=remove)

    def generate(self, **kwargs):
        self.kwargs = kwargs
        config = kwargs["generation_config"]
        prefix = kwargs["input_ids"].tolist()[0]
        width = config.num_beams
        # Frozen API fixtures for batch_size=1 and one scalar EOS. These are
        # stopping candidates, not twice as many neural forward-pass beams.
        rows = {1: 1, 2: 4, 4: 8, 8: 16, 16: 32}[width] if self.callback_rows is None else self.callback_rows
        for index in range(1, self.iterations + 1):
            self.hook(self, ())  # synthetic forward invocation only
            if self.before_observe is not None:
                self.before_observe(index)
            observed = SimpleNamespace(shape=(rows, len(prefix) + index))
            for criterion in kwargs["stopping_criteria"]:
                criterion(observed, None)
                if self.duplicate:
                    criterion(observed, None)
        steps = self.iterations if self.returned_steps is None else self.returned_steps
        if self.mutate_prefix:
            prefix[0] += 1
        return FakeTensor([prefix + [42] * (steps - 1) + [151643] for _ in range(width)])


class DecoderAccountingTests(unittest.TestCase):
    def session(self, model, *, stop=lambda: False, tokens=4096):
        fake_torch = SimpleNamespace(long="synthetic-long", inference_mode=nullcontext,
            tensor=lambda rows, **_: FakeTensor(rows),
            ones_like=lambda tensor: FakeTensor([[1] * tensor.shape[1] for _ in range(tensor.shape[0])]))
        session = subject.TorchModelSession(subject._LOADED, model, SimpleNamespace(eos_token_id=151643),
            fake_torch, {"profile": subject.PROFILE}, subject.SessionLimits(max_calls=4, max_token_slots=tokens),
            lambda: None, stop)
        return session, SimpleNamespace(calls=0, generated_tokens=0)

    def invoke(self, session, tracker, *, width=4, maximum=64, primitive=True):
        transformers = ModuleType("transformers")
        transformers.GenerationConfig = lambda **kwargs: SimpleNamespace(**kwargs)
        transformers.StoppingCriteriaList = list
        processors = [object()]
        authority = SimpleNamespace(generation_constraints=Mock(return_value={"logits_processor": processors}))
        with patch.dict(sys.modules, {"transformers": transformers}), patch.object(subject, "_training", return_value=authority):
            output = session.generate((10, 20, 30), maximum=maximum, width=width,
                                      tracker=tracker, environment=object() if primitive else None)
        if primitive:
            authority.generation_constraints.assert_called_once()
            self.assertIs(session.model.kwargs["logits_processor"], processors)
        else:
            authority.generation_constraints.assert_not_called()
        return output

    def test_vectorized_beam_pool_is_not_double_charged(self):
        for width in (2, 4, 8, 16):
            with self.subTest(width=width):
                session, tracker = self.session(ScriptedModel(iterations=3))
                output = self.invoke(session, tracker, width=width)
                self.assertEqual(len(output), width)
                self.assertEqual(session.generated_tokens, width * 3)
                self.assertEqual(tracker.generated_tokens, width * 3)
                self.assertEqual(session.calls, 1)
                self.assertEqual(session.forward_passes, 3)
                report = session.report()["last_generation_accounting"]
                self.assertEqual(report["last_observed_rows"], 2 * width)
                self.assertEqual(report["expected_callback_rows"], 2 * width)
                self.assertEqual(report["observed_decode_iterations"], 3)
                self.assertEqual(report["generated_token_slots"], width * 3)

    def test_greedy_primitive_and_planner_still_count_one_row(self):
        for primitive, maximum in ((True, 64), (False, 512)):
            with self.subTest(primitive=primitive):
                session, tracker = self.session(ScriptedModel(iterations=2))
                output = self.invoke(session, tracker, width=1, maximum=maximum, primitive=primitive)
                self.assertEqual(output, ((42, 151643),))
                self.assertEqual(session.generated_tokens, 2)
                self.assertEqual(session.report()["last_generation_accounting"]["last_observed_rows"], 1)

    def test_duplicate_callback_does_not_double_charge_an_iteration(self):
        session, tracker = self.session(ScriptedModel(duplicate=True))
        self.invoke(session, tracker)
        self.assertEqual(session.generated_tokens, 12)
        self.assertEqual(session.forward_passes, 3)

    def test_finished_beam_output_length_is_not_the_work_counter(self):
        # Selected finished beams can come from an earlier iteration. The
        # remaining beam search still consumed the three documented forwards.
        session, tracker = self.session(ScriptedModel(iterations=3, returned_steps=1))
        output = self.invoke(session, tracker)
        self.assertEqual(output, ((151643,),) * 4)
        self.assertEqual(session.generated_tokens, 12)

    def test_greedy_return_cannot_hide_an_observed_token(self):
        session, tracker = self.session(ScriptedModel(iterations=3, returned_steps=1))
        with self.assertRaisesRegex(subject.ModelAdmissionError, "Greedy decode token accounting"):
            self.invoke(session, tracker, width=1)
        self.assertEqual(session.generated_tokens, 3)
        self.assertFalse(session._busy)
        self.assertEqual(session.model.removed, 1)

    def test_wrong_candidate_population_fails_and_retains_attempt_evidence(self):
        for wrong in (1, 3, 4, 7, 9, 16):
            with self.subTest(rows=wrong):
                session, tracker = self.session(ScriptedModel(callback_rows=wrong))
                with self.assertRaisesRegex(subject.ModelAdmissionError, "candidate population"):
                    self.invoke(session, tracker, width=4)
                self.assertEqual((session.calls, session.forward_passes, session.generated_tokens), (1, 1, 0))
                self.assertEqual(session.last_generation_accounting["last_observed_rows"], wrong)
                self.assertFalse(session._busy)
                self.assertEqual(session.model.removed, 1)

    def test_cancel_after_observed_step_keeps_width_slots_and_removes_hook(self):
        cancelled = [False]
        model = ScriptedModel(before_observe=lambda index: cancelled.__setitem__(0, index == 1))
        session, tracker = self.session(model, stop=lambda: cancelled[0])
        with self.assertRaises(subject.ExperimentalCancelled):
            self.invoke(session, tracker)
        self.assertEqual((session.calls, session.forward_passes, session.generated_tokens), (1, 1, 4))
        self.assertEqual((tracker.calls, tracker.generated_tokens), (1, 4))
        self.assertEqual(session.last_generation_accounting["observed_decode_iterations"], 1)
        self.assertFalse(session._busy)
        self.assertEqual(model.removed, 1)

    def test_fixed_generation_config_and_native_mask_contract_are_unchanged(self):
        session, tracker = self.session(ScriptedModel())
        self.invoke(session, tracker)
        config = session.model.kwargs["generation_config"]
        self.assertEqual((config.num_beams, config.num_return_sequences, config.max_new_tokens), (4, 4, 64))
        self.assertEqual((config.bos_token_id, config.eos_token_id, config.pad_token_id), (151643,) * 3)
        self.assertFalse(config.do_sample)
        self.assertTrue(config.early_stopping)
        self.assertEqual(config.length_penalty, 1.0)
        self.assertEqual(subject.PRIMITIVE_DECODER, "hydra-experimental-torch-authority-primitive-v1")
        self.assertEqual(subject.PROFILE, "hydra-experimental-torch-qwen3-v2")
        self.assertEqual(session.report()["generation_accounting"], "hydra-transformers-4.53.3-beam-slots-v2")

    def test_prefix_tampering_still_rejects_after_accounting_for_work(self):
        session, tracker = self.session(ScriptedModel(mutate_prefix=True))
        with self.assertRaisesRegex(subject.ModelAdmissionError, "full input prefix"):
            self.invoke(session, tracker)
        self.assertEqual(session.generated_tokens, 12)
        self.assertEqual(session.model.removed, 1)

    def test_total_token_budget_is_unchanged_and_checked_before_dispatch(self):
        session, tracker = self.session(ScriptedModel(), tokens=255)
        with self.assertRaisesRegex(subject.ModelAdmissionError, "budget exhausted"):
            self.invoke(session, tracker, width=4, maximum=64)
        self.assertEqual((session.calls, session.generated_tokens, session.forward_passes), (0, 0, 0))
        self.assertIsNone(session.model.kwargs)

    def test_ledger_bounds_and_backwards_lengths_are_still_rejected(self):
        total = []
        ledger = subject._GenerationLedger(3, 4, 64, total.append, lambda: False)
        ledger.observe(8, 67)
        self.assertEqual(sum(total), 256)
        for rows, columns in ((8, 68), (8, 66), (True, 67), (8, True), (4, 67)):
            with self.subTest(rows=rows, columns=columns), self.assertRaises(subject.ModelAdmissionError):
                ledger.observe(rows, columns)
        self.assertEqual(sum(total), 256)
        for prompt, width, maximum in ((0, 4, 64), (4097, 4, 64), (3, 17, 64), (3, True, 64), (3, 4, 513)):
            with self.subTest(prompt=prompt, width=width, maximum=maximum), self.assertRaises(subject.ModelAdmissionError):
                subject._GenerationLedger(prompt, width, maximum, total.append, lambda: False)

    def test_no_silent_acceptance_of_an_unexpected_tensor_rank(self):
        ledger = subject._GenerationLedger(3, 4, 64, lambda count: None, lambda: False)
        for shape in ((8,), (1, 8, 4)):
            with self.subTest(shape=shape), self.assertRaisesRegex(subject.ModelAdmissionError, "two-dimensional"):
                ledger(SimpleNamespace(shape=shape), None)


if __name__ == "__main__":
    unittest.main()
