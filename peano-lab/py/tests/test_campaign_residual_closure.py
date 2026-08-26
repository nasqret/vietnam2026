"""Exact constructive closure for every remaining Alpha-v18 body-only row."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
from pathlib import Path

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import editions_v18 as v18
from peano_lab.library.campaign_residual_closure import (
    EXPECTED_RESIDUAL_BERTRAND_COUNT,
    EXPECTED_RESIDUAL_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_RESIDUAL_BUNDLE_BYTES,
    EXPECTED_RESIDUAL_BUNDLE_EDGE_COUNT,
    EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT,
    EXPECTED_RESIDUAL_BUNDLE_SHA256,
    EXPECTED_RESIDUAL_DEPENDENCY_EDGE_COUNT,
    EXPECTED_RESIDUAL_K3C_COUNT,
    EXPECTED_RESIDUAL_ORDERED_NAMES_SHA256,
    EXPECTED_RESIDUAL_PROMOTED_NAMES_SHA256,
    EXPECTED_RESIDUAL_PROMOTION_COUNT,
    EXPECTED_RESIDUAL_REBUILT_BODY_COUNT,
    EXPECTED_RESIDUAL_REUSED_BODY_COUNT,
    EXPECTED_RESIDUAL_ROOT_COUNT,
    EXPECTED_RESIDUAL_ROOT_NODE_ID,
    EXPECTED_RESIDUAL_SOURCE_COUNTS,
    EXPECTED_RESIDUAL_SURFACE_SHA256,
    EXPECTED_RESIDUAL_THEOREM_COUNT,
    RESIDUAL_MAXIMAL_ROOT_NAMES,
    RESIDUAL_PROMOTED_NAMES,
    ResidualClosureError,
    _residual_body_script,
    _synthetic_conjunction_body,
    assemble_residual_proof_bundle,
    check_residual_proof_bundle,
    checked_residual_proof_bundle,
    construct_residual_body_microbatch,
    replay_residual_closed_theorem,
    residual_closure_plan,
    residual_pending_layers,
    set_residual_bundle_source,
    verify_residual_body_microbatch,
)
from peano_lab.library.frontier_promotion import (
    MAX_FRONTIER_CLOSURE_MICROBATCH,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
    MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
)
from peano_lab.library.layered_replay import DEFAULT_LAYERED_REPLAY_LIMITS
from peano_lab.library.proof_bundle import ProofBundle


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY
    / "research"
    / "arithmetic-library"
    / "artifacts"
    / "alpha-v19-residual-proof-bundle-v1.json"
)


@pytest.fixture(scope="module")
def actual_bundle():
    return checked_residual_proof_bundle()


def test_exact_parent_release_and_all_eighty_four_unchecked_rows_are_preserved() -> None:
    plan = residual_closure_plan()
    assert plan.parent_alpha_identity_sha256 == v18.ALPHA_V18_IDENTITY_SHA256
    assert plan.parent_alpha_enrollment_sha256 == v18.ALPHA_V18_ENROLLMENT_SHA256
    assert len(v18.ALPHA_ENTRIES) == 1_673
    assert len(v18.ALPHA_CHECKED_SPECS) == 1_589
    assert len(v18.STABLE_ENTRIES) == 432
    assert RESIDUAL_PROMOTED_NAMES == tuple(
        item.spec.name for item in v18.ALPHA_ENTRIES if not item.checked_use
    )
    assert len(RESIDUAL_PROMOTED_NAMES) == EXPECTED_RESIDUAL_PROMOTION_COUNT == 84
    assert sha256("\n".join(RESIDUAL_PROMOTED_NAMES).encode()).hexdigest() == (
        EXPECTED_RESIDUAL_PROMOTED_NAMES_SHA256
    )
    assert all(not v18.ALPHA_EDITION.by_name[name].checked_use for name in RESIDUAL_PROMOTED_NAMES)


def test_exact_transitive_surface_source_precedence_and_pending_layers() -> None:
    plan = residual_closure_plan()
    assert len(plan.rows) == EXPECTED_RESIDUAL_THEOREM_COUNT == 474
    assert len(plan.pending_rows) == EXPECTED_RESIDUAL_PROMOTION_COUNT == 84
    assert len(plan.rebuilt_rows) == EXPECTED_RESIDUAL_REBUILT_BODY_COUNT == 111
    assert len(plan.checked_parent_rows) == 390
    assert len(plan.rows) - len(plan.rebuilt_rows) == EXPECTED_RESIDUAL_REUSED_BODY_COUNT == 363
    assert plan.dependency_edge_count == EXPECTED_RESIDUAL_DEPENDENCY_EDGE_COUNT == 1_412
    assert plan.ordered_names_sha256 == EXPECTED_RESIDUAL_ORDERED_NAMES_SHA256
    assert plan.surface_sha256 == EXPECTED_RESIDUAL_SURFACE_SHA256
    assert Counter(row.source for row in plan.rows) == EXPECTED_RESIDUAL_SOURCE_COUNTS
    assert (
        sum(row.enrollment_origin == "k3c" for row in plan.pending_rows)
        == EXPECTED_RESIDUAL_K3C_COUNT
        == 17
    )
    assert (
        sum(row.enrollment_origin != "k3c" for row in plan.pending_rows)
        == EXPECTED_RESIDUAL_BERTRAND_COUNT
        == 67
    )
    assert [len(layer) for layer in residual_pending_layers()] == [50, 19, 6, 4, 2, 1, 1, 1]


def test_forty_maximal_roots_cover_every_pending_theorem() -> None:
    plan = residual_closure_plan()
    assert plan.roots == RESIDUAL_MAXIMAL_ROOT_NAMES
    assert len(plan.roots) == EXPECTED_RESIDUAL_ROOT_COUNT == 40
    available = {row.name: row for row in plan.rows}
    reached: set[str] = set()
    pending = list(plan.roots)
    while pending:
        name = pending.pop()
        if name in reached:
            continue
        reached.add(name)
        pending.extend(available[name].dependencies)
    assert reached == {row.name for row in plan.rows}
    assert set(RESIDUAL_PROMOTED_NAMES).issubset(reached)


def test_immutable_power_seven_script_gets_only_two_frozen_checked_normalizations() -> None:
    original = v18.ALPHA_EDITION.by_name["pow_two_seven_exact"].spec.script
    transformed = _residual_body_script("pow_two_seven_exact", original)
    assert len(original) == 243
    assert len(transformed) == 39
    assert sum(normalized for _command, normalized in transformed) == 2
    assert all(command == "norm_num" for command, normalized in transformed if normalized)
    with pytest.raises(ResidualClosureError, match="script changed"):
        _residual_body_script("pow_two_seven_exact", original[:-1])


def test_constructor_checks_actual_first_body_under_unchanged_caps() -> None:
    row = residual_closure_plan().rebuilt_rows[0]
    batch = construct_residual_body_microbatch((row.name,))
    assert batch.names == (row.name,)
    assert batch.proof_nodes <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES
    assert batch.proof_objects <= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS
    assert batch.rows[0].envelope_depth <= DEFAULT_LAYERED_REPLAY_LIMITS.max_body_envelope_depth
    assert check((), batch.rows[0].certificate, batch.rows[0].curried_target)
    assert verify_residual_body_microbatch(batch) is batch


@pytest.mark.parametrize(
    "names",
    (
        (),
        ("missing_residual_theorem",),
        ("add_le_cancel_right", "add_le_cancel_right"),
        tuple("add_le_cancel_right" for _ in range(MAX_FRONTIER_CLOSURE_MICROBATCH + 1)),
    ),
)
def test_microbatch_rejects_invalid_names_and_capacity(names: tuple[str, ...]) -> None:
    with pytest.raises(ResidualClosureError):
        construct_residual_body_microbatch(names)


def test_microbatch_rejects_changed_actual_proof_and_missing_predecessor() -> None:
    first = residual_closure_plan().rebuilt_rows[0].name
    actual = construct_residual_body_microbatch((first,))
    mutated = replace(actual.rows[0], certificate=Hyp(0))
    with pytest.raises(ResidualClosureError):
        verify_residual_body_microbatch(replace(actual, rows=(mutated,)))
    with pytest.raises(ResidualClosureError):
        construct_residual_body_microbatch(("cell_list_valid_nil",))


def test_assembly_rejects_partial_actual_evidence() -> None:
    first = residual_closure_plan().rebuilt_rows[0].name
    actual = construct_residual_body_microbatch((first,))
    with pytest.raises(ResidualClosureError, match="all 111"):
        assemble_residual_proof_bundle((actual,))


def test_canonical_artifact_has_exact_frozen_actual_bytes() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == EXPECTED_RESIDUAL_BUNDLE_BYTES
    assert sha256(payload).hexdigest() == EXPECTED_RESIDUAL_BUNDLE_SHA256


def test_unchanged_kernel_independently_accepts_every_theorem_and_all_roots(actual_bundle) -> None:
    bundle, receipt = actual_bundle
    assert type(bundle) is ProofBundle
    assert len(bundle.nodes) == EXPECTED_RESIDUAL_BUNDLE_NODE_COUNT == 475
    assert bundle.root == EXPECTED_RESIDUAL_ROOT_NODE_ID == 474
    assert receipt.node_count == receipt.kernel_calls == 475
    assert receipt.dependency_edges == EXPECTED_RESIDUAL_BUNDLE_EDGE_COUNT == 1_452
    assert receipt.total_body_nodes == EXPECTED_RESIDUAL_BUNDLE_BODY_PROOF_NODES
    assert type(bundle.nodes[-1].target) is And
    assert bundle.nodes[-1].body == _synthetic_conjunction_body()


def test_bundle_rejects_changed_theorem_dependency_and_root(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    plan = residual_closure_plan()
    dependent = next(row for row in plan.rows if row.dependencies)
    changed = replace(bundle.nodes[dependent.node_id], dependencies=())
    nodes = list(bundle.nodes)
    nodes[dependent.node_id] = changed
    with pytest.raises(ResidualClosureError, match="changed frozen theorem"):
        check_residual_proof_bundle(ProofBundle(tuple(nodes), bundle.root), bundle.nodes[-1].target)
    with pytest.raises(ResidualClosureError, match="exact local graph"):
        check_residual_proof_bundle(replace(bundle, root=0), bundle.nodes[-1].target)


def test_bundle_rejects_synthetic_root_and_actual_body_mutations(actual_bundle) -> None:
    bundle, _receipt = actual_bundle
    synthetic = replace(bundle.nodes[-1], body=Hyp(0))
    with pytest.raises(ResidualClosureError, match="synthetic"):
        check_residual_proof_bundle(
            replace(bundle, nodes=bundle.nodes[:-1] + (synthetic,)),
            bundle.nodes[-1].target,
        )
    first = replace(bundle.nodes[0], body=Hyp(0))
    with pytest.raises(ResidualClosureError, match="kernel rejected"):
        check_residual_proof_bundle(
            replace(bundle, nodes=(first,) + bundle.nodes[1:]),
            bundle.nodes[-1].target,
        )


@pytest.mark.parametrize("name", ("cell_list_valid_nil", "prime_power_valuation_exists"))
def test_replay_constructs_exact_empty_context_theorems(name: str, actual_bundle) -> None:
    del actual_bundle
    actual = replay_residual_closed_theorem(name)
    assert actual.spec is v18.ALPHA_EDITION.by_name[name].spec
    assert check((), actual.certificate, actual.formula)


@pytest.mark.parametrize("name", ("bertrand_strict", "missing_residual_theorem", 1))
def test_replay_rejects_names_outside_exact_pending_frontier(name) -> None:
    with pytest.raises(ResidualClosureError, match="exact 84"):
        replay_residual_closed_theorem(name)


def test_artifact_loader_fails_closed_for_missing_source(tmp_path: Path) -> None:
    set_residual_bundle_source(tmp_path / "missing.json")
    try:
        with pytest.raises(ResidualClosureError, match="unavailable"):
            checked_residual_proof_bundle()
    finally:
        set_residual_bundle_source(None)
