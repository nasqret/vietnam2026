"""Evaluation constructs values, never replacement power/accumulation codes."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supplied_composition_evaluation as evaluation


def test_exact_supplied_trace_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = evaluation.frozen_supplied_composition_evaluation_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==16 and len(premises)==3 and type(conclusion) is Exists
    assert len(evaluation.OUTPUTS)==10 and len(evaluation.PARTS)==9
    assert not set(evaluation.OUTPUTS)&set(evaluation.PARAMETERS)
    assert evaluation.json_hash(encode_formula(target))==evaluation.TARGET_SHA256
    assert len(evaluation.canonical(encode_formula(target)))==25505
    c = evaluation.source_contract()
    assert c["supplied_input_weights_power_and_accumulation_preserved"] is True
    assert c["every_supplied_terminal_row_has_same_sum_as_value"] is c["all_row_values_satisfy_monomial_law"] is True
    assert c["power_or_accumulation_trace_replaced"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_nonzero_base_assumption():
    from sqrt2_power_full_composition_evaluation import definition_registry
    assert evaluation.definition_registry()==definition_registry()
    assert evaluation.source_contract()["new_definition_ids"]==[]
    assert evaluation.source_contract()["zero_base_and_empty_lengths_allowed"] is True
    assert evaluation.source_contract()["no_nonzero_factor_cancelled"] is True
    assert evaluation.PREMISES==(evaluation.WIDTH,evaluation.POWER_TRACE,evaluation.ACCUMULATION_TRACE)


def test_changed_support_or_supplied_code_rejected():
    original = evaluation.NAMED_SOURCE
    for source in (original.replace("Le(S(K*L),S J) -> ",""),
                   original.replace("NatPowerTrace(ab,ac,L,S J,pb,pc,qb,qc,K)","NatPowerTrace(ac,ab,L,S J,pb,pc,qb,qc,K)"),
                   original.replace("NatWeightedSeriesTrace(S J,wb,wc", "NatWeightedSeriesTrace(S J,wc,wb"),
                   original.replace("a*y=(v*b)*c","a*y=(v+b)*c")):
        assert source!=original
        with patch.object(evaluation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            evaluation.frozen_supplied_composition_evaluation_target()


def test_actual_endpoint_bodies_and_changed_archive_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    pin = evaluation.COMPOSITION_ARCHIVE;rows = evaluation.read_mixed_archive(pin)
    registry = evaluation.definition_registry()
    for name,source in evaluation.ENDPOINT_SOURCES.items():
        assert evaluation.ENDPOINT_OWNERS[name]==pin["case"]
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
    for key in ("sha256","target_ast_sha256"):
        altered = dict(pin);altered[key] = "0"*64
        with pytest.raises(ValueError):
            evaluation.read_mixed_archive(altered)


def test_same_polynomial_tables_can_be_evaluated_at_different_bases():
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    def horner(A,t):
        value = 0
        for a in A:
            value = t*value+a
        return value
    for A in ([],[0],[2],[0,2],[1,2,1]):
        for K in range(4):
            L = len(A);J = K*L+2;H = J+1;P = [[1]+[0]*J]
            for _ in range(K):
                P.append(conv(A,P[-1],H))
            W = [(j+2)%4 for j in range(K)];R = [[0]*H]
            for j in range(K):
                R.append([R[-1][i]+W[j]*P[j][i] for i in range(H)])
            frozen = tuple(map(tuple,P)),tuple(map(tuple,R))
            for t in (0,1,2,3,5):
                x,p,v = horner(A,t),t**L,t**J
                V = [horner(P[j],t) for j in range(K)];Z = [W[j]*V[j] for j in range(K)]
                assert horner(R[-1],t)==sum(Z)
                for j in range(K):
                    assert p**j*V[j]==v*t**j*x**j
                assert frozen==(tuple(map(tuple,P)),tuple(map(tuple,R)))


def test_ordinary_replay_has_no_new_induction_or_axiom():
    result = evaluation.prove_supplied_composition_evaluation()
    assert result.receipt.target==evaluation.frozen_supplied_composition_evaluation_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_monomial_ancestor_and_false_target_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = evaluation.prove_supplied_composition_evaluation()
    target = parse_named(evaluation.ENDPOINT_SOURCES["monomials"],registry=evaluation.definition_registry())
    matches = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(matches)==1
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==matches[0] else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
