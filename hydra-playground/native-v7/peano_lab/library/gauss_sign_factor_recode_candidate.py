"""Isolated beta recoding of Gauss reflection bits into sign factors.

This module is the conservative coding bridge downstream of
``gauss_sign_product_candidate``.  It builds a beta prefix whose entry is
``1`` when the corresponding bit is zero and ``r`` when that bit is one.  In
the endpoint premise ``p = S r``, ``r`` is exactly the natural predecessor
``p - 1`` without adding subtraction to the object language.

All relations expand to first-order PA before parsing.  The module is an
unregistered candidate and makes no change to the kernel or public registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, bit_count, power_relation, product_relation
from .gauss_sign_product_candidate import (
    sign_factor_prefix,
    sign_factor_successor_prefix,
)
from .gauss_signed_prefix_candidate import _beta_at_term


def make_gauss_sign_factor_recode_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build append, finite recoding, and exact product/power packaging specs."""

    signs_before = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="recode_before"
    )
    signs_after = sign_factor_successor_prefix(
        "sb", "sc", "z", "d", "r", "l", tag="recode_after"
    )
    source_last = beta_at("sb", "sc", "l", "a", tag="recode_source_last")
    chosen_factor = (
        "((a = 0 /\\ f = 1) \\/ (a = 1 /\\ f = r))"
    )
    new_factor_one = _beta_at_term(
        "x",
        "x1",
        "l",
        "1",
        tag="recode_new_one",
        variables=("sb", "sc", "fb", "fc", "r", "l", "a", "f", "x", "x1"),
    )
    new_factor_predecessor = beta_at(
        "x", "x1", "l", "r", tag="recode_new_predecessor"
    )
    old_factor_one = _beta_at_term(
        "fb",
        "fc",
        "i",
        "1",
        tag="recode_old_one",
        variables=("sb", "sc", "fb", "fc", "r", "l", "a", "f", "i", "v"),
    )
    old_factor_predecessor = beta_at(
        "fb", "fc", "i", "r", tag="recode_old_predecessor"
    )

    count = bit_count("sb", "sc", "l", "e", tag="recode_count")
    signs_result = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="recode_result"
    )
    count_last = beta_at("sb", "sc", "l", "a", tag="recode_count_last")
    count_prefix = bit_count(
        "sb", "sc", "l", "k", tag="recode_count_prefix"
    )
    count_decomposition = (
        f"exists a k. ({count_last}) /\\ (({count_prefix}) /\\ "
        "((a = 0 \\/ a = 1) /\\ e = k + a))"
    )
    signs_previous_exists = (
        "exists fb fc. "
        f"({sign_factor_prefix('sb', 'sc', 'fb', 'fc', 'r', 'l', tag='recode_previous')})"
    )
    endpoint_signs = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "l", tag="recode_endpoint_signs"
    )
    endpoint_product = product_relation(
        "fb", "fc", "l", "F", tag="recode_endpoint_product"
    )
    endpoint_power = power_relation(
        "r", "e", "R", tag="recode_endpoint_power"
    )
    endpoint = (
        "exists fb fc F R. "
        f"(({endpoint_signs}) /\\ (({endpoint_product}) /\\ "
        f"(({endpoint_power}) /\\ F = R)))"
    )

    return (
        spec(
            "beta_sign_factor_prefix_extend",
            "forall sb sc fb fc r l a f. "
            f"({signs_before}) -> ({source_last}) -> {chosen_factor} -> "
            f"exists z d. ({signs_after})",
            (
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "beta_at_unique",
            ),
            (
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro r",
                "intro l",
                "intro a",
                "intro f",
                "intro hsigns",
                "intro hlast",
                "intro hchosen",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend fb",
                "specialize beta_prefix_extend fc",
                "specialize beta_prefix_extend f",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "intro i",
                "intro v",
                "intro hi",
                "intro hv",
                "have hsplit : i = l \/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "have hvlast : "
                + beta_at("sb", "sc", "l", "v", tag="recode_top_source"),
                "rewrite hsplit_left at hv",
                "rewrite hsplit_left at hv",
                "exact hv",
                "have hva : v = a",
                "specialize beta_at_unique sb",
                "specialize beta_at_unique sc",
                "specialize beta_at_unique l",
                "specialize beta_at_unique v",
                "specialize beta_at_unique a",
                "apply beta_at_unique",
                "exact hvlast",
                "exact hlast",
                "cases hchosen",
                "cases hchosen_left",
                "left",
                "split",
                "trans a",
                "exact hva",
                "exact hchosen_left_left",
                f"have hnew_one : {new_factor_one}",
                "rewrite hchosen_left_right at beta_prefix_extend_witness_witness_left",
                "rewrite hchosen_left_right at beta_prefix_extend_witness_witness_left",
                "exact beta_prefix_extend_witness_witness_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hnew_one",
                "cases hchosen_right",
                "right",
                "split",
                "trans a",
                "exact hva",
                "exact hchosen_right_left",
                f"have hnew_predecessor : {new_factor_predecessor}",
                "rewrite hchosen_right_right at beta_prefix_extend_witness_witness_left",
                "rewrite hchosen_right_right at beta_prefix_extend_witness_witness_left",
                "exact beta_prefix_extend_witness_witness_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hnew_predecessor",
                "have hold : ((v = 0 /\\ "
                f"({old_factor_one})) \\/ (v = 1 /\\ ({old_factor_predecessor})))",
                "specialize hsigns i",
                "specialize hsigns v",
                "apply hsigns",
                "exact hsplit_right",
                "exact hv",
                "cases hold",
                "cases hold_left",
                "left",
                "split",
                "exact hold_left_left",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right 1",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_left_right",
                "cases hold_right",
                "right",
                "split",
                "exact hold_right_left",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right r",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "exact hold_right_right",
            ),
            "Append the selected 1/r factor while preserving every earlier decoded factor.",
        ),
        spec(
            "beta_sign_factor_prefix_exists",
            "forall sb sc r l e. "
            f"({count}) -> exists fb fc. ({signs_result})",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "bit_count_succ_decompose",
                "beta_sign_factor_prefix_extend",
            ),
            (
                "intro sb",
                "intro sc",
                "intro r",
                "induction l",
                "intro e",
                "intro hcount",
                "exists 0",
                "exists 0",
                "intro i",
                "intro v",
                "intro hi",
                "intro hv",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro e",
                "intro hcount",
                f"have hdecomp : {count_decomposition}",
                "specialize bit_count_succ_decompose sb",
                "specialize bit_count_succ_decompose sc",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose e",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hcount",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                "cases hdecomp_witness_witness_right_right",
                f"have hprevious : {signs_previous_exists}",
                "specialize IH x1",
                "apply IH",
                "exact hdecomp_witness_witness_right_left",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hdecomp_witness_witness_right_right_left",
                "specialize beta_sign_factor_prefix_extend sb",
                "specialize beta_sign_factor_prefix_extend sc",
                "specialize beta_sign_factor_prefix_extend x2",
                "specialize beta_sign_factor_prefix_extend x3",
                "specialize beta_sign_factor_prefix_extend r",
                "specialize beta_sign_factor_prefix_extend l",
                "specialize beta_sign_factor_prefix_extend x",
                "specialize beta_sign_factor_prefix_extend 1",
                "apply beta_sign_factor_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hdecomp_witness_witness_left",
                "left",
                "split",
                "exact hdecomp_witness_witness_right_right_left_left",
                "refl",
                "specialize beta_sign_factor_prefix_extend sb",
                "specialize beta_sign_factor_prefix_extend sc",
                "specialize beta_sign_factor_prefix_extend x2",
                "specialize beta_sign_factor_prefix_extend x3",
                "specialize beta_sign_factor_prefix_extend r",
                "specialize beta_sign_factor_prefix_extend l",
                "specialize beta_sign_factor_prefix_extend x",
                "specialize beta_sign_factor_prefix_extend r",
                "apply beta_sign_factor_prefix_extend",
                "exact hprevious_witness_witness",
                "exact hdecomp_witness_witness_left",
                "right",
                "split",
                "exact hdecomp_witness_witness_right_right_left_right",
                "refl",
            ),
            "Every finite beta bit prefix admits a beta-coded 1/r sign-factor prefix.",
        ),
        spec(
            "beta_sign_factor_product_power_exists",
            "forall p r sb sc l e. p = S r -> "
            f"({count}) -> ({endpoint})",
            (
                "beta_sign_factor_prefix_exists",
                "beta_product_exists",
                "pow_exists",
                "beta_sign_factor_product_power",
            ),
            (
                "intro p",
                "intro r",
                "intro sb",
                "intro sc",
                "intro l",
                "intro e",
                "intro hp",
                "intro hcount",
                "have hsigns_exists : exists fb fc. "
                f"({sign_factor_prefix('sb', 'sc', 'fb', 'fc', 'r', 'l', tag='recode_endpoint_signs_exists')})",
                "specialize beta_sign_factor_prefix_exists sb",
                "specialize beta_sign_factor_prefix_exists sc",
                "specialize beta_sign_factor_prefix_exists r",
                "specialize beta_sign_factor_prefix_exists l",
                "specialize beta_sign_factor_prefix_exists e",
                "apply beta_sign_factor_prefix_exists",
                "exact hcount",
                "cases hsigns_exists",
                "cases hsigns_exists_witness",
                "have hproduct_exists : exists F. "
                f"({product_relation('x', 'x1', 'l', 'F', tag='recode_endpoint_product_exists')})",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists l",
                "exact beta_product_exists",
                "cases hproduct_exists",
                "have hpower_exists : exists R. "
                f"({power_relation('r', 'e', 'R', tag='recode_endpoint_power_exists')})",
                "specialize pow_exists r",
                "specialize pow_exists e",
                "exact pow_exists",
                "cases hpower_exists",
                "have hequal : x2 = x3",
                "specialize beta_sign_factor_product_power sb",
                "specialize beta_sign_factor_product_power sc",
                "specialize beta_sign_factor_product_power x",
                "specialize beta_sign_factor_product_power x1",
                "specialize beta_sign_factor_product_power r",
                "specialize beta_sign_factor_product_power l",
                "specialize beta_sign_factor_product_power e",
                "specialize beta_sign_factor_product_power x2",
                "specialize beta_sign_factor_product_power x3",
                "apply beta_sign_factor_product_power",
                "exact hcount",
                "exact hsigns_exists_witness_witness",
                "exact hproduct_exists_witness",
                "exact hpower_exists_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hsigns_exists_witness_witness",
                "split",
                "exact hproduct_exists_witness",
                "split",
                "exact hpower_exists_witness",
                "exact hequal",
            ),
            "For p=S r, the recoded sign product exists and equals the relational power r^e.",
        ),
    )


__all__ = ["make_gauss_sign_factor_recode_candidate_theorems"]
