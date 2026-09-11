"""Actual rectangular CRT enumeration after the frozen Jordan51 checkpoint.

The inherited Jordan relation counts coordinate tuples, never beta encodings.
New rows are ordinary proof scripts; no definition contains cardinality
multiplication and no stored observation grants proof authority.
"""
from __future__ import annotations

import re
from . import jordan_totient_candidate as _base

_and,_at,_lt,_dvd,_cop,_mod=(_base._and,_base._at,_base._lt,_base._dvd,_base._cop,_base._mod)
_equal,_bounded,_primitive,_pm=_base._equal,_base._bounded,_base._primitive,_base._pointwise_mod
_entry=lambda B,C,D,E,i,b,c,tag:_and(_at(B,C,i,b,tag+'code'),_at(D,E,i,c,tag+'scale'))
_enum,_jordan,_crt=_base._enumeration,_base._jordan,_base._canonical_crt
_call,_intro,_parts,_part=_base._call,_base._intro,_base._parts,_base._part


def _le(a,b,tag):
    g,=_base._fresh(tag,(a,b),'gap')
    return f'exists {g}. {g}+({a})=({b})'


def _lcm(l,m,n,tag):
    d,=_base._fresh(tag,(l,m,n),'common')
    return _and(_and(_dvd(m,l,tag+'left'),_dvd(n,l,tag+'right')),
        f'forall {d}. ({_dvd(m,d,tag+"commonleft")}) -> ({_dvd(n,d,tag+"commonright")}) -> ({_dvd(l,d,tag+"least")})')


def _rewrite(eq,old,formula,hypothesis=None):
    count=len(re.findall(r'\b'+re.escape(old)+r'\b',formula))
    if count==0:raise ValueError('A requested literal rewrite has no occurrence')
    return tuple('rewrite '+eq+(' at '+hypothesis if hypothesis else '') for _ in range(count))


def _rect(m,n,k,A,B,C,D,u,E,F,G,H,v,P,Q,R,T,q,tag):
    args=(m,n,k,A,B,C,D,u,E,F,G,H,v,P,Q,R,T,q)
    p,i,j,b,c,d,e,f,g=_base._fresh(tag,args,'index','row','column','b','c','d','e','f','g')
    return (f'forall {p}. ({_lt(p,q,tag+"index")}) -> exists {i} {j} {b} {c} {d} {e} {f} {g}. '+
        _and(_lt(i,u,tag+'row'),_lt(j,v,tag+'column'),f'{p}=({v})*{i}+{j}',
             _entry(A,B,C,D,i,b,c,tag+'left'),_entry(E,F,G,H,j,d,e,tag+'right'),
             _entry(P,Q,R,T,p,f,g,tag+'output'),_crt(m,n,b,c,d,e,f,g,k,tag+'crt'),
             _primitive(f'{m}*{n}',f,g,k,tag+'primitive')))


def _rect_value(m,n,k,A,B,C,D,u,E,F,G,H,v,P,Q,R,T,p,i,j,b,c,d,e,f,g,tag):
    return _and(_lt(i,u,tag+'row'),_lt(j,v,tag+'column'),f'{p}=({v})*({i})+({j})',
        _entry(A,B,C,D,i,b,c,tag+'left'),_entry(E,F,G,H,j,d,e,tag+'right'),
        _entry(P,Q,R,T,p,f,g,tag+'output'),_crt(m,n,b,c,d,e,f,g,k,tag+'crt'),
        _primitive(f'{m}*{n}',f,g,k,tag+'primitive'))


def _enum_projection_rows(spec):
    sound=_intro('k','n','A','B','C','D','j','i','b','c','he','hi','hentry')
    sound+=_parts('he',3)+('cases hentry',)
    value=_and(_entry('A','B','C','D','i','d','e','enumvalue'),_bounded('d','e','k','n','enumvaluebound'),
               _primitive('n','d','e','k','enumvalueprimitive'))
    sound+=(f'have hv : exists d e. {value}',)+_call('he_left','i')+('exact hi','cases hv','cases hv_witness')
    sound+=_parts('hv_witness_witness',3)+('cases hv_witness_witness_left','have hb : x=b')
    sound+=_call('beta_at_unique','A','B','i','x','b')+('exact hv_witness_witness_left_left','exact hentry_left','have hc : x1=c')
    sound+=_call('beta_at_unique','C','D','i','x1','c')+('exact hv_witness_witness_left_right','exact hentry_right','split')
    for formula,hyp in ((_bounded('x','x1','k','n','valuebound'),'hv_witness_witness_right_left'),
                        (_primitive('n','x','x1','k','valueprimitive'),'hv_witness_witness_right_right')):
        sound+=_rewrite('hb','x',formula,hyp)+_rewrite('hc','x1',formula,hyp)+('exact '+hyp,)
    complete=_intro('k','n','A','B','C','D','j','b','c','he','hb','hp')+_parts('he',3)
    complete+=_call('he_right_left','b','c')+('exact hb','exact hp')
    distinct=_intro('k','n','A','B','C','D','j','i','h','b','c','d','e','he','hi','hh','hfirst','hsecond','hsame')
    distinct+=_parts('he',3)+_call('he_right_right','i','h','b','c','d','e')
    distinct+=('exact hi','exact hh','exact hfirst','exact hsecond','exact hsame')
    return (
        spec('jordan_enumeration_actual_value',f'forall k n A B C D j i b c. ({_enum("k","n","A","B","C","D","j","actualenum")}) -> ({_lt("i","j","actualindex")}) -> ({_entry("A","B","C","D","i","b","c","actualentry")}) -> '+_and(_bounded('b','c','k','n','actualbound'),_primitive('n','b','c','k','actualprimitive')),
             ('beta_at_unique',),sound,'Every actual decoded enumeration entry is bounded and primitive.'),
        spec('jordan_enumeration_complete',f'forall k n A B C D j b c. ({_enum("k","n","A","B","C","D","j","completeenum")}) -> ({_bounded("b","c","k","n","completebound")}) -> ({_primitive("n","b","c","k","completeprimitive")}) -> ({_base._listed("b","c","k","A","B","C","D","j","completelisted")})',
             (),complete,'Extract an actual list position for any primitive canonical tuple.'),
        spec('jordan_enumeration_distinct',f'forall k n A B C D j i h b c d e. ({_enum("k","n","A","B","C","D","j","distinctenum")}) -> ({_lt("i","j","distinctfirst")}) -> ({_lt("h","j","distinctsecond")}) -> ({_entry("A","B","C","D","i","b","c","distinctentryfirst")}) -> ({_entry("A","B","C","D","h","d","e","distinctentrysecond")}) -> ({_equal("b","c","d","e","k","distinctequal")}) -> i=h',
             (),distinct,'The independent enumeration graph identifies equal coordinate tuples with equal positions.'),
    )


