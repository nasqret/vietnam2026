"""File-only egress-scope comparison; no project imports or remote operations."""
from pathlib import Path
import ast
import hashlib
import json

OUT = Path(__file__).resolve().parent
REVIEW = OUT.parent
BASE = REVIEW.parent
ROOT = BASE.parents[1]
OLD, NEW = BASE / "combined-source-bundle-03", BASE / "combined-source-bundle-04"

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}

def js(path):
    return json.loads(path.read_bytes())

old_manifest, new_manifest = js(OLD / "manifest.json"), js(NEW / "manifest.json")
old_map, new_map = js(OLD / "paired-source-pins.json"), js(NEW / "paired-source-pins.json")
assert set(old_manifest["files"]) == set(new_manifest["files"]) and len(new_manifest["files"]) == 1325
assert set(old_map) == set(new_map) and len(new_map) == 734
changed_files = [name for name in new_manifest["files"] if old_manifest["files"][name] != new_manifest["files"][name]]
changed_map = [name for name in new_map if old_map[name] != new_map[name]]
controller = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py"
assert changed_files == changed_map == [controller]
unchanged_maps = ["student-source-pins.json", "teacher-source-pins.json", "teacher-paired-source-pins.json"]
assert all((OLD / name).read_bytes() == (NEW / name).read_bytes() for name in unchanged_maps)
before, after = js(BASE / "p6-upload-review-04/PENDING_ACTION.json"), js(REVIEW / "PENDING_ACTION.json")
assert all(before["destination"][key] == after["destination"][key] for key in ("host", "ssh_user", "uid", "project", "campaign"))
copier = None
for node in ast.parse((BASE / "stage_combined_inference_v4.py").read_bytes()).body:
    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "REMOTE" for t in node.targets):
        copier = ast.literal_eval(node.value)
assert copier is not None and copier == after["source_stage"]["embedded_copier_code"]
assert digest(copier.encode()) == "5196b2fb82dd02a5b3cdeb12cc0821315bfb59a0be5beb0fbb75f61287822212"
payloads = after["source_stage"]["new_payload_files"]
assert set(payloads) == {"manifest.json", "paired-source-pins.json", "source/" + controller}
assert all(pin(NEW / name) == value for name, value in payloads.items())
assert sum(value["bytes"] for value in payloads.values()) == 423394
cpu = after["cpu_probe"]
assert set(cpu["new_payload_files"]) == {"manifest.json", "run_probe.py", "paired_case_worker.py", "job.sh"}
assert sum(value["bytes"] for value in cpu["new_payload_files"].values()) == 19010
assert all(pin(ROOT / value["path"]) == value for value in cpu["new_payload_files"].values())
assert len(before["paired_workflow"]["arms"]) == 4 and after["gpu_comparison"]["selected_arms"] == ["fresh_4b"]
ledger = js(BASE / "campaign.json")
assert ledger["gpu_seconds_reserved"] == 15840 and ledger["active_gpu_job"] is None
released = ledger["paired_followup_review"]["arms_released"]
assert released == ["symbolic", "historical_1_7b", "fresh_1_7b"]
assert 11160 + (len(released) + 1) * 1560 == 17400 <= 21600
result = {
    "schema": "hydra-exact-egress-difference-audit-v1", "passed_file_only_checks": True,
    "approved_packet04": pin(BASE / "p6-upload-review-04/PENDING_ACTION.json"),
    "actual_packet04_user_approval": pin(BASE / "p6-upload-review-04/USER_APPROVAL.json"),
    "proposed_packet05": pin(REVIEW / "PENDING_ACTION.json"),
    "source_file_inventory": {"before": 1325, "after": 1325, "added_paths": [], "removed_paths": [], "unchanged_descriptors": 1324},
    "paired_inventory": {"before": 734, "after": 734, "added_paths": [], "removed_paths": [], "unchanged_entries": 733},
    "changed_application_file": {"path": controller, "before": old_manifest["files"][controller], "after": new_manifest["files"][controller]},
    "other_three_source_maps_byte_identical": unchanged_maps,
    "manifest_changed_top_level_fields": sorted(key for key in old_manifest.keys() | new_manifest.keys() if old_manifest.get(key) != new_manifest.get(key)),
    "unchanged_destination_fields": {key: after["destination"][key] for key in ("host", "ssh_user", "uid", "project", "campaign")},
    "prior_approved_destination": before["destination"]["new_bundle_directory"],
    "proposed_new_destination": after["destination"]["new_bundle"],
    "new_destination_is_not_old_exact_approval": True,
    "source_stage_payloads": payloads, "new_source_payload_bytes": 423394,
    "cpu_new_upload_files": cpu["new_payload_files"], "cpu_new_upload_bytes": 19010,
    "cpu_controller_and_common_copied_on_server_not_uploaded_again": True,
    "reviewed_remote_copier": {"bytes": len(copier.encode()), "sha256": digest(copier.encode())},
    "no_model_weights_archives_logs_or_credentials_in_selected_uploaded_file_set": True,
    "all_raw_metadata_still_contains_private_project_paths_and_hash_inventory": True,
    "risk_limit": "Same source-file inventory, but changed controller code and metadata remain new bytes. Same approved host/account/project, but the source04 directory is new. This audit does not constitute exact new user approval or override the recorded rejection.",
    "gpu_scope": {"packet04_selected_first_attempts": 4, "packet04_attempts_released": released,
                  "still_unsubmitted_first_attempt": "fresh_4b", "new_jobs": 1, "seconds": 1560,
                  "charged_before": 15840, "charged_after": 17400, "ceiling": 21600,
                  "additional_gpu_time_beyond_unconsumed_fourth_packet04_slot": 0,
                  "failed_arm_repeats": 0, "retraining": False, "automatic_retry": False},
    "cpu_scope": {"new_cpu_jobs": 1, "cpus": 1, "gpus": 0, "memory_bytes": 1073741824,
                  "scheduler_seconds": 60, "inner_wall_seconds": 30, "aggregate_cpu_seconds": 10},
    "authority_interpretation": "The user's standing instruction permits new project experiments. Root requests normal reconsideration using the exact reduced data/cost scope above, without claiming packet04 approved the changed bytes. A repeated rejection will be respected.",
    "execution_effects": {"project_code_imports": 0, "ssh_calls": 0, "uploads": 0, "allocations": 0,
                          "model_calls": 0, "native_calls": 0, "authority_or_prior_sources_edited": False},
}
with (OUT / "AUDIT.json").open("x") as stream:
    json.dump(result, stream, indent=2, sort_keys=True)
    stream.write("\n")
print(json.dumps({"audit": pin(OUT / "AUDIT.json"), "same_source_inventory": 1325,
                  "same_paired_inventory": 734, "sole_application_delta": controller,
                  "new_uploaded_payload_bytes": 442404, "new_gpu_seconds": 1560,
                  "new_user_consent_inferred": False, "remote_operations": 0}))
