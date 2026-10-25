"""Constructive signed-conjugate quaternion descent candidates.

All notation expands into unchanged first-order Heyting arithmetic. These
isolated dependency-curried candidates grant no Alpha or Stable authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_two_squares_collision_norm_candidate import _mod, _multiple
from .four_square_descent_candidate import centered_signed_remainder
from .four_square_euler_candidate import _permute_addends, _right_group
from .four_square_identity_candidate import (
    _absolute_expression,
    _conjunction,
    _coordinate_contributions,
)


def _sym(left: str, right: str) -> str:
    return f"(({left}) * ({right}) + ({right}) * ({left}))"


def _sq(value: str) -> str:
    return f"({value}) * ({value})"


def _permutation_commands(source: tuple[str, ...], target: tuple[str, ...]) -> tuple[str, ...]:
    return (
        f"trans {_right_group(source)}",
        "simp [add_assoc]",
        f"trans {_right_group(target)}",
        *_permute_addends(source, target),
        "symm",
        "simp [add_assoc]",
    )


def make_four_square_signed_quaternion_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build sign-independent square congruence and quaternion integrality."""

    centers = tuple(
        centered_signed_remainder("k", value, magnitude, tag=f"fssq_{value}")
        for value, magnitude in zip("abcd", "efgh", strict=True)
    )
    norm_first = "a * a + b * b + c * c + d * d"
    norm_second = "e * e + f * f + g * g + h * h"

    return (
        spec(
            "four_square_signed_lower_remainder_congruent",
            f"forall k a e q. a = k * q + e -> ({_mod('k', 'a', 'e', tag='fssq_lower')})",
            ("zero_add", "add_comm"),
            (
                "intro k",
                "intro a",
                "intro e",
                "intro q",
                "intro hrepresentation",
                "exists 0",
                "exists q",
                "rewrite hrepresentation",
                "simp [zero_add, add_comm]",
            ),
            "A nonnegative signed remainder directly gives balanced modular congruence.",
        ),
        spec(
            "four_square_signed_opposite_remainder_square_congruent",
            f"forall k a e q. a + e = k * q -> "
            f"({_mod('k', 'a * a', 'e * e', tag='fssq_opposite_square')})",
            (
                "multiple_implies_balanced_zero_congruence",
                "balanced_zero_sum_implies_squared_congruence",
            ),
            (
                "intro k",
                "intro a",
                "intro e",
                "intro q",
                "intro hrepresentation",
                f"have hzero : {_mod('k', 'a + e', '0', tag='fssq_opposite_zero')}",
                "specialize multiple_implies_balanced_zero_congruence k",
                "specialize multiple_implies_balanced_zero_congruence (a + e)",
                "apply multiple_implies_balanced_zero_congruence",
                "exists q",
                "exact hrepresentation",
                "specialize balanced_zero_sum_implies_squared_congruence k",
                "specialize balanced_zero_sum_implies_squared_congruence a",
                "specialize balanced_zero_sum_implies_squared_congruence e",
                "apply balanced_zero_sum_implies_squared_congruence",
                "exact hzero",
            ),
            "Oppositely signed modular representatives nevertheless have congruent natural squares.",
        ),
        spec(
            "four_square_signed_centered_square_congruent",
            f"forall k a e. ({centered_signed_remainder('k', 'a', 'e', tag='fssq_center')}) -> "
            f"({_mod('k', 'a * a', 'e * e', tag='fssq_center_square')})",
            (
                "four_square_signed_lower_remainder_congruent",
                "mod_eq_mul",
                "four_square_signed_opposite_remainder_square_congruent",
            ),
            (
                "intro k",
                "intro a",
                "intro e",
                "intro hcenter",
                "cases hcenter",
                "cases hcenter_right",
                "cases hcenter_right_left",
                f"have hmod : {_mod('k', 'a', 'e', tag='fssq_center_lower')}",
                "specialize four_square_signed_lower_remainder_congruent k",
                "specialize four_square_signed_lower_remainder_congruent a",
                "specialize four_square_signed_lower_remainder_congruent e",
                "specialize four_square_signed_lower_remainder_congruent x",
                "apply four_square_signed_lower_remainder_congruent",
                "exact hcenter_right_left_witness",
                "specialize mod_eq_mul k",
                "specialize mod_eq_mul a",
                "specialize mod_eq_mul e",
                "specialize mod_eq_mul a",
                "specialize mod_eq_mul e",
                "apply mod_eq_mul",
                "exact hmod",
                "exact hmod",
                "cases hcenter_right_right",
                "specialize four_square_signed_opposite_remainder_square_congruent k",
                "specialize four_square_signed_opposite_remainder_square_congruent a",
                "specialize four_square_signed_opposite_remainder_square_congruent e",
                "specialize four_square_signed_opposite_remainder_square_congruent x",
                "apply four_square_signed_opposite_remainder_square_congruent",
                "exact hcenter_right_right_witness",
            ),
            "Every centered signed remainder has square congruent to the original coordinate, independently of either sign branch.",
        ),
        spec(
            "four_square_signed_centered_norm_congruent",
            "forall k a b c d e f g h. "
            + " -> ".join(f"({center})" for center in centers)
            + f" -> ({_mod('k', norm_first, norm_second, tag='fssq_norm')})",
            ("four_square_signed_centered_square_congruent", "mod_eq_add"),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro h",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                f"have hfirst : {_mod('k', 'a * a', 'e * e', tag='fssq_first')}",
                "specialize four_square_signed_centered_square_congruent k",
                "specialize four_square_signed_centered_square_congruent a",
                "specialize four_square_signed_centered_square_congruent e",
                "apply four_square_signed_centered_square_congruent",
                "exact ha",
                f"have hsecond : {_mod('k', 'b * b', 'f * f', tag='fssq_second')}",
                "specialize four_square_signed_centered_square_congruent k",
                "specialize four_square_signed_centered_square_congruent b",
                "specialize four_square_signed_centered_square_congruent f",
                "apply four_square_signed_centered_square_congruent",
                "exact hb",
                f"have hthird : {_mod('k', 'c * c', 'g * g', tag='fssq_third')}",
                "specialize four_square_signed_centered_square_congruent k",
                "specialize four_square_signed_centered_square_congruent c",
                "specialize four_square_signed_centered_square_congruent g",
                "apply four_square_signed_centered_square_congruent",
                "exact hc",
                f"have hfourth : {_mod('k', 'd * d', 'h * h', tag='fssq_fourth')}",
                "specialize four_square_signed_centered_square_congruent k",
                "specialize four_square_signed_centered_square_congruent d",
                "specialize four_square_signed_centered_square_congruent h",
                "apply four_square_signed_centered_square_congruent",
                "exact hd",
                f"have hpair : {_mod('k', 'a * a + b * b', 'e * e + f * f', tag='fssq_pair')}",
                "specialize mod_eq_add k",
                "specialize mod_eq_add (a * a)",
                "specialize mod_eq_add (e * e)",
                "specialize mod_eq_add (b * b)",
                "specialize mod_eq_add (f * f)",
                "apply mod_eq_add",
                "exact hfirst",
                "exact hsecond",
                f"have htriple : {_mod('k', 'a * a + b * b + c * c', 'e * e + f * f + g * g', tag='fssq_triple')}",
                "specialize mod_eq_add k",
                "specialize mod_eq_add (a * a + b * b)",
                "specialize mod_eq_add (e * e + f * f)",
                "specialize mod_eq_add (c * c)",
                "specialize mod_eq_add (g * g)",
                "apply mod_eq_add",
                "exact hpair",
                "exact hthird",
                "specialize mod_eq_add k",
                "specialize mod_eq_add (a * a + b * b + c * c)",
                "specialize mod_eq_add (e * e + f * f + g * g)",
                "specialize mod_eq_add (d * d)",
                "specialize mod_eq_add (h * h)",
                "apply mod_eq_add",
                "exact htriple",
                "exact hfourth",
            ),
            "All sixteen independent sign patterns yield the same constructive modular congruence between original and centered four-square norms.",
        ),
        spec(
            "four_square_signed_centered_norm_quotient_exists",
            "forall p k a b c d e f g h. "
            f"p * k = ({norm_first}) -> "
            + " -> ".join(f"({center})" for center in centers)
            + f" -> exists r. k * r = ({norm_second})",
            (
                "four_square_signed_centered_norm_congruent",
                "multiple_implies_balanced_zero_congruence",
                "mod_eq_symm",
                "mod_eq_trans",
                "balanced_zero_congruence_implies_multiple",
                "mul_comm",
            ),
            (
                "intro p",
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro h",
                "intro hnorm",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                f"have hcongruent : {_mod('k', norm_first, norm_second, tag='fssq_quotient_congruence')}",
                "specialize four_square_signed_centered_norm_congruent k",
                "specialize four_square_signed_centered_norm_congruent a",
                "specialize four_square_signed_centered_norm_congruent b",
                "specialize four_square_signed_centered_norm_congruent c",
                "specialize four_square_signed_centered_norm_congruent d",
                "specialize four_square_signed_centered_norm_congruent e",
                "specialize four_square_signed_centered_norm_congruent f",
                "specialize four_square_signed_centered_norm_congruent g",
                "specialize four_square_signed_centered_norm_congruent h",
                "apply four_square_signed_centered_norm_congruent",
                "exact ha",
                "exact hb",
                "exact hc",
                "exact hd",
                f"have hleft_zero : {_mod('k', norm_first, '0', tag='fssq_quotient_left_zero')}",
                "specialize multiple_implies_balanced_zero_congruence k",
                f"specialize multiple_implies_balanced_zero_congruence ({norm_first})",
                "apply multiple_implies_balanced_zero_congruence",
                "exists p",
                "trans p * k",
                "symm",
                "exact hnorm",
                "apply mul_comm",
                f"have hreverse : {_mod('k', norm_second, norm_first, tag='fssq_quotient_reverse')}",
                "specialize mod_eq_symm k",
                f"specialize mod_eq_symm ({norm_first})",
                f"specialize mod_eq_symm ({norm_second})",
                "apply mod_eq_symm",
                "exact hcongruent",
                f"have hzero : {_mod('k', norm_second, '0', tag='fssq_quotient_zero')}",
                "specialize mod_eq_trans k",
                f"specialize mod_eq_trans ({norm_second})",
                f"specialize mod_eq_trans ({norm_first})",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hreverse",
                "exact hleft_zero",
                f"have hmultiple : {_multiple('k', norm_second, tag='fssq_quotient_multiple')}",
                "specialize balanced_zero_congruence_implies_multiple k",
                f"specialize balanced_zero_congruence_implies_multiple ({norm_second})",
                "apply balanced_zero_congruence_implies_multiple",
                "exact hzero",
                "cases hmultiple",
                "exists x",
                "symm",
                "exact hmultiple_witness",
            ),
            "For every one of the sixteen centered sign patterns, a represented prime multiple yields an actual natural quotient of the centered four-square norm.",
        ),
        spec(
            "four_square_signed_absolute_congruence_divisible",
            f"forall k positive negative magnitude. "
            f"({_mod('k', 'positive', 'negative', tag='fssq_absolute_mod')}) -> "
            f"({_absolute_expression('positive', 'negative', 'magnitude')}) -> "
            f"({_multiple('k', 'magnitude', tag='fssq_absolute_multiple')})",
            ("mod_eq_symm", "mod_eq_ordered_gap_multiple", "add_comm"),
            (
                "intro k",
                "intro positive",
                "intro negative",
                "intro magnitude",
                "intro hcongruent",
                "intro habsolute",
                "cases habsolute",
                "specialize mod_eq_ordered_gap_multiple k",
                "specialize mod_eq_ordered_gap_multiple magnitude",
                "specialize mod_eq_ordered_gap_multiple negative",
                "specialize mod_eq_ordered_gap_multiple positive",
                "apply mod_eq_ordered_gap_multiple",
                "trans negative + magnitude",
                "apply add_comm",
                "symm",
                "exact habsolute_left",
                "specialize mod_eq_symm k",
                "specialize mod_eq_symm positive",
                "specialize mod_eq_symm negative",
                "apply mod_eq_symm",
                "exact hcongruent",
                "specialize mod_eq_ordered_gap_multiple k",
                "specialize mod_eq_ordered_gap_multiple magnitude",
                "specialize mod_eq_ordered_gap_multiple positive",
                "specialize mod_eq_ordered_gap_multiple negative",
                "apply mod_eq_ordered_gap_multiple",
                "trans positive + magnitude",
                "apply add_comm",
                "symm",
                "exact habsolute_right",
                "exact hcongruent",
            ),
            "Any natural absolute value of a balanced signed expression congruent to zero has an actual divisibility witness.",
        ),
        spec(
            "four_square_signed_sum_two_decomposition",
            "forall x y. (x + y) * (x + y) = "
            "(x * x + y * y) + (x * y + y * x)",
            (
                "four_square_sum_expansion",
                "add_assoc",
                "add_comm",
                "four_square_add_swap_right_tail",
            ),
            (
                "intro x",
                "intro y",
                "trans (x * x + x * y) + (y * x + y * y)",
                "apply four_square_sum_expansion",
                *_permutation_commands(
                    ("x * x", "x * y", "y * x", "y * y"),
                    ("x * x", "y * y", "x * y", "y * x"),
                ),
            ),
            "The square of two natural addends separates its diagonal squares from its symmetric cross correction.",
        ),
        spec(
            "four_square_signed_sum_four_decomposition",
            "forall x y z w. (x + y + z + w) * (x + y + z + w) = "
            "((x * x + y * y + z * z) + w * w) + "
            "(((x * y + y * x) + (x * z + z * x) + (y * z + z * y)) + "
            "((w * x + x * w) + (w * y + y * w) + (w * z + z * w)))",
            (
                "four_square_signed_sum_two_decomposition",
                "four_square_euler_three_square_expansion",
                "four_square_euler_cross_triple_expansion",
                "add_comm",
                "add_shuffle_middle",
                "add_assoc",
                "four_square_add_swap_right_tail",
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro w",
                "have htwo : ((x + y + z) + w) * ((x + y + z) + w) = "
                "((x + y + z) * (x + y + z) + w * w) + "
                "((x + y + z) * w + w * (x + y + z))",
                "specialize four_square_signed_sum_two_decomposition (x + y + z)",
                "specialize four_square_signed_sum_two_decomposition w",
                "exact four_square_signed_sum_two_decomposition",
                "rewrite htwo",
                "have hthree : (x + y + z) * (x + y + z) = "
                "(x * x + y * y + z * z) + "
                "((x * y + y * x) + (x * z + z * x) + (y * z + z * y))",
                "specialize four_square_euler_three_square_expansion x",
                "specialize four_square_euler_three_square_expansion y",
                "specialize four_square_euler_three_square_expansion z",
                "exact four_square_euler_three_square_expansion",
                "rewrite hthree",
                "have hcross : (x + y + z) * w + w * (x + y + z) = "
                "(w * x + x * w) + (w * y + y * w) + (w * z + z * w)",
                "trans w * (x + y + z) + (x + y + z) * w",
                "apply add_comm",
                "specialize four_square_euler_cross_triple_expansion w",
                "specialize four_square_euler_cross_triple_expansion x",
                "specialize four_square_euler_cross_triple_expansion y",
                "specialize four_square_euler_cross_triple_expansion z",
                "exact four_square_euler_cross_triple_expansion",
                "rewrite hcross",
                *_permutation_commands(
                    (
                        "x * x + y * y + z * z",
                        "(x * y + y * x) + (x * z + z * x) + (y * z + z * y)",
                        "w * w",
                        "(w * x + x * w) + (w * y + y * w) + (w * z + z * w)",
                    ),
                    (
                        "x * x + y * y + z * z",
                        "w * w",
                        "(x * y + y * x) + (x * z + z * x) + (y * z + z * y)",
                        "(w * x + x * w) + (w * y + y * w) + (w * z + z * w)",
                    ),
                ),
            ),
            "A four-addend square splits constructively into four diagonal squares and its six symmetric cross pairs.",
        ),
        spec(
            "four_square_signed_pair_block_decomposition",
            "forall x y z w. (x + y) * (x + y) + (z + w) * (z + w) = "
            "((x * x + y * y) + (z * z + w * w)) + "
            "((x * y + y * x) + (z * w + w * z))",
            (
                "four_square_signed_sum_two_decomposition",
                "add_shuffle_middle",
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro w",
                "have hfirst : (x + y) * (x + y) = "
                "(x * x + y * y) + (x * y + y * x)",
                "specialize four_square_signed_sum_two_decomposition x",
                "specialize four_square_signed_sum_two_decomposition y",
                "exact four_square_signed_sum_two_decomposition",
                "have hsecond : (z + w) * (z + w) = "
                "(z * z + w * w) + (z * w + w * z)",
                "specialize four_square_signed_sum_two_decomposition z",
                "specialize four_square_signed_sum_two_decomposition w",
                "exact four_square_signed_sum_two_decomposition",
                "rewrite hfirst",
                "rewrite hsecond",
                "apply add_shuffle_middle",
            ),
            "A pair-versus-pair signed coordinate square decomposes into four diagonal squares and two symmetric cross pairs.",
        ),
        spec(
            "four_square_signed_pair_cross_decomposition",
            "forall x y z w. (x + y) * (z + w) + (z + w) * (x + y) = "
            "((x * z + z * x) + (x * w + w * x)) + "
            "((y * z + z * y) + (y * w + w * y))",
            (
                "mul_add",
                "add_mul",
                "add_assoc",
                "add_comm",
                "four_square_add_swap_right_tail",
            ),
            (
                "intro x",
                "intro y",
                "intro z",
                "intro w",
                "simp [mul_add, add_mul]",
                *_permutation_commands(
                    (
                        "x * z", "y * z", "x * w", "y * w",
                        "z * x", "w * x", "z * y", "w * y",
                    ),
                    (
                        "x * z", "z * x", "x * w", "w * x",
                        "y * z", "z * y", "y * w", "w * y",
                    ),
                ),
            ),
            "The symmetric cross product of two two-addend blocks decomposes into four independent symmetric coordinate pairs.",
        ),
        spec(
            "four_square_signed_centered_orientation",
            f"forall k a e. ({centered_signed_remainder('k', 'a', 'e', tag='fssq_orientation')}) -> "
            f"(({_mod('k', 'a', 'e', tag='fssq_orientation_positive')}) \\/ "
            f"({_mod('k', 'a + e', '0', tag='fssq_orientation_negative')}))",
            (
                "four_square_signed_lower_remainder_congruent",
                "multiple_implies_balanced_zero_congruence",
            ),
            (
                "intro k",
                "intro a",
                "intro e",
                "intro hcenter",
                "cases hcenter",
                "cases hcenter_right",
                "cases hcenter_right_left",
                "left",
                "specialize four_square_signed_lower_remainder_congruent k",
                "specialize four_square_signed_lower_remainder_congruent a",
                "specialize four_square_signed_lower_remainder_congruent e",
                "specialize four_square_signed_lower_remainder_congruent x",
                "apply four_square_signed_lower_remainder_congruent",
                "exact hcenter_right_left_witness",
                "cases hcenter_right_right",
                "right",
                "specialize multiple_implies_balanced_zero_congruence k",
                "specialize multiple_implies_balanced_zero_congruence (a + e)",
                "apply multiple_implies_balanced_zero_congruence",
                "exists x",
                "exact hcenter_right_right_witness",
            ),
            "Each centered remainder constructively supplies its positive congruence or its opposite signed congruence.",
        ),
        spec(
            "four_square_signed_negative_scale_zero",
            f"forall k a e t. ({_mod('k', 'a + e', '0', tag='fssq_negative_scale_source')}) -> "
            f"({_mod('k', 'a * t + e * t', '0', tag='fssq_negative_scale_result')})",
            ("mod_eq_mul_right", "add_mul", "mul_zero_left"),
            (
                "intro k",
                "intro a",
                "intro e",
                "intro t",
                "intro hsource",
                f"have hscaled : {_mod('k', '(a + e) * t', '0 * t', tag='fssq_negative_scaled')}",
                "specialize mod_eq_mul_right k",
                "specialize mod_eq_mul_right (a + e)",
                "specialize mod_eq_mul_right 0",
                "specialize mod_eq_mul_right t",
                "apply mod_eq_mul_right",
                "exact hsource",
                "have hleft : (a + e) * t = a * t + e * t",
                "apply add_mul",
                "have hright : 0 * t = 0",
                "apply mul_zero_left",
                "rewrite hleft at hscaled",
                "rewrite hright at hscaled",
                "exact hscaled",
            ),
            "Multiplying an opposite signed congruence preserves its subtraction-free zero balance.",
        ),
        spec(
            "four_square_signed_common_zero_cancel",
            f"forall k a b c. ({_mod('k', 'a + c', '0', tag='fssq_common_first')}) -> "
            f"({_mod('k', 'b + c', '0', tag='fssq_common_second')}) -> "
            f"({_mod('k', 'a', 'b', tag='fssq_common_result')})",
            ("mod_eq_symm", "mod_eq_trans", "mod_eq_add_cancel_right"),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro hfirst",
                "intro hsecond",
                f"have hreverse : {_mod('k', '0', 'b + c', tag='fssq_common_reverse')}",
                "specialize mod_eq_symm k",
                "specialize mod_eq_symm (b + c)",
                "specialize mod_eq_symm 0",
                "apply mod_eq_symm",
                "exact hsecond",
                f"have hequal : {_mod('k', 'a + c', 'b + c', tag='fssq_common_equal')}",
                "specialize mod_eq_trans k",
                "specialize mod_eq_trans (a + c)",
                "specialize mod_eq_trans 0",
                "specialize mod_eq_trans (b + c)",
                "apply mod_eq_trans",
                "exact hfirst",
                "exact hreverse",
                "specialize mod_eq_add_cancel_right k",
                "specialize mod_eq_add_cancel_right a",
                "specialize mod_eq_add_cancel_right b",
                "specialize mod_eq_add_cancel_right c",
                "apply mod_eq_add_cancel_right",
                "exact hequal",
            ),
            "Two modular zero balances with the same added natural term yield congruent remaining terms.",
        ),
        spec(
            "four_square_signed_cross_positive",
            f"forall k a b e f. ({_mod('k', 'a', 'e', tag='fssq_cross_positive_a')}) -> "
            f"({_mod('k', 'b', 'f', tag='fssq_cross_positive_b')}) -> "
            f"({_mod('k', 'a * f', 'b * e', tag='fssq_cross_positive_result')})",
            ("mod_eq_mul_right", "mul_comm", "mod_eq_symm", "mod_eq_trans"),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro e",
                "intro f",
                "intro ha",
                "intro hb",
                f"have hfirst : {_mod('k', 'a * f', 'e * f', tag='fssq_cross_positive_first')}",
                "specialize mod_eq_mul_right k",
                "specialize mod_eq_mul_right a",
                "specialize mod_eq_mul_right e",
                "specialize mod_eq_mul_right f",
                "apply mod_eq_mul_right",
                "exact ha",
                f"have hsecond : {_mod('k', 'b * e', 'f * e', tag='fssq_cross_positive_second')}",
                "specialize mod_eq_mul_right k",
                "specialize mod_eq_mul_right b",
                "specialize mod_eq_mul_right f",
                "specialize mod_eq_mul_right e",
                "apply mod_eq_mul_right",
                "exact hb",
                "have hswap : f * e = e * f",
                "apply mul_comm",
                "rewrite hswap at hsecond",
                f"have hreverse : {_mod('k', 'e * f', 'b * e', tag='fssq_cross_positive_reverse')}",
                "specialize mod_eq_symm k",
                "specialize mod_eq_symm (b * e)",
                "specialize mod_eq_symm (e * f)",
                "apply mod_eq_symm",
                "exact hsecond",
                "specialize mod_eq_trans k",
                "specialize mod_eq_trans (a * f)",
                "specialize mod_eq_trans (e * f)",
                "specialize mod_eq_trans (b * e)",
                "apply mod_eq_trans",
                "exact hfirst",
                "exact hreverse",
            ),
            "Two positive signed coordinate orientations have congruent crossed bilinear products.",
        ),
        spec(
            "four_square_signed_cross_negative",
            f"forall k a b e f. ({_mod('k', 'a + e', '0', tag='fssq_cross_negative_a')}) -> "
            f"({_mod('k', 'b + f', '0', tag='fssq_cross_negative_b')}) -> "
            f"({_mod('k', 'a * f', 'b * e', tag='fssq_cross_negative_result')})",
            (
                "four_square_signed_negative_scale_zero",
                "mul_comm",
                "four_square_signed_common_zero_cancel",
            ),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro e",
                "intro f",
                "intro ha",
                "intro hb",
                f"have hfirst : {_mod('k', 'a * f + e * f', '0', tag='fssq_cross_negative_first')}",
                "specialize four_square_signed_negative_scale_zero k",
                "specialize four_square_signed_negative_scale_zero a",
                "specialize four_square_signed_negative_scale_zero e",
                "specialize four_square_signed_negative_scale_zero f",
                "apply four_square_signed_negative_scale_zero",
                "exact ha",
                f"have hsecond : {_mod('k', 'b * e + f * e', '0', tag='fssq_cross_negative_second')}",
                "specialize four_square_signed_negative_scale_zero k",
                "specialize four_square_signed_negative_scale_zero b",
                "specialize four_square_signed_negative_scale_zero f",
                "specialize four_square_signed_negative_scale_zero e",
                "apply four_square_signed_negative_scale_zero",
                "exact hb",
                "have hswap : f * e = e * f",
                "apply mul_comm",
                "rewrite hswap at hsecond",
                "specialize four_square_signed_common_zero_cancel k",
                "specialize four_square_signed_common_zero_cancel (a * f)",
                "specialize four_square_signed_common_zero_cancel (b * e)",
                "specialize four_square_signed_common_zero_cancel (e * f)",
                "apply four_square_signed_common_zero_cancel",
                "exact hfirst",
                "exact hsecond",
            ),
            "Two negative signed coordinate orientations also have congruent crossed bilinear products.",
        ),
        spec(
            "four_square_signed_cross_mixed_zero",
            f"forall k a b e f. ({_mod('k', 'a', 'e', tag='fssq_cross_mixed_a')}) -> "
            f"({_mod('k', 'b + f', '0', tag='fssq_cross_mixed_b')}) -> "
            f"({_mod('k', 'a * f + b * e', '0', tag='fssq_cross_mixed_result')})",
            (
                "mod_eq_mul_right",
                "four_square_signed_negative_scale_zero",
                "mul_comm",
                "add_comm",
                "mod_eq_refl",
                "mod_eq_add",
                "mod_eq_trans",
            ),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro e",
                "intro f",
                "intro ha",
                "intro hb",
                f"have hfirst : {_mod('k', 'a * f', 'e * f', tag='fssq_cross_mixed_first')}",
                "specialize mod_eq_mul_right k",
                "specialize mod_eq_mul_right a",
                "specialize mod_eq_mul_right e",
                "specialize mod_eq_mul_right f",
                "apply mod_eq_mul_right",
                "exact ha",
                f"have hsecond : {_mod('k', 'b * e + f * e', '0', tag='fssq_cross_mixed_second')}",
                "specialize four_square_signed_negative_scale_zero k",
                "specialize four_square_signed_negative_scale_zero b",
                "specialize four_square_signed_negative_scale_zero f",
                "specialize four_square_signed_negative_scale_zero e",
                "apply four_square_signed_negative_scale_zero",
                "exact hb",
                "have hswap_factor : f * e = e * f",
                "apply mul_comm",
                "rewrite hswap_factor at hsecond",
                "have hswap_sum : b * e + e * f = e * f + b * e",
                "apply add_comm",
                "rewrite hswap_sum at hsecond",
                f"have hleft : {_mod('k', 'a * f + b * e', 'e * f + b * e', tag='fssq_cross_mixed_sum')}",
                "specialize mod_eq_add k",
                "specialize mod_eq_add (a * f)",
                "specialize mod_eq_add (e * f)",
                "specialize mod_eq_add (b * e)",
                "specialize mod_eq_add (b * e)",
                "apply mod_eq_add",
                "exact hfirst",
                "specialize mod_eq_refl k",
                "specialize mod_eq_refl (b * e)",
                "exact mod_eq_refl",
                "specialize mod_eq_trans k",
                "specialize mod_eq_trans (a * f + b * e)",
                "specialize mod_eq_trans (e * f + b * e)",
                "specialize mod_eq_trans 0",
                "apply mod_eq_trans",
                "exact hleft",
                "exact hsecond",
            ),
            "Opposite signed coordinate orientations make the sum of their crossed bilinear products vanish modulo the multiplier.",
        ),
        spec(
            "four_square_signed_mod_zero_add",
            f"forall k a b. ({_mod('k', 'a', '0', tag='fssq_zero_add_left')}) -> "
            f"({_mod('k', 'b', '0', tag='fssq_zero_add_right')}) -> "
            f"({_mod('k', 'a + b', '0', tag='fssq_zero_add_result')})",
            ("mod_eq_add", "zero_add"),
            (
                "intro k", "intro a", "intro b", "intro ha", "intro hb",
                f"have hsum : {_mod('k', 'a + b', '0 + 0', tag='fssq_zero_add_sum')}",
                "specialize mod_eq_add k", "specialize mod_eq_add a",
                "specialize mod_eq_add 0", "specialize mod_eq_add b",
                "specialize mod_eq_add 0", "apply mod_eq_add", "exact ha", "exact hb",
                "have hzero : 0 + 0 = 0", "apply zero_add",
                "rewrite hzero at hsum", "exact hsum",
            ),
            "Two independently vanishing signed blocks have vanishing sum modulo the multiplier.",
        ),
        spec(
            "four_square_signed_mod_zero_equivalent",
            f"forall k a b. ({_mod('k', 'a', '0', tag='fssq_zero_equiv_left')}) -> "
            f"({_mod('k', 'b', '0', tag='fssq_zero_equiv_right')}) -> "
            f"({_mod('k', 'a', 'b', tag='fssq_zero_equiv_result')})",
            ("mod_eq_symm", "mod_eq_trans"),
            (
                "intro k", "intro a", "intro b", "intro ha", "intro hb",
                f"have hreverse : {_mod('k', '0', 'b', tag='fssq_zero_equiv_reverse')}",
                "specialize mod_eq_symm k", "specialize mod_eq_symm b",
                "specialize mod_eq_symm 0", "apply mod_eq_symm", "exact hb",
                "specialize mod_eq_trans k", "specialize mod_eq_trans a",
                "specialize mod_eq_trans 0", "specialize mod_eq_trans b",
                "apply mod_eq_trans", "exact ha", "exact hreverse",
            ),
            "Any two natural signed blocks that both vanish modulo the multiplier are congruent.",
        ),
        spec(
            "four_square_signed_mod_zero_swap",
            f"forall k a b. ({_mod('k', 'a + b', '0', tag='fssq_zero_swap_source')}) -> "
            f"({_mod('k', 'b + a', '0', tag='fssq_zero_swap_result')})",
            ("add_comm",),
            (
                "intro k", "intro a", "intro b", "intro hsum",
                "have hswap : a + b = b + a", "apply add_comm",
                "rewrite hswap at hsum", "exact hsum",
            ),
            "Swapping the two summands of a modular zero balance preserves that balance.",
        ),
        spec(
            "four_square_signed_zero_cancel_right",
            f"forall k a b. ({_mod('k', 'a + b', '0', tag='fssq_zero_cancel_sum')}) -> "
            f"({_mod('k', 'b', '0', tag='fssq_zero_cancel_tail')}) -> "
            f"({_mod('k', 'a', '0', tag='fssq_zero_cancel_result')})",
            ("zero_add", "four_square_signed_common_zero_cancel"),
            (
                "intro k", "intro a", "intro b", "intro hsum", "intro htail",
                f"have hpadded : {_mod('k', '0 + b', '0', tag='fssq_zero_cancel_padded')}",
                "have hpad : 0 + b = b", "apply zero_add",
                "rewrite hpad", "exact htail",
                "specialize four_square_signed_common_zero_cancel k",
                "specialize four_square_signed_common_zero_cancel a",
                "specialize four_square_signed_common_zero_cancel 0",
                "specialize four_square_signed_common_zero_cancel b",
                "apply four_square_signed_common_zero_cancel",
                "exact hsum", "exact hpadded",
            ),
            "Cancel a separately vanishing natural tail from a subtraction-free modular zero balance.",
        ),
        spec(
            "four_square_signed_cross_mixed_zero_reversed",
            f"forall k a b e f. ({_mod('k', 'a + e', '0', tag='fssq_cross_reverse_a')}) -> "
            f"({_mod('k', 'b', 'f', tag='fssq_cross_reverse_b')}) -> "
            f"({_mod('k', 'a * f + b * e', '0', tag='fssq_cross_reverse_result')})",
            ("four_square_signed_cross_mixed_zero", "four_square_signed_mod_zero_swap"),
            (
                "intro k", "intro a", "intro b", "intro e", "intro f",
                "intro ha", "intro hb",
                f"have hreverse : {_mod('k', 'b * e + a * f', '0', tag='fssq_cross_reverse_order')}",
                "specialize four_square_signed_cross_mixed_zero k",
                "specialize four_square_signed_cross_mixed_zero b",
                "specialize four_square_signed_cross_mixed_zero a",
                "specialize four_square_signed_cross_mixed_zero f",
                "specialize four_square_signed_cross_mixed_zero e",
                "apply four_square_signed_cross_mixed_zero", "exact hb", "exact ha",
                "specialize four_square_signed_mod_zero_swap k",
                "specialize four_square_signed_mod_zero_swap (b * e)",
                "specialize four_square_signed_mod_zero_swap (a * f)",
                "apply four_square_signed_mod_zero_swap", "exact hreverse",
            ),
            "The negative-positive orientation also makes the crossed bilinear sum vanish.",
        ),
        spec(
            "four_square_signed_dot_positive",
            f"forall k a e. ({_mod('k', 'a', 'e', tag='fssq_dot_positive_source')}) -> "
            f"({_mod('k', 'a * e', 'e * e', tag='fssq_dot_positive_result')})",
            ("mod_eq_mul_right",),
            (
                "intro k", "intro a", "intro e", "intro ha",
                "specialize mod_eq_mul_right k", "specialize mod_eq_mul_right a",
                "specialize mod_eq_mul_right e", "specialize mod_eq_mul_right e",
                "apply mod_eq_mul_right", "exact ha",
            ),
            "A positively oriented coordinate contributes its centered square modulo the multiplier.",
        ),
        spec(
            "four_square_signed_dot_negative_zero",
            f"forall k a e. ({_mod('k', 'a + e', '0', tag='fssq_dot_negative_source')}) -> "
            f"({_mod('k', 'a * e + e * e', '0', tag='fssq_dot_negative_result')})",
            ("four_square_signed_negative_scale_zero",),
            (
                "intro k", "intro a", "intro e", "intro ha",
                "specialize four_square_signed_negative_scale_zero k",
                "specialize four_square_signed_negative_scale_zero a",
                "specialize four_square_signed_negative_scale_zero e",
                "specialize four_square_signed_negative_scale_zero e",
                "apply four_square_signed_negative_scale_zero", "exact ha",
            ),
            "A negatively oriented dot-product contribution and its centered square cancel modulo the multiplier.",
        ),
        spec(
            "four_square_signed_mod_zero_plus_congruent",
            f"forall k a b c. ({_mod('k', 'a', '0', tag='fssq_zero_plus_first')}) -> "
            f"({_mod('k', 'b', 'c', tag='fssq_zero_plus_second')}) -> "
            f"({_mod('k', 'a + b', 'c', tag='fssq_zero_plus_result')})",
            ("mod_eq_add", "zero_add"),
            (
                "intro k", "intro a", "intro b", "intro c", "intro ha", "intro hb",
                f"have hsum : {_mod('k', 'a + b', '0 + c', tag='fssq_zero_plus_sum')}",
                "specialize mod_eq_add k", "specialize mod_eq_add a",
                "specialize mod_eq_add 0", "specialize mod_eq_add b",
                "specialize mod_eq_add c", "apply mod_eq_add", "exact ha", "exact hb",
                "have hzero : 0 + c = c", "apply zero_add",
                "rewrite hzero at hsum", "exact hsum",
            ),
            "A vanishing natural block can be prepended to any modular congruence.",
        ),
        spec(
            "four_square_signed_partition_balance",
            f"forall k p s n t. ({_mod('k', 'p', 's', tag='fssq_partition_positive')}) -> "
            f"({_mod('k', 'n + t', '0', tag='fssq_partition_negative')}) -> "
            f"({_mod('k', 's + t', '0', tag='fssq_partition_norm')}) -> "
            f"({_mod('k', 'p', 'n', tag='fssq_partition_result')})",
            (
                "mod_eq_refl", "mod_eq_add", "mod_eq_trans",
                "four_square_signed_common_zero_cancel",
            ),
            (
                "intro k", "intro p", "intro s", "intro n", "intro t",
                "intro hpositive", "intro hnegative", "intro hnorm",
                f"have hpadded : {_mod('k', 'p + t', 's + t', tag='fssq_partition_padded')}",
                "specialize mod_eq_add k", "specialize mod_eq_add p",
                "specialize mod_eq_add s", "specialize mod_eq_add t",
                "specialize mod_eq_add t", "apply mod_eq_add", "exact hpositive",
                "specialize mod_eq_refl k", "specialize mod_eq_refl t", "exact mod_eq_refl",
                f"have hzero : {_mod('k', 'p + t', '0', tag='fssq_partition_zero')}",
                "specialize mod_eq_trans k", "specialize mod_eq_trans (p + t)",
                "specialize mod_eq_trans (s + t)", "specialize mod_eq_trans 0",
                "apply mod_eq_trans", "exact hpadded", "exact hnorm",
                "specialize four_square_signed_common_zero_cancel k",
                "specialize four_square_signed_common_zero_cancel p",
                "specialize four_square_signed_common_zero_cancel n",
                "specialize four_square_signed_common_zero_cancel t",
                "apply four_square_signed_common_zero_cancel", "exact hzero", "exact hnegative",
            ),
            "Positive and negative signed dot-product groups balance when their combined centered square norm vanishes.",
        ),
        *_canonical_orientation_surface_specs(spec),
    )


