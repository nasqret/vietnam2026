"""Symmetric finite continuity keeps both actual computations and its budget."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_bounded_continuity as continuity


def test_exact_symmetric_statement_has_both_argument_errors_and_budget():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(continuity.frozen_exp_bounded_continuity_target())
    names=tuple(reversed(continuity.PARAMETERS));registry=continuity.definition_registry()
    assert n==17 and len(premises)==14 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in continuity.PREMISES]
    assert conclusion==parse_named(continuity.CONCLUSION,names,registry)
    c=continuity.source_contract()
    assert c['argument_order_assumed'] is c['analytic_continuity_claimed'] is c['closes_IR072'] is False
    assert c['majorant_proved_via_AP073'] is c['actual_ordered_gap_extracted'] is True
    assert c['new_induction_count']==0


def test_twelve_existing_definitions_are_topologically_ordered_and_conservative():
    registry=continuity.definition_registry();source=continuity.source_registry();seen=set();ids=set()
    assert len(registry)==12 and 'Pow' in registry and 'NatScaledExpRecurrence' in registry
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()['new_definition_ids']==[]


def test_changed_argument_error_power_budget_or_conclusion_is_rejected():
    source=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for changed in (source.replace('Le(y,L*e)','Le(y,L*d)'),source.replace('~e=0','e=0'),
                    source.replace('Le(e*x,d*y+g)','Le(d*y,e*x+g)'),source.replace('Pow(9,S L,C)','Pow(9,S N,C)'),
                    source.replace('Le((r*g)*C,d*e)','Le(r*g,d*e)'),source.replace('r*(a0*t)+a0*b0','r*(a0*t)+a0')):
        assert changed!=source
        with patch.object(continuity,'NAMED_SOURCE',changed),pytest.raises(ValueError):continuity.frozen_exp_bounded_continuity_target(_registry=registry)


def test_actual_finite_models_cover_both_orders_nonzero_errors_and_zero_heads():
    from math import factorial
    examples=0;strict_forward=0;strict_reverse=0;zeroheads=0;nonzero_precision_gap=0
    scales=((0,0),(0,1),(1,0),(1,1),(2,3))
    for L in range(4):
        C=9**(L+1);d=2*C;e=3*C
        candidates={(level*d,level*e+delta) for level in range(L+1) for delta in (-2,-1,0,1,2) if 0<=level*e+delta<=L*e}
        for x,y in sorted(candidates):
            exact=abs(d*y-e*x)
            for g in (exact,exact+d):
                for r in (0,1,2,3):
                    if (r*g)*C>d*e:continue
                    assert d*y<=e*x+g and e*x<=d*y+g and x<=L*d and y<=L*e
                    for N in range(4):
                        for sa,sb in scales:
                            a=sa*factorial(N)*d**N;b=sb*factorial(N)*e**N
                            first=[a*x**j//(factorial(j)*d**j) for j in range(N+1)]
                            second=[b*y**j//(factorial(j)*e**j) for j in range(N+1)]
                            u,v=sum(first),sum(second);U=b*u;V=a*v
                            assert first[0]==a and second[0]==b
                            assert all(((j+1)*d)*first[j+1]==x*first[j] and ((j+1)*e)*second[j+1]==y*second[j] for j in range(N))
                            assert u<=C*a and v<=C*b and r*U<=r*V+a*b and r*V<=r*U+a*b
                            assert max(r*U+a*b,r*V+a*b,(r*g)*C,d*e).bit_length()<=128
                            examples+=1;strict_forward+=d*y>e*x;strict_reverse+=d*y<e*x
                            zeroheads+=a==0 or b==0;nonzero_precision_gap+=r>0 and exact>0
    assert examples==4000 and strict_forward==strict_reverse==1200 and zeroheads==2400 and nonzero_precision_gap==1440
    # Without the budget, even degree one can exceed the requested error.
    d,e,x,y,N,a,b,r,C=1,1,0,1,1,1,1,2,81
    u,v=1,2;g=1
    assert x<=d and y<=e and not (r*g)*C<=d*e and not r*(a*v)<=r*(b*u)+a*b


def test_ten_owned_endpoints_include_actual_order_gap_and_cancellation_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found={}
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==10 and found['majorant']==('AP073',continuity.MAJORANT_ARCHIVE['root'])
    assert found['absolute']==('AP070',continuity.ABSOLUTE_ARCHIVE['root'])
    assert all(found[name][0]=='AP007' for name in ('le_gap','cancel_order','allowance','le_total'))
    with pytest.raises(ValueError):continuity.read_mixed_archive(dict(continuity.MAJORANT_ARCHIVE,sha256='0'*64))


def test_current_sources_and_all_actual_archives_are_pinned():
    pins=continuity.exp_bounded_continuity_source_pins()
    for pin in continuity.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    for name in ('exp_bounded_majorant','exp_absolute_continuity','exp_two_sided_continuity','exp_bounded_continuity'):
        assert 'sha256' in pins['scripts/sqrt2_power_'+name+'.py']


def test_complete_bounded_continuity_replays_without_new_induction_or_axiom():
    result=continuity.prove_exp_bounded_continuity()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=continuity.prove_exp_bounded_continuity()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
