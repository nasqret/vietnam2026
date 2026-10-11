"""Finite denominator transport, necessary support and actual proof controls."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_denominator_euler as euler


def test_exact_constructed_composition_with_zero_input_and_no_analytic_claim():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = euler.frozen_denominator_euler_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==1 and type(conclusion) is Exists
    assert euler.json_hash(encode_formula(target))==euler.TARGET_SHA256
    assert len(euler.canonical(encode_formula(target)))==18996
    contract = euler.source_contract()
    assert contract["input_vanishes_below_one_required"] is True
    assert contract["actual_weights_and_composition_constructed"] is True
    assert contract["denominator_cleared_euler_equation"] is True
    assert contract["zero_d_allowed"] is True
    assert contract["factorial_quotient_interpretation"] is contract["analytic_limit_claim"] is contract["closes_IR072"] is False


def test_no_new_definitions_and_hygienic_computation_registry():
    from sqrt2_power_definitions import parse_named
    r = euler.definition_registry()
    assert euler.source_contract()["new_definition_ids"]==[]
    for definition in r.values():
        assert set(definition.conceptual_dependencies)<=r.keys()
    names = ("d","N","a","b")
    alias = parse_named("NatExpWeightTable(d,N,a,b)",names,r)
    explicit = parse_named("BetaAt(a,b,N,1) /\\ (forall k x y. Lt(k,N) -> BetaAt(a,b,k,x) -> BetaAt(a,b,S k,y) -> x=((S k)*d)*y)",names,r)
    assert alias==explicit
    assert {r[n].stable_id for n in ("NatZeroBefore","NatWeightedSeriesTrace","NatExpWeightTable")}=={"ND0408","ND0421","ND0423"}


def test_removed_zero_input_or_changed_equation_is_rejected():
    for source in (euler.NAMED_SOURCE.replace(euler.INPUT_ZERO+" -> ","",1),
                   euler.NAMED_SOURCE.replace("d*(i*p)=v","i*p=v")):
        with patch.object(euler,"NAMED_SOURCE",source),pytest.raises(ValueError):
            euler.frozen_denominator_euler_target()


def test_helpers_and_actual_dependencies_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = euler.definition_registry()
    assert {name:euler.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in euler.HELPER_SOURCES.items()}==euler.HELPER_TARGET_SHA256
    found = set()
    for pin in euler.ARCHIVES:
        rows = euler.read_archive(pin)
        for name,source in euler.ENDPOINT_SOURCES.items():
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==euler.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in euler.ARCHIVES}=={"CV005","CV021","CV022","CV023"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in euler.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                euler.read_archive(changed)


def test_finite_composition_model_and_nonzero_constant_counterexample():
    def convolution(a,b,H):
        return [sum(a[j]*b[i-j] for j in range(i+1) if j<len(a) and i-j<len(b)) for i in range(H)]
    def composition(a,d,N):
        weights = [1]*(N+1)
        for j in range(N-1,-1,-1):
            weights[j] = ((j+1)*d)*weights[j+1]
        result,power = [0]*N,([1]+[0]*(N-1) if N else [])
        for j in range(N+1):
            result = [x+weights[j]*y for x,y in zip(result,power)]
            power = convolution(a,power,N)
        return result
    for N in range(8):
        for d in range(4):
            for L in range(6):
                a = [0 if j==0 else (j*j+3)%7 for j in range(L)]
                c = composition(a,d,N)
                ea = [j*v for j,v in enumerate(a)]
                assert [d*(i*v) for i,v in enumerate(c)]==convolution(ea,c,N)
    a,d,N = [1,1],1,2
    c = composition(a,d,N)
    assert c==[5,4]
    assert d*c[1]!=convolution([0,1],c,N)[1]


def test_guarded_transport_replays_actual_bodies_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = euler.prove_denominator_euler()
    assert result.receipt.target==euler.frozen_denominator_euler_target()
    assert len(result.bundle.nodes)==224
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==16942
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
