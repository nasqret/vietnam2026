"""Actual finite composition, boundary models and adversarial proof checks."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_finite_composition_euler as composition


def test_exact_unconditional_root_constructs_all_five_finite_objects():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = composition.frozen_finite_composition_euler_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    witnesses = 0
    while type(conclusion) is Exists:
        witnesses += 1
        conclusion = conclusion.body
    assert witnesses==16
    assert composition.json_hash(encode_formula(target))==composition.TARGET_SHA256
    assert len(composition.canonical(encode_formula(target)))==17594
    contract = composition.source_contract()
    assert contract["actual_euler_power_shift_and_both_weighted_traces_constructed"] is True
    assert contract["finite_composition_euler_identity"] is True
    assert contract["constant_input_coefficient_need_not_vanish"] is True
    assert contract["exp_composition_recurrence"] is contract["rational_denominator_transport"] is contract["closes_IR072"] is False


def test_exact_conditional_induction_helpers_and_unchanged_definition_dag():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    r = composition.definition_registry()
    assert {name:composition.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in composition.HELPER_SOURCES.items()}==composition.HELPER_TARGET_SHA256
    binders,premises,conclusion = strip_target(parse_named(composition.HELPER_SOURCES["chain_rule"],registry=r))
    assert binders==22 and len(premises)==1 and type(conclusion) is Forall
    assert composition.source_contract()["new_definition_ids"]==[]
    for supplied in (composition.weighted_registry(),composition.shifted_registry(),composition.power_registry()):
        for name,d in supplied.items():
            assert r[name].template_formula==d.template_formula
            assert r[name].stable_id==d.stable_id
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_missing_width_or_wrong_terminal_degree_is_rejected():
    for wrong in (composition.NAMED_SOURCE.replace("Lt(i,H) -> ",""),composition.NAMED_SOURCE.replace("tb,tc,vb,vc,S N,fb,fc","tb,tc,vb,vc,N,fb,fc")):
        assert wrong!=composition.NAMED_SOURCE
        with patch.object(composition,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            composition.frozen_finite_composition_euler_target()


def test_actual_four_archive_ancestor_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = composition.definition_registry()
    formulas = {name:encode_formula(parse_named(source,registry=r)) for name,source in composition.ENDPOINT_SOURCES.items()}
    found = set()
    for pin in composition.ARCHIVES:
        rows = composition.read_archive(pin)
        for name,formula in formulas.items():
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==composition.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in composition.ARCHIVES}=={"CV003","CV017","CV019","CV020"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in composition.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                composition.read_archive(changed)


def test_finite_composition_model_arbitrary_constant_terms_and_boundaries():
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    for L in range(4):
        for a in product(range(3),repeat=L):
            ea = [i*x for i,x in enumerate(a)]
            for N in range(4):
                for H in range(5):
                    powers = [[int(i==0) for i in range(H)]]
                    for _ in range(N):
                        powers.append([coefficient(a,powers[-1],i) for i in range(H)])
                    for weights in product(range(3),repeat=N+1):
                        derivative_weights = [(k+1)*weights[k+1] for k in range(N)]
                        q,r = [0]*H,[0]*H
                        for k in range(N+1):
                            q = [v+weights[k]*p for v,p in zip(q,powers[k])]
                        for k in range(N):
                            r = [v+derivative_weights[k]*p for v,p in zip(r,powers[k])]
                        for i in range(H):
                            assert i*q[i]==coefficient(ea,r,i)
    # At the omitted coefficient i=H=1, padded Q=[0] and EA*R disagree.
    assert 1*0!=coefficient([0,1],[1],1)
    # Unshifted outer weights also fail: A=2X, outer polynomial 3+5X.
    assert 10==coefficient([0,2],[5,0],1)
    assert 10!=coefficient([0,2],[3,0],1)


def test_guarded_chain_rule_replays_full_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = composition.prove_finite_composition_euler()
    assert result.receipt.target==composition.frozen_finite_composition_euler_target()
    assert len(result.bundle.nodes)==208
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==14786
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
