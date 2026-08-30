"""All sixteen constructive signed centered quaternion orientation cases.

The five canonical modular block surfaces reduce all sign patterns through
simultaneous coordinate permutations.  Each case has an explicit independently
checkable proof; no signed arithmetic or orientation axiom is introduced.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .fermat_two_squares_collision_norm_candidate import _mod
from .four_square_conjugate_identity_candidate import (
    conjugate_coordinate_contributions,
)
from .four_square_identity_candidate import (
    _absolute_expression,
    _conjunction,
    _coordinate_contributions,
)
from .four_square_lagrange_candidate import four_square_representation
from .four_square_signed_quaternion_candidate import _permutation_commands


FOUR_SQUARE_SIGNED_CASES_NORM_QUOTIENT_ZERO_CONGRUENCE = (
    "four_square_signed_cases_norm_quotient_zero_congruence"
)
FOUR_SQUARE_SIGNED_ORIENTATION_MASK_NAMES = tuple(
    f"four_square_signed_orientation_mask_{mask:02d}" for mask in range(16)
)


def _norm(values: tuple[str, str, str, str]) -> str:
    return " + ".join(f"{value} * {value}" for value in values)


def _replace_coordinate_names(expression: str, values: tuple[str, ...]) -> str:
    replacements = dict(zip("abcdefgh", values, strict=True))
    return re.sub(r"\b[a-h]\b", lambda match: replacements[match.group(0)], expression)


def _orient(modulus: str, value: str, center: str, *, negative: bool, tag: str) -> str:
    return _mod(
        modulus,
        f"{value} + {center}" if negative else value,
        "0" if negative else center,
        tag=tag,
    )


def _canonical_data(mask: int) -> tuple[str, tuple[int, int, int, int], bool, bool]:
    negative = tuple(index for index in range(4) if mask & (1 << index))
    positive = tuple(index for index in range(4) if not mask & (1 << index))
    if not negative:
        return (
            "four_square_signed_conjugate_positive_blocks",
            (0, 1, 2, 3),
            True,
            False,
        )
    if len(negative) == 4:
        return (
            "four_square_signed_conjugate_negative_blocks",
            (0, 1, 2, 3),
            True,
            False,
        )
    if len(negative) == 2:
        return (
            "four_square_signed_conjugate_mixed_blocks",
            (*negative, *positive),
            True,
            True,
        )
    if len(negative) == 1:
        return (
            "four_square_signed_natural_negative_first_blocks",
            (*negative, *positive),
            False,
            False,
        )
    return (
        "four_square_signed_natural_positive_first_blocks",
        (*positive, *negative),
        False,
        False,
    )


def _norm_permutation_commands(
    source: tuple[str, str, str, str],
    target: tuple[str, str, str, str],
) -> tuple[str, ...]:
    if source == target:
        return ("refl",)
    return _permutation_commands(
        tuple(f"{value} * {value}" for value in source),
        tuple(f"{value} * {value}" for value in target),
    )


def _case(spec: Callable[..., Any], mask: int) -> Any:
    originals = ("a", "b", "c", "d")
    centers = ("e", "f", "g", "j")
    canonical, permutation, conjugate, reverse_centers = _canonical_data(mask)
    original_permuted = tuple(originals[index] for index in permutation)
    center_permuted = tuple(centers[index] for index in permutation)
    center_identity = (
        tuple(reversed(center_permuted)) if reverse_centers else center_permuted
    )
    coordinates = original_permuted + center_identity
    templates = (
        conjugate_coordinate_contributions()
        if conjugate
        else _coordinate_contributions()
    )
    blocks = tuple(
        (
            _replace_coordinate_names(positive, coordinates),
            _replace_coordinate_names(negative, coordinates),
        )
        for positive, negative in templates
    )
    orientation = tuple(
        _orient(
            "k",
            original,
            center,
            negative=bool(mask & (1 << index)),
            tag=f"mask_{mask}_{index}",
        )
        for index, (original, center) in enumerate(zip(originals, centers, strict=True))
    )
    magnitudes = ("m0", "m1", "m2", "m3")
    absolute = tuple(
        _absolute_expression(positive, negative, magnitude)
        for (positive, negative), magnitude in zip(blocks, magnitudes, strict=True)
    )
    block_congruence = tuple(
        _mod("k", positive, negative, tag=f"case_{mask}_block_{index}")
        for index, (positive, negative) in enumerate(blocks)
    )
    original_norm = _norm(originals)
    center_norm = _norm(centers)
    permuted_original_norm = _norm(original_permuted)
    permuted_center_norm = _norm(center_permuted)
    identity_center_norm = _norm(center_identity)
    magnitude_norm = _norm(magnitudes)
    witness_norm = _norm(("x", "x1", "x2", "x3"))
    representation = four_square_representation("p * r", tag=f"fssc_mask_{mask}")
    statement = (
        "forall p k h a b c d e f g j r. ~(k = 0) -> "
        f"k = 2 * h + 1 -> p * k = {original_norm} -> "
        + " -> ".join(f"({condition})" for condition in orientation)
        + f" -> k * r = {center_norm} -> ({representation})"
    )

    script: list[str] = [
        *(f"intro {value}" for value in ("p", "k", "h", *originals, *centers, "r")),
        "intro hnonzero",
        "intro hodd",
        "intro hfirst",
        *(f"intro horientation{index}" for index in range(4)),
        "intro hcenter",
        f"have hfirst_permuted : p * k = {permuted_original_norm}",
        f"trans {original_norm}",
        "exact hfirst",
        *_norm_permutation_commands(originals, original_permuted),
        f"have hcenter_permuted : k * r = {permuted_center_norm}",
        f"trans {center_norm}",
        "exact hcenter",
        *_norm_permutation_commands(centers, center_permuted),
        f"have hzero : ({_mod('k', permuted_center_norm, '0', tag=f'case_{mask}_zero')})",
        "specialize four_square_signed_cases_norm_quotient_zero_congruence k",
        "specialize four_square_signed_cases_norm_quotient_zero_congruence r",
        *(
            f"specialize four_square_signed_cases_norm_quotient_zero_congruence {value}"
            for value in center_permuted
        ),
        "apply four_square_signed_cases_norm_quotient_zero_congruence",
        "exact hcenter_permuted",
        f"have hblocks : ({_conjunction(block_congruence)})",
        f"specialize {canonical} k",
        *(f"specialize {canonical} {value}" for value in original_permuted),
        *(f"specialize {canonical} {value}" for value in center_permuted),
        f"apply {canonical}",
        "exact hzero",
        *(f"exact horientation{index}" for index in permutation),
    ]

    absolute_formula = _conjunction(absolute)
    if conjugate:
        script.extend(
            (
                "have hcoordinates : exists m0 m1 m2 m3. "
                f"(({absolute_formula}) /\\ "
                f"(({permuted_original_norm}) * ({identity_center_norm}) = "
                f"{magnitude_norm}))",
                *(
                    f"specialize four_square_conjugate_absolute_coordinates_total {value}"
                    for value in coordinates
                ),
                "exact four_square_conjugate_absolute_coordinates_total",
            )
        )
    else:
        script.extend(
            (
                "have hcoordinates : exists m0 m1 m2 m3. "
                f"({absolute_formula})",
                *(
                    f"specialize quaternion_coordinate_absolute_total {value}"
                    for value in coordinates
                ),
                "exact quaternion_coordinate_absolute_total",
            )
        )

    script.extend(
        (
            "cases hcoordinates",
            "cases hcoordinates_witness",
            "cases hcoordinates_witness_witness",
            "cases hcoordinates_witness_witness_witness",
        )
    )
    witness_absolute = _conjunction(
        tuple(
            _absolute_expression(positive, negative, magnitude)
            for (positive, negative), magnitude in zip(
                blocks, ("x", "x1", "x2", "x3"), strict=True
            )
        )
    )
    if conjugate:
        script.append("cases hcoordinates_witness_witness_witness_witness")
        abs_source = "hcoordinates_witness_witness_witness_witness_left"
        identity_source = "hcoordinates_witness_witness_witness_witness_right"
    else:
        abs_source = "hcoordinates_witness_witness_witness_witness"
        identity_source = "four_square_euler_quaternion"

    script.extend((f"have habsolute : ({witness_absolute})", f"exact {abs_source}"))
    script.append(
        "have hidentity : "
        f"({permuted_original_norm}) * ({identity_center_norm}) = {witness_norm}"
    )
    if conjugate:
        script.append(f"exact {identity_source}")
    else:
        script.extend(
            (
                *(f"specialize four_square_euler_quaternion {value}" for value in coordinates),
                *(f"specialize four_square_euler_quaternion {value}" for value in ("x", "x1", "x2", "x3")),
                "apply four_square_euler_quaternion",
                "exact habsolute",
            )
        )

    script.extend(
        (
            f"have hcenter_identity : k * r = {identity_center_norm}",
            f"trans {permuted_center_norm}",
            "exact hcenter_permuted",
            *_norm_permutation_commands(center_permuted, center_identity),
            f"have hproduct : (p * k) * (k * r) = {witness_norm}",
            f"trans ({permuted_original_norm}) * ({identity_center_norm})",
            "congr",
            "exact hfirst_permuted",
            "exact hcenter_identity",
            "exact hidentity",
            "cases hblocks",
            "cases hblocks_right",
            "cases hblocks_right_right",
            "cases habsolute",
            "cases habsolute_right",
            "cases habsolute_right_right",
            "specialize four_square_signed_absolute_block_representation p",
            "specialize four_square_signed_absolute_block_representation k",
            "specialize four_square_signed_absolute_block_representation r",
            *(
                f"specialize four_square_signed_absolute_block_representation ({positive})"
                for positive, _negative in blocks
            ),
            *(
                f"specialize four_square_signed_absolute_block_representation ({negative})"
                for _positive, negative in blocks
            ),
            *(
                f"specialize four_square_signed_absolute_block_representation {value}"
                for value in ("x", "x1", "x2", "x3")
            ),
            "apply four_square_signed_absolute_block_representation",
            "exact hnonzero",
            "exact hproduct",
            "exact hblocks_left",
            "exact habsolute_left",
            "exact hblocks_right_left",
            "exact habsolute_right_left",
            "exact hblocks_right_right_left",
            "exact habsolute_right_right_left",
            "exact hblocks_right_right_right",
            "exact habsolute_right_right_right",
        )
    )

    dependencies = [
        FOUR_SQUARE_SIGNED_CASES_NORM_QUOTIENT_ZERO_CONGRUENCE,
        canonical,
        "four_square_signed_absolute_block_representation",
        "add_assoc",
        "add_comm",
        "four_square_add_swap_right_tail",
    ]
    if conjugate:
        dependencies.append("four_square_conjugate_absolute_coordinates_total")
    else:
        dependencies.extend(("quaternion_coordinate_absolute_total", "four_square_euler_quaternion"))

    return spec(
        FOUR_SQUARE_SIGNED_ORIENTATION_MASK_NAMES[mask],
        statement,
        tuple(dependencies),
        tuple(script),
        "Constructive signed quaternion quotient for centered orientation mask "
        f"{mask:04b}, using the exact {canonical} surface.",
    )


def make_four_square_signed_cases_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build all sixteen explicit, independently checked orientation cases."""

    norm = "a * a + b * b + c * c + d * d"
    zero = spec(
        FOUR_SQUARE_SIGNED_CASES_NORM_QUOTIENT_ZERO_CONGRUENCE,
        "forall k r a b c d. "
        f"k * r = {norm} -> ({_mod('k', norm, '0', tag='case_norm_zero')})",
        ("multiple_implies_balanced_zero_congruence",),
        (
            "intro k",
            "intro r",
            "intro a",
            "intro b",
            "intro c",
            "intro d",
            "intro hnorm",
            "specialize multiple_implies_balanced_zero_congruence k",
            f"specialize multiple_implies_balanced_zero_congruence ({norm})",
            "apply multiple_implies_balanced_zero_congruence",
            "exists r",
            "symm",
            "exact hnorm",
        ),
        "An exact centered norm quotient supplies constructive balanced zero congruence for its complete four-square norm.",
    )
    return (zero,) + tuple(_case(spec, mask) for mask in range(16))


__all__ = [
    "FOUR_SQUARE_SIGNED_CASES_NORM_QUOTIENT_ZERO_CONGRUENCE",
    "FOUR_SQUARE_SIGNED_ORIENTATION_MASK_NAMES",
    "make_four_square_signed_cases_candidate_theorems",
]
