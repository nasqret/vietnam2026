"""Pure sacct/parser and completion-gate regressions; no study execution."""
from __future__ import annotations

import argparse
import ast
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / "output/hydra-implementation-2026-09-04"
FROZEN = BASE / "combined-source-bundle-02/source/output/hydra-implementation-2026-09-04/paired-evaluation-v2"
RAW_PATH = BASE / "paired-launchers-v4/prepared/arms/symbolic/observation-003/sacct.txt"
DENIED = []


def guard(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "socket.connect", "socket.bind"}:
        DENIED.append(event)
        raise AssertionError("This gate permits no process/network activity: " + event)
    if event == "import" and args[0].split(".")[0] in {
        "peano_lab", "torch", "transformers", "mlx", "numpy", "sympy", "cvc5", "z3"
    }:
        DENIED.append(args[0])
        raise AssertionError("This gate permits no native/model/framework imports.")


sys.addaudithook(guard)
sys.dont_write_bytecode = True
# Import only the frozen stdlib-only helpers. The concurrently prepared monitor
# correction is deliberately not a dependency of these parser tests.
sys.path.insert(0, str(FROZEN))
spec = importlib.util.spec_from_file_location("paired_summary_parser_candidate", HERE / "paired_summary.py")
summary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(summary)
common = sys.modules["paired_common"]
RAW = RAW_PATH.read_text()
JOB = "21965180"


