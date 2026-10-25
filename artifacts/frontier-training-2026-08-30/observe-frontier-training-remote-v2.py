"""Python 3.6 read-only exact-job observer; no writes or scheduler mutations.

Invoked only by the archive client with the job from a pinned launch receipt.
The only child commands are squeue, sacct and scontrol show for that one job.
V2 changes only proven host compatibility: O_PATH ancestor traversal and the
320MiB address-space limit; RSS was not the cause of the original host failure.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import selectors
import signal
import stat
import subprocess
import sys
import time

ROOT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/frontier-training-v1"
PROFILE = "peano-hydra-frontier-training-v1"
RUN_ID = "frontier-training-v1"
PACKAGE = "_deploy/hydra-frontier-training-v1"
LEDGER = "logs/hydra-frontier-training-v1.jsonl"
ADAPTER = "results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1"
JOB_NAME = PROFILE + "-train"
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
JOB = re.compile(r"[1-9][0-9]{0,19}\Z")
HEX = re.compile(r"[0-9a-f]{64}\Z")
MAX_JSON = 4 * 1024**2


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def decode(raw):
    require(0 < len(raw) <= MAX_JSON, "JSON bound")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite JSON number")
    def integer(value):
        require(len(value) <= 32, "oversized JSON number")
        return int(value)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid, parse_int=integer)
    require(type(value) is dict, "JSON object required")
    return value


def directory(path):
    path = Path(path).absolute()
    require(".." not in path.parts and 1 < len(path.parts) <= 64
            and len(str(path).encode()) <= 4096, "unsafe directory")
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)



def read(name, maximum, tail=False, optional=False):
    require(re.fullmatch(r"[A-Za-z0-9_.\-/]{1,1024}", name) and
            all(part not in ("", ".", "..") for part in name.split("/")), "unsafe observation path")
    parent = None
    fd = None
    try:
        parent_path, leaf = (ROOT + "/" + name).rsplit("/", 1)
        parent = directory(parent_path)
        fd = os.open(leaf, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, "observation target is not a single-link regular file")
        require(tail or before.st_size <= maximum, "observation metadata byte bound")
        offset = max(0, before.st_size - maximum) if tail else 0
        os.lseek(fd, offset, os.SEEK_SET)
        raw = bytearray()
        while len(raw) < maximum:
            block = os.read(fd, min(65536, maximum - len(raw)))
            if not block:
                break
            raw.extend(block)
        after = os.fstat(fd)
        named = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino) == (named.st_dev, named.st_ino), "observation path replaced")
        if not tail:
            require(before.st_size == len(raw) == after.st_size and before.st_mtime_ns == after.st_mtime_ns,
                    "metadata changed while reading")
        return bytes(raw), {"path": name, "exists": True, "file_bytes_at_open": before.st_size,
                            "file_bytes_after_read": after.st_size, "bytes_read": len(raw),
                            "start_offset": offset, "tail": tail, "captured_sha256": sha(raw)}
    except FileNotFoundError:
        if not optional:
            raise
        return None, {"path": name, "exists": False}
    finally:
        if fd is not None:
            os.close(fd)
        if parent is not None:
            os.close(parent)


def metadata_stat(name):
    parent = None
    try:
        path, leaf = (ROOT + "/" + name).rsplit("/", 1)
        parent = directory(path)
        info = os.stat(leaf, dir_fd=parent, follow_symlinks=False)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "artifact is a link or special file")
        return {"path": name, "exists": True, "bytes": info.st_size, "content_downloaded": False}
    except FileNotFoundError:
        return {"path": name, "exists": False, "content_downloaded": False}
    finally:
        if parent is not None:
            os.close(parent)


def bound_job(job, approval_sha):
    approval_raw, _ = read(PACKAGE + "/approval.json", MAX_JSON)
    require(sha(approval_raw) == approval_sha, "remote raw approval differs")
    approval = decode(approval_raw)
    require(approval.get("schema") == "peano-hydra-frontier-training-resource-approval-v1"
            and approval.get("profile") == PROFILE and approval.get("run_id") == RUN_ID
            and approval.get("approved") is True, "foreign/unapproved job profile")
    request_raw, _ = read(PACKAGE + "/resource-request.json", MAX_JSON)
    require(sha(request_raw) == approval["request_file_sha256"], "approved request bytes differ")
    request = decode(request_raw)
    require(request.get("profile") == PROFILE and request.get("run_id") == RUN_ID
            and request.get("maximum_aggregate_gpu_seconds") == 7200, "approved scope differs")
    raw, _ = read(LEDGER, 256 * 1024)
    lines = raw.splitlines(keepends=True)
    require(raw.endswith(b"\n") and len(lines) == 6, "submitted receipt needs the complete one-job ledger")
    previous, events = "0" * 64, []
    kinds = ("header", "reserve", "train-accepted", "held-validated", "release-authorized", "train-released")
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == sha(canonical({k: event[k] for k in ("index", "previous_sha256", "payload")}))
                and canonical(event) + b"\n" == line and event["payload"].get("kind") == kinds[index], "ledger chain differs")
        events.append(event["payload"])
        previous = event["sha256"]
    header, reserve, accepted, held, barrier, released = events
    identity = header["identity"]
    require(header.get("schema") == "peano-hydra-frontier-training-held-job-ledger-v1"
            and header.get("profile") == PROFILE and header.get("run_id") == RUN_ID
            and identity.get("approval_sha256") == approval_sha
            and identity.get("request_file_sha256") == sha(request_raw)
            and identity.get("source_commit") == request.get("source_commit")
            and identity.get("source_files_sha256") == sha(canonical(request.get("source_files")))
            and identity.get("payloads_sha256") == request.get("payloads_sha256")
            and identity.get("job_script_sha256") == {"train": request["source_files"]["slurm/peano_hydra_frontier_training.sbatch"]["sha256"]},
            "ledger is for another approval/source")
    require(reserve.get("reservations") == {"train": {"seconds": 7200, "gpus": 1, "cpus": 8, "memory_gib": 64}}
            and accepted.get("job_id") == job and accepted.get("dependency_job_id") is None
            and barrier.get("jobs") == {"train": job} and released.get("job_id") == job, "receipt job differs from reserved/released job")
    require(set(held.get("snapshots", {})) == {"train"}, "held ledger contains another job")
    return {"approval_sha256": approval_sha, "request_sha256": sha(request_raw),
            "source_commit": request["source_commit"], "ledger_sha256": sha(raw), "ledger_events": 6,
            "reserved_gpu_seconds": 7200, "job_id": job}


def command(args):
    started = time.monotonic()
    child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                             stdin=subprocess.DEVNULL, start_new_session=True)
    streams = {"stdout": bytearray(), "stderr": bytearray()}
    selector, reason = selectors.DefaultSelector(), "exited"
    try:
        for label in streams:
            stream = getattr(child, label)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, label)
        while selector.get_map():
            require(time.monotonic() - started < 10, "scheduler-read deadline")
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 8192)
                if not block:
                    selector.unregister(key.fileobj)
                else:
                    streams[key.data].extend(block)
                    require(len(streams[key.data]) <= 65536, "scheduler-read output bound")
        child.wait(timeout=max(0.01, 10 - (time.monotonic() - started)))
    except BaseException as error:
        reason = type(error).__name__ + ": " + str(error)
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
    finally:
        selector.close()
        child.stdout.close()
        child.stderr.close()
    return {"command": args, "returncode": child.returncode, "reason": reason,
            "wall_seconds": round(time.monotonic() - started, 6),
            **{key: value.decode("utf-8", "replace") for key, value in streams.items()}}


def scheduler_identity(observations, job):
    expected = {"JobId": job, "JobName": JOB_NAME, "WorkDir": ROOT, "Account": ACCOUNT,
                "Partition": PARTITION, "TimeLimit": "02:00:00", "NumCPUs": "8"}
    control = observations["controller"]
    observed, issues = {}, []
    if control["returncode"] == 0 and control["reason"] == "exited":
        values = dict(re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9_]*)=([^\s]*)", control["stdout"]))
        for key, value in expected.items():
            observed[key] = values.get(key)
            if observed[key] != value:
                issues.append(key + " differs")
    account = observations["accounting"]
    rows = []
    if account["returncode"] == 0 and account["reason"] == "exited":
        for line in account["stdout"].splitlines():
            if not line.strip():
                continue
            parts = line.strip().split("|")
            require(len(parts) == 16 and len(rows) < 8, "bounded exact accounting columns/rows required")
            require(parts[0] in (job, job + ".batch", job + ".extern"), "accounting returned an unrelated job")
            rows.append(parts)
            if parts[0] == job:
                for index, value in ((1, JOB_NAME), (5, "120"), (10, ROOT), (11, ACCOUNT), (12, PARTITION), (15, "plgnasqret")):
                    if parts[index] != value:
                        issues.append("accounting column " + str(index) + " differs")
    return {"expected": expected, "observed_controller_fields": observed,
            "integrity_issues": issues, "accounting_rows": rows,
            "controller_unavailable_is_unknown": control["returncode"] != 0}


def manifest_summary(job):
    raw, info = read(ADAPTER + "/manifest.json", MAX_JSON, optional=True)
    if raw is None:
        return info
    value = decode(raw)
    require(value.get("run_id") == RUN_ID and value.get("job", {}).get("job_id") == job,
            "saved manifest belongs to another run/job")
    metrics = value.get("metrics", {})
    require(type(metrics) is dict and len(canonical(metrics)) <= 16384, "manifest metrics summary bound")
    return {**info, "run_id": value["run_id"], "job_id": job, "model_trained": value.get("model_trained"),
            "research_claim_eligible": value.get("research_claim_eligible"), "metrics": metrics,
            "interpretation": "saved metadata and diagnostic DEV loss; not independent model verification or benchmark evaluation"}


def main():
    require(sys.flags.isolated and sys.dont_write_bytecode and len(sys.argv) == 3, "isolated observer arguments required")
    job, approval_sha = sys.argv[1:]
    require(JOB.fullmatch(job) and HEX.fullmatch(approval_sha), "exact external job/approval identities")
    resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
    resource.setrlimit(resource.RLIMIT_AS, (320 * 1024**2, 320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    def expired(signum, frame):
        raise TimeoutError("observer 50-second wall deadline")
    signal.signal(signal.SIGALRM, expired)
    signal.alarm(50)
    result = {"schema": "peano-hydra-frontier-training-observation-v1", "read_only": True,
              "observed_at_utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
              "root": ROOT, "job_id": job, "model_weights_downloaded": False,
              "job_submission_performed": False, "automatic_retry": False}
    code = 2
    try:
        result["binding"] = bound_job(job, approval_sha)
        result["scheduler"] = {
            "queue": command(["squeue", "--noheader", "--jobs=" + job,
                              "--format=%i|%j|%T|%P|%M|%l|%R|%Z|%a|%C|%m|%D|%b|%u"]),
            "accounting": command(["sacct", "--noheader", "--parsable2", "--jobs=" + job,
                                  "--starttime=2026-08-30", "--format=JobIDRaw,JobName%80,State,ExitCode,Elapsed,TimelimitRaw,AllocCPUS,ReqMem,MaxRSS,NodeList,WorkDir%4096,Account,Partition,AllocTRES%160,TotalCPU,User"]),
            "controller": command(["scontrol", "-o", "show", "job", job]),
        }
        result["scheduler_identity"] = scheduler_identity(result["scheduler"], job)
        require(not result["scheduler_identity"]["integrity_issues"], "controller/accounting job identity differs; no logs read")
        result["logs"] = {}
        for suffix in ("out", "err"):
            name = "logs/" + JOB_NAME + "-" + job + "." + suffix
            raw, info = read(name, 65536, tail=True, optional=True)
            result["logs"][suffix] = {**info, "text": None if raw is None else raw.decode("utf-8", "replace")}
        result["manifest"] = manifest_summary(job)
        result["artifact_existence"] = [metadata_stat(ADAPTER + "/" + name) for name in
                                        ("adapter/adapter_model.safetensors", "trainer_state.json", "train_results.json", "eval_results.json")]
        result["status"] = "observed"
        code = 0
    except BaseException as error:
        result.update(status="observation-failed-unknown", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        signal.alarm(0)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
    raise SystemExit(code)
