"""Uniform actual-sample error must preserve scale guards and true computations."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample_uniform_error as uniform


def test_exact_uniform_strict_precision_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    target=uniform.frozen_exp_sample_uniform_error_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==32 and len(premises)==4 and type(conclusion) is And
    c=uniform.source_contract()
    assert c["uniform_two_sided_error"]=="((9*3)+2)/d" and c["dyadic_denominator"]=="d=2^k"
    assert c["actual_cutoff_power_constructed_internally"] is c["only_proved_positive_factors_cancelled"] is True
    assert c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_complete_computation_definition_dag_remains_unchanged():
    from sqrt2_power_exp_sample_modulus import definition_registry
    before=definition_registry();after=uniform.definition_registry();seen=set();ids=set()
    assert len(after)==23 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert uniform.source_contract()["new_definition_ids"]==[]


def test_target_rejects_missing_scales_changed_precision_or_dyadic_error():
    source=uniform.NAMED_SOURCE
    for changed in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("NatSqrt2ExpSample(k+S l,","NatSqrt2ExpSample(k+l,"),
                    source.replace("((9*3)+2)*(w0*v0)","0"),source.replace("Le(d*(w0*o)","Le(p*(w0*o)")):
        assert changed!=source
        with patch.object(uniform,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            uniform.frozen_exp_sample_uniform_error_target()


def test_actual_modulus_power_bounds_and_positive_factor_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=uniform.definition_registry();found=set()
    for pin in uniform.ARCHIVES:
        rows=uniform.read_mixed_archive(pin)
        for name,source in uniform.ENDPOINT_SOURCES.items():
            if uniform.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            uniform.read_mixed_archive(bad)
    assert found==uniform.ENDPOINT_SOURCES.keys()


def test_generic_denominator_reduction_with_zero_numerators_and_error_weights():
    count=0
    for d,p,r,A,B,x,y,h in product(range(4),range(1,4),range(1,4),range(3),range(3),range(3),range(3),range(3)):
        if d<=p and d<=r and (p*r)*x<=(p*r)*y+(A*r+B*p)*h:
            assert d*x<=d*y+(A+B)*h
            count+=1
    assert count>1000
    for d,x,y,h in product(range(5),repeat=4):
        if d*y<=d*x+9*h:
            assert d*y<=d*x+((9*3)+2)*h


def test_actual_sample_models_obey_both_uniform_errors():
    def computation(k,scale):
        M=2*k+1;D=scale*(lcm(*range(1,M,2)) if k else 1);x=0
        for i in range(M):
            x=3*x+(0 if i%2==0 else 2*D//i)
        d=2**k;s=isqrt(2*d*d);p=3**M;U=3*x*d;V=D*p*s;N=k+2
        head=factorial(N)*V**N
        return d,head,sum(head*U**j//(factorial(j)*V**j) for j in range(N+1))
    directions=set()
    for k,l,scale in product(range(6),range(4),range(1,3)):
        d,w0,y=computation(k,scale);q,v0,o=computation(k+l+1,3-scale)
        assert d>0 and w0>0 and v0>0
        assert d*(w0*o)<=d*(v0*y)+29*(w0*v0)
        assert d*(v0*y)<=d*(w0*o)+29*(w0*v0)
        delta=Fraction(o,v0)-Fraction(y,w0)
        assert abs(delta)<=Fraction(29,d)
        directions.add((delta>0)-(delta<0))
    assert directions=={-1,1}


def test_complete_uniform_error_replay_without_new_induction_or_axioms():
    result=uniform.prove_exp_sample_uniform_error()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_denominator_reduction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=uniform.prove_exp_sample_uniform_error();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
