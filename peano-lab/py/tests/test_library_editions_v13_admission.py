"""Minimal Alpha-v13 enrollment, exact evidence limits, and artifact audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v12 as v12
from peano_lab.library import alpha_enrollment_v13 as enrollment_module
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)


REPOSITORY = Path(__file__).resolve().parents[3]
ROOT_HASHES = {
    "four_square_lagrange": (
        "fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5"
    ),
    "lucas_theorem": (
        "396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564"
    ),
}
SORTED_CLOSURE_HASHES = {
    "four_square_lagrange": (
        "75fc0d5fe8bcc38bc98c04886889ccd6ade320cb7236bf72039593c2d03f6569"
    ),
    "lucas_theorem": (
        "d842e9724e120f51a1bdbf80d771170b5a44fff93b1977e282bad6d314b0b9d4"
    ),
    "union": (
        "f2be125fecc9dd1cb890edab33ab174c40bc3cc51c45f011c488424a492ecfda"
    ),
}
EXPECTED_SOURCE_COUNTS = {
    "fermat_two_squares_classification_candidate": 8,
    "fermat_two_squares_collision_norm_candidate": 3,
    "fermat_two_squares_pigeonhole_candidate": 2,
    "finite_prefix_collision_decision_candidate": 5,
    "four_square_bounded_seed_candidate": 6,
    "four_square_branch_descent_candidate": 5,
    "four_square_conjugate_identity_candidate": 9,
    "four_square_cross_pigeonhole_candidate": 4,
    "four_square_descent_candidate": 26,
    "four_square_euler_candidate": 25,
    "four_square_identity_candidate": 15,
    "four_square_lagrange_bridge_candidate": 3,
    "four_square_lagrange_candidate": 3,
    "four_square_lagrange_final_candidate": 3,
    "four_square_parity_selection_candidate": 12,
    "four_square_residue_intersection_candidate": 17,
    "four_square_signed_block_negative_candidate": 2,
    "four_square_signed_cases_candidate": 17,
    "four_square_signed_orientation_candidate": 3,
    "four_square_signed_quaternion_candidate": 28,
    "lucas_block_digit_candidate": 5,
    "lucas_convolution_candidate": 12,
    "lucas_digit_candidate": 1,
    "lucas_low_digit_candidate": 5,
    "lucas_multidigit_candidate": 21,
}
PARENT_ARTIFACT_HASHES = {
    "artifacts/peano-library/alpha/catalog-v12.json": (
        "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109"
    ),
    "artifacts/peano-library/alpha/metrics-v12.json": (
        "64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v12.mmd": (
        "583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8"
    ),
    "artifacts/peano-library/channels-v12.json": (
        "0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982"
    ),
}


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


@lru_cache(maxsize=1)
def _v13():
    return import_module("peano_lab.library.editions_v13")


@lru_cache(maxsize=1)
def _enrollment():
    return enrollment_module.alpha_v13_enrollment()


@lru_cache(maxsize=1)
def _parent_by_name():
    return {entry.spec.name: entry for entry in v12.ALPHA_ENTRIES}


@lru_cache(maxsize=1)
def _frontier_by_name():
    return {spec.name: spec for spec in _enrollment().frontier_specs}


def _closure(root: str) -> tuple[set[str], set[str]]:
    parent = _parent_by_name()
    frontier = _frontier_by_name()
    new_names: set[str] = set()
    parent_names: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in parent:
            parent_names.add(name)
            return
        if name in new_names:
            return
        assert name not in active, f"cyclic Alpha-v13 dependency {name!r}"
        assert name in frontier, f"missing Alpha-v13 dependency {name!r}"
        active.add(name)
        for dependency in frontier[name].dependencies:
            visit(dependency)
        active.remove(name)
        new_names.add(name)

    visit(root)
    return new_names, parent_names


def _sorted_names_hash(names: set[str]) -> str:
    return sha256("\n".join(sorted(names)).encode("utf-8")).hexdigest()


def test_v13_parent_and_stable_entries_are_immutable() -> None:
    v13 = _v13()
    enrollment = _enrollment()
    assert enrollment_module.PARENT_ALPHA_V12_COUNT == len(v12.ALPHA_ENTRIES) == 1_303
    assert enrollment_module.PARENT_ALPHA_V12_ENROLLMENT_SHA256 == (
        v12.ALPHA_V12_ENROLLMENT_SHA256
    )
    assert enrollment_module.PARENT_ALPHA_V12_IDENTITY_SHA256 == (
        v12.ALPHA_V12_IDENTITY_SHA256
    )
    assert enrollment.parent_entries == v12.ALPHA_ENTRIES
    assert all(
        old is new
        for old, new in zip(
            v12.ALPHA_ENTRIES,
            v13.ALPHA_ENTRIES[: len(v12.ALPHA_ENTRIES)],
            strict=True,
        )
    )
    assert v13.STABLE_SPECS == v12.STABLE_SPECS
    assert len(v13.STABLE_SPECS) == 432
    assert v13.STABLE_EDITION.identity_sha256 == v12.STABLE_EDITION.identity_sha256
    assert v13.STABLE_EDITION.enrollment_identity_sha256 == (
        v12.STABLE_EDITION.enrollment_identity_sha256
    )


def test_v13_exact_dependency_minimal_append_is_pinned() -> None:
    enrollment = _enrollment()
    rows = enrollment.frontier_specs
    ordered_names = tuple(spec.name for spec in rows)
    assert len(rows) == enrollment_module.FRONTIER_V13_EXPECTED_COUNT == 240
    assert ordered_names == enrollment_module.FRONTIER_V13_EXPECTED_NAMES
    assert sha256(_compact(ordered_names).encode("utf-8")).hexdigest() == (
        "333c10386d23959fa397e763e236daeadaae0d438a00489b0b089aeb8a4b0148"
    )
    assert len(enrollment.four_square_specs) == 196
    assert len(enrollment.lucas_specs) == 44
    assert rows[195].name == "four_square_lagrange"
    assert rows[-1].name == "lucas_theorem"

    four_square, four_square_parent = _closure("four_square_lagrange")
    lucas, lucas_parent = _closure("lucas_theorem")
    assert len(four_square) == 196
    assert len(lucas) == 44
    assert not (four_square & lucas)
    assert four_square | lucas == set(ordered_names)
    assert len(four_square_parent) == 89
    assert len(lucas_parent) == 49
    assert len(four_square_parent | lucas_parent) == 109
    assert _sorted_names_hash(four_square) == SORTED_CLOSURE_HASHES[
        "four_square_lagrange"
    ]
    assert _sorted_names_hash(lucas) == SORTED_CLOSURE_HASHES["lucas_theorem"]
    assert _sorted_names_hash(four_square | lucas) == SORTED_CLOSURE_HASHES["union"]

    available = set(_parent_by_name())
    for row in rows:
        assert set(row.dependencies) <= available
        available.add(row.name)
    v13 = _v13()
    assert len(v13.ALPHA_ENTRIES) == 1_543
    assert v13.ALPHA_EDITION.edge_count == 5_189
    assert v13.ALPHA_EDITION.layer_count == 45
    assert v13.ALPHA_V13_ENROLLMENT_SHA256 == (
        "6b223edfe6a2e02dc09576671f4fc5f5a41aaf4156f829164222dd3e494da22f"
    )
    assert v13.ALPHA_V13_IDENTITY_SHA256 == (
        "a010e0ee5dece0d3325e8ec084c1f8769ef8e9ca47e2de891d344e54c1b439d1"
    )


def test_v13_exact_source_inventory_and_campaigns_are_pinned() -> None:
    enrollment = _enrollment()
    rows = enrollment.frontier_specs
    counts = Counter(
        Path(enrollment.source_by_name[row.name]).stem for row in rows
    )
    assert counts == EXPECTED_SOURCE_COUNTS
    assert len(enrollment_module.FRONTIER_V13_BODY_ENROLLMENT_MANIFEST) == 25
    assert {
        source.module
        for source in enrollment_module.FRONTIER_V13_BODY_ENROLLMENT_MANIFEST
    } == set(EXPECTED_SOURCE_COUNTS)
    assert {
        enrollment.campaign_by_name[row.name].value
        for row in enrollment.four_square_specs
    } == {"four_square"}
    assert {
        enrollment.campaign_by_name[row.name].value
        for row in enrollment.lucas_specs
    } == {"lucas"}

    inventory = [
        {
            "name": row.name,
            "source": Path(enrollment.source_by_name[row.name]).stem,
            "statement": sha256(row.statement.encode("utf-8")).hexdigest(),
            "dependencies": list(row.dependencies),
        }
        for row in sorted(rows, key=lambda item: item.name)
    ]
    assert sha256(_compact(inventory).encode("utf-8")).hexdigest() == (
        "e15f2d053a9d721988c13abc4543e07cdfbe71a6ceb8805d52e0db6503856df2"
    )


@pytest.mark.parametrize(
    "source",
    enrollment_module.FRONTIER_V13_BODY_ENROLLMENT_MANIFEST,
    ids=lambda source: source.module,
)
def test_v13_every_factory_has_exact_reviewed_source_test_and_rfc(source) -> None:
    module = import_module(f"peano_lab.library.{source.module}")
    factory = getattr(module, source.factory)
    available = {row.name: row for row in factory(type(_enrollment().frontier_specs[0]))}
    enrollment = _enrollment()
    assert len(source.names) == EXPECTED_SOURCE_COUNTS[source.module]
    assert set(source.names) <= set(available)
    assert (REPOSITORY / source.test_path).is_file()
    assert (REPOSITORY / source.rfc_path).is_file()
    for name in source.names:
        assert available[name] == _frontier_by_name()[name]
        assert Path(enrollment.source_by_name[name]).stem == source.module
        assert enrollment.test_by_name[name] == source.test_path
        assert enrollment.rfc_by_name[name] == source.rfc_path
        assert enrollment.campaign_by_name[name] is source.campaign


def test_v13_preserves_checked_use_and_does_not_claim_closed_proofs() -> None:
    v13 = _v13()
    assert len(v13.ALPHA_CHECKED_SPECS) == len(v12.ALPHA_CHECKED_SPECS) == 570
    assert v13.ALPHA_CHECKED_SPECS == v12.ALPHA_CHECKED_SPECS
    assert Counter(entry.evidence.value for entry in v13.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 138,
        "body_checked": 972,
        "pending_layered_closure": 1,
    }
    for entry in v13.ALPHA_ENTRIES[1_303:]:
        assert entry.membership is v13.Membership.ALPHA_ONLY
        assert entry.evidence is v13.EvidenceStatus.BODY_CHECKED
        assert entry.enrollment_origin is v13.EnrollmentOrigin.HA
        assert not entry.checked_use


def test_v13_existing_unchecked_ancestors_are_not_silently_promoted() -> None:
    parent = _parent_by_name()
    _four_square, first = _closure("four_square_lagrange")
    _lucas, second = _closure("lucas_theorem")
    direct = first | second
    assert Counter(parent[name].evidence.value for name in direct) == {
        "stable_closed": 77,
        "alpha_closed": 5,
        "body_checked": 27,
    }

    ancestors: set[str] = set()

    def visit(name: str) -> None:
        if name in ancestors:
            return
        ancestors.add(name)
        for dependency in parent[name].spec.dependencies:
            visit(dependency)

    for name in direct:
        visit(name)
    assert len(ancestors) == 241
    assert Counter(parent[name].evidence.value for name in ancestors) == {
        "stable_closed": 183,
        "alpha_closed": 5,
        "body_checked": 53,
    }


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v13_flagships_are_enrolled_but_never_checked_use(name: str) -> None:
    v13 = _v13()
    item = v13.entry(name, edition="alpha")
    assert item is not None
    assert sha256(item.spec.statement.encode("utf-8")).hexdigest() == ROOT_HASHES[name]
    assert item.evidence is v13.EvidenceStatus.BODY_CHECKED
    assert not item.checked_use
    assert v13.entry(name, edition="stable") is None
    assert v12.entry(name, edition="alpha") is None
    with pytest.raises(v13.EditionV13ReplayError, match="body_checked"):
        v13.replay(name, edition="alpha")


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v13_flagship_dependency_curried_bodies_replay_independently(
    name: str,
) -> None:
    row = _frontier_by_name()[name]
    core = {spec.name: spec for spec in _v13().ALPHA_SPECS}
    receipt, = replay_candidate_bodies((row,), core=core)
    assert receipt.name == name
    assert receipt.proof_nodes > 0
    assert receipt.dependency_count == len(row.dependencies)

    corrupted = replace(row, script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


@pytest.mark.parametrize("path, expected", tuple(PARENT_ARTIFACT_HASHES.items()))
def test_v13_preserves_every_sealed_v12_artifact_byte(
    path: str,
    expected: str,
) -> None:
    assert sha256((REPOSITORY / path).read_bytes()).hexdigest() == expected


def test_v13_new_artifacts_have_real_body_receipts_and_no_false_closure() -> None:
    catalog_path = REPOSITORY / "artifacts/peano-library/alpha/catalog-v13.json"
    metrics_path = REPOSITORY / "artifacts/peano-library/alpha/metrics-v13.json"
    graph_path = REPOSITORY / "artifacts/peano-library/alpha/dependency-graph-v13.mmd"
    channels_path = REPOSITORY / "artifacts/peano-library/channels-v13.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    channels = json.loads(channels_path.read_text(encoding="utf-8"))

    assert catalog["schema"] == "peano-library-alpha-snapshot-v13"
    assert metrics["schema"] == "peano-library-alpha-metrics-v13"
    assert channels["schema"] == "peano-library-channels-v13"
    assert catalog["theorem_count"] == metrics["theorem_count"] == 1_543
    assert catalog["stable_count"] == 432
    assert catalog["checked_use_count"] == metrics["checked_use_count"] == 570
    assert len(catalog["theorems"]) == 1_543
    assert metrics["catalog_sha256"] == sha256(catalog_path.read_bytes()).hexdigest()
    assert metrics["dependency_graph_sha256"] == sha256(graph_path.read_bytes()).hexdigest()
    assert channels["default_channel"] == "stable"

    specs = _frontier_by_name()
    for row in catalog["theorems"][1_303:]:
        spec = specs[row["name"]]
        assert row["evidence_status"] == "body_checked"
        assert row["body_checked"] is True
        assert row["checked_use"] is False
        assert row["empty_context_closure"] is None
        assert row["enrollment_origin"] == "ha"
        assert row["statement_sha256"] == sha256(
            spec.statement.encode("utf-8")
        ).hexdigest()
        assert row["dependencies"] == list(spec.dependencies)
        source = row["source"]
        assert source["path"] == _enrollment().source_by_name[spec.name]
        assert source["sha256"] == sha256(
            (REPOSITORY / source["path"]).read_bytes()
        ).hexdigest()
        receipt = row["body_receipt"]
        assert receipt["name"] == spec.name
        assert receipt["dependency_count"] == len(spec.dependencies)
        assert receipt["command_count"] == len(spec.script)
        assert receipt["proof_nodes"] > 0
        assert receipt["proof_objects"] > 0
        assert receipt["status"] == "kernel_checked_dependency_curried_body"

    core = {spec.name: spec for spec in _v13().ALPHA_SPECS}
    by_name = {row["name"]: row for row in catalog["theorems"]}
    for name in ROOT_HASHES:
        checked, = replay_candidate_bodies((specs[name],), core=core)
        recorded = by_name[name]["body_receipt"]
        for key, value in asdict(checked).items():
            assert recorded[key] == value


def test_v13_rfc_records_exact_evidence_and_nonpromotion_boundary() -> None:
    path = (
        REPOSITORY
        / "research/arithmetic-library/alpha-v13-frontier-admission-rfc-v1.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "196" in text and "44" in text and "240" in text
    assert "1,543" in text and "570" in text
    assert "53" in text and "body_checked" in text
    assert "empty-context" in text
    assert "four_square_lagrange" in text and "lucas_theorem" in text
    assert all(receipt in text for receipt in ROOT_HASHES.values())
