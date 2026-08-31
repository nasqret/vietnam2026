"""Synthetic caller fixtures, never artifact admission or scientific results.

All genuine admission, binding, scheduler, native and model entrypoints are
explicitly stubbed. Temporary JSON and reference objects are only fixtures;
they cannot be used as training provenance, resource approvals or proofs.
"""
import ast
from contextlib import ExitStack, redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("retention_recovery_cli_fixture",
    ROOT / "scripts/execute_peano_hydra_retention_evaluation_recovery.py")
cli = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cli
spec.loader.exec_module(cli)
ev = cli.evaluation


class SyntheticCandidate:
    """Explicit parser/admission stub; no file, producer or receipt is trusted."""
    def __init__(self, identity, locations):
        self.identity = deepcopy(identity)
        self.manifest_path = Path(locations["manifest_path"])
        self.manifest_sha256 = identity["manifest_sha256"]
        self.admission_receipt_sha256 = identity["admission_receipt_sha256"]
        receipt = locations["admission_receipt_path"]
        self.admission_receipt_path = None if receipt is None else Path(receipt)
        self.inputs = SimpleNamespace(evaluation_plan_sha256=cli.EVALUATION_PLAN["sha256"], baseline=object())

    def to_dict(self): return deepcopy(self.identity)
    def protected_paths(self): return (self.manifest_path.parent,)


