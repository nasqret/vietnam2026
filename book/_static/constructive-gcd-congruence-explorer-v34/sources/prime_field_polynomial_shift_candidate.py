"""Actual trailing-zero shift of highest-degree-first polynomial prefixes.

Shift records only preservation of an existing decoded prefix and an actual
zero at the next position.  Its output length is the successor of the input
length.  This is multiplication by X, not harmless leading-zero padding.
Raw beta codes and all entries after the annotated prefix remain free.

The antidiagonal lemmas reuse genuine natural-sum and residue witnesses;
they do not introduce a polynomial-identity premise or an evaluation oracle.
These working-only dependency-curried candidates register no admission.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _le, _length, _pad, _term,
)
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _power_coefficient
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _shift(b: str, c: str, length: str, d: str, e: str, tag: str) -> str:
    return _and(_equal(b, c, d, e, length, tag + 'prefix'),
                _at(d, e, length, '0', tag + 'last'))


def prime_field_polynomial_shift_relation(
    b: str, c: str, length: str, d: str, e: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Actual trailing zero; output length S length, no field-law premise."""
    return _public(_shift, (b, c, length, d, e), tag=tag, variables=variables)


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result)
    )


def _constructor_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('b', 'c', 'L')
    extension = _and(_at('d', 'e', 'L', '0', 'shift_exists_last'),
                     _equal('b', 'c', 'd', 'e', 'L', 'shift_exists_prefix'))
    body += (f'have h : exists d e. {extension}',)
    body += _call('beta_prefix_extend', 'L', 'b', 'c', '0')
    body += ('cases h', 'cases h_witness', 'cases h_witness_witness',
             'exists x', 'exists x1', 'split', 'exact h_witness_witness_right',
             'exact h_witness_witness_left')
    exists = spec(
        'prime_field_polynomial_shift_exists',
        _contract(('b', 'c', 'L'), (), 'exists d e. ' + _shift('b', 'c', 'L', 'd', 'e', 'shift_exists')),
        ('beta_prefix_extend',), body,
        'Construct a genuine trailing-zero prefix by the original beta-prefix extension theorem, including an empty source.',
    )

    body = _intro('p', 'b', 'c', 'L', 'd', 'e', 'hp', 'hc', 'hs')
    body += ('cases hs',) + _intro('i', 'hi')
    body += (f"have ho : i=L \\/ ({_lt('i','L','shift_bound_old_index')})",)
    body += _call('finite_lt_succ_eq_or_lt', 'L', 'i') + ('exact hi', 'cases ho', 'exists 0', 'split')
    body += _rewrite_all('ho_left', _at('d', 'e', 'i', '0', 'shift_bound_last'), 'i')
    body += ('exact hs_right',) + _call('prime_field_zero_below_prime', 'p') + ('exact hp',)
    chosen = _and(_at('b', 'c', 'i', 'a', 'shift_bound_chosen'), _lt('a', 'p', 'shift_bound_value'))
    body += (f'have ha : exists a. {chosen}',) + _call('hc', 'i')
    body += ('exact ho_right', 'cases ha', 'cases ha_witness', 'exists x', 'split')
    body += _call('hs_left', 'i', 'x') + ('exact ho_right', 'exact ha_witness_left', 'exact ha_witness_right')
    bounded = spec(
        'prime_field_polynomial_shift_bounded',
        _contract(('p', 'b', 'c', 'L', 'd', 'e'),
                  (_prime('p', 'shift_bound_prime'), _coeff('p', 'b', 'c', 'L', 'shift_bound_source'),
                   _shift('b', 'c', 'L', 'd', 'e', 'shift_bound_relation')),
                  _coeff('p', 'd', 'e', 'S L', 'shift_bound_result')),
        ('finite_lt_succ_eq_or_lt', 'prime_field_zero_below_prime'), body,
        'A real trailing zero preserves canonical field coefficients; characteristic two uses natural zero and one, not signed codes.',
    )

    body = _intro('b', 'c', 'L', 'd', 'e', 'f', 'g', 'hd', 'hf')
    body += ('cases hd', 'cases hf') + _intro('i', 'a', 'hi', 'ha')
    body += (f"have ho : i=L \\/ ({_lt('i','L','shift_unique_old_index')})",)
    body += _call('finite_lt_succ_eq_or_lt', 'L', 'i') + ('exact hi', 'cases ho')
    body += _rewrite_all('ho_left', _at('d', 'e', 'i', 'a', 'shift_unique_actual_last'), 'i', 'ha')
    body += ('have heq : a=0',) + _call('beta_at_unique', 'd', 'e', 'L', 'a', '0')
    body += ('exact ha', 'exact hd_right')
    body += _rewrite_all('ho_left', _at('f', 'g', 'i', 'a', 'shift_unique_target_last'), 'i')
    body += _rewrite_all('heq', _at('f', 'g', 'L', 'a', 'shift_unique_target_zero'), 'a')
    body += ('exact hf_right', f"have hx : exists x. ({_at('b','c','i','x','shift_unique_source_value')})")
    body += _call('beta_at_exists', 'b', 'c', 'i') + ('cases hx', 'have heq : a=x')
    body += _call('beta_at_unique', 'd', 'e', 'i', 'a', 'x') + ('exact ha',)
    body += _call('hd_left', 'i', 'x') + ('exact ho_right', 'exact hx_witness')
    body += _rewrite_all('heq', _at('f', 'g', 'i', 'a', 'shift_unique_prefix_rewrite'), 'a')
    body += _call('hf_left', 'i', 'x') + ('exact ho_right', 'exact hx_witness')
    functional = spec(
        'prime_field_polynomial_shift_functional',
        _contract(('b', 'c', 'L', 'd', 'e', 'f', 'g'),
                  (_shift('b', 'c', 'L', 'd', 'e', 'shift_unique_first'),
                   _shift('b', 'c', 'L', 'f', 'g', 'shift_unique_second')),
                  _equal('d', 'e', 'f', 'g', 'S L', 'shift_unique_result')),
        ('finite_lt_succ_eq_or_lt', 'beta_at_unique', 'beta_at_exists'), body,
        'Two actual shifts agree on their successor-length decoded prefix; neither raw code nor any later entry is identified.',
    )

    body = _intro('b', 'c', 'L', 'd', 'e', 'hz', 'hs') + ('cases hs',) + _intro('i', 'hi')
    body += (f"have ho : i=L \\/ ({_lt('i','L','shift_zero_old_index')})",)
    body += _call('finite_lt_succ_eq_or_lt', 'L', 'i') + ('exact hi', 'cases ho')
    body += _rewrite_all('ho_left', _at('d', 'e', 'i', '0', 'shift_zero_last'), 'i')
    body += ('exact hs_right',) + _call('hs_left', 'i', '0') + ('exact ho_right',)
    body += _call('hz', 'i') + ('exact ho_right',)
    zero = spec(
        'prime_field_polynomial_shift_zero_prefix',
        _contract(('b', 'c', 'L', 'd', 'e'),
                  (_repeat('b', 'c', '0', 'L', 'shift_zero_source'),
                   _shift('b', 'c', 'L', 'd', 'e', 'shift_zero_relation')),
                  _repeat('d', 'e', '0', 'S L', 'shift_zero_result')),
        ('finite_lt_succ_eq_or_lt',), body,
        'The actual shift of an all-zero prefix is again all zero, including the length-one shift of an empty input.',
    )
    return exists, bounded, functional, zero


