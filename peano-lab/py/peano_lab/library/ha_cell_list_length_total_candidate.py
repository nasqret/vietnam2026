"""Private K3B totality of beta-backed exact-D06 cell-list lengths.

This module contains RFC deliverable 10 only.  ``CellListLen`` is an
authoring abbreviation: the theorem statement is expanded completely to the
unchanged first-order Peano language before it reaches the parser.  The proof
is constructive ordinary induction.  Its base is the reviewed nil history;
its step constructs an exact D06 cell with head zero over the induction
hypothesis and appends that cell with ``cell_history_extend``.

The candidate is dependency-curried, unregistered, and unadmitted.  Its local
gate is deliberately limited to kernel checking the body with the three
declared dependencies left as ordinary hypotheses.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len


def make_ha_cell_list_length_total_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact constructive ``forall l, exists z`` candidate."""

    list_at_length = cell_list_len("z", "l", tag="length_total")

    return (
        spec(
            "cell_list_length_total",
            f"forall l. exists z. ({list_at_length})",
            (
                "cell_history_nil",
                "cell_constructor",
                "cell_history_extend",
            ),
            (
                "intro l",
                "induction l",
                "exists 0",
                "exists 0",
                "exists 0",
                "exact cell_history_nil",
                "cases IH",
                "cases IH_witness",
                "cases IH_witness_witness",
                "specialize cell_constructor 0",
                "specialize cell_constructor x",
                "cases cell_constructor",
                "exists x3",
                "specialize cell_history_extend x1",
                "specialize cell_history_extend x2",
                "specialize cell_history_extend l",
                "specialize cell_history_extend x",
                "specialize cell_history_extend x3",
                "specialize cell_history_extend 0",
                "apply cell_history_extend",
                "exact IH_witness_witness_witness",
                "exact cell_constructor_witness",
            ),
            "Every natural length is inhabited by a reverse beta history of "
            "exact D06 cells, obtained by repeatedly adjoining a zero head.",
        ),
    )


__all__ = ["make_ha_cell_list_length_total_candidate_theorems"]
