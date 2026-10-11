"""Actual same-table evaluation with a proved coefficient pattern."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_evaluation as evaluation


def test_unconditional_constructed_composition_evaluation_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = evaluation.frozen_composition_evaluation_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert evaluation.json_hash(encode_formula(target))==evaluation.TARGET_SHA256
    assert len(evaluation.canonical(encode_formula(target)))==29189
    c = evaluation.source_contract()
    for key in ("whole_actual_composition_constructed","same_coefficients_used_for_horner",
                "factorial_normalization_preserved","coefficient_pattern_is_proved_output",
                "actual_horner_and_nonzero_power_constructed","exact_integer_remainder_identity",
                "normalized_denominator_nonzero"):
        assert c[key] is True
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_preserves_exact_normalization_data_and_definition_dag():
    from sqrt2_power_definitions import parse_named
    r = evaluation.definition_registry()
    source = "forall N. Lt(1,N) -> exists "+" ".join(evaluation.NORMALIZED_OUTPUTS)+". "+evaluation.NORMALIZED_DATA
    assert parse_named(source,registry=r)==parse_named(evaluation.NORMALIZED_SOURCE,registry=r)
    assert evaluation.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_changed_table_width_or_gap_is_rejected():
    for source in (evaluation.NAMED_SOURCE.replace("NatScaledHornerTrace(cb,cc,3,N,hb,hc)","NatScaledHornerTrace(ab,ac,3,N,hb,hc)"),
                   evaluation.NAMED_SOURCE.replace("N=S(S K)","N=S K"),
                   evaluation.NAMED_SOURCE.replace("r+z=(2*z)*p","r=(2*z)*p")):
        with patch.object(evaluation,"NAMED_SOURCE",source),pytest.raises(ValueError):
            evaluation.frozen_composition_evaluation_target()


def test_actual_owned_constructor_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = evaluation.definition_registry()
    found = set()
    for pin in evaluation.ARCHIVES:
        rows = evaluation.read_mixed_archive(pin)
        for name,source in evaluation.ENDPOINT_SOURCES.items():
            if evaluation.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==evaluation.ENDPOINT_SOURCES.keys()


def test_modified_actual_archives_are_rejected():
    for original in evaluation.ARCHIVES:
        for key in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                evaluation.read_mixed_archive(changed)


def test_constructed_composition_and_same_table_horner_model():
    from fractions import Fraction
    from math import factorial,lcm
    for K in range(6):
        N = K+2
        d = lcm(*range(1,N+1))
        a = [0 if j%2==0 else 2*(d//j) for j in range(N)]
        z = factorial(N)*d**N
        power,c = [1]+[0]*(N-1),[0]*N
        for j in range(N+1):
            w = z//(factorial(j)*d**j)
            c = [x+w*y for x,y in zip(c,power)]
            power = [sum(a[j]*power[i-j] for j in range(i+1)) for i in range(N)]
        h = 0
        for x in c:
            h = 3*h+x
        p = 3**(K+1)
        assert z*p>0 and h+z==2*z*p
        assert Fraction(h,z*p)==2-Fraction(1,p)


def test_guarded_constructed_evaluation_certificate_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = evaluation.prove_composition_evaluation()
    assert result.receipt.target==evaluation.frozen_composition_evaluation_target()
    assert len(result.bundle.nodes)==284
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==22574
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
