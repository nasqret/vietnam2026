"""Bounded constructive quaternion cross-cancellation for Euler's identity.

These isolated candidate bodies build the exact mixed-product cancellations,
four-coordinate balance aggregation, diagonal expansion, and conditional
subtraction-free Euler bridge in the unchanged first-order HA kernel.  No
candidate is enrolled in Alpha/Stable or asserts Lagrange's theorem.
"""

from __future__ import annotations

from typing import Any, Callable

from .four_square_identity_candidate import (
    FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
    FOUR_SQUARE_NORM_DISTRIBUTES,
    FOUR_SQUARE_PRODUCT_SQUARE,
    QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
    QUATERNION_COORDINATE_SQUARE_TRANSPORT,
    _absolute_expression,
    _conjunction,
    _coordinate_contributions,
    _square_balance_expression,
)


FOUR_SQUARE_EULER_CROSS_SWAP = "four_square_euler_cross_swap"
FOUR_SQUARE_EULER_MIXED_AB = "four_square_euler_mixed_ab"
FOUR_SQUARE_EULER_MIXED_AC = "four_square_euler_mixed_ac"
FOUR_SQUARE_EULER_MIXED_AD = "four_square_euler_mixed_ad"
FOUR_SQUARE_EULER_MIXED_BC = "four_square_euler_mixed_bc"
FOUR_SQUARE_EULER_MIXED_BD = "four_square_euler_mixed_bd"
FOUR_SQUARE_EULER_MIXED_CD = "four_square_euler_mixed_cd"
FOUR_SQUARE_EULER_ALL_MIXED_CANCEL = "four_square_euler_all_mixed_cancel"
FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE = "four_square_euler_four_add_shuffle"
FOUR_SQUARE_EULER_BALANCE_AGGREGATE = "four_square_euler_balance_aggregate"
FOUR_SQUARE_EULER_COMPENSATION_CANCEL = "four_square_euler_compensation_cancel"
FOUR_SQUARE_EULER_DIAGONAL_BLOCK = "four_square_euler_diagonal_block"
FOUR_SQUARE_EULER_DIAGONAL_EXPANSION = "four_square_euler_diagonal_expansion"
FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL = (
    "four_square_euler_quaternion_conditional"
)
FOUR_SQUARE_EULER_ADD_PERMUTE_SIX = "four_square_euler_add_permute_six"
FOUR_SQUARE_EULER_ADD_PERMUTE_NINE = "four_square_euler_add_permute_nine"
FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE = "four_square_euler_add_permute_twelve"
FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN = "four_square_euler_add_permute_sixteen"
FOUR_SQUARE_EULER_ADD_SWAP_LAST = "four_square_euler_add_swap_last"
FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION = (
    "four_square_euler_three_square_expansion"
)
FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION = (
    "four_square_euler_cross_triple_expansion"
)
FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP = "four_square_euler_double_cross_swap"
FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE = (
    "four_square_euler_coordinate_single_decompose"
)
FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE = (
    "four_square_euler_coordinate_triple_decompose"
)
FOUR_SQUARE_EULER_DIAGONAL_REGROUP = "four_square_euler_diagonal_regroup"
FOUR_SQUARE_EULER_LEFT_DECOMPOSITION = "four_square_euler_left_decomposition"
FOUR_SQUARE_EULER_CROSS_DECOMPOSITION = "four_square_euler_cross_decomposition"
FOUR_SQUARE_EULER_MIXED_DECOMPOSITION = "four_square_euler_mixed_decomposition"
FOUR_SQUARE_EULER_GLOBAL_COMPENSATION = "four_square_euler_global_compensation"
FOUR_SQUARE_EULER_QUATERNION = "four_square_euler_quaternion"
FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL = (
    "four_square_euler_four_square_product_total"
)
FOUR_SQUARE_EULER_REPRESENTATIONS_CLOSED_UNDER_MULTIPLICATION = (
    "four_square_euler_representations_closed_under_multiplication"
)


_MIXED_PAIRS = (
    (FOUR_SQUARE_EULER_MIXED_AB, ("a", "f", "b", "e"), ("a", "h", "b", "g")),
    (FOUR_SQUARE_EULER_MIXED_AC, ("a", "f", "c", "h"), ("a", "g", "c", "e")),
    (FOUR_SQUARE_EULER_MIXED_AD, ("a", "g", "d", "f"), ("a", "h", "d", "e")),
    (FOUR_SQUARE_EULER_MIXED_BC, ("b", "f", "c", "g"), ("b", "e", "c", "h")),
    (FOUR_SQUARE_EULER_MIXED_BD, ("b", "f", "d", "h"), ("b", "g", "d", "e")),
    (FOUR_SQUARE_EULER_MIXED_CD, ("c", "g", "d", "h"), ("c", "e", "d", "f")),
)


def _cross_equality(arguments: tuple[str, str, str, str]) -> str:
    a, b, c, d = arguments
    return f"(({a} * {b}) * ({c} * {d}) = ({a} * {d}) * ({c} * {b}))"


def _four_grouped(parts: tuple[str, str, str, str]) -> str:
    return f"((({parts[0]}) + ({parts[1]})) + (({parts[2]}) + ({parts[3]})))"


