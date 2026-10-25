"""Fixed held/release/collection recipe for the single saved 1.7B recovery.

Only metadata and scheduler operations run on the login node. Original P6-v2
queue, process and phase helpers are copied unchanged below, with provenance.
"""
from __future__ import annotations

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import select
import shlex
import signal
import stat
import subprocess
import sys
import time

PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
TRAINING_SOURCE = CAMPAIGN + "/bundles/source-data-07/source"
SOURCE = CAMPAIGN + "/bundles/source-data-09/source"
PACKAGE = CAMPAIGN + "/recovery/p6-postsave-recovery-v1"
ATTEMPT = "p6-saved-recovery-1.7b-import4-01"
MODEL_KEY = "qwen3-1.7b-base"
ORIGINAL_JOB = "21912020"
UID = 105923
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
REMOTE_USER = "plgnasqret"
ARCHIVE_SHA = "186b7eae5bc6388044a2618353f014f95486e86ed2cd1483978d177570525ddc"
TRAINING_SOURCE_MAP_SHA = "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
SOURCE_MAP_SHA = "85dadd08b91c9678fa8be1cf9624a82a5e0470b1c29f5a2f8cc25c7716a76f55"
TRAINING_PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
PROVIDER_SHA = "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44"
RUNTIME_MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
MANIFEST_SHA = "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135"
FINAL_TENSOR_SHA = "2499801811ee63fb4f6c20e022d59aa0eeb2bb202ee41c9edd6bcd271e646c3c"
ARTIFACT = TRAINING_SOURCE + "/output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01"
BASE = CAMPAIGN + "/authenticated-bases-01/" + MODEL_KEY
CONTROLLER_SHA = 'b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6'
METADATA_VERIFIER_SHA = 'aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16'
MAX_INPUT = 256 * 1024
MAX_COMMAND_OUTPUT = 65536
MAX_OBSERVATION = 8 * 1024**2
MAX_RESPONSE = 14 * 1024**2
PHASE_WALL = 550.0
SACCT_FORMAT = ("JobIDRaw,JobName%100,User,Account,Partition,State,ExitCode,ElapsedRaw,"
                "TimelimitRaw,AllocCPUS,ReqMem,ReqTRES%300,AllocTRES%300,NodeList")
TAILS = {"job/slurm.out", "job/slurm.err", "job/result/scheduler.jsonl"}
FILES = tuple(sorted(TAILS | {"job/actual-process-exit.txt", "job/reservation.json",
    "job/reservation.json.claimed", "job/release-completion.json", "job/result/request.json",
    "job/result/completion.json", "job/result/loaded-model.json", "job/result/artifact-before.json",
    "job/result/artifact-after.json"}))


def validate_spec(spec):
    expected = {"schema": "hydra-p6-saved-reload-allocation-v2", "attempt": ATTEMPT,
        "job_name": "hydra-" + ATTEMPT, "model_key": MODEL_KEY,
        "remote_job_directory": CAMPAIGN + "/jobs/" + ATTEMPT, "source": SOURCE,
        "account": ACCOUNT, "partition": PARTITION, "gpus": 1, "nodes": 1, "cpus": 8,
        "memory_gib": 64, "seconds": 300, "soft_limit_seconds": 240,
        "source_archive_sha256": ARCHIVE_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "training_source_root": TRAINING_SOURCE, "training_source_pins_sha256": TRAINING_SOURCE_MAP_SHA,
        "training_provider_sha256": TRAINING_PROVIDER_SHA, "runtime_manifest_sha256": RUNTIME_MANIFEST_SHA,
        "controller_sha256": CONTROLLER_SHA, "metadata_verifier_sha256": METADATA_VERIFIER_SHA,
        "provider_sha256": PROVIDER_SHA, "scheduler_helper_sha256": SMOKE_SHA,
        "artifact_manifest_sha256": MANIFEST_SHA, "final_tensor_population_sha256": FINAL_TENSOR_SHA,
        "original_job_id": ORIGINAL_JOB, "generation_calls": 0, "optimizer_updates": 0,
        "native_calls": 0, "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    variable = {"nonce", "manifest_content_sha256", "metadata_receipt_sha256", "metadata_actual_sha256"}
    require(type(spec) is dict and set(spec) == set(expected) | variable
            and all(type(spec.get(k)) is type(v) and spec.get(k) == v for k, v in expected.items()),
            "Only the exact saved-adapter recovery allocation is admitted.")
    require(re.fullmatch(r"[0-9a-f]{64}", CONTROLLER_SHA) and re.fullmatch(r"[0-9a-f]{64}", METADATA_VERIFIER_SHA),
            "Recovery recipes are not sealed yet.")
    require(type(spec["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"])
            and all(type(spec[k]) is str and re.fullmatch(r"[0-9a-f]{64}", spec[k])
                    for k in variable - {"nonce"}), "Invalid fixed recovery input pin/nonce.")
    return spec


def reservation(spec, job_id, uid):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id)
            and job_id != ORIGINAL_JOB and type(uid) is int and uid == UID, "Invalid owned recovery identity.")
    return {"schema": "hydra-p6-saved-reload-reservation-v2", "job_id": job_id, "uid": uid,
        "runtime_source_root": SOURCE, "artifact_directory": ARTIFACT, "base_directory": BASE,
        **{k: spec[k] for k in ("attempt", "job_name", "nonce", "account", "partition", "model_key",
            "gpus", "nodes", "cpus", "memory_gib", "seconds", "soft_limit_seconds", "original_job_id",
            "controller_sha256", "metadata_receipt_sha256", "metadata_actual_sha256", "metadata_verifier_sha256",
            "provider_sha256", "scheduler_helper_sha256", "source_pins_sha256", "artifact_manifest_sha256",
            "training_source_root", "training_source_pins_sha256", "training_provider_sha256", "runtime_manifest_sha256",
            "final_tensor_population_sha256", "generation_calls", "optimizer_updates", "native_calls",
            "automatic_retry", "resume")}}


