"""Source/contract/model checks for four independently sized additive laws.

These tests never execute a proof. They reuse the separately byte-pinned
independent native formulas and CRT model helpers from the basic-add tests,
not mathematical candidate builders, to construct the four expected claims.
Whole-cone HA/Lean and ordinary acceptance remain separate obligations.
"""

import ast
from hashlib import sha256
import importlib.util
from pathlib import Path
import re
import sys

import pytest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SOURCE = HERE / 'prime_field_polynomial_aligned_algebra_candidate.py'
HELPERS = HERE.parent / 'prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py'
SOURCE_PIN = (16013, 'a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390')
HELPER_PIN = (33347, '6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8')


def _pin(path, expected):
    assert path.is_file() and not path.is_symlink()
    raw = path.read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == expected
    return raw


def _load(path, expected, name):
    before = _pin(path, expected)
    modules = dict(sys.modules)
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert _pin(path, expected) == before
    assert name not in sys.modules
    assert all(sys.modules[key] is value for key, value in modules.items())
    return module


helpers = _load(HELPERS, HELPER_PIN, '_aligned_algebra_independent_formulas')
candidate = _load(SOURCE, SOURCE_PIN, '_aligned_algebra_actual_source')
ROWS = candidate.make_prime_field_polynomial_aligned_algebra_candidate_theorems(helpers.TheoremSpec)
NAMES = tuple('prime_field_polynomial_'+stem for stem in (
    'aligned_subtract_exists', 'aligned_add_cancel_left', 'aligned_add_associative',
    'aligned_subtract_functional'))
SHARED_DEPS = (
    'prime_field_polynomial_aligned_add_bounded',
    'prime_field_polynomial_bounded_representative_at_length_exists',
    'le_add_right', 'le_refl', 'le_trans', 'prime_field_polynomial_aligned_add_realize',
    'prime_field_polynomial_equivalent_transitive',
    'prime_field_polynomial_equal_implies_equivalent', 'prime_field_polynomial_equivalent_symmetric',
)
DEPENDENCIES = (
    ('prime_field_polynomial_common_representatives_exists', 'prime_field_polynomial_subtract_exists',
     'prime_field_polynomial_subtract_recover_add', 'prime_field_polynomial_add_bounded',
     'prime_field_polynomial_aligned_add_from_common',
     'prime_field_polynomial_power_coefficient_functional', 'prime_field_polynomial_equivalent_symmetric'),
    (*SHARED_DEPS, 'prime_field_polynomial_subtract_functional', 'prime_field_polynomial_subtract_from_add'),
    (*SHARED_DEPS, 'prime_field_polynomial_add_associative'),
    ('prime_field_polynomial_aligned_add_cancel_left',),
)


@pytest.fixture(autouse=True)
def all_current_inputs_and_foreign_bindings_stay_exact():
    before, modules = helpers.actual_input_pins(), helpers.protected_bindings()
    _pin(SOURCE, SOURCE_PIN)
    _pin(HELPERS, HELPER_PIN)
    yield
    _pin(SOURCE, SOURCE_PIN)
    _pin(HELPERS, HELPER_PIN)
    assert helpers.actual_input_pins() == before
    after = helpers.protected_bindings()
    assert after.keys() == modules.keys()
    assert all(after[name] is module for name, module in modules.items())


def contracts():
    A, B, R = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')
    C, S = ('cb', 'cc', 'J'), ('sb', 'sc', 'J')
    polys = tuple((letter+'b', letter+'c', 'L'+letter) for letter in ('a', 'b', 'c', 'u', 'v', 'r', 's'))
    aa, bb, cc, uu, vv, rr, ss = polys
    operations = ((aa, bb, uu), (uu, cc, rr), (bb, cc, vv), (aa, vv, ss))
    return (
        (('p', *A, *B), (helpers.Prime('p'), helpers.Coeff('p', *A), helpers.Coeff('p', *B)),
         'exists rb rc. '+helpers.AlignedSubtract('p', *A, *B, 'rb', 'rc', 'L+M')),
        (('p', *A, *B, *C, *R),
         (helpers.Prime('p'), helpers.AlignedAdd('p', *A, *B, *R),
          helpers.AlignedAdd('p', *A, *C, *R)), helpers.Equivalent(*B, *C)),
        (('p', *(value for poly in polys for value in poly)),
         (helpers.Prime('p'),
          *(helpers.AlignedAdd('p', *(value for poly in operation for value in poly))
            for operation in operations)), helpers.Equivalent(*rr, *ss)),
        (('p', *A, *B, *R, *S),
         (helpers.Prime('p'), helpers.AlignedSubtract('p', *A, *B, *R),
          helpers.AlignedSubtract('p', *A, *B, *S)), helpers.Equivalent(*R, *S)),
    )


