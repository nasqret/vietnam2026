"""Finite tail bound includes valid rational denominators and exact powers."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_rational_tail_majorant as majorant


def test_exact_rational_tail_contract_and_normalization():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_rational_tail_majorant_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==4 and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==11651
    c = majorant.source_contract()
    assert c["nonzero_normalization_required"] is c["whole_table_majorant_required"] is True
    assert c["actual_tail_and_base_three_value_constructed"] is c["rational_division_transport_proved"] is True
    assert c["rational_bound"]=="u/(D*3^(M+r)) <= B*2^M/3^M"
    assert c["empty_tail_case_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_valid_rational_order_definition_and_hygiene():
    from sqrt2_power_definitions import parse_named,DEFINITIONS
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry()
    identifier,name,params,source,deps,digest = majorant.DEFINITIONS[0]
    base = dict(majorant.base_registry());base["IRatValid"] = DEFINITIONS["IRatValid"]
    d = registry[name]
    assert d.stable_id==identifier=="ND0444" and tuple(d.conceptual_dependencies)==deps==("IRatValid","Le")
    assert d.template_formula==parse_named(source,params,base)
    assert majorant.json_hash(encode_formula(d.template_formula))==digest
    assert registry["IRatValid"]==DEFINITIONS["IRatValid"]
    assert all(registry[n]==v for n,v in majorant.base_registry().items())
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()
    for altered in (("ND0443",name,params,source,deps,digest),
                    (identifier,"NatScaledExpRecurrence",params,source,deps,digest),
                    (identifier,name,params,source.replace("p*D","p*d"),deps,digest)):
        with patch.object(majorant,"DEFINITIONS",(altered,)),pytest.raises(ValueError):
            majorant.definition_registry()


def test_missing_guard_or_wrong_rational_denominator_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace("~D=0 -> ",""),
                   majorant.NAMED_SOURCE.replace("IRatLe(u,0,D*h,B*p,0,q)","IRatLe(u,0,h,B*p,0,q)"),
                   majorant.NAMED_SOURCE.replace("IRatLe(u,0,D*h,B*p,0,q)","IRatLe(u,0,D*h,B,0,q)"),
                   majorant.NAMED_SOURCE.replace("NatAffineSlice(ab,ac,M,1,tb,tc,S r)","NatAffineSlice(ab,ac,0,1,tb,tc,S r)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_rational_tail_majorant_target()


def test_owned_actual_tail_power_add_and_guarded_cancellation_bodies():
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
    assert found==majorant.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in majorant.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                majorant.read_mixed_archive(pin)


def test_exact_rational_tail_model_zero_bound_cutoff_and_scale():
    from fractions import Fraction
    def horner(A,t):
        result = 0
        for a in A:
            result = t*result+a
        return result
    for M in range(4):
        for r in range(4):
            J = M+r;H = J+1
            for A in ([0]*H,[1]*H,[i%3 for i in range(H)],[0]*J+[2**J]):
                y,v = horner(A,2),2**J
                for D in range(1,4):
                    B = (y+D*v-1)//(D*v)
                    u,p,q,h = horner(A[M:],3),2**M,3**M,3**J
                    assert y<=B*D*v and D*h>0 and q>0
                    assert u*q<=(B*p)*(D*h)
                    tail = sum(Fraction(A[i],D*3**i) for i in range(M,H))
                    assert Fraction(u,D*h)==tail<=B*Fraction(2,3)**M
    assert Fraction(4,9)>Fraction(1,9)


def test_ordinary_replay_and_forged_power_addition_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_rational_tail_majorant()
    assert result.receipt.target==majorant.frozen_rational_tail_majorant_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["power_add"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
