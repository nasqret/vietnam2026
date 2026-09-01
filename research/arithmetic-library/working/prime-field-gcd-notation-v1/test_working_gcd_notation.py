"""Independent AST/hygiene and finite native-beta examples, never proof tests."""
from dataclasses import replace
import math
import re
import sys

import pytest

import working_gcd_notation as n
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.formula_dag import FormulaArena


def named(text, parameters=()):
    parser = _LocalDefinedParser(text, n.DEFINITIONS)
    parser.free = list(parameters)
    formula = parser.parse()
    assert parser.free == list(parameters)
    return formula


def frozen(formula):
    return FormulaArena().freeze(formula).to_json()


NORMAL = '(G)=0 \\/ FpMonic(p,gb,gc,G)'
GCD = ('FpPolynomialCommonRightDivisor(p,gb,gc,G,ab,ac,L,bb,bc,M) /\\ '
       '(forall db dc D. FpPolynomialCommonRightDivisor(p,db,dc,D,ab,ac,L,bb,bc,M) -> '
       'FpPolynomialRightDivides(p,db,dc,D,gb,gc,G))')
NORMALIZED = '(FpPolynomialZeroOrMonic(p,gb,gc,G)) /\\ (FpPolynomialRightGcd(p,gb,gc,G,ab,ac,L,bb,bc,M))'
CONTRACTS = ((n.ZERO_OR_MONIC, NORMAL), (n.RIGHT_GCD, GCD), (n.NORMALIZED_GCD, NORMALIZED))


@pytest.fixture(autouse=True)
def immutable_sources_and_owners():
    before = n.require_sources()
    owners = {key: value for key, value in sys.modules.items()
              if key.startswith(('peano_lab.library.editions', 'check_alpha_', '_working_gcd_notation'))}
    yield
    assert n.require_sources() == before
    after = {key: value for key, value in sys.modules.items()
             if key.startswith(('peano_lab.library.editions', 'check_alpha_', '_working_gcd_notation'))}
    assert owners.keys() == after.keys()
    assert all(after[key] is value for key, value in owners.items())


def test_old_objects_digest_and_all_old_expansion_arrows_preserved():
    records, _, _ = n.reviewed_registry()
    assert len(records) == 407
    assert sum(len(row['dependencies']) for row in records.values()) == 884
    assert len(n.PRIOR_OBJECTS) == 404
    assert n.PRIOR_REGISTRY_SHA256 == n._registry_digest(n.previous.DEFINITIONS)
    assert all(n.DEFINITIONS[name] is item for name, item in n.PRIOR_OBJECTS)
    assert sum(len(item.conceptual_dependencies) for _, item in n.PRIOR_OBJECTS) == 879
    assert [x.stable_id for x in n.NEW_DEFINITIONS] == ['ND0348', 'ND0349', 'ND0350']


@pytest.mark.parametrize('definition,expected', CONTRACTS, ids=['normal', 'greatest', 'normalized'])
def test_literal_independent_contract(definition, expected):
    assert frozen(definition.template_formula) == frozen(named(expected, definition.parameters))
    for old in n.previous.DEFINITIONS.values():
        if old.arity == definition.arity:
            assert frozen(old.template_formula) != frozen(definition.template_formula)


@pytest.mark.parametrize('definition,expected,index', [
    (definition, expected, i) for definition, expected in CONTRACTS for i in range(definition.arity)])
def test_every_argument_compound_substitution_avoids_bound_variable_capture(definition, expected, index):
    # Deliberately collide with the written universal binder db and with the
    # implementation's generated tag; conservative substitution must rename.
    arguments = list(definition.parameters)
    arguments[index] = '(db+gcd_definition_greatest_D)'
    params = tuple(dict.fromkeys((*definition.parameters, 'db', 'gcd_definition_greatest_D')))
    call = definition.name + '(' + ','.join(arguments) + ')'
    actual = named(call, params)
    # Rename the independent written binders first, then substitute free
    # parameter tokens simultaneously; never reuse the implementation template.
    independent = re.sub(r'\b(db|dc|D)\b', lambda m: 'independent_' + m[0], expected)
    replacements = dict(zip(definition.parameters, arguments))
    independent = re.sub(r'\b[A-Za-z][A-Za-z0-9_]*\b',
                         lambda m: replacements.get(m[0], m[0]), independent)
    assert frozen(actual) == frozen(named(independent, params))


@pytest.mark.parametrize('definition', n.NEW_DEFINITIONS, ids=lambda d: d.name)
@pytest.mark.parametrize('delta', [-1, 1])
def test_wrong_arity_rejected(definition, delta):
    args = ['0'] * (definition.arity + delta)
    with pytest.raises(Exception):
        named(definition.name + '(' + ','.join(args) + ')')


