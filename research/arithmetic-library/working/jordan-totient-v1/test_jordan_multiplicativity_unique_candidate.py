"""Independent arbitrary-count contract and actual recoded beta witnesses."""
from dataclasses import replace
from functools import lru_cache
import hashlib
import importlib.util
from pathlib import Path

import pytest
from peano_lab.library.theorems import TheoremSpec,_closed_formula

HERE=Path(__file__).parent


def load(name,path):
    loader=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(loader);loader.loader.exec_module(module)
    return module


old=load('_independent_unique_jordan_tests',HERE/'test_jordan_count_uniqueness_candidate.py')
source=load('_independent_unique_jordan_source',HERE/'jordan_multiplicativity_unique_candidate.py')
base=old.base


@lru_cache(None)
def rows():return source.make_jordan_multiplicativity_unique_candidate_theorems(TheoremSpec)


def test_exact_arbitrary_three_count_contract():
    expected=base.Contract('k a b u v w',
        [base.Cop('a','b'),base.Jordan('k','a','u'),base.Jordan('k','b','v'),base.Jordan('k','a*b','w')],
        'w=u*v')
    assert len(rows())==1
    assert _closed_formula(rows()[0].statement)==_closed_formula(expected)
    assert rows()[0].dependencies==('jordan_totient_coprime_product','jordan_totient_count_unique')


def test_no_new_count_assumption_or_prime_product_claim():
    row=rows()[0]
    assert 'prime product' not in row.summary.lower()
    assert row.script[-2:]==('exact hw','exact hp')
    assert any(c.startswith('have hp :') for c in row.script)
    core=old.core()
    assert set(row.dependencies)<=core.keys()
    assert row.name not in core


def test_frozen_count_source_pin():
    raw=(HERE/'jordan_count_uniqueness_candidate.py').read_bytes()
    assert len(raw)==16706
    assert hashlib.sha256(raw).hexdigest()=='94fc0194d3fd049666a5475ead7606f5d51a17b6e643cea5b90fa01bc18ef575'


@pytest.mark.parametrize('a,b,k',[(1,1,1),(1,3,2),(2,3,1),(2,3,2),(3,4,1)])
def test_actual_three_independent_recoded_enumerations(a,b,k):
    left,right,whole=base.universe(a,k),base.universe(b,k),base.universe(a*b,k)
    L=base.encode_enumeration(left[::-1],2)
    R=base.encode_enumeration(right,3)
    W=base.encode_enumeration(whole[::-1],4)
    assert base.actual_enumeration(k,a,len(left),L)
    assert base.actual_enumeration(k,b,len(right),R)
    assert base.actual_enumeration(k,a*b,len(whole),W)
    assert len(whole)==len(left)*len(right)


def test_non_coprime_counterexample_and_zero_exclusions():
    assert len(base.universe(4,2))!=len(base.universe(2,2))**2
    assert not base.actual_enumeration(0,1,1,base.encode_enumeration([()]))
    assert not base.actual_enumeration(1,0,0,base.encode_enumeration([]))


@lru_cache(None)
def core():return old.core()|{r.name:r for r in rows()}


def test_native_body():
    from peano_lab.library.candidate_validation import replay_candidate_bodies
    row=rows()[0];receipt=replay_candidate_bodies((row,),core=core())[0]
    assert receipt.name==row.name and receipt.command_count==len(row.script)


def test_native_false_conclusion():
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[0],statement='0=1'),),core=core())


@pytest.mark.parametrize('dependency',rows()[0].dependencies)
def test_native_removed_dependency(dependency):
    from peano_lab.library.candidate_validation import replay_candidate_bodies,CandidateBodyError
    row=rows()[0]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,dependencies=tuple(d for d in row.dependencies if d!=dependency)),),core=core())
