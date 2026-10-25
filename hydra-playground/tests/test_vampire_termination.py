"""Partial transport cannot override an authoritative failure with stdout.

Only synthetic transport/export values are used: no kernel import, native
proof job, solver, model, HTTP request or process is launched.
"""
import hashlib
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import vampire_bridge as bridge
from vampire_limits import RUNTIME_POLICY, solver_args, solver_limits

TEXT = "fof(hydra_goal,conjecture,(hydra_zero = hydra_zero)).\n"
PROBLEM = bridge.ExportedProblem(TEXT, hashlib.sha256(TEXT.encode()).hexdigest(), (), None, (), 1)
APPARENT_PROOF = ("% SZS status Theorem for fixture\n% SZS output start Proof for fixture\n"
                  "fof(last,plain,($false),introduced(test_only)).\n% SZS output end Proof for fixture\n")


class FixedTransport:
    profile = "research"

    def __init__(self, **changes):
        self.calls = 0
        self.changes = changes

    def __call__(self, text):
        self.calls += 1
        return {"available": True, "executed": True, "status": "failed", "exit_code": -9,
                "stdout": "", "stderr": "", "profile": self.profile,
                "runtime_policy": RUNTIME_POLICY, "solver_args": solver_args(self.profile),
                "limits": solver_limits(self.profile), "binary_sha256": "a" * 64,
                "problem_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "termination": {"reason": "owned_child_rss_accounting_error"}, **self.changes}


class AuthoritativeTerminationTests(unittest.TestCase):
    def check_failed(self, **changes):
        runner = FixedTransport(**changes)
        advisor = bridge.VampireAdvisor(runner)
        with patch.object(bridge, "export_state", return_value=PROBLEM), \
                patch.object(bridge, "_native_hints", side_effect=AssertionError("Partial output reached native hints")):
            first, second = advisor.advise(None), advisor.advise(None)
        for result in (first, second):
            self.assertEqual(result["status"], "solver_error")
            self.assertEqual(result["solver"]["status"], "failed")
            self.assertFalse(result["solver"]["timed_out"])
            self.assertFalse(result["solver"]["resource_limited"])
            self.assertEqual(result["solver"]["termination"]["classification_source"], "runner")
            self.assertEqual(result["solver"]["termination"]["reason"], "owned_child_rss_accounting_error")
            self.assertEqual(result["solver"]["invocations"], 1)
            self.assertEqual(result["suggestions"], [])
            self.assertFalse(result["kernel_checked"])
            self.assertFalse(result["cache"]["stored"])
            self.assertFalse(result["cache"]["hit"])
        self.assertEqual(advisor.report()["actual_invocations"], runner.calls)
        self.assertEqual(runner.calls, 2)
        self.assertEqual(advisor.report()["entries"], 0)
        return first

    def test_accounting_failure_overrides_partial_timeout_markers(self):
        for text in ("% Time limit reached!\n", "% SZS status Timeout for fixture\n"):
            with self.subTest(text=text):
                result = self.check_failed(stdout=text, timed_out=True)
                self.assertEqual(result["solver"]["termination"]["output_status"], "timeout")
                self.assertTrue(result["solver"]["termination"]["evidence"])

    def test_failure_and_partial_status_override_apparent_proofs_or_resource_markers(self):
        for status in ("failed", "partial", "incomplete"):
            for text in (APPARENT_PROOF, "% SZS status MemoryOut for fixture\n"):
                with self.subTest(status=status, text=text[:60]):
                    self.check_failed(status=status, stdout=text, exit_code=0)

    def test_output_status_flag_or_capture_limit_rejects_apparent_proof(self):
        for changes in ({"status": "output_limit", "output_limited": False},
                        {"status": "completed", "output_limited": True},
                        {"status": "completed", "stdout": APPARENT_PROOF + "x" * bridge.MAX_OUTPUT_BYTES}):
            with self.subTest(keys=list(changes)):
                runner = FixedTransport(**{"stdout": APPARENT_PROOF, "timed_out": True, "exit_code": 0, **changes})
                advisor = bridge.VampireAdvisor(runner)
                with patch.object(bridge, "export_state", return_value=PROBLEM), \
                        patch.object(bridge, "_native_hints", side_effect=AssertionError("Limited output reached native hints")):
                    result = advisor.advise(None)
                self.assertEqual(result["status"], "output_limit")
                self.assertEqual(result["solver"]["status"], "output_limit")
                self.assertFalse(result["solver"]["timed_out"])
                self.assertFalse(result["cache"]["stored"])
                self.assertEqual(result["suggestions"], [])
                self.assertEqual(result["solver"]["invocations"], runner.calls)
                self.assertFalse(result["kernel_checked"])

    def test_genuine_runner_timeout_keeps_evidence_and_cache_admission(self):
        runner = FixedTransport(status="timeout", stdout="% Time limit reached!\n", exit_code=1,
                                termination={"reason": "solver_time_limit"})
        advisor = bridge.VampireAdvisor(runner)
        with patch.object(bridge, "export_state", return_value=PROBLEM):
            first, second = advisor.advise(None), advisor.advise(None)
        self.assertEqual(first["status"], "timeout")
        self.assertTrue(first["solver"]["timed_out"])
        self.assertEqual(first["solver"]["termination"]["reason"], "solver_time_limit")
        self.assertEqual(second["status"], "cached_unsuccessful")
        self.assertEqual(second["solver"]["invocations"], 0)
        self.assertEqual(advisor.report()["actual_invocations"], runner.calls)
        self.assertEqual(runner.calls, 1)


if __name__ == "__main__":
    unittest.main()
