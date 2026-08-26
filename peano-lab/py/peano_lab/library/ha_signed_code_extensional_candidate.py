"""Strict-HA extensionality candidates for canonical signed codes.

The canonical decoder represents a code by normalized natural parts
``pos`` and ``neg``.  For two decoded codes, equality of their represented
integers is the subtraction-free cross-sum equation
``pos1 + neg2 = neg1 + pos2``.  This module proves that this semantic
equality is equivalent to literal equality of the canonical natural codes.

All statements expand ``SignedDecode`` hygienically to the unchanged
first-order language ``{0,S,+,*,=}``.  The candidates are constructive,
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_decode_candidate import signed_decode


def make_ha_signed_code_extensional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build both semantic/code equality directions and their conjunction."""

    left_decode = signed_decode("code1", "pos1", "neg1", tag="extensional_left")
    right_decode = signed_decode(
        "code2", "pos2", "neg2", tag="extensional_right"
    )
    prefix = (
        "forall code1 pos1 neg1 code2 pos2 neg2. "
        f"({left_decode}) -> ({right_decode}) -> "
    )
    balance = "pos1 + neg2 = neg1 + pos2"

    return (
        spec(
            "signed_decoded_balance_implies_code_eq",
            f"{prefix}{balance} -> code1 = code2",
            (
                "zero_add",
                "add_eq_zero_right",
                "add_eq_zero_left",
                "succ_ne_zero",
            ),
            (
                "intro code1",
                "intro pos1",
                "intro neg1",
                "intro code2",
                "intro pos2",
                "intro neg2",
                "intro hleft",
                "intro hright",
                "intro hbalance",
                "cases hleft",
                "cases hleft_left",
                "cases hright",
                "cases hright_left",
                "have hpos : pos1 = pos2",
                "rewrite hright_left_right at hbalance",
                "rewrite hleft_left_right at hbalance",
                "rewrite PA3 at hbalance",
                "specialize zero_add pos2",
                "rewrite zero_add at hbalance",
                "exact hbalance",
                "trans 2 * pos1",
                "exact hleft_left_left",
                "rewrite hpos",
                "symm",
                "exact hright_left_left",
                "cases hright_right",
                "cases hright_right_witness",
                "cases hright_right_witness_left",
                "exfalso",
                "rewrite hright_right_witness_right at hbalance",
                "rewrite hleft_left_right at hbalance",
                "rewrite hright_right_witness_left_right at hbalance",
                "rewrite PA3 at hbalance",
                "have hsucc : S x = 0",
                "specialize add_eq_zero_right pos1",
                "specialize add_eq_zero_right (S x)",
                "apply add_eq_zero_right",
                "exact hbalance",
                "specialize succ_ne_zero x",
                "apply succ_ne_zero",
                "exact hsucc",
                "cases hleft_right",
                "cases hleft_right_witness",
                "cases hleft_right_witness_left",
                "cases hright",
                "cases hright_left",
                "exfalso",
                "rewrite hleft_right_witness_left_right at hbalance",
                "rewrite hright_left_right at hbalance",
                "rewrite hleft_right_witness_right at hbalance",
                "rewrite PA3 at hbalance",
                "have hsum : S x + pos2 = 0",
                "symm",
                "exact hbalance",
                "have hsucc : S x = 0",
                "specialize add_eq_zero_left (S x)",
                "specialize add_eq_zero_left pos2",
                "apply add_eq_zero_left",
                "exact hsum",
                "specialize succ_ne_zero x",
                "apply succ_ne_zero",
                "exact hsucc",
                "cases hright_right",
                "cases hright_right_witness",
                "cases hright_right_witness_left",
                "have hhalf : x = x1",
                "rewrite hleft_right_witness_left_right at hbalance",
                "rewrite hright_right_witness_left_right at hbalance",
                "rewrite hright_right_witness_right at hbalance",
                "rewrite hleft_right_witness_right at hbalance",
                "specialize zero_add (S x1)",
                "rewrite zero_add at hbalance",
                "rewrite PA3 at hbalance",
                "apply PA2",
                "symm",
                "exact hbalance",
                "trans 2 * x + 1",
                "exact hleft_right_witness_left_left",
                "rewrite hhalf",
                "symm",
                "exact hright_right_witness_left_left",
            ),
            "Decoded cross-sum equality forces literal equality of canonical "
            "signed-natural codes.",
        ),
        spec(
            "signed_code_eq_implies_decoded_balance",
            f"{prefix}code1 = code2 -> {balance}",
            (
                "signed_decode_functional",
                "add_comm",
            ),
            (
                "intro code1",
                "intro pos1",
                "intro neg1",
                "intro code2",
                "intro pos2",
                "intro neg2",
                "intro hleft",
                "intro hright",
                "intro hcode",
                "rewrite hcode at hleft",
                "rewrite hcode at hleft",
                "have hparts : pos1 = pos2 /\\ neg1 = neg2",
                "specialize signed_decode_functional code2",
                "specialize signed_decode_functional pos1",
                "specialize signed_decode_functional neg1",
                "specialize signed_decode_functional pos2",
                "specialize signed_decode_functional neg2",
                "apply signed_decode_functional",
                "exact hleft",
                "exact hright",
                "cases hparts",
                "rewrite hparts_left",
                "rewrite hparts_right",
                "apply add_comm",
            ),
            "Literal equality of decoded canonical codes implies their "
            "subtraction-free cross-sum equality.",
        ),
        spec(
            "signed_code_eq_iff_balance",
            f"{prefix}(({balance} -> code1 = code2) /\\ "
            f"(code1 = code2 -> {balance}))",
            (
                "signed_decoded_balance_implies_code_eq",
                "signed_code_eq_implies_decoded_balance",
            ),
            (
                "intro code1",
                "intro pos1",
                "intro neg1",
                "intro code2",
                "intro pos2",
                "intro neg2",
                "intro hleft",
                "intro hright",
                "split",
                "intro hbalance",
                "specialize signed_decoded_balance_implies_code_eq code1",
                "specialize signed_decoded_balance_implies_code_eq pos1",
                "specialize signed_decoded_balance_implies_code_eq neg1",
                "specialize signed_decoded_balance_implies_code_eq code2",
                "specialize signed_decoded_balance_implies_code_eq pos2",
                "specialize signed_decoded_balance_implies_code_eq neg2",
                "apply signed_decoded_balance_implies_code_eq",
                "exact hleft",
                "exact hright",
                "exact hbalance",
                "intro hcode",
                "specialize signed_code_eq_implies_decoded_balance code1",
                "specialize signed_code_eq_implies_decoded_balance pos1",
                "specialize signed_code_eq_implies_decoded_balance neg1",
                "specialize signed_code_eq_implies_decoded_balance code2",
                "specialize signed_code_eq_implies_decoded_balance pos2",
                "specialize signed_code_eq_implies_decoded_balance neg2",
                "apply signed_code_eq_implies_decoded_balance",
                "exact hleft",
                "exact hright",
                "exact hcode",
            ),
            "For decoded canonical signed naturals, code equality is exactly "
            "subtraction-free balance equality.",
        ),
    )


__all__ = ["make_ha_signed_code_extensional_candidate_theorems"]
