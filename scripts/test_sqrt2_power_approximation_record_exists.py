"""Genuine decoded record construction, conservative DAG and forged-body guards."""
from dataclasses import replace
from math import factorial,prod,gcd
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_record_exists as record


def test_exact_total_record_contract_keeps_all_fields_and_the_fixed_shift():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=record.frozen_approximation_record_exists_target();binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises
    count=0
    while type(conclusion) is Exists:
        count+=1;conclusion=conclusion.body
    assert count==17 and len(record.INTERNAL)==13 and len(record.RECORD_FIELDS)==15
    assert len(record.canonical(encode_formula(target)))==25791
    assert record.RECORD_FIELDS[11]=='ud' and record.RECORD_FIELDS[14]=='up'
    assert len(set(record.RECORD_FIELDS))==15
    for i,name in enumerate(record.RECORD_FIELDS):
        assert f'BetaAt(rb,rc,{i},{name})' in record.DEFINITION_SOURCE
    c=record.source_contract()
    assert c['record_code_components']==2 and c['fixed_precision_shift']==8
    assert c['all_fifteen_decoded_fields_consumed'] is c['no_opaque_unused_trace'] is True
    assert c['accuracy_is_definition_clause'] is c['beta_code_number_canonicality_claim'] is c['single_natural_record_packing_claim'] is c['canonical_PR_approximation_algorithm_claim'] is c['closes_IR072'] is False


def test_new_definition_is_a_hygienic_conservative_leaf_over_the_sample_dag():
    from sqrt2_power_exp_sample import definition_registry
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import parse_formula_in_context
    registry=record.definition_registry();original=definition_registry();seen=set();ids=set()
    assert len(registry)==24
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        if name in original:
            assert spec==original[name]
        seen.add(name);ids.add(spec.stable_id)
    spec=registry[record.DEFINITION_NAME]
    assert spec.stable_id=='ND0449' and spec.parameters==record.DEFINITION_PARAMETERS
    assert spec.template_formula==parse_named(record.DEFINITION_SOURCE,record.DEFINITION_PARAMETERS,original)
    assert spec.template_formula==parse_formula_in_context(spec.template_source,list(spec.parameters))
    assert spec.conceptual_dependencies==('BetaAt','Factorial','NatSqrt2ExpSample')


def test_missing_field_wrong_shift_and_shadowed_definition_are_rejected():
    source=record.DEFINITION_SOURCE
    for changed in (source.replace('n+8','n+7'),source.replace('BetaAt(rb,rc,14,up)','BetaAt(rb,rc,14,ud)'),
                    source.replace('~ud=0','ud=0'),source.replace('~D=0','D=0')):
        assert changed!=source
        with patch.object(record,'DEFINITION_SOURCE',changed),pytest.raises(ValueError):
            record.definition_registry()
    with patch.object(record,'DEFINITION_ID','ND0448'),pytest.raises(ValueError):
        record.definition_registry()


def test_actual_positive_sample_and_prefix_extension_bodies_are_required():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=record.definition_registry();found=set()
    for pin in record.ARCHIVES:
        rows=record.read_mixed_archive(pin)
        for name,source in record.ENDPOINT_SOURCES.items():
            if record.ENDPOINT_OWNERS[name]!=pin['case']:
                continue
            matches=[r for r in rows if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
        bad=dict(pin);bad['sha256']='0'*64
        with pytest.raises(ValueError):
            record.read_mixed_archive(bad)
    assert found==record.ENDPOINT_SOURCES.keys()


def test_small_actual_beta_encodings_retain_all_fifteen_ordered_fields():
    # CRT calibration of finite tuple semantics, not proof authority.
    for length in range(1,16):
        values=tuple((i*i+3*i)%17 for i in range(length))
        c=factorial(length)*(max(values)+1)
        moduli=tuple(1+(i+1)*c for i in range(length));M=prod(moduli)
        assert all(gcd(moduli[i],moduli[j])==1 for i in range(length) for j in range(i))
        b=sum(value*(M//modulus)*pow(M//modulus,-1,modulus) for value,modulus in zip(values,moduli))%M
        decoded=tuple(b%modulus for modulus in moduli)
        assert decoded==values and b.bit_length()<1024
        for i in range(length):
            assert decoded[i]!=values[i]+1


def test_fixed_tuple_constructor_and_order_bounds_reject_out_of_range_requests():
    for length in (0,16):
        with pytest.raises(ValueError):
            record.tuple_source(tuple('v'+str(i) for i in range(length)))
    for index,length in ((0,0),(2,2),(-1,2),(0,15)):
        with pytest.raises(ValueError):
            record._small_bound(record.Scope(),index,length)
    assert len(record.HELPER_SOURCES)==15 and record.source_contract()['new_fixed_tuple_prefix_steps']==15


def test_complete_record_construction_replays_without_new_induction():
    result=record.prove_approximation_record_exists()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_forged_final_tuple_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=record.prove_approximation_record_exists();node=result.provenance['helper_bundle_indices']['tuple_15']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
