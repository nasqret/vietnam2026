"""Genuine signed weighted sums and their constructive linearity laws.

A weighted sum first constructs a pointwise signed-product table and then its
actual two-natural-trace signed prefix sum.  The graph contains no linearity,
divisor cancellation, rectangular rearrangement, or inversion conclusion.
All outputs are canonical signed values; table representations are not unique.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at
from .prime_valuation_support_candidate import _and, _call, _intro, _part, _parts, _public, _rewrite
from .signed_table_operations_candidate import _mul_code, _pointwise_add, _pointwise_multiply, _scalar


def _weighted(W: str, F: str, l: str, z: str, tag: str) -> str:
    H='sws_product_table_'+tag
    return f'exists {H}. '+_and(_pointwise_multiply(W,F,H,l,tag+'products'),_signed_sum(H,l,z,tag+'sum'))


def signed_weighted_sum_relation(W: str, F: str, l: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """An actual product table followed by its actual signed sum on i<l."""
    return _public(_weighted,(W,F,l,z),tag=tag,variables=variables)


def _value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    exists=_intro('l','W','F','hW','hF')+(f"have hp : exists H. ({_pointwise_multiply('W','F','H','l','weighted_product_exists')})",)
    exists+=_call('signed_table_multiply_exists','l','W','F')+('exact hW','exact hF','cases hp',
             f"have hs : exists z. ({_signed_sum('x','l','z','weighted_sum_exists')})")
    exists+=_call('arithmetic_signed_sum_exists','l','x','l')+_parts('hp_witness',4)
    exists+=('exact hp_witness_right_right_left','cases hs','exists x1','exists x','split','exact hp_witness','exact hs_witness')
    functional=_intro('W','F','l','a','b','ha','hb')+('cases ha','cases ha_witness','cases hb','cases hb_witness')
    functional+=_call('divisor_signed_sum_extensional','x','x1','l','a','b')
    functional+=_call('signed_table_multiply_extensional_unique','W','F','x','x1','l')
    functional+=('exact ha_witness_left','exact hb_witness_left','exact ha_witness_right','exact hb_witness_right')
    unique=_intro('l','W','F','hW','hF')+(f"have hs : exists z. ({_weighted('W','F','l','z','weighted_unique_construct')})",)
    unique+=_call('signed_weighted_sum_exists','l','W','F')+('exact hW','exact hF','cases hs','exists x','split','exact hs_witness','intro z','intro hz')
    unique+=_call('signed_weighted_sum_functional','W','F','l','z','x')+('exact hz','exact hs_witness')
    empty=_intro('W','F','z','h')+('cases h','cases h_witness')+_call('divisor_signed_sum_empty_value','x','z')+('exact h_witness_right',)
    zero=_intro('W','F','hW','hF')+(f"have hs : exists z. ({_weighted('W','F','0','z','weighted_zero_construct')})",)
    zero+=_call('signed_weighted_sum_exists','0','W','F')+('exact hW','exact hF','cases hs','have heq : x = 0')
    zero+=_call('signed_weighted_sum_empty_value','W','F','x')+('exact hs_witness',)
    zero+=_rewrite('heq',_weighted('W','F','0','x','weighted_zero_rewrite'),'x','hs_witness')+('exact hs_witness',)
    return (
        spec('signed_weighted_sum_exists',
             f"forall l W F. ({_table('l','W','weighted_exists_weights')}) -> ({_table('l','F','weighted_exists_values')}) -> exists z. ({_weighted('W','F','l','z','weighted_exists_result')})",
             ('signed_table_multiply_exists','arithmetic_signed_sum_exists'),exists,
             'Construct the actual pointwise product table and both natural prefix-sum histories, then their canonical signed weighted-sum value.'),
        spec('signed_weighted_sum_functional',
             f"forall W F l a b. ({_weighted('W','F','l','a','weighted_unique_first')}) -> ({_weighted('W','F','l','b','weighted_unique_second')}) -> a = b",
             ('signed_table_multiply_extensional_unique','divisor_signed_sum_extensional'),functional,
             'Every genuine product-table witness gives the same canonical signed weighted sum, even when its raw beta codes and representatives differ.'),
        spec('signed_weighted_sum_exists_unique',
             f"forall l W F. ({_table('l','W','weighted_total_weights')}) -> ({_table('l','F','weighted_total_values')}) -> exists z. "
             +_and(_weighted('W','F','l','z','weighted_total_result'),f"forall u. ({_weighted('W','F','l','u','weighted_total_compare')}) -> u = z"),
             ('signed_weighted_sum_exists','signed_weighted_sum_functional'),unique,
             'Every two valid input tables have a genuinely constructed, literally unique canonical signed weighted-sum value.'),
        spec('signed_weighted_sum_empty_value',
             f"forall W F z. ({_weighted('W','F','0','z','weighted_empty')}) -> z = 0",
             ('divisor_signed_sum_empty_value',),empty,
             'The empty weighted sum is canonical zero, regardless of the unused endpoint values of its valid table witnesses.'),
        spec('signed_weighted_sum_empty_exists',
             f"forall W F. ({_table('0','W','weighted_empty_weights')}) -> ({_table('0','F','weighted_empty_values')}) -> ({_weighted('W','F','0','0','weighted_empty_result')})",
             ('signed_weighted_sum_exists','signed_weighted_sum_empty_value'),zero,
             'Construct the real zero-length product table and signed fold; its output is then proved to be zero.'),
    )


def _lookups(sources: tuple[tuple[str,str,int,int],...], tag: str) -> tuple[str,...]:
    body=()
    for index,(table,hyp,count,part) in enumerate(sources):
        body+=(f'have he{index} : exists z. ({_table_at(table,"i","z",tag+str(index))})',)
        body+=_call('signed_table_lookup_any','l',table,'i')+_parts(hyp,count)
        body+=(f'exact {_part(hyp,count,part)}',f'cases he{index}')
    return body


def _pointwise_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    add=_intro('l','W','F','G','H','P','Q','R','hs','hp','hq','hr')
    for hyp in ('hp','hq','hr'):
        add+=('split',)+_parts(hyp,4)+(f'exact {hyp}_right_right_left',)
    add+=_intro('i','hi')+_lookups((('W','hp',4,0),('F','hs',4,0),('G','hs',4,1),('H','hs',4,2),
                                   ('P','hp',4,2),('Q','hq',4,2),('R','hr',4,2)),'weighted_distributive_lookup')
    add+=('exists x4','exists x5','exists x6','split','exact he4_witness','split','exact he5_witness','split','exact he6_witness')
    add+=_call('signed_mul_left_distributive','x','x1','x2','x3','x4','x5','x6')
    add+=_call('signed_table_add_lookup','F','G','H','l','i','x1','x2','x3')
    add+=('exact hs','exact hi','exact he1_witness','exact he2_witness','exact he3_witness')
    for left,right,out,hyp,a,b,c in (('W','F','P','hp','x','x1','x4'),('W','G','Q','hq','x','x2','x5'),('W','H','R','hr','x','x3','x6')):
        add+=_call('signed_table_multiply_lookup',left,right,out,'l','i',a,b,c)+(f'exact {hyp}','exact hi')
        add+=tuple('exact he'+str(int(value[1:] or '0'))+'_witness' for value in (a,b,c))

    commute=_intro('a','b','c','ab','cb','out','hab','hcb','hout')
    commute+=(f"have hw : exists w. ({_mul_code('a','cb','w','scalar_commute_construct')})",)
    commute+=_call('signed_mul_total','a','cb')+('cases hw','have heq : x = out')
    commute+=_call('signed_mul_functional','c','ab','x','out')
    commute+=_call('signed_mul_associative','c','b','a','cb','ab','x')+('exact hcb',)
    commute+=_call('signed_mul_commutative','a','cb','x')+('exact hw_witness',)
    commute+=_call('signed_mul_commutative','a','b','ab')+('exact hab','exact hout')
    commute+=_rewrite('heq',_mul_code('a','cb','x','scalar_commute_rewrite'),'x','hw_witness')+('exact hw_witness',)

    scalar=_intro('l','a','W','F','G','P','Q','hs','hp','hq')
    for hyp in ('hp','hq'):
        scalar+=('split',)+_parts(hyp,4)+(f'exact {hyp}_right_right_left',)
    scalar+=_intro('i','hi')+_lookups((('W','hp',4,0),('F','hs',3,0),('G','hs',3,1),('P','hp',4,2),('Q','hq',4,2)),'weighted_scalar_lookup')
    scalar+=('exists x3','exists x4','split','exact he3_witness','split','exact he4_witness')
    scalar+=_call('signed_weighted_scalar_commute','a','x1','x','x2','x3','x4')
    scalar+=_call('signed_table_scalar_lookup','a','F','G','l','i','x1','x2')+('exact hs','exact hi','exact he1_witness','exact he2_witness')
    scalar+=_call('signed_table_multiply_lookup','W','F','P','l','i','x','x1','x3')+('exact hp','exact hi','exact he0_witness','exact he1_witness','exact he3_witness')
    scalar+=_call('signed_table_multiply_lookup','W','G','Q','l','i','x','x2','x4')+('exact hq','exact hi','exact he0_witness','exact he2_witness','exact he4_witness')
    return (
        spec('signed_table_weighted_add_distributive',
             f"forall l W F G H P Q R. ({_pointwise_add('F','G','H','l','weighted_add_inputs')}) -> "
             f"({_pointwise_multiply('W','F','P','l','weighted_add_first')}) -> ({_pointwise_multiply('W','G','Q','l','weighted_add_second')}) -> "
             f"({_pointwise_multiply('W','H','R','l','weighted_add_third')}) -> ({_pointwise_add('P','Q','R','l','weighted_add_outputs')})",
             ('signed_table_lookup_any','signed_mul_left_distributive','signed_table_add_lookup','signed_table_multiply_lookup'),add,
             'The actual pointwise product tables distribute over a witnessed pointwise addition; every entry is constructed and checked against canonical signed scalar distributivity.'),
        spec('signed_weighted_scalar_commute',
             f"forall a b c ab cb out. ({_mul_code('a','b','ab','weighted_commute_first')}) -> ({_mul_code('c','b','cb','weighted_commute_second')}) -> "
             f"({_mul_code('c','ab','out','weighted_commute_output')}) -> ({_mul_code('a','cb','out','weighted_commute_target')})",
             ('signed_mul_total','signed_mul_functional','signed_mul_associative','signed_mul_commutative'),commute,
             'Construct the reordered product and identify its canonical value by signed multiplication associativity, commutativity and functionality.'),
        spec('signed_table_weighted_scalar_commute',
             f"forall l a W F G P Q. ({_scalar('a','F','G','l','weighted_scale_input')}) -> "
             f"({_pointwise_multiply('W','F','P','l','weighted_scale_first')}) -> ({_pointwise_multiply('W','G','Q','l','weighted_scale_second')}) -> "
             f"({_scalar('a','P','Q','l','weighted_scale_result')})",
             ('signed_table_lookup_any','signed_weighted_scalar_commute','signed_table_scalar_lookup','signed_table_multiply_lookup'),scalar,
             'An arbitrary signed scalar commutes with an actual table of pointwise weighted products, with the same strict prefix window and actual table witnesses.'),
    )


def _linearity_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    add=_intro('l','W','F','G','H','a','b','c','hpoint','hF','hG','hH')
    for hyp in ('hF','hG','hH'):
        add+=('cases '+hyp,'cases '+hyp+'_witness')
    add+=_call('signed_prefix_sum_pointwise_add','l','x','x1','x2','a','b','c')
    add+=_call('signed_table_weighted_add_distributive','l','W','F','G','H','x','x1','x2')
    add+=('exact hpoint','exact hF_witness_left','exact hG_witness_left','exact hH_witness_left',
          'exact hF_witness_right','exact hG_witness_right','exact hH_witness_right')
    scalar=_intro('l','a','W','F','G','b','c','hpoint','hF','hG')
    for hyp in ('hF','hG'):
        scalar+=('cases '+hyp,'cases '+hyp+'_witness')
    scalar+=_call('signed_prefix_sum_scalar_multiply','l','a','x','x1','b','c')
    scalar+=_call('signed_table_weighted_scalar_commute','l','a','W','F','G','x','x1')
    scalar+=('exact hpoint','exact hF_witness_left','exact hG_witness_left','exact hF_witness_right','exact hG_witness_right')
    return (
        spec('signed_weighted_sum_add_linearity',
             f"forall l W F G H a b c. ({_pointwise_add('F','G','H','l','weighted_linearity_input')}) -> "
             f"({_weighted('W','F','l','a','weighted_linearity_first')}) -> ({_weighted('W','G','l','b','weighted_linearity_second')}) -> "
             f"({_weighted('W','H','l','c','weighted_linearity_output')}) -> ({_add_code('a','b','c','weighted_linearity_result')})",
             ('signed_table_weighted_add_distributive','signed_prefix_sum_pointwise_add'),add,
             'Actual signed weighted sums are additive in their value table, by genuine pointwise product distributivity and the proved prefix-sum induction.'),
        spec('signed_weighted_sum_scalar_linearity',
             f"forall l a W F G b c. ({_scalar('a','F','G','l','weighted_scalar_input')}) -> "
             f"({_weighted('W','F','l','b','weighted_scalar_first')}) -> ({_weighted('W','G','l','c','weighted_scalar_output')}) -> "
             f"({_mul_code('a','b','c','weighted_scalar_result')})",
             ('signed_table_weighted_scalar_commute','signed_prefix_sum_scalar_multiply'),scalar,
             'Actual signed weighted sums commute with an arbitrary signed scalar; negative values, zero scalars and the empty prefix are included.'),
    )


def make_signed_weighted_sum_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _value_rows(spec)+_pointwise_rows(spec)+_linearity_rows(spec)


__all__=['signed_weighted_sum_relation','make_signed_weighted_sum_candidate_theorems']
