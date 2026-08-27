"""Exact notation, stable identities, capture safety, and separate DAG edges."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_second_wave_definition_graph as prior_graph
import constructive_lower_layer_definition_graph as graph
from constructive_second_wave_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_lower_layer_defined_adapter import compact_formula_source, compact_tactic_command
from constructive_lower_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, LOWER_LAYER_DEFINITIONS as NEW,
    LOWER_LAYER_REGISTRIES, definition_closure,
)
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library.campaign_lower_layer_closure import lower_layer_specs


ROWS = lower_layer_specs()


def test_historical_objects_identifiers_and_reviewed_records_are_preserved():
    old, _, _ = prior_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 198
    assert len(current) == len(ALL) == len(PRIOR) + len(NEW)
    assert all(ALL[name] is definition for name, definition in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert tuple(definition.stable_id for definition in NEW) == tuple(f"ND{index:04d}" for index in range(142, 142 + len(NEW)))
    assert len({definition.stable_id for definition in ALL.values()}) == len(ALL)
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[dependency] + 1 for dependency in current[name]["dependencies"]), default=0)
        assert "proof_dependency" not in current[name]
        seen.add(name)
    assert Counter(item.name for _, definitions in LOWER_LAYER_REGISTRIES for item in definitions) == Counter(item.name for item in NEW)


def test_dependency_closure_is_scoped_and_has_no_unrelated_domain_aliases():
    definitions = definition_closure(("InitialPrimeList", "PowTwo", "InitialPrimeList"))
    names = [item.name for item in definitions]
    assert len(names) == len(set(names))
    assert {"InitialPrimeList", "InitialPrimeChain", "NextPrime", "PowTwo"} <= set(names)
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
    selected = next(item for item in NEW if item.name == "NextPrime")
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


def test_both_rings_reuse_exactly_the_same_carrier_and_additive_objects():
    from peano_lab.library.eisenstein_euclidean_candidate import (
        eisenstein_add_relation, eisenstein_integer_relation,
    )

    for name, builder in (("ZPairValid", eisenstein_integer_relation), ("ZPairAdd", eisenstein_add_relation)):
        definition = ALL[name]
        source = builder(*definition.parameters, tag="shared_carrier", variables=definition.parameters)
        assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula
    assert not {"EAdd", "EInteger", "GInteger", "EDecode", "GDecode"} & ALL.keys()
    assert ALL["GNorm"].template_formula != ALL["ENorm"].template_formula
    assert ALL["GMul"].template_formula != ALL["EMul"].template_formula
    for name in ("GNorm", "ENorm", "GMul", "EMul"):
        assert any(item is ALL["ZPairRep"] for item in definition_closure((name,)))


def test_factorization_has_no_sortedness_or_hidden_permutation_conclusion():
    factors = {item.name for item in definition_closure(("PrimeFactorList",))}
    assert {"Product", "AllPrime", "Prime", "BetaAt"} <= factors
    assert not {"Sorted", "PermutationPrefix", "PrimeFactorListPermutation"} & factors
    matching = {item.name for item in definition_closure(("PrimeFactorListPermutation",))}
    assert {"BoundedPrefix", "InjectivePrefix", "SurjectivePrefix", "FactorListMatching"} <= matching
    assert not {"Factorization", "Permutation", "PrimeList"} & ALL.keys()
    assert ALL["PrimeFactorList"].arity == 4
    assert ALL["PrimeFactorListPermutation"].arity == 8
    assert ALL["InitialPrimeList"].arity == 3


def test_prime_list_does_not_assume_its_power_bound_or_omit_minimality():
    names = {item.name for item in definition_closure(("InitialPrimeList",))}
    assert {"NextPrime", "Prime", "BetaAt", "Lt", "Le"} <= names
    assert not {"PowTwo", "Pow", "BertrandChain", "BertrandWindow"} & names
    row = next(row for row in ROWS if row.name == "first_primes_double_exponential_bound")
    surface = compact_formula_source(row.statement).defined_source
    assert "InitialPrimeList(" in surface and surface.count("PowTwo(") == 2
    assert "BertrandChain(" not in surface and len(surface) < 250


@pytest.mark.parametrize("name, relation", (
    ("gaussian_euclidean_division_exists", "GEuclideanDivision"),
    ("eisenstein_euclidean_division_exists", "EEuclideanDivision"),
))
def test_actual_ring_roots_are_short_in_exact_defined_notation(name, relation):
    row = next(row for row in ROWS if row.name == name)
    surface = compact_formula_source(row.statement).defined_source
    assert surface.count("ZPairValid(") == 2 and relation + "(" in surface
    assert len(surface) < 180
    before_output = surface.split("∃", 1)[0]
    assert "Norm(" not in before_output and "Division(" not in before_output


def test_new_registry_uses_the_unchanged_historical_compaction_engine():
    from hashlib import sha256
    import json

    catalog = json.loads((ROOT / "artifacts/peano-library/alpha/catalog-v27.json").read_bytes())
    documents = {row["path"]: row for row in catalog["evidence_documents"]}
    for name in ("scripts/constructive_formula_compactor.py", "scripts/constructive_second_wave_definitions.py",
                 "scripts/constructive_second_wave_explorer_renderer.py"):
        data = (ROOT / name).read_bytes()
        assert len(data) == documents[name]["bytes"]
        assert sha256(data).hexdigest() == documents[name]["sha256"]
