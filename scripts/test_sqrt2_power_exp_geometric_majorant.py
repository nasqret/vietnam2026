"""Original-head term bounds with actual powers and a positive denominator."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_geometric_majorant as majorant


def test_exact_majorant_requires_actual_power_head_and_recurrence():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=majorant.frozen_exp_geometric_majorant_target();n,premises,conclusion=strip_target(target)
    assert n==10 and len(premises)==7 and type(conclusion) is Exists
    assert len(majorant.canonical(encode_formula(target)))==3210
    c=majorant.source_contract();assert c['supplied_recurrence_head_value_and_power_required'] is True
    assert c['new_induction_count']==1 and c['reference_head_index']==0
    assert c['large_ground_power_materialized'] is c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_seven_existing_definitions_keep_the_exact_dag():
    registry=majorant.definition_registry();source=majorant.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Repeat','Product','Pow','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert majorant.source_contract()['new_definition_ids']==[]


def test_changed_denominator_power_head_index_or_bound_is_rejected():
    source=majorant.NAMED_SOURCE;registry=majorant.definition_registry()
    for changed in (source.replace('~d=0','d=0'),source.replace('Pow(L,k,b)','Pow(x,k,b)'),
                    source.replace('BetaAt(tb,tc,0,h)','BetaAt(tb,tc,1,h)'),
                    source.replace('BetaAt(tb,tc,k,a)','BetaAt(tb,tc,S k,a)'),
                    source.replace('Le(k,N)','Le(N,k)'),source.replace('Le(a,b*h)','Le(b*h,a)')):
        assert changed!=source
        with patch.object(majorant,'NAMED_SOURCE',changed),pytest.raises(ValueError):majorant.frozen_exp_geometric_majorant_target(_registry=registry)


def test_integer_models_cover_zero_bound_head_and_actual_zero_power():
    from math import factorial
    examples=0
    for d in (1,2,3):
        for L in range(4):
            for x in range(L*d+1):
                for N in range(7):
                    for h in (0,factorial(N)*d**N):
                        values=[]
                        for k in range(N+1):
                            numerator,denominator=h*x**k,d**k*factorial(k)
                            assert numerator%denominator==0;values.append(numerator//denominator)
                            assert values[-1]<=L**k*h;examples+=1
                        assert all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
    assert examples==2688
    d,x,L,j,a,b=0,0,0,0,0,1
    assert x<=L*d and ((j+1)*d)*b==x*a and not b<=L*a
    assert not 2<=1**1*1  # x/d=2 is outside L=1.
    assert not 1<=0*1  # Wrong supplied value for 0^0.


def test_all_fifteen_dependencies_resolve_to_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=majorant.definition_registry();found={}
    for pin in majorant.ARCHIVES:
        rows=majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==15 and found['power_step']==('AP010',113) and found['mul_le_cancel']==('CV071',151)
    with pytest.raises(ValueError):majorant.read_mixed_archive(dict(majorant.BOUND_ARCHIVE,sha256='0'*64))


def test_source_archive_pins_and_detached_solver_binding_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=majorant.exp_geometric_majorant_source_pins();assert len(pins)==343
    target,digest,_=observer.target_for('AP056-step')
    assert target==parse_named(majorant.HELPER_SOURCES['step'],registry=majorant.definition_registry())
    assert digest==majorant.HELPER_TARGET_SHA256['step']
    for pin in majorant.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_majorant_certificate_has_one_new_ordinary_induction():
    result=majorant.prove_exp_geometric_majorant()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_induction_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=majorant.prove_exp_geometric_majorant()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
