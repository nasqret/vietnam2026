"""Constructive valuation and quotient-prefix bridges for Bertrand B5.

This isolated factory connects the checked factorial identity for the central
binomial coefficient to prime-power valuations and finite Legendre sums.  It
also records the zero-tail and pointwise doubling facts needed to compare the
two quotient prefixes extensionally.  All notation expands to the unchanged
first-order Peano language; this module is deliberately unregistered.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_prime_support_candidate import (
    _factorial_relation_term,
)
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_factorial_valuation_candidate import factorial_valuation
from .bertrand_legendre_sum_candidate import (
    _power_quotient_prefix_terms,
    legendre_sum,
)
from .bertrand_power_valuation_candidate import (
    _power_terms,
    power_valuation,
)
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import sum_relation
from .finite_sum_theorems import _at, _sum_relation_terms


POWER_VALUATION_VALUE_EQ_TRANSPORT = "power_valuation_value_eq_transport"
CENTRAL_FACTORIAL_VALUATION_BALANCE = (
    "central_binom_factorial_valuation_balance"
)
CENTRAL_LEGENDRE_VALUATION_BALANCE = (
    "central_binom_legendre_valuation_balance"
)
PRIME_POWER_QUOTIENT_ZERO_OF_EXPONENT_GT = (
    "prime_power_quotient_zero_of_exponent_gt"
)
POWER_QUOTIENT_PREFIX_TAIL_ENTRY_ZERO = (
    "power_quotient_prefix_tail_entry_zero"
)
POWER_QUOTIENT_PREFIX_SUM_EXTEND_ZERO = (
    "power_quotient_prefix_sum_extend_zero"
)
LEGENDRE_SUM_EXTENDED_PREFIX_EXISTS = (
    "legendre_sum_extended_prefix_exists"
)
POWER_QUOTIENT_DOUBLE_POINTWISE_UPPER = (
    "power_quotient_double_pointwise_upper"
)
BETA_SUM_POINTWISE_DOUBLE_SUCC_LE = (
    "beta_sum_pointwise_double_succ_le"
)
CENTRAL_PRIME_VALUATION_LE_DOUBLE = (
    "central_binom_prime_valuation_le_double"
)


def _power_valuation_term(
    base: str,
    value: str,
    exponent: str,
    *,
    tag: str,
) -> str:
    """Expand ``PowerVal`` at one factory-owned compound value."""

    marker = f"b5cv_value_marker_{tag}"
    expanded = power_valuation(base, marker, exponent, tag=tag)
    if expanded.count(marker) != 4:
        raise AssertionError("unexpected PowerVal value occurrence count")
    return expanded.replace(marker, f"({value})")


def _factorial_valuation_term(
    base: str,
    length: str,
    exponent: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand ``FactorialVal`` at one possibly compound length."""

    value = f"b5cv_factorial_{tag}"
    if value in variables:
        raise ValueError("factorial-valuation binder captures a variable")
    factorial = _factorial_relation_term(
        length,
        value,
        tag=f"{tag}_factorial",
        variables=variables + (value,),
    )
    valuation = power_valuation(
        base,
        value,
        exponent,
        tag=f"{tag}_valuation",
    )
    return f"exists {value}. (({factorial}) /\\ ({valuation}))"


