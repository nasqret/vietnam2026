"""Exact combined source map; no proof checker or admission capability."""

from collections import Counter
from hashlib import sha256
import sys

import pytest

import working_shift_scalar_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


@pytest.fixture(scope="module")
def rows():
    return notation.source_rows()


@pytest.fixture(scope="module")
def audit():
    return notation.audit()


def _authority_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_", "build_peano_library_channels"))}


@pytest.fixture(autouse=True)
def unchanged_sources_and_no_alpha_imports():
    before, modules = notation.require_sources(), _authority_modules()
    yield
    assert notation.require_sources() == before
    assert _authority_modules() == modules


def test_literal25_inventory_and_existing_scalar_definition(rows, audit):
    assert len(rows) == 25 and sum(len(row.dependencies) for row in rows) == 81
    assert sum(len(row.script) for row in rows) == 1778
    assert rows[:15] == notation.shift.source_rows()
    assert audit["working_family_counts"] == {"shift": 15, "scalar": 10}
    assert audit["ordered_specs_sha256"] == "15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981"
    assert audit["registry_definition_count"] == 398 and audit["registry_expansion_edge_count"] == 867
    assert audit["new_definition_count"] == 1 and audit["new_scalar_definitions"] == 0
    scale = notation.shift.DEFINITIONS["FpPolyScale"]
    assert scale is notation.shift.previous["FpPolyScale"] and scale.stable_id == "ND0271"
    assert audit["source_pins"] == notation.require_sources()
    assert set(audit["source_pins"]) == {path.relative_to(notation.ROOT).as_posix() for path in notation.SOURCES}


@pytest.mark.parametrize("index", range(25))
def test_all_actual_statements_and_scripts_roundtrip(rows, audit, index):
    source, node = rows[index], audit["nodes"][index]
    reading = node["defined"]
    assert node["statement"] == source.statement and node["script"] == list(source.script)
    assert node["dependencies"] == list(source.dependencies)
    assert reading["free_names"] == [] and reading["exact_ast_equivalence"] is True
    parsed = _LocalDefinedParser(reading["defined_statement"], notation.shift.DEFINITIONS).parse()
    original = parse_formula_in_context(source.statement, [])
    assert FormulaArena().freeze(parsed).to_json() == FormulaArena().freeze(original).to_json()
    assert reading["expanded_statement_sha256"] == sha256(source.statement.encode()).hexdigest()
    statement_uses = Counter(part["definition"] for part in reading["statement_parts"] if part["kind"] == "definition")
    script_uses = Counter()
    for command, rendered, parts in zip(source.script, reading["defined_script"], reading["script_parts"], strict=True):
        assert rendered == "".join(part["text"] for part in parts)
        script_uses.update(part["definition"] for part in parts if part["kind"] == "definition")
        if command != rendered:
            assert command.partition(" ")[0] in {"have", "suffices"}
            parser = _LocalDefinedParser(rendered.partition(":")[2].strip(), notation.shift.DEFINITIONS)
            named = parser.parse()
            core = parse_formula_in_context(command.partition(":")[2].strip(), parser.free)
            assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(core).to_json()
    assert statement_uses == reading["statement_definition_uses"]
    assert script_uses == reading["script_definition_uses"]
    assert statement_uses + script_uses == reading["definition_uses"]


def test_source_graph_never_turns_notation_or_unresolved_parents_into_a_proof(rows, audit):
    proofs = [edge for edge in audit["edges"] if edge["kind"] == "proof_dependency"]
    assert len(proofs) == audit["proof_dependency_count"] == 81
    assert proofs == [{"kind": "proof_dependency", "source": parent, "target": row.name}
                      for row in rows for parent in row.dependencies]
    names = {row.name for row in rows}
    assert audit["external_dependencies"] == sorted({parent for row in rows for parent in row.dependencies if parent not in names})
    assert audit["external_dependencies_resolved"] is False
    assert audit["path_policy"] == "proof_dependency_edges_only"
    for name, path in audit["proof_paths"].items():
        assert path[-1] == name and set(path) <= names
        for left, right in zip(path, path[1:]):
            assert left in next(row for row in rows if row.name == right).dependencies
    for key in ("proof_acceptance_performed", "admission_performed", "publication_performed",
                "associativity_proved", "gcd_bezout_proved"):
        assert audit[key] is False
    assert audit["authority"] == "source-syntax-only"


def test_every_scalar_row_uses_reviewed_vocabulary_without_a_new_scalar_alias(audit):
    used = set().union(*(node["defined"]["definition_uses"].keys() for node in audit["nodes"][15:]))
    assert "ND0271" in used
    assert used <= {item.stable_id for item in notation.shift.previous.values()}
    definitions = {row["id"]: row for row in audit["definitions"]}
    assert "ND0271" in definitions and "ND0341" in definitions
    assert all(edge["target"] in definitions for edge in audit["edges"] if edge["kind"] == "uses_definition")


@pytest.mark.parametrize("path", tuple(notation.SOURCES), ids=lambda path: path.name)
def test_every_frozen_source_and_test_pin_is_mandatory(monkeypatch, path):
    replacement = dict(notation.SOURCES)
    size, _digest = replacement[path]
    replacement[path] = (size, "0" * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, "SOURCES", replacement)
        with pytest.raises(notation.shift.NotationError, match="source or independent test changed"):
            notation.source_rows()


def test_factory_loading_uses_no_package_alias_or_source_rewrite(rows):
    assert len(rows) == 25
    assert "working_scalar_notation_source_v1" not in sys.modules
    assert "peano_lab.library.prime_field_polynomial_scalar_convolution_candidate" not in sys.modules
