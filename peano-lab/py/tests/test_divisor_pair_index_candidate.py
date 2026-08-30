"""Actual beta index-map contracts, finite models, and hostile HA bodies."""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import math
import re

import pytest

from peano_lab.library import divisor_pair_index_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from tests.test_coprime_divisor_decomposition_candidate import core, exact_ast, format_contract, instantiate
from tests.test_divisor_sum_reindex_candidate import _encode_beta


def conjoin(*clauses):
    return clauses[0] if len(clauses) == 1 else f'(({clauses[0]}) /\\ ({conjoin(*clauses[1:])}))'


def expected_lt(a,b,tag):
    h = 'model_index_gap_'+tag
    return f'exists {h}. {h}+S ({a})=({b})'


def expected_beta(r,s,i,z,tag):
    h,q = 'model_beta_gap_'+tag,'model_beta_quotient_'+tag
    modulus = f'S ((S ({i}))*({s}))'
    return conjoin(f'exists {h}. {h}+S ({z})={modulus}',
                   f'exists {q}. ({r})={q}*({modulus})+({z})')


def expected_map(V,L,r,s,tag):
    i,d,e = ('model_pair_'+role+'_'+tag for role in ('index','row','column'))
    return conjoin(f'~(({V})=0)',
                   f'forall {i} {d} {e}. ({expected_lt(i,L,tag+"index")}) -> '
                   f'({expected_lt(e,V,tag+"column")}) -> ({i})=({V})*({d})+({e}) -> '
                   f'({expected_beta(r,s,i,f"({d})*({e})",tag+"product")})')


def expected_preserve(r,s,t,u,L,tag):
    i,z = 'model_preserved_index_'+tag,'model_preserved_value_'+tag
    return (f'forall {i} {z}. ({expected_lt(i,L,tag+"window")}) -> '
            f'({expected_beta(r,s,i,z,tag+"before")}) -> '
            f'({expected_beta(t,u,i,z,tag+"after")})')


@lru_cache(maxsize=1)
def rows():
    return candidate.make_divisor_pair_index_candidate_theorems(TheoremSpec)


NAMES = ('divisor_pair_index_map_append','divisor_pair_index_map_exists',
         'divisor_pair_index_map_lookup','divisor_pair_index_map_value')


def contracts():
    return {
        NAMES[0]:('V L r s',(expected_map('V','L','r','s','append_input'),),
                  'exists t u. '+conjoin(expected_map('V','S L','t','u','append_output'),
                                         expected_preserve('r','s','t','u','L','append_preserve'))),
        NAMES[1]:('V L',('~(V=0)',),'exists r s. '+expected_map('V','L','r','s','exists_map')),
        NAMES[2]:('V L r s i d e',(expected_map('V','L','r','s','lookup_map'),
                  expected_lt('i','L','lookup_index'),expected_lt('e','V','lookup_remainder'),'i=V*d+e'),
                  expected_beta('r','s','i','d*e','lookup_value')),
        NAMES[3]:('V L r s i d e z',(expected_map('V','L','r','s','value_map'),
                  expected_lt('i','L','value_index'),expected_lt('e','V','value_remainder'),'i=V*d+e',
                  expected_beta('r','s','i','z','value_decoded')),'z=d*e'),
    }


def test_exact_topology_without_aliases_or_unused_dependencies():
    assert tuple(row.name for row in rows()) == NAMES
    assert sum(len(row.dependencies) for row in rows()) == 8
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert all(any(re.search(r'\b'+re.escape(dep)+r'\b',cmd) for cmd in row.script) for dep in row.dependencies)
        assert not any(cmd.startswith(('use ','admit','sorry','DNE','ring')) for cmd in row.script)
        available.add(row.name)
    assert candidate.__all__ == ['divisor_pair_index_map_relation','make_divisor_pair_index_candidate_theorems']


