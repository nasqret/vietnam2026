"""Constructed finite Möbius tables, with positive-input and zero conventions."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import mobius_table_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.mobius_prime_step_candidate import make_mobius_prime_step_candidate_theorems
from peano_lab.library.mobius_value_candidate import make_mobius_value_candidate_theorems
from peano_lab.library.prime_valuation_support_candidate import _and
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_arithmetic_table_extension_candidate import (
    core as extension_core, rows as extension_rows, _expected_equal,
)
from tests.test_divisor_sum_table_candidate import _assert_same_ast, _expected_entry, _expected_table, _signed_code
from tests.test_divisor_sum_reindex_candidate import _table_code, _lookup
from tests.test_mobius_value_candidate import _expected_mu, _integer_mu


@lru_cache(maxsize=1)
def rows():
    return candidate.make_mobius_table_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    support=(extension_rows()+make_mobius_value_candidate_theorems(TheoremSpec)
             +make_mobius_prime_step_candidate_theorems(TheoremSpec))
    return extension_core() | {row.name:row for row in support}


EXPECTED=((23,17),(209,42),(44,18),(31,18),(56,20),(24,16),(95,26),(79,37))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert checked.name==row.name
        assert (checked.proof_nodes,checked.proof_depth)==EXPECTED[rows().index(row)]
        assert checked.proof_objects==checked.proof_nodes
    finally:
        gc.collect()


def _expected_mu_table(N,M):
    return _and(_expected_table(N,M),_expected_entry(M,'0','0'),
                f'forall i z. ~(i=0) -> (exists h. h+i=({N})) -> '
                f'({_expected_entry(M,"i","z")}) -> ({_expected_mu("i","z")})')


@pytest.mark.parametrize('N,M',[
    ('N','M'),('N+1','M*M'),('0','0'),('12345678901234567890','M+M'),
])
def test_public_mobius_table_has_actual_entries_and_positive_mu_only(N,M):
    source=candidate.mobius_arithmetic_table_relation(N,M,tag='contract',variables=('N','M'))
    _assert_same_ast(_closed_formula('forall N M. '+source),_closed_formula('forall N M. '+_expected_mu_table(N,M)))


def test_all_nested_binders_and_bad_explicit_contexts_are_rejected():
    builder=candidate.mobius_arithmetic_table_relation
    source=builder('N','M',tag='capture',variables=('N','M'))
    binders={name for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in group.split()}
    assert binders
    for binder in binders:
        with pytest.raises(ValueError):
            builder('N','M',tag='capture',variables=('N','M',binder))
    for variables in ((),('N','N'),('N',)):
        with pytest.raises(ValueError):
            builder('N','M',tag='capture',variables=variables)
    for argument in ('missing','N ) -> false','N / M'):
        with pytest.raises(ValueError):
            builder(argument,'M',tag='capture',variables=('N','M'))
    with pytest.raises(ValueError):
        builder('N','M',tag='not a binder',variables=('N','M'))


def test_genuine_existence_and_extensionality_principal_contracts():
    by_name={row.name:row for row in rows()}
    expected='forall N. exists M. ('+_expected_mu_table('N','M')+')'
    _assert_same_ast(_closed_formula(by_name['mobius_table_exists'].statement),_closed_formula(expected))
    expected=('forall N F G. ('+_expected_mu_table('N','F')+') -> ('+_expected_mu_table('N','G')+') -> ('
              +_expected_equal('F','G','S N')+')')
    _assert_same_ast(_closed_formula(by_name['mobius_table_extensional'].statement),_closed_formula(expected))


def _entry_iff(*,positive=True,bounded=True):
    guard='~(i=0) -> ' if positive else ''
    if bounded: guard+='(exists h. h+i=N) -> '
    entry=_expected_entry('M','i','z');value=_expected_mu('i','z')
    return 'forall N M i z. ('+_expected_mu_table('N','M')+') -> '+guard+f'(({entry}) -> ({value})) /\\ (({value}) -> ({entry}))'


@pytest.mark.parametrize('guard',('positive','bounded'))
def test_removing_a_real_entry_domain_guard_is_rejected(guard):
    row=next(row for row in rows() if row.name=='mobius_table_entry_iff')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=_entry_iff(**{guard:False})),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_poisoned_target_cannot_reuse_the_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


def test_ordered_additive_topology_has_no_oracle_or_unused_dependency():
    available=set(core())
    assert len(rows())==8
    for row in rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring','native_decide')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('N',(0,1,2,4,8,12))
def test_actual_beta_encoded_mu_tables_have_correct_signed_codes(N):
    values=(0,)+tuple(_integer_mu(i) for i in range(1,N+1))
    M=_table_code(values,tuple(i+3 for i in range(N+1)))
    assert _lookup(M,0)==0
    assert all(_lookup(M,i)==_integer_mu(i) for i in range(1,N+1))
    if N:
        assert _signed_code(_lookup(M,1))==2
    if N>=2:
        assert _signed_code(_lookup(M,2))==1
    if N>=4:
        assert _signed_code(_lookup(M,4))==0


def test_real_inductive_extension_preserves_the_zero_convention_and_each_value():
    M=_table_code((0,),(7,))
    for N in range(8):
        old=tuple(_lookup(M,i) for i in range(N+1))
        values=old+(_integer_mu(N+1),)
        G=_table_code(values,tuple(N+12+i for i in range(N+2)))
        assert all(_lookup(M,i)==_lookup(G,i) for i in range(N+1))
        assert _lookup(G,0)==0 and _lookup(G,N+1)==_integer_mu(N+1)
        M=G


def test_finite_domain_and_mu_zero_boundaries_really_matter():
    M=_table_code((0,),(0,))
    assert _lookup(M,0)==0
    with pytest.raises(ValueError):
        _integer_mu(0)
    assert _lookup(M,1)==0 and _integer_mu(1)==1


def test_equal_mu_tables_need_not_have_equal_codes_or_component_streams():
    values=(0,1,-1,-1,0,-1,1)
    F=_table_code(values,(0,)*len(values))
    G=_table_code(values,tuple(i+10 for i in range(len(values))))
    assert F!=G and all(_lookup(F,i)==_lookup(G,i) for i in range(len(values)))
    for K in range(len(values)):
        assert all(_lookup(F,i)==_integer_mu(i) for i in range(1,K+1))


if __name__=='__main__':
    import argparse,json,resource,signal,sys,time
    parser=argparse.ArgumentParser(); parser.add_argument('--body'); args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175)); signal.alarm(180); started=time.monotonic()
    selected=tuple(row for row in rows() if args.body is None or row.name==args.body)
    if not selected: raise SystemExit('unknown theorem body')
    for row in selected:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (checked.proof_nodes,checked.proof_depth)==EXPECTED[rows().index(row)]
        print(json.dumps({'name':row.name,'nodes':checked.proof_nodes,'depth':checked.proof_depth,'objects':checked.proof_objects}),flush=True)
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'bodies':len(selected),'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
