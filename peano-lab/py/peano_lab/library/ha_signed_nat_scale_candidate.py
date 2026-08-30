"""Strict-HA core candidates for scaling a canonical signed natural.

``SignedNatScale(scale, input, output)`` decodes the input and output codes
and states the subtraction-free scaling equation

``scale * ip + on = scale * inn + op``.

The graph expands hygienically into the unchanged first-order language
``{0,S,+,*,=}``.  The five specifications provide the exact RFC D07 graph,
its decoded specification in both directions, totality, and literal-output
functionality.  They are constructive, dependency-curried, unregistered,
and unadmitted.
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
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def signed_nat_scale(
    scale: str,
    input_code: str,
    output_code: str,
    *,
    tag: str,
) -> str:
    """Expand RFC ``HA-K3-SIGNED-D07`` hygienically."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (scale, "natural scale"),
            (input_code, "input code"),
            (output_code, "output code"),
        )
    )
    scale, input_code, output_code = variables
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sns_{role}_{safe_tag}"
        for role in ("ip", "inn", "op", "on")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedNatScale binder captures an argument")

    input_decode = signed_decode(
        input_code, names["ip"], names["inn"], tag=f"{safe_tag}_input"
    )
    output_decode = signed_decode(
        output_code, names["op"], names["on"], tag=f"{safe_tag}_output"
    )
    equation = (
        f"{scale} * {names['ip']} + {names['on']} = "
        f"{scale} * {names['inn']} + {names['op']}"
    )
    return (
        f"exists {names['ip']} {names['inn']} {names['op']} {names['on']}. "
        f"(({input_decode}) /\\ (({output_decode}) /\\ {equation}))"
    )


