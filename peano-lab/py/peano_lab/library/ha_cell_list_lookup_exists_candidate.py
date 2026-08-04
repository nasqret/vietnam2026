"""Private K3B in-range existence for outer-head ``ListAt``.

The sole row obtains a selected head directly from the universal edge clause
of a beta-backed exact-D06 cell history.  Every authoring relation expands
into the unchanged first-order Peano language before parsing.  The candidate
is dependency-curried, unregistered, and unadmitted; this module makes no
empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import beta_at, cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _beta_at_successor(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
) -> str:
    """Expand ``BetaAt(code,scale,S index,value)`` safely."""

    placeholder = "hclookexists_successor_index_argument"
    expanded = beta_at(code, scale, placeholder, value, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-index placeholder disappeared")
    return expanded.replace(placeholder, f"S {index}")


def make_ha_cell_list_lookup_exists_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_exists`` candidate row."""

    represented_length = cell_list_len(
        "z", "l", tag="lookup_exists_length"
    )
    lookup = cell_list_at("z", "i", "a", tag="lookup_exists_target")

    # After unpacking CellListLen as b=x,c=x1 and the external bound as
    # j=x2, the history edge supplies tail=x3, successor=x4, and head=x5.
    edge_current = beta_at(
        "x", "x1", "x2", "t", tag="lookup_exists_edge_current"
    )
    edge_following = _beta_at_successor(
        "x",
        "x1",
        "x2",
        "u",
        tag="lookup_exists_edge_following",
    )
    edge = (
        f"exists t u h. (({edge_current}) /\\ "
        f"(({edge_following}) /\\ ({cell('u', 'h', 't')})))"
    )

    return (
        spec(
            "list_at_exists",
            "forall z l i. "
            f"({represented_length}) -> "
            "(exists k. k + S i = l) -> "
            f"exists a. ({lookup})",
            ("add_comm",),
            (
                "intro z",
                "intro l",
                "intro i",
                "intro hlength",
                "intro hbound",
                "cases hlength",
                "cases hlength_witness",
                "cases hbound",
                "have hedge_bound : exists d. d + S x2 = l",
                "exists i",
                "trans x2 + S i",
                "rewrite PA4",
                "rewrite PA4",
                "congr",
                "specialize add_comm i",
                "specialize add_comm x2",
                "exact add_comm",
                "exact hbound_witness",
                f"have hedge : {edge}",
                "cases hlength_witness_witness",
                "cases hlength_witness_witness_right",
                "specialize hlength_witness_witness_right_right x2",
                "apply hlength_witness_witness_right_right",
                "exact hedge_bound",
                "cases hedge",
                "cases hedge_witness",
                "cases hedge_witness_witness",
                "cases hedge_witness_witness_witness",
                "cases hedge_witness_witness_witness_right",
                "exists x5",
                "exists l",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "split",
                "exact hlength_witness_witness",
                "split",
                "exact hbound_witness",
                "split",
                "exact hedge_witness_witness_witness_left",
                "split",
                "exact hedge_witness_witness_witness_right_left",
                "exact hedge_witness_witness_witness_right_right",
            ),
            "Every outer-head index strictly below a represented list length "
            "has a decoded exact-D06 head.",
        ),
    )


__all__ = ["make_ha_cell_list_lookup_exists_candidate_theorems"]
