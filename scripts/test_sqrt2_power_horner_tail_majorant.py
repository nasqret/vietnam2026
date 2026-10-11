"""Finite tail majorization retains actual shifts, values and powers."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_tail_majorant as majorant


def test_exact_constructed_finite_tail_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_horner_tail_majorant_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==6 and len(premises)==1 and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==7155
    c = majorant.source_contract()
    assert c["base_order_required"] is c["actual_shifted_tail_and_two_values_constructed"] is True
    assert c["actual_two_scaling_powers_constructed"] is c["zero_bases_allowed"] is True
    assert c["tail_length"]=="r+1" and c["whole_length"]=="N+(r+1)"
    assert c["rational_division_transport_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_hidden_majorant_definition():
    registry = majorant.definition_registry()
    assert majorant.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_wrong_shift_scaling_or_order_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace("Le(a,b) -> ",""),
                   majorant.NAMED_SOURCE.replace("NatAffineSlice(ab,ac,N,1", "NatAffineSlice(ab,ac,0,1"),
                   majorant.NAMED_SOURCE.replace("Pow(a,r,p)","Pow(a,S r,p)"),
                   majorant.NAMED_SOURCE.replace("Le(p*u,q*v)","Le(u,v)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_horner_tail_majorant_target()


def test_owned_actual_split_comparison_and_uniqueness_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry()
    found = set()
    for pin in majorant.ARCHIVES:
        rows = majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==majorant.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in majorant.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                majorant.read_mixed_archive(pin)


def test_tail_model_and_exact_two_thirds_rational_interpretation():
    from fractions import Fraction
    def horner(A,t):
        v = 0
        for c in A:
            v = t*v+c
        return v
    for N in range(4):
        for r in range(4):
            A = [(j*j+1)%7 for j in range(N+r+1)];tail = A[N:]
            for a in range(4):
                for b in range(a,5):
                    assert a**r*horner(tail,b)<=b**r*horner(A,a)
            actual = sum(Fraction(A[j],3**j) for j in range(N,len(A)))
            bound = Fraction(2,3)**N*sum(Fraction(c,2**j) for j,c in enumerate(A))
            assert actual<=bound
    assert not 3*horner([0,1],2)<=2*horner([0,1],3)


def test_ordinary_replay_and_forged_value_identity_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_horner_tail_majorant()
    assert result.receipt.target==majorant.frozen_horner_tail_majorant_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["value_unique"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
