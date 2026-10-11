"""Exact same-product recurrence at numerator t*x and denominator d*p."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_weighted_monomial_recurrence as recurrence


def test_exact_same_table_weighted_recurrence_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target = recurrence.frozen_weighted_monomial_recurrence_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==13 and len(premises)==5 and type(conclusion) is And
    assert recurrence.json_hash(encode_formula(target))==recurrence.TARGET_SHA256
    assert len(recurrence.canonical(encode_formula(target)))==8698
    c = recurrence.source_contract()
    assert c["denominator"]=="d*p" and c["numerator"]=="t*x" and c["initial_value"]=="w0*v"
    assert c["nonzero_monomial_scale_required"] is c["same_decoded_tables_throughout"] is True
    assert c["actual_composition_constructed"] is c["finite_sum_bound_claimed"] is c["closes_IR072"] is False


def test_existing_recurrence_definition_is_not_strengthened():
    from sqrt2_power_scaled_exp_terms import definition_registry
    assert recurrence.definition_registry()==definition_registry()
    c = recurrence.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==0
    assert c["analytic_limit_claim"] is False and c["zero_weight_denominator_allowed"] is True
    assert "~d=0" not in recurrence.NAMED_SOURCE


def test_dropped_scale_or_wrong_table_or_initial_value_is_rejected():
    for source in (recurrence.NAMED_SOURCE.replace("~p=0 -> ",""),
                   recurrence.NAMED_SOURCE.replace("NatScaledExpRecurrence(d*p,t*x","NatScaledExpRecurrence(d,t*x"),
                   recurrence.NAMED_SOURCE.replace("NatScaledExpRecurrence(d*p,t*x","NatScaledExpRecurrence(d*p,x"),
                   recurrence.NAMED_SOURCE.replace("BetaAt(zb,zc,0,w0*v)","BetaAt(zb,zc,0,w0)"),
                   recurrence.NAMED_SOURCE.replace("NatPointwiseProductPrefix(wb,wc,vb,vc,zb,zc,S N)","NatPointwiseProductPrefix(wb,wc,vb,vc,zc,zb,S N)")):
        with patch.object(recurrence,"NAMED_SOURCE",source),pytest.raises(ValueError):
            recurrence.frozen_weighted_monomial_recurrence_target()


def test_owned_actual_monomial_and_arithmetic_ancestor_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = recurrence.definition_registry();found = set()
    for pin in recurrence.ARCHIVES:
        rows = recurrence.read_mixed_archive(pin)
        for name,source in recurrence.ENDPOINT_SOURCES.items():
            if recurrence.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==recurrence.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in recurrence.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                recurrence.read_mixed_archive(pin)


def test_weighted_monomial_model_including_zero_denominator_and_horizon():
    from math import factorial
    for d in range(4):
        for p in range(1,4):
            for t in range(3):
                for x in range(3):
                    for N in range(6):
                        v = p**(N+1)
                        W = [factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
                        V = [v//p**j*(t*x)**j for j in range(N+1)]
                        Z = [w*y for w,y in zip(W,V)]
                        assert Z[0]==W[0]*v
                        assert all(((j+1)*(d*p))*Z[j+1]==(t*x)*Z[j] for j in range(N))
    d,p,t,x,N = 3,2,2,1,1
    W,V,Z = [3,1],[4,4],[12,4]
    assert (d*p)*Z[1]==(t*x)*Z[0]
    assert d*Z[1]!=(t*x)*Z[0] and (d*p)*Z[1]!=x*Z[0]


def test_ordinary_replay_and_forged_monomial_ancestor_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = recurrence.prove_weighted_monomial_recurrence()
    assert result.receipt.target==recurrence.frozen_weighted_monomial_recurrence_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(recurrence.MONOMIAL_SOURCE,registry=recurrence.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
