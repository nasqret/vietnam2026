"""The power majorant depends on the argument, not the finite horizon."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_integer_majorant as majorant


def test_exact_integer_argument_bound_retains_actual_sum_and_power():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    target=majorant.frozen_exp_integer_majorant_target();n,premises,conclusion=strip_target(target)
    assert n==8 and len(premises)==5 and type(conclusion) is Exists
    names=tuple(reversed(majorant.PARAMETERS));registry=majorant.definition_registry()
    assert premises==[parse_named(p,names,registry) for p in majorant.PREMISES]
    assert conclusion==parse_named('Le(s,C*h)',names,registry)
    c=majorant.source_contract()
    assert c['uniform_in_finite_horizon'] is c['only_constructed_head_product_cancelled'] is c['positive_successor_factor_tables_constructed'] is True
    assert c['new_induction_count']==1 and c['analytic_exponential_claimed'] is c['closes_IR072'] is False


def test_twelve_existing_definitions_preserve_the_conservative_dag():
    registry=majorant.definition_registry();source=majorant.source_registry();seen=set();ids=set()
    assert len(registry)==12 and 'NatExpWeightTable' in registry
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert majorant.source_contract()['new_definition_ids']==[]


def test_changed_integer_argument_exponent_head_or_bound_rejected():
    source=majorant.NAMED_SOURCE;registry=majorant.definition_registry()
    for changed in (source.replace('d,L*d,tb,tc,N','d,L+d,tb,tc,N'),source.replace('~d=0','d=0'),
                    source.replace('Pow(9,S L,C)','Pow(9,L,C)'),source.replace('Pow(9,S L,C)','Pow(9,S N,C)'),
                    source.replace('Le(s,C*h)','Le(s,C)'),source.replace('Sum(tb,tc,S N,s)','Sum(tb,tc,N,s)')):
        assert changed!=source
        with patch.object(majorant,'NAMED_SOURCE',changed),pytest.raises(ValueError):majorant.frozen_exp_integer_majorant_target(_registry=registry)


def test_actual_integer_models_keep_the_same_majorant_across_all_horizons():
    from math import factorial
    def terms(L,d,N,scale):
        h=scale*factorial(N)*d**N;x=L*d
        values=[h*x**j//(factorial(j)*d**j) for j in range(N+1)]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,sum(values)
    examples=0;zeroheads=0;steps=0
    for L in range(8):
        C=9**(L+1)
        for d in (1,2,3):
            for N in range(9):
                for scale in (0,1,3):
                    h,s=terms(L,d,N,scale)
                    assert s<=C*h and max(s,C*h).bit_length()<=128
                    if L:
                        a,u=terms(L-1,d,N,1);b,v=terms(1,d,N,2);p=9**L
                        assert a>0 and b>0 and u<=p*a and v<=9*b and (a*b)*s<=h*(u*v) and C==p*9
                        assert max((a*b)*s,h*(u*v),(a*b)*(C*h)).bit_length()<=128
                        steps+=1
                    examples+=1;zeroheads+=scale==0
    assert examples==648 and zeroheads==216 and steps==567
    for a,b in ((0,1),(1,0)):
        h,s,u,v,p,C=0,1,0,0,1,9
        assert u<=p*a and v<=9*b and (a*b)*s<=h*(u*v) and C==p*9 and not s<=C*h


def test_all_sixteen_endpoints_have_actual_owned_proof_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=majorant.definition_registry();found={}
    for pin in majorant.ARCHIVES:
        rows=majorant.read_mixed_archive(pin)
        for name,source in majorant.ENDPOINT_SOURCES.items():
            if majorant.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==16 and found['product']==('AP071',majorant.PRODUCT_ARCHIVE['root']) and found['constructed']==('CV070',143)
    assert found['power_zero']==('AP010',112) and found['power_step']==('AP010',113) and found['small_bound'][0]=='CV071'
    with pytest.raises(ValueError):majorant.read_mixed_archive(dict(majorant.PRODUCT_ARCHIVE,sha256='0'*64))


def test_source_and_detached_arithmetic_target_are_bound():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=majorant.exp_integer_majorant_source_pins()
    for pin in majorant.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP072-arithmetic')
    assert target==parse_named(majorant.HELPER_SOURCES['arithmetic'],registry=majorant.definition_registry())
    assert digest==majorant.HELPER_TARGET_SHA256['arithmetic']


def test_complete_integer_majorant_has_one_ordinary_induction_and_no_axiom():
    result=majorant.prove_exp_integer_majorant()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=majorant.prove_exp_integer_majorant()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
