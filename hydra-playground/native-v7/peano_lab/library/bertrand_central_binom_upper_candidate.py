"""Capacity-safe upper bounds for central and odd-middle binomials.

The six rows below package the expensive recurrence and double-middle laws
once, prove the strong central estimate ``2 * C(2n,n) <= 4^n`` for positive
indices, and derive ``C(2n+1,n) <= 4^n``.  Every readable relation expands
to first-order Peano arithmetic before parsing.  This module creates no
trusted primitive, authority enrollment, or checked-use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)
from peano_lab.library.bertrand_choose_foundation_candidate import (
    _choose_relation_term,
    _le_term,
)
from peano_lab.library.power_algebra_theorems import _power_terms


CENTRAL_BINOM_STRONG_UPPER_STEP = "central_binom_strong_upper_step"
CENTRAL_BINOM_RECURRENCE_DOUBLE_BUNDLE = (
    "central_binom_recurrence_double_bundle"
)
CENTRAL_BINOM_STRONG_UPPER_OF_LAWS = (
    "central_binom_strong_upper_of_laws"
)
CENTRAL_BINOM_UPPER_SUPPORT_PACKAGE = (
    "central_binom_upper_support_package"
)
CENTRAL_BINOM_STRONG_UPPER = "central_binom_strong_upper"
CENTRAL_BINOM_ODD_MIDDLE_LE_FOUR_POW = (
    "central_binom_odd_middle_le_four_pow"
)


def make_bertrand_central_binom_upper_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the packaged strong-central and odd-middle upper bounds."""

    step_variables = ("n", "c", "d", "q", "r")
    step_source = _le_term(
        "2 * c",
        "q",
        tag="bcbsus_source",
        variables=step_variables,
    )
    step_result = _le_term(
        "2 * d",
        "r",
        tag="bcbsus_result",
        variables=step_variables,
    )
    step_script = (
        "intro n",
        "intro c",
        "intro d",
        "intro q",
        "intro r",
        "intro hsource",
        "intro hrecurrence",
        "intro hpower_step",
        "have hsource_scaled : exists k. "
        "k + S (n + n) * (2 * c) = S (n + n) * q",
        "specialize mul_le_mul_left (2 * c)",
        "specialize mul_le_mul_left q",
        "specialize mul_le_mul_left (S (n + n))",
        "apply mul_le_mul_left",
        "exact hsource",
        "have hcombined : exists k. "
        "k + S (n + n) * (2 * c) = (2 * S n) * q",
        "specialize le_trans (S (n + n) * (2 * c))",
        "specialize le_trans (S (n + n) * q)",
        "specialize le_trans ((2 * S n) * q)",
        "apply le_trans",
        "exact hsource_scaled",
        "specialize mul_le_mul_right (S (n + n))",
        "specialize mul_le_mul_right (2 * S n)",
        "specialize mul_le_mul_right q",
        "apply mul_le_mul_right",
        "exists 1",
        "specialize two_mul_eq_add_self (S n)",
        "rewrite two_mul_eq_add_self",
        "rewrite PA4",
        "rewrite PA4",
        "specialize add_assoc 1",
        "specialize add_assoc n",
        "specialize add_assoc n",
        "rewrite <- add_assoc",
        "specialize add_succ_left 0",
        "specialize add_succ_left n",
        "rewrite add_succ_left",
        "specialize zero_add n",
        "rewrite zero_add",
        "refl",
        "have hleft_align : "
        "(2 * S (n + n)) * c = S (n + n) * (2 * c)",
        "trans 2 * (S (n + n) * c)",
        "apply mul_assoc",
        "trans (S (n + n) * c) * 2",
        "apply mul_comm",
        "trans S (n + n) * (c * 2)",
        "apply mul_assoc",
        "have hcomm_c_two : c * 2 = 2 * c",
        "apply mul_comm",
        "rewrite hcomm_c_two",
        "refl",
        "have hrecurrence_aligned : "
        "S n * d = S (n + n) * (2 * c)",
        "trans (2 * S (n + n)) * c",
        "exact hrecurrence",
        "exact hleft_align",
        "have hright_align : (2 * S n) * q = S n * (2 * q)",
        "trans 2 * (S n * q)",
        "apply mul_assoc",
        "trans (S n * q) * 2",
        "apply mul_comm",
        "trans S n * (q * 2)",
        "apply mul_assoc",
        "have hcomm_q_two : q * 2 = 2 * q",
        "apply mul_comm",
        "rewrite hcomm_q_two",
        "refl",
        "rewrite <- hrecurrence_aligned at hcombined",
        "rewrite hright_align at hcombined",
        "have hhalf : exists k. k + d = 2 * q",
        "specialize mul_le_cancel_left_nonzero (S n)",
        "specialize mul_le_cancel_left_nonzero d",
        "specialize mul_le_cancel_left_nonzero (2 * q)",
        "apply mul_le_cancel_left_nonzero",
        "specialize succ_ne_zero n",
        "exact succ_ne_zero",
        "exact hcombined",
        "have hdouble : exists k. k + 2 * d = 2 * (2 * q)",
        "specialize mul_le_mul_left d",
        "specialize mul_le_mul_left (2 * q)",
        "specialize mul_le_mul_left 2",
        "apply mul_le_mul_left",
        "exact hhalf",
        "have hfour : 2 * (2 * q) = q * 4",
        "trans (2 * 2) * q",
        "symm",
        "apply mul_assoc",
        "trans 4 * q",
        "have htwo_two : 2 * 2 = 4",
        "norm_num",
        "rewrite htwo_two",
        "refl",
        "apply mul_comm",
        "rewrite hfour at hdouble",
        "rewrite hpower_step",
        "exact hdouble",
    )

    law_variables = ("n", "c", "d", "m")
    law_predecessor = _central_binom_relation_term(
        "n",
        "c",
        tag="bcbrdb_predecessor",
        variables=law_variables,
    )
    law_successor = _central_binom_relation_term(
        "S n",
        "d",
        tag="bcbrdb_successor",
        variables=law_variables,
    )
    law_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcbrdb_middle",
        variables=law_variables,
    )
    central_recurrence = (
        "forall n c d. "
        f"({law_predecessor}) -> ({law_successor}) -> "
        "S n * d = (2 * S (n + n)) * c"
    )
    double_functional = (
        "forall n d m. "
        f"({law_successor}) -> ({law_middle}) -> d = m + m"
    )
    bundle_formula = f"(({central_recurrence}) /\\ ({double_functional}))"

    bundle_script = (
        "split",
        "intro n",
        "intro c",
        "intro d",
        "intro hpredecessor",
        "intro hsuccessor",
        f"have hmiddle : exists m. (({law_middle}) /\\ d = m + m)",
        "specialize central_binom_succ_double_middle n",
        "specialize central_binom_succ_double_middle d",
        "apply central_binom_succ_double_middle",
        "exact hsuccessor",
        "cases hmiddle",
        "cases hmiddle_witness",
        "have hweighted : S n * x = S (n + n) * c",
        "specialize choose_weighted_vertical (n + n)",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical n",
        "specialize choose_weighted_vertical c",
        "specialize choose_weighted_vertical x",
        "apply choose_weighted_vertical",
        "refl",
        "exact hpredecessor",
        "exact hmiddle_witness_left",
        "rewrite hmiddle_witness_right",
        "trans S n * x + S n * x",
        "apply mul_add",
        "rewrite hweighted",
        "rewrite hweighted",
        "trans 2 * (S (n + n) * c)",
        "specialize two_mul_eq_add_self (S (n + n) * c)",
        "symm",
        "exact two_mul_eq_add_self",
        "specialize mul_assoc 2",
        "specialize mul_assoc (S (n + n))",
        "specialize mul_assoc c",
        "symm",
        "exact mul_assoc",
        "intro n",
        "intro d",
        "intro m",
        "intro hsuccessor",
        "intro hmiddle_given",
        f"have hmiddle : exists m. (({law_middle}) /\\ d = m + m)",
        "specialize central_binom_succ_double_middle n",
        "specialize central_binom_succ_double_middle d",
        "apply central_binom_succ_double_middle",
        "exact hsuccessor",
        "cases hmiddle",
        "cases hmiddle_witness",
        "have heq : x = m",
        "specialize choose_functional (S (n + n))",
        "specialize choose_functional n",
        "specialize choose_functional x",
        "specialize choose_functional m",
        "apply choose_functional",
        "exact hmiddle_witness_left",
        "exact hmiddle_given",
        "trans x + x",
        "exact hmiddle_witness_right",
        "congr",
        "exact heq",
        "exact heq",
    )

    exists_variables = ("n", "z")
    exists_relation = _central_binom_relation_term(
        "n",
        "z",
        tag="bcbsuo_exists",
        variables=exists_variables,
    )
    central_exists = f"forall n. exists z. ({exists_relation})"

    upper_variables = ("n", "c", "q")
    upper_central = _central_binom_relation_term(
        "S n",
        "c",
        tag="bcbsuo_central",
        variables=upper_variables,
    )
    upper_power = _power_terms(
        "4",
        "S n",
        "q",
        tag="bcbsuo_power",
    )
    upper_result = _le_term(
        "2 * c",
        "q",
        tag="bcbsuo_result",
        variables=upper_variables,
    )
    strong_formula = (
        "forall n c q. "
        f"({upper_central}) -> ({upper_power}) -> ({upper_result})"
    )

    base_central = _central_binom_relation_term(
        "0",
        "a",
        tag="bcbsuo_base_central",
        variables=upper_variables + ("a",),
    )
    base_power = _power_terms(
        "4",
        "0",
        "r",
        tag="bcbsuo_base_power",
    )
    step_central = _central_binom_relation_term(
        "S n",
        "a",
        tag="bcbsuo_step_central",
        variables=upper_variables + ("a", "r"),
    )
    step_power = _power_terms(
        "4",
        "S n",
        "r",
        tag="bcbsuo_step_power",
    )
    strong_script = (
        "intro hrecurrence",
        "intro hcentral_exists",
        "induction n",
        "intro c",
        "intro q",
        "intro hcentral",
        "intro hpower",
        f"have hzero_exists : exists a. ({base_central})",
        "apply hcentral_exists",
        "cases hzero_exists",
        "have hzero_value : x = 1",
        "apply central_binom_zero",
        "exact hzero_exists_witness",
        "have hrecurrence_zero : "
        "S 0 * c = (2 * S (0 + 0)) * x",
        "apply hrecurrence",
        "exact hzero_exists_witness",
        "exact hcentral",
        "rewrite hzero_value at hrecurrence_zero",
        "specialize one_mul c",
        "rewrite one_mul at hrecurrence_zero",
        "have hcentral_value : c = 2",
        "trans (2 * S (0 + 0)) * 1",
        "exact hrecurrence_zero",
        "norm_num",
        f"have hpower_step : exists r. ({base_power}) /\\ q = r * 4",
        "specialize pow_successor_decompose 4",
        "specialize pow_successor_decompose 0",
        "specialize pow_successor_decompose 1",
        "specialize pow_successor_decompose q",
        "apply pow_successor_decompose",
        "refl",
        "exact hpower",
        "cases hpower_step",
        "cases hpower_step_witness",
        "have hpower_zero : x1 = 1",
        "specialize pow_zero 4",
        "specialize pow_zero 0",
        "specialize pow_zero x1",
        "apply pow_zero",
        "refl",
        "exact hpower_step_witness_left",
        "have hpower_value : q = 4",
        "rewrite hpower_zero at hpower_step_witness_right",
        "trans 1 * 4",
        "exact hpower_step_witness_right",
        "norm_num",
        "rewrite hcentral_value",
        "rewrite hpower_value",
        "have htwo_two : 2 * 2 = 4",
        "norm_num",
        "rewrite htwo_two",
        "specialize le_refl 4",
        "exact le_refl",
        "intro c",
        "intro q",
        "intro hcentral",
        "intro hpower",
        f"have hprevious_exists : exists a. ({step_central})",
        "apply hcentral_exists",
        "cases hprevious_exists",
        f"have hpower_step : exists r. ({step_power}) /\\ q = r * 4",
        "specialize pow_successor_decompose 4",
        "specialize pow_successor_decompose (S n)",
        "specialize pow_successor_decompose (S (S n))",
        "specialize pow_successor_decompose q",
        "apply pow_successor_decompose",
        "refl",
        "exact hpower",
        "cases hpower_step",
        "cases hpower_step_witness",
        "have hprevious_bound : exists k. k + 2 * x = x1",
        "specialize IH x",
        "specialize IH x1",
        "apply IH",
        "exact hprevious_exists_witness",
        "exact hpower_step_witness_left",
        "have hrecurrence_step : "
        "S (S n) * c = (2 * S (S n + S n)) * x",
        "apply hrecurrence",
        "exact hprevious_exists_witness",
        "exact hcentral",
        "specialize central_binom_strong_upper_step (S n)",
        "specialize central_binom_strong_upper_step x",
        "specialize central_binom_strong_upper_step c",
        "specialize central_binom_strong_upper_step x1",
        "specialize central_binom_strong_upper_step q",
        "apply central_binom_strong_upper_step",
        "exact hprevious_bound",
        "exact hrecurrence_step",
        "exact hpower_step_witness_right",
    )

    package_formula = f"(({bundle_formula}) /\\ ({central_exists}))"
    package_script = (
        "split",
        "exact central_binom_recurrence_double_bundle",
        "exact central_binom_exists",
    )

    public_strong_script = (
        f"have hpackage : {package_formula}",
        "exact central_binom_upper_support_package",
        "cases hpackage",
        "cases hpackage_left",
        "apply central_binom_strong_upper_of_laws",
        "exact hpackage_left_left",
        "exact hpackage_right",
    )

    odd_variables = ("n", "m", "q")
    odd_middle = _choose_relation_term(
        "S (n + n)",
        "n",
        "m",
        tag="bcomlfp_middle",
        variables=odd_variables,
    )
    odd_power = _power_terms(
        "4",
        "n",
        "q",
        tag="bcomlfp_power",
    )
    odd_result = _le_term(
        "m",
        "q",
        tag="bcomlfp_result",
        variables=odd_variables,
    )
    odd_central = _central_binom_relation_term(
        "S n",
        "d",
        tag="bcomlfp_central",
        variables=odd_variables + ("d",),
    )
    odd_successor_power = _power_terms(
        "4",
        "S n",
        "q * 4",
        tag="bcomlfp_successor_power",
    )
    odd_strong = _le_term(
        "2 * x",
        "q * 4",
        tag="bcomlfp_strong",
        variables=odd_variables + ("x",),
    )
    odd_script = (
        "intro n",
        "intro m",
        "intro q",
        "intro hmiddle",
        "intro hpower",
        f"have hpackage : {package_formula}",
        "exact central_binom_upper_support_package",
        "cases hpackage",
        "cases hpackage_left",
        f"have hcentral_exists : exists d. ({odd_central})",
        "apply hpackage_right",
        "cases hcentral_exists",
        "have hdouble : x = m + m",
        "apply hpackage_left_right",
        "exact hcentral_exists_witness",
        "exact hmiddle",
        f"have hsuccessor_power : {odd_successor_power}",
        "specialize pow_successor_compose 4",
        "specialize pow_successor_compose n",
        "specialize pow_successor_compose q",
        "specialize pow_successor_compose (q * 4)",
        "apply pow_successor_compose",
        "exact hpower",
        "refl",
        f"have hstrong_all : {strong_formula}",
        "apply central_binom_strong_upper_of_laws",
        "exact hpackage_left_left",
        "exact hpackage_right",
        f"have hstrong : {odd_strong}",
        "specialize hstrong_all n",
        "specialize hstrong_all x",
        "specialize hstrong_all (q * 4)",
        "apply hstrong_all",
        "exact hcentral_exists_witness",
        "exact hsuccessor_power",
        "have hleft : 2 * (m + m) = 4 * m",
        "trans 2 * m + 2 * m",
        "apply mul_add",
        "trans 2 * (2 * m)",
        "specialize two_mul_eq_add_self (2 * m)",
        "symm",
        "exact two_mul_eq_add_self",
        "trans (2 * 2) * m",
        "symm",
        "apply mul_assoc",
        "have htwo_two : 2 * 2 = 4",
        "norm_num",
        "rewrite htwo_two",
        "refl",
        "have hright : q * 4 = 4 * q",
        "apply mul_comm",
        "rewrite hdouble at hstrong",
        "rewrite hleft at hstrong",
        "rewrite hright at hstrong",
        "specialize mul_le_cancel_left_nonzero 4",
        "specialize mul_le_cancel_left_nonzero m",
        "specialize mul_le_cancel_left_nonzero q",
        "apply mul_le_cancel_left_nonzero",
        "intro hfour_zero",
        "apply PA1",
        "exact hfour_zero",
        "exact hstrong",
    )

    return (
        spec(
            CENTRAL_BINOM_STRONG_UPPER_STEP,
            "forall n c d q r. "
            f"({step_source}) -> "
            "S n * d = (2 * S (n + n)) * c -> "
            f"r = q * 4 -> ({step_result})",
            (
                "zero_add",
                "add_succ_left",
                "add_assoc",
                "mul_comm",
                "mul_assoc",
                "two_mul_eq_add_self",
                "mul_le_mul_left",
                "mul_le_mul_right",
                "le_trans",
                "succ_ne_zero",
                "mul_le_cancel_left_nonzero",
            ),
            step_script,
            "The weighted recurrence preserves the strong factor-two bound.",
        ),
        spec(
            CENTRAL_BINOM_RECURRENCE_DOUBLE_BUNDLE,
            bundle_formula,
            (
                "mul_add",
                "mul_assoc",
                "two_mul_eq_add_self",
                "central_binom_succ_double_middle",
                "choose_weighted_vertical",
                "choose_functional",
            ),
            bundle_script,
            "The recurrence and functional double-middle law share support.",
        ),
        spec(
            CENTRAL_BINOM_STRONG_UPPER_OF_LAWS,
            f"({central_recurrence}) -> ({central_exists}) -> "
            f"({strong_formula})",
            (
                "one_mul",
                "le_refl",
                "pow_zero",
                "pow_successor_decompose",
                "central_binom_zero",
                CENTRAL_BINOM_STRONG_UPPER_STEP,
            ),
            strong_script,
            "Recurrence and totality imply the positive-index strong bound.",
        ),
        spec(
            CENTRAL_BINOM_UPPER_SUPPORT_PACKAGE,
            package_formula,
            (
                CENTRAL_BINOM_RECURRENCE_DOUBLE_BUNDLE,
                "central_binom_exists",
            ),
            package_script,
            "The expensive recurrence, middle, and totality laws close once.",
        ),
        spec(
            CENTRAL_BINOM_STRONG_UPPER,
            strong_formula,
            (
                CENTRAL_BINOM_UPPER_SUPPORT_PACKAGE,
                CENTRAL_BINOM_STRONG_UPPER_OF_LAWS,
            ),
            public_strong_script,
            "Twice a positive-index central binomial is at most four-power.",
        ),
        spec(
            CENTRAL_BINOM_ODD_MIDDLE_LE_FOUR_POW,
            "forall n m q. "
            f"({odd_middle}) -> ({odd_power}) -> ({odd_result})",
            (
                "mul_add",
                "mul_assoc",
                "mul_comm",
                "two_mul_eq_add_self",
                "mul_le_cancel_left_nonzero",
                "pow_successor_compose",
                CENTRAL_BINOM_UPPER_SUPPORT_PACKAGE,
                CENTRAL_BINOM_STRONG_UPPER_OF_LAWS,
            ),
            odd_script,
            "The odd-row middle coefficient is at most four to the half-row.",
        ),
    )


__all__ = ["make_bertrand_central_binom_upper_candidate_theorems"]
