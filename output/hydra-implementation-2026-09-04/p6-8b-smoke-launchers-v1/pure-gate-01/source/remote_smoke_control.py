"""One fixed 8B smoke, using bundle06 and reviewed P6-v2 control primitives.

No imports of model/native code, and no operation occurs on import. The GPU
command is exactly the smoke08 contract with only the fixed 8B model/config and
fresh job/output changed. This module cannot launch training or saved adapters.
"""
from __future__ import annotations

import base64
import hashlib
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
SOURCE = CAMPAIGN + "/bundles/source-data-07/source"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
REMOTE_USER, UID = "plgnasqret", 105923
ATTEMPT = "p6-smoke-8b-v2-01"
MODEL_KEY = "qwen3-8b-base"
MODEL = {"model_id": "Qwen/Qwen3-8B-Base", "revision": "49e3418fbbbca6ecbdf9608b4d22e5a407081db4"}
ARCHIVE_SHA = "aa0a66ee80f5710e0a42a33805a34cd085be3bb083b06baa066b6954d2f3fbf5"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
TRAINER_SHA = "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617"
SOURCE_MAP_SHA = "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
LAUNCH_INPUTS_SHA = "6ae22bd1075f7e83ad1ff427dbe468eeb5e38f30619e98ea7fcc71d48aae6e88"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
DATA = "output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json"
SMOKE = "output/p6-prototype/remote_provider_smoke.py"
CONFIG = "hydra-playground/training-v5/configs/qwen3_8b_decisions_v2_pilot.toml"
CONFIG_SHA = "a1a826c9b809e1cf4ba84d0a16cc038e5eb6aaeae16ec45afbd7b95f311241f5"
PLAN_SHA = "14a09498273959441093c09c5385ea5f8fa4b47ed2984a7b73b1047374728fc0"
BASE_SHA = "3843ddb12f4e24b4bd4ef1bc79740fdc01da80e19c0fa148566739e9a412dae7"
CPU_SHA = "e784ddabce2c900384c6b94eea7f04e4a4134890d5057e1d34909263526f0913"
PILOTS = {
    "qwen3-1.7b-base": ("p6-training-fresh-1.7b-v2-01", "training-fresh-1.7b-v2-01"),
    "qwen3-4b-base": ("p6-training-fresh-4b-v2-01", "training-fresh-4b-v2-01"),
}
MAX_INPUT, MAX_COMMAND_OUTPUT = 256 * 1024, 65536
MAX_OBSERVATION, MAX_RESPONSE = 8 * 1024**2, 14 * 1024**2
PHASE_WALL = 550.0
SACCT_FORMAT = ("JobIDRaw,JobName%100,User,Account,Partition,State,ExitCode,ElapsedRaw,"
                "TimelimitRaw,AllocCPUS,ReqMem,ReqTRES%300,AllocTRES%300,NodeList")
TAILS = {"job/slurm.out", "job/slurm.err", "job/result/scheduler.jsonl"}
FILES = tuple(sorted(TAILS | {
    "job/actual-process-exit.txt", "job/reservation.json", "job/reservation.json.claimed",
    "job/release-completion.json", "job/result/request.json", "job/result/model-admission.json",
    "job/result/primitive.json", "job/result/planner.json", "job/result/throughput.json",
    "job/result/completion.json"}))


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_pilots(value):
    require(type(value) is dict and set(value) == set(PILOTS), "Both completed fixed fresh pilots are required.")
    for row in value.values():
        require(type(row) is dict and set(row) == {"job_id", "seconds", "reservation_sha256",
                "manifest_sha256", "completion_sha256", "request_sha256", "base_identity_sha256"},
                "Unexpected pilot evidence fields.")
        require(type(row["job_id"]) is str and re.fullmatch(r"[0-9]{1,20}", row["job_id"]), "Invalid pilot job.")
        integer(row["seconds"], 300, 7200, "pilot seconds")
        require(row["seconds"] % 60 == 0 and all(valid_sha(row[key]) for key in row if key.endswith("sha256")),
                "Pilot source/evidence pins are incomplete.")
    require(len({row["job_id"] for row in value.values()}) == 2, "Two distinct completed pilots are required.")


