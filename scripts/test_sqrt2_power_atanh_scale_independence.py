"""Independent actual coefficient encodings preserve normalized finite values."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_scale_independence as scaling


def test_exact_supplied_value_contract_and_natural_cross_identity():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=scaling.frozen_atanh_scale_independence_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==10 and len(premises)==4 and type(conclusion) is Eq
    assert len(scaling.canonical(encode_formula(target)))==4107
    c=scaling.source_contract()
    assert c["two_actual_atanh_prefixes_required"] is c["two_supplied_horner_values_preserved"] is True
    assert c["independent_coefficient_and_history_codes_allowed"] is c["zero_scales_base_and_empty_prefix_allowed"] is True
    assert c["only_proved_nonzero_odd_index_cancelled"] is c["all_row_linearity_reused"] is True
    assert c["exact_identity"]=="e*x=d*y"
    assert c["code_number_equality_claimed"] is c["rational_denominator_validity_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_existing_registry_without_equal_code_or_accuracy_definition():
    from sqrt2_power_atanh_truncation import definition_registry
    assert scaling.definition_registry()==definition_registry()
    c=scaling.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_scale_supplied_prefix_or_history_is_rejected():
    original=scaling.NAMED_SOURCE
    for source in (original.replace("NatAtanhPrefix(e,bb,bc,N) -> ",""),
                   original.replace("NatAtanhPrefix(e,bb,bc,N)","NatAtanhPrefix(d,bb,bc,N)"),
                   original.replace("NatHornerValue(bb,bc,t,N,y)","NatHornerValue(ab,ac,t,N,y)"),
                   original.replace("NatHornerValue(ab,ac,t,N,x)","NatHornerValue(ab,ac,t,S N,x)"),
                   original.replace("e*x=d*y","d*x=e*y"),
                   original.replace("e*x=d*y","x=y")):
        assert source!=original
        with patch.object(scaling,"NAMED_SOURCE",source),pytest.raises(ValueError):
            scaling.frozen_atanh_scale_independence_target()


def test_owned_actual_parity_cancellation_and_all_row_linearity_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=scaling.definition_registry();found=set()
    for pin in scaling.ARCHIVES:
        rows=scaling.read_mixed_archive(pin)
        for name,source in scaling.ENDPOINT_SOURCES.items():
            if scaling.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            scaling.read_mixed_archive(altered)
    assert found==scaling.ENDPOINT_SOURCES.keys()


def test_finite_two_scale_model_zero_cases_and_essential_odd_guard():
    from fractions import Fraction
    from math import lcm
    def horner(A,t):
        result=0
        for a in A:
            result=t*result+a
        return result
    for N in range(10):
        common=lcm(*range(1,N,2))
        for d in (0,common,2*common,5*common):
            for e in (0,common,3*common,7*common):
                A=[2*d//i if i%2 else 0 for i in range(N)]
                B=[2*e//i if i%2 else 0 for i in range(N)]
                assert all(e*a==d*b for a,b in zip(A,B))
                for t in (0,1,3,5):
                    x,y=horner(A,t),horner(B,t)
                    assert e*x==d*y
                    if d and e:
                        assert Fraction(x,d)==Fraction(y,e)
    # Cancelling zero would justify a false coefficient identity.
    i,e,d,a,b=0,1,1,0,1
    assert i*(e*a)==i*(d*b) and e*a!=d*b


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result=scaling.prove_atanh_scale_independence()
    assert result.receipt.target==scaling.frozen_atanh_scale_independence_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_coefficient_cross_identity_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=scaling.prove_atanh_scale_independence();node=result.provenance["helper_bundle_indices"]["coefficient_cross"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
