"""Guard the exact finite product error, actual cutoff and evidence boundary."""
from dataclasses import replace
from fractions import Fraction
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_exp_product_error as product


def test_exact_finite_product_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=product.frozen_exp_product_error_target();binders,premises,conclusion=strip_target(target)
    assert binders==11 and len(premises)==7 and type(conclusion) is Exists
    assert len(product.canonical(encode_formula(target)))==13915
    c=product.source_contract()
    assert c['actual_convolution_table_recurrence_head_and_four_sums_constructed'] is True
    assert c['argument_bound']=='x+y<=d' and c['actual_cutoff_power']=='p=2^n'
    assert c['analytic_exponential_addition'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_thirteen_existing_definitions_are_conservative_and_topological():
    registry=product.definition_registry();pool=product.source_registry();seen=set();ids=set()
    assert len(registry)==13
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_argument_cutoff_head_or_error_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('~d=0 -> ',''),source.replace('Le(x+y,d) -> ',''),
                    source.replace('Pow(2,n,p)','Pow(2,S n,p)'),source.replace('2*(a0*b0)','a0*b0'),
                    source.replace('Le(s,u*v)','s=u*v'),source.replace('(S n)+n','n')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            product.frozen_exp_product_error_target(_registry=registry)


def test_actual_sandwich_recurrence_head_and_tail_bodies_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['sandwich']==('AP041',190) and found['recurrence']==('AP039',160)
    assert found['head']==('AP039',161) and found['truncation']==('CV100',154)
    bad=dict(product.TRUNCATION_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): product.read_mixed_archive(bad)


def _terms(d,x,n):
    h=factorial(n)*d**n
    values=[Fraction(h*x**j,d**j*factorial(j)) for j in range(n+1)]
    assert all(v.denominator==1 for v in values)
    return h,[int(v) for v in values]


def test_integer_scaled_models_match_recurrence_product_and_dyadic_error():
    for n in range(4):
        H=2*n+1
        for d in range(1,5):
            for x in range(d+1):
                for y in range(d-x+1):
                    a0,a=_terms(d,x,H);b0,b=_terms(d,y,H)
                    c=[sum(a[j]*b[i-j] for j in range(i+1)) for i in range(H+1)]
                    assert c[0]==a0*b0
                    assert all((i+1)*d*c[i+1]==(x+y)*c[i] for i in range(H))
                    u,v,s,t=sum(a[:n+1]),sum(b[:n+1]),sum(c[:n+1]),sum(c)
                    assert s<=u*v<=t and 2**n*(u*v)<=2**n*s+2*a0*b0


def test_exact_equality_and_missing_argument_or_denominator_conditions_fail():
    a0,a=_terms(2,1,3);b0,b=_terms(2,1,3)
    assert a0*b0*(1+Fraction(1,2)+Fraction(1,2))<sum(a[:2])*sum(b[:2])
    # n=1, x=y=2, d=1: the omitted upper-argument condition matters.
    assert (1+2)**2>(1+4)+Fraction(2,2)
    # With d=x=y=0 any table satisfies the recurrence, but no tail control follows.
    a=[1,100,0,0];c=[sum(a[j]*a[i-j] for j in range(i+1)) for i in range(4)]
    assert all((i+1)*0*c[i+1]==0*c[i] for i in range(3))
    assert 2*sum(a[:2])**2>2*sum(c[:2])+2


def test_complete_finite_error_replays_without_new_induction():
    result=product.prove_exp_product_error()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_error_body_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=product.prove_exp_product_error();node=result.provenance['helper_bundle_indices']['AP042']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