def _rectangle_construction_rows(spec):
    args=('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q')
    body=_intro(*args,'hm','hn','hcop','hleft','hright','hold','hq')
    body+=('have hv : ~(v=0)','intro hvzero')+_call('jordan_rectangle_width_nonzero','u','v','q')
    body+=('exact hq','exact hvzero',f'have hcoords : exists i j. {_and("q=v*i+j",_lt("j","v","rectcolumn"))}')
    body+=_call('division_remainder_exists','v','q')+('exact hv','cases hcoords','cases hcoords_witness','cases hcoords_witness_witness')
    body+=(f'have hrow : {_lt("x","u","rectrow")}',)+_call('jordan_rectangle_quotient_bound','u','v','q','x','x1')
    body+=('exact hq','exact hcoords_witness_witness_left','exact hcoords_witness_witness_right')
    for prefix,index,modulus,outer,firstwitness in (
        ('hl','x','m',('A','B','C','D'),'x2'),('hr','x1','n',('E','F','G','H'),'x4')):
        bounds='hrow' if prefix=='hl' else 'hcoords_witness_witness_right'
        proofenum='hleft' if prefix=='hl' else 'hright'
        length='u' if prefix=='hl' else 'v'
        value=_and(_entry(*outer,index,'b','c',prefix+'entry'),_bounded('b','c','k',modulus,prefix+'bound'),_primitive(modulus,'b','c','k',prefix+'primitive'))
        # Obtain actual witnesses from the soundness clause; projection rows
        # will later handle arbitrary presentations of the same list entry.
        body+=(f'have {prefix}sound : forall i. ({_lt("i",length,prefix+"soundindex")}) -> exists b c. '+
               _and(_entry(*outer,'i','b','c',prefix+'soundentry'),_bounded('b','c','k',modulus,prefix+'soundbound'),_primitive(modulus,'b','c','k',prefix+'soundprimitive')),)
        body+=(f'have hcopy : {_enum("k",modulus,*outer,length,prefix+"enumcopy")}','exact '+proofenum,'cases hcopy','exact hcopy_left')
        body+=(f'have {prefix} : exists b c. {value}',)+_call(prefix+'sound',index)+('exact '+bounds,'cases '+prefix,'cases '+prefix+'_witness')
        body+=_parts(prefix+'_witness_witness',3)
    crtvalue=_and(_crt('m','n','x2','x3','x4','x5','f','g','k','rectchosencrt'),_primitive('m*n','f','g','k','rectchosenprimitive'))
    body+=(f'have hc : exists f g. {crtvalue}',)+_call('jordan_primitive_crt_tuple_exists','m','n','x2','x3','x4','x5','k')
    body+=('exact hm','exact hn','exact hcop','exact hl_witness_witness_right_right','exact hr_witness_witness_right_right','cases hc','cases hc_witness','cases hc_witness_witness')
    ext=_and(_equal('P','Q','U','V','q','rectpreservecodes'),_equal('R','T','W','X','q','rectpreservescales'),
             _at('U','V','q','x6','rectlastcode'),_at('W','X','q','x7','rectlastscale'))
    body+=(f'have hext : exists U V W X. {ext}',)+_call('jordan_tuple_outer_append_exists','P','Q','R','T','q','x6','x7')
    body+=('cases hext','cases hext_witness','cases hext_witness_witness','cases hext_witness_witness_witness')
    extnode='hext_witness_witness_witness_witness'
    body+=_parts(extnode,4)+('exists x8','exists x9','exists x10','exists x11')+_intro('p','hp')
    body+=(f'have hpc : p=q \\/ ({_lt("p","q","rectnewcase")})',)+_call('finite_lt_succ_eq_or_lt','q','p')
    body+=('exact hp','cases hpc')+tuple('exists '+v for v in ('x','x1','x2','x3','x4','x5','x6','x7'))
    body+=('split','exact hrow','split','exact hcoords_witness_witness_right','split','rewrite hpc_left','exact hcoords_witness_witness_left',
           'split','exact hl_witness_witness_left','split','exact hr_witness_witness_left','split','split')
    body+=('rewrite hpc_left','rewrite hpc_left','exact '+_part(extnode,4,2),
           'rewrite hpc_left','rewrite hpc_left','exact '+_part(extnode,4,3),'split','exact hc_witness_witness_left','exact hc_witness_witness_right')
    value=_rect_value('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','p','i','j','b','c','d','e','f','g','rectoldvalue')
    body+=(f'have hprev : exists i j b c d e f g. {value}',)+_call('hold','p')+('exact hpc_right',)
    body+=tuple('cases hprev'+'_witness'*i for i in range(8))
    pv='hprev'+'_witness'*8
    body+=_parts(pv,8)+('cases '+_part(pv,8,5),)+tuple('exists x'+str(i) for i in range(12,20))
    for i in range(5):body+=('split','exact '+_part(pv,8,i))
    body+=('split','split')
    body+=_call('jordan_tuple_equal_entry','P','Q','x8','x9','q','p','x18')
    body+=('exact '+_part(extnode,4,0),'exact hpc_right','exact '+_part(pv,8,5)+'_left')
    body+=_call('jordan_tuple_equal_entry','R','T','x10','x11','q','p','x19')
    body+=('exact '+_part(extnode,4,1),'exact hpc_right','exact '+_part(pv,8,5)+'_right','split','exact '+_part(pv,8,6),'exact '+_part(pv,8,7))

    prefixargs=('m','n','k','A','B','C','D','u','E','F','G','H','v')
    successor=_intro(*prefixargs,'q','hm','hn','hcop','hleft','hright','hold','hq')+_open('hold',4)
    successor+=_call('jordan_rectangle_crt_append',*prefixargs,'x','x1','x2','x3','q')
    successor+=('exact hm','exact hn','exact hcop','exact hleft','exact hright','exact hold_witness_witness_witness_witness','exact hq')

    total=_intro('m','n','k','A','B','C','D','u','E','F','G','H','v','hm','hn','hcop','hleft','hright')
    total+=('induction q','intro hq')+('exists 0',)*4+_intro('p','hp')+('exfalso',)
    total+=_call('lt_not_le','p','0')+('exact hp',)+_call('zero_le','p')
    total+=('intro hq',f'have hold : exists P Q R T. {_rect("m","n","k","A","B","C","D","u","E","F","G","H","v","P","Q","R","T","q","rectinductionold")}','apply IH')
    total+=_call('le_trans','q','S q','u*v')+_call('le_succ_self','q')+('exact hq',)
    total+=_call('jordan_rectangle_crt_successor',*prefixargs,'q')
    total+=('exact hm','exact hn','exact hcop','exact hleft','exact hright','exact hold','exact hq')
    return (
        spec('jordan_rectangle_crt_append','forall '+' '.join(args)+'. ~(m=0) -> ~(n=0) -> '+
             f'({_cop("m","n","rectappendcop")}) -> ({_enum("k","m","A","B","C","D","u","rectappendleft")}) -> ({_enum("k","n","E","F","G","H","v","rectappendright")}) -> '
             f'({_rect(*args,"rectappendold")}) -> ({_lt("q","u*v","rectappendbound")}) -> exists U V W X. '
             +_rect('m','n','k','A','B','C','D','u','E','F','G','H','v','U','V','W','X','S q','rectappendnew'),
             ('jordan_rectangle_width_nonzero','division_remainder_exists','jordan_rectangle_quotient_bound',
              'jordan_primitive_crt_tuple_exists','jordan_tuple_outer_append_exists','finite_lt_succ_eq_or_lt','jordan_tuple_equal_entry'),body,
             'At the next flat index, construct the actual primitive CRT tuple and append its code and scale to fresh beta lists.'),
        spec('jordan_rectangle_crt_successor','forall '+' '.join(prefixargs)+f' q. ~(m=0) -> ~(n=0) -> ({_cop("m","n","rectsuccessorcop")}) -> '
             f'({_enum("k","m","A","B","C","D","u","rectsuccessorleft")}) -> ({_enum("k","n","E","F","G","H","v","rectsuccessorright")}) -> '
             '(exists P Q R T. '+_rect(*prefixargs,'P','Q','R','T','q','rectsuccessorold')+f') -> ({_lt("q","u*v","rectsuccessorbound")}) -> exists P Q R T. '
             +_rect(*prefixargs,'P','Q','R','T','S q','rectsuccessornew'),
             ('jordan_rectangle_crt_append',),successor,
             'Eliminate the four actual prefix witnesses and append one CRT output in a separate constructive proof scope.'),
        spec('jordan_rectangle_crt_exists',f'forall m n k A B C D u E F G H v. ~(m=0) -> ~(n=0) -> ({_cop("m","n","rectexistscop")}) -> '
             f'({_enum("k","m","A","B","C","D","u","rectexistsleft")}) -> ({_enum("k","n","E","F","G","H","v","rectexistsright")}) -> forall q. ({_le("q","u*v","rectexistsbound")}) -> exists P Q R T. '+
             _rect('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q','rectexiststarget'),
             ('lt_not_le','zero_le','le_trans','le_succ_self','jordan_rectangle_crt_successor'),total,
             'HA induction constructs the genuine rectangular CRT output table at every prefix through u*v, including zero-width rectangles.'),
    )


