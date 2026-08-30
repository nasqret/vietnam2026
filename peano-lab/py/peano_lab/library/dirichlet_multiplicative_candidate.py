"""Full finite signed multiplicative closure of Dirichlet convolution.

Actual summand tables, a constructed Cartesian product and a native-beta map
feed the proved support-only reindexing theorem. The resulting normalized
table has the full coprime law through the inclusive positive prefix.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_multiplicative_candidate import _multiplicative
from .dirichlet_convolution_candidate import _convolution, _convolution_table
from .dirichlet_inverse_candidate import _inverse
from .dirichlet_multiplicative_support_candidate import _data, _length
from .divisor_mask_candidate import _positive_equal
from .divisor_sum_table_candidate import _signed_sum, _table_at
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _le, _part, _parts, _rewrite,
)
from .signed_table_operations_candidate import _mul_code
from .squarefree_decomposition_candidate import _cop


def _scalar_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro('N','F','G','m','n','a','b','c','hF','hG','hm','hn','hb','hc','hsm','hsn','hsc')
    for hypothesis in ('hsm','hsn','hsc'):
        body += ('cases '+hypothesis,'cases '+hypothesis+'_right','cases '+hypothesis+'_right_witness')
    body += (f'have hd : exists T r s. ({_data("N","F","G","m","n","x","x1","T","x2","r","s","scalar_actual_data")})',)
    body += _call('dirichlet_coprime_product_data_construct','N','F','G','m','n','x','x1','x2')
    body += ('exact hF','exact hG','exact hm','exact hn','exact hb','exact hc',
             'exact hsm_right_witness_left','exact hsn_right_witness_left','exact hsc_right_witness_left')
    body += _cases('hd',3) + _parts('hd_witness_witness_witness',11)
    data = 'hd_witness_witness_witness'
    cart = _part(data,11,8)
    body += _parts(cart,4)
    body += (f'have hv : exists value. ({_signed_sum("x3",_length("m","n"),"value","scalar_product_sum")})',)
    body += _call('arithmetic_signed_sum_exists',_length('m','n'),'x3',_length('m','n'))
    body += ('exact '+_part(cart,4,2),'cases hv','have heq : x6=c')
    body += _call('signed_support_reindex_sum_equal','x3','x2','x4','x5',_length('m','n'),'S (m*n)','x6','c')
    body += _call('dirichlet_coprime_grid_support_reindex','N','F','G','m','n','x','x1','x3','x2','x4','x5')
    body += ('exact '+data,'exact hv_witness','exact hsc_right_witness_right')
    body += (f'have hp : {_mul_code("a","b","x6","scalar_result_before_transport")}',)
    body += _call('signed_cartesian_product_prefix_sum','x','x1','x3','S m','S n','a','b','x6')
    body += ('exact '+cart,'exact hsm_right_witness_right','exact hsn_right_witness_right','exact hv_witness')
    body += _rewrite('heq',_mul_code('a','b','x6','scalar_result_transport'),'x6','hp') + ('exact hp',)
    clauses = (
        _multiplicative('N','F','scalar_first'), _multiplicative('N','G','scalar_second'),
        '~(m=0)', '~(n=0)', _le('m*n','N','scalar_bound'), _cop('m','n','scalar_coprime'),
        _convolution('F','G','m','a','scalar_left_sum'), _convolution('F','G','n','b','scalar_right_sum'),
        _convolution('F','G','m*n','c','scalar_target_sum'), _mul_code('a','b','c','scalar_result'))
    return (spec(
        'dirichlet_convolution_multiplicative_values',
        'forall N F G m n a b c. '+' -> '.join('('+clause+')' for clause in clauses),
        ('dirichlet_coprime_product_data_construct','arithmetic_signed_sum_exists','signed_support_reindex_sum_equal',
         'dirichlet_coprime_grid_support_reindex','signed_cartesian_product_prefix_sum'), body,
        'The actual convolution values at positive coprime m,n multiply to the actual value at mn, using genuine divisor-pair support reindexing and only in-prefix multiplicativity.'),)


def _table_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro('N','F','G','H','hF','hG','hc') + _parts('hF',4) + _parts('hG',4) + _parts('hc',4)
    body += ('split','exact hF_left','split','exact hc_right_right_left','split')
    body += (f'have h1 : exists value. {_and(_table_at("H","1","value","table_one_lookup"),_convolution("F","G","1","value","table_one_sum"))}',)
    body += _call('dirichlet_convolution_table_lookup','N','F','G','H','1') + ('exact hc',)
    body += _call('succ_ne_zero','0') + _call('one_le_of_ne_zero','N') + ('exact hF_left','cases h1','cases h1_witness')
    one_convolution = _convolution('F','G','1','x','table_one_equivalence_sum')
    one_product = _mul_code('2','2','x','table_one_equivalence_product')
    body += (f'have he : {_and(f"({one_convolution}) -> ({one_product})",f"({one_product}) -> ({one_convolution})")}',)
    body += _call('dirichlet_convolution_at_one_iff','F','G','2','2','x')
    body += ('exact hF_right_right_left','exact hG_right_right_left','cases he','have hx : x=2')
    body += _call('signed_mul_functional','2','2','x','2')
    body += ('apply he_left','exact h1_witness_right') + _call('signed_mul_one_left','2')
    body += _rewrite('hx',_table_at('H','1','x','table_normalization_transport'),'x','h1_witness_left') + ('exact h1_witness_left',)
    body += _intro('m','n','a','b','c','hm','hn','hb','hcop','ha','hsecond','hthird')
    body += _call('dirichlet_convolution_multiplicative_values','N','F','G','m','n','a','b','c')
    body += ('exact hF','exact hG','exact hm','exact hn','exact hb','exact hcop')
    body += _call('hc_right_right_right','m','a') + ('exact hm',)
    body += _call('le_trans','m','m*n','N') + _call('le_mul_of_one_le_right','m','n')
    body += _call('one_le_of_ne_zero','n') + ('exact hn','exact hb','exact ha')
    body += _call('hc_right_right_right','n','b') + ('exact hn',)
    body += _call('le_trans','n','m*n','N') + _call('le_mul_of_one_le_left','m','n')
    body += _call('one_le_of_ne_zero','m') + ('exact hm','exact hb','exact hsecond')
    body += _call('hc_right_right_right','m*n','c') + ('intro hzero',) + _call('mul_ne_zero','m','n')
    body += ('exact hm','exact hn','exact hzero','exact hb','exact hthird')

    exists = _intro('N','F','G','hF','hG') + _parts('hF',4) + _parts('hG',4)
    exists += (f'have hc : exists H. ({_convolution_table("N","F","G","H","closure_actual_table")})',)
    exists += _call('dirichlet_convolution_table_exists','N','F','G')
    exists += ('exact hF_right_left','exact hG_right_left','cases hc','exists x','split','exact hc_witness','split')
    exists += _call('dirichlet_convolution_multiplicative_table','N','F','G','x') + ('exact hF','exact hG','exact hc_witness')
    exists += _intro('K','hK') + _call('dirichlet_convolution_table_extensional','N','F','G','x','K')
    exists += ('exact hc_witness','exact hK')

    inverse = _intro('N','F','w','hm') + _parts('hm',4)
    inverse += _call('dirichlet_inverse_from_unit_at_one','N','F','w')
    inverse += ('exact hm_right_left','left','exact hm_right_right_left')
    return (
        spec('dirichlet_convolution_multiplicative_table',
             f'forall N F G H. ({_multiplicative("N","F","table_first")}) -> '
             f'({_multiplicative("N","G","table_second")}) -> ({_convolution_table("N","F","G","H","table_convolution")}) -> '
             f'({_multiplicative("N","H","table_result")})',
             ('dirichlet_convolution_table_lookup','succ_ne_zero','one_le_of_ne_zero','dirichlet_convolution_at_one_iff',
              'signed_mul_functional','signed_mul_one_left','dirichlet_convolution_multiplicative_values',
              'le_trans','le_mul_of_one_le_right','le_mul_of_one_le_left','mul_ne_zero'), body,
             'An actual convolution table of two normalized multiplicative signed prefixes is itself normalized and multiplicative on every positive coprime product through the inclusive bound.'),
        spec('dirichlet_convolution_multiplicative_exists_unique',
             f'forall N F G. ({_multiplicative("N","F","exists_first")}) -> '
             f'({_multiplicative("N","G","exists_second")}) -> exists H. '+_and(
                 _convolution_table('N','F','G','H','exists_convolution'), _multiplicative('N','H','exists_multiplicative'),
                 f'forall K. ({_convolution_table("N","F","G","K","exists_other")}) -> '
                 f'({_positive_equal("H","K","N","exists_unique_positive")})'),
             ('dirichlet_convolution_table_exists','dirichlet_convolution_multiplicative_table',
              'dirichlet_convolution_table_extensional'), exists,
             'Construct a genuine multiplicative convolution table and prove uniqueness of its represented positive values, without identifying arbitrary zero values or table encodings.'),
        spec('dirichlet_multiplicative_function_invertible',
             f'forall N F w. ({_multiplicative("N","F","invertible_input")}) -> exists G. '+_and(
                 _inverse('N','F','G','invertible_result'), _table_at('G','0','w','invertible_prescribed_zero')),
             ('dirichlet_inverse_from_unit_at_one',), inverse,
             'Positive-one normalization gives an actual two-sided finite Dirichlet inverse with any prescribed zeroth value; this corollary does not assert multiplicativity of the inverse.'),
    )


def make_dirichlet_multiplicative_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _scalar_rows(spec) + _table_rows(spec)


__all__ = ['make_dirichlet_multiplicative_candidate_theorems']
