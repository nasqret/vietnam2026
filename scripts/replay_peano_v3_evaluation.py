#!/usr/bin/env python3
"""Independently kernel-replay a frozen Peano model-v3 evaluation report."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

from training.peano_policy.evaluation_replay import (  # noqa: E402
    EvaluationReplayError,
    replay_evaluation_report,
    write_replay_attestation,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--source-commit",
        required=True,
        help="externally expected clean 40-hex source commit used by evaluation",
    )
    parser.add_argument(
        "--evaluation-job-id",
        required=True,
        help="externally expected decimal Slurm job id that produced the report",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        attestation = replay_evaluation_report(
            args.report,
            expected_source_commit=args.source_commit,
            expected_evaluation_job_id=args.evaluation_job_id,
        )
        write_replay_attestation(args.output, attestation)
    except (EvaluationReplayError, FileExistsError, OSError, ValueError) as exc:
        print(f"evaluation replay failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "attestation": str(args.output),
                "attestation_sha256": attestation["attestation_sha256"],
                "claimed_proofs": attestation["summary"]["claimed_proofs"],
                "kernel_replayed_proofs": attestation["summary"][
                    "kernel_replayed_proofs"
                ],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
