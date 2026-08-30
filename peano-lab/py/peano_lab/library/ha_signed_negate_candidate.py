"""Strict-HA candidates for canonical signed negation.

``SignedNegate(input, output)`` is the graph obtained by decoding ``input``
as the normalized pair ``(pos, neg)`` and decoding ``output`` as the swapped
pair ``(neg, pos)``.  The relation is expanded hygienically into the
unchanged first-order language ``{0,S,+,*,=}``; it is not a parser or kernel
primitive.

The eight specifications below form the first signed-arithmetic tranche.
They are constructive, dependency-curried, unregistered, and unadmitted.
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


def signed_negate(input_code: str, output_code: str, *, tag: str) -> str:
    """Expand RFC ``HA-K3-SIGNED-D04`` hygienically in a variable context."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (input_code, "input code"),
            (output_code, "output code"),
        )
    )
    input_code, output_code = variables
    safe_tag = _identifier(tag, "binder tag")
    pos = f"sn_pos_{safe_tag}"
    neg = f"sn_neg_{safe_tag}"
    if pos in variables or neg in variables:
        raise ValueError("generated SignedNegate binder captures an argument")
    input_decode = signed_decode(
        input_code, pos, neg, tag=f"{safe_tag}_input"
    )
    output_decode = signed_decode(
        output_code, neg, pos, tag=f"{safe_tag}_output"
    )
    return f"exists {pos} {neg}. (({input_decode}) /\\ ({output_decode}))"


