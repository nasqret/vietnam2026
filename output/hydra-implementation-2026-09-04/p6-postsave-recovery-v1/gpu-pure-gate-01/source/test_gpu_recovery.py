"""Pure synthetic metadata/command tests; never invokes run(), SSH or a model."""
import ast
import base64
from copy import deepcopy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import gpu_saved_reload as gpu
import remote_recovery_control as control
import recovery_launchers as launcher
import derive_helpers

HERE = Path(__file__).resolve().parent


def spec():
    return launcher.make_spec("b" * 32, "c" * 64, "d" * 64, "e" * 64)


def reservation():
    return control.reservation(spec(), "21919999", control.UID)


def metadata():
    return {"schema": gpu.METADATA_SCHEMA, "passed": True, "eligible_for_saved_reload": True,
        "saved_adapter_reload_required": True, "model_loaded": False, "job_id": gpu.ORIGINAL_JOB,
        "original_process_exit_code": 1, "original_slurm_state": "FAILED", "original_slurm_exit_code": "1:0",
        "original_controller_completed": False, "source_root": gpu.SOURCE, "source_pins_sha256": gpu.SOURCE_MAP_SHA,
        "provider_sha256": gpu.PROVIDER_SHA, "manifest_sha256": gpu.MANIFEST_SHA,
        "artifact_directory": gpu.ARTIFACT, "base_directory": gpu.BASE,
        "final_tensor_population_sha256": gpu.FINAL_TENSOR_SHA, "plan_sha256": gpu.PLAN_SHA,
        "metadata_source_sha256": control.METADATA_VERIFIER_SHA, "sources_unchanged": True, "errors": []}


def actual():
    return {"schema": gpu.ACTUAL_SCHEMA, "actual_exit_code": 0, "completion_chunk": "abcdef",
            "receipt_sha256": "c" * 64, "verifier_sha256": control.METADATA_VERIFIER_SHA}


def loaded():
    return {"actual_model_calls": 0, "forward_passes": 0, "generated_token_slots": 0,
        "identity": {"source_sha256": gpu.PROVIDER_SHA, "model_id": gpu.MODEL_ID,
            "revision": gpu.REVISION, "base_identity_sha256": gpu.BASE_SHA, "model_loaded": True,
            "automatic_retry": False, "automatic_download": False,
            "allocation": {"job_id": "21919999", "gpus": 1, "cpus": 8, "memory_gib": 64, "seconds": 300},
            "adapter": {"adapter_present": True, "saved_adapter_reload_checked": True,
                "adapter_manifest_sha256": gpu.MANIFEST_SHA, "final_tensor_population_sha256": gpu.FINAL_TENSOR_SHA,
                "adapter_kind": "fresh_decision_pilot"}}, "reload_elapsed_seconds": 1.0}


def file_row(value, raw=False):
    data = value if raw else control.canonical(value) + b"\n"
    return {"bytes": len(data), "sha256": control.digest(data), "base64": base64.b64encode(data).decode(),
            "offset": 0, "file_bytes_before": len(data), "file_bytes_after": len(data),
            "mtime_ns_before": 1, "stable": True, "complete_file": True}


