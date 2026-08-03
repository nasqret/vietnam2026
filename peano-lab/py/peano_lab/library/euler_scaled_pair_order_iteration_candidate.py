"""Isolated even-length PairOrder iteration for Euler's criterion.

The scaled inverse prefix stores actual residues: a zero-based source ``i``
has a decoded mate ``S j``.  The state and history in this module retain that
shift explicitly.  In particular, the adjacent history records both order
entries ``i,j`` and the raw scaled edge ``At(u,v,i,S j)``.  A later
successor-lift may therefore turn the order into factors ``S i,S j`` without
losing the congruence-to-``a`` witness.

All relations expand to unchanged first-order Peano arithmetic.  This factory
is an unregistered dependency-curried authoring candidate.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import _identifier, prime
from .euler_scaled_inverse_prefix_candidate import scaled_inverse_prefix
from .euler_scaled_pair_order_entrance_candidate import (
    _conjunction,
    _scaled_orbit_closed_term,
)
from .finite_omission_candidate import _bounded_into_term
from .finite_permutation_theorems import surjective_prefix
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import (
    _append_two_trace_term,
    _beta_at_term,
    _injective_prefix_term,
    _lt_term,
    _omits_value_term,
)


def _scaled_pair_order_state_term(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand shifted closure, boundedness, and decoded injectivity."""

    closed = _scaled_orbit_closed_term(
        scaled_code,
        scaled_scale,
        order_code,
        order_scale,
        length,
        tag=f"{tag}_closed",
        avoid=avoid,
    )
    bounded = _bounded_into_term(
        order_code,
        order_scale,
        length,
        bound,
        tag=f"{tag}_bounded",
        avoid=avoid,
    )
    injective = _injective_prefix_term(
        order_code,
        order_scale,
        length,
        tag=f"{tag}_injective",
        avoid=avoid,
    )
    return _conjunction(closed, bounded, injective)


