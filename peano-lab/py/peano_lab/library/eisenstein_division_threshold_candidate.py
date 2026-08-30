"""Constructive threshold arithmetic for Eisenstein row counts.

If ``n = p*q+r`` with a nonzero remainder strictly below ``p``, then the
positive multiple ``p*(j+1)`` lies below ``n`` exactly when ``j+1`` is at
most the quotient ``q``.  This is the arithmetic bridge between one semantic
row-indicator bit and the initial segment counted by that row's quotient.

The proof is independent of beta codes and finite folds.  Its forward half
uses the checked upper-block bound ``n < p*(q+1)`` and constructive order
comparison; its reverse half uses the nonzero remainder as the strict gap
above ``p*q``.  All displayed order relations expand to witness-defined
first-order PA formulas, and this candidate remains outside the registry.
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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"edt_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Eisenstein-threshold binder captures an argument")
    return names


def _lt_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("lt_gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _le_term(
    left: str,
    right: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, variables, ("le_gap",))
    return f"exists {gap}. {gap} + ({left}) = {right}"


def division_positive_multiple_threshold(
    divisor: str,
    dividend: str,
    quotient: str,
    index: str,
    *,
    tag: str,
) -> str:
    """Expand ``p*S(j)<n`` iff ``S(j)<=q`` for named native terms."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (divisor, "divisor"),
            (dividend, "dividend"),
            (quotient, "quotient"),
            (index, "positive-multiple index"),
        )
    )
    below = _lt_term(
        f"{divisor} * S {index}",
        dividend,
        tag=f"{tag}_below",
        variables=variables,
    )
    bounded = _le_term(
        f"S {index}",
        quotient,
        tag=f"{tag}_bounded",
        variables=variables,
    )
    return f"((({below}) -> ({bounded})) /\\ (({bounded}) -> ({below})))"


def make_eisenstein_division_threshold_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the nonzero-remainder positive-multiple threshold theorem."""

    remainder_bound = _lt_term(
        "r",
        "p",
        tag="division_threshold_remainder_bound",
        variables=("p", "n", "q", "r", "j"),
    )
    below = _lt_term(
        "p * S j",
        "n",
        tag="division_threshold_below",
        variables=("p", "n", "q", "r", "j"),
    )
    bounded = _le_term(
        "S j",
        "q",
        tag="division_threshold_bounded",
        variables=("p", "n", "q", "r", "j"),
    )
    block_upper = _lt_term(
        "n",
        "p * S q",
        tag="division_threshold_block_upper",
        variables=("p", "n", "q", "r", "j"),
    )
    strict_products = _lt_term(
        "p * S j",
        "p * S q",
        tag="division_threshold_strict_products",
        variables=("p", "n", "q", "r", "j"),
    )
    quotient_reverse = _lt_term(
        "q",
        "S j",
        tag="division_threshold_quotient_reverse",
        variables=("p", "n", "q", "r", "j"),
    )
    quotient_reverse_le = _le_term(
        "S q",
        "S j",
        tag="division_threshold_quotient_reverse_le",
        variables=("p", "n", "q", "r", "j"),
    )
    products_reverse_le = _le_term(
        "p * S q",
        "p * S j",
        tag="division_threshold_products_reverse_le",
        variables=("p", "n", "q", "r", "j"),
    )
    products_forward_le = _le_term(
        "p * S j",
        "p * q",
        tag="division_threshold_products_forward_le",
        variables=("p", "n", "q", "r", "j"),
    )
    positive_remainder_gap = _lt_term(
        "p * q",
        "n",
        tag="division_threshold_positive_remainder_gap",
        variables=("p", "n", "q", "r", "j"),
    )
    result = division_positive_multiple_threshold(
        "p", "n", "q", "j", tag="division_threshold_result"
    )

    return (
        spec(
            "nonzero_remainder_division_positive_multiple_threshold",
            "forall p n q r j. n = p * q + r -> ~(r = 0) -> "
            f"({remainder_bound}) -> ({result})",
            (
                "division_block_upper",
                "lt_trans",
                "le_or_lt",
                "mul_le_mul_left",
                "lt_not_le",
                "nonzero_is_succ",
                "add_comm",
                "lt_of_le_of_lt",
            ),
            (
                "intro p",
                "intro n",
                "intro q",
                "intro r",
                "intro j",
                "intro hdivision",
                "intro hr0",
                "intro hrp",
                "split",
                "intro hbelow",
                f"have hupper : {block_upper}",
                "rewrite hdivision",
                "specialize division_block_upper p",
                "specialize division_block_upper q",
                "specialize division_block_upper r",
                "apply division_block_upper",
                "exact hrp",
                f"have hstrict : {strict_products}",
                "specialize lt_trans (p * S j)",
                "specialize lt_trans n",
                "specialize lt_trans (p * S q)",
                "apply lt_trans",
                "exact hbelow",
                "exact hupper",
                "specialize le_or_lt (S j)",
                "specialize le_or_lt q",
                "cases le_or_lt",
                "exact le_or_lt_left",
                f"have hqreverse : {quotient_reverse}",
                "exact le_or_lt_right",
                f"have hqle : {quotient_reverse_le}",
                "exact hqreverse",
                f"have hproduct_le : {products_reverse_le}",
                "specialize mul_le_mul_left (S q)",
                "specialize mul_le_mul_left (S j)",
                "specialize mul_le_mul_left p",
                "apply mul_le_mul_left",
                "exact hqle",
                "exfalso",
                "specialize lt_not_le (p * S j)",
                "specialize lt_not_le (p * S q)",
                "apply lt_not_le",
                "exact hstrict",
                "exact hproduct_le",
                "intro hbounded",
                f"have hproduct_le : {products_forward_le}",
                "specialize mul_le_mul_left (S j)",
                "specialize mul_le_mul_left q",
                "specialize mul_le_mul_left p",
                "apply mul_le_mul_left",
                "exact hbounded",
                "have hr_succ : exists t. r = S t",
                "specialize nonzero_is_succ r",
                "apply nonzero_is_succ",
                "exact hr0",
                "cases hr_succ",
                f"have hpositive : {positive_remainder_gap}",
                "rewrite hdivision",
                "exists x",
                "rewrite hr_succ_witness",
                "simp [add_comm]",
                "specialize lt_of_le_of_lt (p * S j)",
                "specialize lt_of_le_of_lt (p * q)",
                "specialize lt_of_le_of_lt n",
                "apply lt_of_le_of_lt",
                "exact hproduct_le",
                "exact hpositive",
            ),
            "A positive multiple lies below a nonintegral division value exactly through the quotient threshold.",
        ),
    )


__all__ = [
    "division_positive_multiple_threshold",
    "make_eisenstein_division_threshold_candidate_theorems",
]
