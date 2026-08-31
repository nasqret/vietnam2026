"""Reuse conservative notation and audit a source-only mixed dependency DAG.

No theorem factory, proof checker, Alpha edition, admission or publisher is
called here. Exact notation expansion is not proof acceptance. The original
397 definition identities and routes are reused rather than re-registered.
Run local tools with Python -B to preserve the previous working directory.
"""

from hashlib import sha256
from pathlib import Path
import re
import sys


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PRIOR = ROOT / "research/arithmetic-library/working/prime-field-euclidean-v1"
if HERE != ROOT / "research/arithmetic-library/working/prime-field-equivalence-v1":
    raise RuntimeError("equivalence notation must remain in its owned working directory")

PRIOR_PINS = (
    ("working_euclidean_definitions.py", 7278, "aec02f0130c3bcaa0b09395874530e2d844eb583411e1a5b7f8033c3fba9c49d"),
    ("working_euclidean_definition_graph.py", 1226, "4489cec7dff3a1ea48d12725f2d28b9c9c648543d94f8ee6a7233b3350e7ba15"),
    ("prime_field_polynomial_representation_candidate.py", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
)


class NotationError(ValueError):
    """A source or conservative-notation boundary was violated."""


def _check_prior():
    for name, size, digest in PRIOR_PINS:
        path = PRIOR / name
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise NotationError("a frozen notation source changed: " + name)
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise NotationError("a frozen notation source changed: " + name)
        existing = sys.modules.get(path.stem)
        if existing is not None and Path(getattr(existing, "__file__", "")).resolve() != path:
            raise NotationError("a foreign module owns a frozen notation name: " + name)


_check_prior()
for directory in (ROOT / "peano-lab/py", ROOT / "scripts", PRIOR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import working_euclidean_definitions as previous
import working_euclidean_definition_graph as previous_graph
from constructive_formula_compactor import _FormulaCompactor
from peano_lab.library.theorems import TheoremSpec


DEFINITIONS = previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
REGISTRIES = previous_graph.DEFAULT_REGISTRIES
definition_closure = previous.definition_closure
SCHEMA = "working-polynomial-equivalence-notation-audit-v1"
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


def reviewed_registry():
    """Audit the exact inherited registry, without inventing any new alias."""
    _check_prior()
    records, order, layers = previous_graph.reviewed_registry(REGISTRIES)
    if (len(records) != 397 or len(DEFINITIONS) != 397
            or sum(len(row["dependencies"]) for row in records.values()) != 865
            or any(records[name]["id"] != item.stable_id for name, item in DEFINITIONS.items())):
        raise NotationError("the exact397 definition/865 expansion inventory changed")
    return records, order, layers


def audit_rows(rows):
    """Compact actual source specifications; expose no proof/admission status.

    Proof arrows are literal declared prerequisites, including unresolved
    external names. Paths cover supplied rows only, never notation arrows or
    an unexamined external dependency cone. This is not a public explorer.
    """
    if (type(rows) is not tuple or not rows
            or any(type(row) is not TheoremSpec for row in rows)):
        raise NotationError("an exact nonempty tuple of theorem specifications is required")
    if any(type(row.name) is not str or _NAME.fullmatch(row.name) is None for row in rows):
        raise NotationError("theorem names must be distinct identifiers")
    names = {row.name for row in rows}
    if len(names) != len(rows):
        raise NotationError("theorem names must be distinct identifiers")
    records, order, _layers = reviewed_registry()
    compactor = _FormulaCompactor(tuple(DEFINITIONS.values()))
    by_id = {item.stable_id: item.name for item in DEFINITIONS.values()}
    if names.intersection(by_id):
        raise NotationError("theorem names cannot shadow definition identifiers")
    nodes, proof_edges, usage_edges = [], [], []
    seen, used, external = set(), set(), set()
    paths, layers = {}, {}
    for row in rows:
        if (type(row.dependencies) is not tuple
                or any(type(name) is not str or _NAME.fullmatch(name) is None for name in row.dependencies)
                or len(row.dependencies) != len(set(row.dependencies))
                or set(row.dependencies).intersection(by_id)):
            raise NotationError("proof prerequisites must be distinct named specifications")
        parents = [name for name in row.dependencies if name in names]
        if not set(parents) <= seen:
            raise NotationError("a supplied proof prerequisite is forward or cyclic")
        if type(row.statement) is not str or not row.statement:
            raise NotationError("an actual nonempty core statement is required")
        compact = compactor.compact(row.statement)
        if compact["free_names"] or compact["exact_ast_equivalence"] is not True:
            raise NotationError("a theorem must be closed and re-expand to its exact core AST")
        used.update(by_id[identifier] for identifier in compact["statement_definition_uses"])
        layers[row.name] = max((layers[name] + 1 for name in parents), default=0)
        longest = max(parents, key=lambda name: len(paths[name]), default=None)
        paths[row.name] = ([] if longest is None else paths[longest]) + [row.name]
        nodes.append({"id": row.name, "name": row.name, "statement": row.statement,
                      "dependencies": list(row.dependencies), "defined": compact,
                      "authority": "source-syntax-only", "proof_acceptance_performed": False})
        for name in row.dependencies:
            proof_edges.append({"kind": "proof_dependency", "source": name, "target": row.name})
            if name not in names:
                external.add(name)
        for identifier, count in compact["statement_definition_uses"].items():
            usage_edges.append({"kind": "uses_definition", "source": row.name,
                                "target": identifier, "occurrence_count": count})
        seen.add(row.name)
    closure = definition_closure(tuple(sorted(used)))
    selected = {item.name for item in closure}
    definitions = []
    for name in order:
        if name not in selected:
            continue
        record = dict(records[name])
        record["dependencies"] = [DEFINITIONS[parent].stable_id for parent in record["dependencies"]]
        record["authority"] = "conservative-abbreviation-only"
        definitions.append(record)
    expansion_edges = [{"kind": "definition_uses_definition", "source": record["id"], "target": parent}
                       for record in definitions for parent in record["dependencies"]]
    _check_prior()
    return {
        "schema": SCHEMA, "authority": "source-syntax-only", "proof_acceptance_performed": False,
        "admission_performed": False, "publication_performed": False,
        "registry_definition_count": 397, "registry_expansion_edge_count": 865,
        "new_definition_count": 0, "nodes": nodes, "definitions": definitions,
        "external_dependencies": sorted(external), "external_dependencies_resolved": False,
        "edges": proof_edges + usage_edges + expansion_edges,
        "proof_dependency_count": len(proof_edges), "definition_use_count": len(usage_edges),
        "definition_expansion_count": len(expansion_edges),
        "proof_layers": layers, "proof_paths": paths,
        "path_policy": "proof_dependency_edges_only",
        "proof_path_scope": "supplied_theorems_only; external prerequisites unresolved",
    }


__all__ = ("DEFINITIONS", "REGISTRIES", "definition_closure", "reviewed_registry",
           "audit_rows", "NotationError", "SCHEMA")
