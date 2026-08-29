"""Exact conservative abbreviation identities, hygiene, and genuine DAGs."""

from collections import Counter
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_bottom_layer_definition_graph as prior_graph
import constructive_lower_tier_definition_graph as graph
from constructive_bottom_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_lower_tier_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, LOWER_TIER_DEFINITIONS as NEW,
    LOWER_TIER_REGISTRIES, definition_closure,
)
from constructive_lower_tier_defined_adapter import compact_formula_source
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library import prime_field_polynomial_candidate as polynomial


def test_all_318_historical_identities_and_actual_edges_remain_literal():
    old, _, _ = prior_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(old) == len(PRIOR) == 318
    assert all(ALL[name] is item for name, item in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert len(ALL) == len(current) == 318 + len(NEW)
    assert len({item.stable_id for item in ALL.values()}) == len(ALL)
    assert tuple(item.stable_id for item in NEW) == tuple(f"ND{i:04d}" for i in range(262, 262 + len(NEW)))
    assert Counter(item.name for _, items in LOWER_TIER_REGISTRIES for item in items) == Counter(item.name for item in NEW)
    seen = set()
    for identifier in order:
        assert set(current[identifier]["dependencies"]) <= seen
        assert layers[identifier] == max((layers[dep] + 1 for dep in current[identifier]["dependencies"]), default=0)
        seen.add(identifier)


def test_no_new_notation_clones_any_existing_or_new_definition():
    seen = list(PRIOR.values())
    for item in NEW:
        for earlier in seen:
            if item.arity == earlier.arity:
                assert item.template_formula != earlier.template_formula, (item.name, earlier.name)
        seen.append(item)
    assert "FpCoefficients" not in ALL
    assert ALL["Horner"] is PRIOR["Horner"]
    assert ALL["CanonicalModularResidue"] is PRIOR["CanonicalModularResidue"]


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_new_template_expands_to_its_exact_ha_ast(definition):
    parser = _LocalDefinedParser(f"{definition.name}({','.join(definition.parameters)})", ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters
    assert parse_formula_in_context(definition.template_source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_nested_binders_and_repeated_compound_arguments_are_hygienic(definition):
    arguments = tuple(("x", "y", "S (x+y)", "x*x")[index % 4] for index in range(definition.arity))
    substitutions = dict(zip(definition.parameters, arguments, strict=True))
    pattern = r"\b(?:" + "|".join(re.escape(parameter) for parameter in definition.parameters) + r")\b"
    expanded = re.sub(pattern, lambda match: f"({substitutions[match.group()]})", definition.template_source)
    expected = parse_formula_in_context(f"forall x. exists y. ({expanded})", [])
    assert _LocalDefinedParser(f"forall x. exists y. {definition.name}({','.join(arguments)})", ALL).parse() == expected
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}()", ALL).parse()


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_declared_definition_edge_actually_occurs_in_the_expansion(definition):
    ancestors = definition_closure(definition.conceptual_dependencies)
    compact = _FormulaCompactor(ancestors).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert definition.stable_id not in compact["statement_definition_uses"]
    for name in definition.conceptual_dependencies:
        child = ALL[name]
        isolated = _FormulaCompactor((child,)).compact(definition.template_source)
        assert isolated["exact_ast_equivalence"] is True
        assert child.stable_id in isolated["statement_definition_uses"], (definition.name, name)


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_readable_notation_round_trips_full_parameter_context(definition):
    compact = compact_formula_source(definition.template_source)
    assert compact.receipt.exact_ast_equivalence is True
    assert compact.expanded_source == definition.template_source
    assert compact.receipt.definition_uses


def test_canonical_coefficients_reuse_one_generic_prefix_bound_with_explicit_alignment():
    item = ALL["BetaPrefixInto"]
    assert item.parameters == ("b", "c", "l", "B")
    source = polynomial.prime_field_polynomial_coefficients_relation(
        "B", "b", "c", "l", tag="alignment", variables=item.parameters)
    assert parse_formula_in_context(source, list(item.parameters)) == item.template_formula
    equality = ALL["BetaPrefixEqual"]
    source = polynomial.prime_field_polynomial_equal_relation(
        *equality.parameters, tag="alignment", variables=equality.parameters)
    assert parse_formula_in_context(source, list(equality.parameters)) == equality.template_formula


@pytest.mark.parametrize("names", [("MissingNotation",), ("ArithTable", "not_reviewed")])
def test_unknown_definition_cannot_enter_a_closure(names):
    with pytest.raises(ValueError, match="unknown or cyclic"):
        definition_closure(names)
