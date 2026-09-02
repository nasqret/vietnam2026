"""Constructive bounded recursion for normalized polynomial gcd witnesses.

Candidate bodies are ordinary HA scripts, not admission authority.  The
induction generalizes both input triples; normalization occurs at the terminal
step and the same actual output polynomial is carried through back-substitution.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _lt, _part, _parts, _prime, _public
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _le
from peano_lab.library.prime_field_polynomial_degree_candidate import _degree
from peano_lab.library.prime_field_polynomial_division_candidate import _division_execution
from peano_lab.library.prime_field_polynomial_monic_candidate import _monic
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters, premises, result):
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _right_divides(p, db, dc, D, ab, ac, L, tag):
    qb, qc, Q, pb, pc, P = tuple('pfgd_' + role + '_' + tag
                                for role in ('qb', 'qc', 'Q', 'pb', 'pc', 'P'))
    return _and(_coeff(p, ab, ac, L, tag + '_bounded'),
        'exists ' + ' '.join((qb, qc, Q, pb, pc, P)) + '. ' + _and(
            _convolution(p, qb, qc, Q, db, dc, D, pb, pc, P, tag + '_product'),
            _equivalent(pb, pc, P, ab, ac, L, tag + '_equivalent')))


def _common(p, db, dc, D, ab, ac, L, bb, bc, M, tag):
    return _and(_right_divides(p, db, dc, D, ab, ac, L, tag + '_left'),
                _right_divides(p, db, dc, D, bb, bc, M, tag + '_right'))


def _aligned_add(p, ab, ac, L, bb, bc, M, rb, rc, N, tag):
    ub, uc, vb, vc, tb, tc, K = tuple('pfga_' + role + '_' + tag
        for role in ('ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K'))
    return _and(_coeff(p, ab, ac, L, tag + '_left_bounded'),
        _coeff(p, bb, bc, M, tag + '_right_bounded'),
        _coeff(p, rb, rc, N, tag + '_result_bounded'),
        'exists ' + ' '.join((ub, uc, vb, vc, tb, tc, K)) + '. ' + _and(
            _and(_equivalent(ab, ac, L, ub, uc, K, tag + '_left'),
                 _equivalent(bb, bc, M, vb, vc, K, tag + '_right')),
            _add(p, ub, uc, vb, vc, tb, tc, K, tag + '_add'),
            _equivalent(tb, tc, K, rb, rc, N, tag + '_result')))


def _bezout(p, ab, ac, L, bb, bc, M, gb, gc, G, ub, uc, U, vb, vc, V, tag):
    pb, pc, P, qb, qc, Q = tuple('pfgb_' + role + '_' + tag
        for role in ('pb', 'pc', 'P', 'qb', 'qc', 'Q'))
    return 'exists ' + ' '.join((pb, pc, P, qb, qc, Q)) + '. ' + _and(
        _convolution(p, ub, uc, U, ab, ac, L, pb, pc, P, tag + '_left'),
        _convolution(p, vb, vc, V, bb, bc, M, qb, qc, Q, tag + '_right'),
        _aligned_add(p, pb, pc, P, qb, qc, Q, gb, gc, G, tag + '_sum'))


def _normal(p, gb, gc, G, tag):
    return f'({G})=0 \\/ (' + _monic(p, gb, gc, G, tag + '_monic') + ')'


def _right_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag):
    db, dc, D = tuple('pfgg_' + role + '_' + tag for role in ('db', 'dc', 'D'))
    greatest = 'forall ' + ' '.join((db, dc, D)) + '. (' + _common(
        p, db, dc, D, ab, ac, L, bb, bc, M, tag + '_divisor') + ') -> (' + _right_divides(
        p, db, dc, D, gb, gc, G, tag + '_greatest') + ')'
    return _and(_common(p, gb, gc, G, ab, ac, L, bb, bc, M, tag + '_common'), greatest)


def _normalized_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag):
    return _and(_normal(p, gb, gc, G, tag + '_normal'),
                _right_gcd(p, gb, gc, G, ab, ac, L, bb, bc, M, tag + '_gcd'))


def prime_field_polynomial_zero_or_monic_relation(p, gb, gc, G, *, tag, variables):
    return _public(_normal, (p, gb, gc, G), tag=tag, variables=variables)


def prime_field_polynomial_right_gcd_relation(p, gb, gc, G, ab, ac, L, bb, bc, M,
                                           *, tag, variables):
    return _public(_right_gcd, (p, gb, gc, G, ab, ac, L, bb, bc, M), tag=tag, variables=variables)


def prime_field_polynomial_normalized_gcd_relation(p, gb, gc, G, ab, ac, L, bb, bc, M,
                                                *, tag, variables):
    return _public(_normalized_gcd, (p, gb, gc, G, ab, ac, L, bb, bc, M), tag=tag, variables=variables)


def _witness(p, A, B, G, U, V, tag):
    return _and(_normal(p, *G, tag + '_normal'),
                _common(p, *G, *A, *B, tag + '_common'),
                _bezout(p, *A, *B, *G, *U, *V, tag + '_bezout'))


def _solution(p, A, B, tag):
    names = tuple('pfgs_' + role + '_' + tag
                  for role in ('gb', 'gc', 'G', 'ub', 'uc', 'U', 'vb', 'vc', 'V'))
    return 'exists ' + ' '.join(names) + '. ' + _witness(
        p, A, B, names[:3], names[3:6], names[6:], tag + '_witness')


A, B, G, U, V = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('gb', 'gc', 'G'), ('ub', 'uc', 'U'), ('vb', 'vc', 'V')
DIVISION_PARAMETERS = ('p', *A, 'bb', 'bc', 'd', 'qb', 'qc', 'q', 'rb', 'rc', 'R')


def _remainder_bounded_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*DIVISION_PARAMETERS, 'he') + _parts('he', 4)
    name = 'he_right_right_right'
    body += tuple('cases ' + name + '_witness' * i for i in range(7))
    inner = name + '_witness' * 7
    body += _parts(inner, 6)
    body += _call('prime_field_polynomial_trim_output_coefficients',
                  'p', 'x4', 'x5', 'L', 'x6', 'rb', 'rc', 'R')
    body += ('exact ' + _part(inner, 6, 5),)
    return spec('prime_field_polynomial_division_remainder_bounded',
        _contract(DIVISION_PARAMETERS,
                  (_division_execution(*DIVISION_PARAMETERS, 'gcd_remainder_execution'),),
                  _coeff('p', 'rb', 'rc', 'R', 'gcd_remainder_bounded')),
        ('prime_field_polynomial_trim_output_coefficients',), body,
        'The actual trim inside division supplies canonical remainder coefficients, including its empty branch; no primality or degree of zero is assumed.')


def _reduced(p, A, T, tag):
    d = 'pfg_degree_' + tag
    return _and(_coeff(p, *T, tag + '_bounded'),
                _equivalent(*T, *A, tag + '_equivalent'),
                _le(T[2], A[2], tag + '_length'),
                f'({T[2]})=0 \\/ (exists {d}. ' + _degree(p, *T, d, tag + '_degree') + ')')


def _reduced_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A)
    body = _intro(*parameters, 'hA')
    trim = _trim('p', *A, 't', 'tb', 'tc', 'K', 'gcd_reduced_trim')
    body += ('have ht : exists t tb tc K. ' + trim,)
    body += _call('prime_field_polynomial_trim_exists', *parameters) + ('exact hA',)
    body += tuple('cases ht' + '_witness' * i for i in range(4))
    tail = 'ht' + '_witness' * 4
    actual = ('p', *A, 'x', 'x1', 'x2', 'x3')
    T = ('x1', 'x2', 'x3')
    body += ('exists x1', 'exists x2', 'exists x3', 'split')
    body += _call('prime_field_polynomial_trim_output_coefficients', *actual) + ('exact ' + tail, 'split')
    body += _call('prime_field_polynomial_equivalent_symmetric', *A, *T)
    body += _call('prime_field_polynomial_trim_equivalent', *actual) + ('exact ' + tail, 'split')
    bounds = _and(_le('x', A[2], 'gcd_reduced_removed'), _le('x3', A[2], 'gcd_reduced_retained'))
    body += ('have hb : ' + bounds,)
    body += _call('prime_field_polynomial_trim_length_bounds', *actual)
    body += ('exact ' + tail, 'cases hb', 'exact hb_right', 'have hz : x3=0 \\/ ~(x3=0)')
    body += _call('eq_decidable', 'x3', '0') + ('cases hz', 'left', 'exact hz_left', 'right')
    body += _call('prime_field_polynomial_trim_nonempty_degree_exists', *actual)
    body += ('exact ' + tail, 'exact hz_right')
    return spec('prime_field_polynomial_reduced_representative_exists',
        _contract(parameters, (_coeff('p', *A, 'gcd_reduced_input'),),
                  'exists tb tc K. ' + _reduced('p', A, ('tb', 'tc', 'K'), 'gcd_reduced_result')),
        ('prime_field_polynomial_trim_exists', 'prime_field_polynomial_trim_output_coefficients',
         'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_trim_equivalent',
         'prime_field_polynomial_trim_length_bounds', 'eq_decidable',
         'prime_field_polynomial_trim_nonempty_degree_exists'), body,
        'Construct a formally equivalent canonical representative of no greater retained length, either empty or with an actual nonzero leading coefficient and represented degree. This trims stored leading zeros without requiring a prime modulus.')


def _terminal_row(spec: Callable[..., Any]) -> Any:
    empty = ('bb', 'bc', '0')
    parameters = ('p', *A, 'bb', 'bc')
    normal = _and(_normal('p', *G, 'gcd_terminal_normal'),
                  _right_divides('p', *A, *G, 'gcd_terminal_multiple'),
                  _right_divides('p', *G, *A, 'gcd_terminal_divisor'))
    body = _intro(*parameters, 'hp', 'hA')
    body += ('have hn : exists gb gc G. ' + normal,)
    body += _call('prime_field_polynomial_normalized_right_associate_exists', 'p', *A)
    body += ('exact hp', 'exact hA')
    body += tuple('cases hn' + '_witness' * i for i in range(3))
    tail = 'hn_witness_witness_witness'
    body += _parts(tail, 3)
    actual_G = ('x', 'x1', 'x2')
    body += ('have hG : ' + _coeff('p', *actual_G, 'gcd_terminal_bound'),)
    body += _call('prime_field_polynomial_right_divides_divisor_bounded', 'p', *actual_G, *A)
    body += ('exact ' + tail + '_right_right',)
    combination = 'exists ub uc U. ' + _bezout('p', *A, *empty, *actual_G, *U,
                                             '0', '0', '0', 'gcd_terminal_combination')
    body += ('have hb : ' + combination,)
    body += _call('prime_field_polynomial_bezout_from_right_multiple', 'p', *A, *empty, *actual_G)
    body += ('exact hp',) + _call('matrix_rank_bounded_prefix_empty', 'bb', 'bc', 'p')
    body += ('exact ' + tail + '_right_left',)
    body += tuple('cases hb' + '_witness' * i for i in range(3))
    body += tuple('exists ' + value for value in (*actual_G, 'x3', 'x4', 'x5', '0', '0', '0'))
    body += ('split', 'exact ' + tail + '_left', 'split', 'split', 'exact ' + tail + '_right_right')
    body += _call('prime_field_polynomial_right_divides_empty', 'p', *actual_G, 'bb', 'bc')
    body += ('exact hG', 'exact hb_witness_witness_witness')
    return spec('prime_field_polynomial_gcd_bezout_empty_second',
        _contract(parameters, (_prime('p', 'gcd_terminal_prime'), _coeff('p', *A, 'gcd_terminal_input')),
                  _solution('p', A, empty, 'gcd_terminal_result')),
        ('prime_field_polynomial_normalized_right_associate_exists',
         'prime_field_polynomial_right_divides_divisor_bounded',
         'prime_field_polynomial_bezout_from_right_multiple',
         'matrix_rank_bounded_prefix_empty', 'prime_field_polynomial_right_divides_empty'), body,
        'Construct an already zero-or-monic common divisor and actual Bezout coefficients for (A,empty), using genuine mutual right-associate witnesses. Empty and all-zero A, including (0,0), require no inverse or degree of zero.')


def _equivalent_second_row(spec: Callable[..., Any]) -> Any:
    BB = ('bb2', 'bc2', 'M2')
    parameters = ('p', *A, *B, *BB)
    body = _intro(*parameters, 'hp', 'hA', 'hBB', 'heq', 'hs')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hz')
    body += tuple('cases hs' + '_witness' * i for i in range(9))
    tail = 'hs' + '_witness' * 9
    body += _parts(tail, 3) + ('cases ' + tail + '_right_left',)
    actual_G, actual_U, actual_V = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5'), ('x6', 'x7', 'x8')
    body += ('have hG : ' + _coeff('p', *actual_G, 'gcd_transport_G'),)
    body += _call('prime_field_polynomial_right_divides_divisor_bounded', 'p', *actual_G, *A)
    body += ('exact ' + tail + '_right_left_left',)
    body += ('have hb : ' + _bezout('p', *A, *BB, *actual_G, *actual_U, *actual_V, 'gcd_transport_bezout'),)
    body += _call('prime_field_polynomial_bezout_equivalent_transport',
                  'p', *A, *B, *actual_G, *actual_U, *actual_V, *A, *BB, *actual_G)
    body += ('exact hp0', 'exact hA', 'exact hBB', 'exact hG')
    body += _call('prime_field_polynomial_power_coefficient_functional', *A)
    body += ('exact heq',) + _call('prime_field_polynomial_power_coefficient_functional', *actual_G)
    body += ('exact ' + tail + '_right_right',)
    body += tuple('exists ' + value for value in (*actual_G, *actual_U, *actual_V))
    body += ('split', 'exact ' + tail + '_left', 'split', 'split', 'exact ' + tail + '_right_left_left')
    body += _call('prime_field_polynomial_right_divides_equivalent_target', 'p', *actual_G, *B, *BB)
    body += ('exact hBB', 'exact ' + tail + '_right_left_right', 'exact heq', 'exact hb')
    return spec('prime_field_polynomial_gcd_bezout_equivalent_second',
        _contract(parameters, (_prime('p', 'gcd_transport_prime'),
                  _coeff('p', *A, 'gcd_transport_A'), _coeff('p', *BB, 'gcd_transport_B'),
                  _equivalent(*B, *BB, 'gcd_transport_equivalent'),
                  _solution('p', A, B, 'gcd_transport_source')),
                  _solution('p', A, BB, 'gcd_transport_result')),
        ('prime_nonzero', 'prime_field_polynomial_right_divides_divisor_bounded',
         'prime_field_polynomial_bezout_equivalent_transport',
         'prime_field_polynomial_power_coefficient_functional',
         'prime_field_polynomial_right_divides_equivalent_target'), body,
        'Replace the second input by any formally equivalent canonical representation while keeping the same zero-or-monic common divisor and the same Bezout coefficients; both new products remain witnessed.')


def _updated_bezout(p, A, B, Q, G, U, V, tag):
    wb, wc, W, tb, tc, T = tuple('pfg_update_' + role + '_' + tag
                               for role in ('wb', 'wc', 'W', 'tb', 'tc', 'T'))
    return 'exists ' + ' '.join((wb, wc, W, tb, tc, T)) + '. ' + _and(
        _convolution(p, *V, *Q, wb, wc, W, tag + '_product'),
        _aligned_add(p, wb, wc, W, tb, tc, T, *U, tag + '_difference'),
        _bezout(p, *A, *B, *G, *V, tb, tc, T, tag + '_combination'))


def _backward_row(spec: Callable[..., Any]) -> Any:
    divisor, quotient, remainder = ('bb', 'bc', 'S d'), ('qb', 'qc', 'q'), ('rb', 'rc', 'R')
    execution = _division_execution(*DIVISION_PARAMETERS, 'gcd_backward_execution')
    body = _intro(*DIVISION_PARAMETERS)
    # Specialize the known input before introducing the large recursive
    # witness. The local universal lemma is proved, not added as a premise.
    body += ('have hupdate : ' + _contract((*G, *U, *V), (
        _prime('p', 'gcd_backward_local_prime'), execution,
        _bezout('p', *divisor, *remainder, *G, *U, *V, 'gcd_backward_local_old')),
        _updated_bezout('p', A, divisor, quotient, G, U, V, 'gcd_backward_local_result')),)
    body += _call('prime_field_polynomial_division_execution_bezout_backward', *DIVISION_PARAMETERS)[:-1]
    body += ('exact prime_field_polynomial_division_execution_bezout_backward',)
    body += _intro('hp', 'he', 'hs')
    body += tuple('cases hs' + '_witness' * i for i in range(9))
    tail = 'hs' + '_witness' * 9
    body += _parts(tail, 3)
    actual_G, actual_U, actual_V = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5'), ('x6', 'x7', 'x8')
    old_common = _common('p', *actual_G, *divisor, *remainder, 'gcd_backward_old_common')
    new_common = _common('p', *actual_G, *A, *divisor, 'gcd_backward_new_common')
    body += ('have hc : ' + new_common,
             'have hm : ' + _and('(' + new_common + ') -> (' + old_common + ')',
                                 '(' + old_common + ') -> (' + new_common + ')'))
    body += _call('prime_field_polynomial_division_execution_common_right_divisors',
                  *DIVISION_PARAMETERS, *actual_G)
    body += ('exact hp', 'exact he', 'cases hm', 'apply hm_right', 'exact ' + tail + '_right_left')
    body += ('have hb : ' + _updated_bezout('p', A, divisor, quotient,
                                           actual_G, actual_U, actual_V, 'gcd_backward_update'),)
    body += _call('hupdate', *actual_G, *actual_U, *actual_V)
    body += ('exact hp', 'exact he', 'exact ' + tail + '_right_right')
    body += tuple('cases hb' + '_witness' * i for i in range(6))
    updated = 'hb' + '_witness' * 6
    body += _parts(updated, 3)
    body += tuple('exists ' + value for value in (*actual_G, *actual_V, 'x12', 'x13', 'x14'))
    body += ('split', 'exact ' + tail + '_left', 'split', 'exact hc', 'exact ' + updated + '_right_right')
    return spec('prime_field_polynomial_gcd_bezout_division_backward',
        _contract(DIVISION_PARAMETERS, (_prime('p', 'gcd_backward_prime'), execution,
                  _solution('p', divisor, remainder, 'gcd_backward_small')),
                  _solution('p', A, divisor, 'gcd_backward_result')),
        ('prime_field_polynomial_division_execution_bezout_backward',
         'prime_field_polynomial_division_execution_common_right_divisors'), body,
        'Carry an already normalized common divisor through an actual Euclidean step. Construct the new coefficients V and U-V*Q from actual products and aligned subtraction, preserving the same G.')


def _bounded(n, tag):
    return _contract(('p', *A, *B), (_prime('p', tag + '_prime'),
        _coeff('p', *A, tag + '_A'), _coeff('p', *B, tag + '_B'),
        _le(B[2], n, tag + '_bound')), _solution('p', A, B, tag + '_solution'))


def _bounded_row(spec: Callable[..., Any]) -> Any:
    body = ('intro n', 'induction n')
    body += _intro('p', *A, *B, 'hp', 'hA', 'hB', 'hbound')
    body += ('have hz : M=0',) + _call('le_zero', 'M') + ('exact hbound',)
    body += _rewrite_all('hz', _solution('p', A, B, 'gcd_induction_base'), 'M')
    body += _call('prime_field_polynomial_gcd_bezout_empty_second', 'p', *A, 'bb', 'bc')
    body += ('exact hp', 'exact hA')
    # Both triples (and the prime) remain quantified in IH. Specializing an
    # induction hypothesis that fixed A would not justify the recursive T,R.
    body += _intro('p', *A, *B, 'hp', 'hA', 'hB', 'hbound')
    body += ('have ht : exists tb tc K. ' + _reduced('p', B, ('tb', 'tc', 'K'), 'gcd_induction_trim'),)
    body += _call('prime_field_polynomial_reduced_representative_exists', 'p', *B)
    body += ('exact hB', 'cases ht', 'cases ht_witness', 'cases ht_witness_witness')
    trimmed, tail = ('x', 'x1', 'x2'), 'ht_witness_witness_witness'
    body += _parts(tail, 4)
    body += _call('prime_field_polynomial_gcd_bezout_equivalent_second', 'p', *A, *trimmed, *B)
    body += ('exact hp', 'exact hA', 'exact hB', 'exact ' + _part(tail, 4, 1),
             'cases ' + _part(tail, 4, 3))
    zero, nonzero = tail + '_right_right_right_left', tail + '_right_right_right_right'
    body += _rewrite_all(zero, _solution('p', A, trimmed, 'gcd_induction_empty'), 'x2')
    body += _call('prime_field_polynomial_gcd_bezout_empty_second', 'p', *A, 'x', 'x1')
    body += ('exact hp', 'exact hA', 'cases ' + nonzero)
    degree = nonzero + '_witness'
    body += ('have hlength : x2=S x3', 'cases ' + degree, 'exact ' + degree + '_left')
    body += ('have hdBound : ' + _le('x3', 'n', 'gcd_induction_degree_bound'),)
    body += _call('le_of_succ_le_succ', 'x3', 'n')
    body += ('have hlengthBound : ' + _le('x2', 'S n', 'gcd_induction_length_bound'),)
    body += _call('le_trans', 'x2', 'M', 'S n')
    body += ('exact ' + _part(tail, 4, 2), 'exact hbound',
             'rewrite hlength at hlengthBound', 'exact hlengthBound')
    body += _rewrite_all('hlength', _solution('p', A, trimmed, 'gcd_induction_nonempty'), 'x2')
    actual = ('p', *A, 'x', 'x1', 'x3', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
    body += ('have he : exists qb qc q rb rc R. ' + _division_execution(*actual, 'gcd_induction_division'),)
    body += _call('prime_field_polynomial_division_execution_exists', 'p', *A, 'x', 'x1', 'x3')
    body += ('exact hp', 'exact hA')
    body += _rewrite_all('hlength', _degree('p', *trimmed, 'x3', 'gcd_induction_degree'), 'x2', at=degree)
    body += ('exact ' + degree,)
    body += tuple('cases he' + '_witness' * i for i in range(6))
    execution = 'he' + '_witness' * 6
    actual = ('p', *A, 'x', 'x1', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9')
    body += _call('prime_field_polynomial_gcd_bezout_division_backward', *actual)
    body += ('exact hp', 'exact ' + execution)
    body += _call('IH', 'p', 'x', 'x1', 'S x3', 'x7', 'x8', 'x9')
    body += ('exact hp',)
    body += _rewrite_all('hlength', _coeff('p', *trimmed, 'gcd_induction_T'), 'x2', at=tail + '_left')
    body += ('exact ' + tail + '_left',)
    body += _call('prime_field_polynomial_division_remainder_bounded', *actual)
    body += ('exact ' + execution,)
    body += _call('le_trans', 'x9', 'x3', 'n')
    body += ('have hr : ' + _and(_le('x9', 'x3', 'gcd_induction_remainder_bound'),
                                _lt('x9', 'S x3', 'gcd_induction_remainder_strict')),)
    body += _call('prime_field_polynomial_division_remainder_length_descent', *actual)
    body += ('exact hp', 'exact ' + execution, 'cases hr', 'exact hr_left', 'exact hdBound')
    return spec('prime_field_polynomial_gcd_bezout_exists_up_to',
        'forall n. ' + _bounded('n', 'gcd_induction'),
        ('le_zero', 'prime_field_polynomial_gcd_bezout_empty_second',
         'prime_field_polynomial_reduced_representative_exists',
         'prime_field_polynomial_gcd_bezout_equivalent_second',
         'le_of_succ_le_succ', 'le_trans', 'prime_field_polynomial_division_execution_exists',
         'prime_field_polynomial_gcd_bezout_division_backward',
         'prime_field_polynomial_division_remainder_bounded',
         'prime_field_polynomial_division_remainder_length_descent'), body,
        'Ordinary natural induction constructs actual normalized gcd and Bezout witnesses for every pair with second retained length at most n. Both input triples are generalized, a stored zero divisor is trimmed before division, and every genuine recursive call has a proved smaller bound.')


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B)
    body = _intro(*parameters, 'hp', 'hA', 'hB')
    body += _call('prime_field_polynomial_gcd_bezout_exists_up_to', 'M', *parameters)
    body += ('exact hp', 'exact hA', 'exact hB') + _call('le_refl', 'M')
    return spec('prime_field_polynomial_gcd_bezout_exists',
        _contract(parameters, (_prime('p', 'gcd_exists_prime'),
                  _coeff('p', *A, 'gcd_exists_A'), _coeff('p', *B, 'gcd_exists_B')),
                  _solution('p', A, B, 'gcd_exists_result')),
        ('prime_field_polynomial_gcd_bezout_exists_up_to', 'le_refl'), body,
        'Take the actual second representation length as induction bound. No supplied quotient, gcd, degree, termination certificate, or Bezout coefficients are premises.')


def _greatest_row(spec: Callable[..., Any]) -> Any:
    D = ('db', 'dc', 'D')
    parameters = ('p', *G, *A, *B, *U, *V)
    body = _intro(*parameters, 'hp', 'hc', 'hb')
    body += ('split', 'exact hc') + _intro(*D, 'hd')
    body += _call('prime_field_polynomial_bezout_common_right_divisor', 'p', *D, *A, *B, *G, *U, *V)
    body += ('exact hp', 'exact hd', 'exact hb')
    return spec('prime_field_polynomial_bezout_is_right_gcd',
        _contract(parameters, (_prime('p', 'gcd_greatest_prime'),
                  _common('p', *G, *A, *B, 'gcd_greatest_common'),
                  _bezout('p', *A, *B, *G, *U, *V, 'gcd_greatest_bezout')),
                  _right_gcd('p', *G, *A, *B, 'gcd_greatest_result')),
        ('prime_field_polynomial_bezout_common_right_divisor',), body,
        'A common right divisor with an actual Bezout representation satisfies the full universally quantified greatestness property, including a zero gcd; no normalization assumption is needed.')


def _normalized_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B)
    result = 'exists ' + ' '.join((*G, *U, *V)) + '. ' + _and(
        _normalized_gcd('p', *G, *A, *B, 'normalized_exists_gcd'),
        _bezout('p', *A, *B, *G, *U, *V, 'normalized_exists_bezout'))
    body = _intro(*parameters, 'hp', 'hA', 'hB')
    body += ('have hs : ' + _solution('p', A, B, 'normalized_exists_solution'),)
    body += _call('prime_field_polynomial_gcd_bezout_exists', *parameters)
    body += ('exact hp', 'exact hA', 'exact hB')
    body += tuple('cases hs' + '_witness' * i for i in range(9))
    tail = 'hs' + '_witness' * 9
    body += _parts(tail, 3)
    actual_G, actual_U, actual_V = ('x', 'x1', 'x2'), ('x3', 'x4', 'x5'), ('x6', 'x7', 'x8')
    body += tuple('exists ' + value for value in (*actual_G, *actual_U, *actual_V))
    body += ('split', 'split', 'exact ' + tail + '_left')
    body += _call('prime_field_polynomial_bezout_is_right_gcd', 'p', *actual_G, *A, *B, *actual_U, *actual_V)
    body += ('exact hp', 'exact ' + tail + '_right_left', 'exact ' + tail + '_right_right',
             'exact ' + tail + '_right_right')
    return spec('prime_field_polynomial_normalized_gcd_bezout_exists',
        _contract(parameters, (_prime('p', 'normalized_exists_prime'),
                  _coeff('p', *A, 'normalized_exists_A'), _coeff('p', *B, 'normalized_exists_B')),
                  result),
        ('prime_field_polynomial_gcd_bezout_exists', 'prime_field_polynomial_bezout_is_right_gcd'), body,
        'Every pair of canonical polynomials over a prime field has an actual zero-or-monic greatest common right divisor and actual Bezout coefficients. The normalized-gcd definition and the existing Bezout graph occur literally in the conclusion.')


def make_prime_field_polynomial_gcd_existence_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_remainder_bounded_row(spec), _reduced_exists_row(spec),
            _terminal_row(spec), _equivalent_second_row(spec), _backward_row(spec),
            _bounded_row(spec), _exists_row(spec), _greatest_row(spec), _normalized_exists_row(spec))


__all__ = ['make_prime_field_polynomial_gcd_existence_candidate_theorems',
           'prime_field_polynomial_zero_or_monic_relation',
           'prime_field_polynomial_right_gcd_relation',
           'prime_field_polynomial_normalized_gcd_relation']