def _zero_extension_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('b', 'c', 'L', 'd', 'e', 'i', 'a')
    body = _intro(*parameters, 'hs', 'ha') + ('cases hs', 'cases ha', 'cases ha_left', 'left', 'split')
    body += _call('le_succ', 'S i', 'L') + ('exact ha_left_left',)
    body += _call('hs_left', 'i', 'a') + ('exact ha_left_left', 'exact ha_left_right', 'cases ha_right')
    body += (f"have ho : L=i \\/ ({_lt('L','i','shift_pad_outside_order')})",)
    body += _call('le_eq_or_lt', 'L', 'i') + ('exact ha_right_left', 'cases ho',
                                             'have hii : i=L', 'symm', 'exact ho_left', 'left', 'split')
    body += _rewrite_all('hii', _lt('i', 'S L', 'shift_pad_last_bound'), 'i')
    body += _call('le_refl', 'S L')
    body += _rewrite_all('hii', _at('d', 'e', 'i', 'a', 'shift_pad_last_entry'), 'i')
    body += _rewrite_all('ha_right_right', _at('d', 'e', 'L', 'a', 'shift_pad_last_zero'), 'a')
    body += ('exact hs_right', 'right', 'split', 'exact ho_right', 'exact ha_right_right')
    forward = spec(
        'polynomial_zero_extended_shift_forward',
        _contract(parameters, (_shift('b', 'c', 'L', 'd', 'e', 'shift_pad_relation'),
                               _pad('b', 'c', 'L', 'i', 'a', 'shift_pad_source')),
                  _pad('d', 'e', 'S L', 'i', 'a', 'shift_pad_target')),
        ('le_succ', 'le_eq_or_lt', 'le_refl'), body,
        'Trailing-zero extension leaves each actual zero-extended array value unchanged, at every natural index.',
    )

    body = _intro(*parameters, 'hs', 'ha')
    body += (f"have hx : exists x. ({_pad('b','c','L','i','x','shift_pad_reverse_chosen')})",)
    body += _call('polynomial_zero_extended_entry_exists', 'b', 'c', 'L', 'i') + ('cases hx', 'have heq : a=x')
    body += _call('polynomial_zero_extended_entry_functional', 'd', 'e', 'S L', 'i', 'a', 'x')
    body += ('exact ha',) + _call('polynomial_zero_extended_shift_forward', 'b', 'c', 'L', 'd', 'e', 'i', 'x')
    body += ('exact hs', 'exact hx_witness')
    body += _rewrite_all('heq', _pad('b', 'c', 'L', 'i', 'a', 'shift_pad_reverse_rewrite'), 'a')
    body += ('exact hx_witness',)
    reverse = spec(
        'polynomial_zero_extended_shift_reverse',
        _contract(parameters, (_shift('b', 'c', 'L', 'd', 'e', 'shift_pad_reverse_relation'),
                               _pad('d', 'e', 'S L', 'i', 'a', 'shift_pad_reverse_source')),
                  _pad('b', 'c', 'L', 'i', 'a', 'shift_pad_reverse_result')),
        ('polynomial_zero_extended_entry_exists', 'polynomial_zero_extended_entry_functional',
         'polynomial_zero_extended_shift_forward'), body,
        'Conversely every zero-extended value of an actual shift is the original zero-extended value; this is not formal polynomial equality.',
    )
    return forward, reverse


