"""Actual proof and fail-closed evidence for the all-natural two-square root."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v17 as v17
from peano_lab.library.proof_bundle import ProofBundle, decode_proof_bundle
from peano_lab.library.two_square_complete_closure import (
    EXPECTED_TWO_SQUARE_BODY_ONLY_COUNT,
    EXPECTED_TWO_SQUARE_BODY_ONLY_NAMES_SHA256,
    EXPECTED_TWO_SQUARE_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_TWO_SQUARE_BUNDLE_BYTES,
    EXPECTED_TWO_SQUARE_BUNDLE_SHA256,
    EXPECTED_TWO_SQUARE_CHECKED_PARENT_COUNT,
    EXPECTED_TWO_SQUARE_DEPENDENCY_EDGE_COUNT,
    EXPECTED_TWO_SQUARE_ORDERED_NAMES_SHA256,
    EXPECTED_TWO_SQUARE_QR_BODY_COUNT,
    EXPECTED_TWO_SQUARE_REBUILT_BODY_COUNT,
    EXPECTED_TWO_SQUARE_REBUILT_NAMES_SHA256,
    EXPECTED_TWO_SQUARE_ROOT_NODE_ID,
    EXPECTED_TWO_SQUARE_ROOT_STATEMENT_SHA256,
    EXPECTED_TWO_SQUARE_SURFACE_SHA256,
    EXPECTED_TWO_SQUARE_THEOREM_COUNT,
    TWO_SQUARE_ROOT_NAME,
    TwoSquareCompleteClosureError,
    assemble_two_square_proof_bundle,
    check_two_square_proof_bundle,
    checked_two_square_proof_bundle,
    construct_two_square_body_microbatch,
    replay_two_square_closed_theorem,
    set_two_square_bundle_source,
    two_square_closure_plan,
)


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / (
    "research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json"
)


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_two_square_proof_bundle()


def test_two_square_plan_seals_the_exact_immutable_alpha_v17_surface() -> None:
    plan = two_square_closure_plan()

    assert plan.root == TWO_SQUARE_ROOT_NAME
    assert plan.parent_alpha_identity_sha256 == v17.ALPHA_V17_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_TWO_SQUARE_THEOREM_COUNT == 517
    assert len(plan.pending_rows) == EXPECTED_TWO_SQUARE_BODY_ONLY_COUNT == 140
    assert len(plan.rebuilt_rows) == EXPECTED_TWO_SQUARE_REBUILT_BODY_COUNT == 161
    assert len(plan.rows) - len(plan.pending_rows) == (
        EXPECTED_TWO_SQUARE_CHECKED_PARENT_COUNT
    )
    assert EXPECTED_TWO_SQUARE_CHECKED_PARENT_COUNT == 377
    assert len(plan.rows) - len(plan.rebuilt_rows) == EXPECTED_TWO_SQUARE_QR_BODY_COUNT
    assert EXPECTED_TWO_SQUARE_QR_BODY_COUNT == 356
    assert plan.dependency_edge_count == EXPECTED_TWO_SQUARE_DEPENDENCY_EDGE_COUNT == 1_599
    assert plan.ordered_names_sha256 == EXPECTED_TWO_SQUARE_ORDERED_NAMES_SHA256
    assert plan.body_only_names_sha256 == EXPECTED_TWO_SQUARE_BODY_ONLY_NAMES_SHA256
    assert plan.rebuilt_names_sha256 == EXPECTED_TWO_SQUARE_REBUILT_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_TWO_SQUARE_SURFACE_SHA256
    assert plan.rows[-1].node_id == EXPECTED_TWO_SQUARE_ROOT_NODE_ID == 516
    assert plan.rows[-1].statement_sha256 == EXPECTED_TWO_SQUARE_ROOT_STATEMENT_SHA256


def test_two_square_closed_proof_never_changes_release_or_stable_authority() -> None:
    plan = two_square_closure_plan()
    root = v17.ALPHA_EDITION.by_name[plan.root]

    assert root.evidence is v17.EvidenceStatus.BODY_CHECKED
    assert not root.checked_use
    assert v17.entry(plan.root, edition="stable") is None
    assert Counter(item.evidence.value for item in v17.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 484,
        "body_checked": 757,
    }


def test_two_square_body_microbatch_checks_actual_proofs_under_original_caps() -> None:
    names = tuple(row.name for row in two_square_closure_plan().rebuilt_rows[:3])
    batch = construct_two_square_body_microbatch(names)

    assert tuple(row.name for row in batch.rows) == names
    assert 0 < batch.proof_nodes < 125_000
    assert 0 < batch.proof_objects < 25_000
    assert len(batch.rows) <= 16


@pytest.mark.parametrize(
    "names,message",
    (
        ((), "1..16"),
        (("foreign_theorem",), "invents"),
        ((TWO_SQUARE_ROOT_NAME,), "lacks exact predecessor"),
    ),
)
def test_two_square_body_microbatch_rejects_false_schedule(names, message: str) -> None:
    with pytest.raises(TwoSquareCompleteClosureError, match=message):
        construct_two_square_body_microbatch(names)


def test_two_square_microbatch_rejects_more_than_sixteen_actual_bodies() -> None:
    names = tuple(row.name for row in two_square_closure_plan().rebuilt_rows[:17])

    with pytest.raises(TwoSquareCompleteClosureError, match="1..16"):
        construct_two_square_body_microbatch(names)


def test_two_square_assembly_rejects_absent_actual_proof_bodies() -> None:
    with pytest.raises(TwoSquareCompleteClosureError, match="lacks its exact"):
        assemble_two_square_proof_bundle(())


def test_two_square_artifact_contains_the_complete_canonical_checked_graph(actual_bundle) -> None:
    payload = ARTIFACT.read_bytes()
    bundle, receipt = actual_bundle

    assert len(payload) == EXPECTED_TWO_SQUARE_BUNDLE_BYTES
    assert sha256(payload).hexdigest() == EXPECTED_TWO_SQUARE_BUNDLE_SHA256
    decoded, target = decode_proof_bundle(payload.decode("utf-8"))
    assert decoded == bundle
    assert target == bundle.nodes[-1].target
    assert receipt.node_count == receipt.kernel_calls == 517
    assert receipt.dependency_edges == 1_599
    assert receipt.total_body_nodes == EXPECTED_TWO_SQUARE_BUNDLE_BODY_PROOF_NODES


def test_two_square_bundle_rejects_mutated_root_formula(actual_bundle) -> None:
    bundle, _receipt = actual_bundle

    with pytest.raises(TwoSquareCompleteClosureError, match="universal root"):
        check_two_square_proof_bundle(bundle, Eq(Zero(), Zero()))


def test_two_square_bundle_rejects_false_actual_proof_body(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    false = replace(bundle.nodes[-1], body=EqRefl(Zero()))
    mutated = ProofBundle(bundle.nodes[:-1] + (false,), bundle.root)

    with pytest.raises(TwoSquareCompleteClosureError, match="kernel rejected"):
        check_two_square_proof_bundle(mutated, bundle.nodes[-1].target)


def test_two_square_unknown_theorem_replay_fails_without_authority() -> None:
    with pytest.raises(TwoSquareCompleteClosureError, match="unknown theorem"):
        replay_two_square_closed_theorem("unknown_theorem")


def test_two_square_missing_actual_artifact_fails_closed(tmp_path: Path) -> None:
    set_two_square_bundle_source(tmp_path / "missing.json")
    try:
        with pytest.raises(TwoSquareCompleteClosureError, match="unavailable"):
            checked_two_square_proof_bundle()
    finally:
        set_two_square_bundle_source(None)


def test_two_square_mutated_actual_artifact_fails_closed(tmp_path: Path) -> None:
    destination = tmp_path / "mutated.json"
    actual = ARTIFACT.read_bytes()
    destination.write_bytes(actual[:-1] + b" ")
    set_two_square_bundle_source(destination)
    try:
        with pytest.raises(TwoSquareCompleteClosureError, match="frozen provenance"):
            checked_two_square_proof_bundle()
    finally:
        set_two_square_bundle_source(None)
