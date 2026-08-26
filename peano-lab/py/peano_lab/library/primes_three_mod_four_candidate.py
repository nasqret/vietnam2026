"""Constructive Euclid witnesses for arbitrarily large primes ``3 mod 4``.

All authoring surfaces expand entirely into the unchanged first-order
Heyting-arithmetic language.  In particular, finite search is an actual
induction, factorization is the previously checked beta-coded factorization,
and ``4*c-1`` is represented without subtraction as ``4*d+3`` with ``c=S d``.

The small reusable two-square factor-fold foundations below already existed as
isolated, unadmitted candidate scripts.  They become dependencies of this new
campaign, but neither this factory nor its authoring helpers enrolls anything,
changes Stable/Alpha authority, adds an axiom, or grants checked-use status.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import prime
from .fermat_two_squares_factor_fold_candidate import (
    make_fermat_two_squares_factor_fold_candidate_theorems,
)
from .finite_fold_surface import _binders, _identifier, _variables


FACTOR_FOLD_FOUNDATION_NAMES = (
    "beta_two_square_prefix_drop_last",
    "beta_two_square_prefix_last_represented",
    "beta_two_square_represented_factor_product",
    "beta_all_prime_entry_is_prime",
    "beta_admissible_prime_factor_product_is_two_square",
    "positive_number_with_admissible_prime_divisors_is_two_square",
)

THREE_MOD_FOUR_PROGRESSION_NONZERO = "three_mod_four_progression_nonzero"
THREE_MOD_FOUR_PROGRESSION_NONUNIT = "three_mod_four_progression_nonunit"
THREE_MOD_FOUR_PROGRESSION_NOT_TWO_SQUARE = (
    "three_mod_four_progression_not_two_square"
)
THREE_MOD_FOUR_GOOD_PRIME_EXCLUSIVE = "three_mod_four_good_prime_exclusive"
THREE_MOD_FOUR_PRIME_DIVISOR_DECIDABLE = "three_mod_four_prime_divisor_decidable"
THREE_MOD_FOUR_PRIME_DIVISOR_BOUNDED_SEARCH = (
    "three_mod_four_prime_divisor_bounded_search"
)
THREE_MOD_FOUR_PRIME_DIVISOR_EXISTS = "three_mod_four_prime_divisor_exists"
EUCLID_THREE_NUMBER_SUCCESSOR_BALANCE = "euclid_three_number_successor_balance"
EUCLID_THREE_COMMON_MULTIPLE_EXCLUSION = "euclid_three_common_multiple_exclusion"
EUCLID_THREE_PRIME_DIVISOR_EXCEEDS_BOUND = (
    "euclid_three_prime_divisor_exceeds_bound"
)
EUCLID_THREE_PROGRESSION_PRIME_EXISTS = "euclid_three_progression_prime_exists"
INFINITELY_MANY_PRIMES_THREE_MOD_FOUR = "infinitely_many_primes_three_mod_four"


class PrimesThreeModFourError(ValueError):
    """A conservative progression surface or frozen factor foundation changed."""


def _context(*labelled: tuple[str, str]) -> tuple[str, ...]:
    try:
        return tuple(dict.fromkeys(_variables(*labelled)))
    except ValueError as error:
        raise PrimesThreeModFourError(str(error)) from error


def _safe_tag(tag: str) -> str:
    try:
        return _identifier(tag, "three-mod-four binder tag")
    except ValueError as error:
        raise PrimesThreeModFourError(str(error)) from error


def _three_terms(value: str, *, tag: str, avoid: tuple[str, ...]) -> str:
    try:
        (residue,) = _binders(f"ptmf_{_safe_tag(tag)}", avoid, ("residue",))
    except ValueError as error:
        raise PrimesThreeModFourError(str(error)) from error
    return f"exists {residue}. ({value}) = 4 * {residue} + 3"


def three_mod_four_relation(value: str, *, tag: str) -> str:
    """Hygienically expand the exact witnessed residue class ``value=4*k+3``."""

    variables = _context((value, "progression value"))
    return _three_terms(value, tag=tag, avoid=variables)


def _divides_terms(
    divisor: str, dividend: str, *, tag: str, avoid: tuple[str, ...]
) -> str:
    try:
        (quotient,) = _binders(f"ptmf_{_safe_tag(tag)}", avoid, ("quotient",))
    except ValueError as error:
        raise PrimesThreeModFourError(str(error)) from error
    return f"exists {quotient}. ({dividend}) = ({divisor}) * {quotient}"


def _prime_divisor_terms(
    dividend: str, divisor: str, *, tag: str, avoid: tuple[str, ...]
) -> str:
    safe_tag = _safe_tag(tag)
    primality = prime(divisor, tag=f"ptmf_{safe_tag}_prime")
    residue = _three_terms(divisor, tag=f"{safe_tag}_residue", avoid=avoid)
    divides = _divides_terms(
        divisor, dividend, tag=f"{safe_tag}_divides", avoid=avoid
    )
    return f"(({primality}) /\\ (({residue}) /\\ ({divides})))"


def three_mod_four_prime_divisor(dividend: str, divisor: str, *, tag: str) -> str:
    """Expand primality, residue ``3 mod 4``, and an actual divisor quotient."""

    variables = _context((dividend, "dividend"), (divisor, "prime divisor"))
    return _prime_divisor_terms(dividend, divisor, tag=tag, avoid=variables)


def euclid_three_number(common: str, value: str, *, tag: str) -> str:
    """Expand the subtraction-free graph ``common=S d /\ value=4*d+3``."""

    variables = _context(
        (common, "nonzero common multiple"), (value, "Euclid number")
    )
    try:
        (predecessor,) = _binders(
            f"ptmf_{_safe_tag(tag)}", variables, ("predecessor",)
        )
    except ValueError as error:
        raise PrimesThreeModFourError(str(error)) from error
    return (
        f"exists {predecessor}. "
        f"({common} = S {predecessor} /\\ {value} = 4 * {predecessor} + 3)"
    )


def _two_square(value: str, *, tag: str) -> str:
    first = f"ptmf_first_{_safe_tag(tag)}"
    second = f"ptmf_second_{_safe_tag(tag)}"
    return (
        f"exists {first} {second}. "
        f"({value}) = {first} * {first} + {second} * {second}"
    )


def _at_most(left: str, right: str, *, tag: str) -> str:
    safe_tag = _safe_tag(tag)
    return f"exists ptmf_gap_{safe_tag}. ptmf_gap_{safe_tag} + {left} = {right}"


def _common_multiple(bound: str, value: str, *, tag: str) -> str:
    safe_tag = _safe_tag(tag)
    predecessor = f"ptmf_predecessor_{safe_tag}"
    gap = f"ptmf_common_gap_{safe_tag}"
    quotient = f"ptmf_common_quotient_{safe_tag}"
    return (
        f"forall {predecessor}. "
        f"(exists {gap}. S {predecessor} + S {gap} = S {bound}) -> "
        f"exists {quotient}. {value} = S {predecessor} * {quotient}"
    )


def _factor_foundations(spec: Callable[..., Any]) -> tuple[Any, ...]:
    source = {
        row.name: row
        for row in make_fermat_two_squares_factor_fold_candidate_theorems(spec)
    }
    try:
        return tuple(source[name] for name in FACTOR_FOLD_FOUNDATION_NAMES)
    except KeyError as error:
        raise PrimesThreeModFourError(
            "the isolated constructive two-square foundation changed"
        ) from error


def make_primes_three_mod_four_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return dependency-ordered, independently kernel-checkable candidates."""

    three_n = three_mod_four_relation("n", tag="number")
    three_p = three_mod_four_relation("p", tag="prime")
    prime_p = prime("p", tag="ptmf_prime")
    bad_divisor = three_mod_four_prime_divisor("n", "p", tag="source")
    represented = _two_square("n", tag="represented")
    bounded = _at_most("p", "B", tag="search")
    excluded = f"forall p. ({bounded}) -> ~({bad_divisor})"
    discovered = f"exists p. (({bounded}) /\\ ({bad_divisor}))"
    euclid_number = "4 * d + 3"
    euclid_divisor = _prime_divisor_terms(
        euclid_number, "p", tag="euclid", avoid=("d", "p")
    )
    divides_common = _divides_terms(
        "p", "c", tag="common", avoid=("c", "p")
    )
    divides_euclid = _divides_terms(
        "p", euclid_number, tag="euclid", avoid=("d", "p")
    )
    common_multiple = _common_multiple("B", "c", tag="source")
    strict_bound = "exists gap. gap + S B = p"

    return (
        *_factor_foundations(spec),
        spec(
            THREE_MOD_FOUR_PROGRESSION_NONZERO,
            f"forall n. ({three_n}) -> ~(n = 0)",
            (),
            (
                "intro n",
                "intro hthree",
                "intro hzero",
                "cases hthree",
                "rewrite hthree_witness at hzero",
                "rewrite PA4 at hzero",
                "apply PA1",
                "exact hzero",
            ),
            "Every witnessed natural of the form 4k+3 is nonzero.",
        ),
        spec(
            THREE_MOD_FOUR_PROGRESSION_NONUNIT,
            f"forall n. ({three_n}) -> ~(n = 1)",
            (),
            (
                "intro n",
                "intro hthree",
                "intro hone",
                "cases hthree",
                "rewrite hthree_witness at hone",
                "rewrite PA4 at hone",
                "have hzero : 4 * x + 2 = 0",
                "apply PA2",
                "exact hone",
                "rewrite PA4 at hzero",
                "apply PA1",
                "exact hzero",
            ),
            "Every witnessed natural of the form 4k+3 differs from the unit one.",
        ),
        spec(
            THREE_MOD_FOUR_PROGRESSION_NOT_TWO_SQUARE,
            f"forall n. ({three_n}) -> ({represented}) -> false",
            ("three_mod_four_number_not_equal_represented",),
            (
                "intro n",
                "intro hthree",
                "intro hrepresented",
                "specialize three_mod_four_number_not_equal_represented n",
                "specialize three_mod_four_number_not_equal_represented n",
                "apply three_mod_four_number_not_equal_represented",
                "exact hthree",
                "exact hrepresented",
                "refl",
            ),
            "A witnessed three-modulo-four natural cannot have a two-square representation.",
        ),
        spec(
            THREE_MOD_FOUR_GOOD_PRIME_EXCLUSIVE,
            f"forall p. ({prime_p}) -> (p = 2 \\/ exists k. p = 4 * k + 1) "
            f"-> ({three_p}) -> false",
            (
                "prime_two_or_one_mod_four_is_sum_of_two_squares",
                THREE_MOD_FOUR_PROGRESSION_NOT_TWO_SQUARE,
            ),
            (
                "intro p",
                "intro hprime",
                "intro hgood",
                "intro hthree",
                "specialize three_mod_four_progression_not_two_square p",
                "apply three_mod_four_progression_not_two_square",
                "exact hthree",
                "specialize prime_two_or_one_mod_four_is_sum_of_two_squares p",
                "apply prime_two_or_one_mod_four_is_sum_of_two_squares",
                "exact hprime",
                "exact hgood",
            ),
            "A prime equal to two or one modulo four cannot also be three modulo four.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_DIVISOR_DECIDABLE,
            f"forall p n. (({bad_divisor}) \\/ ~({bad_divisor}))",
            (
                "prime_divides_decidable",
                "prime_mod_four_good_or_three",
                THREE_MOD_FOUR_GOOD_PRIME_EXCLUSIVE,
            ),
            (
                "intro p",
                "intro n",
                "specialize prime_divides_decidable p",
                "specialize prime_divides_decidable n",
                "cases prime_divides_decidable",
                "cases prime_divides_decidable_left",
                "have hclass : (p = 2 \\/ exists k. p = 4 * k + 1) \\/ "
                "exists k. p = 4 * k + 3",
                "specialize prime_mod_four_good_or_three p",
                "apply prime_mod_four_good_or_three",
                "exact prime_divides_decidable_left_left",
                "cases hclass",
                "right",
                "intro hbad",
                "cases hbad",
                "cases hbad_right",
                "specialize three_mod_four_good_prime_exclusive p",
                "apply three_mod_four_good_prime_exclusive",
                "exact prime_divides_decidable_left_left",
                "exact hclass_left",
                "exact hbad_right_left",
                "left",
                "split",
                "exact prime_divides_decidable_left_left",
                "split",
                "exact hclass_right",
                "exact prime_divides_decidable_left_right",
                "right",
                "intro hbad",
                "cases hbad",
                "cases hbad_right",
                "apply prime_divides_decidable_right",
                "split",
                "exact hbad_left",
                "exact hbad_right_right",
            ),
            "For every candidate and dividend, actual three-mod-four prime divisibility is constructively decidable.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_DIVISOR_BOUNDED_SEARCH,
            f"forall B n. (({excluded}) \\/ ({discovered}))",
            (
                "le_zero",
                "prime_nonzero",
                THREE_MOD_FOUR_PRIME_DIVISOR_DECIDABLE,
                "le_refl",
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "le_succ",
            ),
            (
                "induction B",
                "intro n",
                "left",
                "intro p",
                "intro hbound",
                "intro hbad",
                "cases hbad",
                "have hpzero : p = 0",
                "specialize le_zero p",
                "apply le_zero",
                "exact hbound",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hbad_left",
                "exact hpzero",
                "intro n",
                "specialize three_mod_four_prime_divisor_decidable (S B)",
                "specialize three_mod_four_prime_divisor_decidable n",
                "cases three_mod_four_prime_divisor_decidable",
                "right",
                "exists S B",
                "split",
                "specialize le_refl (S B)",
                "exact le_refl",
                "exact three_mod_four_prime_divisor_decidable_left",
                "specialize IH n",
                "cases IH",
                "left",
                "intro p",
                "intro hbound",
                "intro hbad",
                "have hsplit : p = S B \\/ exists h. h + S p = S B",
                "specialize le_eq_or_lt p",
                "specialize le_eq_or_lt (S B)",
                "apply le_eq_or_lt",
                "exact hbound",
                "cases hsplit",
                "cases hbad",
                "cases hbad_right",
                "rewrite hsplit_left at hbad_left",
                "rewrite hsplit_left at hbad_left",
                "rewrite hsplit_left at hbad_right_left",
                "rewrite hsplit_left at hbad_right_right",
                "apply three_mod_four_prime_divisor_decidable_right",
                "split",
                "exact hbad_left",
                "split",
                "exact hbad_right_left",
                "exact hbad_right_right",
                "specialize IH_left p",
                "apply IH_left",
                "specialize le_of_succ_le_succ p",
                "specialize le_of_succ_le_succ B",
                "apply le_of_succ_le_succ",
                "exact hsplit_right",
                "exact hbad",
                "right",
                "cases IH_right",
                "cases IH_right_witness",
                "exists x",
                "split",
                "specialize le_succ x",
                "specialize le_succ B",
                "apply le_succ",
                "exact IH_right_witness_left",
                "exact IH_right_witness_right",
            ),
            "Finite induction either excludes every three-mod-four prime divisor up to the supplied bound or returns an actual bounded prime-divisor witness.",
        ),
        spec(
            THREE_MOD_FOUR_PRIME_DIVISOR_EXISTS,
            f"forall n. ({three_n}) -> exists p. ({bad_divisor})",
            (
                THREE_MOD_FOUR_PROGRESSION_NONZERO,
                THREE_MOD_FOUR_PRIME_DIVISOR_BOUNDED_SEARCH,
                "positive_number_with_admissible_prime_divisors_is_two_square",
                "prime_mod_four_good_or_three",
                "divisor_le_nonzero",
                THREE_MOD_FOUR_PROGRESSION_NOT_TWO_SQUARE,
            ),
            (
                "intro n",
                "intro hthree",
                "have hnonzero : ~(n = 0)",
                "intro hzero",
                "specialize three_mod_four_progression_nonzero n",
                "apply three_mod_four_progression_nonzero",
                "exact hthree",
                "exact hzero",
                "specialize three_mod_four_prime_divisor_bounded_search n",
                "specialize three_mod_four_prime_divisor_bounded_search n",
                "cases three_mod_four_prime_divisor_bounded_search",
                "exfalso",
                f"have hrepresented : {represented}",
                "specialize positive_number_with_admissible_prime_divisors_is_two_square n",
                "apply positive_number_with_admissible_prime_divisors_is_two_square",
                "exact hnonzero",
                "intro p",
                "intro hprime",
                "intro hdivides",
                "have hclass : (p = 2 \\/ exists k. p = 4 * k + 1) \\/ "
                "exists k. p = 4 * k + 3",
                "specialize prime_mod_four_good_or_three p",
                "apply prime_mod_four_good_or_three",
                "exact hprime",
                "cases hclass",
                "exact hclass_left",
                "exfalso",
                "specialize three_mod_four_prime_divisor_bounded_search_left p",
                "apply three_mod_four_prime_divisor_bounded_search_left",
                "specialize divisor_le_nonzero p",
                "specialize divisor_le_nonzero n",
                "apply divisor_le_nonzero",
                "exact hnonzero",
                "exact hdivides",
                "split",
                "exact hprime",
                "split",
                "exact hclass_right",
                "exact hdivides",
                "specialize three_mod_four_progression_not_two_square n",
                "apply three_mod_four_progression_not_two_square",
                "exact hthree",
                "exact hrepresented",
                "cases three_mod_four_prime_divisor_bounded_search_right",
                "cases three_mod_four_prime_divisor_bounded_search_right_witness",
                "exists x",
                "exact three_mod_four_prime_divisor_bounded_search_right_witness_right",
            ),
            "Every natural congruent to three modulo four has an actual prime divisor congruent to three modulo four, obtained by constructive finite search and beta-coded prime factorization.",
        ),
        spec(
            EUCLID_THREE_NUMBER_SUCCESSOR_BALANCE,
            "forall d. (4 * d + 3) + 1 = 4 * S d",
            (),
            (
                "intro d",
                "simp",
            ),
            "The subtraction-free Euclid number 4d+3 satisfies the exact identity (4d+3)+1=4(d+1).",
        ),
        spec(
            EUCLID_THREE_PROGRESSION_PRIME_EXISTS,
            f"forall d. exists p. ({euclid_divisor})",
            (THREE_MOD_FOUR_PRIME_DIVISOR_EXISTS,),
            (
                "intro d",
                "specialize three_mod_four_prime_divisor_exists (4 * d + 3)",
                "apply three_mod_four_prime_divisor_exists",
                "exists d",
                "refl",
            ),
            "Every actual subtraction-free Euclid number 4d+3 has a witnessed prime divisor congruent to three modulo four.",
        ),
        spec(
            EUCLID_THREE_COMMON_MULTIPLE_EXCLUSION,
            f"forall c d p. c = S d -> ({prime_p}) -> ({divides_common}) -> "
            f"({divides_euclid}) -> false",
            (
                "multiple_mul_left",
                "divides_remainder",
                "mul_one",
                EUCLID_THREE_NUMBER_SUCCESSOR_BALANCE,
                "divisor_one",
            ),
            (
                "intro c",
                "intro d",
                "intro p",
                "intro hpredecessor",
                "intro hprime",
                "intro hcommon",
                "intro heuclid",
                "have hfour : exists q. 4 * c = p * q",
                "specialize multiple_mul_left p",
                "specialize multiple_mul_left c",
                "specialize multiple_mul_left 4",
                "apply multiple_mul_left",
                "exact hcommon",
                "have hone : exists q. 1 = p * q",
                "specialize divides_remainder p",
                "specialize divides_remainder (4 * c)",
                "specialize divides_remainder (4 * d + 3)",
                "specialize divides_remainder 1",
                "specialize divides_remainder 1",
                "apply divides_remainder",
                "exact hfour",
                "exact heuclid",
                "rewrite hpredecessor",
                "specialize mul_one (4 * d + 3)",
                "rewrite mul_one",
                "symm",
                "specialize euclid_three_number_successor_balance d",
                "exact euclid_three_number_successor_balance",
                "have hunit : p = 1",
                "specialize divisor_one p",
                "apply divisor_one",
                "exact hone",
                "cases hprime",
                "apply hprime_left",
                "exact hunit",
            ),
            "No prime dividing a nonzero common multiple can also divide its subtraction-free Euclid number 4c−1.",
        ),
        spec(
            EUCLID_THREE_PRIME_DIVISOR_EXCEEDS_BOUND,
            f"forall B c d p. ({common_multiple}) -> c = S d -> ({prime_p}) -> "
            f"({divides_euclid}) -> ({strict_bound})",
            (
                "le_or_lt",
                "bounded_common_multiple_contains_bounded_prime",
                EUCLID_THREE_COMMON_MULTIPLE_EXCLUSION,
            ),
            (
                "intro B",
                "intro c",
                "intro d",
                "intro p",
                "intro hcommon",
                "intro hpredecessor",
                "intro hprime",
                "intro heuclid",
                "specialize le_or_lt p",
                "specialize le_or_lt B",
                "cases le_or_lt",
                "exfalso",
                "have hdivides : exists q. c = p * q",
                "specialize bounded_common_multiple_contains_bounded_prime B",
                "specialize bounded_common_multiple_contains_bounded_prime c",
                "specialize bounded_common_multiple_contains_bounded_prime p",
                "apply bounded_common_multiple_contains_bounded_prime",
                "exact hcommon",
                "exact hprime",
                "exact le_or_lt_left",
                "specialize euclid_three_common_multiple_exclusion c",
                "specialize euclid_three_common_multiple_exclusion d",
                "specialize euclid_three_common_multiple_exclusion p",
                "apply euclid_three_common_multiple_exclusion",
                "exact hpredecessor",
                "exact hprime",
                "exact hdivides",
                "exact heuclid",
                "exact le_or_lt_right",
            ),
            "Every prime divisor of the exact Euclid number 4c−1 lies strictly above the bound encoded by its nonzero common multiple c.",
        ),
        spec(
            INFINITELY_MANY_PRIMES_THREE_MOD_FOUR,
            f"forall B. exists p. (({prime_p}) /\\ "
            f"(({strict_bound}) /\\ ({three_p})))",
            (
                "bounded_common_multiple_exists",
                "nonzero_is_succ",
                EUCLID_THREE_PROGRESSION_PRIME_EXISTS,
                EUCLID_THREE_PRIME_DIVISOR_EXCEEDS_BOUND,
            ),
            (
                "intro B",
                "specialize bounded_common_multiple_exists B",
                "cases bounded_common_multiple_exists",
                "cases bounded_common_multiple_exists_witness",
                "have hpredecessor : exists d. x = S d",
                "specialize nonzero_is_succ x",
                "apply nonzero_is_succ",
                "exact bounded_common_multiple_exists_witness_left",
                "cases hpredecessor",
                "specialize euclid_three_progression_prime_exists x1",
                "cases euclid_three_progression_prime_exists",
                "cases euclid_three_progression_prime_exists_witness",
                "cases euclid_three_progression_prime_exists_witness_right",
                "exists x2",
                "split",
                "exact euclid_three_progression_prime_exists_witness_left",
                "split",
                "specialize euclid_three_prime_divisor_exceeds_bound B",
                "specialize euclid_three_prime_divisor_exceeds_bound x",
                "specialize euclid_three_prime_divisor_exceeds_bound x1",
                "specialize euclid_three_prime_divisor_exceeds_bound x2",
                "apply euclid_three_prime_divisor_exceeds_bound",
                "exact bounded_common_multiple_exists_witness_right",
                "exact hpredecessor_witness",
                "exact euclid_three_progression_prime_exists_witness_left",
                "exact euclid_three_progression_prime_exists_witness_right_right",
                "exact euclid_three_progression_prime_exists_witness_right_left",
            ),
            "For every natural bound, construct an actual strictly larger prime with an explicit residue witness p=4k+3.",
        ),
    )


__all__ = [
    "FACTOR_FOLD_FOUNDATION_NAMES",
    "INFINITELY_MANY_PRIMES_THREE_MOD_FOUR",
    "PrimesThreeModFourError",
    "euclid_three_number",
    "make_primes_three_mod_four_candidate_theorems",
    "three_mod_four_prime_divisor",
    "three_mod_four_relation",
]
