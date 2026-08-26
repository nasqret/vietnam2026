"""Exact original-kernel closure of every constructive Alpha-v20 theorem."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import editions_v19 as v19
from peano_lab.library.alpha_enrollment_v20 import (
    BERTRAND_CHAIN_ROOT_NAME,
    BERTRAND_MULTIPLICITY_ROOT_NAME,
    CONTINUED_FRACTION_ROOT_NAME,
    MATRIX_DOT_PRODUCT_ROOT_NAME,
    POLYNOMIAL_HORNER_ROOT_NAME,
    alpha_v20_enrollment,
)
from peano_lab.library.campaign_next_layer_closure import (
    EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_NEXT_LAYER_BUNDLE_BYTES,
    EXPECTED_NEXT_LAYER_BUNDLE_EDGE_COUNT,
    EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_NEXT_LAYER_BUNDLE_SHA256,
    EXPECTED_NEXT_LAYER_DEPENDENCY_EDGE_COUNT,
    EXPECTED_NEXT_LAYER_FRONTIER_COUNT,
    EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256,
    EXPECTED_NEXT_LAYER_PARENT_COUNT,
    EXPECTED_NEXT_LAYER_REBUILT_BODY_COUNT,
    EXPECTED_NEXT_LAYER_REBUILT_PARENT_COUNT,
    EXPECTED_NEXT_LAYER_REUSED_BODY_COUNT,
    EXPECTED_NEXT_LAYER_ROOT_COUNT,
    EXPECTED_NEXT_LAYER_SOURCE_COUNTS,
    EXPECTED_NEXT_LAYER_THEOREM_COUNT,
    NEXT_LAYER_ARTIFACT_FILENAME,
    NextLayerClosureError,
    _body_metrics,
    _curried_target,
    _reconstruct_body,
    _reused_parent_bodies,
    _spec_table,
    assemble_next_layer_proof_bundle,
    check_next_layer_proof_bundle,
    checked_next_layer_proof_bundle,
    next_layer_closure_plan,
)
from peano_lab.library.frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from peano_lab.library.proof_bundle import ProofBundle


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research" / "arithmetic-library" / "artifacts" / NEXT_LAYER_ARTIFACT_FILENAME
)


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_next_layer_proof_bundle()


def test_exact_immutable_parent_and_all_thirty_nine_new_theorems_are_preserved() -> None:
    plan = next_layer_closure_plan()
    enrollment = alpha_v20_enrollment()

    assert len(v19.ALPHA_ENTRIES) == len(v19.ALPHA_CHECKED_SPECS) == 1_737
    assert plan.parent_alpha_identity_sha256 == v19.ALPHA_V19_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v19.ALPHA_V19_ENROLLMENT_SHA256
    assert len(plan.frontier_names) == EXPECTED_NEXT_LAYER_FRONTIER_COUNT == 39
    assert plan.frontier_names == tuple(item.name for item in enrollment.frontier_specs)
    assert all(name not in v19.ALPHA_EDITION.by_name for name in plan.frontier_names)


def test_frozen_full_transitive_surface_and_all_four_reused_parent_sources() -> None:
    plan = next_layer_closure_plan()
    assert len(plan.rows) == EXPECTED_NEXT_LAYER_THEOREM_COUNT == 589
    assert sum(not row.new_theorem for row in plan.rows) == EXPECTED_NEXT_LAYER_PARENT_COUNT == 550
    assert len(plan.reused_rows) == EXPECTED_NEXT_LAYER_REUSED_BODY_COUNT == 547
    assert len(plan.rebuilt_rows) == EXPECTED_NEXT_LAYER_REBUILT_BODY_COUNT == 42
    assert (
        sum(row.source == "parent_rebuild" for row in plan.rows)
        == EXPECTED_NEXT_LAYER_REBUILT_PARENT_COUNT
        == 3
    )
    assert Counter(row.source for row in plan.rows) == EXPECTED_NEXT_LAYER_SOURCE_COUNTS
    assert plan.dependency_edge_count == EXPECTED_NEXT_LAYER_DEPENDENCY_EDGE_COUNT == 2_033
    assert plan.ordered_names_sha256 == EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256
    assert sha256("\n".join(row.name for row in plan.rows).encode()).hexdigest() == (
        EXPECTED_NEXT_LAYER_ORDERED_NAMES_SHA256
    )
    assert tuple(row.name for row in plan.rows if row.source == "parent_rebuild") == (
        "beta_pointwise_mul_prefix_extend",
        "beta_pointwise_mul_prefix_exists",
        "cell_constructor",
    )


def test_twelve_maximal_roots_cover_every_parent_and_all_new_campaigns() -> None:
    plan = next_layer_closure_plan()
    assert len(plan.root_names) == EXPECTED_NEXT_LAYER_ROOT_COUNT == 12
    assert {
        MATRIX_DOT_PRODUCT_ROOT_NAME,
        BERTRAND_MULTIPLICITY_ROOT_NAME,
        BERTRAND_CHAIN_ROOT_NAME,
        CONTINUED_FRACTION_ROOT_NAME,
    } <= set(plan.root_names)

    rows = {row.name: row for row in plan.rows}
    assert POLYNOMIAL_HORNER_ROOT_NAME in rows
    selected: set[str] = set()
    pending = list(plan.root_names)
    while pending:
        name = pending.pop()
        if name not in selected:
            selected.add(name)
            pending.extend(rows[name].dependencies)
    assert selected == set(rows)
    assert set(plan.frontier_names) <= selected


@pytest.mark.parametrize(
    "name", ("cell_constructor", CONTINUED_FRACTION_ROOT_NAME)
)
def test_reconstruction_checks_actual_parent_and_new_bodies_under_existing_caps(
    name: str,
) -> None:
    table = _spec_table()
    proof = _reconstruct_body(table[name], table)
    target = _curried_target(table[name], table)
    nodes, objects = _body_metrics(
        proof,
        nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    )
    assert check((), proof, target)
    assert 0 < nodes <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 0 < objects <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS


@pytest.mark.parametrize("batch_size", (0, -1, True, 1.5, MAX_FRONTIER_CLOSURE_MICROBATCH + 1))
def test_invalid_microbatch_cap_fails_before_loading_heavy_artifacts(batch_size) -> None:
    with pytest.raises(NextLayerClosureError, match="1..16"):
        assemble_next_layer_proof_bundle(batch_size=batch_size)


def test_canonical_artifact_has_exact_frozen_genuine_proof_bytes() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == EXPECTED_NEXT_LAYER_BUNDLE_BYTES
    assert sha256(payload).hexdigest() == EXPECTED_NEXT_LAYER_BUNDLE_SHA256


def test_original_kernel_independently_accepts_all_five_hundred_ninety_bodies(
    actual_bundle,
) -> None:
    bundle, receipt = actual_bundle
    assert type(bundle) is ProofBundle
    assert len(bundle.nodes) == EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT == 590
    assert bundle.root == EXPECTED_NEXT_LAYER_THEOREM_COUNT == 589
    assert receipt.node_count == receipt.kernel_calls == EXPECTED_NEXT_LAYER_BUNDLE_NODE_COUNT
    assert receipt.dependency_edges == EXPECTED_NEXT_LAYER_BUNDLE_EDGE_COUNT == 2_045
    assert receipt.total_body_nodes == EXPECTED_NEXT_LAYER_BUNDLE_BODY_PROOF_NODES
    assert type(bundle.nodes[-1].target) is And
    assert len(bundle.nodes[-1].dependencies) == EXPECTED_NEXT_LAYER_ROOT_COUNT


def test_checker_rejects_changed_exact_theorem_dependency_and_root(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    plan = next_layer_closure_plan()
    row = next(item for item in plan.rows if item.dependencies)
    changed = replace(bundle.nodes[row.node_id], dependencies=())
    nodes = list(bundle.nodes)
    nodes[row.node_id] = changed
    with pytest.raises(NextLayerClosureError, match="frozen theorem"):
        check_next_layer_proof_bundle(
            ProofBundle(tuple(nodes), bundle.root), bundle.nodes[-1].target
        )
    with pytest.raises(NextLayerClosureError, match="node surface"):
        check_next_layer_proof_bundle(replace(bundle, root=0), bundle.nodes[-1].target)


def test_checker_rejects_synthetic_conjunction_and_actual_body_mutations(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    synthetic = replace(bundle.nodes[-1], body=Hyp(0))
    with pytest.raises(NextLayerClosureError, match="synthetic"):
        check_next_layer_proof_bundle(
            replace(bundle, nodes=bundle.nodes[:-1] + (synthetic,)),
            bundle.nodes[-1].target,
        )
    first = replace(bundle.nodes[0], body=Hyp(0))
    with pytest.raises(NextLayerClosureError, match="kernel rejected"):
        check_next_layer_proof_bundle(
            replace(bundle, nodes=(first,) + bundle.nodes[1:]),
            bundle.nodes[-1].target,
        )


def test_frozen_parent_provider_rejects_changed_bytes_before_reuse(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peano_lab.library.campaign_next_layer_closure as closure

    damaged = tmp_path / "damaged.json"
    damaged.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(closure, "_artifact_path", lambda _filename: damaged)
    with pytest.raises(NextLayerClosureError, match="parent proof artifact changed"):
        _reused_parent_bodies()


def test_missing_canonical_source_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peano_lab.library.campaign_next_layer_closure as closure

    checked_next_layer_proof_bundle.cache_clear()
    monkeypatch.setattr(
        closure,
        "_artifact_path",
        lambda _filename: tmp_path / "missing-next-layer.json",
    )
    try:
        with pytest.raises(NextLayerClosureError, match="unavailable"):
            checked_next_layer_proof_bundle()
    finally:
        checked_next_layer_proof_bundle.cache_clear()
