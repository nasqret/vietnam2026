"""Independent recursive-gcd contracts, encoded examples, and native rejection.

The finite algorithms below only supply diagnostics.  They neither implement
the proof rule for induction nor supply a certificate accepted by the kernel.
Manual formulas and beta arithmetic are reused from frozen predecessor tests;
the candidate's formula helpers are not the expected-contract oracle.
"""

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
from itertools import product
import json
from pathlib import Path
import sys

import pytest

from peano_lab.library.theorems import TheoremSpec


HERE = Path(__file__).resolve().parent
WORKING = HERE.parent
SOURCE = HERE / 'prime_field_polynomial_gcd_existence_candidate.py'
PRIOR = WORKING / 'prime-field-euclidean-closure-v1/working_euclidean_closure_support.py'
LAWS = WORKING / 'prime-field-gcd-bezout-laws-v1/prime_field_polynomial_gcd_bezout_laws_candidate.py'
MANUAL = WORKING / 'prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py'
MODELS = WORKING / 'prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py'
PINS = {
    PRIOR: '2cf88350845af863835de0c96670a8f1aa96a102ef806e9a0c11b19cc8b6fb5d',
    LAWS: '76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c',
    MANUAL: 'e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791',
    MODELS: '0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab',
}


def load(path, name, *, controller=False):
    if name in sys.modules:
        raise ValueError('private test name already owned')
    if path in PINS:
        assert sha256(path.read_bytes()).hexdigest() == PINS[path]
    before = path.read_bytes()
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    if controller:
        sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
    finally:
        if controller:
            if sys.modules.get(name) is not module:
                raise ValueError('preserve a foreign replacement binding')
            del sys.modules[name]
    assert path.read_bytes() == before and name not in sys.modules
    return module


