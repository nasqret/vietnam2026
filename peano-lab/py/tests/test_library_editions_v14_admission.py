"""Minimal Alpha-v14 Kummer admission, evidence boundary, and artifact audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path

import pytest

from peano_lab.library import alpha_enrollment_v14 as enrollment_module
from peano_lab.library import editions_v13 as v13
from peano_lab.library import editions_v14 as v14
from peano_lab.library.candidate_validation import (
    CandidateBodyError,
    replay_candidate_bodies,
)


REPOSITORY = Path(__file__).resolve().parents[3]
ROOT_HASHES = {
    "kummer_binomial_carry_bit_count": (
        "f9f7312eacb89563dff059b63d310a3148b0b7df7f9e0425bbf4fdbd868e3c4f"
    ),
    "kummer_carry_free_iff_not_divides": (
        "ed30b756bd9703193020ae395a87f1f32a12859d2b9df8fbb79708e9bed2dc00"
    ),
}
EXPECTED_FACTORY_COUNTS = {
    "make_kummer_valuation_candidate_theorems": 4,
    "make_kummer_carry_candidate_theorems": 7,
    "make_kummer_carry_corollary_candidate_theorems": 2,
}
PARENT_ARTIFACT_HASHES = {
    "artifacts/peano-library/alpha/catalog-v13.json": (
        "cad57a21657e2df09f01174069efcfed194d87b68c0b4042b234df5759583e5a"
    ),
    "artifacts/peano-library/alpha/metrics-v13.json": (
        "b3ad8140487486cbe51e8ef6ae0ef9586636cb9576305de47ef77ad864c93bc9"
    ),
    "artifacts/peano-library/alpha/dependency-graph-v13.mmd": (
        "f6664c7f415fff8444dafab331b184b04426e2c395b3828c7d91929dfe74805a"
    ),
    "artifacts/peano-library/channels-v13.json": (
        "db8c195d98fb02ca0b1561d483cb8f5472d550d7e662cfe4b733ffb1b9ae8634"
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
def _enrollment():
    return enrollment_module.alpha_v14_enrollment()


@lru_cache(maxsize=1)
def _parent_by_name():
    return {entry.spec.name: entry for entry in v13.ALPHA_ENTRIES}


@lru_cache(maxsize=1)
def _frontier_by_name():
    return {spec.name: spec for spec in _enrollment().frontier_specs}


def _closure(root: str) -> tuple[set[str], set[str]]:
    parent = _parent_by_name()
    frontier = _frontier_by_name()
    names: set[str] = set()
    boundary: set[str] = set()
    active: set[str] = set()

    def visit(name: str) -> None:
        if name in parent:
            boundary.add(name)
            return
        if name in names:
            return
        assert name not in active, f"cyclic Alpha-v14 dependency {name!r}"
        assert name in frontier, f"missing Alpha-v14 dependency {name!r}"
        active.add(name)
        for dependency in frontier[name].dependencies:
            visit(dependency)
        active.remove(name)
        names.add(name)

    visit(root)
    return names, boundary


def test_v14_parent_and_stable_entries_are_object_identical() -> None:
    enrollment = _enrollment()
    assert enrollment_module.PARENT_ALPHA_V13_COUNT == len(v13.ALPHA_ENTRIES) == 1_543
    assert enrollment_module.PARENT_ALPHA_V13_ENROLLMENT_SHA256 == (
        v13.ALPHA_V13_ENROLLMENT_SHA256
    )
    assert enrollment_module.PARENT_ALPHA_V13_IDENTITY_SHA256 == (
        v13.ALPHA_V13_IDENTITY_SHA256
    )
    assert enrollment.parent_entries == v13.ALPHA_ENTRIES
    assert all(
        old is new
        for old, new in zip(
            v13.ALPHA_ENTRIES,
            v14.ALPHA_ENTRIES[: len(v13.ALPHA_ENTRIES)],
            strict=True,
        )
    )
    assert v14.STABLE_EDITION is v13.STABLE_EDITION
    assert v14.STABLE_ENTRIES is v13.STABLE_ENTRIES
    assert v14.STABLE_SPECS is v13.STABLE_SPECS
    assert len(v14.STABLE_SPECS) == 432


def test_v14_exact_minimal_append_and_runtime_seals_are_pinned() -> None:
    enrollment = _enrollment()
    rows = enrollment.frontier_specs
    names = tuple(spec.name for spec in rows)
    assert len(rows) == enrollment_module.FRONTIER_V14_EXPECTED_COUNT == 13
    assert names == enrollment_module.FRONTIER_V14_EXPECTED_NAMES
    assert sha256(_compact(names).encode("utf-8")).hexdigest() == (
        "2ff93cb296e4d4a077a8e8722bde54be2f0a9e4a72caedac5fcaa58508c60d6c"
    )
    assert len(enrollment.theorem_specs) == 11
    assert len(enrollment.corollary_specs) == 2
    assert rows[10].name == "kummer_binomial_carry_bit_count"
    assert rows[-1].name == "kummer_carry_free_iff_not_divides"

    theorem, theorem_parent = _closure("kummer_binomial_carry_bit_count")
    corollary, corollary_parent = _closure("kummer_carry_free_iff_not_divides")
    assert len(theorem) == 11
    assert len(corollary) == 13
    assert theorem < corollary
    assert corollary == set(names)
    assert len(theorem_parent) == 37
    assert len(corollary_parent) == 41
    assert theorem_parent <= corollary_parent

    available = set(_parent_by_name())
    for row in rows:
        assert set(row.dependencies) <= available
        available.add(row.name)
    assert len(v14.ALPHA_ENTRIES) == 1_556
    assert v14.ALPHA_EDITION.edge_count == 5_251
    assert v14.ALPHA_EDITION.layer_count == 45
    assert v14.ALPHA_V14_ENROLLMENT_SHA256 == (
        "d7758c5cfcce4fbe2b48b6b213b134acf9126b84a58a0016c523055be952024e"
    )
    assert v14.ALPHA_V14_IDENTITY_SHA256 == (
        "06274ac80612403f6851266fa00f8b543d904072434d5717ca95ae7d40588c16"
    )


def test_v14_exact_factory_inventory_and_campaign_are_pinned() -> None:
    enrollment = _enrollment()
    assert len(enrollment_module.FRONTIER_V14_BODY_ENROLLMENT_MANIFEST) == 3
    assert {
        source.factory: len(source.names)
        for source in enrollment_module.FRONTIER_V14_BODY_ENROLLMENT_MANIFEST
    } == EXPECTED_FACTORY_COUNTS
    assert Counter(
        Path(enrollment.source_by_name[row.name]).stem
        for row in enrollment.frontier_specs
    ) == {"kummer_valuation_candidate": 4, "kummer_carry_candidate": 9}
    assert {
        enrollment.campaign_by_name[row.name].value
        for row in enrollment.frontier_specs
    } == {"kummer"}

    inventory = [
        {
            "name": row.name,
            "source": enrollment.source_by_name[row.name],
            "factory": enrollment.factory_by_name[row.name],
            "statement": sha256(row.statement.encode("utf-8")).hexdigest(),
            "dependencies": list(row.dependencies),
        }
        for row in sorted(enrollment.frontier_specs, key=lambda item: item.name)
    ]
    assert sha256(_compact(inventory).encode("utf-8")).hexdigest() == (
        "01997233b915efeb19e85534ccede1e49e92d3c78a34a2c9a2cba6c9902ccef7"
    )


@pytest.mark.parametrize(
    "source",
    enrollment_module.FRONTIER_V14_BODY_ENROLLMENT_MANIFEST,
    ids=lambda source: source.factory,
)
def test_v14_every_factory_has_exact_reviewed_source_test_and_rfc(source) -> None:
    module = import_module(f"peano_lab.library.{source.module}")
    factory = getattr(module, source.factory)
    available = {
        row.name: row for row in factory(type(_enrollment().frontier_specs[0]))
    }
    enrollment = _enrollment()
    assert len(source.names) == EXPECTED_FACTORY_COUNTS[source.factory]
    assert set(source.names) <= set(available)
    assert (REPOSITORY / source.test_path).is_file()
    assert (REPOSITORY / source.rfc_path).is_file()
    for name in source.names:
        assert available[name] == _frontier_by_name()[name]
        assert Path(enrollment.source_by_name[name]).stem == source.module
        assert enrollment.factory_by_name[name] == source.factory
        assert enrollment.test_by_name[name] == source.test_path
        assert enrollment.rfc_by_name[name] == source.rfc_path
        assert enrollment.campaign_by_name[name] is source.campaign


def test_v14_preserves_checked_use_and_never_claims_closed_proofs() -> None:
    assert v14.ALPHA_CHECKED_SPECS == v13.ALPHA_CHECKED_SPECS
    assert len(v14.ALPHA_CHECKED_SPECS) == 570
    assert Counter(entry.evidence.value for entry in v14.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 138,
        "body_checked": 985,
        "pending_layered_closure": 1,
    }
    for entry in v14.ALPHA_ENTRIES[1_543:]:
        assert entry.membership is v14.Membership.ALPHA_ONLY
        assert entry.evidence is v14.EvidenceStatus.BODY_CHECKED
        assert entry.enrollment_origin is v14.EnrollmentOrigin.HA
        assert not entry.checked_use


def test_v14_unchecked_parent_ancestors_remain_unpromoted() -> None:
    parent = _parent_by_name()
    _new, direct = _closure("kummer_carry_free_iff_not_divides")
    assert len(direct) == 41
    assert Counter(parent[name].evidence.value for name in direct) == {
        "stable_closed": 26,
        "alpha_closed": 1,
        "body_checked": 14,
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
    assert len(ancestors) == 267
    assert Counter(parent[name].evidence.value for name in ancestors) == {
        "stable_closed": 171,
        "alpha_closed": 1,
        "body_checked": 95,
    }


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v14_flagships_are_enrolled_but_never_checked_use(name: str) -> None:
    item = v14.entry(name, edition="alpha")
    assert item is not None
    assert sha256(item.spec.statement.encode("utf-8")).hexdigest() == ROOT_HASHES[name]
    assert item.evidence is v14.EvidenceStatus.BODY_CHECKED
    assert not item.checked_use
    assert v14.entry(name, edition="stable") is None
    assert v13.entry(name, edition="alpha") is None
    with pytest.raises(v14.EditionV14ReplayError, match="body_checked"):
        v14.replay(name, edition="alpha")


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v14_flagship_bodies_replay_and_mutations_fail(name: str) -> None:
    row = _frontier_by_name()[name]
    core = {spec.name: spec for spec in v14.ALPHA_SPECS}
    receipt, = replay_candidate_bodies((row,), core=core)
    assert receipt.name == name
    assert receipt.proof_nodes > 0
    assert receipt.dependency_count == len(row.dependencies)
    corrupted = replace(row, script=row.script[:-1])
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((corrupted,), core=core)


@pytest.mark.parametrize("path, expected", tuple(PARENT_ARTIFACT_HASHES.items()))
def test_v14_preserves_every_sealed_v13_artifact_byte(
    path: str,
    expected: str,
) -> None:
    assert sha256((REPOSITORY / path).read_bytes()).hexdigest() == expected


def test_v14_new_artifacts_have_real_body_receipts_and_no_false_closure() -> None:
    catalog_path = REPOSITORY / "artifacts/peano-library/alpha/catalog-v14.json"
    metrics_path = REPOSITORY / "artifacts/peano-library/alpha/metrics-v14.json"
    graph_path = REPOSITORY / "artifacts/peano-library/alpha/dependency-graph-v14.mmd"
    channels_path = REPOSITORY / "artifacts/peano-library/channels-v14.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    channels = json.loads(channels_path.read_text(encoding="utf-8"))
    parent = json.loads(
        (REPOSITORY / "artifacts/peano-library/alpha/catalog-v13.json").read_text(
            encoding="utf-8"
        )
    )

    assert catalog["schema"] == "peano-library-alpha-snapshot-v14"
    assert metrics["schema"] == "peano-library-alpha-metrics-v14"
    assert channels["schema"] == "peano-library-channels-v14"
    assert catalog["theorem_count"] == metrics["theorem_count"] == 1_556
    assert catalog["stable_count"] == 432
    assert catalog["checked_use_count"] == metrics["checked_use_count"] == 570
    assert catalog["theorems"][:1_543] == parent["theorems"]
    assert metrics["catalog_sha256"] == sha256(catalog_path.read_bytes()).hexdigest()
    assert metrics["dependency_graph_sha256"] == sha256(graph_path.read_bytes()).hexdigest()
    assert channels["default_channel"] == "stable"

    specs = _frontier_by_name()
    for row in catalog["theorems"][1_543:]:
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

    core = {spec.name: spec for spec in v14.ALPHA_SPECS}
    by_name = {row["name"]: row for row in catalog["theorems"]}
    for name in ROOT_HASHES:
        checked, = replay_candidate_bodies((specs[name],), core=core)
        recorded = by_name[name]["body_receipt"]
        for key, value in asdict(checked).items():
            assert recorded[key] == value


def test_v14_rfc_records_exact_evidence_and_nonpromotion_boundary() -> None:
    text = (
        REPOSITORY
        / "research/arithmetic-library/alpha-v14-kummer-admission-rfc-v1.md"
    ).read_text(encoding="utf-8")
    assert "1,543" in text and "1,556" in text
    assert "13" in text and "570" in text
    assert "95" in text and "body_checked" in text
    assert "empty-context" in text
    assert all(name in text for name in ROOT_HASHES)
    assert all(receipt in text for receipt in ROOT_HASHES.values())
