"""Actual two-shift convolution, sharp range and hostile proof controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_periodic_convolution as convolution


def test_exact_coefficients_are_constructed_with_five_finite_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = convolution.frozen_periodic_convolution_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==5 and type(conclusion) is Exists
    assert convolution.json_hash(encode_formula(target))==convolution.TARGET_SHA256
    assert len(convolution.canonical(encode_formula(target)))==7051
    contract = convolution.source_contract()
    assert contract["actual_coefficients_constructed"] is True
    assert contract["actual_initial_values_and_period_required"] is True
    assert contract["strict_index_bound_required"] is True
    assert contract["actual_head_tail_antidiagonal_transport"] is True
    assert contract["exp_composition_recurrence"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_reused_slice_definition_has_exact_expansion_and_hygiene():
    from sqrt2_power_definitions import parse_named
    r = convolution.definition_registry()
    assert convolution.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("i","a","b","c","N")
    alias = parse_named("NatAffineSlice(i,a,1,1,b,c,N)",names,r)
    explicit = parse_named("forall j x. Lt(j,N) -> BetaAt(b,c,j,x) -> BetaAt(i,a,1+1*j,x)",names,r)
    assert alias==explicit


def test_removed_zero_or_range_premise_is_rejected():
    for source in (convolution.NAMED_SOURCE.replace("BetaAt(ab,ac,0,0) -> ","",1),
                   convolution.NAMED_SOURCE.replace("Lt(S(S i),N) -> ","",1)):
        with patch.object(convolution,"NAMED_SOURCE",source),pytest.raises(ValueError):
            convolution.frozen_periodic_convolution_target()


def test_helpers_and_actual_sum_shift_and_convolution_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = convolution.definition_registry()
    assert {name:convolution.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in convolution.HELPER_SOURCES.items()}==convolution.HELPER_TARGET_SHA256
    found = set()
    for pin in convolution.ARCHIVES:
        rows = convolution.read_archive(pin)
        for name,source in convolution.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==convolution.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in convolution.ARCHIVES}=={"CV003","CV010"}


def test_forged_actual_archives_are_rejected():
    for original in convolution.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                convolution.read_archive(changed)


def test_periodic_model_and_required_initial_period_and_range_counterexamples():
    def coefficient(a,c,i):
        return sum(a[j]*c[i-j] for j in range(i+1) if j<len(a) and i-j<len(c))
    for N in range(3,10):
        for h in range(5):
            a = [0 if j%2==0 else h for j in range(N)]
            for shift in range(4):
                c = [(j*j+shift)%7 for j in range(N)]
                for i in range(N-2):
                    assert coefficient(a,c,i+2)==coefficient(a,c,i)+h*c[i+1]
    assert coefficient([1,2,1],[0,0,1],2)!=coefficient([1,2,1],[0,0,1],0)
    assert coefficient([0,2,5],[1,0,0],2)!=coefficient([0,2,5],[1,0,0],0)
    assert coefficient([0,2,0],[1,0,0],3)!=coefficient([0,2,0],[1,0,0],1)


def test_guarded_two_shift_proof_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = convolution.prove_periodic_convolution()
    assert result.receipt.target==convolution.frozen_periodic_convolution_target()
    assert len(result.bundle.nodes)==137
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7195
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
