"""Independent rational denominators and all six actual powers are preserved."""
from unittest.mock import patch

import pytest
import sqrt2_power_rational_power_difference as difference


def test_exact_rational_bound_preserves_normalizations_and_positive_outputs():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    n,premises,conclusion=strip_target(difference.frozen_rational_power_difference_target())
    names=tuple(reversed(difference.PARAMETERS));registry=difference.definition_registry()
    assert n==13 and len(premises)==12 and type(conclusion) is And
    assert premises==[parse_named(p,names,registry) for p in difference.PREMISES]
    assert conclusion==parse_named(difference.CONCLUSION,names,registry)
    c=difference.source_contract()
    assert c['all_six_actual_powers_preserved'] is c['both_output_denominator_powers_proved_nonzero'] is True
    assert c['independent_argument_denominators_allowed'] is c['actual_cross_numerator_and_bound_powers_constructed'] is True
    assert c['denominator_cancellation_used'] is c['input_order_assumed'] is c['closes_IR072'] is False
    assert c['new_induction_count']==0


def test_six_existing_definitions_remain_conservative_and_unchanged():
    from sqrt2_power_positive_power_comparison import argument_registry
    registry=difference.definition_registry();source=argument_registry();seen=set();ids=set()
    assert tuple(registry)==('Lt','BetaAt','Product','Repeat','Pow','Le')
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert difference.source_contract()['new_definition_ids']==[]


def test_changed_denominator_power_cross_product_or_error_is_rejected():
    source=difference.NAMED_SOURCE;registry=difference.definition_registry()
    for changed in (source.replace('~e=0','e=0'),source.replace('Pow(e,S k,E)','Pow(d,S k,E)'),
                    source.replace('Le(a*e,b*d+g)','Le(b*d,a*e+g)'),source.replace('Pow(d*e,k,Q)','Pow(d+e,k,Q)'),
                    source.replace('(S k)*(g*(C*Q))','k*(g*(C*Q))'),source.replace('Le(v*D,u*E+','Le(v*E,u*D+')):
        assert changed!=source
        with patch.object(difference,'NAMED_SOURCE',changed),pytest.raises(ValueError):difference.frozen_rational_power_difference_target(_registry=registry)


def test_actual_rational_models_cover_unequal_denominators_both_orders_and_zero_numerators():
    examples=0;zero_numerator=0;forward=0;reverse=0;unequal=0
    for M in range(4):
        for d in range(1,5):
            for e in range(1,5):
                for a in range(M*d+1):
                    for b in range(M*e+1):
                        for slack in range(3):
                            g=abs(b*d-a*e)+slack
                            for k in range(6):
                                m=k+1;u=a**m;v=b**m;D=d**m;E=e**m;C=M**k;Q=(d*e)**k
                                X=(a*e)**m;Y=(b*d)**m;R=(M*(d*e))**k;err=m*(g*(C*Q))
                                assert D>0 and E>0 and X==u*E and Y==v*D and R==C*Q
                                assert v*D<=u*E+err and u*E<=v*D+err
                                assert max(v*D+err,u*E+err).bit_length()<=128
                                examples+=1;zero_numerator+=a==0 or b==0;forward+=a*e<b*d;reverse+=b*d<a*e;unequal+=d!=e
    assert examples==34992 and zero_numerator==9792 and forward==reverse>0 and unequal>0
    # The denominator nonzero premise is necessary for the positive output.
    d,k=0,2
    assert d**(k+1)==0


def test_seven_endpoints_have_actual_unambiguous_proof_owners():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=difference.definition_registry();found={}
    for pin in difference.ARCHIVES:
        rows=difference.read_mixed_archive(pin)
        for name,source in difference.ENDPOINT_SOURCES.items():
            if difference.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==7 and found['symmetric']==('AP077',difference.SYMMETRIC_ARCHIVE['root'])
    assert found['product']==('AP078',difference.PRODUCT_ARCHIVE['root']) and found['power_exists']==('AP010',110)
    assert found['power_nonzero']==('AP010',120)
    with pytest.raises(ValueError):difference.read_mixed_archive(dict(difference.SYMMETRIC_ARCHIVE,sha256='0'*64))


def test_current_producer_and_all_actual_archives_are_pinned():
    pins=difference.rational_power_difference_source_pins()
    for pin in difference.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    for name in ('symmetric_power_difference','product_power','rational_power_difference'):
        assert 'sha256' in pins['scripts/sqrt2_power_'+name+'.py']


def test_complete_rational_bound_replays_without_new_induction_or_axioms():
    result=difference.prove_rational_power_difference()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=difference.prove_rational_power_difference()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
