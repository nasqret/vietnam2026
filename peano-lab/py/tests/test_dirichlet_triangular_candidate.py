"""Independent triangular contracts, actual beta diagnostics and HA rejection.

The positive mathematical checks replay ordinary dependency-curried bodies.
They do not assert a complete empty-context closure or Alpha admission.  Every
dependency mutation is exercised under the unchanged authoring limits.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

ROOT=Path(__file__).resolve().parents[3]
if str(ROOT/'scripts') not in sys.path:
    sys.path.insert(0,str(ROOT/'scripts'))

from peano_lab.library import dirichlet_triangular_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_dirichlet_convolution_candidate import (
    _conjoin, expected_at, expected_convolution, expected_convolution_table,
    expected_entry, expected_equal, expected_le, expected_prefix,
    expected_signed_multiply, expected_signed_sum, expected_table,
)
from tests.test_divisor_sum_table_candidate import _assert_same_ast
from tests.test_mobius_inversion_candidate import core as previous_core, rows as previous_rows
from tests.test_signed_rectangular_slice_candidate import (
    BoundedTestSelection, _instantiate, actual_sum_trace,
)
from tests.test_signed_table_operations_candidate import (
    decode_signed, encode_signed, expected_signed_operation, model_at, model_table,
)


@lru_cache(maxsize=1)
def core():
    inherited=previous_core()|{row.name:row for row in previous_rows()}
    assert len(inherited)==3756
    return inherited


@lru_cache(maxsize=1)
def rows():
    return candidate.make_dirichlet_triangular_candidate_theorems(TheoremSpec)


EXPECTED_NAMES=(
    'dirichlet_convolution_entry_first_input_transport',
    'dirichlet_convolution_prefix_first_input_transport',
    'dirichlet_convolution_first_input_append_preserves',
    'dirichlet_convolution_table_first_input_append_preserves',
    'dirichlet_convolution_last_entry_iff',
    'dirichlet_convolution_strict_prefix_exists',
    'dirichlet_convolution_prefix_last_step',
    'dirichlet_convolution_first_input_append_step',
    'dirichlet_convolution_zero_prefix_sum',
    'dirichlet_convolution_at_one_iff',
)
EXPECTED_METRICS=((134,134,72),(98,98,49),(102,102,58),(127,127,58),
                  (105,105,37),(42,42,17),(114,114,45),(139,139,78),
                  (77,77,27),(269,269,43))
ROOT_PINS={
    'dirichlet_convolution_entry_first_input_transport':'ccfb030916a53c893da49a34e7863312d741a87c230c82d3cbe7b7d3f7595afa',
    'dirichlet_convolution_prefix_first_input_transport':'047fbefe0a5cdea7f10bdaaa998a9f417b3199904af737e3dd0ba7268b60204d',
    'dirichlet_convolution_first_input_append_preserves':'369a219d20e5420d0d0b19487e66486737f2c307e075cfa3fe9f5cc95b419532',
    'dirichlet_convolution_table_first_input_append_preserves':'27fae11df162e639c44d92f0a1d1d8559f2b2aa8bc3a44932b597e1c659471ed',
    'dirichlet_convolution_last_entry_iff':'544cbfda04584af20d96f25ecc1a05d1765c03caedef1b7ab36cbc73acc3be6e',
    'dirichlet_convolution_strict_prefix_exists':'745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1',
    'dirichlet_convolution_prefix_last_step':'93424a839115a8b4230c4b0d8eda3c4f00b9b06264c2fb5e6ccb786f96742807',
    'dirichlet_convolution_first_input_append_step':'0acd77c052775df9717c6c09715c733ab207c9fa18380b5e279222221a5f1404',
    'dirichlet_convolution_zero_prefix_sum':'415cc8e3d5dc76c8bd26d3d6bd8a5e88b820b0898d95c7d7c3ec1b7ef81dbab2',
    'dirichlet_convolution_at_one_iff':'6f1888f04b4d2ac46a57cca07719bed191aa2c1e3fc6092ef671965cc8d6b956',
}


def expected_lt(a,b,tag):
    return expected_le(f'S ({a})',b,tag)


def expected_extension(F,H,l,a,tag):
    return _conjoin(expected_table(l,H,tag+'table'),expected_equal(F,H,l,tag+'equal'),
                    expected_at(H,l,a,tag+'last'))


def expected_add(a,b,c,tag):
    return _instantiate(expected_signed_operation('LEFT','RIGHT','RESULT',multiply=False),
                        {'LEFT':a,'RIGHT':b,'RESULT':c},tag)


def contract_data():
    counter=0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter+=1
            return function(*args,tag='triangular_model_'+str(counter))
        return call
    T,A,L,LT,EQ,E,P,C,CT,X,S,M,ADD=tuple(tagged(function) for function in (
        expected_table,expected_at,expected_le,expected_lt,expected_equal,expected_entry,
        expected_prefix,expected_convolution,expected_convolution_table,expected_extension,
        expected_signed_sum,expected_signed_multiply,expected_add))
    endpoint=E('F','G','n','n','z');product=M('a','b','z')
    one=C('F','G','1','z');one_product=M('a','b','z')
    return {
        EXPECTED_NAMES[0]:('F G H N l n d z',(
            T('N','H'),EQ('F','H','l'),L('d','N'),LT('d','l'),E('F','G','n','d','z')),
            E('H','G','n','d','z')),
        EXPECTED_NAMES[1]:('F G H n k l M',(
            T('k','H'),EQ('F','H','l'),LT('k','l'),P('F','G','n','k','M')),
            P('H','G','n','k','M')),
        EXPECTED_NAMES[2]:('F G H l a m z',(
            X('F','H','l','a'),LT('m','l'),C('F','G','m','z')),C('H','G','m','z')),
        EXPECTED_NAMES[3]:('N F G H K a',(
            CT('N','F','G','K'),X('F','H','S N','a')),CT('N','H','G','K')),
        EXPECTED_NAMES[4]:('F G n a b z',('~(n=0)',A('F','n','a'),A('G','1','b')),
            _conjoin(f'({endpoint}) -> ({product})',f'({product}) -> ({endpoint})')),
        EXPECTED_NAMES[5]:('N k F G',(T('N','F'),T('k','G')),
            'exists M r. '+_conjoin(P('G','F','S k','k','M'),S('M','S k','r'))),
        EXPECTED_NAMES[6]:('F G k M r a b y z',(
            P('F','G','S k','k','M'),S('M','S k','r'),A('F','S k','a'),A('G','1','b'),
            M('a','b','y'),ADD('r','y','z')),C('F','G','S k','z')),
        EXPECTED_NAMES[7]:('k G F M r H x u y e',(
            P('G','F','S k','k','M'),S('M','S k','r'),X('G','H','S k','x'),
            A('F','1','u'),M('x','u','y'),ADD('r','y','e')),C('H','F','S k','e')),
        EXPECTED_NAMES[8]:('F G n M',(P('F','G','n','0','M'),),S('M','1','0')),
        EXPECTED_NAMES[9]:('F G a b z',(A('F','1','a'),A('G','1','b')),
            _conjoin(f'({one}) -> ({one_product})',f'({one_product}) -> ({one})')),
    }


def format_contract(names,premises,result):
    return 'forall '+names+'. '+' -> '.join('('+clause+')' for clause in (*premises,result))


def expected_statements():
    return {name:format_contract(*data) for name,data in contract_data().items()}


def test_exact_inventory_original_limits_and_topological_dependencies():
    assert tuple(row.name for row in rows())==EXPECTED_NAMES
    assert len(rows())==10 and sum(len(row.dependencies) for row in rows())==43
    assert sum(len(row.script) for row in rows())==547
    assert sum(n for n,_,_ in EXPECTED_METRICS)==1207
    assert max(d for _,_,d in EXPECTED_METRICS)==78
    assert sha256('\n'.join(row.name for row in rows()).encode()).hexdigest()=='a94e7a4b3092b11afbfe54f8aa358f6065bcd34e1164c4f1094d52976f7cb010'
    assert {row.name:sha256(row.statement.encode()).hexdigest() for row in rows()}==ROOT_PINS
    available=set(core())
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        assert all(re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script))
                   for dep in row.dependencies)
        assert not any(command.startswith(('use ','admit','sorry','DNE','ring')) for command in row.script)
        available.add(row.name)
    assert candidate.__all__==['make_dirichlet_triangular_candidate_theorems']


def test_all_ten_asts_are_novel_against_all_3756_prior_rows():
    from constructive_dirichlet_inverse_support import statement_duplicates
    assert statement_duplicates(rows())==()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_independent_complete_theorem_contract(row):
    assert tuple(expected_statements())==EXPECTED_NAMES
    _assert_same_ast(_closed_formula(row.statement),_closed_formula(expected_statements()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeated','large'))
def test_exact_contextual_instances_do_not_capture_generated_binders(row,mode):
    names,_,_=contract_data()[row.name]
    terms={name:('ambient_a+ambient_b' if i%2 else 'ambient_a*ambient_b')
           for i,name in enumerate(names.split())}
    if mode=='zero':terms={name:'0' for name in terms}
    if mode=='repeated':terms={name:'ambient_b' for name in terms}
    if mode=='large':terms={name:'79228162514264337593543950335' if i==0 else 'ambient_a'
                           for i,name in enumerate(terms)}
    actual_body=row.statement.split('.',1)[1]
    model_body=expected_statements()[row.name].split('.',1)[1]
    actual=_instantiate(actual_body,terms,'actual_context')
    model=_instantiate(model_body,terms,'independent_context')
    close='forall ambient_a ambient_b unused_context. '
    _assert_same_ast(_closed_formula(close+actual),_closed_formula(close+model))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_kernel_body(row):
    try:
        checked=replay_candidate_bodies((row,),core=core()|{item.name:item for item in rows()})[0]
        assert checked.name==row.name
        assert (checked.proof_nodes,checked.proof_objects,checked.proof_depth)==EXPECTED_METRICS[rows().index(row)]
        assert 0<checked.proof_nodes and checked.proof_depth<=256
    except CandidateBodyError as error:
        pytest.fail(str(error),pytrace=False)
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_missing_body_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=core()|{item.name:item for item in rows()})


DEPENDENCIES=tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_dropped_dependency_rejected(row,dependency):
    altered=replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{item.name:item for item in rows()})


@pytest.mark.parametrize('row,dependency',DEPENDENCIES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_poisoned_dependency_rejected(row,dependency):
    table=core()|{item.name:item for item in rows()}
    table[dependency]=replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def hostile_contracts():
    data=contract_data();result=[]
    def changed(index,label,*,remove=None,replace_premise=None,conclusion=None):
        name=EXPECTED_NAMES[index];names,premises,target=data[name];premises=list(premises)
        if remove is not None:premises.pop(remove)
        if replace_premise is not None:
            position,clause=replace_premise;premises[position]=clause
        result.append((label,name,format_contract(names,tuple(premises),conclusion or target)))
    changed(0,'entry_without_actual_target_table',remove=0)
    changed(0,'entry_without_preserved_values',remove=1)
    changed(1,'inclusive_prefix_equality_does_not_cover_endpoint',
            replace_premise=(2,expected_le('k','l','hostile_nonstrict')))
    changed(2,'appended_index_is_not_an_earlier_input',
            replace_premise=(1,expected_le('m','l','hostile_earlier')))
    changed(3,'old_output_is_not_valid_at_new_endpoint',
            conclusion=expected_convolution_table('S N','H','G','K','hostile_output'))
    changed(4,'zero_is_not_a_positive_last_divisor',remove=0)
    changed(4,'endpoint_uses_one_not_n_as_quotient',
            replace_premise=(2,expected_at('G','n','b','hostile_quotient')))
    changed(6,'remainder_length_cannot_omit_index_k',
            replace_premise=(1,expected_signed_sum('M','k','r','hostile_short')))
    changed(6,'last_product_cannot_be_omitted',remove=4)
    changed(6,'signed_add_equation_cannot_be_omitted',remove=5)
    changed(7,'new_input_must_be_a_real_extension',remove=2)
    changed(7,'old_endpoint_is_not_the_strict_remainder',
            replace_premise=(1,expected_signed_sum('M','S(S k)','r','hostile_full')))
    changed(7,'endpoint_multiplier_is_at_one_not_zero',
            replace_premise=(3,expected_at('F','0','u','hostile_zero')))
    changed(8,'unconstrained_next_entry_need_not_sum_to_zero',
            conclusion=expected_signed_sum('M','2','0','hostile_zero_sum'))
    changed(9,'at_one_requires_second_actual_lookup',remove=1)
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',hostile_contracts(),ids=lambda value:value if len(value)<100 else None)
def test_changed_domain_length_product_or_extension_is_rejected(label,name,statement):
    row=next(item for item in rows() if item.name==name)
    assert _closed_formula(statement)!=_closed_formula(row.statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core()|{item.name:item for item in rows()})


def entry_value(first,second,n,d):
    if d==0 or n%d:return 0
    q=n//d
    assert n==d*q
    return decode_signed(model_at(first,d))*decode_signed(model_at(second,q))


def actual_convolution(first,second,n):
    assert n>0
    values=tuple(entry_value(first,second,n,d) for d in range(n+1))
    mask=model_table(values,offset=13,endpoint=997)
    return actual_sum_trace(mask,n+1)


@pytest.mark.parametrize('k',(0,1,2,3,5))
@pytest.mark.parametrize('new_value',(-7,0,11))
def test_actual_beta_append_step_excludes_old_endpoint_and_preserves_earlier_inputs(k,new_value):
    n=k+1
    old_values=(37,*tuple((-1)**i*(i+2) for i in range(1,n)))
    old=model_table(old_values,offset=3,endpoint=101)
    updated=model_table((*old_values,new_value),offset=7,endpoint=-103)
    fixed=model_table((-41,*tuple(3-2*i for i in range(1,n+1))),offset=11,endpoint=107)
    assert old[0]!=updated[0] and old[1]!=updated[1]
    assert decode_signed(model_at(old,n))==101
    assert decode_signed(model_at(updated,n))==new_value
    for d in range(n):assert model_at(old,d)==model_at(updated,d)
    strict_values=tuple(entry_value(old,fixed,n,d) for d in range(n))
    assert strict_values[0]==0 and all(entry_value(updated,fixed,n,d)==strict_values[d] for d in range(n))
    remainder=model_table(strict_values,offset=17,endpoint=109)
    r=decode_signed(actual_sum_trace(remainder,n))
    endpoint=new_value*decode_signed(model_at(fixed,1))
    assert actual_convolution(updated,fixed,n)==encode_signed(r+endpoint)
    assert actual_convolution(old,fixed,n)!=actual_convolution(updated,fixed,n)
    assert decode_signed(actual_sum_trace(remainder,n+1))==r+109
    for m in range(1,n):assert actual_convolution(old,fixed,m)==actual_convolution(updated,fixed,m)
    assert decode_signed(model_at(old,0))==37 and decode_signed(model_at(fixed,0))==-41


@pytest.mark.parametrize('n,k',((0,0),(0,2),(1,0),(4,2),(9,3)))
def test_actual_restricted_prefix_transport_is_independent_of_target_domain(n,k):
    first=model_table(tuple(i-3 for i in range(k+1)),offset=2,endpoint=997)
    updated=model_table(tuple(i-3 for i in range(k+1)),offset=5,endpoint=-991)
    second=model_table((17,2,-3,5,7,11,-13,19,23,29),offset=7,endpoint=31)
    assert first[0]!=updated[0]
    assert tuple(entry_value(first,second,n,d) for d in range(k+1))==tuple(entry_value(updated,second,n,d) for d in range(k+1))
    if n==0 and k:
        assert entry_value(first,second,n,1)==decode_signed(model_at(first,1))*17


@pytest.mark.parametrize('a,b',((-3,7),(-1,-1),(0,9),(1,-8),(2**80+3,-(2**70+5))))
@pytest.mark.parametrize('zero',(-101,0,103))
def test_at_one_is_actual_signed_product_with_unrestricted_input_zero(a,b,zero):
    first=model_table((zero,a),offset=3,endpoint=991)
    second=model_table((zero+17,b),offset=7,endpoint=-997)
    assert entry_value(first,second,1,0)==0
    assert entry_value(first,second,1,1)==a*b
    assert actual_convolution(first,second,1)==encode_signed(a*b)
    assert decode_signed(model_at(first,1))==a and decode_signed(model_at(second,1))==b


def test_strict_bound_and_positive_last_divisor_have_real_counterexamples():
    first=model_table((23,2,3),offset=2,endpoint=17)
    changed=model_table((23,2,7),offset=5,endpoint=-19)
    second=model_table((29,5,11),offset=7,endpoint=31)
    assert all(model_at(first,i)==model_at(changed,i) for i in range(2))
    assert entry_value(first,second,2,2)!=entry_value(changed,second,2,2)
    assert actual_convolution(first,second,2)!=actual_convolution(changed,second,2)
    assert entry_value(first,second,0,0)==0
    assert decode_signed(model_at(first,0))*decode_signed(model_at(second,1))!=0


def test_zero_and_empty_table_domains_are_not_conflated_with_input_one():
    first=model_table((71,),offset=5,endpoint=-13)
    second=model_table((-73,),offset=7,endpoint=17)
    assert all(actual_convolution(first,second,n)==0 for n in range(1,1))
    assert actual_convolution(first,second,1)==encode_signed(-13*17)
    with pytest.raises(AssertionError):actual_convolution(first,second,0)
    assert encode_signed(1)==2 and encode_signed(-1)==1


if __name__=='__main__':
    import argparse,resource,signal,time
    parser=argparse.ArgumentParser()
    parser.add_argument('--body');parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--count',type=int,default=10);parser.add_argument('--pytest-select')
    parser.add_argument('--case-start',type=int,default=0);parser.add_argument('--case-count',type=int)
    args=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180);started=time.monotonic()
    if args.pytest_select is not None:
        plugins=[] if args.case_count is None else [BoundedTestSelection(args.case_start,args.case_count)]
        status=pytest.main(['-q',__file__,'-x','-k',args.pytest_select],plugins=plugins)
    else:
        if args.start<0 or args.count<1:raise SystemExit('invalid body window')
        selected=tuple(row for row in rows() if args.body is None or row.name==args.body)
        selected=selected[args.start:args.start+args.count]
        if not selected:raise SystemExit('empty or unknown body selection')
        for row in selected:
            test_original_kernel_body(row)
            n,o,d=EXPECTED_METRICS[rows().index(row)]
            print(json.dumps({'name':row.name,'nodes':n,'objects':o,'depth':d}),flush=True)
        status=0
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
    raise SystemExit(status)
