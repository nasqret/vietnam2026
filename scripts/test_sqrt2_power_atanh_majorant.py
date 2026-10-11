"""The inner-polynomial bound uses one actual table and exact denominator."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_majorant as majorant


def test_exact_constructed_atanh_majorant_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_atanh_majorant_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and premises==[] and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==5244
    c = majorant.source_contract()
    assert c["actual_atanh_prefix_constructed"] is c["same_coefficient_table_throughout"] is True
    assert c["actual_nonzero_denominator_constructed"] is c["zero_head_and_coefficient_bound_proved"] is True
    assert c["actual_horner_value_and_power_constructed"] is c["arbitrary_supplied_prefix_helper"] is True
    assert c["rational_division_transport_claimed"] is c["analytic_logarithm_identity"] is c["closes_IR072"] is False
    assert c["IR_parents_closed"]==c["library_admissions"]==0


def test_existing_conservative_definitions_preserved_exactly():
    registry = majorant.definition_registry()
    assert majorant.source_contract()["new_definition_ids"]==[]
    for base in (majorant.atanh_registry(),majorant.bounded_registry()):
        for name,d in base.items():
            assert registry[name].stable_id==d.stable_id
            assert registry[name].template_formula==d.template_formula
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert registry["NatAtanhPrefix"].stable_id=="ND0425"
    assert registry["NatBoundedPrefix"].stable_id=="ND0440"
    assert registry["NatHornerValue"].stable_id=="ND0437"


def test_changed_denominator_table_or_bound_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace("~d=0 /\\ ",""),
                   majorant.NAMED_SOURCE.replace("NatAtanhPrefix(d,ab,ac,S k)","NatAtanhPrefix(S d,ab,ac,S k)"),
                   majorant.NAMED_SOURCE.replace("NatHornerValue(ab,ac,2,S k,y)","NatHornerValue(ac,ab,2,S k,y)"),
                   majorant.NAMED_SOURCE.replace("Le(y+2*d,(2*d)*p)","Le(y+2*d,d*p)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_atanh_majorant_target()


def test_actual_owned_atanh_and_bounded_horner_bodies():
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


def test_finite_atanh_model_with_exact_rational_interpretation():
    from fractions import Fraction
    from math import lcm
    for k in range(16):
        d = lcm(*range(1,k+1,2))
        A = [0 if i%2==0 else 2*d//i for i in range(k+1)]
        assert d>0 and A[0]==0
        y = 0
        for i,a in enumerate(A):
            assert a<=2*d
            assert a==0 if i%2==0 else i*a==2*d
            y = 2*y+a
        p = 2**k
        assert y+2*d<=2*d*p
        actual = sum(Fraction(a,d*2**i) for i,a in enumerate(A))
        assert actual==Fraction(y,d*p)<=2
    assert Fraction(2,3)>0
    assert 2*3//3 < 2*3


def test_ordinary_replay_and_forged_coefficient_authority_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_atanh_majorant()
    assert result.receipt.target==majorant.frozen_atanh_majorant_target()
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["atanh_exists"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
