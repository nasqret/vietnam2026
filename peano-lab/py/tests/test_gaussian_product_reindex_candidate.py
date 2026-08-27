"""Original-kernel tests for actual Gaussian finite product replacement."""

from __future__ import annotations

from dataclasses import asdict,replace
from functools import lru_cache
from hashlib import sha256
import json
from math import factorial
import os
from pathlib import Path
import resource
import subprocess
import sys

import pytest

from peano_lab.library import gaussian_product_reindex_candidate as candidate
from peano_lab.library import gaussian_factorization_candidate as factorization
from peano_lab.library import gaussian_factor_search_candidate as search
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.library import gaussian_euclidean_candidate as ge
from test_gaussian_ring_candidate import ROOT,core,rows as ring_rows,assert_family_contract,reference_code,reference_decode,numerical_mul
from test_gaussian_divisibility_candidate import rows as divisibility_rows
from test_gaussian_gcd_candidate import rows as gcd_rows


@lru_cache(maxsize=1)
def rows():
    return candidate.make_gaussian_product_reindex_candidate_theorems(TheoremSpec)


BODY_PROFILES=dict(zip((row.name for row in rows()),((314,61,314),(106,46,106),(145,45,145)),strict=True))


def previous_rows():
    return (*ring_rows(),*divisibility_rows(),*gcd_rows(),*search.make_gaussian_factor_search_candidate_theorems(TheoremSpec),*factorization.make_gaussian_factorization_candidate_theorems(TheoremSpec))


def check_body(name: str,mutation: str='none'):
    table=core()|{row.name:row for row in (*previous_rows(),*rows())}
    row=table[name]
    if mutation=='false_conclusion':
        row=replace(row,statement=f'({row.statement}) /\\ false')
    elif mutation=='truncated_body':
        row=replace(row,script=row.script[:-1])
    elif mutation=='removed_dependency':
        row=replace(row,dependencies=row.dependencies[:-1])
    elif mutation=='corrupt_dependency':
        dep=row.dependencies[0]
        table=table|{dep:replace(table[dep],statement='0=0')}
    elif mutation=='missing_actual_second_product':
        assert row.name=='gaussian_product_replace_balance'
        row=replace(row,statement=expected_balance(include_second_product=False))
    elif mutation=='missing_unchanged_other_entries':
        assert row.name=='gaussian_product_replace_balance'
        row=replace(row,statement=expected_balance(include_preservation=False))
    elif mutation=='swap_product_is_always_identity':
        assert row.name=='gaussian_product_swap_last_invariant'
        row=replace(row,statement=row.statement.removesuffix('P=Q')+'P=6')
    if mutation!='none':
        with pytest.raises(CandidateBodyError):
            replay_candidate_bodies((row,),core=table)
        return {'rejected':True,'mutation':mutation}
    return asdict(replay_candidate_bodies((row,),core=table)[0])


def isolated_body(name: str,mutation: str='none'):
    environment=os.environ.copy()
    environment['PYTHONPATH']=os.pathsep.join((str(ROOT/'peano-lab/py'),str(ROOT/'scripts')))
    result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--body',name,mutation],cwd=ROOT,env=environment,text=True,capture_output=True,timeout=60)
    assert result.returncode==0,result.stdout+result.stderr
    return json.loads(result.stdout)


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
def test_original_kernel_body_in_fresh_process(name):
    receipt=isolated_body(name)
    assert receipt['name']==name
    assert receipt['proof_nodes']>0 and receipt['proof_depth']<=256
    assert (receipt['proof_nodes'],receipt['proof_depth'],receipt['proof_objects'])==BODY_PROFILES[name]


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('false_conclusion','truncated_body'))
def test_negative_proof_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


