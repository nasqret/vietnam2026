"""Private K3B functionality of beta-backed exact-D06 list length.

``CellListLen`` is only an authoring abbreviation: every occurrence in the
statement and in the induction motive is expanded to the unchanged
first-order Peano language before parsing.  The sole row is
dependency-curried, unregistered, and unadmitted.  Its proof is constructive
and performs ordinary object-level induction on the first displayed length.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def make_ha_cell_list_length_functional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact functional-length row from the two list equations."""

    target_left = cell_list_len("z", "l", tag="functional_target_left")
    target_right = cell_list_len("z", "m", tag="functional_target_right")

    induction_left = cell_list_len(
        "z", "l", tag="functional_induction_left"
    )
    induction_right = cell_list_len(
        "z", "m", tag="functional_induction_right"
    )
    induction_motive = (
        "forall l z m. "
        f"({induction_left}) -> ({induction_right}) -> l = m"
    )

    base_successor_tail = cell_list_len(
        "t", "x", tag="functional_base_successor_tail"
    )
    base_successor_decomposition = (
        "exists t h. "
        f"(({cell('z', 'h', 't')}) /\\ ({base_successor_tail}))"
    )

    step_first_tail = cell_list_len(
        "t", "l", tag="functional_step_first_tail"
    )
    step_first_decomposition = (
        "exists t h. "
        f"(({cell('z', 'h', 't')}) /\\ ({step_first_tail}))"
    )
    step_second_tail = cell_list_len(
        "t", "x", tag="functional_step_second_tail"
    )
    step_second_decomposition = (
        "exists t h. "
        f"(({cell('z', 'h', 't')}) /\\ ({step_second_tail}))"
    )

    return (
        spec(
            "cell_list_length_functional",
            "forall z l m. "
            f"({target_left}) -> ({target_right}) -> l = m",
            (
                "cell_list_zero_iff_nil",
                "cell_list_succ_iff_cell",
                "nil_not_cell",
                "cell_tail_functional",
                "zero_or_succ",
            ),
            (
                f"have hlength_induction : {induction_motive}",
                "intro l",
                "induction l",
                # Base length: split the second length constructively.
                "intro z",
                "intro m",
                "intro hleft",
                "intro hright",
                "specialize zero_or_succ m",
                "cases zero_or_succ",
                "rewrite zero_or_succ_left",
                "refl",
                "cases zero_or_succ_right",
                "rewrite zero_or_succ_right_witness at hright",
                "rewrite zero_or_succ_right_witness at hright",
                "rewrite zero_or_succ_right_witness at hright",
                "specialize cell_list_zero_iff_nil z",
                "cases cell_list_zero_iff_nil",
                "have hnil : z = 0",
                "apply cell_list_zero_iff_nil_left",
                "exact hleft",
                f"have hbase_cell : {base_successor_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell x",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hright",
                "cases hbase_cell",
                "cases hbase_cell_witness",
                "cases hbase_cell_witness_witness",
                "exfalso",
                "specialize nil_not_cell z",
                "specialize nil_not_cell x2",
                "specialize nil_not_cell x1",
                "apply nil_not_cell",
                "exact hnil",
                "exact hbase_cell_witness_witness_left",
                # Successor length: split the second length again.
                "intro z",
                "intro m",
                "intro hleft",
                "intro hright",
                "specialize zero_or_succ m",
                "cases zero_or_succ",
                "rewrite zero_or_succ_left at hright",
                "rewrite zero_or_succ_left at hright",
                "rewrite zero_or_succ_left at hright",
                "specialize cell_list_zero_iff_nil z",
                "cases cell_list_zero_iff_nil",
                "have hnil : z = 0",
                "apply cell_list_zero_iff_nil_left",
                "exact hright",
                f"have hfirst_cell : {step_first_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hleft",
                "cases hfirst_cell",
                "cases hfirst_cell_witness",
                "cases hfirst_cell_witness_witness",
                "exfalso",
                "specialize nil_not_cell z",
                "specialize nil_not_cell x1",
                "specialize nil_not_cell x",
                "apply nil_not_cell",
                "exact hnil",
                "exact hfirst_cell_witness_witness_left",
                "cases zero_or_succ_right",
                "rewrite zero_or_succ_right_witness at hright",
                "rewrite zero_or_succ_right_witness at hright",
                "rewrite zero_or_succ_right_witness at hright",
                f"have hfirst_cell : {step_first_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hleft",
                "cases hfirst_cell",
                "cases hfirst_cell_witness",
                "cases hfirst_cell_witness_witness",
                f"have hsecond_cell : {step_second_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell x",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hright",
                "cases hsecond_cell",
                "cases hsecond_cell_witness",
                "cases hsecond_cell_witness_witness",
                "have htail : x1 = x3",
                "specialize cell_tail_functional z",
                "specialize cell_tail_functional x2",
                "specialize cell_tail_functional x1",
                "specialize cell_tail_functional x4",
                "specialize cell_tail_functional x3",
                "apply cell_tail_functional",
                "exact hfirst_cell_witness_witness_left",
                "exact hsecond_cell_witness_witness_left",
                "rewrite htail at hfirst_cell_witness_witness_right",
                "rewrite htail at hfirst_cell_witness_witness_right",
                "have hpredecessors : l = x",
                "specialize IH x3",
                "specialize IH x",
                "apply IH",
                "exact hfirst_cell_witness_witness_right",
                "exact hsecond_cell_witness_witness_right",
                "rewrite zero_or_succ_right_witness",
                "congr",
                "exact hpredecessors",
                # Reorder the generalized induction result to the RFC surface.
                "intro z",
                "intro l",
                "intro m",
                "intro hleft",
                "intro hright",
                "specialize hlength_induction l",
                "specialize hlength_induction z",
                "specialize hlength_induction m",
                "apply hlength_induction",
                "exact hleft",
                "exact hright",
            ),
            "A beta-backed exact-D06 cell code has at most one represented "
            "length, constructively.",
        ),
    )


__all__ = ["make_ha_cell_list_length_functional_candidate_theorems"]