def observation():
    s, r = spec(), reservation()
    record = {"schema": "hydra-p6-saved-reload-completion-v1", "completed": True, "error": None,
        "job_id": r["job_id"], "original_job_id": gpu.ORIGINAL_JOB, "original_failed_job_preserved": True,
        "original_slurm_state": "FAILED", "original_slurm_exit_code": "1:0",
        "sources_and_artifact_unchanged": True, "model_disposal_completed": True,
        "saved_adapter_reload_checked": True, "resaved_manifest": False, "automatic_retry": False,
        "generation_calls": 0, "optimizer_updates": 0, "native_calls": 0, "solver_calls": 0,
        "elapsed_seconds": 1.5, **{k: s[k] for k in ("metadata_receipt_sha256", "metadata_actual_sha256",
            "controller_sha256", "provider_sha256", "source_pins_sha256", "artifact_manifest_sha256",
            "final_tensor_population_sha256")}}
    line = "|".join([r["job_id"], s["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION,
        "COMPLETED", "0:0", "10", "5", "8", "64G", "cpu=8,mem=64G,node=1,gres/gpu=1",
        "cpu=8,mem=64G,node=1,gres/gpu=1", "x1002c0s3b0n0"])
    pins = {"manifest.json": {"bytes": 100, "sha256": gpu.MANIFEST_SHA}}
    return {"job_id": r["job_id"], "read_only": True,
        "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None, "stdout_stderr": line}},
        "files": {"job/actual-process-exit.txt": file_row(b"0\n", True),
            "job/reservation.json": file_row(r),
            "job/reservation.json.claimed": file_row({"job_id": r["job_id"], "nonce": r["nonce"],
                "reservation_sha256": control.digest(control.canonical(r) + b"\n")}),
            "job/result/request.json": file_row({"reservation": r, "source_pins_before": {"synthetic": "fixture"}}),
            "job/result/completion.json": file_row(record), "job/result/loaded-model.json": file_row(loaded()),
            "job/result/artifact-before.json": file_row(pins), "job/result/artifact-after.json": file_row(pins)}}


class GPURecoveryTests(unittest.TestCase):
    def test_exact_metadata_and_actual_receipt_required(self):
        gpu.validate_metadata(metadata(), actual(), "c" * 64, control.METADATA_VERIFIER_SHA)
        for key, value in (("passed", False), ("original_slurm_state", "COMPLETED"),
                           ("original_process_exit_code", 0), ("sources_unchanged", False),
                           ("final_tensor_population_sha256", "f" * 64), ("errors", ["bad"])):
            bad = metadata(); bad[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                gpu.validate_metadata(bad, actual(), "c" * 64, control.METADATA_VERIFIER_SHA)

    def test_no_cpu_flag_or_exit_fallback(self):
        for key, value in (("actual_exit_code", 1), ("actual_exit_code", False),
                           ("completion_chunk", "not-observed"), ("receipt_sha256", "e" * 64)):
            bad = actual(); bad[key] = value
            with self.subTest(field=key, value=value), self.assertRaises(ValueError):
                gpu.validate_metadata(metadata(), bad, "c" * 64, control.METADATA_VERIFIER_SHA)
        with self.assertRaises(ValueError):
            gpu.validate_metadata(metadata(), {}, "c" * 64, control.METADATA_VERIFIER_SHA)

    def test_controller_and_metadata_pins_are_actual_file_bytes(self):
        self.assertEqual(control.CONTROLLER_SHA, control.digest((HERE / "gpu_saved_reload.py").read_bytes()))
        self.assertEqual(control.METADATA_VERIFIER_SHA, control.digest((HERE / "metadata_recovery.py").read_bytes()))
        self.assertEqual(control.SOURCE_MAP_SHA,
                         control.digest(control.canonical(json.loads((HERE / "controller-source-pins.json").read_bytes()))))

    def test_exact_reservation_is_bound_to_new_owned_job(self):
        gpu.validate_reservation(reservation(), control.UID)
        for key, value in (("seconds", 600), ("soft_limit_seconds", 241), ("gpus", 2),
                           ("job_id", gpu.ORIGINAL_JOB), ("generation_calls", 1),
                           ("model_key", "qwen3-4b-base"), ("source_root", "/tmp/alternate")):
            bad = reservation(); bad[key] = value
            with self.subTest(field=key), self.assertRaises(ValueError):
                gpu.validate_reservation(bad, control.UID)
        bad = reservation(); bad["extra_cli"] = "--train"
        with self.assertRaises(ValueError):
            gpu.validate_reservation(bad, control.UID)

    def test_fixed_job_has_no_training_or_generation_override(self):
        script = control.job_script(spec())
        self.assertTrue(script.startswith("#!/bin/bash -l\n"))
        self.assertIn("module load ML-bundle/25.10", script)
        self.assertIn(control.PROJECT + "/.venv-helios/bin/python -B -P " + control.PACKAGE + "/gpu_saved_reload.py", script)
        self.assertIn("--reservation-sha256", script)
        for forbidden in ("--config", "--throughput", "--model-key", "--resume", "remote_training_pilot.py"):
            self.assertNotIn(forbidden, script)
        bad = spec(); bad["seconds"] = 600
        with self.assertRaises(ValueError): control.job_script(bad)

    def test_held_1_1_null_format_and_queue_preservation(self):
        s = spec()
        row = {"JobId": "21919999", "JobName": s["job_name"], "Comment": "hydra-p6:" + s["nonce"],
            "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
            "Account": control.ACCOUNT, "Partition": control.PARTITION, "NumCPUs": "8", "NumNodes": "1-1",
            "TimeLimit": "00:05:00", "Command": s["remote_job_directory"] + "/job.sbatch",
            "WorkDir": s["remote_job_directory"], "StdOut": s["remote_job_directory"] + "/slurm.out",
            "StdErr": s["remote_job_directory"] + "/slurm.err", "UserId": "plgnasqret(105923)",
            "ReqTRES": "cpu=8,mem=64G,node=1,gres/gpu=1", "AllocTRES": "(null)"}
        control.check_held(row, s, "21919999", control.UID)
        control.check_queue_row("21919999", row, "21919999")
        with self.assertRaises(ValueError): control.check_queue_row("21919999", row)
        row["NumNodes"] = "1-2"
        with self.assertRaises(ValueError): control.check_held(row, s, "21919999", control.UID)
        cpu = {"JobId": "77", "ReqTRES": "cpu=2,mem=4G,node=1", "AllocTRES": "(null)"}
        self.assertTrue(control.check_queue_row("77", cpu)["left_unchanged"])

    def test_copied_safety_helpers_are_unchanged(self):
        def nodes(path):
            return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        current, original = nodes(HERE / "remote_recovery_control.py"), nodes(derive_helpers.REMOTE)
        for name in derive_helpers.REMOTE_NAMES:
            with self.subTest(remote=name): self.assertEqual(current[name], original[name])
        current, original = nodes(HERE / "recovery_launchers.py"), nodes(derive_helpers.LOCAL)
        for name in derive_helpers.LOCAL_NAMES:
            with self.subTest(local=name): self.assertEqual(current[name], original[name])
        source = (HERE / "recovery_launchers.py").read_text()
        source = source.replace('"remote_recovery_control.py"', '"remote_smoke_control.py"').replace(
            '"hydra-p6-saved-recovery-control-phase-v1"', '"hydra-p6-8b-smoke-control-phase-v1"')
        current = {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(source).body
                   if isinstance(n, ast.FunctionDef)}
        original = nodes(derive_helpers.SMOKE)
        for name in derive_helpers.SMOKE_NAMES:
            with self.subTest(transport=name): self.assertEqual(current[name], original[name])

    def test_full_charge_is_written_before_release_transport(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary).resolve()
            (directory / "submit").mkdir()
            (directory / "submit/transport-completion.json").write_text(json.dumps({
                "actual_ssh_exit_code": 0, "owned_child_reaped": True, "output_complete": True, "stop_reason": None}))
            (directory / "submit/response.json").write_text(json.dumps({"result": {
                "actual_sbatch_exit_code": 0, "held": True, "released": False, "job_id": "21919999", "uid": control.UID}}))
            seen = []
            def fake_transport(phase, payload):
                charge = json.loads((phase / "charge-intent.json").read_bytes())
                self.assertEqual(charge["allocated_seconds"], 300)
                self.assertEqual(charge["seconds_after"], 4500)
                self.assertEqual(charge["reservation_sha256"], control.digest(control.canonical(payload["reservation"]) + b"\n"))
                seen.append(payload["phase"])
                return {"synthetic": True}
            with patch.object(launcher, "load_prepared", return_value=(directory, {}, spec(), {})), \
                 patch.object(launcher, "current_ledger", return_value=({}, b"synthetic ledger", 4200)), \
                 patch.object(launcher, "execute_phase", side_effect=fake_transport):
                launcher.mutate_phase(SimpleNamespace(action="release", prepared_sha256="x", ledger_sha256="y"))
                with self.assertRaises(FileExistsError):
                    launcher.mutate_phase(SimpleNamespace(action="release", prepared_sha256="x", ledger_sha256="y"))
            self.assertEqual(seen, ["release"])

    def test_actual_tensor_reload_and_zero_calls_are_mandatory(self):
        gpu.validate_loaded_report(loaded(), "21919999")
        for key in ("actual_model_calls", "forward_passes", "generated_token_slots"):
            bad = loaded(); bad[key] = 1
            with self.subTest(counter=key), self.assertRaises(ValueError): gpu.validate_loaded_report(bad, "21919999")
        bad = loaded(); bad["identity"]["adapter"]["final_tensor_population_sha256"] = "f" * 64
        with self.assertRaises(ValueError): gpu.validate_loaded_report(bad, "21919999")
        bad = loaded(); bad["identity"]["adapter"]["saved_adapter_reload_checked"] = False
        with self.assertRaises(ValueError): gpu.validate_loaded_report(bad, "21919999")

    def test_complete_synthetic_reload_keeps_original_failure_distinct(self):
        o = observation()
        launcher.validate_observation(o)
        summary = launcher.summarize(o, spec(), reservation(), {"synthetic": "fixture"})
        self.assertEqual(summary["status"], "saved_adapter_independent_reload_complete")
        self.assertTrue(summary["saved_adapter_reload_admitted"])
        self.assertEqual(summary["original_training_status"], "FAILED 1:0")
        self.assertFalse(summary["quality_evaluated"])

    def test_terminal_failure_overrides_apparent_success_payload(self):
        o = observation()
        o["scheduler"]["sacct"]["stdout_stderr"] = o["scheduler"]["sacct"]["stdout_stderr"].replace("|COMPLETED|0:0|", "|FAILED|1:0|")
        self.assertFalse(launcher.summarize(o, spec(), reservation(), {"synthetic": "fixture"})["saved_adapter_reload_admitted"])
        o = observation(); o["files"]["job/actual-process-exit.txt"] = file_row(b"1\n", True)
        self.assertFalse(launcher.summarize(o, spec(), reservation(), {"synthetic": "fixture"})["saved_adapter_reload_admitted"])

    def test_changed_artifact_and_unchecked_tensor_cannot_pass_summary(self):
        o = observation()
        o["files"]["job/result/artifact-after.json"] = file_row({"manifest.json": {"bytes": 100, "sha256": "0" * 64}})
        self.assertFalse(launcher.summarize(o, spec(), reservation(), {"synthetic": "fixture"})["saved_adapter_reload_admitted"])
        o = observation(); record = loaded(); record["identity"]["adapter"]["saved_adapter_reload_checked"] = False
        o["files"]["job/result/loaded-model.json"] = file_row(record)
        self.assertFalse(launcher.summarize(o, spec(), reservation(), {"synthetic": "fixture"})["saved_adapter_reload_admitted"])

    def test_recovery_has_no_generation_training_or_native_call_site(self):
        tree = ast.parse((HERE / "gpu_saved_reload.py").read_text())
        forbidden = {"generate", "backward", "run_proof", "checked_surface_final", "probe_completion_gradients", "execute"}
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)]
        leaf = lambda n: n.func.id if isinstance(n.func, ast.Name) else (n.func.attr if isinstance(n.func, ast.Attribute) else "")
        self.assertFalse({leaf(n) for n in calls} & forbidden)
        self.assertEqual(sum(leaf(n) == "load_torch_model" for n in calls), 1)


if __name__ == "__main__":
    unittest.main()
