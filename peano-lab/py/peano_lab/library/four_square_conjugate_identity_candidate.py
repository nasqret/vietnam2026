"""Constructive conjugate-quaternion Euler identity for all signed patterns.

All notation expands into first-order Heyting arithmetic; these isolated
candidate bodies grant no Alpha or Stable admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .four_square_euler_candidate import (
    FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
    FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
    FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
    FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
    _coordinate_balance_surface,
    _four_grouped,
    _left_group,
)
from .four_square_identity_candidate import (
    FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
    FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
    _absolute_expression,
    _conjunction,
    _square_balance_expression,
)
from .four_square_signed_quaternion_candidate import (
    _permutation_commands,
    _sq,
    _sym,
)


FOUR_SQUARE_CONJUGATE_DIAGONAL_REGROUP = "four_square_conjugate_diagonal_regroup"
FOUR_SQUARE_CONJUGATE_SCALAR_DECOMPOSITION = (
    "four_square_conjugate_scalar_decomposition"
)
FOUR_SQUARE_CONJUGATE_LEFT_DECOMPOSITION = "four_square_conjugate_left_decomposition"
FOUR_SQUARE_CONJUGATE_CROSS_DECOMPOSITION = "four_square_conjugate_cross_decomposition"
FOUR_SQUARE_CONJUGATE_MIXED_DECOMPOSITION = "four_square_conjugate_mixed_decomposition"
FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION = "four_square_conjugate_global_compensation"
FOUR_SQUARE_CONJUGATE_COORDINATE_SQUARE_TRANSPORT = (
    "four_square_conjugate_coordinate_square_transport"
)
FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION = "four_square_signed_conjugate_quaternion"
FOUR_SQUARE_CONJUGATE_ABSOLUTE_COORDINATES_TOTAL = (
    "four_square_conjugate_absolute_coordinates_total"
)


def conjugate_coordinate_contributions() -> tuple[tuple[str, str], ...]:
    """Return the exact all-positive scalar and three two-versus-two blocks."""

    return (
        ("a * e + b * f + c * g + d * h", "0"),
        ("a * f + c * h", "b * e + d * g"),
        ("a * g + d * f", "c * e + b * h"),
        ("a * h + b * g", "d * e + c * f"),
    )


def make_four_square_conjugate_identity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Prove conjugate Euler by separately bounded diagonal/cross cancellation."""

    variables = tuple("abcdefgh")
    introductions = tuple(f"intro {value}" for value in variables)
    contributions = conjugate_coordinate_contributions()
    positive = tuple(block[0] for block in contributions)
    negative = tuple(block[1] for block in contributions)
    magnitudes = tuple(f"m{index}" for index in range(4))
    balances, actual_left, actual_square, actual_cross = _coordinate_balance_surface(
        positive,
        negative,
        magnitudes,
    )
    absolute = tuple(
        _absolute_expression(left, right, magnitude)
        for left, right, magnitude in zip(positive, negative, magnitudes, strict=True)
    )

    norm = (
        "(a * a + b * b + c * c + d * d) * "
        "(e * e + f * f + g * g + h * h)"
    )
    scalar_atoms = ("a * e", "b * f", "c * g", "d * h")
    vector_atoms = (
        (("a * f", "c * h"), ("b * e", "d * g")),
        (("a * g", "d * f"), ("c * e", "b * h")),
        (("a * h", "b * g"), ("d * e", "c * f")),
    )
    diagonal_atoms = tuple(_sq(atom) for atom in scalar_atoms) + tuple(
        _sq(atom)
        for positive_pair, negative_pair in vector_atoms
        for atom in (*positive_pair, *negative_pair)
    )
    row_major_atoms = tuple(
        _sq(f"{left} * {right}") for left in "abcd" for right in "efgh"
    )
    scalar_diagonal = _left_group(tuple(_sq(atom) for atom in scalar_atoms))
    vector_diagonals = tuple(
        _left_group(
            (
                _left_group(tuple(_sq(atom) for atom in positive_pair)),
                _left_group(tuple(_sq(atom) for atom in negative_pair)),
            )
        )
        for positive_pair, negative_pair in vector_atoms
    )
    grouped_diagonals = _four_grouped((scalar_diagonal, *vector_diagonals))
    diagonal = _left_group(
        tuple(_left_group(row_major_atoms[index : index + 4]) for index in (0, 4, 8, 12))
    )

    scalar_mixed = (
        _sym("a * e", "b * f"),
        _sym("a * e", "c * g"),
        _sym("b * f", "c * g"),
        _sym("d * h", "a * e"),
        _sym("d * h", "b * f"),
        _sym("d * h", "c * g"),
    )
    vector_mixed = tuple(
        (_sym(*positive_pair), _sym(*negative_pair))
        for positive_pair, negative_pair in vector_atoms
    )
    mixed_atoms = scalar_mixed + tuple(atom for block in vector_mixed for atom in block)
    scalar_mixed_group = _left_group(
        (_left_group(scalar_mixed[:3]), _left_group(scalar_mixed[3:]))
    )
    mixed_groups = (scalar_mixed_group,) + tuple(
        _left_group(block) for block in vector_mixed
    )
    grouped_mixed = _four_grouped(mixed_groups)
    flat_mixed = _left_group(mixed_atoms)

    cross_groups = tuple(
        _left_group(
            (
                _left_group(
                    (
                        _sym(positive_pair[0], negative_pair[0]),
                        _sym(positive_pair[0], negative_pair[1]),
                    )
                ),
                _left_group(
                    (
                        _sym(positive_pair[1], negative_pair[0]),
                        _sym(positive_pair[1], negative_pair[1]),
                    )
                ),
            )
        )
        for positive_pair, negative_pair in vector_atoms
    )
    grouped_cross = _four_grouped(("0", *cross_groups))
    cross_atoms = tuple(
        _sym(first, second)
        for positive_pair, negative_pair in vector_atoms
        for first in positive_pair
        for second in negative_pair
    )
    flat_cross = _left_group(cross_atoms)

    swapped_atoms = (
        _sym("a * f", "b * e"),
        _sym("a * g", "c * e"),
        _sym("b * g", "c * f"),
        _sym("a * h", "d * e"),
        _sym("d * f", "b * h"),
        _sym("c * h", "d * g"),
        _sym("a * h", "c * f"),
        _sym("b * g", "d * e"),
        _sym("a * f", "d * g"),
        _sym("c * h", "b * e"),
        _sym("a * g", "b * h"),
        _sym("d * f", "c * e"),
    )
    if tuple(swapped_atoms[index] for index in (0, 8, 9, 5, 1, 10, 11, 4, 3, 6, 7, 2)) != cross_atoms:
        raise AssertionError("conjugate mixed-product permutation changed")
    flat_swapped = _left_group(swapped_atoms)

    mixed_script: list[str] = list(introductions)
    mixed_script.append(f"trans {flat_swapped}")
    mixed_script.extend("congr" for _ in range(len(mixed_atoms) - 1))
    for index in range(len(mixed_atoms)):
        if index in (3, 5):
            opposite = (
                _sym("d * e", "a * h")
                if index == 3
                else _sym("d * g", "c * h")
            )
            mixed_script.extend(
                (
                    f"trans {opposite}",
                    "apply four_square_euler_double_cross_swap",
                    "apply add_comm",
                )
            )
        else:
            mixed_script.append("apply four_square_euler_double_cross_swap")
    mixed_script.extend(_permutation_commands(swapped_atoms, cross_atoms))

    scalar_decomposition = _left_group((scalar_diagonal, scalar_mixed_group))
    vector_decompositions = tuple(
        _left_group((diagonal_block, mixed_block))
        for diagonal_block, mixed_block in zip(
            vector_diagonals,
            mixed_groups[1:],
            strict=True,
        )
    )
    coordinate_decompositions = _four_grouped(
        (scalar_decomposition, *vector_decompositions)
    )

    return (
        spec(
            FOUR_SQUARE_CONJUGATE_DIAGONAL_REGROUP,
            f"forall {' '.join(variables)}. ({grouped_diagonals}) = ({diagonal})",
            ("add_assoc", "add_comm", "four_square_add_swap_right_tail"),
            introductions + _permutation_commands(diagonal_atoms, row_major_atoms),
            "The conjugate quaternion's sixteen diagonal squares regroup into the exact row-major norm-product diagonal.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_SCALAR_DECOMPOSITION,
            f"forall {' '.join(variables)}. "
            f"({positive[0]}) * ({positive[0]}) + 0 * 0 = ({scalar_decomposition})",
            ("four_square_signed_sum_four_decomposition",),
            introductions
            + (
                f"trans ({positive[0]}) * ({positive[0]})",
                "simp",
                "apply four_square_signed_sum_four_decomposition",
            ),
            "The all-positive conjugate scalar square decomposes into its four diagonal and six symmetric mixed blocks.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_LEFT_DECOMPOSITION,
            f"forall {' '.join(variables)}. ({actual_left}) = "
            f"(({grouped_diagonals}) + ({flat_mixed}))",
            (
                FOUR_SQUARE_CONJUGATE_SCALAR_DECOMPOSITION,
                "four_square_signed_pair_block_decomposition",
                FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
                "add_assoc",
            ),
            introductions
            + (
                f"trans {coordinate_decompositions}",
                "congr",
                "congr",
                "apply four_square_conjugate_scalar_decomposition",
                "apply four_square_signed_pair_block_decomposition",
                "congr",
                "apply four_square_signed_pair_block_decomposition",
                "apply four_square_signed_pair_block_decomposition",
                f"trans ({grouped_diagonals}) + ({grouped_mixed})",
                "apply four_square_euler_four_add_shuffle",
                "congr",
                "refl",
                "simp [add_assoc]",
            ),
            "All conjugate scalar/vector coordinate squares separate into sixteen diagonal squares and exactly twelve same-sign mixed blocks.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_CROSS_DECOMPOSITION,
            f"forall {' '.join(variables)}. ({actual_cross}) = ({flat_cross})",
            (
                "four_square_signed_pair_cross_decomposition",
                "add_assoc",
                "mul_zero_left",
                "zero_add",
            ),
            introductions
            + (
                f"trans {grouped_cross}",
                "congr",
                "congr",
                "simp [mul_zero_left, zero_add]",
                "apply four_square_signed_pair_cross_decomposition",
                "congr",
                "apply four_square_signed_pair_cross_decomposition",
                "apply four_square_signed_pair_cross_decomposition",
                "simp [add_assoc, zero_add]",
            ),
            "The three conjugate vector corrections decompose into the twelve opposite-sign mixed blocks; the scalar correction vanishes.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_MIXED_DECOMPOSITION,
            f"forall {' '.join(variables)}. ({flat_mixed}) = ({flat_cross})",
            (
                FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
                "add_assoc",
                "add_comm",
                "four_square_add_swap_right_tail",
            ),
            tuple(mixed_script),
            "Each of the twelve conjugate same-sign mixed blocks crosses its right factors into its unique opposite-sign correction block.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION,
            f"forall {' '.join(variables)}. "
            f"(({norm}) + ({actual_cross})) = ({actual_left})",
            (
                FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
                FOUR_SQUARE_CONJUGATE_DIAGONAL_REGROUP,
                FOUR_SQUARE_CONJUGATE_CROSS_DECOMPOSITION,
                FOUR_SQUARE_CONJUGATE_MIXED_DECOMPOSITION,
                FOUR_SQUARE_CONJUGATE_LEFT_DECOMPOSITION,
            ),
            introductions
            + (
                f"trans ({diagonal}) + ({actual_cross})",
                "congr",
                "apply four_square_euler_diagonal_expansion",
                "refl",
                f"trans ({grouped_diagonals}) + ({actual_cross})",
                "congr",
                "symm",
                "apply four_square_conjugate_diagonal_regroup",
                "refl",
                f"trans ({grouped_diagonals}) + ({flat_cross})",
                "congr",
                "refl",
                "apply four_square_conjugate_cross_decomposition",
                f"trans ({grouped_diagonals}) + ({flat_mixed})",
                "congr",
                "refl",
                "symm",
                "apply four_square_conjugate_mixed_decomposition",
                "symm",
                "apply four_square_conjugate_left_decomposition",
            ),
            "The complete subtraction-free conjugate quaternion compensation equation follows from sixteen diagonal and twelve explicitly crossed mixed blocks.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_COORDINATE_SQUARE_TRANSPORT,
            f"forall {' '.join(variables)} {' '.join(magnitudes)}. "
            f"({_conjunction(absolute)}) -> ({_conjunction(balances)})",
            (FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,),
            introductions
            + tuple(f"intro {magnitude}" for magnitude in magnitudes)
            + (
                "intro habsolute",
                "cases habsolute",
                "cases habsolute_right",
                "cases habsolute_right_right",
                "split",
                "apply four_square_absolute_square_balance",
                "exact habsolute_left",
                "split",
                "apply four_square_absolute_square_balance",
                "exact habsolute_right_left",
                "split",
                "apply four_square_absolute_square_balance",
                "exact habsolute_right_right_left",
                "apply four_square_absolute_square_balance",
                "exact habsolute_right_right_right",
            ),
            "Each exact conjugate absolute coordinate independently satisfies its constructive natural square/cross-term balance.",
        ),
        spec(
            FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION,
            f"forall {' '.join(variables)} {' '.join(magnitudes)}. "
            f"({_conjunction(absolute)}) -> ({norm}) = "
            "m0 * m0 + m1 * m1 + m2 * m2 + m3 * m3",
            (
                FOUR_SQUARE_CONJUGATE_COORDINATE_SQUARE_TRANSPORT,
                FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
                FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION,
                "add_assoc",
            ),
            introductions
            + tuple(f"intro {magnitude}" for magnitude in magnitudes)
            + (
                "intro habsolute",
                f"have hbalances : ({_conjunction(balances)})",
            )
            + tuple(
                f"specialize four_square_conjugate_coordinate_square_transport {value}"
                for value in (*variables, *magnitudes)
            )
            + (
                "apply four_square_conjugate_coordinate_square_transport",
                "exact habsolute",
                "cases hbalances",
                "cases hbalances_right",
                "cases hbalances_right_right",
                f"trans {actual_square}",
            )
            + (f"specialize four_square_euler_compensation_cancel ({norm})",)
            + tuple(
                command
                for left, right, magnitude in zip(
                    positive,
                    negative,
                    magnitudes,
                    strict=True,
                )
                for command in (
                    f"specialize four_square_euler_compensation_cancel ({left})",
                    f"specialize four_square_euler_compensation_cancel ({right})",
                    f"specialize four_square_euler_compensation_cancel {magnitude}",
                )
            )
            + (
                "apply four_square_euler_compensation_cancel",
                "exact hbalances_left",
                "exact hbalances_right_left",
                "exact hbalances_right_right_left",
                "exact hbalances_right_right_right",
                "apply four_square_conjugate_global_compensation",
                "symm",
                "apply add_assoc",
            ),
            "Euler's full eight-variable conjugate quaternion identity holds for the all-positive scalar and all three exact two-positive/two-negative vector coordinates.",
        ),
        spec(
            FOUR_SQUARE_CONJUGATE_ABSOLUTE_COORDINATES_TOTAL,
            f"forall {' '.join(variables)}. exists {' '.join(magnitudes)}. "
            f"(({_conjunction(absolute)}) /\\ "
            f"(({norm}) = m0 * m0 + m1 * m1 + m2 * m2 + m3 * m3))",
            (
                FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
                FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION,
            ),
            introductions
            + tuple(
                command
                for index, (left, right) in enumerate(contributions)
                for command in (
                    f"have h{index} : exists magnitude. "
                    f"({_absolute_expression(left, right, 'magnitude')})",
                    f"specialize four_square_absolute_difference_total ({left})",
                    f"specialize four_square_absolute_difference_total ({right})",
                    "exact four_square_absolute_difference_total",
                )
            )
            + tuple(f"cases h{index}" for index in range(4))
            + ("exists x", "exists x1", "exists x2", "exists x3", "split")
            + tuple(
                command
                for index in range(3)
                for command in ("split", f"exact h{index}_witness")
            )
            + (
                "exact h3_witness",
                "apply four_square_signed_conjugate_quaternion",
                "split",
                "exact h0_witness",
                "split",
                "exact h1_witness",
                "split",
                "exact h2_witness",
                "exact h3_witness",
            ),
            "Every pair of natural four-square tuples has four explicit conjugate absolute coordinates satisfying the complete norm identity.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_CONJUGATE_ABSOLUTE_COORDINATES_TOTAL",
    "FOUR_SQUARE_CONJUGATE_CROSS_DECOMPOSITION",
    "FOUR_SQUARE_CONJUGATE_COORDINATE_SQUARE_TRANSPORT",
    "FOUR_SQUARE_CONJUGATE_DIAGONAL_REGROUP",
    "FOUR_SQUARE_CONJUGATE_GLOBAL_COMPENSATION",
    "FOUR_SQUARE_CONJUGATE_LEFT_DECOMPOSITION",
    "FOUR_SQUARE_CONJUGATE_MIXED_DECOMPOSITION",
    "FOUR_SQUARE_CONJUGATE_SCALAR_DECOMPOSITION",
    "FOUR_SQUARE_SIGNED_CONJUGATE_QUATERNION",
    "conjugate_coordinate_contributions",
    "make_four_square_conjugate_identity_candidate_theorems",
]
