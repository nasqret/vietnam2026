"""Requested power precision preserves actual data, budgets and positive outputs."""
from unittest.mock import patch

import pytest
import sqrt2_power_requested_power_precision as precision


def test_exact_requested_bound_preserves_five_powers_and_budget():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(precision.frozen_requested_power_precision_target())
    names=tuple(reversed(precision.PARAMETERS));registry=precision.definition_registry()
    assert n==13 and len(premises)==12 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in precision.PREMISES]
    assert conclusion==parse_named(precision.CONCLUSION,names,registry)
    c=precision.source_contract()
    assert c['all_five_supplied_actual_powers_preserved'] is c['both_output_denominator_powers_proved_nonzero'] is True
    assert c['independent_argument_denominators_allowed'] is c['denominator_product_powers_constructed'] is True
    assert c['denominator_cancellation_used'] is c['input_order_assumed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_six_existing_definitions_remain_conservative_and_unchanged():
    from sqrt2_power_positive_power_comparison import argument_registry
    registry=precision.definition_registry();source=argument_registry();seen=set();ids=set()
    assert tuple(registry)==('Lt','BetaAt','Product','Repeat','Pow','Le')
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert precision.source_contract()['new_definition_ids']==[]


def test_changed_budget_denominator_or_power_is_rejected():
    source=precision.NAMED_SOURCE;registry=precision.definition_registry()
    for changed in (source.replace('~e=0','e=0'),source.replace('Pow(e,S k,E)','Pow(d,S k,E)'),
                    source.replace('Le(a*e,b*d+g)','Le(b*d,a*e+g)'),source.replace('r*(S k)','r*k'),
                    source.replace('g*C','g+C'),source.replace('r*(v*D)','r*(v*E)')):
        assert changed!=source
        with patch.object(precision,'NAMED_SOURCE',changed),pytest.raises(ValueError):precision.frozen_requested_power_precision_target(_registry=registry)


def test_actual_requested_precision_models_cover_positive_gaps_and_boundary_cases():
    examples=0;zero_precision=0;nonzero_gap=0;forward=0;reverse=0;unequal=0;zero_bound=0
    for M in range(4):
        for d in range(1,5):
            for e in range(1,5):
                for a in range(M*d+1):
                    for b in range(M*e+1):
                        for slack in range(3):
                            g=abs(b*d-a*e)+slack
                            for k in range(6):
                                m=k+1;u=a**m;v=b**m;D=d**m;E=e**m;C=M**k;Q=(d*e)**k
                                for r in (0,1,2,4,8):
                                    if (r*m)*(g*C)>d*e:continue
                                    assert D>0 and E>0 and D*E==(d*e)*Q
                                    assert r*(v*D)<=r*(u*E)+D*E and r*(u*E)<=r*(v*D)+D*E
                                    assert max(r*(v*D)+D*E,r*(u*E)+D*E).bit_length()<=128
                                    examples+=1;zero_precision+=r==0;nonzero_gap+=r>0 and a*e!=b*d
                                    forward+=r>0 and a*e<b*d;reverse+=r>0 and b*d<a*e
                                    unequal+=d!=e;zero_bound+=M==0
    assert examples>40000 and zero_precision==34992 and nonzero_gap>0 and forward==reverse>0 and unequal>0 and zero_bound>0
    # Without the budget, a legitimate power pair can exceed requested error.
    d=e=r=1;a=1;b=M=2;g=1;k=1
    assert (r*(k+1))*(g*M**k)>d*e and r*b**(k+1)>r*a**(k+1)+d**(k+1)*e**(k+1)
    # Replacing k+1 by k incorrectly accepts this degree-one counterexample.
    a=0;b=M=2;g=2;k=0
    assert (r*k)*(g*M**k)<=d*e and r*b>r*a+d*e


def test_eleven_endpoints_have_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=precision.definition_registry();found={}
    for pin in precision.ARCHIVES:
        rows=precision.read_mixed_archive(pin)
        for name,source in precision.ENDPOINT_SOURCES.items():
            if precision.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==11 and found['difference']==('AP079',precision.DIFFERENCE_ARCHIVE['root'])
    assert found['product']==('AP078',precision.PRODUCT_ARCHIVE['root']) and found['successor_value'][0]=='AP078'
    assert found['power_exists']==('AP010',110)
    with pytest.raises(ValueError):precision.read_mixed_archive(dict(precision.DIFFERENCE_ARCHIVE,sha256='0'*64))


def test_current_sources_archives_and_exact_solver_helper_are_pinned():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=precision.requested_power_precision_source_pins()
    for pin in precision.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert 'sha256' in pins['scripts/sqrt2_power_requested_power_precision.py']
    target,digest,_=target_for('AP080-arithmetic')
    assert target==parse_named(precision.HELPER_SOURCES['arithmetic'],registry=precision.definition_registry())
    assert digest==precision.HELPER_TARGET_SHA256['arithmetic']
    with patch.dict(precision.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP080-arithmetic')


def test_complete_requested_precision_replays_without_new_induction_or_axioms():
    result=precision.prove_requested_power_precision()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=precision.prove_requested_power_precision()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
