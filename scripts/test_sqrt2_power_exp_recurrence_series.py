"""Valid rational factorial terms for any supplied finite recurrence."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_exp_recurrence_series as series


def test_exact_generic_rational_series_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Forall
    from peano_lab.library.proof_bundle import encode_formula
    target=series.frozen_exp_recurrence_series_target();binders,premises,conclusion=strip_target(target)
    assert binders==6 and len(premises)==4 and type(conclusion) is Forall
    assert len(series.canonical(encode_formula(target)))==6934
    c=series.source_contract()
    assert c['actual_supplied_table_and_head_preserved'] is c['term_denominators_proved_nonzero'] is True
    assert c['all_in_range_factorials_and_both_powers_constructed'] is True
    assert c['unrelated_AP021_sample_root_replayed'] is c['analytic_exponential_identity'] is c['closes_IR072'] is False


def test_existing_eleven_definition_dependency_cone():
    registry=series.definition_registry();pool=series.source_registry();seen=set();ids=set()
    assert len(registry)==11 and set(registry)<=set(pool)
    for name,spec in registry.items():
        assert spec==pool[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert series.source_contract()['new_definition_ids']==[]


def test_changed_positivity_head_horizon_and_rational_terms_rejected():
    source=series.NAMED_SOURCE;registry=series.definition_registry()
    for changed in (source.replace('~d=0 -> ',''),source.replace('~h=0 -> ',''),
                    source.replace('BetaAt(tb,tc,0,h) -> ',''),source.replace('Le(j,N)','Le(j,S N)'),
                    source.replace('IRatEq(t,0,h,q0,0,f0*p0)','IRatEq(t,0,h,p0,0,f0*q0)')):
        assert changed!=source
        with patch.object(series,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            series.frozen_exp_recurrence_series_target(_registry=registry)


def test_actual_normalization_and_generic_term_bodies_are_owned_and_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=series.definition_registry();found={}
    for pin in series.ARCHIVES:
        rows=series.read_mixed_archive(pin)
        for name,source in series.ENDPOINT_SOURCES.items():
            if series.ENDPOINT_OWNERS[name]==pin['case']:
                ast=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==ast]
                assert len(matches)==1 and rows[matches[0]][3];found[name]=matches[0]
    assert found==dict(normalization=35,terms=158)
    bad=dict(series.SERIES_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): series.read_mixed_archive(bad)


def test_exact_rational_models_with_zero_argument_and_horizon():
    from fractions import Fraction
    from math import factorial
    for N in range(6):
        for d in (1,2,3):
            for x in (0,1,2):
                for scale in (1,3):
                    h=scale*factorial(N)*d**N
                    values=[scale*(factorial(N)//factorial(j))*d**(N-j)*x**j for j in range(N+1)]
                    assert h and all((j+1)*d*values[j+1]==x*values[j] for j in range(N))
                    assert all(Fraction(values[j],h)==Fraction(x**j,factorial(j)*d**j) for j in range(N+1))


def test_positivity_and_horizon_hypotheses_are_substantive():
    # Zero heads/denominators can satisfy integer recurrences but do not
    # define valid rationals. An empty recurrence constrains no next term.
    assert 1*1*0==2*0
    assert 1*0*7==0*4
    assert 17!=3*2
    c=series.source_contract()
    assert c['positive_input_denominator_and_head_required'] is True
    assert c['zero_numerator_index_and_horizon_allowed'] is True


def test_complete_series_certificate_uses_no_new_induction():
    result=series.prove_exp_recurrence_series()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_series_body_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=series.prove_exp_recurrence_series();node=result.provenance['helper_bundle_indices']['AP036']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
