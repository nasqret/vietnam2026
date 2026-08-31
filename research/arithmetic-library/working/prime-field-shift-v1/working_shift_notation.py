"""Working-only hygienic shift notation and literal source dependency DAG.

The 397 canonical definitions remain identical objects. ND0341 names only an
actual copied prefix followed by zero. This module cannot admit, replay or
publish a theorem. Proof dependencies and notation edges remain disjoint.
"""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import MappingProxyType

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from constructive_polynomial_euclidean_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as previous
from constructive_polynomial_euclidean_definition_graph import DEFAULT_REGISTRIES, reviewed_registry as _registry
from constructive_formula_compactor import _FormulaCompactor
from build_constructive_polynomial_euclidean_explorer_v33 import _compact_script
from peano_lab.library.defined_syntax import _definition
from peano_lab.library.theorems import TheoremSpec

SOURCE = HERE / "prime_field_polynomial_shift_candidate.py"
SOURCE_BYTES = 29786
SOURCE_SHA256 = "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b"
SPECS_SHA256 = "beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081"
SCHEMA = "working-polynomial-shift-notation-audit-v1"
_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_]*\Z")


class NotationError(ValueError):
    """An exact source or hygienic non-authorizing notation boundary failed."""


def _check_sources():
    if (SOURCE.is_symlink() or not SOURCE.is_file() or SOURCE.stat().st_size != SOURCE_BYTES
            or sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA256):
        raise NotationError("the frozen working shift source changed")


_check_sources()
_module_spec = importlib.util.spec_from_file_location("working_shift_notation_source_v1", SOURCE)
if _module_spec is None or _module_spec.loader is None:
    raise NotationError("working shift source is not loadable")
_candidate = importlib.util.module_from_spec(_module_spec)
_module_spec.loader.exec_module(_candidate)
PARAMETERS = ("b", "c", "L", "d", "e")
SHIFT = _definition(
    stable_id="ND0341", name="PolynomialShift", parameters=PARAMETERS,
    template_source=_candidate.prime_field_polynomial_shift_relation(
        *PARAMETERS, tag="working_shift_definition", variables=PARAMETERS),
    summary="Copy the actual length-L decoded prefix and append a genuine zero at index L. "
            "The target length is S L. This is multiplication by X, not harmless leading-zero padding. "
            "Primality, canonical bounds, covariance and formal equivalence are not clauses of this graph. "
            "Raw beta codes and later entries remain unrestricted.",
    category="constructive_polynomial_shift", priority="P2",
    conceptual_dependencies=("BetaPrefixEqual", "BetaAt"),
)
if len(previous) != 397 or SHIFT.name in previous or SHIFT.stable_id in {row.stable_id for row in previous.values()}:
    raise NotationError("shift notation shadows an inherited identity")
DEFINITIONS = MappingProxyType({**previous, SHIFT.name: SHIFT})
REGISTRIES = (*DEFAULT_REGISTRIES, ("polynomial-associativity", (SHIFT,)))


def definition_closure(names):
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise NotationError("definition names must be an exact tuple of nonempty text")
    seen, active, output = set(), set(), []
    def visit(name):
        if name in seen:
            return
        if name in active or name not in DEFINITIONS:
            raise NotationError("unknown or cyclic shift definition")
        active.add(name)
        for parent in DEFINITIONS[name].conceptual_dependencies:
            visit(parent)
        active.remove(name)
        seen.add(name)
        output.append(DEFINITIONS[name])
    for name in names:
        visit(name)
    return tuple(output)


def reviewed_registry():
    _check_sources()
    records, order, layers = _registry(REGISTRIES)
    if (len(records) != 398 or sum(len(row["dependencies"]) for row in records.values()) != 867
            or any(records[name]["id"] != item.stable_id for name, item in DEFINITIONS.items())):
            raise NotationError("the exact 398-definition/867-arrow working inventory changed")
    for name in SHIFT.conceptual_dependencies:
        reading = _FormulaCompactor((DEFINITIONS[name],)).compact(SHIFT.template_source)
        if DEFINITIONS[name].stable_id not in reading["statement_definition_uses"]:
            raise NotationError("a declared shift expansion dependency has no actual occurrence")
    return records, order, layers


def source_rows():
    _check_sources()
    rows = _candidate.make_prime_field_polynomial_shift_candidate_theorems(TheoremSpec)
    digest = sha256()
    for row in rows:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    if len(rows) != 15 or digest.hexdigest() != SPECS_SHA256:
        raise NotationError("the exact 15 working shift specifications changed")
    return rows


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
    if names.intersection(by_id) or names.intersection(DEFINITIONS):
        raise NotationError("theorem names cannot shadow definition identifiers")
    nodes, proof_edges, usage_edges = [], [], []
    seen, used, external = set(), set(), set()
    paths, layers = {}, {}
    for row in rows:
        if (type(row.dependencies) is not tuple
                or any(type(name) is not str or _NAME.fullmatch(name) is None for name in row.dependencies)
                or len(row.dependencies) != len(set(row.dependencies))
                or set(row.dependencies).intersection(by_id)
                or set(row.dependencies).intersection(DEFINITIONS)):
            raise NotationError("proof prerequisites must be distinct named specifications")
        parents = [name for name in row.dependencies if name in names]
        if not set(parents) <= seen:
            raise NotationError("a supplied proof prerequisite is forward or cyclic")
        if type(row.statement) is not str or not row.statement:
            raise NotationError("an actual nonempty core statement is required")
        compact = compactor.compact(row.statement)
        if compact["free_names"] or compact["exact_ast_equivalence"] is not True:
            raise NotationError("a theorem must be closed and re-expand to its exact core AST")
        _compact_script(row, compactor, compact)
        used.update(by_id[identifier] for identifier in compact["definition_uses"])
        layers[row.name] = max((layers[name] + 1 for name in parents), default=0)
        longest = max(parents, key=lambda name: len(paths[name]), default=None)
        paths[row.name] = ([] if longest is None else paths[longest]) + [row.name]
        nodes.append({"id": row.name, "name": row.name, "statement": row.statement,
                      "dependencies": list(row.dependencies), "script": list(row.script),
                      "summary": row.summary, "defined": compact,
                      "authority": "source-syntax-only", "proof_acceptance_performed": False})
        for name in row.dependencies:
            proof_edges.append({"kind": "proof_dependency", "source": name, "target": row.name})
            if name not in names:
                external.add(name)
        for identifier, count in compact["definition_uses"].items():
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
    _check_sources()
    return {
        "schema": SCHEMA, "authority": "source-syntax-only", "proof_acceptance_performed": False,
        "admission_performed": False, "publication_performed": False,
        "registry_definition_count": 398, "registry_expansion_edge_count": 867,
        "new_definition_count": 1, "nodes": nodes, "definitions": definitions,
        "external_dependencies": sorted(external), "external_dependencies_resolved": False,
        "edges": proof_edges + usage_edges + expansion_edges,
        "proof_dependency_count": len(proof_edges), "definition_use_count": len(usage_edges),
        "definition_expansion_count": len(expansion_edges),
        "proof_layers": layers, "proof_paths": paths,
        "path_policy": "proof_dependency_edges_only",
        "proof_path_scope": "supplied_theorems_only; external prerequisites unresolved",
    }


if __name__ == "__main__":
    print(json.dumps(audit_rows(source_rows()), ensure_ascii=False, indent=2, sort_keys=True))