candidate = load(SOURCE, '_gcd_existence_test_candidate')
manual = load(MANUAL, '_gcd_existence_test_manual')
models = load(MODELS, '_gcd_existence_test_models')
And, Prime, Coeff, Le = manual.And, manual.Prime, manual.Coeff, manual.Le
A, B, G, U, V = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('gb', 'gc', 'G'), ('ub', 'uc', 'U'), ('vb', 'vc', 'V')
DIVISION = ('p', *A, 'bb', 'bc', 'd', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
NAMES = tuple('prime_field_polynomial_' + name for name in (
    'division_remainder_bounded', 'reduced_representative_exists',
    'gcd_bezout_empty_second', 'gcd_bezout_equivalent_second', 'gcd_bezout_division_backward',
    'gcd_bezout_exists_up_to', 'gcd_bezout_exists', 'bezout_is_right_gcd',
    'normalized_gcd_bezout_exists'))


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_gcd_existence_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def body_core():
    prior = load(PRIOR, '_gcd_existence_test_prior95', controller=True)
    previous = prior.load_candidate_state()
    assert prior.state_binding(previous, final=True) == '005eeadb5fe1798f531940bac31c9ae60d9346619459814b998500cb958b2449'
    laws = load(LAWS, '_gcd_existence_test_laws')
    core = prior.canonical_provider_table()
    for row in (*previous.rows, *laws.make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems(TheoremSpec), *rows()):
        assert row.name not in core
        core[row.name] = row
    return core


def Normal(p, gb, gc, length):
    return f'({length})=0 \\/ (' + manual.Monic(p, gb, gc, length) + ')'


def RightGcd(p, *polys):
    G, A, B = polys[:3], polys[3:6], polys[6:]
    D = ('expected_gcd_db', 'expected_gcd_dc', 'expected_gcd_D')
    return And(models.common_divisor(p, *G, *A, *B),
        'forall ' + ' '.join(D) + '. (' + models.common_divisor(p, *D, *A, *B)
        + ') -> (' + models.right_divides(p, *D, *G) + ')')


def NormalizedGcd(p, *polys):
    return And(Normal(p, *polys[:3]), RightGcd(p, *polys))


def Solution(p, A, B):
    return 'exists gb gc G ub uc U vb vc V. ' + And(Normal(p, *G),
        models.common_divisor(p, *G, *A, *B), models.bezout(p, *A, *B, *G, *U, *V))


def Reduced(p, A, T):
    return And(Coeff(p, *T), manual.Equivalent(*T, *A), Le(T[2], A[2]),
        f'({T[2]})=0 \\/ (exists expected_degree. ' + manual.Degree(p, *T, 'expected_degree') + ')')


def independent_contracts():
    BB, divisor, remainder = ('bb2', 'bc2', 'M2'), ('bb', 'bc', 'S d'), ('rb', 'rc', 'R')
    common_premises = (Prime('p'), Coeff('p', *A), Coeff('p', *B))
    final = 'exists gb gc G ub uc U vb vc V. ' + And(
        NormalizedGcd('p', *G, *A, *B), models.bezout('p', *A, *B, *G, *U, *V))
    return (
        (DIVISION, (manual.Execution(*DIVISION),), Coeff('p', *remainder)),
        (('p', *A), (Coeff('p', *A),), 'exists tb tc K. ' + Reduced('p', A, ('tb', 'tc', 'K'))),
        (('p', *A, 'bb', 'bc'), (Prime('p'), Coeff('p', *A)), Solution('p', A, ('bb', 'bc', '0'))),
        (('p', *A, *B, *BB), (Prime('p'), Coeff('p', *A), Coeff('p', *BB),
         manual.Equivalent(*B, *BB), Solution('p', A, B)), Solution('p', A, BB)),
        (DIVISION, (Prime('p'), manual.Execution(*DIVISION), Solution('p', divisor, remainder)),
         Solution('p', A, divisor)),
        (('n', 'p', *A, *B), (*common_premises, Le('M', 'n')), Solution('p', A, B)),
        (('p', *A, *B), common_premises, Solution('p', A, B)),
        (('p', *G, *A, *B, *U, *V), (Prime('p'), models.common_divisor('p', *G, *A, *B),
         models.bezout('p', *A, *B, *G, *U, *V)), RightGcd('p', *G, *A, *B)),
        (('p', *A, *B), common_premises, final),
    )


@pytest.fixture(autouse=True)
def source_unchanged_during_test():
    before = SOURCE.read_bytes()
    yield
    assert SOURCE.read_bytes() == before


@pytest.mark.parametrize('index', range(9), ids=tuple(f'row{i:02d}' for i in range(9)))
def test_entire_statement_matches_independent_expansion(index):
    expected = models.contract(*independent_contracts()[index])
    assert rows()[index].name == NAMES[index]
    assert models.independent.exact_ast(rows()[index].statement) == models.independent.exact_ast(expected)


PUBLIC = (
    (candidate.prime_field_polynomial_zero_or_monic_relation, Normal, 4),
    (candidate.prime_field_polynomial_right_gcd_relation, RightGcd, 10),
    (candidate.prime_field_polynomial_normalized_gcd_relation, NormalizedGcd, 10),
)


@pytest.mark.parametrize('builder,expected,arity', PUBLIC, ids=('zero-or-monic', 'right-gcd', 'normalized-gcd'))
def test_public_conservative_graph_accepts_compounds_hygienically(builder, expected, arity):
    variables = tuple('a' + str(i) for i in range(arity))
    for i in range(arity):
        arguments = list(variables)
        arguments[i] = 'S (a0*(a1+1))'
        scope = 'forall ' + ' '.join(variables) + '. '
        actual = builder(*arguments, tag='compound', variables=variables)
        assert models.independent.exact_ast(scope + actual) == models.independent.exact_ast(scope + expected(*arguments))


@pytest.mark.parametrize('builder,expected,arity', PUBLIC, ids=('zero-or-monic', 'right-gcd', 'normalized-gcd'))
def test_public_conservative_graph_rejects_undeclared_or_duplicate_context(builder, expected, arity):
    variables = tuple('a' + str(i) for i in range(arity))
    with pytest.raises(ValueError):
        builder(*variables, tag='safe', variables=variables + (variables[0],))
    with pytest.raises(ValueError):
        builder('undeclared', *variables[1:], tag='safe', variables=variables)


def test_both_input_triples_are_inside_the_induction_predicate():
    row = rows()[5]
    assert row.script[:2] == ('intro n', 'induction n')
    calls = tuple(command for command in row.script if command.startswith('specialize IH '))
    assert calls == tuple('specialize IH (' + term + ')' for term in ('p', 'x', 'x1', 'S x3', 'x7', 'x8', 'x9'))
    assert row.script.index('induction n') < row.script.index('intro ab')
    assert 'prime_field_polynomial_reduced_representative_exists' in row.dependencies
    assert 'prime_field_polynomial_division_remainder_length_descent' in row.dependencies


def recursive_example(p, A, B, bound=None, trace=None):
    """The same bounded recursion, with actual beta-coded division at each step."""
    bound = len(B) if bound is None else bound
    trace = [] if trace is None else trace
    assert len(B) <= bound and all(0 <= x < p for x in (*A, *B))
    trimmed = models.normalize(B)
    if not trimmed:
        reduced = models.normalize(A)
        inverse = pow(reduced[0], -1, p) if reduced else 0
        G = tuple(x * inverse % p for x in reduced)
        U, V = ((inverse,) if reduced else ()), ()
    else:
        assert bound > 0
        execution = manual.actual_execution(p, A, trimmed)
        Q, R = (manual.oracle.prefix(execution[i][:2], execution[i][2]) for i in (2, 6))
        assert len(R) <= len(trimmed) - 1 < len(trimmed) <= len(B) <= bound
        trace.append((bound, A, B, trimmed, Q, R))
        G, old_U, old_V, _ = recursive_example(p, trimmed, R, bound - 1, trace)
        U = old_V
        V = models.poly_sum(p, old_U, models.proper_product(p, old_V, Q), subtract=True)
    P, Q = models.proper_product(p, U, A), models.proper_product(p, V, B)
    assert models.bezout_model(p, A, B, G, U, V, P, Q, salt=7)
    assert not G or G[0] == 1
    return G, U, V, trace


PAIRS = (((), ()), ((0, 0), (0,)), ((1,), ()), ((), (1, 0)),
         ((0, 2, 1), (0, 0)), ((1, 0), (1,)), ((1,), (1, 0, 1)),
         ((1, 0, 0, 1), (1, 1)), ((0, 1, 2, 1), (0, 1, 1)),
         ((2, 1, 0, 1, 1), (1, 2, 1, 0)))


@pytest.mark.parametrize('p', (2, 3, 5))
@pytest.mark.parametrize('A,B', PAIRS, ids=tuple('pair' + str(i) for i in range(len(PAIRS))))
def test_recursive_witnesses_use_actual_division_and_decreasing_bound(p, A, B):
    A, B = tuple(x % p for x in A), tuple(x % p for x in B)
    G, U, V, trace = recursive_example(p, A, B)
    assert len(trace) <= len(B)
    assert all(right[0] == left[0] - 1 for left, right in zip(trace, trace[1:]))
    for target in (A, B):
        quotient, remainder = divide_values(p, target, G)
        assert not remainder
        assert models.divides_model(p, G, target, quotient, models.proper_product(p, quotient, G))


def divide_values(p, A, D):
    a, d = list(models.normalize(A)), models.normalize(D)
    if not d:
        return (), tuple(a)
    quotient = [0] * max(len(a) - len(d) + 1, 0)
    while a and len(a) >= len(d):
        shift, factor = len(a) - len(d), a[0] * pow(d[0], -1, p) % p
        quotient[len(quotient) - shift - 1] = factor
        for i, coefficient in enumerate(d):
            a[i] = (a[i] - factor * coefficient) % p
        a = list(models.normalize(a))
    return tuple(quotient), tuple(a)


@pytest.mark.parametrize('p', (2, 3, 5))
def test_every_small_common_divisor_divides_the_constructed_gcd(p):
    D = (1, 0, 1)
    A, B = models.proper_product(p, (1, 1), D), models.proper_product(p, (1, p - 1), D)
    G, _, _, _ = recursive_example(p, A, B)
    divisors = ((), (1,), *((1, x) for x in range(p)),
                *((1, x, y) for x, y in product(range(p), repeat=2)), G)
    for divisor in divisors:
        if any(divide_values(p, value, divisor)[1] for value in (A, B)):
            continue
        quotient, remainder = divide_values(p, G, divisor)
        assert not remainder
        assert models.divides_model(p, divisor, G, quotient, models.proper_product(p, quotient, divisor))


@pytest.mark.parametrize('p', (2, 3, 5))
def test_evaluation_zero_polynomial_is_not_treated_as_formal_zero(p):
    values = (1,) + (0,) * (p - 2) + (p - 1, 0)  # X^p-X
    assert all(sum(c * pow(x, len(values) - 1 - i, p) for i, c in enumerate(values)) % p == 0 for x in range(p))
    G, _, _, trace = recursive_example(p, values, ())
    assert G == values and G and not trace


def test_nonconstant_gcd_and_two_stage_back_substitution():
    # In F_5[X], (X^3-1)-X*(X^2-1)=X-1; the second division is exact.
    A, B = (1, 0, 0, 4), (1, 0, 4)
    G, U, V, trace = recursive_example(5, A, B)
    assert G == (1, 4) and len(trace) == 2
    assert models.bezout_model(5, A, B, G, U, V,
        models.proper_product(5, U, A), models.proper_product(5, V, B))
    # This particular pair also admits the explicit coefficients 1 and -X;
    # we do not assert that these or the beta encodings are unique.
    assert models.bezout_model(5, A, B, G, (1,), (4, 0), A, (4, 0, 1, 0))


@pytest.mark.parametrize('index', range(9), ids=tuple(f'row{i:02d}' for i in range(9)))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    receipt = replay_candidate_bodies((rows()[index],), core=body_core())[0]
    assert receipt.name == NAMES[index] and receipt.proof_depth <= 256
    print(json.dumps({'conditional_receipt': asdict(receipt)}, sort_keys=True), flush=True)


@pytest.mark.parametrize('index', range(9), ids=tuple(f'row{i:02d}' for i in range(9)))
@pytest.mark.parametrize('fault', ('false_conclusion', 'truncated_body'))
def test_native_rejects_false_or_incomplete_script(index, fault):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    row = rows()[index]
    pars, premises, _ = independent_contracts()[index]
    changed = replace(row, statement=models.contract(pars, premises, '0=1')) if fault == 'false_conclusion' else replace(row, script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('term,replacement', (('x', 'ab'), ('S x3', 'L'), ('x9', 'S n')))
def test_native_rejects_wrong_recursive_pair_or_bound(term, replacement):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    row = rows()[5]
    before, after = 'specialize IH (' + term + ')', 'specialize IH (' + replacement + ')'
    assert row.script.count(before) == 1
    changed = replace(row, script=tuple(after if command == before else command for command in row.script))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('position', range(3), ids=('prime', 'canonical-left', 'canonical-right'))
def test_native_rejects_unconditional_or_noncanonical_final_claim(position):
    from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
    pars, premises, result = independent_contracts()[-1]
    changed = replace(rows()[-1], statement=models.contract(pars, premises[:position] + premises[position + 1:], result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())
