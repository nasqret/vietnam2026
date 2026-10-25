"""Pure fixture gate: no native imports, subprocesses, network or study cases."""
from __future__ import annotations

import base64
import copy
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import paired_launchers as launch
import remote_paired_control as remote


def study():
    value = json.loads((launch.BUNDLE / "source" / remote.CONTROL / "study.template.json").read_bytes())
    api = remote.contract(launch.BUNDLE / "source")
    value.update(wall_profile="guarded-work-60-v1", source_pins_sha256=remote.SOURCE_MAP_SHA,
                 native_work=api.search_settings("guarded-work-60-v1"))
    for arm in remote.ARMS[1:]:
        value["arms"][arm].update(base_directory=remote.CAMPAIGN + "/authenticated-bases-01/" + remote.MODEL_KEYS[arm],
            adapter_directory=remote.ARTIFACTS[arm], adapter_manifest_sha256=remote.HISTORICAL_SHA if arm == "historical_1_7b" else "a" * 64)
    return value


def spec(arm="symbolic"):
    value = study()
    return launch.make_spec(value, remote.digest(remote.canonical(value) + b"\n"), arm, "1" * 32)


def ledger():
    return {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
        "automatic_retry": False, "gpu_hours_allocated": 3000 / 3600, "gpu_seconds_reserved": 3000,
        "gpu_reservations": [{"attempt": "smoke-" + str(i), "seconds": 600, "gpus": 1,
            "job_id": str(100 + i), "allocated_seconds": 600, "status": "failed_before_model_load"} for i in range(5)]}


class SchemaAndArguments(unittest.TestCase):
    def test_real_frozen_package_metadata_and_four_arm_contract(self):
        manifest, mapping = launch.bundle_inputs()
        self.assertEqual(manifest["file_count"], 1301)
        self.assertEqual(len(mapping), 734)
        self.assertEqual(remote.digest(remote.canonical(mapping)), remote.SOURCE_MAP_SHA)
        remote.validate_study(study(), launch.BUNDLE / "source")
        for arm in remote.ARMS:
            request = spec(arm)
            command = remote.job_script(request)
            self.assertIn("#!/bin/bash -l", command)
            self.assertIn("module load ML-bundle/25.10", command)
            self.assertIn("PYTHONHASHSEED=0", command)
            self.assertIn(remote.SOURCE + "/" + remote.CONTROL + "/paired_controller.py", command)
            self.assertNotIn("--model-key", command)
            self.assertNotIn("--resume", command)
            self.assertNotIn(" -I ", command)
            self.assertEqual(request["seconds"], 2040)

    def test_no_optional_arm_profile_override_boolean_or_changed_source(self):
        for key, value in (("arm", "fresh_8b"), ("seconds", 1800), ("uid", 502), ("gpus", True),
                           ("source", remote.TRAINING_SOURCE), ("argv", ["other"]), ("wall_profile", None)):
            row = spec(); row[key] = value
            with self.subTest(key=key), self.assertRaises((ValueError, KeyError)):
                remote.validate_spec(row)

    def test_study_cannot_change_exposure_paths_features_or_scope(self):
        base = study()
        for key, value in (("scope", "paired5"), ("source_pins_sha256", "b" * 64), ("wall_profile", None)):
            row = copy.deepcopy(base); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                remote.validate_study(row, launch.BUNDLE / "source")
        base["arms"]["fresh_4b"]["adapter_directory"] = "/tmp/elsewhere"
        with self.assertRaises(ValueError):
            remote.validate_study(base, launch.BUNDLE / "source")

    def test_null_choice_and_conflicting_actual_exits_fail(self):
        for row in ({}, {"actual_exit_code": True, "completion_chunk": "fake"},
                    {"actual_exit_code": 0, "exit_code": 1, "completion_chunk": "fake"}, {"actual_exit_code": 0}):
            with self.assertRaises(ValueError):
                launch.actual_completion(row)
        launch.actual_completion({"actual_exit_code": 0, "completion_chunk": "constructed-pure-fixture"})

    def test_only_metadata_training_reader_imports_and_pins(self):
        reader = launch.training_reader()
        self.assertEqual(reader.control.SOURCE, remote.TRAINING_SOURCE)
        self.assertEqual(set(reader.control.MODELS), {"qwen3-1.7b-base", "qwen3-4b-base"})
        self.assertFalse(any(name.startswith(("peano_lab", "torch", "transformers", "hydra_training_v5")) for name in sys.modules))


