"""Complete unconditional constructive Lagrange four-square theorem.

Both prime representation and universal Lagrange follow from independently
kernel-checked centered signed quaternion orientations and terminating
bounded multiplier descent.  The intermediate conditional reductions remain
available for an auditable exact proof graph.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .four_square_branch_descent_candidate import odd_signed_centered_representation
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION = (
    "four_square_prime_from_odd_signed_quaternion"
)
FOUR_SQUARE_LAGRANGE_FROM_ODD_SIGNED_QUATERNION = (
    "four_square_lagrange_from_odd_signed_quaternion"
)
FOUR_SQUARE_PRIME_REPRESENTATION = "four_square_prime_representation"
FOUR_SQUARE_LAGRANGE = "four_square_lagrange"


def make_four_square_lagrange_final_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build checked conditional bridges and unconditional prime/Lagrange roots."""

    signed = odd_signed_centered_representation(tag="final")
    represented_prime = four_square_representation("p", tag="fslf_prime")
    represented_natural = four_square_representation("n", tag="fslf_natural")

    return (
        spec(
            FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION,
            f"({signed}) -> forall p. "
            f"({prime('p', tag='fslf_prime')}) -> ({represented_prime})",
            (
                "four_square_bounded_strict_descent_from_odd_signed_quaternion",
                "four_square_prime_from_bounded_strict_descent",
            ),
            (
                "intro hsigned",
                "apply four_square_prime_from_bounded_strict_descent",
                "apply four_square_bounded_strict_descent_from_odd_signed_quaternion",
                "exact hsigned",
            ),
            "The actual bounded modular prime seed, complete even branch, centered odd bounds, and terminating descent reduce representation of every prime to the single signed odd quaternion identity.",
        ),
        spec(
            FOUR_SQUARE_LAGRANGE_FROM_ODD_SIGNED_QUATERNION,
            f"({signed}) -> forall n. ({represented_natural})",
            (
                FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION,
                "four_square_lagrange_from_all_primes",
            ),
            (
                "intro hsigned",
                "apply four_square_lagrange_from_all_primes",
                "apply four_square_prime_from_odd_signed_quaternion",
                "exact hsigned",
            ),
            "Universal Lagrange follows constructively from exactly one visible remaining hypothesis: representation of each odd signed centered quaternion quotient.",
        ),
        spec(
            FOUR_SQUARE_PRIME_REPRESENTATION,
            f"forall p. ({prime('p', tag='fslf_prime')}) -> ({represented_prime})",
            (
                FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION,
                "four_square_signed_centered_representation",
            ),
            (
                "apply four_square_prime_from_odd_signed_quaternion",
                "exact four_square_signed_centered_representation",
            ),
            "Every natural prime has an unconditionally constructed four-square representation, using the checked bounded seed, all sixteen signed quaternion cases, and terminating multiplier descent.",
        ),
        spec(
            FOUR_SQUARE_LAGRANGE,
            f"forall n. ({represented_natural})",
            (
                FOUR_SQUARE_PRIME_REPRESENTATION,
                "four_square_lagrange_from_all_primes",
            ),
            (
                "apply four_square_lagrange_from_all_primes",
                "exact four_square_prime_representation",
            ),
            "Lagrange's complete four-square theorem: every natural number has an unconditionally constructive, independently kernel-checked representation as a sum of four natural squares.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_LAGRANGE",
    "FOUR_SQUARE_LAGRANGE_FROM_ODD_SIGNED_QUATERNION",
    "FOUR_SQUARE_PRIME_FROM_ODD_SIGNED_QUATERNION",
    "FOUR_SQUARE_PRIME_REPRESENTATION",
    "make_four_square_lagrange_final_candidate_theorems",
]
