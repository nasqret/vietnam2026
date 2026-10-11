"""Large-argument finite Cauchy products retain all actual computation fields."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_large_argument_product as product


def test_exact_product_statement_retains_nine_computation_and_error_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();target=product.frozen_exp_large_argument_product_target(_registry=registry)
    n,premises,conclusion=strip_target(target)
    assert n==14 and len(premises)==9 and type(conclusion) is Exists
    assert len(product.canonical(encode_formula(target)))==16415
    for _ in product.OUTPUTS:assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(8):assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(product.PARAMETERS+product.OUTPUTS))
    assert fields==[parse_named(part,names,registry) for part in product.PARTS]
    c=product.source_contract();assert c['actual_convolution_recurrence_product_head_and_four_sums_constructed'] is True
    assert c['analytic_exponential_addition'] is c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_thirteen_existing_definitions_keep_the_exact_dag():
    registry=product.definition_registry();source=product.source_registry();seen=set();ids=set()
    assert len(registry)==13
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert product.source_contract()['new_definition_ids']==[]


def test_changed_argument_cutoff_power_degree_head_or_error_is_rejected():
    source=product.NAMED_SOURCE;registry=product.definition_registry()
    for changed in (source.replace('Le(x+y,L*d)','Le(x+y,d)'),source.replace('Le(2*L,K)','Le(L,K)'),
                    source.replace('Pow(2,S m,p)','Pow(2,m,p)'),source.replace('Pow(L,K,B)','Pow(L,m,B)'),
                    source.replace('BetaAt(cb,cc,0,a0*b0)','BetaAt(cb,cc,0,a0+b0)'),
                    source.replace('S(K+m)+(K+m)','K+m'),source.replace('2*(B*(a0*b0))','2*(a0*b0)')):
        assert changed!=source
        with patch.object(product,'NAMED_SOURCE',changed),pytest.raises(ValueError):product.frozen_exp_large_argument_product_target(_registry=registry)


def test_actual_integer_convolutions_cover_zero_heads_and_large_arguments():
    from math import factorial
    examples=0;large=False
    for d in (1,2):
        for L in range(3):
            for x in range(L*d+1):
                for y in range(L*d-x+1):
                    for K in (2*L,2*L+1):
                        for m in range(3):
                            n=K+m;H=2*n+1;h=factorial(H)*d**H
                            for r0,r1 in ((0,1),(1,0),(1,1),(2,3)):
                                first=[r0*h*x**j//(d**j*factorial(j)) for j in range(H+1)]
                                second=[r1*h*y**j//(d**j*factorial(j)) for j in range(H+1)]
                                conv=[sum(first[i]*second[j-i] for i in range(j+1)) for j in range(H+1)]
                                a0,b0=first[0],second[0]
                                assert conv[0]==a0*b0
                                assert all(((j+1)*d)*conv[j+1]==(x+y)*conv[j] for j in range(H))
                                u,v,s,t=sum(first[:n+1]),sum(second[:n+1]),sum(conv[:n+1]),sum(conv)
                                p,B=2**(m+1),L**K
                                assert s<=u*v<=t and p*(u*v)<=p*s+2*(B*(a0*b0))
                                assert max(p*(u*v),p*s+2*(B*(a0*b0))).bit_length()<=128
                                examples+=1;large|=x+y>d
    assert examples==768 and large


def test_each_product_endpoint_has_one_actual_owned_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=product.definition_registry();found={}
    for pin in product.ARCHIVES:
        rows=product.read_mixed_archive(pin)
        for name,source in product.ENDPOINT_SOURCES.items():
            if product.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==6 and found['sandwich']==('AP041',190) and found['truncation']==('AP057',159)
    with pytest.raises(ValueError):product.read_mixed_archive(dict(product.TRUNCATION_ARCHIVE,sha256='0'*64))


def test_source_and_archive_bytes_are_bound():
    pins=product.exp_large_argument_product_source_pins();assert len(pins)==355
    for pin in product.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_large_argument_product_without_new_induction():
    result=product.prove_exp_large_argument_product()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=product.prove_exp_large_argument_product()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
