"""Relational four-power lower bound for central binomial coefficients.

The candidate below packages the exact fourth-row seed with a structural
induction driven by the checked central-binomial recurrence.  ``Pow``,
``CentralBinom``, weak order, and strict order remain authoring-only
abbreviations which are fully expanded into first-order Peano arithmetic
before parsing.

This module creates no trusted primitive, authority enrollment, or checked-
use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _le_term,
    _lt_term,
)
from peano_lab.library.power_algebra_theorems import _power_terms


FOUR_POW_LT_MUL_CENTRAL_BINOM = "four_pow_lt_mul_central_binom"


def make_bertrand_central_binom_lower_bound_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated central-binomial lower-bound candidate."""

    variables = ("n", "p", "c")
    bound = _le_term(
        "4",
        "n",
        tag="bfplcb_bound",
        variables=variables,
    )
    power = _power_terms("4", "n", "p", tag="bfplcb_power")
    central = _central_binom_relation_term(
        "n",
        "c",
        tag="bfplcb_central",
        variables=variables,
    )
    result = _lt_term(
        "p",
        "n * c",
        tag="bfplcb_result",
        variables=variables,
    )

    package_exists_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcb4we_exists",
        variables=("n", "z"),
    )
    package_exists = f"forall n. exists z. ({package_exists_relation})"
    package_seed_variables = ("p", "c")
    package_seed_power = _power_terms(
        "4",
        "4",
        "p",
        tag="bfplcb4_power",
    )
    package_seed_central = _central_binom_relation_term(
        "4",
        "c",
        tag="bfplcb4_central",
        variables=package_seed_variables,
    )
    package_seed_result = _lt_term(
        "p",
        "4 * c",
        tag="bfplcb4_result",
        variables=package_seed_variables,
    )
    package_seed = (
        f"forall p c. ({package_seed_power}) -> "
        f"({package_seed_central}) -> ({package_seed_result})"
    )

    zero_lt_four = _lt_term(
        "0",
        "4",
        tag="bfplcb_zero_lt_four",
        variables=(),
    )
    one_lt_four = _lt_term(
        "1",
        "4",
        tag="bfplcb_one_lt_four",
        variables=(),
    )
    two_lt_four = _lt_term(
        "2",
        "4",
        tag="bfplcb_two_lt_four",
        variables=(),
    )
    three_lt_four = _lt_term(
        "3",
        "4",
        tag="bfplcb_three_lt_four",
        variables=(),
    )

    predecessor_index = "S (S (S (S n)))"
    successor_index = "S (S (S (S (S n))))"
    step_variables = ("n", "p", "c")
    predecessor_power = _power_terms(
        "4",
        predecessor_index,
        "r",
        tag="bfplcb_predecessor_power",
    )
    predecessor_central = _central_binom_relation_term(
        predecessor_index,
        "a",
        tag="bfplcb_predecessor_central",
        variables=step_variables + ("a",),
    )
    predecessor_bound = _le_term(
        "4",
        predecessor_index,
        tag="bfplcb_predecessor_bound",
        variables=step_variables,
    )
    predecessor_result = _lt_term(
        "x",
        f"{predecessor_index} * x1",
        tag="bfplcb_predecessor_result",
        variables=step_variables + ("x", "x1"),
    )
    successor_result = _lt_term(
        "x * 4",
        f"{successor_index} * c",
        tag="bfplcb_successor_result",
        variables=step_variables + ("x", "x1"),
    )

    script = (
        f"have hzero_lt_four : {zero_lt_four}",
        "exists 3",
        "norm_num",
        f"have hone_lt_four : {one_lt_four}",
        "exists 2",
        "norm_num",
        f"have htwo_lt_four : {two_lt_four}",
        "exists 1",
        "norm_num",
        f"have hthree_lt_four : {three_lt_four}",
        "exists 0",
        "norm_num",
        f"have hpackage : ({package_exists}) /\\ ({package_seed})",
        "apply four_pow_central_seed_package",
        "exact central_binom_succ_recurrence",
        "cases hpackage",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 0",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hzero_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 1",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hone_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 2",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact htwo_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "exfalso",
        "specialize lt_not_le 3",
        "specialize lt_not_le 4",
        "apply lt_not_le",
        "exact hthree_lt_four",
        "exact hbound",
        "induction n",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        "apply hpackage_right",
        "exact hpower",
        "exact hcentral",
        "intro p",
        "intro c",
        "intro hbound",
        "intro hpower",
        "intro hcentral",
        f"have hpower_step : exists r. ({predecessor_power}) /\\ p = r * 4",
        "apply pow_successor_decompose",
        "refl",
        "exact hpower",
        "cases hpower_step",
        "cases hpower_step_witness",
        f"have hpredecessor_exists : exists a. ({predecessor_central})",
        "apply hpackage_left",
        "cases hpredecessor_exists",
        f"have hpredecessor_bound : {predecessor_bound}",
        "exists n",
        "simp",
        f"have hstrict : {predecessor_result}",
        "apply IH4",
        "exact hpredecessor_bound",
        "exact hpower_step_witness_left",
        "exact hpredecessor_exists_witness",
        "have hrecurrence : "
        f"{successor_index} * c = "
        f"(2 * S ({predecessor_index} + {predecessor_index})) * x1",
        "apply central_binom_succ_recurrence",
        "exact hpredecessor_exists_witness",
        "exact hcentral",
        f"have hstep : {successor_result}",
        "apply four_power_central_recurrence_step",
        "exact hstrict",
        "exact hrecurrence",
        "rewrite hpower_step_witness_right",
        "exact hstep",
    )

    return (
        spec(
            FOUR_POW_LT_MUL_CENTRAL_BINOM,
            "forall n p c. "
            f"({bound}) -> ({power}) -> ({central}) -> ({result})",
            (
                "lt_not_le",
                "pow_successor_decompose",
                "central_binom_succ_recurrence",
                "four_power_central_recurrence_step",
                "four_pow_central_seed_package",
            ),
            script,
            (
                "For every index at least four, the fourth power is below "
                "the index-weighted central binomial."
            ),
        ),
    )


__all__ = ["make_bertrand_central_binom_lower_bound_candidate_theorems"]
