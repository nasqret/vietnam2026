"""Independent scales are aligned by constructed data, not assumed code equality."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_cross_continuity as cross


def test_exact_cross_denominator_and_head_continuity_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=cross.frozen_exp_cross_continuity_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==14 and len(premises)==10 and type(conclusion) is And
    assert len(cross.canonical(encode_formula(target)))==5432
    c=cross.source_contract()
    assert c["two_supplied_recurrences_heads_and_sums_preserved"] is c["independent_denominators_and_heads_allowed"] is True
    assert c["actual_common_scale_tables_constructed"] is c["nonzero_argument_denominators_required"] is True
    assert c["common_denominator"]=="d*e" and c["common_initial_scale"]=="a0*b0"
    assert c["argument_gap"]=="d*y=e*x+g" and c["argument_bound"]=="y<=2*e"
    assert c["new_induction_needed"] is c["code_number_equality_claimed"] is c["rational_division_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_registry_without_hidden_cross_scale_or_accuracy_definition():
    from sqrt2_power_sum_linear_bound import definition_registry
    assert cross.definition_registry is definition_registry
    assert cross.definition_registry()
    c=cross.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_gap_denominator_head_normalization_or_interval_is_rejected():
    original=cross.NAMED_SOURCE;registry=cross.definition_registry()
    for source in (original.replace("~d=0 -> ",""),original.replace("~e=0 -> ",""),
                   original.replace("d*y=e*x+g","y=x+g"),
                   original.replace("Le(y,2*e) -> ",""),
                   original.replace("Le(b0*s,a0*t)","Le(s,t)"),
                   original.replace("9*(g*(a0*b0))","9*g")):
        assert source!=original
        with patch.object(cross,"definition_registry",return_value=registry),patch.object(cross,"NAMED_SOURCE",source),pytest.raises(ValueError):
            cross.frozen_exp_cross_continuity_target()


def test_owned_actual_rescaling_continuity_and_arithmetic_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=cross.definition_registry();found=set()
    for pin in cross.ARCHIVES:
        rows=cross.read_mixed_archive(pin)
        for name,source in cross.ENDPOINT_SOURCES.items():
            if cross.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            cross.read_mixed_archive(altered)
    assert found==cross.ENDPOINT_SOURCES.keys()


def test_finite_independent_denominator_head_and_zero_edge_models():
    from math import factorial
    for N in range(6):
        for d in range(1,4):
            for e in range(1,4):
                for x in range(2*d+1):
                    for y in range(2*e+1):
                        g=d*y-e*x
                        if g<0:
                            continue
                        for ca,cb in ((0,0),(0,2),(3,0),(1,1),(2,3)):
                            a0=ca*factorial(N)*d**N;b0=cb*factorial(N)*e**N
                            A=[a0*x**j//(d**j*factorial(j)) for j in range(N+1)]
                            B=[b0*y**j//(e**j*factorial(j)) for j in range(N+1)]
                            s,t=sum(A),sum(B)
                            assert b0*s<=a0*t
                            assert d*e*a0*t<=d*e*b0*s+9*g*a0*b0
    # d=0, x=y=g=0 makes A's recurrence vacuous: the lower bound fails.
    A,B=[1,2],[1,0]
    assert 1*sum(A)>1*sum(B)
    assert 1*0*A[1]==0*A[0] and 1*1*B[1]==0*B[0]
    # The same failure is possible with only e=0 (d=x=1,y=g=0).
    A,B=[1,1],[1,0]
    assert sum(A)>sum(B) and A[1]==A[0] and 0*B[1]==0*B[0]
    # Without the finite argument interval the constant nine is false.
    N=5;a0=b0=factorial(N);x=0;y=g=5
    s=a0;t=sum(b0*y**j//factorial(j) for j in range(N+1))
    assert a0*t>b0*s+9*g*a0*b0


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=cross.prove_exp_cross_continuity()
    assert result.receipt.target==result.target
    assert cross.json_hash(encode_formula(result.target))==cross.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_common_scale_alignment_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=cross.prove_exp_cross_continuity();node=result.provenance["helper_bundle_indices"]["aligned"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
