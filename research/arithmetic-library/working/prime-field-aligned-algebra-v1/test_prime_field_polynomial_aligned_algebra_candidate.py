"""Independent expanded contracts and actual beta models for aligned laws.

The preceding independent test's primitive HA expansions and integer beta
decoder are reused by exact bytes. They are not mathematical-source builders
or proof oracles. Native cases use the unchanged conditional HA checker.
"""

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
SOURCE = HERE / 'prime_field_polynomial_aligned_algebra_candidate.py'
INDEPENDENT = HERE.parent / 'prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py'
PINS = {
    SOURCE: 'a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390',
    INDEPENDENT: '6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8',
}


def load(path, name):
    assert name not in sys.modules and path.is_file() and not path.is_symlink()
    assert sha256(path.read_bytes()).hexdigest() == PINS[path]
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert name not in sys.modules
    return module


independent = load(INDEPENDENT, 'working_aligned_algebra_independent_primitives')
candidate = load(SOURCE, 'working_aligned_algebra_actual_source')


@pytest.fixture(autouse=True)
def exact_inputs_and_authority_are_unchanged():
    protected = independent.protected_bindings()
    before = independent.actual_input_pins()
    for path, digest in PINS.items():
        assert path.is_file() and not path.is_symlink() and sha256(path.read_bytes()).hexdigest() == digest
    yield
    assert independent.actual_input_pins() == before
    for path, digest in PINS.items():
        assert sha256(path.read_bytes()).hexdigest() == digest
    after = independent.protected_bindings()
    assert after.keys() == protected.keys() and all(after[key] is value for key, value in protected.items())


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_aligned_algebra_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    table = independent.body_core()
    for row in rows():
        assert row.name not in table
        table[row.name] = row
    return table


def contracts():
    A, B, R, C, S = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N'), ('cb', 'cc', 'J'), ('sb', 'sc', 'J')
    add, sub, equiv = independent.AlignedAdd, independent.AlignedSubtract, independent.Equivalent
    prime, coeff, contract = independent.Prime, independent.Coeff, independent.contract
    subtract_exists = contract(('p', *A, *B), (prime('p'), coeff('p', *A), coeff('p', *B)),
                               'exists rb rc. ' + sub('p', *A, *B, 'rb', 'rc', 'L+M'))
    cancel = contract(('p', *A, *B, *C, *R), (prime('p'), add('p', *A, *B, *R), add('p', *A, *C, *R)), equiv(*B, *C))
    function = contract(('p', *A, *B, *R, *S), (prime('p'), sub('p', *A, *B, *R), sub('p', *A, *B, *S)), equiv(*R, *S))
    aa, bb, cc, uu, vv, rr, ss = tuple((letter + 'b', letter + 'c', 'L' + letter)
                                     for letter in ('a', 'b', 'c', 'u', 'v', 'r', 's'))
    parameters = ('p', *aa, *bb, *cc, *uu, *vv, *rr, *ss)
    associativity = contract(parameters, (prime('p'), add('p', *aa, *bb, *uu), add('p', *uu, *cc, *rr),
                                         add('p', *bb, *cc, *vv), add('p', *aa, *vv, *ss)), equiv(*rr, *ss))
    return subtract_exists, cancel, associativity, function


def test_frozen_inventory_and_acyclic_native_dependency_ownership():
    assert tuple(row.name for row in rows()) == tuple('prime_field_polynomial_' + suffix for suffix in (
        'aligned_subtract_exists', 'aligned_add_cancel_left', 'aligned_add_associative', 'aligned_subtract_functional'))
    assert tuple(len(row.script) for row in rows()) == (104, 279, 531, 33)
    assert tuple(len(row.dependencies) for row in rows()) == (7, 11, 10, 1)
    known = set(independent.body_core())
    for row in rows():
        assert row.name not in known and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= known
        known.add(row.name)


@pytest.mark.parametrize('index', range(4))
def test_independently_expanded_statement(index):
    independent.same_ast(_closed_formula(rows()[index].statement), _closed_formula(contracts()[index]))


def test_same_conservative_alignment_definitions_not_new_aliases():
    params = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'rb', 'rc', 'N')
    for builder, expected in ((candidate._aligned_add, independent.AlignedAdd),
                              (candidate._aligned_subtract, independent.AlignedSubtract)):
        independent.same_ast(_closed_formula(independent.contract(params, (), builder(*params, 'algebra_definition'))),
                             _closed_formula(independent.contract(params, (), expected(*params))))


def test_constructed_representative_binders_do_not_capture_any_original_code():
    polys = (('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N'))
    commands, _ = candidate._representatives(polys, ('ha', 'hb', 'hr'), 'independent_capture_probe')
    contexts = tuple(value for poly in polys for value in poly)
    for command in commands:
        if command.startswith('have independent_capture_probe_representative_'):
            binders = command.split('exists ', 1)[1].split('.', 1)[0].split()
            assert not set(binders).intersection(contexts)
            assert len(set(binders)) == 2


