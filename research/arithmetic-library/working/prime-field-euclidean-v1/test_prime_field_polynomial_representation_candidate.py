"""Independent working representation tests; no admission or closed replay.

Actual body checks leave the exact declared predecessor statements as
ordinary hypotheses and use the original HA checker.  They do not claim
whole-cone closure, independent Lean verification, or an edition admission.
"""

from __future__ import annotations

from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import resource
import signal
import sys
import time

import pytest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
sys.path.insert(0,str(ROOT/'peano-lab/py/tests'))
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies
from peano_lab.library.theorems import THEOREMS, TheoremSpec, _closed_formula
from test_prime_field_polynomial_candidate import (
    decode_beta, decoded_prefix, encode_beta, expected_and as A, expected_at as At,
    expected_coeff as Coeff, expected_equal as Eq, expected_lt as Lt,
    expected_prime as Prime, expected_repeat as Repeat, expected_add as Add,
    expected_scale as Scale, expected_field_mul as Mul, same_ast,
)
from test_prime_field_polynomial_subtraction_candidate import expected_subtract as Subtract
from test_prime_field_polynomial_trim_candidate import expected_suffix as Suffix, expected_trim as Trim
from test_prime_field_polynomial_convolution_candidate import expected_coefficient as ConvolutionCoefficient, expected_convolution as Convolution


def _load(filename='prime_field_polynomial_representation_candidate.py',alias='_working_prime_field_polynomial_representation'):
    path=HERE/filename
    spec=importlib.util.spec_from_file_location(alias,path)
    assert spec and spec.loader
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module


candidate=_load()
MAX_RSS_BYTES=1536*1024*1024
SOURCE_SHA256='fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a'
EXPECTED_NAMES=(
    'prime_field_polynomial_power_index_bound',
    'prime_field_polynomial_left_pad_index_cases',
    'prime_field_polynomial_power_index_before_padding',
    'prime_field_polynomial_power_coefficient_exists',
    'prime_field_polynomial_power_coefficient_functional',
    'prime_field_polynomial_power_coefficient_transport',
    'prime_field_polynomial_equivalent_symmetric',
    'prime_field_polynomial_equivalent_transitive',
    'prime_field_polynomial_equal_implies_equivalent',
    'prime_field_polynomial_equivalent_implies_equal_same_length',
    'prime_field_polynomial_left_pad_zero',
    'prime_field_polynomial_left_pad_exists',
    'prime_field_polynomial_left_pad_entry',
    'prime_field_polynomial_left_pad_bounded',
    'prime_field_polynomial_left_pad_functional',
    'prime_field_polynomial_zero_suffix_left_pad',
    'prime_field_polynomial_trim_left_pad',
    'prime_field_polynomial_left_pad_power_coefficient',
    'prime_field_polynomial_left_pad_equivalent',
    'prime_field_polynomial_trim_equivalent',
    'prime_field_polynomial_left_pad_transport',
    'prime_field_polynomial_add_left_pad_transport',
    'prime_field_polynomial_subtract_left_pad_transport',
    'prime_field_polynomial_scale_left_pad_transport',
    'prime_field_polynomial_zero_power_coefficient',
    'prime_field_polynomial_zero_prefix_equivalent_empty',
    'prime_field_polynomial_constant_right_coefficient',
    'prime_field_polynomial_constant_product_to_scale',
    'prime_field_polynomial_scale_to_constant_product',
    'prime_field_polynomial_inverse_scale',
)


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_representation_candidate_theorems(TheoremSpec)


