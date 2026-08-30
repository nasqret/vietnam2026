"""Leading coefficients and degree of explicitly nonzero-leading prefixes.

A polynomial representation contains its length as well as its beta-code
pair.  RepresentedDegree(p,b,c,L,d) requires L=S d, canonical coefficients,
and an actually decoded nonzero coefficient at index zero.  It does not trim
zeros, assign a degree to the zero polynomial, or equate beta codes with no
length annotation.  The product theorem uses the genuine antidiagonal sum.
"""

from __future__ import annotations

from typing import Any, Callable

from .prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _parts, _prime, _public, _mul as _field_mul,
)
from .prime_field_polynomial_candidate import _at, _coeff, _equal, _repeat
from .prime_field_polynomial_convolution_candidate import _convolution, _length
from .prime_field_tables_candidate import _rewrite_all


def _degree(p: str, b: str, c: str, length: str, d: str, tag: str) -> str:
    a='pfd_leading_'+tag
    leading=f'exists {a}. '+_and(_at(b,c,'0',a,tag+'entry'),f'~({a}=0)')
    return _and(f'({length})=S ({d})',_coeff(p,b,c,length,tag+'coefficients'),leading)


def prime_field_polynomial_represented_degree_relation(p: str, b: str, c: str, length: str, d: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Degree of a length-annotated, canonical, genuinely nonzero-leading prefix."""
    return _public(_degree,(p,b,c,length,d),tag=tag,variables=variables)


def _positive_length(d: str, e: str) -> tuple[str,...]:
    return ('right','split','intro hz')+_call('succ_ne_zero',d)+('exact hz','split','intro hz')+_call('succ_ne_zero',e)+('exact hz','simp [add_succ_left]')


def _representation_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    length=spec(
        'polynomial_product_length_positive_inputs',
        f"forall d e N. ({_length('S d','S e','N','degree_product_length')}) -> N=S (d+e)",
        ('polynomial_product_length_functional','succ_ne_zero','add_succ_left'),
        _intro('d','e','N','h')+_call('polynomial_product_length_functional','S d','S e','N','S (d+e)')+('exact h',)+_positive_length('d','e'),
        'Two nonempty representation lengths S d and S e have the unique proper product length S(d+e).',
    )
    nonzero=spec(
        'prime_field_polynomial_represented_degree_leading_nonzero',
        f"forall p b c L d a. ({_degree('p','b','c','L','d','degree_nonzero_source')}) -> ({_at('b','c','0','a','degree_nonzero_entry')}) -> ~(a=0)",
        ('beta_at_unique',),
        _intro('p','b','c','L','d','a','h','ha')+_parts('h',3)+('cases h_right_right','cases h_right_right_witness','have heq : a=x')
        +_call('beta_at_unique','b','c','0','a','x')+('exact ha','exact h_right_right_witness_left','intro hz','apply h_right_right_witness_right','trans a','symm','exact heq','exact hz'),
        'Every decoding of the leading coefficient of this nonzero-leading representation is actually nonzero.',
    )
    body=_intro('p','b','c','B','C','L','d','he','h')+_parts('h',3)+('cases h_right_right','cases h_right_right_witness','split','exact h_left','split')
    body+=_call('matrix_rank_bounded_prefix_transport','b','c','B','C','L','p')+('exact he','exact h_right_left','exists x','split')
    body+=_call('he','0','x')+('rewrite h_left','exists d','simp','exact h_right_right_witness_left','exact h_right_right_witness_right')
    transport=spec(
        'prime_field_polynomial_represented_degree_transport',
        f"forall p b c B C L d. ({_equal('b','c','B','C','L','degree_recode')}) -> ({_degree('p','b','c','L','d','degree_old')}) -> ({_degree('p','B','C','L','d','degree_new')})",
        ('matrix_rank_bounded_prefix_transport',),body,
        'Reencoding an actual coefficient prefix preserves its annotated length, canonical bounds and nonzero leading coefficient.',
    )
    zero=spec(
        'prime_field_polynomial_represented_degree_excludes_zero',
        f"forall p b c L d. ({_degree('p','b','c','L','d','degree_not_zero')}) -> ~({_repeat('b','c','0','L','degree_zero_prefix')})",
        ('beta_repeat_entry_eq',),
        _intro('p','b','c','L','d','h','hz')+_parts('h',3)+('cases h_right_right','cases h_right_right_witness','apply h_right_right_witness_right')
        +_call('beta_repeat_entry_eq','b','c','0','L','0','x')+('exact hz','rewrite h_left','exists d','simp','exact h_right_right_witness_left'),
        'An actual zero polynomial prefix cannot satisfy represented nonzero degree, including degree zero.',
    )
    example=spec(
        'prime_field_polynomial_monic_degree_examples',
        f"forall p d. ({_prime('p','degree_example_prime')}) -> exists b c. "
        +_and(_degree('p','b','c','S d','d','degree_example'),_repeat('b','c','1','S d','degree_example_ones')),
        ('prime_field_polynomial_repeat_exists','prime_two_le','succ_ne_zero'),
        _intro('p','d','hp')+(f"have h : exists b c. {_and(_coeff('p','b','c','S d','degree_example_coefficients'),_repeat('b','c','1','S d','degree_example_repeated'))}",)
        +_call('prime_field_polynomial_repeat_exists','p','1','S d')+_call('prime_two_le','p')+('exact hp','cases h','cases h_witness','cases h_witness_witness','exists x','exists x1','split','split','refl','split','exact h_witness_witness_left','exists 1','split')
        +_call('h_witness_witness_right','0')+('exists d','simp','intro hz')+_call('succ_ne_zero','0')+('exact hz','exact h_witness_witness_right'),
        'For every prime and every degree construct an actual all-one coefficient prefix, proving that the nonzero-leading degree interface is inhabited, also in characteristic two.',
    )
    return length,nonzero,transport,zero,example


def _product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    args=('p','ab','ac','d','bb','bc','e','cb','cc','N','a','b','r')
    product=lambda tag:_convolution('p','ab','ac','S d','bb','bc','S e','cb','cc','N',tag)
    body=_intro(*args,'h','ha','hb','hr')+(f'have hcopy : {product("leading_product_copy")}', 'exact h')+_parts('hcopy',4)
    body+=('have hlen : N=S (d+e)',)+_call('polynomial_product_length_positive_inputs','d','e','N')+('exact hcopy_right_right_left',)
    body+=_call('prime_field_convolution_coefficient_leading','p','ab','ac','d','bb','bc','e','a','b','r')
    body+=('exact hcopy_left','exact hcopy_right_left','exact ha','exact hb')
    body+=_call('prime_field_polynomial_convolution_entry','p','ab','ac','S d','bb','bc','S e','cb','cc','N','0','r')
    body+=('exact h','rewrite hlen','exists d+e','simp','exact hr')
    leading=spec(
        'prime_field_polynomial_convolution_leading_coefficient',
        f"forall {' '.join(args)}. ({product('leading_product')}) -> ({_at('ab','ac','0','a','leading_a')}) -> ({_at('bb','bc','0','b','leading_b')}) -> ({_at('cb','cc','0','r','leading_r')}) -> ({_field_mul('p','a','b','r','leading_actual_multiply')})",
        ('polynomial_product_length_positive_inputs','prime_field_convolution_coefficient_leading','prime_field_polynomial_convolution_entry'),body,
        'The leading coefficient of the actual proper-length convolution is the actual canonical product of the input leading coefficients.',
    )
    params=('p','ab','ac','L','d','bb','bc','M','e','cb','cc','N')
    original=lambda tag:_convolution('p','ab','ac','L','bb','bc','M','cb','cc','N',tag)
    body=_intro(*params,'hp','ha','hb','hc')+_parts('ha',3)+_parts('hb',3)
    body+=(f'have hcopy : {original("degree_product_copy")}', 'exact hc')+_parts('hcopy',4)
    body+=(f"have hl : {_length('L','M','N','degree_product_length_copy')}",'exact hcopy_right_right_left')
    body+=_rewrite_all('ha_left',_length('L','M','N','degree_product_length_a'),'L','hl')
    body+=_rewrite_all('hb_left',_length('S d','M','N','degree_product_length_b'),'M','hl')
    body+=('have hlen : N=S (d+e)',)+_call('polynomial_product_length_positive_inputs','d','e','N')+('exact hl','split','exact hlen','split')
    body+=_call('prime_field_polynomial_convolution_bounded','p','ab','ac','L','bb','bc','M','cb','cc','N')+('exact hc',)
    body+=('cases ha_right_right','cases ha_right_right_witness','cases hb_right_right','cases hb_right_right_witness')
    body+=(f"have hout : exists r. ({_at('cb','cc','0','r','degree_product_output')})",)+_call('beta_at_exists','cb','cc','0')+('cases hout','exists x2','split','exact hout_witness','intro hz')
    body+=(f'have hcanon : {product("degree_product_canonical")}',f'have htemp : {original("degree_product_original")}', 'exact hc')
    body+=_rewrite_all('ha_left',original('degree_product_rewrite_a'),'L','htemp')
    body+=_rewrite_all('hb_left',_convolution('p','ab','ac','S d','bb','bc','M','cb','cc','N','degree_product_rewrite_b'),'M','htemp')+('exact htemp',)
    body+=(f"have hm : {_field_mul('p','x','x1','x2','degree_product_leading_mul')}",)
    body+=_call('prime_field_polynomial_convolution_leading_coefficient','p','ab','ac','d','bb','bc','e','cb','cc','N','x','x1','x2')+('exact hcanon','exact ha_right_right_witness_left','exact hb_right_right_witness_left','exact hout_witness')
    body+=_rewrite_all('hz',_field_mul('p','x','x1','x2','degree_product_zero_rewrite'),'x2','hm')
    body+=('have heither : x=0 \\/ x1=0',)+_call('prime_field_no_zero_divisors','p','x','x1')+('exact hp','exact hm','cases heither','apply ha_right_right_witness_right','exact heither_left','apply hb_right_right_witness_right','exact heither_right')
    degree=spec(
        'prime_field_polynomial_convolution_represented_degree',
        f"forall {' '.join(params)}. ({_prime('p','degree_product_prime')}) -> ({_degree('p','ab','ac','L','d','degree_product_left')}) -> ({_degree('p','bb','bc','M','e','degree_product_right')}) -> ({original('degree_product_actual')}) -> ({_degree('p','cb','cc','N','d+e','degree_product_result')})",
        ('polynomial_product_length_positive_inputs','prime_field_polynomial_convolution_bounded','beta_at_exists','prime_field_polynomial_convolution_leading_coefficient','prime_field_no_zero_divisors'),body,
        'Over an actual prime field the convolution of two nonzero-leading representations has nonzero leading coefficient and represented degree exactly d+e.',
    )
    source=('p','ab','ac','L','d','bb','bc','M','e')
    body=_intro(*source,'hp','ha','hb')
    body+=(f"have hacopy : {_degree('p','ab','ac','L','d','degree_exists_left_copy')}",'exact ha')+_parts('hacopy',3)
    body+=(f"have hbcopy : {_degree('p','bb','bc','M','e','degree_exists_right_copy')}",'exact hb')+_parts('hbcopy',3)
    body+=(f"have hlen : {_length('L','M','S (d+e)','degree_exists_length')}",)
    body+=_rewrite_all('hacopy_left',_length('L','M','S (d+e)','degree_exists_length_a'),'L')
    body+=_rewrite_all('hbcopy_left',_length('S d','M','S (d+e)','degree_exists_length_b'),'M')+_positive_length('d','e')
    body+=(f"have hc : exists cb cc. ({_convolution('p','ab','ac','L','bb','bc','M','cb','cc','S (d+e)','degree_exists_convolution')})",)
    body+=_call('prime_field_polynomial_convolution_at_length_exists','p','ab','ac','L','bb','bc','M','S (d+e)')+('intro hz',)+_call('prime_nonzero','p')
    body+=('exact hp','exact hz','exact hacopy_right_left','exact hbcopy_right_left','exact hlen','cases hc','cases hc_witness','exists x','exists x1','split','exact hc_witness_witness')
    body+=_call('prime_field_polynomial_convolution_represented_degree','p','ab','ac','L','d','bb','bc','M','e','x','x1','S (d+e)')+('exact hp','exact ha','exact hb','exact hc_witness_witness')
    exists=spec(
        'prime_field_polynomial_convolution_represented_degree_exists',
        f"forall {' '.join(source)}. ({_prime('p','degree_exists_prime')}) -> ({_degree('p','ab','ac','L','d','degree_exists_left')}) -> ({_degree('p','bb','bc','M','e','degree_exists_right')}) -> exists cb cc. "
        +_and(_convolution('p','ab','ac','L','bb','bc','M','cb','cc','S (d+e)','degree_exists_product'),_degree('p','cb','cc','S (d+e)','d+e','degree_exists_result')),
        ('succ_ne_zero','add_succ_left','prime_field_polynomial_convolution_at_length_exists','prime_nonzero','prime_field_polynomial_convolution_represented_degree'),body,
        'Construct the genuine product and its exact sum-of-degrees certificate for arbitrary nonzero-leading input representations, including constants and characteristic two.',
    )
    return leading,degree,exists


def make_prime_field_polynomial_degree_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_representation_rows(spec),*_product_rows(spec))


__all__=['prime_field_polynomial_represented_degree_relation','make_prime_field_polynomial_degree_candidate_theorems']
