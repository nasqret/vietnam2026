"""Adversarial acceptance tests for Hydra's candidate epoch metadata."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import training.peano_hydra.library_epoch_metadata as metadata_module  # noqa: E402
from training.peano_hydra.library_epoch_metadata import (  # noqa: E402
    LibraryEpochMetadataError,
    build_candidate_epoch_metadata,
    canonical_document_bytes,
    epoch_metadata_schema,
    epoch_metadata_schema_identity,
    load_epoch_metadata,
    readiness_report,
    validate_epoch_metadata,
)


SCHEMA_PATH = (
    ROOT / "training/peano_hydra/library-epoch-metadata-schema-v1.json"
)
REPLAY_MANIFEST_PATH = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
REPLAY_REPORT_PATH = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)
CLI_PATH = ROOT / "scripts/build_peano_hydra_epoch_metadata.py"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _reroot(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    old_preimage = result["root_preimage"]
    preimage = {
        "format": old_preimage["format"],
        "payload": deepcopy(body),
        "v": old_preimage["v"],
    }
    result["root_preimage"] = preimage
    result["root_sha256"] = hashlib.sha256(
        _canonical_json_bytes(preimage)
    ).hexdigest()
    return result


def _mutated(
    candidate: dict[str, object], mutation
) -> dict[str, object]:
    value = deepcopy(candidate)
    mutation(value)
    return _reroot(value)


@pytest.fixture(scope="module")
def candidate() -> dict[str, object]:
    return build_candidate_epoch_metadata()


@pytest.fixture(scope="module")
def replay_manifest() -> dict[str, object]:
    return json.loads(REPLAY_MANIFEST_PATH.read_bytes())


def test_schema_is_canonical_closed_pinned_and_candidate_only() -> None:
    schema = epoch_metadata_schema()
    identity = epoch_metadata_schema_identity()
    raw = SCHEMA_PATH.read_bytes()
    assert raw == canonical_document_bytes(schema)
    assert hashlib.sha256(raw).hexdigest() == (
        "9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956"
    )
    assert hashlib.sha256(_canonical_json_bytes(schema)).hexdigest() == (
        "71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c"
    )
    assert identity == {
        "artifact_sha256": hashlib.sha256(raw).hexdigest(),
        "format": schema["format"],
        "id": schema["id"],
        "sha256": hashlib.sha256(_canonical_json_bytes(schema)).hexdigest(),
        "v": schema["v"],
    }
    assert schema["additional_fields_policy"] == (
        "forbidden-at-every-schema-owned-object"
    )
    assert schema["constants"] == {
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": "intuitionistic",
        "status": "candidate",
    }
    assert schema["claim_boundary"]["candidate_only"] is True
    assert schema["claim_boundary"]["freeze_ready"] is False
    assert "absent" in schema["claim_boundary"]["owner_authority"]


def test_two_clean_builds_are_byte_deterministic_and_validate_detached(
    candidate: dict[str, object],
) -> None:
    second = build_candidate_epoch_metadata()
    assert second == candidate
    assert canonical_document_bytes(second) == canonical_document_bytes(candidate)
    assert len(canonical_document_bytes(candidate)) == 5_880_054
    assert candidate["root_sha256"] == (
        "b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279"
    )
    checked = validate_epoch_metadata(candidate)
    assert checked == candidate
    checked["theorems"][0]["name"] = "detached-mutation"
    assert candidate["theorems"][0]["name"] != "detached-mutation"


def test_candidate_has_exact_replay_order_and_per_theorem_bindings(
    candidate: dict[str, object], replay_manifest: dict[str, object]
) -> None:
    rows = candidate["theorems"]
    replay_rows = replay_manifest["theorems"]
    assert candidate["theorem_count"] == len(rows) == len(replay_rows) == 384
    assert candidate["aggregate"]["theorem_count"] == 384
    assert [row["index"] for row in rows] == list(range(384))
    assert [row["declaration_order"] for row in rows] == list(range(384))
    assert [row["name"] for row in rows] == [row["name"] for row in replay_rows]

    for row, replay in zip(rows, replay_rows, strict=True):
        assert row["statement"] == {
            "canonical": replay["statement_canonical"],
            "canonical_sha256": replay["statement_canonical_sha256"],
            "formula_sha256": replay["formula_sha256"],
            "source": replay["statement_source"],
            "source_sha256": replay["statement_source_sha256"],
        }
        assert row["readable_proof"] == {
            "script": replay["script"],
            "script_sha256": replay["script_sha256"],
        }
        assert row["proof"] == {
            "artifact": replay["artifact"],
            "construction_metrics": replay["construction_metrics"],
            "formula_sha256": replay["formula_sha256"],
            "packed_tree_metrics": replay["packed_tree_metrics"],
            "proof_term_sha256": replay["proof_term_sha256"],
            "replay_status": "kernel-accepted-retained-report",
        }
        assert row["optimized_construction"] == {
            "artifact_sha256": replay["artifact"]["sha256"],
            "claim": "submitted-not-best-known",
            "proof_term_sha256": replay["proof_term_sha256"],
        }
        assert row["dependencies"]["declared_publication_dependencies"] == (
            replay["declared_dependencies"]
        )


def test_candidate_binds_exact_replay_manifest_and_report(
    candidate: dict[str, object], replay_manifest: dict[str, object]
) -> None:
    replay = candidate["replay_pack"]
    manifest_raw = REPLAY_MANIFEST_PATH.read_bytes()
    report_raw = REPLAY_REPORT_PATH.read_bytes()
    report = json.loads(report_raw)
    assert replay["manifest_artifact_sha256"] == hashlib.sha256(
        manifest_raw
    ).hexdigest()
    assert replay["manifest_root_sha256"] == replay_manifest["root_sha256"]
    assert replay["replay_root_sha256"] == replay_manifest["replay_root_sha256"]
    assert replay["verification_report_artifact_sha256"] == hashlib.sha256(
        report_raw
    ).hexdigest()
    assert replay["verification_status"] == report["status"] == "passed"
    assert report["kernel_checked_count"] == report["theorem_count"] == 384
    assert candidate["repository"] == {
        "commit": "32803924d7def862ccf0b738cd1ed494a3165f7e",
        "source": "retained-replay-pack-snapshot",
        "tree": "e945e4963ad53b1c07008fd8356980bdacc3bafe",
        "url": "https://github.com/nasqret/vietnam2026",
    }


def test_replay_artifact_pins_fail_closed_before_semantic_rebinding(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert metadata_module.REPLAY_MANIFEST_ARTIFACT_SHA256 == (
        "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
    )
    assert metadata_module.REPLAY_REPORT_ARTIFACT_SHA256 == (
        "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"
    )
    monkeypatch.setattr(
        metadata_module, "REPLAY_MANIFEST_ARTIFACT_SHA256", "0" * 64
    )
    with pytest.raises(LibraryEpochMetadataError, match="pinned source snapshot"):
        build_candidate_epoch_metadata()
    monkeypatch.undo()
    monkeypatch.setattr(
        metadata_module, "REPLAY_REPORT_ARTIFACT_SHA256", "0" * 64
    )
    with pytest.raises(LibraryEpochMetadataError, match="pinned source snapshot"):
        build_candidate_epoch_metadata()


def test_unresolved_claims_are_explicit_and_gap_counts_are_exact(
    candidate: dict[str, object],
) -> None:
    rows = candidate["theorems"]
    assert candidate["status"] == "candidate"
    assert candidate["logic_mode"] == "intuitionistic"
    assert candidate["evaluation_eligible"] is False
    assert candidate["freeze_ready"] is False
    for row in rows:
        dependencies = row["dependencies"]
        assert dependencies["status"] == "declared-publication-only"
        assert dependencies["minimality_claim"] is False
        assert dependencies["readable_dependencies"] is None
        assert dependencies["optimized_dependencies"] is None
        assert dependencies["publication_union"] is None
        assert dependencies["readable_leave_one_out_receipt_sha256"] is None
        assert dependencies["optimized_leave_one_out_receipt_sha256"] is None
        assert row["explanation"]["review_status"] == "pending-human-review"
        assert row["lineage"] == {"id": None, "status": "pending"}
        assert row["optimized_construction"]["claim"] == (
            "submitted-not-best-known"
        )
    gaps = candidate["gaps"]
    assert gaps["readable_dependency_vectors_unverified_count"] == 384
    assert gaps["optimized_dependency_vectors_pending_count"] == 384
    assert gaps["publication_union_pending_count"] == 384
    assert gaps["optimized_best_known_pending_count"] == 384
    assert gaps["human_review_pending_count"] == 384
    assert gaps["lineage_pending_count"] == 384


def test_source_and_document_statuses_match_aggregate_gap_counts(
    candidate: dict[str, object],
) -> None:
    rows = candidate["theorems"]
    statuses = {"missing", "present", "stale"}
    assert all(row["source"]["status"] in statuses for row in rows)
    assert candidate["aggregate"]["source_locator_count"] == sum(
        row["source"]["status"] == "present" for row in rows
    ) == 384
    assert candidate["gaps"]["source_locator_missing_count"] == sum(
        row["source"]["status"] != "present" for row in rows
    )
    for kind in ("atlas", "defined_explorer", "explicit_explorer", "vault"):
        observed = [row["documentation"][kind]["status"] for row in rows]
        assert set(observed) <= statuses
        assert candidate["gaps"][f"{kind}_missing_count"] == observed.count(
            "missing"
        )
        assert candidate["gaps"][f"{kind}_stale_count"] == observed.count("stale")
    assert candidate["aggregate"]["documentation_complete_count"] == sum(
        row["source"]["status"] == "present"
        and row["definitions"]["status"] == "present"
        and all(
            receipt["status"] == "present"
            for receipt in row["documentation"].values()
        )
        for row in rows
    ) == 240
    assert candidate["aggregate"]["declared_dependency_edges"] == 1038
    assert candidate["gaps"]["atlas_missing_count"] == 0
    assert candidate["gaps"]["atlas_stale_count"] == 0
    assert candidate["gaps"]["vault_missing_count"] == 0
    assert candidate["gaps"]["vault_stale_count"] == 0
    assert candidate["gaps"]["defined_explorer_missing_count"] == 144
    assert candidate["gaps"]["defined_explorer_stale_count"] == 0
    assert candidate["gaps"]["explicit_explorer_missing_count"] == 144
    assert candidate["gaps"]["explicit_explorer_stale_count"] == 0
    assert candidate["gaps"]["definition_receipt_missing_count"] == 144
    assert candidate["gaps"]["definition_receipt_stale_count"] == 0
    assert sum(row["definitions"]["status"] == "present" for row in rows) == 240


def test_nonpublic_explorer_rows_cannot_contaminate_candidate_receipts(
    candidate: dict[str, object],
) -> None:
    paths = {
        "explicit_explorer": (
            ROOT / "book/_static/pa-proof-explorer/api/corpus.json"
        ),
        "defined_explorer": (
            ROOT / "book/_static/pa-proof-explorer/defined/api/corpus.json"
        ),
    }
    candidate_names = {row["name"] for row in candidate["theorems"]}
    for kind, path in paths.items():
        corpus = json.loads(path.read_bytes())
        source_rows = corpus["theorems"]
        public = [
            row
            for row in source_rows
            if row.get("scope") == "public" and row.get("status") == "public"
        ]
        excluded = [row for row in source_rows if row not in public]
        assert len(source_rows) == len({row["name"] for row in source_rows}) == 557
        assert len(public) == 240
        assert len(excluded) == 317
        assert candidate["documentation_sources"][kind]["record_count"] == 557
        assert sum(
            row["documentation"][kind]["status"] == "present"
            for row in candidate["theorems"]
        ) == 240
        source_names = {row["name"] for row in source_rows}
        public_names = {row["name"] for row in public}
        excluded_names = {row["name"] for row in excluded}
        # All 317 non-public rows belong to later library growth and must not
        # leak into L0. The 144 candidate gaps are genuinely absent records,
        # so they are missing rather than stale.
        assert excluded_names.isdisjoint(candidate_names)
        assert len(public_names & candidate_names) == 240
        assert len(source_names & candidate_names) == 240
        assert len(candidate_names - source_names) == 144


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"status": "frozen"}),
        lambda value: value.update({"evaluation_eligible": True}),
        lambda value: value.update({"freeze_ready": True}),
        lambda value: value.update({"logic_mode": "classical"}),
        lambda value: value.update({"independent_owner": {"forged": True}}),
        lambda value: value["theorems"][0]["logic"].update({"mode": "classical"}),
        lambda value: value["theorems"][0]["optimized_construction"].update(
            {"claim": "best-known"}
        ),
        lambda value: value["theorems"][0]["dependencies"].update(
            {"minimality_claim": True}
        ),
    ],
)
def test_candidate_cannot_forge_classical_owner_freeze_or_optimization_authority(
    candidate: dict[str, object], mutation
) -> None:
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(_mutated(candidate, mutation))


def test_readiness_report_revalidates_and_cannot_upgrade_a_rerooted_candidate(
    candidate: dict[str, object],
) -> None:
    report = readiness_report(candidate)
    assert report["status"] == "candidate"
    assert report["freeze_ready"] is False
    assert report["evaluation_eligible"] is False
    assert report["metadata_root_sha256"] == candidate["root_sha256"]
    forged = _mutated(
        candidate,
        lambda value: value["replay_pack"].update(
            {"manifest_root_sha256": "0" * 64}
        ),
    )
    with pytest.raises(LibraryEpochMetadataError):
        readiness_report(forged)


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["theorems"].pop(),
        lambda value: value["theorems"].append(deepcopy(value["theorems"][-1])),
        lambda value: value["theorems"].__setitem__(
            slice(0, 2), list(reversed(value["theorems"][:2]))
        ),
        lambda value: value["theorems"][0].update({"name": "forged_name"}),
        lambda value: value["theorems"][0].update({"index": 1}),
        lambda value: value["theorems"][0].update({"declaration_order": 1}),
        lambda value: value["theorems"][0]["source"].update(
            {"unregistered_field": True}
        ),
        lambda value: value["theorems"][2]["dependencies"].update(
            {"declared_publication_dependencies": []}
        ),
    ],
)
def test_missing_extra_reordered_renamed_or_dependency_forged_rows_fail(
    candidate: dict[str, object], mutation
) -> None:
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(_mutated(candidate, mutation))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value.update({"theorem_count": True}),
        lambda value: value["aggregate"].update({"theorem_count": True}),
        lambda value: value["theorems"][0].update({"index": False}),
        lambda value: value["theorems"][0]["source"].update({"line": True}),
        lambda value: value.update({"v": True}),
    ],
)
def test_counts_indexes_lines_and_versions_are_type_exact(
    candidate: dict[str, object], mutation
) -> None:
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(_mutated(candidate, mutation))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["theorems"][0]["source"].update(
            {"path": "../outside.py"}
        ),
        lambda value: value["theorems"][0]["source"].update(
            {"path": "/absolute/source.py"}
        ),
        lambda value: value["theorems"][0]["source"].update(
            {"path": "peano-lab\\unsafe.py"}
        ),
        lambda value: value["theorems"][0]["documentation"]["vault"].update(
            {"artifact_path": "../outside.md"}
        ),
        lambda value: value["theorems"][0]["documentation"]["atlas"].update(
            {"artifact_path": "/absolute/atlas.html"}
        ),
        lambda value: value["theorems"][0]["proof"]["artifact"].update(
            {"path": "certificates/../forged.pl2"}
        ),
    ],
)
def test_unsafe_source_document_and_proof_paths_fail(
    candidate: dict[str, object], mutation
) -> None:
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(_mutated(candidate, mutation))


@pytest.mark.parametrize(
    "mutation",
    [
        lambda value: value["replay_pack"].update(
            {"manifest_root_sha256": "0" * 64}
        ),
        lambda value: value["replay_pack"].update(
            {"replay_root_sha256": "0" * 64}
        ),
        lambda value: value["replay_pack"].update(
            {"verification_report_artifact_sha256": "0" * 64}
        ),
        lambda value: value["replay_pack"].update(
            {"verification_status": "failed"}
        ),
        lambda value: value["theorems"][0]["statement"].update(
            {"formula_sha256": "0" * 64}
        ),
        lambda value: value["theorems"][0]["proof"].update(
            {"proof_term_sha256": "0" * 64}
        ),
        lambda value: value["theorems"][0]["source"].update(
            {"file_sha256": "0" * 64}
        ),
        lambda value: value["theorems"][0]["documentation"]["vault"].update(
            {"artifact_sha256": "0" * 64, "status": "present"}
        ),
    ],
)
def test_fully_rerooted_replay_statement_proof_source_and_document_forgeries_fail(
    candidate: dict[str, object], mutation
) -> None:
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(_mutated(candidate, mutation))


def test_root_preimage_and_root_mutations_fail(candidate: dict[str, object]) -> None:
    wrong_root = deepcopy(candidate)
    wrong_root["root_sha256"] = "0" * 64
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(wrong_root)

    wrong_preimage = deepcopy(candidate)
    wrong_preimage["root_preimage"]["payload"]["status"] = "frozen"
    with pytest.raises(LibraryEpochMetadataError):
        validate_epoch_metadata(wrong_preimage)


def test_loader_accepts_only_one_canonical_bounded_document(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    path = tmp_path / "candidate-metadata.json"
    canonical = canonical_document_bytes(candidate)
    path.write_bytes(canonical)
    assert load_epoch_metadata(path) == candidate

    path.write_bytes(_canonical_json_bytes(candidate))
    with pytest.raises(LibraryEpochMetadataError):
        load_epoch_metadata(path)

    duplicate = canonical.replace(
        b'{\n  "aggregate"',
        b'{\n  "status": "duplicate",\n  "aggregate"',
        1,
    )
    path.write_bytes(duplicate)
    with pytest.raises(LibraryEpochMetadataError):
        load_epoch_metadata(path)

    extra = deepcopy(candidate)
    extra["owner_receipt"] = None
    path.write_bytes(canonical_document_bytes(extra))
    with pytest.raises(LibraryEpochMetadataError):
        load_epoch_metadata(path)

    floating = canonical.replace(b'"theorem_count": 384', b'"theorem_count": 384.0', 1)
    path.write_bytes(floating)
    with pytest.raises(LibraryEpochMetadataError, match="floating-point"):
        load_epoch_metadata(path)

    nonfinite = canonical.replace(b'"theorem_count": 384', b'"theorem_count": NaN', 1)
    path.write_bytes(nonfinite)
    with pytest.raises(LibraryEpochMetadataError, match="forbidden JSON constant"):
        load_epoch_metadata(path)


def test_loader_and_builder_reject_symlink_and_special_file_inputs(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    canonical_path = tmp_path / "canonical.json"
    canonical_path.write_bytes(canonical_document_bytes(candidate))
    linked = tmp_path / "linked.json"
    linked.symlink_to(canonical_path)
    with pytest.raises(LibraryEpochMetadataError, match="cannot read"):
        load_epoch_metadata(linked)

    fifo = tmp_path / "metadata.fifo"
    os.mkfifo(fifo)
    with pytest.raises(LibraryEpochMetadataError, match="regular file"):
        load_epoch_metadata(fifo)

    linked_root = tmp_path / "repository-link"
    linked_root.symlink_to(ROOT, target_is_directory=True)
    with pytest.raises(LibraryEpochMetadataError, match="non-symlink directory"):
        build_candidate_epoch_metadata(repository_root=linked_root)


def test_live_input_hash_drift_fails_and_document_drift_stays_an_explicit_gap(
    candidate: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    original = metadata_module._read_bounded_regular_file
    source_path = (ROOT / candidate["theorems"][0]["source"]["path"]).resolve()

    def changed_source(path: Path, **kwargs) -> bytes:
        raw = original(path, **kwargs)
        if path.resolve() == source_path:
            return raw + b"\n"
        return raw

    monkeypatch.setattr(
        metadata_module, "_read_bounded_regular_file", changed_source
    )
    with pytest.raises(LibraryEpochMetadataError, match="differs from the replay"):
        build_candidate_epoch_metadata()

    atlas_path = (ROOT / "book/arithmetic-library/theorem-atlas.md").resolve()

    def stale_atlas(path: Path, **kwargs) -> bytes:
        raw = original(path, **kwargs)
        if path.resolve() == atlas_path:
            return raw.replace(
                b"32803924d7def862ccf0b738cd1ed494a3165f7e",
                b"0000000000000000000000000000000000000000",
            )
        return raw

    monkeypatch.setattr(metadata_module, "_read_bounded_regular_file", stale_atlas)
    stale = build_candidate_epoch_metadata()
    assert stale["freeze_ready"] is False
    assert stale["evaluation_eligible"] is False
    assert stale["gaps"]["atlas_stale_count"] == 384
    assert stale["aggregate"]["documentation_complete_count"] == 0


def test_changed_retained_replay_report_cannot_be_rebound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original = metadata_module._read_bounded_regular_file
    report_path = REPLAY_REPORT_PATH.resolve()

    def changed_report(path: Path, **kwargs) -> bytes:
        raw = original(path, **kwargs)
        if path.resolve() == report_path:
            report = json.loads(raw)
            report["replay_root_sha256"] = "0" * 64
            return canonical_document_bytes(report)
        return raw

    monkeypatch.setattr(
        metadata_module, "_read_bounded_regular_file", changed_report
    )
    with pytest.raises(
        LibraryEpochMetadataError,
        match="differs from the pinned source snapshot|not bound to the pack",
    ):
        build_candidate_epoch_metadata()


def _run_cli(*arguments: object, cwd: Path) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [sys.executable, str(CLI_PATH), *(str(item) for item in arguments)],
        cwd=cwd,
        check=False,
        capture_output=True,
        timeout=60,
    )


def test_cli_defaults_to_stdout_without_an_implicit_retained_write(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    suggested = ROOT / "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json"
    existed_before = suggested.exists()
    digest_before = hashlib.sha256(suggested.read_bytes()).hexdigest() if existed_before else None
    completed = _run_cli(cwd=tmp_path)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert completed.stderr == b""
    assert completed.stdout == canonical_document_bytes(candidate)
    assert suggested.exists() is existed_before
    if existed_before:
        assert hashlib.sha256(suggested.read_bytes()).hexdigest() == digest_before


def test_cli_explicit_outputs_are_deterministic_and_check_is_read_only(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    output = tmp_path / "metadata.json"
    report = tmp_path / "readiness.json"
    completed = _run_cli("--output", output, "--report", report, cwd=tmp_path)
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    assert output.read_bytes() == canonical_document_bytes(candidate)
    assert report.read_bytes() == canonical_document_bytes(readiness_report(candidate))
    before = (output.read_bytes(), report.read_bytes())
    checked = _run_cli(
        "--check", "--output", output, "--report", report, cwd=tmp_path
    )
    assert checked.returncode == 0, checked.stderr.decode("utf-8", "replace")
    assert (output.read_bytes(), report.read_bytes()) == before

    output.write_bytes(b"stale\n")
    failed = _run_cli("--check", "--output", output, cwd=tmp_path)
    assert failed.returncode != 0
    assert output.read_bytes() == b"stale\n"


def test_cli_destination_rejection_fails_without_mutating_existing_bytes(
    tmp_path: Path,
) -> None:
    same = tmp_path / "same.json"
    same.write_bytes(b"sentinel\n")
    rejected = _run_cli("--output", same, "--report", same, cwd=tmp_path)
    assert rejected.returncode != 0
    assert same.read_bytes() == b"sentinel\n"

    target = tmp_path / "target.json"
    target.write_bytes(b"target-sentinel\n")
    linked = tmp_path / "linked-output.json"
    linked.symlink_to(target)
    rejected = _run_cli("--output", linked, cwd=tmp_path)
    assert rejected.returncode != 0
    assert target.read_bytes() == b"target-sentinel\n"
    assert linked.is_symlink()


def test_legacy_epoch_v1_schema_remains_byte_pinned() -> None:
    legacy_module = ROOT / "training/peano_hydra/library_epoch.py"
    legacy_path = ROOT / "training/peano_hydra/library-epoch-schema-v1.json"
    assert hashlib.sha256(legacy_module.read_bytes()).hexdigest() == (
        "2bb980aa0900f6a9a5061876aeb393e4b3fc5753116c07e8d77b112d3bf20f8b"
    )
    assert hashlib.sha256(legacy_path.read_bytes()).hexdigest() == (
        "ded0574fef1ff9cee3ad2748ea987a448419cbec2b9d55277bced528307d3613"
    )
