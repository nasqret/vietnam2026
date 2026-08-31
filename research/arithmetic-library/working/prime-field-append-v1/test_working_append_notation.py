"""Independent exact-source and arrow-separation checks, never proof authority."""

from collections import Counter
from hashlib import sha256
import sys

import pytest

import working_append_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena

APPEND_NAMES = (
    "prime_field_polynomial_append_shift_constant_add",
    "prime_field_polynomial_append_shift_constant_decomposition_exists",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_shift_scale_aligned_sum_exists",
    "prime_field_polynomial_convolution_right_append_equivalent",
    "prime_field_polynomial_convolution_right_append_exists",
)


def _authorities():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_",
                                "build_peano_library_channels", "verify_peano_library_channels"))}


@pytest.fixture(autouse=True)
def sources_and_authority_modules_are_unchanged():
    before, modules = notation.require_sources(), _authorities()
    yield
    assert notation.require_sources() == before
    assert _authorities() == modules


@pytest.fixture(scope="module")
def rows():
    return notation.source_rows()


@pytest.fixture(scope="module")
def audit():
    return notation.audit()


def test_exact31_inventory_extends_frozen25_without_new_notation(rows, audit):
    assert rows[:25] == notation.previous.source_rows()
    assert tuple(row.name for row in rows[25:]) == APPEND_NAMES
    assert len(rows) == 31 and sum(len(row.dependencies) for row in rows) == 123
    assert sum(len(row.script) for row in rows) == 2656
    assert audit["ordered_specs_sha256"] == "9ae49cdf4c7d76b59171fcf3bfe099f8f20990a6b78ea1fc2c3d72f33c2a66e2"
    assert audit["working_family_counts"] == {"shift": 15, "scalar": 10, "append": 6}
    assert (audit["registry_definition_count"], audit["registry_expansion_edge_count"]) == (398, 867)
    assert audit["new_definition_count"] == 1
    assert audit["new_scalar_definitions"] == audit["new_append_definitions"] == 0
    assert audit["source_pins"] == notation.require_sources()
    assert len(audit["source_pins"]) == 8


@pytest.mark.parametrize("index", range(31))
def test_all_actual_statements_and_local_proof_formulas_roundtrip(rows, audit, index):
    row, node = rows[index], audit["nodes"][index]
    reading = node["defined"]
    assert node["statement"] == row.statement and node["script"] == list(row.script)
    assert node["dependencies"] == list(row.dependencies)
    assert reading["free_names"] == [] and reading["exact_ast_equivalence"] is True
    named = _LocalDefinedParser(reading["defined_statement"], notation.shift.DEFINITIONS).parse()
    raw = parse_formula_in_context(row.statement, [])
    assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert reading["expanded_statement_sha256"] == sha256(row.statement.encode()).hexdigest()
    statement_uses = Counter(part["definition"] for part in reading["statement_parts"] if part["kind"] == "definition")
    script_uses = Counter()
    for command, rendered, parts in zip(row.script, reading["defined_script"], reading["script_parts"], strict=True):
        assert rendered == "".join(part["text"] for part in parts)
        script_uses.update(part["definition"] for part in parts if part["kind"] == "definition")
        if command != rendered:
            assert command.partition(" ")[0] in {"have", "suffices"}
            parser = _LocalDefinedParser(rendered.partition(":")[2].strip(), notation.shift.DEFINITIONS)
            named = parser.parse()
            raw = parse_formula_in_context(command.partition(":")[2].strip(), parser.free)
            assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert statement_uses == reading["statement_definition_uses"]
    assert script_uses == reading["script_definition_uses"]
    assert statement_uses + script_uses == reading["definition_uses"]


def test_proof_paths_use_only_actual_declared_dependencies(rows, audit):
    edges = [edge for edge in audit["edges"] if edge["kind"] == "proof_dependency"]
    assert edges == [{"kind": "proof_dependency", "source": parent, "target": row.name}
                     for row in rows for parent in row.dependencies]
    assert len(edges) == audit["proof_dependency_count"] == 123
    by_name = {row.name: row for row in rows}
    assert audit["external_dependencies"] == sorted({parent for row in rows
        for parent in row.dependencies if parent not in by_name})
    assert audit["external_dependencies_resolved"] is False
    assert audit["path_policy"] == "proof_dependency_edges_only"
    for name, path in audit["proof_paths"].items():
        assert path[-1] == name and set(path) <= set(by_name)
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
    assert any(edge["source"] in by_name and edge["target"] in APPEND_NAMES
               for edge in edges if edge["source"] not in APPEND_NAMES)


def test_reused_operations_keep_their_exact_definition_objects_and_expansions(audit):
    registry = notation.shift.DEFINITIONS
    for name, item in notation.shift.previous.items():
        assert registry[name] is item
    assert registry["PolynomialShift"] is notation.shift.SHIFT
    assert not any(item.stable_id == "ND0342" for item in registry.values())
    expected = {"shift": "ND0341", "scalar": "ND0271", "left_padding": "ND0334", "formal_equivalence": "ND0336"}
    assert audit["reused_definition_ids"] == expected
    uses = set().union(*(node["defined"]["definition_uses"] for node in audit["nodes"][25:]))
    assert set(expected.values()) <= uses
    definitions = {row["id"]: row for row in audit["definitions"]}
    assert uses <= set(definitions)
    assert all(edge["target"] in definitions for edge in audit["edges"] if edge["kind"] == "uses_definition")
    expansions = [edge for edge in audit["edges"] if edge["kind"] == "definition_uses_definition"]
    assert expansions == [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                          for row in audit["definitions"] for parent in row["dependencies"]]


def test_source_map_never_claims_a_proof_admission_or_completed_future_goal(audit):
    assert audit["authority"] == "source-syntax-only"
    for key in ("proof_acceptance_performed", "admission_performed", "publication_performed",
                "associativity_proved", "gcd_bezout_proved"):
        assert audit[key] is False
    assert all(node["proof_acceptance_performed"] is False for node in audit["nodes"])
    assert "working_append_notation_source_v1" not in sys.modules
    assert "peano_lab.library.prime_field_polynomial_append_candidate" not in sys.modules


@pytest.mark.parametrize("path", tuple(notation.SOURCES), ids=lambda path: path.name)
def test_each_actual_source_and_test_pin_is_mandatory(path, monkeypatch):
    replacement = dict(notation.SOURCES)
    size, _digest = replacement[path]
    replacement[path] = (size, "0" * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, "SOURCES", replacement)
        with pytest.raises(notation.shift.NotationError, match="source or independent test changed"):
            notation.source_rows()
