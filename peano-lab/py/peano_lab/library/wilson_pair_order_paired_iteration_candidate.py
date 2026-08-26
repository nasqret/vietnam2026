"""Pair-history invariant for the native Wilson construction.

The bounded PairOrder state proves terminal coverage, but coverage and orbit
closure do not remember that consecutive positions were appended as inverse
pairs.  This isolated module adds the missing existential witness invariant.
It is an authoring candidate only; no theorem is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_omission_candidate import _bounded_into_term
from .wilson_inverse_prefix_candidate import inverse_prefix, prime
from .wilson_pair_order_candidate import (
    _append_two_trace_term,
    _beta_at_term,
    _injective_prefix_term,
    _lt_term,
)
from .wilson_pair_order_induction_candidate import (
    _pair_order_state_term,
    _pair_step_body_term,
)


def _paired_inverse_witness_term(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    pair_count: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    pair = f"wpop_pair_{tag}"
    left = f"wpop_left_{tag}"
    right = f"wpop_right_{tag}"
    local = avoid + (pair, left, right)
    pair_bound = _lt_term(
        pair, pair_count, tag=f"{tag}_pair_bound", avoid=local
    )
    left_entry = _beta_at_term(
        order_code,
        order_scale,
        f"{pair} + {pair}",
        left,
        tag=f"{tag}_left_entry",
        avoid=local,
    )
    right_entry = _beta_at_term(
        order_code,
        order_scale,
        f"S ({pair} + {pair})",
        right,
        tag=f"{tag}_right_entry",
        avoid=local,
    )
    inverse_entry = _beta_at_term(
        inverse_code,
        inverse_scale,
        left,
        right,
        tag=f"{tag}_inverse_entry",
        avoid=local,
    )
    return (
        f"forall {pair}. ({pair_bound}) -> exists {left} {right}. "
        f"(({left_entry}) /\ (({right_entry}) /\ ({inverse_entry})))"
    )


def paired_inverse_witness(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    pair_count: str,
    *,
    tag: str,
) -> str:
    """Expand witnesses for every adjacent inverse pair below pair_count."""

    variables = (
        inverse_code,
        inverse_scale,
        order_code,
        order_scale,
        pair_count,
    )
    return _paired_inverse_witness_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def make_wilson_pair_order_paired_iteration_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build pair-position arithmetic, the empty case, and append closure."""

    old_pairs = paired_inverse_witness(
        "u", "v", "b", "c", "m", tag="wpop_old_pairs"
    )
    new_pairs = _paired_inverse_witness_term(
        "u",
        "v",
        "z",
        "d",
        "S m",
        tag="wpop_new_pairs",
        avoid=("u", "v", "b", "c", "z", "d", "m", "i", "j"),
    )
    append_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "m + m",
        "i",
        "j",
        tag="wpop_append_trace",
        avoid=("u", "v", "b", "c", "z", "d", "m", "i", "j"),
    )
    inverse_edge = _beta_at_term(
        "u",
        "v",
        "i",
        "j",
        tag="wpop_inverse_edge",
        avoid=("u", "v", "b", "c", "z", "d", "m", "i", "j"),
    )
    zero_pairs = _paired_inverse_witness_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        tag="wpop_zero_pairs",
        avoid=("u", "v", "b", "c"),
    )
    occurrence_variables = (
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "m",
        "i",
        "j",
        "t",
        "oi",
        "oj",
    )
    old_left_at_t = _beta_at_term(
        "b",
        "c",
        "t + t",
        "oi",
        tag="wpop_old_left_at_t",
        avoid=occurrence_variables,
    )
    old_right_at_t = _beta_at_term(
        "b",
        "c",
        "S (t + t)",
        "oj",
        tag="wpop_old_right_at_t",
        avoid=occurrence_variables,
    )
    old_edge_at_t = _beta_at_term(
        "u",
        "v",
        "oi",
        "oj",
        tag="wpop_old_edge_at_t",
        avoid=occurrence_variables,
    )
    old_occurrence_at_t = (
        f"exists oi oj. (({old_left_at_t}) /\ "
        f"(({old_right_at_t}) /\ ({old_edge_at_t})))"
    )

    step_variables = (
        "p",
        "n",
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "m",
        "r",
        "i",
        "j",
    )
    step_prime = prime("p", tag="wpopi_prime")
    step_inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wpopi_inverse"
    )
    paired_old_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "(m + m)",
        "n",
        tag="wpopi_old_state",
        avoid=step_variables,
    )
    paired_next_state = _pair_order_state_term(
        "u",
        "v",
        "z",
        "d",
        "S (S (m + m))",
        "n",
        tag="wpopi_next_state",
        avoid=step_variables,
    )
    paired_step_body = _pair_step_body_term(
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "(m + m)",
        "n",
        "i",
        "j",
        tag="wpopi_step_body",
        avoid=step_variables,
    )
    paired_bounded_after = _bounded_into_term(
        "z",
        "d",
        "S (S (m + m))",
        "n",
        tag="wpopi_bounded_after",
        avoid=step_variables,
    )
    paired_injective_after = _injective_prefix_term(
        "z",
        "d",
        "S (S (m + m))",
        tag="wpopi_injective_after",
        avoid=step_variables,
    )
    paired_raw_step = (
        f"exists z d i j. (({paired_step_body}) /\ "
        f"(({paired_bounded_after}) /\ ({paired_injective_after})))"
    )
    step_witness_variables = (
        "p",
        "n",
        "u",
        "v",
        "b",
        "c",
        "m",
        "r",
        "x",
        "x1",
        "x2",
        "x3",
    )
    paired_step_body_x = _pair_step_body_term(
        "u",
        "v",
        "b",
        "c",
        "x",
        "x1",
        "(m + m)",
        "n",
        "x2",
        "x3",
        tag="wpopi_step_body_x",
        avoid=step_witness_variables,
    )
    paired_bounded_after_x = _bounded_into_term(
        "x",
        "x1",
        "S (S (m + m))",
        "n",
        tag="wpopi_bounded_after_x",
        avoid=step_witness_variables,
    )
    paired_injective_after_x = _injective_prefix_term(
        "x",
        "x1",
        "S (S (m + m))",
        tag="wpopi_injective_after_x",
        avoid=step_witness_variables,
    )
    paired_raw_step_x = (
        f"(({paired_step_body_x}) /\ "
        f"(({paired_bounded_after_x}) /\ ({paired_injective_after_x})))"
    )
    paired_new_history_x = _paired_inverse_witness_term(
        "u",
        "v",
        "x",
        "x1",
        "S m",
        tag="wpopi_new_history_x",
        avoid=step_witness_variables,
    )
    paired_step_result = (
        "exists z d. "
        f"(({paired_next_state}) /\ ({new_pairs}))"
    )

    iteration_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "n",
        tag="wpopi_iteration_state",
        avoid=("p", "n", "u", "v", "b", "c", "r", "m", "k"),
    )
    iteration_history = paired_inverse_witness(
        "u", "v", "b", "c", "m", tag="wpopi_iteration_history"
    )
    iteration_result = (
        f"exists b c. (({iteration_state}) /\ ({iteration_history}))"
    )
    successor_state = _pair_order_state_term(
        "u",
        "v",
        "x2",
        "x3",
        "S m + S m",
        "n",
        tag="wpopi_successor_state",
        avoid=("p", "n", "u", "v", "x2", "x3", "r", "m", "k"),
    )
    zero_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        "n",
        tag="wpopi_zero_state",
        avoid=("p", "n", "u", "v", "b", "c", "r", "k"),
    )
    family_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "t + t",
        "n",
        tag="wpopi_family_state",
        avoid=("p", "n", "u", "v", "b", "c", "r", "t", "q"),
    )
    family_history = paired_inverse_witness(
        "u", "v", "b", "c", "t", tag="wpopi_family_history"
    )
    iteration_family = (
        "forall t q. (q + q) + S (S (t + t)) = n -> "
        f"exists b c. (({family_state}) /\ ({family_history}))"
    )

    return (
        spec(
            "pair_index_left_below_double",
            "forall t m. (exists h. h + S t = m) -> "
            "exists h. h + S (t + t) = m + m",
            (
                "lt_to_le",
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "add_succ_left",
            ),
            (
                "intro t",
                "intro m",
                "intro htm",
                "have htle : exists h. h + t = m",
                "specialize lt_to_le t",
                "specialize lt_to_le m",
                "apply lt_to_le",
                "exact htm",
                "have hfirst : exists h. h + (S t + t) = m + t",
                "specialize add_le_add_right (S t)",
                "specialize add_le_add_right m",
                "specialize add_le_add_right t",
                "apply add_le_add_right",
                "exact htm",
                "have hsingle : S t + t = S (t + t)",
                "specialize add_succ_left t",
                "specialize add_succ_left t",
                "exact add_succ_left",
                "rewrite hsingle at hfirst",
                "have hsecond : exists h. h + (m + t) = m + m",
                "specialize add_le_add_left t",
                "specialize add_le_add_left m",
                "specialize add_le_add_left m",
                "apply add_le_add_left",
                "exact htle",
                "specialize le_trans (S (t + t))",
                "specialize le_trans (m + t)",
                "specialize le_trans (m + m)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
            ),
            "The left position of an earlier pair lies below the doubled prefix.",
        ),
        spec(
            "pair_index_right_below_double",
            "forall t m. (exists h. h + S t = m) -> "
            "exists h. h + S (S (t + t)) = m + m",
            (
                "add_le_add_right",
                "add_le_add_left",
                "le_trans",
                "add_succ_left",
            ),
            (
                "intro t",
                "intro m",
                "intro htm",
                "have hfirst : exists h. h + (S t + S t) = m + S t",
                "specialize add_le_add_right (S t)",
                "specialize add_le_add_right m",
                "specialize add_le_add_right (S t)",
                "apply add_le_add_right",
                "exact htm",
                "have hdouble : S (S (t + t)) = S t + S t",
                "simp [add_succ_left]",
                "rewrite <- hdouble at hfirst",
                "have hsecond : exists h. h + (m + S t) = m + m",
                "specialize add_le_add_left (S t)",
                "specialize add_le_add_left m",
                "specialize add_le_add_left m",
                "apply add_le_add_left",
                "exact htm",
                "specialize le_trans (S (S (t + t)))",
                "specialize le_trans (m + S t)",
                "specialize le_trans (m + m)",
                "apply le_trans",
                "exact hfirst",
                "exact hsecond",
            ),
            "The right position of an earlier pair lies below the doubled prefix.",
        ),
        spec(
            "paired_inverse_witness_zero",
            f"forall u v b c. ({zero_pairs})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro t",
                "intro ht",
                "exfalso",
                "cases ht",
                "have hst : S t = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S t)",
                "apply add_eq_zero_right",
                "exact ht_witness",
                "specialize succ_ne_zero t",
                "apply succ_ne_zero",
                "exact hst",
            ),
            "The adjacent inverse-pair witness invariant is vacuous at zero.",
        ),
        spec(
            "paired_inverse_witness_append",
            "forall u v b c z d m i j. "
            f"({old_pairs}) -> ({append_trace}) -> ({inverse_edge}) -> "
            f"({new_pairs})",
            (
                "finite_lt_succ_eq_or_lt",
                "pair_index_left_below_double",
                "pair_index_right_below_double",
            ),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro m",
                "intro i",
                "intro j",
                "intro hold_pairs",
                "intro htrace",
                "intro hedge",
                "cases htrace",
                "cases htrace_right",
                "intro t",
                "intro ht",
                "have hsplit : t = m \/ exists h. h + S t = m",
                "specialize finite_lt_succ_eq_or_lt m",
                "specialize finite_lt_succ_eq_or_lt t",
                "apply finite_lt_succ_eq_or_lt",
                "exact ht",
                "cases hsplit",
                "have hleft_position : t + t = m + m",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "refl",
                "have hright_position : S (t + t) = S (m + m)",
                "congr",
                "exact hleft_position",
                "exists i",
                "exists j",
                "split",
                "rewrite hleft_position",
                "rewrite hleft_position",
                "exact htrace_left",
                "split",
                "rewrite hright_position",
                "rewrite hright_position",
                "exact htrace_right_left",
                "exact hedge",
                f"have hold : {old_pairs}",
                "exact hold_pairs",
                "specialize hold t",
                f"have hold_at : {old_occurrence_at_t}",
                "apply hold",
                "exact hsplit_right",
                "cases hold_at",
                "cases hold_at_witness",
                "cases hold_at_witness_witness",
                "cases hold_at_witness_witness_right",
                "have hleft_bound : exists h. h + S (t + t) = m + m",
                "specialize pair_index_left_below_double t",
                "specialize pair_index_left_below_double m",
                "apply pair_index_left_below_double",
                "exact hsplit_right",
                "have hright_bound : exists h. h + S (S (t + t)) = m + m",
                "specialize pair_index_right_below_double t",
                "specialize pair_index_right_below_double m",
                "apply pair_index_right_below_double",
                "exact hsplit_right",
                "exists x",
                "exists x1",
                "split",
                "specialize htrace_right_right (t + t)",
                "specialize htrace_right_right x",
                "apply htrace_right_right",
                "exact hleft_bound",
                "exact hold_at_witness_witness_left",
                "split",
                "specialize htrace_right_right (S (t + t))",
                "specialize htrace_right_right x1",
                "apply htrace_right_right",
                "exact hright_bound",
                "exact hold_at_witness_witness_right_left",
                "exact hold_at_witness_witness_right_right",
            ),
            "A two-entry append preserves every old inverse pair and adds the new one.",
        ),
        spec(
            "prime_pair_order_paired_state_step",
            "forall p n u v b c m r. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "(exists h. h + S (S (S (m + m))) = n) -> "
            f"({paired_old_state}) -> ({old_pairs}) -> "
            f"({paired_step_result})",
            (
                "prime_pair_order_choose_append_state",
                "paired_inverse_witness_append",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro m",
                "intro r",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hroom",
                "intro hstate",
                "intro hhistory",
                "cases hstate",
                "cases hstate_right",
                "cases hstate_right_right",
                f"have hstep : {paired_raw_step}",
                "specialize prime_pair_order_choose_append_state p",
                "specialize prime_pair_order_choose_append_state n",
                "specialize prime_pair_order_choose_append_state u",
                "specialize prime_pair_order_choose_append_state v",
                "specialize prime_pair_order_choose_append_state b",
                "specialize prime_pair_order_choose_append_state c",
                "specialize prime_pair_order_choose_append_state (m + m)",
                "specialize prime_pair_order_choose_append_state r",
                "apply prime_pair_order_choose_append_state",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hroom",
                "exact hstate_left",
                "exact hstate_right_left",
                "exact hstate_right_right_left",
                "exact hstate_right_right_right",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                f"have hcombined : {paired_raw_step_x}",
                "exact hstep_witness_witness_witness_witness",
                "cases hcombined",
                "cases hcombined_right",
                "cases hcombined_left",
                "cases hcombined_left_right",
                "cases hcombined_left_right_right",
                "cases hcombined_left_right_right_right",
                "cases hcombined_left_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right_right_right_right_right",
                "cases hcombined_left_right_right_right_right_right_right_right_right_right_right",
                f"have hnew_history : {paired_new_history_x}",
                "specialize paired_inverse_witness_append u",
                "specialize paired_inverse_witness_append v",
                "specialize paired_inverse_witness_append b",
                "specialize paired_inverse_witness_append c",
                "specialize paired_inverse_witness_append x",
                "specialize paired_inverse_witness_append x1",
                "specialize paired_inverse_witness_append m",
                "specialize paired_inverse_witness_append x2",
                "specialize paired_inverse_witness_append x3",
                "apply paired_inverse_witness_append",
                "exact hhistory",
                "exact hcombined_left_left",
                "exact hcombined_left_right_right_right_right_left",
                "exists x",
                "exists x1",
                "split",
                "split",
                "exact hcombined_left_right_right_right_right_right_right_right_right_right_right_left",
                "split",
                "exact hcombined_right_left",
                "split",
                "exact hcombined_left_right_right_right_right_right_right_right_right_right_right_right",
                "exact hcombined_right_right",
                "exact hnew_history",
            ),
            "Preserve the bounded PairOrder state and every adjacent inverse-pair witness through one append.",
        ),
        spec(
            "prime_pair_order_paired_iteration",
            "forall p n u v r. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "forall m k. (k + k) + S (S (m + m)) = n -> "
            f"({iteration_result})",
            (
                "pair_order_state_zero",
                "paired_inverse_witness_zero",
                "pair_order_iteration_previous_balance",
                "pair_order_iteration_step_room",
                "prime_pair_order_paired_state_step",
                "pair_order_double_succ_length",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro r",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "induction m",
                "intro k",
                "intro hbalance",
                f"have hzero_state : exists b c. ({zero_state})",
                "specialize pair_order_state_zero u",
                "specialize pair_order_state_zero v",
                "specialize pair_order_state_zero n",
                "exact pair_order_state_zero",
                "cases hzero_state",
                "cases hzero_state_witness",
                "have hzero : 0 + 0 = 0",
                "simp",
                "exists x",
                "exists x1",
                "split",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "exact hzero_state_witness_witness",
                "specialize paired_inverse_witness_zero u",
                "specialize paired_inverse_witness_zero v",
                "specialize paired_inverse_witness_zero x",
                "specialize paired_inverse_witness_zero x1",
                "exact paired_inverse_witness_zero",
                "intro k",
                "intro hbalance",
                "have hprevious_normalize : (k + k) + S (S (S m + S m)) = (S k + S k) + S (S (m + m))",
                "specialize pair_order_iteration_previous_balance m",
                "specialize pair_order_iteration_previous_balance k",
                "exact pair_order_iteration_previous_balance",
                "have hprevious_balance : (S k + S k) + S (S (m + m)) = n",
                "trans (k + k) + S (S (S m + S m))",
                "symm",
                "exact hprevious_normalize",
                "exact hbalance",
                f"have hprevious : {iteration_result}",
                "specialize IH (S k)",
                "apply IH",
                "exact hprevious_balance",
                "cases hprevious",
                "cases hprevious_witness",
                "cases hprevious_witness_witness",
                "have hroom_normalize : (k + k) + S (S (S m + S m)) = S (k + k) + S (S (S (m + m)))",
                "specialize pair_order_iteration_step_room m",
                "specialize pair_order_iteration_step_room k",
                "exact pair_order_iteration_step_room",
                "have hroom_eq : S (k + k) + S (S (S (m + m))) = n",
                "trans (k + k) + S (S (S m + S m))",
                "symm",
                "exact hroom_normalize",
                "exact hbalance",
                "have hroom : exists h. h + S (S (S (m + m))) = n",
                "exists S (k + k)",
                "exact hroom_eq",
                f"have hnext : {paired_step_result}",
                "specialize prime_pair_order_paired_state_step p",
                "specialize prime_pair_order_paired_state_step n",
                "specialize prime_pair_order_paired_state_step u",
                "specialize prime_pair_order_paired_state_step v",
                "specialize prime_pair_order_paired_state_step x",
                "specialize prime_pair_order_paired_state_step x1",
                "specialize prime_pair_order_paired_state_step m",
                "specialize prime_pair_order_paired_state_step r",
                "apply prime_pair_order_paired_state_step",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hroom",
                "exact hprevious_witness_witness_left",
                "exact hprevious_witness_witness_right",
                "cases hnext",
                "cases hnext_witness",
                "cases hnext_witness_witness",
                "have hlength : S (S (m + m)) = S m + S m",
                "specialize pair_order_double_succ_length (m + m)",
                "specialize pair_order_double_succ_length m",
                "apply pair_order_double_succ_length",
                "refl",
                f"have hsuccessor_state : {successor_state}",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "exact hnext_witness_witness_left",
                "exists x2",
                "exists x3",
                "split",
                "exact hsuccessor_state",
                "exact hnext_witness_witness_right",
            ),
            "Iterate pair appends while retaining both bounded state and adjacent inverse history.",
        ),
        spec(
            "prime_pair_order_paired_terminal_state_exists",
            "forall p n u v r m. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "n = S (S (m + m)) -> "
            f"({iteration_result})",
            ("prime_pair_order_paired_iteration", "zero_add"),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro r",
                "intro m",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hterminal",
                "have hbalance : (0 + 0) + S (S (m + m)) = n",
                "rewrite hterminal",
                "simp [zero_add]",
                f"have hiteration : {iteration_family}",
                "specialize prime_pair_order_paired_iteration p",
                "specialize prime_pair_order_paired_iteration n",
                "specialize prime_pair_order_paired_iteration u",
                "specialize prime_pair_order_paired_iteration v",
                "specialize prime_pair_order_paired_iteration r",
                "apply prime_pair_order_paired_iteration",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "specialize hiteration m",
                "specialize hiteration 0",
                "apply hiteration",
                "exact hbalance",
            ),
            "Specialize the paired iteration to a terminal n-2 prefix with full adjacency history.",
        ),
    )


__all__ = [
    "make_wilson_pair_order_paired_iteration_candidate_theorems",
    "paired_inverse_witness",
]
