"""Actual all-precision half-logarithm/root witness, without an analytic axiom."""
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_root_witness as construction


def test_exact_unconditional_target_retains_every_computation_and_error():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=construction.definition_registry();target=construction.frozen_half_log_root_witness_target(_registry=registry)
    n,premises,conclusion=strip_target(target)
    assert n==1 and not premises and type(conclusion) is Exists
    assert len(construction.canonical(encode_formula(target)))==28913
    assert len(construction.OUTPUTS)==16 and len(construction.PARTS)==25
    for _ in construction.OUTPUTS:
        assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(24):
        assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(('n',)+construction.OUTPUTS))
    assert fields==[parse_named(part,names,registry) for part in construction.PARTS]
    c=construction.source_contract()
    assert c['actual_half_log_and_same_precision_dyadic_root_constructed'] is True
    assert c['analytic_half_log_sqrt2_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_nineteen_existing_definitions_are_shared_without_new_admissions():
    registry=construction.definition_registry();half=construction.half_registry();roots=construction.dyadic_registry()
    assert len(registry)==19 and all(registry[name]==spec for name,spec in half.items())
    assert registry['FloorSqrt']==roots['FloorSqrt'] and registry['DyadicSqrt2']==roots['DyadicSqrt2']
    seen=set();ids=set()
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert construction.source_contract()['new_definition_ids']==[]


def test_changed_root_precision_denominator_half_computation_or_error_rejected():
    source=construction.NAMED_SOURCE
    for changed in (source.replace('DyadicSqrt2(n,r,s)','DyadicSqrt2(S n,r,s)'),
                    source.replace('DyadicSqrt2(n,r,s)','DyadicSqrt2(n,d,s)'),
                    source.replace('2*(d*q)','d*q'),source.replace('~h=0','h=0'),
                    source.replace('7*(h*r)','(h*r)'),source.replace('r*(u*r)+(h*r)','r*(u*r)')):
        assert changed!=source
        with patch.object(construction,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            construction.frozen_half_log_root_witness_target()


def test_small_exact_rational_models_compare_actual_finite_programs():
    from fractions import Fraction
    from math import factorial,isqrt
    for n in (0,1):
        r=2**n;M=18*r+2;s=isqrt(2*r*r)
        log=sum((Fraction(2,j*3**j) for j in range(1,M,2)),Fraction(0))
        half=sum(((log/2)**j/factorial(j) for j in range(M+1)),Fraction(0))
        u,h=half.numerator,half.denominator
        assert s*s<=2*r*r<(s+1)**2 and r>0 and h>0
        assert r*u*r<=r*s*h+7*h*r and r*s*h<=r*u*r+h*r
        assert -Fraction(1,r)<=half-Fraction(s,r)<=Fraction(7,r)


def test_all_five_actual_endpoint_bodies_have_exact_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=construction.definition_registry();found={}
    for pin in construction.ARCHIVES:
        rows=construction.read_mixed_archive(pin)
        for name,source in construction.ENDPOINT_SOURCES.items():
            if construction.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found=={'half':('AP047',534),'comparison':('AP049',37),'square':('SQ009',52),
        'floor_exists':('SQ001',28),'le_refl':('CV071',13)}
    with pytest.raises(ValueError):construction.read_mixed_archive(dict(construction.HALF_ARCHIVE,sha256='0'*64))


def test_all_actual_source_and_archive_bytes_are_pinned():
    pins=construction.half_log_root_witness_source_pins()
    assert len(pins)==343
    for pin in construction.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_ordinary_witness_certificate_has_no_new_induction():
    result=construction.prove_half_log_root_witness()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_local_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=construction.prove_half_log_root_witness()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
