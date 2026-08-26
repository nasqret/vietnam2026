"""Exact, resource-bounded original-kernel closure of the Alpha-v21 frontier."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import editions_v20 as v20
from peano_lab.library import editions_v21 as v21
from peano_lab.library.alpha_enrollment_v21 import (
    BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
    EUCLIDEAN_EXECUTION_ROOT_NAME,
    FRONTIER_V21_EXPECTED_COUNT,
    MATRIX_CODED_PRODUCT_ROOT_NAME,
    SIGNED_DOT_PRODUCT_ROOT_NAME,
    SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
    alpha_v21_enrollment,
)
from peano_lab.library.campaign_advanced_layer_closure import (
    ADVANCED_LAYER_ARTIFACT_FILENAME,
    EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES,
    EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT,
    EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256,
    EXPECTED_ADVANCED_LAYER_DEPENDENCY_EDGE_COUNT,
    EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256,
    EXPECTED_ADVANCED_LAYER_ROOT_COUNT,
    EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS,
    EXPECTED_ADVANCED_LAYER_THEOREM_COUNT,
    AdvancedLayerClosureError,
    _body_metrics,
    _parent_providers,
    _reconstruct_body,
    _spec_table,
    advanced_layer_closure_plan,
    assemble_advanced_layer_proof_bundle,
    check_advanced_layer_proof_bundle,
    checked_advanced_layer_proof_bundle,
)
from peano_lab.library.campaign_next_layer_closure import (
    EXPECTED_NEXT_LAYER_BUNDLE_BYTES,
    EXPECTED_NEXT_LAYER_BUNDLE_SHA256,
    NEXT_LAYER_ARTIFACT_FILENAME,
)
from peano_lab.library.frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from peano_lab.library.proof_bundle import ProofBundle
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY
    / "research"
    / "arithmetic-library"
    / "artifacts"
    / ADVANCED_LAYER_ARTIFACT_FILENAME
)


@pytest.fixture(scope="module")
def actual_bundle():
    """Share the ordinary v21 runtime's independently checked 1 MB cache."""

    return v21.checked_advanced_layer_bundle()


def test_exact_checked_v20_parent_and_all_fifty_four_new_rows_are_preserved() -> None:
    plan = advanced_layer_closure_plan()
    enrollment = alpha_v21_enrollment()

    assert len(v20.ALPHA_ENTRIES) == len(v20.ALPHA_CHECKED_SPECS) == 1_776
    assert plan.parent_alpha_identity_sha256 == v20.ALPHA_V20_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v20.ALPHA_V20_ENROLLMENT_SHA256
    assert len(plan.frontier_names) == FRONTIER_V21_EXPECTED_COUNT == 54
    assert plan.frontier_names == tuple(item.name for item in enrollment.frontier_specs)
    assert all(name not in v20.ALPHA_EDITION.by_name for name in plan.frontier_names)


def test_frozen_complete_transitive_cone_has_exact_ordinary_parent_sources() -> None:
    plan = advanced_layer_closure_plan()

    assert len(plan.rows) == EXPECTED_ADVANCED_LAYER_THEOREM_COUNT == 208
    assert sum(not row.new_theorem for row in plan.rows) == 154
    assert len(plan.rebuilt_rows) == FRONTIER_V21_EXPECTED_COUNT == 54
    assert Counter(row.source for row in plan.rows) == EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS
    assert EXPECTED_ADVANCED_LAYER_SOURCE_COUNTS == {
        "v19_frontier": 132,
        "v20_next_layer": 13,
        "residual": 9,
        "new": 54,
    }
    assert plan.dependency_edge_count == EXPECTED_ADVANCED_LAYER_DEPENDENCY_EDGE_COUNT == 464
    assert plan.ordered_names_sha256 == EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256
    assert sha256("\n".join(row.name for row in plan.rows).encode()).hexdigest() == (
        EXPECTED_ADVANCED_LAYER_ORDERED_NAMES_SHA256
    )


def test_frozen_historical_provider_metadata_is_exact_without_decoding_big_bundle() -> None:
    provider = next(item for item in _parent_providers() if item.label == "v20_next_layer")

    assert provider.filename == NEXT_LAYER_ARTIFACT_FILENAME
    assert provider.bytes == EXPECTED_NEXT_LAYER_BUNDLE_BYTES == 14_775_673
    assert provider.digest == EXPECTED_NEXT_LAYER_BUNDLE_SHA256
    assert len(provider.rows) == 589


def test_all_twenty_seven_maximal_roots_cover_the_exact_transitive_cone() -> None:
    plan = advanced_layer_closure_plan()
    rows = {row.name: row for row in plan.rows}

    assert len(plan.root_names) == EXPECTED_ADVANCED_LAYER_ROOT_COUNT == 27
    assert {
        SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_DOT_PRODUCT_ROOT_NAME,
        EUCLIDEAN_EXECUTION_ROOT_NAME,
        BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
    } <= set(plan.root_names)
    assert MATRIX_CODED_PRODUCT_ROOT_NAME in rows

    selected: set[str] = set()
    pending = list(plan.root_names)
    while pending:
        name = pending.pop()
        if name not in selected:
            selected.add(name)
            pending.extend(rows[name].dependencies)
    assert selected == set(rows)
    assert set(plan.frontier_names) <= selected


