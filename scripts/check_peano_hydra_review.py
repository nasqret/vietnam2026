#!/usr/bin/env python3
"""Plan, execute, or recheck Hydra's bounded reference/lineage review evidence."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from training.peano_hydra.frontier import canonical, decode  # noqa: E402
from training.peano_hydra.review import (  # noqa: E402
    DEFAULT_DEVELOPMENT, HydraReviewError, build_review_plan, execute_review,
    read_allocations, verify_review, worker,
)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--plan", action="store_true", help="read-only review planning (default)")
    modes.add_argument("--run", action="store_true", help="execute fresh bounded source/reference checks")
    modes.add_argument("--verify", type=Path, metavar="DIRECTORY", help="independently rebuild/replay saved evidence")
    modes.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--reference-project", type=Path, default=ROOT.parent / "peano-lab-lean")
    parser.add_argument("--lean-binary", type=Path, help="actual installed Lean executable, not the elan shim")
    parser.add_argument("--development-directory", type=Path, default=DEFAULT_DEVELOPMENT)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--allocations", type=Path, help="explicit JSON array of whole-component allocations")
    parser.add_argument("--cold-scope", choices=("none", "sample", "full"), default="sample")
    parser.add_argument("--cold-batch-size", type=int, default=1)
    parser.add_argument("--cold-wall-budget", type=int, default=900)
    parser.add_argument("--full-plan", action="store_true")
    args = parser.parse_args(argv)
    def progress(stage, done, total, detail):
        print(f"{stage}: {done}/{total} {detail}", file=sys.stderr, flush=True)
    try:
        if args.worker:
            if argv != ["--worker"]:
                raise HydraReviewError("the internal worker accepts only its bounded stdin request")
            worker(decode(sys.stdin.buffer.read(16 * 1024**2 + 1), limit=16 * 1024**2))
            return 0
        if args.verify:
            planning_options = {"--output-dir", "--allocations", "--lean-binary", "--reference-project",
                                "--development-directory", "--cold-scope", "--cold-batch-size", "--cold-wall-budget", "--full-plan"}
            if any(argument.partition("=")[0] in planning_options for argument in argv):
                raise HydraReviewError("verification uses the frozen plan and never changes its inputs")
            result = verify_review(args.verify, progress=progress)
        else:
            if args.lean_binary is None:
                raise HydraReviewError("select --lean-binary /absolute/path/to/the/installed/lean; no toolchain is installed automatically")
            if args.run != (args.output_dir is not None):
                raise HydraReviewError("--run requires a fresh --output-dir; planning never writes")
            allocations = read_allocations(args.allocations) if args.allocations else None
            plan = build_review_plan(reference_project=args.reference_project, lean_binary=args.lean_binary,
                                     development_directory=args.development_directory, cold_scope=args.cold_scope,
                                     cold_batch_size=args.cold_batch_size, allocations=allocations,
                                     cold_wall_budget=args.cold_wall_budget)
            result = execute_review(plan, args.output_dir, progress=progress) if args.run else plan
            if not args.full_plan:
                result = ({"status": result["status"], "report_sha256": result["report_sha256"],
                           "summary": result["summary"], "output_dir": str(args.output_dir),
                           "model_training_authorized": False, "h0_complete": False} if args.run else {
                    "status": "planned", "plan_sha256": plan["plan_sha256"],
                    "lineage_status": plan["lineage_review"]["status"],
                    "feasibility": plan["lineage_review"]["feasibility"],
                    "conformance_cases": plan["conformance"]["case_count"],
                    "positive_formulas": plan["conformance"]["distinct_positive_formula_count"],
                    "selected_compiler": plan["reference"]["compiler_version"],
                    "matches_project_toolchain_pin": plan["reference"]["matches_project_toolchain_pin"],
                    "cold_selection": plan["cold_selection"], "cold_wall_budget": plan["cold_wall_budget"],
                    "model_training_authorized": False, "h0_complete": False,
                })
        sys.stdout.buffer.write(canonical(result) + b"\n")
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError) as error:
        print("hydra-review: " + " ".join(str(error).split())[:3000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
