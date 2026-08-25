"""Full genuine constructive proof and adversarial audit of Bertrand's postulate."""

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
from peano_lab.library.bertrand_complete_closure import (
    BERTRAND_ROOT_NAME,
    EXPECTED_BERTRAND_BODY_ONLY_COUNT,
    EXPECTED_BERTRAND_BODY_ONLY_NAMES_SHA256,
    EXPECTED_BERTRAND_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_BERTRAND_BUNDLE_BYTES,
    EXPECTED_BERTRAND_BUNDLE_SHA256,
    EXPECTED_BERTRAND_CHECKED_PARENT_COUNT,
    EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT,
    EXPECTED_BERTRAND_ORDERED_NAMES_SHA256,
    EXPECTED_BERTRAND_REBUILT_BODY_COUNT,
    EXPECTED_BERTRAND_REBUILT_BODY_ONLY_COUNT,
    EXPECTED_BERTRAND_REBUILT_CHECKED_BODY_COUNT,
    EXPECTED_BERTRAND_REBUILT_NAMES_SHA256,
    EXPECTED_BERTRAND_REUSED_BODY_COUNT,
    EXPECTED_BERTRAND_ROOT_NODE_ID,
    EXPECTED_BERTRAND_ROOT_STATEMENT_SHA256,
    EXPECTED_BERTRAND_SOURCE_COUNTS,
    EXPECTED_BERTRAND_SURFACE_SHA256,
    EXPECTED_BERTRAND_THEOREM_COUNT,
    BertrandCompleteClosureError,
    _bertrand_body_script,
    assemble_bertrand_complete_proof_bundle,
    bertrand_complete_closure_plan,
    bertrand_pending_layers,
    check_bertrand_complete_proof_bundle,
    checked_bertrand_complete_proof_bundle,
    checked_bertrand_proof_bundle,
    construct_bertrand_body_microbatch,
    replay_bertrand_closed_theorem,
    set_bertrand_bundle_source,
    verify_bertrand_body_microbatch,
)
from peano_lab.library.proof_bundle import decode_proof_bundle, encode_proof_bundle
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / "research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json"


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_bertrand_proof_bundle()


def test_exact_544_node_dependency_slice_preserves_alpha_v17() -> None:
    plan = bertrand_complete_closure_plan()

    assert plan.root == BERTRAND_ROOT_NAME == "bertrand_strict"
    assert plan.parent_alpha_identity_sha256 == v17.ALPHA_V17_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v17.ALPHA_V17_ENROLLMENT_SHA256
    assert len(plan.rows) == EXPECTED_BERTRAND_THEOREM_COUNT == 544
    assert len(plan.checked_parent_rows) == EXPECTED_BERTRAND_CHECKED_PARENT_COUNT == 214
    assert len(plan.pending_rows) == EXPECTED_BERTRAND_BODY_ONLY_COUNT == 330
    assert len(plan.rebuilt_rows) == EXPECTED_BERTRAND_REBUILT_BODY_COUNT == 261
    assert plan.dependency_edge_count == EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT == 1_917
    assert plan.ordered_names_sha256 == EXPECTED_BERTRAND_ORDERED_NAMES_SHA256
    assert plan.body_only_names_sha256 == EXPECTED_BERTRAND_BODY_ONLY_NAMES_SHA256
    assert plan.rebuilt_names_sha256 == EXPECTED_BERTRAND_REBUILT_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_BERTRAND_SURFACE_SHA256
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": 202,
        "alpha_closed": 12,
        "body_checked": 330,
    }
    assert tuple(row.node_id for row in plan.rows) == tuple(range(544))
    assert plan.rows[-1].node_id == EXPECTED_BERTRAND_ROOT_NODE_ID == 543
    assert plan.rows[-1].statement_sha256 == EXPECTED_BERTRAND_ROOT_STATEMENT_SHA256


def test_four_genuine_checked_proof_artifacts_share_exact_body_nodes() -> None:
    plan = bertrand_complete_closure_plan()

    assert Counter(row.source for row in plan.rows) == EXPECTED_BERTRAND_SOURCE_COUNTS
    assert EXPECTED_BERTRAND_SOURCE_COUNTS == {
        "quadratic_reciprocity": 183,
        "supplementary": 3,
        "lucas": 33,
        "kummer": 64,
        "rebuild": 261,
    }
    assert sum(not row.requires_rebuilt_body for row in plan.rows) == (
        EXPECTED_BERTRAND_REUSED_BODY_COUNT
    ) == 283
    assert sum(row.needs_closure for row in plan.rebuilt_rows) == (
        EXPECTED_BERTRAND_REBUILT_BODY_ONLY_COUNT
    ) == 241
    assert sum(not row.needs_closure for row in plan.rebuilt_rows) == (
        EXPECTED_BERTRAND_REBUILT_CHECKED_BODY_COUNT
    ) == 20


