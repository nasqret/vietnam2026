"""Strict-HA algebra laws for canonical signed-natural scaling.

This isolated D07 tranche proves scalar transport of subtraction-free
cross-sums, composition of decoded scaling equations, the zero and one
scaling laws, and graph composition.  Every ``SignedNatScale`` occurrence
expands to the unchanged first-order language ``{0,S,+,*,=}``; no parser or
kernel primitive is added.

The public ``signed_nat_scale`` expander intentionally accepts identifiers
only.  Consequently, this module uses private, slot-specific expanders for
the reviewed scale terms ``0``, ``1``, and ``outer * inner``.  They preserve
the exact RFC D07 syntax and hygiene discipline without weakening that core
contract.  All candidates are constructive, dependency-curried,
unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_decode_candidate import signed_decode
from peano_lab.library.ha_signed_nat_scale_candidate import signed_nat_scale


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


def _signed_nat_scale_names(
    tag: str,
    variables: tuple[str, ...],
) -> dict[str, str]:
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sns_{role}_{safe_tag}"
        for role in ("ip", "inn", "op", "on")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedNatScale binder captures an argument")
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


def _assemble_signed_nat_scale(
    names: dict[str, str],
    scale_term: str,
    input_decode: str,
    output_decode: str,
) -> str:
    equation = (
        f"{scale_term} * {names['ip']} + {names['on']} = "
        f"{scale_term} * {names['inn']} + {names['op']}"
    )
    return (
        f"exists {names['ip']} {names['inn']} {names['op']} {names['on']}. "
        f"(({input_decode}) /\\ (({output_decode}) /\\ {equation}))"
    )


def _signed_nat_scale_zero(input_code: str, *, tag: str) -> str:
    """Expand RFC D07 at ``SignedNatScale(0,input,0)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_nat_scale_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_nat_scale(
        names,
        "0",
        signed_decode(
            input_code,
            names["ip"],
            names["inn"],
            tag=f"{safe_tag}_input",
        ),
        _signed_zero_decode(
            names["op"], names["on"], tag=f"{safe_tag}_output"
        ),
    )


