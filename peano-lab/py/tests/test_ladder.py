"""Public theorem ladder: every script ends as a closed checked certificate."""

from __future__ import annotations

from dataclasses import fields, replace

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq, Forall, Imp, parse_formula_with_names
from peano_lab.kernel.proofs import Axiom, EqRefl, ForallIntro, Hyp, ImpElim, ImpIntro, Proof
from peano_lab.kernel.terms import Succ, Var, Zero
from peano_lab.library.theorems import (
    FINITE_BITCOUNT_THEOREMS,
    FINITE_CONGRUENCE_THEOREMS,
    FINITE_FACTORIAL_THEOREMS,
    FINITE_FOLD_THEOREMS,
    FINITE_PERMUTATION_THEOREMS,
    FINITE_PRODUCT_PERMUTATION_THEOREMS,
    FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS,
    FINITE_RANGE_THEOREMS,
    FINITE_SUM_THEOREMS,
    GAUSS_HALF_RANGE_THEOREMS,
    GAUSS_SIGN_BRIDGE_THEOREMS,
    PARITY_THEOREMS,
    POWER_ALGEBRA_THEOREMS,
    POWER_CONGRUENCE_THEOREMS,
    QR_PRIME_UNIT_THEOREMS,
    QR_BOUNDED_UNIT_THEOREMS,
    QR_SMALL_MODULI_THEOREMS,
    QUADRATIC_RESIDUE_THEOREMS,
    THEOREMS,
    get,
    names,
    replay,
    replay_all,
    replay_target,
    _normalise_forall_cuts,
)


EXPECTED_NAMES = (
    "zero_add",
    "add_succ_left",
    "add_comm",
    "add_assoc",
    "mul_zero_left",
    "mul_succ_left",
    "mul_comm",
    "mul_add",
    "mul_assoc",
    "one_mul",
    "mul_one",
    "add_mul",
    "succ_ne_zero",
    "succ_injective",
    "le_refl",
    "le_trans",
    "no_succ_add_fixed",
    "drop_add_prefix_from_fixed",
    "antisymm_from_witnesses",
    "le_antisymm",
    "le_total",
    "add_eq_zero_right",
    "mul_eq_zero",
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
    "fourth_power_regroup",
    "mod5_residue_complete",
    "mod5_nonzero_residue_cases",
    "mod5_square_residue_one",
    "mod5_square_residue_two",
    "mod5_square_residue_three",
    "mod5_square_residue_four",
    "mod5_fourth_power_residue_one",
    "mod5_fourth_power_residue_two",
    "mod5_fourth_power_residue_three",
    "mod5_fourth_power_residue_four",
    "mod5_fourth_power_one",
)

# The reciprocity campaign keeps its native theorem tranches in isolated data
# modules; their ordered names extend the historical ladder without copying
# those source lists into this broad integration test.
EXPECTED_NAMES += tuple(
    spec.name
    for tranche in (
        PARITY_THEOREMS,
        QUADRATIC_RESIDUE_THEOREMS,
        FINITE_FOLD_THEOREMS,
        FINITE_RANGE_THEOREMS,
        FINITE_SUM_THEOREMS,
        FINITE_CONGRUENCE_THEOREMS,
        FINITE_BITCOUNT_THEOREMS,
        QR_PRIME_UNIT_THEOREMS,
        FINITE_FACTORIAL_THEOREMS,
        POWER_CONGRUENCE_THEOREMS,
        QR_SMALL_MODULI_THEOREMS,
        POWER_ALGEBRA_THEOREMS,
        GAUSS_SIGN_BRIDGE_THEOREMS,
        GAUSS_HALF_RANGE_THEOREMS,
        FINITE_PERMUTATION_THEOREMS,
        FINITE_PRODUCT_PERMUTATION_THEOREMS,
        FINITE_PRODUCT_REINDEX_SUPPORT_THEOREMS,
        QR_BOUNDED_UNIT_THEOREMS,
    )
    for spec in tranche
)


def _mutate_first_pa6(proof: Proof) -> tuple[Proof, bool]:
    if type(proof) is Axiom and proof.name == "PA6":
        return Axiom("PA5"), True
    for item in fields(proof):
        child = getattr(proof, item.name)
        if not isinstance(child, Proof):
            continue
        changed_child, changed = _mutate_first_pa6(child)
        if changed:
            return replace(proof, **{item.name: changed_child}), True
    return proof, False


def test_full_binding_ladder_and_helpers_have_stable_acyclic_order() -> None:
    assert names() == EXPECTED_NAMES
    assert tuple(spec.name for spec in THEOREMS) == EXPECTED_NAMES

    earlier: set[str] = set()
    for spec in THEOREMS:
        formula, free_names = parse_formula_with_names(spec.statement)
        assert not free_names
        assert spec.script
        assert set(spec.dependencies) <= earlier
        found = get(spec.name)
        assert found is spec
        assert replay_target(spec) == replay_target(found)
        assert formula == replay(spec.name).formula
        earlier.add(spec.name)


def test_every_script_replays_and_final_certificate_checks_original_statement() -> None:
    checked = replay_all()

    assert tuple(item.spec.name for item in checked) == EXPECTED_NAMES
    assert all(item.proof_nodes > 0 for item in checked)
    assert all(check((), item.certificate, item.formula) for item in checked)


def test_core_capstone_is_the_required_zero_product_theorem() -> None:
    capstone = replay("mul_eq_zero")
    expected, names = parse_formula_with_names(
        "forall n m. n * m = 0 -> n = 0 \\/ m = 0"
    )

    assert names == ()
    assert capstone.formula == expected
    assert check((), capstone.certificate, expected)


def test_mutating_a_capstone_arithmetic_leaf_is_rejected() -> None:
    capstone = replay("mul_eq_zero")
    mutation, changed = _mutate_first_pa6(capstone.certificate)

    assert changed
    assert mutation != capstone.certificate
    assert not check((), mutation, capstone.formula)


def test_multi_dependency_cut_does_not_capture_inserted_internal_hypotheses() -> None:
    # This rung uses two dependencies whose own certificates contain local
    # Hyp nodes.  Sequential substitution once corrupted those internal slots.
    theorem = replay("antisymm_from_witnesses")

    assert theorem.spec.dependencies == (
        "add_assoc",
        "drop_add_prefix_from_fixed",
    )
    assert check((), theorem.certificate, theorem.formula)


def test_implication_beta_normalization_avoids_proposition_capture() -> None:
    a = Eq(Zero(), Zero())
    b = Eq(Succ(Zero()), Succ(Zero()))
    redex = ImpElim(ImpIntro(ImpIntro(Hyp(1))), Hyp(0))

    normalized = _normalise_forall_cuts(redex)

    assert normalized == ImpIntro(Hyp(1))
    assert check((a,), normalized, Imp(b, a))


def test_implication_beta_normalization_shifts_terms_below_forall() -> None:
    # The argument mentions ambient x as Var(0). Once inserted below the new
    # y binder it must become Var(1), not be captured as y.
    redex = ImpElim(
        ImpIntro(ForallIntro(Hyp(0))),
        EqRefl(Var(0)),
    )
    target = Forall(Eq(Var(1), Var(1)))

    normalized = _normalise_forall_cuts(redex)

    assert normalized == ForallIntro(EqRefl(Var(1)))
    assert check((), normalized, target)


def test_lookup_is_casefolded_but_unknown_names_do_not_fabricate_entries() -> None:
    assert get(" ADD_COMM ") is get("add_comm")
    assert get("not_a_theorem") is None
    assert get(17) is None  # type: ignore[arg-type]
