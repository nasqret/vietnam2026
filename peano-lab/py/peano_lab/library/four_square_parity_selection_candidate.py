"""Constructive parity selection and unconditional four-square even descent.

All relations below expand to first-order HA formulas.  These are isolated,
dependency-curried candidate bodies: they do not change Alpha or Stable.
"""

from __future__ import annotations

from typing import Any, Callable

from .four_square_descent_candidate import (
    FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING,
    matching_parity,
)
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF = "four_square_parity_square_mod_two_self"
FOUR_SQUARE_PARITY_PAIR_MOD_TWO_SUM = "four_square_parity_pair_mod_two_sum"
FOUR_SQUARE_PARITY_TRIPLE_MOD_TWO_SUM = "four_square_parity_triple_mod_two_sum"
FOUR_SQUARE_PARITY_NORM_MOD_TWO_SUM = "four_square_parity_norm_mod_two_sum"
FOUR_SQUARE_PARITY_EVEN_NORM_COORDINATE_SUM = (
    "four_square_parity_even_norm_coordinate_sum"
)
FOUR_SQUARE_PARITY_ODD_BLOCKS_CROSSED_SELECTION = (
    "four_square_parity_odd_blocks_crossed_selection"
)
FOUR_SQUARE_PARITY_EVEN_COORDINATE_PAIR_SELECTION = (
    "four_square_parity_even_coordinate_pair_selection"
)
FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION = (
    "four_square_parity_even_norm_pair_selection"
)
FOUR_SQUARE_PARITY_SWAP_MIDDLE_COORDINATES = (
    "four_square_parity_swap_middle_coordinates"
)
FOUR_SQUARE_PARITY_SWAP_OUTER_COORDINATES = (
    "four_square_parity_swap_outer_coordinates"
)
FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING = (
    "four_square_parity_even_multiplier_halving"
)
FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING = (
    "four_square_parity_represented_double_halving"
)
FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING = (
    "four_square_parity_represented_additive_double_halving"
)


def _even(value: str, *, tag: str) -> str:
    witness = f"fsps_even_{tag}"
    return f"exists {witness}. ({value}) = 2 * {witness}"


def _odd(value: str, *, tag: str) -> str:
    witness = f"fsps_odd_{tag}"
    return f"exists {witness}. ({value}) = 2 * {witness} + 1"


def _mod_two(left: str, right: str, *, tag: str) -> str:
    u = f"fsps_u_{tag}"
    v = f"fsps_v_{tag}"
    return f"exists {u} {v}. ({left}) + 2 * {u} = ({right}) + 2 * {v}"


def _matching(first: str, second: str, *, tag: str) -> str:
    return matching_parity(first, second, tag=f"fsps_{tag}")


def _crossed_selection(*, tag: str) -> str:
    return (
        f"((({_matching('a', 'c', tag=f'{tag}_ac')}) /\\ "
        f"({_matching('b', 'd', tag=f'{tag}_bd')})) \\/ "
        f"(({_matching('a', 'd', tag=f'{tag}_ad')}) /\\ "
        f"({_matching('b', 'c', tag=f'{tag}_bc')})))"
    )


def _selection(*, tag: str) -> str:
    return (
        f"((({_matching('a', 'b', tag=f'{tag}_ab')}) /\\ "
        f"({_matching('c', 'd', tag=f'{tag}_cd')})) \\/ "
        f"({_crossed_selection(tag=f'{tag}_crossed')}))"
    )


