"""Finite reciprocal error follows from direct error and actual root ranges."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2_reciprocal as reciprocal


def test_exact_supplied_reciprocal_modulus_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=reciprocal.frozen_dyadic_sqrt2_reciprocal_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==2 and type(conclusion) is And
    assert len(reciprocal.canonical(encode_formula(target)))==4604
    c=reciprocal.source_contract()
    assert c["both_supplied_actual_computations_preserved"] is c["all_used_denominators_proved_nonzero"] is c["reciprocal_order_reversed"] is True
    assert c["exact_natural_upper"]=="d*(d*t)<=d*(q*s)+s*t"
    assert c["new_induction_needed"] is c["real_reciprocal_identity_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_reciprocal_or_accuracy_definition():
    from sqrt2_power_dyadic_sqrt2 import definition_registry
    assert reciprocal.definition_registry is definition_registry
    c=reciprocal.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_changed_reciprocal_sign_denominator_guard_or_error_is_rejected():
    original=reciprocal.NAMED_SOURCE
    for source in (original.replace("~s=0","s=0"),original.replace("~t=0","t=0"),
                   original.replace("Le(q*s,d*t)","Le(d*t,q*s)"),
                   original.replace("d*(q*s)+s*t","d*(q*s)"),
                   original.replace("DyadicSqrt2(k+l,q,t)","DyadicSqrt2(l,q,t)")):
        assert source!=original
        with patch.object(reciprocal,"NAMED_SOURCE",source),pytest.raises(ValueError):
            reciprocal.frozen_dyadic_sqrt2_reciprocal_target()


def test_exact_direct_modulus_root_ranges_and_order_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=reciprocal.definition_registry();found=set()
    for pin in reciprocal.ARCHIVES:
        rows=reciprocal.read_mixed_archive(pin)
        for name,source in reciprocal.ENDPOINT_SOURCES.items():
            if reciprocal.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            reciprocal.read_mixed_archive(altered)
    assert found==reciprocal.ENDPOINT_SOURCES.keys()


def test_finite_reciprocal_and_unrestricted_arithmetic_models():
    for k in range(9):
        d=2**k;s=isqrt(2*d*d)
        for l in range(7):
            q=2**(k+l);t=isqrt(2*q*q)
            assert d!=0 and s!=0 and t!=0 and q*s<=d*t
            assert d*(d*t)<=d*(q*s)+s*t
            assert 0<=Fraction(d,s)-Fraction(q,t)<=Fraction(1,d)
    for d in range(5):
        for s in range(5):
            for q in range(5):
                for t in range(5):
                    if s*q<=t*d<=s*q+q and d<=s and q<=t:
                        assert q*s<=d*t and d*(d*t)<=d*(q*s)+s*t


def test_complete_reciprocal_replay_without_new_induction_or_axioms():
    result=reciprocal.prove_dyadic_sqrt2_reciprocal()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_reciprocal_arithmetic_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=reciprocal.prove_dyadic_sqrt2_reciprocal();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
