"""Actual weighted powers retain their graph and exact sum prefix."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_power_weighted_prefix as terms


def test_exact_constructed_terms_and_sum_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = terms.frozen_power_weighted_prefix_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and not premises and type(conclusion) is Exists
    assert terms.json_hash(encode_formula(target))==terms.TARGET_SHA256
    assert len(terms.canonical(encode_formula(target)))==3728
    c = terms.source_contract()
    assert c["actual_power_weighted_prefix_constructed"] is c["actual_same_prefix_sum_constructed"] is True
    assert c["arbitrary_weight_codes"] is c["zero_base_and_empty_prefix_allowed"] is True
    assert c["actual_power_graph_required"] is True and c["identity"]=="T[j]=W[j]*x^j"
    assert c["factorial_normalization_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_power_product_definition_and_hygiene():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = terms.definition_registry()
    identifier,name,params,source,deps,digest = terms.DEFINITIONS[0]
    d = registry[name]
    assert terms.source_contract()["new_definition_ids"]==["ND0442"]
    assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
    assert d.template_formula==parse_named(source,params,terms.base_registry())
    assert terms.json_hash(encode_formula(d.template_formula))==digest
    assert "Sum" not in deps and "NatRatioBoundPrefix" not in deps
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()
    for altered in (("ND0440",name,params,source,deps,digest),
                    (identifier,"NatHornerValue",params,source,deps,digest),
                    (identifier,name,params,source.replace("Pow(x,j,p)","Pow(x,S j,p)"),deps,digest)):
        with patch.object(terms,"DEFINITIONS",(altered,)),pytest.raises(ValueError):
            terms.definition_registry()


def test_changed_weight_codes_base_or_sum_prefix_is_rejected():
    for source in (terms.NAMED_SOURCE.replace("NatPowerWeightedPrefix(x,wb,wc", "NatPowerWeightedPrefix(S x,wb,wc"),
                   terms.NAMED_SOURCE.replace("NatPowerWeightedPrefix(x,wb,wc,tb,tc,K)","NatPowerWeightedPrefix(x,wc,wb,tb,tc,K)"),
                   terms.NAMED_SOURCE.replace("Sum(tb,tc,K,s)","Sum(tb,tc,S K,s)")):
        with patch.object(terms,"NAMED_SOURCE",source),pytest.raises(ValueError):
            terms.frozen_power_weighted_prefix_target()


def test_owned_actual_power_uniqueness_extension_and_sum_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = terms.definition_registry()
    found = set()
    for pin in terms.ARCHIVES:
        rows = terms.read_mixed_archive(pin)
        for name,source in terms.ENDPOINT_SOURCES.items():
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==terms.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in terms.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                terms.read_mixed_archive(pin)


def test_exact_weighted_power_model_including_zero_and_empty():
    for x in range(5):
        for K in range(8):
            W = [(j*j+3)%7 for j in range(K)]
            T = [w*x**j for j,w in enumerate(W)]
            assert sum(T)==sum(w*x**j for j,w in enumerate(W))
            if K:
                assert T[0]==W[0]
                if x==0:
                    assert all(t==0 for t in T[1:])
                    assert sum(T)==W[0]
            else:
                assert T==[] and sum(T)==0
    assert 3*2**0 != 3*2**1
    assert sum([3,2,0])!=sum([3,2,0,7])


def test_ordinary_replay_and_forged_power_uniqueness_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = terms.prove_power_weighted_prefix()
    assert result.receipt.target==terms.frozen_power_weighted_prefix_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(terms.ENDPOINT_SOURCES["power_unique"],registry=terms.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
