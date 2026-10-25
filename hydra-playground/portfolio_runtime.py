"""Two supervised workers, one original theorem, and no combined proof scripts.

The callback is server.run_worker: it must enforce its fixed worker wall/RSS
limits and return only after cleanup. This coordinator never starts a process,
loads a model, or trusts a solver result in place of a native certificate.
"""
from __future__ import annotations

import copy
import json
import math
import time

POLICY = "hydra-model-first-portfolio-v1"
WALL_SECONDS = 550.0
MAX_RESULT_BYTES = 8 * 1024**2
PHASE_WALL_SECONDS = {"sequential": 360.0, "symbolic": 180.0}
UNKNOWN_REASONS = frozenset({"deadline", "action_budget", "token_budget", "no_candidate",
                             "tactic_error", "tactic_limit", "kernel_rejection", "result_limit"})
ADMISSION_ERRORS = frozenset({
    "formula exceeds the bound/context-variable limit",
    "formula/term exceeds the AST node/depth limits",
    "formula/term source exceeds the 512-token limit",
    "formula/term source exceeds the parenthesis-depth limit",
})
EXECUTION_FIELDS = ("error", "cancelled", "elapsed_seconds", "peak_sampled_rss_bytes",
                    "peak_sampled_solver_rss_bytes", "quiescent", "worker_started", "worker_exit_code")
SUM_COUNTERS = ("model_calls", "vampire_calls", "states_expanded", "tactic_attempts", "forward_passes")


def _require(condition, message):
    if not condition:
        raise ValueError(message)


def _number(value):
    return type(value) in (int, float) and math.isfinite(value) and value >= 0


def _count(value):
    return type(value) is int and value >= 0


def _summary(phase, request, outcome):
    result = outcome.get("result")
    search = result.get("search", {}) if type(result) is dict else {}
    return {"phase": phase, "request": dict(request),
            "execution": {key: outcome.get(key) for key in EXECUTION_FIELDS},
            "status": result.get("status") if type(result) is dict else None,
            "kernel_checked": result.get("kernel_checked") is True if type(result) is dict else False,
            "search_counters": {key: value for key, value in search.items()
                                if type(value) in (int, float, bool) or value is None},
            "stop_reason": search.get("stop_reason", search.get("status")),
            "search_error": search.get("error"),
            "repeated_state_guard": copy.deepcopy(search.get("repeated_state_guard")),
            "proof_sources": copy.deepcopy(result.get("proof_sources", {})) if type(result) is dict else {}}


def _validate_execution(outcome, phase):
    _require(type(outcome) is dict and all(key in outcome for key in EXECUTION_FIELDS),
             "Missing supervised worker completion fields.")
    _require(type(outcome["quiescent"]) is bool and type(outcome["cancelled"]) is bool
             and type(outcome["worker_started"]) is bool, "Invalid worker cleanup fields.")
    _require(_number(outcome["elapsed_seconds"])
             and all(_count(outcome[key]) for key in ("peak_sampled_rss_bytes", "peak_sampled_solver_rss_bytes")),
             "Invalid worker resource accounting.")
    if outcome.get("result") is not None:
        _require(outcome["error"] is None and outcome["cancelled"] is False
                 and outcome["quiescent"] is True and outcome["worker_started"] is True
                 and type(outcome["worker_exit_code"]) is int and outcome["worker_exit_code"] == 0,
                 "A result lacks a clean, quiescent worker exit.")
        _require(outcome["elapsed_seconds"] < PHASE_WALL_SECONDS[phase],
                 "Worker result exceeds its fixed wall budget.")


