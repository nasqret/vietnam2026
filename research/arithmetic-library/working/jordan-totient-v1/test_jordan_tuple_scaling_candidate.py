"""Independent full contracts, decoded beta models, and adverse HA replays."""
from dataclasses import replace
from functools import lru_cache
import importlib.util
from itertools import product
from pathlib import Path

import pytest

from peano_lab.library.finite_division_prefix_candidate import make_finite_division_prefix_candidate_theorems
from peano_lab.library.finite_pointwise_mul_recode_candidate import make_finite_pointwise_mul_recode_candidate_theorems
from peano_lab.library.theorems import TheoremSpec, _closed_formula

HERE = Path(__file__).resolve().parent


def load(name, filename):
    loader = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


base = load('_scaling_independent_models', 'test_jordan_totient_candidate.py')
source = load('_scaling_candidate', 'jordan_tuple_scaling_candidate.py')


def Scale(p,b,c,d,e,k):
    return (f'forall zz_i zz_a zz_z. ({base.Lt("zz_i",k)}) -> '
            f'({base.At(b,c,"zz_i","zz_a")}) -> ({base.At(d,e,"zz_i","zz_z")}) -> '
            f'zz_z=({p})*zz_a')


@lru_cache(None)
def rows():
    return source.make_jordan_tuple_scaling_candidate_theorems(TheoremSpec)


def contracts():
    C,L,B,E,D,A = base.Contract,base.Lt,base.Bounded,base.Equal,base.AllDvd,base.And
    return (
        C('p a A',['~(p=0)',L('a','A')],L('p*a','p*A')),
        C('p a A',[L('p*a','p*A')],L('a','A')),
        C('p b c k',[],'exists d e. '+Scale('p','b','c','d','e','k')),
        C('p b c d e k',[Scale('p','b','c','d','e','k')],D('p','d','e','k')),
        C('p b c d e f g u v k',[Scale('p','b','c','f','g','k'),Scale('p','d','e','u','v','k'),E('b','c','d','e','k')],E('f','g','u','v','k')),
        C('p b c d e f g u v k',['~(p=0)',Scale('p','b','c','f','g','k'),Scale('p','d','e','u','v','k'),E('f','g','u','v','k')],E('b','c','d','e','k')),
        C('p b c k',['~(p=0)',D('p','b','c','k')],'exists d e. '+Scale('p','d','e','b','c','k')),
        C('p A b c d e k',['~(p=0)',B('b','c','k','A'),Scale('p','b','c','d','e','k')],B('d','e','k','p*A')),
        C('p A b c d e k',[B('d','e','k','p*A'),Scale('p','b','c','d','e','k')],B('b','c','k','A')),
        C('p A b c k',['~(p=0)',B('b','c','k','A')],'exists d e. '+A(Scale('p','b','c','d','e','k'),B('d','e','k','p*A'),D('p','d','e','k'))),
        C('p A b c k',['~(p=0)',B('b','c','k','p*A'),D('p','b','c','k')],'exists d e. '+A(Scale('p','d','e','b','c','k'),B('d','e','k','A'))),
    )


@pytest.mark.parametrize('index',range(11))
def test_independent_full_contract_no_supplied_map_or_count(index):
    assert _closed_formula(rows()[index].statement)==_closed_formula(contracts()[index])


@pytest.mark.parametrize('tag',['scaling','renamed','other'])
def test_conservative_definition_alpha_renaming(tag):
    actual=source.tuple_scaling_relation('p','b','c','d','e','k',tag=tag)
    assert _closed_formula('forall p b c d e k. '+actual)==_closed_formula('forall p b c d e k. '+Scale('p','b','c','d','e','k'))


@pytest.mark.parametrize('bad',['jt_index_a','fs_h_a','ff_code','a b','S n','n+1','forall'])
@pytest.mark.parametrize('position',range(6))
def test_public_capture_and_nonidentifier_rejection(position,bad):
    arguments=['p','b','c','d','e','k'];arguments[position]=bad
    with pytest.raises(ValueError):source.tuple_scaling_relation(*arguments,tag='a')


