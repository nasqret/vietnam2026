"""Exact three-graph extension, real expansion edges, and scoped readers."""

from collections import Counter
from dataclasses import replace
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_dirichlet_definition_graph as previous_graph
import constructive_dirichlet_defined_adapter as previous_adapter
import constructive_dirichlet_inverse_definition_graph as graph
import constructive_dirichlet_inverse_definitions as definitions
import constructive_dirichlet_inverse_defined_adapter as adapter
from constructive_dirichlet_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_dirichlet_inverse_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL,
    DIRICHLET_INVERSE_DEFINITIONS as NEW,
    DIRICHLET_INVERSE_REGISTRIES, definition_closure,
)
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library import dirichlet_inverse_candidate as inversion
from peano_lab.library import dirichlet_signed_unit_candidate as signed_units
from peano_lab.library.formula_dag import FormulaArena
from tests.test_constructive_dirichlet_definitions import _same_ast


EXPECTED = (
    ("SignedUnit", ("u",), signed_units.dirichlet_signed_unit_relation, ()),
    ("DirichletUnitAtOne", ("F",), inversion.dirichlet_unit_at_one_relation, ("ArithAt",)),
    ("DirichletInverse", ("N", "F", "G"), inversion.dirichlet_inverse_relation,
     ("KroneckerDeltaTable", "DirichletTable")),
)


def _independent(name, arguments):
    if name == "SignedUnit":
        return f"({arguments[0]})=2 \\/ ({arguments[0]})=1"
    if name == "DirichletUnitAtOne":
        return f"ArithAt({arguments[0]},1,2) \\/ ArithAt({arguments[0]},1,1)"
    N, F, G = arguments
    return (f"exists independent_delta. KroneckerDeltaTable({N},independent_delta) /\\ "
            f"(DirichletTable({N},{F},{G},independent_delta) /\\ "
            f"DirichletTable({N},{G},{F},independent_delta))")


def test_all_369_old_definition_objects_and_every_dag_record_are_unchanged():
    old, _, _ = previous_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 369
    assert all(ALL[name] is item for name, item in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert len(ALL) == len(current) == len({item.stable_id for item in ALL.values()}) == 372
    assert tuple(item.stable_id for item in NEW) == ("ND0313", "ND0314", "ND0315")
    assert tuple(item.name for item in NEW) == tuple(item[0] for item in EXPECTED)
    assert sum(len(row["dependencies"]) for row in old.values()) == 784
    assert sum(len(row["dependencies"]) for row in current.values()) == 787
    assert max(layers.values()) == 12
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[dep] + 1 for dep in current[name]["dependencies"]), default=0)
        seen.add(name)


def test_family_registries_partition_only_actual_new_graphs():
    assert tuple((route, len(items)) for route, items in DIRICHLET_INVERSE_REGISTRIES) == (
        ("dirichlet-signed-units", 1), ("dirichlet-triangular", 0), ("dirichlet-inverses", 2),
    )
    assert Counter(item.name for _, items in DIRICHLET_INVERSE_REGISTRIES for item in items) == Counter(item.name for item in NEW)
    assert graph.DEFAULT_REGISTRIES == previous_graph.DEFAULT_REGISTRIES + DIRICHLET_INVERSE_REGISTRIES
    with pytest.raises(TypeError):
        ALL["unreviewed"] = NEW[0]


def test_exact_definition_novelty_and_old_signed_convolution_identity_reuse():
    seen = {}
    for item in PRIOR.values():
        encoded = FormulaArena().freeze(item.template_formula).to_json()
        seen.setdefault(item.arity, set()).add(encoded)
    for item in NEW:
        encoded = FormulaArena().freeze(item.template_formula).to_json()
        assert encoded not in seen.get(item.arity, set()), item.name
        seen.setdefault(item.arity, set()).add(encoded)
    for name in ("ArithAt", "ArithTable", "ArithExtend", "ArithPositiveEqual", "SignedMul",
                 "SignedAdd", "SignedPrefixSum", "DirichletTable", "KroneckerDeltaTable"):
        assert ALL[name] is PRIOR[name]
    assert graph.REVIEWED_BLUEPRINT_ALIASES is previous_graph.REVIEWED_BLUEPRINT_ALIASES
    assert not set(item.name for item in NEW) & set(graph.REVIEWED_BLUEPRINT_ALIASES)


