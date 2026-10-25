"""One explicit held-submit/release/collection around the frozen paired v2.

Only stdlib is imported here. No upload, evaluator changes, case selection,
model loading, retry, resume, cancellation of another job, or automatic next arm.
Transport/process primitives are copied from the reviewed training launcher v2.
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
SOURCE = CAMPAIGN + "/bundles/combined-source-03/source"
TRAINING_SOURCE = CAMPAIGN + "/bundles/source-data-07/source"
CONTROL = "output/hydra-implementation-2026-09-04/paired-evaluation-v2"
ACCOUNT, PARTITION, UID = "plgccaiautore2026-gpu-gh200", "plgrid-gpu-gh200", 105923
REMOTE_USER = "plgnasqret"
ARCHIVE_SHA = "719e4ec3e602b9617e003358721281dd2b35690b2fcccd6ee98f4e576a75ff9e"
MANIFEST_SHA = "bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08"
SOURCE_MAP_SHA = "bd54c461c17abe7afc45a9c8e6d4bc6402fffe377c7dbbdf399d51d686332f92"
COMMON_SHA = "d8f5dda5bfc1fb9e6769e4dc2f65591c2fb788db909842862e4009d80583d822"
CONTROLLER_SHA = "84e78193613505cab6d8d139720a5bb1b0f460db09aec3b0456fbabe4cd76e94"
WORKER_SHA = "da5df82dea0c1c5c0eaa5228c77fa75cd88d36e59e91e55efc68e4b3da1cff80"
SCHEDULER_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
HOLDOUT_SHA = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
SLICE_SHA = "01836cabc3ebf7bc69ed648816c8e36abe853a0a81baeafc7d956f2e3f3ca3d8"
HISTORICAL_SHA = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
HISTORICAL_DIRECTORY = PROJECT + "/experiments/retention-pilot-v1/results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1"
ARMS = ("symbolic", "historical_1_7b", "fresh_1_7b", "fresh_4b")
MODEL_KEYS = {"historical_1_7b": "qwen3-1.7b-base", "fresh_1_7b": "qwen3-1.7b-base", "fresh_4b": "qwen3-4b-base"}
ARTIFACTS = {"historical_1_7b": HISTORICAL_DIRECTORY,
    "fresh_1_7b": TRAINING_SOURCE + "/output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01",
    "fresh_4b": CAMPAIGN + "/bundles/source-data-08/source/output/hydra-implementation-2026-09-04/training-fresh-4b-v2-01"}
PROFILE_SECONDS = {"guarded-work-60-v1": 2040, "fixed-wall-30-v1": 1560}
MAX_INPUT, MAX_COMMAND_OUTPUT = 256 * 1024, 65536
MAX_OBSERVATION, MAX_RESPONSE = 128 * 1024**2, 176 * 1024**2
PHASE_WALL = 550.0
SACCT_FORMAT = "JobIDRaw,State%40,ExitCode,ElapsedRaw,AllocTRES%300,TimelimitRaw"
TOP_FILES = ("actual-process-exit.txt", "reservation.json", "reservation.json.claimed", "study.json",
    "release-completion.json", "result/request.json", "result/completion.json", "result/scheduler.jsonl", "slurm.out", "slurm.err")
CASE_FILES = ("case-request.json", "case-started.json", "case-result.json", "case-summary.json",
    "execution.json", "model-admission.json", "model-calls.jsonl", "progress.jsonl", "scheduler.jsonl", "stdout", "stderr")
TAIL_FILES = {"slurm.out", "slurm.err", "stdout", "stderr", "progress.jsonl", "scheduler.jsonl"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def ordinary_bytes(path, limit):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path and before.st_size <= limit,
            "Not a bounded ordinary file: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.lstat()
    require(len(raw) == before.st_size and all(getattr(before, key) == getattr(after, key)
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")), "File changed while read.")
    return raw


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_RESPONSE, "Control evidence exceeds its bound.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def contract(source):
    """Load only the hash-bound pure schema module, never native/model modules."""
    path = Path(source) / CONTROL / "paired_common.py"
    require(digest(ordinary_bytes(path, 65536)) == COMMON_SHA, "Frozen paired schema changed.")
    spec = importlib.util.spec_from_file_location("_paired_launch_contract", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_study(study, source):
    api = contract(source)
    api.study_spec(study, SLICE_SHA)
    require(study["scope"] == "full16" and set(study["arms"]) == set(ARMS)
            and study["comparison"] == "fixed_native_work_guarded"
            and study["source_pins_sha256"] == SOURCE_MAP_SHA, "Only the fixed four-arm full16 study is admitted.")
    for arm in ARMS[1:]:
        row = study["arms"][arm]
        require(row["base_directory"] == CAMPAIGN + "/authenticated-bases-01/" + MODEL_KEYS[arm]
                and row["adapter_directory"] == ARTIFACTS[arm], "A model path differs from its fixed recorded artifact.")
    require(api.job_seconds("full16", study["wall_profile"]) == PROFILE_SECONDS[study["wall_profile"]],
            "Frozen job ceiling differs.")
    return api


def attempt(arm):
    require(arm in ARMS, "Only the four main paired arms are admitted.")
    return "p6-paired-" + arm.replace("_", "-") + "-v4-01"


def validate_spec(spec):
    require(type(spec) is dict and spec.get("schema") == "hydra-paired-allocation-v1" and spec.get("arm") in ARMS,
            "Unknown paired allocation identity.")
    arm = spec["arm"]
    require(spec.get("wall_profile") in PROFILE_SECONDS, "Choose an existing finite wall profile explicitly.")
    expected = {"attempt": attempt(arm), "job_name": "hydra-" + attempt(arm),
        "remote_job_directory": CAMPAIGN + "/jobs/" + attempt(arm), "source": SOURCE,
        "account": ACCOUNT, "partition": PARTITION, "uid": UID, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": PROFILE_SECONDS[spec["wall_profile"]], "source_archive_sha256": ARCHIVE_SHA,
        "source_manifest_sha256": MANIFEST_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "controller_sha256": CONTROLLER_SHA, "case_worker_sha256": WORKER_SHA, "common_sha256": COMMON_SHA,
        "holdout_sha256": HOLDOUT_SHA, "slice_sha256": SLICE_SHA, "scope": "full16", "case_count": 16,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    require(all(type(spec.get(key)) is type(value) and spec.get(key) == value for key, value in expected.items()),
            "Paired identity, paths, source or resources differ.")
    require(set(spec) == set(expected) | {"schema", "arm", "nonce", "study_sha256", "wall_profile"}
            and valid_sha(spec["study_sha256"]) and type(spec["nonce"]) is str
            and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"]), "Unknown fields or invalid immutable binding.")


def reservation(spec, job_id):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Exact scalar job id required.")
    return {"schema": "hydra-p6-p10-paired-reservation-v1", "job_id": job_id,
        **{key: spec[key] for key in ("job_name", "nonce", "uid", "account", "partition", "gpus", "nodes", "cpus",
            "memory_gib", "seconds", "arm", "study_sha256", "source_pins_sha256", "controller_sha256",
            "case_worker_sha256", "common_sha256", "holdout_sha256", "slice_sha256")}}


def wall_string(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:00"


def job_script(spec):
    validate_spec(spec)
    job = spec["remote_job_directory"]
    argv = [PROJECT + "/.venv-helios/bin/python", "-B", SOURCE + "/" + CONTROL + "/paired_controller.py",
        "--app-root", SOURCE + "/hydra-playground", "--study", job + "/study.json", "--study-sha256", spec["study_sha256"],
        "--reservation", job + "/reservation.json", "--reservation-sha256", "RESERVATION_SHA_PLACEHOLDER",
        "--output", job + "/result"]
    invocation = shlex.join(argv).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_PAIRED_RESERVATION_SHA"')
    return "\n".join(["#!/bin/bash -l", "set -euo pipefail", "umask 077", "module purge", "module load ML-bundle/25.10",
        "unset PYTHONPATH PYTHONHOME", "export PYTHONHASHSEED=0", "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1",
        "export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1", "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8",
        "cd " + shlex.quote(SOURCE), "read -r HYDRA_PAIRED_RESERVATION_SHA < " + shlex.quote(job + "/reservation.sha256"),
        "set +e", invocation, "HYDRA_PAIRED_ACTUAL_EXIT=$?", "set -C",
        "printf '%s\\n' \"$HYDRA_PAIRED_ACTUAL_EXIT\" > " + shlex.quote(job + "/actual-process-exit.txt"),
        'exit "$HYDRA_PAIRED_ACTUAL_EXIT"', ""])


def fields(raw):
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    require(len(pairs) == len({key for key, _ in pairs}), "Ambiguous scheduler response.")
    return dict(pairs)


def tres(raw):
    pairs = [item.split("=", 1) for item in raw.split(",")]
    require(all(len(pair) == 2 for pair in pairs) and len(pairs) == len({p[0] for p in pairs}), "Invalid TRES.")
    return dict(pairs)


def check_queue_row(identifier, row, allowed_job=None):
    require(re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Invalid queue identity.")
    if "_" in identifier:
        base, task = identifier.split("_")
        require(row.get("ArrayJobId") == base and row.get("ArrayTaskId") == task, "Array identity differs.")
    else:
        require(row.get("JobId") == identifier, "Queue identity differs.")
    requested = tres(row.get("ReqTRES", ""))
    raw = row.get("AllocTRES")
    allocated = {} if raw in (None, "", "(null)") else tres(raw)
    if identifier != allowed_job:
        require(not any(key.startswith("gres/gpu") for key in requested.keys() | allocated.keys()),
                "Another owned GPU reservation/allocation exists; do not alter it.")
    return {"job_id": identifier, "requested_tres": requested, "allocated_tres": allocated, "left_unchanged": True}


def check_held(row, spec, job_id):
    validate_spec(spec)
    expected = {"JobId": job_id, "JobName": spec["job_name"], "Comment": "hydra-p6:" + spec["nonce"],
        "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
        "Account": ACCOUNT, "Partition": PARTITION, "NumCPUs": "8", "TimeLimit": wall_string(spec["seconds"]),
        "Command": spec["remote_job_directory"] + "/job.sbatch", "WorkDir": spec["remote_job_directory"],
        "StdOut": spec["remote_job_directory"] + "/slurm.out", "StdErr": spec["remote_job_directory"] + "/slurm.err"}
    require(all(row.get(key) == value for key, value in expected.items()) and row.get("NumNodes") in {"1", "1-1"},
            "Held job identity/resources differ; one pending node is required.")
    require(re.fullmatch(r"[^()]+\(" + str(UID) + r"\)", row.get("UserId", "")), "Wrong job owner.")
    requested = tres(row.get("ReqTRES", ""))
    require(all(requested.get(key) == value for key, value in {"cpu": "8", "mem": "64G", "node": "1", "gres/gpu": "1"}.items())
            and all(value == "1" for key, value in requested.items() if key.startswith("gres/gpu")), "Requested TRES differ.")


def verify_inputs(spec, source_map, study_raw):
    validate_spec(spec)
    require(type(source_map) is dict and len(source_map) == 734 and digest(canonical(source_map)) == SOURCE_MAP_SHA,
            "Frozen paired source map differs.")
    raw = ordinary_bytes(Path(SOURCE).parent / "manifest.json", 1024 * 1024)
    require(digest(raw) == MANIFEST_SHA, "Remote combined manifest changed.")
    manifest = json.loads(raw)
    require(manifest["archive_sha256"] == ARCHIVE_SHA, "Wrong combined archive.")
    total = 0
    for name, expected in source_map.items():
        require(manifest["files"].get(name) == expected, "Bundle/source map differs.")
        content = ordinary_bytes(Path(SOURCE) / name, 4 * 1024**2)
        total += len(content)
        require(total <= 48 * 1024**2 and len(content) == expected["bytes"] and digest(content) == expected["sha256"],
                "A frozen paired source changed.")
    require(type(study_raw) is str and len(study_raw.encode()) <= 65536
            and digest(study_raw.encode()) == spec["study_sha256"], "Exact study bytes are missing.")
    study = json.loads(study_raw)
    api = validate_study(study, SOURCE)
    require(study["wall_profile"] == spec["wall_profile"], "Study profile differs from allocation.")
    # Every arm must have the same completed inputs before the first symbolic arm.
    for arm in ARMS[1:]:
        directory = Path(study["arms"][arm]["adapter_directory"])
        raw = ordinary_bytes(directory / "manifest.json", 4 * 1024**2)
        require(digest(raw) == study["arms"][arm]["adapter_manifest_sha256"]
                and not (directory / "incomplete.json").exists(), "A saved arm manifest changed or is incomplete.")
        if arm != "historical_1_7b":
            require(api.training_exposure(json.loads(raw)) == study["fresh_training_exposure"], "Fresh exposure differs.")
    return study


def submit(phase, spec, source_map, study_raw):
    verify_inputs(spec, source_map, study_raw)
    queue = phase.queue()
    directory = Path(spec["remote_job_directory"])
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(job_script(spec))
    with (directory / "study.json").open("x") as stream:
        stream.write(study_raw)
    save(directory / "allocation-request.json", spec)
    argv = ["sbatch", "--hold", "--parsable", "--no-requeue", "--account=" + ACCOUNT, "--partition=" + PARTITION,
        "--nodes=1", "--ntasks=1", "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + wall_string(spec["seconds"]),
        "--job-name=" + spec["job_name"], "--comment=hydra-p6:" + spec["nonce"], "--chdir=" + str(directory),
        "--output=" + str(directory / "slurm.out"), "--error=" + str(directory / "slurm.err"), str(directory / "job.sbatch")]
    save(directory / "submit-intent.json", {"argv": argv, "automatic_retry": False})
    actual = phase.run(argv, timeout=20, must_succeed=False)
    result = {"actual_sbatch_exit_code": actual["actual_exit_code"], "uid": os.getuid(), "held": False,
        "released": False, "other_cpu_jobs": queue, "sbatch": actual}
    if actual["actual_exit_code"] == 0 and actual["stop_reason"] is None:
        job_id = actual["stdout_stderr"].strip()
        require(re.fullmatch(r"[0-9]{1,20}", job_id), "Ambiguous sbatch result; no retry.")
        result["job_id"] = job_id
        before = phase.query(job_id)
        check_held(before, spec, job_id)
        result.update(held=True, held_fields=before)
    save(directory / "held-submission.json", result)
    require(result["held"], "Exact held state was not confirmed; preserve evidence, no release/retry.")
    return result


def release(phase, spec, source_map, study_raw, record):
    require(record == reservation(spec, record.get("job_id")), "Paired reservation differs.")
    verify_inputs(spec, source_map, study_raw)
    directory = Path(spec["remote_job_directory"])
    require(json.loads(ordinary_bytes(directory / "allocation-request.json", MAX_INPUT)) == spec
            and ordinary_bytes(directory / "job.sbatch", 32768) == job_script(spec).encode()
            and ordinary_bytes(directory / "study.json", 65536) == study_raw.encode(), "Held command or study changed.")
    before = phase.query(record["job_id"])
    check_held(before, spec, record["job_id"])
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
    limit = 256 * 1024 if tail else 4 * 1024**2
    require(tail or before.st_size <= limit, "Complete evidence exceeds the frozen per-file bound.")
    offset = max(0, before.st_size - limit) if tail else 0
    with path.open("rb") as stream:
        stream.seek(offset)
        raw = stream.read(min(limit, before.st_size - offset))
    after = path.lstat()
    stable = all(getattr(before, key) == getattr(after, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns"))
    return {"bytes": len(raw), "sha256": digest(raw), "base64": base64.b64encode(raw).decode(),
        "offset": offset, "file_bytes_before": before.st_size, "file_bytes_after": after.st_size,
        "stable": stable, "complete_file": stable and offset == 0 and len(raw) == before.st_size}


def collection_files():
    return tuple(TOP_FILES) + tuple(f"result/case-{i:02d}/{name}" for i in range(16) for name in CASE_FILES)


def collect(phase, spec, record):
    require(record == reservation(spec, record.get("job_id")), "Collection reservation differs.")
    root = Path(spec["remote_job_directory"])
    require(json.loads(ordinary_bytes(root / "reservation.json", 65536)) == record, "Wrong remote reservation.")
    result = {"job_id": record["job_id"], "read_only": True, "scheduler": {}, "files": {}}
    result["scheduler"]["sacct"] = phase.run(["sacct", "-n", "-P", "-j", record["job_id"], "--format=" + SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol", "-o", "show", "job", record["job_id"]], must_succeed=False)
    total = 0
    for name in collection_files():
        row = snapshot(root / name, tail=Path(name).name in TAIL_FILES)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Observation exceeds 128 MiB; remote evidence remains untouched.")
            result["files"][name] = row
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema": "hydra-paired-control-phase-v1", "completed": False, "error": None,
                "automatic_retry": False, "commands": phase.commands}
    def deadline(_signum, _frame):
        raise TimeoutError("Bounded control phase expired.")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(int(PHASE_WALL) + 5)
    try:
        require(os.getuid() == UID and sys.version_info[:3] == (3, 11, 5), "Use the exact reviewed login Python and owner.")
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "Control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit-held", "release", "collect"}, "Unknown phase.")
        spec = request["spec"]
        validate_spec(spec)
        response["phase"] = request["phase"]
        if request["phase"] == "submit-held":
            response["result"] = submit(phase, spec, request["source_map"], request["study_raw"])
        elif request["phase"] == "release":
            response["result"] = release(phase, spec, request["source_map"], request["study_raw"], request["reservation"])
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


# Bounded scheduler transport primitives are inserted from reviewed training v2.

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


if __name__ == "__main__":
    raise SystemExit(main())
