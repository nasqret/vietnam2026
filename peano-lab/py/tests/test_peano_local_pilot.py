"""Model-free tests for the three-hour local MPS pilot path."""

from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
TRAINER_PATH = REPOSITORY_ROOT / "scripts/train_peano_local_pilot.py"
INTERFACE_PATH = REPOSITORY_ROOT / "scripts/peano_local_pilot.py"
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))


def _load(name: str, path: Path):  # type: ignore[no-untyped-def]
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


TRAINER = _load("_local_pilot_trainer_test", TRAINER_PATH)
INTERFACE = _load("_local_pilot_interface_test", INTERFACE_PATH)


def test_import_and_help_do_not_import_ml_packages() -> None:
    code = "\n".join(
        (
            "import importlib.util, pathlib, sys",
            f"paths = {[str(TRAINER_PATH), str(INTERFACE_PATH)]!r}",
            "for i, raw in enumerate(paths):",
            " p = pathlib.Path(raw)",
            " s = importlib.util.spec_from_file_location(f'_pilot_{i}', p)",
            " m = importlib.util.module_from_spec(s)",
            " sys.modules[s.name] = m",
            " s.loader.exec_module(m)",
            " try: m._parser().parse_args(['--help'])",
            " except SystemExit as exc: assert exc.code == 0",
            "assert 'torch' not in sys.modules",
            "assert 'transformers' not in sys.modules",
            "assert 'peft' not in sys.modules",
        )
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert "--max-wall-minutes" in completed.stdout
    assert "--next-tactic" in completed.stdout


def test_trainer_defaults_are_the_bounded_deadline_regime() -> None:
    args = TRAINER._parser().parse_args([])
    config = TRAINER._validate_args(args)

    assert args.snapshot == TRAINER.DEFAULT_SNAPSHOT
    assert args.output == TRAINER.DEFAULT_OUTPUT
    assert config.device == "mps"
    assert config.max_steps == 200
    assert config.max_wall_minutes == 145.0
    assert config.max_length == 1024
    assert config.gradient_accumulation_steps == 8
    assert config.rank == 8
    assert config.alpha == 16
    assert TRAINER.TARGET_MODULES == (
        "q_proj",
        "v_proj",
        "o_proj",
        "gate_proj",
        "up_proj",
        "down_proj",
    )


@pytest.mark.parametrize(
    ("option", "value"),
    (
        ("--max-steps", "0"),
        ("--max-wall-minutes", "nan"),
        ("--max-length", "64"),
        ("--gradient-accumulation-steps", "0"),
        ("--learning-rate", "-1"),
        ("--dropout", "1"),
    ),
)
def test_trainer_rejects_unbounded_or_invalid_controls(
    option: str, value: str
) -> None:
    with pytest.raises(ValueError):
        TRAINER._validate_args(TRAINER._parser().parse_args([option, value]))


def _fake_snapshot(tmp_path: Path) -> Path:
    cache = tmp_path / "models--Qwen--Qwen3-0.6B"
    blobs = cache / "blobs"
    snapshot = cache / "snapshots" / TRAINER.MODEL_REVISION
    blobs.mkdir(parents=True)
    snapshot.mkdir(parents=True)
    payloads = {
        "config.json": b"{}\n",
        "model.safetensors": b"safe-fake-model",
        "tokenizer.json": b"{}\n",
        "tokenizer_config.json": b"{}\n",
    }
    for index, (name, payload) in enumerate(payloads.items()):
        blob = blobs / f"blob-{index}"
        blob.write_bytes(payload)
        os.symlink(f"../../blobs/{blob.name}", snapshot / name)
    return snapshot


def test_snapshot_identity_binds_links_and_resolved_bytes(tmp_path: Path) -> None:
    snapshot = _fake_snapshot(tmp_path)
    first = TRAINER.snapshot_identity(snapshot)

    assert first["model_id"] == "Qwen/Qwen3-0.6B"
    assert first["revision"] == TRAINER.MODEL_REVISION
    assert first["files"]["model.safetensors"]["link"].startswith("../../blobs/")
    assert len(first["sha256"]) == 64

    (snapshot / "model.safetensors").resolve().write_bytes(b"mutated")
    second = TRAINER.snapshot_identity(snapshot)
    assert second["sha256"] != first["sha256"]


def test_snapshot_identity_rejects_cache_escape(tmp_path: Path) -> None:
    snapshot = _fake_snapshot(tmp_path)
    outside = tmp_path / "outside"
    outside.write_text("outside", encoding="utf-8")
    (snapshot / "config.json").unlink()
    os.symlink(outside, snapshot / "config.json")

    with pytest.raises(ValueError, match="absolute|escapes"):
        TRAINER.snapshot_identity(snapshot)


def _write_fake_adapter(tmp_path: Path) -> tuple[Path, dict[str, object]]:
    from training.peano_policy.contract import environment_record, model_v2_environment
    from training.peano_policy.manifest import (
        artifact_directory_hash,
        sha256_file,
        sha256_json,
    )

    snapshot = _fake_snapshot(tmp_path)
    root = tmp_path / "results" / "pilot"
    adapter = root / "adapter"
    tokenizer = root / "tokenizer"
    adapter.mkdir(parents=True)
    tokenizer.mkdir()
    (adapter / "adapter_model.safetensors").write_bytes(b"fake-safe-adapter")
    (adapter / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    (tokenizer / "tokenizer.json").write_text("{}\n", encoding="utf-8")
    relative = TRAINER_PATH.relative_to(REPOSITORY_ROOT).as_posix()
    source_files = {relative: sha256_file(TRAINER_PATH)}
    manifest: dict[str, object] = {
        "format": TRAINER.FORMAT,
        "v": TRAINER.VERSION,
        "status": "complete",
        "base_model": TRAINER.snapshot_identity(snapshot),
        "dataset": {
            "environment": environment_record(model_v2_environment()),
            "builder_manifest": {"sha256": "b" * 64},
        },
        "source": {
            "files": source_files,
            "sha256": sha256_json(source_files),
        },
        "run": {"completed_optimizer_steps": 1},
        "adapter": artifact_directory_hash(root, "adapter"),
        "tokenizer": artifact_directory_hash(root, "tokenizer"),
    }
    (root / TRAINER.MANIFEST_NAME).write_text(
        json.dumps(manifest, sort_keys=True), encoding="utf-8"
    )
    return root, manifest


def test_loader_validates_custom_manifest_without_loading_weights(
    tmp_path: Path,
) -> None:
    root, manifest = _write_fake_adapter(tmp_path)
    validated = INTERFACE.validate_local_adapter(root)

    assert validated["root"] == root.resolve()
    assert validated["manifest"] == manifest
    assert "torch" not in INTERFACE.validate_local_adapter.__code__.co_names

    (root / "adapter/adapter_model.safetensors").write_bytes(b"mutated")
    with pytest.raises(ValueError, match="hash mismatch"):
        INTERFACE.validate_local_adapter(root)


def test_loader_rejects_duplicate_manifest_keys(tmp_path: Path) -> None:
    root = tmp_path / "adapter"
    root.mkdir()
    (root / TRAINER.MANIFEST_NAME).write_text(
        '{"format":"first","format":"second"}\n', encoding="utf-8"
    )
    with pytest.raises(ValueError, match="duplicate manifest key"):
        INTERFACE._read_manifest(root)


def test_initial_state_and_cli_are_connected_to_existing_search() -> None:
    assert INTERFACE._initial_goals("forall n. n = n") == ("⊢ ∀ x. x = x",)
    source = INTERFACE_PATH.read_text(encoding="utf-8")
    assert "PeanoPolicyCandidateAdapter" in source
    assert "training.peano_policy.search" in source
    assert "run_checked_search" in source
    assert "save_attempt" in source
    assert "KERNEL CHECKED PROOF" in source


def test_learning_rate_schedule_is_warm_then_cosine() -> None:
    config = TRAINER._validate_args(TRAINER._parser().parse_args([]))
    assert TRAINER._learning_rate_scale(0, config) == pytest.approx(0.1)
    assert TRAINER._learning_rate_scale(9, config) == pytest.approx(1.0)
    assert TRAINER._learning_rate_scale(config.max_steps, config) == pytest.approx(0.0)
