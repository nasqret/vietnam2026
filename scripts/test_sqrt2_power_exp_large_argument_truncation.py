"""Supplied sums retain exact cutoff, normalization and finite error evidence."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_large_argument_truncation as truncation


def test_exact_truncation_statement_keeps_supplied_computations():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And
    from peano_lab.library.proof_bundle import encode_formula
    target=truncation.frozen_exp_large_argument_truncation_target();n,premises,conclusion=strip_target(target)
    assert n==12 and len(premises)==8 and type(conclusion) is And
    assert len(truncation.canonical(encode_formula(target)))==6132
    c=truncation.source_contract();assert c['supplied_table_head_sums_and_power_preserved'] is c['actual_tail_identified_by_value_uniqueness'] is True
    assert c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_eleven_existing_definitions_keep_the_exact_dag():
    registry=truncation.definition_registry();source=truncation.source_registry();seen=set();ids=set()
    assert len(registry)==11
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert truncation.source_contract()['new_definition_ids']==[]


def test_changed_cutoff_power_head_sum_or_bound_is_rejected():
    source=truncation.NAMED_SOURCE;registry=truncation.definition_registry()
    for changed in (source.replace('Le(2*L,K)','Le(L,K)'),source.replace('Pow(2,m,p)','Pow(3,m,p)'),
                    source.replace('BetaAt(ab,ac,K,a0)','BetaAt(ab,ac,0,a0)'),
                    source.replace('Sum(ab,ac,K+m,s)','Sum(ab,ac,S(K+m),s)'),
                    source.replace('Sum(ab,ac,S((K+m)+N),t)','Sum(ab,ac,(K+m)+N,t)'),
                    source.replace('p*s+2*a0','p*s+a0')):
        assert changed!=source
        with patch.object(truncation,'NAMED_SOURCE',changed),pytest.raises(ValueError):truncation.frozen_exp_large_argument_truncation_target(_registry=registry)


def test_exact_rational_models_include_empty_prefix_and_large_arguments():
    from fractions import Fraction
    from math import factorial
    examples=0;empty=0
    for d in (1,2,3):
        for L in range(4):
            for x in range(L*d+1):
                for K in (2*L,2*L+1):
                    for m in (0,1,4):
                        for N in (0,2,5):
                            values=[Fraction(x,d)**j/factorial(j) for j in range(K+m+N+1)]
                            a0,p=values[K],2**m;s,t=sum(values[:K+m]),sum(values)
                            assert s<=t and p*t<=p*s+2*a0
                            examples+=1;empty+=K+m==0
    assert examples==864 and empty==9


def test_each_endpoint_has_its_actual_owned_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=truncation.definition_registry();found={}
    for pin in truncation.ARCHIVES:
        rows=truncation.read_mixed_archive(pin)
        for name,source in truncation.ENDPOINT_SOURCES.items():
            if truncation.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==7 and found['decay']==('AP054',137) and found['finish_bound'][0]=='CV100'
    with pytest.raises(ValueError):truncation.read_mixed_archive(dict(truncation.DECAY_ARCHIVE,sha256='0'*64))


def test_source_and_archive_bytes_are_bound():
    pins=truncation.exp_large_argument_truncation_source_pins();assert len(pins)==349
    for pin in truncation.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_supplied_truncation_certificate_without_new_induction():
    result=truncation.prove_exp_large_argument_truncation()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=truncation.prove_exp_large_argument_truncation()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
