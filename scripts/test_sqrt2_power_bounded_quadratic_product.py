"""Positive bounded-product construction; no supplied output may hide a gap."""
from dataclasses import replace
from itertools import product
from unittest.mock import patch

import pytest

import sqrt2_power_bounded_quadratic_product as bounded


def test_exact_two_input_premises_and_thirteen_constructed_witnesses():
    from peano_lab.kernel.formulas import Forall,Imp,Exists,And
    from peano_lab.library.proof_bundle import encode_formula
    target = bounded.frozen_bounded_quadratic_product_target()
    assert bounded.json_hash(encode_formula(target))==bounded.TARGET_SHA256
    assert len(bounded.canonical(encode_formula(target)))==10240
    for kind,count in ((Forall,10),(Imp,2),(Exists,13)):
        for _ in range(count):
            assert type(target) is kind
            target = target.consequent if kind is Imp else target.body
    assert type(target) is And
    contract = bounded.source_contract()
    for key in ("supplied_trace_required","supplied_power_required","supplied_terminal_required",
                "positive_height_required","original_HA_checked","real_interpretation","closes_IR046","closes_IR072"):
        assert contract[key] is False
    assert contract["new_definition_ids"]==[]


def test_forgetful_bridge_and_power_existence_are_exact_expanded_formulas():
    from sqrt2_power_definitions import parse_named
    from peano_lab.library.proof_bundle import encode_formula
    registry = bounded.definition_registry()
    assert bounded.json_hash(encode_formula(parse_named(bounded.BRIDGE_SOURCE,registry=registry)))==bounded.BRIDGE_SHA256
    assert bounded.json_hash(encode_formula(parse_named(bounded.POWER_SOURCE,registry=registry)))==bounded.POWER_TARGET_SHA256
    assert registry["IQuadProductTrace"].stable_id=="ND0392"
    assert registry["IQuadCanonicalTrace"].stable_id=="ND0397"


def test_dropped_bounds_or_nonzero_or_changed_power_target_rejected():
    for old in (bounded.named("IQuadFactorHeightBound",*bounded.F,"L","H")+" -> ",
                bounded.named("IQuadNonzeroFactors",*bounded.F,"L")+" -> "):
        with patch.object(bounded,"NAMED_SOURCE",bounded.NAMED_SOURCE.replace(old,"")),pytest.raises(ValueError):
            bounded.frozen_bounded_quadratic_product_target()
    with patch.object(bounded,"NAMED_SOURCE",bounded.NAMED_SOURCE.replace("Pow(H,L,N)","Pow(H,S L,N)")),pytest.raises(ValueError):
        bounded.frozen_bounded_quadratic_product_target()


def test_actual_power_totality_cone_and_hostile_archive_hash():
    ids,rows = bounded.inert_power_exists_rows()
    assert len(ids)==109
    assert len(bounded.canonical(rows))==165506
    assert bounded.json_hash(rows)==bounded.POWER_ROWS_SHA256
    assert bounded.json_hash(rows[-1][1])==bounded.POWER_TARGET_SHA256
    with patch.object(bounded,"V28_ARTIFACT_SHA256","0"*64),pytest.raises(ValueError):
        bounded.inert_power_exists_rows()


def test_merge_preserves_all_three_exact_roots_and_ordered_dependencies():
    rows,endpoints,total,depth = bounded.merge_actual_rows()
    assert len(rows)==295
    for pin in bounded.ARCHIVES:
        assert bounded.json_hash(rows[endpoints[pin["case"]]][1])==pin["target_ast_sha256"]
    assert bounded.json_hash(rows[endpoints["power_exists"]][1])==bounded.POWER_TARGET_SHA256
    for index,row in enumerate(rows):
        assert len(set(row[2]))==len(row[2]) and all(d<index for d in row[2])
    assert total<200000 and depth<=256


def test_host_finite_bounded_nonzero_products_include_empty_zero_bound():
    from test_sqrt2_power_quadratic_height import canonical_product,mass
    from test_sqrt2_power_quadratic_product_trace import nonzero
    choices = ((1,0,0,0),(0,1,0,0),(0,0,1,0),(1,0,1,0),(1,1,1,0))
    for length in range(4):
        for factors in product(choices,repeat=length):
            H = max((mass(A) for A in factors),default=0)
            value = (1,0,0,0)
            for A in factors:
                assert nonzero(A)
                value = canonical_product(value,A)
            assert nonzero(value) and mass(value)<=H**length


def test_guarded_complete_positive_certificate_and_negative_controls():
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.proof_bundle import check_proof_bundle,ProofBundleError
    from sqrt2_power_binary_dag import BinaryDAGLimits
    result = bounded.prove_bounded_quadratic_product()
    assert result.receipt.target==bounded.frozen_bounded_quadratic_product_target()
    assert len(result.bundle.nodes)==297 and result.receipt.total_body_nodes==86942
    assert result.provenance["constructed_bounded_nonzero_product"] is True
    assert result.provenance["new_axioms"]==[]
    assert result.provenance["independent_lean_checked"] is False
    forged = replace(result.bundle,nodes=tuple(replace(n,body=EqRefl(Zero()))
        if n.node_id==result.bundle.root else n for n in result.bundle.nodes))
    for bundle,target in ((result.bundle,Bot()),(forged,result.target)):
        with pytest.raises(ProofBundleError):
            check_proof_bundle(bundle,target,limits=BinaryDAGLimits().bundle_limits())
