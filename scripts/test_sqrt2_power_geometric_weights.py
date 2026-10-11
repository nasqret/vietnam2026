"""Actual reverse geometric weights and relational power interpretation."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_geometric_weights as weights


def test_exact_constructed_geometric_weight_and_power_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weights.frozen_geometric_weights_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==2 and not premises and type(conclusion) is Exists
    assert weights.json_hash(encode_formula(target))==weights.TARGET_SHA256
    assert len(weights.canonical(encode_formula(target)))==4908
    c = weights.source_contract()
    assert c["actual_geometric_weights_constructed"] is c["actual_power_constructed"] is True
    assert c["initial_weight_is_power_proved"] is c["all_in_range_weight_power_products_proved"] is True
    assert c["zero_multiplier_allowed"] is True
    assert c["weighted_term_prefix_constructed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_shared_geometric_and_power_definitions_remain_hygienic():
    from sqrt2_power_definitions import parse_named
    r = weights.definition_registry()
    assert weights.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("j","a","b","c")
    assert parse_named("NatGeometricWeightTable(j,a,b,c)",names,r)==parse_named(
        "BetaAt(b,c,a,1) /\\ (forall i x y. Lt(i,a) -> BetaAt(b,c,i,x) -> BetaAt(b,c,S i,y) -> x=j*y)",names,r)


def test_changed_power_index_or_invariant_is_rejected():
    for source in (weights.NAMED_SOURCE.replace("Pow(t,N,p)","Pow(t,S N,p)"),
                   weights.NAMED_SOURCE.replace("w*q=p","w+q=p")):
        with patch.object(weights,"NAMED_SOURCE",source),pytest.raises(ValueError):
            weights.frozen_geometric_weights_target()


def test_helpers_and_owned_actual_scaling_and_power_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    assert {name:weights.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in weights.HELPER_SOURCES.items()}==weights.HELPER_TARGET_SHA256
    found = set()
    for pin in weights.ARCHIVES:
        rows = weights.read_mixed_archive(pin)
        for name,source in weights.ENDPOINT_SOURCES.items():
            if weights.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==weights.ENDPOINT_SOURCES.keys()


def test_modified_actual_archive_is_rejected():
    for original in weights.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                weights.read_mixed_archive(changed)


def test_geometric_weight_scaling_and_power_model_including_zero():
    for t in range(5):
        w = [1]
        for N in range(10):
            assert len(w)==N+1 and w[-1]==1
            assert w[0]==t**N
            assert all(w[j]==t*w[j+1] for j in range(N))
            assert all(w[j]*t**j==t**N for j in range(N+1))
            w = [t*a for a in w]+[1]
    assert 0**0==1 and 0**1==0  # No unconditional nonvanishing claim.


def test_guarded_geometric_weight_proof_replays_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weights.prove_geometric_weights()
    assert result.receipt.target==weights.frozen_geometric_weights_target()
    assert len(result.bundle.nodes)==123
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6042
    assert result.provenance["new_induction_count"]==2
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
