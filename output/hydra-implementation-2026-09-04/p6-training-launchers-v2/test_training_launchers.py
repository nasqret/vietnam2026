"""Pure JSON/file/fake-transport tests; no live child, SSH, native or model."""
from __future__ import annotations

import copy
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import remote_training_control as c
import training_launchers as l


def choice():
    return {"schema": "hydra-p6-training-allocation-choice-v1", "model_key": "qwen3-4b-base", "seconds": 600,
        "soft_limit_seconds": 540, "throughput": {}, "transfer_receipt": {}, "base_admission": {}}


def spec():
    return l.make_spec(choice(), "1" * 32, "2" * 64)


def ledger():
    return {"schema": "hydra-implementation-campaign-v1", "campaign_gpu_hours_ceiling": 6,
        "automatic_retry": False, "gpu_hours_allocated": 4 * 600 / 3600, "gpu_seconds_reserved": 2400,
        "gpu_reservations": [{"attempt": "failed-" + str(i), "seconds": 600, "gpus": 1,
            "job_id": str(20000 + i), "allocated_seconds": 600, "actual_scheduler_elapsed_seconds": 12,
            "status": "failed_before_model_load"} for i in range(4)]}


def pack(raw, *, offset=0, stable=True, complete=True):
    return {"bytes": len(raw), "sha256": c.digest(raw), "base64": c.base64.b64encode(raw).decode(),
        "offset": offset, "file_bytes_before": len(raw) + offset, "file_bytes_after": len(raw) + offset,
        "mtime_ns_before": 0, "stable": stable, "complete_file": complete}


def pack_json(value):
    return pack(c.canonical(value) + b"\n")


