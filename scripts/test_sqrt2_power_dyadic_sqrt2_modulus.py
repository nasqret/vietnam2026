"""An explicit finite modulus with actual denominators and no limit premise."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2_modulus as modulus


def test_exact_supplied_finite_dyadic_modulus_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=modulus.frozen_dyadic_sqrt2_modulus_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==2 and type(conclusion) is And
    assert len(modulus.canonical(encode_formula(target)))==4500
    c=modulus.source_contract()
    assert c["both_supplied_actual_computations_preserved"] is c["denominator_nonzero_conclusions"] is c["ordered_finite_precision_modulus"] is True
    assert c["exact_natural_bounds"]=="s*q<=t*d<=s*q+q"
    assert c["new_induction_needed"] is c["real_square_root_interpretation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_modulus_or_accuracy_definition():
    from sqrt2_power_dyadic_sqrt2_intervals import definition_registry
    assert modulus.definition_registry is definition_registry
    c=modulus.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_changed_denominator_error_or_precision_is_rejected():
    original=modulus.NAMED_SOURCE;registry=modulus.definition_registry()
    for source in (original.replace("Le(t*d,s*q+q)","Le(t*d,s*q)"),
                   original.replace("Le(s*q,t*d)","Le(t*d,s*q)"),
                   original.replace("DyadicSqrt2(k+l,q,t)","DyadicSqrt2(l,q,t)"),
                   original.replace("~q=0","q=0")):
        assert source!=original
        with patch.object(modulus,"definition_registry",return_value=registry),patch.object(modulus,"NAMED_SOURCE",source),pytest.raises(ValueError):
            modulus.frozen_dyadic_sqrt2_modulus_target()


def test_actual_interval_and_ordinary_order_transport_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=modulus.definition_registry();found=set()
    for pin in modulus.ARCHIVES:
        rows=modulus.read_mixed_archive(pin)
        for name,source in modulus.ENDPOINT_SOURCES.items():
            if modulus.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            modulus.read_mixed_archive(altered)
    assert found==modulus.ENDPOINT_SOURCES.keys()


def test_finite_cross_product_and_fraction_modulus_models():
    for k in range(9):
        d=2**k;s=isqrt(2*d*d)
        for l in range(7):
            q=2**(k+l);t=isqrt(2*q*q)
            assert d!=0 and q!=0 and s*q<=t*d<=s*q+q
            assert 0<=Fraction(t,q)-Fraction(s,d)<=Fraction(1,d)
            if l==0:
                assert t*d==s*q


def test_complete_modulus_replay_without_new_induction_or_axioms():
    result=modulus.prove_dyadic_sqrt2_modulus()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_rational_elimination_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=modulus.prove_dyadic_sqrt2_modulus();node=result.provenance["helper_bundle_indices"]["positive_natural"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
