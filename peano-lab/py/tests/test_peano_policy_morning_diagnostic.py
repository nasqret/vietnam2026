from __future__ import annotations

import json
from pathlib import Path

import pytest

import training.peano_policy.morning_diagnostic as diagnostic
from training.peano_policy import generate
from training.peano_policy.manifest import sha256_file, sha256_json, write_manifest


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_catalog_selection_keeps_boundaries_and_one_step_once(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(diagnostic, "EXPECTED_CATALOG_SESSIONS", 2)
    path = tmp_path / "train.jsonl"
    rows = [
        {
            "session": "a",
            "step": step,
            "metadata": {"trajectory": diagnostic.CATALOG_TRAJECTORY},
        }
        for step in (2, 1, 3)
    ]
    rows.extend(
        [
            {
                "session": "b",
                "step": 1,
                "metadata": {"trajectory": diagnostic.CATALOG_TRAJECTORY},
            },
            {
                "session": "synthetic",
                "step": 1,
                "metadata": {"trajectory": "synthetic-root-balanced"},
            },
        ]
    )
    _write_rows(path, rows)

    selected = diagnostic._catalog_boundary_records(path)

    identities = [(row["session"], row["step"]) for _, row in selected]
    assert identities == [("a", 1), ("a", 3), ("b", 1)]


def test_hash_sample_excludes_catalog_and_is_order_independent(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    rows = [
        {
            "session": f"s{index}",
            "step": index + 1,
            "metadata": {
                "trajectory": (
                    diagnostic.CATALOG_TRAJECTORY
                    if index == 0
                    else "synthetic-root-balanced"
                )
            },
        }
        for index in range(8)
    ]
    _write_rows(path, rows)

    selected = diagnostic._hash_sample_records(
        path,
        count=3,
        seed=17,
        exclude_catalog=True,
    )

    assert len(selected) == 3
    assert all(
        row["metadata"]["trajectory"] != diagnostic.CATALOG_TRAJECTORY
        for _, row in selected
    )
    assert len({row["session"] for _, row in selected}) == 3


def test_completed_manifest_contains_selection_and_binds_sidecar(tmp_path: Path) -> None:
    manifest = tmp_path / "training-manifest.json"
    write_manifest(manifest, {"prompt_version": 3, "adapter": {"sha256": "a" * 64}})
    core = {
        "format": diagnostic.FORMAT,
        "v": diagnostic.VERSION,
        "status": "completed-diagnostic-not-production",
        "selection": {"train": {"ordered_example_ids": ["a", "b"]}},
        "sidecar": "morning-diagnostic.json",
    }
    record = {**core, "diagnostic_sha256": sha256_json(core)}

    sidecar, manifest_sha256 = diagnostic._bind_completed_manifest(
        manifest,
        diagnostic=record,
    )

    completed = json.loads(manifest.read_text(encoding="utf-8"))
    receipt = json.loads(sidecar.read_text(encoding="utf-8"))
    assert completed["diagnostic"] == record
    assert completed["diagnostic"]["selection"]["train"]["ordered_example_ids"] == [
        "a",
        "b",
    ]
    assert receipt["diagnostic_sha256"] == record["diagnostic_sha256"]
    assert receipt["training_manifest"]["sha256"] == manifest_sha256
    assert sha256_file(manifest) == manifest_sha256


def test_morning_config_is_bounded_fresh_and_checkpoint_free() -> None:
    root = Path(__file__).resolve().parents[3]
    config = (
        root
        / "training/peano_policy/configs/"
        "qwen3_1_7b_v3_morning_diagnostic_20260731_r1.toml"
    ).read_text(encoding="utf-8")
    sbatch = (
        root / "slurm/peano_wmi_train_v3_morning_diagnostic.sbatch"
    ).read_text(encoding="utf-8")
    assert 'resume = "never"' in config
    assert "max_train_samples = 512" in config
    assert "max_eval_samples = 16" in config
    assert "max_steps = 128" in config
    assert "save_steps = 1000" in config
    assert "#SBATCH --gpus=nvidia_a100:1" in sbatch
    assert "flock -n -s 7" in sbatch
    assert "flock -n -x 8" in sbatch
    assert "forbidden Trainer checkpoint" in sbatch


def test_diagnostic_adapter_requires_explicit_admission() -> None:
    core = {
        "format": diagnostic.FORMAT,
        "v": diagnostic.VERSION,
        "status": "completed-diagnostic-not-production",
    }
    manifest = {
        "diagnostic": {**core, "diagnostic_sha256": sha256_json(core)}
    }
    with pytest.raises(ValueError, match="explicit diagnostic_mode"):
        generate._require_diagnostic_mode(manifest, diagnostic_mode=False)
    admitted = generate._require_diagnostic_mode(manifest, diagnostic_mode=True)
    assert admitted == manifest["diagnostic"]


def test_diagnostic_adapter_rejects_mutated_authority() -> None:
    core = {
        "format": diagnostic.FORMAT,
        "v": diagnostic.VERSION,
        "status": "completed-diagnostic-not-production",
    }
    manifest = {
        "diagnostic": {
            **core,
            "status": "completed-production",
            "diagnostic_sha256": sha256_json(core),
        }
    }
    with pytest.raises(ValueError, match="incomplete or inconsistent"):
        generate._require_diagnostic_mode(manifest, diagnostic_mode=True)
