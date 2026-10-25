"""Constructive positivity for the relational Choose surface.

The candidate below proves positivity directly from Pascal recurrence.  Every
``Choose`` and order occurrence is expanded into ordinary first-order Peano
arithmetic before parsing.  This module creates no trusted primitive,
authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _le_term,
)


CHOOSE_POSITIVE = "choose_positive"


def make_bertrand_choose_positive_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated constructive Choose-positivity candidate."""

    variables = ("n", "k", "z")
    bound = _le_term(
        "k",
        "n",
        tag="bcp_bound",
        variables=variables,
    )
    choose = _choose_relation_term(
        "n",
        "k",
        "z",
        tag="bcp_source",
        variables=variables,
    )
    previous_left = _choose_relation_term(
        "n",
        "k",
        "a",
        tag="bcp_previous_left",
        variables=variables + ("a",),
    )
    previous_right = _choose_relation_term(
        "n",
        "S k",
        "b",
        tag="bcp_previous_right",
        variables=variables + ("b",),
    )

    script = (
        # Induct on the row first so IH is generalized over the column and
        # relational value.  The inner column inductions have unused IHs.
        "induction n",
        "induction k",
        # C(0,0)=1.
        "intro z",
        "intro hbound",
        "intro hchoose",
        "exists 0",
        "specialize choose_zero 0",
        "specialize choose_zero z",
        "apply choose_zero",
        "exact hchoose",
        # No successor column lies below row zero.
        "intro z",
        "intro hbound",
        "intro hchoose",
        "have hk0 : S k = 0",
        "specialize le_zero (S k)",
        "apply le_zero",
        "exact hbound",
        "exfalso",
        "apply PA1",
        "exact hk0",
        # The zero column of every successor row is one.
        "induction k",
        "intro z",
        "intro hbound",
        "intro hchoose",
        "exists 0",
        "specialize choose_zero (S n)",
        "specialize choose_zero z",
        "apply choose_zero",
        "exact hchoose",
        # For an interior successor cell, only the left predecessor needs to
        # be positive.  The right predecessor may be zero on the diagonal.
        "intro z",
        "intro hbound",
        "intro hchoose",
        f"have ha_exists : exists a. ({previous_left})",
        "specialize choose_exists n",
        "specialize choose_exists k",
        "exact choose_exists",
        "cases ha_exists",
        f"have hb_exists : exists b. ({previous_right})",
        "specialize choose_exists n",
        "specialize choose_exists (S k)",
        "exact choose_exists",
        "cases hb_exists",
        "have hpositive : exists p. x = S p",
        "specialize IH k",
        "specialize IH x",
        "apply IH",
        "specialize le_of_succ_le_succ k",
        "specialize le_of_succ_le_succ n",
        "apply le_of_succ_le_succ",
        "exact hbound",
        "exact ha_exists_witness",
        "cases hpositive",
        "have hsum : z = x + x1",
        "specialize choose_succ_succ n",
        "specialize choose_succ_succ k",
        "specialize choose_succ_succ x",
        "specialize choose_succ_succ x1",
        "specialize choose_succ_succ z",
        "apply choose_succ_succ",
        "exact ha_exists_witness",
        "exact hb_exists_witness",
        "exact hchoose",
        "exists x2 + x1",
        "trans x + x1",
        "exact hsum",
        "rewrite hpositive_witness",
        "specialize add_succ_left x2",
        "specialize add_succ_left x1",
        "exact add_succ_left",
    )

    return (
        spec(
            CHOOSE_POSITIVE,
            "forall n k z. "
            f"({bound}) -> ({choose}) -> exists p. z = S p",
            (
                "le_zero",
                "le_of_succ_le_succ",
                "add_succ_left",
                "choose_exists",
                "choose_zero",
                "choose_succ_succ",
            ),
            script,
            "Every in-range relational Choose value is a successor.",
        ),
    )


__all__ = ["make_bertrand_choose_positive_candidate_theorems"]
