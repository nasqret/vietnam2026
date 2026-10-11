"""Weighted evaluation transport with separate pointwise hypotheses."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_linearity as linearity


def test_exact_constructed_weighted_horner_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = linearity.frozen_horner_linearity_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==11 and len(premises)==1 and type(conclusion) is Exists
    assert linearity.json_hash(encode_formula(target))==linearity.TARGET_SHA256
    assert len(linearity.canonical(encode_formula(target)))==5246
    c = linearity.source_contract()
    assert c["pointwise_weighted_relation_required"] is c["three_actual_traces_constructed"] is True
    assert c["three_actual_endpoint_values_constructed"] is c["all_row_linearity_proved"] is True
    assert c["zero_scalars_and_multiplier_allowed"] is c["empty_prefix_allowed"] is True
    assert c["multiplication_evaluation_identity"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_weighted_relation_is_hygienic_and_dag_is_coherent():
    from sqrt2_power_definitions import parse_named
    r = linearity.definition_registry()
    assert linearity.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("i","a","b","c","d","e","f","g","h","N")
    assert parse_named("NatLinearTriple(i,a,b,c,d,e,f,g,h,N)",names,r)==parse_named(
        "forall j x y z. Lt(j,N) -> BetaAt(c,d,j,x) -> BetaAt(e,f,j,y) -> BetaAt(g,h,j,z) -> b*z=i*x+a*y",names,r)


def test_wrong_weight_or_missing_pointwise_relation_is_rejected():
    for source in (linearity.NAMED_SOURCE.replace("gamma*w=alpha*u+beta*v","gamma*w=alpha*u+gamma*v"),
                   linearity.NAMED_SOURCE.replace(linearity.GRAPH+" -> ","",1)):
        with patch.object(linearity,"NAMED_SOURCE",source),pytest.raises(ValueError):
            linearity.frozen_horner_linearity_target()


def test_helpers_and_owned_coding_and_ring_bodies_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = linearity.definition_registry()
    assert {name:linearity.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in linearity.HELPER_SOURCES.items()}==linearity.HELPER_TARGET_SHA256
    found = set()
    for pin in linearity.ARCHIVES:
        rows = linearity.read_mixed_archive(pin)
        for name,source in linearity.ENDPOINT_SOURCES.items():
            if linearity.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==linearity.ENDPOINT_SOURCES.keys()


def test_changed_actual_archive_is_rejected():
    for original in linearity.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                linearity.read_mixed_archive(changed)


def test_weighted_horner_model_with_zero_scalars_and_empty_prefixes():
    from itertools import product
    for alpha,beta,gamma,t,N in product(range(3),range(3),range(3),range(4),range(5)):
        x,y = list(range(N)),list(range(N,0,-1))
        a,b,c = [gamma*v for v in x],[gamma*v for v in y],[alpha*u+beta*v for u,v in zip(x,y)]
        u=v=w=0
        for ai,bi,ci in zip(a,b,c):
            u,v,w = t*u+ai,t*v+bi,t*w+ci
            assert gamma*w==alpha*u+beta*v
        assert gamma*w==alpha*u+beta*v
    assert 1*3!=1*1+1*1  # Without the coefficient relation, length one fails.


def test_guarded_weighted_evaluation_proof_replays_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = linearity.prove_horner_linearity()
    assert result.receipt.target==linearity.frozen_horner_linearity_target()
    assert len(result.bundle.nodes)==111
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5615
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
