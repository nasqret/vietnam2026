"""Independent contracts, native beta models and original conditional HA.

Finite models are diagnostics, not proof fixtures.  Native cases replay the
actual source scripts against exact declared premise types and the unchanged
checker.  Direct-file imports neither install aliases nor load Alpha.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib
import importlib.util
from itertools import product
from pathlib import Path
import sys
from types import ModuleType

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_gcd_uniqueness_candidate.py'
SOURCE_SHA256 = '916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b'
ORACLE_PATH = HERE.parent / 'prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py'
ORACLE_SHA256 = 'e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791'
UNIT_PATH = HERE.parent / 'prime-field-left-unit-v1/prime_field_polynomial_left_unit_candidate.py'
UNIT_SHA256 = 'dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6'
CONGRUENCE_SHA256 = 'effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70'
PRIVATE_NAMES = ('working_gcd_uniqueness_candidate', 'working_gcd_uniqueness_oracle', 'working_gcd_uniqueness_unit')


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name.startswith(('peano_lab.library.editions_v', 'working_'))}


def load_file(name, path):
    before = protected_bindings()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())
    return module


assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
oracle = load_file(PRIVATE_NAMES[1], ORACLE_PATH)
candidate = load_file(PRIVATE_NAMES[0], SOURCE)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_gcd_uniqueness_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    result = dict(oracle.provider_core())
    assert sha256(UNIT_PATH.read_bytes()).hexdigest() == UNIT_SHA256
    assert sha256((LIBRARY / 'prime_field_polynomial_convolution_congruence_candidate.py').read_bytes()).hexdigest() == CONGRUENCE_SHA256
    for name in ('prime_field_polynomial_degree_candidate', 'prime_field_polynomial_convolution_congruence_candidate'):
        module = importlib.import_module('peano_lab.library.' + name)
        assert Path(module.__file__).resolve() == (LIBRARY / (name + '.py')).resolve()
        for row in getattr(module, 'make_' + name.replace('_candidate', '') + '_candidate_theorems')(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    unit = load_file(PRIVATE_NAMES[2], UNIT_PATH)
    for row in unit.make_prime_field_polynomial_left_unit_candidate_theorems(TheoremSpec):
        assert row.name not in result or result[row.name] == row
        result[row.name] = row
    return result


def body_core():
    result = dict(provider_core())
    for row in rows():
        assert row.name not in result
        result[row.name] = row
    return result


And, At, Coeff, Lt, Le = oracle.And, oracle.At, oracle.Coeff, oracle.Lt, oracle.Le
Prime, Degree, Monic = oracle.Prime, oracle.Degree, oracle.Monic
Equivalent, RightDivides, Convolution = oracle.Equivalent, oracle.RightDivides, oracle.Convolution
contract, same_ast = oracle.contract, oracle.same_ast


def Normal(p, b, c, length):
    return f'({length})=0 \\/ (' + Monic(p, b, c, length) + ')'


def Common(p, db, dc, D, ab, ac, L, bb, bc, M):
    return And(RightDivides(p, db, dc, D, ab, ac, L), RightDivides(p, db, dc, D, bb, bc, M))


def RightGcd(p, gb, gc, G, ab, ac, L, bb, bc, M):
    db, dc, D = 'gu_expected_divisor_b', 'gu_expected_divisor_c', 'gu_expected_divisor_length'
    greatest = f'forall {db} {dc} {D}. (' + Common(p, db, dc, D, ab, ac, L, bb, bc, M) + ') -> (' + RightDivides(p, db, dc, D, gb, gc, G) + ')'
    return And(Common(p, gb, gc, G, ab, ac, L, bb, bc, M), greatest)


def NormalizedGcd(p, gb, gc, G, ab, ac, L, bb, bc, M):
    return And(Normal(p, gb, gc, G), RightGcd(p, gb, gc, G, ab, ac, L, bb, bc, M))


def Factorization(p, db, dc, D, ab, ac, L, d, a):
    qb, qc, e, pb, pc = ('gu_expected_qb', 'gu_expected_qc', 'gu_expected_e', 'gu_expected_pb', 'gu_expected_pc')
    return f'exists {qb} {qc} {e} {pb} {pc}. ' + And(
        Degree(p, qb, qc, 'S ' + e, e),
        Convolution(p, qb, qc, 'S ' + e, db, dc, D, pb, pc, 'S (' + a + ')'),
        Equivalent(pb, pc, 'S (' + a + ')', ab, ac, L), f'{e}+({d})=({a})')


PARS_FACTOR = ('p', 'db', 'dc', 'D', 'd', 'ab', 'ac', 'L', 'a')
PARS_ASSOC = ('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H')
PARS_GCD = PARS_ASSOC + ('ab', 'ac', 'L', 'bb', 'bc', 'M')
NAMES = (
    'prime_field_polynomial_nonzero_leading_equivalent_length_bound',
    'prime_field_polynomial_equivalent_represented_degrees_equal',
    'prime_field_polynomial_product_equivalent_nonzero_left_nonempty',
    'prime_field_polynomial_right_divides_represented_factorization',
    'prime_field_polynomial_right_divides_represented_degree_bound',
    'prime_field_polynomial_monic_singleton_multiple_equivalent',
    'prime_field_polynomial_monic_equal_degree_right_divides_equivalent',
    'prime_field_polynomial_monic_right_associates_equivalent',
    'prime_field_polynomial_empty_right_divisor_implies_equivalent_zero',
    'prime_field_polynomial_normal_right_associates_equivalent',
    'prime_field_polynomial_normalized_gcd_equivalent_unique',
)
# Exact nodes/depth from eleven successful fresh original-kernel invocations.
# Object sharing is observed separately, not fixed as a mathematical invariant.
METRICS = ((36, 22), (97, 32), (74, 38), (1029, 78), (46, 29), (322, 53),
           (170, 36), (656, 46), (85, 31), (99, 30), (116, 57))


def independent_contracts():
    degree_premises = (Prime('p'), Degree('p', 'db', 'dc', 'D', 'd'),
        Degree('p', 'ab', 'ac', 'L', 'a'), RightDivides('p', 'db', 'dc', 'D', 'ab', 'ac', 'L'))
    assoc_end = (RightDivides('p', 'gb', 'gc', 'G', 'hb', 'hc', 'H'), RightDivides('p', 'hb', 'hc', 'H', 'gb', 'gc', 'G'))
    assoc_result = Equivalent('gb', 'gc', 'G', 'hb', 'hc', 'H')
    return (
        (('ab', 'ac', 'd', 'bb', 'bc', 'M', 'a'),
         (At('ab', 'ac', '0', 'a'), '~(a=0)', Equivalent('ab', 'ac', 'S d', 'bb', 'bc', 'M')), Le('S d', 'M')),
        (('p', 'ab', 'ac', 'L', 'd', 'bb', 'bc', 'M', 'e'),
         (Degree('p', 'ab', 'ac', 'L', 'd'), Degree('p', 'bb', 'bc', 'M', 'e'), Equivalent('ab', 'ac', 'L', 'bb', 'bc', 'M')), 'd=e'),
        (('p', 'qb', 'qc', 'Q', 'db', 'dc', 'D', 'pb', 'pc', 'P', 'ab', 'ac', 'L', 'a'),
         (Degree('p', 'ab', 'ac', 'L', 'a'), Convolution('p', 'qb', 'qc', 'Q', 'db', 'dc', 'D', 'pb', 'pc', 'P'),
          Equivalent('pb', 'pc', 'P', 'ab', 'ac', 'L')), '~(Q=0)'),
        (PARS_FACTOR, degree_premises, Factorization('p', 'db', 'dc', 'D', 'ab', 'ac', 'L', 'd', 'a')),
        (PARS_FACTOR, degree_premises, Le('d', 'a')),
        (('p', 'kb', 'kc', 'db', 'dc', 'ab', 'ac', 'd', 'pb', 'pc'),
         (Prime('p'), Monic('p', 'db', 'dc', 'S d'), Monic('p', 'ab', 'ac', 'S d'),
          Convolution('p', 'kb', 'kc', '1', 'db', 'dc', 'S d', 'pb', 'pc', 'S d'),
          Equivalent('pb', 'pc', 'S d', 'ab', 'ac', 'S d')), Equivalent('db', 'dc', 'S d', 'ab', 'ac', 'S d')),
        (('p', 'db', 'dc', 'ab', 'ac', 'd'),
         (Prime('p'), Monic('p', 'db', 'dc', 'S d'), Monic('p', 'ab', 'ac', 'S d'),
          RightDivides('p', 'db', 'dc', 'S d', 'ab', 'ac', 'S d')), Equivalent('db', 'dc', 'S d', 'ab', 'ac', 'S d')),
        (PARS_ASSOC, (Prime('p'), Monic('p', 'gb', 'gc', 'G'), Monic('p', 'hb', 'hc', 'H'), *assoc_end), assoc_result),
        (('p', 'db', 'dc', 'ab', 'ac', 'L'), (RightDivides('p', 'db', 'dc', '0', 'ab', 'ac', 'L'),),
         Equivalent('ab', 'ac', 'L', 'db', 'dc', '0')),
        (PARS_ASSOC, (Prime('p'), Normal('p', 'gb', 'gc', 'G'), Normal('p', 'hb', 'hc', 'H'), *assoc_end), assoc_result),
        (PARS_GCD, (Prime('p'), NormalizedGcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M'),
         NormalizedGcd('p', 'hb', 'hc', 'H', 'ab', 'ac', 'L', 'bb', 'bc', 'M')), assoc_result),
    )


def test_exact_source_provider_and_kernel_inventory():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(oracle.oracle.KERNEL_PATH.read_bytes()).hexdigest() == oracle.oracle.KERNEL_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    core = provider_core()
    for index, row in enumerate(rows()):
        assert type(row) is TheoremSpec and row.script and row.name not in core
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
        assert not any(command.startswith(('admit', 'sorry', 'use ')) for command in row.script)
        assert not any('commut' in name for name in row.dependencies)


@pytest.mark.parametrize('index', range(len(NAMES)), ids=tuple(f'row{i:02d}' for i in range(len(NAMES))))
def test_independent_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_shared_graphs_are_exact_grouped_conservative_expansions():
    for actual, expected in (
        (candidate._normal('p', 'gb', 'gc', 'G', 'check'), Normal('p', 'gb', 'gc', 'G')),
        (candidate._right_gcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'check'), RightGcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M')),
        (candidate._normalized_gcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M', 'check'), NormalizedGcd('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M')),
        (candidate._right_divides('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'check'), RightDivides('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L')),
    ):
        variables = ('p', 'gb', 'gc', 'G', 'ab', 'ac', 'L', 'bb', 'bc', 'M')
        same_ast(_closed_formula(contract(variables, (), actual)), _closed_formula(contract(variables, (), expected)))


@pytest.mark.parametrize('name', PRIVATE_NAMES + ('peano_lab.library.editions_v33',))
def test_import_scope_preserves_preexisting_foreign_identities(name, monkeypatch):
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    before = protected_bindings()
    loaded = load_file(PRIVATE_NAMES[0], SOURCE)
    assert loaded is not foreign
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())


def test_direct_metadata_does_not_import_alpha_or_install_working_aliases():
    before = protected_bindings()
    provider_core()
    rows()
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[key] is value for key, value in before.items())


def test_source_only_uses_canonical_graph_imports_and_has_no_side_effect_registration():
    tree = ast.parse(SOURCE.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in ('__future__', 'typing') or node.module.startswith('peano_lab.library.prime_field_')
        assert not isinstance(node, (ast.Import, ast.Global, ast.Nonlocal))
    assert not any(word in SOURCE.read_text() for word in ('editions_v', 'sys.modules', 'setrecursionlimit', 'pickle', 'eval('))


def test_degree_route_trims_actual_quotient_and_constructs_independent_product():
    row = rows()[3]
    assert {'prime_field_polynomial_trim_exists', 'prime_field_polynomial_trim_nonempty_degree_exists',
        'prime_field_polynomial_convolution_at_length_exists', 'prime_field_polynomial_convolution_represented_degree',
        'prime_field_polynomial_convolution_equivalent_congruent_left'} <= set(row.dependencies)
    assert 'prime_field_no_zero_divisors' not in row.dependencies  # inherited through the actual degree law
    parameters, premises, conclusion = independent_contracts()[3]
    assert parameters == PARS_FACTOR and len(premises) == 4
    assert conclusion.startswith('exists ') and not any(item == conclusion for item in premises)


def test_monic_rigidity_uses_ordered_left_singleton_product_not_commutativity():
    assert 'prime_field_polynomial_convolution_left_unit_equivalent' in rows()[5].dependencies
    assert 'prime_field_multiply_one_right' in rows()[5].dependencies
    assert 'prime_field_polynomial_convolution_leading_coefficient' in rows()[5].dependencies
    assert 'specialize prime_field_polynomial_convolution_leading_coefficient (0)' in rows()[5].script


encoded, equivalent, actual_product, right_witness = oracle.encoded, oracle.equivalent, oracle.actual_product, oracle.right_witness
beta_oracle = oracle.oracle


def degree_model(p, poly, d):
    return poly[2] == d + 1 and beta_oracle.bounded(p, poly[:2], poly[2]) and beta_oracle.beta(poly[:2], 0) != 0


def normal_model(p, poly):
    return poly[2] == 0 or (beta_oracle.bounded(p, poly[:2], poly[2]) and beta_oracle.beta(poly[:2], 0) == 1)


POLYNOMIALS = ((), (0,), (0, 0), (1,), (1, 0), (0, 1), (1, 1), (1, 2, 0), (0, 0, 2, 1))


@pytest.mark.parametrize('values', POLYNOMIALS)
@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('padding', (0, 1, 3))
def test_beta_formal_equivalence_leading_length_bound_and_degree(values, p, padding):
    values = tuple(a % p for a in values)
    A = encoded(values, 1, 191)
    B = encoded((0,) * padding + values, 2, 193)
    assert equivalent(A, B) and A[:2] != B[:2]
    if A[2] and values[0]:
        assert degree_model(p, A, A[2] - 1)
        assert A[2] <= B[2]
        if padding:
            assert not degree_model(p, B, B[2] - 1)
        else:
            assert degree_model(p, B, A[2] - 1)


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('divisor', ((1,), (1, 0), (1, 1), (2, 1), (1, 2, 1)))
@pytest.mark.parametrize('quotient', ((1,), (2,), (1, 1), (0, 1), (0, 0, 1, 2)))
def test_actual_trimmed_quotient_factorization_and_degree_additivity(p, divisor, quotient):
    divisor = tuple(a % p for a in divisor)
    quotient = tuple(a % p for a in quotient)
    D, Q = encoded(divisor, 1), encoded(quotient, 2)
    _, Dt = oracle.actual_trim(p, D, 3)
    _, Qt = oracle.actual_trim(p, Q, 4)
    P, witnesses = actual_product(p, Q, Dt, 5)
    _, A = oracle.actual_trim(p, P, 6)
    assert right_witness(p, Dt, A, Q, P)
    C, other_witnesses = actual_product(p, Qt, Dt, 7)
    assert equivalent(C, A)
    if Dt[2] and A[2]:
        assert Qt[2] > 0 and degree_model(p, Qt, Qt[2] - 1)
        assert degree_model(p, Dt, Dt[2] - 1) and degree_model(p, A, A[2] - 1)
        assert (Qt[2] - 1) + (Dt[2] - 1) == A[2] - 1
        assert Dt[2] <= A[2]
    assert len(witnesses) == P[2] and len(other_witnesses) == C[2]


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('values', POLYNOMIALS)
def test_actual_unit_quotients_give_unique_normal_associates_but_not_codes(p, values):
    values = tuple(a % p for a in values)
    _, T = oracle.actual_trim(p, encoded(values), 2)
    if T[2]:
        k = pow(beta_oracle.beta(T[:2], 0), -1, p)
        normalized = tuple(k * a % p for a in beta_oracle.prefix(T[:2], T[2]))
    else:
        normalized = ()
    G, H = encoded(normalized, 3, 197), encoded(normalized, 4, 199)
    Q = encoded((1,), 5)
    GH, _ = actual_product(p, Q, G)
    HG, _ = actual_product(p, Q, H)
    assert normal_model(p, G) and normal_model(p, H)
    assert right_witness(p, G, H, Q, GH) and right_witness(p, H, G, Q, HG)
    assert equivalent(G, H) and G[:2] != H[:2]


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('length', range(4))
def test_empty_divisor_has_only_formal_zero_targets_including_leading_zeros(p, length):
    D, A, Q = encoded((), 1), encoded((0,) * length, 2), encoded((1, 1), 3)
    C, witnesses = actual_product(p, Q, D)
    assert C[2] == 0 and witnesses == ()
    assert right_witness(p, D, A, Q, C) and equivalent(A, D)
    assert not any(degree_model(p, A, d) for d in range(4))
    assert normal_model(p, A) == (length == 0)


@pytest.mark.parametrize('p,k', ((3, 2), (5, 2), (5, 3), (5, 4)))
def test_both_normal_premises_are_essential_scalar_associate_counterexamples(p, k):
    G, H = encoded((1, 1), 1), encoded((k, k), 2)
    K, J = encoded((k,), 3), encoded((pow(k, -1, p),), 4)
    C, _ = actual_product(p, K, G)
    E, _ = actual_product(p, J, H)
    assert right_witness(p, G, H, K, C) and right_witness(p, H, G, J, E)
    assert normal_model(p, G) and not normal_model(p, H) and not equivalent(G, H)
    assert normal_model(p, G) and not normal_model(p, H) and not equivalent(H, G)


def test_composite_modulus_cannot_replace_prime_in_degree_route():
    Q, D = encoded((2, 1), 1), encoded((2, 1), 2)
    P, _ = actual_product(4, Q, D)
    _, T = oracle.actual_trim(4, P, 3)
    assert degree_model(4, Q, 1) and degree_model(4, D, 1)
    assert T[2] - 1 != 2 and not degree_model(4, P, 2)


@pytest.mark.parametrize('p', (2, 3, 5))
def test_zero_zero_normalized_gcd_is_empty_not_one_and_evaluation_is_not_equivalence(p):
    Z, E, O = encoded((0, 0), 1), encoded((), 2), encoded((1,), 3)
    C, _ = actual_product(p, O, E)
    assert right_witness(p, E, Z, O, C)
    assert not right_witness(p, E, O, O, C)
    assert normal_model(p, E) and normal_model(p, O) and not equivalent(E, O)
    values = (1,) + (0,) * (p - 2) + (p - 1, 0)
    V = encoded(values, 4)
    for x in range(p):
        assert sum(a * x ** (len(values) - i - 1) for i, a in enumerate(values)) % p == 0
    assert not equivalent(E, V)


@pytest.mark.parametrize('index', range(len(NAMES)), ids=tuple(f'row{i:02d}' for i in range(len(NAMES))))
def test_actual_original_ha_body(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.command_count, receipt.dependency_count) == (len(row.script), len(row.dependencies))
    assert METRICS[index] is not None
    assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth <= 256


@pytest.mark.parametrize('index', range(len(NAMES)), ids=tuple(f'row{i:02d}' for i in range(len(NAMES))))
@pytest.mark.parametrize('mutation', ('false_conclusion', 'missing_body', 'truncated_body'))
def test_false_or_incomplete_body_is_rejected(index, mutation):
    row = rows()[index]
    parameters, premises, _ = independent_contracts()[index]
    changed = replace(row, statement=contract(parameters, premises, '0=1')) if mutation == 'false_conclusion' else replace(
        row, script=() if mutation == 'missing_body' else row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


EDGES = tuple((index, dependency) for index, row in enumerate(rows()) for dependency in row.dependencies)
EDGE_IDS = tuple(f'row{index:02d}-edge{position:02d}' for position, (index, _) in enumerate(EDGES))


@pytest.mark.parametrize('index,dependency', EDGES, ids=EDGE_IDS)
def test_each_removed_dependency_is_rejected(index, dependency):
    changed = replace(rows()[index], dependencies=tuple(name for name in rows()[index].dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=EDGE_IDS)
def test_each_poisoned_dependency_is_rejected(index, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=core)


PREMISES = tuple((i, j) for i, (_, premises, _) in enumerate(independent_contracts()) for j in range(len(premises)))


@pytest.mark.parametrize('index,position', PREMISES, ids=tuple(f'row{i:02d}-premise{j:02d}' for i, j in PREMISES))
def test_fixed_body_rejects_removed_input_clause(index, position):
    parameters, premises, result = independent_contracts()[index]
    changed = replace(rows()[index], statement=contract(parameters, premises[:position] + premises[position + 1:], result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index', (5, 6, 7, 9, 10))
def test_formal_equivalence_never_claims_unique_raw_codes(index):
    parameters, premises, _ = independent_contracts()[index]
    conclusion = 'db=ab' if index in (5, 6) else 'gb=hb'
    changed = replace(rows()[index], statement=contract(parameters, premises, conclusion))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())
