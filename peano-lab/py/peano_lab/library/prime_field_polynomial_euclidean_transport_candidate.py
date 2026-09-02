"""Right-factor divisibility under genuine aligned polynomial operations.

All quotient and proper-product witnesses are constructed. The old
RightDivides and aligned-addition expansions are literal conservative
definitions and are independently checked against their preceding sources.
No ring oracle, raw-code equality, or implicit product commutativity is used.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _parts, _prime, _public
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length
from peano_lab.library.prime_field_polynomial_division_candidate import _division_execution
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _common_representatives(ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                           ub: str, uc: str, vb: str, vc: str, K: str, tag: str) -> str:
    return _and(_equivalent(ab, ac, L, ub, uc, K, tag + '_left'),
                _equivalent(bb, bc, M, vb, vc, K, tag + '_right'))


def _aligned_witness(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                     rb: str, rc: str, N: str, ub: str, uc: str, vb: str, vc: str,
                     tb: str, tc: str, K: str, tag: str) -> str:
    return _and(_common_representatives(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K,
                                        tag + '_common'),
                _add(p, ub, uc, vb, vc, tb, tc, K, tag + '_operation'),
                _equivalent(tb, tc, K, rb, rc, N, tag + '_output'))


def _aligned_add(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                 rb: str, rc: str, N: str, tag: str) -> str:
    witnesses = tuple('pfaa_' + role + '_' + tag
                      for role in ('left_b', 'left_c', 'right_b', 'right_c',
                                   'sum_b', 'sum_c', 'length'))
    return _and(_coeff(p, ab, ac, L, tag + '_left_bounded'),
                _coeff(p, bb, bc, M, tag + '_right_bounded'),
                _coeff(p, rb, rc, N, tag + '_result_bounded'),
                'exists ' + ' '.join(witnesses) + '. '
                + _aligned_witness(p, ab, ac, L, bb, bc, M, rb, rc, N,
                                   *witnesses, tag + '_witness'))


def _aligned_subtract(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                      rb: str, rc: str, N: str, tag: str) -> str:
    return _aligned_add(p, bb, bc, M, rb, rc, N, ab, ac, L, tag)



def _right_divides(p: str, db: str, dc: str, D: str,
                  ab: str, ac: str, L: str, tag: str) -> str:
    qb, qc, Q, pb, pc, P = tuple('pfrd_' + role + '_' + tag
                                for role in ('qb', 'qc', 'qlen', 'pb', 'pc', 'plen'))
    product = _convolution(p, qb, qc, Q, db, dc, D, pb, pc, P, tag + '_product')
    equivalent = _equivalent(pb, pc, P, ab, ac, L, tag + '_target')
    witnesses = f'exists {qb} {qc} {Q} {pb} {pc} {P}. ' + _and(product, equivalent)
    return _and(_coeff(p, ab, ac, L, tag + '_canonical'), witnesses)


def _common_divisor(p: str, db: str, dc: str, D: str, ab: str, ac: str, L: str,
                    bb: str, bc: str, M: str, tag: str) -> str:
    return _and(_right_divides(p, db, dc, D, ab, ac, L, tag + '_left'),
                _right_divides(p, db, dc, D, bb, bc, M, tag + '_right'))


def prime_field_polynomial_common_right_divisor_relation(
        p: str, db: str, dc: str, D: str, ab: str, ac: str, L: str,
        bb: str, bc: str, M: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_common_divisor, (p, db, dc, D, ab, ac, L, bb, bc, M),
                   tag=tag, variables=variables)


def _destruct(name: str) -> tuple[tuple[str, ...], str]:
    graph = name + '_right' + '_witness' * 6
    commands = ('cases ' + name,)
    commands += tuple('cases ' + name + '_right' + '_witness' * i for i in range(6))
    return commands + ('cases ' + graph,), graph


D, A, B, R = ('db', 'dc', 'J'), ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')


def _product(label, left, right, fresh, left_bound, right_bound):
    length, code, scale = fresh
    body = ('have ' + label + '_length : exists n. ' + _length(left[2], right[2], 'n', label + '_length'),)
    body += _call('polynomial_product_length_exists', left[2], right[2])
    body += ('cases ' + label + '_length',)
    body += ('have ' + label + '_product : exists b c. '
             + _convolution('p', *left, *right, 'b', 'c', length, label + '_product'),)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', *left, *right, length)
    body += ('exact hp0', 'exact ' + left_bound, 'exact ' + right_bound,
             'exact ' + label + '_length_witness', 'cases ' + label + '_product',
             'cases ' + label + '_product_witness')
    return body, (code, scale, length), label + '_product_witness_witness'


def _closure_row(spec: Callable[..., Any], subtract: bool) -> Any:
    kind = 'subtract' if subtract else 'add'
    parameters = ('p', *D, *A, *B, *R)
    operation = _aligned_subtract if subtract else _aligned_add
    body = _intro(*parameters, 'hp', 'hDA', 'hDB', 'hop')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    first_commands, first = _destruct('hDA')
    second_commands, second = _destruct('hDB')
    body += first_commands + second_commands
    U, P = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    V, Q = ('x6', 'x7', 'x8'), ('x9', 'x10', 'x11')
    for label, quotient, product, graph in (('hfirst', U, P, first), ('hsecond', V, Q, second)):
        body += ('have ' + label + ' : ' + _convolution('p', *quotient, *D, *product, kind + '_' + label),
                 'exact ' + graph + '_left') + _parts(label, 4)
        body += ('have ' + label + '_bounded : ' + _coeff('p', *product, kind + '_' + label + '_bounded'),)
        body += _call('prime_field_polynomial_convolution_bounded', 'p', *quotient, *D, *product)
        body += ('exact ' + graph + '_left',)
    quotient_length = '(' + U[2] + ')+(' + V[2] + ')'
    body += ('have hw : exists wb wc. '
             + operation('p', *U, *V, 'wb', 'wc', quotient_length, kind + '_quotient_operation'),)
    body += _call('prime_field_polynomial_aligned_' + kind + '_exists', 'p', *U, *V)
    body += ('exact hp', 'exact hfirst_left', 'exact hsecond_left', 'cases hw', 'cases hw_witness')
    W = ('x12', 'x13', quotient_length)
    quotient_addends = (V, W, U) if subtract else (U, V, W)
    body += ('have hwbound : ' + _and(*(_coeff('p', *poly, kind + '_quotient_bound_' + str(index))
                                       for index, poly in enumerate(quotient_addends))),)
    body += _call('prime_field_polynomial_aligned_add_bounded', 'p',
                  *(value for poly in quotient_addends for value in poly))
    body += ('exact hw_witness_witness',) + _parts('hwbound', 3)
    commands, T, actual = _product('hresult', W, D, ('x14', 'x15', 'x16'),
                                   'hwbound_right_left' if subtract else 'hwbound_right_right',
                                   'hfirst_right_left')
    body += commands
    body += ('have htbound : ' + _coeff('p', *T, kind + '_result_bound'),)
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *W, *D, *T)
    body += ('exact ' + actual,)
    products = (Q, T, P) if subtract else (P, Q, T)
    product_hypotheses = (second + '_left', actual, first + '_left') if subtract else (first + '_left', second + '_left', actual)
    body += ('have hdistr : ' + _aligned_add('p', *(value for poly in products for value in poly), kind + '_distribution'),)
    body += _call('prime_field_polynomial_aligned_convolution_right_add',
                  'p', *(value for poly in quotient_addends for value in poly), *D,
                  *(value for poly in products for value in poly))
    body += ('exact hp', 'exact hw_witness_witness') + tuple('exact ' + h for h in product_hypotheses)
    if subtract:
        body += ('have hcompare : ' + _aligned_add('p', *B, *T, *A, 'subtract_comparison'),)
        body += _call('prime_field_polynomial_aligned_add_transport', 'p', *Q, *T, *P, *B, *T, *A)
        body += ('exact hDB_left', 'exact htbound', 'exact hDA_left')
        body += _call('prime_field_polynomial_equivalent_symmetric', *Q, *B) + ('exact ' + second + '_right',)
        body += _call('prime_field_polynomial_power_coefficient_functional', *T)
        body += ('exact ' + first + '_right', 'exact hdistr')
        body += ('have heq : ' + _equivalent(*T, *R, 'subtract_output_equivalent'),)
        body += _call('prime_field_polynomial_aligned_add_cancel_left', 'p', *B, *T, *R, *A)
        body += ('exact hp', 'exact hcompare', 'exact hop')
        operation_polys, result_bound = (B, R, A), 'hopbound_right_left'
    else:
        body += ('have hcompare : ' + _aligned_add('p', *P, *Q, *R, 'add_comparison'),)
        body += _call('prime_field_polynomial_aligned_add_transport', 'p', *A, *B, *R, *P, *Q, *R)
        body += ('exact hfirst_bounded', 'exact hsecond_bounded')
        body += ('have hrbound : ' + _and(_coeff('p', *A, 'add_input_A'),
                                         _coeff('p', *B, 'add_input_B'), _coeff('p', *R, 'add_input_R')),)
        body += _call('prime_field_polynomial_aligned_add_bounded', 'p', *A, *B, *R)
        body += ('exact hop',) + _parts('hrbound', 3) + ('exact hrbound_right_right',
                 'exact ' + first + '_right', 'exact ' + second + '_right')
        body += _call('prime_field_polynomial_power_coefficient_functional', *R) + ('exact hop',)
        body += ('have heq : ' + _equivalent(*T, *R, 'add_output_equivalent'),)
        body += _call('prime_field_polynomial_aligned_add_functional', 'p', *P, *Q, *T, *R)
        body += ('exact hp', 'exact hdistr', 'exact hcompare')
        operation_polys, result_bound = (A, B, R), 'hopbound_right_right'
    body += ('have hopbound : ' + _and(*(_coeff('p', *poly, kind + '_input_bound_' + str(index))
                                        for index, poly in enumerate(operation_polys))),)
    body += _call('prime_field_polynomial_aligned_add_bounded', 'p',
                  *(value for poly in operation_polys for value in poly))
    body += ('exact hop',) + _parts('hopbound', 3)
    body += _call('prime_field_polynomial_right_divides_from_product', 'p', *D, *R, *W, *T)
    body += ('exact ' + result_bound, 'exact ' + actual, 'exact heq')
    dependencies = ('prime_nonzero', 'prime_field_polynomial_convolution_bounded',
                    'prime_field_polynomial_aligned_' + kind + '_exists',
                    'prime_field_polynomial_aligned_add_bounded',
                    'polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
                    'prime_field_polynomial_aligned_convolution_right_add',
                    'prime_field_polynomial_aligned_add_transport',
                    'prime_field_polynomial_power_coefficient_functional',
                    'prime_field_polynomial_aligned_add_cancel_left' if subtract
                    else 'prime_field_polynomial_aligned_add_functional',
                    'prime_field_polynomial_right_divides_from_product')
    if subtract:
        dependencies += ('prime_field_polynomial_equivalent_symmetric',)
    return spec(
        'prime_field_polynomial_right_divides_aligned_' + kind,
        _contract(parameters, (_prime('p', kind + '_divides_prime'),
                               _right_divides('p', *D, *A, kind + '_divides_left'),
                               _right_divides('p', *D, *B, kind + '_divides_right'),
                               operation('p', *A, *B, *R, kind + '_divides_operation')),
                  _right_divides('p', *D, *R, kind + '_divides_result')),
        dependencies, body,
        'A common actual right divisor divides the genuine aligned ' + kind
        + ': construct the corresponding quotient operation and its proper product, use checked right distributivity and compare real aligned sums.',
    )


def _left_product_row(spec: Callable[..., Any]) -> Any:
    Q, P = ('qb', 'qc', 'H'), ('pb', 'pc', 'I')
    parameters = ('p', *D, *B, *Q, *P)
    body = _intro(*parameters, 'hp', 'hd', 'hc')
    body += _call('prime_field_polynomial_right_divides_transitive', 'p', *D, *B, *P)
    body += ('exact hp', 'exact hd')
    body += _call('prime_field_polynomial_right_divides_from_product', 'p', *B, *P, *Q, *P)
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *Q, *B, *P)
    body += ('exact hc', 'exact hc')
    body += _call('prime_field_polynomial_power_coefficient_functional', *P)
    return spec(
        'prime_field_polynomial_right_divides_left_product',
        _contract(parameters, (_prime('p', 'left_product_prime'),
                               _right_divides('p', *D, *B, 'left_product_divisor'),
                               _convolution('p', *Q, *B, *P, 'left_product_actual')),
                  _right_divides('p', *D, *P, 'left_product_result')),
        ('prime_field_polynomial_right_divides_transitive',
         'prime_field_polynomial_right_divides_from_product',
         'prime_field_polynomial_convolution_bounded',
         'prime_field_polynomial_power_coefficient_functional'), body,
        'An actual right divisor of B divides every actual left multiple Q*B; the composed quotient is supplied by the checked constructive transitivity theorem.',
    )


def _common_divisor_transport_row(spec: Callable[..., Any]) -> Any:
    Q, P = ('qb', 'qc', 'H'), ('pb', 'pc', 'I')
    parameters = ('p', *D, *A, *B, *Q, *P, *R)
    source = _common_divisor('p', *D, *A, *B, 'euclidean_common_source')
    target = _common_divisor('p', *D, *B, *R, 'euclidean_common_target')
    body = _intro(*parameters, 'hp', 'hc', 'hs') + ('split', 'intro hd', 'cases hd',
                                                  'split', 'exact hd_right')
    body += _call('prime_field_polynomial_right_divides_aligned_subtract', 'p', *D, *A, *P, *R)
    body += ('exact hp', 'exact hd_left')
    body += _call('prime_field_polynomial_right_divides_left_product', 'p', *D, *B, *Q, *P)
    body += ('exact hp', 'exact hd_right', 'exact hc', 'exact hs',
             'intro hd', 'cases hd', 'split')
    body += _call('prime_field_polynomial_right_divides_aligned_add', 'p', *D, *P, *R, *A)
    body += ('exact hp',)
    body += _call('prime_field_polynomial_right_divides_left_product', 'p', *D, *B, *Q, *P)
    body += ('exact hp', 'exact hd_left', 'exact hc', 'exact hd_right', 'exact hs', 'exact hd_left')
    return spec(
        'prime_field_polynomial_common_right_divisor_euclidean_transport',
        _contract(parameters, (_prime('p', 'euclidean_common_prime'),
                               _convolution('p', *Q, *B, *P, 'euclidean_common_product'),
                               _aligned_add('p', *P, *R, *A, 'euclidean_common_identity')),
                  _and('(' + source + ') -> (' + target + ')',
                       '(' + target + ') -> (' + source + ')')),
        ('prime_field_polynomial_right_divides_aligned_subtract',
         'prime_field_polynomial_right_divides_left_product',
         'prime_field_polynomial_right_divides_aligned_add'), body,
        'A genuine Euclidean identity A=Q*B+R preserves precisely the actual common right divisors in both directions, using constructed quotient sums and differences.',
    )


def _execution_common_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, 'bb', 'bc', 'd', 'qb', 'qc', 'q', *R, *D)
    divisor, quotient = ('bb', 'bc', 'S d'), ('qb', 'qc', 'q')
    source = _common_divisor('p', *D, *A, *divisor, 'execution_common_source')
    target = _common_divisor('p', *D, *divisor, *R, 'execution_common_target')
    body = _intro(*parameters, 'hp', 'he')
    body += ('have hi : exists pb pc I. ' + _and(
        _convolution('p', *quotient, *divisor, 'pb', 'pc', 'I', 'execution_common_product'),
        _aligned_add('p', 'pb', 'pc', 'I', *R, *A, 'execution_common_sum')),)
    body += _call('prime_field_polynomial_division_execution_aligned_identity',
                  'p', *A, 'bb', 'bc', 'd', *quotient, *R)
    body += ('exact hp', 'exact he', 'cases hi', 'cases hi_witness', 'cases hi_witness_witness',
             'cases hi_witness_witness_witness')
    body += _call('prime_field_polynomial_common_right_divisor_euclidean_transport',
                  'p', *D, *A, *divisor, *quotient, 'x', 'x1', 'x2', *R)
    body += ('exact hp', 'exact hi_witness_witness_witness_left', 'exact hi_witness_witness_witness_right')
    return spec(
        'prime_field_polynomial_division_execution_common_right_divisors',
        _contract(parameters, (_prime('p', 'execution_common_prime'),
                               _division_execution('p', *A, 'bb', 'bc', 'd', *quotient, *R,
                                                   'execution_common_actual')),
                  _and('(' + source + ') -> (' + target + ')',
                       '(' + target + ') -> (' + source + ')')),
        ('prime_field_polynomial_division_execution_aligned_identity',
         'prime_field_polynomial_common_right_divisor_euclidean_transport'), body,
        'Every genuine polynomial division execution preserves common right divisors, including the empty quotient and zero remainder, with its aligned identity constructed from the execution.',
    )


def make_prime_field_polynomial_euclidean_transport_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_closure_row(spec, False), _closure_row(spec, True), _left_product_row(spec),
            _common_divisor_transport_row(spec), _execution_common_row(spec))


__all__ = ['make_prime_field_polynomial_euclidean_transport_candidate_theorems',
           'prime_field_polynomial_common_right_divisor_relation']
