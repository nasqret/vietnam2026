"""Aligned canonical coefficient negation and subtraction over prime fields.

The inherited coefficient order is highest-degree-first.  Every operation
uses one common representation length; no padding, degree normalization or
equality of beta code numbers is asserted.  Subtraction says exactly that
the actual right coefficient plus the actual result equals the actual left
coefficient in the inherited bounded field-addition graph.  Its constructor
uses ordinary finite induction and genuine beta-prefix extension.
"""

from __future__ import annotations

from typing import Any, Callable

from .prime_field_arithmetic_candidate import (
    _add as _field_add, _and, _call, _intro, _lt, _neg as _field_neg,
    _part, _parts, _prime, _public,
)
from .prime_field_polynomial_candidate import _add, _at, _coeff, _equal, _repeat
from .prime_field_tables_candidate import _rewrite_all


def _negate(p: str, ab: str, ac: str, rb: str, rc: str, length: str, tag: str) -> str:
    i, a, r = ('pfs_'+role+'_'+tag for role in ('index','source','result'))
    return f'forall {i}. ({_lt(i,length,tag+"index")}) -> exists {a} {r}. '+_and(
        _at(ab,ac,i,a,tag+'source'), _at(rb,rc,i,r,tag+'result'),
        _field_neg(p,a,r,tag+'operation'),
    )


def _subtract(p: str, ab: str, ac: str, bb: str, bc: str, rb: str, rc: str,
              length: str, tag: str) -> str:
    i, a, b, r = ('pfs_'+role+'_'+tag for role in ('index','left','right','result'))
    return f'forall {i}. ({_lt(i,length,tag+"index")}) -> exists {a} {b} {r}. '+_and(
        _at(ab,ac,i,a,tag+'left'), _at(bb,bc,i,b,tag+'right'),
        _at(rb,rc,i,r,tag+'result'), _field_add(p,b,r,a,tag+'operation'),
    )


