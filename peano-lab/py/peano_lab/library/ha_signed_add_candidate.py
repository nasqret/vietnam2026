"""Strict-HA core candidates for canonical signed addition.

``SignedAdd(left, right, output)`` decodes all three canonical signed-natural
codes and states the subtraction-free contribution equation

``(lp + rp) + on = (ln + rn) + op``.

The relation is expanded hygienically into the unchanged first-order language
``{0,S,+,*,=}``.  The five specifications below provide the exact RFC graph,
its decoded specification in both directions, totality, and literal-output
functionality.  They are constructive, dependency-curried, unregistered, and
unadmitted.
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


def signed_add(
    left: str,
    right: str,
    output: str,
    *,
    tag: str,
) -> str:
    """Expand RFC ``HA-K3-SIGNED-D05`` hygienically."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (left, "left code"),
            (right, "right code"),
            (output, "output code"),
        )
    )
    left, right, output = variables
    safe_tag = _identifier(tag, "binder tag")
    names = {
        role: f"sa_{role}_{safe_tag}"
        for role in ("lp", "ln", "rp", "rn", "op", "on")
    }
    if set(names.values()) & set(variables):
        raise ValueError("generated SignedAdd binder captures an argument")

    left_decode = signed_decode(
        left, names["lp"], names["ln"], tag=f"{safe_tag}_left"
    )
    right_decode = signed_decode(
        right, names["rp"], names["rn"], tag=f"{safe_tag}_right"
    )
    output_decode = signed_decode(
        output, names["op"], names["on"], tag=f"{safe_tag}_output"
    )
    equation = (
        f"({names['lp']} + {names['rp']}) + {names['on']} = "
        f"({names['ln']} + {names['rn']}) + {names['op']}"
    )
    return (
        f"exists {names['lp']} {names['ln']} {names['rp']} {names['rn']} "
        f"{names['op']} {names['on']}. (({left_decode}) /\\ "
        f"(({right_decode}) /\\ (({output_decode}) /\\ {equation})))"
    )