def job_script(spec):
    validate_spec(spec)
    job = spec["remote_job_directory"]
    argv = [PROJECT + "/.venv-helios/bin/python", "-B", "-P", PACKAGE + "/gpu_saved_reload_import4.py",
            "--reservation-sha256", "RESERVATION_SHA_PLACEHOLDER"]
    invocation = shlex.join(argv).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_RECOVERY_RESERVATION_SHA"')
    return "\n".join(["#!/bin/bash -l", "set -euo pipefail", "umask 077", "module purge",
        "module load ML-bundle/25.10", "unset PYTHONPATH", "export PYTHONHASHSEED=20260904",
        "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1", "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1",
        "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8", "cd " + shlex.quote(SOURCE),
        "read -r HYDRA_RECOVERY_RESERVATION_SHA < " + shlex.quote(job + "/reservation.sha256"),
        "set +e", invocation, "HYDRA_RECOVERY_ACTUAL_EXIT=$?", "set -C",
        "printf '%s\\n' \"$HYDRA_RECOVERY_ACTUAL_EXIT\" > " + shlex.quote(job + "/actual-process-exit.txt"),
        'exit "$HYDRA_RECOVERY_ACTUAL_EXIT"', ""])


def verify_sources(spec, source_map):
    require(os.getuid() == UID, "The recovery recipe belongs to the exact campaign owner.")
    require(type(source_map) is dict and len(source_map) == 585 and digest(canonical(source_map)) == SOURCE_MAP_SHA,
            "The explicitly pinned inference-only runtime map changed.")
    manifest_raw = ordinary_bytes(Path(SOURCE).parent / "manifest.json", 2 * 1024**2)
    manifest = json.loads(manifest_raw)
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"]
            and digest(manifest_raw) == RUNTIME_MANIFEST_SHA
            and manifest.get("archive_sha256") == ARCHIVE_SHA and manifest.get("inference_only") is True
            and manifest.get("training_execution_allowed") is False, "Inference-only runtime source archive changed.")
    total = 0
    for name, pin in source_map.items():
        require(name in manifest["files"] and manifest["files"][name] == pin, "Original source inventory changed.")
        raw = ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)
        total += len(raw)
        require(total <= 32 * 1024**2 and pin == {"bytes": len(raw), "sha256": digest(raw)}, "Original source bytes changed.")
    require(json.loads(ordinary_bytes(Path(PACKAGE) / "runtime-source-pins-base3.json", MAX_INPUT)) == source_map,
            "Recovery package does not contain the exact new runtime source map.")
    controller = Path(PACKAGE) / "gpu_saved_reload_import4.py"
    require(digest(ordinary_bytes(controller, 65536)) == CONTROLLER_SHA
            and digest(ordinary_bytes(Path(PACKAGE) / "metadata_recovery_import4.py", 65536)) == METADATA_VERIFIER_SHA,
            "Recovery controller or CPU verifier changed.")
    module_spec = importlib.util.spec_from_file_location("p6_saved_recovery_admission", controller)
    helper = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(helper)  # stdlib definitions only; run() is never invoked here.
    require(helper.source_pins() == source_map, "Original/runtime complete source verification differs.")
    metadata = ordinary_bytes(Path(PACKAGE) / "metadata-recovery-import4.json", 2 * 1024**2)
    actual = ordinary_bytes(Path(PACKAGE) / "metadata-actual-completion-import4.json", 65536)
    require(digest(metadata) == spec["metadata_receipt_sha256"] and digest(actual) == spec["metadata_actual_sha256"],
            "CPU metadata result/actual completion receipt changed.")
    helper.validate_metadata(json.loads(metadata), json.loads(actual), digest(metadata), METADATA_VERIFIER_SHA)
    require(digest(ordinary_bytes(Path(ARTIFACT) / "manifest.json", 4 * 1024**2)) == MANIFEST_SHA
            and not (Path(ARTIFACT) / "incomplete.json").exists(), "Original saved artifact changed or is incomplete.")


