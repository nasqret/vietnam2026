"""Pointwise parity/congruence bridge for signed division data.

Suppose odd ``a`` and odd ``p`` satisfy ``a*x = p*q + r``.  A signed
representative is either the lower remainder (``s=0`` and ``r=m``) or its
reflection (``s=1`` and ``r+m=p``).  This tranche proves constructively that
``x`` is congruent modulo two to ``q+m+s``.

No separate bit premise is needed: the signed-branch disjunction itself
already forces ``s`` to be zero or one, so the final contract is stronger
than the redundant bit-premised presentation.  All readable parity and
congruence relations expand to ordinary first-order PA.  The candidates are
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable


def _even(term: str, *, tag: str) -> str:
    return f"exists sdp_even_{tag}. {term} = 2 * sdp_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists sdp_odd_{tag}. {term} = 2 * sdp_odd_{tag} + 1"


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists sdp_u_{tag} sdp_v_{tag}. "
        f"({left}) + 2 * sdp_u_{tag} = ({right}) + 2 * sdp_v_{tag}"
    )


def make_signed_division_parity_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build matching-parity, reflected-remainder, and signed endpoints."""

    even_x = _even("x", tag="matching_x")
    even_y = _even("y", tag="matching_y")
    odd_x = _odd("x", tag="matching_x")
    odd_y = _odd("y", tag="matching_y")
    matching = (
        f"((({even_x}) /\\ ({even_y})) \/ (({odd_x}) /\\ ({odd_y})))"
    )
    mod_x_y = _mod_two("x", "y", tag="matching_result")

    odd_p = _odd("p", tag="prime_like_modulus")
    odd_a = _odd("a", tag="scale")
    reflected_mod = _mod_two("r", "m + 1", tag="reflected_remainder")
    product_division_mod = _mod_two(
        "x", "q + r", tag="product_division_result"
    )
    signed_branch = "((s = 0 /\\ r = m) \/ (s = 1 /\\ r + m = p))"
    signed_sum_mod = _mod_two(
        "q + r", "q + m + s", tag="signed_sum_result"
    )
    final_mod = _mod_two("x", "q + m + s", tag="signed_final_result")

    proof_x_zero = _mod_two("x", "0", tag="proof_x_zero")
    proof_y_zero = _mod_two("y", "0", tag="proof_y_zero")
    proof_zero_y = _mod_two("0", "y", tag="proof_zero_y")
    proof_x_one = _mod_two("x", "1", tag="proof_x_one")
    proof_y_one = _mod_two("y", "1", tag="proof_y_one")
    proof_one_y = _mod_two("1", "y", tag="proof_one_y")

    proof_even_ax = _even("a * x", tag="proof_ax_even")
    proof_odd_ax = _odd("a * x", tag="proof_ax_odd")
    proof_even_x = _even("x", tag="proof_x_even")
    proof_odd_x = _odd("x", tag="proof_x_odd")
    proof_even_qr = _even("q + r", tag="proof_qr_even")
    proof_odd_qr = _odd("q + r", tag="proof_qr_odd")
    proof_product_parity = (
        f"(((({proof_even_ax}) -> ({proof_even_x})) /\\ "
        f"(({proof_even_x}) -> ({proof_even_ax}))) /\\ "
        f"((({proof_odd_ax}) -> ({proof_odd_x})) /\\ "
        f"(({proof_odd_x}) -> ({proof_odd_ax}))))"
    )
    proof_division_parity = (
        f"(((({proof_even_ax}) -> ({proof_even_qr})) /\\ "
        f"(({proof_even_qr}) -> ({proof_even_ax}))) /\\ "
        f"((({proof_odd_ax}) -> ({proof_odd_qr})) /\\ "
        f"(({proof_odd_qr}) -> ({proof_odd_ax}))))"
    )
    proof_matching_x_qr = (
        f"((({proof_even_x}) /\\ ({proof_even_qr})) \/ "
        f"(({proof_odd_x}) /\\ ({proof_odd_qr})))"
    )
    proof_q_refl = _mod_two("q", "q", tag="proof_q_refl")
    proof_r_reflected = _mod_two("r", "m + 1", tag="proof_r_reflected")
    proof_signed_upper = _mod_two(
        "q + r", "q + (m + 1)", tag="proof_signed_upper"
    )

    return (
        spec(
            "matching_parity_mod_two",
            f"forall x y. ({matching}) -> ({mod_x_y})",
            (
                "even_to_mod_two_zero",
                "odd_to_mod_two_one",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro x",
                "intro y",
                "intro hmatching",
                "cases hmatching",
                "cases hmatching_left",
                f"have hxzero : {proof_x_zero}",
                "specialize even_to_mod_two_zero x",
                "apply even_to_mod_two_zero",
                "exact hmatching_left_left",
                f"have hyzero : {proof_y_zero}",
                "specialize even_to_mod_two_zero y",
                "apply even_to_mod_two_zero",
                "exact hmatching_left_right",
                f"have hzeroy : {proof_zero_y}",
                "specialize mod_eq_symm 2",
                "specialize mod_eq_symm y",
                "specialize mod_eq_symm 0",
                "apply mod_eq_symm",
                "exact hyzero",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans 0",
                "specialize mod_eq_trans y",
                "apply mod_eq_trans",
                "exact hxzero",
                "exact hzeroy",
                "cases hmatching_right",
                f"have hxone : {proof_x_one}",
                "specialize odd_to_mod_two_one x",
                "apply odd_to_mod_two_one",
                "exact hmatching_right_left",
                f"have hyone : {proof_y_one}",
                "specialize odd_to_mod_two_one y",
                "apply odd_to_mod_two_one",
                "exact hmatching_right_right",
                f"have honey : {proof_one_y}",
                "specialize mod_eq_symm 2",
                "specialize mod_eq_symm y",
                "specialize mod_eq_symm 1",
                "apply mod_eq_symm",
                "exact hyone",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans 1",
                "specialize mod_eq_trans y",
                "apply mod_eq_trans",
                "exact hxone",
                "exact honey",
            ),
            "Naturals with the same constructive parity are congruent modulo two.",
        ),
        spec(
            "odd_product_division_mod_two",
            "forall p a x q r. "
            f"({odd_p}) -> ({odd_a}) -> a * x = p * q + r -> "
            f"({product_division_mod})",
            (
                "parity_cases",
                "odd_multiplier_parity_iff",
                "odd_division_parity_iff",
                "matching_parity_mod_two",
            ),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro q",
                "intro r",
                "intro hp",
                "intro ha",
                "intro hdivision",
                f"have hproduct : {proof_product_parity}",
                "specialize odd_multiplier_parity_iff a",
                "specialize odd_multiplier_parity_iff x",
                "apply odd_multiplier_parity_iff",
                "exact ha",
                f"have hquotient : {proof_division_parity}",
                "specialize odd_division_parity_iff p",
                "specialize odd_division_parity_iff q",
                "specialize odd_division_parity_iff r",
                "specialize odd_division_parity_iff (a * x)",
                "apply odd_division_parity_iff",
                "exact hp",
                "exact hdivision",
                "cases hproduct",
                "cases hproduct_left",
                "cases hproduct_right",
                "cases hquotient",
                "cases hquotient_left",
                "cases hquotient_right",
                "have hxcases : exists k. x = 2 * k \/ x = 2 * k + 1",
                "specialize parity_cases x",
                "exact parity_cases",
                "cases hxcases",
                "cases hxcases_witness",
                f"have hmatching : {proof_matching_x_qr}",
                "left",
                "split",
                "exists x1",
                "exact hxcases_witness_left",
                "apply hquotient_left_left",
                "apply hproduct_left_right",
                "exists x1",
                "exact hxcases_witness_left",
                "specialize matching_parity_mod_two x",
                "specialize matching_parity_mod_two (q + r)",
                "apply matching_parity_mod_two",
                "exact hmatching",
                f"have hmatching : {proof_matching_x_qr}",
                "right",
                "split",
                "exists x1",
                "exact hxcases_witness_right",
                "apply hquotient_right_left",
                "apply hproduct_right_right",
                "exists x1",
                "exact hxcases_witness_right",
                "specialize matching_parity_mod_two x",
                "specialize matching_parity_mod_two (q + r)",
                "apply matching_parity_mod_two",
                "exact hmatching",
            ),
            "Odd scale and modulus transport an exact division equation to x == q+r modulo two.",
        ),
        spec(
            "odd_reflected_remainder_mod_two",
            f"forall p r m. ({odd_p}) -> r + m = p -> ({reflected_mod})",
            (
                "add_assoc",
                "add_comm",
                "mul_comm",
                "zero_add",
                "add_succ_left",
            ),
            (
                "intro p",
                "intro r",
                "intro m",
                "intro hp",
                "intro hreflect",
                "cases hp",
                "have hdouble : 2 * m = m + m",
                "trans m * 2",
                "apply mul_comm",
                "simp [zero_add]",
                "exists m",
                "exists x",
                "trans r + (m + m)",
                "congr",
                "refl",
                "exact hdouble",
                "trans (r + m) + m",
                "symm",
                "apply add_assoc",
                "trans p + m",
                "rewrite hreflect",
                "refl",
                "trans (2 * x + 1) + m",
                "rewrite hp_witness",
                "refl",
                "simp [add_assoc, add_comm]",
                "apply add_succ_left",
            ),
            "Reflecting two remainders across an odd modulus flips parity.",
        ),
        spec(
            "signed_remainder_sum_mod_two",
            f"forall p q r m s. ({odd_p}) -> ({signed_branch}) -> "
            f"({signed_sum_mod})",
            (
                "odd_reflected_remainder_mod_two",
                "mod_eq_refl",
                "mod_eq_add",
                "add_assoc",
            ),
            (
                "intro p",
                "intro q",
                "intro r",
                "intro m",
                "intro s",
                "intro hp",
                "intro hbranch",
                "cases hbranch",
                "cases hbranch_left",
                "rewrite hbranch_left_left",
                "rewrite hbranch_left_right",
                "exists 0",
                "exists 0",
                "rewrite PA5",
                "rewrite PA5",
                "symm",
                "apply PA3",
                "cases hbranch_right",
                f"have hrmod : {proof_r_reflected}",
                "specialize odd_reflected_remainder_mod_two p",
                "specialize odd_reflected_remainder_mod_two r",
                "specialize odd_reflected_remainder_mod_two m",
                "apply odd_reflected_remainder_mod_two",
                "exact hp",
                "exact hbranch_right_right",
                f"have hqmod : {proof_q_refl}",
                "specialize mod_eq_refl 2",
                "specialize mod_eq_refl q",
                "exact mod_eq_refl",
                f"have hsum : {proof_signed_upper}",
                "specialize mod_eq_add 2",
                "specialize mod_eq_add q",
                "specialize mod_eq_add q",
                "specialize mod_eq_add r",
                "specialize mod_eq_add (m + 1)",
                "apply mod_eq_add",
                "exact hqmod",
                "exact hrmod",
                "rewrite hbranch_right_left",
                "specialize add_assoc q",
                "specialize add_assoc m",
                "specialize add_assoc 1",
                "rewrite add_assoc",
                "exact hsum",
            ),
            "A lower/reflected signed remainder changes q+r to q+m+s only by an even amount.",
        ),
        spec(
            "odd_scaled_division_signed_mod_two",
            "forall p a x q r m s. "
            f"({odd_p}) -> ({odd_a}) -> a * x = p * q + r -> "
            f"({signed_branch}) -> ({final_mod})",
            (
                "odd_product_division_mod_two",
                "signed_remainder_sum_mod_two",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro a",
                "intro x",
                "intro q",
                "intro r",
                "intro m",
                "intro s",
                "intro hp",
                "intro ha",
                "intro hdivision",
                "intro hbranch",
                f"have hxqr : {_mod_two('x', 'q + r', tag='proof_final_x_qr')}",
                "specialize odd_product_division_mod_two p",
                "specialize odd_product_division_mod_two a",
                "specialize odd_product_division_mod_two x",
                "specialize odd_product_division_mod_two q",
                "specialize odd_product_division_mod_two r",
                "apply odd_product_division_mod_two",
                "exact hp",
                "exact ha",
                "exact hdivision",
                f"have hqrsigned : {_mod_two('q + r', 'q + m + s', tag='proof_final_qr_signed')}",
                "specialize signed_remainder_sum_mod_two p",
                "specialize signed_remainder_sum_mod_two q",
                "specialize signed_remainder_sum_mod_two r",
                "specialize signed_remainder_sum_mod_two m",
                "specialize signed_remainder_sum_mod_two s",
                "apply signed_remainder_sum_mod_two",
                "exact hp",
                "exact hbranch",
                "specialize mod_eq_trans 2",
                "specialize mod_eq_trans x",
                "specialize mod_eq_trans (q + r)",
                "specialize mod_eq_trans (q + m + s)",
                "apply mod_eq_trans",
                "exact hxqr",
                "exact hqrsigned",
            ),
            "The generic Gauss-Eisenstein pointwise join: x == q+m+s modulo two.",
        ),
    )


__all__ = ["make_signed_division_parity_bridge_candidate_theorems"]
