"""Actual support cones after both non-admitted research generations.

This selects syntax, not proof authority. Complete inherited bodies still
pass the original HA bundle checker and the independently compiled Lean
checker. Source authentication is never substituted for either proof check.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import constructive_lower_tier_support as first
import constructive_lower_tier_checkpoints as lower
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[1]
SupportError = first.LowerTierSupportError


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    frontier: tuple[TheoremSpec, ...]
    bottom_support: tuple[str, ...]
    lower_support: tuple[str, ...]
    current_support: tuple[str, ...]
    plan: closure.BottomLayerPlan

    @property
    def published_support(self) -> tuple[str, ...]:
        return self.bottom_support + self.lower_support

    def role(self, name: str) -> str:
        if name in {row.name for row in self.owned}:
            return "new_owned_theorem"
        if name in self.bottom_support:
            return "inherited_published_bottom_layer_checkpoint"
        if name in self.lower_support:
            return "inherited_published_lower_tier_checkpoint"
        if name in self.current_support:
            return "new_cross_track_support"
        if name in {row.name for row in self.plan.rows}:
            return "inherited_alpha_v30"
        raise SupportError("the name is not in the actual complete proof cone")


def previous_rows() -> tuple[TheoremSpec, ...]:
    """Authenticate both frozen generations, including whole factory output."""
    return (*first.previous_rows(), *lower.all_new_rows())


def select_support(new_rows: tuple[TheoremSpec, ...], owned_names: tuple[str, ...]) -> SupportSelection:
    closure._validate_frontier(new_rows)
    current_names = {row.name for row in new_rows}
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or not set(owned_names) <= current_names):
        raise SupportError("owned names must select only the current new proof tranche")
    prior_lower = lower.all_new_rows()
    selected = first.select_support((*prior_lower, *new_rows), owned_names)
    lower_names = {row.name for row in prior_lower}
    return SupportSelection(
        selected.owned, selected.frontier, selected.published_support,
        tuple(name for name in selected.current_support if name in lower_names),
        tuple(name for name in selected.current_support if name not in lower_names),
        selected.plan,
    )


def previous_seed_paths() -> tuple[Path, ...]:
    """Authenticated proof data for subsequent fresh checks, never receipts."""
    paths = list(first.previous_seed_paths())
    for item in lower.CHECKPOINTS:
        path = ROOT / item.artifact
        closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        paths.append(path)
    return tuple(paths)


def statement_duplicates(new_rows: tuple[TheoremSpec, ...]) -> tuple[tuple[str, str], ...]:
    """Exact parsed-AST comparison against all 3,518 prior rows and each other.

    The earlier audited comparator checks canonical formula-DAG bytes, using
    hashes only as an index. Prefixing the frozen 126 rows extends its original
    3,392-row baseline; they are compared, not counted as newly owned results.
    """
    closure._validate_frontier(new_rows)
    names = {row.name for row in new_rows}
    duplicates = first.statement_duplicates((*lower.all_new_rows(), *new_rows))
    return tuple(pair for pair in duplicates if pair[0] in names)


__all__ = ("ROOT", "SupportError", "SupportSelection", "previous_rows",
           "previous_seed_paths", "select_support", "statement_duplicates")
