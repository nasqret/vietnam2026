"""Private K3B history extension with an exposed decoded-prefix map.

The earlier ``cell_history_extend`` row intentionally returns only fresh
history witnesses.  Lookup successor introduction additionally needs the
pointwise preservation map produced by ``beta_prefix_extend``.  This isolated
candidate repeats the same constructive CRT construction and returns that map
beside the extended history.  All surface helpers expand before parsing; the
row is dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_cell_history_candidate import (
    beta_at,
    cell_history,
)
from peano_lab.library.ha_pair_cell_seed_candidate import cell


def _successor_history(
    code: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    """Expand ``CellHistory(code,S length;trace_code,trace_scale)`` safely."""

    placeholder = "hchpres_successor_length_argument"
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


def make_ha_cell_history_prefix_preservation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the strengthened one-cell extension required by ``ListAt``."""

    before = cell_history("t", "l", "b", "c", tag="preserve_before")
    after = _successor_history(
        "u", "l", "b2", "c2", tag="preserve_after"
    )
    exact_cell = cell("u", "h", "t")
    old_entry = beta_at("b", "c", "k", "v", tag="preserve_old_entry")
    new_entry = beta_at(
        "b2", "c2", "k", "v", tag="preserve_new_entry"
    )

    old_edge_current = beta_at(
        "b", "c", "i", "t0", tag="preserve_edge_current"
    )
    old_edge_following_placeholder = "hchpres_following_index_argument"
    old_edge_following = beta_at(
        "b",
        "c",
        old_edge_following_placeholder,
        "u0",
        tag="preserve_edge_following",
    ).replace(old_edge_following_placeholder, "S i")
    old_edge = (
        f"exists t0 u0 h0. (({old_edge_current}) /\\ "
        f"(({old_edge_following}) /\\ ({cell('u0', 'h0', 't0')})))"
    )

    return (
        spec(
            "cell_history_extend_preserves_prefix",
            "forall b c l t u h. "
            f"({before}) -> ({exact_cell}) -> exists b2 c2. "
            f"(({after}) /\\ forall k v. "
            f"(exists d. d + k = l) -> ({old_entry}) -> ({new_entry}))",
            (
                "beta_prefix_extend",
                "finite_lt_succ_eq_or_lt",
                "zero_le",
                "succ_le_succ",
                "le_refl",
            ),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro t",
                "intro u",
                "intro h",
                "intro hhistory",
                "intro hcell",
                "cases hhistory",
                "cases hhistory_right",
                "specialize beta_prefix_extend (S l)",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend u",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "split",
                # First branch: the same extended-history construction as the
                # opaque predecessor theorem.
                "split",
                "specialize beta_prefix_extend_witness_witness_right 0",
                "specialize beta_prefix_extend_witness_witness_right 0",
                "apply beta_prefix_extend_witness_witness_right",
                "have hzero : exists gap. gap + 0 = l",
                "specialize zero_le l",
                "exact zero_le",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hzero",
                "exact hhistory_left",
                "split",
                "exact beta_prefix_extend_witness_witness_left",
                "intro i",
                "intro hi",
                "have hsplit : i = l \\/ exists gap. gap + S i = l",
                "specialize finite_lt_succ_eq_or_lt l",
                "specialize finite_lt_succ_eq_or_lt i",
                "apply finite_lt_succ_eq_or_lt",
                "exact hi",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exists t",
                "exists u",
                "exists h",
                "split",
                "specialize beta_prefix_extend_witness_witness_right l",
                "specialize beta_prefix_extend_witness_witness_right t",
                "apply beta_prefix_extend_witness_witness_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hhistory_right_left",
                "split",
                "exact beta_prefix_extend_witness_witness_left",
                "exact hcell",
                f"have hold : {old_edge}",
                "specialize hhistory_right_right i",
                "apply hhistory_right_right",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "exists x2",
                "exists x3",
                "exists x4",
                "split",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right x2",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hi",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize beta_prefix_extend_witness_witness_right (S i)",
                "specialize beta_prefix_extend_witness_witness_right x3",
                "apply beta_prefix_extend_witness_witness_right",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_left",
                "exact hold_witness_witness_witness_right_right",
                # Second branch: use the same fresh witnesses, but retain the
                # unspecialized prefix map from the sibling proof branch.
                "intro k",
                "intro v",
                "intro hk",
                "intro hv",
                "specialize beta_prefix_extend_witness_witness_right k",
                "specialize beta_prefix_extend_witness_witness_right v",
                "apply beta_prefix_extend_witness_witness_right",
                "specialize succ_le_succ k",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hk",
                "exact hv",
            ),
            "Append one exact D06 cell and expose preservation of every old "
            "decoded beta entry through the old terminal index.",
        ),
    )


__all__ = ["make_ha_cell_history_prefix_preservation_candidate_theorems"]
