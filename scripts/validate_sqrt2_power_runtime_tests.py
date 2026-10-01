#!/usr/bin/env python3
"""Bounded supervisor tests, which intentionally supervise tiny child workers.

Unlike proof leaves, these tests must launch process-accounting helpers. They
run as the controller, never by weakening the proof-worker descendant policy.
Each test worker keeps its own original runtime guard and smaller smoke bounds.
"""
import argparse
from pathlib import Path
import resource
import signal
import sys
import threading
import time

from run_sqrt2_power_pilot import ROOT, save_new
from stage_sqrt2_power_research import encode, file_pin

TEST = "peano-lab/py/tests/test_peano_hydra_review_runtime.py"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists() or args.output.is_symlink():
        parser.error("new append-only report required")
    import pytest
    stop = threading.Event()
    violations = []
    started = time.monotonic()
    scale = 1 if sys.platform == "darwin" else 1024

    def interrupted(_signum, _frame):
        # KeyboardInterrupt lets pytest unwind fixtures and the runtime's
        # BaseException ownership cleanup; this can never count as a pass.
        raise KeyboardInterrupt("supervisor-test resource guard")

    def measures():
        own = resource.getrusage(resource.RUSAGE_SELF)
        children = resource.getrusage(resource.RUSAGE_CHILDREN)
        return dict(cpu_seconds=own.ru_utime+own.ru_stime+children.ru_utime+children.ru_stime,
            peak_controller_rss_bytes=own.ru_maxrss*scale,
            peak_child_rss_bytes=children.ru_maxrss*scale,
            wall_seconds=time.monotonic()-started)

    def monitor():
        while not stop.wait(0.025):
            m = measures()
            if (m["cpu_seconds"] > 25 or m["wall_seconds"] > 35
                or m["peak_controller_rss_bytes"]+m["peak_child_rss_bytes"] > 512*1024**2):
                violations.append(m)
                signal.raise_signal(signal.SIGINT)
                return

    resource.setrlimit(resource.RLIMIT_CPU, (25, 26))
    signal.signal(signal.SIGINT, interrupted)
    signal.signal(signal.SIGALRM, interrupted)
    signal.signal(signal.SIGXCPU, interrupted)
    signal.alarm(35)
    watcher = threading.Thread(target=monitor, daemon=True)
    watcher.start()
    status = 2
    try:
        status = int(pytest.main(["-q", "-x", "--tb=short", "--disable-warnings",
            "-p", "no:cacheprovider", str(ROOT/TEST)]))
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        watcher.join(timeout=0.1)
        signal.alarm(0)
    measured = measures()
    passed = (status == 0 and not violations and measured["cpu_seconds"] <= 25
        and measured["wall_seconds"] <= 35
        and measured["peak_controller_rss_bytes"]+measured["peak_child_rss_bytes"] <= 512*1024**2)
    report = dict(schema="sqrt2-power-runtime-controller-tests-v1", authority="engineering_tests_not_proof",
        status="passed" if passed else "failed", pytest_exit_status=status, resources=measured,
        limits=dict(cpu_seconds=25, wall_seconds=35, rss_bytes=512*1024**2),
        violations=violations, test_source=file_pin(ROOT/TEST),
        runtime_source=file_pin(ROOT/"training/peano_hydra/review_runtime.py"),
        guard_source=file_pin(ROOT/"scripts/hydra_bounded_exec.py"))
    save_new(args.output, encode(report))
    print(encode(report).decode())
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
