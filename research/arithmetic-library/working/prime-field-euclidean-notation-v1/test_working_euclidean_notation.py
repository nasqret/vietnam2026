"""Independent conservative syntax tests for the exact 95-row working map.

Expected new graphs are written in previously reviewed notation, independently
of the two public candidate builders. No proof checker, complete-cone decoder,
Alpha catalogue, receipt, or publication capability supplies test authority.
"""

import ast
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import re
import sys
from types import ModuleType

import pytest

import working_euclidean_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


EXPECTED_NEW = (
    ('ND0346', 'FpPolynomialCommonRightDivisor',
     ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'bb', 'bc', 'M'),
     ('FpPolynomialRightDivides',)),
    ('ND0347', 'FpPolynomialBezoutRepresentation',
     ('p', 'ab', 'ac', 'A', 'bb', 'bc', 'B', 'gb', 'gc', 'G',
      'ub', 'uc', 'U', 'vb', 'vc', 'V'),
     ('FpPolyProduct', 'FpPolynomialAlignedAdd')),
)
EXPECTED_COMPONENTS = (
    (0, 68, 274, 6167, '03d800eaddc4ef197ddb09781e1dd3d707602e4de5ee37a1d53129013df773c1'),
    (68, 72, 29, 947, '0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4'),
    (72, 74, 14, 236, 'f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27'),
    (74, 76, 10, 389, '22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719'),
    (76, 82, 32, 470, '736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836'),
    (82, 87, 25, 385, '815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74'),
    (87, 92, 32, 739, 'aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8'),
    (92, 95, 20, 729, 'bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564'),
)
EXPECTED_SPECS = 'b2b381d67064401d3325b464396c6d156b5fc27a56639f3909dacaa60ae83994'
BUILDERS = {
    'FpPolynomialCommonRightDivisor':
        notation.CANDIDATES['transport'].prime_field_polynomial_common_right_divisor_relation,
    'FpPolynomialBezoutRepresentation':
        notation.CANDIDATES['bezout'].prime_field_polynomial_bezout_representation_relation,
}
PRIVATE_NAMES = ('_working_euclidean_notation_prior68', *(
    '_working_euclidean_notation_' + row[0] for row in notation.FACTORIES))
FUTURE_NAMES = tuple('peano_lab.library.' + row[2] for row in notation.FACTORIES)


