"""One held teacher allocation against the exact combined source package.

Prepared only. This transport never imports a teacher, model, tokenizer, or native
engine. The existing sealed teacher job body runs only after a separate release.
Bounded subprocess/queue/snapshot helpers are copied unchanged from reviewed P6 v2.
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
SOURCE = CAMPAIGN + "/bundles/combined-source-01/source"
BASE = CAMPAIGN + "/authenticated-bases-01/deepseek-prover-v2-7b-teacher"
ATTEMPT = "p7-teacher-32-v2-01"
JOB = CAMPAIGN + "/jobs/" + ATTEMPT
MODEL_KEY = "deepseek-prover-v2-7b-teacher"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
REMOTE_USER = "plgnasqret"
ARCHIVE_SHA = "5097481cdaba15d3942ce153dc7943786c80199e9c4ccda6936419bafb494677"
MANIFEST_SHA = "e874311f7561564f84a526cff226e497cd8e9c3dcc8122f13b9871cc96ecb031"
SOURCE_MAP_SHA = "f3bad0a87debd9f661ba5a239814e52ba50ba96d7fdfff0adeeca8cf1f25b3b1"
SELECTION = "output/p7-prototype/selection-32-v1.json"
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
JOB_BODY = "output/p7-prototype/remote_teacher_job.sh"
JOB_BODY_SHA = "31db28e3b2f85e4d14ec414c0d36b205c6be3c72d30bdeba0ba721bcfb85fc1b"
BASE_IDENTITY_SHA = "22ce838dbec7b31ea0285e73a956e8ea61d982beb40ae1da62942cdaa3fcc71d"
PRIOR_ADMISSION_CONTENT_SHA = "cc9fee3973d32be22c8e0164ea55b76662c589215a018e81c20aa4705a42978e"
PRIOR_ADMISSION = CAMPAIGN + "/jobs/p7-clean-base-admission-01/result.json"
MAX_INPUT = 256 * 1024
MAX_COMMAND_OUTPUT = 65536
MAX_OBSERVATION = 8 * 1024**2
PHASE_WALL = 550.0
SACCT_FORMAT = ("JobIDRaw,JobName%100,User,Account,Partition,State,ExitCode,ElapsedRaw,"
                "TimelimitRaw,AllocCPUS,ReqMem,ReqTRES%300,AllocTRES%300,NodeList")
TAILS = {"slurm.out", "slurm.err", "result/scheduler.jsonl"}
FILES = tuple(sorted(TAILS | {"actual-process-exit.txt", "reservation.json", "reservation.json.claimed",
    "release-completion.json", "result/request.json", "result/completion.json",
    "result/model-admission.json", "result/positive-continuations.json", "result/interrupted-state.json"}))


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


def validate_spec(spec):
    fixed = {"schema": "hydra-p7-teacher-allocation-v1", "attempt": ATTEMPT, "model_key": MODEL_KEY,
        "job_name": "hydra-" + ATTEMPT, "remote_job_directory": JOB, "source": SOURCE, "base_directory": BASE,
        "account": ACCOUNT, "partition": PARTITION, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "archive_sha256": ARCHIVE_SHA, "manifest_sha256": MANIFEST_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "selection_sha256": SELECTION_SHA, "job_body_sha256": JOB_BODY_SHA, "base_identity_sha256": BASE_IDENTITY_SHA,
        "states": 32, "max_proposals": 128, "max_model_calls": 64, "max_output_tokens": 512,
        "max_total_generated_tokens": 32768, "max_input_tokens": 4096,
        "training_updates": 0, "student_calls": 0, "solver_calls": 0,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    require(type(spec) is dict and set(spec) == set(fixed) | {"seconds", "nonce"}, "Unexpected teacher allocation fields.")
    require(all(type(spec[key]) is type(value) and spec[key] == value for key, value in fixed.items()),
            "Teacher allocation source, scope, resource, or authority differs.")
    integer(spec["seconds"], 600, 7200, "teacher duration")
    require(spec["seconds"] % 60 == 0, "Teacher duration must be explicit whole minutes.")
    require(type(spec["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"]), "Invalid teacher nonce.")


def make_spec(seconds, nonce):
    spec = {"schema": "hydra-p7-teacher-allocation-v1", "attempt": ATTEMPT, "model_key": MODEL_KEY,
        "job_name": "hydra-" + ATTEMPT, "remote_job_directory": JOB, "source": SOURCE, "base_directory": BASE,
        "account": ACCOUNT, "partition": PARTITION, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "archive_sha256": ARCHIVE_SHA, "manifest_sha256": MANIFEST_SHA, "source_pins_sha256": SOURCE_MAP_SHA,
        "selection_sha256": SELECTION_SHA, "job_body_sha256": JOB_BODY_SHA, "base_identity_sha256": BASE_IDENTITY_SHA,
        "states": 32, "max_proposals": 128, "max_model_calls": 64, "max_output_tokens": 512,
        "max_total_generated_tokens": 32768, "max_input_tokens": 4096,
        "training_updates": 0, "student_calls": 0, "solver_calls": 0,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False,
        "seconds": seconds, "nonce": nonce}
    validate_spec(spec)
    return spec


def reservation(spec, job_id, uid):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Invalid scalar teacher job ID.")
    require(type(uid) is int and uid == 105923, "Wrong teacher reservation owner.")
    return {"schema": "hydra-p7-teacher-reservation-v1", "job_id": job_id, "uid": uid,
        **{key: spec[key] for key in ("job_name", "nonce", "account", "partition", "model_key", "gpus", "nodes",
                                    "cpus", "memory_gib", "seconds")}}


def job_script(spec):
    validate_spec(spec)
    # The unchanged shell owns module loading and invokes the teacher with -B,
    # deliberately without -P so its pinned sibling provider remains importable.
    argv = ["/bin/bash", "-l", SOURCE + "/" + JOB_BODY, SOURCE, JOB, BASE]
    return "#!/bin/bash -l\nset -euo pipefail\numask 077\nexec " + shlex.join(argv) + "\n"


def verify_sources(spec, source_map):
    validate_spec(spec)
    require(type(source_map) is dict and 600 <= len(source_map) <= 1200
            and digest(canonical(source_map)) == SOURCE_MAP_SHA, "Fixed teacher source map differs.")
    manifest_raw = ordinary_bytes(Path(SOURCE).parent / "manifest.json", 2 * 1024**2)
    require(digest(manifest_raw) == MANIFEST_SHA, "Remote combined manifest changed.")
    manifest = json.loads(manifest_raw)
    require(manifest.get("archive_sha256") == ARCHIVE_SHA, "Wrong remote combined archive.")
    total = 0
    for relative, expected in source_map.items():
        path = Path(relative)
        require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == relative,
                "Invalid fixed source path.")
        require(manifest["files"].get(relative, {}).get("sha256") == expected, "Teacher map and package differ.")
        data = ordinary_bytes(Path(SOURCE) / relative, 4 * 1024**2)
        total += len(data)
        require(total <= 48 * 1024**2 and digest(data) == expected, "Teacher source bytes changed.")
    for relative, expected in ((SELECTION, SELECTION_SHA), (JOB_BODY, JOB_BODY_SHA)):
        require(digest(ordinary_bytes(Path(SOURCE) / relative, 256 * 1024)) == expected,
                "Teacher selection or job body changed.")
    selection = json.loads(ordinary_bytes(Path(SOURCE) / SELECTION, 256 * 1024))
    require(selection.get("training_only") is True and len(selection.get("states", [])) == 32,
            "Expected exact 32-state training selection.")
    prior = json.loads(ordinary_bytes(Path(PRIOR_ADMISSION), 65536))
    require(digest(canonical(prior)) == PRIOR_ADMISSION_CONTENT_SHA and prior.get("completed") is True
            and prior.get("view") == BASE and prior.get("identity", {}).get("base_identity_sha256") == BASE_IDENTITY_SHA
            and prior["identity"].get("weight_bytes_fully_hashed") is True
            and prior["identity"].get("model_loaded") is False, "Prior full teacher base admission differs.")
    base = Path(BASE)
    require(base.resolve(strict=True) == base and base.is_dir(), "Missing exact clean teacher base view.")
    require({p.name for p in base.iterdir()} == set(prior["identity"]["files"]), "Clean teacher base inventory differs.")
    for name, expected in prior["identity"]["files"].items():
        path = (base / name).resolve(strict=True)
        require(path.is_file() and path.stat().st_size == expected["bytes"], "Teacher base file size differs.")
    # Full current weight hashing remains in the unchanged teacher loader,
    # immediately before its actual model load; no inference occurs on login.


def submit(phase, spec, source_map):
    require(os.getuid() == 105923, "Wrong remote UID.")
    verify_sources(spec, source_map)
    queue = phase.queue()
    directory = Path(JOB)
    directory.mkdir(parents=True, exist_ok=False)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(job_script(spec))
    save(directory / "allocation-request.json", spec)
    for name, data in (("selection.json", ordinary_bytes(Path(SOURCE) / SELECTION, 256 * 1024)),
                       ("selection.sha256", (SELECTION_SHA + "\n").encode()),
                       ("source-pins.sha256", (SOURCE_MAP_SHA + "\n").encode())):
        with (directory / name).open("xb") as stream:
            stream.write(data)
    argv = ["sbatch", "--hold", "--parsable", "--no-requeue", "--account=" + ACCOUNT, "--partition=" + PARTITION,
        "--nodes=1", "--ntasks=1", "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1",
        "--time=" + wall_string(spec["seconds"]), "--job-name=" + spec["job_name"],
        "--comment=hydra-p6:" + spec["nonce"], "--chdir=" + JOB,
        "--output=" + JOB + "/slurm.out", "--error=" + JOB + "/slurm.err", JOB + "/job.sbatch"]
    save(directory / "submit-intent.json", {"argv": argv, "automatic_retry": False})
    actual = phase.run(argv, timeout=20, must_succeed=False)
    result = {"actual_sbatch_exit_code": actual["actual_exit_code"], "uid": os.getuid(), "held": False,
              "released": False, "other_cpu_jobs": queue, "sbatch": actual}
    if actual["actual_exit_code"] == 0 and actual["stop_reason"] is None:
        job_id = actual["stdout_stderr"].strip()
        require(re.fullmatch(r"[0-9]{1,20}", job_id), "Ambiguous actual teacher job ID; no retry.")
        result["job_id"] = job_id
        before = phase.query(job_id)
        check_held(before, spec, job_id, os.getuid())
        require(before.get("NumTasks") == "1" and before.get("AllocTRES") in {"(null)", None, ""},
                "Held teacher already has allocated resources or multiple tasks.")
        result.update(held=True, held_fields=before)
    save(directory / "held-submission.json", result)
    require(result["held"], "Exact held submission not confirmed; preserve and do not release/retry.")
    return result


def release(phase, spec, source_map, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Wrong teacher reservation.")
    verify_sources(spec, source_map)
    directory = Path(JOB)
    require(json.loads(ordinary_bytes(directory / "allocation-request.json", MAX_INPUT)) == spec
            and ordinary_bytes(directory / "job.sbatch", 32768) == job_script(spec).encode(),
            "Prepared teacher request or script changed.")
    require(digest(ordinary_bytes(directory / "selection.json", 256 * 1024)) == SELECTION_SHA
            and ordinary_bytes(directory / "selection.sha256", 65) == (SELECTION_SHA + "\n").encode()
            and ordinary_bytes(directory / "source-pins.sha256", 65) == (SOURCE_MAP_SHA + "\n").encode(),
            "Prepared teacher selection or source binding changed.")
    before = phase.query(record["job_id"])
    check_held(before, spec, record["job_id"], os.getuid())
    require(before.get("NumTasks") == "1" and before.get("AllocTRES") in {"(null)", None, ""},
            "Held teacher resources differ.")
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


def collect(phase, spec, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Wrong teacher observation identity.")
    result = {"job_id": record["job_id"], "read_only": True, "scheduler": {}, "files": {},
              "full_native_proof_artifacts_downloaded": False, "remote_result_directory": JOB + "/result"}
    result["scheduler"]["sacct"] = phase.run(["sacct", "-n", "-P", "-j", record["job_id"], "--format=" + SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol", "-o", "show", "job", record["job_id"]], must_succeed=False)
    total = 0
    for name in FILES:
        row = snapshot(Path(JOB) / name, tail=name in TAILS)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Teacher observation byte bound exceeded.")
            result["files"][name] = row
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema": "hydra-p7-teacher-control-phase-v1", "completed": False, "error": None,
                "automatic_retry": False, "commands": phase.commands}
    def deadline(_signum, _frame):
        raise TimeoutError("Bounded teacher control phase expired.")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(int(PHASE_WALL) + 5)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "Teacher control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit", "release", "collect"}, "Unknown phase.")
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
        raw = canonical(response) + b"\n"
        require(len(raw) <= 14 * 1024**2, "Remote teacher phase response exceeds its bound.")
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()
    return 0 if response["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
