#!/usr/bin/env python3
"""Compare BASE/previous/new under one V4 authority on 96 exposed native goals.

Run from the compatible frozen source checkout. Both preparations must remain
at the repository-relative paths bound by their original config.toml files;
adapter bundles may be relocated. --verify never imports model frameworks and
freshly replays every successful exact command route against its original goal.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT, ROOT / "peano-lab/py"):
    sys.path.insert(0, str(directory))

from training.peano_hydra.comparison import (  # noqa: E402
    ComparisonError, MAX_REPORT_BYTES, build_comparison_plan, execute_comparison, verify_comparison,
)
from training.peano_hydra import comparison_checkpoint as checkpoint  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="freeze the complete model-free plan (default)")
    mode.add_argument("--execute-models", action="store_true", help="run three models sequentially on one CUDA GPU")
    mode.add_argument("--verify", type=Path, metavar="FILE", help="authenticate and independently replay saved successful proofs")
    parser.add_argument("--preparation-dir", type=Path, required=True, help="original config-bound new V2 preparation path")
    parser.add_argument("--previous-preparation-dir", type=Path, required=True, help="original config-bound previous V1 preparation path")
    parser.add_argument("--previous-adapter", type=Path, required=True, help="previous bundle/manifest, pinned to the declared external SHA")
    parser.add_argument("--trained-adapter", type=Path, help="completed new preparation-compatible final adapter; not needed for --check")
    parser.add_argument("--output", type=Path, help="write one fresh JSON file; never overwrite")
    parser.add_argument("--checkpoint-dir", type=Path,
                        help="opt-in durable per-goal receipts; parent must exist, directory must be new unless --resume")
    parser.add_argument("--resume", action="store_true",
                        help="authenticate/replay a clean saved prefix; never retry an interrupted in-flight goal")
    parser.add_argument("--stop-after-seconds", type=float,
                        help="checkpoint mode only: soft deadline including planning, checked between goals (exit 3)")
    args = parser.parse_args(argv)
    if (args.execute_models or args.verify is not None or args.resume) and args.trained_adapter is None:
        parser.error("--execute-models/--verify/--resume requires explicit --trained-adapter PATH")
    if (args.resume or args.stop_after_seconds is not None) and args.checkpoint_dir is None:
        parser.error("--resume/--stop-after-seconds requires --checkpoint-dir")
    if args.verify is not None and args.checkpoint_dir is not None:
        parser.error("--verify reads the complete report; use --check --resume for checkpoint prefix verification")
    if args.stop_after_seconds is not None and not args.execute_models:
        parser.error("--stop-after-seconds requires --execute-models")
    progress = checkpoint.Progress(lambda value: print(json.dumps(value, sort_keys=True, allow_nan=False), flush=True))
    requested_stop = [False]
    previous_handler = None
    try:
        if args.output is not None and (args.output.exists() or args.output.is_symlink()):
            raise ComparisonError("comparison output must be a fresh non-symlink file")
        if args.checkpoint_dir is not None and args.output is not None:
            checkpoint.check_fresh_output(args.output)
            if args.output.absolute().is_relative_to(args.checkpoint_dir.absolute()):
                raise ComparisonError("comparison output must be outside its closed checkpoint directory")
        if args.checkpoint_dir is not None and args.execute_models and hasattr(signal, "SIGUSR1"):
            previous_handler = signal.signal(signal.SIGUSR1, lambda *_: requested_stop.__setitem__(0, True))
        keywords = {"previous_preparation_directory": args.previous_preparation_dir,
                    "previous_adapter": args.previous_adapter, "trained_adapter": args.trained_adapter}
        if args.verify is not None:
            result = checkpoint.verify_comparison(args.verify, preparation_directory=args.preparation_dir, **keywords)
        elif args.checkpoint_dir is not None:
            if args.execute_models or args.resume:
                progress.emit("plan-validation-start")
            plan = checkpoint.build_checkpoint_plan(args.preparation_dir, **keywords)
            if args.execute_models:
                result = checkpoint.execute_checkpoint_comparison(
                    plan, checkpoint_directory=args.checkpoint_dir, resume=args.resume, progress=progress,
                    stop_after_seconds=args.stop_after_seconds, stop_requested=lambda: requested_stop[0])
            elif args.resume:
                result = checkpoint.verify_checkpoint(plan, args.checkpoint_dir, progress=progress)
            else:
                result = plan.to_dict()
        else:
            plan = build_comparison_plan(args.preparation_dir, **keywords)
            result = execute_comparison(plan) if args.execute_models else plan.to_dict()
        rendered = json.dumps(result, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"
        if len(rendered.encode()) > MAX_REPORT_BYTES:
            raise ComparisonError("rendered comparison artifact exceeds its byte reservation")
        if args.output is None:
            print(rendered, end="")
        elif args.checkpoint_dir is not None:
            checkpoint.publish_result(args.output, rendered)
            print(args.output, flush=True)
        else:
            with args.output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(rendered)
            print(args.output)
    except checkpoint.CheckpointPaused as paused:
        print(json.dumps(paused.receipt, ensure_ascii=False, allow_nan=False, sort_keys=True), flush=True)
        return 3
    except (ValueError, TypeError, OSError, RuntimeError, RecursionError) as error:
        print(f"eval-peano-hydra-comparison: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    finally:
        if previous_handler is not None:
            signal.signal(signal.SIGUSR1, previous_handler)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
