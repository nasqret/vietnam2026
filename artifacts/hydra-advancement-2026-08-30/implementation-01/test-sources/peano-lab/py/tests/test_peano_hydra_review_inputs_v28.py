"""Ancillary input preflight uses tiny files, never actual proof replay."""

import ast
from copy import deepcopy
from hashlib import sha256
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import review_inputs_v28 as inputs  # noqa: E402
from training.peano_hydra import review_v28 as review  # noqa: E402
from training.peano_hydra.frontier import digest  # noqa: E402


def _tiny_inputs(tmp_path, monkeypatch):
    root = (tmp_path / "repository").resolve()
    root.mkdir()
    records = []
    for index, (relative, _, _) in enumerate(inputs.PROOF_FILES):
        data = (f"tiny synthetic input {index}; no actual proof\n" * 3).encode()
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        records.append((relative, len(data), sha256(data).hexdigest()))
    monkeypatch.setattr(inputs, "PROOF_FILES", tuple(records))
    monkeypatch.setattr(inputs, "ALTERNATE_DIRECTORY", tmp_path / "no-lab-override")
    monkeypatch.setattr(review, "ROOT", root)
    return root, inputs.ancillary_input_closure("native-hotspots")


def _plan(record, root):
    return {
        "mode": "native-hotspots", "ancillary_inputs": record,
        "source": {"git_dirty": False}, "execution_root": str(root),
        "epoch_sha256": inputs.ALPHA_V28_EPOCH,
        "profile": review.development_profile(),
        "cold_wall_budget": 900,
        "cold_selection": {"scope": "hotspots", "batches": [[0], [1]]},
        "cold_plan": {
            "selected_targets": {str(index): {"name": name} for index, name in enumerate(inputs.HOTSPOT_NAMES)},
            "edition_identity_sha256": "a" * 64, "certificate_limits": {},
        },
    }


def _request(record):
    return {
        "schema": review.SCHEMA, "mode": "cold", "source": {"synthetic": True},
        "epoch_sha256": inputs.ALPHA_V28_EPOCH,
        "profile_sha256": review.development_profile()["profile_sha256"],
        "ancillary_inputs": record, "targets": [{"name": inputs.HOTSPOT_NAMES[0]}],
        "pass_number": 1, "batch_number": 0,
        "edition_identity_sha256": "a" * 64, "certificate_limits": {},
    }


def test_exact_closure_seals_match_unchanged_provider_literals():
    provider_values = []
    for filename, prefix in (
        ("bertrand_complete_closure.py", "BERTRAND"),
        ("campaign_milestone_closure.py", "MILESTONE_CLOSURE"),
    ):
        tree = ast.parse((ROOT / "peano-lab/py/peano_lab/library" / filename).read_text())
        names = {f"EXPECTED_{prefix}_BUNDLE_BYTES", f"EXPECTED_{prefix}_BUNDLE_SHA256"}
        values = {target.id: ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign) for target in node.targets
                  if isinstance(target, ast.Name) and target.id in names}
        provider_values.append((values[f"EXPECTED_{prefix}_BUNDLE_BYTES"], values[f"EXPECTED_{prefix}_BUNDLE_SHA256"]))
    assert [(size, sha) for _, size, sha in inputs.PROOF_FILES] == provider_values
    record = inputs.ancillary_input_closure("native-hotspots")
    assert record["total_bytes"] == 16_887_078
    assert record["file_count"] == 2
    assert record["kernel_checked"] is False
    assert record["external_provenance_files"] == []


@pytest.mark.parametrize("mutation", ["missing", "extra", "path", "digest", "size", "epoch", "authority", "boolean_count"])
def test_resealed_closure_mutations_cannot_change_fixed_input_identity(mutation, monkeypatch):
    record = inputs.ancillary_input_closure("native-hotspots")
    first = next(iter(record["files"]))
    if mutation == "missing":
        record["files"].pop(first)
    elif mutation == "extra":
        record["files"]["research/unrelated.json"] = deepcopy(record["files"][first])
    elif mutation == "path":
        record["files"]["../" + first] = record["files"].pop(first)
    elif mutation == "digest":
        record["files"][first]["sha256"] = "0" * 64
    elif mutation == "size":
        record["files"][first]["bytes"] += 1
    elif mutation == "epoch":
        record["epoch_sha256"] = "0" * 64
    elif mutation == "authority":
        record["kernel_checked"] = True
    else:
        record["file_count"] = True
    record.pop("input_closure_sha256")
    record["input_closure_sha256"] = digest(record)
    monkeypatch.setattr(inputs, "_open_input", lambda *a: pytest.fail("mutated metadata reached file I/O"))
    with pytest.raises(ValueError, match="exact historical data"):
        inputs.check_ancillary_inputs(record, mode="native-hotspots", root=ROOT)


@pytest.mark.parametrize("mode", ["reference-only", "full-plan-only"])
def test_nonreplay_modes_have_no_data_dependency_or_input_readiness(mode, monkeypatch):
    monkeypatch.setattr(inputs, "_open_input", lambda *a: pytest.fail("nonreplay mode read proof files"))
    record = inputs.ancillary_input_closure(mode)
    assert record["files"] == {}
    assert inputs.check_ancillary_inputs(record, mode=mode, root=ROOT) == {}
    with pytest.raises(ValueError):
        inputs.validate_ancillary_inputs(record, mode="native-hotspots")


