"""Exact nonzero-leading representation contracts, not degree normalization."""

from __future__ import annotations

from functools import lru_cache
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.library import prime_field_polynomial_degree_candidate as candidate
from peano_lab.library.theorems import TheoremSpec, _closed_formula
from test_prime_field_polynomial_convolution_candidate import (
    assert_inventory, canonical_convolution, capture_cases, compound_cases, core,
    decode_beta, decoded_prefix, encode_beta, expected_and, expected_at,
    expected_coeff, expected_convolution, expected_equal, expected_field_mul,
    expected_length, expected_prime, expected_repeat, fresh, model_convolution,
    rows as convolution_rows, same_ast,
)


SOURCE_SHA256='3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5'
NAMES_SHA256='66383eab05b0a8d6a0903a69bf19bc7d4183cb4428a3c1900e49af0babdecf8c'


@lru_cache(maxsize=1)
def rows():
    return candidate.make_prime_field_polynomial_degree_candidate_theorems(TheoremSpec)


def expected_degree(p,b,c,length,d,*,allow_zero=False,ignore_length=False):
    leading='ind_leading_coefficient'
    point=expected_at(b,c,'0',leading) if allow_zero else expected_and(expected_at(b,c,'0',leading),f'~({leading}=0)')
    size='0=0' if ignore_length else f'({length})=S ({d})'
    return expected_and(size,expected_coeff(p,b,c,length),f'exists {leading}. ({point})')


PUBLIC_CASES=((candidate.prime_field_polynomial_represented_degree_relation,('p','b','c','L','d'),expected_degree),)


@pytest.mark.parametrize('mutation',('none','false_conclusion','truncated_body','removed_dependency','forged_dependency'))
def test_every_degree_body_and_actual_corruption_is_checked_in_fresh_bounded_processes(mutation):
    report=fresh('--bodies','degree',mutation)
    assert [r['name'] for r in report['receipts']]==[r.name for r in rows()]
    if mutation=='none':
        assert sum(r['proof_nodes'] for r in report['receipts'])==677
        assert sum(r['proof_objects'] for r in report['receipts'])==677
        assert max(r['proof_nodes'] for r in report['receipts'])==160
        assert max(r['proof_depth'] for r in report['receipts'])==51
        assert all(r['proof_depth']<=256 and r['proof_objects']<=r['proof_nodes'] for r in report['receipts'])
    else:
        assert all(r['rejected']==mutation for r in report['receipts'])


def test_exact_degree_inventory_and_acyclic_actual_dependencies():
    assert len(rows())==8
    assert sum(len(r.dependencies) for r in rows())==22
    assert sum(len(r.script) for r in rows())==398
    assert sha256(Path(candidate.__file__).read_bytes()).hexdigest()==SOURCE_SHA256
    assert sha256(('\n'.join(row.name for row in rows())+'\n').encode()).hexdigest()==NAMES_SHA256
    assert_inventory(rows(),core()|{r.name:r for r in convolution_rows()})
    dependencies={d for row in rows() for d in row.dependencies}
    assert {'prime_field_no_zero_divisors','prime_field_polynomial_convolution_at_length_exists','prime_field_convolution_coefficient_leading','prime_field_polynomial_repeat_exists'}<=dependencies
    assert not any(any(unproved in r.name for unproved in ('degree_normalization','polynomial_division','polynomial_gcd','extension_field','irreducible')) for r in rows())


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
def test_represented_degree_is_exactly_annotated_length_canonical_prefix_and_nonzero_head(builder,args,expected):
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*args,tag='independent',variables=args)),_closed_formula(binder+expected(*args)))


@pytest.mark.parametrize('builder,args,expected,index,term',compound_cases(PUBLIC_CASES))
def test_every_degree_argument_preserves_compound_and_96bit_numeral_terms(builder,args,expected,index,term):
    values=(*args[:index],term,*args[index+1:])
    binder='forall '+' '.join(args)+'. '
    same_ast(_closed_formula(binder+builder(*values,tag='compound',variables=args)),_closed_formula(binder+expected(*values)))


@pytest.mark.parametrize('builder,args,binder',capture_cases(PUBLIC_CASES))
def test_every_degree_binder_rejects_unused_and_used_context_capture(builder,args,binder):
    with pytest.raises(ValueError,match='captures'):
        builder(*args,tag='capture',variables=args+(binder,))
    with pytest.raises(ValueError,match='captures'):
        builder(f'{args[0]}+{binder}',*args[1:],tag='capture',variables=args+(binder,))


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('context',((),[],('p','p'),('bad name',),('forall',)))
def test_invalid_degree_context_rejected(builder,args,expected,context):
    with pytest.raises(ValueError):
        builder(*('0' for _ in args),tag='invalid',variables=context)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('term',('undeclared','p -> p','p = 0','p; true','',None,7,False))
