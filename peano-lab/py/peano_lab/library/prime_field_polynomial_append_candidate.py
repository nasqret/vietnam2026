"""Actual right-factor append recurrence for highest-degree-first prefixes.

Append is the existing pair of beta-prefix preservation and a witnessed next
entry, not a new definition.  Shift below is exactly the frozen PolynomialShift
expansion.  All other graphs are unchanged canonical operations.  No desired
convolution identity, evaluation agreement or raw-code equality is an input
definition.  Genuine intermediate products and aligned sums are constructed.

This working-only source prepares, but does not prove, associativity or gcd.
Its direct test provider loads the frozen shift/scalar factories by exact file
path without adding package aliases.  No admission or runtime mutation occurs.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _add as _field_add, _and, _call, _intro, _lt, _parts, _prime,
)
from peano_lab.library.prime_field_polynomial_candidate import (
    _add, _at, _coeff, _equal, _repeat, _scale,
)
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _length,
)
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _left_pad
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result)
    )


def _shift(b: str, c: str, length: str, d: str, e: str, tag: str) -> str:
    # Existing ND0341, expanded from its two existing conservative clauses.
    return _and(_equal(b, c, d, e, length, tag + 'prefix'),
                _at(d, e, length, '0', tag + 'last'))


def _decomposition_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'bb', 'bc', 'M', 'c', 'db', 'dc', 'sb', 'sc', 'kb', 'kc', 'tb', 'tc')
    body = _intro(*parameters, 'hp', 'hb', 'hc', 'he', 'hlast', 'hs', 'hk', 'ht')
    body += ('cases hs', 'cases ht')
    body += (f"have hconstant : {_at('tb','tc','M','c','append_sum_constant')}",)
    body += (f"have hraw : {_at('tb','tc','M+0','c','append_sum_raw_constant')}",)
    body += _call('ht_right', '0', 'c') + ('exists 0', 'simp', 'exact hk', 'have hindex : M+0=M', 'simp')
    body += _rewrite_all('hindex', _at('tb', 'tc', 'M+0', 'c', 'append_sum_constant_rewrite'), 'M+0', 'hraw')
    body += ('exact hraw',) + _intro('i', 'hi')
    body += (f"have hcase : i=M \\/ ({_lt('i','M','append_sum_earlier_index')})",)
    body += _call('finite_lt_succ_eq_or_lt', 'M', 'i') + ('exact hi', 'cases hcase', 'exists 0', 'exists c', 'exists c', 'split')
    body += _rewrite_all('hcase_left', _at('sb', 'sc', 'i', '0', 'append_sum_last_shift'), 'i') + ('exact hs_right', 'split')
    body += _rewrite_all('hcase_left', _at('tb', 'tc', 'i', 'c', 'append_sum_last_constant'), 'i') + ('exact hconstant', 'split')
    body += _rewrite_all('hcase_left', _at('db', 'dc', 'i', 'c', 'append_sum_last_output'), 'i') + ('exact hlast',)
    body += _call('prime_field_add_zero_left', 'p', 'c') + ('exact hp', 'exact hc')
    chosen = _and(_at('bb', 'bc', 'i', 'a', 'append_sum_old_value'), _lt('a', 'p', 'append_sum_old_bound'))
    body += ('have ha : exists a. ' + chosen,) + _call('hb', 'i')
    body += ('exact hcase_right', 'cases ha', 'cases ha_witness', 'exists x', 'exists 0', 'exists x', 'split')
    body += _call('hs_left', 'i', 'x') + ('exact hcase_right', 'exact ha_witness_left', 'split')
    body += _call('ht_left', 'i') + ('exact hcase_right', 'split')
    body += _call('he', 'i', 'x') + ('exact hcase_right', 'exact ha_witness_left')
    body += _call('prime_field_add_zero_right', 'p', 'x') + ('exact hp', 'exact ha_witness_right')
    return spec(
        'prime_field_polynomial_append_shift_constant_add',
        _contract(parameters, (
            _prime('p', 'append_sum_prime'), _coeff('p', 'bb', 'bc', 'M', 'append_sum_old_coefficients'),
            _lt('c', 'p', 'append_sum_scalar'), _equal('bb', 'bc', 'db', 'dc', 'M', 'append_sum_preserve'),
            _at('db', 'dc', 'M', 'c', 'append_sum_actual_last'), _shift('bb', 'bc', 'M', 'sb', 'sc', 'append_sum_shift'),
            _at('kb', 'kc', '0', 'c', 'append_sum_singleton'), _left_pad('kb', 'kc', '1', 'M', 'tb', 'tc', 'append_sum_left_pad'),
        ), _add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'S M', 'append_sum_result')),
        ('finite_lt_succ_eq_or_lt', 'prime_field_add_zero_left', 'prime_field_add_zero_right'), body,
        'Every actual appended prefix is the actual aligned sum of a genuine trailing-zero shift and the leading-padded singleton constant; the last and earlier entries are proved separately, including M=0.',
    )


def _decomposition_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'bb', 'bc', 'M', 'c', 'db', 'dc')
    shift = _shift('bb', 'bc', 'M', 'sb', 'sc', 'append_decomposition_shift')
    bounded = _coeff('p', 'kb', 'kc', '1', 'append_decomposition_constant_bound')
    constant = _at('kb', 'kc', '0', 'c', 'append_decomposition_constant')
    padded = _left_pad('kb', 'kc', '1', 'M', 'tb', 'tc', 'append_decomposition_pad')
    added = _add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'S M', 'append_decomposition_add')
    body = _intro(*parameters, 'hp', 'hb', 'hc', 'he', 'hlast')
    body += ('have hs : exists sb sc. ' + shift,) + _call('prime_field_polynomial_shift_exists', 'bb', 'bc', 'M')
    body += ('cases hs', 'cases hs_witness')
    repeated = _repeat('kb', 'kc', 'c', '1', 'append_decomposition_repeat')
    body += ('have hk : exists kb kc. ' + repeated,) + _call('beta_repeat_exists', 'c', '1')
    body += ('cases hk', 'cases hk_witness')
    body += (f"have hconstant : {_at('x2','x3','0','c','append_decomposition_chosen_constant')}",)
    body += _call('hk_witness_witness', '0') + ('exists 0', 'simp')
    body += (f"have hbounded : {_coeff('p','x2','x3','1','append_decomposition_chosen_bound')}",)
    body += _intro('i', 'hi') + ('exists c', 'split') + _call('hk_witness_witness', 'i') + ('exact hi', 'exact hc')
    selected_pad = _left_pad('x2', 'x3', '1', 'M', 'tb', 'tc', 'append_decomposition_chosen_pad')
    body += ('have ht : exists tb tc. ' + selected_pad,)
    body += _call('prime_field_polynomial_left_pad_exists', 'x2', 'x3', 'M', '1')
    body += ('cases ht', 'cases ht_witness', 'exists x', 'exists x1', 'exists x2', 'exists x3', 'exists x4', 'exists x5',
             'split', 'exact hs_witness_witness', 'split', 'exact hbounded', 'split', 'exact hconstant', 'split', 'exact ht_witness_witness')
    body += _call('prime_field_polynomial_append_shift_constant_add',
                  'p', 'bb', 'bc', 'M', 'c', 'db', 'dc', 'x', 'x1', 'x2', 'x3', 'x4', 'x5')
    body += ('exact hp', 'exact hb', 'exact hc', 'exact he', 'exact hlast', 'exact hs_witness_witness', 'exact hconstant', 'exact ht_witness_witness')
    return spec(
        'prime_field_polynomial_append_shift_constant_decomposition_exists',
        _contract(parameters, (
            _prime('p', 'append_decomposition_prime'), _coeff('p', 'bb', 'bc', 'M', 'append_decomposition_old_coefficients'),
            _lt('c', 'p', 'append_decomposition_scalar'), _equal('bb', 'bc', 'db', 'dc', 'M', 'append_decomposition_preserve'),
            _at('db', 'dc', 'M', 'c', 'append_decomposition_actual_last'),
        ), 'exists sb sc kb kc tb tc. ' + _and(shift, bounded, constant, padded, added)),
        ('prime_field_polynomial_shift_exists', 'beta_repeat_exists', 'prime_field_polynomial_left_pad_exists',
         'prime_field_polynomial_append_shift_constant_add'), body,
        'Construct the shifted old prefix, a canonical singleton constant and its genuine leading padding, then prove their actual aligned sum is the given appended prefix.',
    )


FACTORS = ('ab', 'ac', 'L', 'bb', 'bc', 'M')


def _coefficient_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *FACTORS, 'c', 'db', 'dc', 'kb', 'kc', 'tb', 'tc', 'i', 'u', 'v', 'w')
    old = _coefficient('p', *FACTORS, 'i', 'u', 'append_coefficient_old')
    constant = _coefficient('p', 'ab', 'ac', 'L', 'tb', 'tc', 'S M', 'i', 'v', 'append_coefficient_constant')
    new = _coefficient('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'i', 'w', 'append_coefficient_new')
    body = _intro(*parameters, 'hp', 'hb', 'hc', 'he', 'hlast', 'hk', 'ht', 'hu', 'hv', 'hw')
    shift = _shift('bb', 'bc', 'M', 'sb', 'sc', 'append_coefficient_chosen_shift')
    body += ('have hs : exists sb sc. ' + shift,) + _call('prime_field_polynomial_shift_exists', 'bb', 'bc', 'M')
    body += ('cases hs', 'cases hs_witness')
    shifted = _coefficient('p', 'ab', 'ac', 'L', 'x', 'x1', 'S M', 'i', 'u', 'append_coefficient_shifted')
    body += ('have hshifted : ' + shifted,)
    body += ('have hboth : ' + _and('(' + old + ') -> (' + shifted + ')', '(' + shifted + ') -> (' + old + ')'),)
    body += _call('prime_field_convolution_coefficient_shift_right_iff', 'p', *FACTORS, 'x', 'x1', 'i', 'u')
    body += ('exact hs_witness_witness', 'cases hboth', 'apply hboth_left', 'exact hu')
    body += _call('prime_field_convolution_coefficient_left_add',
                  'p', 'x', 'x1', 'tb', 'tc', 'db', 'dc', 'S M', 'ab', 'ac', 'L', 'i', 'u', 'v', 'w')
    body += _call('prime_field_polynomial_append_shift_constant_add',
                  'p', 'bb', 'bc', 'M', 'c', 'db', 'dc', 'x', 'x1', 'kb', 'kc', 'tb', 'tc')
    body += ('exact hp', 'exact hb', 'exact hc', 'exact he', 'exact hlast', 'exact hs_witness_witness',
             'exact hk', 'exact ht', 'exact hshifted', 'exact hv', 'exact hw')
    return spec(
        'prime_field_convolution_coefficient_right_append_add',
        _contract(parameters, (
            _prime('p', 'append_coefficient_prime'), _coeff('p', 'bb', 'bc', 'M', 'append_coefficient_old_coefficients'),
            _lt('c', 'p', 'append_coefficient_scalar'), _equal('bb', 'bc', 'db', 'dc', 'M', 'append_coefficient_preserve'),
            _at('db', 'dc', 'M', 'c', 'append_coefficient_actual_last'), _at('kb', 'kc', '0', 'c', 'append_coefficient_singleton'),
            _left_pad('kb', 'kc', '1', 'M', 'tb', 'tc', 'append_coefficient_pad'), old, constant, new,
        ), _field_add('p', 'u', 'v', 'w', 'append_coefficient_result')),
        ('prime_field_polynomial_shift_exists', 'prime_field_convolution_coefficient_shift_right_iff',
         'prime_field_convolution_coefficient_left_add', 'prime_field_polynomial_append_shift_constant_add'), body,
        'At every natural coefficient index, an actual right append is the actual field sum of the old convolution coefficient and the product with the padded singleton constant, using genuine diagonal sums and residues rather than a finite-evaluation identity.',
    )


ALIGNED_PARAMETERS = ('p', 'c', 'ab', 'ac', 'L', 'pb', 'pc', 'N')
ALIGNED_OUTPUTS = ('ub', 'uc', 'vb', 'vc', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc')
COMMON_LENGTH = 'L+S N'


def _alignment_parts(tag: str) -> tuple[str, ...]:
    return (
        _shift('pb', 'pc', 'N', 'ub', 'uc', tag + 'shift'),
        _scale('p', 'c', 'ab', 'ac', 'vb', 'vc', 'L', tag + 'scale'),
        _left_pad('ub', 'uc', 'S N', 'L', 'UB', 'UC', tag + 'left'),
        _left_pad('vb', 'vc', 'L', 'S N', 'VB', 'VC', tag + 'right'),
        _add('p', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc', COMMON_LENGTH, tag + 'sum'),
    )


def _alignment_exists_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*ALIGNED_PARAMETERS, 'hp', 'hc', 'ha', 'hb')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    shift, scaled, *_ = _alignment_parts('append_alignment_')
    body += ('have hu : exists ub uc. ' + shift,) + _call('prime_field_polynomial_shift_exists', 'pb', 'pc', 'N')
    body += ('cases hu', 'cases hu_witness', 'have hv : exists vb vc. ' + scaled)
    body += _call('prime_field_polynomial_scale_exists', 'p', 'c', 'ab', 'ac', 'L')
    body += ('exact hp0', 'exact hc', 'exact ha', 'cases hv', 'cases hv_witness')
    left = _left_pad('x', 'x1', 'S N', 'L', 'UB', 'UC', 'append_alignment_chosen_left')
    right = _left_pad('x2', 'x3', 'L', 'S N', 'VB', 'VC', 'append_alignment_chosen_right')
    body += ('have hleft : exists UB UC. ' + left,)
    body += _call('prime_field_polynomial_left_pad_exists', 'x', 'x1', 'L', 'S N')
    body += ('cases hleft', 'cases hleft_witness', 'have hright : exists VB VC. ' + right)
    body += _call('prime_field_polynomial_left_pad_exists', 'x2', 'x3', 'S N', 'L')
    body += ('cases hright', 'cases hright_witness')
    body += (f"have hleft_bound : {_coeff('p','x4','x5',COMMON_LENGTH,'append_alignment_left_bound')}",)
    body += _call('prime_field_polynomial_left_pad_bounded', 'p', 'x', 'x1', 'S N', 'L', 'x4', 'x5')
    body += ('exact hp',) + _call('prime_field_polynomial_shift_bounded', 'p', 'pb', 'pc', 'N', 'x', 'x1')
    body += ('exact hp', 'exact hb', 'exact hu_witness_witness', 'exact hleft_witness_witness')
    bounds = _and(_coeff('p', 'ab', 'ac', 'L', 'append_alignment_source_bound'),
                  _coeff('p', 'x2', 'x3', 'L', 'append_alignment_scale_bound'))
    body += ('have hscale_bounds : ' + bounds,)
    body += _call('prime_field_polynomial_scale_bounded', 'p', 'c', 'ab', 'ac', 'x2', 'x3', 'L')
    body += ('exact hv_witness_witness', 'cases hscale_bounds')
    raw_bound = _coeff('p', 'x6', 'x7', 'S N+L', 'append_alignment_right_bound')
    body += ('have hright_bound : ' + raw_bound,)
    body += _call('prime_field_polynomial_left_pad_bounded', 'p', 'x2', 'x3', 'L', 'S N', 'x6', 'x7')
    body += ('exact hp', 'exact hscale_bounds_right', 'exact hright_witness_witness')
    body += ('have hcomm : S N+L=L+S N',) + _call('add_comm', 'S N', 'L')
    body += _rewrite_all('hcomm', raw_bound, 'S N+L', 'hright_bound')
    added = _add('p', 'x4', 'x5', 'x6', 'x7', 'rb', 'rc', COMMON_LENGTH, 'append_alignment_chosen_sum')
    body += ('have hsum : exists rb rc. ' + added,)
    body += _call('prime_field_polynomial_add_exists', 'p', 'x4', 'x5', 'x6', 'x7', COMMON_LENGTH)
    body += ('exact hp0', 'exact hleft_bound', 'exact hright_bound', 'cases hsum', 'cases hsum_witness')
    body += tuple('exists ' + name for name in ('x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9'))
    body += ('split', 'exact hu_witness_witness', 'split', 'exact hv_witness_witness',
             'split', 'exact hleft_witness_witness', 'split', 'exact hright_witness_witness', 'exact hsum_witness_witness')
    return spec(
        'prime_field_polynomial_shift_scale_aligned_sum_exists',
        _contract(ALIGNED_PARAMETERS, (
            _prime('p', 'append_alignment_prime'), _lt('c', 'p', 'append_alignment_scalar'),
            _coeff('p', 'ab', 'ac', 'L', 'append_alignment_A'), _coeff('p', 'pb', 'pc', 'N', 'append_alignment_P'),
        ), 'exists ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + _and(*_alignment_parts('append_alignment_result_'))),
        ('prime_nonzero', 'prime_field_polynomial_shift_exists', 'prime_field_polynomial_scale_exists',
         'prime_field_polynomial_left_pad_exists', 'prime_field_polynomial_left_pad_bounded',
         'prime_field_polynomial_shift_bounded', 'prime_field_polynomial_scale_bounded', 'add_comm',
         'prime_field_polynomial_add_exists'), body,
        'Construct actual shift and scalar outputs, harmless leading paddings to the common length L+S N, and their actual coefficient sum; the commuted S N+L bound is explicitly reconciled, including both empty inputs.',
    )


RECURRENCE_BASE = ('p', *FACTORS, 'c', 'db', 'dc', 'pb', 'pc', 'N', 'qb', 'qc', 'K')
RECURRENCE_PARAMETERS = (*RECURRENCE_BASE, *ALIGNED_OUTPUTS)


def _recurrence_row(spec: Callable[..., Any]) -> Any:
    old = _convolution('p', *FACTORS, 'pb', 'pc', 'N', 'append_recurrence_old')
    new = _convolution('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'qb', 'qc', 'K', 'append_recurrence_new')
    body = _intro(*RECURRENCE_PARAMETERS, 'hp', 'he', 'hlast', 'hP', 'hQ', 'hU', 'hV', 'hUP', 'hVP', 'hR')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    body += ('have hold : ' + old, 'exact hP') + _parts('hold', 4)
    body += ('have hnew : ' + new, 'exact hQ') + _parts('hnew', 4)
    body += (f"have hv_copy : {_scale('p','c','ab','ac','vb','vc','L','append_recurrence_scalar_copy')}", 'exact hV', 'cases hv_copy')
    decomposed = _and(
        _shift('bb', 'bc', 'M', 'sb', 'sc', 'append_recurrence_decomposition_shift'),
        _coeff('p', 'kb', 'kc', '1', 'append_recurrence_decomposition_bound'),
        _at('kb', 'kc', '0', 'c', 'append_recurrence_decomposition_constant'),
        _left_pad('kb', 'kc', '1', 'M', 'tb', 'tc', 'append_recurrence_decomposition_pad'),
        _add('p', 'sb', 'sc', 'tb', 'tc', 'db', 'dc', 'S M', 'append_recurrence_decomposition_sum'),
    )
    body += ('have hdecomp : exists sb sc kb kc tb tc. ' + decomposed,)
    body += _call('prime_field_polynomial_append_shift_constant_decomposition_exists', 'p', 'bb', 'bc', 'M', 'c', 'db', 'dc')
    body += ('exact hp', 'exact hold_right_left', 'exact hv_copy_left', 'exact he', 'exact hlast')
    body += tuple('cases hdecomp' + '_witness' * i for i in range(6))
    chosen = 'hdecomp' + '_witness' * 6
    body += _parts(chosen, 5)
    first_factor = ('ab', 'ac', 'L', 'x', 'x1', 'S M')
    second_factor = ('ab', 'ac', 'L', 'x4', 'x5', 'S M')
    bounds = _and(_coeff('p', 'x', 'x1', 'S M', 'append_recurrence_shift_bound'),
                  _coeff('p', 'x4', 'x5', 'S M', 'append_recurrence_padded_constant_bound'),
                  _coeff('p', 'db', 'dc', 'S M', 'append_recurrence_append_bound'))
    body += ('have hbounds : ' + bounds,)
    body += _call('prime_field_polynomial_add_bounded', 'p', 'x', 'x1', 'x4', 'x5', 'db', 'dc', 'S M')
    body += ('exact ' + chosen + '_right_right_right_right',) + _parts('hbounds', 3)
    for label, factors, bound in (('hfirst', first_factor, 'hbounds_left'),
                                   ('hsecond', second_factor, 'hbounds_right_left')):
        product = _convolution('p', *factors, 'fb', 'fc', 'K', 'append_recurrence_' + label)
        body += ('have ' + label + ' : exists fb fc. ' + product,)
        body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', *factors, 'K')
        body += ('exact hp0', 'exact hold_left', 'exact ' + bound, 'exact hnew_right_right_left',
                 'cases ' + label, 'cases ' + label + '_witness')
    distributed = _add('p', 'x6', 'x7', 'x8', 'x9', 'qb', 'qc', 'K', 'append_recurrence_distributed')
    body += ('have hdistributed : ' + distributed,)
    body += _call('prime_field_polynomial_convolution_left_add',
                  'p', 'x', 'x1', 'x4', 'x5', 'db', 'dc', 'S M', 'ab', 'ac', 'L', 'x6', 'x7', 'x8', 'x9', 'qb', 'qc', 'K')
    body += ('exact ' + chosen + '_right_right_right_right', 'exact hfirst_witness_witness',
             'exact hsecond_witness_witness', 'exact hQ')
    shifted_equal = _equivalent('x6', 'x7', 'K', 'ub', 'uc', 'S N', 'append_recurrence_shift_equivalent')
    body += ('have hshifted_equal : ' + shifted_equal,)
    body += _call('prime_field_polynomial_convolution_shift_right_equivalent',
                  'p', *FACTORS, 'pb', 'pc', 'N', 'x', 'x1', 'x6', 'x7', 'K', 'ub', 'uc')
    body += ('exact hp0', 'exact ' + chosen + '_left', 'exact hP', 'exact hfirst_witness_witness', 'exact hU')
    first_equal = _equivalent('x6', 'x7', 'K', 'UB', 'UC', COMMON_LENGTH, 'append_recurrence_aligned_first')
    body += ('have hfirst_equal : ' + first_equal,)
    body += _call('prime_field_polynomial_equivalent_transitive', 'x6', 'x7', 'K', 'ub', 'uc', 'S N', 'UB', 'UC', COMMON_LENGTH)
    body += ('exact hshifted_equal',) + _call('prime_field_polynomial_left_pad_equivalent', 'ub', 'uc', 'S N', 'L', 'UB', 'UC')
    body += ('exact hUP',)
    constant_product = _convolution('p', 'ab', 'ac', 'L', 'x2', 'x3', '1', 'vb', 'vc', 'L', 'append_recurrence_constant_product')
    body += ('have hconstant_product : ' + constant_product,)
    body += _call('prime_field_polynomial_scale_to_constant_product', 'p', 'c', 'ab', 'ac', 'x2', 'x3', 'vb', 'vc', 'L')
    body += ('exact hp', 'exact ' + chosen + '_right_left', 'exact ' + chosen + '_right_right_left', 'exact hV')
    reverse_equal = _equivalent('vb', 'vc', 'L', 'x8', 'x9', 'K', 'append_recurrence_constant_equivalent')
    body += ('have hreverse_equal : ' + reverse_equal,)
    body += _call('prime_field_polynomial_convolution_left_padding_equivalent_right',
                  'p', 'ab', 'ac', 'L', 'x2', 'x3', '1', 'vb', 'vc', 'L', 'x4', 'x5', 'M', 'x8', 'x9', 'K')
    body += ('exact hp0', 'exact ' + chosen + '_right_right_right_left', 'exact hconstant_product', 'have hlength : M+1=S M', 'simp')
    converted = _convolution('p', 'ab', 'ac', 'L', 'x4', 'x5', 'M+1', 'x8', 'x9', 'K', 'append_recurrence_convert_length')
    body += _rewrite_all('hlength', converted, 'M+1') + ('exact hsecond_witness_witness',)
    second_equal = _equivalent('x8', 'x9', 'K', 'VB', 'VC', COMMON_LENGTH, 'append_recurrence_aligned_second')
    body += ('have hsecond_equal : ' + second_equal,)
    body += _call('prime_field_polynomial_equivalent_transitive', 'x8', 'x9', 'K', 'vb', 'vc', 'L', 'VB', 'VC', COMMON_LENGTH)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'vb', 'vc', 'L', 'x8', 'x9', 'K') + ('exact hreverse_equal',)
    pad_equal = _equivalent('vb', 'vc', 'L', 'VB', 'VC', 'S N+L', 'append_recurrence_commuted_padding')
    body += ('have hpad_equal : ' + pad_equal,)
    body += _call('prime_field_polynomial_left_pad_equivalent', 'vb', 'vc', 'L', 'S N', 'VB', 'VC') + ('exact hVP',)
    body += ('have hcomm : S N+L=L+S N',) + _call('add_comm', 'S N', 'L')
    body += _rewrite_all('hcomm', pad_equal, 'S N+L', 'hpad_equal') + ('exact hpad_equal',)
    body += _call('prime_field_polynomial_add_equivalent_congruent',
                  'p', 'x6', 'x7', 'x8', 'x9', 'qb', 'qc', 'K', 'UB', 'UC', 'VB', 'VC', 'rb', 'rc', COMMON_LENGTH)
    body += ('exact hp', 'exact hfirst_equal', 'exact hsecond_equal', 'exact hdistributed', 'exact hR')
    return spec(
        'prime_field_polynomial_convolution_right_append_equivalent',
        _contract(RECURRENCE_PARAMETERS, (
            _prime('p', 'append_recurrence_prime'), _equal('bb', 'bc', 'db', 'dc', 'M', 'append_recurrence_preserve'),
            _at('db', 'dc', 'M', 'c', 'append_recurrence_last'), old, new, *_alignment_parts('append_recurrence_'),
        ), _equivalent('qb', 'qc', 'K', 'rb', 'rc', COMMON_LENGTH, 'append_recurrence_result')),
        ('prime_nonzero', 'prime_field_polynomial_append_shift_constant_decomposition_exists',
         'prime_field_polynomial_add_bounded', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_left_add', 'prime_field_polynomial_convolution_shift_right_equivalent',
         'prime_field_polynomial_equivalent_transitive', 'prime_field_polynomial_left_pad_equivalent',
         'prime_field_polynomial_scale_to_constant_product', 'prime_field_polynomial_convolution_left_padding_equivalent_right',
         'prime_field_polynomial_equivalent_symmetric', 'add_comm', 'prime_field_polynomial_add_equivalent_congruent'), body,
        'An actual right-factor append satisfies A*append(C,c) formally equivalent to X*(A*C)+c*A through genuine products and arbitrary actual aligned sum outputs. Lengths are not falsely equated in empty cases, and no finite-field evaluation agreement replaces all formal coefficients.',
    )


def _recurrence_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *FACTORS, 'c', 'pb', 'pc', 'N')
    old = _convolution('p', *FACTORS, 'pb', 'pc', 'N', 'append_exists_old')
    preserve = _equal('bb', 'bc', 'db', 'dc', 'M', 'append_exists_preserve')
    last = _at('db', 'dc', 'M', 'c', 'append_exists_last')
    new = _convolution('p', 'ab', 'ac', 'L', 'db', 'dc', 'S M', 'qb', 'qc', 'K', 'append_exists_new')
    equal = _equivalent('qb', 'qc', 'K', 'rb', 'rc', COMMON_LENGTH, 'append_exists_equivalence')
    body = _intro(*parameters, 'hp', 'hc', 'hP')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hp', 'exact hz')
    body += ('have hold : ' + old, 'exact hP') + _parts('hold', 4)
    body += ('have hd : exists db dc. ' + _and(last, preserve),) + _call('beta_prefix_extend', 'M', 'bb', 'bc', 'c')
    body += ('cases hd', 'cases hd_witness', 'cases hd_witness_witness')
    body += (f"have hbounded : {_coeff('p','x','x1','S M','append_exists_new_bound')}",)
    body += _call('matrix_rank_bounded_prefix_extend', 'x', 'x1', 'M', 'p', 'c')
    body += _call('matrix_rank_bounded_prefix_transport', 'bb', 'bc', 'x', 'x1', 'M', 'p')
    body += ('exact hd_witness_witness_right', 'exact hold_right_left', 'exact hd_witness_witness_left', 'exact hc')
    body += (f"have hl : exists K. {_length('L','S M','K','append_exists_product_length')}",)
    body += _call('polynomial_product_length_exists', 'L', 'S M') + ('cases hl',)
    chosen_product = _convolution('p', 'ab', 'ac', 'L', 'x', 'x1', 'S M', 'qb', 'qc', 'x2', 'append_exists_chosen_product')
    body += ('have hQ : exists qb qc. ' + chosen_product,)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', 'ab', 'ac', 'L', 'x', 'x1', 'S M', 'x2')
    body += ('exact hp0', 'exact hold_left', 'exact hbounded', 'exact hl_witness', 'cases hQ', 'cases hQ_witness')
    alignment = _and(*_alignment_parts('append_exists_alignment_'))
    body += ('have hA : exists ' + ' '.join(ALIGNED_OUTPUTS) + '. ' + alignment,)
    body += _call('prime_field_polynomial_shift_scale_aligned_sum_exists', *ALIGNED_PARAMETERS)
    body += ('exact hp', 'exact hc', 'exact hold_left')
    body += _call('prime_field_polynomial_convolution_bounded', 'p', *FACTORS, 'pb', 'pc', 'N') + ('exact hP',)
    body += tuple('cases hA' + '_witness' * i for i in range(10))
    chosen = 'hA' + '_witness' * 10
    body += _parts(chosen, 5)
    witnesses = ('x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', 'x7', 'x8', 'x9', 'x10', 'x11', 'x12', 'x13', 'x14')
    body += tuple('exists ' + name for name in witnesses)
    body += ('split', 'exact hd_witness_witness_right', 'split', 'exact hd_witness_witness_left', 'split', 'exact hQ_witness_witness')
    for i in range(5):
        body += ('split', 'exact ' + chosen + '_right' * i + ('_left' if i < 4 else ''))
    body += _call('prime_field_polynomial_convolution_right_append_equivalent',
                  'p', *FACTORS, 'c', 'x', 'x1', 'pb', 'pc', 'N', 'x3', 'x4', 'x2',
                  'x5', 'x6', 'x7', 'x8', 'x9', 'x10', 'x11', 'x12', 'x13', 'x14')
    body += ('exact hp', 'exact hd_witness_witness_right', 'exact hd_witness_witness_left', 'exact hP', 'exact hQ_witness_witness')
    body += tuple('exact ' + chosen + '_right' * i + ('_left' if i < 4 else '') for i in range(5))
    outputs = ('db', 'dc', 'K', 'qb', 'qc', *ALIGNED_OUTPUTS)
    return spec(
        'prime_field_polynomial_convolution_right_append_exists',
        _contract(parameters, (_prime('p', 'append_exists_prime'), _lt('c', 'p', 'append_exists_scalar'), old),
                  'exists ' + ' '.join(outputs) + '. ' + _and(preserve, last, new, *_alignment_parts('append_exists_result_'), equal)),
        ('prime_nonzero', 'beta_prefix_extend', 'matrix_rank_bounded_prefix_extend',
         'matrix_rank_bounded_prefix_transport', 'polynomial_product_length_exists',
         'prime_field_polynomial_convolution_at_length_exists', 'prime_field_polynomial_shift_scale_aligned_sum_exists',
         'prime_field_polynomial_convolution_bounded', 'prime_field_polynomial_convolution_right_append_equivalent'), body,
        'From an actual old product and a canonical next coefficient, construct the appended right factor, its proper product, the shift and scalar outputs, both aligned paddings and the actual sum, then prove the formal recurrence. No output existence or polynomial identity is assumed.',
    )


def make_prime_field_polynomial_append_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_decomposition_row(spec), _decomposition_exists_row(spec), _coefficient_row(spec),
            _alignment_exists_row(spec), _recurrence_row(spec), _recurrence_exists_row(spec))


__all__ = ['make_prime_field_polynomial_append_candidate_theorems']
