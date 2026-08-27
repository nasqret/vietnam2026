"""Exact notation, stable identities, capture safety, and separate DAG edges."""

from __future__ import annotations

import ast
from collections import Counter
from dataclasses import replace
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_first_wave_definition_graph as prior_graph
import constructive_second_wave_definition_graph as graph
from constructive_first_wave_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_second_wave_defined_adapter import compact_formula_source, compact_tactic_command
from constructive_second_wave_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, SECOND_WAVE_DEFINITIONS as NEW,
    SECOND_WAVE_REGISTRIES, definition_closure,
)
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library.campaign_second_wave_closure import second_wave_specs
from peano_lab.library.finite_modular_set_candidate import finite_modular_set_relation


ROWS = second_wave_specs()


def test_historical_objects_identifiers_and_reviewed_records_are_preserved():
    old, _, _ = prior_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 131
    assert len(current) == len(ALL) == len(PRIOR) + len(NEW)
    assert all(ALL[name] is definition for name, definition in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert tuple(definition.stable_id for definition in NEW) == tuple(f"ND{index:04d}" for index in range(75, 75 + len(NEW)))
    assert len({definition.stable_id for definition in ALL.values()}) == len(ALL)
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[dependency] + 1 for dependency in current[name]["dependencies"]), default=0)
        assert "proof_dependency" not in current[name]
        seen.add(name)
    assert Counter(item.name for _, definitions in SECOND_WAVE_REGISTRIES for item in definitions) == Counter(item.name for item in NEW)


