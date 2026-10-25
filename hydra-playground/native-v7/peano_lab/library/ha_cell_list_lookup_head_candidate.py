"""Private K3B head equation for outer-head ``ListAt``.

The sole row characterizes lookup at index zero by one exact D06 outer cell
whose tail has a beta-backed cell-list length.  All displayed relations are
authoring helpers only and expand into the unchanged first-order Peano
language before parsing.  The candidate is dependency-curried, unregistered,
and unadmitted; this module makes no empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import (
    beta_at,
    cell_history,
    cell_list_len,
)
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _zero_lookup(code: str, value: str, *, tag: str) -> str:
    """Expand ``ListAt(code,0,value)`` through an identifier placeholder."""

    placeholder = "hclookhead_zero_index_argument"
    expanded = cell_list_at(code, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("zero-index placeholder disappeared")
    return expanded.replace(placeholder, "0")


def _successor_history(
    code: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand ``CellHistory(code,S length;trace_code,trace_scale)`` safely."""

    placeholder = "hclookhead_successor_length_argument"
    expanded = cell_history(
        code,
        placeholder,
        trace_code,
        trace_scale,
        tag=tag,
    )
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-length placeholder disappeared")
    return expanded.replace(placeholder, f"S {length}")


def make_ha_cell_list_lookup_head_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_head_iff`` candidate row."""

    lookup_source = _zero_lookup("z", "a", tag="head_source")
    lookup_target = _zero_lookup("z", "a", tag="head_target")
    exact_cell = cell("z", "a", "t")
    source_tail_length = cell_list_len(
        "t", "l", tag="head_source_tail_length"
    )
    target_tail_length = cell_list_len(
        "t", "l", tag="head_target_tail_length"
    )

    # Forward-direction local formulas after unpacking the normative ListAt
    # witnesses as x=l, x1=b, x2=c, x3=j, x4=t, x5=u.
    eliminated = (
        f"exists t0 h0. (({cell('z', 'h0', 't0')}) /\\ "
        f"({cell_history('t0', 'x3', 'x1', 'x2', tag='head_eliminated')}))"
    )
    history_terminal_placeholder = "hclookhead_terminal_index_argument"
    history_terminal = beta_at(
        "x1",
        "x2",
        history_terminal_placeholder,
        "z",
        tag="head_history_terminal",
    ).replace(history_terminal_placeholder, "S x3")
    eliminated_terminal = beta_at(
        "x1", "x2", "x3", "x6", tag="head_eliminated_terminal"
    )

    # Reverse-direction local formulas after unpacking t=x, l=x1, b=x2,
    # c=x3.  The strengthened extension returns b2=x4 and c2=x5.
    old_history = cell_history(
        "x", "x1", "x2", "x3", tag="head_old_history"
    )
    old_terminal = beta_at(
        "x2", "x3", "x1", "x", tag="head_old_terminal"
    )
    extended_history = _successor_history(
        "z", "x1", "b2", "c2", tag="head_extended_history"
    )
    preserved_old = beta_at(
        "x2", "x3", "k", "v", tag="head_preserved_old"
    )
    preserved_new = beta_at(
        "b2", "c2", "k", "v", tag="head_preserved_new"
    )
    extension = (
        f"exists b2 c2. (({extended_history}) /\\ forall k v. "
        f"(exists d. d + k = x1) -> ({preserved_old}) -> "
        f"({preserved_new}))"
    )

    return (
        spec(
            "list_at_head_iff",
            "forall z a. "
            f"((({lookup_source}) -> exists t l. "
            f"(({exact_cell}) /\\ ({source_tail_length}))) /\\ "
            f"((exists t l. (({exact_cell}) /\\ "
            f"({target_tail_length}))) -> ({lookup_target})))",
            (
                "cell_history_succ_elim",
                "cell_history_extend_preserves_prefix",
                "beta_at_unique",
                "le_refl",
            ),
            (
                "intro z",
                "intro a",
                "split",
                # ListAt(z,0,a) -> one outer cell over a represented tail.
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
                "rewrite PA3 at hlookup_witness_witness_witness_witness_witness_witness_right_left",
                "have hlength : x = S x3",
                "symm",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                "rewrite hlength at hlookup_witness_witness_witness_witness_witness_witness_left",
                f"have hdecomp : {eliminated}",
                "specialize cell_history_succ_elim x1",
                "specialize cell_history_succ_elim x2",
                "specialize cell_history_succ_elim x3",
                "specialize cell_history_succ_elim z",
                "apply cell_history_succ_elim",
                "exact hlookup_witness_witness_witness_witness_witness_witness_left",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                f"have hterminal : {history_terminal}",
                "cases hlookup_witness_witness_witness_witness_witness_witness_left",
                "cases hlookup_witness_witness_witness_witness_witness_witness_left_right",
                "exact hlookup_witness_witness_witness_witness_witness_witness_left_right_left",
                "have hcode : x5 = z",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique (S x3)",
                "specialize beta_at_unique x5",
                "specialize beta_at_unique z",
                "apply beta_at_unique",
                f"exact hlookup_witness_witness_witness_witness_witness_witness_right_right_right_left",
                "exact hterminal",
                "rewrite hcode at hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                f"have heliminated_terminal : {eliminated_terminal}",
                "cases hdecomp_witness_witness_right",
                "cases hdecomp_witness_witness_right_right",
                "exact hdecomp_witness_witness_right_right_left",
                "have htail : x4 = x6",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique x2",
                "specialize beta_at_unique x3",
                "specialize beta_at_unique x4",
                "specialize beta_at_unique x6",
                "apply beta_at_unique",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_right_left",
                "exact heliminated_terminal",
                "rewrite htail at hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "rewrite htail at hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "rewrite htail at hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "rewrite htail at hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "exists x6",
                "exists x3",
                "split",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_right_right_right",
                "exists x1",
                "exists x2",
                "exact hdecomp_witness_witness_right",
                # One outer cell over a represented tail -> ListAt(z,0,a).
                "intro hstep",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_right",
                "cases hstep_witness_witness_right_witness",
                f"have hold_history : {old_history}",
                "exact hstep_witness_witness_right_witness_witness",
                f"have hold_terminal : {old_terminal}",
                "cases hold_history",
                "cases hold_history_right",
                "exact hold_history_right_left",
                f"have hextension : {extension}",
                "specialize cell_history_extend_preserves_prefix x2",
                "specialize cell_history_extend_preserves_prefix x3",
                "specialize cell_history_extend_preserves_prefix x1",
                "specialize cell_history_extend_preserves_prefix x",
                "specialize cell_history_extend_preserves_prefix z",
                "specialize cell_history_extend_preserves_prefix a",
                "apply cell_history_extend_preserves_prefix",
                "exact hold_history",
                "exact hstep_witness_witness_left",
                "cases hextension",
                "cases hextension_witness",
                "cases hextension_witness_witness",
                "exists S x1",
                "exists x4",
                "exists x5",
                "exists x1",
                "exists x",
                "exists z",
                "split",
                "exact hextension_witness_witness_left",
                "split",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                "split",
                "specialize hextension_witness_witness_right x1",
                "specialize hextension_witness_witness_right x",
                "apply hextension_witness_witness_right",
                "specialize le_refl x1",
                "exact le_refl",
                "exact hold_terminal",
                "split",
                "cases hextension_witness_witness_left",
                "cases hextension_witness_witness_left_right",
                "exact hextension_witness_witness_left_right_left",
                "exact hstep_witness_witness_left",
            ),
            "Lookup at outer index zero is exactly the head of one exact D06 "
            "cell whose tail has a represented cell-list length.",
        ),
    )


__all__ = ["make_ha_cell_list_lookup_head_candidate_theorems"]
