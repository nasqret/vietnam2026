"""Independent review of the parent's strict finite multiplicativity graph.

Loads the unchanged scratch source as a package-qualified module.  Tests do
not grant any new proof authority to the finite arithmetic diagnostics.
"""

from dataclasses import replace
from functools import lru_cache
import gc
from hashlib import sha256
import importlib.util
import math
from pathlib import Path
import re
import sys

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec
from tests.test_coprime_divisor_decomposition_candidate import (
    core, exact_ast, expected_coprime, format_contract, instantiate,
)
from tests.test_dirichlet_convolution_candidate import (
    expected_at, expected_le, expected_positive_equal, expected_signed_multiply,
    expected_table,
)
from tests.test_divisor_sum_reindex_candidate import _unpair
from tests.test_signed_table_operations_candidate import decode_signed, encode_signed, model_at, model_table


SOURCE = Path(__file__).resolve().parents[1] / 'peano_lab/library/arithmetic_multiplicative_candidate.py'
SOURCE_SHA256 = 'f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e'
assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
MODULE_NAME = 'peano_lab.library._scratch_g009_multiplicative_review'
module_spec = importlib.util.spec_from_file_location(MODULE_NAME,SOURCE)
assert module_spec is not None and module_spec.loader is not None
candidate = importlib.util.module_from_spec(module_spec)
sys.modules[MODULE_NAME] = candidate
module_spec.loader.exec_module(candidate)


def conjoin(*parts):
    return parts[0] if len(parts) == 1 else f'(({parts[0]}) /\\ ({conjoin(*parts[1:])}))'


def expected_law(N,F,tag):
    a,b,x,y,z = ('model_mult_'+role+'_'+tag for role in ('left','right','first','second','product'))
    return (f'forall {a} {b} {x} {y} {z}. ~({a}=0) -> ~({b}=0) -> '
            f'({expected_le(a+"*"+b,N,tag+"bound")}) -> '
            f'({expected_coprime(a,b,tag+"coprime")}) -> '
            f'({expected_at(F,a,x,tag+"first")}) -> ({expected_at(F,b,y,tag+"second")}) -> '
            f'({expected_at(F,a+"*"+b,z,tag+"product")}) -> '
            f'({expected_signed_multiply(x,y,z,tag+"multiply")})')


def expected_multiplicative(N,F,tag):
    return conjoin(f'~(({N})=0)',expected_table(N,F,tag+'table'),
                   expected_at(F,'1','2',tag+'one'),expected_law(N,F,tag+'law'))


@lru_cache(maxsize=1)
def rows():
    return candidate.make_arithmetic_multiplicative_candidate_theorems(TheoremSpec)


NAMES = (
    'signed_multiplicative_nonempty', 'signed_multiplicative_table',
    'signed_multiplicative_normalized', 'signed_multiplicative_coprime_product',
    'signed_multiplicative_intro', 'signed_multiplicative_zero_excluded',
    'signed_multiplicative_at_one_value', 'signed_multiplicative_restrict',
    'signed_multiplicative_product_values_exist', 'signed_positive_table_entry_transport',
    'signed_multiplicative_positive_extensional',
)


def contracts():
    counter = 0
    def tagged(function):
        def call(*args):
            nonlocal counter
            counter += 1
            return function(*args,tag='independent_multiplicative_'+str(counter))
        return call
    M,T,A,L,C,P,Q,E = map(tagged,(expected_multiplicative,expected_table,expected_at,expected_le,
                                 expected_coprime,expected_signed_multiply,expected_law,expected_positive_equal))
    return {
        NAMES[0]:('N F',(M('N','F'),),'~(N=0)'),
        NAMES[1]:('N F',(M('N','F'),),T('N','F')),
        NAMES[2]:('N F',(M('N','F'),),A('F','1','2')),
        NAMES[3]:('N F',(M('N','F'),),Q('N','F')),
        NAMES[4]:('N F',('~(N=0)',T('N','F'),A('F','1','2'),Q('N','F')),M('N','F')),
        NAMES[5]:('F',(),f'~({M("0","F")})'),
        NAMES[6]:('N F z',(M('N','F'),A('F','1','z')),'z=2'),
        NAMES[7]:('N K F',(M('N','F'),'~(K=0)',L('K','N')),M('K','F')),
        NAMES[8]:('N F a b',(M('N','F'),'~(a=0)','~(b=0)',L('a*b','N'),C('a','b')),
                  'exists x y z. '+conjoin(A('F','a','x'),A('F','b','y'),A('F','a*b','z'),P('x','y','z'))),
        NAMES[9]:('N F G i z',(T('N','G'),E('F','G','N'),'~(i=0)',L('i','N'),A('F','i','z')),
                  A('G','i','z')),
        NAMES[10]:('N F G',(M('N','F'),T('N','G'),E('F','G','N')),M('N','G')),
    }