def _signed_nat_scale_one(input_code: str, *, tag: str) -> str:
    """Expand RFC D07 at ``SignedNatScale(1,input,input)`` hygienically."""

    input_code = _identifier(input_code, "input code")
    names = _signed_nat_scale_names(tag, (input_code,))
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_nat_scale(
        names,
        "1",
        signed_decode(
            input_code,
            names["ip"],
            names["inn"],
            tag=f"{safe_tag}_input",
        ),
        signed_decode(
            input_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def _signed_nat_scale_product(
    outer: str,
    inner: str,
    input_code: str,
    output_code: str,
    *,
    tag: str,
) -> str:
    """Expand D07 with the reviewed natural scale ``outer * inner``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (outer, "outer scale"),
            (inner, "inner scale"),
            (input_code, "input code"),
            (output_code, "output code"),
        )
    )
    outer, inner, input_code, output_code = variables
    names = _signed_nat_scale_names(tag, variables)
    safe_tag = _identifier(tag, "binder tag")
    return _assemble_signed_nat_scale(
        names,
        f"({outer} * {inner})",
        signed_decode(
            input_code,
            names["ip"],
            names["inn"],
            tag=f"{safe_tag}_input",
        ),
        signed_decode(
            output_code,
            names["op"],
            names["on"],
            tag=f"{safe_tag}_output",
        ),
    )


def make_ha_signed_nat_scale_laws_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five direct D07 signed-natural-scaling laws."""

    zero_scale = _signed_nat_scale_zero("input", tag="zero")
    one_scale = _signed_nat_scale_one("input", tag="one")
    compose_inner = signed_nat_scale(
        "inner", "input", "middle", tag="compose_inner"
    )
    compose_outer = signed_nat_scale(
        "outer", "middle", "output", tag="compose_outer"
    )
    compose_target = _signed_nat_scale_product(
        "outer", "inner", "input", "output", tag="compose_target"
    )

    return (
        spec(
            "mul_cross_sum_left",
            "forall k a b c d. a + b = c + d -> "
            "k * a + k * b = k * c + k * d",
            ("mul_add",),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hcross",
                "trans k * (a + b)",
                "symm",
                "apply mul_add",
                "trans k * (c + d)",
                "congr",
                "refl",
                "exact hcross",
                "apply mul_add",
            ),
            "Left multiplication preserves a subtraction-free cross-sum.",
        ),
        spec(
            "signed_nat_scale_equations_compose",
            "forall outer inner ip inn mp mn op on. "
            "inner * ip + mn = inner * inn + mp -> "
            "outer * mp + on = outer * mn + op -> "
            "(outer * inner) * ip + on = "
            "(outer * inner) * inn + op",
            (
                "mul_cross_sum_left",
                "mul_assoc",
                "add_cross_sum_chain",
            ),
            (
                "intro outer",
                "intro inner",
                "intro ip",
                "intro inn",
                "intro mp",
                "intro mn",
                "intro op",
                "intro on",
                "intro hinner",
                "intro houter",
                "have hlift : "
                "outer * (inner * ip) + outer * mn = "
                "outer * (inner * inn) + outer * mp",
                "specialize mul_cross_sum_left outer",
                "specialize mul_cross_sum_left (inner * ip)",
                "specialize mul_cross_sum_left mn",
                "specialize mul_cross_sum_left (inner * inn)",
                "specialize mul_cross_sum_left mp",
                "apply mul_cross_sum_left",
                "exact hinner",
                "have hcomposed : "
                "outer * (inner * ip) + on = "
                "outer * (inner * inn) + op",
                "specialize add_cross_sum_chain "
                "(outer * (inner * ip))",
                "specialize add_cross_sum_chain "
                "(outer * (inner * inn))",
                "specialize add_cross_sum_chain (outer * mn)",
                "specialize add_cross_sum_chain (outer * mp)",
                "specialize add_cross_sum_chain on",
                "specialize add_cross_sum_chain op",
                "apply add_cross_sum_chain",
                "exact hlift",
                "exact houter",
                "trans outer * (inner * ip) + on",
                "congr",
                "apply mul_assoc",
                "refl",
                "trans outer * (inner * inn) + op",
                "exact hcomposed",
                "congr",
                "symm",
                "apply mul_assoc",
                "refl",
            ),
            "Decoded natural scaling equations compose multiplicatively.",
        ),
        spec(
            "signed_nat_scale_zero",
            f"forall input. ({zero_scale})",
            (
                "signed_decode_total",
                "signed_nat_scale_of_decoded_equation",
                "mul_zero_left",
            ),
            (
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "have hzero_decode : ((0 = 2 * 0 /\\ 0 = 0) \\/ "
                "exists sd_half_scale_zero_explicit. "
                "((0 = 2 * sd_half_scale_zero_explicit + 1 /\\ "
                "0 = 0) /\\ 0 = S sd_half_scale_zero_explicit))",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "have hzero_ip : 0 * x = 0",
                "specialize mul_zero_left x",
                "exact mul_zero_left",
                "have hzero_inn : 0 * x1 = 0",
                "specialize mul_zero_left x1",
                "exact mul_zero_left",
                "specialize signed_nat_scale_of_decoded_equation 0",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation 0",
                "specialize signed_nat_scale_of_decoded_equation x",
                "specialize signed_nat_scale_of_decoded_equation x1",
                "specialize signed_nat_scale_of_decoded_equation 0",
                "specialize signed_nat_scale_of_decoded_equation 0",
                "apply signed_nat_scale_of_decoded_equation",
                "exact signed_decode_total_witness_witness",
                "exact hzero_decode",
                "rewrite hzero_ip",
                "rewrite hzero_inn",
                "refl",
            ),
            "Natural scale zero maps every canonical signed code to zero.",
        ),
        spec(
            "signed_nat_scale_one",
            f"forall input. ({one_scale})",
            (
                "signed_decode_total",
                "signed_nat_scale_of_decoded_equation",
                "one_mul",
                "add_comm",
            ),
            (
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "have hone_ip : 1 * x = x",
                "specialize one_mul x",
                "exact one_mul",
                "have hone_inn : 1 * x1 = x1",
                "specialize one_mul x1",
                "exact one_mul",
                "specialize signed_nat_scale_of_decoded_equation 1",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation x",
                "specialize signed_nat_scale_of_decoded_equation x1",
                "specialize signed_nat_scale_of_decoded_equation x",
                "specialize signed_nat_scale_of_decoded_equation x1",
                "apply signed_nat_scale_of_decoded_equation",
                "exact signed_decode_total_witness_witness",
                "exact signed_decode_total_witness_witness",
                "rewrite hone_ip",
                "rewrite hone_inn",
                "apply add_comm",
            ),
            "Natural scale one is the identity on canonical signed codes.",
        ),
        spec(
            "signed_nat_scale_compose",
            "forall outer inner input middle output. "
            f"({compose_inner}) -> ({compose_outer}) -> "
            f"({compose_target})",
            (
                "signed_nat_scale_to_decoded_equation",
                "signed_nat_scale_equations_compose",
                "signed_nat_scale_of_decoded_equation",
            ),
            (
                "intro outer",
                "intro inner",
                "intro input",
                "intro middle",
                "intro output",
                "intro hinner",
                "intro houter",
                "cases hinner",
                "cases hinner_witness",
                "cases hinner_witness_witness",
                "cases hinner_witness_witness_witness",
                "cases hinner_witness_witness_witness_witness",
                "cases hinner_witness_witness_witness_witness_right",
                "cases houter",
                "cases houter_witness",
                "cases houter_witness_witness",
                "cases houter_witness_witness_witness",
                "cases houter_witness_witness_witness_witness",
                "cases houter_witness_witness_witness_witness_right",
                "have houter_equation : "
                "outer * x2 + x7 = outer * x3 + x6",
                "specialize signed_nat_scale_to_decoded_equation outer",
                "specialize signed_nat_scale_to_decoded_equation middle",
                "specialize signed_nat_scale_to_decoded_equation output",
                "specialize signed_nat_scale_to_decoded_equation x2",
                "specialize signed_nat_scale_to_decoded_equation x3",
                "specialize signed_nat_scale_to_decoded_equation x6",
                "specialize signed_nat_scale_to_decoded_equation x7",
                "apply signed_nat_scale_to_decoded_equation",
                "exact "
                "hinner_witness_witness_witness_witness_right_left",
                "exact "
                "houter_witness_witness_witness_witness_right_left",
                "exact houter",
                "have htarget_equation : "
                "(outer * inner) * x + x7 = "
                "(outer * inner) * x1 + x6",
                "specialize signed_nat_scale_equations_compose outer",
                "specialize signed_nat_scale_equations_compose inner",
                "specialize signed_nat_scale_equations_compose x",
                "specialize signed_nat_scale_equations_compose x1",
                "specialize signed_nat_scale_equations_compose x2",
                "specialize signed_nat_scale_equations_compose x3",
                "specialize signed_nat_scale_equations_compose x6",
                "specialize signed_nat_scale_equations_compose x7",
                "apply signed_nat_scale_equations_compose",
                "exact "
                "hinner_witness_witness_witness_witness_right_right",
                "exact houter_equation",
                "specialize signed_nat_scale_of_decoded_equation "
                "(outer * inner)",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation output",
                "specialize signed_nat_scale_of_decoded_equation x",
                "specialize signed_nat_scale_of_decoded_equation x1",
                "specialize signed_nat_scale_of_decoded_equation x6",
                "specialize signed_nat_scale_of_decoded_equation x7",
                "apply signed_nat_scale_of_decoded_equation",
                "exact hinner_witness_witness_witness_witness_left",
                "exact "
                "houter_witness_witness_witness_witness_right_left",
                "exact htarget_equation",
            ),
            "Exact D07 graphs compose with multiplication of natural scales.",
        ),
    )


__all__ = ["make_ha_signed_nat_scale_laws_candidate_theorems"]
