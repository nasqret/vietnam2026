"""Constructive order bounds for beta-coded finite products.

This isolated candidate factory adds two reusable finite-fold order laws.  The
first transports pointwise weak inequalities through two synchronized Product
relations.  The second compares a uniformly bounded Product with the
corresponding relational Pow value.

All authoring helpers expand to ordinary first-order Peano arithmetic before
parsing.  No Product, Pow, BetaAt, order, function, sequence, or fold primitive
is added to the parser or kernel, and these candidates are not enrolled in any
library edition.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, power_relation, product_relation


def _pointwise_le(length: str, *, tag: str) -> str:
    """Expand pointwise weak order for the module-owned prefix variables."""

    left = beta_at("b", "c", "i", "a", tag=f"{tag}_left")
    right = beta_at("d", "e", "i", "z", tag=f"{tag}_right")
    return (
        f"forall i a z. (exists {tag}_bound. "
        f"{tag}_bound + S i = {length}) -> "
        f"({left}) -> ({right}) -> "
        f"exists {tag}_factor_gap. {tag}_factor_gap + a = z"
    )


def _uniform_le(length: str, *, tag: str) -> str:
    """Expand a uniform upper bound for one decoded beta prefix."""

    entry = beta_at("b", "c", "i", "x", tag=f"{tag}_source")
    return (
        f"forall i x. (exists {tag}_bound. "
        f"{tag}_bound + S i = {length}) -> "
        f"({entry}) -> "
        f"exists {tag}_factor_gap. {tag}_factor_gap + x = a"
    )


def _product_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = product_relation(
        code, scale, length, "r", tag=f"{tag}_product"
    )
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r * a)"


def make_finite_product_order_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered pointwise and uniform product bounds."""

    pointwise = _pointwise_le("l", tag="bppl")
    left_product = product_relation(
        "b", "c", "l", "n", tag="bppl_left_product"
    )
    right_product = product_relation(
        "d", "e", "l", "q", tag="bppl_right_product"
    )
    pointwise_statement = (
        "forall b c d e l n q. "
        f"({pointwise}) -> ({left_product}) -> ({right_product}) -> "
        "exists bppl_result_gap. bppl_result_gap + n = q"
    )

    uniform = _uniform_le("l", tag="bpulp")
    source_product = product_relation(
        "b", "c", "l", "n", tag="bpulp_source_product"
    )
    target_power = power_relation(
        "a", "l", "q", tag="bpulp_target_power"
    )
    uniform_statement = (
        "forall b c a l n q. "
        f"({uniform}) -> ({source_product}) -> ({target_power}) -> "
        "exists bpulp_result_gap. bpulp_result_gap + n = q"
    )

    left_decomposition = _product_decomposition(
        "b", "c", "l", "n", tag="bppl_left_decomposition"
    )
    right_decomposition = _product_decomposition(
        "d", "e", "l", "q", tag="bppl_right_decomposition"
    )
    prefix_pointwise = _pointwise_le("l", tag="bppl_prefix")

    return (
        spec(
            "beta_product_pointwise_le",
            pointwise_statement,
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "mul_le_mul",
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
                "have hn1 : n = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero n",
                "apply beta_product_zero",
                "exact hn",
                "have hq1 : q = 1",
                "specialize beta_product_zero d",
                "specialize beta_product_zero e",
                "specialize beta_product_zero q",
                "apply beta_product_zero",
                "exact hq",
                "rewrite hn1",
                "rewrite hq1",
                "specialize le_refl 1",
                "exact le_refl",
                "intro n",
                "intro q",
                "intro hpw",
                "intro hn",
                "intro hq",
                f"have hnd : {left_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose n",
                "apply beta_product_succ_decompose",
                "exact hn",
                "cases hnd",
                "cases hnd_witness",
                "cases hnd_witness_witness",
                "cases hnd_witness_witness_right",
                f"have hqd : {right_decomposition}",
                "specialize beta_product_succ_decompose d",
                "specialize beta_product_succ_decompose e",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose q",
                "apply beta_product_succ_decompose",
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
                "have hprefix : exists k. k + x1 = x3",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hpw_prefix",
                "exact hnd_witness_witness_right_left",
                "exact hqd_witness_witness_right_left",
                "have hentry : exists k. k + x = x2",
                "specialize hpw l",
                "specialize hpw x",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hnd_witness_witness_left",
                "exact hqd_witness_witness_left",
                "have hfold : exists k. k + (x1 * x) = (x3 * x2)",
                "specialize mul_le_mul x1",
                "specialize mul_le_mul x3",
                "specialize mul_le_mul x",
                "specialize mul_le_mul x2",
                "apply mul_le_mul",
                "exact hprefix",
                "exact hentry",
                "rewrite hnd_witness_witness_right_right",
                "rewrite hqd_witness_witness_right_right",
                "exact hfold",
            ),
            "Pointwise bounded decoded prefixes have ordered finite products.",
        ),
        spec(
            "beta_product_uniform_le_pow",
            uniform_statement,
            (
                "beta_repeat_entry_eq",
                "beta_product_pointwise_le",
            ),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro n",
                "intro q",
                "intro huniform",
                "intro hn",
                "intro hq",
                "cases hq",
                "cases hq_witness",
                "cases hq_witness_witness",
                "specialize beta_product_pointwise_le b",
                "specialize beta_product_pointwise_le c",
                "specialize beta_product_pointwise_le x",
                "specialize beta_product_pointwise_le x1",
                "specialize beta_product_pointwise_le l",
                "specialize beta_product_pointwise_le n",
                "specialize beta_product_pointwise_le q",
                "apply beta_product_pointwise_le",
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
                "exact hq_witness_witness_left",
                "exact hi",
                "exact hz",
                "rewrite hza",
                "specialize huniform i",
                "specialize huniform p",
                "apply huniform",
                "exact hi",
                "exact hp",
                "exact hn",
                "exact hq_witness_witness_right",
            ),
            "A uniformly bounded finite product is at most the matching power.",
        ),
    )


__all__ = ["make_finite_product_order_candidate_theorems"]
