"""Finite rational truncation errors preserve two independent supplied inputs."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_independent_atanh_truncation as truncation


def test_exact_independent_input_and_rational_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_independent_atanh_truncation_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==12 and len(premises)==8 and type(conclusion) is And
    assert len(truncation.canonical(encode_formula(target)))==8913
    c=truncation.source_contract()
    assert c["two_supplied_atanh_tables_values_and_powers_preserved"] is c["independent_coefficient_and_history_codes_allowed"] is True
    assert c["independent_nonzero_scales_allowed"] is c["actual_value_and_power_uniqueness_used"] is True
    assert c["cross_scale_identity_proved"] is c["all_rational_denominators_proved_nonzero"] is c["empty_prefix_and_empty_tail_allowed"] is True
    assert c["code_number_equality_claimed"] is c["analytic_limit_claim"] is c["analytic_logarithm_identity"] is c["closes_IR072"] is False


def test_existing_conservative_registry_no_new_comparison_or_accuracy_definition():
    from sqrt2_power_atanh_rational_truncation import definition_registry
    assert truncation.definition_registry()==definition_registry()
    c=truncation.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_validity_input_scaling_power_or_error_is_rejected():
    original=truncation.NAMED_SOURCE
    for source in (original.replace("~e=0 -> ",""),
                   original.replace("NatAtanhPrefix(e,bb,bc,M+N)","NatAtanhPrefix(d,bb,bc,M+N)"),
                   original.replace("NatHornerValue(bb,bc,3,M+N,z)","NatHornerValue(ab,ac,3,M+N,z)"),
                   original.replace("Pow(3,M,p)","Pow(3,N,p)"),
                   original.replace("3*z,0,e*h","3*z,0,d*h"),
                   original.replace("3*x+3*d","3*x+d")):
        assert source!=original
        with patch.object(truncation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            truncation.frozen_independent_atanh_truncation_target()


def test_owned_actual_scaling_splitting_uniqueness_and_order_bodies():
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


def test_finite_independent_denominator_fraction_model_and_empty_parts():
    from fractions import Fraction
    from math import lcm
    def horner(A):
        result=0
        for a in A:
            result=3*result+a
        return result
    for M in range(8):
        for N in range(8):
            for scale_d,scale_e in ((1,1),(2,5),(7,3)):
                d=scale_d*lcm(*range(1,M,2));e=scale_e*lcm(*range(1,M+N,2))
                A=[2*d//i if i%2 else 0 for i in range(M)]
                B=[2*e//i if i%2 else 0 for i in range(M+N)]
                x,z=horner(A),horner(B);p,h=3**M,3**(M+N)
                lower=Fraction(3*x,d*p);whole=Fraction(3*z,e*h)
                assert lower<=whole<=Fraction(3*x+3*d,d*p)
                assert 0<=whole-lower<=Fraction(3,p)
                if N==0:
                    assert lower==whole
    # Even at equal lengths the raw integer numerators need not be equal.
    assert horner([0,2])!=horner([0,4])
    assert Fraction(3*horner([0,2]),9)==Fraction(3*horner([0,4]),18)


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result=truncation.prove_independent_atanh_truncation()
    assert result.receipt.target==truncation.frozen_independent_atanh_truncation_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_cross_orders_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=truncation.prove_independent_atanh_truncation();node=result.provenance["helper_bundle_indices"]["cross_orders"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
