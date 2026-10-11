"""Exact component decisions, invalid candidates and proof-body rejection."""
from dataclasses import replace
from math import isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_component_decisions as decisions


def test_exact_three_unconditional_component_decisions():
    from peano_lab.kernel.formulas import And,Forall,Or,Imp,Bot
    from peano_lab.library.proof_bundle import encode_formula
    target=decisions.frozen_approximation_component_decisions_target()
    assert type(target) is And and type(target.right) is And
    for branch in (target.left,target.right.left,target.right.right):
        assert type(branch) is Forall
        while type(branch) is Forall:
            branch=branch.body
        assert type(branch) is Or and type(branch.right) is Imp
        assert branch.left==branch.right.antecedent and type(branch.right.consequent) is Bot
    assert len(decisions.canonical(encode_formula(target)))==7487
    c=decisions.source_contract()
    assert c['premise_count']==0 and len(c['constructive_decisions'])==3
    assert c['arbitrary_natural_inputs_including_invalid_scales'] is True
    assert c['actual_parity_and_Horner_totality_uniqueness_replayed'] is True
    assert c['new_induction_needed'] is c['classical_axioms_used'] is c['complete_CApprox_verifier_claim'] is c['closes_IR072'] is False


def test_twelve_existing_definitions_keep_their_exact_identity_and_dag():
    from sqrt2_power_exp_sample import definition_registry
    registry=decisions.definition_registry();original=definition_registry();seen=set();ids=set()
    assert len(registry)==12
    for name,spec in registry.items():
        assert spec==original[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decisions.source_contract()['new_definition_ids']==[]


def test_changed_parity_horner_or_dyadic_targets_are_rejected():
    source=decisions.NAMED_SOURCE;registry=decisions.definition_registry()
    for changed in (source.replace('NatAtanhCoefficient(d,i,a)','NatAtanhCoefficient(a,i,d)'),
                    source.replace('NatHornerValue(ab,ac,t,N,v)','NatHornerValue(ab,ac,t,S N,v)'),
                    source.replace('DyadicSqrt2(k,d,s)','DyadicSqrt2(k,s,d)')):
        assert changed!=source
        with patch.object(decisions,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decisions.frozen_approximation_component_decisions_target(_registry=registry)


def test_actual_parity_value_and_decision_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decisions.definition_registry();found=set()
    for pin in decisions.ARCHIVES:
        rows=decisions.read_mixed_archive(pin)
        for name,source in decisions.ENDPOINT_SOURCES.items():
            if decisions.ENDPOINT_OWNERS[name]!=pin['case']:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad['sha256']='0'*64
        with pytest.raises(ValueError):
            decisions.read_mixed_archive(bad)
    assert found==decisions.ENDPOINT_SOURCES.keys()


def test_small_component_models_handle_parity_invalid_scale_and_zero():
    coefficient=lambda d,i,a:(i%2==0 and a==0) or (i%2==1 and i*a==2*d)
    for d in range(5):
        for i in range(8):
            for a in range(10):
                expanded=any(i==2*j and a==0 for j in range(i+1)) or any(i==2*j+1 and i*a==2*d for j in range(i+1))
                assert coefficient(d,i,a)==expanded
    assert all(not coefficient(1,3,a) for a in range(20))
    assert coefficient(0,3,0) and coefficient(3,3,2) and coefficient(9,0,0)
    for b in range(5):
        for c in range(3):
            for t in range(3):
                value=0
                for n in range(5):
                    explicit=sum((b%(1+(i+1)*c))*t**(n-1-i) for i in range(n))
                    assert value==explicit
                    value=t*value+b%(1+(n+1)*c)
    for k in range(5):
        d=2**k;s=isqrt(2*d*d)
        assert d>0 and s*s<=2*d*d<(s+1)**2
        assert not ((s+1)**2<=2*d*d<(s+2)**2)


def test_complete_component_decisions_replay_without_new_induction():
    result=decisions.prove_approximation_component_decisions()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['solver_calls']==0 and result.provenance['independent_lean_checked'] is False


def test_forged_parity_decision_and_false_target_fail_replay():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decisions.prove_approximation_component_decisions();node=result.provenance['helper_bundle_indices']['coefficient_dec']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
