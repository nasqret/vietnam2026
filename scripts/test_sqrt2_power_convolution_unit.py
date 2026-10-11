"""Constructed natural unit, exact premises, and ordinary certificate controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_unit as unit


def test_exact_target_constructs_unit_and_actual_padded_value():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = unit.frozen_convolution_unit_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==1 and type(conclusion) is Exists
    assert unit.json_hash(encode_formula(target))==unit.TARGET_SHA256
    assert len(unit.canonical(encode_formula(target)))==3699
    contract = unit.source_contract()
    assert contract["actual_unit_and_padded_coefficient_constructed"] is True
    assert contract["coefficient_index_below_unit_width_required"] is True
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_exact_helpers_and_existing_unit_definition_contain_no_unit_law():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = unit.definition_registry()
    assert {name:unit.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in unit.HELPER_SOURCES.items()}==unit.HELPER_TARGET_SHA256
    assert unit.source_contract()["new_definition_ids"]==[]
    assert r["NatUnitCoefficient"].stable_id=="ND0403"
    assert r["NatUnitPrefix"].conceptual_dependencies==("Lt","BetaAt","NatUnitCoefficient")
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_removed_width_premise_and_wrong_coefficient_value_are_rejected():
    for wrong in (unit.NAMED_SOURCE.replace("Lt(i,H) -> ",""),unit.NAMED_SOURCE.replace("ub,uc,H,ab,ac,L,i,a","ub,uc,H,ab,ac,L,i,S a")):
        assert wrong!=unit.NAMED_SOURCE
        with patch.object(unit,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            unit.frozen_convolution_unit_target()


def test_actual_four_archive_dependency_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = unit.definition_registry()
    found = set()
    for pin in unit.ARCHIVES:
        rows = unit.read_archive(pin)
        for name,source in unit.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==unit.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in unit.ARCHIVES}=={"CV003","CV004","CV010","CV011"}


def test_forged_actual_archives_are_rejected():
    for original in unit.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                unit.read_archive(changed)


def test_finite_unit_model_and_zero_width_counterexample():
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    for length in range(5):
        for a in product(range(3),repeat=length):
            for H in range(7):
                u = [int(j==0) for j in range(H)]
                for i in range(H):
                    padded = a[i] if i<len(a) else 0
                    assert coefficient(u,a,i)==padded
    assert coefficient([],[1],0)==0  # no unit at width zero
    assert [1][0]!=coefficient([],[1],0)


def test_guarded_unit_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = unit.prove_convolution_unit()
    assert result.receipt.target==unit.frozen_convolution_unit_target()
    assert len(result.bundle.nodes)==142
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7503
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
