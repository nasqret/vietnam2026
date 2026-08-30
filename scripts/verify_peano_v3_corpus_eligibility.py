#!/usr/bin/env python3
"""Verify that the current source may reuse one immutable model-v3 corpus.

This is the deliberately cheap successor to dataset attestation.  The original
preparation job independently replayed every proof before the corpus was
sealed.  A later source revision must not repeat that multi-hour replay: it
verifies the complete seal and proves that its current compiler, kernel,
prompt, held-out contract, and library authority still match the sealed
manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.config import ExperimentConfig, load_config  # noqa: E402
from training.peano_policy.corpus_eligibility import (  # noqa: E402
    CorpusEligibilityError,
    verify_sealed_corpus_eligibility,
)
from training.peano_policy.manifest import sha256_file, write_manifest  # noqa: E402
from training.peano_policy.runtime import slurm_job_identity  # noqa: E402


REPORT_FORMAT = "peano-policy-wmi-v3-sealed-corpus-eligibility"
REPORT_VERSION = 1


def _repo_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else REPOSITORY_ROOT / path


def verify_config(config: ExperimentConfig) -> dict[str, object]:
    """Return job-bound evidence for one successful compatibility check."""

    curriculum = config.curriculum
    if curriculum is None:
        raise ValueError("sealed-corpus eligibility requires a model-v3 curriculum")
    eligibility = verify_sealed_corpus_eligibility(
        _repo_path(curriculum.corpus_seal_path),
        configured_train_path=_repo_path(config.data.train_path),
        configured_eval_path=_repo_path(config.data.eval_path),
        historical_source_commit=curriculum.corpus_source_commit,
        historical_prepare_job_id=curriculum.corpus_prepare_job_id,
        sealed_content_sha256=curriculum.corpus_content_sha256,
    )
    return {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "config": {
            "path": str(config.path),
            "sha256": sha256_file(config.path),
        },
        "sealed_corpus_eligibility": eligibility.record,
        "job": slurm_job_identity(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        report = verify_config(load_config(args.config))
        if args.output is None:
            print(json.dumps(report, ensure_ascii=False, sort_keys=True))
        else:
            if args.output.exists():
                raise FileExistsError(
                    f"refusing to replace eligibility report: {args.output}"
                )
            write_manifest(args.output, report)
            print(json.dumps({"report": str(args.output)}, sort_keys=True))
    except (CorpusEligibilityError, FileExistsError, OSError, ValueError) as exc:
        print(f"Peano v3 sealed-corpus eligibility failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
