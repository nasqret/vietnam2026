"""Uniform omitted-term bounds must refer to the caller's actual finite sums."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_truncation as truncation


def test_exact_supplied_prefix_whole_sum_and_power_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_exp_truncation_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==10 and len(premises)==7 and type(conclusion) is And
    assert len(truncation.canonical(encode_formula(target)))==5921
    c=truncation.source_contract()
    assert c["supplied_recurrence_head_two_sums_and_power_preserved"] is c["actual_tail_constructed_and_identified_by_value_uniqueness"] is True
    assert c["uniform_in_every_finite_extra_horizon"] is c["zero_argument_head_cutoff_and_extra_horizon_allowed"] is True
    assert c["prefix_length"]=="m+1" and c["whole_length"]=="m+N+2" and c["tail_length"]=="N+1"
    assert c["natural_bounds"]=="s<=t; p*t<=p*s+2*a0"
    assert c["new_induction_needed"] is c["code_number_equality_claimed"] is c["rational_validity_claimed"] is c["infinite_remainder_claimed"] is c["closes_IR072"] is False


def test_existing_registry_without_new_tail_or_accuracy_definition():
    from sqrt2_power_scaled_exp_tail_decay import definition_registry
    assert truncation.definition_registry is definition_registry
    assert truncation.definition_registry()
    c=truncation.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_guard_sum_horizon_power_or_tail_scale_is_rejected():
    original=truncation.NAMED_SOURCE;registry=truncation.definition_registry()
    for source in (original.replace("~d=0 -> ",""),original.replace("Le(x,d) -> ",""),
                   original.replace("Sum(ab,ac,S m,s)","Sum(ab,ac,m,s)"),
                   original.replace("Sum(ab,ac,S((S m)+N),t)","Sum(ab,ac,S(m+N),t)"),
                   original.replace("Pow(2,m,p)","Pow(3,m,p)"),
                   original.replace("p*s+2*a0","p*s+a0")):
        assert source!=original
        with patch.object(truncation,"definition_registry",return_value=registry),patch.object(truncation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            truncation.frozen_exp_truncation_target()


def test_owned_actual_tail_split_sum_and_power_uniqueness_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=truncation.definition_registry();found=set()
    for pin in truncation.ARCHIVES:
        rows=truncation.read_mixed_archive(pin)
        for name,source in truncation.ENDPOINT_SOURCES.items():
            if truncation.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            truncation.read_mixed_archive(altered)
    assert found==truncation.ENDPOINT_SOURCES.keys()


def test_finite_cutoff_models_zero_cases_and_required_guards():
    from math import factorial
    for m in range(7):
        for N in range(7):
            L=m+N+1
            for d in (1,2,4):
                for x in range(d+1):
                    for c in (0,1,3):
                        a0=c*factorial(L)*d**L
                        A=[a0*x**j//(d**j*factorial(j)) for j in range(L+1)]
                        s,t,p=sum(A[:m+1]),sum(A),2**m
                        assert s<=t and p*t<=p*s+2*a0
    # For zero denominator/argument the recurrence alone allows an arbitrary tail.
    A=[1,5]
    assert 0*A[1]==0*A[0] and sum(A)>A[0]+2*A[0]
    # The hypothesis x<=d is essential to the uniform coefficient two.
    A=[1,4]
    assert A[1]==4*A[0] and sum(A)>A[0]+2*A[0]
    # Replacing 2^m by 3^m also makes this exact bound false.
    m=1;L=6;a0=factorial(L)
    A=[a0//factorial(j) for j in range(L+1)];s=sum(A[:m+1]);t=sum(A)
    assert 3**m*t>3**m*s+2*a0


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=truncation.prove_exp_truncation()
    assert result.receipt.target==result.target
    assert truncation.json_hash(encode_formula(result.target))==truncation.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_supplied_sum_alignment_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=truncation.prove_exp_truncation();node=result.provenance["helper_bundle_indices"]["supplied_split"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
