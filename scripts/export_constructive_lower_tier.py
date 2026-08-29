#!/usr/bin/env python3
"""Construct a complete original-HA checkpoint from ordinary authoring syntax.

This authoring command does not trust cached success records, grant admission,
or claim independent Lean acceptance.  Use check_constructive_lower_tier.py
after freezing the source/specification/artifact pins for that separate gate.
"""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path
import resource
import signal

from check_constructive_bottom_layers import authoring_rss_bytes
from constructive_lower_tier_support import previous_seed_paths, select_support
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


AUTHORING_GROUPS = (
    ("divisor-sums", ("arithmetic_table_extension_candidate", "mobius_table_candidate", "divisor_mask_candidate")),
    ("signed-weighted-sums", ("signed_table_operations_candidate", "signed_sum_linearity_candidate", "signed_weighted_sum_candidate")),
    ("prime-field-polynomials", ("prime_field_polynomial_candidate", "prime_field_polynomial_evaluation_candidate")),
)


def authoring_rows() -> tuple[tuple[str, tuple[TheoremSpec, ...]], ...]:
    return tuple((slug, tuple(row for name in modules
                             for row in getattr(import_module("peano_lab.library." + name), "make_" + name + "_theorems")(TheoremSpec)))
                 for slug, modules in AUTHORING_GROUPS)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", required=True, choices=[slug for slug, _ in AUTHORING_GROUPS])
    parser.add_argument("--output", required=True, type=Path, help="new destination; existing files are never overwritten")
    parser.add_argument("--seed", action="append", type=Path, default=[], help="additional actual proof data, freshly checked in full before reuse")
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError("checkpoint output already exists; no file was overwritten")
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    groups = authoring_rows()
    rows = tuple(row for _, group in groups for row in group)
    owned = next(group for slug, group in groups if slug == args.family)
    selection = select_support(rows, tuple(row.name for row in owned))
    print(f"{args.family}: {len(owned)} owned, {len(selection.published_support)} prior research support, {len(selection.current_support)} current cross-track support; no admission.", flush=True)
    closure.export_bottom_layer_bundle(selection.frontier, output=args.output,
                                       seed_bundles=previous_seed_paths() + tuple(args.seed))
    print(f"Original HA checkpoint constructed; peak RSS {authoring_rss_bytes()} bytes. Independent Lean remains a separate required check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
