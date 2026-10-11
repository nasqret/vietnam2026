"""Scaled exponential terms retain one actual weight/term pair and denominator."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_scaled_exp_terms as terms


def test_exact_same_table_scaled_terms_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = terms.frozen_scaled_exp_terms_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==3 and len(premises)==1 and type(conclusion) is Exists
    assert terms.json_hash(encode_formula(target))==terms.TARGET_SHA256
    assert len(terms.canonical(encode_formula(target)))==15029
    c = terms.source_contract()
    assert c["actual_factorial_weights_and_power_terms_constructed"] is c["same_weight_and_term_tables_throughout"] is True
    assert c["nonzero_denominator_required"] is c["nonzero_initial_value_proved"] is True
    assert c["exact_adjacent_recurrence"] is c["all_index_factorial_normalization"] is c["zero_argument_allowed"] is True
    assert c["finite_exp_sum_bound_claimed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_conservative_recurrence_definition_and_hygiene():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = terms.definition_registry()
    identifier,name,params,source,deps,digest = terms.DEFINITIONS[0]
    d = registry[name]
    assert terms.source_contract()["new_definition_ids"]==["ND0443"]
    assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
    assert d.template_formula==parse_named(source,params,terms.base_registry())
    assert terms.json_hash(encode_formula(d.template_formula))==digest
    assert deps==("Lt","BetaAt")
    for definition in registry.values():
        assert set(definition.conceptual_dependencies)<=registry.keys()
    for altered in (("ND0442",name,params,source,deps,digest),
                    (identifier,"NatPowerWeightedPrefix",params,source,deps,digest),
                    (identifier,name,params,source.replace("=x*a","=x*b"),deps,digest)):
        with patch.object(terms,"DEFINITIONS",(altered,)),pytest.raises(ValueError):
            terms.definition_registry()


def test_removed_denominator_guard_or_changed_normalization_is_rejected():
    for source in (terms.NAMED_SOURCE.replace("~d=0 -> ",""),
                   terms.NAMED_SOURCE.replace("NatScaledExpRecurrence(d,x,tb,tc,N)","NatScaledExpRecurrence(d,x,tc,tb,N)"),
                   terms.NAMED_SOURCE.replace("(t*f0)*p0=w0*q","t*f0=w0*q"),
                   terms.NAMED_SOURCE.replace("Sum(tb,tc,S N,s)","Sum(wb,wc,S N,s)")):
        with patch.object(terms,"NAMED_SOURCE",source),pytest.raises(ValueError):
            terms.frozen_scaled_exp_terms_target()


def test_owned_actual_weight_normalization_and_term_construction_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = terms.definition_registry()
    found = set()
    for pin in terms.ARCHIVES:
        rows = terms.read_mixed_archive(pin)
        for name,source in terms.ENDPOINT_SOURCES.items():
            if terms.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==terms.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in terms.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            pin = dict(original);pin[key] = "0"*64
            with pytest.raises(ValueError):
                terms.read_mixed_archive(pin)


def test_finite_factorial_model_and_exact_denominator_interpretation():
    from fractions import Fraction
    from math import factorial
    for d in range(1,5):
        for x in range(7):
            for N in range(8):
                W = [factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
                T = [w*x**j for j,w in enumerate(W)]
                t0 = factorial(N)*d**N
                assert W[0]==T[0]==t0 and t0>0
                for j in range(N):
                    assert ((j+1)*d)*T[j+1]==x*T[j]
                for j,t in enumerate(T):
                    assert (t*factorial(j))*d**j==t0*x**j
                assert Fraction(sum(T),t0)==sum(Fraction(x,d)**j/factorial(j) for j in range(N+1))
    W,T = [0,1],[0,1]
    assert W[0]==T[0]==0 and 1*0*T[1]==1*T[0]


def test_ordinary_replay_and_forged_factorial_weight_authority_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = terms.prove_scaled_exp_terms()
    assert result.receipt.target==terms.frozen_scaled_exp_terms_target()
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(terms.ENDPOINT_SOURCES["factorial_weights_exists"],registry=terms.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
