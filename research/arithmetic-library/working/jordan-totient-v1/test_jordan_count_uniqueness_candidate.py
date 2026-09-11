"""Independent tuple-map contracts/models; native cases require a root lease."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib
import importlib.util
from itertools import product
from pathlib import Path
import sys

import pytest
from peano_lab.library.theorems import TheoremSpec, _closed_formula

HERE=Path(__file__).parent


def load(name,path):
    loader=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    return module


old=load('_independent_jordan_count_prior_tests',HERE/'test_jordan_multiplicativity_candidate.py')
source=load('_independent_jordan_count_source',HERE/'jordan_count_uniqueness_candidate.py')
base=old.base
And,At,Lt,Equal,Bounded,Enum,Jordan=base.And,base.At,base.Lt,base.Equal,base.Bounded,base.Enum,base.Jordan
LEFT=('A','B','C','D');RIGHT=('E','F','G','H');CODES=LEFT+RIGHT


def Entry(A,B,C,D,i,b,c):return And(At(A,B,i,b),At(C,D,i,c))
def Le(a,b):return f'exists qq_gap. qq_gap+({a})=({b})'


def Match(k,A,B,C,D,E,F,G,H,i,j):
    return ('forall qq_b qq_c qq_d qq_e. ('+Entry(A,B,C,D,i,'qq_b','qq_c')+') -> ('+
            Entry(E,F,G,H,j,'qq_d','qq_e')+') -> '+Equal('qq_b','qq_c','qq_d','qq_e',k))


def IndexMap(k,A,B,C,D,E,F,G,H,Z,W,q,v):
    return f'forall qq_i. ({Lt("qq_i",q)}) -> exists qq_j. '+And(
        At(Z,W,'qq_i','qq_j'),Lt('qq_j',v),Match(k,A,B,C,D,E,F,G,H,'qq_i','qq_j'))


def Injective(b,c,length):
    return (f'forall qq_i qq_j qq_a. ({Lt("qq_i",length)}) -> ({Lt("qq_j",length)}) -> '
            f'({At(b,c,"qq_i","qq_a")}) -> ({At(b,c,"qq_j","qq_a")}) -> qq_i=qq_j')


@lru_cache(None)
def rows():return source.make_jordan_count_uniqueness_candidate_theorems(TheoremSpec)


def contracts():
    def C(args,premises,target):return base.Contract(' '.join(args),premises,target)
    enums=(Enum('k','n',*LEFT,'u'),Enum('k','n',*RIGHT,'v'))
    common=('k','n',*LEFT,'u',*RIGHT,'v')
    return (
        C(('k',*CODES,'i','j','b','c','d','e'),
          (Entry(*LEFT,'i','b','c'),Entry(*RIGHT,'j','d','e'),Equal('b','c','d','e','k')),
          Match('k',*CODES,'i','j')),
        C((*common,'i'),(*enums,Lt('i','u')),'exists j. '+And(Lt('j','v'),Match('k',*CODES,'i','j'))),
        C(('k',*CODES,'Z','W','v'),(),IndexMap('k',*CODES,'Z','W','0','v')),
        C(('k',*CODES,'Z','W','q','v','j'),
          (IndexMap('k',*CODES,'Z','W','q','v'),Lt('j','v'),Match('k',*CODES,'q','j')),
          'exists P Q. '+IndexMap('k',*CODES,'P','Q','S q','v')),
        C(('q',*common),(*enums,Le('q','u')),'exists Z W. '+IndexMap('k',*CODES,'Z','W','q','v')),
        C(('k',*CODES,'Z','W','q','v','i','j'),
          (IndexMap('k',*CODES,'Z','W','q','v'),Lt('i','q'),At('Z','W','i','j')),
          And(Lt('j','v'),Match('k',*CODES,'i','j'))),
        C((*common,'Z','W'),(*enums,IndexMap('k',*CODES,'Z','W','u','v')),
          And(Bounded('Z','W','u','v'),Injective('Z','W','u'))),
        C(common,enums,Le('u','v')),
        C(common,enums,'u=v'),
        C(('k','n','u','v'),(Jordan('k','n','u'),Jordan('k','n','v')),'u=v'),
    )


@pytest.mark.parametrize('index',range(10))
def test_independent_full_contract(index):
    assert _closed_formula(rows()[index].statement)==_closed_formula(contracts()[index])


@lru_cache(None)
def inherited_core():
    core=dict(old.core())
    module=importlib.import_module('peano_lab.library.fermat_two_squares_pigeonhole_candidate')
    for row in module.make_fermat_two_squares_pigeonhole_candidate_theorems(TheoremSpec):
        if row.name in core:
            assert row==core[row.name]
        else:core[row.name]=row
    return core


def test_actual_provider_ownership_and_acyclic_dependencies():
    core=dict(inherited_core())
    for row in rows():
        assert row.name not in core
        assert set(row.dependencies)<=core.keys()
        assert len(row.dependencies)==len(set(row.dependencies))
        assert row.script
        core[row.name]=row
    pigeon=core['finite_bounded_into_oversized_not_injective']
    expected=base.Contract('b c l n',[Bounded('b','c','l','n'),Lt('n','l')],'~('+Injective('b','c','l')+')')
    assert _closed_formula(pigeon.statement)==_closed_formula(expected)


@pytest.mark.parametrize('name,size,digest',source.PRIOR_PINS)
def test_frozen_source_pin(name,size,digest):
    raw=(HERE/name).read_bytes()
    assert len(raw)==size and hashlib.sha256(raw).hexdigest()==digest


@pytest.mark.parametrize('tag',['count','renamed_count','with_apostrophe'])
def test_public_map_exact_alpha_hygiene(tag):
    from peano_lab.kernel.formulas import parse_formula_with_names
    args=('k',*CODES,'Z','W','q','v')
    actual=source.tuple_enumeration_index_map_relation(*args,tag=tag)
    assert _closed_formula(base.Contract(' '.join(args),[],actual))==_closed_formula(base.Contract(' '.join(args),[],IndexMap(*args)))
    _,free=parse_formula_with_names(actual)
    assert set(free)==set(args)
    match_args=('k',*CODES,'i','j')
    match=source.tuple_enumeration_position_match_relation(*match_args,tag=tag)
    assert _closed_formula(base.Contract(' '.join(match_args),[],match))==_closed_formula(base.Contract(' '.join(match_args),[],Match(*match_args)))


@pytest.mark.parametrize('bad',['S q','forall','jt_index_count','fs_value','ff_value','',True,None])
def test_public_map_rejects_capture_and_nonvariables(bad):
    with pytest.raises((TypeError,ValueError)):
        source.tuple_enumeration_index_map_relation('k',*CODES,'Z','W',bad,'v',tag='count')


def test_map_requires_real_entries_and_no_cardinality_equation():
    formula=source.tuple_enumeration_index_map_relation('k',*CODES,'Z','W','q','v',tag='definition')
    assert _closed_formula(base.Contract('k '+' '.join(CODES)+' Z W q v',[],formula))==_closed_formula(
        base.Contract('k '+' '.join(CODES)+' Z W q v',[],IndexMap('k',*CODES,'Z','W','q','v')))
    assert _closed_formula(base.Contract('k '+' '.join(CODES)+' Z W q v',[],formula))!=_closed_formula(
        base.Contract('k '+' '.join(CODES)+' Z W q v',[],And(IndexMap('k',*CODES,'Z','W','q','v'),'q=v')))


def test_position_transport_preserves_input_equality_hypothesis():
    script=rows()[0].script
    assert not any(command.startswith('have he :') for command in script)
    assert all(f'have heq_{name} : {name}=a{i}' in script for i,name in enumerate('bcde'))
    assert script[-1]=='exact he'


def tuple_at(outer,index,k):
    A,B,C,D=outer
    return base.decoded(base.decode(A,B,index),base.decode(C,D,index),k)


def enum_model(k,n,length,outer):
    """Actual Enum clauses, without importing Jordan's positive-k restriction."""
    assert n>0
    values=[tuple_at(outer,i,k) for i in range(length)]
    return (all(all(x<n for x in xs) and base.primitive(n,xs) for xs in values)
            and len(set(values))==length and set(values)==set(base.universe(n,k)))


