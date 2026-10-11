"""The explicit modulus is symbolic, horizon-independent and two-sided."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_dyadic_continuity as continuity


def test_exact_requested_precision_retains_powers_and_both_error_directions():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(continuity.frozen_exp_dyadic_continuity_target())
    names=tuple(reversed(continuity.PARAMETERS));registry=continuity.definition_registry()
    assert n==18 and len(premises)==15 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in continuity.PREMISES]
    assert conclusion==parse_named(continuity.CONCLUSION,names,registry)
    c=continuity.source_contract()
    assert c['actual_majorant_power_constructed'] is c['both_dyadic_scales_proved_nonzero'] is c['uniform_in_finite_horizon'] is True
    assert c['argument_order_assumed'] is c['analytic_continuity_claimed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_twelve_existing_definitions_remain_hygienic_and_topologically_ordered():
    registry=continuity.definition_registry();source=continuity.source_registry();seen=set();ids=set()
    assert len(registry)==12 and 'Pow' in registry and 'NatScaledExpRecurrence' in registry
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()['new_definition_ids']==[]


def test_changed_precision_power_budget_or_error_is_rejected():
    source=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for changed in (source.replace('S(9*(S L)+n)','S(9*(S N)+n)'),source.replace('Pow(2,n,r)','Pow(2,L,r)'),
                    source.replace('Le(p*g,d*e)','Le(g,d*e)'),source.replace('Le(e*x,d*y+g)','Le(d*y,e*x+g)'),
                    source.replace('~e=0','e=0'),source.replace('r*(a0*t)+a0*b0','r*(a0*t)+a0')):
        assert changed!=source
        with patch.object(continuity,'NAMED_SOURCE',changed),pytest.raises(ValueError):continuity.frozen_exp_dyadic_continuity_target(_registry=registry)


def test_actual_dyadic_models_cover_large_denominators_both_orders_and_zero_heads():
    from math import factorial
    examples=0;strict_forward=0;strict_reverse=0;zeroheads=0
    for L in range(4):
        C=9**(L+1)
        for n in range(5):
            r=2**n;p=2**(9*(L+1)+n+1);d=2*p;e=3*p
            assert r>0 and p>0 and 2*r*C<=p
            candidates={(level*d,level*e+delta) for level in range(L+1) for delta in (-2,-1,0,1,2) if 0<=level*e+delta<=L*e}
            # At these denominators N<=1 keeps every model within 128 bits.
            # General N is discharged by the checked induction ancestry.
            for x,y in sorted(candidates):
                exact=abs(d*y-e*x)
                for g in (exact,exact+d):
                    assert p*g<=d*e and (r*g)*C<=d*e
                    for N in range(2):
                        for sa,sb in ((0,0),(0,1),(1,0),(1,1),(2,3)):
                            a=sa*factorial(N)*d**N;b=sb*factorial(N)*e**N
                            first=[a*x**j//(factorial(j)*d**j) for j in range(N+1)]
                            second=[b*y**j//(factorial(j)*e**j) for j in range(N+1)]
                            u,v=sum(first),sum(second)
                            assert first[0]==a and second[0]==b
                            assert all(((j+1)*d)*first[j+1]==x*first[j] and ((j+1)*e)*second[j+1]==y*second[j] for j in range(N))
                            assert r*(b*u)<=r*(a*v)+a*b and r*(a*v)<=r*(b*u)+a*b
                            assert max(r*(b*u)+a*b,r*(a*v)+a*b,p*g,d*e).bit_length()<=128
                            examples+=1;strict_forward+=d*y>e*x;strict_reverse+=d*y<e*x;zeroheads+=a==0 or b==0
    assert examples==3400 and strict_forward==strict_reverse==1200 and zeroheads==2040
    # A lost power-budget guard would make the arithmetic helper false.
    r,C,p,g,D=2,2,1,1,1
    assert not 2*(r*C)<=p and p*g<=D and not (r*g)*C<=D


def test_nine_endpoints_resolve_to_owned_actual_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found={}
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==9 and found['continuity']==('AP074',continuity.CONTINUITY_ARCHIVE['root'])
    assert found['budget']==('AP062',128) and found['power_exists']==('AP010',110)
    with pytest.raises(ValueError):continuity.read_mixed_archive(dict(continuity.CONTINUITY_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_solver_target_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=continuity.exp_dyadic_continuity_source_pins()
    for pin in continuity.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP075-arithmetic')
    assert target==parse_named(continuity.HELPER_SOURCES['arithmetic'],registry=continuity.definition_registry())
    assert digest==continuity.HELPER_TARGET_SHA256['arithmetic']


def test_complete_dyadic_continuity_uses_no_new_induction_or_axiom():
    result=continuity.prove_exp_dyadic_continuity()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=continuity.prove_exp_dyadic_continuity()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
