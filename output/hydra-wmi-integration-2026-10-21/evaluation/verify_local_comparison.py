#!/usr/bin/env python3
"""Offline post-run verifier. No model/native import or proof execution.

Read private outcomes only here, after both arms have terminal supervisor files.
This validates evidence produced by the pinned executed harness; it does not
turn saved fixtures into fresh inference or run a third native replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CHECKPOINTS = {
    "historical_local_mlx": "7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5",
    "wmi_c6_vanilla47_step8192": "c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731",
}
SOURCE_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
SOURCE_MANIFEST = "8208f41172a375b59592f916836a229a9e784c05d3f9de8d4f7e7e260f62fdf3"
NATIVE_ENVIRONMENT = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
LIMITS = {"max_actions": 128, "max_new_tokens": 128, "max_total_decision_tokens": 16384,
          "max_context_tokens": 6144, "wall_seconds": 300.0}
VALID_STATUSES = {"proved", "tactic_error", "tactic_limit", "kernel_rejection", "deadline",
                  "action_budget", "token_budget", "no_candidate"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load(path, checksum=None):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 16 * 1024**2,
            "Missing/unsafe/oversized evidence: " + str(path))
    raw = path.read_bytes()
    require(checksum is None or sha(raw) == checksum, "Evidence SHA differs: " + str(path))
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result
    def bad(_):
        raise ValueError("Nonfinite JSON")
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad), {"bytes": len(raw), "sha256": sha(raw)}


def checked_child(root, item):
    name = item["path"]
    require(type(name) is str and Path(name).name == name, "Unsafe child evidence path")
    value, actual = load(root / name, item["sha256"])
    require(actual["bytes"] == item["bytes"], "Evidence byte count differs")
    return value


def count(value, maximum, label):
    require(type(value) is int and 0 <= value <= maximum, "Invalid " + label)
    return value


def trace_projection(receipt):
    keys = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")
    return [{key: row.get(key) for key in keys} for row in receipt["trace"] if "v" in row]


def check_proof(result, case_id):
    actions = result["actions"]
    require(actions and result["actual_model_calls"] >= len(actions) and result["actual_decision_tokens"] > 0,
            case_id + ": proof has no actual generated work")
    theorem = result["theorem"]
    original, replay = result["last_native_result"], result["independent_replay"]
    for receipt in (original, replay):
        require(receipt["status"] == "proved" and receipt["kernel_checked"] is True
                and receipt["theorem"] == theorem and receipt["classical"] is False
                and receipt["environment_sha256"] == NATIVE_ENVIRONMENT
                and receipt["goals"] == [] and receipt["failed_tactics"] == 0
                and receipt["failed_step"] is None and receipt["error"] is None,
                case_id + ": invalid native proof receipt")
        trace = trace_projection(receipt)
        require(len(trace) == len(actions) == receipt["tactics_applied"] == receipt["tactics_requested"]
                and all(row["status"] == "ok" and row["error"] is None and row["focus"] == 0
                        and row["step"] == index for index, row in enumerate(trace, 1)),
                case_id + ": native proof action accounting differs")
        footer = receipt["trace"][-1]
        require(footer.get("qed") is True and footer.get("theorem") == theorem
                and footer.get("tactic_count") == len(actions)
                and footer.get("proof_size") == receipt["proof_nodes"] == result["certificate_nodes"]
                and type(receipt["proof_nodes"]) is int and receipt["proof_nodes"] > 0,
                case_id + ": missing complete original-theorem QED")
    require(trace_projection(original) == trace_projection(replay), case_id + ": independent replay transitions differ")
    evidence = result["independent_replay_evidence"]
    require(evidence["status"] == "completed" and evidence["actual_exit_code"] == 0
            and evidence["stdout"]["bytes"] > 0 and 0 <= evidence["seconds"] <= 30.1,
            case_id + ": missing actual completed fresh replay child")


def validate_case(record, row, arm):
    case_id = row["id"]
    require(record["schema"] == "hydra-local-matched-case-v1" and record["arm"] == arm
            and record["id"] == case_id and record["input_theorem"] == row["theorem"]
            and record["input_theorem_sha256"] == sha(row["theorem"].encode())
            and record["input_file_sha256"] == row["input_file_sha256"]
            and record["panel_id"] == row["panel_id"], case_id + ": literal case binding differs")
    result, provider = record["result"], record["provider"]
    require(result["schema"] == "hydra-sequential-lane-v1" and result["evidence_kind"] == "fresh_inference"
            and result["input_theorem"] == row["theorem"] and result["limits"] == LIMITS
            and result["heuristic_actions"] == 0 and result["search_branches"] == 1,
            case_id + ": not the matched fresh sequential lane")
    require(result["status"] in VALID_STATUSES and type(result["proved"]) is bool
            and result["proved"] is (result["status"] == "proved"), case_id + ": invalid/incomplete case status")
    admission = result["admission"]
    require(admission["input_theorem"] == row["theorem"] and admission["theorem"] == result["theorem"],
            case_id + ": input was not admitted unchanged through the canonical parser")
    identity = result["native_identity"]
    require(identity["source_commit"] == SOURCE_COMMIT and identity["source_manifest_sha256"] == SOURCE_MANIFEST
            and identity["environment_sha256"] == NATIVE_ENVIRONMENT and identity["allowed_theorems"] == []
            and identity["classical"] is False and identity["limits"]["max_binders"] == 64,
            case_id + ": native authority/source/profile differs")
    calls = count(result["actual_model_calls"], 128, "actual calls")
    tokens = count(result["actual_decision_tokens"], 16384, "actual tokens")
    require(provider["actual_model_calls"] == calls and provider["generated_token_slots"] == tokens
            and provider["kernel_checked"] is False and provider["model_loaded"] is True,
            case_id + ": provider/lane counters differ")
    require(0 <= result["wall_seconds"] <= 360 and 0 <= record["case_wall_seconds"] <= 360,
            case_id + ": unbounded case wall time")
    steps, actions = result["steps"], result["actions"]
    require(len(actions) <= len(steps) <= 128 and len(steps) - len(actions) <= 1,
            case_id + ": invalid trajectory length")
    step_calls = step_tokens = step_forwards = step_attempted = 0
    flattened = []
    for index, step in enumerate(steps, 1):
        require(step["index"] == index, case_id + ": step ordering differs")
        item = step["provider"]
        step_calls += count(item["actual_model_calls"], 1, "one-step actual calls")
        step_tokens += count(item["generated_token_slots"], 128, "one-step decision tokens")
        step_forwards += count(item["forward_passes"], 128, "one-step completed forwards")
        step_attempted += count(item["forward_attempts"], 129, "one-step attempted forwards")
        flattened.extend(item["attempts"])
        require(sum(len(attempt["decision_ids"]) for attempt in item["attempts"]) == item["generated_token_slots"],
                case_id + ": actual token IDs/counter differ")
        for attempt in item["attempts"]:
            if "generation" in attempt:
                generation = attempt["generation"]
                require(generation["provenance"]["checkpoint_sha256"] == CHECKPOINTS[arm]
                        and generation["policy"] == {"kind": "fixed", "depth": 1}
                        and generation["decision_ids"] == attempt["decision_ids"],
                        case_id + ": generation checkpoint/policy differs")
        if index <= len(actions):
            require(step["action"] == actions[index - 1] and len(item["attempts"]) == 1,
                    case_id + ": action was repaired or lacks its one-call receipt")
            attempt = item["attempts"][0]
            require(attempt["status"] == "suggested" and attempt["action"] == actions[index - 1]
                    and attempt["prompt_sha256"] == step["prompt_sha256"]
                    and attempt["strict_generation"]["valid_action"] is True
                    and attempt["strict_generation"]["action"] == actions[index - 1]
                    and attempt["generation"]["eos"] is True
                    and attempt["generation"]["stop_reason"] == "eos"
                    and not attempt["generation"].get("budget_expired", False)
                    and actions[index - 1].split()[0] != "use", case_id + ": action lacks strict literal EOS provenance")
    require((step_calls, step_tokens, step_forwards, step_attempted) == (
                calls, tokens, result["forward_passes"], result["forward_attempts"])
            and flattened == provider["attempts"], case_id + ": aggregate actual work is inconsistent")
    if result["proved"]:
        check_proof(result, case_id)
    return {"id": case_id, "proved": result["proved"], "status": result["status"],
            "actual_model_calls": calls, "actual_decision_tokens": tokens,
            "wall_seconds": record["case_wall_seconds"], "native_identity": identity}


def validate_arm(root, arm, spec, spec_sha, rows):
    root = Path(root)
    supervision, supervision_pin = load(root / "supervisor.json")
    require(supervision["schema"] == "hydra-local-matched-supervisor-v1" and supervision["arm"] == arm
            and supervision["status"] == "completed" and supervision["actual_exit_code"] == 0
            and supervision["completed_cases"] == supervision["required_cases"] == 18
            and supervision["spec_sha256"] == spec_sha and supervision["automatic_retry"] is False
            and supervision["problem"] is None and supervision["phase_hard_seconds"] == spec["phase_hard_seconds"],
            arm + ": supervisor did not complete the full matched arm")
    for label, filename in (("stdout", "child.stdout.jsonl"), ("stderr", "child.stderr.txt")):
        raw = (root / filename).read_bytes()
        require({"bytes": len(raw), "sha256": sha(raw)} == supervision[label], arm + ": raw transport stream changed")
    receipt = checked_child(root, supervision["arm_receipt"])
    require(receipt["schema"] == "hydra-local-matched-arm-v1" and receipt["arm"] == arm
            and receipt["spec_sha256"] == spec_sha and receipt["status"] == "completed"
            and receipt["evidence_kind"] == "fresh_local_mlx_inference" and receipt["limits"] == LIMITS
            and receipt["final_custody"]["status"] == "completed"
            and receipt["shared_load_outside_case_time"] is True,
            arm + ": arm custody/provenance is incomplete")
    require([r["id"] for r in receipt["cases"]] == [r["id"] for r in rows], arm + ": case order/membership differs")
    validated = {}
    for entry, row in zip(receipt["cases"], rows):
        value = validate_case(checked_child(root, entry), row, arm)
        require(all(entry[key] == value[key] for key in ("id", "status", "proved", "actual_model_calls", "actual_decision_tokens")),
                arm + ": case summary differs")
        validated[row["id"]] = value
    return validated, {"directory": str(root.resolve()), "supervisor": supervision_pin,
                       "arm_receipt": supervision["arm_receipt"], "load_identity": receipt["load_identity"],
                       "load_wall_seconds": receipt["load_wall_seconds"], "arm_wall_seconds": receipt["wall_seconds"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    for key in ("spec", "spec-sha256", "old", "wmi", "expectations", "expectations-sha256", "output"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args()
    spec, spec_pin = load(args.spec, args.spec_sha256)
    # Both terminal observations must exist before the verifier opens private gold.
    for folder in (args.old, args.wmi):
        require((Path(folder) / "supervisor.json").is_file(), "Wait for both terminal supervisor receipts")
    expected, expected_pin = load(args.expectations, args.expectations_sha256)
    require(expected["model_access_permitted"] is False, "Expected private outcomes")
    rows = []
    for item in spec["inputs"]:
        data, _ = load(item["path"], item["sha256"])
        rows.extend({**row, "panel_id": data["panel_id"], "input_file_sha256": item["sha256"]} for row in data["cases"])
    gold = {r["id"]: r for r in expected["primary_cases"] + expected["regression_cases"]}
    require(len(rows) == len(gold) == 18 and {r["id"] for r in rows} == set(gold)
            and all(r["theorem"] == gold[r["id"]]["theorem"] for r in rows), "Private/input binding differs")
    output = {"schema": "hydra-local-matched-verification-v1", "spec": spec_pin,
              "private_expectations": expected_pin, "fresh_model_or_native_execution_by_verifier": False,
              "status": "started", "eligible_for_promotion": False, "errors": [],
              "scope": "Small precommitted exposed development comparison; no held-out, generalization, or statistical-significance claim."}
    arms, evidence = {}, {}
    for arm, folder in (("historical_local_mlx", args.old), ("wmi_c6_vanilla47_step8192", args.wmi)):
        try:
            arms[arm], evidence[arm] = validate_arm(folder, arm, spec, args.spec_sha256, rows)
        except (ValueError, KeyError, TypeError, OSError) as error:
            output["errors"].append({"arm": arm, "error_type": type(error).__name__, "error": str(error)})
    output["evidence"] = evidence
    if len(arms) == 2:
        old, wmi = arms["historical_local_mlx"], arms["wmi_c6_vanilla47_step8192"]
        require(all(old[k]["native_identity"] == wmi[k]["native_identity"] for k in gold), "Arms used different native identities")
        paired = []
        for row in rows:
            key, target = row["id"], gold[row["id"]]
            a, b = old[key]["proved"], wmi[key]["proved"]
            paired.append({"id": key, "expected": target["expected"], "cohort": target["cohort"],
                           "historical": {k:v for k,v in old[key].items() if k != "native_identity"},
                           "wmi": {k:v for k,v in wmi[key].items() if k != "native_identity"},
                           "paired": "both_proved" if a and b else "historical_only" if a else "wmi_only" if b else "neither"})
        def table(prefix, positive):
            subset = [r for r in paired if r["id"].startswith(prefix) and (r["expected"] == "provable") is positive]
            return {"total": len(subset), "counts": {label:sum(r["paired"] == label for r in subset)
                    for label in ("both_proved", "historical_only", "wmi_only", "neither")}, "case_ids": [r["id"] for r in subset]}
        primary, regress = table("primary-", True), table("regression-", True)
        false_proofs = [r["id"] for r in paired if r["expected"] == "not_provable" and r["paired"] != "neither"]
        gains, losses = primary["counts"]["wmi_only"], primary["counts"]["historical_only"]
        regression_losses = regress["counts"]["historical_only"]
        output.update(status="verified", paired_cases=paired, primary_positive=primary,
                      regression_positive=regress, primary_false=table("primary-", False),
                      regression_false=table("regression-", False), false_accepted_proofs=false_proofs,
                      positive_net_gain=gains-losses,
                      eligible_for_promotion=gains >= 1 and losses == 0 and regression_losses == 0 and not false_proofs,
                      decision_reasons={"primary_positive_wmi_only": gains, "primary_positive_historical_only": losses,
                                        "regression_positive_historical_only": regression_losses,
                                        "false_accepted_proofs": len(false_proofs)})
    else:
        output["status"] = "incomplete_or_invalid"
    raw = (json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()
    with Path(args.output).open("xb") as stream:
        stream.write(raw)
    print(json.dumps({"status": output["status"], "eligible_for_promotion": output["eligible_for_promotion"],
                      "errors": output["errors"], "path": str(Path(args.output).resolve()), "bytes": len(raw), "sha256": sha(raw)}))
    return 0 if output["status"] == "verified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
