"""Independent syntax/DAG checks; the map itself accepts no mathematical proof."""

import sys

import pytest

import working_induction_notation as notation
import test_working_associativity_notation as previous_checks

NEW_NAMES = (
    "prime_field_polynomial_nested_empty_right_equivalent",
    "prime_field_polynomial_convolution_associative_equivalent",
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


def test_exact37_route_preserves_frozen35_and_actual_induction(rows, audit):
    assert rows[:35] == notation.previous.source_rows()
    assert tuple(row.name for row in rows[35:]) == NEW_NAMES
    assert len(rows) == 37 and sum(len(row.dependencies) for row in rows) == 179
    assert sum(len(row.script) for row in rows) == 4303
    assert audit["ordered_specs_sha256"] == "de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491"
    assert audit["working_family_counts"] == {
        "shift": 15, "scalar": 10, "append": 6, "shift_equivalence": 1,
        "associativity_step": 3, "associativity_induction": 2,
    }
    assert audit["source_pins"] == notation.require_sources()
    assert len(audit["source_pins"]) == 18


@pytest.mark.parametrize("index", range(37))
def test_every_actual_statement_and_local_formula_has_the_same_core_ast(rows, audit, index):
    # Reuse the already independent AST check, not the map's compactor or a
    # stored digest. Both maps use the identical conservative registry.
    assert notation.shift is previous_checks.notation.shift
    previous_checks.test_every_actual_statement_and_local_formula_has_the_same_core_ast(
        rows, audit, index)


def test_three_arrow_kinds_and_induction_dependency_path_are_exact(rows, audit):
    actual = [{"kind": "proof_dependency", "source": parent, "target": row.name}
              for row in rows for parent in row.dependencies]
    assert [edge for edge in audit["edges"] if edge["kind"] == "proof_dependency"] == actual
    assert len(actual) == audit["proof_dependency_count"] == 179
    by_name = {row.name: row for row in rows}
    assert audit["external_dependencies"] == sorted({parent for row in rows
        for parent in row.dependencies if parent not in by_name})
    assert audit["external_dependencies_resolved"] is False
    assert audit["path_policy"] == "proof_dependency_edges_only"
    for name, path in audit["proof_paths"].items():
        assert path[-1] == name and set(path) <= set(by_name)
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
    assert NEW_NAMES[0] in by_name[NEW_NAMES[1]].dependencies
    assert "prime_field_polynomial_convolution_associativity_append_step" in by_name[NEW_NAMES[1]].dependencies
    assert "matrix_rank_bounded_prefix_drop_last" in by_name[NEW_NAMES[1]].dependencies
    definitions = {row["id"]: row for row in audit["definitions"]}
    uses = [edge for edge in audit["edges"] if edge["kind"] == "uses_definition"]
    assert len(uses) == audit["definition_use_count"]
    assert all(edge["source"] in by_name and edge["target"] in definitions for edge in uses)
    expansions = [edge for edge in audit["edges"] if edge["kind"] == "definition_uses_definition"]
    assert expansions == [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                          for row in audit["definitions"] for parent in row["dependencies"]]


def test_including_induction_adds_no_alias_or_proof_authority(audit):
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
    assert audit["full_induction_included"] is True
    for key in ("proof_acceptance_performed", "admission_performed", "publication_performed",
                "associativity_proved", "gcd_bezout_proved"):
        assert audit[key] is False
    assert all(node["proof_acceptance_performed"] is False for node in audit["nodes"])
    assert "working_induction_notation_source_v1" not in sys.modules
    assert "peano_lab.library.prime_field_polynomial_associativity_induction_candidate" not in sys.modules


@pytest.mark.parametrize("path", tuple(notation.SOURCES), ids=lambda path: path.name)
def test_each_source_test_and_prior_map_pin_is_required(path, monkeypatch):
    replacement = dict(notation.SOURCES)
    size, _digest = replacement[path]
    replacement[path] = (size, "0" * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, "SOURCES", replacement)
        with pytest.raises(notation.shift.NotationError, match="source or independent test changed"):
            notation.source_rows()
