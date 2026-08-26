"""M9 strict validation and deterministic export for v=1 trace corpora."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "export_traces.py"


def _load_exporter():
    spec = importlib.util.spec_from_file_location("_test_export_traces_module", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


exporter = _load_exporter()


def _step(
    session: str,
    step: int,
    before: list[str],
    tactic: str,
    after: list[str],
    *,
    status: str = "ok",
    error: str | None = None,
    focus: int = 0,
) -> dict[str, object]:
    return {
        "v": 1,
        "session": session,
        "step": step,
        "goals_before": before,
        "focus": focus,
        "tactic": tactic,
        "goals_after": after,
        "status": status,
        "error": error,
    }


def _footer(
    theorem: str,
    tactic_count: int,
    *,
    qed: bool = True,
    proof_size: int = 1,
) -> dict[str, object]:
    return {
        "qed": qed,
        "theorem": theorem,
        "proof_size": proof_size,
        "tactic_count": tactic_count,
    }


def _write(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records),
        encoding="utf-8",
    )
    return path


def _valid_records(
    session: str = "s-1", theorem: str = "0 = 0"
) -> list[dict[str, object]]:
    return [
        _step(session, 1, [f"⊢ {theorem}"], "refl", []),
        _footer(theorem, 1),
    ]


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _semantic(record: dict[str, object]) -> str:
    return json.dumps(
        {
            key: value
            for key, value in record.items()
            if key not in {"session", "step"}
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def test_loads_complete_sessions_and_preserves_binding_field_order(tmp_path: Path) -> None:
    raw = _write(
        tmp_path / "raw.jsonl",
        _valid_records("first", "0 = 0")
        + [
            _step("second", 1, ["⊢ 0 = S 0"], "refl", ["⊢ 0 = S 0"], status="error", error="the sides differ."),
            _footer("0 = S 0", 1, qed=False, proof_size=0),
        ],
    )

    sessions = exporter.load_trace_file(raw)

    assert [session.session_id for session in sessions] == ["first", "second"]
    assert [session.theorem for session in sessions] == ["0 = 0", "0 = S 0"]
    assert list(sessions[0].steps[0]) == list(exporter.STEP_FIELDS)
    assert list(sessions[0].footer) == list(exporter.FOOTER_FIELDS)


def test_footer_binding_allows_only_original_free_variable_declarations(
    tmp_path: Path,
) -> None:
    free_goal = _write(
        tmp_path / "free.jsonl",
        [
            _step("free", 1, ["b : ℕ, a : ℕ ⊢ a ≤ b"], "exact h", []),
            _footer("a ≤ b", 1),
        ],
    )
    assert exporter.load_trace_file(free_goal)[0].theorem == "a ≤ b"

    contextual = _write(
        tmp_path / "contextual.jsonl",
        [
            _step("contextual", 1, ["h : P ⊢ A"], "exact h", []),
            _footer("A", 1),
        ],
    )
    with pytest.raises(exporter.TraceFormatError, match="free-variable declarations"):
        exporter.load_trace_file(contextual)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda records: [{"session": records[0]["session"], "v": 1, **{key: value for key, value in records[0].items() if key not in {"v", "session"}}}, records[1]],
            "field order/set",
        ),
        (
            lambda records: [{**records[0], "extra": 1}, records[1]],
            "field order/set",
        ),
        (
            lambda records: [{**records[0], "v": True}, records[1]],
            "v must be the integer 1",
        ),
        (
            lambda records: [{**records[0], "step": True}, records[1]],
            "step must be a positive integer",
        ),
        (
            lambda records: [{**records[0], "goals_before": "⊢ 0 = 0"}, records[1]],
            "goals_before must be a JSON array",
        ),
        (
            lambda records: [{**records[0], "focus": 1}, records[1]],
            "focus is outside goals_before",
        ),
        (
            lambda records: [{**records[0], "status": "success"}, records[1]],
            "status must be exactly",
        ),
        (
            lambda records: [{**records[0], "error": "impossible"}, records[1]],
            "ok transition must have error: null",
        ),
        (
            lambda records: [records[0], {**records[1], "qed": 1}],
            "qed must be a boolean",
        ),
        (
            lambda records: [records[0], {**records[1], "tactic_count": True}],
            "tactic_count must be a non-negative integer",
        ),
    ],
)
def test_rejects_wrong_fields_types_and_values(tmp_path: Path, mutate, message: str) -> None:
    raw = _write(tmp_path / "bad.jsonl", mutate(_valid_records()))
    with pytest.raises(exporter.TraceFormatError, match=message):
        exporter.load_trace_file(raw)


def test_rejects_nontransactional_error_and_broken_state_continuity(tmp_path: Path) -> None:
    changed_failure = _write(
        tmp_path / "changed-failure.jsonl",
        [
            _step(
                "bad",
                1,
                ["⊢ 0 = S 0"],
                "refl",
                [],
                status="error",
                error="no",
            ),
            _footer("0 = S 0", 1, qed=False),
        ],
    )
    with pytest.raises(exporter.TraceFormatError, match="must be transactional"):
        exporter.load_trace_file(changed_failure)

    discontinuous = _write(
        tmp_path / "discontinuous.jsonl",
        [
            _step("gap", 1, ["⊢ A"], "first", ["⊢ B"]),
            _step("gap", 2, ["⊢ C"], "second", [], status="ok"),
            _footer("A", 2),
        ],
    )
    with pytest.raises(exporter.TraceFormatError, match="breaks goal-state continuity"):
        exporter.load_trace_file(discontinuous)


@pytest.mark.parametrize(
    ("records", "message"),
    [
        ([_footer("0 = 0", 0)], "footer has no preceding"),
        ([_step("unfinished", 1, ["⊢ 0 = 0"], "refl", [])], "missing its footer"),
        (
            _valid_records() + [_footer("0 = 0", 1)],
            "footer has no preceding",
        ),
        (
            [
                _step("one", 1, ["⊢ A"], "x", ["⊢ B"]),
                _step("two", 1, ["⊢ B"], "y", []),
                _footer("A", 2),
            ],
            "missing its footer before",
        ),
        (
            [_step("wrong-count", 1, ["⊢ A"], "x", []), _footer("A", 2)],
            "footer tactic_count",
        ),
        (
            [_step("open-qed", 1, ["⊢ A"], "x", ["⊢ B"]), _footer("A", 1)],
            "qed footer requires",
        ),
        (
            [_step("wrong-theorem", 1, ["⊢ A"], "x", []), _footer("B", 1)],
            "footer theorem does not match",
        ),
    ],
)
def test_rejects_incomplete_or_ambiguous_session_structure(
    tmp_path: Path, records: list[dict[str, object]], message: str
) -> None:
    raw = _write(tmp_path / "bad-session.jsonl", records)
    with pytest.raises(exporter.TraceFormatError, match=message):
        exporter.load_trace_file(raw)


def test_rejects_dirty_jsonl_and_duplicate_session_ids(tmp_path: Path) -> None:
    no_newline = tmp_path / "partial.jsonl"
    no_newline.write_text(json.dumps(_valid_records()[0]), encoding="utf-8")
    with pytest.raises(exporter.TraceFormatError, match="missing final newline"):
        exporter.load_trace_file(no_newline)

    blank = tmp_path / "blank.jsonl"
    blank.write_text("\n", encoding="utf-8")
    with pytest.raises(exporter.TraceFormatError, match="blank lines"):
        exporter.load_trace_file(blank)

    duplicate_key = tmp_path / "duplicate-key.jsonl"
    duplicate_key.write_text(
        '{"v": 1, "v": 1, "session": "s", "step": 1}\n',
        encoding="utf-8",
    )
    with pytest.raises(exporter.TraceFormatError, match="duplicate JSON key"):
        exporter.load_trace_file(duplicate_key)

    unsafe = _valid_records()
    unsafe[0] = {**unsafe[0], "tactic": "refl\u202e"}
    unsafe_path = _write(tmp_path / "unsafe.jsonl", unsafe)
    with pytest.raises(exporter.TraceFormatError, match="control-free"):
        exporter.load_trace_file(unsafe_path)

    first = _write(tmp_path / "first.jsonl", _valid_records("same"))
    second = _write(tmp_path / "second.jsonl", _valid_records("same"))
    with pytest.raises(exporter.TraceFormatError, match="duplicate session id"):
        exporter.load_sessions([first, second])


def _corpus_files(tmp_path: Path) -> tuple[Path, Path]:
    first = _write(
        tmp_path / "part-a.jsonl",
        [
            _step("alpha-1", 1, ["⊢ A"], "prepare a", ["⊢ Shared"]),
            _step("alpha-1", 2, ["⊢ Shared"], "refl", []),
            _footer("A", 2),
            _step("beta-1", 1, ["⊢ B"], "prepare b", ["⊢ Shared"]),
            # Same semantic transition as alpha-1 step 2: session and step do
            # not participate in dedup identity, even across theorem groups.
            _step("beta-1", 2, ["⊢ Shared"], "refl", []),
            _footer("B", 2),
            _step(
                "gamma-1",
                1,
                ["⊢ C"],
                "refl",
                ["⊢ C"],
                status="error",
                error="the sides differ.",
            ),
            _step("gamma-1", 2, ["⊢ C"], "auto 2", []),
            _footer("C", 2, proof_size=4),
        ],
    )
    second = _write(
        tmp_path / "part-b.jsonl",
        [
            _step("alpha-2", 1, ["⊢ A"], "simp", []),
            _footer("A", 1, proof_size=2),
            _step("delta-1", 1, ["⊢ D"], "exact h", []),
            _footer("D", 1),
        ],
    )
    return first, second


def test_export_is_deterministic_deduplicated_grouped_and_statistically_complete(
    tmp_path: Path,
) -> None:
    first, second = _corpus_files(tmp_path)
    out_one = tmp_path / "one"
    out_two = tmp_path / "two"

    result = exporter.export_traces(
        [first, second], out_one, val_fraction=0.5, seed="fixed"
    )
    exporter.export_traces(
        [second, first], out_two, val_fraction=0.5, seed="fixed"
    )

    for filename in ("train.jsonl", "val.jsonl", "stats.json"):
        assert (out_one / filename).read_bytes() == (out_two / filename).read_bytes()

    train = _read_jsonl(result.train_path)
    val = _read_jsonl(result.val_path)
    all_rows = train + val
    assert len(all_rows) == 7
    assert all(list(row) == list(exporter.STEP_FIELDS) for row in all_rows)
    assert {_semantic(row) for row in train}.isdisjoint({_semantic(row) for row in val})

    # Every retained session belongs to exactly the theorem split reported in
    # stats; both A sessions consequently remain on one side of the boundary.
    session_theorems = {
        "alpha-1": "A",
        "alpha-2": "A",
        "beta-1": "B",
        "gamma-1": "C",
        "delta-1": "D",
    }
    train_theorems = set(result.stats["theorem_coverage"]["train"])
    val_theorems = set(result.stats["theorem_coverage"]["val"])
    assert train_theorems.isdisjoint(val_theorems)
    assert train_theorems | val_theorems == {"A", "B", "C", "D"}
    assert all(session_theorems[row["session"]] in train_theorems for row in train)
    assert all(session_theorems[row["session"]] in val_theorems for row in val)

    stats = result.stats
    assert stats["source"]["sessions"] == 5
    assert stats["source"]["transitions"] == 8
    assert stats["deduplication"] == {
        "eligible_transitions": 8,
        "unique_transitions": 7,
        "duplicates_removed": 1,
        "identity": "v+goals_before+focus+tactic+goals_after+status+error",
    }
    assert stats["outcomes"] == {
        "ok": 6,
        "error": 1,
        "total": 7,
        "failure_ratio": 1 / 7,
    }
    assert stats["tactic_distribution"] == {
        "auto 2": 1,
        "exact h": 1,
        "prepare a": 1,
        "prepare b": 1,
        "refl": 2,
        "simp": 1,
    }
    assert stats["splits"]["train"]["records"] == len(train)
    assert stats["splits"]["val"]["records"] == len(val)


def test_exact_theorem_exclusion_filters_whole_sessions_and_is_reported(
    tmp_path: Path,
) -> None:
    first, second = _corpus_files(tmp_path)
    result = exporter.export_traces(
        [first, second],
        tmp_path / "out",
        val_fraction=0.0,
        exclude_theorems={"A", "not present"},
    )

    rows = _read_jsonl(result.train_path)
    assert {row["session"] for row in rows}.isdisjoint({"alpha-1", "alpha-2"})
    assert result.val_path.read_text(encoding="utf-8") == ""
    assert result.stats["exclusions"] == {
        "requested_theorems": ["A", "not present"],
        "matched_theorems": ["A"],
        "sessions": 2,
        "transitions": 3,
    }
    assert result.stats["theorem_coverage"]["eligible"] == ["B", "C", "D"]


def test_export_rejects_unsafe_seed_and_never_overwrites_an_input_artifact(
    tmp_path: Path,
) -> None:
    unsafe_seed = _write(tmp_path / "raw.jsonl", _valid_records())
    with pytest.raises(ValueError, match="seed must be non-empty control-free text"):
        exporter.export_traces(
            [unsafe_seed], tmp_path / "unsafe-out", seed="split\npoison"
        )
    assert not (tmp_path / "unsafe-out").exists()

    aliased_input = _write(tmp_path / "train.jsonl", _valid_records("source"))
    original = aliased_input.read_bytes()
    with pytest.raises(ValueError, match="refusing to overwrite input trace file"):
        exporter.export_traces([aliased_input], tmp_path)
    assert aliased_input.read_bytes() == original
    assert not (tmp_path / "val.jsonl").exists()
    assert not (tmp_path / "stats.json").exists()


def test_export_rejects_existing_filesystem_alias_of_an_input(tmp_path: Path) -> None:
    source = _write(tmp_path / "source.jsonl", _valid_records("source"))
    destination = tmp_path / "aliased-output"
    destination.mkdir()
    train_alias = destination / "train.jsonl"
    os.link(source, train_alias)
    original = source.read_bytes()

    with pytest.raises(ValueError, match="refusing to overwrite input trace file"):
        exporter.export_traces([source], destination)

    assert source.read_bytes() == original
    assert train_alias.read_bytes() == original
    assert not (destination / "val.jsonl").exists()
    assert not (destination / "stats.json").exists()


def test_export_preflights_outputs_and_rolls_back_a_publish_failure(
    tmp_path: Path, monkeypatch
) -> None:
    raw = _write(tmp_path / "raw.jsonl", _valid_records("source"))
    destination = tmp_path / "out"
    destination.mkdir()
    train = destination / "train.jsonl"
    val = destination / "val.jsonl"
    stats = destination / "stats.json"
    train.write_text("old train\n", encoding="utf-8")
    val.mkdir()
    stats.write_text("old stats\n", encoding="utf-8")

    with pytest.raises(ValueError, match="regular file or absent"):
        exporter.export_traces([raw], destination)
    assert train.read_text(encoding="utf-8") == "old train\n"
    assert val.is_dir()
    assert stats.read_text(encoding="utf-8") == "old stats\n"

    val.rmdir()
    val.write_text("old val\n", encoding="utf-8")
    old = {path: path.read_bytes() for path in (train, val, stats)}
    real_replace = exporter.os.replace
    failed = False

    def fail_second_publish(source, target):
        nonlocal failed
        source_path, target_path = Path(source), Path(target)
        if (
            not failed
            and target_path == val
            and source_path.suffix == ".tmp"
        ):
            failed = True
            raise OSError("planned second-artifact failure")
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", fail_second_publish)
    with pytest.raises(OSError, match="planned second-artifact failure"):
        exporter.export_traces([raw], destination)

    assert failed
    assert {path: path.read_bytes() for path in (train, val, stats)} == old
    assert not list(destination.glob(".*.tmp"))
    assert not list(destination.glob(".*.bak"))


def test_export_preserves_backup_if_rollback_itself_fails(
    tmp_path: Path, monkeypatch
) -> None:
    raw = _write(tmp_path / "raw.jsonl", _valid_records("source"))
    destination = tmp_path / "out"
    destination.mkdir()
    artifacts = tuple(destination / name for name in ("train.jsonl", "val.jsonl", "stats.json"))
    for path in artifacts:
        path.write_text(f"old {path.name}\n", encoding="utf-8")
    old_train = artifacts[0].read_bytes()
    real_replace = exporter.os.replace
    publish_failed = False
    restore_failed = False

    def fail_publish_and_one_restore(source, target):
        nonlocal publish_failed, restore_failed
        source_path, target_path = Path(source), Path(target)
        if (
            not publish_failed
            and target_path == artifacts[1]
            and source_path.suffix == ".tmp"
        ):
            publish_failed = True
            raise OSError("planned publish failure")
        if (
            publish_failed
            and not restore_failed
            and target_path == artifacts[0]
            and source_path.suffix == ".bak"
        ):
            restore_failed = True
            raise RuntimeError("planned restore failure")
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", fail_publish_and_one_restore)
    with pytest.raises(RuntimeError, match="backups preserved at"):
        exporter.export_traces([raw], destination)

    train_backups = list(destination.glob(".train.jsonl.*.bak"))
    assert publish_failed and restore_failed
    assert len(train_backups) == 1
    assert train_backups[0].read_bytes() == old_train


def test_export_rolls_back_interrupts_after_completed_filesystem_moves(
    tmp_path: Path, monkeypatch
) -> None:
    raw = _write(tmp_path / "raw.jsonl", _valid_records("source"))
    real_replace = exporter.os.replace

    backup_dir = tmp_path / "backup-window"
    backup_dir.mkdir()
    old_artifacts = tuple(
        backup_dir / name for name in ("train.jsonl", "val.jsonl", "stats.json")
    )
    for path in old_artifacts:
        path.write_text(f"old {path.name}\n", encoding="utf-8")
    originals = {path: path.read_bytes() for path in old_artifacts}
    interrupted = False

    def interrupt_after_backup_move(source, target):
        nonlocal interrupted
        source_path, target_path = Path(source), Path(target)
        if not interrupted and source_path == old_artifacts[0] and target_path.suffix == ".bak":
            real_replace(source, target)
            interrupted = True
            raise KeyboardInterrupt("planned post-backup interrupt")
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", interrupt_after_backup_move)
    with pytest.raises(KeyboardInterrupt, match="post-backup"):
        exporter.export_traces([raw], backup_dir)
    assert interrupted
    assert {path: path.read_bytes() for path in old_artifacts} == originals
    assert not list(backup_dir.glob(".*.tmp"))
    assert not list(backup_dir.glob(".*.bak"))

    install_dir = tmp_path / "install-window"
    train = install_dir / "train.jsonl"
    interrupted = False

    def interrupt_after_install_move(source, target):
        nonlocal interrupted
        source_path, target_path = Path(source), Path(target)
        if not interrupted and target_path == train and source_path.suffix == ".tmp":
            real_replace(source, target)
            interrupted = True
            raise KeyboardInterrupt("planned post-install interrupt")
        return real_replace(source, target)

    monkeypatch.setattr(exporter.os, "replace", interrupt_after_install_move)
    with pytest.raises(KeyboardInterrupt, match="post-install"):
        exporter.export_traces([raw], install_dir)
    assert interrupted
    assert not any(
        (install_dir / name).exists()
        for name in ("train.jsonl", "val.jsonl", "stats.json")
    )
    assert not list(install_dir.glob(".*.tmp"))
    assert not list(install_dir.glob(".*.bak"))


def test_export_cleans_staged_file_when_fsync_fails(
    tmp_path: Path, monkeypatch
) -> None:
    raw = _write(tmp_path / "raw.jsonl", _valid_records("source"))
    destination = tmp_path / "out"

    def fail_fsync(descriptor):
        del descriptor
        raise OSError("planned fsync failure")

    monkeypatch.setattr(exporter.os, "fsync", fail_fsync)
    with pytest.raises(OSError, match="planned fsync failure"):
        exporter.export_traces([raw], destination)

    assert not list(destination.glob(".*.tmp"))
    assert not list(destination.glob(".*.bak"))
    assert not any((destination / name).exists() for name in ("train.jsonl", "val.jsonl", "stats.json"))


def test_cli_writes_three_artifacts_and_malformed_input_writes_nothing(
    tmp_path: Path,
) -> None:
    raw = _write(
        tmp_path / "raw.jsonl",
        _valid_records("one", "0 = 0") + _valid_records("two", "S 0 = S 0"),
    )
    destination = tmp_path / "export"
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(raw),
            "--output-dir",
            str(destination),
            "--val-fraction",
            "0.5",
            "--seed",
            "cli-test",
            "--exclude-theorem",
            "absent",
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "exported 2 unique transitions" in result.stdout
    assert {path.name for path in destination.iterdir()} == {
        "train.jsonl",
        "val.jsonl",
        "stats.json",
    }

    malformed = tmp_path / "malformed.jsonl"
    malformed.write_text("not json\n", encoding="utf-8")
    failed_destination = tmp_path / "failed"
    failed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(malformed),
            "--output-dir",
            str(failed_destination),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert failed.returncode == 2
    assert "trace export failed:" in failed.stderr
    assert not failed_destination.exists()

    looping_input = tmp_path / "loop.jsonl"
    looping_input.symlink_to(looping_input.name)
    looped = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            str(looping_input),
            "--output-dir",
            str(tmp_path / "loop-output"),
        ],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert looped.returncode == 2
    assert "trace export failed:" in looped.stderr
    assert "Traceback" not in looped.stderr
