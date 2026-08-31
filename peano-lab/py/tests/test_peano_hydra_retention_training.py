"""Synthetic metadata/progress tests; no model/native/network execution.

No successful production input/origin admission is substituted. These tests
exercise only new pure scope/configuration/progress helpers and fail-closed
entrypoint checks. The original training/tokenization/objective files remain
unchanged; no toy record is an approved run or a training artifact.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import io
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import retention_training as training
from training.peano_policy.config import load_config


def _fixture_scope():
    record = {"training_plan_sha256": "a" * 64, "training_rows": 11876,
              "development_rows": 2840, "expected_optimizer_steps": 1485}
    # This object is used only by the pure authorization validator, never by
    # execute/bind_training/any original model or origin API.
    plan = SimpleNamespace(to_dict=lambda: deepcopy(record))
    authorization = {"schema": training.AUTHORIZATION_SCHEMA, **record,
        "token_preflight_sha256": "b" * 64, "resource_approval_sha256": "c" * 64,
        "resource_request_sha256": "d" * 64, "model_training_authorized": True,
        "initialization": deepcopy(training.INITIALIZATION), "max_wall_seconds": 7200,
        "gpu_count": 1, "automatic_retry": False, "resume": False}
    return plan, authorization


def test_fixture_scope_is_not_an_execution_plan():
    plan, authorization = _fixture_scope()
    assert training.validate_training_authorization(plan, authorization,
        expected_authorization_sha256=training.digest(authorization)) == authorization
    called = []
    with pytest.raises(training.RetentionTrainingError, match="genuine plan"):
        training.execute(plan, authorization=authorization, expected_authorization_sha256=training.digest(authorization),
                         reservation_check=lambda _: called.append(True))
    assert called == []


@pytest.mark.parametrize(("field", "value"), [
    ("gpu_count", 2), ("gpu_count", True), ("max_wall_seconds", 7201),
    ("automatic_retry", True), ("resume", True), ("training_rows", 11877),
    ("expected_optimizer_steps", 1486), ("training_plan_sha256", "f" * 64),
    ("initialization", {"kind": "warm-start", "continued_from_ancestor_adapter": True}),
])
def test_changed_scope_never_passes_even_when_rehashed(field, value):
    plan, authorization = _fixture_scope()
    authorization[field] = value
    with pytest.raises(training.RetentionTrainingError):
        training.validate_training_authorization(plan, authorization,
            expected_authorization_sha256=training.digest(authorization))


def test_profile_keeps_old_recipe_and_rejects_larger_learning_rate():
    config = load_config(ROOT / "training/peano_hydra/configs/qwen3_1_7b_retention_pilot.toml")
    locations = SimpleNamespace(directory=ROOT / training.PACKAGE / "preparation")
    checked = training._configuration(config, locations)
    assert checked["trainer"]["learning_rate"] == 0.0001
    assert checked["run"]["resume"] == "never"
    changed = replace(config, trainer=replace(config.trainer, learning_rate=0.0002))
    with pytest.raises(training.RetentionTrainingError, match="trainer recipe"):
        training._configuration(changed, locations)


@pytest.mark.parametrize("changed_field", ("train_rows", "dev_rows", "evaluation_plan", "config"))
def test_refresh_rejects_changed_live_fields_with_unchanged_saved_identity(monkeypatch, changed_field):
    from training.peano_hydra.retention_data import RetentionPreparation

    # Only the equality guard is exercised. This metadata fixture has no origin
    # references and cannot pass the real binder or any execution entrypoint.
    checked = RetentionPreparation(ROOT / "synthetic-only", {}, "a" * 64,
        ({"prompt": "train-original"},), ({"prompt": "dev-original"},))
    config = load_config(ROOT / "training/peano_hydra/configs/qwen3_1_7b_retention_pilot.toml")
    fresh = training.TrainingPlan(None, checked, config, {"goals": ["original"]},
                                  None, None, '{"synthetic_metadata_only":true}')
    stale = deepcopy(fresh)
    monkeypatch.setattr(training, "bind_training", lambda inputs: fresh)
    training._refresh(stale)
    if changed_field in ("train_rows", "dev_rows"):
        getattr(stale.checked_data, changed_field)[0]["prompt"] = "mutated"
    elif changed_field == "evaluation_plan":
        stale.evaluation_plan["goals"][0] = "mutated"
    else:
        stale = replace(stale, config=replace(config, trainer=replace(config.trainer, learning_rate=0.0002)))
    assert stale.to_dict() == fresh.to_dict()
    with pytest.raises(training.RetentionTrainingError, match="configuration or preregistered plan changed"):
        training._refresh(stale)


def _reservation(authorization):
    return {"status": "job-verified", "profile": training.PROFILE, "run_id": training.RUN_ID,
        "stage": "train", "job_id": "123456", "resource_request_sha256": authorization["resource_request_sha256"],
        "approval_sha256": authorization["resource_approval_sha256"], "source_commit": "e" * 40,
        "source_files_sha256": "f" * 64, "payloads_sha256": "1" * 64,
        "reservation": deepcopy(training.RESERVATION), "allocation_elapsed_seconds": 100,
        "allocation_remaining_seconds": 7100, "automatic_retry": False, "resume": False}


def test_live_job_check_and_elapsed_time_cannot_be_omitted(monkeypatch):
    _, authorization = _fixture_scope()
    reservation = _reservation(authorization)
    monkeypatch.setenv("SLURM_JOB_ID", "999999")
    with pytest.raises(training.RetentionTrainingError, match="actual Slurm job"):
        training._reservation(reservation, authorization, live=True)
    reservation["allocation_remaining_seconds"] = 7200
    with pytest.raises(training.RetentionTrainingError, match="elapsed/remaining"):
        training._reservation(reservation, authorization, live=False)


def test_reserved_identity_only_excludes_clock_fields():
    _, authorization = _fixture_scope()
    first = _reservation(authorization)
    next_record = deepcopy(first)
    next_record.update(allocation_elapsed_seconds=200, allocation_remaining_seconds=7000)
    assert training._reservation(first, authorization, live=False) == training._reservation(next_record, authorization, live=False)
    next_record["payloads_sha256"] = "2" * 64
    assert training._reservation(first, authorization, live=False) != training._reservation(next_record, authorization, live=False)


class FlushedBuffer(io.StringIO):
    def __init__(self):
        super().__init__()
        self.flushes = 0

    def flush(self):
        self.flushes += 1
        return super().flush()


def test_optimizer_progress_is_flushed_without_framework_imports():
    stream = FlushedBuffer()
    progress = training.Progress(stream)
    callback = training._ProgressCallback(progress, lambda: False)
    control = object()
    assert callback.on_log(None, SimpleNamespace(global_step=37), control,
        logs={"loss": 0.125, "learning_rate": 0.0001}) is control
    record = json.loads(stream.getvalue())
    assert stream.flushes == 1 and record["step"] == 37 and record["logs"]["loss"] == 0.125
    assert not any(name == "torch" or name.startswith("transformers.") for name in sys.modules)


def test_progress_cap_and_whole_allocation_stop_fail_closed():
    progress = training.Progress(io.StringIO())
    progress.bytes = training.MAX_PROGRESS_BYTES
    with pytest.raises(training.RetentionTrainingError, match="progress output cap"):
        progress.emit("not-allowed")
    callback = training._ProgressCallback(training.Progress(io.StringIO()), lambda: True)
    with pytest.raises(training.RetentionTrainingError, match="whole-allocation stop"):
        callback.on_step_end(None, SimpleNamespace(global_step=37), object())


def test_artifact_loader_refuses_legacy_or_untyped_manifest():
    with pytest.raises(training.RetentionTrainingError, match="exact new artifact-reference"):
        training.load_training_artifact(SimpleNamespace(manifest_path="old/manifest.json"))


def _artifact_byte_fixture(tmp_path):
    from training.peano_policy.manifest import artifact_directory_hash

    # Real closed-tree hashing API, with deliberately non-model fixture bytes.
    # These files are never deserialized or admitted as a training artifact.
    (tmp_path / "adapter").mkdir()
    (tmp_path / "tokenizer").mkdir()
    (tmp_path / "adapter/adapter_model.safetensors").write_bytes(b"file-hashing fixture only")
    (tmp_path / "adapter/adapter_config.json").write_text("{}\n")
    (tmp_path / "tokenizer/tokenizer.json").write_text("{}\n")
    return {name: artifact_directory_hash(tmp_path, name) for name in ("adapter", "tokenizer")}


def test_saved_directories_use_real_artifact_api_and_explicit_loader_roots(tmp_path):
    record = _artifact_byte_fixture(tmp_path)
    assert training._verified_artifact_directories(tmp_path, record) == (
        tmp_path / "adapter", tmp_path / "tokenizer")


@pytest.mark.parametrize("relative", ("adapter/adapter_model.safetensors", "tokenizer/tokenizer.json"))
def test_saved_directories_reject_changed_bytes_in_either_real_tree(tmp_path, relative):
    record = _artifact_byte_fixture(tmp_path)
    (tmp_path / relative).write_bytes(b"changed after recording the manifest")
    with pytest.raises(ValueError, match="artifact hash mismatch"):
        training._verified_artifact_directories(tmp_path, record)


def test_saved_directories_reject_unlisted_files_with_real_api(tmp_path):
    record = _artifact_byte_fixture(tmp_path)
    (tmp_path / "tokenizer/unlisted.py").write_text("# not in the recorded closed tree\n")
    with pytest.raises(ValueError, match="complete tokenizer directory"):
        training._verified_artifact_directories(tmp_path, record)


def test_saved_directories_do_not_accept_a_manifest_chosen_loader_root(tmp_path):
    record = _artifact_byte_fixture(tmp_path)
    record["tokenizer"] = deepcopy(record["adapter"])
    with pytest.raises(ValueError, match="different loader directory"):
        training._verified_artifact_directories(tmp_path, record)
