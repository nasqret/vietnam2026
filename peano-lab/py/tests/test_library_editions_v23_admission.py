"""Immutable, completely checked, fail-closed Alpha-v23 theorem admission."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Exists, Forall
from peano_lab.library import editions_v22 as v22
from peano_lab.library import editions_v23 as v23
from peano_lab.library.alpha_enrollment_v23 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V23_EXPECTED_COUNT,
    FRONTIER_V23_EXPECTED_EDGE_COUNT,
    FRONTIER_V23_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V22_COUNT,
    ROOT_STATEMENT_SHA256,
    alpha_v23_enrollment,
)
from peano_lab.library.campaign_milestone_closure import (
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_BODY_PROOF_NODES,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT,
    EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT,
    MILESTONE_CLOSURE_ARTIFACT_FILENAME,
)
from peano_lab.library.theorems import _closed_formula


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / MILESTONE_CLOSURE_ARTIFACT_FILENAME
)
PARENT_ARTIFACT_SHA256 = {
    "artifacts/peano-library/alpha/catalog-v22.json": (
        "fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22"
    ),
    "artifacts/peano-library/alpha/metrics-v22.json": (
        "07ac17090f4d387fec6e58712f39372daa9956c74887ebb2bc199303e30284c8"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v22.mmd": (
        "c27152c78f90cec10cee7dd708367686e0839c0122a94468d5e133b01e9ce80c"
    ),
    "artifacts/peano-library/channels-v22.json": (
        "a5e218d2ab96ff699b445a4556032ee93e210c32e3573334afee48e76c5489fb"
    ),
}


def test_inventory_import_never_loads_the_actual_proof_provider() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; from peano_lab.library import editions_v23 as v; "
                "assert 'peano_lab.library.campaign_milestone_closure' "
                "not in sys.modules; "
                f"assert len(v.ALPHA_CHECKED_SPECS) == {v23.EXPECTED_ALPHA_V23_COUNT}"
            ),
        ],
        cwd=REPOSITORY / "peano-lab/py",
        check=True,
        capture_output=True,
        text=True,
    )
    assert result.stdout == ""


def test_complete_checked_v22_and_stable_snapshots_remain_exactly_immutable() -> None:
    assert len(v22.ALPHA_ENTRIES) == len(v22.ALPHA_CHECKED_SPECS) == 1_890
    assert all(
        newer is older
        for newer, older in zip(
            v23.ALPHA_ENTRIES[:PARENT_ALPHA_V22_COUNT], v22.ALPHA_ENTRIES, strict=True
        )
    )
    assert v23.STABLE_EDITION is v22.STABLE_EDITION
    assert v23.STABLE_ENTRIES is v22.STABLE_ENTRIES
    assert v23.STABLE_SPECS is v22.STABLE_SPECS
    assert v23.STABLE_RELEASE_ORDER is v22.STABLE_RELEASE_ORDER
    assert len(v23.STABLE_SPECS) == 432
    for filename, expected in PARENT_ARTIFACT_SHA256.items():
        assert sha256((REPOSITORY / filename).read_bytes()).hexdigest() == expected


def test_new_rows_are_additive_and_topologically_dependency_ordered() -> None:
    enrollment = alpha_v23_enrollment()
    new = v23.ALPHA_ENTRIES[PARENT_ALPHA_V22_COUNT:]

    assert len(new) == len(enrollment.frontier_specs) == FRONTIER_V23_EXPECTED_COUNT
    assert FRONTIER_V23_EXPECTED_COUNT > 0
    assert tuple(item.spec for item in new) == enrollment.frontier_specs
    assert tuple(item.spec.name for item in new) == v23.FRONTIER_NEW_NAMES
    assert sha256("\n".join(v23.FRONTIER_NEW_NAMES).encode()).hexdigest() == (
        FRONTIER_V23_EXPECTED_NAMES_SHA256
    )
    assert sum(len(item.spec.dependencies) for item in new) == (
        FRONTIER_V23_EXPECTED_EDGE_COUNT
    )
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    available = set(v22.ALPHA_EDITION.by_name)
    for item in new:
        assert item.spec.name not in v22.ALPHA_EDITION.by_name
        assert item.evidence is v23.EvidenceStatus.ALPHA_CLOSED
        assert item.membership is v23.Membership.ALPHA_ONLY
        assert item.checked_use
        assert set(item.spec.dependencies) <= available
        assert item.source_module == enrollment.source_by_name[item.spec.name]
        available.add(item.spec.name)


def test_complete_checked_partition_graph_and_frozen_identities_are_exact() -> None:
    count = v23.EXPECTED_ALPHA_V23_COUNT
    assert count == PARENT_ALPHA_V22_COUNT + FRONTIER_V23_EXPECTED_COUNT
    assert Counter(item.evidence.value for item in v23.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": count - 432,
    }
    assert v23.ALPHA_EDITION.edge_count == v23.EXPECTED_ALPHA_V23_EDGE_COUNT
    assert v23.ALPHA_EDITION.layer_count == v23.EXPECTED_ALPHA_V23_LAYER_COUNT
    assert v23.ALPHA_V23_ENROLLMENT_SHA256 == v23.EXPECTED_ALPHA_V23_ENROLLMENT_SHA256
    assert v23.ALPHA_V23_IDENTITY_SHA256 == v23.EXPECTED_ALPHA_V23_IDENTITY_SHA256
    assert all(item.checked_use for item in v23.ALPHA_ENTRIES)


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_major_endpoints_have_frozen_exact_constructive_statements(name: str) -> None:
    assert v22.entry(name, edition="alpha") is None
    admitted = v23.entry(name, edition="alpha")

    assert admitted is not None and admitted.checked_use
    assert sha256(admitted.spec.statement.encode()).hexdigest() == ROOT_STATEMENT_SHA256[name]
    assert v23.entry(name, edition="stable") is None


def test_g101_has_actual_terminal_gcd_and_exact_logarithmic_complexity() -> None:
    names = set(v23.FRONTIER_NEW_NAMES)
    assert {
        "euclidean_log_execution_strong",
        "euclidean_gcd_execution_logarithmic_bound",
        "euclidean_gcd_execution_logarithmic_exists",
    } <= names
    bounded = v23.ALPHA_EDITION.by_name[
        "euclidean_gcd_execution_logarithmic_bound"
    ].spec
    assert "gcd-anchored" in bounded.summary
    assert "steps <= 2*l+1" in bounded.summary
    assert "exists gap. gap + k = 2 * l + 1" in bounded.statement
    unconditional = v23.ALPHA_EDITION.by_name[
        "euclidean_gcd_execution_logarithmic_exists"
    ].spec
    assert unconditional.statement.startswith("forall a b. exists l g k.")
    assert "2 * l + 1" in unconditional.statement


def test_g102_has_arbitrary_exponent_digits_execution_and_exact_logarithmic_cost() -> None:
    names = set(v23.FRONTIER_NEW_NAMES)
    assert {
        "binary_exponent_digit_prefix_exists",
        "binary_modular_exponent_coded_execution_power_correct",
        "binary_modular_exponent_coded_execution_exists_unique",
        "binary_modular_execution_bitlength_bound",
        "binary_modular_execution_logarithmic_bound",
    } <= names
    root = v23.ALPHA_EDITION.by_name[
        "binary_modular_execution_logarithmic_bound"
    ].spec
    assert root.statement.startswith("forall n a m.")
    assert "exists l b c r operations." in root.statement
    assert "operations = (2 + (l + l)) +" in root.statement
    assert "gap + operations = 3 * l + 2" in root.statement
    assert "arbitrary natural exponent" in root.summary


def test_g025_has_a_genuine_prime_strict_bound_and_three_mod_four_witness() -> None:
    name = "infinitely_many_primes_three_mod_four"
    assert name in v23.FRONTIER_NEW_NAMES
    assert v22.entry(name, edition="alpha") is None
    row = v23.ALPHA_EDITION.by_name[name].spec
    assert "gap + S B = p" in row.statement
    assert "4 * ff_residue_ptmf_prime + 3" in row.statement

    formula = _closed_formula(row.statement)
    assert isinstance(formula, Forall)
    assert isinstance(formula.body, Exists)
    assert isinstance(formula.body.body, And)
    assert isinstance(formula.body.body.left, And)
    assert isinstance(formula.body.body.right, And)
    assert isinstance(formula.body.body.right.left, Exists)
    assert isinstance(formula.body.body.right.right, Exists)


@pytest.mark.parametrize(
    "name",
    (
        "integer_matrix_arbitrary_determinant_exists",
        "signed_matrix_arbitrary_determinant_exists",
        "integer_matrix_rank_exists",
        "lattice_basis_reduction_exists",
    ),
)
def test_open_general_matrix_lattice_frontier_is_not_falsely_admitted(name: str) -> None:
    assert name not in v23.ALPHA_EDITION.by_name


def test_every_bundle_node_is_independently_checked_with_exact_dependencies() -> None:
    bundle, receipt, positions = v23.checked_milestone_closure_bundle()
    assert receipt.node_count == len(bundle.nodes) == receipt.kernel_calls
    assert receipt.node_count == EXPECTED_MILESTONE_CLOSURE_BUNDLE_NODE_COUNT
    assert receipt.dependency_edges == EXPECTED_MILESTONE_CLOSURE_BUNDLE_EDGE_COUNT
    assert receipt.total_body_nodes == EXPECTED_MILESTONE_CLOSURE_BUNDLE_BODY_PROOF_NODES
    assert set(v23.FRONTIER_NEW_NAMES) <= set(positions)
    for name, index in positions.items():
        item = v23.ALPHA_EDITION.by_name[name]
        node = bundle.nodes[index]
        assert node.target == _closed_formula(item.spec.statement)
        assert node.dependencies == tuple(positions[dep] for dep in item.spec.dependencies)


def test_stable_theorems_still_replay_through_the_immutable_historical_owner() -> None:
    stable = v23.replay("zero_add")
    assert stable.spec is v22.replay("zero_add").spec
    assert check((), stable.certificate, stable.formula)
    assert v23.edition() is v22.STABLE_EDITION


def test_mutated_proof_bytes_fail_before_granting_actual_checked_use(tmp_path: Path) -> None:
    target = tmp_path / "forged-v23.json"
    payload = ARTIFACT.read_bytes()
    target.write_bytes(payload[:-1] + (b" " if payload[-1:] != b" " else b"\n"))
    v23.set_milestone_closure_bundle_source(target)
    try:
        with pytest.raises(v23.EditionV23ReplayError, match="frozen provenance"):
            v23.replay(v23.FRONTIER_NEW_NAMES[0], edition="alpha")
    finally:
        v23.set_milestone_closure_bundle_source(None)


@pytest.mark.parametrize("value", (0, True, object(), [], {}))
def test_nonfilesystem_proof_sources_fail_closed(value: object) -> None:
    with pytest.raises(v23.EditionV23ReplayError, match="filesystem path"):
        v23.set_milestone_closure_bundle_source(value)  # type: ignore[arg-type]


@pytest.mark.parametrize("edition", ("unsafe", "v23", None, 1, object()))
def test_unknown_editions_fail_closed(edition: object) -> None:
    with pytest.raises(v23.EditionV23Error, match="unknown"):
        v23.edition(edition)  # type: ignore[arg-type]


def test_unknown_and_alpha_only_theorems_never_replay_in_stable() -> None:
    with pytest.raises(v23.EditionV23ReplayError, match="unknown"):
        v23.replay("definitely_not_an_admitted_theorem", edition="alpha")
    with pytest.raises(v23.EditionV23ReplayError, match="unknown"):
        v23.replay(v23.FRONTIER_NEW_NAMES[0], edition="stable")


def test_nonstring_theorem_lookup_is_harmless() -> None:
    assert v23.entry(None, edition="alpha") is None  # type: ignore[arg-type]
    assert v23.entry(123, edition="alpha") is None  # type: ignore[arg-type]
