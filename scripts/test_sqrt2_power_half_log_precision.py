"""Actual symbolic powers and a checked induction supply the precision budget."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_precision as precision


def test_exact_cutoff_precision_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=precision.frozen_half_log_precision_target();binders,premises,conclusion=strip_target(target)
    assert binders==2 and len(premises)==1 and type(conclusion) is And
    assert len(precision.canonical(encode_formula(target)))==2641
    c=precision.source_contract()
    assert c['actual_supplied_power_required'] is c['supplied_power_proved_nonzero'] is True
    assert c['generic_binary_growth']=='n+1<=2^n' and c['new_induction_count']==1
    assert c['large_ground_power_materialized'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_six_existing_power_definitions_remain_topological():
    registry=precision.definition_registry();seen=set();ids=set()
    assert len(registry)==6
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert precision.source_contract()['new_definition_ids']==[]


def test_changed_base_degree_power_or_order_rejected():
    source=precision.NAMED_SOURCE;registry=precision.definition_registry()
    for changed in (source.replace('Pow(2,','Pow(1,'),source.replace('18*r','r'),
                    source.replace('Pow(2,S(S(18*r)),p) -> ',''),source.replace('Le(r,p)','Le(p,r)'),
                    source.replace('~p=0','p=0')):
        assert changed!=source
        with patch.object(precision,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            precision.frozen_half_log_precision_target(_registry=registry)


def test_actual_power_descent_and_cutoff_bodies_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=precision.definition_registry();found={}
    assert {k:precision.json_hash(encode_formula(parse_named(v,registry=registry))) for k,v in precision.HELPER_SOURCES.items()}==precision.HELPER_TARGET_SHA256
    for pin in precision.ARCHIVES:
        rows=precision.read_mixed_archive(pin)
        for name,source in precision.ENDPOINT_SOURCES.items():
            if precision.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found['cutoff']==('AP033',43) and found['power_step']==('AP010',113)
    assert found['power_nonzero']==('AP010',120)
    bad=dict(precision.BUDGET_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): precision.read_mixed_archive(bad)


def test_small_actual_models_include_zero_scale_and_zero_exponent():
    for n in range(25):
        assert n+1<=2**n
        assert n+(n+2)==(n+1)*2
    for r in range(7):
        p=2**(18*r+2)
        assert p.bit_length()<=128 and p>0 and r<=p


def test_base_one_or_an_arbitrary_nonzero_value_cannot_replace_actual_power():
    assert not 3<=1**(18*3+2)
    assert not 3<=1
    assert not 0!=0


def test_complete_cutoff_certificate_replays_with_one_new_induction():
    result=precision.prove_half_log_precision()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==1
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_growth_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=precision.prove_half_log_precision();node=result.provenance['helper_bundle_indices']['growth']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
