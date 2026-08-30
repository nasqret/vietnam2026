#!/usr/bin/env python3
"""Plan or run exact Alpha-v28 reference/hotspot calibration; never a full campaign.

Use Python >=3.10. Execution requires a separately frozen clean source commit,
the raw SHA256 of a saved plan, a fresh output directory, and external enclosing
process-group supervision. This CLI enforces the original child-worker bounds;
it neither installs Lean nor grants resource, lineage, H0/H1 or human approval.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from training.peano_hydra.frontier import canonical, decode, read_bytes
from training.peano_hydra.review_v28 import (
    MAX_BYTES, MODES, HydraReviewError, build_review_plan, execute_review,
    verify_review, worker,
)


def main(argv=None):
    args_list = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--plan", action="store_true")
    action.add_argument("--run", action="store_true")
    action.add_argument("--verify", type=Path, metavar="ARCHIVE")
    action.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--mode", choices=MODES, default="native-hotspots")
    parser.add_argument("--reference-project", type=Path)
    parser.add_argument("--lean-binary", type=Path)
    parser.add_argument("--cold-batch-size", type=int, default=1)
    parser.add_argument("--cold-wall-budget", type=int, default=900)
    parser.add_argument("--full-plan", action="store_true")
    parser.add_argument("--plan-file", type=Path)
    parser.add_argument("--plan-sha256", help="external SHA256 of raw plan-file bytes")
    parser.add_argument("--report-sha256", help="external SHA256 of raw archived report.json")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(args_list)
    try:
        if args.worker:
            if args_list != ["--worker"]:
                raise HydraReviewError("internal worker accepts no CLI overrides")
            raw = sys.stdin.buffer.read(16 * 1024**2 + 1)
            worker(decode(raw, limit=16 * 1024**2))
            return 0
        if args.run or args.verify is not None:
            planning_options = {"--mode", "--reference-project", "--lean-binary", "--cold-batch-size",
                                "--cold-wall-budget", "--full-plan"}
            if any(value.split("=", 1)[0] in planning_options for value in args_list):
                raise HydraReviewError("execution and reproduction use only their pinned saved plan")
            if args.output_dir is None:
                raise HydraReviewError("execution/reproduction requires a fresh --output-dir")
            if args.run:
                if args.plan_file is None or args.plan_sha256 is None or args.report_sha256 is not None:
                    raise HydraReviewError("run requires --plan-file and its raw --plan-sha256 only")
                raw = read_bytes(args.plan_file, limit=MAX_BYTES)
                if hashlib.sha256(raw).hexdigest() != args.plan_sha256:
                    raise HydraReviewError("execution plan differs from its external raw file pin")
                result = execute_review(decode(raw, limit=MAX_BYTES), args.output_dir)
            else:
                if args.report_sha256 is None or args.plan_file is not None or args.plan_sha256 is not None:
                    raise HydraReviewError("verify requires the original raw --report-sha256 only")
                result = verify_review(args.verify, args.output_dir, report_sha256=args.report_sha256)
        else:
            if any(value is not None for value in (args.output_dir, args.plan_file, args.plan_sha256, args.report_sha256)):
                raise HydraReviewError("planning does not accept execution artifacts or write directories")
            plan = build_review_plan(mode=args.mode, reference_project=args.reference_project,
                                     lean_binary=args.lean_binary, cold_batch_size=args.cold_batch_size,
                                     cold_wall_budget=args.cold_wall_budget)
            result = plan if args.full_plan else {
                "schema": plan["schema"], "status": "planned", "mode": plan["mode"],
                "plan_sha256": plan["plan_sha256"], "epoch_sha256": plan["epoch_sha256"],
                "source": {key: plan["source"][key] for key in ("git_commit", "git_dirty", "files_sha256")},
                "full_epoch_targets": plan["cold_plan"]["target_count"],
                "full_target_records_sha256": plan["cold_plan"]["full_target_records_sha256"],
                "outside_replay_profile": plan["cold_plan"]["outside_replay_profile"],
                "cold_selection": plan["cold_selection"], "worker_reservations": plan["worker_reservations"],
                "ancillary_inputs": plan["ancillary_inputs"],
                "whole_controller_guard": plan["whole_controller_guard"],
                "full_execution_authorized": False, "model_training_authorized": False,
                "h0_complete": False, "h1_complete": False, "research_claim_eligible": False,
            }
        sys.stdout.buffer.write(canonical(result) + b"\n")
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print(f"v28 review rejected: {str(error)[:3000]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
