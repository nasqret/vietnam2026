"""Focused tests for deterministic M9 batch trace generation."""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

from peano_lab.library.theorems import THEOREMS


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "generate_peano_traces.py"
SPEC = importlib.util.spec_from_file_location("generate_peano_traces", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
generator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = generator
SPEC.loader.exec_module(generator)


STEP_KEYS = [
    "v",
    "session",
    "step",
    "goals_before",
    "focus",
    "tactic",
    "goals_after",
    "status",
    "error",
]
FOOTER_KEYS = ["qed", "theorem", "proof_size", "tactic_count"]


def _run(config, *, theorems=THEOREMS[:2]):
    stream = io.StringIO()
    manifest = generator.generate(stream, config, theorems=theorems)
    return stream.getvalue(), manifest


def _sessions(raw: str) -> list[list[dict]]:
    sessions: list[list[dict]] = []
    current: list[dict] = []
    for line in raw.splitlines():
        record = json.loads(line)
        current.append(record)
        if "qed" in record:
            sessions.append(current)
            current = []
    assert current == []
    return sessions


def _semantic_tree() -> tuple[int, str]:
    digest = hashlib.sha256()
    sources = sorted((ROOT / "peano-lab" / "py" / "peano_lab").rglob("*.py"))
    for path in sources:
        relative = path.relative_to(ROOT).as_posix().encode("utf-8")
        digest.update(len(relative).to_bytes(4, "big"))
        digest.update(relative)
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return len(sources), digest.hexdigest()


def test_generation_is_seed_deterministic_and_preserves_exact_v1_records() -> None:
    config = generator.GenerationConfig(
        seed=17,
        renamed=3,
        commuted=0,
        auto_depth=5,
        auto_max_nodes=100,
    )
    raw, manifest = _run(config)
    repeated_raw, repeated_manifest = _run(config)

    assert raw == repeated_raw
    assert manifest == repeated_manifest
    assert manifest["format"] == generator.MANIFEST_FORMAT
    assert manifest["version"] == 1
    assert manifest["trace_version"] == 1
    assert manifest["provenance"]["sources"] == {
        "generator": {
            "path": "scripts/generate_peano_traces.py",
            "sha256": hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),
        },
        "trusted_checker": {
            "path": "peano-lab/py/peano_lab/kernel/checker.py",
            "sha256": hashlib.sha256(
                (
                    ROOT
                    / "peano-lab"
                    / "py"
                    / "peano_lab"
                    / "kernel"
                    / "checker.py"
                ).read_bytes()
            ).hexdigest(),
        },
    }
    tree_files, tree_sha256 = _semantic_tree()
    assert manifest["provenance"]["semantic_source_tree"] == {
        "root": "peano-lab/py/peano_lab",
        "pattern": "**/*.py",
        "files": tree_files,
        "sha256": tree_sha256,
    }
    assert manifest["raw"] == {
        "encoding": "utf-8",
        "bytes": len(raw.encode("utf-8")),
        "sha256": hashlib.sha256(raw.encode("utf-8")).hexdigest(),
    }

    class ShortSink:
        def __init__(self) -> None:
            self.accepted = ""

        def write(self, text: str) -> int:
            count = len(text) // 2
            self.accepted += text[:count]
            return count

    short = ShortSink()
    digesting = generator._DigestingSink(short)
    with pytest.raises(generator.GenerationError, match="short write"):
        digesting.write("complete record")
    assert short.accepted == "complet"
    assert digesting.bytes_written == 0
    assert digesting.digest.hexdigest() == hashlib.sha256(b"").hexdigest()

    sessions = _sessions(raw)
    assert len(sessions) == 2 + 2 + 3
    for records in sessions:
        steps, footer = records[:-1], records[-1]
        assert list(footer) == FOOTER_KEYS
        assert [record["step"] for record in steps] == list(
            range(1, len(steps) + 1)
        )
        assert all(list(record) == STEP_KEYS for record in steps)
        assert all(record["v"] == 1 for record in steps)
        assert all(record["session"] == steps[0]["session"] for record in steps)
        for record in steps:
            if record["status"] == "error":
                assert record["goals_after"] == record["goals_before"]
                assert record["error"]

    assert [session[-1]["qed"] for session in sessions] == [
        entry["kernel_checked"] for entry in manifest["sessions"]
    ]
    assert all(
        entry["kernel_checked"]
        for entry in manifest["sessions"]
        if entry["kind"] in {"ladder_script", "variant_renamed"}
    )
    assert all(entry["controlled_failures"] == 1 for entry in manifest["sessions"])
    assert {
        entry["target_mode"] for entry in manifest["sessions"]
    } == {
        "original_statement",
        "dependency_curried_statement",
        "generated_statement",
    }


