"""Actual row evaluation graphs are total, conservative and extensional."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_row_horner_values as values


def test_exact_unconditional_actual_prefix_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = values.frozen_row_horner_values_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert values.json_hash(encode_formula(target))==values.TARGET_SHA256
    assert len(values.canonical(encode_formula(target)))==4406
    c = values.source_contract()
    assert c["actual_row_value_prefix_constructed"] is c["extensional_all_actual_values"] is True
    assert c["arbitrary_encoded_rows_allowed"] is c["zero_multiplier_and_empty_lengths_allowed"] is True
    assert c["power_trace_required"] is c["code_number_uniqueness"] is c["closes_IR072"] is False


def test_conservative_definition_dag_contains_only_actual_computations():
    from peano_lab.library.proof_bundle import encode_formula
    registry = values.definition_registry()
    assert values.source_contract()["new_definition_ids"]==["ND0437","ND0438"]
    for identifier,name,params,source,deps,digest in values.DEFINITIONS:
        d = registry[name]
        assert d.stable_id==identifier and values.json_hash(encode_formula(d.template_formula))==digest
        assert tuple(d.conceptual_dependencies)==deps
        assert "Sum(" not in source and "Pow(" not in source and "Le(" not in source
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()
    bad = list(values.DEFINITIONS)
    row = list(bad[0]);row[3] = "y=0";bad[0] = tuple(row)
    with patch.object(values,"DEFINITIONS",tuple(bad)),pytest.raises(ValueError):
        values.definition_registry()


def test_omitted_actual_row_or_value_is_rejected():
    for source in (values.NAMED_SOURCE.replace("NatPowerRow(pb,pc,qb,qc,k,ub,uc) -> ",""),
                   values.NAMED_SOURCE.replace("NatHornerValue(ub,uc,t,H,y) -> ",""),
                   values.NAMED_SOURCE.replace("BetaAt(vb,vc,k,y)","y=0")):
        with patch.object(values,"NAMED_SOURCE",source),pytest.raises(ValueError):
            values.frozen_row_horner_values_target()


def test_helper_targets_and_actual_owned_ancestor_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = values.definition_registry()
    assert {n:values.json_hash(encode_formula(parse_named(s,registry=registry)))
        for n,s in values.HELPER_SOURCES.items()}==values.HELPER_TARGET_SHA256
    rows = values.read_mixed_archive(values.EVALUATION_ARCHIVE)
    for name,source in values.ENDPOINT_SOURCES.items():
        ast = encode_formula(parse_named(source,registry=registry))
        matches = [row for row in rows if row[1]==ast]
        assert len(matches)==1 and matches[0][3]
        assert values.ENDPOINT_OWNERS[name]=="CV058"


def test_changed_actual_archive_is_rejected():
    for key in ("sha256","target_ast_sha256"):
        pin = dict(values.EVALUATION_ARCHIVE);pin[key] = "0"*64
        with pytest.raises(ValueError):
            values.read_mixed_archive(pin)


def test_finite_nonpower_rows_zero_and_empty_evaluations():
    def horner(row,t):
        y = 0
        for a in row:
            y = t*y+a
        return y
    for K in range(5):
        for H in range(4):
            rows = [[(i+1)*(j+2)%5 for j in range(H)] for i in range(K)]
            for t in range(4):
                prefix = [horner(row,t) for row in rows]
                assert len(prefix)==K
                for k,row in enumerate(rows):
                    assert prefix[k]==sum(a*t**(H-1-j) for j,a in enumerate(row))
    assert horner([2,3],0)==3 and horner([],3)==0


def test_ordinary_replay_and_forged_value_uniqueness_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = values.prove_row_horner_values()
    assert result.receipt.target==values.frozen_row_horner_values_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(values.HELPER_SOURCES["value_unique"],registry=values.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
