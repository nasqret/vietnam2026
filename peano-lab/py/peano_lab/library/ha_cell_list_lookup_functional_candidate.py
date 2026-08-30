"""Private K3B functionality of outer-head ``ListAt``.

The sole row proves uniqueness of a decoded head by induction on the outer
index, using the zero and successor lookup equations.  Every authoring
relation expands into the unchanged first-order Peano language before
parsing.  The candidate is dependency-curried, unregistered, and unadmitted;
this module makes no empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def make_ha_cell_list_lookup_functional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_functional`` candidate row."""

    target_left = cell_list_at("z", "i", "a", tag="functional_target_left")
    target_right = cell_list_at(
        "z", "i", "d", tag="functional_target_right"
    )

    induction_left = cell_list_at(
        "z", "i", "a", tag="functional_induction_left"
    )
    induction_right = cell_list_at(
        "z", "i", "d", tag="functional_induction_right"
    )
    induction_motive = (
        "forall i z a d. "
        f"({induction_left}) -> ({induction_right}) -> a = d"
    )

    base_head_a = (
        f"exists t l. (({cell('z', 'a', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='functional_base_length_a')}))"
    )
    base_head_d = (
        f"exists t l. (({cell('z', 'd', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='functional_base_length_d')}))"
    )

    step_tail_a = cell_list_at(
        "t", "i", "a", tag="functional_step_tail_a"
    )
    step_tail_d = cell_list_at(
        "t", "i", "d", tag="functional_step_tail_d"
    )
    step_decomposition_a = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ ({step_tail_a}))"
    )
    step_decomposition_d = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ ({step_tail_d}))"
    )

    return (
        spec(
            "list_at_functional",
            "forall z i a d. "
            f"({target_left}) -> ({target_right}) -> a = d",
            (
                "list_at_head_iff",
                "list_at_succ_iff",
                "cell_functional",
            ),
            (
                f"have hlookup_induction : {induction_motive}",
                "intro i",
                "induction i",
                # Zero outer index: compare the two exact outer heads.
                "intro z",
                "intro a",
                "intro d",
                "intro hlookup_a",
                "intro hlookup_d",
                f"have hhead_a : {base_head_a}",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff a",
                "cases list_at_head_iff",
                "apply list_at_head_iff_left",
                "exact hlookup_a",
                f"have hhead_d : {base_head_d}",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff d",
                "cases list_at_head_iff",
                "apply list_at_head_iff_left",
                "exact hlookup_d",
                "cases hhead_a",
                "cases hhead_a_witness",
                "cases hhead_a_witness_witness",
                "cases hhead_d",
                "cases hhead_d_witness",
                "cases hhead_d_witness_witness",
                "have hcomponents : a = d /\\ x = x2",
                "specialize cell_functional z",
                "specialize cell_functional a",
                "specialize cell_functional x",
                "specialize cell_functional d",
                "specialize cell_functional x2",
                "apply cell_functional",
                "exact hhead_a_witness_witness_left",
                "exact hhead_d_witness_witness_left",
                "cases hcomponents",
                "exact hcomponents_left",
                # Successor outer index: identify tails, then invoke IH.
                "intro z",
                "intro a",
                "intro d",
                "intro hlookup_a",
                "intro hlookup_d",
                f"have hstep_a : {step_decomposition_a}",
                "specialize list_at_succ_iff z",
                "specialize list_at_succ_iff i",
                "specialize list_at_succ_iff a",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_left",
                "exact hlookup_a",
                f"have hstep_d : {step_decomposition_d}",
                "specialize list_at_succ_iff z",
                "specialize list_at_succ_iff i",
                "specialize list_at_succ_iff d",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_left",
                "exact hlookup_d",
                "cases hstep_a",
                "cases hstep_a_witness",
                "cases hstep_a_witness_witness",
                "cases hstep_d",
                "cases hstep_d_witness",
                "cases hstep_d_witness_witness",
                "have hcomponents : x1 = x3 /\\ x = x2",
                "specialize cell_functional z",
                "specialize cell_functional x1",
                "specialize cell_functional x",
                "specialize cell_functional x3",
                "specialize cell_functional x2",
                "apply cell_functional",
                "exact hstep_a_witness_witness_left",
                "exact hstep_d_witness_witness_left",
                "cases hcomponents",
                "have htail : x = x2",
                "exact hcomponents_right",
                "rewrite htail at hstep_a_witness_witness_right",
                "rewrite htail at hstep_a_witness_witness_right",
                "specialize IH x2",
                "specialize IH a",
                "specialize IH d",
                "apply IH",
                "exact hstep_a_witness_witness_right",
                "exact hstep_d_witness_witness_right",
                # Reorder the generalized induction theorem to the RFC surface.
                "intro z",
                "intro i",
                "intro a",
                "intro d",
                "intro hlookup_a",
                "intro hlookup_d",
                "specialize hlookup_induction i",
                "specialize hlookup_induction z",
                "specialize hlookup_induction a",
                "specialize hlookup_induction d",
                "apply hlookup_induction",
                "exact hlookup_a",
                "exact hlookup_d",
            ),
            "Outer-head lookup returns at most one exact-D06 head at each "
            "represented code and index.",
        ),
    )


__all__ = ["make_ha_cell_list_lookup_functional_candidate_theorems"]
