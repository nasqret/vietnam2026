"""Pure controller tests: no subprocesses, native imports, tokenizer, model or fit."""
from copy import deepcopy
from hashlib import sha256
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name("remote_training_pilot.py")
SPEC = importlib.util.spec_from_file_location("remote_training_controller_test", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def reservation(seconds=7200):
    return {"schema": "hydra-p6-training-reservation-v1", "job_id": "21910000", "job_name": "hydra-q4-train",
        "nonce": "a" * 32, "uid": os.getuid(), "account": MODULE.ACCOUNT, "partition": MODULE.PARTITION,
        "model_key": "qwen3-4b-base", "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": seconds, "soft_limit_seconds": min(6900, seconds - 60),
        **{key: "b" * 64 for key in ("config_sha256", "dataset_sha256", "plan_sha256", "controller_sha256", "source_pins_sha256")}}


def scheduler(record):
    hours, remaining = divmod(record["seconds"], 3600)
    minutes, seconds = divmod(remaining, 60)
    return (f"JobId={record['job_id']} JobName={record['job_name']} UserId=owner({record['uid']}) "
        f"Account={record['account']} Partition={record['partition']} Comment=hydra-p6:{record['nonce']} "
        "JobState=RUNNING Requeue=0 Restarts=0 NumNodes=1 NumCPUs=8 NodeList=hgpu0001 "
        "AllocTRES=cpu=8,mem=64G,node=1,billing=8,gres/gpu=1,gres/gpu:gh200=1 "
        f"RunTime=00:00:42 TimeLimit={hours:02d}:{minutes:02d}:{seconds:02d}")


def plan(record):
    value = {"schema": "hydra-decision-pilot-plan-v2", "profile": "hydra-fresh-decision-pilot-v2",
        "model": dict(zip(("model_id", "revision"), MODULE.MODELS[record["model_key"]])),
        "config_sha256": record["config_sha256"], "resume": False, "automatic_retry": False,
        "epochs": 1, "prompt_schema": "primitive_v4", "planner_rows_allowed": False,
        "model_trained": False, "training_rows": 2047, "validation_rows": 432, "expected_optimizer_steps": 256}
    value["plan_sha256"] = sha256(MODULE.canonical(value)).hexdigest()
    record["plan_sha256"] = value["plan_sha256"]
    return value


class TrainingControllerPureTests(unittest.TestCase):
    def test_new_reservation_accepts_explicit_finite_bounds(self):
        helper = MODULE.smoke_helpers()
        for duration in (300, 3600, 7200):
            record = reservation(duration)
            self.assertEqual(MODULE.reservation_spec(record), record)
            live = helper.parse_scontrol(scheduler(record), record)
            self.assertEqual(live["seconds"], duration)
            self.assertEqual(live["elapsed_seconds"], 42)

    def test_budget_pin_types_schema_and_owner_fail_closed(self):
        for key, value in (("schema", "hydra-p6-smoke-reservation-v1"), ("seconds", 7201),
                ("seconds", 299), ("seconds", 7200.0), ("soft_limit_seconds", 7100),
                ("cpus", 16), ("gpus", 2), ("gpus", True), ("memory_gib", 128),
                ("uid", os.getuid() + 1), ("model_key", "unpinned"), ("plan_sha256", "short"),
                ("config_sha256", "B" * 64), ("retry", True)):
            changed = reservation(); changed[key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                MODULE.reservation_spec(changed)

    def test_scheduler_cannot_rebind_nonce_resources_duration_or_requeue(self):
        record = reservation(); helper = MODULE.smoke_helpers(); raw = scheduler(record)
        for before, after in (("hydra-p6:", "another:"), ("Requeue=0", "Requeue=1"),
                ("Restarts=0", "Restarts=1"), ("NumCPUs=8", "NumCPUs=16"),
                ("mem=64G", "mem=128G"), ("gres/gpu=1", "gres/gpu=2"),
                ("TimeLimit=02:00:00", "TimeLimit=03:00:00")):
            with self.subTest(before=before), self.assertRaises(ValueError):
                helper.parse_scontrol(raw.replace(before, after), record)

    def test_claim_survives_failure_and_cannot_be_reused(self):
        record = reservation()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reservation.json"
            MODULE.save(path, record)
            expected = MODULE.digest(path)
            claimed = MODULE.claim_reservation(path, record, expected, Path(directory) / "out", {"job_id": record["job_id"]})
            self.assertTrue(claimed.is_file())
            with self.assertRaises(FileExistsError):
                MODULE.claim_reservation(path, record, expected, Path(directory) / "retry", {"job_id": record["job_id"]})
            self.assertFalse(json.loads(claimed.read_bytes())["automatic_retry"])

    def test_claim_rejects_changed_reservation_without_consumption(self):
        record = reservation()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reservation.json"; MODULE.save(path, record)
            with self.assertRaises(ValueError):
                MODULE.claim_reservation(path, record, "f" * 64, Path(directory) / "out", {"job_id": record["job_id"]})
            self.assertFalse(path.with_name(path.name + ".claimed").exists())

    def test_plan_matches_exact_model_config_hash_rows_and_schema(self):
        record = reservation(); prepared = plan(record)
        MODULE.validate_plan(prepared, record)
        for key, value in (("resume", True), ("planner_rows_allowed", True), ("expected_optimizer_steps", 257),
                ("training_rows", 4097), ("config_sha256", "f" * 64), ("schema", "hydra-decision-pilot-plan-v1")):
            changed = deepcopy(prepared); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): MODULE.validate_plan(changed, record)
        wrong_model = deepcopy(record); wrong_model["model_key"] = "qwen3-8b-base"
        with self.assertRaises(ValueError): MODULE.validate_plan(prepared, wrong_model)

    def test_progress_records_only_actual_callbacks_and_is_bounded(self):
        calls = []; clock = [0.0]
        with tempfile.TemporaryDirectory() as directory, patch("sys.stdout", io.StringIO()):
            logger = MODULE.Progress(Path(directory), lambda: calls.append(True), 2, clock=lambda: clock[0])
            logger({"kind": "training-start", "rows": 16, "expected_optimizer_steps": 2})
            logger({"kind": "optimizer-step", "step": 1})
            clock[0] = 151.0
            logger({"kind": "optimizer-step", "step": 2})
            self.assertEqual(logger.last_optimizer_step, 2)
            self.assertEqual(len(calls), 2)
            for value in ({"kind": "optimizer-step", "step": 2}, {"kind": "optimizer-step", "step": 3},
                          {"kind": "inference"}):
                with self.assertRaises(ValueError): logger(value)
            rows = [json.loads(line) for line in (Path(directory) / "progress.jsonl").read_text().splitlines()]
            self.assertEqual(len(rows), 3)

    def test_failed_scheduler_check_keeps_observed_completed_step(self):
        clock = [0.0]
        def failed(): raise ValueError("No longer the reserved live job")
        with tempfile.TemporaryDirectory() as directory:
            logger = MODULE.Progress(Path(directory), failed, 1, clock=lambda: clock[0]); clock[0] = 151
            with self.assertRaises(ValueError): logger({"kind": "optimizer-step", "step": 1})
            self.assertEqual(logger.last_optimizer_step, 1)
            self.assertEqual(logger.events, 1)

    def test_partial_or_different_artifact_is_never_accepted(self):
        record = reservation(); prepared = plan(record); tokens = {"base": {"identity": "test-only"}}
        with tempfile.TemporaryDirectory() as directory:
            for artifact in ({}, {"model_trained": True}, {"schema": "hydra-decision-pilot-artifact-v1",
                    "model_trained": True, "resume": False, "automatic_retry": False, "plan": prepared,
                    "token_preflight": tokens, "base": tokens["base"], "actual_optimizer_steps": 255,
                    "saved_adapter_reload_admission": "required_by_P6_before_inference"}):
                with self.assertRaises(ValueError):
                    MODULE.validate_artifact(artifact, prepared, tokens, Path(directory), None)

    def test_python_must_honor_the_hash_seed_before_start(self):
        with patch.object(MODULE.platform, "system", return_value="Linux"), \
                patch.object(MODULE.platform, "machine", return_value="aarch64"), \
                patch.object(MODULE.sys, "version_info", (3, 13, 5)), \
                patch.object(MODULE.sys, "flags", SimpleNamespace(ignore_environment=1)):
            with self.assertRaisesRegex(ValueError, "PYTHONHASHSEED"):
                MODULE.runtime_identity({"dependencies": {}})

    def test_no_overwrite_and_strict_regular_file_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"; MODULE.save(path, {"actual": True})
            with self.assertRaises(FileExistsError): MODULE.save(path, {"actual": False})
            with self.assertRaises(ValueError): MODULE.ordinary(path, 1)
            link = Path(directory) / "alias.json"; link.symlink_to(path)
            with self.assertRaises(ValueError): MODULE.ordinary(link)


if __name__ == "__main__": unittest.main()
