"""QED-only, replay-validated next-tactic dataset compilation."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

from peano_lab.batch import capability_sha256, run_proof
from peano_lab.ui.prove import SurfaceCapabilities


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY_ROOT / "scripts" / "build_peano_policy_dataset.py"


def _load_builder():
    spec = importlib.util.spec_from_file_location("_test_policy_dataset_builder", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


builder = _load_builder()


def _session(
    session_id: str,
    theorem: str,
    tactics: tuple[str, ...],
    *,
    on_error: str = "stop",
) -> list[dict[str, object]]:
    result = run_proof(
        theorem,
        tactics,
        request_id=session_id,
        session_id=session_id,
        on_error=on_error,  # type: ignore[arg-type]
    )
    assert result.trace is not None
    return [dict(record) for record in result.trace]


def _write_jsonl(path: Path, records: list[dict[str, object]]) -> Path:
    path.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in records
        ),
        encoding="utf-8",
    )
    return path


def _metadata(
    session: str,
    theorem: str,
    family: str,
    lineage: str,
    *,
    classical: bool = False,
    capabilities: SurfaceCapabilities | None = None,
    **extra: object,
) -> dict[str, object]:
    capabilities = capabilities or SurfaceCapabilities()
    capability_record = {
        "label": capabilities.label,
        "allowed_commands": (
            None
            if capabilities.allowed_commands is None
            else sorted(capabilities.allowed_commands)
        ),
        "allowed_theorems": (
            None
            if capabilities.allowed_theorems is None
            else sorted(capabilities.allowed_theorems)
        ),
    }
    return {
        "session": session,
        "theorem": theorem,
        "family": family,
        "lineage": lineage,
        "classical": classical,
        "surface": capabilities.label,
        "environment_sha256": capability_sha256(capabilities),
        "capabilities": capability_record,
        **extra,
    }


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _all_rows(result) -> list[dict[str, object]]:
    return [
        *_read_jsonl(result.train_path),
        *_read_jsonl(result.val_path),
        *_read_jsonl(result.test_path),
    ]


def _assert_emitted_rows_replay(rows: list[dict[str, object]]) -> None:
    """Every supervised action must reproduce the following stored state."""

    by_session: dict[str, list[dict[str, object]]] = {}
    for row in rows:
        by_session.setdefault(str(row["session"]), []).append(row)
    for session, session_rows in by_session.items():
        session_rows.sort(key=lambda row: int(row["step"]))
        commands = tuple(
            str(row["completion"])[: -len("</tactic>")]
            for row in session_rows
        )
        replay = run_proof(
            str(session_rows[0]["formula"]),
            commands,
            request_id=f"emitted-{session}",
            session_id=f"emitted-{session}",
        )
        assert replay.status == "proved"
        assert replay.trace is not None
        replay_steps = [record for record in replay.trace if "v" in record]
        assert len(replay_steps) == len(session_rows)
        for row, step in zip(session_rows, replay_steps, strict=True):
            assert step["goals_before"] == row["state"]
            assert step["tactic"] + "</tactic>" == row["completion"]


def test_builds_only_replayed_qed_rows_with_group_splits_and_hashes(
    tmp_path: Path,
) -> None:
    # The first positive session contains a deliberately failing tactic.  Its
    # state is transactional, so removing it leaves the successful proof
    # sequence exactly replayable; it must never become a CE target.
    records = (
        _session(
            "zero",
            "0 = 0",
            ("exact missing", "refl"),
            on_error="continue",
        )
        + _session("one", "1 = 1", ("refl",))
        + _session("two", "2 = 2", ("refl",))
        + _session("false", "0 = S 0", ("refl",))
    )
    raw = _write_jsonl(tmp_path / "raw-v1.jsonl", records)
    original_raw = raw.read_bytes()
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata(
                "zero",
                "zero_refl",
                "reflexivity-zero",
                "generated/schema-zero",
                source="0 = 0",
                difficulty={"depth": 1},
            ),
            _metadata("one", "one_refl", "reflexivity-one", "generated/schema-one"),
            _metadata("two", "two_refl", "reflexivity-two", "generated/schema-two"),
            # Metadata may cover a failed raw session, but that session cannot
            # contribute a positive label.
            _metadata("false", "zero_ne_succ", "negative", "mutated/false"),
        ],
    )

    result = builder.build_dataset(
        [raw],
        metadata,
        tmp_path / "dataset",
        seed="fixed",
        val_fraction=0.34,
        test_fraction=0.34,
    )

    assert raw.read_bytes() == original_raw
    rows = _all_rows(result)
    assert len(rows) == 3
    assert {row["session"] for row in rows} == {"zero", "one", "two"}
    assert all(tuple(row) == builder.ROW_FIELDS for row in rows)
    assert not any("missing" in row["completion"] for row in rows)
    assert {row["completion"] for row in rows} == {"refl</tactic>"}
    assert all(row["task"] == "next_tactic" for row in rows)
    expected_hash = capability_sha256(SurfaceCapabilities())
    assert all(
        row["env"]
        == (
            "peano-lab-v1;surface=full;logic=intuitionistic;"
            f"capability_sha256={expected_hash}"
        )
        for row in rows
    )
    assert all(row["surface"] == "full" for row in rows)
    assert all(row["environment_sha256"] == expected_hash for row in rows)
    assert all(row["classical"] is False for row in rows)
    assert all(
        row["capabilities"]
        == {
            "label": "full",
            "allowed_commands": sorted(builder.FULL_BATCH_COMMANDS),
            "allowed_theorems": sorted(builder.SURFACE_THEOREM_NAMES),
        }
        for row in rows
    )
    assert all(
        row["prompt"].startswith(
            "<task>next_tactic</task>\n"
            "<env>peano-lab-v1;surface=full;logic=intuitionistic;"
            f"capability_sha256={expected_hash}</env>\n"
            "<state>"
        )
        and row["prompt"].endswith("</state>\n<tactic>")
        for row in rows
    )
    zero = next(row for row in rows if row["session"] == "zero")
    assert zero["metadata"] == {
        "difficulty": {"depth": 1},
        "source": "0 = 0",
    }

    split_pairs = {
        split: {
            (row["family"], row["lineage"])
            for row in _read_jsonl(getattr(result, f"{split}_path"))
        }
        for split in ("train", "val", "test")
    }
    assert all(len(split_pairs[split]) == 1 for split in split_pairs)
    assert split_pairs["train"].isdisjoint(split_pairs["val"])
    assert split_pairs["train"].isdisjoint(split_pairs["test"])
    assert split_pairs["val"].isdisjoint(split_pairs["test"])

    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest == result.manifest
    assert manifest["source"]["qed_true_sessions"] == 3
    assert manifest["source"]["qed_false_sessions_ignored"] == 1
    compiler = manifest["source"]["compiler"]
    assert compiler["runtime"]["implementation"] == sys.implementation.name
    assert "peano-lab/py/peano_lab/engine/tactics.py" in compiler["sources"]
    assert compiler["sources"]["scripts/build_peano_policy_dataset.py"][
        "sha256"
    ] == hashlib.sha256(SCRIPT.read_bytes()).hexdigest()
    assert manifest["replay"] == {
        "attempted_qed_sessions": 3,
        "accepted_kernel_checked_sessions": 3,
        "positive_rows": 3,
        "transactional_error_steps_ignored": 1,
    }
    assert manifest["environments"] == [
        {
            "surface": "full",
            "environment_sha256": expected_hash,
            "classical": False,
            "capabilities": {
                "label": "full",
                "allowed_commands": sorted(builder.FULL_BATCH_COMMANDS),
                "allowed_theorems": sorted(builder.SURFACE_THEOREM_NAMES),
            },
            "sessions": 3,
        }
    ]
    for split in ("train", "val", "test"):
        content = getattr(result, f"{split}_path").read_bytes()
        assert manifest["splits"][split]["sha256"] == hashlib.sha256(content).hexdigest()
        assert manifest["splits"][split]["rows"] == 1


def test_split_is_assigned_to_family_lineage_before_session_rows(tmp_path: Path) -> None:
    records = _session("long", "forall n. n = n", ("intro n", "refl"))
    records += _session("short", "0 = 0", ("refl",))
    records += _session("linked", "1 = 1", ("refl",))
    records += _session("held", "2 = 2", ("refl",))
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata("long", "forall_refl", "shared", "one-lineage"),
            # A different lineage still cannot split away from the shared
            # family.  Components close both leak paths before row expansion.
            _metadata("short", "zero_refl", "shared", "two-lineage"),
            # A different family sharing short's lineage joins transitively.
            _metadata("linked", "one_refl", "linked", "two-lineage"),
            _metadata("held", "two_refl", "held", "other-lineage"),
        ],
    )

    result = builder.build_dataset(
        [raw], metadata, tmp_path / "out", val_fraction=0.5, test_fraction=0.0
    )
    session_split = {
        row["session"]: row["split"]
        for row in _all_rows(result)
    }
    assert session_split["long"] == session_split["short"]
    assert session_split["short"] == session_split["linked"]
    assert sum(row["session"] == "long" for row in _all_rows(result)) == 2


def test_identical_canonical_theorems_cannot_cross_splits_with_forged_genealogy(
    tmp_path: Path,
) -> None:
    records = _session("same-a", "forall n. n = n", ("intro a", "refl"))
    records += _session("same-b", "forall n. n = n", ("intro b", "refl"))
    records += _session("other", "0 = 0", ("refl",))
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata("same-a", "same_a", "invented-a", "invented-a"),
            _metadata("same-b", "same_b", "invented-b", "invented-b"),
            _metadata("other", "other", "other", "other"),
        ],
    )

    result = builder.build_dataset(
        [raw], metadata, tmp_path / "out", val_fraction=0.5, test_fraction=0.0
    )
    session_split = {
        row["session"]: row["split"]
        for row in _all_rows(result)
    }
    assert session_split["same-a"] == session_split["same-b"]


def test_identical_policy_prompts_cannot_cross_splits_between_distinct_theorems(
    tmp_path: Path,
) -> None:
    records = _session("direct", "forall n. 0 = 0", ("intro n", "refl"))
    records += _session(
        "reduced",
        "forall n. 0 + 0 = 0",
        ("intro n", "rewrite PA3", "refl"),
    )
    records += _session("other", "1 = 1", ("refl",))
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata("direct", "direct", "invented-a", "invented-a"),
            _metadata("reduced", "reduced", "invented-b", "invented-b"),
            _metadata("other", "other", "other", "other"),
        ],
    )

    result = builder.build_dataset(
        [raw], metadata, tmp_path / "out", val_fraction=0.5, test_fraction=0.0
    )
    rows = _all_rows(result)
    session_split = {row["session"]: row["split"] for row in rows}
    assert session_split["direct"] == session_split["reduced"]

    prompts = {
        split: {
            row["prompt"]
            for row in _read_jsonl(getattr(result, f"{split}_path"))
        }
        for split in ("train", "val", "test")
    }
    assert prompts["train"].isdisjoint(prompts["val"])
    assert prompts["train"].isdisjoint(prompts["test"])
    assert prompts["val"].isdisjoint(prompts["test"])
    assert result.manifest["split"]["method"] == (
        "sha256-ranked-genealogy-formula-prompt-components-v2"
    )


def test_named_intro_labels_and_reachable_later_states_are_preserved(
    tmp_path: Path,
) -> None:
    records = _session("alpha-a", "forall n. n = n", ("intro a", "refl"))
    records += _session("alpha-b", "forall n. n = n", ("intro b", "refl"))
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata("alpha-a", "refl_a", "reflexive", "alpha-a"),
            _metadata("alpha-b", "refl_b", "reflexive", "alpha-b"),
        ],
    )

    result = builder.build_dataset(
        [raw], metadata, tmp_path / "out", val_fraction=0.0, test_fraction=0.0
    )
    rows = _all_rows(result)
    intro_rows = [row for row in rows if row["step"] == 1]
    assert len(intro_rows) == 2
    assert len({row["prompt"] for row in intro_rows}) == 1
    assert {row["completion"] for row in intro_rows} == {
        "intro a</tactic>",
        "intro b</tactic>",
    }

    following = [row for row in rows if row["step"] == 2]
    assert {tuple(row["state"]) for row in following} == {
        ("a : ℕ ⊢ a = a",),
        ("b : ℕ ⊢ b = b",),
    }
    assert result.manifest["prompt"]["binder_policy"] == "exact-authored-binders-v1"
    _assert_emitted_rows_replay(rows)


def test_policy_prompt_focus_is_not_leaked_from_focused_action(tmp_path: Path) -> None:
    records = _session(
        "focused",
        "0 = 0 /\\ 1 = 1",
        ("split", "focus 2 refl", "refl"),
    )
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [_metadata("focused", "pair_refl", "logic", "focused-action")],
    )

    result = builder.build_dataset(
        [raw], metadata, tmp_path / "out", val_fraction=0.0, test_fraction=0.0
    )
    rows = sorted(_all_rows(result), key=lambda row: int(row["step"]))
    assert [row["focus"] for row in rows] == [0, 0, 0]
    assert rows[1]["completion"] == "focus 2 refl</tactic>"
    assert '"focus":0' in rows[1]["prompt"]
    assert '"focus":1' not in rows[1]["prompt"]
    _assert_emitted_rows_replay(rows)


def test_replay_mismatch_aborts_without_publishing_outputs(tmp_path: Path) -> None:
    records = _session("forged", "0 = 0", ("refl",))
    records[0]["tactic"] = "exact missing"
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [_metadata("forged", "forged", "mutation", "forged-lineage")],
    )
    output = tmp_path / "out"

    with pytest.raises(builder.DatasetBuildError, match="failed checked replay"):
        builder.build_dataset([raw], metadata, output)
    assert not output.exists()


def test_declared_theorem_allowlist_is_authoritative_during_replay(
    tmp_path: Path,
) -> None:
    # The raw trace is genuinely kernel-checked under the full surface, but its
    # metadata declares an environment in which add_assoc is unavailable.
    # Replaying under full authority would silently launder this row.
    records = _session(
        "forbidden-library",
        "forall n m k. (n + m) + k = n + (m + k)",
        ("use add_assoc", "exact add_assoc"),
    )
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    restricted = SurfaceCapabilities(
        label="no-library-v1",
        allowed_commands=frozenset({"use", "exact"}),
        allowed_theorems=frozenset(),
    )
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata(
                "forbidden-library",
                "add_assoc",
                "addition",
                "library-replay",
                capabilities=restricted,
            )
        ],
    )

    with pytest.raises(
        builder.DatasetBuildError,
        match="failed checked replay:.*add_assoc.*not available",
    ):
        builder.build_dataset([raw], metadata, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_restricted_capability_and_logic_identity_are_bound_to_every_artifact(
    tmp_path: Path,
) -> None:
    raw = _write_jsonl(
        tmp_path / "raw.jsonl", _session("restricted", "0 = 0", ("refl",))
    )
    restricted = SurfaceCapabilities(
        label="refl-only-v1",
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    environment_sha256 = capability_sha256(restricted)
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [
            _metadata(
                "restricted",
                "zero_refl",
                "reflexive",
                "restricted",
                classical=True,
                capabilities=restricted,
            )
        ],
    )

    result = builder.build_dataset([raw], metadata, tmp_path / "out")
    row = _all_rows(result)[0]
    identity = {
        "label": "refl-only-v1",
        "allowed_commands": ["refl"],
        "allowed_theorems": [],
    }
    assert row["classical"] is True
    assert row["surface"] == "refl-only-v1"
    assert row["environment_sha256"] == environment_sha256
    assert row["capabilities"] == identity
    assert row["env"] == (
        "peano-lab-v1;surface=refl-only-v1;logic=classical;"
        f"capability_sha256={environment_sha256}"
    )
    assert f"<env>{row['env']}</env>" in row["prompt"]
    assert result.manifest["environments"] == [
        {
            "surface": "refl-only-v1",
            "environment_sha256": environment_sha256,
            "classical": True,
            "capabilities": identity,
            "sessions": 1,
        }
    ]


def test_metadata_environment_hash_must_match_exact_capabilities(tmp_path: Path) -> None:
    raw = _write_jsonl(tmp_path / "raw.jsonl", _session("qed", "0 = 0", ("refl",)))
    record = _metadata("qed", "zero_refl", "reflexive", "zero")
    record["environment_sha256"] = "0" * 64
    metadata = _write_jsonl(tmp_path / "metadata.jsonl", [record])

    with pytest.raises(builder.DatasetBuildError, match="does not match declared"):
        builder.build_dataset([raw], metadata, tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_requires_metadata_for_every_qed_but_not_for_qed_false(tmp_path: Path) -> None:
    records = _session("positive", "0 = 0", ("refl",))
    records += _session("negative", "0 = S 0", ("refl",))
    raw = _write_jsonl(tmp_path / "raw.jsonl", records)
    missing = _write_jsonl(
        tmp_path / "missing.jsonl",
        [_metadata("negative", "negative", "negative", "negative")],
    )
    with pytest.raises(builder.DatasetBuildError, match="lack metadata: positive"):
        builder.build_dataset([raw], missing, tmp_path / "missing-out")

    enough = _write_jsonl(
        tmp_path / "enough.jsonl",
        [_metadata("positive", "positive", "positive", "positive")],
    )
    result = builder.build_dataset([raw], enough, tmp_path / "enough-out")
    assert {row["session"] for row in _all_rows(result)} == {"positive"}


def test_publication_failure_restores_previous_coherent_dataset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    raw = _write_jsonl(tmp_path / "raw.jsonl", _session("qed", "0 = 0", ("refl",)))
    metadata = _write_jsonl(
        tmp_path / "metadata.jsonl",
        [_metadata("qed", "zero_refl", "reflexive", "zero")],
    )
    output = tmp_path / "out"
    output.mkdir()
    paths = tuple(output / name for name in ("train.jsonl", "val.jsonl", "test.jsonl", "manifest.json"))
    old = tuple(f"old {index}\n".encode() for index in range(len(paths)))
    for path, payload in zip(paths, old, strict=True):
        path.write_bytes(payload)

    real_replace = builder.os.replace
    calls = 0

    def fail_second_install(source, destination):
        nonlocal calls
        calls += 1
        if calls == 6:  # four backups, first install, then fail
            raise OSError("injected dataset publish failure")
        return real_replace(source, destination)

    monkeypatch.setattr(builder.os, "replace", fail_second_install)
    with pytest.raises(OSError, match="injected dataset"):
        builder.build_dataset(
            [raw], metadata, output, val_fraction=0.0, test_fraction=0.0
        )
    assert tuple(path.read_bytes() for path in paths) == old


def test_cli_reports_malformed_metadata_without_creating_dataset(tmp_path: Path) -> None:
    raw = _write_jsonl(tmp_path / "raw.jsonl", _session("qed", "0 = 0", ("refl",)))
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_text('{"session":"qed"}\n', encoding="utf-8")

    assert builder.main(
        [
            str(raw),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(tmp_path / "out"),
        ]
    ) == 2
    assert not (tmp_path / "out").exists()