def _left_group(parts: tuple[str, ...]) -> str:
    """Keep every additive AST shape explicit in generated tactic terms."""

    if not parts:
        raise ValueError("an additive block cannot be empty")
    result = f"({parts[0]})"
    for part in parts[1:]:
        result = f"({result} + ({part}))"
    return result


def _right_group(parts: tuple[str, ...]) -> str:
    if not parts:
        raise ValueError("an additive block cannot be empty")
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"(({part}) + {result})"
    return result


def _move_addend_to_front(parts: tuple[str, ...], position: int) -> list[str]:
    """Prove one adjacent-swap insertion without an AC search tactic."""

    if not 0 <= position < len(parts):
        raise ValueError("additive permutation position is outside its block")
    if position == 0:
        return ["refl"]
    if len(parts) == 2:
        return ["apply add_comm"]
    if position == 1:
        return ["apply four_square_add_swap_right_tail"]

    selected = parts[position]
    tail = parts[1:]
    moved_tail = (selected,) + tuple(
        value for index, value in enumerate(tail) if index != position - 1
    )
    intermediate = _right_group((parts[0],) + moved_tail)
    return (
        [f"trans {intermediate}", "congr", "refl"]
        + _move_addend_to_front(tail, position - 1)
        + ["apply four_square_add_swap_right_tail"]
    )


def _permute_addends(source: tuple[str, ...], target: tuple[str, ...]) -> list[str]:
    """Synthesize ordinary trans/congr/assoc/comm kernel proof commands."""

    if len(source) != len(target) or sorted(source) != sorted(target):
        raise ValueError("additive permutations must have the same exact addends")
    if source == target:
        return ["refl"]
    position = source.index(target[0])
    if position == 0:
        return ["congr", "refl"] + _permute_addends(source[1:], target[1:])

    remainder = tuple(value for index, value in enumerate(source) if index != position)
    intermediate = (target[0],) + remainder
    return (
        [f"trans {_right_group(intermediate)}"]
        + _move_addend_to_front(source, position)
        + ["congr", "refl"]
        + _permute_addends(remainder, target[1:])
    )


def _permutation_script(source: tuple[str, ...], target: tuple[str, ...]) -> tuple[str, ...]:
    return (
        tuple(f"intro {name}" for name in source)
        + (f"trans {_right_group(source)}", "simp [add_assoc]")
        + (f"trans {_right_group(target)}",)
        + tuple(_permute_addends(source, target))
        + ("symm", "simp [add_assoc]")
    )


def _squared(value: str) -> str:
    return f"({value}) * ({value})"


def _symmetric_product(first: str, second: str) -> str:
    return _left_group(
        (f"({first}) * ({second})", f"({second}) * ({first})")
    )


def _cross_swapped_pair(first: str, second: str) -> str:
    first_left, first_right = tuple(part.strip() for part in first.split("*"))
    second_left, second_right = tuple(part.strip() for part in second.split("*"))
    return _symmetric_product(
        f"{first_left} * {second_right}", f"{second_left} * {first_right}"
    )


def _coordinate_balance_surface(
    positive: tuple[str, str, str, str],
    negative: tuple[str, str, str, str],
    magnitude: tuple[str, str, str, str],
) -> tuple[tuple[str, str, str, str], str, str, str]:
    left = tuple(
        f"({p}) * ({p}) + ({n}) * ({n})"
        for p, n in zip(positive, negative, strict=True)
    )
    cross = tuple(
        f"({p}) * ({n}) + ({n}) * ({p})"
        for p, n in zip(positive, negative, strict=True)
    )
    square = tuple(f"({m}) * ({m})" for m in magnitude)
    balances = tuple(
        f"({lhs}) = (({mag}) + ({term}))"
        for lhs, mag, term in zip(left, square, cross, strict=True)
    )
    return balances, _four_grouped(left), _four_grouped(square), _four_grouped(cross)


