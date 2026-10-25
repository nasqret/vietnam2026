"""One-use, CPU-only real-process probe of an exactly pinned paired monitor.

Preparation is not execution authority. Root must first admit the real CPU
allocation and this exact package. No study, theorem, model or solver is loaded.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import stat
import sys
import time

HERE = Path(__file__).resolve().parent
FILES = {"run_probe.py", "paired_case_worker.py", "paired_controller.py", "paired_common.py", "job.sh"}
COMMON_SHA = "d8f5dda5bfc1fb9e6769e4dc2f65591c2fb788db909842862e4009d80583d822"
JOB_NAME = "hydra-p6-linux-monitor-probe-01"
LIMITS = {"cpus": 1, "gpus": 0, "job_memory_bytes": 1024**3,
          "parent_address_space_bytes": 256 * 1024**2,
          "child_address_space_bytes": 256 * 1024**2,
          "parent_cpu_soft_seconds": 3, "parent_cpu_hard_seconds": 4,
          "child_cpu_hard_seconds": 3, "maximum_children": 2,
          "maximum_simultaneous_children": 1, "aggregate_cpu_hard_seconds": 10,
          "inner_wall_seconds": 30, "parent_alarm_seconds": 27,
          "work_deadline_seconds": 24, "child_alarm_seconds": 5,
          "scheduler_seconds": 60, "file_bytes": 128 * 1024,
          "total_result_bytes": 512 * 1024}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def ordinary(path, maximum=128 * 1024):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Expected an ordinary bounded file.")
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "Probe file bound exceeded.")
    return raw


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= LIMITS["file_bytes"], "Probe output file bound exceeded.")
    with path.open("xb") as stream:
        stream.write(raw)


def source_admission(expected_sha):
    raw = ordinary(HERE / "manifest.json")
    require(hashlib.sha256(raw).hexdigest() == expected_sha, "The selected probe manifest changed.")
    manifest = json.loads(raw)
    require(manifest.get("schema") == "hydra-linux-monitor-probe-package-v1"
            and set(manifest["files"]) == FILES and manifest["limits"] == LIMITS,
            "Unreviewed source scope or probe limits.")
    for name in sorted(FILES):
        data = ordinary(HERE / name)
        require(manifest["files"][name] == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()},
                "Pinned probe source changed: " + name)
    require(manifest["files"]["paired_common.py"]["sha256"] == COMMON_SHA,
            "The frozen common limits/helper file changed.")
    return manifest


def observed_gap(execution):
    resolution = execution.get("terminal_resolution")
    if resolution is None:
        return False
    for sample in resolution["samples"]:
        leader = sample["leader"]
        after = leader.get("stats", {}).get("after", {})
        if (leader.get("schema") != "hydra-paired-leader-accounting-v1"
                or after.get("state") == "Z" or not (int(after.get("flags", "0")) & 4)
                or leader.get("exit_observations", [])[:1] != [False]):
            continue
        if any(item.get("state") != "Z" and item.get("rss_fields") == 0
               and item.get("valid_rss_fields") == 0 and item.get("uid_matches") is True
               for item in leader.get("records", [])):
            return True
    return False


def run(args):
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024, 128 * 1024))
    require(sys.platform == "linux", "This unexecuted probe is for a real Linux CPU allocation only.")
    require(args.job_id.isdigit() and 1 <= len(args.job_id) <= 20
            and os.environ.get("SLURM_JOB_ID") == args.job_id
            and os.environ.get("SLURM_JOB_NAME") == JOB_NAME
            and os.environ.get("SLURM_CPUS_PER_TASK") == "1"
            and os.environ.get("SLURM_NTASKS") == "1"
            and os.environ.get("SLURM_MEM_PER_NODE") == "1024"
            and not os.environ.get("SLURM_JOB_GPUS") and not os.environ.get("SLURM_STEP_GPUS"),
            "Wrong CPU job envelope; genuine scheduler admission is also required externally.")
    cpus = sorted(os.sched_getaffinity(0))
    require(cpus, "The allocated CPU set is unavailable.")
    os.sched_setaffinity(0, {cpus[0]})
    def interrupted(signum, frame):
        raise TimeoutError("Probe resource stop: signal " + str(signum))
    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
        signal.signal(signum, interrupted)
    signal.alarm(LIMITS["parent_alarm_seconds"])
    manifest = source_admission(args.manifest_sha256)
    output = HERE / "run-01"
    output.mkdir(exist_ok=False)
    records, error = [], None
    save(output / "request.json", {"schema": "hydra-linux-monitor-probe-request-v1",
         "job_id": args.job_id, "manifest_sha256": args.manifest_sha256,
         "uid": os.getuid(), "pid": os.getpid(), "kernel_release": os.uname().release,
         "affinity_cpus": sorted(os.sched_getaffinity(0)), "limits": LIMITS,
         "allocation_admission": "Actual scheduler record must be checked by the root executor; environment checks alone are not admission.",
         "automatic_retry": False, "model_calls": 0, "native_calls": 0})
    try:
        # Only pinned stdlib-only definitions are imported. No run()/main(),
        # native_identity(), selected_cases() or scheduler helper is invoked.
        require("paired_common" not in sys.modules, "Unexpected pre-imported monitor dependency.")
        sys.path.insert(0, str(HERE))
        spec = importlib.util.spec_from_file_location("hydra_linux_probe_monitor", HERE / "paired_controller.py")
        monitor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(monitor)
        require(Path(sys.modules["paired_common"].__file__).resolve() == HERE / "paired_common.py"
                and monitor.HERE == HERE and monitor.RESOURCE_LIMITS["cleanup_seconds"] == 3
                and monitor.RESOURCE_LIMITS["sample_seconds"] == 0.05,
                "The selected monitor API or bounds changed.")
        for index in (0, 1):
            require(time.monotonic() - began < 16, "No complete child/cleanup reserve remains; no second launch.")
            directory = output / ("case-%02d" % index)
            directory.mkdir()
            request = {"schema": "hydra-linux-monitor-fixture-v1", "index": index,
                       "parent_pid": os.getpid(), "job_id": args.job_id}
            request_path = directory / "case-request.json"
            save(request_path, request)
            request_sha = hashlib.sha256(ordinary(request_path)).hexdigest()
            execution = monitor.supervise_case(HERE / "unused-app", request_path, request_sha,
                {"job_id": args.job_id}, "fixed-wall-30-v1",
                should_stop=lambda: time.monotonic() - began >= LIMITS["work_deadline_seconds"])
            require(json.loads(ordinary(directory / "execution.json")) == execution,
                    "The exact supervisor execution record was not saved unchanged.")
            ready = None
            try:
                ready = json.loads(ordinary(directory / "stdout", 2048))
            except (OSError, ValueError):
                pass
            expected_maps, expected_bytes = ((1, 8 * 1024**2), (8192, 128 * 1024**2))[index]
            passed = (execution.get("exit_code") == 0 and execution.get("leader_reaped") is True
                      and execution.get("quiescent") is True and execution.get("termination_reason") == "process_exit"
                      and type(execution.get("rss_samples")) is int and execution["rss_samples"] >= 1
                      and execution.get("peak_sampled_host_rss_bytes", 0) >= expected_bytes
                      and type(ready) is dict and ready.get("schema") == "hydra-linux-monitor-fixture-ready-v1"
                      and ready.get("index") == index and ready.get("pid") == execution.get("pid")
                      and ready.get("ppid") == os.getpid() and ready.get("uid") == os.getuid()
                      and ready.get("requested_mappings") == expected_maps
                      and ready.get("requested_bytes") == expected_bytes
                      and type(ready.get("observed_vma_lines")) is int
                      and ready["observed_vma_lines"] >= expected_maps)
            records.append({"index": index, "passed": passed, "ready": ready,
                            "execution": execution,
                            "terminal_resolution_observed": execution.get("terminal_resolution") is not None,
                            "pre_z_missing_rss_observed": observed_gap(execution)})
            require(passed, "A real fixed fixture or its owned cleanup failed; no retry or further fixture.")
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:800]}
    finally:
        try:
            unchanged = source_admission(args.manifest_sha256) == manifest
        except BaseException as failure:
            unchanged = False
            error = error or {"type": type(failure).__name__, "detail": str(failure)[:800]}
        own, children = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = own.ru_utime + own.ru_stime + children.ru_utime + children.ru_stime
        elapsed = time.monotonic() - began
        passed = error is None and unchanged and len(records) == 2 and all(x["passed"] for x in records)
        passed = passed and cpu <= 10 and elapsed <= 30
        result = {"schema": "hydra-linux-monitor-probe-result-v1", "passed": passed,
                  "error": error, "job_id": args.job_id, "elapsed_seconds": elapsed,
                  "aggregate_cpu_seconds": cpu, "sources_unchanged": unchanged,
                  "manifest_sha256": args.manifest_sha256, "limits": LIMITS, "fixtures": records,
                  "controller_sha256": manifest["files"]["paired_controller.py"]["sha256"],
                  "common_sha256": COMMON_SHA,
                  "probe_sha256": manifest["files"]["run_probe.py"]["sha256"],
                  "actual_fixture_launches": sum(x["execution"].get("helper_launches", 0) for x in records),
                  "all_owned_leaders_reaped": bool(records) and all(x["execution"].get("leader_reaped") is True for x in records),
                  "all_groups_quiescent": bool(records) and all(x["execution"].get("quiescent") is True for x in records),
                  "terminal_resolutions_observed": sum(x["terminal_resolution_observed"] for x in records),
                  "pre_z_missing_rss_observed": any(x["pre_z_missing_rss_observed"] for x in records),
                  "reproduction_interpretation": "A true pre_z_missing_rss_observed requires same-frame non-Z status without RSS, PF_EXITING in non-Z stat, and a false non-reaping exit observation. Otherwise the interval is unobserved, even if both fixtures pass.",
                  "model_calls": 0, "native_calls": 0, "scheduler_queries_by_probe": 0,
                  "automatic_retry": False, "full_pairing_or_proof_checked": False}
        save(output / "result.json", result)
        total = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
        require(total <= LIMITS["total_result_bytes"], "Total probe evidence bound exceeded.")
        signal.alarm(0)
        print(json.dumps({"passed": passed, "elapsed_seconds": elapsed,
                          "pre_z_missing_rss_observed": result["pre_z_missing_rss_observed"]}), flush=True)
    return 0 if passed else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest-sha256", required=True)
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except BaseException as error:
        print(json.dumps({"passed": False, "type": type(error).__name__, "detail": str(error)[:800]}), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
