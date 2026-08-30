#!/usr/bin/env python3
"""Check or explicitly execute a fresh four-model PRIMARY32 comparison."""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).absolute().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "peano-lab/py"))
from training.peano_hydra import corrective_workflow as workflow


def main(argv=None):
    started, cpu_started = time.monotonic(), time.process_time()
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-report", type=Path)
    parser.add_argument("--experiment-dir", type=Path, default=Path(workflow.BUNDLE))
    parser.add_argument("--origin-request", type=Path, default=Path(workflow.INPUT))
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--expected-readiness-sha256")
    parser.add_argument("--trained-adapter", type=Path)
    parser.add_argument("--checkpoint-dir", type=Path)
    parser.add_argument("--stop-after-seconds", type=float)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        experiment, origins_path = args.experiment_dir.absolute(), args.origin_request.absolute()
        workflow.require(args.stop_after_seconds is None or (args.execute and math.isfinite(args.stop_after_seconds)
                         and 0 < args.stop_after_seconds <= 1800), "soft deadline is only a bounded execution option")
        workflow.require(not (args.approval is not None and args.expected_readiness_sha256 is not None),
                         "approval and offline-readiness anchors cannot be mixed")
        workflow.require(args.verify_report is None or not os.environ.get("SLURM_JOB_ID"),
                         "independent report replay runs in a separate local CPU environment")
        extras = ()
        if args.trained_adapter is not None:
            adapter = args.trained_adapter.absolute()
            if adapter.is_dir():
                descriptor = workflow.directory(adapter)
                os.close(descriptor)
                extras = (adapter,)
            else:
                workflow.require(adapter.name == "manifest.json", "explicit adapter must be its directory or manifest.json")
                workflow.read(adapter)
                extras = (adapter.parent,)
        protected = workflow.protected_roots(origin_request=origins_path, bundle=experiment, extra=extras)
        for destination in (args.output, args.checkpoint_dir):
            if destination is not None:
                workflow.guard_output(destination.absolute(), protected=protected)
        if args.output is not None and args.checkpoint_dir is not None:
            report_path, checkpoint_path = args.output.absolute(), args.checkpoint_dir.absolute()
            workflow.require(report_path != checkpoint_path and checkpoint_path not in report_path.parents
                             and report_path not in checkpoint_path.parents, "report and checkpoint destinations must be separate")
        if args.execute:
            workflow.require(args.checkpoint_dir is not None and args.output is not None,
                             "execution needs fresh checkpoint and report destinations")
        expected = args.expected_readiness_sha256
        if args.execute or args.approval is not None or os.environ.get("SLURM_JOB_ID"):
            workflow.require(args.approval is not None, "actual evaluation needs fresh explicit approval")
            approval = workflow.check_approval(args.approval.absolute(), origin_request=origins_path,
                                               output=experiment, stage_name="evaluate", require_job=True)
            expected = approval["ready_bundle_sha256"]
        workflow.require(expected is not None, "offline planning or verification needs its external readiness SHA")
        if not args.execute:
            result = workflow.offline_comparison(experiment, origin_request=origins_path,
                                                 expected_readiness_sha256=expected, trained_adapter=args.trained_adapter,
                                                 report=args.verify_report)
        else:
            from training.peano_hydra import corrective_comparison as comparison, comparison_checkpoint as cp
            progress = cp.Progress(lambda record: print(json.dumps(record, sort_keys=True), file=sys.stderr, flush=True))
            # Count approval, origin hashing and planning, not only inference.
            progress.started, progress.cpu_started = started, cpu_started
            stopped = [False]
            previous = {sig: signal.signal(sig, lambda *_: stopped.__setitem__(0, True)) for sig in (signal.SIGTERM, signal.SIGINT)}
            try:
                _, references = workflow.load_bundle(experiment, origin_request=origins_path,
                                                      expected_readiness_sha256=expected)
                plan = comparison.build_corrective_plan(experiment / "preparation", catalog=references["catalog"],
                                                        scaled=references["scaled"], trained_adapter=args.trained_adapter)
                workflow.guard_output(args.checkpoint_dir.absolute(), protected=protected)
                workflow.guard_output(args.output.absolute(), protected=protected)
                result = comparison.execute_corrective_comparison(plan, checkpoint_directory=args.checkpoint_dir.absolute(),
                                                                  progress=progress, stop_after_seconds=args.stop_after_seconds,
                                                                  stop_requested=lambda: stopped[0])
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
        rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
        if args.output is not None:
            workflow.guard_output(args.output.absolute(), protected=protected)
            if args.execute:
                cp.publish_result(args.output.absolute(), rendered)
            else:
                workflow.publish_metadata(args.output.absolute(), result, protected=protected)
        print(rendered, end="")
        return 0
    except Exception as error:
        from training.peano_hydra.comparison_checkpoint import CheckpointPaused
        if isinstance(error, CheckpointPaused):
            print(json.dumps(error.receipt, sort_keys=True), file=sys.stderr)
            return 3
        if not isinstance(error, (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError)):
            raise
        print("corrective-evaluation: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