def test_internal_term_capture_rejected():
    with pytest.raises(ValueError):source._scale('jt_index_collision+1','b','c','d','e','k','collision')


@lru_cache(None)
def inherited_core():
    core=dict(base.body_core())
    for row in (make_finite_division_prefix_candidate_theorems(TheoremSpec)
                +make_finite_pointwise_mul_recode_candidate_theorems(TheoremSpec)):
        if row.name in core:
            assert _closed_formula(core[row.name].statement)==_closed_formula(row.statement)
        else:core[row.name]=row
    return core


@lru_cache(None)
def body_core():
    return inherited_core()|{row.name:row for row in rows()}


def test_real_unique_topological_dependencies_and_no_count_change():
    known=dict(inherited_core())
    for row in rows():
        assert row.name not in known
        assert set(row.dependencies)<=known.keys()
        assert len(row.dependencies)==len(set(row.dependencies))
        assert row.script and not any('DNE' in line for line in row.script)
        known[row.name]=row
    assert not any('totient' in row.name or 'count' in row.name for row in rows())


def actual_scale(p,source_pair,target_pair,k):
    return base.decoded(*target_pair,k)==tuple(p*a for a in base.decoded(*source_pair,k))


@pytest.mark.parametrize('p,A,k',[(1,0,0),(2,0,0),(2,0,1),(1,1,3),(2,1,3),(2,3,2),(3,2,2),(4,2,2),(5,2,1)])
def test_actual_box_bijection_and_unique_inverse_under_recoding(p,A,k):
    domain=list(product(range(A),repeat=k))
    divisible=[xs for xs in product(range(p*A),repeat=k) if all(x%p==0 for x in xs)]
    image=[tuple(p*a for a in xs) for xs in domain]
    assert len(set(image))==len(domain)
    assert set(image)==set(divisible)
    for xs,ys in zip(domain,image):
        source1,source2=base.encode(xs),base.encode(xs,2)
        target1,target2=base.encode(ys),base.encode(ys,2)
        assert actual_scale(p,source1,target1,k)
        assert actual_scale(p,source2,target2,k)
        quotient=tuple(y//p for y in base.decoded(*target2,k))
        quotient_pair=base.encode(quotient,3)
        assert actual_scale(p,quotient_pair,target1,k)
        assert quotient==xs
        assert all(a<A for a in quotient)
        assert source1!=source2 and target1!=target2


@pytest.mark.parametrize('p',[0,1,2,3])
def test_scaling_totality_beyond_boxes_including_zero(p):
    for k in range(3):
        for xs in product(range(5),repeat=k):
            ys=tuple(p*a for a in xs)
            assert actual_scale(p,base.encode(xs),base.encode(ys,2),k)


def test_zero_scaling_not_injective_and_positive_bound_hypothesis_necessary():
    assert actual_scale(0,base.encode((0,)),base.encode((0,)),1)
    assert actual_scale(0,base.encode((1,)),base.encode((0,)),1)
    assert (0,)!=(1,)
    assert 0<1 and not 0*0<0*1


def test_divisibility_and_box_bound_cannot_be_dropped():
    assert not any(2*q==3 for q in range(5))
    assert 4%2==0 and not 4//2<2
    assert not actual_scale(2,base.encode((1,)),base.encode((3,)),1)


def test_independent_coordinate_order_model_exhaustively():
    for p,a,A in product(range(7),repeat=3):
        assert not(p!=0 and a<A) or p*a<p*A
        assert not(p*a<p*A) or a<A


@pytest.mark.parametrize('index',range(11))
def test_native_body(index):
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[index]
    receipt=replay_candidate_bodies((row,),core=body_core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


@pytest.mark.parametrize('index',range(11))
def test_native_false_conclusion_rejected(index):
    from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement='0=1'),),core=body_core())


@pytest.mark.parametrize('index,dependency',[(i,d) for i,row in enumerate(rows()) for d in row.dependencies])
def test_native_removed_dependency_rejected(index,dependency):
    from peano_lab.library.candidate_validation import CandidateBodyError,replay_candidate_bodies
    row=rows()[index]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency)),),core=body_core())
