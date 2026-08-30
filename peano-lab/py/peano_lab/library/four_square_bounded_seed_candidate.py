"""Bounded constructive prime seeds for four-square strict descent.

All predicates expand to the unchanged first-order Heyting-arithmetic
language.  These dependency-curried candidates do not modify Alpha or Stable.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .four_square_descent_candidate import (
    FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER,
    FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT,
)
from .four_square_residue_intersection_candidate import (
    make_four_square_residue_intersection_candidate_theorems,
)


FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED = (
    "four_square_odd_prime_half_coordinate_seed"
)
FOUR_SQUARE_ODD_PRIME_HALF_POSITIVE = "four_square_odd_prime_half_positive"
FOUR_SQUARE_ODD_PRIME_HALF_SEED_NORM_STRICT = (
    "four_square_odd_prime_half_seed_norm_strict"
)
FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED = (
    "four_square_odd_prime_bounded_modular_seed"
)
FOUR_SQUARE_NON_TWO_PRIME_BOUNDED_MODULAR_SEED = (
    "four_square_non_two_prime_bounded_modular_seed"
)
FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED = "four_square_prime_bounded_modular_seed"


def _le(left: str, right: str, *, tag: str) -> str:
    gap = f"fsbs_le_gap_{tag}"
    return f"exists {gap}. {gap} + ({left}) = ({right})"


def _lt(left: str, right: str, *, tag: str) -> str:
    gap = f"fsbs_lt_gap_{tag}"
    return f"exists {gap}. {gap} + S ({left}) = ({right})"


def _bounded_seed(*, tag: str) -> str:
    a = f"fsbs_a_{tag}"
    b = f"fsbs_b_{tag}"
    k = f"fsbs_k_{tag}"
    return (
        f"exists {a} {b} {k}. "
        f"(({a} * {a} + {b} * {b} + 1 = p * {k}) /\\ "
        f"({_lt(k, 'p', tag=f'{tag}_multiplier')}))"
    )


def make_four_square_bounded_seed_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Retain actual half-range residue witnesses and bound their multiplier."""

    residue_rows = make_four_square_residue_intersection_candidate_theorems(spec)
    odd_seed = next(
        row for row in residue_rows if row.name == "four_square_odd_prime_modular_seed"
    )
    prime_p = prime("p", tag="fsbs_prime")

    return (
        spec(
            FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED,
            f"forall p h. p = 2 * h + 1 -> ({prime_p}) -> "
            "exists a b k. ((a * a + b * b + 1 = p * k) /\\ "
            f"(({_le('a', 'h', tag='first_half')}) /\\ "
            f"({_le('b', 'h', tag='second_half')})))",
            odd_seed.dependencies + ("le_of_succ_le_succ",),
            odd_seed.script[:-1]
            + (
                "split",
                "exact hmultiple_witness",
                "split",
                "specialize le_of_succ_le_succ x4",
                "specialize le_of_succ_le_succ h",
                "apply le_of_succ_le_succ",
                "exact hcross_witness_witness_witness_left",
                "specialize le_of_succ_le_succ x5",
                "specialize le_of_succ_le_succ h",
                "apply le_of_succ_le_succ",
                "exact hcross_witness_witness_witness_right_left",
            ),
            "The actual odd-prime residue intersection supplies both square coordinates in the witnessed interval 0≤a,b≤h.",
        ),
        spec(
            FOUR_SQUARE_ODD_PRIME_HALF_POSITIVE,
            f"forall p h. p = 2 * h + 1 -> ({prime_p}) -> "
            f"({_le('1', 'h', tag='positive_half')})",
            ("nonzero_is_succ",),
            (
                "intro p",
                "intro h",
                "intro hodd",
                "intro hprime",
                "have hnonzero : ~(h = 0)",
                "intro hzero",
                "cases hprime",
                "apply hprime_left",
                "rewrite hodd",
                "rewrite hzero",
                "norm_num",
                "have hsuccessor : exists t. h = S t",
                "specialize nonzero_is_succ h",
                "apply nonzero_is_succ",
                "exact hnonzero",
                "cases hsuccessor",
                "exists x",
                "rewrite hsuccessor_witness",
                "simp",
            ),
            "The half h of an odd prime p=2h+1 is constructively at least one.",
        ),
        spec(
            FOUR_SQUARE_ODD_PRIME_HALF_SEED_NORM_STRICT,
            f"forall p h a b. p = 2 * h + 1 -> ({prime_p}) -> "
            f"({_le('a', 'h', tag='strict_first')}) -> "
            f"({_le('b', 'h', tag='strict_second')}) -> "
            f"({_lt('a * a + b * b + 1', 'p * p', tag='strict_norm')})",
            (
                FOUR_SQUARE_ODD_PRIME_HALF_POSITIVE,
                FOUR_SQUARE_DESCENT_ODD_HALF_NORM_STRICT,
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro hodd",
                "intro hprime",
                "intro ha",
                "intro hb",
                "have hpositive : exists gap. gap + 1 = h",
                "specialize four_square_odd_prime_half_positive p",
                "specialize four_square_odd_prime_half_positive h",
                "apply four_square_odd_prime_half_positive",
                "exact hodd",
                "exact hprime",
                "have hnorm : exists gap. "
                "gap + S (a * a + b * b + 1 * 1 + 0 * 0) = "
                "(2 * h + 1) * (2 * h + 1)",
                "specialize four_square_descent_odd_half_norm_strict h",
                "specialize four_square_descent_odd_half_norm_strict a",
                "specialize four_square_descent_odd_half_norm_strict b",
                "specialize four_square_descent_odd_half_norm_strict 1",
                "specialize four_square_descent_odd_half_norm_strict 0",
                "apply four_square_descent_odd_half_norm_strict",
                "exact ha",
                "exact hb",
                "exact hpositive",
                "exists h",
                "simp",
                "have hshape : "
                "a * a + b * b + 1 * 1 + 0 * 0 = a * a + b * b + 1",
                "simp",
                "rewrite hshape at hnorm",
                "rewrite hodd",
                "rewrite hodd",
                "exact hnorm",
            ),
            "The actual half-range seed norm a²+b²+1 is strictly smaller than the square of its odd prime modulus.",
        ),
        spec(
            FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED,
            f"forall p h. p = 2 * h + 1 -> ({prime_p}) -> "
            f"({_bounded_seed(tag='odd_bounded')})",
            (
                FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED,
                FOUR_SQUARE_ODD_PRIME_HALF_SEED_NORM_STRICT,
                FOUR_SQUARE_DESCENT_NORM_BOUND_FORCES_SMALLER_MULTIPLIER,
            ),
            (
                "intro p",
                "intro h",
                "intro hodd",
                "intro hprime",
                "have hseed : exists a b k. "
                "((a * a + b * b + 1 = p * k) /\\ "
                "((exists gap. gap + a = h) /\\ "
                "(exists gap. gap + b = h)))",
                "specialize four_square_odd_prime_half_coordinate_seed p",
                "specialize four_square_odd_prime_half_coordinate_seed h",
                "apply four_square_odd_prime_half_coordinate_seed",
                "exact hodd",
                "exact hprime",
                "cases hseed",
                "cases hseed_witness",
                "cases hseed_witness_witness",
                "cases hseed_witness_witness_witness",
                "cases hseed_witness_witness_witness_right",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hseed_witness_witness_witness_left",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier p",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier x2",
                "specialize four_square_descent_norm_bound_forces_smaller_multiplier "
                "(x * x + x1 * x1 + 1)",
                "apply four_square_descent_norm_bound_forces_smaller_multiplier",
                "symm",
                "exact hseed_witness_witness_witness_left",
                "specialize four_square_odd_prime_half_seed_norm_strict p",
                "specialize four_square_odd_prime_half_seed_norm_strict h",
                "specialize four_square_odd_prime_half_seed_norm_strict x",
                "specialize four_square_odd_prime_half_seed_norm_strict x1",
                "apply four_square_odd_prime_half_seed_norm_strict",
                "exact hodd",
                "exact hprime",
                "exact hseed_witness_witness_witness_right_left",
                "exact hseed_witness_witness_witness_right_right",
            ),
            "Every odd prime has an actual modular square seed with a strictly smaller natural multiplier.",
        ),
        spec(
            FOUR_SQUARE_NON_TWO_PRIME_BOUNDED_MODULAR_SEED,
            f"forall p. ({prime_p}) -> ~(p = 2) -> "
            f"({_bounded_seed(tag='non_two_bounded')})",
            ("prime_ne_two_is_odd", FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED),
            (
                "intro p",
                "intro hprime",
                "intro hnot_two",
                "have hodd : exists h. p = 2 * h + 1",
                "specialize prime_ne_two_is_odd p",
                "apply prime_ne_two_is_odd",
                "exact hprime",
                "exact hnot_two",
                "cases hodd",
                "specialize four_square_odd_prime_bounded_modular_seed p",
                "specialize four_square_odd_prime_bounded_modular_seed x",
                "apply four_square_odd_prime_bounded_modular_seed",
                "exact hodd_witness",
                "exact hprime",
            ),
            "Every prime other than two has a strictly prime-bounded constructive modular four-square seed.",
        ),
        spec(
            FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED,
            f"forall p. ({prime_p}) -> ({_bounded_seed(tag='prime_bounded')})",
            ("eq_decidable", FOUR_SQUARE_NON_TWO_PRIME_BOUNDED_MODULAR_SEED),
            (
                "intro p",
                "intro hprime",
                "have hcase : p = 2 \\/ ~(p = 2)",
                "specialize eq_decidable p",
                "specialize eq_decidable 2",
                "exact eq_decidable",
                "cases hcase",
                "rewrite hcase_left",
                "rewrite hcase_left",
                "exists 1",
                "exists 0",
                "exists 1",
                "split",
                "norm_num",
                "exists 0",
                "norm_num",
                "specialize four_square_non_two_prime_bounded_modular_seed p",
                "apply four_square_non_two_prime_bounded_modular_seed",
                "exact hprime",
                "exact hcase_right",
            ),
            "Every prime, including two, has actual witnesses a²+b²+1=p·k with the constructive strict bound k<p.",
        ),
    )


__all__ = [
    "FOUR_SQUARE_NON_TWO_PRIME_BOUNDED_MODULAR_SEED",
    "FOUR_SQUARE_ODD_PRIME_BOUNDED_MODULAR_SEED",
    "FOUR_SQUARE_ODD_PRIME_HALF_COORDINATE_SEED",
    "FOUR_SQUARE_ODD_PRIME_HALF_POSITIVE",
    "FOUR_SQUARE_ODD_PRIME_HALF_SEED_NORM_STRICT",
    "FOUR_SQUARE_PRIME_BOUNDED_MODULAR_SEED",
    "make_four_square_bounded_seed_candidate_theorems",
]
