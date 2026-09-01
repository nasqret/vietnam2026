"""Independent native statements and beta-code models for Euclidean transport.

This file makes no proof-checker call.  Its expected statements use manually
expanded native arithmetic from the pinned identity tests, never a root
candidate relation builder.  Concrete CRT witnesses are integer examples,
not HA, Lean, closed-cone, admission, or saved-observation authority.
"""

from __future__ import annotations

import ast
from hashlib import sha256
import importlib.util
import inspect
from pathlib import Path
import re
import sys

import pytest


HERE = Path(__file__).resolve().parent
WORKING = HERE.parent
TRANSPORT = HERE / 'prime_field_polynomial_euclidean_transport_candidate.py'
BEZOUT = WORKING / 'prime-field-bezout-backward-v1/prime_field_polynomial_bezout_backward_candidate.py'
HELPERS = WORKING / 'prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py'
PINS = (
    (TRANSPORT, 18256, '9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30'),
    (BEZOUT, 18747, 'c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702'),
    (HELPERS, 31004, 'e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0'),
    (HELPERS.with_name('prime_field_polynomial_euclidean_identity_candidate.py'),
     11235, '8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77'),
)
PRIVATE = ('_transport_models_independent_syntax', '_transport_models_actual_transport',
           '_transport_models_actual_bezout')
FUTURE = ('peano_lab.library.prime_field_polynomial_euclidean_transport_candidate',
          'peano_lab.library.prime_field_polynomial_bezout_backward_candidate')


def pin_inputs():
    values = []
    for path, size, digest in PINS:
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (size, digest)
        values.append((str(path), size, digest))
    return tuple(values)


def protected_bindings():
    return {name: value for name, value in sys.modules.items()
            if name in (*PRIVATE, *FUTURE)
            or name.startswith(('peano_lab.library.editions', 'check_alpha_',
                                'build_peano_library_channels', 'verify_peano_library_channels'))}


def load_private(path, name):
    if name in sys.modules:
        raise ValueError('private source name already belongs to another owner')
    before, modules = pin_inputs(), protected_bindings()
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    assert before == pin_inputs() and name not in sys.modules
    after = protected_bindings()
    assert modules.keys() == after.keys()
    assert all(after[key] is value for key, value in modules.items())
    assert module.__file__ == str(path)
    return module


independent = load_private(HELPERS, PRIVATE[0])
transport = load_private(TRANSPORT, PRIVATE[1])
bezout_source = load_private(BEZOUT, PRIVATE[2])
TRANSPORT_ROWS = transport.make_prime_field_polynomial_euclidean_transport_candidate_theorems(independent.TheoremSpec)
BEZOUT_ROWS = bezout_source.make_prime_field_polynomial_bezout_backward_candidate_theorems(independent.TheoremSpec)
ROWS = (*TRANSPORT_ROWS, *BEZOUT_ROWS)
NAMES = tuple('prime_field_polynomial_' + stem for stem in (
    'right_divides_aligned_add', 'right_divides_aligned_subtract', 'right_divides_left_product',
    'common_right_divisor_euclidean_transport', 'division_execution_common_right_divisors',
    'euclidean_backward_coefficient_identity', 'bezout_euclidean_backward',
    'division_execution_bezout_backward'))


@pytest.fixture(autouse=True)
def actual_inputs_and_existing_owners_remain_unchanged():
    before, modules = pin_inputs(), protected_bindings()
    yield
    assert pin_inputs() == before
    after = protected_bindings()
    assert after.keys() == modules.keys()
    assert all(after[name] is value for name, value in modules.items())


def right_divides(p, db, dc, D, ab, ac, L):
    qb, qc, Q, pb, pc, P = ('independent_rd_' + role for role in ('qb', 'qc', 'Q', 'pb', 'pc', 'P'))
    witnesses = f'exists {qb} {qc} {Q} {pb} {pc} {P}. ' + independent.conj(
        independent.product(p, qb, qc, Q, db, dc, D, pb, pc, P),
        independent.equivalent(pb, pc, P, ab, ac, L))
    return independent.conj(independent.coeff(p, ab, ac, L), witnesses)


