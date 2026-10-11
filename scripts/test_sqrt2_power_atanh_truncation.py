"""One supplied atanh table has exact finite prefix/tail difference bounds."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_truncation as truncation


def test_exact_constructed_truncation_contract_and_fields():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_atanh_truncation_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==5 and len(premises)==1 and type(conclusion) is Exists
    assert len(truncation.OUTPUTS)==8 and len(truncation.PARTS)==12
    assert len(truncation.canonical(encode_formula(target)))==11471
    c=truncation.source_contract()
    assert c["supplied_atanh_table_preserved"] is c["actual_prefix_tail_whole_values_slice_and_powers_constructed"] is True
    assert c["actual_power_product_and_scaled_split_proved"] is c["zero_lengths_and_zero_denominator_allowed_for_natural_bounds"] is True
    assert c["code_number_equality_claimed"] is c["rational_denominator_validity_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_existing_registry_no_added_accuracy_predicate():
    from sqrt2_power_ternary_prefix_bound import definition_registry
    assert truncation.definition_registry()==definition_registry()
    assert truncation.source_contract()["new_definition_ids"]==[]
    assert truncation.source_contract()["definition_admissions"]==truncation.source_contract()["IR_parents_closed"]==0


def test_changed_actual_slice_power_or_cross_bound_is_rejected():
    original=truncation.NAMED_SOURCE
    for source in (original.replace("NatAtanhPrefix(d,ab,ac,M+N) -> ",""),
                   original.replace("NatAffineSlice(ab,ac,M,1,bb,bc,N)","NatAffineSlice(ab,ac,N,1,bb,bc,N)"),
                   original.replace("h=p*q","h=p+q"),
                   original.replace("z=q*x+y","z=q*y+x"),
                   original.replace("Le(p*z,h*x+d*h)","Le(p*z,h*x+d)")):
        assert source!=original
        with patch.object(truncation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            truncation.frozen_atanh_truncation_target()


def test_owned_actual_splitting_bound_and_power_addition_bodies():
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


def test_finite_same_table_model_including_empty_prefix_tail_and_zero_scale():
    from fractions import Fraction
    from math import lcm
    def horner(A):
        value=0
        for a in A:
            value=3*value+a
        return value
    for M in range(6):
        for N in range(6):
            for scale in (0,1,2,5):
                L=M+N;d=scale*lcm(*range(1,L,2))
                A=[2*d//i if i%2 else 0 for i in range(L)];B=A[M:]
                x,y,z=horner(A[:M]),horner(B),horner(A)
                p,q,h=3**M,3**N,3**L
                assert h==p*q and z==q*x+y and y+d<=d*q
                assert h*x<=p*z<=h*x+d*h
                if d:
                    difference=Fraction(3*z,d*h)-Fraction(3*x,d*p)
                    assert difference==Fraction(3*y,d*h) and 0<=difference<=Fraction(3,p)
    # Without the tail-bound premise the arithmetic upper bound fails.
    d=p=q=h=1;x=0;y=z=2
    assert h==p*q and z==q*x+y and p*z>h*x+d*h


def test_complete_ordinary_replay_without_new_induction_or_axioms():
    result=truncation.prove_atanh_truncation()
    assert result.receipt.target==truncation.frozen_atanh_truncation_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_cross_bound_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=truncation.prove_atanh_truncation();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
