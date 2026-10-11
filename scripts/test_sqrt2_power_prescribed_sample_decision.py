"""Full supplied-sample decision and sequential proof-schema guard tests."""
from dataclasses import replace
from math import factorial,isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_prescribed_sample_decision as decision


def test_exact_full_sample_decision_keeps_every_computation_and_positivity():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Or,Imp,Bot
    from peano_lab.library.proof_bundle import encode_formula
    target=decision.frozen_prescribed_sample_decision_target();binders,premises,conclusion=strip_target(target)
    assert binders==16 and not premises and type(conclusion) is Or
    assert type(conclusion.right) is Imp and type(conclusion.right.consequent) is Bot
    assert conclusion.left==conclusion.right.antecedent
    assert len(decision.canonical(encode_formula(target)))==35232
    assert decision.CHECK_PARTS==('Factorial(S(2*k),D)','~D=0',decision.GRAPH,'~w0=0')
    c=decision.source_contract()
    assert c['complete_supplied_sample_decision'] is c['exact_original_sample_graph_preserved'] is True
    assert c['all_fifteen_supplied_outputs_including_invalid_candidates'] is True
    assert c['classical_axioms_used'] is c['markov_principle_used'] is c['new_induction_needed'] is c['canonical_record_construction_claim'] is c['canonical_PR_approximation_algorithm_claim'] is c['closes_IR072'] is False


def test_all_twenty_three_sample_definitions_are_unchanged():
    from sqrt2_power_exp_sample import definition_registry
    registry=decision.definition_registry();original=definition_registry();seen=set();ids=set()
    assert dict(registry)==dict(original) and len(registry)==23
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decision.source_contract()['new_definition_ids']==[]


def test_changed_scale_or_denominator_conditions_are_rejected():
    source=decision.NAMED_SOURCE;registry=decision.definition_registry()
    for changed in (source.replace('Factorial(S(2*k),D)','Factorial(2*k,D)'),source.replace('~D=0','D=0'),
                    source.replace('~w0=0','w0=0'),source.replace('NatSqrt2ExpSample(k,','NatSqrt2ExpSample(S k,')):
        assert changed!=source
        with patch.object(decision,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decision.frozen_prescribed_sample_decision_target(_registry=registry)


def test_actual_all_component_decisions_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decision.definition_registry();found=set()
    for pin in decision.ARCHIVES:
        rows=decision.read_mixed_archive(pin)
        for name,source in decision.ENDPOINT_SOURCES.items():
            if decision.ENDPOINT_OWNERS[name]!=pin['case']:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad['sha256']='0'*64
        with pytest.raises(ValueError):
            decision.read_mixed_archive(bad)
    assert found==decision.ENDPOINT_SOURCES.keys()


def test_sequential_schema_checks_one_through_nine_fields_without_elim_holes():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    registry=decision.definition_registry();equality=parse_named(decision.ATOMIC_HELPERS['eq_dec'],registry=registry)
    for n in range(1,10):
        names=tuple('a'+str(i) for i in range(n))
        source='forall '+' '.join(names)+'. '+decision.decision(decision._and(tuple(name+'=0' for name in names)))
        target=Imp(equality,parse_named(source,registry=registry))
        producers=tuple(decision._decision_producer('eq_dec',name,'0') for name in names)
        proof=decision.introduce(decision.Scope(),(),('eq_dec',),lambda t:
            decision.introduce(t,names,(),lambda u:decision.sequential_conjunction_decision(u,producers,'test')))
        assert check((),proof,target)
    with pytest.raises(ValueError):
        decision.sequential_conjunction_decision(decision.Scope(),(),'empty')


def test_small_complete_sample_models_and_corrupted_scalar_fields():
    # Exact finite arithmetic calibration only; no analytic interpretation.
    for k in range(5):
        d=2**k;s=isqrt(2*d*d);D=factorial(2*k+1);x=0
        A=[0 if i%2==0 else 2*D//i for i in range(2*k+1)]
        for a in A:
            x=3*x+a
        p=3**(2*k+1);U=3*x*d;V=D*p*s;N=k+2;f=factorial(N);h=V**N
        W=[factorial(N)//factorial(j)*V**(N-j) for j in range(N+1)]
        T=[W[j]*U**j for j in range(N+1)];w0=W[0];y=sum(T)
        checks=(D==factorial(2*k+1),D!=0,d==2**k,s*s<=2*d*d<(s+1)**2,
            p==3**(2*k+1),W[N]==1,all(W[j]==((j+1)*V)*W[j+1] for j in range(N)),
            all(T[j]==W[j]*U**j for j in range(N+1)),W[0]==w0,T[0]==w0,
            f==factorial(N),h==V**N,w0==f*h,y==sum(T),w0!=0)
        assert all(checks)
        for i in range(len(checks)):
            bad=list(checks);bad[i]=False
            assert not all(bad)
        assert y+1!=sum(T) and w0+1!=f*h and p+1!=3**(2*k+1)


def test_complete_prescribed_sample_decision_replays_without_new_induction():
    result=decision.prove_prescribed_sample_decision()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['solver_calls']==0 and result.provenance['independent_lean_checked'] is False


def test_forged_sample_decision_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decision.prove_prescribed_sample_decision();node=result.provenance['helper_bundle_indices']['sample_dec']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