def collect(phase, spec, record):
    require(record == reservation(spec, record.get("job_id"), UID), "Collection uses another recovery reservation.")
    result = {"job_id": record["job_id"], "read_only": True, "scheduler": {}, "files": {}}
    result["scheduler"]["sacct"] = phase.run(["sacct", "-n", "-P", "-j", record["job_id"],
        "--format=" + SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol", "-o", "show", "job", record["job_id"]], must_succeed=False)
    total = 0
    for name in FILES:
        row = snapshot(Path(spec["remote_job_directory"]) / name.removeprefix("job/"), tail=name in TAILS)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Recovery collection exceeds its fixed metadata bound.")
            result["files"][name] = row
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema": "hydra-p6-saved-recovery-control-phase-v1", "completed": False,
                "error": None, "automatic_retry": False, "commands": phase.commands}
    def alarm(_signum, _frame):
        raise TimeoutError("Recovery control phase expired; no retry.")
    signal.signal(signal.SIGALRM, alarm)
    signal.alarm(int(PHASE_WALL) + 5)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "Control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit", "release", "collect"}, "Unknown recovery phase.")
        spec = validate_spec(request["spec"])
        response["phase"] = request["phase"]
        if request["phase"] == "submit":
            response["result"] = submit(phase, spec, request["source_map"])
        elif request["phase"] == "release":
            response["result"] = release(phase, spec, request["source_map"], request["reservation"])
        else:
            response["result"] = collect(phase, spec, request["reservation"])
        response["completed"] = request["phase"] != "release" or response["result"]["released"]
    except BaseException as error:
        response["error"] = type(error).__name__ + ": " + str(error)[:2048]
    finally:
        signal.alarm(0)
    raw = canonical(response)
    require(len(raw) <= MAX_RESPONSE, "Recovery response exceeds its bound.")
    sys.stdout.buffer.write(raw + b"\n")
    return 0 if response["completed"] else 1


# Exact reviewed P6-v2 helpers are appended by derive_helpers.py, before main.

# BEGIN EXACT REVIEWED HELPERS
def require(condition, message):
    if not condition:
        raise ValueError(message)

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def integer(value, lower, upper, name):
    require(type(value) is int and lower <= value <= upper, "Invalid " + name)
    return value

