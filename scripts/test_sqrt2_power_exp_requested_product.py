"""Requested product accuracy retains independently supplied finite data."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_requested_product as product


def test_exact_requested_product_keeps_all_supplied_data_and_dyadic_scale():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=product.frozen_exp_requested_product_target();n,premises,conclusion=strip_target(target)
    assert n==19 and len(premises)==13 and type(conclusion) is And
    assert len(product.canonical(encode_formula(target)))==10331
    c=product.source_contract()
    assert c['all_three_supplied_recurrences_heads_codes_and_sums_preserved'] is True
    assert c['independent_output_code_and_head_allowed'] is c['auxiliary_powers_constructed_not_assumed'] is True
    assert c['analytic_exponential_addition'] is c['rational_validity_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_thirteen_existing_definitions_preserve_the_exact_dag():
    registry=product.definition_registry();source=product.source_registry();seen=set();ids=set()
    assert len(registry)==13
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_argument_scale_cutoff_or_cross_normalization_is_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('Le(x+y,L*d)','Le(x+y,d)'),source.replace('Le(2*L,K)','Le(L,K)'),
                    source.replace('L*K+n','L+n'),source.replace('Pow(2,n,r)','Pow(2,S n,r)'),
                    source.replace('BetaAt(cb,cc,0,c0)','BetaAt(cb,cc,0,a0*b0)'),
                    source.replace('+c0*(a0*b0)','+a0*b0')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            product.frozen_exp_requested_product_target(_registry=registry)


def test_integer_models_have_independent_heads_and_requested_normalized_error():
    from fractions import Fraction
    from math import factorial,lcm
    def terms(d,x,N,scale):
        coefficients=[Fraction(x,d)**j/factorial(j) for j in range(N+1)]
        h=scale*lcm(*(c.denominator for c in coefficients));raw=[h*c for c in coefficients]
        assert all(v.denominator==1 for v in raw)
        values=[int(v) for v in raw]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,values
    inputs=[(d,L,x,y,3) for d in (1,2) for L in (0,1) for x in range(L*d+1) for y in range(L*d-x+1)]
    inputs += [(1,2,0,2,2),(1,2,2,0,2),(2,2,0,4,2),(2,2,4,0,2)]
    examples=0;large=distinct=False
    for d,L,x,y,precisions in inputs:
        K=2*L
        for n in range(precisions):
            D=K+(L*K+n);H=2*D+1;r=2**n
            for fa,fb,fc in ((0,1,2),(1,0,3),(1,1,0),(1,1,1),(2,3,5)):
                a0,a=terms(d,x,H,fa);b0,b=terms(d,y,H,fb);c0,c=terms(d,x+y,D,fc)
                u,v,w=sum(a[:D+1]),sum(b[:D+1]),sum(c)
                left,right=(a0*b0)*w,c0*(u*v)
                assert r>0 and left<=right and r*right<=r*left+c0*(a0*b0)
                assert max(r*right,r*left+c0*(a0*b0)).bit_length()<=128
                examples+=1;large|=x+y>d;distinct|=c0!=a0*b0
    assert examples==205 and large and distinct


def test_each_endpoint_uses_its_actual_owned_closed_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found=={'product':('AP061',254),'budget':('AP062',128),'error_scale':('AP063',169),'power_exists':('AP010',110)}
    with pytest.raises(ValueError):product.read_mixed_archive(dict(product.TRUNCATION_ARCHIVE,sha256='0'*64))


def test_source_and_archive_pins_include_the_actual_error_scale_producer():
    import sqrt2_power_exp_requested_truncation as truncation
    pins=product.exp_requested_product_source_pins();assert len(pins)==365
    for pin in product.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert product.ENDPOINT_SOURCES['error_scale']==truncation.HELPER_SOURCES['arithmetic']
    assert pins['scripts/sqrt2_power_exp_requested_truncation.py']['sha256']=='c717b1459260df08516efabcebcbca3f69ee271c2122e67f404f8ef8cb20ebc7'


def test_complete_requested_product_without_new_induction():
    result=product.prove_exp_requested_product()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=product.prove_exp_requested_product()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
