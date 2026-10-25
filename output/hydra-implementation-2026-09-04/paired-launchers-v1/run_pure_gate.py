"""Run only constructed metadata/fake-transport tests; no real launch is allowed."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import resource
import signal
import sys
import time
import unittest

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU, (15, 16))
    # macOS rejects lowering this process's virtual-address limit. These pure
    # fixed-size fixtures use the CPU/wall caps; do not claim an RSS guarantee.
    if sys.platform == "linux":
        resource.setrlimit(resource.RLIMIT_AS, (1024**3, 1024**3))
    signal.alarm(30)
    blocked = []
    def guard(event, arguments):
        if event in {"subprocess.Popen", "os.system", "os.fork", "os.posix_spawn", "socket.connect", "socket.bind", "os.kill", "os.killpg"}:
            blocked.append(event)
            raise AssertionError("Forbidden real operation in pure gate: " + event)
        if event == "import" and str(arguments[0]).startswith(("peano_lab", "peano_hydra", "peano_policy", "torch", "transformers", "peft", "hydra_training_v5")):
            blocked.append("import:" + str(arguments[0]))
            raise AssertionError("Forbidden native/model import in pure gate.")
    sys.addaudithook(guard)
    watched = [HERE / name for name in ("paired_launchers.py", "remote_paired_control.py", "test_paired_launchers.py", "run_pure_gate.py")]
    watched += [HERE.parent / "p6-training-launchers-v2" / name for name in ("training_launchers.py", "remote_training_control.py")]
    watched += [HERE.parent / "combined-source-bundle-01" / name for name in ("manifest.json", "paired-source-pins.json")]
    def pins():
        return {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in watched}
    before = pins()
    started = time.monotonic()
    suite = unittest.defaultTestLoader.discover(str(HERE), pattern="test_paired_launchers.py")
    log = io.StringIO()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = pins()
    record = {"schema": "hydra-paired-launchers-pure-gate-v1", "passed": result.wasSuccessful() and before == after and not blocked,
        "tests": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "elapsed_seconds": time.monotonic() - started, "blocked_real_operations": blocked,
        "sources_unchanged": before == after, "sources_before": before, "sources_after": after,
        "native_execution": False, "model_execution": False, "scheduler_queries": 0, "ssh_calls": 0,
        "test_evidence_is_synthetic": True, "cpu_limit_seconds": 15, "wall_alarm_seconds": 30,
        "address_space_limit_bytes": 1024**3 if sys.platform == "linux" else None}
    (args.output / "tests.log").write_text(log.getvalue())
    (args.output / "result.json").write_text(json.dumps(record, indent=2) + "\n")
    print(json.dumps({key: record[key] for key in ("passed", "tests", "failures", "errors", "skipped", "elapsed_seconds", "blocked_real_operations", "sources_unchanged")}), flush=True)
    signal.alarm(0)
    return 0 if record["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