def _geometry_rows(spec):
    nonzero=_intro('u','v','p','hp','hv')+('have hprod : u*v=0','rewrite hv','rewrite PA5','refl',
              'rewrite hprod at hp')+_call('lt_not_le','p','0')+('exact hp',)+_call('zero_le','p')

    quotient=_intro('u','v','p','i','j','hp','heq','hj')
    quotient+=(f'have hc : ({_le("u","i","quotle")}) \\/ ({_lt("i","u","quotlt")})',)
    quotient+=_call('le_or_lt','u','i')+('cases hc','exfalso',)
    quotient+=_call('lt_not_le','p','u*v')+('exact hp',)
    quotient+=_call('le_trans','u*v','v*i','p')
    quotient+=(f'have hm : {_le("v*u","v*i","quotmult")}',)+_call('mul_le_mul_left','u','i','v')
    quotient+=('exact hc_left','have hcomm : v*u=u*v')+_call('mul_comm','v','u')
    quotient+=('rewrite hcomm at hm','exact hm','rewrite heq')+_call('le_add_right','v*i','j')+('exact hc_right',)

    flat=_intro('u','v','i','j','hi','hj')
    flat+=(f'have hs : {_lt("v*i+j","v*i+v","flatadd")}',)
    flat+=_call('finite_add_lt_of_le_of_lt','v*i','v*i','j','v')+_call('le_refl','v*i')+('exact hj',)
    flat+=_call('lt_of_lt_of_le','v*i+j','v*i+v','u*v')+('exact hs',)
    flat+=(f'have hm : {_le("S i*v","u*v","flatmult")}',)+_call('mul_le_mul_right','S i','u','v')+('exact hi',)
    flat+=('have hcomm : S i*v=v*S i',)+_call('mul_comm','S i','v')
    flat+=('rewrite hcomm at hm','have hstep : v*S i=v*i+v','apply PA6','rewrite hstep at hm','exact hm')

    unique=_intro('v','i','j','r','s','hj','hs','heq')
    unique+=_call('division_remainder_unique','v','v*i+j','i','j','r','s')
    unique+=('refl','exact hj','exact heq','exact hs')
    return (
        spec('jordan_rectangle_width_nonzero',f'forall u v p. ({_lt("p","u*v","widthbound")}) -> ~(v=0)',
             ('lt_not_le','zero_le'),nonzero,'A genuine index below u*v forces the rectangle width to be positive.'),
        spec('jordan_rectangle_quotient_bound',f'forall u v p i j. ({_lt("p","u*v","quotbound")}) -> p=v*i+j -> ({_lt("j","v","quotremainder")}) -> ({_lt("i","u","quotresult")})',
             ('le_or_lt','lt_not_le','le_trans','mul_le_mul_left','mul_comm','le_add_right'),quotient,
             'An actual bounded row-major index has a row index below u; no division oracle is assumed.'),
        spec('jordan_rectangle_flat_bound',f'forall u v i j. ({_lt("i","u","flatrow")}) -> ({_lt("j","v","flatcolumn")}) -> ({_lt("v*i+j","u*v","flatresult")})',
             ('finite_add_lt_of_le_of_lt','le_refl','lt_of_lt_of_le','mul_le_mul_right','mul_comm'),flat,
             'Every actual pair of bounded indices has a row-major index below the literal product.'),
        spec('jordan_rectangle_pair_unique',f'forall v i j r s. ({_lt("j","v","uniquecolumn")}) -> ({_lt("s","v","uniqueother")}) -> v*i+j=v*r+s -> (i=r /\\ j=s)',
             ('division_remainder_unique',),unique,'Actual bounded quotient/remainder decomposition uniquely recovers both indices.'),
    )


