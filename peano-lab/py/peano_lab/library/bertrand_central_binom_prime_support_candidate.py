"""Prime-divisor support for the Bertrand central-binomial upper bound.

The two rows in this isolated candidate module establish the outer support
of the B5 five-range argument.  First, every prime divisor of ``C(2*n,n)``
is bounded by ``2*n`` through the checked factorial bridge.  Second, an
explicit ``NoBertrandClosed(n)`` certificate rules out the part above ``n``.

All notation is expanded into the unchanged Peano language.  The factory is
not enrolled in any library edition and grants no theorem-name authority.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_primorial_choose_interval_candidate import (
    _prime_relation_term,
)
from .bertrand_primorial_foundation_candidate import (
    _binders,
    _lt_term,
    _render_term,
    _validated_context,
)
from .bertrand_primorial_membership_candidate import _divides_term, _le_term
from .bertrand_power_valuation_candidate import (
    _power_divides_terms,
    _power_terms,
    power_valuation,
)
from .finite_factorial_theorems import factorial_relation


CENTRAL_BINOM_PRIME_DIVISOR_LE_DOUBLE = (
    "central_binom_prime_divisor_le_double"
)
NO_BERTRAND_CENTRAL_PRIME_DIVISOR_LE = (
    "no_bertrand_central_prime_divisor_le"
)
POWER_VALUATION_NONZERO_EXPONENT_DIVIDES_BASE = (
    "power_valuation_nonzero_exponent_divides_base"
)
PRIME_DIVISOR_POWER_VALUATION_NONZERO = (
    "prime_divisor_power_valuation_nonzero"
)
NO_BERTRAND_CENTRAL_PRIME_DIVISOR_RANGES = (
    "no_bertrand_central_prime_divisor_ranges"
)


def _factorial_relation_term(
    length: str,
    result: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand Factorial at a capture-checked possibly compound length."""

    context = _validated_context(variables)
    rendered_length = _render_term(
        length,
        label="central prime-support factorial length",
        context=context,
    )
    rendered_result = _render_term(
        result,
        label="central prime-support factorial result",
        context=context,
    )
    marker = "bcps_factorial_length_marker"
    if marker in context:
        raise ValueError("factorial marker captures a context variable")
    relation = factorial_relation(marker, rendered_result, tag=tag)
    if relation.count(marker) != 4:
        raise AssertionError("unexpected factorial length occurrence count")
    return relation.replace(marker, f"({rendered_length})")


