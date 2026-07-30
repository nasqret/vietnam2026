"""Tests for the model-free recovery publication filesystem preflight."""

from __future__ import annotations

import errno
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

import training.peano_policy.recovery as recovery  # noqa: E402
from training.peano_policy.recovery import (  # noqa: E402
    RECOVERY_PUBLICATION_PREFLIGHT_FORMAT,
    RecoverySnapshotError,
    run_recovery_publication_preflight,
    verify_recovery_publication_preflight,
)


def _canonical(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")


def _only_probe(root: Path) -> Path:
    probes = [path for path in root.iterdir() if path.name.startswith(".recovery-")]
    assert len(probes) == 1
    return probes[0]


def test_preflight_publishes_and_retains_canonical_protected_evidence(
    tmp_path: Path,
) -> None:
    root = tmp_path / "exact-filesystem"
    root.mkdir()
    report = tmp_path / "preflight.json"

    record = run_recovery_publication_preflight(root, report_path=report)
    assert record["format"] == RECOVERY_PUBLICATION_PREFLIGHT_FORMAT
    assert record["status"] == "passed"
    assert report.read_bytes() == _canonical(record)
    assert stat.S_IMODE(report.stat().st_mode) == 0o444
    assert verify_recovery_publication_preflight(report) == record

    publication = record["publication"]
    parent = Path(publication["probe_parent"]["path"])
    source = Path(publication["source"]["path"])
    destination = Path(publication["destination"]["path"])
    sentinel = Path(publication["sentinel"]["path"])
    assert parent == _only_probe(root)
    assert not source.exists()
    assert destination.is_dir()
    assert sentinel.is_file()
    assert stat.S_IMODE(parent.stat().st_mode) == 0o555
    assert stat.S_IMODE(destination.stat().st_mode) == 0o555
    assert stat.S_IMODE(sentinel.stat().st_mode) == 0o444
    assert bytes.fromhex(publication["sentinel"]["content_hex"]) == sentinel.read_bytes()
    assert publication["destination"]["before"]["device"] == destination.stat().st_dev
    assert publication["destination"]["before"]["inode"] == destination.stat().st_ino
    assert publication["sentinel"]["before"]["device"] == sentinel.stat().st_dev
    assert publication["sentinel"]["before"]["inode"] == sentinel.stat().st_ino
    assert all(publication["checks"].values())
    assert record["filesystem"]["same_device"] is True
    assert record["filesystem"]["statvfs"]["f_namemax"] > 0
    if sys.platform == "darwin":
        assert record["mechanism"]["syscall"] == "renamex_np"
    else:
        assert record["mechanism"]["syscall"] == "renameat2"


def test_existing_report_is_rejected_before_creating_a_probe(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "existing.json"
    report.write_bytes(b"prior authority\n")

    with pytest.raises(RecoverySnapshotError, match="refusing to replace"):
        run_recovery_publication_preflight(root, report_path=report)

    assert report.read_bytes() == b"prior authority\n"
    assert list(root.iterdir()) == []


def test_unique_parent_collision_never_reuses_or_modifies_a_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    collision = root / (".recovery-publication-preflight-" + "a" * 32)
    collision.mkdir()
    marker = collision / "prior-evidence"
    marker.write_bytes(b"preserve me")
    monkeypatch.setattr(recovery.secrets, "token_hex", lambda count: "a" * (count * 2))

    with pytest.raises(RecoverySnapshotError, match="could not allocate"):
        run_recovery_publication_preflight(
            root,
            report_path=tmp_path / "report.json",
        )

    assert marker.read_bytes() == b"preserve me"
    assert list(root.iterdir()) == [collision]


def test_destination_race_uses_no_replace_and_retains_both_evidence_trees(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "report.json"
    real_rename = recovery._rename_noreplace

    def race(source: Path, destination: Path) -> None:
        destination.mkdir()
        (destination / "prior-evidence").write_bytes(b"do not replace")
        real_rename(source, destination)

    monkeypatch.setattr(recovery, "_rename_noreplace", race)
    with pytest.raises(RecoverySnapshotError, match="evidence was retained"):
        run_recovery_publication_preflight(root, report_path=report)

    parent = _only_probe(root)
    source = parent / "source"
    destination = parent / "published"
    assert (destination / "prior-evidence").read_bytes() == b"do not replace"
    assert (source / "publication-sentinel.bin").is_file()
    assert stat.S_IMODE(source.stat().st_mode) == 0o555
    assert stat.S_IMODE((source / "publication-sentinel.bin").stat().st_mode) == 0o444
    assert not report.exists()


def test_unsupported_publication_leaves_protected_source_as_diagnostic_evidence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "report.json"

    def unsupported(source: Path, destination: Path) -> None:
        del source, destination
        raise OSError(errno.EOPNOTSUPP, "filesystem rejects rename no-replace")

    monkeypatch.setattr(recovery, "_rename_noreplace", unsupported)
    with pytest.raises(RecoverySnapshotError, match="evidence was retained"):
        run_recovery_publication_preflight(root, report_path=report)

    parent = _only_probe(root)
    source = parent / "source"
    assert (source / "publication-sentinel.bin").is_file()
    assert stat.S_IMODE(source.stat().st_mode) == 0o555
    assert not (parent / "published").exists()
    assert not report.exists()


def test_report_creation_race_preserves_prior_report_and_published_probe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "report.json"
    real_write = recovery._write_new_canonical_report

    def race(path: Path, value: object) -> None:
        path.write_bytes(b"prior report authority\n")
        real_write(path, value)

    monkeypatch.setattr(recovery, "_write_new_canonical_report", race)
    with pytest.raises(RecoverySnapshotError, match="refusing to replace"):
        run_recovery_publication_preflight(root, report_path=report)

    parent = _only_probe(root)
    assert report.read_bytes() == b"prior report authority\n"
    assert not (parent / "source").exists()
    assert (parent / "published" / "publication-sentinel.bin").is_file()
    assert stat.S_IMODE(parent.stat().st_mode) == 0o555


def test_verifier_rejects_noncanonical_report_and_live_sentinel_tampering(
    tmp_path: Path,
) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "report.json"
    record = run_recovery_publication_preflight(root, report_path=report)
    sentinel = Path(record["publication"]["sentinel"]["path"])

    report.chmod(0o644)
    report.write_bytes(report.read_bytes() + b" \n")
    report.chmod(0o444)
    with pytest.raises(RecoverySnapshotError, match="byte-canonical"):
        verify_recovery_publication_preflight(report)

    report.chmod(0o644)
    report.write_bytes(_canonical(record))
    report.chmod(0o444)
    sentinel.chmod(0o644)
    sentinel.write_bytes(b"changed")
    sentinel.chmod(0o444)
    with pytest.raises(RecoverySnapshotError, match="differs"):
        verify_recovery_publication_preflight(report)


def test_cli_runs_and_rechecks_the_retained_probe(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    report = tmp_path / "report.json"
    script = REPOSITORY_ROOT / "scripts/preflight_recovery_publication.py"

    run = subprocess.run(
        [
            sys.executable,
            str(script),
            "run",
            "--probe-root",
            str(root),
            "--report",
            str(report),
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert run.returncode == 0, run.stderr
    summary = json.loads(run.stdout)
    assert summary["status"] == "passed"
    assert summary["report"] == str(report)

    verify = subprocess.run(
        [sys.executable, str(script), "verify", "--report", str(report)],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert verify.returncode == 0, verify.stderr
    assert json.loads(verify.stdout) == summary

    rerun = subprocess.run(
        [
            sys.executable,
            str(script),
            "run",
            "--probe-root",
            str(root),
            "--report",
            str(report),
        ],
        cwd=REPOSITORY_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert rerun.returncode == 2
    assert "refusing to replace" in rerun.stderr
    assert len(list(root.iterdir())) == 1
