#!/usr/bin/env python3
"""Author complete original-HA bundles for the next non-admitting tranche.

This exporter grants no Lean/admission status. The separately frozen
checkpoint registry subsequently verifies exact artifacts with both checkers.
"""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path
import resource
import signal

from constructive_lower_continuation_support import previous_seed_paths, select_support, statement_duplicates
from check_constructive_bottom_layers import authoring_rss_bytes
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


AUTHORING_GROUPS = (
    ("divisor-involutions", ("divisor_involution_candidate",)),
    ("mobius-divisor-cancellation", ("mobius_divisor_cancellation_candidate",)),
    ("rectangular-sums", ("signed_rectangular_slice_candidate", "signed_rectangular_sums_candidate")),
    ("polynomial-products", ("prime_field_polynomial_convolution_candidate", "prime_field_polynomial_degree_candidate")),
)


def authoring_rows():
    return tuple(row for _, modules in AUTHORING_GROUPS for module in modules
                 for row in getattr(import_module("peano_lab.library." + module), "make_" + module + "_theorems")(TheoremSpec))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--family", choices=[slug for slug, _ in AUTHORING_GROUPS], required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seed", type=Path, action="append", default=[])
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    if args.output.exists() or args.output.is_symlink():
        parser.error("refusing to overwrite an existing artifact")
    modules = dict(AUTHORING_GROUPS)[args.family]
    owned = tuple(row.name for module in modules
                  for row in getattr(import_module("peano_lab.library." + module), "make_" + module + "_theorems")(TheoremSpec))
    rows = authoring_rows()
    duplicates = statement_duplicates(rows)
    if duplicates:
        raise ValueError(f"authoring rows duplicate existing exact statements: {duplicates!r}")
    selected = select_support(rows, owned)
    closure.export_bottom_layer_bundle(selected.frontier, args.output,
        seed_bundles=(*previous_seed_paths(), *args.seed), batch_size=1)
    peak = authoring_rss_bytes()
    print(f"Exported {len(selected.owned)} new owned rows to {args.output}.")
    print(f"Original HA authoring only; no Alpha/Stable admission or Lean claim; peak RSS {peak} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