@pytest.mark.parametrize('name',tuple(row.name for row in rows()))
@pytest.mark.parametrize('mutation',('removed_dependency','corrupt_dependency'))
def test_dependency_mutation_in_fresh_process(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def test_literal_inventory_local_claims_and_dependency_order():
    assert_family_contract(rows(),previous_rows(),(3,22,431,'52a3a25db3d51827c7a85bf37514977d405d1bf1e026d7927e7ef144b18d5ca3'))
    assert not any('cancel' in name for row in rows() for name in row.dependencies)


ROOT_PINS={
    'gaussian_product_replace_balance':'1b5a5e94da214ed6664dd8464acad9a88b1732badc4af8e282daf1800e51350a',
    'gaussian_product_replace_balance_iff':'f9b481d187747f5c3084772a722011398d5f5692e2b7174f8a2d9215505c0f7c',
    'gaussian_product_swap_last_invariant':'fe08f5ab6dc2dfcc72533571cadba5a55dfa4a9a4d320c9f97d4314d47ff480a',
}


@pytest.mark.parametrize('name,digest',ROOT_PINS.items())
def test_actual_product_statement_hashes(name,digest):
    assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def reference_at(b,c,i,a,tag):
    return _beta_at_term(b,c,i,a,tag='independent_'+tag,avoid=())


def reference_product(b,c,l,P,tag):
    return f"exists trace scale. ({reference_at('trace','scale','0','6',tag+'start')}) /\\ " \
           f"(({reference_at('trace','scale',l,P,tag+'end')}) /\\ forall index. (exists gap. gap+S index=({l})) -> exists factor before after. " \
           f"({reference_at(b,c,'index','factor',tag+'factor')}) /\\ (({reference_at('trace','scale','index','before',tag+'before')}) /\\ " \
           f"(({reference_at('trace','scale','S index','after',tag+'after')}) /\\ ({ge._code_mul('before','factor','after',tag+'multiply')}))))"


def reference_preserve_except(b,c,d,e,k,i,tag):
    return f"forall position value. (exists gap. gap+S position=({k})) -> ~(position=({i})) -> ({reference_at(b,c,'position','value',tag+'old')}) -> ({reference_at(d,e,'position','value',tag+'new')})"


def expected_balance(*,include_preservation=True,include_second_product=True,iff=False):
    premises=[
        'exists gap. gap+S i=k',
        reference_at('b','c','i','p','replace_old'),
        reference_at('d','e','i','q','replace_new'),
    ]
    if include_preservation:
        premises.append(reference_preserve_except('b','c','d','e','k','i','replace_others'))
    premises.append(reference_product('b','c','k','P','replace_first_product'))
    if include_second_product:
        premises.append(reference_product('d','e','k','Q','replace_second_product'))
    first=ge._code_mul('Q','p','T','expected_balance_first')
    second=ge._code_mul('P','q','T','expected_balance_second')
    conclusion=f'(({first}) -> ({second}))'
    if iff:
        conclusion+=f' /\\ (({second}) -> ({first}))'
    return 'forall k b c d e i p q P Q T. '+''.join(f'({premise}) -> ' for premise in premises)+conclusion


@pytest.mark.parametrize('name,iff',(('gaussian_product_replace_balance',False),('gaussian_product_replace_balance_iff',True)))
def test_replacement_uses_actual_gaussian_traces_not_natural_code_products(name,iff):
    actual=next(row.statement for row in rows() if row.name==name)
    assert _closed_formula(actual)==_closed_formula(expected_balance(iff=iff))
    if not iff:
        row=next(row for row in rows() if row.name==name)
        assert row.script[0]=='induction k'
        assert 'gaussian_multiply_swap_tail' in row.dependencies
        assert 'gaussian_product_successor_decompose' in row.dependencies


def test_swap_has_the_actual_five_entry_clauses_and_both_real_product_traces():
    clauses=(
        reference_at('b','c','i','p','swap_old_i'),reference_at('b','c','l','q','swap_old_last'),
        reference_at('d','e','i','q','swap_new_i'),reference_at('d','e','l','p','swap_new_last'),
        'forall position value. (exists gap. gap+S position=S l) -> ~(position=i) -> ~(position=l) -> '
        f"({reference_at('b','c','position','value','swap_other_old')}) -> ({reference_at('d','e','position','value','swap_other_new')})",
    )
    swap=f'({clauses[-1]})'
    for clause in reversed(clauses[:-1]):
        swap=f'({clause}) /\\ ({swap})'
    expected=f"forall b c d e l i p q P Q. (exists gap. gap+S i=l) -> ({swap}) -> ({reference_product('b','c','S l','P','swap_first')}) -> ({reference_product('d','e','S l','Q','swap_second')}) -> P=Q"
    row=next(row for row in rows() if row.name=='gaussian_product_swap_last_invariant')
    assert _closed_formula(row.statement)==_closed_formula(expected)
    assert not any(name in row.dependencies for name in ('gaussian_multiply_cancel_left','gaussian_multiply_cancel_right','gaussian_irreducible_is_prime'))


@pytest.mark.parametrize('name,mutation',(
    ('gaussian_product_replace_balance','missing_actual_second_product'),
    ('gaussian_product_replace_balance','missing_unchanged_other_entries'),
    ('gaussian_product_swap_last_invariant','swap_product_is_always_identity'),
))
def test_product_and_preservation_boundary_mutations_are_rejected(name,mutation):
    assert isolated_body(name,mutation)['rejected'] is True


def encode_beta(values):
    if not values:
        return (0,1)
    scale=factorial(len(values))*(max(values)+1)
    code,modulus=0,1
    for index,value in enumerate(values):
        divisor=1+(index+1)*scale
        code+=modulus*((value-code)*pow(modulus,-1,divisor)%divisor)
        modulus*=divisor
    assert all(code%(1+(index+1)*scale)==value for index,value in enumerate(values))
    return code,scale


def numerical_product_trace(factors):
    values=[reference_code((1,0))]
    product=(1,0)
    for factor in factors:
        product=numerical_mul(product,factor)
        values.append(reference_code(product))
    factor_codes=encode_beta([reference_code(factor) for factor in factors])
    trace_codes=encode_beta(values)
    for index,factor in enumerate(factors):
        decoded_factor=reference_decode(factor_codes[0]%(1+(index+1)*factor_codes[1]))
        before=reference_decode(trace_codes[0]%(1+(index+1)*trace_codes[1]))
        after=reference_decode(trace_codes[0]%(1+(index+2)*trace_codes[1]))
        assert decoded_factor==factor
        assert numerical_mul(before,decoded_factor)==after
    assert trace_codes[0]%(1+trace_codes[1])==6
    return factor_codes,trace_codes,product


FACTOR_LISTS=(
    ((1,0),(1,0)),((0,0),(2,1)),((2,1),(0,0),(3,-1)),
    ((1,1),(1,1),(1,-1)),((-1,0),(0,1),(2,3),(0,-1)),
    ((2,0),(3,0),(5,0)),((0,0),(0,0),(1,0),(3,1)),
    ((1,0),(-1,0),(0,1),(0,-1),(1,0)),
)


@pytest.mark.parametrize('factors',FACTOR_LISTS)
def test_actual_beta_trace_replacement_balance_microaudit(factors):
    old_codes,old_trace,old_product=numerical_product_trace(factors)
    for index,old_factor in enumerate(factors):
        for new_factor in ((0,0),(1,0),(-1,0),(1,1),(2,-3)):
            replacement=(*factors[:index],new_factor,*factors[index+1:])
            new_codes,new_trace,new_product=numerical_product_trace(replacement)
            assert all(old_codes[0]%(1+(j+1)*old_codes[1])==new_codes[0]%(1+(j+1)*new_codes[1]) for j in range(len(factors)) if j!=index)
            assert numerical_mul(new_product,old_factor)==numerical_mul(old_product,new_factor)


@pytest.mark.parametrize('factors',FACTOR_LISTS)
def test_actual_beta_trace_last_swap_microaudit_including_zero_units_repetitions(factors):
    old_codes,old_trace,old_product=numerical_product_trace(factors)
    for index in range(len(factors)-1):
        swapped=list(factors)
        swapped[index],swapped[-1]=swapped[-1],swapped[index]
        new_codes,new_trace,new_product=numerical_product_trace(swapped)
        assert new_product==old_product
        assert reference_code(new_product)==reference_code(old_product)
        assert old_codes[0]%(1+(index+1)*old_codes[1])==new_codes[0]%(1+len(factors)*new_codes[1])
        assert old_codes[0]%(1+len(factors)*old_codes[1])==new_codes[0]%(1+(index+1)*new_codes[1])


def test_microaudit_exhibits_missing_preservation_and_false_identity_counterexamples():
    _,_,old=numerical_product_trace(((2,0),(3,0)))
    _,_,bad=numerical_product_trace(((5,0),(7,0)))
    assert numerical_mul(bad,(2,0))!=numerical_mul(old,(5,0))
    assert reference_code(old)!=6
    _,_,empty=numerical_product_trace(())
    assert reference_code(empty)==6


if __name__=='__main__':
    assert sys.argv[1]=='--body'
    resource.setrlimit(resource.RLIMIT_CPU,(45,50))
    print(json.dumps(check_body(sys.argv[2],sys.argv[3] if len(sys.argv)>3 else 'none')))
