"""Argument and finite tail errors must retain independent computation data."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exp_two_error_bound as bound


def test_exact_independent_data_and_two_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=bound.frozen_exp_two_error_bound_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==16 and len(premises)==11 and type(conclusion) is And
    assert len(bound.canonical(encode_formula(target)))==7391
    c=bound.source_contract()
    assert c["two_supplied_recurrences_heads_sums_and_cutoff_power_preserved"] is c["independent_argument_denominators_initial_scales_and_horizons"] is True
    assert c["actual_middle_prefix_sum_constructed"] is c["only_natural_cross_products_asserted"] is True
    assert c["separated_formal_error"]=="9*g/(d*e)+2/p"
    assert c["prefix_degree"]=="m" and c["whole_degree"]=="m+N+1"
    assert c["new_induction_needed"] is c["code_number_equality_claimed"] is c["rational_validity_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_registry_without_error_in_a_new_definition():
    from sqrt2_power_exp_cross_continuity import definition_registry
    assert bound.definition_registry is definition_registry
    assert bound.definition_registry()
    c=bound.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_gap_interval_horizon_power_or_error_is_rejected():
    original=bound.NAMED_SOURCE;registry=bound.definition_registry()
    for source in (original.replace("d*y=e*x+g","y=x+g"),
                   original.replace("Le(y,e)","Le(y,2*e)"),
                   original.replace("Sum(bb,bc,S((S m)+N),t)","Sum(bb,bc,S(m+N),t)"),
                   original.replace("Pow(2,m,p) -> ",""),
                   original.replace("9*(g*p)+2*(d*e)","9*g+2*(d*e)"),
                   original.replace("9*(g*p)+2*(d*e)","9*(g*p)")):
        assert source!=original
        with patch.object(bound,"definition_registry",return_value=registry),patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_exp_two_error_bound_target()


def test_owned_actual_continuity_truncation_and_order_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=bound.definition_registry();found=set()
    for pin in bound.ARCHIVES:
        rows=bound.read_mixed_archive(pin)
        for name,source in bound.ENDPOINT_SOURCES.items():
            if bound.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            bound.read_mixed_archive(altered)
    assert found==bound.ENDPOINT_SOURCES.keys()


def test_finite_two_error_models_and_missing_interval_or_power_counterexamples():
    from math import factorial
    for m in range(5):
        for N in range(4):
            L=m+N+1;p=2**m
            for d,e in ((1,1),(2,3),(3,2)):
                for x in range(d+1):
                    for y in range(e+1):
                        g=d*y-e*x
                        if g<0:
                            continue
                        for ca,cb in ((0,0),(0,2),(3,0),(1,1),(2,3)):
                            a0=ca*factorial(m)*d**m;b0=cb*factorial(L)*e**L
                            s=sum(a0*x**j//(d**j*factorial(j)) for j in range(m+1))
                            t=sum(b0*y**j//(e**j*factorial(j)) for j in range(L+1))
                            assert b0*s<=a0*t
                            assert (d*e)*(p*(a0*t))<=(d*e)*(p*(b0*s))+(9*(g*p)+2*(d*e))*(a0*b0)
    # Equal arguments x=y=2 erase the continuity error but violate the tail interval.
    a0=1;b0=factorial(5);s=1;t=sum(b0*2**j//factorial(j) for j in range(6))
    assert a0*t>b0*s+2*a0*b0
    # An arbitrary p cannot replace the actual cutoff power (m=N=0, x=y=1).
    p=4;a0=b0=s=1;t=2
    assert p*a0*t>p*b0*s+2*a0*b0


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import encode_formula
    result=bound.prove_exp_two_error_bound()
    assert result.receipt.target==result.target
    assert bound.json_hash(encode_formula(result.target))==bound.TARGET_SHA256
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_two_error_arithmetic_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=bound.prove_exp_two_error_bound();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())


def test_source_inventory_sharing_preserves_the_exact_recursive_pin_map():
    first=bound.exp_two_error_bound_source_pins()
    assert first==bound._recursive_source_pins()==bound.exp_two_error_bound_source_pins()
    with pytest.raises(TypeError):
        bound._PIN_EXPECTATIONS["invented"]={}
    name=next(iter(bound._PIN_EXPECTATIONS))
    with pytest.raises(TypeError):
        bound._PIN_EXPECTATIONS[name]["sha256"]="0"*64


def test_repeated_pin_check_still_reads_current_files_and_rejects_changes():
    from io import BytesIO
    bound.exp_two_error_bound_source_pins()
    source=bound.ROOT/"scripts/sqrt2_power_exp_cross_continuity.py"
    original_open=type(source).open
    def changed(path,*args,**kwargs):
        if path==source:
            return BytesIO(b"changed source")
        return original_open(path,*args,**kwargs)
    with patch.object(type(source),"open",changed),pytest.raises(bound.ExpTwoErrorBoundError,match="current source differs"):
        bound.exp_two_error_bound_source_pins()
