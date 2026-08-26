"""Constructive range-boundary arithmetic for the Bertrand B5 split.

The prime-contribution product is split at the floor-square-root ``s`` and
the quotient ``q = floor((n+n)/3)``.  This module proves the missing order
bridge ``s <= q`` from the relational floor and division records, then
packages exact additive gaps for both cut points.  No division or square-root
function is added to the language; every readable relation expands to the
existing witness-defined Peano formulas before parsing.

Importing this module grants no theorem authority and changes no edition.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .bertrand_choose_foundation_candidate import _le_term, _lt_term


TWO_LT_DOUBLE_LOWER_SIX = "two_lt_double_lower_six"
FLOOR_SQRT_TWO_LE_OF_TWO_LT = "floor_sqrt_two_le_of_two_lt"
THREE_MUL_LE_SQUARE_OF_THREE_LE = (
    "three_mul_le_square_of_three_le"
)
FLOOR_SQRT_THREE_MUL_LE_DOUBLE = (
    "floor_sqrt_three_mul_le_double"
)
DIVISION_QUOTIENT_LOWER_OF_SCALED_LE = (
    "division_quotient_lower_of_scaled_le"
)
FLOOR_SQRT_LE_THIRD_QUOTIENT = "floor_sqrt_le_third_quotient"
FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS = (
    "floor_sqrt_third_quotient_gap_exists"
)
DIVISION_QUOTIENT_LE_DIVIDEND = "division_quotient_le_dividend"
THIRD_QUOTIENT_DOUBLE_GAP_EXISTS = (
    "third_quotient_double_gap_exists"
)
FLOOR_THIRD_DOUBLE_GAP_PACKAGE = "floor_third_double_gap_package"


def make_bertrand_b5_range_boundaries_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered B5 cut-point arithmetic rows."""

    base_variables = ("n",)
    base_positive = _lt_term(
        "2",
        "n",
        tag="b5rbtdls_positive",
        variables=base_variables,
    )
    base_result = _le_term(
        "3 + 3",
        "n + n",
        tag="b5rbtdls_result",
        variables=base_variables,
    )
    base_left = _le_term(
        "3 + 3",
        "n + 3",
        tag="b5rbtdls_left",
        variables=base_variables,
    )
    base_right = _le_term(
        "n + 3",
        "n + n",
        tag="b5rbtdls_right",
        variables=base_variables,
    )

    root_variables = ("n", "s")
    root_positive = _lt_term(
        "2",
        "n",
        tag="b5rbfstl_positive",
        variables=root_variables,
    )
    root_floor = floor_sqrt_relation(
        "n + n",
        "s",
        tag="b5rbfstl_floor",
    )
    root_result = _le_term(
        "2",
        "s",
        tag="b5rbfstl_result",
        variables=root_variables,
    )
    root_reverse = _lt_term(
        "s",
        "2",
        tag="b5rbfstl_reverse",
        variables=root_variables,
    )
    root_three = _lt_term(
        "s",
        "3",
        tag="b5rbfstl_three",
        variables=root_variables,
    )
    root_upper = _lt_term(
        "n + n",
        "S s * S s",
        tag="b5rbfstl_upper",
        variables=root_variables,
    )
    root_lower_six = _le_term(
        "3 + 3",
        "n + n",
        tag="b5rbfstl_lower_six",
        variables=root_variables,
    )
    root_zero_small = _le_term(
        "S 0 * S 0",
        "3 + 3",
        tag="b5rbfstl_zero_small",
        variables=root_variables,
    )
    root_zero_reverse = _le_term(
        "S 0 * S 0",
        "n + n",
        tag="b5rbfstl_zero_reverse",
        variables=root_variables,
    )
    root_one_small = _le_term(
        "S 1 * S 1",
        "3 + 3",
        tag="b5rbfstl_one_small",
        variables=root_variables,
    )
    root_one_reverse = _le_term(
        "S 1 * S 1",
        "n + n",
        tag="b5rbfstl_one_reverse",
        variables=root_variables,
    )

    square_variables = ("s",)
    square_source = _le_term(
        "3",
        "s",
        tag="b5rbtmsts_source",
        variables=square_variables,
    )
    square_result = _le_term(
        "3 * s",
        "s * s",
        tag="b5rbtmsts_result",
        variables=square_variables,
    )

    scaled_variables = ("n", "s")
    scaled_positive = _lt_term(
        "2",
        "n",
        tag="b5rbfstmd_positive",
        variables=scaled_variables,
    )
    scaled_floor = floor_sqrt_relation(
        "n + n",
        "s",
        tag="b5rbfstmd_floor",
    )
    scaled_result = _le_term(
        "3 * s",
        "n + n",
        tag="b5rbfstmd_result",
        variables=scaled_variables,
    )
    scaled_two = _le_term(
        "2",
        "s",
        tag="b5rbfstmd_two",
        variables=scaled_variables,
    )
    scaled_strict = _lt_term(
        "2",
        "s",
        tag="b5rbfstmd_strict",
        variables=scaled_variables,
    )
    scaled_three = _le_term(
        "3",
        "s",
        tag="b5rbfstmd_three",
        variables=scaled_variables,
    )
    scaled_square = _le_term(
        "3 * s",
        "s * s",
        tag="b5rbfstmd_square",
        variables=scaled_variables,
    )
    scaled_floor_lower = _le_term(
        "s * s",
        "n + n",
        tag="b5rbfstmd_floor_lower",
        variables=scaled_variables,
    )
    scaled_lower_six = _le_term(
        "3 + 3",
        "n + n",
        tag="b5rbfstmd_lower_six",
        variables=scaled_variables,
    )

    quotient_variables = ("d", "N", "q", "r", "s")
    quotient_division = _divrem_term(
        "d",
        "N",
        "q",
        "r",
        tag="b5rbdqlosl_division",
        variables=quotient_variables,
    )
    quotient_scaled = _le_term(
        "d * s",
        "N",
        tag="b5rbdqlosl_scaled",
        variables=quotient_variables,
    )
    quotient_result = _le_term(
        "s",
        "q",
        tag="b5rbdqlosl_result",
        variables=quotient_variables,
    )
    quotient_reverse = _lt_term(
        "q",
        "s",
        tag="b5rbdqlosl_reverse",
        variables=quotient_variables,
    )
    quotient_upper = _lt_term(
        "N",
        "d * S q",
        tag="b5rbdqlosl_upper",
        variables=quotient_variables,
    )
    quotient_reverse_le = _le_term(
        "S q",
        "s",
        tag="b5rbdqlosl_reverse_le",
        variables=quotient_variables,
    )
    quotient_product_le = _le_term(
        "d * S q",
        "d * s",
        tag="b5rbdqlosl_product_le",
        variables=quotient_variables,
    )
    quotient_contradiction = _lt_term(
        "N",
        "d * s",
        tag="b5rbdqlosl_contradiction",
        variables=quotient_variables,
    )

    boundary_variables = ("n", "s", "q", "r")
    boundary_positive = _lt_term(
        "2",
        "n",
        tag="b5rbfsltq_positive",
        variables=boundary_variables,
    )
    boundary_floor = floor_sqrt_relation(
        "n + n",
        "s",
        tag="b5rbfsltq_floor",
    )
    boundary_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5rbfsltq_division",
        variables=boundary_variables,
    )
    boundary_scaled = _le_term(
        "3 * s",
        "n + n",
        tag="b5rbfsltq_scaled",
        variables=boundary_variables,
    )
    boundary_result = _le_term(
        "s",
        "q",
        tag="b5rbfsltq_result",
        variables=boundary_variables,
    )

    dividend_variables = ("n", "q", "r")
    dividend_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5rbdqld_division",
        variables=dividend_variables,
    )
    dividend_result = _le_term(
        "q",
        "n + n",
        tag="b5rbdqld_result",
        variables=dividend_variables,
    )
    dividend_one_three = _le_term(
        "1",
        "3",
        tag="b5rbdqld_one_three",
        variables=dividend_variables,
    )
    dividend_scaled = _le_term(
        "q",
        "3 * q",
        tag="b5rbdqld_scaled",
        variables=dividend_variables,
    )
    dividend_added = _le_term(
        "3 * q",
        "3 * q + r",
        tag="b5rbdqld_added",
        variables=dividend_variables,
    )
    dividend_raw = _le_term(
        "q",
        "3 * q + r",
        tag="b5rbdqld_raw",
        variables=dividend_variables,
    )

    return (
        spec(
            TWO_LT_DOUBLE_LOWER_SIX,
            f"forall n. ({base_positive}) -> ({base_result})",
            ("add_le_add_right", "add_le_add_left", "le_trans"),
            (
                "intro n",
                "intro hpositive",
                f"have hleft : {base_left}",
                "specialize add_le_add_right 3",
                "specialize add_le_add_right n",
                "specialize add_le_add_right 3",
                "apply add_le_add_right",
                "exact hpositive",
                f"have hright : {base_right}",
                "specialize add_le_add_left 3",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hpositive",
                "specialize le_trans (3 + 3)",
                "specialize le_trans (n + 3)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hleft",
                "exact hright",
            ),
            "A natural above two has double at least three plus three.",
        ),
        spec(
            FLOOR_SQRT_TWO_LE_OF_TWO_LT,
            "forall n s. "
            f"({root_positive}) -> ({root_floor}) -> ({root_result})",
            (
                "le_or_lt",
                "le_refl",
                "le_succ",
                "lt_of_lt_of_le",
                "lt_three_cases",
                "floor_sqrt_strict_upper_bound",
                TWO_LT_DOUBLE_LOWER_SIX,
                "le_trans",
                "lt_not_le",
                "lt_irrefl_expanded",
            ),
            (
                "intro n",
                "intro s",
                "intro hpositive",
                "intro hfloor",
                "have hcases : "
                f"({root_result}) \/ ({root_reverse})",
                "specialize le_or_lt 2",
                "specialize le_or_lt s",
                "exact le_or_lt",
                "cases hcases",
                "exact hcases_left",
                "have htwo_three : exists k. k + 2 = 3",
                "specialize le_refl 2",
                "specialize le_succ 2",
                "specialize le_succ 2",
                "apply le_succ",
                "exact le_refl",
                f"have hthree : {root_three}",
                "specialize lt_of_lt_of_le s",
                "specialize lt_of_lt_of_le 2",
                "specialize lt_of_lt_of_le 3",
                "apply lt_of_lt_of_le",
                "exact hcases_right",
                "exact htwo_three",
                "have hsmall_cases : s = 0 \/ s = 1 \/ s = 2",
                "specialize lt_three_cases s",
                "apply lt_three_cases",
                "exact hthree",
                f"have hupper : {root_upper}",
                "specialize floor_sqrt_strict_upper_bound (n + n)",
                "specialize floor_sqrt_strict_upper_bound s",
                "apply floor_sqrt_strict_upper_bound",
                "exact hfloor",
                f"have hlower : {root_lower_six}",
                "specialize two_lt_double_lower_six n",
                "apply two_lt_double_lower_six",
                "exact hpositive",
                "cases hsmall_cases",
                "cases hsmall_cases_left",
                "rewrite hsmall_cases_left_left at hupper",
                "rewrite hsmall_cases_left_left at hupper",
                f"have hsmall : {root_zero_small}",
                "exists 5",
                "norm_num",
                f"have hreverse : {root_zero_reverse}",
                "specialize le_trans (S 0 * S 0)",
                "specialize le_trans (3 + 3)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hsmall",
                "exact hlower",
                "exfalso",
                "specialize lt_not_le (n + n)",
                "specialize lt_not_le (S 0 * S 0)",
                "apply lt_not_le",
                "exact hupper",
                "exact hreverse",
                "rewrite hsmall_cases_left_right at hupper",
                "rewrite hsmall_cases_left_right at hupper",
                f"have hsmall : {root_one_small}",
                "exists 2",
                "norm_num",
                f"have hreverse : {root_one_reverse}",
                "specialize le_trans (S 1 * S 1)",
                "specialize le_trans (3 + 3)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hsmall",
                "exact hlower",
                "exfalso",
                "specialize lt_not_le (n + n)",
                "specialize lt_not_le (S 1 * S 1)",
                "apply lt_not_le",
                "exact hupper",
                "exact hreverse",
                "rewrite hsmall_cases_right at hcases_right",
                "exfalso",
                "specialize lt_irrefl_expanded 2",
                "apply lt_irrefl_expanded",
                "exact hcases_right",
            ),
            "The floor root of twice a natural above two is at least two.",
        ),
        spec(
            THREE_MUL_LE_SQUARE_OF_THREE_LE,
            f"forall s. ({square_source}) -> ({square_result})",
            ("mul_le_mul_right",),
            (
                "intro s",
                "intro hthree",
                "specialize mul_le_mul_right 3",
                "specialize mul_le_mul_right s",
                "specialize mul_le_mul_right s",
                "apply mul_le_mul_right",
                "exact hthree",
            ),
            "Every natural at least three dominates three times itself by its square.",
        ),
        spec(
            FLOOR_SQRT_THREE_MUL_LE_DOUBLE,
            "forall n s. "
            f"({scaled_positive}) -> ({scaled_floor}) -> ({scaled_result})",
            (
                TWO_LT_DOUBLE_LOWER_SIX,
                FLOOR_SQRT_TWO_LE_OF_TWO_LT,
                THREE_MUL_LE_SQUARE_OF_THREE_LE,
                "le_eq_or_lt",
                "floor_sqrt_lower_bound",
                "le_trans",
            ),
            (
                "intro n",
                "intro s",
                "intro hpositive",
                "intro hfloor",
                f"have htwo : {scaled_two}",
                "specialize floor_sqrt_two_le_of_two_lt n",
                "specialize floor_sqrt_two_le_of_two_lt s",
                "apply floor_sqrt_two_le_of_two_lt",
                "exact hpositive",
                "exact hfloor",
                "have hsplit : 2 = s \/ "
                f"({scaled_strict})",
                "specialize le_eq_or_lt 2",
                "specialize le_eq_or_lt s",
                "apply le_eq_or_lt",
                "exact htwo",
                "cases hsplit",
                f"have hlower : {scaled_lower_six}",
                "specialize two_lt_double_lower_six n",
                "apply two_lt_double_lower_six",
                "exact hpositive",
                "rewrite <- hsplit_left",
                "have hcalc : 3 * 2 = 3 + 3",
                "norm_num",
                "rewrite hcalc",
                "exact hlower",
                f"have hthree : {scaled_three}",
                "exact hsplit_right",
                f"have hsquare : {scaled_square}",
                "specialize three_mul_le_square_of_three_le s",
                "apply three_mul_le_square_of_three_le",
                "exact hthree",
                f"have hfloor_lower : {scaled_floor_lower}",
                "specialize floor_sqrt_lower_bound (n + n)",
                "specialize floor_sqrt_lower_bound s",
                "apply floor_sqrt_lower_bound",
                "exact hfloor",
                "specialize le_trans (3 * s)",
                "specialize le_trans (s * s)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hsquare",
                "exact hfloor_lower",
            ),
            "Three times the floor root lies below the doubled input.",
        ),
        spec(
            DIVISION_QUOTIENT_LOWER_OF_SCALED_LE,
            "forall d N q r s. "
            f"({quotient_division}) -> ({quotient_scaled}) -> "
            f"({quotient_result})",
            (
                "division_block_upper",
                "le_or_lt",
                "mul_le_mul_left",
                "lt_of_lt_of_le",
                "lt_not_le",
            ),
            (
                "intro d",
                "intro N",
                "intro q",
                "intro r",
                "intro s",
                "intro hdivision",
                "intro hscaled",
                "cases hdivision",
                "have hcases : "
                f"({quotient_result}) \/ ({quotient_reverse})",
                "specialize le_or_lt s",
                "specialize le_or_lt q",
                "exact le_or_lt",
                "cases hcases",
                "exact hcases_left",
                f"have hupper : {quotient_upper}",
                "rewrite hdivision_left",
                "specialize division_block_upper d",
                "specialize division_block_upper q",
                "specialize division_block_upper r",
                "apply division_block_upper",
                "exact hdivision_right",
                f"have hreverse : {quotient_reverse_le}",
                "exact hcases_right",
                f"have hproduct : {quotient_product_le}",
                "specialize mul_le_mul_left (S q)",
                "specialize mul_le_mul_left s",
                "specialize mul_le_mul_left d",
                "apply mul_le_mul_left",
                "exact hreverse",
                f"have hstrict : {quotient_contradiction}",
                "specialize lt_of_lt_of_le N",
                "specialize lt_of_lt_of_le (d * S q)",
                "specialize lt_of_lt_of_le (d * s)",
                "apply lt_of_lt_of_le",
                "exact hupper",
                "exact hproduct",
                "exfalso",
                "specialize lt_not_le N",
                "specialize lt_not_le (d * s)",
                "apply lt_not_le",
                "exact hstrict",
                "exact hscaled",
            ),
            "A scaled lower bound forces the division quotient above its scale index.",
        ),
        spec(
            FLOOR_SQRT_LE_THIRD_QUOTIENT,
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> ({boundary_result})",
            (
                FLOOR_SQRT_THREE_MUL_LE_DOUBLE,
                DIVISION_QUOTIENT_LOWER_OF_SCALED_LE,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                f"have hscaled : {boundary_scaled}",
                "specialize floor_sqrt_three_mul_le_double n",
                "specialize floor_sqrt_three_mul_le_double s",
                "apply floor_sqrt_three_mul_le_double",
                "exact hpositive",
                "exact hfloor",
                "specialize division_quotient_lower_of_scaled_le 3",
                "specialize division_quotient_lower_of_scaled_le (n + n)",
                "specialize division_quotient_lower_of_scaled_le q",
                "specialize division_quotient_lower_of_scaled_le r",
                "specialize division_quotient_lower_of_scaled_le s",
                "apply division_quotient_lower_of_scaled_le",
                "exact hdivision",
                "exact hscaled",
            ),
            "The floor root is at most the quotient of the doubled input by three.",
        ),
        spec(
            FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS,
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> exists g. s + g = q",
            ("add_comm", FLOOR_SQRT_LE_THIRD_QUOTIENT),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                f"have hbound : {boundary_result}",
                "specialize floor_sqrt_le_third_quotient n",
                "specialize floor_sqrt_le_third_quotient s",
                "specialize floor_sqrt_le_third_quotient q",
                "specialize floor_sqrt_le_third_quotient r",
                "apply floor_sqrt_le_third_quotient",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "cases hbound",
                "exists x",
                "specialize add_comm s",
                "specialize add_comm x",
                "rewrite add_comm",
                "exact hbound_witness",
            ),
            "The floor-root cut has an exact additive gap to the third quotient.",
        ),
        spec(
            DIVISION_QUOTIENT_LE_DIVIDEND,
            "forall n q r. "
            f"({dividend_division}) -> ({dividend_result})",
            (
                "le_mul_of_one_le_left",
                "le_add_right",
                "le_trans",
            ),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro hdivision",
                "cases hdivision",
                f"have hone_three : {dividend_one_three}",
                "exists 2",
                "norm_num",
                f"have hscaled : {dividend_scaled}",
                "specialize le_mul_of_one_le_left 3",
                "specialize le_mul_of_one_le_left q",
                "apply le_mul_of_one_le_left",
                "exact hone_three",
                f"have hadd : {dividend_added}",
                "specialize le_add_right (3 * q)",
                "specialize le_add_right r",
                "exact le_add_right",
                f"have hraw : {dividend_raw}",
                "specialize le_trans q",
                "specialize le_trans (3 * q)",
                "specialize le_trans (3 * q + r)",
                "apply le_trans",
                "exact hscaled",
                "exact hadd",
                "rewrite hdivision_left",
                "exact hraw",
            ),
            "The quotient by three is bounded by its doubled dividend.",
        ),
        spec(
            THIRD_QUOTIENT_DOUBLE_GAP_EXISTS,
            "forall n q r. "
            f"({dividend_division}) -> exists h. q + h = n + n",
            ("add_comm", DIVISION_QUOTIENT_LE_DIVIDEND),
            (
                "intro n",
                "intro q",
                "intro r",
                "intro hdivision",
                f"have hbound : {dividend_result}",
                "specialize division_quotient_le_dividend n",
                "specialize division_quotient_le_dividend q",
                "specialize division_quotient_le_dividend r",
                "apply division_quotient_le_dividend",
                "exact hdivision",
                "cases hbound",
                "exists x",
                "specialize add_comm q",
                "specialize add_comm x",
                "rewrite add_comm",
                "exact hbound_witness",
            ),
            "The third quotient has an exact additive gap to the doubled input.",
        ),
        spec(
            FLOOR_THIRD_DOUBLE_GAP_PACKAGE,
            "forall n s q r. "
            f"({boundary_positive}) -> ({boundary_floor}) -> "
            f"({boundary_division}) -> "
            "exists g h. s + g = q /\\ q + h = n + n",
            (
                FLOOR_SQRT_THIRD_QUOTIENT_GAP_EXISTS,
                THIRD_QUOTIENT_DOUBLE_GAP_EXISTS,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "have hfirst : exists g. s + g = q",
                "specialize floor_sqrt_third_quotient_gap_exists n",
                "specialize floor_sqrt_third_quotient_gap_exists s",
                "specialize floor_sqrt_third_quotient_gap_exists q",
                "specialize floor_sqrt_third_quotient_gap_exists r",
                "apply floor_sqrt_third_quotient_gap_exists",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "cases hfirst",
                "have hsecond : exists h. q + h = n + n",
                "specialize third_quotient_double_gap_exists n",
                "specialize third_quotient_double_gap_exists q",
                "specialize third_quotient_double_gap_exists r",
                "apply third_quotient_double_gap_exists",
                "exact hdivision",
                "cases hsecond",
                "exists x",
                "exists x1",
                "split",
                "exact hfirst_witness",
                "exact hsecond_witness",
            ),
            "Package the two exact additive gaps used by the three-range split.",
        ),
    )


__all__ = ["make_bertrand_b5_range_boundaries_candidate_theorems"]
