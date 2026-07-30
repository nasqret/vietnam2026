"""Coprimality boundary for the canonical Gauss magnitude product.

Magnitudes in a signed half-range lie in ``1,...,h``.  For an odd modulus
``p = 2*h + 1`` they are therefore positive residues below ``p``; the generic
finite prime-product theorem then makes their product cancellable modulo
``p``.  All named relations expand before parsing, and these candidates are
not registered in the public library.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation
from .finite_prime_product_coprime_candidate import (
    positive_below_prime_prefix,
)
from .fermat_residue_product_candidate import coprime, prime, strictly_below
from .gauss_magnitude_permutation_candidate import magnitude_range_prefix
from .gauss_signed_prefix_candidate import (
    _strictly_below_term,
    _weakly_below_term,
)


def make_gauss_magnitude_coprime_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the odd-half bound and magnitude-product coprimality specs."""

    half_below = strictly_below("h", "p", tag="magnitude_half_below")
    magnitude_range = magnitude_range_prefix(
        "mb", "mc", "h", "h", tag="magnitude_coprime_range"
    )
    bounded = positive_below_prime_prefix(
        "mb", "mc", "h", "p", tag="magnitude_coprime_bounds"
    )
    product = product_relation(
        "mb", "mc", "h", "P", tag="magnitude_coprime_product"
    )
    prime_p = prime("p", tag="magnitude_coprime_prime")
    result = coprime("P", "p", tag="magnitude_coprime_result")
    entry = beta_at("mb", "mc", "i", "x", tag="magnitude_coprime_entry")
    decoded = beta_at(
        "mb",
        "mc",
        "i",
        "x1",
        tag="gmp_magnitude_coprime_range_decoded",
    )
    local_variables = ("p", "h", "mb", "mc", "i", "x", "x1")
    positive = _strictly_below_term(
        "0",
        "x1",
        tag="magnitude_coprime_range_positive",
        variables=local_variables,
    )
    weak_bound = _weakly_below_term(
        "x1",
        "h",
        tag="magnitude_coprime_range_bounded",
        variables=local_variables,
    )
    below = strictly_below("x", "p", tag="magnitude_coprime_local_below")

    return (
        spec(
            "odd_half_strictly_below_modulus",
            f"forall p h. p = 2 * h + 1 -> ({half_below})",
            (
                "mul_succ_left",
                "mul_zero_left",
                "zero_add",
                "add_succ_left",
                "add_assoc",
            ),
            (
                "intro p",
                "intro h",
                "intro hp",
                "exists h",
                "rewrite hp",
                "simp [mul_succ_left, mul_zero_left, zero_add, add_succ_left, add_assoc]",
            ),
            "The half of an odd modulus p=2h+1 is strictly below p.",
        ),
        spec(
            "gauss_magnitude_positive_below_prime",
            "forall p h mb mc. p = 2 * h + 1 -> "
            f"({magnitude_range}) -> ({bounded})",
            (
                "odd_half_strictly_below_modulus",
                "beta_at_unique",
                "lt_irrefl_expanded",
                "lt_of_le_of_lt",
            ),
            (
                "intro p",
                "intro h",
                "intro mb",
                "intro mc",
                "intro hp",
                "intro hrange",
                f"have hhalf : {half_below}",
                "specialize odd_half_strictly_below_modulus p",
                "specialize odd_half_strictly_below_modulus h",
                "apply odd_half_strictly_below_modulus",
                "exact hp",
                "intro i",
                "intro x",
                "intro hi",
                f"intro hentry",
                "specialize hrange i",
                "have hdata : exists x1. "
                f"(({decoded}) /\\ (({positive}) /\\ ({weak_bound})))",
                "apply hrange",
                "exact hi",
                "cases hdata",
                "cases hdata_witness",
                "cases hdata_witness_right",
                "have hxeq : x = x1",
                "specialize beta_at_unique mb",
                "specialize beta_at_unique mc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hentry",
                "exact hdata_witness_left",
                "split",
                "intro hxzero",
                "specialize lt_irrefl_expanded 0",
                "apply lt_irrefl_expanded",
                "rewrite <- hxeq at hdata_witness_right_left",
                "rewrite hxzero at hdata_witness_right_left",
                "exact hdata_witness_right_left",
                f"have hxbelow : {below}",
                "specialize lt_of_le_of_lt x",
                "specialize lt_of_le_of_lt h",
                "specialize lt_of_le_of_lt p",
                "apply lt_of_le_of_lt",
                "rewrite hxeq",
                "exact hdata_witness_right_right",
                "exact hhalf",
                "exact hxbelow",
            ),
            "Every Gauss magnitude is a positive residue strictly below its odd modulus.",
        ),
        spec(
            "gauss_magnitude_product_coprime",
            "forall p h mb mc P. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({magnitude_range}) -> ({product}) -> ({result})",
            (
                "gauss_magnitude_positive_below_prime",
                "prime_positive_bounded_product_coprime",
            ),
            (
                "intro p",
                "intro h",
                "intro mb",
                "intro mc",
                "intro P",
                "intro hpodd",
                "intro hp",
                "intro hrange",
                "intro hproduct",
                f"have hbounded : {bounded}",
                "specialize gauss_magnitude_positive_below_prime p",
                "specialize gauss_magnitude_positive_below_prime h",
                "specialize gauss_magnitude_positive_below_prime mb",
                "specialize gauss_magnitude_positive_below_prime mc",
                "apply gauss_magnitude_positive_below_prime",
                "exact hpodd",
                "exact hrange",
                "specialize prime_positive_bounded_product_coprime p",
                "specialize prime_positive_bounded_product_coprime mb",
                "specialize prime_positive_bounded_product_coprime mc",
                "specialize prime_positive_bounded_product_coprime h",
                "specialize prime_positive_bounded_product_coprime P",
                "apply prime_positive_bounded_product_coprime",
                "exact hp",
                "exact hbounded",
                "exact hproduct",
            ),
            "The product of the positive Gauss magnitudes is coprime to the prime modulus.",
        ),
    )


__all__ = ["make_gauss_magnitude_coprime_candidate_theorems"]