@lru_cache(maxsize=1)
def core():
    from peano_lab.library.matrix_rank_finite_coding_candidate import make_matrix_rank_finite_coding_candidate_theorems
    from peano_lab.library.matrix_recursive_determinant_extensional_candidate import make_matrix_recursive_determinant_extensional_candidate_theorems
    from peano_lab.library.prime_field_arithmetic_candidate import make_prime_field_arithmetic_candidate_theorems
    from peano_lab.library.prime_field_polynomial_candidate import make_prime_field_polynomial_candidate_theorems
    from peano_lab.library.prime_field_polynomial_subtraction_candidate import make_prime_field_polynomial_subtraction_candidate_theorems
    from peano_lab.library.prime_field_polynomial_trim_candidate import make_prime_field_polynomial_trim_candidate_theorems
    from peano_lab.library.prime_field_polynomial_convolution_candidate import make_prime_field_polynomial_convolution_candidate_theorems
    triangular=_load('prime_field_polynomial_convolution_triangular_candidate.py','_working_prime_field_polynomial_triangular_support')
    previous=(*THEOREMS,
        *make_matrix_rank_finite_coding_candidate_theorems(TheoremSpec),
        *make_matrix_recursive_determinant_extensional_candidate_theorems(TheoremSpec),
        *make_prime_field_arithmetic_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_subtraction_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_trim_candidate_theorems(TheoremSpec),
        *make_prime_field_polynomial_convolution_candidate_theorems(TheoremSpec),
        *triangular.make_prime_field_polynomial_convolution_triangular_candidate_theorems(TheoremSpec))
    table={}
    for row in previous:
        assert row.name not in table or table[row.name]==row
        table[row.name]=row
    wanted={dependency for row in rows() for dependency in row.dependencies}-set(EXPECTED_NAMES)
    assert wanted<=table.keys(),sorted(wanted-table.keys())
    return {name:table[name] for name in wanted}|{row.name:row for row in rows()}


def Le(a,b):
    return f'exists independent_representation_gap. independent_representation_gap+({a})=({b})'


def Pad(b,c,L,t,d,e):
    i,a='independent_pad_position','independent_pad_value'
    return A(Repeat(d,e,'0',t),
        f'forall {i} {a}. ({Lt(i,L)}) -> ({At(b,c,i,a)}) -> ({At(d,e,f"({t})+{i}",a)})')


def Power(b,c,L,k,a):
    i='independent_power_position'
    return f'(exists {i}. ({A(f"{i}+S ({k})=({L})",At(b,c,i,a))})) \\/ ({A(Le(L,k),f"({a})=0")})'


def Equivalent(b,c,L,d,e,M):
    k,a,r='independent_power','independent_first','independent_second'
    return f'forall {k} {a} {r}. ({Power(b,c,L,k,a)}) -> ({Power(d,e,M,k,r)}) -> {a}={r}'


def implication(*parts):
    return ' -> '.join(f'({part})' for part in parts)


