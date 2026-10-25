"""Fixed P6 held-submit/release/read-only collection; stdlib, no work on import.

This draft is bound exclusively to sealed bundle06/source-data-07. Each explicit
invocation performs ONE phase. It never trains directly, retries, polls a job to
completion, downloads weights, or cancels another allocation.
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
REMOTE_USER = "plgnasqret"
ARCHIVE_SHA = "aa0a66ee80f5710e0a42a33805a34cd085be3bb083b06baa066b6954d2f3fbf5"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
TRAINER_SHA = "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617"
SOURCE_MAP_SHA = "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
LAUNCH_INPUTS_SHA = "6ae22bd1075f7e83ad1ff427dbe468eeb5e38f30619e98ea7fcc71d48aae6e88"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
DATA = "output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json"
TRAINER = "output/p6-prototype/remote_training_pilot.py"
MODELS = {
    "qwen3-1.7b-base": {
        "attempt": "p6-training-fresh-1.7b-v2-01",
        "config": "hydra-playground/training-v5/configs/qwen3_1_7b_decisions_v2_pilot.toml",
        "config_sha256": "807933e5625536fc2b6412e680010d1534cac7e94156e284ae3e63e87a047e27",
        "plan_sha256": "3ec6e96c39d3294671d61018431614ce02bff5b0874431e5883473cbb1cd5816",
        "artifact": "output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01",
        "model": {"model_id": "Qwen/Qwen3-1.7B-Base", "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}},
    "qwen3-4b-base": {
        "attempt": "p6-training-fresh-4b-v2-01",
        "config": "hydra-playground/training-v5/configs/qwen3_4b_decisions_v2_pilot.toml",
        "config_sha256": "4809f699f6fa6d566d900ccc0748e487746708565604d43258be1574f1430318",
        "plan_sha256": "e332678d9102db48071638b1d94b958cea0cf33c9c60234aef4bf7e5ba64ec7f",
        "artifact": "output/hydra-implementation-2026-09-04/training-fresh-4b-v2-01",
        "model": {"model_id": "Qwen/Qwen3-4B-Base", "revision": "906bfd4b4dc7f14ee4320094d8b41684abff8539"}},
}
MAX_INPUT = 256 * 1024
MAX_COMMAND_OUTPUT = 65536
MAX_OBSERVATION = 8 * 1024**2
PHASE_WALL = 550.0  # At most 32 exact queue identities; no query retry.
SACCT_FORMAT = ("JobIDRaw,JobName%100,User,Account,Partition,State,ExitCode,ElapsedRaw,"
                "TimelimitRaw,AllocCPUS,ReqMem,ReqTRES%300,AllocTRES%300,NodeList")
TAILS = {"job/slurm.out", "job/slurm.err", "job/result/progress.jsonl", "job/result/scheduler.jsonl"}
FILES = tuple(sorted(TAILS | {
    "job/actual-process-exit.txt", "job/reservation.json", "job/reservation.json.claimed",
    "job/release-completion.json", "job/result/request.json", "job/result/runtime.json",
    "job/result/prepared-plan.json", "job/result/token-preflight.json", "job/result/token-preflight-pin.json",
    "job/result/device.json", "job/result/artifact-receipt.json", "job/result/completion.json",
    "artifact/manifest.json", "artifact/incomplete.json"}))


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


def durations(seconds, soft):
    integer(seconds, 300, 7200, "allocation seconds")
    require(seconds % 60 == 0, "Allocation must use exact whole minutes; no rounding.")
    integer(soft, 60, min(6900, seconds - 60), "soft deadline")


def wall_string(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:00"


def validate_spec(spec):
    require(type(spec) is dict and spec.get("schema") == "hydra-p6-fresh-training-allocation-v1", "Unknown allocation schema.")
    require(spec.get("model_key") in MODELS, "Only the two reviewed fresh model configs are allowed.")
    model = MODELS[spec["model_key"]]
    durations(spec.get("seconds"), spec.get("soft_limit_seconds"))
    expected = {"attempt": model["attempt"], "job_name": "hydra-" + model["attempt"],
        "remote_job_directory": CAMPAIGN + "/jobs/" + model["attempt"], "source": SOURCE,
        "account": ACCOUNT, "partition": PARTITION, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "source_archive_sha256": ARCHIVE_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "launch_inputs_sha256": LAUNCH_INPUTS_SHA, "controller_sha256": TRAINER_SHA,
        "scheduler_helper_sha256": SMOKE_SHA, "provider_sha256": PROVIDER_SHA,
        "dataset_sha256": DATA_SHA, "config_sha256": model["config_sha256"], "plan_sha256": model["plan_sha256"],
        "training_rows": 2047, "validation_rows": 432, "expected_optimizer_steps": 256,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    require(all(type(spec.get(key)) is type(value) and spec.get(key) == value for key, value in expected.items()),
            "Allocation identity, fixed config, source pins or resources differ.")
    require(set(spec) == set(expected) | {"schema", "model_key", "nonce", "seconds", "soft_limit_seconds", "manifest_content_sha256"},
            "Unknown allocation fields cannot override the fixed command.")
    require(type(spec.get("nonce")) is str and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"]), "Invalid nonce.")
    require(type(spec.get("manifest_content_sha256")) is str and re.fullmatch(r"[0-9a-f]{64}", spec["manifest_content_sha256"]),
            "Missing exact canonical bundle manifest pin.")
    return model


def job_script(spec):
    model = validate_spec(spec)
    job = spec["remote_job_directory"]
    argv = [PROJECT + "/.venv-helios/bin/python", "-B", "-P", SOURCE + "/" + TRAINER,
        "--app-root", SOURCE + "/hydra-playground", "--reservation", job + "/reservation.json",
        "--reservation-sha256", "RESERVATION_SHA_PLACEHOLDER", "--model-key", spec["model_key"],
        "--config", SOURCE + "/" + model["config"], "--dataset-manifest", SOURCE + "/" + DATA,
        "--base-directory", CAMPAIGN + "/authenticated-bases-01/" + spec["model_key"], "--output", job + "/result"]
    invocation = shlex.join(argv).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_TRAINING_RESERVATION_SHA"')
    return "\n".join(["#!/bin/bash -l", "set -euo pipefail", "umask 077", "module purge",
        "module load ML-bundle/25.10", "unset PYTHONPATH", "export PYTHONHASHSEED=20260904",
        "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1", "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1",
        "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8", "cd " + shlex.quote(SOURCE),
        "read -r HYDRA_TRAINING_RESERVATION_SHA < " + shlex.quote(job + "/reservation.sha256"),
        "set +e", invocation, "HYDRA_TRAINING_ACTUAL_EXIT=$?", "set -C",
        "printf '%s\\n' \"$HYDRA_TRAINING_ACTUAL_EXIT\" > " + shlex.quote(job + "/actual-process-exit.txt"),
        'exit "$HYDRA_TRAINING_ACTUAL_EXIT"', ""])


def reservation(spec, job_id, uid):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Invalid scalar job id.")
    integer(uid, 1, 2**32 - 1, "uid")
    return {"schema": "hydra-p6-training-reservation-v1", "job_id": job_id, "uid": uid,
        **{key: spec[key] for key in ("job_name", "nonce", "account", "partition", "model_key", "gpus", "nodes",
            "cpus", "memory_gib", "seconds", "soft_limit_seconds", "config_sha256", "dataset_sha256",
            "plan_sha256", "controller_sha256", "source_pins_sha256")}}


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
    requested, allocated = tres(row["ReqTRES"]), tres(row["AllocTRES"]) if row.get("AllocTRES") else {}
    if identifier != allowed_job:
        require(not any(key.startswith("gres/gpu") for key in requested.keys() | allocated.keys()),
                "Another owned GPU reservation/allocation exists; leave it unchanged.")
    return {"job_id": identifier, "requested_tres": requested, "allocated_tres": allocated, "left_unchanged": True}


def check_held(row, spec, job_id, uid):
    validate_spec(spec)
    expected = {"JobId": job_id, "JobName": spec["job_name"], "Comment": "hydra-p6:" + spec["nonce"],
        "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
        "Account": ACCOUNT, "Partition": PARTITION, "NumCPUs": "8", "NumNodes": "1",
        "TimeLimit": wall_string(spec["seconds"]), "Command": spec["remote_job_directory"] + "/job.sbatch",
        "WorkDir": spec["remote_job_directory"], "StdOut": spec["remote_job_directory"] + "/slurm.out",
        "StdErr": spec["remote_job_directory"] + "/slurm.err"}
    require(all(row.get(key) == value for key, value in expected.items()), "Held job identity/resources differ.")
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


def verify_sources(spec, source_map):
    require(type(source_map) is dict and len(source_map) == 585 and digest(canonical(source_map)) == SOURCE_MAP_SHA,
            "Controller map does not match bundle06.")
    manifest = json.loads(ordinary_bytes(Path(SOURCE).parent / "manifest.json", 2 * 1024**2))
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"] and manifest.get("archive_sha256") == ARCHIVE_SHA,
            "Remote bundle manifest changed (canonical content comparison permits transfer formatting only).")
    total = 0
    for name, expected in source_map.items():
        require(name in manifest["files"] and manifest["files"][name] == expected, "Manifest/controller inventory differs.")
        raw = ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)
        total += len(raw)
        require(total <= 32 * 1024**2 and len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
                "Pinned controller source changed.")
    for name, expected in ((DATA, DATA_SHA), (MODELS[spec["model_key"]]["config"], spec["config_sha256"])):
        require(digest(ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)) == expected, "Data/config pin changed.")
    require(not (Path(SOURCE) / MODELS[spec["model_key"]]["artifact"]).exists(), "Fresh artifact output already exists; no resume/retry.")


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


def collect(phase, spec, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Collection reservation identity differs.")
    roots = {"job": Path(spec["remote_job_directory"]), "artifact": Path(SOURCE) / MODELS[spec["model_key"]]["artifact"]}
    result = {"job_id": record["job_id"], "read_only": True, "scheduler": {}, "files": {}}
    result["scheduler"]["sacct"] = phase.run(["sacct", "-n", "-P", "-j", record["job_id"], "--format=" + SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol", "-o", "show", "job", record["job_id"]], must_succeed=False)
    total = 0
    for name in FILES:
        prefix, relative = name.split("/", 1)
        row = snapshot(roots[prefix] / relative, tail=name in TAILS)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Observation payload exceeds its finite bound.")
            result["files"][name] = row
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema": "hydra-p6-training-control-phase-v1", "completed": False, "error": None,
                "automatic_retry": False, "commands": phase.commands}
    def deadline(_signum, _frame):
        raise TimeoutError("Bounded control phase expired.")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(int(PHASE_WALL) + 5)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "Control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit", "release", "collect"}, "Unknown control phase.")
        spec = request["spec"]
        validate_spec(spec)
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
    require(len(raw) <= 14 * 1024**2, "Control response exceeds its encoded bound.")
    sys.stdout.buffer.write(raw + b"\n")
    return 0 if response["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