def _congruence_rows(spec):
    congruent=_intro('n','b','c','d','e','k','heq','i','a','z','hi','ha','hz')
    congruent+=('have hval : a=z',)+_call('heq','i','a','z')+('exact hi','exact ha','exact hz','rewrite hval')
    congruent+=_call('mod_eq_refl','n','z')

    equal=_intro('n','b','c','d','e','k','hb','hd','hm','i','a','z','hi','ha','hz')
    equal+=_call('mod_eq_bounded_unique','n','a','z')
    equal+=_call('matrix_rank_bounded_prefix_value','b','c','k','n','i','a')+('exact hb','exact hi','exact ha')
    equal+=_call('matrix_rank_bounded_prefix_value','d','e','k','n','i','z')+('exact hd','exact hi','exact hz')
    equal+=_call('hm','i','a','z')+('exact hi','exact ha','exact hz')

    combine=_intro('m','n','b','c','d','e','k','hcop','hm','hn','i','a','z','hi','ha','hz')
    combine+=_call('mod_eq_lcm_merge','m*n','m','n','a','z')
    combine+=_call('coprime_product_is_lcm','m','n')+('exact hcop',)
    combine+=_call('hm','i','a','z')+('exact hi','exact ha','exact hz')
    combine+=_call('hn','i','a','z')+('exact hi','exact ha','exact hz')

    recover=_intro('n','b','c','d','e','f','g','h','s','k','hb','hd','hleft','hright','heq')
    recover+=(f'have hmiddle : {_pm("n","f","g","d","e","k","recovermiddle")}',)
    recover+=_call('jordan_tuple_congruence_trans','n','f','g','h','s','d','e','k')
    recover+=_call('jordan_tuple_equal_congruence','n','f','g','h','s','k')+('exact heq','exact hright')
    recover+=_call('jordan_tuple_bounded_congruence_equal','n','b','c','d','e','k')+('exact hb','exact hd')
    recover+=_call('jordan_tuple_congruence_trans','n','b','c','f','g','d','e','k')
    recover+=_call('jordan_tuple_congruence_symm','n','f','g','b','c','k')+('exact hleft',)
    recover+=('exact hmiddle',)

    unique=_intro('m','n','b','c','d','e','f','g','h','s','k','hcop','hf','hh')
    unique+=_parts('hf',3)+_parts('hh',3)
    unique+=_call('jordan_tuple_bounded_congruence_equal','m*n','f','g','h','s','k')+('exact hf_left','exact hh_left')
    unique+=_call('jordan_tuple_congruence_coprime_product','m','n','f','g','h','s','k')+('exact hcop',)
    for modulus,ic,is_,left,right in (('m','b','c','hf_right_left','hh_right_left'),('n','d','e','hf_right_right','hh_right_right')):
        unique+=_call('jordan_tuple_congruence_trans',modulus,'f','g',ic,is_,'h','s','k')+('exact '+left,)
        unique+=_call('jordan_tuple_congruence_symm',modulus,'h','s',ic,is_,'k')+('exact '+right,)
    return (
        spec('jordan_tuple_equal_congruence',f'forall n b c d e k. ({_equal("b","c","d","e","k","equalcong")}) -> ({_pm("n","b","c","d","e","k","equalcongresult")})',
             ('mod_eq_refl',),congruent,'Equal decoded coordinates are congruent at every modulus, including zero.'),
        spec('jordan_tuple_bounded_congruence_equal',f'forall n b c d e k. ({_bounded("b","c","k","n","congboundleft")}) -> ({_bounded("d","e","k","n","congboundright")}) -> ({_pm("n","b","c","d","e","k","congboth")}) -> ({_equal("b","c","d","e","k","congequal")})',
             ('mod_eq_bounded_unique','matrix_rank_bounded_prefix_value'),equal,
             'Actual canonical residues with pointwise congruence are equal as coordinate functions.'),
        spec('jordan_tuple_congruence_coprime_product',f'forall m n b c d e k. ({_cop("m","n","combinecop")}) -> ({_pm("m","b","c","d","e","k","combinem")}) -> ({_pm("n","b","c","d","e","k","combinen")}) -> ({_pm("m*n","b","c","d","e","k","combineproduct")})',
             ('mod_eq_lcm_merge','coprime_product_is_lcm'),combine,
             'The actual universal-property lcm merges both coordinate congruences.'),
        spec('jordan_crt_component_recovery',f'forall n b c d e f g h s k. ({_bounded("b","c","k","n","recoverleft")}) -> ({_bounded("d","e","k","n","recoverright")}) -> ({_pm("n","f","g","b","c","k","recoverfirst")}) -> ({_pm("n","h","s","d","e","k","recoversecond")}) -> ({_equal("f","g","h","s","k","recoveroutput")}) -> ({_equal("b","c","d","e","k","recoverinputs")})',
             ('jordan_tuple_bounded_congruence_equal','jordan_tuple_congruence_trans','jordan_tuple_congruence_symm','jordan_tuple_equal_congruence'),recover,
             'Equal output tuples recover equal canonical input components, not equal raw beta codes.'),
        spec('jordan_canonical_crt_tuple_unique',f'forall m n b c d e f g h s k. ({_cop("m","n","uniquecrtcop")}) -> ({_crt("m","n","b","c","d","e","f","g","k","uniquecrtfirst")}) -> ({_crt("m","n","b","c","d","e","h","s","k","uniquecrtsecond")}) -> ({_equal("f","g","h","s","k","uniquecrtoutputs")})',
             ('jordan_tuple_bounded_congruence_equal','jordan_tuple_congruence_coprime_product','jordan_tuple_congruence_trans','jordan_tuple_congruence_symm'),unique,
             'The actual two-coordinate CRT output is unique below the product modulus.'),
    )