CONTRACTS={
    'prime_field_polynomial_power_index_bound':f'forall i k L. i+S k=L -> ({Lt("i","L")})',
    'prime_field_polynomial_left_pad_index_cases':f'forall t L i. ({Lt("i","t+L")}) -> ({Lt("i","t")}) \\/ exists j. ({A(Lt("j","L"),"i=t+j")})',
    'prime_field_polynomial_power_index_before_padding':f'forall t L i k. i+S k=t+L -> ({Le("L","k")}) -> ({Lt("i","t")})',
    'prime_field_polynomial_power_coefficient_exists':f'forall b c L k. exists a. ({Power("b","c","L","k","a")})',
    'prime_field_polynomial_power_coefficient_functional':'forall b c L k a r. '+implication(Power('b','c','L','k','a'),Power('b','c','L','k','r'),'a=r'),
    'prime_field_polynomial_power_coefficient_transport':'forall b c d e L k a. '+implication(Eq('b','c','d','e','L'),Power('b','c','L','k','a'),Power('d','e','L','k','a')),
    'prime_field_polynomial_equivalent_symmetric':'forall b c L d e M. '+implication(Equivalent('b','c','L','d','e','M'),Equivalent('d','e','M','b','c','L')),
    'prime_field_polynomial_equivalent_transitive':'forall b c L d e M f g N. '+implication(Equivalent('b','c','L','d','e','M'),Equivalent('d','e','M','f','g','N'),Equivalent('b','c','L','f','g','N')),
    'prime_field_polynomial_equal_implies_equivalent':'forall b c d e L. '+implication(Eq('b','c','d','e','L'),Equivalent('b','c','L','d','e','L')),
    'prime_field_polynomial_equivalent_implies_equal_same_length':'forall b c d e L. '+implication(Equivalent('b','c','L','d','e','L'),Eq('b','c','d','e','L')),
    'prime_field_polynomial_left_pad_zero':f'forall b c L. ({Pad("b","c","L","0","b","c")})',
    'prime_field_polynomial_left_pad_exists':f'forall b c t L. exists d e. ({Pad("b","c","L","t","d","e")})',
    'prime_field_polynomial_left_pad_entry':'forall b c L t d e i a r. '+implication(Pad('b','c','L','t','d','e'),Lt('i','L'),At('b','c','i','a'),At('d','e','t+i','r'),'r=a'),
    'prime_field_polynomial_left_pad_bounded':'forall p b c L t d e. '+implication(Prime('p'),Coeff('p','b','c','L'),Pad('b','c','L','t','d','e'),Coeff('p','d','e','t+L')),
    'prime_field_polynomial_left_pad_functional':'forall b c L t d e f g. '+implication(Pad('b','c','L','t','d','e'),Pad('b','c','L','t','f','g'),Eq('d','e','f','g','t+L')),
    'prime_field_polynomial_zero_suffix_left_pad':'forall b c L t d e. '+implication(Repeat('d','e','0','t'),Suffix('d','e','t','b','c','L'),Pad('b','c','L','t','d','e')),
    'prime_field_polynomial_trim_left_pad':'forall p b c L t d e M. '+implication(Trim('p','b','c','L','t','d','e','M'),Pad('d','e','M','t','b','c')),
    'prime_field_polynomial_left_pad_power_coefficient':'forall b c L t d e k a. '+implication(Pad('b','c','L','t','d','e'),Power('b','c','L','k','a'),Power('d','e','t+L','k','a')),
    'prime_field_polynomial_left_pad_equivalent':'forall b c L t d e. '+implication(Pad('b','c','L','t','d','e'),Equivalent('b','c','L','d','e','t+L')),
    'prime_field_polynomial_trim_equivalent':'forall p b c L t d e M. '+implication(Trim('p','b','c','L','t','d','e','M'),Equivalent('b','c','L','d','e','M')),
    'prime_field_polynomial_left_pad_transport':'forall b c B C L t d e D E. '+implication(Eq('b','c','B','C','L'),Eq('d','e','D','E','t+L'),Pad('b','c','L','t','d','e'),Pad('B','C','L','t','D','E')),
    'prime_field_polynomial_add_left_pad_transport':'forall p ab ac bb bc cb cc L t AB AC BB BC CB CC. '+implication(Prime('p'),Add('p','ab','ac','bb','bc','cb','cc','L'),Pad('ab','ac','L','t','AB','AC'),Pad('bb','bc','L','t','BB','BC'),Pad('cb','cc','L','t','CB','CC'),Add('p','AB','AC','BB','BC','CB','CC','t+L')),
    'prime_field_polynomial_subtract_left_pad_transport':'forall p ab ac bb bc cb cc L t AB AC BB BC CB CC. '+implication(Prime('p'),Subtract('p','ab','ac','bb','bc','cb','cc','L'),Pad('ab','ac','L','t','AB','AC'),Pad('bb','bc','L','t','BB','BC'),Pad('cb','cc','L','t','CB','CC'),Subtract('p','AB','AC','BB','BC','CB','CC','t+L')),
    'prime_field_polynomial_scale_left_pad_transport':'forall p k ab ac bb bc L t AB AC BB BC. '+implication(Prime('p'),Scale('p','k','ab','ac','bb','bc','L'),Pad('ab','ac','L','t','AB','AC'),Pad('bb','bc','L','t','BB','BC'),Scale('p','k','AB','AC','BB','BC','t+L')),
    'prime_field_polynomial_zero_power_coefficient':'forall b c L k a. '+implication(Repeat('b','c','0','L'),Power('b','c','L','k','a'),'a=0'),
    'prime_field_polynomial_zero_prefix_equivalent_empty':'forall b c L. '+implication(Repeat('b','c','0','L'),Equivalent('b','c','L','0','0','0')),
    'prime_field_polynomial_constant_right_coefficient':'forall p ab ac L bb bc k i a r. '+implication(Prime('p'),Coeff('p','ab','ac','L'),Coeff('p','bb','bc','1'),At('bb','bc','0','k'),Lt('i','L'),At('ab','ac','i','a'),ConvolutionCoefficient('p','ab','ac','L','bb','bc','1','i','r'),Mul('p','k','a','r')),
    'prime_field_polynomial_constant_product_to_scale':'forall p k ab ac bb bc cb cc L. '+implication(Prime('p'),At('bb','bc','0','k'),Convolution('p','ab','ac','L','bb','bc','1','cb','cc','L'),Scale('p','k','ab','ac','cb','cc','L')),
    'prime_field_polynomial_scale_to_constant_product':'forall p k ab ac bb bc cb cc L. '+implication(Prime('p'),Coeff('p','bb','bc','1'),At('bb','bc','0','k'),Scale('p','k','ab','ac','cb','cc','L'),Convolution('p','ab','ac','L','bb','bc','1','cb','cc','L')),
    'prime_field_polynomial_inverse_scale':'forall p a k ab ac bb bc L. '+implication(Prime('p'),A('~(a=0)',Mul('p','a','k','1')),Scale('p','k','ab','ac','bb','bc','L'),Scale('p','a','bb','bc','ab','ac','L')),
}


