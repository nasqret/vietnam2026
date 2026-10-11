"""Actual sample errors must not depend on arbitrary coefficient encodings."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample_modulus as modulus


def test_exact_positive_increment_sample_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=modulus.frozen_exp_sample_modulus_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==33 and len(premises)==5 and type(conclusion) is And
    assert len(modulus.canonical(encode_formula(target)))==35059
    c=modulus.source_contract()
    assert c["rational_increase_bound"]=="27/p+2/r" and c["rational_decrease_bound"]=="9/d"
    assert c["only_positive_factors_cancelled"] is c["all_displayed_rational_denominators_proved_nonzero"] is True
    assert c["argument_monotonicity_assumed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_complete_computation_definition_dag_is_unchanged():
    from sqrt2_power_supplied_exp_sample import definition_registry
    before=definition_registry();after=modulus.definition_registry();seen=set();ids=set()
    assert len(after)==23 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert modulus.source_contract()["new_definition_ids"]==[]


def test_exact_target_rejects_altered_precision_cutoff_and_error():
    source=modulus.NAMED_SOURCE
    for changed in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("NatSqrt2ExpSample(k+S l,","NatSqrt2ExpSample(k+l,"),
                    source.replace("Pow(2,k+2,r)","Pow(2,l+2,r)"),source.replace("+2*p","")):
        assert changed!=source
        with patch.object(modulus,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            modulus.frozen_exp_sample_modulus_target()


def test_actual_input_horizon_sample_and_cancellation_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=modulus.definition_registry();found=set()
    for pin in modulus.ARCHIVES:
        rows=modulus.read_mixed_archive(pin)
        for name,source in modulus.ENDPOINT_SOURCES.items():
            if modulus.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            modulus.read_mixed_archive(bad)
    assert found==modulus.ENDPOINT_SOURCES.keys()


def test_positive_factor_normalization_including_zero_heads_and_cutoff_factor():
    count=0
    for d,F,p,r,B,a,b,u,v in product(range(1,4),range(1,4),range(4),range(4),range(10),range(3),range(3),range(3),range(3)):
        if (p*B==3*F and r*(d*(F*(a*v)))<=r*(d*(F*(b*u)))+(9*(r*(d*B))+2*(d*F))*(a*b)
            and d*(F*(b*u))<=d*(F*(a*v))+9*(F*(a*b))):
            assert (p*r)*(a*v)<=(p*r)*(b*u)+((9*3)*r+2*p)*(a*b)
            assert d*(b*u)<=d*(a*v)+9*(a*b)
            count+=1
    assert count>100


def test_exact_finer_precision_models_with_independent_common_denominators():
    def computation(k,scale):
        M=2*k+1;D=scale*(lcm(*range(1,M,2)) if k else 1);x=0
        for i in range(M):
            x=3*x+(0 if i%2==0 else 2*D//i)
        d=2**k;s=isqrt(2*d*d);p=3**M;U=3*x*d;V=D*p*s;N=k+2
        head=factorial(N)*V**N;terms=[head*U**j//(factorial(j)*V**j) for j in range(N+1)]
        return d,p,head,sum(terms)
    directions=set()
    for k,l,left_scale,right_scale in product(range(5),range(3),range(1,3),range(1,3)):
        d,p,w0,y=computation(k,left_scale);q,h,v0,o=computation(k+l+1,right_scale);r=2**(k+2)
        assert all(n>0 for n in (d,p,r,w0,v0)) and (k+(l+1))+2==((k+2)+1)+l
        assert (p*r)*(w0*o)<=(p*r)*(v0*y)+((9*3)*r+2*p)*(w0*v0)
        assert d*(v0*y)<=d*(w0*o)+9*(w0*v0)
        delta=Fraction(o,v0)-Fraction(y,w0)
        assert delta<=Fraction(27,p)+Fraction(2,r) and -delta<=Fraction(9,d)
        directions.add((delta>0)-(delta<0))
    assert directions=={-1,1}


def test_complete_sample_modulus_replay_without_new_axioms_or_induction():
    result=modulus.prove_exp_sample_modulus()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_positive_factor_normalization_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=modulus.prove_exp_sample_modulus();node=result.provenance["helper_bundle_indices"]["normalize"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
