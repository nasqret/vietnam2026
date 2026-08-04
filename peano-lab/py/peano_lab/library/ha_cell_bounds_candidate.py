"""Constructive component descent for successor-tagged HA cells.

This isolated ``HA-K3-PAIR-1`` layer proves that each component of the
doubled-Cantor pair polynomial is bounded by its code and then lifts those
bounds through the exact D06 successor tag.  The resulting strict head/tail
bounds are the descent facts needed by later cell recursion.

All order statements use native witnesses.  The module depends only on the
private pair-shell lower bound and public K0--K2 arithmetic; it uses no
division, remainder, beta coding, CRT, classical logic, or DNE.  Nothing in
this file is registered or publicly admitted.
"""

from __future__ import annotations

from typing import Any, Callable


def make_ha_cell_bounds_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the two pair bounds and exact D06 strict component bounds."""

    pair = "(left + right) * S (left + right) + (right + right)"
    cell_pair = "(head + tail) * S (head + tail) + (tail + tail)"

    return (
        spec(
            "pair_left_le_code",
            f"forall code left right. code = {pair} -> "
            "exists k. k + left = code",
            ("le_add_right", "pair_code_shell_lower", "le_trans"),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hcode",
                "have hleft_sum : exists k. k + left = left + right",
                "specialize le_add_right left",
                "specialize le_add_right right",
                "exact le_add_right",
                "have hsum_shell : exists k. k + (left + right) = "
                "(left + right) * S (left + right)",
                "exists (left + right) * (left + right)",
                "rewrite PA6",
                "refl",
                "have hleft_shell : exists k. k + left = "
                "(left + right) * S (left + right)",
                "specialize le_trans left",
                "specialize le_trans (left + right)",
                "specialize le_trans ((left + right) * S (left + right))",
                "apply le_trans",
                "exact hleft_sum",
                "exact hsum_shell",
                "have hshell_code : exists k. k + "
                "(left + right) * S (left + right) = code",
                "specialize pair_code_shell_lower code",
                "specialize pair_code_shell_lower left",
                "specialize pair_code_shell_lower right",
                "apply pair_code_shell_lower",
                "exact hcode",
                "specialize le_trans left",
                "specialize le_trans ((left + right) * S (left + right))",
                "specialize le_trans code",
                "apply le_trans",
                "exact hleft_shell",
                "exact hshell_code",
            ),
            "The left component of an exact D01 pair is at most its pair code.",
        ),
        spec(
            "pair_right_le_code",
            f"forall code left right. code = {pair} -> "
            "exists k. k + right = code",
            ("le_add_left", "pair_code_shell_lower", "le_trans"),
            (
                "intro code",
                "intro left",
                "intro right",
                "intro hcode",
                "have hright_sum : exists k. k + right = left + right",
                "specialize le_add_left right",
                "specialize le_add_left left",
                "exact le_add_left",
                "have hsum_shell : exists k. k + (left + right) = "
                "(left + right) * S (left + right)",
                "exists (left + right) * (left + right)",
                "rewrite PA6",
                "refl",
                "have hright_shell : exists k. k + right = "
                "(left + right) * S (left + right)",
                "specialize le_trans right",
                "specialize le_trans (left + right)",
                "specialize le_trans ((left + right) * S (left + right))",
                "apply le_trans",
                "exact hright_sum",
                "exact hsum_shell",
                "have hshell_code : exists k. k + "
                "(left + right) * S (left + right) = code",
                "specialize pair_code_shell_lower code",
                "specialize pair_code_shell_lower left",
                "specialize pair_code_shell_lower right",
                "apply pair_code_shell_lower",
                "exact hcode",
                "specialize le_trans right",
                "specialize le_trans ((left + right) * S (left + right))",
                "specialize le_trans code",
                "apply le_trans",
                "exact hright_shell",
                "exact hshell_code",
            ),
            "The right component of an exact D01 pair is at most its pair code.",
        ),
        spec(
            "cell_head_lt_code",
            f"forall code head tail. code = S ({cell_pair}) -> "
            "exists k. k + S head = code",
            ("pair_left_le_code", "succ_le_succ"),
            (
                "intro code",
                "intro head",
                "intro tail",
                "intro hcell",
                "rewrite hcell",
                "specialize succ_le_succ head",
                f"specialize succ_le_succ ({cell_pair})",
                "apply succ_le_succ",
                f"specialize pair_left_le_code ({cell_pair})",
                "specialize pair_left_le_code head",
                "specialize pair_left_le_code tail",
                "apply pair_left_le_code",
                "refl",
            ),
            "The head of an exact D06 cell is strictly below the tagged code.",
        ),
        spec(
            "cell_tail_lt_code",
            f"forall code head tail. code = S ({cell_pair}) -> "
            "exists k. k + S tail = code",
            ("pair_right_le_code", "succ_le_succ"),
            (
                "intro code",
                "intro head",
                "intro tail",
                "intro hcell",
                "rewrite hcell",
                "specialize succ_le_succ tail",
                f"specialize succ_le_succ ({cell_pair})",
                "apply succ_le_succ",
                f"specialize pair_right_le_code ({cell_pair})",
                "specialize pair_right_le_code head",
                "specialize pair_right_le_code tail",
                "apply pair_right_le_code",
                "refl",
            ),
            "The tail of an exact D06 cell is strictly below the tagged code.",
        ),
    )


__all__ = ["make_ha_cell_bounds_candidate_theorems"]
