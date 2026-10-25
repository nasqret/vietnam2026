"""Fixed stdlib-only fixture for the separate Linux monitor probe.

This file is not the proof worker. It never imports project/native/model code.
The probe intentionally uses the supervisor's unchanged worker basename/argv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import mmap
import os
from pathlib import Path
import resource
import signal
import sys
import time


def require(condition, message):
    if not condition:
        raise ValueError(message)


def run(args):
    resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024, 128 * 1024))
    signal.signal(signal.SIGALRM, signal.SIG_DFL)
    signal.alarm(5)
    require(sys.platform == "linux" and len(os.sched_getaffinity(0)) == 1,
            "The fixture requires one Linux CPU inherited from its probe parent.")
    raw = args.request.read_bytes()
    require(len(raw) <= 4096 and hashlib.sha256(raw).hexdigest() == args.request_sha256,
            "Fixed fixture request changed.")
    request = json.loads(raw)
    require(set(request) == {"schema", "index", "parent_pid", "job_id"}
            and request["schema"] == "hydra-linux-monitor-fixture-v1"
            and type(request["index"]) is int and request["index"] in (0, 1)
            and request["parent_pid"] == os.getppid()
            and request["job_id"] == os.environ.get("SLURM_JOB_ID"),
            "This is not an owned fixed probe fixture.")
    count, size = ((1, 8 * 1024**2), (8192, 16 * 1024))[request["index"]]
    pagesize = os.sysconf("SC_PAGE_SIZE")
    require(pagesize == 4096, "This fixed x86 Linux CPU probe requires 4-KiB pages.")
    mappings = []
    for _ in range(count):
        mapping = mmap.mmap(-1, size, flags=mmap.MAP_SHARED | mmap.MAP_ANONYMOUS,
                            prot=mmap.PROT_READ | mmap.PROT_WRITE)
        for offset in range(0, size, pagesize):
            mapping[offset] = 1
        mappings.append(mapping)
    with Path("/proc/self/maps").open("rb") as stream:
        maps = stream.read(2 * 1024**2 + 1)
    require(len(maps) <= 2 * 1024**2, "Unexpected process mapping inventory.")
    record = {"schema": "hydra-linux-monitor-fixture-ready-v1", "index": request["index"],
              "pid": os.getpid(), "ppid": os.getppid(), "uid": os.getuid(),
              "requested_mappings": count, "requested_bytes": count * size,
              "observed_vma_lines": len(maps.splitlines()), "page_size": pagesize,
              "affinity_cpus": sorted(os.sched_getaffinity(0)),
              "ready_monotonic": time.monotonic(), "intended_exit_code": 0,
              "exit_method": "os._exit; mappings stay live for kernel teardown",
              "model_calls": 0, "native_calls": 0, "forks": 0}
    payload = (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode()
    require(len(payload) <= 2048, "Fixture output bound exceeded.")
    os.write(sys.stdout.fileno(), payload)
    time.sleep(0.3)
    # No Python mmap destructors: the exiting Linux process releases its mm.
    os._exit(0)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", type=Path, required=True)
    parser.add_argument("--request-sha256", required=True)
    args = parser.parse_args()
    try:
        run(args)
    except BaseException as error:
        payload = json.dumps({"schema": "hydra-linux-monitor-fixture-failure-v1",
                              "type": type(error).__name__, "detail": str(error)[:400]}).encode() + b"\n"
        os.write(sys.stderr.fileno(), payload)
        os._exit(2)


if __name__ == "__main__":
    main()
