"""Working congruence of actual convolution under formal coefficient equality.

Representation lengths and beta encodings may differ independently in either
factor.  The proof recovers genuine leading-zero padding in the appropriate
length direction and constructs a real mixed product.  No output equality,
evaluation identity, prime hypothesis, or canonical-code choice is assumed.
This module registers no theorem and changes no released proof gate.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _call, _intro, _parts
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _convolution, _le, _length,
)
from peano_lab.library.prime_field_polynomial_representation_candidate import (
    _equivalent, _left_pad,
)
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return f"forall {' '.join(parameters)}. " + " -> ".join(
        f"({part})" for part in (*premises, result))


def _one_factor_branch(side: str, forward: bool) -> tuple[str, ...]:
    original = ("ab", "ac", "L") if side == "left" else ("bb", "bc", "M")
    replacement = ("AB", "AC", "H") if side == "left" else ("BB", "BC", "H")
    old_factors = ("ab", "ac", "L", "bb", "bc", "M")
    new_factors = (*replacement, "bb", "bc", "M") if side == "left" else ("ab", "ac", "L", *replacement)
    smaller, larger = (original, replacement) if forward else (replacement, original)
    order = "horder_left" if forward else "horder_right"
    equality = order + "_witness"
    shifted = "x+" + smaller[2]
    body = ("cases " + order,
        f"have hpadding : {_left_pad(*smaller, 'x', *larger[:2], 'congruent_padding_' + side)}")
    body += _call("prime_field_polynomial_equivalent_implies_left_pad", *smaller, "x", *larger[:2])
    expanded = _equivalent(*smaller, *larger[:2], shifted, "congruent_padding_equivalence_" + side)
    body += _rewrite_all(equality, expanded, shifted)
    if not forward:
        body += _call("prime_field_polynomial_equivalent_symmetric", *original, *replacement)
    body += ("exact he",)
    if not forward:
        body += _call("prime_field_polynomial_equivalent_symmetric", "CB", "CC", "K", "cb", "cc", "N")
    source_factors = old_factors if forward else new_factors
    source_output = ("cb", "cc", "N") if forward else ("CB", "CC", "K")
    target_output = ("CB", "CC", "K") if forward else ("cb", "cc", "N")
    body += _call("prime_field_polynomial_convolution_left_padding_equivalent_" + side,
                  "p", *source_factors, *source_output, *larger[:2], "x", *target_output)
    body += ("exact hp", "exact hpadding", "exact " + ("hc" if forward else "hd"))
    shifted_factors = (*larger[:2], shifted, "bb", "bc", "M") if side == "left" else (
        "ab", "ac", "L", *larger[:2], shifted)
    expanded = _convolution("p", *shifted_factors, *target_output, "congruent_shifted_product_" + side)
    body += _rewrite_all(equality, expanded, shifted)
    body += ("exact " + ("hd" if forward else "hc"),)
    return body


def _one_factor_row(spec: Callable[..., Any], side: str) -> Any:
    original = ("ab", "ac", "L") if side == "left" else ("bb", "bc", "M")
    replacement = ("AB", "AC", "H") if side == "left" else ("BB", "BC", "H")
    parameters = ("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N",
                  *replacement, "CB", "CC", "K")
    new_factors = (*replacement, "bb", "bc", "M") if side == "left" else (
        "ab", "ac", "L", *replacement)
    body = _intro(*parameters, "hp", "he", "hc", "hd")
    body += (f"have horder : ({_le(original[2], 'H', 'congruent_forward_' + side)}) \\/ "
             f"({_le('H', original[2], 'congruent_backward_' + side)})",)
    body += _call("le_total", original[2], "H") + ("cases horder",)
    body += _one_factor_branch(side, True) + _one_factor_branch(side, False)
    return spec(
        "prime_field_polynomial_convolution_equivalent_congruent_" + side,
        _contract(parameters, (
            "~(p=0)", _equivalent(*original, *replacement, "congruent_factor_" + side),
            _convolution("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N", "congruent_original_" + side),
            _convolution("p", *new_factors, "CB", "CC", "K", "congruent_other_" + side),
        ), _equivalent("cb", "cc", "N", "CB", "CC", "K", "congruent_output_" + side)),
        ("le_total", "prime_field_polynomial_equivalent_implies_left_pad",
         "prime_field_polynomial_equivalent_symmetric",
         "prime_field_polynomial_convolution_left_padding_equivalent_" + side),
        body,
        "Formal coefficient equivalence of the " + side + " factor preserves two actual products at arbitrary representation lengths, including empty factors; actual leading padding is recovered in the appropriate direction.",
    )


def _both_factors_row(spec: Callable[..., Any]) -> Any:
    parameters = ("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N",
                  "AB", "AC", "H", "BB", "BC", "I", "CB", "CC", "K")
    old = _convolution("p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N", "congruent_both_original")
    new = _convolution("p", "AB", "AC", "H", "BB", "BC", "I", "CB", "CC", "K", "congruent_both_other")
    body = _intro(*parameters, "hp", "hA", "hB", "hc", "hd")
    body += (f"have hsource : {old}", "exact hc") + _parts("hsource", 4)
    body += (f"have htarget : {new}", "exact hd") + _parts("htarget", 4)
    body += (f"have hlength : exists J. {_length('H', 'M', 'J', 'congruent_middle_length')}",)
    body += _call("polynomial_product_length_exists", "H", "M") + ("cases hlength",)
    body += (f"have hmiddle : exists db dc. {_convolution('p', 'AB', 'AC', 'H', 'bb', 'bc', 'M', 'db', 'dc', 'x', 'congruent_middle_product')}",)
    body += _call("prime_field_polynomial_convolution_at_length_exists", "p", "AB", "AC", "H", "bb", "bc", "M", "x")
    body += ("exact hp", "exact htarget_left", "exact hsource_right_left", "exact hlength_witness",
             "cases hmiddle", "cases hmiddle_witness")
    body += _call("prime_field_polynomial_equivalent_transitive", "cb", "cc", "N", "x1", "x2", "x", "CB", "CC", "K")
    body += _call("prime_field_polynomial_convolution_equivalent_congruent_left",
                  "p", "ab", "ac", "L", "bb", "bc", "M", "cb", "cc", "N", "AB", "AC", "H", "x1", "x2", "x")
    body += ("exact hp", "exact hA", "exact hc", "exact hmiddle_witness_witness")
    body += _call("prime_field_polynomial_convolution_equivalent_congruent_right",
                  "p", "AB", "AC", "H", "bb", "bc", "M", "x1", "x2", "x", "BB", "BC", "I", "CB", "CC", "K")
    body += ("exact hp", "exact hB", "exact hmiddle_witness_witness", "exact hd")
    return spec(
        "prime_field_polynomial_convolution_equivalent_congruent",
        _contract(parameters, (
            "~(p=0)",
            _equivalent("ab", "ac", "L", "AB", "AC", "H", "congruent_both_left"),
            _equivalent("bb", "bc", "M", "BB", "BC", "I", "congruent_both_right"), old, new,
        ), _equivalent("cb", "cc", "N", "CB", "CC", "K", "congruent_both_result")),
        ("polynomial_product_length_exists", "prime_field_polynomial_convolution_at_length_exists",
         "prime_field_polynomial_equivalent_transitive",
         "prime_field_polynomial_convolution_equivalent_congruent_left",
         "prime_field_polynomial_convolution_equivalent_congruent_right"),
        body,
        "Two actual convolution outputs represent the same formal polynomial whenever their respective factors do, with all four representation lengths independent. A genuine mixed product is constructed from canonical inputs supplied by the actual products; no output identity or extra field hypothesis is assumed.",
    )


def make_prime_field_polynomial_convolution_congruence_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_one_factor_row(spec, "left"), _one_factor_row(spec, "right"), _both_factors_row(spec))


__all__ = ["make_prime_field_polynomial_convolution_congruence_candidate_theorems"]
