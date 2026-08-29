"""Exact support cones after 296 published and 125 local research theorems.

This selects theorem syntax and authenticates seed bytes, not proof authority.
All selected inherited bodies still require fresh original-HA and independent
Lean checks in the caller's complete closure. The local continuation is never
relabelled as published, Alpha-admitted, or newly owned.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import constructive_lower_continuation_support as previous
import constructive_lower_continuation_checkpoints as continuation
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[1]
SupportError = previous.SupportError
_LOCAL_INVENTORY = (
    ("divisor-involutions", 12), ("mobius-divisor-cancellation", 28),
    ("rectangular-sums", 32), ("polynomial-products", 53),
)


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    frontier: tuple[TheoremSpec, ...]
    bottom_support: tuple[str, ...]
    lower_support: tuple[str, ...]
    local_support: tuple[str, ...]
    current_support: tuple[str, ...]
    plan: closure.BottomLayerPlan

    @property
    def published_support(self) -> tuple[str, ...]:
        """Only the two actually published, still non-admitted generations."""
        return self.bottom_support + self.lower_support

    @property
    def inherited_support(self) -> tuple[str, ...]:
        """All three research generations, without changing their statuses."""
        return self.published_support + self.local_support

    def role(self, name: str) -> str:
        if name in {row.name for row in self.owned}:
            return "new_owned_theorem"
        if name in self.bottom_support:
            return "inherited_published_bottom_layer_checkpoint"
        if name in self.lower_support:
            return "inherited_published_lower_tier_checkpoint"
        if name in self.local_support:
            return "inherited_local_lower_continuation_checkpoint"
        if name in self.current_support:
            return "new_cross_track_support"
        if name in {row.name for row in self.plan.rows}:
            return "inherited_alpha_v30"
        raise SupportError("the name is not in the actual complete proof cone")


def _local_rows() -> tuple[TheoremSpec, ...]:
    """Preserve the exact frozen local generation, not an arbitrary registry."""
    if (tuple((item.slug, item.frontier_count) for item in continuation.CHECKPOINTS) != _LOCAL_INVENTORY
            or continuation.EXPECTED_FAMILIES != {name for name, _ in _LOCAL_INVENTORY}):
        raise SupportError("the exact four-family local 125-theorem inventory changed")
    rows = continuation.all_new_rows()  # Actual source bytes AND ordered specs.
    if len(rows) != 125:
        raise SupportError("the exact local 125-theorem generation changed")
    closure._validate_frontier(rows)
    return rows


def previous_rows() -> tuple[TheoremSpec, ...]:
    """Authenticate all 421 research prerequisites without admitting them."""
    inherited = previous.previous_rows()
    if len(inherited) != 296:
        raise SupportError("the two published research generations changed")
    rows = (*inherited, *_local_rows())
    closure._validate_frontier(rows)
    return rows


def select_support(new_rows: tuple[TheoremSpec, ...], owned_names: tuple[str, ...]) -> SupportSelection:
    """Delegate complete topology validation, then split exact inventory roles."""
    closure._validate_frontier(new_rows)
    current_names = {row.name for row in new_rows}
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or not set(owned_names) <= current_names):
        raise SupportError("owned names must select only the current new proof tranche")
    local_rows = _local_rows()
    selected = previous.select_support((*local_rows, *new_rows), owned_names)
    local_names = {row.name for row in local_rows}
    return SupportSelection(
        selected.owned, selected.frontier, selected.bottom_support, selected.lower_support,
        tuple(name for name in selected.current_support if name in local_names),
        tuple(name for name in selected.current_support if name not in local_names),
        selected.plan,
    )


def previous_seed_paths() -> tuple[Path, ...]:
    """Return 11 exact proof-data paths; no stored success receipt is trusted."""
    _local_rows()
    paths = list(previous.previous_seed_paths())
    for item in continuation.CHECKPOINTS:
        path = ROOT / item.artifact
        closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        paths.append(path)
    return tuple(paths)


def statement_duplicates(new_rows: tuple[TheoremSpec, ...]) -> tuple[tuple[str, str], ...]:
    """Exact FormulaDAG comparison against all 3,643 prior rows and new peers.

    The audited comparator compares canonical DAG bytes, not hashes alone.
    Prefixing the exact local 125 extends the earlier 3,518-row comparison;
    those inherited statements are compared, never counted as newly owned.
    """
    closure._validate_frontier(new_rows)
    names = {row.name for row in new_rows}
    duplicates = previous.statement_duplicates((*_local_rows(), *new_rows))
    return tuple(pair for pair in duplicates if pair[0] in names)


__all__ = ("ROOT", "SupportError", "SupportSelection", "previous_rows",
           "previous_seed_paths", "select_support", "statement_duplicates")