class BoundsAndPins(unittest.TestCase):
    def test_exact_two_models_and_fixed_training_command(self):
        self.assertEqual(set(c.MODELS), {"qwen3-1.7b-base", "qwen3-4b-base"})
        for key in c.MODELS:
            item = choice(); item["model_key"] = key
            request = l.make_spec(item, "1" * 32, "2" * 64)
            command = c.job_script(request)
            self.assertIn(c.SOURCE + "/" + c.TRAINER, command)
            self.assertIn("--model-key " + key, command)
            self.assertIn(c.MODELS[key]["config"], command)
            self.assertNotIn("--resume", command)
            self.assertNotIn("--max-steps", command)

    def test_no_fractional_minutes_boolean_or_unbounded_durations(self):
        for seconds, soft in [(True, 60), (599, 500), (299, 100), (7260, 6900), (600, 541), (600, 60.0), (7200, 6901)]:
            with self.subTest(seconds=seconds, soft=soft), self.assertRaises(ValueError):
                c.durations(seconds, soft)
        c.durations(300, 240)
        c.durations(7200, 6900)
        self.assertEqual(c.wall_string(7200), "02:00:00")

    def test_no_eight_b_or_cli_override_or_old_wrapper(self):
        for key, value in [("model_key", "qwen3-8b-base"), ("controller_sha256", "f" * 64),
                           ("source", c.SOURCE.replace("07", "06")), ("gpus", True), ("resume", True),
                           ("argv", ["echo", "override"])]:
            request = spec(); request[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                c.validate_spec(request)

    def test_no_default_choice(self):
        for mutation in ({"seconds": None}, {"model_key": "qwen3-8b-base"}, {"duration_override": 600}):
            item = choice(); item.update(mutation)
            with self.assertRaises(ValueError):
                l.validate_choice(item)

    def test_real_bundle06_metadata_pins_only(self):
        manifest, launch, source_map = l.bundle_inputs()
        self.assertEqual(manifest["file_count"], 1206)
        self.assertEqual(manifest["expanded_bytes"], 108048475)
        self.assertEqual(set(manifest["changed_files"]), {c.TRAINER, "output/p6-prototype/remote_provider_smoke.py"})
        self.assertEqual(c.digest(c.canonical(source_map)), c.SOURCE_MAP_SHA)
        for key in c.MODELS:
            self.assertEqual(launch["models"][key]["plan_sha256"], c.MODELS[key]["plan_sha256"])


class BudgetAndQueue(unittest.TestCase):
    def test_all_four_short_failed_allocations_remain_fully_charged(self):
        self.assertEqual(l.ledger_seconds(ledger()), 2400)

    def test_only_confirmed_pre_sbatch_failure_can_have_zero_charge(self):
        value = ledger()
        value["gpu_reservations"].append({"attempt": "preflight", "seconds": 600, "gpus": 1,
            "allocated_seconds": 0, "status": "preflight_stopped_before_sbatch"})
        self.assertEqual(l.ledger_seconds(value), 2400)
        value["gpu_reservations"][-1]["job_id"] = "999"
        with self.assertRaises(ValueError):
            l.ledger_seconds(value)

    def test_pending_and_uncertain_rows_reserve_full_wall_time(self):
        value = ledger()
        value["gpu_reservations"].append({"attempt": "pending", "seconds": 600, "gpus": 1, "status": "prepared"})
        self.assertEqual(l.ledger_seconds(value), 3000)
        value["gpu_reservations"][-1].update(status="release_uncertain", job_id="999")
        self.assertEqual(l.ledger_seconds(value), 3000)

    def test_no_partial_refund_or_duplicate_job_or_nonfinite_ledger(self):
        for mutate in (lambda value: value["gpu_reservations"][0].update(allocated_seconds=12),
                       lambda value: value["gpu_reservations"][1].update(job_id="20000"),
                       lambda value: value.update(gpu_hours_allocated=float("nan")),
                       lambda value: value.update(gpu_seconds_reserved=True)):
            value = ledger(); mutate(value)
            with self.assertRaises(ValueError):
                l.ledger_seconds(value)

    def test_unreconciled_or_refunded_charge_blocks_the_next_allocation(self):
        value = ledger()
        charge = {"attempt": "new", "job_id": "555", "seconds": 600, "allocated_seconds": 600,
                  "reservation_sha256": "a" * 64}
        with self.assertRaises(ValueError):
            l.check_charges(value, [charge])
        value["gpu_reservations"].append(copy.deepcopy(charge))
        l.check_charges(value, [charge])
        value["gpu_reservations"][-1]["allocated_seconds"] = 0
        with self.assertRaises(ValueError):
            l.check_charges(value, [charge])

    def test_cpu_array_element_is_left_untouched(self):
        row = {"ArrayJobId": "101", "ArrayTaskId": "4", "ReqTRES": "cpu=8,mem=64G,node=1", "AllocTRES": "cpu=8,mem=64G,node=1"}
        self.assertTrue(c.check_queue_row("101_4", row)["left_unchanged"])

    def test_gpu_in_either_requested_or_allocated_resources_blocks(self):
        for field in ("ReqTRES", "AllocTRES"):
            row = {"JobId": "101", "ReqTRES": "cpu=8,mem=64G,node=1", "AllocTRES": "cpu=8"}
            row[field] += ",gres/gpu:gh200=1"
            with self.assertRaises(ValueError):
                c.check_queue_row("101", row)

    def test_array_identity_and_ambiguous_scheduler_fields_fail_closed(self):
        with self.assertRaises(ValueError):
            c.check_queue_row("101_4", {"ArrayJobId": "101", "ArrayTaskId": "5", "ReqTRES": "cpu=8"})
        with self.assertRaises(ValueError):
            c.fields("JobId=101 JobId=102")

    def test_held_exact_identity_argv_and_resources(self):
        request = spec(); directory = request["remote_job_directory"]
        row = {"JobId": "123", "JobName": request["job_name"], "Comment": "hydra-p6:" + request["nonce"],
            "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0", "Account": c.ACCOUNT,
            "Partition": c.PARTITION, "NumCPUs": "8", "NumNodes": "1", "TimeLimit": "00:10:00", "UserId": "test(502)",
            "Command": directory + "/job.sbatch", "WorkDir": directory, "StdOut": directory + "/slurm.out",
            "StdErr": directory + "/slurm.err", "ReqTRES": "cpu=8,mem=64G,node=1,gres/gpu=1,gres/gpu:gh200=1"}
        c.check_held(row, request, "123", 502)
        for key, value in (("NumCPUs", "16"), ("TimeLimit", "01:00:00"), ("UserId", "test(503)"),
                           ("Command", "/tmp/unreviewed"), ("Reason", "Resources"), ("Restarts", "1")):
            changed = dict(row); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                c.check_held(changed, request, "123", 502)


class ActualHeldSerialization(unittest.TestCase):
    def fixture(self):
        # Actual CPU record supplies Slurm syntax only. The GPU-shaped fixture
        # below is synthetic, never an assertion that this CPU job had a GPU.
        path = Path(__file__).resolve().parent / "fixtures/held-cpu-21911629.json"
        raw = path.read_bytes()
        self.assertEqual(c.digest(raw), "f841b3a948c999ab94d85c7380db064dbf161efc956b008ace41e19436f2d8ae")
        actual = json.loads(raw)
        text = actual["files"]["held-inspect.stdout.txt"]["text"]
        self.assertEqual(c.digest(text.encode()), actual["files"]["held-inspect.stdout.txt"]["sha256"])
        row = c.fields(text)
        self.assertEqual(row["NumNodes"], "1-1")
        self.assertEqual(row["AllocTRES"], "(null)")
        self.assertEqual(c.tres(row["ReqTRES"])["node"], "1")
        request = spec()
        with self.assertRaises(ValueError):
            c.check_held(row, request, row["JobId"], actual["uid"])
        directory = request["remote_job_directory"]
        row.update(JobName=request["job_name"], Comment="hydra-p6:" + request["nonce"],
            Account=c.ACCOUNT, Partition=c.PARTITION, NumCPUs="8", NumTasks="1", **{"CPUs/Task": "8"},
            TimeLimit=c.wall_string(request["seconds"]), Command=directory + "/job.sbatch", WorkDir=directory,
            StdOut=directory + "/slurm.out", StdErr=directory + "/slurm.err",
            ReqTRES="cpu=8,mem=64G,node=1,gres/gpu=1,gres/gpu:gh200=1")
        return row, request, actual["uid"]

    def test_actual_shaped_held_target_accepts_single_node_range_and_null_allocation(self):
        row, request, uid = self.fixture()
        for notation in ("1", "1-1"):
            row["NumNodes"] = notation
            c.check_held(row, request, row["JobId"], uid)
            observed = c.check_queue_row(row["JobId"], row, allowed_job=row["JobId"])
            self.assertEqual(observed["allocated_tres"], {})
            self.assertEqual(observed["requested_tres"]["node"], "1")

    def test_larger_or_malformed_node_ranges_are_rejected(self):
        row, request, uid = self.fixture()
        for notation in ("1-2", "2", "0-1", "1-01", "1.0", "(null)", ""):
            row["NumNodes"] = notation
            with self.subTest(notation=notation), self.assertRaises(ValueError):
                c.check_held(row, request, row["JobId"], uid)

    def test_exact_requested_resources_remain_required(self):
        row, request, uid = self.fixture()
        for before, after in (("node=1", "node=2"), ("cpu=8", "cpu=4"),
                              ("mem=64G", "mem=128G"), ("gres/gpu=1", "gres/gpu=2")):
            changed = dict(row); changed["ReqTRES"] = row["ReqTRES"].replace(before, after)
            with self.subTest(resource=before), self.assertRaises(ValueError):
                c.check_held(changed, request, changed["JobId"], uid)

    def test_null_allocation_does_not_hide_another_requested_gpu(self):
        row, _, _ = self.fixture()
        with self.assertRaises(ValueError):
            c.check_queue_row(row["JobId"], row)
        row["ReqTRES"] = "cpu=8,mem=64G,node=1"
        self.assertEqual(c.check_queue_row(row["JobId"], row)["allocated_tres"], {})
        row["AllocTRES"] = "cpu=8,mem=64G,node=1,gres/gpu=1"
        with self.assertRaises(ValueError):
            c.check_queue_row(row["JobId"], row)

    def test_only_exact_null_sentinel_is_newly_normalized(self):
        row, _, _ = self.fixture()
        for malformed in ("null", "(NULL)", "N/A", "none", "cpu", "(null),gres/gpu=1", 0, False):
            row["AllocTRES"] = malformed
            with self.subTest(value=malformed), self.assertRaises(ValueError):
                c.check_queue_row(row["JobId"], row, allowed_job=row["JobId"])


class FakeChildLifecycle(unittest.TestCase):
    def fake(self, code=None):
        process = MagicMock()
        process.stdout.fileno.return_value = 91
        process.poll.return_value = code
        process.wait.return_value = -9 if code is None else code
        return process

    def test_already_finished_child_does_not_receive_kill(self):
        process = self.fake(0)
        with patch.object(c.subprocess, "Popen", return_value=process), patch.object(c.os, "set_blocking"), \
             patch.object(c.select, "select", return_value=([process.stdout], [], [])), \
             patch.object(c.os, "read", side_effect=[b"JobId=123", b""]), patch.object(c.time, "monotonic", return_value=0):
            result = c.bounded_command(["scontrol", "-o", "show", "job", "123"])
        self.assertEqual(result["actual_exit_code"], 0)
        self.assertTrue(result["owned_child_reaped"])
        process.kill.assert_not_called()

    def test_fifteen_second_wall_stop_kills_and_reaps_exact_owned_child(self):
        process = self.fake()
        with patch.object(c.subprocess, "Popen", return_value=process), patch.object(c.os, "set_blocking"), \
             patch.object(c.time, "monotonic", side_effect=[0, 15.1, 15.2]):
            result = c.bounded_command(["scontrol", "-o", "show", "job", "123"])
        self.assertEqual(result["stop_reason"], "wall_limit")
        self.assertEqual(result["actual_exit_code"], -9)
        self.assertTrue(result["owned_child_reaped"])
        process.kill.assert_called_once()
        process.wait.assert_called_once_with(timeout=3)

    def test_output_stop_keeps_only_bounded_evidence_and_reaps(self):
        process = self.fake()
        with patch.object(c.subprocess, "Popen", return_value=process), patch.object(c.os, "set_blocking"), \
             patch.object(c.select, "select", return_value=([process.stdout], [], [])), \
             patch.object(c.os, "read", return_value=b"123456789"), patch.object(c.time, "monotonic", return_value=0):
            result = c.bounded_command(["scontrol", "-o", "show", "job", "123"], limit=8)
        self.assertEqual(result["stop_reason"], "output_limit")
        self.assertEqual(result["stdout_stderr"], "12345678")
        self.assertTrue(result["owned_child_reaped"])
        process.kill.assert_called_once()

    def test_spawn_failure_is_not_a_successful_backend_execution(self):
        with patch.object(c.subprocess, "Popen", side_effect=OSError("fixture failure")):
            result = c.bounded_command(["scontrol", "-o", "show", "job", "123"])
        self.assertFalse(result["executed"])
        self.assertIsNone(result["actual_exit_code"])
        self.assertFalse(result["owned_child_reaped"])

    def test_release_charge_precedes_transport_and_uncertainty_is_one_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve(); (directory / "submit").mkdir()
            l.put(directory / "submit/transport-completion.json", {"actual_ssh_exit_code": 0, "stop_reason": None, "owned_child_reaped": True})
            l.put(directory / "submit/response.json", {"result": {"actual_sbatch_exit_code": 0, "held": True,
                "released": False, "job_id": "123", "uid": 502}})
            request = spec(); value = ledger(); original = c.canonical(value)
            args = SimpleNamespace(action="release", model_key="qwen3-4b-base", prepared_sha256="3" * 64, ledger_sha256="4" * 64)
            def failed_transport(payload):
                charge = json.loads((directory / "release/charge-intent.json").read_bytes())
                self.assertEqual(charge["allocated_seconds"], 600)
                self.assertEqual(charge["seconds_after"], 3000)
                return b"fixture uncertainty", {"actual_ssh_exit_code": -9, "owned_child_reaped": True, "stop_reason": "wall"}
            with patch.object(l, "load_prepared", return_value=(directory, {}, request, {})), \
                 patch.object(l, "current_ledger", return_value=(value, original, 2400)), \
                 patch.object(l, "ssh_once", side_effect=failed_transport) as transport:
                with self.assertRaises(ValueError):
                    l.mutate_phase(args)
                with self.assertRaises(FileExistsError):
                    l.mutate_phase(args)
                self.assertEqual(transport.call_count, 1)
            self.assertEqual(c.canonical(value), original)
            self.assertTrue((directory / "release/transport-completion.json").is_file())


class EvidenceTests(unittest.TestCase):
    def fixture(self):
        request = spec(); record = c.reservation(request, "123", 502)
        _, launch, source_map = l.bundle_inputs()
        plan = json.loads(l.read(l.ROOT / launch["models"][request["model_key"]]["prepared_plan"]["path"]))
        audit = {key: 256 for key in ("expected_optimizer_boundaries", "observed_optimizer_boundaries",
            "raw_finite_optimizer_boundaries", "post_clip_finite_optimizer_boundaries")}
        audit.update(first_optimizer_step=1, last_optimizer_step=256)
        update = {"changed_parameter_tensors": 1, "initial_tensor_population_sha256": "a" * 64,
            "final_tensor_population_sha256": "b" * 64, "trainable_parameter_tensors": 392, "final_finite_parameter_tensors": 392}
        manifest = {"schema": "hydra-decision-pilot-artifact-v1", "profile": "hydra-fresh-decision-pilot-v2",
            "model_trained": True, "actual_optimizer_steps": 256, "model": c.MODELS[request["model_key"]]["model"],
            "automatic_retry": False, "resume": False, "plan": plan, "base": {"base_identity_sha256": "c" * 64},
            "finite_gradient_audit": audit, "adapter_update": update, "saved_adapter_reload_admission": "required_by_P6_before_inference"}
        manifest_file = pack_json(manifest)
        artifact = {"manifest_path": c.MODELS[request["model_key"]]["artifact"] + "/manifest.json",
            "manifest_sha256": manifest_file["sha256"], "actual_optimizer_steps": 256,
            "finite_gradient_audit": audit, "adapter_update": update, "base_identity_sha256": "c" * 64,
            "saved_adapter_reload_admission": "required_by_P6_before_inference"}
        completion = {"schema": "hydra-p6-remote-training-completion-v1", "completed": True, "error": None,
            "sources_unchanged": True, "execute_invoked": True, "optimizer_steps_observed": 256,
            "actual_optimizer_steps_in_complete_artifact": 256, "source_pins_after": source_map,
            "automatic_retry": False, "resume": False, "training_artifact": artifact}
        raw = "|".join(["123", request["job_name"], c.REMOTE_USER, c.ACCOUNT, c.PARTITION, "COMPLETED", "0:0", "420", "10", "8", "64G",
            "cpu=8,mem=64G,node=1,gres/gpu=1", "cpu=8,mem=64G,node=1,gres/gpu=1", "gh200-node"]) + "\n"
        observation = {"job_id": "123", "read_only": True, "scheduler": {"sacct": {"actual_exit_code": 0, "stop_reason": None,
            "stdout_stderr": raw}}, "files": {"job/actual-process-exit.txt": pack(b"0\n"),
            "job/result/request.json": pack_json({"reservation": record, "reservation_sha256": c.digest(c.canonical(record) + b"\n"),
                                                   "source_pins_before": source_map}),
            "job/result/completion.json": pack_json(completion), "job/result/artifact-receipt.json": pack_json(artifact),
            "artifact/manifest.json": manifest_file}}
        return observation, request, record

    def test_synthetic_complete_metadata_still_does_not_admit_reload_or_quality(self):
        observation, request, record = self.fixture()
        result = l.summarize(observation, request, record, "c" * 64)
        self.assertTrue(result["saved_artifact_metadata_complete"], result)
        self.assertFalse(result["adapter_reload_admitted"])
        self.assertFalse(result["quality_evaluated"])

    def test_slurm_failure_overrides_apparent_successful_manifest(self):
        observation, request, record = self.fixture()
        observation["scheduler"]["sacct"]["stdout_stderr"] = observation["scheduler"]["sacct"]["stdout_stderr"].replace("|COMPLETED|0:0|", "|TIMEOUT|0:15|")
        result = l.summarize(observation, request, record)
        self.assertFalse(result["saved_artifact_metadata_complete"])
        self.assertEqual(result["slurm_state"], "TIMEOUT")

    def test_incomplete_marker_or_missing_process_exit_prevents_admission(self):
        for change in (lambda value: value["files"].update({"artifact/incomplete.json": pack_json({"model_trained": False})}),
                       lambda value: value["files"].pop("job/actual-process-exit.txt")):
            observation, request, record = self.fixture(); change(observation)
            self.assertFalse(l.summarize(observation, request, record)["saved_artifact_metadata_complete"])

    def test_unstable_manifest_or_mismatched_base_prevents_admission(self):
        observation, request, record = self.fixture()
        observation["files"]["artifact/manifest.json"]["stable"] = False
        self.assertFalse(l.summarize(observation, request, record)["saved_artifact_metadata_complete"])
        observation, request, record = self.fixture()
        self.assertFalse(l.summarize(observation, request, record, "d" * 64)["saved_artifact_metadata_complete"])

    def test_missing_counters_are_not_silently_zero(self):
        observation, request, record = self.fixture()
        observation["files"].pop("job/result/completion.json")
        result = l.summarize(observation, request, record)
        self.assertIsNone(result["optimizer_steps_observed"])
        self.assertIsNone(result["actual_optimizer_steps_in_complete_artifact"])

    def test_progress_tail_reports_seen_step_without_success(self):
        raw = b'broken prefix\n{"kind":"optimizer-step","step":83,"elapsed_seconds":100}\n{"kind":'
        observation = {"files": {"job/result/progress.jsonl": pack(raw, offset=1000, stable=False, complete=False)}}
        result = l.progress_snapshot(observation)
        self.assertEqual(result["last_optimizer_step_seen"], 83)
        self.assertFalse(result["complete_file"])
        self.assertFalse(result["stable_file_during_read"])

    def test_collection_is_bounded_and_excludes_weights(self):
        self.assertTrue(all(not name.endswith((".safetensors", "tokenizer.json", ".bin")) for name in c.FILES))
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp).resolve() / "large.log"; path.write_bytes(b"a" * (300 * 1024))
            row = c.snapshot(path, tail=True)
            self.assertEqual(row["bytes"], 256 * 1024)
            self.assertEqual(row["offset"], 44 * 1024)
            self.assertFalse(row["complete_file"])
            path.unlink(); path.write_bytes(b"x" * (2 * 1024**2 + 1))
            with self.assertRaises(ValueError):
                c.snapshot(path, tail=False)

    def test_evidence_symlink_is_not_followed(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp).resolve(); original = directory / "original"; original.write_bytes(b"safe")
            link = directory / "link"; link.symlink_to(original)
            with self.assertRaises(ValueError):
                c.snapshot(link, tail=False)


if __name__ == "__main__":
    unittest.main()
