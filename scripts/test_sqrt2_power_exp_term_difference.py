"""Finite exponential differences use actual recurrences and guarded cancellation."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_term_difference as difference


def test_exact_shared_head_finite_difference_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=difference.frozen_exp_term_difference_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==10 and len(premises)==6 and type(conclusion) is Forall
    assert len(difference.canonical(encode_formula(target)))==3048
    c=difference.source_contract()
    assert c["two_supplied_recurrences_preserved"] is c["common_actual_initial_scale_required"] is True
    assert c["explicit_nonnegative_argument_gap_required"] is c["nonzero_common_denominator_required"] is True
    assert c["all_available_positive_indices"] is c["term_monotonicity_proved"] is True
    assert c["zero_argument_gap_and_initial_scale_allowed"] is c["empty_horizon_allowed"] is True
    assert c["only_proved_nonzero_successor_times_denominator_cancelled"] is True
    assert c["derivative_claim"] is c["infinite_sum_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_conservative_recurrence_registry_without_difference_definition():
    from sqrt2_power_scaled_exp_bound import definition_registry
    assert difference.definition_registry is definition_registry
    assert difference.definition_registry()
    c=difference.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_nonzero_gap_shared_head_or_previous_index_is_rejected():
    original=difference.NAMED_SOURCE
    # Registry expansion has its own exact test; the mutations here concern
    # only the caller formula. Keep that checked immutable registry once.
    registry=difference.definition_registry()
    for source in (original.replace("~d=0 -> ",""),
                   original.replace("y=x+g -> ",""),
                   original.replace("BetaAt(bb,bc,0,a0) -> ",""),
                   original.replace("NatScaledExpRecurrence(d,y,bb,bc,N)","NatScaledExpRecurrence(d,x,bb,bc,N)"),
                   original.replace("BetaAt(bb,bc,k,c)","BetaAt(bb,bc,S k,c)"),
                   original.replace("Le(d*b,d*a+g*c)","Le(b,a+g*c)")):
        assert source!=original
        with patch.object(difference,"definition_registry",return_value=registry),patch.object(difference,"NAMED_SOURCE",source),pytest.raises(ValueError):
            difference.frozen_exp_term_difference_target()


def test_owned_actual_order_cancellation_and_sequence_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=difference.definition_registry();found=set()
    for pin in difference.ARCHIVES:
        rows=difference.read_mixed_archive(pin)
        for name,source in difference.ENDPOINT_SOURCES.items():
            assert difference.ENDPOINT_OWNERS[name]==pin["case"]
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            difference.read_mixed_archive(altered)
    assert found==difference.ENDPOINT_SOURCES.keys()


def test_finite_recurrence_models_and_essential_nonzero_shared_head_guards():
    from math import factorial
    for N in range(9):
        for d in (1,2,5):
            for x in range(5):
                for g in range(4):
                    y=x+g
                    for scale in (0,1,3):
                        a0=scale*factorial(N)*d**N
                        A=[a0*x**j//(d**j*factorial(j)) for j in range(N+1)]
                        B=[a0*y**j//(d**j*factorial(j)) for j in range(N+1)]
                        assert A[0]==B[0]==a0
                        for j in range(N):
                            assert (j+1)*d*A[j+1]==x*A[j]
                            assert (j+1)*d*B[j+1]==y*B[j]
                            assert A[j+1]<=B[j+1]
                            assert d*B[j+1]<=d*A[j+1]+g*B[j]
    # d=0 permits unconstrained later values and a false monotonicity claim.
    d=x=y=g=0;A=[0,1];B=[0,0]
    assert d*A[1]==x*A[0] and d*B[1]==y*B[0] and A[1]>B[1]
    # Unequal heads invalidate the zero-gap conclusion even with valid recurrences.
    d=x=y=1;g=0;A=[1,1];B=[2,2]
    assert d*A[1]==x*A[0] and d*B[1]==y*B[0]
    assert d*B[1]>d*A[1]+g*B[0]


def test_complete_ordinary_replay_with_one_explicit_induction_no_axioms():
    result=difference.prove_exp_term_difference()
    assert result.receipt.target==difference.frozen_exp_term_difference_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_induction_step_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=difference.prove_exp_term_difference();node=result.provenance["helper_bundle_indices"]["step"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
