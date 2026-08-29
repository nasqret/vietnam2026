"""Original-kernel signed prefix-sum linearity, not a numerical oracle."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import re

import pytest

from peano_lab.library import signed_sum_linearity_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_signed_table_operations_candidate import core as parent,rows as table_rows


EXPECTED=((61,27),(69,31),(69,31),(175,42),(133,36),(59,28),(43,23))
ROOT_PINS={
    'signed_prefix_sum_pointwise_add':'8cdea91bcb14f0f475b838413f29a8c4e1df9ded8ac198d8c97fbf09d8088464',
    'signed_prefix_sum_scalar_multiply':'37350038ed9cf4a84bf46ecc195ab93684a0e11246c87d9e366b8e75622791c3',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_sum_linearity_candidate_theorems(TheoremSpec)


def core():
    return parent()|{r.name:r for r in table_rows()}


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_original_kernel_body(row):
    try:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        assert report.proof_objects<=report.proof_nodes
        assert report.proof_depth<=256
    finally:
        gc.collect()


def test_additive_native_topology_and_used_dependencies():
    available=set(core())
    assert len(rows())==7
    assert sum(len(r.dependencies) for r in rows())==28
    assert sum(len(r.script) for r in rows())==442
    assert sha256('\n'.join(r.name for r in rows()).encode()).hexdigest()=='583114af42a8f207c511a4865e3b9c783f74a813488790c43aff437ea9dfaf07'
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)
    assert {r.name:sha256(r.statement.encode()).hexdigest() for r in rows() if r.name in ROOT_PINS}==ROOT_PINS


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_false_target_fails_original_kernel(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda v:v.name if hasattr(v,'name') else v)
def test_dropped_dependency_cannot_be_used(row,dependency):
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda v:v.name if hasattr(v,'name') else v)
def test_poisoned_dependency_cannot_replace_a_real_lemma(row,dependency):
    table=core()|{r.name:r for r in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def test_principal_statements_keep_actual_pointwise_and_sum_hypotheses():
    # Independently state both contracts using the independently expanded
    # table graphs rather than reading their target from the candidate.
    from tests.test_signed_table_operations_candidate import expected_binary,expected_scalar,expected_signed_operation
    from tests.test_divisor_sum_table_candidate import _expected_sum,_assert_same_ast
    add='forall l F G H a b c. '+f'({expected_binary("F","G","H","l",multiply=False)}) -> ({_expected_sum("F","l","a")}) -> ({_expected_sum("G","l","b")}) -> ({_expected_sum("H","l","c")}) -> ({expected_signed_operation("a","b","c",multiply=False)})'
    scale='forall l a F G b c. '+f'({expected_scalar("a","F","G","l")}) -> ({_expected_sum("F","l","b")}) -> ({_expected_sum("G","l","c")}) -> ({expected_signed_operation("a","b","c",multiply=True)})'
    by_name={r.name:r for r in rows()}
    _assert_same_ast(_closed_formula(add),_closed_formula(by_name['signed_prefix_sum_pointwise_add'].statement))
    _assert_same_ast(_closed_formula(scale),_closed_formula(by_name['signed_prefix_sum_scalar_multiply'].statement))


if __name__=='__main__':
    import argparse,json,resource,signal,sys,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=3);parser.add_argument('--pytest-select')
    arguments=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if arguments.pytest_select is not None:
        status=pytest.main(['-q',__file__,'-k',arguments.pytest_select])
        peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
        assert peak<=1536*1024*1024
        print(json.dumps({'pytest_status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
        raise SystemExit(status)
    selected=tuple(r for r in rows() if r.name==arguments.body) if arguments.body else rows()[arguments.start:arguments.start+arguments.count]
    if not selected:raise SystemExit('unknown theorem body')
    for row in selected:
        report=replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'depth':report.proof_depth,'objects':report.proof_objects}),flush=True)
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'bodies':len(selected),'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
