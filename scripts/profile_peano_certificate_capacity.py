#!/usr/bin/env python3
"""Profile structural cost and in-memory sharing of checked PA certificates.

This is a measurement tool, not an admission path.  It replays ordinary
library entries, asks the independent kernel to check them through the normal
library machinery, and reports both the historical tree metric and the number
of distinct in-memory proof objects.  The distinction matters for the
quadratic-reciprocity campaign: separate Cut branches may share Python objects
even though the conservative live-tree budget counts every incoming edge.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
import json
from pathlib import Path
import resource
import sys
from time import perf_counter


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.engine.state import proof_identity_metrics, proof_metrics  # noqa: E402
from peano_lab.kernel.proofs import Cut, Proof  # noqa: E402
from peano_lab.library.theorems import get, replay  # noqa: E402


DEFAULT_THEOREMS = (
    "division_remainder_exists",
    "euclid_prime_dvd_product",
    "beta_product_exists_unique",
    "prime_factorization_existence",
    "fundamental_theorem_of_arithmetic",
)


def _dag_metrics(proof: Proof) -> dict[str, int]:
    """Count distinct proof objects and repeated references iteratively."""

    pending = [proof]
    seen: set[int] = set()
    cut_nodes = 0
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        if type(node) is Cut:
            cut_nodes += 1
        children = [
            getattr(node, field.name)
            for field in fields(node)
            if isinstance(getattr(node, field.name), Proof)
        ]
        pending.extend(children)
    distinct, edges, reused = proof_identity_metrics(proof)
    return {
        "distinct_proof_objects": distinct,
        "distinct_cut_objects": cut_nodes,
        "proof_edges": edges,
        "reused_references": reused,
    }


def profile(names: tuple[str, ...]) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    started = perf_counter()
    previous_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    for name in names:
        if get(name) is None:
            raise ValueError(f"unknown checked theorem {name!r}")
        theorem_started = perf_counter()
        theorem = replay(name)
        structural_nodes, structural_depth = proof_metrics(theorem.certificate)
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        dag = _dag_metrics(theorem.certificate)
        rows.append(
            {
                "name": name,
                "structural_nodes": structural_nodes,
                "structural_depth": structural_depth,
                **dag,
                "structural_to_distinct_ratio": round(
                    structural_nodes / dag["distinct_proof_objects"], 3
                ),
                "seconds": round(perf_counter() - theorem_started, 3),
                "process_maxrss": rss,
                "maxrss_growth": max(0, rss - previous_rss),
            }
        )
        previous_rss = rss
    return {
        "format": "peano-certificate-capacity-profile",
        "version": 1,
        "platform_maxrss_units": (
            "bytes on macOS; KiB on most other Unix platforms"
        ),
        "elapsed_seconds": round(perf_counter() - started, 3),
        "theorems": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "theorem",
        nargs="*",
        default=DEFAULT_THEOREMS,
        help="checked theorem names (defaults to representative milestones)",
    )
    args = parser.parse_args()
    try:
        payload = profile(tuple(args.theorem))
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
