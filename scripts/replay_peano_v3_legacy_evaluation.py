#!/usr/bin/env python3
"""Kernel-replay the one version-pinned historical Peano v3 evaluation."""

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
    write_replay_attestation,
)
from training.peano_policy.legacy_evaluation_replay import (  # noqa: E402
    EXPECTED_EVALUATION_JOB_ID,
    EXPECTED_SOURCE_COMMIT,
    replay_historical_evaluation_report,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--training-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        attestation = replay_historical_evaluation_report(
            args.report,
            args.training_manifest,
        )
        write_replay_attestation(args.output, attestation)
    except (EvaluationReplayError, FileExistsError, OSError, ValueError) as exc:
        print(f"historical evaluation replay failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "attestation": str(args.output),
                "attestation_sha256": attestation["attestation_sha256"],
                "source_commit": EXPECTED_SOURCE_COMMIT,
                "evaluation_job_id": EXPECTED_EVALUATION_JOB_ID,
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
