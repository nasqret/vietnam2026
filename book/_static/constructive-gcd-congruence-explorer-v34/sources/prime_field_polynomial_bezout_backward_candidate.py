"""Constructive Euclidean backward transport of polynomial Bezout witnesses.

The coefficient update is (U,V) -> (V,U-V*Q) for A=Q*B+R.
Products are kept in that order. No commutativity of polynomial convolution,
desired sum identity, evaluation equality, or raw-code choice is assumed.
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



def _bezout(p: str, ab: str, ac: str, A: str, bb: str, bc: str, B: str,
            gb: str, gc: str, G: str, ub: str, uc: str, U: str,
            vb: str, vc: str, V: str, tag: str) -> str:
    witnesses = tuple('pfbz_' + role + '_' + tag for role in
                      ('left_code', 'left_scale', 'left_length', 'right_code', 'right_scale', 'right_length'))
    pb, pc, P, qb, qc, Q = witnesses
    return 'exists ' + ' '.join(witnesses) + '. ' + _and(
        _convolution(p, ub, uc, U, ab, ac, A, pb, pc, P, tag + '_left_product'),
        _convolution(p, vb, vc, V, bb, bc, B, qb, qc, Q, tag + '_right_product'),
        _aligned_add(p, pb, pc, P, qb, qc, Q, gb, gc, G, tag + '_sum'))


def prime_field_polynomial_bezout_representation_relation(
        p: str, ab: str, ac: str, A: str, bb: str, bc: str, B: str,
        gb: str, gc: str, G: str, ub: str, uc: str, U: str,
        vb: str, vc: str, V: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_bezout, (p, ab, ac, A, bb, bc, B, gb, gc, G, ub, uc, U, vb, vc, V),
                   tag=tag, variables=variables)


A, B, R, Q, P, U, V, G, C, D, W, T, X, Y, Z, H = tuple(
    (letter + 'b', letter + 'c', 'L' + letter)
    for letter in ('a', 'b', 'r', 'q', 'p', 'u', 'v', 'g', 'c', 'd', 'w', 't', 'x', 'y', 'z', 'h'))


def _bound(label, left, right, product, hypothesis):
    body = ('have ' + label + ' : ' + _coeff('p', *product, label + '_bounded'),)
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *left, *right, *product)
    return body + ('exact ' + hypothesis,)


def _identity_contract_data():
    polys = (A, B, R, Q, P, U, V, G, C, D, W, T, X, Y, Z, H)
    parameters = ('p', *(value for poly in polys for value in poly))
    premises = (
        _prime('p', 'backward_prime'),
        _convolution('p', *Q, *B, *P, 'backward_division_product'),
        _aligned_add('p', *P, *R, *A, 'backward_division_sum'),
        _convolution('p', *U, *B, *C, 'backward_old_left'),
        _convolution('p', *V, *R, *D, 'backward_old_right'),
        _aligned_add('p', *C, *D, *G, 'backward_old_sum'),
        _convolution('p', *V, *Q, *W, 'backward_coefficient_product'),
        _aligned_subtract('p', *U, *W, *T, 'backward_coefficient_difference'),
        _convolution('p', *V, *A, *X, 'backward_new_left'),
        _convolution('p', *T, *B, *Y, 'backward_new_right'),
        _convolution('p', *W, *B, *Z, 'backward_associated_product'),
        _convolution('p', *V, *P, *H, 'backward_distributed_product'),
    )
    return parameters, premises, _aligned_add('p', *X, *Y, *G, 'backward_result')


def _identity_row(spec: Callable[..., Any]) -> Any:
    parameters, premises, result = _identity_contract_data()
    body = _intro(*parameters, 'hp', 'hQB', 'hdivision', 'hUB', 'hVR', 'hold',
                  'hVQ', 'hsub', 'hVA', 'hTB', 'hWB', 'hVP')
    for label, left, right, product, hypothesis in (
            ('hXbound', V, A, X, 'hVA'), ('hYbound', T, B, Y, 'hTB'),
            ('hZbound', W, B, Z, 'hWB'), ('hDbound', V, R, D, 'hVR')):
        body += _bound(label, left, right, product, hypothesis)
    body += ('have hGbound : ' + _and(
        _coeff('p', *C, 'backward_old_C'), _coeff('p', *D, 'backward_old_D'), _coeff('p', *G, 'backward_old_G')),)
    body += _call('prime_field_polynomial_aligned_add_bounded', 'p', *C, *D, *G)
    body += ('exact hold',) + _parts('hGbound', 3)
    body += ('have hright : ' + _aligned_add('p', *Y, *Z, *C, 'backward_right_sum'),)
    body += _call('prime_field_polynomial_aligned_add_commutative', 'p', *Z, *Y, *C)
    body += _call('prime_field_polynomial_aligned_convolution_right_add', 'p', *W, *T, *U, *B, *Z, *Y, *C)
    body += ('exact hp', 'exact hsub', 'exact hWB', 'exact hTB', 'exact hUB')
    body += ('have hleft : ' + _aligned_add('p', *H, *D, *X, 'backward_left_sum'),)
    body += _call('prime_field_polynomial_aligned_convolution_left_add', 'p', *P, *R, *A, *V, *H, *D, *X)
    body += ('exact hp', 'exact hdivision', 'exact hVP', 'exact hVR', 'exact hVA')
    body += ('have heq : ' + _equivalent(*Z, *H, 'backward_associated_equivalent'),)
    body += _call('prime_field_polynomial_convolution_associative_equivalent', 'p', *V, *Q, *W, *B, *P, *Z, *H)
    body += ('exact hp', 'exact hVQ', 'exact hQB', 'exact hWB', 'exact hVP')
    body += ('have hmiddle : ' + _aligned_add('p', *Z, *D, *X, 'backward_middle_sum'),)
    body += _call('prime_field_polynomial_aligned_add_transport', 'p', *H, *D, *X, *Z, *D, *X)
    body += ('exact hZbound', 'exact hDbound', 'exact hXbound', 'exact heq')
    body += _call('prime_field_polynomial_power_coefficient_functional', *D)
    body += _call('prime_field_polynomial_power_coefficient_functional', *X) + ('exact hleft',)
    length = '(' + Y[2] + ')+(' + X[2] + ')'
    body += ('have hnew : exists ob oc. ' + _aligned_add('p', *Y, *X, 'ob', 'oc', length, 'backward_new_sum'),)
    body += _call('prime_field_polynomial_aligned_add_exists', 'p', *Y, *X)
    body += ('exact hp', 'exact hYbound', 'exact hXbound', 'cases hnew', 'cases hnew_witness')
    O = ('x', 'x1', length)
    body += ('have hresult : ' + _equivalent(*G, *O, 'backward_equivalent_result'),)
    body += _call('prime_field_polynomial_aligned_add_associative', 'p', *Y, *Z, *D, *C, *X, *G, *O)
    body += ('exact hp', 'exact hright', 'exact hold', 'exact hmiddle', 'exact hnew_witness_witness')
    body += _call('prime_field_polynomial_aligned_add_commutative', 'p', *Y, *X, *G)
    body += _call('prime_field_polynomial_aligned_add_transport', 'p', *Y, *X, *O, *Y, *X, *G)
    body += ('exact hYbound', 'exact hXbound', 'exact hGbound_right_right')
    body += _call('prime_field_polynomial_power_coefficient_functional', *Y)
    body += _call('prime_field_polynomial_power_coefficient_functional', *X)
    body += _call('prime_field_polynomial_equivalent_symmetric', *G, *O)
    body += ('exact hresult', 'exact hnew_witness_witness')
    return spec(
        'prime_field_polynomial_euclidean_backward_coefficient_identity',
        _contract(parameters, premises, result),
        ('prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_aligned_add_bounded',
         'prime_field_polynomial_aligned_add_commutative',
         'prime_field_polynomial_aligned_convolution_right_add',
         'prime_field_polynomial_aligned_convolution_left_add',
         'prime_field_polynomial_convolution_associative_equivalent',
         'prime_field_polynomial_aligned_add_transport',
         'prime_field_polynomial_power_coefficient_functional',
         'prime_field_polynomial_aligned_add_exists',
         'prime_field_polynomial_aligned_add_associative',
         'prime_field_polynomial_equivalent_symmetric'), body,
        'From genuine products and the actual difference T=U-V*Q, prove G=V*A+T*B by ordered distributivity, actual convolution associativity and aligned addition reassociation; the desired sum is a conclusion.',
    )


def _product(label, left, right, fresh, left_bound, right_bound):
    length, code, scale = fresh
    body = ('have ' + label + '_length : exists n. ' + _length(left[2], right[2], 'n', label + '_length'),)
    body += _call('polynomial_product_length_exists', left[2], right[2]) + ('cases ' + label + '_length',)
    body += ('have ' + label + '_product : exists b c. '
             + _convolution('p', *left, *right, 'b', 'c', length, label + '_product'),)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', *left, *right, length)
    body += ('exact hp0', 'exact ' + left_bound, 'exact ' + right_bound,
             'exact ' + label + '_length_witness', 'cases ' + label + '_product',
             'cases ' + label + '_product_witness')
    return body, (code, scale, length), label + '_product_witness_witness'


def _backward_result(p, A, B, Q, G, U, V, tag):
    wb, wc, W, tb, tc, T = tuple('pfbz_update_' + role + '_' + tag
                                for role in ('wb', 'wc', 'W', 'tb', 'tc', 'T'))
    return f'exists {wb} {wc} {W} {tb} {tc} {T}. ' + _and(
        _convolution(p, *V, *Q, wb, wc, W, tag + '_coefficient_product'),
        _aligned_subtract(p, *U, wb, wc, W, tb, tc, T, tag + '_coefficient_difference'),
        _bezout(p, *A, *B, *G, *V, tb, tc, T, tag + '_bezout'))


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B, *R, *Q, *P, *G, *U, *V)
    body = _intro(*parameters)
    # Specialize the original input parameters before the large actual
    # product contexts and existential witnesses are introduced. This is a
    # proved local universal lemma, not a new premise or a new theorem row.
    identity_parameters, identity_premises, identity_result = _identity_contract_data()
    body += ('have hstep : ' + _contract(identity_parameters[25:], identity_premises, identity_result),)
    body += _call('prime_field_polynomial_euclidean_backward_coefficient_identity',
                  *identity_parameters[:25])[:-1]
    body += ('exact prime_field_polynomial_euclidean_backward_coefficient_identity',)
    body += _intro('hp', 'hQB', 'hdivision', 'hbezout')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    tail = 'hbezout'
    for _ in range(6):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += _parts(tail, 3)
    C, D = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    # Project only the coefficient facts needed in the outer construction.
    # The large product/addition hypotheses are decomposed inside local
    # proofs, so their copied tails do not burden every later specialization.
    for label, poly, hypothesis, index in (
            ('hUbound', U, tail + '_left', 0),
            ('hBbound', B, tail + '_left', 1),
            ('hVbound', V, tail + '_right_left', 0),
            ('hQbound', Q, 'hQB', 0),
            ('hPbound', P, 'hdivision', 0),
            ('hAbound', A, 'hdivision', 2)):
        body += ('have ' + label + ' : ' + _coeff('p', *poly, label + '_local'),)
        body += _parts(hypothesis, index + 2)
        body += ('exact ' + hypothesis + '_right' * index + '_left',)
    commands, W, hW = _product('hcoefficient', V, Q, ('x6', 'x7', 'x8'), 'hVbound', 'hQbound')
    body += commands + _bound('hWbound', V, Q, W, hW)
    length = '(' + U[2] + ')+(' + W[2] + ')'
    body += ('have hdifference : exists tb tc. '
             + _aligned_subtract('p', *U, *W, 'tb', 'tc', length, 'exists_coefficient_difference'),)
    body += _call('prime_field_polynomial_aligned_subtract_exists', 'p', *U, *W)
    body += ('exact hp', 'exact hUbound', 'exact hWbound', 'cases hdifference', 'cases hdifference_witness')
    T = ('x9', 'x10', length)
    body += ('have htbound : ' + _coeff('p', *T, 'exists_difference_T'),)
    # Keep this already-declared small bound theorem in a local proof; its
    # unused coefficient clauses disappear when the local goal is closed.
    body += ('have hsmall : ' + _and(_coeff('p', *W, 'exists_difference_W'),
                                    _coeff('p', *T, 'exists_difference_T'),
                                    _coeff('p', *U, 'exists_difference_U')),)
    body += _call('prime_field_polynomial_aligned_add_bounded', 'p', *W, *T, *U)
    body += ('exact hdifference_witness_witness',) + _parts('hsmall', 3) + ('exact hsmall_right_left',)
    commands, X, hX = _product('hnewleft', V, A, ('x11', 'x12', 'x13'), 'hVbound', 'hAbound')
    body += commands
    commands, Y, hY = _product('hnewright', T, B, ('x14', 'x15', 'x16'), 'htbound', 'hBbound')
    body += commands
    # Z and H are auxiliary products for this identity, not output witnesses.
    # Construct and eliminate them locally, so their six codes/lengths and
    # large product contexts are discharged before packaging the result.
    body += ('have hresult : ' + _aligned_add('p', *X, *Y, *G, 'exists_backward_identity'),)
    commands, Z, hZ = _product('hassociate', W, B, ('x17', 'x18', 'x19'), 'hWbound', 'hBbound')
    body += commands
    commands, H, hH = _product('hdistribute', V, P, ('x20', 'x21', 'x22'), 'hVbound', 'hPbound')
    body += commands
    body += _call('hstep', *C, *D, *W, *T, *X, *Y, *Z, *H)
    body += ('exact hp', 'exact hQB', 'exact hdivision', 'exact ' + tail + '_left',
             'exact ' + tail + '_right_left', 'exact ' + tail + '_right_right',
             'exact ' + hW, 'exact hdifference_witness_witness',
             'exact ' + hX, 'exact ' + hY, 'exact ' + hZ, 'exact ' + hH)
    body += tuple('exists ' + value for value in (*W, *T))
    body += ('split', 'exact ' + hW, 'split', 'exact hdifference_witness_witness')
    body += tuple('exists ' + value for value in (*X, *Y))
    body += ('split', 'exact ' + hX, 'split', 'exact ' + hY, 'exact hresult')
    return spec(
        'prime_field_polynomial_bezout_euclidean_backward',
        _contract(parameters, (_prime('p', 'bezout_backward_prime'),
                               _convolution('p', *Q, *B, *P, 'bezout_backward_product'),
                               _aligned_add('p', *P, *R, *A, 'bezout_backward_identity'),
                               _bezout('p', *B, *R, *G, *U, *V, 'bezout_backward_original')),
                  _backward_result('p', A, B, Q, G, U, V, 'bezout_backward_result')),
        ('prime_nonzero', 'prime_field_polynomial_aligned_add_bounded',
         'polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_aligned_subtract_exists',
         'prime_field_polynomial_euclidean_backward_coefficient_identity'), body,
        'Construct W=V*Q, T=U-W, and genuine new products to turn an actual Bezout representation for (B,R) into one for (A,B), with both coefficient-update graphs returned as witnesses.',
    )


def _execution_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, 'bb', 'bc', 'd', *Q, *R, *G, *U, *V)
    B = ('bb', 'bc', 'S d')
    body = _intro(*parameters, 'hp', 'he', 'hb')
    body += ('have hi : exists pb pc N. ' + _and(
        _convolution('p', *Q, *B, 'pb', 'pc', 'N', 'execution_backward_product'),
        _aligned_add('p', 'pb', 'pc', 'N', *R, *A, 'execution_backward_identity')),)
    body += _call('prime_field_polynomial_division_execution_aligned_identity',
                  'p', *A, 'bb', 'bc', 'd', *Q, *R)
    body += ('exact hp', 'exact he', 'cases hi', 'cases hi_witness', 'cases hi_witness_witness',
             'cases hi_witness_witness_witness')
    body += _call('prime_field_polynomial_bezout_euclidean_backward',
                  'p', *A, *B, *R, *Q, 'x', 'x1', 'x2', *G, *U, *V)
    body += ('exact hp', 'exact hi_witness_witness_witness_left',
             'exact hi_witness_witness_witness_right', 'exact hb')
    return spec(
        'prime_field_polynomial_division_execution_bezout_backward',
        _contract(parameters, (_prime('p', 'execution_backward_prime'),
                               _division_execution('p', *A, 'bb', 'bc', 'd', *Q, *R,
                                                   'execution_backward_actual'),
                               _bezout('p', *B, *R, *G, *U, *V, 'execution_backward_original')),
                  _backward_result('p', A, B, Q, G, U, V, 'execution_backward_result')),
        ('prime_field_polynomial_division_execution_aligned_identity',
         'prime_field_polynomial_bezout_euclidean_backward'), body,
        'A real division execution automatically supplies the proper Euclidean identity and constructs the exact backward Bezout coefficient update, including an empty quotient.',
    )


def make_prime_field_polynomial_bezout_backward_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_identity_row(spec), _exists_row(spec), _execution_row(spec))


__all__ = ['make_prime_field_polynomial_bezout_backward_candidate_theorems',
           'prime_field_polynomial_bezout_representation_relation']
