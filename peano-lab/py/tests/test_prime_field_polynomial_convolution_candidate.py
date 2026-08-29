"""Independent contracts, actual beta examples and bounded HA convolution tests.

Finite numerical models diagnose mistakes; only the ordinary HA bodies and
the separately assembled complete dependency closure are proof evidence.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import gc
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

import pytest

from peano_lab.library import prime_field_polynomial_convolution_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_field_polynomial_candidate import (
    ROOT, MAX_RSS_BYTES, assert_inventory, capture_cases, compound_cases,
    core as parent_and_arithmetic_core, decode_beta, decoded_prefix, encode_beta,
    expected_and, expected_at, expected_coeff, expected_equal, expected_field_mul,
    expected_lt, expected_prime, expected_repeat, expected_residue, rss_bytes, same_ast,
)


SOURCE_SHA256='20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24'
NAMES_SHA256='42bc93136e5cf710eb616ad0879bb2141c1adfb4c77e6664891c21a95853345e'


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_convolution_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def degree_rows():
    from peano_lab.library.prime_field_polynomial_degree_candidate import make_prime_field_polynomial_degree_candidate_theorems
    return make_prime_field_polynomial_degree_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    # The two frozen research generations authenticate exact source bytes AND
    # ordered theorem specifications. Their statements are only hypotheses
    # here; every actual inherited body is required in the separate closure.
    from constructive_lower_continuation_support import previous_rows
    prior=previous_rows()
    assert len(prior)==296
    table=parent_and_arithmetic_core()|{row.name:row for row in prior}
    assert len(table)==3518
    return table


def fresh(*arguments):
    environment=os.environ.copy()
    environment['PYTHONPATH']=os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts')))
    environment['PYTHONMALLOC']='malloc'
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),*arguments],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=185)
    assert result.returncode==0,result.stdout+result.stderr
    report=json.loads(result.stdout)
    assert report['peak_rss_bytes']<=MAX_RSS_BYTES
    assert report['cpu_limits']==[170,175] and report['wall_alarm_seconds']==180
    return report


def _body_batch(family,mutation):
    selected=rows() if family=='convolution' else degree_rows()
    table=core()|{r.name:r for r in (*rows(),*degree_rows())}
    receipts=[]
    for original in selected:
        gc.collect()
        row,current=original,table
        if mutation=='false_conclusion':
            row=replace(row,statement=f'({row.statement}) /\\ false')
        elif mutation=='truncated_body':
            row=replace(row,script=row.script[:-1])
        elif mutation=='removed_dependency':
            if not row.dependencies:
                continue
            row=replace(row,dependencies=row.dependencies[:-1])
        elif mutation=='forged_dependency':
            if not row.dependencies:
                continue
            name=row.dependencies[0]
            current=table|{name:replace(table[name],statement='0=0')}
        elif mutation!='none':
            raise ValueError('unknown convolution mutation')
        if mutation=='none':
            receipts.append(asdict(replay_candidate_bodies((row,),core=current)[0]))
        else:
            with pytest.raises(CandidateBodyError):
                replay_candidate_bodies((row,),core=current)
            receipts.append({'name':original.name,'rejected':mutation})
    return {'receipts':receipts}


@pytest.mark.parametrize('mutation',('none','false_conclusion','truncated_body','removed_dependency','forged_dependency'))
def test_every_convolution_body_and_actual_corruption_is_checked_in_fresh_bounded_processes(mutation):
    report=fresh('--bodies','convolution',mutation)
    expected=[r.name for r in rows() if mutation not in ('removed_dependency','forged_dependency') or r.dependencies]
    assert [r['name'] for r in report['receipts']]==expected
    if mutation=='none':
        assert sum(r['proof_nodes'] for r in report['receipts'])==3717
        assert sum(r['proof_objects'] for r in report['receipts'])==3713
        assert max(r['proof_nodes'] for r in report['receipts'])==264
        assert max(r['proof_depth'] for r in report['receipts'])==95
        assert all(r['proof_depth']<=256 and r['proof_objects']<=r['proof_nodes'] for r in report['receipts'])
    else:
        assert all(r['rejected']==mutation for r in report['receipts'])


def test_exact_convolution_inventory_and_acyclic_actual_dependencies():
    assert len(rows())==45
    assert sum(len(r.dependencies) for r in rows())==101
    assert sum(len(r.script) for r in rows())==2098
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest()==NAMES_SHA256
    assert_inventory(rows(),core())
    dependencies={d for row in rows() for d in row.dependencies}
    assert {'beta_prefix_extend','beta_sum_exists','beta_sum_functional','beta_sum_transport_prefix','beta_sum_succ_decompose','hensel_canonical_residue_exists','binary_canonical_residue_functional'}<=dependencies
    assert not any('division' in row.name or 'horner_product' in row.name for row in rows())


def test_no_new_statement_duplicates_any_of_3518_earlier_statements_or_its_peers():
    result=fresh('--duplicates')
    assert result['new_count']==53 and result['duplicates']==[]


def expected_le(a,b):
    return f'exists ind_le_gap. ind_le_gap+({a})=({b})'


def expected_sum(b,c,length,n):
    u,v,i,a,h,j=('ind_sum_code','ind_sum_scale','ind_sum_index','ind_summand','ind_partial','ind_next')
    step=f'exists {a} {h} {j}. '+expected_and(expected_at(b,c,i,a),expected_at(u,v,i,h),expected_at(u,v,f'S ({i})',j),f'{j}={h}+{a}')
    steps=f'forall {i}. ({expected_lt(i,length)}) -> ({step})'
    return f'exists {u} {v}. '+expected_and(expected_at(u,v,'0','0'),expected_at(u,v,length,n),steps)


def expected_pad(b,c,length,i,a):
    inside=expected_and(expected_lt(i,length),expected_at(b,c,i,a))
    outside=expected_and(expected_le(length,i),f'({a})=0')
    return f'({inside}) \\/ ({outside})'


def expected_term(ab,ac,L,bb,bc,M,i,j,t):
    k,a,b='ind_complement','ind_factor_left','ind_factor_right'
    return f'exists {k} {a} {b}. '+expected_and(f'({j})+{k}=({i})',expected_pad(ab,ac,L,j,a),expected_pad(bb,bc,M,k,b),f'({t})={a}*{b}')


def expected_diagonal(ab,ac,L,bb,bc,M,i,db,dc,length):
    j,t='ind_diag_index','ind_diag_value'
    return f'forall {j}. ({expected_lt(j,length)}) -> exists {t}. '+expected_and(expected_at(db,dc,j,t),expected_term(ab,ac,L,bb,bc,M,i,j,t))


def expected_coefficient(p,ab,ac,L,bb,bc,M,i,r):
    db,dc,n='ind_terms_code','ind_terms_scale','ind_natural_sum'
    return f'exists {db} {dc} {n}. '+expected_and(expected_diagonal(ab,ac,L,bb,bc,M,i,db,dc,f'S ({i})'),expected_sum(db,dc,f'S ({i})',n),expected_residue(p,n,r))


def expected_prefix(p,ab,ac,L,bb,bc,M,cb,cc,length):
    i,r='ind_coefficient_index','ind_coefficient_value'
    return f'forall {i}. ({expected_lt(i,length)}) -> exists {r}. '+expected_and(expected_at(cb,cc,i,r),expected_coefficient(p,ab,ac,L,bb,bc,M,i,r))


def expected_length(L,M,N):
    empty=expected_and(f'({L})=0 \\/ ({M})=0',f'({N})=0')
    positive=expected_and(f'~(({L})=0)',f'~(({M})=0)',f'({L})+({M})=S ({N})')
    return f'({empty}) \\/ ({positive})'


def expected_convolution(p,ab,ac,L,bb,bc,M,cb,cc,N):
    return expected_and(expected_coeff(p,ab,ac,L),expected_coeff(p,bb,bc,M),expected_length(L,M,N),expected_prefix(p,ab,ac,L,bb,bc,M,cb,cc,N))


PUBLIC_CASES=(
    (candidate.prime_field_polynomial_zero_extended_entry_relation,('b','c','L','i','a'),expected_pad),
    (candidate.prime_field_polynomial_diagonal_term_relation,('ab','ac','L','bb','bc','M','i','j','t'),expected_term),
    (candidate.prime_field_polynomial_diagonal_prefix_relation,('ab','ac','L','bb','bc','M','i','db','dc','N'),expected_diagonal),
    (candidate.prime_field_polynomial_convolution_coefficient_relation,('p','ab','ac','L','bb','bc','M','i','r'),expected_coefficient),
    (candidate.prime_field_polynomial_convolution_prefix_relation,('p','ab','ac','L','bb','bc','M','cb','cc','N'),expected_prefix),
    (candidate.prime_field_polynomial_product_length_relation,('L','M','N'),expected_length),
    (candidate.prime_field_polynomial_convolution_relation,('p','ab','ac','L','bb','bc','M','cb','cc','N'),expected_convolution),
)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES,ids=lambda v:v.__name__ if callable(v) else None)
def test_all_convolution_graphs_are_exact_independently_assembled_ha(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC_CASES))
def test_every_convolution_argument_preserves_compound_and_96bit_numeral_terms(builder,args,expected,index,term):
    values=(*args[:index],term,*args[index+1:])
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_generated_convolution_binder_rejects_unused_and_used_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(f'{args[0]}+{binder}',*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_convolution_context_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='invalid',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('undeclared','p -> p','p = 0','p; true','',None,7,False))
def test_invalid_convolution_term_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='invalid',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_convolution_tag_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


PARAMS=('p','ab','ac','L','bb','bc','M')
BASE=(*PARAMS,'cb','cc','N')
PRINCIPAL_CONTRACTS={
    'polynomial_zero_extended_entry_exists':f"forall b c L i. exists a. ({expected_pad('b','c','L','i','a')})",
    'polynomial_zero_extended_entry_functional':f"forall b c L i a d. ({expected_pad('b','c','L','i','a')}) -> ({expected_pad('b','c','L','i','d')}) -> a=d",
    'polynomial_diagonal_term_exists':f"forall ab ac L bb bc M i j. ({expected_lt('j','S i')}) -> exists t. ({expected_term('ab','ac','L','bb','bc','M','i','j','t')})",
    'polynomial_diagonal_term_past_support':f"forall ab ac L bb bc M i j t. ({expected_le('L+M','S i')}) -> ({expected_term('ab','ac','L','bb','bc','M','i','j','t')}) -> t=0",
    'polynomial_diagonal_prefix_exists':f"forall ab ac L bb bc M I. exists db dc. ({expected_diagonal('ab','ac','L','bb','bc','M','I','db','dc','S I')})",
    'prime_field_convolution_coefficient_exists':f"forall {' '.join(PARAMS)} i. ~(p=0) -> exists r. ({expected_coefficient(*PARAMS,'i','r')})",
    'prime_field_convolution_coefficient_functional':f"forall {' '.join(PARAMS)} i r s. ({expected_coefficient(*PARAMS,'i','r')}) -> ({expected_coefficient(*PARAMS,'i','s')}) -> r=s",
    'prime_field_convolution_prefix_exists':f"forall {' '.join(PARAMS)} N. ~(p=0) -> exists cb cc. ({expected_prefix(*PARAMS,'cb','cc','N')})",
    'polynomial_product_length_exists':f"forall L M. exists N. ({expected_length('L','M','N')})",
    'polynomial_product_length_functional':f"forall L M N K. ({expected_length('L','M','N')}) -> ({expected_length('L','M','K')}) -> N=K",
    'prime_field_polynomial_convolution_entry':f"forall {' '.join(BASE)} i r. ({expected_convolution(*BASE)}) -> ({expected_lt('i','N')}) -> ({expected_at('cb','cc','i','r')}) -> ({expected_coefficient(*PARAMS,'i','r')})",
    'prime_field_polynomial_convolution_functional':f"forall {' '.join(BASE)} db dc K. ({expected_convolution(*BASE)}) -> ({expected_convolution(*PARAMS,'db','dc','K')}) -> {expected_and('N=K',expected_equal('cb','cc','db','dc','N'))}",
    'prime_field_polynomial_convolution_at_length_exists':f"forall {' '.join(PARAMS)} N. ~(p=0) -> ({expected_coeff('p','ab','ac','L')}) -> ({expected_coeff('p','bb','bc','M')}) -> ({expected_length('L','M','N')}) -> exists cb cc. ({expected_convolution(*BASE)})",
    'prime_field_polynomial_convolution_exists_unique':f"forall {' '.join(PARAMS)}. ~(p=0) -> ({expected_coeff('p','ab','ac','L')}) -> ({expected_coeff('p','bb','bc','M')}) -> exists N cb cc. {expected_and(expected_convolution(*BASE),'forall db dc K. ('+expected_convolution(*PARAMS,'db','dc','K')+') -> ('+expected_and('N=K',expected_equal('cb','cc','db','dc','N'))+')')}",
    'prime_field_polynomial_convolution_empty':f"forall {' '.join(PARAMS)} cb cc. ({expected_coeff('p','ab','ac','L')}) -> ({expected_coeff('p','bb','bc','M')}) -> (L=0 \\/ M=0) -> ({expected_convolution(*PARAMS,'cb','cc','0')})",
    'prime_field_polynomial_convolution_zero_left':f"forall {' '.join(BASE)}. ~(p=0) -> ({expected_repeat('ab','ac','0','L')}) -> ({expected_convolution(*BASE)}) -> ({expected_repeat('cb','cc','0','N')})",
    'prime_field_polynomial_convolution_zero_right':f"forall {' '.join(BASE)}. ~(p=0) -> ({expected_repeat('bb','bc','0','M')}) -> ({expected_convolution(*BASE)}) -> ({expected_repeat('cb','cc','0','N')})",
    'prime_field_polynomial_convolution_outside_zero':f"forall {' '.join(BASE)} i r. ~(p=0) -> ({expected_convolution(*BASE)}) -> ({expected_le('N','i')}) -> ({expected_coefficient(*PARAMS,'i','r')}) -> r=0",
}


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_CONTRACTS.items()),ids=tuple(PRINCIPAL_CONTRACTS))
def test_principal_convolution_endpoints_have_the_exact_independent_contract(name,expected):
    row=next(r for r in rows() if r.name==name)
    same_ast(_closed_formula(row.statement),_closed_formula(expected))


GUARD_CASES={
    'zero_modulus':('prime_field_convolution_coefficient_exists',f"forall {' '.join(PARAMS)} i. 0=0 -> exists r. ({expected_coefficient(*PARAMS,'i','r')})"),
    'wrong_product_length':('prime_field_polynomial_convolution_at_length_exists',f"forall {' '.join(PARAMS)} N. ~(p=0) -> ({expected_coeff('p','ab','ac','L')}) -> ({expected_coeff('p','bb','bc','M')}) -> 0=0 -> exists cb cc. ({expected_convolution(*BASE)})"),
    'uncanonical_left_input':('prime_field_polynomial_convolution_at_length_exists',f"forall {' '.join(PARAMS)} N. ~(p=0) -> 0=0 -> ({expected_coeff('p','bb','bc','M')}) -> ({expected_length('L','M','N')}) -> exists cb cc. ({expected_convolution(*BASE)})"),
    'raw_code_uniqueness':('prime_field_polynomial_convolution_functional',f"forall {' '.join(BASE)} db dc K. ({expected_convolution(*BASE)}) -> ({expected_convolution(*PARAMS,'db','dc','K')}) -> {expected_and('N=K','cb=db','cc=dc')}"),
    'outside_off_by_one':('prime_field_polynomial_convolution_outside_zero',f"forall {' '.join(BASE)} i r. ~(p=0) -> ({expected_convolution(*BASE)}) -> ({expected_le('N','S i')}) -> ({expected_coefficient(*PARAMS,'i','r')}) -> r=0"),
    'raw_tail_is_not_a_polynomial_coefficient':('prime_field_polynomial_convolution_outside_zero',f"forall {' '.join(BASE)} i r. ~(p=0) -> ({expected_convolution(*BASE)}) -> ({expected_le('N','i')}) -> ({expected_at('cb','cc','i','r')}) -> r=0"),
    'support_off_by_one':('polynomial_diagonal_term_past_support',f"forall ab ac L bb bc M i j t. ({expected_le('L+M','S (S i)')}) -> ({expected_term('ab','ac','L','bb','bc','M','i','j','t')}) -> t=0"),
}


@pytest.mark.parametrize('mutation',tuple(GUARD_CASES))
def test_actual_convolution_proofs_reject_wrong_domains_lengths_and_raw_code_claims(mutation):
    assert fresh('--guard','convolution',mutation)['rejected']==mutation


def padded_value(code,length,i):
    return decode_beta(code,i) if i<length else 0


def diagonal_values(left,L,right,M,i):
    return tuple(padded_value(left,L,j)*padded_value(right,M,i-j) for j in range(i+1))


def product_length(L,M):
    return 0 if L==0 or M==0 else L+M-1


def canonical_convolution(p,left,right):
    if not left or not right:
        return ()
    return tuple(sum(left[j]*right[i-j] for j in range(len(left)) if 0<=i-j<len(right))%p for i in range(len(left)+len(right)-1))


def model_convolution(p,left,L,right,M,result,N):
    if N!=product_length(L,M):
        return False
    if any(not 0<=decode_beta(left,i)<p for i in range(L)) or any(not 0<=decode_beta(right,i)<p for i in range(M)):
        return False
    return all(0<=decode_beta(result,i)<p and decode_beta(result,i)==sum(diagonal_values(left,L,right,M,i))%p for i in range(N))


def sum_trace(values):
    total=0
    trace=[0]
    for value in values:
        total+=value
        trace.append(total)
    return tuple(trace)


@pytest.mark.parametrize('p',(2,3,5,7,11))
@pytest.mark.parametrize('inputs',(((),()),((),(1,)),((1,),()),((0,),(0,)),((1,),(1,)),((1,1),(1,1)),((2,3),(4,5)),((0,1,2),(2,0,1)),((0,0,0),(1,2,3,4))))
def test_actual_antidiagonal_product_codes_sum_traces_reduction_and_recoding(p,inputs):
    a,b=(tuple(x%p for x in values) for values in inputs)
    left,right=encode_beta(a),encode_beta(b)
    A,B=encode_beta(a,2),encode_beta(b,3)
    values=canonical_convolution(p,a,b)
    result,other=encode_beta(values),encode_beta(values,5)
    N=product_length(len(a),len(b))
    assert result!=other and model_convolution(p,left,len(a),right,len(b),result,N)
    assert model_convolution(p,A,len(a),B,len(b),other,N)
    for i in range(N+3):
        terms=diagonal_values(left,len(a),right,len(b),i)
        term_code=encode_beta(terms)
        partial=sum_trace(terms)
        trace=encode_beta(partial)
        assert decoded_prefix(term_code,i+1)==terms
        assert decode_beta(trace,0)==0 and decode_beta(trace,i+1)==sum(terms)
        for j,t in enumerate(terms):
            k=i-j
            assert j+k==i and t==padded_value(left,len(a),j)*padded_value(right,len(b),k)
            assert decode_beta(trace,j+1)==decode_beta(trace,j)+decode_beta(term_code,j)
        if i<N:
            assert decode_beta(result,i)==sum(terms)%p
        else:
            assert sum(terms)==0  # genuine support, not arbitrary raw output tail


def test_highest_degree_first_convolution_is_not_pointwise_multiplication():
    assert canonical_convolution(7,(2,3),(4,5))==(1,1,1)
    assert canonical_convolution(2,(1,1),(1,1))==(1,0,1)
    assert canonical_convolution(2,(1,1),(1,1))!=(1,1)
    assert product_length(0,4)==product_length(3,0)==product_length(0,0)==0
    assert product_length(1,1)==1 and product_length(2,2)==3


def test_padding_and_raw_output_tail_are_deliberately_different_relations():
    left=encode_beta((1,1))
    right=encode_beta((1,))
    arbitrary_tail=encode_beta((1,1))
    assert model_convolution(2,left,1,right,1,arbitrary_tail,1)
    assert decode_beta(arbitrary_tail,1)==1
    assert sum(diagonal_values(left,1,right,1,1))==0
    assert padded_value(left,1,1)==0 and decode_beta(left,1)==1


def test_raw_natural_coefficient_construction_does_not_imply_uncanonical_polynomial_input():
    raw=(2**96+17,2**80+3)
    a,b=encode_beta(raw),encode_beta((5,9))
    coefficients=tuple(sum(diagonal_values(a,2,b,2,i))%7 for i in range(3))
    assert all(0<=r<7 for r in coefficients)
    assert not model_convolution(7,a,2,b,2,encode_beta(coefficients),3)
    # The empty relation is meaningful without a field, but nonempty canonical
    # coefficient existence cannot be extended to modulus zero.
    assert model_convolution(0,a,0,b,0,encode_beta((123,)),0)
    assert not model_convolution(0,encode_beta((0,)),1,b,0,encode_beta(()),0)


if __name__=='__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started=time.monotonic()
    if sys.argv[1:2]==['--bodies']:
        report=_body_batch(sys.argv[2],sys.argv[3])
    elif sys.argv[1:2]==['--guard']:
        family,mutation=sys.argv[2:4]
        if family=='degree':
            from test_prime_field_polynomial_degree_candidate import GUARD_CASES as guards
        else:
            guards=GUARD_CASES
        name,statement=guards[mutation]
        table=core()|{r.name:r for r in (*rows(),*degree_rows())}
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((replace(table[name],statement=statement),),core=table)
        report={'name':name,'rejected':mutation}
    elif sys.argv[1:]==['--duplicates']:
        from constructive_lower_continuation_support import statement_duplicates
        new=(*rows(),*degree_rows())
        report={'new_count':len(new),'duplicates':statement_duplicates(new)}
    else:
        raise SystemExit('expected --bodies FAMILY MUTATION, --guard FAMILY MUTATION, or --duplicates')
    report.update(cpu_limits=list(resource.getrlimit(resource.RLIMIT_CPU)),wall_alarm_seconds=180,peak_rss_bytes=rss_bytes(),seconds=time.monotonic()-started)
    assert report['peak_rss_bytes']<=MAX_RSS_BYTES
    print(json.dumps(report,sort_keys=True),flush=True)