def _open(name,count):
    return tuple('cases '+name+'_witness'*i for i in range(count))


def _rectangle_entry_rows(spec):
    args=('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T','q')
    value=lambda p,i,j,b,c,d,e,f,g,tag:_rect_value(*args[:-1],p,i,j,b,c,d,e,f,g,tag)
    located=_intro(*args,'p','f','g','hr','hp','he')
    located+=(f'have hv : exists i j b c d e f g. {value("p","i","j","b","c","d","e","f","g","located")}',)
    located+=_call('hr','p')+('exact hp',)+_open('hv',8)
    node='hv'+'_witness'*8
    located+=_parts(node,8)+('cases '+_part(node,8,5),'cases he','have hf : x6=f')
    located+=_call('beta_at_unique','P','Q','p','x6','f')+('exact '+_part(node,8,5)+'_left','exact he_left','have hg : x7=g')
    located+=_call('beta_at_unique','R','T','p','x7','g')+('exact '+_part(node,8,5)+'_right','exact he_right')
    located+=tuple('exists '+x for x in ('x','x1','x2','x3','x4','x5'))
    for i in range(5):located+=('split','exact '+_part(node,8,i))
    located+=('split','split','exact he_left','exact he_right','split')
    for formula,hyp in ((_crt('m','n','x2','x3','x4','x5','x6','x7','k','locrewrite'),_part(node,8,6)),
                        (_primitive('m*n','x6','x7','k','locprimrewrite'),_part(node,8,7))):
        located+=_rewrite('hf','x6',formula,hyp)+_rewrite('hg','x7',formula,hyp)+('exact '+hyp,)

    # Given a particular source pair, the flat position's quotient/remainder
    # witnesses and beta functionality recover those exact source entries.
    pairargs=args[:-1]+('i','j','b','c','d','e')
    pair=_intro(*pairargs,'hr','hi','hj','hl','hh')
    pair+=(f'have hp : {_lt("v*i+j","u*v","pairbound")}',)+_call('jordan_rectangle_flat_bound','u','v','i','j')+('exact hi','exact hj')
    pair+=(f'have hv : exists ri rj rb rc rd re rf rg. {value("v*i+j","ri","rj","rb","rc","rd","re","rf","rg","pairvalue")}',)
    pair+=_call('hr','v*i+j')+('exact hp',)+_open('hv',8)+_parts(node,8)
    pair+=('have hij : i=x /\\ j=x1',)+_call('jordan_rectangle_pair_unique','v','i','j','x','x1')
    pair+=('exact hj','exact '+_part(node,8,1),'exact '+_part(node,8,2),'cases hij')
    pair+=('cases '+_part(node,8,3),'cases '+_part(node,8,4),'cases hl','cases hh')
    for tag,outer,index,code,actual,hyp,entry in (
        ('hb',('A','B'),'i','b','x2','hl_left',_part(node,8,3)+'_left'),
        ('hc',('C','D'),'i','c','x3','hl_right',_part(node,8,3)+'_right'),
        ('hd',('E','F'),'j','d','x4','hh_left',_part(node,8,4)+'_left'),
        ('he',('G','H'),'j','e','x5','hh_right',_part(node,8,4)+'_right')):
        pair+=(f'have {tag} : {code}={actual}',)+_call('beta_at_unique',*outer,'x' if index=='i' else 'x1',code,actual)
        pair+=_rewrite('hij_left' if index=='i' else 'hij_right',index,_at(*outer,index,code,tag+'at'),hyp)+('exact '+hyp,'exact '+entry)
    pair+=('exists x6','exists x7','split','exact '+_part(node,8,5),'split')
    crt=_crt('m','n','b','c','d','e','x6','x7','k','pairrewrite')
    for eq,old in (('hb','b'),('hc','c'),('hd','d'),('he','e')):pair+=_rewrite(eq,old,crt)
    pair+=('exact '+_part(node,8,6),'exact '+_part(node,8,7))

    return (
        spec('jordan_rectangle_crt_actual_entry','forall '+' '.join(args)+f' p f g. ({_rect(*args,"locrect")}) -> ({_lt("p","q","locbound")}) -> ({_entry("P","Q","R","T","p","f","g","locentry")}) -> exists i j b c d e. '+value('p','i','j','b','c','d','e','f','g','locresult'),
             ('beta_at_unique',),located,'Decode an arbitrary actual output entry without identifying distinct beta representations.'),
        spec('jordan_rectangle_crt_pair_value','forall '+' '.join(pairargs)+f'. ({_rect(*args[:-1],"u*v","pairrect")}) -> ({_lt("i","u","pairrow")}) -> ({_lt("j","v","paircol")}) -> ({_entry("A","B","C","D","i","b","c","pairleft")}) -> ({_entry("E","F","G","H","j","d","e","pairright")}) -> exists f g. '+_and(_entry('P','Q','R','T','v*i+j','f','g','pairoutput'),_crt('m','n','b','c','d','e','f','g','k','paircrt'),_primitive('m*n','f','g','k','pairprimitive')),
             ('jordan_rectangle_flat_bound','jordan_rectangle_pair_unique','beta_at_unique'),pair,
             'The actual rectangular table realizes every prescribed pair of source entries at its unique flat index.'),
    )


