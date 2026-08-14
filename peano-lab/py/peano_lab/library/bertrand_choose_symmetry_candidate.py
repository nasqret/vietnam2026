"""Diagonal transport support for constructive Choose symmetry.

The candidate below remains outside Stable and Alpha authority.  It transports
an extensionally equal column to the checked diagonal law by reconstructing the
expanded Choose package branch by branch.  No trusted primitive, authority
enrollment, or checked-use grant is created here.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
)


CHOOSE_SELF_OF_EQ = "choose_self_of_eq"
CHOOSE_SYMMETRY = "choose_symmetry"


def make_bertrand_choose_symmetry_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated diagonal-transport support candidate."""

    variables = ("n", "k", "z")
    choose = _choose_relation_term(
        "n",
        "k",
        "z",
        tag="bcse_source",
        variables=variables,
    )

    script = (
        "intro n",
        "intro k",
        "intro z",
        "intro heq",
        "intro hchoose",
        "specialize choose_self n",
        "specialize choose_self z",
        "apply choose_self",
        # Rebuild Choose(n,n,z) without rewriting the whole relation.
        "cases hchoose",
        "cases hchoose_left",
        "left",
        "split",
        "rewrite heq at hchoose_left_left",
        "exact hchoose_left_left",
        "exact hchoose_left_right",
        "cases hchoose_right",
        "right",
        "split",
        "rewrite heq at hchoose_right_left",
        "exact hchoose_right_left",
        # Expose the six package witnesses and its three nested conjunctions.
        "cases hchoose_right_right",
        "cases hchoose_right_right_witness",
        "cases hchoose_right_right_witness_witness",
        "cases hchoose_right_right_witness_witness_witness",
        (
            "cases hchoose_right_right_witness_witness_witness_"
            "witness"
        ),
        (
            "cases hchoose_right_right_witness_witness_witness_"
            "witness_witness"
        ),
        (
            "cases hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness"
        ),
        (
            "cases hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_right"
        ),
        (
            "cases hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_right_right"
        ),
        "exists x",
        "exists x1",
        "exists x2",
        "exists x3",
        "exists x4",
        "exists x5",
        "split",
        (
            "exact hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_left"
        ),
        "split",
        (
            "exact hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_right_left"
        ),
        "split",
        (
            "exact hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_right_right_left"
        ),
        (
            "rewrite heq at hchoose_right_right_witness_witness_"
            "witness_witness_witness_witness_right_right_right"
        ),
        (
            "rewrite heq at hchoose_right_right_witness_witness_"
            "witness_witness_witness_witness_right_right_right"
        ),
        (
            "exact hchoose_right_right_witness_witness_witness_"
            "witness_witness_witness_right_right_right"
        ),
    )

    symmetry_variables = ("n", "k", "j", "x", "y")
    symmetry_left = _choose_relation_term(
        "n",
        "k",
        "x",
        tag="bcsym_left",
        variables=symmetry_variables,
    )
    symmetry_right = _choose_relation_term(
        "n",
        "j",
        "y",
        tag="bcsym_right",
        variables=symmetry_variables,
    )
    previous_left = _choose_relation_term(
        "n",
        "k",
        "a",
        tag="bcs_previous_left",
        variables=symmetry_variables + ("a",),
    )
    current_left = _choose_relation_term(
        "n",
        "S k",
        "b",
        tag="bcs_current_left",
        variables=symmetry_variables + ("b",),
    )
    previous_right = _choose_relation_term(
        "n",
        "j",
        "c",
        tag="bcs_previous_right",
        variables=symmetry_variables + ("c",),
    )
    current_right = _choose_relation_term(
        "n",
        "S j",
        "d",
        tag="bcs_current_right",
        variables=symmetry_variables + ("d",),
    )

    symmetry_script = (
        # The row induction comes first, so IH remains generalized over both
        # columns and both relational values.
        "induction n",
        # Row zero, left column zero.
        "induction k",
        "induction j",
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        "have hx : x = 1",
        "specialize choose_zero 0",
        "specialize choose_zero x",
        "apply choose_zero",
        "exact hleft",
        "have hy : y = 1",
        "specialize choose_zero 0",
        "specialize choose_zero y",
        "apply choose_zero",
        "exact hright",
        "trans 1",
        "exact hx",
        "symm",
        "exact hy",
        # The complementary column cannot be positive in row zero.
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        "specialize zero_add (S j)",
        "rewrite zero_add at hsum",
        "exfalso",
        "apply PA1",
        "exact hsum",
        # Nor can the left column itself be positive in row zero.
        "intro j",
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        "specialize add_succ_left k",
        "specialize add_succ_left j",
        "rewrite add_succ_left at hsum",
        "exfalso",
        "apply PA1",
        "exact hsum",
        # Successor row, left column zero.
        "induction k",
        "intro j",
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        "have hx : x = 1",
        "specialize choose_zero (S n)",
        "specialize choose_zero x",
        "apply choose_zero",
        "exact hleft",
        "have hj : j = S n",
        "trans 0 + j",
        "symm",
        "apply zero_add",
        "exact hsum",
        "have hy : y = 1",
        "specialize choose_self_of_eq (S n)",
        "specialize choose_self_of_eq j",
        "specialize choose_self_of_eq y",
        "apply choose_self_of_eq",
        "exact hj",
        "exact hright",
        "trans 1",
        "exact hx",
        "symm",
        "exact hy",
        # Successor row and successor left column, right column zero.
        "induction j",
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        "have hk : S k = S n",
        "rewrite PA3 at hsum",
        "exact hsum",
        "have hx : x = 1",
        "specialize choose_self_of_eq (S n)",
        "specialize choose_self_of_eq (S k)",
        "specialize choose_self_of_eq x",
        "apply choose_self_of_eq",
        "exact hk",
        "exact hleft",
        "have hy : y = 1",
        "specialize choose_zero (S n)",
        "specialize choose_zero y",
        "apply choose_zero",
        "exact hright",
        "trans 1",
        "exact hx",
        "symm",
        "exact hy",
        # Interior successor/successor case.  Each existential is obtained in
        # an isolated local subgoal, so eliminating it remains inferable.
        "intro x",
        "intro y",
        "intro hsum",
        "intro hleft",
        "intro hright",
        f"have ha_exists : exists a. ({previous_left})",
        "specialize choose_exists n",
        "specialize choose_exists k",
        "exact choose_exists",
        "cases ha_exists",
        f"have hb_exists : exists b. ({current_left})",
        "specialize choose_exists n",
        "specialize choose_exists (S k)",
        "exact choose_exists",
        "cases hb_exists",
        f"have hc_exists : exists c. ({previous_right})",
        "specialize choose_exists n",
        "specialize choose_exists j",
        "exact choose_exists",
        "cases hc_exists",
        f"have hd_exists : exists d. ({current_right})",
        "specialize choose_exists n",
        "specialize choose_exists (S j)",
        "exact choose_exists",
        "cases hd_exists",
        "have hleft_complement : S k + j = n",
        "apply PA2",
        "trans S k + S j",
        "symm",
        "apply PA4",
        "exact hsum",
        "have hright_complement : k + S j = n",
        "trans S (k + j)",
        "apply PA4",
        "trans S k + j",
        "symm",
        "apply add_succ_left",
        "exact hleft_complement",
        "have hx_sum : x = x1 + x2",
        "specialize choose_succ_succ n",
        "specialize choose_succ_succ k",
        "specialize choose_succ_succ x1",
        "specialize choose_succ_succ x2",
        "specialize choose_succ_succ x",
        "apply choose_succ_succ",
        "exact ha_exists_witness",
        "exact hb_exists_witness",
        "exact hleft",
        "have hy_sum : y = x3 + x4",
        "specialize choose_succ_succ n",
        "specialize choose_succ_succ j",
        "specialize choose_succ_succ x3",
        "specialize choose_succ_succ x4",
        "specialize choose_succ_succ y",
        "apply choose_succ_succ",
        "exact hc_exists_witness",
        "exact hd_exists_witness",
        "exact hright",
        "have hfirst : x1 = x4",
        "specialize IH k",
        "specialize IH (S j)",
        "specialize IH x1",
        "specialize IH x4",
        "apply IH",
        "exact hright_complement",
        "exact ha_exists_witness",
        "exact hd_exists_witness",
        "have hsecond : x2 = x3",
        "specialize IH (S k)",
        "specialize IH j",
        "specialize IH x2",
        "specialize IH x3",
        "apply IH",
        "exact hleft_complement",
        "exact hb_exists_witness",
        "exact hc_exists_witness",
        "rewrite hx_sum",
        "rewrite hy_sum",
        "rewrite hfirst",
        "rewrite hsecond",
        "apply add_comm",
    )

    return (
        spec(
            CHOOSE_SELF_OF_EQ,
            "forall n k z. k = n -> "
            f"({choose}) -> z = 1",
            ("choose_self",),
            script,
            "A column equal to its row has Choose value one.",
        ),
        spec(
            CHOOSE_SYMMETRY,
            "forall n k j x y. k + j = n -> "
            f"({symmetry_left}) -> ({symmetry_right}) -> x = y",
            (
                "zero_add",
                "add_succ_left",
                "add_comm",
                "choose_exists",
                "choose_zero",
                CHOOSE_SELF_OF_EQ,
                "choose_succ_succ",
            ),
            symmetry_script,
            "Complementary columns have equal relational Choose values.",
        ),
    )


__all__ = ["make_bertrand_choose_symmetry_candidate_theorems"]
