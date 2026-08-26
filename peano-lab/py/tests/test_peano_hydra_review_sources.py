"""Source receipt attacks use tiny temporary Git repositories, never real data."""

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

from training.peano_hydra import review_sources as sources  # noqa: E402


HELPER = "training/peano_hydra/helper.py"
KERNEL = "peano-lab/py/peano_lab/kernel/checker.py"


def _git(repository: Path, *arguments: str) -> str:
    environment = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    environment.update({"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull})
    return subprocess.run(
        ["git", "-C", str(repository), "-c", "user.name=Review source test",
         "-c", "user.email=review-source@example.invalid", "-c", "commit.gpgsign=false",
         "-c", f"core.hooksPath={os.devnull}", "-c", "init.defaultBranch=main", *arguments],
        check=True, capture_output=True, text=True, timeout=5, env=environment,
    ).stdout.strip()


def _commit(repository: Path) -> str:
    _git(repository, "add", "--all")
    _git(repository, "commit", "-q", "-m", "Synthetic source inventory")
    return _git(repository, "rev-parse", "HEAD")


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(
        value, ensure_ascii=False, allow_nan=False, sort_keys=True,
        separators=(",", ":"),
    ).encode()).hexdigest()


def _seal(record: dict) -> dict:
    record["files_sha256"] = _digest(record["files"])
    return record


def _descriptor(path: Path) -> dict:
    content = path.read_bytes()
    return {"bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}


@pytest.fixture
def repository(tmp_path, monkeypatch) -> Path:
    repository = tmp_path / "repository"
    repository.mkdir()
    for relative in sorted(sources.REQUIRED_FILES | {HELPER, "training/peano_policy/extra.py"}):
        path = repository / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# synthetic fixture: {relative}\n", encoding="utf-8")
        path.chmod(0o644)
    _git(repository, "init", "-q")
    _commit(repository)
    monkeypatch.setattr(sources, "ROOT", repository)
    return repository


def test_clean_committed_source_identity_is_deterministic_and_complete(repository) -> None:
    first = sources.source_identity()
    assert first == sources.source_identity()
    assert first["git_commit"] == _git(repository, "rev-parse", "HEAD")
    assert first["git_dirty"] is False
    assert first["files_sha256"] == _digest(first["files"])
    assert set(first["files"]) == sources.REQUIRED_FILES | {HELPER, "training/peano_policy/extra.py"}
    assert sources.validate_sources(first) is None


def test_draft_identity_can_be_dirty_but_cannot_execute(repository) -> None:
    (repository / "draft-notes.txt").write_text("Not committed\n")
    record = sources.source_identity()
    assert record["git_dirty"] is True
    with pytest.raises(sources.ReviewSourceError, match="clean committed"):
        sources.validate_sources(record)


def test_worker_byte_check_spawns_no_git_or_children_and_rejects_drift(repository, monkeypatch) -> None:
    record = sources.source_identity()

    def forbidden(*arguments, **keywords):
        raise AssertionError("worker source drift checks must not invoke Git or a subprocess")

    monkeypatch.setattr(sources, "_git", forbidden)
    monkeypatch.setattr(sources, "bounded_git", forbidden)
    monkeypatch.setattr(sources.subprocess, "Popen", forbidden)
    assert sources.check_recorded_source_bytes(record) is None
    (repository / KERNEL).write_text("# changed while a worker was starting\n")
    with pytest.raises(sources.ReviewSourceError, match="recorded source bytes"):
        sources.check_recorded_source_bytes(record)


@pytest.mark.parametrize("change", ["dirty", "missing_required", "bad_descriptor", "bad_digest", "extra_claim"])
def test_worker_byte_check_retains_strict_receipt_validation(repository, monkeypatch, change) -> None:
    record = sources.source_identity()
    if change == "dirty":
        record["git_dirty"] = True
    elif change == "missing_required":
        del record["files"][KERNEL]
        _seal(record)
    elif change == "bad_descriptor":
        record["files"][HELPER]["bytes"] = True
        _seal(record)
    elif change == "bad_digest":
        record["files_sha256"] = "0" * 64
    else:
        record["approved"] = True

    def forbidden(*arguments, **keywords):
        raise AssertionError("worker source receipt validation must not invoke Git")

    monkeypatch.setattr(sources, "_git", forbidden)
    with pytest.raises(sources.ReviewSourceError):
        sources.check_recorded_source_bytes(record)


def test_archive_survives_later_commit_with_unrelated_python_addition(repository) -> None:
    original = sources.source_identity()
    (repository / "training/peano_hydra/later.py").write_text("# unrelated later module\n")
    next_commit = _commit(repository)
    assert next_commit != original["git_commit"]
    assert sources.source_identity()["git_dirty"] is False
    assert sources.validate_sources(original) is None


def test_archive_survives_unrelated_dirty_current_files(repository) -> None:
    original = sources.source_identity()
    (repository / "training/peano_hydra/later.py").write_text("# unrelated later draft\n")
    assert sources.source_identity()["git_dirty"] is True
    assert sources.validate_sources(original) is None


@pytest.mark.parametrize("relative", [
    KERNEL, "peano-lab/py/peano_lab/kernel/terms.py",
    "training/peano_hydra/review_sources.py", "scripts/hydra_bounded_exec.py", HELPER,
])
def test_omitted_historical_source_cannot_be_resealed(repository, relative) -> None:
    record = sources.source_identity()
    del record["files"][relative]
    with pytest.raises(sources.ReviewSourceError, match="omits|required|historical Git inventory"):
        sources.validate_sources(_seal(record))


def test_added_entry_cannot_be_resealed_into_an_older_inventory(repository) -> None:
    record = sources.source_identity()
    relative = "training/peano_hydra/inserted.py"
    (repository / relative).write_text("# not in the recorded commit\n")
    record["files"][relative] = _descriptor(repository / relative)
    with pytest.raises(sources.ReviewSourceError, match="exact historical Git inventory"):
        sources.validate_sources(_seal(record))


def test_real_commit_cannot_hide_new_historical_entries(repository) -> None:
    record = sources.source_identity()
    (repository / "training/peano_hydra/extra_historical.py").write_text("# present at next commit\n")
    record["git_commit"] = _commit(repository)
    with pytest.raises(sources.ReviewSourceError, match="exact historical Git inventory"):
        sources.validate_sources(record)


def test_changed_source_is_rejected_even_when_descriptor_and_manifest_are_resealed(repository) -> None:
    record = sources.source_identity()
    (repository / KERNEL).write_text("# maliciously changed kernel\n")
    record["files"][KERNEL] = _descriptor(repository / KERNEL)
    with pytest.raises(sources.ReviewSourceError, match="recorded Git blob"):
        sources.validate_sources(_seal(record))


def test_recorded_bytes_remain_required_without_resealing(repository) -> None:
    record = sources.source_identity()
    (repository / HELPER).write_text("# changed source\n")
    with pytest.raises(sources.ReviewSourceError, match="recorded source bytes"):
        sources.validate_sources(record)


def test_later_changed_source_cannot_be_attributed_to_an_older_commit(repository) -> None:
    original = sources.source_identity()
    (repository / HELPER).write_text("# different committed source\n")
    _commit(repository)
    changed = sources.source_identity()
    assert changed["git_dirty"] is False
    changed["git_commit"] = original["git_commit"]
    with pytest.raises(sources.ReviewSourceError, match="recorded Git blob"):
        sources.validate_sources(changed)


@pytest.mark.parametrize("revision", ["f" * 40, "0" * 40, "HEAD", "A" * 40, "", None, True])
def test_fake_or_noncanonical_commit_is_rejected(repository, revision) -> None:
    record = sources.source_identity()
    record["git_commit"] = revision
    with pytest.raises(sources.ReviewSourceError):
        sources.validate_sources(record)


@pytest.mark.parametrize("kind", ["tree", "blob"])
def test_existing_noncommit_git_object_is_rejected(repository, kind) -> None:
    record = sources.source_identity()
    record["git_commit"] = (
        _git(repository, "rev-parse", "HEAD^{tree}") if kind == "tree"
        else _git(repository, "hash-object", HELPER)
    )
    with pytest.raises(sources.ReviewSourceError, match="real Git commit"):
        sources.validate_sources(record)


@pytest.mark.parametrize("path", [
    "./training/peano_hydra/helper.py", "training/peano_hydra//helper.py",
    "training/peano_hydra/./helper.py", "training/peano_hydra/../helper.py",
    "/training/peano_hydra/helper.py", "training\\peano_hydra\\helper.py",
    "training/peano_hydra/helper\n.py", "training/peano_hydra/helper\x00.py",
    "training/peano_hydra/helper\t.py", "training/peano_hydra2/helper.py",
    "scripts/not_reviewed.py", "peano-lab/py/tests/not_reviewed.py",
    "training/peano_hydra/helper.txt", "training/peano_hydra/helper.py/",
])
def test_noncanonical_or_out_of_scope_paths_cannot_be_resealed(repository, path) -> None:
    record = sources.source_identity()
    record["files"][path] = record["files"].pop(HELPER)
    with pytest.raises(sources.ReviewSourceError, match="canonical|escapes"):
        sources.validate_sources(_seal(record))


@pytest.mark.parametrize("path", [23, None, "training/peano_hydra/bad\ud800.py"])
def test_nonstring_or_invalid_utf8_path_fails_before_digesting(repository, path) -> None:
    record = sources.source_identity()
    record["files"][path] = record["files"].pop(HELPER)
    with pytest.raises(sources.ReviewSourceError):
        sources.validate_sources(record)


@pytest.mark.parametrize("descriptor", [
    {"bytes": True, "sha256": "a" * 64}, {"bytes": -1, "sha256": "a" * 64},
    {"bytes": sources.MAX_SOURCE_BYTES + 1, "sha256": "a" * 64},
    {"bytes": 0, "sha256": "A" * 64}, {"bytes": 0, "sha256": "a" * 63},
    {"bytes": 0, "sha256": "a" * 64, "approved": True}, {"bytes": 0}, [], None,
])
def test_malformed_descriptors_fail_closed(repository, descriptor) -> None:
    record = sources.source_identity()
    record["files"][HELPER] = descriptor
    with pytest.raises(sources.ReviewSourceError, match="descriptor"):
        sources.validate_sources(_seal(record))


@pytest.mark.parametrize("change", [
    {"git_dirty": True}, {"git_dirty": 0}, {"git_dirty": None},
    {"files_sha256": "0" * 64}, {"approved": True}, {"files": []},
])
def test_receipt_schema_and_digest_are_strict(repository, change) -> None:
    record = sources.source_identity()
    record.update(change)
    with pytest.raises(sources.ReviewSourceError):
        sources.validate_sources(record)


def test_current_source_file_symlink_is_rejected_even_with_same_bytes(repository, tmp_path) -> None:
    record = sources.source_identity()
    original = repository / HELPER
    outside = tmp_path / "same-bytes.py"
    outside.write_bytes(original.read_bytes())
    original.unlink()
    original.symlink_to(outside)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.validate_sources(record)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.source_identity()


def test_parent_directory_symlink_cannot_hide_unchanged_source(repository, tmp_path) -> None:
    record = sources.source_identity()
    kernel = repository / "peano-lab/py/peano_lab/kernel"
    outside = tmp_path / "moved-kernel"
    kernel.rename(outside)
    kernel.symlink_to(outside, target_is_directory=True)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.validate_sources(record)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.source_identity()


def test_root_symlink_is_not_an_alternate_source_root(repository, tmp_path, monkeypatch) -> None:
    record = sources.source_identity()
    link = tmp_path / "repository-alias"
    link.symlink_to(repository, target_is_directory=True)
    monkeypatch.setattr(sources, "ROOT", link)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.validate_sources(record)


def test_historical_source_symlink_cannot_be_resealed(repository) -> None:
    record = sources.source_identity()
    relative = "training/peano_hydra/alias.py"
    (repository / relative).symlink_to("helper.py")
    record["git_commit"] = _commit(repository)
    record["files"][relative] = deepcopy(record["files"][HELPER])
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.validate_sources(_seal(record))


def test_historical_directory_symlink_is_not_a_hidden_module_tree(repository) -> None:
    record = sources.source_identity()
    (repository / "training/peano_hydra/alias_directory").symlink_to("../peano_policy", target_is_directory=True)
    record["git_commit"] = _commit(repository)
    with pytest.raises(sources.ReviewSourceError, match="symlink"):
        sources.validate_sources(record)


def test_executable_mode_change_is_bound_to_historical_blob_mode(repository) -> None:
    record = sources.source_identity()
    (repository / HELPER).chmod(0o755)
    with pytest.raises(sources.ReviewSourceError, match="recorded Git blob"):
        sources.validate_sources(record)


def test_missing_source_file_fails_closed(repository) -> None:
    record = sources.source_identity()
    (repository / HELPER).unlink()
    with pytest.raises(sources.ReviewSourceError, match="missing"):
        sources.validate_sources(record)


def test_fifo_is_rejected_without_a_blocking_read(repository) -> None:
    record = sources.source_identity()
    original = repository / HELPER
    original.unlink()
    os.mkfifo(original)
    with pytest.raises(sources.ReviewSourceError, match="regular file"):
        sources.validate_sources(record)


def test_ignored_untracked_python_is_dirty_and_cannot_claim_historical_inventory(repository) -> None:
    (repository / ".gitignore").write_text("*.ignored.py\n")
    _commit(repository)
    (repository / "training/peano_hydra/extra.ignored.py").write_text("# ignored but executable source\n")
    assert _git(repository, "status", "--porcelain") == ""
    record = sources.source_identity()
    assert record["git_dirty"] is True
    record["git_dirty"] = False
    with pytest.raises(sources.ReviewSourceError, match="historical Git inventory"):
        sources.validate_sources(record)


def test_assume_unchanged_cannot_hide_dirty_source_bytes(repository) -> None:
    _git(repository, "update-index", "--assume-unchanged", HELPER)
    (repository / HELPER).write_text("# status-hidden change\n")
    assert _git(repository, "status", "--porcelain") == ""
    record = sources.source_identity()
    assert record["git_dirty"] is True
    record["git_dirty"] = False
    with pytest.raises(sources.ReviewSourceError, match="recorded Git blob"):
        sources.validate_sources(record)


def test_git_replace_refs_cannot_rewrite_the_recorded_tree(repository) -> None:
    record = sources.source_identity()
    (repository / "training/peano_hydra/later.py").write_text("# later inventory\n")
    newer = _commit(repository)
    _git(repository, "replace", record["git_commit"], newer)
    original_names = sources.bounded_git(
        repository, "ls-tree", "-r", "--name-only", record["git_commit"], maximum=16384,
    )
    assert b"training/peano_hydra/later.py" not in original_names
    assert sources.validate_sources(record) is None


def test_shared_bounded_git_uses_explicit_project_despite_hostile_redirects(repository, tmp_path, monkeypatch) -> None:
    other = tmp_path / "independent-reference-repository"
    other.mkdir()
    (other / "Reference.lean").write_text("-- independent reference fixture\n")
    _git(other, "init", "-q")
    expected = _commit(other)
    assert expected != _git(repository, "rev-parse", "HEAD")
    monkeypatch.setenv("GIT_DIR", str(repository / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(repository))
    monkeypatch.setenv("GIT_INDEX_FILE", str(repository / ".git/index"))
    assert sources.bounded_git(other, "rev-parse", "HEAD", maximum=80) == expected.encode() + b"\n"
    assert sources.ROOT == repository


def test_shared_bounded_git_disables_lazy_fetch_and_replace_in_inherited_environment(repository, monkeypatch) -> None:
    commit = _git(repository, "rev-parse", "HEAD")
    seen = []
    original = subprocess.Popen

    def observe(*arguments, **keywords):
        seen.append(keywords["env"])
        return original(*arguments, **keywords)

    monkeypatch.setenv("GIT_NO_LAZY_FETCH", "0")
    monkeypatch.setenv("GIT_NO_REPLACE_OBJECTS", "0")
    monkeypatch.setattr(sources.subprocess, "Popen", observe)
    assert sources.bounded_git(repository, "cat-file", "-t", commit, maximum=32) == b"commit\n"
    assert len(seen) == 1
    assert seen[0]["GIT_NO_LAZY_FETCH"] == "1"
    assert seen[0]["GIT_NO_REPLACE_OBJECTS"] == "1"
    assert seen[0]["GIT_OPTIONAL_LOCKS"] == "0"


def test_inherited_git_environment_cannot_redirect_source_validation(repository, monkeypatch) -> None:
    record = sources.source_identity()
    monkeypatch.setenv("GIT_DIR", "/not-the-source-repository")
    monkeypatch.setenv("GIT_WORK_TREE", "/not-the-source-worktree")
    monkeypatch.setenv("GIT_INDEX_FILE", "/not-the-source-index")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "core.fsmonitor")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "/do-not-execute")
    assert sources.validate_sources(record) is None


@pytest.mark.parametrize("constant,value", [
    ("MAX_SOURCE_BYTES", 1), ("MAX_TOTAL_SOURCE_BYTES", 1),
    ("MAX_SOURCE_FILES", 1), ("MAX_INVENTORY_BYTES", 32),
])
def test_current_and_recorded_inventories_respect_bounds(repository, monkeypatch, constant, value) -> None:
    record = sources.source_identity()
    monkeypatch.setattr(sources, constant, value)
    with pytest.raises(sources.ReviewSourceError):
        sources.source_identity()
    with pytest.raises(sources.ReviewSourceError):
        sources.validate_sources(record)


def test_empty_python_sources_are_valid_when_they_are_committed(repository) -> None:
    (repository / HELPER).write_bytes(b"")
    _commit(repository)
    record = sources.source_identity()
    assert record["files"][HELPER]["bytes"] == 0
    assert sources.validate_sources(record) is None
