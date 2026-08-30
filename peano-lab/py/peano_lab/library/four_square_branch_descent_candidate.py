"""Complete constructive parity branches for below-prime multiplier descent.

The even branch is unconditional.  The odd branch retains exactly one visible
mathematical hypothesis: representation of the same signed centered quotient.
Nothing here changes Alpha, Stable, or any previously sealed edition.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .four_square_descent_candidate import centered_signed_remainder
from .four_square_lagrange_bridge_candidate import (
    bounded_strict_prime_multiple_descent,
)
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_BRANCH_NONZERO_EVEN_HALF = "four_square_branch_nonzero_even_half"
FOUR_SQUARE_BRANCH_POSITIVE_HALF_STRICT = "four_square_branch_positive_half_strict"
FOUR_SQUARE_BRANCH_EVEN_REPRESENTED_STRICT_STEP = (
    "four_square_branch_even_represented_strict_step"
)
FOUR_SQUARE_BRANCH_ODD_REPRESENTED_STRICT_STEP = (
    "four_square_branch_odd_represented_strict_step"
)
FOUR_SQUARE_BOUNDED_STRICT_DESCENT_FROM_ODD_SIGNED_QUATERNION = (
    "four_square_bounded_strict_descent_from_odd_signed_quaternion"
)


def odd_signed_centered_representation(*, tag: str) -> str:
    """Expand exactly the represented signed centered odd quaternion quotient."""

    modulus = f"fsbr_modulus_{tag}"
    multiplier = f"fsbr_multiplier_{tag}"
    half = f"fsbr_half_{tag}"
    coordinates = tuple(f"fsbr_coordinate_{tag}_{index}" for index in range(4))
    centers = tuple(f"fsbr_center_{tag}_{index}" for index in range(4))
    quotient = f"fsbr_quotient_{tag}"
    original_norm = " + ".join(f"{value} * {value}" for value in coordinates)
    centered_norm = " + ".join(f"{value} * {value}" for value in centers)
    center_conditions = " -> ".join(
        f"({centered_signed_remainder(multiplier, value, center, tag=f'{tag}_{index}')})"
        for index, (value, center) in enumerate(zip(coordinates, centers, strict=True))
    )
    result = four_square_representation(
        f"{modulus} * {quotient}", tag=f"fsbr_signed_{tag}"
    )
    quantified = " ".join(
        (modulus, multiplier, half, *coordinates, *centers, quotient)
    )
    return (
        f"forall {quantified}. ~({multiplier} = 0) -> "
        f"{multiplier} = 2 * {half} + 1 -> "
        f"{modulus} * {multiplier} = {original_norm} -> "
        f"{center_conditions} -> "
        f"{multiplier} * {quotient} = {centered_norm} -> ({result})"
    )


def make_four_square_branch_descent_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build unconditional even descent and the exact conditional odd branch."""

    signed_premise = odd_signed_centered_representation(tag="branch")
    bounded_step = bounded_strict_prime_multiple_descent(tag="branch")
    prime_p = prime("p", tag="fsbr_prime")
    represented_multiple = four_square_representation(
        "p * k", tag="fsbr_multiple"
    )
    represented_smaller = four_square_representation(
        "p * r", tag="fsbr_smaller"
    )
    smaller_result = (
        "exists r. (~(r = 0) /\\ "
        "((exists gap. gap + S r = k) /\\ "
        f"({represented_smaller})))"
    )

    return (
        spec(
            FOUR_SQUARE_BRANCH_NONZERO_EVEN_HALF,
            "forall k h. ~(k = 0) -> k = 2 * h -> ~(h = 0)",
            (),
            (
                "intro k",
                "intro h",
                "intro hnonzero",
                "intro hdouble",
                "intro hzero",
                "apply hnonzero",
                "trans 2 * h",
                "exact hdouble",
                "rewrite hzero",
                "simp",
            ),
            "The half of a constructively nonzero even multiplier is itself nonzero.",
        ),
        spec(
            FOUR_SQUARE_BRANCH_POSITIVE_HALF_STRICT,
            "forall h. ~(h = 0) -> exists gap. gap + S h = 2 * h",
            (
                "mul_lt_mul_succ_left_nonzero",
                "mul_one",
                "mul_comm",
            ),
            (
                "intro h",
                "intro hnonzero",
                "have hbound : exists gap. gap + S (h * 1) = h * S 1",
                "specialize mul_lt_mul_succ_left_nonzero h",
                "specialize mul_lt_mul_succ_left_nonzero 1",
                "apply mul_lt_mul_succ_left_nonzero",
                "exact hnonzero",
                "specialize mul_one h",
                "rewrite mul_one at hbound",
                "have htwo : S 1 = 2",
                "norm_num",
                "rewrite htwo at hbound",
                "specialize mul_comm h",
                "specialize mul_comm 2",
                "rewrite mul_comm at hbound",
                "exact hbound",
            ),
            "Every positive natural half is constructively strictly smaller than its doubled value.",
        ),
        spec(
            FOUR_SQUARE_BRANCH_EVEN_REPRESENTED_STRICT_STEP,
            "forall p k h. ~(k = 0) -> k = 2 * h -> "
            f"({represented_multiple}) -> ({smaller_result})",
            (
                FOUR_SQUARE_BRANCH_NONZERO_EVEN_HALF,
                FOUR_SQUARE_BRANCH_POSITIVE_HALF_STRICT,
                "mul_double_right",
                "mul_comm",
                "four_square_parity_represented_double_halving",
            ),
            (
                "intro p",
                "intro k",
                "intro h",
                "intro hnonzero",
                "intro hdouble",
                "intro hrepresented",
                "have hhalf : ~(h = 0)",
                "intro hzero",
                "specialize four_square_branch_nonzero_even_half k",
                "specialize four_square_branch_nonzero_even_half h",
                "apply four_square_branch_nonzero_even_half",
                "exact hnonzero",
                "exact hdouble",
                "exact hzero",
                "exists h",
                "split",
                "exact hhalf",
                "split",
                "rewrite hdouble",
                "apply four_square_branch_positive_half_strict",
                "exact hhalf",
                "rewrite hdouble at hrepresented",
                "specialize mul_double_right p",
                "specialize mul_double_right h",
                "rewrite mul_double_right at hrepresented",
                "specialize mul_comm 2",
                "specialize mul_comm (p * h)",
                "rewrite mul_comm at hrepresented",
                "specialize four_square_parity_represented_double_halving (p * h)",
                "apply four_square_parity_represented_double_halving",
                "exact hrepresented",
            ),
            "Every represented nonzero even prime multiplier unconditionally descends to its nonzero strictly smaller represented half.",
        ),
        spec(
            FOUR_SQUARE_BRANCH_ODD_REPRESENTED_STRICT_STEP,
            f"({signed_premise}) -> forall p k h. ({prime_p}) -> "
            "~(k = 0) -> ~(k = 1) -> "
            "(exists gap. gap + S k = p) -> k = 2 * h + 1 -> "
            f"({represented_multiple}) -> ({smaller_result})",
            (
                "four_square_descent_centered_four_remainders_exist",
                "four_square_signed_centered_norm_quotient_exists",
                "four_square_descent_odd_centered_strict_step",
            ),
            (
                "intro hsigned",
                "intro p",
                "intro k",
                "intro h",
                "intro hprime",
                "intro hnonzero",
                "intro hnonunit",
                "intro hproper",
                "intro hodd",
                "intro hrepresented",
                "cases hrepresented",
                "cases hrepresented_witness",
                "cases hrepresented_witness_witness",
                "cases hrepresented_witness_witness_witness",
                "have hcenters : exists e f g j. "
                f"(({centered_signed_remainder('k', 'x', 'e', tag='branch_a')}) /\\ "
                f"(({centered_signed_remainder('k', 'x1', 'f', tag='branch_b')}) /\\ "
                f"(({centered_signed_remainder('k', 'x2', 'g', tag='branch_c')}) /\\ "
                f"({centered_signed_remainder('k', 'x3', 'j', tag='branch_d')}))))",
                "specialize four_square_descent_centered_four_remainders_exist k",
                "specialize four_square_descent_centered_four_remainders_exist x",
                "specialize four_square_descent_centered_four_remainders_exist x1",
                "specialize four_square_descent_centered_four_remainders_exist x2",
                "specialize four_square_descent_centered_four_remainders_exist x3",
                "apply four_square_descent_centered_four_remainders_exist",
                "exact hnonzero",
                "cases hcenters",
                "cases hcenters_witness",
                "cases hcenters_witness_witness",
                "cases hcenters_witness_witness_witness",
                "cases hcenters_witness_witness_witness_witness",
                "cases hcenters_witness_witness_witness_witness_right",
                "cases hcenters_witness_witness_witness_witness_right_right",
                "have hquotient : "
                "exists r. k * r = x4 * x4 + x5 * x5 + x6 * x6 + x7 * x7",
                "specialize four_square_signed_centered_norm_quotient_exists p",
                "specialize four_square_signed_centered_norm_quotient_exists k",
                "specialize four_square_signed_centered_norm_quotient_exists x",
                "specialize four_square_signed_centered_norm_quotient_exists x1",
                "specialize four_square_signed_centered_norm_quotient_exists x2",
                "specialize four_square_signed_centered_norm_quotient_exists x3",
                "specialize four_square_signed_centered_norm_quotient_exists x4",
                "specialize four_square_signed_centered_norm_quotient_exists x5",
                "specialize four_square_signed_centered_norm_quotient_exists x6",
                "specialize four_square_signed_centered_norm_quotient_exists x7",
                "apply four_square_signed_centered_norm_quotient_exists",
                "exact hrepresented_witness_witness_witness_witness",
                "exact hcenters_witness_witness_witness_witness_left",
                "exact hcenters_witness_witness_witness_witness_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_right",
                "cases hquotient",
                "specialize four_square_descent_odd_centered_strict_step p",
                "specialize four_square_descent_odd_centered_strict_step k",
                "specialize four_square_descent_odd_centered_strict_step h",
                "specialize four_square_descent_odd_centered_strict_step x8",
                "specialize four_square_descent_odd_centered_strict_step x",
                "specialize four_square_descent_odd_centered_strict_step x1",
                "specialize four_square_descent_odd_centered_strict_step x2",
                "specialize four_square_descent_odd_centered_strict_step x3",
                "specialize four_square_descent_odd_centered_strict_step x4",
                "specialize four_square_descent_odd_centered_strict_step x5",
                "specialize four_square_descent_odd_centered_strict_step x6",
                "specialize four_square_descent_odd_centered_strict_step x7",
                "apply four_square_descent_odd_centered_strict_step",
                "exact hprime",
                "exact hnonzero",
                "exact hnonunit",
                "exact hproper",
                "exact hodd",
                "exact hrepresented_witness_witness_witness_witness",
                "exact hcenters_witness_witness_witness_witness_left",
                "exact hcenters_witness_witness_witness_witness_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_right",
                "exact hquotient_witness",
                "specialize hsigned p",
                "specialize hsigned k",
                "specialize hsigned h",
                "specialize hsigned x",
                "specialize hsigned x1",
                "specialize hsigned x2",
                "specialize hsigned x3",
                "specialize hsigned x4",
                "specialize hsigned x5",
                "specialize hsigned x6",
                "specialize hsigned x7",
                "specialize hsigned x8",
                "apply hsigned",
                "exact hnonzero",
                "exact hodd",
                "exact hrepresented_witness_witness_witness_witness",
                "exact hcenters_witness_witness_witness_witness_left",
                "exact hcenters_witness_witness_witness_witness_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_left",
                "exact hcenters_witness_witness_witness_witness_right_right_right",
                "exact hquotient_witness",
            ),
            "A proper odd prime multiplier descends constructively once its one explicitly centered signed quaternion quotient is represented.",
        ),
        spec(
            FOUR_SQUARE_BOUNDED_STRICT_DESCENT_FROM_ODD_SIGNED_QUATERNION,
            f"({signed_premise}) -> ({bounded_step})",
            (
                "parity_cases",
                FOUR_SQUARE_BRANCH_EVEN_REPRESENTED_STRICT_STEP,
                FOUR_SQUARE_BRANCH_ODD_REPRESENTED_STRICT_STEP,
            ),
            (
                "intro hsigned",
                "intro p",
                "intro k",
                "intro hprime",
                "intro hnonzero",
                "intro hnonunit",
                "intro hproper",
                "intro hrepresented",
                "have hparity : exists h. k = 2 * h \\/ k = 2 * h + 1",
                "specialize parity_cases k",
                "exact parity_cases",
                "cases hparity",
                "cases hparity_witness",
                "specialize four_square_branch_even_represented_strict_step p",
                "specialize four_square_branch_even_represented_strict_step k",
                "specialize four_square_branch_even_represented_strict_step x",
                "apply four_square_branch_even_represented_strict_step",
                "exact hnonzero",
                "exact hparity_witness_left",
                "exact hrepresented",
                "have hoddstep : forall q j t. "
                f"({prime('q', tag='fsbr_local_prime')}) -> "
                "~(j = 0) -> ~(j = 1) -> "
                "(exists gap. gap + S j = q) -> j = 2 * t + 1 -> "
                f"({four_square_representation('q * j', tag='fsbr_local_source')}) -> "
                "exists r. (~(r = 0) /\\ "
                "((exists gap. gap + S r = j) /\\ "
                f"({four_square_representation('q * r', tag='fsbr_local_result')})))",
                "apply four_square_branch_odd_represented_strict_step",
                "exact hsigned",
                "specialize hoddstep p",
                "specialize hoddstep k",
                "specialize hoddstep x",
                "apply hoddstep",
                "exact hprime",
                "exact hnonzero",
                "exact hnonunit",
                "exact hproper",
                "exact hparity_witness_right",
                "exact hrepresented",
            ),
            "Parity case distinction discharges the entire below-prime strict-descent obligation except for the single explicitly stated odd signed quaternion representation.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_BOUNDED_STRICT_DESCENT_FROM_ODD_SIGNED_QUATERNION",
    "FOUR_SQUARE_BRANCH_EVEN_REPRESENTED_STRICT_STEP",
    "FOUR_SQUARE_BRANCH_NONZERO_EVEN_HALF",
    "FOUR_SQUARE_BRANCH_ODD_REPRESENTED_STRICT_STEP",
    "FOUR_SQUARE_BRANCH_POSITIVE_HALF_STRICT",
    "make_four_square_branch_descent_candidate_theorems",
    "odd_signed_centered_representation",
]
