"""Native threshold and six-residue base infrastructure for Bertrand B6.

The large-input branch is entered through the relational hypothesis
``64*64 <= 2*n``.  Together with ``FloorSqrt(2*n,s)`` this forces ``64 <= s``
without evaluating ``64*64`` to a giant numeral.  On the six initial roots
``64 <= s <= 69`` we then establish the scalar inequalities behind the two
power envelopes:

* ``42*(s+1) <= s*s`` and hence ``7*(s+1) <= CeilDivSix(s*s)``;
* ``s+1 <= 128`` and ``s+7 <= 128``.  Connecting ``128`` to the relational
  value ``2^7`` is deliberately left to a later, separately checked bridge.

This remains an isolated candidate factory.  All order, ceiling, floor-root,
and power notation is expanded before parsing; no evaluated host power or
square-root computation is proof authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_ceil_sqrt_candidate import (
    ceil_div_six_relation,
    floor_sqrt_relation,
)
from .bertrand_quotient_budget_candidate import witness_le


def make_bertrand_threshold_base_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-closed B6 threshold/base scalar tranche."""

    threshold_floor = floor_sqrt_relation(
        "2 * n", "s", tag="threshold_floor"
    )
    threshold_base_floor = floor_sqrt_relation(
        "64 * 64", "64", tag="threshold_base_floor"
    )
    threshold_input = witness_le(
        "64 * 64", "2 * n", tag="threshold_input"
    )
    threshold_result = witness_le("64", "s", tag="threshold_result")

    scalar_lower = witness_le("64", "s", tag="scalar_lower")
    scalar_result = witness_le(
        "42 * (s + 1)", "s * s", tag="scalar_result"
    )

    ceiling_lower = witness_le("64", "s", tag="ceiling_lower")
    ceiling_graph = ceil_div_six_relation(
        "s * s", "e", tag="ceiling_graph"
    )
    ceiling_result = witness_le(
        "7 * (s + 1)", "e", tag="ceiling_result"
    )

    residue_lower = witness_le("64", "s", tag="residue_lower")
    residue_upper = witness_le("s", "69", tag="residue_upper")
    residue_successor = witness_le("s + 1", "128", tag="residue_successor")
    residue_guard = witness_le("s + 7", "128", tag="residue_guard")
    residue_exponent = witness_le("42", "s + 5", tag="residue_exponent")

    return (
        spec(
            "forty_two_le_sixty_four",
            "exists k. k + 42 = 64",
            ("le_add_right",),
            (
                "have hraw : exists k. k + 42 = 42 + 22",
                "specialize le_add_right 42",
                "specialize le_add_right 22",
                "exact le_add_right",
                "have heq : 42 + 22 = 64",
                *("rewrite PA4",) * 22,
                "rewrite PA3",
                "refl",
                "rewrite heq at hraw",
                "exact hraw",
            ),
            "The small scalar bound 42 <= 64, proved without numeral evaluation.",
        ),
        spec(
            "forty_three_le_sixty_four",
            "exists k. k + 43 = 64",
            ("le_add_right",),
            (
                "have hraw : exists k. k + 43 = 43 + 21",
                "specialize le_add_right 43",
                "specialize le_add_right 21",
                "exact le_add_right",
                "have heq : 43 + 21 = 64",
                *("rewrite PA4",) * 21,
                "rewrite PA3",
                "refl",
                "rewrite heq at hraw",
                "exact hraw",
            ),
            "The neighboring small scalar bound 43 <= 64.",
        ),
        spec(
            "seventy_le_one_twenty_eight",
            "exists k. k + 70 = 128",
            ("le_add_right",),
            (
                "have hraw : exists k. k + 70 = 70 + 58",
                "specialize le_add_right 70",
                "specialize le_add_right 58",
                "exact le_add_right",
                "have heq : 70 + 58 = 128",
                *("rewrite PA4",) * 58,
                "rewrite PA3",
                "refl",
                "rewrite heq at hraw",
                "exact hraw",
            ),
            "The residue-window successor bound 70 <= 128.",
        ),
        spec(
            "seventy_six_le_one_twenty_eight",
            "exists k. k + 76 = 128",
            ("le_add_right",),
            (
                "have hraw : exists k. k + 76 = 76 + 52",
                "specialize le_add_right 76",
                "specialize le_add_right 52",
                "exact le_add_right",
                "have heq : 76 + 52 = 128",
                *("rewrite PA4",) * 52,
                "rewrite PA3",
                "refl",
                "rewrite heq at hraw",
                "exact hraw",
            ),
            "The residue-window guard bound 76 <= 128.",
        ),
        spec(
            "floor_sqrt_threshold_sixty_four",
            "forall n s. "
            f"({threshold_floor}) -> ({threshold_input}) -> "
            f"({threshold_result})",
            ("zero_add", "square_lt_successor_square", "floor_sqrt_monotone"),
            (
                "intro n",
                "intro s",
                "intro hs",
                "intro hthreshold",
                f"have hbase : {threshold_base_floor}",
                "split",
                "exists 0",
                "apply zero_add",
                "specialize square_lt_successor_square 64",
                "exact square_lt_successor_square",
                "specialize floor_sqrt_monotone (64 * 64)",
                "specialize floor_sqrt_monotone (2 * n)",
                "specialize floor_sqrt_monotone 64",
                "specialize floor_sqrt_monotone s",
                "apply floor_sqrt_monotone",
                "exact hbase",
                "exact hs",
                "exact hthreshold",
            ),
            "The relational square-root threshold 64^2 <= 2*n forces 64 <= s.",
        ),
        spec(
            "forty_two_successor_le_square_of_sixty_four_le",
            f"forall s. ({scalar_lower}) -> ({scalar_result})",
            (
                "forty_two_le_sixty_four",
                "forty_three_le_sixty_four",
                "le_trans",
                "add_le_add_left",
                "mul_le_mul_right",
                "mul_succ_left",
            ),
            (
                "intro s",
                "intro hs",
                "have h42s : exists k. k + 42 = s",
                "specialize le_trans 42",
                "specialize le_trans 64",
                "specialize le_trans s",
                "apply le_trans",
                "exact forty_two_le_sixty_four",
                "exact hs",
                "have h43s : exists k. k + 43 = s",
                "specialize le_trans 43",
                "specialize le_trans 64",
                "specialize le_trans s",
                "apply le_trans",
                "exact forty_three_le_sixty_four",
                "exact hs",
                "have hadd : exists k. k + (42 * s + 42) = 42 * s + s",
                "specialize add_le_add_left 42",
                "specialize add_le_add_left s",
                "specialize add_le_add_left (42 * s)",
                "apply add_le_add_left",
                "exact h42s",
                "have hscaled : exists k. k + 43 * s = s * s",
                "specialize mul_le_mul_right 43",
                "specialize mul_le_mul_right s",
                "specialize mul_le_mul_right s",
                "apply mul_le_mul_right",
                "exact h43s",
                "have hfortythree : 43 * s = 42 * s + s",
                "specialize mul_succ_left 42",
                "specialize mul_succ_left s",
                "exact mul_succ_left",
                "rewrite hfortythree at hscaled",
                "have hmiddle : exists k. k + (42 * s + 42) = s * s",
                "specialize le_trans (42 * s + 42)",
                "specialize le_trans (42 * s + s)",
                "specialize le_trans (s * s)",
                "apply le_trans",
                "exact hadd",
                "exact hscaled",
                "have hexpand : 42 * (s + 1) = 42 * s + 42",
                "have hone : s + 1 = S s",
                "trans S (s + 0)",
                "apply PA4",
                "congr",
                "apply PA3",
                "rewrite hone",
                "apply PA6",
                "rewrite hexpand",
                "exact hmiddle",
            ),
            "For every s at least 64, the scalar 42*(s+1) is below s^2.",
        ),
        spec(
            "ceil_square_seven_successor_lower",
            "forall s e. "
            f"({ceiling_lower}) -> ({ceiling_graph}) -> ({ceiling_result})",
            (
                "forty_two_successor_le_square_of_sixty_four_le",
                "le_trans",
                "mul_assoc",
                "succ_ne_zero",
                "mul_le_cancel_left_nonzero",
            ),
            (
                "intro s",
                "intro e",
                "intro hs",
                "intro he",
                "cases he",
                "have hscalar : exists k. k + 42 * (s + 1) = s * s",
                "specialize forty_two_successor_le_square_of_sixty_four_le s",
                "apply forty_two_successor_le_square_of_sixty_four_le",
                "exact hs",
                "have hscaled : exists k. k + 42 * (s + 1) = 6 * e",
                "specialize le_trans (42 * (s + 1))",
                "specialize le_trans (s * s)",
                "specialize le_trans (6 * e)",
                "apply le_trans",
                "exact hscalar",
                "exact he_left",
                "have hfactor : 6 * (7 * (s + 1)) = 42 * (s + 1)",
                "trans (6 * 7) * (s + 1)",
                "symm",
                "apply mul_assoc",
                "congr",
                "norm_num",
                "refl",
                "rewrite <- hfactor at hscaled",
                "have hnonzero : ~(6 = 0)",
                "intro hzero",
                "specialize succ_ne_zero 5",
                "apply succ_ne_zero",
                "exact hzero",
                "specialize mul_le_cancel_left_nonzero 6",
                "specialize mul_le_cancel_left_nonzero (7 * (s + 1))",
                "specialize mul_le_cancel_left_nonzero e",
                "apply mul_le_cancel_left_nonzero",
                "exact hnonzero",
                "exact hscaled",
            ),
            "The ceiling exponent dominates 7*(s+1) once s is at least 64.",
        ),
        spec(
            "bertrand_base_residue_linear_bounds",
            "forall s. "
            f"({residue_lower}) -> ({residue_upper}) -> "
            f"(({residue_successor}) /\\ (({residue_guard}) /\\ "
            f"({residue_exponent})))",
            (
                "add_le_add_right",
                "le_trans",
                "le_add_right",
                "forty_two_le_sixty_four",
                "seventy_le_one_twenty_eight",
                "seventy_six_le_one_twenty_eight",
            ),
            (
                "intro s",
                "intro hlower",
                "intro hupper",
                "have h42s : exists k. k + 42 = s",
                "specialize le_trans 42",
                "specialize le_trans 64",
                "specialize le_trans s",
                "apply le_trans",
                "exact forty_two_le_sixty_four",
                "exact hlower",
                "have hs5 : exists k. k + s = s + 5",
                "specialize le_add_right s",
                "specialize le_add_right 5",
                "exact le_add_right",
                "have h42exp : exists k. k + 42 = s + 5",
                "specialize le_trans 42",
                "specialize le_trans s",
                "specialize le_trans (s + 5)",
                "apply le_trans",
                "exact h42s",
                "exact hs5",
                "have hsucc69 : exists k. k + (s + 1) = 69 + 1",
                "specialize add_le_add_right s",
                "specialize add_le_add_right 69",
                "specialize add_le_add_right 1",
                "apply add_le_add_right",
                "exact hupper",
                "have h6970 : 69 + 1 = 70",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                "rewrite h6970 at hsucc69",
                "have hsucc : exists k. k + (s + 1) = 128",
                "specialize le_trans (s + 1)",
                "specialize le_trans 70",
                "specialize le_trans 128",
                "apply le_trans",
                "exact hsucc69",
                "exact seventy_le_one_twenty_eight",
                "have hguard69 : exists k. k + (s + 7) = 69 + 7",
                "specialize add_le_add_right s",
                "specialize add_le_add_right 69",
                "specialize add_le_add_right 7",
                "apply add_le_add_right",
                "exact hupper",
                "have h6976 : 69 + 7 = 76",
                *("rewrite PA4",) * 7,
                "rewrite PA3",
                "refl",
                "rewrite h6976 at hguard69",
                "have hguard : exists k. k + (s + 7) = 128",
                "specialize le_trans (s + 7)",
                "specialize le_trans 76",
                "specialize le_trans 128",
                "apply le_trans",
                "exact hguard69",
                "exact seventy_six_le_one_twenty_eight",
                "split",
                "exact hsucc",
                "split",
                "exact hguard",
                "exact h42exp",
            ),
            "All six roots 64 through 69 satisfy the uniform linear base bounds.",
        ),
    )


__all__ = ["make_bertrand_threshold_base_candidate_theorems"]
