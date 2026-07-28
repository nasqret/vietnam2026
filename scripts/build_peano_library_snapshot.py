#!/usr/bin/env python3
"""Build or verify the deterministic Peano arithmetic-library snapshot.

The snapshot is evidence, not theorem authority.  Every certificate is first
replayed from its tactic script and checked against the closed statement by the
independent Peano kernel.  The generated hashes make review and downstream
corpus pinning precise without teaching the kernel to trust a theorem store.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
from hashlib import sha256
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
DEFAULT_OUTPUT = ROOT / "artifacts" / "peano-library"
THEOREM_SOURCE = PY_ROOT / "peano_lab" / "library" / "theorems.py"

if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.engine.tactics import (  # noqa: E402
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_PROOF_DEPTH,
)
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.proofs import Cut, Proof  # noqa: E402
from peano_lab.library.theorems import MOD5_THEOREMS, THEOREMS, replay  # noqa: E402


CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"


def _digest(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _cut_nodes(proof: Proof) -> int:
    """Count structural ``Cut`` occurrences in a certificate tree."""

    count = 0
    pending = [proof]
    while pending:
        node = pending.pop()
        if type(node) is Cut:
            count += 1
        for field in fields(node):
            child = getattr(node, field.name)
            if isinstance(child, Proof):
                pending.append(child)
    return count


def build_payloads() -> dict[str, str]:
    """Return every generated file as deterministic UTF-8 text."""

    theorem_rows: list[dict[str, object]] = []
    layer_counts = {
        "legacy_core": 0,
        "foundational_extension": 0,
        "published_mod5_unique": 0,
    }
    foundational_names = {
        "eq_symm",
        "eq_trans",
        "succ_congr",
        "zero_or_succ",
        "nonzero_is_succ",
        "add_congr",
        "mul_congr",
        "add_right_cancel",
        "add_left_cancel",
        "zero_le",
        "le_succ_self",
        "le_zero",
        "one_le_of_ne_zero",
        "ne_zero_of_one_le",
        "le_add_left",
        "le_add_right",
        "add_le_add_right",
        "add_le_add_left",
        "succ_le_succ",
        "le_of_succ_le_succ",
        "le_succ",
        "lt_to_le",
        "add_le_cancel_right",
        "lt_irrefl_expanded",
        "le_eq_or_lt",
        "lt_of_lt_of_le",
        "lt_of_le_of_lt",
        "lt_trans",
        "le_or_lt",
        "lt_trichotomy",
        "lt_not_le",
        "le_not_lt",
        "lt_not_eq_add_middle",
        "mul_le_mul_left",
        "mul_le_mul_right",
        "mul_lt_mul_succ_left_nonzero",
        "division_remainder_succ",
        "division_remainder_exists",
        "remainder_bound_step",
        "division_block_upper",
        "positive_quotient_gap_impossible",
        "remainder_unique_same_quotient",
        "division_remainder_unique",
        "zero_remainder_implies_multiple",
        "multiple_has_zero_remainder",
        "add_eq_zero_left",
        "add_eq_zero_components",
        "mul_eq_one_components",
        "mul_ne_zero",
        "mul_left_cancel_nonzero",
        "mul_right_cancel_nonzero",
        "two_large_factors_impossible",
        "prime_two",
        "multiple_zero",
        "one_multiple",
        "multiple_refl",
        "multiple_add",
        "multiple_mul_right",
        "multiple_mul_left",
        "multiple_trans",
        "divisor_le_nonzero",
        "divisor_one",
        "multiple_antisymm",
        "factor_difference",
        "divides_remainder",
        "divides_linear_step",
        "not_multiple_pointwise",
        "not_multiple_from_pointwise",
        "is_gcd_zero_right",
        "is_gcd_symm",
        "is_gcd_dvd_left",
        "is_gcd_dvd_right",
        "is_gcd_greatest",
        "is_gcd_of_dvd",
        "is_gcd_unique",
        "is_gcd_euclid_forward",
        "is_gcd_euclid_backward",
        "coprime_symm",
        "coprime_one_right",
        "coprime_one_left",
        "coprime_to_is_gcd_one",
        "is_gcd_one_to_coprime",
        "mod_eq_refl",
        "mod_eq_symm",
        "dvd_to_mod_zero",
        "add_residue",
        "add_residue_lift",
        "square_decomp",
        "square_residue_lift",
        "square_residue_witness",
    }
    published_mod5_unique_names = {
        spec.name for spec in MOD5_THEOREMS
    } - foundational_names

    for index, spec in enumerate(THEOREMS):
        checked = replay(spec.name)
        if not check((), checked.certificate, checked.formula):
            raise RuntimeError(f"independent kernel rejected {spec.name!r}")
        nodes, depth = proof_metrics(checked.certificate)
        cut_nodes = _cut_nodes(checked.certificate)
        if nodes > MAX_USE_CERTIFICATE_NODES or depth > MAX_USE_PROOF_DEPTH:
            raise RuntimeError(
                f"{spec.name!r} exceeds live-use bounds: {nodes} nodes, depth {depth}"
            )
        if spec.name in foundational_names:
            layer = "foundational_extension"
        elif spec.name in published_mod5_unique_names:
            layer = "published_mod5_unique"
        else:
            layer = "legacy_core"
        layer_counts[layer] += 1
        script_text = "\n".join(spec.script) + "\n"
        certificate_repr = repr(checked.certificate)
        theorem_rows.append(
            {
                "certificate_representation": CERTIFICATE_REPRESENTATION,
                "certificate_sha256": _digest(certificate_repr),
                "cut_nodes": cut_nodes,
                "dependencies": list(spec.dependencies),
                "index": index,
                "layer": layer,
                "name": spec.name,
                "proof_depth": depth,
                "proof_nodes": nodes,
                "script": list(spec.script),
                "script_sha256": _digest(script_text),
                "statement": spec.statement,
                "statement_sha256": _digest(spec.statement),
                "summary": spec.summary,
            }
        )

    root_material = json.dumps(
        theorem_rows, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    )
    ordered_root = _digest(root_material)
    catalog = {
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "certificate_policy": (
            "Each closed certificate was reconstructed from its script, packages "
            "each declared dependency as a self-contained checked Cut node, and "
            "passed the independent kernel from the empty context. Cut nodes contain "
            "their proposition and both proof branches; they do not refer to an "
            "external theorem environment, theorem name, or certificate hash."
        ),
        "ordered_root_sha256": ordered_root,
        "schema": "peano-library-snapshot-v2",
        "theorem_count": len(theorem_rows),
        "theorem_source": "peano-lab/py/peano_lab/library/theorems.py",
        "theorem_source_sha256": _digest(THEOREM_SOURCE.read_bytes()),
        "theorems": theorem_rows,
    }

    metrics = {
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "live_use_limits": {
            "proof_depth": MAX_USE_PROOF_DEPTH,
            "proof_nodes": MAX_USE_CERTIFICATE_NODES,
        },
        "maximum_cut_nodes": max(row["cut_nodes"] for row in theorem_rows),
        "maximum_proof_depth": max(row["proof_depth"] for row in theorem_rows),
        "maximum_proof_nodes": max(row["proof_nodes"] for row in theorem_rows),
        "ordered_root_sha256": ordered_root,
        "schema": "peano-library-metrics-v2",
        "theorem_count": len(theorem_rows),
        "theorems_with_cut_nodes": sum(
            row["cut_nodes"] > 0 for row in theorem_rows
        ),
        "theorems_by_layer": layer_counts,
        "total_cut_nodes": sum(row["cut_nodes"] for row in theorem_rows),
        "total_proof_nodes": sum(row["proof_nodes"] for row in theorem_rows),
    }

    graph_lines = [
        "%% Generated by scripts/build_peano_library_snapshot.py; do not edit.",
        "flowchart TD",
    ]
    for row in theorem_rows:
        name = str(row["name"])
        graph_lines.append(f"  {name}[{name}]")
    for row in theorem_rows:
        name = str(row["name"])
        for dependency in row["dependencies"]:
            graph_lines.append(f"  {dependency} --> {name}")

    return {
        "catalog-v1.json": _canonical_json(catalog),
        "dependency-graph.mmd": "\n".join(graph_lines) + "\n",
        "metrics.json": _canonical_json(metrics),
    }


def _check_or_write(output: Path, payloads: dict[str, str], check_only: bool) -> None:
    problems: list[str] = []
    if check_only:
        for name, expected in payloads.items():
            path = output / name
            if not path.is_file():
                problems.append(f"missing {path.relative_to(ROOT)}")
            elif path.read_text(encoding="utf-8") != expected:
                problems.append(f"stale {path.relative_to(ROOT)}")
        if problems:
            raise SystemExit("\n".join(problems))
        return

    output.mkdir(parents=True, exist_ok=True)
    for name, value in payloads.items():
        (output / name).write_text(value, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if committed files drift")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    payloads = build_payloads()
    _check_or_write(args.output.resolve(), payloads, args.check)
    action = "verified" if args.check else "wrote"
    print(f"{action} {len(THEOREMS)} checked theorems in {args.output}")


if __name__ == "__main__":
    main()
