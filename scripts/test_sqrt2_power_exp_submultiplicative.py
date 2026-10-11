"""Same-degree submultiplicativity needs no large-argument truncation premise."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_submultiplicative as product


def test_exact_same_degree_statement_has_no_argument_bound_or_extra_horizon():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=product.frozen_exp_submultiplicative_target();n,premises,conclusion=strip_target(target)
    assert n==16 and len(premises)==10 and type(conclusion) is Exists
    assert len(product.canonical(encode_formula(target)))==7229
    names=tuple(reversed(product.PARAMETERS));registry=product.definition_registry()
    assert premises==[parse_named(p,names,registry) for p in product.PREMISES]
    assert conclusion==parse_named('Le((a0*b0)*w,c0*(u*v))',names,registry)
    c=product.source_contract()
    assert c['all_three_degrees_equal'] is c['no_extra_input_horizon_required'] is c['actual_convolution_constructed_and_value_identified'] is True
    assert c['argument_upper_bound_required'] is c['analytic_addition_claimed'] is c['absolute_majorant_claimed'] is c['closes_IR072'] is False


def test_ten_existing_definitions_preserve_the_conservative_dag():
    registry=product.definition_registry();source=product.source_registry();seen=set();ids=set()
    assert len(registry)==10 and 'NatConvolutionPrefix' in registry
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_added_argument_degree_heads_or_product_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('d,x+y,cb,cc,N','d,x,cb,cc,N'),source.replace('~d=0','d=0'),
                    source.replace('d,x+y,cb,cc,N','d,x+y,cb,cc,S N'),
                    source.replace('BetaAt(cb,cc,0,c0)','BetaAt(cb,cc,0,a0)'),
                    source.replace('c0*(u*v)','c0*(u+v)'),source.replace('Sum(cb,cc,S N,w)','Sum(cb,cc,N,w)')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):product.frozen_exp_submultiplicative_target(_registry=registry)


def test_actual_integer_models_identify_convolution_and_include_zero_heads():
    from math import factorial
    def terms(d,x,N,scale):
        h=scale*factorial(N)*d**N;values=[h*x**j//(factorial(j)*d**j) for j in range(N+1)]
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,values
    examples=0;large=0;zeroheads=0;empty=0
    for d in (1,2,3):
        for x in range(3*d+1):
            for y in range(2*d+1):
                for N in range(6):
                    for af,bf,cf in ((0,1,1),(1,0,1),(1,1,0),(1,1,1),(2,3,4)):
                        a,A=terms(d,x,N,af);b,B=terms(d,y,N,bf);c,C=terms(d,x+y,N,cf)
                        convolution=[sum(A[i]*B[j-i] for i in range(j+1)) for j in range(N+1)]
                        assert convolution[0]==a*b and all(((j+1)*d)*convolution[j+1]==(x+y)*convolution[j] for j in range(N))
                        u,v,w,z=sum(A),sum(B),sum(C),sum(convolution)
                        assert (a*b)*w==c*z and z<=u*v and (a*b)*w<=c*(u*v)
                        assert max((a*b)*w,c*(u*v)).bit_length()<=128
                        examples+=1;large+=x+y>2*d;zeroheads+=a*b*c==0;empty+=N==0
    assert examples==3510 and large>0 and zeroheads>0 and empty>0


def test_all_eight_endpoints_have_actual_owned_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==8 and found['sandwich']==('AP041',190) and found['recurrence']==('AP039',160)
    assert found['head']==('AP039',161) and found['same_value']==('AP060',36) and found['sum_unique']==('CV003',109)
    with pytest.raises(ValueError):product.read_mixed_archive(dict(product.INDEPENDENCE_ARCHIVE,sha256='0'*64))


def test_source_and_actual_archive_pins_are_bound():
    pins=product.exp_submultiplicative_source_pins();assert len(pins)==323
    for pin in product.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_submultiplicativity_without_new_induction_or_axiom():
    result=product.prove_exp_submultiplicative()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=product.prove_exp_submultiplicative()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
