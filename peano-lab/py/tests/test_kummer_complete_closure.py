"""Fail-closed original-kernel audit for both exact constructive Kummer roots."""

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
from peano_lab.library import editions_v17 as v17
from peano_lab.library.kummer_complete_closure import (
    EXPECTED_KUMMER_ALPHA_CLOSED_COUNT,
    EXPECTED_KUMMER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_KUMMER_BUNDLE_BYTES,
    EXPECTED_KUMMER_BUNDLE_EDGE_COUNT,
    EXPECTED_KUMMER_BUNDLE_NODE_COUNT,
    EXPECTED_KUMMER_BUNDLE_SHA256,
    EXPECTED_KUMMER_CONSTRUCTED_BODY_COUNT,
    EXPECTED_KUMMER_DEPENDENCY_EDGE_COUNT,
    EXPECTED_KUMMER_ORDERED_NAMES_SHA256,
    EXPECTED_KUMMER_PENDING_COUNT,
    EXPECTED_KUMMER_PENDING_NAMES_SHA256,
    EXPECTED_KUMMER_RECONSTRUCTED_PARENT_COUNT,
    EXPECTED_KUMMER_REUSED_PARENT_COUNT,
    EXPECTED_KUMMER_ROOT_NODE_IDS,
    EXPECTED_KUMMER_ROOT_PROOF_NODES,
    EXPECTED_KUMMER_ROOT_STATEMENT_SHA256,
    EXPECTED_KUMMER_STABLE_COUNT,
    EXPECTED_KUMMER_SURFACE_SHA256,
    EXPECTED_KUMMER_THEOREM_COUNT,
    KUMMER_RECONSTRUCTED_CHECKED_NAMES,
    KUMMER_ROOT_NAMES,
    KummerClosureError,
    assemble_kummer_proof_bundle,
    check_kummer_proof_bundle,
    construct_kummer_body_microbatch,
    kummer_complete_closure_plan,
    kummer_pending_layers,
    load_kummer_proof_bundle,
    replay_kummer_closed_theorem,
    verify_kummer_body_microbatch,
)
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_proof_bundle
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / "research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json"


@pytest.fixture(scope="module")
def actual_bundle():
    return load_kummer_proof_bundle(ARTIFACT)


@pytest.fixture(scope="module")
def first_body():
    return construct_kummer_body_microbatch((KUMMER_RECONSTRUCTED_CHECKED_NAMES[0],))


def test_plan_seals_both_exact_immutable_alpha_v17_kummer_endpoints() -> None:
    plan = kummer_complete_closure_plan()

    assert plan.roots == KUMMER_ROOT_NAMES
    assert plan.parent_alpha_identity_sha256 == v17.ALPHA_V17_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_KUMMER_THEOREM_COUNT == 280
    assert len(plan.checked_parent_rows) == 182
    assert len(plan.pending_rows) == EXPECTED_KUMMER_PENDING_COUNT == 98
    assert len(plan.construction_rows) == EXPECTED_KUMMER_CONSTRUCTED_BODY_COUNT == 105
    assert len(plan.reused_parent_names) == EXPECTED_KUMMER_REUSED_PARENT_COUNT == 175
    assert len(plan.reconstructed_parent_names) == EXPECTED_KUMMER_RECONSTRUCTED_PARENT_COUNT == 7
    assert plan.reconstructed_parent_names == KUMMER_RECONSTRUCTED_CHECKED_NAMES
    assert plan.dependency_edge_count == EXPECTED_KUMMER_DEPENDENCY_EDGE_COUNT == 777
    assert plan.ordered_names_sha256 == EXPECTED_KUMMER_ORDERED_NAMES_SHA256
    assert plan.pending_names_sha256 == EXPECTED_KUMMER_PENDING_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_KUMMER_SURFACE_SHA256
    assert tuple(row.node_id for row in plan.rows) == tuple(range(280))
    assert tuple(row.alpha_index for row in plan.rows) == tuple(
        sorted(row.alpha_index for row in plan.rows)
    )
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": EXPECTED_KUMMER_STABLE_COUNT,
        "alpha_closed": EXPECTED_KUMMER_ALPHA_CLOSED_COUNT,
        "body_checked": EXPECTED_KUMMER_PENDING_COUNT,
    }


