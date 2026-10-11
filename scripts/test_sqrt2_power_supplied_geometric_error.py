"""Actual supplied finite values get two valid rational error comparisons."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supplied_geometric_error as error


def test_exact_supplied_finite_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = error.frozen_supplied_geometric_error_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==14 and len(premises)==11 and type(conclusion) is Exists
    assert len(error.PARTS)==13
    assert error.json_hash(encode_formula(target))==error.TARGET_SHA256
    assert len(error.canonical(encode_formula(target)))==16505
    c = error.source_contract()
    assert c["supplied_coefficients_tail_and_values_preserved"] is c["actual_power_product_proved"] is True
    assert c["exact_prefix_tail_split_proved"] is c["all_rational_denominators_proved_nonzero"] is True
    assert c["approximation_or_composition_existence_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_rational_definition_only_and_no_hidden_accuracy():
    from sqrt2_power_rational_tail_majorant import definition_registry
    registry = error.definition_registry()
    assert registry==definition_registry()
    assert registry["IRatLe"].stable_id=="ND0444"
    assert tuple(registry["IRatLe"].conceptual_dependencies)==("IRatValid","Le")
    assert error.source_contract()["new_definition_ids"]==[]
    assert error.source_contract()["definition_admissions"]==0
    assert error.source_contract()["geometric_pattern_and_tail_bound_are_premises"] is True


def test_missing_guard_or_changed_scales_and_tail_are_rejected():
    original = error.NAMED_SOURCE
    for source in (original.replace("~z=0 -> ",""),
                   original.replace("NatHornerValue(tb,tc,3,S r,u)","NatHornerValue(tc,tb,3,S r,u)"),
                   original.replace("Pow(3,k,p)","Pow(3,S k,p)"),
                   original.replace("IRatLe(y,0,z*h,2*q+9*a,0,q)","IRatLe(y,0,h,2*q+9*a,0,q)"),
                   original.replace("IRatLe(2,0,1,y*p+z*h,0,(z*h)*p)","IRatLe(3,0,1,y*p+z*h,0,(z*h)*p)")):
        assert source!=original
        with patch.object(error,"NAMED_SOURCE",source),pytest.raises(ValueError):
            error.frozen_supplied_geometric_error_target()


def test_owned_actual_split_sandwich_power_and_order_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = error.definition_registry();found = set()
    for pin in error.ARCHIVES:
        rows = error.read_mixed_archive(pin)
        for name,source in error.ENDPOINT_SOURCES.items():
            if error.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered = dict(pin);altered["sha256"] = "0"*64
        with pytest.raises(ValueError):
            error.read_mixed_archive(altered)
    assert found==error.ENDPOINT_SOURCES.keys()


def test_actual_finite_horner_values_satisfy_both_rational_comparisons():
    from fractions import Fraction
    def horner(A):
        result = 0
        for a in A:
            result = 3*result+a
        return result
    for k in range(5):
        for r in range(5):
            for z in (1,2,7):
                N = k+1;J = N+r
                prefix = [z]+[2*z]*k;tail = [z*((i+2)%5) for i in range(r+1)]
                U = prefix+tail;x,y,u = horner(prefix),horner(U),horner(tail)
                p,h,q,a,b = 3**k,3**J,3**N,2**N,3**(r+1)
                assert x+z==2*z*p and len(U)==J+1 and h==p*b
                assert y==b*x+u and u*q<=9*a*z*h
                assert min(p,q,h,z*h,z*h*p)>0
                assert y+z*b==2*z*h+u
                assert Fraction(y,z*h)<=Fraction(2*q+9*a,q)
                assert 2<=Fraction(y*p+z*h,z*h*p)


def test_ordinary_replay_has_no_new_axiom_or_induction():
    result = error.prove_supplied_geometric_error()
    assert result.receipt.target==error.frozen_supplied_geometric_error_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_power_identity_and_false_target_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = error.prove_supplied_geometric_error()
    target = parse_named(error.ENDPOINT_SOURCES["power_add"],registry=error.definition_registry())
    matches = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(matches)==1
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==matches[0] else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
