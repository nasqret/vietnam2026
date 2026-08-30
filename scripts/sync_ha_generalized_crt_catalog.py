#!/usr/bin/env python3
"""Synchronize admitted HA generalized-CRT theorems into the catalog.

The catalog is documentation and provenance, never theorem authority.  This
script copies exact statements, dependency lists, and summaries only from the
reviewed public M5 tuple.  It refuses to replace a differing existing record;
the independent arithmetic knowledge-base validator remains the final
cross-check against the production parser and theorem registry.
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
    HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS,
)


DOMAIN = "congruence"


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
        for spec in HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS
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
                f"existing generalized-CRT catalog record {name!r} differs; "
                "review it manually"
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
            print("HA generalized-CRT catalog is stale", file=sys.stderr)
            return 1
        print(
            "verified "
            f"{len(_records())} HA generalized-CRT catalog records"
        )
        return 0
    CATALOG.write_text(rendered, encoding="utf-8")
    print(
        "synchronized "
        f"{len(_records())} HA generalized-CRT catalog records"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
