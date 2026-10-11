"""Weighted actual-sum execution and the separate pointwise hypothesis."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_sum_linearity as linearity


def test_exact_statement_constructs_three_sums_from_pointwise_data():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = linearity.frozen_sum_linearity_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==10 and len(premises)==1 and type(conclusion) is Exists
    assert linearity.json_hash(encode_formula(target))==linearity.TARGET_SHA256
    assert len(linearity.canonical(encode_formula(target)))==5187
    contract = linearity.source_contract()
    assert contract["all_three_actual_sums_constructed"] is True
    assert contract["sum_values_supplied"] is contract["positive_weights_required"] is False
    assert contract["empty_sum_allowed"] is True
    assert contract["formal_product_derivative"] is contract["closes_IR072"] is False


def test_pointwise_definition_does_not_include_sum_identity():
    registry = linearity.definition_registry()
    definition = registry["NatLinearTriple"]
    assert definition.stable_id=="ND0409" and definition.arity==10
    assert definition.conceptual_dependencies==("Lt","BetaAt")
    assert "Sum(" not in linearity.DEFINITION_SOURCE
    assert "forall i a b c" in linearity.DEFINITION_SOURCE
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_changed_weights_or_missing_pointwise_premise_are_rejected():
    with patch.object(linearity,"NAMED_SOURCE",linearity.NAMED_SOURCE.replace(linearity.POINTWISE+" -> ","")),pytest.raises(ValueError):
        linearity.frozen_sum_linearity_target()
    with patch.object(linearity,"DEFINITION_SOURCE",linearity.DEFINITION_SOURCE.replace("gamma*c","alpha*c")),pytest.raises(ValueError):
        linearity.definition_registry()


def test_actual_sum_ancestor_cone_binds_existence_and_successor_traces():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    ids,rows = linearity.inert_sum_rows()
    assert len(ids)==107 and len(linearity.canonical(rows))==165095
    assert linearity.json_hash(rows)==linearity.ANCESTOR_ROWS_SHA256
    table,registry = dict(zip(ids,rows)),linearity.definition_registry()
    for old,source in linearity.ENDPOINT_SOURCES.values():
        assert table[old][1]==encode_formula(parse_named(source,registry=registry))


def test_changed_archive_or_sum_decomposition_fails_closed():
    with patch.object(linearity,"ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        linearity.inert_sum_rows()
    sources = dict(linearity.ENDPOINT_SOURCES)
    old,source = sources["sum_decompose"]
    sources["sum_decompose"] = (old,source.replace("n=r+a","n=r*a"))
    with patch.object(linearity,"ENDPOINT_SOURCES",sources),pytest.raises(ValueError):
        linearity.inert_sum_rows()


def test_finite_model_all_zero_weights_and_empty_sums():
    for alpha,beta,gamma in product(range(3),repeat=3):
        admissible = [(a,b,c) for a,b,c in product(range(4),repeat=3) if gamma*c==alpha*a+beta*b]
        assert admissible
        for length in range(6):
            for offset in range(len(admissible)):
                rows = [admissible[(offset+i)%len(admissible)] for i in range(length)]
                u,v,w = (sum(row[k] for row in rows) for k in range(3))
                assert gamma*w==alpha*u+beta*v
    # Arbitrary actual sums do not suffice without the pointwise equation.
    assert sum([999])!=sum([1])+sum([2])


def test_guarded_weighted_induction_and_three_witnesses_reject_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = linearity.prove_sum_linearity()
    assert result.receipt.target==linearity.frozen_sum_linearity_target()
    assert len(result.bundle.nodes)==109 and result.receipt.total_body_nodes==5286
    assert result.provenance["all_lengths_weighted_linearity"] is True
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["deterministic_additive_reassociation"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
