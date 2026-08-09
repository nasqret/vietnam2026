"""Constructive equality of factorial valuations and finite Legendre sums.

This isolated gate joins the already checked successor recurrences for
``FactorialVal`` and ``LegendreSum``.  The first row says that equal
predecessor exponents remain equal after adjoining their common valuation
contribution.  The second row performs ordinary Peano induction and obtains
that common predecessor data constructively from the relational existence
theorems.

Factorials, bounded power valuations, primes, beta-coded quotient prefixes,
and finite sums are authoring expansions only.  Both statements parse in the
unchanged first-order Peano language, and both proofs remain intuitionistic.
This module remains deliberately unregistered.  Its focused audit compiles a
root-pruned, self-contained layered certificate and checks the unchanged
empty-context kernel; Alpha enrollment is a separate release step.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_factorial_valuation_candidate import factorial_valuation
from .bertrand_legendre_recurrence_candidate import (
    _successor_legendre_sum_terms,
)
from .bertrand_legendre_sum_candidate import legendre_sum
from .bertrand_legendre_successor_candidate import _power_valuation_terms
from .bertrand_power_valuation_candidate import power_valuation
from .fermat_residue_map_candidate import prime
from .finite_factorial_theorems import factorial_relation


def _successor_factorial_terms(
    predecessor: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``Factorial(S predecessor,result)`` through a private marker."""

    marker = f"blfgsuccessorlength{tag}"
    expanded = factorial_relation(marker, result, tag=tag)
    if expanded.count(marker) != 4:
        raise AssertionError("unexpected successor-factorial length expansion")
    return expanded.replace(marker, f"S {predecessor}")


