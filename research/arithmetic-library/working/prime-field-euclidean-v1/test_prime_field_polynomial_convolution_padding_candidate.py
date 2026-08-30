"""Independent working padding contracts and original conditional HA bodies.

Only direct source-provider hypotheses are loaded.  No current Alpha edition,
closed proof bundle, Lean checker, publication capability or saved receipt is
used.  Successful bodies here do not assert dependency-closed admission.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import gc
import importlib.util
import itertools
import json
import math
from pathlib import Path
import re
import resource
import signal
import sys
import time

STARTED = time.monotonic()
if __name__ == '__main__':
    resource.setrlimit(resource.RLIMIT_CPU,(170,175))
    signal.alarm(180)

import pytest

from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import TheoremSpec


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def load_file(alias, name):
    source = HERE / name
    if alias in sys.modules:
        assert Path(sys.modules[alias].__file__).resolve() == source
        return sys.modules[alias]
    loader = importlib.util.spec_from_file_location(alias, source)
    assert loader is not None and loader.loader is not None
    module = importlib.util.module_from_spec(loader)
    sys.modules[alias] = module
    loader.loader.exec_module(module)
    return module


representation = load_file('peano_lab.library.prime_field_polynomial_representation_candidate',
                           'prime_field_polynomial_representation_candidate.py')
candidate = load_file('working_prime_field_polynomial_convolution_padding_candidate',
                     'prime_field_polynomial_convolution_padding_candidate.py')
independent = load_file('working_padding_independent_triangular_tests',
                       'test_prime_field_polynomial_convolution_triangular_candidate.py')
at, lt, le, conj = independent.at, independent.lt, independent.le, independent.conj
extended, term, diagonal = independent.pad, independent.term, independent.diagonal
finite_sum, coefficient, equal = independent.finite_sum, independent.coefficient, independent.equal
format_contract, exact_ast = independent.format_contract, independent.exact_ast
EXPECTED_NAMES = (
    'polynomial_zero_extended_left_pad_shift',
    'polynomial_zero_extended_left_pad_before',
    'polynomial_left_pad_zero_prefix',
    'polynomial_left_pad_natural_sum_invariant',
    'polynomial_zero_tail_natural_sum_invariant',
    'polynomial_diagonal_term_left_padding_left',
    'polynomial_diagonal_term_left_padding_right',
    'polynomial_diagonal_term_left_padding_zero_left',
    'polynomial_diagonal_term_left_padding_zero_right',
    'polynomial_diagonal_left_padding_left',
    'polynomial_diagonal_left_padding_right',
    'prime_field_convolution_coefficient_left_padding_left',
    'prime_field_convolution_coefficient_left_padding_right',
    'prime_field_convolution_coefficient_before_left_padding_left',
    'prime_field_convolution_coefficient_before_left_padding_right',
    'polynomial_product_length_left_padding_left',
    'polynomial_product_length_left_padding_right',
    'prime_field_polynomial_convolution_left_padding_nonempty_left',
    'prime_field_polynomial_convolution_left_padding_nonempty_right',
    'prime_field_polynomial_convolution_left_padding_equivalent_left',
    'prime_field_polynomial_convolution_left_padding_equivalent_right',
    'prime_field_polynomial_convolution_both_left_paddings_equivalent',
    'prime_field_polynomial_convolution_both_left_paddings_exists',
)
METRICS = ((86,31),(69,32),(46,21),(169,40),(144,34),(99,55),(113,57),
           (57,35),(106,43),(218,53),(238,53),(176,52),(258,56),(124,50),(129,51),
           (121,43),(135,45),(290,57),(290,57),(310,59),(310,59),(118,55),(125,57))
SOURCE_PINS = {
    'prime_field_polynomial_convolution_padding_candidate.py': '2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007',
    'prime_field_polynomial_representation_candidate.py': 'fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a',
    'prime_field_polynomial_convolution_triangular_candidate.py': 'd53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f',
    'prime_field_polynomial_division_candidate.py': 'edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2',
    'prime_field_polynomial_distributivity_candidate.py': 'a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86',
}


def repeat(b, c, a, L):
    return f'forall pad_test_repeat_i. ({lt("pad_test_repeat_i",L)}) -> ({at(b,c,"pad_test_repeat_i",a)})'


def left_pad(b, c, L, t, B, C):
    return conj(repeat(B,C,'0',t),
        f'forall pad_test_i pad_test_a. ({lt("pad_test_i",L)}) -> '
        f'({at(b,c,"pad_test_i","pad_test_a")}) -> ({at(B,C,f"({t})+pad_test_i","pad_test_a")})')


def zero_tail(b, c, L, t):
    return (f'forall pad_test_tail_i. ({lt("pad_test_tail_i",t)}) -> '
            f'({at(b,c,f"({L})+pad_test_tail_i","0")})')


def coeff(p,b,c,L):
    return (f'forall pad_test_coeff_i. ({lt("pad_test_coeff_i",L)}) -> exists pad_test_coeff_a. '+
            conj(at(b,c,'pad_test_coeff_i','pad_test_coeff_a'),lt('pad_test_coeff_a',p)))


def product_length(L,M,N):
    return '('+conj(f'({L})=0 \\/ ({M})=0',f'({N})=0')+') \\/ ('+conj(
        f'~(({L})=0)',f'~(({M})=0)',f'({L})+({M})=S ({N})')+')'


def product(p,ab,ac,L,bb,bc,M,cb,cc,N):
    values=(f'forall pad_test_product_i. ({lt("pad_test_product_i",N)}) -> exists pad_test_product_r. '+
            conj(at(cb,cc,'pad_test_product_i','pad_test_product_r'),
                 coefficient(p,ab,ac,L,bb,bc,M,'pad_test_product_i','pad_test_product_r')))
    return conj(coeff(p,ab,ac,L),coeff(p,bb,bc,M),product_length(L,M,N),values)


def power(b,c,L,k,a):
    return ('(exists pad_test_power_i. '+conj(f'pad_test_power_i+S ({k})=({L})',
                at(b,c,'pad_test_power_i',a))+') \\/ ('+conj(le(L,k),f'({a})=0')+')')


def equivalent(b,c,L,B,C,M):
    return ('forall pad_test_power pad_test_first pad_test_second. ('+
        power(b,c,L,'pad_test_power','pad_test_first')+') -> ('+
        power(B,C,M,'pad_test_power','pad_test_second')+') -> pad_test_first=pad_test_second')


def prime(p):
    return (f'~(({p})=1) /\\ forall pad_test_factor_a pad_test_factor_b. '
            f'({p})=pad_test_factor_a*pad_test_factor_b -> pad_test_factor_a=1 \\/ pad_test_factor_b=1')


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_convolution_padding_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def provider_core():
    from peano_lab.library.finite_repeat_sum_candidate import make_finite_repeat_sum_candidate_theorems
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
    from peano_lab.library.matrix_recursive_determinant_extensional_candidate import make_matrix_recursive_determinant_extensional_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_subtraction_candidate import make_prime_field_polynomial_subtraction_candidate_theorems
    from peano_lab.library.prime_field_polynomial_trim_candidate import make_prime_field_polynomial_trim_candidate_theorems
    result = independent.body_core()
    for factory in (make_finite_repeat_sum_candidate_theorems,
                    make_matrix_rank_finite_coding_candidate_theorems,
                    make_matrix_recursive_determinant_extensional_candidate_theorems,
                    make_prime_field_polynomial_candidate_theorems,
                    make_prime_field_polynomial_subtraction_candidate_theorems,
                    make_prime_field_polynomial_trim_candidate_theorems,
                    representation.make_prime_field_polynomial_representation_candidate_theorems):
        for row in factory(TheoremSpec):
            assert row.name not in result or result[row.name] == row
            result[row.name] = row
    return result


def body_core():
    return provider_core() | {row.name: row for row in rows()}


def contracts():
    result = [
        ('b c L t B C i a', (left_pad('b','c','L','t','B','C'),
                             extended('b','c','L','i','a')), extended('B','C','t+L','t+i','a')),
        ('b c L t B C i', (left_pad('b','c','L','t','B','C'),lt('i','t')),
                            extended('B','C','t+L','i','0')),
        ('b c L t B C', (repeat('b','c','0','L'),left_pad('b','c','L','t','B','C')),
                          repeat('B','C','0','t+L')),
        ('b c B C t L n m', (left_pad('b','c','L','t','B','C'),finite_sum('b','c','L','n'),
                              finite_sum('B','C','t+L','m')), 'm=n'),
        ('b c B C L t n m', (equal('b','c','B','C','L'),zero_tail('B','C','L','t'),
                              finite_sum('b','c','L','n'),finite_sum('B','C','L+t','m')), 'm=n'),
    ]
    for side in ('left','right'):
        padded = ('AB','AC') if side == 'left' else ('BB','BC')
        source = ('ab','ac','L') if side == 'left' else ('bb','bc','M')
        factors = ('AB','AC','t+L','bb','bc','M') if side == 'left' else ('ab','ac','L','BB','BC','t+M')
        result.append((' '.join(('ab','ac','L','bb','bc','M',*padded,'t','i','j','z')),
            (left_pad(*source,'t',*padded),term('ab','ac','L','bb','bc','M','i','j','z')),
            term(*factors,'t+i','t+j' if side=='left' else 'j','z')))
    for side in ('left','right'):
        padded=('AB','AC') if side=='left' else ('BB','BC')
        source=('ab','ac','L') if side=='left' else ('bb','bc','M')
        factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
        result.append((' '.join(('ab','ac','L','bb','bc','M',*padded,'t','i','j','z')),
            (left_pad(*source,'t',*padded),lt('j','t') if side=='left' else lt('i','t+j'),
             term(*factors,'i','j','z')),'z=0'))
    for side in ('left','right'):
        padded=('AB','AC') if side=='left' else ('BB','BC')
        source=('ab','ac','L') if side=='left' else ('bb','bc','M')
        factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
        conclusion=(left_pad('db','dc','S i','t','eb','ec') if side=='left' else
                    conj(equal('db','dc','eb','ec','S i'),zero_tail('eb','ec','S i','t')))
        result.append((' '.join(('ab','ac','L','bb','bc','M',*padded,'t','i','db','dc','eb','ec')),
            (left_pad(*source,'t',*padded),diagonal('ab','ac','L','bb','bc','M','i','db','dc','S i'),
             diagonal(*factors,'t+i','eb','ec','S (t+i)')),conclusion))
    for side in ('left','right'):
        padded=('AB','AC') if side=='left' else ('BB','BC')
        source=('ab','ac','L') if side=='left' else ('bb','bc','M')
        factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
        result.append((' '.join(('p','ab','ac','L','bb','bc','M',*padded,'t','i','r')),
            (left_pad(*source,'t',*padded),coefficient('p','ab','ac','L','bb','bc','M','i','r')),
             coefficient('p',*factors,'t+i','r')))
    for side in ('left','right'):
        padded=('AB','AC') if side=='left' else ('BB','BC')
        source=('ab','ac','L') if side=='left' else ('bb','bc','M')
        factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
        result.append((' '.join(('p','ab','ac','L','bb','bc','M',*padded,'t','i','r')),
            ('~(p=0)',left_pad(*source,'t',*padded),lt('i','t'),coefficient('p',*factors,'i','r')),'r=0'))
    for side in ('left','right'):
        lengths=('t+L','M') if side=='left' else ('L','t+M')
        result.append(('L M N t K',(product_length('L','M','N'),'~(L=0)','~(M=0)',
                                   product_length(*lengths,'K')),'K=t+N'))
    for nonempty in (True,False):
        for side in ('left','right'):
            padded=('AB','AC') if side=='left' else ('BB','BC')
            source=('ab','ac','L') if side=='left' else ('bb','bc','M')
            factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
            premises=('~(p=0)',)+(('~(L=0)','~(M=0)') if nonempty else ())
            premises+=(left_pad(*source,'t',*padded),product('p','ab','ac','L','bb','bc','M','cb','cc','N'),
                       product('p',*factors,'CB','CC','K'))
            conclusion=(conj('K=t+N',left_pad('cb','cc','N','t','CB','CC')) if nonempty else
                        equivalent('cb','cc','N','CB','CC','K'))
            result.append((' '.join(('p','ab','ac','L','bb','bc','M','cb','cc','N',*padded,'t','CB','CC','K')),
                           premises,conclusion))
    names='p ab ac L bb bc M cb cc N AB AC t BB BC s CB CC K'
    pads=(left_pad('ab','ac','L','t','AB','AC'),left_pad('bb','bc','M','s','BB','BC'))
    old=product('p','ab','ac','L','bb','bc','M','cb','cc','N')
    new=product('p','AB','AC','t+L','BB','BC','s+M','CB','CC','K')
    eq=equivalent('cb','cc','N','CB','CC','K')
    result.append((names,('~(p=0)',*pads,old,new),eq))
    result.append((' '.join(names.split()[:-3]),(prime('p'),*pads,old),
                   'exists K CB CC. '+conj(new,eq)))
    return tuple(result)


def test_exact_ordered_dependencies_and_no_duplicate_direct_provider_statements():
    assert tuple(row.name for row in rows())==EXPECTED_NAMES
    assert len(rows())==len(contracts())==len(METRICS)==23
    old=provider_core()
    positions={row.name:index for index,row in enumerate(rows())}
    actual=[]
    for row in rows():
        assert type(row) is TheoremSpec and row.script
        assert len(row.dependencies)==len(set(row.dependencies))
        assert all(dep in old or dep in positions and positions[dep]<positions[row.name]
                   for dep in row.dependencies)
        statement=exact_ast(row.statement)
        assert statement not in actual
        actual.append(statement)
    # This is only the actual direct-provider inventory, not global Alpha novelty.
    for row in old.values():
        assert exact_ast(row.statement) not in actual


@pytest.mark.parametrize('name',tuple(SOURCE_PINS))
def test_actual_new_and_four_immutable_working_sources_match_literal_pins(name):
    assert sha256((HERE/name).read_bytes()).hexdigest()==SOURCE_PINS[name]


def test_working_bridge_never_imports_an_edition_or_claims_code_or_unit_equality():
    assert not any(name.startswith('peano_lab.library.editions') for name in sys.modules)
    source=(HERE/'prime_field_polynomial_convolution_padding_candidate.py').read_text()
    assert 'import editions' not in source and 'normalization' not in '\n'.join(
        line for line in source.splitlines() if line.startswith('from '))
    assert candidate.__all__==['make_prime_field_polynomial_convolution_padding_candidate_theorems']


@pytest.mark.parametrize('index', range(len(rows())))
def test_independently_expanded_contract(index):
    assert exact_ast(rows()[index].statement) == exact_ast(format_contract(*contracts()[index]))


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_original_ha_body(row):
    receipt = replay_candidate_bodies((row,),core=body_core())[0]
    assert receipt.name == row.name and receipt.dependency_count == len(row.dependencies)
    assert receipt.command_count == len(row.script)
    assert (receipt.proof_nodes,receipt.proof_depth)==METRICS[rows().index(row)]
    assert 0 < receipt.proof_objects <= receipt.proof_nodes
    assert 0 < receipt.proof_depth <= receipt.proof_nodes
    print(json.dumps(asdict(receipt),sort_keys=True),flush=True)
    gc.collect()


@pytest.mark.parametrize('index', range(len(rows())))
def test_false_conclusion_is_rejected(index):
    parameters,premises,_ = contracts()[index]
    mutated = replace(rows()[index],statement=format_contract(parameters,premises,'0=1'))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,),core=body_core())


@pytest.mark.parametrize('row', rows(), ids=lambda row: row.name)
def test_missing_body_is_rejected(row):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,script=()),),core=body_core())


EDGES = tuple((row,dependency) for row in rows() for dependency in row.dependencies)


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda item:item.name if hasattr(item,'name') else item)
def test_each_removed_dependency_is_rejected(row,dependency):
    changed = replace(row,dependencies=tuple(name for name in row.dependencies if name!=dependency))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


@pytest.mark.parametrize('row,dependency',EDGES,ids=lambda item:item.name if hasattr(item,'name') else item)
def test_each_poisoned_dependency_is_rejected(row,dependency):
    table = body_core()
    table[dependency] = replace(table[dependency],statement='0=0')
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((row,),core=table)


OMITTED_PREMISES=tuple((index,position) for index,(_,premises,_) in enumerate(contracts())
                      for position in range(len(premises)))


@pytest.mark.parametrize('index,position',OMITTED_PREMISES)
def test_every_removed_actual_graph_or_domain_premise_is_rejected(index,position):
    names,premises,result=contracts()[index]
    changed=replace(rows()[index],statement=format_contract(names,
        tuple(premise for i,premise in enumerate(premises) if i!=position),result))
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((changed,),core=body_core())


def hostile_contracts():
    result=[]
    for index in (17,18,19,20,21):
        names,premises,_=contracts()[index]
        result.append((index,'raw_beta_codes_are_not_equal',format_contract(names,premises,'cb=CB')))
    for index in (17,18):
        names,premises,_=contracts()[index]
        result.append((index,'no_unencoded_output_coefficient',format_contract(names,premises,
            conj('K=t+N',left_pad('cb','cc','S N','t','CB','CC')))))
    for index in (19,20,21):
        names,premises,_=contracts()[index]
        result.append((index,'empty_factors_do_not_obey_the_nonempty_length_law',
                       format_contract(names,premises,'K=t+s+N' if index==21 else 'K=t+N')))
    for index,side in ((11,'left'),(12,'right')):
        factors=('AB','AC','t+L','bb','bc','M') if side=='left' else ('ab','ac','L','BB','BC','t+M')
        names,premises,_=contracts()[index]
        result.append((index,'output_index_must_include_the_padding',
                       format_contract(names,premises,coefficient('p',*factors,'i','r'))))
    for index,side in ((19,'left'),(20,'right')):
        names,premises,result_graph=contracts()[index]
        b,c,L,B,C=('ab','ac','L','AB','AC') if side=='left' else ('bb','bc','M','BB','BC')
        wrong=(premises[0],conj(equal(b,c,B,C,L),zero_tail(B,C,L,'t')),*premises[2:])
        result.append((index,'trailing_zero_padding_is_not_formal_equality',
                       format_contract(names,wrong,result_graph)))
    return tuple(result)


@pytest.mark.parametrize('index,label,statement',hostile_contracts(),
                         ids=lambda value:value if isinstance(value,str) and len(value)<90 else None)
def test_stronger_or_changed_representation_contracts_are_rejected(index,label,statement):
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(rows()[index],statement=statement),),core=body_core())


def encode_beta(values,salt=0):
    """Independent actual CRT witnesses, not a proof-checker simulation."""
    values=tuple(values)
    if not values:
        return salt,1
    scale=math.factorial(len(values))*(max(values)+1)
    code,period=0,1
    for i,value in enumerate(values):
        modulus=1+(i+1)*scale
        assert 0<=value<modulus and math.gcd(period,modulus)==1
        code+=period*((value-code)*pow(period,-1,modulus)%modulus)
        period*=modulus
    return code+salt*period,scale


def beta(code,i):
    return code[0]%(1+(i+1)*code[1])


def actual_sum(values):
    table=encode_beta(values,2)
    trace=encode_beta(tuple(itertools.accumulate(values,initial=0)),3)
    assert beta(trace,0)==0
    for i,value in enumerate(values):
        assert beta(table,i)==value
        assert beta(trace,i+1)==beta(trace,i)+beta(table,i)
    return beta(trace,len(values))


def actual_coefficient(p,A,L,B,M,i):
    assert p>0 and i>=0
    terms=tuple((beta(A,j) if j<L else 0)*(beta(B,i-j) if i-j<M else 0) for j in range(i+1))
    diagonal=encode_beta(terms,5)
    assert all(beta(diagonal,j)==value for j,value in enumerate(terms))
    total=actual_sum(terms)
    residue=total%p
    quotient=(total-residue)//p
    assert 0<=residue<p and total==residue+p*quotient
    return residue,terms,total


def actual_product(p,values_a,values_b,salt=0):
    assert p>0 and all(0<=a<p for a in (*values_a,*values_b))
    A=encode_beta((*values_a,p+7,p+11),salt)
    B=encode_beta((*values_b,p+13,p+17),salt+1)
    L,M=len(values_a),len(values_b)
    N=L+M-1 if L and M else 0
    values=tuple(actual_coefficient(p,A,L,B,M,i)[0] for i in range(N))
    C=encode_beta((*values,p+19,p+23),salt+2)
    assert all(beta(C,i)==value for i,value in enumerate(values))
    assert beta(A,L)>=p and beta(B,M)>=p and beta(C,N)>=p
    return A,B,C,values


def model_power(code,length,k):
    return beta(code,length-1-k) if k<length else 0


NATURAL_MODELS=tuple((values,t,salt) for values in ((),(0,),(1,2),(0,7,0),(13,2,19))
                     for t in (0,1,3) for salt in (0,4))


@pytest.mark.parametrize('values,t,salt',NATURAL_MODELS)
def test_actual_beta_sum_traces_accept_zero_blocks_and_recoding(values,t,salt):
    source=encode_beta((*values,999),salt)
    leading=encode_beta((0,)*t+values+(777,),salt+1)
    trailing=encode_beta(values+(0,)*t+(888,),salt+2)
    assert all(beta(leading,i)==0 for i in range(t))
    assert all(beta(source,i)==beta(leading,t+i)==beta(trailing,i) for i in range(len(values)))
    assert all(beta(trailing,len(values)+i)==0 for i in range(t))
    assert actual_sum(values)==actual_sum((0,)*t+values)==actual_sum(values+(0,)*t)
    assert source!=leading and source!=trailing


PRODUCT_MODELS=tuple((p,A,B,t,s) for p in (1,2,3,5,6) for A,B in (
    ((),()),((),(1%p,0)),((1%p,0),()),((0,),(0,)),
    ((1%p,1%p),(1%p,1%p)),((0,p-1,1%p),(p-1,0)),
) for t,s in ((0,0),(1,0),(0,2),(2,1)))


@pytest.mark.parametrize('p,A,B,t,s',PRODUCT_MODELS)
def test_actual_beta_products_and_antidiagonals_preserve_formal_coefficients(p,A,B,t,s):
    old_a,old_b,old_c,old_values=actual_product(p,A,B,1)
    new_a,new_b,new_c,new_values=actual_product(p,(0,)*t+A,(0,)*s+B,7)
    assert all(beta(new_a,i)==0 for i in range(t))
    assert all(beta(new_b,i)==0 for i in range(s))
    assert all(beta(new_a,t+i)==beta(old_a,i) for i in range(len(A)))
    assert all(beta(new_b,s+i)==beta(old_b,i) for i in range(len(B)))
    for i in range(len(A)+len(B)+3):
        original=actual_coefficient(p,old_a,len(A),old_b,len(B),i)
        padded=actual_coefficient(p,new_a,t+len(A),new_b,s+len(B),t+s+i)
        assert padded[1]==(0,)*t+original[1]+(0,)*s
        assert padded[2]==original[2] and padded[0]==original[0]
    for i in range(t+s):
        assert actual_coefficient(p,new_a,t+len(A),new_b,s+len(B),i)[0]==0
    assert all(model_power(old_c,len(old_values),k)==model_power(new_c,len(new_values),k)
               for k in range(max(len(old_values),len(new_values))+3))
    assert old_c!=new_c
    if A and B:
        assert len(new_values)==t+s+len(old_values)
    else:
        assert all(value==0 for value in new_values)


def test_real_counterexamples_separate_empty_length_right_padding_units_and_evaluation():
    _,_,_,empty=actual_product(2,(),(1,1))
    _,_,_,padded=actual_product(2,(0,0),(1,1))
    assert len(empty)==0 and len(padded)==3 and len(padded)!=2+len(empty)
    _,_,original,_=actual_product(2,(1,),(1,))
    _,_,leading,_=actual_product(2,(0,1),(1,),3)
    _,_,trailing,_=actual_product(2,(1,0),(1,),4)
    assert model_power(original,1,0)==model_power(leading,2,0)==1
    assert model_power(trailing,2,0)==0 and model_power(trailing,2,1)==1
    assert model_power(encode_beta((1,)),1,0)!=model_power(encode_beta((2,)),1,0)
    # X^2+X over F_2 vanishes at both field elements, but is not formally zero.
    example=(1,1,0)
    assert all((x*x+x)%2==0 for x in (0,1))
    assert model_power(encode_beta(example),3,2)==1
    # Empty canonical input at p=0 cannot justify constructing padded zeros.
    assert all(0<=a<0 for a in ())
    assert not all(0<=a<0 for a in (0,))


def _main(arguments):
    if arguments[:1] == ['--bodies']:
        start = int(arguments[1]) if len(arguments)>1 else 0
        count = int(arguments[2]) if len(arguments)>2 else len(rows())
        assert start>=0 and count>0
        chosen=rows()[start:start+count]
        assert len(chosen)==count
        for row in chosen:
            test_original_ha_body(row)
        status=0
    elif arguments[:1] == ['--pytest']:
        class Outcomes:
            def __init__(self):
                self.selected,self.passed,self.bad=[],set(),[]
            def pytest_collection_finish(self,session):
                self.selected=[item.nodeid for item in session.items]
            def pytest_runtest_logreport(self,report):
                if report.when=='call' and report.passed:
                    self.passed.add(report.nodeid)
                if report.failed or report.skipped or hasattr(report,'wasxfail'):
                    self.bad.append(report.nodeid)
        outcomes=Outcomes()
        status=int(pytest.main([str(Path(__file__).resolve()),'-p','no:cacheprovider',*arguments[1:]],plugins=[outcomes]))
        if '--collect-only' not in arguments:
            assert outcomes.selected and len(outcomes.selected)==len(set(outcomes.selected))
            assert not outcomes.bad and outcomes.passed==set(outcomes.selected)
        print(json.dumps({'selected':len(outcomes.selected),'passed':len(outcomes.passed),
            'selected_ids_sha256':sha256(('\n'.join(outcomes.selected)+'\n').encode()).hexdigest()},sort_keys=True),flush=True)
    else:
        raise SystemExit('expected --bodies START COUNT or --pytest PYTEST_ARGUMENTS')
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform!='darwin':
        peak *= 1024
    assert 0 < peak <= 1536*1024*1024 and time.monotonic()-STARTED < 180
    print(json.dumps({'status':status,'seconds':time.monotonic()-STARTED,
        'cpu_seconds':time.process_time(),'peak_rss_bytes':peak,
        'cpu_limits':list(resource.getrlimit(resource.RLIMIT_CPU)),'wall_seconds':180},sort_keys=True),flush=True)
    return status


if __name__ == '__main__':
    raise SystemExit(_main(sys.argv[1:]))