def _authority_modules():
    return {name: value for name, value in sys.modules.items()
            if name in (*PRIVATE_NAMES, *FUTURE_NAMES)
            or name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


@pytest.fixture(autouse=True)
def exact_inputs_and_foreign_module_owners_remain_unchanged():
    before, modules = notation.require_sources(), _authority_modules()
    yield
    assert notation.require_sources() == before
    after = _authority_modules()
    assert after.keys() == modules.keys()
    assert all(after[name] is module for name, module in modules.items())


@pytest.fixture(scope='module')
def rows():
    return notation.source_rows()


@pytest.fixture(scope='module')
def audit():
    return notation.audit()


def named(source, parameters=()):
    parser = _LocalDefinedParser(source, notation.DEFINITIONS)
    parser.free = list(parameters)
    result = parser.parse()
    assert parser.free == list(parameters)
    return result


def exact(left, right):
    arena = FormulaArena()
    assert arena.freeze(left).to_json() == arena.freeze(right).to_json()


def different(left, right):
    arena = FormulaArena()
    assert arena.freeze(left).to_json() != arena.freeze(right).to_json()


def test_exact95_inventory_preserves_the_entire68_prefix(rows, audit):
    assert rows[:68] == notation.previous.source_rows()
    assert len(rows) == len({row.name for row in rows}) == 95
    assert sum(len(row.dependencies) for row in rows) == 436
    assert sum(len(row.script) for row in rows) == 10062
    assert notation.specs_digest(rows) == EXPECTED_SPECS
    assert audit['ordered_specs_sha256'] == EXPECTED_SPECS
    assert len(audit['source_pins']) == 48
    assert audit['source_pins'] == notation.require_sources()
    assert set(notation.previous.require_sources()) < set(audit['source_pins'])


@pytest.mark.parametrize('start,end,edges,commands,digest', EXPECTED_COMPONENTS,
                         ids=lambda value: str(value))
def test_each_component_has_its_exact_ordered_frozen_source_inventory(
        start, end, edges, commands, digest, rows):
    component = rows[start:end]
    assert len(component) == end - start
    assert sum(len(row.dependencies) for row in component) == edges
    assert sum(len(row.script) for row in component) == commands
    assert notation.specs_digest(component) == digest
    assert all(type(row) is notation.TheoremSpec for row in component)


@pytest.mark.parametrize('index', range(95), ids=lambda index: f'row{index:02d}')
def test_every_statement_and_local_formula_roundtrips_exactly(index, rows, audit):
    row, node = rows[index], audit['nodes'][index]
    reading = node['defined']
    assert node['id'] == node['name'] == row.name
    assert node['statement'] == row.statement and node['script'] == list(row.script)
    assert node['dependencies'] == list(row.dependencies) and node['summary'] == row.summary
    assert reading['free_names'] == [] and reading['exact_ast_equivalence'] is True
    exact(named(reading['defined_statement']), parse_formula_in_context(row.statement, []))
    assert reading['expanded_statement_sha256'] == sha256(row.statement.encode()).hexdigest()
    statements = Counter(part['definition'] for part in reading['statement_parts']
                         if part['kind'] == 'definition')
    commands = Counter()
    assert len(reading['defined_script']) == len(reading['script_parts']) == len(row.script)
    for original, rendered, parts in zip(row.script, reading['defined_script'],
                                         reading['script_parts'], strict=True):
        assert rendered == ''.join(part['text'] for part in parts)
        commands.update(part['definition'] for part in parts if part['kind'] == 'definition')
        if original != rendered:
            assert original.partition(' ')[0] in {'have', 'suffices'}
            parser = _LocalDefinedParser(rendered.partition(':')[2].strip(), notation.DEFINITIONS)
            restored = parser.parse()
            raw = parse_formula_in_context(original.partition(':')[2].strip(), parser.free)
            exact(restored, raw)
    assert statements == reading['statement_definition_uses']
    assert commands == reading['script_definition_uses']
    assert statements + commands == reading['definition_uses']


def test_all402_prior_objects_and876_expansion_arrows_are_literal_predecessors(audit):
    assert len(notation.previous.DEFINITIONS) == 402 and len(notation.DEFINITIONS) == 404
    assert tuple(notation.REGISTRIES[:-1]) == notation.previous.REGISTRIES
    for name, definition in notation.previous.DEFINITIONS.items():
        assert notation.DEFINITIONS[name] is definition
    old = {(item.stable_id, notation.previous.DEFINITIONS[parent].stable_id)
           for item in notation.previous.DEFINITIONS.values()
           for parent in item.conceptual_dependencies}
    inherited = {(item.stable_id, notation.DEFINITIONS[parent].stable_id)
                 for name, item in notation.DEFINITIONS.items()
                 if name in notation.previous.DEFINITIONS
                 for parent in item.conceptual_dependencies}
    assert old == inherited and len(old) == 876
    assert (audit['registry_definition_count'], audit['registry_expansion_edge_count']) == (404, 879)
    assert (audit['inherited_definition_count'], audit['inherited_expansion_edge_count']) == (402, 876)
    assert audit['new_definition_count'] == 2
    assert audit['new_definition_ids'] == ['ND0346', 'ND0347']
    assert 'ND0348' not in {item.stable_id for item in notation.DEFINITIONS.values()}


@pytest.mark.parametrize('expected', EXPECTED_NEW, ids=lambda row: row[1])
def test_new_definition_identity_arity_and_actual_parent_occurrences(expected):
    identifier, name, parameters, parents = expected
    definition = notation.DEFINITIONS[name]
    assert (definition.stable_id, definition.parameters, definition.arity) == (
        identifier, parameters, len(parameters))
    assert definition.conceptual_dependencies == parents
    assert name not in notation.previous.DEFINITIONS
    assert identifier not in {item.stable_id for item in notation.previous.DEFINITIONS.values()}
    public = BUILDERS[name](*parameters, tag='independent_named_template', variables=parameters)
    exact(definition.template_formula, parse_formula_in_context(public, list(parameters)))
    for parent in parents:
        rendered = notation.shift._FormulaCompactor((notation.DEFINITIONS[parent],)).compact(
            definition.template_source)
        expected_count = 1 if parent == 'FpPolynomialAlignedAdd' else 2
        assert rendered['statement_definition_uses'] == {
            notation.DEFINITIONS[parent].stable_id: expected_count}
    for old in notation.previous.DEFINITIONS.values():
        if old.arity == definition.arity:
            different(old.template_formula, definition.template_formula)


def test_common_divisor_is_only_two_actual_right_divisibilities():
    expected = ('FpPolynomialRightDivides(p,db,dc,D,ab,ac,L) /\\ '
                'FpPolynomialRightDivides(p,db,dc,D,bb,bc,M)')
    exact(named(expected, notation.COMMON_PARAMETERS), notation.COMMON_RIGHT_DIVISOR.template_formula)
    assert notation.COMMON_RIGHT_DIVISOR.conceptual_dependencies == ('FpPolynomialRightDivides',)
    changed = ('FpPolynomialRightDivides(p,ab,ac,L,db,dc,D) /\\ '
               'FpPolynomialRightDivides(p,bb,bc,M,db,dc,D)')
    different(named(changed, notation.COMMON_PARAMETERS), notation.COMMON_RIGHT_DIVISOR.template_formula)


def test_bezout_representation_contains_two_witnessed_products_and_an_aligned_sum_only():
    expected = (
        'exists pb pc P qb qc Q. FpPolyProduct(p,ub,uc,U,ab,ac,A,pb,pc,P) /\\ '
        '(FpPolyProduct(p,vb,vc,V,bb,bc,B,qb,qc,Q) /\\ '
        'FpPolynomialAlignedAdd(p,pb,pc,P,qb,qc,Q,gb,gc,G))')
    exact(named(expected, notation.BEZOUT_PARAMETERS), notation.BEZOUT_REPRESENTATION.template_formula)
    wrong_orientation = expected.replace('p,ub,uc,U,ab,ac,A', 'p,ab,ac,A,ub,uc,U')
    different(named(wrong_orientation, notation.BEZOUT_PARAMETERS),
              notation.BEZOUT_REPRESENTATION.template_formula)
    missing_products = 'exists pb pc P qb qc Q. FpPolynomialAlignedAdd(p,pb,pc,P,qb,qc,Q,gb,gc,G)'
    different(named(missing_products, notation.BEZOUT_PARAMETERS),
              notation.BEZOUT_REPRESENTATION.template_formula)
    assert notation.BEZOUT_REPRESENTATION.conceptual_dependencies == (
        'FpPolyProduct', 'FpPolynomialAlignedAdd')


@pytest.mark.parametrize('name,position', tuple(
    (name, position) for _identifier, name, parameters, _parents in EXPECTED_NEW
    for position in range(len(parameters))))
def test_every_new_parameter_accepts_compound_terms_without_capture(name, position):
    definition = notation.DEFINITIONS[name]
    arguments = list(definition.parameters)
    term = arguments[position]
    arguments[position] = f'S (({term})+({term}))'
    application = name + '(' + ','.join(arguments) + ')'
    public = BUILDERS[name](*arguments, tag='compound_notation_test', variables=definition.parameters)
    exact(named(application, definition.parameters),
          parse_formula_in_context(public, list(definition.parameters)))


@pytest.mark.parametrize('name', tuple(BUILDERS))
def test_outer_binder_with_a_template_witness_name_is_hygienic(name):
    definition = notation.DEFINITIONS[name]
    binder = next(iter(re.findall(r'\b(?:forall|exists)\s+([A-Za-z][A-Za-z0-9_]*)',
                                  definition.template_source)))
    parameters = (binder, *definition.parameters[1:])
    public = BUILDERS[name](*parameters, tag='different_independent_tag', variables=parameters)
    application = name+'('+','.join(parameters)+')'
    exact(named('forall '+binder+'. '+application, tuple(parameters[1:])),
          parse_formula_in_context('forall '+binder+'. '+public, list(parameters[1:])))


@pytest.mark.parametrize('name', tuple(BUILDERS))
@pytest.mark.parametrize('extra', (-1, 1))
def test_named_wrong_arities_are_rejected(name, extra):
    parameters = list(notation.DEFINITIONS[name].parameters)
    arguments = parameters[:-1] if extra == -1 else [*parameters, parameters[0]]
    with pytest.raises(ValueError):
        named(name+'('+','.join(arguments)+')', tuple(parameters))


def test_no_fabricated_subtraction_or_gcd_definition_usage(audit):
    definitions = {row['id']: row for row in audit['definitions']}
    assert {'ND0343', 'ND0344', 'ND0345', 'ND0346', 'ND0347'} <= definitions.keys()
    assert definitions['ND0345']['dependencies'] == ['ND0344']
    assert definitions['ND0345']['used_in_supplied_formulas'] is False
    uses = [edge for edge in audit['edges'] if edge['kind'] == 'uses_definition']
    assert not any(edge['target'] == 'ND0345' for edge in uses)
    assert any(edge['target'] == 'ND0346' for edge in uses)
    assert any(edge['target'] == 'ND0347' for edge in uses)
    assert all(definitions[edge['target']]['used_in_supplied_formulas'] for edge in uses)
    assert audit['subtraction_render_policy'] == (
        'literal permutation alias; unchanged compactor prefers prior AlignedAdd')


def test_all_three_arrow_types_are_exact_and_paths_use_proof_edges_only(rows, audit):
    expected = [{'kind': 'proof_dependency', 'source': name, 'target': row.name}
                for row in rows for name in row.dependencies]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'proof_dependency'] == expected
    assert audit['proof_dependency_count'] == len(expected) == 436
    by_name = {row.name: row for row in rows}
    definitions = {row['id']: row for row in audit['definitions']}
    assert audit['external_dependencies'] == sorted({
        name for row in rows for name in row.dependencies if name not in by_name})
    assert audit['external_dependencies_resolved'] is False
    assert audit['external_dependencies']
    for name, path in audit['proof_paths'].items():
        assert path[-1] == name and set(path) <= by_name.keys()
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
        parents = [parent for parent in by_name[name].dependencies if parent in by_name]
        assert audit['proof_layers'][name] == max(
            (audit['proof_layers'][parent] + 1 for parent in parents), default=0)
    uses = [edge for edge in audit['edges'] if edge['kind'] == 'uses_definition']
    assert len(uses) == audit['definition_use_count']
    for edge in uses:
        assert edge['source'] in by_name and edge['target'] in definitions
        node = next(node for node in audit['nodes'] if node['id'] == edge['source'])
        assert edge['occurrence_count'] == node['defined']['definition_uses'][edge['target']]
    expansions = [{'kind': 'definition_uses_definition', 'source': row['id'], 'target': parent}
                  for row in audit['definitions'] for parent in row['dependencies']]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'definition_uses_definition'] == expansions
    assert len(expansions) == audit['definition_expansion_count']
    assert {edge['kind'] for edge in audit['edges']} == {
        'proof_dependency', 'uses_definition', 'definition_uses_definition'}
    assert audit['path_policy'] == 'proof_dependency_edges_only'
    assert audit['proof_path_scope'] == 'supplied_theorems_only; external prerequisites unresolved'


