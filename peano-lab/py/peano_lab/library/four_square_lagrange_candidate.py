"""Constructive prime reduction for the universal four-square campaign.

Euler's unconditional quaternion identity already supplies multiplicative
closure.  This isolated tranche proves explicit base cases, embeds the
completed two-square prime cases, and reduces universal Lagrange precisely to
the remaining three-modulo-four prime representations.  It does not silently
assume that missing prime theorem or confer Alpha/Stable authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime


FOUR_SQUARE_ZERO_REPRESENTED = "four_square_zero_represented"
FOUR_SQUARE_ONE_REPRESENTED = "four_square_one_represented"
FOUR_SQUARE_TWO_REPRESENTED = "four_square_two_represented"
FOUR_SQUARE_THREE_REPRESENTED = "four_square_three_represented"
FOUR_SQUARE_SEVEN_REPRESENTED = "four_square_seven_represented"
FOUR_SQUARE_ELEVEN_REPRESENTED = "four_square_eleven_represented"
FOUR_SQUARE_TWO_SQUARE_EMBEDDING = "four_square_two_square_embedding"
FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR = "four_square_prime_two_or_one_mod_four"
FOUR_SQUARE_PRIME_MODULAR_SEED_MULTIPLE = "four_square_prime_modular_seed_multiple"
FOUR_SQUARE_PRIME_UNIT_SEED_REPRESENTED = "four_square_prime_unit_seed_represented"
FOUR_SQUARE_PRIME_CASE_REDUCTION = "four_square_prime_case_reduction"
FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES = (
    "four_square_lagrange_bounded_from_primes"
)
FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES = "four_square_lagrange_from_all_primes"
FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES = (
    "four_square_lagrange_from_three_mod_four_primes"
)
FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES = (
    "four_square_lagrange_iff_three_mod_four_primes"
)


def four_square_representation(value: str, *, tag: str) -> str:
    """Expand four explicitly witnessed natural squares hygienically."""

    if not tag or not tag.replace("_", "").isalnum():
        raise ValueError("four-square tags must be nonempty identifier fragments")
    names = tuple(f"fsl_{coordinate}_{tag}" for coordinate in "abcd")
    return (
        f"exists {' '.join(names)}. ({value}) = "
        + " + ".join(f"{name} * {name}" for name in names)
    )


def _all_prime_representations(*, tag: str) -> str:
    value = f"fsl_prime_{tag}"
    return (
        f"forall {value}. ({prime(value, tag=f'fsl_all_{tag}')}) -> "
        f"({four_square_representation(value, tag=f'all_{tag}')})"
    )


def _three_mod_four_prime_representations(*, tag: str) -> str:
    value = f"fsl_three_prime_{tag}"
    residue = f"fsl_three_residue_{tag}"
    return (
        f"forall {value}. ({prime(value, tag=f'fsl_three_{tag}')}) -> "
        f"(exists {residue}. {value} = 4 * {residue} + 3) -> "
        f"({four_square_representation(value, tag=f'three_{tag}')})"
    )


def make_four_square_lagrange_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build bounded witnesses and the exact prime-to-universal reduction."""

    represented_n = four_square_representation("n", tag="value")
    represented_p = four_square_representation("p", tag="prime")
    prime_p = prime("p", tag="fsl_prime")
    all_primes = _all_prime_representations(tag="universal")
    three_primes = _three_mod_four_prime_representations(tag="universal")
    bound = "exists fsl_bound. fsl_bound + n = B"
    two_square_n = "exists a b. n = a * a + b * b"

    numeric_rows = (
        (FOUR_SQUARE_ZERO_REPRESENTED, 0, (0, 0, 0, 0)),
        (FOUR_SQUARE_ONE_REPRESENTED, 1, (1, 0, 0, 0)),
        (FOUR_SQUARE_TWO_REPRESENTED, 2, (1, 1, 0, 0)),
        (FOUR_SQUARE_THREE_REPRESENTED, 3, (1, 1, 1, 0)),
        (FOUR_SQUARE_SEVEN_REPRESENTED, 7, (2, 1, 1, 1)),
        (FOUR_SQUARE_ELEVEN_REPRESENTED, 11, (3, 1, 1, 0)),
    )

    rows: list[Any] = [
        spec(
            name,
            four_square_representation(str(value), tag=f"numeral_{value}"),
            (),
            tuple(f"exists {coordinate}" for coordinate in coordinates)
            + ("norm_num",),
            f"The natural number {value} has four explicitly checked square witnesses.",
        )
        for name, value, coordinates in numeric_rows
    ]

    rows.extend(
        (
            spec(
                FOUR_SQUARE_TWO_SQUARE_EMBEDDING,
                f"forall n. ({two_square_n}) -> ({represented_n})",
                (),
                (
                    "intro n",
                    "intro htwo",
                    "cases htwo",
                    "cases htwo_witness",
                    "exists x",
                    "exists x1",
                    "exists 0",
                    "exists 0",
                    "simp",
                ),
                "Every constructive sum of two natural squares is a sum of four by adjoining two zero witnesses.",
            ),
            spec(
                FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR,
                f"forall p. ({prime_p}) -> "
                f"(p = 2 \\/ exists k. p = 4 * k + 1) -> ({represented_p})",
                (
                    "prime_two_or_one_mod_four_is_sum_of_two_squares",
                    FOUR_SQUARE_TWO_SQUARE_EMBEDDING,
                ),
                (
                    "intro p",
                    "intro hprime",
                    "intro hclass",
                    "apply four_square_two_square_embedding",
                    "specialize prime_two_or_one_mod_four_is_sum_of_two_squares p",
                    "apply prime_two_or_one_mod_four_is_sum_of_two_squares",
                    "exact hprime",
                    "exact hclass",
                ),
                "The exceptional prime two and every prime congruent to one modulo four already have explicit four-square witnesses.",
            ),
            spec(
                FOUR_SQUARE_PRIME_MODULAR_SEED_MULTIPLE,
                "forall p x y k. "
                "x * x + y * y + 1 = p * k -> "
                f"({four_square_representation('p * k', tag='seed_multiple')})",
                (),
                (
                    "intro p",
                    "intro x",
                    "intro y",
                    "intro k",
                    "intro hseed",
                    "exists x",
                    "exists y",
                    "exists 1",
                    "exists 0",
                    "rewrite <- hseed",
                    "simp",
                ),
                "Any witnessed solution of x² + y² + 1 = p·k gives an actual four-square representation of the prime multiple.",
            ),
            spec(
                FOUR_SQUARE_PRIME_UNIT_SEED_REPRESENTED,
                "forall p x y. x * x + y * y + 1 = p -> "
                f"({represented_p})",
                (),
                (
                    "intro p",
                    "intro x",
                    "intro y",
                    "intro hseed",
                    "exists x",
                    "exists y",
                    "exists 1",
                    "exists 0",
                    "rewrite <- hseed",
                    "simp",
                ),
                "A modular four-square seed whose multiplier is one directly represents the prime itself.",
            ),
            spec(
                FOUR_SQUARE_PRIME_CASE_REDUCTION,
                f"({three_primes}) -> ({all_primes})",
                (
                    "prime_mod_four_good_or_three",
                    FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR,
                ),
                (
                    "intro hthree",
                    "intro p",
                    "intro hprime",
                    "have hclasses : "
                    "((p = 2 \\/ exists k. p = 4 * k + 1) \\/ "
                    "exists k. p = 4 * k + 3)",
                    "specialize prime_mod_four_good_or_three p",
                    "apply prime_mod_four_good_or_three",
                    "exact hprime",
                    "cases hclasses",
                    "specialize four_square_prime_two_or_one_mod_four p",
                    "apply four_square_prime_two_or_one_mod_four",
                    "exact hprime",
                    "exact hclasses_left",
                    "specialize hthree p",
                    "apply hthree",
                    "exact hprime",
                    "exact hclasses_right",
                ),
                "Constructive prime trichotomy reduces representation of every prime exactly to the still-open three-modulo-four prime case.",
            ),
            spec(
                FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES,
                f"forall B n. ({bound}) -> ~(n = 0) -> "
                f"({all_primes}) -> ({represented_n})",
                (
                    "le_zero",
                    "eq_decidable",
                    "prime_divisor_exists",
                    "mul_comm",
                    "proper_factor_lt",
                    "le_trans",
                    "le_of_succ_le_succ",
                    "four_square_euler_representations_closed_under_multiplication",
                ),
                (
                    "intro B",
                    "induction B",
                    "intro n",
                    "intro hbound",
                    "intro hnonzero",
                    "intro hprimes",
                    "exfalso",
                    "apply hnonzero",
                    "specialize le_zero n",
                    "apply le_zero",
                    "exact hbound",
                    "intro n",
                    "intro hbound",
                    "intro hnonzero",
                    "intro hprimes",
                    "specialize eq_decidable n",
                    "specialize eq_decidable 1",
                    "cases eq_decidable",
                    "exists 1",
                    "exists 0",
                    "exists 0",
                    "exists 0",
                    "rewrite eq_decidable_left",
                    "norm_num",
                    "have hfactor : exists p. "
                    f"(({prime('p', tag='fsl_induction_factor')}) /\\ "
                    "exists r. n = p * r)",
                    "specialize prime_divisor_exists n",
                    "apply prime_divisor_exists",
                    "exact hnonzero",
                    "exact eq_decidable_right",
                    "cases hfactor",
                    "cases hfactor_witness",
                    "cases hfactor_witness_right",
                    "have hprefix_nonzero : ~(x1 = 0)",
                    "intro hzero",
                    "apply hnonzero",
                    "trans x * x1",
                    "exact hfactor_witness_right_witness",
                    "rewrite hzero",
                    "apply PA5",
                    "have hrepresented_prime : "
                    f"({four_square_representation('x', tag='induction_prime')})",
                    "specialize hprimes x",
                    "apply hprimes",
                    "exact hfactor_witness_left",
                    "have hordered : n = x1 * x",
                    "trans x * x1",
                    "exact hfactor_witness_right_witness",
                    "apply mul_comm",
                    "have hnotone : ~(x = 1)",
                    "cases hfactor_witness_left",
                    "exact hfactor_witness_left_left",
                    "have hstrict : exists k. k + S x1 = n",
                    "specialize proper_factor_lt n",
                    "specialize proper_factor_lt x1",
                    "specialize proper_factor_lt x",
                    "apply proper_factor_lt",
                    "exact hnonzero",
                    "exact hordered",
                    "exact hnotone",
                    "have hsuccessor_bound : exists k. k + S x1 = S B",
                    "specialize le_trans (S x1)",
                    "specialize le_trans n",
                    "specialize le_trans (S B)",
                    "apply le_trans",
                    "exact hstrict",
                    "exact hbound",
                    "have hprefix_bound : exists k. k + x1 = B",
                    "specialize le_of_succ_le_succ x1",
                    "specialize le_of_succ_le_succ B",
                    "apply le_of_succ_le_succ",
                    "exact hsuccessor_bound",
                    "have hprefix_representation : "
                    f"({four_square_representation('x1', tag='induction_prefix')})",
                    "specialize IH x1",
                    "apply IH",
                    "exact hprefix_bound",
                    "exact hprefix_nonzero",
                    "exact hprimes",
                    "rewrite hordered",
                    "specialize four_square_euler_representations_closed_under_multiplication x1",
                    "specialize four_square_euler_representations_closed_under_multiplication x",
                    "apply four_square_euler_representations_closed_under_multiplication",
                    "exact hprefix_representation",
                    "exact hrepresented_prime",
                ),
                "Bounded constructive prime-factor descent proves every nonzero natural is a sum of four squares once every prime has such a representation.",
            ),
            spec(
                FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES,
                f"({all_primes}) -> forall n. ({represented_n})",
                (
                    "eq_decidable",
                    "le_refl",
                    FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES,
                ),
                (
                    "intro hprimes",
                    "intro n",
                    "specialize eq_decidable n",
                    "specialize eq_decidable 0",
                    "cases eq_decidable",
                    "exists 0",
                    "exists 0",
                    "exists 0",
                    "exists 0",
                    "rewrite eq_decidable_left",
                    "norm_num",
                    "specialize four_square_lagrange_bounded_from_primes n",
                    "specialize four_square_lagrange_bounded_from_primes n",
                    "apply four_square_lagrange_bounded_from_primes",
                    "specialize le_refl n",
                    "exact le_refl",
                    "exact eq_decidable_right",
                    "exact hprimes",
                ),
                "All-natural Lagrange, including zero, follows constructively from the explicit universal prime-representation premise.",
            ),
            spec(
                FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES,
                f"({three_primes}) -> forall n. ({represented_n})",
                (
                    FOUR_SQUARE_PRIME_CASE_REDUCTION,
                    FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES,
                ),
                (
                    "intro hthree",
                    "apply four_square_lagrange_from_all_primes",
                    "apply four_square_prime_case_reduction",
                    "exact hthree",
                ),
                "The full universal four-square theorem is reduced precisely to constructive representation of primes congruent to three modulo four.",
            ),
            spec(
                FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES,
                f"(((forall n. ({represented_n})) -> ({three_primes})) /\\ "
                f"(({three_primes}) -> forall n. ({represented_n})))",
                (FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES,),
                (
                    "split",
                    "intro hall",
                    "intro p",
                    "intro hprime",
                    "intro hclass",
                    "specialize hall p",
                    "exact hall",
                    "exact four_square_lagrange_from_three_mod_four_primes",
                ),
                "Universal Lagrange is constructively equivalent to the one unresolved family of three-modulo-four prime representations.",
            ),
        )
    )
    return tuple(rows)


