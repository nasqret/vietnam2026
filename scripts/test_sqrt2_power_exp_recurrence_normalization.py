"""Factorial-series normalization follows from the caller's actual recurrence."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_exp_recurrence_normalization as norm


def test_exact_supplied_recurrence_normalization_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=norm.frozen_exp_recurrence_normalization_target();binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==2 and type(conclusion) is Forall
    assert len(norm.canonical(encode_formula(target)))==6528
    c=norm.source_contract()
    assert c['actual_supplied_table_and_head_preserved'] is c['all_in_range_entries_and_actual_factorials_powers'] is True
    assert c['zero_input_denominator_numerator_head_and_horizon_allowed'] is True
    assert c['new_induction_count']==1
    assert c['cancellation_used'] is c['rational_validity_claim'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_nine_definition_dependency_cone_is_preserved():
    registry=norm.definition_registry();pool=norm.source_registry();seen=set();ids=set()
    assert len(registry)==9 and set(registry)<=set(pool)
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert norm.source_contract()['new_definition_ids']==[]


def test_changed_table_head_horizon_power_or_normalization_is_rejected():
    source=norm.NAMED_SOURCE;registry=norm.definition_registry()
    for changed in (source.replace('BetaAt(tb,tc,0,h) -> ',''),source.replace('Le(j,N)','Le(j,S N)'),
                    source.replace('Pow(d,j,p)','Pow(x,j,p)'),source.replace('(t*f)*p=h*q','(t*f)*q=h*p'),
                    source.replace('BetaAt(tb,tc,j,t)','BetaAt(tc,tb,j,t)')):
        assert changed!=source
        with patch.object(norm,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            norm.frozen_exp_recurrence_normalization_target(_registry=registry)


def test_actual_factorial_power_and_shuffle_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=norm.definition_registry();rows=norm.read_mixed_archive(norm.EXP_ARCHIVE);found={}
    for name,source in norm.ENDPOINT_SOURCES.items():
        ast=encode_formula(parse_named(source,registry=registry))
        matches=[i for i,row in enumerate(rows) if row[1]==ast]
        assert len(matches)==1 and rows[matches[0]][3];found[name]=matches[0]
    assert found['factorial_zero']==128 and found['factorial_step']==129 and found['shuffle']==137
    bad=dict(norm.EXP_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): norm.read_mixed_archive(bad)


def test_exact_models_include_zero_denominator_head_numerator_and_horizon():
    from math import factorial
    examples=[]
    for N in range(6):
        for d in (1,2,3):
            for x in (0,1,2):
                for scale in (0,1,3):
                    h=scale*factorial(N)*d**N
                    values=[scale*(factorial(N)//factorial(j))*d**(N-j)*x**j for j in range(N+1)]
                    examples.append((d,x,N,h,values))
    examples.extend([(0,0,4,7,[7,13,9,2,5]),(0,2,3,0,[0,0,0,17]),(0,5,0,9,[9])])
    for d,x,N,h,values in examples:
        assert values[0]==h
        assert all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        assert all((values[j]*factorial(j))*d**j==h*x**j for j in range(N+1))


def test_head_and_index_bound_cannot_be_omitted():
    # An empty recurrence says nothing about its head or its next term.
    d=x=1;N=0;h=3;values=[3,17]
    assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
    assert values[1]*d!=h*x and values[0]!=h+1


def test_complete_normalization_replays_with_one_new_induction():
    result=norm.prove_exp_recurrence_normalization()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==1
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_normalization_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=norm.prove_exp_recurrence_normalization();node=result.provenance['helper_bundle_indices']['AP035']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
