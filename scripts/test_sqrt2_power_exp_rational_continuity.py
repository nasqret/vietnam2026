"""Finite rational continuity requires genuine nonzero normalizing scales."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_rational_continuity as rational


def test_exact_rational_finite_continuity_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=rational.frozen_exp_rational_continuity_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==14 and len(premises)==12 and type(conclusion) is And
    assert len(rational.canonical(encode_formula(target)))==5930
    c=rational.source_contract()
    assert c["two_supplied_recurrences_heads_and_sums_preserved"] is c["independent_argument_denominators_and_initial_scales"] is True
    assert c["all_rational_denominators_proved_nonzero"] is c["initial_scales_required_nonzero"] is True
    assert c["finite_error"]=="9*g/(d*e)"
    assert c["new_induction_needed"] is c["code_number_equality_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_rational_validity_and_order_definitions_without_new_alias():
    from sqrt2_power_rational_tail_majorant import definition_registry
    assert rational.definition_registry is definition_registry
    registry=rational.definition_registry()
    assert registry["IRatValid"].stable_id=="ND0382" and registry["IRatLe"].stable_id=="ND0444"
    c=rational.source_contract()
    assert c["new_definition_ids"]==[] and c["reused_definition_ids"]==["ND0382","ND0444"]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_positive_heads_gap_or_error_denominator_is_rejected():
    original=rational.NAMED_SOURCE;registry=rational.definition_registry()
    for source in (original.replace("~a0=0 -> ",""),original.replace("~b0=0 -> ",""),
                   original.replace("d*y=e*x+g","y=x+g"),
                   original.replace("IRatLe(s,0,a0,t,0,b0)","IRatLe(s,0,b0,t,0,a0)"),
                   original.replace("(d*e)*s+(9*g)*a0","(d*e)*s+9*g"),
                   original.replace("0,(d*e)*a0)","0,d*e)")):
        assert source!=original
        with patch.object(rational,"definition_registry",return_value=registry),patch.object(rational,"NAMED_SOURCE",source),pytest.raises(ValueError):
            rational.frozen_exp_rational_continuity_target()


def test_owned_actual_cross_continuity_and_positive_order_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=rational.definition_registry();found=set()
    for pin in rational.ARCHIVES:
        rows=rational.read_mixed_archive(pin)
        for name,source in rational.ENDPOINT_SOURCES.items():
            if rational.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            rational.read_mixed_archive(altered)
    assert found==rational.ENDPOINT_SOURCES.keys()


def test_finite_fraction_models_and_unreduced_independent_denominators():
    from fractions import Fraction
    from math import factorial
    for N in range(6):
        for d,e in ((1,1),(2,3),(3,2),(6,9)):
            for x in range(2*d+1):
                for y in range(2*e+1):
                    g=d*y-e*x
                    if g<0:
                        continue
                    a0=2*factorial(N)*d**N;b0=3*factorial(N)*e**N
                    s=sum(a0*x**j//(d**j*factorial(j)) for j in range(N+1))
                    t=sum(b0*y**j//(e**j*factorial(j)) for j in range(N+1))
                    lower,whole=Fraction(s,a0),Fraction(t,b0)
                    upper=Fraction((d*e)*s+(9*g)*a0,(d*e)*a0)
                    assert upper==lower+Fraction(9*g,d*e)
                    assert lower<=whole<=upper
                    if not N or not g:
                        assert lower==whole
    with pytest.raises(ZeroDivisionError):
        Fraction(0,0)


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=rational.prove_exp_rational_continuity()
    assert result.receipt.target==result.target
    assert rational.json_hash(encode_formula(result.target))==rational.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_rational_order_transport_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=rational.prove_exp_rational_continuity();node=result.provenance["helper_bundle_indices"]["orders"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
