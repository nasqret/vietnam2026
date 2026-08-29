"""Independent positive-divisor masks, genuine finite folds and HA body checks."""

from dataclasses import replace
from functools import lru_cache
import gc
from itertools import accumulate
import re

import pytest

from peano_lab.library import divisor_mask_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_sum_theorems import _sum_relation_terms
from peano_lab.library.gaussian_euclidean_candidate import _balance
from peano_lab.library.prime_valuation_support_candidate import _and
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_arithmetic_table_extension_candidate import core as extension_core, rows as extension_rows
from tests.test_divisor_sum_table_candidate import _assert_same_ast, _expected_entry, _expected_table, _pack, _signed_code
from tests.test_divisor_sum_reindex_candidate import _table_code, _lookup, _unpair, _encode_beta


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_mask_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return extension_core() | {row.name:row for row in extension_rows()}


EXPECTED=((7,6),(15,13),(9,8),(81,26),(137,39),(47,19),(45,21),(49,23),
          (175,39),(70,27),(47,23),(68,33),(84,28),(55,20),(139,41),(57,27),
          (33,16),(95,52),(33,20),(14,9),(118,36),(99,55))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert checked.name==row.name
        assert (checked.proof_nodes,checked.proof_depth)==EXPECTED[rows().index(row)]
        assert checked.proof_objects==checked.proof_nodes
    finally:
        gc.collect()


def _expected_mask_entry(F,n,d,z,*,positive=True):
    keep='exists q. '+_and(f'({n})=({d})*q',_expected_entry(F,d,z))
    if positive: keep=_and(f'~(({d})=0)',keep)
    omit=_and(f'({d})=0 \\/ ~(exists t. ({n})=({d})*t)',f'({z})=0')
    return f'({keep}) \\/ ({omit})'


def _expected_mask(F,n,l,M):
    return _and(_expected_table(l,M),
                f'forall d z. (exists h. h+d=({l})) -> ({_expected_entry(M,"d","z")}) -> '
                f'({_expected_mask_entry(F,n,"d","z")})')


def _expected_positive_equal(F,G,N):
    return (f'forall d a b. ~(d=0) -> (exists h. h+d=({N})) -> '
            f'({_expected_entry(F,"d","a")}) -> ({_expected_entry(G,"d","b")}) -> a=b')


def _expected_signed_fold(F,length,z):
    # The older independent fixture named its negative accumulator `n`.
    # Here length contains the free divisor target n, so use distinct bound
    # names throughout rather than silently capturing that input in the test.
    pb,pc,nb,nc,p,n=('ind_dm_'+role for role in ('pb','pc','nb','nc','positive','negative'))
    return f'exists {pb} {pc} {nb} {nc} {p} {n}. '+_and(
        f'({F})=({_pack(pb,pc,nb,nc)})',
        _sum_relation_terms(pb,pc,length,p,tag='independent_divisor_positive_fold'),
        _sum_relation_terms(nb,nc,length,n,tag='independent_divisor_negative_fold'),
        _balance(z,p,n,'independent_divisor_fold_balance'))


def _expected_divisor_sum(F,n,z,*,positive=True,length=None):
    length=f'S ({n})' if length is None else length
    fold='exists M. '+_and(_expected_mask(F,n,n,'M'),_expected_signed_fold('M',length,z))
    return _and(f'~(({n})=0)',fold) if positive else fold


SURFACES=(
    (candidate.divisor_mask_entry_relation,('F','n','d','z'),_expected_mask_entry),
    (candidate.divisor_mask_prefix_relation,('F','n','l','M'),_expected_mask),
    (candidate.positive_arithmetic_table_equality_relation,('F','G','N'),_expected_positive_equal),
    (candidate.signed_divisor_sum_relation,('F','n','z'),_expected_divisor_sum),
)


@pytest.mark.parametrize('builder,args,expected',SURFACES)
@pytest.mark.parametrize('variant',('variables','compound','constants','large_numeral'))
def test_exact_public_graphs_have_real_quotients_entries_and_S_n_fold(builder,args,expected,variant):
    context=tuple(dict.fromkeys(args))
    terms=tuple(name if variant=='variables' else f'{name}+{name}' if variant=='compound' else
                '0' if variant=='constants' else '12345678901234567890' if index==1 else name
                for index,name in enumerate(args))
    source=builder(*terms,tag='contract',variables=context)
    prefix='forall '+' '.join(context)+'. '
    _assert_same_ast(_closed_formula(prefix+source),_closed_formula(prefix+expected(*terms)))