def _canonical_orientation_surface_specs(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return bounded canonical sign-pattern balance certificates."""

    originals = ("a", "b", "c", "d")
    centered = ("e", "f", "g", "h")
    dots = tuple(f"{left} * {right}" for left, right in zip(originals, centered, strict=True))
    squares = tuple(f"{value} * {value}" for value in centered)
    norm = " + ".join(squares)
    conjugate = (
        ("a * e + b * f + c * g + d * h", "0"),
        ("a * f + c * h", "b * e + d * g"),
        ("a * g + d * f", "c * e + b * h"),
        ("a * h + b * g", "d * e + c * f"),
    )
    mixed_conjugate = (
        ("a * h + b * g + c * f + d * e", "0"),
        ("a * g + c * e", "b * h + d * f"),
        ("a * f + d * g", "c * h + b * e"),
        ("a * e + b * f", "d * h + c * g"),
    )
    configurations = (
        (
            "four_square_signed_conjugate_positive_blocks",
            (False, False, False, False),
            conjugate,
            "positive",
        ),
        (
            "four_square_signed_conjugate_mixed_blocks",
            (True, True, False, False),
            mixed_conjugate,
            "mixed",
        ),
        (
            "four_square_signed_natural_negative_first_blocks",
            (True, False, False, False),
            _coordinate_contributions(),
            "natural",
        ),
    )

    def add_congruence(
        commands: list[str],
        name: str,
        left_a: str,
        right_a: str,
        left_b: str,
        right_b: str,
        first: str,
        second: str,
    ) -> None:
        commands.extend(
            (
                f"have {name} : {_mod('k', f'({left_a}) + ({left_b})', f'({right_a}) + ({right_b})', tag=f'fssq_surface_{name}')}",
                "specialize mod_eq_add k",
                f"specialize mod_eq_add ({left_a})",
                f"specialize mod_eq_add ({right_a})",
                f"specialize mod_eq_add ({left_b})",
                f"specialize mod_eq_add ({right_b})",
                "apply mod_eq_add",
                f"exact {first}",
                f"exact {second}",
            )
        )

    def zero_add(
        commands: list[str],
        name: str,
        left: str,
        right: str,
        first: str,
        second: str,
    ) -> None:
        commands.extend(
            (
                f"have {name} : {_mod('k', f'({left}) + ({right})', '0', tag=f'fssq_surface_{name}')}",
                "specialize four_square_signed_mod_zero_add k",
                f"specialize four_square_signed_mod_zero_add ({left})",
                f"specialize four_square_signed_mod_zero_add ({right})",
                "apply four_square_signed_mod_zero_add",
                f"exact {first}",
                f"exact {second}",
            )
        )

    def reverse(
        commands: list[str], name: str, left: str, right: str, source: str
    ) -> None:
        commands.extend(
            (
                f"have {name} : {_mod('k', right, left, tag=f'fssq_surface_{name}')}",
                "specialize mod_eq_symm k",
                f"specialize mod_eq_symm ({left})",
                f"specialize mod_eq_symm ({right})",
                "apply mod_eq_symm",
                f"exact {source}",
            )
        )

    rows: list[Any] = []
    for theorem_name, signs, blocks, family in configurations:
        orientations = tuple(
            _mod(
                "k",
                f"{left} + {right}" if negative else left,
                "0" if negative else right,
                tag=f"fssq_surface_{theorem_name}_{index}",
            )
            for index, (left, right, negative) in enumerate(
                zip(originals, centered, signs, strict=True)
            )
        )
        balances = tuple(
            _mod("k", left, right, tag=f"fssq_surface_{theorem_name}_block_{index}")
            for index, (left, right) in enumerate(blocks)
        )
        statement = (
            "forall k a b c d e f g h. "
            f"({_mod('k', norm, '0', tag=f'fssq_surface_{theorem_name}_norm')}) -> "
            + " -> ".join(f"({orientation})" for orientation in orientations)
            + f" -> ({_conjunction(balances)})"
        )
        commands = [
            "intro k", "intro a", "intro b", "intro c", "intro d",
            "intro e", "intro f", "intro g", "intro h", "intro hnorm",
            "intro horient0", "intro horient1", "intro horient2", "intro horient3",
        ]

        for first in range(4):
            for second in range(first + 1, 4):
                left = f"{originals[first]} * {centered[second]}"
                right = f"{originals[second]} * {centered[first]}"
                same = signs[first] == signs[second]
                result = _mod(
                    "k", left if same else f"{left} + {right}",
                    right if same else "0", tag=f"fssq_surface_pair_{first}{second}",
                )
                if same:
                    dependency = (
                        "four_square_signed_cross_negative" if signs[first]
                        else "four_square_signed_cross_positive"
                    )
                else:
                    dependency = (
                        "four_square_signed_cross_mixed_zero_reversed" if signs[first]
                        else "four_square_signed_cross_mixed_zero"
                    )
                commands.append(f"have hpair{first}{second} : {result}")
                commands.extend(
                    (
                        f"specialize {dependency} k",
                        f"specialize {dependency} {originals[first]}",
                        f"specialize {dependency} {originals[second]}",
                        f"specialize {dependency} {centered[first]}",
                        f"specialize {dependency} {centered[second]}",
                        f"apply {dependency}",
                        f"exact horient{first}",
                        f"exact horient{second}",
                    )
                )

        positive_indices = tuple(index for index in range(4) if not signs[index])
        negative_indices = tuple(index for index in range(4) if signs[index])

        def positive_aggregate(indices: tuple[int, ...]) -> tuple[str, str, str]:
            for index in indices:
                commands.extend(
                    (
                        f"have hdot{index} : {_mod('k', dots[index], squares[index], tag=f'fssq_surface_dot_{index}')}",
                        "specialize four_square_signed_dot_positive k",
                        f"specialize four_square_signed_dot_positive {originals[index]}",
                        f"specialize four_square_signed_dot_positive {centered[index]}",
                        "apply four_square_signed_dot_positive",
                        f"exact horient{index}",
                    )
                )
            left = dots[indices[0]]
            right = squares[indices[0]]
            proof = f"hdot{indices[0]}"
            for index in indices[1:]:
                next_name = f"hpositive{index}"
                add_congruence(
                    commands, next_name, left, right, dots[index], squares[index],
                    proof, f"hdot{index}",
                )
                left = f"({left}) + ({dots[index]})"
                right = f"({right}) + ({squares[index]})"
                proof = next_name
            return left, right, proof

        def negative_aggregate(indices: tuple[int, ...]) -> tuple[str, str, str]:
            for index in indices:
                commands.extend(
                    (
                        f"have hdot{index} : {_mod('k', f'{dots[index]} + {squares[index]}', '0', tag=f'fssq_surface_dot_{index}')}",
                        "specialize four_square_signed_dot_negative_zero k",
                        f"specialize four_square_signed_dot_negative_zero {originals[index]}",
                        f"specialize four_square_signed_dot_negative_zero {centered[index]}",
                        "apply four_square_signed_dot_negative_zero",
                        f"exact horient{index}",
                    )
                )
            combined = f"({dots[indices[0]]}) + ({squares[indices[0]]})"
            proof = f"hdot{indices[0]}"
            for index in indices[1:]:
                pair = f"({dots[index]}) + ({squares[index]})"
                next_name = f"hnegative{index}"
                zero_add(commands, next_name, combined, pair, proof, f"hdot{index}")
                combined = f"({combined}) + ({pair})"
                proof = next_name
            grouped_dots = " + ".join(dots[index] for index in indices)
            grouped_squares = " + ".join(squares[index] for index in indices)
            target = f"({grouped_dots}) + ({grouped_squares})"
            if len(indices) > 1:
                source_atoms = tuple(
                    atom for index in indices for atom in (dots[index], squares[index])
                )
                target_atoms = tuple(dots[index] for index in indices) + tuple(
                    squares[index] for index in indices
                )
                commands.append(f"have hnegative_shuffle : ({combined}) = ({target})")
                commands.extend(_permutation_commands(source_atoms, target_atoms))
                commands.append(f"rewrite hnegative_shuffle at {proof}")
            return grouped_dots, grouped_squares, proof

        pos_dots, pos_squares, pos_proof = positive_aggregate(positive_indices)
        if negative_indices:
            neg_dots, neg_squares, neg_proof = negative_aggregate(negative_indices)
            norm_order = f"({pos_squares}) + ({neg_squares})"
            commands.append(f"have hnorm_shuffle : ({norm_order}) = ({norm})")
            commands.extend(
                _permutation_commands(
                    tuple(squares[index] for index in positive_indices)
                    + tuple(squares[index] for index in negative_indices),
                    squares,
                )
            )
            commands.extend(
                (
                    f"have hordered_norm : {_mod('k', norm_order, '0', tag='fssq_surface_ordered_norm')}",
                    "rewrite hnorm_shuffle",
                    "exact hnorm",
                    f"have hpartition : {_mod('k', pos_dots, neg_dots, tag='fssq_surface_partition')}",
                    "specialize four_square_signed_partition_balance k",
                    f"specialize four_square_signed_partition_balance ({pos_dots})",
                    f"specialize four_square_signed_partition_balance ({pos_squares})",
                    f"specialize four_square_signed_partition_balance ({neg_dots})",
                    f"specialize four_square_signed_partition_balance ({neg_squares})",
                    "apply four_square_signed_partition_balance",
                    f"exact {pos_proof}",
                    f"exact {neg_proof}",
                    "exact hordered_norm",
                )
            )

        if family == "positive":
            commands.extend(
                (
                    f"have hblock0 : {balances[0]}",
                    "specialize mod_eq_trans k",
                    f"specialize mod_eq_trans ({blocks[0][0]})",
                    f"specialize mod_eq_trans ({norm})",
                    "specialize mod_eq_trans 0",
                    "apply mod_eq_trans",
                    f"exact {pos_proof}",
                    "exact hnorm",
                )
            )
            add_congruence(
                commands, "hblock1", "a * f", "b * e", "c * h", "d * g",
                "hpair01", "hpair23",
            )
            reverse(commands, "hpair13_reverse", "b * h", "d * f", "hpair13")
            add_congruence(
                commands, "hblock2", "a * g", "c * e", "d * f", "b * h",
                "hpair02", "hpair13_reverse",
            )
            add_congruence(
                commands, "hblock3", "a * h", "d * e", "b * g", "c * f",
                "hpair03", "hpair12",
            )
        elif family == "natural":
            reverse(commands, "hblock0", pos_dots, neg_dots, "hpartition")
            for block, pair, same_left, same_right, same_proof in (
                (1, "a * f + b * e", "c * h", "d * g", "hpair23"),
                (2, "a * g + c * e", "d * f", "b * h", "hpair13_reverse"),
            ):
                if block == 2:
                    reverse(commands, "hpair13_reverse", "b * h", "d * f", "hpair13")
                commands.extend(
                    (
                        f"have hblock{block} : {balances[block]}",
                        "specialize four_square_signed_mod_zero_plus_congruent k",
                        f"specialize four_square_signed_mod_zero_plus_congruent ({pair})",
                        f"specialize four_square_signed_mod_zero_plus_congruent ({same_left})",
                        f"specialize four_square_signed_mod_zero_plus_congruent ({same_right})",
                        "apply four_square_signed_mod_zero_plus_congruent",
                        f"exact hpair0{block}",
                        f"exact {same_proof}",
                    )
                )
            commands.extend(
                (
                    f"have hblock3_reordered : {_mod('k', '(a * h + d * e) + b * g', 'c * f', tag='fssq_surface_natural_reordered')}",
                    "specialize four_square_signed_mod_zero_plus_congruent k",
                    "specialize four_square_signed_mod_zero_plus_congruent (a * h + d * e)",
                    "specialize four_square_signed_mod_zero_plus_congruent (b * g)",
                    "specialize four_square_signed_mod_zero_plus_congruent (c * f)",
                    "apply four_square_signed_mod_zero_plus_congruent",
                    "exact hpair03", "exact hpair12",
                    "have hblock3_shuffle : (a * h + d * e) + b * g = a * h + b * g + d * e",
                    *_permutation_commands(
                        ("a * h", "d * e", "b * g"),
                        ("a * h", "b * g", "d * e"),
                    ),
                    "rewrite hblock3_shuffle at hblock3_reordered",
                    f"have hblock3 : {balances[3]}",
                    "exact hblock3_reordered",
                )
            )
        else:
            zero_add(
                commands, "hblock0_reordered", "a * h + d * e", "b * g + c * f",
                "hpair03", "hpair12",
            )
            commands.extend(
                (
                    "have hblock0_shuffle : (a * h + d * e) + (b * g + c * f) = a * h + b * g + c * f + d * e",
                    *_permutation_commands(
                        ("a * h", "d * e", "b * g", "c * f"),
                        ("a * h", "b * g", "c * f", "d * e"),
                    ),
                    "rewrite hblock0_shuffle at hblock0_reordered",
                    f"have hblock0 : {balances[0]}",
                    "exact hblock0_reordered",
                    f"have hblock1 : {balances[1]}",
                    "specialize four_square_signed_mod_zero_equivalent k",
                    "specialize four_square_signed_mod_zero_equivalent (a * g + c * e)",
                    "specialize four_square_signed_mod_zero_equivalent (b * h + d * f)",
                    "apply four_square_signed_mod_zero_equivalent",
                    "exact hpair02", "exact hpair13",
                )
            )
            reverse(commands, "hpair23_reverse", "c * h", "d * g", "hpair23")
            add_congruence(
                commands, "hblock2_reordered", "a * f", "b * e", "d * g", "c * h",
                "hpair01", "hpair23_reverse",
            )
            commands.extend(
                (
                    "have hblock2_swap : b * e + c * h = c * h + b * e",
                    "apply add_comm",
                    "rewrite hblock2_swap at hblock2_reordered",
                    f"have hblock2 : {balances[2]}",
                    "exact hblock2_reordered",
                )
            )
            reverse(commands, "hblock3_reordered", pos_dots, neg_dots, "hpartition")
            commands.extend(
                (
                    "have hblock3_swap : c * g + d * h = d * h + c * g",
                    "apply add_comm",
                    "rewrite hblock3_swap at hblock3_reordered",
                    f"have hblock3 : {balances[3]}",
                    "exact hblock3_reordered",
                )
            )

        commands.extend(
            (
                "split", "exact hblock0", "split", "exact hblock1",
                "split", "exact hblock2", "exact hblock3",
            )
        )
        rows.append(
            spec(
                theorem_name,
                statement,
                (
                    "four_square_signed_cross_positive",
                    "four_square_signed_cross_negative",
                    "four_square_signed_cross_mixed_zero",
                    "four_square_signed_cross_mixed_zero_reversed",
                    "four_square_signed_dot_positive",
                    "four_square_signed_dot_negative_zero",
                    "four_square_signed_mod_zero_add",
                    "four_square_signed_mod_zero_equivalent",
                    "four_square_signed_mod_zero_plus_congruent",
                    "four_square_signed_partition_balance",
                    "mod_eq_add", "mod_eq_symm", "mod_eq_trans",
                    "add_assoc", "add_comm", "four_square_add_swap_right_tail",
                ),
                tuple(commands),
                "All four canonical signed quaternion blocks balance constructively modulo the multiplier under this exact orientation pattern.",
            )
        )

    return tuple(rows)


__all__ = ["make_four_square_signed_quaternion_candidate_theorems"]