class SacctTests(unittest.TestCase):
    def test_actual_allocation_plus_empty_step_limit(self):
        value = summary.terminal_sacct(RAW, JOB)
        self.assertEqual(value, {"job_id": JOB, "state": "FAILED", "exit_code": 2,
            "exit_signal": 0, "elapsed_seconds": 106, "allocated_limit_seconds": 1560,
            "gpus": 1, "cpus": 8, "memory_gib": 64})
        self.assertEqual(len(RAW.splitlines()[1].split("|")), 6)
        self.assertEqual(RAW.splitlines()[1].split("|")[-1], "")

    def test_optional_seventh_separator_is_allowed(self):
        variant = "\n".join(line + "|" for line in RAW.splitlines()) + "\n"
        self.assertEqual(summary.terminal_sacct(variant, JOB), summary.terminal_sacct(RAW, JOB))

    def test_step_cannot_replace_allocation(self):
        with self.assertRaisesRegex(ValueError, "One exact allocation"):
            summary.terminal_sacct(RAW.splitlines()[1] + "\n", JOB)

    def test_other_job_or_other_step_rejected(self):
        for old in (JOB + "|", JOB + ".batch|"):
            with self.subTest(row=old), self.assertRaises(ValueError):
                summary.terminal_sacct(RAW.replace(old, "21965181" + old[len(JOB):]), JOB)

    def test_duplicate_allocation_rejected(self):
        with self.assertRaisesRegex(ValueError, "One exact allocation"):
            summary.terminal_sacct(RAW + RAW.splitlines()[0] + "\n", JOB)

    def test_malformed_field_count_and_allocation_limit_rejected(self):
        allocation, step = RAW.splitlines()
        variants = [allocation.rsplit("|", 1)[0], allocation + "|extra", allocation + "||",
                    allocation.rsplit("|", 1)[0] + "|", allocation + "\n" + step + "||"]
        for raw in variants:
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                summary.terminal_sacct(raw, JOB)

    def test_terminal_exit_and_resource_checks_remain_strict(self):
        replacements = [("FAILED", "RUNNING"), ("2:0", "unknown"), ("|106|", "|unknown|"),
                        ("cpu=8", "cpu=7"), ("mem=64G", "mem=32G"),
                        ("gres/gpu=1", "gres/gpu=2"), ("node=1", "node=2"),
                        ("billing=1,cpu=8", "cpu=8,cpu=8")]
        for before, after in replacements:
            with self.subTest(change=after), self.assertRaises(ValueError):
                summary.terminal_sacct(RAW.replace(before, after), JOB)

    def audit_constructed_empty_arm(self, raw, claimed_status="complete"):
        # These intentionally empty records isolate the existing final scheduler
        # completion gate; they are not a study, theorem, or actual completion.
        with tempfile.TemporaryDirectory(prefix="hydra-summary-parser-") as directory:
            directory = Path(directory).resolve()
            source_pins = {"fixture.py": "a" * 64}
            study = {"arms": {"symbolic": None},
                     "source_pins_sha256": sha256(common.canonical(source_pins)).hexdigest()}
            study_sha = sha256(common.canonical(study)).hexdigest()
            (directory / "sacct.txt").write_text(raw)
            common.save(directory / "receipt.json", {
                "schema": "hydra-paired-terminal-collection-v1", "actual_transport_exit_code": 0,
                "completion_chunk": "synthetic-parser-fixture-not-a-process-receipt", "job_id": JOB,
                "raw_sacct": {"path": "sacct.txt", **common.pin(directory / "sacct.txt")}})
            common.save(directory / "request.json", {"reservation": {
                "job_id": JOB, "seconds": 1560, "arm": "symbolic"}, "study_sha256": study_sha,
                "study": study, "source_pins_before": source_pins})
            common.save(directory / "completion.json", {"job_id": JOB, "study_sha256": study_sha,
                "arm": "symbolic", "sources_unchanged": True, "source_pins_after": source_pins,
                "status": claimed_status, "cases": [], "not_run": []})
            return summary.audit_arm(directory, directory / "receipt.json",
                common.pin(directory / "receipt.json")["sha256"], study, study_sha, [])

    def test_failed_actual_sacct_cannot_be_relabelled_complete(self):
        result = self.audit_constructed_empty_arm(RAW)
        self.assertFalse(result["execution_complete"])
        self.assertEqual(result["terminal"]["state"], "FAILED")
        self.assertEqual(result["terminal"]["exit_code"], 2)

    def test_nonzero_or_incomplete_cannot_claim_success(self):
        completed = RAW.replace("FAILED", "COMPLETED").replace("2:0", "0:0")
        self.assertTrue(self.audit_constructed_empty_arm(completed)["execution_complete"])
        for raw, claimed in [(completed.replace("0:0", "2:0"), "complete"),
                             (completed.replace("0:0", "0:9"), "complete"),
                             (completed.replace("COMPLETED", "TIMEOUT"), "complete"),
                             (completed, "incomplete")]:
            with self.subTest(raw=raw, claimed=claimed):
                self.assertFalse(self.audit_constructed_empty_arm(raw, claimed)["execution_complete"])

    def test_only_terminal_sacct_callable_changed(self):
        def functions(path):
            return {node.name: ast.dump(node, include_attributes=False)
                    for node in ast.parse(path.read_text()).body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
        original = functions(FROZEN / "paired_summary.py")
        candidate = functions(HERE / "paired_summary.py")
        self.assertEqual(set(original), set(candidate))
        self.assertEqual([name for name in original if original[name] != candidate[name]], ["terminal_sacct"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    watched = [FROZEN / "paired_summary.py", FROZEN / "paired_common.py",
               FROZEN / "paired_controller.py", HERE / "paired_summary.py", Path(__file__), RAW_PATH]
    before = {str(path.relative_to(ROOT)): common.pin(path) for path in watched}
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SacctTests))
    after = {str(path.relative_to(ROOT)): common.pin(path) for path in watched}
    passed = result.wasSuccessful() and before == after and not DENIED
    record = {"schema": "hydra-paired-summary-parser-pure-gate-v1", "passed": passed,
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "source_inputs_unchanged": before == after, "source_inputs": before,
        "prohibited_activity_attempts": DENIED, "native_model_scheduler_execution": False,
        "reserved_theorem_input_read": False, "scope": "pure raw sacct and constructed completion-gate tests"}
    with args.report.open("x") as handle:
        json.dump(record, handle, sort_keys=True, indent=2)
        handle.write("\n")
    print(json.dumps({"passed": passed, "tests_run": result.testsRun,
                      "report": str(args.report), "report_pin": common.pin(args.report)}, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
