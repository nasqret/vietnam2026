"""Private K3B extensionality of beta-backed exact-D06 cell lists.

The sole row proves equality of equal-length cell-list codes from relational
pointwise equality of all in-range outer-head lookups.  The proof is by
induction on the shared length and uses only the zero/successor equations for
length and lookup.  Every authoring relation expands into the unchanged
first-order Peano language before parsing.  The candidate is
dependency-curried, unregistered, and unadmitted; this module makes no
empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _zero_lookup(code: str, value: str, *, tag: str) -> str:
    """Expand ``ListAt(code,0,value)`` safely."""

    placeholder = "hclistext_zero_index_argument"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("zero-index placeholder disappeared")
    return expanded.replace(placeholder, "0")


def _successor_lookup(
    code: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``ListAt(code,S index,value)`` safely."""

    placeholder = "hclistext_successor_index_argument"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    return expanded.replace(placeholder, f"S {index}")


def _pointwise(
    length: str,
    left_code: str,
    right_code: str,
    index: str,
    left_value: str,
    right_value: str,
    *,
    tag: str,
) -> str:
    """Expand the relational pointwise-equality hypothesis hygienically."""

    left_lookup = cell_list_at(
        left_code,
        index,
        left_value,
        tag=f"{tag}_left",
    )
    right_lookup = cell_list_at(
        right_code,
        index,
        right_value,
        tag=f"{tag}_right",
    )
    return (
        f"forall {index} {left_value} {right_value}. "
        f"(exists k. k + S {index} = {length}) -> "
        f"({left_lookup}) -> ({right_lookup}) -> "
        f"{left_value} = {right_value}"
    )


