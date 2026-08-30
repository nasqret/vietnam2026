"""Native finite-prime certificates for the Bertrand small range.

This isolated candidate tranche first proves a generic trial-division
criterion below a displayed square.  It then supplies compact remainder
algebra used by the concrete prime certificates required by the final finite
cover.  Every readable relation expands into ordinary first-order Peano
arithmetic before parsing; no host computation becomes theorem authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .bertrand_primorial_foundation_candidate import (
    _lt_term,
    _render_term,
    _validated_context,
)
from .bertrand_primorial_membership_candidate import _divides_term, _le_term


FIXED_NONTRIVIAL_FACTOR_NOT_PRIME = (
    "fixed_nontrivial_factor_not_prime"
)
FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE = (
    "factor_pair_has_small_member_below_square"
)
NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE = (
    "nonprime_has_small_prime_divisor_below_square"
)
PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE = (
    "prime_of_no_small_prime_divisor_below_square"
)
PRIME_LE_TWENTY_TWO_CASES = "prime_le_twenty_two_cases"
NONZERO_REMAINDER_NOT_MULTIPLE = "nonzero_remainder_not_multiple"
SCALED_REMAINDER_LIFT = "scaled_remainder_lift"
ADD_REMAINDER_LIFT = "add_remainder_lift"
DOUBLE_SCALED_REMAINDER_LIFT = "double_scaled_remainder_lift"
PRIME_FIVE = "prime_five"
PRIME_SEVEN = "prime_seven"
PRIME_THIRTEEN = "prime_thirteen"
PRIME_TWENTY_THREE = "prime_twenty_three"
PRIME_FORTY_THREE = "prime_forty_three"
PRIME_EIGHTY_THREE = "prime_eighty_three"
PRIME_ONE_HUNDRED_SIXTY_THREE = "prime_one_hundred_sixty_three"
PRIME_THREE_HUNDRED_SEVENTEEN = "prime_three_hundred_seventeen"
PRIME_FIVE_HUNDRED_TWENTY_ONE = "prime_five_hundred_twenty_one"


_CERTIFICATES = (
    (PRIME_FIVE, "5", 5, 2, None),
    (PRIME_SEVEN, "7", 7, 2, None),
    (PRIME_THIRTEEN, "13", 13, 3, None),
    (PRIME_TWENTY_THREE, "23", 23, 4, None),
    (PRIME_FORTY_THREE, "43", 43, 6, None),
    (PRIME_EIGHTY_THREE, "9 * 9 + 2", 83, 9, (9, 9, 2)),
    (
        PRIME_ONE_HUNDRED_SIXTY_THREE,
        "13 * 12 + 7",
        163,
        12,
        (13, 12, 7),
    ),
    (
        PRIME_THREE_HUNDRED_SEVENTEEN,
        "18 * 17 + 11",
        317,
        17,
        (18, 17, 11),
    ),
    (
        PRIME_FIVE_HUNDRED_TWENTY_ONE,
        "2 * (11 * 22) + 37",
        521,
        22,
        (2, "11 * 22", 37),
    ),
)

_TRIAL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19)


def _render(
    source: str,
    *,
    label: str,
    variables: tuple[str, ...],
) -> str:
    return _render_term(
        source,
        label=label,
        context=_validated_context(variables),
    )


def _prime_cases_result(p: str) -> str:
    values = (2, 3, 5, 7, 11, 13, 17, 19)
    result = f"{p} = {values[-1]}"
    for value in reversed(values[:-1]):
        result = f"{p} = {value} \\/ ({result})"
    return result


def _factorization_refutation(
    value: int,
    left: int,
    right: int,
    split_name: str,
) -> tuple[str, ...]:
    return (
        "exfalso",
        f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} p",
        f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} {left}",
        f"specialize {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME} {right}",
        f"apply {FIXED_NONTRIVIAL_FACTOR_NOT_PRIME}",
        f"trans {value}",
        f"exact {split_name}_left",
        "norm_num",
        "intro hleft_one",
        "apply PA1",
        "apply PA2",
        "exact hleft_one",
        "intro hright_one",
        "apply PA1",
        "apply PA2",
        "exact hright_one",
        "exact hp",
    )


def _prime_cases_script() -> tuple[str, ...]:
    primes = (2, 3, 5, 7, 11, 13, 17, 19)
    factors = {
        4: (2, 2),
        6: (2, 3),
        8: (2, 4),
        9: (3, 3),
        10: (2, 5),
        12: (3, 4),
        14: (2, 7),
        15: (3, 5),
        16: (4, 4),
        18: (3, 6),
        20: (4, 5),
        21: (3, 7),
        22: (2, 11),
    }
    script: list[str] = ["intro p", "intro hp", "intro hbound"]
    bound_name = "hbound"
    for value in range(22, 1, -1):
        split_name = f"hsplit_{value}"
        script.extend(
            (
                f"have {split_name} : p = {value} \\/ "
                f"(exists k. k + S p = {value})",
                f"specialize le_eq_or_lt p",
                f"specialize le_eq_or_lt {value}",
                "apply le_eq_or_lt",
                f"exact {bound_name}",
                f"cases {split_name}",
            )
        )
        if value in primes:
            position = primes.index(value)
            script.extend("right" for _ in range(position))
            if position < len(primes) - 1:
                script.append("left")
            script.append(f"exact {split_name}_left")
        else:
            left, right = factors[value]
            script.extend(
                _factorization_refutation(
                    value,
                    left,
                    right,
                    split_name,
                )
            )
        if value == 2:
            script.extend(
                (
                    "have hshape : exists k. p = S (S k)",
                    "specialize prime_is_succ_succ p",
                    "apply prime_is_succ_succ",
                    "exact hp",
                    "cases hshape",
                    "have htwo : exists k. k + 2 = p",
                    "exists x",
                    "trans S (S x)",
                    "rewrite PA4",
                    "rewrite PA4",
                    "rewrite PA3",
                    "refl",
                    "symm",
                    "exact hshape_witness",
                    "exfalso",
                    "specialize lt_not_le p",
                    "specialize lt_not_le 2",
                    "apply lt_not_le",
                    f"exact {split_name}_right",
                    "exact htwo",
                )
            )
        else:
            next_bound = f"hbound_{value - 1}"
            script.extend(
                (
                    f"have {next_bound} : exists k. k + p = {value - 1}",
                    "apply le_of_succ_le_succ",
                    f"exact {split_name}_right",
                )
            )
            bound_name = next_bound
    return tuple(script)


def _numeric_nonzero_script(name: str) -> tuple[str, ...]:
    return (
        f"intro {name}",
        "apply PA1",
        f"exact {name}",
    )


def _numeric_nonunit_script(name: str) -> tuple[str, ...]:
    return (
        f"intro {name}",
        "apply PA1",
        "apply PA2",
        f"exact {name}",
    )


def _remainder_nonzero_script(name: str) -> tuple[str, ...]:
    return (
        f"intro {name}",
        "apply PA1",
        f"exact {name}",
    )


def _direct_not_divides_script(
    *,
    target: str,
    number: int,
    divisor: int,
    tag: str,
) -> tuple[str, ...]:
    quotient, remainder = divmod(number, divisor)
    if remainder == 0:
        raise AssertionError("trial divisor unexpectedly divides certificate")
    relation = _divides_term(
        str(divisor),
        target,
        tag=f"{tag}_not_{divisor}",
        variables=(),
    )
    return (
        f"have hnot_{divisor} : ~({relation})",
        f"intro hnot_{divisor}_source",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {divisor}",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} ({target})",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {quotient}",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {remainder}",
        f"apply {NONZERO_REMAINDER_NOT_MULTIPLE}",
        "norm_num",
        *_remainder_nonzero_script(f"hrem_{divisor}_zero"),
        f"exists {divisor - remainder - 1}",
        "norm_num",
        f"exact hnot_{divisor}_source",
    )


def _single_scaled_not_divides_script(
    *,
    target: str,
    divisor: int,
    coefficient: int,
    base: int,
    tail: int,
    tag: str,
) -> tuple[str, ...]:
    base_quotient, base_remainder = divmod(base, divisor)
    tail_value = coefficient * base_remainder + tail
    tail_quotient, remainder = divmod(tail_value, divisor)
    if remainder == 0:
        raise AssertionError("trial divisor unexpectedly divides certificate")
    quotient_term = f"{coefficient} * {base_quotient} + {tail_quotient}"
    relation = _divides_term(
        str(divisor),
        target,
        tag=f"{tag}_not_{divisor}",
        variables=(),
    )
    return (
        f"have hdivision_{divisor} : ({target}) = "
        f"{divisor} * ({quotient_term}) + {remainder}",
        f"specialize {SCALED_REMAINDER_LIFT} {divisor}",
        f"specialize {SCALED_REMAINDER_LIFT} {base}",
        f"specialize {SCALED_REMAINDER_LIFT} {base_quotient}",
        f"specialize {SCALED_REMAINDER_LIFT} {base_remainder}",
        f"specialize {SCALED_REMAINDER_LIFT} {coefficient}",
        f"specialize {SCALED_REMAINDER_LIFT} {tail}",
        f"specialize {SCALED_REMAINDER_LIFT} {tail_quotient}",
        f"specialize {SCALED_REMAINDER_LIFT} {remainder}",
        f"apply {SCALED_REMAINDER_LIFT}",
        "norm_num",
        "norm_num",
        f"have hnot_{divisor} : ~({relation})",
        f"intro hnot_{divisor}_source",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {divisor}",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} ({target})",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} "
        f"({quotient_term})",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {remainder}",
        f"apply {NONZERO_REMAINDER_NOT_MULTIPLE}",
        f"exact hdivision_{divisor}",
        *_remainder_nonzero_script(f"hrem_{divisor}_zero"),
        f"exists {divisor - remainder - 1}",
        "norm_num",
        f"exact hnot_{divisor}_source",
    )


def _double_scaled_not_divides_script(
    *,
    target: str,
    divisor: int,
    tag: str,
) -> tuple[str, ...]:
    base_quotient, base_remainder = divmod(22, divisor)
    first_value = 11 * base_remainder
    first_tail_quotient, first_remainder = divmod(first_value, divisor)
    second_value = 2 * first_remainder + 37
    second_tail_quotient, remainder = divmod(second_value, divisor)
    if remainder == 0:
        raise AssertionError("trial divisor unexpectedly divides certificate")
    first_quotient = f"11 * {base_quotient} + {first_tail_quotient}"
    final_quotient = f"2 * ({first_quotient}) + {second_tail_quotient}"
    relation = _divides_term(
        str(divisor),
        target,
        tag=f"{tag}_not_{divisor}",
        variables=(),
    )
    return (
        f"have hnot_{divisor} : ~({relation})",
        f"intro hnot_{divisor}_source",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {divisor}",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} ({target})",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} "
        f"({final_quotient})",
        f"specialize {NONZERO_REMAINDER_NOT_MULTIPLE} {remainder}",
        f"apply {NONZERO_REMAINDER_NOT_MULTIPLE}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} {divisor}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} 22",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} {base_quotient}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} {base_remainder}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} "
        f"{first_tail_quotient}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} {first_remainder}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} "
        f"{second_tail_quotient}",
        f"specialize {DOUBLE_SCALED_REMAINDER_LIFT} {remainder}",
        f"apply {DOUBLE_SCALED_REMAINDER_LIFT}",
        "norm_num",
        "norm_num",
        "norm_num",
        *_remainder_nonzero_script(f"hrem_{divisor}_zero"),
        f"exists {divisor - remainder - 1}",
        "norm_num",
        f"exact hnot_{divisor}_source",
    )


def _large_nonzero_nonunit_script(
    *,
    coefficient: int,
    base: int | str,
    tail: int,
) -> tuple[str, ...]:
    return (
        "have hn0 : ~("
        f"{coefficient} * ({base}) + {tail} = 0)",
        "intro hzero",
        f"have htail_zero : {tail} = 0",
        f"specialize add_eq_zero_right ({coefficient} * ({base}))",
        f"specialize add_eq_zero_right {tail}",
        "apply add_eq_zero_right",
        "exact hzero",
        "apply PA1",
        "exact htail_zero",
        "have hn1 : ~("
        f"{coefficient} * ({base}) + {tail} = 1)",
        "intro hone",
        f"have htail_le_one : exists k. k + {tail} = 1",
        f"exists {coefficient} * ({base})",
        "exact hone",
        f"have hone_lt_tail : exists k. k + S 1 = {tail}",
        f"exists {tail - 2}",
        "norm_num",
        f"specialize le_not_lt {tail}",
        "specialize le_not_lt 1",
        "apply le_not_lt",
        "exact htail_le_one",
        "exact hone_lt_tail",
    )


def _large_square_bound_script(
    *,
    coefficient: int,
    base: int | str,
    tail: int,
    bound: int,
    tag: str,
) -> tuple[str, ...]:
    relation = _lt_term(
        f"{coefficient} * ({base}) + {tail}",
        f"S {bound} * S {bound}",
        tag=f"{tag}_square",
        avoid=(),
    )
    if coefficient == bound + 1 and base == bound:
        gap = coefficient - tail - 1
        return (
            f"have hsquare : {relation}",
            f"exists {gap}",
            f"trans {coefficient} * {base} + {coefficient}",
            "rewrite <- PA4",
            f"trans {coefficient} * {base} + "
            f"({gap} + S {tail})",
            f"trans ({gap} + {coefficient} * {base}) + S {tail}",
            "symm",
            "apply add_assoc",
            f"trans ({coefficient} * {base} + {gap}) + S {tail}",
            "congr",
            "apply add_comm",
            "refl",
            "apply add_assoc",
            "congr",
            "refl",
            "norm_num",
            "symm",
            "apply PA6",
        )
    if (coefficient, base, tail, bound) == (2, "11 * 22", 37, 22):
        return (
            f"have hsquare : {relation}",
            "exists 7",
            "have hvalue : 2 * (11 * 22) + 37 = 23 * 22 + 15",
            "symm",
            "have hcoeff : 23 = 2 * 11 + 1",
            "norm_num",
            "rewrite hcoeff",
            "trans ((2 * 11) * 22 + 1 * 22) + 15",
            "congr",
            "apply add_mul",
            "refl",
            "trans (2 * (11 * 22) + 22) + 15",
            "congr",
            "congr",
            "apply mul_assoc",
            "apply one_mul",
            "refl",
            "trans 2 * (11 * 22) + (22 + 15)",
            "apply add_assoc",
            "trans 2 * (11 * 22) + 37",
            "congr",
            "refl",
            "norm_num",
            "refl",
            "rewrite hvalue",
            "trans 23 * 22 + 23",
            "rewrite <- PA4",
            "trans 23 * 22 + (7 + S 15)",
            "trans (7 + 23 * 22) + S 15",
            "symm",
            "apply add_assoc",
            "trans (23 * 22 + 7) + S 15",
            "congr",
            "apply add_comm",
            "refl",
            "apply add_assoc",
            "congr",
            "refl",
            "norm_num",
            "symm",
            "apply PA6",
        )
    if (coefficient, base, tail, bound) != (9, 9, 2, 9):
        raise AssertionError("unsupported compact square-bound shape")
    return (
        f"have hsquare : {relation}",
        "exists 16",
        "trans (9 * 9 + 9) + 10",
        "rewrite <- PA4",
        "trans 9 * 9 + (16 + S 2)",
        "trans (16 + 9 * 9) + S 2",
        "symm",
        "apply add_assoc",
        "trans (9 * 9 + 16) + S 2",
        "congr",
        "apply add_comm",
        "refl",
        "apply add_assoc",
        "trans 9 * 9 + (9 + 10)",
        "congr",
        "refl",
        "norm_num",
        "symm",
        "apply add_assoc",
        "symm",
        "trans 10 * 9 + 10",
        "apply PA6",
        "congr",
        "apply mul_succ_left",
        "refl",
    )


def _certificate_case_script(
    *,
    target: str,
    number: int,
    bound: int,
    divisors: tuple[int, ...],
    large_data: tuple[int, int, int] | None,
    tag: str,
) -> tuple[str, ...]:
    script: list[str] = []
    current = "hcases"
    for index, value in enumerate(_TRIAL_PRIMES):
        if index < len(_TRIAL_PRIMES) - 1:
            script.append(f"cases {current}")
            equality = f"{current}_left"
            next_current = f"{current}_right"
        else:
            equality = current
            next_current = current
        if value in divisors:
            if large_data is None:
                branch = list(
                    _direct_not_divides_script(
                        target=target,
                        number=number,
                        divisor=value,
                        tag=tag,
                    )
                )
            elif number == 521:
                branch = list(
                    _double_scaled_not_divides_script(
                        target=target,
                        divisor=value,
                        tag=tag,
                    )
                )
            else:
                coefficient, base, tail = large_data
                branch = list(
                    _single_scaled_not_divides_script(
                        target=target,
                        divisor=value,
                        coefficient=coefficient,
                        base=base,
                        tail=tail,
                        tag=tag,
                    )
                )
            not_index = next(
                branch_index
                for branch_index, command in enumerate(branch)
                if command.startswith(f"have hnot_{value} :")
            )
            del branch[not_index : not_index + 2]
            if not branch[-1].startswith(f"exact hnot_{value}_source"):
                raise AssertionError("unexpected remainder branch suffix")
            branch[-1] = "exact hdivides"
            script.append(f"rewrite {equality} at hdivides")
            script.extend(branch)
        else:
            script.extend(
                (
                    f"have htoo_large_{value} : "
                    f"exists k. k + S {bound} = {value}",
                    f"exists {value - bound - 1}",
                    "norm_num",
                    f"specialize lt_not_le {bound}",
                    f"specialize lt_not_le {value}",
                    "apply lt_not_le",
                    f"exact htoo_large_{value}",
                    f"rewrite {equality} at hp_bound",
                    "exact hp_bound",
                )
            )
        current = next_current
    return tuple(script)


def make_bertrand_b8_prime_certificate_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered finite-certificate tranche."""

    factor_variables = ("n", "a", "b")
    factor_prime = _prime_relation_term(
        "n",
        tag="bb8fnfp_prime",
        variables=factor_variables,
    )

    small_variables = ("B", "n", "a", "b")
    small_bound = _lt_term(
        "n",
        "S B * S B",
        tag="bb8fps_bound",
        avoid=small_variables,
    )
    small_left = _le_term(
        "a",
        "B",
        tag="bb8fps_left",
        variables=small_variables,
    )
    small_right = _le_term(
        "b",
        "B",
        tag="bb8fps_right",
        variables=small_variables,
    )

    divisor_variables = ("B", "n")
    divisor_prime = _prime_relation_term(
        "p",
        tag="bb8npsp_prime",
        variables=divisor_variables + ("p",),
    )
    divisor_bound = _le_term(
        "p",
        "B",
        tag="bb8npsp_bound",
        variables=divisor_variables + ("p",),
    )
    divisor_relation = _divides_term(
        "p",
        "n",
        tag="bb8npsp_divides",
        variables=divisor_variables + ("p",),
    )
    bounded_prime = _prime_relation_term(
        "n",
        tag="bb8npsp_source",
        variables=divisor_variables,
    )
    bounded_square = _lt_term(
        "n",
        "S B * S B",
        tag="bb8npsp_square",
        avoid=divisor_variables,
    )
    divisor_exists = (
        f"exists p. ({divisor_prime}) /\\ "
        f"(({divisor_bound}) /\\ ({divisor_relation}))"
    )

    criterion_prime = _prime_relation_term(
        "n",
        tag="bb8pnsp_result",
        variables=divisor_variables,
    )
    criterion_test_prime = _prime_relation_term(
        "p",
        tag="bb8pnsp_prime",
        variables=divisor_variables + ("p",),
    )
    criterion_test_bound = _le_term(
        "p",
        "B",
        tag="bb8pnsp_bound",
        variables=divisor_variables + ("p",),
    )
    criterion_test_divides = _divides_term(
        "p",
        "n",
        tag="bb8pnsp_divides",
        variables=divisor_variables + ("p",),
    )
    criterion_square = _lt_term(
        "n",
        "S B * S B",
        tag="bb8pnsp_square",
        avoid=divisor_variables,
    )

    cases_variables = ("p",)
    cases_prime = _prime_relation_term(
        "p",
        tag="bb8p22_prime",
        variables=cases_variables,
    )
    cases_bound = _le_term(
        "p",
        "22",
        tag="bb8p22_bound",
        variables=cases_variables,
    )

    remainder_variables = ("d", "n", "q", "r")
    remainder_lt = _lt_term(
        "r",
        "d",
        tag="bb8rn_lt",
        avoid=remainder_variables,
    )
    remainder_divides = _divides_term(
        "d",
        "n",
        tag="bb8rn_divides",
        variables=remainder_variables,
    )

    support = (
        spec(
            FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
            "forall n a b. n = a * b -> ~(a = 1) -> ~(b = 1) -> "
            f"({factor_prime}) -> false",
            (),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro hfactor",
                "intro ha",
                "intro hb",
                "intro hprime",
                "cases hprime",
                "specialize hprime_right a",
                "specialize hprime_right b",
                "have hunit : a = 1 \\/ b = 1",
                "apply hprime_right",
                "exact hfactor",
                "cases hunit",
                "apply ha",
                "exact hunit_left",
                "apply hb",
                "exact hunit_right",
            ),
            "A displayed nontrivial factorization refutes primality.",
        ),
        spec(
            FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
            "forall B n a b. n = a * b -> "
            f"({small_bound}) -> ({small_left}) \\/ ({small_right})",
            (
                "le_total",
                "le_or_lt",
                "mul_le_mul_right",
                "mul_le_mul_left",
                "le_trans",
                "lt_not_le",
            ),
            (
                "intro B",
                "intro n",
                "intro a",
                "intro b",
                "intro hfactor",
                "intro hbound",
                "specialize le_total a",
                "specialize le_total b",
                "have horder : (exists k. k + a = b) \\/ "
                "(exists k. k + b = a)",
                "exact le_total",
                "cases horder",
                "specialize le_or_lt a",
                "specialize le_or_lt B",
                "have hsmall : (exists k. k + a = B) \\/ "
                "(exists k. k + S B = a)",
                "exact le_or_lt",
                "cases hsmall",
                "left",
                "exact hsmall_left",
                "exfalso",
                "have hsb : exists k. k + S B = b",
                "specialize le_trans (S B)",
                "specialize le_trans a",
                "specialize le_trans b",
                "apply le_trans",
                "exact hsmall_right",
                "exact horder_left",
                "have hfirst : exists k. k + S B * S B = a * S B",
                "specialize mul_le_mul_right (S B)",
                "specialize mul_le_mul_right a",
                "specialize mul_le_mul_right (S B)",
                "apply mul_le_mul_right",
                "exact hsmall_right",
                "have hsquare : exists k. k + S B * S B = a * b",
                "specialize mul_le_mul_left (S B)",
                "specialize mul_le_mul_left b",
                "specialize mul_le_mul_left a",
                "have hsecond : exists k. k + a * S B = a * b",
                "apply mul_le_mul_left",
                "exact hsb",
                "specialize le_trans (S B * S B)",
                "specialize le_trans (a * S B)",
                "specialize le_trans (a * b)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "rewrite <- hfactor at hsquare",
                "specialize lt_not_le n",
                "specialize lt_not_le (S B * S B)",
                "apply lt_not_le",
                "exact hbound",
                "exact hsquare",
                "specialize le_or_lt b",
                "specialize le_or_lt B",
                "have hsmall : (exists k. k + b = B) \\/ "
                "(exists k. k + S B = b)",
                "exact le_or_lt",
                "cases hsmall",
                "right",
                "exact hsmall_left",
                "exfalso",
                "have hsa : exists k. k + S B = a",
                "specialize le_trans (S B)",
                "specialize le_trans b",
                "specialize le_trans a",
                "apply le_trans",
                "exact hsmall_right",
                "exact horder_right",
                "have hfirst : exists k. k + S B * S B = a * S B",
                "specialize mul_le_mul_right (S B)",
                "specialize mul_le_mul_right a",
                "specialize mul_le_mul_right (S B)",
                "apply mul_le_mul_right",
                "exact hsa",
                "have hsecond : exists k. k + a * S B = a * b",
                "specialize mul_le_mul_left (S B)",
                "specialize mul_le_mul_left b",
                "specialize mul_le_mul_left a",
                "apply mul_le_mul_left",
                "exact hsmall_right",
                "have hsquare : exists k. k + S B * S B = a * b",
                "specialize le_trans (S B * S B)",
                "specialize le_trans (a * S B)",
                "specialize le_trans (a * b)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "rewrite <- hfactor at hsquare",
                "specialize lt_not_le n",
                "specialize lt_not_le (S B * S B)",
                "apply lt_not_le",
                "exact hbound",
                "exact hsquare",
            ),
            "A factor pair below (B+1)^2 has a member at most B.",
        ),
        spec(
            NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
            "forall B n. ~(n = 0) -> ~(n = 1) -> "
            f"({bounded_square}) -> ~({bounded_prime}) -> "
            f"({divisor_exists})",
            (
                "prime_or_composite",
                FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE,
                "mul_zero_left",
                "prime_divisor_exists",
                "divisor_le_nonzero",
                "le_trans",
                "multiple_trans",
                "mul_comm",
            ),
            (
                "intro B",
                "intro n",
                "intro hn0",
                "intro hn1",
                "intro hbound",
                "intro hnotprime",
                "specialize prime_or_composite n",
                "have hkind : "
                "((~(n = 1) /\\ forall a b. n = a * b -> "
                "a = 1 \\/ b = 1) \\/ exists c d. "
                "((~(c = 1) /\\ ~(d = 1)) /\\ n = c * d))",
                "apply prime_or_composite",
                "exact hn0",
                "exact hn1",
                "cases hkind",
                "exfalso",
                "apply hnotprime",
                "exact hkind_left",
                "cases hkind_right",
                "cases hkind_right_witness",
                "cases hkind_right_witness_witness",
                "cases hkind_right_witness_witness_left",
                "have hsmall : (exists k. k + x = B) \\/ "
                "(exists k. k + x1 = B)",
                f"specialize {FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE} B",
                f"specialize {FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE} n",
                f"specialize {FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE} x",
                f"specialize {FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE} x1",
                f"apply {FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE}",
                "exact hkind_right_witness_witness_right",
                "exact hbound",
                "cases hsmall",
                "have hx0 : ~(x = 0)",
                "intro hx0_source",
                "apply hn0",
                "trans x * x1",
                "exact hkind_right_witness_witness_right",
                "rewrite hx0_source",
                "apply mul_zero_left",
                "have hp : exists p. "
                "((~(p = 1) /\\ forall a b. p = a * b -> "
                "a = 1 \\/ b = 1) /\\ exists q. x = p * q)",
                "specialize prime_divisor_exists x",
                "apply prime_divisor_exists",
                "exact hx0",
                "exact hkind_right_witness_witness_left_left",
                "cases hp",
                "cases hp_witness",
                "exists x2",
                "split",
                "exact hp_witness_left",
                "split",
                "have hpx : exists k. k + x2 = x",
                "specialize divisor_le_nonzero x2",
                "specialize divisor_le_nonzero x",
                "apply divisor_le_nonzero",
                "exact hx0",
                "exact hp_witness_right",
                "specialize le_trans x2",
                "specialize le_trans x",
                "specialize le_trans B",
                "apply le_trans",
                "exact hpx",
                "exact hsmall_left",
                "specialize multiple_trans x",
                "specialize multiple_trans x2",
                "specialize multiple_trans n",
                "apply multiple_trans",
                "exists x1",
                "exact hkind_right_witness_witness_right",
                "exact hp_witness_right",
                "have hswap : n = x1 * x",
                "trans x * x1",
                "exact hkind_right_witness_witness_right",
                "apply mul_comm",
                "have hx10 : ~(x1 = 0)",
                "intro hx10_source",
                "apply hn0",
                "trans x1 * x",
                "exact hswap",
                "rewrite hx10_source",
                "apply mul_zero_left",
                "have hp : exists p. "
                "((~(p = 1) /\\ forall a b. p = a * b -> "
                "a = 1 \\/ b = 1) /\\ exists q. x1 = p * q)",
                "specialize prime_divisor_exists x1",
                "apply prime_divisor_exists",
                "exact hx10",
                "exact hkind_right_witness_witness_left_right",
                "cases hp",
                "cases hp_witness",
                "exists x2",
                "split",
                "exact hp_witness_left",
                "split",
                "have hpx : exists k. k + x2 = x1",
                "specialize divisor_le_nonzero x2",
                "specialize divisor_le_nonzero x1",
                "apply divisor_le_nonzero",
                "exact hx10",
                "exact hp_witness_right",
                "specialize le_trans x2",
                "specialize le_trans x1",
                "specialize le_trans B",
                "apply le_trans",
                "exact hpx",
                "exact hsmall_right",
                "specialize multiple_trans x1",
                "specialize multiple_trans x2",
                "specialize multiple_trans n",
                "apply multiple_trans",
                "exists x",
                "exact hswap",
                "exact hp_witness_right",
            ),
            "Every composite below (B+1)^2 has a prime divisor at most B.",
        ),
        spec(
            PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
            "forall B n. ~(n = 0) -> ~(n = 1) -> "
            f"({criterion_square}) -> "
            f"(forall p. ({criterion_test_prime}) -> "
            f"({criterion_test_bound}) -> ~({criterion_test_divides})) -> "
            f"({criterion_prime})",
            (
                "prime_decidable",
                NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
            ),
            (
                "intro B",
                "intro n",
                "intro hn0",
                "intro hn1",
                "intro hsquare",
                "intro hexclude",
                "specialize prime_decidable n",
                "cases prime_decidable",
                "exact prime_decidable_left",
                "exfalso",
                f"have hp : {divisor_exists}",
                f"specialize {NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE} B",
                f"specialize {NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE} n",
                f"apply {NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE}",
                "exact hn0",
                "exact hn1",
                "exact hsquare",
                "exact prime_decidable_right",
                "cases hp",
                "cases hp_witness",
                "cases hp_witness_right",
                "specialize hexclude x",
                "apply hexclude",
                "exact hp_witness_left",
                "exact hp_witness_right_left",
                "exact hp_witness_right_right",
            ),
            "Trial division by primes through B certifies numbers below (B+1)^2.",
        ),
        spec(
            PRIME_LE_TWENTY_TWO_CASES,
            "forall p. "
            f"({cases_prime}) -> ({cases_bound}) -> "
            f"({_prime_cases_result('p')})",
            (
                "le_eq_or_lt",
                "le_of_succ_le_succ",
                "prime_is_succ_succ",
                "lt_not_le",
                FIXED_NONTRIVIAL_FACTOR_NOT_PRIME,
            ),
            _prime_cases_script(),
            "The only primes at most twenty-two are the eight displayed values.",
        ),
        spec(
            NONZERO_REMAINDER_NOT_MULTIPLE,
            "forall d n q r. n = d * q + r -> ~(r = 0) -> "
            f"({remainder_lt}) -> ~({remainder_divides})",
            (
                "multiple_refl",
                "divides_remainder",
                "divisor_le_nonzero",
                "lt_not_le",
            ),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro heq",
                "intro hr0",
                "intro hlt",
                "intro hdivides",
                "have hself : exists u. d = d * u",
                "specialize multiple_refl d",
                "exact multiple_refl",
                "have hrem : exists u. r = d * u",
                "specialize divides_remainder d",
                "specialize divides_remainder n",
                "specialize divides_remainder d",
                "specialize divides_remainder q",
                "specialize divides_remainder r",
                "apply divides_remainder",
                "exact hdivides",
                "exact hself",
                "exact heq",
                "have hle : exists k. k + d = r",
                "specialize divisor_le_nonzero d",
                "specialize divisor_le_nonzero r",
                "apply divisor_le_nonzero",
                "exact hr0",
                "exact hrem",
                "specialize lt_not_le r",
                "specialize lt_not_le d",
                "apply lt_not_le",
                "exact hlt",
                "exact hle",
            ),
            "A nonzero proper remainder refutes divisibility.",
        ),
        spec(
            SCALED_REMAINDER_LIFT,
            "forall d x q t c r s u. x = d * q + t -> "
            "c * t + r = d * s + u -> "
            "c * x + r = d * (c * q + s) + u",
            ("mul_add", "mul_assoc", "mul_comm", "add_assoc"),
            (
                "intro d",
                "intro x",
                "intro q",
                "intro t",
                "intro c",
                "intro r",
                "intro s",
                "intro u",
                "intro hx",
                "intro htail",
                "rewrite hx",
                "have hdist : c * (d * q + t) = "
                "c * (d * q) + c * t",
                "specialize mul_add c",
                "specialize mul_add (d * q)",
                "specialize mul_add t",
                "exact mul_add",
                "rewrite hdist",
                "have hassoc : (c * (d * q) + c * t) + r = "
                "c * (d * q) + (c * t + r)",
                "apply add_assoc",
                "rewrite hassoc",
                "rewrite htail",
                "have hfront : c * (d * q) = d * (c * q)",
                "trans (c * d) * q",
                "symm",
                "apply mul_assoc",
                "trans (d * c) * q",
                "congr",
                "apply mul_comm",
                "refl",
                "apply mul_assoc",
                "rewrite hfront",
                "have hdist2 : d * (c * q + s) = "
                "d * (c * q) + d * s",
                "specialize mul_add d",
                "specialize mul_add (c * q)",
                "specialize mul_add s",
                "exact mul_add",
                "rewrite hdist2",
                "symm",
                "apply add_assoc",
            ),
            "Scale a quotient-remainder equation and normalize its new tail.",
        ),
        spec(
            ADD_REMAINDER_LIFT,
            "forall d x y q s r t u v. x = d * q + r -> "
            "y = d * s + t -> r + t = d * u + v -> "
            "x + y = d * ((q + s) + u) + v",
            ("mul_add", "add_assoc", "add_comm"),
            (
                "intro d",
                "intro x",
                "intro y",
                "intro q",
                "intro s",
                "intro r",
                "intro t",
                "intro u",
                "intro v",
                "intro hx",
                "intro hy",
                "intro htail",
                "rewrite hx",
                "rewrite hy",
                "trans (d * q + d * s) + (r + t)",
                "trans d * q + (r + (d * s + t))",
                "apply add_assoc",
                "trans d * q + (d * s + (r + t))",
                "congr",
                "refl",
                "trans (r + d * s) + t",
                "symm",
                "apply add_assoc",
                "trans (d * s + r) + t",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "symm",
                "apply add_assoc",
                "trans (d * q + d * s) + (d * u + v)",
                "congr",
                "refl",
                "exact htail",
                "have hdist : d * (q + s) = d * q + d * s",
                "specialize mul_add d",
                "specialize mul_add q",
                "specialize mul_add s",
                "exact mul_add",
                "rewrite <- hdist",
                "have hassoc : (d * (q + s) + d * u) + v = "
                "d * (q + s) + (d * u + v)",
                "apply add_assoc",
                "rewrite <- hassoc",
                "have hdist2 : d * ((q + s) + u) = "
                "d * (q + s) + d * u",
                "specialize mul_add d",
                "specialize mul_add (q + s)",
                "specialize mul_add u",
                "exact mul_add",
                "rewrite <- hdist2",
                "refl",
            ),
            "Add two quotient-remainder equations and normalize their tail.",
        ),
        spec(
            DOUBLE_SCALED_REMAINDER_LIFT,
            "forall d x q t s r u v. x = d * q + t -> "
            "11 * t = d * s + r -> 2 * r + 37 = d * u + v -> "
            "2 * (11 * x) + 37 = d * (2 * (11 * q + s) + u) + v",
            (SCALED_REMAINDER_LIFT,),
            (
                "intro d",
                "intro x",
                "intro q",
                "intro t",
                "intro s",
                "intro r",
                "intro u",
                "intro v",
                "intro hx",
                "intro hfirst_tail",
                "intro hsecond_tail",
                "have hfirst : 11 * x = d * (11 * q + s) + r",
                "trans 11 * x + 0",
                "symm",
                "apply PA3",
                f"specialize {SCALED_REMAINDER_LIFT} d",
                f"specialize {SCALED_REMAINDER_LIFT} x",
                f"specialize {SCALED_REMAINDER_LIFT} q",
                f"specialize {SCALED_REMAINDER_LIFT} t",
                f"specialize {SCALED_REMAINDER_LIFT} 11",
                f"specialize {SCALED_REMAINDER_LIFT} 0",
                f"specialize {SCALED_REMAINDER_LIFT} s",
                f"specialize {SCALED_REMAINDER_LIFT} r",
                f"apply {SCALED_REMAINDER_LIFT}",
                "exact hx",
                "rewrite PA3",
                "exact hfirst_tail",
                f"specialize {SCALED_REMAINDER_LIFT} d",
                f"specialize {SCALED_REMAINDER_LIFT} (11 * x)",
                f"specialize {SCALED_REMAINDER_LIFT} (11 * q + s)",
                f"specialize {SCALED_REMAINDER_LIFT} r",
                f"specialize {SCALED_REMAINDER_LIFT} 2",
                f"specialize {SCALED_REMAINDER_LIFT} 37",
                f"specialize {SCALED_REMAINDER_LIFT} u",
                f"specialize {SCALED_REMAINDER_LIFT} v",
                f"apply {SCALED_REMAINDER_LIFT}",
                "exact hfirst",
                "exact hsecond_tail",
            ),
            "Compose the two bounded scaling steps used by the 521 certificate.",
        ),
    )

    certificates: list[Any] = []
    for name, target, number, bound, large_data in _CERTIFICATES:
        tag = f"bb8cert_{name}"
        result_prime = _prime_relation_term(
            target,
            tag=tag,
            variables=(),
        )
        script: list[str] = []
        if large_data is None:
            script.extend(
                (
                    "have hn0 : ~("
                    f"{target} = 0)",
                    *_numeric_nonzero_script("hzero"),
                    "have hn1 : ~("
                    f"{target} = 1)",
                    *_numeric_nonunit_script("hone"),
                )
            )
            square = (bound + 1) * (bound + 1)
            square_relation = _lt_term(
                target,
                f"S {bound} * S {bound}",
                tag=f"{tag}_square",
                avoid=(),
            )
            script.extend(
                (
                    f"have hsquare : {square_relation}",
                    f"exists {square - number - 1}",
                    "norm_num",
                )
            )
        else:
            coefficient, base, tail = large_data
            script.extend(
                _large_nonzero_nonunit_script(
                    coefficient=coefficient,
                    base=base,
                    tail=tail,
                )
            )
            script.extend(
                _large_square_bound_script(
                    coefficient=coefficient,
                    base=base,
                    tail=tail,
                    bound=bound,
                    tag=tag,
                )
            )

        trial_divisors = tuple(
            value for value in _TRIAL_PRIMES if value <= bound
        )
        script.extend(
            (
                f"specialize {PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE} "
                f"{bound}",
                f"specialize {PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE} "
                f"({target})",
                f"apply {PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE}",
                "exact hn0",
                "exact hn1",
                "exact hsquare",
                "intro p",
                "intro hp",
                "intro hp_bound",
                "intro hdivides",
                f"have hbound_22 : exists k. k + {bound} = 22",
                f"exists {22 - bound}",
                "norm_num",
                "have hp_22 : exists k. k + p = 22",
                "specialize le_trans p",
                f"specialize le_trans {bound}",
                "specialize le_trans 22",
                "apply le_trans",
                "exact hp_bound",
                "exact hbound_22",
                f"have hcases : {_prime_cases_result('p')}",
                f"specialize {PRIME_LE_TWENTY_TWO_CASES} p",
                f"apply {PRIME_LE_TWENTY_TWO_CASES}",
                "exact hp",
                "exact hp_22",
                *_certificate_case_script(
                    target=target,
                    number=number,
                    bound=bound,
                    divisors=trial_divisors,
                    large_data=large_data,
                    tag=tag,
                ),
            )
        )

        dependencies: list[str] = []
        if large_data is not None:
            dependencies.extend(
                (
                    "add_eq_zero_right",
                    "le_not_lt",
                    "add_assoc",
                    "add_comm",
                    *(("mul_succ_left",) if number == 83 else ()),
                    (
                        DOUBLE_SCALED_REMAINDER_LIFT
                        if number == 521
                        else SCALED_REMAINDER_LIFT
                    ),
                )
            )
            if number == 521:
                dependencies.extend(("add_mul", "mul_assoc", "one_mul"))
        dependencies.extend(
            (
                NONZERO_REMAINDER_NOT_MULTIPLE,
                PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE,
                "le_trans",
                PRIME_LE_TWENTY_TWO_CASES,
            )
        )
        if bound < 22:
            dependencies.append("lt_not_le")
        certificates.append(
            spec(
                name,
                result_prime,
                tuple(dependencies),
                tuple(script),
                f"A native checked trial-division certificate for {number}.",
            )
        )

    return support + tuple(certificates)


__all__ = [
    "FIXED_NONTRIVIAL_FACTOR_NOT_PRIME",
    "FACTOR_PAIR_HAS_SMALL_MEMBER_BELOW_SQUARE",
    "NONPRIME_HAS_SMALL_PRIME_DIVISOR_BELOW_SQUARE",
    "PRIME_OF_NO_SMALL_PRIME_DIVISOR_BELOW_SQUARE",
    "PRIME_LE_TWENTY_TWO_CASES",
    "NONZERO_REMAINDER_NOT_MULTIPLE",
    "SCALED_REMAINDER_LIFT",
    "ADD_REMAINDER_LIFT",
    "DOUBLE_SCALED_REMAINDER_LIFT",
    "PRIME_FIVE",
    "PRIME_SEVEN",
    "PRIME_THIRTEEN",
    "PRIME_TWENTY_THREE",
    "PRIME_FORTY_THREE",
    "PRIME_EIGHTY_THREE",
    "PRIME_ONE_HUNDRED_SIXTY_THREE",
    "PRIME_THREE_HUNDRED_SEVENTEEN",
    "PRIME_FIVE_HUNDRED_TWENTY_ONE",
    "make_bertrand_b8_prime_certificate_candidate_theorems",
]
