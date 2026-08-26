"""Constructive, subtraction-free prerequisites for Euler's four-square identity.

Quaternion coordinates may be negative even when all eight input coordinates
are natural.  The canonical signed-natural ``SignedBalance`` graph therefore
supplies the four coordinates; its normalized decoder supplies their natural
absolute magnitudes.  All relation names here are authoring abbreviations
expanded into the unchanged first-order language ``{0,S,+,*,=}``.

These isolated, dependency-curried candidates do not establish Euler's full
norm identity or Lagrange's theorem and grant no Alpha/Stable authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_signed_balance_candidate import signed_balance
from .ha_signed_decode_candidate import signed_decode


SIGNED_SQUARE_CROSS_TERM_ZERO = "signed_square_cross_term_zero"
SIGNED_SQUARE_MAGNITUDE_EXPANDS = "signed_square_magnitude_expands"
SIGNED_BALANCE_ABSOLUTE_EXISTS = "signed_balance_absolute_exists"
FOUR_SQUARE_NORM_DISTRIBUTES = "four_square_norm_distributes"
QUATERNION_COORDINATE_BALANCE_TOTAL = "quaternion_coordinate_balance_total"
QUATERNION_COORDINATE_ABSOLUTE_TOTAL = "quaternion_coordinate_absolute_total"
FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL = "four_square_add_swap_right_tail"
FOUR_SQUARE_ADDITIVE_GAP_REORDER = "four_square_additive_gap_reorder"
FOUR_SQUARE_SUM_EXPANSION = "four_square_sum_expansion"
FOUR_SQUARE_GAP_BALANCE_RIGHT = "four_square_gap_balance_right"
FOUR_SQUARE_GAP_BALANCE_LEFT = "four_square_gap_balance_left"
FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE = "four_square_absolute_square_balance"
SIGNED_BALANCE_SQUARE_TRANSPORT = "signed_balance_square_transport"
FOUR_SQUARE_PRODUCT_SHUFFLE = "four_square_product_shuffle"
FOUR_SQUARE_PRODUCT_SQUARE = "four_square_product_square"
QUATERNION_COORDINATE_SQUARE_TRANSPORT = "quaternion_coordinate_square_transport"
QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL = (
    "quaternion_coordinate_square_balance_total"
)
FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL = "four_square_absolute_difference_total"
FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY = "four_square_two_square_factor_identity"
FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL = "four_square_two_square_factor_total"


def _balance_expression(code: str, positive: str, negative: str, *, tag: str) -> str:
    """Expand canonical ``SignedBalance`` while accepting compound terms."""

    positive_marker = f"fs_positive_marker_{tag}"
    negative_marker = f"fs_negative_marker_{tag}"
    if positive_marker in positive or negative_marker in negative:
        raise ValueError("four-square balance marker collides with its expression")
    expanded = signed_balance(code, positive_marker, negative_marker, tag=tag)
    if expanded.count(positive_marker) != 1 or expanded.count(negative_marker) != 1:
        raise AssertionError("unexpected SignedBalance argument occurrence count")
    return expanded.replace(positive_marker, f"({positive})").replace(
        negative_marker, f"({negative})"
    )


def _coordinate_contributions() -> tuple[tuple[str, str], ...]:
    """Return the exact positive/negative Hamilton-product contributions."""

    return (
        ("a * e", "b * f + c * g + d * h"),
        ("a * f + b * e + c * h", "d * g"),
        ("a * g + c * e + d * f", "b * h"),
        ("a * h + b * g + d * e", "c * f"),
    )


def _conjunction(parts: tuple[str, ...]) -> str:
    result = parts[-1]
    for part in reversed(parts[:-1]):
        result = f"({part}) /\\ ({result})"
    return result


def _absolute_expression(positive: str, negative: str, magnitude: str) -> str:
    return (
        f"(({positive}) = ({negative}) + {magnitude}) \\/ "
        f"(({negative}) = ({positive}) + {magnitude})"
    )


def _square_balance_expression(
    positive: str, negative: str, magnitude: str
) -> str:
    return (
        f"({positive}) * ({positive}) + ({negative}) * ({negative}) = "
        f"{magnitude} * {magnitude} + "
        f"(({positive}) * ({negative}) + ({negative}) * ({positive}))"
    )


def make_four_square_identity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the bounded signed-coordinate and norm-expansion foundations."""

    decoded_cross = signed_decode("code", "pos", "neg", tag="fs_cross")
    decoded_square = signed_decode("code", "pos", "neg", tag="fs_square")
    balanced_absolute = signed_balance("code", "left", "right", tag="fs_abs")
    contributions = _coordinate_contributions()
    balances = tuple(
        _balance_expression(f"q{index}", positive, negative, tag=f"fs_q{index}")
        for index, (positive, negative) in enumerate(contributions)
    )
    magnitudes = tuple(
        _absolute_expression(positive, negative, f"m{index}")
        for index, (positive, negative) in enumerate(contributions)
    )
    square_balances = tuple(
        _square_balance_expression(positive, negative, f"m{index}")
        for index, (positive, negative) in enumerate(contributions)
    )
    inputs = "a b c d e f g h"
    introductions = tuple(f"intro {variable}" for variable in inputs.split())
    right_norm = "e * e + f * f + g * g + h * h"
    expanded_norm = " + ".join(
        f"({left} * {left}) * ({right_norm})" for left in "abcd"
    )

    coordinate_script: list[str] = list(introductions)
    for index, (positive, negative) in enumerate(contributions):
        coordinate_script.extend(
            (
                f"have h{index} : exists q{index}. ({balances[index]})",
                f"specialize signed_balance_total ({positive})",
                f"specialize signed_balance_total ({negative})",
                "exact signed_balance_total",
            )
        )
    coordinate_script.extend(f"cases h{index}" for index in range(4))
    coordinate_script.extend(f"exists {'x' if index == 0 else 'x' + str(index)}" for index in range(4))
    for index in range(3):
        coordinate_script.extend(("split", f"exact h{index}_witness"))
    coordinate_script.append("exact h3_witness")

    absolute_script: list[str] = list(introductions)
    absolute_script.extend(
        (
            "specialize quaternion_coordinate_balance_total a",
            "specialize quaternion_coordinate_balance_total b",
            "specialize quaternion_coordinate_balance_total c",
            "specialize quaternion_coordinate_balance_total d",
            "specialize quaternion_coordinate_balance_total e",
            "specialize quaternion_coordinate_balance_total f",
            "specialize quaternion_coordinate_balance_total g",
            "specialize quaternion_coordinate_balance_total h",
            "cases quaternion_coordinate_balance_total",
            "cases quaternion_coordinate_balance_total_witness",
            "cases quaternion_coordinate_balance_total_witness_witness",
            "cases quaternion_coordinate_balance_total_witness_witness_witness",
            "cases quaternion_coordinate_balance_total_witness_witness_witness_witness",
            "cases quaternion_coordinate_balance_total_witness_witness_witness_witness_right",
            "cases quaternion_coordinate_balance_total_witness_witness_witness_witness_right_right",
        )
    )
    hypothesis_names = (
        "quaternion_coordinate_balance_total_witness_witness_witness_witness_left",
        "quaternion_coordinate_balance_total_witness_witness_witness_witness_right_left",
        "quaternion_coordinate_balance_total_witness_witness_witness_witness_right_right_left",
        "quaternion_coordinate_balance_total_witness_witness_witness_witness_right_right_right",
    )
    for index, (positive, negative) in enumerate(contributions):
        coordinate = "x" if index == 0 else f"x{index}"
        absolute_script.extend(
            (
                f"have hm{index} : exists m{index}. ({magnitudes[index]})",
                f"specialize signed_balance_absolute_exists {coordinate}",
                f"specialize signed_balance_absolute_exists ({positive})",
                f"specialize signed_balance_absolute_exists ({negative})",
                "apply signed_balance_absolute_exists",
                f"exact {hypothesis_names[index]}",
            )
        )
    absolute_script.extend(f"cases hm{index}" for index in range(4))
    absolute_script.extend(f"exists x{index + 4}" for index in range(4))
    for index in range(3):
        absolute_script.extend(("split", f"exact hm{index}_witness"))
    absolute_script.append("exact hm3_witness")

    return (
        spec(
            SIGNED_SQUARE_CROSS_TERM_ZERO,
            f"forall code pos neg. ({decoded_cross}) -> pos * neg = 0",
            ("signed_decode_normal", "mul_zero_left"),
            (
                "intro code",
                "intro pos",
                "intro neg",
                "intro hdecode",
                "specialize signed_decode_normal code",
                "specialize signed_decode_normal pos",
                "specialize signed_decode_normal neg",
                "have hnormal : pos = 0 \\/ neg = 0",
                "apply signed_decode_normal",
                "exact hdecode",
                "cases hnormal",
                "rewrite hnormal_left",
                "apply mul_zero_left",
                "rewrite hnormal_right",
                "apply PA5",
            ),
            "A canonical signed decoding has a zero positive/negative cross term.",
        ),
        spec(
            SIGNED_SQUARE_MAGNITUDE_EXPANDS,
            f"forall code pos neg. ({decoded_square}) -> "
            "(pos + neg) * (pos + neg) = pos * pos + neg * neg",
            ("signed_decode_normal", "mul_zero_left", "zero_add"),
            (
                "intro code",
                "intro pos",
                "intro neg",
                "intro hdecode",
                "specialize signed_decode_normal code",
                "specialize signed_decode_normal pos",
                "specialize signed_decode_normal neg",
                "have hnormal : pos = 0 \\/ neg = 0",
                "apply signed_decode_normal",
                "exact hdecode",
                "cases hnormal",
                "simp [hnormal_left, mul_zero_left, zero_add]",
                "simp [hnormal_right, mul_zero_left, zero_add]",
            ),
            "The natural magnitude of a normalized signed coordinate squares "
            "to the sum of its positive and negative component squares.",
        ),
        spec(
            SIGNED_BALANCE_ABSOLUTE_EXISTS,
            f"forall code left right. ({balanced_absolute}) -> exists magnitude. "
            "((left = right + magnitude) \\/ (right = left + magnitude))",
            ("signed_decode_normal",),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hbalance",
                "cases hbalance",
                "cases hbalance_witness",
                "cases hbalance_witness_witness",
                "specialize signed_decode_normal code",
                "specialize signed_decode_normal x",
                "specialize signed_decode_normal x1",
                "have hnormal : x = 0 \\/ x1 = 0",
                "apply signed_decode_normal",
                "exact hbalance_witness_witness_left",
                "cases hnormal",
                "exists x1",
                "right",
                "symm",
                "rewrite hnormal_left at hbalance_witness_witness_right",
                "rewrite PA3 at hbalance_witness_witness_right",
                "exact hbalance_witness_witness_right",
                "exists x",
                "left",
                "rewrite hnormal_right at hbalance_witness_witness_right",
                "rewrite PA3 at hbalance_witness_witness_right",
                "exact hbalance_witness_witness_right",
            ),
            "Every canonical balanced signed coordinate has an explicit natural "
            "absolute magnitude with a constructive sign choice.",
        ),
        spec(
            FOUR_SQUARE_NORM_DISTRIBUTES,
            f"forall {inputs}. "
            "(a * a + b * b + c * c + d * d) * "
            "(e * e + f * f + g * g + h * h) = "
            f"{expanded_norm}",
            ("add_mul",),
            introductions + ("simp [add_mul]",),
            "The product of two four-square norms expands constructively into "
            "four bounded natural square-times-norm blocks.",
        ),
        spec(
            QUATERNION_COORDINATE_BALANCE_TOTAL,
            f"forall {inputs}. exists q0 q1 q2 q3. "
            f"({_conjunction(balances)})",
            ("signed_balance_total",),
            tuple(coordinate_script),
            "Hamilton's four signed product coordinates have canonical "
            "constructively chosen SignedBalance witnesses.",
        ),
        spec(
            QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
            f"forall {inputs}. exists m0 m1 m2 m3. "
            f"({_conjunction(magnitudes)})",
            (QUATERNION_COORDINATE_BALANCE_TOTAL, SIGNED_BALANCE_ABSOLUTE_EXISTS),
            tuple(absolute_script),
            "All four Hamilton-product coordinates have explicit natural "
            "absolute magnitudes and constructive sign choices.",
        ),
        spec(
            FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
            "forall a b c. a + (b + c) = b + (a + c)",
            ("add_assoc", "add_comm"),
            (
                "intro a",
                "intro b",
                "intro c",
                "trans (a + b) + c",
                "symm",
                "apply add_assoc",
                "trans (b + a) + c",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "Two adjacent natural summands exchange positions without "
            "disturbing their shared right tail.",
        ),
        spec(
            FOUR_SQUARE_ADDITIVE_GAP_REORDER,
            "forall a b c d. ((a + b) + (c + d)) + a = "
            "d + ((a + c) + (a + b))",
            (
                "add_shuffle_middle",
                "add_assoc",
                "add_comm",
                FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL,
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans ((a + c) + (b + d)) + a",
                "congr",
                "apply add_shuffle_middle",
                "refl",
                "trans (a + c) + ((b + d) + a)",
                "apply add_assoc",
                "trans (a + c) + (b + (d + a))",
                "congr",
                "refl",
                "apply add_assoc",
                "trans (a + c) + (d + (b + a))",
                "congr",
                "refl",
                "apply four_square_add_swap_right_tail",
                "trans (a + c) + (d + (a + b))",
                "congr",
                "refl",
                "congr",
                "refl",
                "apply add_comm",
                "apply four_square_add_swap_right_tail",
            ),
            "The five additive square-gap contributions reorder without "
            "subtraction or a polynomial normalizer.",
        ),
        spec(
            FOUR_SQUARE_SUM_EXPANSION,
            "forall a b. (a + b) * (a + b) = "
            "(a * a + a * b) + (b * a + b * b)",
            ("add_mul", "mul_add"),
            (
                "intro a",
                "intro b",
                "simp [add_mul, mul_add]",
            ),
            "A natural square of a sum expands to its four ordered "
            "diagonal and cross contributions.",
        ),
        spec(
            FOUR_SQUARE_GAP_BALANCE_RIGHT,
            "forall a b. (a + b) * (a + b) + a * a = "
            "b * b + ((a + b) * a + a * (a + b))",
            (
                FOUR_SQUARE_SUM_EXPANSION,
                "add_mul",
                "mul_add",
                FOUR_SQUARE_ADDITIVE_GAP_REORDER,
            ),
            (
                "intro a",
                "intro b",
                "specialize four_square_sum_expansion a",
                "specialize four_square_sum_expansion b",
                "rewrite four_square_sum_expansion",
                "specialize add_mul a",
                "specialize add_mul b",
                "specialize add_mul a",
                "rewrite add_mul",
                "specialize mul_add a",
                "specialize mul_add a",
                "specialize mul_add b",
                "rewrite mul_add",
                "apply four_square_additive_gap_reorder",
            ),
            "A larger coordinate and its base have squared sum equal to "
            "the gap square plus their two ordered cross products.",
        ),
        spec(
            FOUR_SQUARE_GAP_BALANCE_LEFT,
            "forall a b. a * a + (a + b) * (a + b) = "
            "b * b + (a * (a + b) + (a + b) * a)",
            (FOUR_SQUARE_GAP_BALANCE_RIGHT, "add_comm"),
            (
                "intro a",
                "intro b",
                "trans (a + b) * (a + b) + a * a",
                "apply add_comm",
                "trans b * b + ((a + b) * a + a * (a + b))",
                "apply four_square_gap_balance_right",
                "congr",
                "refl",
                "apply add_comm",
            ),
            "The opposite coordinate orientation has the same gap-square "
            "and ordered cross-term correction.",
        ),
        spec(
            FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,
            "forall left right magnitude. "
            "(left = right + magnitude \\/ right = left + magnitude) -> "
            "left * left + right * right = "
            "magnitude * magnitude + (left * right + right * left)",
            (FOUR_SQUARE_GAP_BALANCE_RIGHT, FOUR_SQUARE_GAP_BALANCE_LEFT),
            (
                "intro left",
                "intro right",
                "intro magnitude",
                "intro hdifference",
                "cases hdifference",
                "rewrite hdifference_left",
                "rewrite hdifference_left",
                "rewrite hdifference_left",
                "rewrite hdifference_left",
                "apply four_square_gap_balance_right",
                "rewrite hdifference_right",
                "rewrite hdifference_right",
                "rewrite hdifference_right",
                "rewrite hdifference_right",
                "apply four_square_gap_balance_left",
            ),
            "Either constructive absolute-difference branch transports "
            "coordinate squares to its magnitude square and cross correction.",
        ),
        spec(
            SIGNED_BALANCE_SQUARE_TRANSPORT,
            f"forall code left right. ({balanced_absolute}) -> "
            "exists magnitude. "
            "((left = right + magnitude \\/ right = left + magnitude) /\\ "
            "left * left + right * right = "
            "magnitude * magnitude + (left * right + right * left))",
            (SIGNED_BALANCE_ABSOLUTE_EXISTS, FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hbalance",
                "have habsolute : exists magnitude. "
                "(left = right + magnitude \\/ right = left + magnitude)",
                "specialize signed_balance_absolute_exists code",
                "specialize signed_balance_absolute_exists left",
                "specialize signed_balance_absolute_exists right",
                "apply signed_balance_absolute_exists",
                "exact hbalance",
                "cases habsolute",
                "exists x",
                "split",
                "exact habsolute_witness",
                "specialize four_square_absolute_square_balance left",
                "specialize four_square_absolute_square_balance right",
                "specialize four_square_absolute_square_balance x",
                "apply four_square_absolute_square_balance",
                "exact habsolute_witness",
            ),
            "Every canonical signed balance supplies a natural magnitude, "
            "constructive sign branch, and exact squared cross-term transport.",
        ),
        spec(
            FOUR_SQUARE_PRODUCT_SHUFFLE,
            "forall a b c d. (a * b) * (c * d) = (a * c) * (b * d)",
            ("mul_assoc", "mul_comm"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "trans a * (b * (c * d))",
                "apply mul_assoc",
                "trans a * ((b * c) * d)",
                "congr",
                "refl",
                "symm",
                "apply mul_assoc",
                "trans a * ((c * b) * d)",
                "congr",
                "refl",
                "congr",
                "apply mul_comm",
                "refl",
                "trans a * (c * (b * d))",
                "congr",
                "refl",
                "apply mul_assoc",
                "symm",
                "apply mul_assoc",
            ),
            "Two natural product factors interchange their middle terms; "
            "this is the bounded Euler cross-term cancellation primitive.",
        ),
        spec(
            FOUR_SQUARE_PRODUCT_SQUARE,
            "forall a b. (a * b) * (a * b) = (a * a) * (b * b)",
            (FOUR_SQUARE_PRODUCT_SHUFFLE,),
            (
                "intro a",
                "intro b",
                "apply four_square_product_shuffle",
            ),
            "The square of a product is the product of the two natural "
            "coordinate squares.",
        ),
        spec(
            QUATERNION_COORDINATE_SQUARE_TRANSPORT,
            f"forall {inputs} m0 m1 m2 m3. "
            f"({_conjunction(magnitudes)}) -> "
            f"({_conjunction(square_balances)})",
            (FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE,),
            introductions
            + (
                "intro m0",
                "intro m1",
                "intro m2",
                "intro m3",
                "intro hmagnitudes",
                "cases hmagnitudes",
                "cases hmagnitudes_right",
                "cases hmagnitudes_right_right",
                "split",
                "apply four_square_absolute_square_balance",
                "exact hmagnitudes_left",
                "split",
                "apply four_square_absolute_square_balance",
                "exact hmagnitudes_right_left",
                "split",
                "apply four_square_absolute_square_balance",
                "exact hmagnitudes_right_right_left",
                "apply four_square_absolute_square_balance",
                "exact hmagnitudes_right_right_right",
            ),
            "Each of the four Hamilton signed coordinates independently "
            "satisfies its exact magnitude-square/cross-term balance.",
        ),
        spec(
            QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL,
            f"forall {inputs}. exists m0 m1 m2 m3. "
            f"(({_conjunction(magnitudes)}) /\\ "
            f"({_conjunction(square_balances)}))",
            (
                QUATERNION_COORDINATE_ABSOLUTE_TOTAL,
                QUATERNION_COORDINATE_SQUARE_TRANSPORT,
            ),
            introductions
            + (
                "specialize quaternion_coordinate_absolute_total a",
                "specialize quaternion_coordinate_absolute_total b",
                "specialize quaternion_coordinate_absolute_total c",
                "specialize quaternion_coordinate_absolute_total d",
                "specialize quaternion_coordinate_absolute_total e",
                "specialize quaternion_coordinate_absolute_total f",
                "specialize quaternion_coordinate_absolute_total g",
                "specialize quaternion_coordinate_absolute_total h",
                "cases quaternion_coordinate_absolute_total",
                "cases quaternion_coordinate_absolute_total_witness",
                "cases quaternion_coordinate_absolute_total_witness_witness",
                "cases quaternion_coordinate_absolute_total_witness_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact quaternion_coordinate_absolute_total_witness_witness_witness_witness",
                "apply quaternion_coordinate_square_transport",
                "exact quaternion_coordinate_absolute_total_witness_witness_witness_witness",
            ),
            "Every Hamilton product has four explicit absolute coordinates "
            "with all four constructive squared cross-term corrections.",
        ),
        spec(
            FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
            "forall left right. exists magnitude. "
            "(left = right + magnitude \\/ right = left + magnitude)",
            ("signed_balance_total", SIGNED_BALANCE_ABSOLUTE_EXISTS),
            (
                "intro left",
                "intro right",
                "have hbalance : exists code. "
                f"({_balance_expression('code', 'left', 'right', tag='fs_difference')})",
                "apply signed_balance_total",
                "cases hbalance",
                "specialize signed_balance_absolute_exists x",
                "specialize signed_balance_absolute_exists left",
                "specialize signed_balance_absolute_exists right",
                "apply signed_balance_absolute_exists",
                "exact hbalance_witness",
            ),
            "Canonical signed totality yields a natural absolute difference "
            "for any ordered pair, without importing another candidate module.",
        ),
        spec(
            FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
            "forall a b c d e f m n. "
            "(a * f = b * e + m \\/ b * e = a * f + m) -> "
            "(c * f = d * e + n \\/ d * e = c * f + n) -> "
            "(a * a + b * b + c * c + d * d) * (e * e + f * f) = "
            "((a * e + b * f) * (a * e + b * f) + m * m) + "
            "((c * e + d * f) * (c * e + d * f) + n * n)",
            (
                "add_assoc",
                "add_mul",
                "brahmagupta_fibonacci_two_square_identity",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro m",
                "intro n",
                "intro hfirst",
                "intro hsecond",
                "trans ((a * a + b * b) + (c * c + d * d)) * "
                "(e * e + f * f)",
                "congr",
                "apply add_assoc",
                "refl",
                "trans (a * a + b * b) * (e * e + f * f) + "
                "(c * c + d * d) * (e * e + f * f)",
                "apply add_mul",
                "congr",
                "apply brahmagupta_fibonacci_two_square_identity",
                "exact hfirst",
                "apply brahmagupta_fibonacci_two_square_identity",
                "exact hsecond",
            ),
            "The six-variable Euler subclass with a two-square right factor "
            "is exactly the sum of two independently composed two-square norms.",
        ),
        spec(
            FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL,
            "forall a b c d e f. exists u v w x. "
            "(a * a + b * b + c * c + d * d) * (e * e + f * f) = "
            "u * u + v * v + w * w + x * x",
            (
                FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL,
                FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY,
                "add_assoc",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "have hfirst : exists m. "
                "(a * f = b * e + m \\/ b * e = a * f + m)",
                "apply four_square_absolute_difference_total",
                "cases hfirst",
                "have hsecond : exists n. "
                "(c * f = d * e + n \\/ d * e = c * f + n)",
                "apply four_square_absolute_difference_total",
                "cases hsecond",
                "exists a * e + b * f",
                "exists x",
                "exists c * e + d * f",
                "exists x1",
                "trans ((a * e + b * f) * (a * e + b * f) + x * x) + "
                "((c * e + d * f) * (c * e + d * f) + x1 * x1)",
                "apply four_square_two_square_factor_identity",
                "exact hfirst_witness",
                "exact hsecond_witness",
                "symm",
                "apply add_assoc",
            ),
            "Every four-square norm multiplied by any two-square norm has "
            "four explicitly constructed natural-square witnesses.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_NORM_DISTRIBUTES",
    "FOUR_SQUARE_ABSOLUTE_DIFFERENCE_TOTAL",
    "FOUR_SQUARE_ABSOLUTE_SQUARE_BALANCE",
    "FOUR_SQUARE_ADDITIVE_GAP_REORDER",
    "FOUR_SQUARE_ADD_SWAP_RIGHT_TAIL",
    "FOUR_SQUARE_GAP_BALANCE_LEFT",
    "FOUR_SQUARE_GAP_BALANCE_RIGHT",
    "FOUR_SQUARE_PRODUCT_SHUFFLE",
    "FOUR_SQUARE_PRODUCT_SQUARE",
    "FOUR_SQUARE_SUM_EXPANSION",
    "FOUR_SQUARE_TWO_SQUARE_FACTOR_IDENTITY",
    "FOUR_SQUARE_TWO_SQUARE_FACTOR_TOTAL",
    "QUATERNION_COORDINATE_ABSOLUTE_TOTAL",
    "QUATERNION_COORDINATE_BALANCE_TOTAL",
    "QUATERNION_COORDINATE_SQUARE_BALANCE_TOTAL",
    "QUATERNION_COORDINATE_SQUARE_TRANSPORT",
    "SIGNED_BALANCE_ABSOLUTE_EXISTS",
    "SIGNED_BALANCE_SQUARE_TRANSPORT",
    "SIGNED_SQUARE_CROSS_TERM_ZERO",
    "SIGNED_SQUARE_MAGNITUDE_EXPANDS",
    "make_four_square_identity_candidate_theorems",
]
