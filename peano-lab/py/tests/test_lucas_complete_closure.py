"""Complete original-kernel and independent-proof-bundle Lucas audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import EqRefl
from peano_lab.kernel.terms import Zero
from peano_lab.library import editions_v17 as v17
from peano_lab.library.lucas_complete_closure import (
    EXPECTED_LUCAS_BODY_ONLY_COUNT,
    EXPECTED_LUCAS_BODY_ONLY_NAMES_SHA256,
    EXPECTED_LUCAS_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_LUCAS_BUNDLE_BYTES,
    EXPECTED_LUCAS_BUNDLE_SHA256,
    EXPECTED_LUCAS_CHECKED_PARENT_COUNT,
    EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT,
    EXPECTED_LUCAS_ORDERED_NAMES_SHA256,
    EXPECTED_LUCAS_QR_BODY_COUNT,
    EXPECTED_LUCAS_REBUILT_BODY_COUNT,
    EXPECTED_LUCAS_REBUILT_NAMES_SHA256,
    EXPECTED_LUCAS_ROOT_NODE_ID,
    EXPECTED_LUCAS_ROOT_STATEMENT_SHA256,
    EXPECTED_LUCAS_SURFACE_SHA256,
    EXPECTED_LUCAS_THEOREM_COUNT,
    LUCAS_CHECKED_OUTSIDE_QR_NAMES,
    LUCAS_ROOT_NAME,
    LucasCompleteClosureError,
    assemble_lucas_proof_bundle,
    check_lucas_proof_bundle,
    checked_lucas_proof_bundle,
    construct_lucas_body_microbatch,
    lucas_closure_plan,
    lucas_pending_layers,
    replay_lucas_closed_theorem,
    set_lucas_bundle_source,
    verify_lucas_body_microbatch,
)
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_proof_bundle
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / "research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json"


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_lucas_proof_bundle()


def test_exact_lucas_dependency_slice_preserves_immutable_alpha_v17() -> None:
    plan = lucas_closure_plan()

    assert plan.root == LUCAS_ROOT_NAME
    assert plan.parent_alpha_identity_sha256 == v17.ALPHA_V17_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_LUCAS_THEOREM_COUNT == 213
    assert len(plan.checked_parent_rows) == EXPECTED_LUCAS_CHECKED_PARENT_COUNT == 139
    assert len(plan.pending_rows) == EXPECTED_LUCAS_BODY_ONLY_COUNT == 74
    assert len(plan.rebuilt_rows) == EXPECTED_LUCAS_REBUILT_BODY_COUNT == 77
    assert plan.dependency_edge_count == EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT == 617
    assert plan.ordered_names_sha256 == EXPECTED_LUCAS_ORDERED_NAMES_SHA256
    assert plan.body_only_names_sha256 == EXPECTED_LUCAS_BODY_ONLY_NAMES_SHA256
    assert plan.rebuilt_names_sha256 == EXPECTED_LUCAS_REBUILT_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_LUCAS_SURFACE_SHA256
    assert tuple(row.node_id for row in plan.rows) == tuple(range(213))
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": 138,
        "alpha_closed": 1,
        "body_checked": 74,
    }


def test_exact_checked_parent_bodies_are_reused_or_rebuilt() -> None:
    plan = lucas_closure_plan()
    outside = tuple(row.name for row in plan.checked_parent_rows if row.requires_rebuilt_body)

    assert outside == LUCAS_CHECKED_OUTSIDE_QR_NAMES == (
        "mul_lt_mul_succ_left_nonzero",
        "beta_factor_divides_product",
        "add_shuffle_middle",
    )
    assert len(plan.checked_parent_rows) - len(outside) == (
        EXPECTED_LUCAS_QR_BODY_COUNT
    ) == 136
    assert plan.rows[-1].node_id == EXPECTED_LUCAS_ROOT_NODE_ID == 212
    assert plan.rows[-1].statement_sha256 == EXPECTED_LUCAS_ROOT_STATEMENT_SHA256


def test_dependency_ready_waves_cover_every_body_only_lucas_ancestor() -> None:
    layers = lucas_pending_layers()

    assert tuple(map(len, layers)) == (
        31, 10, 8, 5, 3, 2, 2, 1, 1, 1, 1, 2, 1, 1, 1, 1, 1, 1, 1,
    )
    assert sum(map(len, layers)) == EXPECTED_LUCAS_BODY_ONLY_COUNT
    assert layers[-1] == (LUCAS_ROOT_NAME,)


def test_small_actual_body_microbatch_preserves_all_original_caps() -> None:
    name = lucas_closure_plan().rebuilt_rows[0].name
    batch = construct_lucas_body_microbatch((name,))

    assert batch.names == (name,)
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert batch.proof_nodes < 125_000
    assert batch.proof_objects < 25_000
    assert verify_lucas_body_microbatch(batch) is batch


@pytest.mark.parametrize(
    ("names", "match"),
    [
        ((), "1..16"),
        (("zero_add",), "unknown or reused QR"),
        (("lucas_theorem",), "lacks predecessors"),
        (("mul_lt_mul_succ_left_nonzero",) * 2, "unique exact strings"),
        (
            ("beta_factor_divides_product", "mul_lt_mul_succ_left_nonzero"),
            "reorders",
        ),
    ],
)
def test_body_microbatch_rejects_unsafe_or_forged_schedules(names, match: str) -> None:
    with pytest.raises(LucasCompleteClosureError, match=match):
        construct_lucas_body_microbatch(names)


def test_body_microbatch_rejects_more_than_sixteen_actual_proofs() -> None:
    names = tuple(row.name for row in lucas_closure_plan().rebuilt_rows[:17])

    with pytest.raises(LucasCompleteClosureError, match="1..16"):
        construct_lucas_body_microbatch(names)


def test_body_verifier_rejects_forged_proof_metrics_and_parent() -> None:
    name = lucas_closure_plan().rebuilt_rows[0].name
    batch = construct_lucas_body_microbatch((name,))

    forged = replace(batch.rows[0], certificate=EqRefl(Zero()))
    with pytest.raises(LucasCompleteClosureError, match="measured envelope|kernel rejected"):
        verify_lucas_body_microbatch(replace(batch, rows=(forged,)))
    with pytest.raises(LucasCompleteClosureError, match="aggregate proof envelope"):
        verify_lucas_body_microbatch(replace(batch, proof_nodes=batch.proof_nodes + 1))
    with pytest.raises(LucasCompleteClosureError, match="frozen parent"):
        verify_lucas_body_microbatch(
            replace(batch, parent_alpha_identity_sha256="0" * 64)
        )


def test_actual_bundle_contains_all_complete_kernel_checked_bodies(actual_bundle) -> None:
    bundle, receipt = actual_bundle

    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == 213
    assert bundle.root == EXPECTED_LUCAS_ROOT_NODE_ID
    assert receipt.dependency_edges == EXPECTED_LUCAS_DEPENDENCY_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_LUCAS_BUNDLE_BODY_PROOF_NODES
    assert receipt.target == _closed_formula(
        v17.ALPHA_EDITION.by_name[LUCAS_ROOT_NAME].spec.statement
    )
    assert check_lucas_proof_bundle(bundle, receipt.target).receipt == receipt


def test_actual_artifact_is_canonical_and_has_frozen_provenance(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    payload = ARTIFACT.read_bytes()

    assert len(payload) == EXPECTED_LUCAS_BUNDLE_BYTES
    assert sha256(payload).hexdigest() == EXPECTED_LUCAS_BUNDLE_SHA256
    decoded, target = decode_proof_bundle(payload.decode("utf-8"))
    assert encode_proof_bundle(decoded, target).encode("utf-8") == payload
    assert target == receipt.target
    assert decoded == bundle


def test_bundle_rejects_forged_actual_proof_body(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    broken = replace(bundle.nodes[0], body=EqRefl(Zero()))
    forged = replace(bundle, nodes=(broken, *bundle.nodes[1:]))

    with pytest.raises(LucasCompleteClosureError, match="kernel rejected|rejected"):
        check_lucas_proof_bundle(forged, receipt.target)


def test_bundle_rejects_wrong_formula_and_forged_dependency(actual_bundle) -> None:
    bundle, receipt = actual_bundle

    with pytest.raises(LucasCompleteClosureError, match="exact original theorem root"):
        check_lucas_proof_bundle(bundle, Bot())

    root = replace(bundle.nodes[-1], dependencies=bundle.nodes[-1].dependencies[:-1])
    forged = replace(bundle, nodes=(*bundle.nodes[:-1], root))
    with pytest.raises(LucasCompleteClosureError, match="exact frozen theorem"):
        check_lucas_proof_bundle(forged, receipt.target)


def test_incomplete_actual_body_batches_do_not_assemble() -> None:
    first = lucas_closure_plan().rebuilt_rows[0].name
    batch = construct_lucas_body_microbatch((first,))

    with pytest.raises(LucasCompleteClosureError, match="exactly 77"):
        assemble_lucas_proof_bundle((batch,))


def test_missing_or_mutated_artifact_fails_closed(tmp_path: Path) -> None:
    try:
        set_lucas_bundle_source(tmp_path / "missing.json")
        with pytest.raises(LucasCompleteClosureError, match="unavailable"):
            checked_lucas_proof_bundle()

        mutated = tmp_path / "mutated.json"
        original = ARTIFACT.read_bytes()
        mutated.write_bytes(original[:-1] + b" ")
        set_lucas_bundle_source(mutated)
        with pytest.raises(LucasCompleteClosureError, match="frozen"):
            checked_lucas_proof_bundle()
    finally:
        set_lucas_bundle_source(None)


def test_complete_lucas_proof_does_not_promote_immutable_alpha_v17() -> None:
    before = (
        v17.ALPHA_V17_IDENTITY_SHA256,
        len(v17.ALPHA_CHECKED_SPECS),
        v17.STABLE_EDITION.identity_sha256,
    )
    name = lucas_closure_plan().pending_rows[0].name
    actual = replay_lucas_closed_theorem(name)

    assert check((), actual.certificate, actual.formula)
    assert v17.ALPHA_EDITION.by_name[LUCAS_ROOT_NAME].evidence is (
        v17.EvidenceStatus.BODY_CHECKED
    )
    assert not v17.ALPHA_EDITION.by_name[LUCAS_ROOT_NAME].checked_use
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(LUCAS_ROOT_NAME, edition="alpha")
    assert before == (
        v17.ALPHA_V17_IDENTITY_SHA256,
        len(v17.ALPHA_CHECKED_SPECS),
        v17.STABLE_EDITION.identity_sha256,
    )


def test_complete_lucas_root_has_actual_original_kernel_closed_proof() -> None:
    actual = replay_lucas_closed_theorem(LUCAS_ROOT_NAME)

    assert actual.spec.name == LUCAS_ROOT_NAME
    assert actual.formula == _closed_formula(actual.spec.statement)
    assert check((), actual.certificate, actual.formula)
    assert actual.proof_nodes <= 500_000


def test_nonpending_theorems_cannot_use_lucas_experimental_replay() -> None:
    with pytest.raises(LucasCompleteClosureError, match="outside the exact 74-row"):
        replay_lucas_closed_theorem("zero_add")
