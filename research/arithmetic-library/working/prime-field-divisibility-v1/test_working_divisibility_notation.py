"""Independent exact-AST, definition-hygiene and non-authorizing DAG checks."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import sys

import pytest

import working_divisibility_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


def _authorities():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


@pytest.fixture(autouse=True)
def inputs_and_authority_bindings_are_preserved():
    before, modules = notation.require_sources(), _authorities()
    yield
    assert notation.require_sources() == before and _authorities() == modules


@pytest.fixture(scope='module')
def rows():
    return notation.source_rows()


@pytest.fixture(scope='module')
def audit():
    return notation.audit()


def test_combined44_inventory_has_the_exact37_predecessor(rows, audit):
    assert rows[:37] == notation.previous.source_rows()
    assert len(rows) == 44 and sum(len(row.script) for row in rows) == 4790
    assert sum(len(row.dependencies) for row in rows) == 199
    assert audit['ordered_specs_sha256'] == '6ecade7114e2d718b6a564a19d98c981b0236e1e6c6e622caaa0dff43fc95129'
    assert len(audit['source_pins']) == 22 and audit['source_pins'] == notation.require_sources()


@pytest.mark.parametrize('index', range(44))
def test_every_statement_and_compacted_local_formula_expands_to_the_actual_core_ast(rows, audit, index):
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
        if rendered != original:
            assert original.partition(' ')[0] in {'have', 'suffices'}
            parser = _LocalDefinedParser(rendered.partition(':')[2].strip(), notation.DEFINITIONS)
            named = parser.parse()
            raw = parse_formula_in_context(original.partition(':')[2].strip(), parser.free)
            assert FormulaArena().freeze(named).to_json() == FormulaArena().freeze(raw).to_json()
    assert statements == reading['statement_definition_uses']
    assert commands == reading['script_definition_uses']
    assert statements + commands == reading['definition_uses']


def test_definition_is_a_single_new_identity_with_three_actual_expansion_parents(audit):
    assert (audit['registry_definition_count'], audit['registry_expansion_edge_count']) == (399, 870)
    assert audit['additional_definitions_beyond_shift'] == 1
    for name, item in notation.shift.DEFINITIONS.items():
        assert notation.DEFINITIONS[name] is item
    definition = notation.RIGHT_DIVIDES
    assert definition.stable_id == 'ND0342' and definition.name == 'FpPolynomialRightDivides'
    assert definition.parameters == ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L')
    assert definition.conceptual_dependencies == ('BetaPrefixInto', 'FpPolyProduct', 'PolynomialEquivalent')
    for parent in definition.conceptual_dependencies:
        rendered = notation.shift._FormulaCompactor((notation.DEFINITIONS[parent],)).compact(definition.template_source)
        assert notation.DEFINITIONS[parent].stable_id in rendered['statement_definition_uses']
    assert all('ND0342' in node['defined']['statement_definition_uses'] for node in audit['nodes'][37:])


def test_arrows_and_paths_keep_their_separate_meanings(rows, audit):
    proof = [{'kind': 'proof_dependency', 'source': name, 'target': row.name}
             for row in rows for name in row.dependencies]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'proof_dependency'] == proof
    assert len(proof) == audit['proof_dependency_count'] == 199
    by_name = {row.name: row for row in rows}
    definitions = {row['id']: row for row in audit['definitions']}
    assert audit['external_dependencies'] == sorted({name for row in rows for name in row.dependencies
                                                    if name not in by_name})
    assert audit['external_dependencies_resolved'] is False
    assert audit['path_policy'] == 'proof_dependency_edges_only'
    for name, path in audit['proof_paths'].items():
        assert path[-1] == name and set(path) <= set(by_name)
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
    uses = [edge for edge in audit['edges'] if edge['kind'] == 'uses_definition']
    assert len(uses) == audit['definition_use_count']
    assert all(edge['source'] in by_name and edge['target'] in definitions for edge in uses)
    assert [edge for edge in audit['edges'] if edge['kind'] == 'definition_uses_definition'] == [
        {'kind': 'definition_uses_definition', 'source': row['id'], 'target': parent}
        for row in audit['definitions'] for parent in row['dependencies']]
    assert 'prime_field_polynomial_convolution_associative_equivalent' in rows[-1].dependencies


def test_included_induction_and_divisibility_never_supply_proof_authority(audit):
    assert audit['full_induction_included'] is True and audit['authority'] == 'source-syntax-only'
    for key in ('proof_acceptance_performed', 'admission_performed', 'publication_performed',
                'associativity_proved', 'divisibility_proved', 'gcd_bezout_proved'):
        assert audit[key] is False
    assert all(node['proof_acceptance_performed'] is False for node in audit['nodes'])
    assert 'working_divisibility_notation_source_v1' not in sys.modules
    assert 'peano_lab.library.prime_field_polynomial_divisibility_candidate' not in sys.modules


@pytest.mark.parametrize('path', tuple(notation.SOURCES), ids=lambda path: path.name)
def test_each_actual_source_test_and_prior_map_pin_is_required(path, monkeypatch):
    replacement = dict(notation.SOURCES)
    size, _digest = replacement[path]
    replacement[path] = (size, '0' * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, 'SOURCES', replacement)
        with pytest.raises(notation.NotationError, match='source or independent test changed'):
            notation.source_rows()


@pytest.mark.parametrize('case', ('none', 'list', 'empty', 'not-spec', 'duplicate',
                                 'definition-name', 'definition-edge', 'forward-edge'))
def test_invalid_proof_graph_inputs_fail_closed(case, rows):
    first, later = rows[37], rows[40]
    bad = {
        'none': None, 'list': [first], 'empty': (), 'not-spec': (0,),
        'duplicate': (first, first),
        'definition-name': (replace(first, name='ND0342'),),
        'definition-edge': (replace(first, dependencies=('ND0342',)),),
        'forward-edge': (later, first),
    }[case]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(bad)


@pytest.mark.parametrize('case', ('bad-container', 'missing', 'cycle'))
def test_definition_closure_rejects_invalid_or_cyclic_inputs(case, monkeypatch):
    if case == 'cycle':
        definitions = dict(notation.DEFINITIONS)
        item = notation.RIGHT_DIVIDES
        definitions[item.name] = replace(item, conceptual_dependencies=(item.name,))
        monkeypatch.setattr(notation, 'DEFINITIONS', definitions)
        names = (item.name,)
    else:
        names = ['FpPolynomialRightDivides'] if case == 'bad-container' else ('MissingDefinition',)
    with pytest.raises(notation.NotationError):
        notation.definition_closure(names)
