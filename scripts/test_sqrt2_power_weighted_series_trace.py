"""Actual weighted trace construction and conservative computation contracts."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_weighted_series_trace as weighted


def test_exact_target_constructs_all_rows_without_input_power_or_trace_premise():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weighted.frozen_weighted_series_trace_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and not premises and type(conclusion) is Exists
    assert weighted.json_hash(encode_formula(target))==weighted.TARGET_SHA256
    assert len(weighted.canonical(encode_formula(target)))==3633
    contract = weighted.source_contract()
    assert contract["all_accumulator_rows_constructed"] is True
    assert contract["zero_initial_row_constructed"] is True
    assert contract["source_rows_are_powers_assumed"] is False
    assert contract["finite_composition_chain_rule"] is contract["closes_IR072"] is False


def test_definition_dag_exact_expansions_and_hygienic_source_row_codes():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weighted.definition_registry()
    for number,name,parameters,source,deps,digest in weighted.DEFINITION_ROWS:
        d = r[name]
        assert d.stable_id==f"ND{number:04d}" and d.conceptual_dependencies==deps
        assert weighted.json_hash(encode_formula(d.template_formula))==digest
        assert d.template_formula==parse_named(source,parameters,r)
        assert "Euler" not in source and "Convolution" not in source and "Sum(" not in source
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("H","wb","wc","ub","uc","eb","ec","tb","tc","vb","vc","K")
    aliased = parse_named("NatWeightedSeriesTrace("+",".join(names)+")",names,r)
    explicit = parse_named("(exists x y. NatPowerRow(tb,tc,vb,vc,0,x,y) /\\ NatZeroPrefix(x,y,H)) /\\ (forall j. Lt(j,K) -> NatWeightedSeriesStep(H,wb,wc,ub,uc,eb,ec,tb,tc,vb,vc,j))",names,r)
    assert aliased==explicit


def test_changed_zero_initialization_or_step_weight_is_rejected():
    rows = list(weighted.DEFINITION_ROWS)
    first = list(rows[0])
    first[3] = first[3].replace("i,0)","i,1)")
    rows[0] = tuple(first)
    with patch.object(weighted,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        weighted.definition_registry()
    rows = list(weighted.DEFINITION_ROWS)
    second = list(rows[1])
    second[3] = second[3].replace("NatLinearTriple(1,w,1,","NatLinearTriple(1,1,1,")
    rows[1] = tuple(second)
    with patch.object(weighted,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        weighted.definition_registry()


def test_actual_dependency_endpoints_and_helper_targets_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weighted.definition_registry()
    assert {name:weighted.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in weighted.HELPER_SOURCES.items()}==weighted.HELPER_TARGET_SHA256
    found = set()
    for pin in weighted.ARCHIVES:
        rows = weighted.read_archive(pin)
        for name,source in weighted.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==weighted.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in weighted.ARCHIVES}=={"CV003","CV004","CV018"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in weighted.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                weighted.read_archive(changed)


def test_actual_weighted_accumulation_model_empty_width_and_zero_weights():
    for H in range(5):
        for K in range(5):
            rows = [[(3*k+2*i)%5 for i in range(H)] for k in range(K)]
            for weights in product(range(3),repeat=K):
                trace = [[0]*H]
                for k in range(K):
                    trace.append([x+weights[k]*a for x,a in zip(trace[-1],rows[k])])
                assert len(trace)==K+1
                for k in range(K+1):
                    assert trace[k]==[sum(weights[j]*rows[j][i] for j in range(k)) for i in range(H)]
    # These direct sum comparisons are model tests, not a claimed HA sum identity.
    assert [2+0*3,0+4*5]==[2,20]


def test_guarded_trace_induction_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weighted.prove_weighted_series_trace()
    assert result.receipt.target==weighted.frozen_weighted_series_trace_target()
    assert len(result.bundle.nodes)==110
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5326
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
