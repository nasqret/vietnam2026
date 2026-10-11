"""Finite comparison of supplied half-log and dyadic root square bounds."""
from itertools import product
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_root_comparison as comparison


def test_exact_asymmetric_error_and_all_eight_supplied_bounds():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=comparison.frozen_half_log_root_comparison_target()
    n,premises,conclusion=strip_target(target)
    assert n==5 and len(premises)==8 and type(conclusion) is And
    assert len(comparison.canonical(encode_formula(target)))==1514
    c=comparison.source_contract()
    assert c['positive_denominators']==['h','d'] and c['precision_order']=='r<=d'
    assert c['supplied_witnesses_not_constructed'] is True
    assert c['analytic_half_log_sqrt2_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_only_existing_order_not_a_root_identity_definition():
    registry=comparison.definition_registry()
    assert tuple(registry)==('Le',) and not registry['Le'].conceptual_dependencies
    assert comparison.source_contract()['new_definition_ids']==[]


def test_changed_precision_guard_half_square_or_cross_error_is_rejected():
    source=comparison.NAMED_SOURCE
    for changed in (source.replace('~h=0','h=0'),source.replace('Le(r,d)','Le(d,r)'),
                    source.replace('Le(d,s)','Le(s,d)'),source.replace('r*(u*u)','r*u'),
                    source.replace('7*(h*d)','3*(h*d)'),source.replace('r*(u*d)+(h*d)','r*(u*d)')):
        assert changed!=source
        with patch.object(comparison,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            comparison.frozen_half_log_root_comparison_target()


def test_finite_models_include_zero_r_and_both_comparison_directions():
    accepted=0;directions=set();r_zero=False
    for r,u,h,s,d in product(range(5),range(10),range(1,5),range(14),range(1,7)):
        if not (r<=d<=s and s*s<=2*d*d<=s*s+4*d and r*u*u<=2*r*h*h+3*h*h and 2*r*h*h<=r*u*u+h*h):continue
        assert r*u*d<=r*s*h+7*h*d and r*s*h<=r*u*d+h*d
        accepted+=1;r_zero|=r==0;directions.add((u*d>s*h)-(u*d<s*h))
    assert accepted>100 and r_zero and directions=={-1,0,1}


def test_actual_linear_and_positive_product_endpoints_are_present():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=comparison.definition_registry();found={}
    for pin in comparison.ARCHIVES:
        rows=comparison.read_mixed_archive(pin)
        for name,source in comparison.ENDPOINT_SOURCES.items():
            if comparison.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==13 and found['linear']==('AP048',30) and found['mul_ne_zero']==('CV071',45)
    with pytest.raises(ValueError):comparison.read_mixed_archive(dict(comparison.LINEAR_ARCHIVE,sha256='0'*64))


def test_actual_source_and_archive_bytes_are_pinned():
    pins=comparison.half_log_root_comparison_source_pins()
    assert len(pins)==340
    for pin in comparison.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_ordinary_certificate_without_new_induction():
    result=comparison.prove_half_log_root_comparison()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_local_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=comparison.prove_half_log_root_comparison()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
