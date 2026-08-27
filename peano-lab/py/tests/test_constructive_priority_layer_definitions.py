"""Exact ASTs, historical identities, and noncircular campaign notation."""

from collections import Counter
from dataclasses import replace
from importlib import import_module
import json
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_lower_layer_definition_graph as prior_graph
import constructive_priority_layer_definition_graph as graph
from constructive_lower_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_priority_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, PRIORITY_LAYER_DEFINITIONS as NEW,
    PRIORITY_LAYER_REGISTRIES, definition_closure,
)
from constructive_priority_layer_defined_adapter import compact_formula_source, compact_tactic_command
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library.theorems import TheoremSpec


MODULES = (
    "prime_valuation_support_candidate", "euler_totient_count_candidate",
    "euler_totient_interval_candidate", "euler_totient_prime_step_candidate",
    "euler_totient_algebra_candidate", "euler_totient_product_candidate",
    "squarefree_decomposition_candidate", "perfect_power_profile_candidate",
    "odd_prime_lte_candidate", "continued_fraction_approximation_candidate",
    "continued_fraction_convergents_candidate",
)
ROWS = tuple(row for module in MODULES
             for row in getattr(import_module("peano_lab.library." + module), "make_" + module + "_theorems")(TheoremSpec))


def test_all_historical_objects_and_registry_records_are_unchanged():
    old, _, _ = prior_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 233
    assert len(current) == len(ALL) == 264
    assert len(NEW) == 31
    assert all(ALL[name] is definition for name, definition in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert tuple(definition.stable_id for definition in NEW) == tuple(f"ND{i:04d}" for i in range(177, 208))
    assert len({definition.stable_id for definition in ALL.values()}) == len(ALL)
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[dependency]+1 for dependency in current[name]["dependencies"]), default=0)
        assert "proof_dependency" not in current[name]
        seen.add(name)
    assert Counter(item.name for _, definitions in PRIORITY_LAYER_REGISTRIES for item in definitions) == Counter(item.name for item in NEW)


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_template_call_is_the_exact_original_ast(definition):
    parser = _LocalDefinedParser(f"{definition.name}({','.join(definition.parameters)})", ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters
    assert parse_formula_in_context(definition.template_source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_nested_binders_and_repeated_compound_arguments_are_hygienic(definition):
    arguments = tuple(("x", "y", "S (x + y)", "x * x")[i % 4] for i in range(definition.arity))
    substitutions = dict(zip(definition.parameters, arguments))
    pattern = r"\b(?:" + "|".join(re.escape(parameter) for parameter in definition.parameters) + r")\b"
    expanded = re.sub(pattern, lambda match: f"({substitutions[match.group()]})", definition.template_source)
    exact = parse_formula_in_context(f"forall x. exists y. ({expanded})", [])
    assert _LocalDefinedParser(f"forall x. exists y. {definition.name}({','.join(arguments)})", ALL).parse() == exact
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}()", ALL).parse()


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_definition_expansions_use_only_actual_ancestors(definition):
    definitions = definition_closure(definition.conceptual_dependencies)
    compact = _FormulaCompactor(definitions).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert definition.stable_id not in compact["statement_definition_uses"]
    assert set(compact["statement_definition_uses"]) <= {item.stable_id for item in definitions}


@pytest.mark.parametrize("mutation", ("cycle", "unknown", "duplicate_id", "changed_ast"))
def test_invalid_registry_extensions_fail_closed(mutation):
    selected = ALL["PrimeValuationSupport"]
    if mutation == "cycle":
        selected = replace(selected, conceptual_dependencies=(selected.name,))
    elif mutation == "unknown":
        selected = replace(selected, conceptual_dependencies=("UnprovedOracle",))
    elif mutation == "duplicate_id":
        selected = replace(selected, stable_id="PD0001")
    else:
        selected = replace(selected, template_source="0 = 1")
    registries = tuple((name, tuple(selected if item.name == selected.name else item for item in definitions)) for name, definitions in graph.DEFAULT_REGISTRIES)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_new_statement_has_an_exact_defined_roundtrip(row):
    compact = compact_formula_source(row.statement)
    assert compact.receipt.exact_ast_equivalence
    assert compact.expanded_source == row.statement
    assert "".join(part.text for part in compact.parts) == compact.defined_source
    assert compact.receipt.free_names == ()
    assert _LocalDefinedParser(compact.defined_source, ALL).parse() == parse_formula_in_context(row.statement, [])


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_local_proposition_has_an_exact_defined_roundtrip(row):
    for index, command in enumerate(row.script, 1):
        reading = compact_tactic_command(command, index)
        assert reading.expanded_command == command and reading.line_number == index
        assert "".join(part.text for part in reading.parts) == reading.defined_command
        if reading.proposition is not None:
            proposition = reading.proposition
            assert proposition.receipt.exact_ast_equivalence
            exact, names = parse_formula_with_names(proposition.expanded_source)
            parser = _LocalDefinedParser(proposition.defined_source, ALL)
            parser.free = list(names)
            assert parser.parse() == exact and tuple(parser.free) == names


def test_count_product_profile_and_computation_are_non_circular():
    phi = {d.name for d in definition_closure(("Phi",))}
    product = {d.name for d in definition_closure(("EulerProduct",))}
    convergent = {d.name for d in definition_closure(("Convergent",))}
    assert {"UnitBitPrefix", "UnitCount", "Coprime", "Sum"} <= phi
    assert not {"EulerProduct", "EulerPrimePowerFactor", "PrimeValuationSupport"} & phi
    assert {"PrimeValuationSupport", "PrimeDivisorSupport", "PrimeExponentEntries", "EulerFactorPrefix", "Product"} <= product
    assert "Phi" not in product and "UnitCount" not in product
    assert {"ConvergentMatrixTrace", "ConvergentMatrixAt", "ConvergentMatrixCode", "NaturalPair", "ListCell"} <= convergent
    assert not {"BestApproximationSecondKind", "SignedBestApproximationSecondKind", "ConvergentErrorInvariant", "AlternatingConvergentIdentity"} & convergent
    profile = {d.name for d in definition_closure(("PowerProfile",))}
    assert {"PrimeValuationSupport", "PrimeExponentPrefixGCD", "PerfectPowerRootTable", "PerfectPowerProfileCode", "NaturalPair"} <= profile


def test_polynomial_squarefree_homonym_is_not_silently_reused():
    assert "NaturalSquarefreeDecomposition" in ALL
    assert "SquarefreeDecomposition" not in ALL
    campaign = json.loads((ROOT / "book/_static/constructive-grand-campaign/campaign.json").read_text())
    assert campaign["definitions"]["SquarefreeDecomposition"]["parameters"] == ["f", "F", "w"]


def test_old_positive_numerator_plan_is_not_granted_a_matching_definition_link():
    campaign = json.loads((ROOT / "book/_static/constructive-grand-campaign/campaign.json").read_text())
    # Independently recreate the old planning-only record even after a later
    # additive atlas publication refines it and preserves its historical copy.
    campaign["definitions"]["Convergent"] = {
        "parameters": ["s", "i", "u", "v"], "meaning": "Finite convergent.",
        "expansion": "u,v>0 are obtained by the explicit two-term numerator and denominator recurrences",
    }
    with pytest.raises(graph.DefinitionGraphError, match="excludes 0/1"):
        graph.build_definition_graph(campaign)


@pytest.mark.parametrize("name,required", (
    ("totient_euler_product_formula", ("PrimeFactorList(", "Phi(", "EulerProduct(")),
    ("positive_squarefree_kernel_and_power_profile", ("Squarefree(", "PowerProfile(")),
    ("odd_prime_lifting_the_exponent", ("Prime(", "BoundedPowerValuation(", "LiftedPowerDifference(")),
    ("continued_fraction_convergent_best_approximation", ("ContinuedFraction(", "Convergent(", "BestApproximationSecondKind(")),
))
def test_principal_endpoints_have_short_exact_defined_readings(name, required):
    row = next(item for item in ROWS if item.name == name)
    surface = compact_formula_source(row.statement).defined_source
    assert all(token in surface for token in required), surface
    assert len(surface) < 1400
