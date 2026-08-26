"""M20 contracts for the general foundational-arithmetic extension."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import MAX_USE_CERTIFICATE_NODES, MAX_USE_PROOF_DEPTH
from peano_lab.kernel.checker import check
from peano_lab.library.theorems import get, replay


ROOT = Path(__file__).resolve().parents[3]


FOUNDATIONAL_NAMES = (
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
)


def test_foundational_extension_is_present_in_dependency_order() -> None:
    specs = [get(name) for name in FOUNDATIONAL_NAMES]

    assert all(spec is not None for spec in specs)
    positions = {spec.name: index for index, spec in enumerate(specs) if spec is not None}
    for spec in specs:
        assert spec is not None
        for dependency in spec.dependencies:
            if dependency in positions:
                assert positions[dependency] < positions[spec.name]


def test_every_foundational_extension_certificate_is_closed_and_live_importable() -> None:
    for name in FOUNDATIONAL_NAMES:
        theorem = replay(name)
        nodes, depth = proof_metrics(theorem.certificate)

        assert check((), theorem.certificate, theorem.formula)
        assert theorem.proof_nodes == nodes
        assert nodes <= MAX_USE_CERTIFICATE_NODES
        assert depth <= MAX_USE_PROOF_DEPTH


def test_divisibility_and_residue_statements_remain_definitional_expansions() -> None:
    multiple = get("multiple_trans")
    residue = get("square_residue_witness")

    assert multiple is not None and "exists q." in multiple.statement
    assert residue is not None and "exists w." in residue.statement
    assert all(
        token not in multiple.statement + residue.statement
        for token in ("%", "∣", "^")
    )


def test_generated_library_artifacts_and_vault_notes_are_current() -> None:
    for script in (
        "scripts/build_peano_library_snapshot.py",
        "scripts/build_arithmetic_vault.py",
    ):
        completed = subprocess.run(
            [sys.executable, script, "--check"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        assert completed.returncode == 0, completed.stdout + completed.stderr


def test_library_snapshot_records_self_contained_cut_representation() -> None:
    artifact_root = ROOT / "artifacts" / "peano-library"
    catalog = json.loads((artifact_root / "catalog-v1.json").read_text())
    metrics = json.loads((artifact_root / "metrics.json").read_text())
    rows = catalog["theorems"]

    assert catalog["schema"] == "peano-library-snapshot-v3"
    assert metrics["schema"] == "peano-library-metrics-v3"
    assert catalog["certificate_representation"] == (
        "python-dataclass-repr-with-cut-v2"
    )
    assert metrics["certificate_representation"] == (
        catalog["certificate_representation"]
    )
    assert all(
        row["certificate_representation"] == catalog["certificate_representation"]
        for row in rows
    )
    assert metrics["total_cut_nodes"] == sum(row["cut_nodes"] for row in rows)
    assert metrics["maximum_cut_nodes"] == max(row["cut_nodes"] for row in rows)
    assert metrics["maximum_distinct_proof_objects"] == max(
        row["distinct_proof_objects"] for row in rows
    )
    assert metrics["total_distinct_proof_objects"] == sum(
        row["distinct_proof_objects"] for row in rows
    )
    assert metrics["live_use_limits"] == {
        "proof_depth": 256,
        "proof_nodes": 500_000,
        "proof_objects": 100_000,
    }
    assert metrics["theorems_by_layer"] == {
        "foundational_extension": 212,
        "ha_number_theory_campaign": 48,
        "legacy_core": 23,
        "published_mod5_unique": 12,
        "quadratic_residue_foundation": 137,
    }
    assert [
        row["name"]
        for row in rows
        if row["layer"] == "ha_number_theory_campaign"
    ] == [
        "canonical_remainder_exists",
        "canonical_remainder_functional",
        "canonical_remainder_zero_impossible",
        "canonical_remainder_exists_unique",
        "canonical_remainders_characterize_mod_eq",
        "bounded_mod_inverse_unique",
        "coprime_bounded_mod_inverse",
        "mod_inverse_implies_coprime",
        "coprime_iff_unique_bounded_mod_inverse",
        "is_lcm_multiple_left",
        "is_lcm_multiple_right",
        "is_lcm_least",
        "is_lcm_symm",
        "is_lcm_unique",
        "is_lcm_zero_right",
        "is_lcm_zero_left",
        "balanced_bezout_one_implies_coprime",
        "coprime_product_is_lcm",
        "is_lcm_scale_nonzero",
        "balanced_bezout_cancel_gcd",
        "gcd_zero_inputs",
        "gcd_lcm_compatible_exists",
        "lcm_exists_relational",
        "canonical_lcm_exists_unique",
        "gcd_lcm_product",
        "mod_eq_zero_iff_eq",
        "mod_eq_scale",
        "crt_solution_pair_congruent",
        "crt_common_solution_implies_gcd_compatible",
        "crt_incompatibility_obstructs_solution",
        "is_gcd_quotients_coprime_nonzero",
        "mod_eq_common_remainder_decomposition",
        "crt_scaled_common_remainder_lift",
        "generalized_binary_crt_sufficient_nonzero",
        "generalized_binary_crt_sufficient_zero_left",
        "generalized_binary_crt_sufficient_zero_right",
        "generalized_binary_crt_sufficient",
        "generalized_binary_crt_solvable_iff",
        "mod_eq_ordered_gap_multiple",
        "mod_eq_lcm_merge",
        "mod_eq_lcm_iff_pair",
        "crt_solution_class_iff_lcm",
        "crt_solution_unique_lcm_zero",
        "crt_solution_canonical_remainder_nonzero",
        "generalized_binary_crt_canonical_boundary",
        "mod_eq_decidable",
        "generalized_binary_crt_solution_or_obstruction",
        "generalized_binary_crt_total_decision",
    ]
    assert [source["path"] for source in catalog["theorem_sources"]] == [
        "peano-lab/py/peano_lab/library/theorems.py",
        "peano-lab/py/peano_lab/library/parity.py",
        "peano-lab/py/peano_lab/library/quadratic_residue_theorems.py",
        "peano-lab/py/peano_lab/library/finite_fold_theorems.py",
        "peano-lab/py/peano_lab/library/finite_range_theorems.py",
        "peano-lab/py/peano_lab/library/finite_sum_theorems.py",
        "peano-lab/py/peano_lab/library/finite_congruence_theorems.py",
        "peano-lab/py/peano_lab/library/finite_bitcount_theorems.py",
        "peano-lab/py/peano_lab/library/finite_factorial_theorems.py",
        "peano-lab/py/peano_lab/library/power_congruence_theorems.py",
        "peano-lab/py/peano_lab/library/power_algebra_theorems.py",
        "peano-lab/py/peano_lab/library/gauss_sign_bridge.py",
        "peano-lab/py/peano_lab/library/gauss_half_range.py",
        "peano-lab/py/peano_lab/library/finite_permutation_theorems.py",
        "peano-lab/py/peano_lab/library/finite_product_permutation_theorems.py",
        "peano-lab/py/peano_lab/library/finite_product_reindex_support.py",
        "peano-lab/py/peano_lab/library/qr_bounded_units.py",
        "peano-lab/py/peano_lab/library/qr_prime_units.py",
        "peano-lab/py/peano_lab/library/qr_small_moduli.py",
        "peano-lab/py/peano_lab/library/ha_canonical_remainder_candidate.py",
        "peano-lab/py/peano_lab/library/ha_canonical_congruence_candidate.py",
        "peano-lab/py/peano_lab/library/wilson_inverse_point_candidate.py",
        "peano-lab/py/peano_lab/library/ha_modular_inverse_candidate.py",
        "peano-lab/py/peano_lab/library/ha_relational_lcm_candidate.py",
        "peano-lab/py/peano_lab/library/ha_lcm_totality_bridge_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_congruence_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_sufficiency_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_zero_boundary_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_classification_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_canonical_boundary_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_decision_candidate.py",
        "peano-lab/py/peano_lab/library/ha_generalized_crt_total_decision_candidate.py",
    ]
    assert metrics["theorems_with_cut_nodes"] == sum(
        row["cut_nodes"] > 0 for row in rows
    )
    assert metrics["ordered_root_sha256"] == catalog["ordered_root_sha256"]
    assert "self-contained checked Cut node" in catalog["certificate_policy"]
    assert "external theorem environment" in catalog["certificate_policy"]
