"""Generic adjacent-pair products as relational powers.

For a beta-coded factor prefix, pair ``t`` occupies positions ``t+t`` and
``S (t+t)``.  ``adjacent_target_pairs`` says that every decoded pair product
is congruent to one fixed natural ``a`` modulo ``p``.  The theorem below then
identifies the exact product of the first ``m+m`` entries with a relational
``Pow(a,m,A)`` modulo ``p``.

This is an authoring-only surface over the unchanged first-order Peano
language.  It introduces no exponentiation, sequence, product, or congruence
primitive, is intentionally absent from the public registry, and must not be
confused with recursive closure or admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation
from .wilson_pair_product_candidate import (
    _beta_at_term,
    _binders,
    _identifier,
    _mod_eq_term,
    _product_relation_term,
    _strictly_below_term,
    _two_factor_decomposition,
)


def _adjacent_target_pairs_term(
    modulus: str,
    target: str,
    code: str,
    scale: str,
    pair_count: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    pair, left, right = _binders(tag, avoid, ("pair", "left", "right"))
    owned = avoid + (pair, left, right)
    bound = _strictly_below_term(
        pair,
        pair_count,
        tag=f"{tag}_pair_bound",
        avoid=owned,
    )
    left_entry = _beta_at_term(
        code,
        scale,
        f"({pair} + {pair})",
        left,
        tag=f"{tag}_left_entry",
        avoid=owned,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        f"S ({pair} + {pair})",
        right,
        tag=f"{tag}_right_entry",
        avoid=owned,
    )
    pair_congruence = _mod_eq_term(
        modulus,
        f"{left} * {right}",
        target,
        tag=f"{tag}_pair_mod",
        avoid=owned,
    )
    return (
        f"forall {pair} {left} {right}. ({bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> ({pair_congruence})"
    )


def adjacent_target_pairs(
    modulus: str,
    target: str,
    code: str,
    scale: str,
    pair_count: str,
    *,
    tag: str,
) -> str:
    """Expand the fixed-target adjacent-pair condition through ``pair_count``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (target, "pair target"),
            (code, "factor code"),
            (scale, "factor scale"),
            (pair_count, "pair count"),
        )
    )
    return _adjacent_target_pairs_term(
        modulus,
        target,
        code,
        scale,
        pair_count,
        tag=tag,
        avoid=variables,
    )


