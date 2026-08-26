"""Exact alignment of Gauss signs with canonical division remainders.

The signed-half prefix records a lower/reflected congruence, while the
Eisenstein division prefix records a canonical exact remainder.  This module
bridges those representations pointwise.  For an odd modulus ``p=2*h+1``, a
positive magnitude ``m<=h`` has a unique positive complement below ``p``;
the predecessor multiplier represents that complement modulo ``p``.  Hence
canonical-remainder uniqueness turns each signed congruence branch into the
exact equations ``r=m`` or ``r+m=p`` required by the parity join.

All relations expand to unchanged first-order PA.  These candidates are
constructive, dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .gauss_signed_prefix_candidate import (
    _strictly_below_term,
    _weakly_below_term,
)
from .wilson_pair_product_candidate import _mod_eq_term


def make_gauss_signed_division_alignment_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build complement, canonical-remainder, and exact-sign alignment."""

    variables = ("p", "h", "m", "t", "n", "q", "r", "s")
    m_positive = _strictly_below_term(
        "0", "m", tag="gsd_m_positive", variables=variables
    )
    m_le_h = _weakly_below_term(
        "m", "h", tag="gsd_m_le_h", variables=variables
    )
    t_below_p = _strictly_below_term(
        "t", "p", tag="gsd_t_below_p", variables=variables
    )
    complement = f"exists t. ({t_below_p}) /\\ t + m = p"

    predecessor_mod = _mod_eq_term(
        "p", "k * m", "t", tag="gsd_predecessor_mod", avoid=("p", "k", "m", "t")
    )

    r_below_p = _strictly_below_term(
        "r", "p", tag="gsd_r_below_p", variables=variables
    )
    canonical_t_below = _strictly_below_term(
        "t", "p", tag="gsd_canonical_t_below", variables=variables
    )
    n_mod_t = _mod_eq_term(
        "p", "n", "t", tag="gsd_n_mod_t", avoid=variables
    )

    m_below_p = _strictly_below_term(
        "m", "p", tag="gsd_m_below_p", variables=variables
    )
    n_mod_m = _mod_eq_term(
        "p", "n", "m", tag="gsd_n_mod_m", avoid=variables
    )
    n_mod_reflected = _mod_eq_term(
        "p",
        "n",
        "(2 * h) * m",
        tag="gsd_n_mod_reflected",
        avoid=variables,
    )
    signed_congruence = (
        f"((s = 0 /\\ ({n_mod_m})) \\/ "
        f"(s = 1 /\\ ({n_mod_reflected})))"
    )
    exact_signed_branch = "((s = 0 /\\ r = m) \\/ (s = 1 /\\ r + m = p))"

    proof_n_mod_r = _mod_eq_term(
        "p", "n", "r", tag="gsd_proof_n_mod_r", avoid=variables
    )
    proof_r_mod_n = _mod_eq_term(
        "p", "r", "n", tag="gsd_proof_r_mod_n", avoid=variables
    )
    proof_r_mod_t = _mod_eq_term(
        "p", "r", "t", tag="gsd_proof_r_mod_t", avoid=variables
    )
    local_predecessor_mod = _mod_eq_term(
        "p",
        "(2 * h) * m",
        "x",
        tag="gsd_local_predecessor_mod",
        avoid=variables + ("x",),
    )
    local_n_mod_t = _mod_eq_term(
        "p", "n", "x", tag="gsd_local_n_mod_t", avoid=variables + ("x",)
    )

    return (
        spec(
            "odd_half_positive_complement_exists",
            "forall p h m. p = 2 * h + 1 -> "
            f"({m_positive}) -> ({m_le_h}) -> ({complement})",
            (
                "lt_irrefl_expanded",
                "nonzero_is_succ",
                "add_assoc",
                "add_comm",
                "mul_comm",
                "zero_add",
                "add_succ_left",
            ),
            (
                "intro p",
                "intro h",
                "intro m",
                "intro hp",
                "intro hmpositive",
                "intro hmle",
                "cases hmle",
                "have hsum : (h + x + 1) + m = p",
                "trans h + (x + m) + 1",
                "simp [add_assoc, add_comm]",
                "congr",
                "trans (m + x) + h",
                "symm",
                "apply add_assoc",
                "trans (x + m) + h",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "rewrite hmle_witness",
                "rewrite hp",
                "trans h + h + 1",
                "refl",
                "congr",
                "trans h * 2",
                "simp [zero_add]",
                "specialize mul_comm h",
                "specialize mul_comm 2",
                "apply mul_comm",
                "refl",
                "have hm0 : ~(m = 0)",
                "intro hmzero",
                "specialize lt_irrefl_expanded 0",
                "apply lt_irrefl_expanded",
                "rewrite hmzero at hmpositive",
                "exact hmpositive",
                "have hmsucc : exists z. m = S z",
                "specialize nonzero_is_succ m",
                "apply nonzero_is_succ",
                "exact hm0",
                "cases hmsucc",
                "exists h + x + 1",
                "split",
                "exists x1",
                "trans S (x1 + (h + x + 1))",
                "apply PA4",
                "trans S ((h + x + 1) + x1)",
                "congr",
                "apply add_comm",
                "trans (h + x + 1) + S x1",
                "symm",
                "apply PA4",
                "trans (h + x + 1) + m",
                "congr",
                "refl",
                "symm",
                "exact hmsucc_witness",
                "exact hsum",
                "exact hsum",
            ),
            "A positive magnitude at most the odd half has a complement below the modulus.",
        ),
        spec(
            "predecessor_multiple_mod_complement",
            f"forall p k m t. p = S k -> t + m = p -> ({predecessor_mod})",
            ("mul_one", "mul_succ_left", "add_assoc", "add_comm"),
            (
                "intro p",
                "intro k",
                "intro m",
                "intro t",
                "intro hp",
                "intro hsum",
                "exists 1",
                "exists m",
                "trans k * m + p",
                "congr",
                "refl",
                "apply mul_one",
                "trans k * m + (t + m)",
                "congr",
                "refl",
                "symm",
                "exact hsum",
                "trans t + (k * m + m)",
                "simp [add_assoc, add_comm]",
                "trans t + (S k) * m",
                "congr",
                "refl",
                "symm",
                "apply mul_succ_left",
                "congr",
                "refl",
                "congr",
                "symm",
                "exact hp",
                "refl",
            ),
            "The predecessor multiplier is congruent to the complementary remainder.",
        ),
        spec(
            "canonical_remainder_from_mod",
            "forall p n q r t. n = p * q + r -> "
            f"({r_below_p}) -> ({canonical_t_below}) -> ({n_mod_t}) -> r = t",
            (
                "mul_comm",
                "remainder_decomposition_to_mod_eq",
                "mod_eq_symm",
                "mod_eq_trans",
                "mod_eq_bounded_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro q",
                "intro r",
                "intro t",
                "intro hdivision",
                "intro hrbelow",
                "intro htbelow",
                "intro hnmodt",
                "have hdirected : n = q * p + r",
                "trans p * q + r",
                "exact hdivision",
                "congr",
                "apply mul_comm",
                "refl",
                f"have hnmodr : {proof_n_mod_r}",
                "specialize remainder_decomposition_to_mod_eq p",
                "specialize remainder_decomposition_to_mod_eq n",
                "specialize remainder_decomposition_to_mod_eq q",
                "specialize remainder_decomposition_to_mod_eq r",
                "apply remainder_decomposition_to_mod_eq",
                "exact hdirected",
                f"have hrmodn : {proof_r_mod_n}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm n",
                "specialize mod_eq_symm r",
                "apply mod_eq_symm",
                "exact hnmodr",
                f"have hrmodt : {proof_r_mod_t}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans r",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans t",
                "apply mod_eq_trans",
                "exact hrmodn",
                "exact hnmodt",
                "specialize mod_eq_bounded_unique p",
                "specialize mod_eq_bounded_unique r",
                "specialize mod_eq_bounded_unique t",
                "apply mod_eq_bounded_unique",
                "exact hrbelow",
                "exact htbelow",
                "exact hrmodt",
            ),
            "A bounded value congruent to an exact division input is its canonical remainder.",
        ),
        spec(
            "odd_signed_division_branch_exact",
            "forall p h n q r m s. p = 2 * h + 1 -> "
            f"n = p * q + r -> ({r_below_p}) -> ({m_positive}) -> "
            f"({m_le_h}) -> ({signed_congruence}) -> ({exact_signed_branch})",
            (
                "odd_half_strictly_below_modulus",
                "lt_of_le_of_lt",
                "odd_half_positive_complement_exists",
                "predecessor_multiple_mod_complement",
                "canonical_remainder_from_mod",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro h",
                "intro n",
                "intro q",
                "intro r",
                "intro m",
                "intro s",
                "intro hp",
                "intro hdivision",
                "intro hrbelow",
                "intro hmpositive",
                "intro hmle",
                "intro hsigned",
                "have hhalfbelow : exists d. d + S h = p",
                "specialize odd_half_strictly_below_modulus p",
                "specialize odd_half_strictly_below_modulus h",
                "apply odd_half_strictly_below_modulus",
                "exact hp",
                f"have hmbelow : {m_below_p}",
                "specialize lt_of_le_of_lt m",
                "specialize lt_of_le_of_lt h",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "exact hmle",
                "exact hhalfbelow",
                "cases hsigned",
                "cases hsigned_left",
                "left",
                "split",
                "exact hsigned_left_left",
                "specialize canonical_remainder_from_mod p",
                "specialize canonical_remainder_from_mod n",
                "specialize canonical_remainder_from_mod q",
                "specialize canonical_remainder_from_mod r",
                "specialize canonical_remainder_from_mod m",
                "apply canonical_remainder_from_mod",
                "exact hdivision",
                "exact hrbelow",
                "exact hmbelow",
                "exact hsigned_left_right",
                "cases hsigned_right",
                "have hcomplement : " + complement,
                "specialize odd_half_positive_complement_exists p",
                "specialize odd_half_positive_complement_exists h",
                "specialize odd_half_positive_complement_exists m",
                "apply odd_half_positive_complement_exists",
                "exact hp",
                "exact hmpositive",
                "exact hmle",
                "cases hcomplement",
                "cases hcomplement_witness",
                "have hpsucc : p = S (2 * h)",
                "trans 2 * h + 1",
                "exact hp",
                "simp",
                f"have hkmodt : {local_predecessor_mod}",
                "specialize predecessor_multiple_mod_complement p",
                "specialize predecessor_multiple_mod_complement (2 * h)",
                "specialize predecessor_multiple_mod_complement m",
                "specialize predecessor_multiple_mod_complement x",
                "apply predecessor_multiple_mod_complement",
                "exact hpsucc",
                "exact hcomplement_witness_right",
                f"have hnlocalt : {local_n_mod_t}",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans n",
                "specialize mod_eq_trans ((2 * h) * m)",
                "specialize mod_eq_trans x",
                "apply mod_eq_trans",
                "exact hsigned_right_right",
                "exact hkmodt",
                "have hrt : r = x",
                "specialize canonical_remainder_from_mod p",
                "specialize canonical_remainder_from_mod n",
                "specialize canonical_remainder_from_mod q",
                "specialize canonical_remainder_from_mod r",
                "specialize canonical_remainder_from_mod x",
                "apply canonical_remainder_from_mod",
                "exact hdivision",
                "exact hrbelow",
                "exact hcomplement_witness_left",
                "exact hnlocalt",
                "right",
                "split",
                "exact hsigned_right_left",
                "trans x + m",
                "congr",
                "exact hrt",
                "refl",
                "exact hcomplement_witness_right",
            ),
            "A Gauss signed congruence determines the exact canonical lower/reflected remainder branch.",
        ),
    )


__all__ = ["make_gauss_signed_division_alignment_candidate_theorems"]