def make_ha_signed_negate_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the eight canonical signed-negation candidates in order."""

    swap_source = signed_decode("input", "pos", "neg", tag="swap_source")
    swap_target = signed_decode("output", "neg", "pos", tag="swap_target")
    intro_source = signed_decode("input", "pos", "neg", tag="intro_source")
    intro_target = signed_decode("output", "neg", "pos", tag="intro_target")
    intro_negate = signed_negate("input", "output", tag="intro")
    elim_source = signed_decode("input", "pos", "neg", tag="elim_source")
    elim_negate = signed_negate("input", "output", tag="elim")
    elim_target = signed_decode("output", "neg", "pos", tag="elim_target")
    total_negate = signed_negate("input", "output", tag="total")
    functional_left = signed_negate(
        "input", "output1", tag="functional_left"
    )
    functional_right = signed_negate(
        "input", "output2", tag="functional_right"
    )
    zero_negate = (
        "exists sn_pos_zero sn_neg_zero. "
        "(((0 = 2 * sn_pos_zero /\\ sn_neg_zero = 0) \\/ "
        "exists sd_half_zero_input. "
        "((0 = 2 * sd_half_zero_input + 1 /\\ sn_pos_zero = 0) /\\ "
        "sn_neg_zero = S sd_half_zero_input)) /\\ "
        "((0 = 2 * sn_neg_zero /\\ sn_pos_zero = 0) \\/ "
        "exists sd_half_zero_output. "
        "((0 = 2 * sd_half_zero_output + 1 /\\ sn_neg_zero = 0) /\\ "
        "sn_pos_zero = S sd_half_zero_output)))"
    )
    symmetric_forward = signed_negate(
        "input", "output", tag="symmetric_forward"
    )
    symmetric_reverse = signed_negate(
        "output", "input", tag="symmetric_reverse"
    )
    involution_first = signed_negate(
        "input", "middle", tag="involution_first"
    )
    involution_second = signed_negate(
        "middle", "output", tag="involution_second"
    )

    return (
        spec(
            "signed_decode_swap_exists",
            f"forall input pos neg. ({swap_source}) -> "
            f"exists output. ({swap_target})",
            ("zero_or_succ",),
            (
                "intro input",
                "intro pos",
                "intro neg",
                "intro hdecode",
                "cases hdecode",
                "cases hdecode_left",
                "specialize zero_or_succ pos",
                "cases zero_or_succ",
                "exists 0",
                "left",
                "split",
                "rewrite hdecode_left_right",
                "rewrite PA5",
                "refl",
                "exact zero_or_succ_left",
                "cases zero_or_succ_right",
                "exists 2 * x + 1",
                "right",
                "exists x",
                "split",
                "split",
                "refl",
                "exact hdecode_left_right",
                "exact zero_or_succ_right_witness",
                "cases hdecode_right",
                "cases hdecode_right_witness",
                "cases hdecode_right_witness_left",
                "exists 2 * S x",
                "left",
                "split",
                "rewrite hdecode_right_witness_right",
                "refl",
                "exact hdecode_right_witness_left_right",
            ),
            "A normalized decoder witness has a canonical code for its "
            "swapped pair.",
        ),
        spec(
            "signed_negate_of_swapped_decode",
            f"forall input output pos neg. ({intro_source}) -> "
            f"({intro_target}) -> ({intro_negate})",
            (),
            (
                "intro input",
                "intro output",
                "intro pos",
                "intro neg",
                "intro hinput",
                "intro houtput",
                "exists pos",
                "exists neg",
                "split",
                "exact hinput",
                "exact houtput",
            ),
            "An input decoding and its swapped output decoding construct "
            "signed negation.",
        ),
        spec(
            "signed_negate_to_swapped_decode",
            f"forall input output pos neg. ({elim_source}) -> "
            f"({elim_negate}) -> ({elim_target})",
            ("signed_decode_functional",),
            (
                "intro input",
                "intro output",
                "intro pos",
                "intro neg",
                "intro hinput",
                "intro hnegate",
                "cases hnegate",
                "cases hnegate_witness",
                "cases hnegate_witness_witness",
                "have hparts : x = pos /\\ x1 = neg",
                "specialize signed_decode_functional input",
                "specialize signed_decode_functional x",
                "specialize signed_decode_functional x1",
                "specialize signed_decode_functional pos",
                "specialize signed_decode_functional neg",
                "apply signed_decode_functional",
                "exact hnegate_witness_witness_left",
                "exact hinput",
                "cases hparts",
                "rewrite hparts_left at hnegate_witness_witness_right",
                "rewrite hparts_left at hnegate_witness_witness_right",
                "rewrite hparts_right at hnegate_witness_witness_right",
                "rewrite hparts_right at hnegate_witness_witness_right",
                "exact hnegate_witness_witness_right",
            ),
            "Relative to a fixed input decoding, signed negation exposes the "
            "swapped output decoding.",
        ),
        spec(
            "signed_negate_total",
            f"forall input. exists output. ({total_negate})",
            (
                "signed_decode_total",
                "signed_decode_swap_exists",
                "signed_negate_of_swapped_decode",
            ),
            (
                "intro input",
                "specialize signed_decode_total input",
                "cases signed_decode_total",
                "cases signed_decode_total_witness",
                "have hswap : exists output. "
                "((output = 2 * x1 /\\ x = 0) \\/ "
                "exists sd_half_total_swap. "
                "((output = 2 * sd_half_total_swap + 1 /\\ x1 = 0) /\\ "
                "x = S sd_half_total_swap))",
                "specialize signed_decode_swap_exists input",
                "specialize signed_decode_swap_exists x",
                "specialize signed_decode_swap_exists x1",
                "apply signed_decode_swap_exists",
                "exact signed_decode_total_witness_witness",
                "cases hswap",
                "exists x2",
                "specialize signed_negate_of_swapped_decode input",
                "specialize signed_negate_of_swapped_decode x2",
                "specialize signed_negate_of_swapped_decode x",
                "specialize signed_negate_of_swapped_decode x1",
                "apply signed_negate_of_swapped_decode",
                "exact signed_decode_total_witness_witness",
                "exact hswap_witness",
            ),
            "Every canonical signed-natural code has a canonical negation.",
        ),
        spec(
            "signed_negate_functional",
            "forall input output1 output2. "
            f"({functional_left}) -> ({functional_right}) -> "
            "output1 = output2",
            (
                "signed_negate_to_swapped_decode",
                "signed_decoded_balance_implies_code_eq",
                "add_comm",
            ),
            (
                "intro input",
                "intro output1",
                "intro output2",
                "intro hleft",
                "intro hright",
                "cases hleft",
                "cases hleft_witness",
                "cases hleft_witness_witness",
                "have hout2 : "
                "((output2 = 2 * x1 /\\ x = 0) \\/ "
                "exists sd_half_functional_derived. "
                "((output2 = 2 * sd_half_functional_derived + 1 /\\ "
                "x1 = 0) /\\ x = S sd_half_functional_derived))",
                "specialize signed_negate_to_swapped_decode input",
                "specialize signed_negate_to_swapped_decode output2",
                "specialize signed_negate_to_swapped_decode x",
                "specialize signed_negate_to_swapped_decode x1",
                "apply signed_negate_to_swapped_decode",
                "exact hleft_witness_witness_left",
                "exact hright",
                "specialize signed_decoded_balance_implies_code_eq output1",
                "specialize signed_decoded_balance_implies_code_eq x1",
                "specialize signed_decoded_balance_implies_code_eq x",
                "specialize signed_decoded_balance_implies_code_eq output2",
                "specialize signed_decoded_balance_implies_code_eq x1",
                "specialize signed_decoded_balance_implies_code_eq x",
                "apply signed_decoded_balance_implies_code_eq",
                "exact hleft_witness_witness_right",
                "exact hout2",
                "specialize add_comm x1",
                "specialize add_comm x",
                "exact add_comm",
            ),
            "Signed negation has a unique literal natural-code output.",
        ),
        spec(
            "signed_negate_zero",
            zero_negate,
            (),
            (
                "exists 0",
                "exists 0",
                "split",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
                "left",
                "split",
                "rewrite PA5",
                "refl",
                "refl",
            ),
            "Signed negation fixes the canonical zero code.",
        ),
        spec(
            "signed_negate_symmetric",
            f"forall input output. ({symmetric_forward}) -> "
            f"({symmetric_reverse})",
            (),
            (
                "intro input",
                "intro output",
                "intro hnegate",
                "cases hnegate",
                "cases hnegate_witness",
                "cases hnegate_witness_witness",
                "exists x1",
                "exists x",
                "split",
                "exact hnegate_witness_witness_right",
                "exact hnegate_witness_witness_left",
            ),
            "The signed-negation graph is symmetric by swapping its decoded "
            "parts.",
        ),
        spec(
            "signed_negate_involutive",
            "forall input middle output. "
            f"({involution_first}) -> ({involution_second}) -> "
            "output = input",
            (
                "signed_negate_symmetric",
                "signed_negate_functional",
            ),
            (
                "intro input",
                "intro middle",
                "intro output",
                "intro hfirst",
                "intro hsecond",
                "have hreverse : "
                f"({signed_negate('middle', 'input', tag='involution_reverse')})",
                "specialize signed_negate_symmetric input",
                "specialize signed_negate_symmetric middle",
                "apply signed_negate_symmetric",
                "exact hfirst",
                "specialize signed_negate_functional middle",
                "specialize signed_negate_functional output",
                "specialize signed_negate_functional input",
                "apply signed_negate_functional",
                "exact hsecond",
                "exact hreverse",
            ),
            "Two successive signed negations return the literal input code.",
        ),
    )


__all__ = [
    "make_ha_signed_negate_candidate_theorems",
    "signed_negate",
]
