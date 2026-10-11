"""Actual scalar premise, arbitrary rows, hygiene, replay and hostile controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_weighted_series_scaling as scaling


def test_exact_constructed_traces_with_scalar_premise_and_no_analytic_claim():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = scaling.frozen_weighted_series_scaling_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==11 and len(premises)==1 and type(conclusion) is Exists
    assert scaling.json_hash(encode_formula(target))==scaling.TARGET_SHA256
    assert len(scaling.canonical(encode_formula(target)))==10088
    contract = scaling.source_contract()
    assert contract["actual_pointwise_weight_relation_required"] is True
    assert contract["both_actual_weighted_traces_constructed"] is True
    assert contract["arbitrary_source_rows"] is True
    assert contract["nonzero_scalar_required"] is False
    assert contract["exp_composition_recurrence"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_conservative_scalar_alias_and_hygienic_names():
    from sqrt2_power_definitions import parse_named
    r = scaling.definition_registry()
    assert scaling.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("d","i","a","b","c","L")
    alias = parse_named("NatLinearTriple(d,0,1,i,a,i,a,b,c,L)",names,r)
    explicit = parse_named("forall j x y z. Lt(j,L) -> BetaAt(i,a,j,x) -> BetaAt(i,a,j,y) -> BetaAt(b,c,j,z) -> 1*z=d*x+0*y",names,r)
    assert alias==explicit


def test_removed_weight_premise_or_wrong_terminal_bound_is_rejected():
    for source in (scaling.NAMED_SOURCE.replace(scaling.WEIGHT_RELATION+" -> ","",1),
                   scaling.NAMED_SOURCE.replace("Le(k,K)","Le(k,S K)")):
        with patch.object(scaling,"NAMED_SOURCE",source),pytest.raises(ValueError):
            scaling.frozen_weighted_series_scaling_target()


def test_helpers_and_actual_dependency_targets_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = scaling.definition_registry()
    assert {name:scaling.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in scaling.HELPER_SOURCES.items()}==scaling.HELPER_TARGET_SHA256
    found = set()
    for pin in scaling.ARCHIVES:
        rows = scaling.read_archive(pin)
        for name,source in scaling.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==scaling.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in scaling.ARCHIVES}=={"CV021"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in scaling.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                scaling.read_archive(changed)


def test_finite_scalar_fold_model_including_zero_and_missing_premise_counterexample():
    for d in range(5):
        for H in range(5):
            for K in range(7):
                weights = [(j*j+2*j+3)%7 for j in range(K)]
                rows = [[(j+1)*(i+3)%11 for i in range(H)] for j in range(K)]
                q,r = [0]*H,[0]*H
                for k in range(K+1):
                    assert q==[d*v for v in r]
                    if k<K:
                        q = [a+(d*weights[k])*b for a,b in zip(q,rows[k])]
                        r = [a+weights[k]*b for a,b in zip(r,rows[k])]
    d,z,w,source = 2,1,3,1
    assert w!=d*z and w*source!=d*(z*source)


def test_guarded_scaling_induction_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = scaling.prove_weighted_series_scaling()
    assert result.receipt.target==scaling.frozen_weighted_series_scaling_target()
    assert len(result.bundle.nodes)==116
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6125
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
