"""Zero-headed bounded prefixes: exact graphs, conservative bounds and replay."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_bounded_horner as majorant


def test_exact_zero_head_and_separate_bound_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_bounded_horner_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and len(premises)==2 and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==3914
    c = majorant.source_contract()
    assert c["zero_head_required"] is c["separate_coefficient_bound_required"] is True
    assert c["actual_horner_value_and_power_constructed"] is c["zero_bound_allowed"] is True
    assert c["length"]=="k+1" and c["power"]=="2^k" and c["inequality"]=="y+D<=D*p"
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False
    assert c["IR_parents_closed"]==c["library_admissions"]==0


def test_conservative_bound_definition_dag_and_collision_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry()
    assert majorant.source_contract()["new_definition_ids"]==["ND0440"]
    identifier,name,params,source,deps,digest = majorant.DEFINITIONS[0]
    d = registry[name]
    assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
    assert d.template_formula==parse_named(source,params,majorant.base_registry())
    assert majorant.json_hash(encode_formula(d.template_formula))==digest
    assert "NatScaledHornerTrace" not in deps and "NatHornerValue" not in deps
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()
    for altered in (("ND0437",name,params,source,deps,digest),
                    (identifier,"NatHornerValue",params,source,deps,digest),
                    (identifier,name,params,source.replace("Le(a,D)","Le(D,a)"),deps,digest)):
        with patch.object(majorant,"DEFINITIONS",(altered,)),pytest.raises(ValueError):
            majorant.definition_registry()


def test_weakened_premises_or_changed_integer_majorant_are_rejected():
    for source in (majorant.NAMED_SOURCE.replace("BetaAt(ab,ac,0,0) -> ",""),
                   majorant.NAMED_SOURCE.replace("NatBoundedPrefix(ab,ac,D,S k)","NatBoundedPrefix(ab,ac,D,k)"),
                   majorant.NAMED_SOURCE.replace("Pow(2,k,p)","Pow(2,S k,p)"),
                   majorant.NAMED_SOURCE.replace("Le(y+D,D*p)","Le(y+D,p)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_bounded_horner_target()


def test_owned_actual_arithmetic_and_computation_bodies():
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


def test_finite_majorant_including_zero_bound_and_necessary_premises():
    def horner(A):
        y = 0
        for a in A:
            y = 2*y+a
        return y
    for D in range(4):
        for k in range(5):
            for tail in product(range(D+1),repeat=k):
                assert horner((0,)+tail)+D<=D*2**k
            assert horner((0,)+(D,)*k)+D==D*2**k
    assert not horner((1,))+1<=1
    assert not horner((0,2))+1<=2
    assert not horner((0,1,1))+1<=2


def test_ordinary_replay_and_forged_bound_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_bounded_horner()
    assert result.receipt.target==majorant.frozen_bounded_horner_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["mul_left_mono"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
