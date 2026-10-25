"""Assemble exact local review evidence; no imports of project execution code.

This does not approve, transfer, prepare a job, allocate, or create actual receipts.
"""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parents[1]
BUNDLE = BASE / "combined-source-bundle-04"
LAUNCHERS = BASE / "paired-launchers-v6"
PROBE = ROOT / "output/p6-paired-linux-monitor-probe-01"
PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
PYTHON = "/opt/homebrew/bin/python3.11"


def raw(path):
    assert path.is_file() and not path.is_symlink(), str(path)
    data = path.read_bytes()
    assert len(data) <= 2 * 1024**2, str(path)
    return data


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = raw(path)
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(data), "sha256": sha(data)}


def read_json(path):
    return json.loads(raw(path))


def literal(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError("Missing literal " + name)


def put(path, data):
    with path.open("xb") as stream:
        stream.write(data)


def main():
    packaging = read_json(BUNDLE / "PACKAGING.json")
    launcher_seal = read_json(LAUNCHERS / "PREPARED.json")
    probe_prepared = read_json(PROBE / "PREPARED.json")
    cpu_control = read_json(PROBE / "control/PREPARED.json")
    cpu_static = read_json(PROBE / "control/STATIC.json")
    source_stager = BASE / "stage_combined_inference_v4.py"
    copier = literal(raw(source_stager).decode(), "REMOTE")
    assert sha(copier.encode()) == packaging["remote_script"]["sha256"]
    assert pin(source_stager)["sha256"] == packaging["stager"]["sha256"]
    assert packaging["payload_pins"] == {name: {"bytes": pin(BUNDLE / name)["bytes"], "sha256": pin(BUNDLE / name)["sha256"]}
                                         for name in packaging["payload_pins"]}
    manifest = read_json(BUNDLE / "manifest.json")
    assert manifest["changed_file_count"] == 1 and manifest["file_count"] == 1325
    assert sorted(manifest["changed_files"]) == ["output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py"]
    study_path = BASE / "paired-size-study-03/study.json"
    study = read_json(study_path)
    old_study = read_json(BASE / "paired-size-study-02/study.json")
    assert {key for key in study if study[key] != old_study[key]} == {"study_id", "source_pins_sha256"}
    assert study["wall_profile"] == "fixed-wall-30-v1" and study["scope"] == "full16"
    ledger_raw = raw(BASE / "campaign.json")
    ledger = json.loads(ledger_raw)
    assert ledger["gpu_seconds_reserved"] == 15840 and ledger["campaign_gpu_hours_ceiling"] == 6
    assert ledger["active_gpu_job"] is None and ledger["active_cpu_job"] is None
    assert not any(row["attempt"].startswith("p6-paired-fresh-4b-") for row in ledger["gpu_reservations"])
    gpu_code = raw(LAUNCHERS / "remote_paired_control.py").decode()
    assert literal(gpu_code, "SELECTED_ARMS") == ("fresh_4b",)
    assert literal(gpu_code, "SELECTED_PROFILE") == "fixed-wall-30-v1"
    cpu_payload_names = ("run_probe.py", "paired_case_worker.py", "job.sh", "manifest.json")
    cpu_payloads = {name: pin(PROBE / name) for name in cpu_payload_names}
    assert sum(item["bytes"] for item in cpu_payloads.values()) == 19010
    assert pin(PROBE / "paired_controller.py")["sha256"] == literal(gpu_code, "CONTROLLER_SHA")
    choice = read_json(BASE / "paired-choice-03/CHOICE.template.json")
    assert all(value is None for group in (choice["transfer"], choice["monitor_probe"])
               for item in group.values() for value in item.values())
    command = lambda relative, *args: [PYTHON, "-B", relative, *args]
    launcher_path = "output/hydra-implementation-2026-09-04/paired-launchers-v6/paired_launchers.py"
    cpu_path = "output/p6-paired-linux-monitor-probe-01/control/probe_control.py"
    packet = {
        "schema": "hydra-bounded-monitor-followup-review-v1",
        "packet_id": "p6-upload-review-05",
        "status": "prepared_for_normal_automatic_review_not_executed",
        "specific_new_user_consent_record": None,
        "automatic_review_rejection_for_this_packet_at_preparation": False,
        "purpose": "Correct the observed owned-leader exit-accounting failure, verify the exact correction on one Linux CPU allocation, then run only the still-unsubmitted fresh4B first comparison attempt.",
        "authority_context": {
            "standing_authority": pin(ROOT / "HYDRA_EXPERIMENT_AUTHORITY.md"),
            "standing_user_quote": "You don't have to ask my permission to run new experiments.",
            "latest_automation_quote": "Further approval is not needed, it should be done automatically.",
            "automation_quote_record": pin(BASE / "p6-upload-review-03/USER_APPROVAL.json"),
            "latest_explicit_user_approval": pin(BASE / "p6-upload-review-04/USER_APPROVAL.json"),
            "latest_explicit_packet": pin(BASE / "p6-upload-review-04/PENDING_ACTION.json"),
            "interpretation": "Standing Hydra consent supports necessary bounded corrections and experiments. Packet04's completed transfer is not repeated or edited; its exact old source bytes are not silently substituted. These newly prepared transfer/control bytes go through the normal tool approval reviewer. No specific packet05 consent or successful operation is fabricated.",
            "old_rejections_preserved": True,
            "new_rejection_bypass_allowed": False,
            "per_experiment_fresh_chat_approval_rule_reinstated": False,
        },
        "selection": pin(BASE / "p6-monitor-followup-01/DECISION.json"),
        "destination": {"host": "helios.cyfronet.pl", "ssh_user": "plgnasqret", "uid": 105923,
            "project": PROJECT, "campaign": CAMPAIGN,
            "source_parent": CAMPAIGN + "/bundles/combined-source-03",
            "new_bundle": CAMPAIGN + "/bundles/combined-source-04",
            "cpu_package": CAMPAIGN + "/diagnostics/p6-paired-linux-monitor-probe-01",
            "gpu_job_directory": CAMPAIGN + "/jobs/p6-paired-fresh-4b-v5-01",
            "unrelated_paths_or_jobs_may_be_modified": False},
        "budget": {"ledger_snapshot": {"path": "campaign-before-packet05.json", "bytes": len(ledger_raw), "sha256": sha(ledger_raw)},
            "charged_gpu_seconds_before": 15840, "maximum_new_gpu_jobs": 1,
            "new_gpu_seconds": 1560, "charged_gpu_seconds_after": 17400,
            "campaign_gpu_seconds_ceiling": 21600, "remaining_after_seconds": 4200,
            "full_failed_and_short_allocations_remain_charged": True,
            "recheck_actual_ledger_before_each_mutation": True, "simultaneous_owned_gpu_jobs": 1},
        "source_stage": {"packaging": packaging, "packaging_file": pin(BUNDLE / "PACKAGING.json"),
            "stager": pin(source_stager), "embedded_copier_code": copier,
            "new_payload_files": {name: pin(BUNDLE / name) for name in packaging["payload_pins"]},
            "actual_command": command("output/hydra-implementation-2026-09-04/stage_combined_inference_v4.py", "--stage"),
            "maximum_attempts": 1, "old_sources_unchanged_required": True,
            "private_source_and_inventory_egress_explicitly_in_scope": True,
            "weights_or_archive_uploaded": False},
        "cpu_probe": {"frozen_preparation": probe_prepared, "preparation_file": pin(PROBE / "PREPARED.json"),
            "control_preparation": cpu_control, "control_static_checks": cpu_static,
            "control_files": {name: pin(PROBE / "control" / name) for name in ("probe_control.py", "remote_probe_control.py", "PREPARED.json", "STATIC.json", "README.md")},
            "remote_phase_code": raw(PROBE / "control/remote_probe_control.py").decode(),
            "new_payload_files": cpu_payloads, "new_payload_raw_bytes": 19010,
            "server_side_ordinary_copies": {name: pin(PROBE / name) for name in ("paired_controller.py", "paired_common.py")},
            "allocation": {"account": "plgccaiautore2026-cpu", "partition": "plgrid", "cpus": 1, "nodes": 1, "gpus": 0, "memory_bytes": 1073741824, "scheduler_seconds": 60},
            "inner_probe_bounds": {"wall_seconds": 30, "aggregate_cpu_seconds": 10, "sequential_children": 2, "maximum_simultaneous_children": 1},
            "scheduler_envelope_interpretation": "The 60-second Slurm ceiling includes startup and shutdown; the actual probe remains bounded to 30 wall seconds and 10 aggregate CPU seconds. This does not select 60 seconds of probe work.",
            "actual_completion_contract": pin(PROBE / "ACTUAL_COMPLETION_CONTRACT.json"),
            "commands": {"stage": command(cpu_path, "stage", "--nonce", "ACTUAL_NEW_32_LOWERCASE_HEX_NONCE"),
                "submit_held": command(cpu_path, "submit-held"), "release": command(cpu_path, "release"),
                "collect": command(cpu_path, "collect", "--observation", "ACTUAL_FRESH_OBSERVATION_INDEX")},
            "maximum_jobs": 1, "actual_cpu_success_required_before_gpu": True,
            "no_model_native_solver_or_training_work": True,
            "unobserved_rss_transition_must_not_be_reported_as_reproduced": True},
        "gpu_comparison": {"launcher_seal": launcher_seal, "launcher_seal_file": pin(LAUNCHERS / "PREPARED.json"),
            "separate_read_only_review": pin(LAUNCHERS / "REVIEW.json"),
            "local_launcher": pin(LAUNCHERS / "paired_launchers.py"),
            "remote_phase_controller": pin(LAUNCHERS / "remote_paired_control.py"),
            "remote_phase_code": gpu_code,
            "ssh_control_egress": "Every submit/release/collect sends this exact remote controller. Submit/release additionally send the same pinned734-entry paired map, study raw text, bounded spec and (release only) actual reservation; collect sends only spec/reservation and returns whitelisted evidence.",
            "study_file": pin(study_path), "study": study,
            "study_derivation": pin(BASE / "paired-size-study-03/DERIVATION.json"),
            "choice_template": pin(BASE / "paired-choice-03/CHOICE.template.json"),
            "paired_source_map": pin(BUNDLE / "paired-source-pins.json"),
            "training_metadata_admission_helper": pin(BASE / "pilot-completion-admission-v3/pilot_admission.py"),
            "selected_arms": ["fresh_4b"], "attempt": "p6-paired-fresh-4b-v5-01",
            "declared_other_study_roles_are_not_launch_authority": True,
            "allocation": {"account": "plgccaiautore2026-gpu-gh200", "partition": "plgrid-gpu-gh200", "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64, "seconds": 1560},
            "cases": 16, "positives": 12, "negative_controls": 4,
            "per_case_limits": {"total_seconds": 90, "load_seconds": 45, "search_seconds": 30, "search_return_grace_seconds": 2, "replay_seconds": 13, "model_calls": 16},
            "native_and_model_work_limits_unchanged": True,
            "features": {"planner": False, "ranker": False, "library": False, "external_advisers": [], "classical": False},
            "commands": {"prepare": command(launcher_path, "prepare", "--choice", "output/hydra-implementation-2026-09-04/paired-choice-03/CHOICE.json", "--choice-sha256", "ACTUAL_CHOICE_SHA256", "--ledger-sha256", "ACTUAL_CURRENT_LEDGER_SHA256"),
                "submit_held": command(launcher_path, "submit-held", "--arm", "fresh_4b", "--prepared-sha256", "ACTUAL_PREPARED_SHA256", "--ledger-sha256", "ACTUAL_CURRENT_LEDGER_SHA256"),
                "release": command(launcher_path, "release", "--arm", "fresh_4b", "--prepared-sha256", "ACTUAL_PREPARED_SHA256", "--ledger-sha256", "ACTUAL_CURRENT_LEDGER_SHA256"),
                "collect": command(launcher_path, "collect", "--arm", "fresh_4b", "--prepared-sha256", "ACTUAL_PREPARED_SHA256", "--index", "ACTUAL_FRESH_INDEX_1_TO_128")},
            "execution_gate": "Only after genuine source04 transfer, CPU process/scheduler success, actual receipt binding and local prepare. Separate one-use held submit, resource/owner check, full immutable charge intent, release and bounded read-only collections. No retries or automatic next action.",
            "reporting": "Report corrected-source4B separately. Source03 symbolic is a descriptive reference, not a complete matched four-arm result; failed or missing model arms are not zero accuracy."},
        "permitted_variable_bindings": ["One fresh CPU nonce and one fresh GPU nonce (32 lowercase hex each)", "The actual held CPU/GPU job IDs from successful sbatch", "Hashes of actual completed transfer/probe/choice/preparation evidence", "Fresh bounded read-only observation indices", "Observed scheduler/process/results and real tool completion identifiers"],
        "exclusions": ["Retraining, optimizer updates, resume, requeue, or any automatic retry", "Repeated symbolic, historical1.7B or fresh1.7B arms", "The old unsubmitted source03 fresh4B attempt", "Teacher fixes, teacher allocation, student distillation, or8B training", "Higher case/model/search/resource limits or different theorems", "GPU budget expansion or refunds of prior allocation ceilings", "Changes to historical source, weights, manifests, results, authority or reviews", "Any unrelated job cancellation or source/secret/credential upload", "Treating SSH/collection success as study or proof success"],
        "preparation_effects": {"file_reads_and_new_local_review_files_only": True, "project_execution_code_imports": 0, "ssh_calls": 0, "allocations": 0, "model_calls": 0, "native_runs": 0, "ledger_writes": 0, "actual_completion_or_consent_fabricated": False},
    }
    data = (json.dumps(packet, indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n").encode()
    assert len(data) <= 256 * 1024
    put(HERE / "campaign-before-packet05.json", ledger_raw)
    put(HERE / "PENDING_ACTION.json", data)
    print(json.dumps({"packet": pin(HERE / "PENDING_ACTION.json"), "source_payload_bytes": 423394,
                      "cpu_payload_bytes": 19010, "new_gpu_jobs": 1, "new_gpu_seconds": 1560,
                      "uploads": 0, "allocations": 0, "approved": False}))


if __name__ == "__main__":
    main()
