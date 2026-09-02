"""Constructive linearity of actual signed beta-prefix sums.

Pointwise hypotheses are witnessed arithmetic-table graphs, not the desired
sum identities.  Ordinary induction follows the existing signed successor
decomposition and reconstructs the unchanged canonical SignedAdd/SignedMul
graphs.  In particular, zero-length sums are genuinely canonical zero.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table_at
from .prime_valuation_support_candidate import _and, _call, _cases, _intro, _parts, _rewrite
from .signed_table_operations_candidate import _mul_code, _pointwise_add, _scalar


def _decompose(F: str, l: str, z: str, tag: str) -> str:
    a,b='ssl_prefix_'+tag,'ssl_entry_'+tag
    return f'exists {a} {b}. '+_and(_signed_sum(F,l,a,tag+'sum'),_table_at(F,l,b,tag+'entry'),_add_code(a,b,z,tag+'addition'))


def _scalar_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    reverse=_intro('a','b','c','ab','bc','out','hab','hbc','hout')
    reverse+=(f"have hw : exists w. ({_add_code('ab','c','w','reassociate_construct')})",)
    reverse+=_call('signed_add_total','ab','c')+('cases hw','have heq : x = out')
    reverse+=_call('signed_add_functional','a','bc','x','out')
    reverse+=_call('signed_add_associative','a','b','c','ab','bc','x')+('exact hab','exact hw_witness','exact hbc','exact hout')
    reverse+=_rewrite('heq',_add_code('ab','c','x','reassociate_rewrite'),'x','hw_witness')+('exact hw_witness',)

    medial=_intro('a','b','c','d','ab','cd','ac','bd','out','hab','hcd','hac','hbd','hout')
    medial+=(f"have hcy : exists w. ({_add_code('c','bd','w','medial_middle')})",)
    medial+=_call('signed_add_total','c','bd')+('cases hcy',f"have hright : {_add_code('b','cd','x','medial_right')}")
    medial+=_call('signed_add_associative','b','d','c','bd','cd','x')+('exact hbd',)
    medial+=_call('signed_add_commutative','c','bd','x')+('exact hcy_witness',)
    medial+=_call('signed_add_commutative','c','d','cd')+('exact hcd',f"have hfull : {_add_code('a','x','out','medial_full')}")
    medial+=_call('signed_add_associative','a','c','bd','ac','x','out')+('exact hac','exact hout','exact hcy_witness')
    medial+=_call('signed_table_add_reassociate','a','b','cd','ab','x','out')+('exact hab','exact hright','exact hfull')

    scalar=_intro('a','b','c','bc','ab','ac','out','hbc','hab','hac','hout')
    scalar+=(f"have hw : exists w. ({_mul_code('a','bc','w','distributive_construct')})",)
    scalar+=_call('signed_mul_total','a','bc')+('cases hw','have heq : x = out')
    scalar+=_call('signed_add_functional','ab','ac','x','out')
    scalar+=_call('signed_mul_left_distributive','a','b','c','bc','ab','ac','x')+('exact hbc','exact hab','exact hac','exact hw_witness','exact hout')
    scalar+=_rewrite('heq',_mul_code('a','bc','x','distributive_rewrite'),'x','hw_witness')+('exact hw_witness',)
    return (
        spec('signed_table_add_reassociate',
             f"forall a b c ab bc out. ({_add_code('a','b','ab','reverse_ab')}) -> ({_add_code('b','c','bc','reverse_bc')}) -> ({_add_code('a','bc','out','reverse_out')}) -> ({_add_code('ab','c','out','reverse_target')})",
             ('signed_add_total','signed_add_functional','signed_add_associative'),reverse,
             'Constructing the other parenthesization and applying literal signed-add functionality proves reverse associativity.'),
        spec('signed_table_add_medial',
             f"forall a b c d ab cd ac bd out. ({_add_code('a','b','ab','medial_ab')}) -> ({_add_code('c','d','cd','medial_cd')}) -> "
             f"({_add_code('a','c','ac','medial_ac')}) -> ({_add_code('b','d','bd','medial_bd')}) -> ({_add_code('ac','bd','out','medial_out')}) -> ({_add_code('ab','cd','out','medial_target')})",
             ('signed_add_total','signed_add_associative','signed_add_commutative','signed_table_add_reassociate'),medial,
             'The actual four canonical signed summands may be regrouped across two prefix/last-entry pairs, with a genuinely constructed intermediate sum.'),
        spec('signed_table_scalar_add_intro',
             f"forall a b c bc ab ac out. ({_add_code('b','c','bc','scalar_intro_sum')}) -> ({_mul_code('a','b','ab','scalar_intro_left')}) -> "
             f"({_mul_code('a','c','ac','scalar_intro_right')}) -> ({_add_code('ab','ac','out','scalar_intro_result')}) -> ({_mul_code('a','bc','out','scalar_intro_target')})",
             ('signed_mul_total','signed_mul_left_distributive','signed_add_functional'),scalar,
             'An actual sum of the two scalar products is the actual scalar multiple of the sum; no product witness or distributivity oracle is assumed.'),
    )


def _linearity_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    add=('induction l',)+_intro('F','G','H','a','b','c','hpoint','hF','hG','hH')
    for table,value,hyp in (('F','a','hF'),('G','b','hG'),('H','c','hH')):
        add+=(f'have h{value} : {value} = 0',)+_call('divisor_signed_sum_empty_value',table,value)+(f'exact {hyp}',)
    add+=_rewrite('ha',_add_code('a','b','c','add_base_a'),'a')
    add+=_rewrite('hb',_add_code('0','b','c','add_base_b'),'b')
    add+=_rewrite('hc',_add_code('0','0','c','add_base_c'),'c')+_call('signed_add_zero_left','0')
    add+=_intro('F','G','H','a','b','c','hpoint','hF','hG','hH')
    for table,value,hyp in (('F','a','hF'),('G','b','hG'),('H','c','hH')):
        name='hd'+table
        add+=(f'have {name} : {_decompose(table,"l",value,"add_step_"+table)}',)
        add+=_call('divisor_signed_sum_successor_decompose',table,'l',value)+(f'exact {hyp}',)+_cases(name,2)+_parts(name+'_witness_witness',3)
    add+=(f"have hp : {_add_code('x','x2','x4','add_prefix')}",)
    add+=_call('IH','F','G','H','x','x2','x4')+_call('signed_table_add_restrict','F','G','H','l')
    add+=('exact hpoint','exact hdF_witness_witness_left','exact hdG_witness_witness_left','exact hdH_witness_witness_left',
          f"have he : {_add_code('x1','x3','x5','add_last')}")
    add+=_call('signed_table_add_lookup','F','G','H','S l','l','x1','x3','x5')+('exact hpoint',)+_call('le_refl','S l')
    add+=('exact hdF_witness_witness_right_left','exact hdG_witness_witness_right_left','exact hdH_witness_witness_right_left')
    add+=_call('signed_table_add_medial','x','x1','x2','x3','a','b','x4','x5','c')
    add+=('exact hdF_witness_witness_right_right','exact hdG_witness_witness_right_right','exact hp','exact he','exact hdH_witness_witness_right_right')

    scalar=('induction l',)+_intro('a','F','G','b','c','hpoint','hF','hG')
    for table,value,hyp in (('F','b','hF'),('G','c','hG')):
        scalar+=(f'have h{value} : {value} = 0',)+_call('divisor_signed_sum_empty_value',table,value)+(f'exact {hyp}',)
    scalar+=_rewrite('hb',_mul_code('a','b','c','scalar_base_b'),'b')
    scalar+=_rewrite('hc',_mul_code('a','0','c','scalar_base_c'),'c')+_call('signed_mul_zero_right','a')
    scalar+=_intro('a','F','G','b','c','hpoint','hF','hG')
    for table,value,hyp in (('F','b','hF'),('G','c','hG')):
        name='hd'+table
        scalar+=(f'have {name} : {_decompose(table,"l",value,"scalar_step_"+table)}',)
        scalar+=_call('divisor_signed_sum_successor_decompose',table,'l',value)+(f'exact {hyp}',)+_cases(name,2)+_parts(name+'_witness_witness',3)
    scalar+=(f"have hp : {_mul_code('a','x','x2','scalar_prefix')}",)
    scalar+=_call('IH','a','F','G','x','x2')+_call('signed_table_scalar_restrict','a','F','G','l')
    scalar+=('exact hpoint','exact hdF_witness_witness_left','exact hdG_witness_witness_left',f"have he : {_mul_code('a','x1','x3','scalar_last')}")
    scalar+=_call('signed_table_scalar_lookup','a','F','G','S l','l','x1','x3')+('exact hpoint',)+_call('le_refl','S l')
    scalar+=('exact hdF_witness_witness_right_left','exact hdG_witness_witness_right_left')
    scalar+=_call('signed_table_scalar_add_intro','a','x','x1','b','x2','x3','c')
    scalar+=('exact hdF_witness_witness_right_right','exact hp','exact he','exact hdG_witness_witness_right_right')
    return (
        spec('signed_prefix_sum_pointwise_add',
             f"forall l F G H a b c. ({_pointwise_add('F','G','H','l','linearity_pointwise')}) -> "
             f"({_signed_sum('F','l','a','linearity_first')}) -> ({_signed_sum('G','l','b','linearity_second')}) -> "
             f"({_signed_sum('H','l','c','linearity_output')}) -> ({_add_code('a','b','c','linearity_result')})",
             ('divisor_signed_sum_empty_value','signed_add_zero_left','divisor_signed_sum_successor_decompose',
              'signed_table_add_restrict','signed_table_add_lookup','le_refl','signed_table_add_medial'),add,
             'Ordinary prefix induction proves that the actual sum of a witnessed pointwise table addition is the canonical signed sum of the two actual prefix sums, including length zero.'),
        spec('signed_prefix_sum_scalar_multiply',
             f"forall l a F G b c. ({_scalar('a','F','G','l','scalar_pointwise')}) -> ({_signed_sum('F','l','b','scalar_source_sum')}) -> "
             f"({_signed_sum('G','l','c','scalar_output_sum')}) -> ({_mul_code('a','b','c','scalar_sum_result')})",
             ('divisor_signed_sum_empty_value','signed_mul_zero_right','divisor_signed_sum_successor_decompose',
              'signed_table_scalar_restrict','signed_table_scalar_lookup','le_refl','signed_table_scalar_add_intro'),scalar,
             'Every actual prefix sum commutes with multiplication by an arbitrary canonical signed scalar, via genuine successor sums and distributivity; zero length and negative scalars are included.'),
    )


def _constructed_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    rows=[]
    for scalar,relation,name,operation in (
        (False,_pointwise_add,'signed_prefix_sum_pointwise_add',_add_code),
        (True,_scalar,'signed_prefix_sum_scalar_multiply',_mul_code),
    ):
        symbols=('a','F','G') if scalar else ('F','G','H')
        tables=('F','G') if scalar else ('F','G','H')
        roots=('x','x1') if scalar else ('x','x1','x2')
        values=('b','c') if scalar else ('a','b','c')
        count=len(tables)+1
        body=_intro('l',*symbols,'hpoint')
        for index,table in enumerate(tables):
            body+=(f'have hs{index} : exists z. ({_signed_sum(table,"l","z",name+"_construct"+str(index))})',)
            body+=_call('arithmetic_signed_sum_exists','l',table,'l')+_parts('hpoint',count)
            hyp='hpoint'+'_right'*index+'_left'
            body+=(f'exact {hyp}',f'cases hs{index}')
        body+=tuple('exists '+root for root in roots)
        for index in range(len(tables)):
            body+=('split',f'exact hs{index}_witness')
        body+=_call(name,'l',*symbols,*roots)+('exact hpoint',)+tuple(f'exact hs{index}_witness' for index in range(len(tables)))
        result=_and(*(tuple(_signed_sum(table,'l',value,name+'_result'+str(index)) for index,(table,value) in enumerate(zip(tables,values,strict=True)))
                      +(operation(*(('a',*values) if scalar else values),name+'_result_operation'),)))
        rows.append(spec(name+'_values_exist',
                         'forall '+' '.join(('l',*symbols))+'. ('+relation(*symbols,'l',name+'_construct_graph')+') -> exists '+' '.join(values)+'. '+result,
                         ('arithmetic_signed_sum_exists',name),body,
                         'Construct all actual signed prefix-sum values and prove their '+('scalar product' if scalar else 'addition')+' relation, including the empty-prefix boundary.'))
    return tuple(rows)


def make_signed_sum_linearity_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _scalar_rows(spec)+_linearity_rows(spec)+_constructed_rows(spec)


__all__=['make_signed_sum_linearity_candidate_theorems']