def test_source_syntax_never_claims_proof_admission_gcd_or_an_algorithm(audit):
    assert audit['authority'] == 'source-syntax-only'
    for key in ('proof_acceptance_performed', 'admission_performed', 'publication_performed',
                'complete_dependency_cone_claimed', 'gcd_bezout_proved',
                'euclidean_algorithm_constructed', 'G091_closed'):
        assert audit[key] is False
    assert all(node['proof_acceptance_performed'] is False for node in audit['nodes'])
    assert all(node['authority'] == 'source-syntax-only' for node in audit['nodes'])
    assert all(row['authority'] == 'conservative-abbreviation-only' for row in audit['definitions'])
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    assert not set(PRIVATE_NAMES + FUTURE_NAMES).intersection(sys.modules)
    tree = ast.parse((notation.HERE / 'working_euclidean_notation.py').read_text())
    called = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
              for node in ast.walk(tree) if isinstance(node, ast.Call)
              and isinstance(node.func, (ast.Name, ast.Attribute))}
    assert not called.intersection({'check_proof', 'check_bundle', 'replay', 'replay_candidate_bodies',
                                    'replay_with_bundle', 'run_lean', 'compile_proof', 'require_live',
                                    'write_text', 'write_bytes'})


@pytest.mark.parametrize('path', tuple(notation.SOURCES), ids=lambda path: path.name)
def test_every_literal_input_pin_is_required(path, monkeypatch):
    changed = dict(notation.SOURCES)
    size, _digest = changed[path]
    changed[path] = (size, '0' * 64)
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, 'SOURCES', changed)
        with pytest.raises(notation.NotationError, match='source or independent test changed'):
            notation.source_rows()


