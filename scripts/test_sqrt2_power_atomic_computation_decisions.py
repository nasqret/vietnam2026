"""Decision-schema proofs, exact relation identities and adversarial controls."""
from dataclasses import replace
from math import factorial,isqrt
from unittest.mock import patch

import pytest
import sqrt2_power_atomic_computation_decisions as decisions


def test_exact_eight_unconditional_constructive_decisions():
    from peano_lab.kernel.formulas import And,Forall,Or,Imp,Bot
    from peano_lab.library.proof_bundle import encode_formula
    target=decisions.frozen_atomic_computation_decisions_target();cursor=target
    branches=[]
    for _ in range(7):
        assert type(cursor) is And
        branches.append(cursor.left);cursor=cursor.right
    branches.append(cursor)
    for branch in branches:
        assert type(branch) is Forall
        while type(branch) is Forall:
            branch=branch.body
        assert type(branch) is Or and type(branch.right) is Imp
        assert branch.left==branch.right.antecedent and type(branch.right.consequent) is Bot
    assert len(decisions.canonical(encode_formula(target)))==11078
    c=decisions.source_contract()
    assert c['premise_count']==0 and len(c['constructive_decisions'])==8
    assert c['totality_and_value_uniqueness_replayed'] is c['deterministic_proof_schema_not_oracle'] is True
    assert c['classical_axioms_used'] is c['markov_principle_used'] is c['complete_CApprox_verifier_claim'] is c['canonical_PR_approximation_algorithm_claim'] is c['closes_IR072'] is False


def test_ten_existing_definitions_are_conservative_and_topologically_ordered():
    from sqrt2_power_exp_sample import definition_registry
    registry=decisions.definition_registry();original=definition_registry();seen=set();ids=set()
    assert len(registry)==10
    for name,spec in registry.items():
        assert spec==original[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decisions.source_contract()['new_definition_ids']==[]


def test_changed_branches_or_computation_graphs_are_rejected():
    source=decisions.NAMED_SOURCE;registry=decisions.definition_registry()
    for changed in (source.replace('~(a=b)','~(b=b)'),source.replace('Pow(a,n,v)','Pow(a,S n,v)'),
                    source.replace('Factorial(n,v)','Factorial(v,n)'),source.replace('FloorSqrt(n,v)','FloorSqrt(v,n)')):
        assert changed!=source
        with patch.object(decisions,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decisions.frozen_atomic_computation_decisions_target(_registry=registry)


def test_each_dependency_resolves_to_exact_actual_proof_bytes():
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


def test_small_exact_models_include_zero_cases_and_false_candidates():
    # Calibration of the relation contracts, not authority for their decisions.
    for b in range(5):
        for c in range(4):
            values=[b%(1+(i+1)*c) for i in range(6)]
            assert all(0<=v<1+(i+1)*c for i,v in enumerate(values))
            for n in range(6):
                for v in (0,sum(values[:n]),sum(values[:n])+1):
                    assert (v==sum(values[:n])) != (v!=sum(values[:n]))
    for n in range(8):
        r=isqrt(n)
        assert r*r<=n<(r+1)*(r+1)
        for v in range(8):
            assert (v*v<=n<(v+1)*(v+1)) == (v==r)
            assert (v==factorial(n)) != (v!=factorial(n))
        for a in range(4):
            assert a**n != a**n+1
    assert 0**0==factorial(0)==1


def test_complete_decision_certificate_replays_with_one_explicit_induction():
    result=decisions.prove_atomic_computation_decisions()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['solver_calls']==0 and result.provenance['independent_lean_checked'] is False


def test_forged_equality_decision_and_false_target_fail_ordinary_replay():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=decisions.prove_atomic_computation_decisions();node=result.provenance['helper_bundle_indices']['eq_dec']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
