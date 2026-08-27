"""Exact self-contained kernel closure and bounded first-wave proof resources."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.formulas import And, Bot
from peano_lab.kernel.proofs import AndIntro, Hyp, ImpIntro
from peano_lab.library import editions_v25 as v25
from peano_lab.library import campaign_first_wave_closure as closure
from peano_lab.library.campaign_breakthrough_layer_closure import (
    BREAKTHROUGH_LAYER_ARTIFACT_FILENAME,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES,
    EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256,
)
from peano_lab.library.frontier_promotion import MAX_FRONTIER_CLOSURE_MICROBATCH
from peano_lab.library.proof_bundle import ProofBundle


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = REPOSITORY / "research/arithmetic-library/artifacts" / closure.FIRST_WAVE_ARTIFACT_FILENAME


@pytest.fixture(scope="module")
def actual_bundle():
    return closure.checked_first_wave_proof_bundle()


def test_checked_v25_parent_and_all_actual_first_wave_endpoints_are_retained() -> None:
    plan = closure.first_wave_plan()
    assert len(v25.ALPHA_ENTRIES) == len(v25.ALPHA_CHECKED_SPECS) == 2_080
    assert plan.parent_alpha_identity_sha256 == v25.ALPHA_V25_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v25.ALPHA_V25_ENROLLMENT_SHA256
    assert plan.frontier_names == tuple(row.name for row in closure.first_wave_specs())
    assert len(plan.frontier_names) == closure.EXPECTED_FIRST_WAVE_FRONTIER_COUNT
    assert all(name not in v25.ALPHA_EDITION.by_name for name in plan.frontier_names)
    assert {
        "coprime_square_product_factors", "square_divides_square_root",
        "pythagorean_positive_primitive_classification", "fermat_four_strict_descent_proved",
        "fermat_four_no_square", "fermat_four_no_fourth", "fermat_four_complete_classification",
        "fermat_four_positive_sum_not_square",
    } <= set(plan.frontier_names)


def test_frozen_exact_dependency_cone_has_smallest_historical_sources() -> None:
    plan = closure.first_wave_plan()
    assert len(plan.rows) == closure.EXPECTED_FIRST_WAVE_THEOREM_COUNT
    assert len(plan.root_names) == closure.EXPECTED_FIRST_WAVE_ROOT_COUNT
    assert plan.dependency_edge_count == closure.EXPECTED_FIRST_WAVE_DEPENDENCY_EDGE_COUNT
    assert plan.ordered_names_sha256 == closure.EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256
    assert Counter(row.source for row in plan.rows) == closure.EXPECTED_FIRST_WAVE_SOURCE_COUNTS
    providers = closure._parent_providers()
    assert tuple(item.bytes for item in providers) == tuple(sorted(item.bytes for item in providers))
    seen: set[str] = set()
    for row in plan.rows:
        assert set(row.dependencies) <= seen
        if not row.new_theorem:
            first = next((provider.label for provider in providers if row.name in {item.name for item in provider.rows}), "parent_rebuild")
            assert row.source == first
        seen.add(row.name)


def test_exact_v25_provider_metadata_preserves_frozen_certificate() -> None:
    provider = next(item for item in closure._parent_providers() if item.label == "v25_breakthrough_layer")
    assert provider.filename == BREAKTHROUGH_LAYER_ARTIFACT_FILENAME
    assert provider.bytes == EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_BYTES == 1_041_166
    assert provider.digest == EXPECTED_BREAKTHROUGH_LAYER_BUNDLE_SHA256
    assert len(provider.rows) == 301


def test_actual_maximal_roots_cover_every_transitive_proof_dependency() -> None:
    plan = closure.first_wave_plan()
    rows = {row.name: row for row in plan.rows}
    pending = list(plan.root_names)
    selected: set[str] = set()
    while pending:
        name = pending.pop()
        if name not in selected:
            selected.add(name)
            pending.extend(rows[name].dependencies)
    assert selected == set(rows)
    assert set(plan.frontier_names) <= selected
    assert sha256("\n".join(row.name for row in plan.rows).encode()).hexdigest() == closure.EXPECTED_FIRST_WAVE_ORDERED_NAMES_SHA256


@pytest.mark.parametrize("batch_size", (0, -1, True, 1.5, MAX_FRONTIER_CLOSURE_MICROBATCH + 1))
def test_invalid_batch_size_is_rejected_before_reading_parent_proofs(batch_size) -> None:
    with pytest.raises(closure.FirstWaveError, match="1..16"):
        closure.assemble_first_wave_proof_bundle(batch_size=batch_size)


def test_microbatch_budget_charges_object_identity_count_not_depth() -> None:
    left, right = Hyp(0), Hyp(0)
    body = ImpIntro(AndIntro(left, right))
    assert closure._body_metrics(body, nodes=4, objects=4) == (4, 4)
    with pytest.raises(closure.FirstWaveError, match="caps"):
        closure._body_metrics(body, nodes=4, objects=3)
    shared = ImpIntro(AndIntro(left, left))
    assert closure._body_metrics(shared, nodes=4, objects=3) == (4, 3)
    with pytest.raises(closure.FirstWaveError, match="caps"):
        closure._body_metrics(shared, nodes=3, objects=3)


def test_microbatch_object_budget_accumulates_each_separate_body() -> None:
    first = ImpIntro(AndIntro(Hyp(0), Hyp(0)))
    second = ImpIntro(AndIntro(Hyp(0), Hyp(0)))
    nodes, identities = closure._body_metrics(first, nodes=8, objects=7)
    assert (nodes, identities) == (4, 4)
    with pytest.raises(closure.FirstWaveError, match="caps"):
        closure._body_metrics(second, nodes=8 - nodes, objects=7 - identities)


def test_canonical_artifact_has_exact_frozen_self_contained_bytes() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == closure.EXPECTED_FIRST_WAVE_BUNDLE_BYTES > 0
    assert sha256(payload).hexdigest() == closure.EXPECTED_FIRST_WAVE_BUNDLE_SHA256


def test_original_kernel_checks_every_actual_ordinary_proof_body(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    assert type(bundle) is ProofBundle
    assert len(bundle.nodes) == closure.EXPECTED_FIRST_WAVE_BUNDLE_NODE_COUNT
    assert bundle.root == closure.EXPECTED_FIRST_WAVE_THEOREM_COUNT
    assert receipt.node_count == receipt.kernel_calls == len(bundle.nodes)
    assert receipt.dependency_edges == closure.EXPECTED_FIRST_WAVE_BUNDLE_EDGE_COUNT
    assert receipt.total_body_nodes == closure.EXPECTED_FIRST_WAVE_BUNDLE_BODY_PROOF_NODES
    assert isinstance(bundle.nodes[-1].target, And)
    assert len(bundle.nodes[-1].dependencies) == closure.EXPECTED_FIRST_WAVE_ROOT_COUNT


def test_changed_theorem_edges_and_packaging_root_are_rejected(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    row = next(item for item in closure.first_wave_plan().rows if item.dependencies)
    nodes = list(bundle.nodes)
    nodes[row.node_id] = replace(nodes[row.node_id], dependencies=())
    with pytest.raises(closure.FirstWaveError, match="exact theorem"):
        closure.check_first_wave_proof_bundle(ProofBundle(tuple(nodes), bundle.root), bundle.nodes[-1].target)
    with pytest.raises(closure.FirstWaveError, match="exact nodes"):
        closure.check_first_wave_proof_bundle(replace(bundle, root=0), bundle.nodes[-1].target)


def test_forged_synthetic_conjunction_and_real_proof_body_are_rejected(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    synthetic = replace(bundle.nodes[-1], body=Hyp(0))
    with pytest.raises(closure.FirstWaveError, match="synthetic conjunction"):
        closure.check_first_wave_proof_bundle(replace(bundle, nodes=bundle.nodes[:-1] + (synthetic,)), bundle.nodes[-1].target)
    forged = replace(bundle.nodes[0], body=Hyp(0))
    with pytest.raises(closure.FirstWaveError, match="kernel rejected"):
        closure.check_first_wave_proof_bundle(replace(bundle, nodes=(forged,) + bundle.nodes[1:]), bundle.nodes[-1].target)


def test_false_root_target_cannot_borrow_a_real_certificate(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    with pytest.raises(closure.FirstWaveError, match="synthetic conjunction"):
        closure.check_first_wave_proof_bundle(bundle, Bot())


def test_missing_canonical_artifact_never_authorizes_checked_use(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    closure.checked_first_wave_proof_bundle.cache_clear()
    monkeypatch.setattr(closure, "_artifact_path", lambda _filename: tmp_path / "missing-first-wave.json")
    try:
        with pytest.raises(closure.FirstWaveError, match="unavailable"):
            closure.checked_first_wave_proof_bundle()
    finally:
        closure.checked_first_wave_proof_bundle.cache_clear()


def test_empty_artifact_seal_never_authorizes_checked_use(monkeypatch: pytest.MonkeyPatch) -> None:
    closure.checked_first_wave_proof_bundle.cache_clear()
    monkeypatch.setattr(closure, "EXPECTED_FIRST_WAVE_BUNDLE_SHA256", "")
    try:
        with pytest.raises(closure.FirstWaveError, match="not been frozen"):
            closure.checked_first_wave_proof_bundle()
    finally:
        closure.checked_first_wave_proof_bundle.cache_clear()
