"""Immutable frontier identities, positive-triple hygiene, and exact notation."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_definition_graph as historical  # noqa: E402
import constructive_first_wave_definition_graph as graph  # noqa: E402
from build_constructive_frontier_explorer import _custom_definitions  # noqa: E402
from build_constructive_next_layer_explorer import (  # noqa: E402
    _FormulaCompactor, _LocalDefinedParser,
)
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR,
)
from constructive_first_wave_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL,
    FIRST_WAVE_DEFINITIONS, FIRST_WAVE_DEFINITIONS_BY_NAME as NEW,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.kernel.terms import ParseError  # noqa: E402
from peano_lab.library.formula_dag import FormulaArena  # noqa: E402
from peano_lab.library.pythagorean_inverse_candidate import (  # noqa: E402
    _positive, make_pythagorean_inverse_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec  # noqa: E402


def test_sealed_v25_objects_and_graph_are_unchanged():
    old, _, _ = historical.reviewed_registry()
    current, _, _ = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 120
    assert len(ALL) == len(current) == 131
    assert all(ALL[name] is definition for name, definition in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert sha256((ROOT / "scripts/constructive_definition_graph.py").read_bytes()).hexdigest() == (
        "5438ab62656ac2b30bfabe7752704a62f39a39a429f4c670bc4f017bd0201aee"
    )


def test_all_five_historical_cf_ids_and_expansions_are_preserved():
    original = _custom_definitions()
    migrated = [definition for definition in FIRST_WAVE_DEFINITIONS if definition.stable_id.startswith("CF")]
    assert [definition.stable_id for definition in migrated] == [
        "CF0011", "CF0013", "CF0014", "CF0015", "CF0016",
    ]
    for definition in migrated:
        old = original[definition.name]
        assert definition.stable_id == old["id"]
        assert definition.parameters == tuple(old["parameters"])
        assert definition.template_source == old["expanded_template"]
        assert definition.conceptual_dependencies == tuple(old["dependency_names"])


def test_reviewed_definition_dag_is_dependency_first_and_not_a_proof_graph():
    records, order, layers = graph.reviewed_registry()
    assert sum(len(record["dependencies"]) for record in records.values()) == 231
    seen = set()
    for name in order:
        assert set(records[name]["dependencies"]) <= seen
        assert layers[name] == max(
            (layers[dependency] + 1 for dependency in records[name]["dependencies"]),
            default=0,
        )
        assert "proof_dependency" not in records[name]
        seen.add(name)
    assert records["PrimitiveTriple"]["dependencies"] == ["PrimitivePythagorean"]
    assert records["EuclidParameters"]["dependencies"] == ["Lt", "Coprime", "OppositeParity"]
    assert records["SmallerFermatFourCounterexample"]["dependencies"] == ["FermatFourCounterexample", "Lt"]


@pytest.mark.parametrize("mutation", ("cycle", "unknown", "duplicate_id", "changed_ast"))
def test_extension_rejects_invalid_definition_dags(mutation):
    selected = NEW["PrimitiveTriple"]
    if mutation == "cycle":
        selected = replace(selected, conceptual_dependencies=(selected.name,))
    elif mutation == "unknown":
        selected = replace(selected, conceptual_dependencies=("ImaginaryDefinition",))
    elif mutation == "duplicate_id":
        selected = replace(selected, stable_id="CF0011")
    else:
        selected = replace(selected, template_source="a = b")
    definitions = tuple(selected if item.name == selected.name else item for item in FIRST_WAVE_DEFINITIONS)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(historical.DEFAULT_REGISTRIES + (("pythagorean-fermat-four", definitions),))


def test_nullary_descent_keeps_its_exact_closed_signature():
    definition = NEW["FermatFourStrictDescent"]
    assert definition.parameters == ()
    compact = _FormulaCompactor(tuple(ALL.values())).compact(definition.template_source)
    assert compact["defined_statement"] == "FermatFourStrictDescent()"
    assert compact["free_names"] == []
    assert compact["exact_ast_equivalence"] is True
    assert _LocalDefinedParser("FermatFourStrictDescent()", ALL).parse() == definition.template_formula
    with pytest.raises(ParseError, match="expects 0 arguments"):
        _LocalDefinedParser("FermatFourStrictDescent(x)", ALL).parse()


def test_positive_triple_definition_is_hygienic_under_nested_binders_and_terms():
    source = f"forall x. exists y. ({_positive('x', 'y', 'S x', tag='nested')})"
    defined = "forall x. exists y. PrimitiveTriple(x,y,S x)"
    parsed = _LocalDefinedParser(defined, ALL).parse()
    assert parsed == parse_formula_in_context(source, [])
    assert NEW["PrimitiveTriple"].template_formula != NEW["PrimitivePythagorean"].template_formula
    assert NEW["PrimitiveTriple"].template_source.startswith("(~((a) = 0)")


def test_full_classification_is_short_and_expands_to_its_exact_proved_formula():
    spec = next(
        row for row in make_pythagorean_inverse_candidate_theorems(TheoremSpec)
        if row.name == "pythagorean_positive_primitive_classification"
    )
    compact = _FormulaCompactor(tuple(ALL.values())).compact(spec.statement)
    assert len(spec.statement) > 5_000
    assert len(compact["defined_statement"]) < 220
    assert "PrimitiveTriple(a,b,c)" in compact["defined_statement"]
    assert "EuclidParametrization(a,b,c)" in compact["defined_statement"]
    assert compact["exact_ast_equivalence"] is True
    formula = _LocalDefinedParser(compact["defined_statement"], ALL).parse()
    assert formula == parse_formula_in_context(spec.statement, [])
    dag = FormulaArena().freeze(formula)
    assert dag.expand() == formula
    assert dag.metrics().unique_nodes < dag.metrics().structural_occurrences
