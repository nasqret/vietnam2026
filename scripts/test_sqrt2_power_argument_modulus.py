"""Independent positive log/root graphs need two error directions, not monotonicity."""
from dataclasses import replace
from fractions import Fraction
from itertools import product
from math import isqrt,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_argument_modulus as modulus


def test_exact_two_sided_supplied_precision_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=modulus.frozen_argument_modulus_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==16 and len(premises)==4 and type(conclusion) is And
    assert len(modulus.canonical(encode_formula(target)))==13867
    c=modulus.source_contract()
    assert c["rational_increase_bound"]=="3/p" and c["rational_decrease_bound"]=="1/d"
    assert c["argument_monotonicity_assumed"] is c["analytic_identity_claim"] is c["closes_IR072"] is False
    assert c["actual_coarse_and_fine_powers_preserved"] is c["exact_prefix_length_alignment"] is True


def test_only_existing_rational_definitions_extend_the_computation_dag():
    from sqrt2_power_log_root_argument import definition_registry
    before=definition_registry();after=modulus.definition_registry();seen=set();ids=set()
    assert len(after)==18 and set(after)-set(before)=={"IRatValid","IRatLe"}
    for name,spec in after.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
        if name in before:
            assert spec==before[name]
    assert modulus.source_contract()["new_definition_ids"]==[]


def test_scale_precision_and_both_error_directions_are_frozen():
    source=modulus.NAMED_SOURCE
    for changed in (source.replace("~D=0 -> ",""),source.replace("~E=0 -> ",""),
                    source.replace("NatSqrt2LogArgument(k+l,q","NatSqrt2LogArgument(l,q"),
                    source.replace("((3*D)*(E*h))*(s*t)","0"),
                    source.replace("+((D*p)*s)*((E*h)*t)","")):
        assert changed!=source
        with patch.object(modulus,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            modulus.frozen_argument_modulus_target()


def test_actual_logarithm_reciprocal_and_supplied_argument_endpoints():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=modulus.definition_registry();found=set()
    for pin in modulus.ARCHIVES:
        rows=modulus.read_mixed_archive(pin)
        for name,source in modulus.ENDPOINT_SOURCES.items():
            if modulus.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            modulus.read_mixed_archive(bad)
    assert found==modulus.ENDPOINT_SOURCES.keys()


def test_generic_arithmetic_including_all_zero_boundary_cases():
    count=0
    for a,b,c,e,d,s,q,t,r in product(range(3),repeat=9):
        if a*e<=b*c<=a*e+r and a<=c and q*s<=d*t and d*(d*t)<=d*(q*s)+s*t and q<=t:
            assert (c*s)*(b*q)<=(e*t)*(a*d)+r*(s*t)
            assert d*((e*t)*(a*d))<=d*((c*s)*(b*q))+(c*s)*(e*t)
            count+=1
    assert count>100


def test_exact_independent_precision_models_and_nonmonotone_inputs():
    def computation(k,scale):
        N=2*k+1;D=scale*(lcm(*range(1,N,2)) if k else 1);x=0
        for i in range(N):
            x=3*x+(0 if i%2==0 else 2*D//i)
        d=2**k;s=isqrt(2*d*d);p=3**N
        return d,s,D,x,p
    values=[]
    for k in range(7):
        d,s,D,x,p=computation(k,1);U=3*x*d;V=D*p*s;values.append(Fraction(U,V))
        for l in range(5):
            q,t,E,z,h=computation(k+l,2);Z=3*z*q;W=E*h*t
            assert V>0 and W>0 and V*Z<=W*U+(3*D)*(E*h)*(s*t)
            assert d*(W*U)<=d*(V*Z)+V*W
            assert Fraction(Z,W)-Fraction(U,V)<=Fraction(3,p)
            assert Fraction(U,V)-Fraction(Z,W)<=Fraction(1,d)
            assert 1+2*(k+l)==(1+2*k)+2*l
    assert any(b>a for a,b in zip(values,values[1:]))
    assert any(b<a for a,b in zip(values,values[1:]))


def test_complete_argument_error_replay_without_new_induction_or_axioms():
    result=modulus.prove_argument_modulus()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_error_arithmetic_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=modulus.prove_argument_modulus();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
