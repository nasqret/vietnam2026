"""Different actual power depths still preserve every consumed weighted term."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_successor_composition_transport as transport


def test_exact_depth_mismatch_and_successor_accumulation_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = transport.frozen_successor_composition_transport_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==24 and len(premises)==5 and type(conclusion) is Forall
    assert transport.json_hash(encode_formula(target))==transport.TARGET_SHA256
    assert len(transport.canonical(encode_formula(target)))==19049
    c = transport.source_contract()
    assert c["supplied_small_power_depth"]=="N" and c["supplied_large_power_depth"]=="N+1"
    assert c["accumulation_terms"]=="N+1" and c["larger_power_trace_restricted_explicitly"] is True
    assert c["same_input_and_weight_codes"] is c["all_accumulation_rows_through_N_plus_one"] is True
    assert c["unused_small_power_row_constructed"] is c["code_number_equality_claimed"] is c["closes_IR072"] is False


def test_no_new_definition_or_hidden_extra_power_row():
    from sqrt2_power_consumed_row_transport import definition_registry
    assert transport.definition_registry()==definition_registry()
    c = transport.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==0
    assert c["analytic_limit_claim"] is False and c["zero_horizon_and_empty_width_allowed"] is True
    assert "Lt(k,S N)" in transport.SOURCE_MATCH
    assert "Le(k,S N)" in transport.RESULT


def test_changed_horizons_or_input_and_weight_codes_are_rejected():
    for source in (transport.NAMED_SOURCE.replace("Le(H,J) -> ",""),
                   transport.NAMED_SOURCE.replace("NatPowerTrace(ab,ac,L,J,rb,rc,sb,sc,S N)","NatPowerTrace(ac,ab,L,J,rb,rc,sb,sc,S N)"),
                   transport.NAMED_SOURCE.replace("NatWeightedSeriesTrace(J,wb,wc,rb,rc,sb,sc", "NatWeightedSeriesTrace(J,wc,wb,rb,rc,sb,sc"),
                   transport.NAMED_SOURCE.replace("Le(k,S N)","Le(k,S(S N))")):
        with patch.object(transport,"NAMED_SOURCE",source),pytest.raises(ValueError):
            transport.frozen_successor_composition_transport_target()


def test_owned_actual_power_and_consumed_transport_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = transport.definition_registry();found = set()
    for pin in transport.ARCHIVES:
        rows = transport.read_mixed_archive(pin)
        for name,source in transport.ENDPOINT_SOURCES.items():
            if transport.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==transport.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in transport.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                transport.read_mixed_archive(pin)


def test_actual_cross_width_powers_and_all_successor_accumulations_model():
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    def powers(A,H,N):
        rows = [[1]+[0]*(H-1) if H else []]
        for _ in range(N):
            rows.append(conv(A,rows[-1],H))
        return rows
    for A in ([],[0],[1],[0,2],[1,2,1]):
        for H in range(4):
            for J in range(H,5):
                for N in range(4):
                    P,Q = powers(A,H,N),powers(A,J,N+1)
                    assert len(P)==N+1 and len(Q)==N+2
                    W = [(j+1)%3 for j in range(N+1)]
                    R,S = [[0]*H],[[0]*J]
                    for k in range(N+1):
                        R.append([R[k][i]+W[k]*P[k][i] for i in range(H)])
                        S.append([S[k][i]+W[k]*Q[k][i] for i in range(J)])
                    assert all(R[k]==S[k][:H] for k in range(N+2))


def test_ordinary_replay_and_forged_consumed_transport_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = transport.prove_successor_composition_transport()
    assert result.receipt.target==transport.frozen_successor_composition_transport_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(transport.TRANSPORT_SOURCE,registry=transport.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
