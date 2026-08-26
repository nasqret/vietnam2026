"""Fail-closed, workstation-bounded genuine quadratic-reciprocity closure."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Eq
from peano_lab.kernel.proofs import DNE, EqRefl
from peano_lab.kernel.terms import Succ, Zero
from peano_lab.library import editions_v15 as v15
from peano_lab.library.frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from peano_lab.library.quadratic_reciprocity_closure import (
    QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT,
    QuadraticReciprocityClosureError,
    assemble_quadratic_reciprocity_proof_bundle,
    assemble_quadratic_reciprocity_root,
    construct_quadratic_reciprocity_body_batch,
    decode_quadratic_reciprocity_body_batch,
    encode_quadratic_reciprocity_body_batch,
    load_quadratic_reciprocity_body_checkpoint,
    quadratic_reciprocity_closure_plan,
    quadratic_reciprocity_next_microbatch,
    verify_quadratic_reciprocity_body_batch,
    write_quadratic_reciprocity_body_checkpoint,
)
from peano_lab.library.proof_bundle import check_encoded_proof_bundle
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.library.theorems import _specs_by_name


@pytest.fixture(scope="module")
def plan():
    return quadratic_reciprocity_closure_plan()


@pytest.fixture(scope="module")
def first_actual_batch(plan):
    return construct_quadratic_reciprocity_body_batch(
        tuple(row.name for row in plan.rows[:3]),
        plan=plan,
    )


@pytest.fixture(scope="module")
def first_actual_checkpoint(first_actual_batch, plan):
    return encode_quadratic_reciprocity_body_batch(
        first_actual_batch,
        plan=plan,
    )


def test_frozen_qr_plan_preserves_exact_alpha_v15_evidence(plan) -> None:
    assert plan.root == QR_ROOT_NAME
    assert len(plan.rows) == 557
    assert len(plan.layers) == 45
    assert plan.dependency_edge_count == 1_787
    assert plan.graph_sha256 == (
        "26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253"
    )
    assert plan.source_sha256 == (
        "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1"
    )
    assert Counter(row.evidence for row in plan.rows) == {
        "stable_closed": 241,
        "alpha_closed": 1,
        "body_checked": 314,
        "pending_layered_closure": 1,
    }
    assert plan.rows[-1].name == QR_ROOT_NAME
    assert plan.rows[-1].evidence == "pending_layered_closure"
    assert QR_ROOT_NAME not in _specs_by_name()
    assert (
        v15.ALPHA_EDITION.by_name[QR_ROOT_NAME].evidence
        is v15.EvidenceStatus.PENDING_LAYERED_CLOSURE
    )


def test_all_557_actual_body_obligations_have_35_safe_microbatches(plan) -> None:
    completed: list[str] = []
    batches: list[tuple[str, ...]] = []
    while batch := quadratic_reciprocity_next_microbatch(
        completed,
        plan=plan,
    ):
        assert 0 < len(batch) <= MAX_FRONTIER_CLOSURE_MICROBATCH
        batches.append(batch)
        completed.extend(batch)

    assert len(batches) == 35
    assert len(batches[-1]) == 13
    assert completed == [row.name for row in plan.rows]
    assert batches[-1][-1] == QR_ROOT_NAME
    assert quadratic_reciprocity_next_microbatch(completed, plan=plan) == ()


@pytest.mark.parametrize("limit", [0, -1, 17, True, 1.0])
def test_microbatch_planner_never_relaxes_its_reviewed_row_limit(
    plan,
    limit,
) -> None:
    with pytest.raises(QuadraticReciprocityClosureError, match="size"):
        quadratic_reciprocity_next_microbatch(plan=plan, max_rows=limit)


def test_planner_rejects_nonclosed_unknown_and_forged_source_state(plan) -> None:
    with pytest.raises(QuadraticReciprocityClosureError, match="dependency closed"):
        quadratic_reciprocity_next_microbatch(("mul_one",), plan=plan)
    with pytest.raises(QuadraticReciprocityClosureError, match="unknown"):
        quadratic_reciprocity_next_microbatch(("invented",), plan=plan)
    with pytest.raises(QuadraticReciprocityClosureError, match="repeats"):
        quadratic_reciprocity_next_microbatch(("zero_add", "zero_add"), plan=plan)
    with pytest.raises(QuadraticReciprocityClosureError, match="sealed"):
        quadratic_reciprocity_next_microbatch(
            plan=replace(plan, graph_sha256="0" * 64)
        )


def test_actual_microbatch_contains_only_checked_dependency_curried_bodies(
    plan,
    first_actual_batch,
) -> None:
    batch = first_actual_batch
    assert batch.names == (
        "zero_add",
        "mul_one",
        "prime_divisor_eq_one_or_self",
    )
    assert 0 < batch.proof_nodes <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 0 < batch.proof_objects <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    assert batch.proof_nodes == sum(row.proof_nodes for row in batch.rows)
    assert batch.proof_objects == sum(row.proof_objects for row in batch.rows)
    assert batch.annotation_occurrences == sum(
        row.annotation_occurrences for row in batch.rows
    )
    assert all(check((), row.certificate, row.curried_target) for row in batch.rows)
    assert batch.rows[0].curried_target == batch.rows[0].target
    assert batch.rows[1].curried_target != batch.rows[1].target
    assert not check((), batch.rows[1].certificate, batch.rows[1].target)
    assert verify_quadratic_reciprocity_body_batch(batch, plan=plan) is batch
    assert (
        v15.ALPHA_EDITION.by_name[QR_ROOT_NAME].evidence
        is v15.EvidenceStatus.PENDING_LAYERED_CLOSURE
    )


@pytest.mark.parametrize(
    "names,match",
    [
        ((), "between 1 and"),
        (("zero_add",) * 17, "between 1 and"),
        (("zero_add", "zero_add"), "repeats"),
        (("mul_one", "zero_add"), "unfinished"),
        (("invented",), "unknown"),
    ],
)
def test_body_constructor_rejects_unsafe_or_unready_requests(
    plan,
    names,
    match,
) -> None:
    with pytest.raises(QuadraticReciprocityClosureError, match=match):
        construct_quadratic_reciprocity_body_batch(names, plan=plan)


def test_changed_hash_surface_metrics_and_proof_fail_closed(
    plan,
    first_actual_batch,
) -> None:
    batch = first_actual_batch
    with pytest.raises(QuadraticReciprocityClosureError, match="snapshot"):
        verify_quadratic_reciprocity_body_batch(
            replace(batch, graph_sha256="0" * 64),
            plan=plan,
        )
    with pytest.raises(QuadraticReciprocityClosureError, match="cumulative"):
        verify_quadratic_reciprocity_body_batch(
            replace(batch, proof_nodes=batch.proof_nodes + 1),
            plan=plan,
        )

    first = batch.rows[0]
    changed_target = replace(first, curried_target=Eq(Zero(), Succ(Zero())))
    with pytest.raises(QuadraticReciprocityClosureError, match="curried target"):
        verify_quadratic_reciprocity_body_batch(
            replace(batch, rows=(changed_target,) + batch.rows[1:]),
            plan=plan,
        )

    changed_body = replace(first, certificate=EqRefl(Zero()))
    with pytest.raises(QuadraticReciprocityClosureError, match="envelope|kernel"):
        verify_quadratic_reciprocity_body_batch(
            replace(batch, rows=(changed_body,) + batch.rows[1:]),
            plan=plan,
        )

    classical_body = replace(first, certificate=DNE(Eq(Zero(), Zero())))
    with pytest.raises(QuadraticReciprocityClosureError, match="resource envelope"):
        verify_quadratic_reciprocity_body_batch(
            replace(batch, rows=(classical_body,) + batch.rows[1:]),
            plan=plan,
        )


def test_partial_batches_and_receipts_never_establish_the_qr_root(
    plan,
    first_actual_batch,
) -> None:
    with pytest.raises(QuadraticReciprocityClosureError, match="all 557"):
        assemble_quadratic_reciprocity_root((first_actual_batch,), plan=plan)
    with pytest.raises(QuadraticReciprocityClosureError, match="all 557"):
        assemble_quadratic_reciprocity_root((), plan=plan)
    with pytest.raises(QuadraticReciprocityClosureError, match="all 557"):
        assemble_quadratic_reciprocity_proof_bundle(
            (first_actual_batch,),
            plan=plan,
        )
    with pytest.raises(QuadraticReciprocityClosureError, match="boolean"):
        assemble_quadratic_reciprocity_root(
            (first_actual_batch,),
            plan=plan,
            intern_bodies=1,
        )
    assert (
        v15.ALPHA_EDITION.by_name[QR_ROOT_NAME].evidence
        is v15.EvidenceStatus.PENDING_LAYERED_CLOSURE
    )


def test_canonical_checkpoint_contains_and_rechecks_every_actual_proof(
    plan,
    first_actual_batch,
    first_actual_checkpoint,
) -> None:
    assert first_actual_checkpoint.endswith("\n")
    payload = json.loads(first_actual_checkpoint)
    assert payload[0] == QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_FORMAT
    assert len(payload[4]) == 3
    assert all(type(row[5]) is list for row in payload[4])

    decoded = decode_quadratic_reciprocity_body_batch(
        first_actual_checkpoint,
        plan=plan,
    )
    assert decoded.names == first_actual_batch.names
    assert decoded.proof_nodes == first_actual_batch.proof_nodes
    # Canonical self-contained proof trees do not inherit Python identity
    # sharing from the original in-memory body; every occurrence is charged.
    assert decoded.proof_objects == decoded.proof_nodes
    assert all(
        check((), row.certificate, row.curried_target)
        for row in decoded.rows
    )
    assert encode_quadratic_reciprocity_body_batch(decoded, plan=plan) == (
        first_actual_checkpoint
    )


def test_checkpoint_rejects_noncanonical_provenance_and_false_proof(
    plan,
    first_actual_checkpoint,
) -> None:
    with pytest.raises(QuadraticReciprocityClosureError, match="canonical"):
        decode_quadratic_reciprocity_body_batch(
            first_actual_checkpoint.rstrip("\n"),
            plan=plan,
        )

    source_changed = json.loads(first_actual_checkpoint)
    source_changed[1] = "0" * 64
    changed_payload = json.dumps(
        source_changed,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"
    with pytest.raises(QuadraticReciprocityClosureError, match="snapshot"):
        decode_quadratic_reciprocity_body_batch(changed_payload, plan=plan)

    false_proof = json.loads(first_actual_checkpoint)
    false_proof[4][0][5] = ["eq_refl", ["zero"]]
    false_payload = json.dumps(
        false_proof,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"
    with pytest.raises(QuadraticReciprocityClosureError, match="envelope|kernel"):
        decode_quadratic_reciprocity_body_batch(false_payload, plan=plan)


def test_checkpoint_rejects_malformed_tags_rows_and_reviewed_size(
    plan,
    first_actual_checkpoint,
    monkeypatch,
) -> None:
    import peano_lab.library.quadratic_reciprocity_closure as closure

    malformed = json.loads(first_actual_checkpoint)
    malformed[4][0][5] = ["non_kernel_proof"]
    payload = json.dumps(
        malformed,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"
    with pytest.raises(QuadraticReciprocityClosureError, match="malformed"):
        decode_quadratic_reciprocity_body_batch(payload, plan=plan)

    too_many = json.loads(first_actual_checkpoint)
    too_many[4] = [too_many[4][0]] * 17
    payload = json.dumps(
        too_many,
        ensure_ascii=False,
        separators=(",", ":"),
    ) + "\n"
    with pytest.raises(QuadraticReciprocityClosureError, match="row count"):
        decode_quadratic_reciprocity_body_batch(payload, plan=plan)

    monkeypatch.setattr(
        closure,
        "MAX_QUADRATIC_RECIPROCITY_BODY_CHECKPOINT_BYTES",
        len(first_actual_checkpoint.encode("utf-8")) - 1,
    )
    with pytest.raises(QuadraticReciprocityClosureError, match="transport"):
        decode_quadratic_reciprocity_body_batch(first_actual_checkpoint, plan=plan)


def test_checkpoint_persistence_rechecks_actual_proofs_without_overwrite(
    plan,
    first_actual_batch,
    tmp_path,
) -> None:
    path = write_quadratic_reciprocity_body_checkpoint(
        first_actual_batch,
        tmp_path,
        plan=plan,
    )
    assert path.name == "qr-body-0000-0002.json"
    decoded = load_quadratic_reciprocity_body_checkpoint(path, plan=plan)
    assert decoded.names == first_actual_batch.names
    assert all(check((), row.certificate, row.curried_target) for row in decoded.rows)

    with pytest.raises(QuadraticReciprocityClosureError, match="fresh"):
        write_quadratic_reciprocity_body_checkpoint(
            first_actual_batch,
            tmp_path,
            plan=plan,
        )

    wrong_name = tmp_path / "not-the-checked-node-range.json"
    wrong_name.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
    with pytest.raises(QuadraticReciprocityClosureError, match="filename"):
        load_quadratic_reciprocity_body_checkpoint(wrong_name, plan=plan)


def test_durable_complete_qr_bundle_rechecks_every_real_kernel_body(
    plan,
) -> None:
    artifact = (
        Path(__file__).resolve().parents[3]
        / "research"
        / "arithmetic-library"
        / "artifacts"
        / "quadratic-reciprocity-proof-bundle-v1.json"
    )
    payload = artifact.read_text(encoding="utf-8")
    assert len(payload.encode("utf-8")) == 2_790_229
    assert sha256(payload.encode("utf-8")).hexdigest() == (
        "3cd040d145f1004d07d277c66a3ffbcb355cd9c4b21938d79a6ec51b4258709c"
    )

    checked = check_encoded_proof_bundle(payload)
    assert checked.node_count == len(plan.rows) == 557
    assert checked.kernel_calls == 557
    assert checked.dependency_edges == plan.dependency_edge_count == 1_787
    assert checked.total_body_nodes == 41_722
    assert checked.root == 556
