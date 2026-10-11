"""Joint finite errors retain two independent computations and both budgets."""
from fractions import Fraction
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_exp_joint_error as joint


def test_exact_joint_error_preserves_both_computations_and_budgets():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(joint.frozen_exp_joint_error_target())
    names=tuple(reversed(joint.PARAMETERS));registry=joint.definition_registry()
    assert n==19 and len(premises)==16 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in joint.PREMISES]
    assert conclusion==parse_named(joint.CONCLUSION,names,registry)
    c=joint.source_contract()
    assert c['both_actual_recurrences_heads_sums_and_codes_preserved'] is c['constructed_middle_prefix'] is True
    assert c['independent_denominators_heads_and_codes_allowed'] is c['input_and_tail_budgets_separate'] is True
    assert c['argument_order_assumed'] is c['analytic_continuity_or_limit_claimed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_twelve_existing_definitions_remain_conservative_and_unchanged():
    registry=joint.definition_registry();source=joint.source_registry();seen=set();ids=set()
    assert len(registry)==12
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert joint.source_contract()['new_definition_ids']==[]


def test_changed_horizon_input_budget_or_output_allowance_is_rejected():
    source=joint.NAMED_SOURCE;registry=joint.definition_registry()
    for changed in (source.replace('~e=0','e=0'),source.replace('S('+joint.D+')+N',joint.D+'+N'),
                    source.replace('Le(e*x,d*y+g)','Le(d*y,e*x+g)'),source.replace('Le(2*L,K)','Le(L,K)'),
                    source.replace('Le(p*g,d*e)','Le(p*g,d+e)'),source.replace('+2*(a0*b0)','+a0*b0')):
        assert changed!=source
        with patch.object(joint,'NAMED_SOURCE',changed),pytest.raises(ValueError):joint.frozen_exp_joint_error_target(_registry=registry)


def _actual_terms(x,d,N):
    terms=[Fraction(1)]
    for j in range(N):terms.append(terms[-1]*Fraction(x,(j+1)*d))
    head=lcm(*(term.denominator for term in terms))
    values=[int(head*term) for term in terms]
    assert values[0]==head and all((j+1)*d*values[j+1]==x*values[j] for j in range(N))
    return head,values


def test_actual_finite_models_cover_both_input_orders_tails_and_zero_heads():
    examples=0;forward=0;backward=0;positive_tail=0;zero_head=0;unequal=0
    def check_model(L,d,e,x,y,n,N):
        nonlocal examples,forward,backward,positive_tail,zero_head,unequal
        K=2*L;D=K+(L*K+n);H=D+1+N;r=2**n;p=2**(9*(L+1)+n+1);g=abs(d*y-e*x)
        assert x<=L*d and y<=L*e and p*g<=d*e
        ah,A=_actual_terms(x,d,D);bh,B=_actual_terms(y,e,H)
        for alpha in (0,1,2):
            for beta in (0,1,3):
                a,b=alpha*ah,beta*bh;s=alpha*sum(A);t=beta*sum(B);z=beta*sum(B[:D+1]);allowance=a*b
                assert r*(b*s)<=r*(a*z)+allowance and r*(a*z)<=r*(b*s)+allowance
                assert z<=t and r*t<=r*z+b
                assert r*(b*s)<=r*(a*t)+allowance and r*(a*t)<=r*(b*s)+2*allowance
                assert max(r*(b*s)+2*allowance,r*(a*t)+allowance,p*g,d*e).bit_length()<=128
                examples+=1;forward+=d*y>e*x;backward+=d*y<e*x
                positive_tail+=alpha>0 and t>z;zero_head+=a==0 or b==0;unequal+=d!=e
    for L in range(2):
        for d in range(1,4):
            for e in range(1,4):
                for x in range(L*d+1):
                    for y in range(L*e+1):
                        if d*y!=e*x:continue
                        for n in range(2):
                            for N in range(3):check_model(L,d,e,x,y,n,N)
    # Large dyadic input scales with small actual arguments keep the complete
    # rational model below 128 bits while genuinely testing a nonzero gap.
    p=2**19
    check_model(1,p,p,0,1,0,0);check_model(1,p,p,1,0,0,0)
    assert examples>1000 and forward==backward==9 and positive_tail>0 and zero_head>0 and unequal>0
    # Each unit of the arithmetic two-error allowance can be necessary.
    r=a=b=1;s=0;z=1;t=2
    assert r*(a*z)<=r*(b*s)+a*b and r*t<=r*z+b and r*(a*t)>r*(b*s)+a*b


def test_sixteen_endpoints_have_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=joint.definition_registry();found={}
    for pin in joint.ARCHIVES:
        rows=joint.read_mixed_archive(pin)
        for name,source in joint.ENDPOINT_SOURCES.items():
            if joint.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==16 and found['continuity']==('AP075',joint.CONTINUITY_ARCHIVE['root'])
    assert found['tail']==('AP063',joint.TAIL_ARCHIVE['root']) and found['restrict'][0]=='CV101'
    assert found['sum_exists'][0]=='CV003'
    with pytest.raises(ValueError):joint.read_mixed_archive(dict(joint.CONTINUITY_ARCHIVE,sha256='0'*64))


def test_current_sources_archives_and_exact_solver_helper_are_pinned():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=joint.exp_joint_error_source_pins()
    for pin in joint.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert 'sha256' in pins['scripts/sqrt2_power_exp_joint_error.py']
    target,digest,_=target_for('AP081-arithmetic')
    assert target==parse_named(joint.HELPER_SOURCES['arithmetic'],registry=joint.definition_registry())
    assert digest==joint.HELPER_TARGET_SHA256['arithmetic']
    with patch.dict(joint.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP081-arithmetic')


def test_complete_joint_error_replays_without_new_induction_or_axioms():
    result=joint.prove_exp_joint_error()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=joint.prove_exp_joint_error()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
