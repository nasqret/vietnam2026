"""Actual constructive proof audit for both quadratic supplementary laws."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v16 as v16
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_proof_bundle
from peano_lab.library.supplementary_laws_closure import (
    EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES,
    EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT,
    EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT,
    EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256,
    EXPECTED_SUPPLEMENTARY_CHECKED_PARENT_COUNT,
    EXPECTED_SUPPLEMENTARY_DEPENDENCY_EDGE_COUNT,
    EXPECTED_SUPPLEMENTARY_NEW_BODY_COUNT,
    EXPECTED_SUPPLEMENTARY_ORDERED_NAMES_SHA256,
    EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT,
    EXPECTED_SUPPLEMENTARY_PROMOTION_NAMES_SHA256,
    EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS,
    EXPECTED_SUPPLEMENTARY_ROOT_STATEMENT_SHA256,
    EXPECTED_SUPPLEMENTARY_SURFACE_SHA256,
    EXPECTED_SUPPLEMENTARY_THEOREM_COUNT,
    SUPPLEMENTARY_EXISTING_BERTRAND_NAMES,
    SUPPLEMENTARY_ROOT_NAMES,
    SupplementaryClosureError,
    assemble_supplementary_proof_bundle,
    check_supplementary_proof_bundle,
    checked_supplementary_proof_bundle,
    construct_supplementary_body_microbatch,
    decode_supplementary_body_microbatch,
    encode_supplementary_body_microbatch,
    load_supplementary_body_checkpoint,
    replay_supplementary_closed_theorem,
    set_supplementary_bundle_source,
    supplementary_laws_closure_plan,
    supplementary_pending_layers,
    verify_supplementary_body_microbatch,
    write_supplementary_body_checkpoint,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / (
    "research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json"
)


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_supplementary_proof_bundle()


def test_plan_preserves_the_exact_immutable_alpha_v16_parent() -> None:
    plan = supplementary_laws_closure_plan()

    assert plan.roots == SUPPLEMENTARY_ROOT_NAMES
    assert plan.parent_alpha_identity_sha256 == v16.ALPHA_V16_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v16.ALPHA_V16_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_SUPPLEMENTARY_THEOREM_COUNT == 437
    assert len(plan.checked_parent_rows) == EXPECTED_SUPPLEMENTARY_CHECKED_PARENT_COUNT == 406
    assert len(plan.pending_rows) == EXPECTED_SUPPLEMENTARY_PROMOTION_COUNT == 31
    assert plan.dependency_edge_count == EXPECTED_SUPPLEMENTARY_DEPENDENCY_EDGE_COUNT == 1_427
    assert plan.ordered_names_sha256 == EXPECTED_SUPPLEMENTARY_ORDERED_NAMES_SHA256
    assert plan.promotion_names_sha256 == EXPECTED_SUPPLEMENTARY_PROMOTION_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_SUPPLEMENTARY_SURFACE_SHA256
    assert tuple(row.node_id for row in plan.rows) == tuple(range(437))
    assert tuple(row.alpha_index for row in plan.rows) == tuple(
        sorted(row.alpha_index for row in plan.rows)
    )
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": 226,
        "alpha_closed": 180,
        "body_checked": 31,
    }
    assert Counter(row.enrollment_origin for row in plan.pending_rows) == {
        "bertrand": 3,
        "ha": EXPECTED_SUPPLEMENTARY_NEW_BODY_COUNT,
    }


def test_exact_roots_statements_and_eisenstein_prefix_are_sealed() -> None:
    plan = supplementary_laws_closure_plan()
    by_name = {row.name: row for row in plan.rows}

    assert tuple(by_name[name].node_id for name in SUPPLEMENTARY_ROOT_NAMES) == (
        EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS
    )
    assert tuple(
        by_name[name].statement_sha256 for name in SUPPLEMENTARY_ROOT_NAMES
    ) == EXPECTED_SUPPLEMENTARY_ROOT_STATEMENT_SHA256
    assert tuple(row.name for row in plan.pending_rows[:3]) == (
        SUPPLEMENTARY_EXISTING_BERTRAND_NAMES
    )
    assert all(
        v16.ALPHA_EDITION.by_name[row.name].evidence
        is v16.EvidenceStatus.BODY_CHECKED
        for row in plan.pending_rows
    )


def test_dependency_waves_distinguish_three_old_and_28_new_actual_bodies() -> None:
    assert tuple(map(len, supplementary_pending_layers())) == (13, 8, 4, 2, 1, 2, 1)
    assert tuple(
        map(
            len,
            supplementary_pending_layers(
                existing_names=SUPPLEMENTARY_EXISTING_BERTRAND_NAMES
            ),
        )
    ) == (11, 7, 4, 2, 1, 2, 1)


def test_planning_and_body_construction_never_change_release_authority() -> None:
    plan = supplementary_laws_closure_plan()
    before = v16.ALPHA_V16_IDENTITY_SHA256
    name = plan.pending_rows[0].name
    batch = construct_supplementary_body_microbatch((name,))

    assert batch.names == (name,)
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert batch.proof_nodes < 125_000
    assert batch.proof_objects < 25_000
    assert verify_supplementary_body_microbatch(batch) is batch
    assert v16.ALPHA_V16_IDENTITY_SHA256 == before
    assert v16.ALPHA_EDITION.by_name[name].evidence is v16.EvidenceStatus.BODY_CHECKED
    with pytest.raises(v16.EditionV16ReplayError, match="checked theorem use"):
        v16.replay(name, edition="alpha")


@pytest.mark.parametrize(
    ("names", "match"),
    [
        ((), "1..16"),
        (("zero_add",), "unknown or already-closed"),
        (("eisenstein_initial_segment_prefix_exists",), "lacks predecessor"),
        (
            (
                "eisenstein_initial_segment_prefix_extend",
                "eisenstein_initial_segment_indicator_choice",
            ),
            "reorders",
        ),
        (
            ("eisenstein_initial_segment_indicator_choice",) * 2,
            "unique",
        ),
    ],
)
def test_body_microbatches_reject_unsafe_schedule(names, match: str) -> None:
    with pytest.raises(SupplementaryClosureError, match=match):
        construct_supplementary_body_microbatch(names)


def test_body_microbatch_rejects_more_than_sixteen_proofs() -> None:
    names = tuple(row.name for row in supplementary_laws_closure_plan().pending_rows[:17])
    with pytest.raises(SupplementaryClosureError, match="1..16"):
        construct_supplementary_body_microbatch(names)


def test_body_verifier_rejects_forged_proof_metrics_and_parent() -> None:
    name = SUPPLEMENTARY_EXISTING_BERTRAND_NAMES[0]
    batch = construct_supplementary_body_microbatch((name,))

    forged = replace(batch.rows[0], certificate=EqRefl(Zero()))
    with pytest.raises(SupplementaryClosureError, match="measured envelope|kernel rejected"):
        verify_supplementary_body_microbatch(replace(batch, rows=(forged,)))
    with pytest.raises(SupplementaryClosureError, match="aggregate envelope"):
        verify_supplementary_body_microbatch(
            replace(batch, proof_nodes=batch.proof_nodes + 1)
        )
    with pytest.raises(SupplementaryClosureError, match="frozen parent"):
        verify_supplementary_body_microbatch(
            replace(batch, parent_alpha_identity_sha256="0" * 64)
        )


def test_deterministic_checkpoint_contains_actual_rechecked_proof_trees(
    tmp_path: Path,
) -> None:
    name = SUPPLEMENTARY_EXISTING_BERTRAND_NAMES[0]
    batch = construct_supplementary_body_microbatch((name,))
    payload = encode_supplementary_body_microbatch(batch)
    restored = decode_supplementary_body_microbatch(payload)

    assert restored.names == (name,)
    assert restored.rows[0].certificate == batch.rows[0].certificate
    assert restored.proof_objects == restored.proof_nodes
    assert check((), restored.rows[0].certificate, restored.rows[0].curried_target)
    destination = write_supplementary_body_checkpoint(batch, tmp_path)
    assert destination.name.startswith("supplementary-body-")
    assert destination.read_text(encoding="utf-8") == payload
    assert load_supplementary_body_checkpoint(destination) == restored
    with pytest.raises(SupplementaryClosureError, match="fresh supplementary proof"):
        write_supplementary_body_checkpoint(batch, tmp_path)


def test_deterministic_checkpoint_rejects_noncanonical_and_forged_bytes() -> None:
    name = SUPPLEMENTARY_EXISTING_BERTRAND_NAMES[0]
    batch = construct_supplementary_body_microbatch((name,))
    payload = encode_supplementary_body_microbatch(batch)

    with pytest.raises(SupplementaryClosureError, match="not canonical"):
        decode_supplementary_body_microbatch(payload + " ")
    tampered = payload.replace(name, "forged_supplementary_name", 1)
    with pytest.raises(SupplementaryClosureError, match="frozen theorem surface"):
        decode_supplementary_body_microbatch(tampered)


def test_assembly_rejects_missing_actual_theorem_proofs() -> None:
    name = SUPPLEMENTARY_EXISTING_BERTRAND_NAMES[0]
    batch = construct_supplementary_body_microbatch((name,))
    with pytest.raises(SupplementaryClosureError, match="requires exactly 31 actual"):
        assemble_supplementary_proof_bundle((batch,))


def test_durable_artifact_is_canonical_content_addressed_actual_proof() -> None:
    data = ARTIFACT.read_bytes()

    assert len(data) == EXPECTED_SUPPLEMENTARY_BUNDLE_BYTES
    assert sha256(data).hexdigest() == EXPECTED_SUPPLEMENTARY_BUNDLE_SHA256
    bundle, target = decode_proof_bundle(data.decode("utf-8"))
    assert encode_proof_bundle(bundle, target).encode("utf-8") == data


def test_complete_actual_proof_graph_checks_both_exact_supplementary_laws(
    actual_bundle,
) -> None:
    bundle, receipt = actual_bundle
    plan = supplementary_laws_closure_plan()

    assert receipt.node_count == EXPECTED_SUPPLEMENTARY_BUNDLE_NODE_COUNT == 438
    assert receipt.kernel_calls == 438
    assert receipt.dependency_edges == EXPECTED_SUPPLEMENTARY_BUNDLE_EDGE_COUNT == 1_429
    assert receipt.total_body_nodes == EXPECTED_SUPPLEMENTARY_BUNDLE_BODY_PROOF_NODES
    assert bundle.root == 437
    assert bundle.nodes[-1].dependencies == EXPECTED_SUPPLEMENTARY_ROOT_NODE_IDS
    left = _closed_formula(v16.ALPHA_EDITION.by_name[plan.roots[0]].spec.statement)
    right = _closed_formula(v16.ALPHA_EDITION.by_name[plan.roots[1]].spec.statement)
    assert receipt.target == And(left, right)
    assert bundle.nodes[415].target == left
    assert bundle.nodes[436].target == right


def test_complete_bundle_rejects_mutated_theorem_or_conjunction(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    mutated = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], dependencies=(0,)),) + bundle.nodes[1:],
    )
    with pytest.raises(SupplementaryClosureError, match="exact frozen theorem"):
        check_supplementary_proof_bundle(mutated, receipt.target)
    changed_root = replace(
        bundle,
        nodes=bundle.nodes[:-1]
        + (replace(bundle.nodes[-1], dependencies=(436, 415)),),
    )
    with pytest.raises(SupplementaryClosureError, match="conjunction"):
        check_supplementary_proof_bundle(changed_root, receipt.target)


def test_complete_bundle_rejects_a_false_actual_dependency_body(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    mutated = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], body=EqRefl(Zero())),) + bundle.nodes[1:],
    )
    with pytest.raises(SupplementaryClosureError, match="kernel rejected"):
        check_supplementary_proof_bundle(mutated, receipt.target)


@pytest.mark.parametrize("name", SUPPLEMENTARY_ROOT_NAMES)
def test_each_supplement_endpoint_has_actual_empty_context_kernel_proof(name: str) -> None:
    actual = replay_supplementary_closed_theorem(name)

    assert actual.spec == v16.ALPHA_EDITION.by_name[name].spec
    assert actual.formula == _closed_formula(actual.spec.statement)
    assert actual.proof_nodes > 0
    assert check((), actual.certificate, actual.formula)


@pytest.mark.parametrize(
    "name",
    ["zero_add", "quadratic_reciprocity_combined", "four_square_lagrange"],
)
def test_replay_does_not_grant_unrelated_checked_authority(name: str) -> None:
    with pytest.raises(SupplementaryClosureError, match="outside the exact 31-row"):
        replay_supplementary_closed_theorem(name)


def test_missing_actual_artifact_fails_closed(tmp_path: Path) -> None:
    set_supplementary_bundle_source(tmp_path / "missing.json")
    try:
        with pytest.raises(SupplementaryClosureError, match="unavailable"):
            replay_supplementary_closed_theorem(SUPPLEMENTARY_ROOT_NAMES[0])
    finally:
        set_supplementary_bundle_source(None)


def test_mutated_actual_artifact_fails_closed(tmp_path: Path) -> None:
    destination = tmp_path / "mutated.json"
    original = ARTIFACT.read_bytes()
    destination.write_bytes(original[:-1] + b" ")
    set_supplementary_bundle_source(destination)
    try:
        with pytest.raises(SupplementaryClosureError, match="frozen actual-proof provenance"):
            replay_supplementary_closed_theorem(SUPPLEMENTARY_ROOT_NAMES[0])
    finally:
        set_supplementary_bundle_source(None)