class BudgetAndHeldState(unittest.TestCase):
    def test_full_failed_charges_and_unknown_reservations_are_not_refunded(self):
        row = ledger(); self.assertEqual(launch.ledger_seconds(row), 3000)
        row["gpu_reservations"].append({"attempt": "uncertain", "seconds": 2040, "gpus": 1, "status": "release_requested_or_uncertain"})
        self.assertEqual(launch.ledger_seconds(row), 5040)
        row["gpu_reservations"][-1]["allocated_seconds"] = 1
        with self.assertRaises(ValueError):
            launch.ledger_seconds(row)

    def test_ledger_requires_charge_reconciliation(self):
        row = ledger(); charge = {"attempt": "new", "seconds": 2040, "allocated_seconds": 2040,
            "job_id": "777", "reservation_sha256": "c" * 64}
        with self.assertRaises(ValueError):
            launch.check_charges(row, [charge])
        row["gpu_reservations"].append(dict(charge, gpus=1))
        launch.check_charges(row, [charge])
        self.assertEqual(launch.ledger_seconds(row), 5040)

    def test_actual_pending_range_and_null_tres_preserve_exact_cpu_gpu_rejection(self):
        row = {"JobId": "55", "ReqTRES": "cpu=2,mem=4G,node=1", "AllocTRES": "(null)"}
        self.assertEqual(remote.check_queue_row("55", row)["allocated_tres"], {})
        row.update(JobId="99", ReqTRES="cpu=8,mem=64G,node=1,gres/gpu=1")
        with self.assertRaises(ValueError):
            remote.check_queue_row("99", row)
        self.assertEqual(remote.check_queue_row("99", row, "99")["job_id"], "99")
        row["AllocTRES"] = "not-a-tres"
        with self.assertRaises(ValueError):
            remote.check_queue_row("99", row, "99")

    def test_pending_num_nodes_1_or_1_dash_1_only(self):
        request = spec()
        row = {"JobId": "555", "JobName": request["job_name"], "Comment": "hydra-p6:" + request["nonce"],
            "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
            "Account": remote.ACCOUNT, "Partition": remote.PARTITION, "NumCPUs": "8", "NumNodes": "1-1",
            "TimeLimit": "00:34:00", "Command": request["remote_job_directory"] + "/job.sbatch",
            "WorkDir": request["remote_job_directory"], "StdOut": request["remote_job_directory"] + "/slurm.out",
            "StdErr": request["remote_job_directory"] + "/slurm.err", "UserId": "plgnasqret(105923)",
            "ReqTRES": "cpu=8,mem=64G,node=1,gres/gpu=1"}
        remote.check_held(row, request, "555")
        row["NumNodes"] = "1"; remote.check_held(row, request, "555")
        for value in ("1-2", "2", "(null)"):
            row["NumNodes"] = value
            with self.assertRaises(ValueError):
                remote.check_held(row, request, "555")


