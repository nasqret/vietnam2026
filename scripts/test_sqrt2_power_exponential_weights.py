"""Constructed weights, exact nonzero premise, hygiene and hostile controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_exponential_weights as weights


def test_exact_unconditional_construction_and_conditional_nonvanishing():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weights.frozen_exponential_weights_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==2 and not premises and type(conclusion) is Exists
    assert weights.json_hash(encode_formula(target))==weights.TARGET_SHA256
    assert len(weights.canonical(encode_formula(target)))==1349
    contract = weights.source_contract()
    assert contract["actual_weight_table_constructed"] is True
    assert contract["zero_denominator_allowed_for_construction"] is True
    assert contract["nonzero_denominator_required_only_for_entry_nonvanishing"] is True
    assert contract["factorial_quotient_interpretation"] is contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_exact_computation_definition_and_hygienic_weight_code_names():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    d = r["NatExpWeightTable"]
    assert d.stable_id=="ND0423" and d.conceptual_dependencies==("Lt","BetaAt")
    assert weights.json_hash(encode_formula(d.template_formula))==weights.DEFINITION_SHA256
    assert "~" not in weights.DEFINITION_SOURCE and "Factorial" not in weights.DEFINITION_SOURCE
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("d","N","a","b")
    alias = parse_named("NatExpWeightTable(d,N,a,b)",names,r)
    explicit = parse_named("BetaAt(a,b,N,1) /\\ (forall k x y. Lt(k,N) -> BetaAt(a,b,k,x) -> BetaAt(a,b,S k,y) -> x=((S k)*d)*y)",names,r)
    assert alias==explicit


def test_changed_terminal_or_removed_nonzero_premise_is_rejected():
    with patch.object(weights,"DEFINITION_SOURCE",weights.DEFINITION_SOURCE.replace("wc,N,1)","wc,N,0)")),pytest.raises(ValueError):
        weights.definition_registry()
    with patch.object(weights,"NAMED_SOURCE",weights.NAMED_SOURCE.replace("~d=0 -> ","")),pytest.raises(ValueError):
        weights.frozen_exponential_weights_target()


def test_actual_constructor_and_arithmetic_endpoints_and_helpers_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    assert {name:weights.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in weights.HELPER_SOURCES.items()}==weights.HELPER_TARGET_SHA256
    found = set()
    for pin in weights.ARCHIVES:
        rows = weights.read_archive(pin)
        for name,source in weights.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==weights.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in weights.ARCHIVES}=={"CV003","CV018"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in weights.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                weights.read_archive(changed)


def test_constructive_scaling_model_and_zero_denominator_counterexample():
    for d in range(7):
        table = [1]
        for N in range(9):
            assert len(table)==N+1 and table[N]==1
            for j in range(N):
                assert table[j]==((j+1)*d)*table[j+1]
            if d:
                assert all(value>0 for value in table)
            elif N:
                assert table[:-1]==[0]*N
            descending = [1]*(N+1)
            for j in range(N-1,-1,-1):
                descending[j]=((j+1)*d)*descending[j+1]
            assert descending==table
            table = [((N+1)*d)*value for value in table]+[1]
    assert [0*1,1]==[0,1]  # unconditional nonvanishing would be false


def test_guarded_weight_induction_replays_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weights.prove_exponential_weights()
    assert result.receipt.target==weights.frozen_exponential_weights_target()
    assert len(result.bundle.nodes)==108
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5284
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
