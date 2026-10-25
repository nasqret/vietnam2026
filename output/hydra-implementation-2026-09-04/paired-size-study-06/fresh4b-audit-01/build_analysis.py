"""Extract measured case diagnostics from the single collected source07 arm."""
from collections import Counter
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / "output/hydra-implementation-2026-09-04"
HERE = Path(__file__).resolve().parent
OBS = BASE / "paired-launchers-v13/prepared/arms/fresh_4b/observation-006"


def pin(path):
    raw = path.read_bytes()
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest()}


def read(path):
    return json.loads(path.read_bytes())


audit = read(HERE / "audit.json")
assert pin(HERE / "audit.json")["sha256"] == "8a4bed76c7dda9b0c48bb50f913028483045dc99c58120b10f7a02326c162e74"
assert pin(HERE / "actual-completion.json")["sha256"] == "6a24e982a1de75b47c7a046073656b85c3ce32acc15656c270cba12d620dccb7"
arm, = audit["arms"]
assert arm["arm"] == "fresh_4b" and arm["execution_complete"] and arm["counter_accounting_complete"]
assert len(arm["cases"]) == 16 and not arm["not_run"]
completion = read(OBS / "result/completion.json")
totals, branch_statuses, rejection_reasons = Counter(), Counter(), Counter()
cases, child_episodes = [], []
model_identities, tensors = set(), set()
for index, checked in enumerate(arm["cases"]):
    directory = OBS / "result" / ("case-%02d" % index)
    result, execution = read(directory / "case-result.json"), read(directory / "execution.json")
    search = result["search"]
    call_file = directory / "model-calls.jsonl"
    calls = [json.loads(line) for line in call_file.read_text().splitlines()] if call_file.exists() else []
    assert result["actual_counters"] == checked["counters"]
    assert len(calls) == checked["counters"]["actual_model_calls"]
    assert all(row["error"] is None for row in calls)
    assert execution["exit_code"] == 0 and execution["leader_reaped"] and execution["quiescent"]
    assert execution["termination_reason"] == "process_exit" and execution["cleanup_error"] is None
    if calls:
        assert calls[-1]["actual_generation_calls_after"] == checked["counters"]["actual_model_calls"]
        assert calls[-1]["actual_forward_passes_after"] == checked["counters"]["forward_passes"]
        assert calls[-1]["actual_token_slots_after"] == checked["counters"]["generated_token_slots"]
    model_identities.add(result["model"]["identity"]["model_manifest_sha256"])
    adapter = result["model"]["identity"]["adapter"]
    tensors.add(adapter["final_tensor_population_sha256"])
    assert adapter["saved_adapter_reload_checked"] and adapter["header"]["tensors"] == 504
    model_branches = [row for row in search["branches"] if row["source"] == "model"]
    statuses = Counter(row["status"] for row in model_branches)
    branch_statuses.update(statuses)
    rejection_reasons.update(row["reason"] for row in model_branches if row["status"] == "rejected")
    case_totals = {
        **{key: checked["counters"][key] for key in ("actual_model_calls", "forward_passes", "generated_token_slots", "planner_calls")},
        "provider_returned_candidate_lines": sum(len(row["accepted_candidates"]) for row in calls),
        "search_model_candidates": search["model_candidates"],
        "provider_rejected_sequences": result["model_policy"]["rejected_sequences"],
        "retained_branch_records_all_sources": len(search["branches"]),
        "omitted_branch_records_all_sources": search["branches_omitted"],
        "native_tactic_attempts": search["tactic_attempts"],
        "search_seconds": search["elapsed_seconds"],
        "model_construction_seconds": result["model_construction_seconds"],
        "post_load_provider_seconds": result["post_load_provider_seconds"],
        "native_transition_seconds": search["native_timing"]["transition_seconds"],
    }
    totals.update(case_totals)
    resolution = execution.get("child_terminal_resolution")
    episodes = []
    for episode in (resolution or {}).get("episodes", []):
        assert episode["outcome"] == "natural_exit_confirmed"
        assert episode["missing_rss_was_zero_filled"] is False
        item = {"pid": episode["pid"], "elapsed_seconds": episode["elapsed_seconds"],
                "terminal": episode["terminal"], "outcome": episode["outcome"],
                "pending_kinds": sorted({frame["child"].get("pending_kind") for frame in episode["samples"]}),
                "missing_rss_was_zero_filled": episode["missing_rss_was_zero_filled"]}
        episodes.append(item)
        child_episodes.append({"case_index": index, **item})
    inputs = {name: pin(directory / name) for name in
              ("case-result.json", "execution.json", "model-admission.json")}
    if call_file.exists():
        inputs["model-calls.jsonl"] = pin(call_file)
    cases.append({"index": index, "case_id": checked["case_id"], "category": checked["category"],
        "family": checked["family"], "original_input_theorem": result["original_input_theorem"],
        "canonical_theorem": result["canonical_theorem"], "status": checked["status"],
        "kernel_checked_and_replayed": checked["kernel_checked_and_replayed"],
        "limits_reached": search["limited_by"], "counts_and_times": case_totals,
        "native_work": checked["native_work"], "native_timing": checked["native_timing"],
        "gpu_memory": checked["gpu_memory"], "sampled_host_peak_rss_bytes": checked["sampled_host_peak_rss_bytes"],
        "whole_child_wall_seconds": execution["elapsed_seconds"], "worker_exit_code": 0,
        "leader_reaped": True, "quiescent": True, "model_identity_sha256": result["model"]["identity"]["model_manifest_sha256"],
        "retained_model_branch_statuses": dict(statuses), "retained_model_branches": model_branches,
        "full_model_acceptance_rate_available": search["branches_omitted"] == 0,
        "winning_steps": checked["winning_steps"],
        "winning_commands": search["commands"] if checked["kernel_checked_and_replayed"] else None,
        "winning_provenance": search["provenance"] if checked["kernel_checked_and_replayed"] else None,
        "independent_original_replay": result["independent_original_replay"],
        "proof_cost": checked["proof_cost"], "leader_terminal_resolution": execution["terminal_resolution"],
        "child_terminal_episodes": episodes, "input_files": inputs})