def test_source_immutable_and_exact_topology():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    assert tuple(row.name for row in rows()) == NAMES
    assert sum(len(row.dependencies) for row in rows()) == 12
    available = set(core())
    for row in rows():
        assert row.name not in available
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= available
        assert all(any(re.search(r'\b'+re.escape(dep)+r'\b',cmd) for cmd in row.script) for dep in row.dependencies)
        assert not any(cmd.startswith(('use ','admit','sorry','DNE','ring')) for cmd in row.script)
        available.add(row.name)
    assert candidate.__all__ == ['signed_multiplicative_prefix_relation','make_arithmetic_multiplicative_candidate_theorems']


def test_all_3796_ast_novelty_and_disjoint_current_divisor_pairs():
    from tests.test_coprime_divisor_decomposition_candidate import rows as divisor_rows
    from tests.test_divisor_pair_index_candidate import rows as map_rows
    buckets = {}
    for row in rows():
        encoded = exact_ast(row.statement)
        key = sha256(encoded.encode()).digest()
        assert all(encoded != other for other in buckets.get(key,()))
        buckets.setdefault(key,[]).append(encoded)
    assert len(core()) == 3796
    for row in (*core().values(),*divisor_rows(),*map_rows()):
        encoded = exact_ast(row.statement)
        assert all(encoded != other for other in buckets.get(sha256(encoded.encode()).digest(),())), row.name


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_independent_complete_statement(row):
    assert exact_ast(row.statement) == exact_ast(format_contract(*contracts()[row.name]))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
@pytest.mark.parametrize('mode',('compound','zero','repeat','large'))
def test_compound_quantified_context_instances(row,mode):
    names = contracts()[row.name][0].split()
    terms = {name:('ambient_left+ambient_right' if i%2 else 'ambient_left*ambient_right') for i,name in enumerate(names)}
    if mode == 'zero': terms = dict.fromkeys(terms,'0')
    if mode == 'repeat': terms = dict.fromkeys(terms,'ambient_left')
    if mode == 'large': terms = dict.fromkeys(terms,'79228162514264337593543950335')
    actual = instantiate(row.statement.split('.',1)[1],terms,'actual_mult')
    expected = instantiate(format_contract(*contracts()[row.name]).split('.',1)[1],terms,'expected_mult')
    close = 'forall ambient_left ambient_right unused. '
    assert exact_ast(close+actual) == exact_ast(close+expected)


@pytest.mark.parametrize('mode',('identifiers','compound','zero','repeat','large'))
def test_public_graph_exactly_normalized_nonempty_coprime_prefix(mode):
    values = ('N','F')
    if mode == 'compound': values = ('S (N+1)','F*F+N')
    if mode == 'zero': values = ('0','0')
    if mode == 'repeat': values = ('N','N')
    if mode == 'large': values = ('79228162514264337593543950335','F')
    actual = candidate.signed_multiplicative_prefix_relation(*values,tag='surface',variables=('N','F','unused'))
    expected = expected_multiplicative(*values,tag='surface_model')
    assert exact_ast('forall N F unused. '+actual) == exact_ast('forall N F unused. '+expected)


