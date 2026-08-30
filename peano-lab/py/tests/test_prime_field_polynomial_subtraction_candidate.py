"""Independent aligned-field subtraction contracts and real HA body checks.

Inherited metadata supplies ordinary hypothesis statements only.  Each new
body is checked by the unchanged kernel; no dependency closure, independent
Lean verification or admission is claimed here.  Concrete beta encodings
below are diagnostic examples, not evidence replacing those proof gates.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
import gc
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest

from peano_lab.library import prime_field_arithmetic_candidate as arithmetic
from peano_lab.library import prime_field_polynomial_candidate as polynomial
from peano_lab.library import prime_field_polynomial_subtraction_candidate as candidate
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from tests.test_prime_field_polynomial_candidate import (
    capture_cases, compound_cases, decode_beta, decoded_prefix, encode_beta,
    expected_add, expected_and, expected_at, expected_coeff, expected_equal,
    expected_field_add, expected_lt, expected_prime, expected_repeat, same_ast,
)


ROOT = Path(__file__).resolve().parents[3]
SOURCE_SHA256 = 'd08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b'
NAMES_SHA256 = '4176d56c06c72c75305c5dbc1567d8ee4aff2dc4ef959e68b87f7fbd48a478be'
PARENT_BYTES = 66503303
PARENT_SHA256 = 'ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7'
ARITHMETIC_SHA256 = 'd4c26bad017d8f9fee173935e93d394ff5b14697b20d1f460c8a8c2fd3091d90'
POLYNOMIAL_SHA256 = '644c11d8838a94716aaec3ef2e88645c32fb837e78ed70aa7ae346e3deb79f72'
MAX_RSS_BYTES = 1536*1024*1024
EXPECTED_METRICS = (
    (97,30),(52,28),(27,18),(121,39),(74,28),(44,19),(118,38),(46,26),
    (35,22),(47,23),(37,23),(29,20),(168,46),(109,35),(77,24),(147,45),
    (66,34),(39,24),(39,24),(76,44),(111,62),(83,48),(94,56),(88,37),
    (93,54),(127,54),
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_subtraction_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    """Keep only actual direct hypothesis types; never load/check a proof bundle."""
    needed = {dependency for row in rows() for dependency in row.dependencies}
    raw = (ROOT/'artifacts/peano-library/alpha/catalog-v30.json').read_bytes()
    assert len(raw) == PARENT_BYTES and sha256(raw).hexdigest() == PARENT_SHA256
    document = json.loads(raw)
    assert document['theorem_count'] == document['checked_use_count'] == 3222
    assert document['stable_count'] == 432
    result = {row['name']:TheoremSpec(row['name'],row['statement'],tuple(row['dependencies']),
                                   tuple(row['script']),row['summary'])
              for row in document['theorems'] if row['name'] in needed}
    del document,raw
    gc.collect()
    assert sha256(Path(arithmetic.__file__).read_bytes()).hexdigest() == ARITHMETIC_SHA256
    assert sha256(Path(polynomial.__file__).read_bytes()).hexdigest() == POLYNOMIAL_SHA256
    earlier = (*arithmetic.make_prime_field_arithmetic_candidate_theorems(TheoremSpec),
               *polynomial.make_prime_field_polynomial_candidate_theorems(TheoremSpec))
    for row in (*earlier,*rows()):
        if row.name in needed:
            assert row.name not in result
            result[row.name] = row
    assert set(result) == needed
    return result


def expected_negate(p,ab,ac,rb,rc,length):
    i,a,r = 'ind_neg_index','ind_neg_source','ind_neg_result'
    return f'forall {i}. ({expected_lt(i,length)}) -> exists {a} {r}. '+expected_and(
        expected_at(ab,ac,i,a),expected_at(rb,rc,i,r),expected_field_add(p,a,r,'0'))


def expected_subtract(p,ab,ac,bb,bc,rb,rc,length):
    i,a,b,r = 'ind_sub_index','ind_sub_left','ind_sub_right','ind_sub_result'
    return f'forall {i}. ({expected_lt(i,length)}) -> exists {a} {b} {r}. '+expected_and(
        expected_at(ab,ac,i,a),expected_at(bb,bc,i,b),expected_at(rb,rc,i,r),expected_field_add(p,b,r,a))


PUBLIC_CASES = (
    (candidate.prime_field_polynomial_negate_relation,('p','ab','ac','rb','rc','l'),expected_negate),
    (candidate.prime_field_polynomial_subtract_relation,('p','ab','ac','bb','bc','rb','rc','l'),expected_subtract),
)


def quantified(parameters, hypotheses, conclusion):
    return 'forall '+' '.join(parameters)+'. '+' -> '.join('('+value+')' for value in (*hypotheses,conclusion))


def operation_contracts(kind):
    negate = kind == 'negate'
    codes = (('ab','ac'),('rb','rc')) if negate else (('ab','ac'),('bb','bc'),('rb','rc'))
    graph = expected_negate if negate else expected_subtract
    parameters = ('p',*(value for pair in codes for value in pair),'l')
    values = ('a','r') if negate else ('a','b','r')
    operation = expected_field_add('p','a','r','0') if negate else expected_field_add('p','b','r','a')
    current = graph(*parameters)
    other = graph('p',*(value for pair in (*codes[:-1],('db','dc')) for value in pair),'l')
    renamed = tuple((b.upper(),c.upper()) for b,c in codes)
    stem = 'prime_field_polynomial_'+kind+'_'
    return {
        stem+'empty':quantified(parameters[:-1],(),graph(*parameters[:-1],'0')),
        stem+'exists':quantified(('p',*(value for pair in codes[:-1] for value in pair),'l'),
            (expected_prime('p'),*(expected_coeff('p',b,c,'l') for b,c in codes[:-1])),
            'exists rb rc. ('+current+')'),
        stem+'entry':quantified((*parameters,'i',*values),
            (current,expected_lt('i','l'),*(expected_at(b,c,'i',value) for (b,c),value in zip(codes,values,strict=True))),operation),
        stem+'bounded':quantified(parameters,(current,),expected_and(*(expected_coeff('p',b,c,'l') for b,c in codes))),
        stem+'functional':quantified((*parameters[:-1],'db','dc','l'),(current,other),expected_equal('rb','rc','db','dc','l')),
        stem+'transport':quantified((*parameters[:-1],*(value for pair in renamed for value in pair),'l'),
            (*(expected_equal(b,c,B,C,'l') for (b,c),(B,C) in zip(codes,renamed,strict=True)),current),
            graph('p',*(value for pair in renamed for value in pair),'l')),
    }


PARAMETERS = ('p','ab','ac','bb','bc','rb','rc','l')
SUB = expected_subtract(*PARAMETERS)
NEG = expected_negate('p','ab','ac','rb','rc','l')
CONTRACTS = {
    'prime_field_subtract_exists':quantified(('p','a','b'),(expected_prime('p'),expected_lt('a','p'),expected_lt('b','p')),
        'exists r. ('+expected_field_add('p','b','r','a')+')'),
    'prime_field_subtract_equal_zero':quantified(('p','a','r'),(expected_prime('p'),expected_field_add('p','a','r','a')),'r=0'),
    **operation_contracts('negate'),
    'prime_field_polynomial_negate_involutive':quantified(('p','ab','ac','rb','rc','l'),(NEG,),expected_negate('p','rb','rc','ab','ac','l')),
    'prime_field_polynomial_negate_zero':quantified(('p','b','c','l'),(expected_prime('p'),expected_repeat('b','c','0','l')),expected_negate('p','b','c','b','c','l')),
    'prime_field_polynomial_negate_add_zero':quantified(('p','ab','ac','rb','rc','zb','zc','l'),(NEG,expected_repeat('zb','zc','0','l')),expected_add('p','ab','ac','rb','rc','zb','zc','l')),
    **operation_contracts('subtract'),
    'prime_field_polynomial_subtract_recover_add':quantified(PARAMETERS,(SUB,),expected_add('p','bb','bc','rb','rc','ab','ac','l')),
    'prime_field_polynomial_subtract_from_add':quantified(PARAMETERS,(expected_add('p','bb','bc','rb','rc','ab','ac','l'),),SUB),
    'prime_field_polynomial_subtract_self_zero':quantified(('p','ab','ac','zb','zc','l'),(expected_prime('p'),expected_coeff('p','ab','ac','l'),expected_repeat('zb','zc','0','l')),expected_subtract('p','ab','ac','ab','ac','zb','zc','l')),
    'prime_field_polynomial_subtract_zero_right':quantified(('p','ab','ac','zb','zc','l'),(expected_prime('p'),expected_coeff('p','ab','ac','l'),expected_repeat('zb','zc','0','l')),expected_subtract('p','ab','ac','zb','zc','ab','ac','l')),
    'prime_field_polynomial_subtract_zero_left':quantified(('p','bb','bc','rb','rc','zb','zc','l'),(expected_negate('p','bb','bc','rb','rc','l'),expected_repeat('zb','zc','0','l')),expected_subtract('p','zb','zc','bb','bc','rb','rc','l')),
    'prime_field_polynomial_subtract_equal_entry_zero':quantified((*PARAMETERS,'i','a','r'),(expected_prime('p'),SUB,expected_lt('i','l'),expected_at('ab','ac','i','a'),expected_at('bb','bc','i','a'),expected_at('rb','rc','i','r')),'r=0'),
    'prime_field_polynomial_subtract_equal_zero':quantified(PARAMETERS,(expected_prime('p'),expected_equal('ab','ac','bb','bc','l'),SUB),expected_repeat('rb','rc','0','l')),
    'prime_field_polynomial_subtract_add_cancel':quantified(('p','ab','ac','bb','bc','cb','cc','rb','rc','l'),(expected_add('p','ab','ac','bb','bc','cb','cc','l'),expected_subtract('p','cb','cc','ab','ac','rb','rc','l')),expected_equal('bb','bc','rb','rc','l')),
    'prime_field_polynomial_subtract_common_right_cancel':quantified(('p','ab','ac','bb','bc','cb','cc','rb','rc','l'),(expected_subtract('p','ab','ac','cb','cc','rb','rc','l'),expected_subtract('p','bb','bc','cb','cc','rb','rc','l')),expected_equal('ab','ac','bb','bc','l')),
}


def test_exact_source_inventory_and_actual_dependency_order():
    assert len(rows()) == len(CONTRACTS) == len(EXPECTED_METRICS) == 26
    assert tuple(row.name for row in rows()) == tuple(CONTRACTS)
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest() == SOURCE_SHA256
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest() == NAMES_SHA256
    assert sum(len(row.dependencies) for row in rows()) == 48
    assert sum(len(row.script) for row in rows()) == 1184
    owned = {row.name for row in rows()}
    available = set(core())-owned
    for row in rows():
        assert row.name not in available and set(row.dependencies) <= available
        assert len(set(row.dependencies)) == len(row.dependencies) and row.script
        for dependency in row.dependencies:
            assert re.search(r"(?<![\w'])"+re.escape(dependency)+r"(?![\w'])",'\n'.join(row.script))
        assert not any(command.startswith(('admit','sorry','use ')) or 'DNE' in command for command in row.script)
        available.add(row.name)
    assert candidate._at is polynomial._at and candidate._coeff is polynomial._coeff
    assert candidate._equal is polynomial._equal and candidate._public is arithmetic._public


@pytest.mark.parametrize('name,expected',tuple(CONTRACTS.items()),ids=tuple(CONTRACTS))
def test_every_statement_matches_an_independently_expanded_first_order_contract(name,expected):
    row = next(row for row in rows() if row.name == name)
    same_ast(_closed_formula(row.statement),_closed_formula(expected))


def test_no_statement_duplicates_another_new_statement_or_its_hypothesis_types():
    actual = [_closed_formula(row.statement) for row in rows()]
    assert len(set(actual)) == len(actual)
    inherited = {_closed_formula(row.statement) for name,row in core().items()
                 if name not in {row.name for row in rows()}}
    assert not (set(actual) & inherited)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
def test_public_graphs_are_exact_actual_beta_and_field_relations(builder,args,expected):
    prefix = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(prefix+builder(*args,tag='exact',variables=args)),_closed_formula(prefix+expected(*args)))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC_CASES))
def test_every_public_argument_preserves_compound_and_96bit_numeral_terms(builder,args,expected,index,term):
    values = (*args[:index],term,*args[index+1:])
    prefix = 'forall '+' '.join(args)+'. '
    same_ast(_closed_formula(prefix+builder(*values,tag='compound',variables=args)),_closed_formula(prefix+expected(*values)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_generated_binder_rejects_used_and_unused_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(args[0]+'+'+binder,*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_contexts_fail_closed(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='bad_context',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('undeclared','p -> p','p=0','p; true','',None,7,False))
def test_invalid_terms_fail_closed(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='bad_term',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_tags_fail_closed(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


@pytest.mark.parametrize('index',range(26))
def test_original_ha_body(index):
    receipt = replay_candidate_bodies((rows()[index],),core=core())[0]
    assert (receipt.proof_nodes,receipt.proof_depth) == EXPECTED_METRICS[index]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes
    assert receipt.dependency_count == len(rows()[index].dependencies)
    assert receipt.command_count == len(rows()[index].script)


@pytest.mark.parametrize('index',range(26))
@pytest.mark.parametrize('attack',('false_conclusion','truncated_body'))
def test_false_or_incomplete_original_bodies_are_rejected(index,attack):
    original = rows()[index]
    changed = (replace(original,statement=f'({original.statement}) /\\ false') if attack=='false_conclusion'
               else replace(original,script=original.script[:-1]))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core())


EDGES = tuple((index,position) for index,row in enumerate(rows()) for position in range(len(row.dependencies)))


@pytest.mark.parametrize('index,position',EDGES)
def test_every_declared_dependency_is_required(index,position):
    original = rows()[index]
    changed = replace(original,dependencies=original.dependencies[:position]+original.dependencies[position+1:])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=core())


@pytest.mark.parametrize('index,position',EDGES)
def test_every_poisoned_dependency_statement_is_rejected(index,position):
    original = rows()[index]
    name = original.dependencies[position]
    changed = core() | {name:replace(core()[name],statement='0=0')}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((original,),core=changed)


GUARDS = {
    'left_canonical_bound':('prime_field_polynomial_subtract_exists',
        quantified(('p','ab','ac','bb','bc','l'),(expected_prime('p'),expected_coeff('p','bb','bc','l')),'exists rb rc. ('+SUB+')')),
    'right_canonical_bound':('prime_field_polynomial_subtract_exists',
        quantified(('p','ab','ac','bb','bc','l'),(expected_prime('p'),expected_coeff('p','ab','ac','l')),'exists rb rc. ('+SUB+')')),
    'index_bound':('prime_field_polynomial_subtract_entry',
        quantified((*PARAMETERS,'i','a','b','r'),(SUB,expected_at('ab','ac','i','a'),expected_at('bb','bc','i','b'),expected_at('rb','rc','i','r')),expected_field_add('p','b','r','a'))),
    'subtraction_direction':('prime_field_polynomial_subtract_entry',
        quantified((*PARAMETERS,'i','a','b','r'),(SUB,expected_lt('i','l'),expected_at('ab','ac','i','a'),expected_at('bb','bc','i','b'),expected_at('rb','rc','i','r')),expected_field_add('p','a','r','b'))),
    'raw_code_equality':('prime_field_polynomial_subtract_functional',
        quantified((*PARAMETERS[:-1],'db','dc','l'),(SUB,expected_subtract('p','ab','ac','bb','bc','db','dc','l')),expected_and('rb=db','rc=dc'))),
    'one_is_not_zero':('prime_field_polynomial_subtract_self_zero',
        quantified(('p','ab','ac','zb','zc','l'),(expected_prime('p'),expected_coeff('p','ab','ac','l'),expected_repeat('zb','zc','1','l')),expected_subtract('p','ab','ac','ab','ac','zb','zc','l'))),
    'wrong_addend_recovered':('prime_field_polynomial_subtract_add_cancel',
        quantified(('p','ab','ac','bb','bc','cb','cc','rb','rc','l'),(expected_add('p','ab','ac','bb','bc','cb','cc','l'),expected_subtract('p','cb','cc','ab','ac','rb','rc','l')),expected_equal('ab','ac','rb','rc','l'))),
}


@pytest.mark.parametrize('attack',tuple(GUARDS))
def test_missing_bounds_wrong_direction_and_raw_code_claims_are_rejected(attack):
    name,statement = GUARDS[attack]
    original = next(row for row in rows() if row.name==name)
    assert _closed_formula(original.statement) != _closed_formula(statement)
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(original,statement=statement),),core=core())


def field_add(p,a,b,r):
    return 0 <= a < p and 0 <= b < p and 0 <= r < p and (a+b-r)%p == 0


def model_negate(p,source,result,length):
    return all(field_add(p,decode_beta(source,i),decode_beta(result,i),0) for i in range(length))


def model_subtract(p,left,right,result,length):
    return all(field_add(p,decode_beta(right,i),decode_beta(result,i),decode_beta(left,i)) for i in range(length))


@pytest.mark.parametrize('p',(2,3,5,7,11))
@pytest.mark.parametrize('length',(0,1,2,4,7))
def test_actual_encoded_constructors_boundedness_transport_zero_and_cancellation(p,length):
    a = tuple((3*i+1)%p for i in range(length))
    b = tuple((i*i+2)%p for i in range(length))
    negative = tuple((-value)%p for value in a)
    difference = tuple((x-y)%p for x,y in zip(a,b,strict=True))
    total = tuple((x+y)%p for x,y in zip(a,b,strict=True))
    A,B,N,R,S,Z = map(encode_beta,(a,b,negative,difference,total,(0,)*length))
    assert model_negate(p,A,N,length) and model_negate(p,N,A,length)
    assert model_subtract(p,A,B,R,length)
    assert model_subtract(p,A,A,Z,length) and model_subtract(p,A,Z,A,length)
    assert model_subtract(p,Z,A,N,length)
    assert model_subtract(p,S,A,B,length)
    assert all(0 <= value < p for code in (A,B,N,R,S,Z) for value in decoded_prefix(code,length))
    again = tuple(encode_beta(values,multiplier=3) for values in (a,b,negative,difference))
    assert all(first!=second for first,second in zip((A,B,N,R),again,strict=True))
    assert model_negate(p,again[0],again[2],length)
    assert model_subtract(p,again[0],again[1],again[3],length)
    assert decoded_prefix(R,length) == decoded_prefix(again[3],length)
    assert model_subtract(p,A,B,again[3],length)


def test_characteristic_two_negation_and_subtraction_keep_the_same_alignment():
    a,b = (1,0,1,1),(0,1,1,0)
    A,B = encode_beta(a),encode_beta(b)
    R = encode_beta(tuple((x+y)%2 for x,y in zip(a,b,strict=True)))
    assert model_negate(2,A,A,4)
    assert model_subtract(2,A,B,R,4)
    assert decoded_prefix(R,4) == (1,1,0,1)


@pytest.mark.parametrize('p',(0,1,2,4,17))
def test_empty_prefixes_are_vacuous_for_every_modulus_and_unrelated_encodings(p):
    codes = ((0,0),(123456789,0),(91,17),(1<<96,1<<70))
    for left in codes:
        for right in codes:
            assert model_negate(p,left,right,0)
            for output in codes:
                assert model_subtract(p,left,right,output,0)


@pytest.mark.parametrize('length',(1,2,4))
def test_modulus_zero_cannot_have_a_nonempty_actual_operation(length):
    zero = encode_beta((0,)*length)
    other = encode_beta(tuple(range(length)))
    assert not model_negate(0,zero,zero,length)
    assert not model_subtract(0,zero,zero,zero,length)
    assert not model_subtract(0,other,zero,other,length)


def test_noncanonical_sources_and_wrong_subtraction_direction_have_concrete_counterexamples():
    good,bad = encode_beta((1,)),encode_beta((2,))
    for value in range(2):
        output = encode_beta((value,))
        assert not model_subtract(2,bad,good,output,1)
        assert not model_subtract(2,good,bad,output,1)
    left,right,result = map(encode_beta,((3,),(1,),(2,)))
    assert model_subtract(5,left,right,result,1)
    assert not field_add(5,decode_beta(left,0),decode_beta(result,0),decode_beta(right,0))
    assert model_subtract(5,left,right,result,0)
    assert not model_subtract(5,left,right,encode_beta((3,)),1)


def test_self_subtraction_really_zero_and_equal_leading_coefficients_cancel():
    a,b = (3,1,4),(3,4,0)
    A,B = encode_beta(a),encode_beta(b)
    result = encode_beta(tuple((x-y)%5 for x,y in zip(a,b,strict=True)))
    assert model_subtract(5,A,B,result,3) and decode_beta(result,0)==0
    recoded = encode_beta(a,5)
    assert A!=recoded and model_subtract(5,A,recoded,encode_beta((0,0,0)),3)
    assert not model_subtract(5,A,recoded,encode_beta((1,1,1)),3)


def test_representation_length_and_highest_degree_first_order_are_not_reversed_or_normalized():
    # X^2 - (X+1) in F_5 retains exactly three aligned coefficients.
    left,right = (1,0,0),(0,1,1)
    difference = (1,4,4)
    A,B,R = map(encode_beta,(left,right,difference))
    assert model_subtract(5,A,B,R,3)
    assert not model_subtract(5,A,B,encode_beta(difference[::-1]),3)
    tail = encode_beta((*difference,999))
    assert model_subtract(5,A,B,tail,3)
    assert decode_beta(tail,3)==999
    # The relation is over a declared prefix, not an implicit degree or a
    # uniqueness claim about all coefficients beyond that prefix.
    assert decoded_prefix(R,3)==decoded_prefix(tail,3) and R!=tail


def test_raw_code_functionality_and_wrong_addend_cancellation_are_false():
    a,b = (1,2),(3,4)
    difference = tuple((x-y)%5 for x,y in zip(a,b,strict=True))
    A,B = encode_beta(a),encode_beta(b)
    first,second = encode_beta(difference),encode_beta(difference,7)
    assert model_subtract(5,A,B,first,2) and model_subtract(5,A,B,second,2)
    assert first!=second and decoded_prefix(first,2)==decoded_prefix(second,2)
    total = encode_beta(tuple((x+y)%5 for x,y in zip(a,b,strict=True)))
    assert model_subtract(5,total,A,B,2)
    assert decoded_prefix(A,2)!=decoded_prefix(B,2)


if __name__ == '__main__':
    import argparse
    import resource
    import signal
    import time
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start',type=int,default=0)
    parser.add_argument('--count',type=int,default=26)
    parser.add_argument('--pytest-select')
    parser.add_argument('--case-start',type=int,default=0)
    parser.add_argument('--case-count',type=int)
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)
    started = time.monotonic()
    if args.pytest_select is not None:
        class Window:
            @pytest.hookimpl(trylast=True)
            def pytest_collection_modifyitems(self,items):
                stop = None if args.case_count is None else args.case_start+args.case_count
                selected = items[args.case_start:stop]
                if not selected or args.case_start<0 or args.case_count is not None and args.case_count<=0:
                    raise ValueError('the exact bounded test window is empty or invalid')
                discarded = [item for item in items if item not in selected]
                if discarded: items[0].config.hook.pytest_deselected(items=discarded)
                items[:] = selected
        selection = '' if args.pytest_select == 'all' else args.pytest_select
        status = int(pytest.main(['-q','--tb=short','-p','no:cacheprovider',__file__,'-k',selection],plugins=[Window()]))
    else:
        selected = rows()[args.start:args.start+args.count]
        if args.start<0 or args.count<=0 or not selected:
            raise SystemExit('invalid body window')
        for row in selected:
            receipt = replay_candidate_bodies((row,),core=core())[0]
            assert (receipt.proof_nodes,receipt.proof_depth)==EXPECTED_METRICS[rows().index(row)]
            print(json.dumps(asdict(receipt)),flush=True)
        status = 0
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    elapsed = time.monotonic()-started
    assert peak<=MAX_RSS_BYTES and elapsed<180
    print(json.dumps({'status':status,'seconds':elapsed,'peak_rss_bytes':peak,
                      'cpu_limits':[170,175],'wall_seconds':180}),flush=True)
    raise SystemExit(status)
