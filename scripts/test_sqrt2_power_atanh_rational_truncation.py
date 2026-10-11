"""Actual finite atanh truncations have valid, explicitly scaled rational bounds."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_rational_truncation as truncation


def test_exact_valid_rational_truncation_contract_and_fields():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_atanh_rational_truncation_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==5 and len(premises)==2 and type(conclusion) is Exists
    assert len(truncation.OUTPUTS)==4 and len(truncation.PARTS)==8
    assert len(truncation.canonical(encode_formula(target)))==8331
    c=truncation.source_contract()
    assert c["supplied_atanh_table_preserved"] is c["actual_prefix_whole_values_and_powers_constructed"] is True
    assert c["all_rational_denominators_proved_nonzero"] is c["nonzero_denominator_required"] is True
    assert c["empty_prefix_and_empty_tail_allowed"] is True
    assert c["independent_code_equality_claimed"] is c["analytic_limit_claim"] is c["analytic_logarithm_identity"] is c["closes_IR072"] is False


def test_conservative_existing_registry_without_accuracy_predicate():
    from sqrt2_power_rational_tail_majorant import definition_registry
    assert truncation.definition_registry()==definition_registry()
    c=truncation.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_validity_actual_values_or_error_scale_is_rejected():
    original=truncation.NAMED_SOURCE
    for source in (original.replace("~d=0 -> ",""),
                   original.replace("NatAtanhPrefix(d,ab,ac,M+N) -> ",""),
                   original.replace("NatHornerValue(ab,ac,3,M,x)","NatHornerValue(ab,ac,3,N,x)"),
                   original.replace("~(d*p)=0","~p=0"),
                   original.replace("3*x+3*d","3*x+d"),
                   original.replace("3*z,0,d*h","3*z,0,d*p")):
        assert source!=original
        with patch.object(truncation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            truncation.frozen_atanh_rational_truncation_target()


def test_owned_actual_truncation_nonzero_and_rational_order_bodies():
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


def test_finite_fraction_model_including_empty_prefix_and_tail():
    from fractions import Fraction
    from math import lcm
    def horner(A):
        value=0
        for a in A:
            value=3*value+a
        return value
    for M in range(7):
        for N in range(7):
            for scale in (1,2,5):
                L=M+N;d=scale*lcm(*range(1,L,2))
                A=[2*d//i if i%2 else 0 for i in range(L)]
                x,z=horner(A[:M]),horner(A)
                p,h=3**M,3**L
                assert d*p>0 and d*h>0
                lower=Fraction(3*x,d*p);whole=Fraction(3*z,d*h)
                upper=Fraction(3*x+3*d,d*p)
                assert lower<=whole<=upper
                assert upper-lower==Fraction(3,3**M)
                if N==0:
                    assert lower==whole
    # A vanishing d is allowed by the natural bound but not rational validity.
    d=0;p=h=1
    assert d*p==d*h==0


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result=truncation.prove_atanh_rational_truncation()
    assert result.receipt.target==truncation.frozen_atanh_rational_truncation_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_rational_order_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=truncation.prove_atanh_rational_truncation();node=result.provenance["helper_bundle_indices"]["orders"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