assert len(model_identities) == len(tensors) == 1
assert arm["positive_proofs"] == 1 and arm["control_checked_proofs"] == 0
assert totals["actual_model_calls"] == 165 and totals["forward_passes"] == 913 and totals["generated_token_slots"] == 3652
proof = cases[11]
assert proof["case_id"] == "holdout_additive_bound_transitivity" and proof["winning_steps"] == {"heuristic": 13, "model": 0}
assert proof["counts_and_times"]["actual_model_calls"] == 0
metrics = {"schema": "hydra-source07-fresh4b-case-analysis-v1", "selected_attempt": "p6-paired-fresh-4b-v8-01",
    "job_id": "22082082", "frozen_audit": pin(HERE / "audit.json"), "actual_audit_completion": pin(HERE / "actual-completion.json"),
    "terminal_collection": pin(OBS / "terminal-collection.json"), "actual_terminal_tool_completion": pin(OBS / "actual-tool-completion.json"),
    "arm_completion": pin(OBS / "result/completion.json"), "analysis_script": pin(Path(__file__)),
    "execution_complete": True, "counter_accounting_complete": True, "selected_cases": 16,
    "positive_proofs": 1, "positive_case_count": 12, "positive_unknowns": 11,
    "control_checked_proofs": 0, "control_case_count": 4, "control_unknowns": 4,
    "proved_cases_with_model_winning_steps": 0, "cases": cases, "totals": dict(totals),
    "retained_model_branch_statuses": dict(branch_statuses), "retained_model_rejection_reasons": dict(rejection_reasons),
    "model_acceptance_rate_available": False,
    "branch_count_limitation": "Model statuses count only retained records; 43,282 branch records across all sources were omitted. Provider-returned lines, search candidates and native accepted branches are different counters.",
    "time_scope": "Provider time is included in search time. Native transition timing includes prefix restoration/tactic checking. These overlapping diagnostic clocks must not be added as independent costs.",
    "scheduler": arm["terminal"], "controller_elapsed_seconds": completion["elapsed_seconds"],
    "model_identity_sha256": next(iter(model_identities)), "final_tensor_population_sha256": next(iter(tensors)),
    "all_saved_adapter_reloads_checked": True, "adapter_tensors": 504,
    "all_workers_clean": True, "child_terminal_episodes": child_episodes,
    "sampled_host_peak_rss_bytes": max(case["sampled_host_peak_rss_bytes"] for case in cases),
    "peak_gpu_allocated_bytes": max(case["gpu_memory"]["peak_allocated_bytes"] for case in cases),
    "comparison_status": audit["status"], "unselected_declared_roles": audit["missing_arms"],
    "same_source_complete_two_model_comparison_claimed": False,
    "model_improvement_demonstrated": False, "full_feature_hybrid_score_claimed": False,
    "local_analysis_work": {"model_calls": 0, "native_runs": 0, "network_calls": 0}}
with (HERE / "case-metrics.json").open("x") as stream:
    json.dump(metrics, stream, sort_keys=True, indent=2, ensure_ascii=False)
    stream.write("\n")

rows = []
for case in cases:
    counts = case["counts_and_times"]
    name = case["case_id"].removeprefix("holdout_")
    link = "../../paired-launchers-v13/prepared/arms/fresh_4b/observation-006/result/case-%02d/case-result.json" % case["index"]
    limits = {"max_frontier": "frontier", "max_states": "states", "max_tactic_attempts": "attempts",
              "max_expansions": "expansions", "max_model_calls": "model calls", "wall_seconds": "wall"}
    rows.append("| [%02d %s](%s) | %s | %d / %d / %d | %s | %.3f |" % (
        case["index"], name, link, case["status"], counts["actual_model_calls"], counts["forward_passes"],
        counts["generated_token_slots"], ", ".join(limits[x] for x in case["limits_reached"]) or "—", counts["search_seconds"]))