class CompletedTrainingAdmission(unittest.TestCase):
    def test_actual_metadata_contract_and_wrong_manifest_rejection(self):
        reader = launch.training_reader()
        _, plans, sources = reader.bundle_inputs()
        model_key = "qwen3-4b-base"
        model = reader.control.MODELS[model_key]
        plan = json.loads(reader.read(reader.ROOT / plans["models"][model_key]["prepared_plan"]["path"]))
        manifest, _, _ = reader.bundle_inputs()
        spec = reader.make_spec({"schema": "hydra-p6-training-allocation-choice-v1", "model_key": model_key,
            "seconds": 600, "soft_limit_seconds": 540, "throughput": {}, "transfer_receipt": {}, "base_admission": {}},
            "2" * 32, remote.digest(remote.canonical(manifest)))
        reservation = reader.control.reservation(spec, "777", remote.UID)
        audit = dict.fromkeys(("expected_optimizer_boundaries", "observed_optimizer_boundaries",
            "raw_finite_optimizer_boundaries", "post_clip_finite_optimizer_boundaries"), 256)
        audit.update(first_optimizer_step=1, last_optimizer_step=256)
        update = {"changed_parameter_tensors": 1, "initial_tensor_population_sha256": "a" * 64,
            "final_tensor_population_sha256": "b" * 64, "trainable_parameter_tensors": 392, "final_finite_parameter_tensors": 392}
        artifact = {"schema": "hydra-decision-pilot-artifact-v1", "profile": "hydra-fresh-decision-pilot-v2",
            "model_trained": True, "actual_optimizer_steps": 256, "model": model["model"], "automatic_retry": False,
            "resume": False, "plan": plan, "base": {"base_identity_sha256": "c" * 64}, "finite_gradient_audit": audit,
            "adapter_update": update, "saved_adapter_reload_admission": "required_by_P6_before_inference"}
        def pack(value, raw=False):
            blob = value if raw else remote.canonical(value) + b"\n"
            return {"bytes": len(blob), "sha256": remote.digest(blob), "base64": base64.b64encode(blob).decode(),
                "offset": 0, "stable": True, "complete_file": True}
        pinned = pack(artifact)
        receipt = {"manifest_path": model["artifact"] + "/manifest.json", "manifest_sha256": pinned["sha256"],
            "actual_optimizer_steps": 256, "finite_gradient_audit": audit, "adapter_update": update,
            "base_identity_sha256": "c" * 64, "saved_adapter_reload_admission": "required_by_P6_before_inference"}
        completion = {"schema": "hydra-p6-remote-training-completion-v1", "completed": True, "error": None,
            "sources_unchanged": True, "execute_invoked": True, "optimizer_steps_observed": 256,
            "actual_optimizer_steps_in_complete_artifact": 256, "source_pins_after": sources,
            "automatic_retry": False, "resume": False, "training_artifact": receipt}
        row = "|".join(["777", spec["job_name"], remote.REMOTE_USER, remote.ACCOUNT, remote.PARTITION,
            "COMPLETED", "0:0", "450", "10", "8", "64G", "cpu=8,mem=64G,node=1,gres/gpu=1",
            "cpu=8,mem=64G,node=1,gres/gpu=1", "gh200-node"]) + "\n"
        observation = {"job_id": "777", "read_only": True,
            "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None, "stdout_stderr": row}},
            "files": {"artifact/manifest.json": pinned, "job/actual-process-exit.txt": pack(b"0\n", raw=True),
                "job/result/request.json": pack({"reservation": reservation, "reservation_sha256": remote.digest(remote.canonical(reservation) + b"\n"),
                    "source_pins_before": sources}), "job/result/completion.json": pack(completion), "job/result/artifact-receipt.json": pack(receipt)}}
        response = {"schema": "hydra-p6-training-control-phase-v1", "phase": "collect", "completed": True, "error": None, "result": observation}
        transport = {"actual_ssh_exit_code": 0, "owned_child_reaped": True, "stop_reason": None,
            "remote_script_sha256": launch.TRAINING_PINS["remote_training_control.py"]}
        selected = study(); selected["arms"]["fresh_4b"]["adapter_manifest_sha256"] = pinned["sha256"]
        api = remote.contract(launch.BUNDLE / "source")
        with tempfile.TemporaryDirectory() as tmp, patch.object(launch, "ROOT", Path(tmp).resolve()):
            descriptors = {}
            for name, value in (("response", response), ("transport", transport),
                                ("actual_completion", {"actual_exit_code": 0, "completion_chunk": "synthetic-only"})):
                path = Path(tmp).resolve() / (name + ".json"); path.write_bytes(remote.canonical(value) + b"\n")
                descriptors[name] = {"path": path.name, "sha256": remote.digest(path.read_bytes())}
            admission = launch.admit_training("fresh_4b", descriptors, selected, api, reader)
            self.assertEqual(admission["manifest_sha256"], pinned["sha256"])
            self.assertFalse(admission["adapter_reload_admitted"])
            self.assertTrue(admission["reload_required_in_each_paired_case"])
            selected["arms"]["fresh_4b"]["adapter_manifest_sha256"] = "f" * 64
            with self.assertRaises(ValueError):
                launch.admit_training("fresh_4b", descriptors, selected, api, reader)


