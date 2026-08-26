#!/usr/bin/env python3
"""Plan, execute, or independently replay a bounded, model-free Hydra DEV run."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from training.peano_hydra.frontier import (  # noqa: E402
    DevelopmentEvaluationError, WorkerLimits, build_plan, canonical, decode,
    execute_plan, verify_run, worker,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="inspect without running any search (default)")
    modes.add_argument("--run", action="store_true", help="execute bounded sequential CPU workers")
    modes.add_argument("--verify", type=Path, metavar="DIRECTORY", help="replay every retained proof")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--preparation", type=Path, action="append", default=[],
                        help="audit an existing preparation without modifying it; repeatable")
    parser.add_argument("--output-dir", type=Path, help="fresh directory required for --run")
    parser.add_argument("--wall-seconds", type=int, default=5)
    parser.add_argument("--cpu-seconds", type=int, default=3)
    parser.add_argument("--full-plan", action="store_true", help="print full planning evidence, including all masks")
    args = parser.parse_args(argv)
    def progress(done, total, row):
        print(f"{done}/{total} {row['lane']} {row['goal']['id']}: {row['status']} ({row['reason']})",
              file=sys.stderr, flush=True)
    try:
        if args.worker:
            result = worker(decode(sys.stdin.buffer.read(2 * 1024 * 1024 + 1), limit=2 * 1024 * 1024))
        elif args.verify:
            if args.output_dir or args.preparation:
                raise DevelopmentEvaluationError("verification never writes or selects new preparations")
            result = verify_run(args.verify, progress=progress)
        else:
            if args.run != (args.output_dir is not None):
                raise DevelopmentEvaluationError("--run requires --output-dir; planning never writes")
            plan = build_plan(tuple(args.preparation), limits=WorkerLimits(
                wall_seconds=args.wall_seconds, cpu_seconds=args.cpu_seconds))
            result = execute_plan(plan, args.output_dir, progress=progress) if args.run else plan
            if not args.full_plan:
                if args.run:
                    result = {"status": result["status"], "output_dir": str(args.output_dir),
                              "report_sha256": result["report_sha256"], "metrics": result["metrics"],
                              "research_claim_eligible": False}
                else:
                    benchmark = plan["benchmark"]
                    result = {"status": "planned", "plan_sha256": plan["plan_sha256"],
                              "profile_sha256": plan["profile"]["profile_sha256"],
                              "benchmark_sha256": benchmark["manifest_sha256"],
                              "goals": benchmark["goal_count"], "expanded_goals": benchmark["expanded_goal_count"],
                              "historical_goals": benchmark["historical_goal_count"],
                              "families": benchmark["declared_family_count"],
                              "connected_components": benchmark["declared_connected_component_count"],
                              "preparation_audits": [{"directory": item["preparation_directory"],
                                  "status": item["audit"]["status"],
                                  "blocked_families": item["audit"]["blocked_family_count"],
                                  "exposed_rows": item["audit"]["exposed_rows"]} for item in plan["preparation_audits"]],
                              "limits": plan["limits"], "reserved_worker_runs": plan["reserved_worker_runs"],
                              "reserved_worker_wall_seconds": plan["reserved_worker_wall_seconds"],
                              "parallel_workers": 1, "research_claim_eligible": False,
                              "sealed_benchmark": False, "model_comparison_performed": False}
        sys.stdout.buffer.write(canonical(result) + b"\n")
        return 0
    except (DevelopmentEvaluationError, ValueError, TypeError, OSError, KeyError) as error:
        print("hydra-development: " + " ".join(str(error).split())[:2000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