@pytest.mark.parametrize('index', range(4))
def test_every_independent_fully_expanded_claim(index):
    expected = helpers.contract(*contracts()[index])
    helpers.same_ast(helpers._closed_formula(ROWS[index].statement), helpers._closed_formula(expected))


def test_exact_source_order_commands_and_all_actual_direct_prerequisites():
    assert tuple(row.name for row in ROWS) == NAMES
    assert tuple(row.dependencies for row in ROWS) == DEPENDENCIES
    assert tuple(len(row.script) for row in ROWS) == (104, 279, 531, 33)
    assert sum(len(row.dependencies) for row in ROWS) == 29
    known = helpers.body_core()
    for row in ROWS:
        assert row.name not in known and all(name in known for name in row.dependencies)
        known[row.name] = row


def test_all_local_operation_expansions_are_the_existing_grouped_graphs():
    parameters = helpers.PARAMETERS
    for builder, independent in (
        (candidate._aligned_add, helpers.AlignedAdd), (candidate._aligned_subtract, helpers.AlignedSubtract),
    ):
        raw = builder(*parameters, 'independent_algebra_expansion')
        expected = independent(*parameters)
        helpers.same_ast(helpers.parse_formula_in_context(raw, list(parameters)),
                         helpers.parse_formula_in_context(expected, list(parameters)))


