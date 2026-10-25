"""Strict-HA elementary laws for canonical signed addition.

This isolated candidate tranche proves commutativity, both zero identities,
and both orientations of addition with the canonical signed negation.  Every
``SignedAdd`` and ``SignedNegate`` occurrence is expanded to the unchanged
first-order language ``{0,S,+,*,=}``; no parser or kernel primitive is added.

The core ``signed_add`` expander intentionally accepts identifiers only.
Consequently, this module uses three private, slot-specific expanders for the
literal-zero instances.  They preserve the same RFC D05 syntax and hygiene
discipline without weakening that core contract.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_add_candidate import signed_add
from peano_lab.library.ha_signed_decode_candidate import signed_decode
from peano_lab.library.ha_signed_negate_candidate import signed_negate


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


def _signed_add_names(tag: str, variables: tuple[str, ...]) -> dict[str, str]:
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sa_{role}_{safe_tag}"
        for role in ("lp", "ln", "rp", "rn", "op", "on")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedAdd binder captures an argument")
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


def _assemble_signed_add(
    names: dict[str, str],
    left_decode: str,
    right_decode: str,
    output_decode: str,
) -> str:
    equation = (
        f"({names['lp']} + {names['rp']}) + {names['on']} = "
        f"({names['ln']} + {names['rn']}) + {names['op']}"
    )
    return (
        f"exists {names['lp']} {names['ln']} {names['rp']} {names['rn']} "
        f"{names['op']} {names['on']}. (({left_decode}) /\\ "
        f"(({right_decode}) /\\ (({output_decode}) /\\ {equation})))"
    )


def _signed_add_zero_left(input_code: str, *, tag: str) -> str:
    """Expand RFC D05 at ``SignedAdd(0,input,input)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_add_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_add(
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
        signed_decode(
            input_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def _signed_add_zero_right(input_code: str, *, tag: str) -> str:
    """Expand RFC D05 at ``SignedAdd(input,0,input)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_add_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_add(
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
        signed_decode(
            input_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def _signed_add_zero_output(
    left: str,
    right: str,
    *,
    tag: str,
) -> str:
    """Expand RFC D05 at ``SignedAdd(left,right,0)`` hygienically."""

    variables = tuple(
        _identifier(value, label)
        for value, label in ((left, "left code"), (right, "right code"))
    )
    left, right = variables
    names = _signed_add_names(tag, variables)
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_add(
        names,
        signed_decode(
            left,
            names["lp"],
            names["ln"],
            tag=f"{safe_tag}_left",
        ),
        signed_decode(
            right,
            names["rp"],
            names["rn"],
            tag=f"{safe_tag}_right",
        ),
        _signed_zero_decode(
            names["op"], names["on"], tag=f"{safe_tag}_output"
        ),
    )


def make_ha_signed_add_laws_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five elementary canonical signed-addition laws."""

    commutative_forward = signed_add(
        "left", "right", "output", tag="comm_forward"
    )
    commutative_reverse = signed_add(
        "right", "left", "output", tag="comm_reverse"
    )
    zero_left = _signed_add_zero_left("input", tag="zero_left")
    zero_right = _signed_add_zero_right("input", tag="zero_right")
    negate_right = signed_negate(
        "input", "negated", tag="add_inverse"
    )
    negate_right_zero = _signed_add_zero_output(
        "input", "negated", tag="negate_right_zero"
    )
    negate_left = signed_negate(
        "input", "negated", tag="add_inverse_left"
    )
    negate_left_zero = _signed_add_zero_output(
        "negated", "input", tag="negate_left_zero"
    )

    return (
        spec(
            "signed_add_commutative",
            "forall left right output. "
            f"({commutative_forward}) -> ({commutative_reverse})",
            ("add_comm",),
            (
                "intro left",
                "intro right",
                "intro output",
                "intro hadd",
                "cases hadd",
                "cases hadd_witness",
                "cases hadd_witness_witness",
                "cases hadd_witness_witness_witness",
                "cases hadd_witness_witness_witness_witness",
                "cases hadd_witness_witness_witness_witness_witness",
                "cases hadd_witness_witness_witness_witness_witness_witness",
                "cases hadd_witness_witness_witness_witness_witness_witness_right",
                "cases hadd_witness_witness_witness_witness_witness_witness_right_right",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "exists x4",
                "exists x5",
                "split",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_left",
                "split",
                "exact hadd_witness_witness_witness_witness_witness_witness_left",
                "split",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_right_left",
                "trans (x + x2) + x5",
                "congr",
                "apply add_comm",
                "refl",
                "trans (x1 + x3) + x4",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "congr",
                "apply add_comm",
                "refl",
            ),
            "Canonical signed addition is commutative at the graph level.",
        ),
        spec(
            "signed_add_zero_left",
            f"forall input. ({zero_left})",
            (
                "signed_decode_total",
                "signed_add_of_decoded_equation",
                "zero_add",
                "add_comm",
            ),
            (
                "intro input",
                "have hzero_add_right : forall n. 0 + n = n",
                "exact zero_add",
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
                "specialize signed_add_of_decoded_equation 0",
                "specialize signed_add_of_decoded_equation input",
                "specialize signed_add_of_decoded_equation input",
                "specialize signed_add_of_decoded_equation 0",
                "specialize signed_add_of_decoded_equation 0",
                "specialize signed_add_of_decoded_equation x",
                "specialize signed_add_of_decoded_equation x1",
                "specialize signed_add_of_decoded_equation x",
                "specialize signed_add_of_decoded_equation x1",
                "apply signed_add_of_decoded_equation",
                "exact hzero",
                "exact signed_decode_total_witness_witness",
                "exact signed_decode_total_witness_witness",
                "specialize zero_add x",
                "rewrite zero_add",
                "specialize hzero_add_right x1",
                "rewrite hzero_add_right",
                "apply add_comm",
            ),
            "Zero is a left identity for canonical signed addition.",
        ),
        spec(
            "signed_add_zero_right",
            f"forall input. ({zero_right})",
            (
                "signed_add_zero_left",
                "signed_add_commutative",
            ),
            (
                "intro input",
                "specialize signed_add_zero_left input",
                "specialize signed_add_commutative 0",
                "specialize signed_add_commutative input",
                "specialize signed_add_commutative input",
                "apply signed_add_commutative",
                "exact signed_add_zero_left",
            ),
            "Zero is a right identity by left identity and commutativity.",
        ),
        spec(
            "signed_add_negate_right_zero",
            f"forall input negated. ({negate_right}) -> "
            f"({negate_right_zero})",
            (
                "signed_add_of_decoded_equation",
                "add_comm",
            ),
            (
                "intro input",
                "intro negated",
                "intro hnegate",
                "cases hnegate",
                "cases hnegate_witness",
                "cases hnegate_witness_witness",
                "have hzero : ((0 = 2 * 0 /\\ 0 = 0) \\/ "
                "exists sd_half_negate_right_zero_explicit. "
                "((0 = 2 * sd_half_negate_right_zero_explicit + 1 /\\ "
                "0 = 0) /\\ 0 = S sd_half_negate_right_zero_explicit))",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "specialize signed_add_of_decoded_equation input",
                "specialize signed_add_of_decoded_equation negated",
                "specialize signed_add_of_decoded_equation 0",
                "specialize signed_add_of_decoded_equation x",
                "specialize signed_add_of_decoded_equation x1",
                "specialize signed_add_of_decoded_equation x1",
                "specialize signed_add_of_decoded_equation x",
                "specialize signed_add_of_decoded_equation 0",
                "specialize signed_add_of_decoded_equation 0",
                "apply signed_add_of_decoded_equation",
                "exact hnegate_witness_witness_left",
                "exact hnegate_witness_witness_right",
                "exact hzero",
                "rewrite PA3",
                "rewrite PA3",
                "apply add_comm",
            ),
            "A canonical signed code plus its negation is canonical zero.",
        ),
        spec(
            "signed_add_negate_left_zero",
            f"forall input negated. ({negate_left}) -> "
            f"({negate_left_zero})",
            (
                "signed_add_negate_right_zero",
                "signed_add_commutative",
            ),
            (
                "intro input",
                "intro negated",
                "intro hnegate",
                "have hright : "
                f"({_signed_add_zero_output('input', 'negated', tag='negate_left_source')})",
                "specialize signed_add_negate_right_zero input",
                "specialize signed_add_negate_right_zero negated",
                "apply signed_add_negate_right_zero",
                "exact hnegate",
                "specialize signed_add_commutative input",
                "specialize signed_add_commutative negated",
                "specialize signed_add_commutative 0",
                "apply signed_add_commutative",
                "exact hright",
            ),
            "A canonical negation plus its source is canonical zero.",
        ),
    )


__all__ = ["make_ha_signed_add_laws_candidate_theorems"]