@pytest.mark.parametrize('builder,args,expected',SURFACES)
def test_every_nested_binder_is_hygienic_in_the_explicit_context(builder,args,expected):
    context=tuple(dict.fromkeys(args))
    source=builder(*args,tag='capture',variables=context)
    binders={name for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in group.split()}
    assert binders
    for binder in binders:
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=context+(binder,))
    for variables in ((),context+(context[0],),context[:-1]):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=variables)
    for term in ('missing',args[0]+' ) -> false',args[0]+' / 2'):
        with pytest.raises(ValueError):
            builder(term,*args[1:],tag='capture',variables=context)
    with pytest.raises(ValueError):
        builder(*args,tag='bad tag',variables=context)


def _unique_root(*,input_table=True,positive=True,bounded=True,length=None):
    clauses=[]
    if input_table: clauses.append(_expected_table('N','F'))
    if positive: clauses.append('~(n=0)')
    if bounded: clauses.append('exists h. h+n=N')
    return ('forall N F n. '+''.join('('+clause+') -> ' for clause in clauses)+'exists z. ('
            +_expected_divisor_sum('F','n','z',length=length)+') /\\ forall w. ('
            +_expected_divisor_sum('F','n','w',length=length)+') -> w=z')


def test_exact_unique_sum_and_positive_source_extensionality_contracts():
    by_name={row.name:row for row in rows()}
    _assert_same_ast(_closed_formula(by_name['signed_divisor_sum_exists_unique'].statement),_closed_formula(_unique_root()))
    expected=('forall F G n a b. ('+_expected_positive_equal('F','G','n')+') -> ('
              +_expected_divisor_sum('F','n','a')+') -> ('+_expected_divisor_sum('G','n','b')+') -> a=b')
    _assert_same_ast(_closed_formula(by_name['signed_divisor_sum_positive_source_extensional'].statement),_closed_formula(expected))


def test_induction_and_literal_fold_are_not_cancellation_oracles():
    names={row.name:row for row in rows()}
    assert 'induction l' in names['divisor_mask_prefix_exists'].script
    assert 'divisor_mask_entry_exists' in names['divisor_mask_prefix_exists'].dependencies
    assert 'divisor_mask_prefix_append' in names['divisor_mask_prefix_exists'].dependencies
    assert 'multiple_decidable_nonzero' in names['divisor_mask_entry_exists'].dependencies
    assert 'arithmetic_signed_table_append' in names['divisor_mask_prefix_append'].dependencies
    assert 'arithmetic_signed_sum_exists' in names['signed_divisor_sum_exists'].dependencies
    assert not any('mobius' in dependency or 'inversion' in dependency for row in rows() for dependency in row.dependencies)


def test_additive_order_and_exact_dependency_use():
    available=set(core())
    assert len(rows())==22
    for row in rows():
        assert row.name not in available and set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring','native_decide')) for command in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_goal_cannot_reuse_any_accepted_body(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('change',('input_table','positive','bounded','wrong_fold_length'))
def test_changed_unique_sum_contract_is_rejected(change):
    row=next(row for row in rows() if row.name=='signed_divisor_sum_exists_unique')
    statement=_unique_root(length='n') if change=='wrong_fold_length' else _unique_root(**{change:False})
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core() | {r.name:r for r in rows()})


def test_dropping_the_positive_divisor_branch_guard_breaks_the_checked_contract():
    row=next(row for row in rows() if row.name=='divisor_mask_entry_functional')
    statement=('forall F n d a b. ('+_expected_mask_entry('F','n','d','a',positive=False)+') -> ('
               +_expected_mask_entry('F','n','d','b',positive=False)+') -> a=b')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('name',('divisor_mask_prefix_exists','signed_divisor_sum_exists_unique',
                                'signed_divisor_sum_one','signed_divisor_sum_positive_source_extensional'))
def test_missing_declared_dependency_is_not_silently_supplied_by_the_library(name):
    row=next(row for row in rows() if row.name==name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,dependencies=row.dependencies[:-1]),),core=core() | {r.name:r for r in rows()})


def _masked_values(F,n,l):
    return tuple(0 if d==0 or n%d else _lookup(F,d) for d in range(l+1))