@pytest.mark.parametrize("name,parameters,builder,dependencies", EXPECTED, ids=lambda value: value if isinstance(value, str) else None)
def test_public_builder_and_independent_old_vocabulary_have_exact_parameter_alignment(name, parameters, builder, dependencies):
    item = ALL[name]
    assert item.parameters == parameters and item.conceptual_dependencies == dependencies
    expected = parse_formula_in_context(builder(*parameters, tag="independent", variables=parameters), list(parameters))
    parser = _LocalDefinedParser(_independent(name, parameters), PRIOR)
    parser.free = list(parameters)
    _same_ast(parser.parse(), expected)
    _same_ast(item.template_formula, expected)
    surface = _LocalDefinedParser(f"{name}({','.join(parameters)})", ALL)
    surface.free = list(parameters)
    _same_ast(surface.parse(), expected)
    assert tuple(surface.free) == tuple(parser.free) == parameters


@pytest.mark.parametrize("name,parameters,builder,dependencies", EXPECTED, ids=lambda value: value if isinstance(value, str) else None)
@pytest.mark.parametrize("kind", ("compound", "large", "zero", "repeated"))
def test_nested_bound_contexts_and_actual_zero_large_repeated_terms(name, parameters, builder, dependencies, kind):
    choices = {"compound": ("S (x+y)", "x*y", "x"),
               "large": (str(2**96+17), "x+y", "y"),
               "zero": ("0", "0", "0"), "repeated": ("x+y",) * 3}[kind]
    arguments = tuple(choices[index % len(choices)] for index in range(len(parameters)))
    raw = builder(*arguments, tag="nested", variables=("x", "y"))
    expected = parse_formula_in_context(f"forall x. exists y. ({raw})", [])
    surface = f"forall x. exists y. {name}({','.join(arguments)})"
    _same_ast(_LocalDefinedParser(surface, ALL).parse(), expected)
    independent = "forall x. exists y. (" + _independent(name, arguments) + ")"
    _same_ast(_LocalDefinedParser(independent, PRIOR).parse(), expected)


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_all_template_binder_names_can_be_free_surface_arguments_without_capture(definition):
    binders = {name for clause in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", definition.template_source)
               for name in clause.split()}
    if definition.name == "SignedUnit":
        assert binders == set()
    else:
        assert binders
    for binder in sorted(binders):
        arguments = (binder,) * definition.arity
        parser = _LocalDefinedParser(f"{definition.name}({','.join(arguments)})", ALL)
        parser.free = [binder]
        actual = parser.parse()
        independent = _LocalDefinedParser(_independent(definition.name, arguments), PRIOR)
        independent.free = [binder]
        _same_ast(actual, independent.parse())
        assert parser.free == independent.free == [binder]


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_expansion_edge_occurs_and_no_theorem_bridge_is_an_extra_edge(definition):
    compact = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    assert definition.stable_id not in compact["statement_definition_uses"]
    for name in definition.conceptual_dependencies:
        child = ALL[name]
        isolated = _FormulaCompactor((child,)).compact(definition.template_source)
        assert child.stable_id in isolated["statement_definition_uses"]
    if definition.name == "DirichletUnitAtOne":
        assert "SignedUnit" not in definition.conceptual_dependencies
        assert not _FormulaCompactor((ALL["SignedUnit"],)).compact(definition.template_source)["statement_definition_uses"]
    if definition.name == "DirichletInverse":
        assert not {"SignedUnit", "DirichletUnitAtOne"} & set(definition.conceptual_dependencies)
        assert not _FormulaCompactor((ALL["SignedUnit"], ALL["DirichletUnitAtOne"])).compact(definition.template_source)["statement_definition_uses"]


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_new_adapter_is_exact_for_each_template(definition):
    result = adapter.compact_formula_source(definition.template_source)
    assert result.receipt.exact_ast_equivalence is True
    assert result.expanded_source == definition.template_source
    assert definition.stable_id in {item.definition_id for item in result.receipt.definition_uses}
    parser = _LocalDefinedParser(result.defined_source, ALL)
    parser.free = list(result.receipt.free_names)
    _same_ast(parser.parse(), parse_formula_in_context(definition.template_source, list(parser.free)))


