"""Focused tests for immutable adapter-only model-v3 recovery evidence."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.manifest import sha256_file, write_manifest  # noqa: E402
import training.peano_policy.recovery as recovery  # noqa: E402
from training.peano_policy.recovery import (  # noqa: E402
    AdapterRecoveryCallbackMixin,
    AdapterRecoverySnapshotter,
    RECOVERY_MANIFEST,
    RecoverySnapshotError,
    recovery_snapshot_plan,
    verify_recovery_snapshot,
)


class _AdapterModel:
    def __init__(self, *, fail: bool = False, unsafe: bool = False) -> None:
        self.calls: list[tuple[Path, bool]] = []
        self.fail = fail
        self.unsafe = unsafe

    def save_pretrained(
        self, path: Path, *, safe_serialization: bool
    ) -> None:
        self.calls.append((path, safe_serialization))
        path.mkdir()
        (path / "adapter_config.json").write_text(
            '{"peft_type":"LORA"}\n', encoding="utf-8"
        )
        if self.unsafe:
            (path / "adapter_model.bin").write_bytes(b"unsafe pickle-compatible")
        else:
            (path / "adapter_model.safetensors").write_bytes(b"safe adapter")
        if self.fail:
            raise OSError("simulated interrupted adapter write")


def _identity(output: Path, *, job_id: str = "173200") -> tuple[Path, dict[str, object], str]:
    output.mkdir()
    record: dict[str, object] = {
        "v": 3,
        "config": {"sha256": "a" * 64},
        "model": {"id": "Qwen/Qwen3-1.7B-Base"},
        "source": {"sha256": "b" * 64, "files": {"train.py": "c" * 64}},
        "job": {
            "scheduler": "slurm",
            "job_id": job_id,
            "ledger": {"row_sha256": "d" * 64},
        },
    }
    path = output / "run-identity.json"
    write_manifest(path, record)
    return path, record, sha256_file(path)


def _snapshotter(output: Path) -> tuple[AdapterRecoverySnapshotter, Path, dict[str, object]]:
    identity_path, identity, digest = _identity(output)
    return (
        AdapterRecoverySnapshotter(
            output_dir=output,
            run_identity_path=identity_path,
            run_identity_sha256=digest,
            run_identity=identity,
            expected_optimizer_steps=650,
        ),
        identity_path,
        identity,
    )


def test_recovery_plan_is_bounded_periodic_and_excludes_terminal_step() -> None:
    assert recovery_snapshot_plan(650) == {
        "format": "peano-policy-adapter-recovery-plan",
        "v": 1,
        "artifact": "adapter-safetensors-only",
        "resumable": False,
        "optimizer_state_included": False,
        "interval_optimizer_steps": 100,
        "planned_optimizer_steps": [100, 200, 300, 400, 500, 600],
    }
    assert recovery_snapshot_plan(50)["planned_optimizer_steps"] == [8, 16, 24, 32, 40, 48]
    assert recovery_snapshot_plan(2)["planned_optimizer_steps"] == [1]
    assert recovery_snapshot_plan(1)["planned_optimizer_steps"] == []
    with pytest.raises(ValueError, match="positive optimizer-step"):
        recovery_snapshot_plan(0)


def test_snapshot_is_adapter_only_manifest_last_and_authority_bound(
    tmp_path: Path,
) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, identity = _snapshotter(output)
    model = _AdapterModel()

    assert snapshotter.maybe_save(model, global_step=99) is None
    snapshot = snapshotter.maybe_save(model, global_step=100)
    assert snapshot is not None
    assert snapshot.name.endswith("-job-173200")
    assert len(model.calls) == 1
    assert model.calls[0][0].name == "adapter"
    assert ".partial-" in model.calls[0][0].parent.name
    assert model.calls[0][1] is True
    assert snapshotter.maybe_save(model, global_step=100) is None
    assert len(model.calls) == 1

    record = verify_recovery_snapshot(
        snapshot,
        run_identity_path=identity_path,
        expected_optimizer_steps=650,
        expected_global_step=100,
    )
    assert record["training_complete"] is False
    assert record["eligible_as_training_result"] is False
    assert record["resumable"] is False
    assert record["optimizer_state_included"] is False
    assert record["authority"]["source"] == identity["source"]
    assert record["authority"]["job"] == identity["job"]
    assert set(record["adapter"]["files"]) == {
        "adapter/adapter_config.json",
        "adapter/adapter_model.safetensors",
    }
    names = {path.name for path in snapshot.rglob("*") if path.is_file()}
    assert names == {
        "adapter_config.json",
        "adapter_model.safetensors",
        RECOVERY_MANIFEST,
    }
    assert not {
        "optimizer.pt",
        "scheduler.pt",
        "rng_state.pth",
        "trainer_state.json",
        "training_args.bin",
        "training-manifest.json",
    } & names
    assert snapshot.stat().st_mode & 0o777 == 0o555
    assert all(
        path.stat().st_mode & 0o777 == (0o555 if path.is_dir() else 0o444)
        for path in snapshot.rglob("*")
    )


@pytest.mark.parametrize(
    ("relative", "mode", "restored"),
    (
        (".", 0o500, 0o555),
        (RECOVERY_MANIFEST, 0o400, 0o444),
        ("adapter", 0o500, 0o555),
        ("adapter/adapter_model.safetensors", 0o400, 0o444),
    ),
)
def test_snapshot_rejects_noncanonical_read_only_modes(
    tmp_path: Path,
    relative: str,
    mode: int,
    restored: int,
) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, _ = _snapshotter(output)
    snapshot = snapshotter.maybe_save(_AdapterModel(), global_step=100)
    assert snapshot is not None
    target = snapshot if relative == "." else snapshot / relative
    target.chmod(mode)
    try:
        with pytest.raises(RecoverySnapshotError, match="exact protected mode"):
            verify_recovery_snapshot(
                snapshot,
                run_identity_path=identity_path,
                expected_optimizer_steps=650,
                expected_global_step=100,
            )
    finally:
        target.chmod(restored)


def test_existing_snapshot_is_never_replaced_or_deleted(tmp_path: Path) -> None:
    output = tmp_path / "run"
    first, identity_path, identity = _snapshotter(output)
    original_model = _AdapterModel()
    snapshot = first.maybe_save(original_model, global_step=100)
    assert snapshot is not None
    original_manifest = (snapshot / RECOVERY_MANIFEST).read_bytes()
    original_adapter = (snapshot / "adapter" / "adapter_model.safetensors").read_bytes()

    second = AdapterRecoverySnapshotter(
        output_dir=output,
        run_identity_path=identity_path,
        run_identity_sha256=sha256_file(identity_path),
        run_identity=identity,
        expected_optimizer_steps=650,
    )
    replacement_model = _AdapterModel()
    with pytest.raises(RecoverySnapshotError, match="refusing to replace"):
        second.maybe_save(replacement_model, global_step=100)
    assert replacement_model.calls == []
    assert (snapshot / RECOVERY_MANIFEST).read_bytes() == original_manifest
    assert (snapshot / "adapter" / "adapter_model.safetensors").read_bytes() == original_adapter


def test_interrupted_or_unsafe_save_never_acquires_completion_manifest(
    tmp_path: Path,
) -> None:
    interrupted_output = tmp_path / "interrupted"
    interrupted, identity_path, _ = _snapshotter(interrupted_output)
    with pytest.raises(OSError, match="simulated interrupted"):
        interrupted.maybe_save(_AdapterModel(fail=True), global_step=100)
    partial = next((interrupted_output / "recovery-snapshots").iterdir())
    assert not (partial / RECOVERY_MANIFEST).exists()
    with pytest.raises(RecoverySnapshotError, match="partial"):
        verify_recovery_snapshot(
            partial,
            run_identity_path=identity_path,
            expected_optimizer_steps=650,
        )

    unsafe_output = tmp_path / "unsafe"
    unsafe, _, _ = _snapshotter(unsafe_output)
    with pytest.raises(ValueError, match="adapter must contain exactly"):
        unsafe.maybe_save(_AdapterModel(unsafe=True), global_step=100)
    unsafe_partial = next((unsafe_output / "recovery-snapshots").iterdir())
    assert not (unsafe_partial / RECOVERY_MANIFEST).exists()


def test_run_identity_mutation_blocks_snapshot_before_model_write(
    tmp_path: Path,
) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, _ = _snapshotter(output)
    identity_path.write_text('{"replaced":true}\n', encoding="utf-8")
    model = _AdapterModel()

    with pytest.raises(RecoverySnapshotError, match="run identity changed"):
        snapshotter.maybe_save(model, global_step=100)
    assert model.calls == []
    assert list((output / "recovery-snapshots").iterdir()) == []


def test_verifier_rejects_run_identity_path_replacement_during_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, _ = _snapshotter(output)
    snapshot = snapshotter.maybe_save(_AdapterModel(), global_step=100)
    assert snapshot is not None
    replacement = output / "replacement-run-identity.json"
    replacement.write_text('{"source":{},"job":{}}\n', encoding="utf-8")
    real_lstat = recovery.os.lstat
    replaced = False

    def replace_at_path_recheck(path: object) -> object:
        nonlocal replaced
        if not replaced and Path(path) == identity_path:
            replacement.replace(identity_path)
            replaced = True
        return real_lstat(path)

    monkeypatch.setattr(recovery.os, "lstat", replace_at_path_recheck)
    with pytest.raises(RecoverySnapshotError, match="changed while read"):
        verify_recovery_snapshot(
            snapshot,
            run_identity_path=identity_path,
            expected_optimizer_steps=650,
        )
    assert replaced is True


def test_publication_race_preserves_staging_and_existing_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    output = tmp_path / "run"
    snapshotter, _, _ = _snapshotter(output)

    def race(source: Path, destination: Path) -> None:
        destination.mkdir()
        (destination / "prior-evidence").write_text("do not replace\n", encoding="utf-8")
        raise FileExistsError(f"refusing to replace existing recovery snapshot {destination}")

    monkeypatch.setattr(recovery, "_rename_noreplace", race)
    with pytest.raises(RecoverySnapshotError, match="refusing to replace"):
        snapshotter.maybe_save(_AdapterModel(), global_step=100)

    children = list((output / "recovery-snapshots").iterdir())
    target = next(path for path in children if not path.name.startswith("."))
    staging = next(path for path in children if path.name.startswith("."))
    assert (target / "prior-evidence").read_text(encoding="utf-8") == "do not replace\n"
    assert (staging / RECOVERY_MANIFEST).is_file()
    assert ".partial-" in staging.name


def test_verifier_rejects_tampering_and_completion_laundering(
    tmp_path: Path,
) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, _ = _snapshotter(output)
    snapshot = snapshotter.maybe_save(_AdapterModel(), global_step=100)
    assert snapshot is not None
    manifest_path = snapshot / RECOVERY_MANIFEST
    record = json.loads(manifest_path.read_text(encoding="utf-8"))
    record["training_complete"] = True
    manifest_path.chmod(0o644)
    manifest_path.write_text(json.dumps(record) + "\n", encoding="utf-8")
    manifest_path.chmod(0o444)

    with pytest.raises(RecoverySnapshotError, match="falsely claims completion"):
        verify_recovery_snapshot(
            snapshot,
            run_identity_path=identity_path,
            expected_optimizer_steps=650,
        )


def test_callback_saves_only_after_world_zero_optimizer_steps(tmp_path: Path) -> None:
    output = tmp_path / "run"
    snapshotter, identity_path, _ = _snapshotter(output)
    callback = AdapterRecoveryCallbackMixin(snapshotter)
    model = _AdapterModel()
    control = object()

    returned = callback.on_step_end(
        object(),
        SimpleNamespace(global_step=100, is_world_process_zero=True),
        control,
        model=model,
    )
    assert returned is control
    snapshot = next((output / "recovery-snapshots").iterdir())
    verify_recovery_snapshot(
        snapshot,
        run_identity_path=identity_path,
        expected_optimizer_steps=650,
        expected_global_step=100,
    )

    with pytest.raises(RecoverySnapshotError, match="one-process"):
        callback.on_step_end(
            object(),
            SimpleNamespace(global_step=200, is_world_process_zero=False),
            control,
            model=model,
        )


def test_trainer_wires_recovery_without_unsafe_checkpoint_or_cleanup_paths() -> None:
    train_source = (REPOSITORY_ROOT / "training/peano_policy/train.py").read_text(
        encoding="utf-8"
    )
    recovery_path = REPOSITORY_ROOT / "training/peano_policy/recovery.py"
    recovery_source = recovery_path.read_text(encoding="utf-8")
    ast.parse(recovery_source, filename=str(recovery_path))

    assert "AdapterRecoverySnapshotter(" in train_source
    assert "AdapterRecoveryCallback(" in train_source
    assert "callbacks=callbacks" in train_source
    assert '"adapter_recovery": recovery_snapshot_plan(' in train_source
    assert "optimizer.pt" not in recovery_source
    assert "scheduler.pt" not in recovery_source
    assert "rng_state.pth" not in recovery_source
    assert "trainer_state.json" not in recovery_source
    assert "training_args.bin" not in recovery_source
    assert ".unlink(" not in recovery_source
    assert ".rmdir(" not in recovery_source
    assert "shutil.rmtree" not in recovery_source
    assert "os.replace(" not in recovery_source
