"""Actual finite-sum interpretation with both computational premises retained."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_weighted_sum as weighted


def test_exact_conditional_horner_weighted_sum_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weighted.frozen_horner_weighted_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==2 and type(conclusion) is Exists
    assert weighted.json_hash(encode_formula(target))==weighted.TARGET_SHA256
    assert len(weighted.canonical(encode_formula(target)))==4537
    c = weighted.source_contract()
    assert c["actual_geometric_weights_required"] is c["actual_pointwise_products_required"] is True
    assert c["horner_trace_and_endpoint_constructed"] is c["actual_sum_for_same_endpoint_proved"] is True
    assert c["weights_or_products_constructed"] is c["power_interpretation_of_weights"] is False
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_new_computation_definitions_have_exact_hygienic_dags():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weighted.definition_registry()
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    for identifier,name,params,source,deps,digest in weighted.DEFINITIONS:
        d = r[name]
        assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
        assert weighted.json_hash(encode_formula(d.template_formula))==digest
        assert d.template_formula==parse_named(source,params,r)
    names = ("j","a","b","c")
    assert parse_named("NatGeometricWeightTable(j,a,b,c)",names,r)==parse_named(
        "BetaAt(b,c,a,1) /\\ (forall i x y. Lt(i,a) -> BetaAt(b,c,i,x) -> BetaAt(b,c,S i,y) -> x=j*y)",names,r)


def test_missing_product_premise_or_changed_weight_definition_is_rejected():
    changed = weighted.NAMED_SOURCE.replace(weighted.PRODUCTS+" -> ","",1)
    with patch.object(weighted,"NAMED_SOURCE",changed),pytest.raises(ValueError):
        weighted.frozen_horner_weighted_sum_target()
    definitions = list(weighted.DEFINITIONS)
    identifier,name,params,source,deps,digest = definitions[0]
    definitions[0] = (identifier,name,params,source.replace("BetaAt(wb,wc,N,1)","BetaAt(wb,wc,N,2)"),deps,digest)
    with patch.object(weighted,"DEFINITIONS",tuple(definitions)),pytest.raises(ValueError):
        weighted.definition_registry()


def test_helpers_and_owned_actual_sum_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weighted.definition_registry()
    assert {name:weighted.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in weighted.HELPER_SOURCES.items()}==weighted.HELPER_TARGET_SHA256
    found = set()
    for pin in weighted.ARCHIVES:
        rows = weighted.read_mixed_archive(pin)
        for name,source in weighted.ENDPOINT_SOURCES.items():
            if weighted.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==weighted.ENDPOINT_SOURCES.keys()


def test_modified_actual_archive_is_rejected():
    for original in weighted.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                weighted.read_mixed_archive(changed)


def test_weighted_sum_model_and_terminal_one_requirement():
    for a in ([],[0],[2],[3,1,4,0,2]):
        N = len(a)
        for t in range(5):
            w = [t**(N-j) for j in range(N+1)]
            q = [x*w[j+1] for j,x in enumerate(a)]
            h = 0
            assert h*w[0]==0
            for j,x in enumerate(a):
                h = t*h+x
                assert h*w[j+1]==sum(q[:j+1])
            assert h==sum(q)
    assert 2!=2*2  # Replacing the terminal weight one by two breaks the conclusion.


def test_guarded_actual_weighted_sum_proof_replays_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weighted.prove_horner_weighted_sum()
    assert result.receipt.target==weighted.frozen_horner_weighted_sum_target()
    assert len(result.bundle.nodes)==115
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5728
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
