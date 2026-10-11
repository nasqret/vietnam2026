"""Nested rational endpoints use the actual supplied dyadic computations."""
from dataclasses import replace
from fractions import Fraction
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_dyadic_sqrt2_intervals as intervals


def test_exact_valid_nested_interval_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=intervals.frozen_dyadic_sqrt2_intervals_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==2 and type(conclusion) is And
    assert len(intervals.canonical(encode_formula(target)))==4740
    c=intervals.source_contract()
    assert c["both_supplied_computations_preserved"] is c["all_rational_denominators_proved_nonzero"] is True
    assert c["valid_lower_endpoint_nondecreasing"] is c["valid_upper_endpoint_nonincreasing"] is True
    assert c["new_induction_needed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_reused_rational_and_computation_definition_dag():
    from peano_lab.library.proof_bundle import encode_formula
    registry=intervals.definition_registry();seen=set()
    for name,d in registry.items():
        assert set(d.conceptual_dependencies)<=seen
        seen.add(name)
    assert len(registry)==10 and registry["DyadicSqrt2"].stable_id=="ND0446"
    for name,(identifier,digest) in intervals.RATIONAL_DEFINITION_PINS.items():
        assert registry[name].stable_id==identifier
        assert intervals.json_hash(encode_formula(registry[name].template_formula))==digest
    c=intervals.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_changed_precision_denominator_or_endpoint_direction_is_rejected():
    original=intervals.NAMED_SOURCE
    registry=intervals.definition_registry()
    for source in (original.replace("DyadicSqrt2(k+l,q,t)","DyadicSqrt2(l,q,t)"),
                   original.replace("IRatLe(s,0,d,t,0,q)","IRatLe(t,0,q,s,0,d)"),
                   original.replace("IRatLe(S t,0,q,S s,0,d)","IRatLe(S s,0,d,S t,0,q)"),
                   original.replace("S t,0,q","S t,0,d")):
        assert source!=original
        with patch.object(intervals,"definition_registry",return_value=registry),patch.object(intervals,"NAMED_SOURCE",source),pytest.raises(ValueError):
            intervals.frozen_dyadic_sqrt2_intervals_target()


def test_actual_refinement_valid_order_and_power_nonzero_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=intervals.definition_registry();found=set()
    for pin in intervals.ARCHIVES:
        rows=intervals.read_mixed_archive(pin)
        for name,source in intervals.ENDPOINT_SOURCES.items():
            if intervals.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            intervals.read_mixed_archive(altered)
    assert found==intervals.ENDPOINT_SOURCES.keys()


def test_finite_fraction_interval_models_including_equal_precisions():
    for k in range(9):
        d=2**k;s=isqrt(2*d*d)
        for l in range(7):
            q=2**(k+l);t=isqrt(2*q*q)
            assert Fraction(s,d)<=Fraction(t,q)<Fraction(t+1,q)<=Fraction(s+1,d)
            if l==0:
                assert Fraction(s,d)==Fraction(t,q) and Fraction(s+1,d)==Fraction(t+1,q)
    with pytest.raises(ZeroDivisionError):
        Fraction(1,0)


def test_complete_interval_replay_without_new_induction_or_axioms():
    result=intervals.prove_dyadic_sqrt2_intervals()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_rational_transport_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=intervals.prove_dyadic_sqrt2_intervals();node=result.provenance["helper_bundle_indices"]["orders"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
