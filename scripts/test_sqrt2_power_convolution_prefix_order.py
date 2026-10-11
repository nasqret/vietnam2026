"""Only extending the same natural input codes guarantees coefficient order."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_convolution_prefix_order as order


def test_exact_same_code_prefix_order_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=order.frozen_convolution_prefix_order_target();binders,premises,conclusion=strip_target(target)
    assert binders==11 and len(premises)==4 and type(conclusion) is Exists
    assert len(order.canonical(encode_formula(target)))==5632
    c=order.source_contract()
    assert c['both_actual_input_beta_codes_preserved'] is c['both_input_length_orders_required'] is True
    assert c['arbitrary_coefficient_index'] is c['empty_input_lengths_and_equal_lengths_allowed'] is True
    assert c['quantitative_tail_bound'] is c['analytic_exponential_addition'] is c['closes_IR072'] is False


def test_nine_existing_definitions_have_exact_topological_dependencies():
    registry=order.definition_registry();pool=order.source_registry();seen=set();ids=set()
    assert len(registry)==9
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert order.source_contract()['new_definition_ids']==[]


def test_changed_length_premise_codes_or_order_rejected():
    source=order.NAMED_SOURCE;registry=order.definition_registry()
    for changed in (source.replace('Le(L,N) -> ',''),source.replace('Le(M,O)','Le(O,M)'),
                    source.replace('ab,ac,N','ac,ab,N'),source.replace('Le(u,v)','Le(v,u)')):
        assert changed!=source
        with patch.object(order,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            order.frozen_convolution_prefix_order_target(_registry=registry)


def test_actual_diagonal_order_and_sum_bound_proofs_match_owned_rows():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=order.definition_registry();found={}
    assert {k:order.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in order.HELPER_SOURCES.items()}==order.HELPER_TARGET_SHA256
    for pin in order.ARCHIVES:
        rows=order.read_mixed_archive(pin)
        for name,source in order.ENDPOINT_SOURCES.items():
            if order.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['sum_bound']==('CV095',25) and found['mul_left_mono']==('CV071',149)
    bad=dict(order.SUM_BOUND_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): order.read_mixed_archive(bad)


def _coefficient(a,L,b,M,i):
    return sum(a[j]*b[i-j] for j in range(L) if 0<=i-j<M)


def test_exact_models_cover_empty_equal_extended_and_high_degree_prefixes():
    for a,b in (([0]*8,[2]*8),([1,0,3,1,5,0,2,1],[0,2,1,0,3,1,1,4])):
        for L in range(5):
            for M in range(5):
                for N in range(L,8):
                    for O in range(M,8):
                        for i in range(15):
                            assert _coefficient(a,L,b,M,i)<=_coefficient(a,N,b,O,i)


def test_length_order_and_preserved_codes_are_necessary():
    assert _coefficient([3],1,[2],1,0)>_coefficient([3],0,[2],1,0)
    assert _coefficient([3],1,[2],1,0)>_coefficient([0],1,[2],1,0)
    assert _coefficient([3],1,[2],1,0)>_coefficient([3],1,[2],0,0)


def test_complete_prefix_order_replays_without_new_induction():
    result=order.prove_convolution_prefix_order()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_padded_order_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=order.prove_convolution_prefix_order();node=result.provenance['helper_bundle_indices']['padded_order']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
