"""Exact fourth-row seed for the central-binomial lower bound.

The first candidate evaluates a supplied relational fourth power of four.
The second derives the weighted value ``4 * C(8,4)`` solely from the checked
central-binomial recurrence.  Their thin combination is the strict seed used
by the later general induction.  ``Pow``, ``CentralBinom``, and strict order
are authoring-only abbreviations which are fully expanded before parsing.

This module creates no trusted primitive, authority enrollment, or checked-
use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import _lt_term
from peano_lab.library.power_algebra_theorems import _power_terms


POW_FOUR_FOUR_EXACT = "pow_four_four_exact"
CENTRAL_BINOM_FOUR_WEIGHTED_OF_RECURRENCE = (
    "central_binom_four_weighted_of_recurrence"
)
FOUR_POW_CENTRAL_SEED_PACKAGE = "four_pow_central_seed_package"


def make_bertrand_central_binom_lower_seed_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact power, weighted central, and strict seed rows."""

    power_four = _power_terms("4", "4", "p", tag="bpf4e_source")
    power_three = _power_terms("4", "3", "r", tag="bpf4e_three")
    power_two = _power_terms("4", "2", "r", tag="bpf4e_two")

    power_script = (
        "intro p",
        "intro hpower",
        f"have hthree : exists r. ({power_three}) /\\ p = r * 4",
        "apply pow_successor_decompose",
        "refl",
        "exact hpower",
        "cases hthree",
        "cases hthree_witness",
        f"have htwo : exists r. ({power_two}) /\\ x = r * 4",
        "apply pow_successor_decompose",
        "refl",
        "exact hthree_witness_left",
        "cases htwo",
        "cases htwo_witness",
        "have htwo_value : x1 = 4 * 4",
        "apply pow_two",
        "refl",
        "exact htwo_witness_left",
        "rewrite hthree_witness_right",
        "rewrite htwo_witness_right",
        "rewrite htwo_value",
        "refl",
    )

    central_variables = ("c",)
    central_four = _central_binom_relation_term(
        "4",
        "c",
        tag="bcb4we_source",
        variables=central_variables,
    )
    central_zero = _central_binom_relation_term(
        "0",
        "a",
        tag="bcb4we_zero",
        variables=central_variables + ("a",),
    )
    central_one = _central_binom_relation_term(
        "1",
        "a",
        tag="bcb4we_one",
        variables=central_variables + ("a",),
    )
    central_two = _central_binom_relation_term(
        "2",
        "a",
        tag="bcb4we_two",
        variables=central_variables + ("a",),
    )
    central_three = _central_binom_relation_term(
        "3",
        "a",
        tag="bcb4we_three",
        variables=central_variables + ("a",),
    )
    recurrence_variables = ("n", "a", "b")
    recurrence_predecessor = _central_binom_relation_term(
        "n",
        "a",
        tag="bcb4we_recurrence_predecessor",
        variables=recurrence_variables,
    )
    recurrence_successor = _central_binom_relation_term(
        "S n",
        "b",
        tag="bcb4we_recurrence_successor",
        variables=recurrence_variables,
    )
    central_recurrence = (
        "forall n a b. "
        f"({recurrence_predecessor}) -> ({recurrence_successor}) -> "
        "S n * b = (2 * S (n + n)) * a"
    )
    exists_variables = ("n", "z")
    exists_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcb4we_exists",
        variables=exists_variables,
    )
    central_exists = f"forall n. exists z. ({exists_relation})"

    central_script = (
        "intro hrecurrence",
        "intro hcentral_exists",
        "intro c",
        "intro hcentral",
        f"have hzero_exists : exists a. ({central_zero})",
        "apply hcentral_exists",
        "cases hzero_exists",
        f"have hone_exists : exists a. ({central_one})",
        "apply hcentral_exists",
        "cases hone_exists",
        f"have htwo_exists : exists a. ({central_two})",
        "apply hcentral_exists",
        "cases htwo_exists",
        f"have hthree_exists : exists a. ({central_three})",
        "apply hcentral_exists",
        "cases hthree_exists",
        "have hzero_value : x = 1",
        "apply central_binom_zero",
        "exact hzero_exists_witness",
        "have hrecurrence_zero : "
        "S 0 * x1 = (2 * S (0 + 0)) * x",
        "apply hrecurrence",
        "exact hzero_exists_witness",
        "exact hone_exists_witness",
        "rewrite hzero_value at hrecurrence_zero",
        "specialize one_mul x1",
        "rewrite one_mul at hrecurrence_zero",
        "have hzero_rhs : (2 * S (0 + 0)) * 1 = 2",
        "norm_num",
        "rewrite hzero_rhs at hrecurrence_zero",
        "have hone_value : x1 = 2",
        "exact hrecurrence_zero",
        "have hrecurrence_one : "
        "S 1 * x2 = (2 * S (1 + 1)) * x1",
        "apply hrecurrence",
        "exact hone_exists_witness",
        "exact htwo_exists_witness",
        "rewrite hone_value at hrecurrence_one",
        "have hone_rhs : (2 * S (1 + 1)) * 2 = 2 * 6",
        "norm_num",
        "rewrite hone_rhs at hrecurrence_one",
        "have htwo_value : x2 = 6",
        "specialize mul_left_cancel_nonzero 2",
        "apply mul_left_cancel_nonzero",
        "intro htwo_zero",
        "apply PA1",
        "exact htwo_zero",
        "exact hrecurrence_one",
        "have hrecurrence_two : "
        "S 2 * x3 = (2 * S (2 + 2)) * x2",
        "apply hrecurrence",
        "exact htwo_exists_witness",
        "exact hthree_exists_witness",
        "rewrite htwo_value at hrecurrence_two",
        "have htwo_rhs : (2 * S (2 + 2)) * 6 = 3 * 20",
        "norm_num",
        "rewrite htwo_rhs at hrecurrence_two",
        "have hthree_value : x3 = 20",
        "specialize mul_left_cancel_nonzero 3",
        "apply mul_left_cancel_nonzero",
        "intro hthree_zero",
        "apply PA1",
        "exact hthree_zero",
        "exact hrecurrence_two",
        "have hrecurrence_three : "
        "S 3 * c = (2 * S (3 + 3)) * x3",
        "apply hrecurrence",
        "exact hthree_exists_witness",
        "exact hcentral",
        "rewrite hthree_value at hrecurrence_three",
        "exact hrecurrence_three",
    )

    seed_variables = ("p", "c")
    seed_power = _power_terms("4", "4", "p", tag="bfplcb4_power")
    seed_central = _central_binom_relation_term(
        "4",
        "c",
        tag="bfplcb4_central",
        variables=seed_variables,
    )
    seed_result = _lt_term(
        "p",
        "4 * c",
        tag="bfplcb4_result",
        variables=seed_variables,
    )
    seed_small = _lt_term(
        "(4 * 4) * 4",
        "(2 * S (3 + 3)) * 5",
        tag="bfplcb4_small",
        variables=seed_variables,
    )
    seed_scaled = _lt_term(
        "((4 * 4) * 4) * 4",
        "((2 * S (3 + 3)) * 5) * 4",
        tag="bfplcb4_scaled",
        variables=seed_variables,
    )
    seed_script = (
        "intro hrecurrence",
        "split",
        "exact central_binom_exists",
        "intro p",
        "intro c",
        "intro hpower",
        "intro hcentral",
        "have hpower_value : p = ((4 * 4) * 4) * 4",
        "apply pow_four_four_exact",
        "exact hpower",
        f"have hweighted : forall c. ({central_four}) -> "
        "4 * c = (2 * S (3 + 3)) * 20",
        "apply central_binom_four_weighted_of_recurrence",
        "exact hrecurrence",
        "exact central_binom_exists",
        "have hcentral_value : 4 * c = (2 * S (3 + 3)) * 20",
        "apply hweighted",
        "exact hcentral",
        f"have hsmall : {seed_small}",
        "exists 5",
        "norm_num",
        f"have hscaled : {seed_scaled}",
        "apply mul_lt_mul_right_nonzero",
        "exact hsmall",
        "intro hfour_zero",
        "apply PA1",
        "exact hfour_zero",
        "have hfive_four : 5 * 4 = 20",
        "norm_num",
        "have hassoc : "
        "((2 * S (3 + 3)) * 5) * 4 = "
        "(2 * S (3 + 3)) * (5 * 4)",
        "apply mul_assoc",
        "rewrite hassoc at hscaled",
        "rewrite hfive_four at hscaled",
        "rewrite hpower_value",
        "rewrite hcentral_value",
        "exact hscaled",
    )

    return (
        spec(
            POW_FOUR_FOUR_EXACT,
            f"forall p. ({power_four}) -> p = ((4 * 4) * 4) * 4",
            ("pow_successor_decompose", "pow_two"),
            power_script,
            "A relational fourth power of four is the fourfold product.",
        ),
        spec(
            CENTRAL_BINOM_FOUR_WEIGHTED_OF_RECURRENCE,
            f"({central_recurrence}) -> ({central_exists}) -> forall c. "
            f"({central_four}) -> 4 * c = (2 * S (3 + 3)) * 20",
            (
                "one_mul",
                "mul_left_cancel_nonzero",
                "central_binom_zero",
            ),
            central_script,
            "The fourth central binomial satisfies the compact weighted value.",
        ),
        spec(
            FOUR_POW_CENTRAL_SEED_PACKAGE,
            f"({central_recurrence}) -> (({central_exists}) /\\ "
            f"(forall p c. ({seed_power}) -> ({seed_central}) -> "
            f"({seed_result})))",
            (
                "mul_assoc",
                "mul_lt_mul_right_nonzero",
                "central_binom_exists",
                POW_FOUR_FOUR_EXACT,
                CENTRAL_BINOM_FOUR_WEIGHTED_OF_RECURRENCE,
            ),
            seed_script,
            "The strict central-binomial lower bound holds at index four.",
        ),
    )


__all__ = ["make_bertrand_central_binom_lower_seed_candidate_theorems"]
