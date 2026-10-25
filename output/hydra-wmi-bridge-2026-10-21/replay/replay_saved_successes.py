#!/usr/bin/env python3
"""CPU-only literal replay of authenticated saved WMI successes in current Hydra.

This does not rerun the WMI evaluator, inference, or checkpoint selection. No
fetched Latent module is imported. The original worker's no-imports authority,
source checks, transport limits and kernel remain unchanged.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = ROOT / "output/hydra-model-upgrade-2026-10-20/local-discovery/native_replay_validator.py"
VALIDATOR_SHA256 = "78f712f1f99cc013091ca7e1ff1a70115b971f9bf42cb4ecea53049badca0242"
WORKER = ROOT / "hydra-playground/worker.py"
WORKER_SHA256 = "e7923426cf39a68719fc79f8efc1db0cf016edf03bd79d248a94ac06235de951"
WMI_AUTHORITY = "72372974368a4a2b66cba42fa48baae47e24bf811a8b2dd030027ea3b7f16363"
TRANSITION_KEYS = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def descriptor(path):
    raw = path.read_bytes()
    return {"path": str(path), "bytes": len(raw), "sha256": sha(raw)}


def write_json(path, value):
    with path.open("xb") as stream:
        stream.write(canonical(value) + b"\n")


def compact_prompt(goals):
    # Copied literal serialization only; it grants no library authority.
    state = json.dumps({"focus": 0, "goals": goals}, ensure_ascii=False,
                       separators=(",", ":"))
    return "HA model-v3 library-prefix=247/247\n" + state + "\nTactic:"


def load_validator():
    require(descriptor(VALIDATOR)["sha256"] == VALIDATOR_SHA256, "validator pin differs")
    require(descriptor(WORKER)["sha256"] == WORKER_SHA256, "worker pin differs")
    sys.dont_write_bytecode = True
    spec = importlib.util.spec_from_file_location("hydra_saved_replay_validator", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_success(record, checkpoint_sha256, validator):
    require(record.get("status") == "proved" and record.get("autonomous_python_kernel_proof") is True,
            "selected record is not a saved autonomous success")
    require(record.get("reference_actions_used") == 0 and record.get("search_branches") == 1
            and record.get("restarts") == 0, "source autonomy accounting differs")
    require(record.get("environment_sha256") == WMI_AUTHORITY, "source authority differs")
    request = {"theorem": record["formula"], "tactics": record["actions"]}
    validator.check_request(request)
    actions, generated, native = record["actions"], record["steps"], record["native_result"]
    require(actions and len(generated) == len(actions) == record["model_calls"]
            == record["accepted_actions"] == record["submitted_actions"], "source action accounting differs")
    require(native.get("status") == "proved" and native.get("kernel_checked") is True
            and native.get("classical") is False and native.get("theorem") == record["formula"]
            and native.get("environment_sha256") == WMI_AUTHORITY and native.get("goals") == []
            and record.get("remaining_goals") == [], "source native completion differs")
    trace = native["trace"]
    require(trace and trace[-1].get("qed") is True
            and trace[-1].get("theorem") == record["formula"]
            and trace[-1].get("tactic_count") == len(actions), "source native QED footer differs")
    transitions = [row for row in trace if "v" in row]
    require(len(transitions) == len(actions) and native["tactics_requested"] == len(actions)
            and native["tactics_applied"] == len(actions) and native["failed_tactics"] == 0,
            "source native transition accounting differs")
    for index, (action, step, transition) in enumerate(zip(actions, generated, transitions), 1):
        require(transition["step"] == index and transition["status"] == "ok"
                and transition.get("error") is None, "source transition failed")
        require(index == 1 or transition["goals_before"] == transitions[index - 2]["goals_after"],
                "source adjacent native states are discontinuous")
        require(step["index"] == index and step["decoded"]["valid_action"] is True
                and step["decoded"]["action"] == action and step["valid_transition"] is True,
                "source generated action is not bound to submitted action")
        prompt = compact_prompt(transition["goals_before"])
        generation = step["generation"]
        require(step["prompt"] == prompt and step["prompt_sha256"] == sha(prompt.encode())
                and generation["prompt_sha256"] == step["prompt_sha256"], "source prompt/state differs")
        require(generation["provenance"]["checkpoint_sha256"] == checkpoint_sha256,
                "source generated checkpoint differs")
    require(transitions[-1]["goals_after"] == [], "source final transition retains goals")
    return request, transitions


def compare_trajectory(expected, actual_result):
    actual = [row for row in actual_result.get("trace", []) if "v" in row]
    comparisons, first = [], None
    for index, before in enumerate(expected):
        after = actual[index] if index < len(actual) else None
        difference = {key: {"expected": before.get(key), "actual": None if after is None else after.get(key)}
                      for key in TRANSITION_KEYS if after is None or before.get(key) != after.get(key)}
        before_prompt = compact_prompt(before["goals_before"])
        after_prompt = compact_prompt(after["goals_before"]) if after and after.get("goals_before") else None
        item = {"step": index + 1, "actual_transition_present": after is not None,
                "equal": not difference, "different_fields": list(difference),
                "expected_transition_sha256": sha(canonical({k: before.get(k) for k in TRANSITION_KEYS})),
                "actual_transition_sha256": None if after is None else sha(canonical({k: after.get(k) for k in TRANSITION_KEYS})),
                "expected_prompt_sha256": sha(before_prompt.encode()),
                "actual_prompt_sha256": None if after_prompt is None else sha(after_prompt.encode())}
        comparisons.append(item)
        if difference and first is None:
            first = {"step": index + 1, "differences": difference}
    return {"expected_transition_count": len(expected), "actual_transition_count": len(actual),
            "exact_trajectory_match": len(expected) == len(actual) and first is None,
            "first_divergence": first, "steps": comparisons}


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--proofs", required=True, type=Path)
    parser.add_argument("--proofs-sha256", required=True)
    parser.add_argument("--checkpoint-sha256", required=True)
    parser.add_argument("--expected-records", type=int, default=64)
    parser.add_argument("--expected-successes", type=int, default=50)
    parser.add_argument("--timeout-seconds", type=float, default=20)
    parser.add_argument("--batch-timeout-seconds", type=float, default=900)
    parser.add_argument("--case-id", action="append", default=[],
                        help="Optional exact success ID; repeat to select an explicit subset.")
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    require(1 <= args.expected_successes <= 50 and args.expected_successes <= args.expected_records <= 64,
            "diagnostic permits at most50 successes among64 records")
    require(0 < args.timeout_seconds <= 30, "per-case timeout must be at most30seconds")
    require(0 < args.batch_timeout_seconds <= 900, "batch timeout must be at most900seconds")
    source = descriptor(args.proofs)
    require(source["bytes"] <= 64 * 1024**2 and source["sha256"] == args.proofs_sha256,
            "source report size/hash differs")
    validator = load_validator()
    records = [validator.strict_json(line) for line in args.proofs.read_bytes().splitlines()]
    require(len(records) == args.expected_records and len({r["id"] for r in records}) == len(records),
            "source record count or unique IDs differ")
    successes = [r for r in records if r.get("autonomous_python_kernel_proof") is True]
    require(len(successes) == args.expected_successes, "source success count differs")
    require(len(set(args.case_id)) == len(args.case_id)
            and set(args.case_id) <= {r["id"] for r in successes}, "selected success IDs differ")
    selected = [r for r in successes if not args.case_id or r["id"] in args.case_id]
    prepared = [(r, *validate_success(r, args.checkpoint_sha256, validator)) for r in selected]
    require(descriptor(args.proofs) == source, "source report changed during admission")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {"schema": "hydra-wmi-saved-success-replay-request-v1", "proofs": source,
                "checkpoint_sha256": args.checkpoint_sha256, "worker": descriptor(WORKER),
                "validator": descriptor(VALIDATOR), "harness": descriptor(Path(__file__).resolve()),
                "source_record_count": len(records), "source_success_count": len(successes),
                "selected_success_count": len(selected), "selection": "all-saved-successes" if not args.case_id else "explicit-IDs",
                "scope": "Current no-imports worker; literal saved actions; no model inference or WMI evaluator rerun.",
                "per_case_timeout_seconds": args.timeout_seconds,
                "batch_timeout_seconds": args.batch_timeout_seconds, "automatic_retry": False,
                "cases": [{"source_id": r["id"], "source_record_sha256": sha(canonical(r)),
                           "request_sha256": sha(canonical(request)), "action_count": len(request["tactics"])}
                          for r, request, _ in prepared]}
    write_json(args.output / "REQUESTS.json", manifest)
    started, outcomes = time.monotonic(), []
    for index, (record, request, expected) in enumerate(prepared, 1):
        remaining_seconds = args.batch_timeout_seconds - (time.monotonic() - started)
        if remaining_seconds <= 0:
            break
        case_dir = args.output / f"case-{index:02d}-{sha(record['id'].encode())[:12]}"
        case_dir.mkdir()
        write_json(case_dir / "request.json", request)
        report, stdout, stderr = validator.replay(request, worker=WORKER,
                                                  timeout_seconds=min(args.timeout_seconds, remaining_seconds))
        with (case_dir / "worker.stdout.jsonl").open("xb") as stream:
            stream.write(stdout)
        with (case_dir / "worker.stderr.txt").open("xb") as stream:
            stream.write(stderr)
        actual_result = report.get("native_result") or {}
        comparison_origin = "validated-native-result" if actual_result else "no-native-result"
        if not actual_result:
            # A canonicalization/authority mismatch can invalidate a completion
            # while its genuine raw worker event still explains the divergence.
            # This fallback is diagnostic only and cannot change proof_accepted.
            try:
                events = [validator.strict_json(line) for line in stdout.splitlines()]
                if len(events) == 1 and events[0].get("type") == "result" and type(events[0].get("result")) is dict:
                    actual_result = events[0]["result"]
                    comparison_origin = "raw-native-result-not-accepted-by-validator"
            except (ValueError, TypeError, UnicodeError, AttributeError):
                pass
        comparison = compare_trajectory(expected, actual_result)
        result = {"schema": "hydra-wmi-saved-success-replay-case-v1", "index": index,
                  "source_id": record["id"], "source_record_sha256": sha(canonical(record)),
                  "source_checkpoint_sha256": args.checkpoint_sha256,
                  "source_actions": record["actions"],
                  "source_use_actions": [x for x in record["actions"] if x.split(maxsplit=1)[0] == "use"],
                  "native_replay": report, "trajectory_comparison": comparison,
                  "comparison_result_origin": comparison_origin,
                  "stdout": descriptor(case_dir / "worker.stdout.jsonl"),
                  "stderr": descriptor(case_dir / "worker.stderr.txt")}
        write_json(case_dir / "RESULT.json", result)
        outcomes.append({"source_id": record["id"], "result": descriptor(case_dir / "RESULT.json"),
                         "proof_accepted": report["proof_accepted"], "replay_status": report["status"],
                         "native_status": actual_result.get("status"),
                         "native_error": actual_result.get("error"),
                         "failed_step": actual_result.get("failed_step"),
                         "source_use_action_count": len(result["source_use_actions"]),
                         "exact_trajectory_match": comparison["exact_trajectory_match"],
                         "first_divergence_step": (comparison["first_divergence"] or {}).get("step")})
        print(json.dumps({"completed": index, "total": len(prepared), **outcomes[-1]}, ensure_ascii=False), flush=True)
    require(descriptor(args.proofs) == source and descriptor(VALIDATOR)["sha256"] == VALIDATOR_SHA256
            and descriptor(WORKER)["sha256"] == WORKER_SHA256, "pinned input changed during diagnostic")
    summary = {"schema": "hydra-wmi-saved-success-replay-summary-v1",
               "status": "diagnostic_completed" if len(outcomes) == len(prepared) else "batch_budget_limit",
               "requests": descriptor(args.output / "REQUESTS.json"), "cases_attempted": len(outcomes),
               "selected_success_count": len(prepared),
               "unattempted_source_ids": [r["id"] for r, _, _ in prepared[len(outcomes):]],
               "proofs_accepted": sum(x["proof_accepted"] for x in outcomes),
               "exact_trajectory_matches": sum(x["exact_trajectory_match"] for x in outcomes),
               "replay_status_counts": dict(Counter(x["replay_status"] for x in outcomes)),
               "seconds": time.monotonic() - started, "results": outcomes,
               "new_model_inference": False, "live_default_changed": False,
               "limitations": ["Saved development successes only, not an unseen or complete quality evaluation.",
                   "Different no-imports execution authority; failure may be an authority/interface mismatch.",
                   "Expected WMI receipt is historical evidence; only actual Hydra worker acceptance is credited here.",
                   "No standalone Lean verification and no original SLURM evaluator re-execution."]}
    write_json(args.output / "SUMMARY.json", summary)
    print(json.dumps({"summary": descriptor(args.output / "SUMMARY.json"),
                      "proofs_accepted": summary["proofs_accepted"], "cases_attempted": len(outcomes)}), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
