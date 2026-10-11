"""Same-precision rational independence retains both actual record premises."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_record_independence as independence


def test_exact_two_record_rational_independence_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=independence.frozen_approximation_record_independence_target();binders,premises,conclusion=strip_target(target)
    assert binders==9 and len(premises)==2 and type(conclusion) is And
    assert len(independence.canonical(encode_formula(target)))==51751
    c=independence.source_contract()
    assert c['both_actual_records_required'] is c['common_precision_required'] is True
    assert c['both_output_denominators_proved_nonzero'] is c['actual_AP005_body_replayed'] is True
    assert c['rational_output_equality']=='vd*up=ud*vp'
    assert c['beta_code_number_equality_claim'] is c['canonical_PR_approximation_algorithm_claim'] is c['analytic_identity_claim'] is c['closes_IR072'] is False


def test_record_definition_dag_is_unchanged():
    from sqrt2_power_approximation_record_exists import definition_registry
    registry=independence.definition_registry();original=definition_registry();seen=set();ids=set()
    assert dict(registry)==dict(original) and len(registry)==24
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert independence.source_contract()['new_definition_ids']==[]


def test_changed_precision_missing_record_or_wrong_cross_products_are_rejected():
    source=independence.NAMED_SOURCE;registry=independence.definition_registry()
    for changed in (source.replace(independence.RIGHT+' -> ',''),
                    source.replace('NatSqrt2ApproxRecord(n,vp,vd,sb,sc)','NatSqrt2ApproxRecord(S n,vp,vd,sb,sc)'),
                    source.replace('vd*up=ud*vp','ud*up=vd*vp'),source.replace('~ud=0','ud=0')):
        assert changed!=source
        with patch.object(independence,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            independence.frozen_approximation_record_independence_target(_registry=registry)


def test_exact_sample_independence_body_is_replayed_not_an_authority_handle():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    pin=independence.INDEPENDENCE_ARCHIVE;rows=independence.read_mixed_archive(pin)
    target=encode_formula(parse_named(independence.INDEPENDENCE_SOURCE,registry=independence.definition_registry()))
    matches=[i for i,row in enumerate(rows) if row[1]==target]
    assert matches==[227] and rows[227][3]
    bad=dict(pin);bad['sha256']='0'*64
    with pytest.raises(ValueError):
        independence.read_mixed_archive(bad)


def test_actual_same_precision_records_allow_unequal_code_numbers():
    from test_sqrt2_power_approximation_record_decision import _sample_values,_encode,_record_holds
    values=_sample_values(8);rb,rc,M=_encode(values);up=values[14];ud=values[11]
    sb,sc=rb+M,rc;vp,vd=up,ud
    assert rb!=sb and _record_holds(0,up,ud,rb,rc) and _record_holds(0,vp,vd,sb,sc)
    assert ud!=0 and vd!=0 and vd*up==ud*vp
    assert not _record_holds(0,vp+1,vd,sb,sc) and vd*up!=ud*(vp+1)


def test_complete_record_independence_replays_without_new_induction():
    result=independence.prove_approximation_record_independence()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_forged_record_wrapper_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=independence.prove_approximation_record_independence();node=result.provenance['helper_bundle_indices']['AP030']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
