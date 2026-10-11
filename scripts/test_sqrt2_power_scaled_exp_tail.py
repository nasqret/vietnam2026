"""Supplied scaled-exp terms have an actual bounded finite omitted tail."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_scaled_exp_tail as tail


def test_exact_supplied_finite_tail_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = tail.frozen_scaled_exp_tail_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and len(premises)==4 and type(conclusion) is Exists
    assert tail.json_hash(encode_formula(target))==tail.TARGET_SHA256
    assert len(tail.canonical(encode_formula(target)))==4016
    c = tail.source_contract()
    assert c["supplied_term_table_and_head_preserved"] is c["actual_tail_slice_and_sum_constructed"] is True
    assert c["actual_tail_ratio_proved_and_retained"] is c["nonzero_denominator_required"] is True
    assert c["cutoff_zero_allowed"] is c["first_omitted_term_decay_claimed"] is c["infinite_remainder_claimed"] is False


def test_exact_conservative_union_without_new_definitions():
    from sqrt2_power_scaled_exp_bound import definition_registry as exp
    from sqrt2_power_ratio_sum_bound import definition_registry as ratio
    registry = tail.definition_registry()
    assert set(registry)==set(exp())|set(ratio())
    for part in (exp(),ratio()):
        for name,d in part.items():
            assert registry[name].stable_id==d.stable_id and registry[name].template_formula==d.template_formula
    assert registry["NatScaledExpRecurrence"].stable_id=="ND0443"
    assert registry["NatRatioBoundPrefix"].stable_id=="ND0441"
    assert tail.source_contract()["new_definition_ids"]==[]
    assert tail.source_contract()["definition_admissions"]==tail.source_contract()["IR_parents_closed"]==0


def test_changed_guard_cutoff_horizon_or_tail_bound_is_rejected():
    original = tail.NAMED_SOURCE
    for source in (original.replace("~d=0 -> ",""),
                   original.replace("Le(x,d)","Le(x,2*d)"),
                   original.replace("NatScaledExpRecurrence(d,x,tb,tc,(S m)+N)","NatScaledExpRecurrence(d,x,tb,tc,m+N)"),
                   original.replace("NatAffineSlice(tb,tc,S m,1,ub,uc,S N)","NatAffineSlice(tb,tc,m,1,ub,uc,S N)"),
                   original.replace("Le(s,2*a)","Le(s,a)")):
        assert source!=original
        with patch.object(tail,"NAMED_SOURCE",source),pytest.raises(ValueError):
            tail.frozen_scaled_exp_tail_target()


def test_actual_owned_cancellation_slice_and_finite_sum_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = tail.definition_registry();found = set()
    for pin in tail.ARCHIVES:
        rows = tail.read_mixed_archive(pin)
        for name,source in tail.ENDPOINT_SOURCES.items():
            if tail.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered = dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            tail.read_mixed_archive(altered)
    assert found==tail.ENDPOINT_SOURCES.keys()


def test_finite_exponential_tail_model_and_required_guard_counterexamples():
    from math import factorial
    for d in range(1,5):
        for x in range(d+1):
            for m in range(4):
                for N in range(5):
                    M=m+1;L=M+N
                    T=[factorial(L)//factorial(j)*d**(L-j)*x**j for j in range(L+1)]
                    assert all(((j+1)*d)*T[j+1]==x*T[j] for j in range(L))
                    U=T[M:];assert len(U)==N+1 and U[0]==T[M]
                    assert all(2*U[i+1]<=U[i] for i in range(N))
                    assert sum(U)<=2*T[M]
    # d=x=0 makes the recurrence vacuous, so the nonzero guard is essential.
    assert 0*3==0*1 and sum([1,3])>2*1
    # x/d=3 is outside the allowed unit interval.
    T=[6,18,27,27]
    assert all((j+1)*T[j+1]==3*T[j] for j in range(3)) and sum(T[1:])>2*T[1]
    # A tail starting at index zero need not have the factor-two bound.
    assert sum([2,2,1])>2*2


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result = tail.prove_scaled_exp_tail()
    assert result.receipt.target==tail.frozen_scaled_exp_tail_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_tail_ratio_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=tail.prove_scaled_exp_tail();node=result.provenance["helper_bundle_indices"]["tail_ratio"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())


def test_forged_actual_order_cancellation_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=tail.prove_scaled_exp_tail()
    ancestor=parse_named(tail.ENDPOINT_SOURCES["mul_le_cancel"],registry=tail.definition_registry())
    matches=[n.node_id for n in result.bundle.nodes if n.target==ancestor];assert len(matches)==1
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==matches[0] else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
