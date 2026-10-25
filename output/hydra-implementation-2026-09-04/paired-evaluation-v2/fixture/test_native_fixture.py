"""Pure fixture admission checks; no native import, subprocess, or scheduler."""
from copy import deepcopy
from hashlib import sha256
import importlib.abc
import importlib.util
import io
import json
import os
from pathlib import Path
import signal
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("hydra_nonreserved_fixture", HERE / "native_fixture.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def authorization():
    return {"schema": MODULE.SCHEMA, "purpose": "nonreserved_native_lifecycle_compatibility",
        "uid": os.getuid(), "nonce": "a" * 32, "app_root": "/explicit/frozen/app", "output": "/explicit/new/output",
        "runtime": {"pure_test_only": True}, "source_pins_sha256": "b" * 64,
        "cases_sha256": MODULE.CASES_SHA, "limits": deepcopy(MODULE.LIMITS), "native_work": deepcopy(MODULE.WORK),
        "expected_slurm_job_id": "123456", "scheduler_validated": False, "gpu_allocation_claim": False,
        "automatic_retry": False, "resume": False}


def case_request(index=0):
    return {"schema": "hydra-cpu-fixture-case-request-v1", "authorization": "/new/authorization.json",
        "authorization_sha256": "a" * 64, "controller_pid": 123,
        "case_index": index, "theorem": MODULE.CASES[index]}


def unknown_result():
    search = {"status": "limit", "theorem": MODULE.CASES[1], "classical": False,
        "kernel_checked": False, "commands": [], "depth_reached": 3, "states_discovered": 8,
        "states_expanded": 4, "tactic_attempts": 12, "model_calls": 0, "model_advisor_calls": 0,
        "structured_planning": {"enabled": False, "requests": 0, "provider": None},
        "lemma_library": None, "branch_ranker": {"enabled": False}}
    for backend in ("vampire", "sympy", "cvc5", "egg", "e"):
        search[backend + "_calls"] = search[backend + "_advisor_calls"] = 0
    return {"status": "unknown", "request_sha256": "a" * 64, "source_pins_sha256": "b" * 64,
        "sources_unchanged": True, "original_input_theorem": MODULE.CASES[1],
        "canonical_theorem": MODULE.CASES[1], "blocked_execution_attempts": [], "search": search,
        "actual_counters": MODULE.common.validate_counts(search, None, None), "native_checked": False,
        "independent_original_replay": None}


def cancelled_execution():
    return {"helper_launches": 1, "quiescent": True, "leader_reaped": True,
        "termination_reason": "cancelled", "exit_code": -signal.SIGKILL,
        "forced_cleanup_ready": True, "rss_samples": 2}


class FixtureAdmissionTests(unittest.TestCase):
    def test_cpu_transport_requires_exact_actual_zero_exit(self):
        MODULE.require_scheduler_transport("JobId=123456", 0)
        for raw, code in (("JobId=123456", 1), ("", -9), ("", False), ("", None),
                          ("x" * 65537, 0), (b"JobId=123456", 0)):
            with self.subTest(code=code), self.assertRaises(ValueError):
                MODULE.require_scheduler_transport(raw, code)

    def test_only_two_fixed_theorem_inputs_and_exact_parent(self):
        self.assertEqual(len(MODULE.CASES), 2)
        self.assertEqual(MODULE.CASES[0], "forall a b. a=b -> b=a")
        self.assertEqual(MODULE.CASES[1], "forall a b. a=b -> S b=a")
        for index in range(2):
            self.assertEqual(MODULE.case_request_spec(case_request(index), 123), index)
        for key, value in (("case_index", 2), ("case_index", False), ("controller_pid", 999),
                           ("theorem", "0 = 0"), ("reference_script", ["refl"])):
            changed = case_request(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                MODULE.case_request_spec(changed, 123)

    def test_fixture_cannot_impersonate_study_or_allocation(self):
        MODULE.authorization_spec(authorization())
        for key, value in (("schema", "hydra-p6-p10-paired-reservation-v1"),
                ("schema", "hydra-p6-smoke-reservation-v1"), ("gpu_allocation_claim", True),
                ("scheduler_validated", True), ("automatic_retry", True), ("resume", True),
                ("job_id", "another"), ("expected_slurm_job_id", "123_4")):
            changed = authorization(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                MODULE.authorization_spec(changed)

    def test_owner_nonce_paths_and_budget_tampering_rejected(self):
        for key, value in (("uid", os.getuid() + 1), ("nonce", "z" * 32), ("cases_sha256", "c" * 64),
                           ("source_pins_sha256", "short"), ("output", "relative")):
            changed = authorization(); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                MODULE.authorization_spec(changed)
        for group, key, value in (("limits", "child_wall_seconds", 13),
                ("native_work", "max_model_calls", 1), ("native_work", "max_model_calls", False),
                ("native_work", "wall_seconds", 3)):
            changed = authorization(); changed[group][key] = value
            with self.subTest(group=group, key=key), self.assertRaises(ValueError):
                MODULE.authorization_spec(changed)

    def test_claim_survives_failure_and_cannot_be_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "authorization.json"
            record = authorization(); MODULE.common.save(path, record)
            digest = MODULE.common.pin(path)["sha256"]
            claim = MODULE.claim_authorization(path, digest, record)
            self.assertEqual(json.loads(claim.read_bytes())["pid"], os.getpid())
            with self.assertRaises(FileExistsError):
                MODULE.claim_authorization(path, digest, record)
            self.assertTrue(claim.exists())

    def test_missing_legacy_dependency_rejected_before_runtime_import(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing exact legacy"):
                MODULE.fixture_sources(Path(directory))

    def test_bounded_ordinary_case_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for index in range(8):
                (root / str(index)).write_text("small")
            self.assertIsNone(MODULE.artifact_limit(root))
            (root / "ninth").write_text("small")
            self.assertEqual(MODULE.artifact_limit(root), "case_artifact_inventory_error")
            (root / "ninth").unlink()
            (root / "7").unlink(); (root / "7").symlink_to(root / "0")
            self.assertEqual(MODULE.artifact_limit(root), "case_artifact_inventory_error")

    def test_false_case_requires_intentional_reaped_kill_and_unproved_search(self):
        result, execution = unknown_result(), cancelled_execution()
        self.assertEqual(MODULE.expected_case_outcome(1, MODULE.CASES[1], execution, result, "a" * 64, "b" * 64),
                         ("cancelled", True))
        for key, value in (("forced_cleanup_ready", False), ("rss_samples", 0), ("exit_code", 0),
                ("quiescent", False), ("termination_reason", "case_wall_limit")):
            changed = deepcopy(execution); changed[key] = value
            with self.subTest(key=key):
                self.assertFalse(MODULE.expected_case_outcome(1, MODULE.CASES[1], changed, result, "a" * 64, "b" * 64)[1])
        changed = deepcopy(result); changed["native_checked"] = True
        self.assertFalse(MODULE.expected_case_outcome(1, MODULE.CASES[1], execution, changed, "a" * 64, "b" * 64)[1])

    def test_unknown_or_unbound_record_cannot_become_positive_proof(self):
        result, execution = unknown_result(), cancelled_execution()
        result["original_input_theorem"] = MODULE.CASES[0]
        execution.update(termination_reason="process_exit", exit_code=0)
        self.assertFalse(MODULE.expected_case_outcome(0, MODULE.CASES[0], execution, result, "a" * 64, "b" * 64)[1])
        for key, value in (("request_sha256", "c" * 64), ("source_pins_sha256", "c" * 64),
                           ("sources_unchanged", False), ("original_input_theorem", "0 = 0")):
            changed = unknown_result(); changed[key] = value
            with self.subTest(key=key):
                self.assertFalse(MODULE.expected_case_outcome(1, MODULE.CASES[1], cancelled_execution(), changed, "a" * 64, "b" * 64)[1])

    def test_external_or_model_activity_cannot_be_hidden(self):
        for key in ("model_calls", "vampire_calls", "sympy_calls", "cvc5_calls", "egg_calls", "e_calls"):
            changed = unknown_result(); changed["search"][key] = 1
            with self.subTest(key=key):
                self.assertFalse(MODULE.expected_case_outcome(1, MODULE.CASES[1], cancelled_execution(), changed, "a" * 64, "b" * 64)[1])


if __name__ == "__main__":
    blocked = []
    class NoRuntime(importlib.abc.MetaPathFinder):
        def find_spec(self, fullname, path=None, target=None):
            if fullname.split(".", 1)[0] in MODULE.FORBIDDEN_IMPORTS | {"peano_lab", "hybrid_search", "training", "hydra_training_v5"}:
                blocked.append("import:" + fullname)
                raise RuntimeError("Pure fixture tests may not import runtime/native code.")
            return None
    def no_execution(event, args):
        if event in {"subprocess.Popen", "os.system", "os.fork", "os.forkpty", "os.posix_spawn",
                     "os.exec", "os.kill", "os.killpg", "socket.connect", "socket.connect_ex", "socket.bind"}:
            blocked.append(event)
            raise RuntimeError("Pure fixture tests cannot launch or signal processes/network.")
    sys.meta_path.insert(0, NoRuntime())
    sys.addaudithook(no_execution)
    files = [HERE / "native_fixture.py", Path(__file__).resolve()] + [MODULE.CONTROL / name for name in MODULE.CONTROL_PINS]
    before = {str(path.relative_to(MODULE.CONTROL)): sha256(path.read_bytes()).hexdigest() for path in files}
    began = time.monotonic(); stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(FixtureAdmissionTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    after = {str(path.relative_to(MODULE.CONTROL)): sha256(path.read_bytes()).hexdigest() for path in files}
    passed = result.wasSuccessful() and result.testsRun == 10 and before == after and not blocked
    record = {"schema": "hydra-cpu-fixture-pure-tests-v1", "passed": passed, "tests": result.testsRun,
        "errors": len(result.errors), "failures": len(result.failures), "skipped": len(result.skipped),
        "source_pins_before": before, "source_pins_after": after, "sources_unchanged": before == after,
        "elapsed_seconds": time.monotonic() - began, "blocked_execution_attempts": blocked,
        "scope": "Pure constructed authority/result metadata only; no native/model/scheduler/child/holdout execution."}
    out = HERE / "pure-gate-02"
    out.mkdir(exist_ok=False)
    with (out / "pure-tests.log").open("x") as handle:
        handle.write(stream.getvalue())
    with (out / "pure-tests.json").open("x") as handle:
        json.dump(record, handle, sort_keys=True, indent=2); handle.write("\n")
    print(json.dumps({key: value for key, value in record.items() if not key.startswith("source_pins_")}, sort_keys=True))
    raise SystemExit(0 if passed else 1)
