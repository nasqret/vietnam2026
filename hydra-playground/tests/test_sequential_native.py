"""Small real native tests, no model/solver/network inference.

Run in a fresh process: python3 -I -B tests/test_sequential_native.py.
Scripted providers below are explicit test doubles, never quality evidence.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from sequential_native import NativeHost, NativeLimits, NativeAdmissionError, NativeBudgetExceeded, authorized_spawn
from sequential_runner import Limits, compact_prompt, run, validate_native_receipt

SOURCE = APP.parent / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"


def deadline():
    return time.monotonic() + 20


class NativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.host = NativeHost(SOURCE)

    def test_large_bounded_input_and_fresh_replay(self):
        theorem = "".join(f"forall v{i}. " for i in range(20)) + "v0 = v0"
        admission = self.host.admit(theorem, deadline=deadline())
        self.assertEqual(admission["ast_metrics"]["maximum_bound_variables"], 20)
        actions = [f"intro v{i}" for i in range(20)] + ["refl"]
        native = self.host.run_prefix(admission["theorem"], actions, deadline=deadline())
        replay = self.host.independent_replay(admission["theorem"], actions, deadline=deadline())
        self.assertTrue(native["kernel_checked"] and replay["kernel_checked"])
        self.assertEqual(native["proof_nodes"], replay["proof_nodes"])
        self.assertNotEqual(self.host.last_replay_evidence["child_process_id"], os.getpid())
        self.assertEqual(self.host.last_replay_evidence["actual_exit_code"], 0)

    def test_all_goals_and_persistent_meta_names(self):
        theorem = self.host.admit("forall x. (forall y. y=x -> 0=0) -> (0=0 /\\ 0=0)", deadline=deadline())["theorem"]
        prefix = ["intro v100", "intro h100", "split", "apply h100"]
        first = self.host.run_prefix(theorem, prefix, deadline=deadline())
        self.assertEqual(len(first["goals"]), 2)
        self.assertIn("?t1", first["goals"][0])
        second = self.host.run_prefix(theorem, prefix + ["refl", "apply h100"], deadline=deadline())
        self.assertEqual(second["goals"], [x for x in second["trace"] if "v" in x][-1]["goals_after"])
        self.assertIn("?t2", second["goals"][0])
        completed = self.host.run_prefix(theorem, prefix + ["refl", "apply h100", "refl"], deadline=deadline())
        self.assertTrue(completed["kernel_checked"])

    def test_false_forbidden_and_invalid_inputs(self):
        for theorem, actions in [("0=1", ["refl"]), ("0=0", ["use add_assoc"])]:
            result = self.host.run_prefix(theorem, actions, deadline=deadline())
            self.assertFalse(result["kernel_checked"])
            self.assertEqual(result["status"], "tactic_error")
        for theorem in ["x=x", "0 == 0", "65=65", "".join(f"forall v{i}. " for i in range(65)) + "0=0"]:
            with self.subTest(theorem=theorem[:50]), self.assertRaises(NativeAdmissionError):
                self.host.admit(theorem, deadline=deadline())

    def test_initial_never_claims_qed(self):
        result = self.host.initial_result("0=0", deadline=deadline())
        self.assertEqual(result["trace"], [])
        self.assertFalse(result["kernel_checked"])
        self.assertEqual(result["tactics_applied"], 0)
        self.assertEqual(result["status"], "open")

    def test_expired_budget_and_child_hard_timeout(self):
        with self.assertRaises(NativeBudgetExceeded):
            self.host.run_prefix("0=0", ["refl"], deadline=time.monotonic() - 1)
        limited = NativeHost(SOURCE, limits=NativeLimits(native_call_seconds=0.001))
        with self.assertRaises(NativeBudgetExceeded):
            limited.independent_replay("0=0", ["refl"], deadline=deadline())
        self.assertEqual(limited.last_replay_evidence["status"], "timeout")
        self.assertFalse(authorized_spawn(sys.executable, [sys.executable, "-c", "print(1)"], None, None))

    def test_independent_transition_mismatch_is_rejected(self):
        theorem = self.host.admit("0=0", deadline=deadline())["theorem"]
        receipt = self.host.run_prefix(theorem, ["refl"], deadline=deadline())
        previous = [x for x in receipt["trace"] if "v" in x]
        bad = copy.deepcopy(receipt)
        bad["trace"][0]["goals_before"] = ["⊢ 0 = 1"]
        with self.assertRaisesRegex(ValueError, "previously accepted"):
            validate_native_receipt(bad, theorem=theorem, actions=["refl"],
                expected_before=tuple(previous[0]["goals_before"]), previous=previous,
                identity=self.host.identity, success_label=self.host.success_label)

    def test_runner_proof_gate_and_action_budget(self):
        def scripted(actions):
            pending = iter(actions)

            def factory(**_limits):
                action = next(pending)

                class TestProvider:
                    def propose(self, goals, *, max_candidates):
                        self.prompt = compact_prompt(goals)
                        return (action,)

                    def report(self):
                        # Test-double counters only: no genuine model is loaded.
                        return {"actual_model_calls": 1, "generated_token_slots": 2,
                                "forward_attempts": 2, "forward_passes": 2,
                                "attempts": [{"prompt_sha256": hashlib.sha256(self.prompt.encode()).hexdigest()}]}
                return TestProvider()
            return factory

        result = run("0=0 /\\ 1=1", native=self.host, provider_factory=scripted(["split", "refl", "refl"]))
        self.assertTrue(result["proved"])
        self.assertTrue(result["independent_replay"]["kernel_checked"])
        self.assertEqual(result["last_native_result"]["proof_nodes"], result["certificate_nodes"])
        self.assertEqual(result["actual_model_calls"], 3)
        limited = run("0=0 /\\ 1=1", native=self.host, provider_factory=scripted(["split"]), limits=Limits(max_actions=1))
        self.assertEqual(limited["status"], "action_budget")
        self.assertFalse(limited["proved"])
        self.assertEqual(len(limited["remaining_goals"]), 2)

    def test_z_worker_audit_guard_allows_only_native_replay(self):
        import subprocess
        import worker
        worker.install_guard("replay", allow_sequential=True)
        with self.assertRaises(RuntimeError):
            subprocess.run([sys.executable, "-c", "print('not authorized')"], check=False)
        result = self.host.independent_replay("0=0", ["refl"], deadline=deadline())
        self.assertTrue(result["kernel_checked"])


if __name__ == "__main__":
    unittest.main()