__all__ = [
    "FOUR_SQUARE_ELEVEN_REPRESENTED",
    "FOUR_SQUARE_LAGRANGE_BOUNDED_FROM_PRIMES",
    "FOUR_SQUARE_LAGRANGE_FROM_ALL_PRIMES",
    "FOUR_SQUARE_LAGRANGE_FROM_THREE_MOD_FOUR_PRIMES",
    "FOUR_SQUARE_LAGRANGE_IFF_THREE_MOD_FOUR_PRIMES",
    "FOUR_SQUARE_ONE_REPRESENTED",
    "FOUR_SQUARE_PRIME_CASE_REDUCTION",
    "FOUR_SQUARE_PRIME_MODULAR_SEED_MULTIPLE",
    "FOUR_SQUARE_PRIME_TWO_OR_ONE_MOD_FOUR",
    "FOUR_SQUARE_PRIME_UNIT_SEED_REPRESENTED",
    "FOUR_SQUARE_SEVEN_REPRESENTED",
    "FOUR_SQUARE_THREE_REPRESENTED",
    "FOUR_SQUARE_TWO_REPRESENTED",
    "FOUR_SQUARE_TWO_SQUARE_EMBEDDING",
    "FOUR_SQUARE_ZERO_REPRESENTED",
    "four_square_representation",
    "make_four_square_lagrange_candidate_theorems",
]
