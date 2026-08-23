"""Constructive cross-collisions between two bounded injective beta prefixes."""

from __future__ import annotations

from typing import Any, Callable

from .fermat_two_squares_pigeonhole_candidate import _collision
from .finite_fold_surface import _beta_at_term
from .finite_permutation_theorems import injective_prefix


FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED = (
    "four_square_cross_covered_prefix_bounded"
)
FOUR_SQUARE_CROSS_PIGEONHOLE = "four_square_cross_pigeonhole"
FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS = (
    "four_square_cross_interleaved_prefix_exists"
)
FOUR_SQUARE_CROSS_INTERSECTION = "four_square_cross_intersection"


def _lt(left: str, right: str, *, tag: str) -> str:
    return f"exists fscp_gap_{tag}. fscp_gap_{tag} + S ({left}) = ({right})"


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    return _beta_at_term(
        code,
        scale,
        index,
        value,
        tag=f"fscp_{tag}",
        avoid=(
            "b", "c", "d", "e", "z", "t", "l", "p", "i", "j", "v", "u",
            "a", "x", "x1", "x2", "x3", "x4", "x5", "x6", "x7",
        ),
    )


def _bounded(code: str, scale: str, length: str, bound: str, *, tag: str) -> str:
    index = f"fscp_index_{tag}"
    value = f"fscp_value_{tag}"
    return (
        f"forall {index}. ({_lt(index, length, tag=f'{tag}_index')}) -> "
        f"exists {value}. (({_at(code, scale, index, value, tag=f'{tag}_entry')}) /\\ "
        f"({_lt(value, bound, tag=f'{tag}_value')}))"
    )


