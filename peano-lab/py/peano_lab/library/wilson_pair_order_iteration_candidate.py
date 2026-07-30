"""Isolated full pair-count iteration for the native Wilson campaign.

This authoring module turns the previously checked one-orbit append into a
genuinely iterable invariant.  It remains deliberately outside the public
theorem registry: dependencies are replayed only as ordinary hypotheses by
the candidate-body validator, while recursive closure, mutation replay and
admission remain WMI-only gates.

The induction is constructive and runs on the number of pairs already
stored.  A second parameter records the pairs still available.  This avoids
subtraction in the object language and keeps the exact conservation law

    (k+k) + S(S(m+m)) = n.

No list, sequence, subtraction, or new kernel symbol is introduced.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_omission_candidate import _bounded_into_term
from .wilson_inverse_prefix_candidate import inverse_prefix, prime
from .wilson_pair_order_candidate import _injective_prefix_term
from .wilson_pair_order_induction_candidate import (
    _pair_order_state_term,
    _pair_step_body_term,
    pair_order_state,
)


def make_wilson_pair_order_iteration_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the state-transition wrapper and pair-count induction."""

    old_state = pair_order_state(
        "u", "v", "b", "c", "l", "n", tag="wpoit_old_state"
    )
    new_state = _pair_order_state_term(
        "u",
        "v",
        "z",
        "d",
        "S (S l)",
        "n",
        tag="wpoit_new_state",
        avoid=("p", "n", "u", "v", "b", "c", "z", "d", "l", "r"),
    )
    step_prime = prime("p", tag="wpoit_prime")
    step_inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wpoit_inverse"
    )
    step_body = _pair_step_body_term(
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "l",
        "n",
        "i",
        "j",
        tag="wpoit_step_body",
        avoid=("p", "n", "u", "v", "b", "c", "z", "d", "l", "r", "i", "j"),
    )
    # This is the exact result exposed by
    # prime_pair_order_choose_append_state.  Keeping it expanded here makes
    # the wrapper's projection audit explicit.
    bounded_after = _bounded_into_term(
        "z",
        "d",
        "S (S l)",
        "n",
        tag="wpoit_bounded_after",
        avoid=("p", "n", "u", "v", "b", "c", "z", "d", "l", "r", "i", "j"),
    )
    injective_after = _injective_prefix_term(
        "z",
        "d",
        "S (S l)",
        tag="wpoit_injective_after",
        avoid=("p", "n", "u", "v", "b", "c", "z", "d", "l", "r", "i", "j"),
    )
    raw_step = (
        f"exists z d i j. (({step_body}) /\\ "
        f"(({bounded_after}) /\\ ({injective_after})))"
    )
    witness_variables = (
        "p",
        "n",
        "u",
        "v",
        "b",
        "c",
        "l",
        "r",
        "x",
        "x1",
        "x2",
        "x3",
    )
    step_body_x = _pair_step_body_term(
        "u",
        "v",
        "b",
        "c",
        "x",
        "x1",
        "l",
        "n",
        "x2",
        "x3",
        tag="wpoit_step_body_x",
        avoid=witness_variables,
    )
    bounded_after_x = _bounded_into_term(
        "x",
        "x1",
        "S (S l)",
        "n",
        tag="wpoit_bounded_after_x",
        avoid=witness_variables,
    )
    injective_after_x = _injective_prefix_term(
        "x",
        "x1",
        "S (S l)",
        tag="wpoit_injective_after_x",
        avoid=witness_variables,
    )
    raw_step_x = (
        f"(({step_body_x}) /\\ "
        f"(({bounded_after_x}) /\\ ({injective_after_x})))"
    )

    iter_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "n",
        tag="wpoit_iter_state",
        avoid=("p", "n", "u", "v", "b", "c", "r", "m", "k"),
    )
    iter_result = f"exists b c. ({iter_state})"
    iter_next_state = _pair_order_state_term(
        "u",
        "v",
        "z",
        "d",
        "S (S (m + m))",
        "n",
        tag="wpoit_iter_next_state",
        avoid=("p", "n", "u", "v", "z", "d", "r", "m", "k"),
    )
    family_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "t + t",
        "n",
        tag="wpoit_family_state",
        avoid=("p", "n", "u", "v", "b", "c", "r", "t", "q"),
    )
    iteration_family = (
        "forall t q. (q + q) + S (S (t + t)) = n -> "
        f"exists b c. ({family_state})"
    )

    return (
        spec(
            "prime_pair_order_state_step",
            "forall p n u v b c l r. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({old_state}) -> exists z d. ({new_state})",
            ("prime_pair_order_choose_append_state",),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hroom",
                "intro hstate",
                "cases hstate",
                "cases hstate_right",
                "cases hstate_right_right",
                f"have hstep : {raw_step}",
                "specialize prime_pair_order_choose_append_state p",
                "specialize prime_pair_order_choose_append_state n",
                "specialize prime_pair_order_choose_append_state u",
                "specialize prime_pair_order_choose_append_state v",
                "specialize prime_pair_order_choose_append_state b",
                "specialize prime_pair_order_choose_append_state c",
                "specialize prime_pair_order_choose_append_state l",
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
                f"have hcombined : {raw_step_x}",
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
                "exists x",
                "exists x1",
                "split",
                "exact hcombined_left_right_right_right_right_right_right_right_right_right_right_left",
                "split",
                "exact hcombined_right_left",
                "split",
                "exact hcombined_left_right_right_right_right_right_right_right_right_right_right_right",
                "exact hcombined_right_right",
            ),
            "Forget append witnesses while preserving the complete bounded PairOrder state.",
        ),
        spec(
            "pair_order_iteration_previous_balance",
            "forall m k. (k + k) + S (S (S m + S m)) = "
            "(S k + S k) + S (S (m + m))",
            ("add_succ_left", "add_assoc", "add_comm"),
            (
                "intro m",
                "intro k",
                "simp [add_succ_left, add_assoc, add_comm]",
            ),
            "Rebalance one stored pair into the predecessor induction hypothesis.",
        ),
        spec(
            "pair_order_iteration_step_room",
            "forall m k. (k + k) + S (S (S m + S m)) = "
            "S (k + k) + S (S (S (m + m)))",
            ("add_succ_left", "add_assoc", "add_comm"),
            (
                "intro m",
                "intro k",
                "simp [add_succ_left, add_assoc, add_comm]",
            ),
            "Expose the exact one-orbit room equation in the successor case.",
        ),
        spec(
            "prime_pair_order_iteration",
            "forall p n u v r. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "forall m k. (k + k) + S (S (m + m)) = n -> "
            f"({iter_result})",
            (
                "pair_order_state_zero",
                "pair_order_iteration_previous_balance",
                "pair_order_iteration_step_room",
                "prime_pair_order_state_step",
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
                "have hzero : 0 + 0 = 0",
                "simp",
                "specialize pair_order_state_zero u",
                "specialize pair_order_state_zero v",
                "specialize pair_order_state_zero n",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "rewrite hzero",
                "exact pair_order_state_zero",
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
                f"have hprevious : {iter_result}",
                "specialize IH (S k)",
                "apply IH",
                "exact hprevious_balance",
                "cases hprevious",
                "cases hprevious_witness",
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
                f"have hnext : exists z d. ({iter_next_state})",
                "specialize prime_pair_order_state_step p",
                "specialize prime_pair_order_state_step n",
                "specialize prime_pair_order_state_step u",
                "specialize prime_pair_order_state_step v",
                "specialize prime_pair_order_state_step x",
                "specialize prime_pair_order_state_step x1",
                "specialize prime_pair_order_state_step (m + m)",
                "specialize prime_pair_order_state_step r",
                "apply prime_pair_order_state_step",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hroom",
                "exact hprevious_witness_witness",
                "cases hnext",
                "cases hnext_witness",
                "have hlength : S (S (m + m)) = S m + S m",
                "specialize pair_order_double_succ_length (m + m)",
                "specialize pair_order_double_succ_length m",
                "apply pair_order_double_succ_length",
                "refl",
                "exists x2",
                "exists x3",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "rewrite <- hlength",
                "exact hnext_witness_witness",
            ),
            "Iterate fresh inverse-orbit pairs under an explicit stored/remaining conservation law.",
        ),
        spec(
            "prime_pair_order_terminal_state_exists",
            "forall p n u v r m. p = S n -> "
            f"({step_prime}) -> ({step_inverse}) -> n = S r -> "
            "n = S (S (m + m)) -> "
            f"({iter_result})",
            ("prime_pair_order_iteration", "zero_add"),
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
                "specialize prime_pair_order_iteration p",
                "specialize prime_pair_order_iteration n",
                "specialize prime_pair_order_iteration u",
                "specialize prime_pair_order_iteration v",
                "specialize prime_pair_order_iteration r",
                "apply prime_pair_order_iteration",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "specialize hiteration m",
                "specialize hiteration 0",
                "apply hiteration",
                "exact hbalance",
            ),
            "Specialize the constructive iteration to a complete n-2 nonendpoint prefix.",
        ),
    )


__all__ = ["make_wilson_pair_order_iteration_candidate_theorems"]
