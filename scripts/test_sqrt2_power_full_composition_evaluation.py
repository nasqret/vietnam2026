"""Whole-support powers and weighted sums must use the same actual witnesses."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_full_composition_evaluation as evaluation


def test_exact_same_witness_composition_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = evaluation.frozen_full_composition_evaluation_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==1 and type(conclusion) is Exists
    assert evaluation.json_hash(encode_formula(target))==evaluation.TARGET_SHA256
    assert len(evaluation.canonical(encode_formula(target)))==25517
    c = evaluation.source_contract()
    assert c["same_actual_power_trace_used_by_accumulation"] is c["all_row_value_entries_have_exact_power_identity"] is True
    assert c["actual_input_value_scaling_powers_row_values_products_and_sum_constructed"] is c["every_terminal_row_evaluates_to_same_sum"] is True
    assert c["zero_multiplier_and_empty_input_allowed"] is c["no_nonzero_factor_cancelled"] is True
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_or_hidden_composition_definition():
    registry = evaluation.definition_registry()
    assert evaluation.source_contract()["new_definition_ids"]==[]
    assert registry["NatPointwiseProductPrefix"].stable_id=="ND0439"
    assert registry["NatHornerValue"].stable_id=="ND0437"
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_missing_width_and_wrong_scaling_or_power_source_rejected():
    for source in (evaluation.NAMED_SOURCE.replace(evaluation.WIDTH+" -> ",""),
                   evaluation.NAMED_SOURCE.replace("a*y=(v*b)*c","y=c"),
                   evaluation.NAMED_SOURCE.replace("Pow(p,k,a) -> ",""),
                   evaluation.NAMED_SOURCE.replace("NatWeightedSeriesTrace(S J,wb,wc,pb,pc,qb,qc", "NatWeightedSeriesTrace(S J,wb,wc,pb,pc,pb,pc")):
        with patch.object(evaluation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            evaluation.frozen_full_composition_evaluation_target()


def test_helper_target_and_actual_owned_composition_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = evaluation.definition_registry()
    assert {n:evaluation.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in evaluation.HELPER_SOURCES.items()}==evaluation.HELPER_TARGET_SHA256
    found = set()
    for pin in evaluation.ARCHIVES:
        rows = evaluation.read_mixed_archive(pin)
        for name,source in evaluation.ENDPOINT_SOURCES.items():
            if evaluation.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==evaluation.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in evaluation.ARCHIVES:
        pin = dict(original);pin["sha256"] = "0"*64
        with pytest.raises(ValueError):
            evaluation.read_mixed_archive(pin)


def test_same_witness_finite_composition_model():
    def horner(coefficients,t):
        z = 0
        for a in coefficients:
            z = t*z+a
        return z
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for A in ([],[0],[2],[0,1],[1,2]):
        for K in range(4):
            J=K*len(A);H=J+1
            rows=[];current=[1]+[0]*J
            for k in range(K):
                rows.append(current);current=conv(A,current,H)
            weights=[(k+1)%3 for k in range(K)]
            total=[sum(weights[k]*rows[k][i] for k in range(K)) for i in range(H)]
            for t in range(4):
                values=[horner(row,t) for row in rows]
                x,p,v=horner(A,t),t**len(A),t**J
                for k,y in enumerate(values):
                    assert p**k*y==(v*t**k)*x**k
                assert horner(total,t)==sum(w*y for w,y in zip(weights,values))


def test_ordinary_replay_and_forged_power_induction_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = evaluation.prove_full_composition_evaluation()
    assert result.receipt.target==evaluation.frozen_full_composition_evaluation_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(evaluation.ENDPOINT_SOURCES["all_power_rows"],registry=evaluation.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
