"""Focused soundness tests for immutable model-v3 corpus publication."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import sys
from types import SimpleNamespace
from typing import Any

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy import corpus_seal  # noqa: E402


SCRIPT = REPOSITORY_ROOT / "scripts" / "seal_peano_v3_corpus.py"
COMMIT = "a" * 40
JOB_ID = "172729"
MODEL_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"


def _canonical(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _digest_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _digest_json(value: object) -> str:
    return _digest_bytes(_canonical(value).encode("utf-8"))


def _digest_file(path: Path) -> str:
    return _digest_bytes(path.read_bytes())


def _write_json(path: Path, value: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical(value) + "\n", encoding="utf-8")
    return path


def _write_jsonl(path: Path, label: str) -> Path:
    return _write_json(path, {"fixture": label})


def _artifact(path: Path) -> dict[str, object]:
    return {
        "path": path.name,
        "bytes": path.stat().st_size,
        "sha256": _digest_file(path),
    }


def _dataset_digest(data: Path) -> str:
    digest = hashlib.sha256()
    for split in ("train", "val", "test"):
        digest.update(split.encode("ascii") + b"\0")
        digest.update((data / f"{split}.jsonl").read_bytes())
    return digest.hexdigest()


def _fixture_bundle(tmp_path: Path, *, job_id: str = JOB_ID) -> dict[str, Path | str]:
    data = tmp_path / "data" / "peano-policy-v3"
    logs = tmp_path / "logs"
    data.mkdir(parents=True)
    logs.mkdir()

    jsonl_names = [name for name in corpus_seal.DATA_FILES if name.endswith(".jsonl")]
    for name in jsonl_names:
        _write_jsonl(data / name, name)

    _write_json(
        data / "balanced-source-manifest.json",
        {
            "format": "peano-policy-corpus",
            "version": 1,
            "profile": "model-v3",
            "authority_schedule": {
                "method": "full-synthetic-v1",
                "library_prefix_length": 247,
                "library_size": 247,
            },
            "artifacts": {
                "trace": _artifact(data / "balanced-raw-traces.jsonl"),
                "metadata": _artifact(data / "balanced-session-metadata.jsonl"),
            },
        },
    )
    _write_json(
        data / "library-source-manifest.json",
        {
            "format": "peano-library-policy-corpus",
            "version": 1,
            "library": {"size": 247},
            "artifacts": {
                "trace": _artifact(data / "library-raw-traces.jsonl"),
                "metadata": _artifact(data / "library-session-metadata.jsonl"),
            },
        },
    )
    _write_json(
        data / "combined-metadata-manifest.json",
        {
            "format": "peano-v3-combined-corpus-metadata",
            "version": 1,
            "inputs": {
                "library_metadata": _artifact(data / "library-session-metadata.jsonl"),
                "synthetic_metadata": _artifact(data / "balanced-session-metadata.jsonl"),
            },
            "artifact": {"metadata": _artifact(data / "session-metadata.jsonl")},
        },
    )

    split_records = {
        split: {
            "rows": 1,
            "sha256": _digest_file(data / f"{split}.jsonl"),
        }
        for split in ("train", "val", "test")
    }
    dataset_sha = _dataset_digest(data)
    _write_json(
        data / "manifest.json",
        {
            "format": "peano-lab-next-tactic",
            "version": 1,
            "source": {
                "traces": [
                    {
                        "path": str(data / "library-raw-traces.jsonl"),
                        "sha256": _digest_file(data / "library-raw-traces.jsonl"),
                    },
                    {
                        "path": str(data / "balanced-raw-traces.jsonl"),
                        "sha256": _digest_file(data / "balanced-raw-traces.jsonl"),
                    },
                ],
                "metadata": {
                    "path": str(data / "session-metadata.jsonl"),
                    "sha256": _digest_file(data / "session-metadata.jsonl"),
                    "records": 1,
                },
            },
            "splits": split_records,
            "dataset_sha256": dataset_sha,
        },
    )

    attestation_path = logs / f"peano-wmi-v3-dataset-attestation-{job_id}.json"
    _write_json(
        attestation_path,
        {
            "format": "peano-policy-dataset-attestation",
            "v": 2,
            "manifest_sha256": _digest_file(data / "manifest.json"),
            "prompt_version": 3,
            "library_snapshot_sha256": "1" * 64,
            "prompt_contract_sha256": "2" * 64,
            "held_out_contract_sha256": "3" * 64,
            "training_environments_sha256": "4" * 64,
            "held_out_contamination": 0,
            "independent_replay": True,
            "source_artifacts": {
                "traces": [
                    _digest_file(data / "library-raw-traces.jsonl"),
                    _digest_file(data / "balanced-raw-traces.jsonl"),
                ],
                "metadata": _digest_file(data / "session-metadata.jsonl"),
            },
            "splits": split_records,
            "dataset_sha256": dataset_sha,
            "authority_schedule": {
                "method": "catalog-predecessor-prefix-v1+full-synthetic-v1",
                "full_library_sha256": "1" * 64,
                "library_size": 247,
                "training_prefixes": list(range(248)),
                "inference_prefix": 247,
            },
        },
    )

    audit_path = logs / f"peano-wmi-v3-token-audit-{job_id}.json"
    _write_json(
        audit_path,
        {
            "format": "peano-policy-token-audit",
            "v": 1,
            "status": "passed",
            "config": {
                "path": "training/peano_policy/configs/qwen3_1_7b_v3_library.toml",
                "sha256": "5" * 64,
                "max_length": 32768,
            },
            "tokenizer": {
                "model_id": "Qwen/Qwen3-1.7B-Base",
                "requested_revision": MODEL_REVISION,
                "resolved_revision": MODEL_REVISION,
            },
            "inputs": {
                "train": {
                    "path": "data/peano-policy-v3/train.jsonl",
                    "sha256": _digest_file(data / "train.jsonl"),
                },
                "eval": {
                    "path": "data/peano-policy-v3/val.jsonl",
                    "sha256": _digest_file(data / "val.jsonl"),
                },
            },
            "splits": {
                "train": {
                    "rows": 1,
                    "maximum": 100,
                    "budget": 32768,
                    "headroom": 32668,
                },
                "eval": {
                    "rows": 1,
                    "maximum": 90,
                    "budget": 32768,
                    "headroom": 32678,
                },
            },
        },
    )

    submission = {
        "timestamp": "2026-07-30T00:00:00Z",
        "job_id": job_id,
        "script": "slurm/peano_wmi_prepare_v3_training.sbatch",
        "dependency_job_id": "",
        "workdir": "/work/bnaskrecki/peano-lab-training",
        "git_commit": COMMIT,
        "git_dirty": "false",
        "sync_timestamp": "2026-07-29T23:59:00Z",
        "script_sha256": "6" * 64,
    }
    smoke_path = logs / f"peano-wmi-v3-prepare-runtime-{job_id}.json"
    _write_json(
        smoke_path,
        {
            "format": "peano-policy-wmi-a100-v3-smoke",
            "v": 1,
            "status": "passed",
            "model": {
                "id": "Qwen/Qwen3-1.7B-Base",
                "requested_revision": MODEL_REVISION,
                "model_commit": MODEL_REVISION,
                "tokenizer_commit": MODEL_REVISION,
            },
            "job": {
                "scheduler": "slurm",
                "job_id": job_id,
                "deployment": {
                    "source_sync": {
                        "status": "synced",
                        "path": ".peano-source-provenance.tsv",
                        "sha256": "7" * 64,
                        "git_commit": COMMIT,
                        "git_dirty": False,
                        "synced_at": "2026-07-29T23:59:00Z",
                    },
                    "job_script": {
                        "status": "declared",
                        "path": "slurm/peano_wmi_prepare_v3_training.sbatch",
                        "sha256": "6" * 64,
                    },
                },
                "submission": submission,
                "ledger": {
                    "path": "logs/submissions.tsv",
                    "row_sha256": _digest_json(submission),
                },
            },
        },
    )
    return {
        "artifact_dir": data,
        "dataset_attestation": attestation_path,
        "token_audit": audit_path,
        "runtime_smoke": smoke_path,
        "destination": tmp_path / "sealed-corpus",
        "source_commit": COMMIT,
        "prepare_job_id": job_id,
    }


def _seal(bundle: dict[str, Path | str]) -> dict[str, object]:
    return corpus_seal.seal_corpus(
        bundle["artifact_dir"],
        bundle["dataset_attestation"],
        bundle["token_audit"],
        bundle["runtime_smoke"],
        bundle["destination"],
        source_commit=str(bundle["source_commit"]),
        prepare_job_id=str(bundle["prepare_job_id"]),
    )


def _hash_anchors(
    bundle: dict[str, Path | str],
) -> tuple[str, dict[str, str], dict[str, str]]:
    data = bundle["artifact_dir"]
    assert isinstance(data, Path)
    data_hashes = {
        name: _digest_file(data / name) for name in corpus_seal.DATA_FILES
    }
    report_hashes = {
        role: _digest_file(bundle[role])  # type: ignore[arg-type]
        for role in corpus_seal.REPORT_FILES
    }
    return data_hashes["manifest.json"], data_hashes, report_hashes


def _anchored_seal(bundle: dict[str, Path | str]) -> dict[str, object]:
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    return corpus_seal.seal_corpus(
        bundle["artifact_dir"],
        bundle["dataset_attestation"],
        bundle["token_audit"],
        bundle["runtime_smoke"],
        bundle["destination"],
        source_commit=str(bundle["source_commit"]),
        prepare_job_id=str(bundle["prepare_job_id"]),
        dataset_manifest_sha256=manifest_sha256,
        data_sha256s=data_sha256s,
        report_sha256s=report_sha256s,
    )


def _unlock_tree(root: Path) -> None:
    if not root.exists():
        return
    for current, directories, files in os.walk(root, topdown=False, followlinks=False):
        for name in files:
            os.chmod(Path(current) / name, 0o600, follow_symlinks=False)
        for name in directories:
            os.chmod(Path(current) / name, 0o700, follow_symlinks=False)
    os.chmod(root, 0o700, follow_symlinks=False)


def _retained_seal_stage(parent: Path) -> Path:
    stages = list(parent.glob(".sealed-corpus.staging-*"))
    assert len(stages) == 1
    return stages[0]


def _load_script():
    specification = importlib.util.spec_from_file_location("_test_peano_v3_seal_cli", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def test_create_is_canonical_protected_and_independently_verifiable(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    try:
        manifest = _seal(bundle)
        assert manifest["format"] == "peano-policy-v3-corpus-seal"
        assert manifest["source"]["prepare_job_id"] == JOB_ID
        assert manifest["source"]["git_commit"] == COMMIT
        assert len(manifest["files"]) == 15
        assert (destination / "seal.json").read_bytes() == (
            _canonical(manifest) + "\n"
        ).encode("utf-8")
        assert corpus_seal.verify_seal(
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
        ) == manifest
        for path in destination.rglob("*"):
            assert path.stat().st_mode & stat.S_IWUSR == 0
    finally:
        _unlock_tree(destination)


@pytest.mark.parametrize("mutation", ("missing", "unexpected", "symlink", "directory"))
def test_rejects_nonclosed_or_nonregular_artifact_directory(
    tmp_path: Path, mutation: str
) -> None:
    bundle = _fixture_bundle(tmp_path)
    data = bundle["artifact_dir"]
    destination = bundle["destination"]
    assert isinstance(data, Path) and isinstance(destination, Path)
    target = data / "test.jsonl"
    if mutation == "missing":
        target.unlink()
    elif mutation == "unexpected":
        (data / "notes.txt").write_text("not part of the corpus\n", encoding="utf-8")
    elif mutation == "symlink":
        target.unlink()
        target.symlink_to(data / "train.jsonl")
    else:
        target.unlink()
        target.mkdir()

    with pytest.raises(corpus_seal.CorpusSealError):
        _seal(bundle)
    assert not destination.exists()


@pytest.mark.parametrize(
    ("name", "contents", "message"),
    (
        ("balanced-source-manifest.json", '{"format":"a","format":"b"}\n', "duplicate JSON key"),
        ("library-source-manifest.json", '{"value":NaN}\n', "non-finite JSON number"),
        ("session-metadata.jsonl", '{}', "missing newline"),
        ("train.jsonl", "\n", "blank JSONL"),
    ),
)
def test_all_json_and_jsonl_are_strictly_loaded(
    tmp_path: Path, name: str, contents: str, message: str
) -> None:
    bundle = _fixture_bundle(tmp_path)
    data = bundle["artifact_dir"]
    destination = bundle["destination"]
    assert isinstance(data, Path) and isinstance(destination, Path)
    (data / name).write_text(contents, encoding="utf-8")
    with pytest.raises(corpus_seal.CorpusSealError, match=message):
        _seal(bundle)
    assert not destination.exists()


def test_rejects_symlinked_report(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    report = bundle["token_audit"]
    destination = bundle["destination"]
    assert isinstance(report, Path) and isinstance(destination, Path)
    contents = report.read_bytes()
    report.unlink()
    replacement = report.with_name("replacement.json")
    replacement.write_bytes(contents)
    report.symlink_to(replacement)
    with pytest.raises(corpus_seal.CorpusSealError, match="symlink"):
        _seal(bundle)
    assert not destination.exists()


def test_copy_rechecks_source_mode_and_link_count_at_final_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source.jsonl"
    target = tmp_path / "target.jsonl"
    source.write_text('{"proof":"checked"}\n', encoding="utf-8")
    original_lstat = corpus_seal.os.lstat
    source_inspections = 0

    def add_link_after_open(path: os.PathLike[str] | str) -> os.stat_result:
        nonlocal source_inspections
        measured = original_lstat(path)
        if Path(path) != source:
            return measured
        source_inspections += 1
        if source_inspections == 1:
            return measured
        return SimpleNamespace(
            st_dev=measured.st_dev,
            st_ino=measured.st_ino,
            st_mode=measured.st_mode,
            st_nlink=2,
            st_size=measured.st_size,
            st_mtime_ns=measured.st_mtime_ns,
            st_ctime_ns=measured.st_ctime_ns,
        )  # type: ignore[return-value]

    monkeypatch.setattr(corpus_seal.os, "lstat", add_link_after_open)
    with pytest.raises(
        corpus_seal.CorpusSealError,
        match="source changed while it was copied",
    ):
        corpus_seal._copy_regular_file(source, target, "copy-race fixture")
    assert source_inspections == 2


@pytest.mark.parametrize("role", ("artifact", "report"))
def test_rejects_external_hard_links_before_publication(
    tmp_path: Path,
    role: str,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    if role == "artifact":
        target = bundle["artifact_dir"] / "train.jsonl"  # type: ignore[operator]
    else:
        target = bundle["token_audit"]
    assert isinstance(target, Path)
    os.link(target, tmp_path / f"external-{role}-alias")
    with pytest.raises(corpus_seal.CorpusSealError, match="single-link"):
        _seal(bundle)
    assert not destination.exists()


def test_rejects_cross_report_hash_or_runtime_identity(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    audit_path = bundle["token_audit"]
    destination = bundle["destination"]
    assert isinstance(audit_path, Path) and isinstance(destination, Path)
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["inputs"]["train"]["sha256"] = "f" * 64
    _write_json(audit_path, audit)
    with pytest.raises(corpus_seal.CorpusSealError, match="differs from sealed data"):
        _seal(bundle)
    assert not destination.exists()

    bundle = _fixture_bundle(tmp_path / "wrong-source")
    smoke_path = bundle["runtime_smoke"]
    destination = bundle["destination"]
    assert isinstance(smoke_path, Path) and isinstance(destination, Path)
    smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    smoke["job"]["deployment"]["source_sync"]["git_commit"] = "b" * 40
    _write_json(smoke_path, smoke)
    with pytest.raises(corpus_seal.CorpusSealError, match="expected clean source"):
        _seal(bundle)
    assert not destination.exists()


def test_never_overwrites_an_existing_destination(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    destination.write_text("keep me\n", encoding="utf-8")
    with pytest.raises(FileExistsError, match="refusing to replace"):
        _seal(bundle)
    assert destination.read_text(encoding="utf-8") == "keep me\n"
    assert not list(tmp_path.glob(".sealed-corpus.staging-*"))


def test_publication_failure_retains_staging_without_masking_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)

    def fail_rename(source: Path, target: Path) -> None:
        raise OSError("simulated no-replace publication failure")

    monkeypatch.setattr(corpus_seal, "_rename_noreplace", fail_rename)
    with pytest.raises(OSError, match="simulated"):
        _seal(bundle)
    assert not destination.exists()
    stage = _retained_seal_stage(tmp_path)
    try:
        assert (stage / "seal.json").is_file()
        assert stat.S_IMODE((stage / "seal.json").stat().st_mode) == 0o444
    finally:
        _unlock_tree(stage)


def test_linux_publication_keeps_staging_root_read_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    observed_mode = None

    def inspect_then_fail(source: Path, target: Path) -> None:
        nonlocal observed_mode
        observed_mode = stat.S_IMODE(source.stat().st_mode)
        raise OSError("stop after permission inspection")

    monkeypatch.setattr(corpus_seal.sys, "platform", "linux")
    monkeypatch.setattr(corpus_seal, "_rename_noreplace", inspect_then_fail)
    with pytest.raises(OSError, match="permission inspection"):
        _seal(bundle)
    assert observed_mode is not None
    assert observed_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH) == 0
    assert not destination.exists()
    stage = _retained_seal_stage(tmp_path)
    try:
        assert stat.S_IMODE(stage.stat().st_mode) == 0o555
    finally:
        _unlock_tree(stage)


def test_final_protected_modes_are_fsynced_before_linux_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    events: list[str] = []
    original_protect = corpus_seal._protect_tree
    original_fsync = corpus_seal._fsync_protected_tree

    def protect(root: Path) -> None:
        original_protect(root)
        events.append("protect")

    def fsync_protected(root: Path) -> None:
        assert stat.S_IMODE(root.stat().st_mode) == 0o555
        assert stat.S_IMODE((root / "data").stat().st_mode) == 0o555
        assert stat.S_IMODE((root / "reports").stat().st_mode) == 0o555
        assert stat.S_IMODE((root / "seal.json").stat().st_mode) == 0o444
        assert all(
            stat.S_IMODE(path.stat().st_mode) == 0o444
            for directory in (root / "data", root / "reports")
            for path in directory.iterdir()
        )
        original_fsync(root)
        events.append("fsync-protected")

    def stop_at_rename(_source: Path, _target: Path) -> None:
        events.append("rename")
        raise OSError("stop after durable-mode inspection")

    monkeypatch.setattr(corpus_seal.sys, "platform", "linux")
    monkeypatch.setattr(corpus_seal, "_protect_tree", protect)
    monkeypatch.setattr(corpus_seal, "_fsync_protected_tree", fsync_protected)
    monkeypatch.setattr(corpus_seal, "_rename_noreplace", stop_at_rename)
    with pytest.raises(OSError, match="durable-mode inspection"):
        _seal(bundle)
    assert events == ["protect", "fsync-protected", "rename"]
    assert not destination.exists()
    stage = _retained_seal_stage(tmp_path)
    try:
        assert stat.S_IMODE(stage.stat().st_mode) == 0o555
    finally:
        _unlock_tree(stage)


def test_protected_tree_fsync_failure_prevents_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    rename_called = False

    def fail_fsync(_root: Path) -> None:
        raise OSError("simulated protected-tree fsync failure")

    def observe_rename(_source: Path, _target: Path) -> None:
        nonlocal rename_called
        rename_called = True

    monkeypatch.setattr(corpus_seal, "_fsync_protected_tree", fail_fsync)
    monkeypatch.setattr(corpus_seal, "_rename_noreplace", observe_rename)
    with pytest.raises(OSError, match="protected-tree fsync failure"):
        _seal(bundle)
    assert rename_called is False
    assert not destination.exists()
    stage = _retained_seal_stage(tmp_path)
    try:
        assert stat.S_IMODE(stage.stat().st_mode) == 0o555
    finally:
        _unlock_tree(stage)


def test_darwin_reprotected_root_is_fsynced_before_parent_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    original_fsync_directory = corpus_seal._fsync_directory
    post_rename_syncs: list[tuple[Path, int]] = []

    def rename(source: Path, target: Path) -> None:
        source.rename(target)

    def fsync_directory(path: Path) -> None:
        if destination.exists():
            post_rename_syncs.append((path, stat.S_IMODE(path.stat().st_mode)))
        original_fsync_directory(path)

    monkeypatch.setattr(corpus_seal.sys, "platform", "darwin")
    monkeypatch.setattr(corpus_seal, "_rename_noreplace", rename)
    monkeypatch.setattr(corpus_seal, "_fsync_directory", fsync_directory)
    try:
        _seal(bundle)
        assert post_rename_syncs[-2:] == [
            (destination, 0o555),
            (destination.parent, stat.S_IMODE(destination.parent.stat().st_mode)),
        ]
    finally:
        _unlock_tree(destination)


@pytest.mark.parametrize("mutation", ("content", "extra", "symlink", "noncanonical"))
def test_verifier_rejects_every_sealed_tree_mutation(tmp_path: Path, mutation: str) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    _seal(bundle)
    try:
        if mutation == "content":
            target = destination / "data" / "test.jsonl"
            os.chmod(target, 0o600)
            target.write_text('{"fixture":"changed"}\n', encoding="utf-8")
        elif mutation == "extra":
            os.chmod(destination, 0o700)
            (destination / "extra.txt").write_text("extra\n", encoding="utf-8")
        elif mutation == "symlink":
            directory = destination / "reports"
            target = directory / "token-audit.json"
            os.chmod(directory, 0o700)
            os.chmod(target, 0o600)
            target.unlink()
            target.symlink_to(directory / "dataset-attestation.json")
        else:
            target = destination / "seal.json"
            os.chmod(target, 0o600)
            value = json.loads(target.read_text(encoding="utf-8"))
            target.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
        with pytest.raises(corpus_seal.CorpusSealError):
            corpus_seal.verify_seal(destination)
    finally:
        _unlock_tree(destination)


def test_verifier_accepts_external_trust_anchors_only_on_exact_match(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    try:
        _seal(bundle)
        with pytest.raises(corpus_seal.CorpusSealError, match="different source commit"):
            corpus_seal.verify_seal(destination, source_commit="b" * 40)
        with pytest.raises(corpus_seal.CorpusSealError, match="different preparation job"):
            corpus_seal.verify_seal(destination, prepare_job_id="172730")
    finally:
        _unlock_tree(destination)


@pytest.mark.parametrize(
    "relative",
    ("seal.json", "data/train.jsonl", "reports/token-audit.json"),
)
def test_verifier_rejects_external_hard_links(
    tmp_path: Path,
    relative: str,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    _seal(bundle)
    alias = tmp_path / (Path(relative).name + ".external-alias")
    try:
        os.link(destination / relative, alias)
        with pytest.raises(corpus_seal.CorpusSealError, match="single-link"):
            corpus_seal.verify_seal(destination)
    finally:
        alias.unlink(missing_ok=True)
        _unlock_tree(destination)


def test_external_hash_anchors_cover_all_data_and_reports(tmp_path: Path) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    try:
        manifest = _anchored_seal(bundle)
        assert corpus_seal.verify_seal(
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
            dataset_manifest_sha256=manifest_sha256,
            data_sha256s=data_sha256s,
            report_sha256s=report_sha256s,
        ) == manifest
        wrong = dict(data_sha256s)
        wrong["balanced-source-manifest.json"] = "f" * 64
        with pytest.raises(corpus_seal.CorpusSealError, match="external SHA-256"):
            corpus_seal.verify_seal(
                destination,
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=wrong,
                report_sha256s=report_sha256s,
            )
    finally:
        _unlock_tree(destination)


def test_report_publication_recovers_crash_window_and_reuses_only_same_job(
    tmp_path: Path,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    try:
        _anchored_seal(bundle)
        assert not report.exists()  # simulated crash after seal publication
        first = corpus_seal.publish_seal_report(
            report,
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
            publisher_job_id="99",
            dataset_manifest_sha256=manifest_sha256,
            data_sha256s=data_sha256s,
            report_sha256s=report_sha256s,
        )
        assert first["publisher"] == {"scheduler": "slurm", "job_id": "99"}
        before = (report.stat().st_dev, report.stat().st_ino, report.read_bytes())
        second = corpus_seal.publish_seal_report(
            report,
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
            publisher_job_id="99",
            dataset_manifest_sha256=manifest_sha256,
            data_sha256s=data_sha256s,
            report_sha256s=report_sha256s,
        )
        assert second == first
        assert (report.stat().st_dev, report.stat().st_ino, report.read_bytes()) == before
        with pytest.raises(corpus_seal.CorpusSealError, match="publisher job"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="100",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=data_sha256s,
                report_sha256s=report_sha256s,
            )
    finally:
        if report.exists():
            os.chmod(report, 0o600)
        _unlock_tree(destination)


def test_report_publication_failure_retains_its_stage_without_masking_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)

    def fail_rename(_source: Path, _destination: Path) -> None:
        raise OSError("simulated report rename failure")

    monkeypatch.setattr(corpus_seal, "_rename_noreplace", fail_rename)
    try:
        with pytest.raises(OSError, match="simulated report rename failure"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=data_sha256s,
                report_sha256s=report_sha256s,
            )
        assert not report.exists()
        stages = list(report.parent.glob(f".{report.name}.staging-*"))
        assert len(stages) == 1
        assert stat.S_IMODE(stages[0].stat().st_mode) == 0o444
        staged = json.loads(stages[0].read_text(encoding="utf-8"))
        assert staged["publisher"] == {"scheduler": "slurm", "job_id": "99"}
    finally:
        _unlock_tree(destination)


def test_report_failure_never_deletes_a_replacement_at_its_stage_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)
    replacement = b"foreign replacement\n"

    def replace_then_fail(source: Path, _destination: Path) -> None:
        os.chmod(source, 0o600)
        source.unlink()
        source.write_bytes(replacement)
        raise OSError("simulated replacement race")

    monkeypatch.setattr(corpus_seal, "_rename_noreplace", replace_then_fail)
    try:
        with pytest.raises(OSError, match="simulated replacement race"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=data_sha256s,
                report_sha256s=report_sha256s,
            )
        stages = list(report.parent.glob(f".{report.name}.staging-*"))
        assert len(stages) == 1
        assert stages[0].read_bytes() == replacement
        stages[0].unlink()
    finally:
        _unlock_tree(destination)


def test_report_publication_requires_every_external_anchor_at_runtime(
    tmp_path: Path,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)
    try:
        with pytest.raises(corpus_seal.CorpusSealError, match="dataset manifest hash"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=None,  # type: ignore[arg-type]
                data_sha256s=data_sha256s,
                report_sha256s=report_sha256s,
            )
        with pytest.raises(corpus_seal.CorpusSealError, match="requires all twelve"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=None,  # type: ignore[arg-type]
                report_sha256s=report_sha256s,
            )
        with pytest.raises(corpus_seal.CorpusSealError, match="requires all twelve"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=data_sha256s,
                report_sha256s=None,  # type: ignore[arg-type]
            )
    finally:
        _unlock_tree(destination)


def test_existing_report_is_fsynced_with_its_parent_then_reverified(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)
    try:
        expected = corpus_seal.publish_seal_report(
            report,
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
            publisher_job_id="99",
            dataset_manifest_sha256=manifest_sha256,
            data_sha256s=data_sha256s,
            report_sha256s=report_sha256s,
        )
        events: list[tuple[str, Path]] = []
        original_file = corpus_seal._fsync_regular_file
        original_directory = corpus_seal._fsync_directory

        def fsync_file(path: Path, label: str) -> None:
            events.append(("file", path))
            original_file(path, label)

        def fsync_directory(path: Path) -> None:
            events.append(("directory", path))
            original_directory(path)

        monkeypatch.setattr(corpus_seal, "_fsync_regular_file", fsync_file)
        monkeypatch.setattr(corpus_seal, "_fsync_directory", fsync_directory)
        assert corpus_seal.publish_seal_report(
            report,
            destination,
            source_commit=COMMIT,
            prepare_job_id=JOB_ID,
            publisher_job_id="99",
            dataset_manifest_sha256=manifest_sha256,
            data_sha256s=data_sha256s,
            report_sha256s=report_sha256s,
        ) == expected
        assert events == [("file", report), ("directory", report.parent)]
    finally:
        if report.exists():
            os.chmod(report, 0o600)
        _unlock_tree(destination)


def test_report_mode_check_is_bound_to_the_inode_that_is_opened(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)
    expected = corpus_seal.publish_seal_report(
        report,
        destination,
        source_commit=COMMIT,
        prepare_job_id=JOB_ID,
        publisher_job_id="99",
        dataset_manifest_sha256=manifest_sha256,
        data_sha256s=data_sha256s,
        report_sha256s=report_sha256s,
    )
    replacement = report.with_name("writable-replacement.json")
    replacement.write_bytes(report.read_bytes())
    os.chmod(replacement, 0o644)
    original_lstat = corpus_seal._regular_lstat
    replaced = False

    def replace_after_lstat(path: Path, label: str) -> os.stat_result:
        nonlocal replaced
        before = original_lstat(path, label)
        if path == report and not replaced:
            os.replace(replacement, report)
            replaced = True
        return before

    monkeypatch.setattr(corpus_seal, "_regular_lstat", replace_after_lstat)
    try:
        with pytest.raises(corpus_seal.CorpusSealError, match="changed while it was opened"):
            corpus_seal._verify_seal_report(report, expected)
    finally:
        if report.exists():
            os.chmod(report, 0o600)
        _unlock_tree(destination)


def test_stage_replacement_after_read_is_rejected_before_report_rename(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    report = tmp_path / "logs" / "seal-report-99.json"
    manifest_sha256, data_sha256s, report_sha256s = _hash_anchors(bundle)
    _anchored_seal(bundle)
    original_read = corpus_seal._read_regular_bytes
    replacement = b"foreign report stage\n"

    def replace_after_read(path: Path, label: str, *, limit: int) -> bytes:
        raw = original_read(path, label, limit=limit)
        if label == "staged corpus seal verification report":
            os.chmod(path, 0o600)
            path.unlink()
            path.write_bytes(replacement)
            os.chmod(path, 0o444)
        return raw

    monkeypatch.setattr(corpus_seal, "_read_regular_bytes", replace_after_read)
    try:
        with pytest.raises(corpus_seal.CorpusSealError, match="changed before publication"):
            corpus_seal.publish_seal_report(
                report,
                destination,
                source_commit=COMMIT,
                prepare_job_id=JOB_ID,
                publisher_job_id="99",
                dataset_manifest_sha256=manifest_sha256,
                data_sha256s=data_sha256s,
                report_sha256s=report_sha256s,
            )
        assert not report.exists()
        stages = list(report.parent.glob(f".{report.name}.staging-*"))
        assert len(stages) == 1
        assert stages[0].read_bytes() == replacement
    finally:
        _unlock_tree(destination)


@pytest.mark.parametrize(
    "relative",
    (
        ".",
        "data",
        "reports",
        "seal.json",
        "data/train.jsonl",
        "reports/token-audit.json",
    ),
)
def test_verifier_rejects_a_writable_seal_component(
    tmp_path: Path, relative: str
) -> None:
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    _seal(bundle)
    try:
        target = destination / relative
        current = stat.S_IMODE(target.stat().st_mode)
        os.chmod(target, current | stat.S_IWUSR, follow_symlinks=False)
        with pytest.raises(corpus_seal.CorpusSealError, match="read-only"):
            corpus_seal.verify_seal(destination)
    finally:
        _unlock_tree(destination)


def test_cli_create_and_verify_contract(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    cli = _load_script()
    bundle = _fixture_bundle(tmp_path)
    destination = bundle["destination"]
    assert isinstance(destination, Path)
    try:
        assert cli.main(
            [
                "create",
                "--artifact-dir",
                str(bundle["artifact_dir"]),
                "--dataset-attestation",
                str(bundle["dataset_attestation"]),
                "--token-audit",
                str(bundle["token_audit"]),
                "--runtime-smoke",
                str(bundle["runtime_smoke"]),
                "--destination",
                str(destination),
                "--source-commit",
                COMMIT,
                "--prepare-job-id",
                JOB_ID,
            ]
        ) == 0
        output = json.loads(capsys.readouterr().out)
        assert output["status"] == "verified"
        assert output["files"] == 15

        assert cli.main(
            [
                "verify",
                "--seal",
                str(destination),
                "--source-commit",
                COMMIT,
                "--prepare-job-id",
                JOB_ID,
            ]
        ) == 0
        assert json.loads(capsys.readouterr().out)["prepare_job_id"] == JOB_ID
    finally:
        _unlock_tree(destination)
