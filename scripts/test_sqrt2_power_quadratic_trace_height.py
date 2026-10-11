"""Finite canonical height induction and its exact dependency boundaries."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_quadratic_trace_height as height


def test_exact_statement_keeps_all_four_mathematical_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = height.frozen_quadratic_trace_height_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==23 and len(premises)==4 and type(conclusion) is Exists
    assert height.json_hash(encode_formula(target))==height.TARGET_SHA256
    assert len(height.canonical(encode_formula(target)))==9024
    contract = height.source_contract()
    assert contract["canonical_trace_required"] is True
    assert contract["bounded_factors_required"] is True
    assert contract["relational_power_required"] is True
    assert contract["positive_height_required"] is False
    assert contract["closes_IR046"] is contract["closes_IR072"] is False


def test_order_power_and_height_definition_dag_is_closed_and_exact():
    registry = height.definition_registry()
    for name,(identifier,digest) in height.POWER_DEFINITIONS.items():
        assert registry[name].stable_id==identifier
        assert set(registry[name].conceptual_dependencies)<=registry.keys()
    assert registry["IQuadHeightBound"].stable_id=="ND0398"
    assert registry["IQuadHeightBound"].arity==5
    assert registry["IQuadFactorHeightBound"].stable_id=="ND0399"
    assert registry["IQuadFactorHeightBound"].arity==10
    assert registry["IQuadHeightBound"].conceptual_dependencies==("IQuadHeight","Le")
    assert registry["IQuadFactorHeightBound"].conceptual_dependencies==("Lt","IQuadAt","IQuadHeightBound")
    assert "Pow" not in height.DEFINITION_ROWS[1][3]
    assert "Trace" not in height.DEFINITION_ROWS[1][3]


def test_dropping_bound_or_power_or_changing_definition_is_rejected():
    for old in (height.named("IQuadFactorHeightBound",*height.F,"L","H")+" -> ","Pow(H,L,N) -> "):
        assert old in height.NAMED_SOURCE
        with patch.object(height,"NAMED_SOURCE",height.NAMED_SOURCE.replace(old,"")),pytest.raises(ValueError):
            height.frozen_quadratic_trace_height_target()
    rows = list(height.DEFINITION_ROWS)
    row = list(rows[0])
    row[3] = row[3].replace("Le(h,H)","Le(H,h)")
    rows[0] = tuple(row)
    with patch.object(height,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        height.definition_registry()


def test_actual_power_ancestor_cone_matches_named_statements():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    ids,rows = height.inert_power_rows()
    assert len(ids)==27
    assert height.json_hash(rows)==height.ANCESTOR_ROWS_SHA256
    assert len(height.canonical(rows))==53866
    registry,table = height.definition_registry(),dict(zip(ids,rows))
    for old,source in height.ENDPOINT_SOURCES.items():
        assert table[old][1]==encode_formula(parse_named(source,registry=registry))


def test_altered_power_archive_or_endpoint_source_fails_closed():
    with patch.object(height,"V28_ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        height.inert_power_rows()
    sources = dict(height.ENDPOINT_SOURCES)
    sources[195] = sources[195].replace("n=r*a","n=r+a")
    with patch.object(height,"ENDPOINT_SOURCES",sources),pytest.raises(ValueError):
        height.inert_power_rows()


def test_host_finite_height_bound_includes_zero_and_empty_cases():
    from test_sqrt2_power_quadratic_height import canonical_product,mass
    choices = ((0,0,0,0),(1,0,0,0),(0,1,0,0),(1,1,0,0),(0,0,1,1))
    for length in range(4):
        for factors in product(choices,repeat=length):
            cap = max((mass(factor) for factor in factors),default=0)
            value = (1,0,0,0)
            for factor in factors:
                value = canonical_product(value,factor)
            assert mass(value)<=cap**length
    assert 0**0==1


def test_guarded_full_induction_canonical_replay_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = height.prove_quadratic_trace_height()
    assert result.receipt.target==height.frozen_quadratic_trace_height_target()
    assert len(result.bundle.nodes)==41 and result.receipt.total_body_nodes==2836
    assert result.provenance["finite_trace_height_bound"] is True
    assert result.provenance["root_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
