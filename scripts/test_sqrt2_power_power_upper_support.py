"""All-power support is proved through the actual trace, including its unit."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_power_upper_support as support


def test_exact_unconditional_constructed_all_power_support():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = support.frozen_power_upper_support_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and not premises and type(conclusion) is Exists
    assert support.json_hash(encode_formula(target))==support.TARGET_SHA256
    assert len(support.canonical(encode_formula(target)))==6206
    c = support.source_contract()
    assert c["actual_power_trace_constructed"] is c["all_rows_through_exponent_bounded"] is True
    assert c["arbitrary_storage_width"] is c["zero_width_and_empty_input_allowed"] is True
    assert c["unit_at_exponent_zero_retained"] is True and c["support_bound"]=="1+k*L"
    assert c["execution_contains_support_claim"] is c["finite_power_evaluation_identity"] is c["closes_IR072"] is False


def test_unchanged_conservative_property_and_computation_dag():
    registry = support.definition_registry()
    assert support.source_contract()["new_definition_ids"]==[]
    assert registry["NatZeroAfter"].template_formula==support.upper_registry()["NatZeroAfter"].template_formula
    assert registry["NatPowerTrace"].template_formula==support.power_registry()["NatPowerTrace"].template_formula
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_missing_unit_allowance_or_wrong_input_length_is_rejected():
    for source in (support.NAMED_SOURCE.replace("S(k*L)","k*L"),
                   support.NAMED_SOURCE.replace("S(k*L)","S k"),
                   support.NAMED_SOURCE.replace("Le(k,K)","Le(k,S K)")):
        with patch.object(support,"NAMED_SOURCE",source),pytest.raises(ValueError):
            support.frozen_power_upper_support_target()


def test_helpers_and_owned_actual_power_convolution_bodies():
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


def test_finite_support_model_with_empty_input_and_unit_counterexample():
    for L in range(5):
        a = [j+1 for j in range(L)]
        for H in range(10):
            b = [int(i==0) for i in range(H)]
            for k in range(6):
                assert all(v==0 for i,v in enumerate(b) if i>=1+k*L)
                b = [sum(a[j]*b[i-j] for j in range(L) if 0<=i-j<H) for i in range(H)]
    assert [1][0]!=0  # k=0 cannot use cutoff k*L=0.


def test_ordinary_replay_and_forged_upper_support_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = support.prove_power_upper_support()
    assert result.receipt.target==support.frozen_power_upper_support_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(support.ENDPOINT_SOURCES["prefix_support"],registry=support.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
