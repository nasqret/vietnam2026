"""Genuine finite Dirichlet associativity from a constructed factor grid.

All intermediate and output functions are actual signed beta tables.  The
pointwise result is equality of canonical signed values on 0<n<=N; no claim
is made about equality of table codes or their unrelated values at zero.
"""

from __future__ import annotations

from typing import Any, Callable

from .dirichlet_convolution_candidate import _convolution, _convolution_table
from .divisor_mask_candidate import _positive_equal
from .divisor_sum_table_candidate import _table
from .prime_valuation_support_candidate import _and, _call, _intro, _le, _part, _parts


def make_dirichlet_associativity_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    scalar=_intro('N','F','G','H','A','B','n','u','v','hA','hB','hn','hN','hu','hv')
    scalar+=_call('dirichlet_convolution_fubini_interchange','N','H','G','F','A','B','n','u','v')+('exact hA',)
    scalar+=_call('dirichlet_convolution_table_commutative','N','G','H','B')
    scalar+=('exact hB','exact hn','exact hN')
    scalar+=_call('dirichlet_convolution_sum_swap','N','A','H','n','u')
    scalar+=_parts('hA',4)+('exact hA_right_right_left',)+_parts('hB',4)+('exact hB_right_left','exact hN','exact hu','exact hv')

    tables=_intro('N','F','G','H','A','B','L','R','hA','hB','hL','hR','n','u','v','hn','hN','hu','hv')
    tables+=_call('dirichlet_convolution_associative','N','F','G','H','A','B','n','u','v')
    tables+=('exact hA','exact hB','exact hn','exact hN')
    for hyp,value,lookup in (('hL','u','hu'),('hR','v','hv')):
        tables+=_parts(hyp,4)+_call(_part(hyp,4,3),'n',value)+('exact hn','exact hN','exact '+lookup)

    exists=_intro('N','F','G','H','hF','hG','hH')
    exists+=(f'have hA : exists A. ({_convolution_table("N","F","G","A","assoc_construct_A")})',)
    exists+=_call('dirichlet_convolution_table_exists','N','F','G')+('exact hF','exact hG','cases hA')
    exists+=(f'have hB : exists B. ({_convolution_table("N","G","H","B","assoc_construct_B")})',)
    exists+=_call('dirichlet_convolution_table_exists','N','G','H')+('exact hG','exact hH','cases hB')
    exists+=(f'have hL : exists L. ({_convolution_table("N","x","H","L","assoc_construct_L")})',)
    exists+=_call('dirichlet_convolution_table_exists','N','x','H')+_parts('hA_witness',4)+('exact hA_witness_right_right_left','exact hH','cases hL')
    exists+=(f'have hR : exists R. ({_convolution_table("N","F","x1","R","assoc_construct_R")})',)
    exists+=_call('dirichlet_convolution_table_exists','N','F','x1')+('exact hF',)+_parts('hB_witness',4)+('exact hB_witness_right_right_left','cases hR')
    exists+=('exists x','exists x1','exists x2','exists x3','split','exact hA_witness','split','exact hB_witness',
             'split','exact hL_witness','split','exact hR_witness')
    exists+=_call('dirichlet_convolution_tables_associative','N','F','G','H','x','x1','x2','x3')
    exists+=('exact hA_witness','exact hB_witness','exact hL_witness','exact hR_witness')
    return (
        spec('dirichlet_convolution_associative',
             f'forall N F G H A B n u v. ({_convolution_table("N","F","G","A","assoc_FG")}) -> '
             f'({_convolution_table("N","G","H","B","assoc_GH")}) -> ~(n=0) -> ({_le("n","N","assoc_domain")}) -> '
             f'({_convolution("A","H","n","u","assoc_left")}) -> ({_convolution("F","B","n","v","assoc_right")}) -> u=v',
             ('dirichlet_convolution_fubini_interchange','dirichlet_convolution_table_commutative','dirichlet_convolution_sum_swap'),scalar,
             'Actual finite Dirichlet convolution is associative at each positive in-domain input, by genuine factor-grid Fubini and the checked divisor-complement commutativity.'),
        spec('dirichlet_convolution_tables_associative',
             f'forall N F G H A B L R. ({_convolution_table("N","F","G","A","assoc_tables_A")}) -> '
             f'({_convolution_table("N","G","H","B","assoc_tables_B")}) -> ({_convolution_table("N","A","H","L","assoc_tables_L")}) -> '
             f'({_convolution_table("N","F","B","R","assoc_tables_R")}) -> ({_positive_equal("L","R","N","assoc_tables_equal")})',
             ('dirichlet_convolution_associative',),tables,
             'Any genuine output tables for the two parenthesizations agree on precisely 0<n<=N; no equality of encodings or arbitrary zero values is asserted.'),
        spec('dirichlet_convolution_associative_tables_exists',
             f'forall N F G H. ({_table("N","F","assoc_exists_F")}) -> ({_table("N","G","assoc_exists_G")}) -> ({_table("N","H","assoc_exists_H")}) -> exists A B L R. '
             +_and(_convolution_table('N','F','G','A','assoc_exists_A'),_convolution_table('N','G','H','B','assoc_exists_B'),
                   _convolution_table('N','A','H','L','assoc_exists_L'),_convolution_table('N','F','B','R','assoc_exists_R'),
                   _positive_equal('L','R','N','assoc_exists_equal')),
             ('dirichlet_convolution_table_exists','dirichlet_convolution_tables_associative'),exists,
             'Construct all four actual intermediate/output beta tables and prove their positive-domain associativity, including the vacuous N=0 boundary.'),
    )


__all__=['make_dirichlet_associativity_candidate_theorems']
