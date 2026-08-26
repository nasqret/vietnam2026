"""Pointwise prime-contribution ranges for the Bertrand B5 upper bound.

The eight rows below translate the quotient and floor-square-root boundaries
into the scaled inequalities consumed by the already checked valuation laws.
They then collapse the five mathematical prime ranges to the three factor
forms needed by the finite-product comparison: a bounded small contribution,
one middle prime, or the neutral factor one.

All readable notation is expanded into first-order Peano arithmetic before
parsing.  Importing this module grants no theorem authority and changes no
library edition.
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
from .bertrand_power_valuation_candidate import _power_terms, power_valuation
from .fermat_residue_map_candidate import prime


DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT = (
    "division_three_scaled_upper_of_quotient_lt"
)
CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT = (
    "central_binom_prime_valuation_zero_above_third_quotient"
)
FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT = (
    "floor_sqrt_above_root_power_two_strict"
)
CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE = (
    "central_binom_prime_above_floor_sqrt_valuation_le_one"
)
NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES = (
    "no_bertrand_central_nonzero_valuation_live_ranges"
)
NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES = (
    "no_bertrand_central_nonzero_valuation_factor_ranges"
)
NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES = (
    "no_bertrand_central_nonzero_contribution_factor_ranges"
)
NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES = (
    "no_bertrand_central_prime_contribution_ranges"
)


def make_bertrand_central_binom_factor_ranges_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered B5 pointwise factor-range rows."""

    quotient_variables = ("n", "q", "r", "p")
    quotient_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bdtsuql_division",
        variables=quotient_variables,
    )
    quotient_order = _lt_term(
        "q",
        "p",
        tag="bdtsuql_quotient",
        variables=quotient_variables,
    )
    quotient_result = _lt_term(
        "n + n",
        "(p + p) + p",
        tag="bdtsuql_result",
        variables=quotient_variables,
    )
    quotient_block = _lt_term(
        "3 * q + r",
        "3 * S q",
        tag="bdtsuql_block",
        variables=quotient_variables,
    )
    quotient_block_aligned = _lt_term(
        "n + n",
        "3 * S q",
        tag="bdtsuql_block_aligned",
        variables=quotient_variables,
    )
    quotient_scaled = _le_term(
        "3 * S q",
        "3 * p",
        tag="bdtsuql_scaled",
        variables=quotient_variables,
    )
    quotient_raw_result = _lt_term(
        "n + n",
        "3 * p",
        tag="bdtsuql_raw_result",
        variables=quotient_variables,
    )

    zero_variables = ("p", "n", "C", "v", "q", "r")
    zero_prime = prime("p", tag="bcpvzatq_prime")
    zero_positive = _lt_term(
        "2", "n", tag="bcpvzatq_positive", variables=zero_variables
    )
    zero_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bcpvzatq_division",
        variables=zero_variables,
    )
    zero_above = _lt_term(
        "q", "p", tag="bcpvzatq_above", variables=zero_variables
    )
    zero_bound = _le_term(
        "p", "n", tag="bcpvzatq_bound", variables=zero_variables
    )
    zero_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bcpvzatq_central",
        variables=zero_variables,
    )
    zero_valuation = power_valuation(
        "p", "C", "v", tag="bcpvzatq_valuation"
    )
    zero_scaled = _lt_term(
        "n + n",
        "(p + p) + p",
        tag="bcpvzatq_scaled",
        variables=zero_variables,
    )

    sqrt_variables = ("x", "s", "p", "t")
    sqrt_source = floor_sqrt_relation("x", "s", tag="bfsarpts_source")
    sqrt_above = _lt_term(
        "s", "p", tag="bfsarpts_above", variables=sqrt_variables
    )
    sqrt_power = _power_terms(
        "p", "2", "t", tag="bfsarpts_power"
    )
    sqrt_result = _lt_term(
        "x", "t", tag="bfsarpts_result", variables=sqrt_variables
    )
    sqrt_first = _le_term(
        "S s * S s",
        "p * S s",
        tag="bfsarpts_first",
        variables=sqrt_variables,
    )
    sqrt_second = _le_term(
        "p * S s",
        "p * p",
        tag="bfsarpts_second",
        variables=sqrt_variables,
    )
    sqrt_square = _le_term(
        "S s * S s",
        "p * p",
        tag="bfsarpts_square",
        variables=sqrt_variables,
    )
    sqrt_raw_result = _lt_term(
        "x", "p * p", tag="bfsarpts_raw_result", variables=sqrt_variables
    )

    upper_variables = ("p", "n", "C", "v", "s")
    upper_prime = prime("p", tag="bcpafs_vlo_prime")
    upper_positive = _lt_term(
        "2", "n", tag="bcpafs_vlo_positive", variables=upper_variables
    )
    upper_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bcpafs_vlo_central",
        variables=upper_variables,
    )
    upper_valuation = power_valuation(
        "p", "C", "v", tag="bcpafs_vlo_valuation"
    )
    upper_floor = floor_sqrt_relation(
        "n + n", "s", tag="bcpafs_vlo_floor"
    )
    upper_above = _lt_term(
        "s", "p", tag="bcpafs_vlo_above", variables=upper_variables
    )
    upper_result = _le_term(
        "v", "1", tag="bcpafs_vlo_result", variables=upper_variables
    )
    upper_power = _power_terms(
        "p", "2", "t", tag="bcpafs_vlo_power"
    )
    upper_square = _lt_term(
        "n + n",
        "x",
        tag="bcpafs_vlo_square",
        variables=upper_variables + ("x",),
    )
    upper_two_le = _le_term(
        "2", "n", tag="bcpafs_vlo_two_le", variables=upper_variables
    )
    upper_one_two = _le_term(
        "1", "2", tag="bcpafs_vlo_one_two", variables=upper_variables
    )
    upper_one_le = _le_term(
        "1", "n", tag="bcpafs_vlo_one_le", variables=upper_variables
    )

    range_variables = ("n", "s", "q", "r", "C", "p", "v")
    range_exclusion = _no_bertrand_closed_term(
        "n", tag="bnbcnvlr_exclusion", variables=range_variables
    )
    range_prime = prime("p", tag="bnbcnvlr_prime")
    range_positive = _lt_term(
        "2", "n", tag="bnbcnvlr_positive", variables=range_variables
    )
    range_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="bnbcnvlr_division",
        variables=range_variables,
    )
    range_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bnbcnvlr_central",
        variables=range_variables,
    )
    range_valuation = power_valuation(
        "p", "C", "v", tag="bnbcnvlr_valuation"
    )
    range_small = _le_term(
        "p", "s", tag="bnbcnvlr_small", variables=range_variables
    )
    range_above_small = _lt_term(
        "s", "p", tag="bnbcnvlr_above_small", variables=range_variables
    )
    range_middle = _le_term(
        "p", "q", tag="bnbcnvlr_middle", variables=range_variables
    )
    range_above_middle = _lt_term(
        "q", "p", tag="bnbcnvlr_above_middle", variables=range_variables
    )
    range_row = _le_term(
        "p", "n", tag="bnbcnvlr_row", variables=range_variables
    )
    range_divides = (
        "exists k. C = p * k"
    )
    range_raw = (
        rf"({range_small}) \/ ((({range_above_small}) /\ "
        rf"({range_middle})) \/ (({range_above_middle}) /\ "
        rf"({range_row})))"
    )
    range_result = (
        rf"({range_small}) \/ (({range_above_small}) /\ "
        rf"({range_middle}))"
    )

    factor_floor = floor_sqrt_relation(
        "n + n", "s", tag="bnbcnvfr_floor"
    )
    factor_result = (
        rf"({range_small}) \/ ((({range_above_small}) /\ "
        rf"({range_middle})) /\ v = 1)"
    )
    factor_upper = _le_term(
        "v", "1", tag="bnbcnvfr_upper", variables=range_variables
    )
    factor_lower = _le_term(
        "1", "v", tag="bnbcnvfr_lower", variables=range_variables
    )

    contribution_variables = range_variables + ("a",)
    contribution_power = _power_terms(
        "p", "v", "a", tag="bnbcncfr_power"
    )
    contribution_bound = _le_term(
        "a",
        "n + n",
        tag="bnbcncfr_bound",
        variables=contribution_variables,
    )
    contribution_result = (
        rf"(({range_small}) /\ ({contribution_bound})) \/ "
        rf"((({range_above_small}) /\ ({range_middle})) /\ a = p)"
    )
    contribution_two_le = _le_term(
        "2",
        "n",
        tag="bnbcncfr_two_le",
        variables=contribution_variables,
    )
    contribution_one_two = _le_term(
        "1",
        "2",
        tag="bnbcncfr_one_two",
        variables=contribution_variables,
    )
    contribution_one_le = _le_term(
        "1",
        "n",
        tag="bnbcncfr_one_le",
        variables=contribution_variables,
    )

    total_result = rf"(({contribution_result}) \/ a = 1)"

    return (
        spec(
            DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT,
            "forall n q r p. "
            f"({quotient_division}) -> ({quotient_order}) -> "
            f"({quotient_result})",
            (
                "division_block_upper",
                "mul_le_mul_left",
                "lt_of_lt_of_le",
                "mul_succ_left",
                "one_mul",
            ),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro p",
                "intro hdivision",
                "intro hquotient",
                "cases hdivision",
                f"have hblock : {quotient_block}",
                "specialize division_block_upper 3",
                "specialize division_block_upper q",
                "specialize division_block_upper r",
                "apply division_block_upper",
                "exact hdivision_right",
                f"have hblock_aligned : {quotient_block_aligned}",
                "rewrite hdivision_left",
                "exact hblock",
                f"have hscaled : {quotient_scaled}",
                "specialize mul_le_mul_left (S q)",
                "specialize mul_le_mul_left p",
                "specialize mul_le_mul_left 3",
                "apply mul_le_mul_left",
                "exact hquotient",
                f"have hraw : {quotient_raw_result}",
                "specialize lt_of_lt_of_le (n + n)",
                "specialize lt_of_lt_of_le (3 * S q)",
                "specialize lt_of_lt_of_le (3 * p)",
                "apply lt_of_lt_of_le",
                "exact hblock_aligned",
                "exact hscaled",
                "have hdouble : 2 * p = p + p",
                "trans 1 * p + p",
                "specialize mul_succ_left 1",
                "specialize mul_succ_left p",
                "exact mul_succ_left",
                "specialize one_mul p",
                "rewrite one_mul",
                "refl",
                "have htriple : 3 * p = (p + p) + p",
                "trans 2 * p + p",
                "specialize mul_succ_left 2",
                "specialize mul_succ_left p",
                "exact mul_succ_left",
                "rewrite hdouble",
                "refl",
                "rewrite htriple at hraw",
                "exact hraw",
            ),
            "A quotient below p places the dividend strictly below 3*p.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT,
            "forall p n C v q r. "
            f"({zero_prime}) -> ({zero_positive}) -> "
            f"({zero_division}) -> ({zero_above}) -> ({zero_bound}) -> "
            f"({zero_central}) -> ({zero_valuation}) -> v = 0",
            (
                DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT,
                "central_binom_prime_valuation_zero_two_thirds_range",
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "intro v",
                "intro q",
                "intro r",
                "intro hp",
                "intro hpositive",
                "intro hdivision",
                "intro habove",
                "intro hbound",
                "intro hcentral",
                "intro hvaluation",
                f"have hscaled : {zero_scaled}",
                "specialize "
                "division_three_scaled_upper_of_quotient_lt n",
                "specialize "
                "division_three_scaled_upper_of_quotient_lt q",
                "specialize "
                "division_three_scaled_upper_of_quotient_lt r",
                "specialize "
                "division_three_scaled_upper_of_quotient_lt p",
                "apply division_three_scaled_upper_of_quotient_lt",
                "exact hdivision",
                "exact habove",
                "specialize "
                "central_binom_prime_valuation_zero_two_thirds_range p",
                "specialize "
                "central_binom_prime_valuation_zero_two_thirds_range n",
                "specialize "
                "central_binom_prime_valuation_zero_two_thirds_range C",
                "specialize "
                "central_binom_prime_valuation_zero_two_thirds_range v",
                "apply "
                "central_binom_prime_valuation_zero_two_thirds_range",
                "exact hp",
                "exact hpositive",
                "exact hbound",
                "exact hscaled",
                "exact hcentral",
                "exact hvaluation",
            ),
            "Valuation vanishes above the floor of two-thirds and at most n.",
        ),
        spec(
            FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT,
            "forall x s p t. "
            f"({sqrt_source}) -> ({sqrt_above}) -> ({sqrt_power}) -> "
            f"({sqrt_result})",
            (
                "mul_le_mul_right",
                "mul_le_mul_left",
                "le_trans",
                "lt_of_lt_of_le",
                "pow_two",
            ),
            (
                "intro x",
                "intro s",
                "intro p",
                "intro t",
                "intro hfloor",
                "intro habove",
                "intro hpower",
                "cases hfloor",
                f"have hfirst : {sqrt_first}",
                "specialize mul_le_mul_right (S s)",
                "specialize mul_le_mul_right p",
                "specialize mul_le_mul_right (S s)",
                "apply mul_le_mul_right",
                "exact habove",
                f"have hsecond : {sqrt_second}",
                "specialize mul_le_mul_left (S s)",
                "specialize mul_le_mul_left p",
                "specialize mul_le_mul_left p",
                "apply mul_le_mul_left",
                "exact habove",
                f"have hsquare : {sqrt_square}",
                "specialize le_trans (S s * S s)",
                "specialize le_trans (p * S s)",
                "specialize le_trans (p * p)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                f"have hraw : {sqrt_raw_result}",
                "specialize lt_of_lt_of_le x",
                "specialize lt_of_lt_of_le (S s * S s)",
                "specialize lt_of_lt_of_le (p * p)",
                "apply lt_of_lt_of_le",
                "exact hfloor_right",
                "exact hsquare",
                "have hvalue : t = p * p",
                "specialize pow_two p",
                "specialize pow_two 2",
                "specialize pow_two t",
                "apply pow_two",
                "refl",
                "exact hpower",
                "rewrite hvalue",
                "exact hraw",
            ),
            "A prime above a floor root has square strictly above the value.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE,
            "forall p n C v s. "
            f"({upper_prime}) -> ({upper_positive}) -> "
            f"({upper_central}) -> ({upper_valuation}) -> "
            f"({upper_floor}) -> ({upper_above}) -> ({upper_result})",
            (
                "lt_to_le",
                "le_trans",
                "pow_exists",
                FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT,
                "central_binom_prime_square_tail_valuation_le_one",
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "intro v",
                "intro s",
                "intro hp",
                "intro hpositive",
                "intro hcentral",
                "intro hvaluation",
                "intro hfloor",
                "intro habove",
                f"have htwo_le : {upper_two_le}",
                "specialize lt_to_le 2",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hpositive",
                f"have hone_two : {upper_one_two}",
                "exists 1",
                "norm_num",
                f"have hone_le : {upper_one_le}",
                "specialize le_trans 1",
                "specialize le_trans 2",
                "specialize le_trans n",
                "apply le_trans",
                "exact hone_two",
                "exact htwo_le",
                f"have hpower_exists : exists t. ({upper_power})",
                "specialize pow_exists p",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases hpower_exists",
                f"have hsquare : {upper_square}",
                "specialize floor_sqrt_above_root_power_two_strict (n + n)",
                "specialize floor_sqrt_above_root_power_two_strict s",
                "specialize floor_sqrt_above_root_power_two_strict p",
                "specialize floor_sqrt_above_root_power_two_strict x",
                "apply floor_sqrt_above_root_power_two_strict",
                "exact hfloor",
                "exact habove",
                "exact hpower_exists_witness",
                "specialize "
                "central_binom_prime_square_tail_valuation_le_one p",
                "specialize "
                "central_binom_prime_square_tail_valuation_le_one n",
                "specialize "
                "central_binom_prime_square_tail_valuation_le_one C",
                "specialize "
                "central_binom_prime_square_tail_valuation_le_one v",
                "specialize "
                "central_binom_prime_square_tail_valuation_le_one x",
                "apply "
                "central_binom_prime_square_tail_valuation_le_one",
                "exact hp",
                "exact hone_le",
                "exact hcentral",
                "exact hvaluation",
                "exact hpower_exists_witness",
                "exact hsquare",
            ),
            "Above the floor root, a central prime valuation is at most one.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES,
            "forall n s q r C p v. "
            f"({range_exclusion}) -> ({range_prime}) -> "
            f"({range_positive}) -> ({range_division}) -> "
            f"({range_central}) -> ({range_valuation}) -> "
            f"~(v = 0) -> ({range_result})",
            (
                "power_valuation_nonzero_exponent_divides_base",
                "no_bertrand_central_prime_divisor_ranges",
                CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro p",
                "intro v",
                "intro hexclusion",
                "intro hp",
                "intro hpositive",
                "intro hdivision",
                "intro hcentral",
                "intro hvaluation",
                "intro hnonzero",
                f"have hdivides : {range_divides}",
                "specialize power_valuation_nonzero_exponent_divides_base p",
                "specialize power_valuation_nonzero_exponent_divides_base C",
                "specialize power_valuation_nonzero_exponent_divides_base v",
                "apply power_valuation_nonzero_exponent_divides_base",
                "exact hvaluation",
                "exact hnonzero",
                f"have hranges : {range_raw}",
                "specialize no_bertrand_central_prime_divisor_ranges n",
                "specialize no_bertrand_central_prime_divisor_ranges s",
                "specialize no_bertrand_central_prime_divisor_ranges q",
                "specialize no_bertrand_central_prime_divisor_ranges C",
                "specialize no_bertrand_central_prime_divisor_ranges p",
                "apply no_bertrand_central_prime_divisor_ranges",
                "exact hexclusion",
                "exact hp",
                "exact hcentral",
                "exact hdivides",
                "cases hranges",
                "left",
                "exact hranges_left",
                "cases hranges_right",
                "right",
                "exact hranges_right_left",
                "cases hranges_right_right",
                "exfalso",
                "apply hnonzero",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient p",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient n",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient C",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient v",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient q",
                "specialize "
                "central_binom_prime_valuation_zero_above_third_quotient r",
                "apply "
                "central_binom_prime_valuation_zero_above_third_quotient",
                "exact hp",
                "exact hpositive",
                "exact hdivision",
                "exact hranges_right_right_left",
                "exact hranges_right_right_right",
                "exact hcentral",
                "exact hvaluation",
            ),
            "Every nonzero central valuation lies in one of two live ranges.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES,
            "forall n s q r C p v. "
            f"({range_exclusion}) -> ({range_prime}) -> "
            f"({range_positive}) -> ({factor_floor}) -> "
            f"({range_division}) -> ({range_central}) -> "
            f"({range_valuation}) -> ~(v = 0) -> ({factor_result})",
            (
                NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES,
                CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE,
                "one_le_of_ne_zero",
                "le_antisymm",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro p",
                "intro v",
                "intro hexclusion",
                "intro hp",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hvaluation",
                "intro hnonzero",
                f"have hranges : {range_result}",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges n",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges s",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges q",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges r",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges C",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges p",
                "specialize "
                "no_bertrand_central_nonzero_valuation_live_ranges v",
                "apply "
                "no_bertrand_central_nonzero_valuation_live_ranges",
                "exact hexclusion",
                "exact hp",
                "exact hpositive",
                "exact hdivision",
                "exact hcentral",
                "exact hvaluation",
                "exact hnonzero",
                "cases hranges",
                "left",
                "exact hranges_left",
                "cases hranges_right",
                "right",
                "split",
                "split",
                "exact hranges_right_left",
                "exact hranges_right_right",
                f"have hupper : {factor_upper}",
                "specialize "
                "central_binom_prime_above_floor_sqrt_valuation_le_one p",
                "specialize "
                "central_binom_prime_above_floor_sqrt_valuation_le_one n",
                "specialize "
                "central_binom_prime_above_floor_sqrt_valuation_le_one C",
                "specialize "
                "central_binom_prime_above_floor_sqrt_valuation_le_one v",
                "specialize "
                "central_binom_prime_above_floor_sqrt_valuation_le_one s",
                "apply "
                "central_binom_prime_above_floor_sqrt_valuation_le_one",
                "exact hp",
                "exact hpositive",
                "exact hcentral",
                "exact hvaluation",
                "exact hfloor",
                "exact hranges_right_left",
                f"have hlower : {factor_lower}",
                "specialize one_le_of_ne_zero v",
                "apply one_le_of_ne_zero",
                "exact hnonzero",
                "specialize le_antisymm v",
                "specialize le_antisymm 1",
                "apply le_antisymm",
                "exact hupper",
                "exact hlower",
            ),
            "The middle live range has exact valuation exponent one.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES,
            "forall n s q r C p v a. "
            f"({range_exclusion}) -> ({range_prime}) -> "
            f"({range_positive}) -> ({factor_floor}) -> "
            f"({range_division}) -> ({range_central}) -> "
            f"({range_valuation}) -> ({contribution_power}) -> "
            f"~(v = 0) -> ({contribution_result})",
            (
                NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES,
                "lt_to_le",
                "le_trans",
                "central_binom_prime_power_contribution_le_double",
                "pow_one",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro p",
                "intro v",
                "intro a",
                "intro hexclusion",
                "intro hp",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hvaluation",
                "intro hpower",
                "intro hnonzero",
                f"have hranges : {factor_result}",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges n",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges s",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges q",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges r",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges C",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges p",
                "specialize "
                "no_bertrand_central_nonzero_valuation_factor_ranges v",
                "apply "
                "no_bertrand_central_nonzero_valuation_factor_ranges",
                "exact hexclusion",
                "exact hp",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hvaluation",
                "exact hnonzero",
                "cases hranges",
                "left",
                "split",
                "exact hranges_left",
                f"have htwo_le : {contribution_two_le}",
                "specialize lt_to_le 2",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hpositive",
                f"have hone_two : {contribution_one_two}",
                "exists 1",
                "norm_num",
                f"have hone_le : {contribution_one_le}",
                "specialize le_trans 1",
                "specialize le_trans 2",
                "specialize le_trans n",
                "apply le_trans",
                "exact hone_two",
                "exact htwo_le",
                "specialize "
                "central_binom_prime_power_contribution_le_double p",
                "specialize "
                "central_binom_prime_power_contribution_le_double n",
                "specialize "
                "central_binom_prime_power_contribution_le_double C",
                "specialize "
                "central_binom_prime_power_contribution_le_double v",
                "specialize "
                "central_binom_prime_power_contribution_le_double a",
                "apply "
                "central_binom_prime_power_contribution_le_double",
                "exact hp",
                "exact hone_le",
                "exact hcentral",
                "exact hvaluation",
                "exact hpower",
                "cases hranges_right",
                "right",
                "split",
                "exact hranges_right_left",
                "specialize pow_one p",
                "specialize pow_one v",
                "specialize pow_one a",
                "apply pow_one",
                "exact hranges_right_right",
                "exact hpower",
            ),
            "A nonzero contribution is small-bounded or one middle prime.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES,
            "forall n s q r C p v a. "
            f"({range_exclusion}) -> ({range_prime}) -> "
            f"({range_positive}) -> ({factor_floor}) -> "
            f"({range_division}) -> ({range_central}) -> "
            f"({range_valuation}) -> ({contribution_power}) -> "
            f"({total_result})",
            (
                "eq_decidable",
                "pow_zero",
                NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro p",
                "intro v",
                "intro a",
                "intro hexclusion",
                "intro hp",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hvaluation",
                "intro hpower",
                r"have hzero : v = 0 \/ ~(v = 0)",
                "specialize eq_decidable v",
                "specialize eq_decidable 0",
                "exact eq_decidable",
                "cases hzero",
                "right",
                "specialize pow_zero p",
                "specialize pow_zero v",
                "specialize pow_zero a",
                "apply pow_zero",
                "exact hzero_left",
                "exact hpower",
                "left",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges n",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges s",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges q",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges r",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges C",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges p",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges v",
                "specialize "
                "no_bertrand_central_nonzero_contribution_factor_ranges a",
                "apply "
                "no_bertrand_central_nonzero_contribution_factor_ranges",
                "exact hexclusion",
                "exact hp",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hvaluation",
                "exact hpower",
                "exact hzero_right",
            ),
            "Every central prime contribution has one reviewed factor form.",
        ),
    )


__all__ = [
    "CENTRAL_BINOM_PRIME_ABOVE_FLOOR_SQRT_VALUATION_LE_ONE",
    "CENTRAL_BINOM_PRIME_VALUATION_ZERO_ABOVE_THIRD_QUOTIENT",
    "DIVISION_THREE_SCALED_UPPER_OF_QUOTIENT_LT",
    "FLOOR_SQRT_ABOVE_ROOT_POWER_TWO_STRICT",
    "NO_BERTRAND_CENTRAL_NONZERO_CONTRIBUTION_FACTOR_RANGES",
    "NO_BERTRAND_CENTRAL_NONZERO_VALUATION_FACTOR_RANGES",
    "NO_BERTRAND_CENTRAL_NONZERO_VALUATION_LIVE_RANGES",
    "NO_BERTRAND_CENTRAL_PRIME_CONTRIBUTION_RANGES",
    "make_bertrand_central_binom_factor_ranges_candidate_theorems",
]
