"""Independent constructive audit of the complete Lagrange proof artifact."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v17 as v17
from peano_lab.library.four_square_complete_closure import (
    EXPECTED_FOUR_SQUARE_BODY_ONLY_COUNT,
    EXPECTED_FOUR_SQUARE_BODY_ONLY_NAMES_SHA256,
    EXPECTED_FOUR_SQUARE_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_FOUR_SQUARE_BUNDLE_BYTES,
    EXPECTED_FOUR_SQUARE_BUNDLE_SHA256,
    EXPECTED_FOUR_SQUARE_CHECKED_PARENT_COUNT,
    EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT,
    EXPECTED_FOUR_SQUARE_HA_BODY_COUNT,
    EXPECTED_FOUR_SQUARE_ORDERED_NAMES_SHA256,
    EXPECTED_FOUR_SQUARE_QR_REUSED_BODY_COUNT,
    EXPECTED_FOUR_SQUARE_RECONSTRUCTED_BODY_COUNT,
    EXPECTED_FOUR_SQUARE_ROOT_STATEMENT_SHA256,
    EXPECTED_FOUR_SQUARE_SURFACE_SHA256,
    EXPECTED_FOUR_SQUARE_THEOREM_COUNT,
    FOUR_SQUARE_ROOT_NAME,
    FourSquareCompleteClosureError,
    assemble_four_square_proof_bundle,
    check_four_square_proof_bundle,
    checked_four_square_proof_bundle,
    construct_four_square_body_microbatch,
    four_square_complete_closure_plan,
    four_square_pending_layers,
    set_four_square_bundle_source,
    verify_four_square_body_microbatch,
)
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_proof_bundle
from peano_lab.library.quadratic_reciprocity_stack_runtime import quadratic_reciprocity_stack
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / (
    "research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json"
)


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_four_square_proof_bundle()


def test_exact_lagrange_plan_preserves_immutable_alpha_v17_authority() -> None:
    plan = four_square_complete_closure_plan()

    assert plan.root == FOUR_SQUARE_ROOT_NAME == "four_square_lagrange"
    assert plan.parent_alpha_identity_sha256 == v17.ALPHA_V17_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_FOUR_SQUARE_THEOREM_COUNT == 390
    assert len(plan.pending_rows) == EXPECTED_FOUR_SQUARE_BODY_ONLY_COUNT == 201
    assert len(plan.qr_reused_rows) == EXPECTED_FOUR_SQUARE_QR_REUSED_BODY_COUNT == 174
    assert len(plan.reconstructed_rows) == EXPECTED_FOUR_SQUARE_RECONSTRUCTED_BODY_COUNT == 216
    assert len(plan.rows) - len(plan.pending_rows) == EXPECTED_FOUR_SQUARE_CHECKED_PARENT_COUNT
    assert plan.dependency_edge_count == EXPECTED_FOUR_SQUARE_DEPENDENCY_EDGE_COUNT == 1_187
    assert plan.ordered_names_sha256 == EXPECTED_FOUR_SQUARE_ORDERED_NAMES_SHA256
    assert plan.body_only_names_sha256 == EXPECTED_FOUR_SQUARE_BODY_ONLY_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_FOUR_SQUARE_SURFACE_SHA256
    assert plan.rows[-1].statement_sha256 == EXPECTED_FOUR_SQUARE_ROOT_STATEMENT_SHA256
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": 166,
        "alpha_closed": 23,
        "body_checked": 201,
    }
    assert sum(row.enrollment_origin == "ha" for row in plan.pending_rows) == (
        EXPECTED_FOUR_SQUARE_HA_BODY_COUNT
    )
    assert v17.ALPHA_EDITION.by_name[plan.root].evidence is (
        v17.EvidenceStatus.BODY_CHECKED
    )


def test_qr_reuse_contains_only_actual_previously_checked_ancestor_bodies() -> None:
    plan = four_square_complete_closure_plan()
    qr_names = {
        spec.name for spec in quadratic_reciprocity_stack().admission_order
    }

    assert all(row.name in qr_names for row in plan.qr_reused_rows)
    assert all(not row.needs_closure for row in plan.qr_reused_rows)
    assert len(
        [row for row in plan.reconstructed_rows if not row.needs_closure]
    ) == 15


def test_lagrange_pending_topology_has_exact_fifteen_dependency_waves() -> None:
    assert tuple(map(len, four_square_pending_layers())) == (
        63,
        37,
        21,
        19,
        12,
        9,
        5,
        4,
        12,
        11,
        3,
        2,
        1,
        1,
        1,
    )


def test_one_real_reconstructed_body_checks_without_changing_alpha_evidence() -> None:
    plan = four_square_complete_closure_plan()
    name = plan.reconstructed_rows[0].name
    batch = construct_four_square_body_microbatch((name,))

    assert batch.names == (name,)
    assert batch.proof_nodes < 125_000
    assert batch.proof_objects < 25_000
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert verify_four_square_body_microbatch(batch) is batch
    assert v17.ALPHA_EDITION.by_name[FOUR_SQUARE_ROOT_NAME].evidence is (
        v17.EvidenceStatus.BODY_CHECKED
    )


@pytest.mark.parametrize(
    ("names", "match"),
    [
        ((), "1..16"),
        (("zero_add",), "unknown or QR-reused"),
        ((FOUR_SQUARE_ROOT_NAME,), "lacks predecessor"),
        (("mul_lt_mul_succ_left_nonzero",) * 2, "unique"),
    ],
)
def test_microbatch_rejects_unsafe_or_incomplete_schedules(names, match: str) -> None:
    with pytest.raises(FourSquareCompleteClosureError, match=match):
        construct_four_square_body_microbatch(names)


def test_microbatch_enforces_sixteen_body_hard_cap() -> None:
    names = tuple(row.name for row in four_square_complete_closure_plan().reconstructed_rows[:17])
    with pytest.raises(FourSquareCompleteClosureError, match="1..16"):
        construct_four_square_body_microbatch(names)


def test_microbatch_verifier_rejects_false_proofs_and_forged_metrics() -> None:
    name = four_square_complete_closure_plan().reconstructed_rows[0].name
    batch = construct_four_square_body_microbatch((name,))
    forged = replace(batch.rows[0], certificate=EqRefl(Zero()))

    with pytest.raises(FourSquareCompleteClosureError, match="resource envelope|kernel rejected"):
        verify_four_square_body_microbatch(replace(batch, rows=(forged,)))
    with pytest.raises(FourSquareCompleteClosureError, match="aggregate metrics"):
        verify_four_square_body_microbatch(replace(batch, proof_nodes=batch.proof_nodes + 1))
    with pytest.raises(FourSquareCompleteClosureError, match="frozen parent"):
        verify_four_square_body_microbatch(
            replace(batch, parent_alpha_identity_sha256="0" * 64)
        )


def test_assembly_requires_all_216_actual_reconstructed_bodies() -> None:
    name = four_square_complete_closure_plan().reconstructed_rows[0].name
    batch = construct_four_square_body_microbatch((name,))

    with pytest.raises(FourSquareCompleteClosureError, match="exactly 216 actual"):
        assemble_four_square_proof_bundle((batch,))


def test_durable_lagrange_artifact_is_canonical_and_content_addressed() -> None:
    data = ARTIFACT.read_bytes()

    assert len(data) == EXPECTED_FOUR_SQUARE_BUNDLE_BYTES
    assert sha256(data).hexdigest() == EXPECTED_FOUR_SQUARE_BUNDLE_SHA256
    bundle, target = decode_proof_bundle(data.decode("utf-8"))
    assert encode_proof_bundle(bundle, target).encode("utf-8") == data


def test_complete_390_node_proof_checks_exact_unconditional_lagrange_root(
    actual_bundle,
) -> None:
    bundle, receipt = actual_bundle
    target = _closed_formula(v17.ALPHA_EDITION.by_name[FOUR_SQUARE_ROOT_NAME].spec.statement)

    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == 390
    assert bundle.root == 389
    assert receipt.dependency_edges == 1_187
    assert receipt.total_body_nodes == EXPECTED_FOUR_SQUARE_BUNDLE_BODY_PROOF_NODES
    assert receipt.target == target
    assert bundle.nodes[-1].target == target


def test_complete_lagrange_bundle_rejects_false_actual_dependency(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    mutated = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], body=EqRefl(Zero())),) + bundle.nodes[1:],
    )
    with pytest.raises(FourSquareCompleteClosureError, match="kernel rejected"):
        check_four_square_proof_bundle(mutated, receipt.target)


def test_complete_lagrange_bundle_rejects_changed_edges_and_root(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    altered = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], dependencies=(0,)),) + bundle.nodes[1:],
    )
    with pytest.raises(FourSquareCompleteClosureError, match="exact frozen theorem"):
        check_four_square_proof_bundle(altered, receipt.target)
    with pytest.raises(FourSquareCompleteClosureError, match="size or root"):
        check_four_square_proof_bundle(replace(bundle, root=388), receipt.target)


def test_four_square_bundle_never_promotes_its_alpha_v17_root(actual_bundle) -> None:
    _bundle, _receipt = actual_bundle
    root = v17.ALPHA_EDITION.by_name[FOUR_SQUARE_ROOT_NAME]

    assert root.evidence is v17.EvidenceStatus.BODY_CHECKED
    assert root.checked_use is False
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(FOUR_SQUARE_ROOT_NAME, edition="alpha")


def test_missing_lagrange_proof_artifact_fails_closed(tmp_path: Path) -> None:
    set_four_square_bundle_source(tmp_path / "missing.json")
    try:
        with pytest.raises(FourSquareCompleteClosureError, match="unavailable"):
            checked_four_square_proof_bundle()
    finally:
        set_four_square_bundle_source(None)

def test_mutated_lagrange_proof_artifact_fails_closed(tmp_path: Path) -> None:
    target = tmp_path / "mutated.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + b" ")
    set_four_square_bundle_source(target)
    try:
        with pytest.raises(FourSquareCompleteClosureError, match="frozen actual-proof provenance"):
            checked_four_square_proof_bundle()
    finally:
        set_four_square_bundle_source(None)