def test_greatestness_direction_and_common_clause_are_not_optional():
    correct = frozen(n.RIGHT_GCD.template_formula)
    reversed_order = GCD.replace('FpPolynomialRightDivides(p,db,dc,D,gb,gc,G)',
                                 'FpPolynomialRightDivides(p,gb,gc,G,db,dc,D)')
    assert correct != frozen(named(reversed_order, n.GCD_PARAMETERS))
    assert correct != frozen(named(GCD.split(' /\\ ')[0], n.GCD_PARAMETERS))


def test_raw_recursion_and_final_public_contract_reuse_exact_common_and_bezout():
    params = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M')
    prefix = 'exists gb gc G ub uc U vb vc V. '
    bezout = 'FpPolynomialBezoutRepresentation(p,ab,ac,L,bb,bc,M,gb,gc,G,ub,uc,U,vb,vc,V)'
    common = 'FpPolynomialCommonRightDivisor(p,gb,gc,G,ab,ac,L,bb,bc,M)'
    gcd = 'FpPolynomialRightGcd(p,gb,gc,G,ab,ac,L,bb,bc,M)'
    raw = prefix + '(' + NORMAL + ') /\\ ((' + common + ') /\\ (' + bezout + '))'
    final = prefix + '(' + NORMAL + ') /\\ ((' + gcd + ') /\\ (' + bezout + '))'
    assert frozen(named(raw, params)) != frozen(named(final, params))
    assert n.DEFINITIONS['FpPolynomialBezoutRepresentation'] is n.previous.BEZOUT_REPRESENTATION
    assert n.DEFINITIONS['FpPolynomialCommonRightDivisor'] is n.previous.COMMON_RIGHT_DIVISOR


def row(name='fixture_one', dependencies=()):
    return n.TheoremSpec(name, 'forall p gb gc G. (' + n.ZERO_OR_MONIC.template_source +
                         ') -> (' + n.ZERO_OR_MONIC.template_source + ')', dependencies,
                         ('intro p', 'intro gb', 'intro gc', 'intro G', 'intro h', 'exact h'),
                         'Unverified source fixture; no checker called.')


@pytest.fixture(scope='module')
def graph():
    return n.audit_rows((row(), row('fixture_two', ('fixture_one', 'external_unresolved'))))


def test_typed_arrows_do_not_create_proof_paths_or_acceptance(graph):
    assert graph['proof_paths'] == {'fixture_one': ['fixture_one'], 'fixture_two': ['fixture_one', 'fixture_two']}
    assert graph['external_dependencies'] == ['external_unresolved']
    assert not graph['external_dependencies_resolved']
    assert {e['kind'] for e in graph['edges']} == {'proof_dependency', 'uses_definition', 'definition_uses_definition'}
    assert not any(graph[key] for key in ('proof_acceptance_performed', 'admission_performed',
        'publication_performed', 'complete_dependency_cone_claimed', 'gcd_bezout_proved'))
    for node in graph['nodes']:
        assert node['authority'] == 'source-syntax-only'
        assert frozen(named(node['defined']['defined_statement'])) == frozen(parse_formula_in_context(node['statement'], []))


def test_caller_extension_preserves_all95_source_rows_without_inventing_status():
    original = n.previous.source_rows()
    document = n.audit((row('unverified_caller_row', (original[-1].name,)),))
    assert len(document['nodes']) == 96
    for spec, node in zip(original, document['nodes'][:95]):
        assert (node['name'], node['statement'], tuple(node['dependencies']), tuple(node['script']), node['summary']) == (
            spec.name, spec.statement, spec.dependencies, spec.script, spec.summary)
    assert document['nodes'][-1]['authority'] == 'source-syntax-only'
    assert all('status' not in node and not node['proof_acceptance_performed'] for node in document['nodes'])


@pytest.mark.parametrize('complete', [True, False])
def test_complete_source_map_is_not_complete_proof_acceptance(complete):
    parent = 'fixture_one' if complete else 'missing_prerequisite'
    rows = (row(), row('fixture_two', (parent,)))
    if not complete:
        with pytest.raises(n.NotationError): n.audit_complete_rows(rows)
    else:
        document = n.audit_complete_rows(rows)
        assert document['external_dependencies'] == []
        assert document['source_dependencies_complete']
        assert not document['proof_acceptance_performed']
        assert not document['complete_dependency_cone_claimed']
        assert document['path_policy'] == 'proof_dependency_edges_only'


