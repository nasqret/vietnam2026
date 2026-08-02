#!/usr/bin/env python3
"""Cross-bind the byte-pinned Peano v3 four-goal launch-smoke records."""

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
    write_replay_attestation,
)
from training.peano_policy.paired_evaluation_attestation import (  # noqa: E402
    PairedEvaluationAttestationError,
    attest_paired_evaluation,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trained-attestation", type=Path, required=True)
    parser.add_argument("--pretrained-attestation", type=Path, required=True)
    parser.add_argument("--trained-report", type=Path, required=True)
    parser.add_argument("--pretrained-report", type=Path, required=True)
    parser.add_argument("--training-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        attestation = attest_paired_evaluation(
            trained_attestation_path=args.trained_attestation,
            pretrained_attestation_path=args.pretrained_attestation,
            trained_report_path=args.trained_report,
            pretrained_report_path=args.pretrained_report,
            training_manifest_path=args.training_manifest,
        )
        write_replay_attestation(args.output, attestation)
    except (
        PairedEvaluationAttestationError,
        FileExistsError,
        OSError,
        ValueError,
    ) as exc:
        print(f"paired evaluation attestation failed: {exc}", file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "attestation": str(args.output),
                "attestation_sha256": attestation["attestation_sha256"],
                "result": attestation["result"],
                "trained_solved": attestation["observed_result"]["trained"][
                    "solved"
                ],
                "pretrained_solved": attestation["observed_result"][
                    "pretrained_comparison"
                ]["solved"],
                "goals": attestation["observed_result"]["denominator"],
                "k": attestation["observed_result"]["k"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
