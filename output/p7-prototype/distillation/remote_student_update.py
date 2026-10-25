"""One explicitly reserved fresh student update on admitted teacher data.

No allocation, download, resume or retry. This is a new P7 plan/profile and
reservation, with reviewed P6 scheduler/runtime/audit helpers used read-only.
All model/tokenizer execution remains an explicit root-scheduled invocation.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import sys
import time

import teacher_data
from teacher_data import APP, ROOT, HERE, BASE_SHA, BASE_ROWS, HOLDOUT_SHA, SELECTION_SHA, Inputs, canonical, digest, require

PROFILE = "hydra-fresh-teacher-augmented-pilot-v1"
CONTROLLER_SCHEMA = "hydra-p7-student-update-reservation-v1"
P6_CONTROLLER_SHA = "241c82deabe4171cf0c2cdabf2cfceb2b2067931482a9cdf8ec11cff6a1085b2"


class UpdateCancelled(BaseException):
    pass


def p6_helpers():
    path = ROOT / "output/p6-prototype/remote_training_pilot.py"
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 128 * 1024
            and sha256(path.read_bytes()).hexdigest() == P6_CONTROLLER_SHA,
            "The reviewed frozen P6 scheduler/runtime helper changed.")
    spec = importlib.util.spec_from_file_location("hydra_p7_frozen_p6_update_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_pins():
    helper = p6_helpers()
    result = helper.source_pins(APP)
    for relative, expected in teacher_data.source_pins().items():
        raw = helper.ordinary(ROOT / relative, 2 * 1024**2)
        require(sha256(raw).hexdigest() == expected, "Teacher update source changed during pinning.")
        result[relative] = {"bytes": len(raw), "sha256": expected}
    return result


def reservation_spec(record):
    helper = p6_helpers()
    fields = {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
        "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds", "soft_limit_seconds",
        "config_sha256", "dataset_sha256", "plan_sha256", "controller_sha256", "source_pins_sha256"}
    require(type(record) is dict and set(record) == fields and record["schema"] == CONTROLLER_SCHEMA,
            "Expected the exact separate one-use P7 student-update reservation.")
    require(type(record["job_id"]) is str and re.fullmatch(r"\d{1,20}", record["job_id"])
            and type(record["job_name"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", record["job_name"])
            and type(record["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", record["nonce"]),
            "Invalid student-update allocation identity.")
    require(type(record["uid"]) is int and record["uid"] == os.getuid()
            and record["account"] == helper.ACCOUNT and record["partition"] == helper.PARTITION
            and record["model_key"] in helper.MODELS, "Student allocation owner/account/model differs.")
    for key, expected in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64)):
        require(type(record[key]) is int and record[key] == expected, "Student update resources exceed the fixed campaign.")
    require(type(record["seconds"]) is int and 300 <= record["seconds"] <= 7200
            and type(record["soft_limit_seconds"]) is int
            and 60 <= record["soft_limit_seconds"] <= min(6900, record["seconds"] - 60),
            "Student update exceeds the finite allocation or cleanup reserve.")
    require(all(helper.valid_sha(record[key]) for key in fields if key.endswith("_sha256")),
            "Every student-update input needs an exact explicit pin.")
    return record


def validate_plan(record, reservation):
    helper = p6_helpers()
    model = dict(zip(("model_id", "revision"), helper.MODELS[reservation["model_key"]]))
    require(record.get("schema") == "hydra-teacher-augmented-pilot-plan-v1"
            and record.get("profile") == PROFILE and record.get("model") == model
            and record.get("config_sha256") == reservation["config_sha256"]
            and record.get("plan_sha256") == reservation["plan_sha256"]
            and digest({k: v for k, v in record.items() if k != "plan_sha256"}) == reservation["plan_sha256"],
            "Student plan does not match its exact reserved extension/model/config.")
    data = record.get("data_attestation") or {}
    require(data.get("schema") == "hydra-teacher-augmented-data-attestation-v1"
            and data.get("manifest_sha256") == reservation["dataset_sha256"]
            and data.get("base_manifest_sha256") == BASE_SHA and data.get("base_training_rows") == BASE_ROWS
            and type(data.get("teacher_rows_added")) is int and data["teacher_rows_added"] > 0
            and type(data.get("fresh_verified_continuations")) is int
            and 0 < data["fresh_verified_continuations"] <= 32
            and type(data.get("actual_teacher_model_calls")) is int
            and data["fresh_verified_continuations"] <= data["actual_teacher_model_calls"] <= 64
            and helper.valid_sha(data.get("teacher_model_manifest_sha256"))
            and data.get("holdout_sha256") == HOLDOUT_SHA and data.get("selection_sha256") == SELECTION_SHA
            and data.get("reserved_intermediate_check") == "exact_closed_AST_plus_declared_template_exclusions"
            and data.get("teacher_source_scope") == "complete_teacher_proposed_native_continuation"
            and data.get("regenerated_byte_exact") is True and data.get("base_train_prefix_preserved") is True
            and data.get("validation_test_unchanged") is True,
            "No nonempty fully admitted teacher augmentation supports this update.")
    rows = record.get("training_rows")
    require(type(rows) is int and BASE_ROWS < rows <= 4096 and rows == BASE_ROWS + data["teacher_rows_added"]
            and record.get("expected_optimizer_steps") == (rows + 7) // 8
            and record.get("epochs") == 1 and record.get("resume") is False
            and record.get("automatic_retry") is False and record.get("model_trained") is False
            and record.get("prompt_schema") == "primitive_v4" and record.get("planner_rows_allowed") is False,
            "Student update must be one fresh bounded primitive-only pass with the intact base rows.")


def run(args):
    helper = p6_helpers()
    raw = helper.ordinary(args.reservation, 65536)
    require(sha256(raw).hexdigest() == args.reservation_sha256, "Student reservation bytes changed.")
    scheduler = helper.smoke_helpers()
    reservation = reservation_spec(scheduler.strict_json(raw))
    require(sys.platform == "linux" and os.environ.get("SLURM_JOB_ID") == reservation["job_id"],
            "Student updates run only in their exact root-owned remote Slurm allocation.")
    require(helper.digest(__file__) == reservation["controller_sha256"], "Student-update controller identity changed.")
    before = source_pins()
    require(digest(before) == reservation["source_pins_sha256"], "Student-update source bundle changed.")
    for path, expected, maximum in ((args.config, reservation["config_sha256"], 32768),
                                   (args.dataset_manifest, reservation["dataset_sha256"], 2 * 1024**2)):
        require(path.absolute().resolve(strict=True) == path.absolute()
                and path.resolve().is_relative_to(ROOT) and helper.digest(path, maximum) == expected,
                "Student config/dataset must be an exact regular input in the sealed source tree.")
    output = args.output.absolute()
    require(output.resolve() == output and not output.exists() and not output.is_symlink(),
            "Use a new controller receipt directory without a symlink escape.")
    output.mkdir(parents=True, exist_ok=False)
    checker = scheduler.LiveReservation(reservation, output)
    first = checker()
    require(first["elapsed_seconds"] < reservation["soft_limit_seconds"] - 30,
            "Insufficient remaining allocation for clean admission and cleanup.")
    helper.save(args.reservation.with_name(args.reservation.name + ".claimed"), {
        "schema": "hydra-p7-student-update-consumption-v1", "job_id": reservation["job_id"],
        "nonce": reservation["nonce"], "reservation_sha256": args.reservation_sha256,
        "dataset_sha256": reservation["dataset_sha256"], "plan_sha256": reservation["plan_sha256"],
        "pid": os.getpid(), "output": str(output), "automatic_retry": False, "resume": False})
    began = time.monotonic() - first["elapsed_seconds"]
    deadline = began + reservation["soft_limit_seconds"]

    def stopped():
        return time.monotonic() >= deadline

    def alarm(signum, frame):
        raise UpdateCancelled("Student update received its bounded stop/cancel signal.")

    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, alarm)
    signal.alarm(max(1, math.ceil(deadline - time.monotonic())))
    helper.save(output / "request.json", {"schema": "hydra-p7-student-update-request-v1", "profile": PROFILE,
        "reservation": reservation, "reservation_sha256": args.reservation_sha256,
        "source_pins_before": before, "base_directory": str(args.base_directory),
        "config": str(args.config), "dataset_manifest": str(args.dataset_manifest),
        "student_initialization": "fresh_pinned_Qwen_base_new_LoRA", "resume": False,
        "automatic_retry": False, "teacher_model_calls": 0, "native_proof_runs": 0,
        "campaign_ledger_enforced_by": "root_orchestrator"})
    plan = artifact = tokens = None
    progress = helper.Progress(output, checker, expected_steps=512)
    error = None
    try:
        teacher_data.bootstrap()
        import teacher_student_pilot as pilot
        from experimental_model import registry
        from hydra_training_v5.peano_policy import manifest as artifacts
        runtime = helper.runtime_identity(registry())
        helper.save(output / "runtime.json", runtime)
        require(os.environ.get("PYTHONHASHSEED") == "20260904", "Fixed hash seed must be set before Python starts.")
        plan = pilot.prepare(args.config, dataset_manifest=args.dataset_manifest,
                              dataset_sha256=reservation["dataset_sha256"])
        validate_plan(plan.record, reservation)
        helper.save(output / "prepared-plan.json", plan.record)
        progress.expected_steps = plan.record["expected_optimizer_steps"]
        require(not stopped(), "Student update stopped before tokenizer preflight.")
        features, tokens, tokenizer = pilot.tokenize(plan, base_directory=args.base_directory, should_stop=stopped)
        del features, tokenizer
        helper.save(output / "token-preflight.json", tokens)
        artifact = pilot.execute(plan, base_directory=args.base_directory,
            expected_token_preflight_sha256=digest(tokens), reservation_check=checker,
            stop_requested=stopped, progress=progress, stop_after_seconds=reservation["soft_limit_seconds"])
        require(artifact.get("profile") == PROFILE, "Trained artifact lost its explicit teacher-data profile.")
        helper.validate_artifact(artifact, plan.record, tokens, ROOT / plan.config.run.output_dir, artifacts)
        helper.save(output / "trained-artifact.json", artifact)
        checker()
        require(source_pins() == before, "Student-update source changed before completion.")
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1024]}
        raise
    finally:
        signal.alarm(0)
        after = source_pins()
        helper.save(output / "completion.json", {"schema": "hydra-p7-student-update-completion-v1",
            "profile": PROFILE, "completed": error is None and artifact is not None and before == after,
            "error": error, "source_pins_after": after, "sources_unchanged": before == after,
            "actual_optimizer_steps": None if artifact is None else artifact["actual_optimizer_steps"],
            "optimizer_callbacks_observed": progress.last_optimizer_step,
            "optimizer_callback_count_is_lower_bound_on_failure": True,
            "elapsed_allocation_seconds": time.monotonic() - began,
            "scheduler_queries": checker.calls, "last_live_allocation": checker.last,
            "teacher_rows_added": None if plan is None else plan.dataset.attestation["teacher_rows_added"],
            "base_rows_preserved": BASE_ROWS, "saved_adapter_reload_admission": "required_by_P6_before_inference",
            "heldout_model_evaluation": "separate_unperformed_gate", "teacher_model_calls": 0,
            "native_proof_runs": 0, "automatic_retry": False, "resume": False,
            "actual_outer_process_exit_required": True, "benchmark_claim": False})
    return 0 if before == after else 1


def main(argv=None):
    parser = argparse.ArgumentParser()
    for name in ("reservation", "config", "dataset-manifest", "base-directory", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--reservation-sha256", required=True)
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
