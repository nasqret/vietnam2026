"""Ordered power differences include zero bases and retain actual powers."""
from unittest.mock import patch

import pytest
import sqrt2_power_ordered_power_difference as difference


def test_exact_ordered_bound_preserves_gap_and_three_actual_powers():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    n,premises,conclusion=strip_target(difference.frozen_ordered_power_difference_target())
    names=tuple(reversed(difference.PARAMETERS));registry=difference.definition_registry()
    assert n==8 and len(premises)==5 and type(conclusion) is Exists
    assert premises==[parse_named(p,names,registry) for p in difference.PREMISES]
    assert conclusion==parse_named(difference.CONCLUSION,names,registry)
    c=difference.source_contract()
    assert c['zero_bases_gap_bound_and_k_allowed'] is c['all_three_actual_powers_preserved'] is True
    assert c['positive_bases_required'] is c['division_or_denominator_cancellation_used'] is c['closes_IR072'] is False
    assert c['new_induction_count']==1


def test_exact_six_existing_definitions_preserve_the_conservative_dag():
    from sqrt2_power_positive_power_comparison import argument_registry
    registry=difference.definition_registry();source=argument_registry();seen=set();ids=set()
    assert tuple(registry)==('Lt','BetaAt','Product','Repeat','Pow','Le')
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert difference.source_contract()['new_definition_ids']==[]


def test_changed_gap_upper_bound_exponent_or_coefficient_is_rejected():
    source=difference.NAMED_SOURCE;registry=difference.definition_registry()
    for changed in (source.replace('b=a+g','a=b+g'),source.replace('Le(b,M)','Le(a,M)'),
                    source.replace('Pow(a,S k,u)','Pow(a,k,u)'),source.replace('Pow(M,k,w)','Pow(M,S k,w)'),
                    source.replace('(S k)*(g*w)','k*(g*w)'),source.replace('Le(v,u+','Le(u,v+')):
        assert changed!=source
        with patch.object(difference,'NAMED_SOURCE',changed),pytest.raises(ValueError):difference.frozen_ordered_power_difference_target(_registry=registry)


def test_actual_power_models_and_arithmetic_boundary_guards():
    examples=0;zeroM=0;zerog=0;kzero=0
    for a in range(6):
        for g in range(5):
            b=a+g
            for margin in range(4):
                M=b+margin
                for k in range(7):
                    u=a**(k+1);v=b**(k+1);w=M**k
                    assert v<=u+(k+1)*(g*w) and max(v,u+(k+1)*(g*w)).bit_length()<=128
                    examples+=1;zeroM+=M==0;zerog+=g==0;kzero+=k==0
    assert examples==840 and zeroM==7 and zerog==168 and kzero==120
    arithmetic=0
    for a in range(4):
        for g in range(4):
            b=a+g
            for M in range(b,b+3):
                for j in range(4):
                    for W in range(3):
                        w=W*M
                        for U in range(w+1):
                            for V in (0,U,U+j*(g*W)):
                                assert V*b<=U*a+(j+1)*(g*w)
                                arithmetic+=1
    assert arithmetic>2000
    # The upper base bound, gap and successor coefficient are substantive.
    assert 2**2>1**2+2*(1*0**1)   # b<=M was dropped.
    assert 2**1>0**1+1*(0*2**0)   # b=a+g was dropped.
    assert 2**2>1**2+1*(1*2**1)   # k replaced k+1.


def test_seventeen_endpoints_have_unambiguous_actual_archive_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=difference.definition_registry();found={}
    for pin in difference.ARCHIVES:
        rows=difference.read_mixed_archive(pin)
        for name,source in difference.ENDPOINT_SOURCES.items():
            if difference.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==17 and found['power_zero']==('AP010',112) and found['power_step']==('AP010',113)
    assert found['base_monotone'][0]=='AP010'
    with pytest.raises(ValueError):difference.read_mixed_archive(dict(difference.POWER_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_arithmetic_target_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=difference.ordered_power_difference_source_pins()
    for pin in difference.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP076-arithmetic')
    assert target==parse_named(difference.HELPER_SOURCES['arithmetic'],registry=difference.definition_registry())
    assert digest==difference.HELPER_TARGET_SHA256['arithmetic']


def test_complete_ordered_power_difference_has_one_new_induction_no_new_axiom():
    result=difference.prove_ordered_power_difference()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=difference.prove_ordered_power_difference()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
