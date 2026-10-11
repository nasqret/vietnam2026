"""The fixed shift threshold is reconstructed, never a trusted ground oracle."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_precision_threshold as threshold


def test_exact_fixed_power_threshold_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=threshold.frozen_fixed_precision_threshold_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and len(premises)==1 and type(conclusion) is And
    assert len(threshold.canonical(encode_formula(target)))==2285
    c=threshold.source_contract()
    assert c["actual_supplied_eighth_power_preserved"] is c["actual_fifth_power_constructed"] is True
    assert c["ground_evaluator_max_value"]==32 and c["fixed_unrolling_steps"]==5
    assert c["ground_evaluation_is_proof_authority"] is c["unary_256_introduced"] is False
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_six_definition_power_dag_is_reused():
    from sqrt2_power_positive_power_comparison import definition_registry
    before=definition_registry();after=threshold.definition_registry();seen=set();ids=set()
    assert len(after)==6 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert threshold.source_contract()["new_definition_ids"]==[]


def test_target_rejects_changed_base_exponent_or_threshold():
    source=threshold.NAMED_SOURCE
    for changed in (source.replace("Pow(2,8,v)","Pow(2,0,v)"),source.replace("Pow(2,8,v)","Pow(1,8,v)"),
                    source.replace("Le(((9*3)+2),v)","Le(v,((9*3)+2))"),source.replace("~v=0", "v=0")):
        assert changed!=source
        with patch.object(threshold,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            threshold.frozen_fixed_precision_threshold_target()


def test_actual_power_and_order_ancestor_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=threshold.definition_registry();found=set()
    for pin in threshold.ARCHIVES:
        rows=threshold.read_mixed_archive(pin)
        for name,source in threshold.ENDPOINT_SOURCES.items():
            if threshold.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            threshold.read_mixed_archive(bad)
    assert found==threshold.ENDPOINT_SOURCES.keys()


def test_tiny_ground_reconstruction_is_checked_by_the_unchanged_kernel():
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Eq
    from peano_lab.kernel.terms import Add,Mul
    for a in range(4):
        for b in range(4):
            for left,right in ((Add(threshold._n(a),threshold._n(b)),threshold._n(a+b)),
                               (Mul(threshold._n(a),threshold._n(b)),threshold._n(a*b))):
                assert check((),threshold._ground_equal(left,right),Eq(left,right))


def test_tiny_evaluator_rejects_false_open_large_or_deep_inputs():
    from peano_lab.kernel.terms import Add,Var,Zero
    for value in (-1,33,True,1.5):
        with pytest.raises(ValueError):
            threshold._n(value)
    deep=Zero()
    for _ in range(65):
        deep=Add(deep,Zero())
    broad=Zero()
    for _ in range(9):
        broad=Add(broad,broad)
    for left,right in ((threshold._n(1),Zero()),(Var(0),Zero()),
                       (Add(threshold._n(32),threshold._n(1)),Zero()),(deep,Zero()),(broad,Zero())):
        with pytest.raises(ValueError):
            threshold._ground_equal(left,right)


def test_fixed_unrolling_keeps_existential_elimination_outside_equality_inference():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    registry=threshold.definition_registry();deps=threshold.HELPER_DEPENDENCIES["power_five"]
    target=parse_named(threshold.HELPER_SOURCES["power_five"],registry=registry)
    for name in reversed(deps):
        target=Imp(parse_named(threshold.ENDPOINT_SOURCES[name],registry=registry),target)
    proof=threshold.introduce(threshold.Scope(),(),deps,threshold._power_five)
    assert check((),proof,target)


def test_complete_threshold_replay_needs_no_new_induction_or_axiom():
    result=threshold.prove_fixed_precision_threshold()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_small_arithmetic_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=threshold.prove_fixed_precision_threshold();node=result.provenance["helper_bundle_indices"]["constant_bound"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
