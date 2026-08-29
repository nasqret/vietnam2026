"""Actual HA bodies, independent contracts and finite zero-window boundaries."""

from dataclasses import replace
from functools import lru_cache
import gc
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

from constructive_dirichlet_support import closure,previous_rows
from peano_lab.library import signed_finite_support_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from peano_lab.library.prime_valuation_support_candidate import _and
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_signed_rectangular_slice_candidate import (
    expected_table,expected_entry,expected_sum,actual_sum_trace,BoundedTestSelection,
)
from tests.test_signed_table_operations_candidate import model_table,model_at,encode_signed


EXPECTED=((22,16),(43,27),(43,28),(177,39),(44,25),(32,15),(77,26),(90,25))


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_finite_support_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    inherited=(*closure.parent_snapshot().specs,*previous_rows())
    assert len(inherited)==len({row.name for row in inherited})==3643
    return {row.name:row for row in inherited}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        assert report.proof_objects<=report.proof_nodes and report.proof_depth<=256
    except CandidateBodyError as error:
        pytest.fail(str(error),pytrace=False)
    finally:
        gc.collect()


def test_native_topology_and_exact_dependency_surface():
    available=set(core())
    assert len(rows())==8
    assert sum(len(row.dependencies) for row in rows())==25
    assert sum(len(row.script) for row in rows())==312
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_fails_original_kernel(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dep) for row in rows() for dep in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda x:x.name if hasattr(x,'name') else x)
def test_dropped_dependency_fails(row,dependency):
    changed=replace(row,dependencies=tuple(dep for dep in row.dependencies if dep!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda x:x.name if hasattr(x,'name') else x)
def test_poisoned_dependency_fails(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def expected_zero_window(F,k,l,tag):
    i,z='model_zero_index_'+tag,'model_zero_value_'+tag
    return (f'forall {i} {z}. (exists model_lower_{tag}. model_lower_{tag}+({k})={i}) -> '
            f'(exists model_upper_{tag}. model_upper_{tag}+S {i}=({l})) -> '
            f'({expected_entry(F,i,z,tag+"entry")}) -> {z}=0')


@pytest.mark.parametrize('arguments',(('F','k','l'),('F+1','k*k','l+1'),('0','0','0'),('F','F','F'),
    ('9999999999999999999999999999999999999999','k','l')))
def test_independent_zero_window_graph(arguments):
    actual=candidate.signed_arithmetic_zero_window_relation(*arguments,tag='contract',variables=('F','k','l'))
    _assert_same_ast(_closed_formula('forall F k l. '+actual),
                     _closed_formula('forall F k l. '+expected_zero_window(*arguments,'independent')))


def test_every_generated_binder_is_rejected_in_the_whole_context():
    builder=candidate.signed_arithmetic_zero_window_relation
    source=builder('F','k','l',tag='capture',variables=('F','k','l'))
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(('F','k','l'))
    for name in binders:
        with pytest.raises(ValueError):builder('F','k','l',tag='capture',variables=('F','k','l',name))


@pytest.mark.parametrize('malformed',('unknown','syntax','empty-context','duplicate-context','missing-context','reserved-tag'))
def test_bad_terms_and_contexts_fail(malformed):
    arguments=('F','k','l');context=arguments;tag='bad'
    if malformed=='unknown':arguments=('missing','k','l')
    if malformed=='syntax':arguments=('F -> k','k','l')
    if malformed=='empty-context':context=()
    if malformed=='duplicate-context':context+=('F',)
    if malformed=='missing-context':context=context[1:]
    if malformed=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):
        candidate.signed_arithmetic_zero_window_relation(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('index',range(8))
def test_every_statement_has_an_independent_exact_ast(index):
    Z=lambda F,k,l:expected_zero_window(F,k,l,'independent_window')
    S=lambda F,l,z:expected_sum(F,l,z,'independent_sum')
    T=lambda N,F:expected_table(N,F,'independent_table')
    A=lambda F,i,z:expected_entry(F,i,z,'independent_entry')
    le=lambda a,b:f'exists independent_gap. independent_gap+({a})=({b})'
    formulas=(
        'forall F k. '+Z('F','k','k'),
        f"forall F k l L. ({le('l','L')}) -> ({Z('F','k','L')}) -> ({Z('F','k','l')})",
        f"forall F k K l. ({le('k','K')}) -> ({Z('F','k','l')}) -> ({Z('F','K','l')})",
        f"forall F k l a b. ({le('k','l')}) -> ({Z('F','k','l')}) -> ({S('F','k','a')}) -> ({S('F','l','b')}) -> a=b",
        f"forall F l z. ({Z('F','0','l')}) -> ({S('F','l','z')}) -> z=0",
        f"forall F l. ({T('0','F')}) -> ({Z('F','0','l')}) -> ({S('F','l','0')})",
        f"forall F l a z. ({Z('F','0','l')}) -> ({A('F','l','a')}) -> ({S('F','S l','z')}) -> z=a",
        f"forall F k l z. ({T('0','F')}) -> ({le('k','l')}) -> ({Z('F','k','l')}) -> "+
            _and(f"({S('F','k','z')}) -> ({S('F','l','z')})",f"({S('F','l','z')}) -> ({S('F','k','z')})"),
    )
    _assert_same_ast(_closed_formula(rows()[index].statement),_closed_formula(formulas[index]))


@pytest.mark.parametrize('prefix,tail',(((),0),((),3),((3,),0),((3,),2),((-3,2),0),((-3,2),3),((0,0),4),((5,-7,4),2)))
@pytest.mark.parametrize('offset',(0,17))
def test_actual_beta_traces_ignore_zero_tail_but_not_the_unused_endpoint(prefix,tail,offset):
    values=(*prefix,*([0]*tail))
    first=model_table(values,offset=offset,endpoint=997)
    other=model_table(values,offset=offset+13,endpoint=-991)
    k,l=len(prefix),len(values)
    assert first[0]!=other[0] and first[1]!=other[1]
    assert all(model_at(first,i)==model_at(other,i)==0 for i in range(k,l))
    assert actual_sum_trace(first,k)==actual_sum_trace(first,l)==actual_sum_trace(other,l)==encode_signed(sum(prefix))
    assert model_at(first,l)!=model_at(other,l)


@pytest.mark.parametrize('last',(-5,0,7))
@pytest.mark.parametrize('length',(0,1,3))
def test_actual_last_entry_after_a_zero_prefix(last,length):
    table=model_table((*([0]*length),last),offset=11,endpoint=991)
    assert actual_sum_trace(table,length+1)==model_at(table,length)==encode_signed(last)


def test_order_and_zero_tail_guards_cannot_be_erased():
    # Empty reversed windows do not imply equal folds; neither does a tail
    # with a nonzero actual last entry. These are semantic boundary checks,
    # not substitutes for the original-HA theorem checks above.
    table=model_table((3,5,-1),offset=7,endpoint=997)
    assert all(model_at(table,i)==0 for i in range(2,1))
    assert actual_sum_trace(table,2)!=actual_sum_trace(table,1)
    assert model_at(table,1)!=0
    assert actual_sum_trace(table,1)!=actual_sum_trace(table,2)


if __name__=='__main__':
    import argparse,json,resource,signal,time
    parser=argparse.ArgumentParser();parser.add_argument('--select',default='');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int)
    arguments=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    plugins=[] if arguments.count is None else [BoundedTestSelection(arguments.start,arguments.count)]
    status=pytest.main(['-q',__file__,'-k',arguments.select,'--tb=short'],plugins=plugins)
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024**2
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
