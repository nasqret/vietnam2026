"""Actual weighted evaluation constructs every table and the same sum."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_weighted_accumulation_evaluation as evaluation


def test_exact_unconditional_weighted_evaluation_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = evaluation.frozen_weighted_accumulation_evaluation_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==9 and not premises and type(conclusion) is Exists
    assert evaluation.json_hash(encode_formula(target))==evaluation.TARGET_SHA256
    assert len(evaluation.canonical(encode_formula(target)))==9902
    c = evaluation.source_contract()
    assert c["actual_weighted_trace_constructed"] is c["actual_source_row_values_constructed"] is True
    assert c["actual_pointwise_products_and_sum_constructed"] is c["every_terminal_row_has_the_sum_as_its_horner_value"] is True
    assert c["arbitrary_source_rows_and_weights"] is c["zero_multiplier_and_empty_lengths_allowed"] is True
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_product_graph_not_sum_identity():
    from peano_lab.library.proof_bundle import encode_formula
    registry = evaluation.definition_registry()
    identifier,name,params,source,deps,digest = evaluation.DEFINITION
    d = registry[name]
    assert d.stable_id==identifier=="ND0439"
    assert evaluation.json_hash(encode_formula(d.template_formula))==digest
    assert tuple(d.conceptual_dependencies)==deps and "Sum(" not in source and "Horner" not in source
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    bad = list(evaluation.DEFINITION);bad[3] = "forall i. Lt(i,K) -> BetaAt(zb,zc,i,0)"
    with patch.object(evaluation,"DEFINITION",tuple(bad)),pytest.raises(ValueError):
        evaluation.definition_registry()


def test_wrong_row_or_sum_is_rejected():
    for source in (evaluation.NAMED_SOURCE.replace("Sum(zb,zc,K,s)","Sum(zb,zc,K,0)"),
                   evaluation.NAMED_SOURCE.replace("NatHornerValue(ub,uc,t,H,s)","NatHornerValue(ub,uc,t,H,0)"),
                   evaluation.NAMED_SOURCE.replace("NatPowerRow(rb,rc,sb,sc,K,ub,uc) -> ","")):
        with patch.object(evaluation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            evaluation.frozen_weighted_accumulation_evaluation_target()


def test_helper_targets_and_owned_actual_ancestors():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = evaluation.definition_registry()
    assert {n:evaluation.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in evaluation.HELPER_SOURCES.items()}==evaluation.HELPER_TARGET_SHA256
    found = set()
    for pin in evaluation.ARCHIVES:
        rows = evaluation.read_mixed_archive(pin)
        for name,source in evaluation.ENDPOINT_SOURCES.items():
            if evaluation.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==evaluation.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in evaluation.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                evaluation.read_mixed_archive(pin)


def test_weighted_sum_model_arbitrary_rows_and_zero_cases():
    def horner(row,t):
        y = 0
        for a in row:
            y = t*y+a
        return y
    for K in range(5):
        for H in range(4):
            rows = [[(i+1)*(j+2)%7 for j in range(H)] for i in range(K)]
            for seed in range(3):
                weights = [(seed+k)%4 for k in range(K)]
                accumulated = [sum(weights[k]*rows[k][j] for k in range(K)) for j in range(H)]
                for t in range(4):
                    assert horner(accumulated,t)==sum(weights[k]*horner(rows[k],t) for k in range(K))


def test_ordinary_replay_and_forged_linearity_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = evaluation.prove_weighted_accumulation_evaluation()
    assert result.receipt.target==evaluation.frozen_weighted_accumulation_evaluation_target()
    assert result.provenance["new_induction_count"]==2
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(evaluation.ENDPOINT_SOURCES["horner_linear"],registry=evaluation.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
