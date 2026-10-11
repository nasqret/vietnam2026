"""Different finite horizons, codes and denominator scales must stay distinct."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_independent_horizon as horizon


def test_exact_horizon_statement_preserves_both_computations_and_scales():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=horizon.frozen_exp_independent_horizon_target();n,premises,conclusion=strip_target(target)
    assert n==17 and len(premises)==12 and type(conclusion) is And
    assert len(horizon.canonical(encode_formula(target)))==7725
    c=horizon.source_contract()
    assert c['both_supplied_recurrences_heads_codes_sums_and_precision_power_preserved'] is True
    assert c['independent_denominators_heads_and_codes_allowed'] is c['fine_short_sum_constructed_not_assumed'] is True
    assert c['code_number_equality_claimed'] is c['analytic_limit_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_eight_existing_definitions_preserve_the_exact_dag():
    registry=horizon.definition_registry();source=horizon.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Sum','Repeat','Product','Pow','NatScaledExpRecurrence'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert horizon.source_contract()['new_definition_ids']==[]


def test_changed_argument_denominator_horizon_head_or_error_is_rejected():
    source=horizon.NAMED_SOURCE;registry=horizon.definition_registry()
    for changed in (source.replace('x*e=y*d','x*d=y*e'),source.replace('~e=0','e=0'),
                    source.replace('S(K+(L*K+n))+N','K+(L*K+n)+N'),
                    source.replace('BetaAt(bb,bc,0,g)','BetaAt(bb,bc,0,h)'),
                    source.replace('Pow(2,n,r)','Pow(2,S n,r)'),source.replace('+h*g','+h')):
        assert changed!=source
        with patch.object(horizon,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            horizon.frozen_exp_independent_horizon_target(_registry=registry)


def test_independent_integer_models_cover_zero_heads_large_arguments_and_extra_horizons():
    from fractions import Fraction
    from math import factorial,lcm
    def terms(d,x,N,scale):
        coefficients=[Fraction(x,d)**j/factorial(j) for j in range(N+1)]
        h=scale*lcm(*(c.denominator for c in coefficients));raw=[h*c for c in coefficients]
        assert all(v.denominator==1 for v in raw);values=[int(v) for v in raw]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,values
    examples=0;large=distinct=False
    for denominator in (1,2):
        for L in range(3):
            for numerator in range(L*denominator+1):
                for alpha in (1,2):
                    for beta in (1,3):
                        d,x,e,y=denominator*alpha,numerator*alpha,denominator*beta,numerator*beta
                        assert d>0 and e>0 and x*e==y*d and y<=L*e
                        K=2*L
                        for n in range(2):
                            for N in range(3):
                                D=K+(L*K+n);H=(D+1)+N;r=2**n
                                for hf,gf in ((0,1),(1,0),(1,1),(2,3)):
                                    h,a=terms(d,x,D,hf);g,b=terms(e,y,H,gf)
                                    s,t,z=sum(a),sum(b),sum(b[:D+1])
                                    assert g*s==h*z and g*s<=h*t and r*(h*t)<=r*(g*s)+h*g
                                    assert max(r*(h*t),r*(g*s)+h*g).bit_length()<=128
                                    examples+=1;large|=numerator>denominator;distinct|=d!=e and h!=g
    assert examples==1440 and large and distinct


def test_all_twelve_endpoints_resolve_to_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=horizon.definition_registry();found={}
    for pin in horizon.ARCHIVES:
        rows=horizon.read_mixed_archive(pin)
        for name,source in horizon.ENDPOINT_SOURCES.items():
            if horizon.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==12 and found['same_value']==('AP060',36) and found['requested']==('AP063',170)
    assert found['restrict']==('CV101',186) and found['sum_exists']==('CV003',107)
    with pytest.raises(ValueError):horizon.read_mixed_archive(dict(horizon.REQUESTED_ARCHIVE,sha256='0'*64))


def test_source_pins_and_detached_helper_target_are_exact():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=horizon.exp_independent_horizon_source_pins();assert len(pins)==362
    for pin in horizon.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP065-arithmetic')
    assert target==parse_named(horizon.HELPER_SOURCES['arithmetic'],registry=horizon.definition_registry())
    assert digest==horizon.HELPER_TARGET_SHA256['arithmetic']


def test_complete_independent_horizon_without_new_induction():
    result=horizon.prove_exp_independent_horizon()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=horizon.prove_exp_independent_horizon()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
