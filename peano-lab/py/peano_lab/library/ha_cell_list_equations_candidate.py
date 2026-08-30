"""Private K3B equations for beta-backed exact-D06 cell lists.

This tranche exposes the zero and successor equations for the RFC
``CellListLen`` relation.  The readable relations are authoring helpers only:
every occurrence expands to the unchanged first-order Peano language before
parsing.  The candidates are dependency-curried, unregistered, and
unadmitted; their intended first gate is lightweight body replay only.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import (
    cell_history,
    cell_list_len,
)
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _cell_list_succ_len(code: str, length: str, *, tag: str) -> str:
    """Expand ``CellListLen(code,S length)`` through the checked helper.

    ``cell_list_len`` deliberately accepts only identifier arguments.  A
    fresh free placeholder is therefore expanded first and then replaced by
    the successor term.  The generated bound witnesses use ``tag`` and never
    contain the placeholder, so this is a capture-free surface substitution.
    """

    placeholder = "hcleq_successor_length_argument"
    expanded = cell_list_len(code, placeholder, tag=tag)
    occurrences = expanded.count(placeholder)
    if occurrences == 0:
        raise ValueError("successor-length placeholder disappeared")
    return expanded.replace(placeholder, f"S {length}")


def make_ha_cell_list_equations_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact zero and successor ``CellListLen`` equations."""

    zero_source = cell_list_len("z", "zero_length", tag="zero_source")
    zero_source = zero_source.replace("zero_length", "0")
    zero_target = cell_list_len("z", "zero_length", tag="zero_target")
    zero_target = zero_target.replace("zero_length", "0")

    succ_source = _cell_list_succ_len("z", "l", tag="succ_source")
    predecessor_target = cell_list_len("t", "l", tag="succ_predecessor")
    predecessor_source = cell_list_len("t", "l", tag="succ_input")
    succ_target = _cell_list_succ_len("z", "l", tag="succ_target")
    exact_cell = cell("z", "h", "t")
    eliminated_history = cell_history(
        "t", "l", "x", "x1", tag="succ_eliminated_history"
    )
    eliminated_result = (
        f"exists t h. (({exact_cell}) /\\ ({eliminated_history}))"
    )

    return (
        spec(
            "cell_list_zero_iff_nil",
            "forall z. "
            f"((({zero_source}) -> z = 0) /\\ "
            f"(z = 0 -> ({zero_target})))",
            ("beta_at_unique", "cell_history_nil"),
            (
                "intro z",
                "split",
                "intro hlist",
                "cases hlist",
                "cases hlist_witness",
                "cases hlist_witness_witness",
                "cases hlist_witness_witness_right",
                "have hzero : 0 = z",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique z",
                "apply beta_at_unique",
                "exact hlist_witness_witness_left",
                "exact hlist_witness_witness_right_left",
                "symm",
                "exact hzero",
                "intro hz",
                "rewrite hz",
                "rewrite hz",
                "exists 0",
                "exists 0",
                "exact cell_history_nil",
            ),
            "A beta-backed exact-D06 cell list has length zero exactly when "
            "its terminal code is nil.",
        ),
        spec(
            "cell_list_succ_iff_cell",
            "forall z l. "
            f"((({succ_source}) -> exists t h. "
            f"(({exact_cell}) /\\ ({predecessor_target}))) /\\ "
            f"((exists t h. (({exact_cell}) /\\ ({predecessor_source}))) -> "
            f"({succ_target})))",
            ("cell_history_succ_elim", "cell_history_extend"),
            (
                "intro z",
                "intro l",
                "split",
                "intro hlist",
                "cases hlist",
                "cases hlist_witness",
                "specialize cell_history_succ_elim x",
                "specialize cell_history_succ_elim x1",
                "specialize cell_history_succ_elim l",
                "specialize cell_history_succ_elim z",
                f"have hdecomp : {eliminated_result}",
                "apply cell_history_succ_elim",
                "exact hlist_witness_witness",
                "cases hdecomp",
                "cases hdecomp_witness",
                "exists x2",
                "exists x3",
                "cases hdecomp_witness_witness",
                "split",
                "exact hdecomp_witness_witness_left",
                "exists x",
                "exists x1",
                "exact hdecomp_witness_witness_right",
                "intro hstep",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_right",
                "cases hstep_witness_witness_right_witness",
                "specialize cell_history_extend x2",
                "specialize cell_history_extend x3",
                "specialize cell_history_extend l",
                "specialize cell_history_extend x",
                "specialize cell_history_extend z",
                "specialize cell_history_extend x1",
                "apply cell_history_extend",
                "exact hstep_witness_witness_right_witness_witness",
                "exact hstep_witness_witness_left",
            ),
            "A positive-length beta-backed list is exactly one exact D06 "
            "cell over a predecessor list of the preceding length.",
        ),
    )


__all__ = ["make_ha_cell_list_equations_candidate_theorems"]
