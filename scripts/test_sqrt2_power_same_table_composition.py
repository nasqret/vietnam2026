"""One actual full composition carries normalization, low identity and tails."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_same_table_composition as composition


CHECKED_ARCHIVE = dict(case="CV080",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-same-table-composition-v3/generation-process.json.gz",
    bytes=157492,sha256="800e4508a43c0dfb246f6fafe33b5e2d8dd80eae7dd2684b217f3cfe18e3a002",
    raw_bytes=4212223,raw_sha256="2c9ccb42958bd058486073a66a6fd9bdc6ad2146029db53ac73025b9134c098a",
    bundle_bytes=2583524,bundle_sha256="739a6442d3cf4657fdb256c65867cd7b790f76676c457cd00f167d607a5b759c",
    nodes=426,root=425,target_ast_sha256="e5ce4e46386b9c0aa0cde7db11202d410819547dc4b6b462458184f2871f9611")


def test_exact_same_table_contract_and_exported_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = composition.frozen_same_table_composition_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(composition.OUTPUTS)==len(set(composition.OUTPUTS))==26
    assert len(composition.PARTS)==28
    assert composition.json_hash(encode_formula(target))==composition.TARGET_SHA256
    assert len(composition.canonical(encode_formula(target)))==43735
    for _ in composition.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion = conclusion.body
    fields = []
    for _ in range(27):
        assert type(conclusion) is And
        fields.append(conclusion.left);conclusion = conclusion.right
    fields.append(conclusion)
    names = tuple(reversed(("K",)+composition.OUTPUTS));registry = composition.definition_registry()
    assert fields==[parse_named(p,names,registry) for p in composition.PARTS]
    c = composition.source_contract()
    assert c["supplied_atanh_and_factorial_weight_codes_preserved"] is True
    assert c["same_full_table_low_prefix_geometric_evaluation"] is c["same_full_table_all_in_range_rational_tails"] is True
    assert c["actual_tail_at_low_cutoff_constructed"] is c["normalization_nonzero"] is True
    assert c["all_CV031_data_retained"] is c["all_CV077_data_retained"] is False
    assert c["code_number_equality_claimed"] is c["whole_value_at_three_constructed"] is c["closes_IR072"] is False


def test_conservative_registry_is_exact_union_without_new_definitions():
    from sqrt2_power_normalized_composition import definition_registry as small
    from sqrt2_power_supplied_composition_bound import definition_registry as full
    result = composition.definition_registry()
    assert set(result)==set(small())|set(full())
    for registry in (small(),full()):
        for name,d in registry.items():
            assert result[name].stable_id==d.stable_id and result[name].template_formula==d.template_formula
    c = composition.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==c["IR_parents_closed"]==0
    assert c["analytic_limit_claim"] is False


def test_changed_table_coefficient_or_normalization_target_is_rejected():
    original = composition.NAMED_SOURCE
    for source in (original.replace("BetaAt(fub,fuc,i,a)","BetaAt(fuc,fub,i,a)"),
                   original.replace("a=2*z","a=3*z"),
                   original.replace("r+z=(2*z)*p3","r+z=(3*z)*p3"),
                   original.replace("IRatLe(u,0,z*h,9*p0,0,q0)","IRatLe(u,0,h,9*p0,0,q0)"),
                   original.replace("z=fn*pn","z=fn+pn")):
        assert source!=original
        with patch.object(composition,"NAMED_SOURCE",source),pytest.raises(ValueError):
            composition.frozen_same_table_composition_target()


def test_owned_actual_normalization_transport_and_tail_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = composition.definition_registry();found = set()
    for pin in composition.ARCHIVES:
        rows = composition.read_mixed_archive(pin)
        for name,source in composition.ENDPOINT_SOURCES.items():
            if composition.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        for key in ("sha256","target_ast_sha256"):
            altered = dict(pin);altered[key] = "0"*64
            with pytest.raises(ValueError):
                composition.read_mixed_archive(altered)
    assert found==composition.ENDPOINT_SOURCES.keys()


def test_finite_model_same_coefficients_geometric_value_and_all_tails():
    from fractions import Fraction
    from math import factorial,lcm
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for N in range(2,6):
        for scaling in (1,2,5):
            d = scaling*lcm(*range(1,N,2));A = [2*d//i if i%2 else 0 for i in range(N)]
            W = [factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
            z = W[0];J = (N+1)*N;H = J+1
            rows = [];current = [1]+[0]*J
            for _ in range(N+1):
                rows.append(current);current = conv(A,current,H)
            U = [sum(W[j]*rows[j][i] for j in range(N+1)) for i in range(H)]
            assert z==factorial(N)*d**N>0 and U[:N]==[z]+[2*z]*(N-1)
            assert all((W[j]*factorial(j))*d**j==z for j in range(N+1))
            r,p3 = horner(U[:N],3),3**(N-1)
            assert r+z==2*z*p3 and z*p3>0
            assert horner(U,2)<=9*z*2**J and N<=J
            for M in range(J+1):
                tail = horner(U[M:],3)
                assert Fraction(tail,z*3**J)<=9*Fraction(2,3)**M


def test_ordinary_replay_without_new_induction_or_axioms():
    from peano_lab.library.proof_bundle import check_proof_bundle
    bundle,target,limits = _archived_bundle()
    receipt = check_proof_bundle(bundle,target,limits=limits)
    assert receipt.target==composition.frozen_same_table_composition_target()
    assert receipt.kernel_calls==receipt.node_count==426 and receipt.total_body_nodes==39864
    assert composition.source_contract()["definition_admissions"]==0


def _archived_bundle():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits().bundle_limits();rows = composition.read_mixed_archive(CHECKED_ARCHIVE)
    root = CHECKED_ARCHIVE["root"]
    bundle,target = decode_proof_bundle(composition.canonical(["peano-lab-bundle-v1",root,rows[root][1],rows]).decode()+"\n",limits=limits)
    assert target==composition.frozen_same_table_composition_target()
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


def test_forged_actual_width_transport_ancestor_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    bundle,target,limits = _archived_bundle()
    ancestor = parse_named(composition.TRANSPORT_SOURCE,registry=composition.definition_registry())
    matches = [n.node_id for n in bundle.nodes if n.target==ancestor]
    assert len(matches)==1
    forged = replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==matches[0] else n for n in bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,target,limits=limits)
