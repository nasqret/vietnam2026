"""Actual Bezout witnesses: terminal construction, recoding and greatestness.

The conservative graphs are literal copies of ND0342, ND0346 and ND0347.
Products retain the left coefficient/right input order.  No polynomial
commutativity, evaluation equality, gcd existence, or proof authority is
assumed.  This module imports canonical syntax helpers only.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _parts, _prime
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff, _repeat
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length
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


A, B, G, U, V, D = tuple((letter + 'b', letter + 'c', letter.upper())
                         for letter in ('a', 'b', 'g', 'u', 'v', 'd'))
EMPTY = ('0', '0', '0')


def _empty_add_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A)
    body = _intro(*parameters, 'hp', 'ha')
    body += ('have hz : exists zb zc. ' + _repeat('zb', 'zc', '0', A[2], 'empty_add_zeros'),)
    body += _call('beta_repeat_exists', '0', A[2]) + ('cases hz', 'cases hz_witness')
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *A, *EMPTY, *A, *A[:2], 'x', 'x1', *A[:2], A[2])
    body += ('exact ha',) + _call('matrix_rank_bounded_prefix_empty', '0', '0', 'p')
    body += ('exact ha', 'split')
    body += _call('prime_field_polynomial_power_coefficient_functional', *A)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'x', 'x1', A[2], *EMPTY)
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty', 'x', 'x1', A[2])
    body += ('exact hz_witness_witness',)
    body += _call('prime_field_polynomial_add_zero_right', 'p', *A[:2], 'x', 'x1', A[2])
    body += ('exact hp', 'exact ha', 'exact hz_witness_witness')
    body += _call('prime_field_polynomial_power_coefficient_functional', *A)
    return spec(
        'prime_field_polynomial_aligned_add_empty_right',
        _contract(parameters, (_prime('p', 'empty_add_prime'), _coeff('p', *A, 'empty_add_bound')),
                  _aligned_add('p', *A, *EMPTY, *A, 'empty_add_result')),
        ('beta_repeat_exists', 'prime_field_polynomial_aligned_add_from_common',
         'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_power_coefficient_functional',
         'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_zero_prefix_equivalent_empty', 'prime_field_polynomial_add_zero_right'),
        body,
        'Construct a real zero prefix at the input length and its formal equivalence to the empty polynomial, giving an actual aligned right-zero sum for every canonical input.',
    )


def _terminal_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B, *G)
    body = _intro(*parameters, 'hp', 'hb', 'hdivides') + ('cases hdivides',)
    tail = 'hdivides_right'
    for _ in range(6):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += ('cases ' + tail,)
    quotient, product = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    body += ('have hproduct_bound : ' + _coeff('p', *product, 'terminal_product_bound'),)
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *quotient, *A, *product)
    body += ('exact ' + tail + '_left',)
    body += ('have hempty_product : ' + _convolution('p', *EMPTY, *B, *EMPTY, 'terminal_empty_product'),)
    body += _call('prime_field_polynomial_convolution_empty', 'p', *EMPTY, *B, '0', '0')
    body += _call('matrix_rank_bounded_prefix_empty', '0', '0', 'p')
    body += ('exact hb', 'left', 'refl')
    # Prove the sum before introducing the nine output witnesses.
    body += ('have hsum : ' + _aligned_add('p', *product, *EMPTY, *G, 'terminal_sum'),)
    body += _call('prime_field_polynomial_aligned_add_transport',
                  'p', *product, *EMPTY, *product, *product, *EMPTY, *G)
    body += ('exact hproduct_bound',) + _call('matrix_rank_bounded_prefix_empty', '0', '0', 'p')
    body += ('exact hdivides_left',)
    body += _call('prime_field_polynomial_power_coefficient_functional', *product)
    body += _call('prime_field_polynomial_power_coefficient_functional', *EMPTY)
    body += ('exact ' + tail + '_right',)
    body += _call('prime_field_polynomial_aligned_add_empty_right', 'p', *product)
    body += ('exact hp', 'exact hproduct_bound')
    body += tuple('exists ' + value for value in (*quotient, *product, *EMPTY))
    body += ('split', 'exact ' + tail + '_left', 'split', 'exact hempty_product', 'exact hsum')
    result = 'exists ub uc U. ' + _bezout('p', *A, *B, *G, *U, *EMPTY, 'terminal_result')
    return spec(
        'prime_field_polynomial_bezout_from_right_multiple',
        _contract(parameters, (_prime('p', 'terminal_prime'), _coeff('p', *B, 'terminal_other_bound'),
                               _right_divides('p', *A, *G, 'terminal_input')), result),
        ('prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_convolution_empty',
         'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_aligned_add_transport',
         'prime_field_polynomial_power_coefficient_functional',
         'prime_field_polynomial_aligned_add_empty_right'),
        body,
        'An actual right multiple G of A supplies its real left quotient U. With the empty coefficient V, construct V*B and an actual aligned sum to give G=U*A+V*B. The second input only needs canonical coefficients.',
    )


def _make_product(label, left, right, fresh, left_bound, right_bound):
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


def _transport_row(spec: Callable[..., Any]) -> Any:
    AA, BB, GG = ('ab2', 'ac2', 'A2'), ('bb2', 'bc2', 'B2'), ('gb2', 'gc2', 'G2')
    parameters = ('p', *A, *B, *G, *U, *V, *AA, *BB, *GG)
    body = _intro(*parameters, 'hp0', 'ha2', 'hb2', 'hg2', 'haeq', 'hbeq', 'hgeq', 'hbezout')
    tail = 'hbezout'
    for _ in range(6):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += _parts(tail, 3)
    P, Q = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    for label, coefficient, graph in (
            ('hub', U, tail + '_left'), ('hvb', V, tail + '_right_left')):
        body += ('have ' + label + ' : ' + _coeff('p', *coefficient, label + '_bound'),)
        body += _parts(graph, 2) + ('exact ' + graph + '_left',)
    commands, PP, hp = _make_product('hnew_left', U, AA, ('x6', 'x7', 'x8'), 'hub', 'ha2')
    body += commands
    commands, QQ, hq = _make_product('hnew_right', V, BB, ('x9', 'x10', 'x11'), 'hvb', 'hb2')
    body += commands
    for label, left, right, product, graph in (
            ('hpp', U, AA, PP, hp), ('hqq', V, BB, QQ, hq)):
        body += ('have ' + label + ' : ' + _coeff('p', *product, label + '_bound'),)
        body += _call('prime_field_polynomial_convolution_bounded', 'p', *left, *right, *product)
        body += ('exact ' + graph,)
    body += ('have hsum : ' + _aligned_add('p', *PP, *QQ, *GG, 'transport_sum'),)
    body += _call('prime_field_polynomial_aligned_add_transport', 'p', *P, *Q, *G, *PP, *QQ, *GG)
    body += ('exact hpp', 'exact hqq', 'exact hg2')
    for coefficient, old_input, old_product, new_input, new_product, equality, old_graph, new_graph in (
            (U, A, P, AA, PP, 'haeq', tail + '_left', hp),
            (V, B, Q, BB, QQ, 'hbeq', tail + '_right_left', hq)):
        body += _call('prime_field_polynomial_equivalent_symmetric', *old_product, *new_product)
        body += _call('prime_field_polynomial_convolution_equivalent_congruent_right',
                      'p', *coefficient, *old_input, *old_product, *new_input, *new_product)
        body += ('exact hp0', 'exact ' + equality, 'exact ' + old_graph, 'exact ' + new_graph)
    body += ('exact hgeq', 'exact ' + tail + '_right_right')
    body += tuple('exists ' + value for value in (*PP, *QQ))
    body += ('split', 'exact ' + hp, 'split', 'exact ' + hq, 'exact hsum')
    return spec(
        'prime_field_polynomial_bezout_equivalent_transport',
        _contract(parameters, ('~(p=0)', _coeff('p', *AA, 'transport_a_bound'),
                               _coeff('p', *BB, 'transport_b_bound'), _coeff('p', *GG, 'transport_g_bound'),
                               _equivalent(*A, *AA, 'transport_a_equivalent'),
                               _equivalent(*B, *BB, 'transport_b_equivalent'),
                               _equivalent(*G, *GG, 'transport_g_equivalent'),
                               _bezout('p', *A, *B, *G, *U, *V, 'transport_old')),
                  _bezout('p', *AA, *BB, *GG, *U, *V, 'transport_result')),
        ('polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_aligned_add_transport',
         'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_convolution_equivalent_congruent_right'),
        body,
        'Independently recode both inputs and the result by formal coefficient equivalence, retaining the same Bezout coefficients. Construct both new proper products; output equivalences are proved, not supplied as premises. No primality is needed beyond a nonzero modulus.',
    )


def _greatest_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *D, *A, *B, *G, *U, *V)
    body = _intro(*parameters, 'hp', 'hcommon', 'hbezout') + ('cases hcommon',)
    tail = 'hbezout'
    for _ in range(6):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += _parts(tail, 3)
    P, Q = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5')
    body += _call('prime_field_polynomial_right_divides_aligned_add', 'p', *D, *P, *Q, *G)
    body += ('exact hp',)
    body += _call('prime_field_polynomial_right_divides_left_product', 'p', *D, *A, *U, *P)
    body += ('exact hp', 'exact hcommon_left', 'exact ' + tail + '_left')
    body += _call('prime_field_polynomial_right_divides_left_product', 'p', *D, *B, *V, *Q)
    body += ('exact hp', 'exact hcommon_right', 'exact ' + tail + '_right_left',
             'exact ' + tail + '_right_right')
    return spec(
        'prime_field_polynomial_bezout_common_right_divisor',
        _contract(parameters, (_prime('p', 'greatest_prime'),
                               _common_divisor('p', *D, *A, *B, 'greatest_common'),
                               _bezout('p', *A, *B, *G, *U, *V, 'greatest_bezout')),
                  _right_divides('p', *D, *G, 'greatest_result')),
        ('prime_field_polynomial_right_divides_aligned_add',
         'prime_field_polynomial_right_divides_left_product'),
        body,
        'Every actual common right divisor of A and B divides any actual Bezout representative G=U*A+V*B. This is the greatestness implication, not an assertion that an arbitrary Bezout representative divides either input.',
    )


def make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_empty_add_row(spec), _terminal_row(spec), _transport_row(spec), _greatest_row(spec))


__all__ = ['make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems']