def test_streamed_tiny_inputs_return_stable_local_identities(tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    before = inputs.check_ancillary_inputs(record, mode="native-hotspots", root=root)
    assert len(before) == 2
    assert before == inputs.check_ancillary_inputs(record, mode="native-hotspots", root=root)


@pytest.mark.parametrize("failure", ["missing", "wrong_hash", "too_large", "symlink", "hardlink", "fifo"])
def test_bad_input_stops_before_any_worker_allocation(failure, tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    first = root / next(iter(record["files"]))
    data = first.read_bytes()
    if failure == "missing":
        first.unlink()
    elif failure == "wrong_hash":
        first.write_bytes(b"!" + data[1:])
    elif failure == "too_large":
        with first.open("r+b") as stream:
            stream.truncate(inputs.MAX_FILE_BYTES + 1)
    elif failure == "symlink":
        target = tmp_path / "elsewhere.json"
        first.rename(target)
        first.symlink_to(target)
    elif failure == "hardlink":
        os.link(first, tmp_path / "extra-link.json")
    else:
        first.unlink()
        os.mkfifo(first)
    monkeypatch.setattr(review, "run_bounded", lambda *a, **k: pytest.fail("bad input allocated a worker"))
    with pytest.raises(ValueError, match="ancillary input"):
        review.run_cold(_plan(record, root))


@pytest.mark.parametrize("component", ["repository-parent", "data-parent"])
def test_symlink_ancestor_is_rejected_even_with_correct_leaf_bytes(component, tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    if component == "repository-parent":
        alias = tmp_path / "alias"
        alias.symlink_to(tmp_path, target_is_directory=True)
        root = alias / root.name
    else:
        directory = root / "research/arithmetic-library"
        actual = root / "actual-data-parent"
        directory.rename(actual)
        directory.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        inputs.check_ancillary_inputs(record, mode="native-hotspots", root=root)


def test_legacy_lab_override_cannot_shadow_pinned_default_source(tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    alternate = tmp_path / "lab"
    alternate.mkdir()
    (alternate / Path(next(iter(record["files"]))).name).write_bytes(b"unapproved override")
    monkeypatch.setattr(inputs, "ALTERNATE_DIRECTORY", alternate)
    with pytest.raises(ValueError, match="shadows"):
        inputs.check_ancillary_inputs(record, mode="native-hotspots", root=root)


@pytest.mark.parametrize("failure", ["missing", "wrong_hash"])
def test_controller_preflight_fails_before_execution_archive_or_checks(failure, tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    first = root / next(iter(record["files"]))
    if failure == "missing":
        first.unlink()
    else:
        data = first.read_bytes()
        first.write_bytes(b"!" + data[1:])
    plan = _plan(record, root)
    monkeypatch.setattr(review, "validate_plan", lambda value: None)
    monkeypatch.setattr(review, "source_identity", lambda: plan["source"])
    monkeypatch.setattr(review, "_execute_checks", lambda *a, **k: pytest.fail("bad input reached execution"))
    output = tmp_path / "never-created"
    with pytest.raises(ValueError, match="ancillary input"):
        review.execute_review(plan, output)
    assert not output.exists()


def test_data_drift_preserves_first_worker_record_and_prevents_next_worker(tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    first = root / next(iter(record["files"]))
    observed = {"synthetic": "the original worker record, not a native result"}
    calls = []
    def fake_worker(*args, **kwargs):
        calls.append(kwargs)
        data = first.read_bytes()
        first.write_bytes(b"!" + data[1:])
        return observed
    monkeypatch.setattr(review, "run_bounded", fake_worker)
    archive = tmp_path / "partial"
    archive.mkdir()
    with pytest.raises(ValueError, match="ancillary input bytes"):
        review.run_cold(_plan(record, root), archive=archive)
    assert len(calls) == 1
    assert calls[0]["limits"] == review.COLD_LIMITS
    assert review.read_record(archive / "cold-worker-pass-1-batch-0.json") == observed


def test_worker_checks_missing_data_before_native_replay(tmp_path, monkeypatch):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    (root / next(iter(record["files"]))).unlink()
    monkeypatch.setattr(review, "check_recorded_source_bytes", lambda value: None)
    monkeypatch.setattr(review, "replay_cold_target", lambda *a, **k: pytest.fail("missing data reached native replay"))
    with pytest.raises(ValueError, match="ancillary input is missing"):
        review.worker(_request(record))


def test_worker_cannot_flush_positive_after_input_drift(tmp_path, monkeypatch, capsys):
    root, record = _tiny_inputs(tmp_path, monkeypatch)
    first = root / next(iter(record["files"]))
    monkeypatch.setattr(review, "check_recorded_source_bytes", lambda value: None)
    def fake_replay(*args, **kwargs):
        data = first.read_bytes()
        first.write_bytes(b"!" + data[1:])
        return {"status": "checked", "synthetic": True}
    monkeypatch.setattr(review, "replay_cold_target", fake_replay)
    with pytest.raises(ValueError, match="ancillary input bytes"):
        review.worker(_request(record))
    assert capsys.readouterr().out == ""


def test_worker_cannot_use_two_file_closure_for_other_targets(tmp_path, monkeypatch):
    _, record = _tiny_inputs(tmp_path, monkeypatch)
    request = _request(record)
    request["targets"][0]["name"] = "unplanned_other_target"
    monkeypatch.setattr(review, "check_recorded_source_bytes", lambda value: None)
    monkeypatch.setattr(review, "replay_cold_target", lambda *a, **k: pytest.fail("uncovered target reached native replay"))
    with pytest.raises(ValueError, match="batch/pass reservation"):
        review.worker(request)
