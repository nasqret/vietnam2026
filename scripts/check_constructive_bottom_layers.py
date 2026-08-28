#!/usr/bin/env python3
"""Verify local bottom-layer proofs; optionally compare/write their audit record."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import resource
import signal
import sys

from constructive_bottom_layer_checkpoints import ROOT, verify_all


RECEIPT = ROOT / "research/arithmetic-library/artifacts/bottom-layer-checkpoints-v2.json"


def canonical_report(report) -> str:
    return json.dumps(report, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n"


def check_receipt_bytes(path: Path, encoded: str) -> None:
    """Bound an untrusted audit sidecar by the freshly computed exact length."""
    expected = encoded.encode("utf-8")
    if not path.is_file() or path.is_symlink() or path.stat().st_size != len(expected):
        raise RuntimeError("the local checkpoint audit record is missing or stale")
    with path.open("rb") as handle:
        actual = handle.read(len(expected) + 1)
    if actual != expected:
        raise RuntimeError("the local checkpoint audit record is missing or stale")


def authoring_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    # ru_maxrss is bytes on macOS and KiB on Linux; the ceiling is unchanged.
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    if peak_bytes > 1536 * 1024 * 1024:
        raise RuntimeError("the original 1536 MiB authoring RSS ceiling was exceeded")
    return peak_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="freshly verify proofs and compare the deterministic audit record")
    mode.add_argument("--write", action="store_true", help="freshly verify proofs and create a new non-admitting audit record; never overwrite")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    report = verify_all(ordinary_roots=True)
    encoded = canonical_report(report)
    if args.check:
        check_receipt_bytes(RECEIPT, encoded)
    # An over-budget proof/serialization run must not leave a success record.
    authoring_rss_bytes()
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        with RECEIPT.open("x", encoding="utf-8") as output:
            output.write(encoded)
    peak_bytes = authoring_rss_bytes()
    for row in report["checkpoints"]:
        print(f"{row['slug']}: {row['frontier_count']} new theorems; complete HA + independent Lean + ordinary roots PASS")
    print(f"{report['new_theorems']} local theorems; Alpha remains 3222, Stable 432; no admission or deployment")
    print(f"Authoring RSS ceiling PASS: {peak_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
