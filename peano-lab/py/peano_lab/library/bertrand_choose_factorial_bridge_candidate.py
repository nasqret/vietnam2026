"""Constructive complement-form factorial representation of Choose.

The candidate below derives the factorial identity directly from the weighted
vertical Choose recurrence.  Every Choose and factorial occurrence is expanded
into ordinary first-order Peano arithmetic before parsing.  This module creates
no trusted primitive, authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
)
from peano_lab.library.finite_factorial_theorems import factorial_relation


CHOOSE_FACTORIAL_BRIDGE = "choose_factorial_bridge"


def make_bertrand_choose_factorial_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated complement-form Choose-factorial bridge."""

    variables = ("n", "k", "j", "c", "F", "K", "J")
    choose = _choose_relation_term(
        "n",
        "k",
        "c",
        tag="bcfb_choose",
        variables=variables,
    )
    total = factorial_relation("n", "F", tag="bcfb_total")
    left = factorial_relation("k", "K", tag="bcfb_left")
    right = factorial_relation("j", "J", tag="bcfb_right")

    predecessor_choose = _choose_relation_term(
        "n",
        "k",
        "a",
        tag="bcfb_predecessor_choose",
        variables=variables + ("a",),
    )
    predecessor_total = factorial_relation(
        "n", "f", tag="bcfb_predecessor_total"
    )
    predecessor_right = factorial_relation(
        "j", "r", tag="bcfb_predecessor_right"
    )

    script = (
        # Keep the outer induction hypothesis generalized over both indices,
        # all four values, and every relational premise.
        "induction n",
        "intro k",
        "induction j",
        # Row zero, complement zero: the sum forces the column to be zero.
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hk : k = 0",
        "trans k + 0",
        "symm",
        "apply PA3",
        "exact hsum",
        "have hc_one : c = 1",
        "specialize choose_self_of_eq 0",
        "specialize choose_self_of_eq k",
        "specialize choose_self_of_eq c",
        "apply choose_self_of_eq",
        "exact hk",
        "exact hchoose",
        "have hF_one : F = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero F",
        "apply factorial_zero",
        "refl",
        "exact hF",
        "have hK_one : K = 1",
        "specialize factorial_zero k",
        "specialize factorial_zero K",
        "apply factorial_zero",
        "exact hk",
        "exact hK",
        "have hJ_one : J = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero J",
        "apply factorial_zero",
        "refl",
        "exact hJ",
        "rewrite hF_one",
        "rewrite hK_one",
        "rewrite hJ_one",
        "rewrite hc_one",
        "specialize mul_one 1",
        "rewrite mul_one",
        "rewrite mul_one",
        "refl",
        # A positive complement cannot occur in row zero.
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "rewrite PA4 at hsum",
        "exfalso",
        "apply PA1",
        "exact hsum",
        # Successor row, complement zero: transport the column factorial to the
        # diagonal before using factorial functionality.
        "intro k",
        "induction j",
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hk : k = S n",
        "trans k + 0",
        "symm",
        "apply PA3",
        "exact hsum",
        "have hc_one : c = 1",
        "specialize choose_self_of_eq (S n)",
        "specialize choose_self_of_eq k",
        "specialize choose_self_of_eq c",
        "apply choose_self_of_eq",
        "exact hk",
        "exact hchoose",
        "have hJ_one : J = 1",
        "specialize factorial_zero 0",
        "specialize factorial_zero J",
        "apply factorial_zero",
        "refl",
        "exact hJ",
        "have hFK : F = K",
        "specialize factorial_functional (S n)",
        "specialize factorial_functional F",
        "specialize factorial_functional K",
        "apply factorial_functional",
        "exact hF",
        "specialize factorial_length_eq_transport k",
        "specialize factorial_length_eq_transport (S n)",
        "specialize factorial_length_eq_transport K",
        "apply factorial_length_eq_transport",
        "exact hk",
        "exact hK",
        "rewrite hFK",
        "rewrite hJ_one",
        "rewrite hc_one",
        "specialize mul_one K",
        "rewrite mul_one",
        "rewrite mul_one",
        "refl",
        # Successor row and complement: remove one from both, then combine the
        # outer induction hypothesis with the weighted vertical identity.
        "intro c",
        "intro F",
        "intro K",
        "intro J",
        "intro hsum",
        "intro hchoose",
        "intro hF",
        "intro hK",
        "intro hJ",
        "have hprevious_sum : k + j = n",
        "apply PA2",
        "trans k + S j",
        "symm",
        "apply PA4",
        "exact hsum",
        f"have ha_exists : exists a. ({predecessor_choose})",
        "specialize choose_exists n",
        "specialize choose_exists k",
        "exact choose_exists",
        "cases ha_exists",
        "have hweighted : S j * c = S n * x",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical k",
        "specialize choose_weighted_vertical j",
        "specialize choose_weighted_vertical x",
        "specialize choose_weighted_vertical c",
        "apply choose_weighted_vertical",
        "exact hprevious_sum",
        "exact ha_exists_witness",
        "exact hchoose",
        f"have hF_decomp : exists f. ({predecessor_total}) /\\ "
        "F = f * S n",
        "specialize factorial_succ_decompose n",
        "specialize factorial_succ_decompose (S n)",
        "specialize factorial_succ_decompose F",
        "apply factorial_succ_decompose",
        "refl",
        "exact hF",
        "cases hF_decomp",
        "cases hF_decomp_witness",
        f"have hJ_decomp : exists r. ({predecessor_right}) /\\ "
        "J = r * S j",
        "specialize factorial_succ_decompose j",
        "specialize factorial_succ_decompose (S j)",
        "specialize factorial_succ_decompose J",
        "apply factorial_succ_decompose",
        "refl",
        "exact hJ",
        "cases hJ_decomp",
        "cases hJ_decomp_witness",
        "have hbridge : x1 = (K * x2) * x",
        "specialize IH k",
        "specialize IH j",
        "specialize IH x",
        "specialize IH x1",
        "specialize IH K",
        "specialize IH x2",
        "apply IH",
        "exact hprevious_sum",
        "exact ha_exists_witness",
        "exact hF_decomp_witness_left",
        "exact hK",
        "exact hJ_decomp_witness_left",
        "specialize factorial_weighted_product_combine (S j)",
        "specialize factorial_weighted_product_combine (S n)",
        "specialize factorial_weighted_product_combine x",
        "specialize factorial_weighted_product_combine c",
        "specialize factorial_weighted_product_combine x1",
        "specialize factorial_weighted_product_combine K",
        "specialize factorial_weighted_product_combine x2",
        "specialize factorial_weighted_product_combine F",
        "specialize factorial_weighted_product_combine J",
        "apply factorial_weighted_product_combine",
        "exact hJ_decomp_witness_right",
        "exact hF_decomp_witness_right",
        "exact hweighted",
        "exact hbridge",
    )

    return (
        spec(
            CHOOSE_FACTORIAL_BRIDGE,
            "forall n k j c F K J. k + j = n -> "
            f"({choose}) -> ({total}) -> ({left}) -> ({right}) -> "
            "F = (K * J) * c",
            (
                "mul_one",
                "choose_exists",
                "choose_self_of_eq",
                "choose_weighted_vertical",
                "factorial_functional",
                "factorial_zero",
                "factorial_succ_decompose",
                "factorial_length_eq_transport",
                "factorial_weighted_product_combine",
            ),
            script,
            "Complementary factorials represent each constructive Choose value.",
        ),
    )


__all__ = ["make_bertrand_choose_factorial_bridge_candidate_theorems"]