def test_seed_changes_names_order_session_ids_and_raw_digest() -> None:
    base = dict(
        renamed=4,
        commuted=1,
        auto_depth=5,
        auto_max_nodes=5_000,
        ladder_auto=False,
        ladder_scripts=False,
    )
    raw_a, manifest_a = _run(generator.GenerationConfig(seed=1, **base))
    raw_b, manifest_b = _run(generator.GenerationConfig(seed=2, **base))

    assert raw_a != raw_b
    assert manifest_a["raw"]["sha256"] != manifest_b["raw"]["sha256"]
    assert manifest_a["sessions"] != manifest_b["sessions"]


def test_session_ids_include_the_full_run_identity_not_only_the_seed() -> None:
    common = dict(
        auto_depth=5,
        auto_max_nodes=5_000,
        ladder_auto=False,
        ladder_scripts=False,
    )
    raw_a, manifest_a = _run(
        generator.GenerationConfig(seed=0, renamed=1, commuted=0, **common)
    )
    raw_b, manifest_b = _run(
        generator.GenerationConfig(seed=0, renamed=0, commuted=1, **common)
    )
    raw_wrapped, manifest_wrapped = _run(
        generator.GenerationConfig(seed=2**64, renamed=1, commuted=0, **common)
    )

    session_sets = [
        {session[0]["session"] for session in _sessions(raw)}
        for raw in (raw_a, raw_b, raw_wrapped)
    ]
    assert session_sets[0].isdisjoint(session_sets[1])
    assert session_sets[0].isdisjoint(session_sets[2])
    assert len(
        {
            manifest_a["run_fingerprint"],
            manifest_b["run_fingerprint"],
            manifest_wrapped["run_fingerprint"],
        }
    ) == 3


def test_ladder_families_can_be_disabled_for_a_leakage_safe_release() -> None:
    config = generator.GenerationConfig(
        seed=9,
        renamed=2,
        commuted=1,
        auto_depth=5,
        auto_max_nodes=5_000,
        ladder_auto=False,
        ladder_scripts=False,
    )
    raw, manifest = _run(config)

    assert raw
    assert manifest["counts"]["sessions_by_kind"] == {
        "variant_commuted": 1,
        "variant_renamed": 2,
    }
    assert all(entry["theorem"] is None for entry in manifest["sessions"])
    commuted = next(
        entry for entry in manifest["sessions"] if entry["kind"] == "variant_commuted"
    )
    assert commuted["family"] == "add_comm"
    assert commuted["template"] in {"add_comm_forward", "add_comm_reversed"}


def test_honest_auto_sweep_covers_every_ladder_statement_and_keeps_failures() -> None:
    config = generator.GenerationConfig(
        seed=3,
        renamed=0,
        commuted=0,
        auto_depth=1,
        auto_max_nodes=1,
        ladder_auto=True,
        ladder_scripts=False,
    )
    raw, manifest = _run(config, theorems=THEOREMS)
    sessions = _sessions(raw)

    assert manifest["theorem_ladder"] == [spec.name for spec in THEOREMS]
    assert manifest["counts"]["sessions_by_kind"] == {
        "ladder_auto": len(THEOREMS)
    }
    assert len(sessions) == len(THEOREMS)
    assert [entry["family"] for entry in manifest["sessions"]] == [
        spec.name for spec in THEOREMS
    ]
    assert all(entry["result"] == "search_failure" for entry in manifest["sessions"])
    assert all(session[-1]["qed"] is False for session in sessions)
    assert all(
        any(record.get("tactic") == "auto 1" for record in session[:-1])
        for session in sessions
    )


def test_default_renamed_scale_exceeds_ten_thousand_deduplicated_transitions() -> None:
    sample_size = 20
    config = generator.GenerationConfig(
        seed=101,
        renamed=sample_size,
        commuted=0,
        auto_depth=5,
        auto_max_nodes=5_000,
        ladder_auto=False,
        ladder_scripts=False,
    )
    raw, manifest = _run(config)
    transitions = [
        record
        for session in _sessions(raw)
        for record in session[:-1]
    ]

    # Match the exporter's session-agnostic transition identity.  Unique
    # seeded surface names occur in the tactic/error or canonical goal fields.
    fingerprints = {
        json.dumps(
            {key: value for key, value in record.items() if key not in {"session", "step"}},
            ensure_ascii=False,
            sort_keys=True,
        )
        for record in transitions
    }
    assert len(fingerprints) == len(transitions)
    records_per_variant = manifest["counts"]["transition_records"] // sample_size
    assert records_per_variant >= 7
    assert generator.DEFAULT_RENAMED * records_per_variant >= 10_000


