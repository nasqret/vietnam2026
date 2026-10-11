"""Strict positive scaling, exact supplied roots and zero-input edge cases."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_floor_sqrt_scaling as scaling


def test_exact_supplied_positive_rescaling_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=scaling.frozen_floor_sqrt_scaling_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==3 and type(conclusion) is And
    assert len(scaling.canonical(encode_formula(target)))==721
    c=scaling.source_contract()
    assert c["positive_scale_required"] is c["two_supplied_actual_floor_roots_preserved"] is c["zero_input_and_root_allowed"] is True
    assert c["integer_bounds"]=="s*e<=t<(s+1)*e"
    assert c["new_induction_needed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_floor_definition_without_accuracy_or_nesting_alias():
    from sqrt2_power_floor_sqrt import definition_registry
    assert scaling.definition_registry is definition_registry
    c=scaling.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0
    assert set(scaling.definition_registry())=={"Le","Lt","FloorSqrt"}


def test_missing_positive_scale_or_changed_scaled_input_is_rejected():
    original=scaling.NAMED_SOURCE
    for source in (original.replace("~e=0 -> ",""),original.replace("n*(e*e)","n*e"),
                   original.replace("FloorSqrt(n,s) -> ",""),original.replace("Lt(t,(S s)*e)","Lt(t,s*e)")):
        assert source!=original
        with patch.object(scaling,"NAMED_SOURCE",source),pytest.raises(ValueError):
            scaling.frozen_floor_sqrt_scaling_target()


def test_actual_order_multiplication_and_comparison_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=scaling.definition_registry();found=set()
    for pin in scaling.ARCHIVES:
        rows=scaling.read_mixed_archive(pin)
        for name,source in scaling.ENDPOINT_SOURCES.items():
            if scaling.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        altered=dict(pin);altered["sha256"]="0"*64
        with pytest.raises(ValueError):
            scaling.read_mixed_archive(altered)
    assert found==scaling.ENDPOINT_SOURCES.keys()


def test_finite_rescaling_models_and_zero_scale_counterexample():
    for n in range(80):
        s=isqrt(n)
        for e in range(1,15):
            t=isqrt(n*e*e)
            assert s*e<=t<(s+1)*e
    n=s=t=e=0
    assert s==isqrt(n) and t==isqrt(n*e*e)
    assert not t<(s+1)*e


def test_complete_actual_body_replay_without_new_induction():
    result=scaling.prove_floor_sqrt_scaling()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_strict_multiplication_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=scaling.prove_floor_sqrt_scaling();node=result.provenance["helper_bundle_indices"]["mul_strict"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