def test_small_dependency_free_candidate_has_a_real_empty_context_kernel_proof() -> None:
    table = _spec_table()
    theorem = table["signed_pair_product_exists"]

    assert theorem.dependencies == ()
    proof = _reconstruct_body(theorem, table)
    nodes, objects = _body_metrics(
        proof,
        nodes=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    )
    assert check((), proof, _closed_formula(theorem.statement))
    assert 0 < nodes <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert 0 < objects <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS


@pytest.mark.parametrize("batch_size", (0, -1, True, 1.5, MAX_FRONTIER_CLOSURE_MICROBATCH + 1))
def test_invalid_microbatch_cap_fails_before_loading_any_historical_proofs(batch_size) -> None:
    with pytest.raises(AdvancedLayerClosureError, match="1..16"):
        assemble_advanced_layer_proof_bundle(batch_size=batch_size)


def test_canonical_artifact_has_exact_frozen_self_contained_proof_bytes() -> None:
    payload = ARTIFACT.read_bytes()

    assert len(payload) == EXPECTED_ADVANCED_LAYER_BUNDLE_BYTES == 1_005_317
    assert sha256(payload).hexdigest() == EXPECTED_ADVANCED_LAYER_BUNDLE_SHA256


def test_original_kernel_independently_accepts_every_one_of_209_bodies(actual_bundle) -> None:
    bundle, receipt, positions = actual_bundle

    assert type(bundle) is ProofBundle
    assert len(bundle.nodes) == EXPECTED_ADVANCED_LAYER_BUNDLE_NODE_COUNT == 209
    assert bundle.root == EXPECTED_ADVANCED_LAYER_THEOREM_COUNT == 208
    assert receipt.node_count == receipt.kernel_calls == len(bundle.nodes)
    assert receipt.dependency_edges == EXPECTED_ADVANCED_LAYER_BUNDLE_EDGE_COUNT == 491
    assert receipt.total_body_nodes == EXPECTED_ADVANCED_LAYER_BUNDLE_BODY_PROOF_NODES == 10_304
    assert type(bundle.nodes[-1].target) is And
    assert len(bundle.nodes[-1].dependencies) == EXPECTED_ADVANCED_LAYER_ROOT_COUNT
    assert len(positions) == EXPECTED_ADVANCED_LAYER_THEOREM_COUNT
    assert set(v21.FRONTIER_NEW_NAMES) <= positions.keys()


def test_exact_theorem_dependency_and_packaging_root_mutations_fail_closed(actual_bundle) -> None:
    bundle, _receipt, _positions = actual_bundle
    plan = advanced_layer_closure_plan()
    row = next(item for item in plan.rows if item.dependencies)
    changed = replace(bundle.nodes[row.node_id], dependencies=())
    nodes = list(bundle.nodes)
    nodes[row.node_id] = changed

    with pytest.raises(AdvancedLayerClosureError, match="exact theorem"):
        check_advanced_layer_proof_bundle(
            ProofBundle(tuple(nodes), bundle.root), bundle.nodes[-1].target
        )
    with pytest.raises(AdvancedLayerClosureError, match="exact nodes"):
        check_advanced_layer_proof_bundle(replace(bundle, root=0), bundle.nodes[-1].target)


def test_synthetic_conjunction_and_real_ordinary_body_mutations_fail_closed(actual_bundle) -> None:
    bundle, _receipt, _positions = actual_bundle
    synthetic = replace(bundle.nodes[-1], body=Hyp(0))

    with pytest.raises(AdvancedLayerClosureError, match="synthetic conjunction"):
        check_advanced_layer_proof_bundle(
            replace(bundle, nodes=bundle.nodes[:-1] + (synthetic,)),
            bundle.nodes[-1].target,
        )
    first = replace(bundle.nodes[0], body=Hyp(0))
    with pytest.raises(AdvancedLayerClosureError, match="kernel rejected"):
        check_advanced_layer_proof_bundle(
            replace(bundle, nodes=(first,) + bundle.nodes[1:]),
            bundle.nodes[-1].target,
        )


def test_missing_canonical_source_never_grants_checked_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peano_lab.library.campaign_advanced_layer_closure as closure

    checked_advanced_layer_proof_bundle.cache_clear()
    monkeypatch.setattr(
        closure,
        "_artifact_path",
        lambda _filename: tmp_path / "missing-advanced-layer.json",
    )
    try:
        with pytest.raises(AdvancedLayerClosureError, match="unavailable"):
            checked_advanced_layer_proof_bundle()
    finally:
        checked_advanced_layer_proof_bundle.cache_clear()
