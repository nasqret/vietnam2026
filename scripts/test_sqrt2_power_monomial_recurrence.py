"""Same actual monomial values, exact scale, guarded ordinary cancellation."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_monomial_recurrence as recurrence


def test_exact_same_monomial_values_and_nonzero_scale_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    from sqrt2_power_full_composition_evaluation import MONOMIALS
    target = recurrence.frozen_monomial_recurrence_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and len(premises)==2 and type(conclusion) is And
    assert recurrence.MONOMIALS==MONOMIALS
    assert recurrence.json_hash(encode_formula(target))==recurrence.TARGET_SHA256
    assert len(recurrence.canonical(encode_formula(target)))==6620
    c = recurrence.source_contract()
    assert c["nonzero_scale_required"] is c["exact_CV061_monomial_premise"] is True
    assert c["same_decoded_row_values"] is c["actual_power_nonvanishing_and_guarded_cancellation"] is True
    assert c["actual_composition_constructed"] is c["finite_sum_bound_claimed"] is c["closes_IR072"] is False


def test_no_new_definition_or_analytic_assumption():
    from sqrt2_power_scaled_exp_terms import definition_registry
    assert recurrence.definition_registry()==definition_registry()
    c = recurrence.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==0
    assert c["analytic_limit_claim"] is False
    assert c["empty_prefix_allowed"] is c["zero_argument_and_base_allowed"] is True


def test_missing_guard_or_changed_scale_and_table_are_rejected():
    for source in (recurrence.NAMED_SOURCE.replace("~p=0 -> ",""),
                   recurrence.NAMED_SOURCE.replace("p*z=(t*x)*y","p*z=x*y"),
                   recurrence.NAMED_SOURCE.replace("BetaAt(vb,vc,S k,z)","BetaAt(vc,vb,S k,z)"),
                   recurrence.NAMED_SOURCE.replace("Lt(S k,K)","Lt(k,K)")):
        with patch.object(recurrence,"NAMED_SOURCE",source),pytest.raises(ValueError):
            recurrence.frozen_monomial_recurrence_target()


def test_owned_actual_power_nonvanishing_and_cancellation_bodies():
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


def test_scaled_monomial_model_and_essential_guard_and_factor():
    for p in range(1,5):
        for t in range(4):
            for x in range(4):
                for K in range(6):
                    v = p**(K+1)
                    values = [v//p**k*(t*x)**k for k in range(K)]
                    assert all(p**k*y==(v*t**k)*x**k for k,y in enumerate(values))
                    assert not K or values[0]==v
                    assert all(p*values[k+1]==(t*x)*values[k] for k in range(K-1))
    p,t,x,v,values = 0,1,1,0,[0,1,5]
    assert all(p**k*y==(v*t**k)*x**k for k,y in enumerate(values))
    assert p*values[2]!=(t*x)*values[1]
    assert 2*6==3*2*2 and 2*6!=2*2


def test_ordinary_replay_and_forged_power_nonvanishing_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = recurrence.prove_monomial_recurrence()
    assert result.receipt.target==recurrence.frozen_monomial_recurrence_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(recurrence.ENDPOINT_SOURCES["power_nonzero"],registry=recurrence.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