PUBLIC=(
    (candidate.prime_field_polynomial_left_pad_relation,('b','c','L','t','d','e'),Pad),
    (candidate.prime_field_polynomial_power_coefficient_relation,('b','c','L','k','a'),Power),
    (candidate.prime_field_polynomial_equivalent_relation,('b','c','L','d','e','M'),Equivalent),
)


def test_exact_independent_inventory_and_topological_dependency_surface():
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    assert tuple(row.name for row in rows())==EXPECTED_NAMES
    assert set(CONTRACTS)==set(EXPECTED_NAMES)
    assert 'peano_lab.library.editions_v31' not in sys.modules
    assert 'peano_lab.library.editions_v32' not in sys.modules
    assert 'prime_field_polynomial_equivalent_reflexive' not in EXPECTED_NAMES
    same_ast(_closed_formula(core()['prime_field_polynomial_power_coefficient_functional'].statement),
             _closed_formula('forall b c L. '+Equivalent('b','c','L','b','c','L')))
    seen=set(core())-set(EXPECTED_NAMES)
    for row in rows():
        assert type(row) is TheoremSpec and row.name not in seen
        assert len(set(row.dependencies))==len(row.dependencies)
        assert set(row.dependencies)<=seen
        for name in row.dependencies:
            assert re.search(r"(?<![\w'])"+re.escape(name)+r"(?![\w'])",'\n'.join(row.script))
        assert not any(command.startswith(('use ','admit','sorry')) for command in row.script)
        seen.add(row.name)


@pytest.mark.parametrize('name',EXPECTED_NAMES)
def test_each_statement_has_the_exact_independent_closed_ast(name):
    same_ast(_closed_formula(core()[name].statement),_closed_formula(CONTRACTS[name]))


@pytest.mark.parametrize('builder,args,expected',PUBLIC,ids=('left_pad','power_coefficient','formal_equivalence'))
def test_public_relations_match_independent_formulas(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='public',variables=args)),_closed_formula(binder+expected(*args)))


COMPOUNDS=tuple((builder,args,expected,index,term) for builder,args,expected in PUBLIC
    for index in range(len(args)) for term in (f'({args[0]})+S ({args[-1]})',str(2**90+7)))


@pytest.mark.parametrize('builder,args,expected,index,term',COMPOUNDS,ids=tuple(f'compound-{i:03d}' for i in range(len(COMPOUNDS))))
def test_compound_terms_are_capture_free_in_every_argument(builder,args,expected,index,term):
    values=(*args[:index],term,*args[index+1:])
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


