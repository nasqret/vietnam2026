"""Exact length alignment and replay of the actual Kummer power-add body."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_weights as weights


def test_exact_constructed_convolution_weight_target_and_scope():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = weights.frozen_convolution_weights_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==3 and not premises and type(conclusion) is Exists
    assert weights.json_hash(encode_formula(target))==weights.TARGET_SHA256
    assert len(weights.canonical(encode_formula(target)))==15985
    c = weights.source_contract()
    assert c["three_geometric_tables_and_power_values_constructed"] is True
    assert c["all_in_range_convolution_weights_related"] is c["extra_multiplier_kept"] is True
    assert c["zero_multiplier_and_empty_lengths_allowed"] is True
    assert c["archived_power_add_metadata_is_authority"] is c["full_convolution_evaluation"] is c["closes_IR072"] is False


def test_exact_geometric_package_and_shared_definition_dag():
    from sqrt2_power_definitions import parse_named
    r = weights.definition_registry()
    source = "forall t N. exists wb wc p. "+weights.data(("wb","wc"),"p","N")
    assert parse_named(source,registry=r)==parse_named(weights.GEOMETRIC_SOURCE,registry=r)
    assert weights.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_dropped_length_factor_or_changed_index_is_rejected():
    for source in (weights.NAMED_SOURCE.replace("c=t*(a*b)","c=a*b"),
                   weights.NAMED_SOURCE.replace("BetaAt(nb,nc,S k,c)","BetaAt(nb,nc,k,c)")):
        with patch.object(weights,"NAMED_SOURCE",source),pytest.raises(ValueError):
            weights.frozen_convolution_weights_target()


def test_exact_helpers_and_owned_kummer_power_add_endpoint():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = weights.definition_registry()
    assert {name:weights.json_hash(encode_formula(parse_named(source,registry=r)))
        for name,source in weights.HELPER_SOURCES.items()}==weights.HELPER_TARGET_SHA256
    found = set()
    for pin in weights.ARCHIVES:
        rows = weights.read_mixed_archive(pin)
        for name,source in weights.ENDPOINT_SOURCES.items():
            if weights.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,row in enumerate(rows) if row[1]==encode_formula(parse_named(source,registry=r))]
            assert len(matches)==1 and rows[matches[0]][3]
            if name=="power_add":
                assert pin["case"]=="kummer-power-add-v1" and matches[0]==168
            found.add(name)
    assert found==weights.ENDPOINT_SOURCES.keys()


def test_changed_actual_raw_or_wave_archive_is_rejected():
    for original in weights.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                weights.read_mixed_archive(changed)


def test_exact_convolution_weight_model_and_required_extra_multiplier():
    for t in range(5):
        for L in range(6):
            for M in range(6):
                a = [t**(L-i) for i in range(L+1)]
                b = [t**(M-j) for j in range(M+1)]
                c = [t**(L+M-k) for k in range(L+M+1)]
                assert a[-1]==b[-1]==c[-1]==1
                for i in range(L):
                    for j in range(M):
                        assert c[i+j+1]==t*a[i+1]*b[j+1]
    assert 3**(1+1-1)!=3**(1-1)*3**(1-1)


def test_guarded_proof_replays_and_rejects_forged_kummer_ancestor():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = weights.prove_convolution_weights()
    assert result.receipt.target==weights.frozen_convolution_weights_target()
    assert len(result.bundle.nodes)==135
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==7022
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    assert result.provenance["endpoint_archive_selection"]["power_add"]["original_node"]==168
    power_add = parse_named(weights.ENDPOINT_SOURCES["power_add"],registry=weights.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==power_add]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
