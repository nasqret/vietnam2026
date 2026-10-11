"""Actual zero padding transports a finite Sum witness; never unconditional."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_sum_zero_tail as tail


def test_exact_target_requires_both_actual_prefix_and_zero_tail():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = tail.frozen_sum_zero_tail_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==5 and len(premises)==2 and type(conclusion) is Exists
    assert tail.json_hash(encode_formula(target))==tail.TARGET_SHA256
    assert len(tail.canonical(encode_formula(target)))==3133
    contract = tail.source_contract()
    assert contract["actual_prefix_sum_required"] is contract["actual_zero_tail_required"] is True
    assert contract["longer_sum_witness_constructed"] is True
    assert contract["natural_convolution_associativity"] is contract["closes_IR072"] is False


def test_zero_sum_helper_is_exact_and_existing_aliases_remain_conservative():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = tail.definition_registry()
    assert tail.json_hash(encode_formula(parse_named(tail.ZERO_SUM_SOURCE,registry=r)))==tail.ZERO_SUM_SHA256
    assert tail.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_wrong_tail_value_or_wrong_extended_total_is_rejected():
    for wrong in (tail.NAMED_SOURCE.replace("m+j,0)","m+j,1)"),tail.NAMED_SOURCE.replace("Sum(ab,ac,m+n,x)","Sum(ab,ac,m+n,S x)")):
        assert wrong!=tail.NAMED_SOURCE
        with patch.object(tail,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            tail.frozen_sum_zero_tail_target()


def test_actual_parent_endpoints_cover_exact_zero_tail_dependencies():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = tail.definition_registry()
    found = set()
    for pin in (tail.SPLIT_ARCHIVE,tail.LINEARITY_ARCHIVE):
        rows = tail.read_archive(pin)
        for name,source in tail.ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=r))
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==tail.ENDPOINT_SOURCES.keys()


def test_forged_actual_parent_records_are_rejected():
    for original in (tail.SPLIT_ARCHIVE,tail.LINEARITY_ARCHIVE):
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                tail.read_archive(changed)


def test_zero_tail_model_and_missing_premise_counterexample():
    for n in range(6):
        for m in range(5):
            for prefix in product(range(3),repeat=m):
                extended = list(prefix)+[0]*n
                assert sum(extended)==sum(prefix)
    # A zero at the old first position does not imply an all-zero appended tail.
    assert sum([0,1])!=sum([0])
    assert sum([2,3,1])!=sum([2,3])


def test_guarded_zero_tail_transport_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = tail.prove_sum_zero_tail()
    assert result.receipt.target==tail.frozen_sum_zero_tail_target()
    assert len(result.bundle.nodes)==123
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==6303
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["all_zero_tail_sum_transport"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