def _validate_result(result, phase, original, canonical=None, source_commit=None):
    _require(type(result) is dict and result.get("kind") == phase,
             "Unexpected worker result kind.")
    theorem = result.get("theorem")
    _require(type(theorem) is str and bool(theorem), "Missing canonical theorem.")
    if canonical is not None:
        _require(theorem == canonical, "Fallback proves a different original theorem.")
    _require(type(result.get("kernel_source_commit")) is str and bool(result["kernel_source_commit"]),
             "Missing native source identity.")
    if source_commit is not None:
        _require(result["kernel_source_commit"] == source_commit, "Native source identities differ.")
    search = result.get("search")
    _require(type(search) is dict and _count(search.get("model_calls"))
             and _count(search.get("vampire_calls")), "Missing actual component counters.")
    if phase == "sequential":
        admission = result.get("native_admission", {})
        _require(result.get("original_theorem") == original and admission.get("input_theorem") == original
                 and admission.get("theorem") == theorem and result.get("proof_profile") == "sequential",
                 "Sequential result is not bound to the original request/admission.")
        _require(search["model_calls"] <= 128 and search["vampire_calls"] == 0,
                 "Sequential component counters exceed the selected route.")
    else:
        _require(search["model_calls"] == 0 and result.get("model_used") is False
                 and search["vampire_calls"] <= 4, "Symbolic fallback used an unexpected model or budget.")
    proved = result.get("status") == "proved"
    _require(result.get("kernel_checked") is proved, "Proof status/kernel flag mismatch.")
    if not proved:
        _require(result.get("status") in ({"unknown"} if phase == "sequential" else {"limit", "exhausted", "unknown"}),
                 "Unexpected unresolved search status.")
        if phase == "sequential":
            _require(search.get("stop_reason") in UNKNOWN_REASONS,
                     "Sequential search ended with an internal failure, not a valid bounded unknown.")
        _require(not result.get("proof_sources"), "Unproved result claims winning proof sources.")
        return False
    commands, trace = result.get("commands"), result.get("trace")
    _require(type(commands) is list and commands and all(type(c) is str for c in commands)
             and type(trace) is list and trace and type(trace[-1]) is dict,
             "Missing winning commands/native replay trace.")
    footer = trace[-1]
    steps = [row for row in trace if type(row) is dict and "tactic" in row]
    _require(result.get("goals") == [] and type(result.get("proof_nodes")) is int
             and result["proof_nodes"] > 0 and footer.get("qed") is True
             and footer.get("theorem") == theorem and footer.get("tactic_count") == len(commands)
             and footer.get("proof_size") == result["proof_nodes"] and len(steps) == len(commands)
             and all(row.get("status") == "ok" and row.get("error") is None for row in steps),
             "Missing exact original-theorem native QED/step accounting.")
    sources = result.get("proof_sources")
    _require(type(sources) is dict and all(_count(v) for v in sources.values())
             and sum(sources.values()) == len(commands), "Winning proof source accounting differs.")
    if phase == "sequential":
        replay = search.get("replay_evidence", {})
        _require(search.get("independent_replay") is True and replay.get("status") == "completed"
                 and type(replay.get("actual_exit_code")) is int and replay["actual_exit_code"] == 0
                 and type(replay.get("child_process_id")) is int and replay["child_process_id"] > 0
                 and set(sources) == {"model"}, "Missing independent model-proof replay evidence.")
    else:
        _require(not sources.get("model"), "Symbolic winning proof credits a model step.")
    return True