def common_divisor(p, db, dc, D, ab, ac, L, bb, bc, M):
    return independent.conj(right_divides(p, db, dc, D, ab, ac, L),
                            right_divides(p, db, dc, D, bb, bc, M))


def bezout(p, ab, ac, A, bb, bc, B, gb, gc, G, ub, uc, U, vb, vc, V):
    pb, pc, P, qb, qc, Q = ('independent_bz_' + role for role in ('pb', 'pc', 'P', 'qb', 'qc', 'Q'))
    return f'exists {pb} {pc} {P} {qb} {qc} {Q}. ' + independent.conj(
        independent.product(p, ub, uc, U, ab, ac, A, pb, pc, P),
        independent.product(p, vb, vc, V, bb, bc, B, qb, qc, Q),
        independent.aligned_add(p, pb, pc, P, qb, qc, Q, gb, gc, G))


def aligned_subtract(p, *polys):
    a, b, r = polys[:3], polys[3:6], polys[6:]
    return independent.aligned_add(p, *b, *r, *a)


def backward_result(p, A, B, Q, G, U, V):
    wb, wc, W, tb, tc, T = ('independent_update_' + role for role in ('wb', 'wc', 'W', 'tb', 'tc', 'T'))
    return f'exists {wb} {wc} {W} {tb} {tc} {T}. ' + independent.conj(
        independent.product(p, *V, *Q, wb, wc, W),
        aligned_subtract(p, *U, wb, wc, W, tb, tc, T),
        bezout(p, *A, *B, *G, *V, tb, tc, T))


def transport_contracts():
    D, A, B, R = ('db', 'dc', 'J'), ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')
    Q, P = ('qb', 'qc', 'H'), ('pb', 'pc', 'I')
    rows = []
    for operation in (independent.aligned_add, aligned_subtract):
        rows.append((('p', *D, *A, *B, *R),
                     (independent.prime('p'), right_divides('p', *D, *A), right_divides('p', *D, *B),
                      operation('p', *A, *B, *R)), right_divides('p', *D, *R)))
    rows.append((('p', *D, *B, *Q, *P),
                 (independent.prime('p'), right_divides('p', *D, *B), independent.product('p', *Q, *B, *P)),
                 right_divides('p', *D, *P)))
    source, target = common_divisor('p', *D, *A, *B), common_divisor('p', *D, *B, *R)
    rows.append((('p', *D, *A, *B, *Q, *P, *R),
                 (independent.prime('p'), independent.product('p', *Q, *B, *P),
                  independent.aligned_add('p', *P, *R, *A)),
                 independent.conj(f'({source}) -> ({target})', f'({target}) -> ({source})')))
    divisor, quotient = ('bb', 'bc', 'S d'), ('qb', 'qc', 'q')
    source, target = common_divisor('p', *D, *A, *divisor), common_divisor('p', *D, *divisor, *R)
    rows.append((('p', *A, 'bb', 'bc', 'd', *quotient, *R, *D),
                 (independent.prime('p'), independent.execution('p', *A, 'bb', 'bc', 'd', *quotient, *R)),
                 independent.conj(f'({source}) -> ({target})', f'({target}) -> ({source})')))
    return tuple(rows)


