"""Actual finite signed-table contracts, independent models and HA body checks."""

from dataclasses import fields, is_dataclass, replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import divisor_sum_table_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_sum_theorems import _sum_relation_terms
from peano_lab.library.gaussian_euclidean_candidate import _balance
from peano_lab.library.prime_valuation_support_candidate import _and, _at
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_mobius_value_candidate import core


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_sum_table_candidate_theorems(TheoremSpec)


EXPECTED=((26,23),(147,38),(39,25),(36,22),(24,16),(49,28),(81,28),
          (28,19),(26,23),(147,38),(43,28),(81,28),(47,19),(31,17))


@pytest.mark.parametrize('row,metrics',tuple(zip(rows(),EXPECTED)),ids=lambda value:value.name if hasattr(value,'name') else str(value))
def test_original_kernel_body(row,metrics):
    try:
        report=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==metrics
        assert report.proof_objects<=report.proof_nodes
    finally:
        gc.collect()


def test_additive_native_topology():
    available=set(core())
    assert len(rows())==14
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)


def _pair(a,b):
    return f'(({a})+({b}))*S(({a})+({b}))+(({b})+({b}))'


def _pack(a,b,c,d):
    return _pair(_pair(a,b),_pair(c,d))


def _expected_entry(F,i,z):
    return 'exists pb pc nb nc p n. '+_and(
        f'({F})=({_pack("pb","pc","nb","nc")})',_at('pb','pc',i,'p','independent_pos'),
        _at('nb','nc',i,'n','independent_neg'),_balance(z,'p','n','independent_value'))


def _expected_sum(F,l,z):
    return 'exists pb pc nb nc p n. '+_and(
        f'({F})=({_pack("pb","pc","nb","nc")})',
        _sum_relation_terms('pb','pc',l,'p',tag='independent_positive_sum'),
        _sum_relation_terms('nb','nc',l,'n',tag='independent_negative_sum'),
        _balance(z,'p','n','independent_sum_value'))


def _expected_table(N,F):
    entry=_and(_at('pb','pc','i','p','independent_table_pos'),_at('nb','nc','i','n','independent_table_neg'),_balance('z','p','n','independent_table_z'))
    return 'exists pb pc nb nc. '+_and(f'({F})=({_pack("pb","pc","nb","nc")})',f'forall i. (exists h. h+i=({N})) -> exists p n z. ({entry})')


def _assert_same_ast(left,right):
    # Independent structural equality without Python's recursive dataclass
    # __eq__; large shared double-and-add numeral DAGs need no recursion-cap
    # change merely to compare the public notation with its exact expansion.
    pending=[(left,right)]
    seen=set()
    while pending:
        a,b=pending.pop()
        if a is b or (id(a),id(b)) in seen:
            continue
        assert type(a) is type(b)
        seen.add((id(a),id(b)))
        if is_dataclass(a):
            pending.extend((getattr(a,f.name),getattr(b,f.name)) for f in fields(a))
        else:
            assert type(a) in (int,str,type(None))
            assert a==b


@pytest.mark.parametrize('N,F,i,z',[('N','F','i','z'),('N+1','F+F','i*i','z+1'),('0','0','0','0'),('999999999999999999','F','i','z')])
def test_independent_exact_table_entry_and_sum_ast(N,F,i,z):
    ctx=('N','F','i','z')
    for builder,args,expected in (
        (candidate.signed_arithmetic_table_relation,(N,F),_expected_table(N,F)),
        (candidate.signed_arithmetic_table_entry_relation,(F,i,z),_expected_entry(F,i,z)),
        (candidate.signed_arithmetic_prefix_sum_relation,(F,i,z),_expected_sum(F,i,z)),
    ):
        source=builder(*args,tag='contract',variables=ctx)
        _assert_same_ast(_closed_formula('forall N F i z. '+source),_closed_formula('forall N F i z. '+expected))


SURFACES=(
    (candidate.signed_arithmetic_table_representation_relation,('F','pb','pc','nb','nc')),
    (candidate.signed_arithmetic_table_relation,('N','F')),
    (candidate.signed_arithmetic_table_entry_relation,('F','i','z')),
    (candidate.signed_arithmetic_prefix_sum_relation,('F','l','z')),
    (candidate.signed_arithmetic_table_equality_relation,('F','G','l')),
)


@pytest.mark.parametrize('builder,args',SURFACES)
def test_full_context_nested_binder_capture_and_malformed_terms(builder,args):
    ctx=tuple(dict.fromkeys(args))
    source=builder(*args,tag='capture',variables=ctx)
    _closed_formula('forall '+' '.join(ctx)+'. '+source)
    for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source):
        for binder in group.split():
            with pytest.raises(ValueError):
                builder(*args,tag='capture',variables=ctx+(binder,))
    for variables in ((),ctx+(ctx[0],),ctx[:-1]):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=variables)
    with pytest.raises(ValueError):
        builder('missing',*args[1:],tag='capture',variables=ctx)


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_false_target_cannot_reuse_a_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


def _natpair(a,b):
    return (a+b)*(a+b+1)+2*b


def _signed_code(n):
    return 2*n if n>=0 else -2*n-1


@pytest.mark.parametrize('positive,negative',[((),()),((0,),(0,)),((1,),(0,)),((0,),(1,)),((4,7,0),(3,9,0)),((100,2),(98,4))])
def test_component_model_sum_including_empty_and_negative(positive,negative):
    values=tuple(p-n for p,n in zip(positive,negative))
    assert _signed_code(sum(values))==_signed_code(sum(positive)-sum(negative))
    if not positive:
        assert _signed_code(sum(values))==0


def test_signed_representation_independence_does_not_equate_components():
    p,n,q,m=(1,0,19,18)
    assert p+m==q+n
    assert (p,n)!=(q,m)
    assert _signed_code(p-n)==_signed_code(q-m)==2
    assert _natpair(p,n)!=_natpair(q,m)


def test_existing_four_code_injectivity_is_reused_not_enrolled_as_alias():
    assert 'divisor_signed_table_pack_unique' not in {row.name for row in rows()}
    for name in ('divisor_signed_table_at_to_components','divisor_signed_sum_to_components'):
        row=next(r for r in rows() if r.name==name)
        assert row.dependencies==('matrix_minor_four_code_components_injective',)


@pytest.mark.parametrize('a,b,c,d',[(0,0,0,0),(1,2,3,4),(4,3,2,1),(1000,0,0,1000)])
def test_actual_nested_pair_constructor_is_not_opaque(a,b,c,d):
    F=_natpair(_natpair(a,b),_natpair(c,d))
    assert F>=0 and F%2==0
    assert _natpair(a,b)<=F and _natpair(c,d)<=F


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