def test_exact_kummer_roots_statements_and_dependency_waves_are_sealed() -> None:
    plan = kummer_complete_closure_plan()
    by_name = {row.name: row for row in plan.rows}

    assert tuple(by_name[name].node_id for name in KUMMER_ROOT_NAMES) == (
        EXPECTED_KUMMER_ROOT_NODE_IDS
    )
    assert tuple(by_name[name].statement_sha256 for name in KUMMER_ROOT_NAMES) == (
        EXPECTED_KUMMER_ROOT_STATEMENT_SHA256
    )
    assert tuple(map(len, kummer_pending_layers())) == (
        35, 14, 7, 7, 6, 7, 6, 4, 2, 1, 1, 2, 1, 1, 1, 1, 1, 1
    )
    assert all(
        v17.ALPHA_EDITION.by_name[row.name].evidence
        is v17.EvidenceStatus.BODY_CHECKED
        for row in plan.pending_rows
    )


def test_reconstructed_parent_bodies_do_not_grant_new_release_authority(first_body) -> None:
    name = KUMMER_RECONSTRUCTED_CHECKED_NAMES[0]
    before = v17.ALPHA_V17_IDENTITY_SHA256

    assert first_body.names == (name,)
    assert check((), first_body.rows[0].certificate, first_body.rows[0].curried_target)
    assert first_body.proof_nodes < 125_000
    assert first_body.proof_objects < 25_000
    assert verify_kummer_body_microbatch(first_body) is first_body
    assert v17.ALPHA_V17_IDENTITY_SHA256 == before
    assert v17.ALPHA_EDITION.by_name[name].checked_use is True


def test_body_only_construction_does_not_change_immutable_alpha_v17_evidence() -> None:
    name = kummer_complete_closure_plan().pending_rows[0].name
    before = v17.ALPHA_V17_IDENTITY_SHA256
    batch = construct_kummer_body_microbatch((name,))

    assert batch.names == (name,)
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert v17.ALPHA_V17_IDENTITY_SHA256 == before
    assert v17.ALPHA_EDITION.by_name[name].evidence is v17.EvidenceStatus.BODY_CHECKED
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(name, edition="alpha")


@pytest.mark.parametrize(
    ("names", "match"),
    [
        ((), "1..16"),
        (("zero_add",), "unknown or already-reused"),
        (("one_le_pow",), "lacks predecessor"),
        (
            (
                "zero_remainder_implies_multiple",
                "mul_lt_mul_succ_left_nonzero",
            ),
            "reorders",
        ),
        (("mul_lt_mul_succ_left_nonzero",) * 2, "distinct"),
    ],
)
def test_body_microbatches_reject_unsafe_schedule(names, match: str) -> None:
    with pytest.raises(KummerClosureError, match=match):
        construct_kummer_body_microbatch(names)


def test_body_microbatch_rejects_more_than_sixteen_actual_proofs() -> None:
    names = tuple(row.name for row in kummer_complete_closure_plan().construction_rows[:17])
    with pytest.raises(KummerClosureError, match="1..16"):
        construct_kummer_body_microbatch(names)


def test_body_verifier_rejects_forged_proof_metrics_and_parent(first_body) -> None:
    forged = replace(first_body.rows[0], certificate=EqRefl(Zero()))
    with pytest.raises(KummerClosureError, match="proof envelope|kernel rejected"):
        verify_kummer_body_microbatch(replace(first_body, rows=(forged,)))
    with pytest.raises(KummerClosureError, match="aggregate proof envelope"):
        verify_kummer_body_microbatch(
            replace(first_body, proof_nodes=first_body.proof_nodes + 1)
        )
    with pytest.raises(KummerClosureError, match="frozen parent"):
        verify_kummer_body_microbatch(
            replace(first_body, parent_alpha_identity_sha256="0" * 64)
        )


def test_assembly_rejects_missing_actual_theorem_proofs(first_body) -> None:
    with pytest.raises(KummerClosureError, match="requires exactly 105 actual"):
        assemble_kummer_proof_bundle((first_body,))


