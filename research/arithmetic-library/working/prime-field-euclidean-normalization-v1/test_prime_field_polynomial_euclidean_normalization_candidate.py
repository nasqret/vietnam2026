"""Independent descent/normalization syntax, beta witnesses, and conditional HA.

The frozen left-constant test supplies independently written native graph
expansions and arithmetic model utilities, not proof acceptance.  All tested
proofs use the original dependency-curried HA checker.  No complete-cone,
Alpha, Lean, gcd-induction, or saved-receipt authority is used here.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
import importlib
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
LIBRARY = ROOT / 'peano-lab/py/peano_lab/library'
SOURCE = HERE / 'prime_field_polynomial_euclidean_normalization_candidate.py'
SOURCE_SHA256 = 'd2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f'
ORACLE_PATH = HERE.parent / 'prime-field-left-constant-v1/test_prime_field_polynomial_left_constant_candidate.py'
ORACLE_SHA256 = 'cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60'
DIVISIBILITY_PATH = HERE.parent / 'prime-field-divisibility-v1/prime_field_polynomial_divisibility_candidate.py'
DIVISIBILITY_SHA256 = 'f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8'
PRIVATE_NAMES = ('working_euclidean_normalization_candidate', 'working_euclidean_normalization_oracle',
                 'working_euclidean_normalization_divisibility_type')


def protected_bindings():
    return {name: module for name, module in sys.modules.items()
            if name.startswith('peano_lab.library.editions_v') or name in PRIVATE_NAMES
            or name in ('working_left_constant_candidate', 'working_left_constant_tail_type')}


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
PROVIDER_PINS = {
    **oracle.PROVIDER_PINS,
    'prime_field_polynomial_division_candidate.py': 'edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2',
    'prime_field_polynomial_degree_candidate.py': '3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5',
    'prime_field_polynomial_trim_candidate.py': '1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c',
    'prime_field_polynomial_monic_candidate.py': '3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef',
    'prime_field_polynomial_subtraction_candidate.py': 'd08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b',
}
FACTORIES = (
    ('prime_field_polynomial_division_candidate', 'make_prime_field_polynomial_division_candidate_theorems'),
    ('prime_field_polynomial_trim_candidate', 'make_prime_field_polynomial_trim_candidate_theorems'),
    ('prime_field_polynomial_monic_candidate', 'make_prime_field_polynomial_monic_candidate_theorems'),
    ('prime_field_polynomial_representation_candidate', 'make_prime_field_polynomial_representation_candidate_theorems'),
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_euclidean_normalization_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    assert sha256(oracle.SOURCE.read_bytes()).hexdigest() == oracle.SOURCE_SHA256
    assert sha256(DIVISIBILITY_PATH.read_bytes()).hexdigest() == DIVISIBILITY_SHA256
    for filename, digest in PROVIDER_PINS.items():
        assert sha256((LIBRARY / filename).read_bytes()).hexdigest() == digest
    result = dict(oracle.provider_core())
    for row in oracle.rows():
        assert row.name not in result
        result[row.name] = row
    for filename, factory in FACTORIES:
        module = importlib.import_module('peano_lab.library.' + filename)
        assert Path(module.__file__).resolve() == (LIBRARY / (filename + '.py')).resolve()
        for row in getattr(module, factory)(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    divisibility = load_file(PRIVATE_NAMES[2], DIVISIBILITY_PATH)
    for row in divisibility.make_prime_field_polynomial_divisibility_candidate_theorems(TheoremSpec):
        assert row.name not in result
        result[row.name] = row
    return result


def body_core():
    result = dict(provider_core())
    for row in rows():
        assert row.name not in result
        result[row.name] = row
    return result


And, At, Coeff, Lt, Le = oracle.And, oracle.At, oracle.Coeff, oracle.Lt, oracle.Le
Prime, Scale, Multiply, Convolution = oracle.Prime, oracle.Scale, oracle.Multiply, oracle.Convolution
contract, same_ast = oracle.contract, oracle.same_ast


def Repeat(b, c, a, length):
    i = 'en_expected_repeat_index'
    return f'forall {i}. ({Lt(i,length)}) -> ({At(b,c,i,a)})'


def Add(p, a, b, r):
    return And(Lt(a, p), Lt(b, p), oracle.Residue(p, f'({a})+({b})', r))


def Inverse(p, a, k):
    return And(f'~(({a})=0)', Multiply(p, a, k, '1'))


def Degree(p, b, c, length, d):
    a = 'en_expected_leading_value'
    return And(f'({length})=S ({d})', Coeff(p, b, c, length),
               f'exists {a}. ' + And(At(b, c, '0', a), f'~({a}=0)'))


def Suffix(b, c, t, d, e, length):
    i, a = 'en_expected_suffix_index', 'en_expected_suffix_value'
    return f'forall {i} {a}. ({Lt(i,length)}) -> ({At(b,c,f"({t})+{i}",a)}) -> ({At(d,e,i,a)})'


def Trim(p, b, c, length, t, d, e, retained):
    a = 'en_expected_trim_leading'
    return And(f'({length})=({t})+({retained})', Coeff(p, b, c, length), Repeat(b, c, '0', t),
               Suffix(b, c, t, d, e, retained),
               f'({retained})=0 \\/ (exists {a}. ' + And(At(d, e, '0', a), f'~({a}=0)') + ')')


def Subtract(p, ab, ac, bb, bc, rb, rc, length):
    i, a, b, r = ('en_expected_sub_index', 'en_expected_sub_left',
                  'en_expected_sub_right', 'en_expected_sub_result')
    return f'forall {i}. ({Lt(i,length)}) -> exists {a} {b} {r}. ' + And(
        At(ab, ac, i, a), At(bb, bc, i, b), At(rb, rc, i, r), Add(p, b, r, a))


def QuotientStep(p, k, ab, ac, bb, bc, M, qb, qc, i, q):
    a, c, s = 'en_expected_step_input', 'en_expected_step_previous', 'en_expected_step_difference'
    return f'exists {a} {c} {s}. ' + And(At(ab, ac, i, a),
        oracle.ConvolutionCoefficient(p, qb, qc, i, bb, bc, M, i, c),
        Add(p, c, s, a), Multiply(p, k, s, q))


def QuotientPrefix(p, k, ab, ac, bb, bc, M, qb, qc, length):
    i, q = 'en_expected_quotient_index', 'en_expected_quotient_value'
    return f'forall {i}. ({Lt(i,length)}) -> exists {q}. ' + And(
        At(qb, qc, i, q), QuotientStep(p, k, ab, ac, bb, bc, M, qb, qc, i, q))


def QuotientLength(L, d, q):
    return '(' + And(f'({q})=0', Le(L, d)) + ') \\/ (' + And(f'~(({q})=0)', f'({q})+({d})=({L})') + ')'


def ConvolutionPrefix(p, ab, ac, L, bb, bc, M, cb, cc, length):
    i, r = 'en_expected_prefix_index', 'en_expected_prefix_value'
    return f'forall {i}. ({Lt(i,length)}) -> exists {r}. ' + And(
        At(cb, cc, i, r), oracle.ConvolutionCoefficient(p, ab, ac, L, bb, bc, M, i, r))


def Execution(p, ab, ac, L, bb, bc, d, qb, qc, q, rb, rc, R):
    b, k, pb, pc, ub, uc, t = ('en_expected_head', 'en_expected_inverse', 'en_expected_product_code',
        'en_expected_product_scale', 'en_expected_residual_code', 'en_expected_residual_scale', 'en_expected_cut')
    data = And(At(bb, bc, '0', b), Inverse(p, b, k),
        QuotientPrefix(p, k, ab, ac, bb, bc, f'S ({d})', qb, qc, q),
        ConvolutionPrefix(p, qb, qc, q, bb, bc, f'S ({d})', pb, pc, L),
        Subtract(p, ab, ac, pb, pc, ub, uc, L), Trim(p, ub, uc, L, t, rb, rc, R))
    return And(Coeff(p, ab, ac, L), Coeff(p, bb, bc, f'S ({d})'), QuotientLength(L, d, q),
               f'exists {b} {k} {pb} {pc} {ub} {uc} {t}. ' + data)


def Power(b, c, length, power, value):
    i = 'en_expected_power_index'
    return '(exists ' + i + '. ' + And(f'{i}+S ({power})=({length})', At(b, c, i, value)) + ') \\/ (' + And(
        Le(length, power), f'({value})=0') + ')'


def Equivalent(b, c, length, d, e, other_length):
    k, a, r = 'en_expected_power', 'en_expected_power_left', 'en_expected_power_right'
    return f'forall {k} {a} {r}. ({Power(b,c,length,k,a)}) -> ({Power(d,e,other_length,k,r)}) -> {a}={r}'


def RightDivides(p, db, dc, D, ab, ac, L):
    qb, qc, q, pb, pc, length = ('en_expected_quotient_code', 'en_expected_quotient_scale',
        'en_expected_quotient_length', 'en_expected_actual_code', 'en_expected_actual_scale', 'en_expected_actual_length')
    return And(Coeff(p, ab, ac, L), f'exists {qb} {qc} {q} {pb} {pc} {length}. ' + And(
        Convolution(p, qb, qc, q, db, dc, D, pb, pc, length), Equivalent(pb, pc, length, ab, ac, L)))


def Monic(p, b, c, length):
    return And(f'~(({length})=0)', Coeff(p, b, c, length), At(b, c, '0', '1'))


def Normalization(p, k, ab, ac, bb, bc, length):
    a = 'en_expected_normalization_head'
    return And(f'~(({length})=0)', f'exists {a}. ' + And(At(ab, ac, '0', a), Inverse(p, a, k)),
               Scale(p, k, ab, ac, bb, bc, length))


DIVISION = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
CONSTANT = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
SCALE = ('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L')
NORMALIZATION = ('p', 'k', 'gb', 'gc', 'hb', 'hc', 'L')
NAMES = ('prime_field_polynomial_division_remainder_length_descent',
         'prime_field_polynomial_division_constant_remainder_empty',
         'prime_field_polynomial_scale_implies_right_divides',
         'prime_field_polynomial_monic_normalization_right_associates',
         'prime_field_polynomial_normalized_right_associate_exists')
# Exact nodes/depth observed in five fresh original-kernel body invocations.
METRICS = ((89, 37), (38, 34), (100, 35), (59, 26), (259, 48))


def independent_contracts():
    final = 'exists hb hc H. ' + And('H=0 \\/ (' + Monic('p', 'hb', 'hc', 'H') + ')',
        RightDivides('p', 'ab', 'ac', 'L', 'hb', 'hc', 'H'),
        RightDivides('p', 'hb', 'hc', 'H', 'ab', 'ac', 'L'))
    return (
        (DIVISION, (Prime('p'), Execution(*DIVISION)), And(Le('R', 'd'), Lt('R', 'S d'))),
        (CONSTANT, (Prime('p'), Execution('p', 'ab', 'ac', 'L', 'bb', 'bc', '0', 'qb', 'qc', 'q', 'rb', 'rc', 'R')), 'R=0'),
        (SCALE, (Prime('p'), Scale(*SCALE)), RightDivides('p', 'ab', 'ac', 'L', 'hb', 'hc', 'L')),
        (NORMALIZATION, (Prime('p'), Normalization(*NORMALIZATION)), And(
            RightDivides('p', 'gb', 'gc', 'L', 'hb', 'hc', 'L'),
            RightDivides('p', 'hb', 'hc', 'L', 'gb', 'gc', 'L'))),
        (('p', 'ab', 'ac', 'L'), (Prime('p'), Coeff('p', 'ab', 'ac', 'L')), final),
    )


def test_frozen_source_provider_and_kernel_inventory():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(oracle.KERNEL_PATH.read_bytes()).hexdigest() == oracle.KERNEL_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    core = provider_core()
    for index, row in enumerate(rows()):
        assert type(row) is TheoremSpec and row.script and row.name not in core
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= set(core) | set(NAMES[:index])
        assert not any('commut' in name for name in row.dependencies)
        assert not any(command.startswith(('admit', 'sorry', 'use ')) for command in row.script)
    assert candidate.__all__ == ['make_prime_field_polynomial_euclidean_normalization_candidate_theorems']


@pytest.mark.parametrize('index', range(5), ids=tuple(f'row{i:02d}' for i in range(5)))
def test_independent_fully_expanded_contract(index):
    same_ast(_closed_formula(rows()[index].statement), _closed_formula(contract(*independent_contracts()[index])))


def test_right_divides_is_exact_existing_nd0342_not_a_new_associate_oracle():
    source = load_file(PRIVATE_NAMES[2], DIVISIBILITY_PATH)
    parameters = ('p', 'db', 'dc', 'D', 'ab', 'ac', 'L')
    actual = candidate._right_divides(*parameters, 'normalization_existing_definition')
    old = source.prime_field_polynomial_right_divides_relation(*parameters, tag='normalization_frozen_definition', variables=parameters)
    same_ast(_closed_formula(contract(parameters, (), actual)), _closed_formula(contract(parameters, (), old)))
    same_ast(_closed_formula(contract(parameters, (), actual)), _closed_formula(contract(parameters, (), RightDivides(*parameters))))
    assert not any('associate' in dependency for row in rows()[:3] for dependency in row.dependencies)


@pytest.mark.parametrize('name', ('peano_lab.library.editions_v_normalization_guard', *PRIVATE_NAMES))
def test_explicit_source_loading_preserves_preloaded_module_identities(name, monkeypatch):
    marker = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, marker)
    before = protected_bindings()
    assert Path(load_file(PRIVATE_NAMES[0], SOURCE).__file__) == SOURCE
    assert Path(load_file(PRIVATE_NAMES[2], DIVISIBILITY_PATH).__file__) == DIVISIBILITY_PATH
    assert before.keys() == protected_bindings().keys()
    assert all(protected_bindings()[key] is value for key, value in before.items())
    assert sys.modules[name] is marker


def test_direct_metadata_does_not_introduce_alpha_or_temporary_aliases():
    before = protected_bindings()
    provider_core()
    after = protected_bindings()
    assert before.keys() == after.keys() and all(after[name] is value for name, value in before.items())
    assert sha256(ORACLE_PATH.read_bytes()).hexdigest() == ORACLE_SHA256
    assert sha256(oracle.SOURCE.read_bytes()).hexdigest() == oracle.SOURCE_SHA256
    assert sha256(oracle.TAIL_SOURCE.read_bytes()).hexdigest() == oracle.TAIL_SOURCE_SHA256


def test_source_contains_only_canonical_graph_imports_and_no_registration_side_effect():
    tree = ast.parse(SOURCE.read_text())
    assert not any(isinstance(node, ast.Import) for node in ast.walk(tree))
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert all(node.level == 0 for node in imports)
    assert all(node.module in ('__future__', 'typing') or node.module.startswith('peano_lab.library.') for node in imports)
    assert not any(isinstance(node, ast.Attribute) and node.attr == 'modules' for node in ast.walk(tree))
    assert not any('induction' in command or 'receipt' in command or 'commut' in command
                   for row in rows() for command in row.script)


def test_descent_uses_real_degree_length_and_separates_zero_before_successor_bound():
    script = rows()[0].script
    assert 'prime_field_polynomial_division_remainder_degree' in rows()[0].dependencies
    assert script.index('cases hdegree') < script.index('cases hdegree_right_witness_left')
    assert 'rewrite hdegree_right_witness_left_left' in script
    assert script.index('exact hdegree_right_witness_right') < script.index('split')
    assert 'specialize succ_le_succ (R)' in script
    assert 'prime_field_polynomial_division_remainder_length_descent' in rows()[1].dependencies


def test_scale_divisibility_constructs_product_and_transports_only_output_values():
    script = rows()[2].script
    assert any(command.startswith('have hactual : exists ub uc vb vc.') for command in script)
    assert 'prime_field_polynomial_left_constant_product_exists' in rows()[2].dependencies
    assert 'prime_field_polynomial_scale_functional' in rows()[2].dependencies
    assert 'prime_field_polynomial_equal_implies_equivalent' in rows()[2].dependencies
    assert 'exact hcopy_left' in script


def test_normalization_reverse_direction_uses_actual_recorded_inverse():
    script = rows()[3].script
    assert 'cases hcopy_right_left_witness' in script
    assert 'specialize prime_field_polynomial_inverse_scale (x)' in script
    assert 'exact hcopy_right_left_witness_right' in script
    assert any(command.startswith('have hreverse :') for command in script)
    assert rows()[3].dependencies == ('prime_field_polynomial_scale_implies_right_divides', 'prime_field_polynomial_inverse_scale')


def test_all_input_constructor_keeps_empty_products_outside_nonzero_degree_branch():
    script = rows()[4].script
    branch = script.index('cases hcase')
    degree = next(i for i, command in enumerate(script) if command.startswith('have hdegree :'))
    assert branch < script.index('exists 0') < degree
    assert 'prime_field_polynomial_right_divides_empty' in rows()[4].dependencies
    assert 'prime_field_polynomial_right_divides_equivalent_divisor' in rows()[4].dependencies
    assert 'prime_field_polynomial_right_divides_equivalent_target' in rows()[4].dependencies
    assert 'prime_field_polynomial_trim_nonempty_degree_exists' in rows()[4].dependencies
    assert all('inverse' not in command for command in script[branch:degree])


def test_local_novelty_uses_actual_parsed_direct_provider_types():
    previous = [_closed_formula(row.statement) for row in provider_core().values()]
    for row in rows():
        current = _closed_formula(row.statement)
        for old in previous:
            with pytest.raises(AssertionError):
                same_ast(current, old)
        previous.append(current)


def encoded(values, variant=1, tail=137):
    values = tuple(values)
    return (*oracle.encode_beta((*values, tail), variant), len(values))


def formal_value(poly, power):
    return oracle.beta(poly[:2], poly[2] - 1 - power) if power < poly[2] else 0


def equivalent(left, right):
    return all(formal_value(left, power) == formal_value(right, power)
               for power in range(max(left[2], right[2]) + 2))


def actual_product(p, left, right, variant=1):
    output, length, witnesses = oracle.actual_product(p, left[:2], left[2], right[:2], right[2], variant)
    return (*output, length), witnesses


def right_witness(p, divisor, target, quotient, product):
    if not oracle.bounded(p, target[:2], target[2]):
        return False
    actual, _ = actual_product(p, quotient, divisor, 7)
    return product[2] == actual[2] and oracle.prefix(product[:2], product[2]) == oracle.prefix(actual[:2], actual[2]) and equivalent(product, target)


def actual_trim(p, source, variant=1):
    assert oracle.bounded(p, source[:2], source[2])
    values = oracle.prefix(source[:2], source[2])
    cut = 0
    while cut < len(values) and values[cut] == 0:
        cut += 1
    target = encoded(values[cut:], variant, 139)
    assert source[2] == cut + target[2]
    assert all(oracle.beta(source[:2], i) == 0 for i in range(cut))
    assert all(oracle.beta(source[:2], cut + i) == oracle.beta(target[:2], i) for i in range(target[2]))
    assert target[2] == 0 or oracle.beta(target[:2], 0) != 0
    assert equivalent(source, target)
    return cut, target


def actual_execution(p, dividend_values, divisor_values):
    assert p in (2, 3, 5) and divisor_values and divisor_values[0] != 0
    assert all(0 <= value < p for value in (*dividend_values, *divisor_values))
    A, B = encoded(dividend_values, 1), encoded(divisor_values, 2)
    L, d = A[2], B[2] - 1
    inverse = pow(divisor_values[0], -1, p)
    assert 0 < inverse < p and divisor_values[0] * inverse % p == 1
    qlength = max(L - d, 0)
    assert (qlength == 0 and L <= d) or (qlength != 0 and qlength + d == L)
    quotients = []
    for i in range(qlength):
        prefix = encoded(quotients, 3)
        _, _, _, total = oracle.actual_diagonal(prefix[:2], i, B[:2], B[2], i, 4)
        previous = total % p
        difference = (dividend_values[i] - previous) % p
        assert (previous + difference) % p == dividend_values[i]
        quotients.append(inverse * difference % p)
    Q = encoded(quotients, 5)
    product_values = []
    for i in range(L):
        _, _, _, total = oracle.actual_diagonal(Q[:2], Q[2], B[:2], B[2], i, 6)
        residue = total % p
        assert total == residue + p * (total // p)
        product_values.append(residue)
    ambient = encoded(product_values, 7)
    residual_values = tuple((a - b) % p for a, b in zip(dividend_values, product_values))
    residual = encoded(residual_values, 8)
    assert all((oracle.beta(ambient[:2], i) + oracle.beta(residual[:2], i)) % p == oracle.beta(A[:2], i) for i in range(L))
    assert all(oracle.beta(residual[:2], i) == 0 for i in range(qlength))
    cut, R = actual_trim(p, residual, 9)
    if qlength:
        proper, _ = actual_product(p, Q, B)
        assert proper[2] == L and oracle.prefix(proper[:2], L) == tuple(product_values)
    else:
        assert all(value == 0 for value in product_values)
    return A, B, Q, ambient, residual, cut, R


DIVIDENDS = ((), (0,), (1,), (0, 0, 0), (1, 0), (0, 1, 0), (1, 2, 0, 1), (2, 3, 4, 0, 1))


@pytest.mark.parametrize('values', DIVIDENDS)
@pytest.mark.parametrize('divisor_kind', range(5))
@pytest.mark.parametrize('p', (2, 3, 5))
def test_actual_execution_beta_prefix_inverse_residual_trim_and_strict_descent(values, divisor_kind, p):
    divisors = ((1,), (p - 1,), (1, 1), (p - 1, 0, 1), (1, 0, 0, 1))
    result = actual_execution(p, tuple(value % p for value in values), divisors[divisor_kind])
    A, B, Q, ambient, residual, cut, R = result
    d = B[2] - 1
    assert R[2] <= d and R[2] < B[2]
    if R[2]:
        assert oracle.bounded(p, R[:2], R[2]) and oracle.beta(R[:2], 0) != 0
        assert R[2] - 1 < d
    else:
        assert cut == residual[2]
    if d == 0:
        assert R[2] == 0
    assert A[2] == ambient[2] == residual[2]
    assert Q[2] == max(A[2] - d, 0)


@pytest.mark.parametrize('values', DIVIDENDS)
@pytest.mark.parametrize('p', (2, 3, 5))
def test_actual_zero_or_monic_associate_has_two_real_left_quotient_witnesses(values, p):
    A = encoded(tuple(value % p for value in values), 1, 149)
    _, T = actual_trim(p, A, 2)
    if T[2] == 0:
        H = encoded((), 3, 151)
        quotient = encoded((), 4, 157)
        forward, _ = actual_product(p, quotient, A)
        reverse, _ = actual_product(p, quotient, H)
        assert right_witness(p, A, H, quotient, forward)
        assert right_witness(p, H, A, quotient, reverse)
        assert H[2] == 0
    else:
        head = oracle.beta(T[:2], 0)
        inverse = pow(head, -1, p)
        normalized = tuple(inverse * oracle.beta(T[:2], i) % p for i in range(T[2]))
        H = encoded(normalized, 3, 163)
        assert H[2] > 0 and oracle.beta(H[:2], 0) == 1 and oracle.bounded(p, H[:2], H[2])
        assert oracle.scale_model(p, inverse, T[:2], H[:2], T[2])
        assert oracle.scale_model(p, head, H[:2], T[:2], T[2])
        K, J = encoded((inverse,), 4), encoded((head,), 5)
        forward, _ = actual_product(p, K, A)
        reverse, _ = actual_product(p, J, H)
        assert right_witness(p, A, H, K, forward)
        assert right_witness(p, H, A, J, reverse)
        assert H[2] == T[2] and H[:2] != T[:2]
    assert equivalent(A, T)


@pytest.mark.parametrize('values', DIVIDENDS[:6])
@pytest.mark.parametrize('p,k', tuple((p, k) for p in (2, 3, 5) for k in range(p)))
def test_actual_scalar_divisibility_includes_zero_scalar_and_empty_codes(values, p, k):
    values = tuple(value % p for value in values)
    A = encoded(values, 1, 167)
    H = encoded(tuple(k * value % p for value in values), 2, 173)
    K = encoded((k,), 3, 179)
    product, _ = actual_product(p, K, A)
    assert oracle.scale_model(p, k, A[:2], H[:2], A[2])
    assert right_witness(p, A, H, K, product)
    assert product[:2] != H[:2]


def test_strict_bound_is_below_divisor_length_not_below_its_degree():
    A, B, _, _, _, _, R = actual_execution(3, (1,), (1, 0))
    assert A[2] == R[2] == B[2] - 1 == 1
    assert R[2] < B[2] and not R[2] < B[2] - 1


@pytest.mark.parametrize('p', (2, 3, 5))
def test_zero_has_no_nonzero_leading_degree_or_monic_normalization(p):
    zero = encoded((0, 0, 0), 1)
    _, trimmed = actual_trim(p, zero)
    assert trimmed[2] == 0 and oracle.beta(zero[:2], 0) == 0
    with pytest.raises(ValueError):
        pow(0, -1, p)
    assert all(oracle.beta(zero[:2], i) == 0 for i in range(zero[2]))


def test_prime_and_nonzero_leading_requirements_have_actual_failure_examples():
    with pytest.raises(ValueError):
        pow(2, -1, 6)
    with pytest.raises(AssertionError):
        actual_execution(3, (1, 2), (0, 1))
    empty = encoded((), 1)
    assert not oracle.scale_model(3, 3, empty[:2], empty[:2], 0)


def test_association_does_not_assert_same_values_same_codes_or_unique_bezout_coefficients():
    G = encoded((2, 1), 1, 181)
    H = encoded((1, 2), 2, 191)
    assert oracle.scale_model(3, 2, G[:2], H[:2], G[2])
    assert not equivalent(G, H) and G[:2] != H[:2]
    zero = encoded((), 3)
    vanishing = encoded((1, 1, 0), 4)
    assert all((x * x + x) % 2 == 0 for x in range(2))
    assert not equivalent(zero, vanishing)


@pytest.mark.parametrize('index', range(5), ids=tuple(f'row{i:02d}' for i in range(5)))
def test_actual_original_ha_body(index):
    row = rows()[index]
    receipt = replay_candidate_bodies((row,), core=body_core())[0]
    assert receipt.name == row.name
    assert (receipt.command_count, receipt.dependency_count) == (len(row.script), len(row.dependencies))
    assert METRICS[index] is not None
    assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes and receipt.proof_depth <= 256


@pytest.mark.parametrize('index', range(5), ids=tuple(f'row{i:02d}' for i in range(5)))
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
    row = rows()[index]
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('index,dependency', EDGES, ids=EDGE_IDS)
def test_each_poisoned_dependency_is_rejected(index, dependency):
    core = body_core()
    core[dependency] = replace(core[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((rows()[index],), core=core)


PREMISES = tuple((index, position) for index, (_, premises, _) in enumerate(independent_contracts())
                 for position in range(len(premises)))


@pytest.mark.parametrize('index,position', PREMISES,
                         ids=tuple(f'row{i:02d}-premise{j:02d}' for i, j in PREMISES))
def test_fixed_body_rejects_a_removed_input_clause(index, position):
    row = rows()[index]
    parameters, premises, result = independent_contracts()[index]
    changed = replace(row, statement=contract(parameters, premises[:position] + premises[position + 1:], result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


STRONGER = (
    (0, 'strict-below-degree', And(Le('R', 'd'), Lt('R', 'd'))),
    (1, 'nonempty-constant-remainder', '~(R=0)'),
    (2, 'scalar-preserves-values', Equivalent('ab', 'ac', 'L', 'hb', 'hc', 'L')),
    (3, 'raw-code-equality', 'gb=hb'),
    (4, 'zero-is-always-monic', 'exists hb hc H. ' + And(Monic('p', 'hb', 'hc', 'H'),
        RightDivides('p', 'ab', 'ac', 'L', 'hb', 'hc', 'H'),
        RightDivides('p', 'hb', 'hc', 'H', 'ab', 'ac', 'L'))),
)


@pytest.mark.parametrize('index,label,result', STRONGER,
                         ids=tuple(f'row{i:02d}-{label}' for i, label, _ in STRONGER))
def test_fixed_body_rejects_false_stronger_output(index, label, result):
    parameters, premises, _ = independent_contracts()[index]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=contract(parameters, premises, result)),),
                                 core=body_core())
