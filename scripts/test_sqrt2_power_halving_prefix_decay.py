"""Actual bounded halving prefixes, including zero heads and zero indices."""
from unittest.mock import patch

import pytest
import sqrt2_power_halving_prefix_decay as decay


def test_exact_decay_statement_requires_power_and_decoded_values():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target=decay.frozen_halving_prefix_decay_target();n,premises,conclusion=strip_target(target)
    assert n==7 and len(premises)==5 and type(conclusion) is Exists
    assert len(decay.canonical(encode_formula(target)))==3117
    c=decay.source_contract();assert c['supplied_power_and_decoded_entries_required'] is True
    assert c['new_induction_count']==1 and c['large_ground_power_materialized'] is False
    assert c['infinite_tail_or_exponential_claimed'] is c['closes_IR072'] is False


def test_seven_existing_definitions_are_exact_and_topological():
    registry=decay.definition_registry();source=decay.source_registry();seen=set();ids=set()
    assert set(registry)=={'Le','Lt','BetaAt','Repeat','Product','Pow','NatRatioBoundPrefix'}
    for name,spec in registry.items():
        assert spec==source[name] and set(spec.conceptual_dependencies)<=seen and spec.stable_id not in ids
        seen.add(name);ids.add(spec.stable_id)
    assert decay.source_contract()['new_definition_ids']==[]


def test_changed_power_horizon_head_index_or_bound_is_rejected():
    source=decay.NAMED_SOURCE;registry=decay.definition_registry()
    for changed in (source.replace('Pow(2,','Pow(3,'),source.replace('1,S N','1,N'),
                    source.replace('BetaAt(ab,ac,0,a0)','BetaAt(ab,ac,1,a0)'),
                    source.replace('BetaAt(ab,ac,k,a)','BetaAt(ab,ac,S k,a)'),
                    source.replace('Le(k,N)','Le(N,k)'),source.replace('Le(p*a,a0)','Le(p*a,a)')):
        assert changed!=source
        with patch.object(decay,'NAMED_SOURCE',changed),pytest.raises(ValueError):
            decay.frozen_halving_prefix_decay_target(_registry=registry)


def test_actual_finite_integer_models_include_zero_head_and_last_index():
    count=0
    for a0 in range(30):
        for N in range(9):
            values=[a0]
            for _ in range(N):values.append(values[-1]//2)
            assert all(2*values[i+1]<=values[i] for i in range(N))
            for k,a in enumerate(values):assert 2**k*a<=a0;count+=1
    assert count>1000


def test_missing_ratio_power_or_index_guard_has_counterexamples():
    assert not 2**1*2<=2  # Unrestricted next value.
    assert not 3*2<=2  # Not the actual power at index zero.
    assert not 2**1*1<=1  # Length-one halving condition says nothing at index one.


def test_actual_owned_endpoints_and_source_archives_are_bound():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry=decay.definition_registry();found={};pins=decay.halving_prefix_decay_source_pins()
    assert len(pins)==342
    for pin in decay.ARCHIVES:
        assert pins[pin['path']]['sha256']==pin['sha256'];rows=decay.read_mixed_archive(pin)
        for name,source in decay.ENDPOINT_SOURCES.items():
            if decay.ENDPOINT_OWNERS[name]!=pin['case']:continue
            exact=encode_formula(parse_named(source,registry=registry));matches=[i for i,row in enumerate(rows) if row[1]==exact]
            assert len(matches)==1 and rows[matches[0]][3];found[name]=(pin['case'],matches[0])
    assert len(found)==11 and found['power_zero']==('AP010',112) and found['power_step']==('AP010',113)
    with pytest.raises(ValueError):decay.read_mixed_archive(dict(decay.COMPARISON_ARCHIVE,sha256='0'*64))


def test_complete_actual_decay_certificate_with_one_new_induction():
    result=decay.prove_halving_prefix_decay()
    assert result.receipt.target==result.target and result.receipt.kernel_calls==len(result.bundle.nodes)
    assert result.provenance['new_induction_count']==1 and result.provenance['new_axioms']==[]
    assert result.provenance['independent_lean_checked'] is False


def test_false_target_and_forged_induction_body_are_rejected():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    from run_sqrt2_power_wave import check_forged_root_rejection
    result=decay.prove_halving_prefix_decay()
    with pytest.raises(ProofBundleError):check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
    check_forged_root_rejection(result.bundle)
