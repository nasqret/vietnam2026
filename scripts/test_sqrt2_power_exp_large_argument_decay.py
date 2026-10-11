"""Effective finite large-argument tails with actual shifted computations."""
from unittest.mock import patch

import pytest
import sqrt2_power_exp_large_argument_decay as decay


def test_exact_decay_statement_retains_all_computations_and_both_bounds():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import And,Exists
    from peano_lab.library.proof_bundle import encode_formula
    registry=decay.definition_registry();target=decay.frozen_exp_large_argument_decay_target(_registry=registry)
    n,premises,conclusion=strip_target(target)
    assert n==8 and len(premises)==4 and type(conclusion) is Exists
    assert len(decay.canonical(encode_formula(target)))==6524
    for _ in decay.OUTPUTS:assert type(conclusion) is Exists;conclusion=conclusion.body
    fields=[]
    for _ in range(8):assert type(conclusion) is And;fields.append(conclusion.left);conclusion=conclusion.right
    fields.append(conclusion);names=tuple(reversed(decay.PARAMETERS+decay.OUTPUTS))
    assert fields==[parse_named(part,names,registry) for part in decay.PARTS]
    c=decay.source_contract();assert c['actual_power_heads_slice_and_sum_constructed'] is c['uniform_in_extra_finite_horizon'] is True
    assert c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_ten_existing_definitions_keep_the_exact_conservative_dag():
    registry=decay.definition_registry();source=decay.source_registry();seen=set();ids=set()
    assert len(registry)==10
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decay.source_contract()['new_definition_ids']==[]


def test_changed_cutoff_power_source_head_or_tail_bound_is_rejected():
    source=decay.NAMED_SOURCE;registry=decay.definition_registry()
    for changed in (source.replace('Le(2*L,K)','Le(L,K)'),source.replace('Pow(2,m,p)','Pow(3,m,p)'),
                    source.replace('BetaAt(tb,tc,K,a0)','BetaAt(tb,tc,0,a0)'),
                    source.replace('K+m,1,ub,uc','K,1,ub,uc'),source.replace('Le(p*s,2*a0)','Le(p*s,a0)'),
                    source.replace('tb,tc,(K+m)+N','tb,tc,K+m')):
        assert changed!=source
        with patch.object(decay,'NAMED_SOURCE',changed),pytest.raises(ValueError):decay.frozen_exp_large_argument_decay_target(_registry=registry)


def test_exact_rational_models_include_large_arguments_and_zero_margins():
    from fractions import Fraction
    from math import factorial
    examples=0
    for d in (1,2,3):
        for L in range(4):
            for x in range(L*d+1):
                for K in (2*L,2*L+1):
                    for m in (0,1,4):
                        for N in (0,2,5):
                            values=[Fraction(x,d)**j/factorial(j) for j in range(K+m+N+1)]
                            a0,a,p=values[K],values[K+m],2**m;tail=values[K+m:]
                            assert p*a<=a0 and p*sum(tail)<=2*a0
                            assert all(2*tail[j+1]<=tail[j] for j in range(N));examples+=1
    assert examples==864


def test_each_named_endpoint_resolves_to_an_actual_owned_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decay.definition_registry();found={}
    for pin in decay.ARCHIVES:
        rows=decay.read_mixed_archive(pin)
        for name,source in decay.ENDPOINT_SOURCES.items():
            if decay.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==14 and found['tail']==('AP052',122) and found['decay']==('AP053',35)
    with pytest.raises(ValueError):decay.read_mixed_archive(dict(decay.DECAY_ARCHIVE,sha256='0'*64))


def test_source_and_archive_bytes_are_bound():
    pins=decay.exp_large_argument_decay_source_pins();assert len(pins)==347
    for pin in decay.ARCHIVES:assert pins[pin['path']]['sha256']==pin['sha256']


def test_complete_large_argument_decay_certificate_without_new_induction():
    result=decay.prove_exp_large_argument_decay()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==0 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=decay.prove_exp_large_argument_decay()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
