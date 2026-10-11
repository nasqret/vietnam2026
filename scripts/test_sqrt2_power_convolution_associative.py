"""Actual natural associativity with its necessary truncation-width premise."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_convolution_associative as assoc


def test_exact_target_constructs_two_inner_prefixes_and_common_nested_value():
    from sqrt2_power_native import strip_target
    from peano_lab.kernel.formulas import Exists
    from peano_lab.library.proof_bundle import encode_formula
    target = assoc.frozen_convolution_associative_target()
    binders,premises,conclusion = strip_target(target)
    assert binders==11 and len(premises)==1 and type(conclusion) is Exists
    assert assoc.json_hash(encode_formula(target))==assoc.TARGET_SHA256
    assert len(assoc.canonical(encode_formula(target)))==11548
    contract = assoc.source_contract()
    assert contract["coefficient_index_below_common_width_required"] is True
    assert contract["both_intermediate_prefixes_constructed"] is True
    assert contract["common_nested_product_value_constructed"] is True
    assert contract["exp_composition_recurrence"] is contract["closes_IR072"] is False


def test_exact_helper_targets_and_conditional_supplied_prefix_assembly():
    from sqrt2_power_definitions import parse_named
    from sqrt2_power_native import strip_target
    from peano_lab.library.proof_bundle import encode_formula
    r = assoc.definition_registry()
    assert {name:assoc.json_hash(encode_formula(parse_named(source,registry=r))) for name,source in assoc.HELPER_SOURCES.items()}==assoc.HELPER_TARGET_SHA256
    binders,premises,conclusion = strip_target(parse_named(assoc.HELPER_SOURCES["associate"],registry=r))
    assert binders==15 and len(premises)==3
    assert assoc.source_contract()["new_definition_ids"]==[]
    for d in r.values():
        assert set(d.conceptual_dependencies)<=r.keys()


def test_removed_width_premise_or_wrong_output_coefficient_is_rejected():
    for wrong in (assoc.NAMED_SOURCE.replace("Lt(i,W) -> ",""),assoc.NAMED_SOURCE.replace("pb,pc,W,cb,cc,K,i,z","pb,pc,W,cb,cc,K,S i,z")):
        assert wrong!=assoc.NAMED_SOURCE
        with patch.object(assoc,"NAMED_SOURCE",wrong),pytest.raises(ValueError):
            assoc.frozen_convolution_associative_target()


def test_actual_five_archive_dependency_endpoints_are_exact():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    r = assoc.definition_registry()
    found = set()
    for pin in assoc.ARCHIVES:
        rows = assoc.read_archive(pin)
        for name,source in assoc.ENDPOINT_SOURCES.items():
            formula = encode_formula(parse_named(source,registry=r))
            matches = [row for row in rows if row[1]==formula]
            assert len(matches)<=1
            if matches:
                assert matches[0][3]
                found.add(name)
    assert found==assoc.ENDPOINT_SOURCES.keys()
    assert {pin["case"] for pin in assoc.ARCHIVES}=={"CV003","CV008","CV010","CV012","CV013"}


def test_forged_actual_dependency_archives_are_rejected():
    for original in assoc.ARCHIVES:
        for field in ("sha256","bundle_sha256","target_ast_sha256"):
            changed = dict(original)
            changed[field] = "0"*64
            with pytest.raises(ValueError):
                assoc.read_archive(changed)


def test_finite_truncated_associativity_and_explicit_width_counterexample():
    seqs = [list(row) for n in range(3) for row in product(range(2),repeat=n)]
    def coefficient(a,b,i):
        return sum(x*y for j,x in enumerate(a) for k,y in enumerate(b) if j+k==i)
    def prefix(a,b,width):
        return [coefficient(a,b,i) for i in range(width)]
    for a,b,c in product(seqs,repeat=3):
        for W in range(1,6):
            ab,bc = prefix(a,b,W),prefix(b,c,W)
            for i in range(W):
                assert coefficient(ab,c,i)==coefficient(a,bc,i)
    # At i=W, asymmetric truncation can discard a needed intermediate term.
    a,b,c,W,i = [1,1],[1],[1],1,1
    assert coefficient(prefix(a,b,W),c,i)==0
    assert coefficient(a,prefix(b,c,W),i)==1


def test_guarded_associativity_replays_full_ancestors_and_rejects_forgery():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = assoc.prove_convolution_associative()
    assert result.receipt.target==assoc.frozen_convolution_associative_target()
    assert len(result.bundle.nodes)==168
    assert sum((n.fuel-16)//8 for n in result.bundle.nodes)==10172
    assert result.provenance["actual_natural_convolution_associativity"] is True
    assert result.provenance["new_induction_count"]==0
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["merged_rows_only_exact_byte_deduplication"] is True
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
