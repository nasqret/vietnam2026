"""Unconditional weighted prefix construction with ordinary proof controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_series_linear_combination as linear


def test_exact_target_constructs_relation_instead_of_assuming_it():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = linear.frozen_series_linear_combination_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert linear.json_hash(encode_formula(target))==linear.TARGET_SHA256
    assert len(linear.canonical(encode_formula(target)))==9171
    contract = linear.source_contract()
    assert contract["actual_pointwise_relation_constructed"] is True
    assert contract["weighted_prefix_constructed"] is True
    assert contract["all_three_convolution_coefficients_constructed"] is True
    assert contract["finite_composition_chain_rule"] is contract["closes_IR072"] is False


def test_exact_constructor_helper_and_existing_pointwise_definition_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = linear.definition_registry()
    assert {name:linear.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in linear.HELPER_SOURCES.items()}==linear.HELPER_TARGET_SHA256
    assert linear.source_contract()["new_definition_ids"]==[]
    assert r["NatLinearTriple"].stable_id=="ND0409"
    assert r["NatLinearTriple"].conceptual_dependencies==("Lt","BetaAt")
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_wrong_computed_prefix_or_convolution_identity_is_rejected():
    for wrong in (linear.NAMED_SOURCE.replace("NatLinearTriple(alpha,beta,1,","NatLinearTriple(alpha,beta,0,"),linear.NAMED_SOURCE.replace("w=alpha*u+beta*v","w=alpha*u*beta*v")):
        assert wrong!=linear.NAMED_SOURCE
        with patch.object(linear,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            linear.frozen_series_linear_combination_target()


def test_actual_convolution_and_linearity_dependency_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = linear.definition_registry()
    found = set()
    for pin in linear.ARCHIVES:
        rows = linear.read_archive(pin)
        for name,source in linear.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==linear.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in linear.ARCHIVES}=={"CV003","CV015"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in linear.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                linear.read_archive(changed)


def test_constructed_linear_prefix_and_all_index_convolution_model():
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    seqs = [list(row) for n in range(3) for row in product(range(3),repeat=n)]
    for alpha,beta in product(range(4),repeat=2):
        for a,b in product(seqs,repeat=2):
            if len(a)!=len(b):
                continue
            c = [alpha*x+beta*y for x,y in zip(a,b)]
            for d in seqs:
                for i in range(6):
                    assert coefficient(c,d,i)==alpha*coefficient(a,d,i)+beta*coefficient(b,d,i)


def test_guarded_prefix_induction_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = linear.prove_series_linear_combination()
    assert result.receipt.target==linear.frozen_series_linear_combination_target()
    assert len(result.bundle.nodes)==125
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6687
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