def map_model(k,left,right,code,scale,q,v):
    return all((j:=base.decode(code,scale,i))<v and tuple_at(left,i,k)==tuple_at(right,j,k)
               for i in range(q))


@pytest.mark.parametrize('n,k',[(1,0),(2,0),(1,1),(2,1),(3,1),(4,1),(1,2),(2,2),(3,2)])
def test_actual_recoded_reordered_enumerations_construct_injective_map(n,k):
    values=base.universe(n,k)
    left=base.encode_enumeration(values)
    right=base.encode_enumeration(values[::-1],2)
    assert enum_model(k,n,len(values),left) and enum_model(k,n,len(values),right)
    image=[next(j for j in range(len(values)) if tuple_at(left,i,k)==tuple_at(right,j,k))
           for i in range(len(values))]
    Z,W=base.encode(image)
    assert map_model(k,left,right,Z,W,len(values),len(values))
    actual=[base.decode(Z,W,i) for i in range(len(values))]
    assert len(set(actual))==len(values) and sorted(actual)==list(range(len(values)))
    for q in range(len(values)+1):
        prefix=base.encode(image[:q],2)
        assert map_model(k,left,right,*prefix,q,len(values))
    assert left!=right or not values


@pytest.mark.parametrize('q,v',tuple(product(range(4),repeat=2)))
def test_map_not_count_equality_and_finite_pigeonhole_boundary(q,v):
    if v:
        image=[i%v for i in range(q)]
        code,scale=base.encode(image)
        actual=[base.decode(code,scale,i) for i in range(q)]
        assert all(x<v for x in actual)
        if q>v:assert len(set(actual))<q
        else:assert len(set(actual))==q
    else:
        assert all(base.decode(0,0,i)<v for i in range(q))==(q==0)


