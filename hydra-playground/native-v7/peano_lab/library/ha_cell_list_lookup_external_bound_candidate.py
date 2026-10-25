"""Private K3B external-length bound for outer-head ``ListAt``.

The sole row transports the hidden length projected by ``ListAt`` to an
externally declared ``CellListLen`` witness.  Every authoring relation expands
into the unchanged first-order Peano language before parsing.  The candidate
is dependency-curried, unregistered, and unadmitted; this module makes no
empty-context closure claim.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at


def make_ha_cell_list_lookup_external_bound_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact RFC ``list_at_external_bound`` candidate row."""

    declared_length = cell_list_len(
        "z", "l", tag="external_bound_declared_length"
    )
    lookup = cell_list_at("z", "i", "a", tag="external_bound_lookup")
    projected_length = cell_list_len(
        "z", "m", tag="external_bound_projected_length"
    )
    projected_domain = (
        f"exists m. (({projected_length}) /\\ "
        "exists k. k + S i = m)"
    )

    return (
        spec(
            "list_at_external_bound",
            "forall z l i a. "
            f"({declared_length}) -> ({lookup}) -> "
            "exists k. k + S i = l",
            (
                "list_at_domain",
                "cell_list_length_functional",
            ),
            (
                "intro z",
                "intro l",
                "intro i",
                "intro a",
                "intro hlength",
                "intro hlookup",
                f"have hdomain : {projected_domain}",
                "specialize list_at_domain z",
                "specialize list_at_domain i",
                "specialize list_at_domain a",
                "apply list_at_domain",
                "exact hlookup",
                "cases hdomain",
                "cases hdomain_witness",
                "have hlength_eq : l = x",
                "specialize cell_list_length_functional z",
                "specialize cell_list_length_functional l",
                "specialize cell_list_length_functional x",
                "apply cell_list_length_functional",
                "exact hlength",
                "exact hdomain_witness_left",
                "rewrite hlength_eq",
                "exact hdomain_witness_right",
            ),
            "A lookup's hidden strict bound transports to every externally "
            "declared functional cell-list length.",
        ),
    )


__all__ = [
    "make_ha_cell_list_lookup_external_bound_candidate_theorems",
]
