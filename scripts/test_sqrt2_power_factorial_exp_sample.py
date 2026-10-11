"""Prescribed coefficient scale is carried through every actual sample field."""
from dataclasses import replace
from fractions import Fraction
from math import factorial,isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_factorial_exp_sample as sample


def test_exact_unconditional_full_sample_contract_keeps_positive_scale():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target=sample.frozen_factorial_exp_sample_target();binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and len(sample.OUTPUTS)==15
    for _ in sample.OUTPUTS:
        assert type(conclusion) is Exists
        conclusion=conclusion.body
    for _ in range(7):
        assert type(conclusion) is And
        conclusion=conclusion.right
    assert len(sample.canonical(encode_formula(target)))==24572
    c=sample.source_contract()
    assert c["prescribed_coefficient_scale"]=="(2*k+1)!"
    assert c["all_AP002_actual_computation_and_normalization_fields_retained"] is c["positive_coefficient_scale_retained_in_conclusion"] is True
    assert c["all_precision_indices_including_zero"] is c["supplied_sample_definition_unchanged"] is True
    assert c["beta_code_number_canonicality_claim"] is c["canonical_PR_approximation_algorithm_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_original_twenty_three_definition_sample_dag_is_unchanged():
    from sqrt2_power_exp_sample import definition_registry
    registry=sample.definition_registry();original=definition_registry();seen=set();ids=set()
    assert dict(registry)==dict(original) and len(registry)==23
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert sample.source_contract()["new_definition_ids"]==[]


def test_target_rejects_changed_prescribed_scale_or_lost_positivity():
    source=sample.NAMED_SOURCE;registry=sample.definition_registry()
    for changed in (source.replace("Factorial(S(2*k),D)","Factorial(2*k,D)"),source.replace("~D=0","D=0"),
                    source.replace("NatSqrt2ExpSample(k,","NatSqrt2ExpSample(S k,"),source.replace("~w0=0","w0=0")):
        assert changed!=source
        with patch.object(sample,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            sample.frozen_factorial_exp_sample_target(_registry=registry)


def test_actual_prescribed_prefix_and_exponential_ancestors_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=sample.definition_registry();found=set()
    for pin in sample.ARCHIVES:
        rows=sample.read_mixed_archive(pin)
        for name,source in sample.ENDPOINT_SOURCES.items():
            if sample.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            sample.read_mixed_archive(bad)
    assert found==sample.ENDPOINT_SOURCES.keys()


def test_exact_models_match_the_original_finite_formula_at_zero_and_shift():
    for k in (0,1,2,3,4,8,9):
        d=2**k;s=isqrt(2*d*d);D=factorial(2*k+1);x=0
        for i in range(2*k+1):
            coefficient=0 if i%2==0 else 2*D//i
            if i%2:
                assert i*coefficient==2*D
            x=3*x+coefficient
        p=3**(2*k+1);U=(3*x)*d;V=(D*p)*s;N=k+2;f=factorial(N);h=V**N;head=f*h
        assert d>0 and s>0 and D>0 and p>0 and V>0 and head>0 and U<=V
        terms=[]
        for j in range(N+1):
            t,remainder=divmod(head*U**j,factorial(j)*V**j)
            assert remainder==0 and (t*factorial(j))*V**j==head*U**j
            terms.append(t)
        log=2*sum((Fraction(1,(2*j+1)*3**(2*j+1)) for j in range(k)),Fraction(0))
        argument=log/Fraction(s,d)
        expected=sum((argument**j/factorial(j) for j in range(N+1)),Fraction(0))
        assert Fraction(U,V)==argument and Fraction(sum(terms),head)==expected
        if k==0:
            assert D==1 and U==0 and sum(terms)==head


def test_complete_fixed_factorial_sample_replay_uses_no_new_induction():
    result=sample.prove_factorial_exp_sample()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_prescribed_argument_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=sample.prove_factorial_exp_sample();node=result.provenance["helper_bundle_indices"]["argument"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
