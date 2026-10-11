"""A local, denominator-cleared coefficient shift from actual finite sums."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_convolution_shift as shift


def test_exact_coefficient_shift_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Eq
    from peano_lab.library.proof_bundle import encode_formula
    target=shift.frozen_convolution_shift_target();binders,premises,conclusion=strip_target(target)
    assert binders==14 and len(premises)==4 and type(conclusion) is Eq
    assert len(shift.canonical(encode_formula(target)))==6986
    c=shift.source_contract()
    assert c['actual_supplied_coefficients_and_padded_inputs_preserved'] is c['proved_zero_shifted_head_required'] is True
    assert c['only_indices_through_coefficient_required'] is c['arbitrary_input_lengths_and_zero_scalars_allowed'] is True
    assert c['analytic_exponential_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_eleven_definitions_are_hygienic_and_topological():
    registry=shift.definition_registry();pool=shift.source_registry();seen=set();ids=set()
    assert len(registry)==11
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert shift.source_contract()['new_definition_ids']==[]


def test_changed_zero_head_local_relation_or_shifted_index_rejected():
    source=shift.NAMED_SOURCE;registry=shift.definition_registry()
    for changed in (source.replace(shift.HEAD+' -> ',''),source.replace('Le(j,i)','Lt(j,i)'),
                    source.replace('gamma*c=alpha*a','gamma*a=alpha*c'),
                    source.replace('M,S i,v','M,i,v'),source.replace('gamma*v=alpha*u','gamma*u=alpha*v')):
        assert changed!=source
        with patch.object(shift,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            shift.frozen_convolution_shift_target(_registry=registry)


def test_helpers_and_actual_owned_ancestor_rows_match_exact_asts():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=shift.definition_registry();found={}
    assert {k:shift.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in shift.HELPER_SOURCES.items()}==shift.HELPER_TARGET_SHA256
    for pin in shift.ARCHIVES:
        rows=shift.read_mixed_archive(pin)
        for name,source in shift.ENDPOINT_SOURCES.items():
            if shift.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['slice_sum_exists']==('CV008',114) and found['head_tail']==('CV010',129)
    bad=dict(shift.FUBINI_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): shift.read_mixed_archive(bad)


def _at(values,j):
    return values[j] if j<len(values) else 0


def _coefficient(a,b,i):
    return sum(_at(a,j)*_at(b,i-j) for j in range(i+1))


def test_exact_models_allow_arbitrary_lengths_zero_scalars_and_unrelated_high_tail():
    for L in range(5):
        base=list(range(1,L+1))
        for M in range(4):
            b=list(range(2,M+2))
            for i in range(7):
                for alpha in (0,1,3):
                    for gamma in (0,1,2):
                        a=[gamma*v for v in base]
                        c=[0]+[alpha*_at(base,j) for j in range(i+1)]+[99,17]
                        assert all(gamma*_at(c,j+1)==alpha*_at(a,j) for j in range(i+1))
                        assert gamma*_coefficient(c,b,i+1)==alpha*_coefficient(a,b,i)
    assert _coefficient([],[],0)==_coefficient([],[],7)==0


def test_shifted_sum_models_include_empty_length_and_zero_scalars():
    for N in range(8):
        for alpha,gamma in ((0,0),(0,2),(3,0),(3,2)):
            base=list(range(1,N+1));a=[gamma*x for x in base];b=[0]+[alpha*x for x in base]
            assert gamma*sum(b)==alpha*sum(a)


def test_zero_head_and_inclusive_local_endpoint_cannot_be_dropped():
    # With a nonzero head, an extra head*B[i+1] contribution survives.
    assert _coefficient([1,0],[0,1],1)!=_coefficient([0],[0,1],0)
    # At i=0 a strict j<i premise is vacuous and loses the required first shift.
    assert _coefficient([0,7],[1],1)!=_coefficient([2],[1],0)


def test_complete_convolution_shift_replays_without_new_induction():
    result=shift.prove_convolution_shift()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_shifted_sum_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=shift.prove_convolution_shift();node=result.provenance['helper_bundle_indices']['sum_shift']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
