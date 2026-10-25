"""CPU fixture, not a proof worker: sixteen real, sequential own-job queries.

Every subprocess argv is the exact scontrol form admitted by the candidate.
No surrogate executable, job mutation, model, native import or automatic retry.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time

QUERIES = 16
JOB_NAME = "hydra-p6-child-linux-probe-02"
ACCOUNT = "plgcredibleai2026-cpu"
QUERY_OUTPUT = 65536


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def ordinary(path, maximum):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Nonordinary fixture input.")
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "Fixture input exceeds its byte ceiling.")
    return raw


def save(path, record):
    raw = canonical(record) + b"\n"
    require(len(raw) <= 256 * 1024, "Fixture artifact exceeded its byte ceiling.")
    with path.open("xb") as stream:
        stream.write(raw)


def scheduler_identity(raw, job_id):
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    require(len(pairs) == len({key for key, _ in pairs}), "Ambiguous actual scheduler response.")
    fields = dict(pairs)
    expected = {"JobId": job_id, "JobName": JOB_NAME, "JobState": "RUNNING",
                "Account": ACCOUNT, "Partition": "plgrid", "NumCPUs": "1", "NumNodes": "1",
                "NumTasks": "1", "TimeLimit": "00:01:00", "Requeue": "0", "Restarts": "0"}
    require(all(fields.get(key) == value for key, value in expected.items())
            and re.fullmatch(r"[^()]+\(" + str(os.getuid()) + r"\)", fields.get("UserId", "")),
            "Query did not return this exact live CPU allocation.")
    for name in ("ReqTRES", "AllocTRES"):
        items = [item.split("=", 1) for item in fields.get(name, "").split(",")]
        require(all(len(item) == 2 for item in items) and len(items) == len({x[0] for x in items}),
                "Malformed CPU query resources.")
        values = dict(items)
        require(set(values) <= {"cpu", "mem", "node", "billing"}
                and values.get("cpu") == values.get("node") == "1"
                and values.get("mem") in {"1G", "1024M"}
                and ("billing" not in values or values["billing"] == "1"),
                "Query allocation is not one CPU/one GiB without GPU.")
    empty = (None, "", "(null)", "N/A", "None")
    require(all(fields.get(key) in empty for key in ("Gres", "TresPerNode", "TresPerJob"))
            and fields.get("TresPerTask") in empty + ("cpu=1", "cpu:1"), "Unexpected GRES in CPU query.")
    return {key: fields[key] for key in expected} | {
        "UserId": fields["UserId"], "ReqTRES": fields["ReqTRES"], "AllocTRES": fields["AllocTRES"]}


def waitable(process):
    require(process.returncode is None, "Scheduler PID was already reaped.")
    value = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    require(value is None or value.si_pid == process.pid, "Wrong direct-query wait identity.")
    return value is not None


def terminal_identity(process):
    raw = ordinary(Path("/proc") / str(process.pid) / "stat", 8192).decode()
    require(raw.startswith(str(process.pid) + " ("), "Query terminal PID changed.")
    tail = raw[raw.rfind(")") + 2:].split()
    require(len(tail) >= 22 and tail[0] == "Z" and tail[6].isdigit(), "Query is not a natural terminal process.")
    value = {"pid": process.pid, "state": tail[0], "ppid": int(tail[1]), "pgid": int(tail[2]),
             "sid": int(tail[3]), "flags": int(tail[6]), "start_ticks": int(tail[19])}
    require(value["ppid"] == value["pgid"] == value["sid"] == os.getpid(), "Query escaped its owned fixture.")
    return value


def one_query(index, executable, job_id, directory, global_deadline):
    began = time.monotonic()
    require(began + 3.05 < global_deadline, "No full query/cleanup reserve remains; no next launch.")
    active_deadline, cleanup_deadline = began + 2.5, began + 3.0
    argv = [executable, "-o", "show", "job", job_id]
    process, error, code, natural, forced = None, None, None, False, False
    terminal = None
    observations = 0
    raw = b""
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=output,
                                       stderr=subprocess.STDOUT)
            while True:
                require(observations < 251, "Fixed query wait-observation ceiling reached.")
                observations += 1
                if waitable(process):
                    natural = True
                    break
                require(time.monotonic() < active_deadline and time.monotonic() < global_deadline,
                        "Query active wall ceiling reached; no retry.")
                require(os.fstat(output.fileno()).st_size <= QUERY_OUTPUT, "Query output ceiling reached.")
                time.sleep(min(0.01, max(0.0, active_deadline - time.monotonic())))
            # This is an already-dead, still-owned direct child. Holding its
            # zombie briefly gives the independent candidate sampler a chance
            # to observe it; this is not a claim of observing the pre-Z gap.
            require(time.monotonic() + 0.15 < active_deadline, "No bounded terminal observation reserve remains.")
            terminal = terminal_identity(process)
            time.sleep(0.15)
            require(waitable(process), "Natural query exit ceased to be waitable.")
        except BaseException as failure:
            error = {"type": type(failure).__name__, "detail": str(failure)[:500]}
        finally:
            if process is not None and process.returncode is None:
                try:
                    if not waitable(process):
                        # The unreaped Popen reserves this PID. Never signal a
                        # recycled PID or use a poll-reaping kill convenience.
                        os.kill(process.pid, signal.SIGKILL)
                        forced = True
                    code = process.wait(timeout=max(0.0, cleanup_deadline - time.monotonic()))
                except BaseException as failure:
                    error = error or {"type": type(failure).__name__, "detail": str(failure)[:500]}
            output.seek(0)
            raw = output.read(QUERY_OUTPUT + 1)
    actual_identity = None
    try:
        require(len(raw) <= QUERY_OUTPUT and error is None and code == 0 and natural and not forced,
                "Scheduler query failed or cleanup is unconfirmed.")
        actual_identity = scheduler_identity(raw.decode("utf-8"), job_id)
    except BaseException as failure:
        error = error or {"type": type(failure).__name__, "detail": str(failure)[:500]}
    elapsed = time.monotonic() - began
    passed = error is None and elapsed <= 3.0 and terminal is not None
    record = {"schema": "hydra-child-linux-query-v1", "index": index, "passed": passed,
              "pid": None if process is None else process.pid, "requested_argv": argv,
              "actual_launches": int(process is not None), "actual_exit_code": code,
              "natural_exit_observed": natural, "forced_signal": forced,
              "reaped": process is not None and process.returncode is not None,
              "terminal_identity": terminal, "scheduler_identity": actual_identity,
              "stdout_stderr": raw.decode("utf-8", "replace"),
              "stdout_stderr_bytes": len(raw), "stdout_stderr_sha256": hashlib.sha256(raw).hexdigest(),
              "wait_observations": observations, "elapsed_seconds": elapsed,
              "active_wall_seconds": 2.5, "total_wall_seconds": 3.0, "cpu_hard_seconds": 1,
              "error": error, "automatic_retry": False}
    save(directory / ("query-%02d.json" % index), record)
    require(passed, "Real scheduler query failed; preserve evidence and stop remaining queries.")
    return record


def run(args):
    began = time.monotonic()
    # Inherit these strict limits through the same Popen kwargs as production.
    # No Python callback executes in the query child before its real exec.
    resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (QUERY_OUTPUT, QUERY_OUTPUT))
    def interrupted(signum, frame):
        raise TimeoutError("CPU query fixture resource stop: " + str(signum))
    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, interrupted)
    signal.alarm(22)
    require(sys.platform == "linux" and os.getuid() == 105923 and len(os.sched_getaffinity(0)) == 1,
            "Fixture requires the owned one-CPU Linux allocation.")
    raw = ordinary(args.request, 4096)
    require(hashlib.sha256(raw).hexdigest() == args.request_sha256, "Exact fixture request changed.")
    request = json.loads(raw)
    require(set(request) == {"schema", "index", "parent_pid", "job_id", "work_deadline_monotonic"}
            and request["schema"] == "hydra-child-linux-fixture-v1" and request["index"] == 0
            and request["parent_pid"] == os.getppid() and request["job_id"] == os.environ.get("SLURM_JOB_ID")
            and os.environ.get("SLURM_JOB_NAME") == JOB_NAME
            and type(request["work_deadline_monotonic"]) is float
            and began < request["work_deadline_monotonic"] <= began + 24,
            "Fixture lacks its exact owned CPU request and deadline.")
    executable = shutil.which("scontrol")
    require(executable is not None and os.path.isabs(executable), "Real scontrol is unavailable.")
    deadline = min(began + 20, request["work_deadline_monotonic"] - 1)
    records = [one_query(i, executable, request["job_id"], args.request.parent, deadline) for i in range(QUERIES)]
    require(len({row["pid"] for row in records}) == QUERIES, "Scheduler PID reuse is not admitted.")
    ready = {"schema": "hydra-child-linux-fixture-ready-v1", "index": 0,
             "pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
             "actual_scheduler_launches": sum(row["actual_launches"] for row in records),
             "successful_queries": len(records), "all_query_children_reaped": all(row["reaped"] for row in records),
             "query_pids": [row["pid"] for row in records], "elapsed_seconds": time.monotonic() - began,
             "affinity_cpus": sorted(os.sched_getaffinity(0)), "model_calls": 0, "native_calls": 0,
             "synthetic_executable_surrogates": 0, "automatic_retry": False}
    os.write(sys.stdout.fileno(), canonical(ready) + b"\n")
    os._exit(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    try:
        run(args)
    except BaseException as error:
        raw = canonical({"schema": "hydra-child-linux-fixture-failure-v1",
                         "type": type(error).__name__, "detail": str(error)[:500]}) + b"\n"
        os.write(sys.stderr.fileno(), raw)
        os._exit(2)


if __name__ == "__main__":
    main()
