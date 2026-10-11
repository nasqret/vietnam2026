"""Relative finite continuity must not import a hidden small-argument bound."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_relative_continuity as continuity


def test_exact_relative_statement_has_no_argument_bound():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    target=continuity.frozen_exp_relative_continuity_target();n,premises,conclusion=strip_target(target)
    assert n==12 and len(premises)==8 and type(conclusion) is And
    names=tuple(reversed(continuity.PARAMETERS));registry=continuity.definition_registry()
    assert premises==[parse_named(p,names,registry) for p in continuity.PREMISES]
    assert conclusion==parse_named('Le(s,t) /\\ Le(d*t,d*s+g*t)',names,registry)
    c=continuity.source_contract()
    assert c['argument_upper_bound_required'] is c['absolute_majorant_claimed'] is c['analytic_continuity_claimed'] is c['closes_IR072'] is False
    assert c['actual_tail_slices_and_preceding_prefix_constructed'] is True


def test_seven_existing_definitions_preserve_the_exact_dag():
    registry=continuity.definition_registry();source=continuity.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','NatAffineSlice','NatLinearBound','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()['new_definition_ids']==[]


def test_changed_gap_head_denominator_or_relative_error_rejected():
    source=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for changed in (source.replace('y=x+g','x=y+g'),source.replace('~d=0','d=0'),
                    source.replace('BetaAt(bb,bc,0,a0)','BetaAt(bb,bc,0,s)'),
                    source.replace('+g*t','+g*s'),source.replace('Le(s,t)','Le(t,s)'),
                    source.replace('Sum(bb,bc,S N,t)','Sum(bb,bc,N,t)')):
        assert changed!=source
        with patch.object(continuity,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            continuity.frozen_exp_relative_continuity_target(_registry=registry)


def test_integer_models_include_large_arguments_zero_heads_and_empty_horizons():
    from math import factorial
    examples=0;large=0;zeroheads=0;empty=0
    for d in (1,2,3):
        for x in range(4*d+1):
            for g in range(4):
                y=x+g
                for N in range(7):
                    for scale in (0,1,2):
                        a0=scale*factorial(N)*d**N
                        A=[a0*x**j//(factorial(j)*d**j) for j in range(N+1)]
                        B=[a0*y**j//(factorial(j)*d**j) for j in range(N+1)]
                        assert A[0]==B[0]==a0
                        assert all(((j+1)*d)*A[j+1]==x*A[j] and ((j+1)*d)*B[j+1]==y*B[j] for j in range(N))
                        s,t=sum(A),sum(B)
                        assert s<=t and d*t<=d*s+g*t and max(d*t,d*s+g*t).bit_length()<=128
                        examples+=1;large+=y>2*d;zeroheads+=scale==0;empty+=N==0
    assert examples==2268 and large>0 and zeroheads>0 and empty>0


def test_actual_unrestricted_slice_and_sum_endpoint_bodies_are_owned():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found={}
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==12 and found['sum_bound']==('CV095',25) and found['sum_exists']==('CV003',107)
    assert all(found[name][0]=='CV096' for name in ('split_head','prefix_below','tail_graphs'))
    with pytest.raises(ValueError):continuity.read_mixed_archive(dict(continuity.CONTINUITY_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_arithmetic_target_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=continuity.exp_relative_continuity_source_pins();assert len(pins)==175
    for pin in continuity.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP068-arithmetic')
    assert target==parse_named(continuity.HELPER_SOURCES['arithmetic'],registry=continuity.definition_registry())
    assert digest==continuity.HELPER_TARGET_SHA256['arithmetic']


def test_complete_relative_continuity_without_new_induction_or_axiom():
    result=continuity.prove_exp_relative_continuity()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=continuity.prove_exp_relative_continuity()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
