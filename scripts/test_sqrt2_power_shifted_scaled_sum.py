"""Actual sums, not the shifted-block value law taken as a premise."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_shifted_scaled_sum as sums


def test_exact_target_and_computational_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = sums.frozen_shifted_scaled_sum_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==3 and type(conclusion) is Exists
    assert sums.json_hash(encode_formula(target))==sums.TARGET_SHA256
    assert len(sums.canonical(encode_formula(target)))==4339
    c = sums.source_contract()
    assert c["actual_leading_and_trailing_zero_entries_required"] is c["actual_shifted_coefficient_scaling_required"] is True
    assert c["both_actual_sum_values_constructed"] is c["arbitrary_shift_block_tail_lengths_and_zero_scalar_allowed"] is True
    assert c["full_convolution_evaluation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_unchanged_conservative_definition_dependencies():
    registry = sums.definition_registry()
    assert sums.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert all("Sum(" not in source for source in (sums.LEADING,sums.MIDDLE,sums.TRAILING))


def test_changed_shift_or_sum_length_is_rejected():
    for source in (sums.NAMED_SOURCE.replace("BetaAt(ub,uc,s+j,c)","BetaAt(ub,uc,j,c)"),
                   sums.NAMED_SOURCE.replace("Sum(ub,uc,(s+N)+q,y)","Sum(ub,uc,N,y)")):
        with patch.object(sums,"NAMED_SOURCE",source),pytest.raises(ValueError):
            sums.frozen_shifted_scaled_sum_target()


def test_exact_helper_and_actual_owned_endpoint_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = sums.definition_registry()
    assert {name:sums.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in sums.HELPER_SOURCES.items()}==sums.HELPER_TARGET_SHA256
    found = set()
    for pin in sums.ARCHIVES:
        rows = sums.read_mixed_archive(pin)
        for name,source in sums.ENDPOINT_SOURCES.items():
            if sums.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,row in enumerate(rows) if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and rows[matches[0]][3]
            found.add(name)
    assert found==sums.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in sums.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                sums.read_mixed_archive(changed)


def test_finite_model_keeps_both_zero_margins_and_scaling():
    for s in range(5):
        for N in range(5):
            for q in range(5):
                for a in range(4):
                    source = [j*j+1 for j in range(N)]
                    shifted = [0]*s+[a*b for b in source]+[0]*q
                    assert len(shifted)==s+N+q and sum(shifted)==a*sum(source)
    assert sum([1,6,10])!=2*sum([3,5])
    assert sum([0,6,10,1])!=2*sum([3,5])


def test_ordinary_replay_and_forged_actual_ancestor_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = sums.prove_shifted_scaled_sum()
    assert result.receipt.target==sums.frozen_shifted_scaled_sum_target()
    assert len(result.bundle.nodes)==125
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6488
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(sums.ENDPOINT_SOURCES["zero_tail"],registry=sums.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
