"""Square-tail valuation bound for the Bertrand B5 factor ranges.

The complete prime-power contribution to ``C(2*n,n)`` is already bounded
by ``2*n``.  If the square of the prime lies strictly above ``2*n``, an
exponent of at least two would force that contribution strictly above the
same bound.  This isolated factory records the constructive contradiction
and its discrete-order corollary that the valuation is at most one.

All notation expands to first-order Peano arithmetic before parsing.  Merely
importing this module registers no theorem and grants no theorem authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_power_valuation_candidate import _power_terms, power_valuation
from .fermat_residue_map_candidate import prime


CENTRAL_BINOM_PRIME_SQUARE_TAIL_EXPONENT_NOT_TWO_LE = (
    "central_binom_prime_square_tail_exponent_not_two_le"
)
CENTRAL_BINOM_PRIME_SQUARE_TAIL_VALUATION_LE_ONE = (
    "central_binom_prime_square_tail_valuation_le_one"
)


def make_bertrand_central_binom_square_tail_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered square-tail valuation rows."""

    variables = ("p", "n", "C", "v", "s")

    exclusion_prime = prime("p", tag="bcpsten_prime")
    exclusion_positive = _le_term(
        "1", "n", tag="bcpsten_positive", variables=variables
    )
    exclusion_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bcpsten_central",
        variables=variables,
    )
    exclusion_valuation = power_valuation(
        "p", "C", "v", tag="bcpsten_valuation"
    )
    exclusion_square = _power_terms(
        "p", "2", "s", tag="bcpsten_square"
    )
    exclusion_strict = _lt_term(
        "n + n", "s", tag="bcpsten_strict", variables=variables
    )
    exclusion_exponent = _le_term(
        "2", "v", tag="bcpsten_exponent", variables=variables
    )

    contribution_power = _power_terms(
        "p", "v", "D", tag="bcpsten_contribution_power"
    )
    prime_positive = _le_term(
        "1",
        "p",
        tag="bcpsten_prime_positive",
        variables=variables,
    )
    contribution_strict = _lt_term(
        "n + n",
        "x",
        tag="bcpsten_contribution_strict",
        variables=variables + ("x",),
    )
    contribution_bound = _le_term(
        "x",
        "n + n",
        tag="bcpsten_contribution_bound",
        variables=variables + ("x",),
    )

    result_prime = prime("p", tag="bcpstvlo_prime")
    result_positive = _le_term(
        "1", "n", tag="bcpstvlo_positive", variables=variables
    )
    result_central = _central_binom_relation_term(
        "n",
        "C",
        tag="bcpstvlo_central",
        variables=variables,
    )
    result_valuation = power_valuation(
        "p", "C", "v", tag="bcpstvlo_valuation"
    )
    result_square = _power_terms(
        "p", "2", "s", tag="bcpstvlo_square"
    )
    result_strict = _lt_term(
        "n + n", "s", tag="bcpstvlo_strict", variables=variables
    )
    result_bound = _le_term(
        "v", "1", tag="bcpstvlo_result", variables=variables
    )
    result_alternative = _lt_term(
        "1", "v", tag="bcpstvlo_alternative", variables=variables
    )

    return (
        spec(
            CENTRAL_BINOM_PRIME_SQUARE_TAIL_EXPONENT_NOT_TWO_LE,
            "forall p n C v s. "
            f"({exclusion_prime}) -> ({exclusion_positive}) -> "
            f"({exclusion_central}) -> ({exclusion_valuation}) -> "
            f"({exclusion_square}) -> ({exclusion_strict}) -> "
            f"~({exclusion_exponent})",
            (
                "pow_exists",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "pow_tail_strict_of_square",
                "central_binom_prime_power_contribution_le_double",
                "lt_not_le",
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
                "intro hsquare",
                "intro hstrict",
                "intro hexponent",
                f"have hpower_exists : exists D. ({contribution_power})",
                "specialize pow_exists p",
                "specialize pow_exists v",
                "exact pow_exists",
                "cases hpower_exists",
                "have hp_nonzero : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                f"have hp_positive : {prime_positive}",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp_nonzero",
                f"have htail : {contribution_strict}",
                "specialize pow_tail_strict_of_square p",
                "specialize pow_tail_strict_of_square v",
                "specialize pow_tail_strict_of_square x",
                "specialize pow_tail_strict_of_square s",
                "specialize pow_tail_strict_of_square (n + n)",
                "apply pow_tail_strict_of_square",
                "exact hp_positive",
                "exact hexponent",
                "exact hsquare",
                "exact hpower_exists_witness",
                "exact hstrict",
                f"have hbound : {contribution_bound}",
                "specialize "
                "central_binom_prime_power_contribution_le_double p",
                "specialize "
                "central_binom_prime_power_contribution_le_double n",
                "specialize "
                "central_binom_prime_power_contribution_le_double C",
                "specialize "
                "central_binom_prime_power_contribution_le_double v",
                "specialize "
                "central_binom_prime_power_contribution_le_double x",
                "apply central_binom_prime_power_contribution_le_double",
                "exact hp",
                "exact hpositive",
                "exact hcentral",
                "exact hvaluation",
                "exact hpower_exists_witness",
                "specialize lt_not_le (n + n)",
                "specialize lt_not_le x",
                "apply lt_not_le",
                "exact htail",
                "exact hbound",
            ),
            "A prime square above twice n rules out valuation exponent two.",
        ),
        spec(
            CENTRAL_BINOM_PRIME_SQUARE_TAIL_VALUATION_LE_ONE,
            "forall p n C v s. "
            f"({result_prime}) -> ({result_positive}) -> "
            f"({result_central}) -> ({result_valuation}) -> "
            f"({result_square}) -> ({result_strict}) -> "
            f"({result_bound})",
            (
                "le_or_lt",
                CENTRAL_BINOM_PRIME_SQUARE_TAIL_EXPONENT_NOT_TWO_LE,
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
                "intro hsquare",
                "intro hstrict",
                f"have horder : ({result_bound}) \\/ "
                f"({result_alternative})",
                "specialize le_or_lt v",
                "specialize le_or_lt 1",
                "exact le_or_lt",
                "cases horder",
                "exact horder_left",
                "exfalso",
                "specialize "
                "central_binom_prime_square_tail_exponent_not_two_le p",
                "specialize "
                "central_binom_prime_square_tail_exponent_not_two_le n",
                "specialize "
                "central_binom_prime_square_tail_exponent_not_two_le C",
                "specialize "
                "central_binom_prime_square_tail_exponent_not_two_le v",
                "specialize "
                "central_binom_prime_square_tail_exponent_not_two_le s",
                "apply "
                "central_binom_prime_square_tail_exponent_not_two_le",
                "exact hp",
                "exact hpositive",
                "exact hcentral",
                "exact hvaluation",
                "exact hsquare",
                "exact hstrict",
                "exact horder_right",
            ),
            "Above the square tail, a central-binomial valuation is at most one.",
        ),
    )


__all__ = [
    "make_bertrand_central_binom_square_tail_candidate_theorems",
]
