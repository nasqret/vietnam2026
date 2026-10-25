"""Constructive large-input Bertrand theorem.

The single candidate below specializes the checked bounded interval search to
``(n,n+n]``.  Its witness branch is returned directly.  The explicit
prime-free branch constructs the relational square root, quotient, central
coefficient, and powers needed by the reviewed B3, B5, and B6 bounds, whose
strict/weak inequality cycle yields ``false`` constructively.

All readable notation expands to the unchanged first-order Peano language.
This module grants no registry authority or edition membership.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_prime_support_candidate import (
    _no_bertrand_closed_term,
)
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .power_algebra_theorems import _power_terms


BERTRAND_EVENTUALLY_CLOSED_UPPER = "bertrand_eventually_closed_upper"


def make_bertrand_b7_eventual_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated B7 large-input theorem candidate."""

    variables = ("n",)
    threshold = _le_term(
        "16 * 32",
        "n",
        tag="b7_threshold",
        variables=variables,
    )
    prime_candidate = "b7_prime"
    result_prime = _prime_relation_term(
        prime_candidate,
        tag="b7_result_prime",
        variables=variables + (prime_candidate,),
    )
    result_lower = _lt_term(
        "n",
        prime_candidate,
        tag="b7_result_lower",
        variables=variables + (prime_candidate,),
    )
    result_upper = _le_term(
        prime_candidate,
        "n + n",
        tag="b7_result_upper",
        variables=variables + (prime_candidate,),
    )
    result = (
        f"exists {prime_candidate}. ({result_prime}) /\\ "
        f"(({result_lower}) /\\ ({result_upper}))"
    )
    exclusion = _no_bertrand_closed_term(
        "n",
        tag="b7_exclusion",
        variables=variables,
    )

    four_sixteen = _le_term(
        "4",
        "16",
        tag="b7_four_sixteen",
        variables=variables,
    )
    one_thirty_two = _le_term(
        "1",
        "32",
        tag="b7_one_thirty_two",
        variables=variables,
    )
    sixteen_threshold = _le_term(
        "16",
        "16 * 32",
        tag="b7_sixteen_threshold",
        variables=variables,
    )
    four_threshold = _le_term(
        "4",
        "16 * 32",
        tag="b7_four_threshold",
        variables=variables,
    )
    four_n = _le_term(
        "4",
        "n",
        tag="b7_four_n",
        variables=variables,
    )
    two_four = _lt_term(
        "2",
        "4",
        tag="b7_two_four",
        variables=variables,
    )
    two_n = _lt_term(
        "2",
        "n",
        tag="b7_two_n",
        variables=variables,
    )

    floor = floor_sqrt_relation("n + n", "s", tag="b7_floor")
    floor_exists = f"exists s. ({floor})"
    division_variables = ("n", "s", "q", "r")
    division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b7_division",
        variables=division_variables,
    )
    division_exists = f"exists q r. ({division})"
    central = _central_binom_relation_term(
        "n",
        "C",
        tag="b7_central",
        variables=("n", "s", "q", "r", "C"),
    )
    central_exists = f"exists C. ({central})"
    power_variables = ("n", "x", "x1", "x2", "x3", "x4", "x5", "x6")
    power_a = _power_terms("n + n", "x", "A", tag="b7_power_a")
    power_b = _power_terms("4", "x1", "B", tag="b7_power_b")
    power_f = _power_terms("4", "n", "F", tag="b7_power_f")
    power_a_exists = f"exists A. ({power_a})"
    power_b_exists = f"exists B. ({power_b})"
    power_f_exists = f"exists F. ({power_f})"

    lower = _lt_term(
        "x6",
        "n * x3",
        tag="b7_lower",
        variables=power_variables,
    )
    central_upper = _le_term(
        "x3",
        "x4 * x5",
        tag="b7_central_upper",
        variables=power_variables,
    )
    scaled_upper = _le_term(
        "n * x3",
        "n * (x4 * x5)",
        tag="b7_scaled_upper",
        variables=power_variables,
    )
    associated_upper = _le_term(
        "n * x3",
        "n * x4 * x5",
        tag="b7_associated_upper",
        variables=power_variables,
    )
    main = _le_term(
        "n * x4 * x5",
        "x6",
        tag="b7_main",
        variables=power_variables,
    )
    contradiction_upper = _le_term(
        "n * x3",
        "x6",
        tag="b7_contradiction_upper",
        variables=power_variables,
    )

    script = (
        "intro n",
        "intro hthreshold",
        f"have hsearch : ({result}) \\/ ({exclusion})",
        "specialize bounded_prime_interval_search n",
        "specialize bounded_prime_interval_search (n + n)",
        "exact bounded_prime_interval_search",
        "cases hsearch",
        "exact hsearch_left",
        "exfalso",
        f"have hone_thirty_two : {one_thirty_two}",
        "exists 31",
        "norm_num",
        f"have hsixteen_threshold : {sixteen_threshold}",
        "specialize le_mul_of_one_le_right 16",
        "specialize le_mul_of_one_le_right 32",
        "apply le_mul_of_one_le_right",
        "exact hone_thirty_two",
        f"have hfour_sixteen : {four_sixteen}",
        "exists 12",
        "norm_num",
        f"have hfour_threshold : {four_threshold}",
        "specialize le_trans 4",
        "specialize le_trans 16",
        "specialize le_trans (16 * 32)",
        "apply le_trans",
        "exact hfour_sixteen",
        "exact hsixteen_threshold",
        f"have hfour_n : {four_n}",
        "specialize le_trans 4",
        "specialize le_trans (16 * 32)",
        "specialize le_trans n",
        "apply le_trans",
        "exact hfour_threshold",
        "exact hthreshold",
        f"have htwo_four : {two_four}",
        "exists 1",
        "norm_num",
        f"have htwo_n : {two_n}",
        "specialize lt_of_lt_of_le 2",
        "specialize lt_of_lt_of_le 4",
        "specialize lt_of_lt_of_le n",
        "apply lt_of_lt_of_le",
        "exact htwo_four",
        "exact hfour_n",
        f"have hfloor_exists : {floor_exists}",
        "specialize floor_sqrt_total (n + n)",
        "exact floor_sqrt_total",
        "cases hfloor_exists",
        f"have hdivision_exists : {division_exists}",
        "specialize division_remainder_exists 3",
        "specialize division_remainder_exists (n + n)",
        "apply division_remainder_exists",
        "intro hthree_zero",
        "apply PA1",
        "exact hthree_zero",
        "cases hdivision_exists",
        "cases hdivision_exists_witness",
        f"have hcentral_exists : {central_exists}",
        "specialize central_binom_exists n",
        "exact central_binom_exists",
        "cases hcentral_exists",
        f"have hpower_a_exists : {power_a_exists}",
        "specialize pow_exists (n + n)",
        "specialize pow_exists x",
        "exact pow_exists",
        "cases hpower_a_exists",
        f"have hpower_b_exists : {power_b_exists}",
        "specialize pow_exists 4",
        "specialize pow_exists x1",
        "exact pow_exists",
        "cases hpower_b_exists",
        f"have hpower_f_exists : {power_f_exists}",
        "specialize pow_exists 4",
        "specialize pow_exists n",
        "exact pow_exists",
        "cases hpower_f_exists",
        f"have hlower : {lower}",
        "specialize four_pow_lt_mul_central_binom n",
        "specialize four_pow_lt_mul_central_binom x6",
        "specialize four_pow_lt_mul_central_binom x3",
        "apply four_pow_lt_mul_central_binom",
        "exact hfour_n",
        "exact hpower_f_exists_witness",
        "exact hcentral_exists_witness",
        f"have hcentral_upper : {central_upper}",
        "specialize central_binom_le_of_no_bertrand_prime n",
        "specialize central_binom_le_of_no_bertrand_prime x",
        "specialize central_binom_le_of_no_bertrand_prime x1",
        "specialize central_binom_le_of_no_bertrand_prime x2",
        "specialize central_binom_le_of_no_bertrand_prime x3",
        "specialize central_binom_le_of_no_bertrand_prime x4",
        "specialize central_binom_le_of_no_bertrand_prime x5",
        "apply central_binom_le_of_no_bertrand_prime",
        "exact hsearch_right",
        "exact htwo_n",
        "exact hfloor_exists_witness",
        "exact hdivision_exists_witness_witness",
        "exact hcentral_exists_witness",
        "exact hpower_a_exists_witness",
        "exact hpower_b_exists_witness",
        f"have hscaled_upper : {scaled_upper}",
        "specialize mul_le_mul_left x3",
        "specialize mul_le_mul_left (x4 * x5)",
        "specialize mul_le_mul_left n",
        "apply mul_le_mul_left",
        "exact hcentral_upper",
        f"have hassociated_upper : {associated_upper}",
        "specialize mul_assoc n",
        "specialize mul_assoc x4",
        "specialize mul_assoc x5",
        "rewrite <- mul_assoc at hscaled_upper",
        "exact hscaled_upper",
        f"have hmain : {main}",
        "specialize bertrand_main_inequality_nat n",
        "specialize bertrand_main_inequality_nat x",
        "specialize bertrand_main_inequality_nat x1",
        "specialize bertrand_main_inequality_nat x2",
        "specialize bertrand_main_inequality_nat x4",
        "specialize bertrand_main_inequality_nat x5",
        "specialize bertrand_main_inequality_nat x6",
        "apply bertrand_main_inequality_nat",
        "exact hthreshold",
        "exact hfloor_exists_witness",
        "exact hdivision_exists_witness_witness",
        "exact hpower_a_exists_witness",
        "exact hpower_b_exists_witness",
        "exact hpower_f_exists_witness",
        f"have hcontradiction_upper : {contradiction_upper}",
        "specialize le_trans (n * x3)",
        "specialize le_trans (n * x4 * x5)",
        "specialize le_trans x6",
        "apply le_trans",
        "exact hassociated_upper",
        "exact hmain",
        "specialize lt_not_le x6",
        "specialize lt_not_le (n * x3)",
        "apply lt_not_le",
        "exact hlower",
        "exact hcontradiction_upper",
    )

    return (
        spec(
            BERTRAND_EVENTUALLY_CLOSED_UPPER,
            f"forall n. ({threshold}) -> ({result})",
            (
                "bounded_prime_interval_search",
                "le_mul_of_one_le_right",
                "le_trans",
                "lt_of_lt_of_le",
                "floor_sqrt_total",
                "division_remainder_exists",
                "central_binom_exists",
                "pow_exists",
                "four_pow_lt_mul_central_binom",
                "central_binom_le_of_no_bertrand_prime",
                "mul_le_mul_left",
                "mul_assoc",
                "bertrand_main_inequality_nat",
                "lt_not_le",
            ),
            script,
            (
                "Every n at least 16*32 has a prime in the constructive "
                "open-closed Bertrand interval."
            ),
        ),
    )


__all__ = ["make_bertrand_b7_eventual_candidate_theorems"]