def prime_field_polynomial_negate_relation(p: str, ab: str, ac: str, rb: str, rc: str,
                                           length: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Each actual result coefficient is the bounded additive inverse."""
    return _public(_negate,(p,ab,ac,rb,rc,length),tag=tag,variables=variables)


def prime_field_polynomial_subtract_relation(p: str, ab: str, ac: str, bb: str, bc: str,
                                             rb: str, rc: str, length: str, *, tag: str,
                                             variables: tuple[str,...]) -> str:
    """Actual aligned B_i+R_i=A_i, not an assumed subtraction law."""
    return _public(_subtract,(p,ab,ac,bb,bc,rb,rc,length),tag=tag,variables=variables)


def _scalar_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro('p','a','b','hp','ha','hb')
    body += (f"have hn : exists n. ({_field_neg('p','b','n','scalar_neg')})",)
    body += _call('prime_field_negate_exists','p','b')+('exact hp','exact hb','cases hn')
    body += (f"have hnb : {_lt('x','p','scalar_neg_bound')}",'cases hn_witness','cases hn_witness_right','exact hn_witness_right_left')
    body += (f"have hr : exists r. ({_field_add('p','x','a','r','scalar_result')})",)
    body += _call('prime_field_add_exists','p','x','a')+('exact hp','exact hnb','exact ha','cases hr')
    body += (f"have hrb : {_lt('x1','p','scalar_result_bound')}",)+_parts('hr_witness',4)+('exact hr_witness_right_right_left',)
    body += (f"have ht : exists t. ({_field_add('p','b','x1','t','scalar_check_sum')})",)
    body += _call('prime_field_add_exists','p','b','x1')+('exact hp','exact hb','exact hrb','cases ht','have heq : a=x2')
    body += _call('prime_field_add_associative','p','b','x','a','0','x1','a','x2')
    body += ('exact hn_witness',)+_call('prime_field_add_zero_left','p','a')+('exact hp','exact ha','exact hr_witness','exact ht_witness','exists x1')
    body += _rewrite_all('heq',_field_add('p','b','x1','a','scalar_finish'),'a')+('exact ht_witness',)
    exists = spec(
        'prime_field_subtract_exists',
        f"forall p a b. ({_prime('p','scalar_prime')}) -> ({_lt('a','p','scalar_left')}) -> ({_lt('b','p','scalar_right')}) -> exists r. ({_field_add('p','b','r','a','scalar_subtract')})",
        ('prime_field_negate_exists','prime_field_add_exists','prime_field_add_associative','prime_field_add_zero_left'),
        body,
        'Construct a genuine bounded solution of b+r=a using actual additive inverse and addition witnesses.',
    )
    zero = spec(
        'prime_field_subtract_equal_zero',
        f"forall p a r. ({_prime('p','scalar_equal_prime')}) -> ({_field_add('p','a','r','a','scalar_equal_sum')}) -> r=0",
        ('prime_field_add_cancel_left','prime_field_add_zero_right'),
        _intro('p','a','r','hp','h')+_call('prime_field_add_cancel_left','p','a','r','0','a')
        +('exact h',)+_call('prime_field_add_zero_right','p','a')+('exact hp','cases h','exact h_left'),
        'The genuine bounded difference of a canonical coefficient from itself is natural zero.',
    )
    return exists,zero


def _operation_rows(spec: Callable[...,Any], kind: str) -> tuple[Any,...]:
    """Two concrete proof-script families, with no new rule or relation oracle."""
    negate = kind == 'negate'
    sources = (('ab','ac'),) if negate else (('ab','ac'),('bb','bc'))
    codes = (*sources,('rb','rc'))
    parameters = ('p',*(value for pair in codes for value in pair),'l')
    source_parameters = ('p',*(value for pair in sources for value in pair))
    values = ('a','r') if negate else ('a','b','r')
    graph = _negate if negate else _subtract
    stem = 'prime_field_polynomial_'+kind
    operation = (lambda vs,t: _field_neg('p',*vs,t)) if negate else (lambda vs,t: _field_add('p',vs[1],vs[2],vs[0],t))
    point = lambda pairs,i,vs,t: _and(*(_at(b,c,i,v,t+str(index)) for index,((b,c),v) in enumerate(zip(pairs,vs,strict=True))),operation(vs,t+'operation'))
    graph_at = lambda pairs,l,t: graph('p',*(value for pair in pairs for value in pair),l,t)
    empty = spec(
        stem+'_empty',
        'forall '+' '.join(parameters[:-1])+'. '+graph_at(codes,'0',kind+'_empty'),
        ('lt_not_le','zero_le'),
        _intro(*parameters[:-1],'i','hi')+('exfalso',)+_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i'),
        'Every pair of empty coefficient prefixes satisfies the operation, including modulus zero and arbitrary encodings.',
    )

    source_hypotheses = ('ha',) if negate else ('ha','hb')
    body = _intro(*source_parameters,'l','hp')+('induction l',)+_intro(*source_hypotheses)+('exists 0','exists 0')
    body += _call(stem+'_empty',*source_parameters,'0','0')
    body += _intro(*source_hypotheses)
    body += (f"have hold : exists rb rc. ({graph_at(codes,'l',kind+'_old')})",)+_call('IH')
    for hypothesis in source_hypotheses:
        body += _intro('j','hj')+_call(hypothesis,'j')+_call('le_succ','S j','l')+('exact hj',)
    body += ('cases hold','cases hold_witness')
    chosen = []
    for index,((b,c),hypothesis) in enumerate(zip(sources,source_hypotheses,strict=True)):
        name = 'hsource'+str(index)
        body += (f"have {name} : exists a. {_and(_at(b,c,'l','a',kind+'_last_source'+str(index)),_lt('a','p',kind+'_last_bound'+str(index)))}",)
        body += _call(hypothesis,'l')+('exists 0','apply zero_add','cases '+name,'cases '+name+'_witness')
        chosen.append('x'+str(index+2))
    last = 'x'+str(len(sources)+2)
    body += (f"have hvalue : exists r. ({operation((*chosen,'r'),kind+'_last_value')})",)
    body += _call('prime_field_negate_exists' if negate else 'prime_field_subtract_exists','p',*chosen)+('exact hp',)
    body += tuple('exact hsource'+str(index)+'_witness_right' for index in range(len(sources)))+('cases hvalue',)
    extension = _and(_at('db','dc','l',last,kind+'_append'),_equal('x','x1','db','dc','l',kind+'_preserve'))
    body += (f'have hnew : exists db dc. ({extension})',)+_call('beta_prefix_extend','l','x','x1',last)
    body += ('cases hnew','cases hnew_witness','cases hnew_witness_witness')
    new_pair = ('x'+str(len(sources)+3),'x'+str(len(sources)+4))
    body += ('exists '+new_pair[0],'exists '+new_pair[1])+_intro('j','hj')
    body += (f"have hcase : j=l \\/ ({_lt('j','l',kind+'_index_case')})",)+_call('finite_lt_succ_eq_or_lt','l','j')+('exact hj','cases hcase')
    body += tuple('exists '+value for value in (*chosen,last))
    for index,((b,c),value) in enumerate(zip((*sources,new_pair),(*chosen,last),strict=True)):
        body += ('split',)+_rewrite_all('hcase_left',_at(b,c,'j',value,kind+'_last_lookup'+str(index)),'j')
        body += ('exact '+('hsource'+str(index)+'_witness_left' if index<len(sources) else 'hnew_witness_witness_left'),)
    body += ('exact hvalue_witness',)
    old_pairs = (*sources,('x','x1'))
    old_values = tuple('v'+str(index) for index in range(len(codes)))
    body += (f"have hprevious : exists {' '.join(old_values)}. ({point(old_pairs,'j',old_values,kind+'_previous')})",)
    body += _call('hold_witness_witness','j')+('exact hcase_right',)
    body += tuple('cases hprevious'+'_witness'*index for index in range(len(codes)))
    witness = 'hprevious'+'_witness'*len(codes)
    body += _parts(witness,len(codes)+1)
    old_chosen = tuple('x'+str(len(sources)+5+index) for index in range(len(codes)))
    body += tuple('exists '+value for value in old_chosen)
    for index in range(len(sources)):
        body += ('split','exact '+_part(witness,len(codes)+1,index))
    body += ('split',)+_call('hnew_witness_witness_right','j',old_chosen[-1])
    body += ('exact hcase_right','exact '+_part(witness,len(codes)+1,len(sources)),'exact '+_part(witness,len(codes)+1,len(codes)))
    exists = spec(
        stem+'_exists',
        'forall '+' '.join((*source_parameters,'l'))+'. '+f"({_prime('p',kind+'_exists_prime')}) -> "
        +' -> '.join('('+_coeff('p',b,c,'l',kind+'_exists_'+b)+')' for b,c in sources)
        +' -> exists rb rc. ('+graph_at(codes,'l',kind+'_exists_result')+')',
        (stem+'_empty','le_succ','zero_add','prime_field_negate_exists' if negate else 'prime_field_subtract_exists','beta_prefix_extend','finite_lt_succ_eq_or_lt'),
        body,
        'Construct the entire actual canonical coefficient output by ordinary induction and beta-prefix extension; no output table is assumed.',
    )

    witness = 'hv'+'_witness'*len(values)
    chosen = ['x'+(str(index) if index else '') for index in range(len(values))]
    body = _intro(*parameters,'i',*values,'h','hi',*('h'+value for value in values))
    unknowns = tuple('u'+str(index) for index in range(len(values)))
    body += (f"have hv : exists {' '.join(unknowns)}. ({point(codes,'i',unknowns,kind+'_entry_chosen')})",)+_call('h','i')+('exact hi',)
    body += tuple('cases hv'+'_witness'*index for index in range(len(values)))+_parts(witness,len(values)+1)
    for index,((b,c),value) in enumerate(zip(codes,values,strict=True)):
        equality = 'heq'+str(index)
        body += (f'have {equality} : {chosen[index]}={value}',)+_call('beta_at_unique',b,c,'i',chosen[index],value)
        body += ('exact '+_part(witness,len(values)+1,index),'exact h'+value)
        body += _rewrite_all(equality,operation(chosen,kind+'_entry_rewrite'+str(index)),chosen[index],_part(witness,len(values)+1,len(values)))
        chosen[index] = value
    body += ('exact '+_part(witness,len(values)+1,len(values)),)
    entry = spec(
        stem+'_entry',
        'forall '+' '.join((*parameters,'i',*values))+'. ('+graph_at(codes,'l',kind+'_entry_graph')+') -> '
        +'('+_lt('i','l',kind+'_entry_index')+') -> '
        +' -> '.join('('+_at(b,c,'i',value,kind+'_entry_'+value)+')' for (b,c),value in zip(codes,values,strict=True))
        +' -> ('+operation(values,kind+'_entry_result')+')',
        ('beta_at_unique',),body,
        'Every actual decoded tuple satisfies the bounded scalar graph, independently of its existential witnesses.',
    )

    body = _intro(*parameters,'h')
    field_bound_indexes = (0,1) if negate else (2,0,1)
    for index in range(len(codes)):
        if index<len(codes)-1: body += ('split',)
        body += _intro('i','hi')+(f"have hv : exists {' '.join(values)}. ({point(codes,'i',values,kind+'_bound_chosen')})",)
        body += _call('h','i')+('exact hi',)+tuple('cases hv'+'_witness'*j for j in range(len(values)))
        body += _parts(witness,len(values)+1)+_parts(_part(witness,len(values)+1,len(values)),4)
        value = 'x'+(str(index) if index else '')
        body += ('exists '+value,'split','exact '+_part(witness,len(values)+1,index),
                 'exact '+_part(_part(witness,len(values)+1,len(values)),4,field_bound_indexes[index]))
    bounded = spec(
        stem+'_bounded',
        'forall '+' '.join(parameters)+'. ('+graph_at(codes,'l',kind+'_bounded_graph')+') -> '
        +_and(*(_coeff('p',b,c,'l',kind+'_bounded_'+b) for b,c in codes)),
        (),body,
        'The actual operation graph itself forces every source and result coefficient to be canonical.',
    )

    other_pairs = (*sources,('db','dc'))
    body = _intro(*parameters[:-1],'db','dc','l','hfirst','hsecond','i','r','hi','hr')
    actual_values = []
    for index,(b,c) in enumerate((*sources,('db','dc'))):
        hypothesis = 'hchosen'+str(index)
        body += (f"have {hypothesis} : exists v. ({_at(b,c,'i','v',kind+'_functional'+str(index))})",)
        body += _call('beta_at_exists',b,c,'i')+('cases '+hypothesis,)
        actual_values.append('x'+(str(index) if index else ''))
    body += (f'have heq : r={actual_values[-1]}',)
    body += (_call('prime_field_negate_functional','p',actual_values[0],'r',actual_values[-1]) if negate
             else _call('prime_field_add_cancel_left','p',actual_values[1],'r',actual_values[-1],actual_values[0]))
    for pairs,hypothesis,value,lookup in ((codes,'hfirst','r','hr'),(other_pairs,'hsecond',actual_values[-1],'hchosen'+str(len(sources))+'_witness')):
        body += _call(stem+'_entry','p',*(v for pair in pairs for v in pair),'l','i',*actual_values[:-1],value)
        body += ('exact '+hypothesis,'exact hi')+tuple('exact hchosen'+str(index)+'_witness' for index in range(len(sources)))+('exact '+lookup,)
    body += _rewrite_all('heq',_at('db','dc','i','r',kind+'_functional_finish'),'r')+('exact hchosen'+str(len(sources))+'_witness',)
    functional = spec(
        stem+'_functional',
        'forall '+' '.join((*parameters[:-1],'db','dc','l'))+'. ('+graph_at(codes,'l',kind+'_functional_first')+') -> ('
        +graph_at(other_pairs,'l',kind+'_functional_second')+') -> ('+_equal('rb','rc','db','dc','l',kind+'_functional_result')+')',
        ('beta_at_exists','prime_field_negate_functional' if negate else 'prime_field_add_cancel_left',stem+'_entry'),
        body,
        'The result is unique by existing decoded-prefix equality, never by equality of beta code numbers.',
    )

    new_pairs = tuple((b.upper(),c.upper()) for b,c in codes)
    body = _intro(*parameters[:-1],*(v for pair in new_pairs for v in pair),'l',*('h'+str(index) for index in range(len(codes))),'h','i','hi')
    body += (f"have hv : exists {' '.join(values)}. ({point(codes,'i',values,kind+'_transport_chosen')})",)
    body += _call('h','i')+('exact hi',)+tuple('cases hv'+'_witness'*index for index in range(len(values)))+_parts(witness,len(values)+1)
    chosen = tuple('x'+(str(index) if index else '') for index in range(len(values)))
    body += tuple('exists '+value for value in chosen)
    for index,value in enumerate(chosen):
        body += ('split',)+_call('h'+str(index),'i',value)+('exact hi','exact '+_part(witness,len(values)+1,index))
    body += ('exact '+_part(witness,len(values)+1,len(values)),)
    transport = spec(
        stem+'_transport',
        'forall '+' '.join((*parameters[:-1],*(v for pair in new_pairs for v in pair),'l'))+'. '
        +' -> '.join('('+_equal(b,c,B,C,'l',kind+'_transport_'+b)+')' for (b,c),(B,C) in zip(codes,new_pairs,strict=True))
        +' -> ('+graph_at(codes,'l',kind+'_transport_old')+') -> ('+graph_at(new_pairs,'l',kind+'_transport_new')+')',
        (),body,
        'Independent beta recodings of every input and output preserve the actual aligned coefficient operation.',
    )
    return empty,exists,entry,bounded,functional,transport


def _negate_laws(spec: Callable[...,Any]) -> tuple[Any,...]:
    chosen = _and(_at('ab','ac','i','a','neg_law_source'),_at('rb','rc','i','r','neg_law_result'),_field_neg('p','a','r','neg_law_value'))
    unpack = (f'have hv : exists a r. ({chosen})',)+_call('h','i')+('exact hi','cases hv','cases hv_witness')+_parts('hv_witness_witness',3)
    involutive = spec(
        'prime_field_polynomial_negate_involutive',
        f"forall p ab ac rb rc l. ({_negate('p','ab','ac','rb','rc','l','neg_inv_old')}) -> ({_negate('p','rb','rc','ab','ac','l','neg_inv_new')})",
        ('prime_field_add_commutative',),
        _intro('p','ab','ac','rb','rc','l','h','i','hi')+unpack
        +('exists x1','exists x','split','exact hv_witness_witness_right_left','split','exact hv_witness_witness_left')
        +_call('prime_field_add_commutative','p','x','x1','0')+('exact hv_witness_witness_right_right',),
        'Reversing a genuine coefficientwise additive inverse gives the original values, without identifying encodings.',
    )
    zero = spec(
        'prime_field_polynomial_negate_zero',
        f"forall p b c l. ({_prime('p','neg_zero_prime')}) -> ({_repeat('b','c','0','l','neg_zero_prefix')}) -> ({_negate('p','b','c','b','c','l','neg_zero_result')})",
        ('prime_field_add_zero_right','prime_field_zero_below_prime'),
        _intro('p','b','c','l','hp','hz','i','hi')+('exists 0','exists 0','split')+_call('hz','i')+('exact hi','split')
        +_call('hz','i')+('exact hi',)+_call('prime_field_add_zero_right','p','0')+('exact hp',)
        +_call('prime_field_zero_below_prime','p')+('exact hp',),
        'A genuinely encoded all-zero coefficient prefix is its own additive inverse.',
    )
    add_zero = spec(
        'prime_field_polynomial_negate_add_zero',
        f"forall p ab ac rb rc zb zc l. ({_negate('p','ab','ac','rb','rc','l','neg_add_graph')}) -> ({_repeat('zb','zc','0','l','neg_add_zero')}) -> ({_add('p','ab','ac','rb','rc','zb','zc','l','neg_add_result')})",
        (),
        _intro('p','ab','ac','rb','rc','zb','zc','l','h','hz','i','hi')+unpack
        +('exists x','exists x1','exists 0','split','exact hv_witness_witness_left','split','exact hv_witness_witness_right_left','split')
        +_call('hz','i')+('exact hi','exact hv_witness_witness_right_right'),
        'Adding actual opposite coefficient values produces any genuine zero-prefix encoding.',
    )
    return involutive,zero,add_zero


def _subtraction_laws(spec: Callable[...,Any]) -> tuple[Any,...]:
    params = ('p','ab','ac','bb','bc','rb','rc','l')
    sub = lambda tag: _subtract(*params,tag)
    recovery = lambda tag: _add('p','bb','bc','rb','rc','ab','ac','l',tag)
    triples = (('ab','ac','a'),('bb','bc','b'),('rb','rc','r'))
    source_point = lambda order,tag: _and(*(_at(b,c,'i',v,tag+v) for b,c,v in order),_field_add('p','b','r','a',tag+'value'))
    bridges = []
    for direction in ('recover_add','from_add'):
        order = triples if direction=='recover_add' else (triples[1],triples[2],triples[0])
        reordered = (1,2,0) if direction=='recover_add' else (2,0,1)
        body = _intro(*params,'h','i','hi')+(f"have hv : exists {' '.join(value for _,_,value in order)}. ({source_point(order,'sub_bridge_'+direction)})",)
        body += _call('h','i')+('exact hi','cases hv','cases hv_witness','cases hv_witness_witness')+_parts('hv_witness_witness_witness',4)
        witnesses = ('x','x1','x2')
        body += tuple('exists '+witnesses[index] for index in reordered)
        for index in reordered: body += ('split','exact '+_part('hv_witness_witness_witness',4,index))
        body += ('exact hv_witness_witness_witness_right_right_right',)
        left,right = (sub,recovery) if direction=='recover_add' else (recovery,sub)
        bridges.append(spec(
            'prime_field_polynomial_subtract_'+direction,
            'forall '+' '.join(params)+'. ('+left('sub_bridge_old_'+direction)+') -> ('+right('sub_bridge_new_'+direction)+')',
            (),body,
            'Relate the actual subtraction witnesses to the actual aligned B+R=A table; no algebraic identity is assumed.',
        ))
    self_zero = spec(
        'prime_field_polynomial_subtract_self_zero',
        f"forall p ab ac zb zc l. ({_prime('p','sub_self_prime')}) -> ({_coeff('p','ab','ac','l','sub_self_coeff')}) -> ({_repeat('zb','zc','0','l','sub_self_zero')}) -> ({_subtract('p','ab','ac','ab','ac','zb','zc','l','sub_self_result')})",
        ('prime_field_polynomial_subtract_from_add','prime_field_polynomial_add_zero_right'),
        _intro('p','ab','ac','zb','zc','l','hp','ha','hz')+_call('prime_field_polynomial_subtract_from_add','p','ab','ac','ab','ac','zb','zc','l')
        +_call('prime_field_polynomial_add_zero_right','p','ab','ac','zb','zc','l')+('exact hp','exact ha','exact hz'),
        'Subtracting a canonical prefix from itself constructs its genuine all-zero coefficient result.',
    )
    zero_right = spec(
        'prime_field_polynomial_subtract_zero_right',
        f"forall p ab ac zb zc l. ({_prime('p','sub_zero_prime')}) -> ({_coeff('p','ab','ac','l','sub_zero_coeff')}) -> ({_repeat('zb','zc','0','l','sub_zero_prefix')}) -> ({_subtract('p','ab','ac','zb','zc','ab','ac','l','sub_zero_result')})",
        ('prime_field_polynomial_subtract_from_add','prime_field_polynomial_add_commutative','prime_field_polynomial_add_zero_right'),
        _intro('p','ab','ac','zb','zc','l','hp','ha','hz')+_call('prime_field_polynomial_subtract_from_add','p','ab','ac','zb','zc','ab','ac','l')
        +_call('prime_field_polynomial_add_commutative','p','ab','ac','zb','zc','ab','ac','l')
        +_call('prime_field_polynomial_add_zero_right','p','ab','ac','zb','zc','l')+('exact hp','exact ha','exact hz'),
        'Subtracting an actual zero prefix leaves the represented canonical coefficients unchanged.',
    )
    zero_left = spec(
        'prime_field_polynomial_subtract_zero_left',
        f"forall p bb bc rb rc zb zc l. ({_negate('p','bb','bc','rb','rc','l','sub_zero_left_neg')}) -> ({_repeat('zb','zc','0','l','sub_zero_left_zero')}) -> ({_subtract('p','zb','zc','bb','bc','rb','rc','l','sub_zero_left_result')})",
        ('prime_field_polynomial_subtract_from_add','prime_field_polynomial_negate_add_zero'),
        _intro('p','bb','bc','rb','rc','zb','zc','l','hn','hz')+_call('prime_field_polynomial_subtract_from_add','p','zb','zc','bb','bc','rb','rc','l')
        +_call('prime_field_polynomial_negate_add_zero','p','bb','bc','rb','rc','zb','zc','l')+('exact hn','exact hz'),
        'Subtracting an actual canonical prefix from zero yields its actual coefficientwise additive inverse.',
    )
    equal_entry = spec(
        'prime_field_polynomial_subtract_equal_entry_zero',
        'forall '+' '.join((*params,'i','a','r'))+'. '+f"({_prime('p','sub_entry_zero_prime')}) -> ({sub('sub_entry_zero_graph')}) -> ({_lt('i','l','sub_entry_zero_index')}) -> "
        +f"({_at('ab','ac','i','a','sub_entry_zero_a')}) -> ({_at('bb','bc','i','a','sub_entry_zero_b')}) -> ({_at('rb','rc','i','r','sub_entry_zero_r')}) -> r=0",
        ('prime_field_subtract_equal_zero','prime_field_polynomial_subtract_entry'),
        _intro(*params,'i','a','r','hp','h','hi','ha','hb','hr')+_call('prime_field_subtract_equal_zero','p','a','r')+('exact hp',)
        +_call('prime_field_polynomial_subtract_entry',*params,'i','a','a','r')+('exact h','exact hi','exact ha','exact hb','exact hr'),
        'Equal aligned coefficients, in particular equal leading coefficients, leave actual zero at that result position.',
    )
    body = _intro(*params,'hp','he','h','i','hi')
    body += (f"have ha : exists a. ({_at('ab','ac','i','a','sub_all_zero_a')})",)+_call('beta_at_exists','ab','ac','i')+('cases ha',)
    body += (f"have hr : exists r. ({_at('rb','rc','i','r','sub_all_zero_r')})",)+_call('beta_at_exists','rb','rc','i')+('cases hr','have hz : x1=0')
    body += _call('prime_field_polynomial_subtract_equal_entry_zero',*params,'i','x','x1')+('exact hp','exact h','exact hi','exact ha_witness')
    body += _call('he','i','x')+('exact hi','exact ha_witness','exact hr_witness')
    body += _rewrite_all('hz',_at('rb','rc','i','x1','sub_all_zero_finish'),'x1','hr_witness')+('exact hr_witness',)
    equal_zero = spec(
        'prime_field_polynomial_subtract_equal_zero',
        'forall '+' '.join(params)+'. '+f"({_prime('p','sub_equal_prime')}) -> ({_equal('ab','ac','bb','bc','l','sub_equal_inputs')}) -> ({sub('sub_equal_graph')}) -> ({_repeat('rb','rc','0','l','sub_equal_result')})",
        ('beta_at_exists','prime_field_polynomial_subtract_equal_entry_zero'),body,
        'Subtracting extensionally equal canonical prefixes gives an actual all-zero prefix even when their beta encodings differ.',
    )
    cancel = spec(
        'prime_field_polynomial_subtract_add_cancel',
        f"forall p ab ac bb bc cb cc rb rc l. ({_add('p','ab','ac','bb','bc','cb','cc','l','sub_cancel_sum')}) -> ({_subtract('p','cb','cc','ab','ac','rb','rc','l','sub_cancel_difference')}) -> ({_equal('bb','bc','rb','rc','l','sub_cancel_result')})",
        ('prime_field_polynomial_subtract_functional','prime_field_polynomial_subtract_from_add'),
        _intro('p','ab','ac','bb','bc','cb','cc','rb','rc','l','hs','hd')
        +_call('prime_field_polynomial_subtract_functional','p','cb','cc','ab','ac','bb','bc','rb','rc','l')
        +_call('prime_field_polynomial_subtract_from_add','p','cb','cc','ab','ac','bb','bc','l')+('exact hs','exact hd'),
        'Subtracting the actual first addend from an actual sum recovers the other addend by represented-prefix equality.',
    )
    cancel_right = spec(
        'prime_field_polynomial_subtract_common_right_cancel',
        f"forall p ab ac bb bc cb cc rb rc l. ({_subtract('p','ab','ac','cb','cc','rb','rc','l','sub_cancel_right_first')}) -> ({_subtract('p','bb','bc','cb','cc','rb','rc','l','sub_cancel_right_second')}) -> ({_equal('ab','ac','bb','bc','l','sub_cancel_right_result')})",
        ('prime_field_polynomial_add_functional','prime_field_polynomial_subtract_recover_add'),
        _intro('p','ab','ac','bb','bc','cb','cc','rb','rc','l','ha','hb')
        +_call('prime_field_polynomial_add_functional','p','cb','cc','rb','rc','ab','ac','bb','bc','l')
        +_call('prime_field_polynomial_subtract_recover_add','p','ab','ac','cb','cc','rb','rc','l')+('exact ha',)
        +_call('prime_field_polynomial_subtract_recover_add','p','bb','bc','cb','cc','rb','rc','l')+('exact hb',),
        'Two actual differences with the same subtrahend and result have equal represented minuend coefficients.',
    )
    return *bridges,self_zero,zero_right,zero_left,equal_entry,equal_zero,cancel,cancel_right


def make_prime_field_polynomial_subtraction_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_scalar_rows(spec),*_operation_rows(spec,'negate'),*_negate_laws(spec),
            *_operation_rows(spec,'subtract'),*_subtraction_laws(spec))


__all__ = [
    'prime_field_polynomial_negate_relation','prime_field_polynomial_subtract_relation',
    'make_prime_field_polynomial_subtraction_candidate_theorems',
]