def test_kernel_rejection_can_never_emit_a_success_footer(monkeypatch) -> None:
    config = generator.GenerationConfig(
        seed=5,
        renamed=1,
        commuted=0,
        ladder_auto=False,
        ladder_scripts=False,
    )
    stream = io.StringIO()

    def reject(*args, **kwargs):
        raise generator.InvalidProof("planned kernel rejection")

    monkeypatch.setattr(generator, "checked_final", reject)
    with pytest.raises(generator.GenerationError, match="kernel rejected"):
        generator.generate(stream, config, theorems=THEOREMS[:1])

    records = [json.loads(line) for line in stream.getvalue().splitlines()]
    assert records
    assert not any(record.get("qed") is True for record in records)


def test_cli_writes_raw_and_separate_manifest(tmp_path: Path, capsys) -> None:
    raw_path = tmp_path / "raw.jsonl"
    status = generator.main(
        [
            "--output",
            str(raw_path),
            "--seed",
            "12",
            "--renamed",
            "1",
            "--commuted",
            "0",
            "--no-ladder-auto",
            "--no-ladder-scripts",
        ]
    )

    assert status == 0
    manifest_path = Path(str(raw_path) + ".manifest.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw_path.read_text(encoding="utf-8").startswith('{"v": 1,')
    assert manifest["counts"]["sessions"] == 1
    assert "generated" in capsys.readouterr().err


def test_cli_rejects_raw_manifest_collision_without_touching_file(
    tmp_path: Path, capsys
) -> None:
    collision = tmp_path / "same.jsonl"
    collision.write_text("keep me\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        generator.main(
            [
                "--output",
                str(collision),
                "--manifest",
                str(collision),
                "--renamed",
                "0",
                "--commuted",
                "0",
            ]
        )

    assert collision.read_text(encoding="utf-8") == "keep me\n"
    assert "must name different files" in capsys.readouterr().err

    upper = tmp_path / "RAW.JSONL"
    lower = tmp_path / "raw.jsonl"
    with pytest.raises(SystemExit):
        generator.main(
            [
                "--output",
                str(upper),
                "--manifest",
                str(lower),
                "--renamed",
                "0",
                "--commuted",
                "0",
            ]
        )

    assert not upper.exists()
    assert not lower.exists()
    assert "must name different files" in capsys.readouterr().err

    composed = tmp_path / "\u00e9.jsonl"
    decomposed = tmp_path / "e\u0301.jsonl"
    assert composed.name != decomposed.name
    with pytest.raises(SystemExit):
        generator.main(
            [
                "--output",
                str(composed),
                "--manifest",
                str(decomposed),
                "--renamed",
                "0",
                "--commuted",
                "0",
            ]
        )

    assert not composed.exists()
    assert not decomposed.exists()
    assert "must name different files" in capsys.readouterr().err

    container = tmp_path / "artifact"
    child = container / "raw.jsonl"
    for output, manifest in ((child, container), (container, child)):
        with pytest.raises(SystemExit):
            generator.main(
                [
                    "--output",
                    str(output),
                    "--manifest",
                    str(manifest),
                    "--renamed",
                    "0",
                    "--commuted",
                    "0",
                ]
            )
        assert not container.exists()
        assert "must not contain one another" in capsys.readouterr().err


def test_failed_generation_preserves_prior_named_artifacts(
    tmp_path: Path, monkeypatch
) -> None:
    raw_path = tmp_path / "raw.jsonl"
    manifest_path = tmp_path / "manifest.json"
    raw_path.write_text("old raw\n", encoding="utf-8")
    manifest_path.write_text("old manifest\n", encoding="utf-8")

    def fail_after_write(sink, config):
        sink.write("partial raw\n")
        raise generator.GenerationError("planned failure")

    monkeypatch.setattr(generator, "generate", fail_after_write)
    with pytest.raises(generator.GenerationError, match="planned failure"):
        generator.main(
            [
                "--output",
                str(raw_path),
                "--manifest",
                str(manifest_path),
                "--renamed",
                "1",
                "--commuted",
                "0",
                "--no-ladder-auto",
                "--no-ladder-scripts",
            ]
        )

    assert raw_path.read_text(encoding="utf-8") == "old raw\n"
    assert manifest_path.read_text(encoding="utf-8") == "old manifest\n"
    assert not list(tmp_path.glob("*.tmp"))


def test_cli_preflights_and_transactionally_publishes_named_pair(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    raw_path = tmp_path / "raw.jsonl"
    manifest_path = tmp_path / "manifest.json"
    raw_path.write_text("old raw\n", encoding="utf-8")
    manifest_path.mkdir()
    arguments = [
        "--output",
        str(raw_path),
        "--manifest",
        str(manifest_path),
        "--renamed",
        "1",
        "--commuted",
        "0",
        "--no-ladder-auto",
        "--no-ladder-scripts",
    ]

    with pytest.raises(SystemExit):
        generator.main(arguments)
    assert raw_path.read_text(encoding="utf-8") == "old raw\n"
    assert manifest_path.is_dir()
    assert "regular file or absent" in capsys.readouterr().err

    manifest_path.rmdir()
    manifest_path.write_text("old manifest\n", encoding="utf-8")
    originals = {
        raw_path: raw_path.read_bytes(),
        manifest_path: manifest_path.read_bytes(),
    }
    real_replace = generator.os.replace
    failed = False

    def fail_manifest_publish(source, target):
        nonlocal failed
        source_path, target_path = Path(source), Path(target)
        if (
            not failed
            and target_path == manifest_path
            and source_path.suffix == ".tmp"
        ):
            failed = True
            raise OSError("planned manifest publish failure")
        return real_replace(source, target)

    monkeypatch.setattr(generator.os, "replace", fail_manifest_publish)
    with pytest.raises(OSError, match="planned manifest publish failure"):
        generator.main(arguments)

    assert failed
    assert {
        raw_path: raw_path.read_bytes(),
        manifest_path: manifest_path.read_bytes(),
    } == originals
    assert not list(tmp_path.glob("*.tmp"))
    assert not list(tmp_path.glob("*.bak"))


def test_cli_rolls_back_interrupts_after_completed_filesystem_moves(
    tmp_path: Path, monkeypatch
) -> None:
    real_replace = generator.os.replace
    common = [
        "--renamed",
        "1",
        "--commuted",
        "0",
        "--no-ladder-auto",
        "--no-ladder-scripts",
    ]

    backup_dir = tmp_path / "backup-window"
    backup_dir.mkdir()
    raw_path = backup_dir / "raw.jsonl"
    manifest_path = backup_dir / "manifest.json"
    raw_path.write_text("old raw\n", encoding="utf-8")
    manifest_path.write_text("old manifest\n", encoding="utf-8")
    originals = {
        raw_path: raw_path.read_bytes(),
        manifest_path: manifest_path.read_bytes(),
    }
    interrupted = False

    def interrupt_after_backup_move(source, target):
        nonlocal interrupted
        source_path, target_path = Path(source), Path(target)
        if not interrupted and source_path == raw_path and target_path.suffix == ".bak":
            real_replace(source, target)
            interrupted = True
            raise KeyboardInterrupt("planned post-backup interrupt")
        return real_replace(source, target)

    monkeypatch.setattr(generator.os, "replace", interrupt_after_backup_move)
    with pytest.raises(KeyboardInterrupt, match="post-backup"):
        generator.main(
            ["--output", str(raw_path), "--manifest", str(manifest_path), *common]
        )
    assert interrupted
    assert {
        raw_path: raw_path.read_bytes(),
        manifest_path: manifest_path.read_bytes(),
    } == originals
    assert not list(backup_dir.glob(".*.tmp"))
    assert not list(backup_dir.glob(".*.bak"))

    install_dir = tmp_path / "install-window"
    raw_path = install_dir / "raw.jsonl"
    manifest_path = install_dir / "manifest.json"
    interrupted = False

    def interrupt_after_install_move(source, target):
        nonlocal interrupted
        source_path, target_path = Path(source), Path(target)
        if not interrupted and target_path == raw_path and source_path.suffix == ".tmp":
            real_replace(source, target)
            interrupted = True
            raise KeyboardInterrupt("planned post-install interrupt")
        return real_replace(source, target)

    monkeypatch.setattr(generator.os, "replace", interrupt_after_install_move)
    with pytest.raises(KeyboardInterrupt, match="post-install"):
        generator.main(
            ["--output", str(raw_path), "--manifest", str(manifest_path), *common]
        )
    assert interrupted
    assert not raw_path.exists()
    assert not manifest_path.exists()
    assert not list(install_dir.glob(".*.tmp"))
    assert not list(install_dir.glob(".*.bak"))


@pytest.mark.parametrize(
    "kwargs, message",
    [
        ({"renamed": -1}, "renamed"),
        ({"commuted": -1}, "commuted"),
        ({"auto_depth": 0}, "auto_depth"),
        ({"auto_max_nodes": 0}, "auto_max_nodes"),
        ({"ladder_auto": 1}, "switches"),
    ],
)
def test_invalid_generation_config_is_rejected(kwargs, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        generator.GenerationConfig(**kwargs)
