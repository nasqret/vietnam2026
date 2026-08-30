"""Isolated induction infrastructure above the submitted PairOrder snapshot.

This module leaves ``wilson_pair_order_candidate.py`` unchanged.  It composes
that module's fresh-orbit append with injectivity preservation, proves the
two-successor length normalization needed by adjacent-pair consumers, and
packages the empty invariant state plus one pair-count successor step.  The
next isolated rung gives the step an explicit iteration contract: if the
current length is ``m+m`` and
``S(k+k) + S(S(S l)) = n``, one pair can be appended and ``k`` pairs remain.

The primitive successor step deliberately retains
``exists h. h + S (S (S l)) = n``.  Removing that premise at the terminal
length requires a separate bounded terminal-coverage bridge: nonendpointness
alone does not imply decoded values are below ``n``.  No candidate is
registered or admitted here.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_omission_candidate import _bounded_into_term
from .finite_permutation_theorems import surjective_prefix
from .gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .wilson_inverse_prefix_candidate import inverse_prefix, prime
from .wilson_pair_order_candidate import (
    _append_two_trace_term,
    _beta_at_term,
    _injective_prefix_term,
    _lt_term,
    _nonendpoint_prefix_term,
    _omits_value_term,
    _orbit_closed_prefix_term,
)


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _pair_order_state_term(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    closed = _orbit_closed_prefix_term(
        inverse_code,
        inverse_scale,
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
    nonendpoint = _nonendpoint_prefix_term(
        order_code,
        order_scale,
        length,
        bound,
        tag=f"{tag}_nonendpoint",
        avoid=avoid,
    )
    injective = _injective_prefix_term(
        order_code,
        order_scale,
        length,
        tag=f"{tag}_injective",
        avoid=avoid,
    )
    return (
        f"(({closed}) /\\ (({bounded}) /\\ "
        f"(({nonendpoint}) /\\ ({injective}))))"
    )


def pair_order_state(
    inverse_code: str,
    inverse_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    bound: str,
    *,
    tag: str,
) -> str:
    """Expand closure, bounded range, nonendpointness, and injectivity."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (inverse_code, "inverse code"),
            (inverse_scale, "inverse scale"),
            (order_code, "order code"),
            (order_scale, "order scale"),
            (length, "prefix length"),
            (bound, "index bound"),
        )
    )
    return _pair_order_state_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _pair_step_body_term(
    inverse_code: str,
    inverse_scale: str,
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
        source,
        bound,
        tag=f"{tag}_source_bound",
        avoid=avoid,
    )
    source_omit = _omits_value_term(
        old_code,
        old_scale,
        length,
        source,
        tag=f"{tag}_source_omit",
        avoid=avoid,
    )
    forward = _beta_at_term(
        inverse_code,
        inverse_scale,
        source,
        mate,
        tag=f"{tag}_forward",
        avoid=avoid,
    )
    mate_bound = _lt_term(
        mate,
        bound,
        tag=f"{tag}_mate_bound",
        avoid=avoid,
    )
    back = _beta_at_term(
        inverse_code,
        inverse_scale,
        mate,
        source,
        tag=f"{tag}_back",
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
    closed_after = _orbit_closed_prefix_term(
        inverse_code,
        inverse_scale,
        new_code,
        new_scale,
        f"S (S {length})",
        tag=f"{tag}_closed_after",
        avoid=avoid,
    )
    nonendpoint_after = _nonendpoint_prefix_term(
        new_code,
        new_scale,
        f"S (S {length})",
        bound,
        tag=f"{tag}_nonendpoint_after",
        avoid=avoid,
    )
    return (
        f"(({trace}) /\\ (({source_bound}) /\\ "
        f"((~({source} = 0) /\\ ~((S {source}) = {bound})) /\\ "
        f"(({source_omit}) /\\ (({forward}) /\\ "
        f"(({mate_bound}) /\\ "
        f"((~({mate} = 0) /\\ ~((S {mate}) = {bound})) /\\ "
        f"(~({source} = {mate}) /\\ (({back}) /\\ "
        f"(({mate_omit}) /\\ "
        f"(({closed_after}) /\\ ({nonendpoint_after}))))))))))))"
    )


def make_wilson_pair_order_induction_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered PairOrder induction entrance ladder."""

    variables = ("p", "n", "u", "v", "b", "c", "l", "r", "m", "k")
    append_variables = ("b", "c", "z", "d", "l", "n", "a", "e")
    append_bounded_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "a",
        "e",
        tag="wpoi_append_bounded_trace",
        avoid=append_variables,
    )
    append_bounded_before = _bounded_into_term(
        "b",
        "c",
        "l",
        "n",
        tag="wpoi_append_bounded_before",
        avoid=append_variables,
    )
    append_first_bound = _lt_term(
        "a",
        "n",
        tag="wpoi_append_first_bound",
        avoid=append_variables,
    )
    append_second_bound = _lt_term(
        "e",
        "n",
        tag="wpoi_append_second_bound",
        avoid=append_variables,
    )
    append_bounded_after = _bounded_into_term(
        "z",
        "d",
        "S (S l)",
        "n",
        tag="wpoi_append_bounded_after",
        avoid=append_variables,
    )
    append_old_entry = _beta_at_term(
        "b",
        "c",
        "q",
        "w",
        tag="wpoi_append_bounded_old_entry",
        avoid=append_variables + ("q", "w"),
    )
    append_new_entry = _beta_at_term(
        "z",
        "d",
        "q",
        "w",
        tag="wpoi_append_bounded_new_entry",
        avoid=append_variables + ("q", "w"),
    )
    append_old_value_bound = _lt_term(
        "w",
        "n",
        tag="wpoi_append_bounded_old_value_bound",
        avoid=append_variables + ("q", "w"),
    )
    append_old_result = (
        f"exists w. (({append_old_entry}) /\\ ({append_old_value_bound}))"
    )
    step_prime = prime("p", tag="wpoi_step_prime")
    step_inverse = inverse_prefix(
        "p", "n", "u", "v", "n", tag="wpoi_step_inverse"
    )
    step_closed_before = _orbit_closed_prefix_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        tag="wpoi_step_closed_before",
        avoid=variables,
    )
    step_bounded_before = _bounded_into_term(
        "b",
        "c",
        "l",
        "n",
        tag="wpoi_step_bounded_before",
        avoid=variables,
    )
    step_nonendpoint_before = _nonendpoint_prefix_term(
        "b",
        "c",
        "l",
        "n",
        tag="wpoi_step_nonendpoint_before",
        avoid=variables,
    )
    step_injective_before = _injective_prefix_term(
        "b",
        "c",
        "l",
        tag="wpoi_step_injective_before",
        avoid=variables,
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
        tag="wpoi_step_body",
        avoid=variables + ("z", "d", "i", "j"),
    )
    step_injective_after = _injective_prefix_term(
        "z",
        "d",
        "S (S l)",
        tag="wpoi_step_injective_after",
        avoid=variables + ("z", "d", "i", "j"),
    )
    step_bounded_after = _bounded_into_term(
        "z",
        "d",
        "S (S l)",
        "n",
        tag="wpoi_step_bounded_after",
        avoid=variables + ("z", "d", "i", "j"),
    )
    plain_step_result = f"exists z d i j. ({step_body})"
    strengthened_result = (
        f"exists z d i j. (({step_body}) /\\ ({step_injective_after}))"
    )
    state_step_result = (
        f"exists z d i j. (({step_body}) /\\ "
        f"(({step_bounded_after}) /\\ ({step_injective_after})))"
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
        tag="wpoi_step_body_x",
        avoid=variables + ("x", "x1", "x2", "x3"),
    )
    step_injective_after_x = _injective_prefix_term(
        "x",
        "x1",
        "S (S l)",
        tag="wpoi_step_injective_after_x",
        avoid=variables + ("x", "x1", "x2", "x3"),
    )
    step_bounded_after_x = _bounded_into_term(
        "x",
        "x1",
        "S (S l)",
        "n",
        tag="wpoi_step_bounded_after_x",
        avoid=variables + ("x", "x1", "x2", "x3"),
    )

    zero_closed = _orbit_closed_prefix_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        tag="wpoi_zero_closed",
        avoid=("u", "v", "b", "c"),
    )
    zero_nonendpoint = _nonendpoint_prefix_term(
        "b",
        "c",
        "0",
        "n",
        tag="wpoi_zero_nonendpoint",
        avoid=("b", "c", "n"),
    )
    zero_bounded = _bounded_into_term(
        "b",
        "c",
        "0",
        "n",
        tag="wpoi_zero_bounded",
        avoid=("b", "c", "n"),
    )
    zero_injective = _injective_prefix_term(
        "b",
        "c",
        "0",
        tag="wpoi_zero_injective",
        avoid=("b", "c"),
    )
    zero_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "0",
        "n",
        tag="wpoi_zero_state",
        avoid=("u", "v", "b", "c", "n"),
    )

    count_state = pair_order_state(
        "u", "v", "b", "c", "l", "n", tag="wpoi_count_state"
    )
    count_result = (
        f"exists z d i j. ((({step_body}) /\\ "
        f"(({step_bounded_after}) /\\ ({step_injective_after}))) /\\ "
        "S (S l) = S m + S m)"
    )
    remaining_pair_room = "S (k + k) + S (S (S l)) = n"

    terminal_variables = ("b", "c", "l", "s", "q", "x", "rb", "rc", "r")
    terminal_bounded = _bounded_into_term(
        "b",
        "c",
        "l",
        "S (S l)",
        tag="wpoi_terminal_bounded",
        avoid=terminal_variables,
    )
    terminal_nonendpoint = _nonendpoint_prefix_term(
        "b",
        "c",
        "l",
        "S (S l)",
        tag="wpoi_terminal_nonendpoint",
        avoid=terminal_variables,
    )
    terminal_injective = _injective_prefix_term(
        "b",
        "c",
        "l",
        tag="wpoi_terminal_injective",
        avoid=terminal_variables,
    )
    terminal_value_bound = _lt_term(
        "s",
        "S (S l)",
        tag="wpoi_terminal_value_bound",
        avoid=terminal_variables,
    )
    terminal_index_bound = _lt_term(
        "q",
        "l",
        tag="wpoi_terminal_index_bound",
        avoid=terminal_variables,
    )
    terminal_entry = _beta_at_term(
        "b",
        "c",
        "q",
        "s",
        tag="wpoi_terminal_entry",
        avoid=terminal_variables,
    )
    terminal_coverage = (
        f"exists q. (({terminal_index_bound}) /\\ ({terminal_entry}))"
    )
    terminal_all_coverage = (
        f"forall s. ({terminal_value_bound}) -> "
        f"(~(s = 0) /\\ ~((S s) = S (S l))) -> ({terminal_coverage})"
    )
    terminal_magnitude_range = magnitude_range_prefix(
        "b", "c", "l", "l", tag="wpoi_terminal_magnitude_range"
    )
    terminal_recode = predecessor_recode_prefix(
        "b", "c", "rb", "rc", "l", tag="wpoi_terminal_recode"
    )
    terminal_recode_exists = f"exists rb rc. ({terminal_recode})"
    terminal_recode_surjective = surjective_prefix(
        "rb", "rc", "l", tag="wpoi_terminal_recode_surjective"
    )
    terminal_source_entry_x = _beta_at_term(
        "b",
        "c",
        "q",
        "x",
        tag="wpoi_terminal_source_entry_x",
        avoid=terminal_variables,
    )
    terminal_source_bound_x = _lt_term(
        "x",
        "S (S l)",
        tag="wpoi_terminal_source_bound_x",
        avoid=terminal_variables,
    )
    terminal_bounded_entry = (
        f"exists x. (({terminal_source_entry_x}) /\\ "
        f"({terminal_source_bound_x}))"
    )
    terminal_source_entry_succ_r = _beta_at_term(
        "b",
        "c",
        "q",
        "S r",
        tag="wpoi_terminal_source_entry_succ_r",
        avoid=terminal_variables,
    )
    terminal_recode_x = predecessor_recode_prefix(
        "b", "c", "x", "x1", "l", tag="wpoi_terminal_recode_x"
    )
    terminal_recode_surjective_x = surjective_prefix(
        "x", "x1", "l", tag="wpoi_terminal_recode_surjective_x"
    )
    terminal_target_index_bound_x2 = _lt_term(
        "x2",
        "l",
        tag="wpoi_terminal_target_index_bound_x2",
        avoid=terminal_variables + ("x1", "x2"),
    )
    terminal_target_entry_x2 = _beta_at_term(
        "x",
        "x1",
        "x2",
        "r",
        tag="wpoi_terminal_target_entry_x2",
        avoid=terminal_variables + ("x1", "x2"),
    )
    terminal_target_occurrence = (
        f"exists q. (({_lt_term('q', 'l', tag='wpoi_terminal_target_occurrence_bound', avoid=terminal_variables)}) /\\ "
        f"({_beta_at_term('x', 'x1', 'q', 'x2', tag='wpoi_terminal_target_occurrence_entry', avoid=terminal_variables + ('x2',))}))"
    )
    terminal_source_entry_x2_succ_r = _beta_at_term(
        "b",
        "c",
        "x3",
        "S x2",
        tag="wpoi_terminal_source_entry_x2_succ_r",
        avoid=terminal_variables + ("x1", "x2", "x3"),
    )
    terminal_state = _pair_order_state_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        "S (S l)",
        tag="wpoi_terminal_state",
        avoid=terminal_variables + ("u", "v"),
    )

    return (
        spec(
            "prime_pair_order_choose_append_injective",
            f"forall p n u v b c l r. p = S n -> ({step_prime}) -> "
            f"({step_inverse}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({step_closed_before}) -> ({step_nonendpoint_before}) -> "
            f"({step_injective_before}) -> ({strengthened_result})",
            (
                "prime_pair_order_choose_append",
                "beta_prefix_append_two_injective",
            ),
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
                "intro hshort",
                "intro hclosed",
                "intro hnonendpoint",
                "intro hinjective",
                f"have hstep : {plain_step_result}",
                "specialize prime_pair_order_choose_append p",
                "specialize prime_pair_order_choose_append n",
                "specialize prime_pair_order_choose_append u",
                "specialize prime_pair_order_choose_append v",
                "specialize prime_pair_order_choose_append b",
                "specialize prime_pair_order_choose_append c",
                "specialize prime_pair_order_choose_append l",
                "specialize prime_pair_order_choose_append r",
                "apply prime_pair_order_choose_append",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hshort",
                "exact hclosed",
                "exact hnonendpoint",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                f"have hparts : {step_body_x}",
                "exact hstep_witness_witness_witness_witness",
                "cases hparts",
                "cases hparts_right",
                "cases hparts_right_right",
                "cases hparts_right_right_right",
                "cases hparts_right_right_right_right",
                "cases hparts_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right_right_right",
                "cases hparts_right_right_right_right_right_right_right_right_right",
                f"have hnew_injective : {step_injective_after_x}",
                "specialize beta_prefix_append_two_injective b",
                "specialize beta_prefix_append_two_injective c",
                "specialize beta_prefix_append_two_injective x",
                "specialize beta_prefix_append_two_injective x1",
                "specialize beta_prefix_append_two_injective l",
                "specialize beta_prefix_append_two_injective x2",
                "specialize beta_prefix_append_two_injective x3",
                "apply beta_prefix_append_two_injective",
                "exact hparts_left",
                "exact hinjective",
                "exact hparts_right_right_right_left",
                "exact hparts_right_right_right_right_right_right_right_right_right_left",
                "exact hparts_right_right_right_right_right_right_right_left",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hstep_witness_witness_witness_witness",
                "exact hnew_injective",
            ),
            "Thread decoded-prefix injectivity through one constructive fresh-orbit append.",
        ),
        spec(
            "pair_order_double_succ_length",
            "forall l m. l = m + m -> S (S l) = S m + S m",
            ("add_succ_left",),
            (
                "intro l",
                "intro m",
                "intro hl",
                "rewrite hl",
                "symm",
                "simp [add_succ_left]",
            ),
            "Normalize the two-entry successor length into the next doubled pair count.",
        ),
        spec(
            "beta_prefix_append_two_bounded_into",
            "forall b c z d l n a e. "
            f"({append_bounded_trace}) -> ({append_bounded_before}) -> "
            f"({append_first_bound}) -> ({append_second_bound}) -> "
            f"({append_bounded_after})",
            ("finite_lt_succ_eq_or_lt",),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro n",
                "intro a",
                "intro e",
                "intro htrace",
                "intro hold_bounded",
                "intro hfirst_bounded",
                "intro hsecond_bounded",
                "cases htrace",
                "cases htrace_right",
                "intro q",
                "intro hq",
                "have htop : q = S l \/ exists h. h + S q = S l",
                "specialize finite_lt_succ_eq_or_lt (S l)",
                "specialize finite_lt_succ_eq_or_lt q",
                "apply finite_lt_succ_eq_or_lt",
                "exact hq",
                "cases htop",
                "exists e",
                "split",
                "rewrite htop_left",
                "rewrite htop_left",
                "exact htrace_right_left",
                "exact hsecond_bounded",
                "have hmiddle : q = l \/ exists h. h + S q = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt q",
                "apply finite_lt_succ_eq_or_lt",
                "exact htop_right",
                "cases hmiddle",
                "exists a",
                "split",
                "rewrite hmiddle_left",
                "rewrite hmiddle_left",
                "exact htrace_left",
                "exact hfirst_bounded",
                f"have hold_entry : {append_old_result}",
                "specialize hold_bounded q",
                "apply hold_bounded",
                "exact hmiddle_right",
                "cases hold_entry",
                "cases hold_entry_witness",
                "exists x",
                "split",
                "specialize htrace_right_right q",
                "specialize htrace_right_right x",
                "apply htrace_right_right",
                "exact hmiddle_right",
                "exact hold_entry_witness_left",
                "exact hold_entry_witness_right",
            ),
            "A two-entry append remains bounded when the old prefix and both appended values are bounded.",
        ),
        spec(
            "prime_pair_order_choose_append_state",
            f"forall p n u v b c l r. p = S n -> ({step_prime}) -> "
            f"({step_inverse}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({step_closed_before}) -> ({step_bounded_before}) -> "
            f"({step_nonendpoint_before}) -> ({step_injective_before}) -> "
            f"({state_step_result})",
            (
                "prime_pair_order_choose_append_injective",
                "beta_prefix_append_two_bounded_into",
            ),
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
                "intro hshort",
                "intro hclosed",
                "intro hbounded",
                "intro hnonendpoint",
                "intro hinjective",
                f"have hstep : {strengthened_result}",
                "specialize prime_pair_order_choose_append_injective p",
                "specialize prime_pair_order_choose_append_injective n",
                "specialize prime_pair_order_choose_append_injective u",
                "specialize prime_pair_order_choose_append_injective v",
                "specialize prime_pair_order_choose_append_injective b",
                "specialize prime_pair_order_choose_append_injective c",
                "specialize prime_pair_order_choose_append_injective l",
                "specialize prime_pair_order_choose_append_injective r",
                "apply prime_pair_order_choose_append_injective",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hshort",
                "exact hclosed",
                "exact hnonendpoint",
                "exact hinjective",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                f"have hcombined : (({step_body_x}) /\\ ({step_injective_after_x}))",
                "exact hstep_witness_witness_witness_witness",
                "cases hcombined",
                f"have hparts : {step_body_x}",
                "exact hcombined_left",
                "cases hparts",
                "cases hparts_right",
                "cases hparts_right_right",
                "cases hparts_right_right_right",
                "cases hparts_right_right_right_right",
                "cases hparts_right_right_right_right_right",
                f"have hnew_bounded : {step_bounded_after_x}",
                "specialize beta_prefix_append_two_bounded_into b",
                "specialize beta_prefix_append_two_bounded_into c",
                "specialize beta_prefix_append_two_bounded_into x",
                "specialize beta_prefix_append_two_bounded_into x1",
                "specialize beta_prefix_append_two_bounded_into l",
                "specialize beta_prefix_append_two_bounded_into n",
                "specialize beta_prefix_append_two_bounded_into x2",
                "specialize beta_prefix_append_two_bounded_into x3",
                "apply beta_prefix_append_two_bounded_into",
                "exact hparts_left",
                "exact hbounded",
                "exact hparts_right_left",
                "exact hparts_right_right_right_right_right_left",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hcombined_left",
                "split",
                "exact hnew_bounded",
                "exact hcombined_right",
            ),
            "Thread the complete bounded PairOrder state through one fresh inverse-orbit append.",
        ),
        spec(
            "orbit_closed_prefix_zero",
            f"forall u v b c. ({zero_closed})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro q",
                "intro s",
                "intro m",
                "intro hq",
                "intro hsource",
                "intro hinverse",
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
            "Orbit closure is vacuous on the empty decoded prefix.",
        ),
        spec(
            "bounded_into_zero",
            f"forall b c n. ({zero_bounded})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro q",
                "intro hq",
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
            "Every empty beta prefix is bounded into every codomain.",
        ),
        spec(
            "nonendpoint_prefix_zero",
            f"forall b c n. ({zero_nonendpoint})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro q",
                "intro s",
                "intro hq",
                "intro hentry",
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
            "The nonendpoint range invariant is vacuous on the empty prefix.",
        ),
        spec(
            "injective_prefix_zero",
            f"forall b c. ({zero_injective})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro q",
                "intro r",
                "intro w",
                "intro hq",
                "intro hr",
                "intro hleft",
                "intro hright",
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
            "Decoded-prefix injectivity is vacuous at length zero.",
        ),
        spec(
            "pair_order_state_zero",
            f"forall u v n. exists b c. ({zero_state})",
            (
                "orbit_closed_prefix_zero",
                "bounded_into_zero",
                "nonendpoint_prefix_zero",
                "injective_prefix_zero",
            ),
            (
                "intro u",
                "intro v",
                "intro n",
                "exists 0",
                "exists 0",
                "split",
                "specialize orbit_closed_prefix_zero u",
                "specialize orbit_closed_prefix_zero v",
                "specialize orbit_closed_prefix_zero 0",
                "specialize orbit_closed_prefix_zero 0",
                "exact orbit_closed_prefix_zero",
                "split",
                "specialize bounded_into_zero 0",
                "specialize bounded_into_zero 0",
                "specialize bounded_into_zero n",
                "exact bounded_into_zero",
                "split",
                "specialize nonendpoint_prefix_zero 0",
                "specialize nonendpoint_prefix_zero 0",
                "specialize nonendpoint_prefix_zero n",
                "exact nonendpoint_prefix_zero",
                "specialize injective_prefix_zero 0",
                "specialize injective_prefix_zero 0",
                "exact injective_prefix_zero",
            ),
            "Arbitrary zero codes witness the empty PairOrder invariant state.",
        ),
        spec(
            "pair_order_remaining_pairs_short",
            "forall l m n k. l = m + m -> "
            "S (k + k) + S (S (S l)) = n -> "
            "exists h. h + S (S (S l)) = n",
            (),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro k",
                "intro hlength",
                "intro hremaining",
                "exists S (k + k)",
                "exact hremaining",
            ),
            "Expose the primitive room witness from the doubled remaining-pair iteration contract.",
        ),
        spec(
            "pair_order_terminal_double_length",
            "forall l m n. l = m + m -> n = S (S l) -> "
            "n = S (S (m + m))",
            (),
            (
                "intro l",
                "intro m",
                "intro n",
                "intro hlength",
                "intro hterminal",
                "rewrite hterminal",
                "rewrite hlength",
                "refl",
            ),
            "Characterize the terminal nonendpoint-prefix length n-2 in doubled pair-count form.",
        ),
        spec(
            "finite_bounded_nonendpoint_injective_coverage",
            "forall b c l. "
            f"({terminal_bounded}) -> ({terminal_nonendpoint}) -> "
            f"({terminal_injective}) -> forall s. ({terminal_value_bound}) -> "
            "(~(s = 0) /\\ ~((S s) = S (S l))) -> "
            f"({terminal_coverage})",
            (
                "one_le_of_ne_zero",
                "le_of_succ_le_succ",
                "le_eq_or_lt",
                "nonzero_is_succ",
                "beta_magnitude_predecessor_recode_exists",
                "beta_magnitude_predecessor_recode_surjective",
                "beta_magnitude_predecessor_recode_reflect",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro hbounded",
                "intro hnonendpoint",
                "intro hinjective",
                f"have hmagnitude : {terminal_magnitude_range}",
                "intro q",
                "intro hq",
                f"have hbounded_entry : {terminal_bounded_entry}",
                "specialize hbounded q",
                "apply hbounded",
                "exact hq",
                "cases hbounded_entry",
                "cases hbounded_entry_witness",
                "have hxnonendpoint : ~(x = 0) /\\ ~((S x) = S (S l))",
                "specialize hnonendpoint q",
                "specialize hnonendpoint x",
                "apply hnonendpoint",
                "exact hq",
                "exact hbounded_entry_witness_left",
                "cases hxnonendpoint",
                "exists x",
                "split",
                "exact hbounded_entry_witness_left",
                "split",
                "specialize one_le_of_ne_zero x",
                "apply one_le_of_ne_zero",
                "exact hxnonendpoint_left",
                "have hxle_succ : exists h. h + x = S l",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ (S l)",
                "apply le_of_succ_le_succ",
                "exact hbounded_entry_witness_right",
                "have hxsplit : x = S l \/ exists h. h + S x = S l",
                "specialize le_eq_or_lt x",
                "specialize le_eq_or_lt (S l)",
                "apply le_eq_or_lt",
                "exact hxle_succ",
                "cases hxsplit",
                "exfalso",
                "apply hxnonendpoint_right",
                "rewrite hxsplit_left",
                "refl",
                "specialize le_of_succ_le_succ x",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hxsplit_right",
                f"have hrecode_exists : {terminal_recode_exists}",
                "specialize beta_magnitude_predecessor_recode_exists b",
                "specialize beta_magnitude_predecessor_recode_exists c",
                "specialize beta_magnitude_predecessor_recode_exists l",
                "specialize beta_magnitude_predecessor_recode_exists l",
                "apply beta_magnitude_predecessor_recode_exists",
                "exact hmagnitude",
                "cases hrecode_exists",
                "cases hrecode_exists_witness",
                f"have hrecode : {terminal_recode_x}",
                "exact hrecode_exists_witness_witness",
                f"have hsurjective : {terminal_recode_surjective_x}",
                "specialize beta_magnitude_predecessor_recode_surjective b",
                "specialize beta_magnitude_predecessor_recode_surjective c",
                "specialize beta_magnitude_predecessor_recode_surjective x",
                "specialize beta_magnitude_predecessor_recode_surjective x1",
                "specialize beta_magnitude_predecessor_recode_surjective l",
                "apply beta_magnitude_predecessor_recode_surjective",
                "exact hmagnitude",
                "exact hinjective",
                "exact hrecode",
                "intro s",
                "intro hsbound",
                "intro hsendpoints",
                "cases hsendpoints",
                "have hspred : exists r. s = S r",
                "specialize nonzero_is_succ s",
                "apply nonzero_is_succ",
                "exact hsendpoints_left",
                "cases hspred",
                "have hsle : exists h. h + s = S l",
                "specialize le_of_succ_le_succ s",
                "specialize le_of_succ_le_succ (S l)",
                "apply le_of_succ_le_succ",
                "exact hsbound",
                "rewrite hspred_witness at hsle",
                "have hrle : exists h. h + x2 = l",
                "specialize le_of_succ_le_succ x2",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hsle",
                "have hrsplit : x2 = l \/ exists h. h + S x2 = l",
                "specialize le_eq_or_lt x2",
                "specialize le_eq_or_lt l",
                "apply le_eq_or_lt",
                "exact hrle",
                "cases hrsplit",
                "exfalso",
                "apply hsendpoints_right",
                "rewrite hspred_witness",
                "rewrite hrsplit_left",
                "refl",
                f"have htarget : {terminal_target_occurrence}",
                "specialize hsurjective x2",
                "apply hsurjective",
                "exact hrsplit_right",
                "cases htarget",
                "cases htarget_witness",
                f"have hsource : {terminal_source_entry_x2_succ_r}",
                "specialize beta_magnitude_predecessor_recode_reflect b",
                "specialize beta_magnitude_predecessor_recode_reflect c",
                "specialize beta_magnitude_predecessor_recode_reflect x",
                "specialize beta_magnitude_predecessor_recode_reflect x1",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect l",
                "specialize beta_magnitude_predecessor_recode_reflect x3",
                "specialize beta_magnitude_predecessor_recode_reflect x2",
                "apply beta_magnitude_predecessor_recode_reflect",
                "exact hmagnitude",
                "exact hrecode",
                "exact htarget_witness_left",
                "exact htarget_witness_right",
                "exists x3",
                "split",
                "exact htarget_witness_left",
                "rewrite hspred_witness",
                "rewrite hspred_witness",
                "exact hsource",
            ),
            "A bounded injective terminal prefix covers exactly every nonendpoint value below n = l+2.",
        ),
        spec(
            "pair_order_state_terminal_coverage",
            "forall u v b c l. "
            f"({terminal_state}) -> forall s. ({terminal_value_bound}) -> "
            "(~(s = 0) /\\ ~((S s) = S (S l))) -> "
            f"({terminal_coverage})",
            ("finite_bounded_nonendpoint_injective_coverage",),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro hstate",
                "cases hstate",
                "cases hstate_right",
                "cases hstate_right_right",
                f"have hall_coverage : {terminal_all_coverage}",
                "specialize finite_bounded_nonendpoint_injective_coverage b",
                "specialize finite_bounded_nonendpoint_injective_coverage c",
                "specialize finite_bounded_nonendpoint_injective_coverage l",
                "apply finite_bounded_nonendpoint_injective_coverage",
                "exact hstate_right_left",
                "exact hstate_right_right_left",
                "exact hstate_right_right_right",
                "intro s",
                "intro hsbound",
                "intro hsendpoints",
                "specialize hall_coverage s",
                "apply hall_coverage",
                "exact hsbound",
                "exact hsendpoints",
            ),
            "The strengthened PairOrder state is complete at the exact terminal length n-2.",
        ),
        spec(
            "prime_pair_order_pair_count_step",
            f"forall p n u v b c l r m. p = S n -> ({step_prime}) -> "
            f"({step_inverse}) -> n = S r -> "
            "(exists h. h + S (S (S l)) = n) -> "
            f"({count_state}) -> l = m + m -> ({count_result})",
            (
                "prime_pair_order_choose_append_state",
                "pair_order_double_succ_length",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro m",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hshort",
                "intro hstate",
                "intro hlength",
                "cases hstate",
                "cases hstate_right",
                "cases hstate_right_right",
                f"have hstep : {state_step_result}",
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
                "exact hshort",
                "exact hstate_left",
                "exact hstate_right_left",
                "exact hstate_right_right_left",
                "exact hstate_right_right_right",
                "have hnext_length : S (S l) = S m + S m",
                "specialize pair_order_double_succ_length l",
                "specialize pair_order_double_succ_length m",
                "apply pair_order_double_succ_length",
                "exact hlength",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hstep_witness_witness_witness_witness",
                "exact hnext_length",
            ),
            "Advance one doubled pair count while the explicit fresh-orbit room premise holds.",
        ),
        spec(
            "prime_pair_order_remaining_pair_step",
            f"forall p n u v b c l r m k. p = S n -> ({step_prime}) -> "
            f"({step_inverse}) -> n = S r -> "
            f"({count_state}) -> l = m + m -> ({remaining_pair_room}) -> "
            f"({count_result})",
            (
                "pair_order_remaining_pairs_short",
                "prime_pair_order_pair_count_step",
            ),
            (
                "intro p",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro r",
                "intro m",
                "intro k",
                "intro hpn",
                "intro hp",
                "intro hprefix",
                "intro hnr",
                "intro hstate",
                "intro hlength",
                "intro hremaining",
                "have hshort : exists h. h + S (S (S l)) = n",
                "specialize pair_order_remaining_pairs_short l",
                "specialize pair_order_remaining_pairs_short m",
                "specialize pair_order_remaining_pairs_short n",
                "specialize pair_order_remaining_pairs_short k",
                "apply pair_order_remaining_pairs_short",
                "exact hlength",
                "exact hremaining",
                "specialize prime_pair_order_pair_count_step p",
                "specialize prime_pair_order_pair_count_step n",
                "specialize prime_pair_order_pair_count_step u",
                "specialize prime_pair_order_pair_count_step v",
                "specialize prime_pair_order_pair_count_step b",
                "specialize prime_pair_order_pair_count_step c",
                "specialize prime_pair_order_pair_count_step l",
                "specialize prime_pair_order_pair_count_step r",
                "specialize prime_pair_order_pair_count_step m",
                "apply prime_pair_order_pair_count_step",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact hnr",
                "exact hshort",
                "exact hstate",
                "exact hlength",
            ),
            "Append one orbit pair from an explicit remaining-pair count, preserving the doubled iteration index.",
        ),
    )


__all__ = [
    "make_wilson_pair_order_induction_candidate_theorems",
    "pair_order_state",
]
