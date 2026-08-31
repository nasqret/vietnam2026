"""Working convolution compatibility with actual leading-zero padding.

All inputs and outputs are actual beta-coded finite prefixes.  Padding is the
existing leading-zero/copy graph, not a unit normalization or an evaluation
identity.  Natural antidiagonal sums are compared before their canonical
residues.  This source registers nothing and changes no released proof gate.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _part, _parts, _prime, _residue,
)
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _diagonal, _le, _length, _pad, _prefix, _sum, _term,
)
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent, _left_pad
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return f"forall {' '.join(parameters)}. " + ' -> '.join(
        f'({part})' for part in (*premises, result))


def _tail(b: str, c: str, length: str, count: str, tag: str) -> str:
    i = 'pfpad_tail_index_' + tag
    return (f'forall {i}. ({_lt(i,count,tag+"bound")}) -> '
            f'({_at(b,c,f"({length})+{i}","0",tag+"zero")})')


def _sum_decomposition(b: str, c: str, length: str, value: str, tag: str) -> str:
    return 'exists a u. ' + _and(_at(b,c,length,'a',tag+'entry'),
        _sum(b,c,length,'u',tag+'prefix'),f'({value})=u+a')


def _zero_extended_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('b','c','L','t','B','C','i','a')
    body = _intro(*parameters,'hpad','hvalue') + ('cases hpad','cases hvalue','cases hvalue_left','left','split')
    body += _call('matrix_recursive_lt_add_left','i','L','t') + ('exact hvalue_left_left',)
    body += _call('hpad_right','i','a') + ('exact hvalue_left_left','exact hvalue_left_right',
                                         'cases hvalue_right','right','split')
    body += _call('add_le_add_left','L','i','t') + ('exact hvalue_right_left','exact hvalue_right_right')
    shifted = spec(
        'polynomial_zero_extended_left_pad_shift',
        _contract(parameters, (
            _left_pad('b','c','L','t','B','C','shift_padding'),
            _pad('b','c','L','i','a','shift_original'),
        ), _pad('B','C','t+L','t+i','a','shift_result')),
        ('matrix_recursive_lt_add_left','add_le_add_left'), body,
        'Leading-zero padding preserves every shifted zero-extended coefficient, including indices outside the original finite prefix.',
    )
    parameters = ('b','c','L','t','B','C','i')
    body = _intro(*parameters,'hpad','hi') + ('cases hpad','left','split','cases hi','exists x+L',
        'trans (x+S i)+L','simp [add_assoc,add_comm,add_succ_left]','congr','exact hi_witness','refl')
    body += _call('hpad_left','i') + ('exact hi',)
    before = spec(
        'polynomial_zero_extended_left_pad_before',
        _contract(parameters, (
            _left_pad('b','c','L','t','B','C','before_padding'), _lt('i','t','before_bound'),
        ), _pad('B','C','t+L','i','0','before_zero')),
        ('add_assoc','add_comm','add_succ_left'), body,
        'Every position in the actual added leading block has zero extended value zero; no source coefficient is read.',
    )
    parameters = ('b','c','L','t','B','C')
    body = _intro(*parameters,'hz','hpad','i','hi') + ('cases hpad',
        f"have hc : ({_lt('i','t','padded_zero_before')}) \\/ exists j. ({_and(_lt('j','L','padded_zero_inside'),'i=t+j')})")
    body += _call('prime_field_polynomial_left_pad_index_cases','t','L','i') + ('exact hi','cases hc',)
    body += _call('hpad_left','i') + ('exact hc_left','cases hc_right','cases hc_right_witness')
    body += _rewrite_all('hc_right_witness_right',_at('B','C','i','0','padded_zero_rewrite'),'i')
    body += _call('hpad_right','x','0') + ('exact hc_right_witness_left',)
    body += _call('hz','x') + ('exact hc_right_witness_left',)
    zero = spec(
        'polynomial_left_pad_zero_prefix',
        _contract(parameters, (
            _repeat('b','c','0','L','padded_zero_original'),
            _left_pad('b','c','L','t','B','C','padded_zero_data'),
        ), _repeat('B','C','0','t+L','padded_zero_result')),
        ('prime_field_polynomial_left_pad_index_cases',), body,
        'An actually zero prefix remains zero after genuine left padding, including an originally empty factor.',
    )
    return shifted, before, zero


def _sum_left_padding_row(spec: Callable[..., Any]) -> Any:
    parameters = ('b','c','B','C','t','L','n','m')
    body = _intro('b','c','B','C','t') + ('induction L',) + _intro('n','m','hpad','hs','ht')
    body += ('cases hpad','have hn : n=0',) + _call('beta_sum_zero','b','c','n') + ('exact hs',
        'have hlength : t+0=t','simp')
    body += _rewrite_all('hlength',_sum('B','C','t+0','m','sum_pad_base_rewrite'),'t+0','ht')
    body += ('trans t*0',) + _call('beta_repeat_sum_exact','B','C','0','t','m')
    body += ('exact hpad_left','exact ht','trans 0','simp','symm','exact hn')
    body += _intro('n','m','hpad','hs','ht') + ('cases hpad',
        f"have hp : {_left_pad('b','c','L','t','B','C','sum_pad_prefix')}",'split','exact hpad_left')
    body += _intro('i','a','hi','ha') + _call('hpad_right','i','a')
    body += _call('le_succ','S i','L') + ('exact hi','exact ha',
        f"have hfirst : {_sum_decomposition('b','c','L','n','sum_pad_first')}")
    body += _call('beta_sum_succ_decompose','b','c','L','n') + ('exact hs','cases hfirst','cases hfirst_witness')
    body += _parts('hfirst_witness_witness',3) + ('have hlength : t+S L=S (t+L)','simp')
    body += _rewrite_all('hlength',_sum('B','C','t+S L','m','sum_pad_step_rewrite'),'t+S L','ht')
    body += (f"have hsecond : {_sum_decomposition('B','C','t+L','m','sum_pad_second')}",)
    body += _call('beta_sum_succ_decompose','B','C','t+L','m') + ('exact ht','cases hsecond','cases hsecond_witness')
    body += _parts('hsecond_witness_witness',3) + ('have hprefix : x3=x1',)
    body += _call('IH','x1','x3') + ('exact hp','exact hfirst_witness_witness_right_left',
        'exact hsecond_witness_witness_right_left','have hentry : x2=x')
    body += _call('beta_at_unique','B','C','t+L','x2','x') + ('exact hsecond_witness_witness_left',)
    body += _call('hpad_right','L','x') + _call('le_refl','S L') + ('exact hfirst_witness_witness_left',
        'trans x3+x2','exact hsecond_witness_witness_right_right','trans x1+x','congr','exact hprefix',
        'exact hentry','symm','exact hfirst_witness_witness_right_right')
    return spec(
        'polynomial_left_pad_natural_sum_invariant',
        _contract(parameters, (
            _left_pad('b','c','L','t','B','C','sum_pad_data'),
            _sum('b','c','L','n','sum_pad_original'),
            _sum('B','C','t+L','m','sum_pad_actual'),
        ), 'm=n'),
        ('beta_sum_zero','beta_repeat_sum_exact','le_succ','beta_sum_succ_decompose',
         'beta_at_unique','le_refl'), body,
        'Two actual natural sum traces have equal totals when one term prefix is the genuine leading-zero padding of the other.',
    )


def _sum_zero_tail_row(spec: Callable[..., Any]) -> Any:
    parameters = ('b','c','B','C','L','t','n','m')
    body = _intro('b','c','B','C','L') + ('induction t',) + _intro('n','m','he','hz','hs','ht')
    body += ('have hlength : L+0=L','simp',)
    body += _rewrite_all('hlength',_sum('B','C','L+0','m','sum_tail_base_rewrite'),'L+0','ht')
    body += _call('beta_sum_functional','B','C','L','m','n') + ('exact ht',)
    body += _call('beta_sum_transport_prefix','b','c','B','C','L','n') + ('exact hs','exact he')
    body += _intro('n','m','he','hz','hs','ht') + ('have hlength : L+S t=S (L+t)','simp',)
    body += _rewrite_all('hlength',_sum('B','C','L+S t','m','sum_tail_step_rewrite'),'L+S t','ht')
    body += (f"have hd : {_sum_decomposition('B','C','L+t','m','sum_tail_decomposition')}",)
    body += _call('beta_sum_succ_decompose','B','C','L+t','m') + ('exact ht','cases hd','cases hd_witness')
    body += _parts('hd_witness_witness',3) + ('have hprefix : x1=n',)
    body += _call('IH','n','x1') + ('exact he',) + _intro('i','hi') + _call('hz','i')
    body += _call('le_succ','S i','t') + ('exact hi','exact hs','exact hd_witness_witness_right_left',
        'have hzero : x=0')
    body += _call('beta_at_unique','B','C','L+t','x','0') + ('exact hd_witness_witness_left',)
    body += _call('hz','t') + _call('le_refl','S t') + ('trans x1+x','exact hd_witness_witness_right_right',
        'trans x1','rewrite hzero','simp','exact hprefix')
    return spec(
        'polynomial_zero_tail_natural_sum_invariant',
        _contract(parameters, (
            _equal('b','c','B','C','L','sum_tail_equal'), _tail('B','C','L','t','sum_tail_zero'),
            _sum('b','c','L','n','sum_tail_original'), _sum('B','C','L+t','m','sum_tail_actual'),
        ), 'm=n'),
        ('beta_sum_functional','beta_sum_transport_prefix','beta_sum_succ_decompose',
         'le_succ','beta_at_unique','le_refl'), body,
        'Appending a genuinely all-zero tail to an independently recoded natural summand prefix preserves its actual sum.',
    )


def _term_shift_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side == 'left' else ('BB','BC')
    parameters = ('ab','ac','L','bb','bc','M',*padded,'t','i','j','z')
    old_factor = ('ab','ac','L') if side == 'left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side == 'left' else ('ab','ac','L','BB','BC','t+M')
    index = 't+j' if side == 'left' else 'j'
    body = _intro(*parameters,'hp','ht') + tuple('cases ht'+'_witness'*i for i in range(3))
    inner = 'ht_witness_witness_witness'
    body += _parts(inner,4) + ('exists '+('x' if side=='left' else 't+x'),'exists x1','exists x2','split',
        'trans t+(j+x)')
    body += ('apply add_assoc',) if side == 'left' else ('simp [add_assoc,add_comm]',)
    body += ('congr','refl','exact '+_part(inner,4,0),'split')
    if side == 'left':
        body += _call('polynomial_zero_extended_left_pad_shift',*old_factor,'t',*padded,'j','x1')
        body += ('exact hp','exact '+_part(inner,4,1),'split','exact '+_part(inner,4,2))
    else:
        body += ('exact '+_part(inner,4,1),'split')
        body += _call('polynomial_zero_extended_left_pad_shift',*old_factor,'t',*padded,'x','x2')
        body += ('exact hp','exact '+_part(inner,4,2))
    body += ('exact '+_part(inner,4,3),)
    return spec(
        'polynomial_diagonal_term_left_padding_'+side,
        _contract(parameters, (
            _left_pad(*old_factor,'t',*padded,'term_padding_'+side),
            _term('ab','ac','L','bb','bc','M','i','j','z','term_original_'+side),
        ), _term(*factors,'t+i',index,'z','term_shifted_'+side)),
        ('add_assoc','polynomial_zero_extended_left_pad_shift') + (('add_comm',) if side=='right' else ()),
        body, 'A genuine '+side+' factor leading-zero padding shifts the antidiagonal position while preserving each actual natural product term.',
    )


def _term_zero_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side == 'left' else ('BB','BC')
    parameters = ('ab','ac','L','bb','bc','M',*padded,'t','i','j','z')
    original = ('ab','ac','L') if side == 'left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side == 'left' else ('ab','ac','L','BB','BC','t+M')
    bound = _lt('j','t','term_zero_left_bound') if side == 'left' else _lt('i','t+j','term_zero_right_bound')
    body = _intro(*parameters,'hpad','hbound','ht') + tuple('cases ht'+'_witness'*i for i in range(3))
    inner = 'ht_witness_witness_witness'
    body += _parts(inner,4)
    if side == 'right':
        body += (f"have hindex : {_lt('x','t','term_zero_complement')}",'cases hbound','exists x3')
        body += _call('add_right_cancel','x3+S x','t','j') + ('trans x3+S (j+x)',
            'simp [add_assoc,add_comm,add_succ_left]','trans x3+S i','congr','refl','congr',
            'exact '+_part(inner,4,0),'exact hbound_witness')
    index, value = ('j','x1') if side == 'left' else ('x','x2')
    body += (f'have hzero : {value}=0',)
    body += _call('polynomial_zero_extended_entry_functional',*padded,
                  't+L' if side=='left' else 't+M',index,value,'0')
    body += ('exact '+_part(inner,4,1 if side=='left' else 2),)
    body += _call('polynomial_zero_extended_left_pad_before',*original,'t',*padded,index)
    body += ('exact hpad','exact '+('hbound' if side=='left' else 'hindex'),
             'trans x1*x2','exact '+_part(inner,4,3),'rewrite hzero')
    body += _call('mul_zero_left','x2') if side == 'left' else ('simp',)
    dependencies = ('polynomial_zero_extended_entry_functional','polynomial_zero_extended_left_pad_before')
    dependencies += ('mul_zero_left',) if side=='left' else ('add_right_cancel','add_assoc','add_comm','add_succ_left')
    return spec(
        'polynomial_diagonal_term_left_padding_zero_'+side,
        _contract(parameters, (_left_pad(*original,'t',*padded,'zero_term_pad_'+side), bound,
                              _term(*factors,'i','j','z','zero_term_actual_'+side)), 'z=0'),
        dependencies, body,
        'A genuine antidiagonal term is zero when its '+side+' factor index lies in the actual leading padding block.',
    )


def _diagonal_padding_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side == 'left' else ('BB','BC')
    original = ('ab','ac','L') if side == 'left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side == 'left' else ('ab','ac','L','BB','BC','t+M')
    parameters = ('ab','ac','L','bb','bc','M',*padded,'t','i','db','dc','eb','ec')
    old = _diagonal('ab','ac','L','bb','bc','M','i','db','dc','S i','diagonal_pad_old_'+side)
    new = _diagonal(*factors,'t+i','eb','ec','S (t+i)','diagonal_pad_new_'+side)
    result = (_left_pad('db','dc','S i','t','eb','ec','diagonal_pad_result_left') if side=='left'
              else _and(_equal('db','dc','eb','ec','S i','diagonal_pad_result_equal'),
                        _tail('eb','ec','S i','t','diagonal_pad_result_tail')))
    body = _intro(*parameters,'hpad','hold','hnew') + ('split',)
    if side == 'left':
        body += _intro('j','hj')
        point = _and(_at('eb','ec','j','z','diagonal_zero_entry'),_term(*factors,'t+i','j','z','diagonal_zero_term'))
        body += (f'have hv : exists z. {point}',) + _call('hnew','j')
        body += _call('le_trans','S j','t','S (t+i)') + ('exact hj',)
        body += _call('le_succ','t','t+i') + _call('le_add_right','t','i')
        body += ('cases hv','cases hv_witness','have hz : x=0')
        body += _call('polynomial_diagonal_term_left_padding_zero_left',
                      'ab','ac','L','bb','bc','M',*padded,'t','t+i','j','x')
        body += ('exact hpad','exact hj','exact hv_witness_right')
        body += _rewrite_all('hz',_at('eb','ec','j','x','diagonal_zero_rewrite'),'x','hv_witness_left')
        body += ('exact hv_witness_left',)
    body += _intro('j','a','hj','ha')
    body += (f"have hterm : {_term('ab','ac','L','bb','bc','M','i','j','a','diagonal_copy_old')}",)
    body += _call('polynomial_diagonal_prefix_entry','ab','ac','L','bb','bc','M','i','db','dc','S i','j','a')
    body += ('exact hold','exact hj','exact ha')
    index = 't+j' if side=='left' else 'j'
    point = _and(_at('eb','ec',index,'z','diagonal_copy_entry'),_term(*factors,'t+i',index,'z','diagonal_copy_actual'))
    body += (f'have hv : exists z. {point}',) + _call('hnew',index)
    if side == 'left':
        body += _call('succ_le_succ','t+j','t+i') + _call('add_le_add_left','j','i','t')
        body += _call('le_of_succ_le_succ','j','i') + ('exact hj',)
    else:
        body += _call('le_trans','S j','S i','S (t+i)') + ('exact hj',)
        body += _call('succ_le_succ','i','t+i') + _call('le_add_left','i','t')
    body += ('cases hv','cases hv_witness','have heq : x=a')
    body += _call('polynomial_diagonal_term_functional',*factors,'t+i',index,'x','a')
    body += ('exact hv_witness_right',)
    body += _call('polynomial_diagonal_term_left_padding_'+side,
                  'ab','ac','L','bb','bc','M',*padded,'t','i','j','a')
    body += ('exact hpad','exact hterm')
    body += _rewrite_all('heq',_at('eb','ec',index,'x','diagonal_copy_rewrite'),'x','hv_witness_left')
    body += ('exact hv_witness_left',)
    if side == 'right':
        body += _intro('j','hj')
        point = _and(_at('eb','ec','S i+j','z','diagonal_tail_entry'),
                     _term(*factors,'t+i','S i+j','z','diagonal_tail_actual'))
        body += (f'have hv : exists z. {point}',) + _call('hnew','S i+j')
        body += ('have hlength : S i+t=S (t+i)','simp [add_succ_left,add_comm]',
                 f"have hbound : {_lt('S i+j','S i+t','diagonal_tail_bound')}")
        body += _call('matrix_recursive_lt_add_left','j','t','S i') + ('exact hj',)
        body += _rewrite_all('hlength',_lt('S i+j','S i+t','diagonal_tail_bound_rewrite'),'S i+t','hbound')
        body += ('exact hbound','cases hv','cases hv_witness','have hz : x=0')
        body += _call('polynomial_diagonal_term_left_padding_zero_right',
                      'ab','ac','L','bb','bc','M',*padded,'t','t+i','S i+j','x')
        body += ('exact hpad',) + _call('matrix_recursive_lt_add_left','i','S i+j','t')
        body += ('exists j',) + _call('add_comm','j','S i') + ('exact hv_witness_right',)
        body += _rewrite_all('hz',_at('eb','ec','S i+j','x','diagonal_tail_rewrite'),'x','hv_witness_left')
        body += ('exact hv_witness_left',)
    dependencies = ('polynomial_diagonal_prefix_entry','le_trans','succ_le_succ',
        'polynomial_diagonal_term_functional','polynomial_diagonal_term_left_padding_'+side,
        'polynomial_diagonal_term_left_padding_zero_'+side)
    dependencies += (('le_succ','le_add_right','add_le_add_left','le_of_succ_le_succ') if side=='left'
                     else ('le_add_left','add_succ_left','add_comm','matrix_recursive_lt_add_left'))
    return spec('polynomial_diagonal_left_padding_'+side,
        _contract(parameters,(_left_pad(*original,'t',*padded,'diagonal_actual_padding_'+side),old,new),result),
        dependencies,body,
        'The two actual antidiagonal tables differ by a proved '+('leading zero block' if side=='left' else 'trailing zero block')+' and exact copied natural summands.')


def _coefficient_padding_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side == 'left' else ('BB','BC')
    original = ('ab','ac','L') if side == 'left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side == 'left' else ('ab','ac','L','BB','BC','t+M')
    parameters = ('p','ab','ac','L','bb','bc','M',*padded,'t','i','r')
    body = _intro(*parameters,'hpad','hc') + tuple('cases hc'+'_witness'*i for i in range(3))
    inner='hc_witness_witness_witness'
    body += _parts(inner,3)
    body += (f"have hd : exists eb ec. {_diagonal(*factors,'t+i','eb','ec','S (t+i)','coefficient_padded_diagonal_'+side)}",)
    body += _call('polynomial_diagonal_prefix_exists',*factors,'t+i') + ('cases hd','cases hd_witness',
        f"have hs : exists n. {_sum('x3','x4','S (t+i)','n','coefficient_padded_sum_'+side)}")
    body += _call('beta_sum_exists','x3','x4','S (t+i)') + ('cases hs',)
    data = (_left_pad('x','x1','S i','t','x3','x4','coefficient_diagonal_padding') if side=='left' else
            _and(_equal('x','x1','x3','x4','S i','coefficient_diagonal_equal'),
                 _tail('x3','x4','S i','t','coefficient_diagonal_tail')))
    body += (f'have hdata : {data}',)
    body += _call('polynomial_diagonal_left_padding_'+side,'ab','ac','L','bb','bc','M',*padded,
                  't','i','x','x1','x3','x4')
    body += ('exact hpad','exact '+_part(inner,3,0),'exact hd_witness_witness','have heq : x5=x2')
    sum_name = 'polynomial_left_pad_natural_sum_invariant' if side=='left' else 'polynomial_zero_tail_natural_sum_invariant'
    if side=='left':
        body += _call(sum_name,'x','x1','x3','x4','t','S i','x2','x5') + ('exact hdata',)
    else:
        body += ('cases hdata',) + _call(sum_name,'x','x1','x3','x4','S i','t','x2','x5')
        body += ('exact hdata_left','exact hdata_right')
    body += ('exact '+_part(inner,3,1),)
    length = 't+S i' if side=='left' else 'S i+t'
    body += (f'have hlength : {length}=S (t+i)',)
    body += ('simp',) if side=='left' else ('simp [add_succ_left,add_comm]',)
    body += _rewrite_all('hlength',_sum('x3','x4',length,'x5','coefficient_sum_length_rewrite'),length)
    body += ('exact hs_witness','exists x3','exists x4','exists x2','split','exact hd_witness_witness','split')
    body += _rewrite_all('heq',_sum('x3','x4','S (t+i)','x5','coefficient_sum_value_rewrite'),'x5','hs_witness')
    body += ('exact hs_witness','exact '+_part(inner,3,2))
    dependencies = ('polynomial_diagonal_prefix_exists','beta_sum_exists','polynomial_diagonal_left_padding_'+side,sum_name)
    if side=='right':
        dependencies += ('add_succ_left','add_comm')
    return spec('prime_field_convolution_coefficient_left_padding_'+side,
        _contract(parameters,(_left_pad(*original,'t',*padded,'coefficient_padding_'+side),
            _coefficient('p','ab','ac','L','bb','bc','M','i','r','coefficient_original_'+side)),
            _coefficient('p',*factors,'t+i','r','coefficient_shifted_'+side)),
        dependencies,body,
        'Construct an actual padded antidiagonal table and actual sum trace, proving the shifted coefficient has the same canonical residue without assuming an equality of sums.')


def _coefficient_before_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side=='left' else ('BB','BC')
    original = ('ab','ac','L') if side=='left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
    parameters = ('p','ab','ac','L','bb','bc','M',*padded,'t','i','r')
    body = _intro(*parameters,'hp','hpad','hi','hc') + tuple('cases hc'+'_witness'*i for i in range(3))
    inner='hc_witness_witness_witness'
    body += _parts(inner,3) + (f"have hz : {_repeat('x','x1','0','S i','before_coefficient_zero_diagonal_'+side)}",)
    body += _intro('j','hj')
    point=_and(_at('x','x1','j','z','before_coefficient_entry_'+side),_term(*factors,'i','j','z','before_coefficient_term_'+side))
    body += (f'have ht : exists z. {point}',) + _call(_part(inner,3,0),'j') + ('exact hj','cases ht','cases ht_witness','have heq : x3=0')
    body += _call('polynomial_diagonal_term_left_padding_zero_'+side,'ab','ac','L','bb','bc','M',*padded,'t','i','j','x3')
    body += ('exact hpad',)
    if side=='left':
        body += _call('le_trans','S j','S i','t') + ('exact hj','exact hi')
    else:
        body += _call('le_trans','S i','t','t+j') + ('exact hi',) + _call('le_add_right','t','j')
    body += ('exact ht_witness_right',)
    body += _rewrite_all('heq',_at('x','x1','j','x3','before_coefficient_zero_rewrite_'+side),'x3','ht_witness_left')
    body += ('exact ht_witness_left','have hsum : x2=0','trans (S i)*0')
    body += _call('beta_repeat_sum_exact','x','x1','0','S i','x2')
    body += ('exact hz','exact '+_part(inner,3,1),'simp')
    body += _rewrite_all('hsum',_residue('p','x2','r','before_coefficient_sum_rewrite_'+side),'x2',_part(inner,3,2))
    body += _call('prime_field_residue_bounded_value','p','0','r') + _call('one_le_of_ne_zero','p')
    body += ('exact hp','exact '+_part(inner,3,2))
    dependencies=('polynomial_diagonal_term_left_padding_zero_'+side,'le_trans','beta_repeat_sum_exact',
                  'prime_field_residue_bounded_value','one_le_of_ne_zero')
    if side=='right':
        dependencies += ('le_add_right',)
    return spec('prime_field_convolution_coefficient_before_left_padding_'+side,
        _contract(parameters,('~(p=0)',_left_pad(*original,'t',*padded,'before_coefficient_pad_'+side),
            _lt('i','t','before_coefficient_index_'+side),
            _coefficient('p',*factors,'i','r','before_coefficient_actual_'+side)), 'r=0'),
        dependencies,body,'Every actual convolution coefficient before the added leading block is zero at a nonzero modulus.')


def _product_length_row(spec: Callable[..., Any], side: str) -> Any:
    lengths = ('t+L','M') if side=='left' else ('L','t+M')
    body = _intro('L','M','N','t','K','hold','hL','hM','hnew')
    body += ('cases hold','cases hold_left','cases hold_left_left','exfalso','apply hL',
             'exact hold_left_left_left','exfalso','apply hM','exact hold_left_left_right')
    body += _parts('hold_right',3) + ('cases hnew','cases hnew_left','cases hnew_left_left','exfalso','apply hL')
    if side=='left':
        body += _call('add_eq_zero_right','t','L')
    body += ('exact hnew_left_left_left','exfalso','apply hM')
    if side=='right':
        body += _call('add_eq_zero_right','t','M')
    body += ('exact hnew_left_left_right',) + _parts('hnew_right',3)
    body += _call('succ_injective','K','t+N')
    body += (f'trans ({lengths[0]})+({lengths[1]})','symm','exact hnew_right_right_right',
             'trans t+(L+M)')
    body += ('apply add_assoc',) if side=='left' else ('simp [add_assoc,add_comm]',)
    body += ('rewrite hold_right_right_right','simp')
    return spec('polynomial_product_length_left_padding_'+side,
        _contract(('L','M','N','t','K'),(_length('L','M','N','length_padding_old_'+side),
            '~(L=0)','~(M=0)',_length(*lengths,'K','length_padding_new_'+side)), 'K=t+N'),
        ('add_eq_zero_right','succ_injective','add_assoc')+(('add_comm',) if side=='right' else ()),body,
        'For two nonempty input representations, padding the '+side+' factor increases the actual product length by exactly the padding count; empty factors are excluded explicitly.')


def _product_nonempty_row(spec: Callable[..., Any], side: str) -> Any:
    padded = ('AB','AC') if side=='left' else ('BB','BC')
    original = ('ab','ac','L') if side=='left' else ('bb','bc','M')
    factors = ('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
    parameters=('p','ab','ac','L','bb','bc','M','cb','cc','N',*padded,'t','CB','CC','K')
    old=_convolution('p','ab','ac','L','bb','bc','M','cb','cc','N','nonempty_old_'+side)
    new=_convolution('p',*factors,'CB','CC','K','nonempty_new_'+side)
    body=_intro(*parameters,'hp','hL','hM','hpad','hc','hn')+_parts('hc',4)+_parts('hn',4)
    body+=('have hlength : K=t+N',)+_call('polynomial_product_length_left_padding_'+side,'L','M','N','t','K')
    body+=('exact hc_right_right_left','exact hL','exact hM','exact hn_right_right_left',
           'split','exact hlength','split')
    body+=_intro('i','hi')
    point=_and(_at('CB','CC','i','r','nonempty_zero_entry_'+side),
               _coefficient('p',*factors,'i','r','nonempty_zero_coefficient_'+side))
    body+=(f'have hv : exists r. {point}',)+_call('hn_right_right_right','i')
    body+=_call('le_trans','S i','t','K')+('exact hi','rewrite hlength')+_call('le_add_right','t','N')
    body+=('cases hv','cases hv_witness','have hzero : x=0')
    body+=_call('prime_field_convolution_coefficient_before_left_padding_'+side,
                'p','ab','ac','L','bb','bc','M',*padded,'t','i','x')
    body+=('exact hp','exact hpad','exact hi','exact hv_witness_right')
    body+=_rewrite_all('hzero',_at('CB','CC','i','x','nonempty_zero_rewrite_'+side),'x','hv_witness_left')
    body+=('exact hv_witness_left',)+_intro('i','a','hi','ha')
    body+=(f"have hcoefficient : {_coefficient('p','ab','ac','L','bb','bc','M','i','a','nonempty_original_coefficient_'+side)}",)
    body+=_call('prime_field_convolution_prefix_entry','p','ab','ac','L','bb','bc','M','cb','cc','N','i','a')
    body+=('exact hc_right_right_right','exact hi','exact ha')
    point=_and(_at('CB','CC','t+i','r','nonempty_shifted_entry_'+side),
               _coefficient('p',*factors,'t+i','r','nonempty_shifted_coefficient_'+side))
    body+=(f'have hv : exists r. {point}',)+_call('hn_right_right_right','t+i')
    body+=_rewrite_all('hlength',_lt('t+i','K','nonempty_shifted_bound_'+side),'K')
    body+=_call('matrix_recursive_lt_add_left','i','N','t')+('exact hi','cases hv','cases hv_witness',
                                                            'have heq : x=a')
    body+=_call('prime_field_convolution_coefficient_functional','p',*factors,'t+i','x','a')
    body+=('exact hv_witness_right',)
    body+=_call('prime_field_convolution_coefficient_left_padding_'+side,
                'p','ab','ac','L','bb','bc','M',*padded,'t','i','a')
    body+=('exact hpad','exact hcoefficient')
    body+=_rewrite_all('heq',_at('CB','CC','t+i','x','nonempty_copy_rewrite_'+side),'x','hv_witness_left')
    body+=('exact hv_witness_left',)
    return spec('prime_field_polynomial_convolution_left_padding_nonempty_'+side,
        _contract(parameters,('~(p=0)','~(L=0)','~(M=0)',
            _left_pad(*original,'t',*padded,'nonempty_factor_padding_'+side),old,new),
            _and('K=t+N',_left_pad('cb','cc','N','t','CB','CC','nonempty_product_padding_'+side))),
        ('polynomial_product_length_left_padding_'+side,'le_trans','le_add_right',
         'prime_field_convolution_coefficient_before_left_padding_'+side,'prime_field_convolution_prefix_entry',
         'matrix_recursive_lt_add_left','prime_field_convolution_coefficient_functional',
         'prime_field_convolution_coefficient_left_padding_'+side),body,
        'Two actual nonempty-factor products are related by exact leading-zero output padding and its proved length equation; no raw beta-code equality is asserted.')


def _zero_products_equal_script(side: str, empty_side: str) -> tuple[str, ...]:
    original_zero=('ab','ac','L') if empty_side=='left' else ('bb','bc','M')
    factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
    new_zero=factors[:3] if empty_side=='left' else factors[3:]
    equality='hL_left' if empty_side=='left' else 'hM_left'
    body=(f"have hz : {_repeat(*original_zero[:2],'0',original_zero[2],'empty_factor_zero_'+side+empty_side)}",)
    body+=_intro('j','hj')
    body+=_rewrite_all(equality,_lt('j',original_zero[2],'empty_factor_index_'+side+empty_side),original_zero[2],'hj')
    body+=('exfalso',)+_call('matrix_rank_no_index_below_zero','j')+('exact hj',
        f"have hc0 : {_repeat('cb','cc','0','N','empty_original_product_'+side+empty_side)}")
    body+=_call('prime_field_polynomial_convolution_zero_'+empty_side,
                'p','ab','ac','L','bb','bc','M','cb','cc','N')+('exact hp','exact hz','exact hc')
    body+=(f"have hn0 : {_repeat('CB','CC','0','K','empty_padded_product_'+side+empty_side)}",)
    body+=_call('prime_field_polynomial_convolution_zero_'+empty_side,'p',*factors,'CB','CC','K')+('exact hp',)
    if side==empty_side:
        body+=_call('polynomial_left_pad_zero_prefix',*original_zero,'t',*new_zero[:2])+('exact hz','exact hpad')
    else:
        body+=('exact hz',)
    body+=('exact hn',f"have hec : {_equivalent('cb','cc','N','0','0','0','empty_first_equivalence_'+side+empty_side)}")
    body+=_call('prime_field_polynomial_zero_prefix_equivalent_empty','cb','cc','N')+('exact hc0',
        f"have hen : {_equivalent('CB','CC','K','0','0','0','empty_second_equivalence_'+side+empty_side)}")
    body+=_call('prime_field_polynomial_zero_prefix_equivalent_empty','CB','CC','K')+('exact hn0',)
    body+=_call('prime_field_polynomial_equivalent_transitive','cb','cc','N','0','0','0','CB','CC','K')+('exact hec',)
    body+=_call('prime_field_polynomial_equivalent_symmetric','CB','CC','K','0','0','0')+('exact hen',)
    return body


def _product_equivalent_row(spec: Callable[..., Any], side: str) -> Any:
    padded=('AB','AC') if side=='left' else ('BB','BC')
    original=('ab','ac','L') if side=='left' else ('bb','bc','M')
    factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
    parameters=('p','ab','ac','L','bb','bc','M','cb','cc','N',*padded,'t','CB','CC','K')
    result=_equivalent('cb','cc','N','CB','CC','K','product_equivalent_'+side)
    body=_intro(*parameters,'hp','hpad','hc','hn')+('have hL : L=0 \\/ ~(L=0)',)
    body+=_call('eq_decidable','L','0')+('cases hL',)+_zero_products_equal_script(side,'left')
    body+=('have hM : M=0 \\/ ~(M=0)',)+_call('eq_decidable','M','0')+('cases hM',)+_zero_products_equal_script(side,'right')
    data=_and('K=t+N',_left_pad('cb','cc','N','t','CB','CC','product_equivalent_padding_'+side))
    body+=(f'have hd : {data}',)
    body+=_call('prime_field_polynomial_convolution_left_padding_nonempty_'+side,*parameters)
    body+=('exact hp','exact hL_right','exact hM_right','exact hpad','exact hc','exact hn','cases hd')
    body+=_rewrite_all('hd_left',result,'K')
    body+=_call('prime_field_polynomial_left_pad_equivalent','cb','cc','N','t','CB','CC')+('exact hd_right',)
    return spec('prime_field_polynomial_convolution_left_padding_equivalent_'+side,
        _contract(parameters,('~(p=0)',_left_pad(*original,'t',*padded,'product_factor_padding_'+side),
            _convolution('p','ab','ac','L','bb','bc','M','cb','cc','N','product_original_'+side),
            _convolution('p',*factors,'CB','CC','K','product_padded_'+side)),result),
        ('eq_decidable','matrix_rank_no_index_below_zero','prime_field_polynomial_convolution_zero_left',
         'prime_field_polynomial_convolution_zero_right','polynomial_left_pad_zero_prefix',
         'prime_field_polynomial_zero_prefix_equivalent_empty','prime_field_polynomial_equivalent_transitive',
         'prime_field_polynomial_equivalent_symmetric','prime_field_polynomial_convolution_left_padding_nonempty_'+side,
         'prime_field_polynomial_left_pad_equivalent'),body,
        'Genuine leading-zero padding of the '+side+' factor preserves the formal polynomial product, including empty factors whose proper product lengths need not differ by the padding count.')


def _both_factor_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters=('p','ab','ac','L','bb','bc','M','cb','cc','N','AB','AC','t','BB','BC','s','CB','CC','K')
    pad_a=_left_pad('ab','ac','L','t','AB','AC','both_left_padding')
    pad_b=_left_pad('bb','bc','M','s','BB','BC','both_right_padding')
    old=_convolution('p','ab','ac','L','bb','bc','M','cb','cc','N','both_original_product')
    new=_convolution('p','AB','AC','t+L','BB','BC','s+M','CB','CC','K','both_padded_product')
    result=_equivalent('cb','cc','N','CB','CC','K','both_equivalent_result')
    body=_intro(*parameters,'hp','hA','hB','hc','hn')
    body+=(f'have hcopy : {old}','exact hc',f'have hnewcopy : {new}','exact hn')
    body+=_parts('hcopy',4)+_parts('hnewcopy',4)
    body+=(f"have hlength : exists J. {_length('t+L','M','J','both_middle_length')}",)
    body+=_call('polynomial_product_length_exists','t+L','M')+('cases hlength',
        f"have hmiddle : exists db dc. {_convolution('p','AB','AC','t+L','bb','bc','M','db','dc','x','both_middle_product')}")
    body+=_call('prime_field_polynomial_convolution_at_length_exists','p','AB','AC','t+L','bb','bc','M','x')
    body+=('exact hp','exact hnewcopy_left','exact hcopy_right_left','exact hlength_witness','cases hmiddle','cases hmiddle_witness')
    body+=_call('prime_field_polynomial_equivalent_transitive','cb','cc','N','x1','x2','x','CB','CC','K')
    body+=_call('prime_field_polynomial_convolution_left_padding_equivalent_left',
                'p','ab','ac','L','bb','bc','M','cb','cc','N','AB','AC','t','x1','x2','x')
    body+=('exact hp','exact hA','exact hc','exact hmiddle_witness_witness')
    body+=_call('prime_field_polynomial_convolution_left_padding_equivalent_right',
                'p','AB','AC','t+L','bb','bc','M','x1','x2','x','BB','BC','s','CB','CC','K')
    body+=('exact hp','exact hB','exact hmiddle_witness_witness','exact hn')
    compatible=spec('prime_field_polynomial_convolution_both_left_paddings_equivalent',
        _contract(parameters,('~(p=0)',pad_a,pad_b,old,new),result),
        ('polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_equivalent_transitive','prime_field_polynomial_convolution_left_padding_equivalent_left',
         'prime_field_polynomial_convolution_left_padding_equivalent_right'),body,
        'Construct an actual intermediate product and compose the two proved factor-padding compatibilities; both empty and nonempty factors are covered.')
    initial=parameters[:-3]
    body=_intro(*initial,'hprime','hA','hB','hc')+(f'have hcopy : {old}','exact hc')+_parts('hcopy',4)
    body+=('have hp : ~(p=0)','intro hz')+_call('prime_nonzero','p')+('exact hprime','exact hz',
        f"have hlength : exists K. {_length('t+L','s+M','K','both_exists_length')}")
    body+=_call('polynomial_product_length_exists','t+L','s+M')+('cases hlength',
        f"have hnew : exists CB CC. {_convolution('p','AB','AC','t+L','BB','BC','s+M','CB','CC','x','both_exists_product')}")
    body+=_call('prime_field_polynomial_convolution_at_length_exists','p','AB','AC','t+L','BB','BC','s+M','x')+('exact hp',)
    for original,padded,count,hbound,hpad in ((('ab','ac','L'),('AB','AC'),'t','hcopy_left','hA'),
                                            (('bb','bc','M'),('BB','BC'),'s','hcopy_right_left','hB')):
        body+=_call('prime_field_polynomial_left_pad_bounded','p',*original,count,*padded)
        body+=('exact hprime','exact '+hbound,'exact '+hpad)
    body+=('exact hlength_witness','cases hnew','cases hnew_witness','exists x','exists x1','exists x2','split','exact hnew_witness_witness')
    body+=_call('prime_field_polynomial_convolution_both_left_paddings_equivalent',*initial,'x1','x2','x')
    body+=('exact hp','exact hA','exact hB','exact hc','exact hnew_witness_witness')
    exists=spec('prime_field_polynomial_convolution_both_left_paddings_exists',
        _contract(initial,(_prime('p','both_exists_prime'),pad_a,pad_b,old),
                  'exists K CB CC. '+_and(new,result)),
        ('prime_nonzero','polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_left_pad_bounded','prime_field_polynomial_convolution_both_left_paddings_equivalent'),body,
        'For actual leading-zero paddings over a prime field, construct a genuine proper-length product and prove its formal equivalence to the original product; no output certificate or identity is supplied.')
    return compatible,exists


def make_prime_field_polynomial_convolution_padding_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (*_zero_extended_rows(spec), _sum_left_padding_row(spec), _sum_zero_tail_row(spec),
            *(_term_shift_row(spec, side) for side in ('left','right')),
            *(_term_zero_row(spec, side) for side in ('left','right')),
            *(_diagonal_padding_row(spec, side) for side in ('left','right')),
            *(_coefficient_padding_row(spec, side) for side in ('left','right')),
            *(_coefficient_before_row(spec, side) for side in ('left','right')),
            *(_product_length_row(spec, side) for side in ('left','right')),
            *(_product_nonempty_row(spec, side) for side in ('left','right')),
            *(_product_equivalent_row(spec, side) for side in ('left','right')),
            *_both_factor_rows(spec))


__all__ = ['make_prime_field_polynomial_convolution_padding_candidate_theorems']