@pytest.mark.parametrize('attack', ['duplicate', 'forward', 'cycle', 'definition_name', 'definition_id',
                                  'definition_parent', 'free_statement', 'list_rows', 'list_deps', 'duplicate_deps'])
def test_source_map_rejects_invalid_ownership_or_topology(attack):
    a, b = row(), row('fixture_two')
    rows = (a, b)
    if attack == 'duplicate': rows = (a, a)
    elif attack == 'forward': rows = (replace(a, dependencies=(b.name,)), b)
    elif attack == 'cycle': rows = (replace(a, dependencies=(a.name,)),)
    elif attack == 'definition_name': rows = (replace(a, name='FpPolynomialRightGcd'),)
    elif attack == 'definition_id': rows = (replace(a, name='ND0349'),)
    elif attack == 'definition_parent': rows = (replace(a, dependencies=('ND0349',)),)
    elif attack == 'free_statement': rows = (replace(a, statement='a=a'),)
    elif attack == 'list_rows': rows = list(rows)
    elif attack == 'list_deps': rows = (replace(a, dependencies=[]),)
    elif attack == 'duplicate_deps': rows = (replace(a, dependencies=('outside', 'outside')),)
    with pytest.raises(Exception): n.audit_rows(rows)


def coded(values, salt=0):
    """Concrete CRT beta prefix, with a genuinely different code for each salt."""
    values = tuple(values)
    scale = math.factorial(len(values)) * (max(values, default=0) + 1)
    code, period = 0, 1
    for i, value in enumerate(values):
        modulus = 1 + (i + 1) * scale
        assert math.gcd(period, modulus) == 1 and value < modulus
        code += period * (((value - code) * pow(period, -1, modulus)) % modulus)
        period *= modulus
    return code + salt * period, scale, len(values)


def decoded(poly):
    b, c, length = poly
    return tuple(b % (1 + (i + 1) * c) for i in range(length))


def normal(p, poly):
    values = decoded(poly)
    return not values or (values[0] == 1 and all(value < p for value in values))


def formal(poly):
    values = decoded(poly)
    return values[next((i for i, x in enumerate(values) if x), len(values)):]


def divides(p, divisor, target):
    """Finite canonical-polynomial division model; not a native proof oracle."""
    if any(x >= p for x in (*decoded(divisor), *decoded(target))): return False
    d, rem = formal(divisor), list(formal(target))
    if not d: return not rem
    while rem and len(rem) >= len(d):
        scalar = rem[0] * pow(d[0], -1, p) % p
        for i, value in enumerate(d): rem[i] = (rem[i] - scalar * value) % p
        while rem and rem[0] == 0: rem.pop(0)
    return not rem


@pytest.mark.parametrize('p', [2, 3, 5])
@pytest.mark.parametrize('values', [(), (0,), (0, 0), (1,), (0, 1), (1, 0), (1, 1, 0)])
def test_native_beta_normal_and_padding_models(p, values):
    a, b = coded(values), coded((0, *values), 2)
    assert decoded(a) == values and formal(a) == formal(b)
    assert a != b
    assert normal(p, a) == (not values or values[0] == 1)
    assert not normal(p, b)
    assert divides(p, a, b) and divides(p, b, a)


def test_both_zero_requires_empty_normal_output_not_one():
    z, stored_zero, one = coded(()), coded((0, 0)), coded((1,))
    assert normal(3, z) and not normal(3, stored_zero)
    assert divides(3, z, stored_zero) and not divides(3, z, one)
    # 1 is common, but misses greatestness for the common divisor 0.
    assert divides(3, one, z) and not divides(3, z, one)


def test_common_divisor_without_greatestness_and_unnormalized_associates():
    x, one, twice_x = coded((1, 0)), coded((1,)), coded((2, 0))
    assert divides(3, one, x) and not divides(3, x, one)
    assert divides(3, x, twice_x) and divides(3, twice_x, x)
    assert formal(x) != formal(twice_x) and normal(3, x) and not normal(3, twice_x)


def test_finite_field_evaluation_impostor_is_not_formal_zero():
    p, impostor, z = 2, coded((1, 1, 0)), coded(())
    for a in range(p):
        value = 0
        for coefficient in decoded(impostor): value = (value * a + coefficient) % p
        assert value == 0
    assert formal(impostor) != formal(z) and normal(p, impostor)
    assert not divides(p, z, impostor)


def test_empty_codes_no_prime_clause_and_natural_one_not_signed_two():
    assert normal(0, (999, 7, 0))
    assert normal(4, coded((1, 3)))  # composite modulus is not a definition clause
    assert not normal(5, coded((2,)))
    assert not normal(3, coded((1, 3)))
