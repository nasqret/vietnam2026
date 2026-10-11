"""All three normalized product computations are actual arithmetic witnesses."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_product_witness as witness


def test_exact_positive_product_witness_retains_all_thirty_nine_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_exp_product_witness_target(_registry=registry)
    n,premises,body=strip_target(target)
    assert n==6 and len(premises)==3 and len(witness.canonical(encode_formula(target)))==56421
    assert len(witness.OUTPUTS)==27 and len(witness.PARTS)==39
    for _ in witness.OUTPUTS:assert type(body) is Exists;body=body.body
    parts=[]
    for _ in range(38):assert type(body) is And;parts.append(body.left);body=body.right
    parts.append(body);names=tuple(reversed(witness.PARAMETERS+witness.OUTPUTS))
    assert parts==[parse_named(part,names,registry) for part in witness.PARTS]
    c=witness.source_contract()
    assert c['all_three_actual_tables_heads_factorizations_and_full_sums_constructed'] is c['both_actual_input_prefixes_constructed'] is True
    assert c['three_heads_and_precision_power_proved_nonzero'] is c['all_three_indexwise_factorial_normalizations_retained'] is True
    assert c['analytic_exponential_addition'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_twelve_existing_definitions_preserve_the_exact_conservative_dag():
    registry=witness.definition_registry();source=witness.source_registry();seen=set();ids=set()
    assert len(registry)==12
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_positive_heads_normalization_prefix_or_error_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('~a0=0','a0=0'),source.replace('~b0=0','b0=0'),
                    source.replace('~c0=0','c0=0'),source.replace('~r=0','r=0'),
                    source.replace('c0=cf*cq','c0=cf+cq'),source.replace('Pow(x+y,j,xj)','Pow(x,j,xj)'),
                    source.replace(f'Sum(ab,ac,S({witness.D}),u)',f'Sum(ab,ac,S({witness.H}),u)'),
                    source.replace('+c0*(a0*b0)','+c0')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):witness.frozen_exp_product_witness_target(_registry=registry)


def test_actual_factorial_tables_and_same_prefixes_satisfy_product_error():
    from math import factorial
    def construct(d,x,H):
        f=factorial(H);q=d**H;h=f*q
        weights=tuple(f//factorial(j)*d**(H-j) for j in range(H+1))
        terms=tuple(weights[j]*x**j for j in range(H+1))
        assert h==weights[0]==terms[0] and h>0
        assert all(((j+1)*d)*terms[j+1]==x*terms[j] for j in range(H))
        assert all((terms[j]*factorial(j))*d**j==h*x**j for j in range(H+1))
        return h,terms
    examples=0;zero_arguments=0;zero_precision=0
    for d in (1,2,3):
        for L in (0,1):
            for x in range(L*d+1):
                for y in range(L*d-x+1):
                    for K in ((0,1) if L==0 else (2,)):
                        for n in (range(4) if L==0 else range(2)):
                            D=K+(L*K+n);H=2*D+1;r=2**n
                            a,A=construct(d,x,H);b,B=construct(d,y,H);c,C=construct(d,x+y,D)
                            u,v,w=sum(A[:D+1]),sum(B[:D+1]),sum(C)
                            assert a*b*w<=c*(u*v) and r*(c*(u*v))<=r*((a*b)*w)+c*(a*b)
                            assert max(r*(c*(u*v)),r*((a*b)*w)+c*(a*b)).bit_length()<=128
                            examples+=1;zero_arguments+=x+y==0;zero_precision+=n==0
    assert examples==62 and zero_arguments>0 and zero_precision>0


def test_actual_product_constructors_and_short_sum_endpoints_are_owned():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();found={}
    for pin in witness.ARCHIVES:
        rows=witness.read_mixed_archive(pin)
        for name,source in witness.ENDPOINT_SOURCES.items():
            if witness.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found==dict(constructed=('CV070',143),product=('AP064',265),power_exists=('AP010',110),sum_exists=('CV003',107))
    with pytest.raises(ValueError):witness.read_mixed_archive(dict(witness.PRODUCT_ARCHIVE,sha256='0'*64))


def test_source_and_actual_archive_bytes_are_bound():
    pins=witness.exp_product_witness_source_pins();assert len(pins)==367
    for pin in witness.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_positive_product_witness_has_no_new_induction_or_axiom():
    result=witness.prove_exp_product_witness()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_exp_product_witness()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
