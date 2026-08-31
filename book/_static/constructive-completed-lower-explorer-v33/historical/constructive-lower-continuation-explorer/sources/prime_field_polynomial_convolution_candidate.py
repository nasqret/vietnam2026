"""Actual finite antidiagonal convolution of canonical coefficient prefixes.

Coefficients use the inherited highest-degree-first convention.  For output
index i, the ordinary natural sum runs over j<S i and the unique k with j+k=i;
input entries outside their finite prefixes are zero.  A bounded residue of
that actual beta-coded sum is the output coefficient.  No convolution law,
degree theorem or evaluation-product identity is supplied as a premise.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_sum_theorems import _sum_relation_terms
from .prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _part, _parts, _public, _residue,
    _mul as _field_mul,
)
from .prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat
from .prime_field_tables_candidate import _rewrite_all


def _le(a: str, b: str, tag: str) -> str:
    gap = 'pfc_gap_' + tag
    return f'exists {gap}. {gap}+({a})=({b})'


def _sum(b: str, c: str, length: str, n: str, tag: str) -> str:
    return _sum_relation_terms(b,c,length,n,tag='pfc_'+tag)


def _pad(b: str, c: str, length: str, i: str, a: str, tag: str) -> str:
    return f"({_and(_lt(i,length,tag+'inside'),_at(b,c,i,a,tag+'entry'))}) \\/ ({_and(_le(length,i,tag+'outside'),f'({a})=0')})"


def _term(ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, j: str, t: str, tag: str) -> str:
    k,a,b = (f'pfc_{role}_{tag}' for role in ('complement','left','right'))
    return f'exists {k} {a} {b}. '+_and(
        f'({j})+{k}=({i})',_pad(ab,ac,L,j,a,tag+'left'),
        _pad(bb,bc,M,k,b,tag+'right'),f'({t})={a}*{b}',
    )


def _diagonal(ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, db: str, dc: str, length: str, tag: str) -> str:
    j,t = 'pfc_index_'+tag,'pfc_value_'+tag
    return f'forall {j}. ({_lt(j,length,tag+"bound")}) -> exists {t}. '+_and(
        _at(db,dc,j,t,tag+'entry'),_term(ab,ac,L,bb,bc,M,i,j,t,tag+'term'),
    )


def _coefficient(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, r: str, tag: str) -> str:
    db,dc,n = (f'pfc_{role}_{tag}' for role in ('terms_code','terms_scale','natural_sum'))
    return f'exists {db} {dc} {n}. '+_and(
        _diagonal(ab,ac,L,bb,bc,M,i,db,dc,f'S ({i})',tag+'diagonal'),
        _sum(db,dc,f'S ({i})',n,tag+'sum'),_residue(p,n,r,tag+'residue'),
    )


def _prefix(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, cb: str, cc: str, length: str, tag: str) -> str:
    i,r = 'pfc_index_'+tag,'pfc_value_'+tag
    return f'forall {i}. ({_lt(i,length,tag+"bound")}) -> exists {r}. '+_and(
        _at(cb,cc,i,r,tag+'entry'),_coefficient(p,ab,ac,L,bb,bc,M,i,r,tag+'coefficient'),
    )


def _length(L: str, M: str, N: str, tag: str) -> str:
    empty = _and(f'({L})=0 \\/ ({M})=0',f'({N})=0')
    positive = _and(f'~(({L})=0)',f'~(({M})=0)',f'({L})+({M})=S ({N})')
    return f'({empty}) \\/ ({positive})'


def _convolution(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, cb: str, cc: str, N: str, tag: str) -> str:
    return _and(_coeff(p,ab,ac,L,tag+'left'),_coeff(p,bb,bc,M,tag+'right'),
                _length(L,M,N,tag+'length'),_prefix(p,ab,ac,L,bb,bc,M,cb,cc,N,tag+'coefficients'))


def prime_field_polynomial_zero_extended_entry_relation(b: str, c: str, length: str, i: str, a: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_pad,(b,c,length,i,a),tag=tag,variables=variables)


def prime_field_polynomial_diagonal_term_relation(ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, j: str, t: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_term,(ab,ac,L,bb,bc,M,i,j,t),tag=tag,variables=variables)


def prime_field_polynomial_diagonal_prefix_relation(ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, db: str, dc: str, length: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_diagonal,(ab,ac,L,bb,bc,M,i,db,dc,length),tag=tag,variables=variables)


def prime_field_polynomial_convolution_coefficient_relation(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, i: str, r: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_coefficient,(p,ab,ac,L,bb,bc,M,i,r),tag=tag,variables=variables)


def prime_field_polynomial_convolution_prefix_relation(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, cb: str, cc: str, length: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_prefix,(p,ab,ac,L,bb,bc,M,cb,cc,length),tag=tag,variables=variables)


def prime_field_polynomial_product_length_relation(L: str, M: str, N: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_length,(L,M,N),tag=tag,variables=variables)


def prime_field_polynomial_convolution_relation(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str, cb: str, cc: str, N: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_convolution,(p,ab,ac,L,bb,bc,M,cb,cc,N),tag=tag,variables=variables)


def _padding_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'polynomial_zero_extended_entry_exists',
            f"forall b c L i. exists a. ({_pad('b','c','L','i','a','pad_exists')})",
            ('le_or_lt','beta_at_exists'),
            _intro('b','c','L','i')+(f"have ho : ({_le('L','i','pad_order_out')}) \\/ ({_lt('i','L','pad_order_in')})",)
            +_call('le_or_lt','L','i')+('cases ho','exists 0','right','split','exact ho_left','refl')
            +(f"have ha : exists a. ({_at('b','c','i','a','pad_chosen')})",)+_call('beta_at_exists','b','c','i')
            +('cases ha','exists x','left','split','exact ho_right','exact ha_witness'),
            'Every index has an actual beta value inside the prefix and the actual zero value outside it.',
        ),
        spec(
            'polynomial_zero_extended_entry_functional',
            f"forall b c L i a d. ({_pad('b','c','L','i','a','pad_first')}) -> ({_pad('b','c','L','i','d','pad_second')}) -> a=d",
            ('beta_at_unique','lt_not_le'),
            _intro('b','c','L','i','a','d','ha','hd')+('cases ha','cases ha_left','cases hd','cases hd_left')
            +_call('beta_at_unique','b','c','i','a','d')+('exact ha_left_right','exact hd_left_right','cases hd_right','exfalso')
            +_call('lt_not_le','i','L')+('exact ha_left_left','exact hd_right_left','cases ha_right','cases hd','cases hd_left','exfalso')
            +_call('lt_not_le','i','L')+('exact hd_left_left','exact ha_right_left','cases hd_right','trans 0','exact ha_right_right','symm','exact hd_right_right'),
            'Zero extension is value-functional; the inside and outside cases cannot overlap.',
        ),
        spec(
            'polynomial_zero_extended_entry_inside',
            f"forall b c L i a. ({_lt('i','L','pad_inside_bound')}) -> ({_pad('b','c','L','i','a','pad_inside_source')}) -> ({_at('b','c','i','a','pad_inside_result')})",
            ('lt_not_le',),
            _intro('b','c','L','i','a','hi','ha')+('cases ha','cases ha_left','exact ha_left_right','cases ha_right','exfalso')
            +_call('lt_not_le','i','L')+('exact hi','exact ha_right_left'),
            'Inside the finite input domain the padded lookup is exactly the original beta entry.',
        ),
        spec(
            'polynomial_zero_extended_entry_transport',
            f"forall b c d e L i a. ({_equal('b','c','d','e','L','pad_recode')}) -> ({_pad('b','c','L','i','a','pad_old')}) -> ({_pad('d','e','L','i','a','pad_new')})",
            (),
            _intro('b','c','d','e','L','i','a','he','ha')+('cases ha','cases ha_left','left','split','exact ha_left_left')
            +_call('he','i','a')+('exact ha_left_left','exact ha_left_right','right','exact ha_right'),
            'Arbitrary beta reencoding of the finite input preserves every zero-extended value, including all outside indices.',
        ),
        spec(
            'polynomial_zero_extended_zero_value',
            f"forall b c L i a. ({_repeat('b','c','0','L','pad_zero_table')}) -> ({_pad('b','c','L','i','a','pad_zero_entry')}) -> a=0",
            ('beta_repeat_entry_eq',),
            _intro('b','c','L','i','a','hz','ha')+('cases ha','cases ha_left')
            +_call('beta_repeat_entry_eq','b','c','0','L','i','a')+('exact hz','exact ha_left_left','exact ha_left_right','cases ha_right','exact ha_right_right'),
            'The zero extension of a genuinely all-zero coefficient prefix is zero at every natural index.',
        ),
    )


def _term_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('ab','ac','L','bb','bc','M')
    exists=spec(
        'polynomial_diagonal_term_exists',
        f"forall {' '.join(params)} i j. ({_lt('j','S i','term_index')}) -> exists t. ({_term(*params,'i','j','t','term_exists')})",
        ('le_of_succ_le_succ','polynomial_zero_extended_entry_exists','add_comm'),
        _intro(*params,'i','j','hj')+('have hk : exists k. k+j=i',)+_call('le_of_succ_le_succ','j','i')+('exact hj','cases hk')
        +(f"have ha : exists a. ({_pad('ab','ac','L','j','a','term_chosen_left')})",)+_call('polynomial_zero_extended_entry_exists','ab','ac','L','j')+('cases ha',)
        +(f"have hb : exists b. ({_pad('bb','bc','M','x','b','term_chosen_right')})",)+_call('polynomial_zero_extended_entry_exists','bb','bc','M','x')
        +('cases hb','exists x1*x2','exists x','exists x1','exists x2','split','trans x+j')+_call('add_comm','j','x')
        +('exact hk_witness','split','exact ha_witness','split','exact hb_witness','refl'),
        'For every j<=i construct its genuine complementary index and the actual product of the two padded coefficients.',
    )
    body=_intro(*params,'i','j','t','s','ht','hs')+tuple('cases ht'+'_witness'*i for i in range(3))+_parts('ht_witness_witness_witness',4)
    body+=tuple('cases hs'+'_witness'*i for i in range(3))+_parts('hs_witness_witness_witness',4)
    body+=('have hk : x=x3',)+_call('add_left_cancel','j','x','x3')+('trans i','exact ht_witness_witness_witness_left','symm','exact hs_witness_witness_witness_left')
    body+=_rewrite_all('hk',_pad('bb','bc','M','x','x2','term_unique_complement'),'x','ht_witness_witness_witness_right_right_left')
    body+=('have ha : x1=x4',)+_call('polynomial_zero_extended_entry_functional','ab','ac','L','j','x1','x4')+('exact ht_witness_witness_witness_right_left','exact hs_witness_witness_witness_right_left')
    body+=('have hb : x2=x5',)+_call('polynomial_zero_extended_entry_functional','bb','bc','M','x3','x2','x5')+('exact ht_witness_witness_witness_right_right_left','exact hs_witness_witness_witness_right_right_left')
    body+=('trans x1*x2','exact ht_witness_witness_witness_right_right_right','trans x4*x5','congr','exact ha','exact hb','symm','exact hs_witness_witness_witness_right_right_right')
    functional=spec(
        'polynomial_diagonal_term_functional',
        f"forall {' '.join(params)} i j t s. ({_term(*params,'i','j','t','term_unique_first')}) -> ({_term(*params,'i','j','s','term_unique_second')}) -> t=s",
        ('add_left_cancel','polynomial_zero_extended_entry_functional'),body,
        'The complementary index and both padded values determine a unique actual antidiagonal product.',
    )
    transport=spec(
        'polynomial_diagonal_term_transport',
        f"forall {' '.join(params)} AB AC BB BC i j t. ({_equal('ab','ac','AB','AC','L','term_transport_a')}) -> ({_equal('bb','bc','BB','BC','M','term_transport_b')}) -> ({_term(*params,'i','j','t','term_transport_old')}) -> ({_term('AB','AC','L','BB','BC','M','i','j','t','term_transport_new')})",
        ('polynomial_zero_extended_entry_transport',),
        _intro(*params,'AB','AC','BB','BC','i','j','t','ha','hb','ht')+tuple('cases ht'+'_witness'*i for i in range(3))+_parts('ht_witness_witness_witness',4)
        +('exists x','exists x1','exists x2','split','exact ht_witness_witness_witness_left','split')
        +_call('polynomial_zero_extended_entry_transport','ab','ac','AB','AC','L','j','x1')+('exact ha','exact ht_witness_witness_witness_right_left','split')
        +_call('polynomial_zero_extended_entry_transport','bb','bc','BB','BC','M','x','x2')+('exact hb','exact ht_witness_witness_witness_right_right_left','exact ht_witness_witness_witness_right_right_right'),
        'Reencoding either input preserves every actual antidiagonal multiplication term.',
    )
    body=_intro('ab','ac','l','bb','bc','m','a','b','t','ha','hb','ht')+tuple('cases ht'+'_witness'*i for i in range(3))+_parts('ht_witness_witness_witness',4)
    body+=('have hk : x=0',)+_call('add_eq_zero_right','0','x')+('exact ht_witness_witness_witness_left',)
    body+=_rewrite_all('hk',_pad('bb','bc','S m','x','x2','term_first_complement'),'x','ht_witness_witness_witness_right_right_left')
    body+=('have heqa : x1=a',)+_call('polynomial_zero_extended_entry_functional','ab','ac','S l','0','x1','a')+('exact ht_witness_witness_witness_right_left','left','split','exists l','simp','exact ha')
    body+=('have heqb : x2=b',)+_call('polynomial_zero_extended_entry_functional','bb','bc','S m','0','x2','b')+('exact ht_witness_witness_witness_right_right_left','left','split','exists m','simp','exact hb')
    body+=('trans x1*x2','exact ht_witness_witness_witness_right_right_right','congr','exact heqa','exact heqb')
    first=spec(
        'polynomial_diagonal_term_leading',
        f"forall ab ac l bb bc m a b t. ({_at('ab','ac','0','a','term_first_a')}) -> ({_at('bb','bc','0','b','term_first_b')}) -> ({_term('ab','ac','S l','bb','bc','S m','0','0','t','term_first_source')}) -> t=a*b",
        ('add_eq_zero_right','polynomial_zero_extended_entry_functional'),body,
        'For two nonempty highest-degree-first inputs the first antidiagonal contains exactly their leading-coefficient product.',
    )
    zeros=[]
    for side in ('left','right'):
        code,scale,length,value=(('ab','ac','L','x1') if side=='left' else ('bb','bc','M','x2'))
        index='j' if side=='left' else 'x'
        hyp='ht_witness_witness_witness_right_left' if side=='left' else 'ht_witness_witness_witness_right_right_left'
        script=_intro(*params,'i','j','t','hz','ht')+tuple('cases ht'+'_witness'*i for i in range(3))+_parts('ht_witness_witness_witness',4)
        script+=(f'have heq : {value}=0',)+_call('polynomial_zero_extended_zero_value',code,scale,length,index,value)+('exact hz','exact '+hyp,'trans x1*x2','exact ht_witness_witness_witness_right_right_right','rewrite heq')
        script+=_call('mul_zero_left','x2') if side=='left' else ('simp',)
        zeros.append(spec(
            'polynomial_diagonal_term_zero_'+side,
            f"forall {' '.join(params)} i j t. ({_repeat(code,scale,'0',length,'term_zero_'+side)}) -> ({_term(*params,'i','j','t','term_zero_source_'+side)}) -> t=0",
            ('polynomial_zero_extended_zero_value',)+(('mul_zero_left',) if side=='left' else ()),script,
            f'An actually all-zero {side} coefficient prefix makes every antidiagonal product zero.',
        ))
    ha='ht_witness_witness_witness_right_left'
    hb='ht_witness_witness_witness_right_right_left'
    body=_intro(*params,'i','j','t','hpast','ht')+tuple('cases ht'+'_witness'*i for i in range(3))+_parts('ht_witness_witness_witness',4)
    body+=('cases '+ha,'cases '+ha+'_left','cases '+hb,'cases '+hb+'_left','exfalso')
    body+=(f"have hsum : {_le('S j+S x','L+M','term_past_sum_bound')}",)+_call('le_trans','S j+S x','L+S x','L+M')
    body+=_call('add_le_add_right','S j','L','S x')+('exact '+ha+'_left_left',)
    body+=_call('add_le_add_left','S x','M','L')+('exact '+hb+'_left_left','have heq : S j+S x=S (S i)','trans S (S (j+x))','simp [add_succ_left]','congr','congr','exact ht_witness_witness_witness_left')
    body+=_rewrite_all('heq',_le('S j+S x','L+M','term_past_rewrite'),'S j+S x','hsum')
    body+=_call('lt_not_le','S i','L+M')+('exact hsum','exact hpast','cases '+hb+'_right','trans x1*x2','exact ht_witness_witness_witness_right_right_right','rewrite '+hb+'_right_right','simp')
    body+=('cases '+ha+'_right','trans x1*x2','exact ht_witness_witness_witness_right_right_right','rewrite '+ha+'_right_right')+_call('mul_zero_left','x2')
    past=spec(
        'polynomial_diagonal_term_past_support',
        f"forall {' '.join(params)} i j t. ({_le('L+M','S i','term_past_guard')}) -> ({_term(*params,'i','j','t','term_past_source')}) -> t=0",
        ('le_trans','add_le_add_right','add_le_add_left','add_succ_left','lt_not_le','mul_zero_left'),body,
        'Beyond the true antidiagonal support, at least one factor is genuinely padded zero; no nonzero term is discarded by the product-length convention.',
    )
    return exists,functional,transport,first,*zeros,past


def _coded_prefix_rows(
    spec: Callable[...,Any], stem: str, parameters: tuple[str,...],
    value: Callable[...,str], prefix: Callable[...,str], value_functional: str,
) -> tuple[Any,...]:
    """Emit ordinary HA for two concrete finite choices, with no new rule."""
    point=lambda index,result,tag: value(*parameters,index,result,tag)
    graph=lambda b,c,N,tag: prefix(*parameters,b,c,N,tag)
    entry=spec(
        stem+'_entry',
        f"forall {' '.join(parameters)} db dc N i a. ({graph('db','dc','N','entry_source')}) -> ({_lt('i','N','entry_index')}) -> ({_at('db','dc','i','a','entry_given')}) -> ({point('i','a','entry_result')})",
        ('beta_at_unique',),
        _intro(*parameters,'db','dc','N','i','a','h','hi','ha')
        +(f"have hv : exists t. {_and(_at('db','dc','i','t','entry_chosen'),point('i','t','entry_chosen_value'))}",)
        +_call('h','i')+('exact hi','cases hv','cases hv_witness','have heq : x=a')
        +_call('beta_at_unique','db','dc','i','x','a')+('exact hv_witness_left','exact ha')
        +_rewrite_all('heq',point('i','x','entry_rewrite'),'x','hv_witness_right')+('exact hv_witness_right',),
        'Every decoded entry of the actual finite coding satisfies its precise value relation, independently of chosen witnesses.',
    )
    recoding=spec(
        stem+'_recoding',
        f"forall {' '.join(parameters)} db dc eb ec N. ({_equal('db','dc','eb','ec','N','recode_equal')}) -> ({graph('db','dc','N','recode_old')}) -> ({graph('eb','ec','N','recode_new')})",
        (),
        _intro(*parameters,'db','dc','eb','ec','N','he','h','i','hi')
        +(f"have hv : exists t. {_and(_at('db','dc','i','t','recode_chosen'),point('i','t','recode_value'))}",)
        +_call('h','i')+('exact hi','cases hv','cases hv_witness','exists x','split')
        +_call('he','i','x')+('exact hi','exact hv_witness_left','exact hv_witness_right'),
        'An independently encoded but extensionally equal target prefix preserves the actual finite value graph.',
    )
    body=_intro(*parameters,'N')+('induction N','intro h','exists 0','exists 0')+_intro('j','hj')+('exfalso',)
    body+=_call('lt_not_le','j','0')+('exact hj',)+_call('zero_le','j')
    body+=('intro h',f"have hold : exists db dc. ({graph('db','dc','N','choice_old')})")+_call('IH')
    body+=_intro('j','hj')+_call('h','j')+_call('le_succ','S j','N')+('exact hj','cases hold','cases hold_witness')
    body+=(f"have hv : exists t. ({point('N','t','choice_last_value')})",)+_call('h','N')+('exists 0','apply zero_add','cases hv')
    extension=_and(_at('db','dc','N','x2','choice_last_entry'),_equal('x','x1','db','dc','N','choice_preservation'))
    body+=(f'have hnew : exists db dc. ({extension})',)+_call('beta_prefix_extend','N','x','x1','x2')
    body+=('cases hnew','cases hnew_witness','cases hnew_witness_witness','exists x3','exists x4')+_intro('j','hj')
    body+=(f"have hcase : j=N \\/ ({_lt('j','N','choice_index_case')})",)+_call('finite_lt_succ_eq_or_lt','N','j')+('exact hj','cases hcase','exists x2','split')
    body+=_rewrite_all('hcase_left',_at('x3','x4','j','x2','choice_new_last_rewrite'),'j')+('exact hnew_witness_witness_left',)
    body+=_rewrite_all('hcase_left',point('j','x2','choice_value_last_rewrite'),'j')+('exact hv_witness',)
    body+=(f"have hp : exists t. {_and(_at('x','x1','j','t','choice_old_entry'),point('j','t','choice_old_value'))}",)
    body+=_call('hold_witness_witness','j')+('exact hcase_right','cases hp','cases hp_witness','exists x5','split')
    body+=_call('hnew_witness_witness_right','j','x5')+('exact hcase_right','exact hp_witness_left','exact hp_witness_right')
    choice=spec(
        stem+'_from_pointwise',
        f"forall {' '.join(parameters)} N. (forall j. ({_lt('j','N','choice_domain')}) -> exists t. ({point('j','t','choice_pointwise')})) -> exists db dc. ({graph('db','dc','N','choice_result')})",
        ('lt_not_le','zero_le','le_succ','zero_add','beta_prefix_extend','finite_lt_succ_eq_or_lt'),body,
        'Ordinary induction and genuine beta-prefix extension construct this concrete finite value table from pointwise witnesses; later roots discharge those witnesses.',
    )
    body=_intro(*parameters,'db','dc','eb','ec','N','hd','he','i','a','hi','ha')
    body+=(f"have hb : exists b. ({_at('eb','ec','i','b','prefix_unique_other')})",)+_call('beta_at_exists','eb','ec','i')+('cases hb','have heq : a=x')
    body+=_call(value_functional,*parameters,'i','a','x')
    body+=_call(stem+'_entry',*parameters,'db','dc','N','i','a')+('exact hd','exact hi','exact ha')
    body+=_call(stem+'_entry',*parameters,'eb','ec','N','i','x')+('exact he','exact hi','exact hb_witness')
    body+=_rewrite_all('heq',_at('eb','ec','i','a','prefix_unique_rewrite'),'a')+('exact hb_witness',)
    functional=spec(
        stem+'_functional',
        f"forall {' '.join(parameters)} db dc eb ec N. ({graph('db','dc','N','prefix_unique_first')}) -> ({graph('eb','ec','N','prefix_unique_second')}) -> ({_equal('db','dc','eb','ec','N','prefix_unique_result')})",
        ('beta_at_exists',value_functional,stem+'_entry'),body,
        'The actual finite output is unique coefficientwise, without identifying different beta-code pairs.',
    )
    return entry,recoding,choice,functional


def _diagonal_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('ab','ac','L','bb','bc','M','I')
    foundational=_coded_prefix_rows(spec,'polynomial_diagonal_prefix',params,_term,_diagonal,'polynomial_diagonal_term_functional')
    exists=spec(
        'polynomial_diagonal_prefix_exists',
        f"forall {' '.join(params)}. exists db dc. ({_diagonal(*params,'db','dc','S I','diagonal_exists')})",
        ('polynomial_diagonal_prefix_from_pointwise','polynomial_diagonal_term_exists'),
        _intro(*params)+_call('polynomial_diagonal_prefix_from_pointwise',*params,'S I')+_intro('j','hj')
        +_call('polynomial_diagonal_term_exists',*params,'j')+('exact hj',),
        'Construct all I+1 genuine antidiagonal products, including boundary padding, without supplying any product table.',
    )
    transport=spec(
        'polynomial_diagonal_prefix_input_transport',
        f"forall {' '.join(params)} AB AC BB BC db dc N. ({_equal('ab','ac','AB','AC','L','diagonal_recode_a')}) -> ({_equal('bb','bc','BB','BC','M','diagonal_recode_b')}) -> ({_diagonal(*params,'db','dc','N','diagonal_old')}) -> ({_diagonal('AB','AC','L','BB','BC','M','I','db','dc','N','diagonal_new')})",
        ('polynomial_diagonal_term_transport',),
        _intro(*params,'AB','AC','BB','BC','db','dc','N','ha','hb','hd','j','hj')
        +(f"have hv : exists t. {_and(_at('db','dc','j','t','diagonal_chosen_entry'),_term(*params,'j','t','diagonal_chosen_term'))}",)
        +_call('hd','j')+('exact hj','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
        +_call('polynomial_diagonal_term_transport','ab','ac','L','bb','bc','M','AB','AC','BB','BC','I','j','x')
        +('exact ha','exact hb','exact hv_witness_right'),
        'Recoding either input preserves the same concrete antidiagonal product table at every requested prefix length.',
    )
    return *foundational,exists,transport


def _coefficient_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ab','ac','L','bb','bc','M','i')
    exists=spec(
        'prime_field_convolution_coefficient_exists',
        f"forall {' '.join(params)}. ~(p=0) -> exists r. ({_coefficient(*params,'r','coefficient_exists')})",
        ('polynomial_diagonal_prefix_exists','beta_sum_exists','hensel_canonical_residue_exists'),
        _intro(*params,'hp')+(f"have hd : exists db dc. ({_diagonal('ab','ac','L','bb','bc','M','i','db','dc','S i','coefficient_diagonal')})",)
        +_call('polynomial_diagonal_prefix_exists','ab','ac','L','bb','bc','M','i')+('cases hd','cases hd_witness')
        +(f"have hs : exists n. ({_sum('x','x1','S i','n','coefficient_sum')})",)+_call('beta_sum_exists','x','x1','S i')+('cases hs',)
        +(f"have hr : exists r. ({_residue('p','x2','r','coefficient_residue')})",)+_call('hensel_canonical_residue_exists','p','x2')
        +('exact hp','cases hr','exists x3','exists x','exists x1','exists x2','split','exact hd_witness_witness','split','exact hs_witness','exact hr_witness'),
        'Every output index has an actual finite antidiagonal product sum and its actual canonical residue.',
    )
    body=_intro(*params,'r','s','hr','hs')+tuple('cases hr'+'_witness'*i for i in range(3))+_parts('hr_witness_witness_witness',3)
    body+=tuple('cases hs'+'_witness'*i for i in range(3))+_parts('hs_witness_witness_witness',3)
    body+=(f"have hsum : {_sum('x3','x4','S i','x2','coefficient_unique_transported_sum')}",)
    body+=_call('beta_sum_transport_prefix','x','x1','x3','x4','S i','x2')+('exact hr_witness_witness_witness_right_left',)
    body+=_call('polynomial_diagonal_prefix_functional','ab','ac','L','bb','bc','M','i','x','x1','x3','x4','S i')
    body+=('exact hr_witness_witness_witness_left','exact hs_witness_witness_witness_left','have heq : x2=x5')
    body+=_call('beta_sum_functional','x3','x4','S i','x2','x5')+('exact hsum','exact hs_witness_witness_witness_right_left')
    body+=_rewrite_all('heq',_residue('p','x2','r','coefficient_unique_rewrite'),'x2','hr_witness_witness_witness_right_right')
    body+=_call('binary_canonical_residue_functional','p','x5','r','s')+('exact hr_witness_witness_witness_right_right','exact hs_witness_witness_witness_right_right')
    functional=spec(
        'prime_field_convolution_coefficient_functional',
        f"forall {' '.join(params)} r s. ({_coefficient(*params,'r','coefficient_first')}) -> ({_coefficient(*params,'s','coefficient_second')}) -> r=s",
        ('beta_sum_transport_prefix','polynomial_diagonal_prefix_functional','beta_sum_functional','binary_canonical_residue_functional'),body,
        'Different real beta sum histories and diagonal encodings yield exactly the same canonical convolution coefficient.',
    )
    bounded=spec(
        'prime_field_convolution_coefficient_bounded',
        f"forall {' '.join(params)} r. ({_coefficient(*params,'r','coefficient_bounded_source')}) -> ({_lt('r','p','coefficient_bound')})",
        (),_intro(*params,'r','h')+tuple('cases h'+'_witness'*i for i in range(3))+_parts('h_witness_witness_witness',4)+('exact h_witness_witness_witness_right_right_left',),
        'Every actual convolution coefficient is a canonical representative strictly below the modulus.',
    )
    transport=spec(
        'prime_field_convolution_coefficient_transport',
        f"forall {' '.join(params)} AB AC BB BC r. ({_equal('ab','ac','AB','AC','L','coefficient_recode_a')}) -> ({_equal('bb','bc','BB','BC','M','coefficient_recode_b')}) -> ({_coefficient(*params,'r','coefficient_old')}) -> ({_coefficient('p','AB','AC','L','BB','BC','M','i','r','coefficient_new')})",
        ('polynomial_diagonal_prefix_input_transport',),
        _intro(*params,'AB','AC','BB','BC','r','ha','hb','h')+tuple('cases h'+'_witness'*i for i in range(3))+_parts('h_witness_witness_witness',3)
        +('exists x','exists x1','exists x2','split')+_call('polynomial_diagonal_prefix_input_transport','ab','ac','L','bb','bc','M','i','AB','AC','BB','BC','x','x1','S i')
        +('exact ha','exact hb','exact h_witness_witness_witness_left','split','exact h_witness_witness_witness_right_left','exact h_witness_witness_witness_right_right'),
        'Input coefficient reencoding preserves each actual convolution sum and its canonical output.',
    )
    return exists,functional,bounded,transport


def _coefficient_boundary_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ab','ac','L','bb','bc','M','i')
    body=_intro('p','ab','ac','l','bb','bc','m','a','b','r','hca','hcb','ha','hb','hr')+tuple('cases hr'+'_witness'*i for i in range(3))+_parts('hr_witness_witness_witness',3)
    decomposition=_and(_at('x','x1','0','t','leading_summand'),_sum('x','x1','0','h','leading_empty_sum'),'x2=h+t')
    body+=(f'have hs : exists t h. ({decomposition})',)+_call('beta_sum_succ_decompose','x','x1','0','x2')+('exact hr_witness_witness_witness_right_left','cases hs','cases hs_witness')+_parts('hs_witness_witness',3)
    body+=('have hz : x4=0',)+_call('beta_sum_zero','x','x1','x4')+('exact hs_witness_witness_right_left',)
    body+=(f"have ht : {_term('ab','ac','S l','bb','bc','S m','0','0','x3','leading_actual_term')}",)
    body+=_call('polynomial_diagonal_prefix_entry','ab','ac','S l','bb','bc','S m','0','x','x1','1','0','x3')+('exact hr_witness_witness_witness_left','exists 0','apply zero_add','exact hs_witness_witness_left')
    body+=('have hn : x2=a*b','trans x4+x3','exact hs_witness_witness_right_right','trans x3','rewrite hz','apply zero_add')
    body+=_call('polynomial_diagonal_term_leading','ab','ac','l','bb','bc','m','a','b','x3')+('exact ha','exact hb','exact ht','split')
    body+=_call('matrix_rank_bounded_prefix_value','ab','ac','S l','p','0','a')+('exact hca','exists l','simp','exact ha','split')
    body+=_call('matrix_rank_bounded_prefix_value','bb','bc','S m','p','0','b')+('exact hcb','exists m','simp','exact hb')
    body+=_call('prime_field_residue_input_equal','p','a*b','x2','r')+('symm','exact hn','exact hr_witness_witness_witness_right_right')
    leading=spec(
        'prime_field_convolution_coefficient_leading',
        f"forall p ab ac l bb bc m a b r. ({_coeff('p','ab','ac','S l','leading_left_coefficients')}) -> ({_coeff('p','bb','bc','S m','leading_right_coefficients')}) -> ({_at('ab','ac','0','a','leading_left')}) -> ({_at('bb','bc','0','b','leading_right')}) -> ({_coefficient('p','ab','ac','S l','bb','bc','S m','0','r','leading_coefficient')}) -> ({_field_mul('p','a','b','r','leading_product')})",
        ('beta_sum_succ_decompose','beta_sum_zero','polynomial_diagonal_prefix_entry','zero_add','polynomial_diagonal_term_leading','matrix_rank_bounded_prefix_value','prime_field_residue_input_equal'),body,
        'The leading convolution coefficient of two nonempty canonical prefixes is their actual canonical field product, proved from its one-term natural sum.',
    )
    zeros=[]
    for kind in ('left','right','past_support'):
        if kind=='left':
            condition=lambda tag:_repeat('ab','ac','0','L',tag)
            term_name='polynomial_diagonal_term_zero_left'
        elif kind=='right':
            condition=lambda tag:_repeat('bb','bc','0','M',tag)
            term_name='polynomial_diagonal_term_zero_right'
        else:
            condition=lambda tag:_le('L+M','S i',tag)
            term_name='polynomial_diagonal_term_past_support'
        body=_intro(*params,'r','hp','hc','hr')+tuple('cases hr'+'_witness'*i for i in range(3))+_parts('hr_witness_witness_witness',3)
        body+=(f"have hz : {_repeat('x','x1','0','S i','zero_diagonal_'+kind)}",)+_intro('j','hj')
        body+=(f"have ht : exists t. {_and(_at('x','x1','j','t','zero_diagonal_entry_'+kind),_term('ab','ac','L','bb','bc','M','i','j','t','zero_diagonal_term_'+kind))}",)
        body+=_call('hr_witness_witness_witness_left','j')+('exact hj','cases ht','cases ht_witness','have heq : x3=0')
        body+=_call(term_name,'ab','ac','L','bb','bc','M','i','j','x3')+('exact hc','exact ht_witness_right')
        body+=_rewrite_all('heq',_at('x','x1','j','x3','zero_diagonal_rewrite_'+kind),'x3','ht_witness_left')+('exact ht_witness_left','have hn : x2=0','trans (S i)*0')
        body+=_call('beta_repeat_sum_exact','x','x1','0','S i','x2')+('exact hz','exact hr_witness_witness_witness_right_left','simp')
        body+=_rewrite_all('hn',_residue('p','x2','r','zero_sum_rewrite_'+kind),'x2','hr_witness_witness_witness_right_right')
        body+=_call('prime_field_residue_bounded_value','p','0','r')+_call('one_le_of_ne_zero','p')+('exact hp','exact hr_witness_witness_witness_right_right')
        zeros.append(spec(
            'prime_field_convolution_coefficient_zero_'+kind,
            f"forall {' '.join(params)} r. ~(p=0) -> ({condition('zero_coefficient_condition_'+kind)}) -> ({_coefficient(*params,'r','zero_coefficient_source_'+kind)}) -> r=0",
            (term_name,'beta_repeat_sum_exact','prime_field_residue_bounded_value','one_le_of_ne_zero'),body,
            ('Every coefficient past the genuine finite convolution support is zero.' if kind=='past_support' else f'An actual zero {kind} input prefix gives zero at every canonical convolution coefficient.'),
        ))
    return leading,*zeros


def _convolution_prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ab','ac','L','bb','bc','M')
    foundational=_coded_prefix_rows(spec,'prime_field_convolution_prefix',params,_coefficient,_prefix,'prime_field_convolution_coefficient_functional')
    exists=spec(
        'prime_field_convolution_prefix_exists',
        f"forall {' '.join(params)} N. ~(p=0) -> exists cb cc. ({_prefix(*params,'cb','cc','N','convolution_prefix_exists')})",
        ('prime_field_convolution_prefix_from_pointwise','prime_field_convolution_coefficient_exists'),
        _intro(*params,'N','hp')+_call('prime_field_convolution_prefix_from_pointwise',*params,'N')+_intro('i','hi')
        +_call('prime_field_convolution_coefficient_exists',*params,'i')+('exact hp',),
        'Construct an actual beta-coded prefix of canonical convolution coefficients of every requested finite length.',
    )
    bounded=spec(
        'prime_field_convolution_prefix_bounded',
        f"forall {' '.join(params)} cb cc N. ({_prefix(*params,'cb','cc','N','prefix_bounded_source')}) -> ({_coeff('p','cb','cc','N','prefix_bounded_result')})",
        ('prime_field_convolution_coefficient_bounded',),
        _intro(*params,'cb','cc','N','h','i','hi')+(f"have hv : exists r. {_and(_at('cb','cc','i','r','prefix_bounded_entry'),_coefficient(*params,'i','r','prefix_bounded_value'))}",)
        +_call('h','i')+('exact hi','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
        +_call('prime_field_convolution_coefficient_bounded',*params,'i','x')+('exact hv_witness_right',),
        'The constructed convolution coefficient table is actually canonical at every encoded position.',
    )
    transport=spec(
        'prime_field_convolution_prefix_input_transport',
        f"forall {' '.join(params)} AB AC BB BC cb cc N. ({_equal('ab','ac','AB','AC','L','prefix_input_recode_a')}) -> ({_equal('bb','bc','BB','BC','M','prefix_input_recode_b')}) -> ({_prefix(*params,'cb','cc','N','prefix_input_old')}) -> ({_prefix('p','AB','AC','L','BB','BC','M','cb','cc','N','prefix_input_new')})",
        ('prime_field_convolution_coefficient_transport',),
        _intro(*params,'AB','AC','BB','BC','cb','cc','N','ha','hb','h','i','hi')
        +(f"have hv : exists r. {_and(_at('cb','cc','i','r','prefix_recode_entry'),_coefficient(*params,'i','r','prefix_recode_value'))}",)
        +_call('h','i')+('exact hi','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
        +_call('prime_field_convolution_coefficient_transport',*params,'i','AB','AC','BB','BC','x')+('exact ha','exact hb','exact hv_witness_right'),
        'Reencoding both finite inputs preserves the same actual canonical convolution output prefix.',
    )
    return *foundational,exists,bounded,transport


def _length_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body=_intro('L','M')+('have hl : L=0 \\/ exists l. L=S l',)+_call('zero_or_succ','L')+('cases hl','exists 0','left','split','left','exact hl_left','refl','cases hl_right','have hm : M=0 \\/ exists m. M=S m')
    body+=_call('zero_or_succ','M')+('cases hm','exists 0','left','split','right','exact hm_left','refl','cases hm_right','exists S (x+x1)','right','split','intro hz')
    body+=_call('succ_ne_zero','x')+('trans L','symm','exact hl_right_witness','exact hz','split','intro hz')
    body+=_call('succ_ne_zero','x1')+('trans M','symm','exact hm_right_witness','exact hz','rewrite hl_right_witness','rewrite hm_right_witness','simp [add_succ_left]')
    exists=spec(
        'polynomial_product_length_exists',
        f"forall L M. exists N. ({_length('L','M','N','length_exists')})",
        ('zero_or_succ','succ_ne_zero','add_succ_left'),body,
        'Construct the exact product representation length: zero for an empty input, and L+M-1 for two nonempty inputs.',
    )
    body=_intro('L','M','N','K','hn','hk')+('cases hn','cases hn_left','cases hk','cases hk_left','trans 0','exact hn_left_right','symm','exact hk_left_right')
    body+=_parts('hk_right',3)+('cases hn_left_left','exfalso','apply hk_right_left','exact hn_left_left_left','exfalso','apply hk_right_right_left','exact hn_left_left_right')
    body+=_parts('hn_right',3)+('cases hk','cases hk_left','cases hk_left_left','exfalso','apply hn_right_left','exact hk_left_left_left','exfalso','apply hn_right_right_left','exact hk_left_left_right')
    body+=_parts('hk_right',3)+('apply PA2','trans L+M','symm','exact hn_right_right_right','exact hk_right_right_right')
    functional=spec(
        'polynomial_product_length_functional',
        f"forall L M N K. ({_length('L','M','N','length_first')}) -> ({_length('L','M','K','length_second')}) -> N=K",
        (),body,
        'The proper finite convolution length is unique, with both-empty and one-empty cases handled explicitly.',
    )
    return exists,functional


def _convolution_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ab','ac','L','bb','bc','M')
    base=(*params,'cb','cc','N')
    bounded=spec(
        'prime_field_polynomial_convolution_bounded',
        f"forall {' '.join(base)}. ({_convolution(*base,'convolution_bound_source')}) -> ({_coeff('p','cb','cc','N','convolution_bound_result')})",
        ('prime_field_convolution_prefix_bounded',),
        _intro(*base,'h')+_parts('h',4)+_call('prime_field_convolution_prefix_bounded',*base)+('exact h_right_right_right',),
        'Every coefficient of the actual proper-length product is a canonical field representative.',
    )
    entry=spec(
        'prime_field_polynomial_convolution_entry',
        f"forall {' '.join(base)} i r. ({_convolution(*base,'convolution_entry_source')}) -> ({_lt('i','N','convolution_entry_bound')}) -> ({_at('cb','cc','i','r','convolution_entry_given')}) -> ({_coefficient(*params,'i','r','convolution_entry_result')})",
        ('prime_field_convolution_prefix_entry',),
        _intro(*base,'i','r','h','hi','hr')+_parts('h',4)+_call('prime_field_convolution_prefix_entry',*base,'i','r')+('exact h_right_right_right','exact hi','exact hr'),
        'Every actual decoded product coefficient has precisely the genuine antidiagonal-sum-and-residue certificate.',
    )
    body=_intro(*base,'AB','AC','BB','BC','CB','CC','ha','hb','hc','h')+_parts('h',4)+('split',)
    body+=_call('matrix_rank_bounded_prefix_transport','ab','ac','AB','AC','L','p')+('exact ha','exact h_left','split')
    body+=_call('matrix_rank_bounded_prefix_transport','bb','bc','BB','BC','M','p')+('exact hb','exact h_right_left','split','exact h_right_right_left')
    body+=_call('prime_field_convolution_prefix_recoding','p','AB','AC','L','BB','BC','M','cb','cc','CB','CC','N')+('exact hc',)
    body+=_call('prime_field_convolution_prefix_input_transport',*params,'AB','AC','BB','BC','cb','cc','N')+('exact ha','exact hb','exact h_right_right_right')
    transport=spec(
        'prime_field_polynomial_convolution_transport',
        f"forall {' '.join(base)} AB AC BB BC CB CC. ({_equal('ab','ac','AB','AC','L','convolution_recode_a')}) -> ({_equal('bb','bc','BB','BC','M','convolution_recode_b')}) -> ({_equal('cb','cc','CB','CC','N','convolution_recode_c')}) -> ({_convolution(*base,'convolution_old')}) -> ({_convolution('p','AB','AC','L','BB','BC','M','CB','CC','N','convolution_new')})",
        ('matrix_rank_bounded_prefix_transport','prime_field_convolution_prefix_recoding','prime_field_convolution_prefix_input_transport'),body,
        'Independent beta reencoding of both inputs and the output preserves the whole actual polynomial convolution.',
    )
    body=_intro(*base,'db','dc','K','hc','hd')+_parts('hc',4)+_parts('hd',4)+('have hlen : N=K',)
    body+=_call('polynomial_product_length_functional','L','M','N','K')+('exact hc_right_right_left','exact hd_right_right_left','split','exact hlen')
    body+=_rewrite_all('hlen',_equal('cb','cc','db','dc','N','convolution_unique_length_rewrite'),'N')
    body+=_rewrite_all('hlen',_prefix(*params,'cb','cc','N','convolution_unique_prefix_rewrite'),'N','hc_right_right_right')
    body+=_call('prime_field_convolution_prefix_functional',*params,'cb','cc','db','dc','K')+('exact hc_right_right_right','exact hd_right_right_right')
    functional=spec(
        'prime_field_polynomial_convolution_functional',
        f"forall {' '.join(base)} db dc K. ({_convolution(*base,'convolution_unique_first')}) -> ({_convolution(*params,'db','dc','K','convolution_unique_second')}) -> "
        +_and('N=K',_equal('cb','cc','db','dc','N','convolution_unique_result')),
        ('polynomial_product_length_functional','prime_field_convolution_prefix_functional'),body,
        'The proper output length and every encoded convolution coefficient are unique; beta code numbers themselves are not.',
    )
    at_length=spec(
        'prime_field_polynomial_convolution_at_length_exists',
        f"forall {' '.join(params)} N. ~(p=0) -> ({_coeff('p','ab','ac','L','convolution_exists_left')}) -> ({_coeff('p','bb','bc','M','convolution_exists_right')}) -> ({_length('L','M','N','convolution_exists_length')}) -> exists cb cc. ({_convolution(*params,'cb','cc','N','convolution_exists_result')})",
        ('prime_field_convolution_prefix_exists',),
        _intro(*params,'N','hp','ha','hb','hlen')+(f"have hc : exists cb cc. ({_prefix(*params,'cb','cc','N','convolution_exists_prefix')})",)
        +_call('prime_field_convolution_prefix_exists',*params,'N')+('exact hp','cases hc','cases hc_witness','exists x','exists x1','split','exact ha','split','exact hb','split','exact hlen','exact hc_witness_witness'),
        'Construct an actual canonical product at its proved proper length, using genuine finite antidiagonal computations.',
    )
    unique_contract=_and(_convolution(*params,'cb','cc','N','convolution_total_chosen'),
        f"forall db dc K. ({_convolution(*params,'db','dc','K','convolution_total_other')}) -> "+_and('N=K',_equal('cb','cc','db','dc','N','convolution_total_equal')))
    body=_intro(*params,'hp','ha','hb')+(f"have hn : exists N. ({_length('L','M','N','convolution_total_length')})",)+_call('polynomial_product_length_exists','L','M')+('cases hn',)
    body+=(f"have hc : exists cb cc. ({_convolution(*params,'cb','cc','x','convolution_total_actual')})",)+_call('prime_field_polynomial_convolution_at_length_exists',*params,'x')
    body+=('exact hp','exact ha','exact hb','exact hn_witness','cases hc','cases hc_witness','exists x','exists x1','exists x2','split','exact hc_witness_witness')
    body+=_intro('db','dc','K','hd')+_call('prime_field_polynomial_convolution_functional',*params,'x1','x2','x','db','dc','K')+('exact hc_witness_witness','exact hd')
    exists=spec(
        'prime_field_polynomial_convolution_exists_unique',
        f"forall {' '.join(params)}. ~(p=0) -> ({_coeff('p','ab','ac','L','convolution_total_left')}) -> ({_coeff('p','bb','bc','M','convolution_total_right')}) -> exists N cb cc. ({unique_contract})",
        ('polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists','prime_field_polynomial_convolution_functional'),body,
        'For every pair of canonical finite prefixes construct a genuine proper-length convolution, including empty inputs, and prove its exact length and coefficientwise uniqueness.',
    )
    empty=spec(
        'prime_field_polynomial_convolution_empty',
        f"forall {' '.join(params)} cb cc. ({_coeff('p','ab','ac','L','convolution_empty_left')}) -> ({_coeff('p','bb','bc','M','convolution_empty_right')}) -> (L=0 \\/ M=0) -> ({_convolution(*params,'cb','cc','0','convolution_empty_result')})",
        ('lt_not_le','zero_le'),
        _intro(*params,'cb','cc','ha','hb','hempty')+('split','exact ha','split','exact hb','split','left','split','exact hempty','refl')+_intro('i','hi')+('exfalso',)
        +_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i'),
        'Either empty input has the actual empty product; arbitrary empty output codes are equivalent and no spurious length-one coefficient is introduced.',
    )
    zeros=[]
    for side in ('left','right'):
        condition=_repeat('ab','ac','0','L','convolution_zero_left') if side=='left' else _repeat('bb','bc','0','M','convolution_zero_right')
        body=_intro(*base,'hp','hz','hc')+_parts('hc',4)+_intro('i','hi')
        body+=(f"have hv : exists r. {_and(_at('cb','cc','i','r','convolution_zero_entry_'+side),_coefficient(*params,'i','r','convolution_zero_value_'+side))}",)
        body+=_call('hc_right_right_right','i')+('exact hi','cases hv','cases hv_witness','have heq : x=0')
        body+=_call('prime_field_convolution_coefficient_zero_'+side,*params,'i','x')+('exact hp','exact hz','exact hv_witness_right')
        body+=_rewrite_all('heq',_at('cb','cc','i','x','convolution_zero_rewrite_'+side),'x','hv_witness_left')+('exact hv_witness_left',)
        zeros.append(spec(
            'prime_field_polynomial_convolution_zero_'+side,
            f"forall {' '.join(base)}. ~(p=0) -> ({condition}) -> ({_convolution(*base,'convolution_zero_source_'+side)}) -> ({_repeat('cb','cc','0','N','convolution_zero_result_'+side)})",
            ('prime_field_convolution_coefficient_zero_'+side,),body,
            f'An actual zero {side} polynomial yields an actually all-zero output prefix at the correct representation length.',
        ))
    body=_intro(*base,'i','r','hp','hconv','hi','hr')+_parts('hconv',4)+('cases hconv_right_right_left','cases hconv_right_right_left_left','cases hconv_right_right_left_left_left')
    for side,equality in (('left','hconv_right_right_left_left_left_left'),('right','hconv_right_right_left_left_left_right')):
        body+=_call('prime_field_convolution_coefficient_zero_'+side,*params,'i','r')+('exact hp',)+_intro('j','hj')+('exfalso',)
        length='L' if side=='left' else 'M'
        body+=_rewrite_all(equality,_lt('j',length,'outside_empty_bound_'+side),length,'hj')
        body+=_call('lt_not_le','j','0')+('exact hj',)+_call('zero_le','j')+('exact hr',)
    body+=_parts('hconv_right_right_left_right',3)
    body+=_call('prime_field_convolution_coefficient_zero_past_support',*params,'i','r')+('exact hp',)
    body+=_rewrite_all('hconv_right_right_left_right_right_right',_le('L+M','S i','outside_positive_bound'),'L+M')
    body+=_call('succ_le_succ','N','i')+('exact hi','exact hr')
    outside=spec(
        'prime_field_polynomial_convolution_outside_zero',
        f"forall {' '.join(base)} i r. ~(p=0) -> ({_convolution(*base,'outside_product')}) -> ({_le('N','i','outside_index')}) -> ({_coefficient(*params,'i','r','outside_coefficient')}) -> r=0",
        ('prime_field_convolution_coefficient_zero_left','prime_field_convolution_coefficient_zero_right','lt_not_le','zero_le','prime_field_convolution_coefficient_zero_past_support','succ_le_succ'),body,
        'Every genuine antidiagonal coefficient outside the proper product length is zero; this makes no assertion about arbitrary raw beta entries beyond the encoded output prefix.',
    )
    return bounded,entry,transport,functional,at_length,exists,empty,*zeros,outside


def make_prime_field_polynomial_convolution_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_padding_rows(spec),*_term_rows(spec),*_diagonal_rows(spec),*_coefficient_rows(spec),*_coefficient_boundary_rows(spec),*_convolution_prefix_rows(spec),*_length_rows(spec),*_convolution_rows(spec))


__all__=[
    'prime_field_polynomial_zero_extended_entry_relation','prime_field_polynomial_diagonal_term_relation',
    'prime_field_polynomial_diagonal_prefix_relation','prime_field_polynomial_convolution_coefficient_relation',
    'prime_field_polynomial_convolution_prefix_relation','prime_field_polynomial_product_length_relation',
    'prime_field_polynomial_convolution_relation','make_prime_field_polynomial_convolution_candidate_theorems',
]
