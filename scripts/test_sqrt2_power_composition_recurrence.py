"""Actual constructed recurrence, retained computation and hostile controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_recurrence as recurrence


def test_unconditional_construction_not_a_recurrence_assumption():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = recurrence.frozen_composition_recurrence_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert recurrence.json_hash(encode_formula(target))==recurrence.TARGET_SHA256
    assert len(recurrence.canonical(encode_formula(target)))==15920
    contract = recurrence.source_contract()
    assert contract["positive_inner_denominator_and_actual_coefficients_constructed"] is True
    assert contract["actual_weights_powers_accumulation_and_terminal_row_constructed"] is True
    assert contract["actual_composition_three_term_recurrence"] is True
    assert contract["recurrence_is_input_premise"] is False
    assert contract["initial_composition_values_proved"] is False
    assert contract["factorial_quotient_interpretation"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_no_new_aliases_and_coherent_computation_dag():
    from sqrt2_power_definitions import parse_named
    r = recurrence.definition_registry()
    assert recurrence.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("d","i","a")
    assert parse_named("NatAtanhCoefficient(d,i,a)",names,r)==parse_named("(exists j. i=2*j /\\ a=0) \\/ (exists j. i=S(2*j) /\\ i*a=2*d)",names,r)
    assert "NatExpAtanhRecurrence" not in recurrence.NAMED_SOURCE


def test_changed_coefficient_rule_or_removed_positive_denominator_is_rejected():
    for source in (recurrence.NAMED_SOURCE.replace("i*a+2*b","i*a+b"),
                   recurrence.NAMED_SOURCE.replace("~d=0 /\\ ","",1)):
        with patch.object(recurrence,"NAMED_SOURCE",source),pytest.raises(ValueError):
            recurrence.frozen_composition_recurrence_target()


def test_helpers_and_all_actual_constructor_and_cancellation_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = recurrence.definition_registry()
    assert {name:recurrence.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in recurrence.HELPER_SOURCES.items()}==recurrence.HELPER_TARGET_SHA256
    found = set()
    for pin in recurrence.ARCHIVES:
        rows = recurrence.read_archive(pin)
        for name,source in recurrence.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==recurrence.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in recurrence.ARCHIVES}=={"CV002","CV024","CV025","CV026","CV027"}


def test_forged_actual_archives_are_rejected():
    for original in recurrence.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                recurrence.read_archive(changed)


def test_actual_finite_composition_model_and_nonzero_cancellation_counterexample():
    from math import lcm
    def multiply(a,b,N):
        return [sum(a[j]*b[i-j] for j in range(i+1) if j<len(a) and i-j<len(b)) for i in range(N)]
    for N in range(8):
        d = lcm(*range(1,N+1))
        a = [0 if i%2==0 else 2*(d//i) for i in range(N)]
        weights = [1]*(N+1)
        for i in range(N-1,-1,-1):
            weights[i] = ((i+1)*d)*weights[i+1]
        power,c = ([1]+[0]*(N-1) if N else []),[0]*N
        for k in range(N+1):
            c = [x+weights[k]*y for x,y in zip(c,power)]
            power = multiply(a,power,N)
        for i in range(max(0,N-2)):
            assert (i+2)*c[i+2]==i*c[i]+2*c[i+1]
    # d=0 makes the Euler equation vacuous for E=0; it cannot justify cancellation.
    c = [0,0,1]
    assert [0*(i*v) for i,v in enumerate(c)]==multiply([0,0,0],c,3)
    assert 2*c[2]!=0*c[0]+2*c[1]


def test_guarded_constructed_recurrence_replays_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = recurrence.prove_composition_recurrence()
    assert result.receipt.target==recurrence.frozen_composition_recurrence_target()
    assert len(result.bundle.nodes)==245
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==18901
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