def bezout_contracts():
    A, B, R, Q, P, U, V, G, C, D, W, T, X, Y, Z, H = tuple(
        (letter + 'b', letter + 'c', 'L' + letter)
        for letter in ('a', 'b', 'r', 'q', 'p', 'u', 'v', 'g', 'c', 'd', 'w', 't', 'x', 'y', 'z', 'h'))
    polys = (A, B, R, Q, P, U, V, G, C, D, W, T, X, Y, Z, H)
    first = (('p', *(value for poly in polys for value in poly)), (
        independent.prime('p'), independent.product('p', *Q, *B, *P),
        independent.aligned_add('p', *P, *R, *A),
        independent.product('p', *U, *B, *C), independent.product('p', *V, *R, *D),
        independent.aligned_add('p', *C, *D, *G),
        independent.product('p', *V, *Q, *W), aligned_subtract('p', *U, *W, *T),
        independent.product('p', *V, *A, *X), independent.product('p', *T, *B, *Y),
        independent.product('p', *W, *B, *Z), independent.product('p', *V, *P, *H),
    ), independent.aligned_add('p', *X, *Y, *G))
    second = (('p', *A, *B, *R, *Q, *P, *G, *U, *V),
              (independent.prime('p'), independent.product('p', *Q, *B, *P),
               independent.aligned_add('p', *P, *R, *A), bezout('p', *B, *R, *G, *U, *V)),
              backward_result('p', A, B, Q, G, U, V))
    divisor = ('bb', 'bc', 'S d')
    third = (('p', *A, 'bb', 'bc', 'd', *Q, *R, *G, *U, *V),
             (independent.prime('p'), independent.execution('p', *A, 'bb', 'bc', 'd', *Q, *R),
              bezout('p', *divisor, *R, *G, *U, *V)),
             backward_result('p', A, divisor, Q, G, U, V))
    return first, second, third


CONTRACTS = (*transport_contracts(), *bezout_contracts())


def contract(parameters, premises, result):
    return independent.format_contract(' '.join(parameters), premises, result)


@pytest.mark.parametrize('index', range(8))
def test_all_eight_complete_claims_match_independent_native_expansions(index):
    assert independent.exact_ast(ROWS[index].statement) == independent.exact_ast(contract(*CONTRACTS[index]))


def test_exact_scope_retains_prime_actual_products_and_the_two_directions():
    assert tuple(row.name for row in ROWS) == NAMES
    assert tuple(len(premises) for _, premises, _ in CONTRACTS) == (4, 4, 3, 3, 2, 12, 4, 3)
    for params, premises, _ in CONTRACTS:
        assert independent.exact_ast(contract(params, (premises[0],), '0=0')) == independent.exact_ast(
            contract(params, (independent.prime('p'),), '0=0'))
    for index in (3, 4):
        assert ') -> (' in CONTRACTS[index][2]
        assert CONTRACTS[index][2].count('independent_rd_') > 0
    assert len(TRANSPORT_ROWS) == 5 and len(BEZOUT_ROWS) == 3


@pytest.mark.parametrize('path,size,digest', PINS, ids=lambda value: value.name if isinstance(value, Path) else str(value))
def test_actual_source_and_independent_helper_bytes_are_fixed(path, size, digest):
    raw = path.read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == (size, digest)


@pytest.mark.parametrize('name', PRIVATE)
def test_private_loader_preserves_and_rejects_a_foreign_owner(monkeypatch, name):
    owner = object()
    monkeypatch.setitem(sys.modules, name, owner)
    with pytest.raises(ValueError, match='another owner'):
        load_private(TRANSPORT, name)
    assert sys.modules[name] is owner


def test_only_manual_graphs_and_integer_models_are_reused_never_proof_fixtures():
    for helper in (independent.product, independent.coeff, independent.execution,
                   independent.aligned_add, independent.equivalent,
                   independent.actual_product_model, independent.aligned_witness_model):
        names = {node.id for node in ast.walk(ast.parse(inspect.getsource(helper)))
                 if isinstance(node, ast.Name)}
        assert not names.intersection({'candidate', 'rows', 'body_core', 'provider_core',
                                       'replay_candidate_bodies', 'BODY_SHAPES', 'receipt'})
    tree = ast.parse(Path(__file__).read_text())
    forbidden = {'replay_candidate_bodies', 'check_bundle', 'check_proof', 'checked_final',
                 'require_live', 'register_axiom', 'exec', 'eval'}
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    assert not any((isinstance(node.func, ast.Name) and node.func.id in forbidden)
                   or (isinstance(node.func, ast.Attribute) and node.func.attr in forbidden)
                   for node in calls)
    assert all(name not in sys.modules for name in PRIVATE)