def wall_string(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:00"

def ordinary_bytes(path, limit):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path and before.st_size <= limit,
            "Not a bounded ordinary file: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.lstat()
    require(len(raw) <= limit and all(getattr(before, key) == getattr(after, key)
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")), "File changed while read.")
    return raw

def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_OBSERVATION, "Control evidence exceeds its bound.")
    with path.open("xb") as stream:
        stream.write(raw)

def fields(raw):
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    require(len(pairs) == len({key for key, _ in pairs}), "Ambiguous scheduler response.")
    return dict(pairs)

def tres(raw):
    pairs = [item.split("=", 1) for item in raw.split(",")]
    require(all(len(pair) == 2 for pair in pairs) and len(pairs) == len({p[0] for p in pairs}), "Invalid TRES.")
    return dict(pairs)

def check_queue_row(identifier, row, allowed_job=None):
    require(re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Invalid queue job identity.")
    if "_" in identifier:
        base, task = identifier.split("_")
        require(row.get("ArrayJobId") == base and row.get("ArrayTaskId") == task, "Array element identity differs.")
    else:
        require(row.get("JobId") == identifier, "Queue job identity differs.")
    require("ReqTRES" in row, "Missing requested resources.")
    requested = tres(row["ReqTRES"])
    allocated_raw = row.get("AllocTRES")
    require(allocated_raw is None or type(allocated_raw) is str, "Invalid allocated resources.")
    # Slurm prints this exact sentinel for pending jobs with no allocation yet.
    allocated = {} if allocated_raw in (None, "", "(null)") else tres(allocated_raw)
    if identifier != allowed_job:
        require(not any(key.startswith("gres/gpu") for key in requested.keys() | allocated.keys()),
                "Another owned GPU reservation/allocation exists; leave it unchanged.")
    return {"job_id": identifier, "requested_tres": requested, "allocated_tres": allocated, "left_unchanged": True}

def check_held(row, spec, job_id, uid):
    validate_spec(spec)
    expected = {"JobId": job_id, "JobName": spec["job_name"], "Comment": "hydra-p6:" + spec["nonce"],
        "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
        "Account": ACCOUNT, "Partition": PARTITION, "NumCPUs": "8",
        "TimeLimit": wall_string(spec["seconds"]), "Command": spec["remote_job_directory"] + "/job.sbatch",
        "WorkDir": spec["remote_job_directory"], "StdOut": spec["remote_job_directory"] + "/slurm.out",
        "StdErr": spec["remote_job_directory"] + "/slurm.err"}
    require(all(row.get(key) == value for key, value in expected.items()), "Held job identity/resources differ.")
    require(row.get("NumNodes") in ("1", "1-1"), "Held job does not request exactly one node.")
    require(re.fullmatch(r"[^()]+\(" + str(uid) + r"\)", row.get("UserId", "")), "Held job belongs to another uid.")
    requested = tres(row.get("ReqTRES", ""))
    require(all(requested.get(key) == value for key, value in {"cpu": "8", "mem": "64G", "node": "1", "gres/gpu": "1"}.items())
            and all(value == "1" for key, value in requested.items() if key.startswith("gres/gpu")), "Requested TRES differ.")

def bounded_command(argv, timeout=15.0, limit=MAX_COMMAND_OUTPUT):
    """One owned CLI child; bounded combined pipe, explicit kill/reap, no retry."""
    started = time.monotonic()
    record = {"command": argv, "actual_exit_code": None, "executed": False, "owned_child_reaped": False,
              "stop_reason": None, "stdout_stderr": ""}
    process, raw = None, bytearray()
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        record["executed"] = True
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            if time.monotonic() - started >= timeout:
                record["stop_reason"] = "wall_limit"
                break
            if not eof and select.select([process.stdout], [], [], 0.05)[0]:
                chunk = os.read(process.stdout.fileno(), min(16384, limit + 1 - len(raw)))
                if chunk:
                    raw.extend(chunk)
                    if len(raw) > limit:
                        record["stop_reason"] = "output_limit"
                        break
                else:
                    eof = True
            elif eof:
                time.sleep(0.02)
    except BaseException as exc:
        record["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:512]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                record["actual_exit_code"] = process.wait(timeout=3)
                record["owned_child_reaped"] = True
            except subprocess.TimeoutExpired:
                record["stop_reason"] = "owned_child_not_reaped"
            if process.stdout:
                process.stdout.close()
        record["stdout_stderr"] = bytes(raw[:limit]).decode("utf-8", "replace")
        record["elapsed_seconds"] = time.monotonic() - started
    return record

class Phase:
    def __init__(self):
        self.deadline = time.monotonic() + PHASE_WALL
        self.commands = []

    def run(self, argv, *, timeout=15.0, must_succeed=True):
        require(len(self.commands) < 36 and time.monotonic() < self.deadline, "Phase command/wall bound reached.")
        row = bounded_command(argv, min(timeout, self.deadline - time.monotonic()))
        self.commands.append(row)
        require(row["owned_child_reaped"], "Owned control child cleanup was not confirmed.")
        if must_succeed:
            require(row["actual_exit_code"] == 0 and row["stop_reason"] is None, "Bounded scheduler command failed.")
        return row

    def query(self, job_id):
        return fields(self.run(["scontrol", "-o", "show", "job", job_id])["stdout_stderr"])

    def queue(self, allowed_job=None):
        raw = self.run(["squeue", "--array", "-h", "-u", str(os.getuid()), "-o", "%i|%T|%j|%b"])["stdout_stderr"]
        rows = raw.splitlines()
        require(len(rows) <= 32, "Too many owned queue records for this bounded preflight.")
        result, seen = [], set()
        for line in rows:
            identifier = line.split("|", 1)[0].strip()
            require(identifier not in seen and re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Ambiguous queue identity.")
            seen.add(identifier)
            result.append(check_queue_row(identifier, self.query(identifier), allowed_job))
        if allowed_job is not None:
            require(allowed_job in seen, "Held job absent from current queue.")
        return result

def submit(phase, spec, source_map):
    verify_sources(spec, source_map)
    queue = phase.queue()
    directory = Path(spec["remote_job_directory"])
    directory.mkdir(parents=True, exist_ok=False)
    script = job_script(spec)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(script)
    save(directory / "allocation-request.json", spec)
    argv = ["sbatch", "--hold", "--parsable", "--no-requeue", "--account=" + ACCOUNT, "--partition=" + PARTITION,
        "--nodes=1", "--ntasks=1", "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + wall_string(spec["seconds"]),
        "--job-name=" + spec["job_name"], "--comment=hydra-p6:" + spec["nonce"], "--chdir=" + str(directory),
        "--output=" + str(directory / "slurm.out"), "--error=" + str(directory / "slurm.err"), str(directory / "job.sbatch")]
    # Exclusive intent survives failed/uncertain sbatch; this path cannot submit twice.
    save(directory / "submit-intent.json", {"argv": argv, "automatic_retry": False})
    actual = phase.run(argv, timeout=20, must_succeed=False)
    result = {"actual_sbatch_exit_code": actual["actual_exit_code"], "uid": os.getuid(), "held": False,
        "released": False, "other_cpu_jobs": queue, "sbatch": actual}
    if actual["actual_exit_code"] == 0 and actual["stop_reason"] is None:
        job_id = actual["stdout_stderr"].strip()
        require(re.fullmatch(r"[0-9]{1,20}", job_id), "Sbatch did not return an exact scalar job id; do not retry.")
        result["job_id"] = job_id
        before = phase.query(job_id)
        check_held(before, spec, job_id, os.getuid())
        result.update(held=True, held_fields=before)
    save(directory / "held-submission.json", result)
    require(result["held"], "Submission failed or exact held state was not confirmed; no release/retry.")
    return result

def release(phase, spec, source_map, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Reservation identity differs.")
    verify_sources(spec, source_map)
    directory = Path(spec["remote_job_directory"])
    require(json.loads(ordinary_bytes(directory / "allocation-request.json", MAX_INPUT)) == spec,
            "Remote submitted request changed.")
    require(ordinary_bytes(directory / "job.sbatch", 32768) == job_script(spec).encode(), "Remote job script changed.")
    before = phase.query(record["job_id"])
    check_held(before, spec, record["job_id"], os.getuid())
    queue = phase.queue(record["job_id"])
    raw = canonical(record) + b"\n"
    with (directory / "reservation.json").open("xb") as stream:
        stream.write(raw)
    with (directory / "reservation.sha256").open("x") as stream:
        stream.write(digest(raw) + "\n")
    save(directory / "release-intent.json", {"reservation_sha256": digest(raw), "before": before,
        "queue": queue, "allocated_seconds_ceiling": spec["seconds"], "automatic_retry": False})
    actual = phase.run(["scontrol", "release", record["job_id"]], must_succeed=False)
    result = {"job_id": record["job_id"], "actual_release_exit_code": actual["actual_exit_code"],
        "released": actual["actual_exit_code"] == 0 and actual["stop_reason"] is None,
        "reservation_sha256": digest(raw), "allocated_seconds_ceiling": spec["seconds"], "release": actual,
        "automatic_retry": False, "uncertain_release_still_fully_charged": True}
    save(directory / "release-completion.json", result)
    return result

def snapshot(path, *, tail):
    if not path.exists() and not path.is_symlink():
        return None
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path, "Evidence path is not ordinary.")
    limit = 256 * 1024 if tail else 2 * 1024**2
    require(tail or before.st_size <= limit, "Complete JSON evidence exceeds its bound.")
    offset = max(0, before.st_size - limit) if tail else 0
    with path.open("rb") as stream:
        stream.seek(offset)
        raw = stream.read(min(limit, before.st_size - offset))
    after = path.lstat()
    stable = all(getattr(before, key) == getattr(after, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns"))
    return {"bytes": len(raw), "sha256": digest(raw), "base64": base64.b64encode(raw).decode(),
        "offset": offset, "file_bytes_before": before.st_size, "file_bytes_after": after.st_size,
        "mtime_ns_before": before.st_mtime_ns, "stable": stable,
        "complete_file": stable and offset == 0 and len(raw) == before.st_size}


if __name__ == "__main__":
    raise SystemExit(main())
