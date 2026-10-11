"""Finite 2^-n errors preserve both computations and construct actual powers."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import factorial,isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_sample_dyadic_error as dyadic


def test_exact_constructed_power_and_fixed_shift_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    target=dyadic.frozen_exp_sample_dyadic_error_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==32 and len(premises)==4 and type(conclusion) is Exists
    assert "NatSqrt2ExpSample(n+8," in dyadic.NAMED_SOURCE
    assert "NatSqrt2ExpSample((n+8)+l," in dyadic.NAMED_SOURCE
    assert "exists r. (Pow(2,n,r)" in dyadic.NAMED_SOURCE
    c=dyadic.source_contract()
    assert c["actual_dyadic_output_power_constructed"] is c["actual_shift_power_constructed"] is True
    assert c["actual_coarse_power_factored"] is c["only_proved_positive_shift_power_cancelled"] is True
    assert c["all_precision_indices_and_increments_including_zero"] is True
    assert c["canonical_PR_approximation_algorithm_claim"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_existing_computation_definition_dag_is_unchanged():
    from sqrt2_power_exp_sample_all_precision import definition_registry
    before=definition_registry();after=dyadic.definition_registry();seen=set();ids=set()
    assert len(after)==23 and dict(before)==dict(after)
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert dyadic.source_contract()["new_definition_ids"]==[]


def test_target_rejects_changed_shift_lost_guard_or_unbound_witness():
    source=dyadic.NAMED_SOURCE
    for changed in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("n+8","n+0"),source.replace("Pow(2,n,r)","Pow(2,n+8,r)"),
                    source.replace("+(w0*v0)","+0")):
        assert changed!=source
        with patch.object(dyadic,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            dyadic.frozen_exp_sample_dyadic_error_target()


def test_actual_all_precision_threshold_and_arithmetic_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=dyadic.definition_registry();found=set()
    for pin in dyadic.ARCHIVES:
        rows=dyadic.read_mixed_archive(pin)
        for name,source in dyadic.ENDPOINT_SOURCES.items():
            if dyadic.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            dyadic.read_mixed_archive(bad)
    assert found==dyadic.ENDPOINT_SOURCES.keys()


def test_finite_shifted_sample_models_have_dyadic_error_with_distinct_scales():
    def computation(k,scale):
        M=2*k+1;D=scale*lcm(*range(1,M,2));x=0
        for i in range(M):
            x=3*x+(0 if i%2==0 else 2*D//i)
        d=2**k;s=isqrt(2*d*d);p=3**M;U=3*x*d;V=D*p*s;N=k+2
        head=factorial(N)*V**N
        return d,head,sum(head*U**j//(factorial(j)*V**j) for j in range(N+1))
    for n,l in product(range(4),range(4)):
        d,w0,y=computation(n+8,1);q,v0,o=computation(n+8+l,2);r=2**n
        assert d==r*2**8 and (9*3)+2<=2**8
        assert r>0 and w0>0 and v0>0
        assert r*(w0*o)<=r*(v0*y)+(w0*v0)
        assert r*(v0*y)<=r*(w0*o)+(w0*v0)
        assert abs(Fraction(o,v0)-Fraction(y,w0))<=Fraction(1,r)
        if l==0:
            assert v0*y==w0*o and w0!=v0


def test_shift_cancellation_models_and_essential_guards():
    for v in range(1,5):
        for C in range(v+1):
            for r,x,y,h in product(range(4),repeat=4):
                d=r*v
                if d*x<=d*y+C*h:
                    assert r*x<=r*y+h
    # Without v!=0 or C<=v, the claimed conclusion need not follow.
    for d,r,v,C,x,y,h in ((0,1,0,0,1,0,0),(1,1,1,2,2,0,1)):
        assert d==r*v and d*x<=d*y+C*h and not r*x<=r*y+h


def test_complete_dyadic_error_replay_without_new_induction_or_axioms():
    result=dyadic.prove_exp_sample_dyadic_error()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_cancellation_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=dyadic.prove_exp_sample_dyadic_error();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
