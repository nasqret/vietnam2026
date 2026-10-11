"""Independent supplied log/exp refinement, with exact retained error powers."""
from dataclasses import replace
from fractions import Fraction
from math import lcm
from unittest.mock import patch

import pytest
import sqrt2_power_log_exp_refinement as refinement


def test_exact_refinement_preserves_log_and_exp_cutoffs_and_data():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(refinement.frozen_log_exp_refinement_target())
    names=tuple(reversed(refinement.PARAMETERS));registry=refinement.definition_registry()
    assert n==23 and len(premises)==15 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in refinement.PREMISES]
    assert conclusion==parse_named(refinement.CONCLUSION,names,registry)
    c=refinement.source_contract()
    assert c['both_actual_logarithm_and_exponential_computations_preserved'] is c['logarithm_and_exponential_cutoffs_independent'] is True
    assert c['independent_coefficient_scales_codes_and_exp_heads_allowed'] is c['actual_ordered_log_gap_constructed'] is True
    assert c['analytic_log_exp_identity_claimed'] is c['analytic_limit_claimed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_shared_definition_identity_is_exact_despite_historical_display_metadata():
    first=refinement.argument_registry();second=refinement.exp_registry();registry=refinement.definition_registry();seen=set();ids=set()
    identity=('stable_id','name','parameters','template_source','template_formula','conceptual_dependencies')
    for name,spec in registry.items():
        original=first[name] if name in first else second[name]
        assert spec==original and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        for source in (first,second):
            if name in source:assert all(getattr(spec,key)==getattr(source[name],key) for key in identity)
        seen.add(name);ids.add(spec.stable_id)
    assert refinement.source_contract()['new_definition_ids']==[] and 'NatSqrt2LogArgument' not in registry
    assert first['Le']!=second['Le'] and first['Lt']!=second['Lt']
    changed=dict(second);changed['Le']=replace(second['Le'],stable_id='ND9999')
    with patch.object(refinement,'exp_registry',return_value=changed),pytest.raises(ValueError):refinement.definition_registry()
    changed=dict(second);changed['Le']=replace(second['Le'],template_formula=second['Lt'].template_formula)
    with patch.object(refinement,'exp_registry',return_value=changed),pytest.raises(ValueError):refinement.definition_registry()


def test_changed_power_log_value_horizon_or_error_is_rejected():
    source=refinement.NAMED_SOURCE;registry=refinement.definition_registry()
    for changed in (source.replace('~e=0','e=0'),source.replace('NatAtanhPrefix(e,bb,bc,(S k)+l)','NatAtanhPrefix(d,bb,bc,(S k)+l)'),
                    source.replace('Pow(3,(S k)+l,q)','Pow(3,S k,q)'),source.replace('(S m)+N','m+N'),
                    source.replace('Pow(2,m,P)','Pow(2,k,P)'),source.replace('(9*3)*P+2*p','9*P+2*p')):
        assert changed!=source
        with patch.object(refinement,'NAMED_SOURCE',changed),pytest.raises(ValueError):refinement.frozen_log_exp_refinement_target(_registry=registry)


def _atanh(M,scale):
    d=scale*lcm(*(i for i in range(1,M,2)));coefficients=[0 if i%2==0 else 2*d//i for i in range(M)];x=0
    for c in coefficients:x=3*x+c
    assert all(c==0 if i%2==0 else i*c==2*d for i,c in enumerate(coefficients))
    return d,x,3**M


def _exp(x,d,N):
    terms=[Fraction(1)]
    for j in range(N):terms.append(terms[-1]*Fraction(x,(j+1)*d))
    head=lcm(*(v.denominator for v in terms));values=[int(head*v) for v in terms]
    assert values[0]==head and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
    return head,sum(values)


def test_actual_independent_log_and_exp_models_and_positive_factor_guard():
    examples=0;strict_log=0;zero_heads=0;equal_log_length=0;unequal_scales=0
    for k in range(3):
        for l in range(3):
            for ds in (1,2):
                for es in (1,3):
                    d,x,p=_atanh(k+1,ds);e,z,q=_atanh(k+1+l,es);F=d*(e*q)
                    gap=(d*p)*(3*z)-(e*q)*(3*x)
                    assert 0<=gap<=3*F and 3*z<=e*q
                    for m in range(3):
                        for N in range(2):
                            ah,us=_exp(3*x,d*p,m);bh,vs=_exp(3*z,e*q,m+1+N);P=2**m
                            for sa,sb in ((0,0),(0,1),(1,0),(1,1),(2,3)):
                                a,b,u,v=sa*ah,sb*bh,sa*us,sb*vs
                                assert b*u<=a*v and (p*P)*(a*v)<=(p*P)*(b*u)+((9*3)*P+2*p)*(a*b)
                                assert max((p*P)*(a*v),(p*P)*(b*u)+((9*3)*P+2*p)*(a*b),F).bit_length()<=128
                                examples+=1;strict_log+=gap>0;zero_heads+=a==0 or b==0;equal_log_length+=l==0;unequal_scales+=d!=e
    assert examples==1080 and strict_log>0 and zero_heads==648 and equal_log_length==360 and unequal_scales>0
    # The purely arithmetic normalization cannot cancel a zero factor.
    F=0;p=P=a=b=1;g=u=0;v=30
    assert (p*F)*(P*(a*v))<=(p*F)*(P*(b*u))+(9*(g*P)+2*(p*F))*(a*b)
    assert not (p*P)*(a*v)<=(p*P)*(b*u)+((9*3)*P+2*p)*(a*b)


def test_twenty_one_endpoints_have_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=refinement.definition_registry();found={}
    for pin in refinement.ARCHIVES:
        rows=refinement.read_mixed_archive(pin)
        for name,source in refinement.ENDPOINT_SOURCES.items():
            if refinement.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==21 and found['logarithm']==('CV093',refinement.LOG_ARCHIVE['root'])
    assert found['two_error']==('CV101',refinement.TWO_ERROR_ARCHIVE['root'])
    assert found['inner_bound']==('CV086',refinement.TERNARY_ARCHIVE['root'])
    with pytest.raises(ValueError):refinement.read_mixed_archive(dict(refinement.LOG_ARCHIVE,sha256='0'*64))


def test_current_sources_archives_and_exact_solver_helper_are_pinned():
    from observe_sqrt2_power_tail_steps import target_for
    from sqrt2_power_definitions import parse_named
    pins=refinement.log_exp_refinement_source_pins()
    for pin in refinement.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    assert 'sha256' in pins['scripts/sqrt2_power_log_exp_refinement.py']
    target,digest,_=target_for('AP082-arithmetic')
    assert target==parse_named(refinement.HELPER_SOURCES['arithmetic'],registry=refinement.definition_registry())
    assert digest==refinement.HELPER_TARGET_SHA256['arithmetic']
    with patch.dict(refinement.HELPER_TARGET_SHA256,arithmetic='0'*64),pytest.raises(ValueError):target_for('AP082-arithmetic')


def test_complete_refinement_replays_without_new_induction_or_axioms():
    result=refinement.prove_log_exp_refinement()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=refinement.prove_log_exp_refinement()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
