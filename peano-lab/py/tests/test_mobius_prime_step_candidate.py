"""Independent definition, boundary, topology and genuine body checks for μ steps."""

from dataclasses import replace
from functools import lru_cache
import gc
import re

import pytest

from peano_lab.library import mobius_prime_step_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.ha_signed_negate_candidate import signed_negate
from peano_lab.library.mobius_value_candidate import _mu
from peano_lab.library.prime_valuation_support_candidate import _dvd, _prime
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_mobius_value_candidate import core as parent, rows as value_rows, _integer_mu


@lru_cache(maxsize=1)
def rows():
    return candidate.make_mobius_prime_step_candidate_theorems(TheoremSpec)


def core():
    return parent() | {r.name:r for r in value_rows()}


EXPECTED = {
    'mobius_squarefree_divisor':(73,30),
    'mobius_prime_squarefree':(88,25),
    'mobius_squarefree_fresh_prime_product':(107,31),
    'mobius_prime_factor_list_append':(74,28),
    'mobius_positive_unit_negates_to_negative_unit':(24,13),
    'alternating_signed_unit_successor_negates':(102,22),
    'mobius_prime_square_value_zero':(53,31),
    'mobius_fresh_prime_negates':(131,32),
}


@pytest.mark.parametrize('row',rows(),ids=lambda r:r.name)
def test_original_kernel_body(row):
    try:
        report = replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth) == EXPECTED[row.name]
        assert report.proof_objects <= report.proof_nodes
    finally:
        gc.collect()


def test_exact_topology_no_missing_or_unused_dependencies():
    available=set(core())
    assert len(rows())==8
    for row in rows():
        assert row.name not in available
        assert len(row.dependencies)==len(set(row.dependencies))
        assert set(row.dependencies)<=available
        for dep in row.dependencies:
            assert re.search(r'(?<![\w\'])'+re.escape(dep)+r'(?![\w\'])','\n'.join(row.script))
        assert all(not line.startswith(('use ','admit','sorry','DNE','ring')) for line in row.script)
        _closed_formula(row.statement)
        available.add(row.name)


def test_signed_negation_is_the_historical_graph_not_an_alias_claim():
    actual=candidate.mobius_signed_negation_relation('a','b',tag='old',variables=('a','b'))
    assert _closed_formula('forall a b. '+actual)==_closed_formula('forall a b. '+signed_negate('a','b',tag='old_exact'))


@pytest.mark.parametrize('a,b',[('a+1','b*b'),('a*a','b+12345678901234567890'),('2','1'),('0','0')])
def test_signed_negation_compound_terms(a,b):
    source=candidate.mobius_signed_negation_relation(a,b,tag='terms',variables=('a','b'))
    expected=(f'exists p n. (((({a})=2*p /\\ n=0) \\/ exists k. ((({a})=2*k+1 /\\ p=0) /\\ n=S k)) /\\ '
              f'((({b})=2*n /\\ p=0) \\/ exists j. ((({b})=2*j+1 /\\ n=0) /\\ p=S j)))')
    assert _closed_formula('forall a b. '+source)==_closed_formula('forall a b. '+expected)


def test_every_nested_signed_binder_is_rejected_from_context():
    source=candidate.mobius_signed_negation_relation('a','b',tag='capture',variables=('a','b'))
    for group in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',source):
        for binder in group.split():
            with pytest.raises(ValueError):
                candidate.mobius_signed_negation_relation('a','b',tag='capture',variables=('a','b',binder))


def _step_statement(*,fresh=True,prime=True):
    guards=(f'({_prime("p","expected")}) -> ' if prime else '')
    guards+=(f'~({_dvd("p","n","expected")}) -> ' if fresh else '')
    return (f'forall p n a b. {guards}({_mu("n","a","expected_left")}) -> '
            f'({_mu("p * n","b","expected_right")}) -> ({signed_negate("a","b",tag="expected_output")})')


def test_prime_step_exact_contract():
    row=next(r for r in rows() if r.name=='mobius_fresh_prime_negates')
    assert _closed_formula(row.statement)==_closed_formula(_step_statement())


@pytest.mark.parametrize('name',tuple(EXPECTED))
def test_poisoned_bodies_rejected(name):
    row=next(r for r in rows() if r.name==name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('guard',('fresh','prime'))
def test_full_prime_step_requires_real_guards(guard):
    row=next(r for r in rows() if r.name=='mobius_fresh_prime_negates')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=_step_statement(**{guard:False})),),core=core() | {r.name:r for r in rows()})


@pytest.mark.parametrize('p,n',[(p,n) for p in (2,3,5,7,11,13) for n in range(1,41) if n%p])
def test_independent_prime_adjoining_semantics_including_zero_values(p,n):
    assert _integer_mu(p*n)==-_integer_mu(n)


def test_guards_matter_in_actual_arithmetic():
    assert _integer_mu(2*2)!=-_integer_mu(2)
    assert _integer_mu(6*1)!=-_integer_mu(1)
    with pytest.raises(ValueError):
        _integer_mu(0)


if __name__=='__main__':
    import argparse
    import json
    import resource
    import signal
    import sys
    import time
    parser=argparse.ArgumentParser()
    parser.add_argument('--body')
    arguments=parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started=time.monotonic()
    selected=tuple(r for r in rows() if arguments.body is None or r.name==arguments.body)
    if not selected:
        raise SystemExit('unknown theorem body')
    for row in selected:
        report=replay_candidate_bodies((row,),core=core() | {r.name:r for r in rows()})[0]
        assert (report.proof_nodes,report.proof_depth)==EXPECTED[row.name]
        print(json.dumps({'name':row.name,'nodes':report.proof_nodes,'depth':report.proof_depth,'objects':report.proof_objects}),flush=True)
        gc.collect()
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert peak<=1536*1024*1024
    print(json.dumps({'body_count':len(selected),'elapsed_seconds':time.monotonic()-started,'peak_rss_bytes':peak}),flush=True)
