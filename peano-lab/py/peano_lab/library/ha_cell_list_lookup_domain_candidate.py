"""Private K3B domain projection for outer-head ``ListAt``.

The sole row eliminates the hidden history witnesses of the frozen lookup
surface and repackages its length as ``CellListLen`` together with the native
strict-bound witness.  It uses no theorem dependency and adds no predicate to
the object language.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_cell_list_lookup_surface_candidate import cell_list_at


def make_ha_cell_list_lookup_domain_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact lookup-domain projection row."""

    lookup = cell_list_at("z", "i", "a", tag="domain_lookup")
    represented_length = cell_list_len("z", "l", tag="domain_length")

    return (
        spec(
            "list_at_domain",
            "forall z i a. "
            f"({lookup}) -> exists l. (({represented_length}) /\\ "
            "exists k. k + S i = l)",
            (),
            (
                "intro z",
                "intro i",
                "intro a",
                "intro hlookup",
                "cases hlookup",
                "cases hlookup_witness",
                "cases hlookup_witness_witness",
                "cases hlookup_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness_witness",
                "cases hlookup_witness_witness_witness_witness_witness_witness_right",
                "exists x",
                "split",
                "exists x1",
                "exists x2",
                "exact hlookup_witness_witness_witness_witness_witness_witness_left",
                "exists x3",
                "exact hlookup_witness_witness_witness_witness_witness_witness_right_left",
            ),
            "Every represented lookup exposes a semantic list length and its "
            "native strict index bound.",
        ),
    )


__all__ = ["make_ha_cell_list_lookup_domain_candidate_theorems"]
