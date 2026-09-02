"""Actual common-length representatives for formal polynomial operations.

Common representatives mean formal power-coefficient equivalence, not
evaluation equality, raw code equality, or a claim that a shorter prefix
is a padding.  The at-length constructor requires the genuine length
bounds and constructs actual leading-zero beta prefixes.  No edition,
kernel rule, proof capability, or published definition is registered here.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _coeff
from peano_lab.library.prime_field_polynomial_representation_candidate import (
    _equivalent, _le, _left_pad,
)
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _common_representatives(ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                           ub: str, uc: str, vb: str, vc: str, K: str, tag: str) -> str:
    return _and(_equivalent(ab, ac, L, ub, uc, K, tag + '_left'),
                _equivalent(bb, bc, M, vb, vc, K, tag + '_right'))


def prime_field_polynomial_common_representatives_relation(
        ab: str, ac: str, L: str, bb: str, bc: str, M: str,
        ub: str, uc: str, vb: str, vc: str, K: str, *,
        tag: str, variables: tuple[str, ...]) -> str:
    """Two actual length-K prefixes formally represent the independent inputs."""
    return _public(_common_representatives,
                   (ab, ac, L, bb, bc, M, ub, uc, vb, vc, K),
                   tag=tag, variables=variables)


A, B = ('ab', 'ac', 'L'), ('bb', 'bc', 'M')
U, V = ('ub', 'uc', 'K'), ('vb', 'vc', 'K')
PARAMETERS = (*A, *B, 'ub', 'uc', 'vb', 'vc', 'K')


def _bounded_representative(p: str, ab: str, ac: str, L: str,
                            ub: str, uc: str, K: str, tag: str) -> str:
    return _and(_coeff(p, ub, uc, K, tag + '_bounded'),
                _equivalent(ab, ac, L, ub, uc, K, tag + '_equivalent'))


def _bounded_common(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                    ub: str, uc: str, vb: str, vc: str, K: str, tag: str) -> str:
    return _and(_coeff(p, ub, uc, K, tag + '_left_bounded'),
                _coeff(p, vb, vc, K, tag + '_right_bounded'),
                _common_representatives(ab, ac, L, bb, bc, M,
                                        ub, uc, vb, vc, K, tag + '_common'))


def _representative_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A, 'K')
    body = _intro(*parameters, 'hp', 'ha', 'hlen') + ('cases hlen',)
    body += ('have hpad : exists ub uc. ('
             + _left_pad(*A, 'x', 'ub', 'uc', 'alignment_constructed_pad') + ')',)
    body += _call('prime_field_polynomial_left_pad_exists', 'ab', 'ac', 'x', 'L')
    body += ('cases hpad', 'cases hpad_witness', 'exists x1', 'exists x2', 'split')
    body += _rewrite_all('<- hlen_witness', _coeff('p', 'x1', 'x2', 'K', 'alignment_bound'), 'K')
    body += _call('prime_field_polynomial_left_pad_bounded', 'p', *A, 'x', 'x1', 'x2')
    body += ('exact hp', 'exact ha', 'exact hpad_witness_witness')
    body += _rewrite_all('<- hlen_witness', _equivalent(*A, 'x1', 'x2', 'K', 'alignment_equiv'), 'K')
    body += _call('prime_field_polynomial_left_pad_equivalent', *A, 'x', 'x1', 'x2')
    body += ('exact hpad_witness_witness',)
    return spec(
        'prime_field_polynomial_bounded_representative_at_length_exists',
        _contract(parameters, (_prime('p', 'alignment_prime'),
                               _coeff('p', *A, 'alignment_input'),
                               _le('L', 'K', 'alignment_length_bound')),
                  'exists ub uc. ' + _bounded_representative(
                      'p', *A, 'ub', 'uc', 'K', 'alignment_output')),
        ('prime_field_polynomial_left_pad_exists', 'prime_field_polynomial_left_pad_bounded',
         'prime_field_polynomial_left_pad_equivalent'), body,
        'From L<=K construct a genuine leading-zero beta prefix of length K, retain canonical coefficients, and prove formal equivalence to the input, including empty prefixes.',
    )


def _same_length_row(spec: Callable[..., Any]) -> Any:
    parameters = ('ab', 'ac', 'bb', 'bc', 'K')
    body = _intro(*parameters) + ('split',)
    body += _call('prime_field_polynomial_power_coefficient_functional', 'ab', 'ac', 'K')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'bb', 'bc', 'K')
    return spec(
        'prime_field_polynomial_common_representatives_same_length',
        _contract(parameters, (), _common_representatives(
            'ab', 'ac', 'K', 'bb', 'bc', 'K', 'ab', 'ac', 'bb', 'bc', 'K', 'common_self')),
        ('prime_field_polynomial_power_coefficient_functional',), body,
        'Two prefixes already at one length serve as their actual common representatives; no new beta encoding or prime premise is needed.',
    )


def _transport_row(spec: Callable[..., Any]) -> Any:
    D, E = ('db', 'dc', 'J'), ('eb', 'ec', 'N')
    parameters = (*PARAMETERS, *D, *E)
    body = _intro(*parameters, 'ha', 'hb', 'h') + ('cases h', 'split')
    body += _call('prime_field_polynomial_equivalent_transitive', *D, *A, *U)
    body += ('exact ha', 'exact h_left')
    body += _call('prime_field_polynomial_equivalent_transitive', *E, *B, *V)
    body += ('exact hb', 'exact h_right')
    return spec(
        'prime_field_polynomial_common_representatives_transport',
        _contract(parameters, (_equivalent(*D, *A, 'common_transport_left'),
                               _equivalent(*E, *B, 'common_transport_right'),
                               _common_representatives(*PARAMETERS, 'common_transport_old')),
                  _common_representatives(*D, *E, 'ub', 'uc', 'vb', 'vc', 'K',
                                          'common_transport_new')),
        ('prime_field_polynomial_equivalent_transitive',), body,
        'Independent formal recodings of the original inputs preserve the same actual common representatives, without asserting a padding length inequality.',
    )


def _common_exists_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('p', *A, *B, 'K')
    body = _intro(*parameters, 'hp', 'ha', 'hb', 'hL', 'hM')
    body += ('have hu : exists ub uc. ' + _bounded_representative(
        'p', *A, 'ub', 'uc', 'K', 'common_construct_left'),)
    body += _call('prime_field_polynomial_bounded_representative_at_length_exists', 'p', *A, 'K')
    body += ('exact hp', 'exact ha', 'exact hL', 'cases hu', 'cases hu_witness',
             'cases hu_witness_witness')
    body += ('have hv : exists vb vc. ' + _bounded_representative(
        'p', *B, 'vb', 'vc', 'K', 'common_construct_right'),)
    body += _call('prime_field_polynomial_bounded_representative_at_length_exists', 'p', *B, 'K')
    body += ('exact hp', 'exact hb', 'exact hM', 'cases hv', 'cases hv_witness',
             'cases hv_witness_witness', 'exists x', 'exists x1', 'exists x2', 'exists x3',
             'split', 'exact hu_witness_witness_left', 'split', 'exact hv_witness_witness_left',
             'split', 'exact hu_witness_witness_right', 'exact hv_witness_witness_right')
    at_length = spec(
        'prime_field_polynomial_common_representatives_at_length_exists',
        _contract(parameters, (_prime('p', 'common_at_prime'), _coeff('p', *A, 'common_at_A'),
                               _coeff('p', *B, 'common_at_B'), _le('L', 'K', 'common_at_L'),
                               _le('M', 'K', 'common_at_M')),
                  'exists ub uc vb vc. ' + _bounded_common('p', *PARAMETERS, 'common_at_output')),
        ('prime_field_polynomial_bounded_representative_at_length_exists',), body,
        'Construct two actual canonical common-length representatives by independent leading-zero padding at any supplied common upper bound.',
    )
    parameters = ('p', *A, *B)
    body = _intro(*parameters, 'hp', 'ha', 'hb')
    body += _call('prime_field_polynomial_common_representatives_at_length_exists', *parameters, 'L+M')
    body += ('exact hp', 'exact ha', 'exact hb') + _call('le_add_right', 'L', 'M')
    body += ('exists L', 'refl')
    exists = spec(
        'prime_field_polynomial_common_representatives_exists',
        _contract(parameters, (_prime('p', 'common_exists_prime'),
                               _coeff('p', *A, 'common_exists_A'), _coeff('p', *B, 'common_exists_B')),
                  'exists ub uc vb vc. ' + _bounded_common(
                      'p', *A, *B, 'ub', 'uc', 'vb', 'vc', 'L+M', 'common_exists_output')),
        ('prime_field_polynomial_common_representatives_at_length_exists', 'le_add_right'), body,
        'Use the explicit common length L+M to construct real canonical representatives for any two independently sized inputs, including zero lengths.',
    )
    return at_length, exists


def _functional_row(spec: Callable[..., Any]) -> Any:
    parameters = (*PARAMETERS, 'db', 'dc', 'eb', 'ec', 'J')
    D, E = ('db', 'dc', 'J'), ('eb', 'ec', 'J')
    body = _intro(*parameters, 'h', 'hnew') + ('cases h', 'cases hnew', 'split')
    for original, first, other, old_hyp, new_hyp, tag in (
            (A, U, D, 'h_left', 'hnew_left', 'common_function_left'),
            (B, V, E, 'h_right', 'hnew_right', 'common_function_right')):
        body += ('have hr : ' + _equivalent(*first, *original, tag + '_reverse'),)
        body += _call('prime_field_polynomial_equivalent_symmetric', *original, *first)
        body += ('exact ' + old_hyp,)
        body += _call('prime_field_polynomial_equivalent_transitive', *first, *original, *other)
        body += ('exact hr', 'exact ' + new_hyp)
    return spec(
        'prime_field_polynomial_common_representatives_functional',
        _contract(parameters, (_common_representatives(*PARAMETERS, 'common_function_first'),
                               _common_representatives(*A, *B, 'db', 'dc', 'eb', 'ec', 'J',
                                                       'common_function_second')),
                  _and(_equivalent(*U, *D, 'common_function_result_left'),
                       _equivalent(*V, *E, 'common_function_result_right'))),
        ('prime_field_polynomial_equivalent_symmetric', 'prime_field_polynomial_equivalent_transitive'),
        body,
        'Any two choices of common representatives are pairwise formally equivalent, even at different common lengths; no raw-code or length uniqueness is asserted.',
    )


def _symmetric_row(spec: Callable[..., Any]) -> Any:
    return spec(
        'prime_field_polynomial_common_representatives_symmetric',
        _contract(PARAMETERS, (_common_representatives(*PARAMETERS, 'common_symmetric_old'),),
                  _common_representatives(*B, *A, 'vb', 'vc', 'ub', 'uc', 'K',
                                          'common_symmetric_new')),
        (), _intro(*PARAMETERS, 'h') + ('cases h', 'split', 'exact h_right', 'exact h_left'),
        'Swapping the two original inputs and their actual representatives preserves the common-representation graph.',
    )


def make_prime_field_polynomial_alignment_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_representative_exists_row(spec), _same_length_row(spec),
            _transport_row(spec), *_common_exists_rows(spec), _functional_row(spec),
            _symmetric_row(spec))


__all__ = ['make_prime_field_polynomial_alignment_candidate_theorems',
           'prime_field_polynomial_common_representatives_relation']
