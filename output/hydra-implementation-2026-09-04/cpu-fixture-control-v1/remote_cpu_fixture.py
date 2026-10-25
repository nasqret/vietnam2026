"""CPU-only allocation admission followed by one prepared compatibility fixture.

This file submits nothing. The fixture's separate native authorization is made
inside the job, then consumed once. Its existing guards remain authoritative.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import signal
import stat
import subprocess
import sys
import time

ACCOUNT = "plgccaiautore2026-cpu"
PARTITION = "plgrid"
CPU_UID = 105923
PYTHON_ROOT = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0"
CONTROL = "output/hydra-implementation-2026-09-04/paired-evaluation-v2"
SELF_DIRECTORY = "output/hydra-implementation-2026-09-04/cpu-fixture-control-v1"
SCHEDULER_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
MAX_LOG_BYTES = 1024 * 1024


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def ordinary(path, limit):
    path = Path(path)
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= limit,
            "Missing, linked, or oversized input: " + str(path))
    with path.open("rb") as stream:
        value = stream.read(limit + 1)
    require(len(value) == info.st_size, "Input changed while reading.")
    return value


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_LOG_BYTES, "Oversized CPU receipt.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate input key.")
            result[key] = value
        return result
    result = json.loads(raw, object_pairs_hook=pairs,
                        parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    require(type(result) is dict, "Expected one object.")
    return result


def parse_cpu_allocation(raw, reservation, seconds, memory_gib):
    """No GPU parser or fallback: exact one-node CPU request is mandatory."""
    require(type(raw) is str and len(raw.encode()) <= 65536 and "\x00" not in raw,
            "Malformed CPU scheduler response.")
    fields = {}
    for key, value in re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw):
        require(key not in fields, "Duplicate CPU scheduler field.")
        fields[key] = value
    for key, expected in {
        "JobId": reservation["job_id"], "JobName": reservation["job_name"],
        "Comment": "hydra-cpu-fixture:" + reservation["nonce"],
        "Account": ACCOUNT, "Partition": PARTITION, "JobState": "RUNNING",
        "Requeue": "0", "Restarts": "0", "NumNodes": "1", "NumCPUs": "2", "NumTasks": "1",
    }.items():
        require(fields.get(key) == expected, "CPU allocation differs at " + key)
    owner = re.fullmatch(r"[^()\s]+\((\d+)\)", fields.get("UserId", ""))
    require(owner is not None and int(owner[1]) == reservation["uid"] == os.getuid() == CPU_UID,
            "CPU allocation has another owner.")
    node = fields.get("NodeList", "")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", node) and node not in {"None", "(null)"},
            "CPU allocation must have exactly one named node.")
    require(os.uname().nodename.split(".")[0] == node.split(".")[0], "Wrong allocated CPU node.")
    observed_tres = {}
    for field in ("ReqTRES", "AllocTRES"):
        tres = {}
        for item in fields.get(field, "").split(","):
            require(item.count("=") == 1, "Missing or malformed " + field)
            key, value = item.split("=", 1)
            require(key not in tres and not key.startswith("gres"), "Duplicate TRES or unexpected GRES.")
            tres[key] = value
        require(tres.get("cpu") == "2" and tres.get("node") == "1"
                and memory_gib(tres.get("mem", "")) == 4, "CPU/memory allocation differs.")
        observed_tres[field] = tres
    require(fields.get("TresPerTask", "(null)") in {"(null)", "N/A", "None", "0", "cpu=2"},
            "Unexpected per-task TRES; only the exact two CPU allocation is admitted.")
    for field in ("Gres", "TresPerNode", "TresPerSocket", "TresPerJob"):
        require(fields.get(field, "(null)") in {"(null)", "N/A", "None", "0"}, "CPU job has GRES.")
    total, elapsed = seconds(fields.get("TimeLimit", "")), seconds(fields.get("RunTime", ""))
    require(total == 120 and 0 <= elapsed < 50, "Insufficient fixed CPU allocation remains.")
    require(not os.environ.get("SLURM_JOB_GPUS") and not os.environ.get("SLURM_STEP_GPUS")
            and not os.environ.get("CUDA_VISIBLE_DEVICES"), "Unexpected GPU exposure.")
    return {"job_id": reservation["job_id"], "node": node, "account": ACCOUNT,
            "partition": PARTITION, "cpus": 2, "memory_gib": 4, "gpus": 0,
            "seconds": total, "elapsed_seconds": elapsed, "actual_tres": observed_tres}


def invoke(argv, job, label, wall):
    """One owned process group, bounded files and wall, with an actual exit."""
    start = time.monotonic()
    process, stop, code, failure, forced_kill = None, None, None, None, False
    output, error = job / (label + ".stdout.txt"), job / (label + ".stderr.txt")
    try:
        with output.open("xb") as stdout, error.open("xb") as stderr:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=stdout,
                                       stderr=stderr, start_new_session=True)
            while process.poll() is None:
                if time.monotonic() - start > wall:
                    stop = "wall"
                elif output.stat().st_size + error.stat().st_size > MAX_LOG_BYTES:
                    stop = "output"
                if stop:
                    # The unchanged fixture handles TERM by cleaning its own
                    # separately-sessioned native child. Allow that cleanup.
                    process.terminate()
                    try:
                        process.wait(timeout=4)
                    except subprocess.TimeoutExpired:
                        forced_kill = True
                        os.killpg(process.pid, signal.SIGKILL)
                    break
                time.sleep(0.05)
            code = process.wait(timeout=3)
    except Exception as exc:
        failure = exc
    finally:
        if process is not None and process.poll() is None:
            forced_kill = True
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait(timeout=3)
    record = {"argv": argv, "actual_exit_code": code, "elapsed_seconds": time.monotonic() - start,
              "stop_reason": stop, "child_reaped": process is not None and process.returncode is not None,
              "stdout_bytes": output.stat().st_size if output.exists() else None,
              "stderr_bytes": error.stat().st_size if error.exists() else None,
              "forced_kill": forced_kill, "native_quiescence_claim": False,
              "error": None if failure is None else str(failure)[:4096], "automatic_retry": False}
    save(job / (label + ".execution.json"), record)
    if failure is not None:
        raise failure
    require(stop is None and code == 0, "CPU " + label + " failed; inspect actual execution receipt.")
    return record


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--job-directory", type=Path, required=True)
    parser.add_argument("--reservation-sha256", required=True)
    args = parser.parse_args(argv)
    os.umask(0o077)
    started = time.monotonic()
    source, job = args.source.resolve(strict=True), args.job_directory.resolve(strict=True)
    result = {"schema": "hydra-cpu-fixture-job-completion-v1", "passed": False,
              "gpu_allocations": 0, "model_calls": 0, "automatic_retry": False, "resume": False,
              "native_quiescence_claim": False, "maximum_compute_scheduler_reads": 2,
              "final_slurm_exit_still_required": True}
    try:
        require(source == args.source and job == args.job_directory, "Explicit non-symlink absolute paths required.")
        require(platform.system() == "Linux" and platform.machine() == "x86_64"
                and platform.python_version() == "3.11.5"
                and Path(sys.executable).resolve() == Path(PYTHON_ROOT + "/bin/python3").resolve(),
                "Use the exact observed x86 CPython 3.11.5 runtime.")
        require(os.environ.get("LD_LIBRARY_PATH") == PYTHON_ROOT + "/lib"
                and os.environ.get("PYTHONHASHSEED") == "0" and not sys.flags.ignore_environment,
                "CPU runtime libraries or hash seed differ.")
        raw = ordinary(job / "reservation.json", 65536)
        require(hashlib.sha256(raw).hexdigest() == args.reservation_sha256, "CPU reservation bytes changed.")
        reservation = strict_json(raw)
        require(set(reservation) == {"schema", "job_id", "job_name", "nonce", "uid", "source", "job_directory",
                "archive_sha256", "manifest_sha256", "account", "partition", "cpus", "memory_gib", "seconds",
                "gpus", "automatic_retry", "resume"}, "Unexpected CPU reservation fields.")
        require(reservation["schema"] == "hydra-cpu-fixture-reservation-v1"
                and reservation["source"] == str(source) and reservation["job_directory"] == str(job)
                and reservation["account"] == ACCOUNT and reservation["partition"] == PARTITION
                and reservation["cpus"] == 2 and reservation["memory_gib"] == 4
                and reservation["seconds"] == 120 and reservation["gpus"] == 0
                and reservation["uid"] == CPU_UID and reservation["automatic_retry"] is False
                and reservation["resume"] is False and re.fullmatch(r"[0-9a-f]{32}", reservation["nonce"])
                and re.fullmatch(r"[0-9]{1,20}", reservation["job_id"])
                and os.environ.get("SLURM_JOB_ID") == reservation["job_id"], "CPU identity or budget differs.")
        for name in ("archive_sha256", "manifest_sha256"):
            require(re.fullmatch(r"[0-9a-f]{64}", reservation[name]), "Invalid CPU package pin.")
        manifest_raw = ordinary(source.parent / "manifest.json", 1024 * 1024)
        manifest = strict_json(manifest_raw)
        require(hashlib.sha256(manifest_raw).hexdigest() == reservation["manifest_sha256"]
                and manifest["archive_sha256"] == reservation["archive_sha256"], "CPU package identity differs.")
        # Every executable input is rehashed by fixture.prepare. These outer files
        # must additionally match the sealed package before their first action.
        for relative in (SELF_DIRECTORY + "/remote_cpu_fixture.py", SELF_DIRECTORY + "/remote_cpu_job.sh",
                         CONTROL + "/remote_provider_smoke.py", CONTROL + "/fixture/native_fixture.py"):
            data = ordinary(source / relative, 1024 * 1024)
            require(manifest["files"][relative] == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()},
                    "CPU control source changed: " + relative)
        require(hashlib.sha256(ordinary(source / CONTROL / "remote_provider_smoke.py", 65536)).hexdigest()
                == SCHEDULER_SHA, "Reviewed scheduler helper changed.")
        save(job / "reservation.claimed.json", {"schema": "hydra-cpu-fixture-job-consumption-v1",
             "reservation_sha256": args.reservation_sha256, "pid": os.getpid(), "uid": os.getuid(),
             "job_id": reservation["job_id"], "nonce": reservation["nonce"], "gpu_allocations": 0})
        spec = importlib.util.spec_from_file_location("cpu_only_scheduler", source / CONTROL / "remote_provider_smoke.py")
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        query_start = time.monotonic()
        scheduler_raw, actual_exit = helper.read_scontrol(reservation["job_id"])
        save(job / "scheduler-admission.raw.json", {"actual_exit_code": actual_exit, "raw": scheduler_raw,
             "elapsed_seconds": time.monotonic() - query_start, "query_count": 1, "automatic_retry": False})
        require(actual_exit == 0, "CPU scheduler query returned a nonzero exit.")
        observed = parse_cpu_allocation(scheduler_raw, reservation, helper.seconds, helper.memory_gib)
        save(job / "scheduler-admission.json", observed)
        fixture = source / CONTROL / "fixture/native_fixture.py"
        authorization = job / "fixture-authorization.json"
        invoke([sys.executable, "-B", "-s", str(fixture), "prepare", "--app-root", str(source / "hydra-playground"),
                "--authorization", str(authorization), "--output", str(job / "fixture-result"),
                "--job-id", reservation["job_id"]], job, "prepare", 20)
        auth_sha = hashlib.sha256(ordinary(authorization, 65536)).hexdigest()
        save(job / "prepared-authorization-pin.json", {"sha256": auth_sha})
        invoke([sys.executable, "-B", "-s", str(fixture), "run", "--authorization", str(authorization),
                "--authorization-sha256", auth_sha], job, "fixture", 45)
        completion = strict_json(ordinary(job / "fixture-result/completion.json", 1024 * 1024))
        require(completion.get("passed") is True, "Fixture did not pass; no compatibility claim is made.")
        result.update(passed=True, fixture_completion_sha256=hashlib.sha256(canonical(completion)).hexdigest(),
                      reservation_sha256=args.reservation_sha256, scheduler=observed)
    except Exception as error:
        result.update(error_type=type(error).__name__, error=str(error)[:4096])
    finally:
        result["elapsed_seconds"] = time.monotonic() - started
        save(job / "job-completion.json", result)
        print(canonical(result).decode(), flush=True)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
