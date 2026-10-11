"""Exact full-length homogeneous Horner product, retaining the extra factor."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_product as product


def test_exact_unconditional_full_horner_product_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = product.frozen_horner_product_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert product.json_hash(encode_formula(target))==product.TARGET_SHA256
    assert len(product.canonical(encode_formula(target)))==7338
    c = product.source_contract()
    assert c["actual_convolution_and_all_three_horner_traces_constructed"] is c["full_convolution_evaluation"] is True
    assert c["extra_multiplier_kept"] is c["empty_inputs_and_zero_multiplier_allowed"] is True
    assert c["actual_sum_product_and_weight_compatibility_replayed"] is True
    assert c["output_length"]=="L+M"
    assert c["truncated_product_evaluation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_unchanged_conservative_definition_dag():
    registry = product.definition_registry()
    assert product.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_omitted_multiplier_or_changed_trace_endpoint_is_rejected():
    for source in (product.NAMED_SOURCE.replace("z=t*(x*y)","z=x*y"),
                   product.NAMED_SOURCE.replace("BetaAt(chb,chc,L+M,z)","BetaAt(chb,chc,L,z)")):
        with patch.object(product,"NAMED_SOURCE",source),pytest.raises(ValueError):
            product.frozen_horner_product_target()


def test_exact_helpers_and_owned_actual_certificate_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = product.definition_registry()
    assert {name:product.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in product.HELPER_SOURCES.items()}==product.HELPER_TARGET_SHA256
    found = set()
    for pin in product.ARCHIVES:
        rows = product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==product.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in product.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                product.read_mixed_archive(changed)


def test_finite_product_model_with_empty_lengths_and_zero_multiplier():
    def horner(a,t):
        h = 0
        for v in a:
            h = t*h+v
        return h
    for L in range(6):
        for M in range(6):
            a,b = [i+1 for i in range(L)],[2*j+3 for j in range(M)]
            c = [sum(a[i]*b[k-i] for i in range(L) if 0<=k-i<M) for k in range(L+M)]
            for t in range(5):
                assert horner(c,t)==t*(horner(a,t)*horner(b,t))
    assert horner([3,10,8,0],2)!=horner([1,2],2)*horner([3,4],2)


def test_ordinary_replay_and_forged_product_ancestor_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = product.prove_horner_product()
    assert result.receipt.target==product.frozen_horner_product_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(product.ENDPOINT_SOURCES["convolution_total"],registry=product.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