def _enumeration_reduction_row(spec):
    body=_intro('n','k','A','B','C','D','j','b','c','hn','he','hp')
    normalized=_and(_bounded('d','e','k','n','reducebound'),_pm('n','b','c','d','e','k','reducemod'))
    body+=(f'have hnrm : exists d e. {normalized}',)+_call('jordan_tuple_normalize_exists','n','b','c','k')+('exact hn',)+_open('hnrm',2)+('cases hnrm_witness_witness',)
    body+=(f'have hprim : {_primitive("n","x","x1","k","reduceprim")}',)+_call('jordan_primitive_tuple_congruence_transport','n','b','c','x','x1','k')
    body+=('exact hnrm_witness_witness_right','exact hp')
    body+=(f'have hl : {_base._listed("x","x1","k","A","B","C","D","j","reducelisted")}',)
    body+=_call('jordan_enumeration_complete','k','n','A','B','C','D','j','x','x1')+('exact he','exact hnrm_witness_witness_left','exact hprim')
    body+=_open('hl',3)+_parts('hl_witness_witness_witness',3)
    body+=('exists x2','exists x3','exists x4','split','exact hl_witness_witness_witness_left','split','exact hl_witness_witness_witness_right_left')
    body+=_call('jordan_tuple_congruence_trans','n','b','c','x','x1','x3','x4','k')+('exact hnrm_witness_witness_right',)
    body+=_call('jordan_tuple_equal_congruence','n','x','x1','x3','x4','k')+('exact hl_witness_witness_witness_right_right',)
    return spec('jordan_enumeration_reduce_primitive',f'forall n k A B C D j b c. ~(n=0) -> ({_enum("k","n","A","B","C","D","j","reduceenum")}) -> ({_primitive("n","b","c","k","reduceinput")}) -> exists i d e. '+_and(_lt('i','j','reduceindex'),_entry('A','B','C','D','i','d','e','reduceentry'),_pm('n','b','c','d','e','k','reduceresult')),
        ('jordan_tuple_normalize_exists','jordan_primitive_tuple_congruence_transport','jordan_enumeration_complete','jordan_tuple_congruence_trans','jordan_tuple_equal_congruence'),body,
        'Reduce any primitive tuple to an actual canonical enumeration entry, retaining coordinate congruences and the genuine index.')