def test_reader_uses_identical_pure_code_with_private_scopes_and_separate_cache():
    old_formula = previous_adapter.compact_formula_source.__wrapped__
    new_formula = adapter.compact_formula_source.__wrapped__
    assert new_formula.__code__ is old_formula.__code__
    assert new_formula.__globals__ is not old_formula.__globals__
    assert new_formula.__globals__["_COMPACTOR"] is adapter._COMPACTOR
    assert old_formula.__globals__["_COMPACTOR"] is previous_adapter._COMPACTOR
    assert new_formula.__globals__["DEFINITIONS"] is adapter.DEFINITIONS
    assert old_formula.__globals__["DEFINITIONS"] is previous_adapter.DEFINITIONS
    assert adapter.compact_formula_source is not previous_adapter.compact_formula_source
    assert adapter.compact_formula_source.cache_parameters() == previous_adapter.compact_formula_source.cache_parameters()
    assert adapter.compact_tactic_command.__code__ is previous_adapter.compact_tactic_command.__code__
    assert adapter.compact_tactic_command.__globals__ is not previous_adapter.compact_tactic_command.__globals__
    assert adapter.compact_tactic_command.__globals__["compact_formula_source"] is adapter.compact_formula_source
    assert previous_adapter.compact_tactic_command.__globals__["compact_formula_source"] is previous_adapter.compact_formula_source
    assert all(item is ALL[item.name] for item in previous_adapter.DEFINITIONS)


def _new_rows():
    from export_constructive_dirichlet_inverse import authoring_rows
    return authoring_rows()


@pytest.mark.parametrize("row", _new_rows(), ids=lambda row: row.name)
def test_all_40_actual_statements_and_1712_local_commands_roundtrip(row):
    statement = adapter.compact_formula_source(row.statement)
    exact, names = parse_formula_with_names(row.statement)
    parser = _LocalDefinedParser(statement.defined_source, ALL)
    parser.free = list(names)
    _same_ast(parser.parse(), exact)
    assert tuple(parser.free) == names and statement.receipt.exact_ast_equivalence
    for line, command in enumerate(row.script, 1):
        result = adapter.compact_tactic_command(command, line)
        assert result.expanded_command == command and result.line_number == line
        if result.proposition is not None:
            proposition = result.proposition
            exact, names = parse_formula_with_names(proposition.expanded_source)
            parser = _LocalDefinedParser(proposition.defined_source, ALL)
            parser.free = list(names)
            _same_ast(parser.parse(), exact)
            assert tuple(parser.free) == names and proposition.receipt.exact_ast_equivalence
        else:
            assert result.defined_command == command


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
@pytest.mark.parametrize("arity_delta", (-1, 1))
def test_wrong_surface_arities_fail_closed(definition, arity_delta):
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}({','.join(('x',) * (definition.arity + arity_delta))})", ALL).parse()


@pytest.mark.parametrize("names", (None, True, "ArithTable", ["ArithTable"], ("",), (True,)))
def test_malformed_selection_fails_closed(names):
    with pytest.raises(ValueError, match="exact tuple"):
        definition_closure(names)


@pytest.mark.parametrize("names", (("MissingNotation",), ("DirichletInverse", "not_reviewed")))
def test_unknown_definition_is_not_accepted(names):
    with pytest.raises(ValueError, match="unknown or cyclic"):
        definition_closure(names)


def test_empty_and_repeated_closures_do_not_invent_proof_dependency_edges():
    assert definition_closure(()) == ()
    selected = definition_closure(("DirichletInverse", "DirichletInverse"))
    names = tuple(item.name for item in selected)
    assert len(names) == len(set(names))
    assert "DirichletTable" in names and "KroneckerDeltaTable" in names
    assert "SignedUnit" not in names and "DirichletUnitAtOne" not in names
    assert "DirichletGrid" not in names and "DivisorTransform" not in names
    seen = set()
    for item in selected:
        assert set(item.conceptual_dependencies) <= seen
        seen.add(item.name)


def _with_replacement(original, altered):
    return tuple((route, tuple(altered if item.name == original.name else item for item in items))
                 for route, items in graph.DEFAULT_REGISTRIES)


@pytest.mark.parametrize("attack", ("duplicate_id", "duplicate_name", "wrong_template", "wrong_formula",
                                   "missing_dependency", "self_cycle", "two_cycle", "bad_route"))
