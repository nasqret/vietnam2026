"""Private K3B history-witness independence for outer-head lookup.

The sole row transports a selected exact-D06 edge between two beta histories
of the same terminal code and length.  Raw beta codes are never equated: both
histories produce client-level ``ListAt`` witnesses, whose decoded heads are
identified by lookup functionality.  Every authoring relation expands into
the unchanged first-order Peano language before parsing.  The candidate is
dependency-curried, unregistered, and unadmitted; this module makes no
empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import beta_at, cell_history
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(
            character.isalnum() or character in "_'"
            for character in value[1:]
        )
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _history_at(
    length: str,
    trace_code: str,
    trace_scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand RFC D01 ``HistoryAt(length;code,scale;index,value)``."""

    variables = tuple(
        _identifier(item, label)
        for item, label in (
            (length, "history length"),
            (trace_code, "trace code"),
            (trace_scale, "trace scale"),
            (index, "outer-head index"),
            (value, "selected head"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    edge = f"hclookhist_edge_{safe_tag}"
    tail = f"hclookhist_tail_{safe_tag}"
    successor = f"hclookhist_successor_{safe_tag}"
    binders = (edge, tail, successor)
    if len(set(binders)) != len(binders) or set(binders) & set(variables):
        raise ValueError("generated history-lookup binder captures an argument")

    current = beta_at(
        trace_code,
        trace_scale,
        edge,
        tail,
        tag=f"{safe_tag}_current",
    )
    following_placeholder = f"hclookhist_following_index_{safe_tag}"
    following = beta_at(
        trace_code,
        trace_scale,
        following_placeholder,
        successor,
        tag=f"{safe_tag}_following",
    )
    occurrences = following.count(following_placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    following = following.replace(following_placeholder, f"S {edge}")
    return (
        f"exists {edge} {tail} {successor}. "
        f"({edge} + S {index} = {length} /\\ "
        f"(({current}) /\\ (({following}) /\\ "
        f"({cell(successor, value, tail)}))))"
    )


def _beta_at_successor(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,S index,value)`` safely."""

    placeholder = "hclookhist_successor_index_argument"
    expanded = beta_at(code, scale, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    return expanded.replace(placeholder, f"S {index}")


def make_ha_cell_list_lookup_history_independent_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_history_independent`` candidate row."""

    first_history = cell_history(
        "z", "l", "b", "c", tag="history_independent_first_history"
    )
    second_history = cell_history(
        "z", "l", "d", "e", tag="history_independent_second_history"
    )
    first_at = _history_at(
        "l", "b", "c", "i", "a", tag="history_independent_first_at"
    )
    second_at = _history_at(
        "l", "d", "e", "i", "a", tag="history_independent_second_at"
    )

    first_lookup = cell_list_at(
        "z", "i", "a", tag="history_independent_first_lookup"
    )
    second_edge_current = beta_at(
        "d", "e", "x", "t", tag="history_independent_second_current"
    )
    second_edge_following = _beta_at_successor(
        "d",
        "e",
        "x",
        "u",
        tag="history_independent_second_following",
    )
    second_edge = (
        f"exists t u h. (({second_edge_current}) /\\ "
        f"(({second_edge_following}) /\\ ({cell('u', 'h', 't')})))"
    )
    selected_second_at = _history_at(
        "l", "d", "e", "i", "x5", tag="history_independent_selected_at"
    )
    second_lookup = cell_list_at(
        "z", "i", "x5", tag="history_independent_second_lookup"
    )

    return (
        spec(
            "list_at_history_independent",
            "forall z l b c d e i a. "
            f"({first_history}) -> ({second_history}) -> "
            f"({first_at}) -> ({second_at})",
            (
                "list_at_functional",
                "add_comm",
            ),
            (
                "intro z",
                "intro l",
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro i",
                "intro a",
                "intro hhistory_first",
                "intro hhistory_second",
                "intro hfirst_at",
                "cases hfirst_at",
                "cases hfirst_at_witness",
                "cases hfirst_at_witness_witness",
                "cases hfirst_at_witness_witness_witness",
                "cases hfirst_at_witness_witness_witness_right",
                "cases hfirst_at_witness_witness_witness_right_right",
                f"have hlookup_first : {first_lookup}",
                "exists l",
                "exists b",
                "exists c",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hhistory_first",
                "split",
                "exact hfirst_at_witness_witness_witness_left",
                "split",
                "exact hfirst_at_witness_witness_witness_right_left",
                "split",
                "exact hfirst_at_witness_witness_witness_right_right_left",
                "exact hfirst_at_witness_witness_witness_right_right_right",
                "have hedge_bound : exists gap. gap + S x = l",
                "exists i",
                "trans x + S i",
                "rewrite PA4",
                "rewrite PA4",
                "congr",
                "specialize add_comm i",
                "specialize add_comm x",
                "exact add_comm",
                "exact hfirst_at_witness_witness_witness_left",
                f"have hsecond_edge : {second_edge}",
                "cases hhistory_second",
                "cases hhistory_second_right",
                "specialize hhistory_second_right_right x",
                "apply hhistory_second_right_right",
                "exact hedge_bound",
                "cases hsecond_edge",
                "cases hsecond_edge_witness",
                "cases hsecond_edge_witness_witness",
                "cases hsecond_edge_witness_witness_witness",
                "cases hsecond_edge_witness_witness_witness_right",
                f"have hselected_second_at : {selected_second_at}",
                "exists x",
                "exists x3",
                "exists x4",
                "split",
                "exact hfirst_at_witness_witness_witness_left",
                "split",
                "exact hsecond_edge_witness_witness_witness_left",
                "split",
                "exact hsecond_edge_witness_witness_witness_right_left",
                "exact hsecond_edge_witness_witness_witness_right_right",
                f"have hlookup_second : {second_lookup}",
                "exists l",
                "exists d",
                "exists e",
                "exists x",
                "exists x3",
                "exists x4",
                "split",
                "exact hhistory_second",
                "split",
                "exact hfirst_at_witness_witness_witness_left",
                "split",
                "exact hsecond_edge_witness_witness_witness_left",
                "split",
                "exact hsecond_edge_witness_witness_witness_right_left",
                "exact hsecond_edge_witness_witness_witness_right_right",
                "have hvalue : a = x5",
                "specialize list_at_functional z",
                "specialize list_at_functional i",
                "specialize list_at_functional a",
                "specialize list_at_functional x5",
                "apply list_at_functional",
                "exact hlookup_first",
                "exact hlookup_second",
                "rewrite hvalue",
                "rewrite hvalue",
                "exact hselected_second_at",
            ),
            "Selected exact-D06 heads are independent of the beta witnesses "
            "used to encode one reverse history.",
        ),
    )


__all__ = [
    "make_ha_cell_list_lookup_history_independent_candidate_theorems",
]
