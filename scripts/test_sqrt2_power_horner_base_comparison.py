"""Scaled comparison uses the actual base order and length-minus-one power."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_base_comparison as comparison


def test_exact_ordered_base_comparison_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = comparison.frozen_horner_base_comparison_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==1 and type(conclusion) is Exists
    assert comparison.json_hash(encode_formula(target))==comparison.TARGET_SHA256
    assert len(comparison.canonical(encode_formula(target)))==6468
    c = comparison.source_contract()
    assert c["base_order_required"] is c["actual_two_horner_values_and_powers_constructed"] is True
    assert c["zero_bases_allowed"] is c["no_division_or_nonzero_cancellation"] is True
    assert c["length"]=="r+1" and c["scaling_exponent"]=="r"
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_hidden_inequality():
    registry = comparison.definition_registry()
    assert comparison.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_missing_order_wrong_exponent_or_unscaled_bound_rejected():
    for source in (comparison.NAMED_SOURCE.replace("Le(a,b) -> ",""),
                   comparison.NAMED_SOURCE.replace("Pow(a,r,p)","Pow(a,S r,p)"),
                   comparison.NAMED_SOURCE.replace("Le(p*x,q*y)","Le(x,y)"),
                   comparison.NAMED_SOURCE.replace("NatHornerValue(ab,ac,b,S r,x)","NatHornerValue(ab,ac,a,S r,x)")):
        with patch.object(comparison,"NAMED_SOURCE",source),pytest.raises(ValueError):
            comparison.frozen_horner_base_comparison_target()


def test_helper_targets_and_owned_actual_arithmetic():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = comparison.definition_registry()
    assert {n:comparison.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in comparison.HELPER_SOURCES.items()}==comparison.HELPER_TARGET_SHA256
    rows = comparison.read_mixed_archive(comparison.COMPOSITION_ARCHIVE)
    for name,source in comparison.ENDPOINT_SOURCES.items():
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
        assert comparison.ENDPOINT_OWNERS[name]=="CV061"


def test_changed_actual_archive_is_rejected():
    for key in ("sha256","target_ast_sha256"):
        pin = dict(comparison.COMPOSITION_ARCHIVE);pin[key] = "0"*64
        with pytest.raises(ValueError):
            comparison.read_mixed_archive(pin)


def test_scaled_comparison_model_and_missing_order_counterexample():
    def horner(A,t):
        z = 0
        for c in A:
            z = t*z+c
        return z
    for r in range(5):
        for seed in range(4):
            A = [(seed+j*j)%5 for j in range(r+1)]
            for a in range(4):
                for b in range(a,5):
                    p,q,x,y = a**r,b**r,horner(A,b),horner(A,a)
                    assert p<=q and p*x<=q*y
    assert not 3*horner([0,1],2)<=2*horner([0,1],3)
    assert horner([1,1],3)>horner([1,1],2)


def test_ordinary_replay_and_forged_comparison_step_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = comparison.prove_horner_base_comparison()
    assert result.receipt.target==comparison.frozen_horner_base_comparison_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(comparison.HELPER_SOURCES["step_bound"],registry=comparison.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
