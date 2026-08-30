"""Constructive Euclid witnesses for arbitrarily large primes ``1 mod 4``.

Every relation expands into the unchanged first-order Heyting-arithmetic
language.  A nonzero common multiple ``c`` of the positive naturals up to the
requested bound supplies the Euclid number ``(2*c)^2+1``.  Each prime divisor
is strictly above the bound, and the independently checked two-square
obstruction excludes both the exceptional prime two and primes ``3 mod 4``.

These dependency-curried candidate bodies neither enroll a theorem nor alter
Alpha/Stable authority, theorem definitions, the kernel, or proof limits.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime


DOUBLED_SQUARE_PLUS_ONE_NONZERO = "doubled_square_plus_one_nonzero"
DOUBLED_SQUARE_PLUS_ONE_NONUNIT = "doubled_square_plus_one_nonunit"
DOUBLED_SQUARE_PLUS_ONE_HAS_PRIME_DIVISOR = (
    "doubled_square_plus_one_has_prime_divisor"
)
DOUBLED_SQUARE_PLUS_ONE_NOT_DIVISIBLE_BY_TWO = (
    "doubled_square_plus_one_not_divisible_by_two"
)
THREE_MOD_FOUR_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE = (
    "three_mod_four_prime_cannot_divide_doubled_square_plus_one"
)
PRIME_DIVISOR_OF_DOUBLED_SQUARE_PLUS_ONE_IS_ONE_MOD_FOUR = (
    "prime_divisor_of_doubled_square_plus_one_is_one_mod_four"
)
BOUNDED_COMMON_MULTIPLE_CONTAINS_BOUNDED_PRIME = (
    "bounded_common_multiple_contains_bounded_prime"
)
COMMON_MULTIPLE_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE = (
    "common_multiple_prime_cannot_divide_doubled_square_plus_one"
)
DOUBLED_SQUARE_PRIME_DIVISOR_EXCEEDS_COMMON_MULTIPLE_BOUND = (
    "doubled_square_prime_divisor_exceeds_common_multiple_bound"
)
INFINITELY_MANY_PRIMES_ONE_MOD_FOUR = "infinitely_many_primes_one_mod_four"


def _euclid_norm(value: str) -> str:
    return f"(2 * {value}) * (2 * {value}) + 1"


def _divides(divisor: str, value: str, *, tag: str) -> str:
    witness = f"pomf_factor_{tag}"
    return f"exists {witness}. ({value}) = ({divisor}) * {witness}"


def _one_mod_four(value: str, *, tag: str) -> str:
    witness = f"pomf_one_{tag}"
    return f"exists {witness}. ({value}) = 4 * {witness} + 1"


def _three_mod_four(value: str, *, tag: str) -> str:
    witness = f"pomf_three_{tag}"
    return f"exists {witness}. ({value}) = 4 * {witness} + 3"


def _bounded_common_multiple(bound: str, value: str, *, tag: str) -> str:
    predecessor = f"pomf_predecessor_{tag}"
    gap = f"pomf_gap_{tag}"
    quotient = f"pomf_quotient_{tag}"
    return (
        f"forall {predecessor}. "
        f"(exists {gap}. S {predecessor} + S {gap} = S {bound}) -> "
        f"exists {quotient}. {value} = S {predecessor} * {quotient}"
    )


def make_primes_one_mod_four_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return actual constructive proof candidates in dependency order."""

    norm = _euclid_norm("c")
    primality = prime("p", tag="pomf_prime")
    prime_divides_norm = _divides("p", norm, tag="norm")
    prime_divides_common = _divides("p", "c", tag="common")
    common_multiple = _bounded_common_multiple("B", "c", tag="source")
    one_mod_four = _one_mod_four("p", tag="result")
    three_mod_four = _three_mod_four("p", tag="obstruction")

    return (
        spec(
            DOUBLED_SQUARE_PLUS_ONE_NONZERO,
            f"forall c. ~(({norm}) = 0)",
            (),
            (
                "intro c",
                "intro hzero",
                "rewrite PA4 at hzero",
                "rewrite PA3 at hzero",
                "apply PA1",
                "exact hzero",
            ),
            "The Euclidean norm (2c)^2+1 is never zero.",
        ),
        spec(
            DOUBLED_SQUARE_PLUS_ONE_NONUNIT,
            f"forall c. ~(c = 0) -> ~(({norm}) = 1)",
            ("mul_eq_zero",),
            (
                "intro c",
                "intro hnonzero",
                "intro hunit",
                "rewrite PA4 at hunit",
                "rewrite PA3 at hunit",
                "have hsquare : (2 * c) * (2 * c) = 0",
                "apply PA2",
                "exact hunit",
                "have hdoublecases : 2 * c = 0 \/ 2 * c = 0",
                "specialize mul_eq_zero (2 * c)",
                "specialize mul_eq_zero (2 * c)",
                "apply mul_eq_zero",
                "exact hsquare",
                "have hdouble : 2 * c = 0",
                "cases hdoublecases",
                "exact hdoublecases_left",
                "exact hdoublecases_right",
                "have hfactor : 2 = 0 \/ c = 0",
                "specialize mul_eq_zero 2",
                "specialize mul_eq_zero c",
                "apply mul_eq_zero",
                "exact hdouble",
                "cases hfactor",
                "apply PA1",
                "exact hfactor_left",
                "apply hnonzero",
                "exact hfactor_right",
            ),
            "For nonzero c, the Euclidean norm (2c)^2+1 is not the unit one.",
        ),
        spec(
            DOUBLED_SQUARE_PLUS_ONE_HAS_PRIME_DIVISOR,
            f"forall c. ~(c = 0) -> exists p. "
            f"(({primality}) /\\ ({prime_divides_norm}))",
            (
                DOUBLED_SQUARE_PLUS_ONE_NONZERO,
                DOUBLED_SQUARE_PLUS_ONE_NONUNIT,
                "prime_divisor_exists",
            ),
            (
                "intro c",
                "intro hnonzero",
                f"specialize prime_divisor_exists ({norm})",
                "apply prime_divisor_exists",
                "specialize doubled_square_plus_one_nonzero c",
                "exact doubled_square_plus_one_nonzero",
                "intro hunit",
                "specialize doubled_square_plus_one_nonunit c",
                "apply doubled_square_plus_one_nonunit",
                "exact hnonzero",
                "exact hunit",
            ),
            "Every nonzero common multiple yields an actual prime divisor of (2c)^2+1.",
        ),
        spec(
            DOUBLED_SQUARE_PLUS_ONE_NOT_DIVISIBLE_BY_TWO,
            f"forall c k. ({norm}) = 2 * k -> false",
            ("mul_assoc", "even_odd_exclusive_pointwise"),
            (
                "intro c",
                "intro k",
                "intro heven",
                f"have hodd : ({norm}) = 2 * (c * (2 * c)) + 1",
                "congr",
                "apply mul_assoc",
                "refl",
                f"specialize even_odd_exclusive_pointwise ({norm})",
                "specialize even_odd_exclusive_pointwise k",
                "specialize even_odd_exclusive_pointwise (c * (2 * c))",
                "apply even_odd_exclusive_pointwise",
                "exact heven",
                "exact hodd",
            ),
            "The Euclidean norm (2c)^2+1 is odd and therefore not divisible by two.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE,
            f"forall c p. ({primality}) -> ({three_mod_four}) -> "
            f"({prime_divides_norm}) -> false",
            (
                "three_mod_four_prime_divides_two_square_norm_divides_both",
                "mul_one",
                "divisor_one",
            ),
            (
                "intro c",
                "intro p",
                "intro hprime",
                "intro hthree",
                "intro hdivides",
                "have hnorm : exists k. "
                "(2 * c) * (2 * c) + 1 * 1 = p * k",
                "cases hdivides",
                "exists x",
                f"trans {norm}",
                "congr",
                "refl",
                "apply mul_one",
                "exact hdivides_witness",
                "have hcoordinates : "
                "((exists u. 2 * c = p * u) /\\ (exists v. 1 = p * v))",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both p",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both (2 * c)",
                "specialize three_mod_four_prime_divides_two_square_norm_divides_both 1",
                "apply three_mod_four_prime_divides_two_square_norm_divides_both",
                "exact hprime",
                "exact hthree",
                "exact hnorm",
                "cases hcoordinates",
                "have hunit : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hcoordinates_right",
                "cases hprime",
                "apply hprime_left",
                "exact hunit",
            ),
            "A prime three modulo four cannot divide (2c)^2+1, since it would divide one.",
        ),
        spec(
            PRIME_DIVISOR_OF_DOUBLED_SQUARE_PLUS_ONE_IS_ONE_MOD_FOUR,
            f"forall c p. ({primality}) -> ({prime_divides_norm}) -> "
            f"({one_mod_four})",
            (
                "prime_mod_four_trichotomy",
                DOUBLED_SQUARE_PLUS_ONE_NOT_DIVISIBLE_BY_TWO,
                THREE_MOD_FOUR_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE,
            ),
            (
                "intro c",
                "intro p",
                "intro hprime",
                "intro hdivides",
                f"have hcases : p = 2 \/ (({one_mod_four}) \/ ({three_mod_four}))",
                "specialize prime_mod_four_trichotomy p",
                "apply prime_mod_four_trichotomy",
                "exact hprime",
                "cases hcases",
                "exfalso",
                "cases hdivides",
                "specialize doubled_square_plus_one_not_divisible_by_two c",
                "specialize doubled_square_plus_one_not_divisible_by_two x",
                "apply doubled_square_plus_one_not_divisible_by_two",
                "rewrite hcases_left at hdivides_witness",
                "exact hdivides_witness",
                "cases hcases_right",
                "exact hcases_right_left",
                "exfalso",
                "specialize three_mod_four_prime_cannot_divide_doubled_square_plus_one c",
                "specialize three_mod_four_prime_cannot_divide_doubled_square_plus_one p",
                "apply three_mod_four_prime_cannot_divide_doubled_square_plus_one",
                "exact hprime",
                "exact hcases_right_right",
                "exact hdivides",
            ),
            "Every prime divisor of (2c)^2+1 has a witnessed representative 4k+1.",
        ),
        spec(
            BOUNDED_COMMON_MULTIPLE_CONTAINS_BOUNDED_PRIME,
            f"forall B c p. ({common_multiple}) -> ({primality}) -> "
            f"(exists k. k + p = B) -> ({prime_divides_common})",
            ("prime_nonzero", "nonzero_is_succ", "add_comm"),
            (
                "intro B",
                "intro c",
                "intro p",
                "intro hcommon",
                "intro hprime",
                "intro hbounded",
                "have hnonzero : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                "have hsuccessor : exists t. p = S t",
                "specialize nonzero_is_succ p",
                "apply nonzero_is_succ",
                "exact hnonzero",
                "cases hsuccessor",
                "cases hbounded",
                "rewrite hsuccessor_witness at hbounded_witness",
                "have hbound : exists h. S x + S h = S B",
                "exists x1",
                "rewrite PA4",
                "congr",
                "trans x1 + S x",
                "apply add_comm",
                "exact hbounded_witness",
                "have hdivisor : exists k. c = S x * k",
                "specialize hcommon x",
                "apply hcommon",
                "exact hbound",
                "rewrite hsuccessor_witness",
                "exact hdivisor",
            ),
            "Every prime at most B divides any witnessed common multiple of 1 through B.",
        ),
        spec(
            COMMON_MULTIPLE_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE,
            f"forall c p. ({primality}) -> ({prime_divides_common}) -> "
            f"({prime_divides_norm}) -> false",
            (
                "multiple_mul_left",
                "multiple_mul_right",
                "divides_remainder",
                "mul_one",
                "divisor_one",
            ),
            (
                "intro c",
                "intro p",
                "intro hprime",
                "intro hcommon",
                "intro hnorm",
                "have hdouble : exists q. 2 * c = p * q",
                "specialize multiple_mul_left p",
                "specialize multiple_mul_left c",
                "specialize multiple_mul_left 2",
                "apply multiple_mul_left",
                "exact hcommon",
                "have hsquare : exists q. (2 * c) * (2 * c) = p * q",
                "specialize multiple_mul_right p",
                "specialize multiple_mul_right (2 * c)",
                "specialize multiple_mul_right (2 * c)",
                "apply multiple_mul_right",
                "exact hdouble",
                "have hone : exists q. 1 = p * q",
                "specialize divides_remainder p",
                f"specialize divides_remainder ({norm})",
                "specialize divides_remainder ((2 * c) * (2 * c))",
                "specialize divides_remainder 1",
                "specialize divides_remainder 1",
                "apply divides_remainder",
                "exact hnorm",
                "exact hsquare",
                "specialize mul_one ((2 * c) * (2 * c))",
                "rewrite mul_one",
                "refl",
                "have hunit : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hone",
                "cases hprime",
                "apply hprime_left",
                "exact hunit",
            ),
            "A prime dividing a common multiple cannot also divide its Euclidean norm.",
        ),
        spec(
            DOUBLED_SQUARE_PRIME_DIVISOR_EXCEEDS_COMMON_MULTIPLE_BOUND,
            f"forall B c p. ({common_multiple}) -> ({primality}) -> "
            f"({prime_divides_norm}) -> exists gap. gap + S B = p",
            (
                "le_or_lt",
                BOUNDED_COMMON_MULTIPLE_CONTAINS_BOUNDED_PRIME,
                COMMON_MULTIPLE_PRIME_CANNOT_DIVIDE_DOUBLED_SQUARE_PLUS_ONE,
            ),
            (
                "intro B",
                "intro c",
                "intro p",
                "intro hcommon",
                "intro hprime",
                "intro hnorm",
                "specialize le_or_lt p",
                "specialize le_or_lt B",
                "cases le_or_lt",
                "exfalso",
                "have hdivisor : exists k. c = p * k",
                "specialize bounded_common_multiple_contains_bounded_prime B",
                "specialize bounded_common_multiple_contains_bounded_prime c",
                "specialize bounded_common_multiple_contains_bounded_prime p",
                "apply bounded_common_multiple_contains_bounded_prime",
                "exact hcommon",
                "exact hprime",
                "exact le_or_lt_left",
                "specialize common_multiple_prime_cannot_divide_doubled_square_plus_one c",
                "specialize common_multiple_prime_cannot_divide_doubled_square_plus_one p",
                "apply common_multiple_prime_cannot_divide_doubled_square_plus_one",
                "exact hprime",
                "exact hdivisor",
                "exact hnorm",
                "exact le_or_lt_right",
            ),
            "Every prime factor of the Euclidean norm lies strictly above the common-multiple bound.",
        ),
        spec(
            INFINITELY_MANY_PRIMES_ONE_MOD_FOUR,
            f"forall B. exists p. (({primality}) /\\ "
            f"((exists gap. gap + S B = p) /\\ ({one_mod_four})))",
            (
                "bounded_common_multiple_exists",
                DOUBLED_SQUARE_PLUS_ONE_HAS_PRIME_DIVISOR,
                PRIME_DIVISOR_OF_DOUBLED_SQUARE_PLUS_ONE_IS_ONE_MOD_FOUR,
                DOUBLED_SQUARE_PRIME_DIVISOR_EXCEEDS_COMMON_MULTIPLE_BOUND,
            ),
            (
                "intro B",
                "specialize bounded_common_multiple_exists B",
                "cases bounded_common_multiple_exists",
                "cases bounded_common_multiple_exists_witness",
                f"have hdivisor : exists p. (({primality}) /\\ "
                f"({_divides('p', _euclid_norm('x'), tag='endpoint_norm')}))",
                "specialize doubled_square_plus_one_has_prime_divisor x",
                "apply doubled_square_plus_one_has_prime_divisor",
                "exact bounded_common_multiple_exists_witness_left",
                "cases hdivisor",
                "cases hdivisor_witness",
                "exists x1",
                "split",
                "exact hdivisor_witness_left",
                "split",
                "specialize doubled_square_prime_divisor_exceeds_common_multiple_bound B",
                "specialize doubled_square_prime_divisor_exceeds_common_multiple_bound x",
                "specialize doubled_square_prime_divisor_exceeds_common_multiple_bound x1",
                "apply doubled_square_prime_divisor_exceeds_common_multiple_bound",
                "exact bounded_common_multiple_exists_witness_right",
                "exact hdivisor_witness_left",
                "exact hdivisor_witness_right",
                "specialize prime_divisor_of_doubled_square_plus_one_is_one_mod_four x",
                "specialize prime_divisor_of_doubled_square_plus_one_is_one_mod_four x1",
                "apply prime_divisor_of_doubled_square_plus_one_is_one_mod_four",
                "exact hdivisor_witness_left",
                "exact hdivisor_witness_right",
            ),
            "For every natural bound, construct a strictly larger prime congruent to one modulo four.",
        ),
    )


__all__ = [
    "INFINITELY_MANY_PRIMES_ONE_MOD_FOUR",
    "make_primes_one_mod_four_candidate_theorems",
]
