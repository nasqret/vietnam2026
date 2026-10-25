"""Read-only comparison audit; never runs search, a model, or a scheduler.

Each arm needs a collected raw sacct record and an actual successful collection
receipt. An SSH exit alone is not an allocated job's terminal exit.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import re

from paired_common import (FEATURES, HOLDOUT_SHA, KERNEL_SHA, MODEL_LIMITS, NATIVE_MANIFEST_SHA,
    ORIGINAL, PROVIDER_SHA, canonical, holdout_cases, legacy_study_spec, ordinary, pin,
    proof_acceptance, require, save, strict_json, study_spec, validate_counts)
from paired_controller import SLICE_SHA, classify_case, selected_cases
from teacher_exposure import PUBLIC_KIND, TENSOR_KIND

BASELINE_MAP_SHA = "382098dc8a3f9d79370006d874e4afef23a83896486cd686b87f0d7397040395"
OLD_SCOPE = "output/hydra-implementation-2026-09-04/paired-evaluation-v2/"
NEW_SCOPE = "output/hydra-implementation-2026-09-04/teacher-paired-evaluation-v1/"


def terminal_sacct(raw, job_id):
    require(type(raw) is str and len(raw.encode()) <= 65536, "Bounded raw sacct evidence is required.")
    records = []
    lines = raw.strip().splitlines()
    require(1 <= len(lines) <= 32, "Unexpected scheduler row count.")
    for line in lines:
        fields = line.split("|")
        if fields[-1] == "":
            fields.pop()
        require(len(fields) == 6 and (fields[0] == job_id or fields[0].startswith(job_id + ".")),
                "Use exact no-header JobIDRaw|State|ExitCode|ElapsedRaw|AllocTRES|TimelimitRaw output.")
        if fields[0] != job_id:
            continue
        require(fields[1] in {"COMPLETED", "FAILED", "TIMEOUT", "CANCELLED", "OUT_OF_MEMORY", "NODE_FAIL",
                              "PREEMPTED", "BOOT_FAIL", "DEADLINE"}
                or re.fullmatch(r"CANCELLED by \d+", fields[1]), "Job is not in a recorded terminal scheduler state.")
        exit_parts = fields[2].split(":")
        require(len(exit_parts) == 2 and all(part.isdigit() for part in exit_parts)
                and fields[3].isdigit() and fields[5].isdigit(), "Missing actual terminal exit/time values.")
        tres = {}
        for item in fields[4].split(","):
            key, value = item.split("=", 1)
            require(key not in tres, "Duplicate actual allocated TRES.")
            tres[key] = value
        require(tres.get("gres/gpu") == "1" and tres.get("cpu") == "8" and tres.get("node") == "1"
                and tres.get("mem") in {"64G", "65536M"}, "Actual completed job resources differ.")
        records.append({"job_id": job_id, "state": fields[1].split(" by ")[0],
            "exit_code": int(exit_parts[0]), "exit_signal": int(exit_parts[1]),
            "elapsed_seconds": int(fields[3]), "allocated_limit_seconds": int(fields[5]) * 60,
            "gpus": 1, "cpus": 8, "memory_gib": 64})
    require(len(records) == 1, "One exact allocation-level sacct row is required.")
    return records[0]


def audit_arm(directory, receipt_path, receipt_sha, study, study_sha, cases):
    directory = Path(directory)
    raw = ordinary(receipt_path, 65536)
    require(sha256(raw).hexdigest() == receipt_sha, "Collected terminal receipt pin differs.")
    receipt = strict_json(raw)
    require(receipt.get("schema") == "hydra-paired-terminal-collection-v1"
            and type(receipt.get("actual_transport_exit_code")) is int
            and receipt.get("actual_transport_exit_code") == 0
            and type(receipt.get("completion_chunk")) is str and receipt["completion_chunk"]
            and type(receipt.get("raw_sacct")) is dict, "Actual terminal collection receipt is missing.")
    artifact = receipt["raw_sacct"]
    raw_path = Path(receipt_path).parent / artifact["path"]
    require(raw_path.resolve().is_relative_to(Path(receipt_path).resolve().parent)
            and pin(raw_path, 65536) == {key: artifact[key] for key in ("bytes", "sha256")},
            "Raw scheduler evidence changed or escaped its receipt directory.")
    terminal = terminal_sacct(ordinary(raw_path, 65536).decode(), receipt["job_id"])
    completion = strict_json(ordinary(directory / "completion.json"))
    request = strict_json(ordinary(directory / "request.json"))
    require(completion["job_id"] == terminal["job_id"] == request["reservation"]["job_id"]
            and completion["study_sha256"] == request["study_sha256"] == study_sha
            and canonical(request["study"]) == canonical(study)
            and terminal["allocated_limit_seconds"] == request["reservation"]["seconds"],
            "Arm, study, or actual allocation binding differs.")
    require(sha256(canonical(request["source_pins_before"])).hexdigest() == study["source_pins_sha256"]
            and completion.get("sources_unchanged") is True
            and completion["source_pins_after"] == request["source_pins_before"],
            "Executed sources changed or differ between arms.")
    arm = completion["arm"]
    require(arm in study["arms"] and arm == request["reservation"]["arm"], "Undeclared completed arm.")
    expected = {row["id"]: row for row in cases}
    rows = []
    identities = set()
    for index, row in enumerate(completion["cases"]):
        require(index < len(cases) and row["case_id"] == cases[index]["id"], "Case order differs or a case was retried.")
        case = expected[row["case_id"]]
        execution_path = directory / row["execution_path"]
        require(execution_path.resolve().is_relative_to(directory.resolve())
                and pin(execution_path) == row["execution_pin"], "Actual child exit receipt changed.")
        execution = strict_json(ordinary(execution_path))
        result = None
        if row["result_path"] is not None:
            result_path = directory / row["result_path"]
            require(result_path.resolve().is_relative_to(directory.resolve())
                    and pin(result_path) == row["result_pin"], "Case result pin differs.")
            result = strict_json(ordinary(result_path))
            require(result["original_input_theorem"] == case["theorem"]
                    and result["source_pins_sha256"] == result["source_pins_after_sha256"] == study["source_pins_sha256"],
                    "A case changed its original input/source identity.")
        status = classify_case(execution, result)
        require(status == row["status"], "Public status differs from authoritative process/resource evidence.")
        checked = False
        counts = None
        if status in {"proved", "unknown"}:
            require(result.get("kernel_identity") == {"native_manifest_sha256": NATIVE_MANIFEST_SHA, "kernel_sha256": KERNEL_SHA}
                    and canonical(result.get("features")) == canonical(FEATURES), "Completed result changed the native authority/features.")
            counts = validate_counts(result["search"], result["model"], result["model_policy"])
            require(counts == result["actual_counters"], "Public actual counters differ from the underlying records.")
            checked = proof_acceptance(result["search"], result["independent_original_replay"], result["canonical_theorem"])
            require(checked == (status == "proved") == result["native_checked"], "Native proof acceptance differs.")
            if result["model"] is not None:
                identity = result["model"]["identity"]
                identities.add(identity["model_manifest_sha256"])
                require(identity.get("source_sha256") == PROVIDER_SHA
                        and identity["adapter"].get("saved_adapter_reload_checked") is True
                        and identity["model_manifest_sha256"] == sha256(canonical({k: v for k, v in identity.items() if k != "model_manifest_sha256"})).hexdigest(),
                        "Exact fresh tensor reload/provider identity is missing.")
                require(identity["adapter"]["adapter_manifest_sha256"]
                        == study["arms"][arm]["adapter_manifest_sha256"], "Selected saved adapter changed between cases.")
                if arm in {"fresh_1_7b", "distilled_1_7b"}:
                    expected = study["distilled_training_exposure"] if arm == "distilled_1_7b" else study["fresh_training_exposure"]
                    require(result.get("training_exposure") == expected
                            and identity["adapter"].get("adapter_kind") == TENSOR_KIND,
                            "Public training exposure or frozen tensor compatibility contract differs.")
                if arm == "distilled_1_7b":
                    admission = result.get("teacher_exposure_admission") or {}
                    require(admission.get("public_adapter_kind") == PUBLIC_KIND
                            and admission.get("tensor_loader_contract") == TENSOR_KIND
                            and admission.get("teacher_admission_sha256") == study["teacher_admission"]["sha256"]
                            and admission.get("teacher_exposure") == study["distilled_training_exposure"]
                            and admission.get("teacher_evidence_sent_to_search") is False
                            and admission.get("provider_identity_modified") is False,
                            "The teacher arm lacks separate admitted data provenance before its actual load.")
        search = None if result is None else result["search"]
        rows.append({"case_id": case["id"], "family": case["family"], "category": case["category"],
            "status": status, "kernel_checked_and_replayed": checked, "counters": counts,
            "actual_child_exit": execution["exit_code"], "quiescent": execution["quiescent"],
            "case_wall_seconds": execution["elapsed_seconds"], "sampled_host_peak_rss_bytes": execution["peak_sampled_host_rss_bytes"],
            "model_construction_seconds": None if result is None else result["model_construction_seconds"],
            "post_load_provider_seconds": None if result is None else result["post_load_provider_seconds"],
            "gpu_memory": None if result is None else result["gpu_memory"],
            "proof_cost": None if search is None else search["proof_cost"],
            "native_timing": None if search is None else search["native_timing"],
            "native_work": None if search is None else {key: search[key] for key in
                ("tactic_attempts", "states_expanded", "states_discovered", "depth_reached")},
            "winning_steps": None if not checked else {source: sum(step["source"] == source for step in search["provenance"])
                                                       for source in ("heuristic", "model")}})
    require(len(identities) <= 1, "Base/tokenizer/adapter/provider identity varied within an arm.")
    complete = (completion["status"] == "complete" and len(rows) == len(cases)
                and terminal["state"] == "COMPLETED" and terminal["exit_code"] == terminal["exit_signal"] == 0)
    positives = [row for row in rows if row["category"] == "prospective_positive"]
    controls = [row for row in rows if row["category"] == "negative_control"]
    return {"arm": arm, "execution_complete": complete, "terminal": terminal, "cases": rows,
        "positive_proofs": sum(row["kernel_checked_and_replayed"] for row in positives),
        "positive_case_count": sum(case["category"] == "prospective_positive" for case in cases),
        "control_checked_proofs": sum(row["kernel_checked_and_replayed"] for row in controls),
        "control_case_count": sum(case["category"] == "negative_control" for case in cases),
        "counter_accounting_complete": len(rows) == len(cases) and all(row["counters"] is not None for row in rows),
        "model_identity_sha256": next(iter(identities), None), "not_run": completion["not_run"]}


def reuse_compatible(old_study, study, old_pins, new_pins):
    """A guarded full16 baseline may contribute its already-declared five rows."""
    legacy_study_spec(old_study, SLICE_SHA)
    require(old_study["scope"] == "full16" and study["scope"] == "paired5"
            and old_study["comparison"] == study["comparison"] == "fixed_native_work_guarded"
            and old_study["wall_profile"] == study["wall_profile"] == "guarded-work-60-v1",
            "Full16 guarded baseline reuse cannot stand in for a fixed-wall or changed-budget baseline.")
    for key in ("features", "native_work", "model_limits", "resource_limits", "holdout_sha256", "slice_sha256", "fresh_training_exposure"):
        require(canonical(old_study[key]) == canonical(study[key]), "Baseline reuse changed shared inputs/exposure/limits: " + key)
    require(old_study["arms"]["fresh_1_7b"] == study["arms"]["fresh_1_7b"], "Baseline reuse selected a different saved model or Base path.")
    require(sha256(canonical(old_pins)).hexdigest() == old_study["source_pins_sha256"] == BASELINE_MAP_SHA
            and sha256(canonical(new_pins)).hexdigest() == study["source_pins_sha256"], "Baseline or new executed source map differs.")
    old_runtime = {k: v for k, v in old_pins.items() if not k.startswith(OLD_SCOPE)}
    new_runtime = {k: v for k, v in new_pins.items() if not k.startswith(NEW_SCOPE)}
    require(old_runtime == new_runtime and old_runtime,
            "Only the separately reviewed admission/controller-report branch may differ; search/provider/kernel bytes cannot change.")
    return True


def audit_reused_baseline(item, study, cases, all_cases, new_pins):
    require(set(item) == {"directory", "receipt", "receipt_sha256", "baseline_study", "baseline_study_sha256"},
            "Baseline reuse requires original complete arm receipts and its original study.")
    raw = ordinary(item["baseline_study"])
    require(sha256(raw).hexdigest() == item["baseline_study_sha256"], "Original baseline study changed.")
    old_study = strict_json(raw)
    request = strict_json(ordinary(Path(item["directory"]) / "request.json"))
    reuse_compatible(old_study, study, request["source_pins_before"], new_pins)
    audited = audit_arm(item["directory"], item["receipt"], item["receipt_sha256"], old_study,
        item["baseline_study_sha256"], all_cases)
    require(audited["arm"] == "fresh_1_7b" and audited["execution_complete"] is True
            and len(audited["cases"]) == 16, "Only a genuinely complete original full16 fresh arm can be reused.")
    by_id = {row["case_id"]: row for row in audited["cases"]}
    rows = [by_id[case["id"]] for case in cases]
    positives = [r for r in rows if r["category"] == "prospective_positive"]
    controls = [r for r in rows if r["category"] == "negative_control"]
    return {**audited, "cases": rows, "positive_proofs": sum(r["kernel_checked_and_replayed"] for r in positives),
        "positive_case_count": len(positives), "control_checked_proofs": sum(r["kernel_checked_and_replayed"] for r in controls),
        "control_case_count": len(controls), "counter_accounting_complete": all(r["counters"] is not None for r in rows),
        "reused_baseline": {"original_scope": "full16", "original_case_count": 16,
            "original_study_sha256": item["baseline_study_sha256"], "original_source_pins_sha256": BASELINE_MAP_SHA,
            "original_terminal_receipt_sha256": item["receipt_sha256"], "selected_case_ids": [r["case_id"] for r in rows],
            "original_results_modified": False, "new_baseline_jobs_launched": 0,
            "source_delta": "Only separately reviewed exposure admission and comparison reporting; native search/provider/kernel unchanged"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--study-sha256", required=True)
    parser.add_argument("--completed-arms", type=Path, required=True,
                        help="Original receipts; a fresh baseline may additionally name its original full16 baseline_study and SHA.")
    parser.add_argument("--completed-arms-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raw = ordinary(args.study)
    require(sha256(raw).hexdigest() == args.study_sha256, "Study pin differs.")
    study = study_spec(strict_json(raw), SLICE_SHA)
    cases = selected_cases(args.app_root, study)
    raw_inputs = ordinary(args.completed_arms)
    require(sha256(raw_inputs).hexdigest() == args.completed_arms_sha256, "Explicit completed-arm descriptors changed.")
    inputs = strict_json(raw_inputs)
    require(set(inputs) <= set(study["arms"]), "Unexpected arm in comparison input.")
    records = []
    for name, item in inputs.items():
        require(type(item) is dict, "Malformed completed-arm descriptor.")
        if "baseline_study" in item:
            require(name == "fresh_1_7b" and "distilled_1_7b" in inputs,
                    "Reuse applies only to the fresh baseline beside an actual teacher-arm record.")
            new_request = strict_json(ordinary(Path(inputs["distilled_1_7b"]["directory"]) / "request.json"))
            require(new_request["study_sha256"] == args.study_sha256, "The new teacher arm does not bind this study.")
            record = audit_reused_baseline(item, study, cases, holdout_cases(args.app_root / "evaluation-holdout.json"),
                                          new_request["source_pins_before"])
        else:
            require(set(item) == {"directory", "receipt", "receipt_sha256"}, "Malformed completed-arm descriptor.")
            record = audit_arm(item["directory"], item["receipt"], item["receipt_sha256"], study, args.study_sha256, cases)
        require(record["arm"] == name, "Duplicate/substituted arm descriptor.")
        records.append(record)
    complete = (set(inputs) == set(study["arms"]) and all(row["execution_complete"] for row in records)
                and not any(row["control_checked_proofs"] for row in records))
    value = {"schema": "hydra-p7-teacher-paired-comparison-v1", "status": "complete" if complete else "incomplete",
        "study_sha256": args.study_sha256, "holdout_sha256": HOLDOUT_SHA, "scope": study["scope"],
        "comparison": study["comparison"], "wall_profile": study["wall_profile"], "arms": records,
        "missing_arms": sorted(set(study["arms"]) - set(inputs)),
        "prospective_suite_not_independently_sealed": True, "pretraining_independence_claimed": False,
        "controls_unknown_are_not_refuted": True, "resource_stops_are_not_false_theorems": True,
        "historical_torch_control_is_not_an_archived_MLX_reproduction": True,
        "fresh_size_training_exposure": study["fresh_training_exposure"],
        "teacher_training_exposure": study["distilled_training_exposure"], "teacher_admission": study["teacher_admission"],
        "teacher_effect_includes_extra_training_rows_and_optimizer_work": True,
        "matched_training_compute_or_teacher_quality_isolation_claimed": False,
        "public_distilled_kind": PUBLIC_KIND, "unchanged_tensor_loader_compatibility_kind": TENSOR_KIND,
        "local_MLX_deployment_validated": False, "reserved_slice_case_count": 5,
        "promotes_default_components": False, "training_allowed": False, "retrieval_allowed": False}
    save(args.output, value)
    return 0 if complete else 2


if __name__ == "__main__":
    raise SystemExit(main())