def test_330_body_only_rows_have_actual_dependency_ready_layers() -> None:
    layers = bertrand_pending_layers()

    assert tuple(map(len, layers)) == (
        100, 56, 33, 28, 14, 19, 12, 11, 8, 8, 6, 6, 2, 1, 1, 1,
        2, 2, 2, 2, 1, 1, 1, 1, 3, 3, 2, 1, 1, 1, 1,
    )
    assert sum(map(len, layers)) == EXPECTED_BERTRAND_BODY_ONLY_COUNT
    assert layers[-1] == (BERTRAND_ROOT_NAME,)


def test_one_exact_body_is_independently_checked_under_original_caps() -> None:
    first = bertrand_complete_closure_plan().rebuilt_rows[0].name
    batch = construct_bertrand_body_microbatch((first,))

    assert batch.names == (first,)
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert batch.proof_nodes < 125_000
    assert batch.proof_objects < 25_000
    assert verify_bertrand_body_microbatch(batch) is batch


def test_frozen_power_seed_gets_only_checked_proof_arithmetic_normalization() -> None:
    plan = bertrand_complete_closure_plan()
    row = next(
        item
        for item in plan.rebuilt_rows
        if item.name == "pow_two_seed_bundle_from_total"
    )
    specification = v17.ALPHA_ENTRIES[row.alpha_index].spec
    original = specification.script
    normalized = _bertrand_body_script(row.name, original)

    assert len(original) == 266
    assert specification.dependencies == (
        "pow_successor_compose_from_total",
        "pow_two_base_two_value_four",
    )
    assert len(normalized) == 62
    assert tuple(
        index for index, (command, replaced) in enumerate(normalized) if replaced
    ) == (49, 58)
    assert all(command == "norm_num" for command, replaced in normalized if replaced)
    assert v17.ALPHA_ENTRIES[row.alpha_index].spec.script == original
    with pytest.raises(BertrandCompleteClosureError, match="historical.*script changed"):
        _bertrand_body_script(row.name, original[:-1])
    broken = (*original[:49], "refl", *original[50:])
    with pytest.raises(BertrandCompleteClosureError, match="rewrite blocks changed"):
        _bertrand_body_script(row.name, broken)


@pytest.mark.parametrize(
    ("names", "match"),
    [
        ((), "1..16"),
        (("zero_add",), "unknown or reused"),
        (("bertrand_strict",), "lacks predecessors"),
        (("le_not_lt",) * 2, "unique exact strings"),
        (("two_large_factors_impossible", "le_not_lt"), "reorders"),
    ],
)
def test_unsafe_body_schedules_are_rejected(names, match: str) -> None:
    with pytest.raises(BertrandCompleteClosureError, match=match):
        construct_bertrand_body_microbatch(names)


def test_microbatch_rejects_more_than_sixteen_proofs() -> None:
    names = tuple(row.name for row in bertrand_complete_closure_plan().rebuilt_rows[:17])

    with pytest.raises(BertrandCompleteClosureError, match="1..16"):
        construct_bertrand_body_microbatch(names)


def test_body_verifier_rejects_forged_proof_parent_and_metrics() -> None:
    first = bertrand_complete_closure_plan().rebuilt_rows[0].name
    batch = construct_bertrand_body_microbatch((first,))

    forged = replace(batch.rows[0], certificate=EqRefl(Zero()))
    with pytest.raises(BertrandCompleteClosureError, match="measured envelope|kernel rejected"):
        verify_bertrand_body_microbatch(replace(batch, rows=(forged,)))
    with pytest.raises(BertrandCompleteClosureError, match="proof envelope"):
        verify_bertrand_body_microbatch(replace(batch, proof_nodes=batch.proof_nodes + 1))
    with pytest.raises(BertrandCompleteClosureError, match="frozen parent"):
        verify_bertrand_body_microbatch(
            replace(batch, parent_alpha_identity_sha256="0" * 64)
        )


