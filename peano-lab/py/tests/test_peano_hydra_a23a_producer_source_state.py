from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import training.peano_hydra.library_optimizer_comparison_pilot as pilot  # noqa: E402


SCRIPT_PATH = ROOT / "scripts" / "build_peano_hydra_a23a_producer_source_state.py"


def _load_source_state_module():
    name = "_test_peano_hydra_a23a_producer_source_state"
    specification = importlib.util.spec_from_file_location(name, SCRIPT_PATH)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


source_state = _load_source_state_module()


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
    ).stdout


@pytest.fixture()
def clean_repository(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    owned_paths = tuple(path for path, _digest in source_state.FROZEN_PRODUCER_SOURCES)
    for relative in (*owned_paths, source_state.GENERATOR_PATH):
        destination = repo / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, destination)
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "hydra-test@example.invalid")
    _git(repo, "config", "user.name", "Hydra Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "fixture")
    assert _git(repo, "status", "--porcelain=v1", "-z") == b""
    return repo


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _compact(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def test_source_state_has_exact_frozen_shape_and_integrates_with_builder_validation(
    clean_repository: Path,
) -> None:
    state, receipt, envelope = source_state.build_producer_evidence(clean_repository)

    assert set(state) == {
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    }
    assert state["git_verified"] is False
    assert [(row["path"], row["sha256"]) for row in state["files"]] == [
        (path.as_posix(), digest)
        for path, digest in source_state.FROZEN_PRODUCER_SOURCES
    ]
    assert state["root_sha256"] == _sha(_compact(state["root_preimage"]))

    # This is the frozen producer's exact shape/live-byte validator, but it
    # does not run a proof build or import the optimizer into the generator.
    assert pilot._validate_producer_source_state(state, root=clean_repository) == state
    assert source_state.validate_producer_source_state(
        state, repository_root=clean_repository
    ) == state
    assert envelope["source_state"] == state
    assert envelope["git_receipt"] == receipt


def test_git_receipt_binds_clean_commit_tree_generator_tool_and_children(
    clean_repository: Path,
) -> None:
    state, receipt, envelope = source_state.build_producer_evidence(clean_repository)
    source_raw = source_state.canonical_document_bytes(state)
    receipt_raw = source_state.canonical_document_bytes(receipt)

    assert set(receipt) == {
        "authority_claims",
        "commands",
        "commit_sha1",
        "format",
        "generator",
        "git_tool",
        "root_preimage",
        "root_sha256",
        "source_files",
        "source_state_artifact_sha256",
        "source_state_root_sha256",
        "source_state_sha256",
        "status",
        "tree_sha1",
        "v",
        "verification",
    }
    assert receipt["format"] == source_state.GIT_RECEIPT_FORMAT
    assert receipt["status"] == "passed"
    assert receipt["commit_sha1"] == _git(clean_repository, "rev-parse", "HEAD").strip().decode()
    assert receipt["tree_sha1"] == _git(
        clean_repository, "rev-parse", "HEAD^{tree}"
    ).strip().decode()
    assert receipt["generator"]["path"] == source_state.GENERATOR_PATH.as_posix()
    assert receipt["generator"]["verified"] is True
    assert receipt["source_state_artifact_sha256"] == _sha(source_raw)
    assert receipt["source_state_sha256"] == _sha(_compact(state))
    assert receipt["source_state_root_sha256"] == state["root_sha256"]
    assert receipt["root_sha256"] == _sha(_compact(receipt["root_preimage"]))
    assert receipt["verification"] == {
        **receipt["verification"],
        "clean_after": True,
        "clean_before": True,
        "commit_stable": True,
        "porcelain_after_bytes": 0,
        "porcelain_after_sha256": _sha(b""),
        "porcelain_before_bytes": 0,
        "porcelain_before_sha256": _sha(b""),
        "stage_zero_regular_blobs": True,
        "tree_stable": True,
    }
    assert all(row["exit_code"] == 0 for row in receipt["commands"])
    assert receipt["commands"][0]["argv"] == ["git", "--version"]
    assert receipt["git_tool"]["path"].startswith("/")
    assert receipt["git_tool"]["bytes"] > 0
    assert len(receipt["source_files"]) == 4
    assert all(
        set(row)
        == {
            "blob_oid_sha1",
            "bytes",
            "committed_sha256",
            "live_sha256",
            "mode",
            "path",
            "verified",
        }
        for row in [*receipt["source_files"], receipt["generator"]]
    )
    assert all(row["verified"] is True for row in receipt["source_files"])
    assert all(value is False for value in receipt["authority_claims"].values())

    assert envelope["source_state_artifact_sha256"] == _sha(source_raw)
    assert envelope["git_receipt_artifact_sha256"] == _sha(receipt_raw)
    assert envelope["source_state_root_sha256"] == state["root_sha256"]
    assert envelope["git_receipt_root_sha256"] == receipt["root_sha256"]
    assert envelope["root_sha256"] == _sha(_compact(envelope["root_preimage"]))


def test_build_is_deterministic_in_one_clean_repository(clean_repository: Path) -> None:
    first = source_state.build_producer_evidence(clean_repository)
    second = source_state.build_producer_evidence(clean_repository)
    assert tuple(source_state.canonical_document_bytes(item) for item in first) == tuple(
        source_state.canonical_document_bytes(item) for item in second
    )


def test_ambient_git_redirection_and_config_are_not_inherited(
    clean_repository: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    baseline = source_state.build_producer_evidence(clean_repository)
    poison = tmp_path / "poison"
    poison.mkdir()
    _git(poison, "init", "-q")
    poisoned_index = tmp_path / "poison.index"
    for key, value in {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(poison / "objects"),
        "GIT_CONFIG_COUNT": "1",
        "GIT_CONFIG_KEY_0": "core.pager",
        "GIT_CONFIG_VALUE_0": "false",
        "GIT_DIR": str(poison / ".git"),
        "GIT_INDEX_FILE": str(poisoned_index),
        "GIT_NAMESPACE": "poison",
        "GIT_OBJECT_DIRECTORY": str(poison / "objects"),
        "GIT_WORK_TREE": str(poison),
    }.items():
        monkeypatch.setenv(key, value)

    assert source_state.build_producer_evidence(clean_repository) == baseline


def test_untracked_or_modified_worktree_fails_closed(
    clean_repository: Path,
) -> None:
    (clean_repository / "untracked.txt").write_text("not evidence\n", encoding="utf-8")
    with pytest.raises(source_state.ProducerSourceStateError, match="not clean"):
        source_state.build_producer_evidence(clean_repository)


def test_clean_commit_with_frozen_source_drift_fails_pin(
    clean_repository: Path,
) -> None:
    relative = source_state.FROZEN_PRODUCER_SOURCES[0][0]
    with (clean_repository / relative).open("ab") as stream:
        stream.write(b"\n")
    _git(clean_repository, "add", relative.as_posix())
    _git(clean_repository, "commit", "-q", "-m", "drift")
    with pytest.raises(source_state.ProducerSourceStateError, match="hash drifted"):
        source_state.build_producer_evidence(clean_repository)


def test_generator_must_be_one_committed_stage_zero_regular_blob(
    clean_repository: Path,
) -> None:
    generator = clean_repository / source_state.GENERATOR_PATH
    generator.unlink()
    generator.symlink_to("build_peano_hydra_library_optimizer_comparison_pilot.py")
    _git(clean_repository, "add", source_state.GENERATOR_PATH.as_posix())
    _git(clean_repository, "commit", "-q", "-m", "replace generator with link")
    with pytest.raises(source_state.ProducerSourceStateError):
        source_state.build_producer_evidence(clean_repository)


def test_mutated_source_state_root_or_file_is_rejected(clean_repository: Path) -> None:
    state = source_state.build_producer_source_state(clean_repository)
    wrong_root = deepcopy(state)
    wrong_root["root_sha256"] = "0" * 64
    with pytest.raises(source_state.ProducerSourceStateError, match="root"):
        source_state.validate_producer_source_state(
            wrong_root, repository_root=clean_repository
        )

    wrong_file = deepcopy(state)
    wrong_file["files"][0]["sha256"] = "0" * 64
    with pytest.raises(source_state.ProducerSourceStateError, match="identity drifted"):
        source_state.validate_producer_source_state(
            wrong_file, repository_root=clean_repository
        )


def test_cli_stdout_create_only_and_check(
    clean_repository: Path, tmp_path: Path
) -> None:
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    state_path = output_dir / "source-state.json"
    receipt_path = output_dir / "git-receipt.json"
    command = [
        sys.executable,
        str(SCRIPT_PATH),
        "--repository-root",
        str(clean_repository),
        "--source-state-output",
        str(state_path),
        "--git-receipt-output",
        str(receipt_path),
    ]
    created = subprocess.run(command, check=False, capture_output=True, timeout=30)
    assert created.returncode == 0, created.stderr.decode()
    envelope = json.loads(created.stdout)
    assert envelope["format"] == source_state.EVIDENCE_ENVELOPE_FORMAT
    assert state_path.read_bytes() == source_state.canonical_document_bytes(
        envelope["source_state"]
    )
    assert receipt_path.read_bytes() == source_state.canonical_document_bytes(
        envelope["git_receipt"]
    )

    refused = subprocess.run(command, check=False, capture_output=True, timeout=30)
    assert refused.returncode != 0
    assert b"already exists" in refused.stderr

    checked = subprocess.run(
        [*command, "--check"], check=False, capture_output=True, timeout=30
    )
    assert checked.returncode == 0, checked.stderr.decode()
    assert json.loads(checked.stdout) == envelope

    receipt_path.write_bytes(receipt_path.read_bytes() + b" ")
    rejected = subprocess.run(
        [*command, "--check"], check=False, capture_output=True, timeout=30
    )
    assert rejected.returncode != 0
    assert b"differs" in rejected.stderr


def test_generator_has_no_optimizer_import() -> None:
    source = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "import training.peano_hydra.library_optimizer_comparison_pilot" not in source
    assert "from training.peano_hydra.library_optimizer_comparison_pilot" not in source