SAMPLE = candidate.signed_multiplicative_prefix_relation('N','F',tag='collision',variables=('N','F'))
BINDERS = tuple(dict.fromkeys(name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',SAMPLE)
                              for name in clause.split()))


@pytest.mark.parametrize('binder',BINDERS)
def test_all_generated_binder_collisions_including_unused_context_rejected(binder):
    with pytest.raises(ValueError):
        candidate.signed_multiplicative_prefix_relation('N','F',tag='collision',variables=('N','F',binder))


@pytest.mark.parametrize('variables',((),['N','F'],('N','N','F'),('N',),('N','F','bad name')))
def test_bad_context_rejected(variables):
    with pytest.raises(ValueError):
        candidate.signed_multiplicative_prefix_relation('N','F',tag='surface',variables=variables)


@pytest.mark.parametrize('tag',('', 'two words', 'forall', '1', 'x.y'))
def test_bad_tag_rejected(tag):
    with pytest.raises(ValueError):
        candidate.signed_multiplicative_prefix_relation('N','F',tag=tag,variables=('N','F'))


@pytest.mark.parametrize('term',('unknown','N+','N -> F','exists x. x=0'))
def test_bad_term_rejected(term):
    with pytest.raises(ValueError):
        candidate.signed_multiplicative_prefix_relation(term,'F',tag='surface',variables=('N','F'))


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_original_ha_body(row):
    try:
        report = replay_candidate_bodies((row,),core=core()|{r.name:r for r in rows()})[0]
        assert report.name == row.name and report.dependency_count == len(row.dependencies)
        assert 0 < report.proof_objects <= report.proof_nodes <= 512 and report.proof_depth <= 256
    finally:
        gc.collect()


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_false_target_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement='0=1'),),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row',rows(),ids=lambda row:row.name)
def test_empty_body_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=core()|{r.name:r for r in rows()})


EDGES = tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_dropped_dependency_rejected(row,dependency):
    altered = replace(row,dependencies=tuple(dep for dep in row.dependencies if dep != dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((altered,),core=core()|{r.name:r for r in rows()})


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda value:value.name if hasattr(value,'name') else value)
def test_every_poisoned_dependency_rejected(row,dependency):
    table = core()|{r.name:r for r in rows()}
    table[dependency] = replace(table[dependency],statement='0=1')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


def hostile_contracts():
    data,result = contracts(),[]
    for index,position,label in ((4,0,'constructor_requires_nonempty_domain'),(4,1,'constructor_requires_actual_table'),
                                (4,2,'constructor_requires_positive_one'),(4,3,'constructor_requires_real_product_law'),
                                (7,1,'restriction_cannot_be_empty'),(7,2,'restriction_cannot_enlarge_domain'),
                                (8,1,'first_product_input_cannot_be_zero'),(8,2,'second_product_input_cannot_be_zero'),
                                (8,3,'product_must_lie_in_certified_prefix'),(8,4,'law_is_not_complete_multiplicativity'),
                                (9,0,'transport_needs_actual_target_table'),(9,1,'transport_needs_positive_equality'),
                                (9,2,'zero_values_need_not_agree'),(9,3,'outside_prefix_values_need_not_agree'),
                                (10,1,'extensionality_requires_valid_target'),(10,2,'extensionality_requires_positive_equality')):
        names,premises,target = data[NAMES[index]]
        result.append((label,NAMES[index],format_contract(names,tuple(p for i,p in enumerate(premises) if i != position),target)))
    names,premises,target = data[NAMES[4]]
    changed = list(premises)
    changed[2] = expected_at('F','1','1','hostile_negative_one')
    result.append(('negative_one_is_not_normalization',NAMES[4],format_contract(names,tuple(changed),target)))
    names,premises,_ = data[NAMES[6]]
    result.append(('one_value_is_two_not_one',NAMES[6],format_contract(names,premises,'z=1')))
    return tuple(result)


@pytest.mark.parametrize('label,name,statement',hostile_contracts(),ids=lambda value:value)
def test_hostile_guards_normalization_or_target_rejected(label,name,statement):
    row = next(row for row in rows() if row.name == name)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,statement=statement),),core=core()|{r.name:r for r in rows()})


