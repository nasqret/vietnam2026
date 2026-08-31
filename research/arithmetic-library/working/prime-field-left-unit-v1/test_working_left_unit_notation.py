"""Independent exact-AST and source-only DAG checks for the combined52 map."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import sys

import pytest

import working_left_unit_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


def _authorities():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


@pytest.fixture(autouse=True)
def input_bytes_and_authority_bindings_are_preserved():
    before, modules = notation.require_sources(), _authorities()
    yield
    assert notation.require_sources() == before and _authorities() == modules


@pytest.fixture(scope='module')
def rows():
    return notation.source_rows()


@pytest.fixture(scope='module')
def audit():
    return notation.audit()


def test_exact_combined52_inventory_retains_its_complete44_predecessor(rows, audit):
    assert rows[:44] == notation.previous.source_rows()
    assert len(rows) == 52 and sum(len(row.script) for row in rows) == 5256
    assert sum(len(row.dependencies) for row in rows) == 234
    assert audit['ordered_specs_sha256'] == 'c6c4b0610b911d1f17a8b0ef2b6fa4b8f7b79e73e7f1f85f0fe2d6b1a42edc63'
    assert len(audit['source_pins']) == 26 and audit['source_pins'] == notation.require_sources()


@pytest.mark.parametrize('index', range(52))
def test_every_statement_and_local_formula_roundtrips_to_exact_core_ast(rows, audit, index):
    row, node = rows[index], audit['nodes'][index]
    reading = node['defined']
    assert node['statement'] == row.statement and node['script'] == list(row.script)
    assert node['dependencies'] == list(row.dependencies)
    assert reading['free_names'] == [] and reading['exact_ast_equivalence'] is True
    named = _LocalDefinedParser(reading['defined_statement'], notation.DEFINITIONS).parse()
    raw = parse_formula_in_context(row.statement, [])
    assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert reading['expanded_statement_sha256'] == sha256(row.statement.encode()).hexdigest()
    statements = Counter(part['definition'] for part in reading['statement_parts']
                         if part['kind'] == 'definition')
    commands = Counter()
    for original, rendered, parts in zip(row.script, reading['defined_script'],
                                          reading['script_parts'], strict=True):
        assert rendered == ''.join(part['text'] for part in parts)
        commands.update(part['definition'] for part in parts if part['kind'] == 'definition')
        if original != rendered:
            assert original.partition(' ')[0] in {'have', 'suffices'}
            parser = _LocalDefinedParser(rendered.partition(':')[2].strip(), notation.DEFINITIONS)
            named = parser.parse()
            raw = parse_formula_in_context(original.partition(':')[2].strip(), parser.free)
            assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert statements == reading['statement_definition_uses']
    assert commands == reading['script_definition_uses']
    assert statements + commands == reading['definition_uses']


def test_all399_definition_objects_are_reused_and_reflexivity_uses_same_nd0342(audit):
    assert notation.DEFINITIONS is notation.previous.DEFINITIONS
    assert notation.REGISTRIES is notation.previous.REGISTRIES
    assert (audit['registry_definition_count'], audit['registry_expansion_edge_count']) == (399, 870)
    assert audit['additional_definitions_beyond_divisibility'] == 0
    for name, definition in notation.previous.DEFINITIONS.items():
        assert notation.DEFINITIONS[name] is definition
    assert 'ND0342' in audit['nodes'][-1]['defined']['statement_definition_uses']
    assert len(audit['definitions']) == 26


def test_real_proof_arrows_define_paths_not_notation_expansions(rows, audit):
    proof = [{'kind': 'proof_dependency', 'source': name, 'target': row.name}
             for row in rows for name in row.dependencies]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'proof_dependency'] == proof
    assert len(proof) == audit['proof_dependency_count'] == 234
    by_name = {row.name: row for row in rows}
    definitions = {row['id']: row for row in audit['definitions']}
    external = sorted({name for row in rows for name in row.dependencies if name not in by_name})
    assert audit['external_dependencies'] == external and len(external) == 83
    assert audit['external_dependencies_resolved'] is False
    assert audit['path_policy'] == 'proof_dependency_edges_only'
    assert max(audit['proof_layers'].values()) + 1 == 10
    for name, path in audit['proof_paths'].items():
        assert path[-1] == name and set(path) <= set(by_name)
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
    uses = [edge for edge in audit['edges'] if edge['kind'] == 'uses_definition']
    assert len(uses) == audit['definition_use_count'] == 238
    assert all(edge['source'] in by_name and edge['target'] in definitions for edge in uses)
    expansions = [{'kind': 'definition_uses_definition', 'source': row['id'], 'target': parent}
                  for row in audit['definitions'] for parent in row['dependencies']]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'definition_uses_definition'] == expansions
    assert len(expansions) == audit['definition_expansion_count'] == 46


def test_unit_and_reflexivity_are_included_without_any_proof_authority(audit):
    assert audit['full_induction_included'] is True and audit['left_unit_included'] is True
    assert audit['authority'] == 'source-syntax-only'
    for key in ('proof_acceptance_performed', 'admission_performed', 'publication_performed',
                'associativity_proved', 'divisibility_proved', 'left_unit_proved',
                'reflexive_divisibility_proved', 'gcd_bezout_proved'):
        assert audit[key] is False
    assert all(node['proof_acceptance_performed'] is False for node in audit['nodes'])
    assert 'working_left_unit_notation_source_v1' not in sys.modules
    assert 'peano_lab.library.prime_field_polynomial_left_unit_candidate' not in sys.modules


@pytest.mark.parametrize('path', tuple(notation.SOURCES), ids=lambda path: path.name)
def test_every_source_test_and_prior_map_pin_is_required(path, monkeypatch):
    altered = dict(notation.SOURCES)
    size, _digest = altered[path]
    altered[path] = (size, '0' * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, 'SOURCES', altered)
        with pytest.raises(notation.NotationError, match='source or independent test changed'):
            notation.source_rows()


@pytest.mark.parametrize('case', ('none', 'list', 'empty', 'not-spec', 'duplicate',
                                 'definition-name', 'definition-edge', 'forward-edge'))
def test_invalid_graphs_do_not_gain_validity_from_definition_edges(case, rows):
    first, later = rows[44], rows[46]
    bad = {
        'none': None, 'list': [first], 'empty': (), 'not-spec': (0,),
        'duplicate': (first, first), 'definition-name': (replace(first, name='ND0342'),),
        'definition-edge': (replace(first, dependencies=('ND0342',)),),
        'forward-edge': (later, first),
    }[case]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(bad)


def test_unit_route_is_actual_sum_then_residue_then_product_then_reflexivity(rows):
    by_name = {row.name: row for row in rows}
    chain = ('polynomial_diagonal_left_unit_first_term', 'polynomial_diagonal_left_unit_natural_sum',
             'prime_field_convolution_coefficient_left_unit',
             'prime_field_polynomial_convolution_left_unit_equal',
             'prime_field_polynomial_convolution_left_unit_equivalent',
             'prime_field_polynomial_convolution_left_unit_exists',
             'prime_field_polynomial_right_divides_reflexive')
    assert all(left in by_name[right].dependencies for left, right in zip(chain, chain[1:]))
    assert 'prime_field_polynomial_right_divides_from_product' in rows[-1].dependencies
