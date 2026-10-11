"""Preserve the actual Horner history, not equality of unequal-length values."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_prefix_transport as transport


def test_exact_shared_history_and_shorter_endpoint_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = transport.frozen_horner_prefix_transport_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and len(premises)==2 and type(conclusion) is Exists
    assert transport.json_hash(encode_formula(target))==transport.TARGET_SHA256
    assert len(transport.canonical(encode_formula(target)))==3147
    c = transport.source_contract()
    assert c["length_order_and_low_input_match_required"] is c["actual_shared_horner_history_constructed"] is True
    assert c["actual_shorter_endpoint_constructed"] is c["coefficient_reencoding_and_prefix_restriction"] is True
    assert c["empty_prefix_and_zero_multiplier_allowed"] is True
    assert c["different_length_endpoint_equality"] is c["factors_cancelled"] is c["closes_IR072"] is False


def test_unchanged_conservative_definition_dag():
    registry = transport.definition_registry()
    assert transport.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_changed_length_order_or_target_input_is_rejected():
    for source in (transport.NAMED_SOURCE.replace("Le(M,N)","Le(N,M)"),
                   transport.NAMED_SOURCE.replace("NatScaledHornerTrace(bb,bc,t,M,","NatScaledHornerTrace(bb,bc,t,N,")):
        with patch.object(transport,"NAMED_SOURCE",source),pytest.raises(ValueError):
            transport.frozen_horner_prefix_transport_target()


def test_exact_helper_and_owned_actual_horner_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = transport.definition_registry()
    assert {name:transport.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in transport.HELPER_SOURCES.items()}==transport.HELPER_TARGET_SHA256
    rows = transport.read_mixed_archive(transport.HORNER_ARCHIVE)
    for name,source in transport.ENDPOINT_SOURCES.items():
        assert transport.ENDPOINT_OWNERS[name]=="CV032"
        matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=registry))]
        assert len(matches)==1 and matches[0][3]


def test_changed_actual_archive_is_rejected():
    for key in ("sha256","bundle_sha256","target_ast_sha256"):
        changed = dict(transport.HORNER_ARCHIVE);changed[key] = "0"*64
        with pytest.raises(ValueError):
            transport.read_mixed_archive(changed)


def test_shared_history_model_and_unequal_length_counterexample():
    def history(a,t):
        h = [0]
        for v in a:
            h.append(t*h[-1]+v)
        return h
    for N in range(7):
        a = [j+1 for j in range(N)]
        for M in range(N+1):
            b = a[:M]+[97,103]
            for t in range(5):
                assert history(a,t)[:M+1]==history(b[:M],t)
    assert history([1,2],3)[1]!=history([1,2],3)[2]


def test_ordinary_replay_and_forged_history_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = transport.prove_horner_prefix_transport()
    assert result.receipt.target==transport.frozen_horner_prefix_transport_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(transport.ENDPOINT_SOURCES["horner_exists"],registry=transport.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
