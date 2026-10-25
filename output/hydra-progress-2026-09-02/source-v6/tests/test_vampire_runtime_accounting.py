"""Pure report/accounting checks; no native search, model, solver or HTTP."""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
from hybrid_runtime import MAX_VAMPIRE_CACHE_REPORT_BYTES, vampire_cache_report


class VampireRuntimeAccountingTests(unittest.TestCase):
    def fixture(self):
        report = {"policy": "test-report", "actual_invocations": 2, "requests": 5, "cache_hits": 3,
                  "hit_records": [{"request": 3, "previous_request": 1}], "kernel_checked": False}
        return ({"vampire_calls": 2, "vampire_advisor_calls": 5},
                SimpleNamespace(report=lambda: report), SimpleNamespace(calls=2), report)

    def test_keeps_cache_hits_separate_and_returns_a_detached_report(self):
        result, advisor, runner, original = self.fixture()
        retained = vampire_cache_report(result, advisor, runner)
        self.assertEqual(retained, original)
        retained["hit_records"][0]["request"] = 100
        self.assertEqual(original["hit_records"][0]["request"], 3)
        self.assertEqual(retained["actual_invocations"], 2)
        self.assertEqual(retained["cache_hits"], 3)

    def test_no_advisor_requires_both_absent_and_explicit_zero_counters(self):
        self.assertIsNone(vampire_cache_report({"vampire_calls": 0, "vampire_advisor_calls": 0}, None, None))
        for result in ({}, {"vampire_calls": 0}, {"vampire_calls": False, "vampire_advisor_calls": 0},
                       {"vampire_calls": 0, "vampire_advisor_calls": 1}):
            with self.subTest(result=result), self.assertRaises(ValueError):
                vampire_cache_report(result, None, None)
        result, advisor, runner, _ = self.fixture()
        for components in ((advisor, None), (None, runner), (None, None)):
            with self.subTest(components=components), self.assertRaises(ValueError):
                vampire_cache_report(result, *components)

    def test_each_actual_request_and_hit_mismatch_is_rejected_not_coerced(self):
        for key, value in (("actual_invocations", 1), ("requests", 4), ("cache_hits", 4),
                           ("actual_invocations", True), ("requests", "5"), ("cache_hits", -1)):
            with self.subTest(key=key, value=value):
                result, advisor, runner, report = self.fixture()
                report[key] = value
                with self.assertRaises(ValueError):
                    vampire_cache_report(result, advisor, runner)
        result, advisor, runner, _ = self.fixture()
        runner.calls = 1
        with self.assertRaises(ValueError):
            vampire_cache_report(result, advisor, runner)
        runner.calls = 2
        for key in ("vampire_calls", "vampire_advisor_calls"):
            changed = deepcopy(result)
            changed[key] += 1
            with self.assertRaises(ValueError):
                vampire_cache_report(changed, advisor, runner)

    def test_malformed_unbounded_or_proof_claiming_reports_are_rejected(self):
        result, advisor, runner, report = self.fixture()
        original = deepcopy(report)
        for change in ({"kernel_checked": True}, {"detail": "x" * MAX_VAMPIRE_CACHE_REPORT_BYTES},
                       {"detail": float("nan")}):
            with self.subTest(keys=list(change)):
                report.clear()
                report.update(original | change)
                with self.assertRaises(ValueError):
                    vampire_cache_report(result, advisor, runner)
        for invalid in (None, [], "missing"):
            with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                vampire_cache_report(result, SimpleNamespace(report=lambda: invalid), runner)


if __name__ == "__main__":
    unittest.main()