class FakeTransportAndCollection(unittest.TestCase):
    def test_spawn_failure_is_unknown_without_unbound_eof(self):
        with patch.object(launch.subprocess, "Popen", side_effect=OSError("pure fixture")):
            raw, receipt = launch.ssh_once({"phase": "collect"})
        self.assertEqual(raw, b"")
        self.assertEqual(receipt["remote_outcome"], "unknown")
        self.assertIsNone(receipt["actual_ssh_exit_code"])
        self.assertFalse(receipt["output_complete"])

    def test_ssh_timeout_records_unknown_and_reaps_without_retry(self):
        process = MagicMock(); process.poll.return_value = None; process.wait.return_value = -9
        process.stdin.fileno.return_value = 90; process.stdout.fileno.return_value = 91
        with patch.object(launch.subprocess, "Popen", return_value=process) as spawn, \
             patch.object(launch.os, "set_blocking"), patch.object(launch.time, "monotonic", side_effect=[0, 600.1, 600.2]):
            raw, receipt = launch.ssh_once({"phase": "collect"})
        self.assertEqual(receipt["stop_reason"], "ssh_wall_limit")
        self.assertEqual(receipt["remote_outcome"], "unknown")
        self.assertEqual(receipt["actual_ssh_exit_code"], -9)
        self.assertTrue(receipt["owned_child_reaped"])
        self.assertFalse(receipt["output_complete"])
        self.assertEqual(spawn.call_count, 1)
        process.kill.assert_called_once(); process.wait.assert_called_once_with(timeout=3)
        command = spawn.call_args.args[0][-1]
        self.assertIn(launch.LOGIN_PYTHON, command); self.assertIn(launch.LOGIN_PYTHON_LIB, command)

    def test_full_charge_precedes_the_only_release_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve(); (directory / "submit-held").mkdir()
            launch.put(directory / "submit-held/transport-completion.json", {"actual_ssh_exit_code": 0, "stop_reason": None, "owned_child_reaped": True})
            launch.put(directory / "submit-held/response.json", {"result": {"actual_sbatch_exit_code": 0, "held": True,
                "released": False, "job_id": "555", "uid": remote.UID}})
            request = spec(); value = ledger(); original = remote.canonical(value)
            args = SimpleNamespace(action="release", arm="symbolic", prepared_sha256="a" * 64, ledger_sha256="b" * 64)
            def failed(payload):
                charge = json.loads((directory / "release/charge-intent.json").read_bytes())
                self.assertEqual(charge["allocated_seconds"], 2040)
                self.assertEqual(charge["seconds_after"], 5040)
                return b"partial", {"actual_ssh_exit_code": -9, "owned_child_reaped": True, "stop_reason": "wall", "output_complete": False}
            with patch.object(launch, "load_prepared", return_value=(directory, {}, request, {}, "{}")), \
                 patch.object(launch, "current_ledger", return_value=(value, original, 3000)), \
                 patch.object(launch, "ssh_once", side_effect=failed) as transport:
                with self.assertRaises(ValueError):
                    launch.mutate_phase(args)
                with self.assertRaises(FileExistsError):
                    launch.mutate_phase(args)
                self.assertEqual(transport.call_count, 1)
            self.assertEqual(remote.canonical(value), original)
            self.assertTrue((directory / "release/transport-completion.json").is_file())

    def test_snapshot_marks_tail_and_symlink_rejection(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / "stdout"; path.write_bytes(b"a" * (256 * 1024 + 10))
            row = remote.snapshot(path, tail=True)
            self.assertFalse(row["complete_file"]); self.assertEqual(row["offset"], 10)
            link = path.with_name("link"); link.symlink_to(path)
            with self.assertRaises(ValueError):
                remote.snapshot(link, tail=True)
        self.assertEqual(len(remote.collection_files()), 10 + 16 * 11)
        self.assertFalse(any("safetensors" in name for name in remote.collection_files()))


if __name__ == "__main__":
    unittest.main()
