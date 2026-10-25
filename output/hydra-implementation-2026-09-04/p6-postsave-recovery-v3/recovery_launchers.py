"""Explicit one-use saved 1.7B recovery phases; no work on import.

prepare is local metadata only. submit/release/collect each make at most one
bounded SSH call, only when root explicitly invokes that phase. No retries.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
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

import gpu_saved_reload as reload_check
import remote_recovery_control as control

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMPAIGN_FILE = HERE.parent / "campaign.json"
BUNDLE = HERE.parent / "p6-source-bundle-08"
BUNDLE_MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
require, canonical, digest = control.require, control.canonical, control.digest
SOURCES = ("gpu_saved_reload.py", "metadata_recovery.py", "remote_recovery_control.py", "recovery_launchers.py")
CHARGE_GLOBS = (
    "p6-training-launchers-v*/attempts/*/release/charge-intent.json",
    "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
    "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
    "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
    "p6-postsave-recovery-v*/attempts/*/release/charge-intent.json",
)


def current_ledger(expected):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    used = ledger_seconds(ledger)
    paths = sorted({p for pattern in CHARGE_GLOBS for p in HERE.parent.glob(pattern)})
    require(len(paths) <= 64, "Cross-family release history exceeds its finite bound.")
    check_charges(ledger, [json.loads(read(p)) for p in paths])
    require(all(row["attempt"] != control.ATTEMPT for row in ledger["gpu_reservations"]),
            "Recovery already appears in the ledger; no second submission/release.")
    originals = [r for r in ledger["gpu_reservations"] if r.get("job_id") == control.ORIGINAL_JOB]
    require(len(originals) == 1 and originals[0].get("seconds") == 1200
            and originals[0].get("allocated_seconds") == 1200,
            "The failed original allocation must remain fully charged before recovery.")
    require(used + 300 <= 21600, "Recovery exceeds the six-GPU-hour full-reservation ceiling.")
    return ledger, raw, used


def input_metadata(metadata_sha, actual_sha):
    raw = read(HERE / "metadata-recovery-base3.json", metadata_sha, 2 * 1024**2)
    actual = read(HERE / "metadata-actual-completion-base3.json", actual_sha, 65536)
    read(HERE / "metadata_recovery.py", control.METADATA_VERIFIER_SHA, 65536)
    read(HERE / "gpu_saved_reload.py", control.CONTROLLER_SHA, 65536)
    reload_check.validate_metadata(json.loads(raw), json.loads(actual), metadata_sha, control.METADATA_VERIFIER_SHA)
    return raw, actual


def bundle_inputs():
    manifest = json.loads(read(BUNDLE / "manifest.json", BUNDLE_MANIFEST_SHA))
    source_map = json.loads(read(BUNDLE / "controller-source-pins.json"))
    require(manifest.get("archive_sha256") == control.ARCHIVE_SHA and len(source_map) == 585
            and digest(canonical(source_map)) == control.SOURCE_MAP_SHA
            and manifest.get("inference_only") is True and manifest.get("training_execution_allowed") is False,
            "The new inference-only runtime09 bundle binding differs.")
    require(json.loads(read(HERE / "runtime-source-pins-base3.json")) == source_map,
            "Recovery runtime source-map copy differs from bundle08.")
    training_map = json.loads(read(HERE / "controller-source-pins.json"))
    reload_check.validate_source_maps(training_map, source_map)
    return manifest, source_map


def make_spec(nonce, metadata_sha, actual_sha, manifest_content_sha):
    spec = {"schema": "hydra-p6-saved-reload-allocation-v2", "attempt": control.ATTEMPT,
        "job_name": "hydra-" + control.ATTEMPT, "model_key": control.MODEL_KEY, "nonce": nonce,
        "remote_job_directory": control.CAMPAIGN + "/jobs/" + control.ATTEMPT, "source": control.SOURCE,
        "account": control.ACCOUNT, "partition": control.PARTITION, "gpus": 1, "nodes": 1,
        "cpus": 8, "memory_gib": 64, "seconds": 300, "soft_limit_seconds": 240,
        "source_archive_sha256": control.ARCHIVE_SHA, "source_pins_sha256": control.SOURCE_MAP_SHA,
        "training_source_root": control.TRAINING_SOURCE, "training_source_pins_sha256": control.TRAINING_SOURCE_MAP_SHA,
        "training_provider_sha256": control.TRAINING_PROVIDER_SHA, "runtime_manifest_sha256": control.RUNTIME_MANIFEST_SHA,
        "manifest_content_sha256": manifest_content_sha, "controller_sha256": control.CONTROLLER_SHA,
        "metadata_verifier_sha256": control.METADATA_VERIFIER_SHA,
        "metadata_receipt_sha256": metadata_sha, "metadata_actual_sha256": actual_sha,
        "provider_sha256": control.PROVIDER_SHA, "scheduler_helper_sha256": control.SMOKE_SHA,
        "artifact_manifest_sha256": control.MANIFEST_SHA, "final_tensor_population_sha256": control.FINAL_TENSOR_SHA,
        "original_job_id": control.ORIGINAL_JOB, "generation_calls": 0, "optimizer_updates": 0,
        "native_calls": 0, "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    control.validate_spec(spec)
    return spec


def prepare(args):
    input_metadata(args.metadata_sha256, args.metadata_actual_sha256)
    manifest, source_map = bundle_inputs()
    ledger, raw, used = current_ledger(args.ledger_sha256)
    spec = make_spec(secrets.token_hex(16), args.metadata_sha256,
                     args.metadata_actual_sha256, digest(canonical(manifest)))
    directory = HERE / "attempts" / control.ATTEMPT
    directory.mkdir(parents=True, exist_ok=False)
    put(directory / "prepare-ledger.json", ledger)
    put(directory / "source-map.json", source_map)
    prepared = {"schema": "hydra-p6-prepared-saved-recovery-v2", "status": "prepared_not_submitted",
        "spec": spec, "ledger_sha256": digest(raw), "full_seconds_before": used,
        "full_seconds_after_potential_release": used + 300,
        "launcher_sources": {name: file_pin(HERE / name) for name in SOURCES},
        "automatic_launch": False, "automatic_retry": False}
    put(directory / "prepared.json", prepared)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(control.job_script(spec))
    (directory / "job.sbatch").chmod(0o444)
    print(json.dumps({"prepared": file_pin(directory / "prepared.json"), "ssh_calls": 0, "allocations": 0}))


def load_prepared(expected, *, recheck_metadata=True):
    directory = HERE / "attempts" / control.ATTEMPT
    prepared = json.loads(read(directory / "prepared.json", expected))
    require(prepared.get("schema") == "hydra-p6-prepared-saved-recovery-v2", "Prepared recovery schema differs.")
    spec = control.validate_spec(prepared["spec"])
    for name in SOURCES:
        require(file_pin(HERE / name) == prepared["launcher_sources"][name], "Recovery sources changed since preparation.")
    manifest, source_map = bundle_inputs()
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"]
            and json.loads(read(directory / "source-map.json")) == source_map, "Prepared source scope changed.")
    if recheck_metadata:
        input_metadata(spec["metadata_receipt_sha256"], spec["metadata_actual_sha256"])
    return directory, prepared, spec, source_map


def mutate_phase(args):
    directory, _, spec, source_map = load_prepared(args.prepared_sha256)
    ledger, raw, used = current_ledger(args.ledger_sha256)
    phase_dir = directory / args.action
    phase_dir.mkdir(exist_ok=False)
    put(phase_dir / "ledger-snapshot.json", ledger)
    payload = {"phase": args.action, "spec": spec, "source_map": source_map}
    if args.action == "release":
        receipt = json.loads(read(directory / "submit/transport-completion.json"))
        require(receipt.get("actual_ssh_exit_code") == 0 and receipt.get("owned_child_reaped") is True
                and receipt.get("output_complete") is True and receipt.get("stop_reason") is None,
                "Held submission transport was not completed.")
        submission = json.loads(read(directory / "submit/response.json"))["result"]
        require(submission["actual_sbatch_exit_code"] == 0 and submission["held"] is True
                and submission["released"] is False, "Exact held submission is not confirmed.")
        record = control.reservation(spec, submission["job_id"], submission["uid"])
        put(phase_dir / "reservation.json", record)
        # Immutable full charge is written BEFORE any release SSH invocation.
        put(phase_dir / "charge-intent.json", {"schema": "hydra-p6-full-release-charge-v1",
            "attempt": control.ATTEMPT, "job_id": record["job_id"], "gpus": 1, "seconds": 300,
            "allocated_seconds": 300, "reservation_sha256": digest(canonical(record) + b"\n"),
            "status": "release_requested_or_uncertain", "ledger_before_sha256": digest(raw),
            "seconds_before": used, "seconds_after": used + 300,
            "refund_allowed_automatically": False, "automatic_retry": False})
        payload["reservation"] = record
    result = execute_phase(phase_dir, payload)
    print(json.dumps({"phase": args.action, "result": result, "automatic_next_phase": False}))


def summarize(observation, spec, record, source_map):
    summary = {"job_id": record["job_id"], "original_job_id": control.ORIGINAL_JOB,
        "original_training_status": "FAILED 1:0", "status": "in_progress_or_incomplete_evidence",
        "saved_adapter_reload_admitted": False, "quality_evaluated": False,
        "errors": [], "automatic_retry": False}
    try:
        sacct = observation["scheduler"]["sacct"]
        require(sacct["actual_exit_code"] == 0 and sacct["stop_reason"] is None,
                "Actual accounting query unavailable.")
        rows = [line.split("|") for line in sacct["stdout_stderr"].splitlines()
                if line.split("|", 1)[0] == record["job_id"]]
        require(len(rows) == 1 and len(rows[0]) == 14, "Exact actual allocation record unavailable.")
        row = rows[0]
        require(row[1:5] == [spec["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION],
                "Actual recovery allocation identity differs.")
        summary.update(slurm_state=row[5], slurm_exit_code=row[6], actual_scheduler_elapsed_seconds=row[7])
        if row[5] not in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
            return summary
        summary["status"] = "terminal_failed_or_incomplete_evidence"
        require(row[5] == "COMPLETED" and row[6] == "0:0" and row[8] == "5" and row[9] == "8",
                "Recovery did not finish with actual Slurm COMPLETED 0:0 at its fixed cap.")
        allocated = control.tres(row[12])
        require(allocated.get("gres/gpu") == "1" and allocated.get("cpu") == "8" and allocated.get("node") == "1"
                and allocated.get("mem") in {"64G", "65536M"}, "Final recovery resources differ.")
        process = observation["files"].get("job/actual-process-exit.txt", {})
        require(process.get("complete_file") is True and process.get("stable") is True
                and control.base64.b64decode(process["base64"], validate=True).strip() == b"0",
                "Actual recovery process exit0 is missing.")
        require(complete_json(observation, "job/reservation.json") == record, "Observed reservation differs.")
        claim = complete_json(observation, "job/reservation.json.claimed")
        require(claim and claim.get("schema") == "hydra-p6-saved-reload-consumption-v2"
                and claim.get("job_id") == record["job_id"] and claim.get("nonce") == record["nonce"]
                and claim.get("reservation_sha256") == digest(canonical(record) + b"\n"), "One-use claim differs.")
        request = complete_json(observation, "job/result/request.json")
        require(request and request.get("schema") == "hydra-p6-saved-reload-request-v2"
                and request.get("reservation") == record and request.get("source_pins_before") == source_map,
                "Actual runtime request/source scope differs.")
        identities = {"runtime_source_root": control.SOURCE, "runtime_provider_sha256": control.PROVIDER_SHA,
            "runtime_source_pins_sha256": control.SOURCE_MAP_SHA,
            "training_source_root": control.TRAINING_SOURCE, "training_provider_sha256": control.TRAINING_PROVIDER_SHA,
            "training_source_pins_sha256": control.TRAINING_SOURCE_MAP_SHA}
        require(all(request.get(key) == expected for key, expected in identities.items()),
                "Runtime request conflates original training with the new inference provider.")
        result = complete_json(observation, "job/result/completion.json")
        require(result and result.get("schema") == "hydra-p6-saved-reload-completion-v2"
                and result.get("completed") is True and result.get("error") is None
                and result.get("job_id") == record["job_id"] and result.get("original_job_id") == control.ORIGINAL_JOB
                and result.get("original_failed_job_preserved") is True
                and result.get("original_slurm_state") == "FAILED" and result.get("original_slurm_exit_code") == "1:0"
                and result.get("sources_and_artifact_unchanged") is True and result.get("model_disposal_completed") is True
                and result.get("saved_adapter_reload_checked") is True and result.get("resaved_manifest") is False
                and result.get("automatic_retry") is False, "Separate reload completion evidence is missing or inconsistent.")
        require(all(result.get(key) == expected for key, expected in identities.items())
                and result.get("runtime_manifest_sha256") == control.RUNTIME_MANIFEST_SHA,
                "Recovery completion lacks the exact original/runtime source distinction.")
        for key in ("metadata_receipt_sha256", "metadata_actual_sha256", "controller_sha256", "provider_sha256",
                    "source_pins_sha256", "artifact_manifest_sha256", "final_tensor_population_sha256"):
            require(result.get(key) == spec[key], "Recovery completion input binding differs: " + key)
        require(all(type(result.get(k)) is int and result[k] == 0
                    for k in ("generation_calls", "optimizer_updates", "native_calls", "solver_calls")),
                "Recovery exceeded its no-computation contract.")
        loaded = complete_json(observation, "job/result/loaded-model.json")
        reload_check.validate_loaded_report(loaded, record["job_id"])
        before = complete_json(observation, "job/result/artifact-before.json")
        after = complete_json(observation, "job/result/artifact-after.json")
        require(before and before == after and before.get("manifest.json", {}).get("sha256") == control.MANIFEST_SHA,
                "Original artifact bytes were not preserved.")
        require(loaded["identity"]["adapter"]["base_identity_admission"]["config_file"]
                == before.get("adapter/adapter_config.json"), "Reloaded config evidence differs from the unchanged saved file.")
        summary.update(status="saved_adapter_independent_reload_complete", saved_adapter_reload_admitted=True,
            manifest_sha256=control.MANIFEST_SHA, final_tensor_population_sha256=control.FINAL_TENSOR_SHA,
            actual_process_exit_code=0, generation_calls=0, optimizer_updates=0, native_calls=0,
            reload_elapsed_seconds=loaded.get("reload_elapsed_seconds"), elapsed_seconds=result["elapsed_seconds"],
            **identities, runtime_manifest_sha256=control.RUNTIME_MANIFEST_SHA)
    except (KeyError, TypeError, ValueError) as error:
        summary["errors"].append(type(error).__name__ + ": " + str(error)[:1500])
    return summary


def collect(args):
    directory, _, spec, source_map = load_prepared(args.prepared_sha256, recheck_metadata=False)
    record = json.loads(read(directory / "release/reservation.json"))
    require(record == control.reservation(spec, record.get("job_id"), control.UID), "Collection reservation differs.")
    control.integer(args.index, 1, 999, "new observation index")
    output = directory / ("observation-" + str(args.index).zfill(3))
    output.mkdir(exist_ok=False)
    observation = execute_phase(output, {"phase": "collect", "spec": spec, "reservation": record})
    validate_observation(observation)
    put(output / "observation.json", observation)
    for name, row in observation["files"].items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(control.base64.b64decode(row["base64"], validate=True))
        target.chmod(0o444)
    summary = summarize(observation, spec, record, source_map)
    put(output / "summary.json", summary)
    print(json.dumps({"observation_succeeded": True, "recovery": summary,
        "collection_exit_is_not_recovery_success": True, "automatic_next_phase": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    preparation = sub.add_parser("prepare")
    for name in ("metadata-sha256", "metadata-actual-sha256", "ledger-sha256"):
        preparation.add_argument("--" + name, required=True)
    for action in ("submit", "release"):
        child = sub.add_parser(action)
        child.add_argument("--prepared-sha256", required=True)
        child.add_argument("--ledger-sha256", required=True)
    observation = sub.add_parser("collect")
    observation.add_argument("--prepared-sha256", required=True)
    observation.add_argument("--index", type=int, required=True)
    args = parser.parse_args()
    try:
        with phase_lock():
            if args.action == "prepare":
                prepare(args)
            elif args.action in {"submit", "release"}:
                mutate_phase(args)
            else:
                collect(args)
        return 0
    except BaseException as error:
        print(json.dumps({"completed": False, "error_type": type(error).__name__, "error": str(error)[:1500],
            "automatic_retry": False, "uncertain_remote_mutation_is_not_refunded": True}))
        return 1


# Exact reviewed helper copies are appended by derive_helpers.py, before main.

# BEGIN EXACT REVIEWED HELPERS
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

@contextmanager
def phase_lock():
    # Serializes only these local launchers; root also serializes the overall campaign.
    with (HERE / ".phase.lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)

def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 600-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_recovery_control.py", limit=65536).decode()
    argv = SSH + ["/usr/bin/env " + shlex.quote("LD_LIBRARY_PATH=" + LOGIN_PYTHON_LIB)
                  + " " + shlex.quote(LOGIN_PYTHON) + " -I -B -c " + shlex.quote(code)]
    process, output, offset, started = None, bytearray(), 0, time.monotonic()
    eof = False
    receipt = {"actual_ssh_exit_code": None, "ssh_attempted": False, "owned_child_reaped": False,
        "stop_reason": None, "automatic_retry": False, "remote_script_sha256": digest(code.encode())}
    limit = control.MAX_RESPONSE
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
                       output_bytes_retained=min(limit, len(output)), output_complete=bool(eof and offset == len(raw) and receipt["stop_reason"] is None and len(output) <= limit),
                       remote_outcome="reported_in_response" if receipt["stop_reason"] is None
                           and receipt["actual_ssh_exit_code"] == 0 and eof else "unknown")
    return bytes(output[:limit]), receipt

def execute_phase(directory, payload):
    put(directory / "request.json", payload)
    output, receipt = ssh_once(payload)
    with (directory / "transport.stdout").open("xb") as stream:
        stream.write(output)
    (directory / "transport.stdout").chmod(0o444)
    put(directory / "transport-completion.json", receipt)
    require(receipt["actual_ssh_exit_code"] == 0 and receipt["owned_child_reaped"] is True
            and receipt["output_complete"] is True and receipt["stop_reason"] is None,
            "The single SSH attempt failed or is uncertain; preserve it and do not retry.")
    response = json.loads(output)
    require(response.get("schema") == "hydra-p6-saved-recovery-control-phase-v1" and response.get("completed") is True
            and response.get("phase") == payload["phase"] and response.get("error") is None,
            "Remote phase did not complete.")
    put(directory / "response.json", response)
    return response["result"]

def complete_json(observation, name):
    row = observation["files"].get(name)
    if row is None or row["complete_file"] is not True or row["stable"] is not True:
        return None
    return json.loads(control.base64.b64decode(row["base64"], validate=True))

def validate_observation(observation, *, allowed=None):
    require(type(observation) is dict and observation.get("read_only") is True
            and type(observation.get("files")) is dict and set(observation["files"]) <= set(allowed or control.FILES),
            "Unexpected observation files.")
    total = 0
    for row in observation["files"].values():
        raw = control.base64.b64decode(row["base64"], validate=True)
        total += len(raw)
        require(type(row["bytes"]) is int and len(raw) == row["bytes"] and digest(raw) == row["sha256"]
                and len(raw) <= 2 * 1024**2 and total <= control.MAX_OBSERVATION, "Observation bytes differ or exceed limits.")


if __name__ == "__main__":
    raise SystemExit(main())
