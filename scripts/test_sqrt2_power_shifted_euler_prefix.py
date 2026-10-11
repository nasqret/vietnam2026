"""Constructed shifted coefficient tables, hygiene and actual proof controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_shifted_euler_prefix as shifted


def test_exact_target_constructs_shifted_table_with_no_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = shifted.frozen_shifted_euler_prefix_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==3 and not premises and type(conclusion) is Exists
    assert shifted.json_hash(encode_formula(target))==shifted.TARGET_SHA256
    assert len(shifted.canonical(encode_formula(target)))==667
    contract = shifted.source_contract()
    assert contract["actual_shifted_euler_table_constructed"] is True
    assert contract["finite_composition_chain_rule"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_exact_definition_and_hygienic_colliding_input_code_names():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = shifted.definition_registry()
    d = r["NatShiftedEulerPrefix"]
    assert d.stable_id=="ND0422" and d.conceptual_dependencies==("Lt","BetaAt")
    assert shifted.json_hash(encode_formula(d.template_formula))==shifted.DEFINITION_SHA256
    assert "Sum(" not in shifted.DEFINITION_SOURCE and "Convolution" not in shifted.DEFINITION_SOURCE
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("i","a","db","dc","N")
    alias = parse_named("NatShiftedEulerPrefix(i,a,db,dc,N)",names,r)
    explicit = parse_named("forall j v. Lt(j,N) -> BetaAt(i,a,S j,v) -> BetaAt(db,dc,j,(S j)*v)",names,r)
    assert alias==explicit


def test_wrong_shift_or_multiplier_is_rejected():
    for wrong in (shifted.DEFINITION_SOURCE.replace("ac,S i,a","ac,i,a"),shifted.DEFINITION_SOURCE.replace("(S i)*a","i*a")):
        assert wrong!=shifted.DEFINITION_SOURCE
        with patch.object(shifted,"DEFINITION_SOURCE",wrong),pytest.raises(ValueError):
            shifted.definition_registry()


def test_actual_euler_and_affine_dependency_endpoints_and_helpers_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = shifted.definition_registry()
    assert {name:shifted.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in shifted.HELPER_SOURCES.items()}==shifted.HELPER_TARGET_SHA256
    found = set()
    for pin in shifted.ARCHIVES:
        rows = shifted.read_archive(pin)
        for name,source in shifted.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==shifted.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in shifted.ARCHIVES}=={"CV007","CV008"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in shifted.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                shifted.read_archive(changed)


def test_finite_shifted_euler_construction_including_empty_outputs():
    for N in range(6):
        for values in product(range(3),repeat=N+1):
            euler = [i*a for i,a in enumerate(values)]
            sliced = euler[1:N+1]
            assert sliced==[(i+1)*values[i+1] for i in range(N)]
    assert [0,3,8][1:]==[3,8]
    assert []==[0][1:1]


def test_guarded_shifted_operator_replays_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = shifted.prove_shifted_euler_prefix()
    assert result.receipt.target==shifted.frozen_shifted_euler_prefix_target()
    assert len(result.bundle.nodes)==107
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==4967
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