def test_invalid_degree_term_rejected(builder,args,expected,term):
    with pytest.raises(ValueError):
        builder(term,*args[1:],tag='invalid',variables=args)


@pytest.mark.parametrize('builder,args,expected',PUBLIC_CASES)
@pytest.mark.parametrize('tag',('bad tag','forall','S','',None,False))
def test_invalid_degree_tag_rejected(builder,args,expected,tag):
    with pytest.raises(ValueError):
        builder(*args,tag=tag,variables=args)


PARAMS=('p','ab','ac','L','d','bb','bc','M','e','cb','cc','N')
PRODUCT_ARGS=('p','ab','ac','L','bb','bc','M','cb','cc','N')
SOURCE=('p','ab','ac','L','d','bb','bc','M','e')
PRINCIPAL_CONTRACTS={
    'polynomial_product_length_positive_inputs':f"forall d e N. ({expected_length('S d','S e','N')}) -> N=S (d+e)",
    'prime_field_polynomial_represented_degree_leading_nonzero':f"forall p b c L d a. ({expected_degree('p','b','c','L','d')}) -> ({expected_at('b','c','0','a')}) -> ~(a=0)",
    'prime_field_polynomial_represented_degree_transport':f"forall p b c B C L d. ({expected_equal('b','c','B','C','L')}) -> ({expected_degree('p','b','c','L','d')}) -> ({expected_degree('p','B','C','L','d')})",
    'prime_field_polynomial_represented_degree_excludes_zero':f"forall p b c L d. ({expected_degree('p','b','c','L','d')}) -> ~({expected_repeat('b','c','0','L')})",
    'prime_field_polynomial_monic_degree_examples':f"forall p d. ({expected_prime('p')}) -> exists b c. {expected_and(expected_degree('p','b','c','S d','d'),expected_repeat('b','c','1','S d'))}",
    'prime_field_polynomial_convolution_leading_coefficient':f"forall p ab ac d bb bc e cb cc N a b r. ({expected_convolution('p','ab','ac','S d','bb','bc','S e','cb','cc','N')}) -> ({expected_at('ab','ac','0','a')}) -> ({expected_at('bb','bc','0','b')}) -> ({expected_at('cb','cc','0','r')}) -> ({expected_field_mul('p','a','b','r')})",
    'prime_field_polynomial_convolution_represented_degree':f"forall {' '.join(PARAMS)}. ({expected_prime('p')}) -> ({expected_degree('p','ab','ac','L','d')}) -> ({expected_degree('p','bb','bc','M','e')}) -> ({expected_convolution(*PRODUCT_ARGS)}) -> ({expected_degree('p','cb','cc','N','d+e')})",
    'prime_field_polynomial_convolution_represented_degree_exists':f"forall {' '.join(SOURCE)}. ({expected_prime('p')}) -> ({expected_degree('p','ab','ac','L','d')}) -> ({expected_degree('p','bb','bc','M','e')}) -> exists cb cc. {expected_and(expected_convolution('p','ab','ac','L','bb','bc','M','cb','cc','S (d+e)'),expected_degree('p','cb','cc','S (d+e)','d+e'))}",
}


@pytest.mark.parametrize('name,expected',tuple(PRINCIPAL_CONTRACTS.items()),ids=tuple(PRINCIPAL_CONTRACTS))
def test_every_degree_theorem_has_the_exact_independently_assembled_contract(name,expected):
    row=next(r for r in rows() if r.name==name)
    same_ast(_closed_formula(row.statement),_closed_formula(expected))


