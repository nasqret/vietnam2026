"""Strict-HA decoder candidates for canonical signed-natural codes.

The selected code interleaves signs by parity: ``2 * p`` represents the
nonnegative integer ``p`` and ``2 * k + 1`` represents ``-(k + 1)``.  This
module expands the decoder relation all the way to the unchanged first-order
language ``{0,S,+,*,=}``; it adds no kernel or parser primitive.

All seven theorem specifications are dependency-curried, constructive,
unregistered, and unadmitted.  In particular, the functionality proof uses
the isolated K1 parity candidates rather than the public parity theorem whose
historical proof depends on division with remainder.
"""

from __future__ import annotations

from typing import Any, Callable


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


def signed_decode(code: str, pos: str, neg: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-SIGNED-D01`` hygienically in a variable context."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "code"),
            (pos, "positive part"),
            (neg, "negative part"),
        )
    )
    code, pos, neg = variables
    safe_tag = _identifier(tag, "binder tag")
    half = f"sd_half_{safe_tag}"
    if half in variables:
        raise ValueError("generated SignedDecode binder captures an argument")
    return (
        f"({code} = 2 * {pos} /\\ {neg} = 0) \\/ exists {half}. "
        f"(({code} = 2 * {half} + 1 /\\ {pos} = 0) /\\ {neg} = S {half})"
    )


