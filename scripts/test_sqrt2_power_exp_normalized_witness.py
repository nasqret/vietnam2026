"""Actual denominator-cleared exponential tables with normalized finite errors."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_normalized_witness as witness


def test_exact_witness_retains_all_seventeen_fields_and_positive_denominators():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();target=witness.frozen_exp_normalized_witness_target(_registry=registry)
    n,premises,conclusion=strip_target(target)
    assert n==6 and len(premises)==3 and type(conclusion) is Exists
    assert len(witness.canonical(encode_formula(target)))==21058
    for _ in witness.OUTPUTS:assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(16):assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(witness.PARAMETERS+witness.OUTPUTS))
    assert fields==[parse_named(part,names,registry) for part in witness.PARTS]
    c=witness.source_contract();assert c['actual_weights_terms_head_normalization_powers_and_sums_constructed'] is True
    assert c['positive_original_head_and_binary_power_proved'] is c['all_term_factorial_normalization_retained'] is True
    assert c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_twelve_existing_definitions_keep_the_exact_dag():
    registry=witness.definition_registry();source=witness.source_registry();seen=set();ids=set()
    assert len(registry)==12
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert witness.source_contract()['new_definition_ids']==[]


def test_changed_head_power_table_degree_or_error_is_rejected():
    source=witness.NAMED_SOURCE;registry=witness.definition_registry()
    for changed in (source.replace('~h=0','h=0'),source.replace('~p=0','p=0'),
                    source.replace('Pow(L,K,B)','Pow(L,m,B)'),source.replace('h=f*q','h=f+q'),
                    source.replace('Sum(tb,tc,K+m,s)','Sum(tb,tc,S(K+m),s)'),
                    source.replace('NatExpWeightTable(d,(K+m)+N','NatExpWeightTable(d,K+m'),
                    source.replace('2*(B*h)','2*h')):
        assert changed!=source
        with patch.object(witness,'NAMED_SOURCE',changed),pytest.raises(ValueError):witness.frozen_exp_normalized_witness_target(_registry=registry)


def test_actual_weighted_integer_models_verify_normalization_and_error():
    from math import factorial
    examples=0;empty=0
    for d in (1,2,3):
        for L in range(4):
            for x in range(L*d+1):
                for K in (2*L,2*L+1):
                    for m in (0,1,4):
                        for N in (0,2,5):
                            H=K+m+N;f=factorial(H);q=d**H;h=f*q
                            weights=[f//factorial(j)*d**(H-j) for j in range(H+1)]
                            values=[weights[j]*x**j for j in range(H+1)]
                            assert h==weights[0]==values[0] and h>0
                            assert all(((j+1)*d)*values[j+1]==x*values[j] for j in range(H))
                            assert all((values[j]*factorial(j))*d**j==h*x**j for j in range(H+1))
                            s,t,p,B=sum(values[:K+m]),sum(values),2**m,L**K
                            assert p>0 and s<=t and p*t<=p*s+2*(B*h)
                            assert max(p*t,p*s+2*(B*h)).bit_length()<=128
                            examples+=1;empty+=K+m==0
    assert examples==864 and empty==9


def test_each_actual_constructor_and_normalization_endpoint_is_owned():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=witness.definition_registry();found={}
    for pin in witness.ARCHIVES:
        rows=witness.read_mixed_archive(pin)
        for name,source in witness.ENDPOINT_SOURCES.items():
            if witness.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==6 and found['truncation']==('AP057',159) and found['constructed']==('CV070',143)
    assert found['power_nonzero']==('AP010',120)
    with pytest.raises(ValueError):witness.read_mixed_archive(dict(witness.TRUNCATION_ARCHIVE,sha256='0'*64))


def test_source_and_archive_bytes_are_bound():
    pins=witness.exp_normalized_witness_source_pins();assert len(pins)==355
    for pin in witness.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_constructed_witness_without_new_induction():
    result=witness.prove_exp_normalized_witness()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=witness.prove_exp_normalized_witness()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
