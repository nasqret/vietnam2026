"""Actual positive quotient/involution contracts and original-HA bodies."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
from pathlib import Path
import re
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / 'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT / 'scripts'))

from constructive_lower_tier_support import closure, previous_rows
from constructive_lower_tier_checkpoints import all_new_rows
from peano_lab.library import divisor_involution_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.finite_fold_surface import _beta_at_term
from peano_lab.library.prime_valuation_support_candidate import _and
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_divisor_sum_reindex_candidate import _encode_beta
from tests.test_divisor_sum_table_candidate import _assert_same_ast


@lru_cache(maxsize=1)
def core():
    # These authenticated specifications are only premises for conditional
    # body checks.  A later complete bundle must prove all actual ancestors.
    inherited = (*closure.parent_snapshot().specs,*previous_rows(),*all_new_rows())
    assert len(inherited) == len({row.name for row in inherited}) == 3518
    assert closure.PARENT_CATALOG_SHA256 == 'ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
    return {row.name: row for row in inherited}


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_involution_candidate_theorems(TheoremSpec)


EXPECTED = ((102,102,36),(34,34,12),(105,105,27),(34,34,15),(71,71,25),(48,48,23),
            (95,95,32),(43,43,22),(188,180,35),(24,24,15),(118,118,29),(58,58,22))
PRINCIPAL_STATEMENT_SHA256 = {
    'positive_divisor_quotient_exists_unique': 'a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384',
    'positive_divisor_involution_exists': '7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d',
    'divisor_complement_prefix_involution': '24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1',
    'divisor_complement_prefix_positive_quotient': '758424c31f40bb748a54a9609b49b71c9df767580b50917f16d44e4e08e2edf0',
}


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert checked.name == row.name
        assert (checked.proof_nodes,checked.proof_objects,checked.proof_depth) == EXPECTED[rows().index(row)]
    finally:
        gc.collect()


def test_exact_topology_has_no_shadowing_or_unused_declared_dependency():
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        for dependency in row.dependencies:
            assert any(re.search(r'\b'+re.escape(dependency)+r'\b',command) for command in row.script)
        assert not any(command.startswith(('use ','admit','sorry','ring')) for command in row.script)
        available.add(row.name)


def test_literal_inventory_and_principal_statement_pins():
    assert len(rows())==12
    assert sum(len(row.dependencies) for row in rows())==34
    assert sum(len(row.script) for row in rows())==480
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest() == '16959bbf9fd0bb571dab2e5034cc2d8c647cccde91e1bfe4da28f38126a93f41'
    for name,digest in PRINCIPAL_STATEMENT_SHA256.items():
        assert sha256(next(row.statement for row in rows() if row.name==name).encode()).hexdigest()==digest


def test_exact_ast_novelty_includes_all_3518_earlier_rows():
    from constructive_lower_tier_support import statement_duplicates
    # The old helper's base is3222+170; placing the frozen126 before the new
    # rows also checks that entire latest tranche, without admitting anything.
    assert statement_duplicates((*all_new_rows(),*rows())) == ()


def _expected_complement(n,d,q):
    return f'(~(({d})=0) /\\ ({n})=({d})*({q})) \\/ ((({d})=0 \\/ ~(exists ind_dv_factor. ({n})=({d})*ind_dv_factor)) /\\ ({q})=({d}))'


def _expected_at(b,c,i,q,tag):
    return _beta_at_term(*(f'({term})' for term in (b,c,i,q)),tag='ind_dv_'+tag,avoid=())


def _expected_lt(a,b):
    return f'exists ind_dv_gap. ind_dv_gap+S ({a})=({b})'


def _expected_prefix(n,b,c,l):
    return ('forall ind_dv_index. ('+_expected_lt('ind_dv_index',l)+') -> exists ind_dv_value. '
            +_and(_expected_at(b,c,'ind_dv_index','ind_dv_value','prefix'),_expected_complement(n,'ind_dv_index','ind_dv_value')))


def _expected_permutation(b,c,l):
    bound = ('forall ind_dv_i. ('+_expected_lt('ind_dv_i',l)+') -> exists ind_dv_a. '
             +_and(_expected_at(b,c,'ind_dv_i','ind_dv_a','bound'),_expected_lt('ind_dv_a',l)))
    injection = ('forall ind_dv_i ind_dv_j ind_dv_a. ('+_expected_lt('ind_dv_i',l)+') -> ('+_expected_lt('ind_dv_j',l)+') -> ('
                 +_expected_at(b,c,'ind_dv_i','ind_dv_a','injection_left')+') -> ('+_expected_at(b,c,'ind_dv_j','ind_dv_a','injection_right')+') -> ind_dv_i=ind_dv_j')
    surjection = ('forall ind_dv_a. ('+_expected_lt('ind_dv_a',l)+') -> exists ind_dv_i. '
                  +_and(_expected_lt('ind_dv_i',l),_expected_at(b,c,'ind_dv_i','ind_dv_a','surjection')))
    return _and(bound,injection,surjection)


SURFACES=((candidate.positive_divisor_complement_relation,('n','d','q'),_expected_complement),
          (candidate.divisor_complement_prefix_relation,('n','b','c','l'),_expected_prefix))


@pytest.mark.parametrize('builder,args,expected',SURFACES)
@pytest.mark.parametrize('variant',('variables','compound','constants','large_numeral'))
def test_public_graphs_are_exact_hygienic_actual_product_and_beta_relations(builder,args,expected,variant):
    context=tuple(dict.fromkeys(args))
    terms=tuple(name if variant=='variables' else f'{name}+{name}' if variant=='compound' else '0' if variant=='constants'
                else str(2**90+37) if index==0 else name for index,name in enumerate(args))
    prefix='forall '+' '.join(context)+'. '
    _assert_same_ast(_closed_formula(prefix+builder(*terms,tag='contract',variables=context)),
                     _closed_formula(prefix+expected(*terms)))


@pytest.mark.parametrize('builder,args,expected',SURFACES)
def test_all_generated_binders_and_the_whole_context_are_hygienic(builder,args,expected):
    context=tuple(dict.fromkeys(args))
    text=builder(*args,tag='capture',variables=context)
    binders={name for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',text) for name in group.split()}
    assert binders
    for binder in binders:
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=context+(binder,))
    for bad in ((),context+(context[0],),context[:-1]):
        with pytest.raises(ValueError):
            builder(*args,tag='capture',variables=bad)
    for bad in ('missing',args[0]+' ) -> false',args[0]+' / 2'):
        with pytest.raises(ValueError):
            builder(bad,*args[1:],tag='capture',variables=context)
    with pytest.raises(ValueError):
        builder(*args,tag='bad tag',variables=context)


def _quotient_root(*,positive_input=True,positive_quotient=True,quotient_bound=True,uniqueness=True):
    properties=['n=d*q']
    if positive_quotient: properties.append('~(q=0)')
    properties.append('exists w. n=q*w')
    if quotient_bound: properties.append('exists h. h+q=n')
    if uniqueness: properties.append('forall r. n=d*r -> r=q')
    return ('forall n d. '+('~(n=0) -> ' if positive_input else '')+'(exists k. n=d*k) -> exists q. '+_and(*properties))


def _involution_root(*,positive=True,permutation=True,length='S n'):
    result=_expected_prefix('n','b','c',length)
    if permutation: result=_and(result,_expected_permutation('b','c',length))
    return 'forall n. '+('~(n=0) -> ' if positive else '')+'exists b c. '+result


def _decoded_root(*,positive=True,bounded=True,equation_input=False):
    if equation_input:
        return ('forall n b c d q. ~(n=0) -> ('+_expected_prefix('n','b','c','S n')+') -> ~(d=0) -> n=d*q -> '
                +_expected_at('b','c','d','q','quotient_root'))
    return ('forall n b c i q. '+('~(n=0) -> ' if positive else '')+'('+_expected_prefix('n','b','c','S n')+') -> '
            +('(exists h. h+i=n) -> ' if bounded else '')+'('+_expected_at('b','c','i','q','decoded_first')+') -> '
            +_expected_at('b','c','q','i','decoded_second'))


@pytest.mark.parametrize('name,expected',(
    ('positive_divisor_quotient_exists_unique',_quotient_root()),
    ('positive_divisor_involution_exists',_involution_root()),
    ('divisor_complement_prefix_involution',_decoded_root()),
    ('divisor_complement_prefix_positive_quotient',_decoded_root(equation_input=True)),
))
def test_independently_written_principal_contracts(name,expected):
    row=next(row for row in rows() if row.name==name)
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected))


@pytest.mark.parametrize('name,statement',(
    ('positive_divisor_quotient_exists_unique',_quotient_root(positive_input=False)),
    ('positive_divisor_quotient_exists_unique',_quotient_root(positive_quotient=False)),
    ('positive_divisor_quotient_exists_unique',_quotient_root(quotient_bound=False)),
    ('positive_divisor_quotient_exists_unique',_quotient_root(uniqueness=False)),
    ('positive_divisor_involution_exists',_involution_root(permutation=False)),
    ('positive_divisor_involution_exists',_involution_root(length='n')),
    ('divisor_complement_prefix_involution',_decoded_root(positive=False)),
    ('divisor_complement_prefix_involution',_decoded_root(bounded=False)),
))
def test_original_proof_rejects_altered_principal_contracts(name,statement):
    row=next(row for row in rows() if row.name==name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_poisoned_theorem_is_not_accepted(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_used_dependency_is_not_an_implicit_oracle(row):
    if not row.dependencies:
        assert row.name=='divisor_complement_positive_equation'
        return
    dependency=row.dependencies[0]
    basis=core() | {r.name:r for r in rows()}
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=basis)


def _complement_value(n,d):
    return n//d if d and n%d==0 else d


@pytest.mark.parametrize('n',(1,2,3,4,6,8,9,12,18,24))
def test_actual_beta_permutation_decodes_twice_and_preserves_every_positive_quotient(n):
    values=tuple(_complement_value(n,d) for d in range(n+1))
    b,c=_encode_beta(values)
    decoded=tuple(b%(1+(i+1)*c) for i in range(n+1))
    assert decoded==values
    assert sorted(decoded)==list(range(n+1))
    for d,q in enumerate(decoded):
        assert decoded[q]==d
        assert 0<=q<=n
        if d and n%d==0:
            assert n==d*q and q>0 and n%q==0
            assert [r for r in range(n+1) if n==d*r]==[q]
        else:
            assert q==d


@pytest.mark.parametrize('n,length',((1,0),(1,7),(6,0),(6,2),(6,7),(6,13),(10,17)))
def test_prefix_construction_is_not_falsely_limited_to_S_n(n,length):
    values=tuple(_complement_value(n,d) for d in range(length))
    b,c=_encode_beta(values)
    assert tuple(b%(1+(i+1)*c) for i in range(length))==values


def test_zero_input_explains_the_positive_quotient_and_unrestricted_symmetry_guards():
    assert _complement_value(0,1)==0
    assert _complement_value(0,0)==0
    assert _complement_value(0,_complement_value(0,1))!=1
    assert 0==1*0  # The actual quotient is not positive when n=0.


@pytest.mark.parametrize('root',(1,2,3,4,9))
def test_divisor_complement_is_not_falsely_claimed_fixed_point_free(root):
    assert _complement_value(root*root,root)==root


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
