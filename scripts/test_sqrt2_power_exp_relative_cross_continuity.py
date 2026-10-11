"""Relative continuity preserves independent input scales and decoded tables."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_relative_cross_continuity as continuity


def test_exact_independent_relative_statement_has_no_argument_bound():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    target=continuity.frozen_exp_relative_cross_continuity_target();n,premises,conclusion=strip_target(target)
    assert n==14 and len(premises)==9 and type(conclusion) is And
    names=tuple(reversed(continuity.PARAMETERS));registry=continuity.definition_registry()
    assert premises==[parse_named(p,names,registry) for p in continuity.PREMISES]
    assert conclusion==parse_named(continuity.CONCLUSION,names,registry)
    c=continuity.source_contract()
    assert c['independent_argument_denominators_heads_and_codes_allowed'] is c['actual_common_denominator_and_head_tables_constructed'] is True
    assert c['argument_upper_bound_required'] is c['absolute_majorant_claimed'] is c['rational_validity_claimed'] is c['analytic_continuity_claimed'] is c['closes_IR072'] is False


def test_six_existing_definitions_preserve_the_exact_dag():
    registry=continuity.definition_registry();source=continuity.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','NatLinearTriple','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert continuity.source_contract()['new_definition_ids']==[]


def test_changed_cross_gap_head_denominator_or_relative_error_rejected():
    source=continuity.NAMED_SOURCE;registry=continuity.definition_registry()
    for changed in (source.replace('d*y=e*x+g','e*y=d*x+g'),source.replace('~e=0','e=0'),
                    source.replace('BetaAt(bb,bc,0,b0)','BetaAt(bb,bc,0,a0)'),
                    source.replace('+g*(a0*t)','+g*(b0*s)'),source.replace('Le(b0*s,a0*t)','Le(a0*t,b0*s)'),
                    source.replace('Sum(bb,bc,S N,t)','Sum(bb,bc,N,t)')):
        assert changed!=source
        with patch.object(continuity,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            continuity.frozen_exp_relative_cross_continuity_target(_registry=registry)


def test_independent_integer_models_cover_large_arguments_and_zero_scales():
    from math import factorial
    def terms(d,x,N,scale):
        h=scale*factorial(N)*d**N
        values=[h*x**j//(factorial(j)*d**j) for j in range(N+1)]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,values
    examples=0;large=0;distinct=0;zeroheads=0;empty=0
    for d in (1,2):
        for e in (1,3):
            for x in range(4*d+1):
                for extra in (0,1,3):
                    y=(e*x+d-1)//d+extra;g=d*y-e*x
                    assert g>=0
                    for N in (0,1,3,5):
                        for first,second in ((0,1),(1,0),(1,1),(2,3)):
                            a,A=terms(d,x,N,first);b,B=terms(e,y,N,second);s,t=sum(A),sum(B)
                            assert b*s<=a*t and (d*e)*(a*t)<=(d*e)*(b*s)+g*(a*t)
                            assert max((d*e)*(a*t),(d*e)*(b*s)+g*(a*t)).bit_length()<=128
                            examples+=1;large+=y>2*e;distinct+=d!=e and a!=b;zeroheads+=a*b==0;empty+=N==0
    assert examples==1344 and large>0 and distinct>0 and zeroheads>0 and empty>0


def test_each_relative_and_rescaling_endpoint_has_an_actual_owned_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=continuity.definition_registry();found={}
    for pin in continuity.ARCHIVES:
        rows=continuity.read_mixed_archive(pin)
        for name,source in continuity.ENDPOINT_SOURCES.items():
            if continuity.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==4 and found['continuity']==('AP068',continuity.RELATIVE_ARCHIVE['root'])
    assert found['rescaling']==('CV097',113) and found['mul_ne_zero']==('CV071',45) and found['mul_comm']==('CV071',6)
    with pytest.raises(ValueError):continuity.read_mixed_archive(dict(continuity.RELATIVE_ARCHIVE,sha256='0'*64))


def test_source_and_actual_archive_pins_are_bound():
    pins=continuity.exp_relative_cross_continuity_source_pins()
    for pin in continuity.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert 'scripts/sqrt2_power_exp_relative_continuity.py' in pins and 'scripts/sqrt2_power_exp_rescaling.py' in pins


def test_complete_relative_cross_continuity_without_new_induction_or_axiom():
    result=continuity.prove_exp_relative_cross_continuity()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=continuity.prove_exp_relative_cross_continuity()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
