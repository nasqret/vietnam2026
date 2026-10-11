"""Finite record error retains both computations and the actual dyadic scale."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_approximation_record_error as error


def test_exact_two_record_error_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=error.frozen_approximation_record_error_target();binders,premises,conclusion=strip_target(target)
    assert binders==10 and len(premises)==2 and type(conclusion) is Exists
    assert len(error.canonical(encode_formula(target)))==54415 and len(error.PARTS)==6
    c=error.source_contract()
    assert c['both_actual_records_required'] is c['all_precisions_and_finer_increments_including_zero'] is True
    assert c['actual_power_two_to_n_constructed'] is c['all_three_denominators_proved_nonzero'] is True
    assert c['fixed_shift_alignment_proved'] is c['actual_AP015_body_replayed'] is True
    assert c['canonical_PR_approximation_algorithm_claim'] is c['analytic_identity_claim'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_record_definition_dag_is_unchanged():
    from sqrt2_power_approximation_record_exists import definition_registry
    registry=error.definition_registry();original=definition_registry();seen=set();ids=set()
    assert dict(registry)==dict(original) and len(registry)==24
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert error.source_contract()['new_definition_ids']==[]


def test_changed_precision_missing_record_wrong_power_or_bound_are_rejected():
    source=error.NAMED_SOURCE;registry=error.definition_registry()
    for changed in (source.replace(error.RIGHT+' -> ',''),
                    source.replace('NatSqrt2ApproxRecord(n+l,vp,vd,sb,sc)','NatSqrt2ApproxRecord(n,vp,vd,sb,sc)'),
                    source.replace('Pow(2,n,r)','Pow(2,l,r)'),source.replace('+(ud*vd)','+ud'),
                    source.replace('~vd=0','vd=0')):
        assert changed!=source
        with patch.object(error,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            error.frozen_approximation_record_error_target(_registry=registry)


def test_exact_finite_error_body_is_replayed_not_an_authority_handle():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    pin=error.ERROR_ARCHIVE;rows=error.read_mixed_archive(pin)
    target=encode_formula(parse_named(error.ERROR_SOURCE,registry=error.definition_registry()))
    matches=[i for i,row in enumerate(rows) if row[1]==target]
    assert matches==[302] and rows[302][3]
    bad=dict(pin);bad['sha256']='0'*64
    with pytest.raises(ValueError):
        error.read_mixed_archive(bad)


def test_flat_source_closure_revalidates_actual_bytes_and_rejects_changed_manifest():
    pins=error.approximation_record_error_source_pins()
    assert len(pins)==272 and pins[error.ERROR_ARCHIVE['path']]['sha256']==error.ERROR_ARCHIVE['sha256']
    assert pins['scripts/sqrt2_power_approximation_record_exists.py']['sha256']=='a6a83ae09292398d9a690753164840f581d9e3b43aa7c5475d6514c917cb911a'
    with patch.object(error,'SOURCE_CLOSURE_SHA256','0'*64),pytest.raises(ValueError):
        error.approximation_record_error_source_pins()


def test_actual_equal_and_finer_records_satisfy_both_integer_bounds():
    from test_sqrt2_power_approximation_record_decision import _sample_values,_encode,_record_holds
    first=_sample_values(8);rb,rc,_=_encode(first);up=first[14];ud=first[11]
    assert _record_holds(0,up,ud,rb,rc)
    for l in (0,1):
        second=_sample_values(8+l);sb,sc,_=_encode(second);vp=second[14];vd=second[11];r=1
        assert _record_holds(l,vp,vd,sb,sc)
        assert r and ud and vd and r*ud*vp<=r*vd*up+ud*vd and r*vd*up<=r*ud*vp+ud*vd
        assert not _record_holds(l,vp+1,vd,sb,sc)


def test_complete_record_error_replays_without_new_induction():
    result=error.prove_approximation_record_error()
    assert result.receipt.target==result.target
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_forged_precision_alignment_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=error.prove_approximation_record_error();node=result.provenance['helper_bundle_indices']['precision']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError):
        check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
