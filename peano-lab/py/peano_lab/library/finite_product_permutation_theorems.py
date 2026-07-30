"""Constructive product transport for beta-coded finite permutations.

The public contracts in this module expand every decoded entry and finite
product into the unchanged first-order PA language.  The central balance law
states that replacing one factor ``x`` by ``y`` changes the total products
``p`` and ``q`` by ``q*x = p*y``.  It is proved by ordinary induction and then
specialized to an interior/last swap, where the two totals are equal.

This is an isolated theorem-spec factory.  It adds no product, list, function,
or permutation primitive to the parser or kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation, product_successor_relation


def make_finite_product_permutation_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered product-permutation tranche."""

    reflect_new_i = beta_at("z", "d", "i", "y", tag="replace_reflect_new_i")
    reflect_old_j = beta_at("b", "c", "j", "a", tag="replace_reflect_old_j")
    reflect_new_j = beta_at("z", "d", "j", "a", tag="replace_reflect_new_j")

    balance_old_i = beta_at("b", "c", "i", "x", tag="balance_old_i")
    balance_new_i = beta_at("z", "d", "i", "y", tag="balance_new_i")
    balance_old_j = beta_at("b", "c", "j", "a", tag="balance_old_j")
    balance_new_j = beta_at("z", "d", "j", "a", tag="balance_new_j")
    balance_old_product = product_relation("b", "c", "k", "p", tag="balance_old")
    balance_new_product = product_relation("z", "d", "k", "q", tag="balance_new")

    swap_old_i = beta_at("b", "c", "i", "x", tag="product_swap_old_i")
    swap_old_n = beta_at("b", "c", "n", "y", tag="product_swap_old_n")
    swap_new_i = beta_at("z", "d", "i", "y", tag="product_swap_new_i")
    swap_new_n = beta_at("z", "d", "n", "x", tag="product_swap_new_n")
    swap_old_j = beta_at("b", "c", "j", "a", tag="product_swap_old_j")
    swap_new_j = beta_at("z", "d", "j", "a", tag="product_swap_new_j")
    swap_old_product = product_successor_relation(
        "b", "c", "n", "p", tag="product_swap_old"
    )
    swap_new_product = product_successor_relation(
        "z", "d", "n", "q", tag="product_swap_new"
    )
    balance_old_last = beta_at("b", "c", "k", "a", tag="balance_old_last")
    balance_new_last = beta_at("z", "d", "k", "a", tag="balance_new_last")
    balance_old_prefix = product_relation(
        "b", "c", "k", "r", tag="balance_old_prefix"
    )
    balance_new_prefix = product_relation(
        "z", "d", "k", "r", tag="balance_new_prefix"
    )
    balance_old_decomposition = (
        f"exists a r. ({balance_old_last}) /\\ "
        f"(({balance_old_prefix}) /\\ p = r * a)"
    )
    balance_new_decomposition = (
        f"exists a r. ({balance_new_last}) /\\ "
        f"(({balance_new_prefix}) /\\ q = r * a)"
    )
    balance_transported_prefix = product_relation(
        "z", "d", "k", "x2", tag="balance_transported_prefix"
    )

    swap_old_last = beta_at("b", "c", "n", "a", tag="swap_old_last")
    swap_new_last = beta_at("z", "d", "n", "a", tag="swap_new_last")
    swap_old_prefix = product_relation("b", "c", "n", "r", tag="swap_old_prefix")
    swap_new_prefix = product_relation("z", "d", "n", "r", tag="swap_new_prefix")
    swap_old_decomposition = (
        f"exists a r. ({swap_old_last}) /\\ (({swap_old_prefix}) /\\ p = r * a)"
    )
    swap_new_decomposition = (
        f"exists a r. ({swap_new_last}) /\\ (({swap_new_prefix}) /\\ q = r * a)"
    )

    return (
        spec(
            "beta_prefix_replace_reflect",
            "forall b c z d k i y. (exists h. h + S i = k) -> "
            f"({reflect_new_i}) -> "
            "(forall j a. (exists h. h + S j = k) -> ~(j = i) -> "
            f"({reflect_old_j}) -> ({reflect_new_j})) -> "
            "forall j a. (exists h. h + S j = k) -> "
            f"({reflect_new_j}) -> ((j = i /\\ a = y) \\/ "
            f"(~(j = i) /\\ ({reflect_old_j})))",
            ("eq_decidable", "beta_at_exists", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro k",
                "intro i",
                "intro y",
                "intro hi",
                "intro hnew_i",
                "intro hpreserve",
                "intro j",
                "intro a",
                "intro hj",
                "intro hnew",
                "specialize eq_decidable j",
                "specialize eq_decidable i",
                "cases eq_decidable",
                "left",
                "split",
                "exact eq_decidable_left",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique i",
                "specialize beta_at_unique a",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "rewrite eq_decidable_left at hnew",
                "rewrite eq_decidable_left at hnew",
                "exact hnew",
                "exact hnew_i",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists j",
                "cases beta_at_exists",
                "have htransport : "
                "((exists h. h + S x = S ((S j) * d)) /\\ "
                "exists q. z = q * S ((S j) * d) + x)",
                "specialize hpreserve j",
                "specialize hpreserve x",
                "apply hpreserve",
                "exact hj",
                "exact eq_decidable_right",
                "exact beta_at_exists_witness",
                "have hax : a = x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique j",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hnew",
                "exact htransport",
                "right",
                "split",
                "exact eq_decidable_right",
                "rewrite hax",
                "rewrite hax",
                "exact beta_at_exists_witness",
            ),
            "A decoded entry of a one-position replacement is either the replacement or the original entry.",
        ),
        spec(
            "beta_product_replace_balance",
            "forall k b c z d i x y p q. "
            "(exists h. h + S i = k) -> "
            f"({balance_old_i}) -> ({balance_new_i}) -> "
            "(forall j a. (exists h. h + S j = k) -> ~(j = i) -> "
            f"({balance_old_j}) -> ({balance_new_j})) -> "
            f"({balance_old_product}) -> ({balance_new_product}) -> "
            "q * x = p * y",
            (
                "add_eq_zero_right",
                "succ_ne_zero",
                "finite_lt_succ_eq_or_lt",
                "beta_product_succ_decompose",
                "beta_product_transport_prefix",
                "beta_product_functional",
                "beta_at_unique",
                "mul_assoc",
                "mul_comm",
                "le_succ",
                "le_refl",
                "lt_irrefl_expanded",
            ),
            (
                "induction k",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro i",
                "intro x",
                "intro y",
                "intro p",
                "intro q",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x1",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro i",
                "intro x",
                "intro y",
                "intro p",
                "intro q",
                "intro hi",
                "intro hold_i",
                "intro hnew_i",
                "intro hpreserve",
                "intro hproduct_old",
                "intro hproduct_new",
                "have hisplit : i = k \\/ exists h. h + S i = k",
                "specialize finite_lt_succ_eq_or_lt k",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                f"have hold_decomp : {balance_old_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose k",
                "specialize beta_product_succ_decompose p",
                "apply beta_product_succ_decompose",
                "exact hproduct_old",
                f"have hnew_decomp : {balance_new_decomposition}",
                "specialize beta_product_succ_decompose z",
                "specialize beta_product_succ_decompose d",
                "specialize beta_product_succ_decompose k",
                "specialize beta_product_succ_decompose q",
                "apply beta_product_succ_decompose",
                "exact hproduct_new",
                "cases hold_decomp",
                "cases hold_decomp_witness",
                "cases hold_decomp_witness_witness",
                "cases hold_decomp_witness_witness_right",
                "cases hnew_decomp",
                "cases hnew_decomp_witness",
                "cases hnew_decomp_witness_witness",
                "cases hnew_decomp_witness_witness_right",
                "cases hisplit",
                "have hax : x1 = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique k",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hold_decomp_witness_witness_left",
                "rewrite hisplit_left at hold_i",
                "rewrite hisplit_left at hold_i",
                "exact hold_i",
                "have hby : x3 = y",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique k",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "exact hnew_decomp_witness_witness_left",
                "rewrite hisplit_left at hnew_i",
                "rewrite hisplit_left at hnew_i",
                "exact hnew_i",
                f"have hprefix_transport : {balance_transported_prefix}",
                "specialize beta_product_transport_prefix b",
                "specialize beta_product_transport_prefix c",
                "specialize beta_product_transport_prefix z",
                "specialize beta_product_transport_prefix d",
                "specialize beta_product_transport_prefix k",
                "specialize beta_product_transport_prefix x2",
                "apply beta_product_transport_prefix",
                "exact hold_decomp_witness_witness_right_left",
                "intro j",
                "intro a",
                "intro hj",
                "intro hold",
                "specialize hpreserve j",
                "specialize hpreserve a",
                "apply hpreserve",
                "specialize le_succ (S j)",
                "specialize le_succ k",
                "apply le_succ",
                "exact hj",
                "intro hjk",
                "specialize lt_irrefl_expanded k",
                "apply lt_irrefl_expanded",
                "rewrite hjk at hj",
                "rewrite hisplit_left at hj",
                "exact hj",
                "exact hold",
                "cases hprefix_transport",
                "cases hprefix_transport_witness",
                "cases hnew_decomp_witness_witness_right_left",
                "cases hnew_decomp_witness_witness_right_left_witness",
                "rewrite hold_decomp_witness_witness_right_right",
                "rewrite hnew_decomp_witness_witness_right_right",
                "rewrite hax",
                "rewrite hby",
                "trans (x4 * x) * y",
                "simp [mul_assoc, mul_comm]",
                "congr",
                "congr",
                "symm",
                "specialize beta_product_functional z",
                "specialize beta_product_functional d",
                "specialize beta_product_functional k",
                "specialize beta_product_functional x2",
                "specialize beta_product_functional x5",
                "specialize beta_product_functional x6",
                "specialize beta_product_functional x4",
                "specialize beta_product_functional x7",
                "specialize beta_product_functional x8",
                "apply beta_product_functional",
                "exact hprefix_transport_witness_witness",
                "exact hnew_decomp_witness_witness_right_left_witness_witness",
                "refl",
                "refl",
                "have hki : ~(k = i)",
                "intro hki_eq",
                "specialize lt_irrefl_expanded k",
                "apply lt_irrefl_expanded",
                "rewrite <- hki_eq at hisplit_right",
                "exact hisplit_right",
                "have hlast_new : "
                "((exists h. h + S x1 = S ((S k) * d)) /\\ "
                "exists w. z = w * S ((S k) * d) + x1)",
                "specialize hpreserve k",
                "specialize hpreserve x1",
                "apply hpreserve",
                "specialize le_refl (S k)",
                "exact le_refl",
                "exact hki",
                "exact hold_decomp_witness_witness_left",
                "have hlast_eq : x3 = x1",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique k",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hnew_decomp_witness_witness_left",
                "exact hlast_new",
                "have hprefix_preserve : forall j a. "
                "(exists h. h + S j = k) -> ~(j = i) -> "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists w. b = w * S ((S j) * c) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists w. z = w * S ((S j) * d) + a)",
                "intro j",
                "intro a",
                "intro hj",
                "intro hji",
                "intro hold",
                "specialize hpreserve j",
                "specialize hpreserve a",
                "apply hpreserve",
                "specialize le_succ (S j)",
                "specialize le_succ k",
                "apply le_succ",
                "exact hj",
                "exact hji",
                "exact hold",
                "have hbalance : x4 * x = x2 * y",
                "specialize IH b",
                "specialize IH c",
                "specialize IH z",
                "specialize IH d",
                "specialize IH i",
                "specialize IH x",
                "specialize IH y",
                "specialize IH x2",
                "specialize IH x4",
                "apply IH",
                "exact hisplit_right",
                "exact hold_i",
                "exact hnew_i",
                "exact hprefix_preserve",
                "exact hold_decomp_witness_witness_right_left",
                "exact hnew_decomp_witness_witness_right_left",
                "rewrite hold_decomp_witness_witness_right_right",
                "rewrite hnew_decomp_witness_witness_right_right",
                "rewrite hlast_eq",
                "trans (x4 * x) * x1",
                "simp [mul_assoc, mul_comm]",
                "rewrite hbalance",
                "simp [mul_assoc, mul_comm]",
            ),
            "Replacing one factor balances the old and new finite products by the exchanged values.",
        ),
        spec(
            "beta_product_swap_last_invariant",
            "forall b c z d n i x y p q. "
            "(exists h. h + S i = n) -> "
            f"({swap_old_i}) -> ({swap_old_n}) -> "
            f"({swap_new_i}) -> ({swap_new_n}) -> "
            "(forall j a. (exists h. h + S j = S n) -> "
            f"~(j = i) -> ~(j = n) -> ({swap_old_j}) -> ({swap_new_j})) -> "
            f"({swap_old_product}) -> ({swap_new_product}) -> p = q",
            (
                "beta_product_replace_balance",
                "beta_product_succ_decompose",
                "beta_at_unique",
                "le_succ",
                "le_refl",
                "lt_irrefl_expanded",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro n",
                "intro i",
                "intro x",
                "intro y",
                "intro p",
                "intro q",
                "intro hi",
                "intro hold_i",
                "intro hold_n",
                "intro hnew_i",
                "intro hnew_n",
                "intro hpreserve",
                "intro hproduct_old",
                "intro hproduct_new",
                f"have hold_decomp : {swap_old_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose n",
                "specialize beta_product_succ_decompose p",
                "apply beta_product_succ_decompose",
                "exact hproduct_old",
                f"have hnew_decomp : {swap_new_decomposition}",
                "specialize beta_product_succ_decompose z",
                "specialize beta_product_succ_decompose d",
                "specialize beta_product_succ_decompose n",
                "specialize beta_product_succ_decompose q",
                "apply beta_product_succ_decompose",
                "exact hproduct_new",
                "cases hold_decomp",
                "cases hold_decomp_witness",
                "cases hold_decomp_witness_witness",
                "cases hold_decomp_witness_witness_right",
                "cases hnew_decomp",
                "cases hnew_decomp_witness",
                "cases hnew_decomp_witness_witness",
                "cases hnew_decomp_witness_witness_right",
                "have hold_last : x1 = y",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "exact hold_decomp_witness_witness_left",
                "exact hold_n",
                "have hnew_last : x3 = x",
                "specialize beta_at_unique z",
                "specialize beta_at_unique d",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hnew_decomp_witness_witness_left",
                "exact hnew_n",
                "have hprefix_preserve : forall j a. "
                "(exists h. h + S j = n) -> ~(j = i) -> "
                "((exists h. h + S a = S ((S j) * c)) /\\ "
                "exists w. b = w * S ((S j) * c) + a) -> "
                "((exists h. h + S a = S ((S j) * d)) /\\ "
                "exists w. z = w * S ((S j) * d) + a)",
                "intro j",
                "intro a",
                "intro hj",
                "intro hji",
                "intro hold",
                "specialize hpreserve j",
                "specialize hpreserve a",
                "apply hpreserve",
                "specialize le_succ (S j)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hj",
                "exact hji",
                "intro hjn",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "rewrite hjn at hj",
                "exact hj",
                "exact hold",
                "have hbalance : x4 * x = x2 * y",
                "specialize beta_product_replace_balance n",
                "specialize beta_product_replace_balance b",
                "specialize beta_product_replace_balance c",
                "specialize beta_product_replace_balance z",
                "specialize beta_product_replace_balance d",
                "specialize beta_product_replace_balance i",
                "specialize beta_product_replace_balance x",
                "specialize beta_product_replace_balance y",
                "specialize beta_product_replace_balance x2",
                "specialize beta_product_replace_balance x4",
                "apply beta_product_replace_balance",
                "exact hi",
                "exact hold_i",
                "exact hnew_i",
                "exact hprefix_preserve",
                "exact hold_decomp_witness_witness_right_left",
                "exact hnew_decomp_witness_witness_right_left",
                "rewrite hold_decomp_witness_witness_right_right",
                "rewrite hnew_decomp_witness_witness_right_right",
                "rewrite hold_last",
                "rewrite hnew_last",
                "symm",
                "exact hbalance",
            ),
            "Swapping an interior beta-coded factor with the last factor preserves the exact finite product.",
        ),
    )


__all__ = ["make_finite_product_permutation_theorems"]