class RecoveryCallerGuards(unittest.TestCase):
    def setUp(self):
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="retention-recovery-fixture-", dir="/private/tmp")))
        self.stack.enter_context(patch.object(cli, "ROOT", self.root))
        self.stack.enter_context(patch.dict(cli.os.environ, {}, clear=True))
        self.stack.enter_context(redirect_stdout(io.StringIO()))
        self.stack.enter_context(redirect_stderr(io.StringIO()))
        self.stack.enter_context(patch.object(cli.saved, "PreservedRetentionArtifactReference", SyntheticCandidate))
        self.stack.enter_context(patch.object(cli.saved, "reference", side_effect=SyntheticCandidate))
        self.package = self.root / cli.gate.PACKAGE
        self.package.mkdir(parents=True)
        for name in ("training", "scripts", "slurm", "peano-lab", ".git", "archive"):
            (self.root / name).mkdir()
        model = self.save(self.root / "saved-model/manifest.json", {"synthetic_only": True})
        self.stack.enter_context(patch.object(cli, "MODEL_MANIFEST", {key: model[key] for key in ("bytes", "sha256")}))
        plan = self.save(self.package / "evaluation-plan.json", {"synthetic_only": True})
        self.stack.enter_context(patch.object(cli, "EVALUATION_PLAN", plan))
        self.bound_record = {"plan_sha256": "b" * 64, "synthetic_only": True}
        self.bound = SimpleNamespace(to_dict=lambda: deepcopy(self.bound_record))

    def save(self, path, record):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        raw = cli.canonical(record) + b"\n"
        path.write_bytes(raw)
        return {"path": path.relative_to(self.root).as_posix(), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

    def input_fixture(self, *, draft=False):
        record = {"schema": cli.INPUT_SCHEMA, "profile": cli.gate.PROFILE, "run_id": cli.gate.RUN_ID,
            "candidate_reference": {"synthetic_only": True, "manifest_sha256": cli.MODEL_MANIFEST["sha256"],
                                    "admission_receipt_sha256": None if draft else "a" * 64},
            "locations": {"local": {"manifest_path": str(self.root / "saved-model/manifest.json"),
                "admission_receipt_path": None if draft else str(self.package / "admission.json")},
                "helios": {"manifest_path": "/synthetic-not-present/saved-model/manifest.json",
                    "admission_receipt_path": None if draft else "/synthetic-not-present/admission.json"}},
            "evaluation_plan": deepcopy(cli.EVALUATION_PLAN)}
        pin = self.save(self.package / ("admission-request.json" if draft else "inputs.json"), record)
        inputs = cli.load_inputs(self.root / pin["path"], pin["sha256"], draft=draft)
        return record, pin, inputs

    def stage_fixture(self):
        _, inputs_pin, inputs = self.input_fixture()
        preflight = self.save(self.package / "preflight.json", cli.preflight_record(inputs, self.bound))
        request = {"schema": cli.STAGE_SCHEMA, "profile": cli.gate.PROFILE, "run_id": cli.gate.RUN_ID,
            "stage": "evaluate", "inputs": inputs_pin, "preflight": preflight,
            "evaluation_plan_sha256": cli.EVALUATION_PLAN["sha256"],
            "bound_evaluation_plan_sha256": self.bound_record["plan_sha256"],
            "model_manifest": deepcopy(cli.MODEL_MANIFEST), "producer_source_commit": cli.PRODUCER_COMMIT,
            "training_job_id": cli.TRAINING_JOB_ID, "failed_evaluation_job_id": cli.FAILED_EVALUATION_JOB_ID,
            "output": cli.OUTPUT, "training_authorized": False, "automatic_retry": False, "resume": False,
            "historical_checkpoint_reuse_allowed": False}
        pin = self.save(self.package / "evaluate-request.json", request)
        return request, pin, inputs

    def test_draft_cannot_become_final_inputs_without_actual_receipt(self):
        record, pin, _ = self.input_fixture(draft=True)
        with self.assertRaisesRegex(ValueError, "fixed recovery input"):
            cli.load_inputs(self.root / pin["path"], pin["sha256"])
        final = self.save(self.package / "inputs.json", record)
        with self.assertRaisesRegex(ValueError, "nullable draft"):
            cli.load_inputs(self.root / final["path"], final["sha256"])
        record["candidate_reference"]["admission_receipt_sha256"] = "a" * 64
        draft = self.save(self.package / "admission-request.json", record)
        with self.assertRaisesRegex(ValueError, "nullable draft"):
            cli.load_inputs(self.root / draft["path"], draft["sha256"], draft=True)

    def test_duplicate_or_wrong_final_physical_binding_is_rejected(self):
        record, pin, _ = self.input_fixture()
        for other in (deepcopy(record["locations"]["local"]), {"manifest_path": "/absent/model.json", "admission_receipt_path": None}):
            record["locations"]["helios"] = other
            pin = self.save(self.root / pin["path"], record)
            with self.assertRaises(ValueError):
                cli.load_inputs(self.root / pin["path"], pin["sha256"])

    def test_source_or_admission_change_invalidates_cpu_preflight(self):
        _, pin, _ = self.stage_fixture()
        with patch.object(cli, "bind_inputs", return_value=self.bound) as binding:
            self.assertIs(cli.check_stage_request(self.root / pin["path"], pin["sha256"])[2], self.bound)
            self.bound_record["plan_sha256"] = "c" * 64
            with self.assertRaisesRegex(ValueError, "differs from the CPU preflight"):
                cli.check_stage_request(self.root / pin["path"], pin["sha256"])
            self.assertEqual(binding.call_count, 2)

    def test_training_retry_resume_and_old_job_mutations_fail_before_binding(self):
        request, pin, _ = self.stage_fixture()
        for key, value in (("stage", "train"), ("training_authorized", True), ("resume", True),
                           ("automatic_retry", True), ("historical_checkpoint_reuse_allowed", True),
                           ("training_job_id", "999"), ("failed_evaluation_job_id", "999")):
            with self.subTest(key=key), patch.object(cli, "bind_inputs") as binding:
                changed = self.save(self.root / pin["path"], {**request, key: value})
                with self.assertRaisesRegex(ValueError, "evaluation-only scope"):
                    cli.check_stage_request(self.root / changed["path"], changed["sha256"])
                binding.assert_not_called()

    def execution_fixture(self):
        request, stage_pin, inputs = self.stage_fixture()
        observed = {"scientific_input": stage_pin, "model_manifest": deepcopy(cli.MODEL_MANIFEST),
            "producer_source_commit": cli.PRODUCER_COMMIT, "training_job_id": cli.TRAINING_JOB_ID,
            "failed_evaluation_job_id": cli.FAILED_EVALUATION_JOB_ID, "job_id": "9999",
            "allocation_elapsed_seconds": 42, "allocation_remaining_seconds": 3558,
            "approval_sha256": "a" * 64, "source_files_sha256": "f" * 64}
        clock = [100.0]
        def live(*_):
            clock[0] += 25.0  # Synthetic gate delay; no scheduler runs.
            return deepcopy(observed)
        gate = self.stack.enter_context(patch.object(cli.gate, "check_job_reservation", side_effect=live))
        self.stack.enter_context(patch.object(cli.time, "monotonic", side_effect=lambda: clock[0]))
        self.stack.enter_context(patch.object(cli, "check_stage_request", return_value=(request, inputs, self.bound)))
        authorization = {"synthetic_scientific_assertion_only": True}
        self.stack.enter_context(patch.object(cli, "evaluation_authorization", return_value=authorization))
        self.stack.enter_context(patch.object(ev, "_guard_output"))
        execute = self.stack.enter_context(patch.object(ev, "execute_evaluation", return_value={"metrics": {"synthetic_only": True}}))
        return observed, gate, authorization, execute

    def test_live_gate_model_and_producer_must_match_exact_saved_candidate(self):
        observed, _, _, execute = self.execution_fixture()
        observed["model_manifest"] = {"bytes": 1, "sha256": "0" * 64}
        with self.assertRaisesRegex(ValueError, "reserved historical producer"):
            cli.execute("a" * 64, lambda: False)
        execute.assert_not_called()

    def test_immutable_gate_change_prevents_execution(self):
        observed, gate, _, execute = self.execution_fixture()
        gate.side_effect = [observed, {**observed, "source_files_sha256": "0" * 64}]
        with self.assertRaisesRegex(ValueError, "reserved source/input/model identity"):
            cli.execute("a" * 64, lambda: False)
        execute.assert_not_called()

    def test_deadline_includes_first_gate_and_only_exact_assertion_can_refresh(self):
        _, gate, authorization, execute = self.execution_fixture()
        result = cli.execute("a" * 64, lambda: False)
        self.assertFalse(result["independent_proof_verification_performed"])
        self.assertFalse(result["training_performed"])
        kwargs = execute.call_args.kwargs
        self.assertEqual(kwargs["allocation_deadline"], 100.0 + 3300 - 42 - 1.0)
        self.assertEqual(kwargs["expected_authorization_sha256"], cli.digest(authorization))
        with self.assertRaisesRegex(ValueError, "exact derived scientific authorization"):
            kwargs["reservation_check"]({"changed": True})
        self.assertEqual(gate.call_count, 2)

    def test_cpu_output_protection_precedes_admission_and_evaluation_binding(self):
        for draft, mode in ((True, "--authenticate-admission"), (False, "--check-inputs")):
            _, pin, _ = self.input_fixture(draft=draft)
            with self.subTest(mode=mode), patch.object(cli.saved, "authenticate_admission") as admission, \
                    patch.object(cli, "bind_inputs") as binding:
                result = cli.main([mode, "--inputs", str(self.root / pin["path"]), "--expected-inputs-sha256", pin["sha256"],
                                   "--output", str(self.root / "scripts/forbidden.json")])
                self.assertEqual(result, 2)
                admission.assert_not_called(); binding.assert_not_called()

    def verifier_fixture(self):
        _, pin, _ = self.input_fixture()
        checkpoint = self.root / "collected-checkpoint"
        head = self.save(checkpoint / "HEAD.json", {"synthetic_only": True})
        output = self.root / "archive/verification.json"
        args = ["--verify-checkpoint", str(checkpoint), "--inputs", str(self.root / pin["path"]),
            "--expected-inputs-sha256", pin["sha256"], "--expected-authorization-sha256", "c" * 64,
            "--expected-checkpoint-head-sha256", head["sha256"], "--output", str(output)]
        return args, checkpoint, output

    def test_wrong_external_head_is_rejected_before_binding_or_native_replay(self):
        args, _, output = self.verifier_fixture()
        args[args.index("--expected-checkpoint-head-sha256") + 1] = "0" * 64
        with patch.object(cli, "bind_inputs") as binding, patch.object(ev, "verify_checkpoint") as replay:
            self.assertEqual(cli.main(args), 2)
            binding.assert_not_called(); replay.assert_not_called()
        self.assertFalse(output.exists())

    def test_replay_uses_external_authorization_and_changed_head_cannot_publish(self):
        args, checkpoint, output = self.verifier_fixture()
        def changed_head(*_, **kwargs):
            self.assertEqual(kwargs, {"expected_authorization_sha256": "c" * 64, "replay": True})
            self.save(checkpoint / "HEAD.json", {"synthetic_only": True, "changed": True})
            return {"synthetic_not_native_replay": True}
        with patch.object(cli, "bind_inputs", return_value=self.bound) as binding, \
                patch.object(ev, "verify_checkpoint", side_effect=changed_head) as replay:
            self.assertEqual(cli.main(args), 2)
            binding.assert_called_once(); replay.assert_called_once()
        self.assertFalse(output.exists())

    def test_evaluation_path_overrides_are_rejected_before_live_gate(self):
        with patch.object(cli, "execute") as execute:
            self.assertEqual(cli.main(["--evaluate", "--approval-sha256", "a" * 64,
                "--inputs", str(self.package / "inputs.json")]), 2)
            execute.assert_not_called()


class PreservedScientificControls(unittest.TestCase):
    def test_new_resource_context_cannot_relabel_old_profile_or_package(self):
        record = {"status": "job-verified", "profile": cli.gate.PROFILE, "run_id": cli.gate.RUN_ID,
            "stage": "evaluate", "job_id": "9999", "resource_request_sha256": "1" * 64,
            "approval_sha256": "2" * 64, "source_commit": "3" * 40, "source_files_sha256": "4" * 64,
            "payloads_sha256": "5" * 64, "reservation": {"seconds": 3600, "gpus": 1, "cpus": 8, "memory_gib": 64},
            "allocation_elapsed_seconds": 42, "allocation_remaining_seconds": 3558,
            "scientific_input": {"path": cli.gate.PACKAGE + "/evaluate-request.json", "bytes": 1, "sha256": "6" * 64},
            "automatic_retry": False, "resume": False, "producer_source_commit": cli.PRODUCER_COMMIT}
        checked = ev._reservation(record)
        self.assertEqual(checked["producer_source_commit"], cli.PRODUCER_COMMIT)
        self.assertNotIn("allocation_elapsed_seconds", checked)
        for mutation in ({"run_id": "retention-pilot-v1"}, {"stage": "train"}, {"resume": True},
                         {"reservation": {"seconds": 3601, "gpus": 1, "cpus": 8, "memory_gib": 64}},
                         {"scientific_input": {**record["scientific_input"], "path": "_deploy/hydra-retention-pilot-v1/evaluate-request.json"}}):
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                ev._reservation({**record, **mutation})
        old = {**record, "profile": "peano-hydra-retention-pilot-v1", "run_id": "retention-pilot-v1",
               "scientific_input": {**record["scientific_input"], "path": "_deploy/hydra-retention-pilot-v1/evaluate-request.json"}}
        self.assertEqual(ev._reservation(old)["run_id"], "retention-pilot-v1")

    def test_original_goal_search_proof_checkpoint_and_metrics_code_is_unchanged(self):
        original = ROOT.parent / "hydra-retention-execution-20260830/training/peano_hydra/retention_evaluation.py"
        raw = original.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), "1f42a76f0c1127b7edd2ce171c0e238b5846941a40b1c5cd185f676b9dc5bf92")
        old, new = (ast.parse(value) for value in (raw, (ROOT / "training/peano_hydra/retention_evaluation.py").read_bytes()))
        excluded = {"execution_sources", "bind_evaluation", "_reservation"}
        def functions(tree):
            return {node.name: ast.dump(node, include_attributes=False) for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name not in excluded}
        self.assertEqual(functions(old), functions(new))


if __name__ == "__main__":
    unittest.main()
