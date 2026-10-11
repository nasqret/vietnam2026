"""Unrestricted recurrence equality must retain actual tables and guards."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_recurrence_independence as independence


def test_exact_identity_has_no_argument_bound_or_positive_head_premise():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=independence.frozen_exp_recurrence_independence_target();n,premises,conclusion=strip_target(target)
    assert n==13 and len(premises)==9 and type(conclusion) is Eq
    assert len(independence.canonical(encode_formula(target)))==4943
    c=independence.source_contract()
    assert c['both_supplied_recurrences_heads_and_sums_required'] is c['positive_denominators_required'] is True
    assert c['argument_upper_bound_required'] is c['head_positivity_required'] is False
    assert c['new_induction_count']==1 and c['natural_sum_identity']=='g*s=h*t'
    assert c['code_number_equality_claimed'] is c['analytic_exponential_identity_claimed'] is c['closes_IR072'] is False


def test_six_existing_definitions_preserve_the_exact_conservative_dag():
    registry=independence.definition_registry();source=independence.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','NatLinearTriple','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert independence.source_contract()['new_definition_ids']==[]


def test_changed_argument_guards_head_sum_or_result_are_rejected():
    source=independence.NAMED_SOURCE;registry=independence.definition_registry()
    for changed in (source.replace('~d=0','d=0'),source.replace('~e=0','e=0'),
                    source.replace('x*e=y*d','x*d=y*e'),source.replace('BetaAt(ab,ac,0,h)','BetaAt(ab,ac,1,h)'),
                    source.replace('Sum(bb,bc,S N,t)','Sum(bb,bc,N,t)'),source.replace('g*s=h*t','g*t=h*s'),
                    source.replace('~d=0 ->','~d=0 -> Le(x,d) ->')):
        assert changed!=source
        with patch.object(independence,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            independence.frozen_exp_recurrence_independence_target(_registry=registry)


def test_actual_integer_recurrence_models_include_large_arguments_and_zero_heads():
    from math import factorial
    examples=large=0
    for denominator in (1,2,3):
        for numerator in range(2*denominator+3):
            for alpha in (1,2):
                for beta in (1,2,3):
                    d,x,e,y=denominator*alpha,numerator*alpha,denominator*beta,numerator*beta
                    assert x*e==y*d
                    for N in range(6):
                        for hf,gf in ((0,1),(1,0),(1,1),(2,3)):
                            h,g=hf*factorial(N)*d**N,gf*factorial(N)*e**N
                            left=[];right=[]
                            for j in range(N+1):
                                an,ad=h*x**j,factorial(j)*d**j
                                bn,bd=g*y**j,factorial(j)*e**j
                                assert an%ad==bn%bd==0
                                a,b=an//ad,bn//bd;left.append(a);right.append(b)
                                assert g*a==h*b and max(an,ad,bn,bd,g*a,h*b).bit_length()<=128
                            assert left[0]==h and right[0]==g
                            assert all(((j+1)*d)*left[j+1]==x*left[j] for j in range(N))
                            assert all(((j+1)*e)*right[j+1]==y*right[j] for j in range(N))
                            assert g*sum(left)==h*sum(right)
                            examples+=1;large+=numerator>denominator
    assert examples==3024 and large==1728
    # Dropping d!=0 allows unconstrained successor values in the left table.
    d,e,x,y=0,1,0,0;left,right=[1,2],[1,0]
    assert x*e==y*d and d*left[1]==x*left[0] and e*right[1]==y*right[0]
    assert right[0]*sum(left)!=left[0]*sum(right)
    # Unequal arguments at positive denominators give different sums.
    assert sum((1,2))!=sum((1,3))


def test_all_thirteen_dependencies_resolve_to_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=independence.definition_registry();found={}
    for pin in independence.ARCHIVES:
        rows=independence.read_mixed_archive(pin)
        for name,source in independence.ENDPOINT_SOURCES.items():
            if independence.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==13 and found['mul_cancel']==('CV002',25) and found['linearity']==('CV006',107)
    with pytest.raises(ValueError):independence.read_mixed_archive(dict(independence.RECURRENCE_ARCHIVE,sha256='0'*64))


def test_pins_and_detached_solver_target_are_exact_without_proof_authority():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=independence.exp_recurrence_independence_source_pins();assert len(pins)==171
    target,digest,_=observer.target_for('AP060-cross-step')
    assert target==parse_named(independence.HELPER_SOURCES['cross_step'],registry=independence.definition_registry())
    assert digest==independence.HELPER_TARGET_SHA256['cross_step']
    for pin in independence.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert independence.source_contract()['original_HA_checked'] is False


def test_complete_independence_certificate_has_one_new_ordinary_induction():
    result=independence.prove_exp_recurrence_independence()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_induction_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=independence.prove_exp_recurrence_independence()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
