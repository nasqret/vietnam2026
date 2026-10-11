"""Finite construction, conservative coefficient graphs and hostile controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_atanh_coefficients as atanh


def test_exact_unconditional_finite_construction_not_logarithm():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = atanh.frozen_atanh_coefficients_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert atanh.json_hash(encode_formula(target))==atanh.TARGET_SHA256
    assert len(atanh.canonical(encode_formula(target)))==1233
    contract = atanh.source_contract()
    assert contract["actual_finite_coefficient_table_constructed"] is True
    assert contract["positive_common_denominator_constructed"] is True
    assert contract["zero_order_one_proved"] is True
    assert contract["logarithm_identity"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_exact_conservative_definition_dag_and_hygiene():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = atanh.definition_registry()
    for identifier,name,parameters,source,dependencies,digest in atanh.DEFINITION_ROWS:
        definition = r[name]
        assert definition.stable_id==identifier and definition.conceptual_dependencies==dependencies
        assert atanh.json_hash(encode_formula(definition.template_formula))==digest
        assert set(dependencies)<=r.keys()
    names = ("d","i","j")
    alias = parse_named("NatAtanhCoefficient(d,i,j)",names,r)
    explicit = parse_named("(exists k. i=2*k /\\ j=0) \\/ (exists k. i=S(2*k) /\\ i*j=2*d)",names,r)
    assert alias==explicit
    assert "log" not in atanh.DEFINITION_ROWS[0][3] and "exp" not in atanh.DEFINITION_ROWS[0][3]


def test_changed_coefficient_or_removed_positive_denominator_is_rejected():
    rows = list(atanh.DEFINITION_ROWS)
    row = list(rows[0]);row[3] = row[3].replace("i*a=2*d","i*a=d");rows[0] = tuple(row)
    with patch.object(atanh,"DEFINITION_ROWS",tuple(rows)),pytest.raises(ValueError):
        atanh.definition_registry()
    with patch.object(atanh,"NAMED_SOURCE",atanh.NAMED_SOURCE.replace("~d=0 /\\ ","")),pytest.raises(ValueError):
        atanh.frozen_atanh_coefficients_target()


def test_helpers_and_actual_common_multiple_division_extension_bodies_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = atanh.definition_registry()
    assert {name:atanh.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in atanh.HELPER_SOURCES.items()}==atanh.HELPER_TARGET_SHA256
    found = set()
    for pin in atanh.ARCHIVES:
        rows = atanh.read_archive(pin)
        for name,source in atanh.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==atanh.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in atanh.ARCHIVES}=={"CV003"}


def test_forged_actual_archives_are_rejected():
    for original in atanh.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                atanh.read_archive(changed)


def test_finite_common_denominator_model_and_divisibility_counterexample():
    from math import lcm
    from fractions import Fraction
    for N in range(20):
        d = lcm(*range(1,N+1))
        assert d>0
        table = [0 if i%2==0 else 2*(d//i) for i in range(N)]
        for i,a in enumerate(table):
            if i%2:
                assert i*a==2*d and Fraction(a,d)==Fraction(2,i)
            else:
                assert a==0
        assert not table or table[0]==0
    assert 2%3!=0  # d=1 cannot represent the odd coefficient at index 3


def test_guarded_coefficient_induction_replays_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = atanh.prove_atanh_coefficients()
    assert result.receipt.target==atanh.frozen_atanh_coefficients_target()
    assert len(result.bundle.nodes)==108
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5026
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
