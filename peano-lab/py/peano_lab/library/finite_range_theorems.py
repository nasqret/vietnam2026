"""Checked theorem data for beta-coded consecutive ranges.

The registry imports this data factory only after the prerequisite β-prefix
theorems. Its statements expand the conservative ``Range`` surface into
ordinary first-order Peano formulas. Admission tests replay every script
against the existing checked ladder and submit the resulting closed
certificate to the unchanged kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import RANGE_EXISTS, beta_at, range_relation


def make_finite_range_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build the dependency-ordered beta ``Range`` theorem tranche."""

    range_empty = range_relation("b", "c", "a", "l", tag="empty")
    range_before = range_relation("b", "c", "a", "l", tag="before")
    range_after = range_relation("z", "d", "a", "sl", tag="after")
    range_entry = range_relation("b", "c", "a", "l", tag="entry")
    at_entry = beta_at("b", "c", "i", "x", tag="range_entry_x")
    range_transport_left = range_relation(
        "b", "c", "a", "l", tag="transport_l"
    )
    range_transport_right = range_relation(
        "z", "d", "a", "l", tag="transport_r"
    )
    at_transport_left = beta_at(
        "b", "c", "i", "x", tag="range_transport_x"
    )
    at_transport_right = beta_at(
        "z", "d", "i", "x", tag="range_transport_y"
    )

    return (
        spec(
            "beta_range_empty",
            f"forall b c a l. l = 0 -> ({range_empty})",
            ("add_eq_zero_right", "succ_ne_zero"),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro hl",
                "intro i",
                "intro hi",
                "rewrite hl at hi",
                "exfalso",
                "cases hi",
                "have hsi : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi",
            ),
            "Every consecutive beta range of length zero is vacuous.",
        ),
        spec(
            "beta_range_succ_extend",
            f"forall b c a l sl. sl = S l -> ({range_before}) -> "
            f"exists z d. ({range_after})",
            (
                "beta_prefix_extend",
                "le_of_succ_le_succ",
                "le_eq_or_lt",
            ),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro sl",
                "intro hsl",
                "intro hrange",
                "specialize beta_prefix_extend l",
                "specialize beta_prefix_extend b",
                "specialize beta_prefix_extend c",
                "specialize beta_prefix_extend (a + l)",
                "cases beta_prefix_extend",
                "cases beta_prefix_extend_witness",
                "cases beta_prefix_extend_witness_witness",
                "exists x",
                "exists x1",
                "intro i",
                "intro hi",
                "rewrite hsl at hi",
                "have hil : exists h. h + i = l",
                "specialize le_of_succ_le_succ i",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hi",
                "have hsplit : i = l \/ exists h. h + S i = l",
                "specialize le_eq_or_lt i",
                "specialize le_eq_or_lt l",
                "apply le_eq_or_lt",
                "exact hil",
                "cases hsplit",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact beta_prefix_extend_witness_witness_left",
                "specialize beta_prefix_extend_witness_witness_right i",
                "specialize beta_prefix_extend_witness_witness_right (a + i)",
                "apply beta_prefix_extend_witness_witness_right",
                "exact hsplit_right",
                "specialize hrange i",
                "apply hrange",
                "exact hsplit_right",
            ),
            "Recode a consecutive prefix and append its next value.",
        ),
        spec(
            "beta_range_exists",
            RANGE_EXISTS,
            ("beta_range_empty", "beta_range_succ_extend"),
            (
                "intro a",
                "induction l",
                "exists 0",
                "exists 0",
                "specialize beta_range_empty 0",
                "specialize beta_range_empty 0",
                "specialize beta_range_empty a",
                "specialize beta_range_empty 0",
                "apply beta_range_empty",
                "refl",
                "cases IH",
                "cases IH_witness",
                "specialize beta_range_succ_extend x",
                "specialize beta_range_succ_extend x1",
                "specialize beta_range_succ_extend a",
                "specialize beta_range_succ_extend l",
                "specialize beta_range_succ_extend (S l)",
                "apply beta_range_succ_extend",
                "refl",
                "exact IH_witness_witness",
            ),
            "Every start and length admit a beta-coded consecutive range.",
        ),
        spec(
            "beta_range_entry_eq",
            f"forall b c a l i x. ({range_entry}) -> "
            f"(exists h. h + S i = l) -> ({at_entry}) -> x = a + i",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro a",
                "intro l",
                "intro i",
                "intro x",
                "intro hrange",
                "intro hi",
                "intro hx",
                "have ha : ((exists h. h + S (a + i) = S ((S i) * c)) /\\ "
                "exists q. b = q * S ((S i) * c) + (a + i))",
                "specialize hrange i",
                "apply hrange",
                "exact hi",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x",
                "specialize beta_at_unique (a + i)",
                "apply beta_at_unique",
                "exact hx",
                "exact ha",
            ),
            "A decoded entry of a Range prefix is its start plus its index.",
        ),
        spec(
            "beta_range_transport_entry",
            f"forall b c z d a l. ({range_transport_left}) -> "
            f"({range_transport_right}) -> forall i x. "
            f"(exists h. h + S i = l) -> ({at_transport_left}) -> "
            f"({at_transport_right})",
            ("beta_range_entry_eq",),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro a",
                "intro l",
                "intro hleft",
                "intro hright",
                "intro i",
                "intro x",
                "intro hi",
                "intro hx",
                "have hxa : x = a + i",
                "specialize beta_range_entry_eq b",
                "specialize beta_range_entry_eq c",
                "specialize beta_range_entry_eq a",
                "specialize beta_range_entry_eq l",
                "specialize beta_range_entry_eq i",
                "specialize beta_range_entry_eq x",
                "apply beta_range_entry_eq",
                "exact hleft",
                "exact hi",
                "exact hx",
                "rewrite hxa",
                "rewrite hxa",
                "specialize hright i",
                "apply hright",
                "exact hi",
            ),
            "Two Range codes preserve every decoded entry extensionally.",
        ),
    )


__all__ = ["make_finite_range_theorems"]