def test_durable_artifact_contains_exact_canonical_complete_proof_data() -> None:
    data = ARTIFACT.read_bytes()
    assert len(data) == EXPECTED_KUMMER_BUNDLE_BYTES == 1_528_814
    assert sha256(data).hexdigest() == EXPECTED_KUMMER_BUNDLE_SHA256
    bundle, target = decode_proof_bundle(data.decode("utf-8"))
    assert encode_proof_bundle(bundle, target).encode("utf-8") == data


def test_complete_actual_proof_graph_checks_both_original_kummer_endpoints(
    actual_bundle,
) -> None:
    plan = kummer_complete_closure_plan()
    bundle = actual_bundle.bundle
    receipt = actual_bundle.receipt

    assert receipt.node_count == EXPECTED_KUMMER_BUNDLE_NODE_COUNT == 281
    assert receipt.kernel_calls == 281
    assert receipt.dependency_edges == EXPECTED_KUMMER_BUNDLE_EDGE_COUNT == 779
    assert receipt.total_body_nodes == EXPECTED_KUMMER_BUNDLE_BODY_PROOF_NODES == 19_062
    assert bundle.root == 280
    assert bundle.nodes[-1].dependencies == EXPECTED_KUMMER_ROOT_NODE_IDS
    left = _closed_formula(v17.ALPHA_EDITION.by_name[plan.roots[0]].spec.statement)
    right = _closed_formula(v17.ALPHA_EDITION.by_name[plan.roots[1]].spec.statement)
    assert receipt.target == And(left, right)
    assert bundle.nodes[277].target == left
    assert bundle.nodes[279].target == right


def test_complete_bundle_rejects_changed_theorem_or_conjunction(actual_bundle) -> None:
    bundle = actual_bundle.bundle
    mutated = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], dependencies=(0,)),) + bundle.nodes[1:],
    )
    with pytest.raises(KummerClosureError, match="exact frozen theorem"):
        check_kummer_proof_bundle(mutated, actual_bundle.target)
    changed_root = replace(
        bundle,
        nodes=bundle.nodes[:-1]
        + (replace(bundle.nodes[-1], dependencies=(279, 277)),),
    )
    with pytest.raises(KummerClosureError, match="conjunction"):
        check_kummer_proof_bundle(changed_root, actual_bundle.target)


def test_complete_bundle_rejects_false_actual_dependency_body(actual_bundle) -> None:
    bundle = actual_bundle.bundle
    mutated = replace(
        bundle,
        nodes=(replace(bundle.nodes[0], body=EqRefl(Zero())),) + bundle.nodes[1:],
    )
    with pytest.raises(KummerClosureError, match="kernel rejected"):
        check_kummer_proof_bundle(mutated, actual_bundle.target)


@pytest.mark.parametrize(("name", "expected_nodes"), zip(
    KUMMER_ROOT_NAMES,
    EXPECTED_KUMMER_ROOT_PROOF_NODES,
    strict=True,
))
def test_each_kummer_endpoint_has_an_actual_bounded_empty_context_proof(
    name: str,
    expected_nodes: int,
    actual_bundle,
) -> None:
    actual = replay_kummer_closed_theorem(name, actual_bundle)

    assert actual.spec == v17.ALPHA_EDITION.by_name[name].spec
    assert actual.formula == _closed_formula(actual.spec.statement)
    assert actual.proof_nodes == expected_nodes
    assert actual.proof_nodes < 125_000


@pytest.mark.parametrize("name", KUMMER_ROOT_NAMES)
def test_complete_proof_bundle_does_not_promote_immutable_v17_root(
    name: str,
    actual_bundle,
) -> None:
    assert actual_bundle.receipt.kernel_calls == 281
    assert v17.ALPHA_EDITION.by_name[name].evidence is v17.EvidenceStatus.BODY_CHECKED
    assert v17.ALPHA_EDITION.by_name[name].checked_use is False
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(name, edition="alpha")


def test_missing_or_malformed_artifact_fails_closed(tmp_path: Path) -> None:
    with pytest.raises(KummerClosureError, match="cannot decode"):
        load_kummer_proof_bundle(tmp_path / "missing.json")
    mutated = tmp_path / "mutated.json"
    mutated.write_text("[\"peano-lab-bundle-v1\",0,[],[]]\n", encoding="utf-8")
    with pytest.raises(KummerClosureError, match="frozen actual-proof provenance"):
        load_kummer_proof_bundle(mutated)
