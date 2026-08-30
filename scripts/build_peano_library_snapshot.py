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

from peano_lab.engine.state import proof_identity_metrics, proof_metrics  # noqa: E402
from peano_lab.engine.tactics import (  # noqa: E402
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_CERTIFICATE_OBJECTS,
    MAX_USE_PROOF_DEPTH,
)
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.proofs import Cut, Proof  # noqa: E402
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
    HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS,
    HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS,
    HA_NUMBER_THEORY_TRANCHE01_THEOREMS,
    MOD5_THEOREMS,
    PARITY_THEOREMS,
    POWER_ALGEBRA_THEOREMS,
    POWER_CONGRUENCE_THEOREMS,
    QR_PRIME_UNIT_THEOREMS,
    QR_BOUNDED_UNIT_THEOREMS,
    QR_SMALL_MODULI_THEOREMS,
    QUADRATIC_RESIDUE_THEOREMS,
    THEOREMS,
    replay,
)


CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"
THEOREM_SOURCES = (
    THEOREM_SOURCE,
    PY_ROOT / "peano_lab" / "library" / "parity.py",
    PY_ROOT / "peano_lab" / "library" / "quadratic_residue_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_fold_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_range_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_sum_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_congruence_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_bitcount_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_factorial_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "power_congruence_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "power_algebra_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "gauss_sign_bridge.py",
    PY_ROOT / "peano_lab" / "library" / "gauss_half_range.py",
    PY_ROOT / "peano_lab" / "library" / "finite_permutation_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_product_permutation_theorems.py",
    PY_ROOT / "peano_lab" / "library" / "finite_product_reindex_support.py",
    PY_ROOT / "peano_lab" / "library" / "qr_bounded_units.py",
    PY_ROOT / "peano_lab" / "library" / "qr_prime_units.py",
    PY_ROOT / "peano_lab" / "library" / "qr_small_moduli.py",
    PY_ROOT / "peano_lab" / "library" / "ha_canonical_remainder_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_canonical_congruence_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "wilson_inverse_point_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_modular_inverse_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_relational_lcm_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_lcm_totality_bridge_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_congruence_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_sufficiency_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_zero_boundary_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_classification_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_canonical_boundary_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_decision_candidate.py",
    PY_ROOT / "peano_lab" / "library" / "ha_generalized_crt_total_decision_candidate.py",
)


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
        "quadratic_residue_foundation": 0,
        "ha_number_theory_campaign": 0,
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
        "gcd_exists_up_to",
        "gcd_exists_relational",
        "coprime_symm",
        "coprime_one_right",
        "coprime_one_left",
        "coprime_to_is_gcd_one",
        "is_gcd_one_to_coprime",
        "add_permute_outer",
        "balanced_bezout_euclid_step",
        "gcd_balanced_bezout_exists_up_to",
        "gcd_balanced_bezout_exists",
        "balanced_combination_scale_right",
        "common_divisor_divides_balanced_result",
        "coprime_balanced_bezout",
        "gauss_coprime_cancel",
        "eq_decidable",
        "multiple_decidable_nonzero",
        "multiple_decidable",
        "factor_property_succ",
        "factor_search_up_to",
        "prime_or_composite",
        "prime_nonzero",
        "prime_decidable",
        "factor_nonzero_left",
        "proper_factor_lt",
        "prime_divisor_exists_up_to",
        "prime_divisor_exists",
        "prime_divisor_eq_one_or_self",
        "euclid_prime_dvd_product",
        "mod_eq_refl",
        "mod_eq_symm",
        "mod_eq_trans",
        "mod_eq_add",
        "mod_eq_mul_right",
        "mod_eq_mul_left",
        "mod_eq_mul",
        "remainder_decomposition_to_mod_eq",
        "mod_eq_bounded_unique",
        "mod_eq_to_remainder_decomposition",
        "beta_modulus_nonzero",
        "beta_at_self_of_bound",
        "beta_at_exists",
        "beta_at_unique",
        "beta_at_exists_unique",
        "beta_at_to_mod_eq",
        "beta_at_of_mod_eq_bound",
        "dvd_to_mod_zero",
        "add_residue",
        "add_residue_lift",
        "square_decomp",
        "square_residue_lift",
        "square_residue_witness",
        "bezout_mod_left",
        "bezout_mod_right",
        "mod_eq_predecessor_cancel",
        "binary_crt",
        "binary_crt_remainders",
        "binary_crt_beta_pair",
        "beta_modulus_coprime_base",
        "common_divisor_beta_moduli_divides_gap_times_c",
        "beta_moduli_coprime_of_gap_dvd",
        "binary_crt_beta_pair_of_gap_dvd",
        "bounded_common_multiple_step",
        "bounded_common_multiple_exists",
        "beta_moduli_coprime_of_lt_bounded_common_multiple",
        "beta_moduli_pairwise_coprime_bounded",
        "bounded_beta_moduli_pairwise_coprime_exists",
        "coprime_mul_left",
        "coprime_mul_right",
        "mod_eq_of_mod_eq_multiple",
        "binary_crt_fold_step",
        "right_factor_divides_product",
        "beta_accumulated_product_step",
        "beta_crt_prefix_congruence_step",
        "beta_crt_prefix_invariant_step",
        "bounded_beta_crt_prefix_invariant",
        "bounded_beta_crt_for_existing_code",
        "prime_unbounded",
        "beta_value_le_code",
        "base_le_beta_modulus",
        "le_scaled_nonzero",
        "scaled_bounded_common_multiple",
        "beta_value_lt_scaled_base",
        "new_value_lt_scaled_base",
        "beta_exclusive_accumulated_product_step",
        "beta_exclusive_recode_congruence_step",
        "beta_exclusive_recode_invariant_step",
        "bounded_beta_exclusive_recode_invariant",
        "beta_prefix_extend",
        "beta_prefix_product_trace_exists",
        "beta_product_exists",
        "beta_product_functional",
        "beta_product_exists_unique",
        "beta_product_zero",
        "beta_product_succ_decompose",
        "beta_product_succ_append",
    "beta_product_transport_prefix",
    "beta_factor_prefix_product_append",
    "all_prime_empty",
    "all_prime_succ_intro",
    "all_prime_succ_elim_prefix",
    "all_prime_succ_elim_last",
    "all_prime_transport",
    "sorted_empty",
    "sorted_singleton",
    "sorted_succ_intro",
    "sorted_succ_elim_prefix",
    "sorted_succ_elim_last",
    "sorted_transport",
    "beta_prefix_extend_all_prime",
    "beta_prefix_extend_sorted_singleton",
    "beta_prefix_extend_sorted_succ",
    "beta_canonical_append_empty",
    "beta_canonical_append_succ",
    "prime_divides_decidable",
    "greatest_prime_divisor_search",
    "greatest_prime_divisor_exists",
    "greatest_prime_divisor_quotient_bound",
    "greatest_prime_divisor_descent",
    "beta_factor_divides_product",
    "beta_canonical_append_general",
    "beta_canonical_last_factor_bound",
    "prime_factorization_exists_up_to",
    "prime_factorization_existence",
    "beta_prime_divisor_product_member",
    "beta_sorted_factor_le_last",
    "beta_nonempty_all_prime_product_ne_one",
    "beta_all_prime_product_one_iff_length_zero",
    "beta_canonical_last_factors_equal",
    "beta_canonical_product_cancel_last",
    "prime_factorization_uniqueness_by_length",
    "prime_factorization_uniqueness",
    "fundamental_theorem_of_arithmetic",
    "prime_three",
    "two_prime_product_uniqueness",
    }
    published_mod5_unique_names = {
        spec.name for spec in MOD5_THEOREMS
    } - foundational_names
    quadratic_residue_names = {
        spec.name
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
    }
    ha_number_theory_campaign_names = {
        spec.name
        for spec in (
            HA_NUMBER_THEORY_TRANCHE01_THEOREMS
            + HA_NUMBER_THEORY_K4_GCD_LCM_THEOREMS
            + HA_NUMBER_THEORY_M5_GENERALIZED_CRT_THEOREMS
        )
    }

    for index, spec in enumerate(THEOREMS):
        checked = replay(spec.name)
        if not check((), checked.certificate, checked.formula):
            raise RuntimeError(f"independent kernel rejected {spec.name!r}")
        nodes, depth = proof_metrics(checked.certificate)
        distinct_objects, proof_edges, reused_references = proof_identity_metrics(
            checked.certificate
        )
        cut_nodes = _cut_nodes(checked.certificate)
        if (
            nodes > MAX_USE_CERTIFICATE_NODES
            or distinct_objects > MAX_USE_CERTIFICATE_OBJECTS
            or depth > MAX_USE_PROOF_DEPTH
        ):
            raise RuntimeError(
                f"{spec.name!r} exceeds live-use bounds: {nodes} occurrences, "
                f"{distinct_objects} objects, depth {depth}"
            )
        if spec.name in foundational_names:
            layer = "foundational_extension"
        elif spec.name in published_mod5_unique_names:
            layer = "published_mod5_unique"
        elif spec.name in ha_number_theory_campaign_names:
            layer = "ha_number_theory_campaign"
        elif spec.name in quadratic_residue_names:
            layer = "quadratic_residue_foundation"
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
                "distinct_proof_objects": distinct_objects,
                "index": index,
                "layer": layer,
                "name": spec.name,
                "proof_depth": depth,
                "proof_edges": proof_edges,
                "proof_nodes": nodes,
                "reused_proof_references": reused_references,
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
    theorem_sources = [
        {
            "path": str(path.relative_to(ROOT)),
            "sha256": _digest(path.read_bytes()),
        }
        for path in THEOREM_SOURCES
    ]
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
        "schema": "peano-library-snapshot-v3",
        "theorem_count": len(theorem_rows),
        "theorem_source_root_sha256": _digest(_canonical_json(theorem_sources)),
        "theorem_sources": theorem_sources,
        "theorems": theorem_rows,
    }

    metrics = {
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "live_use_limits": {
            "proof_depth": MAX_USE_PROOF_DEPTH,
            "proof_nodes": MAX_USE_CERTIFICATE_NODES,
            "proof_objects": MAX_USE_CERTIFICATE_OBJECTS,
        },
        "maximum_cut_nodes": max(row["cut_nodes"] for row in theorem_rows),
        "maximum_distinct_proof_objects": max(
            row["distinct_proof_objects"] for row in theorem_rows
        ),
        "maximum_proof_depth": max(row["proof_depth"] for row in theorem_rows),
        "maximum_proof_nodes": max(row["proof_nodes"] for row in theorem_rows),
        "ordered_root_sha256": ordered_root,
        "schema": "peano-library-metrics-v3",
        "theorem_count": len(theorem_rows),
        "theorems_with_cut_nodes": sum(
            row["cut_nodes"] > 0 for row in theorem_rows
        ),
        "theorems_by_layer": layer_counts,
        "total_cut_nodes": sum(row["cut_nodes"] for row in theorem_rows),
        "total_distinct_proof_objects": sum(
            row["distinct_proof_objects"] for row in theorem_rows
        ),
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
