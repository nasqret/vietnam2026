#!/usr/bin/env python3
"""Prove that adapter recovery can publish safely on a target filesystem."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.recovery import (  # noqa: E402
    RecoverySnapshotError,
    run_recovery_publication_preflight,
    verify_recovery_publication_preflight,
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    run = subparsers.add_parser(
        "run",
        help="publish a retained probe and exclusively create its report",
    )
    run.add_argument(
        "--probe-root",
        type=Path,
        required=True,
        help="existing directory on the exact filesystem to exercise",
    )
    run.add_argument(
        "--report",
        type=Path,
        required=True,
        help="absent output pathname for the canonical report",
    )
    verify = subparsers.add_parser(
        "verify",
        help="recheck canonical report bytes and the retained live probe",
    )
    verify.add_argument("--report", type=Path, required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "run":
            record = run_recovery_publication_preflight(
                args.probe_root,
                report_path=args.report,
            )
            report = Path(record["report"]["path"])
        else:
            record = verify_recovery_publication_preflight(args.report)
            report = Path(record["report"]["path"])
        publication = record["publication"]
        print(
            json.dumps(
                {
                    "report": str(report),
                    "report_sha256": _sha256(report),
                    "retained_probe": publication["probe_parent"]["path"],
                    "publication_profile": record["publication_profile"],
                    "status": "passed",
                },
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
    except (OSError, RecoverySnapshotError, TypeError, ValueError) as exc:
        print(f"Recovery publication preflight failed: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