def _successor_factorial_valuation_terms(
    base: str,
    predecessor: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    value = f"blfg_factorial_{tag}"
    factorial = _successor_factorial_terms(
        predecessor,
        value,
        tag=f"{tag}_factorial",
    )
    valuation = power_valuation(
        base,
        value,
        exponent,
        tag=f"{tag}_valuation",
    )
    return f"exists {value}. (({factorial}) /\\ ({valuation}))"


def make_bertrand_factorial_legendre_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build successor agreement followed by the induction capstone."""

    agreement_prime = prime("p", tag="blfg_agreement_prime")
    agreement_factorial_old = factorial_valuation(
        "p", "n", "a", tag="blfg_agreement_factorial_old"
    )
    agreement_factorial_new = _successor_factorial_valuation_terms(
        "p", "n", "b", tag="blfg_agreement_factorial_new"
    )
    agreement_contribution = _power_valuation_terms(
        "p", "S n", "f", tag="blfg_agreement_contribution"
    )
    agreement_legendre_old = legendre_sum(
        "p", "n", "c", tag="blfg_agreement_legendre_old"
    )
    agreement_legendre_new = _successor_legendre_sum_terms(
        "p", "n", "d", tag="blfg_agreement_legendre_new"
    )

    equality_prime = prime("p", tag="blfg_equality_prime")
    equality_factorial = factorial_valuation(
        "p", "n", "a", tag="blfg_equality_factorial"
    )
    equality_legendre = legendre_sum(
        "p", "n", "b", tag="blfg_equality_legendre"
    )

    return (
        spec(
            "factorial_legendre_successor_agreement",
            "forall p n a b c d f. "
            f"({agreement_prime}) -> ({agreement_factorial_old}) -> "
            f"({agreement_factorial_new}) -> ({agreement_contribution}) -> "
            f"({agreement_legendre_old}) -> ({agreement_legendre_new}) -> "
            "a = c -> b = d",
            (
                "prime_factorial_valuation_succ",
                "prime_legendre_sum_succ",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro f",
                "intro hp",
                "intro hfactorial_old",
                "intro hfactorial_new",
                "intro hcontribution",
                "intro hlegendre_old",
                "intro hlegendre_new",
                "intro hagreement",
                "have hfactorial_step : b = a + f",
                "specialize prime_factorial_valuation_succ p",
                "specialize prime_factorial_valuation_succ n",
                "specialize prime_factorial_valuation_succ (S n)",
                "specialize prime_factorial_valuation_succ a",
                "specialize prime_factorial_valuation_succ f",
                "specialize prime_factorial_valuation_succ b",
                "apply prime_factorial_valuation_succ",
                "refl",
                "exact hp",
                "exact hfactorial_old",
                "exact hcontribution",
                "exact hfactorial_new",
                "have hlegendre_step : d = c + f",
                "specialize prime_legendre_sum_succ p",
                "specialize prime_legendre_sum_succ n",
                "specialize prime_legendre_sum_succ f",
                "specialize prime_legendre_sum_succ c",
                "specialize prime_legendre_sum_succ d",
                "apply prime_legendre_sum_succ",
                "exact hp",
                "exact hcontribution",
                "exact hlegendre_old",
                "exact hlegendre_new",
                "trans a + f",
                "exact hfactorial_step",
                "trans c + f",
                "rewrite hagreement",
                "refl",
                "symm",
                "exact hlegendre_step",
            ),
            "Factorial and Legendre successor recurrences preserve predecessor agreement.",
        ),
        spec(
            "prime_factorial_valuation_eq_legendre_sum",
            "forall p n a b. "
            f"({equality_prime}) -> ({equality_factorial}) -> "
            f"({equality_legendre}) -> a = b",
            (
                "prime_factorial_valuation_zero",
                "legendre_sum_zero",
                "factorial_valuation_exists",
                "prime_legendre_sum_exists",
                "power_valuation_exists",
                "factorial_legendre_successor_agreement",
            ),
            (
                "intro p",
                "induction n",
                "intro a",
                "intro b",
                "intro hp",
                "intro hfactorial",
                "intro hlegendre",
                "have ha : a = 0",
                "specialize prime_factorial_valuation_zero p",
                "specialize prime_factorial_valuation_zero 0",
                "specialize prime_factorial_valuation_zero a",
                "apply prime_factorial_valuation_zero",
                "refl",
                "exact hp",
                "exact hfactorial",
                "have hb : b = 0",
                "specialize legendre_sum_zero p",
                "specialize legendre_sum_zero 0",
                "specialize legendre_sum_zero b",
                "apply legendre_sum_zero",
                "refl",
                "exact hlegendre",
                "trans 0",
                "exact ha",
                "symm",
                "exact hb",
                "intro a",
                "intro b",
                "intro hp",
                "intro hfactorial",
                "intro hlegendre",
                "have hfactorial_old : exists e. "
                + factorial_valuation(
                    "p", "n", "e", tag="blfg_induction_factorial_old"
                ),
                "specialize factorial_valuation_exists p",
                "specialize factorial_valuation_exists n",
                "exact factorial_valuation_exists",
                "cases hfactorial_old",
                "have hlegendre_old : exists s. "
                + legendre_sum(
                    "p", "n", "s", tag="blfg_induction_legendre_old"
                ),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists n",
                "apply prime_legendre_sum_exists",
                "exact hp",
                "cases hlegendre_old",
                "have hcontribution : exists f. "
                + _power_valuation_terms(
                    "p", "S n", "f", tag="blfg_induction_contribution"
                ),
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists (S n)",
                "exact power_valuation_exists",
                "cases hcontribution",
                "have hpredecessor_agreement : x = x1",
                "specialize IH x",
                "specialize IH x1",
                "apply IH",
                "exact hp",
                "exact hfactorial_old_witness",
                "exact hlegendre_old_witness",
                "specialize factorial_legendre_successor_agreement p",
                "specialize factorial_legendre_successor_agreement n",
                "specialize factorial_legendre_successor_agreement x",
                "specialize factorial_legendre_successor_agreement a",
                "specialize factorial_legendre_successor_agreement x1",
                "specialize factorial_legendre_successor_agreement b",
                "specialize factorial_legendre_successor_agreement x2",
                "apply factorial_legendre_successor_agreement",
                "exact hp",
                "exact hfactorial_old_witness",
                "exact hfactorial",
                "exact hcontribution_witness",
                "exact hlegendre_old_witness",
                "exact hlegendre",
                "exact hpredecessor_agreement",
            ),
            "At every prime, the factorial valuation exponent equals the finite Legendre sum.",
        ),
    )


__all__ = ["make_bertrand_factorial_legendre_candidate_theorems"]
