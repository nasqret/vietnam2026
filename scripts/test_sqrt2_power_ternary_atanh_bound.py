"""Actual ternary atanh values, sharp finite invariant, and negative controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_ternary_atanh_bound as bound


def test_exact_supplied_ternary_bound_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    target = bound.frozen_ternary_atanh_bound_target()
    binders,premises,_ = strip_target(target)
    assert binders==6 and len(premises)==3
    assert bound.json_hash(encode_formula(target))==bound.TARGET_SHA256
    assert len(bound.canonical(encode_formula(target)))==4077
    c = bound.source_contract()
    assert c["supplied_atanh_coefficients_value_and_power_preserved"] is True
    assert c["zero_denominator_allowed_for_natural_bound"] is c["no_division"] is True
    assert c["denominator_nonzero_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_definitions_have_no_new_or_hidden_accuracy_clause():
    from sqrt2_power_atanh_majorant import definition_registry
    assert bound.definition_registry()==definition_registry()
    assert bound.source_contract()["new_definition_ids"]==[]
    assert bound.source_contract()["definition_admissions"]==bound.source_contract()["IR_parents_closed"]==0
    assert bound.definition_registry()["NatBoundedPrefix"].stable_id=="ND0440"


def test_changed_base_power_scale_or_supplied_table_is_rejected():
    original = bound.NAMED_SOURCE
    for source in (original.replace("NatAtanhPrefix(d,ab,ac,S k) -> ",""),
                   original.replace("NatHornerValue(ab,ac,3,S k,y)","NatHornerValue(ac,ab,3,S k,y)"),
                   original.replace("Pow(3,S k,p)","Pow(3,k,p)"),
                   original.replace("Le(3*y+3*d,d*p)","Le(3*y+4*d,d*p)")):
        assert source!=original
        with patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_ternary_atanh_bound_target()


def test_owned_actual_prefix_and_order_ancestor_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = bound.definition_registry();rows = bound.read_mixed_archive(bound.ARCHIVES[0])
    for name,source in bound.ENDPOINT_SOURCES.items():
        assert bound.ENDPOINT_OWNERS[name]=="CV066"
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
    altered = dict(bound.ARCHIVES[0]);altered["sha256"]="0"*64
    with pytest.raises(ValueError):
        bound.read_mixed_archive(altered)


def test_finite_atanh_and_general_bounded_prefix_models():
    from itertools import product
    from math import lcm
    def horner(A):
        y = 0
        for a in A:
            y = 3*y+a
        return y
    for k in range(8):
        for scaling in (0,1,2,5):
            d = scaling*lcm(*range(1,k+1,2))
            A = [2*d//i if i%2 else 0 for i in range(k+1)]
            y,p = horner(A),3**(k+1)
            assert y+d<=d*3**k
            assert 3*y+3*d<=d*p
    for D in range(3):
        for k in range(5):
            for tail in product(range(2*D+1),repeat=k):
                assert horner((0,)+tail)+D<=D*3**k
            assert horner([0]+[2*D]*k)+D==D*3**k
    assert horner([1])+1>1  # Removing the zero head fails.
    assert horner([0,3])+1>3  # Replacing the coefficient bound 2D by 3D fails.


def test_ordinary_HA_replay_has_one_explicit_induction_no_axioms():
    result = bound.prove_ternary_atanh_bound()
    assert result.receipt.target==bound.frozen_ternary_atanh_bound_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_ternary_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = bound.prove_ternary_atanh_bound()
    node = result.provenance["helper_bundle_indices"]["all_prefixes"]
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
