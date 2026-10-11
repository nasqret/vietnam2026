"""Actual initial values, all coefficient values and hostile certificate checks."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_coefficients as coefficients


def test_constructed_all_coefficient_formula_with_only_width_premise():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = coefficients.frozen_composition_coefficients_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and len(premises)==1 and type(conclusion) is Exists
    assert coefficients.json_hash(encode_formula(target))==coefficients.TARGET_SHA256
    assert len(coefficients.canonical(encode_formula(target)))==18359
    contract = coefficients.source_contract()
    assert contract["width_at_least_two_required"] is True
    assert contract["whole_actual_computation_constructed"] is True
    assert contract["initial_weight_constructed_and_nonzero"] is True
    assert contract["initial_values_proved"] is True
    assert contract["all_in_range_coefficients_identified"] is True
    assert contract["recurrence_and_initial_values_are_outputs"] is True
    assert contract["factorial_quotient_interpretation"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_reused_recurrence_alias_is_hygienic_and_dag_is_coherent():
    from sqrt2_power_definitions import parse_named
    r = coefficients.definition_registry()
    assert coefficients.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    assert r["NatExpAtanhRecurrence"].stable_id=="ND0400"
    names = ("i","a","N","k")
    alias = parse_named("NatExpAtanhRecurrence(i,a,N,k)",names,r)
    explicit = parse_named("BetaAt(i,a,0,k) /\\ (BetaAt(i,a,1,2*k) /\\ (forall j x y z. Lt(S(S j),N) -> BetaAt(i,a,j,x) -> BetaAt(i,a,S j,y) -> BetaAt(i,a,S(S j),z) -> (S(S j))*z=j*x+2*y))",names,r)
    assert alias==explicit


def test_changed_coefficient_or_removed_width_is_rejected():
    for source in (coefficients.NAMED_SOURCE.replace("a=2*z","a=3*z"),
                   coefficients.NAMED_SOURCE.replace("Lt(1,N) -> ","",1)):
        with patch.object(coefficients,"NAMED_SOURCE",source),pytest.raises(ValueError):
            coefficients.frozen_composition_coefficients_target()


def test_helpers_and_actual_constructor_vanishing_and_recurrence_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = coefficients.definition_registry()
    assert {name:coefficients.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in coefficients.HELPER_SOURCES.items()}==coefficients.HELPER_TARGET_SHA256
    found = set()
    for pin in coefficients.ARCHIVES:
        rows = coefficients.read_archive(pin)
        for name,source in coefficients.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==coefficients.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in coefficients.ARCHIVES}=={"CV002","CV028"}


def test_forged_actual_archives_are_rejected():
    for original in coefficients.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[field] = "0"*64
            with pytest.raises(ValueError):
                coefficients.read_archive(changed)


def test_actual_initial_values_and_all_coefficients_model():
    from math import lcm
    def multiply(a,b,N):
        return [sum(a[j]*b[i-j] for j in range(i+1) if j<len(a) and i-j<len(b)) for i in range(N)]
    def compose(a,d,N):
        weights = [1]*(N+1)
        for i in range(N-1,-1,-1):
            weights[i] = ((i+1)*d)*weights[i+1]
        power,c = [1]+[0]*(N-1),[0]*N
        for k in range(N+1):
            c = [x+weights[k]*y for x,y in zip(c,power)]
            power = multiply(a,power,N)
        return weights,c
    for N in range(2,9):
        d = lcm(*range(1,N+1))
        a = [0 if i%2==0 else 2*(d//i) for i in range(N)]
        weights,c = compose(a,d,N)
        z = weights[0]
        assert z>0 and c==[z]+[2*z]*(N-1)
    weights,c = compose([1,1],1,2)
    assert c[0]==5 and weights[0]==2  # zero constant input is needed by fold_constant


def test_guarded_initial_and_all_coefficient_proof_replays_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = coefficients.prove_composition_coefficients()
    assert result.receipt.target==coefficients.frozen_composition_coefficients_target()
    assert len(result.bundle.nodes)==252
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==20299
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
