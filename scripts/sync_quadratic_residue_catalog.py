#!/usr/bin/env python3
"""Synchronize checked QR-campaign theorem data into the research catalog.

The catalog remains documentation and provenance, never theorem authority.
This script copies exact statements and dependency lists only from runtime
entries that are explicitly enrolled in a reviewed campaign tuple. It refuses
to overwrite an existing record; the independent knowledge-base validator
still compares every checked claim with the production parser and library.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
CATALOG = ROOT / "research" / "arithmetic-library" / "catalog.json"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.library.theorems import (  # noqa: E402
    FINITE_BITCOUNT_THEOREMS,
    FINITE_CONGRUENCE_THEOREMS,
    FINITE_FACTORIAL_THEOREMS,
    FINITE_FOLD_THEOREMS,
    FINITE_PERMUTATION_THEOREMS,
    FINITE_PRODUCT_PERMUTATION_THEOREMS,
    FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS,
    FINITE_RANGE_THEOREMS,
    FINITE_SUM_THEOREMS,
    GAUSS_SIGN_BRIDGE_THEOREMS,
    GAUSS_HALF_RANGE_THEOREMS,
    PARITY_THEOREMS,
    POWER_ALGEBRA_THEOREMS,
    POWER_CONGRUENCE_THEOREMS,
    QR_PRIME_UNIT_THEOREMS,
    QR_BOUNDED_UNIT_THEOREMS,
    QR_SMALL_MODULI_THEOREMS,
    QUADRATIC_RESIDUE_THEOREMS,
)


DOMAIN = "quadratic_residues"


def _title(name: str) -> str:
    return name.replace("_", " ").capitalize()


def _records() -> list[dict[str, object]]:
    return [
        {
            "id": spec.name,
            "title": _title(spec.name),
            "domain": DOMAIN,
            "status": "checked_m20",
            "dependencies": list(spec.dependencies),
            "sources": ["peano_lab_library"],
            "summary": spec.summary,
            "peano": {
                "statement": spec.statement,
                "existing_name": spec.name,
            },
            "blocker": None,
        }
        for spec in (
            PARITY_THEOREMS
            + QUADRATIC_RESIDUE_THEOREMS
            + FINITE_FOLD_THEOREMS
            + FINITE_RANGE_THEOREMS
            + FINITE_SUM_THEOREMS
            + FINITE_CONGRUENCE_THEOREMS
            + FINITE_BITCOUNT_THEOREMS
            + FINITE_FACTORIAL_THEOREMS
            + POWER_CONGRUENCE_THEOREMS
            + QR_PRIME_UNIT_THEOREMS
            + QR_SMALL_MODULI_THEOREMS
            + POWER_ALGEBRA_THEOREMS
            + GAUSS_SIGN_BRIDGE_THEOREMS
            + GAUSS_HALF_RANGE_THEOREMS
            + FINITE_PERMUTATION_THEOREMS
            + FINITE_PRODUCT_PERMUTATION_THEOREMS
            + FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS
            + QR_BOUNDED_UNIT_THEOREMS
        )
    ]


def _expected(catalog: dict[str, object]) -> dict[str, object]:
    result = json.loads(json.dumps(catalog))
    domain_order = result["domain_order"]
    lemmas = result["lemmas"]
    if not isinstance(domain_order, list) or not isinstance(lemmas, list):
        raise ValueError("catalog domain_order and lemmas must be lists")
    if DOMAIN not in domain_order:
        domain_order.append(DOMAIN)
    for record in _records():
        name = record["id"]
        matching = next(
            (
                row
                for row in lemmas
                if isinstance(row, dict) and row.get("id") == name
            ),
            None,
        )
        if matching is None:
            lemmas.append(record)
        elif matching != record:
            raise ValueError(
                f"existing campaign catalog record {name!r} differs; review it manually"
            )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    try:
        expected = _expected(catalog)
    except ValueError as exc:
        parser.error(str(exc))
    rendered = json.dumps(expected, ensure_ascii=False, indent=2) + "\n"
    if args.check:
        if CATALOG.read_text(encoding="utf-8") != rendered:
            print("quadratic-residue catalog is stale", file=sys.stderr)
            return 1
        print(f"verified {len(_records())} quadratic-residue catalog records")
        return 0
    CATALOG.write_text(rendered, encoding="utf-8")
    print(f"synchronized {len(_records())} quadratic-residue catalog records")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
