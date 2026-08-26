"""Immutable, complete, fail-closed admission of constructive Alpha v20."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions_v19 as v19
from peano_lab.library import editions_v20 as v20
from peano_lab.library.alpha_enrollment_v20 import (
    BERTRAND_CHAIN_ROOT_NAME,
    BERTRAND_MULTIPLICITY_ROOT_NAME,
    CONTINUED_FRACTION_ROOT_NAME,
    FRONTIER_V20_EXPECTED_NAMES_SHA256,
    MATRIX_DOT_PRODUCT_ROOT_NAME,
    POLYNOMIAL_HORNER_ROOT_NAME,
    alpha_v20_enrollment,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY
    / "research/arithmetic-library/artifacts/alpha-v20-next-layer-proof-bundle-v1.json"
)
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v19.json": (
        "f1c3d3fba013ca3a5b62a4103dd00bd5b7e39b1f785ed9023099704ad033004b"
    ),
    "artifacts/peano-library/alpha/metrics-v19.json": (
        "e9990f647d5e75a9a1fa2c817627c66c91f528fa3c3c0617059401c196af656a"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v19.mmd": (
        "a1a967629e0a87684f99da0bcedb0248f91e3c72bc5a4bb5dfc067e1e7dc243d"
    ),
    "artifacts/peano-library/channels-v19.json": (
        "5f221a45ee69b45196e0816652f5d6ee734f2f2f9d802a2527d1ab6dcad50cb7"
    ),
}
ROOT_STATEMENT_SHA256 = {
    POLYNOMIAL_HORNER_ROOT_NAME: (
        "bd1fa1601bd14a7dd6e769eb49bb646326d12f9a26d206c89eea1c7de54ac7d3"
    ),
    MATRIX_DOT_PRODUCT_ROOT_NAME: (
        "8a40343d3cb482060f468b5d8d2f3fe02f76bf740482be0ee67730d0d8c2969d"
    ),
    BERTRAND_MULTIPLICITY_ROOT_NAME: (
        "d0899600b713e85d0cb20997ada171ce02b6a6e8316364ed4ab603389724f5a8"
    ),
    BERTRAND_CHAIN_ROOT_NAME: (
        "02c52d46368ec2320c8d316b41d37ef7c1dbb5de32dbd15247325a17382650d2"
    ),
    CONTINUED_FRACTION_ROOT_NAME: (
        "d3b12766820bb64d9b1437e0ef96a9068c84d6d3176e066fe70f5a4f2d9e087d"
    ),
}


def test_import_seals_inventory_without_loading_actual_proof_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from peano_lab.library import editions_v20 as v; "
                "assert 'peano_lab.library.campaign_next_layer_closure' not in sys.modules; "
                "assert len(v.ALPHA_CHECKED_SPECS) == 1776"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_complete_historical_alpha_v19_and_stable_snapshots_remain_identical() -> None:
    assert len(v19.ALPHA_ENTRIES) == len(v19.ALPHA_CHECKED_SPECS) == 1_737
    assert len(v20.ALPHA_ENTRIES) == len(v20.ALPHA_CHECKED_SPECS) == 1_776
    assert all(
        newer is older
        for newer, older in zip(v20.ALPHA_ENTRIES[:1_737], v19.ALPHA_ENTRIES, strict=True)
    )
    assert v20.STABLE_EDITION is v19.STABLE_EDITION
    assert v20.STABLE_ENTRIES is v19.STABLE_ENTRIES
    assert v20.STABLE_SPECS is v19.STABLE_SPECS
    assert v20.STABLE_RELEASE_ORDER is v19.STABLE_RELEASE_ORDER
    assert len(v20.STABLE_SPECS) == 432
    for filename, expected in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == expected


def test_exactly_39_new_next_layer_rows_are_additive_and_dependency_ordered() -> None:
    enrollment = alpha_v20_enrollment()
    new = v20.ALPHA_ENTRIES[1_737:]
    assert len(new) == len(enrollment.frontier_specs) == 39
    assert tuple(item.spec for item in new) == enrollment.frontier_specs
    assert tuple(item.spec.name for item in new) == v20.FRONTIER_NEW_NAMES
    assert sha256("\n".join(v20.FRONTIER_NEW_NAMES).encode()).hexdigest() == (
        FRONTIER_V20_EXPECTED_NAMES_SHA256
    )
    assert Counter(item.value for item in enrollment.campaign_by_name.values()) == {
        "polynomial_horner": 7,
        "matrix_dot_product": 10,
        "bertrand_prime": 13,
        "continued_fraction": 9,
    }
    available = set(v19.ALPHA_EDITION.by_name)
    for item in new:
        assert item.spec.name not in v19.ALPHA_EDITION.by_name
        assert item.evidence is v20.EvidenceStatus.ALPHA_CLOSED
        assert item.membership is v20.Membership.ALPHA_ONLY
        assert item.checked_use
        assert set(item.spec.dependencies) <= available
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        available.add(item.spec.name)


def test_complete_checked_partition_graph_and_immutable_identities_are_exact() -> None:
    assert Counter(item.evidence.value for item in v20.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 1_344,
    }
    assert (v20.ALPHA_EDITION.edge_count, v20.ALPHA_EDITION.layer_count) == (5_882, 53)
    assert v20.ALPHA_V20_ENROLLMENT_SHA256 == (
        "947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c"
    )
    assert v20.ALPHA_V20_IDENTITY_SHA256 == (
        "ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b"
    )
    assert all(item.checked_use for item in v20.ALPHA_ENTRIES)


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_five_major_roots_have_frozen_exact_constructive_statements(name: str) -> None:
    assert v19.entry(name, edition="alpha") is None
    after = v20.entry(name, edition="alpha")
    assert after is not None and after.checked_use
    assert sha256(after.spec.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256[name]
    assert v20.entry(name, edition="stable") is None


def test_arbitrary_signed_matrices_and_lattices_are_not_falsely_claimed() -> None:
    names = set(v20.FRONTIER_NEW_NAMES)
    assert "beta_dot_product_exists_unique" in names
    assert "signed_matrix_two_determinant_exists" in names
    assert "integer_matrix_arbitrary_product_exists" not in names
    assert "integer_matrix_arbitrary_determinant_exists" not in names
    assert "lattice_basis_reduction_exists" not in names


def test_every_bundle_node_is_independently_checked_with_exact_dependencies() -> None:
    bundle, receipt, positions = v20.checked_next_layer_bundle()
    assert receipt.node_count == len(bundle.nodes) == receipt.kernel_calls == 590
    assert receipt.dependency_edges == 2_045
    assert set(v20.FRONTIER_NEW_NAMES) <= set(positions)
    assert len(positions) == 589
    for name, index in positions.items():
        item = v20.ALPHA_EDITION.by_name[name]
        node = bundle.nodes[index]
        assert node.target == _closed_formula(item.spec.statement)
        assert node.dependencies == tuple(positions[dep] for dep in item.spec.dependencies)


def test_actual_dependency_free_new_theorem_has_an_empty_context_kernel_proof() -> None:
    checked = v20.replay("signed_matrix_two_determinant_exists", edition="alpha")
    assert checked.spec.name == "signed_matrix_two_determinant_exists"
    assert check((), checked.certificate, checked.formula)


def test_stable_and_parent_theorems_still_replay_through_immutable_owners() -> None:
    stable = v20.replay("zero_add")
    assert stable.spec is v19.replay("zero_add").spec
    assert check((), stable.certificate, stable.formula)
    assert v20.edition() is v19.STABLE_EDITION


def test_mutated_proof_bytes_fail_before_they_can_grant_checked_use(tmp_path: Path) -> None:
    target = tmp_path / "forged-v20.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))
    v20.set_next_layer_bundle_source(target)
    try:
        with pytest.raises(v20.EditionV20ReplayError, match="frozen genuine provenance"):
            v20.replay("signed_matrix_two_determinant_exists", edition="alpha")
    finally:
        v20.set_next_layer_bundle_source(None)


@pytest.mark.parametrize("value", (0, True, object(), [], {}))
def test_nonfilesystem_proof_sources_fail_closed(value: object) -> None:
    with pytest.raises(v20.EditionV20ReplayError, match="filesystem path"):
        v20.set_next_layer_bundle_source(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("edition", ("unsafe", "v20", None, 1, object()))
def test_unknown_editions_fail_closed(edition: object) -> None:
    with pytest.raises(v20.EditionV20Error, match="unknown"):
        v20.edition(edition)  # type: ignore[arg-type]


def test_unknown_and_alpha_only_theorems_never_replay_in_stable() -> None:
    with pytest.raises(v20.EditionV20ReplayError, match="unknown"):
        v20.replay("definitely_not_an_admitted_theorem", edition="alpha")
    with pytest.raises(v20.EditionV20ReplayError, match="unknown"):
        v20.replay(BERTRAND_CHAIN_ROOT_NAME, edition="stable")


def test_nonstring_theorem_lookup_is_harmless() -> None:
    assert v20.entry(None, edition="alpha") is None  # type: ignore[arg-type]
    assert v20.entry(123, edition="alpha") is None  # type: ignore[arg-type]
