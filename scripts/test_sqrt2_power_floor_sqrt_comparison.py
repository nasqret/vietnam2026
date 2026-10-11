"""Both square bounds are explicit and the floor-root computation is retained."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_floor_sqrt_comparison as comparison


def test_exact_supplied_floor_square_comparison_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=comparison.frozen_floor_sqrt_comparison_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==3 and type(conclusion) is And
    assert len(comparison.canonical(encode_formula(target)))==536
    c=comparison.source_contract()
    assert c["supplied_actual_floor_root_preserved"] is c["both_square_bound_premises_preserved"] is True
    assert c["lower_bound_nonstrict"] is c["upper_bound_strict"] is c["natural_decidable_order_replayed"] is True
    assert c["new_induction_needed"] is c["real_square_root_or_dyadic_accuracy_claim"] is c["closes_IR072"] is False


def test_original_floor_and_order_definitions_without_new_alias():
    from sqrt2_power_floor_sqrt import definition_registry
    assert comparison.definition_registry is definition_registry
    c=comparison.source_contract()
    assert c["reused_definition_ids"]==["PD0001","PD0002","PD0051"]
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0


def test_missing_or_nonstrict_upper_bound_is_rejected():
    original=comparison.NAMED_SOURCE
    for source in (original.replace("Le(a*a,n) -> ",""),original.replace("Lt(n,b*b)","Le(n,b*b)"),
                   original.replace("FloorSqrt(n,s) -> ",""),original.replace("Le(a,s)","Lt(a,s)")):
        assert source!=original
        with patch.object(comparison,"NAMED_SOURCE",source),pytest.raises(ValueError):
            comparison.frozen_floor_sqrt_comparison_target()


def test_actual_archived_decidable_order_and_square_monotonicity_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    rows=comparison.read_mixed_archive(comparison.FLOOR_ARCHIVE)
    registry=comparison.definition_registry()
    for name,source in comparison.ENDPOINT_SOURCES.items():
        ast=encode_formula(parse_named(source,registry=registry))
        matches=[r for r in rows if r[1]==ast]
        assert len(matches)==1 and matches[0][3]
    altered=dict(comparison.FLOOR_ARCHIVE);altered["sha256"]="0"*64
    with pytest.raises(ValueError):
        comparison.read_mixed_archive(altered)


def test_finite_models_and_necessity_of_strict_upper_square_bound():
    for n in range(100):
        s=isqrt(n)
        for a in range(s+2):
            for b in range(s+3):
                if a*a<=n<b*b:
                    assert a<=s<b
    n=s=b=1
    assert n<=b*b and not s<b


def test_complete_replay_uses_no_new_induction_or_axioms():
    result=comparison.prove_floor_sqrt_comparison()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_square_monotonicity_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=comparison.prove_floor_sqrt_comparison();node=result.provenance["helper_bundle_indices"]["square_mono"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