def scaled_pair_order_state(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Public hygienic expansion of the iterable Euler PairOrder state."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (scaled_code, "scaled code"),
            (scaled_scale, "scaled scale"),
            (order_code, "order code"),
            (order_scale, "order scale"),
            (length, "prefix length"),
            (bound, "codomain bound"),
        )
    )
    return _scaled_pair_order_state_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _adjacent_scaled_orbit_history_term(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    pair_count: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Record adjacent zero-based sources and their actual-mate edge."""

    safe_tag = _identifier(tag, "history binder tag")
    pair = f"espi_pair_{safe_tag}"
    left = f"espi_left_{safe_tag}"
    right = f"espi_right_{safe_tag}"
    generated = (pair, left, right)
    if len(set(generated)) != len(generated) or set(generated) & set(avoid):
        raise ValueError("generated Euler pair-history binder captures an argument")
    local = avoid + generated
    pair_bound = _lt_term(
        pair,
        pair_count,
        tag=f"{tag}_pair_bound",
        avoid=local,
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
    scaled_edge = _beta_at_term(
        scaled_code,
        scaled_scale,
        left,
        f"S {right}",
        tag=f"{tag}_scaled_edge",
        avoid=local,
    )
    return (
        f"forall {pair}. ({pair_bound}) -> exists {left} {right}. "
        f"({_conjunction(left_entry, right_entry, scaled_edge)})"
    )


def adjacent_scaled_orbit_history(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    pair_count: str,
    *,
    tag: str,
) -> str:
    """Public hygienic expansion of the adjacent scaled-orbit history."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (scaled_code, "scaled code"),
            (scaled_scale, "scaled scale"),
            (order_code, "order code"),
            (order_scale, "order scale"),
            (pair_count, "pair count"),
        )
    )
    return _adjacent_scaled_orbit_history_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _append_payload_term(
    scaled_code: str,
    scaled_scale: str,
    old_code: str,
    old_scale: str,
    new_code: str,
    new_scale: str,
    length: str,
    bound: str,
    source: str,
    mate: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Mirror the exact result of the isolated entrance append theorem."""

    trace = _append_two_trace_term(
        old_code,
        old_scale,
        new_code,
        new_scale,
        length,
        source,
        mate,
        tag=f"{tag}_trace",
        avoid=avoid,
    )
    source_bound = _lt_term(
        source, bound, tag=f"{tag}_source_bound", avoid=avoid
    )
    mate_bound = _lt_term(
        mate, bound, tag=f"{tag}_mate_bound", avoid=avoid
    )
    source_omit = _omits_value_term(
        old_code,
        old_scale,
        length,
        source,
        tag=f"{tag}_source_omit",
        avoid=avoid,
    )
    mate_omit = _omits_value_term(
        old_code,
        old_scale,
        length,
        mate,
        tag=f"{tag}_mate_omit",
        avoid=avoid,
    )
    forward = _beta_at_term(
        scaled_code,
        scaled_scale,
        source,
        f"S {mate}",
        tag=f"{tag}_forward",
        avoid=avoid,
    )
    back = _beta_at_term(
        scaled_code,
        scaled_scale,
        mate,
        f"S {source}",
        tag=f"{tag}_back",
        avoid=avoid,
    )
    closed_after = _scaled_orbit_closed_term(
        scaled_code,
        scaled_scale,
        new_code,
        new_scale,
        f"S (S ({length}))",
        tag=f"{tag}_closed_after",
        avoid=avoid,
    )
    injective_after = _injective_prefix_term(
        new_code,
        new_scale,
        f"S (S ({length}))",
        tag=f"{tag}_injective_after",
        avoid=avoid,
    )
    return _conjunction(
        trace,
        source_bound,
        mate_bound,
        source_omit,
        mate_omit,
        f"~({source} = {mate})",
        forward,
        back,
        closed_after,
        injective_after,
    )


def make_euler_scaled_pair_order_iteration_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build empty state/history, append closure, iteration, and coverage."""

    base_variables = (
        "p",
        "a",
        "n",
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "m",
        "k",
        "i",
        "j",
    )
    zero_closed = _scaled_orbit_closed_term(
        "u", "v", "b", "c", "0", tag="zero_closed", avoid=base_variables
    )
    zero_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        "n",
        tag="zero_state",
        avoid=base_variables,
    )
    zero_history = _adjacent_scaled_orbit_history_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        tag="zero_history",
        avoid=base_variables,
    )

    append_old_history = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "m", tag="append_old_history"
    )
    append_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "m + m",
        "i",
        "j",
        tag="append_trace",
        avoid=base_variables,
    )
    append_forward = _beta_at_term(
        "u",
        "v",
        "i",
        "S j",
        tag="append_forward",
        avoid=base_variables,
    )
    append_new_history = _adjacent_scaled_orbit_history_term(
        "u",
        "v",
        "z",
        "d",
        "S m",
        tag="append_new_history",
        avoid=base_variables,
    )
    history_occurrence_variables = base_variables + ("t", "oi", "oj")
    old_history_at_t = "exists oi oj. " + _conjunction(
        _beta_at_term(
            "b",
            "c",
            "t + t",
            "oi",
            tag="old_history_left",
            avoid=history_occurrence_variables,
        ),
        _beta_at_term(
            "b",
            "c",
            "S (t + t)",
            "oj",
            tag="old_history_right",
            avoid=history_occurrence_variables,
        ),
        _beta_at_term(
            "u",
            "v",
            "oi",
            "S oj",
            tag="old_history_edge",
            avoid=history_occurrence_variables,
        ),
    )

    step_prime = prime("p", tag="iteration_prime")
    step_nonresidue = quadratic_residue(
        "p", "a", tag="iteration_nonresidue"
    )
    step_prefix = scaled_inverse_prefix(
        "p", "a", "n", "u", "v", "n", tag="iteration_prefix"
    )
    step_short = _lt_term(
        "m + m", "n", tag="iteration_short", avoid=base_variables
    )
    step_old_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "n",
        tag="step_old_state",
        avoid=base_variables,
    )
    step_old_history = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "m", tag="step_old_history"
    )
    step_payload = _append_payload_term(
        "u",
        "v",
        "b",
        "c",
        "z",
        "d",
        "m + m",
        "n",
        "i",
        "j",
        tag="step_payload",
        avoid=base_variables,
    )
    raw_step = f"exists z d i j. ({step_payload})"

    witness_variables = base_variables + ("x", "x1", "x2", "x3")
    step_payload_x = _append_payload_term(
        "u",
        "v",
        "b",
        "c",
        "x",
        "x1",
        "m + m",
        "n",
        "x2",
        "x3",
        tag="step_payload_x",
        avoid=witness_variables,
    )
    bounded_after_x = _bounded_into_term(
        "x",
        "x1",
        "S (S (m + m))",
        "n",
        tag="bounded_after_x",
        avoid=witness_variables,
    )
    state_after_x = _scaled_pair_order_state_term(
        "u",
        "v",
        "x",
        "x1",
        "S (S (m + m))",
        "n",
        tag="state_after_x",
        avoid=witness_variables,
    )
    history_after_x = _adjacent_scaled_orbit_history_term(
        "u",
        "v",
        "x",
        "x1",
        "S m",
        tag="history_after_x",
        avoid=witness_variables,
    )
    step_result = f"exists z d. ({_conjunction(_scaled_pair_order_state_term('u', 'v', 'z', 'd', 'S (S (m + m))', 'n', tag='step_result_state', avoid=base_variables), append_new_history)})"

    iteration_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "m + m",
        "n",
        tag="iteration_state",
        avoid=base_variables,
    )
    iteration_history = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "m", tag="iteration_history"
    )
    iteration_result = (
        f"exists b c. ({_conjunction(iteration_state, iteration_history)})"
    )
    iteration_all = (
        "forall m k. (m + m) + (k + k) = n -> "
        f"({iteration_result})"
    )
    successor_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "x2",
        "x3",
        "S m + S m",
        "n",
        tag="successor_state",
        avoid=witness_variables,
    )
    terminal_state = _scaled_pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "h + h",
        "n",
        tag="terminal_state",
        avoid=base_variables + ("h",),
    )
    terminal_history = adjacent_scaled_orbit_history(
        "u", "v", "b", "c", "h", tag="terminal_history"
    )
    terminal_state_x = _scaled_pair_order_state_term(
        "u",
        "v",
        "x",
        "x1",
        "h + h",
        "n",
        tag="terminal_state_x",
        avoid=witness_variables + ("h",),
    )
    terminal_history_x = _adjacent_scaled_orbit_history_term(
        "u",
        "v",
        "x",
        "x1",
        "h",
        tag="terminal_history_x",
        avoid=witness_variables + ("h",),
    )
    terminal_result = (
        f"exists b c. ({_conjunction(terminal_state, terminal_history)})"
    )
    terminal_surjective = surjective_prefix(
        "b", "c", "n", tag="terminal_surjective"
    )
    coverage_result = "exists b c. " + _conjunction(
        terminal_state,
        terminal_history,
        terminal_surjective,
    )
    terminal_bounded_raw = _bounded_into_term(
        "x",
        "x1",
        "h + h",
        "n",
        tag="terminal_bounded_raw",
        avoid=witness_variables + ("h",),
    )
    terminal_bounded_n = _bounded_into_term(
        "x",
        "x1",
        "n",
        "n",
        tag="terminal_bounded_n",
        avoid=witness_variables + ("h",),
    )
    terminal_injective_raw = _injective_prefix_term(
        "x",
        "x1",
        "h + h",
        tag="terminal_injective_raw",
        avoid=witness_variables + ("h",),
    )
    terminal_injective_n = _injective_prefix_term(
        "x",
        "x1",
        "n",
        tag="terminal_injective_n",
        avoid=witness_variables + ("h",),
    )
    terminal_surjective_x = surjective_prefix(
        "x", "x1", "n", tag="terminal_surjective_x"
    )

    return (
        spec(
            "scaled_orbit_closed_prefix_zero",
            f"forall u v b c. ({zero_closed})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro q",
                "intro s",
                "intro t",
                "intro hq",
                "intro hsource",
                "intro hscaled",
                "exfalso",
                "cases hq",
                "have hsq : S q = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S q)",
                "apply add_eq_zero_right",
                "exact hq_witness",
                "specialize succ_ne_zero q",
                "apply succ_ne_zero",
                "exact hsq",
            ),
            "Shifted orbit closure is vacuous on an empty order prefix.",
        ),
        spec(
            "adjacent_scaled_orbit_history_zero",
            f"forall u v b c. ({zero_history})",
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
            "The explicit adjacent scaled-orbit history is empty at zero pairs.",
        ),
        spec(
            "adjacent_scaled_orbit_history_append",
            "forall u v b c z d m i j. "
            f"({append_old_history}) -> ({append_trace}) -> ({append_forward}) -> "
            f"({append_new_history})",
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
                "intro hold",
                "intro htrace",
                "intro hforward",
                "cases htrace",
                "cases htrace_right",
                "intro t",
                "intro ht",
                "have hsplit : t = m \\/ exists h. h + S t = m",
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
                "exact hforward",
                f"have hold_at : {old_history_at_t}",
                "specialize hold t",
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
            "Append one adjacent pair while retaining its raw At(i,S j) scaled edge.",
        ),
        spec(
            "scaled_pair_order_state_zero",
            f"forall u v n. exists b c. ({zero_state})",
            (
                "scaled_orbit_closed_prefix_zero",
                "bounded_into_zero",
                "injective_prefix_zero",
            ),
            (
                "intro u",
                "intro v",
                "intro n",
                "exists 0",
                "exists 0",
                "split",
                "specialize scaled_orbit_closed_prefix_zero u",
                "specialize scaled_orbit_closed_prefix_zero v",
                "specialize scaled_orbit_closed_prefix_zero 0",
                "specialize scaled_orbit_closed_prefix_zero 0",
                "exact scaled_orbit_closed_prefix_zero",
                "split",
                "specialize bounded_into_zero 0",
                "specialize bounded_into_zero 0",
                "specialize bounded_into_zero n",
                "exact bounded_into_zero",
                "specialize injective_prefix_zero 0",
                "specialize injective_prefix_zero 0",
                "exact injective_prefix_zero",
            ),
            "Zero codes witness the empty shifted, bounded, injective state.",
        ),
        spec(
            "scaled_inverse_pair_order_paired_state_step",
            "forall p a n u v b c m. p = S n -> "
            f"({step_prime}) -> ~({step_nonresidue}) -> ({step_prefix}) -> "
            f"({step_short}) -> ({step_old_state}) -> ({step_old_history}) -> "
            f"({step_result})",
            (
                "scaled_inverse_pair_order_choose_append",
                "beta_prefix_append_two_bounded_into",
                "adjacent_scaled_orbit_history_append",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro m",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "intro hshort",
                "intro hstate",
                "intro hhistory",
                "cases hstate",
                "cases hstate_right",
                f"have hraw : {raw_step}",
                "specialize scaled_inverse_pair_order_choose_append p",
                "specialize scaled_inverse_pair_order_choose_append a",
                "specialize scaled_inverse_pair_order_choose_append n",
                "specialize scaled_inverse_pair_order_choose_append u",
                "specialize scaled_inverse_pair_order_choose_append v",
                "specialize scaled_inverse_pair_order_choose_append b",
                "specialize scaled_inverse_pair_order_choose_append c",
                "specialize scaled_inverse_pair_order_choose_append (m + m)",
                "apply scaled_inverse_pair_order_choose_append",
                "exact hpn",
                "exact hp",
                "exact hnotqres",
                "exact hprefix",
                "exact hshort",
                "exact hstate_left",
                "exact hstate_right_right",
                "cases hraw",
                "cases hraw_witness",
                "cases hraw_witness_witness",
                "cases hraw_witness_witness_witness",
                f"have hparts : {step_payload_x}",
                "exact hraw_witness_witness_witness_witness",
                "cases hparts",
                "cases hparts_right",
                "cases hparts_right_right",
                "cases hparts_right_right_right",
                "cases hparts_right_right_right_right",
                "cases hparts_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right_right_right",
                f"have hbounded_after : {bounded_after_x}",
                "specialize beta_prefix_append_two_bounded_into b",
                "specialize beta_prefix_append_two_bounded_into c",
                "specialize beta_prefix_append_two_bounded_into x",
                "specialize beta_prefix_append_two_bounded_into x1",
                "specialize beta_prefix_append_two_bounded_into (m + m)",
                "specialize beta_prefix_append_two_bounded_into n",
                "specialize beta_prefix_append_two_bounded_into x2",
                "specialize beta_prefix_append_two_bounded_into x3",
                "apply beta_prefix_append_two_bounded_into",
                "exact hparts_left",
                "exact hstate_right_left",
                "exact hparts_right_left",
                "exact hparts_right_right_left",
                f"have hhistory_after : {history_after_x}",
                "specialize adjacent_scaled_orbit_history_append u",
                "specialize adjacent_scaled_orbit_history_append v",
                "specialize adjacent_scaled_orbit_history_append b",
                "specialize adjacent_scaled_orbit_history_append c",
                "specialize adjacent_scaled_orbit_history_append x",
                "specialize adjacent_scaled_orbit_history_append x1",
                "specialize adjacent_scaled_orbit_history_append m",
                "specialize adjacent_scaled_orbit_history_append x2",
                "specialize adjacent_scaled_orbit_history_append x3",
                "apply adjacent_scaled_orbit_history_append",
                "exact hhistory",
                "exact hparts_left",
                "exact hparts_right_right_right_right_right_right_left",
                f"have hstate_after : {state_after_x}",
                "split",
                "exact hparts_right_right_right_right_right_right_right_right_left",
                "split",
                "exact hbounded_after",
                "exact hparts_right_right_right_right_right_right_right_right_right",
                "exists x",
                "exists x1",
                "split",
                "exact hstate_after",
                "exact hhistory_after",
            ),
            "Append one fixed-point-free scaled orbit and preserve iterable state plus history.",
        ),
        spec(
            "euler_pair_iteration_previous_balance",
            "forall m k. (S m + S m) + (k + k) = "
            "(m + m) + (S k + S k)",
            ("add_succ_left", "add_assoc", "add_comm"),
            (
                "intro m",
                "intro k",
                "simp [add_succ_left, add_assoc, add_comm]",
            ),
            "Move the newest pair from stored count to remaining count.",
        ),
        spec(
            "euler_pair_iteration_step_short",
            "forall m k. S (k + k) + S (m + m) = "
            "(S m + S m) + (k + k)",
            ("add_succ_left", "add_comm"),
            (
                "intro m",
                "intro k",
                "simp [add_succ_left, add_comm]",
            ),
            "Expose a strict-prefix witness whenever at least one pair remains.",
        ),
        spec(
            "scaled_inverse_pair_order_paired_iteration",
            "forall p a n u v. p = S n -> "
            f"({step_prime}) -> ~({step_nonresidue}) -> ({step_prefix}) -> "
            "forall m k. (m + m) + (k + k) = n -> "
            f"({iteration_result})",
            (
                "scaled_pair_order_state_zero",
                "adjacent_scaled_orbit_history_zero",
                "euler_pair_iteration_previous_balance",
                "euler_pair_iteration_step_short",
                "scaled_inverse_pair_order_paired_state_step",
                "pair_order_double_succ_length",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "induction m",
                "intro k",
                "intro hbalance",
                f"have hzero_state : exists b c. ({zero_state})",
                "specialize scaled_pair_order_state_zero u",
                "specialize scaled_pair_order_state_zero v",
                "specialize scaled_pair_order_state_zero n",
                "exact scaled_pair_order_state_zero",
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
                "exact hzero_state_witness_witness",
                "specialize adjacent_scaled_orbit_history_zero u",
                "specialize adjacent_scaled_orbit_history_zero v",
                "specialize adjacent_scaled_orbit_history_zero x",
                "specialize adjacent_scaled_orbit_history_zero x1",
                "exact adjacent_scaled_orbit_history_zero",
                "intro k",
                "intro hbalance",
                "have hprevious_normalize : (S m + S m) + (k + k) = (m + m) + (S k + S k)",
                "specialize euler_pair_iteration_previous_balance m",
                "specialize euler_pair_iteration_previous_balance k",
                "exact euler_pair_iteration_previous_balance",
                "have hprevious_balance : (m + m) + (S k + S k) = n",
                "trans (S m + S m) + (k + k)",
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
                "have hshort_normalize : S (k + k) + S (m + m) = (S m + S m) + (k + k)",
                "specialize euler_pair_iteration_step_short m",
                "specialize euler_pair_iteration_step_short k",
                "exact euler_pair_iteration_step_short",
                "have hshort_eq : S (k + k) + S (m + m) = n",
                "trans (S m + S m) + (k + k)",
                "exact hshort_normalize",
                "exact hbalance",
                "have hshort : exists q. q + S (m + m) = n",
                "exists S (k + k)",
                "exact hshort_eq",
                f"have hnext : {step_result}",
                "specialize scaled_inverse_pair_order_paired_state_step p",
                "specialize scaled_inverse_pair_order_paired_state_step a",
                "specialize scaled_inverse_pair_order_paired_state_step n",
                "specialize scaled_inverse_pair_order_paired_state_step u",
                "specialize scaled_inverse_pair_order_paired_state_step v",
                "specialize scaled_inverse_pair_order_paired_state_step x",
                "specialize scaled_inverse_pair_order_paired_state_step x1",
                "specialize scaled_inverse_pair_order_paired_state_step m",
                "apply scaled_inverse_pair_order_paired_state_step",
                "exact hpn",
                "exact hp",
                "exact hnotqres",
                "exact hprefix",
                "exact hshort",
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
                "exact hnext_witness_witness_left",
                "exists x2",
                "exists x3",
                "split",
                "exact hsuccessor_state",
                "exact hnext_witness_witness_right",
            ),
            "Iterate exactly one adjacent scaled orbit for every stored pair.",
        ),
        spec(
            "scaled_inverse_pair_order_terminal_package",
            "forall p a n u v h. p = S n -> "
            f"({step_prime}) -> ~({step_nonresidue}) -> ({step_prefix}) -> "
            f"n = h + h -> ({terminal_result})",
            ("scaled_inverse_pair_order_paired_iteration",),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro h",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "intro heven",
                "have hbalance : (h + h) + (0 + 0) = n",
                "rewrite heven",
                "simp",
                f"have hall : {iteration_all}",
                "specialize scaled_inverse_pair_order_paired_iteration p",
                "specialize scaled_inverse_pair_order_paired_iteration a",
                "specialize scaled_inverse_pair_order_paired_iteration n",
                "specialize scaled_inverse_pair_order_paired_iteration u",
                "specialize scaled_inverse_pair_order_paired_iteration v",
                "apply scaled_inverse_pair_order_paired_iteration",
                "exact hpn",
                "exact hp",
                "exact hnotqres",
                "exact hprefix",
                "specialize hall h",
                "specialize hall 0",
                "apply hall",
                "exact hbalance",
            ),
            "At n=h+h, package a complete adjacent scaled-orbit order of length n.",
        ),
        spec(
            "scaled_inverse_pair_order_terminal_coverage",
            "forall p a n u v h. p = S n -> "
            f"({step_prime}) -> ~({step_nonresidue}) -> ({step_prefix}) -> "
            f"n = h + h -> ({coverage_result})",
            (
                "scaled_inverse_pair_order_terminal_package",
                "finite_bounded_injective_surjective",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro h",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "intro heven",
                f"have hterminal : {terminal_result}",
                "specialize scaled_inverse_pair_order_terminal_package p",
                "specialize scaled_inverse_pair_order_terminal_package a",
                "specialize scaled_inverse_pair_order_terminal_package n",
                "specialize scaled_inverse_pair_order_terminal_package u",
                "specialize scaled_inverse_pair_order_terminal_package v",
                "specialize scaled_inverse_pair_order_terminal_package h",
                "apply scaled_inverse_pair_order_terminal_package",
                "exact hpn",
                "exact hp",
                "exact hnotqres",
                "exact hprefix",
                "exact heven",
                "cases hterminal",
                "cases hterminal_witness",
                "cases hterminal_witness_witness",
                f"have hstate_keep : {terminal_state_x}",
                "exact hterminal_witness_witness_left",
                f"have hhistory_keep : {terminal_history_x}",
                "exact hterminal_witness_witness_right",
                "cases hterminal_witness_witness_left",
                "cases hterminal_witness_witness_left_right",
                f"have hbounded_raw : {terminal_bounded_raw}",
                "exact hterminal_witness_witness_left_right_left",
                "rewrite <- heven at hbounded_raw",
                f"have hbounded_n : {terminal_bounded_n}",
                "exact hbounded_raw",
                f"have hinjective_raw : {terminal_injective_raw}",
                "exact hterminal_witness_witness_left_right_right",
                "rewrite <- heven at hinjective_raw",
                "rewrite <- heven at hinjective_raw",
                f"have hinjective_n : {terminal_injective_n}",
                "exact hinjective_raw",
                f"have hsurjective : {terminal_surjective_x}",
                "specialize finite_bounded_injective_surjective n",
                "specialize finite_bounded_injective_surjective x",
                "specialize finite_bounded_injective_surjective x1",
                "apply finite_bounded_injective_surjective",
                "exact hbounded_n",
                "exact hinjective_n",
                "exists x",
                "exists x1",
                "split",
                "exact hstate_keep",
                "split",
                "exact hhistory_keep",
                "exact hsurjective",
            ),
            "A terminal bounded injection covers every zero-based source below n.",
        ),
    )


__all__ = [
    "adjacent_scaled_orbit_history",
    "make_euler_scaled_pair_order_iteration_candidate_theorems",
    "scaled_pair_order_state",
]
