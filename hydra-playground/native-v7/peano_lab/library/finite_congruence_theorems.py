"""Pointwise balanced-congruence transport for beta-coded finite folds.

This is an isolated, untrusted theorem-spec factory.  Its two public theorem
contracts contain only fully expanded first-order PA formulas: no ``BetaAt``,
``Product``, ``Sum``, or congruence predicate is added to the parser or kernel.
The checked proofs are constructive inductions over the common prefix length.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation, sum_relation


def _mod_eq(modulus: str, left: str, right: str, *, tag: str) -> str:
    """Expand balanced natural congruence for trusted internal identifiers."""

    return (
        f"exists fc_u_{tag} fc_v_{tag}. "
        f"{left} + {modulus} * fc_u_{tag} = "
        f"{right} + {modulus} * fc_v_{tag}"
    )


def _pointwise_mod(length: str, *, tag: str) -> str:
    """Expand pointwise congruence of two decoded prefixes."""

    left = beta_at("b", "c", "i", "a", tag=f"{tag}_la")
    right = beta_at("d", "e", "i", "z", tag=f"{tag}_ra")
    congruence = _mod_eq("m", "a", "z", tag=f"{tag}_me")
    return (
        f"forall i a z. (exists fc_h_{tag}. "
        f"fc_h_{tag} + S i = {length}) -> "
        f"({left}) -> ({right}) -> {congruence}"
    )


def _product_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_a")
    prefix = product_relation(code, scale, length, "r", tag=f"{tag}_p")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r * a)"


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_a")
    prefix = sum_relation(code, scale, length, "r", tag=f"{tag}_p")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_finite_congruence_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered finite-fold congruence tranche."""

    product_pointwise = _pointwise_mod("l", tag="pp")
    product_left = product_relation("b", "c", "l", "n", tag="pl")
    product_right = product_relation("d", "e", "l", "q", tag="pr")
    product_result = _mod_eq("m", "n", "q", tag="pv")
    product_statement = (
        f"forall m b c d e l n q. ({product_pointwise}) -> "
        f"({product_left}) -> ({product_right}) -> {product_result}"
    )

    sum_pointwise = _pointwise_mod("l", tag="sp")
    sum_left = sum_relation("b", "c", "l", "n", tag="sl")
    sum_right = sum_relation("d", "e", "l", "q", tag="sr")
    sum_result = _mod_eq("m", "n", "q", tag="sv")
    sum_statement = (
        f"forall m b c d e l n q. ({sum_pointwise}) -> "
        f"({sum_left}) -> ({sum_right}) -> {sum_result}"
    )

    product_prefix_pointwise = _pointwise_mod("l", tag="pp_pre")
    sum_prefix_pointwise = _pointwise_mod("l", tag="sp_pre")
    left_product_decomposition = _product_decomposition(
        "b", "c", "l", "n", tag="pd_l"
    )
    right_product_decomposition = _product_decomposition(
        "d", "e", "l", "q", tag="pd_r"
    )
    left_sum_decomposition = _sum_decomposition(
        "b", "c", "l", "n", tag="sd_l"
    )
    right_sum_decomposition = _sum_decomposition(
        "d", "e", "l", "q", tag="sd_r"
    )

    return (
        spec(
            "beta_product_pointwise_mod_congruent",
            product_statement,
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "le_succ",
                "le_refl",
                "mod_eq_refl",
                "mod_eq_mul",
            ),
            (
                "intro m",
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
                "specialize mod_eq_refl m",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro n",
                "intro q",
                "intro hpw",
                "intro hn",
                "intro hq",
                f"have hnd : {left_product_decomposition}",
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
                f"have hqd : {right_product_decomposition}",
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
                f"have hpw_prefix : {product_prefix_pointwise}",
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
                "have hprefix : exists u v. x1 + m * u = x3 + m * v",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hpw_prefix",
                "exact hnd_witness_witness_right_left",
                "exact hqd_witness_witness_right_left",
                "have hentry : exists u v. x + m * u = x2 + m * v",
                "specialize hpw l",
                "specialize hpw x",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hnd_witness_witness_left",
                "exact hqd_witness_witness_left",
                "have hfold : exists u v. (x1 * x) + m * u = "
                "(x3 * x2) + m * v",
                "specialize mod_eq_mul m",
                "specialize mod_eq_mul x1",
                "specialize mod_eq_mul x3",
                "specialize mod_eq_mul x",
                "specialize mod_eq_mul x2",
                "apply mod_eq_mul",
                "exact hprefix",
                "exact hentry",
                "rewrite hnd_witness_witness_right_right",
                "rewrite hqd_witness_witness_right_right",
                "exact hfold",
            ),
            "Pointwise congruent decoded prefixes have congruent finite products.",
        ),
        spec(
            "beta_sum_pointwise_mod_congruent",
            sum_statement,
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "le_succ",
                "le_refl",
                "mod_eq_refl",
                "mod_eq_add",
            ),
            (
                "intro m",
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
                "specialize mod_eq_refl m",
                "specialize mod_eq_refl 0",
                "exact mod_eq_refl",
                "intro n",
                "intro q",
                "intro hpw",
                "intro hn",
                "intro hq",
                f"have hnd : {left_sum_decomposition}",
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
                f"have hqd : {right_sum_decomposition}",
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
                f"have hpw_prefix : {sum_prefix_pointwise}",
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
                "have hprefix : exists u v. x1 + m * u = x3 + m * v",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hpw_prefix",
                "exact hnd_witness_witness_right_left",
                "exact hqd_witness_witness_right_left",
                "have hentry : exists u v. x + m * u = x2 + m * v",
                "specialize hpw l",
                "specialize hpw x",
                "specialize hpw x2",
                "apply hpw",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hnd_witness_witness_left",
                "exact hqd_witness_witness_left",
                "have hfold : exists u v. (x1 + x) + m * u = "
                "(x3 + x2) + m * v",
                "specialize mod_eq_add m",
                "specialize mod_eq_add x1",
                "specialize mod_eq_add x3",
                "specialize mod_eq_add x",
                "specialize mod_eq_add x2",
                "apply mod_eq_add",
                "exact hprefix",
                "exact hentry",
                "rewrite hnd_witness_witness_right_right",
                "rewrite hqd_witness_witness_right_right",
                "exact hfold",
            ),
            "Pointwise congruent decoded prefixes have congruent finite sums.",
        ),
    )


__all__ = ["make_finite_congruence_theorems"]
