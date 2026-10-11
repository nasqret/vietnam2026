"""Finite decision schemas retain every supplied row and the last boundary."""
from dataclasses import replace
from math import factorial
from unittest.mock import patch

import pytest
import sqrt2_power_finite_table_decisions as decisions


def test_exact_three_unconditional_table_decisions_and_finite_domains():
    from peano_lab.kernel.formulas import And,Forall,Or,Imp,Bot
    from peano_lab.library.proof_bundle import encode_formula
    from sqrt2_power_definitions import parse_named
    registry=decisions.definition_registry();target=decisions.frozen_finite_table_decisions_target(_registry=registry)
    assert type(target) is And and type(target.right) is And
    for branch in (target.left,target.right.left,target.right.right):
        assert type(branch) is Forall
        while type(branch) is Forall:
            branch=branch.body
        assert type(branch) is Or and type(branch.right) is Imp
        assert branch.left==branch.right.antecedent and type(branch.right.consequent) is Bot
    assert len(decisions.canonical(encode_formula(target)))==7856
    assert parse_named(decisions.PARTS[0],registry=registry)==parse_named(decisions.HELPER_SOURCES['coefficient_prefix_dec'],registry=registry)
    assert parse_named(decisions.PARTS[2],registry=registry)==parse_named(decisions.HELPER_SOURCES['term_prefix_dec'],registry=registry)
    c=decisions.source_contract()
    assert c['premise_count']==0 and len(c['constructive_decisions'])==3
    assert c['arbitrary_supplied_tables_including_invalid_ones'] is c['zero_scale_and_empty_prefix_allowed'] is True
    assert c['classical_axioms_used'] is c['complete_CApprox_verifier_claim'] is c['closes_IR072'] is False


def test_ten_existing_definitions_keep_their_identity_and_acyclic_order():
    from sqrt2_power_exp_sample import definition_registry
    registry=decisions.definition_registry();original=definition_registry();seen=set();ids=set()
    assert len(registry)==10
    for name,spec in registry.items():
        assert spec==original[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decisions.source_contract()['new_definition_ids']==[]


def test_changed_domains_tables_or_scale_are_rejected():
    source=decisions.NAMED_SOURCE;registry=decisions.definition_registry()
    for changed in (source.replace('NatAtanhPrefix(d,ab,ac,N)','NatAtanhPrefix(d,ab,ac,S N)'),
                    source.replace('NatExpWeightTable(d,N,wb,wc)','NatExpWeightTable(N,d,wb,wc)'),
                    source.replace('NatPowerWeightedPrefix(x,wb,wc,tb,tc,N)','NatPowerWeightedPrefix(x,tb,tc,wb,wc,N)')):
        assert changed!=source
        with patch.object(decisions,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decisions.frozen_finite_table_decisions_target(_registry=registry)


def test_all_actual_decision_and_totality_dependencies_resolve_exactly():
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


def test_finite_models_reject_last_row_mutations_and_cover_empty_zero_cases():
    coefficient=lambda d,i,a:(i%2==0 and a==0) or (i%2==1 and i*a==2*d)
    prefix=lambda d,A,N:all(coefficient(d,i,A[i]) for i in range(N))
    weights=lambda d,W,N:W[N]==1 and all(W[j]==((j+1)*d)*W[j+1] for j in range(N))
    terms=lambda x,W,T,N:all(T[j]==W[j]*x**j for j in range(N))
    for N in range(6):
        D=factorial(N);A=[0 if i%2==0 else 2*D//i for i in range(N)]
        assert prefix(D,A,N)
        if N:
            bad=A.copy();bad[-1]+=1
            assert not prefix(D,bad,N) and prefix(D,bad,N-1)
        for d in range(3):
            W=[factorial(N)//factorial(j)*d**(N-j) for j in range(N+1)]
            assert weights(d,W,N)
            bad=W.copy();bad[N]=0
            assert not weights(d,bad,N)
            for x in range(3):
                T=[W[j]*x**j for j in range(N+1)]
                assert terms(x,W,T,N+1)
                bad=T.copy();bad[N]+=1
                assert not terms(x,W,bad,N+1) and terms(x,W,bad,N)
    assert prefix(0,[],0) and terms(0,[],[],0)
    assert weights(0,[1],0) and not weights(0,[0],0)


def test_complete_generated_table_decisions_replay_with_three_inductions():
    result=decisions.prove_finite_table_decisions()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==3 and result.provenance['new_axioms']==[]
    assert result.provenance['solver_calls']==0 and result.provenance['independent_lean_checked'] is False


def test_forged_bounded_prefix_and_false_target_fail_replay():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decisions.prove_finite_table_decisions();node=result.provenance['helper_bundle_indices']['term_prefix_dec']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
