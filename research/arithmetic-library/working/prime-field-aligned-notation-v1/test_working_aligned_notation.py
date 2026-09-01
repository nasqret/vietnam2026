"""Independent conservative-AST and source-only alignment-DAG tests.

No proof evaluator, Alpha catalogue or receipt is used. Successful formula
roundtrips are syntax evidence only, including for the literal subtraction
permutation and every old theorem that remains in the displayed prefix.
"""

import ast
from collections import Counter
from dataclasses import replace
from hashlib import sha256
import re
import sys
from types import ModuleType

import pytest

import working_aligned_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


EXPECTED_NEW = (
    ('ND0343', 'CommonRepresentatives',
     ('ab', 'ac', 'L', 'bb', 'bc', 'M', 'ub', 'uc', 'vb', 'vc', 'K'),
     ('PolynomialEquivalent',)),
    ('ND0344', 'FpPolynomialAlignedAdd',
     ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'rb', 'rc', 'N'),
     ('BetaPrefixInto', 'CommonRepresentatives', 'FpPolyAdd', 'PolynomialEquivalent')),
    ('ND0345', 'FpPolynomialAlignedSubtract',
     ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'rb', 'rc', 'N'),
     ('FpPolynomialAlignedAdd',)),
)
BUILDERS = {
    'CommonRepresentatives': notation.alignment.prime_field_polynomial_common_representatives_relation,
    'FpPolynomialAlignedAdd': notation.aligned_add.prime_field_polynomial_aligned_add_relation,
    'FpPolynomialAlignedSubtract': notation.aligned_add.prime_field_polynomial_aligned_subtract_relation,
}


def _authority_modules():
    return {name: value for name, value in sys.modules.items()
            if name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))
            or name in ('_working_aligned_notation_alignment', '_working_aligned_notation_add',
                        'peano_lab.library.prime_field_polynomial_alignment_candidate',
                        'peano_lab.library.prime_field_polynomial_aligned_add_candidate')}


@pytest.fixture(autouse=True)
def exact_inputs_and_foreign_module_identities_remain_unchanged():
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


def test_exact68_source_inventory_preserves_all52_old_rows(rows, audit):
    assert rows[:52] == notation.previous.source_rows()
    assert len(rows) == 68
    assert sum(len(row.dependencies) for row in rows) == 274
    assert sum(len(row.script) for row in rows) == 6167
    assert notation.specs_digest(rows[52:59]) == (
        '76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec')
    assert notation.specs_digest(rows[59:]) == (
        'b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339')
    assert audit['ordered_specs_sha256'] == notation.specs_digest(rows)
    assert len(audit['source_pins']) == 32
    assert audit['source_pins'] == notation.require_sources()


@pytest.mark.parametrize('index', range(68), ids=lambda index: f'row{index:02d}')
def test_each_statement_and_local_formula_roundtrips_exactly(index, rows, audit):
    row, node = rows[index], audit['nodes'][index]
    reading = node['defined']
    assert node['statement'] == row.statement and node['script'] == list(row.script)
    assert node['dependencies'] == list(row.dependencies) and node['summary'] == row.summary
    assert reading['free_names'] == [] and reading['exact_ast_equivalence'] is True
    exact(named(reading['defined_statement']), parse_formula_in_context(row.statement, []))
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
            restored = parser.parse()
            raw = parse_formula_in_context(original.partition(':')[2].strip(), parser.free)
            exact(restored, raw)
    assert statements == reading['statement_definition_uses']
    assert commands == reading['script_definition_uses']
    assert statements + commands == reading['definition_uses']


def test_all399_prior_objects_and870_edges_are_preserved(audit):
    assert len(notation.previous.DEFINITIONS) == 399 and len(notation.DEFINITIONS) == 402
    assert tuple(notation.REGISTRIES[:-1]) == notation.previous.REGISTRIES
    for name, definition in notation.previous.DEFINITIONS.items():
        assert notation.DEFINITIONS[name] is definition
    old_edges = {(item.stable_id, notation.previous.DEFINITIONS[parent].stable_id)
                 for item in notation.previous.DEFINITIONS.values()
                 for parent in item.conceptual_dependencies}
    current_old_edges = {(item.stable_id, notation.DEFINITIONS[parent].stable_id)
                         for item in notation.DEFINITIONS.values()
                         if item.name in notation.previous.DEFINITIONS
                         for parent in item.conceptual_dependencies}
    assert old_edges == current_old_edges and len(old_edges) == 870
    assert (audit['registry_definition_count'], audit['registry_expansion_edge_count']) == (402, 876)
    assert (audit['inherited_definition_count'], audit['inherited_expansion_edge_count']) == (399, 870)
    assert audit['new_definition_count'] == 3
    assert audit['new_definition_ids'] == ['ND0343', 'ND0344', 'ND0345']


