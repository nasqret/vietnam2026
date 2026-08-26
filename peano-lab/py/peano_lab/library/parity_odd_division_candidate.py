"""Odd-multiplier and exact-division parity transport in native PA.

This isolated tranche supplies the generic parity bridge used by later
floor-sum arguments.  Multiplication by an odd natural preserves and reflects
both parity classes.  Consequently an exact equation ``n = p*q + r`` with
odd ``p`` identifies the parity of ``n`` with that of ``q+r``.

``Even`` and ``Odd`` remain authoring notation only: every contract below is
expanded to existential equations before parsing.  The candidates are
dependency-curried, constructive, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable


def _even(term: str, *, tag: str) -> str:
    return f"exists pod_even_{tag}. {term} = 2 * pod_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists pod_odd_{tag}. {term} = 2 * pod_odd_{tag} + 1"


def make_parity_odd_division_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build odd-product parity reflection and division parity packages."""

    odd_p = _odd("p", tag="multiplier")
    even_q = _even("q", tag="factor_even")
    odd_q = _odd("q", tag="factor_odd")
    even_product = _even("p * q", tag="product_even")
    odd_product = _odd("p * q", tag="product_odd")
    even_product_iff = (
        f"((({even_product}) -> ({even_q})) /\\ "
        f"(({even_q}) -> ({even_product})))"
    )
    odd_product_iff = (
        f"((({odd_product}) -> ({odd_q})) /\\ "
        f"(({odd_q}) -> ({odd_product})))"
    )

    even_n = _even("n", tag="division_n_even")
    odd_n = _odd("n", tag="division_n_odd")
    even_qr = _even("q + r", tag="division_qr_even")
    odd_qr = _odd("q + r", tag="division_qr_odd")
    even_division_iff = (
        f"((({even_n}) -> ({even_qr})) /\\ (({even_qr}) -> ({even_n})))"
    )
    odd_division_iff = (
        f"((({odd_n}) -> ({odd_qr})) /\\ (({odd_qr}) -> ({odd_n})))"
    )

    proof_even_pq = _even("p * q", tag="proof_pq_even")
    proof_odd_pq = _odd("p * q", tag="proof_pq_odd")
    proof_even_q = _even("q", tag="proof_q_even")
    proof_odd_q = _odd("q", tag="proof_q_odd")
    proof_even_r = _even("r", tag="proof_r_even")
    proof_odd_r = _odd("r", tag="proof_r_odd")
    proof_even_pqr = _even("p * q + r", tag="proof_pqr_even")
    proof_odd_pqr = _odd("p * q + r", tag="proof_pqr_odd")
    proof_even_qr = _even("q + r", tag="proof_qr_even")
    proof_odd_qr = _odd("q + r", tag="proof_qr_odd")

    proof_even_mul_iff = (
        f"((({proof_even_pq}) -> ({proof_even_q})) /\\ "
        f"(({proof_even_q}) -> ({proof_even_pq})))"
    )
    proof_odd_mul_iff = (
        f"((({proof_odd_pq}) -> ({proof_odd_q})) /\\ "
        f"(({proof_odd_q}) -> ({proof_odd_pq})))"
    )
    proof_same_pqr = (
        f"((({proof_even_pq}) /\\ ({proof_even_r})) \/ "
        f"(({proof_odd_pq}) /\\ ({proof_odd_r})))"
    )
    proof_same_qr = (
        f"((({proof_even_q}) /\\ ({proof_even_r})) \/ "
        f"(({proof_odd_q}) /\\ ({proof_odd_r})))"
    )
    proof_opposite_pqr = (
        f"((({proof_even_pq}) /\\ ({proof_odd_r})) \/ "
        f"(({proof_odd_pq}) /\\ ({proof_even_r})))"
    )
    proof_opposite_qr = (
        f"((({proof_even_q}) /\\ ({proof_odd_r})) \/ "
        f"(({proof_odd_q}) /\\ ({proof_even_r})))"
    )
    proof_even_pqr_iff = (
        f"((({proof_even_pqr}) -> ({proof_same_pqr})) /\\ "
        f"(({proof_same_pqr}) -> ({proof_even_pqr})))"
    )
    proof_even_qr_iff = (
        f"((({proof_even_qr}) -> ({proof_same_qr})) /\\ "
        f"(({proof_same_qr}) -> ({proof_even_qr})))"
    )
    proof_odd_pqr_iff = (
        f"((({proof_odd_pqr}) -> ({proof_opposite_pqr})) /\\ "
        f"(({proof_opposite_pqr}) -> ({proof_odd_pqr})))"
    )
    proof_odd_qr_iff = (
        f"((({proof_odd_qr}) -> ({proof_opposite_qr})) /\\ "
        f"(({proof_opposite_qr}) -> ({proof_odd_qr})))"
    )

    division_prefix = f"forall p q r n. ({odd_p}) -> n = p * q + r -> "

    return (
        spec(
            "odd_multiplier_even_product_iff",
            f"forall p q. ({odd_p}) -> ({even_product_iff})",
            (
                "parity_cases",
                "odd_mul_odd",
                "even_not_odd",
                "even_mul_right",
            ),
            (
                "intro p",
                "intro q",
                "intro hp",
                "split",
                "intro hproduct",
                "have hqcases : exists k. q = 2 * k \/ q = 2 * k + 1",
                "specialize parity_cases q",
                "exact parity_cases",
                "cases hqcases",
                "cases hqcases_witness",
                "exists x",
                "exact hqcases_witness_left",
                "exfalso",
                f"have hproduct_odd : {_odd('p * q', tag='even_iff_contradiction')}",
                "specialize odd_mul_odd p",
                "specialize odd_mul_odd q",
                "apply odd_mul_odd",
                "exact hp",
                "exists x",
                "exact hqcases_witness_right",
                "specialize even_not_odd (p * q)",
                "apply even_not_odd",
                "exact hproduct",
                "exact hproduct_odd",
                "intro hq",
                "specialize even_mul_right p",
                "specialize even_mul_right q",
                "apply even_mul_right",
                "exact hq",
            ),
            "Multiplication by an odd natural preserves and reflects evenness.",
        ),
        spec(
            "odd_multiplier_odd_product_iff",
            f"forall p q. ({odd_p}) -> ({odd_product_iff})",
            (
                "parity_cases",
                "even_mul_right",
                "odd_not_even",
                "odd_mul_odd",
            ),
            (
                "intro p",
                "intro q",
                "intro hp",
                "split",
                "intro hproduct",
                "have hqcases : exists k. q = 2 * k \/ q = 2 * k + 1",
                "specialize parity_cases q",
                "exact parity_cases",
                "cases hqcases",
                "cases hqcases_witness",
                "exfalso",
                f"have hproduct_even : {_even('p * q', tag='odd_iff_contradiction')}",
                "specialize even_mul_right p",
                "specialize even_mul_right q",
                "apply even_mul_right",
                "exists x",
                "exact hqcases_witness_left",
                "specialize odd_not_even (p * q)",
                "apply odd_not_even",
                "exact hproduct",
                "exact hproduct_even",
                "exists x",
                "exact hqcases_witness_right",
                "intro hq",
                "specialize odd_mul_odd p",
                "specialize odd_mul_odd q",
                "apply odd_mul_odd",
                "exact hp",
                "exact hq",
            ),
            "Multiplication by an odd natural preserves and reflects oddness.",
        ),
        spec(
            "odd_multiplier_parity_iff",
            f"forall p q. ({odd_p}) -> (({even_product_iff}) /\\ ({odd_product_iff}))",
            (
                "odd_multiplier_even_product_iff",
                "odd_multiplier_odd_product_iff",
            ),
            (
                "intro p",
                "intro q",
                "intro hp",
                "split",
                "specialize odd_multiplier_even_product_iff p",
                "specialize odd_multiplier_even_product_iff q",
                "apply odd_multiplier_even_product_iff",
                "exact hp",
                "specialize odd_multiplier_odd_product_iff p",
                "specialize odd_multiplier_odd_product_iff q",
                "apply odd_multiplier_odd_product_iff",
                "exact hp",
            ),
            "An odd multiplier preserves both parity classes exactly.",
        ),
        spec(
            "odd_division_even_iff",
            f"{division_prefix}({even_division_iff})",
            (
                "odd_multiplier_even_product_iff",
                "odd_multiplier_odd_product_iff",
                "even_sum_iff_same_parity",
            ),
            (
                "intro p",
                "intro q",
                "intro r",
                "intro n",
                "intro hp",
                "intro hdivision",
                f"have hmul_even : {proof_even_mul_iff}",
                "specialize odd_multiplier_even_product_iff p",
                "specialize odd_multiplier_even_product_iff q",
                "apply odd_multiplier_even_product_iff",
                "exact hp",
                f"have hmul_odd : {proof_odd_mul_iff}",
                "specialize odd_multiplier_odd_product_iff p",
                "specialize odd_multiplier_odd_product_iff q",
                "apply odd_multiplier_odd_product_iff",
                "exact hp",
                f"have hleft : {proof_even_pqr_iff}",
                "specialize even_sum_iff_same_parity (p * q)",
                "specialize even_sum_iff_same_parity r",
                "exact even_sum_iff_same_parity",
                f"have hright : {proof_even_qr_iff}",
                "specialize even_sum_iff_same_parity q",
                "specialize even_sum_iff_same_parity r",
                "exact even_sum_iff_same_parity",
                "cases hmul_even",
                "cases hmul_odd",
                "cases hleft",
                "cases hright",
                "split",
                "intro hn",
                f"have hpqr : {proof_even_pqr}",
                "rewrite <- hdivision",
                "exact hn",
                "apply hright_right",
                "have hsame : " + proof_same_pqr,
                "apply hleft_left",
                "exact hpqr",
                "cases hsame",
                "cases hsame_left",
                "left",
                "split",
                "apply hmul_even_left",
                "exact hsame_left_left",
                "exact hsame_left_right",
                "cases hsame_right",
                "right",
                "split",
                "apply hmul_odd_left",
                "exact hsame_right_left",
                "exact hsame_right_right",
                "intro hqr",
                f"have hpqr : {proof_even_pqr}",
                "apply hleft_right",
                "have hsame : " + proof_same_qr,
                "apply hright_left",
                "exact hqr",
                "cases hsame",
                "cases hsame_left",
                "left",
                "split",
                "apply hmul_even_right",
                "exact hsame_left_left",
                "exact hsame_left_right",
                "cases hsame_right",
                "right",
                "split",
                "apply hmul_odd_right",
                "exact hsame_right_left",
                "exact hsame_right_right",
                "rewrite hdivision",
                "exact hpqr",
            ),
            "For odd divisor coefficient p, n=p*q+r is even exactly when q+r is even.",
        ),
        spec(
            "odd_division_odd_iff",
            f"{division_prefix}({odd_division_iff})",
            (
                "odd_multiplier_even_product_iff",
                "odd_multiplier_odd_product_iff",
                "odd_sum_iff_opposite_parity",
            ),
            (
                "intro p",
                "intro q",
                "intro r",
                "intro n",
                "intro hp",
                "intro hdivision",
                f"have hmul_even : {proof_even_mul_iff}",
                "specialize odd_multiplier_even_product_iff p",
                "specialize odd_multiplier_even_product_iff q",
                "apply odd_multiplier_even_product_iff",
                "exact hp",
                f"have hmul_odd : {proof_odd_mul_iff}",
                "specialize odd_multiplier_odd_product_iff p",
                "specialize odd_multiplier_odd_product_iff q",
                "apply odd_multiplier_odd_product_iff",
                "exact hp",
                f"have hleft : {proof_odd_pqr_iff}",
                "specialize odd_sum_iff_opposite_parity (p * q)",
                "specialize odd_sum_iff_opposite_parity r",
                "exact odd_sum_iff_opposite_parity",
                f"have hright : {proof_odd_qr_iff}",
                "specialize odd_sum_iff_opposite_parity q",
                "specialize odd_sum_iff_opposite_parity r",
                "exact odd_sum_iff_opposite_parity",
                "cases hmul_even",
                "cases hmul_odd",
                "cases hleft",
                "cases hright",
                "split",
                "intro hn",
                f"have hpqr : {proof_odd_pqr}",
                "rewrite <- hdivision",
                "exact hn",
                "apply hright_right",
                "have hopposite : " + proof_opposite_pqr,
                "apply hleft_left",
                "exact hpqr",
                "cases hopposite",
                "cases hopposite_left",
                "left",
                "split",
                "apply hmul_even_left",
                "exact hopposite_left_left",
                "exact hopposite_left_right",
                "cases hopposite_right",
                "right",
                "split",
                "apply hmul_odd_left",
                "exact hopposite_right_left",
                "exact hopposite_right_right",
                "intro hqr",
                f"have hpqr : {proof_odd_pqr}",
                "apply hleft_right",
                "have hopposite : " + proof_opposite_qr,
                "apply hright_left",
                "exact hqr",
                "cases hopposite",
                "cases hopposite_left",
                "left",
                "split",
                "apply hmul_even_right",
                "exact hopposite_left_left",
                "exact hopposite_left_right",
                "cases hopposite_right",
                "right",
                "split",
                "apply hmul_odd_right",
                "exact hopposite_right_left",
                "exact hopposite_right_right",
                "rewrite hdivision",
                "exact hpqr",
            ),
            "For odd divisor coefficient p, n=p*q+r is odd exactly when q+r is odd.",
        ),
        spec(
            "odd_division_parity_iff",
            f"{division_prefix}(({even_division_iff}) /\\ ({odd_division_iff}))",
            ("odd_division_even_iff", "odd_division_odd_iff"),
            (
                "intro p",
                "intro q",
                "intro r",
                "intro n",
                "intro hp",
                "intro hdivision",
                "split",
                "specialize odd_division_even_iff p",
                "specialize odd_division_even_iff q",
                "specialize odd_division_even_iff r",
                "specialize odd_division_even_iff n",
                "apply odd_division_even_iff",
                "exact hp",
                "exact hdivision",
                "specialize odd_division_odd_iff p",
                "specialize odd_division_odd_iff q",
                "specialize odd_division_odd_iff r",
                "specialize odd_division_odd_iff n",
                "apply odd_division_odd_iff",
                "exact hp",
                "exact hdivision",
            ),
            "An exact quotient-remainder equation with odd coefficient preserves the complete parity classification.",
        ),
    )


__all__ = ["make_parity_odd_division_candidate_theorems"]