PUBLIC = (
    (transport.prime_field_polynomial_common_right_divisor_relation, common_divisor, 10),
    (bezout_source.prime_field_polynomial_bezout_representation_relation, bezout, 16),
)


@pytest.mark.parametrize('builder,expected,arity', PUBLIC, ids=lambda value: getattr(value, '__name__', str(value)))
def test_new_composite_relations_expand_to_actual_products_and_grouped_sums(builder, expected, arity):
    names = tuple('arg' + str(i) for i in range(arity))
    scope = 'forall ' + ' '.join(names) + '. '
    actual = builder(*names, tag='public', variables=names)
    assert independent.exact_ast(scope + actual) == independent.exact_ast(scope + expected(*names))


COMPOUND = tuple((builder, expected, arity, index) for builder, expected, arity in PUBLIC for index in range(arity))


@pytest.mark.parametrize('builder,expected,arity,index', COMPOUND,
                         ids=lambda value: getattr(value, '__name__', str(value)))
def test_all_composite_graph_arguments_accept_hygienic_compound_terms(builder, expected, arity, index):
    names = tuple('arg' + str(i) for i in range(arity))
    args = list(names)
    args[index] = 'S (arg0*(arg1+1))'
    scope = 'forall ' + ' '.join(names) + '. '
    actual = builder(*args, tag='compound', variables=names)
    assert independent.exact_ast(scope + actual) == independent.exact_ast(scope + expected(*args))


@pytest.mark.parametrize('builder,expected,arity', PUBLIC, ids=lambda value: getattr(value, '__name__', str(value)))
@pytest.mark.parametrize('fault', ('empty_context', 'list_context', 'duplicate_context',
                                  'invalid_tag', 'undeclared_term', 'nonstring_term', 'capture'))
def test_composite_relations_reject_invalid_or_capturing_contexts(builder, expected, arity, fault):
    names = tuple('arg' + str(i) for i in range(arity))
    args, context, tag = list(names), names, 'hostile'
    if fault == 'empty_context':
        context = ()
    elif fault == 'list_context':
        context = list(names)
    elif fault == 'duplicate_context':
        context = (*names, names[0])
    elif fault == 'invalid_tag':
        tag = 'x. false'
    elif fault == 'undeclared_term':
        args[0] = 'not_declared'
    elif fault == 'nonstring_term':
        args[0] = 1
    elif fault == 'capture':
        raw = builder(*names, tag=tag, variables=names)
        binders = [name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.', raw)
                   for name in clause.split()]
        context = (*names, binders[0])
    with pytest.raises(ValueError):
        builder(*args, tag=tag, variables=context)


def test_backward_product_order_is_V_times_Q_in_the_native_statement():
    params, premises, result = CONTRACTS[5]
    U, V, Q, W = ('ub', 'uc', 'Lu'), ('vb', 'vc', 'Lv'), ('qb', 'qc', 'Lq'), ('wb', 'wc', 'Lw')
    assert independent.exact_ast(contract(params, (premises[6],), '0=0')) == independent.exact_ast(
        contract(params, (independent.product('p', *V, *Q, *W),), '0=0'))
    reversed_product = independent.product('p', *Q, *V, *W)
    changed = (*premises[:6], reversed_product, *premises[7:])
    assert independent.exact_ast(contract(params, changed, result)) != independent.exact_ast(ROWS[5].statement)
    assert premises[7] == aligned_subtract('p', *U, *W, 'tb', 'tc', 'Lt')
    assert all('commutative' not in dependency or 'aligned_add' in dependency
               for row in ROWS for dependency in row.dependencies)


