#!/usr/bin/env python3
"""Plan, explicitly execute, or independently verify the paired search ablation.

CPU planning/verification uses bounded isolated native children. Execution is
only available in the new, explicitly approved one-shot Helios reservation.
No mode trains, uploads, resumes, overwrites or silently retries anything.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import sys
import time

sys.dont_write_bytecode = True
sys.pycache_prefix = "/dev/null"
ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]

from training.peano_hydra import search_workflow as workflow  # noqa: E402
from training.peano_hydra import origin_bridge as bridge  # noqa: E402


def main(argv=None):
    started, cpu_started = time.monotonic(), time.process_time()
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--metadata-worker"]:
        try:
            raw = sys.stdin.buffer.read(workflow.MAX_REQUEST_BYTES + 1)
            request = bridge._decode(raw, workflow.MAX_REQUEST_BYTES, "paired metadata request")
            bridge._require(raw == workflow.canonical(request), "metadata request must be canonical JSON")
            result = workflow.metadata_worker(request)
            sys.stdout.buffer.write(workflow.canonical(result) + b"\n")
            return 0
        except (ValueError, TypeError, KeyError, OSError, RuntimeError, RecursionError) as error:
            print("paired-metadata-worker: " + " ".join(str(error).split())[:3000], file=sys.stderr)
            return 2
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="bounded CPU plan; no inference or approval")
    mode.add_argument("--execute", action="store_true", help="fresh approved scheduled model evaluation")
    mode.add_argument("--verify-report", type=Path, help="authenticate complete report, then replay every positive")
    mode.add_argument("--verify-checkpoint", type=Path, help="read-only committed-prefix verification; never resume")
    parser.add_argument("--origin-reference", type=Path, default=ROOT / "_deploy/hydra-search-v2/origin/manifest.json")
    parser.add_argument("--expected-origin-reference-sha256", help="external RAW origin-reference file SHA")
    parser.add_argument("--origin-source-root", type=Path, help="explicit OFFLINE relocation; never inferred")
    parser.add_argument("--origin-adapter-manifest", type=Path, help="explicit OFFLINE relocation; never inferred")
    parser.add_argument("--approval", type=Path)
    parser.add_argument("--expected-approval-sha256", help="external RAW approved-record SHA")
    parser.add_argument("--checkpoint-dir", type=Path, help="new execution checkpoint; cannot be resumed")
    parser.add_argument("--stop-after-seconds", type=float, help="approved between-goal soft deadline")
    parser.add_argument("--output", type=Path, help="fresh plan/report/verification JSON; never overwrite")
    parser.add_argument("--process-output", type=Path, help="fresh CPU supervisor receipt, separate from plan/report")
    args = parser.parse_args(argv)
    reference, audit = None, None
    try:
        require = bridge._require
        require(args.stop_after_seconds is None or args.execute and math.isfinite(args.stop_after_seconds)
                and 0 < args.stop_after_seconds <= 1800, "soft deadline is only an approved bounded execution option")
        require(not args.execute or args.checkpoint_dir is not None and args.output is not None,
                "paired execution requires fresh checkpoint and report destinations")
        require(not args.execute or args.process_output is None, "CPU supervisor receipt option is not an execution option")
        require(args.checkpoint_dir is None or args.execute or args.check,
                "verification does not accept a new execution checkpoint directory")
        require((args.approval is None) == (args.expected_approval_sha256 is None),
                "approval path and its external RAW SHA are both required")
        require(not args.execute or args.approval is not None, "fresh GPU execution needs explicit approval")
        require(not os.environ.get("SLURM_JOB_ID") or args.approval is not None,
                "scheduled paired checks require their exact approved reservation")
        require(not (args.verify_report or args.verify_checkpoint) or not os.environ.get("SLURM_JOB_ID"),
                "independent proof verification belongs to a separate local CPU environment")
        reference_path, reference_sha = args.origin_reference.absolute(), args.expected_origin_reference_sha256
        source_root, adapter_manifest = args.origin_source_root, args.origin_adapter_manifest
        approved_plan = None
        if args.approval is not None:
            # This metadata-only gate is deliberately before any native or
            # model import. An approved old profile or a proposal cannot pass.
            from training.peano_hydra import search_launch

            require(args.approval.absolute() == ROOT / search_launch.APPROVAL, "paired approval path must be its fixed input")
            approval, approved_plan, _ = search_launch.validate_metadata(args.expected_approval_sha256)
            if args.execute or os.environ.get("SLURM_JOB_ID"):
                search_launch.check_job_reservation(args.expected_approval_sha256)
            require(reference_path == ROOT / approval["origin_reference_file"], "approved origin-reference path changed")
            require(reference_sha is None or reference_sha == approval["origin_reference_sha256"],
                    "approved origin-reference RAW hash changed")
            require(source_root is None and adapter_manifest is None,
                    "approved execution derives relocation only from its authenticated staged locations")
            reference_sha = approval["origin_reference_sha256"]
            source_root = ROOT / approval["locations"]["source_root"]
            adapter_manifest = ROOT / approval["locations"]["adapter_manifest"]
        require(reference_sha is not None, "CPU planning/verification requires an external origin-reference RAW SHA")
        reference = workflow.load_input(reference_path, reference_sha, source_root=source_root, adapter_manifest=adapter_manifest)
        input_path = args.verify_report or args.verify_checkpoint
        outputs = [value.absolute() for value in (args.output, args.process_output, args.checkpoint_dir) if value is not None]
        require(len(set(outputs)) == len(outputs), "paired output destinations must be distinct")
        for output in outputs:
            others = [value for value in outputs if value != output]
            if input_path is not None:
                others.append(input_path.absolute())
            workflow.guard_output(output, reference, other_paths=others)

        def progress(record):
            print(json.dumps(record, sort_keys=True, allow_nan=False), file=sys.stderr, flush=True)

        if not args.execute:
            check_mode = "report" if args.verify_report else "checkpoint" if args.verify_checkpoint else "plan"
            result, audit = workflow.offline_check(
                reference_path, reference_sha, mode=check_mode, input_path=input_path,
                source_root=source_root, adapter_manifest=adapter_manifest, progress=progress)
            if approved_plan is not None and check_mode == "plan":
                require(workflow.canonical(result) == workflow.canonical(approved_plan),
                        "CPU plan differs from the exact approved paired plan")
        else:
            from training.peano_hydra import search_comparison as comparison, comparison_checkpoint as cp

            plan = comparison.build_paired_plan(reference)
            require(workflow.canonical(plan.to_dict()) == workflow.canonical(approved_plan),
                    "fresh model evaluation differs from its exact approved plan")
            tracker = cp.Progress(progress)
            tracker.started, tracker.cpu_started = started, cpu_started
            stopped = [False]
            previous = {sig: signal.signal(sig, lambda *_: stopped.__setitem__(0, True)) for sig in (signal.SIGTERM, signal.SIGINT)}
            try:
                result = comparison.execute_paired_comparison(
                    plan, checkpoint_directory=args.checkpoint_dir.absolute(),
                    approval_sha256=args.expected_approval_sha256, progress=tracker,
                    stop_after_seconds=1500 if args.stop_after_seconds is None else args.stop_after_seconds,
                    stop_requested=lambda: stopped[0])
            finally:
                for sig, handler in previous.items():
                    signal.signal(sig, handler)
        if args.process_output is not None:
            workflow.publish_metadata(args.process_output.absolute(), audit, reference)
        if args.output is not None:
            workflow.guard_output(args.output.absolute(), reference)
            if args.execute:
                cp.publish_result(args.output.absolute(), workflow.canonical(result).decode() + "\n")
            else:
                workflow.publish_metadata(args.output.absolute(), result, reference)
            raw = bridge._read(args.output.absolute(), workflow.MAX_REPORT_BYTES)
            print(json.dumps({"output": str(args.output.absolute()), "sha256": hashlib.sha256(raw).hexdigest(),
                              "schema": result["schema"], "status": result.get("status", "planned")}, sort_keys=True))
        else:
            sys.stdout.buffer.write(workflow.canonical(result) + b"\n")
        return 0
    except Exception as error:
        cp_module = sys.modules.get("training.peano_hydra.comparison_checkpoint")
        if cp_module is not None and isinstance(error, cp_module.CheckpointPaused):
            print(json.dumps(error.receipt, sort_keys=True), file=sys.stderr, flush=True)
            return 3
        if not isinstance(error, (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError, RecursionError)):
            raise
        observation = getattr(error, "observation", None)
        if observation is not None and args.process_output is not None and reference is not None:
            try:
                workflow.publish_metadata(args.process_output.absolute(), {
                    "schema": workflow.AUDIT_SCHEMA, "status": "incomplete", "observation": observation,
                    "automatic_retry": False, "model_generation_performed": False,
                }, reference)
            except (ValueError, OSError):
                pass
        print("paired-search-evaluation: " + " ".join(str(error).split())[:3000], file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
