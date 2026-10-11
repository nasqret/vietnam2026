"""A finite rectangular product has two different convolution cutoffs."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_convolution_sum_sandwich as sandwich


def test_exact_constructed_rectangular_sandwich_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=sandwich.frozen_convolution_sum_sandwich_target();binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==1 and type(conclusion) is Exists
    assert len(sandwich.canonical(encode_formula(target)))==8800
    c=sandwich.source_contract()
    assert c['both_actual_input_codes_preserved'] is c['long_input_convolution_and_all_four_sums_constructed'] is True
    assert c['lower_output_length']=='L' and c['upper_output_length']=='L+L'
    assert c['quantitative_tail_bound'] is c['analytic_exponential_addition'] is c['closes_IR072'] is False


def test_eleven_existing_definitions_form_exact_dependency_dag():
    registry=sandwich.definition_registry();pool=sandwich.source_registry();seen=set();ids=set()
    assert len(registry)==11
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert sandwich.source_contract()['new_definition_ids']==[]


def test_changed_input_order_sum_cutoff_or_rectangular_product_rejected():
    source=sandwich.NAMED_SOURCE;registry=sandwich.definition_registry()
    for changed in (source.replace('Le(L,M) -> ',''),source.replace('L+L','L'),
                    source.replace('Sum(cb,cc,L,s)','Sum(cb,cc,S L,s)'),
                    source.replace('Le(u*v,t)','Le(t,u*v)'),source.replace('Sum(ab,ac,L,u)','Sum(ab,ac,M,u)')):
        assert changed!=source
        with patch.object(sandwich,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            sandwich.frozen_convolution_sum_sandwich_target(_registry=registry)


def test_helpers_and_actual_locality_order_product_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=sandwich.definition_registry();found={}
    assert {k:sandwich.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in sandwich.HELPER_SOURCES.items()}==sandwich.HELPER_TARGET_SHA256
    for pin in sandwich.ARCHIVES:
        rows=sandwich.read_mixed_archive(pin)
        for name,source in sandwich.ENDPOINT_SOURCES.items():
            if sandwich.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['coefficient_order']==('AP040',45) and found['sum_order']==('AP040',43)
    assert found['total']==('CV048',161) and found['locality']==('CV050',115)
    bad=dict(sandwich.TOTAL_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): sandwich.read_mixed_archive(bad)


def _convolution(a,b,M,length):
    return [sum(a[j]*b[i-j] for j in range(M) if 0<=i-j<M) for i in range(length)]


def test_exact_sandwich_models_cover_empty_equal_and_extended_inputs():
    for a,b in (([0]*7,[3]*7),([1,0,3,1,5,0,2],[0,2,1,0,3,1,1]),([1]*7,[2]*7)):
        for L in range(7):
            for M in range(L,7):
                c=_convolution(a,b,M,L+L);product=sum(a[:L])*sum(b[:L])
                assert sum(c[:L])<=product<=sum(c)


def test_length_order_and_two_distinct_output_cutoffs_are_necessary():
    a=b=[1,2];L=2;M=1;product=sum(a[:L])*sum(b[:L])
    assert product>sum(_convolution(a,b,M,2*L))
    c=_convolution(a,b,2,4)
    assert sum(c[:2])<product  # The upper sum cannot generally stop at L.
    c=_convolution(a,b,2,2);product=a[0]*b[0]
    assert sum(c)>product  # Nor may the lower sum be extended past L=1.


def test_complete_sandwich_replays_without_new_induction():
    result=sandwich.prove_convolution_sum_sandwich()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_prefix_sum_order_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=sandwich.prove_convolution_sum_sandwich();node=result.provenance['helper_bundle_indices']['sum_prefix']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
