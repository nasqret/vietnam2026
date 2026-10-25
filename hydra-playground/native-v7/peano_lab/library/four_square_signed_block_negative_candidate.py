"""Negative-orientation modular quaternion blocks for constructive descent.

Both isolated canonical surfaces use only expanded first-order HA relations
and do not modify the Alpha or Stable theorem editions.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_two_squares_collision_norm_candidate import _mod
from .four_square_conjugate_identity_candidate import (
    conjugate_coordinate_contributions,
)
from .four_square_identity_candidate import _conjunction, _coordinate_contributions
from .four_square_signed_quaternion_candidate import _permutation_commands


FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS = (
    "four_square_signed_conjugate_negative_blocks"
)
FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS = (
    "four_square_signed_natural_positive_first_blocks"
)


def _modulo(left: str, right: str, *, tag: str) -> str:
    return _mod("k", left, right, tag=f"fssbn_{tag}")


def _negative_orientation(original: str, centered: str, *, tag: str) -> str:
    return _modulo(f"{original} + {centered}", "0", tag=f"{tag}_negative")


def _positive_orientation(original: str, centered: str, *, tag: str) -> str:
    return _modulo(original, centered, tag=f"{tag}_positive")


def _surface(
    blocks: tuple[tuple[str, str], ...],
    signs: tuple[bool, bool, bool, bool],
    *,
    tag: str,
) -> str:
    norm = "e * e + f * f + g * g + h * h"
    orientations = tuple(
        _positive_orientation(original, centered, tag=f"{tag}_{original}")
        if positive
        else _negative_orientation(original, centered, tag=f"{tag}_{original}")
        for original, centered, positive in zip("abcd", "efgh", signs, strict=True)
    )
    conclusions = tuple(
        _modulo(left, right, tag=f"{tag}_block_{index}")
        for index, (left, right) in enumerate(blocks)
    )
    return (
        "forall k a b c d e f g h. "
        f"({_modulo(norm, '0', tag=f'{tag}_norm')}) -> "
        + " -> ".join(f"({orientation})" for orientation in orientations)
        + f" -> ({_conjunction(conclusions)})"
    )


def _negative_dot(
    label: str,
    original: str,
    centered: str,
    hypothesis: str,
) -> tuple[str, ...]:
    return (
        f"have {label} : "
        f"{_modulo(f'{original} * {centered} + {centered} * {centered}', '0', tag=label)}",
        "specialize four_square_signed_dot_negative_zero k",
        f"specialize four_square_signed_dot_negative_zero {original}",
        f"specialize four_square_signed_dot_negative_zero {centered}",
        "apply four_square_signed_dot_negative_zero",
        f"exact {hypothesis}",
    )


def _zero_add(
    label: str,
    left: str,
    right: str,
    left_hypothesis: str,
    right_hypothesis: str,
) -> tuple[str, ...]:
    return (
        f"have {label} : {_modulo(f'({left}) + ({right})', '0', tag=label)}",
        "specialize four_square_signed_mod_zero_add k",
        f"specialize four_square_signed_mod_zero_add ({left})",
        f"specialize four_square_signed_mod_zero_add ({right})",
        "apply four_square_signed_mod_zero_add",
        f"exact {left_hypothesis}",
        f"exact {right_hypothesis}",
    )


def _negative_cross(
    label: str,
    first_original: str,
    second_original: str,
    first_centered: str,
    second_centered: str,
    first_hypothesis: str,
    second_hypothesis: str,
) -> tuple[str, ...]:
    left = f"{first_original} * {second_centered}"
    right = f"{second_original} * {first_centered}"
    return (
        f"have {label} : {_modulo(left, right, tag=label)}",
        "specialize four_square_signed_cross_negative k",
        f"specialize four_square_signed_cross_negative {first_original}",
        f"specialize four_square_signed_cross_negative {second_original}",
        f"specialize four_square_signed_cross_negative {first_centered}",
        f"specialize four_square_signed_cross_negative {second_centered}",
        "apply four_square_signed_cross_negative",
        f"exact {first_hypothesis}",
        f"exact {second_hypothesis}",
    )


def _combine_congruences(
    first_left: str,
    first_right: str,
    second_left: str,
    second_right: str,
    first_hypothesis: str,
    second_hypothesis: str,
) -> tuple[str, ...]:
    return (
        "specialize mod_eq_add k",
        f"specialize mod_eq_add ({first_left})",
        f"specialize mod_eq_add ({first_right})",
        f"specialize mod_eq_add ({second_left})",
        f"specialize mod_eq_add ({second_right})",
        "apply mod_eq_add",
        f"exact {first_hypothesis}",
        f"exact {second_hypothesis}",
    )


def _negative_vector(
    first: tuple[str, str, str, str, str, str],
    second: tuple[str, str, str, str, str, str],
    *,
    tag: str,
) -> tuple[str, ...]:
    a, b, e, f, ha, hb = first
    c, d, g, h, hc, hd = second
    return (
        *_negative_cross(f"h{tag}_first", a, b, e, f, ha, hb),
        *_negative_cross(f"h{tag}_second", c, d, g, h, hc, hd),
        *_combine_congruences(
            f"{a} * {f}",
            f"{b} * {e}",
            f"{c} * {h}",
            f"{d} * {g}",
            f"h{tag}_first",
            f"h{tag}_second",
        ),
    )


def _mixed_zero(
    label: str,
    positive_original: str,
    negative_original: str,
    positive_centered: str,
    negative_centered: str,
    positive_hypothesis: str,
    negative_hypothesis: str,
) -> tuple[str, ...]:
    left = f"{positive_original} * {negative_centered} + {negative_original} * {positive_centered}"
    return (
        f"have {label} : {_modulo(left, '0', tag=label)}",
        "specialize four_square_signed_cross_mixed_zero k",
        f"specialize four_square_signed_cross_mixed_zero {positive_original}",
        f"specialize four_square_signed_cross_mixed_zero {negative_original}",
        f"specialize four_square_signed_cross_mixed_zero {positive_centered}",
        f"specialize four_square_signed_cross_mixed_zero {negative_centered}",
        "apply four_square_signed_cross_mixed_zero",
        f"exact {positive_hypothesis}",
        f"exact {negative_hypothesis}",
    )


def _prepend_zero(
    zero: str,
    left: str,
    right: str,
    zero_hypothesis: str,
    congruence_hypothesis: str,
) -> tuple[str, ...]:
    return (
        "specialize four_square_signed_mod_zero_plus_congruent k",
        f"specialize four_square_signed_mod_zero_plus_congruent ({zero})",
        f"specialize four_square_signed_mod_zero_plus_congruent ({left})",
        f"specialize four_square_signed_mod_zero_plus_congruent ({right})",
        "apply four_square_signed_mod_zero_plus_congruent",
        f"exact {zero_hypothesis}",
        f"exact {congruence_hypothesis}",
    )


def make_four_square_signed_block_negative_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the all-negative conjugate and positive-first natural surfaces."""

    introductions = (
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
    )
    centered_norm = "e * e + f * f + g * g + h * h"
    negative_dot_blocks = tuple(
        f"{original} * {centered} + {centered} * {centered}"
        for original, centered in zip("abcd", "efgh", strict=True)
    )
    scalar_dot = "a * e + b * f + c * g + d * h"
    scalar_zero_source = (
        f"(({negative_dot_blocks[0]}) + ({negative_dot_blocks[1]})) + "
        f"(({negative_dot_blocks[2]}) + ({negative_dot_blocks[3]}))"
    )
    scalar_grouped = (
        "((a * e + b * f) + (c * g + d * h)) + "
        "((e * e + f * f) + (g * g + h * h))"
    )

    negative_scalar = (
        *_negative_dot("hda", "a", "e", "ha"),
        *_negative_dot("hdb", "b", "f", "hb"),
        *_negative_dot("hdc", "c", "g", "hc"),
        *_negative_dot("hdd", "d", "h", "hd"),
        *_zero_add(
            "habzero", negative_dot_blocks[0], negative_dot_blocks[1], "hda", "hdb"
        ),
        *_zero_add(
            "hcdzero", negative_dot_blocks[2], negative_dot_blocks[3], "hdc", "hdd"
        ),
        *_zero_add(
            "hallzero",
            f"({negative_dot_blocks[0]}) + ({negative_dot_blocks[1]})",
            f"({negative_dot_blocks[2]}) + ({negative_dot_blocks[3]})",
            "habzero",
            "hcdzero",
        ),
        f"have hshuffle : ({scalar_zero_source}) = (({scalar_dot}) + ({centered_norm}))",
        f"trans {scalar_grouped}",
        "apply four_square_euler_four_add_shuffle",
        "congr",
        "symm",
        "apply add_assoc",
        "symm",
        "apply add_assoc",
        "rewrite hshuffle at hallzero",
        "specialize four_square_signed_zero_cancel_right k",
        f"specialize four_square_signed_zero_cancel_right ({scalar_dot})",
        f"specialize four_square_signed_zero_cancel_right ({centered_norm})",
        "apply four_square_signed_zero_cancel_right",
        "exact hallzero",
        "exact hnorm",
    )

    negative_script = introductions + (
        "split",
        *negative_scalar,
        "split",
        *_negative_vector(
            ("a", "b", "e", "f", "ha", "hb"),
            ("c", "d", "g", "h", "hc", "hd"),
            tag="negative_one",
        ),
        "split",
        *_negative_vector(
            ("a", "c", "e", "g", "ha", "hc"),
            ("d", "b", "h", "f", "hd", "hb"),
            tag="negative_two",
        ),
        *_negative_vector(
            ("a", "d", "e", "h", "ha", "hd"),
            ("b", "c", "f", "g", "hb", "hc"),
            tag="negative_three",
        ),
    )

    negative_group = "b * f + c * g + d * h"
    negative_squares = "f * f + g * g + h * h"
    source_negative_group = (
        f"(({negative_dot_blocks[1]}) + ({negative_dot_blocks[2]})) + "
        f"({negative_dot_blocks[3]})"
    )
    source_atoms = ("b * f", "f * f", "c * g", "g * g", "d * h", "h * h")
    target_atoms = ("b * f", "c * g", "d * h", "f * f", "g * g", "h * h")

    positive_scalar = (
        f"have hpositive : {_modulo('a * e', 'e * e', tag='positive_first_dot')}",
        "specialize four_square_signed_dot_positive k",
        "specialize four_square_signed_dot_positive a",
        "specialize four_square_signed_dot_positive e",
        "apply four_square_signed_dot_positive",
        "exact ha",
        *_negative_dot("hdb", "b", "f", "hb"),
        *_negative_dot("hdc", "c", "g", "hc"),
        *_negative_dot("hdd", "d", "h", "hd"),
        *_zero_add(
            "hbczero", negative_dot_blocks[1], negative_dot_blocks[2], "hdb", "hdc"
        ),
        *_zero_add(
            "hnegative",
            f"({negative_dot_blocks[1]}) + ({negative_dot_blocks[2]})",
            negative_dot_blocks[3],
            "hbczero",
            "hdd",
        ),
        f"have hshuffle : ({source_negative_group}) = "
        f"(({negative_group}) + ({negative_squares}))",
        *_permutation_commands(source_atoms, target_atoms),
        "rewrite hshuffle at hnegative",
        f"have hnormshape : ({centered_norm}) = "
        f"((e * e) + ({negative_squares}))",
        "simp [add_assoc]",
        "rewrite hnormshape at hnorm",
        "specialize four_square_signed_partition_balance k",
        "specialize four_square_signed_partition_balance (a * e)",
        "specialize four_square_signed_partition_balance (e * e)",
        f"specialize four_square_signed_partition_balance ({negative_group})",
        f"specialize four_square_signed_partition_balance ({negative_squares})",
        "apply four_square_signed_partition_balance",
        "exact hpositive",
        "exact hnegative",
        "exact hnorm",
    )

    positive_first_script = introductions + (
        "split",
        *positive_scalar,
        "split",
        *_mixed_zero("hfirst_zero", "a", "b", "e", "f", "ha", "hb"),
        *_negative_cross("hfirst_cross", "c", "d", "g", "h", "hc", "hd"),
        *_prepend_zero(
            "a * f + b * e", "c * h", "d * g", "hfirst_zero", "hfirst_cross"
        ),
        "split",
        *_mixed_zero("hsecond_zero", "a", "c", "e", "g", "ha", "hc"),
        *_negative_cross("hsecond_cross", "d", "b", "h", "f", "hd", "hb"),
        *_prepend_zero(
            "a * g + c * e", "d * f", "b * h", "hsecond_zero", "hsecond_cross"
        ),
        *_mixed_zero("hthird_zero", "a", "d", "e", "h", "ha", "hd"),
        *_negative_cross("hthird_cross", "b", "c", "f", "g", "hb", "hc"),
        "have hswap : (a * h + b * g) + d * e = (a * h + d * e) + b * g",
        "apply four_square_euler_add_swap_last",
        "rewrite hswap",
        *_prepend_zero(
            "a * h + d * e", "b * g", "c * f", "hthird_zero", "hthird_cross"
        ),
    )

    return (
        spec(
            FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS,
            _surface(
                conjugate_coordinate_contributions(),
                (False, False, False, False),
                tag="conjugate_negative",
            ),
            (
                "four_square_signed_dot_negative_zero",
                "four_square_signed_mod_zero_add",
                "four_square_euler_four_add_shuffle",
                "add_assoc",
                "four_square_signed_zero_cancel_right",
                "four_square_signed_cross_negative",
                "mod_eq_add",
            ),
            negative_script,
            "When all four centered coordinate orientations are negative, every exact conjugate-quaternion positive/negative block is congruent modulo the multiplier.",
        ),
        spec(
            FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS,
            _surface(
                _coordinate_contributions(),
                (True, False, False, False),
                tag="natural_positive_first",
            ),
            (
                "four_square_signed_dot_positive",
                "four_square_signed_dot_negative_zero",
                "four_square_signed_mod_zero_add",
                "add_assoc",
                "add_comm",
                "four_square_add_swap_right_tail",
                "four_square_signed_partition_balance",
                "four_square_signed_cross_mixed_zero",
                "four_square_signed_cross_negative",
                "four_square_signed_mod_zero_plus_congruent",
                "four_square_euler_add_swap_last",
            ),
            positive_first_script,
            "A positive first orientation and three negative orientations make all four ordinary Hamilton quaternion blocks congruent modulo the multiplier.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_SIGNED_CONJUGATE_NEGATIVE_BLOCKS",
    "FOUR_SQUARE_SIGNED_NATURAL_POSITIVE_FIRST_BLOCKS",
    "make_four_square_signed_block_negative_candidate_theorems",
]
