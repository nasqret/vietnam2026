"""Uniform near-two bounds over arbitrary independent later computations."""
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_uniform_two as uniform


def test_precision_witness_precedes_all_later_tables_and_horizons():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    registry=uniform.definition_registry();n,premises,conclusion=strip_target(uniform.frozen_log_exp_uniform_two_target())
    assert n==1 and not premises and type(conclusion) is Exists
    body=conclusion.body
    assert type(body) is And and body.left==parse_named('Pow(2,n,r)',('r','n'),registry)
    assert body.right.left==parse_named('~r=0',('r','n'),registry)
    assert body.right.right==parse_named(uniform.UNIFORM_SOURCE,('r','n'),registry)
    m,fine_premises,fine_conclusion=strip_target(body.right.right)
    names=tuple(reversed(uniform.FINE_PARAMETERS))+('r','n')
    assert m==11 and len(fine_premises)==7
    assert fine_premises==[parse_named(p,names,registry) for p in uniform.FINE_PREMISES]
    assert fine_conclusion==parse_named(uniform.FINE_CONCLUSION,names,registry)
    assert not any('Le(' in p for p in uniform.FINE_PREMISES)
    c=uniform.source_contract()
    assert c['reference_and_precision_chosen_before_arbitrary_later_tables'] is True
    assert c['analytic_limit_claimed'] is c['analytic_log_exp_identity_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_exact_thirteen_definition_cone_reuses_old_identities():
    original=uniform.refinement_registry();registry=uniform.definition_registry();seen=set();ids=set()
    assert len(registry)==13 and 'IRatLe' not in registry and 'IRatValid' not in registry
    for name,spec in registry.items():
        assert spec==original[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert uniform.source_contract()['new_definition_ids']==[]


def test_changed_quantifier_order_computations_or_error_is_rejected():
    source=uniform.NAMED_SOURCE;registry=uniform.definition_registry()
    for changed in (source.replace('exists r.','forall r.'),source.replace('Pow(2,n,r)','Pow(3,n,r)'),
                    source.replace('18*r','18'),source.replace('~e=0','e=0'),
                    source.replace('(S(S(S(18*r))))+N','(S(S(18*r)))+N'),source.replace('(r*2)*b+2*b','(r*2)*b+b')):
        assert changed!=source
        with patch.object(uniform,'NAMED_SOURCE',changed),pytest.raises(ValueError):uniform.frozen_log_exp_uniform_two_target(_registry=registry)


def test_arithmetic_transfer_models_and_necessary_positive_head():
    examples=0;strict=0;unequal=0;zero_fine=0
    for r in range(5):
        for h in range(1,5):
            for y in range(4*h+1):
                if not (r*y<=(r*2)*h+h and (r*2)*h<=r*y+h):continue
                for b in range(5):
                    for v in range(5*b+2):
                        if not (b*y<=h*v and r*(h*v)<=r*(b*y)+h*b):continue
                        assert r*v<=(r*2)*b+2*b and (r*2)*b<=r*v+b
                        assert max(r*h*v,r*b*y+h*b).bit_length()<=128
                        examples+=1;strict+=h*v>b*y;unequal+=h!=b;zero_fine+=b==0
    assert examples>1000 and strict>0 and unequal>0 and zero_fine>0
    r=1;h=y=0;b=1;v=5
    assert r*y<=(r*2)*h+h and (r*2)*h<=r*y+h
    assert b*y<=h*v and r*(h*v)<=r*(b*y)+h*b
    assert not r*v<=(r*2)*b+2*b
    # This is an arithmetic leaf test, not a bounded evaluation of the full
    # M=18*2^n+2 exponential tables, which would exceed the 128-bit guard.


def test_fifteen_exact_endpoints_have_authenticated_actual_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=uniform.definition_registry();found={}
    for pin in uniform.ARCHIVES:
        rows=uniform.read_mixed_archive(pin)
        for name,source in uniform.ENDPOINT_SOURCES.items():
            if uniform.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==15 and found['reference']==('AP034',uniform.WITNESS_ARCHIVE['root'])
    assert found['refinement']==('AP083',uniform.REFINEMENT_ARCHIVE['root'])
    with pytest.raises(ValueError):uniform.read_mixed_archive(dict(uniform.WITNESS_ARCHIVE,bundle_sha256='0'*64))


def test_source_closure_and_exact_solver_helper_are_bound():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=uniform.log_exp_uniform_two_source_pins()
    for pin in uniform.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=target_for('AP084-arithmetic')
    assert target==parse_named(uniform.HELPER_SOURCES['arithmetic'],registry=uniform.definition_registry())
    assert digest==uniform.HELPER_TARGET_SHA256['arithmetic']
    with patch.dict(uniform.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP084-arithmetic')


def test_optimized_inputs_equal_recursive_sources_and_reject_mutations():
    from copy import deepcopy
    assert dict(uniform.definition_registry())==dict(uniform.recursive_definition_registry_for_audit())
    current=uniform.log_exp_uniform_two_source_pins();recursive=uniform.recursive_source_pins_for_audit()
    assert {name:pin for name,pin in current.items() if name!=uniform.INPUT_SNAPSHOT}==recursive
    with patch.object(uniform,'INPUT_SNAPSHOT_SHA256','0'*64),pytest.raises(ValueError):uniform.definition_registry()
    snapshot=deepcopy(uniform._input_snapshot());snapshot['definitions'][0]['template_ast_sha256']='0'*64
    with patch.object(uniform,'_input_snapshot',return_value=snapshot),pytest.raises(ValueError):uniform.definition_registry()


def test_complete_uniform_root_replays_without_new_induction_or_axioms():
    result=uniform.prove_log_exp_uniform_two()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=uniform.prove_log_exp_uniform_two()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
