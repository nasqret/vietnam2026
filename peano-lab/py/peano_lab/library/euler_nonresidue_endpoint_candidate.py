"""Constructive nonresidue endpoint for Euler's criterion.

The terminal scaled PairOrder stores zero-based source indices, while its
history retains an actual scaled edge ``At(u,v,i,S j)`` for each adjacent
pair.  This module successor-lifts the order to the actual factors
``S i,S j``, transports the history to adjacent products congruent to ``a``,
and identifies the lifted product with the relational factorial.  Wilson's
checked factorial congruence then gives ``a^h == p-1 (mod p)``.

Every helper expands before parsing to unchanged first-order Peano
arithmetic.  The theorem factory is intentionally unregistered,
dependency-curried, constructive, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_pair_product_candidate import adjacent_target_pairs
from .euler_scaled_inverse_candidate import prime
from .euler_scaled_inverse_prefix_candidate import (
    scaled_inverse_index,
    scaled_inverse_prefix,
)
from .euler_scaled_pair_order_iteration_candidate import (
    _scaled_pair_order_state_term,
    adjacent_scaled_orbit_history,
)
from .finite_factorial_theorems import factorial_relation
from .finite_fold_surface import (
    _beta_at_term,
    _product_relation_term,
    power_relation,
)
from .finite_omission_candidate import _bounded_into_term
from .finite_product_reindex_support import _aligned_prefix_term
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import _injective_prefix_term, _lt_term
from .wilson_pair_product_candidate import _mod_eq_term
from .wilson_successor_lift_candidate import _successor_lift_prefix_term


def _conjunction(*parts: str) -> str:
    if not parts:
        raise ValueError("a conjunction needs at least one part")
    result = parts[-1]
    for part in reversed(parts[:-1]):
        result = f"({part}) /\\ ({result})"
    return result


def make_euler_nonresidue_endpoint_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build semantic lift, factorial comparison, and nonresidue endpoint."""

    variables = (
        "p",
        "a",
        "n",
        "u",
        "v",
        "b",
        "c",
        "f",
        "g",
        "h",
        "A",
        "F",
        "Q",
    )

    prefix = scaled_inverse_prefix(
        "p", "a", "n", "u", "v", "n", tag="enr_prefix"
    )
    raw_bounded = _bounded_into_term(
        "b",
        "c",
        "h + h",
        "n",
        tag="enr_raw_bounded",
        avoid=variables,
    )
    history = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "h", tag="enr_history"
    )
    lift_n = _successor_lift_prefix_term(
        "b", "c", "f", "g", "n", tag="enr_lift_n", avoid=variables
    )
    target_pairs = adjacent_target_pairs(
        "p", "a", "f", "g", "h", tag="enr_target_pairs"
    )

    occurrence_variables = variables + ("t", "left", "right", "i", "j")
    history_occurrence = "exists i j. " + _conjunction(
        _beta_at_term(
            "b",
            "c",
            "t + t",
            "i",
            tag="enr_history_left",
            avoid=occurrence_variables,
        ),
        _beta_at_term(
            "b",
            "c",
            "S (t + t)",
            "j",
            tag="enr_history_right",
            avoid=occurrence_variables,
        ),
        _beta_at_term(
            "u",
            "v",
            "i",
            "S j",
            tag="enr_history_scaled",
            avoid=occurrence_variables,
        ),
    )
    even_bound_raw = _lt_term(
        "t + t",
        "h + h",
        tag="enr_even_bound_raw",
        avoid=occurrence_variables,
    )
    odd_bound_raw = _lt_term(
        "S (t + t)",
        "h + h",
        tag="enr_odd_bound_raw",
        avoid=occurrence_variables,
    )
    even_bound_n = _lt_term(
        "t + t",
        "n",
        tag="enr_even_bound_n",
        avoid=occurrence_variables,
    )
    odd_bound_n = _lt_term(
        "S (t + t)",
        "n",
        tag="enr_odd_bound_n",
        avoid=occurrence_variables,
    )
    lifted_left = _beta_at_term(
        "f",
        "g",
        "t + t",
        "S x",
        tag="enr_lifted_left",
        avoid=occurrence_variables + ("x", "x1", "x2", "x3"),
    )
    lifted_right = _beta_at_term(
        "f",
        "g",
        "S (t + t)",
        "S x1",
        tag="enr_lifted_right",
        avoid=occurrence_variables + ("x", "x1", "x2", "x3"),
    )
    bounded_even = (
        "exists w. "
        + _conjunction(
            _beta_at_term(
                "b",
                "c",
                "t + t",
                "w",
                tag="enr_bounded_even_entry",
                avoid=occurrence_variables + ("w",),
            ),
            _lt_term(
                "w",
                "n",
                tag="enr_bounded_even_value",
                avoid=occurrence_variables + ("w",),
            ),
        )
    )
    prefix_at_x = (
        "exists y. "
        + _conjunction(
            _beta_at_term(
                "u",
                "v",
                "x",
                "y",
                tag="enr_prefix_at_x_entry",
                avoid=occurrence_variables + ("x", "x1", "x2", "x3", "y"),
            ),
            scaled_inverse_index(
                "p", "a", "n", "x", "y", tag="enr_prefix_at_x_relation"
            ),
        )
    )

    generic_bounded = _bounded_into_term(
        "b", "c", "n", "n", tag="enr_generic_bounded", avoid=variables
    )
    generic_injective = _injective_prefix_term(
        "b", "c", "n", tag="enr_generic_injective", avoid=variables
    )
    generic_lift = _successor_lift_prefix_term(
        "b", "c", "f", "g", "n", tag="enr_generic_lift", avoid=variables
    )
    lifted_product = _product_relation_term(
        "f", "g", "n", "Q", tag="enr_lifted_product", avoid=variables
    )
    factorial = factorial_relation("n", "F", tag="enr_factorial")

    alignment_variables = variables + ("x", "x1", "i", "j", "y")
    alignment_x = _aligned_prefix_term(
        "b",
        "c",
        "x",
        "x1",
        "f",
        "g",
        "n",
        tag="enr_alignment_x",
        avoid=alignment_variables,
    )
    generic_bounded_at_i = (
        "exists w. "
        + _conjunction(
            _beta_at_term(
                "b",
                "c",
                "i",
                "w",
                tag="enr_generic_bounded_entry",
                avoid=alignment_variables + ("w",),
            ),
            _lt_term(
                "w",
                "n",
                tag="enr_generic_bounded_value",
                avoid=alignment_variables + ("w",),
            ),
        )
    )
    generic_lifted_at_i = _beta_at_term(
        "f",
        "g",
        "i",
        "S j",
        tag="enr_generic_lifted_at_i",
        avoid=alignment_variables,
    )

    terminal_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "h + h",
        "n",
        tag="enr_terminal_state",
        avoid=variables,
    )
    terminal_power = power_relation("a", "h", "A", tag="enr_terminal_power")
    terminal_result = _mod_eq_term(
        "p", "A", "n", tag="enr_terminal_result", avoid=variables
    )
    target_pairs_x = adjacent_target_pairs(
        "p", "a", "x", "x1", "h", tag="enr_target_pairs_x"
    )
    terminal_product_exists_x = (
        "exists Q. "
        + _product_relation_term(
            "x",
            "x1",
            "n",
            "Q",
            tag="enr_terminal_product_x",
            avoid=variables + ("x", "x1"),
        )
    )
    terminal_product_even_x2 = _product_relation_term(
        "x",
        "x1",
        "h + h",
        "x2",
        tag="enr_terminal_product_even",
        avoid=variables + ("x", "x1", "x2"),
    )
    terminal_factorial = factorial_relation("n", "F", tag="enr_terminal_factorial")
    product_mod_power_x2 = _mod_eq_term(
        "p",
        "x2",
        "A",
        tag="enr_product_mod_power",
        avoid=variables + ("x2",),
    )
    power_mod_product_x2 = _mod_eq_term(
        "p",
        "A",
        "x2",
        tag="enr_power_mod_product",
        avoid=variables + ("x2",),
    )
    power_mod_factorial_x3 = _mod_eq_term(
        "p",
        "A",
        "x3",
        tag="enr_power_mod_factorial",
        avoid=variables + ("x3",),
    )
    factorial_mod_predecessor_x3 = _mod_eq_term(
        "p",
        "x3",
        "n",
        tag="enr_factorial_mod_predecessor",
        avoid=variables + ("x3",),
    )

    nonresidue = quadratic_residue("p", "a", tag="enr_nonresidue")
    prime_p = prime("p", tag="enr_prime")
    terminal_package = (
        "exists b c. "
        + _conjunction(terminal_state, history)
    )
    full_prefix_exists = f"exists u v. ({prefix})"
    target_bound = _lt_term(
        "a", "p", tag="enr_target_bound", avoid=variables
    )

    return (
        spec(
            "scaled_pair_order_successor_lift_adjacent_targets",
            "forall p a n u v b c f g h. n = h + h -> "
            f"({prefix}) -> ({raw_bounded}) -> ({history}) -> ({lift_n}) -> "
            f"({target_pairs})",
            (
                "pair_index_left_below_double",
                "pair_index_right_below_double",
                "beta_at_unique",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro f",
                "intro g",
                "intro h",
                "intro heven",
                "intro hprefix",
                "intro hbounded",
                "intro hhistory",
                "intro hlift",
                "intro t",
                "intro left",
                "intro right",
                "intro ht",
                "intro hleft",
                "intro hright",
                f"have horbit : {history_occurrence}",
                "specialize hhistory t",
                "apply hhistory",
                "exact ht",
                "cases horbit",
                "cases horbit_witness",
                "cases horbit_witness_witness",
                "cases horbit_witness_witness_right",
                f"have heven_raw : {even_bound_raw}",
                "specialize pair_index_left_below_double t",
                "specialize pair_index_left_below_double h",
                "apply pair_index_left_below_double",
                "exact ht",
                f"have hodd_raw : {odd_bound_raw}",
                "specialize pair_index_right_below_double t",
                "specialize pair_index_right_below_double h",
                "apply pair_index_right_below_double",
                "exact ht",
                f"have heven_n : {even_bound_n}",
                "rewrite heven",
                "exact heven_raw",
                f"have hodd_n : {odd_bound_n}",
                "rewrite heven",
                "exact hodd_raw",
                f"have hlift_left : {lifted_left}",
                "specialize hlift (t + t)",
                "specialize hlift x",
                "apply hlift",
                "exact heven_n",
                "exact horbit_witness_witness_left",
                f"have hlift_right : {lifted_right}",
                "specialize hlift (S (t + t))",
                "specialize hlift x1",
                "apply hlift",
                "exact hodd_n",
                "exact horbit_witness_witness_right_left",
                "have hleft_eq : left = S x",
                "specialize beta_at_unique f",
                "specialize beta_at_unique g",
                "specialize beta_at_unique (t + t)",
                "specialize beta_at_unique left",
                "specialize beta_at_unique (S x)",
                "apply beta_at_unique",
                "exact hleft",
                "exact hlift_left",
                "have hright_eq : right = S x1",
                "specialize beta_at_unique f",
                "specialize beta_at_unique g",
                "specialize beta_at_unique (S (t + t))",
                "specialize beta_at_unique right",
                "specialize beta_at_unique (S x1)",
                "apply beta_at_unique",
                "exact hright",
                "exact hlift_right",
                f"have hbounded_even : {bounded_even}",
                "specialize hbounded (t + t)",
                "apply hbounded",
                "exact heven_raw",
                "cases hbounded_even",
                "cases hbounded_even_witness",
                "have hsource_eq : x = x2",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique (t + t)",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact horbit_witness_witness_left",
                "exact hbounded_even_witness_left",
                "have hsource_bound : exists gap. gap + S x = n",
                "rewrite hsource_eq",
                "exact hbounded_even_witness_right",
                f"have hprefix_data : {prefix_at_x}",
                "specialize hprefix x",
                "apply hprefix",
                "exact hsource_bound",
                "cases hprefix_data",
                "cases hprefix_data_witness",
                "cases hprefix_data_witness_right",
                "cases hprefix_data_witness_right_right",
                "cases hprefix_data_witness_right_right_right",
                "have hmate_eq : x3 = S x1",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique (S x1)",
                "apply beta_at_unique",
                "exact hprefix_data_witness_left",
                "exact horbit_witness_witness_right_right",
                "rewrite hleft_eq",
                "rewrite hright_eq",
                "rewrite <- hmate_eq",
                "exact hprefix_data_witness_right_right_right_right",
            ),
            "A successor-lifted terminal scaled-orbit history has adjacent products congruent to a.",
        ),
        spec(
            "scaled_pair_order_successor_lift_product_is_factorial",
            "forall b c f g n Q F. "
            f"({generic_bounded}) -> ({generic_injective}) -> ({generic_lift}) -> "
            f"({lifted_product}) -> ({factorial}) -> Q = F",
            (
                "beta_at_unique",
                "beta_range_entry_eq",
                "beta_product_permutation_invariant",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro b",
                "intro c",
                "intro f",
                "intro g",
                "intro n",
                "intro Q",
                "intro F",
                "intro hbounded",
                "intro hinjective",
                "intro hlift",
                "intro hproduct",
                "intro hfactorial",
                "cases hfactorial",
                "cases hfactorial_witness",
                "cases hfactorial_witness_witness",
                f"have haligned : {alignment_x}",
                "intro i",
                "intro j",
                "intro y",
                "intro hi",
                "intro hmap",
                "intro hsource",
                f"have hbounded_data : {generic_bounded_at_i}",
                "specialize hbounded i",
                "apply hbounded",
                "exact hi",
                "cases hbounded_data",
                "cases hbounded_data_witness",
                "have hj_eq : j = x2",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact hmap",
                "exact hbounded_data_witness_left",
                "have hj_bound : exists gap. gap + S j = n",
                "rewrite hj_eq",
                "exact hbounded_data_witness_right",
                "have hy_eq : y = 1 + j",
                "specialize beta_range_entry_eq x",
                "specialize beta_range_entry_eq x1",
                "specialize beta_range_entry_eq 1",
                "specialize beta_range_entry_eq n",
                "specialize beta_range_entry_eq j",
                "specialize beta_range_entry_eq y",
                "apply beta_range_entry_eq",
                "exact hfactorial_witness_witness_left",
                "exact hj_bound",
                "exact hsource",
                f"have hlifted : {generic_lifted_at_i}",
                "specialize hlift i",
                "specialize hlift j",
                "apply hlift",
                "exact hi",
                "exact hmap",
                "have hone : 1 + j = S j",
                "simp [add_succ_left, zero_add]",
                "rewrite hy_eq",
                "rewrite hy_eq",
                "rewrite hone",
                "rewrite hone",
                "exact hlifted",
                "have hfactorial_eq : F = Q",
                "specialize beta_product_permutation_invariant n",
                "specialize beta_product_permutation_invariant b",
                "specialize beta_product_permutation_invariant c",
                "specialize beta_product_permutation_invariant x",
                "specialize beta_product_permutation_invariant x1",
                "specialize beta_product_permutation_invariant f",
                "specialize beta_product_permutation_invariant g",
                "specialize beta_product_permutation_invariant F",
                "specialize beta_product_permutation_invariant Q",
                "apply beta_product_permutation_invariant",
                "exact hbounded",
                "exact hinjective",
                "exact haligned",
                "exact hfactorial_witness_witness_right",
                "exact hproduct",
                "symm",
                "exact hfactorial_eq",
            ),
            "A bounded injective order and its successor lift multiply to n factorial.",
        ),
        spec(
            "scaled_pair_order_terminal_power_mod_predecessor",
            "forall p a n u v b c h A. p = S n -> "
            f"({prime_p}) -> ({prefix}) -> n = h + h -> ({terminal_state}) -> "
            f"({history}) -> ({terminal_power}) -> ({terminal_result})",
            (
                "beta_successor_lift_exists",
                "scaled_pair_order_successor_lift_adjacent_targets",
                "beta_product_exists",
                "beta_adjacent_target_pairs_product_power",
                "factorial_exists",
                "scaled_pair_order_successor_lift_product_is_factorial",
                "prime_factorial_wilson_congruence",
                "mod_eq_symm",
                "mod_eq_trans",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro heven",
                "intro hstate",
                "intro hhistory",
                "intro hpower",
                "cases hstate",
                "cases hstate_right",
                f"have hlift_exists : exists f g. ({lift_n})",
                "specialize beta_successor_lift_exists b",
                "specialize beta_successor_lift_exists c",
                "specialize beta_successor_lift_exists n",
                "exact beta_successor_lift_exists",
                "cases hlift_exists",
                "cases hlift_exists_witness",
                f"have hpairs : {target_pairs_x}",
                "specialize scaled_pair_order_successor_lift_adjacent_targets p",
                "specialize scaled_pair_order_successor_lift_adjacent_targets a",
                "specialize scaled_pair_order_successor_lift_adjacent_targets n",
                "specialize scaled_pair_order_successor_lift_adjacent_targets u",
                "specialize scaled_pair_order_successor_lift_adjacent_targets v",
                "specialize scaled_pair_order_successor_lift_adjacent_targets b",
                "specialize scaled_pair_order_successor_lift_adjacent_targets c",
                "specialize scaled_pair_order_successor_lift_adjacent_targets x",
                "specialize scaled_pair_order_successor_lift_adjacent_targets x1",
                "specialize scaled_pair_order_successor_lift_adjacent_targets h",
                "apply scaled_pair_order_successor_lift_adjacent_targets",
                "exact heven",
                "exact hprefix",
                "exact hstate_right_left",
                "exact hhistory",
                "exact hlift_exists_witness_witness",
                f"have hproduct_exists : {terminal_product_exists_x}",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists n",
                "exact beta_product_exists",
                "cases hproduct_exists",
                f"have hproduct_even : {terminal_product_even_x2}",
                "rewrite <- heven",
                "rewrite <- heven",
                "rewrite <- heven",
                "exact hproduct_exists_witness",
                f"have hproduct_power : {product_mod_power_x2}",
                "specialize beta_adjacent_target_pairs_product_power p",
                "specialize beta_adjacent_target_pairs_product_power a",
                "specialize beta_adjacent_target_pairs_product_power x",
                "specialize beta_adjacent_target_pairs_product_power x1",
                "specialize beta_adjacent_target_pairs_product_power h",
                "specialize beta_adjacent_target_pairs_product_power x2",
                "specialize beta_adjacent_target_pairs_product_power A",
                "apply beta_adjacent_target_pairs_product_power",
                "exact hpairs",
                "exact hproduct_even",
                "exact hpower",
                f"have hfactorial_exists : exists F. ({terminal_factorial})",
                "specialize factorial_exists n",
                "exact factorial_exists",
                "cases hfactorial_exists",
                f"have hbounded_n : {generic_bounded}",
                "rewrite heven",
                "exact hstate_right_left",
                f"have hinjective_n : {generic_injective}",
                "rewrite heven",
                "rewrite heven",
                "exact hstate_right_right",
                "have hQF : x2 = x3",
                "specialize scaled_pair_order_successor_lift_product_is_factorial b",
                "specialize scaled_pair_order_successor_lift_product_is_factorial c",
                "specialize scaled_pair_order_successor_lift_product_is_factorial x",
                "specialize scaled_pair_order_successor_lift_product_is_factorial x1",
                "specialize scaled_pair_order_successor_lift_product_is_factorial n",
                "specialize scaled_pair_order_successor_lift_product_is_factorial x2",
                "specialize scaled_pair_order_successor_lift_product_is_factorial x3",
                "apply scaled_pair_order_successor_lift_product_is_factorial",
                "exact hbounded_n",
                "exact hinjective_n",
                "exact hlift_exists_witness_witness",
                "exact hproduct_exists_witness",
                "exact hfactorial_exists_witness",
                f"have hpower_product : {power_mod_product_x2}",
                "specialize mod_eq_symm p",
                "specialize mod_eq_symm x2",
                "specialize mod_eq_symm A",
                "apply mod_eq_symm",
                "exact hproduct_power",
                f"have hpower_factorial : {power_mod_factorial_x3}",
                "rewrite <- hQF",
                "exact hpower_product",
                f"have hfactorial_mod : {factorial_mod_predecessor_x3}",
                "specialize prime_factorial_wilson_congruence p",
                "specialize prime_factorial_wilson_congruence n",
                "specialize prime_factorial_wilson_congruence x3",
                "apply prime_factorial_wilson_congruence",
                "exact hpn",
                "exact hp",
                "exact hfactorial_exists_witness",
                "specialize mod_eq_trans p",
                "specialize mod_eq_trans A",
                "specialize mod_eq_trans x3",
                "specialize mod_eq_trans n",
                "apply mod_eq_trans",
                "exact hpower_factorial",
                "exact hfactorial_mod",
            ),
            "A completed terminal scaled pairing sends a^h to the predecessor p-1 modulo p.",
        ),
        spec(
            "scaled_inverse_nonresidue_half_power_mod_predecessor",
            "forall p a n u v h A. p = S n -> "
            f"({prime_p}) -> ~({nonresidue}) -> ({prefix}) -> n = h + h -> "
            f"({terminal_power}) -> ({terminal_result})",
            (
                "scaled_inverse_pair_order_terminal_package",
                "scaled_pair_order_terminal_power_mod_predecessor",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnonresidue",
                "intro hprefix",
                "intro heven",
                "intro hpower",
                f"have hterminal : {terminal_package}",
                "specialize scaled_inverse_pair_order_terminal_package p",
                "specialize scaled_inverse_pair_order_terminal_package a",
                "specialize scaled_inverse_pair_order_terminal_package n",
                "specialize scaled_inverse_pair_order_terminal_package u",
                "specialize scaled_inverse_pair_order_terminal_package v",
                "specialize scaled_inverse_pair_order_terminal_package h",
                "apply scaled_inverse_pair_order_terminal_package",
                "exact hpn",
                "exact hp",
                "exact hnonresidue",
                "exact hprefix",
                "exact heven",
                "cases hterminal",
                "cases hterminal_witness",
                "cases hterminal_witness_witness",
                "specialize scaled_pair_order_terminal_power_mod_predecessor p",
                "specialize scaled_pair_order_terminal_power_mod_predecessor a",
                "specialize scaled_pair_order_terminal_power_mod_predecessor n",
                "specialize scaled_pair_order_terminal_power_mod_predecessor u",
                "specialize scaled_pair_order_terminal_power_mod_predecessor v",
                "specialize scaled_pair_order_terminal_power_mod_predecessor x",
                "specialize scaled_pair_order_terminal_power_mod_predecessor x1",
                "specialize scaled_pair_order_terminal_power_mod_predecessor h",
                "specialize scaled_pair_order_terminal_power_mod_predecessor A",
                "apply scaled_pair_order_terminal_power_mod_predecessor",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact heven",
                "exact hterminal_witness_witness_left",
                "exact hterminal_witness_witness_right",
                "exact hpower",
            ),
            "A full nonresidue scaled-inverse prefix satisfies Euler's minus-one branch.",
        ),
        spec(
            "quadratic_nonresidue_half_power_mod_predecessor",
            "forall p a n h A. p = S n -> "
            f"({prime_p}) -> ~(a = 0) -> ({target_bound}) -> "
            f"~({nonresidue}) -> n = h + h -> ({terminal_power}) -> "
            f"({terminal_result})",
            (
                "prime_scaled_inverse_prefix_exists",
                "scaled_inverse_nonresidue_half_power_mod_predecessor",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro h",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro ha0",
                "intro hap",
                "intro hnonresidue",
                "intro heven",
                "intro hpower",
                f"have hprefix_exists : {full_prefix_exists}",
                "specialize prime_scaled_inverse_prefix_exists p",
                "specialize prime_scaled_inverse_prefix_exists a",
                "specialize prime_scaled_inverse_prefix_exists n",
                "apply prime_scaled_inverse_prefix_exists",
                "exact hpn",
                "exact hp",
                "exact ha0",
                "exact hap",
                "cases hprefix_exists",
                "cases hprefix_exists_witness",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor p",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor a",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor n",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor x",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor x1",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor h",
                "specialize scaled_inverse_nonresidue_half_power_mod_predecessor A",
                "apply scaled_inverse_nonresidue_half_power_mod_predecessor",
                "exact hpn",
                "exact hp",
                "exact hnonresidue",
                "exact hprefix_exists_witness_witness",
                "exact heven",
                "exact hpower",
            ),
            "For a reduced nonzero nonresidue, a^((p-1)/2) is p-1 modulo p.",
        ),
    )


__all__ = ["make_euler_nonresidue_endpoint_candidate_theorems"]
