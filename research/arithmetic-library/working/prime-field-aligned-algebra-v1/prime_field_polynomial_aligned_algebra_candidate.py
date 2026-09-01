"""Length-independent canonical polynomial addition and subtraction laws.

The literal aligned-operation expansions are the preceding layer's reviewed
definitions, not new identities.  Every comparison first constructs actual
bounded representatives at a stated common length and realizes real table
operations there.  No coefficient law or desired output equality is assumed.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _parts, _prime,
)
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff, _equal
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _le
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


A, B, R = ('ab', 'ac', 'L'), ('bb', 'bc', 'M'), ('rb', 'rc', 'N')


def _subtract_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, *B)
    length = 'L+M'
    common = _and(_coeff('p', 'ub', 'uc', length, 'sub_exists_left_bound'),
                  _coeff('p', 'vb', 'vc', length, 'sub_exists_right_bound'),
                  _common_representatives(*A, *B, 'ub', 'uc', 'vb', 'vc', length, 'sub_exists_common'))
    body = _intro(*parameters, 'hp', 'ha', 'hb') + ('have hc : exists ub uc vb vc. ' + common,)
    body += _call('prime_field_polynomial_common_representatives_exists', *parameters)
    body += ('exact hp', 'exact ha', 'exact hb', 'cases hc', 'cases hc_witness',
             'cases hc_witness_witness', 'cases hc_witness_witness_witness')
    hc = 'hc_witness_witness_witness_witness'
    body += _parts(hc, 3) + ('cases ' + hc + '_right_right',)
    body += ('have hd : exists rb rc. ' + _subtract('p', 'x', 'x1', 'x2', 'x3',
                                                   'rb', 'rc', length, 'sub_exists_difference'),)
    body += _call('prime_field_polynomial_subtract_exists', 'p', 'x', 'x1', 'x2', 'x3', length)
    body += ('exact hp', 'exact ' + hc + '_left', 'exact ' + hc + '_right_left',
             'cases hd', 'cases hd_witness')
    body += ('have hs : ' + _add('p', 'x2', 'x3', 'x4', 'x5', 'x', 'x1', length, 'sub_exists_recover'),)
    body += _call('prime_field_polynomial_subtract_recover_add', 'p', 'x', 'x1', 'x2', 'x3', 'x4', 'x5', length)
    body += ('exact hd_witness_witness',)
    body += ('have hbound : ' + _and(
        _coeff('p', 'x2', 'x3', length, 'sub_exists_sum_left'),
        _coeff('p', 'x4', 'x5', length, 'sub_exists_sum_right'),
        _coeff('p', 'x', 'x1', length, 'sub_exists_sum_result')),)
    body += _call('prime_field_polynomial_add_bounded', 'p', 'x2', 'x3', 'x4', 'x5', 'x', 'x1', length)
    body += ('exact hs',) + _parts('hbound', 3) + ('exists x4', 'exists x5')
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *B, 'x4', 'x5', length, *A, 'x2', 'x3', 'x4', 'x5', 'x', 'x1', length)
    body += ('exact hb', 'exact hbound_right_left', 'exact ha', 'split',
             'exact ' + hc + '_right_right_right')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'x4', 'x5', length)
    body += ('exact hs',)
    body += _call('prime_field_polynomial_equivalent_symmetric', *A, 'x', 'x1', length)
    body += ('exact ' + hc + '_right_right_left',)
    return spec(
        'prime_field_polynomial_aligned_subtract_exists',
        _contract(parameters, (_prime('p', 'sub_exists_prime'),
                               _coeff('p', *A, 'sub_exists_A'), _coeff('p', *B, 'sub_exists_B')),
                  'exists rb rc. ' + _aligned_subtract('p', *A, *B, 'rb', 'rc', length, 'sub_exists_result')),
        ('prime_field_polynomial_common_representatives_exists', 'prime_field_polynomial_subtract_exists',
         'prime_field_polynomial_subtract_recover_add', 'prime_field_polynomial_add_bounded',
         'prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_power_coefficient_functional',
         'prime_field_polynomial_equivalent_symmetric'), body,
        'Construct actual aligned field subtraction at length L+M, using real canonical common representatives and the genuine solution B+R=A.',
    )


def _sum_length(lengths: tuple[str, ...]) -> str:
    result = lengths[-1]
    for length in reversed(lengths[:-1]):
        result = '(' + length + ')+(' + result + ')'
    return result


def _length_bound(lengths: tuple[str, ...], index: int, tag: str) -> tuple[str, ...]:
    if len(lengths) == 1:
        return _call('le_refl', lengths[0])
    tail = _sum_length(lengths[1:])
    if index == 0:
        return _call('le_add_right', lengths[0], tail)
    name = 'length_bound_' + tag
    body = ('have ' + name + ' : ' + _le(lengths[index], tail, tag + '_inner'),)
    body += _length_bound(lengths[1:], index - 1, tag + '_inner')
    body += _call('le_trans', lengths[index], tail, _sum_length(lengths))
    return body + ('exact ' + name, 'exists ' + lengths[0], 'refl')


def _representatives(polys: tuple[tuple[str, str, str], ...], bounds: tuple[str, ...], tag: str):
    """Emit native constructions; this helper has no proof authority itself."""
    lengths = tuple(poly[2] for poly in polys)
    length = _sum_length(lengths)
    body: tuple[str, ...] = ()
    result = []
    for index, (poly, bound) in enumerate(zip(polys, bounds, strict=True)):
        hypothesis = tag + '_representative_' + str(index)
        witness_b, witness_c = hypothesis + '_code', hypothesis + '_scale'
        body += ('have ' + hypothesis + ' : exists ' + witness_b + ' ' + witness_c + '. ' + _and(
            _coeff('p', witness_b, witness_c, length, hypothesis + '_bounded'),
            _equivalent(*poly, witness_b, witness_c, length, hypothesis + '_equivalent')),)
        body += _call('prime_field_polynomial_bounded_representative_at_length_exists', 'p', *poly, length)
        body += ('exact hp', 'exact ' + bound) + _length_bound(lengths, index, hypothesis)
        body += ('cases ' + hypothesis, 'cases ' + hypothesis + '_witness',
                 'cases ' + hypothesis + '_witness_witness')
        codes = tuple('x' + (str(number) if number else '') for number in (2 * index, 2 * index + 1))
        result.append(((*codes, length), hypothesis + '_witness_witness_left',
                       hypothesis + '_witness_witness_right'))
    return body, tuple(result)


def _bounds(polys, hypothesis: str, name: str) -> tuple[str, ...]:
    body = ('have ' + name + ' : ' + _and(*(
        _coeff('p', *poly, name + '_' + str(index)) for index, poly in enumerate(polys))),)
    body += _call('prime_field_polynomial_aligned_add_bounded', 'p', *(value for poly in polys for value in poly))
    return body + ('exact ' + hypothesis,) + _parts(name, 3)


def _realize(polys, representatives, hypothesis: str, name: str) -> tuple[str, ...]:
    U, V, T = (item[0] for item in representatives)
    body = ('have ' + name + ' : ' + _add('p', *U[:2], *V[:2], *T[:2], U[2], name + '_operation'),)
    body += _call('prime_field_polynomial_aligned_add_realize',
                  'p', *(value for poly in polys for value in poly), *U[:2], *V[:2], *T[:2], U[2])
    body += ('exact hp', 'exact ' + hypothesis)
    body += tuple('exact ' + item[1] for item in representatives)
    return body + ('split', 'exact ' + representatives[0][2], 'exact ' + representatives[1][2],
                   'exact ' + representatives[2][2])


def _finish_equivalence(first, second, first_rep, second_rep, equality: str, tag: str) -> tuple[str, ...]:
    U, V = first_rep[0], second_rep[0]
    body = ('have ' + tag + '_middle : ' + _equivalent(*first, *V, tag + '_middle_result'),)
    body += _call('prime_field_polynomial_equivalent_transitive', *first, *U, *V)
    body += ('exact ' + first_rep[2],)
    body += _call('prime_field_polynomial_equal_implies_equivalent', *U[:2], *V[:2], U[2])
    body += ('exact ' + equality,)
    body += _call('prime_field_polynomial_equivalent_transitive', *first, *V, *second)
    body += ('exact ' + tag + '_middle',)
    body += _call('prime_field_polynomial_equivalent_symmetric', *second, *V)
    return body + ('exact ' + second_rep[2],)


ALIGNMENT_DEPENDENCIES = (
    'prime_field_polynomial_aligned_add_bounded',
    'prime_field_polynomial_bounded_representative_at_length_exists',
    'le_add_right', 'le_refl', 'le_trans', 'prime_field_polynomial_aligned_add_realize',
    'prime_field_polynomial_equivalent_transitive',
    'prime_field_polynomial_equal_implies_equivalent',
    'prime_field_polynomial_equivalent_symmetric',
)


def _cancel_row(spec: Callable[..., Any]) -> Any:
    C = ('cb', 'cc', 'J')
    polys = (A, B, C, R)
    parameters = ('p', *(value for poly in polys for value in poly))
    body = _intro(*parameters, 'hp', 'hb', 'hc')
    body += _bounds((A, B, R), 'hb', 'hbbound') + _bounds((A, C, R), 'hc', 'hcbound')
    construction, reps = _representatives(polys, ('hbbound_left', 'hbbound_right_left',
                                                 'hcbound_right_left', 'hbbound_right_right'), 'cancel')
    body += construction
    body += _realize((A, B, R), (reps[0], reps[1], reps[3]), 'hb', 'hfirst')
    body += _realize((A, C, R), (reps[0], reps[2], reps[3]), 'hc', 'hsecond')
    U, V, W, T = (item[0] for item in reps)
    body += ('have heq : ' + _equal(*V[:2], *W[:2], U[2], 'cancel_actual_outputs'),)
    body += _call('prime_field_polynomial_subtract_functional',
                  'p', *T[:2], *U[:2], *V[:2], *W[:2], U[2])
    body += _call('prime_field_polynomial_subtract_from_add', 'p', *T[:2], *U[:2], *V[:2], U[2])
    body += ('exact hfirst',)
    body += _call('prime_field_polynomial_subtract_from_add', 'p', *T[:2], *U[:2], *W[:2], U[2])
    body += ('exact hsecond',) + _finish_equivalence(B, C, reps[1], reps[2], 'heq', 'cancel')
    return spec(
        'prime_field_polynomial_aligned_add_cancel_left',
        _contract(parameters, (_prime('p', 'cancel_prime'),
                               _aligned_add('p', *A, *B, *R, 'cancel_first'),
                               _aligned_add('p', *A, *C, *R, 'cancel_second')),
                  _equivalent(*B, *C, 'cancel_result')),
        (*ALIGNMENT_DEPENDENCIES, 'prime_field_polynomial_subtract_functional',
         'prime_field_polynomial_subtract_from_add'), body,
        'Cancel a common addend from actual aligned sums: construct four real common-length prefixes, realize both additions and apply checked coefficient subtraction functionality.',
    )


def _associative_row(spec: Callable[..., Any]) -> Any:
    polys = tuple((letter + 'b', letter + 'c', 'L' + letter) for letter in ('a', 'b', 'c', 'u', 'v', 'r', 's'))
    A, B, C, U, V, R, S = polys
    operations = ((A, B, U), (U, C, R), (B, C, V), (A, V, S))
    hypotheses = ('hab', 'hleft', 'hbc', 'hright')
    parameters = ('p', *(value for poly in polys for value in poly))
    body = _intro(*parameters, 'hp', *hypotheses)
    for operation, hypothesis in zip(operations, hypotheses, strict=True):
        body += _bounds(operation, hypothesis, hypothesis + '_bounded')
    construction, reps = _representatives(polys, ('hab_bounded_left', 'hab_bounded_right_left',
        'hbc_bounded_right_left', 'hab_bounded_right_right', 'hbc_bounded_right_right',
        'hleft_bounded_right_right', 'hright_bounded_right_right'), 'associative')
    body += construction
    for operation, hypothesis, indices in zip(operations, hypotheses, ((0, 1, 3), (3, 2, 5), (1, 2, 4), (0, 4, 6)), strict=True):
        body += _realize(operation, tuple(reps[index] for index in indices), hypothesis, hypothesis + '_actual')
    codes = tuple(value for item in reps for value in item[0][:2])
    length = reps[0][0][2]
    body += ('have heq : ' + _equal(*reps[5][0][:2], *reps[6][0][:2], length, 'associative_actual_outputs'),)
    body += _call('prime_field_polynomial_add_associative', 'p', *codes, length)
    body += tuple('exact ' + hypothesis + '_actual' for hypothesis in hypotheses)
    body += _finish_equivalence(R, S, reps[5], reps[6], 'heq', 'associative')
    return spec(
        'prime_field_polynomial_aligned_add_associative',
        _contract(parameters, (_prime('p', 'associative_prime'),
                               *(_aligned_add('p', *(value for poly in operation for value in poly),
                                              'associative_' + str(index))
                                 for index, operation in enumerate(operations))),
                  _equivalent(*R, *S, 'associative_result')),
        (*ALIGNMENT_DEPENDENCIES, 'prime_field_polynomial_add_associative'), body,
        'Both actual bracketings of three independently sized polynomials give formally equivalent outputs; all seven comparison prefixes and all four coefficient operations are genuinely constructed.',
    )


def _subtract_functional_row(spec: Callable[..., Any]) -> Any:
    S = ('sb', 'sc', 'J')
    parameters = ('p', *A, *B, *R, *S)
    body = _intro(*parameters, 'hp', 'hr', 'hs')
    body += _call('prime_field_polynomial_aligned_add_cancel_left', 'p', *B, *R, *S, *A)
    body += ('exact hp', 'exact hr', 'exact hs')
    return spec(
        'prime_field_polynomial_aligned_subtract_functional',
        _contract(parameters, (_prime('p', 'sub_function_prime'),
                               _aligned_subtract('p', *A, *B, *R, 'sub_function_first'),
                               _aligned_subtract('p', *A, *B, *S, 'sub_function_second')),
                  _equivalent(*R, *S, 'sub_function_result')),
        ('prime_field_polynomial_aligned_add_cancel_left',), body,
        'Actual aligned subtraction has a formally unique result, including unequal lengths and unrelated beta encodings.',
    )


def make_prime_field_polynomial_aligned_algebra_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_subtract_exists_row(spec), _cancel_row(spec), _associative_row(spec),
            _subtract_functional_row(spec))


__all__ = ['make_prime_field_polynomial_aligned_algebra_candidate_theorems']
