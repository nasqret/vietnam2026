"""Both dyadic errors refer to the same actual finite log/exponential sum."""
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_dyadic_witness as witness


def test_exact_unconditional_dyadic_witness_and_every_exported_field():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_log_exp_dyadic_witness_target(_registry=registry)
    binders,premises,conclusion=strip_target(target)
    assert binders==1 and not premises and type(conclusion) is Exists
    assert len(witness.canonical(encode_formula(target)))==11021 and len(witness.OUTPUTS)==10 and len(witness.PARTS)==15
    for _ in witness.OUTPUTS:
        assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(14):
        assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(('n',)+witness.OUTPUTS))
    assert fields==[parse_named(source,names,registry) for source in witness.PARTS]
    c=witness.source_contract()
    assert c['actual_r_equals_two_to_n_constructed'] is c['all_logarithm_and_exponential_computations_constructed'] is True
    assert c['positive_input_output_and_dyadic_denominators_proved'] is c['comparison_powers_cancelled_only_after_nonzero_proof'] is True
    assert c['fixed_approximation_program_changed'] is c['analytic_logarithm_identity'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_existing_definition_dag_is_unchanged():
    from sqrt2_power_log_exp_witness import definition_registry
    registry=witness.definition_registry();seen=set();ids=set()
    assert registry==definition_registry() and len(registry)==53
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_precision_degree_table_or_error_is_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('Pow(2,n,r)','Pow(3,n,r)'),source.replace('18*r','r'),
                    source.replace('BetaAt(tb,tc,0,h)','BetaAt(tc,tb,0,h)'),
                    source.replace('Le(r*y,(r*2)*h+h)','Le(r*y,(r*2)*h)'),source.replace('~h=0','h=0')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            witness.frozen_log_exp_dyadic_witness_target(_registry=registry)


def test_actual_construction_and_budget_archives_are_retained():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry()
    for name,pin in (('witness',witness.WITNESS_ARCHIVE),('budget',witness.BUDGET_ARCHIVE)):
        rows=witness.read_mixed_archive(pin);target=encode_formula(parse_named(witness.ENDPOINT_SOURCES[name],registry=registry))
        assert rows[pin['root']][1]==target and rows[pin['root']][3]
        bad=dict(pin);bad['sha256']='0'*64
        with pytest.raises(ValueError): witness.read_mixed_archive(bad)


def test_exact_small_finite_series_have_the_stated_dyadic_error():
    from fractions import Fraction
    from math import factorial
    for n in (0,1):
        r=2**n;N=18*r+2
        argument=sum((Fraction(2,i*3**i) for i in range(1,N,2)),Fraction(0))
        value=sum((argument**j/factorial(j) for j in range(N+1)),Fraction(0))
        assert 0<=argument<=1 and abs(value-2)<=Fraction(1,r)
        y,h=value.numerator,value.denominator
        assert r*y<=(r*2)*h+h and (r*2)*h<=r*y+h


def test_positive_comparison_denominator_guard_is_substantive():
    r,y,h,p,a=1,1,0,0,0
    assert r*(9*a)<=p and y*p<=(2*p+9*a)*h
    assert not r*y<=(r*2)*h+h
    pins=witness.log_exp_dyadic_witness_source_pins()
    assert pins[witness.WITNESS_ARCHIVE['path']]['sha256']==witness.WITNESS_ARCHIVE['sha256']
    assert pins[witness.BUDGET_ARCHIVE['path']]['sha256']==witness.BUDGET_ARCHIVE['sha256']


def test_complete_dyadic_witness_replays_without_new_induction():
    result=witness.prove_log_exp_dyadic_witness()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==0
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_root_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_log_exp_dyadic_witness()
    check_forged_root_rejection(result.bundle)
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
