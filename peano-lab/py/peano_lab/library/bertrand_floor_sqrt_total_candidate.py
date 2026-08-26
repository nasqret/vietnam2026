"""Constructive totality and monotonicity of the Bertrand floor-square graph.

This isolated candidate layer reuses the exact expanded relation from
``bertrand_ceil_sqrt_candidate``.  For the induction step at ``S x``, a stored
root ``s`` supplies ``S x <= (S s)^2``.  Constructive bounded comparison then
chooses either equality, in which case the root advances to ``S s``, or a
strict bound, in which case the root remains ``s``.

No square-root function, subtraction, classical principle, or host
computation occurs in a theorem certificate.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation


def make_bertrand_floor_sqrt_total_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-closed FloorSqrt totality tranche."""

    total_result = floor_sqrt_relation("x", "s", tag="total_result")
    unique_result = floor_sqrt_relation("x", "s", tag="unique_result")
    unique_comparison = floor_sqrt_relation(
        "x", "t", tag="unique_comparison"
    )
    monotone_left = floor_sqrt_relation("x", "s", tag="monotone_left")
    monotone_right = floor_sqrt_relation("y", "t", tag="monotone_right")

    return (
        spec(
            "square_lt_successor_square",
            "forall s. exists k. k + S (s * s) = S s * S s",
            (
                "le_succ_self",
                "mul_le_mul_right",
                "succ_ne_zero",
                "mul_lt_mul_succ_left_nonzero",
                "lt_of_le_of_lt",
            ),
            (
                "intro s",
                "have hleft : exists k. k + s * s = S s * s",
                "apply mul_le_mul_right",
                "apply le_succ_self",
                "have hright : exists k. k + S (S s * s) = S s * S s",
                "apply mul_lt_mul_succ_left_nonzero",
                "intro hz",
                "specialize succ_ne_zero s",
                "apply succ_ne_zero",
                "exact hz",
                "specialize lt_of_le_of_lt (s * s)",
                "specialize lt_of_le_of_lt (S s * s)",
                "specialize lt_of_le_of_lt (S s * S s)",
                "apply lt_of_le_of_lt",
                "exact hleft",
                "exact hright",
            ),
            "Every square is strictly below the next natural square.",
        ),
        spec(
            "floor_sqrt_total",
            f"forall x. exists s. ({total_result})",
            (
                "square_lt_successor_square",
                "le_eq_or_lt",
                "zero_add",
                "le_succ",
            ),
            (
                "induction x",
                "exists 0",
                "split",
                "exists 0",
                "norm_num",
                "exists 0",
                "norm_num",
                "cases IH",
                "cases IH_witness",
                "have hsplit : S x = S x1 * S x1 \\/ "
                "exists k. k + S (S x) = S x1 * S x1",
                "specialize le_eq_or_lt (S x)",
                "specialize le_eq_or_lt (S x1 * S x1)",
                "apply le_eq_or_lt",
                "exact IH_witness_right",
                "cases hsplit",
                "exists S x1",
                "split",
                "exists 0",
                "trans S x1 * S x1",
                "apply zero_add",
                "symm",
                "exact hsplit_left",
                "specialize square_lt_successor_square (S x1)",
                "rewrite hsplit_left",
                "exact square_lt_successor_square",
                "exists x1",
                "split",
                "specialize le_succ (x1 * x1)",
                "specialize le_succ x",
                "apply le_succ",
                "exact IH_witness_left",
                "exact hsplit_right",
            ),
            "Every natural lies in a constructively selected adjacent-square interval.",
        ),
        spec(
            "floor_sqrt_exists_unique",
            "forall x. exists s. "
            f"(({unique_result}) /\\ forall t. "
            f"({unique_comparison}) -> t = s)",
            ("floor_sqrt_total", "floor_sqrt_functional"),
            (
                "intro x",
                f"have htotal : exists s. ({total_result})",
                "specialize floor_sqrt_total x",
                "exact floor_sqrt_total",
                "cases htotal",
                "exists x1",
                "split",
                "exact htotal_witness",
                "intro t",
                "intro ht",
                "specialize floor_sqrt_functional x",
                "specialize floor_sqrt_functional t",
                "specialize floor_sqrt_functional x1",
                "apply floor_sqrt_functional",
                "exact ht",
                "exact htotal_witness",
            ),
            "The expanded floor-square graph is total and single-valued.",
        ),
        spec(
            "floor_sqrt_monotone",
            "forall x y s t. "
            f"({monotone_left}) -> ({monotone_right}) -> "
            "(exists k. k + x = y) -> exists k. k + s = t",
            (
                "le_or_lt",
                "mul_le_mul_right",
                "mul_le_mul_left",
                "le_trans",
                "lt_of_lt_of_le",
                "lt_not_le",
            ),
            (
                "intro x",
                "intro y",
                "intro s",
                "intro t",
                "intro hs",
                "intro ht",
                "intro hxy",
                "cases hs",
                "cases ht",
                "specialize le_or_lt s",
                "specialize le_or_lt t",
                "cases le_or_lt",
                "exact le_or_lt_left",
                "exfalso",
                "have hone : exists k. k + S t * S t = s * S t",
                "apply mul_le_mul_right",
                "exact le_or_lt_right",
                "have htwo : exists k. k + s * S t = s * s",
                "apply mul_le_mul_left",
                "exact le_or_lt_right",
                "have hsquare : exists k. k + S t * S t = s * s",
                "specialize le_trans (S t * S t)",
                "specialize le_trans (s * S t)",
                "specialize le_trans (s * s)",
                "apply le_trans",
                "exact hone",
                "exact htwo",
                "have hsy : exists k. k + s * s = y",
                "specialize le_trans (s * s)",
                "specialize le_trans x",
                "specialize le_trans y",
                "apply le_trans",
                "exact hs_left",
                "exact hxy",
                "have hylt : exists k. k + S y = s * s",
                "specialize lt_of_lt_of_le y",
                "specialize lt_of_lt_of_le (S t * S t)",
                "specialize lt_of_lt_of_le (s * s)",
                "apply lt_of_lt_of_le",
                "exact ht_right",
                "exact hsquare",
                "specialize lt_not_le y",
                "specialize lt_not_le (s * s)",
                "apply lt_not_le",
                "exact hylt",
                "exact hsy",
            ),
            "Witness order on inputs is transported monotonically to floor roots.",
        ),
    )


__all__ = ["make_bertrand_floor_sqrt_total_candidate_theorems"]