@pytest.mark.parametrize('expected', EXPECTED_NEW, ids=lambda row: row[1])
def test_new_definition_identity_arity_and_literal_parents(expected):
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
        assert notation.DEFINITIONS[parent].stable_id in rendered['statement_definition_uses']
    for old in notation.previous.DEFINITIONS.values():
        if old.arity == definition.arity:
            assert FormulaArena().freeze(old.template_formula).to_json() != (
                FormulaArena().freeze(definition.template_formula).to_json())


def test_common_is_only_the_literal_grouped_pair_of_formal_equivalences():
    expected = ('PolynomialEquivalent(ab,ac,L,ub,uc,K) /\\ '
                'PolynomialEquivalent(bb,bc,M,vb,vc,K)')
    exact(named(expected, notation.COMMON_PARAMETERS), notation.COMMON_REPRESENTATIVES.template_formula)
    assert 'p' not in notation.COMMON_REPRESENTATIVES.parameters
    assert notation.COMMON_REPRESENTATIVES.conceptual_dependencies == ('PolynomialEquivalent',)


def test_add_retains_three_original_bounds_and_real_witnesses_in_exact_order():
    expected = (
        'BetaPrefixInto(ab,ac,L,p) /\\ (BetaPrefixInto(bb,bc,M,p) /\\ '
        '(BetaPrefixInto(rb,rc,N,p) /\\ exists u v w x y z K. '
        '(CommonRepresentatives(ab,ac,L,bb,bc,M,u,v,w,x,K) /\\ '
        '(FpPolyAdd(p,u,v,w,x,y,z,K) /\\ PolynomialEquivalent(y,z,K,rb,rc,N)))))')
    exact(named(expected, notation.ALIGNED_PARAMETERS), notation.ALIGNED_ADD.template_formula)
    only_common = notation.shift._FormulaCompactor((notation.COMMON_REPRESENTATIVES,)).compact(
        notation.ALIGNED_ADD.template_source)
    assert only_common['statement_definition_uses'] == {'ND0343': 1}
    assert 'Prime' not in notation.ALIGNED_ADD.conceptual_dependencies
    assert 'PolynomialLeftPad' not in notation.ALIGNED_ADD.conceptual_dependencies


def test_subtract_is_exactly_add_with_B_R_A_permuted_not_a_new_operation():
    parameters = notation.ALIGNED_PARAMETERS
    expected = 'FpPolynomialAlignedAdd(p,bb,bc,M,rb,rc,N,ab,ac,L)'
    exact(named(expected, parameters), notation.ALIGNED_SUBTRACT.template_formula)
    exact(named('FpPolynomialAlignedSubtract('+','.join(parameters)+')', parameters),
          named(expected, parameters))
    assert notation.ALIGNED_SUBTRACT.conceptual_dependencies == ('FpPolynomialAlignedAdd',)
    unpermuted = named('FpPolynomialAlignedAdd('+','.join(parameters)+')', parameters)
    assert FormulaArena().freeze(unpermuted).to_json() != (
        FormulaArena().freeze(notation.ALIGNED_SUBTRACT.template_formula).to_json())


@pytest.mark.parametrize('name,position', tuple(
    (name, position) for _identifier, name, parameters, _parents in EXPECTED_NEW
    for position in range(len(parameters))))
def test_each_named_parameter_substitutes_compound_terms_without_capture(name, position):
    definition = notation.DEFINITIONS[name]
    arguments = list(definition.parameters)
    term = arguments[position]
    arguments[position] = f'S (({term})+({term}))'
    application = name + '(' + ','.join(arguments) + ')'
    public = BUILDERS[name](*arguments, tag='compound_notation_test', variables=definition.parameters)
    exact(named(application, definition.parameters),
          parse_formula_in_context(public, list(definition.parameters)))


@pytest.mark.parametrize('name', tuple(BUILDERS))
def test_outer_binder_named_like_template_witness_is_hygienic(name):
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
def test_named_wrong_arity_is_rejected(name, extra):
    parameters = list(notation.DEFINITIONS[name].parameters)
    arguments = parameters[:-1] if extra == -1 else [*parameters, parameters[0]]
    with pytest.raises(ValueError):
        named(name+'('+','.join(arguments)+')', tuple(parameters))


def test_literal_subtract_alias_has_no_fabricated_theorem_usage(audit):
    definitions = {row['id']: row for row in audit['definitions']}
    assert {'ND0343', 'ND0344', 'ND0345'} <= definitions.keys()
    assert definitions['ND0345']['dependencies'] == ['ND0344']
    assert definitions['ND0345']['used_in_supplied_formulas'] is False
    uses = [edge for edge in audit['edges'] if edge['kind'] == 'uses_definition']
    assert not any(edge['target'] == 'ND0345' for edge in uses)
    assert any(edge['target'] == 'ND0343' for edge in uses)
    assert any(edge['target'] == 'ND0344' for edge in uses)


