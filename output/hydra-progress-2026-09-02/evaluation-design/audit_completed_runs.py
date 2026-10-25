#!/usr/bin/env python3
"""Audit the fixed v4/v5 comparison and v6 extension without executing Hydra.

Run only after root has observed and saved the seven runner completions:
  python3 -I -B audit_completed_runs.py --output /path/to/FRESH_DIRECTORY

Writes audit.json and AUDIT.md. No subprocesses, network, model, solver,
native replay, current weight hashing, or gallery changes. A saved proof is
checked for internal evidence consistency here, not independently reproved.
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
import re
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent.parent
OLD = ROOT / "output/hydra-advanced-2026-09-02"
SHARED = ("fermat_7", "sophie_germain_nonnegative_coordinates",
          "brahmagupta_balanced_identity", "pythagorean_positive_coordinates", "parity_dichotomy")
# name, version, curriculum, IDs, mode, profile, model request cap, beam, total wall
SPECS = (
    ("baseline-v4-01", "v4", "original", SHARED, "hybrid", "deep", 32, 4, 1800),
    ("comparison-v5-01", "v5", "original", SHARED, "hybrid", "deep", 32, 4, 1800),
    ("regression-v6-01", "v6", "original", ("cubic_mod_6",), "hybrid", "deep", 32, 4, 360),
    ("multivariate-v6-01", "v6", "additional", ("multivariate_consecutive_product_even",), "hybrid", "deep", 32, 4, 360),
    ("negative-v6-01", "v6", "additional", ("negative_fermat_7_mod_8", "negative_sophie_germain_coefficient"), "hybrid", "standard", 16, 4, 400),
    ("adviser-v6-01", "v6", "additional", ("successor_zero_explosion",), "symbolic", "standard", 8, 1, 210),
    ("followup-v6-01", "v6", "original", ("fermat_7",), "hybrid", "deep", 32, 4, 360),
)
TOTAL_CASES = sum(len(spec[3]) for spec in SPECS)
CURRICULA = {
    "original": (OLD / "candidate-research/curriculum.json", "b9584794bb72736a6f47ba065b48738c15b970886e58b41b66bba54bd1d031d0"),
    "additional": (HERE / "additional-curriculum.json", "a34f2e3bc0bb8335a5d5fa5468e643d0f5db26b5c0213a3379ac0466b21aa5cd"),
}
ARCHIVES = {
    "v4": (OLD / "source-v4-final", "b5545968ee358f39787a72916d84249e9c79fe4e93df64ce48e404a09e39d37a"),
    "v5": (BASE / "source-v5", "bb7b21d9ae8fd780aaa438c31d3ca5ef76f816ab708e69146547d4f21090c5e1"),
    "v6": (BASE / "source-v6", "73be0e8fc4aa8e37110c6faef8a2d18673e23b5854e2dc4da27e5a87f373b445"),
}
V6_GATE = ("refinement-gate-v6-01", 0, "8b1e8a", 48, 0)
V6_GATE_RESULT_SHA = "267ffc714bf57ffe035181ca4ead3774fdc6011fd1978812cf9baf2abb200333"
V6_REFINEMENT_SHA = "f873434813b9121a487c9325375e7fd088fdfab6fb1b942bf69531dacdf05b2e"
APP_NAMES = set(("server.py worker.py model_runtime.py hybrid_runtime.py hybrid_search.py "
    "arithmetic_search.py finite_difference.py vampire_bridge.py vampire_process.py vampire_worker.py "
    "vampire_limits.py search_settings.py evaluate_hybrid.py evaluate_advanced.py app.js index.html styles.css").split())
NEW_NAMES = {"advice_memory.py", "atom_polynomial.py", "polynomial_chunks.py"}
V6_NAMES = {"decomposition_memory.py"}
RUNTIME_NAMES = APP_NAMES - {"server.py", "evaluate_hybrid.py", "evaluate_advanced.py", "app.js", "index.html", "styles.css"}
COUNTERS = ("model_calls", "model_decode_attempts", "model_advisor_calls", "vampire_calls",
    "vampire_advisor_calls", "tactic_attempts", "candidates_executed", "states_expanded",
    "states_discovered", "forward_passes", "generated_token_steps", "depth_reached")
TIMES = ("client_elapsed_seconds", "server_elapsed_seconds", "worker_elapsed_seconds", "search_elapsed_seconds")
KERNEL_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
VAMPIRE_SHA = "b5168c690e0293cdac78f16d8418d7eeabcd6708f90a60cd2bf45313b6d98699"
UNCHANGED_PIN_KEYS = ("kernel_commit", "kernel_entrypoints", "kernel_catalog", "model_metadata",
                      "vampire_package", "prepared_runtime_packages", "client_python")
MAX_FILE_BYTES = 16 * 1024**2
MAX_TOTAL_BYTES = 256 * 1024**2
INPUTS: dict[str, dict] = {}
READ_BYTES = 0


class AuditError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise AuditError(message)


def check(condition, message, errors):
    if not condition:
        errors.append(message)


def number(value):
    return type(value) in (int, float) and math.isfinite(value)


def count(value):
    return type(value) is int and value >= 0


def relative(path):
    return str(path.relative_to(ROOT))


def safe_child(directory, name):
    require(type(name) is str and name and not Path(name).is_absolute()
            and ".." not in Path(name).parts, "Unsafe artifact member path")
    path = directory / name
    require(not any(parent.is_symlink() for parent in (path, *path.parents)), "Symlinked artifact path")
    return path


def read_bytes(path):
    global READ_BYTES
    require(path.is_file() and not path.is_symlink(), "Missing regular file: " + relative(path))
    require(0 < path.stat().st_size <= MAX_FILE_BYTES, "Artifact exceeds file bound: " + relative(path))
    raw = path.read_bytes()
    require(0 < len(raw) <= MAX_FILE_BYTES, "Artifact changed size beyond bound")
    READ_BYTES += len(raw)
    require(READ_BYTES <= MAX_TOTAL_BYTES and len(INPUTS) < 350, "Audit input budget exceeded")
    pin = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
    key = relative(path)
    require(key not in INPUTS or INPUTS[key] == pin, "Input changed during audit: " + key)
    INPUTS[key] = pin
    return raw


def load(path):
    value = json.loads(read_bytes(path), parse_constant=lambda text: (_ for _ in ()).throw(AuditError("Nonfinite JSON: " + text)))
    require(type(value) is dict, "Expected JSON object: " + relative(path))
    return value


def pin(path):
    key = relative(path)
    if key not in INPUTS:
        read_bytes(path)
    return dict(INPUTS[key])


def binding(path, claimed):
    require(type(claimed) is dict and all(claimed.get(k) == v for k, v in pin(path).items()),
            "Hash/byte binding mismatch: " + relative(path))


def normalized_receipt(path):
    receipt = load(path)
    def alias(keys, valid):
        values = [receipt[key] for key in keys if key in receipt]
        require(values and all(valid(value) for value in values) and all(value == values[0] for value in values),
                "Missing, malformed, or conflicting receipt aliases: " + "/".join(keys))
        return values[0]
    actual_exit = alias(("actual_exit_code", "exit_code"), lambda v: type(v) is int)
    completion = alias(("completion_chunk", "completion_chunk_id"), lambda v: type(v) is str and bool(v))
    launch = alias(("launch_chunk", "launch_chunk_id"), lambda v: type(v) is str and bool(v))
    require(type(receipt.get("session_id")) is int and receipt["session_id"] > 0, "Receipt lacks an observed process session")
    return receipt, {"path": relative(path), "actual_exit_code": actual_exit,
                     "completion_chunk": completion, "launch_chunk": launch, "session_id": receipt["session_id"]}


def configured_limits(profile, mode, calls, beam):
    if profile == "deep":
        search = dict(max_depth=96, max_states=2048, max_tactic_attempts=12000, max_expansions=768,
                      candidates_per_state=48, max_macro_steps=8, closure_steps=16, heuristic_burst=8,
                      max_vampire_calls=12, wall_seconds=300.0)
        worker = dict(wall_seconds=330, cpu_seconds=600, rss_bytes=8589934592, stdout_bytes=8388608)
        frontier, reserve = 128, 12.0
    else:
        search = dict(max_depth=32, max_states=256, max_tactic_attempts=1024, max_expansions=128,
                      candidates_per_state=24, max_macro_steps=4, closure_steps=8, heuristic_burst=4,
                      max_vampire_calls=4, wall_seconds=150.0)
        worker = dict(wall_seconds=180, cpu_seconds=300, rss_bytes=8589934592, stdout_bytes=2097152)
        frontier, reserve = (64 if beam == 4 else 16), 8.0
    native = {**search, "max_frontier": frontier, "max_model_calls": calls if mode == "hybrid" else 0}
    return search, native, worker, reserve


def added_names(version):
    return (NEW_NAMES if version in {"v5", "v6"} else set()) | (V6_NAMES if version == "v6" else set())


def audit_archive(version):
    directory, expected = ARCHIVES[version]
    require(type(expected) is str and len(expected) == 64, "Final archive digest not supplied: " + version)
    manifest = load(directory / "manifest.json")
    require(pin(directory / "manifest.json")["sha256"] == expected, "Frozen " + version + " manifest changed")
    files = manifest.get("files")
    require(type(files) is dict and 1 <= len(files) <= 120, "Invalid source archive size")
    for name, descriptor in files.items():
        binding(safe_child(directory, name), descriptor)
    require(manifest.get("search_profile") == "hydra-playground-hybrid-" + version, "Wrong archive search version")
    return manifest


def normalized_metrics(job):
    result = job.get("result") if type(job.get("result")) is dict else {}
    search = result.get("search") if type(result.get("search")) is dict else {}
    progress = job.get("progress") if type(job.get("progress")) is dict else {}
    values, sources = {}, {}
    for key in COUNTERS:
        values[key], sources[key] = None, None
        for label, scope in (("result.search", search), ("result", result), ("last_progress", progress)):
            if count(scope.get(key)):
                values[key], sources[key] = scope[key], label
                break
    return {"values": values, "sources": sources,
            "last_progress_is_partial": "last_progress" in sources.values(), "missing_counters_are_not_zero": True}


def model_audit(search, errors):
    proposals, omitted = search.get("proposals"), search.get("proposals_omitted")
    actual, attempts, requests = (search.get(k) for k in ("model_calls", "model_decode_attempts", "model_advisor_calls"))
    groups, actual_rows = Counter(), {}
    valid = type(proposals) is list
    if valid:
        require(len(proposals) <= 128, "Too many retained model proposals")
        previous = 0
        for proposal in proposals:
            goals, ordinal = proposal.get("goals"), proposal.get("call")
            require(type(goals) is list and goals and all(type(g) is str for g in goals), "Malformed full model goals")
            require(type(ordinal) is int and ordinal > previous and count(attempts) and ordinal <= attempts,
                    "Provider proposal ordinals do not index decode attempts")
            previous = ordinal
            groups[tuple(goals)] += 1
    if all(count(v) for v in (actual, attempts, requests)):
        check(actual <= attempts <= requests, "Model batch/decode/adviser counts do not reconcile", errors)
    if count(search.get("forward_passes")) and count(actual):
        check(search["forward_passes"] >= actual, "Actual batches exceed completed forward passes", errors)
    complete = valid and omitted == 0 and count(actual) and len(proposals) == actual
    if valid and count(omitted) and count(actual):
        check(len(proposals) + omitted <= actual, "More completed proposal records than actual batches", errors)
    if complete:
        # Provider 'call' is a decode-attempt ordinal. Only complete actual
        # batch coverage permits this separate one-based actual-batch mapping.
        actual_rows = {i: p for i, p in enumerate(proposals, 1)}
    memory = search.get("model_advice_memory")
    linked, link_scope = None, "No complete actual-batch mapping or no memory report"
    if type(memory) is dict:
        hits, events = memory.get("repeated_prompts_skipped"), memory.get("events")
        require(type(events) is list and len(events) <= 64, "Invalid bounded model memory events")
        check(hits == search.get("model_repeated_prompts_skipped"), "Model skip counters disagree", errors)
        check(count(hits) and count(memory.get("events_omitted")) and len(events) + memory["events_omitted"] == hits,
              "Model memory event omissions disagree", errors)
        check(memory.get("tactics_reused") is False and memory.get("kernel_authority_changed") is False,
              "Model memory claims tactic reuse or changed authority", errors)
        check(count(memory.get("retained_prompts")) and memory["retained_prompts"] <= 128
              and count(memory.get("retained_bytes")) and memory["retained_bytes"] <= 524288,
              "Model memory exceeds declared retention bounds", errors)
        if count(requests) and count(hits):
            check(memory.get("checks") == requests + hits, "Model memory checks differ from requests plus skips", errors)
        linked = 0 if complete else None
        for event in events:
            check(event.get("action") == "skip_repeated_decode" and event.get("tactics_reused") is False,
                  "Invalid model skip event", errors)
            if complete:
                prior = actual_rows.get(event.get("previous_model_call"))
                digest = None if prior is None else hashlib.sha256(json.dumps(prior["goals"], ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
                check(digest == event.get("goals_sha256"), "Model memory link does not match full earlier goals", errors)
                linked += int(digest is not None and digest == event.get("goals_sha256"))
        if complete:
            link_scope = "Memory hashes linked to exact complete-goals JSON; actual-batch ordinals mapped separately from decode attempts"
    return {"actual_batches": actual, "decode_attempts": attempts, "adviser_requests": requests,
            "forward_passes": search.get("forward_passes"), "generated_token_steps": search.get("generated_token_steps"),
            "model_call_unit": search.get("model_call_unit"), "proposal_call_unit": search.get("proposal_call_unit"),
            "proposals_retained": len(proposals) if valid else None, "proposals_omitted": omitted,
            "complete_for_actual_batches": complete, "unique_full_goals": len(groups) if complete else None,
            "repeated_full_goals": len(proposals) - len(groups) if complete else None,
            "retained_unique_full_goals": len(groups) if valid else None,
            "retained_repeats_only": sum(n - 1 for n in groups.values()) if valid else None,
            "repeat_groups": [{"goals_sha256": hashlib.sha256(json.dumps(g, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest(), "count": n}
                              for g, n in groups.items() if n > 1] if valid else None,
            "memory": memory, "linked_memory_events": linked, "memory_link_scope": link_scope,
            "prompt_text_reconstructed": False}, actual_rows


def vampire_audit(search, profile, errors, warnings):
    runs, advice = search.get("vampire_runs"), search.get("advisor_results")
    if type(runs) is not list or type(advice) is not list:
        return {"actual_invocations": search.get("vampire_calls"), "requests": search.get("vampire_advisor_calls"),
                "raw_statuses": None, "cache": search.get("vampire_advice_cache"), "coverage": "missing"}
    require(len(runs) <= 24 and len(advice) <= 24, "Vampire records exceed fixed profile scope")
    executed = [run for run in runs if run.get("executed") is True]
    invoked = [item for item in advice if item.get("invocations") == 1]
    check(all(type(run.get("executed")) is bool for run in runs), "Raw Vampire record lacks invocation flag", errors)
    check(len(executed) == search.get("vampire_calls"), "Actual Vampire launches disagree with raw records", errors)
    complete = len(invoked) == len(executed) and len(advice) == search.get("vampire_advisor_calls")
    if not complete:
        warnings.append("Adviser-result rows do not cover every request/invocation; raw process statuses remain authoritative")
    mismatches, raw_rows = [], []
    for i, run in enumerate(executed, 1):
        check(run.get("profile") == profile and run.get("binary_sha256") == VAMPIRE_SHA
              and run.get("runtime_policy") == "hydra-playground-vampire-runtime-policy-v3",
              "Vampire process profile, binary, or memory policy differs", errors)
        item = invoked[i - 1] if len(invoked) == len(executed) else {}
        if item:
            check(item.get("problem_sha256") == run.get("problem_sha256"), "Vampire advice/process problem hashes differ", errors)
        termination = run.get("termination") or {}
        row = {"invocation": i, "status": run.get("status"), "exit_code": run.get("exit_code"),
               "termination_reason": termination.get("reason"), "advisory_status": item.get("status"),
               "problem_sha256": run.get("problem_sha256"), "elapsed_seconds": run.get("elapsed_seconds"),
               "peak_sampled_rss_bytes": run.get("peak_sampled_rss_bytes"), "rss_samples": run.get("rss_samples")}
        raw_rows.append(row)
        if run.get("status") == "failed" and item.get("status") in {"timeout", "resource_limit"}:
            mismatches.append(row)
    cache = search.get("vampire_advice_cache")
    if type(cache) is dict:
        hits = [a for a in advice if type(a.get("cache")) is dict and a["cache"].get("hit") is True]
        check(cache.get("actual_invocations") == search.get("vampire_calls")
              and cache.get("requests") == search.get("vampire_advisor_calls")
              and cache.get("cache_hits") == len(hits), "Vampire cache/request/actual invocation accounting differs", errors)
        check(cache.get("kernel_checked") is False and count(cache.get("entries")) and cache["entries"] <= 24
              and count(cache.get("retained_input_bytes")) and cache["retained_input_bytes"] <= 262144,
              "Vampire cache exceeds bounds or claims proof authority", errors)
        links = cache.get("hit_records")
        require(type(links) is list and len(links) <= 64, "Missing bounded Vampire cache links")
        check(count(cache.get("hit_records_omitted")) and len(links) + cache["hit_records_omitted"] == len(hits),
              "Vampire cache link omissions differ", errors)
        requests = {a["cache"]["request"]: a for a in advice if type(a.get("cache")) is dict and count(a["cache"].get("request"))}
        for hit in hits:
            check(hit.get("invocations") == 0 and hit.get("suggestions") == 0
                  and hit.get("kernel_checked") is False, "Cached unsuccessful advice supplied new work/proof tactics", errors)
        for link in links:
            current, previous = requests.get(link.get("request")), requests.get(link.get("previous_request"))
            ordinal = link.get("previous_invocation")
            prior_run = executed[ordinal - 1] if type(ordinal) is int and 1 <= ordinal <= len(executed) else None
            require(current is not None and previous is not None and prior_run is not None, "Unbound Vampire cache provenance link")
            check(link["previous_request"] < link["request"] and previous.get("invocations") == 1
                  and prior_run.get("status") in {"completed", "timeout", "resource_limit"}
                  and link.get("previous_status") == previous.get("status")
                  and link.get("previous_exit_code") == prior_run.get("exit_code")
                  and link.get("previous_reason") == str((prior_run.get("termination") or {}).get("reason", ""))[:160]
                  and link.get("previous_profile") == profile and link.get("previous_binary_sha256") == VAMPIRE_SHA
                  and link.get("problem_sha256") == prior_run.get("problem_sha256") == current.get("problem_sha256") == previous.get("problem_sha256"),
                  "Cached unsuccessful provenance differs from an actual previous process", errors)
            check(all(current["cache"].get(k) == v for k, v in link.items() if k != "problem_sha256"),
                  "Cache report and per-request link disagree", errors)
    if mismatches:
        warnings.append("Legacy adviser labels misclassify raw process failures; raw statuses are used below")
    return {"actual_invocations": search.get("vampire_calls"), "requests": search.get("vampire_advisor_calls"),
            "raw_statuses": dict(Counter(run.get("status") for run in executed)),
            "advisory_statuses": dict(Counter(item.get("status") for item in advice)),
            "raw_runs": raw_rows, "cache": cache, "raw_failure_label_mismatches": mismatches,
            "coverage": "complete" if complete else "partial_adviser_metadata"}


def native_observations(search, errors):
    branches = search.get("branches")
    observations = Counter()
    if type(branches) is list:
        require(len(branches) <= 1024, "Retained native branch log is unexpectedly large")
        for branch in branches:
            reason = branch.get("reason")
            if branch.get("status") == "rejected" and type(reason) is str and re.search(r"25000|100000|256[- ]|limit|budget|exceed|too large", reason, re.I):
                observations[(branch.get("command"), reason)] += 1
    plans = search.get("polynomial_decomposition")
    repeated_plans = None
    if type(plans) is dict:
        check(plans.get("trusted_as_proof") is False, "Polynomial plan metadata claims proof authority", errors)
        check(count(plans.get("planning_attempts")) and plans["planning_attempts"] <= 12
              and count(plans.get("planner_invocations")) and plans["planner_invocations"] <= 2 * plans["planning_attempts"]
              and count(plans.get("generated_plans")) and plans["generated_plans"] <= 6,
              "Polynomial planning counters exceed fixed limits", errors)
        rows = plans.get("plans")
        require(type(rows) is list and len(rows) <= 12, "Polynomial plan records exceed bound")
        check(len(rows) == plans.get("planning_attempts"), "Polynomial planning records/counters differ", errors)
        pairs = Counter((row.get("state_sha256"), row.get("script_sha256")) for row in rows
                        if count(row.get("chunks_attempted")) and row["chunks_attempted"] > 0)
        repeated_plans = [{"state_sha256": state, "script_sha256": script, "attempts": n}
                          for (state, script), n in pairs.items() if n > 1]
        for row in rows:
            check(row.get("kernel_checked") is False, "Partial polynomial plan marked as a proved theorem", errors)
            if row.get("commands") is not None:
                check(type(row["commands"]) is int and 1 <= row["commands"] <= 156
                      and count(row.get("script_bytes")) and row["script_bytes"] <= 65536,
                      "Polynomial plan script exceeds its bound", errors)
        memory = plans.get("attempt_memory")
        if type(memory) is dict:
            check(memory.get("repeated_decompositions_skipped") == plans.get("repeated_decompositions_skipped")
                  and memory.get("checks") == plans["planning_attempts"] + plans["repeated_decompositions_skipped"]
                  and memory.get("remember_requests") == plans["generated_plans"], "Decomposition skip/attempt counters disagree", errors)
            check(memory.get("tactics_cached") is False and memory.get("proofs_cached") is False
                  and memory.get("kernel_authority_changed") is False, "Decomposition memory claims proof/tactic authority", errors)
            check(count(memory.get("retained_goal_states")) and memory["retained_goal_states"] <= 6
                  and count(memory.get("retained_payload_bytes")) and memory["retained_payload_bytes"] <= 524288,
                  "Decomposition memory exceeds bounds", errors)
            events = memory.get("events")
            require(type(events) is list and len(events) <= 64, "Invalid decomposition memory events")
            if memory.get("events_omitted") == 0:
                check(sum(event.get("action") == "skip_repeated_decomposition" for event in events)
                      == memory.get("repeated_decompositions_skipped"), "Decomposition skip-event count differs", errors)
                remembered = {}
                for event in events:
                    if event.get("action") in {"remember_attempt", "remember_shallower_attempt"}:
                        remembered[event.get("plan_id")] = event
                    if event.get("action") == "skip_repeated_decomposition":
                        prior = remembered.get(event.get("previous_plan_id")) or {}
                        check(prior.get("goals_sha256") == event.get("goals_sha256")
                              and prior.get("depth") == event.get("previous_depth")
                              and count(event.get("requested_depth")) and count(event.get("previous_depth"))
                              and event["requested_depth"] >= event["previous_depth"], "Decomposition skip has no earlier equal/shallower attempt link", errors)
    return {"retained_branches": len(branches) if type(branches) is list else None,
            "branches_omitted": search.get("branches_omitted"), "diagnostics_omitted": search.get("diagnostics_omitted"),
            "limit_rejections_in_retained_branches": [{"command": command, "reason": reason, "count": n}
                                                       for (command, reason), n in observations.items()] if type(branches) is list else None,
            "scope": "Retained rejected attempts only; omitted branches are not reconstructed or extrapolated",
            "repeated_plan_state_digest_pairs": repeated_plans,
            "plan_digest_scope": "Reported state/script digest pairs; full plan-state goals are not reconstructed by this auditor",
            "polynomial_decomposition": plans}


def audit_case(path, case, planned, spec, batch_pins, plan_pin, errors, warnings):
    record = load(path)
    name, version, _, _, mode, profile, calls, beam, _ = spec
    _, native, worker, reserve = configured_limits(profile, mode, calls, beam)
    request = {"theorem": case["theorem"], "search_mode": mode, "search_profile": profile,
               "max_model_calls": calls, "beam_width": beam}
    canonical = planned.get("canonical_theorem")
    check(record.get("schema") == "hydra-advanced-http-case-v1" and record.get("origin") == "live_http_search",
          "Case is not a live HTTP search record", errors)
    check(record.get("case_id") == case["id"] and record.get("record_file") == path.name
          and record.get("expected") == case.get("expected", "provable") and record.get("input_supported") is True,
          "Case identity/expectation differs from fixed curriculum", errors)
    check(record.get("request") == request == planned.get("request")
          and record.get("normalized_request") == request == planned.get("normalized_request")
          and type(canonical) is str and bool(canonical) and record.get("canonical_theorem") == canonical,
          "Original theorem/settings differ from frozen request or canonical record", errors)
    check(record.get("search_mode") == mode and record.get("search_profile") == profile
          and record.get("submission_count") == 1 and record.get("automatic_retry") is False
          and record.get("reference_scripts_sent_to_server") is False, "Search mode/submission/no-reference contract differs", errors)
    check(record.get("run_context") == {"plan_sha256": plan_pin["sha256"], "source_pins_sha256": pin(path.parent / "source-pins.json")["sha256"]},
          "Case is not bound to its plan and source pins", errors)
    check(record.get("limits") == {"worker_wall_seconds": worker["wall_seconds"], "cleanup_seconds": reserve,
                                   "case_wall_seconds": worker["wall_seconds"] + reserve}, "Case deadline settings differ", errors)
    job = record.get("last_job_after_cancel", record.get("last_job", {}))
    job = job if type(job) is dict else {}
    result = job.get("result") if type(job.get("result")) is dict else {}
    search = result.get("search") if type(result.get("search")) is dict else {}
    execution = result.get("execution", job.get("execution"))
    execution = execution if type(execution) is dict else {}
    observed_metrics = normalized_metrics(job)
    check(record.get("metrics") == observed_metrics, "Case counters do not match final result/progress with null-preserving precedence", errors)
    for key, expected in (("server_elapsed_seconds", job.get("elapsed_seconds")), ("worker_elapsed_seconds", execution.get("elapsed_seconds")), ("search_elapsed_seconds", search.get("elapsed_seconds"))):
        check(record.get(key) == expected, "Timing source mismatch: " + key, errors)
    outcome = record.get("outcome")
    if case.get("expected") == "not_provable":
        check(result.get("kernel_checked") is not True and result.get("status") not in {"proof", "proved"},
              "CRITICAL: false control has a claimed checked proof", errors)
    row = {"batch": name, "case_id": case["id"], "record": relative(path), "record_pin": pin(path),
           "expected": case.get("expected", "provable"), "request": request, "canonical_theorem": canonical,
           "outcome": outcome, "job_id": record.get("job_id"), "job_state": job.get("state"),
           "search_status": search.get("status"), "result_status": result.get("status"), "limited_by": search.get("limited_by"),
           "kernel_verified_by_server": record.get("kernel_verified"), "new_replay_by_this_auditor": False,
           "proof_steps": record.get("proof_steps"), "proof_nodes": record.get("proof_nodes"),
           "winning_steps": None, "counters": observed_metrics["values"], "counter_sources": observed_metrics["sources"],
           "counters_include_partial_progress": observed_metrics["last_progress_is_partial"],
           "timings_seconds": {key: record.get(key) for key in TIMES}, "worker_execution": execution,
           "cleanup": record.get("cleanup"), "error": record.get("error", job.get("error")),
           "started_at_utc": record.get("started_at_utc"), "finished_at_utc": record.get("finished_at_utc"),
           "errors": errors, "warnings": warnings}
    check(type(record.get("finished_at_utc")) is str, "Case has no finished timestamp", errors)
    if record.get("job_id") is not None:
        check(type(record["job_id"]) is str and re.fullmatch(r"[0-9a-f]{32}", record["job_id"]) is not None
              and job.get("id") == record["job_id"], "Terminal job is not the submitted owned ID", errors)
        check(record.get("submission_http_status") == 202
              and (record.get("submission_response") or {}).get("job_id") == record["job_id"], "Job lacks a matching accepted HTTP submission", errors)
        check(job.get("state") in {"completed", "failed", "cancelled"} and execution.get("quiescent") is True,
              "Owned worker is not terminal and quiescent", errors)
    if outcome not in {"proved", "unknown"}:
        errors.append("Retained non-search outcome; not reclassified as unknown: " + str(outcome))
        row.update(model=model_audit(search, errors)[0], vampire=vampire_audit(search, profile, errors, warnings),
                   native_observations=native_observations(search, errors))
        return row
    check(job.get("state") == "completed" and execution.get("worker_started") is True
          and execution.get("worker_exit_code") == 0 and execution.get("quiescent") is True,
          "Normal result lacks zero worker exit and owned cleanup", errors)
    check(result.get("theorem") == search.get("theorem") == canonical
          and result.get("kernel_source_commit") == KERNEL_COMMIT, "Result theorem/kernel does not match requested original", errors)
    check(search.get("profile") == "hydra-playground-hybrid-" + version and search.get("limits") == native
          and search.get("settings_profile") == profile and search.get("search_mode") == mode
          and search.get("requested_beam_width") == beam and result.get("search_mode") == mode,
          "Actual search version/profile/budget differs from request", errors)
    runtime_names = RUNTIME_NAMES | added_names(version)
    check(search.get("application_source_pins") == {key: batch_pins["application"][key] for key in runtime_names},
          "Per-worker application source binding differs from frozen batch", errors)
    model, actual_rows = model_audit(search, errors)
    row.update(model=model, vampire=vampire_audit(search, profile, errors, warnings), native_observations=native_observations(search, errors))
    if count(search.get("model_calls")) and count(search.get("vampire_calls")):
        check(result.get("model_used") is (search["model_calls"] > 0)
              and result.get("vampire_used") is (search["vampire_calls"] > 0),
              "Adviser-used flags disagree with actual invocation counters", errors)
    for counter, ceiling in (("model_calls", native["max_model_calls"]), ("model_advisor_calls", native["max_model_calls"]),
                             ("vampire_calls", native["max_vampire_calls"]), ("vampire_advisor_calls", native["max_vampire_calls"])):
        value = search.get(counter)
        check(count(value) and value <= ceiling, "Adviser count exceeds request cap: " + counter, errors)
    commands, provenance, trace = result.get("commands"), search.get("provenance"), result.get("trace")
    require(type(commands) is list and type(provenance) is list and type(trace) is list, "Missing returned proof path/trace")
    check(search.get("commands") == commands and len(commands) == len(provenance), "Proof commands/provenance lengths disagree", errors)
    sources = Counter(item.get("source") for item in provenance)
    check(set(sources) <= {"heuristic", "model", "vampire"} and dict(sources) == result.get("proof_sources"), "Winning-source counters disagree", errors)
    row["winning_steps"] = {source: sources[source] for source in ("heuristic", "model", "vampire")}
    if outcome == "unknown":
        check(record.get("kernel_verified") is False and result.get("kernel_checked") is False
              and search.get("kernel_checked") is False and result.get("status") == search.get("status") in {"limit", "exhausted"}
              and record.get("search_status") == result.get("status") and commands == provenance == trace == []
              and result.get("proof_nodes") is None, "Unknown status contains a claimed certificate or wrong stop reason", errors)
        return row
    check(case.get("expected", "provable") == "provable", "CRITICAL: a false control has a claimed checked proof", errors)
    check(record.get("kernel_verified") is True and result.get("kernel_checked") is True and search.get("kernel_checked") is True
          and result.get("status") == "proved" and search.get("status") == "proof" and result.get("goals") == []
          and type(result.get("proof_nodes")) is int and 0 < result["proof_nodes"] <= 100000
          and record.get("proof_nodes") == search.get("certificate_nodes") == result.get("proof_nodes")
          and 0 < len(commands) == record.get("proof_steps") <= native["max_depth"], "Proof claim lacks original-goal kernel evidence", errors)
    tactic_trace = [item for item in trace if "tactic" in item]
    check([item.get("tactic") for item in tactic_trace] == commands
          and [item.get("origin") for item in tactic_trace] == provenance
          and all(item.get("status") == "ok" for item in tactic_trace), "Native replay trace does not match full proof/provenance", errors)
    check(bool(tactic_trace) and tactic_trace[0].get("goals_before") == ["⊢ " + canonical]
          and tactic_trace[-1].get("goals_after") == []
          and all(a.get("goals_after") == b.get("goals_before") for a, b in zip(tactic_trace, tactic_trace[1:])),
          "Native trace does not connect the original goal to no remaining goals", errors)
    check(bool(trace) and trace[-1].get("qed") is True and trace[-1].get("theorem") == canonical
          and trace[-1].get("proof_size") == result.get("proof_nodes") and trace[-1].get("tactic_count") == len(commands),
          "Native final QED record differs from proof claim", errors)
    previous_branch = 0
    for i, item in enumerate(provenance, 1):
        check(item.get("step") == i and item.get("command") == commands[i - 1] and item.get("parent_id") == previous_branch,
              "Winning proof step/prefix identity is discontinuous", errors)
        previous_branch = item.get("branch_id")
        evidence = item.get("evidence") or {}
        if item.get("source") == "model":
            ordinal = int(evidence.get("model_call", "0"))
            check(count(search.get("model_calls")) and 1 <= ordinal <= search["model_calls"], "Winning model step has no actual batch", errors)
            if actual_rows:
                check(item.get("command") in actual_rows.get(ordinal, {}).get("candidates", []), "Winning model tactic absent from its actual batch", errors)
        if item.get("source") == "vampire":
            digest = evidence.get("problem_sha256")
            check(any(run.get("problem_sha256") == digest and run.get("executed") is True and run.get("status") == "completed" for run in search.get("vampire_runs", []))
                  and any(a.get("problem_sha256") == digest and a.get("invocations") == 1 and (a.get("suggestions") or 0) > 0 for a in search.get("advisor_results", [])),
                  "Winning Vampire step lacks an actual solver/advice record", errors)
    row["commands"] = commands
    row["provenance"] = provenance
    return row


def check_summary(summary, records):
    modes = {}
    for mode in {record["search_mode"] for record in records}:
        selected = [record for record in records if record["search_mode"] == mode]
        counters = {}
        for key in COUNTERS:
            values = [r["metrics"]["values"][key] for r in selected if r["metrics"]["values"].get(key) is not None]
            final = sum(r["metrics"]["sources"].get(key) in {"result", "result.search"} for r in selected)
            counters[key] = {"observed_total": sum(values) if values else None, "observed_cases": len(values),
                             "final_result_cases": final, "includes_partial_progress": final < len(values)}
        timings = {key: {"observed_total": round(sum(r[key] for r in selected if number(r.get(key))), 5),
                         "observed_cases": sum(number(r.get(key)) for r in selected)} for key in TIMES}
        modes[mode] = {"recorded": len(selected), "outcomes": dict(Counter(r["outcome"] for r in selected)),
                       "counters": counters, "timings": timings}
    require(summary.get("modes") == modes, "Saved summary does not reconcile with case counters/outcomes/timing sources")


def audit_batch(spec, curricula, archives):
    name, version, curriculum_name, ids, mode, profile, calls, beam, ceiling = spec
    directory = BASE / name
    errors, warnings = [], []
    report = {"name": name, "version": version, "expected_case_ids": list(ids), "status": "not_finalized",
              "receipt": None, "cases": [], "errors": errors, "warnings": warnings}
    # Do not read any plan, pins, or cases from a still-running batch.
    if not (directory / "actual-completion.json").is_file():
        errors.append("No externally observed completion receipt; live batch not inspected")
        return report, None
    try:
        receipt, observed = normalized_receipt(directory / "actual-completion.json")
        report["receipt"] = observed
        summary = load(directory / "summary.json")
        plan = load(directory / "plan.json")
        before = load(directory / "source-pins.json")
        after = load(directory / "source-pins-after.json")
        report.update(status="failed_or_incomplete", summary=relative(directory / "summary.json"),
                      summary_status=summary.get("status"), elapsed_client_batch_seconds=summary.get("elapsed_seconds"),
                      reported_outcomes=summary.get("modes"), source_pins_unchanged=before == after)
        if type(receipt.get("summary")) is dict and "sha256" in receipt["summary"]:
            binding(directory / "summary.json", receipt["summary"])
        require(before == after and summary.get("source_pins_unchanged") is True, "Source pins changed during batch")
        expected_names = APP_NAMES | added_names(version)
        require(type(before.get("application")) is dict and set(before["application"]) == expected_names, "Active application pin scope differs")
        require(all(before["application"][key] == archives[version]["files"].get(key) for key in expected_names), "Batch application pins differ from frozen source archive")
        require(before.get("kernel_commit") == KERNEL_COMMIT and before.get("vampire_package", {}).get("vampire", {}).get("sha256") == VAMPIRE_SHA, "Kernel or Vampire binary identity differs")
        binding(directory / "source-pins.json", plan.get("source_pins"))
        binding(CURRICULA[curriculum_name][0], plan.get("curriculum"))
        search_limits, _, worker_limits, reserve = configured_limits(profile, mode, calls, beam)
        limits = plan.get("limits") or {}
        selected = limits.get("selected_profile") or {}
        require(plan.get("schema") == "hydra-advanced-http-plan-v1" and plan.get("origin") == "live_http_search"
                and plan.get("modes") == [mode] and plan.get("profile") == profile and plan.get("max_model_calls") == calls
                and plan.get("beam_width") == beam and plan.get("automatic_retry") is False and plan.get("reference_scripts_sent_to_server") is False,
                "Batch plan differs from frozen selection/settings/no-reference contract")
        require(limits.get("global_wall_seconds") == ceiling and limits.get("cleanup_reserve_seconds") == reserve
                and selected.get("id") == profile and selected.get("worker") == worker_limits and selected.get("search") == search_limits,
                "Batch plan changed native/worker resource limits")
        planned = plan.get("jobs")
        require(type(planned) is list and [job.get("case_id") for job in planned] == list(ids), "Requested case order/selection differs")
        expected_files = [f"{i:03d}-{case_id}-{mode}.json" for i, case_id in enumerate(ids)]
        files = summary.get("case_files")
        require(type(files) is list and files == expected_files[:len(files)], "Case filenames/order differ or include unplanned records")
        require(summary.get("requested_jobs") == len(ids) and summary.get("recorded_jobs") == len(files), "Batch count metadata differs")
        report["selected_profile"] = selected
        report["plan_pin"] = pin(directory / "plan.json")
        raw_records = []
        for i, filename in enumerate(files):
            case_errors, case_warnings = [], []
            path = safe_child(directory, filename)
            raw = None
            try:
                binding(path, (summary.get("case_file_pins") or {}).get(filename))
                raw = load(path)
                raw_records.append(raw)
                row = audit_case(path, curricula[curriculum_name][ids[i]], planned[i], spec, before,
                                 pin(directory / "plan.json"), case_errors, case_warnings)
            except Exception as error:
                case_errors.append(type(error).__name__ + ": " + str(error))
                row = {"batch": name, "case_id": ids[i], "record": relative(path), "outcome": None if raw is None else raw.get("outcome"),
                       "job_id": None if raw is None else raw.get("job_id"), "retained_raw_metrics": None if raw is None else raw.get("metrics"),
                       "errors": case_errors, "warnings": case_warnings}
            row["artifact_consistency_passed"] = not case_errors
            report["cases"].append(row)
        check_summary(summary, raw_records)
        check(observed["actual_exit_code"] == 0, "Runner actually exited nonzero", errors)
        check(summary.get("status") == "complete" and summary.get("all_requested_cases_completed") is True
              and summary.get("fatal_error") is None and len(files) == len(ids), "Runner did not complete all requested cases", errors)
        check(summary.get("automatic_retry") is False and summary.get("benchmark_claim") is False
              and summary.get("training_performed") is False, "Summary training/retry/benchmark contract differs", errors)
        if name == "baseline-v4-01":
            check(observed["completion_chunk"] == "ce12c4" and observed["launch_chunk"] == "aaa714" and observed["session_id"] == 33870,
                  "Baseline completion differs from the already observed receipt", errors)
        if name == "comparison-v5-01":
            check(observed["launch_chunk"] == "9bdc91" and observed["session_id"] == 42748 and observed["completion_chunk"] == "6c600e",
                  "Comparison is not the observed single completed run", errors)
        if not errors and all(row["artifact_consistency_passed"] for row in report["cases"]):
            report["status"] = "complete"
        return report, before
    except Exception as error:
        errors.append(type(error).__name__ + ": " + str(error))
        report["status"] = "failed_or_incomplete"
        return report, None


def audit_gates(archives):
    rows, source_records = [], []
    gate_specs = (("full-gate-01", 1, "ad9270", 162, 9), ("worker-gate-02", 0, "6e05f7", 10, 0), V6_GATE)
    for name, expected_exit, completion, tests, failures in gate_specs:
        errors = []
        version = "v6" if name == V6_GATE[0] else "v5"
        archive = archives[version]
        row = {"name": name, "version": version, "errors": errors}
        try:
            directory = BASE / name
            receipt, observed = normalized_receipt(directory / "actual-completion.json")
            result = load(directory / "result.json")
            if "result" in receipt:
                binding(directory / "result.json", receipt["result"])
            elif version == "v6":
                require(pin(directory / "result.json")["sha256"] == V6_GATE_RESULT_SHA
                        and receipt.get("tests") == tests, "Final focused gate result differs from its observed checkpoint")
            else:
                raise AuditError("Legacy gate receipt lacks its observed result hash")
            before, after = load(directory / "source-before.json"), load(directory / "source-after.json")
            if version == "v5":
                source_records.append(before)
            check(before == after and all(archive["files"].get(k) == v for k, v in before.items()), "Gate sources differ from their frozen " + version + " archive", errors)
            output = read_bytes(directory / "output.txt").decode("utf-8")
            read_bytes(directory / "run.py")
            fail_lines = re.findall(r"^FAIL: (.+)$", output, re.M)
            check(observed["actual_exit_code"] == expected_exit and observed["completion_chunk"] == completion
                  and result.get("tests") == tests and result.get("failures") == failures and result.get("errors") == 0
                  and result.get("skipped") == 0 and result.get("passed") is (expected_exit == 0)
                  and result.get("source_pins_unchanged") is True, "Gate receipt/result differs from observed outcome", errors)
            check(len(fail_lines) == failures and all("test_worker.NativeReplayTests." in line for line in fail_lines)
                  and re.search(r"^Ran " + str(tests) + r" tests in ", output, re.M) is not None,
                  "Gate transcript does not match declared tests/failure scope", errors)
            interpretation = ("Failed whole-suite attempt retained; affected worker tests separately rerun" if expected_exit else
                              "Ten affected worker tests passed on unchanged app source; not a rerun of the whole suite")
            if version == "v6":
                interpretation = "Separate final-version focused tests; does not relabel the original whole-suite attempt"
            row.update(receipt=observed, result=result, result_hash_in_receipt="result" in receipt,
                       failure_entries=fail_lines, interpretation=interpretation)
        except Exception as error:
            errors.append(type(error).__name__ + ": " + str(error))
        row["evidence_consistent"] = not errors
        rows.append(row)
    if len(source_records) == 2 and source_records[0] != source_records[1]:
        rows[1]["errors"].append("The retest used different application source from the failed gate")
        rows[1]["evidence_consistent"] = False
    return rows


def markdown(report, destination):
    def link(label, path):
        return "[" + label + "](" + os.path.relpath(ROOT / path, destination) + ")"
    def value(item):
        return "—" if item is None else str(item)
    def cell(row):
        if not row:
            return "not finalized"
        state = row.get("outcome") or "unavailable"
        if state == "unknown":
            state += " / " + str(row.get("result_status"))
        return state
    cases = {(batch["name"], row["case_id"]): row for batch in report["batches"] for row in batch["cases"]}
    lines = ["Artifact audit: **" + report["status"] + "**. " + str(report["audited_case_records"]) + "/" + str(TOTAL_CASES) + " planned case records inspected only after external runner completion receipts.",
             "This is a saved-evidence consistency audit, with no new proof replay, model, solver or HTTP calls. Mathematical expectations do not convert bounded search failure into refutation. Weight/gallery authentication and independent publication replays are separate.",
             "Five fixed Hybrid/Deep/32/beam-4 cases are paired below. The final v6 regressions/controls and one F7 follow-up are an explicitly separate prospective extension, excluded from that paired denominator.",
             "| Target | v4 outcome | v5 outcome | v4/v5 server seconds | v4/v5 actual model batches | v4/v5 repeated full goals |",
             "| --- | --- | --- | ---: | ---: | ---: |"]
    for case_id in SHARED:
        a, b = (cases.get((name, case_id), {}) for name in ("baseline-v4-01", "comparison-v5-01"))
        pair = lambda getter: " / ".join(value(getter(row)) for row in (a, b))
        time_value = lambda r: round(r["timings_seconds"]["server_elapsed_seconds"], 3) if number(r.get("timings_seconds", {}).get("server_elapsed_seconds")) else None
        lines.append("| " + case_id + " | " + cell(a) + " | " + cell(b) + " | " + pair(time_value) + " | "
                     + pair(lambda r: r.get("model", {}).get("actual_batches")) + " | "
                     + pair(lambda r: r.get("model", {}).get("repeated_full_goals")) + " |")
    lines += ["", "| Batch / case | Outcome | Proof steps / nodes | Winning H/M/V | Actual model / decode attempts | Vampire launches / requests / cache hits |",
              "| --- | --- | ---: | ---: | ---: | ---: |"]
    for batch in report["batches"]:
        for row in batch["cases"]:
            source = row.get("winning_steps") or {}
            model, vampire = row.get("model") or {}, row.get("vampire") or {}
            hits = (vampire.get("cache") or {}).get("cache_hits")
            lines.append("| " + link(batch["name"] + " / " + row["case_id"], row["record"]) + " | " + cell(row) + " | "
                         + value(row.get("proof_steps")) + " / " + value(row.get("proof_nodes")) + " | "
                         + "/".join(value(source.get(k)) for k in ("heuristic", "model", "vampire")) + " | "
                         + value(model.get("actual_batches")) + " / " + value(model.get("decode_attempts")) + " | "
                         + " / ".join(value(v) for v in (vampire.get("actual_invocations"), vampire.get("requests"), hits)) + " |")
    lines += ["", "Exact-goal repeats use the complete ordered goal tuple, without normalization. The complete count is null when proposal omissions or missing actual batches prevent reconciliation. Decode attempts, actual forward-pass batches, model skips, Vampire requests and Vampire launches are separate units. Legacy absent cache fields remain null. Raw Vampire process statuses take priority over adviser labels.",
              "Native work/proof-size rejections, polynomial plan counters, raw solver failures, worker exit/cleanup, omitted diagnostic counts, all timing sources, source pins and full winning scripts/provenance are retained in " + link("audit.json", relative(destination / "audit.json")) + ". Retained branch counts are not extrapolated to omitted logs.",
              "Whole-version engineering comparison only: selected exposed classical probes, one paired run, familiar schemas and a lossy local 4-bit model. Weights, native kernel and fixed profile caps were not intentionally changed. Early baseline timing overlapped short native prototype checks, so no controlled speedup or model-quality improvement is inferred. A winning source is credited only by its actual returned proof steps.", ""]
    for batch in report["batches"]:
        receipt = batch.get("receipt") or {}
        lines.append(link(batch["name"], relative(BASE / batch["name"] / "summary.json")) + ": " + batch["status"]
                     + "; observed outer exit " + value(receipt.get("actual_exit_code")) + ", completion " + value(receipt.get("completion_chunk")) + ".")
    lines.append("")
    for gate in report["gates"]:
        result, receipt = gate.get("result") or {}, gate.get("receipt") or {}
        lines.append(link(gate["name"], relative(BASE / gate["name"] / "actual-completion.json")) + ": observed exit "
                     + value(receipt.get("actual_exit_code")) + ", " + value(result.get("tests")) + " tests, "
                     + value(result.get("failures")) + " failure entries. " + gate.get("interpretation", "Evidence incomplete.") + ".")
    issues = list(report["errors"])
    for batch in report["batches"]:
        issues.extend(batch["name"] + ": " + text for text in batch["errors"] + batch["warnings"])
        for row in batch["cases"]:
            issues.extend(batch["name"] + "/" + row["case_id"] + ": " + text for text in row["errors"] + row["warnings"])
    for gate in report["gates"]:
        issues.extend(gate["name"] + ": " + text for text in gate["errors"])
    if issues:
        lines += ["", "Audit issues and retained caveats:", ""] + ["- " + text for text in issues]
    return "\n\n".join(lines).replace("|\n\n|", "|\n|").replace("\n\n\n\n", "\n\n") + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    destination = args.output.absolute()
    require(destination.resolve().is_relative_to(BASE) and not any(p.is_symlink() for p in (destination, *destination.parents)), "Output must be a fresh ordinary directory under this progress artifact root")
    destination.mkdir(parents=False, exist_ok=False)
    report = {"schema": "hydra-progress-completed-runs-audit-v1", "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
              "status": "incomplete", "planned_case_records": TOTAL_CASES, "audited_case_records": 0,
              "input_path_base": "workspace root; artifact links in AUDIT.md are relative", "batches": [], "gates": [], "errors": [],
              "scope": "Read-only finalized artifact/hash/accounting audit; no native replay, model, solver, HTTP, current weight or gallery authentication",
              "unseen_benchmark_claim": False, "model_quality_claim": False, "fresh_native_replays": 0,
              "proof_scope": "Saved server original-goal kernel result and native replay trace consistency; independent publisher replay remains separate"}
    try:
        read_bytes(Path(__file__).resolve())
        design = load(HERE / "manifest.json")
        require(pin(HERE / "manifest.json")["sha256"] == "8b553252fd17fe0907a88a86c11a3fd98d559679fcab984e2b5f2ca07a09aaaf", "Frozen evaluation design manifest changed")
        for name, descriptor in design["files"].items():
            binding(safe_child(HERE, name), descriptor)
        read_bytes(HERE / "V6_REFINEMENT.md")
        require(pin(HERE / "V6_REFINEMENT.md")["sha256"] == V6_REFINEMENT_SHA, "Prospective v6 extension changed after its pre-run checkpoint")
        report["prospective_v6_extension"] = {"path": relative(HERE / "V6_REFINEMENT.md"), **pin(HERE / "V6_REFINEMENT.md")}
        curricula = {}
        for key, (path, expected) in CURRICULA.items():
            curriculum = load(path)
            require(pin(path)["sha256"] == expected, "Frozen curriculum changed: " + key)
            curricula[key] = {case["id"]: case for case in curriculum["cases"]}
        archives = {version: audit_archive(version) for version in ARCHIVES}
        report["archives"] = {version: {"manifest": relative(ARCHIVES[version][0] / "manifest.json"),
                                        "files_rehashed": len(archive["files"])} for version, archive in archives.items()}
        pins = {}
        for spec in SPECS:
            batch, saved = audit_batch(spec, curricula, archives)
            report["batches"].append(batch)
            if saved is not None:
                pins[spec[0]] = saved
        report["gates"] = audit_gates(archives)
        if "baseline-v4-01" in pins:
            baseline = pins["baseline-v4-01"]
            for name, saved in pins.items():
                check(all(saved.get(key) == baseline.get(key) for key in UNCHANGED_PIN_KEYS), name + ": saved kernel/model/package metadata differs from baseline", report["errors"])
        batches = {batch["name"]: batch for batch in report["batches"]}
        a, b = batches.get("baseline-v4-01", {}), batches.get("comparison-v5-01", {})
        if a.get("selected_profile") is not None and b.get("selected_profile") is not None:
            check(a["selected_profile"] == b["selected_profile"], "Full selected profile differs across matched versions", report["errors"])
        paired_a = {row["case_id"]: row for row in a.get("cases", [])}
        paired_b = {row["case_id"]: row for row in b.get("cases", [])}
        for case_id in SHARED:
            if case_id in paired_a and case_id in paired_b:
                check(paired_a[case_id].get("request") == paired_b[case_id].get("request")
                      and paired_a[case_id].get("canonical_theorem") == paired_b[case_id].get("canonical_theorem"),
                      "Matched request/canonical theorem differs: " + case_id, report["errors"])
        jobs = [row.get("job_id") for batch in report["batches"] for row in batch["cases"] if row.get("job_id") is not None]
        check(len(jobs) == len(set(jobs)), "An HTTP job ID was reused across case records", report["errors"])
        # Rehash only already-read finalized inputs, never any current runtime.
        for key in tuple(INPUTS):
            read_bytes(ROOT / key)
    except Exception as error:
        report["errors"].append(type(error).__name__ + ": " + str(error))
    report["audited_case_records"] = sum(len(batch["cases"]) for batch in report["batches"])
    complete = (not report["errors"] and len(report["batches"]) == len(SPECS) and report["audited_case_records"] == TOTAL_CASES
                and all(batch["status"] == "complete" for batch in report["batches"])
                and len(report["gates"]) == 3 and all(gate["evidence_consistent"] for gate in report["gates"]))
    report["status"] = "complete" if complete else "failed_or_incomplete"
    report["inputs"] = [{"path": key, **descriptor} for key, descriptor in sorted(INPUTS.items())]
    report["input_read_bytes_including_rechecks"] = READ_BYTES
    (destination / "audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    (destination / "AUDIT.md").write_text(markdown(report, destination), encoding="utf-8")
    print(json.dumps({"status": report["status"], "audited_case_records": report["audited_case_records"],
                      "audit": str(destination / "audit.json"), "report": str(destination / "AUDIT.md")}))
    return 0 if complete else 2


if __name__ == "__main__":
    sys.exit(main())
