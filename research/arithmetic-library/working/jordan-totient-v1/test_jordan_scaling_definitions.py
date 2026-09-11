"""The sole scaling definition is conservative, minimal and locally scoped."""
from dataclasses import replace
from functools import lru_cache
import sys

import pytest
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.defined_syntax import parse_defined_formula
from peano_lab.library.theorems import TheoremSpec
import jordan_scaling_definition_dag as surface
from jordan_tuple_scaling_candidate import make_jordan_tuple_scaling_candidate_theorems

ROWS = make_jordan_tuple_scaling_candidate_theorems(TheoremSpec)


@lru_cache(None)
def compactor():
    return _FormulaCompactor(surface.definition_closure((
        'JordanTupleScaling', 'JordanTupleAllDivisible', 'BetaPrefixInto', 'IntegerVectorZero')))


def test_exact_append_preserves_493_historical_objects():
    assert len(surface.PREVIOUS) == 493 and len(surface.ALL_DEFINITIONS) == 494
    assert len(surface.NEW_DEFINITIONS) == 1
    assert surface.NEW_DEFINITIONS[0].stable_id == 'ND0440'
    assert surface.NEW_DEFINITIONS[0].name == 'JordanTupleScaling'
    for name, value in surface.PREVIOUS.items():
        assert surface.ALL_DEFINITIONS[name] is value
    with pytest.raises(TypeError):
        surface.ALL_DEFINITIONS['new'] = surface.NEW_DEFINITIONS[0]


def test_minimal_parents_are_actual_direct_expansion_uses():
    definition = surface.NEW_DEFINITIONS[0]
    assert definition.conceptual_dependencies == ('Lt', 'BetaAt')
    reading = _FormulaCompactor(surface.definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
    assert set(reading['statement_definition_uses']) == {
        surface.ALL_DEFINITIONS[name].stable_id for name in ('Lt', 'BetaAt')}


@pytest.mark.parametrize('row', ROWS, ids=lambda row: row.name)
def test_exact_statement_ast_roundtrip_through_local_definition_dag(row):
    formula, names = parse_formula_with_names(row.statement)
    reading = compactor().compact(row.statement)
    parser = _LocalDefinedParser(reading['defined_statement'], compactor().by_name)
    parser.free = list(names)
    assert parser.parse() == formula and tuple(parser.free) == names
    assert reading['statement_definition_uses']
    if row not in ROWS[:2]:
        assert 'ND0440' in reading['statement_definition_uses']


def test_composite_arguments_are_capture_free():
    arguments = tuple(f'(S argument{i}+argument{i+1})' for i in range(6))
    parser = _LocalDefinedParser('JordanTupleScaling(' + ','.join(arguments) + ')', compactor().by_name)
    formula = parser.parse()
    free = tuple(parser.free)
    from peano_lab.kernel.formulas import pretty_formula
    reading = compactor().compact(pretty_formula(formula, list(free)))
    replay = _LocalDefinedParser(reading['defined_statement'], compactor().by_name)
    replay.free = list(free)
    assert replay.parse() == formula and tuple(replay.free) == free


def test_definition_dag_is_topological_and_syntax_only():
    dag = surface.definition_dag()
    assert dag['syntax_only'] and not dag['alpha_admitted'] and not dag['stable_changed']
    positions = {row['id']: i for i, row in enumerate(dag['nodes'])}
    assert len(positions) == len(dag['nodes'])
    for edge in dag['edges']:
        assert edge['kind'] == 'definition_uses_definition'
        assert positions[edge['source']] < positions[edge['target']]


def test_shadows_and_duplicate_semantic_identity_are_rejected():
    with pytest.raises(ValueError):
        surface.extend_definitions(surface.ALL_DEFINITIONS)
    modified = dict(surface.PREVIOUS)
    alias = replace(surface.NEW_DEFINITIONS[0], name='AlreadyScaled', stable_id='ND9999')
    modified[alias.name] = alias
    with pytest.raises(ValueError):
        surface.extend_definitions(modified)


def test_no_global_parser_mutation_or_alpha_import():
    with pytest.raises(ValueError):
        parse_defined_formula('JordanTupleScaling(p,b,c,d,e,k)')
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
