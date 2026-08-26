"""Exact, bounded, original-kernel closure of the constructive v24 frontier."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import editions_v23 as v23
from peano_lab.library import editions_v24 as v24
from peano_lab.library.alpha_enrollment_v24 import (
    FRONTIER_V24_EXPECTED_COUNT,
    ROOT_STATEMENT_SHA256,
    alpha_v24_enrollment,
)
from peano_lab.library.campaign_milestone_closure import (
    MILESTONE_CLOSURE_ARTIFACT_FILENAME,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_BYTES,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256,
)
from peano_lab.library.campaign_research_layer_closure import (
    EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES,
    EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT,
    EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
    EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256,
    EXPECTED_RESEARCH_LAYER_DEPENDENCY_EDGE_COUNT,
    EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256,
    EXPECTED_RESEARCH_LAYER_ROOT_COUNT,
    EXPECTED_RESEARCH_LAYER_SOURCE_COUNTS,
    EXPECTED_RESEARCH_LAYER_THEOREM_COUNT,
    RESEARCH_LAYER_ARTIFACT_FILENAME,
    ResearchLayerError,
    _parent_providers,
    assemble_research_layer_proof_bundle,
    check_research_layer_proof_bundle,
    checked_research_layer_proof_bundle,
    research_layer_plan,
)
from peano_lab.library.frontier_promotion import MAX_FRONTIER_CLOSURE_MICROBATCH
from peano_lab.library.proof_bundle import ProofBundle


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / RESEARCH_LAYER_ARTIFACT_FILENAME
)


@pytest.fixture(scope="module")
def actual_bundle():
    return v24.checked_research_layer_bundle()


def test_exact_checked_v23_parent_and_every_new_row_are_preserved() -> None:
    plan = research_layer_plan()
    enrollment = alpha_v24_enrollment()
    assert len(v23.ALPHA_ENTRIES) == len(v23.ALPHA_CHECKED_SPECS) == 1_949
    assert plan.parent_alpha_identity_sha256 == v23.ALPHA_V23_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v23.ALPHA_V23_ENROLLMENT_SHA256
    assert len(plan.frontier_names) == FRONTIER_V24_EXPECTED_COUNT
    assert plan.frontier_names == tuple(item.name for item in enrollment.frontier_specs)
    assert all(name not in v23.ALPHA_EDITION.by_name for name in plan.frontier_names)


def test_frozen_complete_transitive_cone_has_exact_ordinary_parent_sources() -> None:
    plan = research_layer_plan()
    assert len(plan.rows) == EXPECTED_RESEARCH_LAYER_THEOREM_COUNT
    assert len(plan.rebuilt_rows) >= FRONTIER_V24_EXPECTED_COUNT
    assert Counter(row.source for row in plan.rows) == EXPECTED_RESEARCH_LAYER_SOURCE_COUNTS
    assert plan.dependency_edge_count == EXPECTED_RESEARCH_LAYER_DEPENDENCY_EDGE_COUNT
    assert plan.ordered_names_sha256 == EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256
    assert sha256("\n".join(row.name for row in plan.rows).encode()).hexdigest() == (
        EXPECTED_RESEARCH_LAYER_ORDERED_NAMES_SHA256
    )


def test_frozen_v23_provider_metadata_is_exact_without_loading_large_history() -> None:
    provider = next(item for item in _parent_providers() if item.label == "v23_milestone_closure")
    assert provider.filename == MILESTONE_CLOSURE_ARTIFACT_FILENAME
    assert provider.bytes == EXPECTED_MILESTONE_CLOSURE_BUNDLE_BYTES == 2_518_315
    assert provider.digest == EXPECTED_MILESTONE_CLOSURE_BUNDLE_SHA256
    assert len(provider.rows) == 616


def test_maximal_roots_cover_the_exact_transitive_cone() -> None:
    plan = research_layer_plan()
    rows = {row.name: row for row in plan.rows}
    assert len(plan.root_names) == EXPECTED_RESEARCH_LAYER_ROOT_COUNT
    assert set(ROOT_STATEMENT_SHA256) <= rows.keys()
    selected: set[str] = set()
    pending = list(plan.root_names)
    while pending:
        name = pending.pop()
        if name not in selected:
            selected.add(name)
            pending.extend(rows[name].dependencies)
    assert selected == set(rows)
    assert set(plan.frontier_names) <= selected


@pytest.mark.parametrize("batch_size", (0, -1, True, 1.5, MAX_FRONTIER_CLOSURE_MICROBATCH + 1))
def test_invalid_microbatch_cap_fails_before_loading_historical_proofs(batch_size) -> None:
    with pytest.raises(ResearchLayerError, match="1..16"):
        assemble_research_layer_proof_bundle(batch_size=batch_size)


def test_canonical_artifact_has_exact_frozen_self_contained_proof_bytes() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == EXPECTED_RESEARCH_LAYER_BUNDLE_BYTES > 0
    assert sha256(payload).hexdigest() == EXPECTED_RESEARCH_LAYER_BUNDLE_SHA256


def test_original_kernel_independently_accepts_every_ordinary_body(actual_bundle) -> None:
    bundle, receipt, positions = actual_bundle
    assert type(bundle) is ProofBundle
    assert len(bundle.nodes) == EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
    assert bundle.root == EXPECTED_RESEARCH_LAYER_THEOREM_COUNT
    assert receipt.node_count == receipt.kernel_calls == len(bundle.nodes)
    assert receipt.dependency_edges == EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES
    assert type(bundle.nodes[-1].target) is And
    assert len(bundle.nodes[-1].dependencies) == EXPECTED_RESEARCH_LAYER_ROOT_COUNT
    assert len(positions) == EXPECTED_RESEARCH_LAYER_THEOREM_COUNT
    assert set(v24.FRONTIER_NEW_NAMES) <= positions.keys()


def test_exact_dependency_and_packaging_root_mutations_fail_closed(actual_bundle) -> None:
    bundle, _receipt, _positions = actual_bundle
    plan = research_layer_plan()
    row = next(item for item in plan.rows if item.dependencies)
    changed = replace(bundle.nodes[row.node_id], dependencies=())
    nodes = list(bundle.nodes)
    nodes[row.node_id] = changed
    with pytest.raises(ResearchLayerError, match="exact theorem"):
        check_research_layer_proof_bundle(
            ProofBundle(tuple(nodes), bundle.root), bundle.nodes[-1].target
        )
    with pytest.raises(ResearchLayerError, match="exact nodes"):
        check_research_layer_proof_bundle(replace(bundle, root=0), bundle.nodes[-1].target)


def test_synthetic_conjunction_and_real_body_mutations_fail_closed(actual_bundle) -> None:
    bundle, _receipt, _positions = actual_bundle
    synthetic = replace(bundle.nodes[-1], body=Hyp(0))
    with pytest.raises(ResearchLayerError, match="synthetic conjunction"):
        check_research_layer_proof_bundle(
            replace(bundle, nodes=bundle.nodes[:-1] + (synthetic,)),
            bundle.nodes[-1].target,
        )
    first = replace(bundle.nodes[0], body=Hyp(0))
    with pytest.raises(ResearchLayerError, match="kernel rejected"):
        check_research_layer_proof_bundle(
            replace(bundle, nodes=(first,) + bundle.nodes[1:]),
            bundle.nodes[-1].target,
        )


def test_missing_canonical_source_never_grants_checked_use(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import peano_lab.library.campaign_research_layer_closure as closure

    checked_research_layer_proof_bundle.cache_clear()
    monkeypatch.setattr(
        closure,
        "_artifact_path",
        lambda _filename: tmp_path / "missing-research-layer.json",
    )
    try:
        with pytest.raises(ResearchLayerError, match="unavailable"):
            checked_research_layer_proof_bundle()
    finally:
        checked_research_layer_proof_bundle.cache_clear()
