"""Private K3B successor equation for outer-head ``ListAt``.

The sole row shifts a positive outer-head lookup through one exact D06 cell.
All authoring relations expand into the unchanged first-order Peano language
before parsing.  The candidate is dependency-curried, unregistered, and
unadmitted; this module makes no empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import (
    beta_at,
    cell_history,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _successor_lookup(
    code: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``ListAt(code,S index,value)`` using a fresh placeholder."""

    placeholder = "hclooksucc_successor_index_argument"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    return expanded.replace(placeholder, f"S {index}")


def _history_at_length_term(
    code: str,
    length_term: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand a history whose length is a non-identifier PA term."""

    placeholder = "hclooksucc_length_term_argument"
    expanded = cell_history(
        code,
        placeholder,
        trace_code,
        trace_scale,
        tag=tag,
    )
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("history-length placeholder disappeared")
    return expanded.replace(placeholder, f"({length_term})")


def _successor_history(
    code: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand ``CellHistory(code,S length;trace_code,trace_scale)`` safely."""

    return _history_at_length_term(
        code,
        f"S {length}",
        trace_code,
        trace_scale,
        tag=tag,
    )


def make_ha_cell_list_lookup_succ_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_succ_iff`` candidate row."""

    lookup_source = _successor_lookup("z", "i", "a", tag="succ_source")
    lookup_target = _successor_lookup("z", "i", "a", tag="succ_target")
    tail_lookup_target = cell_list_at(
        "t", "i", "a", tag="succ_tail_target"
    )
    tail_lookup_source = cell_list_at(
        "t", "i", "a", tag="succ_tail_source"
    )
    tail_lookup_local = cell_list_at(
        "x", "i", "a", tag="succ_tail_local"
    )
    exact_cell = cell("z", "h", "t")

    # Forward local result after unpacking ListAt witnesses as
    # x=L, x1=b, x2=c, x3=j, x4=r, x5=s.
    eliminated = (
        f"exists t0 h0. (({cell('z', 'h0', 't0')}) /\\ "
        f"({_history_at_length_term('t0', 'x3 + S i', 'x1', 'x2', tag='succ_eliminated')}))"
    )

    # Reverse local extension after unpacking the outer cell as t=x,h=x1 and
    # the tail lookup as L=x2,b=x3,c=x4,j=x5,r=x6,s=x7.
    extended_history = _successor_history(
        "z", "x2", "b2", "c2", tag="succ_extended_history"
    )
    preserved_old = beta_at(
        "x3", "x4", "k", "v", tag="succ_preserved_old"
    )
    preserved_new = beta_at(
        "b2", "c2", "k", "v", tag="succ_preserved_new"
    )
    extension = (
        f"exists b2 c2. (({extended_history}) /\\ forall k v. "
        f"(exists d. d + k = x2) -> ({preserved_old}) -> "
        f"({preserved_new}))"
    )

    return (
        spec(
            "list_at_succ_iff",
            "forall z i a. "
            f"((({lookup_source}) -> exists t h. "
            f"(({exact_cell}) /\\ ({tail_lookup_target}))) /\\ "
            f"((exists t h. (({exact_cell}) /\\ "
            f"({tail_lookup_source}))) -> ({lookup_target})))",
            (
                "cell_history_succ_elim",
                "cell_history_extend_preserves_prefix",
                "add_comm",
            ),
            (
                "intro z",
                "intro i",
                "intro a",
                "split",
                # ListAt(z,S i,a) -> expose z's outer cell and tail lookup.
                "intro hlookup",
                "cases hlookup",
                "cases hlookup_witness",
                "cases hlookup_witness_witness",
                "cases hlookup_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness_witness_right",
                "cases hlookup_witness_witness_witness_witness_witness_witness_right_right",
                "cases hlookup_witness_witness_witness_witness_witness_witness_right_right_right",
                "rewrite PA4 at hlookup_witness_witness_witness_witness_witness_witness_right_left",
                "have hlength : x = S (x3 + S i)",
                "symm",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                f"have hdecomp : {eliminated}",
                "specialize cell_history_succ_elim x1",
                "specialize cell_history_succ_elim x2",
                "specialize cell_history_succ_elim (x3 + S i)",
                "specialize cell_history_succ_elim z",
                "apply cell_history_succ_elim",
                "exact hlookup_witness_witness_witness_witness_witness_witness_left",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "exists x6",
                "exists x7",
                "split",
                "exact hdecomp_witness_witness_left",
                "exists (x3 + S i)",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "split",
                "exact hdecomp_witness_witness_right",
                "split",
                "refl",
                "split",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_right_left",
                "split",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_right_right_left",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                # One outer cell over ListAt(t,i,a) -> ListAt(z,S i,a).
                "intro hstep",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                f"have htail_lookup : {tail_lookup_local}",
                "exact hstep_witness_witness_right",
                "cases htail_lookup",
                "cases htail_lookup_witness",
                "cases htail_lookup_witness_witness",
                "cases htail_lookup_witness_witness_witness",
                "cases htail_lookup_witness_witness_witness_witness",
                "cases htail_lookup_witness_witness_witness_witness_witness",
                "cases htail_lookup_witness_witness_witness_witness_witness_witness",
                "cases htail_lookup_witness_witness_witness_witness_witness_witness_right",
                "cases htail_lookup_witness_witness_witness_witness_witness_witness_right_right",
                "cases htail_lookup_witness_witness_witness_witness_witness_witness_right_right_right",
                f"have hextension : {extension}",
                "specialize cell_history_extend_preserves_prefix x3",
                "specialize cell_history_extend_preserves_prefix x4",
                "specialize cell_history_extend_preserves_prefix x2",
                "specialize cell_history_extend_preserves_prefix x",
                "specialize cell_history_extend_preserves_prefix z",
                "specialize cell_history_extend_preserves_prefix x1",
                "apply cell_history_extend_preserves_prefix",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_left",
                "exact hstep_witness_witness_left",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "have htarget_index : x5 + S (S i) = S x2",
                "rewrite PA4",
                "congr",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_left",
                "have hcurrent_bound : exists d. d + x5 = x2",
                "exists S i",
                "trans x5 + S i",
                "specialize add_comm (S i)",
                "specialize add_comm x5",
                "exact add_comm",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_left",
                "have hfollowing_bound : exists d. d + S x5 = x2",
                "exists i",
                "trans x5 + S i",
                "rewrite PA4",
                "rewrite PA4",
                "congr",
                "specialize add_comm i",
                "specialize add_comm x5",
                "exact add_comm",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_left",
                "exists S x2",
                "exists x8",
                "exists x9",
                "exists x5",
                "exists x6",
                "exists x7",
                "split",
                "exact hextension_witness_witness_left",
                "split",
                "exact htarget_index",
                "split",
                "specialize hextension_witness_witness_right x5",
                "specialize hextension_witness_witness_right x6",
                "apply hextension_witness_witness_right",
                "exact hcurrent_bound",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_right_left",
                "split",
                "specialize hextension_witness_witness_right (S x5)",
                "specialize hextension_witness_witness_right x7",
                "apply hextension_witness_witness_right",
                "exact hfollowing_bound",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_right_right_left",
                "exact htail_lookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
            ),
            "Lookup at a successor outer index is exactly lookup at the "
            "preceding index in the tail of one exact D06 outer cell.",
        ),
    )


__all__ = ["make_ha_cell_list_lookup_succ_candidate_theorems"]
