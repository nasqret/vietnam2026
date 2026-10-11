"""The exact weighted coefficient law and its ordinary closed proof data."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_weighted_convolution as weighted


def test_exact_target_and_separate_computational_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weighted.frozen_weighted_convolution_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==18 and len(premises)==5 and type(conclusion) is Exists
    assert weighted.json_hash(encode_formula(target))==weighted.TARGET_SHA256
    assert len(weighted.canonical(encode_formula(target)))==10330
    c = weighted.source_contract()
    assert c["actual_three_geometric_tables_required"] is c["actual_two_weighted_prefixes_required"] is True
    assert c["both_actual_convolution_coefficients_and_output_weight_constructed"] is True
    assert c["all_natural_indices_and_zero_multiplier_allowed"] is c["extra_multiplier_kept"] is True
    assert c["full_convolution_evaluation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_shared_conservative_definition_dag_has_no_new_axioms():
    from sqrt2_power_definitions import parse_named
    registry = weighted.definition_registry()
    assert weighted.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert parse_named(weighted.GRAPHS[3],weighted.P,registry)==parse_named(
        "forall j a b c. Lt(j,L) -> BetaAt(ab,ac,j,a) -> BetaAt(lb,lc,S j,b) -> BetaAt(ub,uc,j,c) -> c=a*b",
        weighted.P,registry)


def test_changed_multiplier_or_weight_index_is_rejected():
    for source in (weighted.NAMED_SOURCE.replace("u*w=t*v","u*w=v"),
                   weighted.NAMED_SOURCE.replace("BetaAt(nb,nc,S k,w)","BetaAt(nb,nc,k,w)")):
        with patch.object(weighted,"NAMED_SOURCE",source),pytest.raises(ValueError):
            weighted.frozen_weighted_convolution_target()


def test_exact_helpers_and_actual_owned_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = weighted.definition_registry()
    assert {name:weighted.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in weighted.HELPER_SOURCES.items()}==weighted.HELPER_TARGET_SHA256
    found = set()
    for pin in weighted.ARCHIVES:
        rows = weighted.read_mixed_archive(pin)
        for name,source in weighted.ENDPOINT_SOURCES.items():
            if weighted.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,row in enumerate(rows) if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and rows[matches[0]][3]
            found.add(name)
    assert found==weighted.ENDPOINT_SOURCES.keys()


def test_changed_actual_wave_archive_is_rejected():
    for original in weighted.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                weighted.read_mixed_archive(changed)


def test_finite_model_includes_zero_base_empty_inputs_and_outside_indices():
    def coefficient(a,b,k):
        return sum(a[i]*b[k-i] for i in range(len(a)) if 0<=k-i<len(b))
    for t in range(4):
        for L in range(5):
            for M in range(5):
                for offset in range(3):
                    a,b = [(i+offset)%4 for i in range(L)],[(2*j+offset)%5 for j in range(M)]
                    u,v = [x*t**(L-i-1) for i,x in enumerate(a)],[y*t**(M-j-1) for j,y in enumerate(b)]
                    for k in range(L+M+3):
                        w = t**(L+M-k-1) if k<L+M else 17
                        assert coefficient(a,b,k)*w==t*coefficient(u,v,k)
    assert coefficient([2],[5],0)*3!=coefficient([2],[5],0)


def test_ordinary_replay_rejects_false_target_forged_root_and_imported_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weighted.prove_weighted_convolution()
    assert result.receipt.target==weighted.frozen_weighted_convolution_target()
    assert len(result.bundle.nodes)==148
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==8193
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    ancestor = parse_named(weighted.ENDPOINT_SOURCES["weights_product"],registry=weighted.definition_registry())
    nodes = [n.node_id for n in result.bundle.nodes if n.target==ancestor]
    assert len(nodes)==1
    for node_id in (result.bundle.root,nodes[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
