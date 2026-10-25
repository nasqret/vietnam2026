"""Real CPU-only public-worker integration; no model inference or live server."""
import hashlib
import json
from pathlib import Path
import sys
import threading
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import server
import sequential_runtime
from sequential_native import NativeHost
from sequential_runner import compact_prompt, run, MAX_RESULT_BYTES


class ScriptedPolicy:
    """Explicit test double. Counts are fixtures, never model-quality evidence."""
    identity = {"kind": "scripted_test_double"}
    policy = None
    prompt_renderer = staticmethod(compact_prompt)

    def provider_factory(self, **_limits):
        class Step:
            def propose(self, goals, *, max_candidates):
                self.prompt = compact_prompt(goals)
                return ("refl",)

            def report(self):
                return {"actual_model_calls": 1, "generated_token_slots": 2,
                        "attempts": [{"prompt_sha256": hashlib.sha256(self.prompt.encode()).hexdigest()}]}
        return Step()

    def finalize(self):
        return {"model_loaded": False, "forward_passes": 0, "attempts": []}


class PublicTests(unittest.TestCase):
    def test_public_manual_extended_input_and_false_control(self):
        theorem = "".join(f"forall v{i}. " for i in range(20)) + "v0 = v0"
        actions = [f"intro v{i}" for i in range(20)] + ["refl"]
        cases = [(theorem, actions, True), ("0=1", ["refl"], False)]
        for formula, script, expect_proof in cases:
            execution = server.run_worker("replay", {"theorem": formula, "tactics": script,
                "proof_profile": "sequential"}, threading.Event(), lambda _event: None)
            self.assertIsNone(execution["error"], execution)
            self.assertTrue(execution["quiescent"])
            self.assertEqual(execution["worker_exit_code"], 0)
            result = execution["result"]
            self.assertIs(result["kernel_checked"], expect_proof)
            self.assertFalse(result["model_used"])
            self.assertEqual(result["original_theorem"], formula)
            if expect_proof:
                self.assertEqual(result["native_admission"]["ast_metrics"]["maximum_bound_variables"], 20)
                self.assertEqual(result["tactics_applied"], 21)
                self.assertTrue(result["trace"][-1]["qed"])
            else:
                self.assertEqual(result["status"], "tactic_error")
                self.assertEqual(result["tactics_applied"], 0)

    def test_rejected_native_action_is_not_proof_provenance(self):
        with patch.object(sequential_runtime, "create_policy", return_value=ScriptedPolicy()):
            result = sequential_runtime.run_search({"theorem": "0=1", "model_id": "hydra-mixed",
                "max_model_calls": 32}, lambda _event: None)
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["proof_sources"], {})
        self.assertEqual(result["search"]["provenance"], [])
        self.assertEqual(result["search"]["accepted_model_steps"], 0)
        self.assertEqual(result["search"]["tactic_attempts"], 1)
        self.assertEqual(result["search"]["stop_reason"], "tactic_error")

    def test_oversized_result_keeps_bounded_accounting_without_proof_claim(self):
        policy = ScriptedPolicy()
        factory = policy.provider_factory
        def oversized_factory(**limits):
            step = factory(**limits)
            report = step.report
            step.report = lambda: {**report(), "fixture_padding": "x" * (MAX_RESULT_BYTES + 1)}
            return step
        result = run("0=0", native=NativeHost(server.worker.SOURCE), provider_factory=oversized_factory)
        self.assertEqual(result["status"], "result_limit")
        self.assertFalse(result["proved"])
        self.assertEqual(result["actions"], ["refl"])
        self.assertEqual(len(result["steps"]), 1)
        self.assertEqual(result["actual_model_calls"], 1)
        self.assertLess(len(json.dumps(result).encode()), MAX_RESULT_BYTES)


if __name__ == "__main__":
    unittest.main()
