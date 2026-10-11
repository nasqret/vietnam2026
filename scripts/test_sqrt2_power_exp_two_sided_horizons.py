"""Unequal horizons must preserve both input directions and the actual tail."""
from dataclasses import replace
from itertools import product
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_exp_two_sided_horizons as horizons


def test_exact_two_sided_unequal_horizon_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=horizons.frozen_exp_two_sided_horizons_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==18 and len(premises)==13 and type(conclusion) is And
    assert len(horizons.canonical(encode_formula(target)))==8031
    c=horizons.source_contract()
    assert c["actual_cutoff_power"]=="p=2^m" and c["whole_degree"]=="m+N+1"
    assert c["shorter_sum_uses_actual_longer_table"] is c["rational_reading_requires_separate_positivity"] is True
    assert c["argument_monotonicity_assumed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_exact_existing_power_and_recurrence_definition_dag():
    before=horizons.horizon_registry();after=horizons.definition_registry();seen=set();ids=set()
    assert tuple(after)==("Le","Lt","BetaAt","Sum","Repeat","Product","Pow","NatScaledExpRecurrence")
    for name,spec in after.items():
        assert spec==before[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert horizons.source_contract()["new_definition_ids"]==[]


def test_exact_target_rejects_changed_horizon_power_scale_or_error():
    source=horizons.NAMED_SOURCE
    for changed in (source.replace("~d=0 -> ",""),source.replace("~e=0 -> ",""),
                    source.replace("(S m)+N","m+N"),source.replace("Pow(2,m,p)","Pow(2,N,p)"),
                    source.replace("C*(d*y)","d*y"),source.replace("+2*(C*(d*e))","")):
        assert changed!=source
        with patch.object(horizons,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            horizons.frozen_exp_two_sided_horizons_target()


def test_actual_continuity_truncation_restriction_and_sum_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=horizons.definition_registry();found=set()
    for pin in horizons.ARCHIVES:
        rows=horizons.read_mixed_archive(pin)
        for name,source in horizons.ENDPOINT_SOURCES.items():
            if horizons.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            ast=encode_formula(parse_named(source,registry=registry));matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            horizons.read_mixed_archive(bad)
    assert found==horizons.ENDPOINT_SOURCES.keys()


def test_arithmetic_combination_including_all_zero_scale_boundaries():
    count=0
    for D,C,R,H,p,a0,b0,s,r,t in product(range(3),repeat=10):
        if (C*(D*(a0*r))<=C*(D*(b0*s))+9*(R*(a0*b0)) and
            C*(D*(b0*s))<=C*(D*(a0*r))+9*(H*(a0*b0)) and r<=t and p*t<=p*r+2*b0):
            assert p*(C*(D*(a0*t)))<=p*(C*(D*(b0*s)))+(9*(p*R)+2*(C*D))*(a0*b0)
            assert C*(D*(b0*s))<=C*(D*(a0*t))+9*(H*(a0*b0))
            count+=1
    assert count>1000


def test_distinct_horizon_models_keep_the_longer_tables_actual_prefix():
    directions=set();count=0
    def sample(d,x,n,scale):
        head=scale*factorial(n)*d**n
        terms=[head*x**j//(factorial(j)*d**j) for j in range(n+1)]
        assert all((j+1)*d*terms[j+1]==x*terms[j] for j in range(n))
        return head,terms
    for d,e,m,N,C,scale_a,scale_b in product(range(1,4),range(1,4),range(3),range(3),range(3),range(2),range(2)):
        for x,y in product(range(d+1),range(e+1)):
            a0,A=sample(d,x,m,scale_a);b0,B=sample(e,y,m+N+1,scale_b)
            s,r,t=sum(A),sum(B[:m+1]),sum(B);p=2**m;D=d*e
            assert r<=t and p*t<=p*r+2*b0
            R=max(C*(d*y-e*x),0);H=max(C*(e*x-d*y),0)
            assert p*(C*(D*(a0*t)))<=p*(C*(D*(b0*s)))+(9*(p*R)+2*(C*D))*(a0*b0)
            assert C*(D*(b0*s))<=C*(D*(a0*t))+9*(H*(a0*b0))
            directions.add((d*y>e*x)-(d*y<e*x));count+=1
    assert directions=={-1,0,1} and count>1000


def test_complete_ordinary_replay_with_no_new_induction_or_axiom():
    result=horizons.prove_exp_two_sided_horizons()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False


def test_forged_combination_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=horizons.prove_exp_two_sided_horizons();node=result.provenance["helper_bundle_indices"]["arithmetic"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
