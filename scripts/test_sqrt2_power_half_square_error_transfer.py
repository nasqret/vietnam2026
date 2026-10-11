"""Positive cancellation and precision ordering in finite square-error algebra."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_half_square_error_transfer as error


def test_exact_error_transfer_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=error.frozen_half_square_error_transfer_target();binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==7 and type(conclusion) is And
    assert len(error.canonical(encode_formula(target)))==1184
    c=error.source_contract()
    assert c['positive_cancellation_factors']==['b','p'] and c['precision_order']=='r<=p'
    assert c['upper_error_coefficient']==3 and c['lower_error_coefficient']==1
    assert c['square_or_exponential_construction_claimed'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_only_existing_natural_order_definition_is_used():
    registry=error.definition_registry();pool=error.source_registry()
    assert tuple(registry)==('Le',) and registry['Le']==pool['Le']
    assert registry['Le'].conceptual_dependencies==()
    assert error.source_contract()['new_definition_ids']==[]


def test_changed_error_allowance_guards_or_precision_rejected():
    source=error.NAMED_SOURCE;registry=error.definition_registry()
    for changed in (source.replace('~b=0 -> ',''),source.replace('~p=0 -> ',''),source.replace('Le(r,p) -> ',''),
                    source.replace('3*a','2*a'),source.replace('Le((r*2)*a,r*s+a)','Le((r*2)*a,r*s)'),
                    source.replace('Le(a*v,b*s) -> ','')):
        assert changed!=source
        with patch.object(error,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            error.frozen_half_square_error_transfer_target(_registry=registry)


def test_all_helpers_and_actual_positive_cancellation_body_match():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=error.definition_registry();rows=error.read_mixed_archive(error.BOUND_ARCHIVE)
    assert {k:error.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in error.HELPER_SOURCES.items()}==error.HELPER_TARGET_SHA256
    for name,source in error.ENDPOINT_SOURCES.items():
        ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
        assert len(matches)==1 and rows[matches[0]][3]
        if name=='mul_le_cancel': assert matches==[151]
    bad=dict(error.BOUND_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): error.read_mixed_archive(bad)


def test_exhaustive_small_natural_models_include_zero_scales():
    accepted=0
    for p in range(1,5):
        for r in range(p+1):
            for b in range(1,4):
                for a in range(4):
                    for s in range(10):
                        for v in range(8):
                            if a*v<=b*s and p*(b*s)<=p*(a*v)+2*b*a and r*v<=2*r*b+b and 2*r*b<=r*v+b:
                                accepted+=1
                                assert r*s<=2*r*a+3*a and 2*r*a<=r*s+a
    assert accepted>100


def test_zero_cancelled_head_and_missing_precision_order_have_counterexamples():
    r,p,b,a,s,v=1,1,0,1,100,0
    assert r<=p and a*v<=b*s and p*b*s<=p*a*v+2*b*a and r*v<=2*r*b+b and 2*r*b<=r*v+b
    assert r*s>2*r*a+3*a
    r,p,b,a,s,v=3,1,1,1,4,2
    assert a*v<=b*s and p*b*s<=p*a*v+2*b*a and r*v<=2*r*b+b and 2*r*b<=r*v+b
    assert r>p and r*s>2*r*a+3*a


def test_precision_weakening_models_preserve_the_same_absolute_allowance():
    for p in range(1,6):
        for r in range(p+1):
            for s in range(8):
                for t in range(8):
                    for e in range(4):
                        if p*s<=p*t+2*e:
                            assert r*s<=r*t+2*e


def test_complete_error_transfer_replays_without_new_induction():
    result=error.prove_half_square_error_transfer()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_precision_weakening_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=error.prove_half_square_error_transfer();node=result.provenance['helper_bundle_indices']['weaken']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
