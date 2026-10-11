"""Exact natural sum splitting, arbitrary lengths and rejected forgeries."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_sum_splitting as split


def test_exact_unconditional_target_constructs_three_sums():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = split.frozen_sum_splitting_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==4 and not premises and type(conclusion) is Exists
    assert split.json_hash(encode_formula(target))==split.TARGET_SHA256
    assert len(split.canonical(encode_formula(target)))==4866
    contract = split.source_contract()
    assert contract["all_three_sum_values_constructed"] is contract["actual_shifted_tail"] is True
    assert contract["natural_convolution_associativity"] is contract["closes_IR072"] is False
    assert contract["new_definition_ids"]==[]


def test_all_stride_concatenation_and_raw_bridge_have_exact_asts():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = split.definition_registry()
    assert {name:split.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in split.HELPER_SOURCES.items()}==split.HELPER_TARGET_SHA256
    assert "forall n ab ac o t m x y z" in split.HELPER_SOURCES["concatenate"]
    assert "o+t*m" in split.HELPER_SOURCES["concatenate"]
    assert "NatAffineSum(ab,ac,0,1,L,x)" in split.HELPER_SOURCES["raw_as_affine"]


def test_wrong_total_or_wrong_tail_offset_is_rejected():
    for wrong in (split.NAMED_SOURCE.replace("z=x+y","z=x*y"),split.NAMED_SOURCE.replace("ab,ac,m,1,n,y","ab,ac,n,1,n,y")):
        with patch.object(split,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            split.frozen_sum_splitting_target()


def test_actual_ancestor_endpoints_are_unique_full_formulas():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    rows = split.read_archive(split.FUBINI_ARCHIVE)
    r = split.definition_registry()
    for source in split.ENDPOINT_SOURCES.values():
        formula = encode_formula(parse_named(source,registry=r))
        assert sum(row[1]==formula for row in rows)==1


def test_changed_parent_archive_hash_is_rejected():
    for field in ("sha256","raw_sha256","bundle_sha256","target_ast_sha256"):
        changed = dict(split.FUBINI_ARCHIVE)
        changed[field] = "0"*64
        with pytest.raises(ValueError):
            split.read_archive(changed)


def test_finite_splitting_model_all_zero_lengths_and_zero_strides():
    def beta(b,c,i):
        return b % (1+(i+1)*c)
    for b,c,o,t,m,n in product(range(5),range(3),range(3),range(3),range(5),range(5)):
        prefix = sum(beta(b,c,o+t*i) for i in range(m))
        tail = sum(beta(b,c,(o+t*m)+t*j) for j in range(n))
        whole = sum(beta(b,c,o+t*i) for i in range(m+n))
        assert whole==prefix+tail
    assert sum(beta(17,3,2+j) for j in range(3))!=sum(beta(17,3,3+j) for j in range(3))


def test_guarded_split_replay_and_rejection_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = split.prove_sum_splitting()
    assert result.receipt.target==split.frozen_sum_splitting_target()
    assert len(result.bundle.nodes)==120
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==5872
    assert result.provenance["new_induction_count"]==1
    assert result.provenance["all_affine_sums_concatenate"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
