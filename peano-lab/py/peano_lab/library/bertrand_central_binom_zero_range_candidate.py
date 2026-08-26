"""Zero central-binomial valuation on the Bertrand two-thirds range.

For ``2 < n`` and ``2*n < 3*p <= 3*n``, the first quotient of ``n`` by
``p`` is one and the first quotient of ``2*n`` is two.  The square of the
prime already lies above ``2*n``, so every later doubled quotient is zero.
The sparse carry encoding therefore contains no one bit, forcing the exact
prime valuation of ``C(2*n,n)`` to be zero.

All readable relations expand into first-order Peano arithmetic before
parsing.  Importing this module registers no theorem and grants no authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_carry_candidate import (
    BIT_COUNT_POSITIVE_LAST_ONE,
    CENTRAL_BINOM_CARRY_BIT_COUNT,
    _bit_count_term,
    _carry_prefix,
    _carry_stored_point,
)
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_legendre_sum_candidate import _power_quotient_prefix_terms
from .bertrand_power_valuation_candidate import _power_terms, power_valuation
from .fermat_residue_map_candidate import prime
from .finite_sum_theorems import _at


DIVISION_QUOTIENT_ONE_OF_BOUNDS = "division_quotient_one_of_bounds"
DIVISION_QUOTIENT_TWO_OF_BOUNDS = "division_quotient_two_of_bounds"
PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE = (
    "prime_square_tail_of_two_three_range"
)
DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE = (
    "division_first_two_of_two_three_range"
)
DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO = (
    "double_quotient_carry_prefix_entries_zero"
)
CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS = (
    "central_binom_prime_valuation_zero_of_exact_double_quotients"
)
CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE = (
    "central_binom_prime_valuation_zero_two_thirds_range"
)


def make_bertrand_central_binom_zero_range_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered two-thirds zero-range rows."""

    one_variables = ("d", "n")
    one_lower = _le_term(
        "d", "n", tag="bdqob_lower", variables=one_variables
    )
    one_upper = _lt_term(
        "n", "d + d", tag="bdqob_upper", variables=one_variables
    )
    one_result = _divrem_term(
        "d",
        "n",
        "1",
        "r",
        tag="bdqob_result",
        variables=one_variables + ("r",),
    )
    one_remainder = _lt_term(
        "x", "d", tag="bdqob_remainder", variables=one_variables + ("x",)
    )

    two_variables = ("d", "n")
    two_lower = _le_term(
        "d + d", "n", tag="bdqtb_lower", variables=two_variables
    )
    two_upper = _lt_term(
        "n", "(d + d) + d", tag="bdqtb_upper", variables=two_variables
    )
    two_result = _divrem_term(
        "d",
        "n",
        "2",
        "r",
        tag="bdqtb_result",
        variables=two_variables + ("r",),
    )
    two_remainder = _lt_term(
        "x", "d", tag="bdqtb_remainder", variables=two_variables + ("x",)
    )

    square_variables = ("p", "n", "s")
    square_prime = prime("p", tag="bpstt_prime")
    square_positive = _lt_term(
        "2", "n", tag="bpstt_positive", variables=square_variables
    )
    square_scaled = _lt_term(
        "n + n",
        "(p + p) + p",
        tag="bpstt_scaled",
        variables=square_variables,
    )
    square_power = _power_terms(
        "p", "2", "s", tag="bpstt_power"
    )
    square_result = _lt_term(
        "n + n", "s", tag="bpstt_result", variables=square_variables
    )
    square_three_lower = _le_term(
        "3", "n", tag="bpstt_three_lower", variables=square_variables
    )
    square_six_lower = _le_term(
        "3 + 3",
        "n + n",
        tag="bpstt_six_lower",
        variables=square_variables,
    )
    square_first_add = _le_term(
        "3 + 3",
        "n + 3",
        tag="bpstt_first_add",
        variables=square_variables,
    )
    square_second_add = _le_term(
        "n + 3",
        "n + n",
        tag="bpstt_second_add",
        variables=square_variables,
    )
    square_prime_lower = _le_term(
        "3", "p", tag="bpstt_prime_lower", variables=square_variables
    )
    square_product_lower = _le_term(
        "(p + p) + p",
        "p * p",
        tag="bpstt_product_lower",
        variables=square_variables,
    )
    square_raw_product_lower = _le_term(
        "p * 3",
        "p * p",
        tag="bpstt_raw_product_lower",
        variables=square_variables,
    )
    square_strict_product = _lt_term(
        "n + n",
        "p * p",
        tag="bpstt_strict_product",
        variables=square_variables,
    )

    first_variables = ("p", "n")
    first_lower = _le_term(
        "p", "n", tag="bdftt_lower", variables=first_variables
    )
    first_scaled = _lt_term(
        "n + n",
        "(p + p) + p",
        tag="bdftt_scaled",
        variables=first_variables,
    )
    first_result_left = _divrem_term(
        "p",
        "n",
        "1",
        "r",
        tag="bdftt_left",
        variables=first_variables + ("r", "R"),
    )
    first_result_right = _divrem_term(
        "p",
        "n + n",
        "2",
        "R",
        tag="bdftt_right",
        variables=first_variables + ("r", "R"),
    )
    first_double_lower = _le_term(
        "p + p",
        "n + n",
        tag="bdftt_double_lower",
        variables=first_variables,
    )
    first_double_left = _le_term(
        "p + p",
        "n + p",
        tag="bdftt_double_left",
        variables=first_variables,
    )
    first_shift_lower = _le_term(
        "n + p",
        "n + n",
        tag="bdftt_shift_lower",
        variables=first_variables,
    )
    first_shift_strict = _lt_term(
        "n + p",
        "(p + p) + p",
        tag="bdftt_shift_strict",
        variables=first_variables,
    )
    first_upper = _lt_term(
        "n", "p + p", tag="bdftt_upper", variables=first_variables
    )

    entries_variables = (
        "p",
        "n",
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        "q",
        "r",
        "R",
        "s",
        "i",
    )
    entries_base = _le_term(
        "1", "p", tag="bdqcpez_base", variables=entries_variables
    )
    entries_square = _power_terms(
        "p", "2", "s", tag="bdqcpez_square"
    )
    entries_strict = _lt_term(
        "n + n",
        "s",
        tag="bdqcpez_strict",
        variables=entries_variables,
    )
    entries_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="bdqcpez_left"
    )
    entries_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="bdqcpez_right"
    )
    entries_carry = _carry_prefix(
        "b",
        "c",
        "d",
        "e",
        "f",
        "g",
        "l",
        tag="bdqcpez_carry",
        variables=entries_variables,
    )
    entries_first = _divrem_term(
        "p",
        "n",
        "q",
        "r",
        tag="bdqcpez_first",
        variables=entries_variables,
    )
    entries_double = _divrem_term(
        "p",
        "n + n",
        "q + q",
        "R",
        tag="bdqcpez_double",
        variables=entries_variables,
    )
    entries_bound = _lt_term(
        "i", "l", tag="bdqcpez_bound", variables=entries_variables
    )
    entries_result = _at("f", "g", "i", "0", tag="bdqcpez_result")
    entries_left_data = (
        "exists D u a. ("
        + _power_terms("p", "S i", "D", tag="bdqcpez_left_power")
        + ") /\\ (("
        + _at("b", "c", "i", "u", tag="bdqcpez_left_entry")
        + ") /\\ ("
        + _divrem_term(
            "D",
            "n",
            "u",
            "a",
            tag="bdqcpez_left_division",
            variables=entries_variables + ("D", "u", "a"),
        )
        + "))"
    )
    entries_right_data = (
        "exists D u a. ("
        + _power_terms("p", "S i", "D", tag="bdqcpez_right_power")
        + ") /\\ (("
        + _at("d", "e", "i", "u", tag="bdqcpez_right_entry")
        + ") /\\ ("
        + _divrem_term(
            "D",
            "n + n",
            "u",
            "a",
            tag="bdqcpez_right_division",
            variables=entries_variables + ("D", "u", "a"),
        )
        + "))"
    )
    entries_semantic = _carry_stored_point(
        "b", "c", "d", "e", "f", "g", "i", tag="bdqcpez_semantic"
    )
    entries_tail_exponent = _le_term(
        "2",
        "S i",
        tag="bdqcpez_tail_exponent",
        variables=entries_variables,
    )
    entries_tail_strict = _lt_term(
        "n + n",
        "x3",
        tag="bdqcpez_tail_strict",
        variables=entries_variables
        + tuple(f"x{index}" if index else "x" for index in range(10)),
    )

    exact_variables = ("p", "n", "C", "v", "q", "r", "R", "s")
    exact_prime = prime("p", tag="bcpvzeq_prime")
    exact_central = _central_binom_relation_term(
        "n", "C", tag="bcpvzeq_central", variables=exact_variables
    )
    exact_valuation = power_valuation(
        "p", "C", "v", tag="bcpvzeq_valuation"
    )
    exact_base = _le_term(
        "1", "p", tag="bcpvzeq_base", variables=exact_variables
    )
    exact_square = _power_terms("p", "2", "s", tag="bcpvzeq_square")
    exact_strict = _lt_term(
        "n + n", "s", tag="bcpvzeq_strict", variables=exact_variables
    )
    exact_first = _divrem_term(
        "p",
        "n",
        "q",
        "r",
        tag="bcpvzeq_first",
        variables=exact_variables,
    )
    exact_double = _divrem_term(
        "p",
        "n + n",
        "q + q",
        "R",
        tag="bcpvzeq_double",
        variables=exact_variables,
    )
    exact_package = (
        "exists b c d e f g. ("
        + _power_quotient_prefix_terms(
            "p", "n", "b", "c", "n + n", tag="bcpvzeq_left"
        )
        + ") /\\ (("
        + _power_quotient_prefix_terms(
            "p", "n + n", "d", "e", "n + n", tag="bcpvzeq_right"
        )
        + ") /\\ (("
        + _carry_prefix(
            "b",
            "c",
            "d",
            "e",
            "f",
            "g",
            "n + n",
            tag="bcpvzeq_carry",
            variables=exact_variables + ("b", "c", "d", "e", "f", "g"),
        )
        + ") /\\ ("
        + _bit_count_term(
            "f", "g", "n + n", "v", tag="bcpvzeq_count"
        )
        + ")))"
    )
    exact_last = (
        "exists i. ("
        + _lt_term(
            "i",
            "n + n",
            tag="bcpvzeq_last_bound",
            variables=exact_variables + ("i",),
        )
        + ") /\\ (("
        + _at("x4", "x5", "i", "1", tag="bcpvzeq_last_entry")
        + ") /\\ ("
        + _le_term(
            "S x6",
            "S i",
            tag="bcpvzeq_last_result",
            variables=exact_variables
            + tuple(f"x{index}" if index else "x" for index in range(8)),
        )
        + "))"
    )
    exact_zero_entries = (
        "forall i. ("
        + _lt_term(
            "i",
            "n + n",
            tag="bcpvzeq_zero_bound",
            variables=exact_variables
            + tuple(f"x{index}" if index else "x" for index in range(7))
            + ("i",),
        )
        + ") -> ("
        + _at("x4", "x5", "i", "0", tag="bcpvzeq_zero_entries")
        + ")"
    )

    public_variables = ("p", "n", "C", "v")
    public_prime = prime("p", tag="bcpvztt_prime")
    public_positive = _lt_term(
        "2", "n", tag="bcpvztt_positive", variables=public_variables
    )
    public_lower = _le_term(
        "p", "n", tag="bcpvztt_lower", variables=public_variables
    )
    public_scaled = _lt_term(
        "n + n",
        "(p + p) + p",
        tag="bcpvztt_scaled",
        variables=public_variables,
    )
    public_central = _central_binom_relation_term(
        "n", "C", tag="bcpvztt_central", variables=public_variables
    )
    public_valuation = power_valuation(
        "p", "C", "v", tag="bcpvztt_valuation"
    )
    public_square = _power_terms("p", "2", "s", tag="bcpvztt_square")
    public_square_strict = _lt_term(
        "n + n",
        "x",
        tag="bcpvztt_square_strict",
        variables=public_variables + ("x",),
    )
    public_first = _divrem_term(
        "p",
        "n",
        "1",
        "x",
        tag="bcpvztt_first",
        variables=public_variables + ("x", "x1"),
    )
    public_double = _divrem_term(
        "p",
        "n + n",
        "2",
        "x1",
        tag="bcpvztt_double",
        variables=public_variables + ("x", "x1"),
    )
    public_double_aligned = _divrem_term(
        "p",
        "n + n",
        "1 + 1",
        "x2",
        tag="bcpvztt_double_aligned",
        variables=public_variables + ("x", "x1", "x2"),
    )

    return (
        spec(
            DIVISION_QUOTIENT_ONE_OF_BOUNDS,
            "forall d n. "
            f"({one_lower}) -> ({one_upper}) -> exists r. ({one_result})",
            ("add_comm", "mul_one", "add_lt_cancel_left"),
            (
                "intro d",
                "intro n",
                "intro hlower",
                "intro hupper",
                "cases hlower",
                "have hsum : d + x = n",
                "trans x + d",
                "apply add_comm",
                "exact hlower_witness",
                f"have hremainder : {one_remainder}",
                "rewrite <- hsum at hupper",
                "specialize add_lt_cancel_left d",
                "specialize add_lt_cancel_left x",
                "specialize add_lt_cancel_left d",
                "apply add_lt_cancel_left",
                "exact hupper",
                "exists x",
                "split",
                "trans d + x",
                "symm",
                "exact hsum",
                "specialize mul_one d",
                "rewrite mul_one",
                "refl",
                "exact hremainder",
            ),
            "Bounds between one and two divisors force quotient one.",
        ),
        spec(
            DIVISION_QUOTIENT_TWO_OF_BOUNDS,
            "forall d n. "
            f"({two_lower}) -> ({two_upper}) -> exists r. ({two_result})",
            ("add_comm", "mul_one", "add_lt_cancel_left"),
            (
                "intro d",
                "intro n",
                "intro hlower",
                "intro hupper",
                "cases hlower",
                "have hsum : (d + d) + x = n",
                "trans x + (d + d)",
                "apply add_comm",
                "exact hlower_witness",
                f"have hremainder : {two_remainder}",
                "rewrite <- hsum at hupper",
                "specialize add_lt_cancel_left (d + d)",
                "specialize add_lt_cancel_left x",
                "specialize add_lt_cancel_left d",
                "apply add_lt_cancel_left",
                "exact hupper",
                "exists x",
                "split",
                "trans (d + d) + x",
                "symm",
                "exact hsum",
                "congr",
                "rewrite PA6",
                "specialize mul_one d",
                "rewrite mul_one",
                "refl",
                "refl",
                "exact hremainder",
            ),
            "Bounds between two and three divisors force quotient two.",
        ),
        spec(
            PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE,
            "forall p n s. "
            f"({square_prime}) -> ({square_positive}) -> "
            f"({square_scaled}) -> ({square_power}) -> ({square_result})",
            (
                "prime_is_succ_succ",
                "zero_or_succ",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "lt_not_le",
                "mul_le_mul_left",
                "mul_one",
                "lt_of_lt_of_le",
                "pow_two",
            ),
            (
                "intro p",
                "intro n",
                "intro s",
                "intro hp",
                "intro hpositive",
                "intro hscaled",
                "intro hsquare",
                "have hshape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hshape",
                "specialize zero_or_succ x",
                "cases zero_or_succ",
                f"have hn_lower : {square_three_lower}",
                "exact hpositive",
                f"have hdouble_lower : {square_six_lower}",
                f"have hfirst_add : {square_first_add}",
                "specialize add_le_add_right 3",
                "specialize add_le_add_right n",
                "specialize add_le_add_right 3",
                "apply add_le_add_right",
                "exact hn_lower",
                f"have hsecond_add : {square_second_add}",
                "specialize add_le_add_left 3",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hn_lower",
                "specialize le_trans (3 + 3)",
                "specialize le_trans (n + 3)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hfirst_add",
                "exact hsecond_add",
                "rewrite zero_or_succ_left at hshape_witness",
                "rewrite hshape_witness at hscaled",
                "rewrite hshape_witness at hscaled",
                "rewrite hshape_witness at hscaled",
                "exfalso",
                "specialize lt_not_le (n + n)",
                "specialize lt_not_le ((2 + 2) + 2)",
                "apply lt_not_le",
                "exact hscaled",
                "have hsmall : (2 + 2) + 2 = 3 + 3",
                "norm_num",
                "rewrite hsmall",
                "exact hdouble_lower",
                "cases zero_or_succ_right",
                f"have hp_lower : {square_prime_lower}",
                "exists x1",
                "rewrite hshape_witness",
                "rewrite zero_or_succ_right_witness",
                "simp",
                f"have hproduct_lower : {square_product_lower}",
                f"have hraw_product_lower : {square_raw_product_lower}",
                "specialize mul_le_mul_left 3",
                "specialize mul_le_mul_left p",
                "specialize mul_le_mul_left p",
                "apply mul_le_mul_left",
                "exact hp_lower",
                "have htriple : p * 3 = (p + p) + p",
                "rewrite PA6",
                "rewrite PA6",
                "specialize mul_one p",
                "rewrite mul_one",
                "refl",
                "rewrite htriple at hraw_product_lower",
                "exact hraw_product_lower",
                f"have hstrict_product : {square_strict_product}",
                "specialize lt_of_lt_of_le (n + n)",
                "specialize lt_of_lt_of_le ((p + p) + p)",
                "specialize lt_of_lt_of_le (p * p)",
                "apply lt_of_lt_of_le",
                "exact hscaled",
                "exact hproduct_lower",
                "have hsquare_value : s = p * p",
                "specialize pow_two p",
                "specialize pow_two 2",
                "specialize pow_two s",
                "apply pow_two",
                "refl",
                "exact hsquare",
                "rewrite hsquare_value",
                "exact hstrict_product",
            ),
            "The scaled two-thirds range places the prime square above 2*n.",
        ),
        spec(
            DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE,
            "forall p n. "
            f"({first_lower}) -> ({first_scaled}) -> "
            f"exists r R. ({first_result_left}) /\ ({first_result_right})",
            (
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "lt_of_le_of_lt",
                "add_comm",
                "add_lt_cancel_left",
                DIVISION_QUOTIENT_ONE_OF_BOUNDS,
                DIVISION_QUOTIENT_TWO_OF_BOUNDS,
            ),
            (
                "intro p",
                "intro n",
                "intro hlower",
                "intro hscaled",
                f"have hdouble_lower : {first_double_lower}",
                f"have hdouble_left : {first_double_left}",
                "specialize add_le_add_right p",
                "specialize add_le_add_right n",
                "specialize add_le_add_right p",
                "apply add_le_add_right",
                "exact hlower",
                f"have hshift_lower : {first_shift_lower}",
                "specialize add_le_add_left p",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hlower",
                "specialize le_trans (p + p)",
                "specialize le_trans (n + p)",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hdouble_left",
                "exact hshift_lower",
                f"have hshift_lower : {first_shift_lower}",
                "specialize add_le_add_left p",
                "specialize add_le_add_left n",
                "specialize add_le_add_left n",
                "apply add_le_add_left",
                "exact hlower",
                f"have hshift_strict : {first_shift_strict}",
                "specialize lt_of_le_of_lt (n + p)",
                "specialize lt_of_le_of_lt (n + n)",
                "specialize lt_of_le_of_lt ((p + p) + p)",
                "apply lt_of_le_of_lt",
                "exact hshift_lower",
                "exact hscaled",
                "have hleft_comm : n + p = p + n",
                "apply add_comm",
                "rewrite hleft_comm at hshift_strict",
                "have hright_comm : (p + p) + p = p + (p + p)",
                "apply add_comm",
                "rewrite hright_comm at hshift_strict",
                f"have hfirst_upper : {first_upper}",
                "specialize add_lt_cancel_left p",
                "specialize add_lt_cancel_left n",
                "specialize add_lt_cancel_left (p + p)",
                "apply add_lt_cancel_left",
                "exact hshift_strict",
                "have hfirst : exists r. " + first_result_left,
                "specialize division_quotient_one_of_bounds p",
                "specialize division_quotient_one_of_bounds n",
                "apply division_quotient_one_of_bounds",
                "exact hlower",
                "exact hfirst_upper",
                "have hsecond : exists R. " + first_result_right,
                "specialize division_quotient_two_of_bounds p",
                "specialize division_quotient_two_of_bounds (n + n)",
                "apply division_quotient_two_of_bounds",
                "exact hdouble_lower",
                "exact hscaled",
                "cases hfirst",
                "cases hsecond",
                "exists x",
                "exists x1",
                "split",
                "exact hfirst_witness",
                "exact hsecond_witness",
            ),
            "The two-thirds range fixes the first quotients at one and two.",
        ),
        spec(
            DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO,
            "forall p n b c d e f g l q r R s. "
            f"({entries_base}) -> ({entries_square}) -> "
            f"({entries_strict}) -> ({entries_left}) -> "
            f"({entries_right}) -> ({entries_carry}) -> "
            f"({entries_first}) -> ({entries_double}) -> "
            f"forall i. ({entries_bound}) -> ({entries_result})",
            (
                "zero_or_succ",
                "pow_one",
                "division_remainder_unique",
                "beta_at_unique",
                "zero_add",
                "lt_irrefl_expanded",
                "pow_tail_strict_of_square",
                "division_zero_quotient_of_lt",
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "intro l",
                "intro q",
                "intro r",
                "intro R",
                "intro s",
                "intro hbase",
                "intro hsquare",
                "intro hstrict",
                "intro hleft",
                "intro hright",
                "intro hcarry",
                "intro hfirst",
                "intro hdouble",
                "intro i",
                "intro hi",
                f"have hleft_data : {entries_left_data}",
                "specialize hleft i",
                "apply hleft",
                "exact hi",
                "cases hleft_data",
                "cases hleft_data_witness",
                "cases hleft_data_witness_witness",
                "cases hleft_data_witness_witness_witness",
                "cases hleft_data_witness_witness_witness_right",
                f"have hright_data : {entries_right_data}",
                "specialize hright i",
                "apply hright",
                "exact hi",
                "cases hright_data",
                "cases hright_data_witness",
                "cases hright_data_witness_witness",
                "cases hright_data_witness_witness_witness",
                "cases hright_data_witness_witness_witness_right",
                f"have hsemantic : {entries_semantic}",
                "specialize hcarry i",
                "apply hcarry",
                "exact hi",
                "cases hsemantic",
                "cases hsemantic_witness",
                "cases hsemantic_witness_witness",
                "cases hsemantic_witness_witness_witness",
                "cases hsemantic_witness_witness_witness_right",
                "cases hsemantic_witness_witness_witness_right_right",
                "specialize zero_or_succ i",
                "cases zero_or_succ",
                "have hexponent_one : S i = 1",
                "rewrite zero_or_succ_left",
                "refl",
                "have hleft_power : x = p",
                "specialize pow_one p",
                "specialize pow_one (S i)",
                "specialize pow_one x",
                "apply pow_one",
                "exact hexponent_one",
                "exact hleft_data_witness_witness_witness_left",
                "have hright_power : x3 = p",
                "specialize pow_one p",
                "specialize pow_one (S i)",
                "specialize pow_one x3",
                "apply pow_one",
                "exact hexponent_one",
                "exact hright_data_witness_witness_witness_left",
                "rewrite hleft_power at "
                "hleft_data_witness_witness_witness_right_right",
                "rewrite hleft_power at "
                "hleft_data_witness_witness_witness_right_right",
                "rewrite hright_power at "
                "hright_data_witness_witness_witness_right_right",
                "rewrite hright_power at "
                "hright_data_witness_witness_witness_right_right",
                "cases hleft_data_witness_witness_witness_right_right",
                "cases hright_data_witness_witness_witness_right_right",
                "cases hfirst",
                "cases hdouble",
                "have hleft_unique : x1 = q /\\ x2 = r",
                "specialize division_remainder_unique p",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique x1",
                "specialize division_remainder_unique x2",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique r",
                "apply division_remainder_unique",
                "exact hleft_data_witness_witness_witness_right_right_left",
                "exact hleft_data_witness_witness_witness_right_right_right",
                "exact hfirst_left",
                "exact hfirst_right",
                "have hright_unique : x4 = q + q /\\ x5 = R",
                "specialize division_remainder_unique p",
                "specialize division_remainder_unique (n + n)",
                "specialize division_remainder_unique x4",
                "specialize division_remainder_unique x5",
                "specialize division_remainder_unique (q + q)",
                "specialize division_remainder_unique R",
                "apply division_remainder_unique",
                "exact hright_data_witness_witness_witness_right_right_left",
                "exact hright_data_witness_witness_witness_right_right_right",
                "exact hdouble_left",
                "exact hdouble_right",
                "cases hleft_unique",
                "cases hright_unique",
                "have hleft_entry : x1 = x6",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x6",
                "apply beta_at_unique",
                "exact hleft_data_witness_witness_witness_right_left",
                "exact hsemantic_witness_witness_witness_left",
                "have hright_entry : x4 = x7",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x7",
                "apply beta_at_unique",
                "exact hright_data_witness_witness_witness_right_left",
                "exact hsemantic_witness_witness_witness_right_left",
                "cases hsemantic_witness_witness_witness_right_right_right",
                "cases hsemantic_witness_witness_witness_right_right_"
                "right_left",
                "rewrite hsemantic_witness_witness_witness_right_right_"
                "right_left_left at "
                "hsemantic_witness_witness_witness_right_right_left",
                "rewrite hsemantic_witness_witness_witness_right_right_"
                "right_left_left at "
                "hsemantic_witness_witness_witness_right_right_left",
                "exact hsemantic_witness_witness_witness_right_right_left",
                "cases hsemantic_witness_witness_witness_right_right_"
                "right_right",
                "rewrite <- hright_entry at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite hright_unique_left at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite <- hleft_entry at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite <- hleft_entry at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite hleft_unique_left at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite hleft_unique_left at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "exfalso",
                "specialize lt_irrefl_expanded (q + q)",
                "apply lt_irrefl_expanded",
                "exists 0",
                "trans S (q + q)",
                "specialize zero_add (S (q + q))",
                "exact zero_add",
                "symm",
                "exact hsemantic_witness_witness_witness_right_right_"
                "right_right_right",
                "cases zero_or_succ_right",
                f"have hexponent_tail : {entries_tail_exponent}",
                "exists x9",
                "rewrite zero_or_succ_right_witness",
                "simp",
                f"have htail : {entries_tail_strict}",
                "specialize pow_tail_strict_of_square p",
                "specialize pow_tail_strict_of_square (S i)",
                "specialize pow_tail_strict_of_square x3",
                "specialize pow_tail_strict_of_square s",
                "specialize pow_tail_strict_of_square (n + n)",
                "apply pow_tail_strict_of_square",
                "exact hbase",
                "exact hexponent_tail",
                "exact hsquare",
                "exact hright_data_witness_witness_witness_left",
                "exact hstrict",
                "have hright_zero : x4 = 0",
                "specialize division_zero_quotient_of_lt x3",
                "specialize division_zero_quotient_of_lt (n + n)",
                "specialize division_zero_quotient_of_lt x4",
                "specialize division_zero_quotient_of_lt x5",
                "apply division_zero_quotient_of_lt",
                "exact hright_data_witness_witness_witness_right_right",
                "exact htail",
                "have hright_entry : x4 = x7",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x7",
                "apply beta_at_unique",
                "exact hright_data_witness_witness_witness_right_left",
                "exact hsemantic_witness_witness_witness_right_left",
                "cases hsemantic_witness_witness_witness_right_right_right",
                "cases hsemantic_witness_witness_witness_right_right_"
                "right_left",
                "rewrite hsemantic_witness_witness_witness_right_right_"
                "right_left_left at "
                "hsemantic_witness_witness_witness_right_right_left",
                "rewrite hsemantic_witness_witness_witness_right_right_"
                "right_left_left at "
                "hsemantic_witness_witness_witness_right_right_left",
                "exact hsemantic_witness_witness_witness_right_right_left",
                "cases hsemantic_witness_witness_witness_right_right_"
                "right_right",
                "rewrite <- hright_entry at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "rewrite hright_zero at "
                "hsemantic_witness_witness_witness_right_right_right_"
                "right_right",
                "exfalso",
                "apply PA1",
                "symm",
                "exact hsemantic_witness_witness_witness_right_right_"
                "right_right_right",
            ),
            "Exact doubled quotients and a square tail force every carry to zero.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS,
            "forall p n C v q r R s. "
            f"({exact_prime}) -> ({exact_central}) -> "
            f"({exact_valuation}) -> ({exact_base}) -> "
            f"({exact_square}) -> ({exact_strict}) -> "
            f"({exact_first}) -> ({exact_double}) -> v = 0",
            (
                CENTRAL_BINOM_CARRY_BIT_COUNT,
                "zero_or_succ",
                BIT_COUNT_POSITIVE_LAST_ONE,
                DOUBLE_QUOTIENT_CARRY_PREFIX_ENTRIES_ZERO,
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "intro v",
                "intro q",
                "intro r",
                "intro R",
                "intro s",
                "intro hp",
                "intro hcentral",
                "intro hvaluation",
                "intro hbase",
                "intro hsquare",
                "intro hstrict",
                "intro hfirst",
                "intro hdouble",
                f"have hpackage : {exact_package}",
                "specialize central_binom_carry_bit_count p",
                "specialize central_binom_carry_bit_count n",
                "specialize central_binom_carry_bit_count C",
                "specialize central_binom_carry_bit_count v",
                "apply central_binom_carry_bit_count",
                "exact hp",
                "exact hcentral",
                "exact hvaluation",
                "cases hpackage",
                "cases hpackage_witness",
                "cases hpackage_witness_witness",
                "cases hpackage_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness",
                "cases hpackage_witness_witness_witness_witness_witness_"
                "witness",
                "cases hpackage_witness_witness_witness_witness_witness_"
                "witness_right",
                "cases hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right",
                "specialize zero_or_succ v",
                "cases zero_or_succ",
                "exact zero_or_succ_left",
                "cases zero_or_succ_right",
                "rewrite zero_or_succ_right_witness at "
                "hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_right",
                "rewrite zero_or_succ_right_witness at "
                "hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_right",
                f"have hlast : {exact_last}",
                "specialize bit_count_positive_last_one x4",
                "specialize bit_count_positive_last_one x5",
                "specialize bit_count_positive_last_one (n + n)",
                "specialize bit_count_positive_last_one x6",
                "apply bit_count_positive_last_one",
                "exact hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_right",
                "cases hlast",
                "cases hlast_witness",
                "cases hlast_witness_right",
                f"have hentries : {exact_zero_entries}",
                "specialize double_quotient_carry_prefix_entries_zero p",
                "specialize double_quotient_carry_prefix_entries_zero n",
                "specialize double_quotient_carry_prefix_entries_zero x",
                "specialize double_quotient_carry_prefix_entries_zero x1",
                "specialize double_quotient_carry_prefix_entries_zero x2",
                "specialize double_quotient_carry_prefix_entries_zero x3",
                "specialize double_quotient_carry_prefix_entries_zero x4",
                "specialize double_quotient_carry_prefix_entries_zero x5",
                "specialize double_quotient_carry_prefix_entries_zero (n + n)",
                "specialize double_quotient_carry_prefix_entries_zero q",
                "specialize double_quotient_carry_prefix_entries_zero r",
                "specialize double_quotient_carry_prefix_entries_zero R",
                "specialize double_quotient_carry_prefix_entries_zero s",
                "apply double_quotient_carry_prefix_entries_zero",
                "exact hbase",
                "exact hsquare",
                "exact hstrict",
                "exact hpackage_witness_witness_witness_witness_witness_"
                "witness_left",
                "exact hpackage_witness_witness_witness_witness_witness_"
                "witness_right_left",
                "exact hpackage_witness_witness_witness_witness_witness_"
                "witness_right_right_left",
                "exact hfirst",
                "exact hdouble",
                "have hzero : "
                + _at("x4", "x5", "x7", "0", tag="bcpvzeq_zero_entry"),
                "specialize hentries x7",
                "apply hentries",
                "exact hlast_witness_left",
                "have hone_zero : 1 = 0",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x5",
                "specialize beta_at_unique x7",
                "specialize beta_at_unique 1",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact hlast_witness_right_left",
                "exact hzero",
                "exfalso",
                "apply PA1",
                "exact hone_zero",
            ),
            "An all-zero carry prefix forces the exact central valuation to zero.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_VALUATION_ZERO_TWO_THIRDS_RANGE,
            "forall p n C v. "
            f"({public_prime}) -> ({public_positive}) -> "
            f"({public_lower}) -> ({public_scaled}) -> "
            f"({public_central}) -> ({public_valuation}) -> v = 0",
            (
                "pow_exists",
                PRIME_SQUARE_TAIL_OF_TWO_THREE_RANGE,
                DIVISION_FIRST_TWO_OF_TWO_THREE_RANGE,
                "prime_nonzero",
                "one_le_of_ne_zero",
                CENTRAL_BINOM_PRIME_VALUATION_ZERO_OF_EXACT_DOUBLE_QUOTIENTS,
            ),
            (
                "intro p",
                "intro n",
                "intro C",
                "intro v",
                "intro hp",
                "intro hpositive",
                "intro hlower",
                "intro hscaled",
                "intro hcentral",
                "intro hvaluation",
                "have hsquare : exists s. " + public_square,
                "specialize pow_exists p",
                "specialize pow_exists 2",
                "exact pow_exists",
                "cases hsquare",
                f"have hstrict : {public_square_strict}",
                "specialize prime_square_tail_of_two_three_range p",
                "specialize prime_square_tail_of_two_three_range n",
                "specialize prime_square_tail_of_two_three_range x",
                "apply prime_square_tail_of_two_three_range",
                "exact hp",
                "exact hpositive",
                "exact hscaled",
                "exact hsquare_witness",
                "have hquotients : exists r R. "
                f"({first_result_left}) /\\ ({first_result_right})",
                "specialize division_first_two_of_two_three_range p",
                "specialize division_first_two_of_two_three_range n",
                "apply division_first_two_of_two_three_range",
                "exact hlower",
                "exact hscaled",
                "cases hquotients",
                "cases hquotients_witness",
                "cases hquotients_witness_witness",
                "have hp_nonzero : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hbase : {exact_base}",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp_nonzero",
                f"have hdouble_aligned : {public_double_aligned}",
                "have htwo : 2 = 1 + 1",
                "norm_num",
                "rewrite <- htwo",
                "exact hquotients_witness_witness_right",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients p",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients n",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients C",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients v",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients 1",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients x1",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients x2",
                "specialize "
                "central_binom_prime_valuation_zero_of_exact_double_quotients x",
                "apply "
                "central_binom_prime_valuation_zero_of_exact_double_quotients",
                "exact hp",
                "exact hcentral",
                "exact hvaluation",
                "exact hbase",
                "exact hsquare_witness",
                "exact hstrict",
                "exact hquotients_witness_witness_left",
                "exact hdouble_aligned",
            ),
            "Primes in the open two-thirds range contribute zero valuation.",
        ),
    )


__all__ = ["make_bertrand_central_binom_zero_range_candidate_theorems"]
