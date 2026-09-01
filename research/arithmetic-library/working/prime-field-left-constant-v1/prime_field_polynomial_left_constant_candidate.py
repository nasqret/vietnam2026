"""Actual constant-left convolution and canonical coefficient scalar action.

The singleton is the LEFT factor.  Its first natural antidiagonal summand is
k*a and all subsequent summands vanish by the existing, value-independent
left-unit tail theorem.  No polynomial or scalar commutativity is assumed.
The length-zero case is an actual empty proper product; values outside each
annotated prefix remain unconstrained.  These are working conditional bodies,
not dependency-complete proof, Lean, admission, gcd, or Bezout authority.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _mul, _parts, _prime, _residue,
)
from peano_lab.library.prime_field_polynomial_candidate import (
    _at, _coeff, _repeat, _scale,
)
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _diagonal, _sum, _term,
)
from peano_lab.library.prime_field_polynomial_convolution_padding_candidate import _tail
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result))


K, A, H = ('kb', 'kc', '1'), ('ab', 'ac', 'L'), ('hb', 'hc', 'L')
PARAMETERS = ('p', 'k', 'kb', 'kc', 'ab', 'ac', 'hb', 'hc', 'L')


def _first_term_row(spec: Callable[..., Any]) -> Any:
    parameters = ('k', 'kb', 'kc', *A, 'i', 'a', 't')
    body = _intro(*parameters, 'hk', 'hi', 'ha', 'ht')
    body += _call('polynomial_diagonal_term_functional', *K, *A, 'i', '0', 't', 'k*a')
    body += ('exact ht', 'exists i', 'exists k', 'exists a', 'split',
             'apply zero_add', 'split', 'left', 'split', 'exists 0',
             'apply zero_add', 'exact hk', 'split', 'left', 'split',
             'exact hi', 'exact ha', 'refl')
    return spec(
        'polynomial_diagonal_left_constant_first_term',
        _contract(parameters, (
            _at('kb', 'kc', '0', 'k', 'left_constant_first_K'),
            _lt('i', 'L', 'left_constant_first_index'),
            _at('ab', 'ac', 'i', 'a', 'left_constant_first_A'),
            _term(*K, *A, 'i', '0', 't', 'left_constant_first_actual'),
        ), 't=k*a'),
        ('polynomial_diagonal_term_functional', 'zero_add'), body,
        'The first actual antidiagonal term of a genuine left singleton is the ordered natural product k*a. No modulus, coefficient bound, or commutativity premise is needed.',
    )


def _sum_row(spec: Callable[..., Any]) -> Any:
    parameters = ('k', 'kb', 'kc', *A, 'i', 'a', 'db', 'dc', 'n')
    body = _intro(*parameters, 'hk', 'hi', 'ha', 'hd', 'hs')
    body += ('have hhead : ' + _at('db', 'dc', '0', 'k*a', 'left_constant_sum_head'),)
    point = _and(_at('db', 'dc', '0', 't', 'left_constant_sum_first_entry'),
                 _term(*K, *A, 'i', '0', 't', 'left_constant_sum_first_term'))
    body += ('have hv : exists t. ' + point,) + _call('hd', '0')
    body += ('exists i', 'simp', 'cases hv', 'cases hv_witness', 'have heq : x=k*a')
    body += _call('polynomial_diagonal_left_constant_first_term',
                  'k', 'kb', 'kc', *A, 'i', 'a', 'x')
    body += ('exact hk', 'exact hi', 'exact ha', 'exact hv_witness_right')
    body += _rewrite_all('heq', _at('db', 'dc', '0', 'x', 'left_constant_sum_head_rewrite'),
                         'x', 'hv_witness_left') + ('exact hv_witness_left',)
    body += ('have htail : ' + _tail('db', 'dc', '1', 'i', 'left_constant_sum_tail'),)
    body += _intro('j', 'hj')
    point = _and(_at('db', 'dc', '1+j', 't', 'left_constant_sum_tail_entry'),
                 _term(*K, *A, 'i', '1+j', 't', 'left_constant_sum_tail_term'))
    body += ('have hv : exists t. ' + point,) + _call('hd', '1+j')
    body += ('have hindex : 1+j=S j', 'simp [add_succ_left,zero_add]')
    body += _rewrite_all('hindex', _lt('1+j', 'S i', 'left_constant_sum_tail_index'), '1+j')
    body += _call('succ_le_succ', 'S j', 'i') + ('exact hj', 'cases hv', 'cases hv_witness',
                                                              'have heq : x=0')
    # This unchanged theorem has NO singleton-value premise: its statement is
    # solely about a left index outside the actual length-one prefix.
    body += _call('polynomial_diagonal_left_unit_tail_term', 'kb', 'kc', *A, 'i', '1+j', 'x')
    body += _call('le_add_right', '1', 'j') + ('exact hv_witness_right',)
    body += _rewrite_all('heq', _at('db', 'dc', '1+j', 'x', 'left_constant_sum_tail_rewrite'),
                         'x', 'hv_witness_left') + ('exact hv_witness_left',)
    body += ('have hsingle : exists m. (' + _sum('db', 'dc', '1', 'm', 'left_constant_single_sum') + ')',)
    body += _call('beta_sum_exists', 'db', 'dc', '1') + ('cases hsingle',)
    decomposition = _and(_at('db', 'dc', '0', 't', 'left_constant_single_entry'),
                         _sum('db', 'dc', '0', 's', 'left_constant_single_empty'), 'x=s+t')
    body += ('have hdecomp : exists t s. ' + decomposition,)
    body += _call('beta_sum_succ_decompose', 'db', 'dc', '0', 'x')
    body += ('exact hsingle_witness', 'cases hdecomp', 'cases hdecomp_witness')
    body += _parts('hdecomp_witness_witness', 3)
    body += ('have hzero : x2=0',) + _call('beta_sum_zero', 'db', 'dc', 'x2')
    body += ('exact hdecomp_witness_witness_right_left', 'have hentry : x1=k*a')
    body += _call('beta_at_unique', 'db', 'dc', '0', 'x1', 'k*a')
    body += ('exact hdecomp_witness_witness_left', 'exact hhead', 'have hvalue : x=k*a',
             'trans x2+x1', 'exact hdecomp_witness_witness_right_right', 'rewrite hzero',
             'trans x1', 'apply zero_add', 'exact hentry', 'trans x')
    body += _call('polynomial_zero_tail_natural_sum_invariant',
                  'db', 'dc', 'db', 'dc', '1', 'i', 'x', 'n')
    body += _intro('j0', 'v0', 'hj0', 'hv0') + ('exact hv0', 'exact htail', 'exact hsingle_witness',
                                              'have hlength : 1+i=S i', 'simp [add_succ_left,zero_add]')
    body += _rewrite_all('hlength', _sum('db', 'dc', '1+i', 'n', 'left_constant_sum_length_rewrite'), '1+i')
    body += ('exact hs', 'exact hvalue')
    return spec(
        'polynomial_diagonal_left_constant_natural_sum',
        _contract(parameters, (
            _at('kb', 'kc', '0', 'k', 'left_constant_sum_K'),
            _lt('i', 'L', 'left_constant_sum_index'), _at('ab', 'ac', 'i', 'a', 'left_constant_sum_A'),
            _diagonal(*K, *A, 'i', 'db', 'dc', 'S i', 'left_constant_sum_diagonal'),
            _sum('db', 'dc', 'S i', 'n', 'left_constant_sum_actual'),
        ), 'n=k*a'),
        ('polynomial_diagonal_left_constant_first_term', 'polynomial_diagonal_left_unit_tail_term',
         'add_succ_left', 'zero_add', 'succ_le_succ', 'le_add_right', 'beta_sum_exists',
         'beta_sum_succ_decompose', 'beta_sum_zero', 'beta_at_unique',
         'polynomial_zero_tail_natural_sum_invariant'), body,
        'The actual finite natural sum equals k*a: construct its one-term sum and use the existing zero-tail invariant for every subsequent summand. The total need not itself be a canonical field coefficient.',
    )


def _coefficient_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', 'kb', 'kc', *A, 'i', 'a', 'r')
    body = _intro(*parameters, 'hk', 'hi', 'ha', 'hkb', 'hab', 'hr')
    body += tuple('cases hr' + '_witness' * i for i in range(3))
    inner = 'hr_witness_witness_witness'
    body += _parts(inner, 3) + ('have hn : x2=k*a',)
    body += _call('polynomial_diagonal_left_constant_natural_sum',
                  'k', 'kb', 'kc', *A, 'i', 'a', 'x', 'x1', 'x2')
    body += ('exact hk', 'exact hi', 'exact ha', 'exact ' + inner + '_left',
             'exact ' + inner + '_right_left')
    body += _rewrite_all('hn', _residue('p', 'x2', 'r', 'left_constant_coefficient_residue'),
                         'x2', inner + '_right_right')
    body += ('split', 'exact hkb', 'split', 'exact hab', 'exact ' + inner + '_right_right')
    return spec(
        'prime_field_convolution_coefficient_left_constant',
        _contract(parameters, (
            _at('kb', 'kc', '0', 'k', 'left_constant_coefficient_K'),
            _lt('i', 'L', 'left_constant_coefficient_index'),
            _at('ab', 'ac', 'i', 'a', 'left_constant_coefficient_A'),
            _lt('k', 'p', 'left_constant_coefficient_k_bound'),
            _lt('a', 'p', 'left_constant_coefficient_a_bound'),
            _coefficient('p', *K, *A, 'i', 'r', 'left_constant_coefficient_actual'),
        ), _mul('p', 'k', 'a', 'r', 'left_constant_coefficient_result')),
        ('polynomial_diagonal_left_constant_natural_sum',), body,
        'Every actual in-range constant-left convolution coefficient is the canonical residue of the ordered product k*a. Both input bounds and the actual natural-sum witness are explicit; primality is unnecessary for this implication.',
    )


def _product_to_scale_row(spec: Callable[..., Any]) -> Any:
    product = _convolution('p', *K, *A, *H, 'left_constant_product_source')
    body = _intro(*PARAMETERS, 'hk', 'hproduct') + _parts('hproduct', 4)
    body += ('have hkb : ' + _lt('k', 'p', 'left_constant_product_k_bound'),)
    body += _call('matrix_rank_bounded_prefix_value', 'kb', 'kc', '1', 'p', '0', 'k')
    body += ('exact hproduct_left', 'exists 0', 'apply zero_add', 'exact hk', 'split', 'exact hkb')
    body += _intro('i', 'hi')
    body += ('have ha : exists a. ' + _at('ab', 'ac', 'i', 'a', 'left_constant_product_A'),)
    body += _call('beta_at_exists', 'ab', 'ac', 'i') + ('cases ha',)
    point = _and(_at('hb', 'hc', 'i', 'r', 'left_constant_product_H'),
                 _coefficient('p', *K, *A, 'i', 'r', 'left_constant_product_coefficient'))
    body += ('have hr : exists r. ' + point,) + _call('hproduct_right_right_right', 'i')
    body += ('exact hi', 'cases hr', 'cases hr_witness', 'exists x', 'exists x1',
             'split', 'exact ha_witness', 'split', 'exact hr_witness_left')
    body += _call('prime_field_convolution_coefficient_left_constant',
                  'p', 'k', 'kb', 'kc', *A, 'i', 'x', 'x1')
    body += ('exact hk', 'exact hi', 'exact ha_witness', 'exact hkb')
    body += _call('matrix_rank_bounded_prefix_value', 'ab', 'ac', 'L', 'p', 'i', 'x')
    body += ('exact hproduct_right_left', 'exact hi', 'exact ha_witness', 'exact hr_witness_right')
    return spec(
        'prime_field_polynomial_left_constant_product_to_scale',
        _contract(PARAMETERS, (_at('kb', 'kc', '0', 'k', 'left_constant_product_K'), product),
                  _scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L', 'left_constant_product_scale')),
        ('matrix_rank_bounded_prefix_value', 'zero_add', 'beta_at_exists',
         'prime_field_convolution_coefficient_left_constant'), body,
        'An actual length-L product of a canonical left singleton and a length-L prefix yields the existing scalar graph, even when L=0. The scalar bound follows from the singleton rather than from vacuous output entries.',
    )


def _scale_to_product_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*PARAMETERS, 'hp', 'hK', 'hk', 'hs')
    bounds = _and(_coeff('p', *A, 'left_constant_recover_A'),
                  _coeff('p', *H, 'left_constant_recover_H'))
    body += ('have hbounds : ' + bounds,)
    body += _call('prime_field_polynomial_scale_bounded', 'p', 'k', 'ab', 'ac', 'hb', 'hc', 'L')
    body += ('exact hs', 'cases hbounds', 'split', 'exact hK', 'split', 'exact hbounds_left', 'split',
             'have hz : L=0 \\/ ~(L=0)')
    body += _call('eq_decidable', 'L', '0') + ('cases hz', 'left', 'split', 'right',
                                             'exact hz_left', 'exact hz_left', 'right', 'split', 'intro hbad')
    body += _call('succ_ne_zero', '0') + ('exact hbad', 'split', 'exact hz_right',
                                        'simp [add_succ_left,zero_add]')
    body += _intro('i', 'hi')
    point = _and(_at('ab', 'ac', 'i', 'a', 'left_constant_recover_source'),
                 _at('hb', 'hc', 'i', 'r', 'left_constant_recover_target'),
                 _mul('p', 'k', 'a', 'r', 'left_constant_recover_multiply'))
    body += ('have hv : exists a r. ' + point, 'cases hs') + _call('hs_right', 'i')
    body += ('exact hi', 'cases hv', 'cases hv_witness') + _parts('hv_witness_witness', 3)
    body += ('have hm : ' + _mul('p', 'k', 'x', 'x1', 'left_constant_recover_bounds'),
             'exact hv_witness_witness_right_right') + _parts('hm', 3)
    actual = _coefficient('p', *K, *A, 'i', 'r', 'left_constant_recover_actual')
    body += ('have hcoefficient : exists r. ' + actual,)
    body += _call('prime_field_convolution_coefficient_exists', 'p', *K, *A, 'i')
    body += ('intro hpzero',) + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hpzero', 'cases hcoefficient', 'have heq : x2=x1')
    body += _call('prime_field_multiply_functional', 'p', 'k', 'x', 'x2', 'x1')
    body += _call('prime_field_convolution_coefficient_left_constant',
                  'p', 'k', 'kb', 'kc', *A, 'i', 'x', 'x2')
    body += ('exact hk', 'exact hi', 'exact hv_witness_witness_left', 'exact hm_left',
             'exact hm_right_left', 'exact hcoefficient_witness', 'exact hv_witness_witness_right_right',
             'exists x1', 'split', 'exact hv_witness_witness_right_left')
    body += _rewrite_all('heq', _coefficient('p', *K, *A, 'i', 'x2', 'left_constant_recover_rewrite'),
                         'x2', 'hcoefficient_witness') + ('exact hcoefficient_witness',)
    return spec(
        'prime_field_polynomial_scale_to_left_constant_product',
        _contract(PARAMETERS, (
            _prime('p', 'left_constant_recover_prime'), _coeff('p', *K, 'left_constant_recover_K'),
            _at('kb', 'kc', '0', 'k', 'left_constant_recover_value'),
            _scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L', 'left_constant_recover_scale'),
        ), _convolution('p', *K, *A, *H, 'left_constant_recover_product')),
        ('prime_field_polynomial_scale_bounded', 'eq_decidable', 'succ_ne_zero',
         'add_succ_left', 'zero_add', 'prime_field_convolution_coefficient_exists',
         'prime_nonzero', 'prime_field_multiply_functional',
         'prime_field_convolution_coefficient_left_constant'), body,
        'Recover the genuine LEFT-constant convolution on the supplied scalar-output codes. Every needed antidiagonal sum is actually constructed and its residue identified; the empty proper-length branch is separate, including scalar zero and characteristic two.',
    )


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', *A)
    body = _intro(*parameters, 'hp', 'hk', 'ha')
    singleton = _and(_coeff('p', *K, 'left_constant_exists_K'),
                     _repeat('kb', 'kc', 'k', '1', 'left_constant_exists_repeat'))
    body += ('have hK : exists kb kc. ' + singleton,)
    body += _call('prime_field_polynomial_repeat_exists', 'p', 'k', '1')
    body += ('exact hk', 'cases hK', 'cases hK_witness', 'cases hK_witness_witness')
    scale = _scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L', 'left_constant_exists_scale')
    body += ('have hs : exists hb hc. ' + scale,)
    body += _call('prime_field_polynomial_scale_exists', 'p', 'k', 'ab', 'ac', 'L')
    body += ('intro hz',) + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hz', 'exact hk', 'exact ha', 'cases hs', 'cases hs_witness',
             'have hentry : ' + _at('x', 'x1', '0', 'k', 'left_constant_exists_head'))
    body += _call('hK_witness_witness_right', '0') + ('exists 0', 'apply zero_add',
             'exists x', 'exists x1', 'exists x2', 'exists x3', 'split',
             'exact hK_witness_witness_left', 'split', 'exact hentry', 'split',
             'exact hs_witness_witness')
    body += _call('prime_field_polynomial_scale_to_left_constant_product',
                  'p', 'k', 'x', 'x1', 'ab', 'ac', 'x2', 'x3', 'L')
    body += ('exact hp', 'exact hK_witness_witness_left', 'exact hentry', 'exact hs_witness_witness')
    result = 'exists kb kc hb hc. ' + _and(
        _coeff('p', *K, 'left_constant_exists_result_K'),
        _at('kb', 'kc', '0', 'k', 'left_constant_exists_result_head'),
        _scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L', 'left_constant_exists_result_scale'),
        _convolution('p', *K, *A, *H, 'left_constant_exists_result_product'))
    return spec(
        'prime_field_polynomial_left_constant_product_exists',
        _contract(parameters, (_prime('p', 'left_constant_exists_prime'),
                               _lt('k', 'p', 'left_constant_exists_scalar'),
                               _coeff('p', *A, 'left_constant_exists_input')), result),
        ('prime_field_polynomial_repeat_exists', 'prime_field_polynomial_scale_exists',
         'prime_nonzero', 'zero_add', 'prime_field_polynomial_scale_to_left_constant_product'), body,
        'Construct the canonical singleton and actual scalar output, then prove their genuine left-factor product using those same output codes. Empty source prefixes still require a canonical scalar and singleton; no beta-code uniqueness or gcd endpoint is claimed.',
    )


def make_prime_field_polynomial_left_constant_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_first_term_row(spec), _sum_row(spec), _coefficient_row(spec),
            _product_to_scale_row(spec), _scale_to_product_row(spec), _exists_row(spec))


__all__ = ['make_prime_field_polynomial_left_constant_candidate_theorems']
