"""Actual conservative expansion DAG, full binder hygiene and no aliases."""

from collections import Counter
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_lower_tier_definition_graph as previous
import constructive_lower_continuation_definition_graph as graph
from constructive_lower_tier_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_lower_continuation_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, CONTINUATION_DEFINITIONS as NEW,
    CONTINUATION_REGISTRIES, definition_closure,
)
from constructive_lower_continuation_defined_adapter import compact_formula_source
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError


def test_all_337_prior_identities_and_actual_dag_records_remain_unchanged():
    old, _, _ = previous.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(old) == len(PRIOR) == 337
    assert all(ALL[name] is item for name, item in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert len(ALL) == len(current) == 356
    assert len({item.stable_id for item in ALL.values()}) == 356
    assert tuple(item.stable_id for item in NEW) == tuple(f"ND{i:04d}" for i in range(281, 300))
    assert Counter(item.name for _, items in CONTINUATION_REGISTRIES for item in items) == Counter(item.name for item in NEW)
    assert sum(len(row["dependencies"]) for row in current.values()) == 742
    assert max(layers.values()) == 12
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[dep] + 1 for dep in current[name]["dependencies"]), default=0)
        seen.add(name)


def test_no_new_definition_duplicates_any_existing_exact_identity():
    seen = list(PRIOR.values())
    for item in NEW:
        for earlier in seen:
            if item.arity == earlier.arity:
                assert item.template_formula != earlier.template_formula, (item.name, earlier.name)
        seen.append(item)
    for name in ("Sum", "SignedPrefixSum", "BetaAt", "BetaPrefixInto", "SignedNegate", "CanonicalModularResidue"):
        assert ALL[name] is PRIOR[name]
    assert graph.REVIEWED_BLUEPRINT_ALIASES is previous.REVIEWED_BLUEPRINT_ALIASES


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_abbreviation_has_the_exact_original_ha_expansion(definition):
    parser = _LocalDefinedParser(f"{definition.name}({','.join(definition.parameters)})", ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters
    assert parse_formula_in_context(definition.template_source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_compound_repeated_arguments_under_binders_are_hygienic(definition):
    arguments = tuple(("x", "y", "S (x+y)", "x*x")[i % 4] for i in range(definition.arity))
    substitutions = dict(zip(definition.parameters, arguments, strict=True))
    pattern = r"\b(?:" + "|".join(re.escape(name) for name in definition.parameters) + r")\b"
    expanded = re.sub(pattern, lambda match: f"({substitutions[match.group()]})", definition.template_source)
    expected = parse_formula_in_context(f"forall x. exists y. ({expanded})", [])
    assert _LocalDefinedParser(f"forall x. exists y. {definition.name}({','.join(arguments)})", ALL).parse() == expected
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}()", ALL).parse()


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_declared_expansion_arrow_really_occurs(definition):
    compact = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert definition.stable_id not in compact["statement_definition_uses"]
    for name in definition.conceptual_dependencies:
        child = ALL[name]
        actual = _FormulaCompactor((child,)).compact(definition.template_source)
        assert child.stable_id in actual["statement_definition_uses"], (definition.name, name)


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_readable_forms_preserve_full_parameter_context(definition):
    compact = compact_formula_source(definition.template_source)
    assert compact.receipt.exact_ast_equivalence is True
    assert compact.receipt.definition_uses
    assert compact.expanded_source == definition.template_source


@pytest.mark.parametrize("names", (("not_a_definition",), ("ArithTable", "not_a_definition")))
def test_unknown_notation_cannot_enter_definition_closure(names):
    with pytest.raises(ValueError, match="unknown or cyclic"):
        definition_closure(names)


def test_definition_prose_retains_the_actual_domain_and_window_guards():
    assert "For n>0" in ALL["DivisorComplement"].summary
    prefix = ALL["DivisorComplementPrefix"].summary
    assert "For n>0" in prefix and "length S n" in prefix
    assert "Prime(p), n>0 and Dvd(p,n)" in ALL["DivisorPrimeToggle"].summary
    diagonal = ALL["PolynomialDiagonalPrefix"].summary
    assert "full window l=S i" in diagonal and "l<=S i" not in diagonal


@pytest.mark.parametrize("name", ("FpMul", "BetaPrefixEqual", "ArithTableEqual"))
def test_theorem_vocabulary_reuses_existing_operations_without_new_aliases(name):
    item = ALL[name]
    assert item is PRIOR[name]
    compact = compact_formula_source(item.template_source)
    assert compact.receipt.exact_ast_equivalence is True
    assert item.stable_id in {use.definition_id for use in compact.receipt.definition_uses}
