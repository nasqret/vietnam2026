"""Finite Horner computation, hygienic definitions and hostile exact targets."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_trace as horner


def test_exact_unconditional_horner_trace_and_value_uniqueness_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = horner.frozen_horner_trace_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and not premises and type(conclusion) is Exists
    assert horner.json_hash(encode_formula(target))==horner.TARGET_SHA256
    assert len(horner.canonical(encode_formula(target)))==2868
    c = horner.source_contract()
    assert c["actual_horner_trace_constructed"] is c["all_in_range_values_unique"] is True
    assert c["empty_prefix_and_zero_multiplier_allowed"] is True
    assert c["code_number_uniqueness"] is c["rational_evaluation_identity"] is c["closes_IR072"] is False


def test_horner_definition_dag_is_conservative_and_hygienic():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = horner.definition_registry()
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    for identifier,name,params,source,deps,digest in horner.DEFINITIONS:
        d = r[name]
        assert d.stable_id==identifier and tuple(d.conceptual_dependencies)==deps
        assert horner.json_hash(encode_formula(d.template_formula))==digest
        assert d.template_formula==parse_named(source,params,r)
    names = ("h","a","k","N","t","b")
    assert parse_named("NatScaledHornerStep(h,a,k,N,t,b)",names,r)==parse_named(
        "exists v w. BetaAt(N,t,b,v) /\\ (BetaAt(h,a,b,w) /\\ BetaAt(N,t,S b,k*v+w))",names,r)


def test_changed_computation_or_target_is_rejected():
    with patch.object(horner,"NAMED_SOURCE",horner.NAMED_SOURCE.replace("h=u","h=S u")),pytest.raises(ValueError):
        horner.frozen_horner_trace_target()
    changed = list(horner.DEFINITIONS)
    identifier,name,params,source,deps,digest = changed[0]
    changed[0] = (identifier,name,params,source.replace("t*h+a","t+h+a"),deps,digest)
    with patch.object(horner,"DEFINITIONS",tuple(changed)),pytest.raises(ValueError):
        horner.definition_registry()


def test_helpers_and_actual_finite_coding_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = horner.definition_registry()
    assert {name:horner.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in horner.HELPER_SOURCES.items()}==horner.HELPER_TARGET_SHA256
    rows = horner.read_archive(horner.ARCHIVES[0])
    for name,source in horner.ENDPOINT_SOURCES.items():
        matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
        assert len(matches)==1 and matches[0][3],name


def test_forged_actual_ancestor_archive_is_rejected():
    for key in ("sha256","bundle_sha256","target_ast_sha256"):
        pin = dict(horner.ARCHIVES[0]);pin[key] = "0"*64
        with pytest.raises(ValueError):
            horner.read_archive(pin)


def test_horner_model_and_denominator_orientation():
    from fractions import Fraction
    for a in ([],[0],[2],[1,2,2,2],[3,0,4,1]):
        for t in range(5):
            h = [0]
            for value in a:
                h.append(t*h[-1]+value)
            for k in range(len(a)+1):
                assert h[k]==sum(a[j]*t**(k-1-j) for j in range(k))
            if a and t:
                assert Fraction(h[-1],t**(len(a)-1))==sum(Fraction(a[j],t**j) for j in range(len(a)))
            if a and not t:
                assert h[-1]==a[-1]


def test_guarded_trace_certificate_replays_and_rejects_forged_body():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = horner.prove_horner_trace()
    assert result.receipt.target==horner.frozen_horner_trace_target()
    assert len(result.bundle.nodes)==107
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5084
    assert result.provenance["new_induction_count"]==2
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