def test_only_native_source_helpers_and_no_checker_or_admission_oracle():
    import ast
    tree = ast.parse(SOURCE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in ('__future__', 'typing') or node.module.startswith('peano_lab.library.prime_field_')
        assert not (isinstance(node, ast.Import) and any('edition' in alias.name for alias in node.names))
    assert not any('admit' in command or 'sorry' in command for row in rows() for command in row.script)


@pytest.mark.parametrize('index', range(4))
def test_original_conditional_ha_body(index):
    receipt = replay_candidate_bodies((rows()[index],), core=core())[0]
    assert (receipt.proof_nodes, receipt.proof_depth) == ((140, 49), (353, 67), (644, 84), (76, 47))[index]


@pytest.mark.parametrize('index', range(4))
@pytest.mark.parametrize('mutation', ('false', 'empty', 'truncated'))
def test_native_checker_rejects_wrong_or_incomplete_proof(index, mutation):
    row = rows()[index]
    bad = replace(row, statement='0=1') if mutation == 'false' else replace(row, script=() if mutation == 'empty' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((bad,), core=core())


EDGES = tuple((index, dependency) for index, row in enumerate(rows()) for dependency in row.dependencies)


@pytest.mark.parametrize('index,dependency', EDGES)
def test_native_checker_rejects_missing_prerequisite(index, dependency):
    row = rows()[index]
    bad = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((bad,), core=core())


@pytest.mark.parametrize('index,dependency', EDGES)
def test_native_checker_rejects_poisoned_prerequisite(index, dependency):
    table = dict(core())
    table[dependency] = TheoremSpec(dependency, '0=1', (), (), 'Deliberately false test premise.')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=table)


def add_values(p, a, b, subtract=False):
    length = max(len(a), len(b))
    left, right = (0,) * (length - len(a)) + a, (0,) * (length - len(b)) + b
    return independent.trim(tuple((x - y if subtract else x + y) % p for x, y in zip(left, right, strict=True)))


def holds(p, a, b, r, padding=0):
    length = max(len(independent.trim(a)), len(independent.trim(b))) + padding
    ca, cb, _, _, cu, cv, ct = independent.model_witnesses(p, a, b, length)
    cr = independent.encode_beta(r, 7)
    return independent.aligned_add_model(p, ca, len(a), cb, len(b), cr, len(r), cu, cv, ct, length)


TRIPLES = (((), (), ()), ((), (1,), (1, 0)), ((1,), (), (1,)),
           ((0, 1), (1, 0), (1,)), ((1, 0, 1), (1, 1), (0, 1)),
           ((0, 0), (0,), (0, 0, 1)), ((2, 3), (4, 1, 2), (3, 1)))


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('triple', TRIPLES)
def test_actual_beta_associativity_and_cancellation_models(p, triple):
    a, b, c = (tuple(value % p for value in values) for values in triple)
    u, v = add_values(p, a, b), add_values(p, b, c)
    r, s = (0,) + add_values(p, u, c), add_values(p, a, v)
    assert holds(p, a, b, u, 1) and holds(p, u, c, r, 2)
    assert holds(p, b, c, v) and holds(p, a, v, s, 1)
    assert independent.equivalent(independent.encode_beta(r), len(r), independent.encode_beta(s, 2), len(s))
    recoded_b = (0, 0) + b
    assert holds(p, a, recoded_b, u, 1)
    assert independent.equivalent(independent.encode_beta(b), len(b), independent.encode_beta(recoded_b, 3), len(recoded_b))


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('triple', TRIPLES)
def test_actual_beta_subtraction_witness_and_formal_uniqueness(p, triple):
    a, b = (tuple(value % p for value in values) for values in triple[:2])
    r = add_values(p, a, b, subtract=True)
    s = (0, 0) + r
    assert holds(p, b, r, a, 1) and holds(p, b, s, a, 2)
    assert independent.equivalent(independent.encode_beta(r), len(r), independent.encode_beta(s, 3), len(s))
    hostile = ((r[0] + 1) % p, *r[1:]) if r else (1,)
    assert not holds(p, b, hostile, a, 1)


def test_length_alignment_is_not_an_evaluation_identity():
    p = 3
    impostor, zero = (1, 0, 2, 0), ()
    assert all(sum(value * pow(x, len(impostor) - index - 1, p) for index, value in enumerate(impostor)) % p == 0 for x in range(p))
    assert not independent.equivalent(independent.encode_beta(impostor), len(impostor), (0, 0), 0)
    assert not holds(p, impostor, zero, zero)