@pytest.mark.parametrize('kind', ('missing', 'directory', 'symlink'))
def test_nonordinary_source_paths_are_rejected(kind, tmp_path):
    path = tmp_path / 'source.py'
    if kind == 'directory':
        path.mkdir()
    elif kind == 'symlink':
        path.symlink_to(notation.PRIOR_SOURCE)
    with pytest.raises(ValueError, match='ordinary file'):
        notation._pin(path, notation.PRIOR_PIN)


@pytest.mark.parametrize('name', PRIVATE_NAMES + FUTURE_NAMES)
def test_private_source_execution_preserves_every_foreign_module_owner(name, monkeypatch):
    foreign = ModuleType(name)
    path = notation.WORKING / notation.FACTORIES[3][1] / (notation.FACTORIES[3][2] + '.py')
    with monkeypatch.context() as scoped:
        scoped.setitem(sys.modules, name, foreign)
        loaded = notation._load_source(path, name)
        assert loaded is not foreign and sys.modules[name] is foreign
        assert loaded.__file__ == str(path)
        assert loaded.__spec__.origin == str(path)


@pytest.mark.parametrize('case', (
    'none', 'list', 'empty', 'not-spec', 'duplicate', 'definition-name', 'definition-id',
    'definition-edge', 'definition-name-edge', 'repeated-edge', 'forward-edge',
    'name-empty', 'name-bool', 'name-spaces', 'dependency-list', 'dependency-bool',
    'dependency-empty', 'statement-empty', 'statement-bool', 'free-variable'))
