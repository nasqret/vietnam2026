"""Successor-lift a paired inverse order into Wilson factor values.

PairOrder stores zero-based inverse indices.  Wilson's product consumes the
actual residues, so an entry i must become S i before the adjacent-pair fold.
The generic beta_successor_lift_exists candidate already constructs that
recoding.  This module proves that a bounded paired order becomes an
AdjacentUnitPairs factor code and packages its exact product.

The candidates remain isolated and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_omission_candidate import _bounded_into_term
from .wilson_inverse_prefix_candidate import inverse_prefix
from .wilson_pair_order_candidate import _beta_at_term, _lt_term
from .wilson_pair_order_paired_iteration_candidate import (
    paired_inverse_witness,
)
from .wilson_pair_product_candidate import (
    _mod_eq_term,
    _product_relation_term,
    adjacent_unit_pairs,
)


def _successor_lift_prefix_term(
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    index = f"wsl_index_{tag}"
    value = f"wsl_value_{tag}"
    local = avoid + (index, value)
    bound = _lt_term(
        index, length, tag=f"{tag}_bound", avoid=local
    )
    source = _beta_at_term(
        source_code,
        source_scale,
        index,
        value,
        tag=f"{tag}_source",
        avoid=local,
    )
    target = _beta_at_term(
        target_code,
        target_scale,
        index,
        f"S {value}",
        tag=f"{tag}_target",
        avoid=local,
    )
    return (
        f"forall {index} {value}. ({bound}) -> "
        f"({source}) -> ({target})"
    )


def successor_lift_prefix(
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise successor recoding across a beta prefix."""

    variables = (
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
    )
    return _successor_lift_prefix_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def make_wilson_successor_lift_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build lift existence, adjacent-unit transport, and product endpoint."""

    lift = _successor_lift_prefix_term(
        "b",
        "c",
        "f",
        "g",
        "m + m",
        tag="wsl_lift",
        avoid=("p", "n", "u", "v", "b", "c", "f", "g", "m"),
    )
    bounded = _bounded_into_term(
        "b",
        "c",
        "m + m",
        "n",
        tag="wsl_bounded",
        avoid=("p", "n", "u", "v", "b", "c", "f", "g", "m"),
    )
    pairs = paired_inverse_witness(
        "u", "v", "b", "c", "m", tag="wsl_pairs"
    )
    inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wsl_inverse"
    )
    adjacent = adjacent_unit_pairs(
        "p", "f", "g", "m", tag="wsl_adjacent"
    )
    product = _product_relation_term(
        "f",
        "g",
        "m + m",
        "Q",
        tag="wsl_product",
        avoid=("p", "n", "u", "v", "b", "c", "f", "g", "m", "Q"),
    )
    product_mod_one = _mod_eq_term(
        "p",
        "Q",
        "1",
        tag="wsl_product_mod_one",
        avoid=("p", "n", "u", "v", "b", "c", "f", "g", "m", "Q"),
    )

    lift_exists_result = f"exists f g. ({lift})"
    factor_result = f"exists f g. (({lift}) /\ ({adjacent}))"
    product_result = (
        f"exists f g Q. (({lift}) /\ (({adjacent}) /\ "
        f"(({product}) /\ ({product_mod_one}))))"
    )

    variables = (
        "p",
        "n",
        "u",
        "v",
        "b",
        "c",
        "f",
        "g",
        "m",
        "t",
        "a",
        "d",
        "i",
        "j",
        "w",
        "q",
    )
    even_bound = _lt_term(
        "t + t",
        "m + m",
        tag="wsl_even_bound",
        avoid=variables,
    )
    odd_bound = _lt_term(
        "S (t + t)",
        "m + m",
        tag="wsl_odd_bound",
        avoid=variables,
    )
    order_even_i = _beta_at_term(
        "b",
        "c",
        "t + t",
        "i",
        tag="wsl_order_even_i",
        avoid=variables,
    )
    order_odd_j = _beta_at_term(
        "b",
        "c",
        "S (t + t)",
        "j",
        tag="wsl_order_odd_j",
        avoid=variables,
    )
    inverse_i_j = _beta_at_term(
        "u",
        "v",
        "i",
        "j",
        tag="wsl_inverse_i_j",
        avoid=variables,
    )
    pair_occurrence = (
        f"exists i j. (({order_even_i}) /\ "
        f"(({order_odd_j}) /\ ({inverse_i_j})))"
    )
    lifted_even_i = _beta_at_term(
        "f",
        "g",
        "t + t",
        "S x",
        tag="wsl_lifted_even_i",
        avoid=variables + ("x", "x1", "x2", "x3"),
    )
    lifted_odd_j = _beta_at_term(
        "f",
        "g",
        "S (t + t)",
        "S x1",
        tag="wsl_lifted_odd_j",
        avoid=variables + ("x", "x1", "x2", "x3"),
    )
    factor_even_a = _beta_at_term(
        "f",
        "g",
        "t + t",
        "a",
        tag="wsl_factor_even_a",
        avoid=variables,
    )
    factor_odd_d = _beta_at_term(
        "f",
        "g",
        "S (t + t)",
        "d",
        tag="wsl_factor_odd_d",
        avoid=variables,
    )
    bounded_even = (
        "exists w. "
        f"(({_beta_at_term('b', 'c', 't + t', 'w', tag='wsl_bounded_even_entry', avoid=variables)}) /\ "
        f"({_lt_term('w', 'n', tag='wsl_bounded_even_value', avoid=variables)}))"
    )
    inverse_at_i = (
        "exists q. "
        f"(({_beta_at_term('u', 'v', 'x', 'q', tag='wsl_inverse_at_i_entry', avoid=variables + ('x', 'x1', 'x2', 'x3'))}) /\ "
        f"(({_lt_term('x', 'n', tag='wsl_inverse_at_i_source_bound', avoid=variables + ('x', 'x1', 'x2', 'x3'))}) /\ "
        f"(({_lt_term('q', 'n', tag='wsl_inverse_at_i_mate_bound', avoid=variables + ('x', 'x1', 'x2', 'x3'))}) /\ "
        "exists y z. (S x * S q) + p * y = 1 + p * z)))"
    )

    return (
        spec(
            "pair_order_successor_lift_exists",
            f"forall b c m. ({lift_exists_result})",
            ("beta_successor_lift_exists",),
            (
                "intro b",
                "intro c",
                "intro m",
                "specialize beta_successor_lift_exists b",
                "specialize beta_successor_lift_exists c",
                "specialize beta_successor_lift_exists (m + m)",
                "exact beta_successor_lift_exists",
            ),
            "Every zero-based pair order has a beta code of successor-valued factors.",
        ),
        spec(
            "paired_successor_lift_adjacent_units",
            "forall p n u v b c f g m. "
            f"({inverse}) -> ({bounded}) -> ({pairs}) -> ({lift}) -> "
            f"({adjacent})",
            (
                "pair_index_left_below_double",
                "pair_index_right_below_double",
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro f",
                "intro g",
                "intro m",
                "intro hinverse",
                "intro hbounded",
                "intro hpairs",
                "intro hlift",
                "intro t",
                "intro a",
                "intro d",
                "intro ht",
                "intro ha",
                "intro hd",
                f"have hpair : {pair_occurrence}",
                "specialize hpairs t",
                "apply hpairs",
                "exact ht",
                "cases hpair",
                "cases hpair_witness",
                "cases hpair_witness_witness",
                "cases hpair_witness_witness_right",
                f"have heven : {even_bound}",
                "specialize pair_index_left_below_double t",
                "specialize pair_index_left_below_double m",
                "apply pair_index_left_below_double",
                "exact ht",
                f"have hodd : {odd_bound}",
                "specialize pair_index_right_below_double t",
                "specialize pair_index_right_below_double m",
                "apply pair_index_right_below_double",
                "exact ht",
                f"have hlift_left : {lifted_even_i}",
                "specialize hlift (t + t)",
                "specialize hlift x",
                "apply hlift",
                "exact heven",
                "exact hpair_witness_witness_left",
                f"have hlift_right : {lifted_odd_j}",
                "specialize hlift (S (t + t))",
                "specialize hlift x1",
                "apply hlift",
                "exact hodd",
                "exact hpair_witness_witness_right_left",
                "have haeq : a = S x",
                "specialize beta_at_unique f",
                "specialize beta_at_unique g",
                "specialize beta_at_unique (t + t)",
                "specialize beta_at_unique a",
                "specialize beta_at_unique (S x)",
                "apply beta_at_unique",
                "exact ha",
                "exact hlift_left",
                "have hdeq : d = S x1",
                "specialize beta_at_unique f",
                "specialize beta_at_unique g",
                "specialize beta_at_unique (S (t + t))",
                "specialize beta_at_unique d",
                "specialize beta_at_unique (S x1)",
                "apply beta_at_unique",
                "exact hd",
                "exact hlift_right",
                f"have hbounded_data : {bounded_even}",
                "specialize hbounded (t + t)",
                "apply hbounded",
                "exact heven",
                "cases hbounded_data",
                "cases hbounded_data_witness",
                "have hieq : x = x2",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (t + t)",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact hpair_witness_witness_left",
                "exact hbounded_data_witness_left",
                "have hibound : exists h. h + S x = n",
                "rewrite hieq",
                "exact hbounded_data_witness_right",
                f"have hinverse_data : {inverse_at_i}",
                "specialize hinverse x",
                "apply hinverse",
                "exact hibound",
                "cases hinverse_data",
                "cases hinverse_data_witness",
                "cases hinverse_data_witness_right",
                "cases hinverse_data_witness_right_right",
                "have hjeq : x1 = x3",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x3",
                "apply beta_at_unique",
                "exact hpair_witness_witness_right_right",
                "exact hinverse_data_witness_left",
                "rewrite haeq",
                "rewrite hdeq",
                "rewrite hjeq",
                "exact hinverse_data_witness_right_right_right",
            ),
            "Successor-lifted adjacent inverse indices multiply to one modulo p.",
        ),
        spec(
            "paired_pair_order_factor_code_exists",
            "forall p n u v b c m. "
            f"({inverse}) -> ({bounded}) -> ({pairs}) -> ({factor_result})",
            (
                "pair_order_successor_lift_exists",
                "paired_successor_lift_adjacent_units",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro m",
                "intro hinverse",
                "intro hbounded",
                "intro hpairs",
                f"have hlift_exists : {lift_exists_result}",
                "specialize pair_order_successor_lift_exists b",
                "specialize pair_order_successor_lift_exists c",
                "specialize pair_order_successor_lift_exists m",
                "exact pair_order_successor_lift_exists",
                "cases hlift_exists",
                "cases hlift_exists_witness",
                "exists x",
                "exists x1",
                "split",
                "exact hlift_exists_witness_witness",
                "specialize paired_successor_lift_adjacent_units p",
                "specialize paired_successor_lift_adjacent_units n",
                "specialize paired_successor_lift_adjacent_units u",
                "specialize paired_successor_lift_adjacent_units v",
                "specialize paired_successor_lift_adjacent_units b",
                "specialize paired_successor_lift_adjacent_units c",
                "specialize paired_successor_lift_adjacent_units x",
                "specialize paired_successor_lift_adjacent_units x1",
                "specialize paired_successor_lift_adjacent_units m",
                "apply paired_successor_lift_adjacent_units",
                "exact hinverse",
                "exact hbounded",
                "exact hpairs",
                "exact hlift_exists_witness_witness",
            ),
            "Package a successor-valued factor code with adjacent unit pairs.",
        ),
        spec(
            "paired_pair_order_product_one_exists",
            "forall p n u v b c m. "
            f"({inverse}) -> ({bounded}) -> ({pairs}) -> ({product_result})",
            (
                "paired_pair_order_factor_code_exists",
                "beta_product_exists",
                "beta_adjacent_unit_pairs_product_one",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro m",
                "intro hinverse",
                "intro hbounded",
                "intro hpairs",
                f"have hfactors : {factor_result}",
                "specialize paired_pair_order_factor_code_exists p",
                "specialize paired_pair_order_factor_code_exists n",
                "specialize paired_pair_order_factor_code_exists u",
                "specialize paired_pair_order_factor_code_exists v",
                "specialize paired_pair_order_factor_code_exists b",
                "specialize paired_pair_order_factor_code_exists c",
                "specialize paired_pair_order_factor_code_exists m",
                "apply paired_pair_order_factor_code_exists",
                "exact hinverse",
                "exact hbounded",
                "exact hpairs",
                "cases hfactors",
                "cases hfactors_witness",
                "cases hfactors_witness_witness",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists (m + m)",
                "cases beta_product_exists",
                "cases beta_product_exists_witness",
                "cases beta_product_exists_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hfactors_witness_witness_left",
                "split",
                "exact hfactors_witness_witness_right",
                "split",
                "exists x3",
                "exists x4",
                "exact beta_product_exists_witness_witness_witness",
                "specialize beta_adjacent_unit_pairs_product_one p",
                "specialize beta_adjacent_unit_pairs_product_one x",
                "specialize beta_adjacent_unit_pairs_product_one x1",
                "specialize beta_adjacent_unit_pairs_product_one m",
                "specialize beta_adjacent_unit_pairs_product_one x2",
                "apply beta_adjacent_unit_pairs_product_one",
                "exact hfactors_witness_witness_right",
                "exists x3",
                "exists x4",
                "exact beta_product_exists_witness_witness_witness",
            ),
            "The complete successor-lifted nonendpoint factor product is one modulo p.",
        ),
    )


__all__ = [
    "make_wilson_successor_lift_candidate_theorems",
    "successor_lift_prefix",
]
