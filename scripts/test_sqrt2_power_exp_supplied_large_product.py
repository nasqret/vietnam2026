"""General-argument product transport must preserve all supplied computations."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_supplied_large_product as product


def test_exact_supplied_product_has_no_unit_argument_restriction():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=product.frozen_exp_supplied_large_product_target();n,premises,conclusion=strip_target(target)
    assert n==20 and len(premises)==14 and type(conclusion) is And
    assert len(product.canonical(encode_formula(target)))==11548
    c=product.source_contract()
    assert c['all_three_supplied_recurrences_heads_codes_and_sums_preserved'] is True
    assert c['internal_convolution_identified_by_unrestricted_cross_value_equality'] is True
    assert c['unit_argument_restriction_required'] is c['analytic_exponential_addition'] is c['closes_IR072'] is False


def test_thirteen_existing_definitions_keep_the_exact_dag():
    registry=product.definition_registry();source=product.source_registry();seen=set();ids=set()
    assert len(registry)==13
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_supplied_sum_head_argument_cutoff_or_error_is_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('Sum(cb,cc,S(K+m),w) -> ',''),
                    source.replace('BetaAt(cb,cc,0,c0)','BetaAt(cb,cc,0,a0*b0)'),
                    source.replace('Le(x+y,L*d)','Le(x+y,d)'),source.replace('Le(2*L,K)','Le(L,K)'),
                    source.replace('NatScaledExpRecurrence(d,x+y,cb,cc,K+m)','NatScaledExpRecurrence(d,x,cb,cc,K+m)'),
                    source.replace('2*(B*(c0*(a0*b0)))','2*(c0*(a0*b0))'),source.replace('Pow(2,S m,p)','Pow(2,m,p)')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            product.frozen_exp_supplied_large_product_target(_registry=registry)


def test_integer_models_cover_independent_scales_zero_heads_and_large_arguments():
    from math import factorial
    examples=0;large=distinct=False
    def terms(d,x,N,scale):
        h=scale*factorial(N)*d**N;values=[]
        for j in range(N+1):
            numerator,denominator=h*x**j,d**j*factorial(j)
            assert numerator%denominator==0;values.append(numerator//denominator)
        assert values[0]==h and all(((j+1)*d)*values[j+1]==x*values[j] for j in range(N))
        return h,values
    for d in (1,2):
        for L in range(3):
            for x in range(L*d+1):
                for y in range(L*d-x+1):
                    for K in (2*L,2*L+1):
                        for m in range(2):
                            n=K+m;H=2*n+1;p=2**(m+1);B=L**K
                            for fa,fb,fc in ((0,1,2),(1,0,3),(1,1,0),(1,1,1),(2,3,5)):
                                a0,a=terms(d,x,H,fa);b0,b=terms(d,y,H,fb);c0,c=terms(d,x+y,n,fc)
                                u,v,w=sum(a[:n+1]),sum(b[:n+1]),sum(c)
                                internal=[sum(a[i]*b[j-i] for i in range(j+1)) for j in range(n+1)]
                                assert c0*sum(internal)==(a0*b0)*w
                                assert (a0*b0)*w<=c0*(u*v)
                                assert p*(c0*(u*v))<=p*((a0*b0)*w)+2*(B*(c0*(a0*b0)))
                                assert max(p*(c0*(u*v)),p*((a0*b0)*w)+2*(B*(c0*(a0*b0)))).bit_length()<=128
                                examples+=1;large|=x+y>d;distinct|=c0!=a0*b0 and w!=sum(internal)
    assert examples==640 and large and distinct


def test_exact_unrestricted_independence_restriction_and_sum_uniqueness_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    import sqrt2_power_exp_recurrence_independence as independence
    registry=product.definition_registry();found={}
    assert product.ENDPOINT_SOURCES['same_value']==independence.NAMED_SOURCE
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==8 and found['product']==('AP059',247) and found['same_value']==('AP060',36)
    assert found['restrict']==('CV101',186) and found['sum_unique']==('CV003',109)
    with pytest.raises(ValueError):product.read_mixed_archive(dict(product.INDEPENDENCE_ARCHIVE,sha256='0'*64))


def test_source_pins_and_exact_detached_arithmetic_target():
    import observe_sqrt2_power_tail_steps as observer
    from sqrt2_power_definitions import parse_named
    pins=product.exp_supplied_large_product_source_pins();assert len(pins)==359
    for pin in product.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']
    target,digest,_=observer.target_for('AP061-arithmetic')
    assert target==parse_named(product.HELPER_SOURCES['arithmetic'],registry=product.definition_registry())
    assert digest==product.HELPER_TARGET_SHA256['arithmetic']


def test_complete_general_supplied_product_without_new_induction():
    result=product.prove_exp_supplied_large_product()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=product.prove_exp_supplied_large_product()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
