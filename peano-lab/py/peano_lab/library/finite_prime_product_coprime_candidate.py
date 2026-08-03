"""Coprimality of finite products of positive residues below a prime.

This isolated candidate supplies the cancellation boundary shared by Gauss,
Euler, and Wilson arguments.  Its readable relations are only hygienic surface
expansions: the resulting proposition and proof still use the unchanged
first-order language of Peano arithmetic.

The module is deliberately absent from the public theorem registry pending an
independent recursive replay and mutation audit.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation
from .fermat_residue_product_candidate import (
    coprime,
    pointwise_coprime,
    prime,
    strictly_below,
)


def positive_below_prime_prefix(
    code: str,
    scale: str,
    length: str,
    modulus: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise nonzero and strict-modulus bounds on a beta prefix."""

    index = f"fppc_index_{tag}"
    factor = f"fppc_factor_{tag}"
    index_bound = strictly_below(index, length, tag=f"{tag}_index_bound")
    factor_bound = strictly_below(factor, modulus, tag=f"{tag}_factor_bound")
    decoded = beta_at(code, scale, index, factor, tag=f"fppc_{tag}_decoded")
    return (
        f"forall {index} {factor}. ({index_bound}) -> ({decoded}) -> "
        f"(~({factor} = 0) /\\ ({factor_bound}))"
    )


def make_finite_prime_product_coprime_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the generic prime-product cancellation prerequisite."""

    bounded = positive_below_prime_prefix(
        "b", "c", "l", "p", tag="prime_product_bounds"
    )
    pointwise = pointwise_coprime(
        "b", "c", "l", "p", tag="prime_product_pointwise"
    )
    product = product_relation(
        "b", "c", "l", "F", tag="prime_product_product"
    )
    prime_p = prime("p", tag="prime_product_prime")
    result = coprime("F", "p", tag="prime_product_result")
    factor_prime_coprime = coprime("p", "x", tag="prime_product_factor")

    return (
        spec(
            "prime_positive_bounded_product_coprime",
            f"forall p b c l F. ({prime_p}) -> ({bounded}) -> "
            f"({product}) -> ({result})",
            (
                "divisor_le_nonzero",
                "lt_not_le",
                "prime_not_divides_coprime",
                "coprime_symm",
                "beta_product_pointwise_coprime",
            ),
            (
                "intro p",
                "intro b",
                "intro c",
                "intro l",
                "intro F",
                "intro hp",
                "intro hbounded",
                "intro hproduct",
                f"have hpointwise : {pointwise}",
                "intro i",
                "intro x",
                "intro hi",
                "intro hx",
                "have hbounds : (~(x = 0) /\\ "
                f"({strictly_below('x', 'p', tag='prime_product_local_bound')}))",
                "specialize hbounded i",
                "specialize hbounded x",
                "apply hbounded",
                "exact hi",
                "exact hx",
                "cases hbounds",
                "have hnotdiv : ~(exists k. x = p * k)",
                "intro hdiv",
                "have hle : exists k. k + p = x",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero x",
                "apply divisor_le_nonzero",
                "exact hbounds_left",
                "exact hdiv",
                "specialize lt_not_le x",
                "specialize lt_not_le p",
                "apply lt_not_le",
                "exact hbounds_right",
                "exact hle",
                f"have hprimecop : {factor_prime_coprime}",
                "specialize prime_not_divides_coprime p",
                "specialize prime_not_divides_coprime x",
                "apply prime_not_divides_coprime",
                "exact hp",
                "exact hnotdiv",
                "specialize coprime_symm p",
                "specialize coprime_symm x",
                "apply coprime_symm",
                "exact hprimecop",
                "specialize beta_product_pointwise_coprime p",
                "specialize beta_product_pointwise_coprime b",
                "specialize beta_product_pointwise_coprime c",
                "specialize beta_product_pointwise_coprime l",
                "specialize beta_product_pointwise_coprime F",
                "apply beta_product_pointwise_coprime",
                "exact hpointwise",
                "exact hproduct",
            ),
            "A product of positive residues below a prime is coprime to that prime.",
        ),
    )


__all__ = [
    "make_finite_prime_product_coprime_candidate_theorems",
    "positive_below_prime_prefix",
]
