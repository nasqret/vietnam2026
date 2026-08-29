"""Independent full finite signed Möbius inversion contracts and HA checks.

This file does not own or alter the mathematical candidate. Independent
literal graphs, actual beta diagnostics and hostile authoring tests check
its boundary; none is used to admit a theorem or bypass full closure.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from random import Random
import re
import sys

import pytest

from peano_lab.library import mobius_inversion_candidate as candidate
from peano_lab.library.dirichlet_units_candidate import make_dirichlet_units_candidate_theorems
from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec,_closed_formula
from tests.test_dirichlet_associativity_candidate import core as association_core,rows as association_rows
from tests.test_dirichlet_fubini_candidate import actual_convolution
from tests.test_dirichlet_convolution_candidate import (
    _conjoin,expected_table,expected_at,expected_le,expected_convolution,expected_convolution_table,expected_positive_equal,
)
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_divisor_mask_candidate import _expected_divisor_sum
from tests.test_mobius_table_candidate import _expected_mu_table
from tests.test_mobius_value_candidate import _integer_mu
from tests.test_signed_rectangular_slice_candidate import _instantiate,actual_sum_trace,BoundedTestSelection
from tests.test_signed_table_operations_candidate import model_table,model_at,decode_signed,encode_signed


EXPECTED=((46,29),(41,24),(90,32),(92,40),(116,46),(46,28),(216,45),(62,24))
ROOT_PINS={
    'arithmetic_divisor_transform_convolution':'1a1351a2192050706a610c087073608db1607e6a95211c455f4c8c96b788face',
    'arithmetic_divisor_convolution_transform':'cc0fac1007dfddd037c1bb6d520900e5b9f78eec48d064ad9947588d5890dc88',
    'mobius_constant_one_convolution_delta':'80179388561a414b176711cc9c2f1d5547bd30a628ea4628e77cdb3333c99d9e',
    'mobius_dirichlet_inversion_value':'d0939137bcaad092eca200d68eba1e4c44602c41c31bc854983f7594c632b0da',
    'mobius_inversion_for_actual_mobius_table':'c69a34ea1a32d3d1188c00a95754507739ed77b953a355e2ffccf0ad69e21dab',
    'mobius_inversion_arithmetic_tables':'a0cacd2561b809b9cd7e9909fd37cbbcd7a60f086560bf1bd5a2fecad5c978b9',
    'mobius_inversion_reconstructs_divisor_transform':'6cb49be33af24bbb85373f81287581f2ae0492116acd5163300ab049ed7c533b',
    'mobius_inversion_iff':'c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1',
}


@lru_cache(maxsize=1)
def rows():return candidate.make_mobius_inversion_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    return association_core()|{row.name:row for row in (*association_rows(),*make_dirichlet_units_candidate_theorems(TheoremSpec))}


def expected_divisor_sum(F,n,z,tag):
    return _instantiate(_expected_divisor_sum('SOURCE','INPUT','VALUE'),{'SOURCE':F,'INPUT':n,'VALUE':z},tag)


def expected_mobius_table(N,M,tag):
    return _instantiate(_expected_mu_table('BOUND','MOBIUS'),{'BOUND':N,'MOBIUS':M},tag)


def expected_one(N,U,tag):
    i,z='model_one_index_'+tag,'model_one_value_'+tag
    return _conjoin(expected_table(N,U,tag+'table'),f'forall {i} {z}. ~({i}=0) -> '
        f'({expected_le(i,N,tag+"bound")}) -> ({expected_at(U,i,z,tag+"lookup")}) -> {z}=2')


def expected_delta(N,E,tag):
    i,z='model_delta_index_'+tag,'model_delta_value_'+tag
    return _conjoin(expected_table(N,E,tag+'table'),f'forall {i} {z}. ~({i}=0) -> '
        f'({expected_le(i,N,tag+"bound")}) -> ({expected_at(E,i,z,tag+"lookup")}) -> '
        f'(({i}=1 -> {z}=2) /\\ (~({i}=1) -> {z}=0))')


def expected_transform(N,F,G,tag):
    n,z='model_transform_input_'+tag,'model_transform_value_'+tag
    return (f'forall {n} {z}. ~({n}=0) -> ({expected_le(n,N,tag+"bound")}) -> '
            f'({expected_at(G,n,z,tag+"lookup")}) -> ({expected_divisor_sum(F,n,z,tag+"sum")})')


def expected_statements():
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='inversion_'+str(counter))
        return call
    T,A,L,C,CT,PE,M,U,E,D=tuple(tagged(function) for function in (
        expected_table,expected_at,expected_le,expected_convolution,expected_convolution_table,
        expected_positive_equal,expected_mobius_table,expected_one,expected_delta,expected_transform))
    def all_(names,*clauses):return 'forall '+names+'. '+' -> '.join('('+clause+')' for clause in clauses)
    implication=D('N','F','G');convolution=CT('N','M','G','F')
    return {
        'arithmetic_divisor_transform_convolution':all_('N F G U',T('N','F'),T('N','G'),U('N','U'),D('N','F','G'),CT('N','F','U','G')),
        'arithmetic_divisor_convolution_transform':all_('N F G U',U('N','U'),CT('N','F','U','G'),D('N','F','G')),
        'mobius_constant_one_convolution_delta':all_('N M U E',M('N','M'),U('N','U'),E('N','E'),CT('N','M','U','E')),
        'mobius_dirichlet_inversion_value':all_('N F G M U E n a b',T('N','F'),T('N','G'),M('N','M'),U('N','U'),E('N','E'),D('N','F','G'),
            '~(n=0)',L('n','N'),A('F','n','a'),C('M','G','n','b'),'a=b'),
        'mobius_inversion_for_actual_mobius_table':all_('N F G M',T('N','F'),T('N','G'),M('N','M'),D('N','F','G'),CT('N','M','G','F')),
        'mobius_inversion_arithmetic_tables':all_('N F G',T('N','F'),T('N','G'),D('N','F','G'),
            'exists M H. '+_conjoin(M('N','M'),CT('N','M','G','H'),PE('H','F','N'))),
        'mobius_inversion_reconstructs_divisor_transform':all_('N F G M',T('N','F'),T('N','G'),M('N','M'),CT('N','M','G','F'),D('N','F','G')),
        'mobius_inversion_iff':all_('N F G M',T('N','F'),T('N','G'),M('N','M'),
            _conjoin(f'({implication}) -> ({convolution})',f'({convolution}) -> ({implication})')),
    }


@pytest.mark.parametrize('mode',('identifiers','compound','large','zero','repeated'))
def test_public_transform_is_the_independent_full_positive_divisor_sum_graph(mode):
    arguments=('N','F','G');context=('N','F','G','unused')
    if mode=='compound':arguments=('N+F','F*G','G+N')
    if mode=='large':arguments=('999999999999999999999999999999999999','F','G')
    if mode=='zero':arguments=('0',)*3
    if mode=='repeated':arguments=('F',)*3
    actual=candidate.signed_arithmetic_divisor_transform_relation(*arguments,tag='contract',variables=context)
    _assert_same_ast(_closed_formula('forall '+' '.join(context)+'. '+actual),
                     _closed_formula('forall '+' '.join(context)+'. '+expected_transform(*arguments,'independent')))


def test_every_transform_binder_rejects_collision_with_unused_context_variables():
    builder=candidate.signed_arithmetic_divisor_transform_relation
    context=('N','F','G','unused')
    source=builder('N','F','G',tag='capture',variables=context)
    binders={name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source) for name in clause.split()}
    assert binders and not binders.intersection(context)
    for binder in binders:
        with pytest.raises(ValueError):builder('N','F','G',tag='capture',variables=context+(binder,))


@pytest.mark.parametrize('bad',('unknown','formula','division','empty','duplicate','missing','list','bad-tag','reserved-tag'))
def test_malformed_transform_terms_and_contexts_are_rejected(bad):
    arguments=('N','F','G');context=('N','F','G');tag='invalid'
    if bad=='unknown':arguments=('unknown_variable','F','G')
    if bad=='formula':arguments=('N -> false','F','G')
    if bad=='division':arguments=('N / 2','F','G')
    if bad=='empty':context=()
    if bad=='duplicate':context=context+('N',)
    if bad=='missing':context=context[:-1]
    if bad=='list':context=list(context)
    if bad=='bad-tag':tag='bad tag'
    if bad=='reserved-tag':tag='forall'
    with pytest.raises(ValueError):candidate.signed_arithmetic_divisor_transform_relation(*arguments,tag=tag,variables=context)


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_all_eight_principal_statements_have_independent_exact_contracts(row):
    statements=expected_statements()
    assert tuple(statements)==tuple(item.name for item in rows())
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(statements[row.name]))


def test_exact_native_topology_source_pins_and_real_dependencies():
    assert len(rows())==8
    assert sum(len(row.dependencies) for row in rows())==28
    assert sum(len(row.script) for row in rows())==458
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='8c3f2f2c6a84ded9f245f11eb66b35a2202fabfa00e790cee4793ceef14c7703'
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies)) and set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script)) for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    assert {row.name:sha256(row.statement.encode()).hexdigest() for row in rows()}==ROOT_PINS


def test_all_new_inversion_asts_are_novel_against_3643_and_other_new_rows():
    from constructive_dirichlet_support import statement_duplicates
    from peano_lab.library.dirichlet_convolution_candidate import make_dirichlet_convolution_candidate_theorems
    from peano_lab.library.signed_finite_support_candidate import make_signed_finite_support_candidate_theorems
    from peano_lab.library.dirichlet_commutativity_candidate import make_dirichlet_commutativity_candidate_theorems
    from tests.test_dirichlet_fubini_candidate import rows as grid_rows
    current=(*make_dirichlet_convolution_candidate_theorems(TheoremSpec),*make_signed_finite_support_candidate_theorems(TheoremSpec),
        *make_dirichlet_commutativity_candidate_theorems(TheoremSpec),*make_dirichlet_units_candidate_theorems(TheoremSpec),
        *grid_rows(),*association_rows(),*rows())
    assert len(current)==113
    assert statement_duplicates(current)==()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        receipt=replay_candidate_bodies((row,),core=core()|{item.name:item for item in rows()})[0]
        assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED[rows().index(row)]
        assert receipt.proof_objects==receipt.proof_nodes
    except CandidateBodyError as error:pytest.fail(str(error),pytrace=False)
    finally:gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_cannot_reuse_a_valid_body(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((replace(row,script=()),),core=core()|{item.name:item for item in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_dropped_dependency_cannot_be_used(row,dependency):
    changed=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((changed,),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_poisoned_dependency_cannot_replace_actual_statement(row,dependency):
    table=core()|{item.name:item for item in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):replay_candidate_bodies((row,),core=table)


def actual_divisor_sum(F,n,*,offset=7):
    if n<=0:raise ValueError('divisor sums are positive-input graphs')
    values=tuple(0 if d==0 or n%d else decode_signed(model_at(F,d)) for d in range(n+1))
    mask=model_table(values,offset=offset,endpoint=683)
    assert all(model_at(mask,d)==encode_signed(value) for d,value in enumerate(values))
    return actual_sum_trace(mask,n+1),mask


def actual_mobius_table(N,*,offset):
    return model_table(tuple([0]+[_integer_mu(n) for n in range(1,N+1)]),offset=offset,endpoint=677)


@pytest.mark.parametrize('N',(0,1,2,4,6,8))
@pytest.mark.parametrize('seed',(0,17,101))
def test_actual_beta_signed_transform_and_mobius_inverse_with_independent_zero_values(N,seed):
    random=Random(seed)
    values=tuple([211]+[random.randint(-7,7) for _ in range(N)])
    F=model_table(values,offset=3,endpoint=673)
    transform=[-223]
    for n in range(1,N+1):transform.append(decode_signed(actual_divisor_sum(F,n)[0]))
    G=model_table(tuple(transform),offset=5,endpoint=-673)
    M=actual_mobius_table(N,offset=7);M2=actual_mobius_table(N,offset=11)
    assert M[0]!=M2[0] and M[1]!=M2[1]
    recovered=[227]
    for n in range(1,N+1):
        assert model_at(G,n)==actual_divisor_sum(F,n,offset=13)[0]
        inverse,_=actual_convolution(M,G,n)
        assert inverse==actual_convolution(M2,G,n)[0]==model_at(F,n)
        recovered.append(decode_signed(inverse))
    H=model_table(tuple(recovered),offset=17,endpoint=661)
    assert len({model_at(code,0) for code in (F,G,H)})==3
    assert F[0]!=H[0]
    for n in range(1,N+1):assert model_at(H,n)==model_at(F,n)
    if N==0:assert model_at(M,0)==0 and actual_sum_trace(M,0)==0


@pytest.mark.parametrize('N',(0,1,2,4,6,8))
@pytest.mark.parametrize('seed',(0,17,101))
def test_actual_inverse_reconstructs_every_positive_original_divisor_transform(N,seed):
    random=Random(seed)
    G=model_table(tuple([-229]+[random.randint(-7,7) for _ in range(N)]),offset=3)
    M=actual_mobius_table(N,offset=5)
    original=[233]
    for n in range(1,N+1):original.append(decode_signed(actual_convolution(M,G,n)[0]))
    F=model_table(tuple(original),offset=7)
    for n in range(1,N+1):
        assert actual_convolution(M,G,n)[0]==model_at(F,n)
        assert actual_divisor_sum(F,n)[0]==model_at(G,n)
    assert model_at(F,0)!=model_at(G,0)


def test_only_the_last_transform_value_is_insufficient_for_inversion():
    # g(2)=f(1)+f(2) holds, but deliberately wrong g(1) changes the inverse.
    F=model_table((19,3,5),offset=3)
    G=model_table((-23,101,8),offset=5)
    M=actual_mobius_table(2,offset=7)
    assert actual_divisor_sum(F,2)[0]==model_at(G,2)
    assert actual_divisor_sum(F,1)[0]!=model_at(G,1)
    assert actual_convolution(M,G,2)[0]!=model_at(F,2)


def test_signed_one_is_code_two_and_zero_is_not_a_divisor_sum_input():
    M=actual_mobius_table(1,offset=3)
    assert model_at(M,1)==2 and decode_signed(1)==-1
    F=model_table((101,-3),offset=5)
    G=model_table((-103,-3),offset=7)
    assert actual_convolution(M,G,1)[0]==actual_divisor_sum(F,1)[0]==model_at(F,1)
    with pytest.raises(ValueError):actual_divisor_sum(F,0)


if __name__=='__main__':
    import argparse,resource,signal,time
    parser=argparse.ArgumentParser();parser.add_argument('--body');parser.add_argument('--start',type=int,default=0);parser.add_argument('--count',type=int,default=1);parser.add_argument('--pytest-select');parser.add_argument('--case-start',type=int,default=0);parser.add_argument('--case-count',type=int)
    args=parser.parse_args();resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if args.pytest_select is not None:
        plugins=[] if args.case_count is None else [BoundedTestSelection(args.case_start,args.case_count)]
        status=pytest.main(['-q',__file__,'-k',args.pytest_select],plugins=plugins)
    else:
        selected=tuple(row for row in rows() if row.name==args.body) if args.body else rows()[args.start:args.start+args.count]
        if not selected:raise SystemExit('unknown theorem body')
        for row in selected:
            test_original_kernel_body(row)
            print(json.dumps({'name':row.name,'nodes':EXPECTED[rows().index(row)][0],'depth':EXPECTED[rows().index(row)][1]}),flush=True)
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
