"""Unconditional same-witness weighted terms and actual Horner/sum values."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_constructed_horner_sum as constructed


def test_exact_unconditional_constructed_weighted_sum_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = constructed.frozen_constructed_horner_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and not premises and type(conclusion) is Exists
    assert constructed.json_hash(encode_formula(target))==constructed.TARGET_SHA256
    assert len(constructed.canonical(encode_formula(target)))==8561
    c = constructed.source_contract()
    for key in ("geometric_weights_and_actual_power_constructed","weighted_product_prefix_constructed",
                "horner_trace_and_endpoint_constructed","actual_sum_for_same_endpoint_proved",
                "same_witnesses_preserved","zero_multiplier_and_empty_prefix_allowed"):
        assert c[key] is True
    assert c["multiplication_evaluation_identity"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_geometric_data_preserved_and_definition_dag_coherent():
    from sqrt2_power_definitions import parse_named
    r = constructed.definition_registry()
    assert parse_named("forall t N. exists wb wc p. "+constructed.GEOMETRIC_DATA,registry=r)==parse_named(constructed.GEOMETRIC_SOURCE,registry=r)
    assert constructed.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_wrong_sum_table_or_endpoint_is_rejected():
    for source in (constructed.NAMED_SOURCE.replace("Sum(qb,qc,N,r)","Sum(ab,ac,N,r)"),
                   constructed.NAMED_SOURCE.replace("BetaAt(hb,hc,N,r)","BetaAt(hb,hc,N,p)")):
        with patch.object(constructed,"NAMED_SOURCE",source),pytest.raises(ValueError):
            constructed.frozen_constructed_horner_sum_target()


def test_helpers_and_actual_owned_constructors_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = constructed.definition_registry()
    assert {name:constructed.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in constructed.HELPER_SOURCES.items()}==constructed.HELPER_TARGET_SHA256
    found = set()
    for pin in constructed.ARCHIVES:
        rows = constructed.read_mixed_archive(pin)
        for name,source in constructed.ENDPOINT_SOURCES.items():
            if constructed.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==constructed.ENDPOINT_SOURCES.keys()


def test_changed_actual_archive_is_rejected():
    for original in constructed.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                constructed.read_mixed_archive(changed)


def test_actual_weight_and_product_prefix_construction_model():
    for a in ([],[0],[2],[1,4,0,5,3]):
        N = len(a)
        for t in range(5):
            w = [1]
            for _ in range(N):
                w = [t*x for x in w]+[1]
            q = []
            for j,x in enumerate(a):
                q.append(x*w[j+1])
            h = 0
            for x in a:
                h = t*h+x
            assert w[0]==t**N
            assert all(w[j]*t**j==t**N for j in range(N+1))
            assert h==sum(q)
            assert q==[x*t**(N-1-j) for j,x in enumerate(a)]


def test_guarded_unconditional_sum_proof_replays_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = constructed.prove_constructed_horner_sum()
    assert result.receipt.target==constructed.frozen_constructed_horner_sum_target()
    assert len(result.bundle.nodes)==137
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7321
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