def test_hostile_identity_formula_and_topology_fail_closed(attack):
    item = NEW[0]
    if attack == "duplicate_id":
        registries = _with_replacement(item, replace(item, stable_id=PRIOR["ArithTable"].stable_id))
    elif attack == "duplicate_name":
        registries = _with_replacement(item, replace(item, name="ArithTable"))
    elif attack == "wrong_template":
        registries = _with_replacement(item, replace(item, template_source="0=1"))
    elif attack == "wrong_formula":
        registries = _with_replacement(item, replace(item, template_formula=parse_formula_in_context("0=1", [])))
    elif attack == "missing_dependency":
        registries = _with_replacement(item, replace(item, conceptual_dependencies=("MissingNotation",)))
    elif attack == "self_cycle":
        registries = _with_replacement(item, replace(item, conceptual_dependencies=(item.name,)))
    elif attack == "two_cycle":
        replacements = {NEW[0].name: replace(NEW[0], conceptual_dependencies=(NEW[1].name,)),
                        NEW[1].name: replace(NEW[1], conceptual_dependencies=(NEW[0].name,))}
        registries = tuple((route, tuple(replacements.get(entry.name, entry) for entry in items))
                          for route, items in graph.DEFAULT_REGISTRIES)
    else:
        registries = graph.DEFAULT_REGISTRIES + (("../outside", (NEW[0],)),)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


def test_runtime_selection_rejects_a_cycle_in_a_hostile_map(monkeypatch):
    item = ALL["DirichletInverse"]
    changed = dict(ALL)
    changed[item.name] = replace(item, conceptual_dependencies=(item.name,))
    monkeypatch.setattr(definitions, "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", changed)
    with pytest.raises(ValueError, match="unknown or cyclic"):
        definition_closure((item.name,))


def _small_campaign(parameters=("N", "F", "G")):
    convergent = PRIOR["Convergent"]
    return {"schema": "constructive-grand-campaign-v1", "definitions": {
        "Convergent": {"parameters": list(convergent.parameters), "meaning": convergent.summary,
                       "expansion": convergent.template_source, "reviewed_definition_id": convergent.stable_id},
        "DirichletInverse": {"parameters": list(parameters), "meaning": "Planning text is not checked evidence.",
                             "expansion": "N=N"}},
        "nodes": [{"id": "G009", "statement": "DirichletInverse(N,F,G)"}]}


def test_notation_graph_grants_no_inverse_or_admission_authority():
    data = graph.build_definition_graph(_small_campaign())
    assert (data["reviewed_definition_count"], data["reviewed_definition_edge_count"]) == (372, 787)
    assert data["compatible_reviewed_match_count"] == 2
    assert all(item["blueprint_expansion_is_kernel_checked"] is False for item in data["compatible_reviewed_matches"])
    assert all(item["authority"] == "blueprint-vocabulary-only" for item in data["definitions"])
    assert {edge["kind"] for edge in data["milestone_usage_edges"]} == {"statement_uses_definition"}
    assert "never theorem-proof dependencies" in data["authority_policy"]["notation_edges"]
    assert not {"alpha_eligible", "stable_eligible", "general_dirichlet_inverse_criterion_proved",
                "full_G009_dirichlet_convolution_theory_proved"} & data.keys()


def test_wrong_planning_arity_is_not_compatible_evidence():
    data = graph.build_definition_graph(_small_campaign(("F", "G")))
    assert data["compatible_reviewed_match_count"] == 1
    assert data["incompatible_reviewed_match_count"] == 1
    assert data["incompatible_reviewed_matches"][0]["confers_checked_evidence"] is False


def test_historical_zero_numerator_erratum_guard_is_preserved():
    campaign = _small_campaign()
    del campaign["definitions"]["Convergent"]
    with pytest.raises(graph.DefinitionGraphError, match="excludes 0/1"):
        graph.build_definition_graph(campaign)


def test_prose_keeps_codes_real_lookups_positive_window_and_free_zero_distinct():
    assert "2 (+1) and 1 (-1)" in ALL["SignedUnit"].summary
    assert "actual lookup F(1)" in ALL["DirichletUnitAtOne"].summary
    assert "not a SignedUnit or inverse subformula" in ALL["DirichletUnitAtOne"].summary
    summary = ALL["DirichletInverse"].summary
    assert "F*G=E and G*F=E" in summary and "0<n<=N" in summary
    assert "values at zero remain unrestricted" in summary
    assert "necessity requires N>0" in summary
    assert "zero-window inverse identities" in summary
