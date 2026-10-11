"""The coarse positive witness is chosen before every later finite horizon."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_uniform_witness as witness


def test_exact_quantifier_order_and_all_coarse_and_fine_fields():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists,Forall
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_exp_uniform_witness_target(_registry=registry)
    n,premises,body=strip_target(target)
    assert n==5 and len(premises)==3 and len(witness.canonical(encode_formula(target)))==34688
    for _ in witness.OUTPUTS:assert type(body) is Exists;body=body.body
    parts=[]
    for _ in range(13):assert type(body) is And;parts.append(body.left);body=body.right
    parts.append(body);names=tuple(reversed(witness.PARAMETERS+witness.OUTPUTS))
    assert parts==[parse_named(part,names,registry) for part in witness.PARTS]
    assert type(body) is Forall;body=body.body
    for _ in witness.FINE_OUTPUTS:assert type(body) is Exists;body=body.body
    fine=[]
    for _ in range(12):assert type(body) is And;fine.append(body.left);body=body.right
    fine.append(body);names=tuple(reversed(witness.PARAMETERS+witness.OUTPUTS+('N',)+witness.FINE_OUTPUTS))
    assert fine==[parse_named(part,names,registry) for part in witness.FINE_PARTS]
    c=witness.source_contract()
    assert c['coarse_witness_and_precision_chosen_before_arbitrary_horizon'] is c['both_heads_and_precision_power_proved_nonzero'] is True
    assert c['all_index_factorial_normalizations_retained'] is True
    assert c['analytic_limit_claimed'] is c['fixed_approximation_program_changed'] is c['closes_IR072'] is False


def test_twelve_existing_definitions_preserve_the_conservative_dag():
    registry=witness.definition_registry();source=witness.source_registry();seen=set();ids=set()
    assert len(registry)==12
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_universal_horizon_positivity_or_normalization_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('forall N.','exists N.'),source.replace('~h=0','h=0'),
                    source.replace('~g=0','g=0'),source.replace('~r=0','r=0'),
                    source.replace('h=f*q','h=f+q'),source.replace('g=F*Q','g=F+Q'),
                    source.replace('h*g','h'),source.replace('Pow(2,n,r)','Pow(2,K,r)')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):witness.frozen_exp_uniform_witness_target(_registry=registry)


def test_same_coarse_integer_computation_works_for_every_later_model():
    from math import factorial
    def construct(d,x,H):
        f=factorial(H);q=d**H;h=f*q
        weights=tuple(f//factorial(j)*d**(H-j) for j in range(H+1))
        terms=tuple(weights[j]*x**j for j in range(H+1))
        assert h==weights[0]==terms[0] and h>0
        assert all(((j+1)*d)*terms[j+1]==x*terms[j] for j in range(H))
        assert all((terms[j]*factorial(j))*d**j==h*x**j for j in range(H+1))
        return weights,terms,h,f,q,sum(terms)
    examples=0;coarse_count=0;zero_arguments=0;zero_horizons=0
    for d in (1,2):
        for L in range(3):
            for x in range(L*d+1):
                for K in ((2*L,2*L+1) if L<2 else (2*L,)):
                    for n in (range(4) if L<2 else range(2)):
                        D=K+(L*K+n);coarse=construct(d,x,D);h,s=coarse[2],coarse[5];r=2**n
                        assert r>0;coarse_count+=1
                        for N in ((0,1,2,4) if L<2 else (0,1,2)):
                            fine=construct(d,x,D+1+N);g,t=fine[2],fine[5]
                            assert g*s<=h*t and r*(h*t)<=r*(g*s)+h*g
                            assert max(r*(h*t),r*(g*s)+h*g).bit_length()<=128
                            assert coarse==construct(d,x,D)
                            examples+=1;zero_arguments+=x==0;zero_horizons+=N==0
    assert examples==272 and coarse_count==72 and zero_arguments>0 and zero_horizons==72


def test_each_actual_constructor_and_comparison_endpoint_is_owned():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();found={}
    for pin in witness.ARCHIVES:
        rows=witness.read_mixed_archive(pin)
        for name,source in witness.ENDPOINT_SOURCES.items():
            if witness.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert found==dict(constructed=('CV070',143),horizon=('AP065',178),power_exists=('AP010',110),power_nonzero=('AP010',120),succ_ne_zero=('CV071',12))
    with pytest.raises(ValueError):witness.read_mixed_archive(dict(witness.HORIZON_ARCHIVE,sha256='0'*64))


def test_source_and_actual_archive_bytes_are_bound():
    pins=witness.exp_uniform_witness_source_pins();assert len(pins)==364
    for pin in witness.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_uniform_witness_has_no_new_induction_or_axiom():
    result=witness.prove_exp_uniform_witness()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_exp_uniform_witness()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
