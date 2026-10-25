"""Independent synthetic binding-corruption checks; execute in SLURM only.

No model or native proof claim: the tensor/checker boundary is replaced with a
fixture to isolate whether load_binding rechecks its own mutable metadata.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace

if not os.environ.get("SLURM_JOB_ID"):
    raise RuntimeError("Reviewer tests require WMI/Helios SLURM")

import pytest

from latentproof import campaign6_sharded_eval as target


@pytest.fixture
def bound(tmp_path, monkeypatch):
    run_id = "helios-c6-main-qwen_random-s11"
    registered = {"run_id": run_id, "arm": "qwen_random", "seed": 11}
    args = SimpleNamespace(bindings=tmp_path / "bindings", runs_root=tmp_path / "runs",
                           plan_sha256="a" * 64)
    parent = args.bindings / run_id
    (parent / "validated").mkdir(parents=True)
    run = args.runs_root / run_id
    run.mkdir(parents=True)
    checkpoint = {"receipt_sha256": "b" * 64, "selection_sha256": "c" * 64,
                  "checkpoint_sha256": "d" * 64}
    cfg = {"campaign_id": "qwen-c6-main-fixture", "steps": 16,
           "prelude_layers": 8, "core_layers": 12, "max_recurrence": 4,
           "campaign5": {"proof_eval_steps": [4, 8, 16]}}
    producer = {"config": cfg, "data_manifest": {"tokenizer_identity_sha256": "f" * 64}}
    selection = {"checkpoint_step": 8, "identity_sha256": "e" * 64}
    monkeypatch.setattr(target, "checkpoint_binding", lambda *_:
                        (producer, selection, run / "best.pt", {}))
    freeze = {**registered, "original": checkpoint, "checkpoint_step": 8,
              "original_identity_sha256": "e" * 64,
              "protocol_sha256": "1" * 64,
              "selected_proof_binding": {"exact_tensor_equality": True}}
    freeze_path = parent / "validated" / "freeze.json"
    freeze_path.write_text(json.dumps(freeze))
    schedule = {"format": "latent-c6-selection-schedule-assessment-v1",
                "registered_steps": [4, 8, 16], "attained_step": 16,
                "selection_schedule_complete": False,
                "milestones": [{"step": step, "eligible": step != 8}
                               for step in (4, 8, 16)]}
    schedule_path = run / "selection-schedule.json"
    schedule_path.write_text(json.dumps(schedule))
    value = {**registered, "format": target.FORMAT, "plan_sha256": args.plan_sha256,
             "state": "bound", "checkpoint": checkpoint, "checkpoint_step": 8,
             "original_identity_sha256": "e" * 64,
             "selection_binding_relative": "validated",
             "selection_binding_sha256": target.digest(freeze_path),
             "selected_proof_binding": freeze["selected_proof_binding"],
             "tokenizer_identity_sha256": "f" * 64,
             "architecture_counts": {"prelude_layers": 8, "core_layers": 12,
                                     "coda_layers": 8, "max_recurrence": 4},
             "selection_schedule_sha256": target.digest(schedule_path),
             "selection_schedule_complete": False, "primary_comparison_eligible": False,
             "selection_schedule_scope": "Fixture complete byte bindings; one ineligible milestone"}
    plan = {"runs": [registered], "protocol": {"training_protocol_sha256": "1" * 64},
            "training_protocol": {"campaign_id": cfg["campaign_id"]}}

    def write(changes=None):
        edited = copy.deepcopy(value)
        edited.update(changes or {})
        (parent / "binding.json").write_text(json.dumps(edited))
        return edited

    write()
    return args, plan, run_id, write, value


def test_incomplete_selection_remains_explicitly_ineligible(bound):
    args, plan, run_id, _, _ = bound
    result = target.load_binding(args, plan, run_id)
    assert result["selection_schedule_complete"] is False
    assert result["primary_comparison_eligible"] is False


@pytest.mark.parametrize("changes", [
    {"primary_comparison_eligible": True},
    {"selection_schedule_complete": True, "primary_comparison_eligible": True},
    {"selection_schedule_sha256": None},
    {"checkpoint_step": 16},
    {"original_identity_sha256": "9" * 64},
    {"selected_proof_binding": {"exact_tensor_equality": False}},
])
def test_edited_binding_cannot_promote_or_relabel_evidence(bound, changes):
    args, plan, run_id, write, _ = bound
    write(changes)
    with pytest.raises(target.IntegrityError):
        target.load_binding(args, plan, run_id)
