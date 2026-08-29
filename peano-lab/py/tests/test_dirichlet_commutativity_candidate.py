"""Exact reindexing contracts and actual signed convolution diagnostics."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import dirichlet_commutativity_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library.prime_valuation_support_candidate import _and
from tests.test_signed_finite_support_candidate import core as inherited,rows as support_rows,expected_zero_window
from tests.test_dirichlet_convolution_candidate import (
    rows as convolution_rows,expected_entry,expected_prefix,expected_convolution,expected_convolution_table,
    expected_at,expected_table,expected_le,expected_signed_sum,
)
from tests.test_divisor_involution_candidate import _expected_complement,_expected_prefix
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import actual_sum_trace,BoundedTestSelection
from tests.test_signed_table_operations_candidate import model_table,model_at,encode_signed,decode_signed,beta_stream


EXPECTED=((239,236,37),(63,63,25),(103,103,38),(68,68,29),(51,51,23),
          (84,84,45),(62,62,37),(86,86,48),(95,95,32),(89,89,30))


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_commutativity_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return inherited()|{r.name:r for r in (*support_rows(),*convolution_rows())}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_objects,report.proof_depth)==EXPECTED[rows().index(row)]
        assert report.proof_depth<=256
    except CandidateBodyError as error:
        pytest.fail(str(error),pytrace=False)
    finally:
        gc.collect()


def test_native_topology_and_used_dependencies():
    available=set(core())
    assert len(rows())==10
    assert sum(len(row.dependencies) for row in rows())==34
    assert sum(len(row.script) for row in rows())==481
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_fails(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dep) for row in rows() for dep in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda x:x.name if hasattr(x,'name') else x)
def test_dropped_dependency_fails(row,dependency):
    altered=replace(row,dependencies=tuple(dep for dep in row.dependencies if dep!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda x:x.name if hasattr(x,'name') else x)
def test_poisoned_dependency_fails(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


@pytest.mark.parametrize('index',range(10))
def test_every_statement_matches_an_independent_exact_graph(index):
    E=lambda F,G,n,d,z:expected_entry(F,G,n,d,z,'independent_entry')
    P=lambda F,G,n,l,M:expected_prefix(F,G,n,l,M,'independent_prefix')
    C=lambda F,G,n,z:expected_convolution(F,G,n,z,'independent_convolution')
    T=lambda N,F,G,H:expected_convolution_table(N,F,G,H,'independent_frame')
    B=lambda a,b:expected_le(a,b,'independent_bound')
    S=lambda F,l,z:expected_signed_sum(F,l,z,'independent_fold')
    A=lambda F,d,z:expected_at(F,d,z,'independent_lookup')
    table=lambda N,F:expected_table(N,F,'independent_table')
    from tests.test_divisor_involution_candidate import _expected_at as beta_at
    reindex=(f"forall i j z. (exists gap. gap+S i=S n) -> ({beta_at('r','s','i','j','independent_reindex')}) -> "
             f"({A('P','j','z')}) -> ({A('Q','i','z')})")
    short,long=C('F','G','n','z'),S('M','S L','z')
    formulas=(
        f"forall F G n d q z. ~(n=0) -> ({_expected_complement('n','d','q')}) -> ({E('F','G','n','q','z')}) -> ({E('G','F','n','d','z')})",
        f"forall F G n l M d z. ({P('F','G','n','l','M')}) -> ({B('d','l')}) -> ({E('F','G','n','d','z')}) -> ({A('M','d','z')})",
        f"forall F G n P Q r s. ~(n=0) -> ({P('F','G','n','n','P')}) -> ({P('G','F','n','n','Q')}) -> ({_expected_prefix('n','r','s','S n')}) -> ({reindex})",
        f"forall F G n a b. ({C('F','G','n','a')}) -> ({C('G','F','n','b')}) -> a=b",
        f"forall N F G n z. ({table('N','F')}) -> ({table('N','G')}) -> ({B('n','N')}) -> ({C('F','G','n','z')}) -> ({C('G','F','n','z')})",
        f"forall N F G H. ({T('N','F','G','H')}) -> ({T('N','G','F','H')})",
        f"forall F G n d z. ~(n=0) -> (exists gap. gap+S n=d) -> ({E('F','G','n','d','z')}) -> z=0",
        f"forall F G n L M. ~(n=0) -> ({P('F','G','n','L','M')}) -> ({expected_zero_window('M','S n','S L','independent_tail')})",
        f"forall F G n L M z. ~(n=0) -> ({B('n','L')}) -> ({P('F','G','n','L','M')}) -> ({long}) -> ({short})",
        f"forall F G n L M z. ~(n=0) -> ({B('n','L')}) -> ({P('F','G','n','L','M')}) -> "+_and(f'({long}) -> ({short})',f'({short}) -> ({long})'),
    )
    _assert_same_ast(_closed_formula(rows()[index].statement),_closed_formula(formulas[index]))


@pytest.mark.parametrize('n',(1,2,3,4,6,8,10))
@pytest.mark.parametrize('padding',(0,3))
def test_actual_beta_complement_maps_reindex_real_signed_products(n,padding):
    left=tuple((-1 if i%2 else 1)*(i+2) for i in range(n+1))
    right=tuple(3-i for i in range(n+1))
    F=model_table(left,offset=7,endpoint=991)
    G=model_table(right,offset=19,endpoint=-997)
    Fother=model_table((123,*left[1:]),offset=29,endpoint=-991)
    Gother=model_table((-313,*right[1:]),offset=31,endpoint=997)
    def summands(A,B):
        return tuple(decode_signed(model_at(A,d))*decode_signed(model_at(B,n//d))
                     if d>0 and n%d==0 else 0 for d in range(n+padding+1))
    values,swapped=summands(F,G),summands(G,F)
    assert values==summands(Fother,Gother)
    P=model_table(values,offset=11,endpoint=997)
    Q=model_table(swapped,offset=23,endpoint=-991)
    permutation=tuple(n//d if d>0 and n%d==0 else d for d in range(n+1))
    b,c=beta_stream(permutation)
    assert sorted(permutation)==list(range(n+1))
    for d in range(n+1):
        q=b%(1+(d+1)*c)
        assert q==permutation[d] and b%(1+(q+1)*c)==d
        assert model_at(P,q)==model_at(Q,d)
    assert actual_sum_trace(P,n+1)==actual_sum_trace(Q,n+1)==encode_signed(sum(values))
    assert all(model_at(P,i)==model_at(Q,i)==0 for i in range(n+1,n+padding+1))
    assert actual_sum_trace(P,n+padding+1)==actual_sum_trace(P,n+1)
    assert model_at(P,n+padding+1)!=model_at(Q,n+padding+1)


def test_last_positive_divisor_and_quotient_one_must_not_be_dropped():
    F=model_table((999,2,3,5,7),offset=7,endpoint=991)
    G=model_table((-997,11,13,17,19),offset=11,endpoint=-991)
    full=tuple(decode_signed(model_at(F,d))*decode_signed(model_at(G,4//d)) if d and 4%d==0 else 0 for d in range(5))
    P=model_table(full,offset=19,endpoint=997)
    assert model_at(P,0)==0 and model_at(P,4)==encode_signed(7*11)
    assert actual_sum_trace(P,4)!=actual_sum_trace(P,5)


if __name__=='__main__':
    import argparse,json,resource,signal,sys,time
    parser=argparse.ArgumentParser();parser.add_argument('--select',default='');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int)
    arguments=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    plugins=[] if arguments.count is None else [BoundedTestSelection(arguments.start,arguments.count)]
    status=pytest.main(['-q',__file__,'-k',arguments.select,'--tb=short'],plugins=plugins)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024**2
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
