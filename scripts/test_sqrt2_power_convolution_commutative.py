"""Genuine reversal of finite sums and all-index natural commutativity."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_commutative as comm


def test_exact_unconditional_common_coefficient_target():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = comm.frozen_convolution_commutative_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==7 and not premises and type(conclusion) is Exists
    assert comm.json_hash(encode_formula(target))==comm.TARGET_SHA256
    assert len(comm.canonical(encode_formula(target)))==5407
    contract = comm.source_contract()
    assert contract["both_coefficients_constructed"] is True
    assert contract["arbitrary_input_lengths_and_index"] is True
    assert contract["natural_convolution_associativity"] is contract["closes_IR072"] is False
    assert contract["new_definition_ids"]==[]


def test_reversal_contract_is_a_pointwise_index_equation_not_a_sum_identity():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = comm.definition_registry()
    assert {name:comm.json_hash(encode_formula(parse_named(source,registry=registry))) for name,source in comm.HELPER_SOURCES.items()}==comm.HELPER_TARGET_SHA256
    relation = comm.HELPER_SOURCES["reverse"].split("(forall j k a b.",1)[1]
    assert "j+k=N" in relation and "a=b" in relation and "Sum(" not in relation
    for d in registry.values():
        assert set(d.conceptual_dependencies)<=registry.keys()


def test_changed_swapped_coefficient_index_is_rejected():
    wrong = comm.NAMED_SOURCE.replace("bb,bc,M,ab,ac,L,i,n","bb,bc,M,ab,ac,L,S i,n")
    assert wrong!=comm.NAMED_SOURCE
    with patch.object(comm,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
        comm.frozen_convolution_commutative_target()


def test_actual_ancestor_endpoint_coverage_and_exact_bodies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = comm.definition_registry()
    found = set()
    for pin in (comm.CONVOLUTION_ARCHIVE,comm.SPLIT_ARCHIVE):
        rows = comm.read_archive(pin)
        for name,source in comm.ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=registry))
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==comm.ENDPOINT_SOURCES.keys()


def test_parent_archive_forgery_controls():
    for original in (comm.CONVOLUTION_ARCHIVE,comm.SPLIT_ARCHIVE):
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                comm.read_archive(changed)


def test_finite_reversal_and_commutative_models_empty_lengths_and_far_indices():
    sequences = [list(row) for n in range(4) for row in product(range(3),repeat=n)]
    def coefficient(left,right,i):
        return sum(a*b for j,a in enumerate(left) for k,b in enumerate(right) if j+k==i)
    for left in sequences:
        assert sum(left)==sum(reversed(left))
        for right in sequences:
            for i in range(8):
                assert coefficient(left,right,i)==coefficient(right,left,i)
    assert coefficient([1,2],[3,4],0)!=coefficient([3,4],[1,2],1)


def test_guarded_reversal_and_commutativity_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = comm.prove_convolution_commutative()
    assert result.receipt.target==comm.frozen_convolution_commutative_target()
    assert len(result.bundle.nodes)==133
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6944
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["coefficientwise_natural_commutativity"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
