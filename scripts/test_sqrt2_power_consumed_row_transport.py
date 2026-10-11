"""Only rows below K are consumed; every accumulated row through K is covered."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_consumed_row_transport as transport


def test_exact_consumed_range_and_all_accumulation_rows_contract():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from sqrt2_power_composition_width_transport import SOURCE_MATCH,OUTPUT_MATCH
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = transport.frozen_consumed_row_transport_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==21 and len(premises)==4 and type(conclusion) is Forall
    assert transport.json_hash(encode_formula(target))==transport.TARGET_SHA256
    assert len(transport.canonical(encode_formula(target)))==10504
    names = tuple(reversed(transport.FIXED));registry = transport.definition_registry()
    assert transport.CONSUMED_MATCH==SOURCE_MATCH.replace("Le(k,K)","Lt(k,K)")
    assert premises[1]==parse_named(transport.CONSUMED_MATCH,names,registry)
    assert conclusion==parse_named(OUTPUT_MATCH,names,registry)
    c = transport.source_contract()
    assert c["source_rows_required"]=="k<K" and c["accumulated_rows_proved"]=="k<=K"
    assert c["same_actual_weight_codes"] is c["supplied_accumulation_traces_required"] is True
    assert c["unused_source_row_agreement_required"] is c["code_number_equality_claimed"] is c["closes_IR072"] is False


def test_no_new_definition_or_hidden_transport_assumption():
    from sqrt2_power_supplied_composition_bound import definition_registry
    assert transport.definition_registry()==definition_registry()
    c = transport.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==0
    assert c["analytic_limit_claim"] is False and c["zero_width_and_zero_horizon_allowed"] is True


def test_changed_width_consumption_or_weight_codes_are_rejected():
    for source in (transport.NAMED_SOURCE.replace("Le(H,J) -> ",""),
                   transport.NAMED_SOURCE.replace("Lt(k,K)","Le(k,K)"),
                   transport.NAMED_SOURCE.replace("NatWeightedSeriesTrace(J,wb,wc,rb,rc,sb,sc", "NatWeightedSeriesTrace(J,wc,wb,rb,rc,sb,sc"),
                   transport.NAMED_SOURCE.replace("Lt(i,H)","Lt(i,J)")):
        with patch.object(transport,"NAMED_SOURCE",source),pytest.raises(ValueError):
            transport.frozen_consumed_row_transport_target()


def test_owned_actual_weighted_step_and_value_bodies():
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


def test_unread_final_source_row_can_differ_including_empty_accumulation():
    for H in range(4):
        for J in range(H,5):
            for K in range(5):
                W = [(k+1)%3 for k in range(K)]
                P = [[k+i+1 for i in range(H)] for k in range(K+1)]
                Q = [[(P[k][i] if k<K else P[k][i]+7) if i<H else 9 for i in range(J)] for k in range(K+1)]
                R,S = [[0]*H],[[0]*J]
                for k in range(K):
                    R.append([R[k][i]+W[k]*P[k][i] for i in range(H)])
                    S.append([S[k][i]+W[k]*Q[k][i] for i in range(J)])
                assert all(P[k]==Q[k][:H] for k in range(K))
                assert all(R[k]==S[k][:H] for k in range(K+1))
                if H:
                    assert P[K]!=Q[K][:H]
    assert 0+1*1!=0+1*2


def test_ordinary_replay_and_forged_weighted_step_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = transport.prove_consumed_row_transport()
    assert result.receipt.target==transport.frozen_consumed_row_transport_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(transport.ENDPOINT_SOURCES["weighted_graph"],registry=transport.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
