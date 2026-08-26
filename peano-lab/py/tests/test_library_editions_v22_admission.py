"""Immutable, completely checked, fail-closed Alpha-v22 theorem admission."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions_v21 as v21
from peano_lab.library import editions_v22 as v22
from peano_lab.library.alpha_enrollment_v22 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V22_EXPECTED_COUNT,
    FRONTIER_V22_EXPECTED_EDGE_COUNT,
    FRONTIER_V22_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V21_COUNT,
    ROOT_STATEMENT_SHA256,
    alpha_v22_enrollment,
)
from peano_lab.library.campaign_transport_layer_closure import (
    EXPECTED_TRANSPORT_LAYER_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_TRANSPORT_LAYER_BUNDLE_EDGE_COUNT,
    EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT,
    TRANSPORT_LAYER_ARTIFACT_FILENAME,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / TRANSPORT_LAYER_ARTIFACT_FILENAME
)
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v21.json": (
        "84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1"
    ),
    "artifacts/peano-library/alpha/metrics-v21.json": (
        "b9eafd8366867eae105c05d1dc7896a591791f34a85ed598c516307cba895dd4"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v21.mmd": (
        "3c62ba04f0ef31c6c4d196cdaafd3118563cc233bfcc48a67dc44cbdd18d2bfb"
    ),
    "artifacts/peano-library/channels-v21.json": (
        "23d3f34df63397af870e6173af93a74b77643225655e073c7aed6fd02e0b03c7"
    ),
}


def test_inventory_import_never_loads_the_actual_proof_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from peano_lab.library import editions_v22 as v; "
                "assert 'peano_lab.library.campaign_transport_layer_closure' "
                "not in sys.modules; "
                f"assert len(v.ALPHA_CHECKED_SPECS) == {v22.EXPECTED_ALPHA_V22_COUNT}"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_complete_checked_v21_and_stable_snapshots_remain_exactly_immutable() -> None:
    assert len(v21.ALPHA_ENTRIES) == len(v21.ALPHA_CHECKED_SPECS) == 1_830
    assert all(
        newer is older
        for newer, older in zip(
            v22.ALPHA_ENTRIES[:PARENT_ALPHA_V21_COUNT], v21.ALPHA_ENTRIES, strict=True
        )
    )
    assert v22.STABLE_EDITION is v21.STABLE_EDITION
    assert v22.STABLE_ENTRIES is v21.STABLE_ENTRIES
    assert v22.STABLE_SPECS is v21.STABLE_SPECS
    assert v22.STABLE_RELEASE_ORDER is v21.STABLE_RELEASE_ORDER
    assert len(v22.STABLE_SPECS) == 432
    for filename, expected in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == expected


def test_new_rows_are_additive_and_topologically_dependency_ordered() -> None:
    enrollment = alpha_v22_enrollment()
    new = v22.ALPHA_ENTRIES[PARENT_ALPHA_V21_COUNT:]

    assert len(new) == len(enrollment.frontier_specs) == FRONTIER_V22_EXPECTED_COUNT
    assert FRONTIER_V22_EXPECTED_COUNT > 0
    assert tuple(item.spec for item in new) == enrollment.frontier_specs
    assert tuple(item.spec.name for item in new) == v22.FRONTIER_NEW_NAMES
    assert sha256("\n".join(v22.FRONTIER_NEW_NAMES).encode()).hexdigest() == (
        FRONTIER_V22_EXPECTED_NAMES_SHA256
    )
    assert sum(len(item.spec.dependencies) for item in new) == (
        FRONTIER_V22_EXPECTED_EDGE_COUNT
    )
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    available = set(v21.ALPHA_EDITION.by_name)
    for item in new:
        assert item.spec.name not in v21.ALPHA_EDITION.by_name
        assert item.evidence is v22.EvidenceStatus.ALPHA_CLOSED
        assert item.membership is v22.Membership.ALPHA_ONLY
        assert item.checked_use
        assert set(item.spec.dependencies) <= available
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        available.add(item.spec.name)


def test_complete_checked_partition_graph_and_frozen_identities_are_exact() -> None:
    count = v22.EXPECTED_ALPHA_V22_COUNT
    assert count == PARENT_ALPHA_V21_COUNT + FRONTIER_V22_EXPECTED_COUNT
    assert Counter(item.evidence.value for item in v22.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": count - 432,
    }
    assert v22.ALPHA_EDITION.edge_count == v22.EXPECTED_ALPHA_V22_EDGE_COUNT
    assert v22.ALPHA_EDITION.layer_count == v22.EXPECTED_ALPHA_V22_LAYER_COUNT
    assert v22.ALPHA_V22_ENROLLMENT_SHA256 == v22.EXPECTED_ALPHA_V22_ENROLLMENT_SHA256
    assert v22.ALPHA_V22_IDENTITY_SHA256 == v22.EXPECTED_ALPHA_V22_IDENTITY_SHA256
    assert all(item.checked_use for item in v22.ALPHA_ENTRIES)


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_major_endpoints_have_frozen_exact_constructive_statements(name: str) -> None:
    assert v21.entry(name, edition="alpha") is None
    admitted = v22.entry(name, edition="alpha")

    assert admitted is not None and admitted.checked_use
    assert sha256(admitted.spec.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256[name]
    assert v22.entry(name, edition="stable") is None


def test_euclidean_terminal_gcd_gap_is_genuinely_closed_without_inventing_log_bounds() -> None:
    names = set(v22.FRONTIER_NEW_NAMES)
    assert "euclidean_anchored_execution_linear_bound" in names
    assert "euclidean_gcd_execution_logarithmic_bound" not in names
    assert "euclidean_gcd_execution_bitlength_bound" not in names


def test_g102_does_not_falsely_claim_an_unproved_complete_logarithmic_bound() -> None:
    assert "binary_modular_exponentiation_execution_bitlength_bound" not in (
        v22.FRONTIER_NEW_NAMES
    )


def test_every_bundle_node_is_independently_checked_with_exact_dependencies() -> None:
    bundle, receipt, positions = v22.checked_transport_layer_bundle()
    assert receipt.node_count == len(bundle.nodes) == receipt.kernel_calls
    assert receipt.node_count == EXPECTED_TRANSPORT_LAYER_BUNDLE_NODE_COUNT
    assert receipt.dependency_edges == EXPECTED_TRANSPORT_LAYER_BUNDLE_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_TRANSPORT_LAYER_BUNDLE_BODY_PROOF_NODES
    assert set(v22.FRONTIER_NEW_NAMES) <= set(positions)
    for name, index in positions.items():
        item = v22.ALPHA_EDITION.by_name[name]
        node = bundle.nodes[index]
        assert node.target == _closed_formula(item.spec.statement)
        assert node.dependencies == tuple(positions[dep] for dep in item.spec.dependencies)


def test_stable_theorems_still_replay_through_the_immutable_historical_owner() -> None:
    stable = v22.replay("zero_add")
    assert stable.spec is v21.replay("zero_add").spec
    assert check((), stable.certificate, stable.formula)
    assert v22.edition() is v21.STABLE_EDITION


def test_mutated_proof_bytes_fail_before_granting_actual_checked_use(tmp_path: Path) -> None:
    target = tmp_path / "forged-v22.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))
    v22.set_transport_layer_bundle_source(target)
    try:
        with pytest.raises(v22.EditionV22ReplayError, match="frozen provenance"):
            v22.replay(v22.FRONTIER_NEW_NAMES[0], edition="alpha")
    finally:
        v22.set_transport_layer_bundle_source(None)


@pytest.mark.parametrize("value", (0, True, object(), [], {}))
def test_nonfilesystem_proof_sources_fail_closed(value: object) -> None:
    with pytest.raises(v22.EditionV22ReplayError, match="filesystem path"):
        v22.set_transport_layer_bundle_source(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("edition", ("unsafe", "v22", None, 1, object()))
def test_unknown_editions_fail_closed(edition: object) -> None:
    with pytest.raises(v22.EditionV22Error, match="unknown"):
        v22.edition(edition)  # type: ignore[arg-type]


def test_unknown_and_alpha_only_theorems_never_replay_in_stable() -> None:
    with pytest.raises(v22.EditionV22ReplayError, match="unknown"):
        v22.replay("definitely_not_an_admitted_theorem", edition="alpha")
    with pytest.raises(v22.EditionV22ReplayError, match="unknown"):
        v22.replay(v22.FRONTIER_NEW_NAMES[0], edition="stable")


def test_nonstring_theorem_lookup_is_harmless() -> None:
    assert v22.entry(None, edition="alpha") is None  # type: ignore[arg-type]
    assert v22.entry(123, edition="alpha") is None  # type: ignore[arg-type]