report = """The saved 4B model completed the full 16-case source07 test: **1 of 12 positive theorems proved (8.3%), 11 positive results unknown, and all four negative controls unknown**. The sole proof used 13 heuristic steps and zero model calls. This run establishes successful model loading and complete measured execution; it provides no proof-success gain attributable to the trained model.

The frozen [audit](audit.json) confirms `execution_complete: true` and `counter_accounting_complete: true` for the selected fresh4B arm. Its four-role comparison remains `incomplete` because fresh1.7B, historical1.7B and symbolic roles were unselected. The single auditor invocation returned **2**, chunk `a9db7a`, with a valid output; [the actual completion](actual-completion.json) records those semantics. No evaluation cases are missing from this selected arm.

All cases below exited cleanly with their leaders reaped and process groups confirmed quiescent. “Unknown” means the bounded search did not produce an accepted proof; the four control results are not refutations. The full source, file pins, theorem texts, per-case work and timings are in [case-metrics.json](case-metrics.json).

| Case | Result | Model calls / forwards / beam slots | Limits reported | Search seconds |
| --- | --- | ---: | --- | ---: |
""" + "\n".join(rows) + """

The complete model-work totals are **165 calls, 913 forward passes and 3,652 generated beam slots**. The call log contains 656 provider-returned tactic lines; search records count 648 model candidates. These counters describe different stages and neither is a native-acceptance count. The provider records four rejected sequences and no call-log errors. Across all sources, search performed 54,884 native tactic attempts.

Cases 00–04 exhausted 6,000 attempts and 2,048 states before the search clock. Cases 05, 09, 10, 12, 13 and 15 reached 384 expansions and 16 model calls. The residue cases 06–08 and 14 reached the 30-second search clock; their returns took at most 31.023 seconds, within the selected two-second return grace. Every unknown case also reports frontier pruning. Larger limits alone would leave the observed tactic-quality problems unresolved.

The retained branch log contains **27 open model steps, 38 duplicate model states and 90 rejected model proposals**. Open steps passed native tactic checking but left proof obligations. There are 43,282 omitted branch records across all sources, so these visible counts cannot support a complete model acceptance rate. Several accepted witnesses merely strengthen the remaining obligation without helping close it.

The native diagnostics show concrete mismatches between generated text and the available tactic language:

- In residue problems, `cases n` treats a natural-number variable as a hypothesis; `cases (n % 4)` is also outside the tactic syntax. The engine reports that `cases` requires a local hypothesis name.
- In additive cancellation, `specialize h n` targets an equality hypothesis, while `compact_arith h` uses invalid argument syntax. The supported form is `compact_arith [h]`.
- `exists (n * n / 4)` uses division outside the current term grammar. Other proposals refer to unavailable variables such as `x2`, or apply `ring` where the goal is not a polynomial identity.

These are observed failures, not an explanation proved to account for the entire score. They make context-aware syntax and tactic precondition checks a concrete implementation target. Future training should measure useful residual proof decisions and tactic coverage on independent validation families; this exposed test suite should remain excluded from training and retrieval.

The one accepted theorem is:

```text
forall a b c.
  (exists u. a + u = b) ->
  (exists v. b + v = c) ->
  exists w. a + w = c
```

Its heuristic route introduces variables and assumptions, unpacks the two witnesses, chooses their sum, and closes the algebra with rewrites and `ring`. The independent original-theorem replay checked all 13 steps with no remaining goals. The final proof has 2,684 distinct proof objects, 3,989 structural occurrences and depth 38. Search took 0.739 seconds and 48 native attempts; the model was loaded for the arm but inference was never called for this theorem. The earlier source03 symbolic run also proved this theorem, which is a descriptive reference rather than a matched source07 ablation.

All 16 worker processes authenticated and reloaded the same saved 504-tensor adapter, with the final tensor population matching the completed 4B training artifact. The raw scheduler evidence records job **22082082 COMPLETED 0:0**, process exit 0, 560 scheduler seconds and 556.776 controller seconds. Its full 1,560-second allocation charge is retained. All executed source maps match before and after. Eight recorded scheduler-child exit intervals naturally resolved in 51.6–52.6 milliseconds; missing RSS was never filled with zero. This actual model run completed without the former monitor interruption.

Model construction totals 193.434 seconds across the 16 independent workers. Search totals 335.486 seconds, of which 265.771 seconds are recorded provider time; these overlap and must not be added as separate costs. Native transition work totals 36.673 seconds. Reload overhead is measurable, but changing worker lifetime would require an explicit new execution design and comparable testing.

This harness isolates primitive model guidance: library, planner, ranker and external advisers are off. Its 1/12 result is not the full-feature hybrid's score. The incomplete source05 1.7B test remains a separate partial reference, so there is no complete matched two-size comparison and no demonstrated advantage from the larger trained adapter here. This audit and analysis ran no model, native proof, scheduler or network operation.
"""
with (HERE / "ANALYSIS.md").open("x") as stream:
    stream.write(report)
print(json.dumps({"metrics": pin(HERE / "case-metrics.json"), "analysis": pin(HERE / "ANALYSIS.md"),
    "totals": dict(totals), "retained_model_branch_statuses": dict(branch_statuses),
    "child_terminal_episodes": len(child_episodes), "local_model_native_network_calls": 0}, sort_keys=True))
