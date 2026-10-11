"""The actual full convolution total, including capture-free shared sum data."""
from dataclasses import replace
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_total as total


def test_exact_unconditional_convolution_and_three_sums():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = total.frozen_convolution_total_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==6 and not premises and type(conclusion) is Exists
    assert total.json_hash(encode_formula(target))==total.TARGET_SHA256
    assert len(total.canonical(encode_formula(target)))==7262
    c = total.source_contract()
    assert c["actual_convolution_and_all_three_sum_values_constructed"] is c["full_convolution_sum_product"] is True
    assert c["finite_fubini_replayed"] is c["column_zero_tail_proved"] is c["empty_inputs_allowed"] is True
    assert c["output_length"]=="L+M"
    assert c["full_convolution_evaluation"] is c["analytic_limit_claim"] is c["closes_IR072"] is False


def test_unchanged_conservative_definition_dag():
    registry = total.definition_registry()
    assert total.source_contract()["new_definition_ids"]==[]
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_shared_sum_renaming_is_exact_and_cannot_capture_column_witness():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_cauchy_grid_sums import ALL_COLUMNS
    registry = total.definition_registry()
    original_context = tuple("x" if name=="y" else name for name in total.FIXED)
    original = parse_named(ALL_COLUMNS,original_context,registry)
    actual = parse_named(total.COLS,total.FIXED,registry)
    assert actual==original
    captured = parse_named(ALL_COLUMNS.replace("a*x","a*y"),total.FIXED,registry)
    assert captured!=original
    from peano_lab.library.proof_bundle import encode_formula
    changed_source = total.HELPER_SOURCES["column_entry"].replace(total.COLS,ALL_COLUMNS.replace("a*x","a*y"))
    assert total.json_hash(encode_formula(parse_named(changed_source,registry=registry)))!=total.HELPER_TARGET_SHA256["column_entry"]


def test_changed_output_length_or_product_is_rejected():
    for source in (total.NAMED_SOURCE.replace("Sum(rb,rc,L+M,z)","Sum(rb,rc,L,z)"),
                   total.NAMED_SOURCE.replace("z=x*y","z=x+y")):
        with patch.object(total,"NAMED_SOURCE",source),pytest.raises(ValueError):
            total.frozen_convolution_total_target()


def test_exact_helpers_and_actual_owned_fubini_body():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = total.definition_registry()
    assert {name:total.json_hash(encode_formula(parse_named(source,registry=registry)))
        for name,source in total.HELPER_SOURCES.items()}==total.HELPER_TARGET_SHA256
    found = set()
    for pin in total.ARCHIVES:
        actual = total.read_mixed_archive(pin)
        for name,source in total.ENDPOINT_SOURCES.items():
            if total.ENDPOINT_OWNERS[name]!=pin["case"]:
                continue
            matches = [i for i,r in enumerate(actual) if r[1]==encode_formula(parse_named(source,registry=registry))]
            assert len(matches)==1 and actual[matches[0]][3]
            found.add(name)
    assert found==total.ENDPOINT_SOURCES.keys()


def test_changed_actual_archives_are_rejected():
    for original in total.ARCHIVES:
        for key in ("sha256","target_ast_sha256"):
            changed = dict(original);changed[key] = "0"*64
            with pytest.raises(ValueError):
                total.read_mixed_archive(changed)


def test_finite_full_convolution_product_and_truncation_counterexample():
    for L in range(6):
        for M in range(6):
            for offset in range(3):
                a,b = [(i+offset)%5 for i in range(L)],[(2*j+offset)%7 for j in range(M)]
                c = [sum(a[i]*b[k-i] for i in range(L) if 0<=k-i<M) for k in range(L+M)]
                assert sum(c)==sum(a)*sum(b)
    assert sum([3,10])!=sum([1,2])*sum([3,4])


def test_ordinary_replay_and_forged_fubini_rejection():
    from sqrt2_power_definitions import parse_named
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = total.prove_convolution_total()
    assert result.receipt.target==total.frozen_convolution_total_target()
    assert len(result.bundle.nodes)==162
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==9597
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    target = parse_named(total.ENDPOINT_SOURCES["fubini"],registry=total.definition_registry())
    ancestors = [n.node_id for n in result.bundle.nodes if n.target==target]
    assert len(ancestors)==1
    for node_id in (result.bundle.root,ancestors[0]):
        forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
            if n.node_id==node_id else n for n in result.bundle.nodes))
        with pytest.raises(ProofBundleError):
            check_proof_bundle(forged,result.target,limits=BinaryDAGLimits().bundle_limits())
    with pytest.raises(ProofBundleError):
        check_proof_bundle(result.bundle,Bot(),limits=BinaryDAGLimits().bundle_limits())
