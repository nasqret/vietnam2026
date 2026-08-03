"""Strict-HA elementary laws for canonical signed multiplication.

This isolated candidate tranche proves commutativity, both zero laws, and
both one laws for RFC D06 ``SignedMul``.  Every relation occurrence expands
to the unchanged first-order language ``{0,S,+,*,=}``; no parser or kernel
primitive is added.

The core ``signed_mul`` expander intentionally accepts identifiers only.
Consequently, this module uses private, slot-specific expanders for the
reviewed literal codes ``0`` (signed zero) and ``2`` (signed positive one).
They preserve the exact RFC D06 syntax and hygiene discipline without
weakening that core contract.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_decode_candidate import signed_decode
from peano_lab.library.ha_signed_mul_candidate import signed_mul


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _signed_mul_names(tag: str, variables: tuple[str, ...]) -> dict[str, str]:
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sm_{role}_{safe_tag}"
        for role in ("lp", "ln", "rp", "rn", "op", "on")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedMul binder captures an argument")
    return names


def _signed_zero_decode(pos: str, neg: str, *, tag: str) -> str:
    """Expand ``SignedDecode(0,pos,neg)`` for a reviewed literal-zero slot."""

    pos = _identifier(pos, "positive part")
    neg = _identifier(neg, "negative part")
    safe_tag = _identifier(tag, "binder tag")
    half = f"sd_half_{safe_tag}"
    if half in {pos, neg}:
        raise ValueError("generated SignedDecode binder captures an argument")
    return (
        f"(0 = 2 * {pos} /\\ {neg} = 0) \\/ exists {half}. "
        f"((0 = 2 * {half} + 1 /\\ {pos} = 0) /\\ {neg} = S {half})"
    )


def _signed_one_decode(pos: str, neg: str, *, tag: str) -> str:
    """Expand ``SignedDecode(2,pos,neg)`` for a reviewed literal-one slot."""

    pos = _identifier(pos, "positive part")
    neg = _identifier(neg, "negative part")
    safe_tag = _identifier(tag, "binder tag")
    half = f"sd_half_{safe_tag}"
    if half in {pos, neg}:
        raise ValueError("generated SignedDecode binder captures an argument")
    return (
        f"(2 = 2 * {pos} /\\ {neg} = 0) \\/ exists {half}. "
        f"((2 = 2 * {half} + 1 /\\ {pos} = 0) /\\ {neg} = S {half})"
    )


def _assemble_signed_mul(
    names: dict[str, str],
    left_decode: str,
    right_decode: str,
    output_decode: str,
) -> str:
    equation = (
        f"({names['lp']} * {names['rp']} + "
        f"{names['ln']} * {names['rn']}) + {names['on']} = "
        f"({names['lp']} * {names['rn']} + "
        f"{names['ln']} * {names['rp']}) + {names['op']}"
    )
    return (
        f"exists {names['lp']} {names['ln']} {names['rp']} {names['rn']} "
        f"{names['op']} {names['on']}. (({left_decode}) /\\ "
        f"(({right_decode}) /\\ (({output_decode}) /\\ {equation})))"
    )


def _signed_mul_zero_left(input_code: str, *, tag: str) -> str:
    """Expand RFC D06 at ``SignedMul(0,input,0)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_mul_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_mul(
        names,
        _signed_zero_decode(
            names["lp"], names["ln"], tag=f"{safe_tag}_left"
        ),
        signed_decode(
            input_code,
            names["rp"],
            names["rn"],
            tag=f"{safe_tag}_right",
        ),
        _signed_zero_decode(
            names["op"], names["on"], tag=f"{safe_tag}_output"
        ),
    )


