"""Exact actual weighted-sum graph and ordinary HA proof checks."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import re

import pytest

from peano_lab.library import signed_weighted_sum_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_signed_sum_linearity_candidate import core as parent,rows as linearity_rows


EXPECTED=((31,14),(80,45),(31,20),(26,16),(30,14),(195,52),(82,28),(141,43),(121,68),(97,55))
ROOT_PINS={
    'signed_weighted_sum_exists_unique':'1ed794504914ee8304903be9fce6c08e5e310c7b0e75c244382438433c4c3f14',
    'signed_weighted_sum_add_linearity':'0515fa77e429a50f266b273b77efa2682ec7cc78c3e30948559d6a5c3363f255',
    'signed_weighted_sum_scalar_linearity':'488852252ab9e41daf5e2e6e234f8a9e046042f269dd9f5fd1bd9a074c45cbeb',
}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_signed_weighted_sum_candidate_theorems(TheoremSpec)


def core():
    return parent()|{r.name:r for r in linearity_rows()}


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
    assert len(rows())==10
    assert sum(len(r.dependencies) for r in rows())==25
    assert sum(len(r.script) for r in rows())==525
    assert sha256('\n'.join(r.name for r in rows()).encode()).hexdigest()=='71ddda43a654845c0637ecb0ab16bc5ea4307921b289a0ab987015f4a0b0cb83'
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


def expected_weighted(W,F,l,z):
    from tests.test_signed_table_operations_candidate import expected_binary
    from tests.test_divisor_sum_table_candidate import _expected_sum
    return f'exists model_product. ({expected_binary(W,F,"model_product",l,multiply=True)}) /\\ ({_expected_sum("model_product",l,z)})'


@pytest.mark.parametrize('arguments',(('W','F','l','z'),('W+1','F*F','l+2','S z'),('0','0','0','0'),('9999999999999999999999999999999999999999','F','l','z')))
def test_independent_exact_weighted_graph(arguments):
    from tests.test_divisor_sum_table_candidate import _assert_same_ast
    actual=candidate.signed_weighted_sum_relation(*arguments,tag='contract',variables=('W','F','l','z'))
    _assert_same_ast(_closed_formula('forall W F l z. '+actual),_closed_formula('forall W F l z. '+expected_weighted(*arguments)))


def test_every_generated_binder_and_whole_context_is_hygienic():
    context=('W','F','l','z')
    source=candidate.signed_weighted_sum_relation(*context,tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for name in binders:
        with pytest.raises(ValueError):
            candidate.signed_weighted_sum_relation(*context,tag='capture',variables=context+(name,))
    for bad in ((),context[:-1],context+('W',)):
        with pytest.raises(ValueError):
            candidate.signed_weighted_sum_relation(*context,tag='capture',variables=bad)
    for argument in ('missing','W -> F','exists x. x=0'):
        with pytest.raises(ValueError):
            candidate.signed_weighted_sum_relation(argument,'F','l','z',tag='capture',variables=context)


def test_independent_weighted_linearity_and_totality_statements():
    from tests.test_signed_table_operations_candidate import expected_binary,expected_scalar,expected_signed_operation
    from tests.test_divisor_sum_table_candidate import _expected_table,_assert_same_ast
    by_name={r.name:r for r in rows()}
    add=f'forall l W F G H a b c. ({expected_binary("F","G","H","l",multiply=False)}) -> ({expected_weighted("W","F","l","a")}) -> ({expected_weighted("W","G","l","b")}) -> ({expected_weighted("W","H","l","c")}) -> ({expected_signed_operation("a","b","c",multiply=False)})'
    scale=f'forall l a W F G b c. ({expected_scalar("a","F","G","l")}) -> ({expected_weighted("W","F","l","b")}) -> ({expected_weighted("W","G","l","c")}) -> ({expected_signed_operation("a","b","c",multiply=True)})'
    total=f'forall l W F. ({_expected_table("l","W")}) -> ({_expected_table("l","F")}) -> exists z. ({expected_weighted("W","F","l","z")})'
    unique=f'forall l W F. ({_expected_table("l","W")}) -> ({_expected_table("l","F")}) -> exists z. ({expected_weighted("W","F","l","z")}) /\\ (forall u. ({expected_weighted("W","F","l","u")}) -> u=z)'
    for name,formula in (('signed_weighted_sum_add_linearity',add),('signed_weighted_sum_scalar_linearity',scale),('signed_weighted_sum_exists',total),('signed_weighted_sum_exists_unique',unique)):
        _assert_same_ast(_closed_formula(formula),_closed_formula(by_name[name].statement))


@pytest.mark.parametrize('weights,values,other',(((),(),()),((0,),(7,),(-3,)),((2,-3),(4,5),(-1,6)),((-1,0,3),(7,-2,-4),(2,9,1))))
@pytest.mark.parametrize('scalar',(-4,-1,0,1,5))
def test_actual_beta_weighted_sum_models_include_empty_negative_and_zero(weights,values,other,scalar):
    from tests.test_signed_table_operations_candidate import model_table,model_at,model_sum,decode_signed,encode_signed
    W=model_table(weights,offset=7,endpoint=991)
    F=model_table(values,offset=3,endpoint=-999)
    products=tuple(w*v for w,v in zip(weights,values,strict=True))
    H=model_table(products,offset=13,endpoint=101)
    alternate=model_table(products,offset=19,endpoint=-103)
    assert H[0]!=alternate[0]
    for i in range(len(weights)):
        assert decode_signed(model_at(H,i))==decode_signed(model_at(W,i))*decode_signed(model_at(F,i))
        assert model_at(H,i)==model_at(alternate,i)
    assert model_sum(H,len(weights))==model_sum(alternate,len(weights))==encode_signed(sum(products))
    assert sum(w*(v+g) for w,v,g in zip(weights,values,other,strict=True))==sum(products)+sum(w*g for w,g in zip(weights,other,strict=True))
    assert sum(w*(scalar*v) for w,v in zip(weights,values,strict=True))==scalar*sum(products)


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
