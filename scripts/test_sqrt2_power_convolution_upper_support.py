"""Explicit upper supports stay separate from the convolution computation."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_upper_support as support


def test_exact_constructed_convolution_upper_support_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = support.frozen_convolution_upper_support_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==9 and len(premises)==2 and type(conclusion) is Exists
    assert support.json_hash(encode_formula(target))==support.TARGET_SHA256
    assert len(support.canonical(encode_formula(target)))==4670
    c = support.source_contract()
    assert c["input_zero_after_properties_required"] is c["actual_convolution_prefix_constructed"] is True
    assert c["output_zero_after_sum_of_cutoffs_proved"] is c["arbitrary_output_width"] is True
    assert c["zero_cutoffs_and_empty_lengths_allowed"] is True
    assert c["execution_contains_support_claim"] is c["all_power_row_upper_support"] is c["closes_IR072"] is False


def test_exact_conservative_zero_after_property_and_unchanged_execution():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = support.definition_registry()
    d = registry["NatZeroAfter"]
    assert d.stable_id=="ND0436" and d.parameters==support.DEFINITION_PARAMETERS
    assert d.conceptual_dependencies==("Le","BetaZeroExtend")
    assert d.template_formula==parse_named(support.DEFINITION_SOURCE,support.DEFINITION_PARAMETERS,support.base_registry())
    assert support.json_hash(encode_formula(d.template_formula))==support.DEFINITION_SHA256
    assert registry["NatConvolutionPrefix"].template_formula==support.base_registry()["NatConvolutionPrefix"].template_formula
    for value in registry.values():
        assert set(value.conceptual_dependencies)<=registry.keys()
    with patch.object(support,"DEFINITION_SOURCE",support.DEFINITION_SOURCE.replace("Le(r,i)","Lt(r,i)")),pytest.raises(ValueError):
        support.definition_registry()


def test_changed_output_cutoff_or_missing_input_hypothesis_is_rejected():
    for source in (support.NAMED_SOURCE.replace("NatZeroAfter(cb,cc,N,r+s)","NatZeroAfter(cb,cc,N,r)"),
                   support.NAMED_SOURCE.replace("NatZeroAfter(bb,bc,M,s) -> ","")):
        with patch.object(support,"NAMED_SOURCE",source),pytest.raises(ValueError):
            support.frozen_convolution_upper_support_target()


def test_exact_helpers_and_actual_owned_order_sum_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = support.definition_registry()
    assert {name:support.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in support.HELPER_SOURCES.items()}==support.HELPER_TARGET_SHA256
    found = set()
    for pin in support.ARCHIVES:
        rows = support.read_mixed_archive(pin)
        for name,source in support.ENDPOINT_SOURCES.items():
            if support.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==support.ENDPOINT_SOURCES.keys()


def test_changed_actual_archive_is_rejected():
    for original in support.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                support.read_mixed_archive(changed)


def test_finite_support_model_and_too_small_cutoff_counterexample():
    def coefficient(a,b,i):
        return sum(a[j]*b[i-j] for j in range(len(a)) if 0<=i-j<len(b))
    for r in range(6):
        for s in range(6):
            a,b = [j+1 for j in range(r)]+[0,0],[2*k+1 for k in range(s)]+[0]
            assert all(coefficient(a,b,i)==0 for i in range(r+s,r+s+6))
    assert coefficient([1,1],[1,1],2)!=0


def test_ordinary_replay_and_forged_support_ancestor_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = support.prove_convolution_upper_support()
    assert result.receipt.target==support.frozen_convolution_upper_support_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(support.HELPER_SOURCES["split_indices"],registry=support.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
