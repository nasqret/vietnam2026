"""The hybrid wrapper distinguishes attempted decoding from actual inference."""
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from hybrid_runtime import LazyModelPolicy


class ProviderFixture:
    def __init__(self, emit):
        self.emit = emit
        self.calls = self.forward_passes = self.generated_token_steps = 0
        self.proposals, self.rejections = [], []
        self.fail_before_forward = False
        self.fail_after_forward = False

    def propose(self, goals, *, max_candidates):
        self.calls += 1
        self.emit({"phase": "proposing", "model_calls": self.calls})
        if self.fail_before_forward:
            raise ValueError("fixture: prompt exceeds the token bound")
        self.forward_passes += 1
        self.generated_token_steps += 1
        self.emit({"phase": "decoding", "model_calls": self.calls})
        if self.fail_after_forward:
            raise ValueError("fixture: decoding stopped after an actual forward pass")
        return ("refl",)


class LazyAccountingTests(unittest.TestCase):
    def prepared(self):
        events = []
        wrapper = LazyModelPolicy(None, events.append)
        wrapper.load_attempted = True
        wrapper.policy = ProviderFixture(wrapper._policy_progress)
        return wrapper, events

    def test_prompt_preflight_failure_never_claims_inference(self):
        wrapper, events = self.prepared()
        wrapper.policy.fail_before_forward = True
        with self.assertRaises(ValueError):
            wrapper.propose(("a = a",), max_candidates=4)
        record = wrapper.finalize()
        self.assertEqual(record["model_calls"], 0)
        self.assertEqual(record["model_decode_attempts"], 1)
        self.assertEqual(record["forward_passes"], 0)
        self.assertFalse(wrapper.identity["used"])
        self.assertEqual(events[-1]["model_calls"], 0)
        self.assertEqual(events[-1]["model_decode_attempts"], 1)

    def test_only_actual_batches_count_after_an_earlier_prompt_rejection(self):
        wrapper, events = self.prepared()
        wrapper.policy.fail_before_forward = True
        with self.assertRaises(ValueError):
            wrapper.propose(("a = a",), max_candidates=4)
        wrapper.policy.fail_before_forward = False
        self.assertEqual(wrapper.propose(("a = a",), max_candidates=4), ("refl",))
        record = wrapper.finalize()
        self.assertEqual(record["model_calls"], 1)
        self.assertEqual(record["model_decode_attempts"], 2)
        self.assertTrue(wrapper.identity["used"])
        self.assertEqual(events[-1]["model_calls"], 1)

    def test_failure_after_inference_retains_actual_work_count(self):
        wrapper, events = self.prepared()
        wrapper.policy.fail_after_forward = True
        with self.assertRaises(ValueError):
            wrapper.propose(("a = a",), max_candidates=4)
        record = wrapper.finalize()
        self.assertEqual(record["model_calls"], 1)
        self.assertEqual(record["forward_passes"], 1)
        self.assertTrue(wrapper.identity["used"])
        self.assertEqual(events[-1]["model_calls"], 1)


if __name__ == "__main__":
    unittest.main()