def _no_bertrand_closed_term(
    index: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand the explicit absence certificate for ``(n,n+n]``."""

    context = _validated_context(variables)
    rendered_index = _render_term(
        index,
        label="no-Bertrand index",
        context=context,
    )
    (candidate,) = _binders(tag, context, ("prime_candidate",))
    local = context + (candidate,)
    lower = _lt_term(
        rendered_index,
        candidate,
        tag=f"{tag}_lower",
        avoid=local,
    )
    upper = _le_term(
        candidate,
        f"{rendered_index} + {rendered_index}",
        tag=f"{tag}_upper",
        variables=local,
    )
    primality = _prime_relation_term(
        candidate,
        tag=f"{tag}_prime",
        variables=local,
    )
    return (
        f"forall {candidate}. (({lower}) /\\ ({upper})) -> "
        f"~({primality})"
    )


def make_bertrand_central_binom_prime_support_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered B5 outer prime-support rows."""

    divisor_variables = ("n", "c", "p")
    divisor_prime = _prime_relation_term(
        "p",
        tag="bcpdl_prime",
        variables=divisor_variables,
    )
    divisor_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bcpdl_central",
        variables=divisor_variables,
    )
    divisor_source = _divides_term(
        "p",
        "c",
        tag="bcpdl_divides",
        variables=divisor_variables,
    )
    divisor_result = _le_term(
        "p",
        "n + n",
        tag="bcpdl_result",
        variables=divisor_variables,
    )
    total_factorial = _factorial_relation_term(
        "n + n",
        "F",
        tag="bcpdl_total_factorial",
        variables=divisor_variables + ("F",),
    )
    column_factorial = _factorial_relation_term(
        "n",
        "K",
        tag="bcpdl_column_factorial",
        variables=divisor_variables + ("K",),
    )
    central_divides_total = _divides_term(
        "c",
        "x",
        tag="bcpdl_central_divides_total",
        variables=divisor_variables + ("x", "x1"),
    )
    prime_divides_total = _divides_term(
        "p",
        "x",
        tag="bcpdl_prime_divides_total",
        variables=divisor_variables + ("x", "x1"),
    )

    no_bertrand_variables = ("n", "c", "p")
    no_bertrand = _no_bertrand_closed_term(
        "n",
        tag="bnbcpdl_exclusion",
        variables=no_bertrand_variables,
    )
    no_bertrand_prime = _prime_relation_term(
        "p",
        tag="bnbcpdl_prime",
        variables=no_bertrand_variables,
    )
    no_bertrand_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bnbcpdl_central",
        variables=no_bertrand_variables,
    )
    no_bertrand_divides = _divides_term(
        "p",
        "c",
        tag="bnbcpdl_divides",
        variables=no_bertrand_variables,
    )
    no_bertrand_result = _le_term(
        "p",
        "n",
        tag="bnbcpdl_result",
        variables=no_bertrand_variables,
    )

    valuation_variables = ("p", "c", "e")
    valuation_source = power_valuation(
        "p",
        "c",
        "e",
        tag="bpvnedb_source",
    )
    valuation_result = _divides_term(
        "p",
        "c",
        tag="bpvnedb_result",
        variables=valuation_variables,
    )
    valuation_selected = _power_divides_terms(
        "p",
        "e",
        "c",
        tag="bpvnedb_selected",
    )
    valuation_unit = _power_divides_terms(
        "p",
        "1",
        "c",
        tag="bpvnedb_unit",
    )
    valuation_one_bound = _le_term(
        "1",
        "e",
        tag="bpvnedb_one_bound",
        variables=valuation_variables,
    )

    divisor_valuation_variables = ("p", "c", "e")
    divisor_valuation_prime = _prime_relation_term(
        "p",
        tag="bpdvpn_prime",
        variables=divisor_valuation_variables,
    )
    divisor_valuation_source = power_valuation(
        "p",
        "c",
        "e",
        tag="bpdvpn_source",
    )
    divisor_valuation_divides = _divides_term(
        "p",
        "c",
        tag="bpdvpn_divides",
        variables=divisor_valuation_variables,
    )
    divisor_valuation_power = _power_terms(
        "p",
        "1",
        "x",
        tag="bpdvpn_unit_power",
    )
    divisor_valuation_power_divides = _power_divides_terms(
        "p",
        "1",
        "c",
        tag="bpdvpn_unit_divides",
    )
    divisor_valuation_bound = _le_term(
        "1",
        "e",
        tag="bpdvpn_bound",
        variables=divisor_valuation_variables,
    )

    range_variables = ("n", "s", "q", "c", "p")
    range_exclusion = _no_bertrand_closed_term(
        "n",
        tag="bnbcpdr_exclusion",
        variables=range_variables,
    )
    range_prime = _prime_relation_term(
        "p",
        tag="bnbcpdr_prime",
        variables=range_variables,
    )
    range_central = _central_binom_relation_term(
        "n",
        "c",
        tag="bnbcpdr_central",
        variables=range_variables,
    )
    range_divides = _divides_term(
        "p",
        "c",
        tag="bnbcpdr_divides",
        variables=range_variables,
    )
    range_small = _le_term(
        "p",
        "s",
        tag="bnbcpdr_small",
        variables=range_variables,
    )
    range_above_small = _lt_term(
        "s",
        "p",
        tag="bnbcpdr_above_small",
        avoid=range_variables,
    )
    range_middle_bound = _le_term(
        "p",
        "q",
        tag="bnbcpdr_middle_bound",
        variables=range_variables,
    )
    range_above_middle = _lt_term(
        "q",
        "p",
        tag="bnbcpdr_above_middle",
        avoid=range_variables,
    )
    range_row_bound = _le_term(
        "p",
        "n",
        tag="bnbcpdr_row_bound",
        variables=range_variables,
    )

    return (
        spec(
            CENTRAL_BINOM_PRIME_DIVISOR_LE_DOUBLE,
            "forall n c p. "
            f"({divisor_prime}) -> ({divisor_central}) -> "
            f"({divisor_source}) -> ({divisor_result})",
            (
                "factorial_exists",
                "choose_factorial_bridge",
                "mul_comm",
                "multiple_trans",
                "factorial_prime_le_of_divides",
            ),
            (
                "intro n",
                "intro c",
                "intro p",
                "intro hp",
                "intro hcentral",
                "intro hdivides",
                f"have hF : exists F. ({total_factorial})",
                "specialize factorial_exists (n + n)",
                "exact factorial_exists",
                "cases hF",
                f"have hK : exists K. ({column_factorial})",
                "specialize factorial_exists n",
                "exact factorial_exists",
                "cases hK",
                "have hbridge : x = (x1 * x1) * c",
                "specialize choose_factorial_bridge (n + n)",
                "specialize choose_factorial_bridge n",
                "specialize choose_factorial_bridge n",
                "specialize choose_factorial_bridge c",
                "specialize choose_factorial_bridge x",
                "specialize choose_factorial_bridge x1",
                "specialize choose_factorial_bridge x1",
                "apply choose_factorial_bridge",
                "refl",
                "exact hcentral",
                "exact hF_witness",
                "exact hK_witness",
                "exact hK_witness",
                f"have hcentral_factor : {central_divides_total}",
                "exists (x1 * x1)",
                "trans (x1 * x1) * c",
                "exact hbridge",
                "apply mul_comm",
                f"have hprime_factor : {prime_divides_total}",
                "specialize multiple_trans c",
                "specialize multiple_trans p",
                "specialize multiple_trans x",
                "apply multiple_trans",
                "exact hcentral_factor",
                "exact hdivides",
                "specialize factorial_prime_le_of_divides p",
                "specialize factorial_prime_le_of_divides (n + n)",
                "specialize factorial_prime_le_of_divides x",
                "apply factorial_prime_le_of_divides",
                "exact hp",
                "exact hF_witness",
                "exact hprime_factor",
            ),
            "Every prime divisor of a central coefficient is at most 2*n.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_PRIME_DIVISOR_LE,
            "forall n c p. "
            f"({no_bertrand}) -> ({no_bertrand_prime}) -> "
            f"({no_bertrand_central}) -> ({no_bertrand_divides}) -> "
            f"({no_bertrand_result})",
            (
                "le_total",
                "le_eq_or_lt",
                "le_refl",
                CENTRAL_BINOM_PRIME_DIVISOR_LE_DOUBLE,
            ),
            (
                "intro n",
                "intro c",
                "intro p",
                "intro hfree",
                "intro hp",
                "intro hcentral",
                "intro hdivides",
                "specialize le_total p",
                "specialize le_total n",
                "cases le_total",
                "exact le_total_left",
                "specialize le_eq_or_lt n",
                "specialize le_eq_or_lt p",
                "have hcases : n = p \\/ exists gap. gap + S n = p",
                "apply le_eq_or_lt",
                "exact le_total_right",
                "cases hcases",
                "rewrite hcases_left",
                "specialize le_refl p",
                "exact le_refl",
                "have hdouble : exists gap. gap + p = n + n",
                "specialize central_binom_prime_divisor_le_double n",
                "specialize central_binom_prime_divisor_le_double c",
                "specialize central_binom_prime_divisor_le_double p",
                "apply central_binom_prime_divisor_le_double",
                "exact hp",
                "exact hcentral",
                "exact hdivides",
                "specialize hfree p",
                "exfalso",
                "apply hfree",
                "split",
                "exact hcases_right",
                "exact hdouble",
                "exact hp",
            ),
            "A no-Bertrand certificate forces central prime divisors below n.",
        ),
        spec(
            POWER_VALUATION_NONZERO_EXPONENT_DIVIDES_BASE,
            "forall p c e. "
            f"({valuation_source}) -> ~(e = 0) -> ({valuation_result})",
            (
                "one_le_of_ne_zero",
                "power_valuation_power_divides",
                "power_divides_exponent_antitone",
                "pow_one",
            ),
            (
                "intro p",
                "intro c",
                "intro e",
                "intro hvaluation",
                "intro hexponent",
                f"have hone : {valuation_one_bound}",
                "specialize one_le_of_ne_zero e",
                "apply one_le_of_ne_zero",
                "exact hexponent",
                f"have hselected : {valuation_selected}",
                "specialize power_valuation_power_divides p",
                "specialize power_valuation_power_divides c",
                "specialize power_valuation_power_divides e",
                "apply power_valuation_power_divides",
                "exact hvaluation",
                f"have hunit : {valuation_unit}",
                "specialize power_divides_exponent_antitone p",
                "specialize power_divides_exponent_antitone 1",
                "specialize power_divides_exponent_antitone e",
                "specialize power_divides_exponent_antitone c",
                "apply power_divides_exponent_antitone",
                "exact hone",
                "exact hselected",
                "cases hunit",
                "cases hunit_witness",
                "have hvalue : x = p",
                "specialize pow_one p",
                "specialize pow_one 1",
                "specialize pow_one x",
                "apply pow_one",
                "refl",
                "exact hunit_witness_left",
                "rewrite hvalue at hunit_witness_right",
                "exact hunit_witness_right",
            ),
            "A nonzero valuation exponent exposes the base as a divisor.",
        ),
        spec(
            PRIME_DIVISOR_POWER_VALUATION_NONZERO,
            "forall p c e. "
            f"({divisor_valuation_prime}) -> ~(c = 0) -> "
            f"({divisor_valuation_source}) -> "
            f"({divisor_valuation_divides}) -> ~(e = 0)",
            (
                "pow_exists",
                "pow_one",
                "prime_power_divides_exponent_le_valuation",
                "le_zero",
            ),
            (
                "intro p",
                "intro c",
                "intro e",
                "intro hp",
                "intro hc",
                "intro hvaluation",
                "intro hdivides",
                f"have hpower : exists x. ({divisor_valuation_power})",
                "specialize pow_exists p",
                "specialize pow_exists 1",
                "exact pow_exists",
                "cases hpower",
                "have hvalue : x = p",
                "specialize pow_one p",
                "specialize pow_one 1",
                "specialize pow_one x",
                "apply pow_one",
                "refl",
                "exact hpower_witness",
                f"have hunit : {divisor_valuation_power_divides}",
                "exists x",
                "split",
                "exact hpower_witness",
                "rewrite hvalue",
                "exact hdivides",
                f"have hbound : {divisor_valuation_bound}",
                "specialize prime_power_divides_exponent_le_valuation p",
                "specialize prime_power_divides_exponent_le_valuation c",
                "specialize prime_power_divides_exponent_le_valuation e",
                "specialize prime_power_divides_exponent_le_valuation 1",
                "apply prime_power_divides_exponent_le_valuation",
                "exact hp",
                "exact hc",
                "exact hvaluation",
                "exact hunit",
                "intro heq",
                "rewrite heq at hbound",
                "have hone_zero : 1 = 0",
                "specialize le_zero 1",
                "apply le_zero",
                "exact hbound",
                "apply PA1",
                "exact hone_zero",
            ),
            "A prime divisor forces its canonical valuation exponent nonzero.",
        ),
        spec(
            NO_BERTRAND_CENTRAL_PRIME_DIVISOR_RANGES,
            "forall n s q c p. "
            f"({range_exclusion}) -> ({range_prime}) -> "
            f"({range_central}) -> ({range_divides}) -> "
            f"(({range_small}) \\/ "
            f"((({range_above_small}) /\\ ({range_middle_bound})) \\/ "
            f"(({range_above_middle}) /\\ ({range_row_bound}))))",
            (
                "le_total",
                "le_eq_or_lt",
                "le_refl",
                NO_BERTRAND_CENTRAL_PRIME_DIVISOR_LE,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro c",
                "intro p",
                "intro hfree",
                "intro hp",
                "intro hcentral",
                "intro hdivides",
                f"have hrow : {range_row_bound}",
                "specialize no_bertrand_central_prime_divisor_le n",
                "specialize no_bertrand_central_prime_divisor_le c",
                "specialize no_bertrand_central_prime_divisor_le p",
                "apply no_bertrand_central_prime_divisor_le",
                "exact hfree",
                "exact hp",
                "exact hcentral",
                "exact hdivides",
                "have hps : (exists a. a + p = s) \\/ exists b. b + s = p",
                "specialize le_total p",
                "specialize le_total s",
                "exact le_total",
                "cases hps",
                "left",
                "exact hps_left",
                "have hsmall_cases : s = p \\/ exists g. g + S s = p",
                "specialize le_eq_or_lt s",
                "specialize le_eq_or_lt p",
                "apply le_eq_or_lt",
                "exact hps_right",
                "cases hsmall_cases",
                "left",
                "rewrite hsmall_cases_left",
                "specialize le_refl p",
                "exact le_refl",
                "have hpq : (exists a. a + p = q) \\/ exists b. b + q = p",
                "specialize le_total p",
                "specialize le_total q",
                "exact le_total",
                "cases hpq",
                "right",
                "left",
                "split",
                "exact hsmall_cases_right",
                "exact hpq_left",
                "have hmiddle_cases : q = p \\/ exists g. g + S q = p",
                "specialize le_eq_or_lt q",
                "specialize le_eq_or_lt p",
                "apply le_eq_or_lt",
                "exact hpq_right",
                "cases hmiddle_cases",
                "right",
                "left",
                "split",
                "exact hsmall_cases_right",
                "rewrite hmiddle_cases_left",
                "specialize le_refl p",
                "exact le_refl",
                "right",
                "right",
                "split",
                "exact hmiddle_cases_right",
                "exact hrow",
            ),
            "Every central prime divisor lies in one of the three live ranges.",
        ),
    )


__all__ = ["make_bertrand_central_binom_prime_support_candidate_theorems"]