def normalize(values):
    values = tuple(values)
    return values[next((i for i, value in enumerate(values) if value), len(values)):]


def poly_sum(p, left, right, *, subtract=False, exact_length=None, padding=0):
    K = max(len(left), len(right)) if exact_length is None else exact_length
    assert K >= max(len(left), len(right))
    left, right = (0,) * (K - len(left)) + tuple(left), (0,) * (K - len(right)) + tuple(right)
    values = tuple((a - b if subtract else a + b) % p for a, b in zip(left, right, strict=True))
    return values if exact_length is not None else (0,) * padding + normalize(values)


def proper_product(p, left, right):
    if not left or not right:
        return ()
    return tuple(sum(left[j] * right[i - j] for j in range(len(left)) if 0 <= i - j < len(right)) % p
                 for i in range(len(left) + len(right) - 1))


def aligned_data(p, left, right, result, salt=0):
    K = max(len(left), len(right), len(result))
    originals = tuple(independent.coded(values, salt + i + 1) for i, values in enumerate((left, right, result)))
    witnesses = tuple(independent.coded((0,) * (K - len(values)) + tuple(values), salt + i + 7)
                      for i, values in enumerate((left, right, result)))
    return originals, witnesses


def aligned_model(p, left, right, result, salt=0):
    originals, witnesses = aligned_data(p, left, right, result, salt)
    return independent.aligned_witness_model(p, *originals, *witnesses)


def divides_model(p, divisor, target, quotient, product, salt=0):
    d, a, q, r = (independent.coded(values, salt + i + 1)
                  for i, values in enumerate((divisor, target, quotient, product)))
    return (independent.canonical_model(p, a) and independent.actual_product_model(p, q, d, r)
            and independent.equivalent_model(r, a))


def bezout_model(p, A, B, G, U, V, P, Q, salt=0):
    a, b, u, v, left, right = (independent.coded(values, salt + i + 1)
                              for i, values in enumerate((A, B, U, V, P, Q)))
    return (independent.actual_product_model(p, u, a, left)
            and independent.actual_product_model(p, v, b, right)
            and aligned_model(p, P, Q, G, salt + 11))


QUOTIENT_CASES = tuple((p, D, U, V) for p in (2, 3, 5)
                       for D in ((), (0,), (1,), (p - 1, 1), (0, 1))
                       for U, V in (((), ()), ((), (1,)), ((1,), (0, 1)), ((1, 0), (p - 1,))))


@pytest.mark.parametrize('subtract', (False, True))
@pytest.mark.parametrize('p,D,U,V', QUOTIENT_CASES)
def test_real_quotient_addition_and_subtraction_produce_right_divisibility_witnesses(p, D, U, V, subtract):
    P, Q = proper_product(p, U, D), proper_product(p, V, D)
    A, B = (0,) + normalize(P), (0, 0) + normalize(Q)
    R = poly_sum(p, A, B, subtract=subtract, padding=3)
    W = poly_sum(p, U, V, subtract=subtract, exact_length=len(U) + len(V))
    T = proper_product(p, W, D)
    assert divides_model(p, D, A, U, P, 1) and divides_model(p, D, B, V, Q, 20)
    assert aligned_model(p, B, R, A) if subtract else aligned_model(p, A, B, R)
    assert aligned_model(p, V, W, U) if subtract else aligned_model(p, U, V, W)
    assert len(W) == len(U) + len(V)
    assert divides_model(p, D, R, W, T, 40)
    assert independent.equivalent_model(independent.coded(T, 1), independent.coded(R, 8))


COMMON_CASES = tuple((p, D, U, V, Q) for p in (2, 3, 5)
                     for D, U, V, Q in (
                         ((), (), (), ()), ((1,), (1,), (), ()),
                         ((1, 1), (1, 0), (), (1,)), ((1, 1), (1, 0), (1,), (1, 0)),
                         ((1,), (1, 1), (p - 1, 0), (p - 1, 1)),
                         ((0,), (1, 0), (1,), (1,))))


