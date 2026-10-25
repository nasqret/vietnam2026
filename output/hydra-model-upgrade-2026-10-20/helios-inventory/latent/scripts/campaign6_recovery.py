"""Narrow C6 recovery candidate; execute only in SLURM.

The caller owns the run lock and supplies an independently reconstructed exact
identity.  This helper does not deserialize tensors, change the trainer,
repair a missed proof milestone, or certify native proof correctness.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re


def require(condition, message):
    if not condition:
        raise ValueError(message)


def require_slurm():
    require(bool(os.environ.get("SLURM_JOB_ID")), "Recovery/assessment requires SLURM")


def digest(path):
    value = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def object_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def inventory(path):
    """Regular files only; never follow a symlink out of the owned run."""
    path = Path(path)
    require(not path.is_symlink(), "Recovery candidate is a symlink")
    if path.is_file():
        return {".": digest(path)}
    require(path.is_dir(), "Recovery candidate is not a regular file or directory")
    result = {}
    for entry in sorted(path.rglob("*")):
        require(not entry.is_symlink(), "Symlink inside recovery candidate")
        if entry.is_file():
            result[str(entry.relative_to(path))] = digest(entry)
        else:
            require(entry.is_dir(), "Nonregular object inside recovery candidate")
    return result


ARTIFACT = re.compile(
    r"(?:evaluation-step-(?P<tensor>[0-9]+)\.pt(?:\.tmp)?|"
    r"validation-proof-step-(?P<proof>[0-9]+)|"
    r"validation-predictions-(?P<prediction>[0-9]+)\.json)\Z"
)


def archive_uncommitted_evaluations(run_dir, *, saved, checkpoint_sha256,
                                    expected_identity, expected_total_steps):
    """Preserve artifacts newer than the exact last.pt state before replay.

    ``saved`` is the just-deserialized last.pt object. The caller must hash
    last.pt before deserialization and independently reconstruct the entire
    expected identity (source, config, data, base, device and environment).
    Reading expected_identity from the same checkpoint is not verification.
    The caller must serialize all mutation of this run, including training.

    A prepared journal remains on failure; later recovery fails closed instead
    of hiding a partly completed transport. Nothing is deleted or overwritten.
    """
    require_slurm()
    run = Path(run_dir)
    require(run.is_dir() and not run.is_symlink(), "Owned run directory required")
    require(type(expected_total_steps) is int and expected_total_steps > 0,
            "Positive registered total steps required")
    require(type(saved) is dict and saved.get("identity") == expected_identity
            and type(expected_identity) is dict and bool(expected_identity),
            "Recovery checkpoint identity differs from expected identity")
    step = saved.get("step")
    require(type(step) is int and 0 <= step <= expected_total_steps,
            "Invalid recovery checkpoint step")
    require(digest(run / "last.pt") == checkpoint_sha256,
            "last.pt changed since deserialization")
    best = saved.get("best")
    require(best is None or (type(best) is dict and type(best.get("step")) is int
                            and 0 < best["step"] <= step
                            and best.get("identity") == expected_identity),
            "Saved selected checkpoint is newer than committed state or has another identity")

    for previous in sorted(run.glob("recovery-archive-*/recovery.json")):
        require(json.loads(previous.read_text()).get("state") == "completed",
                "An earlier recovery journal is incomplete; manual inspection required")

    candidates = []
    for entry in sorted(run.iterdir()):
        match = ARTIFACT.fullmatch(entry.name)
        if match and int(next(value for value in match.groupdict().values() if value is not None)) > step:
            candidates.append({"name": entry.name, "files_sha256": inventory(entry)})
    record = {"format": "latent-c6-resume-recovery-v1", "state": "completed",
              "job_id": os.environ["SLURM_JOB_ID"], "saved_step": step,
              "checkpoint_sha256": checkpoint_sha256,
              "expected_identity_sha256": object_digest(expected_identity),
              "registered_total_steps": expected_total_steps, "archived": candidates,
              "scope": "Archives only uncommitted evaluation artifacts; no skipped milestone repair"}
    if not candidates:
        return {**record, "archive": None}

    name = "recovery-archive-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    archive = run / name
    archive.mkdir()
    journal = archive / "recovery.json"
    record.update(state="prepared", archive=name)
    atomic_json(journal, record)
    for item in candidates:
        source = run / item["name"]
        require(inventory(source) == item["files_sha256"], "Recovery source changed")
        source.rename(archive / item["name"])
        require(inventory(archive / item["name"]) == item["files_sha256"],
                "Archived evidence differs from original bytes")
    require(digest(run / "last.pt") == checkpoint_sha256, "last.pt changed during recovery")
    record["state"] = "completed"
    atomic_json(journal, record)
    return record


def assess_milestones(run_dir, *, proof_eval_steps, attained_step, expected_roster,
                      expected_policy):
    """Report selection opportunity separately from attained training updates.

    This checks saved metadata and actual snapshot/proof hashes, not checker
    semantics or tensor equivalence. Existing native finalization/audit gates
    remain required. An ineligible or absent milestone never becomes repaired.
    """
    require_slurm()
    run = Path(run_dir)
    require(type(proof_eval_steps) is list and proof_eval_steps
            and all(type(step) is int and step > 0 for step in proof_eval_steps)
            and proof_eval_steps == sorted(set(proof_eval_steps)),
            "Registered unique increasing proof milestones required")
    require(type(attained_step) is int and attained_step >= 0, "Invalid attained step")
    require(type(expected_roster) is list and expected_roster
            and len(expected_roster) == len(set(expected_roster)), "Invalid registered proof roster")
    points = {}
    metrics = run / "metrics.jsonl"
    if metrics.is_file():
        for line in metrics.read_text().splitlines():
            value = json.loads(line)
            step = value.get("step")
            require(type(step) is int and step > 0 and step not in points,
                    "Malformed or duplicate committed metric step")
            points[step] = value
    rows = []
    for step in proof_eval_steps:
        row = {"step": step, "eligible": False}
        point = points.get(step)
        if step > attained_step:
            row["state"] = "not_reached"
        elif point is None:
            row["state"] = "missing_metric"
        elif point.get("proof_selection_eligible") is not True:
            row["state"] = "ineligible_or_skipped"
            row["evaluation_skipped"] = point.get("evaluation_skipped")
        else:
            candidate = point.get("proof_selection_candidate", {})
            directory = run / f"validation-proof-step-{step}"
            summary_path = directory / "summary.json"
            proofs_path = directory / "proofs.jsonl"
            snapshot = run / f"evaluation-step-{step}.pt"
            require(summary_path.is_file() and proofs_path.is_file() and snapshot.is_file(),
                    "Eligible milestone lacks its actual evidence files")
            summary = json.loads(summary_path.read_text())
            counts = summary.get("proof_counts", {})
            provenance = summary.get("provenance", {})
            require(summary.get("status") == "completed"
                    and summary.get("split") == "dev"
                    and summary.get("test_parsed") is False
                    and summary.get("validation_used_for_selection") is True
                    and summary.get("proof_task_ids") == expected_roster
                    and all(counts.get(key) == len(expected_roster)
                            for key in ("selected", "attempted", "recorded"))
                    and counts.get("wall_budget_limited", 0) == 0,
                    "Eligible milestone is incomplete or has another development roster")
            proof_pin, snapshot_pin = digest(proofs_path), digest(snapshot)
            require(candidate.get("complete") is True and candidate.get("step") == step
                    and candidate.get("selected") == len(expected_roster)
                    and candidate.get("selection_policy") == expected_policy
                    and candidate.get("proofs_sha256") == summary.get("proofs_sha256") == proof_pin
                    and provenance.get("policy") == expected_policy
                    and provenance.get("checkpoint_step") == step
                    and provenance.get("checkpoint_role") == "current-evaluation-snapshot"
                    and candidate.get("evaluated_checkpoint_step") == step
                    and candidate.get("evaluated_checkpoint_sha256")
                    == provenance.get("checkpoint_sha256") == snapshot_pin,
                    "Eligible milestone checkpoint, policy or proof binding differs")
            row.update(state="eligible_complete", eligible=True, proofs_sha256=proof_pin,
                       evaluation_snapshot_sha256=snapshot_pin)
        rows.append(row)
    return {"format": "latent-c6-selection-schedule-assessment-v1",
            "attained_step": attained_step, "registered_steps": proof_eval_steps,
            "selection_schedule_complete": all(row["eligible"] for row in rows),
            "eligible_steps": [row["step"] for row in rows if row["eligible"]],
            "milestones": rows,
            "scope": "Saved complete-selection metadata and byte bindings only; no native replay"}