def test_incomplete_actual_body_batches_cannot_be_accepted() -> None:
    first = bertrand_complete_closure_plan().rebuilt_rows[0].name
    batch = construct_bertrand_body_microbatch((first,))

    with pytest.raises(BertrandCompleteClosureError, match="exactly 261"):
        assemble_bertrand_complete_proof_bundle((batch,))


def test_every_original_theorem_body_and_exact_root_are_kernel_checked(actual_bundle) -> None:
    bundle, receipt = actual_bundle

    assert len(bundle.nodes) == receipt.node_count == receipt.kernel_calls == 544
    assert bundle.root == EXPECTED_BERTRAND_ROOT_NODE_ID
    assert receipt.dependency_edges == EXPECTED_BERTRAND_DEPENDENCY_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_BERTRAND_BUNDLE_BODY_PROOF_NODES
    assert receipt.target == _closed_formula(
        v17.ALPHA_EDITION.by_name[BERTRAND_ROOT_NAME].spec.statement
    )
    assert checked_bertrand_complete_proof_bundle() == actual_bundle
    assert check_bertrand_complete_proof_bundle(bundle, receipt.target).receipt == receipt


def test_actual_artifact_is_canonical_and_bound_to_frozen_proof_bytes(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    data = ARTIFACT.read_bytes()

    assert len(data) == EXPECTED_BERTRAND_BUNDLE_BYTES
    assert sha256(data).hexdigest() == EXPECTED_BERTRAND_BUNDLE_SHA256
    decoded, target = decode_proof_bundle(data.decode("utf-8"))
    assert encode_proof_bundle(decoded, target).encode("utf-8") == data
    assert decoded == bundle
    assert target == receipt.target


def test_mutated_proof_dependency_or_target_is_rejected(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    broken = replace(bundle.nodes[0], body=EqRefl(Zero()))

    with pytest.raises(BertrandCompleteClosureError, match="rejected"):
        check_bertrand_complete_proof_bundle(
            replace(bundle, nodes=(broken, *bundle.nodes[1:])),
            receipt.target,
        )
    with pytest.raises(BertrandCompleteClosureError, match="exact original root"):
        check_bertrand_complete_proof_bundle(bundle, Bot())

    last = replace(bundle.nodes[-1], dependencies=bundle.nodes[-1].dependencies[:-1])
    with pytest.raises(BertrandCompleteClosureError, match="exact frozen theorem"):
        check_bertrand_complete_proof_bundle(
            replace(bundle, nodes=(*bundle.nodes[:-1], last)),
            receipt.target,
        )


def test_missing_or_mutated_complete_artifact_fails_closed(tmp_path: Path) -> None:
    try:
        set_bertrand_bundle_source(tmp_path / "missing.json")
        with pytest.raises(BertrandCompleteClosureError, match="unavailable"):
            checked_bertrand_proof_bundle()

        mutated = tmp_path / "mutated.json"
        original = ARTIFACT.read_bytes()
        mutated.write_bytes(original[:-1] + b" ")
        set_bertrand_bundle_source(mutated)
        with pytest.raises(BertrandCompleteClosureError, match="frozen"):
            checked_bertrand_proof_bundle()
    finally:
        set_bertrand_bundle_source(None)


def test_small_actual_closed_proof_does_not_mutate_immutable_alpha_v17() -> None:
    before = (
        v17.ALPHA_V17_IDENTITY_SHA256,
        len(v17.ALPHA_CHECKED_SPECS),
        v17.STABLE_EDITION.identity_sha256,
    )
    name = bertrand_complete_closure_plan().pending_rows[0].name
    actual = replay_bertrand_closed_theorem(name)

    assert check((), actual.certificate, actual.formula)
    assert v17.ALPHA_EDITION.by_name[BERTRAND_ROOT_NAME].evidence is (
        v17.EvidenceStatus.BODY_CHECKED
    )
    assert not v17.ALPHA_EDITION.by_name[BERTRAND_ROOT_NAME].checked_use
    with pytest.raises(v17.EditionV17ReplayError, match="checked theorem use"):
        v17.replay(BERTRAND_ROOT_NAME, edition="alpha")
    assert before == (
        v17.ALPHA_V17_IDENTITY_SHA256,
        len(v17.ALPHA_CHECKED_SPECS),
        v17.STABLE_EDITION.identity_sha256,
    )


def test_nonpending_theorems_are_not_admitted_by_experimental_replay() -> None:
    with pytest.raises(BertrandCompleteClosureError, match="outside the exact 330-row"):
        replay_bertrand_closed_theorem("zero_add")