GUARD_CASES={
    'composite_modulus':('prime_field_polynomial_convolution_represented_degree',f"forall {' '.join(PARAMS)}. ~(p=0) -> ({expected_degree('p','ab','ac','L','d')}) -> ({expected_degree('p','bb','bc','M','e')}) -> ({expected_convolution(*PRODUCT_ARGS)}) -> ({expected_degree('p','cb','cc','N','d+e')})"),
    'zero_leading_input':('prime_field_polynomial_convolution_represented_degree',f"forall {' '.join(PARAMS)}. ({expected_prime('p')}) -> ({expected_degree('p','ab','ac','L','d',allow_zero=True)}) -> ({expected_degree('p','bb','bc','M','e')}) -> ({expected_convolution(*PRODUCT_ARGS)}) -> ({expected_degree('p','cb','cc','N','d+e')})"),
    'missing_length_annotation':('prime_field_polynomial_convolution_represented_degree',f"forall {' '.join(PARAMS)}. ({expected_prime('p')}) -> ({expected_degree('p','ab','ac','L','d',ignore_length=True)}) -> ({expected_degree('p','bb','bc','M','e')}) -> ({expected_convolution(*PRODUCT_ARGS)}) -> ({expected_degree('p','cb','cc','N','d+e')})"),
    'wrong_degree_formula':('prime_field_polynomial_convolution_represented_degree',f"forall {' '.join(PARAMS)}. ({expected_prime('p')}) -> ({expected_degree('p','ab','ac','L','d')}) -> ({expected_degree('p','bb','bc','M','e')}) -> ({expected_convolution(*PRODUCT_ARGS)}) -> ({expected_degree('p','cb','cc','N','d*e')})"),
    'zero_prefix_has_degree':('prime_field_polynomial_represented_degree_excludes_zero',f"forall p b c L d. ({expected_coeff('p','b','c','L')}) -> ~({expected_repeat('b','c','0','L')})"),
    'zero_instead_of_monic_examples':('prime_field_polynomial_monic_degree_examples',f"forall p d. ({expected_prime('p')}) -> exists b c. {expected_and(expected_degree('p','b','c','S d','d'),expected_repeat('b','c','0','S d'))}"),
}


@pytest.mark.parametrize('mutation',tuple(GUARD_CASES))
def test_degree_proofs_reject_composites_zero_heads_and_wrong_length_or_degree_claims(mutation):
    assert fresh('--guard','degree',mutation)['rejected']==mutation


def model_degree(p,code,length,d):
    return length==d+1 and all(0<=decode_beta(code,i)<p for i in range(length)) and decode_beta(code,0)!=0


@pytest.mark.parametrize('p',(2,3,5,7,11))
@pytest.mark.parametrize('d',range(7))
def test_actual_monic_examples_exist_at_every_tested_degree_and_reencode(p,d):
    coefficients=(1,)*(d+1)
    first,second=encode_beta(coefficients),encode_beta(coefficients,3)
    assert first!=second
    assert decoded_prefix(first,d+1)==decoded_prefix(second,d+1)==coefficients
    assert model_degree(p,first,d+1,d) and model_degree(p,second,d+1,d)


@pytest.mark.parametrize('p',(2,3,5,7))
@pytest.mark.parametrize('lengths',((1,1),(1,4),(4,1),(2,2),(3,4)))
def test_actual_convolution_nonzero_leading_coefficient_and_sum_of_represented_degrees(p,lengths):
    L,M=lengths
    a=(1,)+tuple((i+1)%p for i in range(L-1))
    b=(p-1,)+tuple((2*i+1)%p for i in range(M-1))
    left,right=encode_beta(a),encode_beta(b)
    assert model_degree(p,left,L,L-1) and model_degree(p,right,M,M-1)
    result=canonical_convolution(p,a,b)
    output=encode_beta(result,2)
    assert model_convolution(p,left,L,right,M,output,L+M-1)
    assert result[0]==a[0]*b[0]%p and result[0]!=0
    assert model_degree(p,output,L+M-1,(L-1)+(M-1))


def test_prime_and_nonzero_leading_hypotheses_are_mathematically_necessary():
    a,b=encode_beta((2,)),encode_beta((2,))
    c=encode_beta((0,))
    assert model_degree(4,a,1,0) and model_degree(4,b,1,0)
    assert model_convolution(4,a,1,b,1,c,1)
    assert not model_degree(4,c,1,0)
    for length in (0,1,3):
        zero=encode_beta((0,)*length)
        assert not any(model_degree(2,zero,length,d) for d in range(5))
    assert canonical_convolution(2,(1,1),(1,1))==(1,0,1)
    assert model_degree(2,encode_beta((1,0,1)),3,2)


def test_a_beta_code_pair_without_its_length_is_not_a_unique_polynomial_or_degree():
    code=encode_beta((1,0))
    assert model_degree(2,code,1,0)  # constant 1
    assert model_degree(2,code,2,1)  # X
    assert not model_degree(2,code,1,1)
    assert not model_degree(2,code,2,0)