def _coverage(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    merged_code: str,
    merged_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    index = f"fscp_index_{tag}"
    value = f"fscp_value_{tag}"
    source = _at(merged_code, merged_scale, index, value, tag=f"{tag}_source")
    return (
        f"forall {index} {value}. ({_lt(index, f'{length} + {length}', tag=f'{tag}_index')}) "
        f"-> ({source}) -> "
        f"({_coverage_case(left_code, left_scale, right_code, right_scale, index, value, length, tag=tag)})"
    )


def _coverage_case(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    index: str,
    value: str,
    length: str,
    *,
    tag: str,
) -> str:
    left = f"fscp_left_{tag}"
    right = f"fscp_right_{tag}"
    first = _at(left_code, left_scale, left, value, tag=f"{tag}_left")
    second = _at(right_code, right_scale, right, value, tag=f"{tag}_right")
    left_case = (
        f"exists {left}. (({_lt(left, length, tag=f'{tag}_left_bound')}) /\\ "
        f"(({first}) /\\ {index} = {left} + {left}))"
    )
    right_case = (
        f"exists {right}. (({_lt(right, length, tag=f'{tag}_right_bound')}) /\\ "
        f"(({second}) /\\ {index} = S ({right} + {right})))"
    )
    return f"(({left_case}) \\/ ({right_case}))"


def _cross(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    first = f"fscp_left_{tag}"
    second = f"fscp_right_{tag}"
    value = f"fscp_value_{tag}"
    return (
        f"exists {first} {second} {value}. "
        f"(({_lt(first, length, tag=f'{tag}_left_bound')}) /\\ "
        f"(({_lt(second, length, tag=f'{tag}_right_bound')}) /\\ "
        f"(({_at(left_code, left_scale, first, value, tag=f'{tag}_left')}) /\\ "
        f"({_at(right_code, right_scale, second, value, tag=f'{tag}_right')}))))"
    )


def make_four_square_cross_pigeonhole_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Turn two injective half-ranges and a genuine merged cover into a cross collision."""

    left_bounded = _bounded("b", "c", "l", "p", tag="left")
    right_bounded = _bounded("d", "e", "l", "p", tag="right")
    merged_bounded = _bounded("z", "t", "l + l", "p", tag="merged")
    coverage = _coverage("b", "c", "d", "e", "z", "t", "l", tag="merged")
    left_injective = injective_prefix("b", "c", "l", tag="fscp_left")
    right_injective = injective_prefix("d", "e", "l", tag="fscp_right")
    collision = _collision("z", "t", "l + l", tag="fscp_merge")
    cross = _cross("b", "c", "d", "e", "l", tag="result")

    return (
        spec(
            FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED,
            f"forall b c d e z t l p. ({left_bounded}) -> ({right_bounded}) "
            f"-> ({coverage}) -> ({merged_bounded})",
            ("beta_at_exists", "beta_at_unique"),
            (
                "intro b", "intro c", "intro d", "intro e",
                "intro z", "intro t", "intro l", "intro p",
                "intro hleft", "intro hright", "intro hcover",
                "intro i", "intro hibound",
                f"have hvalue : exists v. {_at('z', 't', 'i', 'v', tag='bounded_value')}",
                "apply beta_at_exists",
                "cases hvalue",
                f"have hcase : "
                f"{_coverage_case('b', 'c', 'd', 'e', 'i', 'x', 'l', tag='bounded_case')}",
                "specialize hcover i", "specialize hcover x", "apply hcover",
                "exact hibound", "exact hvalue_witness", "cases hcase",
                "cases hcase_left", "cases hcase_left_witness",
                "cases hcase_left_witness_right",
                f"have hbound : exists v. "
                f"(({_at('b', 'c', 'x1', 'v', tag='bounded_first_lookup')}) /\\ "
                f"({_lt('v', 'p', tag='bounded_first_limit')}))",
                "specialize hleft x1", "apply hleft",
                "exact hcase_left_witness_left", "cases hbound",
                "cases hbound_witness",
                "have hequal : x = x2",
                "specialize beta_at_unique b", "specialize beta_at_unique c",
                "specialize beta_at_unique x1", "specialize beta_at_unique x",
                "specialize beta_at_unique x2", "apply beta_at_unique",
                "exact hcase_left_witness_right_left", "exact hbound_witness_left",
                "exists x", "split", "exact hvalue_witness", "rewrite hequal",
                "exact hbound_witness_right",
                "cases hcase_right", "cases hcase_right_witness",
                "cases hcase_right_witness_right",
                f"have hbound : exists v. "
                f"(({_at('d', 'e', 'x1', 'v', tag='bounded_second_lookup')}) /\\ "
                f"({_lt('v', 'p', tag='bounded_second_limit')}))",
                "specialize hright x1", "apply hright",
                "exact hcase_right_witness_left", "cases hbound",
                "cases hbound_witness",
                "have hequal : x = x2",
                "specialize beta_at_unique d", "specialize beta_at_unique e",
                "specialize beta_at_unique x1", "specialize beta_at_unique x",
                "specialize beta_at_unique x2", "apply beta_at_unique",
                "exact hcase_right_witness_right_left", "exact hbound_witness_left",
                "exists x", "split", "exact hvalue_witness", "rewrite hequal",
                "exact hbound_witness_right",
            ),
            "A genuinely covered interleaving of two bounded decoded beta prefixes remains bounded in their common finite codomain.",
        ),
        spec(
            FOUR_SQUARE_CROSS_PIGEONHOLE,
            f"forall b c d e z t l p. ({left_bounded}) -> ({right_bounded}) -> "
            f"({left_injective}) -> ({right_injective}) -> ({coverage}) -> "
            f"({_lt('p', 'l + l', tag='overflow')}) -> ({cross})",
            (
                FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED,
                "finite_bounded_into_oversized_collision",
            ),
            (
                "intro b", "intro c", "intro d", "intro e",
                "intro z", "intro t", "intro l", "intro p",
                "intro hleft", "intro hright", "intro hleft_injective",
                "intro hright_injective", "intro hcover", "intro hoverflow",
                f"have hbounded : {merged_bounded}",
                "specialize four_square_cross_covered_prefix_bounded b",
                "specialize four_square_cross_covered_prefix_bounded c",
                "specialize four_square_cross_covered_prefix_bounded d",
                "specialize four_square_cross_covered_prefix_bounded e",
                "specialize four_square_cross_covered_prefix_bounded z",
                "specialize four_square_cross_covered_prefix_bounded t",
                "specialize four_square_cross_covered_prefix_bounded l",
                "specialize four_square_cross_covered_prefix_bounded p",
                "apply four_square_cross_covered_prefix_bounded",
                "exact hleft", "exact hright", "exact hcover",
                f"have hcollision : {collision}",
                "specialize finite_bounded_into_oversized_collision z",
                "specialize finite_bounded_into_oversized_collision t",
                "specialize finite_bounded_into_oversized_collision (l + l)",
                "specialize finite_bounded_into_oversized_collision p",
                "apply finite_bounded_into_oversized_collision",
                "exact hbounded", "exact hoverflow",
                "cases hcollision", "cases hcollision_witness",
                "cases hcollision_witness_witness",
                "cases hcollision_witness_witness_witness",
                "cases hcollision_witness_witness_witness_right",
                "cases hcollision_witness_witness_witness_right_right",
                "cases hcollision_witness_witness_witness_right_right_right",
                f"have hfirst_case : "
                f"{_coverage_case('b', 'c', 'd', 'e', 'x', 'x2', 'l', tag='first_case')}",
                "specialize hcover x", "specialize hcover x2", "apply hcover",
                "exact hcollision_witness_witness_witness_left",
                "exact hcollision_witness_witness_witness_right_right_right_left",
                f"have hsecond_case : "
                f"{_coverage_case('b', 'c', 'd', 'e', 'x1', 'x2', 'l', tag='second_case')}",
                "specialize hcover x1", "specialize hcover x2", "apply hcover",
                "exact hcollision_witness_witness_witness_right_left",
                "exact hcollision_witness_witness_witness_right_right_right_right",
                "cases hfirst_case",
                "cases hfirst_case_left", "cases hfirst_case_left_witness",
                "cases hfirst_case_left_witness_right",
                "cases hsecond_case",
                "cases hsecond_case_left", "cases hsecond_case_left_witness",
                "cases hsecond_case_left_witness_right",
                "have hequal : x3 = x4",
                "specialize hleft_injective x3", "specialize hleft_injective x4",
                "specialize hleft_injective x2", "apply hleft_injective",
                "exact hfirst_case_left_witness_left",
                "exact hsecond_case_left_witness_left",
                "exact hfirst_case_left_witness_right_left",
                "exact hsecond_case_left_witness_right_left",
                "exfalso",
                "apply hcollision_witness_witness_witness_right_right_left",
                "trans x3 + x3", "exact hfirst_case_left_witness_right_right",
                "trans x4 + x4", "congr", "exact hequal", "exact hequal",
                "symm", "exact hsecond_case_left_witness_right_right",
                "cases hsecond_case_right", "cases hsecond_case_right_witness",
                "cases hsecond_case_right_witness_right",
                "exists x3", "exists x4", "exists x2", "split",
                "exact hfirst_case_left_witness_left", "split",
                "exact hsecond_case_right_witness_left", "split",
                "exact hfirst_case_left_witness_right_left",
                "exact hsecond_case_right_witness_right_left",
                "cases hfirst_case_right", "cases hfirst_case_right_witness",
                "cases hfirst_case_right_witness_right",
                "cases hsecond_case",
                "cases hsecond_case_left", "cases hsecond_case_left_witness",
                "cases hsecond_case_left_witness_right",
                "exists x4", "exists x3", "exists x2", "split",
                "exact hsecond_case_left_witness_left", "split",
                "exact hfirst_case_right_witness_left", "split",
                "exact hsecond_case_left_witness_right_left",
                "exact hfirst_case_right_witness_right_left",
                "cases hsecond_case_right", "cases hsecond_case_right_witness",
                "cases hsecond_case_right_witness_right",
                "have hequal : x3 = x4",
                "specialize hright_injective x3", "specialize hright_injective x4",
                "specialize hright_injective x2", "apply hright_injective",
                "exact hfirst_case_right_witness_left",
                "exact hsecond_case_right_witness_left",
                "exact hfirst_case_right_witness_right_left",
                "exact hsecond_case_right_witness_right_left",
                "exfalso",
                "apply hcollision_witness_witness_witness_right_right_left",
                "trans S (x3 + x3)",
                "exact hfirst_case_right_witness_right_right",
                "trans S (x4 + x4)", "congr", "congr",
                "exact hequal", "exact hequal",
                "symm", "exact hsecond_case_right_witness_right_right",
            ),
            "Two bounded injective equal-length prefixes whose covered interleaving overflows their finite codomain have an actual witnessed cross-family value collision.",
        ),
        spec(
            FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS,
            f"forall b c d e l. exists z t. "
            f"({_coverage('b', 'c', 'd', 'e', 'z', 't', 'l', tag='exists_result')})",
            (
                "le_zero",
                "succ_ne_zero",
                "beta_at_exists",
                "beta_prefix_append_two_exists",
                "pair_order_double_succ_length",
                "finite_lt_succ_eq_or_lt",
                "beta_at_unique",
                "le_refl",
                "le_succ",
            ),
            (
                "intro b", "intro c", "intro d", "intro e", "induction l",
                "exists 0", "exists 0", "intro i", "intro v", "intro hibound",
                "intro hentry", "exfalso", "have hzero : S i = 0",
                "specialize le_zero (S i)", "apply le_zero",
                "have hsum : 0 + 0 = 0", "apply PA3",
                "rewrite hsum at hibound", "exact hibound",
                "specialize succ_ne_zero i", "apply succ_ne_zero", "exact hzero",
                "cases IH", "cases IH_witness",
                f"have hleft : exists a. {_at('b', 'c', 'l', 'a', tag='exists_left')}",
                "apply beta_at_exists", "cases hleft",
                f"have hright : exists a. {_at('d', 'e', 'l', 'a', tag='exists_right')}",
                "apply beta_at_exists", "cases hright",
                f"have hpair : exists z t. "
                f"(({_at('z', 't', 'l + l', 'x2', tag='exists_pair_first')}) /\\ "
                f"(({_at('z', 't', 'S (l + l)', 'x3', tag='exists_pair_second')}) /\\ "
                f"(forall i v. ({_lt('i', 'l + l', tag='exists_pair_before')}) -> "
                f"({_at('x', 'x1', 'i', 'v', tag='exists_pair_old')}) -> "
                f"({_at('z', 't', 'i', 'v', tag='exists_pair_new')}))))",
                "specialize beta_prefix_append_two_exists x",
                "specialize beta_prefix_append_two_exists x1",
                "specialize beta_prefix_append_two_exists (l + l)",
                "specialize beta_prefix_append_two_exists x2",
                "specialize beta_prefix_append_two_exists x3",
                "exact beta_prefix_append_two_exists",
                "cases hpair", "cases hpair_witness", "cases hpair_witness_witness",
                "cases hpair_witness_witness_right",
                "exists x4", "exists x5", "intro i", "intro v",
                "intro hibound", "intro hentry",
                "have hshape : S (S (l + l)) = S l + S l",
                "specialize pair_order_double_succ_length (l + l)",
                "specialize pair_order_double_succ_length l",
                "apply pair_order_double_succ_length", "refl",
                "rewrite <- hshape at hibound",
                "have hlast : i = S (l + l) \\/ "
                f"({_lt('i', 'S (l + l)', tag='exists_last_before')})",
                "specialize finite_lt_succ_eq_or_lt (S (l + l))",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hibound",
                "cases hlast",
                f"have hnormalized : {_at('x4', 'x5', 'S (l + l)', 'v', tag='exists_last_normal')}",
                "rewrite <- hlast_left", "rewrite <- hlast_left", "exact hentry",
                "have hequal : v = x3",
                "specialize beta_at_unique x4", "specialize beta_at_unique x5",
                "specialize beta_at_unique (S (l + l))",
                "specialize beta_at_unique v", "specialize beta_at_unique x3",
                "apply beta_at_unique", "exact hnormalized",
                "exact hpair_witness_witness_right_left",
                "right", "exists l", "split", "apply le_refl", "split",
                "rewrite hequal", "rewrite hequal", "exact hright_witness",
                "exact hlast_left",
                "have hprevious : i = l + l \\/ "
                f"({_lt('i', 'l + l', tag='exists_previous_before')})",
                "specialize finite_lt_succ_eq_or_lt (l + l)",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt", "exact hlast_right",
                "cases hprevious",
                f"have hnormalized : {_at('x4', 'x5', 'l + l', 'v', tag='exists_previous_normal')}",
                "rewrite <- hprevious_left", "rewrite <- hprevious_left", "exact hentry",
                "have hequal : v = x2",
                "specialize beta_at_unique x4", "specialize beta_at_unique x5",
                "specialize beta_at_unique (l + l)",
                "specialize beta_at_unique v", "specialize beta_at_unique x2",
                "apply beta_at_unique", "exact hnormalized",
                "exact hpair_witness_witness_left",
                "left", "exists l", "split", "apply le_refl", "split",
                "rewrite hequal", "rewrite hequal", "exact hleft_witness",
                "exact hprevious_left",
                f"have hold : exists u. {_at('x', 'x1', 'i', 'u', tag='exists_old')}",
                "apply beta_at_exists", "cases hold",
                f"have hpreserved : {_at('x4', 'x5', 'i', 'x6', tag='exists_preserved')}",
                "specialize hpair_witness_witness_right_right i",
                "specialize hpair_witness_witness_right_right x6",
                "apply hpair_witness_witness_right_right",
                "exact hprevious_right", "exact hold_witness",
                "have hequal : v = x6",
                "specialize beta_at_unique x4", "specialize beta_at_unique x5",
                "specialize beta_at_unique i", "specialize beta_at_unique v",
                "specialize beta_at_unique x6", "apply beta_at_unique",
                "exact hentry", "exact hpreserved",
                f"have holdcase : "
                f"{_coverage_case('b', 'c', 'd', 'e', 'i', 'x6', 'l', tag='exists_old_case')}",
                "specialize IH_witness_witness i",
                "specialize IH_witness_witness x6", "apply IH_witness_witness",
                "exact hprevious_right", "exact hold_witness",
                "cases holdcase",
                "cases holdcase_left", "cases holdcase_left_witness",
                "cases holdcase_left_witness_right",
                "left", "exists x7", "split",
                "specialize le_succ (S x7)", "specialize le_succ l",
                "apply le_succ", "exact holdcase_left_witness_left",
                "split", "rewrite hequal", "rewrite hequal",
                "exact holdcase_left_witness_right_left",
                "exact holdcase_left_witness_right_right",
                "cases holdcase_right", "cases holdcase_right_witness",
                "cases holdcase_right_witness_right",
                "right", "exists x7", "split",
                "specialize le_succ (S x7)", "specialize le_succ l",
                "apply le_succ", "exact holdcase_right_witness_left",
                "split", "rewrite hequal", "rewrite hequal",
                "exact holdcase_right_witness_right_left",
                "exact holdcase_right_witness_right_right",
            ),
            "Any two equally long beta-coded prefixes have an actual beta-coded even/odd interleaving with complete constructive source coverage.",
        ),
        spec(
            FOUR_SQUARE_CROSS_INTERSECTION,
            f"forall b c d e l p. ({left_bounded}) -> ({right_bounded}) -> "
            f"({left_injective}) -> ({right_injective}) -> "
            f"({_lt('p', 'l + l', tag='intersection_overflow')}) -> ({cross})",
            (FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS, FOUR_SQUARE_CROSS_PIGEONHOLE),
            (
                "intro b", "intro c", "intro d", "intro e", "intro l", "intro p",
                "intro hleft", "intro hright", "intro hleft_injective",
                "intro hright_injective", "intro hoverflow",
                f"have hcode : exists z t. "
                f"({_coverage('b', 'c', 'd', 'e', 'z', 't', 'l', tag='intersection_code')})",
                "specialize four_square_cross_interleaved_prefix_exists b",
                "specialize four_square_cross_interleaved_prefix_exists c",
                "specialize four_square_cross_interleaved_prefix_exists d",
                "specialize four_square_cross_interleaved_prefix_exists e",
                "specialize four_square_cross_interleaved_prefix_exists l",
                "exact four_square_cross_interleaved_prefix_exists",
                "cases hcode", "cases hcode_witness",
                "specialize four_square_cross_pigeonhole b",
                "specialize four_square_cross_pigeonhole c",
                "specialize four_square_cross_pigeonhole d",
                "specialize four_square_cross_pigeonhole e",
                "specialize four_square_cross_pigeonhole x",
                "specialize four_square_cross_pigeonhole x1",
                "specialize four_square_cross_pigeonhole l",
                "specialize four_square_cross_pigeonhole p",
                "apply four_square_cross_pigeonhole", "exact hleft", "exact hright",
                "exact hleft_injective", "exact hright_injective",
                "exact hcode_witness_witness", "exact hoverflow",
            ),
            "Any two injective bounded equal-length decoded prefixes with combined length exceeding their codomain have an explicit actual common value.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_CROSS_COVERED_PREFIX_BOUNDED",
    "FOUR_SQUARE_CROSS_INTERLEAVED_PREFIX_EXISTS",
    "FOUR_SQUARE_CROSS_INTERSECTION",
    "FOUR_SQUARE_CROSS_PIGEONHOLE",
    "make_four_square_cross_pigeonhole_candidate_theorems",
]
