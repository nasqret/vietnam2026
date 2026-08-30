"""Isolated terminal Wilson bridge from PairOrder to a canonical product.

The terminal PairOrder prefix contains the zero-based nonendpoint inverse
indices ``1,...,l``.  Its successor lift therefore contains the actual
nonendpoint residues ``2,...,l+1``.  A predecessor recode of the PairOrder
values is a beta-coded permutation map into ``0,...,l-1``; this map aligns a
canonical range starting at two with the lifted factor prefix.  The existing
finite-product reindex theorem then identifies their exact products.

All relations below expand before parsing.  This module is an unregistered
authoring candidate and introduces no kernel or parser symbol.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import (
    _beta_at_term as _fold_beta_at_term,
    _product_relation_term,
    beta_at,
    product_relation,
)
from .finite_permutation_theorems import bounded_prefix, injective_prefix
from .finite_product_reindex_support import aligned_prefix
from .gauss_magnitude_permutation_candidate import (
    _magnitude_range_term,
    _predecessor_recode_term,
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .wilson_inverse_prefix_candidate import inverse_prefix, prime
from .wilson_pair_order_candidate import _beta_at_term, _lt_term
from .wilson_pair_order_induction_candidate import _pair_order_state_term
from .wilson_pair_order_paired_iteration_candidate import paired_inverse_witness
from .wilson_pair_product_candidate import _mod_eq_term, adjacent_unit_pairs
from .wilson_successor_lift_candidate import (
    _successor_lift_prefix_term,
    successor_lift_prefix,
)


def _range_two_prefix_term(
    code: str,
    scale: str,
    length_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand the trusted module-owned range ``2,...,2+length-1``."""

    index = f"wtp_range_index_{tag}"
    gap = f"wtp_range_gap_{tag}"
    local = avoid + (index, gap)
    bound = f"exists {gap}. {gap} + S {index} = {length_term}"
    decoded = _fold_beta_at_term(
        code,
        scale,
        index,
        f"2 + {index}",
        tag=f"{tag}_decoded",
        avoid=local,
    )
    return f"forall {index}. ({bound}) -> ({decoded})"


def _conjunction(*terms: str) -> str:
    """Associate a nonempty list of expanded formulas to the right."""

    if not terms:
        raise ValueError("a conjunction requires at least one formula")
    result = terms[-1]
    for term in reversed(terms[:-1]):
        result = f"(({term}) /\\ ({result}))"
    return result


