#!/usr/bin/env python3
"""Plan or explicitly execute one matched frozen-Alpha Hydra comparison.

Default and ``--check`` modes do not import a model framework, start a GPU,
submit a remote job, or invent inference metrics. ``--symbolic-controls`` may
optionally run fixed verifier-backed controls. Actual Qwen inference requires
both explicit ``--execute-models`` and ``--trained-adapter PATH``; the pinned
pretrained model and fresh epoch-compatible LoRA then run sequentially on one
CUDA GPU under identical bounded proof-search authority.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from training.peano_hydra.epoch import HydraEpochError  # noqa: E402
from training.peano_hydra.evaluation import (  # noqa: E402
    DEFAULT_LIMITS,
    DEFAULT_MAX_NEW_TOKENS,
    DEFAULT_SEED,
    HydraEvaluationError,
    _digest,
    build_matched_evaluation_plan,
    execute_model_comparison,
    run_symbolic_controls,
)
from training.peano_hydra.runner import HydraRunnerError  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--preparation-dir",
        type=Path,
        default=REPOSITORY_ROOT / "_deploy" / "hydra-posttrain",
        metavar="PATH",
        help="complete digest-bound Hydra Alpha post-training preparation directory",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the complete model-free matched plan without writing any artifact",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help="create one new evaluation artifact; never overwrites an existing path",
    )
    parser.add_argument(
        "--symbolic-controls",
        action="store_true",
        help="run explicitly labeled fixed symbolic controls through the independent kernel",
    )
    parser.add_argument(
        "--execute-models",
        action="store_true",
        help="explicitly execute genuine matched pretrained and trained inference on one CUDA GPU",
    )
    parser.add_argument(
        "--trained-adapter",
        type=Path,
        metavar="PATH",
        help="completed frozen-Alpha LoRA directory or its exact manifest.json",
    )
    parser.add_argument("--max-depth", type=int, default=DEFAULT_LIMITS.max_depth)
    parser.add_argument("--beam-width", type=int, default=DEFAULT_LIMITS.beam_width)
    parser.add_argument(
        "--candidates-per-state",
        type=int,
        default=DEFAULT_LIMITS.candidates_per_state,
    )
    parser.add_argument(
        "--max-model-calls",
        type=int,
        default=DEFAULT_LIMITS.max_model_calls,
    )
    parser.add_argument("--max-states", type=int, default=DEFAULT_LIMITS.max_states)
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.check and arguments.output is not None:
        parser.error("--check never writes an artifact and cannot be combined with --output")
    if arguments.check and arguments.execute_models:
        parser.error("--check is model-free and cannot be combined with --execute-models")
    if arguments.execute_models and arguments.trained_adapter is None:
        parser.error("actual matched model execution requires explicit --trained-adapter PATH")
    try:
        limits = SearchLimits(
            max_depth=arguments.max_depth,
            beam_width=arguments.beam_width,
            candidates_per_state=arguments.candidates_per_state,
            max_model_calls=arguments.max_model_calls,
            max_states=arguments.max_states,
        )
        plan = build_matched_evaluation_plan(
            arguments.preparation_dir,
            limits=limits,
            seed=arguments.seed,
            max_new_tokens=arguments.max_new_tokens,
            trained_adapter=arguments.trained_adapter,
        )
        report = plan.to_dict()
        if arguments.symbolic_controls:
            report["symbolic_controls"] = run_symbolic_controls(plan)
        if arguments.execute_models:
            measured = execute_model_comparison(plan)
            report["comparison"] = measured
            for name, lane in measured["lanes"].items():
                report["lanes"][name]["status"] = "executed"
                report["lanes"][name]["kernel_checked_proofs"] = lane[
                    "kernel_checked_proofs"
                ]
                report["lanes"][name]["model_generate_calls"] = lane[
                    "model_generate_calls"
                ]
        report["evaluation_sha256"] = _digest(report)
        rendered = json.dumps(
            report,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        ) + "\n"
        if arguments.output is not None:
            if arguments.output.is_symlink():
                raise HydraEvaluationError("evaluation output refuses a symbolic-link destination")
            with arguments.output.open("x", encoding="utf-8", newline="\n") as destination:
                destination.write(rendered)
            print(arguments.output)
        else:
            print(rendered, end="")
    except (
        HydraEpochError,
        HydraEvaluationError,
        HydraRunnerError,
        OSError,
        RuntimeError,
        TypeError,
        ValueError,
    ) as error:
        print(
            f"eval-peano-hydra-posttrain: {' '.join(str(error).split())}",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
