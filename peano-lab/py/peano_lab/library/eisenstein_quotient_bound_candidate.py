"""Odd-half cross-product and Eisenstein quotient bounds.

The elementary strict gap

``(2*k+1)*h < (2*h+1)*(k+1)``

is enough to bound a quotient in a half-range division row.  If ``i<h`` and
``(2*k+1)*(i+1) = (2*h+1)*d+r``, then ``d<=k``.  Neither primality nor a
nonzero remainder is needed for this bound.

Both candidates expand order to additive witnesses in unchanged first-order
Peano arithmetic.  They remain isolated from the public theorem registry and
provide dependency-curried evidence only.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _le_term, _lt_term


def make_eisenstein_quotient_bound_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the odd-half gap and division-quotient bound candidates."""

    cross_gap = _lt_term(
        "(2 * k + 1) * h",
        "(2 * h + 1) * S k",
        tag="odd_half_cross_gap",
        variables=("h", "k"),
    )
    index_bound = _lt_term(
        "i",
        "h",
        tag="odd_half_quotient_index_bound",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    quotient_bound = _le_term(
        "d",
        "k",
        tag="odd_half_quotient_bound",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    reverse_quotient = _lt_term(
        "k",
        "d",
        tag="odd_half_reverse_quotient",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    divisor_product_le = _le_term(
        "p * S k",
        "p * d",
        tag="odd_half_divisor_product_le",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    division_product_le = _le_term(
        "p * d",
        "q * S i",
        tag="odd_half_division_product_le",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    source_product_le = _le_term(
        "q * S i",
        "q * h",
        tag="odd_half_source_product_le",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    combined_product_le = _le_term(
        "p * S k",
        "q * h",
        tag="odd_half_combined_product_le",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )
    shaped_cross_gap = _lt_term(
        "q * h",
        "p * S k",
        tag="odd_half_shaped_cross_gap",
        variables=("p", "q", "h", "k", "i", "d", "r"),
    )

    return (
        spec(
            "odd_half_cross_product_gap",
            f"forall h k. ({cross_gap})",
            (
                "mul_add",
                "add_mul",
                "mul_assoc",
                "mul_comm",
                "add_assoc",
                "add_comm",
                "one_mul",
                "mul_one",
                "mul_succ_left",
            ),
            (
                "intro h",
                "intro k",
                "exists h + k",
                "simp [mul_add, add_mul, mul_assoc, mul_comm, add_assoc, add_comm, one_mul, mul_one, mul_succ_left]",
                "congr",
                "trans (h + k) + (h + (k * h + k * h))",
                "symm",
                "apply add_assoc",
                "trans (k + h) + (h + (k * h + k * h))",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "The odd half-products differ by the explicit positive gap h+k+1.",
        ),
        spec(
            "odd_half_division_quotient_bounded",
            "forall p q h k i d r. p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({index_bound}) -> q * S i = p * d + r -> ({quotient_bound})",
            (
                "odd_half_cross_product_gap",
                "le_or_lt",
                "mul_le_mul_left",
                "le_add_right",
                "le_trans",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro d",
                "intro r",
                "intro hp",
                "intro hq",
                "intro hi",
                "intro hdivision",
                "specialize le_or_lt d",
                "specialize le_or_lt k",
                "cases le_or_lt",
                "exact le_or_lt_left",
                f"have hreverse : {reverse_quotient}",
                "exact le_or_lt_right",
                f"have hdivisor_le : {divisor_product_le}",
                "specialize mul_le_mul_left (S k)",
                "specialize mul_le_mul_left d",
                "specialize mul_le_mul_left p",
                "apply mul_le_mul_left",
                "exact hreverse",
                f"have hdivision_le : {division_product_le}",
                "rewrite hdivision",
                "specialize le_add_right (p * d)",
                "specialize le_add_right r",
                "exact le_add_right",
                f"have hsource_le : {source_product_le}",
                "specialize mul_le_mul_left (S i)",
                "specialize mul_le_mul_left h",
                "specialize mul_le_mul_left q",
                "apply mul_le_mul_left",
                "exact hi",
                f"have hcombined : {combined_product_le}",
                "have htrans_all : forall a b c. (exists t. t + a = b) -> (exists t. t + b = c) -> exists t. t + a = c",
                "exact le_trans",
                "specialize le_trans (p * S k)",
                "specialize le_trans (p * d)",
                "specialize le_trans (q * S i)",
                "have hfirst : exists t. t + (p * S k) = q * S i",
                "apply le_trans",
                "exact hdivisor_le",
                "exact hdivision_le",
                "specialize htrans_all (p * S k)",
                "specialize htrans_all (q * S i)",
                "specialize htrans_all (q * h)",
                "apply htrans_all",
                "exact hfirst",
                "exact hsource_le",
                f"have hcross : {shaped_cross_gap}",
                "rewrite hp",
                "rewrite hq",
                "specialize odd_half_cross_product_gap h",
                "specialize odd_half_cross_product_gap k",
                "exact odd_half_cross_product_gap",
                "exfalso",
                "specialize lt_not_le (q * h)",
                "specialize lt_not_le (p * S k)",
                "apply lt_not_le",
                "exact hcross",
                "exact hcombined",
            ),
            "A division row from the first odd half has quotient at most the second half.",
        ),
    )


__all__ = ["make_eisenstein_quotient_bound_candidate_theorems"]
