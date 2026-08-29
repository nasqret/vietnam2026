"""Exact support cones for the next non-admitting research checkpoints.

The previous 170 checkpoint theorems are proof prerequisites, not Alpha
members and not newly counted results.  This module only selects syntax.
Every selected body must still pass the unchanged complete HA bundle checker;
neither a source pin, an inventory role, nor a stored receipt proves anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(ROOT / "peano-lab/py"))

import constructive_bottom_layer_checkpoints as previous
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import TheoremSpec, _closed_formula


class LowerTierSupportError(ValueError):
    """A new row or an exact inherited proof prerequisite is inconsistent."""


@dataclass(frozen=True, slots=True)
class SupportSelection:
    owned: tuple[TheoremSpec, ...]
    frontier: tuple[TheoremSpec, ...]
    published_support: tuple[str, ...]
    current_support: tuple[str, ...]
    plan: closure.BottomLayerPlan

    def role(self, name: str) -> str:
        if name in {row.name for row in self.owned}:
            return "new_owned_theorem"
        if name in self.published_support:
            return "inherited_published_non_admitted_checkpoint"
        if name in self.current_support:
            return "new_cross_track_support"
        if name in {row.name for row in self.plan.rows}:
            return "inherited_alpha_v30"
        raise LowerTierSupportError("the name is not in this complete proof cone")


def previous_rows() -> tuple[TheoremSpec, ...]:
    """Re-authenticate source bytes AND complete ordered factory output."""
    return tuple(row for item in previous.CHECKPOINTS for row in previous.load_rows(item))


def select_support(
    new_rows: tuple[TheoremSpec, ...], owned_names: tuple[str, ...],
) -> SupportSelection:
    """Select only actual prerequisites; preserve their global proof order.

    ``new_rows`` is the complete topologically ordered current tranche.
    ``owned_names`` names one chapter's new results in that same order.  No
    previous research row can be enrolled as a newly owned result.  The
    unchanged closure checker receives *all* non-Alpha prerequisites, while
    the presentation/reporting layer keeps the three inventory roles separate.
    """
    closure._validate_frontier(new_rows)
    if (type(owned_names) is not tuple or not owned_names
            or any(type(name) is not str for name in owned_names)
            or len(set(owned_names)) != len(owned_names)):
        raise LowerTierSupportError("owned names must be a nonempty distinct exact tuple")
    owned_set = set(owned_names)
    owned = tuple(row for row in new_rows if row.name in owned_set)
    if tuple(row.name for row in owned) != owned_names:
        raise LowerTierSupportError("owned names must select only new rows in inventory order")

    inherited = previous_rows()
    inventory = (*inherited, *new_rows)
    # Validate even unused rows before selecting a cone: no hidden shadowing,
    # forward edges, unknown dependencies, or cyclic support is permitted.
    closure.bottom_layer_plan(inventory)
    non_alpha = {row.name: row for row in inventory}
    included: set[str] = set()
    pending = list(owned_names)
    while pending:
        name = pending.pop()
        if name in included or name not in non_alpha:
            continue  # Alpha dependencies are closed by the original helper.
        included.add(name)
        pending.extend(non_alpha[name].dependencies)
    frontier = tuple(row for row in inventory if row.name in included)
    published_support = tuple(row.name for row in inherited if row.name in included)
    current_support = tuple(row.name for row in new_rows
                            if row.name in included and row.name not in owned_set)
    plan = closure.bottom_layer_plan(frontier)
    if set(plan.root_names) - owned_set:
        raise LowerTierSupportError("an inherited support row became an unrelated chapter root")
    return SupportSelection(owned, frontier, published_support, current_support, plan)


def previous_seed_paths() -> tuple[Path, ...]:
    """Identify exact old proof data, for subsequent fresh full proof checks."""
    paths = []
    for item in previous.CHECKPOINTS:
        path = ROOT / item.artifact
        closure._read_pinned(path, item.artifact_bytes, item.artifact_sha256)
        paths.append(path)
    return tuple(paths)


def statement_duplicates(new_rows: tuple[TheoremSpec, ...]) -> tuple[tuple[str, str], ...]:
    """Compare exact parsed ASTs against all 3,392 earlier rows and each other.

    Reuse the audited formula DAG to avoid recursively expanding shared
    double-and-add numerals.  Hashes are only an index: exact canonical DAG
    bytes must match before reporting a duplicate.  Binder spelling, source
    length, and theorem names are irrelevant to this comparison.
    """
    closure._validate_frontier(new_rows)
    index: dict[bytes, list[tuple[str, str]]] = {}
    duplicates: list[tuple[str, str]] = []

    def exact_ast(row: TheoremSpec) -> tuple[bytes, str]:
        encoded = FormulaArena().freeze(_closed_formula(row.statement)).to_json()
        return sha256(encoded.encode()).digest(), encoded

    for row in new_rows:
        fingerprint, encoded = exact_ast(row)
        duplicates.extend((row.name, name) for name, other in index.get(fingerprint, ())
                          if encoded == other)
        index.setdefault(fingerprint, []).append((row.name, encoded))
    for row in (*closure.parent_snapshot().specs, *previous_rows()):
        fingerprint, encoded = exact_ast(row)
        duplicates.extend((name, row.name) for name, other in index.get(fingerprint, ())
                          if encoded == other)
    return tuple(duplicates)


__all__ = (
    "LowerTierSupportError", "ROOT", "SupportSelection", "previous_rows",
    "previous_seed_paths", "select_support", "statement_duplicates",
)
