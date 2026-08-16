"""Constructive order and quotient support for Bertrand B5.

This isolated factory supplies strict-addition, finite-sum order,
division-doubling, and monotone-power laws used by the five-range
central-binomial valuation audit.  Every readable relation is fully expanded
to ordinary first-order Peano arithmetic before parsing.  No division,
sequence, order, sum, product, or power primitive is added to the kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_power_valuation_candidate import _power_terms
from .finite_fold_surface import (
    beta_at,
    power_relation,
    repeat_relation,
    sum_relation,
)


def _divrem_term(
    divisor: str,
    value: str,
    quotient: str,
    remainder: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    """Expand one canonical quotient/remainder record."""

    bound = _lt_term(
        remainder,
        divisor,
        tag=f"{tag}_bound",
        variables=variables,
    )
    return (
        f"(({value}) = ({divisor}) * ({quotient}) + ({remainder}) /\\ "
        f"({bound}))"
    )


def _sum_pointwise_le(
    length: str,
    *,
    tag: str,
    left_code: str = "b",
    left_scale: str = "c",
    right_code: str = "d",
    right_scale: str = "e",
    left_value: str = "a",
    right_value: str = "z",
    variables: tuple[str, ...] = (
        "b",
        "c",
        "d",
        "e",
        "l",
        "n",
        "q",
        "i",
        "a",
        "z",
    ),
) -> str:
    left = beta_at(
        left_code, left_scale, "i", left_value, tag=f"{tag}_left"
    )
    right = beta_at(
        right_code, right_scale, "i", right_value, tag=f"{tag}_right"
    )
    bound = _lt_term(
        "i", length, tag=f"{tag}_bound", variables=variables
    )
    factor_order = _le_term(
        left_value,
        right_value,
        tag=f"{tag}_factor",
        variables=variables,
    )
    return (
        f"forall i {left_value} {right_value}. "
        f"({bound}) -> ({left}) -> ({right}) -> "
        f"({factor_order})"
    )


def _sum_uniform_le(length: str, *, tag: str) -> str:
    decoded = beta_at("b", "c", "i", "x", tag=f"{tag}_source")
    variables = ("b", "c", "a", "l", "n", "i", "x")
    bound = _lt_term(
        "i", length, tag=f"{tag}_bound", variables=variables
    )
    factor_order = _le_term(
        "x", "a", tag=f"{tag}_factor", variables=variables
    )
    return (
        f"forall i x. ({bound}) -> ({decoded}) -> ({factor_order})"
    )


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = sum_relation(code, scale, length, "r", tag=f"{tag}_sum")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_bertrand_b5_order_quotient_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the ten new rows of the B5 order/quotient tranche."""

    add_variables = ("a", "b", "c", "d")
    add_left = _lt_term(
        "a", "b", tag="b5alaa_left", variables=add_variables
    )
    add_right = _lt_term(
        "c", "d", tag="b5alaa_right", variables=add_variables
    )
    add_result = _lt_term(
        "a + c", "b + d", tag="b5alaa_result", variables=add_variables
    )

    cancel_variables = ("c", "a", "b")
    cancel_source = _lt_term(
        "c + a",
        "c + b",
        tag="b5altcl_source",
        variables=cancel_variables,
    )
    cancel_result = _lt_term(
        "a", "b", tag="b5altcl_result", variables=cancel_variables
    )

    pointwise = _sum_pointwise_le("l", tag="bspl")
    left_sum = sum_relation("b", "c", "l", "n", tag="bspl_left_sum")
    right_sum = sum_relation("d", "e", "l", "q", tag="bspl_right_sum")
    sum_result = _le_term(
        "n",
        "q",
        tag="bspl_result",
        variables=("b", "c", "d", "e", "l", "n", "q"),
    )
    left_decomposition = _sum_decomposition(
        "b", "c", "l", "n", tag="bspl_left_decomposition"
    )
    right_decomposition = _sum_decomposition(
        "d", "e", "l", "q", tag="bspl_right_decomposition"
    )
    prefix_pointwise = _sum_pointwise_le("l", tag="bspl_prefix")
    prefix_order = _le_term(
        "x1",
        "x3",
        tag="bspl_prefix_result",
        variables=("b", "c", "d", "e", "l", "n", "q", "x", "x1", "x2", "x3"),
    )
    entry_order = _le_term(
        "x",
        "x2",
        tag="bspl_entry_result",
        variables=("b", "c", "d", "e", "l", "n", "q", "x", "x1", "x2", "x3"),
    )
    first_add_order = _le_term(
        "x1 + x",
        "x3 + x",
        tag="bspl_first_add",
        variables=("b", "c", "d", "e", "l", "n", "q", "x", "x1", "x2", "x3"),
    )
    second_add_order = _le_term(
        "x3 + x",
        "x3 + x2",
        tag="bspl_second_add",
        variables=("b", "c", "d", "e", "l", "n", "q", "x", "x1", "x2", "x3"),
    )
    fold_order = _le_term(
        "x1 + x",
        "x3 + x2",
        tag="bspl_fold",
        variables=("b", "c", "d", "e", "l", "n", "q", "x", "x1", "x2", "x3"),
    )

    uniform = _sum_uniform_le("l", tag="bsulm")
    uniform_sum = sum_relation(
        "b", "c", "l", "n", tag="bsulm_source_sum"
    )
    uniform_result = _le_term(
        "n",
        "l * a",
        tag="bsulm_result",
        variables=("b", "c", "a", "l", "n"),
    )
    repeat_exists = (
        "exists d e. "
        f"({repeat_relation('d', 'e', 'a', 'l', tag='bsulm_repeat')})"
    )
    repeat_sum_exists = (
        "exists q. "
        f"({sum_relation('x', 'x1', 'l', 'q', tag='bsulm_repeat_sum')})"
    )
    uniform_pointwise = _sum_pointwise_le(
        "l",
        tag="bsulm_pointwise",
        left_code="b",
        left_scale="c",
        right_code="x",
        right_scale="x1",
        left_value="p",
        right_value="z",
        variables=(
            "b",
            "c",
            "a",
            "l",
            "n",
            "x",
            "x1",
            "x2",
            "i",
            "p",
            "z",
        ),
    )
    uniform_fold_order = _le_term(
        "n",
        "x2",
        tag="bsulm_fold_order",
        variables=("b", "c", "a", "l", "n", "x", "x1", "x2"),
    )

    zero_variables = ("d", "n", "q", "r")
    zero_division = _divrem_term(
        "d", "n", "q", "r", tag="bdzq_source", variables=zero_variables
    )
    zero_bound = _lt_term(
        "n", "d", tag="bdzq_bound", variables=zero_variables
    )
    double_variables = ("d", "n", "q", "r", "Q", "R")
    double_source = _divrem_term(
        "d",
        "n",
        "q",
        "r",
        tag="bddqb_source",
        variables=double_variables,
    )
    double_target = _divrem_term(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddqb_double",
        variables=double_variables,
    )
    lower_source = _divrem_term(
        "d",
        "n",
        "q",
        "r",
        tag="bddql_source",
        variables=double_variables,
    )
    lower_double = _divrem_term(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddql_double",
        variables=double_variables,
    )
    lower_result = _le_term(
        "q + q",
        "Q",
        tag="bddql_result",
        variables=double_variables,
    )
    upper_source = _divrem_term(
        "d",
        "n",
        "q",
        "r",
        tag="bddqu_source",
        variables=double_variables,
    )
    upper_double = _divrem_term(
        "d",
        "n + n",
        "Q",
        "R",
        tag="bddqu_double",
        variables=double_variables,
    )
    upper_result = _le_term(
        "Q",
        "S (q + q)",
        tag="bddqu_result",
        variables=double_variables,
    )

    power_variables = ("p", "e", "f", "x", "y")
    power_base = _le_term(
        "1", "p", tag="bppem_base", variables=power_variables
    )
    power_exponent = _le_term(
        "e", "f", tag="bppem_exponent", variables=power_variables
    )
    power_left = power_relation(
        "p", "e", "x", tag="bppem_left_power"
    )
    power_right = power_relation(
        "p", "f", "y", tag="bppem_right_power"
    )
    power_result = _le_term(
        "x", "y", tag="bppem_result", variables=power_variables
    )
    gap_power = (
        "exists z. "
        f"({power_relation('p', 'x1', 'z', tag='bppem_gap_power')})"
    )
    gap_power_order = _le_term(
        "1",
        "x2",
        tag="bppem_gap_power_order",
        variables=power_variables + ("x1", "x2"),
    )
    product_order = _le_term(
        "x",
        "x * x2",
        tag="bppem_product_order",
        variables=power_variables + ("x1", "x2"),
    )

    tail_variables = ("p", "e", "x", "s", "n")
    tail_base = _le_term(
        "1", "p", tag="bpsts_base", variables=tail_variables
    )
    tail_exponent = _le_term(
        "2", "e", tag="bpsts_exponent", variables=tail_variables
    )
    square_power = _power_terms(
        "p", "2", "s", tag="bpsts_square_power"
    )
    tail_power = power_relation(
        "p", "e", "x", tag="bpsts_tail_power"
    )
    tail_source = _lt_term(
        "n", "s", tag="bpsts_source", variables=tail_variables
    )
    tail_result = _lt_term(
        "n", "x", tag="bpsts_result", variables=tail_variables
    )
    square_order = _le_term(
        "s",
        "x",
        tag="bpsts_square_order",
        variables=tail_variables,
    )

    return (
        spec(
            "add_lt_add",
            "forall a b c d. "
            f"({add_left}) -> ({add_right}) -> ({add_result})",
            ("add_succ_left", "add_shuffle_middle"),
            (
                "intro a",
                "intro b",
                "intro c",
                "intro d",
                "intro hab",
                "intro hcd",
                "cases hab",
                "cases hcd",
                "exists S (x + x1)",
                "rewrite <- hab_witness",
                "rewrite <- hcd_witness",
                "trans S ((x + x1) + S (a + c))",
                "apply add_succ_left",
                "trans S (S ((x + x1) + (a + c)))",
                "congr",
                "apply PA4",
                "trans S (S ((x + a) + (x1 + c)))",
                "congr",
                "congr",
                "apply add_shuffle_middle",
                "trans S ((x + a) + S (x1 + c))",
                "congr",
                "symm",
                "apply PA4",
                "trans S ((x + a) + (x1 + S c))",
                "congr",
                "congr",
                "refl",
                "symm",
                "apply PA4",
                "trans S (x + a) + (x1 + S c)",
                "symm",
                "apply add_succ_left",
                "congr",
                "symm",
                "apply PA4",
                "refl",
            ),
            "Strict inequalities add componentwise.",
        ),
        spec(
            "add_lt_cancel_left",
            "forall c a b. "
            f"({cancel_source}) -> ({cancel_result})",
            ("add_assoc", "add_comm", "add_left_cancel"),
            (
                "intro c",
                "intro a",
                "intro b",
                "intro hsource",
                "cases hsource",
                "exists x",
                "specialize add_left_cancel c",
                "specialize add_left_cancel (x + S a)",
                "specialize add_left_cancel b",
                "apply add_left_cancel",
                "trans x + S (c + a)",
                "trans c + S (x + a)",
                "congr",
                "refl",
                "apply PA4",
                "trans S (c + (x + a))",
                "apply PA4",
                "trans S (x + (c + a))",
                "congr",
                "trans (c + x) + a",
                "symm",
                "apply add_assoc",
                "trans (x + c) + a",
                "congr",
                "apply add_comm",
                "refl",
                "apply add_assoc",
                "symm",
                "apply PA4",
                "exact hsource_witness",
            ),
            "A common left summand cancels from strict witness order.",
        ),
        spec(
            "beta_sum_pointwise_le",
            "forall b c d e l n q. "
            f"({pointwise}) -> ({left_sum}) -> ({right_sum}) -> "
            f"({sum_result})",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "le_succ",
                "le_refl",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
            ),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "induction l",
                "intro n",
                "intro q",
                "intro hpw",
                "intro hn",
                "intro hq",
                "have hn0 : n = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero n",
                "apply beta_sum_zero",
                "exact hn",
                "have hq0 : q = 0",
                "specialize beta_sum_zero d",
                "specialize beta_sum_zero e",
                "specialize beta_sum_zero q",
                "apply beta_sum_zero",
                "exact hq",
                "rewrite hn0",
                "rewrite hq0",
                "specialize le_refl 0",
                "exact le_refl",
                "intro n",
                "intro q",
                "intro hpw",
                "intro hn",
                "intro hq",
                f"have hnd : {left_decomposition}",
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose n",
                "apply beta_sum_succ_decompose",
                "exact hn",
                "cases hnd",
                "cases hnd_witness",
                "cases hnd_witness_witness",
                "cases hnd_witness_witness_right",
                f"have hqd : {right_decomposition}",
                "specialize beta_sum_succ_decompose d",
                "specialize beta_sum_succ_decompose e",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose q",
                "apply beta_sum_succ_decompose",
                "exact hq",
                "cases hqd",
                "cases hqd_witness",
                "cases hqd_witness_witness",
                "cases hqd_witness_witness_right",
                f"have hpw_prefix : {prefix_pointwise}",
                "intro i",
                "intro a",
                "intro z",
                "intro hi",
                "intro ha",
                "intro hz",
                "specialize hpw i",
                "specialize hpw a",
                "specialize hpw z",
                "apply hpw",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
                "exact hz",
                f"have hprefix : {prefix_order}",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hpw_prefix",
                "exact hnd_witness_witness_right_left",
                "exact hqd_witness_witness_right_left",
                f"have hentry : {entry_order}",
                "specialize hpw l",
                "specialize hpw x",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hnd_witness_witness_left",
                "exact hqd_witness_witness_left",
                f"have hfirst : {first_add_order}",
                "specialize add_le_add_right x1",
                "specialize add_le_add_right x3",
                "specialize add_le_add_right x",
                "apply add_le_add_right",
                "exact hprefix",
                f"have hsecond : {second_add_order}",
                "specialize add_le_add_left x",
                "specialize add_le_add_left x2",
                "specialize add_le_add_left x3",
                "apply add_le_add_left",
                "exact hentry",
                f"have hfold : {fold_order}",
                "specialize le_trans (x1 + x)",
                "specialize le_trans (x3 + x)",
                "specialize le_trans (x3 + x2)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
                "rewrite hnd_witness_witness_right_right",
                "rewrite hqd_witness_witness_right_right",
                "exact hfold",
            ),
            "Pointwise bounded decoded prefixes have ordered finite sums.",
        ),
        spec(
            "beta_sum_uniform_le_mul",
            "forall b c a l n. "
            f"({uniform}) -> ({uniform_sum}) -> ({uniform_result})",
            (
                "beta_repeat_exists",
                "beta_sum_exists",
                "beta_repeat_entry_eq",
                "beta_repeat_sum_exact",
                "beta_sum_pointwise_le",
            ),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro n",
                "intro huniform",
                "intro hsum",
                f"have hrepeat_exists : {repeat_exists}",
                "specialize beta_repeat_exists a",
                "specialize beta_repeat_exists l",
                "exact beta_repeat_exists",
                "cases hrepeat_exists",
                "cases hrepeat_exists_witness",
                f"have hrepeat_sum_exists : {repeat_sum_exists}",
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists l",
                "exact beta_sum_exists",
                "cases hrepeat_sum_exists",
                "have hrepeat_sum : x2 = l * a",
                "specialize beta_repeat_sum_exact x",
                "specialize beta_repeat_sum_exact x1",
                "specialize beta_repeat_sum_exact a",
                "specialize beta_repeat_sum_exact l",
                "specialize beta_repeat_sum_exact x2",
                "apply beta_repeat_sum_exact",
                "exact hrepeat_exists_witness_witness",
                "exact hrepeat_sum_exists_witness",
                f"have hpw : {uniform_pointwise}",
                "intro i",
                "intro p",
                "intro z",
                "intro hi",
                "intro hp",
                "intro hz",
                "have hza : z = a",
                "specialize beta_repeat_entry_eq x",
                "specialize beta_repeat_entry_eq x1",
                "specialize beta_repeat_entry_eq a",
                "specialize beta_repeat_entry_eq l",
                "specialize beta_repeat_entry_eq i",
                "specialize beta_repeat_entry_eq z",
                "apply beta_repeat_entry_eq",
                "exact hrepeat_exists_witness_witness",
                "exact hi",
                "exact hz",
                "rewrite hza",
                "specialize huniform i",
                "specialize huniform p",
                "apply huniform",
                "exact hi",
                "exact hp",
                f"have hfold : {uniform_fold_order}",
                "specialize beta_sum_pointwise_le b",
                "specialize beta_sum_pointwise_le c",
                "specialize beta_sum_pointwise_le x",
                "specialize beta_sum_pointwise_le x1",
                "specialize beta_sum_pointwise_le l",
                "specialize beta_sum_pointwise_le n",
                "specialize beta_sum_pointwise_le x2",
                "apply beta_sum_pointwise_le",
                "exact hpw",
                "exact hsum",
                "exact hrepeat_sum_exists_witness",
                "rewrite <- hrepeat_sum",
                "exact hfold",
            ),
            "A uniformly bounded finite sum is bounded by length times bound.",
        ),
        spec(
            "division_zero_quotient_of_lt",
            "forall d n q r. "
            f"({zero_division}) -> ({zero_bound}) -> q = 0",
            ("zero_add", "division_remainder_unique"),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro hdivision",
                "intro hbound",
                "cases hdivision",
                "have hzero : n = d * 0 + n",
                "rewrite PA5",
                "symm",
                "specialize zero_add n",
                "apply zero_add",
                "have hunique : q = 0 /\\ r = n",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique n",
                "specialize division_remainder_unique q",
                "specialize division_remainder_unique r",
                "specialize division_remainder_unique 0",
                "specialize division_remainder_unique n",
                "apply division_remainder_unique",
                "exact hdivision_left",
                "exact hdivision_right",
                "exact hzero",
                "exact hbound",
                "cases hunique",
                "exact hunique_left",
            ),
            "A dividend below its divisor has quotient zero.",
        ),
        spec(
            "division_double_quotient_bit",
            "forall d n q r Q R. "
            f"({double_source}) -> ({double_target}) -> "
            "(Q = q + q \\/ Q = S (q + q))",
            (
                "le_or_lt",
                "le_eq_or_lt",
                "lt_not_le",
                "zero_le",
                "one_le_of_ne_zero",
                "add_shuffle_middle",
                "mul_add",
                "add_assoc",
                "add_comm",
                "add_lt_add",
                "add_lt_cancel_left",
                "division_remainder_unique",
            ),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro Q",
                "intro R",
                "intro hsource",
                "intro hdouble",
                "cases hsource",
                "cases hdouble",
                "have hdouble_eq : n + n = d * (q + q) + (r + r)",
                "rewrite hsource_left",
                "rewrite hsource_left",
                "trans (d * q + d * q) + (r + r)",
                "apply add_shuffle_middle",
                "congr",
                "symm",
                "apply mul_add",
                "refl",
                "specialize le_or_lt (r + r)",
                "specialize le_or_lt d",
                "cases le_or_lt",
                "have hsplit : r + r = d \\/ exists k. k + S (r + r) = d",
                "specialize le_eq_or_lt (r + r)",
                "specialize le_eq_or_lt d",
                "apply le_eq_or_lt",
                "exact le_or_lt_left",
                "cases hsplit",
                "have hd0 : ~(d = 0)",
                "intro hd",
                "rewrite hd at hsource_right",
                "specialize lt_not_le r",
                "specialize lt_not_le 0",
                "apply lt_not_le",
                "exact hsource_right",
                "specialize zero_le r",
                "exact zero_le",
                "have hzero_bound : exists k. k + S 0 = d",
                "specialize one_le_of_ne_zero d",
                "apply one_le_of_ne_zero",
                "exact hd0",
                "have hcandidate_eq : "
                "n + n = d * S (q + q) + 0",
                "trans d * (q + q) + (r + r)",
                "exact hdouble_eq",
                "rewrite hsplit_left",
                "trans d * S (q + q)",
                "symm",
                "apply PA6",
                "symm",
                "apply PA3",
                "have hunique : Q = S (q + q) /\\ R = 0",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (n + n)",
                "specialize division_remainder_unique Q",
                "specialize division_remainder_unique R",
                "specialize division_remainder_unique (S (q + q))",
                "specialize division_remainder_unique 0",
                "apply division_remainder_unique",
                "exact hdouble_left",
                "exact hdouble_right",
                "exact hcandidate_eq",
                "exact hzero_bound",
                "cases hunique",
                "right",
                "exact hunique_left",
                "have hunique : Q = q + q /\\ R = r + r",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (n + n)",
                "specialize division_remainder_unique Q",
                "specialize division_remainder_unique R",
                "specialize division_remainder_unique (q + q)",
                "specialize division_remainder_unique (r + r)",
                "apply division_remainder_unique",
                "exact hdouble_left",
                "exact hdouble_right",
                "exact hdouble_eq",
                "exact hsplit_right",
                "cases hunique",
                "left",
                "exact hunique_left",
                "cases le_or_lt_right",
                "have hrr : r + r = d + S x",
                "trans x + S d",
                "symm",
                "exact le_or_lt_right_witness",
                "trans S (x + d)",
                "apply PA4",
                "trans S (d + x)",
                "congr",
                "apply add_comm",
                "symm",
                "apply PA4",
                "have hsum_lt : exists k. k + S (r + r) = d + d",
                "specialize add_lt_add r",
                "specialize add_lt_add d",
                "specialize add_lt_add r",
                "specialize add_lt_add d",
                "apply add_lt_add",
                "exact hsource_right",
                "exact hsource_right",
                "rewrite hrr at hsum_lt",
                "have hcarry_bound : exists k. k + S (S x) = d",
                "specialize add_lt_cancel_left d",
                "specialize add_lt_cancel_left (S x)",
                "specialize add_lt_cancel_left d",
                "apply add_lt_cancel_left",
                "exact hsum_lt",
                "have hcandidate_eq : "
                "n + n = d * S (q + q) + S x",
                "trans d * (q + q) + (r + r)",
                "exact hdouble_eq",
                "rewrite hrr",
                "trans (d * (q + q) + d) + S x",
                "symm",
                "apply add_assoc",
                "congr",
                "symm",
                "apply PA6",
                "refl",
                "have hunique : Q = S (q + q) /\\ R = S x",
                "specialize division_remainder_unique d",
                "specialize division_remainder_unique (n + n)",
                "specialize division_remainder_unique Q",
                "specialize division_remainder_unique R",
                "specialize division_remainder_unique (S (q + q))",
                "specialize division_remainder_unique (S x)",
                "apply division_remainder_unique",
                "exact hdouble_left",
                "exact hdouble_right",
                "exact hcandidate_eq",
                "exact hcarry_bound",
                "cases hunique",
                "right",
                "exact hunique_left",
            ),
            "Doubling a dividend changes its quotient by one binary carry.",
        ),
        spec(
            "division_double_quotient_lower",
            "forall d n q r Q R. "
            f"({lower_source}) -> ({lower_double}) -> ({lower_result})",
            ("division_double_quotient_bit", "le_refl", "le_succ"),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro Q",
                "intro R",
                "intro hsource",
                "intro hdouble",
                "specialize division_double_quotient_bit d",
                "specialize division_double_quotient_bit n",
                "specialize division_double_quotient_bit q",
                "specialize division_double_quotient_bit r",
                "specialize division_double_quotient_bit Q",
                "specialize division_double_quotient_bit R",
                "have hbit : Q = q + q \\/ Q = S (q + q)",
                "apply division_double_quotient_bit",
                "exact hsource",
                "exact hdouble",
                "cases hbit",
                "rewrite hbit_left",
                "specialize le_refl (q + q)",
                "exact le_refl",
                "rewrite hbit_right",
                "specialize le_succ (q + q)",
                "specialize le_succ (q + q)",
                "apply le_succ",
                "specialize le_refl (q + q)",
                "exact le_refl",
            ),
            "The doubled quotient is at least twice the original quotient.",
        ),
        spec(
            "division_double_quotient_upper",
            "forall d n q r Q R. "
            f"({upper_source}) -> ({upper_double}) -> ({upper_result})",
            ("division_double_quotient_bit", "le_refl", "le_succ"),
            (
                "intro d",
                "intro n",
                "intro q",
                "intro r",
                "intro Q",
                "intro R",
                "intro hsource",
                "intro hdouble",
                "specialize division_double_quotient_bit d",
                "specialize division_double_quotient_bit n",
                "specialize division_double_quotient_bit q",
                "specialize division_double_quotient_bit r",
                "specialize division_double_quotient_bit Q",
                "specialize division_double_quotient_bit R",
                "have hbit : Q = q + q \\/ Q = S (q + q)",
                "apply division_double_quotient_bit",
                "exact hsource",
                "exact hdouble",
                "cases hbit",
                "rewrite hbit_left",
                "specialize le_succ (q + q)",
                "specialize le_succ (q + q)",
                "apply le_succ",
                "specialize le_refl (q + q)",
                "exact le_refl",
                "rewrite hbit_right",
                "specialize le_refl (S (q + q))",
                "exact le_refl",
            ),
            "The doubled quotient is at most one above twice the original.",
        ),
        spec(
            "pow_le_pow_of_exponent_le",
            "forall p e f x y. "
            f"({power_base}) -> ({power_exponent}) -> ({power_left}) -> "
            f"({power_right}) -> ({power_result})",
            (
                "pow_exists",
                "add_comm",
                "pow_add",
                "one_le_pow",
                "le_mul_of_one_le_right",
            ),
            (
                "intro p",
                "intro e",
                "intro f",
                "intro x",
                "intro y",
                "intro hbase",
                "intro hexponent",
                "intro hx",
                "intro hy",
                "cases hexponent",
                f"have hgap_power : {gap_power}",
                "specialize pow_exists p",
                "specialize pow_exists x1",
                "exact pow_exists",
                "cases hgap_power",
                "have hsum : f = e + x1",
                "trans x1 + e",
                "symm",
                "exact hexponent_witness",
                "apply add_comm",
                "have hfactor : y = x * x2",
                "specialize pow_add p",
                "specialize pow_add e",
                "specialize pow_add x1",
                "specialize pow_add f",
                "specialize pow_add x",
                "specialize pow_add x2",
                "specialize pow_add y",
                "apply pow_add",
                "exact hsum",
                "exact hx",
                "exact hgap_power_witness",
                "exact hy",
                f"have hgap_order : {gap_power_order}",
                "specialize one_le_pow p",
                "specialize one_le_pow x1",
                "specialize one_le_pow x2",
                "apply one_le_pow",
                "exact hbase",
                "exact hgap_power_witness",
                f"have hproduct_order : {product_order}",
                "specialize le_mul_of_one_le_right x",
                "specialize le_mul_of_one_le_right x2",
                "apply le_mul_of_one_le_right",
                "exact hgap_order",
                "rewrite hfactor",
                "exact hproduct_order",
            ),
            "Relational powers are monotone in the exponent above base one.",
        ),
        spec(
            "pow_tail_strict_of_square",
            "forall p e x s n. "
            f"({tail_base}) -> ({tail_exponent}) -> ({square_power}) -> "
            f"({tail_power}) -> ({tail_source}) -> ({tail_result})",
            ("pow_le_pow_of_exponent_le", "lt_of_lt_of_le"),
            (
                "intro p",
                "intro e",
                "intro x",
                "intro s",
                "intro n",
                "intro hbase",
                "intro hexponent",
                "intro hsquare",
                "intro hpower",
                "intro hstrict",
                f"have hpower_order : {square_order}",
                "specialize pow_le_pow_of_exponent_le p",
                "specialize pow_le_pow_of_exponent_le 2",
                "specialize pow_le_pow_of_exponent_le e",
                "specialize pow_le_pow_of_exponent_le s",
                "specialize pow_le_pow_of_exponent_le x",
                "apply pow_le_pow_of_exponent_le",
                "exact hbase",
                "exact hexponent",
                "exact hsquare",
                "exact hpower",
                "specialize lt_of_lt_of_le n",
                "specialize lt_of_lt_of_le s",
                "specialize lt_of_lt_of_le x",
                "apply lt_of_lt_of_le",
                "exact hstrict",
                "exact hpower_order",
            ),
            "Every exponent-two-or-larger power lies above the square tail.",
        ),
    )


__all__ = ["make_bertrand_b5_order_quotient_candidate_theorems"]
