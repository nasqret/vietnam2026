"""Decoded-value uniqueness of the actual triangular division execution.

The quotient recursion, ambient product, subtraction, and trim are the frozen
execution graphs, not an arbitrary assumed polynomial identity.  The results
below identify representation lengths and bounded decoded coefficient values;
they never identify beta code numbers or constrain entries past those lengths.
Conditional functionality does not require primality.  Constructing an
execution still uses the existing prime-field/nonzero-divisor hypotheses.

This module does not assert uniqueness of arbitrary quotient/remainder pairs
with unrelated representation lengths merely satisfying a formal identity.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _add, _and, _call, _intro, _inv, _lt, _mul, _part, _parts, _prime,
)
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal
from peano_lab.library.prime_field_polynomial_convolution_candidate import _coefficient, _le, _prefix
from peano_lab.library.prime_field_polynomial_degree_candidate import _degree
from peano_lab.library.prime_field_polynomial_division_candidate import (
    _division_execution, _quotient_data, _quotient_length, _quotient_prefix,
    _quotient_step, _residual_data,
)
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _step_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    base = ('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'qb', 'qc')
    params = (*base, 'i', 'q', 'r')
    body = _intro(*params, 'hfirst', 'hsecond')
    for name in ('hfirst', 'hsecond'):
        body += tuple('cases ' + name + '_witness' * index for index in range(3))
        body += _parts(name + '_witness' * 3, 4)
    first, second = 'hfirst' + '_witness' * 3, 'hsecond' + '_witness' * 3
    body += ('have hinput : x=x3',) + _call('beta_at_unique', 'ab', 'ac', 'i', 'x', 'x3')
    body += ('exact ' + _part(first, 4, 0), 'exact ' + _part(second, 4, 0), 'have hprevious : x1=x4')
    body += _call('prime_field_convolution_coefficient_functional', 'p', 'qb', 'qc', 'i', 'bb', 'bc', 'M', 'i', 'x1', 'x4')
    body += ('exact ' + _part(first, 4, 1), 'exact ' + _part(second, 4, 1))
    body += _rewrite_all('hinput', _add('p', 'x1', 'x2', 'x', 'step_unique_input'), 'x', _part(first, 4, 2))
    body += _rewrite_all('hprevious', _add('p', 'x1', 'x2', 'x3', 'step_unique_previous'), 'x1', _part(first, 4, 2))
    body += ('have hdifference : x2=x5',) + _call('prime_field_add_cancel_left', 'p', 'x4', 'x2', 'x5', 'x3')
    body += ('exact ' + _part(first, 4, 2), 'exact ' + _part(second, 4, 2))
    body += _rewrite_all('hdifference', _mul('p', 'k', 'x2', 'q', 'step_unique_product'), 'x2', _part(first, 4, 3))
    body += _call('prime_field_multiply_functional', 'p', 'k', 'x5', 'q', 'r')
    body += ('exact ' + _part(first, 4, 3), 'exact ' + _part(second, 4, 3))
    same = spec(
        'prime_field_polynomial_quotient_step_functional',
        f"forall {' '.join(params)}. ({_quotient_step(*base, 'i', 'q', 'step_unique_first')}) -> "
        f"({_quotient_step(*base, 'i', 'r', 'step_unique_second')}) -> q=r",
        ('beta_at_unique', 'prime_field_convolution_coefficient_functional',
         'prime_field_add_cancel_left', 'prime_field_multiply_functional'), body,
        'An actual triangular execution step has one decoded output, by beta and convolution functionality, additive cancellation, and product functionality.',
    )
    params = (*base, 'QB', 'QC', 'i', 'q', 'r')
    body = _intro(*params, 'hequal', 'hfirst', 'hsecond')
    body += _call('prime_field_polynomial_quotient_step_functional', 'p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', 'i', 'q', 'r')
    body += _call('prime_field_polynomial_quotient_step_recode', *base, 'QB', 'QC', 'i', 'q')
    body += ('exact hequal', 'exact hfirst', 'exact hsecond')
    recoded = spec(
        'prime_field_polynomial_quotient_step_prefix_functional',
        f"forall {' '.join(params)}. ({_equal('qb', 'qc', 'QB', 'QC', 'i', 'step_unique_prefix')}) -> "
        f"({_quotient_step(*base, 'i', 'q', 'step_unique_old')}) -> "
        f"({_quotient_step('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', 'i', 'r', 'step_unique_new')}) -> q=r",
        ('prime_field_polynomial_quotient_step_functional', 'prime_field_polynomial_quotient_step_recode'), body,
        'Two genuine steps with equal previously computed coefficients agree, even when their beta encodings and unused entries differ.',
    )
    return same, recoded


def _prefix_functional_row(spec: Callable[..., Any]) -> Any:
    params = ('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'qb', 'qc', 'QB', 'QC')
    old = lambda n, tag: _quotient_prefix('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'qb', 'qc', n, tag)
    new = lambda n, tag: _quotient_prefix('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', n, tag)
    body = _intro(*params, 'N') + ('induction N',) + _intro('hfirst', 'hsecond', 'i', 'a', 'hindex', 'hvalue')
    body += ('exfalso',) + _call('lt_not_le', 'i', '0') + ('exact hindex',) + _call('zero_le', 'i')
    body += _intro('hfirst', 'hsecond')
    body += (f"have hequal : {_equal('qb', 'qc', 'QB', 'QC', 'N', 'prefix_unique_induction')}",) + _call('IH')
    for b, c, hypothesis in (('qb', 'qc', 'hfirst'), ('QB', 'QC', 'hsecond')):
        body += _call('prime_field_polynomial_quotient_prefix_restrict', 'p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', b, c, 'S N', 'N')
        body += _call('le_succ', 'N', 'N') + _call('le_refl', 'N') + ('exact ' + hypothesis,)
    body += _intro('i', 'a', 'hindex', 'hvalue')
    body += (f"have hcase : i=N \\/ ({_lt('i', 'N', 'prefix_unique_earlier')})",)
    body += _call('finite_lt_succ_eq_or_lt', 'N', 'i') + ('exact hindex', 'cases hcase')
    body += _rewrite_all('hcase_left', _at('qb', 'qc', 'i', 'a', 'prefix_unique_source_last'), 'i', 'hvalue')
    body += _rewrite_all('hcase_left', _at('QB', 'QC', 'i', 'a', 'prefix_unique_target_last'), 'i')
    point = _and(_at('QB', 'QC', 'N', 'r', 'prefix_unique_other_value'),
                 _quotient_step('p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'QB', 'QC', 'N', 'r', 'prefix_unique_other_step'))
    body += (f'have hchosen : exists r. ({point})',) + _call('hsecond', 'N') + _call('le_refl', 'S N')
    body += ('cases hchosen', 'cases hchosen_witness', 'have hlast : a=x')
    body += _call('prime_field_polynomial_quotient_step_prefix_functional', *params, 'N', 'a', 'x') + ('exact hequal',)
    body += _call('prime_field_polynomial_quotient_prefix_entry', 'p', 'k', 'ab', 'ac', 'bb', 'bc', 'M', 'qb', 'qc', 'S N', 'N', 'a')
    body += ('exact hfirst',) + _call('le_refl', 'S N') + ('exact hvalue', 'exact hchosen_witness_right')
    body += _rewrite_all('hlast', _at('QB', 'QC', 'N', 'a', 'prefix_unique_last_rewrite'), 'a') + ('exact hchosen_witness_left',)
    body += _call('hequal', 'i', 'a') + ('exact hcase_right', 'exact hvalue')
    return spec(
        'prime_field_polynomial_quotient_prefix_functional',
        f"forall {' '.join(params)} N. ({old('N', 'prefix_unique_first')}) -> ({new('N', 'prefix_unique_second')}) -> "
        f"({_equal('qb', 'qc', 'QB', 'QC', 'N', 'prefix_unique_result')})",
        ('lt_not_le', 'zero_le', 'prime_field_polynomial_quotient_prefix_restrict', 'le_succ', 'le_refl',
         'finite_lt_succ_eq_or_lt', 'prime_field_polynomial_quotient_step_prefix_functional',
         'prime_field_polynomial_quotient_prefix_entry'), body,
        'Finite induction proves coefficientwise uniqueness of the actual quotient recursion, with no claim about beta code identity or unused entries.',
    )


def _length_functional_row(spec: Callable[..., Any]) -> Any:
    body = _intro('L', 'd', 'q', 'Q', 'hfirst', 'hsecond') + ('cases hfirst', 'cases hfirst_left', 'cases hsecond', 'cases hsecond_left')
    body += ('trans 0', 'exact hfirst_left_left', 'symm', 'exact hsecond_left_left', 'cases hsecond_right', 'exfalso')
    body += _call('hsecond_right_left') + _call('le_zero', 'Q') + _call('add_le_cancel_right', 'Q', '0', 'd')
    body += ('have hzero : 0+d=d',) + _call('zero_add', 'd')
    body += ('rewrite hzero', 'rewrite hsecond_right_right', 'exact hfirst_left_right', 'cases hfirst_right', 'cases hsecond', 'cases hsecond_left', 'exfalso')
    body += _call('hfirst_right_left') + _call('le_zero', 'q') + _call('add_le_cancel_right', 'q', '0', 'd')
    body += ('have hzero : 0+d=d',) + _call('zero_add', 'd')
    body += ('rewrite hzero', 'rewrite hfirst_right_right', 'exact hsecond_left_right', 'cases hsecond_right')
    body += _call('add_right_cancel', 'q', 'Q', 'd') + ('trans L', 'exact hfirst_right_right', 'symm', 'exact hsecond_right_right')
    return spec(
        'polynomial_quotient_length_functional',
        f"forall L d q Q. ({_quotient_length('L', 'd', 'q', 'length_unique_first')}) -> "
        f"({_quotient_length('L', 'd', 'Q', 'length_unique_second')}) -> q=Q",
        ('le_zero', 'add_le_cancel_right', 'zero_add', 'add_right_cancel'), body,
        'The actual short-input or positive-length quotient convention determines exactly one natural length, including L=0 and d=0.',
    )


def _trim_transport_row(spec: Callable[..., Any]) -> Any:
    params = ('p', 'b', 'c', 'B', 'C', 'L', 't', 'rb', 'rc', 'R')
    body = _intro(*params, 'hequal', 'htrim')
    body += (f"have hreverse : {_equal('B', 'C', 'b', 'c', 'L', 'trim_transport_reverse')}",)
    body += _call('matrix_rank_prefix_equality_symmetric', 'b', 'c', 'B', 'C', 'L') + ('exact hequal',)
    body += (f"have hbounds : {_and(_le('t', 'L', 'trim_transport_cut'), _le('R', 'L', 'trim_transport_length'))}",)
    body += _call('prime_field_polynomial_trim_length_bounds', 'p', 'b', 'c', 'L', 't', 'rb', 'rc', 'R') + ('exact htrim', 'cases hbounds')
    body += _parts('htrim', 5) + ('split', 'exact htrim_left', 'split')
    body += _call('matrix_rank_bounded_prefix_transport', 'b', 'c', 'B', 'C', 'L', 'p') + ('exact hequal', 'exact htrim_right_left', 'split')
    body += _intro('i', 'hindex') + _call('hequal', 'i', '0')
    body += _call('lt_of_lt_of_le', 'i', 't', 'L') + ('exact hindex', 'exact hbounds_left')
    body += _call('htrim_right_right_left', 'i') + ('exact hindex', 'split')
    body += _intro('i', 'a', 'hindex', 'hvalue') + _call('htrim_right_right_right_left', 'i', 'a') + ('exact hindex',)
    body += _call('hreverse', 't+i', 'a') + ('rewrite htrim_left',)
    body += _call('matrix_recursive_lt_add_left', 'i', 'R', 't') + ('exact hindex', 'exact hvalue', 'exact htrim_right_right_right_right')
    return spec(
        'prime_field_polynomial_trim_input_transport',
        f"forall {' '.join(params)}. ({_equal('b', 'c', 'B', 'C', 'L', 'trim_transport_equal')}) -> "
        f"({_trim('p', 'b', 'c', 'L', 't', 'rb', 'rc', 'R', 'trim_transport_source')}) -> "
        f"({_trim('p', 'B', 'C', 'L', 't', 'rb', 'rc', 'R', 'trim_transport_result')})",
        ('matrix_rank_prefix_equality_symmetric', 'prime_field_polynomial_trim_length_bounds',
         'matrix_rank_bounded_prefix_transport', 'lt_of_lt_of_le', 'matrix_recursive_lt_add_left'), body,
        'Actual trim witnesses transport under equality of the annotated input prefix, including its zero prefix and genuinely shifted suffix.',
    )


def _quotient_data_functional_row(spec: Callable[..., Any]) -> Any:
    initial = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd')
    first, second = ('b', 'k', 'q', 'qb', 'qc'), ('B', 'K', 'Q', 'QB', 'QC')
    params = (*initial, *first, *second)
    result = _and('b=B', 'k=K', 'q=Q', _equal('qb', 'qc', 'QB', 'QC', 'q', 'data_unique_quotient'))
    body = _intro(*params, 'hfirst', 'hsecond') + _parts('hfirst', 4) + _parts('hsecond', 4)
    body += ('have hhead : b=B',) + _call('beta_at_unique', 'bb', 'bc', '0', 'b', 'B') + ('exact hfirst_left', 'exact hsecond_left')
    body += _rewrite_all('hhead', _inv('p', 'b', 'k', 'data_unique_inverse_head'), 'b', 'hfirst_right_left')
    body += ('have hscalar : k=K',) + _call('prime_field_inverse_functional', 'p', 'B', 'k', 'K')
    body += ('exact hfirst_right_left', 'exact hsecond_right_left', 'have hlength : q=Q')
    body += _call('polynomial_quotient_length_functional', 'L', 'd', 'q', 'Q') + ('exact hfirst_right_right_left', 'exact hsecond_right_right_left')
    body += ('split', 'exact hhead', 'split', 'exact hscalar', 'split', 'exact hlength')
    body += _rewrite_all('hscalar', _quotient_prefix('p', 'k', 'ab', 'ac', 'bb', 'bc', 'S d', 'qb', 'qc', 'q', 'data_unique_scalar'), 'k', 'hfirst_right_right_right')
    body += _rewrite_all('hlength', _quotient_prefix('p', 'K', 'ab', 'ac', 'bb', 'bc', 'S d', 'qb', 'qc', 'q', 'data_unique_length'), 'q', 'hfirst_right_right_right')
    body += _rewrite_all('hlength', _equal('qb', 'qc', 'QB', 'QC', 'q', 'data_unique_length_result'), 'q')
    body += _call('prime_field_polynomial_quotient_prefix_functional', 'p', 'K', 'ab', 'ac', 'bb', 'bc', 'S d', 'qb', 'qc', 'QB', 'QC', 'Q')
    body += ('exact hfirst_right_right_right', 'exact hsecond_right_right_right')
    return spec(
        'prime_field_polynomial_division_quotient_data_functional',
        f"forall {' '.join(params)}. ({_quotient_data(*initial, *first, 'data_unique_first')}) -> "
        f"({_quotient_data(*initial, *second, 'data_unique_second')}) -> ({result})",
        ('beta_at_unique', 'prime_field_inverse_functional', 'polynomial_quotient_length_functional',
         'prime_field_polynomial_quotient_prefix_functional'), body,
        'The actual divisor head, inverse, quotient length, and decoded quotient coefficients are unique; no primality or code-number equality is inserted.',
    )


def _residual_data_functional_row(spec: Callable[..., Any]) -> Any:
    initial = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd')
    params = (*initial, 'qb', 'qc', 'QB', 'QC', 'q', 'pb', 'pc', 'ub', 'uc', 't', 'rb', 'rc', 'R',
              'PB', 'PC', 'UB', 'UC', 'T', 'RB', 'RC', 'K')
    first = (*initial, 'qb', 'qc', 'q', 'pb', 'pc', 'ub', 'uc', 't', 'rb', 'rc', 'R')
    second = (*initial, 'QB', 'QC', 'q', 'PB', 'PC', 'UB', 'UC', 'T', 'RB', 'RC', 'K')
    body = _intro(*params, 'hequal', 'hfirst', 'hsecond') + _parts('hfirst', 3) + _parts('hsecond', 3)
    body += (f"have hproduct : {_prefix('p', 'QB', 'QC', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'L', 'residual_unique_recode')}",)
    body += _call('prime_field_convolution_prefix_input_transport', 'p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', 'QB', 'QC', 'bb', 'bc', 'pb', 'pc', 'L')
    body += ('exact hequal',) + _intro('i', 'a', 'hindex', 'hvalue') + ('exact hvalue', 'exact hfirst_left')
    body += (f"have hproducts : {_equal('pb', 'pc', 'PB', 'PC', 'L', 'residual_unique_products')}",)
    body += _call('prime_field_convolution_prefix_functional', 'p', 'QB', 'QC', 'q', 'bb', 'bc', 'S d', 'pb', 'pc', 'PB', 'PC', 'L')
    body += ('exact hproduct', 'exact hsecond_left')
    body += (f"have hsubtract : {_subtract('p', 'ab', 'ac', 'PB', 'PC', 'ub', 'uc', 'L', 'residual_unique_difference')}",)
    body += _call('prime_field_polynomial_subtract_transport', 'p', 'ab', 'ac', 'pb', 'pc', 'ub', 'uc', 'ab', 'ac', 'PB', 'PC', 'ub', 'uc', 'L')
    body += _intro('i', 'a', 'hindex', 'hvalue') + ('exact hvalue', 'exact hproducts')
    body += _intro('i', 'a', 'hindex', 'hvalue') + ('exact hvalue', 'exact hfirst_right_left')
    body += (f"have hresiduals : {_equal('ub', 'uc', 'UB', 'UC', 'L', 'residual_unique_inputs')}",)
    body += _call('prime_field_polynomial_subtract_functional', 'p', 'ab', 'ac', 'PB', 'PC', 'ub', 'uc', 'UB', 'UC', 'L')
    body += ('exact hsubtract', 'exact hsecond_right_left')
    body += (f"have htrim : {_trim('p', 'UB', 'UC', 'L', 't', 'rb', 'rc', 'R', 'residual_unique_trim_recode')}",)
    body += _call('prime_field_polynomial_trim_input_transport', 'p', 'ub', 'uc', 'UB', 'UC', 'L', 't', 'rb', 'rc', 'R')
    body += ('exact hresiduals', 'exact hfirst_right_right')
    comparison = ('p', 'UB', 'UC', 'L', 't', 'rb', 'rc', 'R', 'T', 'RB', 'RC', 'K')
    for index, name in enumerate(('prime_field_polynomial_trim_removed_count_unique',
                                  'prime_field_polynomial_trim_retained_length_unique',
                                  'prime_field_polynomial_trim_output_equal')):
        if index < 2:
            body += ('split',)
        body += _call(name, *comparison) + ('exact htrim', 'exact hsecond_right_right')
    return spec(
        'prime_field_polynomial_division_residual_data_functional',
        f"forall {' '.join(params)}. ({_equal('qb', 'qc', 'QB', 'QC', 'q', 'residual_unique_quotients')}) -> "
        f"({_residual_data(*first, 'residual_unique_first')}) -> ({_residual_data(*second, 'residual_unique_second')}) -> "
        f"({_and('t=T', 'R=K', _equal('rb', 'rc', 'RB', 'RC', 'R', 'residual_unique_output'))})",
        ('prime_field_convolution_prefix_input_transport', 'prime_field_convolution_prefix_functional',
         'prime_field_polynomial_subtract_transport', 'prime_field_polynomial_subtract_functional',
         'prime_field_polynomial_trim_input_transport', 'prime_field_polynomial_trim_removed_count_unique',
         'prime_field_polynomial_trim_retained_length_unique', 'prime_field_polynomial_trim_output_equal'), body,
        'Equal decoded quotients give equal actual ambient products and residuals, hence identical trim lengths and coefficientwise equal normalized remainders.',
    )


def _execution_equal(qb: str, qc: str, q: str, rb: str, rc: str, R: str,
                     QB: str, QC: str, Q: str, RB: str, RC: str, K: str, tag: str) -> str:
    return _and(f'({q})=({Q})', _equal(qb, qc, QB, QC, q, tag + 'quotient'),
                f'({R})=({K})', _equal(rb, rc, RB, RC, R, tag + 'remainder'))


def _execution_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    initial = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd')
    first = ('qb', 'qc', 'q', 'rb', 'rc', 'R')
    second = ('QB', 'QC', 'Q', 'RB', 'RC', 'K')
    params = (*initial, *first, *second)
    body = _intro(*params, 'hfirst', 'hsecond') + _parts('hfirst', 4) + _parts('hsecond', 4)
    inner = []
    for name in ('hfirst', 'hsecond'):
        data = name + '_right_right_right'
        body += tuple('cases ' + data + '_witness' * index for index in range(7))
        inside = data + '_witness' * 7
        body += _parts(inside, 6)
        inner.append(inside)
    quotient_result = _and('x=x7', 'x1=x8', 'q=Q', _equal('qb', 'qc', 'QB', 'QC', 'q', 'execution_unique_quotients'))
    body += (f'have hquotients : {quotient_result}',)
    body += _call('prime_field_polynomial_division_quotient_data_functional', *initial,
                  'x', 'x1', 'q', 'qb', 'qc', 'x7', 'x8', 'Q', 'QB', 'QC')
    for name, inside in zip(('hfirst', 'hsecond'), inner, strict=True):
        body += ('split', 'exact ' + _part(inside, 6, 0), 'split', 'exact ' + _part(inside, 6, 1),
                 'split', 'exact ' + name + '_right_right_left', 'exact ' + _part(inside, 6, 2))
    body += _parts('hquotients', 4)
    residual_result = _and('x6=x13', 'R=K', _equal('rb', 'rc', 'RB', 'RC', 'R', 'execution_unique_residuals'))
    body += (f'have hremainder : {residual_result}',)
    body += _call('prime_field_polynomial_division_residual_data_functional', *initial,
                  'qb', 'qc', 'QB', 'QC', 'q', 'x2', 'x3', 'x4', 'x5', 'x6', 'rb', 'rc', 'R',
                  'x9', 'x10', 'x11', 'x12', 'x13', 'RB', 'RC', 'K')
    body += ('exact hquotients_right_right_right', 'split', 'exact ' + _part(inner[0], 6, 3),
             'split', 'exact ' + _part(inner[0], 6, 4), 'exact ' + _part(inner[0], 6, 5))
    second_residual = _residual_data(*initial, 'QB', 'QC', 'q', 'x9', 'x10', 'x11', 'x12', 'x13', 'RB', 'RC', 'K', 'execution_unique_second_residual')
    body += _rewrite_all('hquotients_right_right_left', second_residual, 'q')
    body += ('split', 'exact ' + _part(inner[1], 6, 3), 'split', 'exact ' + _part(inner[1], 6, 4),
             'exact ' + _part(inner[1], 6, 5))
    body += _parts('hremainder', 3) + ('split', 'exact hquotients_right_right_left',
                                      'split', 'exact hquotients_right_right_right',
                                      'split', 'exact hremainder_right_left', 'exact hremainder_right_right')
    functional = spec(
        'prime_field_polynomial_division_execution_functional',
        f"forall {' '.join(params)}. ({_division_execution(*initial, *first, 'execution_unique_first')}) -> "
        f"({_division_execution(*initial, *second, 'execution_unique_second')}) -> "
        f"({_execution_equal(*first, *second, 'execution_unique_outputs')})",
        ('prime_field_polynomial_division_quotient_data_functional',
         'prime_field_polynomial_division_residual_data_functional'), body,
        'Two actual executions on the same annotated inputs agree in quotient and remainder lengths and decoded coefficients, not in beta codes.',
    )
    chosen = ('x', 'x1', 'x2', 'x3', 'x4', 'x5')
    body = _intro(*initial, 'hprime', 'hinput', 'hdivisor')
    body += (f"have hexecution : exists {' '.join(first)}. ({_division_execution(*initial, *first, 'execution_exists_unique_chosen')})",)
    body += _call('prime_field_polynomial_division_execution_exists', *initial) + ('exact hprime', 'exact hinput', 'exact hdivisor')
    body += tuple('cases hexecution' + '_witness' * index for index in range(6))
    hchosen = 'hexecution' + '_witness' * 6
    body += tuple('exists ' + value for value in chosen) + ('split', 'exact ' + hchosen)
    body += _intro(*second, 'hother') + _call('prime_field_polynomial_division_execution_functional', *initial, *chosen, *second)
    body += ('exact ' + hchosen, 'exact hother')
    conclusion = _and(_division_execution(*initial, *first, 'execution_exists_unique_actual'),
                      f"forall {' '.join(second)}. ({_division_execution(*initial, *second, 'execution_exists_unique_other')}) -> "
                      f"({_execution_equal(*first, *second, 'execution_exists_unique_equal')})")
    exists = spec(
        'prime_field_polynomial_division_execution_exists_unique',
        f"forall {' '.join(initial)}. ({_prime('p', 'execution_exists_unique_prime')}) -> "
        f"({_coeff('p', 'ab', 'ac', 'L', 'execution_exists_unique_input')}) -> "
        f"({_degree('p', 'bb', 'bc', 'S d', 'd', 'execution_exists_unique_divisor')}) -> "
        f"exists {' '.join(first)}. ({conclusion})",
        ('prime_field_polynomial_division_execution_exists', 'prime_field_polynomial_division_execution_functional'), body,
        'Construct the actual execution over a prime field with nonzero divisor head and prove its coefficientwise uniqueness against every other execution.',
    )
    return functional, exists




def make_prime_field_polynomial_division_uniqueness_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_step_rows(spec), _prefix_functional_row(spec), _length_functional_row(spec),
            _trim_transport_row(spec), _quotient_data_functional_row(spec),
            _residual_data_functional_row(spec), *_execution_rows(spec))