def _signed_mul_zero_right(input_code: str, *, tag: str) -> str:
    """Expand RFC D06 at ``SignedMul(input,0,0)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_mul_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_mul(
        names,
        signed_decode(
            input_code,
            names["lp"],
            names["ln"],
            tag=f"{safe_tag}_left",
        ),
        _signed_zero_decode(
            names["rp"], names["rn"], tag=f"{safe_tag}_right"
        ),
        _signed_zero_decode(
            names["op"], names["on"], tag=f"{safe_tag}_output"
        ),
    )


def _signed_mul_one_left(input_code: str, *, tag: str) -> str:
    """Expand RFC D06 at ``SignedMul(2,input,input)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_mul_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_mul(
        names,
        _signed_one_decode(
            names["lp"], names["ln"], tag=f"{safe_tag}_left"
        ),
        signed_decode(
            input_code,
            names["rp"],
            names["rn"],
            tag=f"{safe_tag}_right",
        ),
        signed_decode(
            input_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def _signed_mul_one_right(input_code: str, *, tag: str) -> str:
    """Expand RFC D06 at ``SignedMul(input,2,input)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_mul_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_mul(
        names,
        signed_decode(
            input_code,
            names["lp"],
            names["ln"],
            tag=f"{safe_tag}_left",
        ),
        _signed_one_decode(
            names["rp"], names["rn"], tag=f"{safe_tag}_right"
        ),
        signed_decode(
            input_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def make_ha_signed_mul_laws_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five elementary canonical signed-multiplication laws."""

    commutative_forward = signed_mul(
        "left", "right", "output", tag="comm_forward"
    )
    commutative_reverse = signed_mul(
        "right", "left", "output", tag="comm_reverse"
    )
    zero_left = _signed_mul_zero_left("input", tag="zero_left")
    zero_right = _signed_mul_zero_right("input", tag="zero_right")
    one_left = _signed_mul_one_left("input", tag="one_left")
    one_right = _signed_mul_one_right("input", tag="one_right")

    return (
        spec(
            "signed_mul_commutative",
            "forall left right output. "
            f"({commutative_forward}) -> ({commutative_reverse})",
            ("mul_comm", "add_comm"),
            (
                "intro left",
                "intro right",
                "intro output",
                "intro hmul",
                "cases hmul",
                "cases hmul_witness",
                "cases hmul_witness_witness",
                "cases hmul_witness_witness_witness",
                "cases hmul_witness_witness_witness_witness",
                "cases hmul_witness_witness_witness_witness_witness",
                "cases hmul_witness_witness_witness_witness_witness_witness",
                "cases hmul_witness_witness_witness_witness_witness_witness_right",
                "cases hmul_witness_witness_witness_witness_witness_witness_right_right",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "exists x4",
                "exists x5",
                "split",
                "exact hmul_witness_witness_witness_witness_witness_witness_right_left",
                "split",
                "exact hmul_witness_witness_witness_witness_witness_witness_left",
                "split",
                "exact hmul_witness_witness_witness_witness_witness_witness_right_right_left",
                "trans (x * x2 + x1 * x3) + x5",
                "congr",
                "congr",
                "apply mul_comm",
                "apply mul_comm",
                "refl",
                "trans (x * x3 + x1 * x2) + x4",
                "exact hmul_witness_witness_witness_witness_witness_witness_right_right_right",
                "trans (x3 * x + x2 * x1) + x4",
                "congr",
                "congr",
                "apply mul_comm",
                "apply mul_comm",
                "refl",
                "congr",
                "apply add_comm",
                "refl",
            ),
            "Canonical signed multiplication is commutative at the graph level.",
        ),
        spec(
            "signed_mul_zero_left",
            f"forall input. ({zero_left})",
            (
                "signed_decode_total",
                "signed_mul_of_decoded_equation",
                "mul_zero_left",
            ),
            (
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "have hzero : ((0 = 2 * 0 /\\ 0 = 0) \\/ "
                "exists sd_half_zero_left_explicit. "
                "((0 = 2 * sd_half_zero_left_explicit + 1 /\\ 0 = 0) /\\ "
                "0 = S sd_half_zero_left_explicit))",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "have hzero_x : 0 * x = 0",
                "specialize mul_zero_left x",
                "exact mul_zero_left",
                "have hzero_x1 : 0 * x1 = 0",
                "specialize mul_zero_left x1",
                "exact mul_zero_left",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation input",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation x",
                "specialize signed_mul_of_decoded_equation x1",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation 0",
                "apply signed_mul_of_decoded_equation",
                "exact hzero",
                "exact signed_decode_total_witness_witness",
                "exact hzero",
                "rewrite hzero_x",
                "rewrite hzero_x1",
                "rewrite hzero_x1",
                "rewrite hzero_x",
                "refl",
            ),
            "Zero annihilates canonical signed multiplication on the left.",
        ),
        spec(
            "signed_mul_zero_right",
            f"forall input. ({zero_right})",
            (
                "signed_mul_zero_left",
                "signed_mul_commutative",
            ),
            (
                "intro input",
                "specialize signed_mul_zero_left input",
                "specialize signed_mul_commutative 0",
                "specialize signed_mul_commutative input",
                "specialize signed_mul_commutative 0",
                "apply signed_mul_commutative",
                "exact signed_mul_zero_left",
            ),
            "Zero annihilates canonical signed multiplication on the right.",
        ),
        spec(
            "signed_mul_one_left",
            f"forall input. ({one_left})",
            (
                "signed_decode_total",
                "signed_mul_of_decoded_equation",
                "mul_one",
                "one_mul",
                "mul_zero_left",
                "add_comm",
            ),
            (
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "have hone : ((2 = 2 * 1 /\\ 0 = 0) \\/ "
                "exists sd_half_one_left_explicit. "
                "((2 = 2 * sd_half_one_left_explicit + 1 /\\ 1 = 0) /\\ "
                "0 = S sd_half_one_left_explicit))",
                "left",
                "split",
                "specialize mul_one 2",
                "rewrite mul_one",
                "refl",
                "refl",
                "have hone_x : 1 * x = x",
                "specialize one_mul x",
                "exact one_mul",
                "have hone_x1 : 1 * x1 = x1",
                "specialize one_mul x1",
                "exact one_mul",
                "have hzero_x : 0 * x = 0",
                "specialize mul_zero_left x",
                "exact mul_zero_left",
                "have hzero_x1 : 0 * x1 = 0",
                "specialize mul_zero_left x1",
                "exact mul_zero_left",
                "specialize signed_mul_of_decoded_equation 2",
                "specialize signed_mul_of_decoded_equation input",
                "specialize signed_mul_of_decoded_equation input",
                "specialize signed_mul_of_decoded_equation 1",
                "specialize signed_mul_of_decoded_equation 0",
                "specialize signed_mul_of_decoded_equation x",
                "specialize signed_mul_of_decoded_equation x1",
                "specialize signed_mul_of_decoded_equation x",
                "specialize signed_mul_of_decoded_equation x1",
                "apply signed_mul_of_decoded_equation",
                "exact hone",
                "exact signed_decode_total_witness_witness",
                "exact signed_decode_total_witness_witness",
                "rewrite hone_x",
                "rewrite hzero_x1",
                "rewrite hone_x1",
                "rewrite hzero_x",
                "rewrite PA3",
                "rewrite PA3",
                "apply add_comm",
            ),
            "Signed positive one is a left identity for canonical multiplication.",
        ),
        spec(
            "signed_mul_one_right",
            f"forall input. ({one_right})",
            (
                "signed_mul_one_left",
                "signed_mul_commutative",
            ),
            (
                "intro input",
                "specialize signed_mul_one_left input",
                "specialize signed_mul_commutative 2",
                "specialize signed_mul_commutative input",
                "specialize signed_mul_commutative input",
                "apply signed_mul_commutative",
                "exact signed_mul_one_left",
            ),
            "Signed positive one is a right identity by commutativity.",
        ),
    )


__all__ = ["make_ha_signed_mul_laws_candidate_theorems"]
