"""Finite exponential sum error bounds retain recurrences, scales and actual sums."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_sum_continuity as continuity


def test_exact_common_scale_and_finite_sum_difference_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=continuity.frozen_exp_sum_continuity_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==12 and len(premises)==9 and type(conclusion) is And
    assert len(continuity.canonical(encode_formula(target)))==5187
    c=continuity.source_contract()
    assert c["two_supplied_recurrences_heads_and_sums_preserved"] is c["common_actual_initial_scale_required"] is True
    assert c["nonzero_common_denominator_required"] is c["actual_tail_slices_constructed"] is True
    assert c["pointwise_bound_and_sum_bound_separately_proved"] is c["zero_arguments_gap_head_and_degree_allowed"] is True
    assert c["argument_bound"]=="y<=2*d" and c["finite_difference"]=="d*t<=d*s+9*(g*a0)"
    assert c["independent_denominator_transport_claimed"] is c["rational_division_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_conservative_registry_without_new_continuity_definition():
    from sqrt2_power_sum_linear_bound import definition_registry
    assert continuity.definition_registry is definition_registry
    assert continuity.definition_registry()["NatLinearBound"].stable_id=="ND0445"
    c=continuity.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_guard_actual_sum_gap_or_error_scale_is_rejected():
    original=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for source in (original.replace("~d=0 -> ",""),
                   original.replace("Le(y,2*d) -> ",""),
                   original.replace("y=x+g","x=y+g"),
                   original.replace("BetaAt(bb,bc,0,a0) -> ",""),
                   original.replace("Sum(bb,bc,S N,t)","Sum(ab,ac,S N,t)"),
                   original.replace("Le(d*t,d*s+9*(g*a0))","Le(t,s+9*(g*a0))")):
        assert source!=original
        with patch.object(continuity,"definition_registry",return_value=registry),patch.object(continuity,"NAMED_SOURCE",source),pytest.raises(ValueError):
            continuity.frozen_exp_sum_continuity_target()


def test_owned_actual_term_sum_split_uniqueness_and_majorant_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found=set()
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            continuity.read_mixed_archive(altered)
    assert found==continuity.ENDPOINT_SOURCES.keys()


def test_finite_factorial_models_zero_cases_and_argument_guard_counterexample():
    from math import factorial
    def total(N,d,x,a0):
        return sum(a0*x**j//(d**j*factorial(j)) for j in range(N+1))
    for N in range(8):
        for d in (1,2,4):
            for y in range(2*d+1):
                for x in range(y+1):
                    for scale in (0,1,3):
                        a0=scale*factorial(N)*d**N;g=y-x
                        s,t=total(N,d,x,a0),total(N,d,y,a0)
                        assert s<=t and d*t<=d*s+9*g*a0
                        if not g or not N:
                            assert s==t
    # The same coefficient 9 is not a global bound for unrestricted arguments.
    N=5;d=1;x=0;y=g=5;a0=factorial(N)
    s,t=total(N,d,x,a0),total(N,d,y,a0)
    assert y>2*d and d*t>d*s+9*g*a0
    # Different initial scales defeat the zero-gap conclusion.
    assert total(1,1,1,2)>total(1,1,1,1)


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=continuity.prove_exp_sum_continuity()
    assert result.receipt.target==result.target
    assert continuity.json_hash(encode_formula(result.target))==continuity.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_tail_graph_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=continuity.prove_exp_sum_continuity();node=result.provenance["helper_bundle_indices"]["tail_graphs"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
