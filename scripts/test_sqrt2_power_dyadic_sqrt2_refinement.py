"""Dyadic refinement keeps the actual supplied computations and both bounds."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2_refinement as refinement


def test_exact_ordered_supplied_dyadic_refinement_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=refinement.frozen_dyadic_sqrt2_refinement_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==2 and type(conclusion) is Exists
    assert len(refinement.canonical(encode_formula(target)))==6207
    c=refinement.source_contract()
    assert c["both_supplied_actual_computations_preserved"] is c["intervening_power_constructed"] is c["actual_denominator_product_proved"] is True
    assert c["scale_nonzero_proved"] is c["zero_precision_and_increment_allowed"] is True
    assert c["new_induction_needed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_computation_definition_without_nesting_assumption():
    from sqrt2_power_dyadic_sqrt2 import definition_registry
    assert refinement.definition_registry is definition_registry
    assert refinement.definition_registry()["DyadicSqrt2"].stable_id=="ND0446"
    c=refinement.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_changed_precision_alignment_power_or_denominator_product_is_rejected():
    original=refinement.NAMED_SOURCE
    for source in (original.replace("DyadicSqrt2(k+l,q,t)","DyadicSqrt2(l,q,t)"),
                   original.replace("DyadicSqrt2(k,d,s) -> ",""),original.replace("Pow(2,l,e)","Pow(3,l,e)"),
                   original.replace("q=d*e","q=d+e"),original.replace("Lt(t,(S s)*e)","Lt(t,s*e)")):
        assert source!=original
        with patch.object(refinement,"NAMED_SOURCE",source),pytest.raises(ValueError):
            refinement.frozen_dyadic_sqrt2_refinement_target()


def test_exact_power_addition_positivity_and_rescaling_bodies_are_replayed():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=refinement.definition_registry();found=set()
    for pin in refinement.ARCHIVES:
        rows=refinement.read_mixed_archive(pin)
        for name,source in refinement.ENDPOINT_SOURCES.items():
            if refinement.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            refinement.read_mixed_archive(altered)
    assert found==refinement.ENDPOINT_SOURCES.keys()


def test_finite_refinement_models_including_equal_precisions():
    for k in range(9):
        d=2**k;s=isqrt(2*d*d)
        for l in range(7):
            e=2**l;q=2**(k+l);t=isqrt(2*q*q)
            assert e!=0 and q==d*e and s*e<=t<(s+1)*e
            if l==0:
                assert (q,t)==(d,s)


def test_complete_refinement_replay_without_new_induction_or_axioms():
    result=refinement.prove_dyadic_sqrt2_refinement()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_refinement_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=refinement.prove_dyadic_sqrt2_refinement();node=result.provenance["helper_bundle_indices"]["SQ006"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
