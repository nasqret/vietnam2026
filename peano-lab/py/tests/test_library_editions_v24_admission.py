"""Immutable, completely checked, fail-closed Alpha-v24 theorem admission."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Exists, Forall, Imp
from peano_lab.library import editions_v23 as v23
from peano_lab.library import editions_v24 as v24
from peano_lab.library.alpha_enrollment_v24 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V24_EXPECTED_COUNT,
    FRONTIER_V24_EXPECTED_EDGE_COUNT,
    FRONTIER_V24_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V23_COUNT,
    ROOT_STATEMENT_SHA256,
    alpha_v24_enrollment,
)
from peano_lab.library.campaign_research_layer_closure import (
    EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT,
    EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT,
    RESEARCH_LAYER_ARTIFACT_FILENAME,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / RESEARCH_LAYER_ARTIFACT_FILENAME
)
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v23.json": (
        "818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2"
    ),
    "artifacts/peano-library/alpha/metrics-v23.json": (
        "7660ae6d49522adaae93b1091d98fb2e8d2b2ce4a52f392ad99bda07aa487a5c"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v23.mmd": (
        "4967506a9a4e0cd52ca7103954e76abcce478c9ed70b63285b0abc54aa768cc9"
    ),
    "artifacts/peano-library/channels-v23.json": (
        "b9b53b2ebc158719ac98537b5e10b8b319795ba4eb847d3a01f64cfdd04bfeca"
    ),
}


def test_inventory_import_never_loads_the_actual_proof_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from peano_lab.library import editions_v24 as v; "
                "assert 'peano_lab.library.campaign_research_layer_closure' "
                "not in sys.modules; "
                f"assert len(v.ALPHA_CHECKED_SPECS) == {v24.EXPECTED_ALPHA_V24_COUNT}"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_complete_checked_v23_and_stable_snapshots_remain_exactly_immutable() -> None:
    assert len(v23.ALPHA_ENTRIES) == len(v23.ALPHA_CHECKED_SPECS) == 1_949
    assert all(
        newer is older
        for newer, older in zip(
            v24.ALPHA_ENTRIES[:PARENT_ALPHA_V23_COUNT], v23.ALPHA_ENTRIES, strict=True
        )
    )
    assert v24.STABLE_EDITION is v23.STABLE_EDITION
    assert v24.STABLE_ENTRIES is v23.STABLE_ENTRIES
    assert v24.STABLE_SPECS is v23.STABLE_SPECS
    assert v24.STABLE_RELEASE_ORDER is v23.STABLE_RELEASE_ORDER
    assert len(v24.STABLE_SPECS) == 432
    for filename, expected in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == expected


def test_new_rows_are_additive_and_topologically_dependency_ordered() -> None:
    enrollment = alpha_v24_enrollment()
    new = v24.ALPHA_ENTRIES[PARENT_ALPHA_V23_COUNT:]

    assert len(new) == len(enrollment.frontier_specs) == FRONTIER_V24_EXPECTED_COUNT
    assert FRONTIER_V24_EXPECTED_COUNT > 0
    assert tuple(item.spec for item in new) == enrollment.frontier_specs
    assert tuple(item.spec.name for item in new) == v24.FRONTIER_NEW_NAMES
    assert sha256("\n".join(v24.FRONTIER_NEW_NAMES).encode()).hexdigest() == (
        FRONTIER_V24_EXPECTED_NAMES_SHA256
    )
    assert sum(len(item.spec.dependencies) for item in new) == (
        FRONTIER_V24_EXPECTED_EDGE_COUNT
    )
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    available = set(v23.ALPHA_EDITION.by_name)
    for item in new:
        assert item.spec.name not in v23.ALPHA_EDITION.by_name
        assert item.evidence is v24.EvidenceStatus.ALPHA_CLOSED
        assert item.membership is v24.Membership.ALPHA_ONLY
        assert item.checked_use
        assert set(item.spec.dependencies) <= available
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        available.add(item.spec.name)


def test_complete_checked_partition_graph_and_frozen_identities_are_exact() -> None:
    count = v24.EXPECTED_ALPHA_V24_COUNT
    assert count == PARENT_ALPHA_V23_COUNT + FRONTIER_V24_EXPECTED_COUNT
    assert Counter(item.evidence.value for item in v24.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": count - 432,
    }
    assert v24.ALPHA_EDITION.edge_count == v24.EXPECTED_ALPHA_V24_EDGE_COUNT
    assert v24.ALPHA_EDITION.layer_count == v24.EXPECTED_ALPHA_V24_LAYER_COUNT
    assert v24.ALPHA_V24_ENROLLMENT_SHA256 == v24.EXPECTED_ALPHA_V24_ENROLLMENT_SHA256
    assert v24.ALPHA_V24_IDENTITY_SHA256 == v24.EXPECTED_ALPHA_V24_IDENTITY_SHA256
    assert all(item.checked_use for item in v24.ALPHA_ENTRIES)


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_major_endpoints_have_frozen_exact_constructive_statements(name: str) -> None:
    assert v23.entry(name, edition="alpha") is None
    admitted = v24.entry(name, edition="alpha")

    assert admitted is not None and admitted.checked_use
    assert sha256(admitted.spec.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256[name]
    assert v24.entry(name, edition="stable") is None


def test_arbitrary_matrix_minors_and_actual_signed_four_by_four_determinants_are_proved() -> None:
    names = set(v24.FRONTIER_NEW_NAMES)
    assert {
        "beta_matrix_minor_exists",
        "beta_signed_matrix_minor_exists",
        "signed_matrix_four_cofactor_expansion_exists",
        "signed_matrix_four_full_determinant_exists",
        "signed_matrix_four_full_determinant_functional",
    } <= names
    minor = v24.ALPHA_EDITION.by_name["beta_signed_matrix_minor_exists"].spec
    determinant = v24.ALPHA_EDITION.by_name[
        "signed_matrix_four_full_determinant_exists"
    ].spec
    assert "arbitrary-dimensional" in minor.summary
    assert "row and column" in minor.summary
    assert "four-by-four" in determinant.summary
    assert "32 natural entry components" in determinant.summary
    assert sha256(minor.statement.encode()).hexdigest() == (
        "bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1"
    )
    assert sha256(determinant.statement.encode()).hexdigest() == (
        "7ae77d34a56bc459140fcd9afab5bb70cf4792cdb6ebac833c448381adfff848"
    )


def test_polynomial_frontier_contains_actual_formal_derivative_evaluation() -> None:
    names = set(v24.FRONTIER_NEW_NAMES)
    assert {
        "beta_horner_derivative_trace_exists",
        "beta_horner_derivative_value_exists",
        "beta_horner_derivative_successor_decompose",
        "beta_horner_derivative_exists_unique",
    } <= names
    root = v24.ALPHA_EDITION.by_name["beta_horner_derivative_exists_unique"].spec
    assert "formal-derivative" in root.summary
    assert "exactly one" in root.summary
    assert sha256(root.statement.encode()).hexdigest() == (
        "171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f"
    )


def test_general_list_lcm_and_genuinely_coprime_finite_crt_are_distinguished() -> None:
    names = set(v24.FRONTIER_NEW_NAMES)
    assert {
        "crt_prefix_lcm_exists_unique",
        "crt_pairwise_coprime_prefix_solution_exists",
        "crt_prefix_solution_class_iff_lcm",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
    } <= names
    general_lcm = v24.ALPHA_EDITION.by_name["crt_prefix_lcm_exists_unique"].spec
    assert "noncoprime and zero entries" in general_lcm.summary
    assert sha256(general_lcm.statement.encode()).hexdigest() == (
        "09fa610c42ac069677f4fb90f00c6e0780d2b1de843380599e725a9cf19e1175"
    )
    root = v24.ALPHA_EDITION.by_name[
        "crt_pairwise_coprime_prefix_canonical_exists_unique"
    ].spec
    assert "positive pairwise-coprime" in root.summary
    assert sha256(root.statement.encode()).hexdigest() == (
        "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f"
    )
    formula = _closed_formula(root.statement)
    for _ in range(5):
        assert isinstance(formula, Forall)
        formula = formula.body
    assert isinstance(formula, Imp)
    assert isinstance(formula.right, Imp)
    assert isinstance(formula.right.right, Exists)
    assert isinstance(formula.right.right.body, Exists)
    assert isinstance(formula.right.right.body.body, And)


@pytest.mark.parametrize(
    "name",
    (
        "integer_matrix_arbitrary_determinant_exists",
        "signed_matrix_arbitrary_determinant_exists",
        "integer_matrix_rank_exists",
        "lattice_basis_reduction_exists",
        "simple_root_hensel_lifting",
        "hensel_simple_root_lift_exists",
        "generalized_pairwise_compatible_crt_prefix_canonical_exists_unique",
        "crt_pairwise_compatible_prefix_canonical_exists_unique",
    ),
)
def test_open_arbitrary_matrix_and_noncoprime_crt_goals_are_not_falsely_admitted(name: str) -> None:
    assert name not in v24.ALPHA_EDITION.by_name


def test_every_bundle_node_is_independently_checked_with_exact_dependencies() -> None:
    bundle, receipt, positions = v24.checked_research_layer_bundle()
    assert receipt.node_count == len(bundle.nodes) == receipt.kernel_calls
    assert receipt.node_count == EXPECTED_RESEARCH_LAYER_BUNDLE_NODE_COUNT
    assert receipt.dependency_edges == EXPECTED_RESEARCH_LAYER_BUNDLE_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_RESEARCH_LAYER_BUNDLE_BODY_PROOF_NODES
    assert set(v24.FRONTIER_NEW_NAMES) <= set(positions)
    for name, index in positions.items():
        item = v24.ALPHA_EDITION.by_name[name]
        node = bundle.nodes[index]
        assert node.target == _closed_formula(item.spec.statement)
        assert node.dependencies == tuple(positions[dep] for dep in item.spec.dependencies)


def test_stable_theorems_still_replay_through_the_immutable_historical_owner() -> None:
    stable = v24.replay("zero_add")
    assert stable.spec is v23.replay("zero_add").spec
    assert check((), stable.certificate, stable.formula)
    assert v24.edition() is v23.STABLE_EDITION


def test_mutated_proof_bytes_fail_before_granting_actual_checked_use(tmp_path: Path) -> None:
    target = tmp_path / "forged-v24.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))
    v24.set_research_layer_bundle_source(target)
    try:
        with pytest.raises(v24.EditionV24ReplayError, match="frozen provenance"):
            v24.replay(v24.FRONTIER_NEW_NAMES[0], edition="alpha")
    finally:
        v24.set_research_layer_bundle_source(None)


@pytest.mark.parametrize("value", (0, True, object(), [], {}))
def test_nonfilesystem_proof_sources_fail_closed(value: object) -> None:
    with pytest.raises(v24.EditionV24ReplayError, match="filesystem path"):
        v24.set_research_layer_bundle_source(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("edition", ("unsafe", "v24", None, 1, object()))
def test_unknown_editions_fail_closed(edition: object) -> None:
    with pytest.raises(v24.EditionV24Error, match="unknown"):
        v24.edition(edition)  # type: ignore[arg-type]


def test_unknown_and_alpha_only_theorems_never_replay_in_stable() -> None:
    with pytest.raises(v24.EditionV24ReplayError, match="unknown"):
        v24.replay("definitely_not_an_admitted_theorem", edition="alpha")
    with pytest.raises(v24.EditionV24ReplayError, match="unknown"):
        v24.replay(v24.FRONTIER_NEW_NAMES[0], edition="stable")


def test_nonstring_theorem_lookup_is_harmless() -> None:
    assert v24.entry(None, edition="alpha") is None  # type: ignore[arg-type]
    assert v24.entry(123, edition="alpha") is None  # type: ignore[arg-type]
