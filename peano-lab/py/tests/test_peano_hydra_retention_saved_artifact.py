"""Small type, bounds, and actual source-byte guards; no real admission run."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import origin_bridge as bridge, scaling_evaluation as original
from training.peano_hydra import retention_saved_artifact as saved, retention_training as training


def fixture_reference(tmp_path):
    # Typed location fixtures only. None has an origin/admission receipt and
    # none is ever passed to an actual original binding or model loader.
    ancestors = []
    for role in ("old", "frontier"):
        root = tmp_path / role
        request = bridge.OriginRequest(root, root / "source.json", "a" * 64, "b" * 40,
            root / "preparation", "c" * 64, root / "model/manifest.json", "d" * 64, bridge.AUTHORITY_PROFILE)
        ancestors.append(original.OriginReference(request, root / "receipt.json", "e" * 64))
    inputs = training.TrainingInputReference(tmp_path / "mixture", "f" * 64, tmp_path / "config.toml", "1" * 64,
        *ancestors, tmp_path / "evaluation-plan.json", "2" * 64)
    root = tmp_path / "producer"
    producer = saved.PreservedProducerReference(root, root / "source.json", saved.PRODUCER_SOURCE_SHA,
        root / training.PACKAGE / "inputs.json", saved.PRODUCER_INPUTS_SHA)
    return saved.PreservedRetentionArtifactReference(tmp_path / "model/manifest.json", saved.MODEL_MANIFEST_SHA,
        inputs, producer)


def test_nullable_reference_roundtrips_but_cannot_load_any_candidate(tmp_path):
    ref = fixture_reference(tmp_path)
    rebound = saved.reference(ref.to_dict(), ref.locations())
    assert rebound == ref
    assert type(ref) is not training.TrainingArtifactReference and type(ref) is not original.OriginReference
    with pytest.raises(training.RetentionTrainingError, match="nullable historical admission draft"):
        rebound.load()


def test_admission_path_and_external_pin_are_indivisible(tmp_path):
    ref = fixture_reference(tmp_path)
    with pytest.raises(training.RetentionTrainingError, match="both its path and external raw pin"):
        replace(ref, admission_receipt_sha256="3" * 64)
    with pytest.raises(training.RetentionTrainingError, match="both its path and external raw pin"):
        replace(ref, admission_receipt_path=tmp_path / "admission.json")


def test_new_evaluator_source_cannot_relabel_historical_producer(tmp_path):
    ref = fixture_reference(tmp_path)
    identity = deepcopy(ref.to_dict())
    identity["producer"]["trainer_sha256"] = hashlib.sha256((ROOT / "training/peano_hydra/retention_training.py").read_bytes()).hexdigest()
    assert identity["producer"]["trainer_sha256"] != saved.PRODUCER_TRAINER_SHA
    with pytest.raises(training.RetentionTrainingError, match="fields or paths changed"):
        saved.reference(identity, ref.locations())


@pytest.mark.parametrize(("key", "value"), [("cpu_seconds", 31), ("wall_seconds", 61),
    ("rss_bytes", 3 * 1024**3), ("output_bytes", 5 * 1024**2), ("cpu_seconds", True)])
def test_historical_metadata_limits_cannot_expand_original_constructor(key, value):
    changed = {**saved.LIMITS, key: value}
    with pytest.raises(training.RetentionTrainingError, match="separate metadata envelope"):
        saved._process_limits(changed)


def worker_definitions():
    # Imports only new definitions, never run/main or any producer API.
    spec = importlib.util.spec_from_file_location("retention_saved_worker_fixture", ROOT / saved.WORKER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_source_loader_uses_pinned_source_and_rejects_changed_bytes(tmp_path):
    worker = worker_definitions()
    target = tmp_path / "fixture.py"
    target.write_bytes(b"value = 17\n")
    (tmp_path / "fixture.pyc").write_bytes(b"This deliberately invalid cache must never be read")
    files = {target.name: {"bytes": target.stat().st_size, "sha256": hashlib.sha256(target.read_bytes()).hexdigest()}}
    finder = worker.SourceFinder(tmp_path, files)
    loader = worker.SourceLoader(finder, target.name)
    spec = importlib.util.spec_from_file_location("byte_fixture_only", target, loader=loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    assert module.value == 17
    target.write_bytes(b"value = 18\n")
    with pytest.raises(ValueError, match="original source changed before import"):
        loader.exec_module(importlib.util.module_from_spec(spec))


def test_worker_read_rejects_symlink_ancestor_and_hardlinked_file(tmp_path):
    worker = worker_definitions()
    actual = tmp_path / "actual"
    actual.mkdir()
    target = actual / "fixture.txt"
    target.write_bytes(b"fixture")
    alias = tmp_path / "alias"
    alias.symlink_to(actual, target_is_directory=True)
    with pytest.raises(OSError):
        worker.read(alias / target.name, 1024)
    (actual / "other.txt").hardlink_to(target)
    with pytest.raises(ValueError, match="one bounded regular file"):
        worker.read(target, 1024)


def test_passed_inner_receipt_is_not_a_loadable_candidate_after_late_failure(tmp_path):
    # A real outer failure may retain precisely this status. No producer files
    # exist in this fixture, so rejection must occur before any model/input read.
    ref = fixture_reference(tmp_path)
    raw = saved.canonical({"schema": saved.RECEIPT_SCHEMA,
        "status": "passed-corrected-historical-admission"}) + b"\n"
    path = tmp_path / "provisional.json"
    path.write_bytes(raw)
    ref = replace(ref, admission_receipt_path=path, admission_receipt_sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(training.RetentionTrainingError, match="bare provisional admission"):
        ref.load()


@pytest.mark.parametrize(("field", "value"), [("exit_code", 2), ("exit_code", True),
    ("observed_from", "owner-before-its-own-exit"), ("status", "started")])
def test_failed_or_unobserved_owner_exit_cannot_establish_custody(field, value):
    # Rejection fixture only, not a synthesized successful process observation.
    invocation = {"schema": saved.INVOCATION_SCHEMA, "status": "exited", "mode": "authenticate-admission",
        "source_commit": "0" * 40, "argv": [], "exit_code": 0, "helper": {}, "owner_result": {}, "output": {},
        "observed_from": "actual-tool-process-completion", "recorded_at_utc": "2026-08-31T00:00:00Z",
        "automatic_retry": False}
    invocation[field] = value
    with pytest.raises(training.RetentionTrainingError, match="externally observed successful owner exit"):
        saved._completed_invocation(invocation)


def test_custody_recorded_locations_are_portable_metadata_without_host_io(monkeypatch):
    def forbidden_stat(*args, **kwargs):
        raise AssertionError("recorded Mac receipt paths must not be statted on Helios")
    monkeypatch.setattr(Path, "stat", forbidden_stat)
    descriptor = {"path": "/Users/recorded-only/nonexistent/admission-owner.json", "bytes": 7, "sha256": "a" * 64}
    assert saved._custody_descriptor(descriptor) == descriptor
