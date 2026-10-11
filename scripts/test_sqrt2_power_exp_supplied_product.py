"""Finite product transport preserves all supplied codes and independent heads."""
from dataclasses import replace
from fractions import Fraction
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_exp_supplied_product as product


def test_exact_supplied_product_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=product.frozen_exp_supplied_product_target();binders,premises,conclusion=strip_target(target)
    assert binders==17 and len(premises)==12 and type(conclusion) is And
    assert len(product.canonical(encode_formula(target)))==9375
    c=product.source_contract()
    assert c['all_three_supplied_recurrences_heads_codes_and_sums_preserved'] is True
    assert c['independent_output_code_and_head_allowed'] is c['zero_arguments_heads_and_cutoff_allowed'] is True
    assert c['analytic_exponential_addition'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_definition_dag_has_no_error_assumption():
    registry=product.definition_registry();pool=product.source_registry();seen=set();ids=set()
    assert len(registry)==13
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_supplied_sum_head_argument_or_error_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('Sum(cb,cc,S n,w) -> ',''),source.replace('BetaAt(cb,cc,0,c0)','BetaAt(cb,cc,0,a0*b0)'),
                    source.replace('Le(x+y,d) -> ',''),source.replace('NatScaledExpRecurrence(d,x+y,cb,cc,n)','NatScaledExpRecurrence(d,x,cb,cc,n)'),
                    source.replace('2*(c0*(a0*b0))','c0*(a0*b0)'),source.replace('Pow(2,n,p)','Pow(2,S n,p)')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            product.frozen_exp_supplied_product_target(_registry=registry)


def test_actual_independence_restriction_and_sum_uniqueness_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    assert {k:product.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in product.HELPER_SOURCES.items()}==product.HELPER_TARGET_SHA256
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['product']==('AP042',242) and found['same_value']==('AP005',226)
    assert found['restrict']==('CV101',186) and found['sum_unique']==('CV003',109)
    bad=dict(product.INDEPENDENCE_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): product.read_mixed_archive(bad)


def _terms(d,x,N,scale):
    h=scale*factorial(N)*d**N
    terms=[Fraction(h*x**j,d**j*factorial(j)) for j in range(N+1)]
    assert all(v.denominator==1 for v in terms)
    return h,[int(v) for v in terms]


def test_independent_head_models_include_zero_and_distinct_normalizations():
    for n in range(4):
        for x,y,d in ((0,0,1),(1,0,1),(1,1,2),(1,2,4)):
            for A,B,C in ((1,2,3),(0,1,5),(2,0,7),(2,3,0)):
                a0,a=_terms(d,x,2*n+1,A);b0,b=_terms(d,y,2*n+1,B);c0,c=_terms(d,x+y,n,C)
                u,v,w=sum(a[:n+1]),sum(b[:n+1]),sum(c)
                assert (a0*b0)*w<=c0*(u*v)
                assert 2**n*(c0*(u*v))<=2**n*((a0*b0)*w)+2*(c0*(a0*b0))


def test_cross_value_equality_does_not_mean_numerator_or_code_equality():
    a0,a=_terms(2,1,3,1);b0,b=_terms(2,1,3,2);c0,c=_terms(2,2,1,3)
    conv=[sum(a[j]*b[i-j] for j in range(i+1)) for i in range(2)]
    assert sum(conv)!=sum(c) and c0!=a0*b0
    assert c0*sum(conv)==a0*b0*sum(c)
    assert sum(c)<=Fraction(sum(a[:2])*sum(b[:2])*c0,a0*b0)


def test_complete_supplied_product_replays_without_new_induction():
    result=product.prove_exp_supplied_product()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_scale_transport_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=product.prove_exp_supplied_product();node=result.provenance['helper_bundle_indices']['arithmetic']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