@pytest.mark.parametrize('p,D,U,V,Q', COMMON_CASES)
def test_euclidean_identity_transports_common_right_divisors_in_both_directions(p, D, U, V, Q):
    BP, RP = proper_product(p, U, D), proper_product(p, V, D)
    B, R = (0,) + normalize(BP), (0, 0) + normalize(RP)
    P = proper_product(p, Q, B)
    A = poly_sum(p, P, R, padding=3)
    QU = proper_product(p, Q, U)
    quotient_A = poly_sum(p, QU, V, exact_length=len(QU) + len(V))
    product_A = proper_product(p, quotient_A, D)
    assert aligned_model(p, P, R, A)
    assert divides_model(p, D, A, quotient_A, product_A)
    assert divides_model(p, D, B, U, BP)
    assert divides_model(p, D, R, V, RP)
    forward_quotient = poly_sum(p, quotient_A, QU, subtract=True,
                                exact_length=len(quotient_A) + len(QU))
    forward_product = proper_product(p, forward_quotient, D)
    assert divides_model(p, D, R, forward_quotient, forward_product, 10)
    backward_quotient = poly_sum(p, QU, V, exact_length=len(QU) + len(V))
    backward_product = proper_product(p, backward_quotient, D)
    assert divides_model(p, D, A, backward_quotient, backward_product, 30)


DIVISION_CASES = tuple((p, A, B) for p in (2, 3, 5) for A, B in (
    ((), (1,)), ((), (1, 1)), ((0,), (1,)), ((1,), (1, 0, 1)),
    ((1, 0, 1), (1, 1)), ((1, 0), (1, 1)),
    ((0, 1, p - 1, 1), (p - 1, 1)), ((p - 1, 1, 0), (p - 1,))))


@pytest.mark.parametrize('p,A,B', DIVISION_CASES)
def test_actual_division_execution_preserves_unit_common_divisor_and_empty_cases(p, A, B):
    Q, ambient, residual, cut, R = independent.independent.model_division(p, A, B)
    P = ambient if Q else ()
    assert independent.actual_product_model(p, independent.coded(Q, 1), independent.coded(B, 2),
                                             independent.coded(P, 3))
    assert independent.trim_model(p, independent.coded(residual, 4), cut, independent.coded(R, 5))
    assert aligned_model(p, P, R, A)
    for target in (A, B, R):
        assert divides_model(p, (1,), target, target, proper_product(p, target, (1,)), 7)
    if not Q:
        assert P == () and independent.equivalent_model(independent.coded(ambient), independent.coded(P))
    if not R:
        assert residual == (0,) * len(A)


MULTIPLIERS = (((), ()), ((1,), (1,)), ((0, 1), (1, 0)), ((1, 1), (0, 1, 1)))


@pytest.mark.parametrize('U,V', MULTIPLIERS)
@pytest.mark.parametrize('p,A,B', DIVISION_CASES)
def test_actual_backward_update_constructs_VQ_U_minus_VQ_and_both_new_products(p, A, B, U, V):
    Q, ambient, _, _, R = independent.independent.model_division(p, A, B)
    P = ambient if Q else ()
    C, D = proper_product(p, U, B), proper_product(p, V, R)
    G = poly_sum(p, C, D, padding=2)
    W = proper_product(p, V, Q)
    T = poly_sum(p, U, W, subtract=True, exact_length=len(U) + len(W))
    X, Y = proper_product(p, V, A), proper_product(p, T, B)
    Z, H = proper_product(p, W, B), proper_product(p, V, P)
    assert aligned_model(p, P, R, A)
    assert bezout_model(p, B, R, G, U, V, C, D)
    assert independent.actual_product_model(p, independent.coded(V, 4), independent.coded(Q, 5),
                                             independent.coded(W, 6))
    assert aligned_model(p, W, T, U)
    for left, right, result in ((V, A, X), (T, B, Y), (W, B, Z), (V, P, H)):
        assert independent.actual_product_model(p, independent.coded(left, 7), independent.coded(right, 8),
                                                 independent.coded(result, 9))
    assert independent.equivalent_model(independent.coded(Z, 11), independent.coded(H, 12))
    assert aligned_model(p, Z, Y, C) and aligned_model(p, H, D, X)
    assert bezout_model(p, A, B, G, V, T, X, Y, 20)
    assert len(T) == len(U) + len(W)
    if not Q:
        assert W == () and independent.equivalent_model(independent.coded(T), independent.coded(U))


