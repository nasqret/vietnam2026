"""Exact splitting keeps the genuine shifted tail and its scaling power."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_splitting as splitting


def test_exact_unconditional_shifted_tail_splitting():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = splitting.frozen_horner_splitting_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and not premises and type(conclusion) is Exists
    assert splitting.json_hash(encode_formula(target))==splitting.TARGET_SHA256
    assert len(splitting.canonical(encode_formula(target)))==6647
    c = splitting.source_contract()
    assert c["actual_shifted_tail_constructed"] is c["actual_prefix_tail_and_whole_values_constructed"] is True
    assert c["actual_scaling_power_constructed"] is c["arbitrary_coefficients_and_split_lengths"] is True
    assert c["zero_multiplier_and_empty_lengths_allowed"] is True
    assert c["identity"]=="z=p*x+y" and c["power"]=="p=t^N"
    assert c["tail_bound_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_existing_computation_definition_dag_only():
    registry = splitting.definition_registry()
    assert splitting.source_contract()["new_definition_ids"]==[]
    assert registry["NatAffineSlice"].stable_id=="ND0411"
    assert registry["NatHornerValue"].stable_id=="ND0437"
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_wrong_tail_offset_power_or_endpoint_is_rejected():
    for source in (splitting.NAMED_SOURCE.replace("NatAffineSlice(ab,ac,M,1", "NatAffineSlice(ab,ac,0,1"),
                   splitting.NAMED_SOURCE.replace("Pow(t,N,p)","Pow(t,M,p)"),
                   splitting.NAMED_SOURCE.replace("z=p*x+y","z=x+y"),
                   splitting.NAMED_SOURCE.replace("NatHornerValue(bb,bc,t,N,y)","NatHornerValue(ab,ac,t,N,y)")):
        with patch.object(splitting,"NAMED_SOURCE",source),pytest.raises(ValueError):
            splitting.frozen_horner_splitting_target()


def test_helper_target_and_owned_actual_ancestors():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = splitting.definition_registry()
    assert {n:splitting.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in splitting.HELPER_SOURCES.items()}==splitting.HELPER_TARGET_SHA256
    rows = splitting.read_mixed_archive(splitting.COMPOSITION_ARCHIVE)
    for name,source in splitting.ENDPOINT_SOURCES.items():
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
        assert splitting.ENDPOINT_OWNERS[name]=="CV061"


def test_changed_actual_archive_is_rejected():
    for key in ("sha256","target_ast_sha256"):
        pin = dict(splitting.COMPOSITION_ARCHIVE);pin[key] = "0"*64
        with pytest.raises(ValueError):
            splitting.read_mixed_archive(pin)


def test_splitting_model_zero_empty_and_genuine_tail():
    def horner(A,t):
        z = 0
        for a in A:
            z = t*z+a
        return z
    for M in range(5):
        for N in range(5):
            A = [(i+1)**2%7 for i in range(M+N)]
            for t in range(4):
                assert horner(A,t)==t**N*horner(A[:M],t)+horner(A[M:],t)
    assert horner([1,2,3],3)!=horner([1],3)+horner([2,3],3)
    assert horner([1,2,3],3)!=3**2*horner([1],3)+horner([1,2],3)


def test_ordinary_replay_and_forged_splitting_induction_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = splitting.prove_horner_splitting()
    assert result.receipt.target==splitting.frozen_horner_splitting_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(splitting.HELPER_SOURCES["all_prefixes"],registry=splitting.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
