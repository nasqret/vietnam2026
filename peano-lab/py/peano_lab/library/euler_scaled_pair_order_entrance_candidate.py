"""Isolated fixed-point-free PairOrder entrance for Euler's scaled map.

The scaled inverse prefix is indexed by zero-based source indices but stores
actual mate residues.  Thus a decoded edge from source ``i`` to source ``j``
has the form ``BetaAt(u,v,i,S j)``.  Wilson's generic PairOrder closure stores
``j`` itself and therefore cannot be reused unchanged.  This module adds only
the shifted closure relation; finite omission, two-entry append reflection,
and append injectivity remain the generic Wilson infrastructure.

Every relation expands to unchanged first-order Peano arithmetic.  The
factory is an unregistered authoring candidate and introduces no axiom,
parser form, or kernel constant.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_scaled_inverse_candidate import _identifier, prime
from .euler_scaled_inverse_prefix_candidate import (
    scaled_inverse_index,
    scaled_inverse_prefix,
)
from .quadratic_residue_surface import quadratic_residue
from .wilson_pair_order_candidate import (
    _append_two_reflection_term,
    _append_two_trace_term,
    _beta_at_term,
    _contains_term,
    _injective_prefix_term,
    _lt_term,
    _omits_some_term,
    _omits_value_term,
)


def _scaled_orbit_closed_term(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    length_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    """Expand closure under edges decoded as source ``i`` to mate ``S j``."""

    position = f"espo_position_{tag}"
    source = f"espo_source_{tag}"
    mate = f"espo_mate_{tag}"
    mate_position = f"espo_mate_position_{tag}"
    generated = (position, source, mate, mate_position)
    if len(set(generated)) != len(generated) or set(generated) & set(avoid):
        raise ValueError("generated scaled-orbit binder captures an argument")
    local = avoid + generated
    position_bound = _lt_term(
        position,
        length_term,
        tag=f"{tag}_position_bound",
        avoid=local,
    )
    source_entry = _beta_at_term(
        order_code,
        order_scale,
        position,
        source,
        tag=f"{tag}_source_entry",
        avoid=local,
    )
    scaled_entry = _beta_at_term(
        scaled_code,
        scaled_scale,
        source,
        f"S {mate}",
        tag=f"{tag}_scaled_entry",
        avoid=local,
    )
    mate_bound = _lt_term(
        mate_position,
        length_term,
        tag=f"{tag}_mate_bound",
        avoid=local,
    )
    mate_entry = _beta_at_term(
        order_code,
        order_scale,
        mate_position,
        mate,
        tag=f"{tag}_mate_entry",
        avoid=local,
    )
    return (
        f"forall {position} {source} {mate}. ({position_bound}) -> "
        f"({source_entry}) -> ({scaled_entry}) -> exists {mate_position}. "
        f"(({mate_bound}) /\\ ({mate_entry}))"
    )


def scaled_orbit_closed_prefix(
    scaled_code: str,
    scaled_scale: str,
    order_code: str,
    order_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand shifted orbit closure at an identifier-valued length."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (scaled_code, "scaled code"),
            (scaled_scale, "scaled scale"),
            (order_code, "order code"),
            (order_scale, "order scale"),
            (length, "prefix length"),
        )
    )
    return _scaled_orbit_closed_term(
        *variables,
        tag=tag,
        avoid=variables,
    )


def _conjunction(*terms: str) -> str:
    if not terms:
        raise ValueError("a conjunction requires at least one formula")
    result = terms[-1]
    for term in reversed(terms[:-1]):
        result = f"(({term}) /\\ ({result}))"
    return result


def make_euler_scaled_pair_order_entrance_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build shifted closure, omitted-orbit choice, and one append step."""

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
        "l",
        "i",
        "j",
        "y",
        "q",
        "s",
        "m",
    )
    unused_closed = _scaled_orbit_closed_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        tag="unused_closed",
        avoid=base_variables,
    )
    unused_source_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "i",
        tag="unused_source_omit",
        avoid=base_variables,
    )
    unused_back = _beta_at_term(
        "u",
        "v",
        "j",
        "S i",
        tag="unused_back",
        avoid=base_variables,
    )
    unused_mate_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "j",
        tag="unused_mate_omit",
        avoid=base_variables,
    )
    unused_source_occurs = _contains_term(
        "b",
        "c",
        "l",
        "i",
        tag="unused_source_occurs",
        avoid=base_variables,
    )

    closure_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "i",
        "j",
        tag="closure_trace",
        avoid=base_variables,
    )
    closure_before = _scaled_orbit_closed_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        tag="closure_before",
        avoid=base_variables,
    )
    closure_forward = _beta_at_term(
        "u",
        "v",
        "i",
        "S j",
        tag="closure_forward",
        avoid=base_variables,
    )
    closure_back = _beta_at_term(
        "u",
        "v",
        "j",
        "S i",
        tag="closure_back",
        avoid=base_variables,
    )
    closure_after = _scaled_orbit_closed_term(
        "u",
        "v",
        "z",
        "d",
        "S (S l)",
        tag="closure_after",
        avoid=base_variables,
    )
    closure_reflection = _append_two_reflection_term(
        "b",
        "c",
        "l",
        "i",
        "j",
        "q",
        "s",
        tag="closure_reflection",
        avoid=base_variables,
    )
    closure_reflection_bound = _lt_term(
        "q",
        "S (S l)",
        tag="closure_reflection_bound",
        avoid=base_variables,
    )
    closure_reflection_entry = _beta_at_term(
        "z",
        "d",
        "q",
        "s",
        tag="closure_reflection_entry",
        avoid=base_variables,
    )
    closure_reflection_all = (
        f"forall q s. ({closure_reflection_bound}) -> "
        f"({closure_reflection_entry}) -> ({closure_reflection})"
    )
    closure_old_occurrence = _contains_term(
        "b",
        "c",
        "l",
        "m",
        tag="closure_old_occurrence",
        avoid=base_variables,
    )

    choose_prime = prime("p", tag="espo_choose_prime")
    choose_nonresidue = quadratic_residue(
        "p", "a", tag="espo_choose_nonresidue"
    )
    choose_prefix = scaled_inverse_prefix(
        "p", "a", "n", "u", "v", "n", tag="espo_choose_prefix"
    )
    choose_short = _lt_term(
        "l", "n", tag="choose_short", avoid=base_variables
    )
    choose_omitted = _omits_some_term(
        "b",
        "c",
        "l",
        "n",
        tag="choose_omitted",
        avoid=base_variables,
    )
    chosen_i_bound = _lt_term(
        "i", "n", tag="chosen_i_bound", avoid=base_variables
    )
    chosen_i_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "i",
        tag="chosen_i_omit",
        avoid=base_variables,
    )
    chosen_j_bound = _lt_term(
        "j", "n", tag="chosen_j_bound", avoid=base_variables
    )
    chosen_forward = _beta_at_term(
        "u",
        "v",
        "i",
        "S j",
        tag="chosen_forward",
        avoid=base_variables,
    )
    chosen_back = _beta_at_term(
        "u",
        "v",
        "j",
        "S i",
        tag="chosen_back",
        avoid=base_variables,
    )
    chosen_result = "exists i j. " + _conjunction(
        chosen_i_bound,
        chosen_i_omit,
        chosen_j_bound,
        "~(i = j)",
        chosen_forward,
        chosen_back,
    )

    chosen_stored_x = (
        "exists y. "
        + _conjunction(
            _beta_at_term(
                "u",
                "v",
                "x",
                "y",
                tag="chosen_stored_x_entry",
                avoid=base_variables + ("x", "x1", "x2"),
            ),
            scaled_inverse_index(
                "p", "a", "n", "x", "y", tag="chosen_stored_x_relation"
            ),
        )
    )
    chosen_involutive_x1 = (
        "exists j. "
        + _conjunction(
            "x1 = S j",
            _lt_term(
                "j",
                "n",
                tag="chosen_involutive_j_bound",
                avoid=base_variables + ("x", "x1", "x2"),
            ),
            _beta_at_term(
                "u",
                "v",
                "j",
                "S x",
                tag="chosen_involutive_back",
                avoid=base_variables + ("x", "x1", "x2"),
            ),
        )
    )
    chosen_forward_x2 = _beta_at_term(
        "u",
        "v",
        "x",
        "S x2",
        tag="chosen_forward_x2",
        avoid=base_variables + ("x", "x1", "x2"),
    )
    step_closed_before = _scaled_orbit_closed_term(
        "u",
        "v",
        "b",
        "c",
        "l",
        tag="step_closed_before",
        avoid=base_variables,
    )
    step_injective_before = _injective_prefix_term(
        "b",
        "c",
        "l",
        tag="step_injective_before",
        avoid=base_variables,
    )
    step_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "i",
        "j",
        tag="step_trace",
        avoid=base_variables,
    )
    step_j_omit = _omits_value_term(
        "b",
        "c",
        "l",
        "j",
        tag="step_j_omit",
        avoid=base_variables,
    )
    step_closed_after = _scaled_orbit_closed_term(
        "u",
        "v",
        "z",
        "d",
        "S (S l)",
        tag="step_closed_after",
        avoid=base_variables,
    )
    step_injective_after = _injective_prefix_term(
        "z",
        "d",
        "S (S l)",
        tag="step_injective_after",
        avoid=base_variables,
    )
    step_result = "exists z d i j. " + _conjunction(
        step_trace,
        chosen_i_bound,
        chosen_j_bound,
        chosen_i_omit,
        step_j_omit,
        "~(i = j)",
        chosen_forward,
        chosen_back,
        step_closed_after,
        step_injective_after,
    )

    witness_variables = base_variables + ("x", "x1", "x2", "x3")
    witness_chosen_parts = _conjunction(
        _lt_term("x", "n", tag="witness_i_bound", avoid=witness_variables),
        _omits_value_term(
            "b", "c", "l", "x", tag="witness_i_omit", avoid=witness_variables
        ),
        _lt_term("x1", "n", tag="witness_j_bound", avoid=witness_variables),
        "~(x = x1)",
        _beta_at_term(
            "u", "v", "x", "S x1", tag="witness_forward", avoid=witness_variables
        ),
        _beta_at_term(
            "u", "v", "x1", "S x", tag="witness_back", avoid=witness_variables
        ),
    )
    witness_j_omit = _omits_value_term(
        "b", "c", "l", "x1", tag="witness_j_omit", avoid=witness_variables
    )
    witness_exists_trace = _append_two_trace_term(
        "b",
        "c",
        "z",
        "d",
        "l",
        "x",
        "x1",
        tag="witness_exists_trace",
        avoid=witness_variables,
    )
    witness_trace = _append_two_trace_term(
        "b",
        "c",
        "x2",
        "x3",
        "l",
        "x",
        "x1",
        tag="witness_trace",
        avoid=witness_variables,
    )
    witness_closed_after = _scaled_orbit_closed_term(
        "u",
        "v",
        "x2",
        "x3",
        "S (S l)",
        tag="witness_closed_after",
        avoid=witness_variables,
    )
    witness_injective_after = _injective_prefix_term(
        "x2",
        "x3",
        "S (S l)",
        tag="witness_injective_after",
        avoid=witness_variables,
    )

    return (
        spec(
            "scaled_orbit_closed_unused_mate",
            f"forall u v b c l i j. ({unused_closed}) -> "
            f"({unused_source_omit}) -> ({unused_back}) -> ({unused_mate_omit})",
            (),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro i",
                "intro j",
                "intro hclosed",
                "intro hiomit",
                "intro hback",
                "intro hjcontains",
                "cases hjcontains",
                "cases hjcontains_witness",
                f"have hioccurs : {unused_source_occurs}",
                "specialize hclosed x",
                "specialize hclosed j",
                "specialize hclosed i",
                "apply hclosed",
                "exact hjcontains_witness_left",
                "exact hjcontains_witness_right",
                "exact hback",
                "cases hioccurs",
                "cases hioccurs_witness",
                "apply hiomit",
                "exists x1",
                "split",
                "exact hioccurs_witness_left",
                "exact hioccurs_witness_right",
            ),
            "Shifted orbit closure transfers omission across a decoded back edge.",
        ),
        spec(
            "beta_prefix_append_two_scaled_orbit_closed",
            f"forall u v b c z d l i j. ({closure_trace}) -> "
            f"({closure_before}) -> ({closure_forward}) -> "
            f"({closure_back}) -> ({closure_after})",
            (
                "beta_prefix_append_two_reflect",
                "beta_at_unique",
                "succ_injective",
                "le_refl",
                "le_succ",
            ),
            (
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro l",
                "intro i",
                "intro j",
                "intro htrace",
                "intro hclosed",
                "intro hforward",
                "intro hback",
                f"have htrace_parts : {closure_trace}",
                "exact htrace",
                "cases htrace_parts",
                "cases htrace_parts_right",
                "intro q",
                "intro s",
                "intro m",
                "intro hq",
                "intro hsource",
                "intro hscaled",
                f"have hreflect_all : {closure_reflection_all}",
                "specialize beta_prefix_append_two_reflect b",
                "specialize beta_prefix_append_two_reflect c",
                "specialize beta_prefix_append_two_reflect z",
                "specialize beta_prefix_append_two_reflect d",
                "specialize beta_prefix_append_two_reflect l",
                "specialize beta_prefix_append_two_reflect i",
                "specialize beta_prefix_append_two_reflect j",
                "apply beta_prefix_append_two_reflect",
                "exact htrace",
                f"have hreflect : {closure_reflection}",
                "specialize hreflect_all q",
                "specialize hreflect_all s",
                "apply hreflect_all",
                "exact hq",
                "exact hsource",
                "cases hreflect",
                "cases hreflect_left",
                "have hmate_succ : S m = S i",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique j",
                "specialize beta_at_unique (S m)",
                "specialize beta_at_unique (S i)",
                "apply beta_at_unique",
                "rewrite hreflect_left_right at hscaled",
                "rewrite hreflect_left_right at hscaled",
                "exact hscaled",
                "exact hback",
                "have hmate : m = i",
                "specialize succ_injective m",
                "specialize succ_injective i",
                "apply succ_injective",
                "exact hmate_succ",
                "exists l",
                "split",
                "specialize le_succ (S l)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "specialize le_refl (S l)",
                "exact le_refl",
                "rewrite hmate",
                "rewrite hmate",
                "exact htrace_parts_left",
                "cases hreflect_right",
                "cases hreflect_right_left",
                "have hmate_succ_second : S m = S j",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique i",
                "specialize beta_at_unique (S m)",
                "specialize beta_at_unique (S j)",
                "apply beta_at_unique",
                "rewrite hreflect_right_left_right at hscaled",
                "rewrite hreflect_right_left_right at hscaled",
                "exact hscaled",
                "exact hforward",
                "have hmate_second : m = j",
                "specialize succ_injective m",
                "specialize succ_injective j",
                "apply succ_injective",
                "exact hmate_succ_second",
                "exists (S l)",
                "split",
                "specialize le_refl (S (S l))",
                "exact le_refl",
                "rewrite hmate_second",
                "rewrite hmate_second",
                "exact htrace_parts_right_left",
                "cases hreflect_right_right",
                f"have hold_occurrence : {closure_old_occurrence}",
                "specialize hclosed q",
                "specialize hclosed s",
                "specialize hclosed m",
                "apply hclosed",
                "exact hreflect_right_right_left",
                "exact hreflect_right_right_right",
                "exact hscaled",
                "cases hold_occurrence",
                "cases hold_occurrence_witness",
                "exists x",
                "split",
                "have hlift : exists h. h + S x = S l",
                "specialize le_succ (S x)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hold_occurrence_witness_left",
                "specialize le_succ (S x)",
                "specialize le_succ (S l)",
                "apply le_succ",
                "exact hlift",
                "specialize htrace_parts_right_right x",
                "specialize htrace_parts_right_right m",
                "apply htrace_parts_right_right",
                "exact hold_occurrence_witness_left",
                "exact hold_occurrence_witness_right",
            ),
            "Appending both zero-based sources preserves closure under actual-mate entries S j.",
        ),
        spec(
            "scaled_inverse_prefix_choose_omitted_orbit",
            "forall p a n u v b c l. p = S n -> "
            f"({choose_prime}) -> ~({choose_nonresidue}) -> "
            f"({choose_prefix}) -> ({choose_short}) -> ({chosen_result})",
            (
                "finite_short_prefix_omits",
                "scaled_inverse_prefix_involutive",
                "scaled_inverse_prefix_no_fixed_of_not_qres",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "intro hshort",
                f"have homitted : {choose_omitted}",
                "specialize finite_short_prefix_omits b",
                "specialize finite_short_prefix_omits c",
                "specialize finite_short_prefix_omits l",
                "specialize finite_short_prefix_omits n",
                "apply finite_short_prefix_omits",
                "exact hshort",
                "cases homitted",
                "cases homitted_witness",
                f"have hstored : {chosen_stored_x}",
                "specialize hprefix x",
                "apply hprefix",
                "exact homitted_witness_left",
                "cases hstored",
                "cases hstored_witness",
                f"have hinvolutive : {chosen_involutive_x1}",
                "specialize scaled_inverse_prefix_involutive p",
                "specialize scaled_inverse_prefix_involutive a",
                "specialize scaled_inverse_prefix_involutive n",
                "specialize scaled_inverse_prefix_involutive u",
                "specialize scaled_inverse_prefix_involutive v",
                "specialize scaled_inverse_prefix_involutive x",
                "specialize scaled_inverse_prefix_involutive x1",
                "apply scaled_inverse_prefix_involutive",
                "exact hpn",
                "exact hp",
                "exact hprefix",
                "exact homitted_witness_left",
                "exact hstored_witness_left",
                "cases hinvolutive",
                "cases hinvolutive_witness",
                "cases hinvolutive_witness_right",
                f"have hforward : {chosen_forward_x2}",
                "rewrite <- hinvolutive_witness_left",
                "rewrite <- hinvolutive_witness_left",
                "exact hstored_witness_left",
                "have hdistinct : ~(x = x2)",
                "intro heq",
                "rewrite <- heq at hforward",
                "rewrite <- heq at hforward",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres p",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres a",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres n",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres u",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres v",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres n",
                "specialize scaled_inverse_prefix_no_fixed_of_not_qres x",
                "apply scaled_inverse_prefix_no_fixed_of_not_qres",
                "exact hnotqres",
                "exact hprefix",
                "exact homitted_witness_left",
                "exact hforward",
                "exists x",
                "exists x2",
                "split",
                "exact homitted_witness_left",
                "split",
                "exact homitted_witness_right",
                "split",
                "exact hinvolutive_witness_right_left",
                "split",
                "exact hdistinct",
                "split",
                "exact hforward",
                "exact hinvolutive_witness_right_right",
            ),
            "Choose an omitted source, decode its actual mate S j, and expose a distinct involutive pair.",
        ),
        spec(
            "scaled_inverse_pair_order_choose_append",
            "forall p a n u v b c l. p = S n -> "
            f"({choose_prime}) -> ~({choose_nonresidue}) -> "
            f"({choose_prefix}) -> ({choose_short}) -> "
            f"({step_closed_before}) -> ({step_injective_before}) -> ({step_result})",
            (
                "scaled_inverse_prefix_choose_omitted_orbit",
                "scaled_orbit_closed_unused_mate",
                "beta_prefix_append_two_exists",
                "beta_prefix_append_two_scaled_orbit_closed",
                "beta_prefix_append_two_injective",
            ),
            (
                "intro p",
                "intro a",
                "intro n",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro l",
                "intro hpn",
                "intro hp",
                "intro hnotqres",
                "intro hprefix",
                "intro hshort",
                "intro hclosed",
                "intro hinjective",
                "have hchosen : exists i j. "
                + _conjunction(
                    chosen_i_bound,
                    chosen_i_omit,
                    chosen_j_bound,
                    "~(i = j)",
                    chosen_forward,
                    chosen_back,
                ),
                "specialize scaled_inverse_prefix_choose_omitted_orbit p",
                "specialize scaled_inverse_prefix_choose_omitted_orbit a",
                "specialize scaled_inverse_prefix_choose_omitted_orbit n",
                "specialize scaled_inverse_prefix_choose_omitted_orbit u",
                "specialize scaled_inverse_prefix_choose_omitted_orbit v",
                "specialize scaled_inverse_prefix_choose_omitted_orbit b",
                "specialize scaled_inverse_prefix_choose_omitted_orbit c",
                "specialize scaled_inverse_prefix_choose_omitted_orbit l",
                "apply scaled_inverse_prefix_choose_omitted_orbit",
                "exact hpn",
                "exact hp",
                "exact hnotqres",
                "exact hprefix",
                "exact hshort",
                "cases hchosen",
                "cases hchosen_witness",
                f"have hparts : {witness_chosen_parts}",
                "exact hchosen_witness_witness",
                "cases hparts",
                "cases hparts_right",
                "cases hparts_right_right",
                "cases hparts_right_right_right",
                "cases hparts_right_right_right_right",
                f"have hjomit : {witness_j_omit}",
                "intro hjcontains",
                "specialize scaled_orbit_closed_unused_mate u",
                "specialize scaled_orbit_closed_unused_mate v",
                "specialize scaled_orbit_closed_unused_mate b",
                "specialize scaled_orbit_closed_unused_mate c",
                "specialize scaled_orbit_closed_unused_mate l",
                "specialize scaled_orbit_closed_unused_mate x",
                "specialize scaled_orbit_closed_unused_mate x1",
                "apply scaled_orbit_closed_unused_mate",
                "exact hclosed",
                "exact hparts_right_left",
                "exact hparts_right_right_right_right_right",
                "exact hjcontains",
                f"have happend : exists z d. ({witness_exists_trace})",
                "specialize beta_prefix_append_two_exists b",
                "specialize beta_prefix_append_two_exists c",
                "specialize beta_prefix_append_two_exists l",
                "specialize beta_prefix_append_two_exists x",
                "specialize beta_prefix_append_two_exists x1",
                "exact beta_prefix_append_two_exists",
                "cases happend",
                "cases happend_witness",
                f"have hclosed_after : {witness_closed_after}",
                "specialize beta_prefix_append_two_scaled_orbit_closed u",
                "specialize beta_prefix_append_two_scaled_orbit_closed v",
                "specialize beta_prefix_append_two_scaled_orbit_closed b",
                "specialize beta_prefix_append_two_scaled_orbit_closed c",
                "specialize beta_prefix_append_two_scaled_orbit_closed x2",
                "specialize beta_prefix_append_two_scaled_orbit_closed x3",
                "specialize beta_prefix_append_two_scaled_orbit_closed l",
                "specialize beta_prefix_append_two_scaled_orbit_closed x",
                "specialize beta_prefix_append_two_scaled_orbit_closed x1",
                "apply beta_prefix_append_two_scaled_orbit_closed",
                "exact happend_witness_witness",
                "exact hclosed",
                "exact hparts_right_right_right_right_left",
                "exact hparts_right_right_right_right_right",
                f"have hinjective_after : {witness_injective_after}",
                "specialize beta_prefix_append_two_injective b",
                "specialize beta_prefix_append_two_injective c",
                "specialize beta_prefix_append_two_injective x2",
                "specialize beta_prefix_append_two_injective x3",
                "specialize beta_prefix_append_two_injective l",
                "specialize beta_prefix_append_two_injective x",
                "specialize beta_prefix_append_two_injective x1",
                "apply beta_prefix_append_two_injective",
                "exact happend_witness_witness",
                "exact hinjective",
                "exact hparts_right_left",
                "exact hjomit",
                "exact hparts_right_right_right_left",
                "exists x2",
                "exists x3",
                "exists x",
                "exists x1",
                "split",
                "exact happend_witness_witness",
                "split",
                "exact hparts_left",
                "split",
                "exact hparts_right_right_left",
                "split",
                "exact hparts_right_left",
                "split",
                "exact hjomit",
                "split",
                "exact hparts_right_right_right_left",
                "split",
                "exact hparts_right_right_right_right_left",
                "split",
                "exact hparts_right_right_right_right_right",
                "split",
                "exact hclosed_after",
                "exact hinjective_after",
            ),
            "Choose one omitted fixed-point-free scaled orbit and append its two sources adjacently.",
        ),
    )


__all__ = [
    "make_euler_scaled_pair_order_entrance_candidate_theorems",
    "scaled_orbit_closed_prefix",
]
