"""Ordinary proof and exact signed-algebra tests for the finite-table substrate."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import divisor_sum_algebra_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.ha_signed_add_candidate import signed_add
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_divisor_sum_table_candidate import core as parent,rows as table_rows


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_sum_algebra_candidate_theorems(TheoremSpec)


def core():
    return parent() | {r.name:r for r in table_rows()}


EXPECTED=((45,27),(49,21),(37,17),(93,28),(135,49),(111,46),(62,32),(103,34),(127,39))


@pytest.mark.parametrize('row,metrics',tuple(zip(rows(),EXPECTED)),ids=lambda v:v.name if hasattr(v,'name') else str(v))
def test_original_kernel_body(row,metrics):
    try:
        report=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==metrics
        assert report.proof_objects<=report.proof_nodes
    finally:
        gc.collect()


def test_native_topological_inventory():
    available=set(core())
    assert len(rows())==9
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(c.startswith(('use ','admit','sorry','DNE','ring')) for c in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def test_internal_addition_is_exactly_old_canonical_graph():
    assert _closed_formula('forall a b c. '+candidate._add_code('a','b','c','actual'))==_closed_formula('forall a b c. '+signed_add('a','b','c',tag='old'))


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_false_target_fails_original_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('a,b',[(a,b) for a in range(-4,5) for b in range(-4,5)])
def test_independent_signed_prefix_and_negation_model(a,b):
    p,n=max(a,0),max(-a,0)
    q,m=max(b,0)+9,max(-b,0)+9
    assert (p+q)-(n+m)==a+b
    assert n-p==-a
    assert ((a==-a)==(a==0))


if __name__=='__main__':
    import argparse,json,resource,signal,sys,time
    parser=argparse.ArgumentParser(); parser.add_argument('--body'); arguments=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175)); signal.alarm(180); started=time.monotonic()
    selected=tuple(r for r in rows() if arguments.body is None or r.name==arguments.body)
    if not selected: raise SystemExit('unknown theorem body')
    for row in selected:
        report=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[rows().index(row)]
        print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'depth':report.proof_depth,'objects':report.proof_objects}),flush=True)
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'bodies':len(selected),'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
