"""Full actual composition, separate bounds, and all denominator factors."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_majorant as majorant


CHECKED_ARCHIVE = dict(case="CV074",
    path="research/arithmetic-library/sqrt2-power/observations/shared-wave-composition-majorant-v1/generation-process.json.gz",
    bytes=97871,sha256="0b9dc655d19ddce1a289a2fb7cb2fc4e12188728681730f70d0ec084e5d73464",
    raw_bytes=2673911,raw_sha256="98e40f58d752dbc133fa1766b71da82c14261eb280abe078dbaed833ce9dfb22",
    bundle_bytes=1627627,bundle_sha256="1ec6611c5e094c392f09d2203b46e4ce9380c95ad0ab421a8c9f3d7c600aa221",
    nodes=325,root=324,target_ast_sha256="0a0ef5814cf4d9655010b47abf33ab8cbcb9f86f7d6f336cafcc1a6d7556273b")


def test_exact_unconditional_majorant_retains_actual_composition_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from sqrt2_power_full_composition_evaluation import PARTS
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_composition_majorant_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==2 and not premises and type(conclusion) is Exists
    assert len(majorant.OUTPUTS)==27 and len(majorant.PARTS)==37
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==42344
    for _ in majorant.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion = conclusion.body
    fields = []
    for _ in range(36):
        assert type(conclusion) is And
        fields.append(conclusion.left);conclusion = conclusion.right
    fields.append(conclusion)
    names = tuple(reversed(("k","N")+majorant.OUTPUTS));registry = majorant.definition_registry()
    assert fields[16:27]==[parse_named(majorant.at_two(p),names,registry) for p in PARTS]
    assert fields[-1]==parse_named("Le(s,9*(w0*v))",names,registry)
    c = majorant.source_contract()
    assert c["premise_count"]==0 and c["all_CV061_fields_retained_at_base_two"] is True
    assert c["same_actual_row_values_products_sum_and_terminal_value"] is c["nonzero_normalization_proved"] is True
    assert c["rational_division_transport_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_hidden_analytic_or_majorant_definition():
    from sqrt2_power_scaled_exp_terms import definition_registry
    assert majorant.definition_registry()==definition_registry()
    c = majorant.source_contract()
    assert c["new_definition_ids"]==[] and c["definition_admissions"]==0
    assert c["inner_scale"]=="p=q*2; q=2^k; p=2^(k+1)"
    assert c["normalization"]=="w0*v; v=2^J; w0=N!*d^N"
    assert c["exponential_recurrence_denominator"]=="d*p"


def test_wrong_scale_width_or_terminal_sum_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace("Le(s,9*(w0*v))","Le(s,9*w0)"),
                   majorant.NAMED_SOURCE.replace("p=q*2","p=q"),
                   majorant.NAMED_SOURCE.replace("((S N)*(S k))","(N*(S k))"),
                   majorant.NAMED_SOURCE.replace("Sum(zb,zc,S N,s)","Sum(vb,vc,S N,s)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_composition_majorant_target()


def test_actual_owned_bound_and_computation_bodies_and_archive_integrity():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry();found = set()
    for pin in majorant.ARCHIVES:
        rows = majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        for key in ("sha256","target_ast_sha256"):
            altered = dict(pin);altered[key] = "0"*64
            with pytest.raises(ValueError):
                majorant.read_mixed_archive(altered)
    assert found==majorant.ENDPOINT_SOURCES.keys()


def test_actual_atanh_composition_model_and_scale_at_one_half():
    from fractions import Fraction
    from math import factorial,lcm
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    def conv(A,B,H):
        return [sum(A[j]*B[i-j] for j in range(len(A)) if 0<=i-j<len(B)) for i in range(H)]
    for k in range(6):
        L = k+1;d = lcm(*range(1,L,2))
        A = [2*d//i if i%2 else 0 for i in range(L)]
        x,p,q = horner(A,2),2**L,2**k
        assert x+2*d<=2*d*q and p==q*2 and x<=d*p
        for N in range(6):
            K = N+1;J = K*L;v = 2**J;H = J+1
            W = [factorial(N)//factorial(j)*d**(N-j) for j in range(K)]
            rows = [];current = [1]+[0]*J
            for j in range(K):
                rows.append(current);current = conv(A,current,H)
            V = [horner(row,2) for row in rows]
            Z = [w*y for w,y in zip(W,V)]
            total = [sum(W[j]*rows[j][i] for j in range(K)) for i in range(H)]
            s = sum(Z);scale = W[0]*v
            assert d*p>0 and scale>0 and 2*x<=2*(d*p)
            assert Z[0]==scale and horner(total,2)==s
            assert all(p**j*y==(v*2**j)*x**j for j,y in enumerate(V))
            assert all(((j+1)*(d*p))*Z[j+1]==(2*x)*Z[j] for j in range(N))
            assert Fraction(s,scale)==sum(Fraction(2*x,d*p)**j/factorial(j) for j in range(K))
            assert s<=9*scale


def test_ordinary_replay_constructs_all_traces_without_new_induction():
    result = majorant.prove_composition_majorant()
    assert result.receipt.target==majorant.frozen_composition_majorant_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    assert len(result.bundle.nodes)==325


def test_forged_finite_bound_ancestor_and_root_and_false_target_are_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import decode_proof_bundle,check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    limits = BinaryDAGLimits().bundle_limits()
    rows = majorant.read_mixed_archive(CHECKED_ARCHIVE)
    bundle,target = decode_proof_bundle(majorant.canonical(["peano-lab-bundle-v1",324,rows[324][1],rows]).decode()+"\n",limits=limits)
    assert target==majorant.frozen_composition_majorant_target()
    ancestor_target = parse_named(majorant.ENDPOINT_SOURCES["finite_bound"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in bundle.nodes if n.target==ancestor_target]
    assert len(ancestors)==1
    for node_id in (bundle.root,ancestors[0]):
        forged = replace(bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,target,limits=limits)
    with pytest.raises(ProofBundleError):
        check_proof_bundle(bundle,Bot(),limits=limits)
