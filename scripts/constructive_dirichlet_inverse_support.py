"""Exact syntax support after four non-admitted research generations.

The first 170 and 126 research rows were published; the following 125 and
113 remain local. None becomes Alpha-admitted or newly owned here. Source,
specification and seed-byte authentication identifies inputs, not proof
authority: callers must still freshly check every selected proof body.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path

import constructive_dirichlet_support as previous
import constructive_dirichlet_checkpoints as dirichlet
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.theorems import TheoremSpec


ROOT = Path(__file__).resolve().parents[1]
SupportError = previous.SupportError
PRIOR_RESEARCH_COUNTS = (170, 126, 125, 113)
PRIOR_RESEARCH_COUNT = 534
PRIOR_THEOREM_COUNT = 3756
PRIOR_SEED_COUNT = 16
_DIRICHLET_INVENTORY = (
    ("finite-support", 8), ("dirichlet-convolution", 40),
    ("dirichlet-fubini", 32), ("dirichlet-units", 25),
    ("mobius-inversion", 8),
)
# Exact metadata from the completed, frozen 113-row checkpoint. These pins
# include ordered modules/source hashes/spec hashes, roots and artifact paths,
# sizes and hashes. A saved successful audit is deliberately not an input.
_DIRICHLET_REGISTRY_BYTES = 3616
_DIRICHLET_REGISTRY_SHA256 = "919b375e128659f7752c32c069d6408a04dd0dff5610716d9da1324d30968a14"
_DIRICHLET_SPECS_SHA256 = "858f5de9aeacc11d2ea3704dbc116fc45c4f38a20636cd2820aeea81fb808804"


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    frontier: tuple[TheoremSpec, ...]
    bottom_support: tuple[str, ...]
    lower_support: tuple[str, ...]
    continuation_support: tuple[str, ...]
    dirichlet_support: tuple[str, ...]
    current_support: tuple[str, ...]
    plan: closure.BottomLayerPlan

    @property
    def published_support(self) -> tuple[str, ...]:
        """The two published generations, still outside Alpha admission."""
        return self.bottom_support + self.lower_support

    @property
    def local_support(self) -> tuple[str, ...]:
        """The two local generations, without merging their distinct roles."""
        return self.continuation_support + self.dirichlet_support

    @property
    def inherited_support(self) -> tuple[str, ...]:
        return self.published_support + self.local_support

    def role(self, name: str) -> str:
        if name in {row.name for row in self.owned}:
            return "new_owned_theorem"
        if name in self.bottom_support:
            return "inherited_published_bottom_layer_checkpoint"
        if name in self.lower_support:
            return "inherited_published_lower_tier_checkpoint"
        if name in self.continuation_support:
            return "inherited_local_lower_continuation_checkpoint"
        if name in self.dirichlet_support:
            return "inherited_local_dirichlet_checkpoint"
        if name in self.current_support:
            return "new_cross_track_support"
        if name in {row.name for row in self.plan.rows}:
            return "inherited_alpha_v30"
        raise SupportError("the name is not in the actual complete proof cone")


def _dirichlet_registry():
    items = dirichlet.CHECKPOINTS
    if (type(items) is not tuple or any(type(item) is not dirichlet.Checkpoint for item in items)
            or tuple((item.slug, item.frontier_count) for item in items) != _DIRICHLET_INVENTORY
            or dirichlet.EXPECTED_FAMILIES != {name for name, _ in _DIRICHLET_INVENTORY}):
        raise SupportError("the exact five-family local 113-theorem inventory changed")
    try:
        encoded = json.dumps([asdict(item) for item in items], ensure_ascii=False,
                             sort_keys=True, allow_nan=False, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise SupportError("the frozen 113-theorem checkpoint metadata changed") from error
    if (len(encoded) != _DIRICHLET_REGISTRY_BYTES
            or sha256(encoded).hexdigest() != _DIRICHLET_REGISTRY_SHA256):
        raise SupportError("the frozen 113-theorem checkpoint metadata changed")
    return items


def _dirichlet_rows() -> tuple[TheoremSpec, ...]:
    _dirichlet_registry()
    rows = dirichlet.all_new_rows()  # Actual source bytes AND every ordered spec.
    closure._validate_frontier(rows)
    if len(rows) != 113 or closure._specs_digest(rows) != _DIRICHLET_SPECS_SHA256:
        raise SupportError("the exact frozen 113-theorem specifications changed")
    return rows


def previous_rows() -> tuple[TheoremSpec, ...]:
    """Authenticate all 534 prior research rows in their four-generation order."""
    inherited = previous.previous_rows()
    if len(inherited) != 421:
        raise SupportError("the three earlier research generations changed")
    rows = (*inherited, *_dirichlet_rows())
    closure._validate_frontier(rows)
    return rows


def select_support(new_rows: tuple[TheoremSpec, ...], owned_names: tuple[str, ...]) -> SupportSelection:
    """Retain original whole-inventory topology checks, then split seven roles."""
    closure._validate_frontier(new_rows)
    current_names = {row.name for row in new_rows}
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or not set(owned_names) <= current_names):
        raise SupportError("owned names must select only the current new proof tranche")
    inherited_dirichlet = _dirichlet_rows()
    selected = previous.select_support((*inherited_dirichlet, *new_rows), owned_names)
    prior_names = {row.name for row in inherited_dirichlet}
    return SupportSelection(
        selected.owned, selected.frontier, selected.bottom_support, selected.lower_support,
        selected.local_support,
        tuple(name for name in selected.current_support if name in prior_names),
        tuple(name for name in selected.current_support if name not in prior_names),
        selected.plan,
    )


def previous_seed_paths() -> tuple[Path, ...]:
    """Authenticate 16 literal proof-data files; never consume an old receipt."""
    _dirichlet_rows()
    paths = list(previous.previous_seed_paths())
    for item in _dirichlet_registry():
        path = ROOT / item.artifact
        closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        paths.append(path)
    if len(paths) != PRIOR_SEED_COUNT or len(set(paths)) != PRIOR_SEED_COUNT:
        raise SupportError("the exact sixteen-file inherited seed inventory changed")
    return tuple(paths)


def statement_duplicates(new_rows: tuple[TheoremSpec, ...]) -> tuple[tuple[str, str], ...]:
    """Exact FormulaDAG comparison against all 3,756 prior rows and new peers.

    Delegate to the reviewed comparator with the frozen local 113 prefixed.
    Hashes only index canonical DAG bytes; they never decide equality alone.
    Inherited comparisons are filtered out, not counted as new discoveries.
    """
    closure._validate_frontier(new_rows)
    names = {row.name for row in new_rows}
    duplicates = previous.statement_duplicates((*_dirichlet_rows(), *new_rows))
    return tuple(pair for pair in duplicates if pair[0] in names)


__all__ = ("ROOT", "SupportError", "SupportSelection", "PRIOR_RESEARCH_COUNTS",
           "PRIOR_RESEARCH_COUNT", "PRIOR_THEOREM_COUNT", "PRIOR_SEED_COUNT",
           "previous_rows", "previous_seed_paths", "select_support", "statement_duplicates")
