"""Actual addition and subtraction for independently sized polynomials.

The common-representative clause is a literal grouped subtree, shared with
the preceding alignment layer.  Addition retains canonical original inputs
and output and constructs a real equal-length coefficient operation.
Subtraction is the literal argument permutation B+R=A, not a new oracle.
This source registers no kernel rule, edition, or published definition.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff, _equal
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract


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


def prime_field_polynomial_aligned_add_relation(
        p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
        rb: str, rc: str, N: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_aligned_add, (p, ab, ac, L, bb, bc, M, rb, rc, N),
                   tag=tag, variables=variables)


def prime_field_polynomial_aligned_subtract_relation(
        p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
        rb: str, rc: str, N: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_aligned_subtract, (p, ab, ac, L, bb, bc, M, rb, rc, N),
                   tag=tag, variables=variables)


A, B, R = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')
PARAMETERS = ('p', *A, *B, *R)
WITNESSES = ('ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K')


def _unpack(hypothesis: str) -> tuple[tuple[str, ...], str]:
    commands = _parts(hypothesis, 4)
    tail = hypothesis + '_right_right_right'
    for _ in range(7):
        commands += ('cases ' + tail,)
        tail += '_witness'
    commands += _parts(tail, 3)
    return commands, tail


def _from_common_row(spec: Callable[..., Any]) -> Any:
    parameters = (*PARAMETERS, *WITNESSES)
    premises = (*(_coeff('p', *poly, 'from_common_' + str(index))
                  for index, poly in enumerate((A, B, R))),
                _common_representatives(*A, *B, 'ub', 'uc', 'vb', 'vc', 'K', 'from_common_reps'),
                _add('p', 'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K', 'from_common_sum'),
                _equivalent('tb', 'tc', 'K', *R, 'from_common_output'))
    body = _intro(*parameters, 'ha', 'hb', 'hr', 'hc', 'hs', 'he')
    body += ('split', 'exact ha', 'split', 'exact hb', 'split', 'exact hr')
    body += tuple('exists ' + value for value in WITNESSES)
    body += ('split', 'exact hc', 'split', 'exact hs', 'exact he')
    return spec(
        'prime_field_polynomial_aligned_add_from_common',
        _contract(parameters, premises, _aligned_add(*PARAMETERS, 'from_common_result')),
        (), body,
        'Package actual common representatives, an actual coefficient sum, and formal output equivalence while retaining all three original canonical coefficient guards.',
    )


def _bounded_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*PARAMETERS, 'h') + _parts('h', 4)
    body += ('split', 'exact h_left', 'split', 'exact h_right_left', 'exact h_right_right_left')
    return spec(
        'prime_field_polynomial_aligned_add_bounded',
        _contract(PARAMETERS, (_aligned_add(*PARAMETERS, 'aligned_bound_input'),),
                  _and(*(_coeff('p', *poly, 'aligned_bound_' + str(index))
                         for index, poly in enumerate((A, B, R))))),
        (), body,
        'Aligned addition includes canonical coefficients for the actual originals and output, not merely for equivalent witnesses.',
    )


def _fixed_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'rb', 'rc', 'K')
    body = _intro(*parameters, 'h')
    body += ('have hb : ' + _and(*(_coeff('p', b, c, 'K', 'fixed_bound_' + b)
                                  for b, c in (('ab', 'ac'), ('bb', 'bc'), ('rb', 'rc')))),)
    body += _call('prime_field_polynomial_add_bounded', *parameters) + ('exact h',) + _parts('hb', 3)
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'K',
                  'ab', 'ac', 'bb', 'bc', 'rb', 'rc', 'K')
    body += ('exact hb_left', 'exact hb_right_left', 'exact hb_right_right')
    body += _call('prime_field_polynomial_common_representatives_same_length', 'ab', 'ac', 'bb', 'bc', 'K')
    body += ('exact h',) + _call('prime_field_polynomial_power_coefficient_functional', 'rb', 'rc', 'K')
    return spec(
        'prime_field_polynomial_aligned_add_from_fixed',
        _contract(parameters, (_add(*parameters, 'fixed_input'),),
                  _aligned_add('p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'K', 'fixed_result')),
        ('prime_field_polynomial_add_bounded', 'prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_common_representatives_same_length',
         'prime_field_polynomial_power_coefficient_functional'), body,
        'Every genuine fixed-length addition supplies its own actual common representatives and is an aligned addition, without an extra prime hypothesis.',
    )


def _transport_row(spec: Callable[..., Any]) -> Any:
    D, E, F = ('db', 'dc', 'J'), ('eb', 'ec', 'H'), ('fb', 'fc', 'I')
    parameters = (*PARAMETERS, *D, *E, *F)
    body = _intro(*parameters, 'hd', 'he', 'hf', 'hda', 'heb', 'hrf', 'h')
    unpack, tail = _unpack('h')
    body += unpack
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *D, *E, *F, 'x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6')
    body += ('exact hd', 'exact he', 'exact hf')
    body += _call('prime_field_polynomial_common_representatives_transport',
                  *A, *B, 'x', 'x1', 'x2', 'x3', 'x6', *D, *E)
    body += ('exact hda', 'exact heb', 'exact ' + tail + '_left', 'exact ' + tail + '_right_left')
    body += _call('prime_field_polynomial_equivalent_transitive', 'x4', 'x5', 'x6', *R, *F)
    body += ('exact ' + tail + '_right_right', 'exact hrf')
    return spec(
        'prime_field_polynomial_aligned_add_transport',
        _contract(parameters, (*(_coeff('p', *poly, 'aligned_transport_' + str(index))
                                 for index, poly in enumerate((D, E, F))),
                               _equivalent(*D, *A, 'aligned_transport_left'),
                               _equivalent(*E, *B, 'aligned_transport_right'),
                               _equivalent(*R, *F, 'aligned_transport_output'),
                               _aligned_add(*PARAMETERS, 'aligned_transport_old')),
                  _aligned_add('p', *D, *E, *F, 'aligned_transport_new')),
        ('prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_common_representatives_transport',
         'prime_field_polynomial_equivalent_transitive'), body,
        'Independent formal recoding of all three canonical originals preserves a real aligned sum; canonicality is never inferred solely from equivalence.',
    )


def _commutative_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*PARAMETERS, 'h')
    unpack, tail = _unpack('h')
    body += unpack
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *B, *A, *R, 'x2', 'x3', 'x', 'x1', 'x4', 'x5', 'x6')
    body += ('exact h_right_left', 'exact h_left', 'exact h_right_right_left')
    body += _call('prime_field_polynomial_common_representatives_symmetric',
                  *A, *B, 'x', 'x1', 'x2', 'x3', 'x6')
    body += ('exact ' + tail + '_left',)
    body += _call('prime_field_polynomial_add_commutative',
                  'p', 'x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6')
    body += ('exact ' + tail + '_right_left', 'exact ' + tail + '_right_right')
    return spec(
        'prime_field_polynomial_aligned_add_commutative',
        _contract(PARAMETERS, (_aligned_add(*PARAMETERS, 'aligned_comm_old'),),
                  _aligned_add('p', *B, *A, *R, 'aligned_comm_new')),
        ('prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_common_representatives_symmetric',
         'prime_field_polynomial_add_commutative'), body,
        'Actual aligned addition commutes by swapping its real common representatives and the checked coefficient addition.',
    )


def _functional_row(spec: Callable[..., Any]) -> Any:
    S = ('sb', 'sc', 'J')
    parameters = (*PARAMETERS, *S)
    body = _intro(*parameters, 'hp', 'hr', 'hs')
    first, hr = _unpack('hr')
    second, hs = _unpack('hs')
    body += first + second
    body += ('have hc : ' + _and(
        _equivalent('x', 'x1', 'x6', 'x7', 'x8', 'x13', 'aligned_function_left'),
        _equivalent('x2', 'x3', 'x6', 'x9', 'x10', 'x13', 'aligned_function_right')),)
    body += _call('prime_field_polynomial_common_representatives_functional',
                  *A, *B, 'x', 'x1', 'x2', 'x3', 'x6', 'x7', 'x8', 'x9', 'x10', 'x13')
    body += ('exact ' + hr + '_left', 'exact ' + hs + '_left', 'cases hc')
    body += ('have hm : ' + _equivalent('x4', 'x5', 'x6', 'x11', 'x12', 'x13', 'aligned_function_sums'),)
    body += _call('prime_field_polynomial_add_equivalent_congruent',
                  'p', 'x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6',
                  'x7', 'x8', 'x9', 'x10', 'x11', 'x12', 'x13')
    body += ('exact hp', 'exact hc_left', 'exact hc_right',
             'exact ' + hr + '_right_left', 'exact ' + hs + '_right_left')
    body += ('have hreverse : ' + _equivalent(*R, 'x4', 'x5', 'x6', 'aligned_function_reverse'),)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'x4', 'x5', 'x6', *R)
    body += ('exact ' + hr + '_right_right',)
    body += ('have hmiddle : ' + _equivalent(*R, 'x11', 'x12', 'x13', 'aligned_function_middle'),)
    body += _call('prime_field_polynomial_equivalent_transitive', *R, 'x4', 'x5', 'x6', 'x11', 'x12', 'x13')
    body += ('exact hreverse', 'exact hm')
    body += _call('prime_field_polynomial_equivalent_transitive', *R, 'x11', 'x12', 'x13', *S)
    body += ('exact hmiddle', 'exact ' + hs + '_right_right')
    return spec(
        'prime_field_polynomial_aligned_add_functional',
        _contract(parameters, (_prime('p', 'aligned_function_prime'),
                               _aligned_add(*PARAMETERS, 'aligned_function_first'),
                               _aligned_add('p', *A, *B, *S, 'aligned_function_second')),
                  _equivalent(*R, *S, 'aligned_function_result')),
        ('prime_field_polynomial_common_representatives_functional',
         'prime_field_polynomial_add_equivalent_congruent',
         'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_equivalent_transitive'), body,
        'Two actual aligned sums represent the same formal polynomial even when their witnesses, original output lengths, and beta codes differ.',
    )


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B)
    length = 'L+M'
    common = _and(_coeff('p', 'ub', 'uc', length, 'aligned_exists_left_bound'),
                  _coeff('p', 'vb', 'vc', length, 'aligned_exists_right_bound'),
                  _common_representatives(*A, *B, 'ub', 'uc', 'vb', 'vc', length,
                                          'aligned_exists_common'))
    body = _intro(*parameters, 'hp', 'ha', 'hb')
    body += ('have hc : exists ub uc vb vc. ' + common,)
    body += _call('prime_field_polynomial_common_representatives_exists', *parameters)
    body += ('exact hp', 'exact ha', 'exact hb', 'cases hc', 'cases hc_witness',
             'cases hc_witness_witness', 'cases hc_witness_witness_witness')
    hc = 'hc_witness_witness_witness_witness'
    body += _parts(hc, 3)
    body += ('have hs : exists rb rc. ' + _add('p', 'x', 'x1', 'x2', 'x3', 'rb', 'rc', length,
                                              'aligned_exists_sum'),)
    body += _call('prime_field_polynomial_add_exists', 'p', 'x', 'x1', 'x2', 'x3', length)
    body += ('intro hz',) + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz',
             'exact ' + hc + '_left', 'exact ' + hc + '_right_left', 'cases hs', 'cases hs_witness')
    body += ('have hsbound : ' + _and(
        _coeff('p', 'x', 'x1', length, 'aligned_exists_sum_left'),
        _coeff('p', 'x2', 'x3', length, 'aligned_exists_sum_right'),
        _coeff('p', 'x4', 'x5', length, 'aligned_exists_sum_output')),)
    body += _call('prime_field_polynomial_add_bounded', 'p', 'x', 'x1', 'x2', 'x3', 'x4', 'x5', length)
    body += ('exact hs_witness_witness',) + _parts('hsbound', 3)
    body += ('exists x4', 'exists x5')
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *A, *B, 'x4', 'x5', length, 'x', 'x1', 'x2', 'x3', 'x4', 'x5', length)
    body += ('exact ha', 'exact hb', 'exact hsbound_right_right', 'exact ' + hc + '_right_right',
             'exact hs_witness_witness')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'x4', 'x5', length)
    return spec(
        'prime_field_polynomial_aligned_add_exists',
        _contract(parameters, (_prime('p', 'aligned_exists_prime'),
                               _coeff('p', *A, 'aligned_exists_A'), _coeff('p', *B, 'aligned_exists_B')),
                  'exists rb rc. ' + _aligned_add('p', *A, *B, 'rb', 'rc', length, 'aligned_exists_output')),
        ('prime_field_polynomial_common_representatives_exists', 'prime_field_polynomial_add_exists',
         'prime_nonzero', 'prime_field_polynomial_add_bounded',
         'prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_power_coefficient_functional'), body,
        'Construct a genuine canonical aligned sum at the explicit length L+M from any two canonical inputs, rather than assuming operation witnesses.',
    )


def _realization_row(spec: Callable[..., Any]) -> Any:
    parameters = (*PARAMETERS, *WITNESSES)
    U, V, T = ('ub', 'uc', 'K'), ('vb', 'vc', 'K'), ('tb', 'tc', 'K')
    body = _intro(*parameters, 'hp', 'h', 'hu', 'hv', 'ht', 'hc', 'hr') + ('cases hc',)
    body += ('have hz : exists zb zc. ' + _add('p', 'ub', 'uc', 'vb', 'vc', 'zb', 'zc', 'K',
                                              'realize_constructed_sum'),)
    body += _call('prime_field_polynomial_add_exists', 'p', 'ub', 'uc', 'vb', 'vc', 'K')
    body += ('intro hpzero',) + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hpzero', 'exact hu', 'exact hv', 'cases hz', 'cases hz_witness')
    body += ('have hzgraph : ' + _aligned_add('p', *U, *V, 'x', 'x1', 'K', 'realize_constructed_graph'),)
    body += _call('prime_field_polynomial_aligned_add_from_fixed',
                  'p', 'ub', 'uc', 'vb', 'vc', 'x', 'x1', 'K') + ('exact hz_witness_witness',)
    body += ('have htgraph : ' + _aligned_add('p', *U, *V, *T, 'realize_target_graph'),)
    body += _call('prime_field_polynomial_aligned_add_transport', *PARAMETERS, *U, *V, *T)
    body += ('exact hu', 'exact hv', 'exact ht')
    body += _call('prime_field_polynomial_equivalent_symmetric', *A, *U) + ('exact hc_left',)
    body += _call('prime_field_polynomial_equivalent_symmetric', *B, *V) + ('exact hc_right', 'exact hr', 'exact h')
    body += ('have he : ' + _equivalent('x', 'x1', 'K', *T, 'realize_output_equivalent'),)
    body += _call('prime_field_polynomial_aligned_add_functional',
                  'p', *U, *V, 'x', 'x1', 'K', *T)
    body += ('exact hp', 'exact hzgraph', 'exact htgraph')
    body += _call('prime_field_polynomial_add_transport',
                  'p', 'ub', 'uc', 'vb', 'vc', 'x', 'x1',
                  'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K')
    body += _intro('i', 'a', 'hi', 'ha') + ('exact ha',)
    body += _intro('i', 'a', 'hi', 'ha') + ('exact ha',)
    body += _call('prime_field_polynomial_equivalent_implies_equal_same_length', 'x', 'x1', 'tb', 'tc', 'K')
    body += ('exact he', 'exact hz_witness_witness')
    return spec(
        'prime_field_polynomial_aligned_add_realize',
        _contract(parameters, (_prime('p', 'realize_prime'), _aligned_add(*PARAMETERS, 'realize_original'),
                               *(_coeff('p', *poly, 'realize_bound_' + str(index))
                                 for index, poly in enumerate((U, V, T))),
                               _common_representatives(*A, *B, 'ub', 'uc', 'vb', 'vc', 'K', 'realize_common'),
                               _equivalent(*R, *T, 'realize_output')),
                  _add('p', 'ub', 'uc', 'vb', 'vc', 'tb', 'tc', 'K', 'realize_actual_operation')),
        ('prime_field_polynomial_add_exists', 'prime_nonzero',
         'prime_field_polynomial_aligned_add_from_fixed', 'prime_field_polynomial_aligned_add_transport',
         'prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_aligned_add_functional',
         'prime_field_polynomial_add_transport', 'prime_field_polynomial_equivalent_implies_equal_same_length'),
        body,
        'Realize the addition on any supplied canonical equal-length representatives: construct a sum, prove formal output uniqueness, then transport the actual operation by decoded coefficient equality.',
    )


def _subtract_fixed_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'bb', 'bc', 'rb', 'rc', 'K')
    body = _intro(*parameters, 'h')
    body += _call('prime_field_polynomial_aligned_add_from_fixed',
                  'p', 'bb', 'bc', 'rb', 'rc', 'ab', 'ac', 'K')
    body += _call('prime_field_polynomial_subtract_recover_add', *parameters) + ('exact h',)
    return spec(
        'prime_field_polynomial_aligned_subtract_from_fixed',
        _contract(parameters, (_subtract(*parameters, 'sub_fixed_input'),),
                  _aligned_subtract('p', 'ab', 'ac', 'K', 'bb', 'bc', 'K', 'rb', 'rc', 'K', 'sub_fixed_result')),
        ('prime_field_polynomial_aligned_add_from_fixed', 'prime_field_polynomial_subtract_recover_add'), body,
        'A genuine fixed-length subtraction is an aligned subtraction because its actual coefficient graph supplies B+R=A.',
    )


def make_prime_field_polynomial_aligned_add_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_from_common_row(spec), _bounded_row(spec), _fixed_row(spec),
            _transport_row(spec), _commutative_row(spec), _functional_row(spec),
            _exists_row(spec), _realization_row(spec), _subtract_fixed_row(spec))


__all__ = ['make_prime_field_polynomial_aligned_add_candidate_theorems',
           'prime_field_polynomial_aligned_add_relation',
           'prime_field_polynomial_aligned_subtract_relation']