def _rectangle_enumeration_rows(spec):
    args=('m','n','k','A','B','C','D','u','E','F','G','H','v','P','Q','R','T')
    rect=_rect(*args,'u*v','enumrect')
    left=_enum('k','m','A','B','C','D','u','enumleft')
    right=_enum('k','n','E','F','G','H','v','enumright')
    distinct=_intro(*args,'p','z','f','g','h','s','hl','hh','hr','hp','hz','he','hf','hsame')
    nodes=[]
    for prefix,index,code,scale,bound,entry in (('ha','p','f','g','hp','he'),('hb','z','h','s','hz','hf')):
        val=_rect_value(*args,index,'i','j','b','c','d','e',code,scale,prefix+'value')
        distinct+=(f'have {prefix} : exists i j b c d e. {val}',)
        distinct+=_call('jordan_rectangle_crt_actual_entry',*args,'u*v',index,code,scale)+('exact hr','exact '+bound,'exact '+entry)
        distinct+=_open(prefix,6)
        node=prefix+'_witness'*6;nodes.append(node)
        distinct+=_parts(node,8)
        distinct+=(f'have {prefix}crt : {_crt("m","n","x2" if prefix=="ha" else "x8","x3" if prefix=="ha" else "x9","x4" if prefix=="ha" else "x10","x5" if prefix=="ha" else "x11",code,scale,"k",prefix+"crt")}',
                   'exact '+_part(node,8,6))+_parts(prefix+'crt',3)
    an,bn=nodes
    for label,modulus,outer,length,indices,tuplecodes,clause in (
        ('left','m',('A','B','C','D'),'u',('x','x6'),(('x2','x3'),('x8','x9')),3),
        ('right','n',('E','F','G','H'),'v',('x1','x7'),(('x4','x5'),('x10','x11')),4)):
        for position,(index,(code,scale),node) in enumerate(zip(indices,tuplecodes,nodes)):
            nm=label+str(position)
            formula=_and(_bounded(code,scale,'k',modulus,nm+'bound'),_primitive(modulus,code,scale,'k',nm+'primitive'))
            distinct+=(f'have {nm} : {formula}',)+_call('jordan_enumeration_actual_value','k',modulus,*outer,length,index,code,scale)
            distinct+=('exact '+('hl' if label=='left' else 'hh'),'exact '+_part(node,8,0 if label=='left' else 1),'exact '+_part(node,8,clause),'cases '+nm)
        (b,c),(d,e)=tuplecodes
        distinct+=(f'have {label}same : {_equal(b,c,d,e,"k",label+"same")}',)
        distinct+=_call('jordan_crt_component_recovery',modulus,b,c,d,e,'f','g','h','s','k')
        distinct+=('exact '+label+'0_left','exact '+label+'1_left','exact '+_part('hacrt',3,1 if label=='left' else 2),
                   'exact '+_part('hbcrt',3,1 if label=='left' else 2),'exact hsame')
        distinct+=(f'have {label}index : {indices[0]}={indices[1]}',)
        distinct+=_call('jordan_enumeration_distinct','k',modulus,*outer,length,*indices,b,c,d,e)
        distinct+=('exact '+('hl' if label=='left' else 'hh'),'exact '+_part(an,8,0 if label=='left' else 1),
                   'exact '+_part(bn,8,0 if label=='left' else 1),'exact '+_part(an,8,clause),'exact '+_part(bn,8,clause),'exact '+label+'same')
    distinct+=('have hpos : p=v*x+x1','exact '+_part(an,8,2),'rewrite leftindex at hpos','rewrite rightindex at hpos',
               'trans v*x6+x7','exact hpos','symm','exact '+_part(bn,8,2))

    covers=_intro(*args,'b','c','hm','hn','hcop','hl','hh','hr','hbound','hprim')
    components=_and(_primitive('m','b','c','k','coverm'),_primitive('n','b','c','k','covern'))
    covers+=(f'have hcomponents : {components}',)+_call('jordan_primitive_tuple_product_components','m','n','b','c','k')+('exact hprim','cases hcomponents')
    for prefix,modulus,outer,length,nonzero,enumeration,primitive in (
        ('ha','m',('A','B','C','D'),'u','hm','hl','hcomponents_left'),
        ('hb','n',('E','F','G','H'),'v','hn','hh','hcomponents_right')):
        reduced=_and(_lt('i',length,prefix+'index'),_entry(*outer,'i','d','e',prefix+'entry'),_pm(modulus,'b','c','d','e','k',prefix+'mod'))
        covers+=(f'have {prefix} : exists i d e. {reduced}',)+_call('jordan_enumeration_reduce_primitive',modulus,'k',*outer,length,'b','c')
        covers+=('exact '+nonzero,'exact '+enumeration,'exact '+primitive)+_open(prefix,3)+_parts(prefix+'_witness'*3,3)
    pair=_and(_entry('P','Q','R','T','v*x+x3','f','g','coverentry'),_crt('m','n','x1','x2','x4','x5','f','g','k','covercrt'),_primitive('m*n','f','g','k','coverprimitive'))
    covers+=(f'have hout : exists f g. {pair}',)+_call('jordan_rectangle_crt_pair_value',*args,'x','x3','x1','x2','x4','x5')
    covers+=('exact hr','exact ha_witness_witness_witness_left','exact hb_witness_witness_witness_left',
             'exact ha_witness_witness_witness_right_left','exact hb_witness_witness_witness_right_left')
    covers+=_open('hout',2)+_parts('hout_witness_witness',3)
    covers+=('exists v*x+x3','exists x6','exists x7','split')+_call('jordan_rectangle_flat_bound','u','v','x','x3')
    covers+=('exact ha_witness_witness_witness_left','exact hb_witness_witness_witness_left','split','exact hout_witness_witness_left')
    covers+=_call('jordan_canonical_crt_tuple_unique','m','n','x1','x2','x4','x5','b','c','x6','x7','k')
    covers+=('exact hcop','split','exact hbound','split','exact ha_witness_witness_witness_right_right',
             'exact hb_witness_witness_witness_right_right','exact hout_witness_witness_right_left')

    enumeration=_intro(*args,'hm','hn','hcop','hl','hh','hr')+('split',)+_intro('p','hp')
    val=_rect_value(*args,'p','i','j','b','c','d','e','f','g','soundrectvalue')
    enumeration+=(f'have hv : exists i j b c d e f g. {val}',)+_call('hr','p')+('exact hp',)+_open('hv',8)
    node='hv'+'_witness'*8
    enumeration+=_parts(node,8)+('exists x6','exists x7','split','exact '+_part(node,8,5),'split')
    enumeration+=(f'have hc : {_crt("m","n","x2","x3","x4","x5","x6","x7","k","soundcrt")}',
                  'exact '+_part(node,8,6),'cases hc','exact hc_left','exact '+_part(node,8,7),'split')
    enumeration+=_intro('b','c','hb','hp')+_call('jordan_rectangle_crt_covers',*args,'b','c')
    enumeration+=('exact hm','exact hn','exact hcop','exact hl','exact hh','exact hr','exact hb','exact hp')
    enumeration+=_intro('i','j','b','c','d','e','hi','hj','he','hf','hsame')
    enumeration+=_call('jordan_rectangle_crt_distinct',*args,'i','j','b','c','d','e')
    enumeration+=('exact hl','exact hh','exact hr','exact hi','exact hj','exact he','exact hf','exact hsame')
    common=f'~(m=0) -> ~(n=0) -> ({_cop("m","n","rectenumcop")}) -> ({left}) -> ({right}) -> ({rect}) -> '
    return (
        spec('jordan_rectangle_crt_distinct','forall '+' '.join(args)+f' p z f g h s. ({left}) -> ({right}) -> ({rect}) -> ({_lt("p","u*v","distinctp")}) -> ({_lt("z","u*v","distinctz")}) -> ({_entry("P","Q","R","T","p","f","g","distinctentryp")}) -> ({_entry("P","Q","R","T","z","h","s","distinctentryz")}) -> ({_equal("f","g","h","s","k","distinctoutputs")}) -> p=z',
             ('jordan_rectangle_crt_actual_entry','jordan_enumeration_actual_value','jordan_crt_component_recovery','jordan_enumeration_distinct'),distinct,
             'Equal decoded CRT output tuples recover equal source positions and hence the same flat index.'),
        spec('jordan_rectangle_crt_covers','forall '+' '.join(args)+f' b c. '+common+f'({_bounded("b","c","k","m*n","coverbound")}) -> ({_primitive("m*n","b","c","k","coverprim")}) -> ({_base._listed("b","c","k","P","Q","R","T","u*v","coverlisted")})',
             ('jordan_primitive_tuple_product_components','jordan_enumeration_reduce_primitive','jordan_rectangle_crt_pair_value','jordan_rectangle_flat_bound','jordan_canonical_crt_tuple_unique'),covers,
             'Every primitive product-modulus tuple reduces to a genuine source pair and is formally equal to its table output.'),
        spec('jordan_rectangle_crt_enumeration','forall '+' '.join(args)+'. '+common+_enum('k','m*n','P','Q','R','T','u*v','productenum'),
             ('jordan_rectangle_crt_covers','jordan_rectangle_crt_distinct'),enumeration,
             'The constructed table is a duplicate-free exhaustive primitive tuple enumeration of literal length u*v.'),
    )