def make_ha_signed_nat_scale_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five canonical signed-natural-scaling core candidates."""

    intro_input = signed_decode("input", "ip", "inn", tag="scale_intro_input")
    intro_output = signed_decode(
        "output", "op", "on", tag="scale_intro_output"
    )
    intro_scale = signed_nat_scale("scale", "input", "output", tag="intro")

    elim_input = signed_decode("input", "ip", "inn", tag="scale_elim_input")
    elim_output = signed_decode(
        "output", "op", "on", tag="scale_elim_output"
    )
    elim_scale = signed_nat_scale("scale", "input", "output", tag="elim")

    iff_input = signed_decode("input", "ip", "inn", tag="scale_iff_input")
    iff_output = signed_decode("output", "op", "on", tag="scale_iff_output")
    iff_scale = signed_nat_scale("scale", "input", "output", tag="iff")

    total_scale = signed_nat_scale("scale", "input", "output", tag="total")
    functional_left = signed_nat_scale(
        "scale", "input", "output1", tag="functional_left"
    )
    functional_right = signed_nat_scale(
        "scale", "input", "output2", tag="functional_right"
    )

    equation = "scale * ip + on = scale * inn + op"

    return (
        spec(
            "signed_nat_scale_of_decoded_equation",
            "forall scale input output ip inn op on. "
            f"({intro_input}) -> ({intro_output}) -> {equation} -> "
            f"({intro_scale})",
            (),
            (
                "intro scale",
                "intro input",
                "intro output",
                "intro ip",
                "intro inn",
                "intro op",
                "intro on",
                "intro hinput",
                "intro houtput",
                "intro hequation",
                "exists ip",
                "exists inn",
                "exists op",
                "exists on",
                "split",
                "exact hinput",
                "split",
                "exact houtput",
                "exact hequation",
            ),
            "Fixed decoder witnesses and their scaling equation construct "
            "the exact SignedNatScale graph.",
        ),
        spec(
            "signed_nat_scale_to_decoded_equation",
            "forall scale input output ip inn op on. "
            f"({elim_input}) -> ({elim_output}) -> ({elim_scale}) -> "
            f"{equation}",
            ("signed_decode_functional",),
            (
                "intro scale",
                "intro input",
                "intro output",
                "intro ip",
                "intro inn",
                "intro op",
                "intro on",
                "intro hinput",
                "intro houtput",
                "intro hscale",
                "cases hscale",
                "cases hscale_witness",
                "cases hscale_witness_witness",
                "cases hscale_witness_witness_witness",
                "cases hscale_witness_witness_witness_witness",
                "cases hscale_witness_witness_witness_witness_right",
                "have hinput_parts : x = ip /\\ x1 = inn",
                "specialize signed_decode_functional input",
                "specialize signed_decode_functional x",
                "specialize signed_decode_functional x1",
                "specialize signed_decode_functional ip",
                "specialize signed_decode_functional inn",
                "apply signed_decode_functional",
                "exact hscale_witness_witness_witness_witness_left",
                "exact hinput",
                "have houtput_parts : x2 = op /\\ x3 = on",
                "specialize signed_decode_functional output",
                "specialize signed_decode_functional x2",
                "specialize signed_decode_functional x3",
                "specialize signed_decode_functional op",
                "specialize signed_decode_functional on",
                "apply signed_decode_functional",
                "exact hscale_witness_witness_witness_witness_right_left",
                "exact houtput",
                "cases hinput_parts",
                "cases houtput_parts",
                "rewrite hinput_parts_left at hscale_witness_witness_witness_witness_right_right",
                "rewrite hinput_parts_right at hscale_witness_witness_witness_witness_right_right",
                "rewrite houtput_parts_left at hscale_witness_witness_witness_witness_right_right",
                "rewrite houtput_parts_right at hscale_witness_witness_witness_witness_right_right",
                "exact hscale_witness_witness_witness_witness_right_right",
            ),
            "SignedNatScale plus fixed decoders entails its exact scaling "
            "equation.",
        ),
        spec(
            "signed_nat_scale_decoded_iff_equation",
            "forall scale input output ip inn op on. "
            f"({iff_input}) -> ({iff_output}) -> "
            f"(({equation} -> ({iff_scale})) /\\ "
            f"(({iff_scale}) -> {equation}))",
            (
                "signed_nat_scale_of_decoded_equation",
                "signed_nat_scale_to_decoded_equation",
            ),
            (
                "intro scale",
                "intro input",
                "intro output",
                "intro ip",
                "intro inn",
                "intro op",
                "intro on",
                "intro hinput",
                "intro houtput",
                "split",
                "intro hequation",
                "specialize signed_nat_scale_of_decoded_equation scale",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation output",
                "specialize signed_nat_scale_of_decoded_equation ip",
                "specialize signed_nat_scale_of_decoded_equation inn",
                "specialize signed_nat_scale_of_decoded_equation op",
                "specialize signed_nat_scale_of_decoded_equation on",
                "apply signed_nat_scale_of_decoded_equation",
                "exact hinput",
                "exact houtput",
                "exact hequation",
                "intro hscale",
                "specialize signed_nat_scale_to_decoded_equation scale",
                "specialize signed_nat_scale_to_decoded_equation input",
                "specialize signed_nat_scale_to_decoded_equation output",
                "specialize signed_nat_scale_to_decoded_equation ip",
                "specialize signed_nat_scale_to_decoded_equation inn",
                "specialize signed_nat_scale_to_decoded_equation op",
                "specialize signed_nat_scale_to_decoded_equation on",
                "apply signed_nat_scale_to_decoded_equation",
                "exact hinput",
                "exact houtput",
                "exact hscale",
            ),
            "For fixed decoders, SignedNatScale is equivalent to its natural "
            "scaling equation.",
        ),
        spec(
            "signed_nat_scale_total",
            f"forall scale input. exists output. ({total_scale})",
            (
                "signed_decode_total",
                "signed_balance_total",
                "signed_nat_scale_of_decoded_equation",
            ),
            (
                "intro scale",
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "specialize signed_balance_total (scale * x)",
                "specialize signed_balance_total (scale * x1)",
                "cases signed_balance_total",
                "cases signed_balance_total_witness",
                "cases signed_balance_total_witness_witness",
                "cases signed_balance_total_witness_witness_witness",
                "exists x2",
                "specialize signed_nat_scale_of_decoded_equation scale",
                "specialize signed_nat_scale_of_decoded_equation input",
                "specialize signed_nat_scale_of_decoded_equation x2",
                "specialize signed_nat_scale_of_decoded_equation x",
                "specialize signed_nat_scale_of_decoded_equation x1",
                "specialize signed_nat_scale_of_decoded_equation x3",
                "specialize signed_nat_scale_of_decoded_equation x4",
                "apply signed_nat_scale_of_decoded_equation",
                "exact signed_decode_total_witness_witness",
                "exact signed_balance_total_witness_witness_witness_left",
                "exact signed_balance_total_witness_witness_witness_right",
            ),
            "Every natural scale and canonical signed code have a canonical "
            "scaled output.",
        ),
        spec(
            "signed_nat_scale_functional",
            "forall scale input output1 output2. "
            f"({functional_left}) -> ({functional_right}) -> "
            "output1 = output2",
            (
                "signed_nat_scale_to_decoded_equation",
                "signed_balance_functional",
            ),
            (
                "intro scale",
                "intro input",
                "intro output1",
                "intro output2",
                "intro hscale1",
                "intro hscale2",
                "cases hscale1",
                "cases hscale1_witness",
                "cases hscale1_witness_witness",
                "cases hscale1_witness_witness_witness",
                "cases hscale1_witness_witness_witness_witness",
                "cases hscale1_witness_witness_witness_witness_right",
                "cases hscale2",
                "cases hscale2_witness",
                "cases hscale2_witness_witness",
                "cases hscale2_witness_witness_witness",
                "cases hscale2_witness_witness_witness_witness",
                "cases hscale2_witness_witness_witness_witness_right",
                "have hequation2 : scale * x + x7 = scale * x1 + x6",
                "specialize signed_nat_scale_to_decoded_equation scale",
                "specialize signed_nat_scale_to_decoded_equation input",
                "specialize signed_nat_scale_to_decoded_equation output2",
                "specialize signed_nat_scale_to_decoded_equation x",
                "specialize signed_nat_scale_to_decoded_equation x1",
                "specialize signed_nat_scale_to_decoded_equation x6",
                "specialize signed_nat_scale_to_decoded_equation x7",
                "apply signed_nat_scale_to_decoded_equation",
                "exact hscale1_witness_witness_witness_witness_left",
                "exact hscale2_witness_witness_witness_witness_right_left",
                "exact hscale2",
                "have hbalance1 : exists op on. "
                "((((output1 = 2 * op /\\ on = 0) \\/ "
                "exists sd_half_scale_functional_balance1. "
                "((output1 = 2 * sd_half_scale_functional_balance1 + 1 /\\ "
                "op = 0) /\\ on = S sd_half_scale_functional_balance1))) /\\ "
                "scale * x + on = scale * x1 + op)",
                "exists x2",
                "exists x3",
                "split",
                "exact hscale1_witness_witness_witness_witness_right_left",
                "exact hscale1_witness_witness_witness_witness_right_right",
                "have hbalance2 : exists op on. "
                "((((output2 = 2 * op /\\ on = 0) \\/ "
                "exists sd_half_scale_functional_balance2. "
                "((output2 = 2 * sd_half_scale_functional_balance2 + 1 /\\ "
                "op = 0) /\\ on = S sd_half_scale_functional_balance2))) /\\ "
                "scale * x + on = scale * x1 + op)",
                "exists x6",
                "exists x7",
                "split",
                "exact hscale2_witness_witness_witness_witness_right_left",
                "exact hequation2",
                "specialize signed_balance_functional (scale * x)",
                "specialize signed_balance_functional (scale * x1)",
                "specialize signed_balance_functional output1",
                "specialize signed_balance_functional output2",
                "apply signed_balance_functional",
                "exact hbalance1",
                "exact hbalance2",
            ),
            "Canonical signed-natural scaling has a unique literal output "
            "code.",
        ),
    )


__all__ = [
    "make_ha_signed_nat_scale_candidate_theorems",
    "signed_nat_scale",
]