CAPTURES=tuple((builder,args,binder) for builder,args,_ in PUBLIC
    for binder in sorted({name for clause in re.findall(r'\b(?:forall|exists)\s+([^.]*)\.',builder(*args,tag='capture',variables=args)) for name in clause.split()}))


@pytest.mark.parametrize('builder,args,binder',CAPTURES,ids=tuple(f'capture-{i:03d}' for i in range(len(CAPTURES))))
def test_all_generated_binders_reject_whole_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=(*args,binder))
    with pytest.raises(ValueError,match='captures'):
        builder(binder,*args[1:],tag='capture',variables=(*args,binder))


@pytest.mark.parametrize('name',EXPECTED_NAMES)
def test_actual_dependency_curried_bodies(name):
    receipt=replay_candidate_bodies((core()[name],),core=core())[0]
    assert receipt.name==name and 0<receipt.proof_objects<=receipt.proof_nodes
    assert receipt.proof_depth<=256


@pytest.mark.parametrize('name',EXPECTED_NAMES)
@pytest.mark.parametrize('kind',('false_conclusion','truncated_body'))
def test_false_conclusions_and_missing_body_endings_are_rejected(name,kind):
    row=core()[name]
    mutant=replace(row,statement=f'({row.statement}) /\\ false') if kind=='false_conclusion' else replace(row,script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutant,),core=core())


EDGES=tuple((row.name,index,name) for row in rows() for index,name in enumerate(row.dependencies))


@pytest.mark.parametrize('name,index,dependency',EDGES,ids=tuple(f'drop-{i:03d}' for i in range(len(EDGES))))
def test_every_declared_dependency_is_needed(name,index,dependency):
    row=core()[name]
    assert row.dependencies[index]==dependency
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(row,dependencies=row.dependencies[:index]+row.dependencies[index+1:]),),core=core())


@pytest.mark.parametrize('name,index,dependency',EDGES,ids=tuple(f'poison-{i:03d}' for i in range(len(EDGES))))
def test_every_dependency_rejects_an_unrelated_true_statement(name,index,dependency):
    assert core()[name].dependencies[index]==dependency
    poisoned=core()|{dependency:replace(core()[dependency],statement='0=0')}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((core()[name],),core=poisoned)


WRONG_CONTRACTS={
    'raw_code_uniqueness':('prime_field_polynomial_left_pad_functional',
        'forall b c L t d e f g. '+implication(Pad('b','c','L','t','d','e'),Pad('b','c','L','t','f','g'),A('d=f','e=g'))),
    'same_length_required':('prime_field_polynomial_equivalent_implies_equal_same_length',
        'forall b c d e L M. '+implication(Equivalent('b','c','L','d','e','M'),Eq('b','c','d','e','L'))),
    'padding_must_be_leading':('prime_field_polynomial_left_pad_equivalent',
        'forall b c L t d e. '+implication(Eq('b','c','d','e','L'),Equivalent('b','c','L','d','e','t+L'))),
    'boundedness_does_not_extend_past_output':('prime_field_polynomial_left_pad_bounded',
        'forall p b c L t d e. '+implication(Prime('p'),Coeff('p','b','c','L'),Pad('b','c','L','t','d','e'),Coeff('p','d','e','S(t+L)'))),
    'constant_factor_must_have_length_one':('prime_field_polynomial_constant_right_coefficient',
        'forall p ab ac L bb bc k i a r. '+implication(Prime('p'),Coeff('p','ab','ac','L'),Coeff('p','bb','bc','2'),At('bb','bc','0','k'),Lt('i','L'),At('ab','ac','i','a'),ConvolutionCoefficient('p','ab','ac','L','bb','bc','2','i','r'),Mul('p','k','a','r'))),
    'coefficient_index_must_be_in_source':('prime_field_polynomial_constant_right_coefficient',
        'forall p ab ac L bb bc k i a r. '+implication(Prime('p'),Coeff('p','ab','ac','L'),Coeff('p','bb','bc','1'),At('bb','bc','0','k'),At('ab','ac','i','a'),ConvolutionCoefficient('p','ab','ac','L','bb','bc','1','i','r'),Mul('p','k','a','r'))),
    'reverse_scalar_requires_actual_inverse':('prime_field_polynomial_inverse_scale',
        'forall p a k ab ac bb bc L. '+implication(Prime('p'),Lt('a','p'),Lt('k','p'),Scale('p','k','ab','ac','bb','bc','L'),Scale('p','a','bb','bc','ab','ac','L'))),
    'empty_product_is_not_constant_one':('prime_field_polynomial_zero_prefix_equivalent_empty',
        'forall b c L. '+implication(Repeat('b','c','0','L'),Equivalent('b','c','L','1','1','1'))),
}


