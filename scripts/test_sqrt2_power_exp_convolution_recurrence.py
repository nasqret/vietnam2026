"""The added-argument recurrence holds only below the common finite cutoff."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_exp_convolution_recurrence as recurrence


def test_exact_finite_exponential_convolution_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=recurrence.frozen_exp_convolution_recurrence_target();binders,premises,conclusion=strip_target(target)
    assert binders==11 and len(premises)==5 and type(conclusion) is Eq
    assert len(recurrence.canonical(encode_formula(target)))==7109
    c=recurrence.source_contract()
    assert c['both_actual_input_recurrences_and_convolution_coefficients_required'] is c['strict_recurrence_index_bound_required'] is True
    assert c['actual_euler_tables_and_auxiliary_coefficients_constructed'] is True
    assert c['cancellation_used'] is c['analytic_exponential_addition'] is c['full_convolution_tail_recurrence'] is c['closes_IR072'] is False


def test_ten_existing_definitions_keep_exact_dependency_dag():
    registry=recurrence.definition_registry();pool=recurrence.source_registry();seen=set();ids=set()
    assert len(registry)==10
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert recurrence.source_contract()['new_definition_ids']==[]


def test_changed_cutoff_missing_input_and_wrong_argument_rejected():
    source=recurrence.NAMED_SOURCE;registry=recurrence.definition_registry()
    for changed in (source.replace('Lt(i,N)','Le(i,N)'),source.replace(recurrence.SECOND+' -> ',''),
                    source.replace('(x+y)*u','(x*y)*u'),source.replace('S N,bb','N,bb'),
                    source.replace('((S i)*d)*v','(i*d)*v')):
        assert changed!=source
        with patch.object(recurrence,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            recurrence.frozen_exp_convolution_recurrence_target(_registry=registry)


def test_exact_helpers_and_owned_product_shift_swap_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=recurrence.definition_registry();found={}
    assert {k:recurrence.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in recurrence.HELPER_SOURCES.items()}==recurrence.HELPER_TARGET_SHA256
    for pin in recurrence.ARCHIVES:
        rows=recurrence.read_mixed_archive(pin)
        for name,source in recurrence.ENDPOINT_SOURCES.items():
            if recurrence.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['coefficient_shift']==('AP037',130)
    assert found['product_rule']==('CV007',121) and found['coefficient_swap']==('CV014',158)
    bad=dict(recurrence.SHIFT_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): recurrence.read_mixed_archive(bad)


def _coefficient(a,b,i):
    return sum(a[j]*b[i-j] for j in range(len(a)) if 0<=i-j<len(b))


def test_positive_scale_exact_convolution_models():
    from math import factorial
    for N in range(6):
        for d in (1,2,3):
            for x,y in ((0,0),(0,2),(1,1),(2,3)):
                for left_scale,right_scale in ((0,1),(1,1),(2,3)):
                    def values(z,scale):
                        return [scale*(factorial(N)//factorial(j))*d**(N-j)*z**j for j in range(N+1)]
                    a,b=values(x,left_scale),values(y,right_scale)
                    assert all((j+1)*d*a[j+1]==x*a[j] and (j+1)*d*b[j+1]==y*b[j] for j in range(N))
                    assert all((i+1)*d*_coefficient(a,b,i+1)==(x+y)*_coefficient(a,b,i) for i in range(N))


def test_zero_denominator_models_are_not_silently_excluded():
    for N in range(5):
        a=list(range(1,N+2));b=list(range(2,N+3));d=x=y=0
        assert all((i+1)*d*_coefficient(a,b,i+1)==(x+y)*_coefficient(a,b,i) for i in range(N))
        a=[0]*N+[7];b=[0]*N+[9];x=1;y=2
        assert all((j+1)*d*a[j+1]==x*a[j] and (j+1)*d*b[j+1]==y*b[j] for j in range(N))
        assert all((i+1)*d*_coefficient(a,b,i+1)==(x+y)*_coefficient(a,b,i) for i in range(N))


def test_past_cutoff_and_omitted_recurrence_have_counterexamples():
    a=b=[1,1];N=1;d=x=y=1
    assert d*a[1]==x*a[0] and d*b[1]==y*b[0]
    assert (N+1)*d*_coefficient(a,b,N+1)!=(x+y)*_coefficient(a,b,N)
    assert _coefficient([1,9],[1,1],1)!=2*_coefficient([1,9],[1,1],0)


def test_solver_observer_is_bound_to_the_frozen_arithmetic_goal():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    target,digest,pins=observer.target_for('AP038-arithmetic')
    assert target==parse_named(recurrence.HELPER_SOURCES['arithmetic'],registry=recurrence.definition_registry())
    assert digest==recurrence.HELPER_TARGET_SHA256['arithmetic']
    assert pins()==recurrence.exp_convolution_recurrence_source_pins()


def test_complete_exponential_convolution_replays_without_new_induction():
    result=recurrence.prove_exp_convolution_recurrence()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_euler_shift_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=recurrence.prove_exp_convolution_recurrence();node=result.provenance['helper_bundle_indices']['euler_shift']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
