"""Constructive power-tail and valuation-order bridges for Bertrand.

The finite Legendre sum stops at exponent ``n``.  Its omitted next quotient is
zero because a prime power ``p^(n+1)`` is strictly larger than ``n``.  This
module records that fact as the exact native quotient/remainder relation with
quotient zero and remainder ``n``.

It also exposes the order-theoretic characterization of the canonical bounded
valuation.  On the intended prime/nonzero domain, a relational power divides
the value exactly when its exponent is at most the selected valuation.  The
reverse implication is stated at its strongest natural generality: it needs
only the valuation graph, since lower relational powers divide by antitonicity.

Every displayed predicate is expanded into the unchanged first-order Peano
language before parsing.  This factory is intentionally unregistered; Alpha
enrollment and publication require a separate review.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_power_valuation_candidate import (
    _power_terms,
    at_most,
    power_divides,
    power_valuation,
)
from .fermat_residue_map_candidate import prime


def _divrem_terms(
    value: str,
    divisor: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
) -> str:
    """Expand the canonical quotient/remainder graph used by the library."""

    return (
        f"({value} = ({divisor}) * ({quotient}) + ({remainder}) /\\ "
        f"exists blvb_remainder_gap_{tag}. "
        f"blvb_remainder_gap_{tag} + S ({remainder}) = ({divisor}))"
    )


def make_bertrand_legendre_valuation_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered tail and valuation bridge tranche."""

    prime_p = prime("p", tag="blvb_prime")
    successor_power = _power_terms(
        "p", "S n", "d", tag="blvb_quotient_tail_power"
    )
    quotient_tail = _divrem_terms(
        "n", "d", "0", "n", tag="blvb_quotient_tail_zero"
    )

    valuation = power_valuation("p", "a", "f", tag="blvb_valuation")
    candidate_divides = power_divides(
        "p", "k", "a", tag="blvb_candidate_divides"
    )
    candidate_bound = at_most("k", "f", tag="blvb_candidate_bound")

    return (
        spec(
            "prime_power_quotient_tail_zero",
            f"forall p n d. ({prime_p}) -> ({successor_power}) -> "
            f"({quotient_tail})",
            ("prime_power_exponent_le", "zero_add"),
            (
                "intro p",
                "intro n",
                "intro d",
                "intro hp",
                "intro hpower",
                "split",
                "symm",
                "trans 0 + n",
                "congr",
                "apply PA5",
                "refl",
                "apply zero_add",
                "specialize prime_power_exponent_le p",
                "specialize prime_power_exponent_le (S n)",
                "specialize prime_power_exponent_le d",
                "apply prime_power_exponent_le",
                "exact hp",
                "exact hpower",
            ),
            "The first omitted prime-power quotient is canonically zero.",
        ),
        spec(
            "prime_power_divides_exponent_le_valuation",
            f"forall p a f k. ({prime_p}) -> ~(a = 0) -> ({valuation}) -> "
            f"({candidate_divides}) -> ({candidate_bound})",
            (
                "prime_power_divides_exponent_le_value",
                "power_valuation_dominates",
            ),
            (
                "intro p",
                "intro a",
                "intro f",
                "intro k",
                "intro hp",
                "intro ha",
                "intro hvaluation",
                "intro hdivides",
                "have hvalue_bound : exists gap. gap + k = a",
                "specialize prime_power_divides_exponent_le_value p",
                "specialize prime_power_divides_exponent_le_value k",
                "specialize prime_power_divides_exponent_le_value a",
                "apply prime_power_divides_exponent_le_value",
                "exact hp",
                "exact ha",
                "exact hdivides",
                "specialize power_valuation_dominates p",
                "specialize power_valuation_dominates a",
                "specialize power_valuation_dominates f",
                "specialize power_valuation_dominates k",
                "apply power_valuation_dominates",
                "exact hvaluation",
                "exact hvalue_bound",
                "exact hdivides",
            ),
            "Every dividing prime-power exponent lies below the valuation.",
        ),
        spec(
            "power_divides_of_exponent_le_valuation",
            f"forall p a f k. ({valuation}) -> ({candidate_bound}) -> "
            f"({candidate_divides})",
            (
                "power_valuation_power_divides",
                "power_divides_exponent_antitone",
            ),
            (
                "intro p",
                "intro a",
                "intro f",
                "intro k",
                "intro hvaluation",
                "intro hbound",
                "have hselected : "
                f"{power_divides('p', 'f', 'a', tag='blvb_selected_divides')}",
                "specialize power_valuation_power_divides p",
                "specialize power_valuation_power_divides a",
                "specialize power_valuation_power_divides f",
                "apply power_valuation_power_divides",
                "exact hvaluation",
                "specialize power_divides_exponent_antitone p",
                "specialize power_divides_exponent_antitone k",
                "specialize power_divides_exponent_antitone f",
                "specialize power_divides_exponent_antitone a",
                "apply power_divides_exponent_antitone",
                "exact hbound",
                "exact hselected",
            ),
            "Every exponent below a valuation exponent supplies a power divisor.",
        ),
    )


__all__ = ["make_bertrand_legendre_valuation_bridge_candidate_theorems"]
