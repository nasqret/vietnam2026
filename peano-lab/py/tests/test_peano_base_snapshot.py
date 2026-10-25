"""Network-free closure tests for the pinned Hugging Face base snapshot."""

from __future__ import annotations

import json
import os
from pathlib import Path
import sys

import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import training.peano_policy.base_snapshot as base_snapshot
from training.peano_policy.manifest import sha256_json


MODEL_ID = "Example/Peano-Base"
REVISION = "e" * 40


def _snapshot_tree(tmp_path: Path, *, symlink: bool) -> tuple[Path, Path, Path]:
    hf_home = tmp_path / "hf"
    model_root = hf_home / "hub" / "models--Example--Peano-Base"
    blobs = model_root / "blobs"
    snapshot = model_root / "snapshots" / REVISION
    blobs.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    payload = b'{"model_type":"unit"}\n'
    visible = snapshot / "config.json"
    if symlink:
        blob = blobs / "unit-blob"
        blob.write_bytes(payload)
        visible.symlink_to(Path("../../blobs/unit-blob"))
    else:
        visible.write_bytes(payload)
    return hf_home, snapshot, visible


def _seal_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    hf_home: Path,
) -> dict[str, object]:
    record = base_snapshot.current_base_snapshot(
        model_id=MODEL_ID,
        revision=REVISION,
        hf_home=hf_home,
    )
    authority = tmp_path / "authority.json"
    authority.write_text(
        json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(base_snapshot, "EXPECTED_RECORD_PATH", authority)
    return record


@pytest.mark.parametrize("symlink", (False, True))
def test_exact_regular_or_relative_blob_snapshot_is_loader_visible_and_valid(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    symlink: bool,
) -> None:
    hf_home, snapshot, _visible = _snapshot_tree(tmp_path, symlink=symlink)
    expected = _seal_authority(monkeypatch, tmp_path, hf_home)

    assert base_snapshot.validate_base_snapshot(
        model_id=MODEL_ID,
        revision=REVISION,
        hf_home=hf_home,
    ) == expected
    path, identity = base_snapshot.validated_snapshot_path(
        model_id=MODEL_ID,
        revision=REVISION,
        hf_home=hf_home,
    )
    assert path == snapshot.resolve()
    assert identity == expected


def test_authority_binds_model_revision_size_hash_and_complete_file_set(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    hf_home, snapshot, visible = _snapshot_tree(tmp_path, symlink=False)
    _seal_authority(monkeypatch, tmp_path, hf_home)

    with pytest.raises(ValueError, match="no matching snapshot authority"):
        base_snapshot.validate_base_snapshot(
            model_id="Other/Model",
            revision=REVISION,
            hf_home=hf_home,
        )
    with pytest.raises(ValueError, match="no matching snapshot authority"):
        base_snapshot.validate_base_snapshot(
            model_id=MODEL_ID,
            revision="f" * 40,
            hf_home=hf_home,
        )

    visible.write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="differs from authority"):
        base_snapshot.validate_base_snapshot(
            model_id=MODEL_ID,
            revision=REVISION,
            hf_home=hf_home,
        )
    visible.write_bytes(b'{"model_type":"unit"}\n')
    (snapshot / "extra.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="differs from authority"):
        base_snapshot.validate_base_snapshot(
            model_id=MODEL_ID,
            revision=REVISION,
            hf_home=hf_home,
        )


def test_empty_or_nested_snapshot_entries_are_rejected(
    tmp_path: Path,
) -> None:
    hf_home, snapshot, visible = _snapshot_tree(tmp_path, symlink=False)
    visible.unlink()
    with pytest.raises(ValueError, match="snapshot is empty"):
        base_snapshot.current_base_snapshot(
            model_id=MODEL_ID,
            revision=REVISION,
            hf_home=hf_home,
        )

    (snapshot / "unexpected").mkdir()
    with pytest.raises(ValueError, match="unexpected directory"):
        base_snapshot.current_base_snapshot(
            model_id=MODEL_ID,
            revision=REVISION,
            hf_home=hf_home,
        )


@pytest.mark.parametrize("kind", ("broken", "absolute", "outside", "directory"))
def test_unsafe_or_broken_snapshot_links_are_rejected(
    tmp_path: Path,
    kind: str,
) -> None:
    hf_home, snapshot, visible = _snapshot_tree(tmp_path, symlink=True)
    visible.unlink()
    blobs = snapshot.parents[1] / "blobs"
    if kind == "broken":
        target = Path("../../blobs/missing")
    elif kind == "absolute":
        target = (blobs / "unit-blob").resolve()
    elif kind == "outside":
        outside = hf_home / "outside"
        outside.write_text("outside\n", encoding="utf-8")
        target = Path(os.path.relpath(outside, snapshot))
    else:
        target = Path("../../blobs")
    visible.symlink_to(target, target_is_directory=kind == "directory")

    with pytest.raises(ValueError):
        base_snapshot.current_base_snapshot(
            model_id=MODEL_ID,
            revision=REVISION,
            hf_home=hf_home,
        )


def test_special_snapshot_entry_and_empty_forged_authority_are_rejected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    hf_home, snapshot, visible = _snapshot_tree(tmp_path, symlink=False)
    visible.unlink()
    fifo = snapshot / "config.json"
    os.mkfifo(fifo)
    try:
        with pytest.raises(ValueError, match="not one plain regular file"):
            base_snapshot.current_base_snapshot(
                model_id=MODEL_ID,
                revision=REVISION,
                hf_home=hf_home,
            )
    finally:
        fifo.unlink()

    empty = {
        "algorithm": "sha256-json-v1(logical-path-to-size-and-sha256)",
        "file_count": 0,
        "files": {},
        "format": base_snapshot.RECORD_FORMAT,
        "model_id": MODEL_ID,
        "revision": REVISION,
        "sha256": sha256_json({}),
        "total_bytes": 0,
        "v": base_snapshot.RECORD_VERSION,
    }
    authority = tmp_path / "empty-authority.json"
    authority.write_text(json.dumps(empty), encoding="utf-8")
    monkeypatch.setattr(base_snapshot, "EXPECTED_RECORD_PATH", authority)
    with pytest.raises(ValueError, match="forged aggregate identity"):
        base_snapshot.expected_base_snapshot()


def test_authority_rejects_duplicate_json_keys(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    authority = tmp_path / "duplicate-authority.json"
    authority.write_text('{"format":"first","format":"second"}\n', encoding="utf-8")
    monkeypatch.setattr(base_snapshot, "EXPECTED_RECORD_PATH", authority)
    with pytest.raises(ValueError, match="duplicate JSON object key: format"):
        base_snapshot.expected_base_snapshot()