def make_four_square_parity_selection_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Select equal-parity pairs without assuming their original positions."""

    norm = "a * a + b * b + c * c + d * d"
    coordinate_sum = "a + b + c + d"
    return (
        spec(
            FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF,
            f"forall a. ({_mod_two('a * a', 'a', tag='square')})",
            ("parity_cases", "matching_parity_mod_two", "even_mul_left", "odd_mul_odd"),
            (
                "intro a",
                "have hparity : exists q. a = 2 * q \\/ a = 2 * q + 1",
                "apply parity_cases",
                "cases hparity",
                "cases hparity_witness",
                "specialize matching_parity_mod_two (a * a)",
                "specialize matching_parity_mod_two a",
                "apply matching_parity_mod_two",
                "left",
                "split",
                "specialize even_mul_left a",
                "specialize even_mul_left a",
                "apply even_mul_left",
                "exists x",
                "exact hparity_witness_left",
                "exists x",
                "exact hparity_witness_left",
                "specialize matching_parity_mod_two (a * a)",
                "specialize matching_parity_mod_two a",
                "apply matching_parity_mod_two",
                "right",
                "split",
                "specialize odd_mul_odd a",
                "specialize odd_mul_odd a",
                "apply odd_mul_odd",
                "exists x",
                "exact hparity_witness_right",
                "exists x",
                "exact hparity_witness_right",
                "exists x",
                "exact hparity_witness_right",
            ),
            "Every natural square has exactly the same residue modulo two as its coordinate.",
        ),
        spec(
            FOUR_SQUARE_PARITY_PAIR_MOD_TWO_SUM,
            f"forall a b. ({_mod_two('a * a + b * b', 'a + b', tag='pair')})",
            (FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF, "mod_eq_add"),
            (
                "intro a",
                "intro b",
                "specialize mod_eq_add 2",
                "specialize mod_eq_add (a * a)",
                "specialize mod_eq_add a",
                "specialize mod_eq_add (b * b)",
                "specialize mod_eq_add b",
                "apply mod_eq_add",
                "apply four_square_parity_square_mod_two_self",
                "apply four_square_parity_square_mod_two_self",
            ),
            "The sum of two coordinate squares is congruent modulo two to their ordinary sum.",
        ),
        spec(
            FOUR_SQUARE_PARITY_TRIPLE_MOD_TWO_SUM,
            f"forall a b c. ({_mod_two('a * a + b * b + c * c', 'a + b + c', tag='triple')})",
            (
                FOUR_SQUARE_PARITY_PAIR_MOD_TWO_SUM,
                FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF,
                "mod_eq_add",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "specialize mod_eq_add 2",
                "specialize mod_eq_add (a * a + b * b)",
                "specialize mod_eq_add (a + b)",
                "specialize mod_eq_add (c * c)",
                "specialize mod_eq_add c",
                "apply mod_eq_add",
                "apply four_square_parity_pair_mod_two_sum",
                "apply four_square_parity_square_mod_two_self",
            ),
            "Three coordinate squares preserve their coordinate-sum parity.",
        ),
        spec(
            FOUR_SQUARE_PARITY_NORM_MOD_TWO_SUM,
            f"forall a b c d. ({_mod_two(norm, coordinate_sum, tag='norm')})",
            (
                FOUR_SQUARE_PARITY_TRIPLE_MOD_TWO_SUM,
                FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF,
                "mod_eq_add",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "specialize mod_eq_add 2",
                "specialize mod_eq_add (a * a + b * b + c * c)",
                "specialize mod_eq_add (a + b + c)",
                "specialize mod_eq_add (d * d)",
                "specialize mod_eq_add d",
                "apply mod_eq_add",
                "apply four_square_parity_triple_mod_two_sum",
                "apply four_square_parity_square_mod_two_self",
            ),
            "Every four-square norm has the parity of the sum of all four coordinates.",
        ),
        spec(
            FOUR_SQUARE_PARITY_EVEN_NORM_COORDINATE_SUM,
            f"forall n a b c d. n * 2 = {norm} -> "
            f"({_even(coordinate_sum, tag='coordinate_sum')})",
            (
                FOUR_SQUARE_PARITY_NORM_MOD_TWO_SUM,
                "mod_two_preserves_parity",
                "mul_comm",
            ),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnorm",
                "have htransport : "
                f"(((({_even(norm, tag='transport_norm')}) -> "
                f"({_even(coordinate_sum, tag='transport_sum')})) /\\ "
                f"(({_even(coordinate_sum, tag='transport_back')}) -> "
                f"({_even(norm, tag='transport_back_norm')}))) /\\ "
                f"((({_odd(norm, tag='transport_odd_norm')}) -> "
                f"({_odd(coordinate_sum, tag='transport_odd_sum')})) /\\ "
                f"(({_odd(coordinate_sum, tag='transport_odd_back')}) -> "
                f"({_odd(norm, tag='transport_odd_back_norm')}))))",
                f"specialize mod_two_preserves_parity ({norm})",
                f"specialize mod_two_preserves_parity ({coordinate_sum})",
                "apply mod_two_preserves_parity",
                "apply four_square_parity_norm_mod_two_sum",
                "cases htransport",
                "cases htransport_left",
                "apply htransport_left_left",
                "exists n",
                "trans n * 2",
                "symm",
                "exact hnorm",
                "apply mul_comm",
            ),
            "An actually even represented norm forces the ordinary sum of its coordinates to be even.",
        ),
        spec(
            FOUR_SQUARE_PARITY_ODD_BLOCKS_CROSSED_SELECTION,
            "forall a b c d. "
            f"({_odd('a + b', tag='odd_first')}) -> "
            f"({_odd('c + d', tag='odd_second')}) -> "
            f"({_crossed_selection(tag='odd_blocks')})",
            ("odd_sum_parity_cases",),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hfirst_odd",
                "intro hsecond_odd",
                "have hfirst : "
                f"((({_even('a', tag='first_a_even')}) /\\ "
                f"({_odd('b', tag='first_b_odd')})) \\/ "
                f"(({_odd('a', tag='first_a_odd')}) /\\ "
                f"({_even('b', tag='first_b_even')})))",
                "specialize odd_sum_parity_cases a",
                "specialize odd_sum_parity_cases b",
                "apply odd_sum_parity_cases",
                "exact hfirst_odd",
                "have hsecond : "
                f"((({_even('c', tag='second_c_even')}) /\\ "
                f"({_odd('d', tag='second_d_odd')})) \\/ "
                f"(({_odd('c', tag='second_c_odd')}) /\\ "
                f"({_even('d', tag='second_d_even')})))",
                "apply odd_sum_parity_cases",
                "exact hsecond_odd",
                "cases hfirst",
                "cases hfirst_left",
                "cases hsecond",
                "cases hsecond_left",
                "left",
                "split",
                "left",
                "split",
                "exact hfirst_left_left",
                "exact hsecond_left_left",
                "right",
                "split",
                "exact hfirst_left_right",
                "exact hsecond_left_right",
                "cases hsecond_right",
                "right",
                "split",
                "left",
                "split",
                "exact hfirst_left_left",
                "exact hsecond_right_right",
                "right",
                "split",
                "exact hfirst_left_right",
                "exact hsecond_right_left",
                "cases hfirst_right",
                "cases hsecond",
                "cases hsecond_left",
                "right",
                "split",
                "right",
                "split",
                "exact hfirst_right_left",
                "exact hsecond_left_right",
                "left",
                "split",
                "exact hfirst_right_right",
                "exact hsecond_left_left",
                "cases hsecond_right",
                "left",
                "split",
                "right",
                "split",
                "exact hfirst_right_left",
                "exact hsecond_right_left",
                "left",
                "split",
                "exact hfirst_right_right",
                "exact hsecond_right_right",
            ),
            "If both original coordinate-pair sums are odd, one of the two crossed pairings has matching parity in each pair.",
        ),
        spec(
            FOUR_SQUARE_PARITY_EVEN_COORDINATE_PAIR_SELECTION,
            f"forall a b c d. ({_even(coordinate_sum, tag='selection_sum')}) -> "
            f"({_selection(tag='coordinate_selection')})",
            (
                "add_assoc",
                "even_sum_parity_cases",
                FOUR_SQUARE_PARITY_ODD_BLOCKS_CROSSED_SELECTION,
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro heven",
                f"have hgrouped : {_even('(a + b) + (c + d)', tag='grouped')}",
                "cases heven",
                "exists x",
                "trans a + b + c + d",
                "symm",
                "apply add_assoc",
                "exact heven_witness",
                "have hblocks : "
                f"((({_even('a + b', tag='block_first_even')}) /\\ "
                f"({_even('c + d', tag='block_second_even')})) \\/ "
                f"(({_odd('a + b', tag='block_first_odd')}) /\\ "
                f"({_odd('c + d', tag='block_second_odd')})))",
                "specialize even_sum_parity_cases (a + b)",
                "specialize even_sum_parity_cases (c + d)",
                "apply even_sum_parity_cases",
                "exact hgrouped",
                "cases hblocks",
                "cases hblocks_left",
                "left",
                "split",
                "apply even_sum_parity_cases",
                "exact hblocks_left_left",
                "apply even_sum_parity_cases",
                "exact hblocks_left_right",
                "cases hblocks_right",
                "right",
                "apply four_square_parity_odd_blocks_crossed_selection",
                "exact hblocks_right_left",
                "exact hblocks_right_right",
            ),
            "Every even sum of four naturals constructively selects one of the three partitions into two equal-parity pairs.",
        ),
        spec(
            FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION,
            f"forall n a b c d. n * 2 = {norm} -> "
            f"({_selection(tag='norm_selection')})",
            (
                FOUR_SQUARE_PARITY_EVEN_NORM_COORDINATE_SUM,
                FOUR_SQUARE_PARITY_EVEN_COORDINATE_PAIR_SELECTION,
            ),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnorm",
                "apply four_square_parity_even_coordinate_pair_selection",
                "specialize four_square_parity_even_norm_coordinate_sum n",
                "apply four_square_parity_even_norm_coordinate_sum",
                "exact hnorm",
            ),
            "Every even four-square norm admits a witnessed choice of two equal-parity coordinate pairs.",
        ),
        spec(
            FOUR_SQUARE_PARITY_SWAP_MIDDLE_COORDINATES,
            "forall a b c d. "
            "a * a + b * b + c * c + d * d = "
            "a * a + c * c + b * b + d * d",
            ("add_assoc", "add_shuffle_middle"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans (a * a + b * b) + (c * c + d * d)",
                "apply add_assoc",
                "trans (a * a + c * c) + (b * b + d * d)",
                "apply add_shuffle_middle",
                "symm",
                "apply add_assoc",
            ),
            "Swapping the middle coordinates preserves an explicitly left-associated four-square norm.",
        ),
        spec(
            FOUR_SQUARE_PARITY_SWAP_OUTER_COORDINATES,
            "forall a b c d. "
            "a * a + b * b + c * c + d * d = "
            "a * a + d * d + b * b + c * c",
            ("add_assoc", "add_comm", "add_shuffle_middle"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans (a * a + b * b) + (c * c + d * d)",
                "apply add_assoc",
                "trans (a * a + b * b) + (d * d + c * c)",
                "congr",
                "refl",
                "apply add_comm",
                "trans (a * a + d * d) + (b * b + c * c)",
                "apply add_shuffle_middle",
                "symm",
                "apply add_assoc",
            ),
            "The second crossed coordinate partition preserves the full natural four-square norm.",
        ),
        spec(
            FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING,
            f"forall n a b c d. n * 2 = {norm} -> "
            f"({four_square_representation('n', tag='fsps_half')})",
            (
                FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION,
                FOUR_SQUARE_PARITY_SWAP_MIDDLE_COORDINATES,
                FOUR_SQUARE_PARITY_SWAP_OUTER_COORDINATES,
                FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING,
            ),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnorm",
                f"have hpairs : {_selection(tag='half_pairs')}",
                "specialize four_square_parity_even_norm_pair_selection n",
                "apply four_square_parity_even_norm_pair_selection",
                "exact hnorm",
                "cases hpairs",
                "cases hpairs_left",
                "specialize four_square_descent_even_multiplier_matching_parity_halving n",
                "specialize four_square_descent_even_multiplier_matching_parity_halving a",
                "specialize four_square_descent_even_multiplier_matching_parity_halving b",
                "specialize four_square_descent_even_multiplier_matching_parity_halving c",
                "specialize four_square_descent_even_multiplier_matching_parity_halving d",
                "apply four_square_descent_even_multiplier_matching_parity_halving",
                "exact hnorm",
                "exact hpairs_left_left",
                "exact hpairs_left_right",
                "cases hpairs_right",
                "cases hpairs_right_left",
                "specialize four_square_descent_even_multiplier_matching_parity_halving n",
                "specialize four_square_descent_even_multiplier_matching_parity_halving a",
                "specialize four_square_descent_even_multiplier_matching_parity_halving c",
                "specialize four_square_descent_even_multiplier_matching_parity_halving b",
                "specialize four_square_descent_even_multiplier_matching_parity_halving d",
                "apply four_square_descent_even_multiplier_matching_parity_halving",
                "trans a * a + b * b + c * c + d * d",
                "exact hnorm",
                "apply four_square_parity_swap_middle_coordinates",
                "exact hpairs_right_left_left",
                "exact hpairs_right_left_right",
                "cases hpairs_right_right",
                "specialize four_square_descent_even_multiplier_matching_parity_halving n",
                "specialize four_square_descent_even_multiplier_matching_parity_halving a",
                "specialize four_square_descent_even_multiplier_matching_parity_halving d",
                "specialize four_square_descent_even_multiplier_matching_parity_halving b",
                "specialize four_square_descent_even_multiplier_matching_parity_halving c",
                "apply four_square_descent_even_multiplier_matching_parity_halving",
                "trans a * a + b * b + c * c + d * d",
                "exact hnorm",
                "apply four_square_parity_swap_outer_coordinates",
                "exact hpairs_right_right_left",
                "exact hpairs_right_right_right",
            ),
            "Every represented even natural n·2 has an actual four-square representation of n, with no coordinate-parity premise.",
        ),
        spec(
            FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING,
            f"forall n. ({four_square_representation('n * 2', tag='fsps_double')}) -> "
            f"({four_square_representation('n', tag='fsps_double_half')})",
            (FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING,),
            (
                "intro n",
                "intro hdouble",
                "cases hdouble",
                "cases hdouble_witness",
                "cases hdouble_witness_witness",
                "cases hdouble_witness_witness_witness",
                "specialize four_square_parity_even_multiplier_halving n",
                "specialize four_square_parity_even_multiplier_halving x",
                "specialize four_square_parity_even_multiplier_halving x1",
                "specialize four_square_parity_even_multiplier_halving x2",
                "specialize four_square_parity_even_multiplier_halving x3",
                "apply four_square_parity_even_multiplier_halving",
                "exact hdouble_witness_witness_witness_witness",
            ),
            "Four-square representability is unconditionally closed under division of represented doubles by two.",
        ),
        spec(
            FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING,
            f"forall n. ({four_square_representation('n + n', tag='fsps_add_double')}) -> "
            f"({four_square_representation('n', tag='fsps_add_half')})",
            (
                "mul_comm",
                "two_mul_eq_add_self",
                FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING,
            ),
            (
                "intro n",
                "intro hdouble",
                "cases hdouble",
                "cases hdouble_witness",
                "cases hdouble_witness_witness",
                "cases hdouble_witness_witness_witness",
                "specialize four_square_parity_even_multiplier_halving n",
                "specialize four_square_parity_even_multiplier_halving x",
                "specialize four_square_parity_even_multiplier_halving x1",
                "specialize four_square_parity_even_multiplier_halving x2",
                "specialize four_square_parity_even_multiplier_halving x3",
                "apply four_square_parity_even_multiplier_halving",
                "trans n + n",
                "trans 2 * n",
                "apply mul_comm",
                "apply two_mul_eq_add_self",
                "exact hdouble_witness_witness_witness_witness",
            ),
            "For every natural n, an actual four-square representation of n+n constructively produces one of n.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_PARITY_EVEN_COORDINATE_PAIR_SELECTION",
    "FOUR_SQUARE_PARITY_EVEN_MULTIPLIER_HALVING",
    "FOUR_SQUARE_PARITY_EVEN_NORM_COORDINATE_SUM",
    "FOUR_SQUARE_PARITY_EVEN_NORM_PAIR_SELECTION",
    "FOUR_SQUARE_PARITY_NORM_MOD_TWO_SUM",
    "FOUR_SQUARE_PARITY_ODD_BLOCKS_CROSSED_SELECTION",
    "FOUR_SQUARE_PARITY_PAIR_MOD_TWO_SUM",
    "FOUR_SQUARE_PARITY_REPRESENTED_ADDITIVE_DOUBLE_HALVING",
    "FOUR_SQUARE_PARITY_REPRESENTED_DOUBLE_HALVING",
    "FOUR_SQUARE_PARITY_SQUARE_MOD_TWO_SELF",
    "FOUR_SQUARE_PARITY_SWAP_MIDDLE_COORDINATES",
    "FOUR_SQUARE_PARITY_SWAP_OUTER_COORDINATES",
    "FOUR_SQUARE_PARITY_TRIPLE_MOD_TWO_SUM",
    "make_four_square_parity_selection_candidate_theorems",
]