def signed_valid(code: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-SIGNED-D02`` hygienically in a variable context."""

    code = _identifier(code, "code")
    safe_tag = _identifier(tag, "binder tag")
    pos = f"sd_pos_{safe_tag}"
    neg = f"sd_neg_{safe_tag}"
    if code in {pos, neg}:
        raise ValueError("generated SignedValid binder captures its argument")
    relation = signed_decode(code, pos, neg, tag=f"{safe_tag}_valid")
    return f"exists {pos} {neg}. ({relation})"


def make_ha_signed_decode_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the seven first-stage decoder candidates in dependency order."""

    normal_decode = signed_decode("code", "pos", "neg", tag="normal")
    left_decode = signed_decode("code", "pos1", "neg1", tag="left")
    right_decode = signed_decode("code", "pos2", "neg2", tag="right")

    return (
        spec(
            "signed_decode_nonnegative_constructor",
            "forall p. ((2 * p = 2 * p /\\ 0 = 0) \\/ exists "
            "sd_half_nonnegative. ((2 * p = 2 * sd_half_nonnegative + 1 "
            "/\\ p = 0) /\\ 0 = S sd_half_nonnegative))",
            (),
            (
                "intro p",
                "left",
                "split",
                "refl",
                "refl",
            ),
            "Every doubled natural decodes to its nonnegative constructor.",
        ),
        spec(
            "signed_decode_negative_constructor",
            "forall k. ((2 * k + 1 = 2 * 0 /\\ S k = 0) \\/ exists "
            "sd_half_negative. ((2 * k + 1 = 2 * sd_half_negative + 1 "
            "/\\ 0 = 0) /\\ S k = S sd_half_negative))",
            (),
            (
                "intro k",
                "right",
                "exists k",
                "split",
                "split",
                "refl",
                "refl",
                "refl",
            ),
            "Every odd code decodes to a strictly negative successor magnitude.",
        ),
        spec(
            "signed_decode_total",
            "forall code. exists pos neg. ((code = 2 * pos /\\ neg = 0) "
            "\\/ exists sd_half_total. ((code = 2 * sd_half_total + 1 "
            "/\\ pos = 0) /\\ neg = S sd_half_total))",
            ("parity_cases",),
            (
                "intro code",
                "specialize parity_cases code",
                "cases parity_cases",
                "cases parity_cases_witness",
                "exists x",
                "exists 0",
                "left",
                "split",
                "exact parity_cases_witness_left",
                "refl",
                "exists 0",
                "exists S x",
                "right",
                "exists x",
                "split",
                "split",
                "exact parity_cases_witness_right",
                "refl",
                "refl",
            ),
            "Every natural code has a normalized signed decoding by parity.",
        ),
        spec(
            "signed_decode_normal",
            f"forall code pos neg. ({normal_decode}) -> pos = 0 \\/ neg = 0",
            (),
            (
                "intro code",
                "intro pos",
                "intro neg",
                "intro hdecode",
                "cases hdecode",
                "cases hdecode_left",
                "right",
                "exact hdecode_left_right",
                "cases hdecode_right",
                "cases hdecode_right_witness",
                "cases hdecode_right_witness_left",
                "left",
                "exact hdecode_right_witness_left_right",
            ),
            "Every decoding has at least one zero sign-magnitude component.",
        ),
        spec(
            "signed_decode_functional",
            f"forall code pos1 neg1 pos2 neg2. ({left_decode}) -> "
            f"({right_decode}) -> pos1 = pos2 /\\ neg1 = neg2",
            (
                "even_half_unique",
                "odd_half_unique",
                "even_odd_exclusive_k1",
            ),
            (
                "intro code",
                "intro pos1",
                "intro neg1",
                "intro pos2",
                "intro neg2",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_left",
                "cases hright",
                "cases hright_left",
                "split",
                "specialize even_half_unique code",
                "specialize even_half_unique pos1",
                "specialize even_half_unique pos2",
                "apply even_half_unique",
                "exact hleft_left_left",
                "exact hright_left_left",
                "trans 0",
                "exact hleft_left_right",
                "symm",
                "exact hright_left_right",
                "cases hright_right",
                "cases hright_right_witness",
                "cases hright_right_witness_left",
                "exfalso",
                "specialize even_odd_exclusive_k1 code",
                "specialize even_odd_exclusive_k1 pos1",
                "specialize even_odd_exclusive_k1 x",
                "apply even_odd_exclusive_k1",
                "exact hleft_left_left",
                "exact hright_right_witness_left_left",
                "cases hleft_right",
                "cases hleft_right_witness",
                "cases hleft_right_witness_left",
                "cases hright",
                "cases hright_left",
                "exfalso",
                "specialize even_odd_exclusive_k1 code",
                "specialize even_odd_exclusive_k1 pos2",
                "specialize even_odd_exclusive_k1 x",
                "apply even_odd_exclusive_k1",
                "exact hright_left_left",
                "exact hleft_right_witness_left_left",
                "cases hright_right",
                "cases hright_right_witness",
                "cases hright_right_witness_left",
                "split",
                "trans 0",
                "exact hleft_right_witness_left_right",
                "symm",
                "exact hright_right_witness_left_right",
                "have hhalf : x = x1",
                "specialize odd_half_unique code",
                "specialize odd_half_unique x",
                "specialize odd_half_unique x1",
                "apply odd_half_unique",
                "exact hleft_right_witness_left_left",
                "exact hright_right_witness_left_left",
                "trans S x",
                "exact hleft_right_witness_right",
                "trans S x1",
                "congr",
                "exact hhalf",
                "symm",
                "exact hright_right_witness_right",
            ),
            "A natural code has unique normalized positive and negative parts.",
        ),
        spec(
            "signed_decode_zero_iff",
            "forall code. ((((code = 2 * 0 /\\ 0 = 0) \\/ exists "
            "sd_half_zero_forward. ((code = 2 * sd_half_zero_forward + 1 "
            "/\\ 0 = 0) /\\ 0 = S sd_half_zero_forward)) -> code = 0) "
            "/\\ (code = 0 -> ((code = 2 * 0 /\\ 0 = 0) \\/ exists "
            "sd_half_zero_backward. ((code = 2 * sd_half_zero_backward + 1 "
            "/\\ 0 = 0) /\\ 0 = S sd_half_zero_backward))))",
            ("succ_ne_zero",),
            (
                "intro code",
                "split",
                "intro hdecode",
                "cases hdecode",
                "cases hdecode_left",
                "rewrite PA5 at hdecode_left_left",
                "exact hdecode_left_left",
                "cases hdecode_right",
                "cases hdecode_right_witness",
                "exfalso",
                "specialize succ_ne_zero x",
                "apply succ_ne_zero",
                "symm",
                "exact hdecode_right_witness_right",
                "intro hzero",
                "left",
                "split",
                "rewrite hzero",
                "rewrite PA5",
                "refl",
                "refl",
            ),
            "The canonical signed zero decoding occurs exactly at code zero.",
        ),
        spec(
            "signed_valid_all",
            "forall code. exists pos neg. ((code = 2 * pos /\\ neg = 0) "
            "\\/ exists sd_half_valid. ((code = 2 * sd_half_valid + 1 "
            "/\\ pos = 0) /\\ neg = S sd_half_valid))",
            ("signed_decode_total",),
            (
                "intro code",
                "specialize signed_decode_total code",
                "exact signed_decode_total",
            ),
            "Every natural is a valid canonical signed code.",
        ),
    )


__all__ = [
    "make_ha_signed_decode_candidate_theorems",
    "signed_decode",
    "signed_valid",
]
