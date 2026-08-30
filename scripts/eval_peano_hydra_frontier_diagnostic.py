#!/usr/bin/env python3
"""Check, execute one approved completed-adapter comparison, or independently replay it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import sys
import time

STARTED = time.monotonic()
ROOT = Path(__file__).absolute().parents[1]
sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-run", type=Path)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--expected-request-sha256", required=True)
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--expected-approval-sha256")
    parser.add_argument("--expected-run-sha256")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stop-after-seconds", type=float)
    args = parser.parse_args(argv)
    from training.peano_hydra import frontier_diagnostic_run as runner
    stopped = False
    def stop(_signum, _frame):
        nonlocal stopped
        stopped = True
    try:
        runner.require((args.approval is None) == (args.expected_approval_sha256 is None),
                       "approval path and its external raw SHA are required together")
        runner.require(not args.execute or args.approval is not None and args.output is not None,
                       "execution requires exact resource approval and a fresh output directory")
        runner.require(args.execute or args.approval is None and args.stop_after_seconds is None,
                       "approval and soft deadline options belong only to execution")
        runner.require(bool(args.verify_run) == (args.expected_run_sha256 is not None),
                       "independent verification requires an external raw run-manifest SHA")
        runner.require(not args.verify_run or args.output is not None,
                       "verification requires a separate fresh output receipt")
        if args.verify_run:
            runner.require(not runner.os.environ.get("SLURM_JOB_ID"), "independent verification belongs outside a GPU allocation")
        if args.output is not None and not args.execute:
            runner.guard_output(args.output, extra=(args.verify_run,) if args.verify_run else ())
        progress = None
        if args.execute:
            signal.signal(signal.SIGINT, stop)
            signal.signal(signal.SIGTERM, stop)
            if hasattr(signal, "SIGUSR1"): signal.signal(signal.SIGUSR1, stop)
            # Progress validates each canonical event against its existing
            # 4096-byte bound. Keep stdout reserved for the final result.
            progress = runner.evaluation.cp.Progress(lambda record: print(
                runner.canonical(record).decode("utf-8"), file=sys.stderr, flush=True))
            progress.emit("diagnostic-input-validation-start")
        checked = runner.check_request(args.request, args.expected_request_sha256)
        if args.execute:
            progress.emit("diagnostic-input-validation-complete")
            result = runner.execute(checked, approval_path=args.approval,
                approval_sha256=args.expected_approval_sha256, output=args.output,
                stop_after_seconds=args.stop_after_seconds if args.stop_after_seconds is not None else 720,
                started=STARTED, stop_requested=lambda: stopped, progress=progress)
        elif args.verify_run:
            result = runner.verify_run(checked, args.verify_run, args.expected_run_sha256)
            runner.guard_output(args.output, extra=(args.verify_run,))
            runner.write_report(args.output, result)
        else:
            result = checked.summary()
            if args.output is not None:
                runner.guard_output(args.output)
                runner.files.publish_metadata(args.output, result, protected=runner.launch.output_protections())
        print(json.dumps(result, sort_keys=True, ensure_ascii=False, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, RecursionError) as error:
        print("frontier-dev-diagnostic: " + " ".join(str(error).split())[:3000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