@pytest.mark.parametrize('tag,polys', (
    ('cancel', (('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('cb', 'cc', 'J'), ('rb', 'rc', 'N'))),
    ('associative', tuple((letter+'b', letter+'c', 'L'+letter) for letter in ('a', 'b', 'c', 'u', 'v', 'r', 's'))),
))
def test_actual_representative_have_formulas_do_not_capture_an_original_code_or_scale(tag, polys):
    bound_names = tuple('actual_bound_'+str(index) for index in range(len(polys)))
    body, representatives = candidate._representatives(polys, bound_names, tag)
    outer = ('p', *(value for poly in polys for value in poly))
    lengths = tuple(poly[2] for poly in polys)
    length = lengths[-1]
    for item in reversed(lengths[:-1]):
        length = '('+item+')+('+length+')'
    have_commands = tuple(command for command in body
                          if command.startswith('have '+tag+'_representative_'))
    assert len(have_commands) == len(polys) == len(representatives)
    witness_names = set()
    for index, (command, poly) in enumerate(zip(have_commands, polys, strict=True)):
        raw = command.partition(':')[2].strip()
        first, second = re.match(r'exists ([A-Za-z0-9_]+) ([A-Za-z0-9_]+)\.', raw).groups()
        assert (first, second) == (f'{tag}_representative_{index}_code',
                                   f'{tag}_representative_{index}_scale')
        assert not {first, second}.intersection(outer)
        assert not {first, second}.intersection(witness_names)
        witness_names.update((first, second))
        expected = 'exists independent_code independent_scale. '+helpers.And(
            helpers.Coeff('p', 'independent_code', 'independent_scale', length),
            helpers.Equivalent(*poly, 'independent_code', 'independent_scale', length))
        helpers.same_ast(helpers.parse_formula_in_context(raw, list(outer)),
                         helpers.parse_formula_in_context(expected, list(outer)))
        assert representatives[index][0][2] == length
    assert len(witness_names) == 2*len(polys)


def test_no_new_relation_identity_or_proof_or_alpha_call_is_installed():
    tree = ast.parse(SOURCE.read_text())
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert all(name in {'__future__', 'typing',
                       'peano_lab.library.prime_field_arithmetic_candidate',
                       'peano_lab.library.prime_field_polynomial_candidate',
                       'peano_lab.library.prime_field_polynomial_representation_candidate',
                       'peano_lab.library.prime_field_polynomial_subtraction_candidate'} for name in imports)
    calls = {node.func.id for node in ast.walk(tree)
             if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)}
    assert not calls.intersection({'check_proof', 'check_bundle', 'replay_candidate_bodies',
                                   'register_axiom', '_definition', 'require_live', 'eval', 'exec'})
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    assert '_aligned_algebra_actual_source' not in sys.modules
    assert '_aligned_algebra_independent_formulas' not in sys.modules


def _triple(values, multiplier=1):
    return helpers.encode_beta(values, multiplier), len(values)


def _sum_values(p, av, bv, padding=0):
    K = max(len(av), len(bv))
    av, bv = (0,)*(K-len(av))+av, (0,)*(K-len(bv))+bv
    return (0,)*padding+helpers.trim(tuple((a+b) % p for a, b in zip(av, bv)))


def _assert_aligned(p, av, bv, rv, multiplier=1):
    K = max(len(helpers.trim(av)), len(helpers.trim(bv)), len(helpers.trim(rv)))
    def padded(values):
        values = helpers.trim(values)
        return (0,)*(K-len(values))+values
    a, b, r = (helpers.encode_beta(values, multiplier+index)
               for index, values in enumerate((av, bv, rv)))
    u, v, t = (helpers.encode_beta(padded(values), multiplier+index+3)
               for index, values in enumerate((av, bv, rv)))
    assert helpers.aligned_add_model(p, a, len(av), b, len(bv), r, len(rv), u, v, t, K)
    return a, b, r


PAIRS = (((), ()), ((), (1,)), ((0, 1), (1, 0)), ((2, 1), (0, 3, 2)))
TRIPLES = (((), (), ()), ((1,), (), (0, 1)), ((1, 0), (2,), (0, 2, 1)),
           ((0, 0, 1), (0, 1), (1,)))


@pytest.mark.parametrize('values', PAIRS)
@pytest.mark.parametrize('p', (2, 3, 5))
def test_subtraction_constructor_uses_actual_length_L_plus_M(values, p):
    av, bv = (tuple(value % p for value in part) for part in values)
    K = len(av)+len(bv)
    aa, bb = (0,)*(K-len(av))+av, (0,)*(K-len(bv))+bv
    rv = tuple((a-b) % p for a, b in zip(aa, bb))
    assert len(rv) == K
    _assert_aligned(p, bv, rv, av)


@pytest.mark.parametrize('values', PAIRS)
@pytest.mark.parametrize('p', (2, 3, 5))
def test_cancellation_compares_formal_outputs_not_beta_codes(values, p):
    av, bv = (tuple(value % p for value in part) for part in values)
    cv = (0, 0)+bv
    rv = _sum_values(p, av, bv, 1)
    _assert_aligned(p, av, bv, rv)
    _assert_aligned(p, av, cv, rv, 7)
    b, c = helpers.encode_beta(bv, 2), helpers.encode_beta(cv, 8)
    assert helpers.equivalent(b, len(bv), c, len(cv))
    assert len(bv) != len(cv)


@pytest.mark.parametrize('values', TRIPLES)
@pytest.mark.parametrize('p', (2, 3, 5))
def test_both_bracketings_use_four_actual_operations_with_seven_independent_lengths(values, p):
    av, bv, cv = (tuple(value % p for value in part) for part in values)
    uv, vv = _sum_values(p, av, bv, 1), _sum_values(p, bv, cv, 2)
    rv, sv = _sum_values(p, uv, cv, 3), _sum_values(p, av, vv, 4)
    for index, operation in enumerate(((av, bv, uv), (uv, cv, rv), (bv, cv, vv), (av, vv, sv))):
        _assert_aligned(p, *operation, multiplier=1+index*6)
    r, s = helpers.encode_beta(rv), helpers.encode_beta(sv, 2)
    assert helpers.equivalent(r, len(rv), s, len(sv))
    assert len(rv) != len(sv)


@pytest.mark.parametrize('p', (2, 3, 5))
def test_subtraction_functionality_reuses_cancellation_and_allows_distinct_output_lengths(p):
    av, bv = (1, 0), (0, 1)
    rv = tuple((a-b) % p for a, b in zip(av, bv))
    sv = (0, 0)+rv
    _assert_aligned(p, bv, rv, av)
    _assert_aligned(p, bv, sv, av, 7)
    assert helpers.equivalent(helpers.encode_beta(rv), len(rv), helpers.encode_beta(sv, 2), len(sv))


def test_field_evaluation_agreement_does_not_supply_an_additive_identity():
    impostor, empty = helpers.encode_beta((1, 1, 0)), helpers.encode_beta(())
    assert all((x*x+x) % 2 == 0 for x in (0, 1))
    assert not helpers.equivalent(impostor, 3, empty, 0)
    assert not helpers.aligned_add_model(2, empty, 0, empty, 0, impostor, 3,
                                         empty, empty, empty, 0)
