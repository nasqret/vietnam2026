"""Symbolic power budgets retain all actual computations and zero cases."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_binary_budget as budget


def test_exact_binary_budget_includes_both_nonzero_dyadic_scales():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=budget.frozen_exp_binary_budget_target();n,premises,conclusion=strip_target(target)
    assert n==6 and len(premises)==3 and type(conclusion) is And
    assert len(budget.canonical(encode_formula(target)))==5603
    c=budget.source_contract();assert c['both_dyadic_powers_proved_nonzero'] is True
    assert c['zero_L_K_and_n_allowed'] is True and c['new_induction_count']==1
    assert c['large_ground_power_materialized'] is c['fixed_approximation_program_changed'] is c['analytic_remainder_claimed'] is c['closes_IR072'] is False


def test_six_existing_power_definitions_are_unchanged():
    from sqrt2_power_half_log_precision import definition_registry as source_registry
    registry=budget.definition_registry();source=source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Repeat','Product','Pow'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert budget.source_contract()['new_definition_ids']==[]


def test_changed_supplied_power_cutoff_factor_or_positivity_is_rejected():
    source=budget.NAMED_SOURCE;registry=budget.definition_registry()
    for changed in (source.replace('Pow(L,K,B)','Pow(L,n,B)'),source.replace('Pow(2,n,r)','Pow(2,K,r)'),
                    source.replace('S(L*K+n)','L*K+n'),source.replace('2*(r*B)','3*(r*B)'),
                    source.replace('~r=0','r=0'),source.replace('~p=0','p=0')):
        assert changed!=source
        with patch.object(budget,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            budget.frozen_exp_binary_budget_target(_registry=registry)


def test_small_integer_power_models_cover_zero_base_exponent_and_precision():
    examples=0
    for L in range(11):
        for K in range(7):
            for n in range(9):
                B,C,r,p=L**K,2**(L*K),2**n,2**(L*K+n+1)
                assert B<=C and r>0 and p>0 and 2*(r*B)<=p
                assert max(B,C,r,p).bit_length()<=128
                examples+=1
    assert examples==693
    # At L=K=n=0, 0^0=1; omitting the successor in the cutoff is false.
    assert not 2*(2**0*0**0)<=2**(0*0+0)
    # A forged majorant value is not an actual power computation.
    assert not 2*(1*2)<=2**(0*0+0+1)


def test_all_fourteen_power_endpoints_have_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=budget.definition_registry();found={}
    for pin in budget.ARCHIVES:
        rows=budget.read_mixed_archive(pin)
        for name,source in budget.ENDPOINT_SOURCES.items():
            if budget.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==14 and found['binary_growth']==('AP046',35) and found['power_add']==('AP010',119)
    with pytest.raises(ValueError):budget.read_mixed_archive(dict(budget.PRECISION_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_solver_binding_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=budget.exp_binary_budget_source_pins();assert len(pins)==235
    for pin in budget.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP062-arithmetic')
    assert target==parse_named(budget.HELPER_SOURCES['arithmetic'],registry=budget.definition_registry())
    assert digest==budget.HELPER_TARGET_SHA256['arithmetic']


def test_complete_budget_certificate_has_one_new_ordinary_induction():
    result=budget.prove_exp_binary_budget()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_induction_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=budget.prove_exp_binary_budget()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
