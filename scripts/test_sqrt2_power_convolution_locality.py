"""Local convolution transport preserves the actual diagonal and its sum."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_locality as locality


def test_exact_conditional_common_coefficient_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = locality.frozen_convolution_locality_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==14 and len(premises)==3 and type(conclusion) is Exists
    assert locality.json_hash(encode_formula(target))==locality.TARGET_SHA256
    assert len(locality.canonical(encode_formula(target)))==7346
    c = locality.source_contract()
    assert c["two_local_padded_input_transports_required"] is c["strict_coefficient_bound_required"] is True
    assert c["common_actual_coefficient_constructed"] is c["arbitrary_input_lengths_and_encodings"] is True
    assert c["same_actual_diagonal_and_sum_witnesses_preserved"] is True
    assert c["all_degree_product_equality"] is c["cross_width_power_trace_transport"] is c["closes_IR072"] is False


def test_unchanged_conservative_definition_dag():
    registry = locality.definition_registry()
    assert locality.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_weakened_strict_cutoff_or_changed_padding_transport_is_rejected():
    for source in (locality.NAMED_SOURCE.replace("Lt(i,H)","Le(i,H)"),
                   locality.NAMED_SOURCE.replace("BetaZeroExtend(cb,cc,N,j,a)","BetaZeroExtend(ab,ac,L,j,a)")):
        with patch.object(locality,"NAMED_SOURCE",source),pytest.raises(ValueError):
            locality.frozen_convolution_locality_target()


def test_helpers_and_actual_owned_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = locality.definition_registry()
    assert {name:locality.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in locality.HELPER_SOURCES.items()}==locality.HELPER_TARGET_SHA256
    rows = locality.read_mixed_archive(locality.CONVOLUTION_ARCHIVE)
    for name,source in locality.ENDPOINT_SOURCES.items():
        assert locality.ENDPOINT_OWNERS[name]=="CV003"
        matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=registry))]
        assert len(matches)==1 and matches[0][3]


def test_changed_actual_archive_is_rejected():
    for key in ("sha256","bundle_sha256","target_ast_sha256"):
        changed = dict(locality.CONVOLUTION_ARCHIVE);changed[key] = "0"*64
        with pytest.raises(ValueError):
            locality.read_mixed_archive(changed)


def test_locality_model_and_boundary_counterexample():
    def coeff(a,b,i):
        return sum(a[j]*b[i-j] for j in range(len(a)) if 0<=i-j<len(b))
    for H in range(7):
        a,b = [j+1 for j in range(H)],[2*j+3 for j in range(H)]
        for extra in range(4):
            c,d = a+[13]*extra,b+[17]*(extra+1)
            for i in range(H):
                assert coeff(a,b,i)==coeff(c,d,i)
    assert coeff([1],[1],1)!=coeff([1,1],[1],1)


def test_ordinary_replay_and_forged_transport_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = locality.prove_convolution_locality()
    assert result.receipt.target==locality.frozen_convolution_locality_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(locality.HELPER_SOURCES["term_transport"],registry=locality.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
