"""Strict-HA seed candidates for canonical signed balance codes.

``SignedBalance(code, left, right)`` is the fully expanded graph saying that
``code`` canonically represents the formal difference ``left - right``.  It
is only surface notation: every generated statement remains in the unchanged
first-order language ``{0,S,+,*,=}``.

This deliberately small tranche contains only totality, transport from an
already supplied decoder witness, and the additive cross-sum calculation
needed by the later functionality proof.  The candidates are constructive,
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_decode_candidate import signed_decode


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'" for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def signed_balance(code: str, left: str, right: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-SIGNED-D03`` hygienically in a variable context."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (left, "left component"),
            (right, "right component"),
        )
    )
    code, left, right = variables
    safe_tag = _identifier(tag, "binder tag")
    pos = f"sb_pos_{safe_tag}"
    neg = f"sb_neg_{safe_tag}"
    if pos in variables or neg in variables:
        raise ValueError("generated SignedBalance binder captures an argument")
    relation = signed_decode(code, pos, neg, tag=safe_tag)
    return (
        f"exists {pos} {neg}. (({relation}) /\\ "
        f"{left} + {neg} = {right} + {pos})"
    )


def make_ha_signed_balance_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first three SignedBalance candidates in dependency order."""

    total_balance = signed_balance("code", "left", "right", tag="total")
    decode_input = signed_decode("code", "pos", "neg", tag="decode_input")
    decode_output = signed_balance("code", "pos", "neg", tag="decode_output")

    return (
        spec(
            "signed_balance_total",
            f"forall left right. exists code. ({total_balance})",
            ("lt_trichotomy", "add_comm"),
            (
                "intro left",
                "intro right",
                "specialize lt_trichotomy left",
                "specialize lt_trichotomy right",
                "cases lt_trichotomy",
                "exists 0",
                "exists 0",
                "exists 0",
                "split",
                "left",
                "split",
                "symm",
                "apply PA5",
                "refl",
                "rewrite PA3",
                "rewrite PA3",
                "exact lt_trichotomy_left",
                "cases lt_trichotomy_right",
                "cases lt_trichotomy_right_left",
                "exists 2 * x + 1",
                "exists 0",
                "exists S x",
                "split",
                "right",
                "exists x",
                "split",
                "split",
                "refl",
                "refl",
                "refl",
                "rewrite PA3",
                "trans x + S left",
                "trans S (left + x)",
                "apply PA4",
                "trans S (x + left)",
                "congr",
                "apply add_comm",
                "symm",
                "apply PA4",
                "exact lt_trichotomy_right_left_witness",
                "cases lt_trichotomy_right_right",
                "exists 2 * S x",
                "exists S x",
                "exists 0",
                "split",
                "left",
                "split",
                "refl",
                "refl",
                "rewrite PA3",
                "symm",
                "trans x + S right",
                "trans S (right + x)",
                "apply PA4",
                "trans S (x + right)",
                "congr",
                "apply add_comm",
                "symm",
                "apply PA4",
                "exact lt_trichotomy_right_right_witness",
            ),
            "Every balanced pair has a canonical signed-natural code.",
        ),
        spec(
            "signed_decode_to_balance",
            f"forall code pos neg. ({decode_input}) -> ({decode_output})",
            ("add_comm",),
            (
                "intro code",
                "intro pos",
                "intro neg",
                "intro hdecode",
                "exists pos",
                "exists neg",
                "split",
                "exact hdecode",
                "specialize add_comm pos",
                "specialize add_comm neg",
                "exact add_comm",
            ),
            "A decoder witness induces the corresponding balanced witness.",
        ),
        spec(
            "signed_balance_equations_cross_sum",
            "forall left1 right1 pos1 neg1 left2 right2 pos2 neg2. "
            "left1 + neg1 = right1 + pos1 -> "
            "left2 + neg2 = right2 + pos2 -> "
            "left1 + right2 = right1 + left2 -> "
            "pos1 + neg2 = neg1 + pos2",
            ("add_permute_outer", "add_left_cancel"),
            (
                "intro left1",
                "intro right1",
                "intro pos1",
                "intro neg1",
                "intro left2",
                "intro right2",
                "intro pos2",
                "intro neg2",
                "intro hfirst",
                "intro hsecond",
                "intro hcross",
                "have hcomm : forall a b. a + b = b + a",
                "intro a",
                "intro b",
                "specialize add_permute_outer a",
                "specialize add_permute_outer 0",
                "specialize add_permute_outer b",
                "specialize add_permute_outer 0",
                "rewrite PA3 at add_permute_outer",
                "rewrite PA3 at add_permute_outer",
                "rewrite PA3 at add_permute_outer",
                "rewrite PA3 at add_permute_outer",
                "exact add_permute_outer",
                "have hshuffle : forall a b c d. "
                "(a + b) + (c + d) = (a + c) + (b + d)",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans (b + a) + (c + d)",
                "congr",
                "apply hcomm",
                "refl",
                "trans (c + a) + (b + d)",
                "apply add_permute_outer",
                "congr",
                "apply hcomm",
                "refl",
                "specialize add_left_cancel (right1 + left2)",
                "specialize add_left_cancel (pos1 + neg2)",
                "specialize add_left_cancel (neg1 + pos2)",
                "apply add_left_cancel",
                "trans (right1 + pos1) + (left2 + neg2)",
                "apply hshuffle",
                "trans (left1 + neg1) + (right2 + pos2)",
                "congr",
                "symm",
                "exact hfirst",
                "exact hsecond",
                "trans (left1 + right2) + (neg1 + pos2)",
                "apply hshuffle",
                "congr",
                "exact hcross",
                "refl",
            ),
            "Balanced equations and a cross-sum equality force decoded "
            "cross-sum equality.",
        ),
    )


__all__ = [
    "make_ha_signed_balance_candidate_theorems",
    "signed_balance",
]
