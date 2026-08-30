"""Strict Bertrand endpoint and its factorization boundary.

The first row rules out a prime equal to ``n + n`` when ``1 < n`` by
displaying the factorization ``2 * n``.  The second row applies BP01 and
eliminates its sole closed-endpoint case, yielding the exact frozen BP02
base-language statement.

This module is candidate evidence only.  It grants no registry authority or
edition membership.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b8_prime_certificates_candidate import (
    FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
)
from .bertrand_bp01_candidate import BERTRAND_CLOSED_UPPER
from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .bertrand_primorial_foundation_candidate import _lt_term
from .bertrand_primorial_membership_candidate import _le_term


BERTRAND_UPPER_ENDPOINT_FACTORIZATION = (
    "bertrand_upper_endpoint_factorization"
)
BERTRAND_STRICT = "bertrand_strict"

BERTRAND_STRICT_BASE_SOURCE = (
    "forall n. (exists h. h + S 1 = n) -> exists p. "
    "((~(p = 1) /\\ forall a b. p = a * b -> "
    "a = 1 \\/ b = 1) /\\ ((exists u. u + S n = p) /\\ "
    "(exists v. v + S p = n + n)))"
)


def make_bertrand_bp02_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the endpoint boundary followed by exact BP02."""

    boundary_variables = ("n", "p")
    boundary_lower = _lt_term(
        "1",
        "n",
        tag="bbp02_boundary_lower",
        avoid=boundary_variables,
    )
    boundary_prime = _prime_relation_term(
        "p",
        tag="bbp02_boundary_prime",
        variables=boundary_variables,
    )

    closed_variables = ("n", "x")
    closed_prime = _prime_relation_term(
        "x",
        tag="bbp02_closed_prime",
        variables=closed_variables,
    )
    closed_lower = _lt_term(
        "n",
        "x",
        tag="bbp02_closed_lower",
        avoid=closed_variables,
    )
    closed_upper = _le_term(
        "x",
        "n + n",
        tag="bbp02_closed_upper",
        variables=closed_variables,
    )
    closed_result = (
        f"exists x. ({closed_prime}) /\\ "
        f"(({closed_lower}) /\\ ({closed_upper}))"
    )

    return (
        spec(
            BERTRAND_UPPER_ENDPOINT_FACTORIZATION,
            f"forall n p. ({boundary_lower}) -> "
            f"({boundary_prime}) -> p = n + n -> false",
            (
                "lt_not_le",
                "zero_add",
                "two_mul_eq_add_self",
                FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
            ),
            (
                "intro n",
                "intro p",
                "intro hlower",
                "intro hprime",
                "intro heq",
                "have hn_not_one : ~(n = 1)",
                "intro hn_one",
                "specialize lt_not_le 1",
                "specialize lt_not_le n",
                "apply lt_not_le",
                "exact hlower",
                "exists 0",
                "rewrite hn_one",
                "apply zero_add",
                "have htwo_not_one : ~(2 = 1)",
                "intro htwo_one",
                "apply PA1",
                "apply PA2",
                "exact htwo_one",
                "have hfactor : p = 2 * n",
                "trans n + n",
                "exact heq",
                "symm",
                "specialize two_mul_eq_add_self n",
                "exact two_mul_eq_add_self",
                f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} p",
                f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} 2",
                f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} n",
                f"apply {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME}",
                "exact hfactor",
                "exact htwo_not_one",
                "exact hn_not_one",
                "exact hprime",
            ),
            "The closed upper endpoint is composite whenever 1<n.",
        ),
        spec(
            BERTRAND_STRICT,
            BERTRAND_STRICT_BASE_SOURCE,
            (
                "add_eq_zero_right",
                BERTRAND_CLOSED_UPPER,
                "le_eq_or_lt",
                BERTRAND_UPPER_ENDPOINT_FACTORIZATION,
            ),
            (
                "intro n",
                "intro hlower",
                "have hn_nonzero : ~(n = 0)",
                "intro hn_zero",
                "cases hlower",
                "rewrite hn_zero at hlower_witness",
                "have htwo_zero : 2 = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right 2",
                "apply add_eq_zero_right",
                "exact hlower_witness",
                "apply PA1",
                "exact htwo_zero",
                f"have hclosed : {closed_result}",
                f"specialize {BERTRAND_CLOSED_UPPER} n",
                f"apply {BERTRAND_CLOSED_UPPER}",
                "exact hn_nonzero",
                "cases hclosed",
                "cases hclosed_witness",
                "cases hclosed_witness_right",
                "have hsplit : x = n + n \/ "
                "(exists v. v + S x = n + n)",
                "specialize le_eq_or_lt x",
                "specialize le_eq_or_lt (n + n)",
                "apply le_eq_or_lt",
                "exact hclosed_witness_right_right",
                "cases hsplit",
                "exfalso",
                f"specialize {BERTRAND_UPPER_ENDPOINT_FACTORIZATION} n",
                f"specialize {BERTRAND_UPPER_ENDPOINT_FACTORIZATION} x",
                f"apply {BERTRAND_UPPER_ENDPOINT_FACTORIZATION}",
                "exact hlower",
                "exact hclosed_witness_left",
                "exact hsplit_left",
                "exists x",
                "split",
                "exact hclosed_witness_left",
                "split",
                "exact hclosed_witness_right_left",
                "exact hsplit_right",
            ),
            "Every n greater than one has a prime strictly below n+n.",
        ),
    )


__all__ = [
    "BERTRAND_UPPER_ENDPOINT_FACTORIZATION",
    "BERTRAND_STRICT",
    "BERTRAND_STRICT_BASE_SOURCE",
    "make_bertrand_bp02_candidate_theorems",
]
