"""Constructive multiplicative order laws for the Bertrand campaign.

This isolated candidate tranche supplies the first quantitative arithmetic
facts needed by the central-binomial route.  It combines the existing
one-sided multiplication monotonicity theorems into a two-sided law, records
the two useful ``1 <=`` factor embeddings, and proves that the relational
``Pow`` operation is monotone in its base.

Every order relation is expanded to an additive witness and every ``Pow``
occurrence is expanded through the existing beta-coded finite-fold surface.
The module adds no primitive notation, kernel rule, classical principle, or
admitted theorem.  The factory remains outside every library edition until a
separate enrollment and closure tranche is reviewed.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists bpo_gap_{tag}. bpo_gap_{tag} + ({left}) = ({right})"


def make_bertrand_power_order_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the first four reusable quantitative-order candidates."""

    base_le = _le("a", "b", tag="pow_base")
    result_le = _le("x", "y", tag="pow_result")
    pow_left = power_relation("a", "e", "x", tag="bpo_left")
    pow_right = power_relation("b", "e", "y", tag="bpo_right")
    pow_left_prefix = power_relation("a", "e", "r", tag="bpo_left_prefix")
    pow_right_prefix = power_relation("b", "e", "s", tag="bpo_right_prefix")

    return (
        spec(
            "mul_le_mul",
            "forall a b c d. "
            f"({_le('a', 'b', tag='mul_left')}) -> "
            f"({_le('c', 'd', tag='mul_right')}) -> "
            f"({_le('a * c', 'b * d', tag='mul_result')})",
            ("mul_le_mul_right", "mul_le_mul_left", "le_trans"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hab",
                "intro hcd",
                "have hacbc : exists k. k + a * c = b * c",
                "specialize mul_le_mul_right a",
                "specialize mul_le_mul_right b",
                "specialize mul_le_mul_right c",
                "apply mul_le_mul_right",
                "exact hab",
                "have hbcbd : exists k. k + b * c = b * d",
                "specialize mul_le_mul_left c",
                "specialize mul_le_mul_left d",
                "specialize mul_le_mul_left b",
                "apply mul_le_mul_left",
                "exact hcd",
                "specialize le_trans (a * c)",
                "specialize le_trans (b * c)",
                "specialize le_trans (b * d)",
                "apply le_trans",
                "exact hacbc",
                "exact hbcbd",
            ),
            "Multiplication is monotone in both natural-number arguments.",
        ),
        spec(
            "le_mul_of_one_le_right",
            "forall a b. "
            f"({_le('1', 'b', tag='right_factor')}) -> "
            f"({_le('a', 'a * b', tag='right_result')})",
            ("mul_le_mul_left", "mul_one"),
            (
                "intro a",
                "intro b",
                "intro hb",
                "have hscaled : exists k. k + a * 1 = a * b",
                "specialize mul_le_mul_left 1",
                "specialize mul_le_mul_left b",
                "specialize mul_le_mul_left a",
                "apply mul_le_mul_left",
                "exact hb",
                "specialize mul_one a",
                "rewrite mul_one at hscaled",
                "exact hscaled",
            ),
            "A factor at least one makes right multiplication extensive.",
        ),
        spec(
            "le_mul_of_one_le_left",
            "forall a b. "
            f"({_le('1', 'a', tag='left_factor')}) -> "
            f"({_le('b', 'a * b', tag='left_result')})",
            ("mul_le_mul_right", "one_mul"),
            (
                "intro a",
                "intro b",
                "intro ha",
                "have hscaled : exists k. k + 1 * b = a * b",
                "specialize mul_le_mul_right 1",
                "specialize mul_le_mul_right a",
                "specialize mul_le_mul_right b",
                "apply mul_le_mul_right",
                "exact ha",
                "specialize one_mul b",
                "rewrite one_mul at hscaled",
                "exact hscaled",
            ),
            "A factor at least one makes left multiplication extensive.",
        ),
        spec(
            "pow_base_monotone",
            "forall a b e x y. "
            f"({base_le}) -> ({pow_left}) -> ({pow_right}) -> ({result_le})",
            (
                "pow_zero",
                "pow_successor_decompose",
                "le_refl",
                "mul_le_mul",
            ),
            (
                "intro a",
                "intro b",
                "intro e",
                "induction e",
                "intro x",
                "intro y",
                "intro hab",
                "intro hx",
                "intro hy",
                "have hx1 : x = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero x",
                "apply pow_zero",
                "refl",
                "exact hx",
                "have hy1 : y = 1",
                "specialize pow_zero b",
                "specialize pow_zero 0",
                "specialize pow_zero y",
                "apply pow_zero",
                "refl",
                "exact hy",
                "rewrite hx1",
                "rewrite hy1",
                "specialize le_refl 1",
                "exact le_refl",
                "intro x",
                "intro y",
                "intro hab",
                "intro hx",
                "intro hy",
                f"have hxstep : exists r. ({pow_left_prefix}) /\\ x = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "refl",
                "exact hx",
                "cases hxstep",
                "cases hxstep_witness",
                f"have hystep : exists s. ({pow_right_prefix}) /\\ y = s * b",
                "specialize pow_successor_decompose b",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose y",
                "apply pow_successor_decompose",
                "refl",
                "exact hy",
                "cases hystep",
                "cases hystep_witness",
                "have hpref : exists k. k + x1 = x2",
                "specialize IH x1",
                "specialize IH x2",
                "apply IH",
                "exact hab",
                "exact hxstep_witness_left",
                "exact hystep_witness_left",
                "rewrite hxstep_witness_right",
                "rewrite hystep_witness_right",
                "specialize mul_le_mul x1",
                "specialize mul_le_mul x2",
                "specialize mul_le_mul a",
                "specialize mul_le_mul b",
                "apply mul_le_mul",
                "exact hpref",
                "exact hab",
            ),
            "Relational powers are monotone in the base at every exponent.",
        ),
    )


__all__ = ["make_bertrand_power_order_candidate_theorems"]