def test_three_arrow_types_are_exact_and_paths_use_only_supplied_proof_edges(rows, audit):
    expected = [{'kind': 'proof_dependency', 'source': name, 'target': row.name}
                for row in rows for name in row.dependencies]
    assert [edge for edge in audit['edges'] if edge['kind'] == 'proof_dependency'] == expected
    assert audit['proof_dependency_count'] == len(expected) == 274
    by_name = {row.name: row for row in rows}
    definitions = {row['id']: row for row in audit['definitions']}
    assert audit['external_dependencies'] == sorted({
        name for row in rows for name in row.dependencies if name not in by_name})
    assert audit['external_dependencies_resolved'] is False
    for name, path in audit['proof_paths'].items():
        assert path[-1] == name and set(path) <= by_name.keys()
        assert all(left in by_name[right].dependencies for left, right in zip(path, path[1:]))
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


def test_source_syntax_and_rendering_are_never_proof_or_admission_evidence(audit):
    assert audit['authority'] == 'source-syntax-only'
    for key in ('proof_acceptance_performed', 'admission_performed', 'publication_performed',
                'complete_dependency_cone_claimed', 'gcd_bezout_proved'):
        assert audit[key] is False
    assert all(node['proof_acceptance_performed'] is False for node in audit['nodes'])
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    assert '_working_aligned_notation_alignment' not in sys.modules
    assert '_working_aligned_notation_add' not in sys.modules
    assert 'peano_lab.library.prime_field_polynomial_alignment_candidate' not in sys.modules
    assert 'peano_lab.library.prime_field_polynomial_aligned_add_candidate' not in sys.modules
    tree = ast.parse((notation.HERE / 'working_aligned_notation.py').read_text())
    called = {node.func.attr if isinstance(node.func, ast.Attribute) else node.func.id
              for node in ast.walk(tree) if isinstance(node, ast.Call)
              and isinstance(node.func, (ast.Name, ast.Attribute))}
    assert not called.intersection({'check_proof', 'check_bundle', 'replay', 'replay_candidate_bodies',
                                    'replay_with_bundle', 'run_lean', 'compile_proof', 'require_live'})


@pytest.mark.parametrize('path', tuple(notation.SOURCES), ids=lambda path: path.name)
def test_each_literal_input_pin_is_required(path, monkeypatch):
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
        path.symlink_to(notation.ALIGNMENT_SOURCE)
    with pytest.raises(ValueError, match='ordinary file'):
        notation._pin(path, notation.SOURCES[notation.ALIGNMENT_SOURCE])


@pytest.mark.parametrize('name', ('_working_aligned_notation_alignment', '_working_aligned_notation_add',
                                'peano_lab.library.prime_field_polynomial_alignment_candidate',
                                'peano_lab.library.prime_field_polynomial_aligned_add_candidate'))
def test_direct_loader_leaves_every_foreign_identity_untouched(name, monkeypatch):
    foreign = ModuleType(name)
    with monkeypatch.context() as scoped:
        scoped.setitem(sys.modules, name, foreign)
        loaded = notation._load_source(notation.ALIGNMENT_SOURCE, name)
        assert loaded is not foreign and sys.modules[name] is foreign
        assert loaded.__file__ == str(notation.ALIGNMENT_SOURCE)
        assert loaded.__spec__.origin == str(notation.ALIGNMENT_SOURCE)


@pytest.mark.parametrize('case', ('none', 'list', 'empty', 'not-spec', 'duplicate',
                                 'definition-name', 'definition-id', 'definition-edge',
                                 'repeated-edge', 'forward-edge'))
def test_invalid_graphs_cannot_gain_authority_from_definition_arrows(case, rows):
    first, later = rows[59], rows[61]
    bad = {
        'none': None, 'list': [first], 'empty': (), 'not-spec': (0,),
        'duplicate': (first, first),
        'definition-name': (replace(first, name='CommonRepresentatives'),),
        'definition-id': (replace(first, name='ND0345'),),
        'definition-edge': (replace(first, dependencies=('ND0343',)),),
        'repeated-edge': (replace(first, dependencies=('external', 'external')),),
        'forward-edge': (later, first),
    }[case]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(bad)


@pytest.mark.parametrize('names', (None, [], ('unknown',), ('',), (False,)))
def test_definition_closure_rejects_unknown_or_malformed_roots(names):
    with pytest.raises(notation.NotationError):
        notation.definition_closure(names)


def test_definition_closure_is_prior_first_and_subtraction_preserves_its_add_parent():
    closure = notation.definition_closure(('FpPolynomialAlignedSubtract', 'CommonRepresentatives'))
    names = [item.name for item in closure]
    assert len(names) == len(set(names))
    assert names.index('CommonRepresentatives') < names.index('FpPolynomialAlignedAdd')
    assert names.index('FpPolynomialAlignedAdd') < names.index('FpPolynomialAlignedSubtract')
    assert all(closure[names.index(name)] is notation.DEFINITIONS[name] for name in names)
    for position, item in enumerate(closure):
        assert set(item.conceptual_dependencies) <= set(names[:position])