def run_portfolio(request, cancel, on_progress=lambda _: None, *, run_worker, clock=time.monotonic):
    """Run the exact public Sequential then Standard Symbolic worker profiles.

`run_worker(mode, request, cancel, progress)` must implement the server's owned
process and cleanup contract. The fixed worker ceilings total 540 seconds;
10 seconds remain for coordination. A fallback is never started without its
full 180-second allowance. Deadline/cancellation suppress every proof result.
"""
    started = clock()
    phases = []
    primary = None
    fallback = {"status": "not_started", "reason": None}
    callback_active = False

    def finish(result=None, error=None):
        elapsed = clock() - started
        quiescent = not callback_active and all(p["execution"]["quiescent"] is True for p in phases)
        cancelled = cancel.is_set() or any(p["execution"]["cancelled"] is True for p in phases)
        if not _number(elapsed) or elapsed >= WALL_SECONDS:
            error = "Portfolio exceeded its whole wall-time limit."
        if not quiescent:
            error = "Portfolio worker cleanup could not be confirmed."
        if cancelled or error is not None:
            result = None
        if result is not None:
            try:
                encoded = json.dumps(result, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()
                if len(encoded) > MAX_RESULT_BYTES:
                    error, result = "Portfolio result exceeds its 8 MiB output bound.", None
            except (TypeError, ValueError):
                error, result = "Portfolio result is not finite JSON.", None
        elapsed = clock() - started
        cancelled = cancelled or cancel.is_set()
        if elapsed >= WALL_SECONDS:
            error, result = "Portfolio exceeded its whole wall-time limit.", None
        if cancelled:
            result = None
        return {"result": result, "error": None if cancelled and quiescent else error,
                "cancelled": bool(cancelled and quiescent), "elapsed_seconds": elapsed,
                "peak_sampled_rss_bytes": max((p["execution"].get("peak_sampled_rss_bytes", 0) for p in phases), default=0),
                "peak_sampled_solver_rss_bytes": max((p["execution"].get("peak_sampled_solver_rss_bytes", 0) for p in phases), default=0),
                "quiescent": quiescent, "worker_started": callback_active or any(p["execution"]["worker_started"] for p in phases),
                "worker_exit_code": None, "portfolio_phases": copy.deepcopy(phases)}

    def invoke(phase, phase_request):
        nonlocal callback_active
        on_progress({"phase": "portfolio", "portfolio_phase": phase,
                     "message": "Starting selected model from the original theorem." if phase == "sequential"
                     else "Model attempt unresolved; starting fresh native heuristics and Vampire."})
        if cancel.is_set():
            return None
        def progress(event):
            if not cancel.is_set():
                update = {**event, "portfolio_phase": phase}
                if phase == "symbolic" and _count(update.get("model_calls")):
                    update["model_calls"] += primary["search"]["model_calls"]
                on_progress(update)
        callback_active = True
        outcome = run_worker("search", phase_request, cancel, progress)
        _validate_execution(outcome, phase)
        phases.append(_summary(phase, phase_request, outcome))
        callback_active = False
        return outcome

    def composed(winner=None):
        result = copy.deepcopy(winner if winner is not None else primary)
        winner_phase = None if winner is None else winner["kind"]
        search = result["search"]
        # The winner's provenance/trace stay unchanged. Aggregate work is not
        # interpreted as winning proof contribution.
        for key in SUM_COUNTERS:
            values = [p["search_counters"].get(key) for p in phases]
            if all(_count(v) for v in values):
                search[key] = sum(values)
            elif key in search:
                search[key] = None
        # The Symbolic route has no model at all, including when it fails
        # before returning diagnostics. Its failure must not erase measured
        # primary model work; unknown solver/search work stays explicitly null.
        search["model_calls"] = primary["search"]["model_calls"]
        search["forward_passes"] = primary["search"].get("forward_passes")
        search["generated_token_slots"] = primary["search"].get("generated_token_slots")
        search["wall_seconds"] = clock() - started
        search["model_loaded"] = primary["search"].get("model_loaded")
        search["portfolio_model_accepted_steps"] = primary["search"].get("accepted_model_steps")
        search["portfolio_model_repeated_state_guard"] = copy.deepcopy(primary["search"].get("repeated_state_guard"))
        search["search_mode"] = "portfolio"
        search["settings_profile"] = "portfolio"
        search["settings_policy"] = POLICY
        search["model_used"] = primary["search"]["model_calls"] > 0
        search["vampire_used"] = (
            any(p["search_counters"]["vampire_calls"] > 0 for p in phases)
            if all(_count(p["search_counters"].get("vampire_calls")) for p in phases) else None)
        search["diagnostic_scope"] = {
            "aggregate_fields": [*SUM_COUNTERS, "generated_token_slots", "wall_seconds",
                                 "model_loaded", "model_used", "vampire_used"],
            "model_phase_fields": ["portfolio_model_accepted_steps", "portfolio_model_repeated_state_guard"],
            "other_fields_phase": winner_phase or "sequential",
            "other_fields_are_aggregate": False,
            "detail": "Other diagnostics, including model_advisor_calls and generated_token_steps, "
                      "are retained from the winning phase, or the primary phase when unresolved; "
                      "they are not portfolio totals. Phase-local counters remain in portfolio.phases."}
        result.update(kind="portfolio", search_mode="portfolio", original_theorem=request["theorem"],
                      settings_profile="portfolio",
                      model=copy.deepcopy(primary.get("model")),
                      model_used=search["model_used"], vampire_used=search["vampire_used"])
        result["portfolio"] = {"policy": POLICY, "winner": winner_phase,
            "selected_model_id": request["model_id"], "original_theorem": request["theorem"],
            "canonical_theorem": primary["theorem"], "whole_wall_seconds": WALL_SECONDS,
            "phase_worker_wall_seconds": dict(PHASE_WALL_SECONDS),
            "phases": copy.deepcopy(phases), "fallback": dict(fallback),
            "component_accounting_complete": all(_count(p["search_counters"].get("vampire_calls")) for p in phases),
            "known_counter_lower_bounds": {key: sum(p["search_counters"].get(key, 0) for p in phases
                                                if _count(p["search_counters"].get(key))) for key in SUM_COUNTERS},
            "script_combination": False, "unresolved_is_not_disproof": True}
        if winner is None:
            result.update(status="unknown", kernel_checked=False, proof_sources={})
        return result

    try:
        _require(type(request) is dict and request.get("search_mode") == "portfolio"
                 and request.get("search_profile") == "portfolio" and request.get("max_model_calls") == 128
                 and type(request.get("max_model_calls")) is int and request.get("beam_width") == 1
                 and type(request.get("beam_width")) is int and not request.get("experimental")
                 and type(request.get("model_id")) is str and bool(request["model_id"])
                 and type(request.get("theorem")) is str and bool(request["theorem"]),
                 "Portfolio requires an explicit model and its fixed no-imports 128-call/one-trajectory profile.")
        if cancel.is_set():
            return finish()
        model_request = {"theorem": request["theorem"], "search_mode": "sequential",
                         "search_profile": "sequential", "max_model_calls": 128, "beam_width": 1,
                         "model_id": request["model_id"]}
        outcome = invoke("sequential", model_request)
        if outcome is None or cancel.is_set() or outcome["cancelled"]:
            return finish()
        if outcome["result"] is None or outcome["error"] is not None or not outcome["quiescent"]:
            return finish(error=outcome["error"] or "Sequential worker returned no valid result.")
        primary = outcome["result"]
        proved = _validate_result(primary, "sequential", request["theorem"])
        if proved:
            fallback.update(status="not_needed", reason="model_proof")
            return finish(composed(primary))
        # This metric is recorded by genuine native admission. Do not import or
        # modify the legacy parser merely to preflight an expanded formula.
        binders = primary["native_admission"].get("ast_metrics", {}).get("maximum_bound_variables")
        if _count(binders) and binders > 16:
            fallback.update(status="unavailable", reason="legacy_bound_variable_limit", maximum_bound_variables=binders)
            return finish(composed())
        if clock() - started + PHASE_WALL_SECONDS["symbolic"] >= WALL_SECONDS:
            fallback.update(status="not_started", reason="insufficient_whole_wall_budget")
            return finish(composed())
        symbolic_request = {"theorem": request["theorem"], "search_mode": "symbolic",
                            "search_profile": "standard", "max_model_calls": 16, "beam_width": 4}
        outcome = invoke("symbolic", symbolic_request)
        if outcome is None or cancel.is_set() or outcome["cancelled"]:
            return finish()
        if not outcome["quiescent"]:
            return finish(error="Symbolic worker cleanup could not be confirmed.")
        if outcome["result"] is None or outcome["error"] is not None:
            unavailable = (outcome["worker_started"] is True and type(outcome["worker_exit_code"]) is int
                           and outcome["worker_exit_code"] == 2 and outcome["error"] in ADMISSION_ERRORS)
            fallback.update(status="unavailable" if unavailable else "failed",
                            reason="legacy_input_admission" if unavailable else "symbolic_worker_failure",
                            error=outcome["error"] or "Symbolic worker returned no result.")
            return finish(composed())
        proved = _validate_result(outcome["result"], "symbolic", request["theorem"],
                                  primary["theorem"], primary["kernel_source_commit"])
        fallback.update(status="proved" if proved else "unknown", reason=None)
        return finish(composed(outcome["result"] if proved else None))
    except Exception as exc:
        return finish(error="Portfolio rejected execution: " + str(exc)[:1200])