@pytest.mark.parametrize('mutation',tuple(WRONG_CONTRACTS))
def test_original_bodies_reject_false_representation_and_algebra_guards(mutation):
    name,statement=WRONG_CONTRACTS[mutation]
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((replace(core()[name],statement=statement),),core=core())


def test_all_new_exact_asts_are_distinct_from_each_other_and_selected_support():
    # This bounded check does not claim the separate 3971-row global novelty
    # audit or import the full current Alpha catalogue.
    from peano_lab.library.formula_dag import FormulaArena
    serialized={name:FormulaArena().freeze(_closed_formula(row.statement)).to_json()
                for name,row in core().items()}
    for name in EXPECTED_NAMES:
        assert all(serialized[name]!=other for key,other in serialized.items() if key!=name)


def model_power(code,length,k):
    return 0 if k>=length else decode_beta(code,length-1-k)


def model_pad(source,length,count,target):
    return (all(decode_beta(target,i)==0 for i in range(count))
        and all(decode_beta(target,count+i)==decode_beta(source,i) for i in range(length)))


EXAMPLES=((),(0,),(1,),(0,0),(0,1),(1,0),(1,1,0),(0,0,1),(0,1,0,1),(0,0,0,0))


@pytest.mark.parametrize('values',EXAMPLES)
@pytest.mark.parametrize('count',(0,1,3))
def test_actual_beta_left_padding_preserves_all_formal_coefficients(values,count):
    source=encode_beta(values)
    target=encode_beta((0,)*count+values,2)
    alternate=encode_beta((0,)*count+values,3)
    assert model_pad(source,len(values),count,target)
    assert model_pad(source,len(values),count,alternate)
    assert target!=alternate
    assert decoded_prefix(target,count+len(values))==decoded_prefix(alternate,count+len(values))
    for k in range(count+len(values)+4):
        assert model_power(source,len(values),k)==model_power(target,count+len(values),k)


def test_trailing_zeros_are_not_harmless_left_padding():
    one=encode_beta((1,)); x=encode_beta((1,0))
    assert model_power(one,1,0)==1 and model_power(x,2,0)==0
    assert not model_pad(one,1,1,x)


def test_equality_of_field_evaluations_is_not_formal_polynomial_equality():
    # Over F_2, X^2+X and zero agree at both field elements but have different
    # formal coefficients; the proposed relation deliberately rejects this.
    polynomial=encode_beta((1,1,0)); zero=encode_beta(())
    assert all((x*x+x)%2==0 for x in (0,1))
    assert model_power(polynomial,3,2)==1 and model_power(zero,0,2)==0


@pytest.mark.parametrize('source,target',(((0,0),(0,0)),((27,19),(31,7)),((1,0),(123,0))))
def test_empty_windows_do_not_impose_raw_code_equality(source,target):
    assert model_pad(source,0,0,target)
    assert all(model_power(source,0,k)==model_power(target,0,k)==0 for k in range(8))


def convolution(p,left,right):
    if not left or not right:
        return ()
    return tuple(sum(left[j]*right[i-j] for j in range(len(left)) if 0<=i-j<len(right))%p
                 for i in range(len(left)+len(right)-1))


