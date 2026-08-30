"""Independent execution-uniqueness contracts and actual conditional HA.

The direct provider table contains source-derived theorem hypotheses only.
No closed proof, Lean result, edition entry, or publication authority is
created here.  Arithmetic models use actual beta encodings and distinguish
decoded prefix equality from equality of codes or polynomial evaluations.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
import importlib.util
import itertools
import math
from pathlib import Path
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


DIRECTORY = Path(__file__).parent


def load_file(name, filename, *, package_dependency=False):
    source = DIRECTORY / filename
    if package_dependency and name in sys.modules:
        module = sys.modules[name]
        assert Path(module.__file__).resolve() == source.resolve()
        return module
    loader = importlib.util.spec_from_file_location(name, source)
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    if package_dependency:
        sys.modules[name] = module
    try:
        loader.loader.exec_module(module)
    except BaseException:
        if package_dependency and sys.modules.get(name) is module:
            del sys.modules[name]
        raise
    return module


# Only the actual working source is loaded under its future package name.
# This is an import adapter, not a replacement theorem/checker implementation.
division = load_file('peano_lab.library.prime_field_polynomial_division_candidate',
                     'prime_field_polynomial_division_candidate.py', package_dependency=True)
candidate = load_file('working_polynomial_division_uniqueness_candidate',
                      'prime_field_polynomial_division_uniqueness_candidate.py')
independent = load_file('working_uniqueness_independent_contracts',
                        'test_prime_field_polynomial_division_candidate.py')

conj, at, lt, le = independent.conj, independent.at, independent.lt, independent.le
equal, add, multiply = independent.equal, independent.add, independent.multiply
step, prefix = independent.step, independent.prefix
prime, inverse, coeff, degree = independent.prime, independent.inverse, independent.coeff, independent.degree
trim, quotient_length = independent.trim, independent.quotient_length
quotient_data, residual_data, execution = independent.quotient_data, independent.residual_data, independent.execution
exact_ast, format_contract = independent.exact_ast, independent.format_contract


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_division_uniqueness_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.matrix_recursive_determinant_extensional_candidate import make_matrix_recursive_determinant_extensional_candidate_theorems

    result = independent.body_core()
    for row in make_matrix_recursive_determinant_extensional_candidate_theorems(TheoremSpec):
        assert row.name not in result or result[row.name] == row
        result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def execution_equal(qb, qc, q, rb, rc, R, QB, QC, Q, RB, RC, K):
    return conj(f'({q})=({Q})', equal(qb, qc, QB, QC, q),
                f'({R})=({K})', equal(rb, rc, RB, RC, R))


def contracts():
    base = ('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'qb', 'qc')
    initial = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd')
    first, second = ('qb', 'qc', 'q', 'rb', 'rc', 'R'), ('QB', 'QC', 'Q', 'RB', 'RC', 'K')
    actual = execution(*initial, *first)
    other = execution(*initial, *second)
    unique = execution_equal(*first, *second)
    data_first, data_second = ('b', 'k', 'q', 'qb', 'qc'), ('B', 'K', 'Q', 'QB', 'QC')
    residual_params = (*initial, 'qb', 'qc', 'QB', 'QC', 'q', 'pb', 'pc', 'ub', 'uc', 't', 'rb', 'rc', 'R',
                       'PB', 'PC', 'UB', 'UC', 'T', 'RB', 'RC', 'K')
    residual_first = (*initial, 'qb', 'qc', 'q', 'pb', 'pc', 'ub', 'uc', 't', 'rb', 'rc', 'R')
    residual_second = (*initial, 'QB', 'QC', 'q', 'PB', 'PC', 'UB', 'UC', 'T', 'RB', 'RC', 'K')
    return (
        (' '.join((*base, 'i', 'q', 'r')), (step(*base, 'i', 'q'), step(*base, 'i', 'r')), 'q=r'),
        (' '.join((*base, 'QB', 'QC', 'i', 'q', 'r')),
         (equal('qb', 'qc', 'QB', 'QC', 'i'), step(*base, 'i', 'q'),
          step('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', 'i', 'r')), 'q=r'),
        (' '.join((*base, 'QB', 'QC', 'N')), (prefix(*base, 'N'),
          prefix('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', 'N')),
         equal('qb', 'qc', 'QB', 'QC', 'N')),
        ('L d q Q', (quotient_length('L', 'd', 'q'), quotient_length('L', 'd', 'Q')), 'q=Q'),
        ('p b c B C L t rb rc R', (equal('b', 'c', 'B', 'C', 'L'), trim('p', 'b', 'c', 'L', 't', 'rb', 'rc', 'R')),
         trim('p', 'B', 'C', 'L', 't', 'rb', 'rc', 'R')),
        (' '.join((*initial, *data_first, *data_second)),
         (quotient_data(*initial, *data_first), quotient_data(*initial, *data_second)),
         conj('b=B', 'k=K', 'q=Q', equal('qb', 'qc', 'QB', 'QC', 'q'))),
        (' '.join(residual_params), (equal('qb', 'qc', 'QB', 'QC', 'q'),
          residual_data(*residual_first), residual_data(*residual_second)),
         conj('t=T', 'R=K', equal('rb', 'rc', 'RB', 'RC', 'R'))),
        (' '.join((*initial, *first, *second)), (actual, other), unique),
        (' '.join(initial), (prime('p'), coeff('p', 'ab', 'ac', 'L'), degree('p', 'bb', 'bc', 'S d', 'd')),
         f"exists {' '.join(first)}. " + conj(actual, f"forall {' '.join(second)}. ({other}) -> ({unique})")),
    )


EXPECTED_NAMES = (
    'prime_field_polynomial_quotient_step_functional',
    'prime_field_polynomial_quotient_step_prefix_functional',
    'prime_field_polynomial_quotient_prefix_functional',
    'polynomial_quotient_length_functional',
    'prime_field_polynomial_trim_input_transport',
    'prime_field_polynomial_division_quotient_data_functional',
    'prime_field_polynomial_division_residual_data_functional',
    'prime_field_polynomial_division_execution_functional',
    'prime_field_polynomial_division_execution_exists_unique',
)


def test_exact_local_inventory_and_dependency_topology():
    assert tuple(row.name for row in rows()) == EXPECTED_NAMES
    assert len(rows()) == len(contracts())
    known = set(provider_core())
    for row in rows():
        assert row.name not in known and row.script
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= known
        known.add(row.name)


@pytest.mark.parametrize('index', range(len(rows())))
def test_independently_expanded_exact_contract(index):
    assert exact_ast(rows()[index].statement) == exact_ast(format_contract(*contracts()[index]))


METRICS = ((212, 45), (128, 74), (298, 56), (77, 21), (111, 37),
           (267, 45), (416, 70), (652, 74), (76, 54))


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert receipt.dependency_count == len(row.dependencies)
        assert receipt.command_count == len(row.script)
        assert (receipt.proof_nodes, receipt.proof_depth) == METRICS[rows().index(row)]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
        print(receipt, flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(len(rows())))
def test_false_conclusion_rejected(index):
    names, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=format_contract(names, premises, '0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_missing_body_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row, script=()),), core=body_core())


EDGES = tuple((row, dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency', EDGES, ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_each_removed_dependency_rejected(row, dependency):
    changed = replace(row, dependencies=tuple(name for name in row.dependencies if name != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row,dependency', EDGES, ids=lambda value: value.name if hasattr(value, 'name') else value)
def test_each_poisoned_dependency_rejected(row, dependency):
    table = body_core()
    table[dependency] = replace(table[dependency], statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,), core=table)


def stronger_contracts():
    result = []
    for index, (names, premises, conclusion) in enumerate(contracts()):
        for position in range(len(premises)):
            result.append((index, 'removed_premise_' + str(position),
                           format_contract(names, tuple(p for i, p in enumerate(premises) if i != position), conclusion)))
    names, premises, _ = contracts()[2]
    result.extend((2, label, format_contract(names, premises, conclusion)) for label, conclusion in (
        ('quotient_codes_not_identical', 'qb=QB'),
        ('quotient_scales_not_identical', 'qc=QC'),
        ('unused_quotient_entry_unconstrained', equal('qb', 'qc', 'QB', 'QC', 'S N')),
    ))
    names, premises, _ = contracts()[7]
    result.extend((7, label, format_contract(names, premises, conclusion)) for label, conclusion in (
        ('execution_quotient_codes_not_identical', 'qb=QB'),
        ('execution_remainder_codes_not_identical', 'rb=RB'),
        ('unused_remainder_entry_unconstrained', equal('rb', 'rc', 'RB', 'RC', 'S R')),
    ))
    return tuple(result)


@pytest.mark.parametrize('index,label,statement', stronger_contracts(), ids=lambda value: value if isinstance(value, str) and len(value) < 100 else None)
def test_stronger_or_guardless_claim_rejected(index, label, statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index], statement=statement),), core=body_core())


def test_functionality_has_no_prime_or_identity_premise():
    for index in range(8):
        names, premises, _ = contracts()[index]
        assert prime('p') not in premises
        assert 'degree' not in rows()[index].name
    names, premises, _ = contracts()[-1]
    assert premises == (prime('p'), coeff('p', 'ab', 'ac', 'L'), degree('p', 'bb', 'bc', 'S d', 'd'))


encode_beta, beta_value = independent.encode_beta, independent.beta_value


def actual_execution(p, A, B, salt):
    """Actual finite arithmetic witnesses, not a formal-proof authority."""
    if p < 2 or not B or not 0 < B[0] < p or math.gcd(B[0], p) != 1:
        raise ValueError('the actual execution model needs a bounded invertible nonzero divisor head')
    if any(not 0 <= value < p for value in (*A, *B)):
        raise ValueError('the actual execution model needs canonical input coefficients')
    A, B = tuple(A), tuple(B)
    a_codes, b_codes = encode_beta(A), encode_beta(B)
    L, d = len(A), len(B) - 1
    q = max(L - d, 0)
    k = pow(B[0], -1, p)
    assert B[0] * k % p == 1
    values = []
    q_codes = encode_beta(values, salt=salt)
    for i in range(q):
        old_codes = q_codes
        diagonal = tuple((beta_value(old_codes, j) if j < i else 0)
                         * (beta_value(b_codes, i - j) if i - j < len(B) else 0)
                         for j in range(i + 1))
        previous = independent.assert_actual_beta_sum(diagonal) % p
        a = beta_value(a_codes, i)
        difference = (a - previous) % p
        value = k * difference % p
        assert 0 <= previous < p and 0 <= difference < p and 0 <= value < p
        assert (previous + difference) % p == a
        values.append(value)
        q_codes = encode_beta(values, salt=salt + i + 1)
        assert all(beta_value(old_codes, j) == beta_value(q_codes, j) for j in range(i))
        assert beta_value(q_codes, i) == value
    products = tuple(sum(values[j] * B[i - j] for j in range(q) if 0 <= i - j < len(B)) % p
                     for i in range(L))
    residuals = tuple((a - product) % p for a, product in zip(A, products, strict=True))
    cut = next((i for i, value in enumerate(residuals) if value != 0), L)
    remainder = residuals[cut:]
    p_codes, u_codes, r_codes = (encode_beta(v, salt=salt + 17) for v in (products, residuals, remainder))
    assert L == cut + len(remainder)
    assert all(beta_value(u_codes, i) == 0 for i in range(cut))
    assert all(beta_value(u_codes, cut + i) == beta_value(r_codes, i) for i in range(len(remainder)))
    assert not remainder or remainder[0] != 0
    return q, q_codes, len(remainder), r_codes, cut, p_codes, u_codes


MODEL_CASES = tuple(dict.fromkeys(
    (p, A, B)
    for p in (2, 3, 4, 5, 6)
    for A in ((), (0,), (1,), (p - 1,), (1, 0), (0, 1), (1, p - 1, 1), (0, 0, 0))
    for B in ((1,), (p - 1,), (1, 1), (p - 1, 1), (1, 0, 1))
))


@pytest.mark.parametrize('p,A,B', MODEL_CASES)
def test_actual_beta_executions_are_value_unique_but_codes_are_not(p, A, B):
    first, second = actual_execution(p, A, B, 0), actual_execution(p, A, B, 3)
    q, q_codes, R, r_codes, cut, p_codes, u_codes = first
    Q, Q_codes, K, R_codes, other_cut, P_codes, U_codes = second
    assert q == Q and R == K and cut == other_cut
    for length, left, right in ((q, q_codes, Q_codes), (R, r_codes, R_codes),
                                (len(A), p_codes, P_codes), (len(A), u_codes, U_codes)):
        assert left != right
        assert all(beta_value(left, i) == beta_value(right, i) for i in range(length))
    assert R <= len(B) - 1


@pytest.mark.parametrize('L,d', itertools.product(range(7), repeat=2))
def test_quotient_length_has_exactly_one_actual_natural_witness(L, d):
    witnesses = tuple(q for q in range(10) if q == 0 and L <= d or q != 0 and q + d == L)
    assert witnesses == (max(L - d, 0),)


@pytest.mark.parametrize('p,A,B', ((2, (1,), (0,)), (3, (), ()), (6, (1,), (2,)), (2, (2,), (1,))))
def test_nonzero_invertible_head_and_canonical_input_are_not_silently_dropped(p, A, B):
    with pytest.raises(ValueError):
        actual_execution(p, A, B, 0)


def test_characteristic_two_uses_field_one_and_allows_empty_remainder():
    q, Q, R, _, _, _, _ = actual_execution(2, (1, 0, 1), (1, 1), 0)
    assert q == 2 and R == 0
    assert tuple(beta_value(Q, i) for i in range(q)) == (1, 1)
    assert 1 * 1 % 2 == 1 and 2 % 2 == 0


def test_formal_polynomial_identity_does_not_force_a_chosen_representation_length():
    # Over F_3, (x+1)*1+0 has quotients (1) and (0,1) as formal
    # polynomials.  The second is a leading-zero recoding, not an execution
    # with the fixed length max(2-1,0)=1.  Arbitrary identity uniqueness needs
    # representation alignment; raw lengths cannot be inferred from it.
    short, padded = encode_beta((1,)), encode_beta((0, 1))
    assert beta_value(short, 0) == 1 and beta_value(padded, 0) == 0
    assert (1,) != (0, 1)
    assert tuple(reversed((1,))) == tuple(reversed((0, 1)))[:1]
    assert max(2 - 1, 0) == 1
