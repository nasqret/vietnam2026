"""Majorant and all tails preserve caller-supplied coefficient/weight codes."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_supplied_composition_bound as bound


CHECKED_ARCHIVE = dict(case="CV077",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-supplied-composition-bound-v1/generation-process.json.gz",
    bytes=99881,sha256="34ac810fa77d2751628940bcd8a6b2ae123fbee1c5e87d0f2c17f4631c96b902",
    raw_bytes=2729665,raw_sha256="537663b03f156dab01b8bb1a9670de3059b9b8f1686e554a78bb5d8c3b97b5ed",
    bundle_bytes=1661719,bundle_sha256="8b53d2ca3cedcb2b91b3752eb9b01fea4860ef11429582dc25a3b8a9efd78a41",
    nodes=317,root=316,target_ast_sha256="e21e4c6b538bc01cb88d592709a53809b0e7e69f1048918f9661e0965cd5e421")


def test_exact_supplied_table_contract_and_same_computation_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = bound.frozen_supplied_composition_bound_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==5 and type(conclusion) is Exists
    assert len(bound.OUTPUTS)==21 and len(bound.PARTS)==25
    assert not set(bound.OUTPUTS)&set(bound.A+bound.W)
    assert bound.json_hash(encode_formula(target))==bound.TARGET_SHA256
    assert len(bound.canonical(encode_formula(target)))==43729
    for _ in bound.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion = conclusion.body
    fields = []
    for _ in range(24):
        assert type(conclusion) is And
        fields.append(conclusion.left);conclusion = conclusion.right
    fields.append(conclusion)
    names = tuple(reversed(bound.PARAMETERS+bound.OUTPUTS));registry = bound.definition_registry()
    assert fields[:11]==[parse_named(p,names,registry) for p in bound.COMPOSITION_FIELDS]
    assert fields[-1]==parse_named(bound.SPECIALIZED_CUTS,names,registry)
    c = bound.source_contract()
    assert c["supplied_atanh_and_weight_codes_preserved"] is c["supplied_nonzero_weight_head_required"] is True
    assert c["supplied_weight_table_replaced"] is c["factorial_normalization_constructed"] is False
    assert c["empty_tail_case_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_new_definition_or_hidden_supplied_table_validity():
    from sqrt2_power_composition_tail_bound import definition_registry
    assert bound.definition_registry()==definition_registry()
    assert bound.source_contract()["new_definition_ids"]==[]
    assert bound.source_contract()["definition_admissions"]==0
    assert bound.PREMISES==("~d=0","NatAtanhPrefix(d,ab,ac,S k)","NatExpWeightTable(d,N,wb,wc)","BetaAt(wb,wc,0,w0)","~w0=0")


def test_missing_supplied_guard_or_changed_weight_and_normalization_rejected():
    for source in (bound.NAMED_SOURCE.replace("~d=0 -> ",""),
                   bound.NAMED_SOURCE.replace("~w0=0 -> ",""),
                   bound.NAMED_SOURCE.replace("BetaAt(wb,wc,0,w0) -> ",""),
                   bound.NAMED_SOURCE.replace("NatPointwiseProductPrefix(wb,wc,vb,vc,zb,zc,S N)","NatPointwiseProductPrefix(wc,wb,vb,vc,zb,zc,S N)"),
                   bound.NAMED_SOURCE.replace("IRatLe(u,0,w0*h,9*p0,0,q0)","IRatLe(u,0,h,9*p0,0,q0)")):
        with patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_supplied_composition_bound_target()


def test_owned_actual_generic_helpers_and_archive_integrity():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = bound.definition_registry();found = set()
    for pin in bound.ARCHIVES:
        rows = bound.read_mixed_archive(pin)
        for name,source in bound.ENDPOINT_SOURCES.items():
            if bound.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        for key in ("sha256","target_ast_sha256"):
            altered = dict(pin);altered[key] = "0"*64
            with pytest.raises(ValueError):
                bound.read_mixed_archive(altered)
    assert found==bound.ENDPOINT_SOURCES.keys()


def test_supplied_scaled_denominators_and_same_weight_table_model():
    from fractions import Fraction
    from math import factorial,lcm
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for k in range(4):
        L = k+1
        for scaling in (1,2,5):
            d = scaling*lcm(*range(1,L,2));A = [2*d//i if i%2 else 0 for i in range(L)]
            for N in range(4):
                K = N+1;J = K*L;H = J+1;v = 2**J
                W = [factorial(N)//factorial(j)*d**(N-j) for j in range(K)]
                assert W[-1]==1 and all(W[j]==((j+1)*d)*W[j+1] for j in range(N))
                rows = [];current = [1]+[0]*J
                for _ in range(K):
                    rows.append(current);current = conv(A,current,H)
                C = [sum(W[j]*rows[j][i] for j in range(K)) for i in range(H)]
                s,w0 = horner(C,2),W[0]
                assert d>0 and w0>0 and s<=9*w0*v
                for M in range(J+1):
                    u = horner(C[M:],3)
                    assert Fraction(u,w0*3**J)<=9*Fraction(2,3)**M


def test_ordinary_replay_preserves_supplied_codes_without_new_induction():
    result = bound.prove_supplied_composition_bound()
    assert result.receipt.target==bound.frozen_supplied_composition_bound_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def _archived_bundle():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits().bundle_limits();rows = bound.read_mixed_archive(CHECKED_ARCHIVE)
    root = CHECKED_ARCHIVE["root"]
    bundle,target = decode_proof_bundle(bound.canonical(["peano-lab-bundle-v1",root,rows[root][1],rows]).decode()+"\n",limits=limits)
    assert target==bound.frozen_supplied_composition_bound_target()
    return bundle,target,limits


def test_forged_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    bundle,target,limits = _archived_bundle()
    forged = replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==bundle.root else n for n in bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,target,limits=limits)
    with pytest.raises(ProofBundleError):
        check_proof_bundle(bundle,Bot(),limits=limits)


def test_forged_generic_tail_ancestor_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    bundle,target,limits = _archived_bundle()
    ancestor = parse_named(bound.ENDPOINT_SOURCES["all_tails"],registry=bound.definition_registry())
    matches = [n.node_id for n in bundle.nodes if n.target==ancestor]
    assert len(matches)==1
    forged = replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==matches[0] else n for n in bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,target,limits=limits)
