"""Fixed CPU monitor package: one stage, held submit, release, or read-only collection.

This stdlib-only control is sent through SSH -c only after normal review.
It never imports the probe, changes a source bundle, retries, or cancels a job.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
import re
import select
import signal
import stat
import subprocess
import sys
import time

PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
PACKAGE = Path(CAMPAIGN + "/diagnostics/p6-paired-child-linux-probe-01")
SOURCE = Path(CAMPAIGN + "/bundles/combined-source-04/source")
SOURCE_CONTROL = "output/hydra-implementation-2026-09-04/paired-evaluation-v2"
SOURCE_MANIFEST = {"bytes": 253561, "sha256": "4beeb386a118229b4e3fa9b751d7a4a560853252ab3103cff661a48dc2eb9f0e"}
ACCOUNT, PARTITION, UID = "plgcredibleai2026-cpu", "plgrid", 105923
JOB_NAME = "hydra-p6-child-linux-probe-01"
PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
ALLOCATION = {"cpus": 1, "gpus": 0, "nodes": 1, "memory_bytes": 1073741824, "seconds": 60}
PINS = {'run_probe.py': {'bytes': 20696, 'sha256': '2d65cb4391e37e8b756309263e8642ff97ea58767524b1ca2b012a3fb21f4ad3'}, 'paired_case_worker.py': {'bytes': 11905, 'sha256': '4115ec9ed131944f40024a2a9269e50ddfdacbe681c92e978f5dd43d7f990b64'}, 'paired_controller.py': {'bytes': 53996, 'sha256': 'cb5ba7840f85c00bf54953bddf5bb168414a0e6e84c9b41369da63b315e195be'}, 'paired_common.py': {'bytes': 21344, 'sha256': 'd8f5dda5bfc1fb9e6769e4dc2f65591c2fb788db909842862e4009d80583d822'}, 'job.sh': {'bytes': 943, 'sha256': '7094b959e8db6eefb6f6209522c57f6d855c7b9d2bb64af1a1a6284dc4b8b875'}, 'manifest.json': {'bytes': 2263, 'sha256': '0a2781c6bb8514c799ea7d9f1b47747f565c61ac07a9f3410a6be46290d0d051'}}
UPLOADS = ('run_probe.py', 'paired_case_worker.py', 'paired_controller.py', 'job.sh', 'manifest.json')
COPIES = ('paired_common.py',)
CONTROL_FILES = {"stage-request.json", "stage-completion.json", "submit-intent.json",
                 "submit-command.json", "held-submission.json", "release-intent.json", "release-command.json"}
RUN_FILES = {"request.json", "result.json"} | {
    "case-00/" + name for name in ("case-request.json", "execution.json", "stdout", "stderr")
} | {"case-00/query-%02d.json" % i for i in range(16)}
MAX_INPUT, MAX_COMMAND_OUTPUT, MAX_RESPONSE = 128 * 1024, 65536, 4 * 1024**2
PHASE_WALL = 120.0
SACCT_FORMAT = "JobIDRaw,State%40,ExitCode,ElapsedRaw,AllocTRES%300,TimelimitRaw"


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


def owned_directory(path):
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == UID and path.resolve(strict=True) == path,
            "Expected an ordinary owned directory: " + str(path))


def owned_bytes(path, limit):
    raw = ordinary_bytes(path, limit)
    info = path.lstat()
    require(info.st_uid == UID and info.st_nlink == 1, "Expected a single-link owned file.")
    return raw


def write_bytes(path, raw):
    require(len(raw) <= MAX_RESPONSE, "Control file bound exceeded.")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    path.chmod(0o444)
    require(owned_bytes(path, len(raw)) == raw, "Exclusive write verification failed.")


def save(path, value):
    write_bytes(Path(path), canonical(value) + b"\n")


def pin(raw):
    return {"bytes": len(raw), "sha256": digest(raw)}


def fields(raw):
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    require(len(pairs) == len({key for key, _ in pairs}), "Ambiguous scheduler response.")
    return dict(pairs)


def tres(raw):
    pairs = [item.split("=", 1) for item in raw.split(",")]
    require(all(len(pair) == 2 and all(pair) for pair in pairs)
            and len(pairs) == len({p[0] for p in pairs}), "Invalid TRES.")
    return dict(pairs)


def cpu_tres(raw):
    value = tres(raw)
    require(set(value) <= {"cpu", "mem", "node", "billing"}
            and value.get("cpu") == "1" and value.get("node") == "1"
            and value.get("mem") in {"1G", "1024M"}
            and ("billing" not in value or value["billing"] == "1"), "CPU-only one-GiB TRES differ.")
    return value


def check_queue_row(identifier, row, allowed_job=None):
    require(re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Invalid queue identity.")
    if "_" in identifier:
        base, task = identifier.split("_")
        require(row.get("ArrayJobId") == base and row.get("ArrayTaskId") == task, "Array identity differs.")
    else:
        require(row.get("JobId") == identifier, "Queue identity differs.")
    require(re.fullmatch(r"[^()]+\(" + str(UID) + r"\)", row.get("UserId", "")), "Wrong queue owner.")
    requested = tres(row.get("ReqTRES", ""))
    allocated = {} if row.get("AllocTRES") in (None, "", "(null)") else tres(row["AllocTRES"])
    gpu = any(key.startswith("gres/gpu") for key in requested.keys() | allocated.keys())
    gpu = gpu or any("gpu" in row.get(key, "").lower() for key in ("Gres", "TresPerNode", "TresPerTask", "TresPerJob"))
    name = row.get("JobName", "").lower()
    hydra = name.startswith(("hydra", "p6-", "p7-", "peano"))
    hydra = hydra or any(row.get(key, "").startswith(PROJECT + "/") for key in ("Command", "WorkDir"))
    if identifier != allowed_job:
        require(not gpu and not hydra, "Conflicting owned GPU or Hydra CPU work exists; leave it unchanged.")
    return {"job_id": identifier, "job_name": row.get("JobName"), "state": row.get("JobState"),
            "requested_tres": requested, "allocated_tres": allocated, "left_unchanged": True}


def check_identity(row, nonce, job_id, *, held):
    expected = {"JobId": job_id, "JobName": JOB_NAME, "Comment": "hydra-linux-monitor:" + nonce,
                "Requeue": "0", "Restarts": "0", "Account": ACCOUNT, "Partition": PARTITION,
                "NumCPUs": "1", "NumTasks": "1", "TimeLimit": "00:01:00",
                "Command": str(PACKAGE / "job.sh"), "WorkDir": str(PACKAGE),
                "StdOut": str(PACKAGE / ("slurm-" + job_id + ".out")),
                "StdErr": str(PACKAGE / ("slurm-" + job_id + ".err"))}
    if held:
        expected.update(JobState="PENDING", Reason="JobHeldUser")
    require(all(row.get(key) == value for key, value in expected.items())
            and row.get("NumNodes") in {"1", "1-1"}, "Exact CPU job identity/resources differ.")
    require(re.fullmatch(r"[^()]+\(" + str(UID) + r"\)", row.get("UserId", "")), "Wrong CPU job owner.")
    cpu_tres(row.get("ReqTRES", ""))
    raw = row.get("AllocTRES")
    if raw not in (None, "", "(null)"):
        cpu_tres(raw)
    empty = (None, "", "(null)", "N/A", "None")
    require(all(row.get(key) in empty for key in ("Gres", "TresPerNode", "TresPerJob"))
            and row.get("TresPerTask") in empty + ("cpu=1", "cpu:1"), "CPU job has a GRES request.")


def verify_sources():
    owned_directory(SOURCE)
    raw = owned_bytes(SOURCE.parent / "manifest.json", SOURCE_MANIFEST["bytes"])
    require(pin(raw) == SOURCE_MANIFEST, "The exact source04 manifest is absent or changed.")
    manifest = json.loads(raw)
    require(manifest.get("schema") == "hydra-combined-inference-source-v4"
            and manifest.get("runtime_destination") == "combined-source-04/source"
            and manifest.get("file_count") == 1325, "Wrong source04 identity.")
    copied = {}
    for name in COPIES:
        relative = SOURCE_CONTROL + "/" + name
        require(manifest["files"].get(relative) == PINS[name], "Source04 copy descriptor differs.")
        data = owned_bytes(SOURCE / relative, PINS[name]["bytes"])
        require(pin(data) == PINS[name], "The selected existing source file changed.")
        copied[name] = data
    return copied


def verify_package(*, before_run, job_id=None):
    owned_directory(PACKAGE)
    owned_directory(PACKAGE / "control")
    require({item.name for item in (PACKAGE / "control").iterdir()} <= CONTROL_FILES,
            "Unlisted control artifact in fixed package.")
    for item in (PACKAGE / "control").iterdir():
        owned_bytes(item, MAX_RESPONSE)
    allowed = set(PINS) | {"control"}
    if not before_run:
        require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Actual scalar job ID required.")
        allowed |= {"run-01", "actual-process-exit.txt", "slurm-" + job_id + ".out", "slurm-" + job_id + ".err"}
    require({item.name for item in PACKAGE.iterdir()} <= allowed, "Unlisted or already-run package content.")
    for name, expected in PINS.items():
        require(pin(owned_bytes(PACKAGE / name, expected["bytes"])) == expected, "Pinned probe package changed.")
    require(os.access(PYTHON, os.X_OK) and os.path.isfile(PYTHON)
            and os.access("/usr/bin/timeout", os.X_OK), "Exact Python/timeout prerequisite unavailable.")


def request_binding(request):
    return {key: request[key] for key in ("schema", "nonce", "manifest_sha256", "remote_control_sha256")}


def prior_stage(request):
    recorded = json.loads(owned_bytes(PACKAGE / "control/stage-request.json", MAX_INPUT))
    require(request_binding(recorded) == request_binding(request), "Stage nonce/source binding differs.")
    completed = json.loads(owned_bytes(PACKAGE / "control/stage-completion.json", MAX_RESPONSE))
    require(completed.get("completed") is True and completed.get("binding") == request_binding(request),
            "No complete matching stage exists; do not retry it.")


def prior_held(request):
    prior_stage(request)
    recorded = json.loads(owned_bytes(PACKAGE / "control/held-submission.json", MAX_RESPONSE))
    job_id = recorded.get("job_id")
    require(recorded.get("held_confirmed") is True and recorded.get("nonce") == request["nonce"]
            and type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id)
            and job_id == request["job_id"], "Matching actual held submission required.")
    return job_id


def stage(request, phase):
    copied = verify_sources()
    require(type(request["uploads"]) is dict and set(request["uploads"]) == set(UPLOADS), "Exactly five uploads required.")
    uploaded = {name: base64.b64decode(request["uploads"][name], validate=True) for name in UPLOADS}
    require(all(pin(raw) == PINS[name] for name, raw in uploaded.items())
            and sum(map(len, uploaded.values())) == 89803, "Uploaded bytes differ from the sealed payload.")
    owned_directory(Path(CAMPAIGN))
    require(not PACKAGE.exists() and not PACKAGE.is_symlink(), "Package already exists; no staging retry.")
    queue = phase.queue()
    if not PACKAGE.parent.exists():
        PACKAGE.parent.mkdir(mode=0o700)
    owned_directory(PACKAGE.parent)
    PACKAGE.mkdir(mode=0o700)
    (PACKAGE / "control").mkdir(mode=0o700)
    save(PACKAGE / "control/stage-request.json", request)
    for name, raw in {**copied, **uploaded}.items():
        write_bytes(PACKAGE / name, raw)
    verify_package(before_run=True)
    require(all(owned_bytes(SOURCE / (SOURCE_CONTROL + "/" + name), PINS[name]["bytes"]) == raw
                for name, raw in copied.items()), "Copy sources changed during staging.")
    result = {"completed": True, "binding": request_binding(request), "package": str(PACKAGE),
              "uploaded_files": {name: PINS[name] for name in UPLOADS}, "uploaded_bytes": 89803,
              "copied_files": {name: PINS[name] for name in COPIES}, "normal_copies_no_hardlinks": True,
              "source_manifest": SOURCE_MANIFEST, "payload_bytes": 111147, "queue": queue,
              "allocation_created": False, "automatic_retry": False}
    save(PACKAGE / "control/stage-completion.json", result)
    return result


def submit(request, phase):
    prior_stage(request)
    verify_sources()
    verify_package(before_run=True)
    queue = phase.queue()
    argv = ["sbatch", "--parsable", "--hold", "--no-requeue", "--account=" + ACCOUNT,
            "--partition=" + PARTITION, "--nodes=1", "--ntasks=1", "--cpus-per-task=1", "--mem=1024M",
            "--time=00:01:00", "--job-name=" + JOB_NAME, "--comment=hydra-linux-monitor:" + request["nonce"],
            "--output=" + str(PACKAGE / "slurm-%j.out"), "--error=" + str(PACKAGE / "slurm-%j.err"),
            str(PACKAGE / "job.sh"), str(PACKAGE), PINS["manifest.json"]["sha256"]]
    save(PACKAGE / "control/submit-intent.json", {"binding": request_binding(request), "argv": argv,
         "cwd": str(PACKAGE), "queue": queue, "allocation": ALLOCATION, "automatic_retry": False})
    os.chdir(PACKAGE)
    result = phase.run(argv, timeout=20.0, must_succeed=False)
    save(PACKAGE / "control/submit-command.json", result)
    require(result["actual_exit_code"] == 0 and result["stop_reason"] is None,
            "Held submission failed or is uncertain; preserve evidence, never submit again.")
    job_id = result["stdout_stderr"].strip()
    require(re.fullmatch(r"[0-9]{1,20}", job_id), "Held submission identity is uncertain; no retry.")
    row = phase.query(job_id)
    confirmed = False
    try:
        check_identity(row, request["nonce"], job_id, held=True)
        confirmed = True
    finally:
        save(PACKAGE / "control/held-submission.json", {"job_id": job_id, "nonce": request["nonce"],
             "held_confirmed": confirmed, "actual_sbatch_exit_code": result["actual_exit_code"], "scheduler": row,
             "allocation": ALLOCATION, "automatic_release": False, "automatic_retry": False})
    return {"job_id": job_id, "nonce": request["nonce"], "held_confirmed": True,
            "scheduler": row, "queue": queue, "allocation": ALLOCATION, "released": False}


def release(request, phase):
    job_id = prior_held(request)
    verify_sources()
    verify_package(before_run=True)
    queue = phase.queue(allowed_job=job_id)
    row = phase.query(job_id)
    check_identity(row, request["nonce"], job_id, held=True)
    save(PACKAGE / "control/release-intent.json", {"job_id": job_id, "binding": request_binding(request),
         "queue": queue, "scheduler": row, "allocation": ALLOCATION, "automatic_retry": False})
    result = phase.run(["scontrol", "release", job_id], must_succeed=False)
    save(PACKAGE / "control/release-command.json", result)
    require(result["actual_exit_code"] == 0 and result["stop_reason"] is None,
            "Release failed or is uncertain; do not repeat or cancel it automatically.")
    return {"job_id": job_id, "release_command_acknowledged": True, "allocation": ALLOCATION,
            "job_running_or_complete_inferred": False, "automatic_retry": False}


def scheduler_summary(raw, job_id):
    lines = [line for line in raw.splitlines() if line.strip()]
    require(len(lines) <= 3, "Unexpected CPU accounting row count.")
    seen, primary = set(), None
    for line in lines:
        parts = line.split("|")
        if len(parts) == 7 and parts[-1] == "":
            parts.pop()
        require(len(parts) == 6 and parts[0] in {job_id, job_id + ".batch", job_id + ".extern"}
                and parts[0] not in seen, "Unexpected or ambiguous CPU accounting row.")
        seen.add(parts[0])
        if parts[0] == job_id:
            require(re.fullmatch(r"[0-9]+:[0-9]+", parts[2]) and parts[3].isdigit()
                    and parts[5] == "1", "CPU accounting exit/time fields differ.")
            allocation = None if not parts[4] else cpu_tres(parts[4])
            primary = {"job_id": job_id, "state": parts[1], "slurm_exit_code": parts[2],
                       "elapsed_scheduler_seconds": int(parts[3]), "allocated_tres": allocation,
                       "time_limit_minutes": 1}
    return primary


def collect(request, phase):
    job_id = prior_held(request)
    verify_package(before_run=False, job_id=job_id)
    scheduler = phase.run(["sacct", "-j", job_id, "--parsable2", "--noheader", "--format=" + SACCT_FORMAT])
    summary = scheduler_summary(scheduler["stdout_stderr"], job_id)
    current = phase.run(["scontrol", "-o", "show", "job", job_id], must_succeed=False)
    if current["actual_exit_code"] == 0 and current["stop_reason"] is None:
        check_identity(fields(current["stdout_stderr"]), request["nonce"], job_id, held=False)
    files, missing, total = {}, [], 0
    paths = {"actual-process-exit.txt": 16, "slurm-" + job_id + ".out": 65536,
             "slurm-" + job_id + ".err": 65536}
    run = PACKAGE / "run-01"
    if run.exists() or run.is_symlink():
        owned_directory(run)
        for child in run.rglob("*"):
            rel = child.relative_to(run).as_posix()
            if rel in {"case-00"}:
                owned_directory(child)
            else:
                require(rel in RUN_FILES, "Unlisted probe result artifact.")
                raw = owned_bytes(child, 256 * 1024)
                total += len(raw)
        require(total <= 2 * 1024**2, "Probe result scope exceeded its total byte limit.")
    paths.update({"run-01/" + name: 256 * 1024 for name in RUN_FILES})
    retained_run = 0
    for relative, maximum in sorted(paths.items()):
        path = PACKAGE / relative
        if not path.exists() and not path.is_symlink():
            missing.append(relative)
            continue
        raw = owned_bytes(path, maximum)
        if relative.startswith("run-01/"):
            retained_run += len(raw)
        require(retained_run <= 2 * 1024**2, "Collected probe bytes exceeded their scope.")
        files[relative] = {**pin(raw), "base64": base64.b64encode(raw).decode("ascii")}
    actual = None
    if "actual-process-exit.txt" in files:
        raw = base64.b64decode(files["actual-process-exit.txt"]["base64"])
        require(re.fullmatch(rb"[0-9]{1,3}\n", raw), "Malformed observed process exit.")
        actual = int(raw)
    return {"job_id": job_id, "files": files, "missing_files": missing, "scheduler": summary,
            "actual_probe_process_exit_code": actual, "run_bytes_collected": retained_run,
            "observation_only": True, "probe_success_claimed": False,
            "actual_tool_companion_required": True, "automatic_retry": False}


# The bounded scheduler child and Phase below are copied verbatim from the
# reviewed paired-v5 remote control; only globals and CPU guards differ.
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


def main():
    os.umask(0o077)
    began, request, phase = time.monotonic(), {}, Phase()
    response = {"schema": "hydra-child-linux-monitor-control-response-v1", "completed": False,
                "phase": None, "nonce": None, "job_id": None, "phase_result": None, "error": None,
                "probe_success_claimed": False, "automatic_retry": False, "automatic_next_phase": False}
    def expired(signum, frame):
        raise TimeoutError("Remote CPU control wall limit.")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(125)
    try:
        require(os.getuid() == UID and sys.version_info[:2] == (3, 11), "Wrong login owner or Python runtime.")
        raw = sys.stdin.buffer.read(MAX_INPUT + 1)
        require(len(raw) <= MAX_INPUT, "CPU control request exceeds its input bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("schema") == "hydra-child-linux-monitor-control-request-v1",
                "Unknown control request.")
        action = request.get("phase")
        require(action in {"stage", "submit-held", "release", "collect"}, "Only four explicit phases are allowed.")
        expected = {"schema", "phase", "nonce", "manifest_sha256", "remote_control_sha256"}
        expected |= {"uploads"} if action == "stage" else ({"job_id"} if action in {"release", "collect"} else set())
        require(set(request) == expected and type(request.get("nonce")) is str
                and re.fullmatch(r"[0-9a-f]{32}", request["nonce"])
                and request.get("manifest_sha256") == PINS["manifest.json"]["sha256"]
                and valid_sha(request.get("remote_control_sha256")), "Unexpected phase identity/source fields.")
        if "job_id" in request:
            require(type(request["job_id"]) is str and re.fullmatch(r"[0-9]{1,20}", request["job_id"]),
                    "An actual scalar job ID is required.")
        response.update(phase=action, nonce=request["nonce"], job_id=request.get("job_id"),
                        manifest_sha256=request["manifest_sha256"], remote_control_sha256=request["remote_control_sha256"])
        # Do not let inherited sbatch option variables expand the fixed request.
        removed = sorted(key for key in os.environ if key.startswith("SBATCH_"))
        for key in removed:
            del os.environ[key]
        response["removed_sbatch_environment_names"] = removed
        result = {"stage": stage, "submit-held": submit, "release": release, "collect": collect}[action](request, phase)
        response.update(phase_result=result, job_id=result.get("job_id"), completed=True)
    except BaseException as error:
        response["completed"] = False
        response["error"] = {"type": type(error).__name__, "detail": str(error)[:1200]}
    finally:
        signal.alarm(0)
        response.update(commands=phase.commands, elapsed_seconds=time.monotonic() - began,
                        allocation=ALLOCATION, package=str(PACKAGE))
    raw = canonical(response)
    require(len(raw) <= MAX_RESPONSE, "Bounded response exceeded its ceiling.")
    sys.stdout.buffer.write(raw + b"\n")
    return 0 if response["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