def _legendre_sum_term(
    base: str,
    value: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``LegendreSum`` at one factory-owned compound dividend."""

    marker = f"b5cv_legendre_marker_{tag}"
    expanded = legendre_sum(base, marker, result, tag=tag)
    if expanded.count(marker) < 2:
        raise AssertionError("unexpected Legendre dividend occurrence count")
    return expanded.replace(marker, f"({value})")


def _sum_double_pointwise(
    length: str,
    *,
    tag: str,
    left_code: str = "b",
    left_scale: str = "c",
    right_code: str = "d",
    right_scale: str = "e",
) -> str:
    variables = (
        left_code,
        left_scale,
        right_code,
        right_scale,
        "l",
        "B",
        "A",
        "i",
        "q",
        "Q",
    )
    bound = _lt_term(
        "i",
        length,
        tag=f"{tag}_bound",
        variables=variables,
    )
    left = _at(
        left_code,
        left_scale,
        "i",
        "q",
        tag=f"{tag}_left",
    )
    right = _at(
        right_code,
        right_scale,
        "i",
        "Q",
        tag=f"{tag}_right",
    )
    result = _le_term(
        "Q",
        "S (q + q)",
        tag=f"{tag}_result",
        variables=variables,
    )
    return (
        f"forall i q Q. ({bound}) -> ({left}) -> ({right}) -> ({result})"
    )


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = _at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = _sum_relation_terms(
        code,
        scale,
        length,
        "r",
        tag=f"{tag}_prefix",
    )
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_bertrand_central_binom_valuation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered central-valuation bridge tranche."""

    transport_source = power_valuation(
        "p", "a", "e", tag="b5cvvet_source"
    )
    transport_target = power_valuation(
        "p", "b", "e", tag="b5cvvet_target"
    )

    balance_variables = ("p", "n", "c", "e", "A", "B")
    balance_prime = prime("p", tag="b5cvfb_prime")
    balance_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvfb_central",
        variables=balance_variables,
    )
    balance_value = power_valuation(
        "p", "c", "e", tag="b5cvfb_value"
    )
    balance_total = _factorial_valuation_term(
        "p",
        "n + n",
        "A",
        tag="b5cvfb_total",
        variables=balance_variables,
    )
    balance_column = factorial_valuation(
        "p", "n", "B", tag="b5cvfb_column"
    )

    legendre_prime = prime("p", tag="b5cvlb_prime")
    legendre_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvlb_central",
        variables=balance_variables,
    )
    legendre_value = power_valuation(
        "p", "c", "e", tag="b5cvlb_value"
    )
    legendre_total = _legendre_sum_term(
        "p", "n + n", "A", tag="b5cvlb_total"
    )
    legendre_column = legendre_sum(
        "p", "n", "B", tag="b5cvlb_column"
    )

    quotient_variables = ("p", "n", "e", "d", "q", "r")
    quotient_prime = prime("p", tag="b5cvqz_prime")
    quotient_exponent = _lt_term(
        "n",
        "e",
        tag="b5cvqz_exponent",
        variables=quotient_variables,
    )
    quotient_power = _power_terms(
        "p", "e", "d", tag="b5cvqz_power"
    )
    quotient_division = _divrem_term(
        "d",
        "n",
        "q",
        "r",
        tag="b5cvqz_division",
        variables=quotient_variables,
    )

    tail_variables = ("p", "n", "b", "c", "l", "i")
    tail_prime = prime("p", tag="b5cvptez_prime")
    tail_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5cvptez_prefix"
    )
    tail_start = _le_term(
        "n",
        "i",
        tag="b5cvptez_start",
        variables=tail_variables,
    )
    tail_bound = _lt_term(
        "i",
        "l",
        tag="b5cvptez_bound",
        variables=tail_variables,
    )
    tail_result = _at(
        "b", "c", "i", "0", tag="b5cvptez_result"
    )

    extension_variables = ("p", "n", "b", "c", "g", "t", "e")
    extension_prime = prime("p", tag="b5cvpsez_prime")
    extension_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "n + g", tag="b5cvpsez_prefix"
    )
    extension_sum = _sum_relation_terms(
        "b", "c", "n + g", "t", tag="b5cvpsez_sum"
    )
    extension_legendre = legendre_sum(
        "p", "n", "e", tag="b5cvpsez_legendre"
    )

    extended_exists_prime = prime("p", tag="b5cvlsepe_prime")
    extended_exists_legendre = legendre_sum(
        "p", "n", "e", tag="b5cvlsepe_legendre"
    )
    extended_exists_prefix = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "n + g", tag="b5cvlsepe_prefix"
    )
    extended_exists_sum = _sum_relation_terms(
        "b", "c", "n + g", "e", tag="b5cvlsepe_sum"
    )

    pointwise_variables = ("p", "n", "b", "c", "d", "e", "l")
    pointwise_left = _power_quotient_prefix_terms(
        "p", "n", "b", "c", "l", tag="b5cvpdpu_left"
    )
    pointwise_right = _power_quotient_prefix_terms(
        "p", "n + n", "d", "e", "l", tag="b5cvpdpu_right"
    )
    pointwise_result = _sum_double_pointwise(
        "l", tag="b5cvpdpu_result"
    )

    fold_left = sum_relation("b", "c", "l", "B", tag="b5cvbsdsl_left")
    fold_right = sum_relation(
        "d", "e", "l", "A", tag="b5cvbsdsl_right"
    )
    fold_pointwise = _sum_double_pointwise(
        "l", tag="b5cvbsdsl_pointwise"
    )
    fold_result = _le_term(
        "A",
        "(B + B) + l",
        tag="b5cvbsdsl_result",
        variables=("b", "c", "d", "e", "l", "B", "A"),
    )

    final_variables = ("p", "n", "c", "e")
    final_prime = prime("p", tag="b5cvpvd_prime")
    final_central = _central_binom_relation_term(
        "n",
        "c",
        tag="b5cvpvd_central",
        variables=final_variables,
    )
    final_valuation = power_valuation(
        "p", "c", "e", tag="b5cvpvd_valuation"
    )
    final_result = _le_term(
        "e",
        "n + n",
        tag="b5cvpvd_result",
        variables=final_variables,
    )

    return (
        spec(
            POWER_VALUATION_VALUE_EQ_TRANSPORT,
            "forall p a b e. a = b -> "
            f"({transport_source}) -> ({transport_target})",
            (),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro e",
                "intro hvalue",
                "intro hsource",
                "rewrite hvalue at hsource",
                "rewrite hvalue at hsource",
                "rewrite hvalue at hsource",
                "rewrite hvalue at hsource",
                "exact hsource",
            ),
            "Power valuation transports along equality of its valued number.",
        ),
        spec(
            CENTRAL_FACTORIAL_VALUATION_BALANCE,
            "forall p n c e A B. "
            f"({balance_prime}) -> ({balance_central}) -> "
            f"({balance_value}) -> ({balance_total}) -> "
            f"({balance_column}) -> A = (B + B) + e",
            (
                "central_binom_positive",
                "factorial_nonzero",
                "choose_factorial_bridge",
                "power_valuation_exists",
                POWER_VALUATION_VALUE_EQ_TRANSPORT,
                "prime_power_valuation_mul",
                "mul_ne_zero",
            ),
            (
                "intro p",
                "intro n",
                "intro c",
                "intro e",
                "intro A",
                "intro B",
                "intro hp",
                "intro hcentral",
                "intro hvalue",
                "intro htotal",
                "intro hcolumn",
                "cases htotal",
                "cases htotal_witness",
                "cases hcolumn",
                "cases hcolumn_witness",
                "have hc_positive : exists r. c = S r",
                "specialize central_binom_positive n",
                "specialize central_binom_positive c",
                "apply central_binom_positive",
                "exact hcentral",
                "cases hc_positive",
                "have hc_nonzero : ~(c = 0)",
                "intro hc_zero",
                "apply PA1",
                "trans c",
                "symm",
                "exact hc_positive_witness",
                "exact hc_zero",
                "have htotal_nonzero : ~(x = 0)",
                "intro htotal_zero",
                "specialize factorial_nonzero (n + n)",
                "specialize factorial_nonzero x",
                "apply factorial_nonzero",
                "exact htotal_witness_left",
                "exact htotal_zero",
                "have hcolumn_nonzero : ~(x1 = 0)",
                "intro hcolumn_zero",
                "specialize factorial_nonzero n",
                "specialize factorial_nonzero x1",
                "apply factorial_nonzero",
                "exact hcolumn_witness_left",
                "exact hcolumn_zero",
                "have hpair_nonzero : ~(x1 * x1 = 0)",
                "intro hpair_zero",
                "specialize mul_ne_zero x1",
                "specialize mul_ne_zero x1",
                "apply mul_ne_zero",
                "exact hcolumn_nonzero",
                "exact hcolumn_nonzero",
                "exact hpair_zero",
                "have hpair_valuation : exists g. "
                + _power_valuation_term(
                    "p", "x1 * x1", "g", tag="b5cvfb_pair"
                ),
                "specialize power_valuation_exists p",
                "specialize power_valuation_exists (x1 * x1)",
                "exact power_valuation_exists",
                "cases hpair_valuation",
                "have hpair_exponent : x3 = B + B",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul x1",
                "specialize prime_power_valuation_mul x1",
                "specialize prime_power_valuation_mul B",
                "specialize prime_power_valuation_mul B",
                "specialize prime_power_valuation_mul x3",
                "apply prime_power_valuation_mul",
                "exact hp",
                "exact hcolumn_nonzero",
                "exact hcolumn_nonzero",
                "exact hcolumn_witness_right",
                "exact hcolumn_witness_right",
                "exact hpair_valuation_witness",
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
                "exact htotal_witness_left",
                "exact hcolumn_witness_left",
                "exact hcolumn_witness_left",
                "have hproduct_valuation : "
                + _power_valuation_term(
                    "p", "(x1 * x1) * c", "A", tag="b5cvfb_product"
                ),
                "specialize power_valuation_value_eq_transport p",
                "specialize power_valuation_value_eq_transport x",
                "specialize power_valuation_value_eq_transport ((x1 * x1) * c)",
                "specialize power_valuation_value_eq_transport A",
                "apply power_valuation_value_eq_transport",
                "exact hbridge",
                "exact htotal_witness_right",
                "have htotal_exponent : A = x3 + e",
                "specialize prime_power_valuation_mul p",
                "specialize prime_power_valuation_mul (x1 * x1)",
                "specialize prime_power_valuation_mul c",
                "specialize prime_power_valuation_mul x3",
                "specialize prime_power_valuation_mul e",
                "specialize prime_power_valuation_mul A",
                "apply prime_power_valuation_mul",
                "exact hp",
                "exact hpair_nonzero",
                "exact hc_nonzero",
                "exact hpair_valuation_witness",
                "exact hvalue",
                "exact hproduct_valuation",
                "trans x3 + e",
                "exact htotal_exponent",
                "rewrite hpair_exponent",
                "refl",
            ),
            "The central valuation is the doubled-column factorial deficit.",
        ),
        spec(
            CENTRAL_LEGENDRE_VALUATION_BALANCE,
            "forall p n c e A B. "
            f"({legendre_prime}) -> ({legendre_central}) -> "
            f"({legendre_value}) -> ({legendre_total}) -> "
            f"({legendre_column}) -> A = (B + B) + e",
            (
                "factorial_valuation_exists",
                "prime_factorial_valuation_eq_legendre_sum",
                CENTRAL_FACTORIAL_VALUATION_BALANCE,
            ),
            (
                "intro p",
                "intro n",
                "intro c",
                "intro e",
                "intro A",
                "intro B",
                "intro hp",
                "intro hcentral",
                "intro hvalue",
                "intro htotal_legendre",
                "intro hcolumn_legendre",
                "have htotal : exists a. "
                + _factorial_valuation_term(
                    "p",
                    "n + n",
                    "a",
                    tag="b5cvlb_total_factorial",
                    variables=balance_variables + ("a",),
                ),
                "specialize factorial_valuation_exists p",
                "specialize factorial_valuation_exists (n + n)",
                "exact factorial_valuation_exists",
                "cases htotal",
                "have hcolumn : exists b. "
                + factorial_valuation(
                    "p", "n", "b", tag="b5cvlb_column_factorial"
                ),
                "specialize factorial_valuation_exists p",
                "specialize factorial_valuation_exists n",
                "exact factorial_valuation_exists",
                "cases hcolumn",
                "have hbalance : x = (x1 + x1) + e",
                "specialize central_binom_factorial_valuation_balance p",
                "specialize central_binom_factorial_valuation_balance n",
                "specialize central_binom_factorial_valuation_balance c",
                "specialize central_binom_factorial_valuation_balance e",
                "specialize central_binom_factorial_valuation_balance x",
                "specialize central_binom_factorial_valuation_balance x1",
                "apply central_binom_factorial_valuation_balance",
                "exact hp",
                "exact hcentral",
                "exact hvalue",
                "exact htotal_witness",
                "exact hcolumn_witness",
                "have htotal_eq : x = A",
                "specialize prime_factorial_valuation_eq_legendre_sum p",
                "specialize prime_factorial_valuation_eq_legendre_sum (n + n)",
                "specialize prime_factorial_valuation_eq_legendre_sum x",
                "specialize prime_factorial_valuation_eq_legendre_sum A",
                "apply prime_factorial_valuation_eq_legendre_sum",
                "exact hp",
                "exact htotal_witness",
                "exact htotal_legendre",
                "have hcolumn_eq : x1 = B",
                "specialize prime_factorial_valuation_eq_legendre_sum p",
                "specialize prime_factorial_valuation_eq_legendre_sum n",
                "specialize prime_factorial_valuation_eq_legendre_sum x1",
                "specialize prime_factorial_valuation_eq_legendre_sum B",
                "apply prime_factorial_valuation_eq_legendre_sum",
                "exact hp",
                "exact hcolumn_witness",
                "exact hcolumn_legendre",
                "trans x",
                "symm",
                "exact htotal_eq",
                "trans (x1 + x1) + e",
                "exact hbalance",
                "rewrite hcolumn_eq",
                "rewrite hcolumn_eq",
                "refl",
            ),
            "Factorial Legendre equality exposes the central carry balance.",
        ),
        spec(
            PRIME_POWER_QUOTIENT_ZERO_OF_EXPONENT_GT,
            "forall p n e d q r. "
            f"({quotient_prime}) -> ({quotient_exponent}) -> "
            f"({quotient_power}) -> ({quotient_division}) -> q = 0",
            (
                "prime_power_exponent_le",
                "lt_of_lt_of_le",
                "division_zero_quotient_of_lt",
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro d",
                "intro q",
                "intro r",
                "intro hp",
                "intro hexponent",
                "intro hpower",
                "intro hdivision",
                "have hpower_bound : exists g. g + e = d",
                "specialize prime_power_exponent_le p",
                "specialize prime_power_exponent_le e",
                "specialize prime_power_exponent_le d",
                "apply prime_power_exponent_le",
                "exact hp",
                "exact hpower",
                "have hvalue_bound : exists g. g + S n = d",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le e",
                "specialize lt_of_lt_of_le d",
                "apply lt_of_lt_of_le",
                "exact hexponent",
                "exact hpower_bound",
                "specialize division_zero_quotient_of_lt d",
                "specialize division_zero_quotient_of_lt n",
                "specialize division_zero_quotient_of_lt q",
                "specialize division_zero_quotient_of_lt r",
                "apply division_zero_quotient_of_lt",
                "exact hdivision",
                "exact hvalue_bound",
            ),
            "A prime-power quotient vanishes once its exponent exceeds the dividend.",
        ),
        spec(
            POWER_QUOTIENT_PREFIX_TAIL_ENTRY_ZERO,
            "forall p n b c l i. "
            f"({tail_prime}) -> ({tail_prefix}) -> ({tail_start}) -> "
            f"({tail_bound}) -> ({tail_result})",
            (PRIME_POWER_QUOTIENT_ZERO_OF_EXPONENT_GT,),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro hp",
                "intro hprefix",
                "intro hstart",
                "intro hibound",
                "have hdata : exists d q r. "
                f"({_power_terms('p', 'S i', 'd', tag='b5cvptez_data_power')}) /\\ "
                f"(({_at('b', 'c', 'i', 'q', tag='b5cvptez_data_entry')}) /\\ "
                + "("
                + _divrem_term(
                    "d",
                    "n",
                    "q",
                    "r",
                    tag="b5cvptez_data_division",
                    variables=tail_variables + ("d", "q", "r"),
                )
                + "))",
                "specialize hprefix i",
                "apply hprefix",
                "exact hibound",
                "cases hdata",
                "cases hdata_witness",
                "cases hdata_witness_witness",
                "cases hdata_witness_witness_witness",
                "cases hdata_witness_witness_witness_right",
                "have hexponent : exists g. g + S n = S i",
                "cases hstart",
                "exists x3",
                "rewrite PA4",
                "congr",
                "exact hstart_witness",
                "have hzero : x1 = 0",
                "specialize prime_power_quotient_zero_of_exponent_gt p",
                "specialize prime_power_quotient_zero_of_exponent_gt n",
                "specialize prime_power_quotient_zero_of_exponent_gt (S i)",
                "specialize prime_power_quotient_zero_of_exponent_gt x",
                "specialize prime_power_quotient_zero_of_exponent_gt x1",
                "specialize prime_power_quotient_zero_of_exponent_gt x2",
                "apply prime_power_quotient_zero_of_exponent_gt",
                "exact hp",
                "exact hexponent",
                "exact hdata_witness_witness_witness_left",
                "exact hdata_witness_witness_witness_right_right",
                "rewrite <- hzero",
                "rewrite <- hzero",
                "exact hdata_witness_witness_witness_right_left",
            ),
            "Every decoded quotient entry at or beyond the dividend is zero.",
        ),
        spec(
            POWER_QUOTIENT_PREFIX_SUM_EXTEND_ZERO,
            "forall p n b c g t e. "
            f"({extension_prime}) -> ({extension_prefix}) -> "
            f"({extension_sum}) -> ({extension_legendre}) -> t = e",
            (
                "legendre_sum_functional",
                "le_succ",
                "add_comm",
                "zero_add",
                "beta_sum_succ_last_zero",
                POWER_QUOTIENT_PREFIX_TAIL_ENTRY_ZERO,
            ),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "induction g",
                "intro t",
                "intro e",
                "intro hp",
                "intro hprefix",
                "intro hsum",
                "intro hlegendre",
                "have hbase_length : n + 0 = n",
                "apply PA3",
                "rewrite hbase_length at hprefix",
                "rewrite hbase_length at hsum",
                "rewrite hbase_length at hsum",
                "rewrite hbase_length at hsum",
                "have hcompeting : "
                + legendre_sum("p", "n", "t", tag="b5cvpsez_base"),
                "exists b",
                "exists c",
                "split",
                "exact hprefix",
                "exact hsum",
                "specialize legendre_sum_functional p",
                "specialize legendre_sum_functional n",
                "specialize legendre_sum_functional t",
                "specialize legendre_sum_functional e",
                "apply legendre_sum_functional",
                "exact hcompeting",
                "exact hlegendre",
                "intro t",
                "intro e",
                "intro hp",
                "intro hprefix",
                "intro hsum",
                "intro hlegendre",
                "have hstep_length : n + S g = S (n + g)",
                "apply PA4",
                "have hrestricted : "
                + _power_quotient_prefix_terms(
                    "p",
                    "n",
                    "b",
                    "c",
                    "n + g",
                    tag="b5cvpsez_restricted",
                ),
                "intro i",
                "intro hi",
                "specialize hprefix i",
                "apply hprefix",
                "rewrite hstep_length",
                "specialize le_succ (S i)",
                "specialize le_succ (n + g)",
                "apply le_succ",
                "exact hi",
                "have htail_start : exists k. k + n = n + g",
                "exists g",
                "apply add_comm",
                "have htail_bound : exists k. k + S (n + g) = n + S g",
                "exists 0",
                "rewrite hstep_length",
                "specialize zero_add (S (n + g))",
                "exact zero_add",
                "have hzero : "
                + _at("b", "c", "n + g", "0", tag="b5cvpsez_zero"),
                "specialize power_quotient_prefix_tail_entry_zero p",
                "specialize power_quotient_prefix_tail_entry_zero n",
                "specialize power_quotient_prefix_tail_entry_zero b",
                "specialize power_quotient_prefix_tail_entry_zero c",
                "specialize power_quotient_prefix_tail_entry_zero (n + S g)",
                "specialize power_quotient_prefix_tail_entry_zero (n + g)",
                "apply power_quotient_prefix_tail_entry_zero",
                "exact hp",
                "exact hprefix",
                "exact htail_start",
                "exact htail_bound",
                "rewrite hstep_length at hsum",
                "rewrite hstep_length at hsum",
                "rewrite hstep_length at hsum",
                "have hprefix_sum : "
                + _sum_relation_terms(
                    "b",
                    "c",
                    "n + g",
                    "t",
                    tag="b5cvpsez_prefix_sum",
                ),
                "specialize beta_sum_succ_last_zero b",
                "specialize beta_sum_succ_last_zero c",
                "specialize beta_sum_succ_last_zero (n + g)",
                "specialize beta_sum_succ_last_zero t",
                "apply beta_sum_succ_last_zero",
                "exact hsum",
                "exact hzero",
                "specialize IH t",
                "specialize IH e",
                "apply IH",
                "exact hp",
                "exact hrestricted",
                "exact hprefix_sum",
                "exact hlegendre",
            ),
            "Zero quotient tails preserve the finite Legendre sum.",
        ),
        spec(
            LEGENDRE_SUM_EXTENDED_PREFIX_EXISTS,
            "forall p n e g. "
            f"({extended_exists_prime}) -> ({extended_exists_legendre}) -> "
            f"exists b c. (({extended_exists_prefix}) /\\ "
            f"({extended_exists_sum}))",
            (
                "prime_power_quotient_prefix_exists",
                "beta_sum_exists",
                POWER_QUOTIENT_PREFIX_SUM_EXTEND_ZERO,
            ),
            (
                "intro p",
                "intro n",
                "intro e",
                "intro g",
                "intro hp",
                "intro hlegendre",
                "have hprefix : exists b c. "
                + _power_quotient_prefix_terms(
                    "p",
                    "n",
                    "b",
                    "c",
                    "n + g",
                    tag="b5cvlsepe_generated_prefix",
                ),
                "specialize prime_power_quotient_prefix_exists p",
                "specialize prime_power_quotient_prefix_exists n",
                "specialize prime_power_quotient_prefix_exists (n + g)",
                "apply prime_power_quotient_prefix_exists",
                "exact hp",
                "cases hprefix",
                "cases hprefix_witness",
                "have hsum : exists t. "
                + _sum_relation_terms(
                    "x",
                    "x1",
                    "n + g",
                    "t",
                    tag="b5cvlsepe_generated_sum",
                ),
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists (n + g)",
                "exact beta_sum_exists",
                "cases hsum",
                "have htotal : x2 = e",
                "specialize power_quotient_prefix_sum_extend_zero p",
                "specialize power_quotient_prefix_sum_extend_zero n",
                "specialize power_quotient_prefix_sum_extend_zero x",
                "specialize power_quotient_prefix_sum_extend_zero x1",
                "specialize power_quotient_prefix_sum_extend_zero g",
                "specialize power_quotient_prefix_sum_extend_zero x2",
                "specialize power_quotient_prefix_sum_extend_zero e",
                "apply power_quotient_prefix_sum_extend_zero",
                "exact hp",
                "exact hprefix_witness_witness",
                "exact hsum_witness",
                "exact hlegendre",
                "exists x",
                "exists x1",
                "split",
                "exact hprefix_witness_witness",
                "rewrite <- htotal",
                "rewrite <- htotal",
                "exact hsum_witness",
            ),
            "A Legendre sum admits an arbitrarily long zero-extended quotient code.",
        ),
        spec(
            POWER_QUOTIENT_DOUBLE_POINTWISE_UPPER,
            "forall p n b c d e l. "
            f"({pointwise_left}) -> ({pointwise_right}) -> "
            f"({pointwise_result})",
            ("beta_at_unique", "pow_functional", "division_double_quotient_upper"),
            (
                "intro p",
                "intro n",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro l",
                "intro hleft",
                "intro hright",
                "intro i",
                "intro q",
                "intro Q",
                "intro hi",
                "intro hq",
                "intro hQ",
                "have hleft_data : exists D u r. "
                f"({_power_terms('p', 'S i', 'D', tag='b5cvpdpu_left_power')}) /\\ "
                f"(({_at('b', 'c', 'i', 'u', tag='b5cvpdpu_left_entry')}) /\\ "
                + "("
                + _divrem_term(
                    "D",
                    "n",
                    "u",
                    "r",
                    tag="b5cvpdpu_left_division",
                    variables=pointwise_variables + ("i", "D", "u", "r"),
                )
                + "))",
                "specialize hleft i",
                "apply hleft",
                "exact hi",
                "cases hleft_data",
                "cases hleft_data_witness",
                "cases hleft_data_witness_witness",
                "cases hleft_data_witness_witness_witness",
                "cases hleft_data_witness_witness_witness_right",
                "have hright_data : exists D u r. "
                f"({_power_terms('p', 'S i', 'D', tag='b5cvpdpu_right_power')}) /\\ "
                f"(({_at('d', 'e', 'i', 'u', tag='b5cvpdpu_right_entry')}) /\\ "
                + "("
                + _divrem_term(
                    "D",
                    "n + n",
                    "u",
                    "r",
                    tag="b5cvpdpu_right_division",
                    variables=pointwise_variables + ("i", "D", "u", "r"),
                )
                + "))",
                "specialize hright i",
                "apply hright",
                "exact hi",
                "cases hright_data",
                "cases hright_data_witness",
                "cases hright_data_witness_witness",
                "cases hright_data_witness_witness_witness",
                "cases hright_data_witness_witness_witness_right",
                "have hq_eq : q = x1",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique q",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hq",
                "exact hleft_data_witness_witness_witness_right_left",
                "have hQ_eq : Q = x4",
                "specialize beta_at_unique d",
                "specialize beta_at_unique e",
                "specialize beta_at_unique i",
                "specialize beta_at_unique Q",
                "specialize beta_at_unique x4",
                "apply beta_at_unique",
                "exact hQ",
                "exact hright_data_witness_witness_witness_right_left",
                "have hpower_eq : x = x3",
                "specialize pow_functional p",
                "specialize pow_functional (S i)",
                "specialize pow_functional x",
                "specialize pow_functional x3",
                "apply pow_functional",
                "exact hleft_data_witness_witness_witness_left",
                "exact hright_data_witness_witness_witness_left",
                "rewrite <- hpower_eq at "
                "hright_data_witness_witness_witness_right_right",
                "rewrite <- hpower_eq at "
                "hright_data_witness_witness_witness_right_right",
                "have hupper : exists g. g + x4 = S (x1 + x1)",
                "specialize division_double_quotient_upper x",
                "specialize division_double_quotient_upper n",
                "specialize division_double_quotient_upper x1",
                "specialize division_double_quotient_upper x2",
                "specialize division_double_quotient_upper x4",
                "specialize division_double_quotient_upper x5",
                "apply division_double_quotient_upper",
                "exact hleft_data_witness_witness_witness_right_right",
                "exact hright_data_witness_witness_witness_right_right",
                "rewrite hQ_eq",
                "rewrite hq_eq",
                "rewrite hq_eq",
                "exact hupper",
            ),
            "Doubled quotient prefixes satisfy the pointwise carry upper bound.",
        ),
        spec(
            BETA_SUM_POINTWISE_DOUBLE_SUCC_LE,
            "forall b c d e l B A. "
            f"({fold_left}) -> ({fold_right}) -> ({fold_pointwise}) -> "
            f"({fold_result})",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "le_succ",
                "le_refl",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "induction l",
                "intro B",
                "intro A",
                "intro hleft",
                "intro hright",
                "intro hpointwise",
                "have hB : B = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero B",
                "apply beta_sum_zero",
                "exact hleft",
                "have hA : A = 0",
                "specialize beta_sum_zero d",
                "specialize beta_sum_zero e",
                "specialize beta_sum_zero A",
                "apply beta_sum_zero",
                "exact hright",
                "rewrite hA",
                "rewrite hB",
                "rewrite hB",
                "exists 0",
                "simp",
                "intro B",
                "intro A",
                "intro hleft",
                "intro hright",
                "intro hpointwise",
                "have hleft_decomp : "
                + _sum_decomposition(
                    "b", "c", "l", "B", tag="b5cvbsdsl_left_decomp"
                ),
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose B",
                "apply beta_sum_succ_decompose",
                "exact hleft",
                "cases hleft_decomp",
                "cases hleft_decomp_witness",
                "cases hleft_decomp_witness_witness",
                "cases hleft_decomp_witness_witness_right",
                "have hright_decomp : "
                + _sum_decomposition(
                    "d", "e", "l", "A", tag="b5cvbsdsl_right_decomp"
                ),
                "specialize beta_sum_succ_decompose d",
                "specialize beta_sum_succ_decompose e",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose A",
                "apply beta_sum_succ_decompose",
                "exact hright",
                "cases hright_decomp",
                "cases hright_decomp_witness",
                "cases hright_decomp_witness_witness",
                "cases hright_decomp_witness_witness_right",
                "have hprefix_pointwise : "
                + _sum_double_pointwise(
                    "l", tag="b5cvbsdsl_prefix_pointwise"
                ),
                "intro i",
                "intro q",
                "intro Q",
                "intro hi",
                "intro hq",
                "intro hQ",
                "specialize hpointwise i",
                "specialize hpointwise q",
                "specialize hpointwise Q",
                "apply hpointwise",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hq",
                "exact hQ",
                "have hprefix : exists g. g + x3 = (x1 + x1) + l",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hleft_decomp_witness_witness_right_left",
                "exact hright_decomp_witness_witness_right_left",
                "exact hprefix_pointwise",
                "have hlast : exists g. g + x2 = S (x + x)",
                "specialize hpointwise l",
                "specialize hpointwise x",
                "specialize hpointwise x2",
                "apply hpointwise",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hleft_decomp_witness_witness_left",
                "exact hright_decomp_witness_witness_left",
                "have hfirst : exists g. g + (x3 + x2) = ((x1 + x1) + l) + x2",
                "specialize add_le_add_right x3",
                "specialize add_le_add_right ((x1 + x1) + l)",
                "specialize add_le_add_right x2",
                "apply add_le_add_right",
                "exact hprefix",
                "have hsecond : exists g. "
                "g + (((x1 + x1) + l) + x2) = "
                "((x1 + x1) + l) + S (x + x)",
                "specialize add_le_add_left x2",
                "specialize add_le_add_left (S (x + x))",
                "specialize add_le_add_left ((x1 + x1) + l)",
                "apply add_le_add_left",
                "exact hlast",
                "have hfold : exists g. g + (x3 + x2) = ((x1 + x1) + l) + S (x + x)",
                "specialize le_trans (x3 + x2)",
                "specialize le_trans (((x1 + x1) + l) + x2)",
                "specialize le_trans (((x1 + x1) + l) + S (x + x))",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hleft_decomp_witness_witness_right_right",
                "cases hfold",
                "exists x4",
                "trans ((x1 + x1) + l) + S (x + x)",
                "exact hfold_witness",
                "simp [add_assoc, add_comm]",
                "congr",
                "congr",
                "refl",
                "trans (x1 + x) + (x + l)",
                "symm",
                "apply add_assoc",
                "trans (x + x1) + (x + l)",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
            ),
            "Pointwise doubled carry bounds control the two finite sums.",
        ),
        spec(
            CENTRAL_PRIME_VALUATION_LE_DOUBLE,
            "forall p n c e. "
            f"({final_prime}) -> ({final_central}) -> "
            f"({final_valuation}) -> ({final_result})",
            (
                "prime_legendre_sum_exists",
                CENTRAL_LEGENDRE_VALUATION_BALANCE,
                LEGENDRE_SUM_EXTENDED_PREFIX_EXISTS,
                POWER_QUOTIENT_DOUBLE_POINTWISE_UPPER,
                BETA_SUM_POINTWISE_DOUBLE_SUCC_LE,
                "add_comm",
                "add_le_cancel_right",
            ),
            (
                "intro p",
                "intro n",
                "intro c",
                "intro e",
                "intro hp",
                "intro hcentral",
                "intro hvaluation",
                "have hcolumn : exists B. "
                + legendre_sum("p", "n", "B", tag="b5cvpvd_column"),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists n",
                "apply prime_legendre_sum_exists",
                "exact hp",
                "cases hcolumn",
                "have htotal : exists A. "
                + _legendre_sum_term(
                    "p", "n + n", "A", tag="b5cvpvd_total"
                ),
                "specialize prime_legendre_sum_exists p",
                "specialize prime_legendre_sum_exists (n + n)",
                "apply prime_legendre_sum_exists",
                "exact hp",
                "cases htotal",
                "have hbalance : x1 = (x + x) + e",
                "specialize central_binom_legendre_valuation_balance p",
                "specialize central_binom_legendre_valuation_balance n",
                "specialize central_binom_legendre_valuation_balance c",
                "specialize central_binom_legendre_valuation_balance e",
                "specialize central_binom_legendre_valuation_balance x1",
                "specialize central_binom_legendre_valuation_balance x",
                "apply central_binom_legendre_valuation_balance",
                "exact hp",
                "exact hcentral",
                "exact hvaluation",
                "exact htotal_witness",
                "exact hcolumn_witness",
                "have hextended : exists b c. "
                + "("
                + _power_quotient_prefix_terms(
                    "p",
                    "n",
                    "b",
                    "c",
                    "n + n",
                    tag="b5cvpvd_extended_prefix",
                )
                + ") /\\ ("
                + _sum_relation_terms(
                    "b",
                    "c",
                    "n + n",
                    "x",
                    tag="b5cvpvd_extended_sum",
                )
                + ")",
                "specialize legendre_sum_extended_prefix_exists p",
                "specialize legendre_sum_extended_prefix_exists n",
                "specialize legendre_sum_extended_prefix_exists x",
                "specialize legendre_sum_extended_prefix_exists n",
                "apply legendre_sum_extended_prefix_exists",
                "exact hp",
                "exact hcolumn_witness",
                "cases hextended",
                "cases hextended_witness",
                "cases hextended_witness_witness",
                "cases htotal_witness",
                "cases htotal_witness_witness",
                "cases htotal_witness_witness_witness",
                "have hpointwise : "
                + _sum_double_pointwise(
                    "n + n",
                    tag="b5cvpvd_pointwise",
                    left_code="x2",
                    left_scale="x3",
                    right_code="x4",
                    right_scale="x5",
                ),
                "specialize power_quotient_double_pointwise_upper p",
                "specialize power_quotient_double_pointwise_upper n",
                "specialize power_quotient_double_pointwise_upper x2",
                "specialize power_quotient_double_pointwise_upper x3",
                "specialize power_quotient_double_pointwise_upper x4",
                "specialize power_quotient_double_pointwise_upper x5",
                "specialize power_quotient_double_pointwise_upper (n + n)",
                "apply power_quotient_double_pointwise_upper",
                "exact hextended_witness_witness_left",
                "exact htotal_witness_witness_witness_left",
                "have hupper : exists g. g + x1 = (x + x) + (n + n)",
                "specialize beta_sum_pointwise_double_succ_le x2",
                "specialize beta_sum_pointwise_double_succ_le x3",
                "specialize beta_sum_pointwise_double_succ_le x4",
                "specialize beta_sum_pointwise_double_succ_le x5",
                "specialize beta_sum_pointwise_double_succ_le (n + n)",
                "specialize beta_sum_pointwise_double_succ_le x",
                "specialize beta_sum_pointwise_double_succ_le x1",
                "apply beta_sum_pointwise_double_succ_le",
                "exact hextended_witness_witness_right",
                "exact htotal_witness_witness_witness_right",
                "exact hpointwise",
                "rewrite hbalance at hupper",
                "have hleft_comm : (x + x) + e = e + (x + x)",
                "apply add_comm",
                "rewrite hleft_comm at hupper",
                "have hright_comm : (x + x) + (n + n) = (n + n) + (x + x)",
                "apply add_comm",
                "rewrite hright_comm at hupper",
                "specialize add_le_cancel_right e",
                "specialize add_le_cancel_right (n + n)",
                "specialize add_le_cancel_right (x + x)",
                "apply add_le_cancel_right",
                "exact hupper",
            ),
            "Every prime valuation exponent of a central coefficient is at most 2*n.",
        ),
    )


__all__ = [
    "make_bertrand_central_binom_valuation_candidate_theorems",
]
