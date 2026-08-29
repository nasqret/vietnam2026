#!/usr/bin/env python3
"""Freshly verify the next non-admitting lower-tier proofs and exact audit."""

from __future__ import annotations

import argparse
from pathlib import Path
import resource
import signal

from check_constructive_bottom_layers import authoring_rss_bytes, canonical_report, check_receipt_bytes
from constructive_lower_tier_checkpoints import ROOT, verify_all


RECEIPT = ROOT / "research/arithmetic-library/artifacts/lower-tier-checkpoints-v1.json"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="fresh proof checks and byte-exact audit comparison")
    mode.add_argument("--write", action="store_true", help="create a new checked audit; never overwrite")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    report = verify_all(ordinary_roots=True)
    encoded = canonical_report(report)
    if args.check:
        check_receipt_bytes(RECEIPT, encoded)
    peak = authoring_rss_bytes()
    if args.write:
        RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        with RECEIPT.open("x", encoding="utf-8") as output:
            output.write(encoded)
    for item in report["checkpoints"]:
        print(f"{item['slug']}: {item['new_theorem_count']} genuinely new theorems; complete HA, independent Lean, ordinary roots PASS")
    print(f"Exact AST novelty: all {report['new_theorems']} new statements distinct from all 3392 prior statements and one another.")
    print(f"Peak RSS {peak} bytes; Alpha remains 3222 / Stable 432. No admission or publication.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
