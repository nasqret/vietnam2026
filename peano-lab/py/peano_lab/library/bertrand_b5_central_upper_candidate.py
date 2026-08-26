"""Range-wise Product bounds for the Bertrand B5 contradiction.

This candidate tranche turns the reviewed pointwise contribution trichotomy
into quantitative bounds on the three Product ranges.  Its final two rows are
the RFC B5 factorization and central-binomial upper-bound interfaces.  Every
readable relation is expanded into ordinary first-order Peano arithmetic;
importing this module grants no theorem authority or edition membership.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b5_contribution_split_candidate import (
    _interval_relation_term,
)
from .bertrand_b5_order_quotient_candidate import _divrem_term
from .bertrand_ceil_sqrt_candidate import floor_sqrt_relation
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_central_binom_prime_support_candidate import (
    _no_bertrand_closed_term,
)
from .bertrand_choose_foundation_candidate import _le_term, _lt_term
from .bertrand_power_valuation_candidate import _power_terms
from .bertrand_prime_contribution_candidate import (
    _prime_contribution_choice_term,
    _prime_contribution_product_term,
)
from .bertrand_primorial_foundation_candidate import (
    _beta_at_term,
    _primorial_factor_choice_term,
    _primorial_relation_term,
)
from .bertrand_primorial_interval_candidate import (
    _primorial_interval_relation_term,
)
from .finite_fold_surface import _product_relation_term


BETA_PRODUCT_ALL_ONE_EXACT = "beta_product_all_one_exact"
NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE = (
    "no_bertrand_small_contribution_choice_le_double"
)
NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR = (
    "no_bertrand_middle_contribution_choice_le_selector"
)
NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE = (
    "no_bertrand_high_contribution_choice_eq_one"
)
NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER = (
    "no_bertrand_small_contribution_product_le_power"
)
NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL = (
    "no_bertrand_middle_contribution_interval_le_primorial_interval"
)
NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW = (
    "no_bertrand_middle_contribution_interval_le_four_pow"
)
NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE = (
    "no_bertrand_high_contribution_interval_eq_one"
)
CENTRAL_BINOM_FACTORIZATION_SMALL = "central_binom_factorization_small"
CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME = (
    "central_binom_le_of_no_bertrand_prime"
)


def make_bertrand_b5_central_upper_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered B5 range-product bounds."""

    one_variables = ("b", "c", "l", "z")
    one_bound = _lt_term(
        "i",
        "l",
        tag="b5bpao_bound",
        variables=one_variables + ("i", "a"),
    )
    one_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="b5bpao_entry",
        avoid=one_variables + ("i", "a"),
    )
    one_source = (
        f"forall i a. ({one_bound}) -> ({one_entry}) -> a = 1"
    )
    one_product = _product_relation_term(
        "b",
        "c",
        "l",
        "z",
        tag="b5bpao_product",
        avoid=one_variables,
    )
    one_previous_bound = _lt_term(
        "i",
        "l",
        tag="b5bpao_previous_bound",
        variables=one_variables + ("i", "a"),
    )
    one_previous_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "a",
        tag="b5bpao_previous_entry",
        avoid=one_variables + ("i", "a"),
    )
    one_previous = (
        f"forall i a. ({one_previous_bound}) -> "
        f"({one_previous_entry}) -> a = 1"
    )
    one_decomposition_entry = _beta_at_term(
        "b",
        "c",
        "l",
        "a",
        tag="b5bpao_decomposition_entry",
        avoid=one_variables + ("a", "r"),
    )
    one_decomposition_product = _product_relation_term(
        "b",
        "c",
        "l",
        "r",
        tag="b5bpao_decomposition_product",
        avoid=one_variables + ("a", "r"),
    )
    one_decomposition = (
        f"exists a r. ({one_decomposition_entry}) /\\ "
        f"(({one_decomposition_product}) /\\ z = r * a)"
    )

    small_variables = ("n", "s", "q", "r", "C", "i", "a")
    small_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbscc_exclusion", variables=small_variables
    )
    small_positive = _lt_term(
        "2", "n", tag="b5nbscc_positive", variables=small_variables
    )
    small_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbscc_floor"
    )
    small_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbscc_division",
        variables=small_variables,
    )
    small_central = _central_binom_relation_term(
        "n", "C", tag="b5nbscc_central", variables=small_variables
    )
    small_index = _lt_term(
        "i", "s", tag="b5nbscc_index", variables=small_variables
    )
    small_choice = _prime_contribution_choice_term(
        "C", "i", "a", tag="b5nbscc_choice", variables=small_variables
    )
    small_result = _le_term(
        "a", "n + n", tag="b5nbscc_result", variables=small_variables
    )
    small_si_s = _le_term(
        "S i", "s", tag="b5nbscc_si_s", variables=small_variables
    )
    small_s_double = _le_term(
        "n", "n + n", tag="b5nbscc_n_double", variables=small_variables
    )

    middle_variables = (
        "n",
        "s",
        "q",
        "r",
        "C",
        "i",
        "a",
        "p",
    )
    middle_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbmcc_exclusion", variables=middle_variables
    )
    middle_positive = _lt_term(
        "2", "n", tag="b5nbmcc_positive", variables=middle_variables
    )
    middle_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbmcc_floor"
    )
    middle_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbmcc_division",
        variables=middle_variables,
    )
    middle_central = _central_binom_relation_term(
        "n", "C", tag="b5nbmcc_central", variables=middle_variables
    )
    middle_above = _lt_term(
        "s", "S i", tag="b5nbmcc_above", variables=middle_variables
    )
    middle_bound = _le_term(
        "S i", "q", tag="b5nbmcc_bound", variables=middle_variables
    )
    middle_choice = _prime_contribution_choice_term(
        "C", "i", "a", tag="b5nbmcc_choice", variables=middle_variables
    )
    middle_selector = _primorial_factor_choice_term(
        "i", "p", tag="b5nbmcc_selector", variables=middle_variables
    )
    middle_result = _le_term(
        "a", "p", tag="b5nbmcc_result", variables=middle_variables
    )
    middle_small_bound = _le_term(
        "S i", "s", tag="b5nbmcc_small_bound", variables=middle_variables
    )

    high_variables = ("n", "s", "q", "r", "C", "i", "a")
    high_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbhcc_exclusion", variables=high_variables
    )
    high_positive = _lt_term(
        "2", "n", tag="b5nbhcc_positive", variables=high_variables
    )
    high_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbhcc_floor"
    )
    high_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbhcc_division",
        variables=high_variables,
    )
    high_central = _central_binom_relation_term(
        "n", "C", tag="b5nbhcc_central", variables=high_variables
    )
    high_above = _lt_term(
        "q", "S i", tag="b5nbhcc_above", variables=high_variables
    )
    high_choice = _prime_contribution_choice_term(
        "C", "i", "a", tag="b5nbhcc_choice", variables=high_variables
    )
    high_root_bound = _le_term(
        "s", "q", tag="b5nbhcc_root_bound", variables=high_variables
    )
    high_small_bound = _le_term(
        "S i", "s", tag="b5nbhcc_small_bound", variables=high_variables
    )
    high_middle_bound = _le_term(
        "S i", "q", tag="b5nbhcc_middle_bound", variables=high_variables
    )

    small_product_variables = ("n", "s", "q", "r", "C", "z", "A")
    sp_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbscplp_exclusion", variables=small_product_variables
    )
    sp_positive = _lt_term(
        "2", "n", tag="b5nbscplp_positive", variables=small_product_variables
    )
    sp_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbscplp_floor"
    )
    sp_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbscplp_division",
        variables=small_product_variables,
    )
    sp_central = _central_binom_relation_term(
        "n", "C", tag="b5nbscplp_central", variables=small_product_variables
    )
    sp_source = _prime_contribution_product_term(
        "C", "s", "z", tag="b5nbscplp_source", variables=small_product_variables
    )
    sp_power = _power_terms("n + n", "s", "A", tag="b5nbscplp_power")
    sp_result = _le_term(
        "z", "A", tag="b5nbscplp_result", variables=small_product_variables
    )
    sp_bound = _lt_term(
        "i",
        "s",
        tag="b5nbscplp_uniform_bound",
        variables=small_product_variables + ("x", "x1", "i", "a"),
    )
    sp_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "a",
        tag="b5nbscplp_uniform_decoded",
        avoid=small_product_variables + ("x", "x1", "i", "a"),
    )
    sp_factor_result = _le_term(
        "a",
        "n + n",
        tag="b5nbscplp_uniform_result",
        variables=small_product_variables + ("x", "x1", "i", "a"),
    )
    sp_uniform = (
        f"forall i a. ({sp_bound}) -> ({sp_decoded}) -> "
        f"({sp_factor_result})"
    )
    sp_entry_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "p",
        tag="b5nbscplp_entry_decoded",
        avoid=small_product_variables + ("x", "x1", "i", "a", "p"),
    )
    sp_entry_choice = _prime_contribution_choice_term(
        "C",
        "i",
        "p",
        tag="b5nbscplp_entry_choice",
        variables=small_product_variables + ("x", "x1", "i", "a", "p"),
    )
    sp_entry = (
        f"exists p. ({sp_entry_decoded}) /\\ ({sp_entry_choice})"
    )

    middle_product_variables = (
        "n",
        "s",
        "q",
        "r",
        "C",
        "g",
        "y",
        "P",
    )
    mp_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbmcilpi_exclusion", variables=middle_product_variables
    )
    mp_positive = _lt_term(
        "2", "n", tag="b5nbmcilpi_positive", variables=middle_product_variables
    )
    mp_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbmcilpi_floor"
    )
    mp_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbmcilpi_division",
        variables=middle_product_variables,
    )
    mp_central = _central_binom_relation_term(
        "n", "C", tag="b5nbmcilpi_central", variables=middle_product_variables
    )
    mp_contribution = _interval_relation_term(
        "C",
        "s",
        "g",
        "y",
        tag="b5nbmcilpi_contribution",
        variables=middle_product_variables,
    )
    mp_primorial = _primorial_interval_relation_term(
        "s",
        "g",
        "P",
        tag="b5nbmcilpi_primorial",
        variables=middle_product_variables,
    )
    mp_result = _le_term(
        "y", "P", tag="b5nbmcilpi_result", variables=middle_product_variables
    )
    mp_pointwise_bound = _lt_term(
        "i",
        "g",
        tag="b5nbmcilpi_pointwise_bound",
        variables=middle_product_variables
        + ("b", "c", "d", "e", "i", "a", "p"),
    )
    mp_pointwise_left = _beta_at_term(
        "x",
        "x1",
        "i",
        "a",
        tag="b5nbmcilpi_pointwise_left",
        avoid=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p"),
    )
    mp_pointwise_right = _beta_at_term(
        "x2",
        "x3",
        "i",
        "p",
        tag="b5nbmcilpi_pointwise_right",
        avoid=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p"),
    )
    mp_pointwise_result = _le_term(
        "a",
        "p",
        tag="b5nbmcilpi_pointwise_result",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p"),
    )
    mp_pointwise = (
        f"forall i a p. ({mp_pointwise_bound}) -> "
        f"({mp_pointwise_left}) -> ({mp_pointwise_right}) -> "
        f"({mp_pointwise_result})"
    )
    mp_left_entry_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "u",
        tag="b5nbmcilpi_left_entry_decoded",
        avoid=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u"),
    )
    mp_left_entry_choice = _prime_contribution_choice_term(
        "C",
        "s + i",
        "u",
        tag="b5nbmcilpi_left_entry_choice",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u"),
    )
    mp_left_entry = (
        f"exists u. ({mp_left_entry_decoded}) /\\ ({mp_left_entry_choice})"
    )
    mp_right_entry_decoded = _beta_at_term(
        "x2",
        "x3",
        "i",
        "v",
        tag="b5nbmcilpi_right_entry_decoded",
        avoid=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u", "v"),
    )
    mp_right_entry_choice = _primorial_factor_choice_term(
        "s + i",
        "v",
        tag="b5nbmcilpi_right_entry_choice",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u", "v"),
    )
    mp_right_entry = (
        f"exists v. ({mp_right_entry_decoded}) /\\ "
        f"({mp_right_entry_choice})"
    )
    mp_global_above = _lt_term(
        "s",
        "S (s + i)",
        tag="b5nbmcilpi_global_above",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u", "v"),
    )
    mp_global_bound = _le_term(
        "S (s + i)",
        "q",
        tag="b5nbmcilpi_global_bound",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u", "v"),
    )
    mp_raw_bound = _le_term(
        "s + S i",
        "s + g",
        tag="b5nbmcilpi_raw_bound",
        variables=middle_product_variables
        + ("x", "x1", "x2", "x3", "i", "a", "p", "u", "v"),
    )

    middle_power_variables = ("n", "s", "q", "r", "C", "g", "y", "B")
    mfp_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbmcilfp_exclusion", variables=middle_power_variables
    )
    mfp_positive = _lt_term(
        "2", "n", tag="b5nbmcilfp_positive", variables=middle_power_variables
    )
    mfp_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbmcilfp_floor"
    )
    mfp_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbmcilfp_division",
        variables=middle_power_variables,
    )
    mfp_central = _central_binom_relation_term(
        "n", "C", tag="b5nbmcilfp_central", variables=middle_power_variables
    )
    mfp_contribution = _interval_relation_term(
        "C",
        "s",
        "g",
        "y",
        tag="b5nbmcilfp_contribution",
        variables=middle_power_variables,
    )
    mfp_power = _power_terms("4", "q", "B", tag="b5nbmcilfp_power")
    mfp_result = _le_term(
        "y", "B", tag="b5nbmcilfp_result", variables=middle_power_variables
    )
    mfp_primorial_q = _primorial_relation_term(
        "q",
        "P",
        tag="b5nbmcilfp_primorial_q",
        variables=middle_power_variables + ("P",),
    )
    mfp_primorial_sum = _primorial_relation_term(
        "s + g",
        "x",
        tag="b5nbmcilfp_primorial_sum",
        variables=middle_power_variables + ("x",),
    )
    mfp_prefix = _primorial_relation_term(
        "s",
        "u",
        tag="b5nbmcilfp_prefix",
        variables=middle_power_variables + ("x", "u", "v"),
    )
    mfp_interval = _primorial_interval_relation_term(
        "s",
        "g",
        "v",
        tag="b5nbmcilfp_interval",
        variables=middle_power_variables + ("x", "u", "v"),
    )
    mfp_split = (
        f"exists u v. ({mfp_prefix}) /\\ "
        f"(({mfp_interval}) /\\ x = u * v)"
    )
    mfp_y_v = _le_term(
        "y",
        "x2",
        tag="b5nbmcilfp_y_v",
        variables=middle_power_variables + ("x", "x1", "x2"),
    )
    mfp_v_product = _le_term(
        "x2",
        "x1 * x2",
        tag="b5nbmcilfp_v_product",
        variables=middle_power_variables + ("x", "x1", "x2"),
    )
    mfp_y_p = _le_term(
        "y",
        "x",
        tag="b5nbmcilfp_y_p",
        variables=middle_power_variables + ("x", "x1", "x2"),
    )
    mfp_p_b = _le_term(
        "x",
        "B",
        tag="b5nbmcilfp_p_b",
        variables=middle_power_variables + ("x", "x1", "x2"),
    )

    high_product_variables = ("n", "s", "q", "r", "C", "h", "w")
    hp_exclusion = _no_bertrand_closed_term(
        "n", tag="b5nbhcieu_exclusion", variables=high_product_variables
    )
    hp_positive = _lt_term(
        "2", "n", tag="b5nbhcieu_positive", variables=high_product_variables
    )
    hp_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5nbhcieu_floor"
    )
    hp_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5nbhcieu_division",
        variables=high_product_variables,
    )
    hp_central = _central_binom_relation_term(
        "n", "C", tag="b5nbhcieu_central", variables=high_product_variables
    )
    hp_interval = _interval_relation_term(
        "C",
        "q",
        "h",
        "w",
        tag="b5nbhcieu_interval",
        variables=high_product_variables,
    )
    hp_all_bound = _lt_term(
        "i",
        "h",
        tag="b5nbhcieu_all_bound",
        variables=high_product_variables + ("b", "c", "i", "a"),
    )
    hp_all_entry = _beta_at_term(
        "x",
        "x1",
        "i",
        "a",
        tag="b5nbhcieu_all_entry",
        avoid=high_product_variables + ("x", "x1", "i", "a"),
    )
    hp_all = (
        f"forall i a. ({hp_all_bound}) -> ({hp_all_entry}) -> a = 1"
    )
    hp_local_decoded = _beta_at_term(
        "x",
        "x1",
        "i",
        "p",
        tag="b5nbhcieu_local_decoded",
        avoid=high_product_variables + ("x", "x1", "i", "a", "p"),
    )
    hp_local_choice = _prime_contribution_choice_term(
        "C",
        "q + i",
        "p",
        tag="b5nbhcieu_local_choice",
        variables=high_product_variables + ("x", "x1", "i", "a", "p"),
    )
    hp_local = (
        f"exists p. ({hp_local_decoded}) /\\ ({hp_local_choice})"
    )
    hp_global_above = _lt_term(
        "q",
        "S (q + i)",
        tag="b5nbhcieu_global_above",
        variables=high_product_variables + ("x", "x1", "i", "a", "p"),
    )

    factor_variables = ("n", "s", "q", "r", "C", "g", "h", "z")
    factor_exclusion = _no_bertrand_closed_term(
        "n", tag="b5cbfs_exclusion", variables=factor_variables
    )
    factor_positive = _lt_term(
        "2", "n", tag="b5cbfs_positive", variables=factor_variables
    )
    factor_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5cbfs_floor"
    )
    factor_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5cbfs_division",
        variables=factor_variables,
    )
    factor_central = _central_binom_relation_term(
        "n", "C", tag="b5cbfs_central", variables=factor_variables
    )
    factor_source = _prime_contribution_product_term(
        "C", "n + n", "z", tag="b5cbfs_source", variables=factor_variables
    )
    factor_small = _prime_contribution_product_term(
        "C",
        "s",
        "x",
        tag="b5cbfs_small",
        variables=factor_variables + ("x", "y"),
    )
    factor_middle = _interval_relation_term(
        "C",
        "s",
        "g",
        "y",
        tag="b5cbfs_middle",
        variables=factor_variables + ("x", "y"),
    )
    factor_result = (
        f"exists x y. ({factor_small}) /\\ "
        f"(({factor_middle}) /\\ z = x * y)"
    )
    factor_outer_source = _prime_contribution_product_term(
        "C",
        "q + h",
        "z",
        tag="b5cbfs_outer_source",
        variables=factor_variables,
    )
    factor_outer_prefix = _prime_contribution_product_term(
        "C",
        "q",
        "x",
        tag="b5cbfs_outer_prefix",
        variables=factor_variables + ("x", "x1"),
    )
    factor_outer_high = _interval_relation_term(
        "C",
        "q",
        "h",
        "x1",
        tag="b5cbfs_outer_high",
        variables=factor_variables + ("x", "x1"),
    )
    factor_outer = (
        f"exists x x1. ({factor_outer_prefix}) /\\ "
        f"(({factor_outer_high}) /\\ z = x * x1)"
    )
    factor_inner_source = _prime_contribution_product_term(
        "C",
        "s + g",
        "x",
        tag="b5cbfs_inner_source",
        variables=factor_variables + ("x", "x1"),
    )
    factor_inner_small = _prime_contribution_product_term(
        "C",
        "s",
        "x2",
        tag="b5cbfs_inner_small",
        variables=factor_variables + ("x", "x1", "x2", "x3"),
    )
    factor_inner_middle = _interval_relation_term(
        "C",
        "s",
        "g",
        "x3",
        tag="b5cbfs_inner_middle",
        variables=factor_variables + ("x", "x1", "x2", "x3"),
    )
    factor_inner = (
        f"exists x2 x3. ({factor_inner_small}) /\\ "
        f"(({factor_inner_middle}) /\\ x = x2 * x3)"
    )

    final_variables = ("n", "s", "q", "r", "C", "A", "B")
    final_exclusion = _no_bertrand_closed_term(
        "n", tag="b5cblonbp_exclusion", variables=final_variables
    )
    final_positive = _lt_term(
        "2", "n", tag="b5cblonbp_positive", variables=final_variables
    )
    final_floor = floor_sqrt_relation(
        "n + n", "s", tag="b5cblonbp_floor"
    )
    final_division = _divrem_term(
        "3",
        "n + n",
        "q",
        "r",
        tag="b5cblonbp_division",
        variables=final_variables,
    )
    final_central = _central_binom_relation_term(
        "n", "C", tag="b5cblonbp_central", variables=final_variables
    )
    final_power_a = _power_terms("n + n", "s", "A", tag="b5cblonbp_power_a")
    final_power_b = _power_terms("4", "q", "B", tag="b5cblonbp_power_b")
    final_result = _le_term(
        "C", "A * B", tag="b5cblonbp_result", variables=final_variables
    )
    final_product = _prime_contribution_product_term(
        "C",
        "n + n",
        "z",
        tag="b5cblonbp_product",
        variables=final_variables + ("z",),
    )
    final_product_exists = (
        f"exists z. ({final_product}) /\\ C = z"
    )
    final_factor_small = _prime_contribution_product_term(
        "C",
        "s",
        "u",
        tag="b5cblonbp_small",
        variables=final_variables + ("x", "x1", "x2", "u", "v"),
    )
    final_factor_middle = _interval_relation_term(
        "C",
        "s",
        "x",
        "v",
        tag="b5cblonbp_middle",
        variables=final_variables + ("x", "x1", "x2", "u", "v"),
    )
    final_factorization = (
        f"exists u v. ({final_factor_small}) /\\ "
        f"(({final_factor_middle}) /\\ x2 = u * v)"
    )
    final_x_a = _le_term(
        "x3",
        "A",
        tag="b5cblonbp_x_a",
        variables=final_variables + ("x", "x1", "x2", "x3", "x4"),
    )
    final_y_b = _le_term(
        "x4",
        "B",
        tag="b5cblonbp_y_b",
        variables=final_variables + ("x", "x1", "x2", "x3", "x4"),
    )
    final_product_bound = _le_term(
        "x3 * x4",
        "A * B",
        tag="b5cblonbp_product_bound",
        variables=final_variables + ("x", "x1", "x2", "x3", "x4"),
    )

    return (
        spec(
            BETA_PRODUCT_ALL_ONE_EXACT,
            "forall b c l z. "
            f"({one_source}) -> ({one_product}) -> z = 1",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "mul_one",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro z",
                "intro hall",
                "intro hproduct",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero z",
                "apply beta_product_zero",
                "exact hproduct",
                "intro z",
                "intro hall",
                "intro hproduct",
                f"have hdecomposition : {one_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose z",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_right",
                f"have hprevious : {one_previous}",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize hall i",
                "specialize hall a",
                "apply hall",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
                "have hprefix_one : x1 = 1",
                "specialize IH x1",
                "apply IH",
                "exact hprevious",
                "exact hdecomposition_witness_witness_right_left",
                "have hfactor_one : x = 1",
                "specialize hall l",
                "specialize hall x",
                "apply hall",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_left",
                "rewrite hdecomposition_witness_witness_right_right",
                "rewrite hprefix_one",
                "rewrite hfactor_one",
                "specialize mul_one 1",
                "exact mul_one",
            ),
            "A Product whose decoded factors are all one is exactly one.",
        ),
        spec(
            NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
            "forall n s q r C i a. "
            f"({small_exclusion}) -> ({small_positive}) -> "
            f"({small_floor}) -> ({small_division}) -> "
            f"({small_central}) -> ({small_index}) -> "
            f"({small_choice}) -> ({small_result})",
            (
                "lt_not_le",
                "lt_to_le",
                "le_trans",
                "le_add_right",
                "no_bertrand_central_contribution_choice_ranges",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro i",
                "intro a",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hindex",
                "intro hchoice",
                "have hranges : "
                "((" + small_si_s + ") /\\ (" + small_result + ")) \\/ "
                "(((" + _lt_term(
                    "s",
                    "S i",
                    tag="b5nbscc_range_above",
                    variables=small_variables,
                ) + ") /\\ (" + _le_term(
                    "S i",
                    "q",
                    tag="b5nbscc_range_middle",
                    variables=small_variables,
                ) + ")) /\\ a = S i) \\/ a = 1",
                "specialize no_bertrand_central_contribution_choice_ranges n",
                "specialize no_bertrand_central_contribution_choice_ranges s",
                "specialize no_bertrand_central_contribution_choice_ranges q",
                "specialize no_bertrand_central_contribution_choice_ranges r",
                "specialize no_bertrand_central_contribution_choice_ranges C",
                "specialize no_bertrand_central_contribution_choice_ranges i",
                "specialize no_bertrand_central_contribution_choice_ranges a",
                "apply no_bertrand_central_contribution_choice_ranges",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hchoice",
                "cases hranges",
                "cases hranges_left",
                "cases hranges_left_left",
                "exact hranges_left_left_right",
                "cases hranges_left_right",
                "cases hranges_left_right_left",
                "exfalso",
                "specialize lt_not_le s",
                "specialize lt_not_le (S i)",
                "apply lt_not_le",
                "exact hranges_left_right_left_left",
                "exact hindex",
                "rewrite hranges_right",
                "have hone_two : "
                + _le_term(
                    "1",
                    "2",
                    tag="b5nbscc_one_two",
                    variables=small_variables,
                ),
                "exists 1",
                "norm_num",
                "have htwo_n : "
                + _le_term(
                    "2",
                    "n",
                    tag="b5nbscc_two_n",
                    variables=small_variables,
                ),
                "specialize lt_to_le 2",
                "specialize lt_to_le n",
                "apply lt_to_le",
                "exact hpositive",
                "have hone_n : "
                + _le_term(
                    "1",
                    "n",
                    tag="b5nbscc_one_n",
                    variables=small_variables,
                ),
                "specialize le_trans 1",
                "specialize le_trans 2",
                "specialize le_trans n",
                "apply le_trans",
                "exact hone_two",
                "exact htwo_n",
                f"have hn_double : {small_s_double}",
                "specialize le_add_right n",
                "specialize le_add_right n",
                "exact le_add_right",
                "specialize le_trans 1",
                "specialize le_trans n",
                "specialize le_trans (n + n)",
                "apply le_trans",
                "exact hone_n",
                "exact hn_double",
            ),
            "Every small-range contribution is bounded by the doubled row.",
        ),
        spec(
            NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
            "forall n s q r C i a p. "
            f"({middle_exclusion}) -> ({middle_positive}) -> "
            f"({middle_floor}) -> ({middle_division}) -> "
            f"({middle_central}) -> ({middle_above}) -> "
            f"({middle_bound}) -> ({middle_choice}) -> "
            f"({middle_selector}) -> ({middle_result})",
            (
                "lt_not_le",
                "le_refl",
                "no_bertrand_central_contribution_choice_ranges",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro i",
                "intro a",
                "intro p",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro habove",
                "intro hbound",
                "intro hchoice",
                "intro hselector",
                "cases hselector",
                "cases hselector_left",
                "have hranges : "
                "((" + middle_small_bound + ") /\\ (" + _le_term(
                    "a",
                    "n + n",
                    tag="b5nbmcc_small_value",
                    variables=middle_variables,
                ) + ")) \\/ (((" + middle_above + ") /\\ ("
                + middle_bound + ")) /\\ a = S i) \\/ a = 1",
                "specialize no_bertrand_central_contribution_choice_ranges n",
                "specialize no_bertrand_central_contribution_choice_ranges s",
                "specialize no_bertrand_central_contribution_choice_ranges q",
                "specialize no_bertrand_central_contribution_choice_ranges r",
                "specialize no_bertrand_central_contribution_choice_ranges C",
                "specialize no_bertrand_central_contribution_choice_ranges i",
                "specialize no_bertrand_central_contribution_choice_ranges a",
                "apply no_bertrand_central_contribution_choice_ranges",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hchoice",
                "cases hranges",
                "cases hranges_left",
                "cases hranges_left_left",
                "exfalso",
                "specialize lt_not_le s",
                "specialize lt_not_le (S i)",
                "apply lt_not_le",
                "exact habove",
                "exact hranges_left_left_left",
                "cases hranges_left_right",
                "cases hranges_left_right_left",
                "rewrite hranges_left_right_right",
                "rewrite hselector_left_right",
                "specialize le_refl (S i)",
                "exact le_refl",
                "rewrite hranges_right",
                "rewrite hselector_left_right",
                "exists i",
                "simp",
                "cases hselector_right",
                "cases hchoice",
                "cases hchoice_left",
                "exfalso",
                "apply hselector_right_left",
                "exact hchoice_left_left",
                "cases hchoice_right",
                "rewrite hchoice_right_right",
                "rewrite hselector_right_right",
                "specialize le_refl 1",
                "exact le_refl",
            ),
            "Middle-range contributions are bounded by dense selector factors.",
        ),
        spec(
            NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
            "forall n s q r C i a. "
            f"({high_exclusion}) -> ({high_positive}) -> "
            f"({high_floor}) -> ({high_division}) -> "
            f"({high_central}) -> ({high_above}) -> "
            f"({high_choice}) -> a = 1",
            (
                "le_trans",
                "lt_not_le",
                "floor_sqrt_le_third_quotient",
                "no_bertrand_central_contribution_choice_ranges",
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro i",
                "intro a",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro habove",
                "intro hchoice",
                f"have hroot : {high_root_bound}",
                "specialize floor_sqrt_le_third_quotient n",
                "specialize floor_sqrt_le_third_quotient s",
                "specialize floor_sqrt_le_third_quotient q",
                "specialize floor_sqrt_le_third_quotient r",
                "apply floor_sqrt_le_third_quotient",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "have hranges : "
                "((" + high_small_bound + ") /\\ (" + _le_term(
                    "a",
                    "n + n",
                    tag="b5nbhcc_small_value",
                    variables=high_variables,
                ) + ")) \\/ (((" + _lt_term(
                    "s",
                    "S i",
                    tag="b5nbhcc_range_above",
                    variables=high_variables,
                ) + ") /\\ (" + high_middle_bound
                + ")) /\\ a = S i) \\/ a = 1",
                "specialize no_bertrand_central_contribution_choice_ranges n",
                "specialize no_bertrand_central_contribution_choice_ranges s",
                "specialize no_bertrand_central_contribution_choice_ranges q",
                "specialize no_bertrand_central_contribution_choice_ranges r",
                "specialize no_bertrand_central_contribution_choice_ranges C",
                "specialize no_bertrand_central_contribution_choice_ranges i",
                "specialize no_bertrand_central_contribution_choice_ranges a",
                "apply no_bertrand_central_contribution_choice_ranges",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hchoice",
                "cases hranges",
                "cases hranges_left",
                "cases hranges_left_left",
                f"have hsmall_to_q : {high_middle_bound}",
                "specialize le_trans (S i)",
                "specialize le_trans s",
                "specialize le_trans q",
                "apply le_trans",
                "exact hranges_left_left_left",
                "exact hroot",
                "exfalso",
                "specialize lt_not_le q",
                "specialize lt_not_le (S i)",
                "apply lt_not_le",
                "exact habove",
                "exact hsmall_to_q",
                "cases hranges_left_right",
                "cases hranges_left_right_left",
                "exfalso",
                "specialize lt_not_le q",
                "specialize lt_not_le (S i)",
                "apply lt_not_le",
                "exact habove",
                "exact hranges_left_right_left_right",
                "exact hranges_right",
            ),
            "Every contribution above the third quotient is neutral.",
        ),
        spec(
            NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
            "forall n s q r C z A. "
            f"({sp_exclusion}) -> ({sp_positive}) -> "
            f"({sp_floor}) -> ({sp_division}) -> ({sp_central}) -> "
            f"({sp_source}) -> ({sp_power}) -> ({sp_result})",
            (
                "beta_at_unique",
                "beta_product_uniform_le_pow",
                NO_BERTRAND_SMALL_CONTRIBUTION_CHOICE_LE_DOUBLE,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro z",
                "intro A",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hsource",
                "intro hpower",
                "cases hsource",
                "cases hsource_witness",
                "cases hsource_witness_witness",
                f"have huniform : {sp_uniform}",
                "intro i",
                "intro a",
                "intro hi",
                "intro hdecoded",
                f"have hentry : {sp_entry}",
                "apply hsource_witness_witness_left",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "have heq : a = x2",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact hdecoded",
                "exact hentry_witness_left",
                "have hfactor : "
                + _le_term(
                    "x2",
                    "n + n",
                    tag="b5nbscplp_factor",
                    variables=small_product_variables
                    + ("x", "x1", "i", "a", "x2"),
                ),
                "specialize "
                "no_bertrand_small_contribution_choice_le_double n",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double s",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double q",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double r",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double C",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double i",
                "specialize "
                "no_bertrand_small_contribution_choice_le_double x2",
                "apply no_bertrand_small_contribution_choice_le_double",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hi",
                "exact hentry_witness_right",
                "rewrite heq",
                "exact hfactor",
                "specialize beta_product_uniform_le_pow x",
                "specialize beta_product_uniform_le_pow x1",
                "specialize beta_product_uniform_le_pow (n + n)",
                "specialize beta_product_uniform_le_pow s",
                "specialize beta_product_uniform_le_pow z",
                "specialize beta_product_uniform_le_pow A",
                "apply beta_product_uniform_le_pow",
                "exact huniform",
                "exact hsource_witness_witness_right",
                "exact hpower",
            ),
            "The small contribution Product is bounded by (2n)^s.",
        ),
        spec(
            NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
            "forall n s q r C g y P. "
            f"({mp_exclusion}) -> ({mp_positive}) -> "
            f"({mp_floor}) -> ({mp_division}) -> ({mp_central}) -> "
            f"s + g = q -> ({mp_contribution}) -> "
            f"({mp_primorial}) -> ({mp_result})",
            (
                "add_comm",
                "add_le_add_left",
                "beta_at_unique",
                "beta_product_pointwise_le",
                NO_BERTRAND_MIDDLE_CONTRIBUTION_CHOICE_LE_SELECTOR,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro g",
                "intro y",
                "intro P",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hgap",
                "intro hcontribution",
                "intro hprimorial",
                "cases hcontribution",
                "cases hcontribution_witness",
                "cases hcontribution_witness_witness",
                "cases hprimorial",
                "cases hprimorial_witness",
                "cases hprimorial_witness_witness",
                f"have hpointwise : {mp_pointwise}",
                "intro i",
                "intro a",
                "intro p",
                "intro hi",
                "intro ha",
                "intro hp",
                f"have hleft_entry : {mp_left_entry}",
                "apply hcontribution_witness_witness_left",
                "exact hi",
                "cases hleft_entry",
                "cases hleft_entry_witness",
                f"have hright_entry : {mp_right_entry}",
                "apply hprimorial_witness_witness_left",
                "exact hi",
                "cases hright_entry",
                "cases hright_entry_witness",
                "have ha_eq : a = x4",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x4",
                "apply beta_at_unique",
                "exact ha",
                "exact hleft_entry_witness_left",
                "have hp_eq : p = x5",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique i",
                "specialize beta_at_unique p",
                "specialize beta_at_unique x5",
                "apply beta_at_unique",
                "exact hp",
                "exact hright_entry_witness_left",
                f"have habove : {mp_global_above}",
                "exists i",
                "trans S (i + s)",
                "apply PA4",
                "congr",
                "specialize add_comm i",
                "specialize add_comm s",
                "exact add_comm",
                f"have hraw_bound : {mp_raw_bound}",
                "specialize add_le_add_left (S i)",
                "specialize add_le_add_left g",
                "specialize add_le_add_left s",
                "apply add_le_add_left",
                "exact hi",
                "have hadd_succ : s + S i = S (s + i)",
                "apply PA4",
                "rewrite hadd_succ at hraw_bound",
                "rewrite hgap at hraw_bound",
                f"have hglobal_bound : {mp_global_bound}",
                "exact hraw_bound",
                "have hfactor_bound : "
                + _le_term(
                    "x4",
                    "x5",
                    tag="b5nbmcilpi_factor_bound",
                    variables=middle_product_variables
                    + (
                        "x",
                        "x1",
                        "x2",
                        "x3",
                        "i",
                        "a",
                        "p",
                        "x4",
                        "x5",
                    ),
                ),
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector n",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector s",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector q",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector r",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector C",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector (s + i)",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector x4",
                "specialize "
                "no_bertrand_middle_contribution_choice_le_selector x5",
                "apply "
                "no_bertrand_middle_contribution_choice_le_selector",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact habove",
                "exact hglobal_bound",
                "exact hleft_entry_witness_right",
                "exact hright_entry_witness_right",
                "rewrite ha_eq",
                "rewrite hp_eq",
                "exact hfactor_bound",
                "specialize beta_product_pointwise_le x",
                "specialize beta_product_pointwise_le x1",
                "specialize beta_product_pointwise_le x2",
                "specialize beta_product_pointwise_le x3",
                "specialize beta_product_pointwise_le g",
                "specialize beta_product_pointwise_le y",
                "specialize beta_product_pointwise_le P",
                "apply beta_product_pointwise_le",
                "exact hpointwise",
                "exact hcontribution_witness_witness_right",
                "exact hprimorial_witness_witness_right",
            ),
            "The middle contribution interval is bounded by its selector interval.",
        ),
        spec(
            NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
            "forall n s q r C g y B. "
            f"({mfp_exclusion}) -> ({mfp_positive}) -> "
            f"({mfp_floor}) -> ({mfp_division}) -> ({mfp_central}) -> "
            f"s + g = q -> ({mfp_contribution}) -> "
            f"({mfp_power}) -> ({mfp_result})",
            (
                "le_trans",
                "le_mul_of_one_le_left",
                "primorial_exists",
                "primorial_index_eq_transport",
                "primorial_positive",
                "primorial_prefix_interval_split",
                "primorial_le_four_pow",
                NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_PRIMORIAL_INTERVAL,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro g",
                "intro y",
                "intro B",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hgap",
                "intro hcontribution",
                "intro hpower",
                f"have hprimorial : exists P. ({mfp_primorial_q})",
                "specialize primorial_exists q",
                "exact primorial_exists",
                "cases hprimorial",
                "have hreverse : q = s + g",
                "symm",
                "exact hgap",
                f"have haligned : {mfp_primorial_sum}",
                "specialize primorial_index_eq_transport q",
                "specialize primorial_index_eq_transport (s + g)",
                "specialize primorial_index_eq_transport x",
                "apply primorial_index_eq_transport",
                "exact hreverse",
                "exact hprimorial_witness",
                f"have hsplit : {mfp_split}",
                "specialize primorial_prefix_interval_split s",
                "specialize primorial_prefix_interval_split g",
                "specialize primorial_prefix_interval_split x",
                "apply primorial_prefix_interval_split",
                "exact haligned",
                "cases hsplit",
                "cases hsplit_witness",
                "cases hsplit_witness_witness",
                "cases hsplit_witness_witness_right",
                f"have hmiddle : {mfp_y_v}",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval n",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval s",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval q",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval r",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval C",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval g",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval y",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_primorial_interval x2",
                "apply "
                "no_bertrand_middle_contribution_interval_le_primorial_interval",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hgap",
                "exact hcontribution",
                "exact hsplit_witness_witness_right_left",
                "have hprefix_positive : exists t. x1 = S t",
                "specialize primorial_positive s",
                "specialize primorial_positive x1",
                "apply primorial_positive",
                "exact hsplit_witness_witness_left",
                "cases hprefix_positive",
                "have hone_prefix : "
                + _le_term(
                    "1",
                    "x1",
                    tag="b5nbmcilfp_one_prefix",
                    variables=middle_power_variables
                    + ("x", "x1", "x2", "x3"),
                ),
                "exists x3",
                "rewrite hprefix_positive_witness",
                "simp",
                f"have hinterval_product : {mfp_v_product}",
                "specialize le_mul_of_one_le_left x1",
                "specialize le_mul_of_one_le_left x2",
                "apply le_mul_of_one_le_left",
                "exact hone_prefix",
                f"have hraw_y_product : "
                + _le_term(
                    "y",
                    "x1 * x2",
                    tag="b5nbmcilfp_y_product",
                    variables=middle_power_variables
                    + ("x", "x1", "x2", "x3"),
                ),
                "specialize le_trans y",
                "specialize le_trans x2",
                "specialize le_trans (x1 * x2)",
                "apply le_trans",
                "exact hmiddle",
                "exact hinterval_product",
                f"have hy_primorial : {mfp_y_p}",
                "rewrite <- hsplit_witness_witness_right_right at hraw_y_product",
                "exact hraw_y_product",
                f"have hprimorial_power : {mfp_p_b}",
                "specialize primorial_le_four_pow q",
                "specialize primorial_le_four_pow x",
                "specialize primorial_le_four_pow B",
                "apply primorial_le_four_pow",
                "exact hprimorial_witness",
                "exact hpower",
                "specialize le_trans y",
                "specialize le_trans x",
                "specialize le_trans B",
                "apply le_trans",
                "exact hy_primorial",
                "exact hprimorial_power",
            ),
            "The middle contribution interval is bounded by four to q.",
        ),
        spec(
            NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
            "forall n s q r C h w. "
            f"({hp_exclusion}) -> ({hp_positive}) -> "
            f"({hp_floor}) -> ({hp_division}) -> ({hp_central}) -> "
            f"({hp_interval}) -> w = 1",
            (
                "add_comm",
                "beta_at_unique",
                BETA_PRODUCT_ALL_ONE_EXACT,
                NO_BERTRAND_HIGH_CONTRIBUTION_CHOICE_EQ_ONE,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro h",
                "intro w",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hinterval",
                "cases hinterval",
                "cases hinterval_witness",
                "cases hinterval_witness_witness",
                f"have hall : {hp_all}",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                f"have hlocal : {hp_local}",
                "apply hinterval_witness_witness_left",
                "exact hi",
                "cases hlocal",
                "cases hlocal_witness",
                "have heq : a = x2",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact ha",
                "exact hlocal_witness_left",
                f"have habove : {hp_global_above}",
                "exists i",
                "trans S (i + q)",
                "apply PA4",
                "congr",
                "specialize add_comm i",
                "specialize add_comm q",
                "exact add_comm",
                "have hfactor_one : x2 = 1",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one n",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one s",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one q",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one r",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one C",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one (q + i)",
                "specialize "
                "no_bertrand_high_contribution_choice_eq_one x2",
                "apply no_bertrand_high_contribution_choice_eq_one",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact habove",
                "exact hlocal_witness_right",
                "rewrite heq",
                "exact hfactor_one",
                "specialize beta_product_all_one_exact x",
                "specialize beta_product_all_one_exact x1",
                "specialize beta_product_all_one_exact h",
                "specialize beta_product_all_one_exact w",
                "apply beta_product_all_one_exact",
                "exact hall",
                "exact hinterval_witness_witness_right",
            ),
            "The high contribution interval is the multiplicative unit.",
        ),
        spec(
            CENTRAL_BINOM_FACTORIZATION_SMALL,
            "forall n s q r C g h z. "
            f"({factor_exclusion}) -> ({factor_positive}) -> "
            f"({factor_floor}) -> ({factor_division}) -> "
            f"({factor_central}) -> s + g = q -> q + h = n + n -> "
            f"({factor_source}) -> ({factor_result})",
            (
                "mul_one",
                "prime_contribution_product_length_eq_transport",
                "prime_contribution_prefix_interval_split",
                NO_BERTRAND_HIGH_CONTRIBUTION_INTERVAL_EQ_ONE,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro g",
                "intro h",
                "intro z",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hfirst",
                "intro hsecond",
                "intro hsource",
                "have hsecond_reverse : n + n = q + h",
                "symm",
                "exact hsecond",
                f"have houter_source : {factor_outer_source}",
                "specialize prime_contribution_product_length_eq_transport C",
                "specialize prime_contribution_product_length_eq_transport "
                "(n + n)",
                "specialize prime_contribution_product_length_eq_transport "
                "(q + h)",
                "specialize prime_contribution_product_length_eq_transport z",
                "apply prime_contribution_product_length_eq_transport",
                "exact hsecond_reverse",
                "exact hsource",
                f"have houter : {factor_outer}",
                "specialize prime_contribution_prefix_interval_split C",
                "specialize prime_contribution_prefix_interval_split q",
                "specialize prime_contribution_prefix_interval_split h",
                "specialize prime_contribution_prefix_interval_split z",
                "apply prime_contribution_prefix_interval_split",
                "exact houter_source",
                "cases houter",
                "cases houter_witness",
                "cases houter_witness_witness",
                "cases houter_witness_witness_right",
                "have hfirst_reverse : q = s + g",
                "symm",
                "exact hfirst",
                f"have hinner_source : {factor_inner_source}",
                "specialize prime_contribution_product_length_eq_transport C",
                "specialize prime_contribution_product_length_eq_transport q",
                "specialize prime_contribution_product_length_eq_transport "
                "(s + g)",
                "specialize prime_contribution_product_length_eq_transport x",
                "apply prime_contribution_product_length_eq_transport",
                "exact hfirst_reverse",
                "exact houter_witness_witness_left",
                f"have hinner : {factor_inner}",
                "specialize prime_contribution_prefix_interval_split C",
                "specialize prime_contribution_prefix_interval_split s",
                "specialize prime_contribution_prefix_interval_split g",
                "specialize prime_contribution_prefix_interval_split x",
                "apply prime_contribution_prefix_interval_split",
                "exact hinner_source",
                "cases hinner",
                "cases hinner_witness",
                "cases hinner_witness_witness",
                "cases hinner_witness_witness_right",
                "have hunit : x1 = 1",
                "specialize no_bertrand_high_contribution_interval_eq_one n",
                "specialize no_bertrand_high_contribution_interval_eq_one s",
                "specialize no_bertrand_high_contribution_interval_eq_one q",
                "specialize no_bertrand_high_contribution_interval_eq_one r",
                "specialize no_bertrand_high_contribution_interval_eq_one C",
                "specialize no_bertrand_high_contribution_interval_eq_one h",
                "specialize no_bertrand_high_contribution_interval_eq_one x1",
                "apply no_bertrand_high_contribution_interval_eq_one",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact houter_witness_witness_right_left",
                "exists x2",
                "exists x3",
                "split",
                "exact hinner_witness_witness_left",
                "split",
                "exact hinner_witness_witness_right_left",
                "trans x * x1",
                "exact houter_witness_witness_right_right",
                "rewrite hinner_witness_witness_right_right",
                "rewrite hunit",
                "specialize mul_one (x2 * x3)",
                "exact mul_one",
            ),
            "The complete central contribution Product has only two live ranges.",
        ),
        spec(
            CENTRAL_BINOM_LE_OF_NO_BERTRAND_PRIME,
            "forall n s q r C A B. "
            f"({final_exclusion}) -> ({final_positive}) -> "
            f"({final_floor}) -> ({final_division}) -> "
            f"({final_central}) -> ({final_power_a}) -> "
            f"({final_power_b}) -> ({final_result})",
            (
                "mul_le_mul",
                "floor_third_double_gap_package",
                "central_binom_prime_contribution_product_exists",
                NO_BERTRAND_SMALL_CONTRIBUTION_PRODUCT_LE_POWER,
                NO_BERTRAND_MIDDLE_CONTRIBUTION_INTERVAL_LE_FOUR_POW,
                CENTRAL_BINOM_FACTORIZATION_SMALL,
            ),
            (
                "intro n",
                "intro s",
                "intro q",
                "intro r",
                "intro C",
                "intro A",
                "intro B",
                "intro hexclusion",
                "intro hpositive",
                "intro hfloor",
                "intro hdivision",
                "intro hcentral",
                "intro hpower_a",
                "intro hpower_b",
                "have hgaps : exists g h. s + g = q /\\ q + h = n + n",
                "specialize floor_third_double_gap_package n",
                "specialize floor_third_double_gap_package s",
                "specialize floor_third_double_gap_package q",
                "specialize floor_third_double_gap_package r",
                "apply floor_third_double_gap_package",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "cases hgaps",
                "cases hgaps_witness",
                "cases hgaps_witness_witness",
                f"have hproduct : {final_product_exists}",
                "specialize central_binom_prime_contribution_product_exists n",
                "specialize central_binom_prime_contribution_product_exists C",
                "apply central_binom_prime_contribution_product_exists",
                "exact hcentral",
                "cases hproduct",
                "cases hproduct_witness",
                f"have hfactorization : {final_factorization}",
                "specialize central_binom_factorization_small n",
                "specialize central_binom_factorization_small s",
                "specialize central_binom_factorization_small q",
                "specialize central_binom_factorization_small r",
                "specialize central_binom_factorization_small C",
                "specialize central_binom_factorization_small x",
                "specialize central_binom_factorization_small x1",
                "specialize central_binom_factorization_small x2",
                "apply central_binom_factorization_small",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hgaps_witness_witness_left",
                "exact hgaps_witness_witness_right",
                "exact hproduct_witness_left",
                "cases hfactorization",
                "cases hfactorization_witness",
                "cases hfactorization_witness_witness",
                "cases hfactorization_witness_witness_right",
                f"have hsmall : {final_x_a}",
                "specialize "
                "no_bertrand_small_contribution_product_le_power n",
                "specialize "
                "no_bertrand_small_contribution_product_le_power s",
                "specialize "
                "no_bertrand_small_contribution_product_le_power q",
                "specialize "
                "no_bertrand_small_contribution_product_le_power r",
                "specialize "
                "no_bertrand_small_contribution_product_le_power C",
                "specialize "
                "no_bertrand_small_contribution_product_le_power x3",
                "specialize "
                "no_bertrand_small_contribution_product_le_power A",
                "apply no_bertrand_small_contribution_product_le_power",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hfactorization_witness_witness_left",
                "exact hpower_a",
                f"have hmiddle : {final_y_b}",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow n",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow s",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow q",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow r",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow C",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow x",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow x4",
                "specialize "
                "no_bertrand_middle_contribution_interval_le_four_pow B",
                "apply no_bertrand_middle_contribution_interval_le_four_pow",
                "exact hexclusion",
                "exact hpositive",
                "exact hfloor",
                "exact hdivision",
                "exact hcentral",
                "exact hgaps_witness_witness_left",
                "exact hfactorization_witness_witness_right_left",
                "exact hpower_b",
                f"have hproduct_bound : {final_product_bound}",
                "specialize mul_le_mul x3",
                "specialize mul_le_mul A",
                "specialize mul_le_mul x4",
                "specialize mul_le_mul B",
                "apply mul_le_mul",
                "exact hsmall",
                "exact hmiddle",
                "rewrite hproduct_witness_right",
                "rewrite hfactorization_witness_witness_right_right",
                "exact hproduct_bound",
            ),
            "No Bertrand prime forces the reviewed central-binomial upper bound.",
        ),
    )


__all__ = ["make_bertrand_b5_central_upper_candidate_theorems"]
