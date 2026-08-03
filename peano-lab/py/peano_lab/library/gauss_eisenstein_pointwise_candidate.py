"""Pointwise Gauss--Eisenstein join over aligned beta prefixes.

This layer composes exact signed-remainder alignment with the modulo-two
division theorem.  Its prefix endpoint opens the canonical half range, exact
scaled source, quotient/remainder trace, and Gauss magnitude/sign trace at one
common index and proves the decoded relation

``x == q + m + s (mod 2)``.

The theorem is still pointwise: aggregation into finite sums and cancellation
of the magnitude permutation are deliberately separate gates.  Every surface
relation expands to unchanged first-order PA; nothing is registered or
admitted here.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import beta_at
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    _strictly_below_term,
    _weakly_below_term,
    half_range,
    signed_half_prefix,
)
from .signed_division_parity_bridge_candidate import _mod_two, _odd
from .wilson_pair_product_candidate import _mod_eq_term


def make_gauss_eisenstein_pointwise_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the generic composition and its beta-prefix specialization."""

    variables = ("p", "h", "a", "x", "n", "q", "r", "m", "s")
    odd_a = _odd("a", tag="gep_scale")
    odd_p = _odd("p", tag="gep_modulus")
    r_below = _strictly_below_term(
        "r", "p", tag="gep_r_below", variables=variables
    )
    m_positive = _strictly_below_term(
        "0", "m", tag="gep_m_positive", variables=variables
    )
    m_bounded = _weakly_below_term(
        "m", "h", tag="gep_m_bounded", variables=variables
    )
    n_mod_m = _mod_eq_term(
        "p", "n", "m", tag="gep_n_mod_m", avoid=variables
    )
    n_mod_reflected = _mod_eq_term(
        "p", "n", "(2 * h) * m", tag="gep_n_mod_reflected", avoid=variables
    )
    signed_congruence = (
        f"((s = 0 /\\ ({n_mod_m})) \\/ "
        f"(s = 1 /\\ ({n_mod_reflected})))"
    )
    exact_branch = "((s = 0 /\\ r = m) \\/ (s = 1 /\\ r + m = p))"
    final_mod = _mod_two("x", "q + m + s", tag="gep_generic_result")

    half = half_range("b", "c", "h", tag="gep_half")
    scaled = scaled_successor_prefix("a", "tb", "tc", "h", tag="gep_scaled")
    division = division_prefix(
        "p", "tb", "tc", "qb", "qc", "rb", "rc", "h", tag="gep_division"
    )
    signed_prefix = signed_half_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "h",
        tag="gep_signed",
    )
    prefix_variables = (
        "p", "h", "a", "b", "c", "tb", "tc", "qb", "qc", "rb", "rc",
        "mb", "mc", "sb", "sc", "i", "x", "q", "m", "s",
    )
    index_bound = _strictly_below_term(
        "i", "h", tag="gep_index", variables=prefix_variables
    )
    source_entry = beta_at("b", "c", "i", "x", tag="gep_source_entry")
    quotient_entry = beta_at("qb", "qc", "i", "q", tag="gep_quotient_entry")
    magnitude_entry = beta_at("mb", "mc", "i", "m", tag="gep_magnitude_entry")
    sign_entry = beta_at("sb", "sc", "i", "s", tag="gep_sign_entry")
    prefix_result = _mod_two("x", "q + m + s", tag="gep_prefix_result")
    pointwise = (
        f"forall i x q m s. ({index_bound}) -> ({source_entry}) -> "
        f"({quotient_entry}) -> ({magnitude_entry}) -> ({sign_entry}) -> "
        f"({prefix_result})"
    )

    # Proof-local decoded packages.  Existential elimination names the three
    # division values x1,x2,x3 and the signed values x4,x5,x6.
    div_data = division_prefix(
        "p", "tb", "tc", "qb", "qc", "rb", "rc", "h", tag="gep_proof_division"
    )
    div_source = beta_at("tb", "tc", "i", "x1", tag="gep_proof_div_source")
    div_q = beta_at("qb", "qc", "i", "x2", tag="gep_proof_div_q")
    div_r = beta_at("rb", "rc", "i", "x3", tag="gep_proof_div_r")
    div_r_below = _strictly_below_term(
        "x3", "p", tag="gep_proof_div_r_below", variables=prefix_variables + ("x1", "x2", "x3")
    )
    local_division_package = (
        f"exists x1 x2 x3. ({div_source}) /\\ (({div_q}) /\\ "
        f"(({div_r}) /\\ (x1 = p * x2 + x3 /\\ ({div_r_below}))))"
    )
    signed_source = beta_at("b", "c", "i", "x4", tag="gep_proof_signed_source")
    signed_magnitude = beta_at("mb", "mc", "i", "x5", tag="gep_proof_signed_magnitude")
    signed_sign = beta_at("sb", "sc", "i", "x6", tag="gep_proof_signed_sign")
    signed_positive = _strictly_below_term(
        "0", "x5", tag="gep_proof_signed_positive", variables=prefix_variables + ("x4", "x5", "x6")
    )
    signed_bounded = _weakly_below_term(
        "x5", "h", tag="gep_proof_signed_bounded", variables=prefix_variables + ("x4", "x5", "x6")
    )
    signed_lower = _mod_eq_term(
        "p", "a * x4", "x5", tag="gep_proof_signed_lower", avoid=prefix_variables + ("x4", "x5", "x6")
    )
    signed_upper = _mod_eq_term(
        "p", "a * x4", "(2 * h) * x5", tag="gep_proof_signed_upper", avoid=prefix_variables + ("x4", "x5", "x6")
    )
    local_signed_branch = (
        f"((x6 = 0 /\\ ({signed_lower})) \\/ "
        f"(x6 = 1 /\\ ({signed_upper})))"
    )
    local_signed_package = (
        f"exists x4 x5 x6. ({signed_source}) /\\ (({signed_magnitude}) /\\ "
        f"(({signed_sign}) /\\ (({signed_positive}) /\\ (({signed_bounded}) /\\ "
        f"((x6 = 0 \\/ x6 = 1) /\\ ({local_signed_branch}))))))"
    )
    canonical_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "1 + i",
        tag="gep_proof_canonical",
        variables=prefix_variables,
    )
    local_scaled = scaled_successor_prefix("a", "tb", "tc", "h", tag="gep_proof_scaled")
    local_n_mod_m = _mod_eq_term(
        "p", "x1", "x5", tag="gep_proof_n_mod_m", avoid=prefix_variables + ("x1", "x5")
    )
    local_n_mod_upper = _mod_eq_term(
        "p", "x1", "(2 * h) * x5", tag="gep_proof_n_mod_upper", avoid=prefix_variables + ("x1", "x5")
    )
    local_signed_n = (
        f"((x6 = 0 /\\ ({local_n_mod_m})) \\/ "
        f"(x6 = 1 /\\ ({local_n_mod_upper})))"
    )
    local_final_mod = _mod_two("x4", "x2 + x5 + x6", tag="gep_proof_final")

    return (
        spec(
            "odd_signed_division_congruence_mod_two",
            "forall p h a x n q r m s. p = 2 * h + 1 -> "
            f"({odd_a}) -> n = a * x -> n = p * q + r -> ({r_below}) -> "
            f"({m_positive}) -> ({m_bounded}) -> ({signed_congruence}) -> "
            f"({final_mod})",
            (
                "odd_signed_division_branch_exact",
                "odd_scaled_division_signed_mod_two",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro x",
                "intro n",
                "intro q",
                "intro r",
                "intro m",
                "intro s",
                "intro hp",
                "intro ha",
                "intro hnscale",
                "intro hdivision",
                "intro hrbelow",
                "intro hmpositive",
                "intro hmbounded",
                "intro hsigned",
                f"have hexact : {exact_branch}",
                "specialize odd_signed_division_branch_exact p",
                "specialize odd_signed_division_branch_exact h",
                "specialize odd_signed_division_branch_exact n",
                "specialize odd_signed_division_branch_exact q",
                "specialize odd_signed_division_branch_exact r",
                "specialize odd_signed_division_branch_exact m",
                "specialize odd_signed_division_branch_exact s",
                "apply odd_signed_division_branch_exact",
                "exact hp",
                "exact hdivision",
                "exact hrbelow",
                "exact hmpositive",
                "exact hmbounded",
                "exact hsigned",
                f"have hpodd : {odd_p}",
                "exists h",
                "exact hp",
                "specialize odd_scaled_division_signed_mod_two p",
                "specialize odd_scaled_division_signed_mod_two a",
                "specialize odd_scaled_division_signed_mod_two x",
                "specialize odd_scaled_division_signed_mod_two q",
                "specialize odd_scaled_division_signed_mod_two r",
                "specialize odd_scaled_division_signed_mod_two m",
                "specialize odd_scaled_division_signed_mod_two s",
                "apply odd_scaled_division_signed_mod_two",
                "exact hpodd",
                "exact ha",
                "trans n",
                "symm",
                "exact hnscale",
                "exact hdivision",
                "exact hexact",
            ),
            "Exact signed division data gives the Gauss--Eisenstein modulo-two relation.",
        ),
        spec(
            "gauss_eisenstein_prefix_pointwise_mod_two",
            "forall p h a b c tb tc qb qc rb rc mb mc sb sc. "
            f"p = 2 * h + 1 -> ({odd_a}) -> ({half}) -> ({scaled}) -> "
            f"({division}) -> ({signed_prefix}) -> ({pointwise})",
            (
                "beta_at_unique",
                "odd_signed_division_congruence_mod_two",
            ),
            (
                "intro p", "intro h", "intro a", "intro b", "intro c",
                "intro tb", "intro tc", "intro qb", "intro qc", "intro rb",
                "intro rc", "intro mb", "intro mc", "intro sb", "intro sc",
                "intro hp", "intro ha", "intro hhalf", "intro hscaled",
                "intro hdivision", "intro hsigned",
                "intro i", "intro x", "intro q", "intro m", "intro s",
                "intro hi", "intro hx", "intro hq", "intro hm", "intro hs",
                f"have hcanonical : {canonical_entry}",
                "specialize hhalf i",
                "apply hhalf",
                "exact hi",
                f"have hdivdata : {local_division_package}",
                "specialize hdivision i",
                "apply hdivision",
                "exact hi",
                "cases hdivdata",
                "cases hdivdata_witness",
                "cases hdivdata_witness_witness",
                "cases hdivdata_witness_witness_witness",
                "cases hdivdata_witness_witness_witness_right",
                "cases hdivdata_witness_witness_witness_right_right",
                "cases hdivdata_witness_witness_witness_right_right_right",
                f"have hsigneddata : {local_signed_package}",
                "specialize hsigned i",
                "apply hsigned",
                "exact hi",
                "cases hsigneddata",
                "cases hsigneddata_witness",
                "cases hsigneddata_witness_witness",
                "cases hsigneddata_witness_witness_witness",
                "cases hsigneddata_witness_witness_witness_right",
                "cases hsigneddata_witness_witness_witness_right_right",
                "cases hsigneddata_witness_witness_witness_right_right_right",
                "cases hsigneddata_witness_witness_witness_right_right_right_right",
                "cases hsigneddata_witness_witness_witness_right_right_right_right_right",
                "have hxcanonical : x4 = 1 + i",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique (1 + i)",
                "apply beta_at_unique",
                "exact hsigneddata_witness_witness_witness_left",
                "exact hcanonical",
                "have hnscale : x1 = a * x4",
                f"have hscale_exact : {local_scaled}",
                "exact hscaled",
                "trans a * (1 + i)",
                "specialize hscale_exact i",
                "specialize hscale_exact x1",
                "apply hscale_exact",
                "exact hi",
                "exact hdivdata_witness_witness_witness_left",
                "congr",
                "refl",
                "symm",
                "exact hxcanonical",
                f"have hsignedn : {local_signed_n}",
                "cases hsigneddata_witness_witness_witness_right_right_right_right_right_right",
                "left",
                "cases hsigneddata_witness_witness_witness_right_right_right_right_right_right_left",
                "split",
                "exact hsigneddata_witness_witness_witness_right_right_right_right_right_right_left_left",
                "rewrite hnscale",
                "exact hsigneddata_witness_witness_witness_right_right_right_right_right_right_left_right",
                "right",
                "cases hsigneddata_witness_witness_witness_right_right_right_right_right_right_right",
                "split",
                "exact hsigneddata_witness_witness_witness_right_right_right_right_right_right_right_left",
                "rewrite hnscale",
                "exact hsigneddata_witness_witness_witness_right_right_right_right_right_right_right_right",
                f"have hlocal : {local_final_mod}",
                "specialize odd_signed_division_congruence_mod_two p",
                "specialize odd_signed_division_congruence_mod_two h",
                "specialize odd_signed_division_congruence_mod_two a",
                "specialize odd_signed_division_congruence_mod_two x4",
                "specialize odd_signed_division_congruence_mod_two x1",
                "specialize odd_signed_division_congruence_mod_two x2",
                "specialize odd_signed_division_congruence_mod_two x3",
                "specialize odd_signed_division_congruence_mod_two x5",
                "specialize odd_signed_division_congruence_mod_two x6",
                "apply odd_signed_division_congruence_mod_two",
                "exact hp", "exact ha", "exact hnscale",
                "exact hdivdata_witness_witness_witness_right_right_right_left",
                "exact hdivdata_witness_witness_witness_right_right_right_right",
                "exact hsigneddata_witness_witness_witness_right_right_right_left",
                "exact hsigneddata_witness_witness_witness_right_right_right_right_left",
                "exact hsignedn",
                "have hxeq : x = x4",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique i", "specialize beta_at_unique x",
                "specialize beta_at_unique x4", "apply beta_at_unique",
                "exact hx", "exact hsigneddata_witness_witness_witness_left",
                "have hqeq : q = x2",
                "specialize beta_at_unique qb", "specialize beta_at_unique qc",
                "specialize beta_at_unique i", "specialize beta_at_unique q",
                "specialize beta_at_unique x2", "apply beta_at_unique",
                "exact hq", "exact hdivdata_witness_witness_witness_right_left",
                "have hmeq : m = x5",
                "specialize beta_at_unique mb", "specialize beta_at_unique mc",
                "specialize beta_at_unique i", "specialize beta_at_unique m",
                "specialize beta_at_unique x5", "apply beta_at_unique",
                "exact hm", "exact hsigneddata_witness_witness_witness_right_left",
                "have hseq : s = x6",
                "specialize beta_at_unique sb", "specialize beta_at_unique sc",
                "specialize beta_at_unique i", "specialize beta_at_unique s",
                "specialize beta_at_unique x6", "apply beta_at_unique",
                "exact hs", "exact hsigneddata_witness_witness_witness_right_right_left",
                "rewrite hxeq", "rewrite hqeq", "rewrite hmeq", "rewrite hseq",
                "exact hlocal",
            ),
            "Aligned Gauss and Eisenstein prefixes satisfy x == q+m+s modulo two pointwise.",
        ),
    )


__all__ = ["make_gauss_eisenstein_pointwise_candidate_theorems"]
