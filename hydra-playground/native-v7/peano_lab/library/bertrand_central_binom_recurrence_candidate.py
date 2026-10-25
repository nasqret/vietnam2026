"""Weighted successor recurrence for relational central binomials.

The candidate below combines the checked odd-row middle decomposition with
the constructive weighted vertical identity.  Every authoring abbreviation
expands into ordinary first-order Peano arithmetic before parsing.  This
module creates no trusted primitive, authority enrollment, or checked-use
grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
)


CENTRAL_BINOM_SUCC_RECURRENCE = "central_binom_succ_recurrence"


def make_bertrand_central_binom_recurrence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated weighted central-binomial recurrence candidate."""

    variables = ("n", "c", "d")
    predecessor = _central_binom_relation_term(
        "n",
        "c",
        tag="bcbsr_predecessor",
        variables=variables,
    )
    successor = _central_binom_relation_term(
        "S n",
        "d",
        tag="bcbsr_successor",
        variables=variables,
    )
    middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcbsr_middle",
        variables=variables + ("m",),
    )

    script = (
        "intro n",
        "intro c",
        "intro d",
        "intro hpredecessor",
        "intro hsuccessor",
        f"have hmiddle : exists m. (({middle}) /\\ d = m + m)",
        "specialize central_binom_succ_double_middle n",
        "specialize central_binom_succ_double_middle d",
        "apply central_binom_succ_double_middle",
        "exact hsuccessor",
        "cases hmiddle",
        "cases hmiddle_witness",
        "have hweighted : S n * x = S (n + n) * c",
        "specialize choose_weighted_vertical (n + n)",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical c",
        "specialize choose_weighted_vertical x",
        "apply choose_weighted_vertical",
        "refl",
        "exact hpredecessor",
        "exact hmiddle_witness_left",
        "rewrite hmiddle_witness_right",
        "trans S n * x + S n * x",
        "apply mul_add",
        "rewrite hweighted",
        "rewrite hweighted",
        "trans 2 * (S (n + n) * c)",
        "specialize two_mul_eq_add_self (S (n + n) * c)",
        "symm",
        "exact two_mul_eq_add_self",
        "specialize mul_assoc 2",
        "specialize mul_assoc (S (n + n))",
        "specialize mul_assoc c",
        "symm",
        "exact mul_assoc",
    )

    return (
        spec(
            CENTRAL_BINOM_SUCC_RECURRENCE,
            "forall n c d. "
            f"({predecessor}) -> ({successor}) -> "
            "S n * d = (2 * S (n + n)) * c",
            (
                "mul_add",
                "mul_assoc",
                "two_mul_eq_add_self",
                "central_binom_succ_double_middle",
                "choose_weighted_vertical",
            ),
            script,
            "Successive central binomials satisfy the weighted recurrence.",
        ),
    )


__all__ = ["make_bertrand_central_binom_recurrence_candidate_theorems"]
