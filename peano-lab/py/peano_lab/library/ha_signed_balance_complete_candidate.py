"""Strict-HA completion candidates for canonical signed balance codes.

This second ``SignedBalance`` tranche proves that normalization is
extensional, functional, and detects equality by the zero code.  The
relation is still expanded hygienically into the unchanged first-order
language ``{0,S,+,*,=}``; this module adds neither a parser primitive nor a
trusted definition.

All three specifications are constructive, dependency-curried,
unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_balance_candidate import signed_balance


def make_ha_signed_balance_complete_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the three second-stage ``SignedBalance`` candidates."""

    extensional_left = signed_balance(
        "code1", "left1", "right1", tag="ext_left"
    )
    extensional_right = signed_balance(
        "code2", "left2", "right2", tag="ext_right"
    )
    functional_left = signed_balance(
        "code1", "left", "right", tag="functional_left"
    )
    functional_right = signed_balance(
        "code2", "left", "right", tag="functional_right"
    )
    zero_balance = signed_balance("code", "left", "right", tag="zero")

    return (
        spec(
            "signed_balance_extensional",
            "forall code1 code2 left1 right1 left2 right2. "
            f"({extensional_left}) -> ({extensional_right}) -> "
            "left1 + right2 = right1 + left2 -> code1 = code2",
            (
                "signed_balance_equations_cross_sum",
                "signed_decoded_balance_implies_code_eq",
            ),
            (
                "intro code1",
                "intro code2",
                "intro left1",
                "intro right1",
                "intro left2",
                "intro right2",
                "intro hleft",
                "intro hright",
                "intro hcross",
                "cases hleft",
                "cases hleft_witness",
                "cases hleft_witness_witness",
                "cases hright",
                "cases hright_witness",
                "cases hright_witness_witness",
                "have hdecoded_cross : x + x3 = x1 + x2",
                "specialize signed_balance_equations_cross_sum left1",
                "specialize signed_balance_equations_cross_sum right1",
                "specialize signed_balance_equations_cross_sum x",
                "specialize signed_balance_equations_cross_sum x1",
                "specialize signed_balance_equations_cross_sum left2",
                "specialize signed_balance_equations_cross_sum right2",
                "specialize signed_balance_equations_cross_sum x2",
                "specialize signed_balance_equations_cross_sum x3",
                "apply signed_balance_equations_cross_sum",
                "exact hleft_witness_witness_right",
                "exact hright_witness_witness_right",
                "exact hcross",
                "specialize signed_decoded_balance_implies_code_eq code1",
                "specialize signed_decoded_balance_implies_code_eq x",
                "specialize signed_decoded_balance_implies_code_eq x1",
                "specialize signed_decoded_balance_implies_code_eq code2",
                "specialize signed_decoded_balance_implies_code_eq x2",
                "specialize signed_decoded_balance_implies_code_eq x3",
                "apply signed_decoded_balance_implies_code_eq",
                "exact hleft_witness_witness_left",
                "exact hright_witness_witness_left",
                "exact hdecoded_cross",
            ),
            "Cross-sum-equivalent balanced pairs normalize to the same "
            "canonical signed code.",
        ),
        spec(
            "signed_balance_functional",
            "forall left right code1 code2. "
            f"({functional_left}) -> ({functional_right}) -> code1 = code2",
            (
                "signed_balance_extensional",
                "add_comm",
            ),
            (
                "intro left",
                "intro right",
                "intro code1",
                "intro code2",
                "intro hleft",
                "intro hright",
                "specialize signed_balance_extensional code1",
                "specialize signed_balance_extensional code2",
                "specialize signed_balance_extensional left",
                "specialize signed_balance_extensional right",
                "specialize signed_balance_extensional left",
                "specialize signed_balance_extensional right",
                "apply signed_balance_extensional",
                "exact hleft",
                "exact hright",
                "apply add_comm",
            ),
            "A fixed balanced pair has a unique canonical signed code.",
        ),
        spec(
            "signed_balance_zero_iff",
            f"forall code left right. ({zero_balance}) -> "
            "((code = 0 -> left = right) /\\ (left = right -> code = 0))",
            (
                "signed_decode_functional",
                "signed_balance_functional",
            ),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hbalance",
                "split",
                "intro hcode",
                "cases hbalance",
                "cases hbalance_witness",
                "cases hbalance_witness_witness",
                "have hzero_decode : "
                "((0 = 2 * 0 /\\ 0 = 0) \\/ exists sd_half_zero_explicit. "
                "((0 = 2 * sd_half_zero_explicit + 1 /\\ 0 = 0) /\\ "
                "0 = S sd_half_zero_explicit))",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "have hparts : x = 0 /\\ x1 = 0",
                "specialize signed_decode_functional code",
                "specialize signed_decode_functional x",
                "specialize signed_decode_functional x1",
                "specialize signed_decode_functional 0",
                "specialize signed_decode_functional 0",
                "apply signed_decode_functional",
                "exact hbalance_witness_witness_left",
                "rewrite hcode",
                "rewrite hcode",
                "exact hzero_decode",
                "cases hparts",
                "rewrite hparts_left at hbalance_witness_witness_right",
                "rewrite hparts_right at hbalance_witness_witness_right",
                "rewrite PA3 at hbalance_witness_witness_right",
                "rewrite PA3 at hbalance_witness_witness_right",
                "exact hbalance_witness_witness_right",
                "intro hequal",
                "have hzero_balance : "
                "exists zero_pos zero_neg. "
                "((((0 = 2 * zero_pos /\\ zero_neg = 0) \\/ "
                "exists zero_half. ((0 = 2 * zero_half + 1 /\\ "
                "zero_pos = 0) /\\ zero_neg = S zero_half))) /\\ "
                "left + zero_neg = right + zero_pos)",
                "exists 0",
                "exists 0",
                "split",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "rewrite PA3",
                "rewrite PA3",
                "exact hequal",
                "specialize signed_balance_functional left",
                "specialize signed_balance_functional right",
                "specialize signed_balance_functional code",
                "specialize signed_balance_functional 0",
                "apply signed_balance_functional",
                "exact hbalance",
                "exact hzero_balance",
            ),
            "For a balanced pair, the canonical code is zero exactly when "
            "the two natural components are equal.",
        ),
    )


__all__ = ["make_ha_signed_balance_complete_candidate_theorems"]
