"""Constructive quaternion quotient and strictly decreasing multiplier descent.

The checked arithmetic below isolates the two real outstanding mathematical
inputs for universal Lagrange: a prime modular seed and a centered quaternion
certificate producing a strictly smaller nonzero multiplier.  Neither input
is assumed silently: both remain visible first-order premises.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .four_square_identity_candidate import (
    _absolute_expression,
    _conjunction,
    _coordinate_contributions,
)
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_DESCENT_NONZERO_SQUARE = "four_square_descent_nonzero_square"
FOUR_SQUARE_DESCENT_PRODUCT_REASSOCIATE = (
    "four_square_descent_product_reassociate"
)
FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM = "four_square_descent_square_factor_norm"
FOUR_SQUARE_DESCENT_SQUARE_FACTOR_CANCEL = (
    "four_square_descent_square_factor_cancel"
)
FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT = (
    "four_square_descent_scaled_norm_quotient"
)
FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT = (
    "four_square_descent_quaternion_quotient"
)
FOUR_SQUARE_DESCENT_STRICT_STEP_FROM_CENTERED_QUATERNION = (
    "four_square_descent_strict_step_from_centered_quaternion"
)
FOUR_SQUARE_DESCENT_MODULAR_SEED_MULTIPLIER_NONZERO = (
    "four_square_descent_modular_seed_multiplier_nonzero"
)
FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED = (
    "four_square_descent_strict_multiplier_bounded"
)
FOUR_SQUARE_DESCENT_PRIME_FROM_STRICT_STEP = (
    "four_square_descent_prime_from_strict_step"
)
FOUR_SQUARE_DESCENT_PRIME_FROM_MODULAR_SEED_AND_STEP = (
    "four_square_descent_prime_from_modular_seed_and_step"
)
FOUR_SQUARE_DESCENT_THREE_MOD_FOUR_PRIMES_FROM_SEED_AND_STEP = (
    "four_square_descent_three_mod_four_primes_from_seed_and_step"
)
FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT = (
    "four_square_lagrange_from_modular_seeds_and_strict_descent"
)
FOUR_SQUARE_DESCENT_REMAINDER_COMPLEMENT_EXISTS = (
    "four_square_descent_remainder_complement_exists"
)
FOUR_SQUARE_DESCENT_CENTERED_SIGNED_REMAINDER_EXISTS = (
    "four_square_descent_centered_signed_remainder_exists"
)
FOUR_SQUARE_DESCENT_CENTERED_FOUR_REMAINDERS_EXIST = (
    "four_square_descent_centered_four_remainders_exist"
)
FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER = (
    "four_square_descent_norm_bound_forces_smaller_multiplier"
)
FOUR_SQUARE_DESCENT_MATCHING_PARITY_SUM_EVEN = (
    "four_square_descent_matching_parity_sum_even"
)
FOUR_SQUARE_DESCENT_MATCHING_PARITY_ABSOLUTE_EVEN = (
    "four_square_descent_matching_parity_absolute_even"
)
FOUR_SQUARE_DESCENT_DOUBLE_PAIR_IDENTITY = (
    "four_square_descent_double_pair_identity"
)
FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_PAIRED_HALVING = (
    "four_square_descent_even_multiplier_paired_halving"
)
FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING = (
    "four_square_descent_even_multiplier_matching_parity_halving"
)
FOUR_SQUARE_DESCENT_ODD_CENTERED_MAGNITUDE_HALF_BOUND = (
    "four_square_descent_odd_centered_magnitude_half_bound"
)
FOUR_SQUARE_DESCENT_ADD_LE_ADD = "four_square_descent_add_le_add"
FOUR_SQUARE_DESCENT_DOUBLE_SQUARE_FOUR_SUM = (
    "four_square_descent_double_square_four_sum"
)
FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT = (
    "four_square_descent_odd_half_norm_strict"
)
FOUR_SQUARE_DESCENT_ODD_CENTERED_NORM_STRICT = (
    "four_square_descent_odd_centered_norm_strict"
)
FOUR_SQUARE_DESCENT_ZERO_NORM_COORDINATES = (
    "four_square_descent_zero_norm_coordinates"
)
FOUR_SQUARE_DESCENT_ZERO_CENTERED_REMAINDER_DIVIDES = (
    "four_square_descent_zero_centered_remainder_divides"
)
FOUR_SQUARE_DESCENT_NONUNIT_PROPER_FACTOR_NOT_PRIME = (
    "four_square_descent_nonunit_proper_factor_not_prime"
)
FOUR_SQUARE_DESCENT_DIVISIBLE_COORDINATES_PRIME_FACTOR = (
    "four_square_descent_divisible_coordinates_prime_factor"
)
FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO = (
    "four_square_descent_bounded_centered_quotient_nonzero"
)
FOUR_SQUARE_DESCENT_ODD_CENTERED_STRICT_STEP = (
    "four_square_descent_odd_centered_strict_step"
)


def _strict_step(*, tag: str) -> str:
    modulus = f"fsd_prime_{tag}"
    multiplier = f"fsd_multiplier_{tag}"
    smaller = f"fsd_smaller_{tag}"
    gap = f"fsd_gap_{tag}"
    return (
        f"forall {modulus} {multiplier}. "
        f"({prime(modulus, tag=f'fsd_{tag}_prime')}) -> "
        f"~({multiplier} = 0) -> ~({multiplier} = 1) -> "
        f"({four_square_representation(f'{modulus} * {multiplier}', tag=f'fsd_{tag}_source')}) -> "
        f"exists {smaller}. (~({smaller} = 0) /\\ "
        f"((exists {gap}. {gap} + S {smaller} = {multiplier}) /\\ "
        f"({four_square_representation(f'{modulus} * {smaller}', tag=f'fsd_{tag}_target')})))"
    )


def _three_mod_four_seeds(*, tag: str) -> str:
    modulus = f"fsd_seed_prime_{tag}"
    residue = f"fsd_seed_residue_{tag}"
    first = f"fsd_seed_first_{tag}"
    second = f"fsd_seed_second_{tag}"
    multiplier = f"fsd_seed_multiplier_{tag}"
    return (
        f"forall {modulus}. ({prime(modulus, tag=f'fsd_seed_{tag}')}) -> "
        f"(exists {residue}. {modulus} = 4 * {residue} + 3) -> "
        f"exists {first} {second} {multiplier}. "
        f"{first} * {first} + {second} * {second} + 1 = "
        f"{modulus} * {multiplier}"
    )


def centered_signed_remainder(modulus: str, value: str, magnitude: str, *, tag: str) -> str:
    """Expand a witnessed signed residue with twice-magnitude bound."""

    gap = f"fsd_center_bound_{tag}"
    lower_quotient = f"fsd_center_lower_{tag}"
    upper_quotient = f"fsd_center_upper_{tag}"
    return (
        f"((exists {gap}. {gap} + ({magnitude} + {magnitude}) = {modulus}) /\\ "
        f"((exists {lower_quotient}. "
        f"{value} = {modulus} * {lower_quotient} + {magnitude}) \\/ "
        f"(exists {upper_quotient}. "
        f"{value} + {magnitude} = {modulus} * {upper_quotient})))"
    )


def matching_parity(first: str, second: str, *, tag: str) -> str:
    """Expand the same-even or same-odd constructive parity alternatives."""

    first_even = f"fsd_even_first_{tag}"
    second_even = f"fsd_even_second_{tag}"
    first_odd = f"fsd_odd_first_{tag}"
    second_odd = f"fsd_odd_second_{tag}"
    return (
        f"(((exists {first_even}. {first} = 2 * {first_even}) /\\ "
        f"(exists {second_even}. {second} = 2 * {second_even})) \\/ "
        f"((exists {first_odd}. {first} = 2 * {first_odd} + 1) /\\ "
        f"(exists {second_odd}. {second} = 2 * {second_odd} + 1)))"
    )


def make_four_square_descent_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build checked quotient algebra and explicit multiplier induction."""

    inputs = ("a", "b", "c", "d", "e", "f", "g", "h")
    quotient_names = ("u", "v", "w", "x")
    contributions = _coordinate_contributions()
    divisibility_balances = tuple(
        _absolute_expression(positive, negative, f"(k * {quotient})")
        for (positive, negative), quotient in zip(
            contributions, quotient_names, strict=True
        )
    )
    norm_first = "a * a + b * b + c * c + d * d"
    norm_second = "e * e + f * f + g * g + h * h"
    quotient_norm = "u * u + v * v + w * w + x * x"
    scaled_norm = " + ".join(
        f"(k * {quotient}) * (k * {quotient})" for quotient in quotient_names
    )
    prime_p = prime("p", tag="fsd_p")
    prime_multiple = four_square_representation("p * k", tag="fsd_multiple")
    prime_result = four_square_representation("p", tag="fsd_prime_result")
    strict_step = _strict_step(tag="universal")
    seed_family = _three_mod_four_seeds(tag="universal")
    bad_prime_family = (
        "forall p. "
        f"({prime('p', tag='fsd_bad_prime')}) -> "
        "(exists t. p = 4 * t + 3) -> "
        f"({four_square_representation('p', tag='fsd_bad_result')})"
    )
    induction_bound = "exists fsd_bound. fsd_bound + k = B"
    strict_result = (
        "exists r. (~(r = 0) /\\ "
        "((exists fsd_strict_gap. fsd_strict_gap + S r = k) /\\ "
        f"({four_square_representation('p * r', tag='fsd_strict_result')})))"
    )

    return (
        spec(
            FOUR_SQUARE_DESCENT_NONZERO_SQUARE,
            "forall k. ~(k = 0) -> ~(k * k = 0)",
            ("mul_eq_zero",),
            (
                "intro k",
                "intro hnonzero",
                "intro hproduct",
                "specialize mul_eq_zero k",
                "specialize mul_eq_zero k",
                "have hcases : k = 0 \\/ k = 0",
                "apply mul_eq_zero",
                "exact hproduct",
                "cases hcases",
                "apply hnonzero",
                "exact hcases_left",
                "apply hnonzero",
                "exact hcases_right",
            ),
            "The square of a nonzero natural multiplier remains nonzero constructively.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_PRODUCT_REASSOCIATE,
            "forall p k r. (p * k) * (k * r) = (k * k) * (p * r)",
            ("mul_comm", "mul_shuffle_four"),
            (
                "intro p",
                "intro k",
                "intro r",
                "trans (k * p) * (k * r)",
                "congr",
                "apply mul_comm",
                "refl",
                "apply mul_shuffle_four",
            ),
            "The product of two k-divisible norms exposes its exact common square factor k².",
        ),
        spec(
            FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM,
            f"forall k {' '.join(quotient_names)}. "
            f"({scaled_norm}) = (k * k) * ({quotient_norm})",
            ("four_square_product_square", "mul_add"),
            (
                "intro k",
                "intro u",
                "intro v",
                "intro w",
                "intro x",
                "trans (k * k) * (u * u) + (k * k) * (v * v) + "
                "(k * k) * (w * w) + (k * k) * (x * x)",
                "congr",
                "congr",
                "congr",
                "apply four_square_product_square",
                "apply four_square_product_square",
                "apply four_square_product_square",
                "apply four_square_product_square",
                "symm",
                "simp [mul_add]",
            ),
            "Four coordinates each divisible by k have a norm exactly divisible by the natural square k².",
        ),
        spec(
            FOUR_SQUARE_DESCENT_SQUARE_FACTOR_CANCEL,
            "forall k s t. ~(k = 0) -> "
            "(k * k) * s = (k * k) * t -> s = t",
            (
                FOUR_SQUARE_DESCENT_NONZERO_SQUARE,
                "mul_left_cancel_nonzero",
            ),
            (
                "intro k",
                "intro s",
                "intro t",
                "intro hnonzero",
                "intro hequality",
                "specialize mul_left_cancel_nonzero (k * k)",
                "specialize mul_left_cancel_nonzero s",
                "specialize mul_left_cancel_nonzero t",
                "apply mul_left_cancel_nonzero",
                "specialize four_square_descent_nonzero_square k",
                "intro hsquare",
                "apply four_square_descent_nonzero_square",
                "exact hnonzero",
                "exact hsquare",
                "exact hequality",
            ),
            "A nonzero natural square factor cancels without subtraction or division axioms.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT,
            f"forall p k r {' '.join(quotient_names)}. "
            f"~(k = 0) -> (p * k) * (k * r) = ({scaled_norm}) -> "
            f"p * r = ({quotient_norm})",
            (
                FOUR_SQUARE_DESCENT_PRODUCT_REASSOCIATE,
                FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM,
                FOUR_SQUARE_DESCENT_SQUARE_FACTOR_CANCEL,
            ),
            (
                "intro p",
                "intro k",
                "intro r",
                "intro u",
                "intro v",
                "intro w",
                "intro x",
                "intro hnonzero",
                "intro hnorm",
                "specialize four_square_descent_square_factor_cancel k",
                "specialize four_square_descent_square_factor_cancel (p * r)",
                f"specialize four_square_descent_square_factor_cancel ({quotient_norm})",
                "apply four_square_descent_square_factor_cancel",
                "exact hnonzero",
                "trans (p * k) * (k * r)",
                "symm",
                "apply four_square_descent_product_reassociate",
                f"trans {scaled_norm}",
                "exact hnorm",
                "apply four_square_descent_square_factor_norm",
            ),
            "An exact represented product of a prime multiple and a k-multiple descends through their common square factor.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT,
            f"forall p k r {' '.join(inputs)} {' '.join(quotient_names)}. "
            "~(k = 0) -> "
            f"p * k = ({norm_first}) -> "
            f"k * r = ({norm_second}) -> "
            f"({_conjunction(divisibility_balances)}) -> "
            f"p * r = ({quotient_norm})",
            (
                "four_square_euler_quaternion",
                FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT,
            ),
            tuple(f"intro {name}" for name in ("p", "k", "r", *inputs, *quotient_names))
            + ("intro hnonzero", "intro hfirst", "intro hsecond", "intro hbalances")
            + (
                f"have hnorm : ({norm_first}) * ({norm_second}) = ({scaled_norm})",
            )
            + tuple(
                f"specialize four_square_euler_quaternion {value}"
                for value in (*inputs, *(f"(k * {name})" for name in quotient_names))
            )
            + (
                "apply four_square_euler_quaternion",
                "exact hbalances",
                "rewrite <- hfirst at hnorm",
                "rewrite <- hsecond at hnorm",
                "apply four_square_descent_scaled_norm_quotient",
                "exact hnonzero",
                "exact hnorm",
            ),
            "A centered quaternion product whose four absolute coordinates are all k-divisible yields the exact four-square quotient p·r.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_STRICT_STEP_FROM_CENTERED_QUATERNION,
            f"forall p k r {' '.join(inputs)} {' '.join(quotient_names)}. "
            "~(k = 0) -> ~(r = 0) -> "
            "(exists fsd_center_gap. fsd_center_gap + S r = k) -> "
            f"p * k = ({norm_first}) -> "
            f"k * r = ({norm_second}) -> "
            f"({_conjunction(divisibility_balances)}) -> ({strict_result})",
            (FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT,),
            tuple(f"intro {name}" for name in ("p", "k", "r", *inputs, *quotient_names))
            + (
                "intro hk",
                "intro hr",
                "intro hstrict",
                "intro hfirst",
                "intro hsecond",
                "intro hbalances",
                "exists r",
                "split",
                "exact hr",
                "split",
                "exact hstrict",
                "exists u",
                "exists v",
                "exists w",
                "exists x",
                "apply four_square_descent_quaternion_quotient",
                "exact hk",
                "exact hfirst",
                "exact hsecond",
                "exact hbalances",
            ),
            "Every explicit centered nonzero quaternion certificate constructs a genuinely represented strictly smaller prime multiplier.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_MODULAR_SEED_MULTIPLIER_NONZERO,
            "forall p x y k. x * x + y * y + 1 = p * k -> ~(k = 0)",
            ("succ_ne_zero",),
            (
                "intro p",
                "intro x",
                "intro y",
                "intro k",
                "intro hseed",
                "intro hzero",
                "rewrite hzero at hseed",
                "rewrite PA5 at hseed",
                "specialize succ_ne_zero (x * x + y * y)",
                "apply succ_ne_zero",
                "trans x * x + y * y + 1",
                "symm",
                "simp",
                "exact hseed",
            ),
            "A modular seed x²+y²+1=p·k has a constructively nonzero multiplier because its left side is a successor.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED,
            f"forall B p k. ({induction_bound}) -> ({prime_p}) -> "
            f"~(k = 0) -> ({prime_multiple}) -> ({strict_step}) -> ({prime_result})",
            (
                "le_zero",
                "eq_decidable",
                "mul_one",
                "le_trans",
                "le_of_succ_le_succ",
            ),
            (
                "intro B",
                "induction B",
                "intro p",
                "intro k",
                "intro hbound",
                "intro hprime",
                "intro hnonzero",
                "intro hrepresented",
                "intro hstep",
                "exfalso",
                "apply hnonzero",
                "specialize le_zero k",
                "apply le_zero",
                "exact hbound",
                "intro p",
                "intro k",
                "intro hbound",
                "intro hprime",
                "intro hnonzero",
                "intro hrepresented",
                "intro hstep",
                "specialize eq_decidable k",
                "specialize eq_decidable 1",
                "cases eq_decidable",
                "rewrite eq_decidable_left at hrepresented",
                "specialize mul_one p",
                "rewrite mul_one at hrepresented",
                "exact hrepresented",
                "have hsmaller : "
                f"({strict_result})",
                "specialize hstep p",
                "specialize hstep k",
                "apply hstep",
                "exact hprime",
                "exact hnonzero",
                "exact eq_decidable_right",
                "exact hrepresented",
                "cases hsmaller",
                "cases hsmaller_witness",
                "cases hsmaller_witness_right",
                "have hsuccessor_bound : exists t. t + S x = S B",
                "specialize le_trans (S x)",
                "specialize le_trans k",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hsmaller_witness_right_left",
                "exact hbound",
                "have hsmaller_bound : exists t. t + x = B",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsuccessor_bound",
                "specialize IH p",
                "specialize IH x",
                "apply IH",
                "exact hsmaller_bound",
                "exact hprime",
                "exact hsmaller_witness_left",
                "exact hsmaller_witness_right_right",
                "exact hstep",
            ),
            "Bounded constructive induction on a nonzero represented multiplier terminates at one under an explicit strictly decreasing quaternion step.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_PRIME_FROM_STRICT_STEP,
            f"({strict_step}) -> forall p k. ({prime_p}) -> "
            f"~(k = 0) -> ({prime_multiple}) -> ({prime_result})",
            ("le_refl", FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED),
            (
                "intro hstep",
                "intro p",
                "intro k",
                "intro hprime",
                "intro hnonzero",
                "intro hrepresented",
                "specialize four_square_descent_strict_multiplier_bounded k",
                "specialize four_square_descent_strict_multiplier_bounded p",
                "specialize four_square_descent_strict_multiplier_bounded k",
                "apply four_square_descent_strict_multiplier_bounded",
                "specialize le_refl k",
                "exact le_refl",
                "exact hprime",
                "exact hnonzero",
                "exact hrepresented",
                "exact hstep",
            ),
            "Every nonzero represented prime multiple descends all the way to a representation of the prime under the precise strict-step hypothesis.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_PRIME_FROM_MODULAR_SEED_AND_STEP,
            f"({strict_step}) -> forall p x y k. ({prime_p}) -> "
            f"x * x + y * y + 1 = p * k -> ({prime_result})",
            (
                FOUR_SQUARE_DESCENT_MODULAR_SEED_MULTIPLIER_NONZERO,
                "four_square_prime_modular_seed_multiple",
                FOUR_SQUARE_DESCENT_PRIME_FROM_STRICT_STEP,
            ),
            (
                "intro hstep",
                "intro p",
                "intro x",
                "intro y",
                "intro k",
                "intro hprime",
                "intro hseed",
                "have hdescent : forall p k. "
                f"({prime('p', tag='fsd_local_prime')}) -> ~(k = 0) -> "
                f"({four_square_representation('p * k', tag='fsd_local_multiple')}) -> "
                f"({four_square_representation('p', tag='fsd_local_result')})",
                "apply four_square_descent_prime_from_strict_step",
                "exact hstep",
                "specialize hdescent p",
                "specialize hdescent k",
                "apply hdescent",
                "exact hprime",
                "specialize four_square_descent_modular_seed_multiplier_nonzero p",
                "specialize four_square_descent_modular_seed_multiplier_nonzero x",
                "specialize four_square_descent_modular_seed_multiplier_nonzero y",
                "specialize four_square_descent_modular_seed_multiplier_nonzero k",
                "intro hzero",
                "apply four_square_descent_modular_seed_multiplier_nonzero",
                "exact hseed",
                "exact hzero",
                "specialize four_square_prime_modular_seed_multiple p",
                "specialize four_square_prime_modular_seed_multiple x",
                "specialize four_square_prime_modular_seed_multiple y",
                "specialize four_square_prime_modular_seed_multiple k",
                "apply four_square_prime_modular_seed_multiple",
                "exact hseed",
            ),
            "A concrete modular square seed and the explicit strict multiplier step suffice for an actual representation of the prime.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_THREE_MOD_FOUR_PRIMES_FROM_SEED_AND_STEP,
            f"({seed_family}) -> ({strict_step}) -> ({bad_prime_family})",
            (FOUR_SQUARE_DESCENT_PRIME_FROM_MODULAR_SEED_AND_STEP,),
            (
                "intro hseeds",
                "intro hstep",
                "intro p",
                "intro hprime",
                "intro hclass",
                "specialize hseeds p",
                "have hseed : exists x y k. x * x + y * y + 1 = p * k",
                "apply hseeds",
                "exact hprime",
                "exact hclass",
                "cases hseed",
                "cases hseed_witness",
                "cases hseed_witness_witness",
                "have hseed_descent : forall p x y k. "
                f"({prime('p', tag='fsd_seed_local_prime')}) -> "
                "x * x + y * y + 1 = p * k -> "
                f"({four_square_representation('p', tag='fsd_seed_local_result')})",
                "apply four_square_descent_prime_from_modular_seed_and_step",
                "exact hstep",
                "specialize hseed_descent p",
                "specialize hseed_descent x",
                "specialize hseed_descent x1",
                "specialize hseed_descent x2",
                "apply hseed_descent",
                "exact hprime",
                "exact hseed_witness_witness_witness",
            ),
            "All remaining three-modulo-four primes are represented once their modular square seeds and the decreasing quaternion step are supplied.",
        ),
        spec(
            FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT,
            f"({seed_family}) -> ({strict_step}) -> "
            f"forall n. ({four_square_representation('n', tag='fsd_lagrange_result')})",
            (
                FOUR_SQUARE_DESCENT_THREE_MOD_FOUR_PRIMES_FROM_SEED_AND_STEP,
                "four_square_lagrange_from_three_mod_four_primes",
            ),
            (
                "intro hseeds",
                "intro hstep",
                "apply four_square_lagrange_from_three_mod_four_primes",
                "apply four_square_descent_three_mod_four_primes_from_seed_and_step",
                "exact hseeds",
                "exact hstep",
            ),
            "All-natural Lagrange follows by checked construction from exactly two explicit remaining premises: modular square seeds and strict centered-quaternion multiplier descent.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_REMAINDER_COMPLEMENT_EXISTS,
            "forall k n. ~(k = 0) -> exists q r s. "
            "((n = k * q + r) /\\ ((r + s = k) /\\ "
            "((exists t. t + r = s) \\/ (exists t. t + s = r))))",
            ("division_remainder_exists", "add_comm", "le_total"),
            (
                "intro k",
                "intro n",
                "intro hnonzero",
                "have hdivision : exists q r. "
                "((n = k * q + r) /\\ (exists t. t + S r = k))",
                "specialize division_remainder_exists k",
                "specialize division_remainder_exists n",
                "apply division_remainder_exists",
                "exact hnonzero",
                "cases hdivision",
                "cases hdivision_witness",
                "cases hdivision_witness_witness",
                "cases hdivision_witness_witness_right",
                "exists x",
                "exists x1",
                "exists S x2",
                "split",
                "exact hdivision_witness_witness_left",
                "split",
                "trans x2 + S x1",
                "trans S (x1 + x2)",
                "apply PA4",
                "trans S (x2 + x1)",
                "congr",
                "apply add_comm",
                "symm",
                "apply PA4",
                "exact hdivision_witness_witness_right_witness",
                "specialize le_total x1",
                "specialize le_total (S x2)",
                "exact le_total",
            ),
            "Every nonzero-modulus remainder has a complementary nonnegative residue and a decidable ordering between the two.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_CENTERED_SIGNED_REMAINDER_EXISTS,
            "forall k n. ~(k = 0) -> exists m. "
            f"({centered_signed_remainder('k', 'n', 'm', tag='single')})",
            (
                FOUR_SQUARE_DESCENT_REMAINDER_COMPLEMENT_EXISTS,
                "four_square_add_swap_right_tail",
                "add_assoc",
            ),
            (
                "intro k",
                "intro n",
                "intro hnonzero",
                "have hparts : exists q r s. "
                "((n = k * q + r) /\\ ((r + s = k) /\\ "
                "((exists t. t + r = s) \\/ (exists t. t + s = r))))",
                "specialize four_square_descent_remainder_complement_exists k",
                "specialize four_square_descent_remainder_complement_exists n",
                "apply four_square_descent_remainder_complement_exists",
                "exact hnonzero",
                "cases hparts",
                "cases hparts_witness",
                "cases hparts_witness_witness",
                "cases hparts_witness_witness_witness",
                "cases hparts_witness_witness_witness_right",
                "cases hparts_witness_witness_witness_right_right",
                "cases hparts_witness_witness_witness_right_right_left",
                "exists x1",
                "split",
                "exists x3",
                "trans x1 + (x3 + x1)",
                "apply four_square_add_swap_right_tail",
                "trans x1 + x2",
                "congr",
                "refl",
                "exact hparts_witness_witness_witness_right_right_left_witness",
                "exact hparts_witness_witness_witness_right_left",
                "left",
                "exists x",
                "exact hparts_witness_witness_witness_left",
                "cases hparts_witness_witness_witness_right_right_right",
                "exists x2",
                "split",
                "exists x3",
                "trans (x3 + x2) + x2",
                "symm",
                "apply add_assoc",
                "trans x1 + x2",
                "congr",
                "exact hparts_witness_witness_witness_right_right_right_witness",
                "refl",
                "exact hparts_witness_witness_witness_right_left",
                "right",
                "exists S x",
                "trans (k * x + x1) + x2",
                "congr",
                "exact hparts_witness_witness_witness_left",
                "refl",
                "trans k * x + (x1 + x2)",
                "apply add_assoc",
                "trans k * x + k",
                "congr",
                "refl",
                "exact hparts_witness_witness_witness_right_left",
                "symm",
                "apply PA6",
            ),
            "Every natural has a constructively chosen signed residue m with 2m≤k and either n=kq+m or n+m=kq.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_CENTERED_FOUR_REMAINDERS_EXIST,
            "forall k a b c d. ~(k = 0) -> exists e f g h. "
            f"({_conjunction(tuple(centered_signed_remainder('k', value, magnitude, tag=f'four_{index}') for index, (value, magnitude) in enumerate(zip('abcd', 'efgh', strict=True))))})",
            (FOUR_SQUARE_DESCENT_CENTERED_SIGNED_REMAINDER_EXISTS,),
            (
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnonzero",
                "have ha : exists e. "
                f"({centered_signed_remainder('k', 'a', 'e', tag='four_a')})",
                "specialize four_square_descent_centered_signed_remainder_exists k",
                "specialize four_square_descent_centered_signed_remainder_exists a",
                "apply four_square_descent_centered_signed_remainder_exists",
                "exact hnonzero",
                "have hb : exists f. "
                f"({centered_signed_remainder('k', 'b', 'f', tag='four_b')})",
                "apply four_square_descent_centered_signed_remainder_exists",
                "exact hnonzero",
                "have hc : exists g. "
                f"({centered_signed_remainder('k', 'c', 'g', tag='four_c')})",
                "apply four_square_descent_centered_signed_remainder_exists",
                "exact hnonzero",
                "have hd : exists h. "
                f"({centered_signed_remainder('k', 'd', 'h', tag='four_d')})",
                "apply four_square_descent_centered_signed_remainder_exists",
                "exact hnonzero",
                "cases ha",
                "cases hb",
                "cases hc",
                "cases hd",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact ha_witness",
                "split",
                "exact hb_witness",
                "split",
                "exact hc_witness",
                "exact hd_witness",
            ),
            "Every four-coordinate natural quaternion admits four independent constructively chosen centered signed remainders.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER,
            "forall k r z. k * r = z -> "
            "(exists gap. gap + S z = k * k) -> "
            "exists gap. gap + S r = k",
            ("le_or_lt", "mul_le_mul_left", "lt_not_le"),
            (
                "intro k",
                "intro r",
                "intro z",
                "intro hnorm",
                "intro hbound",
                "specialize le_or_lt k",
                "specialize le_or_lt r",
                "cases le_or_lt",
                "exfalso",
                "have hscaled : exists t. t + k * k = k * r",
                "specialize mul_le_mul_left k",
                "specialize mul_le_mul_left r",
                "specialize mul_le_mul_left k",
                "apply mul_le_mul_left",
                "exact le_or_lt_left",
                "rewrite hnorm at hscaled",
                "specialize lt_not_le z",
                "specialize lt_not_le (k * k)",
                "apply lt_not_le",
                "exact hbound",
                "exact hscaled",
                "exact le_or_lt_right",
            ),
            "A centered quaternion norm k·r strictly below k² forces its quotient r to be strictly smaller than k.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_MATCHING_PARITY_SUM_EVEN,
            "forall a b. "
            f"({matching_parity('a', 'b', tag='sum')}) -> "
            "exists u. a + b = 2 * u",
            ("even_sum_iff_same_parity",),
            (
                "intro a",
                "intro b",
                "intro hmatching",
                "specialize even_sum_iff_same_parity a",
                "specialize even_sum_iff_same_parity b",
                "cases even_sum_iff_same_parity",
                "apply even_sum_iff_same_parity_right",
                "exact hmatching",
            ),
            "A pair of natural coordinates with matching constructive parity has an explicitly even sum.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_MATCHING_PARITY_ABSOLUTE_EVEN,
            "forall a b. "
            f"({matching_parity('a', 'b', tag='absolute')}) -> "
            "exists v. ((a = b + 2 * v) \\/ (b = a + 2 * v))",
            (
                "four_square_absolute_difference_total",
                "mul_add",
                "four_square_euler_add_swap_last",
            ),
            (
                "intro a",
                "intro b",
                "intro hmatching",
                "cases hmatching",
                "cases hmatching_left",
                "cases hmatching_left_left",
                "cases hmatching_left_right",
                "have hgap : exists v. x = x1 + v \\/ x1 = x + v",
                "apply four_square_absolute_difference_total",
                "cases hgap",
                "exists x2",
                "cases hgap_witness",
                "left",
                "rewrite hmatching_left_left_witness",
                "rewrite hmatching_left_right_witness",
                "rewrite hgap_witness_left",
                "apply mul_add",
                "right",
                "rewrite hmatching_left_right_witness",
                "rewrite hmatching_left_left_witness",
                "rewrite hgap_witness_right",
                "apply mul_add",
                "cases hmatching_right",
                "cases hmatching_right_left",
                "cases hmatching_right_right",
                "have hgap : exists v. x = x1 + v \\/ x1 = x + v",
                "apply four_square_absolute_difference_total",
                "cases hgap",
                "exists x2",
                "cases hgap_witness",
                "left",
                "rewrite hmatching_right_left_witness",
                "rewrite hmatching_right_right_witness",
                "rewrite hgap_witness_left",
                "trans (2 * x1 + 2 * x2) + 1",
                "congr",
                "apply mul_add",
                "refl",
                "apply four_square_euler_add_swap_last",
                "right",
                "rewrite hmatching_right_right_witness",
                "rewrite hmatching_right_left_witness",
                "rewrite hgap_witness_right",
                "trans (2 * x + 2 * x2) + 1",
                "congr",
                "apply mul_add",
                "refl",
                "apply four_square_euler_add_swap_last",
            ),
            "Matching even or odd coordinate witnesses construct an explicitly even absolute difference without subtraction.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_DOUBLE_PAIR_IDENTITY,
            "forall a b c d v x. "
            "(a = b + 2 * v \\/ b = a + 2 * v) -> "
            "(c = d + 2 * x \\/ d = c + 2 * x) -> "
            "(a * a + b * b + c * c + d * d) * 2 = "
            "(((a + b) * (a + b) + (2 * v) * (2 * v)) + "
            "((c + d) * (c + d) + (2 * x) * (2 * x)))",
            (
                "four_square_two_square_factor_identity",
                "zero_add",
                "mul_one",
            ),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro v",
                "intro x",
                "intro hfirst",
                "intro hsecond",
                "have hidentity : "
                "(a * a + b * b + c * c + d * d) * (1 * 1 + 1 * 1) = "
                "(((a * 1 + b * 1) * (a * 1 + b * 1) + "
                "(2 * v) * (2 * v)) + "
                "((c * 1 + d * 1) * (c * 1 + d * 1) + "
                "(2 * x) * (2 * x)))",
                "specialize four_square_two_square_factor_identity a",
                "specialize four_square_two_square_factor_identity b",
                "specialize four_square_two_square_factor_identity c",
                "specialize four_square_two_square_factor_identity d",
                "specialize four_square_two_square_factor_identity 1",
                "specialize four_square_two_square_factor_identity 1",
                "specialize four_square_two_square_factor_identity (2 * v)",
                "specialize four_square_two_square_factor_identity (2 * x)",
                "apply four_square_two_square_factor_identity",
                "cases hfirst",
                "left",
                "simp [zero_add]",
                "right",
                "simp [zero_add]",
                "cases hsecond",
                "left",
                "simp [zero_add]",
                "right",
                "simp [zero_add]",
                "have htwo : 1 * 1 + 1 * 1 = 2",
                "norm_num",
                "rewrite htwo at hidentity",
                "have haone : a * 1 = a",
                "apply mul_one",
                "rewrite haone at hidentity",
                "rewrite haone at hidentity",
                "have hbone : b * 1 = b",
                "apply mul_one",
                "rewrite hbone at hidentity",
                "rewrite hbone at hidentity",
                "have hcone : c * 1 = c",
                "apply mul_one",
                "rewrite hcone at hidentity",
                "rewrite hcone at hidentity",
                "have hdone : d * 1 = d",
                "apply mul_one",
                "rewrite hdone at hidentity",
                "rewrite hdone at hidentity",
                "exact hidentity",
            ),
            "Multiplication by the two-square norm 1²+1² gives a fully explicit paired four-square doubling identity.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_PAIRED_HALVING,
            "forall p a b c d u v w x. "
            "p * 2 = a * a + b * b + c * c + d * d -> "
            "a + b = 2 * u -> "
            "(a = b + 2 * v \\/ b = a + 2 * v) -> "
            "c + d = 2 * w -> "
            "(c = d + 2 * x \\/ d = c + 2 * x) -> "
            f"({four_square_representation('p', tag='even_paired')})",
            (
                FOUR_SQUARE_DESCENT_DOUBLE_PAIR_IDENTITY,
                FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT,
                "mul_one",
                "add_assoc",
                "succ_ne_zero",
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro u",
                "intro v",
                "intro w",
                "intro x",
                "intro hnorm",
                "intro hsumfirst",
                "intro hgapfirst",
                "intro hsumsecond",
                "intro hgapsecond",
                "have hidentity : "
                "(a * a + b * b + c * c + d * d) * 2 = "
                "(((a + b) * (a + b) + (2 * v) * (2 * v)) + "
                "((c + d) * (c + d) + (2 * x) * (2 * x)))",
                "specialize four_square_descent_double_pair_identity a",
                "specialize four_square_descent_double_pair_identity b",
                "specialize four_square_descent_double_pair_identity c",
                "specialize four_square_descent_double_pair_identity d",
                "specialize four_square_descent_double_pair_identity v",
                "specialize four_square_descent_double_pair_identity x",
                "apply four_square_descent_double_pair_identity",
                "exact hgapfirst",
                "exact hgapsecond",
                "rewrite hsumfirst at hidentity",
                "rewrite hsumfirst at hidentity",
                "rewrite hsumsecond at hidentity",
                "rewrite hsumsecond at hidentity",
                "have hscaled : (p * 2) * (2 * 1) = "
                "(2 * u) * (2 * u) + (2 * v) * (2 * v) + "
                "(2 * w) * (2 * w) + (2 * x) * (2 * x)",
                "trans (a * a + b * b + c * c + d * d) * 2",
                "congr",
                "exact hnorm",
                "apply mul_one",
                "trans (((2 * u) * (2 * u) + (2 * v) * (2 * v)) + "
                "((2 * w) * (2 * w) + (2 * x) * (2 * x)))",
                "exact hidentity",
                "symm",
                "apply add_assoc",
                "exists u",
                "exists v",
                "exists w",
                "exists x",
                "trans p * 1",
                "symm",
                "apply mul_one",
                "specialize four_square_descent_scaled_norm_quotient p",
                "specialize four_square_descent_scaled_norm_quotient 2",
                "specialize four_square_descent_scaled_norm_quotient 1",
                "specialize four_square_descent_scaled_norm_quotient u",
                "specialize four_square_descent_scaled_norm_quotient v",
                "specialize four_square_descent_scaled_norm_quotient w",
                "specialize four_square_descent_scaled_norm_quotient x",
                "apply four_square_descent_scaled_norm_quotient",
                "intro hzero",
                "specialize succ_ne_zero 1",
                "apply succ_ne_zero",
                "exact hzero",
                "exact hscaled",
            ),
            "An actually represented double p·2 descends unconditionally to p when its four coordinates are supplied as two matching-parity pairs.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING,
            "forall p a b c d. "
            "p * 2 = a * a + b * b + c * c + d * d -> "
            f"({matching_parity('a', 'b', tag='halve_first')}) -> "
            f"({matching_parity('c', 'd', tag='halve_second')}) -> "
            f"({four_square_representation('p', tag='even_matching')})",
            (
                FOUR_SQUARE_DESCENT_MATCHING_PARITY_SUM_EVEN,
                FOUR_SQUARE_DESCENT_MATCHING_PARITY_ABSOLUTE_EVEN,
                FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_PAIRED_HALVING,
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnorm",
                "intro hfirst",
                "intro hsecond",
                "have hsumfirst : exists u. a + b = 2 * u",
                "specialize four_square_descent_matching_parity_sum_even a",
                "specialize four_square_descent_matching_parity_sum_even b",
                "apply four_square_descent_matching_parity_sum_even",
                "exact hfirst",
                "cases hsumfirst",
                "have hgapfirst : exists v. "
                "((a = b + 2 * v) \\/ (b = a + 2 * v))",
                "specialize four_square_descent_matching_parity_absolute_even a",
                "specialize four_square_descent_matching_parity_absolute_even b",
                "apply four_square_descent_matching_parity_absolute_even",
                "exact hfirst",
                "cases hgapfirst",
                "have hsumsecond : exists w. c + d = 2 * w",
                "apply four_square_descent_matching_parity_sum_even",
                "exact hsecond",
                "cases hsumsecond",
                "have hgapsecond : exists z. "
                "((c = d + 2 * z) \\/ (d = c + 2 * z))",
                "apply four_square_descent_matching_parity_absolute_even",
                "exact hsecond",
                "cases hgapsecond",
                "specialize four_square_descent_even_multiplier_paired_halving p",
                "specialize four_square_descent_even_multiplier_paired_halving a",
                "specialize four_square_descent_even_multiplier_paired_halving b",
                "specialize four_square_descent_even_multiplier_paired_halving c",
                "specialize four_square_descent_even_multiplier_paired_halving d",
                "specialize four_square_descent_even_multiplier_paired_halving x",
                "specialize four_square_descent_even_multiplier_paired_halving x1",
                "specialize four_square_descent_even_multiplier_paired_halving x2",
                "specialize four_square_descent_even_multiplier_paired_halving x3",
                "apply four_square_descent_even_multiplier_paired_halving",
                "exact hnorm",
                "exact hsumfirst_witness",
                "exact hgapfirst_witness",
                "exact hsumsecond_witness",
                "exact hgapsecond_witness",
            ),
            "Any represented even multiplier with two constructively matching-parity coordinate pairs has a fully checked four-square half representation.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ODD_CENTERED_MAGNITUDE_HALF_BOUND,
            "forall h m. "
            "(exists gap. gap + (m + m) = 2 * h + 1) -> "
            "exists gap. gap + m = h",
            (
                "le_eq_or_lt",
                "even_odd_exclusive_pointwise",
                "two_mul_eq_add_self",
                "le_of_succ_le_succ",
                "mul_le_cancel_left_nonzero",
                "succ_ne_zero",
            ),
            (
                "intro h",
                "intro m",
                "intro hbound",
                "specialize le_eq_or_lt (m + m)",
                "specialize le_eq_or_lt (2 * h + 1)",
                "have hsplit : "
                "m + m = 2 * h + 1 \\/ "
                "(exists gap. gap + S (m + m) = 2 * h + 1)",
                "apply le_eq_or_lt",
                "exact hbound",
                "cases hsplit",
                "exfalso",
                "specialize even_odd_exclusive_pointwise (m + m)",
                "specialize even_odd_exclusive_pointwise m",
                "specialize even_odd_exclusive_pointwise h",
                "apply even_odd_exclusive_pointwise",
                "symm",
                "apply two_mul_eq_add_self",
                "exact hsplit_left",
                "have hone : 2 * h + 1 = S (2 * h)",
                "simp",
                "rewrite hone at hsplit_right",
                "have hdouble : exists gap. gap + (m + m) = 2 * h",
                "specialize le_of_succ_le_succ (m + m)",
                "specialize le_of_succ_le_succ (2 * h)",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "have hscaled : exists gap. gap + 2 * m = 2 * h",
                "cases hdouble",
                "exists x",
                "trans x + (m + m)",
                "congr",
                "refl",
                "apply two_mul_eq_add_self",
                "exact hdouble_witness",
                "specialize mul_le_cancel_left_nonzero 2",
                "specialize mul_le_cancel_left_nonzero m",
                "specialize mul_le_cancel_left_nonzero h",
                "apply mul_le_cancel_left_nonzero",
                "intro hzero",
                "specialize succ_ne_zero 1",
                "apply succ_ne_zero",
                "exact hzero",
                "exact hscaled",
            ),
            "For an odd modulus 2h+1, the constructive centered bound m+m≤2h+1 implies the sharp half-range bound m≤h.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ADD_LE_ADD,
            "forall a b c d. "
            "(exists gap. gap + a = b) -> "
            "(exists gap. gap + c = d) -> "
            "exists gap. gap + (a + c) = b + d",
            ("add_shuffle_middle",),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hfirst",
                "intro hsecond",
                "cases hfirst",
                "cases hsecond",
                "exists x + x1",
                "trans (x + a) + (x1 + c)",
                "apply add_shuffle_middle",
                "congr",
                "exact hfirst_witness",
                "exact hsecond_witness",
            ),
            "Two explicitly witnessed natural weak inequalities add constructively.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_DOUBLE_SQUARE_FOUR_SUM,
            "forall h. "
            "(2 * h) * (2 * h) = "
            "(h * h + h * h) + (h * h + h * h)",
            (
                "four_square_product_square",
                "four_mul_eq_double_double",
                "two_mul_eq_add_self",
            ),
            (
                "intro h",
                "trans (2 * 2) * (h * h)",
                "apply four_square_product_square",
                "trans 4 * (h * h)",
                "congr",
                "norm_num",
                "refl",
                "trans 2 * (2 * (h * h))",
                "apply four_mul_eq_double_double",
                "trans (2 * (h * h)) + (2 * (h * h))",
                "apply two_mul_eq_add_self",
                "congr",
                "apply two_mul_eq_add_self",
                "apply two_mul_eq_add_self",
            ),
            "The square of the doubled odd half is exactly four copies of the half-square.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT,
            "forall h a b c d. "
            "(exists gap. gap + a = h) -> "
            "(exists gap. gap + b = h) -> "
            "(exists gap. gap + c = h) -> "
            "(exists gap. gap + d = h) -> "
            "exists gap. gap + S (a * a + b * b + c * c + d * d) = "
            "(2 * h + 1) * (2 * h + 1)",
            (
                "mul_le_mul",
                FOUR_SQUARE_DESCENT_ADD_LE_ADD,
                "add_assoc",
                FOUR_SQUARE_DESCENT_DOUBLE_SQUARE_FOUR_SUM,
                "lt_of_le_of_lt",
                "square_lt_successor_square",
            ),
            (
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                "have hsa : exists gap. gap + a * a = h * h",
                "apply mul_le_mul",
                "exact ha",
                "exact ha",
                "have hsb : exists gap. gap + b * b = h * h",
                "apply mul_le_mul",
                "exact hb",
                "exact hb",
                "have hsc : exists gap. gap + c * c = h * h",
                "apply mul_le_mul",
                "exact hc",
                "exact hc",
                "have hsd : exists gap. gap + d * d = h * h",
                "apply mul_le_mul",
                "exact hd",
                "exact hd",
                "have hab : exists gap. "
                "gap + (a * a + b * b) = h * h + h * h",
                "apply four_square_descent_add_le_add",
                "exact hsa",
                "exact hsb",
                "have hcd : exists gap. "
                "gap + (c * c + d * d) = h * h + h * h",
                "apply four_square_descent_add_le_add",
                "exact hsc",
                "exact hsd",
                "have hpaired : exists gap. "
                "gap + ((a * a + b * b) + (c * c + d * d)) = "
                "(h * h + h * h) + (h * h + h * h)",
                "apply four_square_descent_add_le_add",
                "exact hab",
                "exact hcd",
                "have hnorm : exists gap. "
                "gap + (a * a + b * b + c * c + d * d) = "
                "(2 * h) * (2 * h)",
                "cases hpaired",
                "exists x",
                "trans x + ((a * a + b * b) + (c * c + d * d))",
                "congr",
                "refl",
                "apply add_assoc",
                "trans (h * h + h * h) + (h * h + h * h)",
                "exact hpaired_witness",
                "symm",
                "apply four_square_descent_double_square_four_sum",
                "have hone : 2 * h + 1 = S (2 * h)",
                "simp",
                "rewrite hone",
                "rewrite hone",
                "specialize lt_of_le_of_lt (a * a + b * b + c * c + d * d)",
                "specialize lt_of_le_of_lt ((2 * h) * (2 * h))",
                "specialize lt_of_le_of_lt (S (2 * h) * S (2 * h))",
                "apply lt_of_le_of_lt",
                "exact hnorm",
                "apply square_lt_successor_square",
            ),
            "Four coordinates in the odd half interval have norm strictly below the square of the full odd modulus.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ODD_CENTERED_NORM_STRICT,
            "forall k h a b c d e f g j. k = 2 * h + 1 -> "
            f"({centered_signed_remainder('k', 'a', 'e', tag='odd_a')}) -> "
            f"({centered_signed_remainder('k', 'b', 'f', tag='odd_b')}) -> "
            f"({centered_signed_remainder('k', 'c', 'g', tag='odd_c')}) -> "
            f"({centered_signed_remainder('k', 'd', 'j', tag='odd_d')}) -> "
            "exists gap. gap + S (e * e + f * f + g * g + j * j) = k * k",
            (
                FOUR_SQUARE_DESCENT_ODD_CENTERED_MAGNITUDE_HALF_BOUND,
                FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT,
            ),
            (
                "intro k",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro j",
                "intro hmodulus",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                "cases ha",
                "cases hb",
                "cases hc",
                "cases hd",
                "rewrite hmodulus",
                "rewrite hmodulus",
                "apply four_square_descent_odd_half_norm_strict",
                "specialize four_square_descent_odd_centered_magnitude_half_bound h",
                "specialize four_square_descent_odd_centered_magnitude_half_bound e",
                "apply four_square_descent_odd_centered_magnitude_half_bound",
                "rewrite <- hmodulus",
                "exact ha_left",
                "apply four_square_descent_odd_centered_magnitude_half_bound",
                "rewrite <- hmodulus",
                "exact hb_left",
                "apply four_square_descent_odd_centered_magnitude_half_bound",
                "rewrite <- hmodulus",
                "exact hc_left",
                "apply four_square_descent_odd_centered_magnitude_half_bound",
                "rewrite <- hmodulus",
                "exact hd_left",
            ),
            "All four actual centered signed residues modulo any odd multiplier have norm strictly below its square, independently of their sign choices.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ZERO_NORM_COORDINATES,
            "forall a b c d. a * a + b * b + c * c + d * d = 0 -> "
            "(a = 0 /\\ (b = 0 /\\ (c = 0 /\\ d = 0)))",
            ("add_eq_zero_components", "mul_eq_zero"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hnorm",
                "have hfirst : "
                "((a * a + b * b + c * c = 0) /\\ (d * d = 0))",
                "apply add_eq_zero_components",
                "exact hnorm",
                "cases hfirst",
                "have hsecond : ((a * a + b * b = 0) /\\ (c * c = 0))",
                "apply add_eq_zero_components",
                "exact hfirst_left",
                "cases hsecond",
                "have hthird : ((a * a = 0) /\\ (b * b = 0))",
                "apply add_eq_zero_components",
                "exact hsecond_left",
                "cases hthird",
                "have ha : a = 0 \\/ a = 0",
                "apply mul_eq_zero",
                "exact hthird_left",
                "have hb : b = 0 \\/ b = 0",
                "apply mul_eq_zero",
                "exact hthird_right",
                "have hc : c = 0 \\/ c = 0",
                "apply mul_eq_zero",
                "exact hsecond_right",
                "have hd : d = 0 \\/ d = 0",
                "apply mul_eq_zero",
                "exact hfirst_right",
                "split",
                "cases ha",
                "exact ha_left",
                "exact ha_right",
                "split",
                "cases hb",
                "exact hb_left",
                "exact hb_right",
                "split",
                "cases hc",
                "exact hc_left",
                "exact hc_right",
                "cases hd",
                "exact hd_left",
                "exact hd_right",
            ),
            "A zero natural four-square norm forces all four coordinates to vanish constructively.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ZERO_CENTERED_REMAINDER_DIVIDES,
            "forall k a. "
            f"({centered_signed_remainder('k', 'a', '0', tag='zero')}) -> "
            "exists q. a = k * q",
            (),
            (
                "intro k",
                "intro a",
                "intro hcenter",
                "cases hcenter",
                "cases hcenter_right",
                "cases hcenter_right_left",
                "exists x",
                "rewrite PA3 at hcenter_right_left_witness",
                "exact hcenter_right_left_witness",
                "cases hcenter_right_right",
                "exists x",
                "rewrite PA3 at hcenter_right_right_witness",
                "exact hcenter_right_right_witness",
            ),
            "A coordinate with centered magnitude zero is an actual natural multiple of the modulus in either signed-remainder branch.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_NONUNIT_PROPER_FACTOR_NOT_PRIME,
            f"forall p k q. ({prime_p}) -> ~(k = 1) -> "
            "(exists gap. gap + S k = p) -> ~(p = k * q)",
            ("mul_one", "lt_irrefl_expanded"),
            (
                "intro p",
                "intro k",
                "intro q",
                "intro hprime",
                "intro hnonunit",
                "intro hproper",
                "intro hfactor",
                "cases hprime",
                "specialize hprime_right k",
                "specialize hprime_right q",
                "have hcases : k = 1 \\/ q = 1",
                "apply hprime_right",
                "exact hfactor",
                "cases hcases",
                "apply hnonunit",
                "exact hcases_left",
                "rewrite hcases_right at hfactor",
                "specialize mul_one k",
                "rewrite mul_one at hfactor",
                "rewrite hfactor at hproper",
                "specialize lt_irrefl_expanded k",
                "apply lt_irrefl_expanded",
                "exact hproper",
            ),
            "A prime has no divisor k that is simultaneously nonunit and strictly smaller than the prime.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_DIVISIBLE_COORDINATES_PRIME_FACTOR,
            "forall p k a b c d u v w x. ~(k = 0) -> "
            "p * k = a * a + b * b + c * c + d * d -> "
            "a = k * u -> b = k * v -> c = k * w -> d = k * x -> "
            "p = k * (u * u + v * v + w * w + x * x)",
            (
                "mul_left_cancel_nonzero",
                "mul_comm",
                FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM,
                "mul_assoc",
            ),
            (
                "intro p",
                "intro k",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro u",
                "intro v",
                "intro w",
                "intro x",
                "intro hnonzero",
                "intro hnorm",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                "rewrite ha at hnorm",
                "rewrite ha at hnorm",
                "rewrite hb at hnorm",
                "rewrite hb at hnorm",
                "rewrite hc at hnorm",
                "rewrite hc at hnorm",
                "rewrite hd at hnorm",
                "rewrite hd at hnorm",
                "specialize mul_left_cancel_nonzero k",
                "specialize mul_left_cancel_nonzero p",
                "specialize mul_left_cancel_nonzero "
                "(k * (u * u + v * v + w * w + x * x))",
                "apply mul_left_cancel_nonzero",
                "exact hnonzero",
                "trans p * k",
                "apply mul_comm",
                "trans (k * u) * (k * u) + (k * v) * (k * v) + "
                "(k * w) * (k * w) + (k * x) * (k * x)",
                "exact hnorm",
                "trans (k * k) * (u * u + v * v + w * w + x * x)",
                "apply four_square_descent_square_factor_norm",
                "apply mul_assoc",
            ),
            "If all four coordinates of a represented prime multiple are k-divisible, square-factor cancellation makes k an actual divisor of the prime.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO,
            "forall p k r a b c d e f g j. "
            f"({prime_p}) -> ~(k = 0) -> ~(k = 1) -> "
            "(exists gap. gap + S k = p) -> "
            "p * k = a * a + b * b + c * c + d * d -> "
            f"({centered_signed_remainder('k', 'a', 'e', tag='nonzero_a')}) -> "
            f"({centered_signed_remainder('k', 'b', 'f', tag='nonzero_b')}) -> "
            f"({centered_signed_remainder('k', 'c', 'g', tag='nonzero_c')}) -> "
            f"({centered_signed_remainder('k', 'd', 'j', tag='nonzero_d')}) -> "
            "k * r = e * e + f * f + g * g + j * j -> ~(r = 0)",
            (
                FOUR_SQUARE_DESCENT_ZERO_NORM_COORDINATES,
                FOUR_SQUARE_DESCENT_ZERO_CENTERED_REMAINDER_DIVIDES,
                FOUR_SQUARE_DESCENT_DIVISIBLE_COORDINATES_PRIME_FACTOR,
                FOUR_SQUARE_DESCENT_NONUNIT_PROPER_FACTOR_NOT_PRIME,
            ),
            (
                "intro p",
                "intro k",
                "intro r",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro j",
                "intro hprime",
                "intro hk",
                "intro hnonunit",
                "intro hproper",
                "intro hnorm",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                "intro hcenter_norm",
                "intro hrzero",
                "rewrite hrzero at hcenter_norm",
                "rewrite PA5 at hcenter_norm",
                "have hzeros : "
                "(e = 0 /\\ (f = 0 /\\ (g = 0 /\\ j = 0)))",
                "apply four_square_descent_zero_norm_coordinates",
                "symm",
                "exact hcenter_norm",
                "cases hzeros",
                "cases hzeros_right",
                "cases hzeros_right_right",
                "rewrite hzeros_left at ha",
                "rewrite hzeros_left at ha",
                "rewrite hzeros_left at ha",
                "rewrite hzeros_left at ha",
                "rewrite hzeros_right_left at hb",
                "rewrite hzeros_right_left at hb",
                "rewrite hzeros_right_left at hb",
                "rewrite hzeros_right_left at hb",
                "rewrite hzeros_right_right_left at hc",
                "rewrite hzeros_right_right_left at hc",
                "rewrite hzeros_right_right_left at hc",
                "rewrite hzeros_right_right_left at hc",
                "rewrite hzeros_right_right_right at hd",
                "rewrite hzeros_right_right_right at hd",
                "rewrite hzeros_right_right_right at hd",
                "rewrite hzeros_right_right_right at hd",
                "have hda : exists q. a = k * q",
                "apply four_square_descent_zero_centered_remainder_divides",
                "exact ha",
                "have hdb : exists q. b = k * q",
                "apply four_square_descent_zero_centered_remainder_divides",
                "exact hb",
                "have hdc : exists q. c = k * q",
                "apply four_square_descent_zero_centered_remainder_divides",
                "exact hc",
                "have hdd : exists q. d = k * q",
                "apply four_square_descent_zero_centered_remainder_divides",
                "exact hd",
                "cases hda",
                "cases hdb",
                "cases hdc",
                "cases hdd",
                "have hfactor : "
                "p = k * (x * x + x1 * x1 + x2 * x2 + x3 * x3)",
                "specialize four_square_descent_divisible_coordinates_prime_factor p",
                "specialize four_square_descent_divisible_coordinates_prime_factor k",
                "specialize four_square_descent_divisible_coordinates_prime_factor a",
                "specialize four_square_descent_divisible_coordinates_prime_factor b",
                "specialize four_square_descent_divisible_coordinates_prime_factor c",
                "specialize four_square_descent_divisible_coordinates_prime_factor d",
                "specialize four_square_descent_divisible_coordinates_prime_factor x",
                "specialize four_square_descent_divisible_coordinates_prime_factor x1",
                "specialize four_square_descent_divisible_coordinates_prime_factor x2",
                "specialize four_square_descent_divisible_coordinates_prime_factor x3",
                "apply four_square_descent_divisible_coordinates_prime_factor",
                "exact hk",
                "exact hnorm",
                "exact hda_witness",
                "exact hdb_witness",
                "exact hdc_witness",
                "exact hdd_witness",
                "specialize four_square_descent_nonunit_proper_factor_not_prime p",
                "specialize four_square_descent_nonunit_proper_factor_not_prime k",
                "specialize four_square_descent_nonunit_proper_factor_not_prime "
                "(x * x + x1 * x1 + x2 * x2 + x3 * x3)",
                "apply four_square_descent_nonunit_proper_factor_not_prime",
                "exact hprime",
                "exact hnonunit",
                "exact hproper",
                "exact hfactor",
            ),
            "For a nonunit multiplier strictly below a prime, the centered quaternion norm quotient cannot vanish: otherwise all original coordinates would make the multiplier a forbidden prime divisor.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_ODD_CENTERED_STRICT_STEP,
            "forall p k h r a b c d e f g j. "
            f"({prime_p}) -> ~(k = 0) -> ~(k = 1) -> "
            "(exists gap. gap + S k = p) -> k = 2 * h + 1 -> "
            "p * k = a * a + b * b + c * c + d * d -> "
            f"({centered_signed_remainder('k', 'a', 'e', tag='odd_step_a')}) -> "
            f"({centered_signed_remainder('k', 'b', 'f', tag='odd_step_b')}) -> "
            f"({centered_signed_remainder('k', 'c', 'g', tag='odd_step_c')}) -> "
            f"({centered_signed_remainder('k', 'd', 'j', tag='odd_step_d')}) -> "
            "k * r = e * e + f * f + g * g + j * j -> "
            f"({four_square_representation('p * r', tag='odd_step_representation')}) -> "
            "exists s. (~(s = 0) /\\ "
            "((exists gap. gap + S s = k) /\\ "
            f"({four_square_representation('p * s', tag='odd_step_smaller')})))",
            (
                FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO,
                FOUR_SQUARE_DESCENT_ODD_CENTERED_NORM_STRICT,
                FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER,
            ),
            (
                "intro p",
                "intro k",
                "intro h",
                "intro r",
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro j",
                "intro hprime",
                "intro hk",
                "intro hnonunit",
                "intro hproper",
                "intro hodd",
                "intro hnorm",
                "intro ha",
                "intro hb",
                "intro hc",
                "intro hd",
                "intro hcenter_norm",
                "intro hrepresented",
                "have hnonzero : ~(r = 0)",
                "intro hrzero",
                "specialize four_square_descent_bounded_centered_quotient_nonzero p",
                "specialize four_square_descent_bounded_centered_quotient_nonzero k",
                "specialize four_square_descent_bounded_centered_quotient_nonzero r",
                "specialize four_square_descent_bounded_centered_quotient_nonzero a",
                "specialize four_square_descent_bounded_centered_quotient_nonzero b",
                "specialize four_square_descent_bounded_centered_quotient_nonzero c",
                "specialize four_square_descent_bounded_centered_quotient_nonzero d",
                "specialize four_square_descent_bounded_centered_quotient_nonzero e",
                "specialize four_square_descent_bounded_centered_quotient_nonzero f",
                "specialize four_square_descent_bounded_centered_quotient_nonzero g",
                "specialize four_square_descent_bounded_centered_quotient_nonzero j",
                "apply four_square_descent_bounded_centered_quotient_nonzero",
                "exact hprime",
                "exact hk",
                "exact hnonunit",
                "exact hproper",
                "exact hnorm",
                "exact ha",
                "exact hb",
                "exact hc",
                "exact hd",
                "exact hcenter_norm",
                "exact hrzero",
                "have hnormbound : "
                "exists gap. gap + S (e * e + f * f + g * g + j * j) = k * k",
                "specialize four_square_descent_odd_centered_norm_strict k",
                "specialize four_square_descent_odd_centered_norm_strict h",
                "specialize four_square_descent_odd_centered_norm_strict a",
                "specialize four_square_descent_odd_centered_norm_strict b",
                "specialize four_square_descent_odd_centered_norm_strict c",
                "specialize four_square_descent_odd_centered_norm_strict d",
                "specialize four_square_descent_odd_centered_norm_strict e",
                "specialize four_square_descent_odd_centered_norm_strict f",
                "specialize four_square_descent_odd_centered_norm_strict g",
                "specialize four_square_descent_odd_centered_norm_strict j",
                "apply four_square_descent_odd_centered_norm_strict",
                "exact hodd",
                "exact ha",
                "exact hb",
                "exact hc",
                "exact hd",
                "exists r",
                "split",
                "exact hnonzero",
                "split",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier k",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier r",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier "
                "(e * e + f * f + g * g + j * j)",
                "apply four_square_descent_norm_bound_forces_smaller_multiplier",
                "exact hcenter_norm",
                "exact hnormbound",
                "exact hrepresented",
            ),
            "For every proper nonunit odd prime multiplier, any represented signed centered quotient automatically gives a nonzero strictly smaller represented multiplier.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_DESCENT_CENTERED_FOUR_REMAINDERS_EXIST",
    "FOUR_SQUARE_DESCENT_CENTERED_SIGNED_REMAINDER_EXISTS",
    "FOUR_SQUARE_DESCENT_BOUNDED_CENTERED_QUOTIENT_NONZERO",
    "FOUR_SQUARE_DESCENT_ADD_LE_ADD",
    "FOUR_SQUARE_DESCENT_DOUBLE_SQUARE_FOUR_SUM",
    "FOUR_SQUARE_DESCENT_DIVISIBLE_COORDINATES_PRIME_FACTOR",
    "FOUR_SQUARE_DESCENT_DOUBLE_PAIR_IDENTITY",
    "FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_MATCHING_PARITY_HALVING",
    "FOUR_SQUARE_DESCENT_EVEN_MULTIPLIER_PAIRED_HALVING",
    "FOUR_SQUARE_DESCENT_MATCHING_PARITY_ABSOLUTE_EVEN",
    "FOUR_SQUARE_DESCENT_MATCHING_PARITY_SUM_EVEN",
    "FOUR_SQUARE_DESCENT_MODULAR_SEED_MULTIPLIER_NONZERO",
    "FOUR_SQUARE_DESCENT_NONZERO_SQUARE",
    "FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER",
    "FOUR_SQUARE_DESCENT_NONUNIT_PROPER_FACTOR_NOT_PRIME",
    "FOUR_SQUARE_DESCENT_ODD_CENTERED_MAGNITUDE_HALF_BOUND",
    "FOUR_SQUARE_DESCENT_ODD_CENTERED_NORM_STRICT",
    "FOUR_SQUARE_DESCENT_ODD_CENTERED_STRICT_STEP",
    "FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT",
    "FOUR_SQUARE_DESCENT_PRIME_FROM_MODULAR_SEED_AND_STEP",
    "FOUR_SQUARE_DESCENT_PRIME_FROM_STRICT_STEP",
    "FOUR_SQUARE_DESCENT_PRODUCT_REASSOCIATE",
    "FOUR_SQUARE_DESCENT_QUATERNION_QUOTIENT",
    "FOUR_SQUARE_DESCENT_REMAINDER_COMPLEMENT_EXISTS",
    "FOUR_SQUARE_DESCENT_SCALED_NORM_QUOTIENT",
    "FOUR_SQUARE_DESCENT_SQUARE_FACTOR_CANCEL",
    "FOUR_SQUARE_DESCENT_SQUARE_FACTOR_NORM",
    "FOUR_SQUARE_DESCENT_STRICT_MULTIPLIER_BOUNDED",
    "FOUR_SQUARE_DESCENT_STRICT_STEP_FROM_CENTERED_QUATERNION",
    "FOUR_SQUARE_DESCENT_THREE_MOD_FOUR_PRIMES_FROM_SEED_AND_STEP",
    "FOUR_SQUARE_DESCENT_ZERO_CENTERED_REMAINDER_DIVIDES",
    "FOUR_SQUARE_DESCENT_ZERO_NORM_COORDINATES",
    "FOUR_SQUARE_LAGRANGE_FROM_MODULAR_SEEDS_AND_STRICT_DESCENT",
    "centered_signed_remainder",
    "matching_parity",
    "make_four_square_descent_candidate_theorems",
]
