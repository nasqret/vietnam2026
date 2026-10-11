"""Finite ratio domination: no convergence axiom or hidden sum bound."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_ratio_sum_bound as majorant


def test_exact_actual_sum_and_ratio_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = majorant.frozen_ratio_sum_bound_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==2 and type(conclusion) is Exists
    assert majorant.json_hash(encode_formula(target))==majorant.TARGET_SHA256
    assert len(majorant.canonical(encode_formula(target)))==2413
    c = majorant.source_contract()
    assert c["explicit_consecutive_ratio_bounds_required"] is c["actual_head_required"] is True
    assert c["actual_sum_constructed"] is c["empty_prefix_and_zero_ratio_allowed"] is True
    assert c["supplied_sum_helper"] is True and c["inequality"]=="s<=(r+1)*a0"
    assert c["finite_exp_sum_bound_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_ratio_definition_and_hygienic_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = majorant.definition_registry()
    identifier,name,params,source,deps,digest = majorant.DEFINITIONS[0]
    d = registry[name]
    assert majorant.source_contract()["new_definition_ids"]==["ND0441"]
    assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
    assert d.template_formula==parse_named(source,params,majorant.base_registry())
    assert majorant.json_hash(encode_formula(d.template_formula))==digest
    assert "Sum" not in deps
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()
    for altered in (("ND0440",name,params,source,deps,digest),
                    (identifier,"NatBoundedPrefix",params,source,deps,digest),
                    (identifier,name,params,source.replace("Lt(S i,N)","Lt(i,N)"),deps,digest)):
        with patch.object(majorant,"DEFINITIONS",(altered,)),pytest.raises(ValueError):
            majorant.definition_registry()


def test_removed_ratio_or_wrong_head_or_constant_is_rejected():
    for source in (majorant.NAMED_SOURCE.replace(majorant.RATIO+" -> ",""),
                   majorant.NAMED_SOURCE.replace("BetaAt(ab,ac,0,a0)","BetaAt(ab,ac,1,a0)"),
                   majorant.NAMED_SOURCE.replace("Le(s,(S r)*a0)","Le(s,r*a0)")):
        with patch.object(majorant,"NAMED_SOURCE",source),pytest.raises(ValueError):
            majorant.frozen_ratio_sum_bound_target()


def test_owned_actual_sum_and_order_bodies():
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


def test_exact_finite_ratio_model_including_empty_prefix():
    for r in range(4):
        for N in range(5):
            for A in product(range(5),repeat=max(1,N)):
                if all((r+1)*A[i+1]<=r*A[i] for i in range(N-1)):
                    assert sum(A[:N])<=(r+1)*A[0]
                    for k in range(N):
                        assert sum(A[:k+1])+r*A[k]<=(r+1)*A[0]
    assert not sum([1,1,1,1])<=3
    assert not sum([1,0])<=0
    assert not sum([3,2,1])<=3*1
    for n in range(1,8):
        A = [2**i*3**(n-1-i) for i in range(n)]
        assert all(3*A[i+1]==2*A[i] for i in range(n-1))
        assert sum(A)+2*A[-1]==3*A[0]


def test_ordinary_replay_and_forged_sum_decomposition_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = majorant.prove_ratio_sum_bound()
    assert result.receipt.target==majorant.frozen_ratio_sum_bound_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(majorant.ENDPOINT_SOURCES["sum_decompose"],registry=majorant.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