@pytest.mark.parametrize('attack', ('wrong_division_product', 'wrong_old_left', 'wrong_old_right',
                                   'wrong_coefficient_product', 'wrong_difference_orientation',
                                   'wrong_new_left', 'wrong_new_right', 'wrong_target'))
def test_backward_models_reject_wrong_actual_products_updates_or_target(attack):
    p, A, B, U, V = 5, (1, 0, 0), (1, 1), (2, 1), (1, 1)
    Q, ambient, _, _, R = independent.independent.model_division(p, A, B)
    P = ambient if Q else ()
    C, D = proper_product(p, U, B), proper_product(p, V, R)
    G = poly_sum(p, C, D)
    W = proper_product(p, V, Q)
    T = poly_sum(p, U, W, subtract=True, exact_length=len(U) + len(W))
    X, Y = proper_product(p, V, A), proper_product(p, T, B)
    def wrong(values):
        return (*values[:-1], (values[-1] + 1) % p) if values else (1,)
    if attack == 'wrong_division_product':
        P = wrong(P)
    elif attack == 'wrong_old_left':
        C = wrong(C)
    elif attack == 'wrong_old_right':
        D = wrong(D)
    elif attack == 'wrong_coefficient_product':
        W = wrong(W)
    elif attack == 'wrong_difference_orientation':
        T = poly_sum(p, W, U, subtract=True, exact_length=len(U) + len(W))
    elif attack == 'wrong_new_left':
        X = wrong(X)
    elif attack == 'wrong_new_right':
        Y = wrong(Y)
    elif attack == 'wrong_target':
        G = wrong(G)
    def actual(left, right, result):
        return independent.actual_product_model(p, independent.coded(left), independent.coded(right),
                                                independent.coded(result))
    accepted = (actual(Q, B, P) and aligned_model(p, P, R, A)
                and bezout_model(p, B, R, G, U, V, C, D)
                and actual(V, Q, W) and aligned_model(p, W, T, U)
                and bezout_model(p, A, B, G, V, T, X, Y))
    assert not accepted


def test_evaluation_impostor_is_not_a_zero_dividend_or_bezout_target():
    impostor = (1, 1, 0)
    assert all((x * x + x) % 2 == 0 for x in range(2))
    assert not divides_model(2, (), impostor, (), ())
    assert not bezout_model(2, (), (), impostor, (), (), (), ())
    assert not independent.equivalent_model(independent.coded(impostor), independent.coded(()))


def test_zero_modulus_empty_graphs_do_not_remove_canonical_target_guards():
    assert divides_model(0, (), (), (), ())
    assert bezout_model(0, (), (), (), (), (), (), ())
    assert not divides_model(0, (), (0,), (), ())
    assert not divides_model(0, (0,), (), (), ())
    assert not bezout_model(0, (), (), (0,), (), (), (), ())
    assert not bezout_model(0, (0,), (), (), (), (), (), ())


def test_raw_beta_codes_and_lengths_are_not_the_transport_equality():
    first, second = independent.coded((0, 1), 3), independent.coded((1,), 8)
    assert first != second and first[2] != second[2]
    assert independent.equivalent_model(first, second)
    assert divides_model(3, (1,), (0, 0, 1), (1,), (1,), 9)
    assert bezout_model(3, (1,), (), (0, 0, 1), (1,), (), (1,), (), 20)
