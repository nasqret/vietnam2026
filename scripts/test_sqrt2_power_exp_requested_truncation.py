"""Requested finite truncation accuracy must retain computations and guards."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_requested_truncation as truncation


def test_exact_requested_cutoff_retains_nonzero_scale_and_both_bounds():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_exp_requested_truncation_target();n,premises,conclusion=strip_target(target)
    assert n==12 and len(premises)==8 and type(conclusion) is And
    assert len(truncation.canonical(encode_formula(target)))==6482
    c=truncation.source_contract()
    assert c['supplied_recurrence_head_sums_and_precision_power_preserved'] is True
    assert c['auxiliary_powers_constructed_not_assumed'] is c['uniform_in_extra_finite_horizon'] is True
    assert c['fixed_approximation_program_changed'] is c['infinite_remainder_or_analytic_exponential_claimed'] is c['closes_IR072'] is False


def test_eight_existing_definitions_preserve_the_exact_dag():
    registry=truncation.definition_registry();source=truncation.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','Repeat','Product','Pow','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert truncation.source_contract()['new_definition_ids']==[]


def test_changed_cutoff_head_scale_or_error_is_rejected():
    source=truncation.NAMED_SOURCE;registry=truncation.definition_registry()
    for changed in (source.replace('S(L*K+n)','L*K+n'),source.replace('Le(2*L,K)','Le(L,K)'),
                    source.replace('BetaAt(ab,ac,0,h)','BetaAt(ab,ac,K,h)'),source.replace('Pow(2,n,r)','Pow(2,S n,r)'),
                    source.replace('Le(r*t,r*s+h)','Le(r*t,r*s)'),source.replace('~d=0','d=0')):
        assert changed!=source
        with patch.object(truncation,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            truncation.frozen_exp_requested_truncation_target(_registry=registry)


def test_integer_tail_models_and_positive_cancellation_counterexamples():
    from math import factorial
    examples=0;large=False
    for d in (1,2):
        for L in range(3):
            for x in range(L*d+1):
                K=2*L
                for n in range(3):
                    for N in range(4):
                        short=K+(L*K+n+1);H=short+N;r=2**n
                        for scale in (0,1,2):
                            h=scale*factorial(H)*d**H;values=[]
                            for j in range(H+1):
                                numerator,denominator=h*x**j,d**j*factorial(j)
                                assert numerator%denominator==0 and max(numerator,denominator).bit_length()<=128
                                values.append(numerator//denominator)
                            assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(H))
                            s,t=sum(values[:short]),sum(values)
                            assert r>0 and s<=t and r*t<=r*s+h
                            examples+=1;large|=x>d
    assert examples==540 and large
    p,r,B,h,s,t=0,1,0,0,0,1
    assert 2*(r*B)<=p and p*t<=p*s+2*(B*h) and not r*t<=r*s+h
    p,r,B,h,s,t=1,1,1,1,0,2
    assert p>0 and p*t<=p*s+2*(B*h) and not 2*(r*B)<=p and not r*t<=r*s+h


def test_all_eleven_dependencies_resolve_to_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=truncation.definition_registry();found={}
    for pin in truncation.ARCHIVES:
        rows=truncation.read_mixed_archive(pin)
        for name,source in truncation.ENDPOINT_SOURCES.items():
            if truncation.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==11 and found['budget']==('AP062',128) and found['truncation']==('AP057',159)
    with pytest.raises(ValueError):truncation.read_mixed_archive(dict(truncation.BUDGET_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_arithmetic_target_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=truncation.exp_requested_truncation_source_pins();assert len(pins)==357
    for pin in truncation.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP063-arithmetic')
    assert target==parse_named(truncation.HELPER_SOURCES['arithmetic'],registry=truncation.definition_registry())
    assert digest==truncation.HELPER_TARGET_SHA256['arithmetic']


def test_complete_requested_truncation_without_new_induction():
    result=truncation.prove_exp_requested_truncation()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=truncation.prove_exp_requested_truncation()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
