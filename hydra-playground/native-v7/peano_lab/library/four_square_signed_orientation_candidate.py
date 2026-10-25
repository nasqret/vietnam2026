"""Bounded signed-coordinate orientation and exact four-square quotients.

The generic quotient bridge is unconditional.  Any later orientation endpoint
must supply its actual modular coordinate balances; no signed Euler premise
is silently assumed.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_two_squares_collision_norm_candidate import _mod, _multiple
from .four_square_branch_descent_candidate import odd_signed_centered_representation
from .four_square_identity_candidate import _absolute_expression
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION = (
    "four_square_signed_divisible_norm_product_representation"
)
FOUR_SQUARE_SIGNED_ABSOLUTE_BLOCK_REPRESENTATION = (
    "four_square_signed_absolute_block_representation"
)
FOUR_SQUARE_SIGNED_CENTERED_REPRESENTATION = (
    "four_square_signed_centered_representation"
)
SIGNED_ORIENTATION_MASK_NAMES = tuple(
    f"four_square_signed_orientation_mask_{mask:02d}" for mask in range(16)
)


def _centered_orientation_dispatch_script() -> tuple[str, ...]:
    """Split actual centered signed witnesses into their sixteen checked cases."""

    originals = ("a", "b", "c", "d")
    centers = ("e", "f", "g", "j")
    script: list[str] = [
        *(f"intro {name}" for name in ("p", "k", "h", *originals, *centers, "r")),
        "intro hnonzero",
        "intro hodd",
        "intro hfirst",
        *(f"intro hcenter_{name}" for name in originals),
        "intro hsecond",
    ]
    for original, center in zip(originals, centers, strict=True):
        positive = _mod("k", original, center, tag=f"fsso_dispatch_positive_{original}")
        negative = _mod(
            "k", f"{original} + {center}", "0", tag=f"fsso_dispatch_negative_{original}"
        )
        script.extend(
            (
                f"have hsign_{original} : (({positive}) \\/ ({negative}))",
                "specialize four_square_signed_centered_orientation k",
                f"specialize four_square_signed_centered_orientation {original}",
                f"specialize four_square_signed_centered_orientation {center}",
                "apply four_square_signed_centered_orientation",
                f"exact hcenter_{original}",
            )
        )

    def branch(index: int, mask: int) -> list[str]:
        if index < len(originals):
            return (
                [f"cases hsign_{originals[index]}"]
                + branch(index + 1, mask)
                + branch(index + 1, mask | (1 << index))
            )

        name = SIGNED_ORIENTATION_MASK_NAMES[mask]
        commands = [
            *(f"specialize {name} {value}" for value in ("p", "k", "h", *originals, *centers, "r")),
            f"apply {name}",
            "exact hnonzero",
            "exact hodd",
            "exact hfirst",
        ]
        commands.extend(
            f"exact hsign_{original}_{'right' if mask & (1 << position) else 'left'}"
            for position, original in enumerate(originals)
        )
        commands.append("exact hsecond")
        return commands

    script.extend(branch(0, 0))
    return tuple(script)


def make_four_square_signed_orientation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Construct exact represented quotients from modular signed coordinates."""

    magnitudes = ("m0", "m1", "m2", "m3")
    positive = ("p0", "p1", "p2", "p3")
    negative = ("n0", "n1", "n2", "n3")
    norm = " + ".join(f"{value} * {value}" for value in magnitudes)
    representation = four_square_representation("p * r", tag="fsso_quotient")
    multiples = tuple(
        _multiple("k", value, tag=f"fsso_multiple_{index}")
        for index, value in enumerate(magnitudes)
    )
    balances = tuple(
        _mod("k", left, right, tag=f"fsso_balance_{index}")
        for index, (left, right) in enumerate(zip(positive, negative, strict=True))
    )
    absolute = tuple(
        _absolute_expression(left, right, magnitude)
        for left, right, magnitude in zip(
            positive, negative, magnitudes, strict=True
        )
    )

    quotient_script: list[str] = [
        "intro p",
        "intro k",
        "intro r",
        *(f"intro {value}" for value in magnitudes),
        "intro hnonzero",
        "intro hnorm",
        *(f"intro hdiv{index}" for index in range(4)),
        *(f"cases hdiv{index}" for index in range(4)),
        "exists x",
        "exists x1",
        "exists x2",
        "exists x3",
        "specialize four_square_descent_scaled_norm_quotient p",
        "specialize four_square_descent_scaled_norm_quotient k",
        "specialize four_square_descent_scaled_norm_quotient r",
        "specialize four_square_descent_scaled_norm_quotient x",
        "specialize four_square_descent_scaled_norm_quotient x1",
        "specialize four_square_descent_scaled_norm_quotient x2",
        "specialize four_square_descent_scaled_norm_quotient x3",
        "apply four_square_descent_scaled_norm_quotient",
        "exact hnonzero",
        *(
            f"rewrite hdiv{index}_witness at hnorm"
            for index in range(4)
            for _occurrence in range(2)
        ),
        "exact hnorm",
    ]

    block_script: list[str] = [
        "intro p",
        "intro k",
        "intro r",
        *(f"intro {value}" for value in positive),
        *(f"intro {value}" for value in negative),
        *(f"intro {value}" for value in magnitudes),
        "intro hnonzero",
        "intro hnorm",
    ]
    for index in range(4):
        block_script.extend((f"intro hmod{index}", f"intro habs{index}"))
    block_script.extend(
        (
            "specialize four_square_signed_divisible_norm_product_representation p",
            "specialize four_square_signed_divisible_norm_product_representation k",
            "specialize four_square_signed_divisible_norm_product_representation r",
        )
    )
    block_script.extend(
        f"specialize four_square_signed_divisible_norm_product_representation {value}"
        for value in magnitudes
    )
    block_script.extend(
        (
            "apply four_square_signed_divisible_norm_product_representation",
            "exact hnonzero",
            "exact hnorm",
        )
    )
    for index in range(4):
        block_script.extend(
            (
                "specialize four_square_signed_absolute_congruence_divisible k",
                f"specialize four_square_signed_absolute_congruence_divisible {positive[index]}",
                f"specialize four_square_signed_absolute_congruence_divisible {negative[index]}",
                f"specialize four_square_signed_absolute_congruence_divisible {magnitudes[index]}",
                "apply four_square_signed_absolute_congruence_divisible",
                f"exact hmod{index}",
                f"exact habs{index}",
            )
        )

    return (
        spec(
            FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION,
            f"forall p k r {' '.join(magnitudes)}. ~(k = 0) -> "
            f"(p * k) * (k * r) = ({norm}) -> "
            + " -> ".join(f"({part})" for part in multiples)
            + f" -> ({representation})",
            ("four_square_descent_scaled_norm_quotient",),
            tuple(quotient_script),
            "Any four individually k-divisible natural norm-product coordinates yield an explicit four-square representation of the exact quotient p·r.",
        ),
        spec(
            FOUR_SQUARE_SIGNED_ABSOLUTE_BLOCK_REPRESENTATION,
            f"forall p k r {' '.join(positive)} {' '.join(negative)} {' '.join(magnitudes)}. "
            f"~(k = 0) -> (p * k) * (k * r) = ({norm}) -> "
            + " -> ".join(
                f"({balance}) -> ({magnitude})"
                for balance, magnitude in zip(balances, absolute, strict=True)
            )
            + f" -> ({representation})",
            (
                FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION,
                "four_square_signed_absolute_congruence_divisible",
            ),
            tuple(block_script),
            "Four signed absolute-coordinate blocks with actual modular balance construct every quotient coordinate and the represented prime-multiple quotient.",
        ),
        spec(
            FOUR_SQUARE_SIGNED_CENTERED_REPRESENTATION,
            odd_signed_centered_representation(tag="orientation"),
            (
                "four_square_signed_centered_orientation",
                *SIGNED_ORIENTATION_MASK_NAMES,
            ),
            _centered_orientation_dispatch_script(),
            "All sixteen actual centered sign patterns construct their signed quaternion quotient, yielding a genuine four-square representation without any orientation premise.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_SIGNED_ABSOLUTE_BLOCK_REPRESENTATION",
    "FOUR_SQUARE_SIGNED_CENTERED_REPRESENTATION",
    "FOUR_SQUARE_SIGNED_DIVISIBLE_NORM_PRODUCT_REPRESENTATION",
    "SIGNED_ORIENTATION_MASK_NAMES",
    "make_four_square_signed_orientation_candidate_theorems",
]