FACTORS = ('ab', 'ac', 'L', 'bb', 'bc', 'M')
SHIFTED_FACTORS = ('ab', 'ac', 'L', 'BB', 'BC', 'S M')


def _term_row(spec: Callable[..., Any]) -> Any:
    parameters = (*FACTORS, 'BB', 'BC', 'i', 'j', 't')
    old = _term(*FACTORS, 'i', 'j', 't', 'shift_term_old')
    new = _term(*SHIFTED_FACTORS, 'i', 'j', 't', 'shift_term_new')
    body = _intro(*parameters, 'hs') + ('split',)
    for direction in ('forward', 'reverse'):
        body += ('intro ht',) + tuple('cases ht' + '_witness' * i for i in range(3))
        body += _parts('ht_witness_witness_witness', 4)
        body += ('exists x', 'exists x1', 'exists x2', 'split', 'exact ht_witness_witness_witness_left',
                 'split', 'exact ht_witness_witness_witness_right_left', 'split')
        body += _call('polynomial_zero_extended_shift_' + direction, 'bb', 'bc', 'M', 'BB', 'BC', 'x', 'x2')
        body += ('exact hs', 'exact ht_witness_witness_witness_right_right_left',
                 'exact ht_witness_witness_witness_right_right_right')
    return spec(
        'polynomial_diagonal_term_shift_right_iff',
        _contract(parameters, (_shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_term_relation'),),
                  _and(f'({old}) -> ({new})', f'({new}) -> ({old})')),
        ('polynomial_zero_extended_shift_forward', 'polynomial_zero_extended_shift_reverse'), body,
        'An actual trailing-zero shift of the right factor preserves exactly the same antidiagonal term witnesses in both directions.',
    )


def _coefficient_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *FACTORS, 'BB', 'BC', 'i', 'r')
    old = _coefficient('p', *FACTORS, 'i', 'r', 'shift_coefficient_old')
    new = _coefficient('p', *SHIFTED_FACTORS, 'i', 'r', 'shift_coefficient_new')
    body = _intro(*parameters, 'hs') + ('split',)
    for source, direction in ((FACTORS, 'left'), (SHIFTED_FACTORS, 'right')):
        body += ('intro hc',) + tuple('cases hc' + '_witness' * i for i in range(3))
        body += _parts('hc_witness_witness_witness', 3)
        body += ('exists x', 'exists x1', 'exists x2', 'split') + _intro('j', 'hj')
        chosen = _and(_at('x', 'x1', 'j', 't', 'shift_coefficient_chosen_entry_' + direction),
                      _term(*source, 'i', 'j', 't', 'shift_coefficient_chosen_term_' + direction))
        body += (f'have ht : exists t. {chosen}',) + _call('hc_witness_witness_witness_left', 'j')
        body += ('exact hj', 'cases ht', 'cases ht_witness', 'exists x3', 'split', 'exact ht_witness_left')
        old_term = _term(*FACTORS, 'i', 'j', 'x3', 'shift_coefficient_old_term_' + direction)
        new_term = _term(*SHIFTED_FACTORS, 'i', 'j', 'x3', 'shift_coefficient_new_term_' + direction)
        body += ('have htiff : ' + _and(f'({old_term}) -> ({new_term})', f'({new_term}) -> ({old_term})'),)
        body += _call('polynomial_diagonal_term_shift_right_iff', *FACTORS, 'BB', 'BC', 'i', 'j', 'x3')
        body += ('exact hs', 'cases htiff') + _call('htiff_' + direction)
        body += ('exact ht_witness_right', 'split', 'exact hc_witness_witness_witness_right_left',
                 'exact hc_witness_witness_witness_right_right')
    return spec(
        'prime_field_convolution_coefficient_shift_right_iff',
        _contract(parameters, (_shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_coefficient_relation'),),
                  _and(f'({old}) -> ({new})', f'({new}) -> ({old})')),
        ('polynomial_diagonal_term_shift_right_iff',), body,
        'Every actual convolution coefficient is preserved at every index, with the identical natural sum and residue witnesses; no primality is needed.',
    )


def _product_length_row(spec: Callable[..., Any]) -> Any:
    body = _intro('L', 'M', 'N', 'K', 'hold', 'hL', 'hM', 'hnew')
    body += ('cases hold', 'cases hold_left', 'cases hold_left_left', 'exfalso', 'apply hL',
             'exact hold_left_left_left', 'exfalso', 'apply hM', 'exact hold_left_left_right')
    body += _parts('hold_right', 3)
    body += ('cases hnew', 'cases hnew_left', 'cases hnew_left_left', 'exfalso', 'apply hL',
             'exact hnew_left_left_left', 'exfalso')
    body += _call('succ_ne_zero', 'M') + ('exact hnew_left_left_right',)
    body += _parts('hnew_right', 3)
    body += ('apply PA2', 'trans L+S M', 'symm', 'exact hnew_right_right_right',
             'trans S (L+M)', 'apply PA4', 'congr', 'exact hold_right_right_right')
    return spec(
        'polynomial_product_length_shift_right_nonempty',
        _contract(('L', 'M', 'N', 'K'),
                  (_length('L', 'M', 'N', 'shift_length_old'), '~(L=0)', '~(M=0)',
                   _length('L', 'S M', 'K', 'shift_length_new')), 'K=S N'),
        ('succ_ne_zero',), body,
        'For two nonempty factors, shifting the right factor raises the proper product length by exactly one; empty factors are explicitly excluded.',
    )


PRODUCT_PARAMETERS = ('p', *FACTORS, 'cb', 'cc', 'N', 'BB', 'BC', 'db', 'dc', 'K')


def _products(tag: str) -> tuple[str, str]:
    return (_convolution('p', *FACTORS, 'cb', 'cc', 'N', tag + 'old'),
            _convolution('p', *SHIFTED_FACTORS, 'db', 'dc', 'K', tag + 'new'))


def _coefficient_transport_script(index: str, value: str, direction: str, source: str, tag: str) -> tuple[str, ...]:
    old = _coefficient('p', *FACTORS, index, value, tag + 'old')
    new = _coefficient('p', *SHIFTED_FACTORS, index, value, tag + 'new')
    return ('have hiff : ' + _and(f'({old}) -> ({new})', f'({new}) -> ({old})'),) \
        + _call('prime_field_convolution_coefficient_shift_right_iff', *PRODUCT_PARAMETERS[:7], 'BB', 'BC', index, value) \
        + ('exact hs', 'cases hiff') + _call('hiff_' + direction) + ('exact ' + source,)


def _nonempty_product_row(spec: Callable[..., Any]) -> Any:
    old, new = _products('shift_product_')
    body = _intro(*PRODUCT_PARAMETERS, 'hp', 'hL', 'hM', 'hs', 'hc', 'hd')
    body += ('have hwhole : ' + old, 'exact hc') + _parts('hc', 4) + _parts('hd', 4)
    body += ('have hk : K=S N',) + _call('polynomial_product_length_shift_right_nonempty', 'L', 'M', 'N', 'K')
    body += ('exact hc_right_right_left', 'exact hL', 'exact hM', 'exact hd_right_right_left',
             'split', 'exact hk', 'split') + _intro('i', 'a', 'hi', 'ha')
    body += (f"have hca : {_coefficient('p',*FACTORS,'i','a','shift_product_source_coefficient')}",)
    body += _call('prime_field_convolution_prefix_entry', 'p', *FACTORS, 'cb', 'cc', 'N', 'i', 'a')
    body += ('exact hc_right_right_right', 'exact hi', 'exact ha')
    body += (f"have hda : {_coefficient('p',*SHIFTED_FACTORS,'i','a','shift_product_transported_coefficient')}",)
    body += _coefficient_transport_script('i', 'a', 'left', 'hca', 'shift_product_transport_')
    chosen = _and(_at('db', 'dc', 'i', 'r', 'shift_product_chosen_entry'),
                  _coefficient('p', *SHIFTED_FACTORS, 'i', 'r', 'shift_product_chosen_coefficient'))
    body += (f'have hv : exists r. {chosen}',) + _call('hd_right_right_right', 'i')
    body += _rewrite_all('hk', _lt('i', 'K', 'shift_product_chosen_bound'), 'K')
    body += _call('le_succ', 'S i', 'N') + ('exact hi', 'cases hv', 'cases hv_witness', 'have heq : a=x')
    body += _call('prime_field_convolution_coefficient_functional', 'p', *SHIFTED_FACTORS, 'i', 'a', 'x')
    body += ('exact hda', 'exact hv_witness_right')
    body += _rewrite_all('heq', _at('db', 'dc', 'i', 'a', 'shift_product_recode_entry'), 'a')
    body += ('exact hv_witness_left',)

    last = _and(_at('db', 'dc', 'N', 'r', 'shift_product_last_entry'),
                _coefficient('p', *SHIFTED_FACTORS, 'N', 'r', 'shift_product_last_coefficient'))
    body += (f'have hv : exists r. {last}',) + _call('hd_right_right_right', 'N')
    body += _rewrite_all('hk', _lt('N', 'K', 'shift_product_last_bound'), 'K')
    body += _call('le_refl', 'S N') + ('cases hv', 'cases hv_witness')
    body += (f"have hco : {_coefficient('p',*FACTORS,'N','x','shift_product_exterior_old')}",)
    body += _coefficient_transport_script('N', 'x', 'right', 'hv_witness_right', 'shift_product_last_transport_')
    body += ('have hz : x=0',)
    body += _call('prime_field_polynomial_convolution_outside_zero', 'p', *FACTORS, 'cb', 'cc', 'N', 'N', 'x')
    body += ('exact hp', 'exact hwhole') + _call('le_refl', 'N') + ('exact hco',)
    body += _rewrite_all('hz', _at('db', 'dc', 'N', 'x', 'shift_product_actual_last_zero'), 'x', 'hv_witness_left')
    body += ('exact hv_witness_left',)
    return spec(
        'prime_field_polynomial_convolution_shift_right_nonempty',
        _contract(PRODUCT_PARAMETERS,
                  ('~(p=0)', '~(L=0)', '~(M=0)', _shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_product_factor'), old, new),
                  _and('K=S N', _shift('cb', 'cc', 'N', 'db', 'dc', 'shift_product_result'))),
        ('polynomial_product_length_shift_right_nonempty', 'prime_field_convolution_prefix_entry',
         'prime_field_convolution_coefficient_shift_right_iff', 'le_succ',
         'prime_field_convolution_coefficient_functional', 'le_refl', 'prime_field_polynomial_convolution_outside_zero'),
        body,
        'For actual nonempty factors, the shifted product is exactly a trailing-zero extension of the original decoded product, at its proved successor length.',
    )


def _empty_product_row(spec: Callable[..., Any]) -> Any:
    old, new = _products('shift_empty_')
    body = _intro(*PRODUCT_PARAMETERS, 'hp', 'hs', 'hc', 'hd', 'hempty') + ('cases hempty',)
    for side, equality in (('left', 'hempty_left'), ('right', 'hempty_right')):
        code, scale, length = ('ab', 'ac', 'L') if side == 'left' else ('bb', 'bc', 'M')
        body += (f"have hz : {_repeat(code,scale,'0',length,'shift_empty_source_'+side)}",) + _intro('i', 'hi')
        body += _rewrite_all(equality, _lt('i', length, 'shift_empty_impossible_' + side), length, 'hi')
        body += ('exfalso',) + _call('lt_not_le', 'i', '0') + ('exact hi',) + _call('zero_le', 'i')
        body += ('split',) + _call('prime_field_polynomial_convolution_zero_' + side,
                                  'p', *FACTORS, 'cb', 'cc', 'N')
        body += ('exact hp', 'exact hz', 'exact hc')
        body += _call('prime_field_polynomial_convolution_zero_' + side,
                      'p', *SHIFTED_FACTORS, 'db', 'dc', 'K') + ('exact hp',)
        if side == 'right':
            body += _call('prime_field_polynomial_shift_zero_prefix', 'bb', 'bc', 'M', 'BB', 'BC')
            body += ('exact hz', 'exact hs')
        else:
            body += ('exact hz',)
        body += ('exact hd',)
    return spec(
        'prime_field_polynomial_convolution_shift_right_empty',
        _contract(PRODUCT_PARAMETERS,
                  ('~(p=0)', _shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_empty_factor'), old, new, 'L=0 \\/ M=0'),
                  _and(_repeat('cb', 'cc', '0', 'N', 'shift_empty_old_zero'),
                       _repeat('db', 'dc', '0', 'K', 'shift_empty_new_zero'))),
        ('lt_not_le', 'zero_le', 'prime_field_polynomial_convolution_zero_left',
         'prime_field_polynomial_convolution_zero_right', 'prime_field_polynomial_shift_zero_prefix'), body,
        'If either original factor is empty, both actual products are zero prefixes; no false successor-length equation is imposed.',
    )


def _empty_equivalence_script(empty_proof: tuple[str, ...], tag: str) -> tuple[str, ...]:
    zeros = _and(_repeat('cb', 'cc', '0', 'N', tag + 'old_zero'),
                 _repeat('db', 'dc', '0', 'K', tag + 'new_zero'))
    body = ('have hz : ' + zeros,)
    body += _call('prime_field_polynomial_convolution_shift_right_empty', *PRODUCT_PARAMETERS)
    body += ('exact hp', 'exact hs', 'exact hc', 'exact hd') + empty_proof + ('cases hz',)
    body += (f"have hezero : {_repeat('eb','ec','0','S N',tag+'shifted_zero')}",)
    body += _call('prime_field_polynomial_shift_zero_prefix', 'cb', 'cc', 'N', 'eb', 'ec')
    body += ('exact hz_left', 'exact he')
    body += _call('prime_field_polynomial_equivalent_transitive', 'db', 'dc', 'K', '0', '0', '0', 'eb', 'ec', 'S N')
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty', 'db', 'dc', 'K') + ('exact hz_right',)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'eb', 'ec', 'S N', '0', '0', '0')
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty', 'eb', 'ec', 'S N') + ('exact hezero',)
    return body


def _equivalent_product_row(spec: Callable[..., Any]) -> Any:
    parameters = (*PRODUCT_PARAMETERS, 'eb', 'ec')
    old, new = _products('shift_equivalent_')
    conclusion = _equivalent('db', 'dc', 'K', 'eb', 'ec', 'S N', 'shift_equivalent_result')
    body = _intro(*parameters, 'hp', 'hs', 'hc', 'hd', 'he')
    body += ('have hL : L=0 \\/ ~(L=0)',) + _call('eq_decidable', 'L', '0') + ('cases hL',)
    body += _empty_equivalence_script(('left', 'exact hL_left'), 'shift_equivalent_empty_left_')
    body += ('have hM : M=0 \\/ ~(M=0)',) + _call('eq_decidable', 'M', '0') + ('cases hM',)
    body += _empty_equivalence_script(('right', 'exact hM_left'), 'shift_equivalent_empty_right_')
    data = _and('K=S N', _shift('cb', 'cc', 'N', 'db', 'dc', 'shift_equivalent_nonempty_data'))
    body += ('have hdata : ' + data,)
    body += _call('prime_field_polynomial_convolution_shift_right_nonempty', *PRODUCT_PARAMETERS)
    body += ('exact hp', 'exact hL_right', 'exact hM_right', 'exact hs', 'exact hc', 'exact hd', 'cases hdata')
    body += _rewrite_all('hdata_left', conclusion, 'K')
    body += _call('prime_field_polynomial_equal_implies_equivalent', 'db', 'dc', 'eb', 'ec', 'S N')
    body += _call('prime_field_polynomial_shift_functional', 'cb', 'cc', 'N', 'db', 'dc', 'eb', 'ec')
    body += ('exact hdata_right', 'exact he')
    return spec(
        'prime_field_polynomial_convolution_shift_right_equivalent',
        _contract(parameters, ('~(p=0)', _shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_equivalent_factor'),
                               old, new, _shift('cb', 'cc', 'N', 'eb', 'ec', 'shift_equivalent_comparison')), conclusion),
        ('eq_decidable', 'prime_field_polynomial_convolution_shift_right_empty',
         'prime_field_polynomial_shift_zero_prefix', 'prime_field_polynomial_equivalent_transitive',
         'prime_field_polynomial_zero_prefix_equivalent_empty', 'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_convolution_shift_right_nonempty',
         'prime_field_polynomial_equal_implies_equivalent', 'prime_field_polynomial_shift_functional'), body,
        'At every nonzero modulus, the actual product with a shifted right factor is formally coefficient-equivalent to every actual shift of the original product, including both empty-factor cases.',
    )


def _product_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *FACTORS, 'cb', 'cc', 'N', 'BB', 'BC')
    old, new = _products('shift_exists_product_')
    shifted_product = _shift('cb', 'cc', 'N', 'eb', 'ec', 'shift_exists_product_shift')
    equivalence = _equivalent('db', 'dc', 'K', 'eb', 'ec', 'S N', 'shift_exists_product_equivalence')
    body = _intro(*parameters, 'hprime', 'hs', 'hc')
    body += ('have hcopy : ' + old, 'exact hc') + _parts('hcopy', 4)
    body += ('have hp : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p') + ('exact hprime', 'exact hz')
    body += (f"have hlength : exists K. ({_length('L','S M','K','shift_exists_product_length')})",)
    body += _call('polynomial_product_length_exists', 'L', 'S M') + ('cases hlength',)
    chosen_product = _convolution('p', *SHIFTED_FACTORS, 'd', 'e', 'x', 'shift_exists_product_chosen')
    body += ('have hv : exists d e. ' + chosen_product,)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', *SHIFTED_FACTORS, 'x')
    body += ('exact hp', 'exact hcopy_left')
    body += _call('prime_field_polynomial_shift_bounded', 'p', 'bb', 'bc', 'M', 'BB', 'BC')
    body += ('exact hprime', 'exact hcopy_right_left', 'exact hs', 'exact hlength_witness',
             'cases hv', 'cases hv_witness')
    body += (f"have he : exists e f. ({_shift('cb','cc','N','e','f','shift_exists_product_actual_comparison')})",)
    body += _call('prime_field_polynomial_shift_exists', 'cb', 'cc', 'N') + ('cases he', 'cases he_witness',
        'exists x', 'exists x1', 'exists x2', 'exists x3', 'exists x4',
        'split', 'exact hv_witness_witness', 'split', 'exact he_witness_witness')
    body += _call('prime_field_polynomial_convolution_shift_right_equivalent',
                  'p', *FACTORS, 'cb', 'cc', 'N', 'BB', 'BC', 'x1', 'x2', 'x', 'x3', 'x4')
    body += ('exact hp', 'exact hs', 'exact hc', 'exact hv_witness_witness', 'exact he_witness_witness')
    return spec(
        'prime_field_polynomial_convolution_shift_right_exists',
        _contract(parameters, (_prime('p', 'shift_exists_product_prime'),
                               _shift('bb', 'bc', 'M', 'BB', 'BC', 'shift_exists_product_factor'), old),
                  'exists K db dc eb ec. ' + _and(new, shifted_product, equivalence)),
        ('prime_nonzero', 'polynomial_product_length_exists', 'prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_shift_bounded', 'prime_field_polynomial_shift_exists',
         'prime_field_polynomial_convolution_shift_right_equivalent'), body,
        'Given a genuine shifted factor, construct its proper-length product and a genuine shift of the original output, then derive their formal equivalence without any output witness premise.',
    )


def _power_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    zero = spec(
        'prime_field_polynomial_shift_power_zero',
        _contract(('b', 'c', 'L', 'd', 'e'), (_shift('b', 'c', 'L', 'd', 'e', 'shift_power_zero_relation'),),
                  _power_coefficient('d', 'e', 'S L', '0', '0', 'shift_power_zero_result')),
        (), _intro('b', 'c', 'L', 'd', 'e', 'hs') + ('cases hs', 'left', 'exists L', 'split', 'simp', 'exact hs_right'),
        'The actual constant coefficient of a trailing-zero shift is zero, even when the original representation is empty.',
    )
    body = _intro('b', 'c', 'L', 'd', 'e', 'k', 'a', 'hs', 'ha')
    body += ('cases hs', 'cases ha', 'cases ha_left', 'cases ha_left_witness', 'left', 'exists x', 'split',
             'trans S (x+S k)', 'apply PA4', 'congr', 'exact ha_left_witness_left')
    body += _call('hs_left', 'x', 'a')
    body += _call('prime_field_polynomial_power_index_bound', 'x', 'k', 'L')
    body += ('exact ha_left_witness_left', 'exact ha_left_witness_right', 'cases ha_right', 'right', 'split')
    body += _call('succ_le_succ', 'L', 'k') + ('exact ha_right_left', 'exact ha_right_right')
    successor = spec(
        'prime_field_polynomial_shift_power_successor',
        _contract(('b', 'c', 'L', 'd', 'e', 'k', 'a'),
                  (_shift('b', 'c', 'L', 'd', 'e', 'shift_power_successor_relation'),
                   _power_coefficient('b', 'c', 'L', 'k', 'a', 'shift_power_successor_source')),
                  _power_coefficient('d', 'e', 'S L', 'S k', 'a', 'shift_power_successor_result')),
        ('prime_field_polynomial_power_index_bound', 'succ_le_succ'), body,
        'Each actual coefficient at power k becomes the same coefficient at power S k; together with constant zero this is genuine multiplication by X, not evaluation equality.',
    )
    return zero, successor


def make_prime_field_polynomial_shift_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (*_constructor_rows(spec), *_zero_extension_rows(spec), _term_row(spec), _coefficient_row(spec),
            _product_length_row(spec), _nonempty_product_row(spec), _empty_product_row(spec),
            _equivalent_product_row(spec), _product_exists_row(spec), *_power_rows(spec))


__all__ = ['prime_field_polynomial_shift_relation', 'make_prime_field_polynomial_shift_candidate_theorems']