def test_invalid_rows_cannot_gain_authority_from_definition_arrows(case, rows):
    first, later = rows[72], rows[73]
    bad = {
        'none': None, 'list': [first], 'empty': (), 'not-spec': (0,),
        'duplicate': (first, first),
        'definition-name': (replace(first, name='FpPolynomialCommonRightDivisor'),),
        'definition-id': (replace(first, name='ND0347'),),
        'definition-edge': (replace(first, dependencies=('ND0346',)),),
        'definition-name-edge': (replace(first, dependencies=('FpPolynomialBezoutRepresentation',)),),
        'repeated-edge': (replace(first, dependencies=('external', 'external')),),
        'forward-edge': (later, first),
        'name-empty': (replace(first, name=''),),
        'name-bool': (replace(first, name=True),),
        'name-spaces': (replace(first, name='not an identifier'),),
        'dependency-list': (replace(first, dependencies=[]),),
        'dependency-bool': (replace(first, dependencies=(True,)),),
        'dependency-empty': (replace(first, dependencies=('',)),),
        'statement-empty': (replace(first, statement=''),),
        'statement-bool': (replace(first, statement=True),),
        'free-variable': (replace(first, statement='unbound=unbound', script=()),),
    }[case]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(bad)


@pytest.mark.parametrize('label', tuple(row[0] for row in notation.FACTORIES))
@pytest.mark.parametrize('attack', ('list', 'dropped', 'changed-summary'))
def test_each_exact_component_is_reconciled_against_its_frozen_specs(label, attack, monkeypatch):
    metadata = next(row for row in notation.FACTORIES if row[0] == label)
    module, factory = notation.CANDIDATES[label], metadata[3]
    actual = getattr(module, factory)(notation.TheoremSpec)
    if attack == 'list':
        changed = list(actual)
    elif attack == 'dropped':
        changed = actual[:-1]
    else:
        changed = (replace(actual[0], summary='changed source specification'), *actual[1:])
    with monkeypatch.context() as scoped:
        scoped.setattr(module, factory, lambda _spec: changed)
        with pytest.raises(notation.NotationError, match='component specification inventory'):
            notation.source_rows()


@pytest.mark.parametrize('names', (None, [], ('unknown',), ('',), (False,)))
def test_definition_closure_rejects_unknown_or_malformed_roots(names):
    with pytest.raises(notation.NotationError):
        notation.definition_closure(names)


def test_definition_closure_preserves_all_old_parents_before_the_two_new_aliases():
    closure = notation.definition_closure(
        ('FpPolynomialCommonRightDivisor', 'FpPolynomialBezoutRepresentation',
         'FpPolynomialAlignedSubtract'))
    names = [item.name for item in closure]
    assert len(names) == len(set(names))
    assert names.index('FpPolynomialRightDivides') < names.index('FpPolynomialCommonRightDivisor')
    assert names.index('FpPolyProduct') < names.index('FpPolynomialBezoutRepresentation')
    assert names.index('FpPolynomialAlignedAdd') < names.index('FpPolynomialBezoutRepresentation')
    assert names.index('FpPolynomialAlignedAdd') < names.index('FpPolynomialAlignedSubtract')
    assert all(closure[names.index(name)] is notation.DEFINITIONS[name] for name in names)
    for position, item in enumerate(closure):
        assert set(item.conceptual_dependencies) <= set(names[:position])
