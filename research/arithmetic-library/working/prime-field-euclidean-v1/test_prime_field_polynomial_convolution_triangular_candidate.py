"""Independent contracts and real conditional HA for working triangular steps.

The provider table supplies source-derived dependency types only.  None of
these tests is a closed-proof, Lean, admission, or publication receipt.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
import gc
import importlib.util
from pathlib import Path

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.formula_dag import FormulaArena
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula


SOURCE = Path(__file__).with_name('prime_field_polynomial_convolution_triangular_candidate.py')
MODULE_SPEC = importlib.util.spec_from_file_location('working_prime_field_polynomial_convolution_triangular_candidate', SOURCE)
assert MODULE_SPEC is not None and MODULE_SPEC.loader is not None
candidate = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(candidate)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_convolution_triangular_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.finite_sum_theorems import make_finite_sum_theorems
    from peano_lab.library.finite_sum_transport_candidate import make_finite_sum_transport_candidate_theorems
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems

    result = {row.name: row for row in THEOREMS}
    for factory in (make_finite_sum_theorems, make_finite_sum_transport_candidate_theorems,
                    make_prime_field_arithmetic_candidate_theorems,
                    make_prime_field_polynomial_convolution_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def conj(*items):
    result = f'({items[-1]})'
    for item in reversed(items[:-1]):
        result = f'({item}) /\\ ({result})'
    return result


def le(a, b):
    return f'exists ind_le_gap. ind_le_gap+({a})=({b})'


def lt(a, b):
    return f'exists ind_lt_gap. ind_lt_gap+S ({a})=({b})'


def at(b, c, i, a):
    modulus = f'S ((S ({i}))*({c}))'
    return conj(lt(a, modulus), f'exists ind_quotient. ({b})=ind_quotient*({modulus})+({a})')


def equal(b, c, B, C, n):
    return (f'forall ind_equal_i ind_equal_a. ({lt("ind_equal_i",n)}) -> '
            f'({at(b,c,"ind_equal_i","ind_equal_a")}) -> ({at(B,C,"ind_equal_i","ind_equal_a")})')


def pad(b, c, n, i, a):
    return f'({conj(lt(i,n),at(b,c,i,a))}) \\/ ({conj(le(n,i),f"({a})=0")})'


def term(ab, ac, L, bb, bc, M, i, j, t):
    return 'exists ind_complement ind_left ind_right. ' + conj(
        f'({j})+ind_complement=({i})', pad(ab,ac,L,j,'ind_left'),
        pad(bb,bc,M,'ind_complement','ind_right'), f'({t})=ind_left*ind_right')


def diagonal(ab, ac, L, bb, bc, M, i, db, dc, n):
    return f'forall ind_diag_j. ({lt("ind_diag_j",n)}) -> exists ind_diag_t. ' + conj(
        at(db,dc,'ind_diag_j','ind_diag_t'), term(ab,ac,L,bb,bc,M,i,'ind_diag_j','ind_diag_t'))


def finite_sum(b, c, n, r):
    step = f'forall ind_sum_i. ({lt("ind_sum_i",n)}) -> exists ind_sum_a ind_sum_r ind_sum_s. ' + conj(
        at(b,c,'ind_sum_i','ind_sum_a'), at('ind_sum_b','ind_sum_c','ind_sum_i','ind_sum_r'),
        at('ind_sum_b','ind_sum_c','S ind_sum_i','ind_sum_s'), 'ind_sum_s=ind_sum_r+ind_sum_a')
    return 'exists ind_sum_b ind_sum_c. ' + conj(
        at('ind_sum_b','ind_sum_c','0','0'), at('ind_sum_b','ind_sum_c',n,r), step)


def residue(p, n, r):
    return conj(lt(r,p), f'exists ind_mod_u ind_mod_v. ({n})+({p})*ind_mod_u=({r})+({p})*ind_mod_v')


def multiply(p, a, b, r):
    return conj(lt(a,p),lt(b,p),residue(p,f'({a})*({b})',r))


def add(p, a, b, r):
    return conj(lt(a,p),lt(b,p),residue(p,f'({a})+({b})',r))


def coefficient(p, ab, ac, L, bb, bc, M, i, r):
    return 'exists ind_coeff_db ind_coeff_dc ind_coeff_sum. ' + conj(
        diagonal(ab,ac,L,bb,bc,M,i,'ind_coeff_db','ind_coeff_dc',f'S ({i})'),
        finite_sum('ind_coeff_db','ind_coeff_dc',f'S ({i})','ind_coeff_sum'),
        residue(p,'ind_coeff_sum',r))


def format_contract(names, premises, result):
    return f'forall {names}. ' + ''.join(f'({item}) -> ' for item in premises) + f'({result})'


def contracts():
    common = ('ab ac L AB AC K bb bc M N', (le('N','L'),le('N','K'),equal('ab','ac','AB','AC','N')))
    return (
        (common[0]+' i j t', (*common[1],lt('j','N'),term('ab','ac','L','bb','bc','M','i','j','t')),
         term('AB','AC','K','bb','bc','M','i','j','t')),
        (common[0]+' i db dc', (*common[1],diagonal('ab','ac','L','bb','bc','M','i','db','dc','N')),
         diagonal('AB','AC','K','bb','bc','M','i','db','dc','N')),
        ('p '+common[0]+' i r', (*common[1],lt('i','N'),coefficient('p','ab','ac','L','bb','bc','M','i','r')),
         coefficient('p','AB','AC','K','bb','bc','M','i','r')),
        ('p ab ac AB AC bb bc M N i r', (equal('ab','ac','AB','AC','N'),lt('i','N'),
          coefficient('p','ab','ac','N','bb','bc','M','i','r')),
         coefficient('p','AB','AC','S N','bb','bc','M','i','r')),
        ('ab ac bb bc M N t', (term('ab','ac','N','bb','bc','M','N','N','t'),), 't=0'),
        ('ab ac bb bc d N a b t', (at('ab','ac','N','a'),at('bb','bc','0','b'),
          term('ab','ac','S N','bb','bc','S d','N','N','t')), 't=a*b'),
        ('ab ac AB AC bb bc d N a b db dc eb ec u v',
         (equal('ab','ac','AB','AC','N'),at('AB','AC','N','a'),at('bb','bc','0','b'),
          diagonal('ab','ac','N','bb','bc','S d','N','db','dc','S N'),finite_sum('db','dc','S N','u'),
          diagonal('AB','AC','S N','bb','bc','S d','N','eb','ec','S N'),finite_sum('eb','ec','S N','v')),
         'v=u+a*b'),
        ('p ab ac AB AC bb bc d N a b c t r',
         (equal('ab','ac','AB','AC','N'),at('AB','AC','N','a'),at('bb','bc','0','b'),
          coefficient('p','ab','ac','N','bb','bc','S d','N','c'),
          coefficient('p','AB','AC','S N','bb','bc','S d','N','r'),multiply('p','a','b','t')),
         add('p','c','t','r')),
    )


def exact_ast(source):
    return FormulaArena().freeze(_closed_formula(source)).to_json()


def test_exact_ordered_local_dependency_topology():
    known = set(provider_core())
    assert len(rows()) == len(contracts())
    for row in rows():
        assert row.name not in known
        assert len(row.dependencies) == len(set(row.dependencies))
        assert set(row.dependencies) <= known
        assert row.script
        known.add(row.name)


METRICS=((77,39),(54,42),(81,51),(98,55),(87,40),(128,32),(223,64),(121,59))


@pytest.mark.parametrize('index', range(8))
def test_independently_expanded_contract(index):
    assert exact_ast(rows()[index].statement) == exact_ast(format_contract(*contracts()[index]))


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,), core=body_core())[0]
        assert receipt.name == row.name
        assert receipt.dependency_count == len(row.dependencies)
        assert receipt.command_count == len(row.script)
        assert (receipt.proof_nodes,receipt.proof_depth)==METRICS[rows().index(row)]
        assert 0 < receipt.proof_objects <= receipt.proof_nodes
        assert 0 < receipt.proof_depth <= receipt.proof_nodes
        print(receipt, flush=True)
    finally:
        gc.collect()


@pytest.mark.parametrize('index', range(8))
def test_false_conclusion_is_rejected(index):
    names, premises, _ = contracts()[index]
    changed = replace(rows()[index], statement=format_contract(names,premises,'0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),), core=body_core())


EDGES = tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_each_removed_dependency_is_rejected(row,dependency):
    changed = replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,), core=body_core())


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_each_poisoned_dependency_is_rejected(row,dependency):
    table=body_core()
    table[dependency]=replace(table[dependency],statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)