def make_ha_signed_add_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the five canonical signed-addition core candidates."""

    intro_left = signed_decode("left", "lp", "ln", tag="add_intro_left")
    intro_right = signed_decode("right", "rp", "rn", tag="add_intro_right")
    intro_output = signed_decode("output", "op", "on", tag="add_intro_output")
    intro_add = signed_add("left", "right", "output", tag="intro")

    elim_left = signed_decode("left", "lp", "ln", tag="add_elim_left")
    elim_right = signed_decode("right", "rp", "rn", tag="add_elim_right")
    elim_output = signed_decode("output", "op", "on", tag="add_elim_output")
    elim_add = signed_add("left", "right", "output", tag="elim")

    iff_left = signed_decode("left", "lp", "ln", tag="add_iff_left")
    iff_right = signed_decode("right", "rp", "rn", tag="add_iff_right")
    iff_output = signed_decode("output", "op", "on", tag="add_iff_output")
    iff_add = signed_add("left", "right", "output", tag="iff")

    total_add = signed_add("left", "right", "output", tag="total")
    functional_left = signed_add(
        "left", "right", "output1", tag="functional_left"
    )
    functional_right = signed_add(
        "left", "right", "output2", tag="functional_right"
    )

    return (
        spec(
            "signed_add_of_decoded_equation",
            "forall left right output lp ln rp rn op on. "
            f"({intro_left}) -> ({intro_right}) -> ({intro_output}) -> "
            "(lp + rp) + on = (ln + rn) + op -> "
            f"({intro_add})",
            (),
            (
                "intro left",
                "intro right",
                "intro output",
                "intro lp",
                "intro ln",
                "intro rp",
                "intro rn",
                "intro op",
                "intro on",
                "intro hleft",
                "intro hright",
                "intro houtput",
                "intro hequation",
                "exists lp",
                "exists ln",
                "exists rp",
                "exists rn",
                "exists op",
                "exists on",
                "split",
                "exact hleft",
                "split",
                "exact hright",
                "split",
                "exact houtput",
                "exact hequation",
            ),
            "Fixed decoder witnesses and their contribution equation construct "
            "the exact SignedAdd graph.",
        ),
        spec(
            "signed_add_to_decoded_equation",
            "forall left right output lp ln rp rn op on. "
            f"({elim_left}) -> ({elim_right}) -> ({elim_output}) -> "
            f"({elim_add}) -> (lp + rp) + on = (ln + rn) + op",
            ("signed_decode_functional",),
            (
                "intro left",
                "intro right",
                "intro output",
                "intro lp",
                "intro ln",
                "intro rp",
                "intro rn",
                "intro op",
                "intro on",
                "intro hleft",
                "intro hright",
                "intro houtput",
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
                "have hleft_parts : x = lp /\\ x1 = ln",
                "specialize signed_decode_functional left",
                "specialize signed_decode_functional x",
                "specialize signed_decode_functional x1",
                "specialize signed_decode_functional lp",
                "specialize signed_decode_functional ln",
                "apply signed_decode_functional",
                "exact hadd_witness_witness_witness_witness_witness_witness_left",
                "exact hleft",
                "have hright_parts : x2 = rp /\\ x3 = rn",
                "specialize signed_decode_functional right",
                "specialize signed_decode_functional x2",
                "specialize signed_decode_functional x3",
                "specialize signed_decode_functional rp",
                "specialize signed_decode_functional rn",
                "apply signed_decode_functional",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_left",
                "exact hright",
                "have houtput_parts : x4 = op /\\ x5 = on",
                "specialize signed_decode_functional output",
                "specialize signed_decode_functional x4",
                "specialize signed_decode_functional x5",
                "specialize signed_decode_functional op",
                "specialize signed_decode_functional on",
                "apply signed_decode_functional",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact houtput",
                "cases hleft_parts",
                "cases hright_parts",
                "cases houtput_parts",
                "rewrite hleft_parts_left at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite hleft_parts_right at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite hright_parts_left at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite hright_parts_right at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite houtput_parts_left at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite houtput_parts_right at hadd_witness_witness_witness_witness_witness_witness_right_right_right",
                "exact hadd_witness_witness_witness_witness_witness_witness_right_right_right",
            ),
            "SignedAdd plus fixed decoders entails its exact contribution "
            "equation.",
        ),
        spec(
            "signed_add_decoded_iff_equation",
            "forall left right output lp ln rp rn op on. "
            f"({iff_left}) -> ({iff_right}) -> ({iff_output}) -> "
            "(((lp + rp) + on = (ln + rn) + op -> "
            f"({iff_add})) /\\ (({iff_add}) -> "
            "(lp + rp) + on = (ln + rn) + op))",
            (
                "signed_add_of_decoded_equation",
                "signed_add_to_decoded_equation",
            ),
            (
                "intro left",
                "intro right",
                "intro output",
                "intro lp",
                "intro ln",
                "intro rp",
                "intro rn",
                "intro op",
                "intro on",
                "intro hleft",
                "intro hright",
                "intro houtput",
                "split",
                "intro hequation",
                "specialize signed_add_of_decoded_equation left",
                "specialize signed_add_of_decoded_equation right",
                "specialize signed_add_of_decoded_equation output",
                "specialize signed_add_of_decoded_equation lp",
                "specialize signed_add_of_decoded_equation ln",
                "specialize signed_add_of_decoded_equation rp",
                "specialize signed_add_of_decoded_equation rn",
                "specialize signed_add_of_decoded_equation op",
                "specialize signed_add_of_decoded_equation on",
                "apply signed_add_of_decoded_equation",
                "exact hleft",
                "exact hright",
                "exact houtput",
                "exact hequation",
                "intro hadd",
                "specialize signed_add_to_decoded_equation left",
                "specialize signed_add_to_decoded_equation right",
                "specialize signed_add_to_decoded_equation output",
                "specialize signed_add_to_decoded_equation lp",
                "specialize signed_add_to_decoded_equation ln",
                "specialize signed_add_to_decoded_equation rp",
                "specialize signed_add_to_decoded_equation rn",
                "specialize signed_add_to_decoded_equation op",
                "specialize signed_add_to_decoded_equation on",
                "apply signed_add_to_decoded_equation",
                "exact hleft",
                "exact hright",
                "exact houtput",
                "exact hadd",
            ),
            "For fixed decoders, SignedAdd is equivalent to its natural "
            "contribution equation.",
        ),
        spec(
            "signed_add_total",
            f"forall left right. exists output. ({total_add})",
            (
                "signed_decode_total",
                "signed_balance_total",
                "signed_add_of_decoded_equation",
            ),
            (
                "intro left",
                "intro right",
                "have hdecode_right_all : forall code. exists pos neg. "
                "((code = 2 * pos /\\ neg = 0) \\/ "
                "exists sd_half_add_total_copy. "
                "((code = 2 * sd_half_add_total_copy + 1 /\\ pos = 0) /\\ "
                "neg = S sd_half_add_total_copy))",
                "exact signed_decode_total",
                "have hright_decode : exists rp rn. "
                "((right = 2 * rp /\\ rn = 0) \\/ "
                "exists sd_half_add_total_right. "
                "((right = 2 * sd_half_add_total_right + 1 /\\ rp = 0) /\\ "
                "rn = S sd_half_add_total_right))",
                "specialize hdecode_right_all right",
                "exact hdecode_right_all",
                "have hleft_decode : exists lp ln. "
                "((left = 2 * lp /\\ ln = 0) \\/ "
                "exists sd_half_add_total_left. "
                "((left = 2 * sd_half_add_total_left + 1 /\\ lp = 0) /\\ "
                "ln = S sd_half_add_total_left))",
                "specialize signed_decode_total left",
                "exact signed_decode_total",
                "cases hleft_decode",
                "cases hleft_decode_witness",
                "cases hright_decode",
                "cases hright_decode_witness",
                "specialize signed_balance_total (x + x2)",
                "specialize signed_balance_total (x1 + x3)",
                "cases signed_balance_total",
                "cases signed_balance_total_witness",
                "cases signed_balance_total_witness_witness",
                "cases signed_balance_total_witness_witness_witness",
                "exists x4",
                "specialize signed_add_of_decoded_equation left",
                "specialize signed_add_of_decoded_equation right",
                "specialize signed_add_of_decoded_equation x4",
                "specialize signed_add_of_decoded_equation x",
                "specialize signed_add_of_decoded_equation x1",
                "specialize signed_add_of_decoded_equation x2",
                "specialize signed_add_of_decoded_equation x3",
                "specialize signed_add_of_decoded_equation x5",
                "specialize signed_add_of_decoded_equation x6",
                "apply signed_add_of_decoded_equation",
                "exact hleft_decode_witness_witness",
                "exact hright_decode_witness_witness",
                "exact signed_balance_total_witness_witness_witness_left",
                "exact signed_balance_total_witness_witness_witness_right",
            ),
            "Every pair of canonical signed-natural codes has a canonical sum.",
        ),
        spec(
            "signed_add_functional",
            "forall left right output1 output2. "
            f"({functional_left}) -> ({functional_right}) -> output1 = output2",
            (
                "signed_add_to_decoded_equation",
                "signed_balance_functional",
            ),
            (
                "intro left",
                "intro right",
                "intro output1",
                "intro output2",
                "intro hadd1",
                "intro hadd2",
                "cases hadd1",
                "cases hadd1_witness",
                "cases hadd1_witness_witness",
                "cases hadd1_witness_witness_witness",
                "cases hadd1_witness_witness_witness_witness",
                "cases hadd1_witness_witness_witness_witness_witness",
                "cases hadd1_witness_witness_witness_witness_witness_witness",
                "cases hadd1_witness_witness_witness_witness_witness_witness_right",
                "cases hadd1_witness_witness_witness_witness_witness_witness_right_right",
                "cases hadd2",
                "cases hadd2_witness",
                "cases hadd2_witness_witness",
                "cases hadd2_witness_witness_witness",
                "cases hadd2_witness_witness_witness_witness",
                "cases hadd2_witness_witness_witness_witness_witness",
                "cases hadd2_witness_witness_witness_witness_witness_witness",
                "cases hadd2_witness_witness_witness_witness_witness_witness_right",
                "cases hadd2_witness_witness_witness_witness_witness_witness_right_right",
                "have hequation2 : (x + x2) + x11 = (x1 + x3) + x10",
                "specialize signed_add_to_decoded_equation left",
                "specialize signed_add_to_decoded_equation right",
                "specialize signed_add_to_decoded_equation output2",
                "specialize signed_add_to_decoded_equation x",
                "specialize signed_add_to_decoded_equation x1",
                "specialize signed_add_to_decoded_equation x2",
                "specialize signed_add_to_decoded_equation x3",
                "specialize signed_add_to_decoded_equation x10",
                "specialize signed_add_to_decoded_equation x11",
                "apply signed_add_to_decoded_equation",
                "exact hadd1_witness_witness_witness_witness_witness_witness_left",
                "exact hadd1_witness_witness_witness_witness_witness_witness_right_left",
                "exact hadd2_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hadd2",
                "have hbalance1 : exists op on. "
                "((((output1 = 2 * op /\\ on = 0) \\/ "
                "exists sd_half_add_functional_balance1. "
                "((output1 = 2 * sd_half_add_functional_balance1 + 1 /\\ op = 0) /\\ "
                "on = S sd_half_add_functional_balance1))) /\\ "
                "(x + x2) + on = (x1 + x3) + op)",
                "exists x4",
                "exists x5",
                "split",
                "exact hadd1_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hadd1_witness_witness_witness_witness_witness_witness_right_right_right",
                "have hbalance2 : exists op on. "
                "((((output2 = 2 * op /\\ on = 0) \\/ "
                "exists sd_half_add_functional_balance2. "
                "((output2 = 2 * sd_half_add_functional_balance2 + 1 /\\ op = 0) /\\ "
                "on = S sd_half_add_functional_balance2))) /\\ "
                "(x + x2) + on = (x1 + x3) + op)",
                "exists x10",
                "exists x11",
                "split",
                "exact hadd2_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact hequation2",
                "specialize signed_balance_functional (x + x2)",
                "specialize signed_balance_functional (x1 + x3)",
                "specialize signed_balance_functional output1",
                "specialize signed_balance_functional output2",
                "apply signed_balance_functional",
                "exact hbalance1",
                "exact hbalance2",
            ),
            "Canonical signed addition has a unique literal natural-code output.",
        ),
    )


__all__ = ["make_ha_signed_add_candidate_theorems", "signed_add"]
