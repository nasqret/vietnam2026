"""The constructed product prefix has its own exact head and normalization."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_exp_convolution_prefix as prefix


def test_exact_constructed_product_prefix_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=prefix.frozen_exp_convolution_prefix_target();binders,premises,conclusion=strip_target(target)
    assert binders==10 and len(premises)==4 and type(conclusion) is Exists
    assert len(prefix.canonical(encode_formula(target)))==12926
    c=prefix.source_contract()
    assert c['actual_convolution_prefix_and_sum_constructed'] is c['all_index_factorial_normalization_proved'] is True
    assert c['supplied_recurrences_and_heads_preserved'] is c['zero_denominator_arguments_heads_and_horizon_allowed'] is True
    assert c['truncated_output_sum_equals_product_of_input_sums'] is c['analytic_exponential_addition'] is c['closes_IR072'] is False


def test_fifteen_existing_definitions_preserve_their_exact_dag():
    registry=prefix.definition_registry();pool=prefix.source_registry();seen=set();ids=set()
    assert len(registry)==15
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert prefix.source_contract()['new_definition_ids']==[]


def test_changed_head_horizon_argument_or_normalization_rejected():
    source=prefix.NAMED_SOURCE;registry=prefix.definition_registry()
    for changed in (source.replace('a0*b0','a0+b0'),source.replace('Le(j,N)','Le(j,S N)'),
                    source.replace('x+y','x*y'),source.replace('Sum(cb,cc,S N,s)','Sum(cb,cc,N,s)'),
                    source.replace('BetaAt(bb,bc,0,b0) -> ','')):
        assert changed!=source
        with patch.object(prefix,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            prefix.frozen_exp_convolution_prefix_target(_registry=registry)


def test_helpers_and_actual_ancestor_bodies_have_exact_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=prefix.definition_registry();found={}
    assert {k:prefix.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in prefix.HELPER_SOURCES.items()}==prefix.HELPER_TARGET_SHA256
    for pin in prefix.ARCHIVES:
        rows=prefix.read_mixed_archive(pin)
        for name,source in prefix.ENDPOINT_SOURCES.items():
            if prefix.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['normalization']==('AP035',35) and found['coefficient_recurrence']==('AP038',146)
    assert found['prefix_exists']==('CV003',123) and found['sum_one']==('CV010',128)
    bad=dict(prefix.RECURRENCE_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): prefix.read_mixed_archive(bad)


def test_exact_product_prefix_models_include_zero_cases():
    from math import factorial
    for N in range(6):
        for d in (1,2,3):
            for x,y in ((0,0),(0,2),(1,1),(2,3)):
                for scale in (0,1,2):
                    a=[scale*(factorial(N)//factorial(j))*d**(N-j)*x**j for j in range(N+1)]
                    b=[(factorial(N)//factorial(j))*d**(N-j)*y**j for j in range(N+1)]
                    c=[sum(a[k]*b[j-k] for k in range(j+1)) for j in range(N+1)]
                    assert c[0]==a[0]*b[0]
                    assert all((j+1)*d*c[j+1]==(x+y)*c[j] for j in range(N))
                    assert all((c[j]*factorial(j))*d**j==(a[0]*b[0])*(x+y)**j for j in range(N+1))
        a=list(range(1,N+2));b=list(range(2,N+3));d=x=y=0
        c=[sum(a[k]*b[j-k] for k in range(j+1)) for j in range(N+1)]
        assert all((c[j]*factorial(j))*d**j==(a[0]*b[0])*(x+y)**j for j in range(N+1))


def test_truncated_output_sum_is_not_the_full_product_sum():
    a=b=[1,1];c=[1,2]
    assert sum(c)==3 and sum(a)*sum(b)==4
    assert prefix.source_contract()['truncated_output_sum_equals_product_of_input_sums'] is False


def test_complete_constructed_product_prefix_replays_without_new_induction():
    result=prefix.prove_exp_convolution_prefix()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_product_head_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=prefix.prove_exp_convolution_prefix();node=result.provenance['helper_bundle_indices']['head']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