def _multiplicativity_rows(spec):
    args=('m','n','k','A','B','C','D','u','E','F','G','H','v')
    output=_enum('k','m*n','P','Q','R','T','u*v','mulenumoutput')
    table=_rect(*args,'P','Q','R','T','u*v','mulenumtable')
    exists=_intro(*args,'hm','hn','hcop','hl','hh')
    alltable=f'forall q. ({_le("q","u*v","multablebound")}) -> exists P Q R T. '+_rect(*args,'P','Q','R','T','q','multableprefix')
    exists+=(f'have ht : {alltable}',)+_call('jordan_rectangle_crt_exists',*args)
    exists+=('exact hm','exact hn','exact hcop','exact hl','exact hh',f'have hv : exists P Q R T. {table}')
    exists+=_call('ht','u*v')+_call('le_refl','u*v')+_open('hv',4)
    exists+=('exists x','exists x1','exists x2','exists x3')+_call('jordan_rectangle_crt_enumeration',*args,'x','x1','x2','x3')
    exists+=('exact hm','exact hn','exact hcop','exact hl','exact hh','exact hv_witness_witness_witness_witness')

    multiply=_intro('k','a','b','u','v','hcop','ha','hb')+_parts('ha',3)+_parts('hb',3)
    multiply+=_open('ha_right_right',4)+_open('hb_right_right',4)
    multiply+=('split','exact ha_left','split','intro hz')+_call('mul_ne_zero','a','b')
    multiply+=('exact ha_right_left','exact hb_right_left','exact hz')
    multiply+=_call('jordan_product_enumeration_exists','a','b','k','x','x1','x2','x3','u','x4','x5','x6','x7','v')
    multiply+=('exact ha_right_left','exact hb_right_left','exact hcop','exact ha_right_right_witness_witness_witness_witness','exact hb_right_right_witness_witness_witness_witness')

    endpoint=_intro('k','a','b','hk','ha','hb','hcop')
    endpoint+=(f'have hu : exists u. {_jordan("k","a","u","endpointleft")}',)+_call('jordan_totient_exists','k','a')+('exact hk','exact ha','cases hu')
    endpoint+=(f'have hv : exists v. {_jordan("k","b","v","endpointright")}',)+_call('jordan_totient_exists','k','b')+('exact hk','exact hb','cases hv')
    endpoint+=('exists x','exists x1','exists x*x1','split','exact hu_witness','split','exact hv_witness','split')
    endpoint+=_call('jordan_totient_coprime_product','k','a','b','x','x1')+('exact hcop','exact hu_witness','exact hv_witness','refl')
    return (
        spec('jordan_product_enumeration_exists','forall '+' '.join(args)+f'. ~(m=0) -> ~(n=0) -> ({_cop("m","n","mulenumcop")}) -> ({_enum("k","m","A","B","C","D","u","mulenumleft")}) -> ({_enum("k","n","E","F","G","H","v","mulenumright")}) -> exists P Q R T. '+output,
             ('jordan_rectangle_crt_exists','le_refl','jordan_rectangle_crt_enumeration'),exists,
             'Construct an actual product enumeration; no count-uniqueness or multiplicativity premise is used.'),
        spec('jordan_totient_coprime_product',f'forall k a b u v. ({_cop("a","b","jmulcop")}) -> ({_jordan("k","a","u","jmulleft")}) -> ({_jordan("k","b","v","jmulright")}) -> ({_jordan("k","a*b","u*v","jmulresult")})',
             ('mul_ne_zero','jordan_product_enumeration_exists'),multiply,
             'Actual finite tuple-count Jordan values multiply at coprime moduli.'),
        spec('jordan_totient_multiplicativity_exists',f'forall k a b. ~(k=0) -> ~(a=0) -> ~(b=0) -> ({_cop("a","b","jendpointcop")}) -> exists u v w. '+_and(_jordan('k','a','u','jendpointleft'),_jordan('k','b','v','jendpointright'),_jordan('k','a*b','w','jendpointproduct'),'w=u*v'),
             ('jordan_totient_exists','jordan_totient_coprime_product'),endpoint,
             'The requested constructive G008 coprime multiplicativity endpoint with all three actual counts supplied.'),
    )


def make_jordan_multiplicativity_candidate_theorems(spec):
    return (_geometry_rows(spec)+_congruence_rows(spec)+_enum_projection_rows(spec)+_rectangle_construction_rows(spec)
            +_rectangle_entry_rows(spec)+(_enumeration_reduction_row(spec),)+_rectangle_enumeration_rows(spec)+_multiplicativity_rows(spec))