def test_exact_3796_prior_and_current_pair_eight_novelty():
    from tests.test_coprime_divisor_decomposition_candidate import rows as divisor_rows
    new = {}
    for row in rows():
        encoded = exact_ast(row.statement)
        key = sha256(encoded.encode()).digest()
        assert all(encoded != other for other in new.get(key,()))
        new.setdefault(key,[]).append(encoded)
    assert len(core()) == 3796 and len(divisor_rows()) == 8
    for row in (*core().values(),*divisor_rows()):
        encoded = exact_ast(row.statement)
        assert all(encoded != other for other in new.get(sha256(encoded.encode()).digest(),())), row.name


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_independent_complete_statement(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contracts()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeat','large'))
def test_compound_and_repeated_contexts(row,mode):
    names = contracts()[row.name][0].split()
    terms = {name:('a+b' if i%2 else 'a*b') for i,name in enumerate(names)}
    if mode == 'zero': terms = dict.fromkeys(terms,'0')
    if mode == 'repeat': terms = dict.fromkeys(terms,'a')
    if mode == 'large': terms = dict.fromkeys(terms,'79228162514264337593543950335')
    actual = instantiate(row.statement.split('.',1)[1],terms,'actual_index')
    expected = instantiate(format_contract(*contracts()[row.name]).split('.',1)[1],terms,'expected_index')
    assert exact_ast('forall a b unused. '+actual) == exact_ast('forall a b unused. '+expected)


@pytest.mark.parametrize('mode',('identifiers','compound','zero','repeat','large'))
def test_public_graph_independent_ast(mode):
    values = ('V','L','r','s')
    if mode == 'compound': values = ('S V','L*V','r+s','S s')
    if mode == 'zero': values = ('0',)*4
    if mode == 'repeat': values = ('V',)*4
    if mode == 'large': values = ('79228162514264337593543950335',*values[1:])
    actual = candidate.divisor_pair_index_map_relation(*values,tag='surface',variables=('V','L','r','s','unused'))
    expected = expected_map(*values,tag='surface_model')
    assert exact_ast('forall V L r s unused. '+actual) == exact_ast('forall V L r s unused. '+expected)


SAMPLE = candidate.divisor_pair_index_map_relation('V','L','r','s',tag='collision',variables=('V','L','r','s'))
BINDERS = tuple(name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',SAMPLE) for name in clause.split())


@pytest.mark.parametrize('binder',BINDERS)
def test_every_unused_generated_binder_collision_rejected(binder):
    with pytest.raises(ValueError):
        candidate.divisor_pair_index_map_relation('V','L','r','s',tag='collision',variables=('V','L','r','s',binder))


@pytest.mark.parametrize('variables',((),['V','L','r','s'],('V','V','L','r','s'),('V','L','r'),('V','L','r','s','bad name')))
def test_bad_context_rejected(variables):
    with pytest.raises(ValueError):
        candidate.divisor_pair_index_map_relation('V','L','r','s',tag='surface',variables=variables)


@pytest.mark.parametrize('tag',('', 'two words', 'exists', '1', 'x.y'))
def test_bad_tag_rejected(tag):
    with pytest.raises(ValueError):
        candidate.divisor_pair_index_map_relation('V','L','r','s',tag=tag,variables=('V','L','r','s'))


@pytest.mark.parametrize('term',('unknown','V+','V -> L','exists x. x=0'))
def test_bad_or_unbound_term_rejected(term):
    with pytest.raises(ValueError):
        candidate.divisor_pair_index_map_relation(term,'L','r','s',tag='surface',variables=('V','L','r','s'))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_actual_original_ha_body(row):
    try:
        receipt = replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert receipt.name == row.name and receipt.dependency_count == len(row.dependencies)
        assert 0 < receipt.proof_objects <= receipt.proof_nodes <= 512 and receipt.proof_depth <= 256
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_absent_body_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=core()|{r.name:r for r in rows()})


EDGES = tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_all_dropped_edges_rejected(row,dependency):
    altered = replace(row,dependencies=tuple(dep for dep in row.dependencies if dep != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_all_poisoned_edges_rejected(row,dependency):
    table = core()|{r.name:r for r in rows()}
    table[dependency] = replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def hostile_contracts():
    result = []
    for index,position,label in ((1,0,'zero_width_not_constructed'),(2,0,'actual_map_required'),
                                (2,1,'outside_window_not_certified'),(2,2,'column_remainder_bound_required'),
                                (2,3,'actual_flattening_equation_required'),(3,4,'actual_beta_lookup_required')):
        names,premises,target = contracts()[NAMES[index]]
        result.append((label,NAMES[index],format_contract(names,tuple(p for i,p in enumerate(premises) if i != position),target)))
    names,premises,_ = contracts()[NAMES[3]]
    result.append(('product_not_sum',NAMES[3],format_contract(names,premises,'z=d+e')))
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',hostile_contracts(),ids=lambda value:value)
def test_hostile_map_or_coordinate_contract_rejected(label,name,statement):
    row = next(row for row in rows() if row.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core()|{r.name:r for r in rows()})


def decoded(r,s,i):
    return r%(1+(i+1)*s)


@pytest.mark.parametrize('V',range(1,7))
@pytest.mark.parametrize('L',(0,1,2,5,9,14))
def test_actual_beta_prefix_construction_and_extension_models(V,L):
    values = tuple((i//V)*(i%V) for i in range(L))
    r,s = _encode_beta(values)
    t,u = _encode_beta((*values,(L//V)*(L%V)))
    for i in range(L):
        d,e = divmod(i,V)
        assert i == V*d+e and e < V
        assert decoded(r,s,i) == decoded(t,u,i) == d*e
    assert decoded(t,u,L) == (L//V)*(L%V)


def test_inactive_map_values_may_collide_and_no_global_permutation_is_claimed():
    V,L = 4,12
    values = tuple((i//V)*(i%V) for i in range(L))
    r,s = _encode_beta(values)
    assert len(set(values)) < L and decoded(r,s,0) == decoded(r,s,4) == 0
    assert 'injective' not in candidate.divisor_pair_index_map_relation.__doc__
    assert values[5] == 1 and values[6] == 2


def test_remainder_bound_and_exact_source_window_are_essential():
    V = 3
    assert V*0+4 == V*1+1 and 0*4 != 1*1  # unbounded alternate remainder
    values = (0,0,0,0,1)
    r,s = _encode_beta((*values,997))
    assert all(decoded(r,s,i) == (i//V)*(i%V) for i in range(5))
    assert decoded(r,s,5) == 997 != (5//V)*(5%V)


def test_no_upper_row_guard_and_unit_width_are_handled_honestly():
    V,L = 2,17
    values = tuple((i//V)*(i%V) for i in range(L))
    assert (15//V) == 7 and values[15] == 7
    r,s = _encode_beta(values)
    assert decoded(r,s,15) == 7
    r,s = _encode_beta((0,)*20)
    assert all(decoded(r,s,i) == 0 == (i//1)*(i%1) for i in range(20))


def test_represented_map_values_do_not_determine_native_beta_codes():
    V,L = 3,8
    values = tuple((i//V)*(i%V) for i in range(L))
    r,s = _encode_beta(values)
    modulus_product = math.prod(1+(i+1)*s for i in range(L))
    different_r = r+modulus_product
    assert different_r != r
    assert tuple(decoded(r,s,i) for i in range(L)) == values
    assert tuple(decoded(different_r,s,i) for i in range(L)) == values
