"""Exact finite signed-reindex contracts and actual encoded permutation models."""

from dataclasses import replace
from functools import lru_cache
import gc
from math import factorial, isqrt
import re

import pytest

from peano_lab.library import divisor_sum_reindex_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.prime_factorization_permutation_candidate import _bounded,_injective
from peano_lab.library.prime_valuation_support_candidate import _at
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_divisor_sum_algebra_candidate import rows as algebra_rows
from tests.test_divisor_sum_table_candidate import (
    core as parent,rows as table_rows,_assert_same_ast,_expected_entry,_expected_sum,_natpair,_signed_code,
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_sum_reindex_candidate_theorems(TheoremSpec)


def core():
    return parent() | {r.name:r for r in table_rows()+algebra_rows()}


EXPECTED=((57,32),(33,18),(82,40),(68,37),(75,34),(120,48),(136,53))


@pytest.mark.parametrize('row,metrics',tuple(zip(rows(),EXPECTED)),ids=lambda r:r.name if hasattr(r,'name') else str(r))
def test_original_kernel_body(row,metrics):
    try:
        report=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==metrics
        assert report.proof_objects<=report.proof_nodes
    finally:
        gc.collect()


def test_topology_reuses_only_actual_closed_parent_or_earlier_bodies():
    available=set(core())
    assert len(rows())==7
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(line.startswith(('use ','admit','sorry','DNE','ring')) for line in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def _expected_reindex(F,G,r,s,l):
    return (f'forall i j a. (exists h. h+S i=({l})) -> ({_at("("+r+")","("+s+")","i","j","independent_reindex_map")}) -> '
            f'({_expected_entry(F,"j","a")}) -> ({_expected_entry(G,"i","a")})')


@pytest.mark.parametrize('F,G,r,s,l',[
    ('F','G','r','s','l'),('F+F','G*G','r+1','s*s','l+1'),
    ('0','0','0','0','0'),('F','G','1234567890123456789','s','l'),
])
def test_public_reindex_is_exact_actual_lookup_pullback(F,G,r,s,l):
    source=candidate.signed_arithmetic_table_reindex_relation(F,G,r,s,l,tag='contract',variables=('F','G','r','s','l'))
    _assert_same_ast(_closed_formula('forall F G r s l. '+source),_closed_formula('forall F G r s l. '+_expected_reindex(F,G,r,s,l)))


def test_every_nested_capture_rejected_in_explicit_context():
    builder=candidate.signed_arithmetic_table_reindex_relation
    args=('F','G','r','s','l')
    source=builder(*args,tag='capture',variables=args)
    for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source):
        for binder in group.split():
            with pytest.raises(ValueError):
                builder(*args,tag='capture',variables=args+(binder,))
    for variables in ((),args+('F',),args[:-1]):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=variables)


def _root_contract(*,bounded=True,injective=True,source=True,target=True):
    clauses=[]
    if bounded: clauses.append(_bounded('r','s','l','independent_bound'))
    if injective: clauses.append(_injective('r','s','l','independent_inj'))
    clauses.append(_expected_reindex('F','G','r','s','l'))
    if source: clauses.append(_expected_sum('F','l','u'))
    if target: clauses.append(_expected_sum('G','l','v'))
    return 'forall F G r s l u v. '+''.join('('+c+') -> ' for c in clauses)+'u=v'


def test_principal_exact_contract_requires_real_map_and_both_sum_traces():
    row=next(r for r in rows() if r.name=='divisor_signed_sum_permutation_invariant')
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(_root_contract()))


@pytest.mark.parametrize('guard',('bounded','injective','source','target'))
def test_removing_an_actual_principal_premise_is_rejected(guard):
    row=next(r for r in rows() if r.name=='divisor_signed_sum_permutation_invariant')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=_root_contract(**{guard:False})),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_poisoned_body_does_not_check(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


def _encode_beta(values):
    """Actual finite CRT model, not a theorem premise or proof authority."""
    if not values:
        return 0,0
    scale=factorial(len(values))*(max(values)+1)
    code,product=0,1
    for i,value in enumerate(values):
        modulus=1+(i+1)*scale
        code+=((value-code)*pow(product,-1,modulus)%modulus)*product
        product*=modulus
    assert all(code%(1+(i+1)*scale)==value for i,value in enumerate(values))
    return code,scale


def _unpair(code):
    assert code>=0 and code%2==0
    shell=(isqrt(1+4*code)-1)//2
    right=(code-shell*(shell+1))//2
    left=shell-right
    assert left>=0 and right>=0 and _natpair(left,right)==code
    return left,right


def _table_code(values,offsets):
    positive=tuple(max(value,0)+offset for value,offset in zip(values,offsets))
    negative=tuple(max(-value,0)+offset for value,offset in zip(values,offsets))
    pb,pc=_encode_beta(positive); nb,nc=_encode_beta(negative)
    return _natpair(_natpair(pb,pc),_natpair(nb,nc))


def _lookup(F,i):
    pcodes,ncodes=_unpair(F)
    pb,pc=_unpair(pcodes); nb,nc=_unpair(ncodes)
    return pb%(1+(i+1)*pc)-nb%(1+(i+1)*nc)


PERMUTATIONS=((),(0,),(1,0),(2,0,1),(3,1,0,2),(4,3,2,1,0))


@pytest.mark.parametrize('permutation',PERMUTATIONS)
@pytest.mark.parametrize('shift',(-3,0,4))
def test_real_beta_encoded_signed_permutations_with_distinct_representatives(permutation,shift):
    values=tuple(((-1)**i)*(i+shift) for i in range(len(permutation)))
    pulled=tuple(values[j] for j in permutation)
    F=_table_code(values,tuple(i+2 for i in range(len(values))))
    G=_table_code(pulled,tuple(i+11 for i in range(len(values))))
    r,s=_encode_beta(permutation)
    decoded=tuple(r%(1+(i+1)*s) for i in range(len(permutation)))
    assert decoded==permutation
    assert set(decoded)==set(range(len(values)))
    assert all(_lookup(F,j)==_lookup(G,i) for i,j in enumerate(decoded))
    assert tuple(_lookup(F,i) for i in range(len(values)))==values
    assert _signed_code(sum(_lookup(F,i) for i in range(len(values))))==_signed_code(sum(_lookup(G,i) for i in range(len(values))))


def test_noninjective_map_really_changes_a_signed_sum():
    F=_table_code((1,2),(0,0)); G=_table_code((1,1),(8,8))
    r,s=_encode_beta((0,0))
    assert all(_lookup(G,i)==_lookup(F,r%(1+(i+1)*s)) for i in range(2))
    assert sum(_lookup(F,i) for i in range(2))!=sum(_lookup(G,i) for i in range(2))


def test_unbounded_injective_map_really_changes_a_prefix_sum():
    F=_table_code((1,2,7),(0,0,0)); G=_table_code((1,7),(8,8))
    r,s=_encode_beta((0,2))
    assert all(_lookup(G,i)==_lookup(F,r%(1+(i+1)*s)) for i in range(2))
    assert sum(_lookup(F,i) for i in range(2))!=sum(_lookup(G,i) for i in range(2))


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
