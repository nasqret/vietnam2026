"""A bounded ternary tail needs no zero-head assumption, including length zero."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_ternary_prefix_bound as bound


def test_exact_arbitrary_ternary_prefix_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target=bound.frozen_ternary_prefix_bound_target()
    binders,premises,_=strip_target(target)
    assert binders==6 and len(premises)==3
    assert len(bound.canonical(encode_formula(target)))==3726
    c=bound.source_contract()
    assert c["supplied_coefficients_horner_value_and_power_preserved"] is True
    assert c["empty_prefix_and_zero_bound_allowed"] is c["no_division"] is True
    assert c["zero_head_required"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_unchanged_conservative_registry_no_hidden_zero_head():
    from sqrt2_power_ternary_atanh_bound import definition_registry
    assert bound.definition_registry()==definition_registry()
    assert bound.source_contract()["new_definition_ids"]==[]
    assert bound.source_contract()["definition_admissions"]==bound.source_contract()["IR_parents_closed"]==0
    assert "BetaAt(ab,ac,0,0)" not in bound.NAMED_SOURCE


def test_changed_coefficient_bound_base_or_scaling_is_rejected():
    original=bound.NAMED_SOURCE
    for source in (original.replace("NatBoundedPrefix(ab,ac,2*D,N)","NatBoundedPrefix(ab,ac,3*D,N)"),
                   original.replace("NatHornerValue(ab,ac,3,N,y)","NatHornerValue(ab,ac,2,N,y)"),
                   original.replace("Pow(3,N,p)","Pow(3,S N,p)"),
                   original.replace("Le(y+D,D*p)","Le(S(y+D),D*p)")):
        assert source!=original
        with patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_ternary_prefix_bound_target()


def test_actual_owned_ternary_step_and_value_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=bound.definition_registry();rows=bound.read_mixed_archive(bound.ARCHIVES[0])
    for name,source in bound.ENDPOINT_SOURCES.items():
        ast=encode_formula(parse_named(source,registry=registry))
        matches=[row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3] and bound.ENDPOINT_OWNERS[name]=="CV086"
    altered=dict(bound.ARCHIVES[0]);altered["sha256"]="0"*64
    with pytest.raises(ValueError):
        bound.read_mixed_archive(altered)


def test_all_small_bounded_prefixes_and_sharpness_without_zero_head():
    from itertools import product
    def horner(A):
        y=0
        for a in A:
            y=3*y+a
        return y
    for D in range(3):
        for N in range(6):
            for A in product(range(2*D+1),repeat=N):
                assert horner(A)+D<=D*3**N
            assert horner([2*D]*N)+D==D*3**N
    assert horner([2])+1==3 and [2][0]!=0
    assert horner([3])+1>3  # A coefficient bound 3D is too weak.


def test_ordinary_replay_has_one_explicit_induction_and_no_new_axiom():
    result=bound.prove_ternary_prefix_bound()
    assert result.receipt.target==bound.frozen_ternary_prefix_bound_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_prefix_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=bound.prove_ternary_prefix_bound();node=result.provenance["helper_bundle_indices"]["all_prefixes"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
