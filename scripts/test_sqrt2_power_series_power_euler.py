"""Actual all-exponents power differentiation and adversarial proof controls."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_series_power_euler as power


def test_exact_target_constructs_both_euler_and_power_tables_without_premises():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = power.frozen_series_power_euler_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and not premises and type(conclusion) is Exists
    assert power.json_hash(encode_formula(target))==power.TARGET_SHA256
    assert len(power.canonical(encode_formula(target)))==9879
    contract = power.source_contract()
    assert contract["actual_euler_and_power_tables_constructed"] is True
    assert contract["all_exponents_and_coefficients_below_width"] is True
    assert contract["input_constant_coefficient_need_not_vanish"] is True
    assert contract["coefficientwise_euler_power_rule"] is True
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_exact_helper_targets_and_conservative_execution_definition_dag():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = power.definition_registry()
    assert {name:power.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in power.HELPER_SOURCES.items()}==power.HELPER_TARGET_SHA256
    assert power.source_contract()["new_definition_ids"]==[]
    assert r["NatPowerTrace"].stable_id=="ND0407"
    assert r["NatEulerPrefix"].stable_id=="ND0410"
    assert r["NatPowerTrace"].conceptual_dependencies==("NatPowerRow","NatUnitPrefix","Lt","NatPowerStep")
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("db","dc","L","ub","uc","H","i","t")
    aliased = parse_named("NatConvolutionCoefficient(db,dc,L,ub,uc,H,i,t)",names,r)
    explicit = parse_named("exists x y. PolynomialDiagonalPrefix(db,dc,L,ub,uc,H,i,x,y,S i) /\\ Sum(x,y,S i,t)",names,r)
    assert aliased==explicit


def test_missing_width_or_wrong_exponent_factor_is_rejected():
    for wrong in (power.NAMED_SOURCE.replace("Lt(i,H) -> ",""),power.NAMED_SOURCE.replace("i*p=(S k)*t","i*p=k*t")):
        assert wrong!=power.NAMED_SOURCE
        with patch.object(power,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            power.frozen_series_power_euler_target()


def test_actual_six_archive_dependency_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = power.definition_registry()
    formulas = {name:encode_formula(parse_named(source,registry=r)) for name,source in power.ENDPOINT_SOURCES.items()}
    found = set()
    for pin in power.ARCHIVES:
        rows = power.read_archive(pin)
        for name,formula in formulas.items():
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==power.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in power.ARCHIVES}=={"CV003","CV004","CV007","CV014","CV015","CV016"}


def test_forged_actual_archive_or_helper_source_is_rejected():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    for original in power.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                power.read_archive(changed)
    altered = power.HELPER_SOURCES["power_rule"].replace("i*p=(S k)*t","i*p=k*t")
    assert power.json_hash(encode_formula(parse_named(altered,registry=power.definition_registry())))!=power.HELPER_TARGET_SHA256["power_rule"]


def test_finite_all_exponent_power_rule_and_outside_width_counterexample():
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    for L in range(5):
        for a in product(range(3),repeat=L):
            ea = [j*x for j,x in enumerate(a)]
            for H in range(6):
                previous = [int(j==0) for j in range(H)]
                for k in range(6):
                    current = [coefficient(a,previous,i) for i in range(H)]
                    for i in range(H):
                        assert i*current[i]==(k+1)*coefficient(ea,previous,i)
                    previous = current
    # Truncated P1=[0] has padded value zero at i=H=1; EA*P0 has value one.
    assert coefficient([0,1],[1],1)==1
    assert 1*0!=coefficient([0,1],[1],1)


def test_guarded_power_induction_replays_ancestors_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = power.prove_series_power_euler()
    assert result.receipt.target==power.frozen_series_power_euler_target()
    assert len(result.bundle.nodes)==193
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==12931
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
