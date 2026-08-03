#!/usr/bin/env python3
"""Run Peano Hydra's paired teacher-oracle plumbing pilot.

The default experiment compares a genuine fixed symbolic arithmetic head with
the same head plus exact-state structural actions extracted from the checked
``triangular-even-readable.pa`` script.  It is an interface/headroom smoke,
not a Qwen or sealed-benchmark result.  Every positive route is freshly traced
and independently kernel checked before JSON publication.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from training.peano_hydra.pilot import (  # noqa: E402
    DEFAULT_ARTIFACT,
    PILOT_VERSION,
    TeacherOraclePilotError,
    run_teacher_oracle_pilot,
)
from training.peano_hydra.runner import HydraRunnerError  # noqa: E402
from training.peano_hydra.profile import semantic_profile_sha256  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "run the fixed Peano Hydra symbolic-only versus "
            "teacher_oracle_plumbing pilot"
        ),
        epilog=(
            "A successful hybrid row demonstrates checked interface plumbing "
            "only; it is not evidence of Qwen capability or an LLM advantage."
        ),
    )
    parser.add_argument(
        "--artifact",
        type=Path,
        default=DEFAULT_ARTIFACT,
        metavar="PATH",
        help=(
            "readable checked teacher script "
            "(default: artifacts/triangular-even-readable.pa)"
        ),
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit one canonical JSON line instead of indented JSON",
    )
    parser.add_argument(
        "--include-trace",
        action="store_true",
        help="include complete binding v1 replay traces in the JSON report",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help=(
            "create PATH with the report instead of printing it; refuses to "
            "overwrite an existing artifact"
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version=(
            f"eval-peano-hydra pilot-v{PILOT_VERSION}\n"
            f"profile={semantic_profile_sha256()}"
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        report = run_teacher_oracle_pilot(args.artifact)
        rendered = report.json(
            indent=None if args.compact else 2,
            include_trace=args.include_trace,
        )
    except (HydraRunnerError, TeacherOraclePilotError, TypeError, ValueError) as exc:
        print(f"eval-peano-hydra: {' '.join(str(exc).split())}", file=sys.stderr)
        return 2
    if args.output is not None:
        try:
            with args.output.open("x", encoding="utf-8", newline="\n") as sink:
                sink.write(rendered)
                sink.write("\n")
        except OSError as exc:
            print(
                f"eval-peano-hydra: cannot create output: "
                f"{' '.join(str(exc).split())}",
                file=sys.stderr,
            )
            return 2
        print(args.output)
    else:
        try:
            print(rendered)
        except BrokenPipeError:  # a downstream consumer deliberately stopped early
            return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
