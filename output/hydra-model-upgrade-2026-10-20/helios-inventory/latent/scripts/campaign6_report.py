#!/usr/bin/env python3
"""SLURM-only private C6 monitoring projection; never executes a model or checker.

Read canonical registration, atomic producer receipts, complete JSONL records and
the evaluation adapter's aggregates. Keep all evidence T4 and all missing data
explicit. The HTML embeds the same snapshot for offline artifact viewing.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


FORMAT = "latent-c6-monitor-snapshot-v1"
FAILED = {"FAILED", "TIMEOUT", "OUT_OF_MEMORY", "CANCELLED", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL"}
METRICS = ("train_loss", "train_objective_loss", "train_mean_recurrence", "elapsed_seconds",
           "training_seconds", "cumulative_evaluation_seconds", "train_token_block_calls",
           "train_forward_token_block_calls", "val_loss", "val_accuracy", "val_tokens")


def now():
    return datetime.now(timezone.utc).isoformat()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def inside(root, value):
    path = (root / value).resolve()
    if not path.is_relative_to(root):
        raise ValueError("Path escapes project: " + str(value))
    return path


def atomic(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp-" + str(os.getpid()))
    temporary.write_text(content)
    temporary.replace(path)


def encoded(value):
    return json.dumps(value, indent=2, allow_nan=False) + "\n"


def read_json(path, provenance, root, *, optional=False):
    if optional and not path.is_file():
        return None
    raw = path.read_bytes()
    value = json.loads(raw)
    provenance[str(path.relative_to(root))] = sha256(raw)
    return value


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def scheduler_observation(job_ids):
    """Only query the IDs registered for this project and local cluster."""
    if not job_ids:
        return {}, None
    if any(not str(value).replace("_", "").isdigit() for value in job_ids):
        raise ValueError("Unexpected scheduler job ID")
    try:
        result = subprocess.run(["sacct", "-X", "-n", "-P", "-j", ",".join(sorted(job_ids)),
                                 "--format=JobIDRaw,State,Elapsed,ExitCode,AllocCPUS,AllocTRES"],
                                text=True, capture_output=True, timeout=12, check=True)
        rows = {}
        for line in result.stdout.splitlines():
            fields = line.split("|")
            if len(fields) >= 6:
                rows[fields[0]] = dict(zip(("job_id", "state", "elapsed", "exit_code", "allocated_cpus", "allocated_tres"), fields[:6]))
        return rows, None
    except (OSError, subprocess.SubprocessError) as exc:
        return {}, str(exc)


def compact_history(directory, status, provenance, root, warnings):
    history_file = directory / "metrics.jsonl"
    if history_file.is_file():
        raw = history_file.read_bytes()
        provenance[str(history_file.relative_to(root))] = sha256(raw)
        # A trailing non-newline record may belong to an in-progress append.
        lines = raw.splitlines(keepends=True)
        records = []
        for index, line in enumerate(lines):
            if not line.endswith(b"\n"):
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                warnings.append("Malformed committed history row " + str(index + 1))
    else:
        records = status.get("history", [])
    step = status.get("step", 0)
    clean, seen = [], set()
    for row in records:
        if type(row.get("step")) is not int or row["step"] > step:
            continue
        if row["step"] in seen:
            warnings.append("Duplicate optimizer update in history: " + str(row["step"]))
            continue
        seen.add(row["step"])
        point = {"step": row["step"], "updated_at": row.get("updated_at")}
        for key in METRICS:
            if finite(row.get(key)) and (not key.startswith("val_") or row.get("validation") is True):
                point[key] = row[key]
        if row.get("proof_validation") is True:
            point["proof_validation"] = True
            summary_path = directory / ("validation-proof-step-" + str(row["step"])) / "summary.json"
            try:
                summary = read_json(summary_path, provenance, root, optional=True)
                counts = summary.get("proof_counts", {}) if summary else {}
                if summary:
                    point["proof"] = {
                        "selected": counts.get("selected", len(summary.get("proof_task_ids", []))),
                        "attempted": counts.get("attempted"),
                        "solved": counts.get("autonomous_python_kernel_proof", 0),
                        "wall_limited": counts.get("wall_budget_limited", 0),
                        "complete": summary.get("status") == "completed",
                        "summary": str(summary_path.relative_to(root)),
                    }
                else:
                    candidate = row.get("proof_selection_candidate")
                    if candidate and candidate.get("complete") is True:
                        point["proof"] = {"selected": candidate["selected"], "attempted": candidate["selected"],
                                          "solved": candidate["solved"], "wall_limited": 0, "complete": True,
                                          "source": "complete trainer selection candidate"}
                    else:
                        point["proof"] = {"selected": row.get("proof_total"), "attempted": row.get("proof_attempted"),
                                          "solved": None, "complete": False, "state": "summary_unavailable"}
            except (OSError, ValueError, TypeError) as exc:
                warnings.append("Proof milestone unavailable at " + str(row["step"]) + ": " + str(exc))
        clean.append(point)
    return sorted(clean, key=lambda row: row["step"])


def training_row(planned, root, cluster, scheduler, provenance):
    keys = ("run_id", "campaign_id", "cluster", "arm", "seed", "job_id", "role", "max_steps", "condition")
    row = {key: planned.get(key) for key in keys}
    row.update(state="registered", step=0, history=[], metrics={}, warnings=[], evidence_tier="T4",
               review_state="live-unreviewed", training_completed=False,
               selection_schedule_complete=None, primary_comparison_eligible=None)
    if planned.get("cluster") != cluster:
        row["state"] = "remote_receipt_unavailable"
        return row
    try:
        directory = inside(root, planned["directory"])
        status = read_json(directory / "status.json", provenance, root, optional=True)
        dispatch = (read_json(inside(root, planned["dispatch_file"]), provenance, root, optional=True)
                    if planned.get("dispatch_file") else None)
        if dispatch and dispatch.get("run_id") != planned["run_id"]:
            raise ValueError("Dispatch identity differs from registration")
        if status:
            for key in ("run_id", "arm", "seed", "cluster"):
                if key in status and key in planned and status[key] != planned[key]:
                    raise ValueError("Trainer " + key + " differs from registration")
            row.update({key: status[key] for key in ("state", "step", "max_steps", "updated_at", "best_checkpoint_step", "checkpoint_step", "smoke") if key in status})
            row["metrics"] = {key: status.get("metrics", {})[key] for key in METRICS if finite(status.get("metrics", {}).get(key))}
            forward = status.get("metrics", {}).get("training_forward_cost", {})
            if isinstance(forward, dict):
                row["metrics"]["training_forward_cost"] = {key: value for key, value in forward.items() if finite(value)}
            row["history"] = compact_history(directory, status, provenance, root, row["warnings"])
            if row["state"] == "completed" and (row["step"] != row["max_steps"] or status.get("smoke") is not False):
                row["state"] = "producer_completed_unvalidated"
            row["training_completed"] = row["state"] == "completed"
            selection = read_json(directory / "selection.json", provenance, root, optional=True)
            if selection:
                row["selection"] = {key: selection.get(key) for key in ("state", "selected_using", "checkpoint_step", "checkpoint_sha256", "checkpoint_selection_criterion", "test_labels_read")}
        if dispatch:
            row["dispatch_state"] = dispatch.get("state")
            for key in ("training_completed", "selection_schedule_complete", "primary_comparison_eligible", "eligibility_basis"):
                if key in dispatch:
                    row[key] = dispatch[key]
            if not status or str(dispatch.get("state", "")).startswith(("failed", "skipped_", "not_started_", "budget_limited")):
                row["state"] = dispatch.get("state", "unknown")
        observation = scheduler.get(str(planned.get("job_id")))
        if observation:
            row["scheduler"] = observation
            scheduler_state = observation["state"].split()[0].split("+")[0]
            if not status and not dispatch:
                row["state"] = "queued" if scheduler_state == "RUNNING" else scheduler_state.lower()
                if scheduler_state == "COMPLETED":
                    row["state"] = "scheduler_completed_receipt_missing"
            elif scheduler_state in FAILED and row["state"] not in {"completed", "budget_limited"} and not row["state"].startswith(("failed", "skipped_", "not_started_")):
                row["producer_state"] = row["state"]
                row["state"] = "scheduler_" + scheduler_state.lower()
    except (OSError, ValueError, TypeError, KeyError) as exc:
        row["state"] = "receipt_invalid"
        row["warnings"].append(str(exc))
    return row


def evaluation_reports(paths, root, provenance):
    reports, warnings = [], []
    for relative in paths:
        path = inside(root, relative)
        try:
            value = read_json(path, provenance, root, optional=True)
            if value and value.get("format") != "latent-c6-sharded-evaluation-v1":
                raise ValueError("Unexpected evaluation aggregate format")
            reports.append({"path": str(path.relative_to(root)), "state": "available" if value else "missing",
                            "report": value})
        except (OSError, ValueError, TypeError) as exc:
            warnings.append(str(path.relative_to(root)) + ": " + str(exc))
            reports.append({"path": str(path.relative_to(root)), "state": "invalid", "report": None})
    return reports, warnings


def normalized_evaluations(reports):
    """The adapter owns scientific aggregation; this is a display-only projection."""
    evaluations, comparisons = [], []
    for entry in reports:
        report = entry.get("report")
        if not report:
            continue
        for suite in report.get("evaluations", []):
            allowed = ("id", "suite_id", "run_id", "arm", "seed", "split", "label", "policy", "primary",
                       "checkpoint_step", "checkpoint_sha256", "roster_sha256", "budgets_sha256", "source_manifest_sha256",
                       "counts", "status", "selected", "attempted", "completed", "solved", "wall_limited",
                       "missing", "infrastructure_errors", "complete_roster", "costs", "training_completed",
                       "selection_schedule_complete", "primary_comparison_eligible", "eligibility_basis")
            evaluations.append({**{key: suite[key] for key in allowed if key in suite}, "aggregate_source": entry["path"]})
        for pair in report.get("comparisons", []):
            # No comparison table is allowed to turn a partial receipt into a
            # paired estimate or a significance claim.
            if (pair.get("complete") is True and pair.get("paired") is True
                    and pair.get("primary_comparison_eligible") is True):
                allowed = ("comparison_id", "left", "right", "seed", "split", "selected", "both_solved", "left_only", "right_only", "neither_solved", "complete", "paired", "scope", "primary_comparison_eligible", "eligibility_basis")
                comparisons.append({key: pair.get(key) for key in allowed})
    return evaluations, comparisons


def snapshot(root, registry_path, manifest_path, canonical_path, report_paths, cluster, *, scheduler=True):
    provenance = {}
    registry = read_json(inside(root, registry_path), provenance, root)
    manifest = read_json(inside(root, manifest_path), provenance, root, optional=True)
    canonical = read_json(inside(root, canonical_path), provenance, root, optional=True)
    if not isinstance(registry.get("runs"), list):
        raise ValueError("Registry has no run list")
    names = [row["run_id"] for row in registry["runs"]]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate registered run IDs")
    # The registry may also contain evaluation processes, which are represented
    # by their coverage aggregates below, never as fictitious zero-step training.
    training = [row for row in registry["runs"] if row.get("max_steps", 0) > 0]
    jobs = {str(row["job_id"]) for row in registry["runs"] if row.get("job_id") and row.get("cluster") == cluster}
    if canonical:
        for row in canonical.get("jobs", []):
            if row.get("cluster") == cluster and row.get("job_id"):
                jobs.add(str(row["job_id"]))
    observations, error = scheduler_observation(jobs) if scheduler else ({}, None)
    rows = [training_row(row, root, cluster, observations, provenance) for row in training]
    reports, warnings = evaluation_reports(report_paths, root, provenance)
    evaluations, comparisons = normalized_evaluations(reports)
    report_receipts = []
    for entry in reports:
        report = entry.get("report") or {}
        report_receipts.append({"path": entry["path"], "state": entry["state"], **{key: report.get(key) for key in (
            "format", "generated_at", "job_id", "cluster", "plan_sha256", "native_replay_performed",
            "independent_checker_implementation", "model_generation_replayed", "coverage_semantics", "cost_semantics")}})
    if error:
        warnings.append("Scheduler query unavailable: " + error)
    return {"format": FORMAT, "generated_at": now(), "cluster": cluster,
            "monitor_job_id": os.environ.get("SLURM_JOB_ID"), "campaign": registry.get("campaign", {}),
            "evidence_tier": "T4", "review_state": "live-unreviewed",
            "manifest": {"path": manifest_path, "state": "bound" if manifest else "missing",
                         "sha256": provenance.get(manifest_path)},
            "training": rows, "training_states": dict(Counter(row["state"] for row in rows)),
            "evaluation_reports": report_receipts, "evaluations": evaluations, "comparisons": comparisons,
            "scheduler": {"observed_at": now(), "jobs": list(observations.values()), "error": error},
            "allocation": canonical.get("allocation", canonical.get("budget", {})) if canonical else {},
            "notes": registry.get("notes", []) + [
                "Live receipts are unreviewed computational evidence (T4). Completion and independent validation are separate.",
                "Training arms share data and update counts where registered; compute costs differ.",
                "Training completion, complete checkpoint-selection schedule and primary comparison eligibility are separate gates. Ineligible results remain exploratory.",
                "Held-out comparisons require the same target roster, seed and evaluation budget, with complete coverage. Registered per-target wall caps count as terminal budget outcomes; suite-wide missing coverage does not.",
                "Missing or failed tasks are shown separately. No p-values or pooled partial accuracy are reported.",
                "All models, checking, aggregation and dashboard generation run under cluster SLURM; this artifact is private."],
            "warnings": warnings, "source_sha256": provenance}


def publish(value, output, template):
    payload = json.dumps(value, separators=(",", ":"), allow_nan=False)
    safe = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    html = template.read_text()
    if html.count("__LATENT_WEEKEND_SNAPSHOT__") != 1:
        raise ValueError("Template snapshot marker must occur once")
    atomic(output / "snapshot.json", encoded(value))
    atomic(output / "index.html", html.replace("__LATENT_WEEKEND_SNAPSHOT__", safe))


def main():
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Scientific report projection requires a SLURM allocation")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", default="artifacts/campaign6/registry.json")
    parser.add_argument("--manifest", default="configs/campaign6-weekend.json")
    parser.add_argument("--canonical", default="status/campaign6.json")
    parser.add_argument("--evaluation-report", action="append", default=[])
    parser.add_argument("--cluster", choices=("helios", "wmi"), required=True)
    parser.add_argument("--output", default="dashboard/training/weekend")
    parser.add_argument("--template", type=Path, default=Path(__file__).with_name("weekend-template.html"))
    parser.add_argument("--watch-seconds", type=int, default=0)
    parser.add_argument("--interval", type=int, default=120)
    args = parser.parse_args()
    if not 0 <= args.watch_seconds <= 172800 or not 30 <= args.interval <= 1800:
        parser.error("Watch must be bounded by 48 hours; interval must be 30 to 1800 seconds")
    root = args.root.resolve()
    output = inside(root, args.output)
    stopped = False
    def stop(signum, frame):
        nonlocal stopped
        stopped = True
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGUSR1):
        signal.signal(sig, stop)
    deadline = time.monotonic() + args.watch_seconds
    passes = 0
    while True:
        try:
            value = snapshot(root, args.registry, args.manifest, args.canonical, args.evaluation_report, args.cluster)
            value["monitor"] = {"pass": passes + 1, "watch_seconds": args.watch_seconds, "interval_seconds": args.interval,
                                "projector_sha256": sha256(Path(__file__).read_bytes()), "template_sha256": sha256(args.template.read_bytes())}
            publish(value, output, args.template)
            passes += 1
            print(json.dumps({"state": "projected", "at": value["generated_at"], "training": len(value["training"]),
                              "evaluations": len(value["evaluations"]), "warnings": len(value["warnings"])}), flush=True)
        except (OSError, ValueError, TypeError, KeyError) as exc:
            # Keep the last good snapshot, with its original timestamp. Never
            # replace a valid report by empty success or hide watch failures.
            atomic(output / "monitor-error.json", encoded({"state": "projection_failed", "at": now(), "error": str(exc)}))
            print(json.dumps({"state": "projection_failed", "error": str(exc)}), flush=True)
            if not args.watch_seconds:
                raise
        if stopped or not args.watch_seconds or time.monotonic() >= deadline:
            break
        until = min(deadline, time.monotonic() + args.interval)
        while not stopped and time.monotonic() < until:
            time.sleep(min(1, until - time.monotonic()))


if __name__ == "__main__":
    main()