def make_euler_pair_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated adjacent-target product-to-power candidate."""

    pairs = adjacent_target_pairs("p", "a", "b", "c", "m", tag="pairs")
    product = _product_relation_term(
        "b",
        "c",
        "m + m",
        "Q",
        tag="target_product",
        avoid=("p", "a", "b", "c", "m", "Q", "A"),
    )
    power = power_relation("a", "m", "A", tag="target_power")
    result = _mod_eq_term(
        "p",
        "Q",
        "A",
        tag="target_result",
        avoid=("p", "a", "b", "c", "m", "Q", "A"),
    )

    successor_decomposition = _two_factor_decomposition(
        "b",
        "c",
        "m + m",
        "Q",
        tag="target_successor_decomposition",
        avoid=("p", "a", "b", "c", "m", "Q", "A"),
    )
    all_successor_pairs = _adjacent_target_pairs_term(
        "p",
        "a",
        "b",
        "c",
        "S m",
        tag="target_all_successor_pairs",
        avoid=("p", "a", "b", "c", "m", "Q", "A"),
    )
    prefix_pairs = adjacent_target_pairs(
        "p", "a", "b", "c", "m", tag="target_prefix_pairs"
    )
    successor_power_decomposition = (
        f"exists r. ({power_relation('a', 'm', 'r', tag='target_predecessor_power')}) "
        "/\\ A = r * a"
    )
    prefix_congruence = _mod_eq_term(
        "p",
        "x2",
        "x3",
        tag="target_prefix_congruence",
        avoid=("p", "a", "b", "c", "m", "Q", "A", "x", "x1", "x2", "x3"),
    )
    last_pair_congruence = _mod_eq_term(
        "p",
        "x * x1",
        "a",
        tag="target_last_pair_congruence",
        avoid=("p", "a", "b", "c", "m", "Q", "A", "x", "x1", "x2", "x3"),
    )
    folded_congruence = _mod_eq_term(
        "p",
        "x2 * (x * x1)",
        "x3 * a",
        tag="target_folded_congruence",
        avoid=("p", "a", "b", "c", "m", "Q", "A", "x", "x1", "x2", "x3"),
    )

    return (
        spec(
            "beta_adjacent_target_pairs_product_power",
            f"forall p a b c m Q A. ({pairs}) -> ({product}) -> "
            f"({power}) -> ({result})",
            (
                "beta_product_double_succ_decompose",
                "beta_product_zero",
                "pow_zero",
                "pow_successor_decompose",
                "le_succ",
                "le_refl",
                "mod_eq_refl",
                "mod_eq_mul",
                "add_succ_left",
                "mul_assoc",
            ),
            (
                "intro p",
                "intro a",
                "intro b",
                "intro c",
                "induction m",
                "intro Q",
                "intro A",
                "intro hpairs",
                "intro hproduct",
                "intro hpower",
                "have hzero : 0 + 0 = 0",
                "simp",
                "rewrite hzero at hproduct",
                "rewrite hzero at hproduct",
                "rewrite hzero at hproduct",
                "have hQ : Q = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero Q",
                "apply beta_product_zero",
                "exact hproduct",
                "have hA : A = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero A",
                "apply pow_zero",
                "refl",
                "exact hpower",
                "rewrite hQ",
                "rewrite hA",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro Q",
                "intro A",
                "intro hpairs",
                "intro hproduct",
                "intro hpower",
                "have hdouble : S m + S m = S (S (m + m))",
                "simp [add_succ_left]",
                f"have hdecomposition : {successor_decomposition}",
                "specialize beta_product_double_succ_decompose b",
                "specialize beta_product_double_succ_decompose c",
                "specialize beta_product_double_succ_decompose (m + m)",
                "specialize beta_product_double_succ_decompose (S m + S m)",
                "specialize beta_product_double_succ_decompose Q",
                "apply beta_product_double_succ_decompose",
                "exact hdouble",
                "exact hproduct",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_witness",
                "cases hdecomposition_witness_witness_witness_right",
                "cases hdecomposition_witness_witness_witness_right_right",
                f"have hpairs_all : {all_successor_pairs}",
                "exact hpairs",
                f"have hpairs_prefix : {prefix_pairs}",
                "intro t",
                "intro u",
                "intro v",
                "intro ht",
                "intro hu",
                "intro hv",
                "specialize hpairs_all t",
                "specialize hpairs_all u",
                "specialize hpairs_all v",
                "apply hpairs_all",
                "specialize le_succ (S t)",
                "specialize le_succ m",
                "apply le_succ",
                "exact ht",
                "exact hu",
                "exact hv",
                f"have hpower_step : {successor_power_decomposition}",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose m",
                "specialize pow_successor_decompose (S m)",
                "specialize pow_successor_decompose A",
                "apply pow_successor_decompose",
                "refl",
                "exact hpower",
                "cases hpower_step",
                "cases hpower_step_witness",
                f"have hprefix : {prefix_congruence}",
                "specialize IH x2",
                "specialize IH x3",
                "apply IH",
                "exact hpairs_prefix",
                "exact hdecomposition_witness_witness_witness_right_right_left",
                "exact hpower_step_witness_left",
                f"have hlast : {last_pair_congruence}",
                "specialize hpairs m",
                "specialize hpairs x",
                "specialize hpairs x1",
                "apply hpairs",
                "specialize le_refl (S m)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_witness_left",
                "exact hdecomposition_witness_witness_witness_right_left",
                f"have hfold : {folded_congruence}",
                "specialize mod_eq_mul p",
                "specialize mod_eq_mul x2",
                "specialize mod_eq_mul x3",
                "specialize mod_eq_mul (x * x1)",
                "specialize mod_eq_mul a",
                "apply mod_eq_mul",
                "exact hprefix",
                "exact hlast",
                "have hassoc : (x2 * x) * x1 = x2 * (x * x1)",
                "specialize mul_assoc x2",
                "specialize mul_assoc x",
                "specialize mul_assoc x1",
                "exact mul_assoc",
                "rewrite hdecomposition_witness_witness_witness_right_right_right",
                "rewrite hassoc",
                "rewrite hpower_step_witness_right",
                "exact hfold",
            ),
            "Adjacent fixed-target pairs multiply to the corresponding relational power.",
        ),
    )


__all__ = [
    "adjacent_target_pairs",
    "make_euler_pair_product_candidate_theorems",
]
