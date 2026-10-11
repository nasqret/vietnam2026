"""Actual positive fixed-schedule samples with all-index normalization."""
from math import factorial,lcm
from unittest.mock import patch

import pytest
import sqrt2_power_fixed_log_exp_witness as fixed


def test_uniform_threshold_precedes_every_constructed_positive_sample():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    registry=fixed.definition_registry();n,premises,conclusion=strip_target(fixed.frozen_fixed_log_exp_witness_target())
    assert n==1 and not premises and type(conclusion) is Exists
    body=conclusion.body
    assert body.left==parse_named('Pow(2,n,r)',('r','n'),registry)
    assert body.right.left==parse_named('~r=0',('r','n'),registry)
    assert body.right.right==parse_named(fixed.LATER_SOURCE,('r','n'),registry)
    k,guards,out=strip_target(body.right.right)
    assert k==1 and guards==[parse_named('Le(S(S(18*r)),k)',('k','r','n'),registry)]
    count=0
    while type(out) is Exists:count+=1;out=out.body
    assert count==13
    names=tuple(reversed(fixed.OUTPUTS))+('k','r','n')
    assert out==parse_named(fixed.conjoin(fixed.PARTS),names,registry)
    assert len(fixed.PARTS)==19 and fixed.PARTS[10]=='~h=0' and fixed.PARTS[16]==fixed.NORMALIZATION
    c=fixed.source_contract()
    assert c['precision_chosen_before_arbitrary_later_index'] is c['every_actual_term_factorial_normalization_retained'] is True
    assert c['root_quotient_accuracy_claimed'] is c['analytic_limit_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_nineteen_existing_definition_identities_and_dependency_order():
    registry=fixed.definition_registry();original=fixed.recursive_definition_registry_for_audit();seen=set();ids=set()
    assert len(registry)==19 and dict(registry)==dict(original)
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert {'NatZeroBefore','NatExpWeightTable','NatPowerWeightedPrefix','Factorial'}<=seen
    assert fixed.source_contract()['new_definition_ids']==[]


def test_changed_quantifier_order_schedule_positivity_or_normalization_is_rejected():
    source=fixed.NAMED_SOURCE;registry=fixed.definition_registry()
    for changed in (source.replace('exists r.','forall r.'),source.replace('18*r','18'),source.replace('S(2*k)','S k'),
                    source.replace('~h=0','h=0'),source.replace('h=f*q','h=f+q'),
                    source.replace('Pow(3*x,j,xj)','Pow(x,j,xj)'),source.replace('(r*2)*h+2*h','(r*2)*h+h')):
        assert changed!=source
        with patch.object(fixed,'NAMED_SOURCE',changed),pytest.raises(ValueError):fixed.frozen_fixed_log_exp_witness_target(_registry=registry)


def test_small_actual_log_and_factorial_exp_subcomputations():
    examples=0;normalized_terms=0;recurrences=0
    for k in range(3):
        for scale in (1,2):
            d=scale*lcm(*(j for j in range(1,2*k+1,2)));x=0
            for j in range(2*k+1):x=3*x+(0 if j%2==0 else 2*d//j)
            p=3**(2*k+1);den=d*p;X=3*x;N=k+2;f=factorial(N);q=den**N;h=f*q
            weights=[factorial(N)//factorial(j)*den**(N-j) for j in range(N+1)]
            terms=[weights[j]*X**j for j in range(N+1)];y=sum(terms)
            assert d>0 and p>0 and den>0 and weights[0]==terms[0]==h and h>0
            for j,a in enumerate(terms):
                assert (a*factorial(j))*den**j==h*X**j
                assert max((a*factorial(j))*den**j,h*X**j,y).bit_length()<=128
                normalized_terms+=1
            for j in range(N):
                assert (j+1)*den*terms[j+1]==X*terms[j];recurrences+=1
            examples+=1
    assert examples==6 and normalized_terms==24 and recurrences==18
    # These check the constructed subcomputations, not the full quantified
    # cutoff theorem: its first eligible index is 20, beyond this example cap.


def test_eight_endpoints_retain_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=fixed.definition_registry();found={}
    for pin in fixed.ARCHIVES:
        rows=fixed.read_mixed_archive(pin)
        for name,source in fixed.ENDPOINT_SOURCES.items():
            if fixed.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==8 and found['fixed']==('AP085',fixed.FIXED_ARCHIVE['root'])
    assert found['atanh']==('CV025',107) and found['exponential']==('CV070',143)
    with pytest.raises(ValueError):fixed.read_mixed_archive(dict(fixed.EXP_ARCHIVE,raw_sha256='0'*64))


def test_snapshot_sources_match_recursive_closure_and_reject_mutations():
    from copy import deepcopy
    current=fixed.fixed_log_exp_witness_source_pins();recursive=fixed.recursive_source_pins_for_audit()
    assert {name:pin for name,pin in current.items() if name!=fixed.INPUT_SNAPSHOT}==recursive
    for pin in fixed.ARCHIVES:assert current[pin['path']]['sha256']==pin['sha256']
    with patch.object(fixed,'INPUT_SNAPSHOT_SHA256','0'*64),pytest.raises(ValueError):fixed.definition_registry()
    snapshot=deepcopy(fixed._input_snapshot());snapshot['definitions'][0]['template_ast_sha256']='0'*64
    with patch.object(fixed,'_input_snapshot',return_value=snapshot),pytest.raises(ValueError):fixed.definition_registry()
    assert fixed.source_contract()['new_solver_arithmetic_leaf_needed'] is False


def test_complete_positive_witness_replays_without_new_induction_or_axioms():
    result=fixed.prove_fixed_log_exp_witness()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=fixed.prove_fixed_log_exp_witness()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