def make_wilson_terminal_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build terminal range extraction, alignment, and product packaging."""

    state_variables = ("u", "v", "b", "c", "l", "n", "q", "x")
    terminal_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        "n",
        tag="wtp_terminal_state",
        avoid=state_variables,
    )
    terminal_range = magnitude_range_prefix(
        "b", "c", "l", "l", tag="wtp_terminal_range"
    )
    terminal_entry_x = _beta_at_term(
        "b",
        "c",
        "q",
        "x",
        tag="wtp_terminal_entry_x",
        avoid=state_variables,
    )
    terminal_value_bound_x = _lt_term(
        "x",
        "S (S l)",
        tag="wtp_terminal_value_bound_x",
        avoid=state_variables,
    )
    terminal_bounded_entry = (
        f"exists x. (({terminal_entry_x}) /\\ ({terminal_value_bound_x}))"
    )

    magnitude_range = magnitude_range_prefix(
        "b", "c", "l", "l", tag="wtp_alignment_range"
    )
    predecessor_recode = predecessor_recode_prefix(
        "b", "c", "r", "s", "l", tag="wtp_alignment_recode"
    )
    successor_lift = successor_lift_prefix(
        "b", "c", "f", "g", "l", tag="wtp_alignment_lift"
    )
    canonical_range = _range_two_prefix_term(
        "z",
        "d",
        "l",
        tag="wtp_alignment_range_two",
        avoid=("b", "c", "r", "s", "z", "d", "f", "g", "l"),
    )
    alignment = aligned_prefix(
        "r", "s", "z", "d", "f", "g", "l", tag="wtp_alignment"
    )
    predecessor_bounded = bounded_prefix(
        "r", "s", "l", tag="wtp_predecessor_bounded"
    )
    predecessor_injective = injective_prefix(
        "r", "s", "l", tag="wtp_predecessor_injective"
    )
    source_injective = injective_prefix(
        "b", "c", "l", tag="wtp_source_injective"
    )
    canonical_product = product_relation(
        "z", "d", "l", "P", tag="wtp_canonical_product"
    )
    lifted_product = product_relation(
        "f", "g", "l", "Q", tag="wtp_lifted_product"
    )

    alignment_variables = (
        "b",
        "c",
        "r",
        "s",
        "z",
        "d",
        "f",
        "g",
        "l",
        "i",
        "j",
        "x",
        "x1",
    )
    reflected_order_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "S j",
        tag="wtp_reflected_order_entry",
        avoid=alignment_variables,
    )
    lifted_target_entry = _beta_at_term(
        "f",
        "g",
        "i",
        "S (S j)",
        tag="wtp_lifted_target_entry",
        avoid=alignment_variables,
    )

    cap_variables = (
        "p",
        "n",
        "u",
        "v",
        "r",
        "m",
        "b",
        "c",
        "f",
        "g",
        "Q",
        "z",
        "d",
        "P",
        "s",
        "q",
    )
    cap_prime = prime("p", tag="wtp_cap_prime")
    cap_inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wtp_cap_inverse"
    )
    cap_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "n",
        tag="wtp_cap_state",
        avoid=cap_variables,
    )
    cap_exact_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "S (S (m + m))",
        tag="wtp_cap_exact_state",
        avoid=cap_variables,
    )
    cap_history = paired_inverse_witness(
        "u", "v", "b", "c", "m", tag="wtp_cap_history"
    )
    cap_lift = _successor_lift_prefix_term(
        "b",
        "c",
        "f",
        "g",
        "m + m",
        tag="wtp_cap_lift",
        avoid=cap_variables,
    )
    cap_adjacent = adjacent_unit_pairs(
        "p", "f", "g", "m", tag="wtp_cap_adjacent"
    )
    cap_lifted_product = _product_relation_term(
        "f",
        "g",
        "m + m",
        "Q",
        tag="wtp_cap_lifted_product",
        avoid=cap_variables,
    )
    cap_mod_one = _mod_eq_term(
        "p", "Q", "1", tag="wtp_cap_mod_one", avoid=cap_variables
    )
    cap_range = _range_two_prefix_term(
        "z",
        "d",
        "m + m",
        tag="wtp_cap_range_two",
        avoid=cap_variables,
    )
    cap_canonical_product = _product_relation_term(
        "z",
        "d",
        "m + m",
        "P",
        tag="wtp_cap_canonical_product",
        avoid=cap_variables,
    )
    cap_coverage_value_bound = _lt_term(
        "s",
        "S (S (m + m))",
        tag="wtp_cap_coverage_value_bound",
        avoid=cap_variables,
    )
    cap_coverage_index_bound = _lt_term(
        "q",
        "m + m",
        tag="wtp_cap_coverage_index_bound",
        avoid=cap_variables,
    )
    cap_coverage_entry = _beta_at_term(
        "b",
        "c",
        "q",
        "s",
        tag="wtp_cap_coverage_entry",
        avoid=cap_variables,
    )
    cap_coverage = (
        f"forall s. ({cap_coverage_value_bound}) -> "
        "(~(s = 0) /\\ ~((S s) = S (S (m + m)))) -> "
        f"exists q. (({cap_coverage_index_bound}) /\\ ({cap_coverage_entry}))"
    )
    cap_state_x = _pair_order_state_term(
        "u",
        "v",
        "x",
        "x1",
        "m + m",
        "n",
        tag="wtp_cap_state_x",
        avoid=cap_variables + ("x", "x1"),
    )
    cap_exact_state_x = _pair_order_state_term(
        "u",
        "v",
        "x",
        "x1",
        "m + m",
        "S (S (m + m))",
        tag="wtp_cap_exact_state_x",
        avoid=cap_variables + ("x", "x1"),
    )
    cap_history_x = paired_inverse_witness(
        "u", "v", "x", "x1", "m", tag="wtp_cap_history_x"
    )
    cap_coverage_entry_x = _beta_at_term(
        "x",
        "x1",
        "q",
        "s",
        tag="wtp_cap_coverage_entry_x",
        avoid=cap_variables + ("x", "x1"),
    )
    cap_coverage_x = (
        f"forall s. ({cap_coverage_value_bound}) -> "
        "(~(s = 0) /\\ ~((S s) = S (S (m + m)))) -> "
        f"exists q. (({cap_coverage_index_bound}) /\\ ({cap_coverage_entry_x}))"
    )
    cap_lift_x = _successor_lift_prefix_term(
        "x",
        "x1",
        "f",
        "g",
        "m + m",
        tag="wtp_cap_lift_x",
        avoid=cap_variables + ("x", "x1"),
    )
    cap_factor_result_x = (
        "exists f g Q. "
        + _conjunction(
            cap_lift_x,
            cap_adjacent,
            cap_lifted_product,
            cap_mod_one,
        )
    )
    cap_canonical_product_x5_x6 = _product_relation_term(
        "x5",
        "x6",
        "m + m",
        "P",
        tag="wtp_cap_canonical_product_x5_x6",
        avoid=cap_variables + ("x", "x1", "x2", "x3", "x4", "x5", "x6"),
    )
    cap_result = "exists b c f g Q z d P. " + _conjunction(
        cap_state,
        cap_history,
        cap_coverage,
        cap_lift,
        cap_adjacent,
        cap_lifted_product,
        cap_mod_one,
        cap_range,
        cap_canonical_product,
        "P = Q",
    )

    return (
        spec(
            "pair_order_terminal_state_magnitude_range",
            "forall u v b c l n. n = S (S l) -> "
            f"({terminal_state}) -> ({terminal_range})",
            ("one_le_of_ne_zero", "le_of_succ_le_succ", "le_eq_or_lt"),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hterminal",
                "intro hstate",
                "cases hstate",
                "cases hstate_right",
                "cases hstate_right_right",
                "rewrite hterminal at hstate_right_left",
                "rewrite hterminal at hstate_right_right_left",
                "intro q",
                "intro hq",
                f"have hentry : {terminal_bounded_entry}",
                "specialize hstate_right_left q",
                "apply hstate_right_left",
                "exact hq",
                "cases hentry",
                "cases hentry_witness",
                "have hnonendpoint : ~(x = 0) /\\ ~((S x) = S (S l))",
                "specialize hstate_right_right_left q",
                "specialize hstate_right_right_left x",
                "apply hstate_right_right_left",
                "exact hq",
                "exact hentry_witness_left",
                "cases hnonendpoint",
                "exists x",
                "split",
                "exact hentry_witness_left",
                "split",
                "specialize one_le_of_ne_zero x",
                "apply one_le_of_ne_zero",
                "exact hnonendpoint_left",
                "have hxle_succ : exists h. h + x = S l",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ (S l)",
                "apply le_of_succ_le_succ",
                "exact hentry_witness_right",
                "have hxsplit : x = S l \\/ exists h. h + S x = S l",
                "specialize le_eq_or_lt x",
                "specialize le_eq_or_lt (S l)",
                "apply le_eq_or_lt",
                "exact hxle_succ",
                "cases hxsplit",
                "exfalso",
                "apply hnonendpoint_right",
                "rewrite hxsplit_left",
                "refl",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hxsplit_right",
            ),
            "A terminal PairOrder state decodes exactly positive values bounded by its length.",
        ),
        spec(
            "pair_order_predecessor_range_two_successor_lift_aligned",
            "forall b c r s z d f g l. "
            f"({magnitude_range}) -> ({predecessor_recode}) -> "
            f"({successor_lift}) -> ({canonical_range}) -> ({alignment})",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_reflect",
                "beta_at_unique",
                "beta_range_entry_eq",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro b",
                "intro c",
                "intro r",
                "intro s",
                "intro z",
                "intro d",
                "intro f",
                "intro g",
                "intro l",
                "intro hrange",
                "intro hrecode",
                "intro hlift",
                "intro hcanonical",
                f"have hbounded : {predecessor_bounded}",
                "specialize beta_magnitude_predecessor_recode_bounded b",
                "specialize beta_magnitude_predecessor_recode_bounded c",
                "specialize beta_magnitude_predecessor_recode_bounded r",
                "specialize beta_magnitude_predecessor_recode_bounded s",
                "specialize beta_magnitude_predecessor_recode_bounded l",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                "intro i",
                "intro j",
                "intro x",
                "intro hi",
                "intro hmap",
                "intro hsource",
                "have hjdata : exists y. "
                f"(({beta_at('r', 's', 'i', 'y', tag='wtp_alignment_bounded_entry')}) /\\ "
                f"({_lt_term('y', 'l', tag='wtp_alignment_bounded_value', avoid=alignment_variables + ('y',))}))",
                "specialize hbounded i",
                "apply hbounded",
                "exact hi",
                "cases hjdata",
                "cases hjdata_witness",
                "have hjy : j = x1",
                "specialize beta_at_unique r",
                "specialize beta_at_unique s",
                "specialize beta_at_unique i",
                "specialize beta_at_unique j",
                "specialize beta_at_unique x1",
                "apply beta_at_unique",
                "exact hmap",
                "exact hjdata_witness_left",
                "have hj : exists h. h + S j = l",
                "rewrite hjy",
                "exact hjdata_witness_right",
                f"have horder : {reflected_order_entry}",
                "specialize beta_magnitude_predecessor_recode_reflect b",
                "specialize beta_magnitude_predecessor_recode_reflect c",
                "specialize beta_magnitude_predecessor_recode_reflect r",
                "specialize beta_magnitude_predecessor_recode_reflect s",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect i",
                "specialize beta_magnitude_predecessor_recode_reflect j",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hrange",
                "exact hrecode",
                "exact hi",
                "exact hmap",
                f"have htarget : {lifted_target_entry}",
                "specialize hlift i",
                "specialize hlift (S j)",
                "apply hlift",
                "exact hi",
                "exact horder",
                "have hxraw : x = 2 + j",
                "specialize beta_range_entry_eq z",
                "specialize beta_range_entry_eq d",
                "specialize beta_range_entry_eq 2",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq j",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hcanonical",
                "exact hj",
                "exact hsource",
                "have htwo : 2 + j = S (S j)",
                "simp [add_succ_left, zero_add]",
                "have hxsucc : x = S (S j)",
                "trans 2 + j",
                "exact hxraw",
                "exact htwo",
                "rewrite hxsucc",
                "rewrite hxsucc",
                "exact htarget",
            ),
            "The predecessor map aligns canonical residues 2+j with successor-lifted PairOrder entries.",
        ),
        spec(
            "pair_order_terminal_successor_product_eq_range_two",
            "forall b c r s z d f g l P Q. "
            f"({magnitude_range}) -> ({source_injective}) -> "
            f"({predecessor_recode}) -> ({successor_lift}) -> "
            f"({canonical_range}) -> ({canonical_product}) -> "
            f"({lifted_product}) -> P = Q",
            (
                "beta_magnitude_predecessor_recode_bounded",
                "beta_magnitude_predecessor_recode_injective",
                "pair_order_predecessor_range_two_successor_lift_aligned",
                "beta_product_permutation_invariant",
            ),
            (
                "intro b",
                "intro c",
                "intro r",
                "intro s",
                "intro z",
                "intro d",
                "intro f",
                "intro g",
                "intro l",
                "intro P",
                "intro Q",
                "intro hrange",
                "intro hinjective",
                "intro hrecode",
                "intro hlift",
                "intro hcanonical",
                "intro hcanonical_product",
                "intro hlifted_product",
                f"have hbounded : {predecessor_bounded}",
                "specialize beta_magnitude_predecessor_recode_bounded b",
                "specialize beta_magnitude_predecessor_recode_bounded c",
                "specialize beta_magnitude_predecessor_recode_bounded r",
                "specialize beta_magnitude_predecessor_recode_bounded s",
                "specialize beta_magnitude_predecessor_recode_bounded l",
                "apply beta_magnitude_predecessor_recode_bounded",
                "exact hrange",
                "exact hrecode",
                f"have hmap_injective : {predecessor_injective}",
                "specialize beta_magnitude_predecessor_recode_injective b",
                "specialize beta_magnitude_predecessor_recode_injective c",
                "specialize beta_magnitude_predecessor_recode_injective r",
                "specialize beta_magnitude_predecessor_recode_injective s",
                "specialize beta_magnitude_predecessor_recode_injective l",
                "apply beta_magnitude_predecessor_recode_injective",
                "exact hrange",
                "exact hinjective",
                "exact hrecode",
                f"have haligned : {alignment}",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned b",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned c",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned r",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned s",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned z",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned d",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned f",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned g",
                "specialize pair_order_predecessor_range_two_successor_lift_aligned l",
                "apply pair_order_predecessor_range_two_successor_lift_aligned",
                "exact hrange",
                "exact hrecode",
                "exact hlift",
                "exact hcanonical",
                "specialize beta_product_permutation_invariant l",
                "specialize beta_product_permutation_invariant r",
                "specialize beta_product_permutation_invariant s",
                "specialize beta_product_permutation_invariant z",
                "specialize beta_product_permutation_invariant d",
                "specialize beta_product_permutation_invariant f",
                "specialize beta_product_permutation_invariant g",
                "specialize beta_product_permutation_invariant P",
                "specialize beta_product_permutation_invariant Q",
                "apply beta_product_permutation_invariant",
                "exact hbounded",
                "exact hmap_injective",
                "exact haligned",
                "exact hcanonical_product",
                "exact hlifted_product",
            ),
            "The lifted terminal product equals the product of the canonical nonendpoint range.",
        ),
        spec(
            "prime_wilson_terminal_product_package_exists",
            "forall p n u v r m. p = S n -> "
            f"({cap_prime}) -> ({cap_inverse}) -> n = S r -> "
            f"n = S (S (m + m)) -> ({cap_result})",
            (
                "prime_pair_order_paired_terminal_state_exists",
                "pair_order_state_terminal_coverage",
                "paired_pair_order_product_one_exists",
                "pair_order_terminal_state_magnitude_range",
                "beta_magnitude_predecessor_recode_exists",
                "beta_range_exists",
                "beta_product_exists",
                "pair_order_terminal_successor_product_eq_range_two",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro r",
                "intro m",
                "intro hpn",
                "intro hp",
                "intro hinverse",
                "intro hnr",
                "intro hterminal",
                "have hpair_state : exists b c. "
                f"(({cap_state}) /\\ ({cap_history}))",
                "specialize prime_pair_order_paired_terminal_state_exists p",
                "specialize prime_pair_order_paired_terminal_state_exists n",
                "specialize prime_pair_order_paired_terminal_state_exists u",
                "specialize prime_pair_order_paired_terminal_state_exists v",
                "specialize prime_pair_order_paired_terminal_state_exists r",
                "specialize prime_pair_order_paired_terminal_state_exists m",
                "apply prime_pair_order_paired_terminal_state_exists",
                "exact hpn",
                "exact hp",
                "exact hinverse",
                "exact hnr",
                "exact hterminal",
                "cases hpair_state",
                "cases hpair_state_witness",
                "cases hpair_state_witness_witness",
                f"have hstate : {cap_state_x}",
                "exact hpair_state_witness_witness_left",
                f"have hhistory : {cap_history_x}",
                "exact hpair_state_witness_witness_right",
                f"have hstate_parts : {cap_state_x}",
                "exact hstate",
                "cases hstate_parts",
                "cases hstate_parts_right",
                "cases hstate_parts_right_right",
                f"have hexact_state : {cap_exact_state_x}",
                "rewrite <- hterminal",
                "rewrite <- hterminal",
                "exact hstate",
                f"have hcoverage : {cap_coverage_x}",
                "specialize pair_order_state_terminal_coverage u",
                "specialize pair_order_state_terminal_coverage v",
                "specialize pair_order_state_terminal_coverage x",
                "specialize pair_order_state_terminal_coverage x1",
                "specialize pair_order_state_terminal_coverage (m + m)",
                "apply pair_order_state_terminal_coverage",
                "exact hexact_state",
                "have hrange : "
                + _magnitude_range_term(
                    "x",
                    "x1",
                    "m + m",
                    "m + m",
                    tag="wtp_cap_range",
                    variables=cap_variables + ("x", "x1"),
                ),
                "specialize pair_order_terminal_state_magnitude_range u",
                "specialize pair_order_terminal_state_magnitude_range v",
                "specialize pair_order_terminal_state_magnitude_range x",
                "specialize pair_order_terminal_state_magnitude_range x1",
                "specialize pair_order_terminal_state_magnitude_range (m + m)",
                "specialize pair_order_terminal_state_magnitude_range n",
                "apply pair_order_terminal_state_magnitude_range",
                "exact hterminal",
                "exact hstate",
                f"have hfactor_product : {cap_factor_result_x}",
                "specialize paired_pair_order_product_one_exists p",
                "specialize paired_pair_order_product_one_exists n",
                "specialize paired_pair_order_product_one_exists u",
                "specialize paired_pair_order_product_one_exists v",
                "specialize paired_pair_order_product_one_exists x",
                "specialize paired_pair_order_product_one_exists x1",
                "specialize paired_pair_order_product_one_exists m",
                "apply paired_pair_order_product_one_exists",
                "exact hinverse",
                "exact hstate_parts_right_left",
                "exact hhistory",
                "cases hfactor_product",
                "cases hfactor_product_witness",
                "cases hfactor_product_witness_witness",
                "cases hfactor_product_witness_witness_witness",
                "cases hfactor_product_witness_witness_witness_right",
                "cases hfactor_product_witness_witness_witness_right_right",
                f"have hcanonical_range_exists : exists z d. ({cap_range})",
                "specialize beta_range_exists 2",
                "specialize beta_range_exists (m + m)",
                "exact beta_range_exists",
                "cases hcanonical_range_exists",
                "cases hcanonical_range_exists_witness",
                "have hcanonical_product_exists : exists P. "
                f"({cap_canonical_product_x5_x6})",
                "specialize beta_product_exists x5",
                "specialize beta_product_exists x6",
                "specialize beta_product_exists (m + m)",
                "exact beta_product_exists",
                "cases hcanonical_product_exists",
                "have hrecode_exists : exists rb rc. "
                + _predecessor_recode_term(
                    "x",
                    "x1",
                    "rb",
                    "rc",
                    "m + m",
                    tag="wtp_cap_recode",
                    variables=cap_variables + ("x", "x1", "rb", "rc"),
                ),
                "specialize beta_magnitude_predecessor_recode_exists x",
                "specialize beta_magnitude_predecessor_recode_exists x1",
                "specialize beta_magnitude_predecessor_recode_exists (m + m)",
                "specialize beta_magnitude_predecessor_recode_exists (m + m)",
                "apply beta_magnitude_predecessor_recode_exists",
                "exact hrange",
                "cases hrecode_exists",
                "cases hrecode_exists_witness",
                "have hequal : x7 = x4",
                "specialize pair_order_terminal_successor_product_eq_range_two x",
                "specialize pair_order_terminal_successor_product_eq_range_two x1",
                "specialize pair_order_terminal_successor_product_eq_range_two x8",
                "specialize pair_order_terminal_successor_product_eq_range_two x9",
                "specialize pair_order_terminal_successor_product_eq_range_two x5",
                "specialize pair_order_terminal_successor_product_eq_range_two x6",
                "specialize pair_order_terminal_successor_product_eq_range_two x2",
                "specialize pair_order_terminal_successor_product_eq_range_two x3",
                "specialize pair_order_terminal_successor_product_eq_range_two (m + m)",
                "specialize pair_order_terminal_successor_product_eq_range_two x7",
                "specialize pair_order_terminal_successor_product_eq_range_two x4",
                "apply pair_order_terminal_successor_product_eq_range_two",
                "exact hrange",
                "exact hstate_parts_right_right_right",
                "exact hrecode_exists_witness_witness",
                "exact hfactor_product_witness_witness_witness_left",
                "exact hcanonical_range_exists_witness_witness",
                "exact hcanonical_product_exists_witness",
                "exact hfactor_product_witness_witness_witness_right_right_left",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "exists x6",
                "exists x7",
                "split",
                "exact hstate",
                "split",
                "exact hhistory",
                "split",
                "exact hcoverage",
                "split",
                "exact hfactor_product_witness_witness_witness_left",
                "split",
                "exact hfactor_product_witness_witness_witness_right_left",
                "split",
                "exact hfactor_product_witness_witness_witness_right_right_left",
                "split",
                "exact hfactor_product_witness_witness_witness_right_right_right",
                "split",
                "exact hcanonical_range_exists_witness_witness",
                "split",
                "exact hcanonical_product_exists_witness",
                "exact hequal",
            ),
            "Package terminal PairOrder history, coverage, lifted product, and equality with residues 2,...,p-2.",
        ),
    )


__all__ = ["make_wilson_terminal_product_candidate_theorems"]
