"""Exact canonical traces, conservative notation and hostile HA boundaries."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_canonical_quadratic_trace as trace


def test_exact_unconditional_canonical_trace_statement():
    from peano_lab.kernel.formulas import Forall,Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target = trace.frozen_canonical_quadratic_trace_target()
    assert trace.json_hash(encode_formula(target)) == trace.TARGET_SHA256
    assert len(trace.canonical(encode_formula(target))) == 4889
    for kind,count in ((Forall,9),(Exists,8)):
        for _ in range(count):
            assert type(target) is kind
            target = target.body
    assert type(target) is And
    contract = trace.source_contract()
    assert contract["premise_count"] == 0 and contract["canonical_outputs_constructed"] is True
    for key in ("nonzero_factors_required","height_bound_in_definition","finite_trace_height_bound",
                "ordinary_trace_bridge_proved","real_interpretation","closes_IR046","closes_IR072",
                "original_HA_checked"):
        assert contract[key] is False


def test_canonical_definitions_separate_from_unchanged_balanced_trace():
    registry = trace.definition_registry()
    assert registry["IQuadProductTrace"].stable_id == "ND0392"
    assert registry["IQuadCanonicalStep"].stable_id == "ND0396"
    assert registry["IQuadCanonicalTrace"].stable_id == "ND0397"
    assert registry["IQuadCanonicalStep"].arity == registry["IQuadCanonicalTrace"].arity == 17
    assert registry["IQuadCanonicalStep"].conceptual_dependencies == ("IQuadAt","IQuadCanonicalProduct")
    assert registry["IQuadCanonicalTrace"].conceptual_dependencies == ("IQuadAt","Lt","IQuadCanonicalStep")
    for row in trace.DEFINITION_ROWS:
        assert "IQuadHeight" not in row[3] and "Nonzero" not in row[3]


def test_definition_mutations_and_id_collisions_fail_closed():
    for index,old,new in ((0,",S i,",",i,"),(1,",0,1,0,0,0)",",0,0,0,0,0)")):
        rows = list(trace.DEFINITION_ROWS)
        row = list(rows[index])
        assert old in row[3]
        row[3] = row[3].replace(old,new)
        rows[index] = tuple(row)
        with patch.object(trace,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
            trace.definition_registry()
    rows = list(trace.DEFINITION_ROWS)
    row = list(rows[0])
    row[0] = 394
    rows[0] = tuple(row)
    with patch.object(trace,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        trace.definition_registry()


def test_capture_safe_canonical_trace_and_helper_target_hashes():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = trace.definition_registry()
    for name,source,deps,digest in trace.HELPERS:
        assert trace.json_hash(encode_formula(parse_named(source,registry=registry))) == digest
    names = trace.F+trace.U+("L",)
    actual = parse_named(trace.trace(trace.F,trace.U,"S L"),names,registry)
    expected = parse_named(trace.at(trace.U,"0",("1","0","0","0"))+" /\\ (forall j. Lt(j,S L) -> "+
        trace.named("IQuadCanonicalStep",*trace.F,*trace.U,"j")+")",names,registry)
    assert actual == expected


def test_actual_105_row_prefix_preserved_not_parent_receipt_lookup():
    rows = trace.inert_prefix_rows()
    assert len(rows) == 105
    assert trace.json_hash(rows) == trace.PREFIX_ROWS_SHA256
    assert len(trace.canonical(rows)) == 157671
    with patch.object(trace,"PREFIX_ROWS_SHA256","0"*64),pytest.raises(ValueError):
        trace.inert_prefix_rows()


def test_finite_host_beta_calibration_includes_zero_factors_and_empty_trace():
    from test_sqrt2_power_quadratic_height import canonical_product,mass
    from test_sqrt2_power_quadratic_product_trace import streams,quad_at,balances
    choices = ((0,0,0,0),(1,0,0,0),(0,1,2,1),(1,1,1,1))
    for length in range(4):
        for factors in product(choices,repeat=length):
            values = [(1,0,0,0)]
            for factor in factors:
                values.append(canonical_product(values[-1],factor))
            factor_codes,trace_codes = streams(factors),streams(values)
            assert quad_at(trace_codes,0,(1,0,0,0))
            for i,factor in enumerate(factors):
                assert quad_at(factor_codes,i,factor)
                assert quad_at(trace_codes,i,values[i])
                assert quad_at(trace_codes,i+1,values[i+1])
                assert balances(values[i],factor,values[i+1]) == (True,True)
                assert mass(values[i+1]) <= mass(values[i])*mass(factor)


def test_guarded_canonical_replay_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = trace.prove_canonical_quadratic_trace()
    assert result.receipt.target == trace.frozen_canonical_quadratic_trace_target()
    assert len(result.bundle.nodes) == 108
    assert result.receipt.total_body_nodes == 5268
    assert result.provenance["root_induction_count"] == 1
    assert result.provenance["new_axioms"] == []
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
