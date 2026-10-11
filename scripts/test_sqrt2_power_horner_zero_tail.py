"""Actual zero padding, exact power scaling and hostile target checks."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_horner_zero_tail as padding


def test_exact_constructed_zero_padding_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,Forall
    from peano_lab.library.proof_bundle import encode_formula
    target = padding.frozen_horner_zero_tail_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==1 and type(premises[0]) is Forall and type(conclusion) is Exists
    assert padding.json_hash(encode_formula(target))==padding.TARGET_SHA256
    assert len(padding.canonical(encode_formula(target)))==3856
    c = padding.source_contract()
    assert c["actual_zero_tail_required"] is c["actual_trace_and_endpoints_constructed"] is True
    assert c["actual_power_constructed"] is c["exact_padding_scale_proved"] is True
    assert c["zero_multiplier_and_empty_lengths_allowed"] is True
    assert c["multiplication_evaluation_identity"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_reused_trace_definition_and_dag_are_exact():
    from sqrt2_power_definitions import parse_named
    r = padding.definition_registry()
    assert padding.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()
    names = ("a","b","k","h","j","N")
    assert parse_named("NatScaledHornerTrace(a,b,k,N,h,j)",names,r)==parse_named(
        "BetaAt(h,j,0,0) /\\ (forall i. Lt(i,N) -> NatScaledHornerStep(a,b,k,h,j,i))",names,r)


def test_missing_tail_or_wrong_scaling_is_rejected():
    for source in (padding.NAMED_SOURCE.replace("v=p*u","v=u"),
                   padding.NAMED_SOURCE.replace("Pow(t,N,p)","Pow(t,M,p)"),
                   padding.NAMED_SOURCE.replace("("+padding.ZERO_TAIL+") -> ","",1)):
        with patch.object(padding,"NAMED_SOURCE",source),pytest.raises(ValueError):
            padding.frozen_horner_zero_tail_target()


def test_helpers_and_owned_actual_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = padding.definition_registry()
    assert {name:padding.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in padding.HELPER_SOURCES.items()}==padding.HELPER_TARGET_SHA256
    found = set()
    for pin in padding.ARCHIVES:
        rows = padding.read_mixed_archive(pin)
        for name,source in padding.ENDPOINT_SOURCES.items():
            if padding.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==padding.ENDPOINT_SOURCES.keys()


def test_modified_archival_proof_data_is_rejected():
    for original in padding.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                padding.read_mixed_archive(changed)


def test_zero_padding_model_and_necessary_zero_tail():
    from fractions import Fraction
    for a in ([],[0],[1],[2,3,0,4]):
        for t in range(5):
            u = 0
            for x in a:
                u = t*u+x
            for N in range(8):
                v = u
                for _ in range(N):
                    v = t*v
                assert v==t**N*u
                if t and a:
                    assert Fraction(v,t**(len(a)+N-1))==Fraction(u,t**(len(a)-1))
    assert 3*2+1!=3*2  # A nonzero appended coefficient cannot be discarded.


def test_guarded_padding_certificate_replays_and_rejects_false_proof():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = padding.prove_horner_zero_tail()
    assert result.receipt.target==padding.frozen_horner_zero_tail_target()
    assert len(result.bundle.nodes)==122
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6061
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
