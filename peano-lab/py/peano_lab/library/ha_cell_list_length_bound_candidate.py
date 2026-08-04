"""Private K3B length bound for beta-backed exact-D06 cell lists.

The sole candidate in this module is RFC deliverable 9.  ``CellListLen`` is
only an authoring helper: its occurrence is expanded into the unchanged
first-order Peano language before parsing.  The proof is constructive and
uses object-level induction on the represented length.  It remains
dependency-curried, unregistered, and unadmitted; this module claims only a
lightweight proof-body check, not recursive empty-context closure.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import cell_list_len
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def make_ha_cell_list_length_bound_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact ``length <= code`` deliverable."""

    statement_list = cell_list_len("z", "l", tag="length_bound_statement")
    induction_list = cell_list_len("z", "l", tag="length_bound_induction")
    decomposition = (
        f"exists t h. (({cell('z', 'h', 't')}) /\\ "
        f"({cell_list_len('t', 'l', tag='length_bound_decomposition')}))"
    )

    return (
        spec(
            "cell_list_length_le_code",
            f"forall z l. ({statement_list}) -> exists k. k + l = z",
            (
                "cell_list_succ_iff_cell",
                "cell_tail_lt_code",
                "zero_le",
                "succ_le_succ",
                "le_trans",
            ),
            (
                f"have hbound : forall l z. ({induction_list}) -> "
                "exists k. k + l = z",
                "induction l",
                "intro z",
                "intro hlist",
                "specialize zero_le z",
                "exact zero_le",
                "intro z",
                "intro hlist",
                "specialize cell_list_succ_iff_cell z",
                "specialize cell_list_succ_iff_cell l",
                "cases cell_list_succ_iff_cell",
                f"have hdecomp : {decomposition}",
                "apply cell_list_succ_iff_cell_left",
                "exact hlist",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                f"have hpre : exists k. k + l = x",
                "specialize IH x",
                "apply IH",
                "exact hdecomp_witness_witness_right",
                "have hsuccpre : exists k. k + S l = S x",
                "specialize succ_le_succ l",
                "specialize succ_le_succ x",
                "apply succ_le_succ",
                "exact hpre",
                "have htail : exists k. k + S x = z",
                "specialize cell_tail_lt_code z",
                "specialize cell_tail_lt_code x1",
                "specialize cell_tail_lt_code x",
                "apply cell_tail_lt_code",
                "exact hdecomp_witness_witness_left",
                "specialize le_trans (S l)",
                "specialize le_trans (S x)",
                "specialize le_trans z",
                "apply le_trans",
                "exact hsuccpre",
                "exact htail",
                "intro z",
                "intro l",
                "specialize hbound l",
                "specialize hbound z",
                "exact hbound",
            ),
            "Every valid reverse exact-D06 cell list has length at most its "
            "terminal code.",
        ),
    )


__all__ = ["make_ha_cell_list_length_bound_candidate_theorems"]
