"""Explicit, one-use P6 preparation/submission/release/collection; no defaults.

Only stdlib modules and the adjacent pure control module are imported. Merely
importing this file never contacts SSH, Slurm, a model, a tokenizer or a kernel.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import secrets
import select
import shlex
import subprocess
import sys
import time

import remote_training_control as control

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMPAIGN_FILE = HERE.parent / "campaign.json"
BUNDLE = HERE.parent / "p6-source-bundle-06"
BUNDLE_MANIFEST_SHA = "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96"
BUNDLE_SEAL_SHA = "fe2b602d75c6e2c9a3227bdfc7783717ea6cc546407b1614211322f17071e79b"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
require, canonical, digest = control.require, control.canonical, control.digest


def read(path, expected=None, limit=4 * 1024**2):
    raw = control.ordinary_bytes(path, limit)
    if expected is not None:
        require(type(expected) is str and len(expected) == 64 and digest(raw) == expected, "File pin differs: " + str(path))
    return raw


def put(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= 14 * 1024**2, "Local metadata exceeds its bound.")
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(0o444)


def file_pin(path):
    raw = read(path)
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def evidence(record):
    require(type(record) is dict and set(record) == {"path", "sha256", "format"}, "Evidence needs an exact path/hash/format.")
    relative = Path(record["path"])
    require(not relative.is_absolute() and ".." not in relative.parts and str(relative) == record["path"], "Evidence must stay in this workspace.")
    raw = read(ROOT / relative, record["sha256"])
    require(record["format"] in {"json", "jsonl-last"}, "Unknown evidence format.")
    return json.loads(raw if record["format"] == "json" else raw.rstrip().splitlines()[-1])


def ledger_seconds(ledger):
    """Conservative full reservations, never actual short failure elapsed time."""
    require(ledger.get("schema") == "hydra-implementation-campaign-v1"
            and ledger.get("campaign_gpu_hours_ceiling") == 6 and ledger.get("automatic_retry") is False,
            "Campaign authority/ceiling differs.")
    rows = ledger.get("gpu_reservations")
    require(type(rows) is list and len(rows) <= 64, "Invalid bounded campaign ledger.")
    total, attempts, jobs = 0, set(), set()
    for row in rows:
        require(type(row) is dict and type(row.get("attempt")) is str and row["attempt"] not in attempts,
                "Ambiguous campaign attempt.")
        attempts.add(row["attempt"])
        seconds = control.integer(row.get("seconds"), 1, 21600, "reserved seconds")
        require(type(row.get("gpus")) is int and row["gpus"] == 1, "Only single-GPU campaign rows are admitted.")
        job = row.get("job_id")
        if job is not None:
            require(type(job) is str and control.re.fullmatch(r"[0-9]{1,20}", job) and job not in jobs, "Ambiguous actual job id.")
            jobs.add(job)
        allocated = row.get("allocated_seconds")
        if allocated is not None:
            control.integer(allocated, 0, seconds, "charged seconds")
        zero = row.get("status") == "preflight_stopped_before_sbatch" and allocated == 0 and job is None
        if not zero:
            require(allocated in (None, seconds), "A submitted, failed or uncertain allocation cannot receive an automatic partial refund.")
            total += seconds
    reported = ledger.get("gpu_hours_allocated")
    require(type(reported) in (int, float) and math.isfinite(reported) and 0 <= reported <= 6, "Invalid allocated-hours total.")
    reserved = control.integer(ledger.get("gpu_seconds_reserved"), 0, 21600, "campaign reserved seconds")
    total = max(total, math.ceil(reported * 3600 - 1e-7), reserved)
    require(total <= 21600, "Campaign has exceeded its six-GPU-hour ceiling.")
    return total


def check_charges(ledger, charges):
    """Root must reconcile full immutable charges before any later allocation."""
    rows = {row["attempt"]: row for row in ledger["gpu_reservations"]}
    for charge in charges:
        row = rows.get(charge["attempt"], {})
        require(all(row.get(key) == charge[key] for key in ("attempt", "job_id", "seconds", "allocated_seconds", "reservation_sha256")),
                "Reconcile the existing full release charge into campaign.json before another allocation; no refund/retry.")


def current_ledger(expected, model_key):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    total = ledger_seconds(ledger)
    charges = [json.loads(read(path)) for path in sorted((HERE / "attempts").glob("*/release/charge-intent.json"))]
    require(len(charges) <= 2, "Unexpected local release history.")
    check_charges(ledger, charges)
    target = control.MODELS[model_key]["attempt"]
    require(all(row["attempt"] != target for row in ledger["gpu_reservations"]),
            "This fresh attempt is already in the campaign ledger; do not submit/release it twice.")
    return ledger, raw, total


def bundle_inputs():
    read(BUNDLE / "local-seal.json", BUNDLE_SEAL_SHA)
    manifest = json.loads(read(BUNDLE / "manifest.json", BUNDLE_MANIFEST_SHA))
    launch = json.loads(read(BUNDLE / "training-launch-inputs.json", control.LAUNCH_INPUTS_SHA))
    source_map = json.loads(read(BUNDLE / "controller-source-pins.json"))
    require(digest(canonical(source_map)) == control.SOURCE_MAP_SHA and len(source_map) == 585
            and launch["source_pins_sha256"] == control.SOURCE_MAP_SHA
            and launch["training_controller_sha256"] == control.TRAINER_SHA
            and launch["scheduler_helper_sha256"] == control.SMOKE_SHA
            and launch["provider_sha256"] == control.PROVIDER_SHA
            and manifest["archive_sha256"] == control.ARCHIVE_SHA, "Sealed bundle06 launch bindings differ.")
    return manifest, launch, source_map


def validate_choice(choice):
    required = {"schema", "model_key", "seconds", "soft_limit_seconds", "throughput", "transfer_receipt", "base_admission"}
    require(type(choice) is dict and set(choice) == required and choice["schema"] == "hydra-p6-training-allocation-choice-v1",
            "An explicit reviewed allocation choice is required; unknown keys are rejected.")
    require(choice["model_key"] in control.MODELS, "Only fresh 1.7B or 4B is allowed.")
    control.durations(choice["seconds"], choice["soft_limit_seconds"])


def make_spec(choice, nonce, manifest_content_sha):
    validate_choice(choice)
    model = control.MODELS[choice["model_key"]]
    spec = {"schema": "hydra-p6-fresh-training-allocation-v1", "model_key": choice["model_key"],
        "attempt": model["attempt"], "job_name": "hydra-" + model["attempt"], "nonce": nonce,
        "remote_job_directory": control.CAMPAIGN + "/jobs/" + model["attempt"], "source": control.SOURCE,
        "account": control.ACCOUNT, "partition": control.PARTITION, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": choice["seconds"], "soft_limit_seconds": choice["soft_limit_seconds"],
        "source_archive_sha256": control.ARCHIVE_SHA, "source_pins_sha256": control.SOURCE_MAP_SHA,
        "manifest_content_sha256": manifest_content_sha, "launch_inputs_sha256": control.LAUNCH_INPUTS_SHA,
        "controller_sha256": control.TRAINER_SHA, "scheduler_helper_sha256": control.SMOKE_SHA,
        "provider_sha256": control.PROVIDER_SHA, "dataset_sha256": control.DATA_SHA,
        "config_sha256": model["config_sha256"], "plan_sha256": model["plan_sha256"],
        "training_rows": 2047, "validation_rows": 432, "expected_optimizer_steps": 256,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    control.validate_spec(spec)
    return spec


@contextmanager
def phase_lock():
    # Serializes only these local launchers; root also serializes the overall campaign.
    with (HERE / ".phase.lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def prepare(args):
    choice_raw = read(Path(args.choice).resolve(), args.choice_sha256, 65536)
    choice = json.loads(choice_raw)
    validate_choice(choice)
    manifest, launch, source_map = bundle_inputs()
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, choice["model_key"])
    require(used + choice["seconds"] <= 21600, "The chosen allocation exceeds the remaining full-charge budget.")
    throughput = evidence(choice["throughput"])
    require(throughput.get("schema") == "hydra-completion-gradient-probe-v1"
            and throughput.get("status") == "complete" and throughput.get("max_examples") == 8
            and throughput.get("examples_completed") == throughput.get("forward_calls") == throughput.get("backward_calls") == 8
            and throughput.get("optimizer_steps") == 0 and throughput.get("optimizer_created") is False
            and throughput.get("finite_gradients") is True and throughput.get("trainable_tensors_unchanged") is True
            and throughput.get("model_trained") is False and throughput.get("adapter_saved") is False
            and throughput.get("automatic_retry") is False
            and throughput.get("model") == control.MODELS["qwen3-4b-base"]["model"]
            and throughput.get("plan_sha256") == control.MODELS["qwen3-4b-base"]["plan_sha256"],
            "The required actual eight-example 4B throughput result is not complete; no duration is inferred.")
    transfer = evidence(choice["transfer_receipt"])
    require(transfer.get("actual_ssh_exit_code") == 0 and transfer.get("archive_sha256") == control.ARCHIVE_SHA
            and transfer.get("archive_bytes") == 10257464
            and transfer.get("remote_directory") == str(Path(control.SOURCE).parent),
            "The exact source-data-07 transfer has not completed.")
    base = evidence(choice["base_admission"])
    require(base.get("completed") is True and choice["model_key"] in base.get("models", {}), "Prior exact base admission is missing.")
    identity = base["models"][choice["model_key"]].get("identity", {}).get("base_identity_sha256")
    require(type(identity) is str and control.re.fullmatch(r"[0-9a-f]{64}", identity), "Missing authenticated base identity.")
    model = control.MODELS[choice["model_key"]]
    row = launch["models"][choice["model_key"]]
    require(row["plan_sha256"] == model["plan_sha256"] and row["config_sha256"] == model["config_sha256"]
            and row["training_rows"] == 2047 and row["expected_optimizer_steps"] == 256
            and row["future_artifact_directory"] == model["artifact"], "Prepared training exposure differs.")
    plan = ROOT / row["prepared_plan"]["path"]
    read(plan, row["prepared_plan"]["sha256"])
    directory = HERE / "attempts" / model["attempt"]
    directory.mkdir(parents=True, exist_ok=False)
    spec = make_spec(choice, secrets.token_hex(16), digest(canonical(manifest)))
    put(directory / "choice.json", choice)
    put(directory / "prepare-ledger.json", ledger)
    put(directory / "source-map.json", source_map)
    prepared = {"schema": "hydra-p6-prepared-training-launch-v1", "status": "prepared_not_submitted",
        "spec": spec, "choice": file_pin(directory / "choice.json"), "original_choice_sha256": digest(choice_raw),
        "ledger_read_sha256": digest(ledger_raw), "full_seconds_charged_or_reserved_before": used,
        "full_seconds_after_potential_release": used + spec["seconds"], "base_identity_sha256": identity,
        "launcher_sources": {name: file_pin(HERE / name) for name in ("training_launchers.py", "remote_training_control.py")},
        "prepared_plan": row["prepared_plan"], "automatic_retry": False, "automatic_launch": False}
    put(directory / "prepared.json", prepared)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(control.job_script(spec))
    (directory / "job.sbatch").chmod(0o444)
    print(json.dumps({"prepared": file_pin(directory / "prepared.json"), "model_key": spec["model_key"],
        "seconds": spec["seconds"], "soft_limit_seconds": spec["soft_limit_seconds"], "ssh_calls": 0, "allocations": 0}))


def load_prepared(model_key, expected):
    directory = HERE / "attempts" / control.MODELS[model_key]["attempt"]
    prepared = json.loads(read(directory / "prepared.json", expected))
    spec = prepared["spec"]
    control.validate_spec(spec)
    require(spec["model_key"] == model_key, "Wrong prepared model.")
    for name in ("training_launchers.py", "remote_training_control.py"):
        require(file_pin(HERE / name) == prepared["launcher_sources"][name], "Launcher source changed since preparation.")
    read(directory / "choice.json", prepared["choice"]["sha256"])
    manifest, _, source_map = bundle_inputs()
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"]
            and json.loads(read(directory / "source-map.json")) == source_map, "Prepared source map changed.")
    return directory, prepared, spec, source_map


def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 600-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_training_control.py", limit=65536).decode()
    argv = SSH + ["/usr/bin/env " + shlex.quote("LD_LIBRARY_PATH=" + LOGIN_PYTHON_LIB)
                  + " " + shlex.quote(LOGIN_PYTHON) + " -I -B -c " + shlex.quote(code)]
    process, output, offset, started = None, bytearray(), 0, time.monotonic()
    receipt = {"actual_ssh_exit_code": None, "ssh_attempted": False, "owned_child_reaped": False,
        "stop_reason": None, "automatic_retry": False, "remote_script_sha256": digest(code.encode())}
    limit = 14 * 1024**2
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        receipt["ssh_attempted"] = True
        os.set_blocking(process.stdin.fileno(), False)
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            if time.monotonic() - started >= 600:
                receipt["stop_reason"] = "ssh_wall_limit"
                break
            readable, writable, _ = select.select([] if eof else [process.stdout],
                [process.stdin] if offset < len(raw) else [], [], 0.05)
            if writable:
                offset += os.write(process.stdin.fileno(), raw[offset:offset + 16384])
                if offset == len(raw):
                    process.stdin.close()
            if readable:
                chunk = os.read(process.stdout.fileno(), min(65536, limit + 1 - len(output)))
                if chunk:
                    output.extend(chunk)
                    if len(output) > limit:
                        receipt["stop_reason"] = "ssh_output_limit"
                        break
                else:
                    eof = True
    except BaseException as exc:
        receipt["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:1024]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                receipt["actual_ssh_exit_code"] = process.wait(timeout=3)
                receipt["owned_child_reaped"] = True
            except subprocess.TimeoutExpired:
                receipt["stop_reason"] = "ssh_child_not_reaped"
            for pipe in (process.stdin, process.stdout):
                if pipe and not pipe.closed:
                    pipe.close()
        receipt.update(elapsed_seconds=time.monotonic() - started, input_bytes_sent=offset,
                       output_bytes_retained=min(limit, len(output)), output_complete=len(output) <= limit)
    return bytes(output[:limit]), receipt


def execute_phase(directory, payload):
    put(directory / "request.json", payload)
    output, receipt = ssh_once(payload)
    with (directory / "transport.stdout").open("xb") as stream:
        stream.write(output)
    (directory / "transport.stdout").chmod(0o444)
    put(directory / "transport-completion.json", receipt)
    require(receipt["actual_ssh_exit_code"] == 0 and receipt["owned_child_reaped"] and receipt["stop_reason"] is None,
            "The single SSH attempt failed or was uncertain; preserve it and do not retry.")
    response = json.loads(output)
    require(response.get("completed") is True and response.get("phase") == payload["phase"], "Remote phase did not complete.")
    put(directory / "response.json", response)
    return response["result"]


def mutate_phase(args):
    directory, prepared, spec, source_map = load_prepared(args.model_key, args.prepared_sha256)
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.model_key)
    require(used + spec["seconds"] <= 21600, "The full new allocation exceeds the remaining campaign budget.")
    phase_dir = directory / args.action
    phase_dir.mkdir(exist_ok=False)
    put(phase_dir / "ledger-snapshot.json", ledger)
    payload = {"phase": args.action, "spec": spec, "source_map": source_map}
    if args.action == "release":
        submit_receipt = json.loads(read(directory / "submit/transport-completion.json"))
        require(submit_receipt["actual_ssh_exit_code"] == 0 and submit_receipt["stop_reason"] is None
                and submit_receipt["owned_child_reaped"] is True, "Held submission transport did not complete.")
        submission = json.loads(read(directory / "submit/response.json"))["result"]
        require(submission["actual_sbatch_exit_code"] == 0 and submission["held"] is True
                and submission["released"] is False, "Held submission was not confirmed.")
        record = control.reservation(spec, submission["job_id"], submission["uid"])
        put(phase_dir / "reservation.json", record)
        # Full charge happens BEFORE the only release SSH attempt; never refund automatically.
        charge = {"schema": "hydra-p6-full-release-charge-v1", "attempt": spec["attempt"],
            "job_id": record["job_id"], "gpus": 1, "seconds": spec["seconds"], "allocated_seconds": spec["seconds"],
            "reservation_sha256": digest(canonical(record) + b"\n"), "status": "release_requested_or_uncertain",
            "ledger_before_sha256": digest(ledger_raw), "seconds_before": used, "seconds_after": used + spec["seconds"],
            "refund_allowed_automatically": False, "automatic_retry": False}
        put(phase_dir / "charge-intent.json", charge)
        payload["reservation"] = record
    put(phase_dir / "phase-intent.json", {"action": args.action, "prepared_sha256": args.prepared_sha256,
        "ledger_sha256": digest(ledger_raw), "source_pins_sha256": control.SOURCE_MAP_SHA,
        "automatic_retry": False, "one_use": True})
    result = execute_phase(phase_dir, payload)
    print(json.dumps({"phase": args.action, "result": result, "campaign_file_modified": False,
        "next_phase_automatic": False}, sort_keys=True))


def complete_json(observation, name):
    row = observation["files"].get(name)
    if row is None or row["complete_file"] is not True or row["stable"] is not True:
        return None
    return json.loads(control.base64.b64decode(row["base64"], validate=True))


def progress_snapshot(observation):
    row = observation["files"].get("job/result/progress.jsonl")
    if row is None:
        return None
    raw = control.base64.b64decode(row["base64"], validate=True)
    lines = raw.splitlines()
    if row["offset"] and lines:
        lines = lines[1:]  # The first retained line may begin in the middle of JSON.
    if not raw.endswith(b"\n") and lines:
        lines = lines[:-1]
    events = []
    for line in lines:
        if len(line) <= 8192:
            try:
                event = json.loads(line)
                if type(event) is dict:
                    events.append(event)
            except ValueError:
                pass
    steps = [event["step"] for event in events if event.get("kind") == "optimizer-step"
             and type(event.get("step")) is int and 1 <= event["step"] <= 256]
    return {"stable_file_during_read": row["stable"], "complete_file": row["complete_file"],
        "last_event": None if not events else {key: events[-1].get(key) for key in ("kind", "step", "elapsed_seconds")},
        "last_optimizer_step_seen": max(steps) if steps else None,
        "interpretation": "Bounded log snapshot only; a seen step is not complete training or reload evidence."}


def summarize(observation, spec, record, expected_base_identity=None):
    """Metadata-only admission; no saved tensor reload or quality claim."""
    summary = {"job_id": record["job_id"], "status": "in_progress_or_incomplete_evidence",
        "saved_artifact_metadata_complete": False, "adapter_reload_admitted": False, "quality_evaluated": False,
        "optimizer_steps_observed": None, "actual_optimizer_steps_in_complete_artifact": None,
        "errors": [], "automatic_retry": False}
    try:
        summary["progress_snapshot"] = progress_snapshot(observation)
        completion = complete_json(observation, "job/result/completion.json")
        if completion:
            summary.update({key: completion.get(key) for key in ("optimizer_steps_observed", "actual_optimizer_steps_in_complete_artifact")})
            summary["controller_completed"] = completion.get("completed")
            summary["controller_error"] = completion.get("error")
        sacct = observation["scheduler"]["sacct"]
        require(sacct["actual_exit_code"] == 0 and sacct["stop_reason"] is None, "Actual accounting query is unavailable.")
        rows = [line.split("|") for line in sacct["stdout_stderr"].splitlines() if line.split("|", 1)[0] == record["job_id"]]
        require(len(rows) == 1 and len(rows[0]) == 14, "Exact allocation accounting record is unavailable.")
        row = rows[0]
        require(row[1:5] == [spec["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION], "Allocation accounting identity differs.")
        summary.update(slurm_state=row[5], slurm_exit_code=row[6], actual_scheduler_elapsed_seconds=row[7])
        if row[5] not in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
            return summary
        summary["status"] = "terminal_failed_or_incomplete_evidence"
        require(row[5] == "COMPLETED" and row[6] == "0:0" and row[8] == str(spec["seconds"] // 60)
                and row[9] == "8", "Slurm did not report exact successful allocation completion.")
        allocated = control.tres(row[12])
        require(allocated.get("gres/gpu") == "1" and allocated.get("cpu") == "8" and allocated.get("node") == "1"
                and allocated.get("mem") in {"64G", "65536M"}, "Final allocated resources differ.")
        exit_row = observation["files"].get("job/actual-process-exit.txt", {})
        require(exit_row.get("complete_file") is True and control.base64.b64decode(exit_row["base64"], validate=True).strip() == b"0",
                "Actual training process exit 0 is missing.")
        require(completion and completion.get("schema") == "hydra-p6-remote-training-completion-v1"
                and completion.get("completed") is True and completion.get("error") is None
                and completion.get("sources_unchanged") is True and completion.get("execute_invoked") is True
                and completion.get("optimizer_steps_observed") == 256
                and completion.get("actual_optimizer_steps_in_complete_artifact") == 256
                and completion.get("automatic_retry") is False and completion.get("resume") is False,
                "Training completion/source/step evidence is incomplete.")
        request = complete_json(observation, "job/result/request.json")
        require(request and request.get("reservation") == record
                and request.get("reservation_sha256") == digest(canonical(record) + b"\n")
                and request.get("source_pins_before") == completion.get("source_pins_after")
                and digest(canonical(request.get("source_pins_before"))) == control.SOURCE_MAP_SHA,
                "Controller request/source scope is not bound to this reservation.")
        manifest = complete_json(observation, "artifact/manifest.json")
        artifact = complete_json(observation, "job/result/artifact-receipt.json")
        require("artifact/incomplete.json" not in observation["files"], "An incomplete artifact marker is present.")
        require(artifact == completion.get("training_artifact") and type(artifact) is dict,
                "Completion and saved artifact receipts disagree.")
        require(manifest and manifest.get("schema") == "hydra-decision-pilot-artifact-v1"
                and manifest.get("profile") == "hydra-fresh-decision-pilot-v2"
                and manifest.get("model_trained") is True and manifest.get("actual_optimizer_steps") == 256
                and manifest.get("model") == control.MODELS[spec["model_key"]]["model"]
                and manifest.get("automatic_retry") is False and manifest.get("resume") is False,
                "Saved artifact identity or update evidence differs.")
        require(observation["files"]["artifact/manifest.json"]["sha256"] == artifact.get("manifest_sha256")
                and manifest.get("plan", {}).get("plan_sha256") == spec["plan_sha256"]
                and digest(canonical({key: value for key, value in manifest["plan"].items() if key != "plan_sha256"})) == spec["plan_sha256"],
                "Saved manifest/plan hash differs.")
        require(artifact.get("manifest_path") == control.MODELS[spec["model_key"]]["artifact"] + "/manifest.json"
                and artifact.get("actual_optimizer_steps") == 256
                and artifact.get("base_identity_sha256") == manifest.get("base", {}).get("base_identity_sha256")
                and (expected_base_identity is None or artifact.get("base_identity_sha256") == expected_base_identity)
                and artifact.get("saved_adapter_reload_admission") == manifest.get("saved_adapter_reload_admission")
                == "required_by_P6_before_inference", "Artifact path/base/reload requirement differs.")
        audit, update = manifest.get("finite_gradient_audit", {}), manifest.get("adapter_update", {})
        require(all(audit.get(key) == 256 for key in ("expected_optimizer_boundaries", "observed_optimizer_boundaries",
                "raw_finite_optimizer_boundaries", "post_clip_finite_optimizer_boundaries"))
                and audit.get("first_optimizer_step") == 1 and audit.get("last_optimizer_step") == 256,
                "Finite-gradient audit does not cover all 256 optimizer boundaries.")
        require(type(update.get("changed_parameter_tensors")) is int and update["changed_parameter_tensors"] > 0
                and update.get("initial_tensor_population_sha256") != update.get("final_tensor_population_sha256")
                and update.get("trainable_parameter_tensors") == update.get("final_finite_parameter_tensors")
                and artifact.get("finite_gradient_audit") == audit and artifact.get("adapter_update") == update,
                "Adapter update audit is incomplete or inconsistent.")
        summary.update(status="complete_saved_artifact_metadata_requires_fresh_reload",
            saved_artifact_metadata_complete=True, manifest_sha256=artifact["manifest_sha256"],
            finite_gradient_boundaries=256, changed_parameter_tensors=update["changed_parameter_tensors"])
    except (ValueError, KeyError, TypeError) as exc:
        summary["errors"].append(str(exc)[:1024])
    return summary


def collect(args):
    directory, prepared, spec, _ = load_prepared(args.model_key, args.prepared_sha256)
    record = json.loads(read(directory / "release/reservation.json"))
    output = directory / ("observation-" + str(args.index).zfill(3))
    output.mkdir(exist_ok=False)
    observation = execute_phase(output, {"phase": "collect", "spec": spec, "reservation": record})
    require(observation.get("job_id") == record["job_id"] and observation.get("read_only") is True, "Wrong observation identity.")
    require(set(observation["files"]) <= set(control.FILES), "Observation contains an unapproved path.")
    total = 0
    for name, row in observation["files"].items():
        raw = control.base64.b64decode(row["base64"], validate=True)
        total += len(raw)
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"] and total <= control.MAX_OBSERVATION,
                "Collected byte evidence differs or exceeds bounds.")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        target.chmod(0o444)
    summary = summarize(observation, spec, record, prepared["base_identity_sha256"])
    for row in observation["files"].values():
        row.pop("base64")
    put(output / "observation.json", observation)
    put(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--choice", required=True)
    prep.add_argument("--choice-sha256", required=True)
    prep.add_argument("--ledger-sha256", required=True)
    for action in ("submit", "release", "collect"):
        sub = subs.add_parser(action)
        sub.add_argument("--model-key", choices=tuple(control.MODELS), required=True)
        sub.add_argument("--prepared-sha256", required=True)
        if action == "collect":
            sub.add_argument("--index", type=int, choices=range(1, 129), required=True)
        else:
            sub.add_argument("--ledger-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    with phase_lock():
        if args.action == "prepare":
            prepare(args)
        elif args.action == "collect":
            collect(args)
        else:
            mutate_phase(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
