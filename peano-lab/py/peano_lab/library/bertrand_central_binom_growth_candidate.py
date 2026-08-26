"""Strict arithmetic growth support for the central-binomial lower bound.

The first candidate upgrades a witnessed strict inequality through right
multiplication by a nonzero natural.  The second is the pure arithmetic step
which turns the weighted central-binomial recurrence equation into the exact
successor inequality needed by ``four_pow_lt_mul_central_binom``.

``Lt`` remains authoring-only notation and is expanded hygienically into
ordinary first-order Peano arithmetic before a theorem specification is
returned.  This module adds no trusted primitive, authority enrollment, or
checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)


MUL_LT_MUL_RIGHT_NONZERO = "mul_lt_mul_right_nonzero"
FOUR_POWER_CENTRAL_RECURRENCE_STEP = (
    "four_power_central_recurrence_step"
)


def make_bertrand_central_binom_growth_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build strict right scaling followed by the central successor step."""

    scaling_variables = ("a", "b", "c")
    scaling_source = _lt_term(
        "a",
        "b",
        tag="mlmrn_source",
        variables=scaling_variables,
    )
    scaling_raw_step = _lt_term(
        "c * a",
        "c * S a",
        tag="mlmrn_raw_step",
        variables=scaling_variables,
    )
    scaling_step = _lt_term(
        "a * c",
        "S a * c",
        tag="mlmrn_step",
        variables=scaling_variables,
    )
    scaling_tail = _le_term(
        "S a * c",
        "b * c",
        tag="mlmrn_tail",
        variables=scaling_variables,
    )
    scaling_result = _lt_term(
        "a * c",
        "b * c",
        tag="mlmrn_result",
        variables=scaling_variables,
    )

    scaling_script = (
        "intro a",
        "intro b",
        "intro c",
        "intro hab",
        "intro hc",
        f"have hraw : {scaling_raw_step}",
        "specialize mul_lt_mul_succ_left_nonzero c",
        "specialize mul_lt_mul_succ_left_nonzero a",
        "apply mul_lt_mul_succ_left_nonzero",
        "exact hc",
        "have hleft_comm : c * a = a * c",
        "specialize mul_comm c",
        "specialize mul_comm a",
        "exact mul_comm",
        "have hright_comm : c * S a = S a * c",
        "specialize mul_comm c",
        "specialize mul_comm (S a)",
        "exact mul_comm",
        "rewrite hleft_comm at hraw",
        "rewrite hright_comm at hraw",
        f"have hstep : {scaling_step}",
        "exact hraw",
        f"have htail : {scaling_tail}",
        "specialize mul_le_mul_right (S a)",
        "specialize mul_le_mul_right b",
        "specialize mul_le_mul_right c",
        "apply mul_le_mul_right",
        "exact hab",
        "specialize lt_of_lt_of_le (a * c)",
        "specialize lt_of_lt_of_le (S a * c)",
        "specialize lt_of_lt_of_le (b * c)",
        "apply lt_of_lt_of_le",
        "exact hstep",
        "exact htail",
    )

    step_variables = ("n", "q", "c", "d")
    step_source = _lt_term(
        "q",
        "n * c",
        tag="bfpcrs_source",
        variables=step_variables,
    )
    step_scaled = _lt_term(
        "q * 4",
        "(n * c) * 4",
        tag="bfpcrs_scaled",
        variables=step_variables,
    )
    step_coefficient = _lt_term(
        "4 * n",
        "2 * S (n + n)",
        tag="bfpcrs_coefficient",
        variables=step_variables,
    )
    step_coefficient_product = _lt_term(
        "(4 * n) * c",
        "(2 * S (n + n)) * c",
        tag="bfpcrs_coefficient_product",
        variables=step_variables,
    )
    step_gap = _lt_term(
        "(n * c) * 4",
        "S n * d",
        tag="bfpcrs_gap",
        variables=step_variables,
    )
    step_result = _lt_term(
        "q * 4",
        "S n * d",
        tag="bfpcrs_result",
        variables=step_variables,
    )

    step_script = (
        "intro n",
        "intro q",
        "intro c",
        "intro d",
        "intro hstrict",
        "intro hrecurrence",
        "have hc : ~(c = 0)",
        "intro hc_zero",
        "cases hstrict",
        "apply PA1",
        "specialize add_eq_zero_right x",
        "specialize add_eq_zero_right (S q)",
        "apply add_eq_zero_right",
        "trans n * c",
        "exact hstrict_witness",
        "rewrite hc_zero",
        "apply PA5",
        f"have hscaled : {step_scaled}",
        "specialize mul_lt_mul_right_nonzero q",
        "specialize mul_lt_mul_right_nonzero (n * c)",
        "specialize mul_lt_mul_right_nonzero 4",
        "apply mul_lt_mul_right_nonzero",
        "exact hstrict",
        "intro hfour_zero",
        "apply PA1",
        "exact hfour_zero",
        "have hfour : 4 * n = 2 * n + 2 * n",
        "trans (2 + 2) * n",
        "congr",
        "norm_num",
        "refl",
        "apply add_mul",
        f"have hcoefficient : {step_coefficient}",
        "exists 1",
        "trans S (1 + 4 * n)",
        "apply PA4",
        "trans S (4 * n + 1)",
        "congr",
        "apply add_comm",
        "trans 4 * n + 2",
        "symm",
        "apply PA4",
        "trans (2 * n + 2 * n) + 2",
        "congr",
        "exact hfour",
        "refl",
        "trans 2 * (n + n) + 2",
        "congr",
        "symm",
        "apply mul_add",
        "refl",
        "symm",
        "apply PA6",
        f"have hcoefficient_product : {step_coefficient_product}",
        "specialize mul_lt_mul_right_nonzero (4 * n)",
        "specialize mul_lt_mul_right_nonzero (2 * S (n + n))",
        "specialize mul_lt_mul_right_nonzero c",
        "apply mul_lt_mul_right_nonzero",
        "exact hcoefficient",
        "exact hc",
        "have hshuffle : (n * c) * 4 = (4 * n) * c",
        "trans 4 * (n * c)",
        "apply mul_comm",
        "symm",
        "apply mul_assoc",
        f"have hgap : {step_gap}",
        "rewrite hshuffle",
        "rewrite hrecurrence",
        "exact hcoefficient_product",
        "specialize lt_trans (q * 4)",
        "specialize lt_trans ((n * c) * 4)",
        "specialize lt_trans (S n * d)",
        "apply lt_trans",
        "exact hscaled",
        "exact hgap",
    )

    return (
        spec(
            MUL_LT_MUL_RIGHT_NONZERO,
            "forall a b c. "
            f"({scaling_source}) -> ~(c = 0) -> ({scaling_result})",
            (
                "mul_comm",
                "mul_lt_mul_succ_left_nonzero",
                "mul_le_mul_right",
                "lt_of_lt_of_le",
            ),
            scaling_script,
            "Right multiplication by a nonzero natural preserves strict order.",
        ),
        spec(
            FOUR_POWER_CENTRAL_RECURRENCE_STEP,
            "forall n q c d. "
            f"({step_source}) -> S n * d = (2 * S (n + n)) * c -> "
            f"({step_result})",
            (
                "add_eq_zero_right",
                "add_comm",
                "mul_comm",
                "mul_assoc",
                "mul_add",
                "add_mul",
                MUL_LT_MUL_RIGHT_NONZERO,
                "lt_trans",
            ),
            step_script,
            (
                "A weighted central recurrence equation advances the strict "
                "four-power lower bound."
            ),
        ),
    )


__all__ = ["make_bertrand_central_binom_growth_candidate_theorems"]
