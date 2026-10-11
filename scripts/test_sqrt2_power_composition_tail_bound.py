"""One actual composition and terminal row, with all valid in-range tails."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_tail_bound as bound


CHECKED_ARCHIVE = dict(case="CV076",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-tail-bound-v1/generation-process.json.gz",
    bytes=106298,sha256="2aeb08cdd435d9896fb5cd8eb7249308d7546e71927ab04b23a4ad54fbd45aa8",
    raw_bytes=2986198,raw_sha256="14dd671883b377f9b0c563f13ef55299b2fab09c66e58cad9102cd8ce8d1c251",
    bundle_bytes=1824130,bundle_sha256="cf5c84b108e2db80fcaf846e709839e44402011c309e596c4b9c90c74560289e",
    nodes=336,root=335,target_ast_sha256="2baa8df68b336dc9d80d78e7f1d9797fdeb2859efc39377e00c1c0a18de9f83f")


def test_exact_unconditional_package_retains_every_majorant_field():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from sqrt2_power_composition_majorant import PARTS
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = bound.frozen_composition_tail_bound_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==2 and not premises and type(conclusion) is Exists
    assert len(bound.OUTPUTS)==29 and len(bound.PARTS)==40
    assert bound.json_hash(encode_formula(target))==bound.TARGET_SHA256
    assert len(bound.canonical(encode_formula(target)))==53005
    for _ in bound.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion = conclusion.body
    fields = []
    for _ in range(39):
        assert type(conclusion) is And
        fields.append(conclusion.left);conclusion = conclusion.right
    fields.append(conclusion)
    names = tuple(reversed(("k","N")+bound.OUTPUTS));registry = bound.definition_registry()
    assert fields[:37]==[parse_named(p,names,registry) for p in PARTS]
    assert fields[37]==parse_named("NatPowerRow(rb,rc,sb,sc,S N,ub,uc)",names,registry)
    assert fields[-1]==parse_named(bound.SPECIALIZED_CUTS,names,registry)
    c = bound.source_contract()
    assert c["premise_count"]==0 and c["all_CV074_data_retained"] is True
    assert c["same_row_value_and_normalization_for_every_tail"] is c["nonzero_rational_denominators_proved"] is True
    assert c["empty_tail_case_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reuses_conservative_rational_order_without_new_definitions():
    from sqrt2_power_rational_tail_majorant import definition_registry
    registry = bound.definition_registry()
    assert registry==definition_registry()
    assert registry["IRatLe"].stable_id=="ND0444"
    assert tuple(registry["IRatLe"].conceptual_dependencies)==("IRatValid","Le")
    assert bound.source_contract()["new_definition_ids"]==[]
    assert bound.source_contract()["definition_admissions"]==0


def test_wrong_cutoff_row_or_normalization_is_rejected():
    for source in (bound.NAMED_SOURCE.replace("forall M. Le(M,","forall M. Le(0,"),
                   bound.NAMED_SOURCE.replace("IRatLe(u,0,w0*h,9*p0,0,q0)","IRatLe(u,0,h,9*p0,0,q0)"),
                   bound.NAMED_SOURCE.replace("NatPowerRow(rb,rc,sb,sc,S N,ub,uc)","NatPowerRow(pb,pc,qb,qc,S N,ub,uc)"),
                   bound.NAMED_SOURCE.replace("IRatLe(u,0,w0*h,9*p0,0,q0)","IRatLe(u,0,w0*h,9,0,q0)")):
        with patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_composition_tail_bound_target()


def test_owned_actual_majorant_and_tail_bodies_and_archive_integrity():
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


def test_every_in_range_tail_of_same_actual_finite_composition_model():
    from fractions import Fraction
    from math import factorial,lcm
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for k in range(5):
        L = k+1;d = lcm(*range(1,L,2));A = [2*d//i if i%2 else 0 for i in range(L)]
        for N in range(5):
            K = N+1;J = K*L;H = J+1;v = 2**J
            W = [factorial(N)//factorial(j)*d**(N-j) for j in range(K)]
            rows = [];current = [1]+[0]*J
            for _ in range(K):
                rows.append(current);current = conv(A,current,H)
            C = [sum(W[j]*rows[j][i] for j in range(K)) for i in range(H)]
            s = horner(C,2);w0 = W[0]
            assert w0>0 and s<=9*w0*v
            for M in range(J+1):
                r = J-M;T = C[M:];u = horner(T,3);p,q,h = 2**M,3**M,3**J
                assert J==M+r and len(T)==r+1
                assert q>0 and w0*h>0 and u*q<=9*p*(w0*h)
                assert Fraction(u,w0*h)==sum(Fraction(C[i],w0*3**i) for i in range(M,H))
                assert Fraction(u,w0*h)<=9*Fraction(2,3)**M


def test_ordinary_replay_constructs_same_row_and_all_cuts():
    result = bound.prove_composition_tail_bound()
    assert result.receipt.target==bound.frozen_composition_tail_bound_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    assert len(result.bundle.nodes)==336


def _archived_bundle():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits().bundle_limits();rows = bound.read_mixed_archive(CHECKED_ARCHIVE)
    root = CHECKED_ARCHIVE["root"]
    bundle,target = decode_proof_bundle(bound.canonical(["peano-lab-bundle-v1",root,rows[root][1],rows]).decode()+"\n",limits=limits)
    assert target==bound.frozen_composition_tail_bound_target()
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


def test_forged_rational_tail_ancestor_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    bundle,target,limits = _archived_bundle()
    ancestor = parse_named(bound.ENDPOINT_SOURCES["rational_tail"],registry=bound.definition_registry())
    matches = [n.node_id for n in bundle.nodes if n.target==ancestor]
    assert len(matches)==1
    forged = replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==matches[0] else n for n in bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,target,limits=limits)
