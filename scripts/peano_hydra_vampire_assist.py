#!/usr/bin/env python3
"""Print one canonical JSON result from the offline Hydra/Vampire preview."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    while str(import_root) in sys.path:
        sys.path.remove(str(import_root))
sys.path[:0] = [str(PEANO_PYTHON), str(REPOSITORY_ROOT)]

from training.peano_hydra.vampire_assistant import (  # noqa: E402
    VAMPIRE_ASSISTANT_VERSION,
    VampireAssistantError,
    canonical_evidence_bytes,
    run_vampire_assistant,
)


DEFAULT_VAMPIRE_ARGUMENTS = (
    "--mode",
    "vampire",
    "--input_syntax",
    "tptp",
    "--proof",
    "tptp",
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "run one offline diagnostic Vampire search, reconstruct ordinary "
            "Peano commands, and require a fresh original-goal kernel check"
        ),
        epilog=(
            "This preview has authority=none and live_dispatch_registered=false; "
            "it is not an H0-contained campaign runner."
        ),
    )
    parser.add_argument("goal", help="closed canonical Peano goal")
    parser.add_argument(
        "--premise",
        action="append",
        default=[],
        metavar="NAME",
        help="explicit premise name, repeated in disclosure order",
    )
    parser.add_argument(
        "--allow-premise",
        action="append",
        default=None,
        metavar="NAME",
        help="optional capability mask; repeat for every permitted name",
    )
    parser.add_argument("--vampire", required=True, type=Path, metavar="PATH")
    parser.add_argument(
        "--vampire-arg",
        action="append",
        default=None,
        metavar="ARG",
        help=(
            "exact solver argument; one or more explicit values replace the pinned "
            "Vampire TPTP defaults (use --vampire-arg=VALUE for leading dashes)"
        ),
    )
    parser.add_argument("--wall-time-ms", required=True, type=int)
    parser.add_argument("--output-bytes", required=True, type=int)
    parser.add_argument(
        "--version",
        action="version",
        version=f"peano-hydra-vampire-assist v{VAMPIRE_ASSISTANT_VERSION}",
    )
    return parser


def _input_rejection(args: argparse.Namespace, error: BaseException) -> dict[str, object]:
    arguments = (
        DEFAULT_VAMPIRE_ARGUMENTS
        if args.vampire_arg is None
        else tuple(args.vampire_arg)
    )
    return {
        "arguments": list(arguments),
        "authority": "none",
        "campaign_host_eligible": False,
        "campaign_peak_metric_eligible": False,
        "campaign_usage_metric_eligible": False,
        "comparison_eligible": False,
        "diagnostic": " ".join(str(error).split())[:2_000],
        "evaluation_eligible": False,
        "format": "peano-hydra-vampire-assistant",
        "goal": args.goal,
        "h0_host_contained": False,
        "kernel_accepted": False,
        "live_dispatch_registered": False,
        "mode": "offline-diagnostic",
        "premise_names": list(args.premise),
        "publication_eligible": False,
        "retrieval_eligible": False,
        "status": "input-rejected",
        "training_eligible": False,
        "v": VAMPIRE_ASSISTANT_VERSION,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    arguments = (
        DEFAULT_VAMPIRE_ARGUMENTS
        if args.vampire_arg is None
        else tuple(args.vampire_arg)
    )
    allowlist = (
        None if args.allow_premise is None else frozenset(args.allow_premise)
    )
    try:
        result = run_vampire_assistant(
            args.goal,
            tuple(args.premise),
            executable=args.vampire,
            arguments=arguments,
            wall_time_ms=args.wall_time_ms,
            output_bytes=args.output_bytes,
            premise_allowlist=allowlist,
        )
    except (VampireAssistantError, TypeError, ValueError) as exc:
        result = _input_rejection(args, exc)
    try:
        sys.stdout.buffer.write(canonical_evidence_bytes(result))
    except BrokenPipeError:
        return 0
    return 0 if result.get("status") == "accepted" else 1


if __name__ == "__main__":
    raise SystemExit(main())