def make_four_square_euler_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build bounded quaternion cancellation without polynomial automation."""

    inputs = ("a", "b", "c", "d", "e", "f", "g", "h")
    introductions = tuple(f"intro {name}" for name in inputs)
    pair_formulas = tuple(
        f"(({_cross_equality(first)}) /\\ ({_cross_equality(second)}))"
        for _, first, second in _MIXED_PAIRS
    )
    pair_rows = []
    for name, first, second in _MIXED_PAIRS:
        script: list[str] = list(introductions)
        script.append("split")
        for arguments in (first, second):
            script.extend(
                f"specialize four_square_euler_cross_swap {argument}"
                for argument in arguments
            )
            script.append("exact four_square_euler_cross_swap")
        pair_rows.append(
            spec(
                name,
                f"forall {' '.join(inputs)}. "
                f"(({_cross_equality(first)}) /\\ ({_cross_equality(second)}))",
                (FOUR_SQUARE_EULER_CROSS_SWAP,),
                tuple(script),
                f"The two mixed Hamilton products for the {name[-2:]} left-coordinate pair cancel exactly.",
            )
        )

    aggregate_inputs = tuple(
        coordinate for index in range(4) for coordinate in (f"p{index}", f"n{index}", f"m{index}")
    )
    abstract_positive = tuple(f"p{index}" for index in range(4))
    abstract_negative = tuple(f"n{index}" for index in range(4))
    abstract_magnitude = tuple(f"m{index}" for index in range(4))
    abstract_balances, abstract_left, abstract_square, abstract_cross = (
        _coordinate_balance_surface(
            abstract_positive, abstract_negative, abstract_magnitude
        )
    )

    contributions = _coordinate_contributions()
    positive = tuple(point[0] for point in contributions)
    negative = tuple(point[1] for point in contributions)
    magnitude = tuple(f"m{index}" for index in range(4))
    actual_balances, actual_left, actual_square, actual_cross = (
        _coordinate_balance_surface(positive, negative, magnitude)
    )
    absolute = tuple(
        _absolute_expression(p, n, m)
        for p, n, m in zip(positive, negative, magnitude, strict=True)
    )
    square_balances = tuple(
        _square_balance_expression(p, n, m)
        for p, n, m in zip(positive, negative, magnitude, strict=True)
    )
    norm = (
        "(a * a + b * b + c * c + d * d) * "
        "(e * e + f * f + g * g + h * h)"
    )
    row_block = lambda variable: (
        f"({variable} * e) * ({variable} * e) + "
        f"({variable} * f) * ({variable} * f) + "
        f"({variable} * g) * ({variable} * g) + "
        f"({variable} * h) * ({variable} * h)"
    )
    diagonal = " + ".join(f"({row_block(variable)})" for variable in "abcd")

    all_pair_script: list[str] = list(introductions)
    for index, (name, _, _) in enumerate(_MIXED_PAIRS):
        if index < len(_MIXED_PAIRS) - 1:
            all_pair_script.append("split")
        all_pair_script.extend(f"specialize {name} {value}" for value in inputs)
        all_pair_script.append(f"exact {name}")

    aggregate_script = tuple(f"intro {variable}" for variable in aggregate_inputs)
    aggregate_script += tuple(f"intro h{index}" for index in range(4))
    aggregate_script += tuple(f"rewrite h{index}" for index in range(4))
    aggregate_script += ("apply four_square_euler_four_add_shuffle",)

    cancellation_script: list[str] = ["intro norm"]
    cancellation_script.extend(f"intro {variable}" for variable in aggregate_inputs)
    cancellation_script.extend(f"intro h{index}" for index in range(4))
    cancellation_script.append("intro hcompensation")
    cancellation_script.extend(
        (
            f"have hgroup : ({abstract_left}) = "
            f"(({abstract_square}) + ({abstract_cross}))",
        )
    )
    cancellation_script.extend(
        f"specialize four_square_euler_balance_aggregate {variable}"
        for variable in aggregate_inputs
    )
    cancellation_script.append("apply four_square_euler_balance_aggregate")
    cancellation_script.extend(f"exact h{index}" for index in range(4))
    cancellation_script.extend(
        (
            "specialize add_right_cancel norm",
            f"specialize add_right_cancel ({abstract_square})",
            f"specialize add_right_cancel ({abstract_cross})",
            "apply add_right_cancel",
            f"trans {abstract_left}",
            "exact hcompensation",
            "exact hgroup",
        )
    )

    conditional_script: list[str] = list(introductions)
    conditional_script.extend(f"intro {value}" for value in magnitude)
    conditional_script.extend(("intro habsolute", "intro hcompensation"))
    conditional_script.append(f"have hbalances : ({_conjunction(square_balances)})")
    conditional_script.extend(
        f"specialize quaternion_coordinate_square_transport {variable}"
        for variable in (*inputs, *magnitude)
    )
    conditional_script.extend(
        (
            "apply quaternion_coordinate_square_transport",
            "exact habsolute",
            "cases hbalances",
            "cases hbalances_right",
            "cases hbalances_right_right",
            f"trans {actual_square}",
            f"specialize four_square_euler_compensation_cancel ({norm})",
        )
    )
    for p, n, m in zip(positive, negative, magnitude, strict=True):
        conditional_script.extend(
            (
                f"specialize four_square_euler_compensation_cancel ({p})",
                f"specialize four_square_euler_compensation_cancel ({n})",
                f"specialize four_square_euler_compensation_cancel {m}",
            )
        )
    conditional_script.extend(
        (
            "apply four_square_euler_compensation_cancel",
            "exact hbalances_left",
            "exact hbalances_right_left",
            "exact hbalances_right_right_left",
            "exact hbalances_right_right_right",
            "exact hcompensation",
            "symm",
            "apply add_assoc",
        )
    )

    six_variables = tuple(f"u{index}" for index in range(6))
    six_target = tuple(six_variables[index] for index in (0, 3, 1, 4, 2, 5))
    six_source_surface = _left_group(
        (_left_group(six_variables[:3]), _left_group(six_variables[3:]))
    )
    six_target_surface = _left_group(
        tuple(_left_group(six_target[index : index + 2]) for index in (0, 2, 4))
    )

    nine_variables = tuple(f"u{index}" for index in range(9))
    nine_target = tuple(
        nine_variables[index] for index in (0, 4, 8, 3, 1, 6, 2, 7, 5)
    )
    nine_source_surface = _left_group(
        tuple(_left_group(nine_variables[index : index + 3]) for index in (0, 3, 6))
    )
    nine_target_surface = _left_group(
        (
            _left_group(nine_target[:3]),
            _left_group(
                tuple(_left_group(nine_target[index : index + 2]) for index in (3, 5, 7))
            ),
        )
    )

    twelve_variables = tuple(f"u{index}" for index in range(12))
    twelve_target = tuple(
        twelve_variables[index]
        for index in (3, 6, 10, 7, 11, 2, 9, 5, 1, 4, 0, 8)
    )
    twelve_source_surface = _four_grouped(
        tuple(_left_group(twelve_variables[index : index + 3]) for index in (0, 3, 6, 9))
    )
    twelve_target_surface = _four_grouped(
        tuple(_left_group(twelve_target[index : index + 3]) for index in (0, 3, 6, 9))
    )

    sixteen_variables = tuple(f"u{index}" for index in range(16))
    sixteen_target = tuple(
        sixteen_variables[index]
        for index in (0, 4, 8, 12, 5, 1, 13, 11, 9, 15, 2, 6, 14, 10, 7, 3)
    )
    sixteen_source_surface = _four_grouped(
        (
            _left_group(
                (sixteen_variables[0], _left_group(sixteen_variables[1:4]))
            ),
            _left_group(sixteen_variables[4:8]),
            _left_group(sixteen_variables[8:12]),
            _left_group(sixteen_variables[12:16]),
        )
    )
    sixteen_target_surface = _left_group(
        tuple(_left_group(sixteen_target[index : index + 4]) for index in (0, 4, 8, 12))
    )

    triple_diagonal = _left_group(("x * x", "y * y", "z * z"))
    triple_mixed = _left_group(
        (
            _left_group(("x * y", "y * x")),
            _left_group(("x * z", "z * x")),
            _left_group(("y * z", "z * y")),
        )
    )
    cross_triple = _left_group(
        (
            _left_group(("u * x", "x * u")),
            _left_group(("u * y", "y * u")),
            _left_group(("u * z", "z * u")),
        )
    )

    singleton_atoms = ("a * e", "d * g", "b * h", "c * f")
    triple_atoms = (
        ("b * f", "c * g", "d * h"),
        ("a * f", "b * e", "c * h"),
        ("a * g", "c * e", "d * f"),
        ("a * h", "b * g", "d * e"),
    )
    mixed_pairs = tuple(
        tuple(
            _symmetric_product(atoms[first], atoms[second])
            for first, second in ((0, 1), (0, 2), (1, 2))
        )
        for atoms in triple_atoms
    )
    mixed_groups = tuple(_left_group(block) for block in mixed_pairs)
    coordinate_diagonals = tuple(
        _left_group((_squared(singleton), _left_group(tuple(_squared(atom) for atom in atoms))))
        if index == 0
        else _left_group((_left_group(tuple(_squared(atom) for atom in atoms)), _squared(singleton)))
        for index, (singleton, atoms) in enumerate(
            zip(singleton_atoms, triple_atoms, strict=True)
        )
    )
    grouped_diagonals = _four_grouped(coordinate_diagonals)
    grouped_mixed = _four_grouped(mixed_groups)
    coordinate_decompositions = _four_grouped(
        tuple(
            _left_group((diagonal_block, mixed_block))
            for diagonal_block, mixed_block in zip(
                coordinate_diagonals, mixed_groups, strict=True
            )
        )
    )

    canonical_cross_pairs = (
        (("a * e", "b * f"), ("a * e", "c * g"), ("a * e", "d * h")),
        (("a * f", "d * g"), ("b * e", "d * g"), ("c * h", "d * g")),
        (("a * g", "b * h"), ("b * h", "c * e"), ("b * h", "d * f")),
        (("a * h", "c * f"), ("b * g", "c * f"), ("c * f", "d * e")),
    )
    canonical_cross_blocks = tuple(
        tuple(_symmetric_product(first, second) for first, second in pairs)
        for pairs in canonical_cross_pairs
    )
    grouped_cross = _four_grouped(
        tuple(_left_group(blocks) for blocks in canonical_cross_blocks)
    )

    swapped_blocks = tuple(
        tuple(
            _cross_swapped_pair(atoms[first], atoms[second])
            for first, second in ((0, 1), (0, 2), (1, 2))
        )
        for atoms in triple_atoms
    )
    flattened_swapped = tuple(block for group in swapped_blocks for block in group)
    flattened_cross = tuple(
        block for group in canonical_cross_blocks for block in group
    )
    if tuple(
        flattened_swapped[index]
        for index in (3, 6, 10, 7, 11, 2, 9, 5, 1, 4, 0, 8)
    ) != flattened_cross:
        raise AssertionError("Hamilton cross blocks changed their pinned permutation")
    grouped_swapped = _four_grouped(
        tuple(_left_group(blocks) for blocks in swapped_blocks)
    )

    left_decomposition_script = introductions + (
        f"trans {coordinate_decompositions}",
        "congr",
        "congr",
        "apply four_square_euler_coordinate_single_decompose",
        "apply four_square_euler_coordinate_triple_decompose",
        "congr",
        "apply four_square_euler_coordinate_triple_decompose",
        "apply four_square_euler_coordinate_triple_decompose",
        "apply four_square_euler_four_add_shuffle",
    )

    def cross_branch(index: int, reversed_pairs: tuple[bool, bool, bool]) -> list[str]:
        singleton = singleton_atoms[index]
        atoms = triple_atoms[index]
        triple = _left_group(atoms)
        single_first = f"({singleton}) * ({triple}) + ({triple}) * ({singleton})"
        all_single_first = _left_group(
            tuple(_symmetric_product(singleton, atom) for atom in atoms)
        )
        commands: list[str] = []
        if index != 0:
            commands.extend((f"trans {single_first}", "apply add_comm"))
        commands.extend(
            (
                f"trans {all_single_first}",
                "apply four_square_euler_cross_triple_expansion",
                "congr",
                "congr",
            )
        )
        commands.extend(
            "apply add_comm" if reverse else "refl" for reverse in reversed_pairs
        )
        return commands

    cross_decomposition_script = list(introductions)
    cross_decomposition_script.extend(("congr", "congr"))
    cross_decomposition_script.extend(cross_branch(0, (False, False, False)))
    cross_decomposition_script.extend(cross_branch(1, (True, True, True)))
    cross_decomposition_script.append("congr")
    cross_decomposition_script.extend(cross_branch(2, (True, False, False)))
    cross_decomposition_script.extend(cross_branch(3, (True, True, False)))

    mixed_decomposition_script = list(introductions)
    mixed_decomposition_script.append(f"trans {grouped_swapped}")
    mixed_decomposition_script.extend(("congr", "congr"))
    for index in range(4):
        if index == 2:
            mixed_decomposition_script.append("congr")
        mixed_decomposition_script.extend(
            (
                "congr",
                "congr",
                "apply four_square_euler_double_cross_swap",
                "apply four_square_euler_double_cross_swap",
                "apply four_square_euler_double_cross_swap",
            )
        )
    mixed_decomposition_script.append("apply four_square_euler_add_permute_twelve")

    return (
        spec(
            FOUR_SQUARE_EULER_CROSS_SWAP,
            "forall a b c d. (a * b) * (c * d) = (a * d) * (c * b)",
            ("mul_shuffle_four", "mul_comm"),
            (
                "intro a", "intro b", "intro c", "intro d",
                "trans (a * c) * (b * d)",
                "apply mul_shuffle_four",
                "trans (a * c) * (d * b)",
                "congr", "refl", "apply mul_comm",
                "symm", "apply mul_shuffle_four",
            ),
            "Two products with fixed outer factors exchange their crossed middle factors.",
        ),
        *pair_rows,
        spec(
            FOUR_SQUARE_EULER_ALL_MIXED_CANCEL,
            f"forall {' '.join(inputs)}. ({_conjunction(pair_formulas)})",
            tuple(name for name, _, _ in _MIXED_PAIRS),
            tuple(all_pair_script),
            "All twelve mixed Hamilton-coordinate products cancel in six separately witnessed coordinate-pair blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
            "forall a b c d e f g h. "
            "((a + b) + (c + d)) + ((e + f) + (g + h)) = "
            "((a + c) + (e + g)) + ((b + d) + (f + h))",
            ("add_shuffle_middle",),
            (
                "intro a", "intro b", "intro c", "intro d",
                "intro e", "intro f", "intro g", "intro h",
                "trans ((a + c) + (b + d)) + ((e + g) + (f + h))",
                "congr", "apply add_shuffle_middle", "apply add_shuffle_middle",
                "apply add_shuffle_middle",
            ),
            "Eight additive terms are transposed as four independent magnitude/cross-term pairs.",
        ),
        spec(
            FOUR_SQUARE_EULER_BALANCE_AGGREGATE,
            f"forall {' '.join(aggregate_inputs)}. "
            + " -> ".join(f"({balance})" for balance in abstract_balances)
            + f" -> ({abstract_left}) = (({abstract_square}) + ({abstract_cross}))",
            (FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,),
            aggregate_script,
            "Four exact signed-coordinate square balances aggregate into the sum of their natural squares plus their full cross correction.",
        ),
        spec(
            FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
            f"forall norm {' '.join(aggregate_inputs)}. "
            + " -> ".join(f"({balance})" for balance in abstract_balances)
            + f" -> ((norm) + ({abstract_cross}) = ({abstract_left})) "
            + f"-> norm = ({abstract_square})",
            (FOUR_SQUARE_EULER_BALANCE_AGGREGATE, "add_right_cancel"),
            tuple(cancellation_script),
            "Ordinary constructive additive cancellation turns all four signed cross corrections into an exact norm identity.",
        ),
        spec(
            FOUR_SQUARE_EULER_DIAGONAL_BLOCK,
            "forall a e f g h. "
            "(a * a) * (e * e + f * f + g * g + h * h) = "
            + row_block("a"),
            ("mul_add", FOUR_SQUARE_PRODUCT_SQUARE),
            (
                "intro a", "intro e", "intro f", "intro g", "intro h",
                "simp [mul_add]",
                "congr", "congr", "congr",
                "symm", "apply four_square_product_square",
                "symm", "apply four_square_product_square",
                "symm", "apply four_square_product_square",
                "symm", "apply four_square_product_square",
            ),
            "One left coordinate distributes into the four exact squared coordinate products of a quaternion norm.",
        ),
        spec(
            FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
            f"forall {' '.join(inputs)}. {norm} = {diagonal}",
            (FOUR_SQUARE_NORM_DISTRIBUTES, FOUR_SQUARE_EULER_DIAGONAL_BLOCK),
            introductions
            + (
                "specialize four_square_norm_distributes a",
                "specialize four_square_norm_distributes b",
                "specialize four_square_norm_distributes c",
                "specialize four_square_norm_distributes d",
                "specialize four_square_norm_distributes e",
                "specialize four_square_norm_distributes f",
                "specialize four_square_norm_distributes g",
                "specialize four_square_norm_distributes h",
                "rewrite four_square_norm_distributes",
                "congr", "congr", "congr",
                "apply four_square_euler_diagonal_block",
                "apply four_square_euler_diagonal_block",
                "apply four_square_euler_diagonal_block",
                "apply four_square_euler_diagonal_block",
            ),
            "The complete eight-variable quaternion norm product expands into exactly its sixteen squared coordinate products.",
        ),
        spec(
            FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL,
            f"forall {' '.join(inputs)} {' '.join(magnitude)}. "
            f"({_conjunction(absolute)}) -> "
            f"(({norm}) + ({actual_cross}) = ({actual_left})) -> "
            f"({norm}) = "
            "m0 * m0 + m1 * m1 + m2 * m2 + m3 * m3",
            (
                QUATERNION_COORDINATE_SQUARE_TRANSPORT,
                FOUR_SQUARE_EULER_COMPENSATION_CANCEL,
                "add_assoc",
            ),
            tuple(conditional_script),
            "The exact eight-variable quaternion Euler identity follows constructively from its one remaining subtraction-free global compensation equality.",
        ),
        spec(
            FOUR_SQUARE_EULER_ADD_PERMUTE_SIX,
            f"forall {' '.join(six_variables)}. "
            f"({six_source_surface}) = ({six_target_surface})",
            ("add_assoc", "add_comm", FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL),
            _permutation_script(six_variables, six_target),
            "Six abstract additive entries are paired by a bounded explicit adjacent-swap proof.",
        ),
        spec(
            FOUR_SQUARE_EULER_ADD_PERMUTE_NINE,
            f"forall {' '.join(nine_variables)}. "
            f"({nine_source_surface}) = ({nine_target_surface})",
            ("add_assoc", "add_comm", FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL),
            _permutation_script(nine_variables, nine_target),
            "A three-by-three square expansion separates its diagonal and its six ordered mixed products.",
        ),
        spec(
            FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE,
            f"forall {' '.join(twelve_variables)}. "
            f"({twelve_source_surface}) = ({twelve_target_surface})",
            ("add_assoc", "add_comm", FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL),
            _permutation_script(twelve_variables, twelve_target),
            "The twelve paired Hamilton mixed blocks are placed in their four signed-coordinate correction groups.",
        ),
        spec(
            FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN,
            f"forall {' '.join(sixteen_variables)}. "
            f"({sixteen_source_surface}) = ({sixteen_target_surface})",
            ("add_assoc", "add_comm", FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL),
            _permutation_script(sixteen_variables, sixteen_target),
            "All sixteen Hamilton diagonal squares transpose from coordinate order into row-major norm order.",
        ),
        spec(
            FOUR_SQUARE_EULER_ADD_SWAP_LAST,
            "forall a b c. (a + b) + c = (a + c) + b",
            ("add_assoc", "add_comm"),
            (
                "intro a",
                "intro b",
                "intro c",
                "trans a + (b + c)",
                "apply add_assoc",
                "trans a + (c + b)",
                "congr",
                "refl",
                "apply add_comm",
                "symm",
                "apply add_assoc",
            ),
            "Two final additive entries exchange places while their common first entry is preserved.",
        ),
        spec(
            FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION,
            "forall x y z. "
            "(x + y + z) * (x + y + z) = "
            f"({triple_diagonal}) + ({triple_mixed})",
            ("mul_add", "add_mul", FOUR_SQUARE_EULER_ADD_PERMUTE_NINE),
            (
                "intro x",
                "intro y",
                "intro z",
                "trans (x * x + y * x + z * x) + "
                "(x * y + y * y + z * y) + "
                "(x * z + y * z + z * z)",
                "simp [mul_add, add_mul]",
                "apply four_square_euler_add_permute_nine",
            ),
            "A three-term natural square expands into three diagonal squares and three explicitly paired mixed blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION,
            "forall u x y z. "
            "u * (x + y + z) + (x + y + z) * u = "
            f"{cross_triple}",
            ("mul_add", "add_mul", FOUR_SQUARE_EULER_ADD_PERMUTE_SIX),
            (
                "intro u",
                "intro x",
                "intro y",
                "intro z",
                "trans (u * x + u * y + u * z) + "
                "(x * u + y * u + z * u)",
                "simp [mul_add, add_mul]",
                "apply four_square_euler_add_permute_six",
            ),
            "The two ordered products of one entry with a three-entry sum split into three exact symmetric pairs.",
        ),
        spec(
            FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
            "forall a b c d. "
            "((a * b) * (c * d) + (c * d) * (a * b)) = "
            "((a * d) * (c * b) + (c * b) * (a * d))",
            (FOUR_SQUARE_EULER_CROSS_SWAP,),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "congr",
                "apply four_square_euler_cross_swap",
                "apply four_square_euler_cross_swap",
            ),
            "Both ordered occurrences of a mixed Hamilton product exchange their crossed right-hand factors constructively.",
        ),
        spec(
            FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE,
            "forall w x y z. "
            "w * w + (x + y + z) * (x + y + z) = "
            f"(w * w + ({triple_diagonal})) + ({triple_mixed})",
            (FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION, "add_assoc"),
            (
                "intro w",
                "intro x",
                "intro y",
                "intro z",
                f"trans w * w + (({triple_diagonal}) + ({triple_mixed}))",
                "congr",
                "refl",
                "apply four_square_euler_three_square_expansion",
                "symm",
                "apply add_assoc",
            ),
            "A singleton-square plus a triple-square decomposes into its four diagonal squares and three paired cross blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE,
            "forall w x y z. "
            "(x + y + z) * (x + y + z) + w * w = "
            f"(({triple_diagonal}) + w * w) + ({triple_mixed})",
            (
                FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION,
                FOUR_SQUARE_EULER_ADD_SWAP_LAST,
            ),
            (
                "intro w",
                "intro x",
                "intro y",
                "intro z",
                f"trans (({triple_diagonal}) + ({triple_mixed})) + w * w",
                "congr",
                "apply four_square_euler_three_square_expansion",
                "refl",
                "apply four_square_euler_add_swap_last",
            ),
            "A triple-square plus a singleton-square decomposes into its four diagonal squares and three paired cross blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_DIAGONAL_REGROUP,
            f"forall {' '.join(inputs)}. ({grouped_diagonals}) = ({diagonal})",
            (FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN,),
            introductions + ("apply four_square_euler_add_permute_sixteen",),
            "The sixteen exact Hamilton-coordinate diagonal squares are the sixteen row-major norm-product squares.",
        ),
        spec(
            FOUR_SQUARE_EULER_LEFT_DECOMPOSITION,
            f"forall {' '.join(inputs)}. "
            f"({actual_left}) = (({grouped_diagonals}) + ({grouped_mixed}))",
            (
                FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE,
                FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE,
                FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE,
            ),
            left_decomposition_script,
            "All eight positive/negative Hamilton-coordinate squares split exactly into sixteen diagonal squares plus twelve paired mixed blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_CROSS_DECOMPOSITION,
            f"forall {' '.join(inputs)}. ({actual_cross}) = ({grouped_cross})",
            (FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION, "add_comm"),
            tuple(cross_decomposition_script),
            "The complete four-coordinate signed correction splits into its twelve exact symmetric mixed-product blocks.",
        ),
        spec(
            FOUR_SQUARE_EULER_MIXED_DECOMPOSITION,
            f"forall {' '.join(inputs)}. ({grouped_mixed}) = ({grouped_cross})",
            (
                FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP,
                FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE,
            ),
            tuple(mixed_decomposition_script),
            "All twelve same-sign Hamilton mixed blocks become the twelve opposite-sign correction blocks by explicit crossed-factor swaps.",
        ),
        spec(
            FOUR_SQUARE_EULER_GLOBAL_COMPENSATION,
            f"forall {' '.join(inputs)}. "
            f"(({norm}) + ({actual_cross})) = ({actual_left})",
            (
                FOUR_SQUARE_EULER_DIAGONAL_EXPANSION,
                FOUR_SQUARE_EULER_DIAGONAL_REGROUP,
                FOUR_SQUARE_EULER_CROSS_DECOMPOSITION,
                FOUR_SQUARE_EULER_MIXED_DECOMPOSITION,
                FOUR_SQUARE_EULER_LEFT_DECOMPOSITION,
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
                "apply four_square_euler_diagonal_regroup",
                "refl",
                f"trans ({grouped_diagonals}) + ({grouped_cross})",
                "congr",
                "refl",
                "apply four_square_euler_cross_decomposition",
                f"trans ({grouped_diagonals}) + ({grouped_mixed})",
                "congr",
                "refl",
                "symm",
                "apply four_square_euler_mixed_decomposition",
                "symm",
                "apply four_square_euler_left_decomposition",
            ),
            "The exact previously missing global subtraction-free Hamilton compensation equation is proved without any remaining premise.",
        ),
        spec(
            FOUR_SQUARE_EULER_QUATERNION,
            f"forall {' '.join(inputs)} {' '.join(magnitude)}. "
            f"({_conjunction(absolute)}) -> "
            f"({norm}) = "
            "m0 * m0 + m1 * m1 + m2 * m2 + m3 * m3",
            (
                FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL,
                FOUR_SQUARE_EULER_GLOBAL_COMPENSATION,
            ),
            introductions
            + tuple(f"intro {value}" for value in magnitude)
            + ("intro habsolute",)
            + tuple(
                f"specialize four_square_euler_quaternion_conditional {value}"
                for value in (*inputs, *magnitude)
            )
            + (
                "apply four_square_euler_quaternion_conditional",
                "exact habsolute",
                "apply four_square_euler_global_compensation",
            ),
            "Euler's complete eight-variable quaternion four-square identity holds unconditionally for all constructively chosen natural absolute coordinates.",
        ),
        spec(
            FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL,
            f"forall {' '.join(inputs)}. exists m0 m1 m2 m3. "
            f"({norm}) = "
            "m0 * m0 + m1 * m1 + m2 * m2 + m3 * m3",
            (
                QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
                FOUR_SQUARE_EULER_QUATERNION,
            ),
            introductions
            + tuple(
                f"specialize quaternion_coordinate_absolute_total {value}"
                for value in inputs
            )
            + (
                "cases quaternion_coordinate_absolute_total",
                "cases quaternion_coordinate_absolute_total_witness",
                "cases quaternion_coordinate_absolute_total_witness_witness",
                "cases quaternion_coordinate_absolute_total_witness_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "apply four_square_euler_quaternion",
                "exact quaternion_coordinate_absolute_total_witness_witness_witness_witness",
            ),
            "Every product of two arbitrary four-square natural norms has four explicitly constructed natural-square witnesses.",
        ),
        spec(
            FOUR_SQUARE_EULER_REPRESENTATIONS_CLOSED_UNDER_MULTIPLICATION,
            "forall n m. "
            "(exists a b c d. n = a * a + b * b + c * c + d * d) -> "
            "(exists e f g h. m = e * e + f * f + g * g + h * h) -> "
            "exists u v w x. n * m = u * u + v * v + w * w + x * x",
            (FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL,),
            (
                "intro n",
                "intro m",
                "intro hn",
                "intro hm",
                "cases hn",
                "cases hn_witness",
                "cases hn_witness_witness",
                "cases hn_witness_witness_witness",
                "cases hm",
                "cases hm_witness",
                "cases hm_witness_witness",
                "cases hm_witness_witness_witness",
                "rewrite hn_witness_witness_witness_witness",
                "rewrite hm_witness_witness_witness_witness",
                "apply four_square_euler_four_square_product_total",
            ),
            "The class of constructively represented natural sums of four squares is closed under multiplication without any sign or compensation hypothesis.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_EULER_ALL_MIXED_CANCEL",
    "FOUR_SQUARE_EULER_ADD_PERMUTE_NINE",
    "FOUR_SQUARE_EULER_ADD_PERMUTE_SIX",
    "FOUR_SQUARE_EULER_ADD_PERMUTE_SIXTEEN",
    "FOUR_SQUARE_EULER_ADD_PERMUTE_TWELVE",
    "FOUR_SQUARE_EULER_ADD_SWAP_LAST",
    "FOUR_SQUARE_EULER_BALANCE_AGGREGATE",
    "FOUR_SQUARE_EULER_COMPENSATION_CANCEL",
    "FOUR_SQUARE_EULER_COORDINATE_SINGLE_DECOMPOSE",
    "FOUR_SQUARE_EULER_COORDINATE_TRIPLE_DECOMPOSE",
    "FOUR_SQUARE_EULER_CROSS_DECOMPOSITION",
    "FOUR_SQUARE_EULER_CROSS_TRIPLE_EXPANSION",
    "FOUR_SQUARE_EULER_CROSS_SWAP",
    "FOUR_SQUARE_EULER_DIAGONAL_BLOCK",
    "FOUR_SQUARE_EULER_DIAGONAL_EXPANSION",
    "FOUR_SQUARE_EULER_DIAGONAL_REGROUP",
    "FOUR_SQUARE_EULER_DOUBLE_CROSS_SWAP",
    "FOUR_SQUARE_EULER_FOUR_ADD_SHUFFLE",
    "FOUR_SQUARE_EULER_FOUR_SQUARE_PRODUCT_TOTAL",
    "FOUR_SQUARE_EULER_GLOBAL_COMPENSATION",
    "FOUR_SQUARE_EULER_LEFT_DECOMPOSITION",
    "FOUR_SQUARE_EULER_MIXED_AB",
    "FOUR_SQUARE_EULER_MIXED_AC",
    "FOUR_SQUARE_EULER_MIXED_AD",
    "FOUR_SQUARE_EULER_MIXED_BC",
    "FOUR_SQUARE_EULER_MIXED_BD",
    "FOUR_SQUARE_EULER_MIXED_CD",
    "FOUR_SQUARE_EULER_MIXED_DECOMPOSITION",
    "FOUR_SQUARE_EULER_QUATERNION",
    "FOUR_SQUARE_EULER_QUATERNION_CONDITIONAL",
    "FOUR_SQUARE_EULER_REPRESENTATIONS_CLOSED_UNDER_MULTIPLICATION",
    "FOUR_SQUARE_EULER_THREE_SQUARE_EXPANSION",
    "make_four_square_euler_candidate_theorems",
]