def fixed_spec_fields():
    return {"schema": "hydra-p6-8b-smoke-allocation-v1", "attempt": ATTEMPT,
        "job_name": "hydra-" + ATTEMPT, "model_key": MODEL_KEY,
        "remote_job_directory": CAMPAIGN + "/jobs/" + ATTEMPT, "source": SOURCE,
        "account": ACCOUNT, "partition": PARTITION, "gpus": 1, "nodes": 1, "cpus": 8,
        "memory_gib": 64, "seconds": 600, "maximum_actual_model_calls": 2,
        "primitive_beams": 4, "primitive_new_tokens": 64, "planner_new_tokens": 256,
        "input_token_cap": 4096, "generated_token_slot_cap": 512, "maximum_gradient_examples": 8,
        "optimizer_updates": 0, "training_pilot": False, "adapter_requested": False,
        "source_archive_sha256": ARCHIVE_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "launch_inputs_sha256": LAUNCH_INPUTS_SHA, "provider_sha256": PROVIDER_SHA,
        "scheduler_helper_sha256": SMOKE_SHA, "dataset_sha256": DATA_SHA,
        "config_sha256": CONFIG_SHA, "plan_sha256": PLAN_SHA, "base_identity_sha256": BASE_SHA,
        "cpu_prerequisite_sha256": CPU_SHA, "submit_held": True,
        "automatic_retry": False, "resume": False, "requeue": False}


def validate_spec(spec):
    expected = fixed_spec_fields()
    require(type(spec) is dict and set(spec) == set(expected) | {"nonce", "manifest_content_sha256", "pilot_evidence"},
            "Unknown allocation fields cannot override this fixed smoke.")
    require(all(type(spec[key]) is type(value) and spec[key] == value for key, value in expected.items()),
            "Smoke model, command, source, resources or no-update policy differ.")
    require(type(spec["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"])
            and valid_sha(spec["manifest_content_sha256"]), "Missing exact one-use/source identity.")
    validate_pilots(spec["pilot_evidence"])
    return spec


def reservation(spec, job_id, uid):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Invalid scalar job id.")
    require(type(uid) is int and uid == UID, "Wrong actual owner.")
    return {"schema": "hydra-p6-smoke-reservation-v1", "job_id": job_id, "uid": uid,
        **{key: spec[key] for key in ("job_name", "nonce", "account", "partition", "model_key",
                                     "gpus", "nodes", "cpus", "memory_gib", "seconds")}}


def job_script(spec):
    validate_spec(spec)
    job = spec["remote_job_directory"]
    argv = [PROJECT + "/.venv-helios/bin/python", "-B", "-P", SOURCE + "/" + SMOKE,
        "--app-root", SOURCE + "/hydra-playground", "--reservation", job + "/reservation.json",
        "--reservation-sha256", "RESERVATION_SHA_PLACEHOLDER", "--base-directory",
        CAMPAIGN + "/authenticated-bases-01/" + MODEL_KEY, "--output", job + "/result",
        "--throughput-examples", "8", "--throughput-config", SOURCE + "/" + CONFIG,
        "--dataset-manifest", DATA, "--dataset-sha256", DATA_SHA]
    invocation = shlex.join(argv).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_RESERVATION_SHA"')
    return "\n".join(["#!/bin/bash -l", "set -euo pipefail", "umask 077", "module purge",
        "module load ML-bundle/25.10", "unset PYTHONPATH", "export PYTHONHASHSEED=20260904",
        "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1", "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1",
        "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=1", "cd " + shlex.quote(SOURCE),
        "read -r HYDRA_RESERVATION_SHA < " + shlex.quote(job + "/reservation.sha256"), "set +e", invocation,
        "HYDRA_ACTUAL_EXIT=$?", "set -C",
        "printf '%s\\n' \"$HYDRA_ACTUAL_EXIT\" > " + shlex.quote(job + "/actual-process-exit.txt"),
        'exit "$HYDRA_ACTUAL_EXIT"', ""])


