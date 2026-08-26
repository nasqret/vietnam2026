"""Adversarial tests for closed adapter/tokenizer artifact hashing."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import training.peano_policy.manifest as manifest  # noqa: E402
from training.peano_policy.manifest import (  # noqa: E402
    PublicationError,
    artifact_directory_hash,
    verify_artifact_directory,
)


def _artifact_tree(root: Path) -> Path:
    adapter = root / "adapter"
    nested = adapter / "metadata"
    nested.mkdir(parents=True)
    (adapter / "adapter_model.safetensors").write_bytes(b"safe weights\n")
    (nested / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    return adapter


def _protect_tree(root: Path) -> None:
    for current, directories, files in os.walk(root, topdown=False):
        current_path = Path(current)
        for name in files:
            os.chmod(current_path / name, 0o444, follow_symlinks=False)
        for name in directories:
            os.chmod(current_path / name, 0o555, follow_symlinks=False)
        os.chmod(current_path, 0o555, follow_symlinks=False)


def test_protected_mode_is_opt_in_for_legacy_but_exact_for_model_v3(
    tmp_path: Path,
) -> None:
    adapter = _artifact_tree(tmp_path)

    # Historical artifacts were commonly saved with owner-writable defaults.
    legacy = artifact_directory_hash(tmp_path, "adapter")
    assert verify_artifact_directory(tmp_path, legacy, "adapter") == adapter
    with pytest.raises(ValueError, match="not protected as 0(555|444)"):
        artifact_directory_hash(tmp_path, "adapter", require_protected=True)

    _protect_tree(adapter)
    protected = artifact_directory_hash(
        tmp_path,
        "adapter",
        require_protected=True,
    )
    assert (
        verify_artifact_directory(
            tmp_path,
            protected,
            "adapter",
            require_protected=True,
        )
        == adapter
    )

    payload = adapter / "adapter_model.safetensors"
    os.chmod(payload, 0o644, follow_symlinks=False)
    with pytest.raises(ValueError, match="not protected as 0444"):
        verify_artifact_directory(
            tmp_path,
            protected,
            "adapter",
            require_protected=True,
        )
    # The compatibility lane still authenticates legacy bytes without
    # retroactively imposing the model-v3 publication mode contract.
    assert verify_artifact_directory(tmp_path, protected, "adapter") == adapter


@pytest.mark.parametrize(
    "threat",
    ("file-symlink", "directory-symlink", "fifo"),
)
def test_closed_tree_rejects_symlinks_and_nonregular_payload_nodes(
    tmp_path: Path,
    threat: str,
) -> None:
    adapter = _artifact_tree(tmp_path)
    expected = artifact_directory_hash(tmp_path, "adapter")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "payload").write_bytes(b"outside\n")
    unsafe = adapter / "unsafe"

    if threat == "file-symlink":
        unsafe.symlink_to(outside / "payload")
    elif threat == "directory-symlink":
        unsafe.symlink_to(outside, target_is_directory=True)
    else:
        os.mkfifo(unsafe)

    with pytest.raises(ValueError, match="non-symlink (regular file|directory)"):
        artifact_directory_hash(tmp_path, "adapter")
    with pytest.raises(ValueError, match="non-symlink (regular file|directory)"):
        verify_artifact_directory(tmp_path, expected, "adapter")


def test_closed_tree_rejects_a_symlinked_directory_component(tmp_path: Path) -> None:
    real = tmp_path / "real"
    _artifact_tree(real)
    alias = tmp_path / "alias"
    alias.symlink_to(real, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink component"):
        artifact_directory_hash(alias, "adapter")


def test_closed_tree_rejects_duplicate_and_external_hard_links(tmp_path: Path) -> None:
    adapter = _artifact_tree(tmp_path)
    expected = artifact_directory_hash(tmp_path, "adapter")
    original = adapter / "adapter_model.safetensors"
    os.link(original, adapter / "weights-alias.safetensors")

    with pytest.raises(ValueError, match="hard-linked"):
        artifact_directory_hash(tmp_path, "adapter")
    with pytest.raises(ValueError, match="hard-linked"):
        verify_artifact_directory(tmp_path, expected, "adapter")


def test_descriptor_bound_hash_rejects_path_replacement_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _artifact_tree(tmp_path)
    target = adapter / "adapter_model.safetensors"
    displaced = adapter / "displaced.safetensors"
    real_read = manifest.os.read
    replaced = False

    def racing_read(descriptor: int, size: int) -> bytes:
        nonlocal replaced
        chunk = real_read(descriptor, size)
        if chunk and not replaced:
            replaced = True
            target.rename(displaced)
            target.write_bytes(b"replacement bytes\n")
        return chunk

    monkeypatch.setattr(manifest.os, "read", racing_read)
    with pytest.raises(ValueError, match="changed while hashed"):
        artifact_directory_hash(tmp_path, "adapter")
    assert replaced


def test_whole_tree_snapshot_rejects_new_entry_during_hash(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    adapter = _artifact_tree(tmp_path)
    expected = artifact_directory_hash(tmp_path, "adapter")
    real_hash = manifest._stable_artifact_file_sha256
    inserted = False

    def racing_hash(*args: object, **kwargs: object) -> str:
        nonlocal inserted
        digest = real_hash(*args, **kwargs)
        if not inserted:
            inserted = True
            (adapter / "late.json").write_text("{}\n", encoding="utf-8")
        return digest

    monkeypatch.setattr(manifest, "_stable_artifact_file_sha256", racing_hash)
    with pytest.raises(ValueError, match="directory changed while hashed"):
        verify_artifact_directory(tmp_path, expected, "adapter")
    assert inserted


def test_artifact_manifest_entries_must_be_canonical_and_digest_shaped(
    tmp_path: Path,
) -> None:
    _artifact_tree(tmp_path)
    expected = artifact_directory_hash(tmp_path, "adapter")

    escaped = dict(expected)
    escaped["files"] = {"tokenizer/foreign.json": "a" * 64}
    with pytest.raises(ValueError, match="escapes its loader directory"):
        verify_artifact_directory(tmp_path, escaped, "adapter")

    malformed = dict(expected)
    malformed["sha256"] = "not-a-sha256"
    with pytest.raises(ValueError, match="malformed"):
        verify_artifact_directory(tmp_path, malformed, "adapter")


@pytest.mark.parametrize("kind", (stat.S_IFSOCK, stat.S_IFCHR, stat.S_IFBLK))
def test_special_node_gate_rejects_socket_and_device_modes_without_mknod(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    kind: int,
) -> None:
    # Sandboxed/non-root test processes cannot portably create device nodes or
    # filesystem sockets.  Feed their real mode bits through the exact lstat
    # gate used by artifact enumeration instead.
    metadata = os.stat_result((kind | 0o600, 1, 1, 1, 0, 0, 0, 0, 0, 0))
    monkeypatch.setattr(manifest.os, "lstat", lambda _path: metadata)
    with pytest.raises(PublicationError, match="non-symlink regular file"):
        manifest._regular_publication_file(
            tmp_path / "special-node",
            label="artifact payload",
        )
