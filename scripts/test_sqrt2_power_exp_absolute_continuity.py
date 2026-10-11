"""Absolute error depends on a genuine supplied bound and precision budget."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_absolute_continuity as continuity


def test_exact_statement_preserves_majorant_and_symbolic_precision_premises():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=continuity.frozen_exp_absolute_continuity_target();n,premises,conclusion=strip_target(target)
    assert n==16 and len(premises)==11 and type(conclusion) is And
    assert len(continuity.canonical(encode_formula(target)))==5407
    names=tuple(reversed(continuity.PARAMETERS));registry=continuity.definition_registry()
    assert premises==[parse_named(p,names,registry) for p in continuity.PREMISES]
    assert conclusion==parse_named(continuity.CONCLUSION,names,registry)
    c=continuity.source_contract()
    assert c['independent_denominators_heads_and_codes_allowed'] is c['symbolic_precision_scale'] is True
    assert c['precision_power_constructed'] is c['majorant_constructed'] is c['analytic_continuity_claimed'] is c['closes_IR072'] is False


def test_five_existing_definitions_preserve_the_exact_dag():
    registry=continuity.definition_registry();source=continuity.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()['new_definition_ids']==[]


def test_changed_gap_denominator_majorant_budget_or_allowance_rejected():
    source=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for changed in (source.replace('d*y=e*x+g','e*y=d*x+g'),source.replace('~e=0','e=0'),
                    source.replace('Le(t,C*b0)','Le(s,C*b0)'),source.replace('Le((r*g)*C,d*e)','Le(r*g,d*e)'),
                    source.replace('+a0*b0','+a0'),source.replace('BetaAt(bb,bc,0,b0)','BetaAt(bb,bc,0,a0)')):
        assert changed!=source
        with patch.object(continuity,'NAMED_SOURCE',changed),pytest.raises(ValueError):continuity.frozen_exp_absolute_continuity_target(_registry=registry)


def test_actual_integer_models_and_essential_arithmetic_guards():
    from math import factorial
    def terms(d,x,N,scale):
        h=scale*factorial(N)*d**N;values=[h*x**j//(factorial(j)*d**j) for j in range(N+1)]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,sum(values)
    examples=0;nonzero_gap_budget=0;distinct=0
    for d in (1,2,4):
        for e in (1,3,4):
            for x in range(2*d+1):
                for extra in (0,1):
                    y=(e*x+d-1)//d+extra;g=d*y-e*x
                    for N in range(4):
                        for first,second in ((0,1),(1,0),(1,1),(2,3)):
                            a,s=terms(d,x,N,first);b,t=terms(e,y,N,second);C=(t+b-1)//b if b else 0
                            assert t<=C*b
                            for r in (0,1,2,4):
                                if (r*g)*C>d*e:continue
                                assert b*s<=a*t and r*(a*t)<=r*(b*s)+a*b
                                assert max(r*(a*t),r*(b*s)+a*b).bit_length()<=128
                                examples+=1;nonzero_gap_budget+=r*g*a*b>0;distinct+=d!=e and a!=b
    assert examples>1000 and nonzero_gap_budget>0 and distinct>0
    # Dropping any of the helper's essential guards can make it false.
    for p,r,g,C,A,U,V,missing in ((1,1,1,1,1,0,2,'majorant'),(1,1,1,2,1,0,2,'budget'),(0,1,0,2,1,0,2,'nonzero')):
        guards=dict(nonzero=p!=0,relative=p*V<=p*U+g*V,majorant=V<=C*A,budget=(r*g)*C<=p)
        assert guards[missing] is False and all(ok for name,ok in guards.items() if name!=missing)
        assert r*V>r*U+A


def test_all_ten_endpoints_have_owned_actual_proof_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found={}
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==10 and found['relative']==('AP069',143) and found['mul_le_cancel']==('CV071',151)
    with pytest.raises(ValueError):continuity.read_mixed_archive(dict(continuity.RELATIVE_ARCHIVE,sha256='0'*64))


def test_source_pins_and_exact_detached_arithmetic_target():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=continuity.exp_absolute_continuity_source_pins();assert len(pins)==181
    for pin in continuity.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP070-arithmetic')
    assert target==parse_named(continuity.HELPER_SOURCES['arithmetic'],registry=continuity.definition_registry())
    assert digest==continuity.HELPER_TARGET_SHA256['arithmetic']


def test_complete_absolute_continuity_without_new_induction_or_axiom():
    result=continuity.prove_exp_absolute_continuity()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=continuity.prove_exp_absolute_continuity()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