def verify_sources(spec, source_map):
    require(type(source_map) is dict and len(source_map) == 585 and digest(canonical(source_map)) == SOURCE_MAP_SHA,
            "Controller map does not match bundle06.")
    manifest = json.loads(ordinary_bytes(Path(SOURCE).parent / "manifest.json", 2 * 1024**2))
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"] and manifest.get("archive_sha256") == ARCHIVE_SHA,
            "Remote bundle manifest changed.")
    total = 0
    for name, expected in source_map.items():
        require(manifest["files"].get(name) == expected, "Manifest/controller inventory differs.")
        raw = ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)
        total += len(raw)
        require(total <= 32 * 1024**2 and len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
                "Pinned controller source changed.")
    for name, expected in ((DATA, DATA_SHA), (CONFIG, CONFIG_SHA)):
        require(digest(ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)) == expected, "Data/config pin changed.")
    for model, (attempt, artifact) in PILOTS.items():
        pins = spec["pilot_evidence"][model]
        artifact_root = Path(SOURCE) / "output/hydra-implementation-2026-09-04" / artifact
        require(not (artifact_root / "incomplete.json").exists(), "Prior training has an incomplete marker.")
        paths = {"manifest_sha256": artifact_root / "manifest.json",
            "completion_sha256": Path(CAMPAIGN) / "jobs" / attempt / "result/completion.json",
            "request_sha256": Path(CAMPAIGN) / "jobs" / attempt / "result/request.json"}
        for key, path in paths.items():
            require(digest(ordinary_bytes(path, 2 * 1024**2)) == pins[key], "Prior completed pilot evidence changed.")


def collect(phase, spec, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Collection reservation differs.")
    directory = Path(spec["remote_job_directory"])
    require(json.loads(ordinary_bytes(directory / "reservation.json", 65536)) == record,
            "Remote one-use reservation changed.")
    result = {"job_id": record["job_id"], "read_only": True, "scheduler": {}, "files": {}}
    result["scheduler"]["sacct"] = phase.run(["sacct", "-n", "-P", "-j", record["job_id"], "--format=" + SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol", "-o", "show", "job", record["job_id"]], must_succeed=False)
    total = 0
    for name in FILES:
        row = snapshot(directory / name.split("/", 1)[1], tail=name in TAILS)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Observation exceeds its finite bound.")
            result["files"][name] = row
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema": "hydra-p6-8b-smoke-control-phase-v1", "completed": False, "error": None,
                "automatic_retry": False, "commands": phase.commands}
    def deadline(_signum, _frame):
        raise TimeoutError("Bounded control phase expired.")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(int(PHASE_WALL) + 5)
    try:
        require(os.getuid() == UID and sys.version_info[:3] == (3, 11, 5), "Unexpected login identity/interpreter.")
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "Control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit", "release", "collect"}, "Unknown control phase.")
        spec = validate_spec(request["spec"])
        response["phase"] = request["phase"]
        if request["phase"] == "submit":
            response["result"] = submit(phase, spec, request["source_map"])
        elif request["phase"] == "release":
            response["result"] = release(phase, spec, request["source_map"], request["reservation"])
        else:
            response["result"] = collect(phase, spec, request["reservation"])
        response["completed"] = request["phase"] != "release" or response["result"]["released"]
    except BaseException as exc:
        response["error"] = type(exc).__name__ + ": " + str(exc)[:2048]
    finally:
        signal.alarm(0)
    raw = canonical(response)
    require(len(raw) <= MAX_RESPONSE, "Control response exceeds its encoded bound.")
    sys.stdout.buffer.write(raw + b"\n")
    return 0 if response["completed"] else 1


# Reviewed P6-v2 helper definitions are appended verbatim by the derivation step.
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
