"""Focused tests for immutable final-artifact publication primitives."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import stat
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import training.peano_policy.manifest as publication  # noqa: E402
import training.peano_policy.recovery as recovery  # noqa: E402
import training.peano_policy.corpus_seal as corpus_seal  # noqa: E402
from training.peano_policy.manifest import (  # noqa: E402
    PublicationError,
    publish_staged_directory_noreplace,
    write_manifest,
    write_manifest_noreplace,
)


def _canonical_pretty(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def test_all_authoritative_publishers_share_exact_profile_identifiers() -> None:
    assert (
        publication.NATIVE_PUBLICATION_PROFILE
        == recovery.NATIVE_PUBLICATION_PROFILE
        == corpus_seal.NATIVE_PUBLICATION_PROFILE
    )
    assert (
        publication.CLAIM_RENAME_PUBLICATION_PROFILE
        == recovery.CLAIM_RENAME_PUBLICATION_PROFILE
        == corpus_seal.CLAIM_RENAME_PUBLICATION_PROFILE
    )


def _staging(parent: Path, destination_name: str, suffix: str = "test") -> Path:
    path = parent / f".{destination_name}.partial-{suffix}"
    path.mkdir()
    return path


def _assert_exact_protected_tree(
    root: Path, *, expected_root_mode: int = 0o555
) -> None:
    for current, directories, files in os.walk(root, followlinks=False):
        current_path = Path(current)
        expected_mode = expected_root_mode if current_path == root else 0o555
        metadata = os.lstat(current_path)
        assert stat.S_ISDIR(metadata.st_mode)
        assert not stat.S_ISLNK(metadata.st_mode)
        assert stat.S_IMODE(metadata.st_mode) == expected_mode
        for name in directories:
            child = os.lstat(current_path / name)
            assert stat.S_ISDIR(child.st_mode)
            assert not stat.S_ISLNK(child.st_mode)
            assert stat.S_IMODE(child.st_mode) == 0o555
        for name in files:
            payload = os.lstat(current_path / name)
            assert stat.S_ISREG(payload.st_mode)
            assert not stat.S_ISLNK(payload.st_mode)
            assert payload.st_nlink == 1
            assert stat.S_IMODE(payload.st_mode) == 0o444


def test_new_manifest_is_canonical_atomic_and_flushes_file_and_parent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    record = {"z": [3, 2, 1], "a": "proof ✓"}
    destination = tmp_path / "training-manifest.json"
    flushed: list[str] = []
    real_fsync = publication.os.fsync
    real_rename = publication._atomic_rename_noreplace
    protected_at_install: list[tuple[int, int]] = []

    def observe_fsync(descriptor: int) -> None:
        mode = os.fstat(descriptor).st_mode
        flushed.append(
            "file" if stat.S_ISREG(mode) else "directory" if stat.S_ISDIR(mode) else "other"
        )
        real_fsync(descriptor)

    def observe_rename(source: Path, target: Path) -> None:
        metadata = os.lstat(source)
        assert stat.S_ISREG(metadata.st_mode)
        assert metadata.st_nlink == 1
        assert stat.S_IMODE(metadata.st_mode) == 0o444
        protected_at_install.append((metadata.st_dev, metadata.st_ino))
        real_rename(source, target)

    monkeypatch.setattr(publication.os, "fsync", observe_fsync)
    monkeypatch.setattr(publication, "_atomic_rename_noreplace", observe_rename)
    result = write_manifest_noreplace(destination, record)

    assert result == destination
    assert destination.read_bytes() == _canonical_pretty(record)
    assert protected_at_install == [
        (destination.stat().st_dev, destination.stat().st_ino)
    ]
    assert stat.S_IMODE(destination.stat().st_mode) == 0o444
    assert list(tmp_path.glob(".training-manifest.json.partial-*.tmp")) == []
    assert flushed.count("file") == 2
    assert flushed.count("directory") >= 2


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "fifo"])
def test_new_manifest_rejects_every_existing_target_without_touching_it(
    tmp_path: Path,
    kind: str,
) -> None:
    destination = tmp_path / "training-manifest.json"
    if kind == "file":
        destination.write_bytes(b"prior authority\n")
    elif kind == "directory":
        destination.mkdir()
        (destination / "prior").write_bytes(b"directory authority")
    elif kind == "symlink":
        prior = tmp_path / "prior.json"
        prior.write_bytes(b"symlink authority\n")
        destination.symlink_to(prior)
    else:
        os.mkfifo(destination)
    before = os.lstat(destination)

    with pytest.raises(FileExistsError, match="refusing to replace"):
        write_manifest_noreplace(destination, {"replacement": True})

    after = os.lstat(destination)
    assert (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode)) == (
        before.st_dev,
        before.st_ino,
        stat.S_IFMT(before.st_mode),
    )
    if kind == "file":
        assert destination.read_bytes() == b"prior authority\n"
    elif kind == "directory":
        assert (destination / "prior").read_bytes() == b"directory authority"
    elif kind == "symlink":
        assert destination.is_symlink()


def test_manifest_race_preserves_complete_partial_and_prior_authority(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "training-manifest.json"
    record = {"training_complete": True, "optimizer_steps": 650}
    real_rename = publication._atomic_rename_noreplace

    def race(source: Path, target: Path) -> None:
        target.write_bytes(b"prior race winner\n")
        real_rename(source, target)

    monkeypatch.setattr(publication, "_atomic_rename_noreplace", race)
    with pytest.raises(FileExistsError, match="refusing to replace"):
        write_manifest_noreplace(destination, record)

    assert destination.read_bytes() == b"prior race winner\n"
    partials = list(tmp_path.glob(".training-manifest.json.partial-*.tmp"))
    assert len(partials) == 1
    assert partials[0].read_bytes() == _canonical_pretty(record)
    assert stat.S_IMODE(partials[0].stat().st_mode) == 0o444


def test_manifest_rejects_symlink_parent_and_nonfinite_json(tmp_path: Path) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(PublicationError, match="symlink component"):
        write_manifest_noreplace(alias / "manifest.json", {"v": 1})
    with pytest.raises(PublicationError, match="strict JSON"):
        write_manifest_noreplace(real_parent / "manifest.json", {"loss": float("nan")})

    assert list(real_parent.iterdir()) == []


def test_legacy_manifest_writer_still_replaces_existing_manifest(tmp_path: Path) -> None:
    destination = tmp_path / "legacy.json"
    write_manifest(destination, {"version": 1})
    write_manifest(destination, {"version": 2})
    assert json.loads(destination.read_text(encoding="utf-8")) == {"version": 2}


def test_staged_directory_publication_is_atomic_sibling_install_and_flushes_tree(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name)
    adapter = staging / "adapter"
    adapter.mkdir()
    (adapter / "adapter_model.safetensors").write_bytes(b"safe weights")
    write_manifest_noreplace(
        staging / "training-manifest.json",
        {"training_complete": True},
    )
    staging_inode = staging.stat().st_ino
    flushed: list[str] = []
    real_fsync = publication.os.fsync
    real_protect = publication._protect_publication_tree
    real_rename = publication._atomic_rename_noreplace
    protected_before_install: list[bool] = []
    protected_at_install: list[bool] = []

    def observe_fsync(descriptor: int) -> None:
        mode = os.fstat(descriptor).st_mode
        flushed.append(
            "file" if stat.S_ISREG(mode) else "directory" if stat.S_ISDIR(mode) else "other"
        )
        real_fsync(descriptor)

    def observe_protect(root: Path, *, device: int) -> None:
        real_protect(root, device=device)
        _assert_exact_protected_tree(root)
        protected_before_install.append(True)

    def observe_rename(source: Path, target: Path) -> None:
        root_mode = 0o700 if sys.platform == "darwin" else 0o555
        _assert_exact_protected_tree(source, expected_root_mode=root_mode)
        protected_at_install.append(True)
        real_rename(source, target)

    monkeypatch.setattr(publication.os, "fsync", observe_fsync)
    monkeypatch.setattr(publication, "_protect_publication_tree", observe_protect)
    monkeypatch.setattr(publication, "_atomic_rename_noreplace", observe_rename)
    result = publish_staged_directory_noreplace(staging, destination)

    assert result == destination
    assert not staging.exists()
    assert destination.stat().st_ino == staging_inode
    assert protected_before_install == [True]
    assert protected_at_install == [True]
    _assert_exact_protected_tree(destination)
    assert (destination / "adapter" / "adapter_model.safetensors").read_bytes() == b"safe weights"
    assert json.loads(
        (destination / "training-manifest.json").read_text(encoding="utf-8")
    ) == {"training_complete": True}
    assert flushed.count("file") == 4
    assert flushed.count("directory") >= 4


@pytest.mark.parametrize("race_kind", ["mode", "type"])
def test_directory_publication_mode_or_type_race_fails_closed(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    race_kind: str,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name)
    adapter = staging / "adapter"
    adapter.mkdir()
    payload = adapter / "adapter_model.safetensors"
    payload.write_bytes(b"safe weights")
    real_rename = publication._atomic_rename_noreplace

    def race(source: Path, target: Path) -> None:
        source_adapter = source / "adapter"
        source_payload = source_adapter / "adapter_model.safetensors"
        if race_kind == "mode":
            os.chmod(source_payload, 0o644, follow_symlinks=False)
        else:
            os.chmod(source_adapter, 0o755, follow_symlinks=False)
            source_payload.unlink()
            source_payload.mkdir(mode=0o555)
            os.chmod(source_payload, 0o555, follow_symlinks=False)
            os.chmod(source_adapter, 0o555, follow_symlinks=False)
        real_rename(source, target)

    monkeypatch.setattr(publication, "_atomic_rename_noreplace", race)
    with pytest.raises(PublicationError, match="protected|differs"):
        publish_staged_directory_noreplace(staging, destination)

    assert not staging.exists()
    assert destination.is_dir()
    raced_payload = destination / "adapter" / "adapter_model.safetensors"
    if race_kind == "mode":
        assert raced_payload.is_file()
        assert stat.S_IMODE(raced_payload.stat().st_mode) == 0o644
    else:
        assert raced_payload.is_dir()


def test_directory_publication_race_retains_partial_and_existing_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name)
    (staging / "complete-payload").write_bytes(b"candidate")
    real_rename = publication._atomic_rename_noreplace

    def race(source: Path, target: Path) -> None:
        target.mkdir()
        (target / "prior-authority").write_bytes(b"winner")
        real_rename(source, target)

    monkeypatch.setattr(publication, "_atomic_rename_noreplace", race)
    with pytest.raises(FileExistsError, match="refusing to replace"):
        publish_staged_directory_noreplace(staging, destination)

    assert staging.is_dir()
    assert staging.name.startswith(f".{destination.name}.partial-")
    _assert_exact_protected_tree(staging)
    assert (staging / "complete-payload").read_bytes() == b"candidate"
    assert (destination / "prior-authority").read_bytes() == b"winner"


def test_postcommit_publication_error_is_not_masked_as_missing_staging(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name, suffix="postcommit")
    (staging / "payload").write_bytes(b"complete")
    staging_inode = staging.stat().st_ino
    real_publish = publication._atomic_rename_noreplace

    def commit_then_fail(source: Path, target: Path) -> None:
        real_publish(source, target)
        raise OSError(5, "simulated post-commit parent fsync failure")

    monkeypatch.setattr(
        publication,
        "_atomic_rename_noreplace",
        commit_then_fail,
    )
    with pytest.raises(OSError, match="simulated post-commit parent fsync failure"):
        publish_staged_directory_noreplace(staging, destination)

    assert not staging.exists()
    assert destination.stat().st_ino == staging_inode
    assert (destination / "payload").read_bytes() == b"complete"


@pytest.mark.parametrize("kind", ["directory", "file", "symlink", "fifo"])
def test_directory_publication_rejects_every_existing_destination(
    tmp_path: Path,
    kind: str,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name)
    (staging / "payload").write_bytes(b"candidate")
    if kind == "directory":
        destination.mkdir()
        (destination / "prior").write_bytes(b"directory authority")
    elif kind == "file":
        destination.write_bytes(b"file authority")
    elif kind == "symlink":
        prior = tmp_path / "prior"
        prior.mkdir()
        destination.symlink_to(prior, target_is_directory=True)
    else:
        os.mkfifo(destination)
    before = os.lstat(destination)

    with pytest.raises(FileExistsError, match="refusing to replace"):
        publish_staged_directory_noreplace(staging, destination)

    after = os.lstat(destination)
    assert staging.is_dir()
    assert (after.st_dev, after.st_ino, stat.S_IFMT(after.st_mode)) == (
        before.st_dev,
        before.st_ino,
        stat.S_IFMT(before.st_mode),
    )


def test_directory_publication_rejects_cross_parent_and_unsafe_source(
    tmp_path: Path,
) -> None:
    left = tmp_path / "left"
    right = tmp_path / "right"
    left.mkdir()
    right.mkdir()
    cross_parent = _staging(left, "trained-policy")
    (cross_parent / "payload").write_bytes(b"candidate")

    with pytest.raises(PublicationError, match="lexical siblings"):
        publish_staged_directory_noreplace(cross_parent, right / "trained-policy")
    assert cross_parent.is_dir()
    assert not (right / "trained-policy").exists()

    real_staging = _staging(tmp_path, "symlink-policy")
    alias = tmp_path / ".symlink-policy.partial-alias"
    alias.symlink_to(real_staging, target_is_directory=True)
    with pytest.raises(PublicationError, match="non-symlink directory"):
        publish_staged_directory_noreplace(alias, tmp_path / "symlink-policy")
    assert alias.is_symlink()
    assert real_staging.is_dir()

    wrong_name = tmp_path / "ordinary-staging"
    wrong_name.mkdir()
    with pytest.raises(PublicationError, match="staging name"):
        publish_staged_directory_noreplace(wrong_name, tmp_path / "another-policy")


@pytest.mark.parametrize("kind", ["symlink", "fifo"])
def test_directory_publication_rejects_unsafe_payload_nodes(
    tmp_path: Path,
    kind: str,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name)
    unsafe = staging / "unsafe-payload"
    if kind == "symlink":
        outside = tmp_path / "outside"
        outside.write_bytes(b"outside authority")
        unsafe.symlink_to(outside)
    else:
        os.mkfifo(unsafe)

    with pytest.raises(PublicationError, match="non-symlink regular file"):
        publish_staged_directory_noreplace(staging, destination)

    assert staging.is_dir()
    assert not destination.exists()


def test_directory_publication_rejects_symlinked_parent(tmp_path: Path) -> None:
    real_parent = tmp_path / "real"
    real_parent.mkdir()
    alias_parent = tmp_path / "alias"
    alias_parent.symlink_to(real_parent, target_is_directory=True)
    staging = _staging(real_parent, "trained-policy")

    with pytest.raises(PublicationError, match="symlink component"):
        publish_staged_directory_noreplace(
            alias_parent / staging.name,
            alias_parent / "trained-policy",
        )
    assert staging.is_dir()
    assert not (real_parent / "trained-policy").exists()


@pytest.mark.parametrize("node_kind", ["file", "directory"])
def test_atomic_no_replace_boundary_matches_recovery_semantics(
    tmp_path: Path,
    node_kind: str,
) -> None:
    """Keep the lower-layer copy aligned until recovery can import it."""

    implementations = (
        publication._atomic_rename_noreplace,
        recovery._rename_noreplace,
    )
    for index, rename_noreplace in enumerate(implementations):
        parent = tmp_path / f"implementation-{index}"
        parent.mkdir()
        source = parent / "source"
        destination = parent / "destination"
        if node_kind == "file":
            source.write_bytes(b"candidate")
        else:
            source.mkdir()
            (source / "payload").write_bytes(b"candidate")

        rename_noreplace(source, destination)
        assert not source.exists()
        assert destination.exists()

        losing_source = parent / "losing-source"
        if node_kind == "file":
            losing_source.write_bytes(b"loser")
        else:
            losing_source.mkdir()
            (losing_source / "payload").write_bytes(b"loser")
        with pytest.raises(FileExistsError, match="refusing to replace"):
            rename_noreplace(losing_source, destination)
        assert losing_source.exists()
        if node_kind == "file":
            assert destination.read_bytes() == b"candidate"
        else:
            assert (destination / "payload").read_bytes() == b"candidate"


def test_claim_profile_publishes_regular_file_and_directory_without_renegotiating(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(publication.sys, "platform", "linux")

    def forbidden_native(_source: Path, _destination: Path) -> None:
        raise AssertionError("a preflight-selected profile must not renegotiate")

    monkeypatch.setattr(
        publication,
        "_native_atomic_rename_noreplace",
        forbidden_native,
    )
    manifest = tmp_path / "manifest.json"
    write_manifest_noreplace(
        manifest,
        {"profile": "claim"},
        publication_profile=publication.CLAIM_RENAME_PUBLICATION_PROFILE,
    )
    assert json.loads(manifest.read_text(encoding="utf-8")) == {"profile": "claim"}
    assert manifest.stat().st_nlink == 1
    assert stat.S_IMODE(manifest.stat().st_mode) == 0o444

    # APFS refuses plain rename over an empty directory when the protected
    # source root is 0555.  The production fallback is Linux/Ceph-only; its
    # directory half is exercised by the Linux CI and live WMI preflight.
    if os.uname().sysname == "Darwin":
        return

    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name, suffix="claim")
    (staging / "payload").write_bytes(b"complete tree")
    staging_inode = staging.stat().st_ino
    publish_staged_directory_noreplace(
        staging,
        destination,
        publication_profile=publication.CLAIM_RENAME_PUBLICATION_PROFILE,
    )
    assert not staging.exists()
    assert destination.stat().st_ino == staging_inode
    assert (destination / "payload").read_bytes() == b"complete tree"
    _assert_exact_protected_tree(destination)


def test_selected_native_profile_fails_instead_of_falling_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.write_bytes(b"candidate")

    def unsupported(_source: Path, _destination: Path) -> None:
        raise OSError(22, "unsupported")

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(
        publication,
        "_native_atomic_rename_noreplace",
        unsupported,
    )
    with pytest.raises(OSError, match="unsupported"):
        publication._atomic_rename_noreplace(
            source,
            destination,
            publication_profile=publication.NATIVE_PUBLICATION_PROFILE,
        )
    assert source.read_bytes() == b"candidate"
    assert not destination.exists()


@pytest.mark.parametrize(
    "unsupported_errno",
    [errno.EINVAL, errno.EOPNOTSUPP, errno.ENOSYS],
)
def test_linux_native_unsupported_errno_selects_file_claim_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    unsupported_errno: int,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.write_bytes(b"candidate")

    def unsupported(_source: Path, _destination: Path) -> None:
        raise OSError(unsupported_errno, "native no-replace is unsupported")

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(
        publication,
        "_native_atomic_rename_noreplace",
        unsupported,
    )

    selected = publication._atomic_rename_noreplace(source, destination)

    assert selected == publication.CLAIM_RENAME_PUBLICATION_PROFILE
    assert not source.exists()
    assert destination.read_bytes() == b"candidate"


def test_linux_native_unrelated_error_never_falls_back(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.write_bytes(b"candidate")

    def fail(_source: Path, _destination: Path) -> None:
        raise OSError(errno.EIO, "simulated filesystem failure")

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(publication, "_native_atomic_rename_noreplace", fail)

    with pytest.raises(OSError, match="simulated filesystem failure"):
        publication._atomic_rename_noreplace(source, destination)

    assert source.read_bytes() == b"candidate"
    assert not destination.exists()


def test_linux_fallback_collision_preserves_external_winner(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    destination = tmp_path / "destination"
    source.write_bytes(b"candidate")

    def lose_native_race(_source: Path, target: Path) -> None:
        target.write_bytes(b"external winner")
        raise OSError(errno.EINVAL, "native no-replace is unsupported")

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(
        publication,
        "_native_atomic_rename_noreplace",
        lose_native_race,
    )

    with pytest.raises(FileExistsError, match="refusing to replace"):
        publication._atomic_rename_noreplace(source, destination)

    assert source.read_bytes() == b"candidate"
    assert destination.read_bytes() == b"external winner"


def test_file_claim_rename_failure_retains_stage_and_empty_claim(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "training-manifest.json"
    real_rename = publication.os.rename

    def fail_rename(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise OSError(5, "simulated claim commit failure")

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(publication.os, "rename", fail_rename)
    with pytest.raises(OSError, match="simulated claim commit failure"):
        write_manifest_noreplace(
            destination,
            {"training_complete": True},
            publication_profile=publication.CLAIM_RENAME_PUBLICATION_PROFILE,
        )
    monkeypatch.setattr(publication.os, "rename", real_rename)

    assert destination.is_file()
    assert destination.read_bytes() == b""
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    partials = list(tmp_path.glob(".training-manifest.json.partial-*.tmp"))
    assert len(partials) == 1
    assert json.loads(partials[0].read_text(encoding="utf-8")) == {
        "training_complete": True
    }
    assert stat.S_IMODE(partials[0].stat().st_mode) == 0o444


def test_nonempty_directory_claim_blocks_commit_and_retains_both_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    destination = tmp_path / "trained-policy"
    staging = _staging(tmp_path, destination.name, suffix="nonempty-claim")
    (staging / "payload").write_bytes(b"candidate")
    real_rename = publication.os.rename

    def populate_claim(
        source: str,
        target: str,
        *,
        src_dir_fd: int,
        dst_dir_fd: int,
    ) -> None:
        descriptor = os.open(
            f"{target}/intruder",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
            dir_fd=dst_dir_fd,
        )
        os.close(descriptor)
        real_rename(
            source,
            target,
            src_dir_fd=src_dir_fd,
            dst_dir_fd=dst_dir_fd,
        )

    monkeypatch.setattr(publication.sys, "platform", "linux")
    monkeypatch.setattr(publication.os, "rename", populate_claim)
    with pytest.raises(OSError):
        publish_staged_directory_noreplace(
            staging,
            destination,
            publication_profile=publication.CLAIM_RENAME_PUBLICATION_PROFILE,
        )

    assert staging.is_dir()
    _assert_exact_protected_tree(staging)
    assert destination.is_dir()
    assert (destination / "intruder").is_file()