@pytest.mark.parametrize('p',(2,3,5))
@pytest.mark.parametrize('values',((),(0,),(1,),(0,1),(1,0),(1,1,0),(0,1,0,1)))
def test_actual_constant_convolution_and_inverse_scalar_models(p,values):
    source=encode_beta(values)
    for k in range(p):
        constant=encode_beta((k,),2)
        result=convolution(p,values,(k,))
        product=encode_beta(result,3)
        assert decoded_prefix(constant,1)==(k,)
        assert decoded_prefix(product,len(values))==tuple(k*a%p for a in values)
        assert all(model_power(product,len(values),i)==k*model_power(source,len(values),i)%p
                   for i in range(len(values)+3))
        if k:
            inverse=pow(k,-1,p)
            restored=encode_beta(tuple(inverse*a%p for a in result),4)
            assert decoded_prefix(restored,len(values))==values
        else:
            assert all(a==0 for a in result)


@pytest.mark.parametrize('p',(2,3,5))
@pytest.mark.parametrize('count',(0,1,3))
def test_common_left_padding_transports_actual_add_subtract_and_scale(p,count):
    a,b=(1,0,1),(0,1,1)
    pa,pb=(0,)*count+a,(0,)*count+b
    for operation in (lambda x,y:(x+y)%p,lambda x,y:(x-y)%p):
        c=tuple(operation(x,y) for x,y in zip(a,b))
        pc=tuple(operation(x,y) for x,y in zip(pa,pb))
        assert model_pad(encode_beta(c),len(c),count,encode_beta(pc,2))
    for k in range(p):
        c=tuple(k*x%p for x in a)
        pc=tuple(k*x%p for x in pa)
        assert model_pad(encode_beta(c),len(c),count,encode_beta(pc,2))


def test_numerical_counterexamples_cover_the_rejected_guard_changes():
    one=encode_beta((1,)); padded=encode_beta((0,1))
    assert all(model_power(one,1,k)==model_power(padded,2,k) for k in range(5))
    assert decode_beta(one,0)!=decode_beta(padded,0)
    assert convolution(2,(1,1),(1,1))==(1,0,1)
    assert tuple(a for a in (1,1))!=(1,0)
    assert (1*(2*1%3))%3!=1
    outside=encode_beta((1,9))
    assert model_pad(one,1,0,outside) and decode_beta(outside,1)>=2
    missing_zero=encode_beta((1,1))
    assert decode_beta(missing_zero,1)==decode_beta(one,0)
    assert not model_pad(one,1,1,missing_zero)
    assert model_power(encode_beta(()),0,0)==0!=model_power(one,1,0)


def _main(arguments):
    resource.setrlimit(resource.RLIMIT_CPU,(170,175));signal.alarm(180)
    started=time.monotonic()
    if arguments[:1]==['--bodies']:
        start=int(arguments[1]) if len(arguments)>1 else 0
        count=int(arguments[2]) if len(arguments)>2 else len(rows())
        chosen=rows()[start:start+count]
        assert chosen
        for row in chosen:
            print(json.dumps(asdict(replay_candidate_bodies((row,),core=core())[0]),sort_keys=True),flush=True)
        status=0
    elif arguments[:1]==['--pytest']:
        status=int(pytest.main([str(Path(__file__).resolve()),*arguments[1:]]))
    else:
        raise SystemExit('expected --bodies [START [COUNT]] or --pytest [PYTEST ARGUMENTS]')
    peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*(1 if sys.platform=='darwin' else 1024)
    assert 0<peak<=MAX_RSS_BYTES and time.monotonic()-started<=180
    print(json.dumps({'status':status,'seconds':time.monotonic()-started,'cpu_seconds':time.process_time(),
        'peak_rss_bytes':peak,'cpu_limits':list(resource.getrlimit(resource.RLIMIT_CPU)),
        'wall_alarm_seconds':180}),flush=True)
    return status


if __name__=='__main__':
    raise SystemExit(_main(sys.argv[1:]))
