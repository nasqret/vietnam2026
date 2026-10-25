#!/usr/bin/env python3
"""Analyze saved, complete October comparison results. Never run inference.

Use only after the real three-arm terminal collection is available. A failed
validation produces an error report and exit2, never a partial quality score.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ARMS = ("historical_retention", "wmi_c6_vanilla47", "helios_c5_vanilla29")
PANEL_SHA = "94bc2553af3b6d36a7f51b6c0d5e7f58e43e9e39c2fa69b87062fb199feac1e6"
INPUTS_SHA = "f20441c9a03b9f337a7e9c0ea5d7648646e1f095c4244bc33ca41be84af901aa"
BASELINE_ADAPTER_SHA = "7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5"
SEARCH_AUTHORITY_SHA = "ac5efc6260bd7aa706ee02f943c30c8fa4acc413a1be246722b2163a21688a87"
REPLAY_AUTHORITY_SHA = "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f"
KERNEL_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def load(path, expected_sha=None):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), f"Missing or linked result: {path}")
    require(path.stat().st_size <= 16 * 1024 * 1024, f"Oversized JSON: {path}")
    raw = path.read_bytes()
    pin = {"path": str(path), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    require(expected_sha is None or pin["sha256"] == expected_sha, f"Hash mismatch: {path}")

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, f"Duplicate JSON key in {path}: {key}")
            result[key] = value
        return result

    def bad_number(value):
        raise ValueError(f"Non-finite JSON value in {path}: {value}")

    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad_number), pin


def natural(value, name):
    require(type(value) is int and value >= 0, f"Invalid nonnegative integer: {name}")
    return value


def seconds(value, name):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0,
            f"Invalid duration: {name}")
    return value


def winning_proof(record, case, calls):
    """Read exact winning provenance and native certificate size, not branch logs."""
    search, replay = record["search"], record["independent_replay"]
    theorem, commands = case["theorem"], search["commands"]
    require(search["status"] == "proof" and search["kernel_checked"] is True
            and search["theorem"] == theorem and search["classical"] is False,
            f"Unverified search proof: {case['id']}")
    require(type(commands) is list and commands and all(type(line) is str for line in commands)
            and not any(line.split(maxsplit=1)[0] == "use" for line in commands),
            "Winning commands are missing or import a theorem")
    require(replay["status"] == "proved" and replay["kernel_checked"] is True
            and replay["theorem"] == replay["original_theorem"] == theorem
            and replay["commands"] == commands and replay["goals"] == []
            and replay["classical"] is False and replay["model_used"] is False
            and replay["kernel_source_commit"] == KERNEL_COMMIT and "experimental" not in replay
            and replay["environment_sha256"] == REPLAY_AUTHORITY_SHA,
            "Independent native replay does not bind the original theorem and authority")
    trace = replay["trace"]
    steps = [step for step in trace if "v" in step]
    require(trace[-1].get("qed") is True and trace[-1].get("theorem") == theorem
            and trace[-1].get("tactic_count") == len(commands)
            and replay["tactics_requested"] == replay["tactics_applied"] == len(steps) == len(commands)
            and replay["failed_tactics"] == 0 and replay["failed_step"] is None
            and replay["error"] is None
            and all(step.get("status") == "ok" and step.get("error") is None for step in steps),
            "Incomplete or erroneous winning replay trace")
    nodes = natural(search["certificate_nodes"], "certificate_nodes")
    require(nodes > 0 and nodes == replay["proof_nodes"] == search["replay"]["proof_nodes"],
            "Native certificate size differs between search and both replays")
    provenance = search["provenance"]
    require(type(provenance) is list and len(provenance) == len(commands),
            "Winning provenance does not cover every command")
    sources = Counter()
    model_steps = []
    for index, (row, command) in enumerate(zip(provenance, commands), 1):
        require(row["step"] == index and row["command"] == command
                and row["source"] in {"heuristic", "model"}, "Malformed winning-step provenance")
        sources[row["source"]] += 1
        if row["source"] == "model":
            model_call = int(row["evidence"]["model_call"])
            require(1 <= model_call <= calls, "Winning model step lacks an actual decode call")
            model_steps.append({"step": index, "command": command, "model_call": model_call})
    return {"winning_steps": len(commands), "winning_steps_by_source": dict(sources),
            "model_sourced_winning_steps": len(model_steps), "model_winning_steps": model_steps,
            "certificate_nodes": nodes,
            "certificate_nodes_source": "search.certificate_nodes, equal to independent_replay.proof_nodes and search.replay.proof_nodes"}


def analyze_arm(name, directory, study, study_sha, cases):
    receipt, receipt_pin = load(directory / "receipt.json")
    ids = [case["id"] for case in cases]
    require(receipt["schema"] == "hydra-upgrade-arm-v1" and receipt["arm"] == name
            and receipt["study_sha256"] == study_sha and receipt["status"] == "completed"
            and receipt["training"] is False and receipt["automatic_retry"] is False
            and receipt["cases_completed"] == 32 and len(receipt["cases"]) == 32
            and [row["case_id"] for row in receipt["cases"]] == ids,
            f"Arm is not a complete, ordered 32-case evaluation: {name}")
    require(receipt["dependencies"] == study["dependencies"] and str(receipt["job_id"]).isdigit(),
            "Missing or mismatched runtime/job identity")
    checkpoint = BASELINE_ADAPTER_SHA if name == ARMS[0] else study["arms"][name]["checkpoint_sha256"]
    require(receipt["checkpoint_sha256"] == checkpoint, "Arm checkpoint differs from selection")
    rows = []
    for case, declared in zip(cases, receipt["cases"]):
        record, pin = load(directory / (case["id"] + ".json"))
        require(record["case_id"] == case["id"] and record["theorem"] == case["theorem"]
                and {key: record[key] for key in declared} == declared,
                f"Case or summary differs: {name}/{case['id']}")
        require(record["status"] in {"proof", "limit", "exhausted", "timeout"}
                and type(record["proved"]) is bool and record["proved"] is (record["status"] == "proof"),
                f"Infrastructure failure or inconsistent proof flag: {name}/{case['id']}")
        provider = record["provider"]
        identity = provider["identity"]
        require(identity["provenance"]["checkpoint_sha256"] == checkpoint
                and identity["provenance"]["run_id"] == name
                and identity["execution_environment_sha256"] == SEARCH_AUTHORITY_SHA
                and identity["limits"] == study["provider_limits"], "Provider identity or limits changed")
        calls = natural(provider["actual_model_calls"], "actual_model_calls")
        forwards = natural(provider["forward_passes"], "forward_passes")
        attempts = natural(provider["forward_attempts"], "forward_attempts")
        tokens = natural(provider["generated_token_slots"], "generated_token_slots")
        require(calls <= study["provider_limits"]["max_calls"] and calls <= attempts
                and tokens <= forwards <= attempts
                and tokens <= study["provider_limits"]["max_total_decision_tokens"], "Invalid numerical work counters")
        require(not any(row["status"] == "failed" and row.get("error_type") != "TimeoutError"
                        for row in provider["attempts"]), "Provider infrastructure failure in completed arm")
        search = record.get("search")
        if search is not None:
            require(search["theorem"] == case["theorem"] and search["limits"] == study["search_limits"]
                    and search["model_calls"] == calls
                    and not any(row.get("kind") == "model_error" for row in search.get("diagnostics", [])),
                    "Search/provider accounting, limits or infrastructure diagnostics differ")
        require(record["status"] == "timeout" or search is not None, "Non-timeout lacks search result")
        proof = winning_proof(record, case, calls) if record["proved"] else {
            "winning_steps": 0, "winning_steps_by_source": {}, "model_sourced_winning_steps": 0,
            "model_winning_steps": [], "certificate_nodes": None, "certificate_nodes_source": None}
        rows.append({"case_id": case["id"], "stratum": case["stratum"], "family": case["family"],
                     "expected": case["expected"], "status": record["status"], "proved": record["proved"],
                     "outcome_classification": "proved" if record["proved"] else
                         "budget_limited_unknown" if record["status"] == "timeout" else "search_unknown",
                     "actual_model_calls": calls, "forward_passes": forwards, "forward_attempts": attempts,
                     "generated_token_slots": tokens, "provider_seconds": seconds(provider["provider_seconds"], "provider_seconds"),
                     "wall_seconds": seconds(record["wall_seconds"], "wall_seconds"),
                     "winning_proof_used_model": bool(proof["model_sourced_winning_steps"]),
                     "proved_with_zero_model_calls": record["proved"] and calls == 0,
                     "search_claimed_proof_uncredited": not record["proved"] and bool(search and search["status"] == "proof"),
                     "result_file": pin, **proof})
    positives = [row for row in rows if row["expected"] == "provable"]
    controls = [row for row in rows if row["expected"] == "not_provable"]
    return {"arm": name, "receipt": receipt_pin, "job_id": receipt["job_id"], "checkpoint_sha256": checkpoint,
            "complete": True, "positive_total": 24, "positive_proved": sum(row["proved"] for row in positives),
            "control_total": 8, "controls_proved": [row["case_id"] for row in controls if row["proved"]],
            "positive_proof_ids": [row["case_id"] for row in positives if row["proved"]],
            "proofs_with_model_winning_steps": sum(row["winning_proof_used_model"] for row in positives),
            "proofs_with_zero_model_calls": sum(row["proved_with_zero_model_calls"] for row in positives),
            "model_sourced_winning_steps": sum(row["model_sourced_winning_steps"] for row in rows),
            "certificate_nodes_total_for_accepted_proofs": sum(row["certificate_nodes"] or 0 for row in rows),
            "actual_model_calls": sum(row["actual_model_calls"] for row in rows),
            "forward_passes": sum(row["forward_passes"] for row in rows),
            "generated_token_slots": sum(row["generated_token_slots"] for row in rows),
            "case_wall_seconds_sum": sum(row["wall_seconds"] for row in rows),
            "model_load_seconds": seconds(receipt["model_load_seconds"], "model_load_seconds"),
            "arm_wall_seconds": seconds(receipt["wall_seconds"], "arm_wall_seconds"),
            "budget_timeout_count": sum(row["status"] == "timeout" for row in rows),
            "status_counts": dict(Counter(row["status"] for row in rows)),
            "by_stratum": {key: {"positive_total": sum(row["stratum"] == key for row in positives),
                "positive_proved": sum(row["stratum"] == key and row["proved"] for row in positives),
                "controls_proved": sum(row["stratum"] == key and row["proved"] for row in controls)}
                for key in sorted({row["stratum"] for row in rows})}, "cases": rows}


def analyze(args):
    study, study_pin = load(args.study, args.study_sha256)
    panel, panel_pin = load(args.panel, PANEL_SHA)
    inputs, inputs_pin = load(Path(args.study).parent / "inputs.json", INPUTS_SHA)
    require(study["schema"] == "hydra-model-upgrade-comparison-v1" and set(study["arms"]) == set(ARMS)
            and study["payload_files"]["inputs.json"] == INPUTS_SHA, "Unexpected study or arm roster")
    cases = panel["cases"]
    require(len(cases) == 32 and len({case["id"] for case in cases}) == 32
            and Counter(case["expected"] for case in cases) == {"provable": 24, "not_provable": 8}
            and inputs["cases"] == [{"id": case["id"], "theorem": case["theorem"]} for case in cases],
            "Fixed panel, truth-label counts or search inputs differ")
    arms = {name: analyze_arm(name, Path(args.results) / name, study, args.study_sha256, cases) for name in ARMS}
    require(len({str(arm["job_id"]) for arm in arms.values()}) == 1, "Arms came from different jobs")
    terminal, terminal_pin = load(args.terminal_completion, args.terminal_completion_sha256)
    require(terminal["schema"] == "hydra-model-upgrade-terminal-completion-v1"
            and terminal["study_sha256"] == args.study_sha256
            and str(terminal["job_id"]) == str(arms[ARMS[0]]["job_id"])
            and terminal["scheduler_state"] == "COMPLETED"
            and terminal["scheduler_exit_code"] == "0:0"
            and type(terminal["collection_actual_exit_code"]) is int
            and terminal["collection_actual_exit_code"] == 0
            and type(terminal["collection_completion_chunk"]) is str
            and bool(terminal["collection_completion_chunk"]),
            "A genuine clean terminal job and successful collection receipt are required")
    inventory = {}
    for name, arm in arms.items():
        inventory[name + "/receipt.json"] = {key: arm["receipt"][key] for key in ("bytes", "sha256")}
        for row in arm["cases"]:
            inventory[name + "/" + row["case_id"] + ".json"] = {
                key: row["result_file"][key] for key in ("bytes", "sha256")}
    inventory_sha = hashlib.sha256(json.dumps(inventory, ensure_ascii=False, sort_keys=True,
        separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    require(len(inventory) == 99 and terminal["results_json_inventory_sha256"] == inventory_sha,
            "Terminal collection receipt does not bind these99 actual result JSON files")
    controls_clean = all(not arm["controls_proved"] for arm in arms.values())
    baseline = set(arms[ARMS[0]]["positive_proof_ids"])
    pairs = {}
    for name in ARMS[1:]:
        candidate = set(arms[name]["positive_proof_ids"])
        wins, losses = sorted(candidate - baseline), sorted(baseline - candidate)
        pairs[name] = {"baseline_arm": ARMS[0], "candidate_arm": name,
                       "wins": wins, "losses": losses, "win_count": len(wins), "loss_count": len(losses),
                       "common_proofs": sorted(candidate & baseline),
                       "promotion_eligible": controls_clean and baseline < candidate,
                       "eligibility_scope": "Remote development screen only; actual local runtime validation is still required."}
    return {"schema": "hydra-model-upgrade-comparison-analysis-v1",
            "status": "valid" if controls_clean else "invalid_false_control_proof", "study": study_pin,
            "panel": panel_pin, "inputs": inputs_pin, "all_three_arms_complete": True,
            "clean_terminal_job_and_collection": True, "terminal_completion": terminal_pin,
            "results_json_inventory_sha256": inventory_sha,
            "zero_controls_proved": controls_clean, "arms": arms, "paired_comparisons": pairs,
            "promotion_rule": "Clean terminal scheduler exit and successful collection bound to all99 result JSONs; all three arms complete; no infrastructure failure; zero controls proved; candidate positive proof set is a strict superset of baseline. Remote eligibility does not authorize automatic deployment.",
            "caveats": ["Exposed engineering development panel; not an unseen benchmark or training-excluded sample.",
                "Torch BF16 greedy width-one screen differs from deployed MLX4bit beam-four inference.",
                "Historical decoding constructs an authority token mask that latent decoding does not. Wall budgets include this and other runtime overhead; the comparison does not isolate model weights from decoder cost.",
                "Latent full247 prompt is conditioning only; all actual execution uses the original no-imports authority.",
                "Model calls do not prove model contribution. Only model-sourced steps on the exact winning proof count.",
                "Certificate size comes from the native winning certificate, never sampled branch logs.",
                "Timeouts, including pre-forward setup timeouts with no search result, are budget-limited unknowns, not native proof failures or refutations. Controls have evaluator expectations, not new refutation receipts.",
                "This script inspects saved results; it runs no inference, native replay or scheduler query."]}


def partial_analysis(args, failure):
    """Retain useful collected evidence without treating it as a full comparison."""
    report = {"schema": "hydra-model-upgrade-comparison-analysis-v1", "status": "incomplete_analysis",
              "all_three_arms_complete": False, "clean_terminal_job_and_collection": False,
              "promotion_eligible": False, "quality_scores_reported": False,
              "error_type": type(failure).__name__, "error": str(failure),
              "scope": "Partial saved evidence only. No complete-arm rate, superiority or deployment claim.",
              "arms": {}}
    try:
        panel, report["panel"] = load(args.panel, PANEL_SHA)
        study, report["study"] = load(args.study, args.study_sha256)
    except (ValueError, OSError) as exc:
        report["partial_read_error"] = str(exc)
        return report
    try:
        terminal, terminal_pin = load(args.terminal_completion, args.terminal_completion_sha256)
        report["terminal_evidence_not_full_comparison_validated"] = {"file": terminal_pin, "record": terminal}
    except (ValueError, OSError) as exc:
        report["terminal_receipt_error"] = str(exc)
    for name in ARMS:
        directory = Path(args.results) / name
        arm = {"promotion_eligible": False, "expected_cases": 32, "collected_cases": [],
               "missing_case_ids": [], "errors": [], "quality_score": None}
        try:
            receipt, arm["receipt"] = load(directory / "receipt.json")
            arm["reported_receipt_status"] = receipt.get("status")
            arm["reported_cases_completed"] = receipt.get("cases_completed")
            arm["reported_job_id"] = receipt.get("job_id")
            require(receipt.get("arm") == name and receipt.get("study_sha256") == args.study_sha256,
                    "Partial arm receipt identity differs")
        except (ValueError, OSError) as exc:
            arm["errors"].append(str(exc))
        for case in panel["cases"]:
            path = directory / (case["id"] + ".json")
            if not path.exists():
                arm["missing_case_ids"].append(case["id"])
                continue
            try:
                record, pin = load(path)
                require(record.get("case_id") == case["id"] and record.get("theorem") == case["theorem"],
                        "Partial case differs from fixed theorem")
                provider = record.get("provider", {})
                calls = natural(provider.get("actual_model_calls"), "partial actual_model_calls")
                row = {"case_id": case["id"], "expected": case["expected"],
                       "status": record.get("status"), "reported_proved": record.get("proved"),
                       "actual_model_calls_from_record": calls, "result_file": pin,
                       "saved_proof_evidence_consistent": False}
                if record.get("proved") is True:
                    checkpoint = BASELINE_ADAPTER_SHA if name == ARMS[0] else study["arms"][name]["checkpoint_sha256"]
                    require(provider["identity"]["provenance"]["checkpoint_sha256"] == checkpoint,
                            "Partial proof provider checkpoint differs")
                    row["winning_proof"] = winning_proof(record, case, calls)
                    row["saved_proof_evidence_consistent"] = True
                arm["collected_cases"].append(row)
            except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
                arm["errors"].append(f"{case['id']}: {type(exc).__name__}: {exc}")
        arm["collected_case_count"] = len(arm["collected_cases"])
        arm["observed_status_counts"] = dict(Counter(row["status"] for row in arm["collected_cases"]))
        arm["actual_model_calls_from_collected_records"] = sum(
            row["actual_model_calls_from_record"] for row in arm["collected_cases"])
        arm["recorded_proof_ids_with_consistent_native_evidence"] = [
            row["case_id"] for row in arm["collected_cases"] if row["saved_proof_evidence_consistent"]]
        arm["reported_control_proof_ids"] = [row["case_id"] for row in arm["collected_cases"]
            if row["expected"] == "not_provable" and row["reported_proved"] is True]
        report["arms"][name] = arm
    return report


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument("--study", required=True, type=Path)
    parser.add_argument("--study-sha256", required=True)
    parser.add_argument("--results", required=True, type=Path)
    parser.add_argument("--terminal-completion", required=True, type=Path)
    parser.add_argument("--terminal-completion-sha256", required=True)
    parser.add_argument("--panel", type=Path, default=Path(__file__).with_name("COMPARISON_PANEL_32.json"))
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = analyze(args)
    except (ValueError, KeyError, TypeError, OSError, IndexError) as exc:
        report = partial_analysis(args, exc)
    raw = Path(__file__).read_bytes()
    report["analyzer"] = {"path": str(Path(__file__)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": report["status"], "output": str(args.output)}, ensure_ascii=False))
    return 0 if report["status"] == "valid" else 2


if __name__ == "__main__":
    raise SystemExit(main())
