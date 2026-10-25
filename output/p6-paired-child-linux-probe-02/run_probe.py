"""One-use Linux CPU prerequisite for the exact local child-monitor candidate.

The root executor owns genuine scheduler admission and all remote phases.
This package exercises only stdlib process monitoring and sixteen read-only
scontrol queries of its own CPU job. It loads no theorem, native code or model.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import time

HERE = Path(__file__).resolve().parent
FILES = {"run_probe.py", "paired_case_worker.py", "paired_controller.py", "paired_common.py", "job.sh"}
CONTROLLER_SHA = "cb5ba7840f85c00bf54953bddf5bb168414a0e6e84c9b41369da63b315e195be"
COMMON_SHA = "d8f5dda5bfc1fb9e6769e4dc2f65591c2fb788db909842862e4009d80583d822"
JOB_NAME = "hydra-p6-child-linux-probe-02"
LIMITS = {"cpus": 1, "gpus": 0, "job_memory_bytes": 1024**3, "scheduler_seconds": 60,
          "parent_address_space_bytes": 256 * 1024**2, "fixture_address_space_bytes": 256 * 1024**2,
          "query_address_space_bytes": 256 * 1024**2, "parent_cpu_soft_seconds": 3,
          "parent_cpu_hard_seconds": 4, "fixture_cpu_hard_seconds": 1, "query_cpu_hard_seconds": 1,
          "nominal_aggregate_cpu_hard_seconds": 21, "aggregate_cpu_seconds": 24,
          "maximum_fixture_leaders": 1, "maximum_scheduler_children": 16,
          "maximum_simultaneous_scheduler_children": 1, "maximum_simultaneous_processes": 3,
          "inner_wall_seconds": 30, "parent_alarm_seconds": 27, "work_deadline_seconds": 24,
          "fixture_work_seconds": 20, "fixture_alarm_seconds": 22,
          "query_active_wall_seconds": 2.5, "query_total_wall_seconds": 3.0,
          "query_terminal_hold_seconds": 0.15, "query_output_bytes": 65536,
          "maximum_sampler_calls": 512, "maximum_retained_traces": 64,
          "file_bytes": 256 * 1024, "total_result_bytes": 2 * 1024**2}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def ordinary(path, maximum=256 * 1024):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "Expected an ordinary bounded probe file.")
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
    require(hashlib.sha256(raw).hexdigest() == expected_sha, "Selected probe manifest changed.")
    manifest = json.loads(raw)
    require(manifest.get("schema") == "hydra-child-linux-monitor-probe-package-v1"
            and set(manifest["files"]) == FILES and manifest["limits"] == LIMITS,
            "Unreviewed probe source scope or limits.")
    for name in sorted(FILES):
        data = ordinary(HERE / name)
        require(manifest["files"][name] == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()},
                "Pinned source changed: " + name)
    require(manifest["files"]["paired_controller.py"]["sha256"] == CONTROLLER_SHA
            and manifest["files"]["paired_common.py"]["sha256"] == COMMON_SHA, "Wrong monitor/common source.")
    return manifest


class SamplerObservation:
    """Transparent, bounded observation of inputs/results, never a decision.

    Arguments and returned values/raised exceptions are delegated unchanged.
    Captured metadata is from the same proc_read bytes used by the sampler;
    there is no extra /proc read, surrogate argv or manufactured exit evidence.
    """
    def __init__(self, monitor):
        self.monitor = monitor
        self.original_read = monitor.proc_read
        self.original_child = monitor.sample_scheduler_child
        self.active = None
        self.calls = 0
        self.pids = set()
        self.accepted_pids = set()
        self.first_kept, self.terminal_kept = set(), set()
        self.pending_kept = 0
        self.traces = []
        self.observation_errors = 0
        self.limit_exceeded = False

    def install(self):
        self.monitor.proc_read = self.read
        self.monitor.sample_scheduler_child = self.child

    def restore(self):
        self.monitor.proc_read = self.original_read
        self.monitor.sample_scheduler_child = self.original_child

    def compact(self, path, raw):
        value = {"kind": path.name, "bytes": len(raw)}
        if path.name == "stat":
            parsed = self.monitor.parse_proc_stat(raw.decode(), self.active["pid"])
            value.update({key: str(item)[:32] for key, item in parsed.items()})
        elif path.name == "status":
            text = raw.decode()
            states = re.findall(r"^State:[ \t]+([RSDZTtXxKWPI])(?:[ \t][^\r\n]*)?$", text, re.MULTILINE)
            uids = re.findall(r"^Uid:[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]*$", text, re.MULTILINE)
            rss = re.findall(r"^VmRSS:[ \t]+(\d+)[ \t]+kB[ \t]*$", text, re.MULTILINE)
            value.update(state=states[0] if len(states) == 1 else None, state_fields=len(states),
                         uid_fields=len(uids), uid_matches=len(uids) == 1 and all(int(x) == os.getuid() for x in uids[0]),
                         rss_fields=len(rss))
        elif path.name == "cmdline":
            value.update(argv_empty=raw == b"", argv_matches=raw.split(b"\0") == self.active["expected_argv"],
                         cmdline_sha256=hashlib.sha256(raw).hexdigest())
        elif path.name == "children":
            value["empty"] = not raw.strip()
        return value

    def read(self, path, maximum):
        raw = self.original_read(path, maximum)
        if self.active is not None and str(path).startswith("/proc/" + str(self.active["pid"]) + "/"):
            try:
                if len(self.active["reads"]) < 12:
                    self.active["reads"].append(self.compact(Path(path), raw))
                else:
                    self.limit_exceeded = True
            except Exception:
                self.observation_errors += 1
        return raw

    def child(self, *args, **kwargs):
        pid, leader, job_id, executable = args[:4]
        self.calls += 1
        self.pids.add(pid)
        if self.calls > LIMITS["maximum_sampler_calls"] or len(self.pids) > 16:
            self.limit_exceeded = True
        trace = {"pid": pid, "leader": leader, "reads": [],
                 "expected_argv": [os.fsencode(executable), b"-o", b"show", b"job", job_id.encode(), b""],
                 "candidate_argv_sha256": hashlib.sha256(canonical([executable, "-o", "show", "job", job_id])).hexdigest(),
                 "result_kind": None, "pending_exit": False}
        self.active = trace
        try:
            result = self.original_child(*args, **kwargs)
            trace["result_kind"] = "pending_or_terminal" if type(result) is dict else ("gone" if result is None else "measured")
            trace["rss_bytes"] = result.get("rss_bytes") if type(result) is dict else result
            if type(result) is dict:
                trace["pending_exit"] = result["pending_exit"]
                trace["terminal"] = result["terminal"]
            if result is not None:
                self.accepted_pids.add(pid)
            return result
        except BaseException as error:
            trace["result_kind"] = "raised"
            trace["error"] = {"type": type(error).__name__, "detail": str(error)[:256]}
            raise
        finally:
            self.active = None
            trace.pop("expected_argv")
            terminal = any(read.get("kind") == "stat" and read.get("state") == "Z" for read in trace["reads"])
            keep = pid not in self.first_kept or (terminal and pid not in self.terminal_kept)
            if trace["pending_exit"] and self.pending_kept < 32:
                self.pending_kept += 1
                keep = True
            if keep and len(self.traces) < LIMITS["maximum_retained_traces"]:
                if len(canonical(trace)) <= 4096:
                    self.traces.append(trace)
                    self.first_kept.add(pid)
                    if terminal:
                        self.terminal_kept.add(pid)
                else:
                    self.limit_exceeded = True


def query_identity_observed(query, traces, leader):
    terminal = query.get("terminal_identity") or {}
    expected = {"ppid": leader, "pgid": leader, "sid": leader, "start_ticks": terminal.get("start_ticks")}
    if (terminal.get("pid") != query.get("pid") or terminal.get("state") != "Z"
            or any(terminal.get(key) != value for key, value in expected.items())
            or type(terminal.get("flags")) is not int or not (terminal["flags"] & 4)):
        return False
    argv_sha = hashlib.sha256(canonical(query["requested_argv"])).hexdigest()
    for trace in traces:
        if (trace["pid"] != query["pid"] or trace["leader"] != leader
                or trace["candidate_argv_sha256"] != argv_sha
                or trace["result_kind"] not in {"measured", "pending_or_terminal"}):
            continue
        stats = [row for row in trace["reads"] if row["kind"] == "stat"]
        statuses = [row for row in trace["reads"] if row["kind"] == "status"]
        if (len(stats) >= 2 and statuses and all(row.get("uid_matches") is True for row in statuses)
                and all(all(row.get(key) == str(value) for key, value in expected.items()) for row in stats)):
            return True
    return False


def child_gap(execution):
    resolution = execution.get("child_terminal_resolution") or {}
    for episode in resolution.get("episodes", []):
        for frame in episode["samples"]:
            child = frame["child"]
            after = child.get("stats", {}).get("after", {})
            if after.get("state") == "Z" or not (int(after.get("flags", "0")) & 4):
                continue
            if any(row.get("state") != "Z" and row.get("rss_fields") == row.get("valid_rss_fields") == 0
                   and row.get("uid_matches") is True for row in child.get("records", [])):
                return True
    return False


def run(args):
    began = time.monotonic()
    resource.setrlimit(resource.RLIMIT_CPU, (3, 4))
    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (256 * 1024, 256 * 1024))
    require(sys.platform == "linux" and os.getuid() == 105923, "Owned Linux CPU prerequisite only.")
    require(re.fullmatch(r"[0-9]{1,20}", args.job_id) and os.environ.get("SLURM_JOB_ID") == args.job_id
            and os.environ.get("SLURM_JOB_NAME") == JOB_NAME and os.environ.get("SLURM_CPUS_PER_TASK") == "1"
            and os.environ.get("SLURM_NTASKS") == "1" and os.environ.get("SLURM_MEM_PER_NODE") == "1024"
            and not os.environ.get("SLURM_JOB_GPUS") and not os.environ.get("SLURM_STEP_GPUS"), "Wrong CPU envelope.")
    cpus = sorted(os.sched_getaffinity(0))
    require(cpus, "Allocated CPU set is unavailable.")
    os.sched_setaffinity(0, {cpus[0]})
    def interrupted(signum, frame):
        raise TimeoutError("CPU probe resource stop: " + str(signum))
    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT, signal.SIGXCPU):
        signal.signal(signum, interrupted)
    signal.alarm(LIMITS["parent_alarm_seconds"])
    manifest = source_admission(args.manifest_sha256)
    output = HERE / "run-01"
    output.mkdir(exist_ok=False)
    save(output / "request.json", {"schema": "hydra-child-linux-probe-request-v1", "job_id": args.job_id,
         "manifest_sha256": args.manifest_sha256, "pid": os.getpid(), "uid": os.getuid(),
         "kernel_release": os.uname().release, "affinity_cpus": sorted(os.sched_getaffinity(0)), "limits": LIMITS,
         "actual_scheduler_admission_required": True, "automatic_retry": False, "model_calls": 0, "native_calls": 0})
    execution = ready = observer = None
    queries, error, fixture_passed = [], None, False
    try:
        require("paired_common" not in sys.modules, "Unexpected pre-imported monitor dependency.")
        sys.path.insert(0, str(HERE))
        spec = importlib.util.spec_from_file_location("hydra_child_linux_probe_monitor", HERE / "paired_controller.py")
        monitor = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(monitor)
        require(Path(sys.modules["paired_common"].__file__).resolve() == HERE / "paired_common.py"
                and monitor.HERE == HERE and monitor.RESOURCE_LIMITS["cleanup_seconds"] == 3
                and monitor.RESOURCE_LIMITS["sample_seconds"] == 0.05, "Wrong imported monitor API or bounds.")
        observer = SamplerObservation(monitor)
        observer.install()
        require(time.monotonic() - began < 3, "No full fixture/global cleanup reserve remains; no launch.")
        directory = output / "case-00"
        directory.mkdir()
        request_path = directory / "case-request.json"
        save(request_path, {"schema": "hydra-child-linux-fixture-v1", "index": 0,
             "parent_pid": os.getpid(), "job_id": args.job_id,
             "work_deadline_monotonic": began + LIMITS["work_deadline_seconds"]})
        request_sha = hashlib.sha256(ordinary(request_path)).hexdigest()
        execution = monitor.supervise_case(HERE / "unused-app", request_path, request_sha,
            {"job_id": args.job_id}, "fixed-wall-30-v1",
            should_stop=lambda: time.monotonic() - began >= LIMITS["work_deadline_seconds"] or observer.limit_exceeded)
        require(json.loads(ordinary(directory / "execution.json")) == execution, "Saved execution differs from returned monitor record.")
        for index in range(16):
            path = directory / ("query-%02d.json" % index)
            if not path.exists():
                continue
            raw = ordinary(path)
            record = json.loads(raw)
            require(record.get("schema") == "hydra-child-linux-query-v1" and record.get("index") == index,
                    "Query evidence index/schema changed.")
            record.pop("stdout_stderr", None)  # Raw text remains in its separately collected exact file.
            queries.append({**record, "file": {"name": path.name, "bytes": len(raw),
                             "sha256": hashlib.sha256(raw).hexdigest()}})
        try:
            ready = json.loads(ordinary(directory / "stdout", 4096))
        except (OSError, ValueError):
            pass
        query_pids = {row["pid"] for row in queries}
        queries_passed = len(queries) == len(query_pids) == 16 and all(
            row.get("passed") is True and row.get("actual_launches") == 1 and row.get("actual_exit_code") == 0
            and row.get("reaped") is True and row.get("natural_exit_observed") is True
            and row.get("forced_signal") is False and row.get("error") is None
            and row["terminal_identity"]["pid"] == row["pid"]
            and row["terminal_identity"]["ppid"] == execution["pid"]
            and row["scheduler_identity"]["JobId"] == args.job_id
            and query_identity_observed(row, observer.traces, execution["pid"]) for row in queries)
        fixture_passed = (execution.get("exit_code") == 0 and execution.get("leader_reaped") is True
            and execution.get("quiescent") is True and execution.get("termination_reason") == "process_exit"
            and execution.get("rss_samples", 0) >= 1 and queries_passed
            and type(ready) is dict and ready.get("schema") == "hydra-child-linux-fixture-ready-v1"
            and ready.get("pid") == execution["pid"] and ready.get("ppid") == os.getpid()
            and ready.get("uid") == os.getuid() and ready.get("successful_queries") == 16
            and ready.get("actual_scheduler_launches") == 16 and ready.get("all_query_children_reaped") is True
            and set(ready.get("query_pids", [])) == query_pids
            and observer.pids == observer.accepted_pids == query_pids
            and not observer.limit_exceeded and observer.observation_errors == 0)
        require(fixture_passed, "Real query lifecycle/sampler prerequisite did not complete; no retry.")
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:800]}
    finally:
        if observer is not None:
            observer.restore()
        try:
            unchanged = source_admission(args.manifest_sha256) == manifest
        except BaseException as failure:
            unchanged = False
            error = error or {"type": type(failure).__name__, "detail": str(failure)[:800]}
        own, descendants = resource.getrusage(resource.RUSAGE_SELF), resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu = own.ru_utime + own.ru_stime + descendants.ru_utime + descendants.ru_stime
        elapsed = time.monotonic() - began
        passed = error is None and unchanged and fixture_passed and cpu <= 24 and elapsed <= 30
        query_pids = {row["pid"] for row in queries}
        result = {"schema": "hydra-child-linux-monitor-probe-result-v1", "passed": passed, "error": error,
            "job_id": args.job_id, "elapsed_seconds": elapsed, "aggregate_cpu_seconds": cpu,
            "sources_unchanged": unchanged, "manifest_sha256": args.manifest_sha256, "limits": LIMITS,
            "controller_sha256": CONTROLLER_SHA, "common_sha256": COMMON_SHA,
            "probe_sha256": manifest["files"]["run_probe.py"]["sha256"],
            "fixtures": [{"index": 0, "passed": fixture_passed, "execution": execution, "ready": ready, "queries": queries}],
            "actual_fixture_launches": 0 if execution is None else execution.get("helper_launches", 0),
            "actual_scheduler_launches": sum(row.get("actual_launches", 0) for row in queries),
            "all_query_children_reaped": len(queries) == 16 and all(row.get("reaped") is True for row in queries),
            "all_owned_leaders_reaped": execution is not None and execution.get("leader_reaped") is True,
            "all_groups_quiescent": execution is not None and execution.get("quiescent") is True,
            "all_query_pids_sampled": observer is not None and len(query_pids) == 16 and observer.accepted_pids == query_pids,
            "all_query_identities_matched": observer is not None and execution is not None
                and len(queries) == 16 and all(query_identity_observed(row, observer.traces, execution["pid"]) for row in queries),
            "candidate_child_sample_calls": 0 if observer is None else observer.calls,
            "sampled_query_pids": [] if observer is None else sorted(observer.accepted_pids),
            "retained_child_traces": [] if observer is None else observer.traces,
            "observation_errors": 0 if observer is None else observer.observation_errors,
            "pre_z_child_missing_rss_observed": execution is not None and child_gap(execution),
            "child_terminal_resolution_observed": execution is not None and execution.get("child_terminal_resolution") is not None,
            "reproduction_interpretation": "Only actual candidate frames with non-Z state, PF_EXITING and missing RSS establish the pending interval. Held Z children are already terminal. Successful sixteen-query lifecycle coverage alone is not reproduction.",
            "model_calls": 0, "native_calls": 0, "gpu_calls": 0, "synthetic_executable_surrogates": 0,
            "automatic_retry": False, "full_pairing_or_proof_checked": False}
        save(output / "result.json", result)
        total = sum(path.stat().st_size for path in output.rglob("*") if path.is_file())
        require(total <= LIMITS["total_result_bytes"], "Total probe evidence bound exceeded.")
        signal.alarm(0)
        print(json.dumps({"passed": passed, "elapsed_seconds": elapsed,
                          "pre_z_child_missing_rss_observed": result["pre_z_child_missing_rss_observed"]}), flush=True)
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
