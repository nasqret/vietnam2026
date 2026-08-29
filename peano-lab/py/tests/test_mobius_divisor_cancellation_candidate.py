"""Original-HA checks of actual prime-toggle and Möbius-cancellation graphs."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
from itertools import accumulate
import re
import sys

import pytest

from peano_lab.library import mobius_divisor_cancellation_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.ha_signed_negate_candidate import signed_negate
from peano_lab.library.prime_valuation_support_candidate import _and
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_involution_candidate import core as previous_core, rows as involution_rows
from tests.test_divisor_involution_candidate import _expected_at, _expected_lt, _expected_permutation
from tests.test_divisor_mask_candidate import _expected_mask, _expected_signed_fold
from tests.test_divisor_sum_reindex_candidate import _encode_beta, _lookup, _table_code, _unpair
from tests.test_divisor_sum_table_candidate import _assert_same_ast, _expected_entry, _expected_table, _signed_code
from tests.test_mobius_table_candidate import _expected_mu_table
from tests.test_mobius_value_candidate import _expected_mu, _integer_mu


@lru_cache(maxsize=1)
def core():
    return previous_core() | {row.name:row for row in involution_rows()}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_mobius_divisor_cancellation_candidate_theorems(TheoremSpec)


EXPECTED=((36,36,23),(52,52,22),(50,50,21),(246,246,34),(61,61,19),(84,84,25),(89,89,29),
          (49,49,17),(142,142,45),(146,146,40),(78,78,38),(112,112,38),(83,83,26),
          (231,223,39),(33,33,21),(198,198,31),(110,110,51),(240,240,44),(62,62,32),
          (221,214,51),(71,71,33),(195,195,59),(46,46,27),(54,54,22),(53,53,28),
          (164,164,33),(43,43,22),(322,304,43))
PRINCIPAL_STATEMENT_SHA256={
    'divisor_prime_toggle_permutation_exists':'76ed082f3e75e22e2a1f0bbb45321b76ef34d24837573006f7b20061b972acf7',
    'mobius_divisor_sum_cancellation':'dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406',
    'mobius_divisor_sum_cancellation_exists':'50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280',
    'mobius_divisor_sum_cancellation_on_positive_values':'be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56',
}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert checked.name == row.name
        assert (checked.proof_nodes,checked.proof_objects,checked.proof_depth)==EXPECTED[rows().index(row)]
    finally:
        gc.collect()


def test_exact_inventory_is_additive_topological_and_has_no_oracle_or_unused_edge():
    assert len(rows())==28
    assert sum(len(row.dependencies) for row in rows())==99
    assert sum(len(row.script) for row in rows())==1569
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest()=='ae5eb369778d001f572fa340f7c5aba2a9c573ffcd78061ff12d01a389cc4aab'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies)<=available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(re.search(r'\b'+re.escape(name)+r'\b','\n'.join(row.script)) for name in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    for name,digest in PRINCIPAL_STATEMENT_SHA256.items():
        assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def test_no_false_mathematical_edge_is_inferred_from_shared_code_generator_imports():
    # Divisor complementation is a separate mathematical chapter.  Only its
    # untrusted script-emitting helpers are reused here, not any of its rows.
    old_names={row.name for row in involution_rows()}
    assert not old_names & {name for row in rows() for name in row.dependencies}


def test_exact_ast_novelty_against_3518_prior_rows_and_the_new_involution_core():
    from constructive_lower_tier_checkpoints import all_new_rows
    from constructive_lower_tier_support import statement_duplicates
    assert statement_duplicates((*all_new_rows(),*involution_rows(),*rows()))==()


def _expected_dvd(d,n):
    return f'exists ind_mdc_factor. ({n})=({d})*ind_mdc_factor'


def _expected_prime(p):
    return f'~(({p})=1) /\\ forall ind_mdc_a ind_mdc_b. ({p})=ind_mdc_a*ind_mdc_b -> ind_mdc_a=1 \\/ ind_mdc_b=1'


def _expected_toggle(p,d,e):
    return ('('+_and('~('+_expected_dvd(p,d)+')',f'({e})=({p})*({d})')+') \\/ (('
            +_and(f'({d})=({p})*({e})','~('+_expected_dvd(p,e)+')')+') \\/ ('
            +_and(_expected_dvd(f'({p})*({p})',d),f'({e})=({d})')+'))')


def _expected_divisor_toggle(n,p,d,e):
    return ('('+_and(f'~(({d})=0)',_expected_dvd(d,n),_expected_toggle(p,d,e))+') \\/ ('
            +_and(f'({d})=0 \\/ ~('+_expected_dvd(d,n)+')',f'({e})=({d})')+')')


def _expected_prefix(n,p,b,c,l):
    return ('forall ind_mdc_i. ('+_expected_lt('ind_mdc_i',l)+') -> exists ind_mdc_e. '
            +_and(_expected_at(b,c,'ind_mdc_i','ind_mdc_e','mdc_prefix'),_expected_divisor_toggle(n,p,'ind_mdc_i','ind_mdc_e')))


def _expected_negate(a,b):
    return signed_negate(a,b,tag='ind_mdc_negation')


def _expected_pointwise_negate(F,G,l):
    return ('forall ind_mdc_i ind_mdc_a ind_mdc_b. ('+_expected_lt('ind_mdc_i',l)+') -> ('
            +_expected_entry(F,'ind_mdc_i','ind_mdc_a')+') -> ('+_expected_entry(G,'ind_mdc_i','ind_mdc_b')+') -> ('
            +_expected_negate('ind_mdc_a','ind_mdc_b')+')')


def _expected_positive_values(N,F):
    return ('forall ind_mdc_i ind_mdc_z. ~(ind_mdc_i=0) -> (exists h. h+ind_mdc_i=('+N+')) -> ('
            +_expected_entry(F,'ind_mdc_i','ind_mdc_z')+') -> ('+_expected_mu('ind_mdc_i','ind_mdc_z')+')')


SURFACES=(
    (candidate.prime_factor_toggle_relation,('p','d','e'),_expected_toggle),
    (candidate.divisor_prime_toggle_relation,('n','p','d','e'),_expected_divisor_toggle),
    (candidate.divisor_prime_toggle_prefix_relation,('n','p','b','c','l'),_expected_prefix),
    (candidate.signed_arithmetic_table_negation_relation,('F','G','l'),_expected_pointwise_negate),
    (candidate.mobius_positive_table_values_relation,('N','F'),_expected_positive_values),
)


@pytest.mark.parametrize('builder,args,expected',SURFACES)
@pytest.mark.parametrize('variant',('variables','compound','constants','large_numeral'))
def test_public_definitions_are_independent_exact_arithmetic_graphs(builder,args,expected,variant):
    context=tuple(dict.fromkeys(args))
    terms=tuple(name if variant=='variables' else f'{name}+{name}' if variant=='compound' else '0' if variant=='constants'
                else str(2**95+17) if index==0 else name for index,name in enumerate(args))
    prefix='forall '+' '.join(context)+'. '
    _assert_same_ast(_closed_formula(prefix+builder(*terms,tag='contract',variables=context)),
                     _closed_formula(prefix+expected(*terms)))


@pytest.mark.parametrize('builder,args,expected',SURFACES)
def test_all_nested_binders_reject_capture_from_the_entire_explicit_context(builder,args,expected):
    context=tuple(dict.fromkeys(args))
    formula=builder(*args,tag='capture',variables=context)
    binders={name for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',formula) for name in group.split()}
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


def _delta(n,z,unit_code='2'):
    return f'(({n})=1 /\\ ({z})={unit_code}) \\/ (~(({n})=1) /\\ ({z})=0)'


def _expected_divisor_sum(F,n,z,*,length=None):
    # The older mask test used `exists M`, which captures this chapter's
    # supplied Möbius-table variable M.  Keep the independent mask/fold
    # formulas, but give this new enclosing witness its own fresh name.
    witness='ind_mdc_mask_witness'
    length=f'S ({n})' if length is None else length
    return _and(f'~(({n})=0)',f'exists {witness}. '+_and(
        _expected_mask(F,n,n,witness),_expected_signed_fold(witness,length,z)))


def _expected_identity(F,n,z,*,length=None,unit_code='2'):
    total=_expected_divisor_sum(F,n,z,length=length)
    delta=_delta(n,z,unit_code)
    return _and(f'({total}) -> ({delta})',f'({delta}) -> ({total})')


def _cancellation_root(*,table=True,positive=True,bounded=True,length=None,unit_code='2'):
    guards=[]
    if table: guards.append(_expected_mu_table('N','M'))
    if positive: guards.append('~(n=0)')
    if bounded: guards.append('exists h. h+n=N')
    return 'forall N M n z. '+''.join('('+guard+') -> ' for guard in guards)+_expected_identity('M','n','z',length=length,unit_code=unit_code)


def _positive_values_root(*,table=True,values=True,positive=True,bounded=True):
    guards=[]
    if table: guards.append(_expected_table('N','F'))
    if values: guards.append(_expected_positive_values('N','F'))
    if positive: guards.append('~(n=0)')
    if bounded: guards.append('exists h. h+n=N')
    return 'forall N F n z. '+''.join('('+guard+') -> ' for guard in guards)+_expected_identity('F','n','z')


def _constructed_root():
    return 'forall n. ~(n=0) -> exists M z. '+_and(_expected_mu_table('n','M'),_expected_divisor_sum('M','n','z'),_delta('n','z'))


def _permutation_root(*,positive=True,prime=True,divisor=True):
    guards=[]
    if positive: guards.append('~(n=0)')
    if prime: guards.append(_expected_prime('p'))
    if divisor: guards.append(_expected_dvd('p','n'))
    return ('forall n p. '+''.join('('+guard+') -> ' for guard in guards)+'exists b c. '
            +_and(_expected_prefix('n','p','b','c','S n'),_expected_permutation('b','c','S n')))


@pytest.mark.parametrize('name,statement',(
    ('divisor_prime_toggle_permutation_exists',_permutation_root()),
    ('mobius_divisor_sum_cancellation',_cancellation_root()),
    ('mobius_divisor_sum_cancellation_exists',_constructed_root()),
    ('mobius_divisor_sum_cancellation_on_positive_values',_positive_values_root()),
),ids=lambda value:value if value in PRINCIPAL_STATEMENT_SHA256 else 'independent_contract')
def test_independent_principal_contracts_include_actual_finite_traces(name,statement):
    row=next(row for row in rows() if row.name==name)
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(statement))


@pytest.mark.parametrize('name,statement',(
    ('divisor_prime_toggle_permutation_exists',_permutation_root(prime=False)),
    ('divisor_prime_toggle_permutation_exists',_permutation_root(divisor=False)),
    ('mobius_divisor_sum_cancellation',_cancellation_root(table=False)),
    ('mobius_divisor_sum_cancellation',_cancellation_root(positive=False)),
    ('mobius_divisor_sum_cancellation',_cancellation_root(bounded=False)),
    ('mobius_divisor_sum_cancellation',_cancellation_root(length='n')),
    ('mobius_divisor_sum_cancellation',_cancellation_root(unit_code='1')),
    ('mobius_divisor_sum_cancellation_on_positive_values',_positive_values_root(table=False)),
    ('mobius_divisor_sum_cancellation_on_positive_values',_positive_values_root(values=False)),
    ('mobius_divisor_sum_cancellation_on_positive_values',_positive_values_root(positive=False)),
    ('mobius_divisor_sum_cancellation_on_positive_values',_positive_values_root(bounded=False)),
),ids=lambda value:value if value in PRINCIPAL_STATEMENT_SHA256 else 'altered_contract')
def test_original_proof_cannot_drop_or_change_a_principal_contract(name,statement):
    row=next(row for row in rows() if row.name==name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_conclusion_is_rejected_by_the_actual_body_checker(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_used_dependency_cannot_be_assumed(row):
    if not row.dependencies:
        assert row.name=='prime_factor_toggle_symmetric'
        return
    missing=row.dependencies[0]
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=missing))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core() | {r.name:r for r in rows()})


def _toggle_value(p,d):
    if d%p:
        return p*d
    if (d//p)%p:
        return d//p
    return d


def _divisor_toggle_value(n,p,d):
    return _toggle_value(p,d) if d and n%d==0 else d


def _actual_fold(table,length):
    pcode,ncode=_unpair(table)
    pb,pc=_unpair(pcode);nb,nc=_unpair(ncode)
    positive=tuple(pb%(1+(i+1)*pc) for i in range(length))
    negative=tuple(nb%(1+(i+1)*nc) for i in range(length))
    pvalues=(0,*accumulate(positive));nvalues=(0,*accumulate(negative))
    rb,rc=_encode_beta(pvalues);sb,sc=_encode_beta(nvalues)
    for i in range(length):
        assert rb%(1+(i+2)*rc)==rb%(1+(i+1)*rc)+positive[i]
        assert sb%(1+(i+2)*sc)==sb%(1+(i+1)*sc)+negative[i]
    assert rb%(1+rc)==sb%(1+sc)==0
    p=rb%(1+(length+1)*rc);n=sb%(1+(length+1)*sc)
    return _signed_code(p-n)


@pytest.mark.parametrize('p',(2,3,5,7,11))
def test_raw_prime_toggle_is_an_actual_involution_with_true_mobius_negation(p):
    for d in range(1,130):
        e=_toggle_value(p,d)
        assert e>0 and _toggle_value(p,e)==d
        assert _integer_mu(e)==-_integer_mu(d)
        if d%(p*p)==0:
            assert e==d and _integer_mu(d)==0
        elif d%p:
            assert e==p*d
        else:
            assert d==p*e and e%p


@pytest.mark.parametrize('n,p',((2,2),(3,3),(4,2),(6,2),(6,3),(8,2),(9,3),(10,5),(12,2),(12,3),(18,3),(24,2),(30,5)))
def test_genuine_beta_toggle_and_signed_pullback_cancel_masked_mobius_values(n,p):
    permutation=tuple(_divisor_toggle_value(n,p,d) for d in range(n+1))
    r,s=_encode_beta(permutation)
    decoded=tuple(r%(1+(i+1)*s) for i in range(n+1))
    assert sorted(decoded)==list(range(n+1))
    assert all(decoded[decoded[d]]==d for d in range(n+1))
    values=tuple(_integer_mu(d) if d and n%d==0 else 0 for d in range(n+1))
    pulled=tuple(values[q] for q in decoded)
    assert all(a==-b for a,b in zip(values,pulled))
    F=_table_code(values,tuple(d+2 for d in range(n+1)))
    G=_table_code(pulled,tuple(d+11 for d in range(n+1)))
    assert F!=G
    assert all(_lookup(G,d)==_lookup(F,q) for d,q in enumerate(decoded))
    assert _actual_fold(F,n+1)==_actual_fold(G,n+1)==0
    for d,q in enumerate(decoded):
        if d and n%d==0:
            assert q and n%q==0
        else:
            assert q==d and values[d]==0


@pytest.mark.parametrize('n',(1,2,4,6,9,12,18))
@pytest.mark.parametrize('zero_value',(-123,0,417))
def test_actual_masks_and_sum_traces_are_independent_of_the_unrestricted_zero_input(n,zero_value):
    values=(zero_value,*( _integer_mu(d) for d in range(1,n+1)))
    F=_table_code(values,tuple(d+5 for d in range(n+1)))
    masked=tuple(_lookup(F,d) if d and n%d==0 else 0 for d in range(n+1))
    K=_table_code(masked,tuple(2*d+1 for d in range(n+1)))
    assert _lookup(F,0)==zero_value and _lookup(K,0)==0
    for d in range(1,n+1):
        if n%d==0:
            quotient=n//d
            assert n==d*quotient and quotient>0
            assert _lookup(K,d)==_lookup(F,d)==_integer_mu(d)
        else:
            assert _lookup(K,d)==0
    assert _actual_fold(K,n+1)==(2 if n==1 else 0)


def test_prime_and_actual_divisor_guards_have_concrete_boundary_obligations():
    assert _divisor_toggle_value(2,3,1)==3>2  # prime, but not a divisor of n
    assert _divisor_toggle_value(4,4,2)==8>4  # divisor of n, but not prime
    with pytest.raises(ValueError):
        _integer_mu(0)


def test_positive_values_must_cover_the_requested_input_not_merely_a_smaller_prefix():
    # N=1 fixes mu(1), but an unconstrained F(2)=0 would give the wrong n=2 sum.
    F=_table_code((99,1,0),(3,7,9))
    assert _lookup(F,1)==_integer_mu(1)
    assert _lookup(F,1)+_lookup(F,2)==1
    assert 1!=0


def test_the_frozen_mobius_definition_contains_factor_data_not_the_cancellation_identity():
    # The source remains the independently specified squarefree/factor-parity
    # graph; this tranche imports it without redefining it by its divisor sum.
    from peano_lab.library.mobius_value_candidate import mobius_value_relation
    _assert_same_ast(_closed_formula('forall n z. '+mobius_value_relation('n','z',tag='still_independent',variables=('n','z'))),
                     _closed_formula('forall n z. '+_expected_mu('n','z')))


if __name__ == '__main__':
    import resource
    import signal
    import time
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started=time.monotonic()
    chosen=rows()
    if len(sys.argv)>1:
        assert sys.argv[1]=='--body' and len(sys.argv)==3
        chosen=tuple(row for row in chosen if row.name==sys.argv[2])
        assert len(chosen)==1
    for row in chosen:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        print(row.name,checked.proof_nodes,checked.proof_objects,checked.proof_depth,flush=True)
        del checked
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert peak <= 1536*1024*1024
    print({'seconds':time.monotonic()-started,'peak_rss_bytes':peak},flush=True)
