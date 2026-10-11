"""Both natural input orders and zero error multipliers must remain sound."""
from dataclasses import replace
from itertools import product
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_exp_two_sided_continuity as continuity


def test_exact_supplied_two_sided_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=continuity.frozen_exp_two_sided_continuity_target()
    binders,premises,conclusion=strip_target(target)
    assert binders==16 and len(premises)==12 and type(conclusion) is And
    assert len(continuity.canonical(encode_formula(target)))==6019
    c=continuity.source_contract()
    assert c["finite_lipschitz_constant"]==9
    assert c["common_error_multiplier_preserved"] is c["zero_error_multiplier_and_heads_allowed"] is True
    assert c["argument_monotonicity_assumed"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_minimal_existing_definition_dag_preserves_exact_identity():
    before=continuity.continuity_registry();after=continuity.definition_registry();seen=set();ids=set()
    assert tuple(after)==("Le","Lt","BetaAt","Sum","NatScaledExpRecurrence")
    for name,spec in after.items():
        assert spec==before[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()["new_definition_ids"]==[]


def test_target_rejects_missing_guards_changed_scales_and_shortcuts():
    source=continuity.NAMED_SOURCE
    for changed in (source.replace("~d=0 -> ",""),source.replace("~e=0 -> ",""),
                    source.replace("Le(x,d) -> ",""),source.replace("C*(d*y)","d*y"),
                    source.replace("+9*(R*(a0*b0))",""),source.replace("Sum(bb,bc,S N,t)","Sum(ab,ac,S N,t)")):
        assert changed!=source
        with patch.object(continuity,"NAMED_SOURCE",changed),pytest.raises(ValueError):
            continuity.frozen_exp_two_sided_continuity_target()


def test_actual_continuity_order_and_cancellation_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found=set()
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            ast=encode_formula(parse_named(source,registry=registry))
            matches=[r for r in rows if r[1]==ast]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad["sha256"]="0"*64
        with pytest.raises(ValueError):
            continuity.read_mixed_archive(bad)
    assert found==continuity.ENDPOINT_SOURCES.keys()


def test_natural_gap_cancellation_and_error_transport_including_zero():
    count=0
    for a,b,C,g,R,w in product(range(4),repeat=6):
        if b==a+g and C*b<=C*a+R:
            assert C*g<=R
        if a<=b+9*(g*w) and C*g<=R:
            assert C*a<=C*b+9*(R*w)
            count+=1
    assert count>100


def test_finite_rational_models_both_orders_independent_scales_and_zero_heads():
    directions=set();zero_heads=0;count=0
    def sample(d,x,N,scale):
        head=scale*factorial(N)*d**N
        terms=[head*x**j//(factorial(j)*d**j) for j in range(N+1)]
        assert all((j+1)*d*terms[j+1]==x*terms[j] for j in range(N))
        return head,sum(terms)
    for d,e,N,C,scale_a,scale_b in product(range(1,4),range(1,4),range(4),range(3),range(2),range(2)):
        for x,y in product(range(d+1),range(e+1)):
            a0,s=sample(d,x,N,scale_a);b0,t=sample(e,y,N,scale_b)
            R=max(C*(d*y-e*x),0);H=max(C*(e*x-d*y),0)
            assert C*((d*e)*(a0*t))<=C*((d*e)*(b0*s))+9*(R*(a0*b0))
            assert C*((d*e)*(b0*s))<=C*((d*e)*(a0*t))+9*(H*(a0*b0))
            directions.add((d*y>e*x)-(d*y<e*x));zero_heads+=int(a0==0 or b0==0);count+=1
    assert directions=={-1,0,1} and zero_heads>100 and count>1000


def test_complete_ordinary_replay_needs_no_new_induction_or_axioms():
    result=continuity.prove_exp_two_sided_continuity()
    assert result.receipt.target==result.target
    assert result.provenance["new_induction_count"]==0 and result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["endpoint_archive_selection"]["le_total"]["case"]=="CV098"


def test_forged_gap_cancellation_body_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=continuity.prove_exp_two_sided_continuity();node=result.provenance["helper_bundle_indices"]["cancel_order"]
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
