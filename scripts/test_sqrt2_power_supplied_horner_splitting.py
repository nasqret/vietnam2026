"""Supplied prefix, tail and whole values obey the same finite split."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supplied_horner_splitting as splitting


def test_exact_five_premise_split_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target = splitting.frozen_supplied_horner_splitting_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==11 and len(premises)==5 and type(conclusion) is Eq
    assert splitting.json_hash(encode_formula(target))==splitting.TARGET_SHA256
    assert len(splitting.canonical(encode_formula(target)))==6637
    c = splitting.source_contract()
    assert c["supplied_coefficient_and_tail_codes_preserved"] is c["supplied_prefix_tail_and_whole_values_preserved"] is True
    assert c["independent_horner_histories_allowed"] is c["prefix_value_transported_by_proved_uniqueness"] is True
    assert c["code_number_equality_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_nonzero_assumption():
    from sqrt2_power_horner_splitting import definition_registry
    assert splitting.definition_registry()==definition_registry()
    assert splitting.source_contract()["new_definition_ids"]==[]
    assert splitting.source_contract()["definition_admissions"]==0
    assert splitting.source_contract()["zero_base_and_empty_parts_allowed"] is True
    assert splitting.source_contract()["no_nonzero_factor_cancelled"] is True


def test_changed_slice_or_actual_value_rejected():
    original = splitting.NAMED_SOURCE
    for source in (original.replace("NatAffineSlice(ab,ac,M,1,bb,bc,N) -> ",""),
                   original.replace("NatHornerValue(bb,bc,t,N,y)","NatHornerValue(bc,bb,t,N,y)"),
                   original.replace("Pow(t,N,p)","Pow(t,M,p)"),
                   original.replace("z=p*x+y","z=p*y+x")):
        assert source!=original
        with patch.object(splitting,"NAMED_SOURCE",source),pytest.raises(ValueError):
            splitting.frozen_supplied_horner_splitting_target()


def test_owned_actual_splitting_and_value_uniqueness_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = splitting.definition_registry();found = set()
    for pin in splitting.ARCHIVES:
        rows = splitting.read_mixed_archive(pin)
        for name,source in splitting.ENDPOINT_SOURCES.items():
            if splitting.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==splitting.ENDPOINT_SOURCES.keys()


def test_altered_archives_are_rejected():
    for original in splitting.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                splitting.read_mixed_archive(pin)


def test_finite_model_including_empty_parts_and_zero_base():
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    for M in range(5):
        for N in range(5):
            A = [(j*j+2)%7 for j in range(M+N)]
            tail = A[M:]
            for t in (0,1,2,3,7):
                x,y,z,p = horner(A[:M],t),horner(tail,t),horner(A,t),t**N
                assert z==p*x+y


def test_ordinary_replay_and_forged_split_ancestor_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = splitting.prove_supplied_horner_splitting()
    assert result.receipt.target==splitting.frozen_supplied_horner_splitting_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    target = parse_named(splitting.ENDPOINT_SOURCES["all_prefixes"],registry=splitting.definition_registry())
    matches = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(matches)==1
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==matches[0] else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
