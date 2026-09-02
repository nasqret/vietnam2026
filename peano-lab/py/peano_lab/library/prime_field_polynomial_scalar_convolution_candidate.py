"""Actual right-input scalar covariance of natural-coded convolution.

This working-only tranche reuses the existing FpPolyScale graph (ND0271).
That graph requires k<p even on an empty prefix and records actual canonical
products at each represented coefficient.  It assumes no convolution law.

An induction on two genuine natural Sum traces transports pointwise modular
scalar congruences.  Actual antidiagonal witnesses supply its premises;
canonical residue bounds turn the resulting congruence into actual FpMul.
No primality, evaluation identity, raw beta-code equality, or desired output
identity is smuggled into a graph.  Nonzero composite moduli are supported.
The source registers no admission and claims neither associativity nor gcd.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _mod, _mul as _field_mul, _parts,
)
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat, _scale
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _diagonal, _pad, _sum, _term,
)
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], conclusion: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + value + ')' for value in (*premises, conclusion)
    )


def _pointwise(p: str, k: str, ab: str, ac: str, bb: str, bc: str, length: str, tag: str) -> str:
    i, a, b = ('pfscalar_' + role + '_' + tag for role in ('index', 'source', 'target'))
    return (f'forall {i} {a} {b}. ({_lt(i,length,tag+"index")}) -> '
            f'({_at(ab,ac,i,a,tag+"source")}) -> ({_at(bb,bc,i,b,tag+"target")}) -> '
            f'({_mod(p,f"({k})*{a}",b,tag+"congruence")})')


def _sum_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', 'ab', 'ac', 'bb', 'bc', 'L', 'u', 'v')
    body = _intro(*parameters[:6]) + ('induction L',) + _intro('u', 'v', 'hu', 'hv', 'hw')
    body += ('have hu0 : u=0',) + _call('beta_sum_zero', 'ab', 'ac', 'u') + ('exact hu',)
    body += ('have hv0 : v=0',) + _call('beta_sum_zero', 'bb', 'bc', 'v') + ('exact hv',)
    body += ('rewrite hu0', 'rewrite hv0', 'exists 0', 'exists 0', 'simp')
    body += _intro('u', 'v', 'hu', 'hv', 'hw')
    first = _and(_at('ab', 'ac', 'L', 'a', 'scalar_sum_old_last'),
                 _sum('ab', 'ac', 'L', 'n', 'scalar_sum_old_prefix'), 'u=n+a')
    second = _and(_at('bb', 'bc', 'L', 'a', 'scalar_sum_new_last'),
                  _sum('bb', 'bc', 'L', 'n', 'scalar_sum_new_prefix'), 'v=n+a')
    body += ('have hfirst : exists a n. ' + first,) + _call('beta_sum_succ_decompose', 'ab', 'ac', 'L', 'u')
    body += ('exact hu', 'cases hfirst', 'cases hfirst_witness') + _parts('hfirst_witness_witness', 3)
    body += ('have hsecond : exists a n. ' + second,) + _call('beta_sum_succ_decompose', 'bb', 'bc', 'L', 'v')
    body += ('exact hv', 'cases hsecond', 'cases hsecond_witness') + _parts('hsecond_witness_witness', 3)
    body += (f"have hprefix : {_mod('p','k*x1','x3','scalar_sum_prefix_congruence')}",)
    body += _call('IH', 'x1', 'x3') + ('exact hfirst_witness_witness_right_left', 'exact hsecond_witness_witness_right_left')
    body += _intro('i', 'a', 'b', 'hi', 'ha', 'hb') + _call('hw', 'i', 'a', 'b')
    body += _call('le_succ', 'S i', 'L') + ('exact hi', 'exact ha', 'exact hb')
    body += (f"have hlast : {_mod('p','k*x','x2','scalar_sum_last_congruence')}",)
    body += _call('hw', 'L', 'x', 'x2') + _call('le_refl', 'S L')
    body += ('exact hfirst_witness_witness_left', 'exact hsecond_witness_witness_left')
    body += (f"have hcombined : {_mod('p','k*x1+k*x','x3+x2','scalar_sum_combined')}",)
    body += _call('mod_eq_add', 'p', 'k*x1', 'x3', 'k*x', 'x2') + ('exact hprefix', 'exact hlast')
    body += ('rewrite hfirst_witness_witness_right_right', 'rewrite hsecond_witness_witness_right_right',
             'have hdistribute : k*(x1+x)=k*x1+k*x', 'apply mul_add', 'rewrite hdistribute', 'exact hcombined')
    return spec(
        'beta_sum_pointwise_mod_scale',
        _contract(parameters, (_sum('ab', 'ac', 'L', 'u', 'scalar_sum_source'),
                               _sum('bb', 'bc', 'L', 'v', 'scalar_sum_target'),
                               _pointwise('p', 'k', 'ab', 'ac', 'bb', 'bc', 'L', 'scalar_sum_points')),
                  _mod('p', 'k*u', 'v', 'scalar_sum_result')),
        ('beta_sum_zero', 'beta_sum_succ_decompose', 'le_succ', 'le_refl', 'mod_eq_add', 'mul_add'), body,
        'Pointwise scalar congruences lift through two actual natural Sum traces at every modulus, including zero and the empty length; no new sum witness is assumed equal to a desired total.',
    )


def _zero_extended_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'i', 'b', 's')
    body = _intro(*parameters, 'hs', 'hb', 'hr') + ('cases hb', 'cases hb_left')
    body += (f"have htarget : {_at('sb','sc','i','s','scalar_pad_inside_target')}",)
    body += _call('polynomial_zero_extended_entry_inside', 'sb', 'sc', 'M', 'i', 's')
    body += ('exact hb_left_left', 'exact hr')
    body += (f"have hm : {_field_mul('p','k','b','s','scalar_pad_inside_product')}",)
    body += _call('prime_field_polynomial_scale_entry', *parameters)
    body += ('exact hs', 'exact hb_left_left', 'exact hb_left_right', 'exact htarget') + _parts('hm', 4)
    body += ('exact hm_right_right_right', 'cases hb_right', 'have hz : s=0')
    body += _call('polynomial_zero_extended_entry_functional', 'sb', 'sc', 'M', 'i', 's', '0')
    body += ('exact hr', 'right', 'split', 'exact hb_right_left', 'refl',
             'rewrite hb_right_right', 'rewrite hz', 'exists 0', 'exists 0', 'simp')
    return spec(
        'polynomial_zero_extended_scale_congruent',
        _contract(parameters, (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_pad_operation'),
                               _pad('bb', 'bc', 'M', 'i', 'b', 'scalar_pad_source'),
                               _pad('sb', 'sc', 'M', 'i', 's', 'scalar_pad_target')),
                  _mod('p', 'k*b', 's', 'scalar_pad_result')),
        ('polynomial_zero_extended_entry_inside', 'prime_field_polynomial_scale_entry',
         'polynomial_zero_extended_entry_functional'), body,
        'Actual coefficient scaling extends by genuine exterior zeros to a scalar congruence at every array index, with no condition on raw entries after the prefixes.',
    )


FACTORS = ('ab', 'ac', 'L', 'bb', 'bc', 'M')
SCALED_FACTORS = ('ab', 'ac', 'L', 'sb', 'sc', 'M')


def _term_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'j', 't', 'r')
    body = _intro(*parameters, 'hs', 'ht', 'hr')
    for hypothesis in ('ht', 'hr'):
        body += tuple('cases ' + hypothesis + '_witness' * i for i in range(3))
        body += _parts(hypothesis + '_witness_witness_witness', 4)
    body += ('have hindex : x=x3',) + _call('add_left_cancel', 'j', 'x', 'x3')
    body += ('trans i', 'exact ht_witness_witness_witness_left', 'symm', 'exact hr_witness_witness_witness_left')
    body += _rewrite_all('hindex', _pad('bb', 'bc', 'M', 'x', 'x2', 'scalar_term_old_complement'),
                         'x', 'ht_witness_witness_witness_right_right_left')
    body += ('have hleft : x1=x4',) + _call('polynomial_zero_extended_entry_functional', 'ab', 'ac', 'L', 'j', 'x1', 'x4')
    body += ('exact ht_witness_witness_witness_right_left', 'exact hr_witness_witness_witness_right_left')
    body += (f"have hscale : {_mod('p','k*x2','x5','scalar_term_actual_right_scale')}",)
    body += _call('polynomial_zero_extended_scale_congruent', 'p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'x3', 'x2', 'x5')
    body += ('exact hs', 'exact ht_witness_witness_witness_right_right_left', 'exact hr_witness_witness_witness_right_right_left')
    body += (f"have hm : {_mod('p','x4*(k*x2)','x4*x5','scalar_term_product_congruence')}",)
    body += _call('mod_eq_mul_left', 'p', 'k*x2', 'x5', 'x4') + ('exact hscale',)
    body += ('have hshuffle : k*(x1*x2)=x4*(k*x2)', 'rewrite hleft', 'simp [mul_assoc,mul_comm]',
             'rewrite ht_witness_witness_witness_right_right_right',
             'rewrite hr_witness_witness_witness_right_right_right', 'rewrite hshuffle', 'exact hm')
    return spec(
        'polynomial_diagonal_term_right_scale_congruent',
        _contract(parameters, (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_term_operation'),
                               _term(*FACTORS, 'i', 'j', 't', 'scalar_term_original'),
                               _term(*SCALED_FACTORS, 'i', 'j', 'r', 'scalar_term_scaled')),
                  _mod('p', 'k*t', 'r', 'scalar_term_result')),
        ('add_left_cancel', 'polynomial_zero_extended_entry_functional',
         'polynomial_zero_extended_scale_congruent', 'mod_eq_mul_left', 'mul_assoc', 'mul_comm'), body,
        'The uniquely identified complementary index and unchanged left coefficient turn actual right-input scaling into pointwise antidiagonal scalar congruence.',
    )


def _diagonal_sum_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'db', 'dc', 'eb', 'ec', 'N', 'u', 'v')
    body = _intro(*parameters, 'hs', 'hd', 'hu', 'he', 'hv')
    body += _call('beta_sum_pointwise_mod_scale', 'p', 'k', 'db', 'dc', 'eb', 'ec', 'N', 'u', 'v')
    body += ('exact hu', 'exact hv') + _intro('j', 'a', 'b', 'hj', 'ha', 'hb')
    body += _call('polynomial_diagonal_term_right_scale_congruent', 'p', 'k', *FACTORS, 'sb', 'sc', 'i', 'j', 'a', 'b')
    body += ('exact hs',) + _call('polynomial_diagonal_prefix_entry', *FACTORS, 'i', 'db', 'dc', 'N', 'j', 'a')
    body += ('exact hd', 'exact hj', 'exact ha')
    body += _call('polynomial_diagonal_prefix_entry', *SCALED_FACTORS, 'i', 'eb', 'ec', 'N', 'j', 'b')
    body += ('exact he', 'exact hj', 'exact hb')
    return spec(
        'polynomial_diagonal_sum_right_scale_congruent',
        _contract(parameters, (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_diagonal_operation'),
                               _diagonal(*FACTORS, 'i', 'db', 'dc', 'N', 'scalar_diagonal_old'),
                               _sum('db', 'dc', 'N', 'u', 'scalar_diagonal_old_sum'),
                               _diagonal(*SCALED_FACTORS, 'i', 'eb', 'ec', 'N', 'scalar_diagonal_new'),
                               _sum('eb', 'ec', 'N', 'v', 'scalar_diagonal_new_sum')),
                  _mod('p', 'k*u', 'v', 'scalar_diagonal_result')),
        ('beta_sum_pointwise_mod_scale', 'polynomial_diagonal_term_right_scale_congruent',
         'polynomial_diagonal_prefix_entry'), body,
        'Two actual antidiagonal tables and their actual natural sums satisfy scalar congruence; no supplied output identity or Fubini oracle is used.',
    )


def _coefficient_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', *FACTORS, 'sb', 'sc', 'i', 'c', 'r')
    body = _intro(*parameters, 'hs', 'hc', 'hr')
    for hypothesis in ('hc', 'hr'):
        body += tuple('cases ' + hypothesis + '_witness' * i for i in range(3))
        body += _parts(hypothesis + '_witness_witness_witness', 3)
    body += (f"have hsum : {_mod('p','k*x2','x5','scalar_coefficient_actual_sum')}",)
    body += _call('polynomial_diagonal_sum_right_scale_congruent',
                  'p', 'k', *FACTORS, 'sb', 'sc', 'i', 'x', 'x1', 'x3', 'x4', 'S i', 'x2', 'x5')
    body += ('exact hs', 'exact hc_witness_witness_witness_left', 'exact hc_witness_witness_witness_right_left',
             'exact hr_witness_witness_witness_left', 'exact hr_witness_witness_witness_right_left')
    body += ('cases hs', 'cases hc_witness_witness_witness_right_right',
             'cases hr_witness_witness_witness_right_right')
    body += (f"have htail : {_mod('p','k*x2','r','scalar_coefficient_tail')}",)
    body += _call('mod_eq_trans', 'p', 'k*x2', 'x5', 'r')
    body += ('exact hsum', 'exact hr_witness_witness_witness_right_right_right',
             'split', 'exact hs_left', 'split', 'exact hc_witness_witness_witness_right_right_left',
             'split', 'exact hr_witness_witness_witness_right_right_left')
    body += _call('mod_eq_trans', 'p', 'k*c', 'k*x2', 'r')
    body += _call('mod_eq_symm', 'p', 'k*x2', 'k*c')
    body += _call('mod_eq_mul_left', 'p', 'x2', 'c', 'k')
    body += ('exact hc_witness_witness_witness_right_right_right',)
    body += ('exact htail',)
    return spec(
        'prime_field_convolution_coefficient_right_scale',
        _contract(parameters, (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_coefficient_operation'),
                               _coefficient('p', *FACTORS, 'i', 'c', 'scalar_coefficient_original'),
                               _coefficient('p', *SCALED_FACTORS, 'i', 'r', 'scalar_coefficient_scaled')),
                  _field_mul('p', 'k', 'c', 'r', 'scalar_coefficient_result')),
        ('polynomial_diagonal_sum_right_scale_congruent', 'mod_eq_trans', 'mod_eq_symm', 'mod_eq_mul_left'), body,
        'At every natural index the actual scaled-input convolution coefficient is the actual canonical product of k and the original coefficient, including all exterior coefficients and composite moduli.',
    )


PRODUCT_PARAMETERS = ('p', 'k', *FACTORS, 'sb', 'sc', 'cb', 'cc', 'N', 'db', 'dc', 'K')


def _products(tag: str) -> tuple[str, str]:
    return (_convolution('p', *FACTORS, 'cb', 'cc', 'N', tag + 'old'),
            _convolution('p', *SCALED_FACTORS, 'db', 'dc', 'K', tag + 'scaled'))


def _product_row(spec: Callable[..., Any]) -> Any:
    old, new = _products('scalar_product_')
    body = _intro(*PRODUCT_PARAMETERS, 'hs', 'hc', 'hd')
    body += _parts('hc', 4) + _parts('hd', 4)
    body += ('have hk : K=N',) + _call('polynomial_product_length_functional', 'L', 'M', 'K', 'N')
    body += ('exact hd_right_right_left', 'exact hc_right_right_left', 'split', 'exact hk')
    body += (f"have hcopy : {_scale('p','k','bb','bc','sb','sc','M','scalar_product_scale_copy')}", 'exact hs',
             'cases hcopy', 'split', 'exact hcopy_left') + _intro('i', 'hi')
    first = _and(_at('cb', 'cc', 'i', 'a', 'scalar_product_original_entry'),
                 _coefficient('p', *FACTORS, 'i', 'a', 'scalar_product_original_coefficient'))
    second = _and(_at('db', 'dc', 'i', 'a', 'scalar_product_scaled_entry'),
                  _coefficient('p', *SCALED_FACTORS, 'i', 'a', 'scalar_product_scaled_coefficient'))
    body += ('have ha : exists a. ' + first,) + _call('hc_right_right_right', 'i')
    body += ('exact hi', 'cases ha', 'cases ha_witness', 'have hb : exists a. ' + second)
    body += _call('hd_right_right_right', 'i')
    body += _rewrite_all('hk', _lt('i', 'K', 'scalar_product_scaled_bound'), 'K')
    body += ('exact hi', 'cases hb', 'cases hb_witness', 'exists x', 'exists x1',
             'split', 'exact ha_witness_left', 'split', 'exact hb_witness_left')
    body += _call('prime_field_convolution_coefficient_right_scale', 'p', 'k', *FACTORS, 'sb', 'sc', 'i', 'x', 'x1')
    body += ('exact hs', 'exact ha_witness_right', 'exact hb_witness_right')
    return spec(
        'prime_field_polynomial_convolution_right_scale',
        _contract(PRODUCT_PARAMETERS,
                  (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_product_input'), old, new),
                  _and('K=N', _scale('p', 'k', 'cb', 'cc', 'db', 'dc', 'N', 'scalar_product_result'))),
        ('polynomial_product_length_functional', 'prime_field_convolution_coefficient_right_scale'), body,
        'Scaling the actual right input preserves the proper representation length and gives the actual scalar action on the product output, including empty factors and zero scalars.',
    )


def _comparison_row(spec: Callable[..., Any]) -> Any:
    parameters = (*PRODUCT_PARAMETERS, 'eb', 'ec')
    old, new = _products('scalar_comparison_')
    data = _and('K=N', _scale('p', 'k', 'cb', 'cc', 'db', 'dc', 'N', 'scalar_comparison_data'))
    body = _intro(*parameters, 'hs', 'hc', 'hd', 'he') + ('have hdata : ' + data,)
    body += _call('prime_field_polynomial_convolution_right_scale', *PRODUCT_PARAMETERS)
    body += ('exact hs', 'exact hc', 'exact hd', 'cases hdata', 'split', 'exact hdata_left')
    body += _call('prime_field_polynomial_scale_functional', 'p', 'k', 'cb', 'cc', 'db', 'dc', 'eb', 'ec', 'N')
    body += ('exact hdata_right', 'exact he')
    return spec(
        'prime_field_polynomial_convolution_right_scale_equal',
        _contract(parameters, (_scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_comparison_input'), old, new,
                               _scale('p', 'k', 'cb', 'cc', 'eb', 'ec', 'N', 'scalar_comparison_output')),
                  _and('K=N', _equal('db', 'dc', 'eb', 'ec', 'N', 'scalar_comparison_result'))),
        ('prime_field_polynomial_convolution_right_scale', 'prime_field_polynomial_scale_functional'), body,
        'Every actual product A*(k B) agrees coefficientwise with every actual scalar result k*(A*B), at the same proper length; no equality of beta codes follows.',
    )


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', *FACTORS, 'cb', 'cc', 'N')
    old = _convolution('p', *FACTORS, 'cb', 'cc', 'N', 'scalar_exists_original')
    new = _convolution('p', *SCALED_FACTORS, 'db', 'dc', 'N', 'scalar_exists_new')
    input_scale = _scale('p', 'k', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_exists_input')
    output_scale = _scale('p', 'k', 'cb', 'cc', 'eb', 'ec', 'N', 'scalar_exists_output')
    output_equal = _equal('db', 'dc', 'eb', 'ec', 'N', 'scalar_exists_equal')
    body = _intro(*parameters, 'hp', 'hk', 'hc') + ('have hcopy : ' + old, 'exact hc') + _parts('hcopy', 4)
    body += ('have hs : exists sb sc. ' + input_scale,) + _call('prime_field_polynomial_scale_exists', 'p', 'k', 'bb', 'bc', 'M')
    body += ('exact hp', 'exact hk', 'exact hcopy_right_left', 'cases hs', 'cases hs_witness')
    bounds = _and(_coeff('p', 'bb', 'bc', 'M', 'scalar_exists_old_bound'),
                  _coeff('p', 'x', 'x1', 'M', 'scalar_exists_scaled_bound'))
    body += ('have hb : ' + bounds,) + _call('prime_field_polynomial_scale_bounded', 'p', 'k', 'bb', 'bc', 'x', 'x1', 'M')
    body += ('exact hs_witness_witness', 'cases hb')
    chosen = _convolution('p', 'ab', 'ac', 'L', 'x', 'x1', 'M', 'd', 'e', 'N', 'scalar_exists_chosen_product')
    body += ('have hd : exists d e. ' + chosen,)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', 'ab', 'ac', 'L', 'x', 'x1', 'M', 'N')
    body += ('exact hp', 'exact hcopy_left', 'exact hb_right', 'exact hcopy_right_right_left', 'cases hd', 'cases hd_witness')
    body += ('have he : exists eb ec. ' + output_scale,) + _call('prime_field_polynomial_scale_exists', 'p', 'k', 'cb', 'cc', 'N')
    body += ('exact hp', 'exact hk') + _call('prime_field_polynomial_convolution_bounded', 'p', *FACTORS, 'cb', 'cc', 'N')
    body += ('exact hc', 'cases he', 'cases he_witness', 'exists x', 'exists x1', 'exists x2', 'exists x3', 'exists x4', 'exists x5',
             'split', 'exact hs_witness_witness', 'split', 'exact hd_witness_witness', 'split', 'exact he_witness_witness')
    data = _and('N=N', _equal('x2', 'x3', 'x4', 'x5', 'N', 'scalar_exists_comparison'))
    body += ('have hdata : ' + data,)
    body += _call('prime_field_polynomial_convolution_right_scale_equal', 'p', 'k', *FACTORS,
                  'x', 'x1', 'cb', 'cc', 'N', 'x2', 'x3', 'N', 'x4', 'x5')
    body += ('exact hs_witness_witness', 'exact hc', 'exact hd_witness_witness', 'exact he_witness_witness',
             'cases hdata', 'exact hdata_right')
    return spec(
        'prime_field_polynomial_convolution_right_scale_exists',
        _contract(parameters, ('~(p=0)', _lt('k', 'p', 'scalar_exists_scalar'), old),
                  'exists sb sc db dc eb ec. ' + _and(input_scale, new, output_scale, output_equal)),
        ('prime_field_polynomial_scale_exists', 'prime_field_polynomial_scale_bounded',
         'prime_field_polynomial_convolution_at_length_exists', 'prime_field_polynomial_convolution_bounded',
         'prime_field_polynomial_convolution_right_scale_equal'), body,
        'At any nonzero modulus and canonical scalar, construct the actual scaled input, its actual convolution, and an independently encoded scalar output, then derive their exact decoded-prefix agreement.',
    )


def _zero_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('p', 'bb', 'bc', 'sb', 'sc', 'M')
    body = _intro(*parameters, 'hs') + ('cases hs',) + _intro('i', 'hi')
    chosen = _and(_at('bb', 'bc', 'i', 'a', 'scalar_zero_chosen_source'),
                  _at('sb', 'sc', 'i', 'r', 'scalar_zero_chosen_target'),
                  _field_mul('p', '0', 'a', 'r', 'scalar_zero_chosen_product'))
    body += ('have hv : exists a r. ' + chosen,) + _call('hs_right', 'i')
    body += ('exact hi', 'cases hv', 'cases hv_witness') + _parts('hv_witness_witness', 3)
    body += (f"have hm : {_field_mul('p','0','x','x1','scalar_zero_actual_product')}", 'exact hv_witness_witness_right_right')
    body += _parts('hm', 3) + ('have hzero : 0*x=0', 'apply mul_zero_left', 'rewrite hzero at hm_right_right', 'have heq : x1=0')
    body += _call('prime_field_residue_bounded_value', 'p', '0', 'x1') + ('exact hs_left', 'exact hm_right_right')
    body += _rewrite_all('heq', _at('sb', 'sc', 'i', 'x1', 'scalar_zero_target_rewrite'), 'x1', 'hv_witness_witness_right_left')
    body += ('exact hv_witness_witness_right_left',)
    zero_value = spec(
        'prime_field_polynomial_scale_zero_value',
        _contract(parameters, (_scale('p', '0', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_zero_actual'),),
                  _repeat('sb', 'sc', '0', 'M', 'scalar_zero_result')),
        ('mul_zero_left', 'prime_field_residue_bounded_value'), body,
        'Every actual scalar-zero output is an actually all-zero prefix, without primality and without dropping the scalar bound on an empty input.',
    )
    parameters = ('p', *FACTORS, 'sb', 'sc', 'db', 'dc', 'N')
    body = _intro(*parameters, 'hp', 'hs', 'hd')
    body += _call('prime_field_polynomial_convolution_zero_right', 'p', *SCALED_FACTORS, 'db', 'dc', 'N')
    body += ('exact hp',) + _call('prime_field_polynomial_scale_zero_value', 'p', 'bb', 'bc', 'sb', 'sc', 'M')
    body += ('exact hs', 'exact hd')
    zero_product = spec(
        'prime_field_polynomial_convolution_right_scale_zero',
        _contract(parameters, ('~(p=0)', _scale('p', '0', 'bb', 'bc', 'sb', 'sc', 'M', 'scalar_zero_product_input'),
                               _convolution('p', *SCALED_FACTORS, 'db', 'dc', 'N', 'scalar_zero_product_actual')),
                  _repeat('db', 'dc', '0', 'N', 'scalar_zero_product_result')),
        ('prime_field_polynomial_convolution_zero_right', 'prime_field_polynomial_scale_zero_value'), body,
        'An actual product with a scalar-zero right input has a genuine zero output prefix at its actual proper length, including empty factors and composite nonzero moduli.',
    )
    return zero_value, zero_product


def make_prime_field_polynomial_scalar_convolution_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_sum_row(spec), _zero_extended_row(spec), _term_row(spec), _diagonal_sum_row(spec),
            _coefficient_row(spec), _product_row(spec), _comparison_row(spec), _exists_row(spec), *_zero_rows(spec))


__all__ = ['make_prime_field_polynomial_scalar_convolution_candidate_theorems']
