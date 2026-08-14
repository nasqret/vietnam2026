"""Focused adversarial tests for Hydra H1.1 library-epoch isolation."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from types import MappingProxyType, SimpleNamespace
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import training.peano_hydra.library_epoch as epoch_module  # noqa: E402
from training.peano_hydra.library_epoch import (  # noqa: E402
    AUTHORING_REPOSITORY_SOURCE,
    AUTHORING_SCOPE,
    CANDIDATE_STATUS,
    CATALOG_CERTIFICATE_REPRESENTATION,
    EPOCH_PACK_FORMAT,
    EPOCH_PACK_ROOT_PREIMAGE_FORMAT,
    EPOCH_PACK_VERSION,
    FROZEN_REPOSITORY_SOURCE,
    FROZEN_SCOPE,
    FROZEN_STATUS,
    H0_REPORT_SHA256,
    LIBRARY_EPOCH_FORMAT,
    LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT,
    LIBRARY_EPOCH_SCHEMA_ID,
    LIBRARY_EPOCH_SCHEMA_PATH,
    LIBRARY_EPOCH_SCHEMA_SHA256,
    LIBRARY_EPOCH_VERSION,
    LOGIC_MODE,
    OWNER_RECEIPT_FORMAT,
    OWNER_RECEIPT_VERSION,
    OWNER_ROLE,
    LibraryEpochError,
    build_candidate_library_epoch,
    build_candidate_library_epoch_pack,
    build_frozen_library_epoch,
    canonical_document_bytes,
    canonical_json_bytes,
    library_epoch_schema,
    library_epoch_schema_identity,
    load_library_epoch,
    validate_library_epoch,
)
from training.peano_hydra.profile import (  # noqa: E402
    SEMANTIC_PROFILE_FORMAT,
    SEMANTIC_PROFILE_ID,
    SEMANTIC_PROFILE_V2_DOCUMENT_SHA256,
    SEMANTIC_PROFILE_V2_SHA256,
    SEMANTIC_PROFILE_VERSION,
)


EXPECTED_SCHEMA_SHA256 = (
    "f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b"
)
EXPECTED_CATALOG_ARTIFACT_SHA256 = (
    "326ffe660da6e34a3aa12e0aa13096078a0bf20c45c440049aaf5d5bed1f1be7"
)
EXPECTED_CATALOG_SHA256 = (
    "f5c7318229ea76b372d7f09250241ba7bb98b3829a8853e85ad2d8528b710a51"
)
EXPECTED_ORDERED_ROOT = (
    "73b31b4775d24b6bb9730f2f2df37409aa56dc771fe3e1d0f9de5134b166e89b"
)
EXPECTED_SOURCE_ROOT = (
    "6fefaa2bdc92e477ce20444122ea1c752420e7efc1706a664777cb887128a3be"
)
EXPECTED_H0_REPLAY_ROOT = (
    "fae19fad55c416ae7b695107390c1c733d6740fe63d10cf0efed127f5801b9d2"
)
TEST_DEPOSIT_ID = "independent-deposit-test"
TEST_OWNER_ID = "independent-owner:test"


@pytest.fixture(scope="module")
def candidate() -> dict[str, object]:
    return build_candidate_library_epoch("h1-contract-test")


@pytest.fixture(scope="module")
def pack_files(candidate: dict[str, object]) -> dict[str, bytes]:
    return build_candidate_library_epoch_pack(candidate)


def _reroot(value: dict[str, object]) -> dict[str, object]:
    result = deepcopy(value)
    body = {
        key: item
        for key, item in result.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT,
        "payload": deepcopy(body),
        "v": LIBRARY_EPOCH_VERSION,
    }
    result["root_preimage"] = preimage
    result["root_sha256"] = hashlib.sha256(
        canonical_json_bytes(preimage)
    ).hexdigest()
    return result


def _clean_candidate(candidate: dict[str, object]) -> dict[str, object]:
    result = deepcopy(candidate)
    result["repository"]["relevant_dirty"] = False
    return _reroot(result)


def _owner_receipt(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    *,
    sealed: bool = False,
) -> bytes:
    benchmark = (
        {"commitment_sha256": "b" * 64, "status": "sealed"}
        if sealed
        else {"commitment_sha256": None, "status": "not-sealed"}
    )
    receipt = {
        "benchmark": benchmark,
        "candidate_root_sha256": candidate["root_sha256"],
        "catalog_sha256": candidate["catalog"]["catalog_sha256"],
        "deposit_id": TEST_DEPOSIT_ID,
        "epoch_id": candidate["id"],
        "format": OWNER_RECEIPT_FORMAT,
        "owner_id": TEST_OWNER_ID,
        "owner_role": OWNER_ROLE,
        "pack_root_sha256": epoch_module._pack_manifest(pack_files)["root_sha256"],
        "repository_commit": candidate["repository"]["commit"],
        "semantic_profile_sha256": candidate["semantic_profile"]["sha256"],
        "v": OWNER_RECEIPT_VERSION,
    }
    return canonical_document_bytes(receipt)


def _register_test_receipt(
    monkeypatch: pytest.MonkeyPatch, receipt: bytes
) -> None:
    monkeypatch.setattr(
        epoch_module,
        "_REGISTERED_OWNER_RECEIPTS",
        {
            hashlib.sha256(receipt).hexdigest(): (
                TEST_DEPOSIT_ID,
                TEST_OWNER_ID,
            )
        },
    )


def _build_synthetic_frozen_fixture(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    *,
    sealed: bool = False,
) -> tuple[dict[str, object], dict[str, object], bytes]:
    clean = _clean_candidate(candidate)
    receipt = _owner_receipt(clean, pack_files, sealed=sealed)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", lambda: False)
    _register_test_receipt(monkeypatch, receipt)
    frozen = build_frozen_library_epoch(
        clean,
        independent_owner_receipt=receipt,
        pack_files=pack_files,
    )
    return clean, frozen, receipt


def test_schema_is_canonical_closed_and_semantically_pinned() -> None:
    schema = library_epoch_schema()
    assert LIBRARY_EPOCH_SCHEMA_SHA256 == EXPECTED_SCHEMA_SHA256
    assert LIBRARY_EPOCH_SCHEMA_PATH.read_bytes() == canonical_document_bytes(schema)
    assert hashlib.sha256(canonical_json_bytes(schema)).hexdigest() == (
        EXPECTED_SCHEMA_SHA256
    )
    assert library_epoch_schema_identity() == {
        "format": "peano-hydra-library-epoch-schema",
        "id": LIBRARY_EPOCH_SCHEMA_ID,
        "sha256": EXPECTED_SCHEMA_SHA256,
        "v": 1,
    }
    assert schema["additional_fields_policy"] == (
        "forbidden-at-every-schema-owned-object"
    )
    assert schema["epoch"]["candidate"]["constants"] == {
        "benchmark.status": "not-sealed",
        "evaluation_eligible": False,
        "independent_commitment": None,
        "pack": None,
        "repository.source": AUTHORING_REPOSITORY_SOURCE,
        "scope": AUTHORING_SCOPE,
        "status": CANDIDATE_STATUS,
    }
    assert schema["epoch"]["frozen"]["constants"] == {
        "external_owner_receipt_required": True,
        "pack_bytes_required": True,
        "repository.relevant_dirty": False,
        "repository.source": FROZEN_REPOSITORY_SOURCE,
        "scope": FROZEN_SCOPE,
        "status": FROZEN_STATUS,
    }
    assert schema["freeze_authority"] == {
        "current_registered_receipts": 0,
        "rule": (
            "receipt SHA-256, deposit ID, and owner ID must match a reviewed "
            "registry entry"
        ),
        "v1_can_publish_frozen_epoch": False,
    }


def test_candidate_binds_live_head_profile_catalog_and_h0(
    candidate: dict[str, object],
) -> None:
    assert candidate["format"] == LIBRARY_EPOCH_FORMAT
    assert candidate["v"] == LIBRARY_EPOCH_VERSION
    assert candidate["status"] == CANDIDATE_STATUS
    assert candidate["scope"] == AUTHORING_SCOPE
    assert candidate["logic_mode"] == LOGIC_MODE
    assert candidate["evaluation_eligible"] is False
    assert candidate["benchmark"] == {
        "commitment_sha256": None,
        "status": "not-sealed",
    }
    assert candidate["independent_commitment"] is None
    assert candidate["pack"] is None

    assert candidate["semantic_profile"] == {
        "artifact_path": "training/peano_hydra/semantic-profile-v2.json",
        "artifact_sha256": SEMANTIC_PROFILE_V2_DOCUMENT_SHA256,
        "certificate_representation": "peano-lab-v2",
        "format": SEMANTIC_PROFILE_FORMAT,
        "id": SEMANTIC_PROFILE_ID,
        "logic": LOGIC_MODE,
        "sha256": SEMANTIC_PROFILE_V2_SHA256,
        "v": SEMANTIC_PROFILE_VERSION,
    }
    assert candidate["catalog"] == {
        "artifact_path": "artifacts/peano-library/catalog-v1.json",
        "artifact_sha256": EXPECTED_CATALOG_ARTIFACT_SHA256,
        "catalog_sha256": EXPECTED_CATALOG_SHA256,
        "certificate_representation": CATALOG_CERTIFICATE_REPRESENTATION,
        "evaluation_certificate_representation": "peano-lab-v2",
        "id": "peano-lab-public-runtime",
        "ordered_root_sha256": EXPECTED_ORDERED_ROOT,
        "schema": "peano-library-snapshot-v3",
        "source_root_sha256": EXPECTED_SOURCE_ROOT,
        "theorem_count": 384,
    }
    h0 = candidate["h0_replay"]
    assert h0["report_path"] == "artifacts/peano-hydra/h0-validation-v2.json"
    assert h0["report_sha256"] == H0_REPORT_SHA256
    assert h0["profile_sha256"] == SEMANTIC_PROFILE_V2_SHA256
    assert h0["library_count"] == 384
    assert h0["replay_pass_count"] == 2
    assert h0["replay_root_sha256"] == EXPECTED_H0_REPLAY_ROOT
    assert h0["artifact_case_count"] == 2058
    assert h0["validation_passed"] is h0["campaign_eligible"] is True
    repository = candidate["repository"]
    assert len(repository["commit"]) == 40
    assert type(repository["relevant_dirty"]) is bool
    assert repository["source"] == AUTHORING_REPOSITORY_SOURCE


def test_candidate_pack_is_exact_content_addressed_and_non_self_referential(
    pack_files: dict[str, bytes],
) -> None:
    assert len(pack_files) == 3
    manifest = epoch_module._pack_manifest(pack_files)
    assert epoch_module._pack_manifest(MappingProxyType(pack_files)) == manifest
    checked_manifest, checked_files = epoch_module._validate_pack(
        manifest, MappingProxyType(pack_files)
    )
    assert checked_manifest == manifest
    assert checked_files == pack_files
    assert manifest["format"] == EPOCH_PACK_FORMAT
    assert manifest["v"] == EPOCH_PACK_VERSION
    assert [row["role"] for row in manifest["files"]] == [
        "catalog",
        "semantic-profile",
        "h0-replay",
    ]
    for row in manifest["files"]:
        raw = pack_files[row["path"]]
        assert row["path"] == f"pack/{row['role']}-{row['sha256']}.json"
        assert row["sha256"] == hashlib.sha256(raw).hexdigest()
        assert row["bytes"] == len(raw)
    preimage = manifest["root_preimage"]
    assert preimage == {
        "files": manifest["files"],
        "format": EPOCH_PACK_ROOT_PREIMAGE_FORMAT,
        "v": EPOCH_PACK_VERSION,
    }
    assert "root_sha256" not in preimage
    assert "root_preimage" not in preimage
    assert manifest["root_sha256"] == hashlib.sha256(
        canonical_json_bytes(preimage)
    ).hexdigest()


def test_epoch_root_has_an_explicit_non_self_referential_preimage(
    candidate: dict[str, object],
) -> None:
    preimage = candidate["root_preimage"]
    assert set(preimage) == {"format", "payload", "v"}
    assert preimage["format"] == LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT
    assert "root_preimage" not in preimage["payload"]
    assert "root_sha256" not in preimage["payload"]
    assert preimage["payload"] == {
        key: value
        for key, value in candidate.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    assert candidate["root_sha256"] == hashlib.sha256(
        canonical_json_bytes(preimage)
    ).hexdigest()


def test_validation_returns_detached_data_and_detects_live_drift(
    candidate: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    checked = validate_library_epoch(candidate, require_live=True)
    checked["catalog"]["theorem_count"] = 1
    assert candidate["catalog"]["theorem_count"] == 384

    drift = deepcopy(candidate["catalog"])
    drift["theorem_count"] = 383
    monkeypatch.setattr(epoch_module, "live_tracked_catalog_identity", lambda: drift)
    with pytest.raises(LibraryEpochError, match="drifted from the live catalog"):
        validate_library_epoch(candidate, require_live=True)


def test_relevant_dirty_probe_includes_untracked_semantic_sources(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seen: list[list[str]] = []
    output = {"stdout": "?? training/peano_hydra/new_rule.py\n"}

    def fake_run(command, **_kwargs):
        seen.append(command)
        return SimpleNamespace(returncode=0, stderr="", stdout=output["stdout"])

    monkeypatch.setattr(epoch_module.subprocess, "run", fake_run)
    assert epoch_module._git_relevant_dirty() is True
    assert "--untracked-files=all" in seen[0]
    assert "training/peano_hydra" in seen[0]
    assert "peano-lab/py/peano_lab/kernel" in seen[0]
    output["stdout"] = ""
    assert epoch_module._git_relevant_dirty() is False


def test_candidate_live_validation_rejects_dirty_state_drift(
    candidate: dict[str, object], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        epoch_module,
        "_git_relevant_dirty",
        lambda: not candidate["repository"]["relevant_dirty"],
    )
    with pytest.raises(LibraryEpochError, match="dirtiness drifted"):
        validate_library_epoch(candidate, require_live=True)


def test_live_catalog_derivation_rejects_a_changed_runtime_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        epoch_module.theorem_library,
        "THEOREMS",
        epoch_module.theorem_library.THEOREMS[:-1],
    )
    with pytest.raises(LibraryEpochError, match="count differs"):
        epoch_module._derive_live_catalog_identity()


def test_live_catalog_rejects_revision_change_until_fresh_process(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keys = iter(("revision-a", "revision-b"))
    calls: list[int] = []

    def derive() -> dict[str, object]:
        calls.append(len(calls) + 1)
        return {"revision": calls[-1]}

    epoch_module._cached_live_catalog_identity_json.cache_clear()
    monkeypatch.setattr(epoch_module, "_IMPORTED_LIVE_CONTENT_KEY", "revision-a")
    monkeypatch.setattr(epoch_module, "_live_catalog_cache_key", lambda: next(keys))
    monkeypatch.setattr(epoch_module, "_derive_live_catalog_identity", derive)
    assert epoch_module.live_tracked_catalog_identity() == {"revision": 1}
    with pytest.raises(LibraryEpochError, match="restart the authoring process"):
        epoch_module.live_tracked_catalog_identity()
    assert calls == [1]
    epoch_module._cached_live_catalog_identity_json.cache_clear()


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda row: row.update({"extra": True}), "non-canonical fields"),
        (lambda row: row.update({"status": "frozen"}), "immutable scope"),
        (
            lambda row: row["benchmark"].update(
                {"commitment_sha256": "b" * 64, "status": "sealed"}
            ),
            "cannot claim",
        ),
        (lambda row: row.update({"evaluation_eligible": True}), "cannot claim"),
        (lambda row: row.update({"logic_mode": "classical"}), "classical"),
        (
            lambda row: row["semantic_profile"].update({"logic": "classical"}),
            "classical",
        ),
        (
            lambda row: row["semantic_profile"].update(
                {"artifact_path": "training/../semantic-profile-v2.json"}
            ),
            "differs from active",
        ),
        (
            lambda row: row["catalog"].update(
                {"artifact_path": "artifacts/../peano-library/catalog-v1.json"}
            ),
            "unsafe",
        ),
        (
            lambda row: row["h0_replay"].update(
                {"report_path": "artifacts/../peano-hydra/h0-validation-v2.json"}
            ),
            "unsafe",
        ),
        (lambda row: row.update({"pack": {}}), "cannot claim"),
        (lambda row: row["catalog"].update({"theorem_count": -1}), "positive"),
        (
            lambda row: row["catalog"].update({"catalog_sha256": "A" * 64}),
            "lowercase SHA-256",
        ),
        (
            lambda row: row["repository"].update({"commit": "0" * 39}),
            "Git commit",
        ),
        (
            lambda row: row["repository"].update({"relevant_dirty": "false"}),
            "must be Boolean",
        ),
        (
            lambda row: row["repository"].update({"source": "git-commit"}),
            "source identity",
        ),
        (
            lambda row: row["h0_replay"].update(
                {"replay_root_sha256": "0" * 64}
            ),
            "evidence drifted",
        ),
    ],
)
def test_candidate_rejects_extra_forged_classical_path_and_identity_material(
    candidate: dict[str, object], mutate, message: str
) -> None:
    mutation = deepcopy(candidate)
    mutate(mutation)
    mutation = _reroot(mutation)
    with pytest.raises(LibraryEpochError, match=message):
        validate_library_epoch(mutation)


def test_root_and_preimage_mutations_are_rejected(
    candidate: dict[str, object],
) -> None:
    wrong_root = deepcopy(candidate)
    wrong_root["root_sha256"] = "0" * 64
    with pytest.raises(LibraryEpochError, match="root does not match"):
        validate_library_epoch(wrong_root)

    wrong_preimage = deepcopy(candidate)
    wrong_preimage["root_preimage"]["payload"]["id"] = "different"
    with pytest.raises(LibraryEpochError, match="preimage does not match"):
        validate_library_epoch(wrong_preimage)

    recursive = deepcopy(candidate)
    recursive["root_preimage"]["payload"]["root_sha256"] = "0" * 64
    with pytest.raises(LibraryEpochError, match="preimage does not match"):
        validate_library_epoch(recursive)


def test_root_preimage_and_versions_are_json_type_exact(
    candidate: dict[str, object],
) -> None:
    bool_alias = deepcopy(candidate)
    bool_alias["root_preimage"]["payload"]["evaluation_eligible"] = 0
    bool_alias["root_sha256"] = hashlib.sha256(
        canonical_json_bytes(bool_alias["root_preimage"])
    ).hexdigest()
    with pytest.raises(LibraryEpochError, match="preimage does not match"):
        validate_library_epoch(bool_alias)

    epoch_version = deepcopy(candidate)
    epoch_version["v"] = True
    epoch_version = _reroot(epoch_version)
    with pytest.raises(LibraryEpochError, match="version must be integer"):
        validate_library_epoch(epoch_version)

    preimage_version = deepcopy(candidate)
    preimage_version["root_preimage"]["v"] = True
    preimage_version["root_sha256"] = hashlib.sha256(
        canonical_json_bytes(preimage_version["root_preimage"])
    ).hexdigest()
    with pytest.raises(LibraryEpochError, match="version must be integer"):
        validate_library_epoch(preimage_version)


def test_candidate_validation_and_loading_cannot_forge_live_provenance(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    forged_commit = deepcopy(candidate)
    forged_commit["repository"]["commit"] = "0" * 40
    forged_commit = _reroot(forged_commit)
    with pytest.raises(LibraryEpochError, match="drifted from HEAD"):
        validate_library_epoch(forged_commit)
    path = tmp_path / "forged-candidate.json"
    path.write_bytes(canonical_document_bytes(forged_commit))
    with pytest.raises(LibraryEpochError, match="drifted from HEAD"):
        load_library_epoch(path)

    forged_catalog = deepcopy(candidate)
    forged_catalog["catalog"]["catalog_sha256"] = "0" * 64
    forged_catalog = _reroot(forged_catalog)
    with pytest.raises(LibraryEpochError, match="drifted from the live catalog"):
        validate_library_epoch(forged_catalog)


def test_freeze_fails_closed_for_dirty_or_unregistered_candidates(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dirty = deepcopy(candidate)
    dirty["repository"]["relevant_dirty"] = True
    dirty = _reroot(dirty)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", lambda: True)
    dirty_receipt = _owner_receipt(dirty, pack_files)
    _register_test_receipt(monkeypatch, dirty_receipt)
    with pytest.raises(LibraryEpochError, match="dirty relevant source tree"):
        build_frozen_library_epoch(
            dirty,
            independent_owner_receipt=dirty_receipt,
            pack_files=pack_files,
        )

    clean = _clean_candidate(candidate)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", lambda: False)
    receipt = _owner_receipt(clean, pack_files)
    monkeypatch.setattr(epoch_module, "_REGISTERED_OWNER_RECEIPTS", {})
    with pytest.raises(LibraryEpochError, match="reviewed independent deposit"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )


def test_unmodified_production_registry_cannot_mint_l0(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert dict(epoch_module._REGISTERED_OWNER_RECEIPTS) == {}
    with pytest.raises(TypeError):
        epoch_module._REGISTERED_OWNER_RECEIPTS["0" * 64] = (
            TEST_DEPOSIT_ID,
            TEST_OWNER_ID,
        )

    clean = _clean_candidate(candidate)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", lambda: False)
    receipt = _owner_receipt(clean, pack_files)
    with pytest.raises(LibraryEpochError, match="reviewed independent deposit"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )


@pytest.mark.parametrize("sealed", [False, True])
def test_synthetic_registered_protocol_is_pack_relative_and_validates_offline(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    sealed: bool,
) -> None:
    clean, frozen, receipt = _build_synthetic_frozen_fixture(
        candidate, pack_files, monkeypatch, sealed=sealed
    )
    assert frozen["status"] == FROZEN_STATUS
    assert frozen["scope"] == FROZEN_SCOPE
    assert frozen["repository"] == {
        "commit": clean["repository"]["commit"],
        "relevant_dirty": False,
        "source": FROZEN_REPOSITORY_SOURCE,
    }
    assert frozen["evaluation_eligible"] is sealed
    assert frozen["benchmark"]["status"] == ("sealed" if sealed else "not-sealed")
    assert frozen["catalog"]["artifact_path"].startswith("pack/catalog-")
    assert frozen["semantic_profile"]["artifact_path"].startswith(
        "pack/semantic-profile-"
    )
    assert frozen["h0_replay"]["report_path"].startswith("pack/h0-replay-")
    commitment = frozen["independent_commitment"]
    assert commitment == {
        "candidate_root_sha256": clean["root_sha256"],
        "deposit_id": TEST_DEPOSIT_ID,
        "owner_id": TEST_OWNER_ID,
        "owner_role": OWNER_ROLE,
        "pack_root_sha256": frozen["pack"]["root_sha256"],
        "receipt_format": OWNER_RECEIPT_FORMAT,
        "receipt_sha256": hashlib.sha256(receipt).hexdigest(),
        "receipt_v": OWNER_RECEIPT_VERSION,
    }
    assert validate_library_epoch(
        frozen,
        independent_owner_receipt=receipt,
        pack_files=pack_files,
    ) == frozen

    # Frozen validation is lexical/content-addressed.  Hostile symlinks under
    # an unrelated living repository root must not affect its outcome.
    hostile_root = tmp_path / "hostile-live-root"
    outside = tmp_path / "outside-live-root"
    hostile_root.mkdir()
    outside.mkdir()
    (hostile_root / "peano-lab").symlink_to(outside, target_is_directory=True)
    (hostile_root / "pack").symlink_to(outside, target_is_directory=True)
    monkeypatch.setattr(epoch_module, "_REPOSITORY_ROOT", hostile_root)
    assert validate_library_epoch(
        frozen,
        independent_owner_receipt=receipt,
        pack_files=pack_files,
    ) == frozen

    with pytest.raises(LibraryEpochError, match="must not resolve living HEAD"):
        validate_library_epoch(
            frozen,
            require_live=True,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )

    def fail_live(*_args, **_kwargs):
        raise AssertionError("frozen validation consulted living authoring state")

    monkeypatch.setattr(epoch_module, "library_epoch_schema", fail_live)
    monkeypatch.setattr(epoch_module, "_active_profile_epoch_identity", fail_live)
    monkeypatch.setattr(epoch_module, "live_tracked_catalog_identity", fail_live)
    monkeypatch.setattr(epoch_module, "h0_replay_identity", fail_live)
    monkeypatch.setattr(epoch_module, "_git_head_commit", fail_live)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", fail_live)
    monkeypatch.setattr(epoch_module.theorem_library, "replay", fail_live)
    monkeypatch.setattr(epoch_module, "_CATALOG_PATH", tmp_path / "missing-catalog")
    monkeypatch.setattr(epoch_module, "_H0_REPORT_PATH", tmp_path / "missing-h0")
    monkeypatch.setattr(
        epoch_module, "SEMANTIC_PROFILE_PATH", tmp_path / "missing-profile"
    )
    assert validate_library_epoch(
        frozen,
        independent_owner_receipt=receipt,
        pack_files=pack_files,
    ) == frozen


def test_frozen_pack_rejects_missing_extra_corrupt_and_malformed_material(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clean, frozen, receipt = _build_synthetic_frozen_fixture(
        candidate, pack_files, monkeypatch
    )
    paths = {row["role"]: row["path"] for row in frozen["pack"]["files"]}

    missing = dict(pack_files)
    del missing[paths["catalog"]]
    with pytest.raises(LibraryEpochError, match="pack file"):
        validate_library_epoch(
            frozen, independent_owner_receipt=receipt, pack_files=missing
        )

    extra = dict(pack_files)
    extra["pack/extra-" + "0" * 64 + ".json"] = b"{}\n"
    with pytest.raises(LibraryEpochError, match="incomplete or extra"):
        validate_library_epoch(
            frozen, independent_owner_receipt=receipt, pack_files=extra
        )

    corrupt = dict(pack_files)
    corrupt[paths["catalog"]] += b"\n"
    with pytest.raises(LibraryEpochError, match="file identity"):
        validate_library_epoch(
            frozen, independent_owner_receipt=receipt, pack_files=corrupt
        )

    duplicate_role = deepcopy(frozen)
    duplicate_role["pack"]["files"][1]["role"] = "catalog"
    duplicate_role["pack"]["root_preimage"]["files"][1]["role"] = "catalog"
    duplicate_role["pack"]["root_sha256"] = hashlib.sha256(
        canonical_json_bytes(duplicate_role["pack"]["root_preimage"])
    ).hexdigest()
    duplicate_role = _reroot(duplicate_role)
    with pytest.raises(LibraryEpochError, match="roles are malformed"):
        validate_library_epoch(
            duplicate_role,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )

    catalog_value = json.loads(pack_files[paths["catalog"]])
    catalog_value["extra"] = True
    extra_catalog = dict(pack_files)
    extra_catalog.pop(paths["catalog"])
    raw = canonical_document_bytes(catalog_value)
    extra_catalog[epoch_module._pack_path("catalog", hashlib.sha256(raw).hexdigest())] = raw
    altered = deepcopy(frozen)
    altered["pack"] = epoch_module._pack_manifest(extra_catalog)
    altered = _reroot(altered)
    with pytest.raises(LibraryEpochError, match="catalog has non-canonical fields"):
        validate_library_epoch(
            altered,
            independent_owner_receipt=receipt,
            pack_files=extra_catalog,
        )

    compact_catalog = dict(pack_files)
    compact_catalog.pop(paths["catalog"])
    raw = canonical_json_bytes(catalog_value)
    compact_catalog[
        epoch_module._pack_path("catalog", hashlib.sha256(raw).hexdigest())
    ] = raw
    altered = deepcopy(frozen)
    altered["pack"] = epoch_module._pack_manifest(compact_catalog)
    altered = _reroot(altered)
    with pytest.raises(LibraryEpochError, match="not one canonical JSON document"):
        validate_library_epoch(
            altered,
            independent_owner_receipt=receipt,
            pack_files=compact_catalog,
        )

    profile_value = json.loads(pack_files[paths["semantic-profile"]])
    profile_value["calculus"]["classical"] = True
    classical = dict(pack_files)
    classical.pop(paths["semantic-profile"])
    raw = canonical_document_bytes(profile_value)
    classical[
        epoch_module._pack_path(
            "semantic-profile", hashlib.sha256(raw).hexdigest()
        )
    ] = raw
    altered = deepcopy(frozen)
    altered["pack"] = epoch_module._pack_manifest(classical)
    altered = _reroot(altered)
    with pytest.raises(LibraryEpochError, match="classical material"):
        validate_library_epoch(
            altered,
            independent_owner_receipt=receipt,
            pack_files=classical,
        )


def test_owner_receipt_is_canonical_registered_external_evidence(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean = _clean_candidate(candidate)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", lambda: False)
    receipt = _owner_receipt(clean, pack_files)

    noncanonical = canonical_json_bytes(json.loads(receipt))
    _register_test_receipt(monkeypatch, noncanonical)
    with pytest.raises(LibraryEpochError, match="canonical JSON document"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=noncanonical,
            pack_files=pack_files,
        )

    duplicate = receipt.replace(
        b'{\n  "benchmark"',
        b'{\n  "format": "duplicate",\n  "benchmark"',
        1,
    )
    _register_test_receipt(monkeypatch, duplicate)
    with pytest.raises(LibraryEpochError, match="duplicate JSON key"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=duplicate,
            pack_files=pack_files,
        )

    extra_value = json.loads(receipt)
    extra_value["extra"] = True
    extra = canonical_document_bytes(extra_value)
    _register_test_receipt(monkeypatch, extra)
    with pytest.raises(LibraryEpochError, match="non-canonical fields"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=extra,
            pack_files=pack_files,
        )

    with pytest.raises(LibraryEpochError, match="must not consume"):
        validate_library_epoch(clean, independent_owner_receipt=receipt)


def test_frozen_pack_and_receipt_versions_reject_boolean_aliases(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean, frozen, receipt = _build_synthetic_frozen_fixture(
        candidate, pack_files, monkeypatch
    )

    pack_version = deepcopy(frozen)
    pack_version["pack"]["v"] = True
    pack_version = _reroot(pack_version)
    with pytest.raises(LibraryEpochError, match="version must be integer"):
        validate_library_epoch(
            pack_version,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )

    receipt_value = json.loads(receipt)
    receipt_value["v"] = True
    bool_receipt = canonical_document_bytes(receipt_value)
    _register_test_receipt(monkeypatch, bool_receipt)
    with pytest.raises(LibraryEpochError, match="version must be integer"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=bool_receipt,
            pack_files=pack_files,
        )


def test_receipt_bindings_and_frozen_commitment_cannot_be_forged(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    clean, frozen, receipt = _build_synthetic_frozen_fixture(
        candidate, pack_files, monkeypatch
    )
    bad_value = json.loads(receipt)
    bad_value["candidate_root_sha256"] = "0" * 64
    bad_receipt = canonical_document_bytes(bad_value)
    _register_test_receipt(monkeypatch, bad_receipt)
    with pytest.raises(LibraryEpochError, match="candidate candidate_root_sha256"):
        build_frozen_library_epoch(
            clean,
            independent_owner_receipt=bad_receipt,
            pack_files=pack_files,
        )

    _register_test_receipt(monkeypatch, receipt)
    forged = deepcopy(frozen)
    forged["independent_commitment"]["pack_root_sha256"] = "0" * 64
    forged = _reroot(forged)
    with pytest.raises(LibraryEpochError, match="reference is forged"):
        validate_library_epoch(
            forged,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )

    forged = deepcopy(frozen)
    forged["evaluation_eligible"] = True
    forged = _reroot(forged)
    with pytest.raises(LibraryEpochError, match="eligibility is forged"):
        validate_library_epoch(
            forged,
            independent_owner_receipt=receipt,
            pack_files=pack_files,
        )


def test_epoch_loader_rejects_duplicate_extra_and_noncanonical_json(
    candidate: dict[str, object], tmp_path: Path
) -> None:
    path = tmp_path / "candidate.json"
    path.write_bytes(canonical_document_bytes(candidate))
    assert load_library_epoch(path) == candidate

    path.write_bytes(canonical_json_bytes(candidate))
    with pytest.raises(LibraryEpochError, match="canonical JSON document"):
        load_library_epoch(path)

    raw = canonical_document_bytes(candidate)
    path.write_bytes(
        raw.replace(
            b'{\n  "benchmark"',
            b'{\n  "format": "duplicate",\n  "benchmark"',
            1,
        )
    )
    with pytest.raises(LibraryEpochError, match="duplicate JSON key"):
        load_library_epoch(path)

    extra = deepcopy(candidate)
    extra["classical"] = True
    path.write_bytes(canonical_document_bytes(extra))
    with pytest.raises(LibraryEpochError, match="non-canonical fields"):
        load_library_epoch(path)

    path.write_bytes(b"x" * (epoch_module.MAX_EPOCH_BYTES + 1))
    with pytest.raises(LibraryEpochError, match="exceeds the .*byte limit"):
        load_library_epoch(path)


def test_frozen_loader_is_pack_only_and_rejects_traversal(
    candidate: dict[str, object],
    pack_files: dict[str, bytes],
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    _clean, frozen, receipt = _build_synthetic_frozen_fixture(
        candidate, pack_files, monkeypatch, sealed=True
    )
    epoch_path = tmp_path / "frozen.json"
    receipt_path = tmp_path / "receipt.json"
    epoch_path.write_bytes(canonical_document_bytes(frozen))
    receipt_path.write_bytes(receipt)
    for path_text, raw in pack_files.items():
        path = tmp_path / path_text
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)

    with pytest.raises(LibraryEpochError, match="all supplied pack bytes"):
        load_library_epoch(
            epoch_path, independent_owner_receipt_path=receipt_path
        )
    with pytest.raises(LibraryEpochError, match="separate independent owner receipt"):
        load_library_epoch(epoch_path, pack_root=tmp_path)

    def fail_live(*_args, **_kwargs):
        raise AssertionError("frozen loader consulted living authoring state")

    monkeypatch.setattr(epoch_module, "library_epoch_schema", fail_live)
    monkeypatch.setattr(epoch_module, "_active_profile_epoch_identity", fail_live)
    monkeypatch.setattr(epoch_module, "live_tracked_catalog_identity", fail_live)
    monkeypatch.setattr(epoch_module, "h0_replay_identity", fail_live)
    monkeypatch.setattr(epoch_module, "_git_head_commit", fail_live)
    monkeypatch.setattr(epoch_module, "_git_relevant_dirty", fail_live)
    assert load_library_epoch(
        epoch_path,
        independent_owner_receipt_path=receipt_path,
        pack_root=tmp_path,
    ) == frozen

    catalog_path_text = next(
        row["path"] for row in frozen["pack"]["files"] if row["role"] == "catalog"
    )
    catalog_path = tmp_path / catalog_path_text
    catalog_raw = pack_files[catalog_path_text]
    symlink_target = tmp_path / "catalog-symlink-target.json"
    symlink_target.write_bytes(catalog_raw)
    catalog_path.unlink()
    catalog_path.symlink_to(symlink_target)
    with pytest.raises(LibraryEpochError, match="cannot read supplied epoch pack"):
        load_library_epoch(
            epoch_path,
            independent_owner_receipt_path=receipt_path,
            pack_root=tmp_path,
        )
    catalog_path.unlink()
    catalog_path.write_bytes(b"x" * (epoch_module.MAX_CATALOG_BYTES + 1))
    with pytest.raises(LibraryEpochError, match="exceeds the .*byte limit"):
        load_library_epoch(
            epoch_path,
            independent_owner_receipt_path=receipt_path,
            pack_root=tmp_path,
        )
    catalog_path.write_bytes(catalog_raw)

    traversal = deepcopy(frozen)
    traversal["pack"]["files"][0]["path"] = "pack/../escaped.json"
    traversal = _reroot(traversal)
    epoch_path.write_bytes(canonical_document_bytes(traversal))
    with pytest.raises(LibraryEpochError, match="safe repository path"):
        load_library_epoch(
            epoch_path,
            independent_owner_receipt_path=receipt_path,
            pack_root=tmp_path,
        )
