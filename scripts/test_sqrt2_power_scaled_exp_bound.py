"""Finite exponential bound preserves all computations and guarded cancellation."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_scaled_exp_bound as bound


def test_exact_bound_preserves_every_constructed_exp_term_clause():
    from sqrt2_power_native import strip_target
    from sqrt2_power_scaled_exp_terms import frozen_scaled_exp_terms_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = bound.frozen_scaled_exp_bound_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==3 and len(premises)==2 and type(conclusion) is Exists
    assert bound.json_hash(encode_formula(target))==bound.TARGET_SHA256
    assert len(bound.canonical(encode_formula(target)))==15290
    previous = strip_target(frozen_scaled_exp_terms_target())[2]
    for _ in bound.OUTPUTS:
        assert type(conclusion) is type(previous) is Exists
        conclusion,previous = conclusion.body,previous.body
    def fields(f,n):
        result = []
        for _ in range(n-1):
            assert type(f) is And
            result.append(f.left);f = f.right
        return result+[f]
    assert fields(conclusion,12)[:11]==fields(previous,11)
    c = bound.source_contract()
    assert c["all_CV070_computation_and_normalization_data_retained"] is True
    assert c["nonzero_denominator_required"] is c["zero_argument_and_zero_horizon_allowed"] is True
    assert c["finite_sum_bound"]=="s<=9*w0"
    assert c["rational_division_transport_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_no_definition_hides_the_analytic_or_sum_bound():
    from sqrt2_power_scaled_exp_terms import definition_registry
    registry = bound.definition_registry()
    assert bound.source_contract()["new_definition_ids"]==[]
    for name,d in definition_registry().items():
        assert registry[name].stable_id==d.stable_id and registry[name].template_formula==d.template_formula
        assert set(d.conceptual_dependencies)<=registry.keys()
    assert tuple(registry["NatScaledExpRecurrence"].conceptual_dependencies)==("Lt","BetaAt")
    with pytest.raises(ValueError):
        bound._n(10)
    with pytest.raises(ValueError):
        bound._n(-1)


def test_removed_guards_or_changed_scale_are_rejected():
    for source in (bound.NAMED_SOURCE.replace("~d=0 -> ",""),
                   bound.NAMED_SOURCE.replace("Le(x,2*d) -> ",""),
                   bound.NAMED_SOURCE.replace("Le(s,9*w0)","Le(s,9)"),
                   bound.NAMED_SOURCE.replace("Le(s,9*w0)","Le(s,8*w0)")):
        with patch.object(bound,"NAMED_SOURCE",source),pytest.raises(ValueError):
            bound.frozen_scaled_exp_bound_target()


def test_actual_owned_cancellation_and_sum_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = bound.definition_registry();found = set()
    for pin in bound.ARCHIVES:
        rows = bound.read_mixed_archive(pin)
        for name,source in bound.ENDPOINT_SOURCES.items():
            if bound.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==bound.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in bound.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                bound.read_mixed_archive(pin)


def test_exact_finite_bound_surplus_and_essential_guards():
    from math import factorial
    from fractions import Fraction
    for d in range(1,5):
        for x in range(2*d+1):
            for N in range(11):
                t0 = factorial(N)*d**N
                T = [factorial(N)//factorial(j)*d**(N-j)*x**j for j in range(N+1)]
                assert sum(T)<=9*t0
                assert Fraction(sum(T),t0)==sum(Fraction(x,d)**j/factorial(j) for j in range(N+1))
                for j in range(2,N+1):
                    assert sum(T[:j+1])+2*T[j]<=9*t0
                for j in range(2,N):
                    assert 3*T[j+1]<=2*T[j]
    assert 0*2<=0*1 and not 2<=1
    zero_denominator_terms = [1,0,0,10]
    assert all((j+1)*0*zero_denominator_terms[j+1]==0*zero_denominator_terms[j] for j in range(3))
    assert sum(zero_denominator_terms)>9*zero_denominator_terms[0]
    assert sum([1,10])>9
    assert not 3*2<=2*2  # the ratio cannot start at index one


def test_ordinary_replay_and_forged_guarded_cancellation_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = bound.prove_scaled_exp_bound()
    assert result.receipt.target==bound.frozen_scaled_exp_bound_target()
    assert result.provenance["new_induction_count"]==1 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(bound.HELPER_SOURCES["mul_le_cancel"],registry=bound.definition_registry())
    helpers = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(helpers)==1
    for node_id in (result.bundle.root,helpers[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
