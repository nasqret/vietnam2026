"""Immutable, complete, fail-closed admission of constructive Alpha v21."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.library import editions_v20 as v20
from peano_lab.library import editions_v21 as v21
from peano_lab.library.alpha_enrollment_v21 import (
    BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
    EUCLIDEAN_EXECUTION_ROOT_NAME,
    EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME,
    FRONTIER_V21_EXPECTED_EDGE_COUNT,
    FRONTIER_V21_EXPECTED_NAMES_SHA256,
    MATRIX_CODED_PRODUCT_ROOT_NAME,
    SIGNED_DOT_PRODUCT_ROOT_NAME,
    SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
    SIGNED_THREE_DETERMINANT_ROOT_NAME,
    alpha_v21_enrollment,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY
    / "research/arithmetic-library/artifacts/alpha-v21-advanced-layer-proof-bundle-v1.json"
)
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v20.json": (
        "8f86225cc560d7b59ff665e58594ac6249c12dbb5cdfe47ae2708a0e497c86ce"
    ),
    "artifacts/peano-library/alpha/metrics-v20.json": (
        "5e55e2579a924e3886a19ff24f40ae71ec71aa55f0b00624aa86f30d52ddcc1d"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v20.mmd": (
        "86bb9755ba61f24ce46efc196f40a7d15a364a6864a862f755c2a7b5422b88ef"
    ),
    "artifacts/peano-library/channels-v20.json": (
        "1adacfb6332f700ef90be9945ae95bf38c9adc05ad02a2a59d1ae0f07668f257"
    ),
}
ROOT_STATEMENT_SHA256 = {
    MATRIX_CODED_PRODUCT_ROOT_NAME: (
        "c2d3335be60c889559096aa9a36ed8d9bd38c8b33b5f776d73cdec0a60e951c2"
    ),
    SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME: (
        "13291ba49b84a8b1345863e446bca126321e7962eb912bd84b48761f9db24c7f"
    ),
    SIGNED_DOT_PRODUCT_ROOT_NAME: (
        "f84fbb5d723d32ea972a38d562c3e59cbedc78ab485e9f20cda90c0c4f186c04"
    ),
    SIGNED_THREE_DETERMINANT_ROOT_NAME: (
        "edd7918f03a700f96dc345ba77e3dae458485fb323162139c2e93dbc09fae784"
    ),
    EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME: (
        "a7bf1c208237e02edcfdb3b7c819e944be1d0bc8783a06bcb05cfcab5ba7df94"
    ),
    EUCLIDEAN_EXECUTION_ROOT_NAME: (
        "cde09bcea3d247bca7dc5d0b44a0576b1822a0464826f54f5ff3424bdeec2435"
    ),
    BINARY_MODULAR_EXPONENTIATION_ROOT_NAME: (
        "7b9895f8ad3956c33e9fb06ea8040113f17f272be5e97d942ca71aed2a88f136"
    ),
}


def test_inventory_import_never_loads_the_actual_proof_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from peano_lab.library import editions_v21 as v; "
                "assert 'peano_lab.library.campaign_advanced_layer_closure' "
                "not in sys.modules; "
                "assert len(v.ALPHA_CHECKED_SPECS) == 1830"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_complete_checked_v20_and_stable_snapshots_remain_exactly_immutable() -> None:
    assert len(v20.ALPHA_ENTRIES) == len(v20.ALPHA_CHECKED_SPECS) == 1_776
    assert len(v21.ALPHA_ENTRIES) == len(v21.ALPHA_CHECKED_SPECS) == 1_830
    assert all(
        newer is older
        for newer, older in zip(v21.ALPHA_ENTRIES[:1_776], v20.ALPHA_ENTRIES, strict=True)
    )
    assert v21.STABLE_EDITION is v20.STABLE_EDITION
    assert v21.STABLE_ENTRIES is v20.STABLE_ENTRIES
    assert v21.STABLE_SPECS is v20.STABLE_SPECS
    assert v21.STABLE_RELEASE_ORDER is v20.STABLE_RELEASE_ORDER
    assert len(v21.STABLE_SPECS) == 432
    for filename, expected in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == expected


def test_exactly_54_new_rows_are_additive_and_topologically_dependency_ordered() -> None:
    enrollment = alpha_v21_enrollment()
    new = v21.ALPHA_ENTRIES[1_776:]

    assert len(new) == len(enrollment.frontier_specs) == 54
    assert tuple(item.spec for item in new) == enrollment.frontier_specs
    assert tuple(item.spec.name for item in new) == v21.FRONTIER_NEW_NAMES
    assert sha256("\n".join(v21.FRONTIER_NEW_NAMES).encode()).hexdigest() == (
        FRONTIER_V21_EXPECTED_NAMES_SHA256
    )
    assert sum(len(item.spec.dependencies) for item in new) == (
        FRONTIER_V21_EXPECTED_EDGE_COUNT
    ) == 104
    assert Counter(item.value for item in enrollment.campaign_by_name.values()) == {
        "matrix_coded_product": 23,
        "euclidean_complexity": 15,
        "binary_modular_exponentiation": 16,
    }
    available = set(v20.ALPHA_EDITION.by_name)
    for item in new:
        assert item.spec.name not in v20.ALPHA_EDITION.by_name
        assert item.evidence is v21.EvidenceStatus.ALPHA_CLOSED
        assert item.membership is v21.Membership.ALPHA_ONLY
        assert item.checked_use
        assert set(item.spec.dependencies) <= available
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        available.add(item.spec.name)


def test_complete_checked_partition_graph_and_frozen_identities_are_exact() -> None:
    assert Counter(item.evidence.value for item in v21.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 1_398,
    }
    assert (v21.ALPHA_EDITION.edge_count, v21.ALPHA_EDITION.layer_count) == (5_986, 53)
    assert v21.ALPHA_V21_ENROLLMENT_SHA256 == (
        "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98"
    )
    assert v21.ALPHA_V21_IDENTITY_SHA256 == (
        "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6"
    )
    assert all(item.checked_use for item in v21.ALPHA_ENTRIES)


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_seven_major_endpoints_have_frozen_exact_constructive_statements(name: str) -> None:
    assert v20.entry(name, edition="alpha") is None
    admitted = v21.entry(name, edition="alpha")

    assert admitted is not None and admitted.checked_use
    assert sha256(admitted.spec.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256[name]
    assert v21.entry(name, edition="stable") is None


def test_t13_has_arbitrary_signed_products_but_does_not_falsely_claim_full_closure() -> None:
    names = set(v21.FRONTIER_NEW_NAMES)

    assert {
        MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_DOT_PRODUCT_ROOT_NAME,
        SIGNED_THREE_DETERMINANT_ROOT_NAME,
    } <= names
    assert "integer_matrix_arbitrary_determinant_exists" not in names
    assert "signed_matrix_arbitrary_determinant_exists" not in names
    assert "integer_matrix_rank_exists" not in names
    assert "lattice_basis_reduction_exists" not in names


def test_g101_has_real_execution_and_halving_but_no_unproved_logarithmic_bound() -> None:
    names = set(v21.FRONTIER_NEW_NAMES)
    admitted = v21.entry(EUCLIDEAN_EXECUTION_ROOT_NAME, edition="alpha")

    assert EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME in names
    assert EUCLIDEAN_EXECUTION_ROOT_NAME in names
    assert admitted is not None
    assert "linear bound" in admitted.spec.summary
    assert "BitLen bound remains open" in admitted.spec.summary
    assert "euclidean_gcd_execution_logarithmic_bound" not in names
    assert "euclidean_gcd_execution_bitlength_bound" not in names


def test_g102_has_checked_binary_steps_but_no_unproved_bitlength_trace_bound() -> None:
    names = set(v21.FRONTIER_NEW_NAMES)

    assert {
        "binary_exponent_split_exists",
        "binary_modular_step_exists",
        "binary_modular_step_functional",
        BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
    } <= names
    assert "binary_modular_exponentiation_trace_exists" not in names
    assert "binary_modular_exponentiation_execution_bitlength_bound" not in names


def test_every_bundle_node_is_independently_checked_with_exact_dependencies() -> None:
    bundle, receipt, positions = v21.checked_advanced_layer_bundle()

    assert receipt.node_count == len(bundle.nodes) == receipt.kernel_calls == 209
    assert receipt.dependency_edges == 491
    assert receipt.total_body_nodes == 10_304
    assert set(v21.FRONTIER_NEW_NAMES) <= set(positions)
    assert len(positions) == 208
    for name, index in positions.items():
        item = v21.ALPHA_EDITION.by_name[name]
        node = bundle.nodes[index]
        assert node.target == _closed_formula(item.spec.statement)
        assert node.dependencies == tuple(positions[dep] for dep in item.spec.dependencies)


def test_actual_dependency_free_new_theorem_has_an_empty_context_kernel_proof() -> None:
    checked = v21.replay("signed_pair_product_exists", edition="alpha")

    assert checked.spec.name == "signed_pair_product_exists"
    assert check((), checked.certificate, checked.formula)


def test_stable_theorems_still_replay_through_the_immutable_historical_owner() -> None:
    stable = v21.replay("zero_add")

    assert stable.spec is v20.replay("zero_add").spec
    assert check((), stable.certificate, stable.formula)
    assert v21.edition() is v20.STABLE_EDITION


def test_mutated_proof_bytes_fail_before_granting_actual_checked_use(tmp_path: Path) -> None:
    target = tmp_path / "forged-v21.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))
    v21.set_advanced_layer_bundle_source(target)
    try:
        with pytest.raises(v21.EditionV21ReplayError, match="frozen genuine provenance"):
            v21.replay("signed_pair_product_exists", edition="alpha")
    finally:
        v21.set_advanced_layer_bundle_source(None)


@pytest.mark.parametrize("value", (0, True, object(), [], {}))
def test_nonfilesystem_proof_sources_fail_closed(value: object) -> None:
    with pytest.raises(v21.EditionV21ReplayError, match="filesystem path"):
        v21.set_advanced_layer_bundle_source(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("edition", ("unsafe", "v21", None, 1, object()))
def test_unknown_editions_fail_closed(edition: object) -> None:
    with pytest.raises(v21.EditionV21Error, match="unknown"):
        v21.edition(edition)  # type: ignore[arg-type]


def test_unknown_and_alpha_only_theorems_never_replay_in_stable() -> None:
    with pytest.raises(v21.EditionV21ReplayError, match="unknown"):
        v21.replay("definitely_not_an_admitted_theorem", edition="alpha")
    with pytest.raises(v21.EditionV21ReplayError, match="unknown"):
        v21.replay(BINARY_MODULAR_EXPONENTIATION_ROOT_NAME, edition="stable")


def test_nonstring_theorem_lookup_is_harmless() -> None:
    assert v21.entry(None, edition="alpha") is None  # type: ignore[arg-type]
    assert v21.entry(123, edition="alpha") is None  # type: ignore[arg-type]
