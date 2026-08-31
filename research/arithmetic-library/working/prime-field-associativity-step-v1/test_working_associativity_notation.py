"""Independent conservative-notation checks; never mathematical authority."""

from collections import Counter
from hashlib import sha256
import sys

import pytest

import working_associativity_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena

NEW_NAMES = (
    "prime_field_polynomial_shift_equivalent_congruent",
    "prime_field_polynomial_convolution_shift_scale_aligned_equivalent",
    "prime_field_polynomial_shift_scale_aligned_congruent",
    "prime_field_polynomial_convolution_associativity_append_step",
)


def _authorities():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_",
                                "build_peano_library_channels", "verify_peano_library_channels"))}


@pytest.fixture(autouse=True)
def source_and_authority_bindings_are_preserved():
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


def test_exact35_route_preserves_frozen31_in_source_order(rows, audit):
    assert rows[:31] == notation.previous.source_rows()
    assert tuple(row.name for row in rows[31:]) == NEW_NAMES
    assert len(rows) == 35 and sum(len(row.dependencies) for row in rows) == 166
    assert sum(len(row.script) for row in rows) == 3916
    assert audit["ordered_specs_sha256"] == "60a14dc8aecb17f7a2e5f43ccb11d05f520e0277e6604e51c8440974640dbba9"
    assert audit["working_family_counts"] == {
        "shift": 15, "scalar": 10, "append": 6, "shift_equivalence": 1, "associativity_step": 3,
    }
    assert audit["source_pins"] == notation.require_sources()
    assert len(audit["source_pins"]) == 14


@pytest.mark.parametrize("index", range(35))
def test_every_actual_statement_and_local_formula_has_the_same_core_ast(rows, audit, index):
    row, node = rows[index], audit["nodes"][index]
    reading = node["defined"]
    assert node["statement"] == row.statement and node["script"] == list(row.script)
    assert node["dependencies"] == list(row.dependencies)
    assert reading["free_names"] == [] and reading["exact_ast_equivalence"] is True
    named = _LocalDefinedParser(reading["defined_statement"], notation.shift.DEFINITIONS).parse()
    raw = parse_formula_in_context(row.statement, [])
    assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert reading["expanded_statement_sha256"] == sha256(row.statement.encode()).hexdigest()
    statements = Counter(part["definition"] for part in reading["statement_parts"]
                         if part["kind"] == "definition")
    commands = Counter()
    for original, rendered, parts in zip(row.script, reading["defined_script"],
                                          reading["script_parts"], strict=True):
        assert rendered == "".join(part["text"] for part in parts)
        commands.update(part["definition"] for part in parts if part["kind"] == "definition")
        if rendered != original:
            assert original.partition(" ")[0] in {"have", "suffices"}
            parser = _LocalDefinedParser(rendered.partition(":")[2].strip(), notation.shift.DEFINITIONS)
            named = parser.parse()
            raw = parse_formula_in_context(original.partition(":")[2].strip(), parser.free)
            assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert statements == reading["statement_definition_uses"]
    assert commands == reading["script_definition_uses"]
    assert statements + commands == reading["definition_uses"]


def test_all_three_arrow_kinds_have_their_actual_and_separate_meanings(rows, audit):
    actual = [{"kind": "proof_dependency", "source": parent, "target": row.name}
              for row in rows for parent in row.dependencies]
    assert [edge for edge in audit["edges"] if edge["kind"] == "proof_dependency"] == actual
    assert len(actual) == audit["proof_dependency_count"] == 166
    by_name = {row.name: row for row in rows}
    assert audit["external_dependencies"] == sorted({parent for row in rows
        for parent in row.dependencies if parent not in by_name})
    assert audit["external_dependencies_resolved"] is False
    assert audit["path_policy"] == "proof_dependency_edges_only"
    for name, path in audit["proof_paths"].items():
        assert path[-1] == name and set(path) <= set(by_name)
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
    assert NEW_NAMES[0] in by_name[NEW_NAMES[2]].dependencies
    assert NEW_NAMES[1] in by_name[NEW_NAMES[3]].dependencies
    assert NEW_NAMES[2] in by_name[NEW_NAMES[3]].dependencies
    definitions = {row["id"]: row for row in audit["definitions"]}
    uses = [edge for edge in audit["edges"] if edge["kind"] == "uses_definition"]
    assert len(uses) == audit["definition_use_count"]
    assert all(edge["source"] in by_name and edge["target"] in definitions for edge in uses)
    expansions = [edge for edge in audit["edges"] if edge["kind"] == "definition_uses_definition"]
    assert expansions == [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                          for row in audit["definitions"] for parent in row["dependencies"]]


def test_route_adds_no_alias_and_never_claims_step_or_full_proof_acceptance(audit):
    assert (audit["registry_definition_count"], audit["registry_expansion_edge_count"]) == (398, 867)
    assert audit["new_definition_count"] == 1
    assert audit["additional_definitions_beyond_shift"] == 0
    for name, item in notation.shift.previous.items():
        assert notation.shift.DEFINITIONS[name] is item
    assert notation.shift.DEFINITIONS["PolynomialShift"] is notation.shift.SHIFT
    assert audit["reused_definition_ids"] == {
        "shift": "ND0341", "scalar": "ND0271", "left_padding": "ND0334", "formal_equivalence": "ND0336",
    }
    assert audit["authority"] == "source-syntax-only"
    for key in ("proof_acceptance_performed", "admission_performed", "publication_performed",
                "full_induction_included", "associativity_proved", "gcd_bezout_proved"):
        assert audit[key] is False
    assert all(node["proof_acceptance_performed"] is False for node in audit["nodes"])
    assert "working_associativity_notation_bridge_v1" not in sys.modules
    assert "working_associativity_notation_step_v1" not in sys.modules
    assert "peano_lab.library.prime_field_polynomial_associativity_step_candidate" not in sys.modules


@pytest.mark.parametrize("path", tuple(notation.SOURCES), ids=lambda path: path.name)
def test_each_source_test_and_prior_map_pin_is_required(path, monkeypatch):
    replacement = dict(notation.SOURCES)
    size, _digest = replacement[path]
    replacement[path] = (size, "0" * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, "SOURCES", replacement)
        with pytest.raises(notation.shift.NotationError, match="source or independent test changed"):
            notation.source_rows()