def _actual_component_traces(M,length):
    positive,negative=_unpair(M)
    pb,pc=_unpair(positive);nb,nc=_unpair(negative)
    result=[]
    for b,c in ((pb,pc),(nb,nc)):
        values=tuple(b%(1+(i+1)*c) for i in range(length))
        trace=(0,)+tuple(accumulate(values))
        tb,tc=_encode_beta(trace)
        at=lambda i:tb%(1+(i+1)*tc)
        assert at(0)==0 and at(length)==sum(values)
        assert all(at(i+1)==at(i)+values[i] for i in range(length))
        result.append(at(length))
    return tuple(result)


@pytest.mark.parametrize('n',(1,2,3,4,6,8,12))
@pytest.mark.parametrize('zero_value',(-137,0,241))
def test_actual_beta_mask_and_two_real_fold_traces_compute_positive_divisor_sum(n,zero_value):
    values=(zero_value,)+tuple(((-1)**i)*(i+2) for i in range(1,n+1))
    F=_table_code(values,tuple(i+3 for i in range(n+1)))
    masked=_masked_values(F,n,n)
    M=_table_code(masked,tuple(12+i for i in range(n+1)))
    assert _lookup(F,0)==zero_value and _lookup(M,0)==0
    for d in range(1,n+1):
        if n%d==0:
            q=n//d
            assert q>0 and n==d*q and _lookup(M,d)==_lookup(F,d)
        else:
            assert _lookup(M,d)==0
    p,q=_actual_component_traces(M,n+1)
    expected=sum(values[d] for d in range(1,n+1) if n%d==0)
    assert p-q==sum(_lookup(M,i) for i in range(n+1))==expected
    assert _signed_code(p-q)==_signed_code(expected)


@pytest.mark.parametrize('n,l',((0,0),(0,3),(1,0),(1,4),(6,2),(6,7)))
def test_mask_prefix_bound_is_independent_of_its_fixed_divisibility_target(n,l):
    values=(77,)+tuple(i-4 for i in range(1,l+1))
    F=_table_code(values,tuple(3+i for i in range(l+1)))
    M=_table_code(_masked_values(F,n,l),tuple(10+i for i in range(l+1)))
    assert _lookup(M,0)==0
    for d in range(1,l+1):
        assert _lookup(M,d)==(values[d] if n%d==0 else 0)


def test_quotient_witness_is_real_but_the_unweighted_input_is_at_the_divisor():
    values=(99,0,0,17,-9,23,0,0,0,0,0,0,0)
    F=_table_code(values,(0,)*len(values))
    masked=_masked_values(F,12,12)
    assert 12==3*4 and masked[3]==17 and masked[3]!=_lookup(F,4)
    assert 12%5!=0 and _lookup(F,5)==23 and masked[5]==0


def test_positive_source_equality_ignores_completely_different_zero_entries():
    values=(1,-2,4,-5,0,9)
    F=_table_code((101,)+values,(0,)*7)
    G=_table_code((-202,)+values,tuple(range(10,17)))
    assert _lookup(F,0)!=_lookup(G,0)
    assert all(_lookup(F,i)==_lookup(G,i) for i in range(1,7))
    assert _masked_values(F,6,6)==_masked_values(G,6,6)
    assert sum(_lookup(F,i) for i in range(7))!=sum(_lookup(G,i) for i in range(7))


@pytest.mark.parametrize('first',(-8,0,11))
def test_unit_divisor_sum_is_F_one_not_F_zero_plus_F_one(first):
    F=_table_code((137,first),(4,8))
    masked=_masked_values(F,1,1)
    assert masked==(0,first) and sum(masked)==first
    assert sum(masked)!=137+first
    assert sum(masked[:1])!=first or first==0


def test_zero_divisor_guard_prevents_overlapping_keep_and_omit_values():
    F=_table_code((7,),(2,))
    assert 0==0*0 and _lookup(F,0)==7
    assert _masked_values(F,0,0)==(0,)
    assert _lookup(F,0)!=0  # Without d!=0, the two entry branches would disagree.


def test_mask_code_and_component_uniqueness_is_not_claimed():
    values=(0,3,-4,0)
    M=_table_code(values,(0,)*4)
    K=_table_code(values,(10,11,12,13))
    assert M!=K and all(_lookup(M,i)==_lookup(K,i) for i in range(4))


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
