"""The explicit finite convergence budget is proved, including zero cutoff."""
from dataclasses import replace
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_budget as budget


def test_exact_finite_power_budget_contract():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=budget.frozen_log_exp_budget_target();binders,premises,conclusion=strip_target(target)
    assert binders==4 and len(premises)==3 and type(conclusion) is And
    assert len(budget.canonical(encode_formula(target)))==7921
    c=budget.source_contract()
    assert c['explicit_cutoff']=='N=18*r+2' and c['new_induction_count']==2
    assert c['three_actual_power_computations_required'] is c['positive_cancel_factor_proved'] is True
    assert c['large_ground_exponentials_materialized'] is c['fixed_approximation_program_changed'] is c['analytic_limit_claim'] is c['closes_IR072'] is False


def test_power_definition_dag_is_preserved():
    from sqrt2_power_positive_power_comparison import definition_registry
    registry=budget.definition_registry();seen=set();ids=set()
    assert registry==definition_registry() and len(registry)==6
    for name,spec in registry.items():
        assert set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert budget.source_contract()['new_definition_ids']==[]


def test_changed_power_cutoff_error_coefficient_or_missing_premise_rejected():
    source=budget.NAMED_SOURCE;registry=budget.definition_registry()
    for changed in (source.replace('18*r','r'),source.replace('9*a','18*a'),
                    source.replace('Pow(3,S(18*r),q) -> ',''),source.replace('Le(r,q)','Le(q,r)')):
        assert changed!=source
        with patch.object(budget,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            budget.frozen_log_exp_budget_target(_registry=registry)


def test_actual_power_and_order_endpoints_have_exact_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=budget.definition_registry();found=set()
    for pin in budget.ARCHIVES:
        rows=budget.read_mixed_archive(pin)
        for name,source in budget.ENDPOINT_SOURCES.items():
            if budget.ENDPOINT_OWNERS[name]!=pin['case']: continue
            target=encode_formula(parse_named(source,registry=registry))
            matches=[i for i,row in enumerate(rows) if row[1]==target]
            assert len(matches)==1 and rows[matches[0]][3];found.add(name)
    assert found==budget.ENDPOINT_SOURCES.keys()
    bad=dict(budget.COMPARISON_ARCHIVE);bad['sha256']='0'*64
    with pytest.raises(ValueError): budget.read_mixed_archive(bad)


def test_small_exact_models_include_zero_parameter_and_both_inductions():
    for n in range(65):
        assert (n+2)*2**n<=2*3**n and n+1<=3**n
    for r in range(5):
        N=18*r+2;a=2**N;p=3**N;q=3**(N-1)
        assert p and q and r*9*a<=p and r<=q
    assert 9*2**2>3**2  # N=2 would not suffice uniformly for r=1.


def test_tiny_linear_generator_rejects_larger_factors_and_false_equalities():
    from peano_lab.kernel.terms import Add,Mul,parse_term
    s=budget.Scope(variables=('n',),hypotheses=tuple(reversed(budget.LINEAR)))
    n=s.term('n');one=parse_term('1')
    with pytest.raises(ValueError): budget._linear_equal(s,Mul(parse_term('4'),n),Mul(parse_term('4'),n))
    with pytest.raises(ValueError): budget._linear_equal(s,n,Add(n,one))


def test_frozen_source_manifest_is_revalidated():
    pins=budget.log_exp_budget_source_pins();assert len(pins)==231
    assert pins[budget.COMPARISON_ARCHIVE['path']]['sha256']==budget.COMPARISON_ARCHIVE['sha256']
    with patch.object(budget,'SOURCE_CLOSURE_SHA256','0'*64),pytest.raises(ValueError): budget.log_exp_budget_source_pins()


def test_solver_observer_uses_the_exact_frozen_arithmetic_helpers():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    registry=budget.definition_registry()
    for helper in ('step','budget'):
        target,digest,pins=observer.target_for('AP033-'+helper)
        assert target==parse_named(budget.HELPER_SOURCES[helper],registry=registry)
        assert digest==budget.HELPER_TARGET_SHA256[helper] and pins()==budget.log_exp_budget_source_pins()


def test_complete_power_budget_replays_with_exactly_two_new_inductions():
    result=budget.prove_log_exp_budget()
    assert result.receipt.target==result.target and result.provenance['new_induction_count']==2
    assert result.provenance['new_axioms']==[] and result.provenance['independent_lean_checked'] is False


def test_forged_bernoulli_induction_and_false_target_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result=budget.prove_log_exp_budget();node=result.provenance['helper_bundle_indices']['bernoulli']
    forged=replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero())) if n.node_id==node else n for n in result.bundle.nodes))
    with pytest.raises(ProofBundleError): check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError): check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
