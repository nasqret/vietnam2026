"""Focused source/metadata/accounting tests. No MLX/model/native execution."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import model_selection as selection
import wmi_model_runtime as runtime
from wmi_mlx_loader import MLXVanillaBackend


class FakeCore:
    """Accounting fixture only; numbers are fixture values, not model work."""
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.evaluation_identity = {}
        self._report = {"actual_model_calls": 0, "forward_attempts": 0, "forward_passes": 0,
                        "generated_token_slots": 0, "attempts": []}

    def propose(self, goals, *, max_candidates):
        prompt = runtime.prompt_renderer(goals)
        self._report = {"actual_model_calls": 1, "forward_attempts": 3, "forward_passes": 3,
            "generated_token_slots": 3, "attempts": [{"prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                "status": "suggested", "action": "intro v100"}]}
        return ("intro v100",)

    def report(self):
        return copy.deepcopy(self._report)


def prepared():
    owner = runtime.WMIModelPolicy(SimpleNamespace(allowed_commands=frozenset(), allowed_theorems=frozenset()))
    owner.policy = SimpleNamespace(backend=object(), tokenizer=object(), kind="latent_compact_v3",
        environment=object(), provenance={}, render_prompt=runtime.prompt_renderer, strict_generation=object(),
        check_prompt_binding=object(), validate_tactic=object(), constraint_factory=None, finalize=lambda: {})
    return owner


class MetadataAndLifecycle(unittest.TestCase):
    def test_default_and_explicit_selection(self):
        self.assertEqual(selection.resolve_model_id(), "hydra-mixed")
        self.assertEqual(selection.resolve_model_id("wmi-c6-vanilla47"), "wmi-c6-vanilla47")
        for value in ("auto", "", False, "unknown"):
            with self.assertRaises(ValueError):
                selection.resolve_model_id(value)

    def test_constructor_and_selector_never_load_frameworks(self):
        caps = SimpleNamespace()
        self.assertIsInstance(selection.create_sequential_policy("hydra-mixed", caps, lambda e: None), runtime.HistoricalGreedyPolicy)
        self.assertIsInstance(selection.create_sequential_policy("wmi-c6-vanilla47", caps, lambda e: None), runtime.WMIModelPolicy)
        self.assertFalse(any(name == "mlx" or name.startswith("mlx.") or name in {"torch", "transformers"} for name in sys.modules))

    def test_actual_export_configuration_and_header_only(self):
        spec = runtime.candidate_spec()
        self.assertEqual(spec.export_bytes, 139520392)
        with patch.object(runtime.trained, "metadata_status", return_value={"available": True, "detail": "fixture base status"}):
            status = runtime.metadata_status()
        self.assertTrue(status["available"], status)
        self.assertFalse(status["loaded"])
        self.assertFalse(status["automatic_fallback"])
        self.assertIn("metadata only", status["byte_authentication"])

    def test_missing_candidate_does_not_claim_fallback_or_availability(self):
        with patch.object(runtime.trained, "metadata_status", return_value={"available": True, "detail": "fixture"}), \
             patch.object(runtime, "EXPORT", runtime.ROOT / "missing-wmi-fixture.safetensors"):
            status = selection.metadata_status("wmi-c6-vanilla47")
        self.assertFalse(status["available"])
        self.assertEqual(status["selection_id"], "wmi-c6-vanilla47")
        self.assertFalse(status["automatic_fallback"])

    def test_failed_initialization_is_never_retried(self):
        owner = runtime.WMIModelPolicy(SimpleNamespace())
        with patch.object(runtime, "_frozen_helpers", return_value=(object(), object(), {})), \
             patch.object(runtime, "load_local_policy", side_effect=ValueError("fixture load failure")) as load:
            with self.assertRaisesRegex(ValueError, "fixture load failure"):
                owner.propose(("⊢ 0 = 0",), max_candidates=1)
            with self.assertRaisesRegex(RuntimeError, "no automatic reload"):
                owner.propose(("⊢ 0 = 0",), max_candidates=1)
        self.assertEqual(load.call_count, 1)
        self.assertEqual(owner.calls, 0)

    def test_expired_deadline_does_not_load(self):
        owner = runtime.WMIModelPolicy(SimpleNamespace(), deadline_monotonic=time.monotonic() - 1)
        with patch.object(owner, "_prepare") as load:
            with self.assertRaises(TimeoutError):
                owner.propose(("⊢ 0 = 0",), max_candidates=1)
        load.assert_not_called()

    def test_shared_model_has_fresh_case_counters_and_exact_all_goals(self):
        owner = prepared()
        case = owner.new_case(deadline_monotonic=time.monotonic() + 300)
        self.assertIs(case.policy, owner.policy)
        goals = ("h : 0 = 0 ⊢ ?t2 = 0", "⊢ 1 = 1")
        with patch.object(runtime, "CandidatePolicy", FakeCore):
            for _ in range(2):
                step = case.provider_factory(deadline=time.monotonic() + 300, max_new_tokens=128, max_context_tokens=6144)
                self.assertEqual(step.propose(goals, max_candidates=1), ("intro v100",))
                self.assertEqual(step.report()["actual_model_calls"], 1)
                with self.assertRaisesRegex(ValueError, "cannot be reused"):
                    step.propose(goals, max_candidates=1)
        self.assertEqual(case.calls, 2)
        self.assertEqual(case.generated_tokens, 6)
        self.assertEqual(owner.calls, 0)
        self.assertEqual(case.finalize()["proposals"], [{"tactic": "intro v100"}] * 2)
        expected = hashlib.sha256(runtime.prompt_renderer(goals).encode()).hexdigest()
        self.assertEqual(case.report()["attempts"][0]["prompt_sha256"], expected)

    def test_global_budget_cannot_reset_through_new_step(self):
        owner = prepared()
        case = owner.new_case(deadline_monotonic=time.monotonic() + 300, max_calls=1)
        with patch.object(runtime, "CandidatePolicy", FakeCore):
            case.propose(("⊢ 0 = 0",), max_candidates=1)
            with self.assertRaisesRegex(ValueError, "model-call budget exhausted"):
                case.provider_factory(deadline=time.monotonic() + 300, max_new_tokens=128,
                    max_context_tokens=6144).propose(("⊢ 0 = 0",), max_candidates=1)
        self.assertEqual(case.calls, 1)

    def test_mask_contract_keeps_wmi_unmasked(self):
        wmi = MLXVanillaBackend(object(), object())
        old = MLXVanillaBackend(object(), object(), kind="historical_primitive_v4")
        for backend, mask in ((wmi, [1]), (old, None)):
            with self.assertRaisesRegex(ValueError, "authority mask"):
                backend.next_token([1], mask, forward_started=lambda: None, forward_completed=lambda: None)


if __name__ == "__main__":
    unittest.main()
