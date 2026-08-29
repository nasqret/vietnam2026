"""Exact positive-domain associativity, real-table diagnostics and HA checks."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from random import Random
import re
import sys

import pytest

from peano_lab.library import dirichlet_associativity_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_dirichlet_fubini_candidate import core as grid_core,rows as grid_rows,actual_convolution
from tests.test_dirichlet_convolution_candidate import (
    _conjoin,expected_table,expected_le,expected_convolution,expected_convolution_table,expected_positive_equal,
)
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import BoundedTestSelection
from tests.test_signed_table_operations_candidate import model_table,model_at,decode_signed


EXPECTED=((161,65),(145,60),(80,34))
ROOT_PINS={
    'dirichlet_convolution_associative':'7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738',
    'dirichlet_convolution_tables_associative':'804e50efe285fc4b5536b7ed6200fc5fa8b0d8f83b806da81e1707c5769e9b49',
    'dirichlet_convolution_associative_tables_exists':'f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_associativity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return grid_core()|{row.name:row for row in grid_rows()}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        receipt=replay_candidate_bodies((row,),core=core()|{item.name:item for item in rows()})[0]
        assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED[rows().index(row)]
        assert receipt.proof_objects==receipt.proof_nodes
    except CandidateBodyError as error:pytest.fail(str(error),pytrace=False)
    finally:gc.collect()


def expected_statements():
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='associativity_'+str(counter))
        return call
    T,L,C,CT,PE=tuple(tagged(function) for function in (
        expected_table,expected_le,expected_convolution,expected_convolution_table,expected_positive_equal))
    def all_(names,*clauses):return 'forall '+names+'. '+' -> '.join('('+clause+')' for clause in clauses)
    def frames():return (CT('N','F','G','A'),CT('N','G','H','B'),CT('N','A','H','L'),CT('N','F','B','R'))
    return {
        'dirichlet_convolution_associative':all_('N F G H A B n u v',CT('N','F','G','A'),CT('N','G','H','B'),
            '~(n=0)',L('n','N'),C('A','H','n','u'),C('F','B','n','v'),'u=v'),
        'dirichlet_convolution_tables_associative':all_('N F G H A B L R',*frames(),PE('L','R','N')),
        'dirichlet_convolution_associative_tables_exists':all_('N F G H',T('N','F'),T('N','G'),T('N','H'),
            'exists A B L R. '+_conjoin(*frames(),PE('L','R','N'))),
    }


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_every_endpoint_matches_independent_actual_table_contract(row):
    statements=expected_statements()
    assert tuple(statements)==tuple(item.name for item in rows())
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(statements[row.name]))


def test_exact_topology_and_source_independent_root_pins():
    assert len(rows())==3
    assert sum(len(row.dependencies) for row in rows())==6
    assert sum(len(row.script) for row in rows())==172
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='36942b46f5fa173cb0f4a954586cff8824c14939cc9efc927fa96bb13496e6f9'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    assert {row.name:sha256(row.statement.encode()).hexdigest() for row in rows()}==ROOT_PINS


def test_all_32_statements_are_novel_against_3643_prior_rows_and_each_other():
    from constructive_dirichlet_support import statement_duplicates
    assert statement_duplicates((*grid_rows(),*rows()))==()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_cannot_reuse_the_body(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,script=()),),core=core()|{item.name:item for item in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_cannot_be_used(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((changed,),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_cannot_replace_actual_statement(row,dependency):
    table=core()|{item.name:item for item in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((row,),core=table)


def actual_convolution_table(F,G,N,*,zero,offset):
    values=[zero]
    for n in range(1,N+1):
        z,_=actual_convolution(F,G,n,offset=offset+1)
        values.append(decode_signed(z))
    result=model_table(tuple(values),offset=offset,endpoint=743)
    for n in range(1,N+1):
        z,_=actual_convolution(F,G,n,offset=offset+2)
        assert model_at(result,n)==z
    return result


@pytest.mark.parametrize('N',(0,1,2,4,6))
@pytest.mark.parametrize('seed',(0,17,101))
def test_actual_intermediate_and_output_beta_tables_associate_only_at_positive_indices(N,seed):
    random=Random(seed)
    F,G,H=tuple(model_table(tuple(random.randint(-5,5) for _ in range(N+1)),offset=i+2,endpoint=739+i) for i in range(3))
    A=actual_convolution_table(F,G,N,zero=113,offset=5)
    B=actual_convolution_table(G,H,N,zero=-127,offset=7)
    L=actual_convolution_table(A,H,N,zero=131,offset=11)
    R=actual_convolution_table(F,B,N,zero=-137,offset=13)
    assert L[0]!=R[0] and L[1]!=R[1]
    assert model_at(L,0)!=model_at(R,0)
    for n in range(1,N+1):
        left,_=actual_convolution(A,H,n);right,_=actual_convolution(F,B,n)
        assert left==right==model_at(L,n)==model_at(R,n)
        explicit=sum(decode_signed(model_at(F,a))*decode_signed(model_at(G,c))*decode_signed(model_at(H,e))
            for a in range(1,n+1) for e in range(1,n+1) for c in range(1,n+1) if (a*e)*c==n)
        assert decode_signed(left)==explicit
    if N==0:assert all(model_at(L,n)==model_at(R,n) for n in range(1,N+1))


def test_intermediate_zeroth_entries_are_independent_and_unconsumed():
    N=4
    F=model_table((997,2,-1,3,4),offset=3)
    G=model_table((-991,1,3,-2,5),offset=5)
    H=model_table((983,-2,4,1,-3),offset=7)
    A=actual_convolution_table(F,G,N,zero=11,offset=11)
    A2=actual_convolution_table(F,G,N,zero=-17,offset=13)
    B=actual_convolution_table(G,H,N,zero=23,offset=17)
    B2=actual_convolution_table(G,H,N,zero=-29,offset=19)
    assert len({model_at(code,0) for code in (A,A2,B,B2)})==4
    for n in range(1,N+1):
        assert actual_convolution(A,H,n)[0]==actual_convolution(A2,H,n)[0]
        assert actual_convolution(F,B,n)[0]==actual_convolution(F,B2,n)[0]
        assert actual_convolution(A,H,n)[0]==actual_convolution(F,B,n)[0]


if __name__=='__main__':
    import argparse,resource,signal,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=1);parser.add_argument('--pytest-select');parser.add_argument('--case-start',type=int,default=0);parser.add_argument('--case-count',type=int)
    args=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if args.pytest_select is not None:
        plugins=[] if args.case_count is None else [BoundedTestSelection(args.case_start,args.case_count)]
        status=pytest.main(['-q',__file__,'-k',args.pytest_select],plugins=plugins)
    else:
        selected=tuple(row for row in rows() if row.name==args.body) if args.body else rows()[args.start:args.start+args.count]
        if not selected:raise SystemExit('unknown theorem body')
        for row in selected:
            test_original_kernel_body(row)
            print(json.dumps({'name':row.name,'nodes':EXPECTED[rows().index(row)][0],'depth':EXPECTED[rows().index(row)][1]}),flush=True)
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
