"""Finite exponential output retains actual factorial/power computations."""
from dataclasses import replace
from fractions import Fraction
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample as sample


def test_exact_unconditional_actual_sample_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=sample.frozen_exp_sample_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(sample.canonical(encode_formula(target)))==22595
    c=sample.source_contract()
    assert c["output_rational"]=="y/w0" and c["exponential_degree"]=="k+2"
    assert c["output_denominator_nonzero_proved"] is c["all_index_factorial_normalization_proved"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_identity_claim"] is c["closes_IR072"] is False


def test_computation_only_conservative_sample_definition_and_complete_dag():
    from sqrt2_power_definitions import parse_named
    registry=sample.definition_registry();seen=set();ids=set()
    assert len(registry)==23
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    spec=registry[sample.DEFINITION_NAME]
    assert spec.stable_id=="ND0448" and spec.conceptual_dependencies==sample.DEFINITION_DEPENDENCIES
    assert spec.template_formula==parse_named(sample.DEFINITION_SOURCE,sample.DEFINITION_PARAMETERS,registry)
    assert all(fragment not in sample.DEFINITION_SOURCE for fragment in ("~","Le(","Recurrence","CApprox","Accuracy"))
    assert all(fragment in sample.DEFINITION_SOURCE for fragment in ("Factorial(","Pow(","Sum(","w0=f*h"))


def test_changed_degree_quotient_output_or_normalization_is_rejected():
    for old,new in (("~w0=0","w0=0"),("(k+2)","(k+1)"),("w0*q","w0+q")):
        changed=sample.NAMED_SOURCE.replace(old,new)
        assert changed!=sample.NAMED_SOURCE
        with patch.object(sample,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            sample.frozen_exp_sample_target()
    with patch.object(sample,"DEFINITION_SOURCE",sample.DEFINITION_SOURCE.replace("w0=f*h","w0=f+h")),pytest.raises(ValueError):
        sample.definition_registry()


def test_shared_definition_identity_and_reserved_id_are_protected():
    registry=dict(sample.argument_registry())
    registry["Pow"]=replace(registry["Pow"],stable_id="PD9999")
    with patch.object(sample,"argument_registry",return_value=registry),pytest.raises(ValueError):
        sample.computation_registry()
    with patch.object(sample,"DEFINITION_ID","ND0447"),pytest.raises(ValueError):
        sample.definition_registry()


def test_both_totality_endpoints_have_exact_replayed_bodies():
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


def test_small_exact_samples_and_all_index_factorial_normalization():
    for k in range(6):
        N=2*k+1;degree=k+2;d=2**k;s=isqrt(2*d*d)
        common=lcm(*range(1,N,2)) if k else 1
        previous=None
        for scale in (1,2,3):
            D=scale*common;x=0
            for i in range(N):
                x=3*x+(0 if i%2==0 else 2*D//i)
            p=3**N;u=3*x*d;v=D*p*s;f=factorial(degree);h=v**degree;w0=f*h
            weights=[(f//factorial(j))*v**(degree-j) for j in range(degree+1)]
            terms=[weights[j]*u**j for j in range(degree+1)];y=sum(terms)
            assert v!=0 and w0!=0 and u<=v and weights[0]==terms[0]==w0 and weights[-1]==1
            for j,t in enumerate(terms):
                assert (t*factorial(j))*v**j==w0*u**j
                if j<degree:
                    assert ((j+1)*v)*terms[j+1]==u*t
            exact=sum((Fraction(u,v)**j/factorial(j) for j in range(degree+1)),Fraction())
            assert Fraction(y,w0)==exact
            assert previous is None or previous==exact
            previous=exact


def test_complete_actual_sample_replay_without_new_induction_or_axioms():
    result=sample.prove_exp_sample()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_sample_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=sample.prove_exp_sample();node=result.bundle.root
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