def test_dependency_closure_is_scoped_and_has_no_unrelated_domain_aliases():
    definitions = definition_closure(("PrimeCount", "BitLen", "PrimeCount"))
    names = [item.name for item in definitions]
    assert len(names) == len(set(names))
    assert {"PrimeCount", "PrimeBitPrefix", "Sum", "BitLen"} <= set(names)
    assert "BinaryModulus" not in names
    seen = set()
    for definition in definitions:
        assert set(definition.conceptual_dependencies) <= seen
        seen.add(definition.name)
    with pytest.raises(ValueError, match="unknown"):
        definition_closure(("UnreviewedAlias",))


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_each_template_call_expands_to_its_exact_reviewed_ast(definition):
    source = f"{definition.name}({','.join(definition.parameters)})"
    parser = _LocalDefinedParser(source, ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters
    assert parse_formula_in_context(definition.template_source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_all_definitions_are_hygienic_with_nested_binders_and_repeated_terms(definition):
    arguments = tuple(("x", "y", "S (x + y)", "x * x")[index % 4] for index in range(definition.arity))
    substitutions = dict(zip(definition.parameters, arguments))
    pattern = r"\b(?:" + "|".join(re.escape(parameter) for parameter in definition.parameters) + r")\b"
    expanded = re.sub(pattern, lambda match: f"({substitutions[match.group()]})", definition.template_source)
    exact = parse_formula_in_context(f"forall x. exists y. ({expanded})", [])
    compact = f"forall x. exists y. {definition.name}({','.join(arguments)})"
    assert _LocalDefinedParser(compact, ALL).parse() == exact
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}()", ALL).parse()


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_definition_pages_expand_through_prerequisites_not_self_aliases(definition):
    definitions = definition_closure(definition.conceptual_dependencies)
    compact = _FormulaCompactor(definitions).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert definition.stable_id not in compact["statement_definition_uses"]
    assert set(compact["statement_definition_uses"]) <= {item.stable_id for item in definitions}


@pytest.mark.parametrize("mutation", ("cycle", "unknown", "duplicate_id", "changed_ast"))
def test_invalid_definition_extensions_are_rejected(mutation):
    selected = next(item for item in NEW if item.name == "PrimeCount")
    if mutation == "cycle":
        selected = replace(selected, conceptual_dependencies=(selected.name,))
    elif mutation == "unknown":
        selected = replace(selected, conceptual_dependencies=("UnprovedNotation",))
    elif mutation == "duplicate_id":
        selected = replace(selected, stable_id="PD0001")
    else:
        selected = replace(selected, template_source="x = z")
    registries = tuple((name, tuple(selected if item.name == selected.name else item for item in definitions))
                       for name, definitions in graph.DEFAULT_REGISTRIES)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


def test_standalone_compactor_is_the_canonical_algorithm_without_edition_imports():
    old = ast.parse((ROOT / "scripts/build_constructive_next_layer_explorer.py").read_text())
    new = ast.parse((ROOT / "scripts/constructive_formula_compactor.py").read_text())
    names = {"_LocalDefinedParser", "_parts_append", "_FormulaCompactor"}

    class Normalize(ast.NodeTransformer):
        def visit_Name(self, node):
            if node.id == "NextLayerExplorerError":
                node.id = "ConservativeCompactionError"
            return node

        def visit_Constant(self, node):
            if isinstance(node.value, str):
                node.value = node.value.replace("next-layer", "local")
            return node

    canonical = {node.name: ast.dump(Normalize().visit(node), include_attributes=False)
                 for node in old.body if getattr(node, "name", None) in names}
    extracted = {node.name: ast.dump(node, include_attributes=False)
                 for node in new.body if getattr(node, "name", None) in names}
    assert canonical == extracted
    assert not any(isinstance(node, ast.ImportFrom) and "editions" in (node.module or "") for node in ast.walk(new))


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_candidate_statement_has_an_exact_defined_roundtrip(row):
    compact = compact_formula_source(row.statement)
    assert compact.receipt.exact_ast_equivalence
    assert compact.expanded_source == row.statement
    assert "".join(part.text for part in compact.parts) == compact.defined_source
    assert compact.receipt.free_names == ()
    parser = _LocalDefinedParser(compact.defined_source, ALL)
    assert parser.parse() == parse_formula_in_context(row.statement, [])


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_local_tactic_proposition_has_an_exact_defined_roundtrip(row):
    for number, command in enumerate(row.script, 1):
        reading = compact_tactic_command(command, number)
        assert reading.expanded_command == command
        assert reading.line_number == number
        assert "".join(part.text for part in reading.parts) == reading.defined_command
        if reading.proposition is None:
            assert reading.defined_command == command
        else:
            proposition = reading.proposition
            assert proposition.receipt.exact_ast_equivalence
            exact, names = parse_formula_with_names(proposition.expanded_source)
            parser = _LocalDefinedParser(proposition.defined_source, ALL)
            parser.free = list(names)
            assert parser.parse() == exact
            assert tuple(parser.free) == names


def test_chebyshev_root_displays_prime_count_and_length_without_a_foreign_guard():
    row = next(item for item in ROWS if item.name == "prime_count_chebyshev_bounds")
    surface = compact_formula_source(row.statement).defined_source
    assert "PrimeCount(N,k)" in surface and "BitLen(N,ell)" in surface
    assert "BinaryModulus" not in surface
    assert len(surface) < 160


def test_carry_count_and_cornacchia_trace_do_not_define_the_desired_conclusion():
    carry_names = {item.name for item in definition_closure(("CarryCountMany",))}
    assert not {"PowerValuation", "Multinomial", "MultinomialBinomialPrefix"} & carry_names
    trace_names = {item.name for item in definition_closure(("CornacchiaTrace",))}
    assert not {"TwoSquares", "SignedRecursiveDeterminant"} & trace_names
    assert "proved conclusion" in ALL["CornacchiaTrace"].summary
    assert "no independence, index, or covolume" in ALL["IntegerColumnSpan"].summary


def test_finite_modular_cardinality_reuses_the_exact_historical_bit_count():
    definition = ALL["BitCount"]
    source = finite_modular_set_relation(*definition.parameters, tag="reuse_audit")
    assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula
    assert "FiniteModularSet" not in ALL
