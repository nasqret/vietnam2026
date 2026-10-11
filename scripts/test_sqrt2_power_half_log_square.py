"""Actual half-logarithm computation with a finite square-error certificate."""
from unittest.mock import patch

import pytest
import sqrt2_power_half_log_square as witness


def test_exact_unconditional_witness_and_every_computation_field():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_half_log_square_target(_registry=registry)
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(witness.canonical(encode_formula(target)))==26429 and len(witness.OUTPUTS)==15 and len(witness.PARTS)==22
    for _ in witness.OUTPUTS:
        assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(21):
        assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(('n',)+witness.OUTPUTS))
    assert fields==[parse_named(source,names,registry) for source in witness.PARTS]
    c=witness.source_contract()
    assert c['actual_logarithm_and_half_exponential_computations_constructed'] is True
    assert c['proved_positive_scales']==['r','d','q','d*q','h']
    assert c['sqrt2_identification'] is c['analytic_exponential_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_seventeen_existing_definitions_form_the_exact_dependency_cone():
    registry=witness.definition_registry();pool=witness.source_registry();seen=set();ids=set()
    assert len(registry)==17
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_half_argument_precision_sum_or_square_error_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('Pow(2,n,r)','Pow(3,n,r)'),source.replace('2*(d*q)','d*q'),
                    source.replace('18*r','r'),source.replace('~h=0','h=0'),
                    source.replace('BetaAt(ab,ac,0,h)','BetaAt(ac,ab,0,h)'),
                    source.replace('+3*(h*h)',''),source.replace('h=f*t','h=f*q')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            witness.frozen_half_log_square_target(_registry=registry)


def test_all_actual_log_half_error_and_precision_roots_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();found={}
    for pin in witness.ARCHIVES:
        rows=witness.read_mixed_archive(pin)
        for name,source in witness.ENDPOINT_SOURCES.items():
            if witness.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found=={'log_witness':('AP034',451),'half_square':('AP044',302),
        'error_transfer':('AP045',27),'precision':('AP046',36),'power_exists':('AP010',110)}
    bad=dict(witness.LOG_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): witness.read_mixed_archive(bad)


def test_small_exact_rational_models_obey_both_square_errors():
    from fractions import Fraction
    from math import factorial
    for n in (0,1):
        r=2**n;M=18*r+2
        argument=sum((Fraction(2,j*3**j) for j in range(1,M,2)),Fraction(0))
        half=sum(((argument/2)**j/factorial(j) for j in range(M+1)),Fraction(0))
        assert 0<argument<=1 and half>=1
        assert 2-Fraction(1,r)<=half*half<=2+Fraction(3,r)
        u,h=half.numerator,half.denominator
        assert r*u*u<=(r*2)*h*h+3*h*h and (r*2)*h*h<=r*u*u+h*h
        assert half*half!=2  # A finite approximation is not the algebraic identity.


def test_all_exact_parent_source_and_archive_pins_are_rechecked():
    pins=witness.half_log_square_source_pins()
    assert len(pins)==337
    original=witness.recursive_source_pins_for_audit()
    assert {k:v for k,v in pins.items() if k!=witness.INPUT_SNAPSHOT}==original
    for archive in witness.ARCHIVES:
        assert pins[archive['path']]['sha256']==archive['sha256']
    with patch.object(witness,'LOG_ARCHIVE',dict(witness.LOG_ARCHIVE,sha256='0'*64)):
        # Read the changed pin itself; the archive tuple intentionally remains immutable.
        with pytest.raises(ValueError): witness.read_mixed_archive(witness.LOG_ARCHIVE)


def test_complete_half_log_square_replays_without_new_induction():
    result=witness.prove_half_log_square()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False
    # The protocol repair changes no theorem target, proof constructor or row.
    assert witness.sha256(result.payload.encode()).hexdigest()=='bcfc3286e107e3bdd1183f92793abd07c53a65c28f685c9f8f147cde6b08dc08'


def test_forged_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_half_log_square()
    check_forged_root_rejection(result.bundle)
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())


def test_changed_definition_snapshot_is_rejected_before_parsing():
    with patch.object(witness,'INPUT_SNAPSHOT_SHA256','0'*64):
        with pytest.raises(ValueError): witness.definition_registry()
        with pytest.raises(ValueError): witness.half_log_square_source_pins()
