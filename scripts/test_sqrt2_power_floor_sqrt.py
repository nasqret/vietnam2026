"""Exact conservative square-root reuse and full ordinary proof boundaries."""
from dataclasses import replace
from hashlib import sha256
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_floor_sqrt as floor


def test_exact_unconditional_totality_and_uniqueness_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=floor.frozen_floor_sqrt_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and premises==[] and type(conclusion) is Exists
    assert len(floor.canonical(encode_formula(target)))==441
    c=floor.source_contract()
    assert c["actual_floor_root_constructed"] is c["all_competing_roots_equal"] is c["zero_input_allowed"] is True
    assert c["audited_reuse_not_new_discovery"] is True
    assert c["new_induction_needed"] is c["real_square_root_or_dyadic_accuracy_claim"] is c["closes_IR072"] is False


def test_original_definition_source_ast_and_dependency_dag_preserved():
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.library.proof_bundle import encode_formula
    registry=floor.definition_registry()
    assert set(registry)=={"Le","Lt","FloorSqrt"}
    for identifier,name,parameters,source,deps,digest in floor.DEFINITION_ROWS:
        d=registry[name]
        assert d.stable_id==identifier and d.parameters==parameters
        assert sha256(d.template_source.encode()).hexdigest()==digest
        assert floor.json_hash(encode_formula(d.template_formula))==floor.DEFINITION_AST_SHA256[name]
        assert parse_formula_in_context(d.template_source,list(parameters))==d.template_formula
        assert d.conceptual_dependencies==deps
    c=floor.source_contract()
    assert c["new_definition_ids"]==[]
    assert c["definition_admissions"]==c["IR_parents_closed"]==c["library_admissions"]==0


def test_changed_existence_uniqueness_or_floor_bound_is_rejected():
    original=floor.NAMED_SOURCE
    for source in ("forall n. exists s. FloorSqrt(n,s)",
                   original.replace("t=s","t=n"),original.replace("FloorSqrt(n,t)","Le(t*t,n)")):
        assert source!=original
        with patch.object(floor,"NAMED_SOURCE",source),pytest.raises(ValueError):
            floor.frozen_floor_sqrt_target()
    with patch.object(floor,"DEFINITION_AST_SHA256",dict(floor.DEFINITION_AST_SHA256,FloorSqrt="0"*64)),pytest.raises(ValueError):
        floor.definition_registry()


def test_actual_30_node_historical_cone_and_fail_closed_pins():
    ids,rows=floor.inert_ancestor_rows()
    assert ids==floor.ANCESTOR_IDS and len(rows)==30
    assert floor.json_hash(rows)==floor.ANCESTOR_ROWS_SHA256
    assert set(d for row in rows for d in row[2])<=set(ids)
    with patch.object(floor,"ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        floor.inert_ancestor_rows()
    with patch.object(floor,"ANCESTOR_ROWS_SHA256","0"*64),pytest.raises(ValueError):
        floor.inert_ancestor_rows()
    altered=dict(floor.ENDPOINTS);n,source,_=altered["total"];altered["total"]=(n,source,"0"*64)
    with patch.object(floor,"ENDPOINTS",altered),pytest.raises(ValueError):
        floor.inert_ancestor_rows()


def test_finite_floor_models_include_zero_squares_and_successors():
    for n in range(257):
        s=isqrt(n)
        assert s*s<=n<(s+1)*(s+1)
        assert [t for t in range(s+3) if t*t<=n<(t+1)*(t+1)]==[s]
    assert isqrt(0)==0 and isqrt(1)==1 and isqrt(2)==1


def test_complete_actual_body_replay_without_new_induction_or_axioms():
    result=floor.prove_floor_sqrt()
    assert result.receipt.target==result.target
    assert len(result.bundle.nodes)==31 and len(result.payload.encode())<65536
    p=result.provenance
    assert p["actual_ancestor_nodes"]==30 and p["canonical_bytes_replayed"] is True
    assert p["new_induction_count"]==0 and p["new_axioms"]==[]
    assert p["historical_input_not_decoded_as_certificate"] is True
    assert p["independent_lean_checked"] is False


def test_forged_historical_root_and_false_target_are_not_authority():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=floor.prove_floor_sqrt()
    node=result.provenance["endpoint_bundle_indices"]["total"]
    for index in (node,len(result.bundle.nodes)-1):
        forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==index else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())


def test_no_larger_final_decoder_or_body_limit_for_historical_input():
    from sqrt2_power_binary_dag import BinaryDAGLimits
    assert BinaryDAGLimits().max_payload_bytes==8*1024**2
    with pytest.raises(ValueError):
        floor.prove_floor_sqrt(limits=BinaryDAGLimits(max_nodes=30))
