"""Actual signed summand factorization at coprime divisor pairs.

The pair and the six source values are genuine witnesses. Their products are
canonical signed multiplication graphs, never multiplication of encodings.
No sum reindexing or multiplicative-convolution conclusion is assumed here.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_multiplicative_candidate import _multiplicative
from .coprime_divisor_decomposition_candidate import _cofactors, _pair
from .dirichlet_convolution_candidate import _entry
from .divisor_sum_table_candidate import _table_at
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _part, _parts, _rewrite,
)
from .signed_table_operations_candidate import _mul_code
from .squarefree_decomposition_candidate import _cop


def _scalar_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    reorder = _intro('a','b','c','d','ab','cd','ac','bd','out','hab','hcd','hac','hbd','hout')
    reorder += (f'have hk : exists k. ({_mul_code("c","bd","k","four_construct")})',)
    reorder += _call('signed_mul_total','c','bd') + ('cases hk',)
    reorder += (f'have hak : {_mul_code("a","x","out","four_first_rebracket")}',)
    reorder += _call('signed_mul_associative','a','c','bd','ac','x','out')
    reorder += ('exact hac','exact hout','exact hk_witness')
    reorder += (f'have hbk : {_mul_code("b","cd","x","four_middle_swap")}',)
    reorder += _call('signed_weighted_scalar_commute','b','d','c','bd','cd','x')
    reorder += ('exact hbd','exact hcd','exact hk_witness')
    reorder += (f'have hcb : {_mul_code("cd","b","x","four_middle_commute")}',)
    reorder += _call('signed_mul_commutative','b','cd','x') + ('exact hbk',)
    reorder += _call('signed_mul_commutative','cd','ab','out')
    reorder += _call('signed_weighted_scalar_commute','cd','b','a','x','ab','out')
    reorder += ('exact hcb','exact hab','exact hak')

    nonzero = _intro('a','b','z','hp','hz') + ('split','intro ha','apply hz')
    nonzero += _rewrite('ha',_mul_code('a','b','z','nonzero_left_rewrite'),'a','hp')
    nonzero += _call('signed_mul_functional','0','b','z','0') + ('exact hp',)
    nonzero += _call('signed_mul_zero_left','b') + ('intro hb','apply hz',)
    nonzero += _rewrite('hb',_mul_code('a','b','z','nonzero_right_rewrite'),'b','hp')
    nonzero += _call('signed_mul_functional','a','0','z','0') + ('exact hp',)
    nonzero += _call('signed_mul_zero_right','a')

    support = _intro('F','G','n','d','z','he','hz') + ('cases he','cases he_left',)
    support += _cases('he_left_right',3) + _parts('he_left_right_witness_witness_witness',4)
    support += ('split','exact he_left_left','exists x','exact he_left_right_witness_witness_witness_left',
                'cases he_right','exfalso','apply hz','exact he_right_right')
    return (
        spec('signed_mul_four_factor_interchange',
             'forall a b c d ab cd ac bd out. ' + ' -> '.join('('+p+')' for p in (
                 _mul_code('a','b','ab','four_ab'), _mul_code('c','d','cd','four_cd'),
                 _mul_code('a','c','ac','four_ac'), _mul_code('b','d','bd','four_bd'),
                 _mul_code('ac','bd','out','four_source'), _mul_code('ab','cd','out','four_target'))),
             ('signed_mul_total','signed_mul_associative','signed_weighted_scalar_commute','signed_mul_commutative'),
             reorder,
             'Reorder four actual signed factors by constructing the intermediate product and using checked associativity and commutativity.'),
        spec('signed_mul_nonzero_factors',
             f'forall a b z. ({_mul_code("a","b","z","nonzero_product")}) -> ~(z=0) -> (~(a=0) /\\ ~(b=0))',
             ('signed_mul_functional','signed_mul_zero_left','signed_mul_zero_right'), nonzero,
             'A nonzero actual signed product has two nonzero factors, by the signed zero laws and functionality.'),
        spec('dirichlet_convolution_entry_nonzero_support',
             f'forall F G n d z. ({_entry("F","G","n","d","z","support_entry")}) -> ~(z=0) -> '
             + _and('~(d=0)', _dvd('d','n','support_divisor')),
             (), support,
             'A genuinely nonzero convolution summand supplies a positive divisor and its actual quotient; omitted indices cannot enter the support.'),
    )


def _pair_premises(tag: str) -> tuple[str, ...]:
    return (
        _multiplicative('N','F',tag+'F'), _multiplicative('N','G',tag+'G'),
        '~(m=0)', '~(n=0)', _le('m*n','N',tag+'bound'), _cop('m','n',tag+'coprime'),
        _pair('m','n','d*e','d','e',tag+'pair'),
        _entry('F','G','m','d','left',tag+'left'), _entry('F','G','n','e','right',tag+'right'),
    )


def _pair_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    factor = _intro('N','F','G','m','n','d','e','left','right','total',
                    'hF','hG','hm','hn','hb','hc','hp','hl','hr','ht')
    factor += _parts('hF',4) + _parts('hG',4) + _parts('hp',5)
    factor += (f'have hq : exists u v. ({_cofactors("m","n","d*e","d","e","u","v","factor_cofactors")})',)
    factor += _call('coprime_divisor_factor_pair_cofactors','m','n','d*e','d','e')
    factor += ('exact hm','exact hn','exact hc','exact hp') + _cases('hq',2) + _parts('hq_witness_witness',11)
    q = lambda index: _part('hq_witness_witness',11,index)
    factor += ('have hmn : ~(m*n=0)','intro hz') + _call('mul_ne_zero','m','n')
    factor += ('exact hm','exact hn','exact hz','have hde : ~(d*e=0)','intro hz')
    factor += _call('mul_ne_zero','d','e') + ('exact hp_left','exact hp_right_left','exact hz')
    factor += (f'have hdb : {_le("d*e","N","factor_divisor_bound")}',)
    factor += _call('le_trans','d*e','m*n','N') + _call('divisor_le_nonzero','d*e','m*n')
    factor += ('exact hmn','exists x*x1','exact '+q(10),'exact hb')
    factor += (f'have hqb : {_le("x*x1","N","factor_quotient_bound")}',)
    factor += _call('le_trans','x*x1','m*n','N') + _call('divisor_le_nonzero','x*x1','m*n')
    factor += ('exact hmn','exists d*e','trans (d*e)*(x*x1)','exact '+q(10),'apply mul_comm','exact hb')
    for name, table, index, table_hyp in (
        ('hfd','F','d','hF_right_left'), ('hfe','F','e','hF_right_left'),
        ('hgu','G','x','hG_right_left'), ('hgv','G','x1','hG_right_left'),
        ('hfde','F','d*e','hF_right_left'), ('hguv','G','x*x1','hG_right_left'),
    ):
        factor += (f'have {name} : exists value. ({_table_at(table,index,"value",name+"actual")})',)
        factor += _call('signed_table_lookup_any','N',table,index) + ('exact '+table_hyp,'cases '+name)
    factor += _call('signed_mul_four_factor_interchange','x2','x4','x3','x5','left','right','x6','x7','total')
    factor += _call('dirichlet_convolution_entry_quotient_product','F','G','m','d','x','x2','x4','left')
    factor += ('exact hp_left','exact '+q(0),'exact hfd_witness','exact hgu_witness','exact hl')
    factor += _call('dirichlet_convolution_entry_quotient_product','F','G','n','e','x1','x3','x5','right')
    factor += ('exact hp_right_left','exact '+q(1),'exact hfe_witness','exact hgv_witness','exact hr')
    factor += _call('hF_right_right_right','d','e','x2','x3','x6')
    factor += ('exact hp_left','exact hp_right_left','exact hdb','exact '+q(6),
               'exact hfd_witness','exact hfe_witness','exact hfde_witness')
    factor += _call('hG_right_right_right','x','x1','x4','x5','x7')
    factor += ('exact '+q(2),'exact '+q(3),'exact hqb','exact '+q(9),
               'exact hgu_witness','exact hgv_witness','exact hguv_witness')
    factor += _call('dirichlet_convolution_entry_quotient_product','F','G','m*n','d*e','x*x1','x6','x7','total')
    factor += ('exact hde','exact '+q(10),'exact hfde_witness','exact hguv_witness','exact ht')

    construct = _intro('N','F','G','m','n','d','e','left','right','total',
                       'hF','hG','hm','hn','hb','hc','hp','hl','hr','ht')
    construct += _parts('hF',4) + _parts('hG',4)
    construct += (f'have hv : exists value. ({_entry("F","G","m*n","d*e","value","construct_target_entry")})',)
    construct += _call('dirichlet_convolution_entry_exists','F','G','m*n','d*e')
    construct += _call('signed_table_domain_resize','N','0','F') + ('exact hF_right_left',)
    construct += _call('signed_table_domain_resize','N','0','G') + ('exact hG_right_left','cases hv','have heq : total=x')
    construct += _call('signed_mul_functional','left','right','total','x') + ('exact ht',)
    construct += _call('dirichlet_multiplicative_pair_factorization','N','F','G','m','n','d','e','left','right','x')
    construct += ('exact hF','exact hG','exact hm','exact hn','exact hb','exact hc','exact hp','exact hl','exact hr','exact hv_witness')
    construct += _rewrite('heq',_entry('F','G','m*n','d*e','total','construct_result'),'total') + ('exact hv_witness',)
    return (
        spec('dirichlet_multiplicative_pair_factorization',
             'forall N F G m n d e left right total. ' + ' -> '.join('('+p+')' for p in (
                 *_pair_premises('factor_'), _entry('F','G','m*n','d*e','total','factor_target'),
                 _mul_code('left','right','total','factor_result'))),
             ('coprime_divisor_factor_pair_cofactors','mul_ne_zero','le_trans','divisor_le_nonzero','mul_comm',
              'signed_table_lookup_any','signed_mul_four_factor_interchange','dirichlet_convolution_entry_quotient_product'),
             factor,
             'On a genuine coprime divisor pair, construct positive cofactors and six signed lookups, apply both bounded multiplicative laws, and factor the actual target summand.'),
        spec('dirichlet_multiplicative_pair_entry',
             'forall N F G m n d e left right total. ' + ' -> '.join('('+p+')' for p in (
                 *_pair_premises('construct_'), _mul_code('left','right','total','construct_product'),
                 _entry('F','G','m*n','d*e','total','construct_result'))),
             ('dirichlet_convolution_entry_exists','signed_table_domain_resize','signed_mul_functional',
              'dirichlet_multiplicative_pair_factorization'), construct,
             'The product of the two actual pair summands is a genuine target convolution entry; its value is identified using a constructed target entry, never assumed.'),
    )


def make_dirichlet_multiplicative_entry_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _scalar_rows(spec) + _pair_rows(spec)


__all__ = ['make_dirichlet_multiplicative_entry_candidate_theorems']