def checked_model(table):
    code,(pb,pc,nb,nc) = table
    outer_positive,outer_negative = _unpair(code)
    assert _unpair(outer_positive) == (pb,pc)
    assert _unpair(outer_negative) == (nb,nc)
    return lambda index:decode_signed(model_at(table,index))


def model_multiplicative(N,table):
    value = checked_model(table)
    if N == 0 or model_at(table,1) != 2:
        return False
    return all(value(a*b) == value(a)*value(b)
               for a in range(1,N+1) for b in range(1,N+1)
               if a*b <= N and math.gcd(a,b) == 1)


def arithmetic_value(kind,n):
    if kind == 'one': return 1
    if kind == 'identity': return n
    if kind == 'delta': return int(n == 1)
    if kind == 'character3': return 0 if n%3 == 0 else (1 if n%3 == 1 else -1)
    raise AssertionError(kind)


@pytest.mark.parametrize('kind',('one','identity','delta','character3'))
@pytest.mark.parametrize('N',(1,2,4,6,12))
@pytest.mark.parametrize('zero',(-7,0,11))
def test_actual_packed_beta_normalized_multiplicative_examples(kind,N,zero):
    values = (zero,*(arithmetic_value(kind,i) for i in range(1,N+1)))
    table = model_table(values,offset=5,endpoint=991)
    value = checked_model(table)
    assert value(0) == zero and model_at(table,1) == 2
    assert model_multiplicative(N,table)
    for K in range(1,N+1):
        assert model_multiplicative(K,table)
    assert not model_multiplicative(0,table)


@pytest.mark.parametrize('kind',('one','identity','delta','character3'))
def test_positive_extensionality_has_no_zero_code_or_outside_prefix_requirement(kind):
    N = 9
    positive = tuple(arithmetic_value(kind,i) for i in range(1,N+1))
    first = model_table((-31,*positive),offset=3,endpoint=997)
    second = model_table((29,*positive),offset=11,endpoint=-991)
    assert first[0] != second[0] and first[1] != second[1]
    assert model_at(first,0) != model_at(second,0)
    assert model_at(first,N+1) != model_at(second,N+1)
    assert all(model_at(first,i) == model_at(second,i) for i in range(1,N+1))
    assert model_multiplicative(N,first) and model_multiplicative(N,second)


def test_positive_one_not_arbitrary_signed_unit_and_no_empty_prefix_vacuity():
    negative_delta = model_table((17,-1,0,0,0),offset=7,endpoint=0)
    assert model_at(negative_delta,1) == 1 and encode_signed(1) == 2
    assert checked_model(negative_delta)(1)**2 != checked_model(negative_delta)(1)
    assert not model_multiplicative(1,negative_delta)
    normalized = model_table((13,1),offset=5,endpoint=0)
    assert model_at(normalized,1) == 2 and not model_multiplicative(0,normalized)


def test_bound_is_inclusive_and_coprime_condition_is_not_complete_multiplicativity():
    boundary_bad = model_table((11,1,2,3,4,5,7),offset=3,endpoint=0)
    assert model_multiplicative(5,boundary_bad)
    assert math.gcd(2,3) == 1 and 2*3 == 6
    assert not model_multiplicative(6,boundary_bad)
    prime_power_arbitrary = model_table((9,1,2,3,3),offset=7,endpoint=0)
    assert model_multiplicative(4,prime_power_arbitrary)
    assert math.gcd(2,2) != 1 and checked_model(prime_power_arbitrary)(4) != checked_model(prime_power_arbitrary)(2)**2


def test_zero_indices_are_excluded_from_the_product_law():
    table = model_table((5,1,2,3,4,5,6),offset=3,endpoint=0)
    value = checked_model(table)
    assert model_multiplicative(6,table)
    assert value(0*2) != value(0)*value(2)


def test_source_still_unchanged_after_all_models():
    assert sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