def test_empty_length_enum_is_not_a_positive_order_jordan_witness():
    empty=base.encode_enumeration([])
    singleton=base.encode_enumeration([()])
    assert enum_model(0,2,0,empty)
    assert enum_model(0,1,1,singleton)
    assert not enum_model(0,1,0,empty)
    assert not base.actual_enumeration(0,1,1,singleton)
    assert map_model(0,empty,empty,0,0,0,0)
    assert not map_model(0,singleton,empty,0,0,1,0)


def test_duplicate_tuple_in_distinct_raw_codes_does_not_give_injection():
    pairs=[base.encode((1,),factor) for factor in (1,2)]
    assert pairs[0]!=pairs[1]
    left=(*base.encode([p[0] for p in pairs]),*base.encode([p[1] for p in pairs]))
    right=base.encode_enumeration([(1,)],3)
    code,scale=base.encode([0,0])
    assert map_model(1,left,right,code,scale,2,1)
    assert not enum_model(1,2,2,left)
    assert enum_model(1,2,1,right)
    assert base.decode(code,scale,0)==base.decode(code,scale,1)


def test_incomplete_target_and_wrong_index_map_are_rejected():
    values=base.universe(2,2)
    left=base.encode_enumeration(values)
    right=base.encode_enumeration(values[:1],2)
    assert not enum_model(2,2,1,right)
    assert not map_model(2,left,right,*base.encode([0]*len(values)),len(values),1)


@lru_cache(None)
def core():return inherited_core()|{row.name:row for row in rows()}


@pytest.mark.parametrize('index',range(10))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[index]
    receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


@pytest.mark.parametrize('index',range(10))
def test_native_false_conclusion(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement='0=1'),),core=core())


@pytest.mark.parametrize('index,dependency',[(i,d) for i,row in enumerate(rows()) for d in row.dependencies])
def test_native_removed_dependency(index,dependency):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    row=rows()[index]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency)),),core=core())
