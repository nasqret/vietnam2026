"""Working division checks using exact small source-provider hypotheses.

Independent graph expansions are shared only with the sibling test's plain
syntax helpers, never with a production graph builder or accepting checker.
Conditional original-HA body checks are not admission or closed-proof claims.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
import importlib.util
import itertools
import math
import re
from pathlib import Path

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


def load_sibling(name):
    source=Path(__file__).with_name(name+'.py')
    spec=importlib.util.spec_from_file_location('working_'+name,source)
    assert spec is not None and spec.loader is not None
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


candidate=load_sibling('prime_field_polynomial_division_candidate')
independent=load_sibling('test_prime_field_polynomial_convolution_triangular_candidate')


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_division_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.finite_permutation_theorems import make_finite_permutation_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
    from peano_lab.library.prime_field_polynomial_subtraction_candidate import make_prime_field_polynomial_subtraction_candidate_theorems
    from peano_lab.library.prime_field_polynomial_trim_candidate import make_prime_field_polynomial_trim_candidate_theorems

    result=independent.body_core()
    for factory in (make_finite_permutation_theorems,make_matrix_rank_finite_coding_candidate_theorems,
                    make_prime_field_polynomial_subtraction_candidate_theorems,
                    make_prime_field_polynomial_trim_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name]==row
            result[row.name]=row
    return result


def body_core():
    return provider_core() | {row.name:row for row in rows()}


conj=independent.conj
at=independent.at
lt=independent.lt
le=independent.le
equal=independent.equal
multiply=independent.multiply
add=independent.add
coefficient=independent.coefficient
format_contract=independent.format_contract
exact_ast=independent.exact_ast


def prime(p):
    return f'~(({p})=1) /\\ forall independent_factor_a independent_factor_b. ({p})=independent_factor_a*independent_factor_b -> independent_factor_a=1 \\/ independent_factor_b=1'


def inverse(p,b,k):
    return conj(f'~(({b})=0)',multiply(p,b,k,'1'))


def coeff(p,b,c,n):
    return f'forall independent_coeff_i. ({lt("independent_coeff_i",n)}) -> exists independent_coeff_a. '+conj(
        at(b,c,'independent_coeff_i','independent_coeff_a'),lt('independent_coeff_a',p))


def repeat(b,c,a,n):
    return f'forall independent_repeat_i. ({lt("independent_repeat_i",n)}) -> ({at(b,c,"independent_repeat_i",a)})'


def step(p,k,ab,ac,bb,bc,M,qb,qc,i,q):
    return 'exists independent_step_a independent_step_c independent_step_s. '+conj(
        at(ab,ac,i,'independent_step_a'),
        coefficient(p,qb,qc,i,bb,bc,M,i,'independent_step_c'),
        add(p,'independent_step_c','independent_step_s','independent_step_a'),
        multiply(p,k,'independent_step_s',q))


def prefix(p,k,ab,ac,bb,bc,M,qb,qc,N):
    return f'forall independent_execution_i. ({lt("independent_execution_i",N)}) -> exists independent_execution_q. '+conj(
        at(qb,qc,'independent_execution_i','independent_execution_q'),
        step(p,k,ab,ac,bb,bc,M,qb,qc,'independent_execution_i','independent_execution_q'))


def product_prefix(p,ab,ac,L,bb,bc,M,pb,pc,N):
    return f'forall independent_product_i. ({lt("independent_product_i",N)}) -> exists independent_product_r. '+conj(
        at(pb,pc,'independent_product_i','independent_product_r'),
        coefficient(p,ab,ac,L,bb,bc,M,'independent_product_i','independent_product_r'))


def subtract(p,ab,ac,pb,pc,ub,uc,L):
    return f'forall independent_sub_i. ({lt("independent_sub_i",L)}) -> exists independent_sub_a independent_sub_b independent_sub_r. '+conj(
        at(ab,ac,'independent_sub_i','independent_sub_a'),at(pb,pc,'independent_sub_i','independent_sub_b'),
        at(ub,uc,'independent_sub_i','independent_sub_r'),add(p,'independent_sub_b','independent_sub_r','independent_sub_a'))


def degree(p,b,c,L,d):
    return conj(f'({L})=S ({d})',coeff(p,b,c,L),'exists independent_degree_a. '+conj(
        at(b,c,'0','independent_degree_a'),'~(independent_degree_a=0)'))


def trim(p,b,c,L,t,rb,rc,R):
    suffix=f'forall independent_suffix_i independent_suffix_a. ({lt("independent_suffix_i",R)}) -> '+(
        f'({at(b,c,f"({t})+independent_suffix_i","independent_suffix_a")}) -> '
        f'({at(rb,rc,"independent_suffix_i","independent_suffix_a")})')
    head='exists independent_trim_head. '+conj(at(rb,rc,'0','independent_trim_head'),'~(independent_trim_head=0)')
    return conj(f'({L})=({t})+({R})',coeff(p,b,c,L),repeat(b,c,'0',t),suffix,f'({R})=0 \\/ ({head})')


def quotient_length(L,d,q):
    return f'({conj(f"({q})=0",le(L,d))}) \\/ ({conj(f"~(({q})=0)",f"({q})+({d})=({L})")})'


def execution(p,ab,ac,L,bb,bc,d,qb,qc,q,rb,rc,R):
    b,k,pb,pc,ub,uc,t=('independent_execution_'+role for role in ('b','k','pb','pc','ub','uc','t'))
    data=conj(at(bb,bc,'0',b),inverse(p,b,k),prefix(p,k,ab,ac,bb,bc,f'S ({d})',qb,qc,q),
              product_prefix(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L),subtract(p,ab,ac,pb,pc,ub,uc,L),
              trim(p,ub,uc,L,t,rb,rc,R))
    return conj(coeff(p,ab,ac,L),coeff(p,bb,bc,f'S ({d})'),quotient_length(L,d,q),
                f'exists {b} {k} {pb} {pc} {ub} {uc} {t}. {data}')


def remainder_degree(p,rb,rc,R,d):
    return f'({R})=0 \\/ (exists independent_remainder_e. '+conj(
        degree(p,rb,rc,R,'independent_remainder_e'),lt('independent_remainder_e',d))+')'


def quotient_data(p,ab,ac,L,bb,bc,d,b,k,q,qb,qc):
    return conj(at(bb,bc,'0',b),inverse(p,b,k),quotient_length(L,d,q),prefix(p,k,ab,ac,bb,bc,f'S ({d})',qb,qc,q))


def residual_data(p,ab,ac,L,bb,bc,d,qb,qc,q,pb,pc,ub,uc,t,rb,rc,R):
    return conj(product_prefix(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L),
                subtract(p,ab,ac,pb,pc,ub,uc,L),trim(p,ub,uc,L,t,rb,rc,R))


def product_length(L,M,N):
    empty=f'({L})=0 \\/ ({M})=0'
    return f'({conj(empty,f"({N})=0")}) \\/ ('+conj(
        f'~(({L})=0)',f'~(({M})=0)',f'({L})+({M})=S ({N})')+')'


def product(p,ab,ac,L,bb,bc,M,pb,pc,N):
    return conj(coeff(p,ab,ac,L),coeff(p,bb,bc,M),product_length(L,M,N),
                product_prefix(p,ab,ac,L,bb,bc,M,pb,pc,N))


def polynomial_add(p,pb,pc,ub,uc,ab,ac,L):
    return f'forall independent_add_i. ({lt("independent_add_i",L)}) -> exists independent_add_p independent_add_u independent_add_a. '+conj(
        at(pb,pc,'independent_add_i','independent_add_p'),at(ub,uc,'independent_add_i','independent_add_u'),
        at(ab,ac,'independent_add_i','independent_add_a'),add(p,'independent_add_p','independent_add_u','independent_add_a'))


def coefficient_identity(p,ab,ac,L,bb,bc,d,qb,qc,q,rb,rc,R):
    pb,pc,ub,uc,t=('independent_identity_'+role for role in ('pb','pc','ub','uc','t'))
    alternative=f'({conj(f"({q})=0",repeat(pb,pc,"0",L))}) \\/ ('+conj(
        f'~(({q})=0)',product(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L))+')'
    return f'exists {pb} {pc} {ub} {uc} {t}. '+conj(
        alternative,polynomial_add(p,pb,pc,ub,uc,ab,ac,L),trim(p,ub,uc,L,t,rb,rc,R))


def contracts():
    base=('p','k','ab','ac','bb','bc','M','qb','qc')
    actual=lambda n:prefix(*base,n)
    matching=(prime('p'),at('bb','bc','0','b'),inverse('p','b','k'),
              prefix('p','k','ab','ac','bb','bc','S d','qb','qc','N'))
    table=(*matching,le('N','L'),product_prefix('p','qb','qc','N','bb','bc','S d','pb','pc','L'))
    return (
        ('p b k c s a q t r',(prime('p'),inverse('p','b','k'),add('p','c','s','a'),
          multiply('p','k','s','q'),multiply('p','q','b','t'),add('p','c','t','r')),'r=a'),
        ('p k ab ac bb bc M qb qc QB QC i q',(equal('qb','qc','QB','QC','i'),step(*base,'i','q')),
         step('p','k','ab','ac','bb','bc','M','QB','QC','i','q')),
        (' '.join(base),(),actual('0')),
        (' '.join(base)+' N K',(le('K','N'),actual('N')),actual('K')),
        (' '.join(base)+' N i q',(actual('N'),lt('i','N'),at('qb','qc','i','q')),step(*base,'i','q')),
        (' '.join(base)+' N',(actual('N'),),coeff('p','qb','qc','N')),
        ('p k ab ac bb bc M qb qc QB QC N q',
         (actual('N'),equal('qb','qc','QB','QC','N'),at('QB','QC','N','q'),step(*base,'N','q')),
         prefix('p','k','ab','ac','bb','bc','M','QB','QC','S N')),
        ('p k ab ac bb bc M N',(prime('p'),lt('k','p'),coeff('p','ab','ac','N')),
         'exists qb qc. ('+actual('N')+')'),
        ('p k ab ac bb bc d qb qc N b i r',(*matching,lt('i','N'),coefficient('p','qb','qc','N','bb','bc','S d','i','r')),
         at('ab','ac','i','r')),
        ('p k ab ac bb bc d qb qc N b pb pc L',table,equal('ab','ac','pb','pc','N')),
        ('p k ab ac bb bc d qb qc N b pb pc L ub uc',(*table,subtract('p','ab','ac','pb','pc','ub','uc','L')),
         repeat('ub','uc','0','N')),
        ('L d',(),'exists q. ('+quotient_length('L','d','q')+')'),
        ('L d q',(quotient_length('L','d','q'),),conj(le('q','L'),le('L','q+d'))),
        ('p ub uc L t rb rc R q',(le('q','L'),repeat('ub','uc','0','q'),trim('p','ub','uc','L','t','rb','rc','R')),le('q','t')),
        ('p ub uc L t rb rc R q d',(le('q','L'),le('L','q+d'),repeat('ub','uc','0','q'),
          trim('p','ub','uc','L','t','rb','rc','R')),le('R','d')),
        ('p ub uc L t rb rc R d',(trim('p','ub','uc','L','t','rb','rc','R'),le('R','d')),
         remainder_degree('p','rb','rc','R','d')),
        ('p ab ac L bb bc d',(prime('p'),coeff('p','ab','ac','L'),degree('p','bb','bc','S d','d')),
         'exists b k q qb qc. ('+quotient_data('p','ab','ac','L','bb','bc','d','b','k','q','qb','qc')+')'),
        ('p ab ac L bb bc d qb qc q',(prime('p'),coeff('p','ab','ac','L')),
         'exists pb pc ub uc t rb rc R. ('+residual_data('p','ab','ac','L','bb','bc','d','qb','qc','q','pb','pc','ub','uc','t','rb','rc','R')+')'),
        ('p ab ac L bb bc d',(prime('p'),coeff('p','ab','ac','L'),degree('p','bb','bc','S d','d')),
         'exists qb qc q rb rc R. ('+execution('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')+')'),
        ('p ab ac L bb bc d qb qc q rb rc R',
         (prime('p'),execution('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')),
         remainder_degree('p','rb','rc','R','d')),
        ('p ab ac L bb bc d',(prime('p'),coeff('p','ab','ac','L'),degree('p','bb','bc','S d','d')),
         'exists qb qc q rb rc R. '+conj(execution('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R'),
                                       remainder_degree('p','rb','rc','R','d'))),
        ('L d q',(quotient_length('L','d','q'),'~(q=0)'),product_length('q','S d','L')),
        ('p k ab ac bb bc d qb qc q pb pc L',
         (quotient_length('L','d','q'),'~(q=0)',coeff('p','bb','bc','S d'),
          prefix('p','k','ab','ac','bb','bc','S d','qb','qc','q'),product_prefix('p','qb','qc','q','bb','bc','S d','pb','pc','L')),
         product('p','qb','qc','q','bb','bc','S d','pb','pc','L')),
        ('p qb qc bb bc M pb pc L',('~(p=0)',product_prefix('p','qb','qc','0','bb','bc','M','pb','pc','L')),repeat('pb','pc','0','L')),
        ('p ab ac L bb bc d qb qc q rb rc R',
         (prime('p'),execution('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')),
         coefficient_identity('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')),
    )


def test_local_topology_has_only_actual_earlier_source_dependencies():
    known=set(provider_core())
    assert len(rows())==len(contracts())
    for row in rows():
        assert row.name not in known
        assert row.script and len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=known
        known.add(row.name)


METRICS=((95,35),(118,69),(31,22),(39,28),(47,27),(36,26),(138,51),(157,53),
         (241,54),(115,52),(157,79),(37,17),(40,16),(59,32),(64,38),(40,30),
         (112,32),(105,37),(111,49),(150,53),(63,41),(49,20),(85,43),(79,32),(140,55))


@pytest.mark.parametrize('index',range(len(rows())))
def test_independently_expanded_contract(index):
    assert exact_ast(rows()[index].statement)==exact_ast(format_contract(*contracts()[index]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body(row):
    try:
        receipt=replay_candidate_bodies((row,),core=body_core())[0]
        assert receipt.name==row.name
        assert receipt.dependency_count==len(row.dependencies)
        assert receipt.command_count==len(row.script)
        assert (receipt.proof_nodes,receipt.proof_depth)==METRICS[rows().index(row)]
        assert 0<receipt.proof_objects<=receipt.proof_nodes
        assert 0<receipt.proof_depth<=receipt.proof_nodes
        print(receipt,flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index',range(len(rows())))
def test_false_conclusion_is_rejected(index):
    names,premises,_=contracts()[index]
    changed=replace(rows()[index],statement=format_contract(names,premises,'0=1'))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((changed,),core=body_core())


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,script=()),),core=body_core())


EDGES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_each_removed_dependency_is_rejected(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((changed,),core=body_core())


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_each_poisoned_dependency_is_rejected(row,dependency):
    table=body_core();table[dependency]=replace(table[dependency],statement='0=0')
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((row,),core=table)


def test_quotient_constructor_rejects_a_duplicate_local_hypothesis_name():
    row=next(row for row in rows() if row.name=='prime_field_polynomial_division_quotient_data_exists')
    changed=replace(row,script=tuple('intro hi' if command=='intro hindex' else command for command in row.script))
    with pytest.raises(CandidateBodyError,match="name 'hi' is already in use"):
        replay_candidate_bodies((changed,),core=body_core())


PUBLIC=(
    (candidate.prime_field_polynomial_quotient_step_relation,step,11),
    (candidate.prime_field_polynomial_quotient_prefix_relation,prefix,10),
    (candidate.prime_field_polynomial_quotient_length_relation,quotient_length,3),
    (candidate.prime_field_polynomial_division_execution_relation,execution,13),
)


@pytest.mark.parametrize('builder,expected,arity',PUBLIC,ids=lambda value:getattr(value,'__name__',str(value)))
def test_public_graphs_match_independent_expansions(builder,expected,arity):
    names=tuple('arg'+str(i) for i in range(arity))
    actual=builder(*names,tag='public',variables=names)
    assert exact_ast('forall '+' '.join(names)+'. '+actual)==exact_ast('forall '+' '.join(names)+'. '+expected(*names))


COMPOUND=tuple((builder,expected,arity,index) for builder,expected,arity in PUBLIC for index in range(arity))


@pytest.mark.parametrize('builder,expected,arity,index',COMPOUND,ids=lambda value:getattr(value,'__name__',str(value)))
def test_every_public_argument_accepts_compound_terms_without_capture(builder,expected,arity,index):
    names=tuple('arg'+str(i) for i in range(arity))
    args=list(names);args[index]='S (arg0*(arg1+1))'
    actual=builder(*args,tag='compound',variables=names)
    assert exact_ast('forall '+' '.join(names)+'. '+actual)==exact_ast('forall '+' '.join(names)+'. '+expected(*args))


@pytest.mark.parametrize('builder,expected,arity',PUBLIC,ids=lambda value:getattr(value,'__name__',str(value)))
@pytest.mark.parametrize('fault',('empty_context','list_context','duplicate_context','invalid_tag','undeclared_term','nonstring_term','capture'))
def test_public_graph_hygiene_rejects_invalid_or_capturing_inputs(builder,expected,arity,fault):
    names=tuple('arg'+str(i) for i in range(arity));args=list(names);tag='hostile';context=names
    if fault=='empty_context':context=()
    elif fault=='list_context':context=list(names)
    elif fault=='duplicate_context':context=(*names,names[0])
    elif fault=='invalid_tag':tag='x. false'
    elif fault=='undeclared_term':args[0]='not_declared'
    elif fault=='nonstring_term':args[0]=1
    elif fault=='capture':
        ordinary=builder(*names,tag=tag,variables=names)
        binders=[name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',ordinary) for name in clause.split()]
        context=(*names,binders[0])
    with pytest.raises(ValueError):builder(*args,tag=tag,variables=context)


def hostile_contracts():
    data=contracts();result=[]
    def remove(index,premise,label):
        names,old,target=data[index]
        result.append((rows()[index],label,format_contract(names,tuple(value for i,value in enumerate(old) if i!=premise),target)))
    remove(0,1,'scalar_cancellation_needs_actual_inverse')
    remove(1,0,'step_recoding_needs_actual_prefix_equality')
    remove(4,1,'execution_entry_needs_index_bound')
    remove(6,1,'append_needs_actual_old_prefix_preservation')
    remove(6,2,'append_needs_actual_new_beta_entry')
    remove(7,0,'construction_needs_prime')
    remove(7,1,'construction_needs_canonical_scalar')
    remove(7,2,'construction_needs_canonical_input')
    remove(8,1,'matching_needs_actual_divisor_head')
    remove(8,2,'matching_needs_actual_inverse')
    remove(8,4,'matching_does_not_constrain_outside_prefix')
    remove(13,0,'empty_trim_still_needs_quotient_within_input')
    remove(13,1,'trim_cut_bound_needs_proved_zero_prefix')
    remove(14,1,'degree_bound_needs_quotient_length_cover')
    remove(14,2,'degree_bound_needs_proved_zero_prefix')
    remove(15,1,'normalized_does_not_imply_small_degree')
    remove(18,2,'general_constructor_needs_nonzero_divisor')
    remove(22,1,'proper_product_length_needs_nonempty_quotient')
    names,premises,_=data[15]
    result.append((rows()[15],'constant_divisor_does_not_give_zero_a_degree',format_contract(
        names,premises,'exists e. '+degree('p','rb','rc','R','e'))))
    names,premises,_=data[14]
    result.append((rows()[14],'remainder_length_can_equal_divisor_degree',format_contract(names,premises,lt('R','d'))))
    return tuple(result)


@pytest.mark.parametrize('row,label,statement',hostile_contracts(),ids=lambda value:value.name if hasattr(value,'name') else value if len(value)<100 else None)
def test_substantively_stronger_or_guardless_claims_are_rejected(row,label,statement):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,statement=statement),),core=body_core())


def encode_beta(values,salt=0):
    """Independent CRT coding, used as arithmetic model data, not a proof."""
    values=tuple(values)
    if not values:return salt,1
    scale=math.factorial(len(values))*(max(values)+1)
    code=0;period=1
    for i,value in enumerate(values):
        modulus=1+(i+1)*scale
        assert value<modulus and math.gcd(period,modulus)==1
        code+=period*((value-code)*pow(period,-1,modulus)%modulus)
        period*=modulus
    return code+salt*period,scale


def beta_value(pair,index):
    return pair[0]%(1+(index+1)*pair[1])


def assert_actual_beta_sum(values):
    entries=encode_beta(values)
    partials=tuple(itertools.accumulate(values,initial=0))
    history=encode_beta(partials)
    assert beta_value(history,0)==0
    for i,value in enumerate(values):
        assert beta_value(entries,i)==value
        assert beta_value(history,i+1)==beta_value(history,i)+beta_value(entries,i)
    assert beta_value(history,len(values))==sum(values)
    return sum(values)


def model_division(p,A,B):
    if p not in (2,3,5,7) or not B or B[0]==0 or any(not 0<=a<p for a in (*A,*B)):
        raise ValueError('the model requires a prime and a genuinely nonzero canonical divisor head')
    A=tuple(A);B=tuple(B);L=len(A);d=len(B)-1;q=max(L-d,0)
    inverse_head=pow(B[0],-1,p)
    Acodes=encode_beta(A);Bcodes=encode_beta(B)
    Q=[];Qcodes=encode_beta(Q)
    for i in range(q):
        old=Qcodes
        terms=[(beta_value(old,j) if j<i else 0)*(beta_value(Bcodes,i-j) if i-j<len(B) else 0)
               for j in range(i+1)]
        previous=assert_actual_beta_sum(terms)%p
        difference=(beta_value(Acodes,i)-previous)%p
        new_value=inverse_head*difference%p
        assert (previous+difference)%p==beta_value(Acodes,i)
        Q.append(new_value);Qcodes=encode_beta(Q,salt=i+1)
        assert all(beta_value(old,j)==beta_value(Qcodes,j) for j in range(i))
        assert beta_value(Qcodes,i)==new_value
        new_terms=[beta_value(Qcodes,j)*(beta_value(Bcodes,i-j) if i-j<len(B) else 0)
                   for j in range(i+1)]
        assert assert_actual_beta_sum(new_terms)==sum(terms)+new_value*B[0]
    proper=[] if not Q else [sum(Q[j]*B[i-j] for j in range(len(Q)) if 0<=i-j<len(B))%p
                            for i in range(len(Q)+len(B)-1)]
    P=proper if Q else [0]*L
    assert len(P)==L
    U=[(A[i]-P[i])%p for i in range(L)]
    cut=next((i for i,value in enumerate(U) if value),L)
    R=U[cut:]
    return tuple(Q),tuple(P),tuple(U),cut,tuple(R)


MODEL_CASES=tuple(dict.fromkeys(
    (p,A,B)
    for p in (2,3,5)
    for A in ((),(0,),(1,),(p-1,),(1,0),(0,1),(1,p-1,1),(0,0,1),(0,0,0,0),(p-1,1,0,p-1))
    for B in ((1,),(p-1,),(1,0),(p-1,1),(1,1,1))
))


@pytest.mark.parametrize('p,A,B',MODEL_CASES)
def test_actual_beta_execution_product_identity_and_degree_models(p,A,B):
    Q,P,U,cut,R=model_division(p,A,B)
    q=len(Q);L=len(A);d=len(B)-1
    assert q==0 and L<=d or q>0 and q+d==L
    assert q<=cut and U[:q]==(0,)*q
    assert L==cut+len(R) and len(R)<=d
    assert not R or R[0]!=0 and len(R)-1<d
    assert tuple((P[i]+((0,)*cut+R)[i])%p for i in range(L))==A
    for values in (A,B,Q,P,U,R):
        first=encode_beta(values);second=encode_beta(values,salt=1)
        assert first!=second
        assert all(beta_value(first,i)==beta_value(second,i)==a for i,a in enumerate(values))
        assert beta_value(first,len(values))!=beta_value(second,len(values))
    ucodes=encode_beta(U);rcodes=encode_beta(R)
    assert all(beta_value(ucodes,i)==0 for i in range(cut))
    assert all(beta_value(ucodes,cut+i)==beta_value(rcodes,i) for i in range(len(R)))


@pytest.mark.parametrize('p,A,B',((2,(1,),(0,)),(3,(1,2),(0,1)),(3,(),()),(6,(1,),(2,)),(2,(2,),(1,))))
def test_models_do_not_silently_remove_domain_or_nonzero_head_guards(p,A,B):
    with pytest.raises(ValueError):model_division(p,A,B)


def test_highest_first_remainder_needs_left_not_right_zero_padding():
    Q,P,U,cut,R=model_division(3,(1,0),(1,1))
    assert (Q,P,U,cut,R)==((1,),(1,1),(0,2),1,(2,))
    assert tuple((a+b)%3 for a,b in zip(P,(0,)*cut+R,strict=True))==(1,0)
    assert tuple((a+b)%3 for a,b in zip(P,R+(0,)*cut,strict=True))!=(1,0)


def test_characteristic_two_uses_natural_one_not_signed_code_two():
    Q,P,U,cut,R=model_division(2,(1,0,1),(1,1))
    assert Q==(1,1) and P==(1,0,1) and not R
    assert 1*1%2==1 and 2%2==0
