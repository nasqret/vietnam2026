"""Actual signed-prefix extension bodies and independent finite-table models."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import arithmetic_table_extension_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.prime_valuation_support_candidate import _and
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_reindex_candidate import (
    core as frozen_core, rows as reindex_rows, _table_code, _lookup,
)
from tests.test_divisor_sum_table_candidate import (
    _assert_same_ast, _expected_entry, _expected_table, _signed_code,
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_arithmetic_table_extension_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return frozen_core() | {row.name:row for row in reindex_rows()}


EXPECTED=((82,42),(46,23),(105,41),(24,15),(26,13),(27,18),(61,30))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert checked.name==row.name
        assert (checked.proof_nodes,checked.proof_depth)==EXPECTED[rows().index(row)]
        assert checked.proof_objects==checked.proof_nodes
    finally:
        gc.collect()


def _expected_equal(F,G,l):
    return (f'forall i a b. (exists h. h+S i=({l})) -> '
            f'({_expected_entry(F,"i","a")}) -> ({_expected_entry(G,"i","b")}) -> a=b')


def _expected_extension(F,G,l,z,*,preserved=None,table=True,last=True):
    clauses=[]
    if table: clauses.append(_expected_table(l,G))
    clauses.append(_expected_equal(F,G,l if preserved is None else preserved))
    if last: clauses.append(_expected_entry(G,l,z))
    return _and(*clauses)


@pytest.mark.parametrize('F,G,l,z',[
    ('F','G','l','z'),('F+F','G*G','l+1','z*z'),('0','0','0','0'),
    ('F','G','12345678901234567890','z+1'),
])
def test_public_extension_is_exact_packing_prefix_and_last_lookup(F,G,l,z):
    source=candidate.signed_arithmetic_table_extension_relation(F,G,l,z,tag='contract',variables=('F','G','l','z'))
    _assert_same_ast(_closed_formula('forall F G l z. '+source),
                     _closed_formula('forall F G l z. '+_expected_extension(F,G,l,z)))


def test_full_context_hygiene_rejects_every_generated_binder():
    builder=candidate.signed_arithmetic_table_extension_relation
    args=('F','G','l','z')
    source=builder(*args,tag='capture',variables=args)
    binders={binder for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for binder in group.split()}
    assert binders
    for binder in binders:
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=args+(binder,))
    for variables in ((),args+('F',),args[:-1]):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=variables)
    for term in ('missing','F ) -> false','F / G'):
        with pytest.raises(ValueError):
            builder(term,*args[1:],tag='capture',variables=args)


def test_exact_extend_root_has_arbitrary_l_without_an_l_equals_N_hypothesis():
    row=next(row for row in rows() if row.name=='arithmetic_signed_table_extend_at')
    expected='forall N F l z. ('+_expected_table('N','F')+') -> exists G. ('+_expected_extension('F','G','l','z')+')'
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_additive_topology_has_no_unused_dependencies_or_unproved_primitive():
    available=set(core())
    assert len(rows())==7
    for row in rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring','native_decide')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_does_not_reuse_an_accepted_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('change',('preserve_changed_index','remove_input_packing','remove_actual_last_entry'))
def test_unmatched_extension_contract_does_not_accept_the_original_body(change):
    row=next(row for row in rows() if row.name=='arithmetic_signed_table_extend_at')
    premise='' if change=='remove_input_packing' else '('+_expected_table('N','F')+') -> '
    result=_expected_extension('F','G','l','z',preserved='S l' if change=='preserve_changed_index' else None,
                               last=change!='remove_actual_last_entry')
    statement='forall N F l z. '+premise+'exists G. ('+result+')'
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('l',(0,1,3,4,6))
@pytest.mark.parametrize('value',(-7,0,9))
def test_real_beta_recoding_preserves_exactly_earlier_values_for_arbitrary_l(l,value):
    original=(17,-2,0,5)
    F=_table_code(original,(2,4,6,8))
    earlier=tuple(_lookup(F,i) for i in range(l))
    values=earlier+(value,)
    G=_table_code(values,tuple(11+i for i in range(l+1)))
    assert tuple(_lookup(G,i) for i in range(l))==earlier
    assert _lookup(G,l)==value
    assert _signed_code(sum(_lookup(G,i) for i in range(l+1)))==_signed_code(sum(earlier)+value)
    if l:
        assert _lookup(F,0)==17 and _lookup(G,0)==17
    else:
        assert _lookup(G,0)==value


def test_preserving_the_replaced_index_would_be_a_false_stronger_claim():
    F=_table_code((41,),(3,))
    G=_table_code((-5,),(10,))
    assert _lookup(F,0)!=_lookup(G,0)
    assert _lookup(F,0)==41
    assert _lookup(G,0)==-5


def test_equal_signed_prefixes_do_not_imply_equal_packed_codes_or_components():
    values=(3,-4,0)
    F=_table_code(values,(0,0,0))
    G=_table_code(values,(11,12,13))
    assert F!=G
    assert all(_lookup(F,i)==_lookup(G,i) for i in range(3))


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
