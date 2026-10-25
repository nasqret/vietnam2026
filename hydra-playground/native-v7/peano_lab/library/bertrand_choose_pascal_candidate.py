"""Unconditional Pascal recurrence for the relational Choose surface.

The single candidate below combines the already checked interior, diagonal,
and out-of-range laws.  All ``Choose`` notation is expanded into ordinary
first-order Peano arithmetic before parsing.  This module creates no trusted
primitive, authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _lt_term,
)


CHOOSE_SUCC_SUCC = "choose_succ_succ"


def make_bertrand_choose_pascal_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated unconditional Pascal-recurrence candidate."""

    variables = ("n", "k", "x", "y", "z")
    left_choose = _choose_relation_term(
        "n",
        "k",
        "x",
        tag="bcss_left",
        variables=variables,
    )
    right_choose = _choose_relation_term(
        "n",
        "S k",
        "y",
        tag="bcss_right",
        variables=variables,
    )
    result_choose = _choose_relation_term(
        "S n",
        "S k",
        "z",
        tag="bcss_result",
        variables=variables,
    )
    equality_right_bound = _lt_term(
        "n",
        "S k",
        tag="bcss_equality_right_bound",
        variables=variables,
    )
    above_right_bound = _lt_term(
        "n",
        "S k",
        tag="bcss_above_right_bound",
        variables=variables,
    )
    above_result_bound = _lt_term(
        "S n",
        "S k",
        tag="bcss_above_result_bound",
        variables=variables,
    )

    script = (
        "intro n",
        "intro k",
        "intro x",
        "intro y",
        "intro z",
        "intro hleft",
        "intro hright",
        "intro hresult",
        "specialize lt_trichotomy k",
        "specialize lt_trichotomy n",
        "cases lt_trichotomy",
        # k = n.  Each expanded Choose has exactly four free k
        # occurrences.  Keep all eight large transports inside their value
        # subproofs so the rewritten packages do not pollute the continuation.
        "have hx : x = 1",
        "specialize choose_self n",
        "specialize choose_self x",
        "apply choose_self",
        "rewrite lt_trichotomy_left at hleft",
        "rewrite lt_trichotomy_left at hleft",
        "rewrite lt_trichotomy_left at hleft",
        "rewrite lt_trichotomy_left at hleft",
        "exact hleft",
        "have hz : z = 1",
        "specialize choose_self (S n)",
        "specialize choose_self z",
        "apply choose_self",
        "rewrite lt_trichotomy_left at hresult",
        "rewrite lt_trichotomy_left at hresult",
        "rewrite lt_trichotomy_left at hresult",
        "rewrite lt_trichotomy_left at hresult",
        "exact hresult",
        f"have hequality_right_bound : {equality_right_bound}",
        "rewrite lt_trichotomy_left",
        "specialize le_refl (S n)",
        "exact le_refl",
        "have hy : y = 0",
        "specialize choose_out_of_range_zero n",
        "specialize choose_out_of_range_zero (S k)",
        "specialize choose_out_of_range_zero y",
        "apply choose_out_of_range_zero",
        "exact hequality_right_bound",
        "exact hright",
        "rewrite hx",
        "rewrite hy",
        "trans 1",
        "exact hz",
        "symm",
        "apply PA3",
        # The remaining trichotomy branch is k < n or n < k.
        "cases lt_trichotomy_right",
        "specialize choose_succ_succ_of_lt n",
        "specialize choose_succ_succ_of_lt k",
        "specialize choose_succ_succ_of_lt x",
        "specialize choose_succ_succ_of_lt y",
        "specialize choose_succ_succ_of_lt z",
        "apply choose_succ_succ_of_lt",
        "exact lt_trichotomy_right_left",
        "exact hleft",
        "exact hright",
        "exact hresult",
        # n < k.  All three relational values are out of range.
        "have hx : x = 0",
        "specialize choose_out_of_range_zero n",
        "specialize choose_out_of_range_zero k",
        "specialize choose_out_of_range_zero x",
        "apply choose_out_of_range_zero",
        "exact lt_trichotomy_right_right",
        "exact hleft",
        f"have habove_right_bound : {above_right_bound}",
        "specialize le_succ (S n)",
        "specialize le_succ k",
        "apply le_succ",
        "exact lt_trichotomy_right_right",
        "have hy : y = 0",
        "specialize choose_out_of_range_zero n",
        "specialize choose_out_of_range_zero (S k)",
        "specialize choose_out_of_range_zero y",
        "apply choose_out_of_range_zero",
        "exact habove_right_bound",
        "exact hright",
        f"have habove_result_bound : {above_result_bound}",
        "specialize succ_le_succ (S n)",
        "specialize succ_le_succ k",
        "apply succ_le_succ",
        "exact lt_trichotomy_right_right",
        "have hz : z = 0",
        "specialize choose_out_of_range_zero (S n)",
        "specialize choose_out_of_range_zero (S k)",
        "specialize choose_out_of_range_zero z",
        "apply choose_out_of_range_zero",
        "exact habove_result_bound",
        "exact hresult",
        "rewrite hx",
        "rewrite hy",
        "trans 0",
        "exact hz",
        "symm",
        "apply PA3",
    )

    return (
        spec(
            CHOOSE_SUCC_SUCC,
            "forall n k x y z. "
            f"({left_choose}) -> ({right_choose}) -> "
            f"({result_choose}) -> z = x + y",
            (
                "lt_trichotomy",
                "le_refl",
                "le_succ",
                "succ_le_succ",
                "choose_out_of_range_zero",
                "choose_self",
                "choose_succ_succ_of_lt",
            ),
            script,
            "Relational Choose values satisfy Pascal recurrence everywhere.",
        ),
    )


__all__ = ["make_bertrand_choose_pascal_candidate_theorems"]
