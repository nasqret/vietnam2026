"""Discharge the actual prime-seed premise in constructive Lagrange descent.

The only hypothesis remaining in either endpoint is the explicit, uniformly
strict prime-multiple descent step.  No universal representation is asserted
without that hypothesis.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .four_square_descent_candidate import _strict_step
from .four_square_lagrange_candidate import four_square_representation


FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT = "four_square_prime_from_strict_descent"
FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT = (
    "four_square_lagrange_from_strict_descent"
)
FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED = (
    "four_square_descent_below_prime_multiplier_bounded"
)
FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED = (
    "four_square_prime_from_bounded_strict_descent_and_seed"
)
FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT = (
    "four_square_prime_from_bounded_strict_descent"
)
FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT = (
    "four_square_lagrange_from_bounded_strict_descent"
)


def bounded_strict_prime_multiple_descent(*, tag: str) -> str:
    """Expand strict descent only below the prime, where centered norms persist."""

    modulus = f"fslb_bounded_prime_{tag}"
    multiplier = f"fslb_bounded_multiplier_{tag}"
    smaller = f"fslb_bounded_smaller_{tag}"
    upper_gap = f"fslb_bounded_upper_gap_{tag}"
    lower_gap = f"fslb_bounded_lower_gap_{tag}"
    represented_source = four_square_representation(
        f"{modulus} * {multiplier}", tag=f"fslb_bounded_source_{tag}"
    )
    represented_target = four_square_representation(
        f"{modulus} * {smaller}", tag=f"fslb_bounded_target_{tag}"
    )
    return (
        f"forall {modulus} {multiplier}. "
        f"({prime(modulus, tag=f'fslb_bounded_prime_{tag}')}) -> "
        f"~({multiplier} = 0) -> ~({multiplier} = 1) -> "
        f"(exists {upper_gap}. {upper_gap} + S {multiplier} = {modulus}) -> "
        f"({represented_source}) -> exists {smaller}. "
        f"(~({smaller} = 0) /\\ "
        f"((exists {lower_gap}. {lower_gap} + S {smaller} = {multiplier}) /\\ "
        f"({represented_target})))"
    )


def make_four_square_lagrange_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact one-hypothesis prime and all-natural Lagrange reductions."""

    strict = _strict_step(tag="bridge")
    prime_p = prime("p", tag="fslb_prime")
    represented_p = four_square_representation("p", tag="fslb_prime_result")
    represented_n = four_square_representation("n", tag="fslb_natural_result")
    represented_multiple = four_square_representation(
        "p * k", tag="fslb_bounded_multiple"
    )
    bounded_step = bounded_strict_prime_multiple_descent(tag="bridge")
    smaller_result = (
        "exists r. (~(r = 0) /\\ "
        "((exists gap. gap + S r = k) /\\ "
        f"({four_square_representation('p * r', tag='fslb_bounded_smaller')})))"
    )

    return (
        spec(
            FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT,
            f"({strict}) -> forall p. ({prime_p}) -> ({represented_p})",
            (
                "four_square_prime_modular_seed",
                "four_square_descent_prime_from_modular_seed_and_step",
            ),
            (
                "intro hstep",
                "intro p",
                "intro hprime",
                "have hseed : exists a b k. a * a + b * b + 1 = p * k",
                "specialize four_square_prime_modular_seed p",
                "apply four_square_prime_modular_seed",
                "exact hprime",
                "cases hseed",
                "cases hseed_witness",
                "cases hseed_witness_witness",
                "have hdescent : forall q a b k. "
                f"({prime('q', tag='fslb_local_prime')}) -> "
                "a * a + b * b + 1 = q * k -> "
                f"({four_square_representation('q', tag='fslb_local_result')})",
                "apply four_square_descent_prime_from_modular_seed_and_step",
                "exact hstep",
                "specialize hdescent p",
                "specialize hdescent x",
                "specialize hdescent x1",
                "specialize hdescent x2",
                "apply hdescent",
                "exact hprime",
                "exact hseed_witness_witness_witness",
            ),
            "The checked unconditional modular seed for every prime removes the entire seed hypothesis; only uniform strict multiplier descent remains.",
        ),
        spec(
            FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT,
            f"({strict}) -> forall n. ({represented_n})",
            (
                FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT,
                "four_square_lagrange_from_all_primes",
            ),
            (
                "intro hstep",
                "apply four_square_lagrange_from_all_primes",
                "apply four_square_prime_from_strict_descent",
                "exact hstep",
            ),
            "The all-natural Lagrange four-square theorem follows from exactly one remaining explicit hypothesis: uniform strict prime-multiple descent.",
        ),
        spec(
            FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED,
            f"forall B p k. (exists gap. gap + k = B) -> ({prime_p}) -> "
            "~(k = 0) -> (exists gap. gap + S k = p) -> "
            f"({represented_multiple}) -> ({bounded_step}) -> ({represented_p})",
            (
                "le_zero",
                "eq_decidable",
                "mul_one",
                "le_trans",
                "le_of_succ_le_succ",
                "lt_trans",
            ),
            (
                "intro B",
                "induction B",
                "intro p",
                "intro k",
                "intro hbound",
                "intro hprime",
                "intro hnonzero",
                "intro hbelow",
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
                "intro hbelow",
                "intro hrepresented",
                "intro hstep",
                "specialize eq_decidable k",
                "specialize eq_decidable 1",
                "cases eq_decidable",
                "rewrite eq_decidable_left at hrepresented",
                "specialize mul_one p",
                "rewrite mul_one at hrepresented",
                "exact hrepresented",
                f"have hsmaller : ({smaller_result})",
                "specialize hstep p",
                "specialize hstep k",
                "apply hstep",
                "exact hprime",
                "exact hnonzero",
                "exact eq_decidable_right",
                "exact hbelow",
                "exact hrepresented",
                "cases hsmaller",
                "cases hsmaller_witness",
                "cases hsmaller_witness_right",
                "have hsuccessor_bound : exists gap. gap + S x = S B",
                "specialize le_trans (S x)",
                "specialize le_trans k",
                "specialize le_trans (S B)",
                "apply le_trans",
                "exact hsmaller_witness_right_left",
                "exact hbound",
                "have hsmaller_bound : exists gap. gap + x = B",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsuccessor_bound",
                "have hsmaller_below : exists gap. gap + S x = p",
                "specialize lt_trans x",
                "specialize lt_trans k",
                "specialize lt_trans p",
                "apply lt_trans",
                "exact hsmaller_witness_right_left",
                "exact hbelow",
                "specialize IH p",
                "specialize IH x",
                "apply IH",
                "exact hsmaller_bound",
                "exact hprime",
                "exact hsmaller_witness_left",
                "exact hsmaller_below",
                "exact hsmaller_witness_right_right",
                "exact hstep",
            ),
            "Bounded constructive multiplier induction preserves k<p at every strictly decreasing step and reaches an actual representation of the prime.",
        ),
        spec(
            FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED,
            f"({bounded_step}) -> forall p a b k. ({prime_p}) -> "
            "a * a + b * b + 1 = p * k -> "
            f"(exists gap. gap + S k = p) -> ({represented_p})",
            (
                "le_refl",
                "four_square_descent_modular_seed_multiplier_nonzero",
                "four_square_prime_modular_seed_multiple",
                FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED,
            ),
            (
                "intro hstep",
                "intro p",
                "intro a",
                "intro b",
                "intro k",
                "intro hprime",
                "intro hseed",
                "intro hbelow",
                "specialize four_square_descent_below_prime_multiplier_bounded k",
                "specialize four_square_descent_below_prime_multiplier_bounded p",
                "specialize four_square_descent_below_prime_multiplier_bounded k",
                "apply four_square_descent_below_prime_multiplier_bounded",
                "specialize le_refl k",
                "exact le_refl",
                "exact hprime",
                "specialize four_square_descent_modular_seed_multiplier_nonzero p",
                "specialize four_square_descent_modular_seed_multiplier_nonzero a",
                "specialize four_square_descent_modular_seed_multiplier_nonzero b",
                "specialize four_square_descent_modular_seed_multiplier_nonzero k",
                "intro hzero",
                "apply four_square_descent_modular_seed_multiplier_nonzero",
                "exact hseed",
                "exact hzero",
                "exact hbelow",
                "specialize four_square_prime_modular_seed_multiple p",
                "specialize four_square_prime_modular_seed_multiple a",
                "specialize four_square_prime_modular_seed_multiple b",
                "specialize four_square_prime_modular_seed_multiple k",
                "apply four_square_prime_modular_seed_multiple",
                "exact hseed",
                "exact hstep",
            ),
            "An actual modular prime seed with multiplier strictly below the prime needs only the bounded strict-descent step to construct a four-square representation of the prime.",
        ),
        spec(
            FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT,
            f"({bounded_step}) -> forall p. ({prime_p}) -> ({represented_p})",
            (
                "four_square_prime_bounded_modular_seed",
                FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED,
            ),
            (
                "intro hstep",
                "intro p",
                "intro hprime",
                "have hseed : exists a b k. "
                "((a * a + b * b + 1 = p * k) /\\ "
                "(exists gap. gap + S k = p))",
                "specialize four_square_prime_bounded_modular_seed p",
                "apply four_square_prime_bounded_modular_seed",
                "exact hprime",
                "cases hseed",
                "cases hseed_witness",
                "cases hseed_witness_witness",
                "cases hseed_witness_witness_witness",
                "have hdescent : forall q a b k. "
                f"({prime('q', tag='fslb_bounded_local_prime')}) -> "
                "a * a + b * b + 1 = q * k -> "
                "(exists gap. gap + S k = q) -> "
                f"({four_square_representation('q', tag='fslb_bounded_local_result')})",
                "apply four_square_prime_from_bounded_strict_descent_and_seed",
                "exact hstep",
                "specialize hdescent p",
                "specialize hdescent x",
                "specialize hdescent x1",
                "specialize hdescent x2",
                "apply hdescent",
                "exact hprime",
                "exact hseed_witness_witness_witness_left",
                "exact hseed_witness_witness_witness_right",
            ),
            "The checked unconditional bounded modular seed discharges every seed premise, so the exact below-prime strict step alone represents every prime.",
        ),
        spec(
            FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT,
            f"({bounded_step}) -> forall n. ({represented_n})",
            (
                FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT,
                "four_square_lagrange_from_all_primes",
            ),
            (
                "intro hstep",
                "apply four_square_lagrange_from_all_primes",
                "apply four_square_prime_from_bounded_strict_descent",
                "exact hstep",
            ),
            "The complete all-natural Lagrange conclusion follows from exactly the sharp bounded strict-multiplier descent hypothesis, with every prime seed already constructed.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_DESCENT_BELOW_PRIME_MULTIPLIER_BOUNDED",
    "FOUR_SQUARE_LAGRANGE_FROM_BOUNDED_STRICT_DESCENT",
    "FOUR_SQUARE_LAGRANGE_FROM_STRICT_DESCENT",
    "FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT",
    "FOUR_SQUARE_PRIME_FROM_BOUNDED_STRICT_DESCENT_AND_SEED",
    "FOUR_SQUARE_PRIME_FROM_STRICT_DESCENT",
    "bounded_strict_prime_multiple_descent",
    "make_four_square_lagrange_bridge_candidate_theorems",
]