def make_ha_cell_list_extensional_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``cell_list_extensional`` candidate row."""

    target_left_length = cell_list_len(
        "z", "l", tag="extensional_target_left_length"
    )
    target_right_length = cell_list_len(
        "w", "l", tag="extensional_target_right_length"
    )
    target_pointwise = _pointwise(
        "l", "z", "w", "i", "a", "d", tag="extensional_target"
    )

    induction_left_length = cell_list_len(
        "z", "l", tag="extensional_induction_left_length"
    )
    induction_right_length = cell_list_len(
        "w", "l", tag="extensional_induction_right_length"
    )
    induction_pointwise = _pointwise(
        "l",
        "z",
        "w",
        "i",
        "a",
        "d",
        tag="extensional_induction",
    )
    induction_motive = (
        "forall l z w. "
        f"({induction_left_length}) -> ({induction_right_length}) -> "
        f"({induction_pointwise}) -> z = w"
    )

    left_decomposition = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='extensional_left_tail')}))"
    )
    right_decomposition = (
        f"exists t h. (({cell('w', 'h', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='extensional_right_tail')}))"
    )
    left_head_lookup = _zero_lookup(
        "z", "x1", tag="extensional_left_head_lookup"
    )
    right_head_lookup = _zero_lookup(
        "w", "x3", tag="extensional_right_head_lookup"
    )
    tail_pointwise = _pointwise(
        "l", "x", "x2", "j", "p", "q", tag="extensional_tail"
    )
    lifted_left_lookup = _successor_lookup(
        "z", "j", "p", tag="extensional_lifted_left"
    )
    lifted_right_lookup = _successor_lookup(
        "w", "j", "q", tag="extensional_lifted_right"
    )
    normalized_left_cell = cell("z", "x3", "x2")
    common_cell_term = (
        "S ((x3 + x2) * S (x3 + x2) + (x2 + x2))"
    )

    return (
        spec(
            "cell_list_extensional",
            "forall z w l. "
            f"({target_left_length}) -> ({target_right_length}) -> "
            f"({target_pointwise}) -> z = w",
            (
                "cell_list_zero_iff_nil",
                "cell_list_succ_iff_cell",
                "list_at_head_iff",
                "list_at_succ_iff",
            ),
            (
                f"have hextensional_induction : {induction_motive}",
                "intro l",
                "induction l",
                # Length zero: both codes are nil.
                "intro z",
                "intro w",
                "intro hlength_z",
                "intro hlength_w",
                "intro hpointwise",
                "have hz_zero : z = 0",
                "specialize cell_list_zero_iff_nil z",
                "cases cell_list_zero_iff_nil",
                "apply cell_list_zero_iff_nil_left",
                "exact hlength_z",
                "have hw_zero : w = 0",
                "specialize cell_list_zero_iff_nil w",
                "cases cell_list_zero_iff_nil",
                "apply cell_list_zero_iff_nil_left",
                "exact hlength_w",
                "trans 0",
                "exact hz_zero",
                "symm",
                "exact hw_zero",
                # Successor length: compare heads and recurse on tails.
                "intro z",
                "intro w",
                "intro hlength_z",
                "intro hlength_w",
                "intro hpointwise",
                f"have hz_decomp : {left_decomposition}",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hlength_z",
                f"have hw_decomp : {right_decomposition}",
                "specialize cell_list_succ_iff_cell w",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                "apply cell_list_succ_iff_cell_left",
                "exact hlength_w",
                "cases hz_decomp",
                "cases hz_decomp_witness",
                "cases hz_decomp_witness_witness",
                "cases hw_decomp",
                "cases hw_decomp_witness",
                "cases hw_decomp_witness_witness",
                "have hhead_bound : exists k. k + S 0 = S l",
                "exists l",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                f"have hhead_lookup_z : {left_head_lookup}",
                "specialize list_at_head_iff z",
                "specialize list_at_head_iff x1",
                "cases list_at_head_iff",
                "apply list_at_head_iff_right",
                "exists x",
                "exists l",
                "split",
                "exact hz_decomp_witness_witness_left",
                "exact hz_decomp_witness_witness_right",
                f"have hhead_lookup_w : {right_head_lookup}",
                "specialize list_at_head_iff w",
                "specialize list_at_head_iff x3",
                "cases list_at_head_iff",
                "apply list_at_head_iff_right",
                "exists x2",
                "exists l",
                "split",
                "exact hw_decomp_witness_witness_left",
                "exact hw_decomp_witness_witness_right",
                "have hheads : x1 = x3",
                "specialize hpointwise 0",
                "specialize hpointwise x1",
                "specialize hpointwise x3",
                "apply hpointwise",
                "exact hhead_bound",
                "exact hhead_lookup_z",
                "exact hhead_lookup_w",
                f"have htail_pointwise : {tail_pointwise}",
                "intro j",
                "intro p",
                "intro q",
                "intro hbound",
                "intro hlookup_z",
                "intro hlookup_w",
                f"have hlifted_z : {lifted_left_lookup}",
                "specialize list_at_succ_iff z",
                "specialize list_at_succ_iff j",
                "specialize list_at_succ_iff p",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_right",
                "exists x",
                "exists x1",
                "split",
                "exact hz_decomp_witness_witness_left",
                "exact hlookup_z",
                f"have hlifted_w : {lifted_right_lookup}",
                "specialize list_at_succ_iff w",
                "specialize list_at_succ_iff j",
                "specialize list_at_succ_iff q",
                "cases list_at_succ_iff",
                "apply list_at_succ_iff_right",
                "exists x2",
                "exists x3",
                "split",
                "exact hw_decomp_witness_witness_left",
                "exact hlookup_w",
                "cases hbound",
                "have hlifted_bound : exists k. k + S (S j) = S l",
                "exists x4",
                "rewrite PA4",
                "congr",
                "exact hbound_witness",
                "specialize hpointwise (S j)",
                "specialize hpointwise p",
                "specialize hpointwise q",
                "apply hpointwise",
                "exact hlifted_bound",
                "exact hlifted_z",
                "exact hlifted_w",
                "have htails : x = x2",
                "specialize IH x",
                "specialize IH x2",
                "apply IH",
                "exact hz_decomp_witness_witness_right",
                "exact hw_decomp_witness_witness_right",
                "exact htail_pointwise",
                f"have hnormalized_z : {normalized_left_cell}",
                "rewrite hheads at hz_decomp_witness_witness_left",
                "rewrite hheads at hz_decomp_witness_witness_left",
                "rewrite htails at hz_decomp_witness_witness_left",
                "rewrite htails at hz_decomp_witness_witness_left",
                "rewrite htails at hz_decomp_witness_witness_left",
                "rewrite htails at hz_decomp_witness_witness_left",
                "exact hz_decomp_witness_witness_left",
                f"trans {common_cell_term}",
                "exact hnormalized_z",
                "symm",
                "exact hw_decomp_witness_witness_left",
                # Reorder the generalized induction theorem to the RFC surface.
                "intro z",
                "intro w",
                "intro l",
                "intro hlength_z",
                "intro hlength_w",
                "intro hpointwise",
                "specialize hextensional_induction l",
                "specialize hextensional_induction z",
                "specialize hextensional_induction w",
                "apply hextensional_induction",
                "exact hlength_z",
                "exact hlength_w",
                "exact hpointwise",
            ),
            "Equal-length exact-D06 cell lists are equal when all in-range "
            "outer-head lookups agree relationally.",
        ),
    )


__all__ = ["make_ha_cell_list_extensional_candidate_theorems"]
