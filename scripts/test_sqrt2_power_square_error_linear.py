"""Exact natural square-error conversion, ordinary bodies and hostile inputs."""
from itertools import product
from unittest.mock import patch

import pytest
import sqrt2_power_square_error_linear as arithmetic


def test_exact_two_sided_statement_has_both_square_errors_and_scale_guards():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=arithmetic.frozen_square_error_linear_target()
    n,premises,conclusion=strip_target(target)
    assert n==6 and len(premises)==4 and type(conclusion) is And
    assert len(arithmetic.canonical(encode_formula(target)))==841
    c=arithmetic.source_contract()
    assert c['positive_cancellation_factor']=='k' and c['scale_lower_bound']=='k<=x+y'
    assert c['allows_zero_r_x_y_a_b'] is True
    assert c['square_root_construction'] is c['analytic_identity_claim'] is c['closes_IR072'] is False


def test_only_the_existing_natural_order_definition_is_used():
    registry=arithmetic.definition_registry()
    assert tuple(registry)==('Le',)
    assert registry['Le']==arithmetic.source_registry()['Le']
    assert not registry['Le'].conceptual_dependencies
    assert arithmetic.source_contract()['new_definition_ids']==[]


def test_changed_guard_squared_factor_or_error_side_is_rejected():
    source=arithmetic.NAMED_SOURCE
    for changed in (source.replace('~k=0','k=0'),source.replace('Le(k,x+y)','Le(k,x)'),
                    source.replace('r*(x*x)','r*x'),source.replace('a*(k*k)','a*k'),
                    source.replace('r*y+a*k','r*y+b*k'),source.replace('r*x+b*k','r*x')):
        assert changed!=source
        with patch.object(arithmetic,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            arithmetic.frozen_square_error_linear_target()


def test_small_exact_natural_models_cover_both_order_branches_and_zero_cases():
    accepted=0;orders=set();zeros=set()
    for r,x,y,k,a,b in product(range(4),range(6),range(6),range(1,7),range(4),range(4)):
        if k<=x+y and r*x*x<=r*y*y+a*k*k and r*y*y<=r*x*x+b*k*k:
            assert r*x<=r*y+a*k and r*y<=r*x+b*k
            accepted+=1;orders.add((x>y)-(x<y))
            zeros.update(name for name,value in zip(('r','x','y','a','b'),(r,x,y,a,b)) if value==0)
    assert accepted>1000 and orders=={-1,0,1} and zeros=={'r','x','y','a','b'}


def test_actual_order_and_cancellation_bodies_have_exact_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=arithmetic.definition_registry();found={}
    for pin in arithmetic.ARCHIVES:
        rows=arithmetic.read_mixed_archive(pin)
        for name,source in arithmetic.ENDPOINT_SOURCES.items():
            if arithmetic.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry))
            matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3]
            found[name]=(pin['case'],matches[0])
    assert len(found)==14 and found['le_gap']==('AP007',157)
    assert found['cancel_order']==('AP007',158) and found['le_total']==('AP007',14)
    assert found['mul_le_cancel']==('CV071',151)
    bad=dict(arithmetic.CONTINUITY_ARCHIVE,sha256='0'*64)
    with pytest.raises(ValueError):arithmetic.read_mixed_archive(bad)


def test_all_source_and_archive_bytes_are_checked():
    pins=arithmetic.square_error_linear_source_pins()
    assert len(pins)==338
    for pin in arithmetic.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_ordinary_certificate_has_no_new_induction_or_axiom():
    result=arithmetic.prove_square_error_linear()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_local_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=arithmetic.prove_square_error_linear()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
