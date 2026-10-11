"""Support-complete truncated products retain both exact scaling factors."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supported_horner_product as product


def test_exact_support_complete_constructed_scaled_product():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = product.frozen_supported_horner_product_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==11 and len(premises)==4 and type(conclusion) is Exists
    assert product.json_hash(encode_formula(target))==product.TARGET_SHA256
    assert len(product.canonical(encode_formula(target)))==10230
    c = product.source_contract()
    assert c["input_support_and_length_alignment_required"] is c["cutoff_covers_product_support_required"] is True
    assert c["actual_shorter_convolution_and_three_horner_values_constructed"] is c["actual_scaling_power_constructed"] is True
    assert c["zero_multiplier_and_empty_lengths_allowed"] is c["no_nonzero_factor_cancelled"] is True
    assert c["identity"]=="p*z=t*(x*y)" and c["length_alignment"]=="N+q=L+M"
    assert c["arbitrary_truncated_product_equality"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_unchanged_conservative_computation_and_support_dag():
    registry = product.definition_registry()
    assert product.source_contract()["new_definition_ids"]==[]
    assert registry["NatZeroAfter"].template_formula==product.upper_registry()["NatZeroAfter"].template_formula
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_omitted_scaling_or_support_completeness_is_rejected():
    for source in (product.NAMED_SOURCE.replace("p*z=t*(x*y)","z=t*(x*y)"),
                   product.NAMED_SOURCE.replace("p*z=t*(x*y)","p*z=x*y"),
                   product.NAMED_SOURCE.replace("Le(r+s,N) -> ",""),
                   product.NAMED_SOURCE.replace("N+q=L+M","N=L+M")):
        with patch.object(product,"NAMED_SOURCE",source),pytest.raises(ValueError):
            product.frozen_supported_horner_product_target()


def test_helpers_and_owned_actual_product_support_and_tail_bodies():
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


def test_changed_actual_archive_is_rejected():
    for original in product.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                product.read_mixed_archive(changed)


def test_scaled_product_model_and_missing_support_counterexample():
    def horner(a,t):
        h = 0
        for v in a:
            h = t*h+v
        return h
    for r in range(4):
        for s in range(4):
            for padding in range(3):
                a,b = [j+1 for j in range(r)]+[0]*padding,[2*j+1 for j in range(s)]+[0]*padding
                L,M = len(a),len(b)
                c = [sum(a[j]*b[i-j] for j in range(L) if 0<=i-j<M) for i in range(L+M)]
                for N in range(r+s,L+M+1):
                    q = L+M-N
                    for t in range(4):
                        assert t**q*horner(c[:N],t)==t*(horner(a,t)*horner(b,t))
    assert 3**2*horner([1,2],3)!=3*horner([1,1],3)**2
    assert horner([3,0],3)!=3*(horner([1,0],3)*horner([3,0],3))


def test_ordinary_replay_and_forged_full_product_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = product.prove_supported_horner_product()
    assert result.receipt.target==product.frozen_supported_horner_product_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(product.ENDPOINT_SOURCES["full_product"],registry=product.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
