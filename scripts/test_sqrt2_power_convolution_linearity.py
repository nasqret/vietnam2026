"""Exact weighted convolution, ordinary proof replay, and adversarial controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_linearity as linear


def test_exact_target_constructs_three_coefficients_from_pointwise_relation():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = linear.frozen_convolution_linearity_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==14 and len(premises)==1 and type(conclusion) is Exists
    assert linear.json_hash(encode_formula(target))==linear.TARGET_SHA256
    assert len(linear.canonical(encode_formula(target)))==9200
    contract = linear.source_contract()
    assert contract["actual_pointwise_relation_required"] is True
    assert contract["all_three_coefficients_constructed"] is True
    assert contract["positive_weights_required"] is False
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_exact_helper_targets_and_hygienic_right_input_codes():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = linear.definition_registry()
    assert {name:linear.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in linear.HELPER_SOURCES.items()}==linear.HELPER_TARGET_SHA256
    assert linear.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("ab","ac","L","db","dc","M","i","u")
    aliased = parse_named("NatConvolutionCoefficient(ab,ac,L,db,dc,M,i,u)",names,r)
    explicit = parse_named("exists x y. PolynomialDiagonalPrefix(ab,ac,L,db,dc,M,i,x,y,S i) /\\ Sum(x,y,S i,u)",names,r)
    assert aliased==explicit


def test_removed_pointwise_premise_and_wrong_weighted_total_are_rejected():
    for wrong in (linear.NAMED_SOURCE.replace(linear.POINTWISE+" -> ",""),linear.NAMED_SOURCE.replace("gamma*w=alpha*u+beta*v","gamma*w=alpha*u*beta*v")):
        assert wrong!=linear.NAMED_SOURCE
        with patch.object(linear,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            linear.frozen_convolution_linearity_target()


def test_actual_convolution_and_sum_linearity_dependency_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = linear.definition_registry()
    found = set()
    for pin in linear.ARCHIVES:
        rows = linear.read_archive(pin)
        for name,source in linear.ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=r))
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==linear.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in linear.ARCHIVES}=={"CV003","CV006"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in linear.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                linear.read_archive(changed)


def test_finite_weighted_convolution_model_including_zero_weights_and_lengths():
    seqs = [list(row) for n in range(3) for row in product(range(3),repeat=n)]
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    for alpha,beta,gamma in product(range(3),repeat=3):
        for a,b in product(seqs,repeat=2):
            if len(a)!=len(b):
                continue
            sums = [alpha*x+beta*y for x,y in zip(a,b)]
            if gamma==0:
                if any(sums):
                    continue
                c = [2]*len(a)
            else:
                if any(s%gamma for s in sums):
                    continue
                c = [s//gamma for s in sums]
            for d in seqs:
                for i in range(6):
                    assert gamma*coefficient(c,d,i)==alpha*coefficient(a,d,i)+beta*coefficient(b,d,i)
    assert coefficient([0],[1],0)!=coefficient([1],[1],0)


def test_guarded_linearity_replays_full_ancestors_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = linear.prove_convolution_linearity()
    assert result.receipt.target==linear.frozen_convolution_linearity_target()
    assert len(result.bundle.nodes)==123
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6449
    assert result.provenance["actual_weighted_convolution_linearity"] is True
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
