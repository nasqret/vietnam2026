"""Both natural input orders and both output error directions are retained."""
from unittest.mock import patch

import pytest
import sqrt2_power_symmetric_power_difference as difference


def test_exact_symmetric_statement_retains_both_bounds_gaps_and_powers():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(difference.frozen_symmetric_power_difference_target())
    names=tuple(reversed(difference.PARAMETERS));registry=difference.definition_registry()
    assert n==8 and len(premises)==7 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in difference.PREMISES]
    assert conclusion==parse_named(difference.CONCLUSION,names,registry)
    c=difference.source_contract()
    assert c['actual_ordered_gap_extracted'] is c['all_three_actual_powers_preserved'] is True
    assert c['input_order_assumed'] is c['positive_bases_required'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_six_existing_definitions_keep_the_same_conservative_dag():
    from sqrt2_power_positive_power_comparison import argument_registry
    registry=difference.definition_registry();source=argument_registry();seen=set();ids=set()
    assert tuple(registry)==('Lt','BetaAt','Product','Repeat','Pow','Le')
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert difference.source_contract()['new_definition_ids']==[]


def test_changed_symmetric_gap_exponent_coefficient_or_direction_is_rejected():
    source=difference.NAMED_SOURCE;registry=difference.definition_registry()
    for changed in (source.replace('Le(a,M)','Le(b,M)'),source.replace('Le(a,b+g)','Le(b,a+g)'),
                    source.replace('Pow(a,S k,u)','Pow(a,k,u)'),source.replace('Pow(M,k,w)','Pow(M,S k,w)'),
                    source.replace('(S k)*(g*w)','k*(g*w)'),source.replace('Le(u,v+(S k)*(g*w))','Le(v,u+(S k)*(g*w))')):
        assert changed!=source
        with patch.object(difference,'NAMED_SOURCE',changed),pytest.raises(ValueError):difference.frozen_symmetric_power_difference_target(_registry=registry)


def test_actual_power_models_cover_both_orders_loose_errors_and_zero_bounds():
    examples=0;forward=0;reverse=0;zeroM=0
    for a in range(10):
        for b in range(10):
            for margin in range(3):
                M=max(a,b)+margin
                for slack in range(3):
                    g=abs(b-a)+slack
                    for k in range(7):
                        u=a**(k+1);v=b**(k+1);w=M**k;E=(k+1)*(g*w)
                        assert a<=M and b<=M and b<=a+g and a<=b+g
                        assert v<=u+E and u<=v+E and max(v+E,u+E).bit_length()<=128
                        examples+=1;forward+=a<b;reverse+=b<a;zeroM+=M==0
    assert examples==6300 and forward==reverse==2835 and zeroM==21
    # Dropping either one-sided input error invalidates the other output bound.
    assert 1<=3+0 and not 3<=1+0
    assert 3**1>1**1+1*(0*3**0)


def test_eleven_owned_endpoints_include_actual_order_and_cancellation_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=difference.definition_registry();found={}
    for pin in difference.ARCHIVES:
        rows=difference.read_mixed_archive(pin)
        for name,source in difference.ENDPOINT_SOURCES.items():
            if difference.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==11 and found['ordered']==('AP076',difference.ORDERED_ARCHIVE['root'])
    assert found['base_monotone']==('AP010',123)
    assert all(found[name][0]=='AP007' for name in ('le_gap','cancel_order','allowance','le_total'))
    with pytest.raises(ValueError):difference.read_mixed_archive(dict(difference.ORDERED_ARCHIVE,sha256='0'*64))


def test_source_pins_bind_every_actual_archive_and_new_producer():
    pins=difference.symmetric_power_difference_source_pins()
    for pin in difference.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    for name in ('ordered_power_difference','symmetric_power_difference','exp_two_sided_continuity'):
        assert 'sha256' in pins['scripts/sqrt2_power_'+name+'.py']


def test_complete_symmetric_bound_replays_without_new_induction_or_axioms():
    result=difference.prove_symmetric_power_difference()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=difference.prove_symmetric_power_difference()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
