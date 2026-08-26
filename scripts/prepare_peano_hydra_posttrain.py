#!/usr/bin/env python3
"""Replay checked Alpha Hydra evidence into a benchmark-safe Qwen SFT handoff.

The frozen historical benchmark, aliases, checked descendants, and every
contaminated theorem lineage stay outside both training and training-time
validation.  This command never initializes CUDA, trains weights, starts a
remote job, modifies the mathematical DAGs, or deploys public content.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
for _import_root in (
    REPOSITORY_ROOT,
    REPOSITORY_ROOT / "peano-lab" / "py",
    REPOSITORY_ROOT / "scripts",
):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from training.peano_hydra.posttrain import (  # noqa: E402
    HydraPosttrainError,
    prepare_posttraining,
    publish_preparation,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=REPOSITORY_ROOT / "_deploy" / "hydra",
        metavar="PATH",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "_deploy" / "hydra-posttrain",
        metavar="PATH",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="independently replay and prepare the complete handoff without writing files",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        prepared = prepare_posttraining(args.source_dir, args.output_dir)
        destination = None if args.check else publish_preparation(prepared)
    except (HydraPosttrainError, OSError, TypeError, ValueError) as error:
        print(f"prepare-peano-hydra-posttrain: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "version": prepared.source.epoch.version,
                "epoch_sha256": prepared.source.epoch.epoch_sha256,
                "training_rows": len(prepared.train_rows),
                "development_rows": len(prepared.development_rows),
                "quarantined_rows": prepared.manifest["held_out"]["quarantine_rows"],
                "checked_catalog_routes": prepared.manifest["source"][
                    "independently_replayed_catalog_routes"
                ],
                "model_trained": False,
                "research_claim_eligible": False,
                "output_dir": None if destination is None else str(destination),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
