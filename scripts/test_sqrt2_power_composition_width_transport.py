"""Cross-width composition keeps the same input, weights and low cutoff."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_composition_width_transport as transport


def test_exact_four_constructed_traces_and_both_all_row_invariants():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = transport.frozen_composition_width_transport_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==8 and len(premises)==1 and type(conclusion) is Exists
    assert transport.json_hash(encode_formula(target))==transport.TARGET_SHA256
    assert len(transport.canonical(encode_formula(target)))==20599
    c = transport.source_contract()
    assert c["width_order_required"] is c["four_actual_traces_constructed"] is True
    assert c["every_power_and_accumulation_row_preserved"] is c["coefficients_preserved_only_below_smaller_width"] is True
    assert c["same_actual_input_and_outer_weights"] is c["generic_weighted_transport_helper"] is True
    assert c["all_degree_product_equality"] is c["truncated_full_evaluation_equality"] is c["closes_IR072"] is False


def test_no_new_definition_or_unproved_property_in_computation_dag():
    registry = transport.definition_registry()
    assert transport.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_changed_weights_or_cutoff_is_rejected():
    for source in (transport.NAMED_SOURCE.replace("NatWeightedSeriesTrace(J,wb,wc,","NatWeightedSeriesTrace(J,wb,wb,"),
                   transport.NAMED_SOURCE.replace("Lt(i,H)","Lt(i,J)"),
                   transport.NAMED_SOURCE.replace("Le(H,J)","Le(J,H)")):
        with patch.object(transport,"NAMED_SOURCE",source),pytest.raises(ValueError):
            transport.frozen_composition_width_transport_target()


def test_helpers_and_owned_actual_power_and_weighted_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = transport.definition_registry()
    assert {name:transport.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in transport.HELPER_SOURCES.items()}==transport.HELPER_TARGET_SHA256
    found = set()
    for pin in transport.ARCHIVES:
        rows = transport.read_mixed_archive(pin)
        for name,source in transport.ENDPOINT_SOURCES.items():
            if transport.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [row for row in rows if row[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and matches[0][3]
            found.add(name)
    assert found==transport.ENDPOINT_SOURCES.keys()


def test_changed_actual_archive_is_rejected():
    for original in transport.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                transport.read_mixed_archive(changed)


def test_finite_power_and_weighted_rows_and_omitted_tail_counterexample():
    def compute(a,H,w):
        powers = [[int(i==0) for i in range(H)]]
        sums = [[0]*H]
        for c in w:
            b = powers[-1]
            sums.append([s+c*v for s,v in zip(sums[-1],b)])
            powers.append([sum(a[j]*b[i-j] for j in range(len(a)) if 0<=i-j<H) for i in range(H)])
        return powers,sums
    for H in range(5):
        for J in range(H,7):
            for K in range(5):
                a,w = [1,2,0,3],[k+1 for k in range(K)]
                small,large = compute(a,H,w),compute(a,J,w)
                assert all(s==l[:H] for first,second in zip(small,large) for s,l in zip(first,second))
    small,large = compute([1,1],1,[1,1]),compute([1,1],2,[1,1])
    assert small[1][-1]==large[1][-1][:1] and sum(small[1][-1])!=sum(large[1][-1])


def test_ordinary_replay_and_forged_power_transport_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = transport.prove_composition_width_transport()
    assert result.receipt.target==transport.frozen_composition_width_transport_target()
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(transport.ENDPOINT_SOURCES["power_width"],registry=transport.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
