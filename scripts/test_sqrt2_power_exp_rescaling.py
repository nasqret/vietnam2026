"""Exponential rescaling constructs data and proves the recurrence and sum law."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_rescaling as scaling


def test_exact_constructed_rescaling_contract_and_fields():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=scaling.frozen_exp_rescaling_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==9 and len(premises)==3 and type(conclusion) is Exists
    assert len(scaling.OUTPUTS)==3 and len(scaling.PARTS)==5
    assert len(scaling.canonical(encode_formula(target)))==5726
    c=scaling.source_contract()
    assert c["supplied_recurrence_head_and_sum_preserved"] is c["actual_scaled_table_and_sum_constructed"] is True
    assert c["pointwise_relation_constructed_not_assumed"] is c["zero_denominator_factors_and_scalars_allowed"] is c["zero_degree_allowed"] is True
    assert c["denominator"]=="d*f" and c["numerator"]=="f*x" and c["sum_identity"]=="t=c*s"
    assert c["new_induction_needed"] is c["code_number_equality_claimed"] is c["rational_validity_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_conservative_graph_registry_no_hidden_sum_definition():
    from sqrt2_power_sum_linear_bound import definition_registry
    assert scaling.definition_registry is definition_registry
    assert scaling.definition_registry()
    c=scaling.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_supplied_sum_or_recurrence_head_and_sum_scale_is_rejected():
    original=scaling.NAMED_SOURCE;registry=scaling.definition_registry()
    for source in (original.replace("Sum(ab,ac,S N,s) -> ",""),
                   original.replace("NatScaledExpRecurrence(d*f,f*x,ub,uc,N)","NatScaledExpRecurrence(d*f,x,ub,uc,N)"),
                   original.replace("NatScaledExpRecurrence(d*f,f*x,ub,uc,N)","NatScaledExpRecurrence(d,f*x,ub,uc,N)"),
                   original.replace("BetaAt(ub,uc,0,c*a0)","BetaAt(ub,uc,0,a0)"),
                   original.replace("Sum(ub,uc,S N,t)","Sum(ab,ac,S N,t)"),
                   original.replace("t=c*s","t=s")):
        assert source!=original
        with patch.object(scaling,"definition_registry",return_value=registry),patch.object(scaling,"NAMED_SOURCE",source),pytest.raises(ValueError):
            scaling.frozen_exp_rescaling_target()


def test_owned_actual_prefix_constructor_linearity_and_arithmetic_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=scaling.definition_registry();found=set()
    for pin in scaling.ARCHIVES:
        rows=scaling.read_mixed_archive(pin)
        for name,source in scaling.ENDPOINT_SOURCES.items():
            if scaling.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            scaling.read_mixed_archive(altered)
    assert found==scaling.ENDPOINT_SOURCES.keys()


def test_finite_models_including_zero_denominators_scalars_and_argument_factors():
    from math import factorial
    for N in range(7):
        for d in range(4):
            for x in range(4):
                if d:
                    a0=factorial(N)*d**N
                    A=[a0*x**j//(d**j*factorial(j)) for j in range(N+1)]
                elif not x:
                    A=[j*j+1 for j in range(N+1)]
                else:
                    A=[0]*N+[7]
                for c in (0,1,3):
                    for f in (0,1,5):
                        U=[c*a for a in A]
                        assert U[0]==c*A[0] and sum(U)==c*sum(A)
                        for j in range(N):
                            assert (j+1)*d*A[j+1]==x*A[j]
                            assert ((j+1)*(d*f))*U[j+1]==(f*x)*U[j]
    # Scaling the denominator alone changes the recurrence.
    A=[2,1];d=2;x=1;f=3
    assert d*A[1]==x*A[0] and (d*f)*A[1]!=x*A[0]


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=scaling.prove_exp_rescaling()
    assert result.receipt.target==result.target
    assert scaling.json_hash(encode_formula(result.target))==scaling.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_scaled_recurrence_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=scaling.prove_exp_rescaling();node=result.provenance["helper_bundle_indices"]["recurrence"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
