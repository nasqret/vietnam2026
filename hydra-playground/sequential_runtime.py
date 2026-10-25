"""HTTP-worker adapter for explicit sequential model inference and native replay."""
from __future__ import annotations

import time

import worker
from sequential_native import NativeHost
from sequential_runner import Limits, run
from deployment_models import create_policy, resolve_model_id
from sequential_cycle_guard import wrap_factory


def replay(request):
    deadline = time.monotonic() + 100
    native = NativeHost(worker.SOURCE)
    admission = native.admit(request["theorem"], deadline=deadline)
    theorem = admission["theorem"]
    actions = request["tactics"]
    if actions:
        result = native.run_prefix(theorem, actions, deadline=deadline)
    else:
        goals = list(native.initial(theorem, deadline=deadline))
        result = {"status": "open", "theorem": theorem, "goals": goals, "initial_goals": goals,
                  "kernel_checked": False, "proof_nodes": None, "trace": [], "mode": "initial-state",
                  "tactics_requested": 0, "tactics_applied": 0, "engine_steps": 0,
                  "classical": False, "error": None}
    native.verify_sources()
    result.update(kind="manual", original_theorem=request["theorem"], commands=actions,
                  kernel_source_commit=worker.SOURCE_COMMIT, model_used=False,
                  proof_profile="sequential", native_admission=admission)
    return result


def run_search(request, progress):
    started = time.monotonic()
    native = NativeHost(worker.SOURCE)
    admission = native.admit(request["theorem"], deadline=started + 300)
    theorem = admission["theorem"]
    model_id = resolve_model_id(request.get("model_id"))
    policy = create_policy(model_id, native.capabilities, progress,
                           deadline_monotonic=started + 300,
                           max_calls=request["max_model_calls"])
    limits = Limits(max_actions=request["max_model_calls"], wall_seconds=max(0.001, 300 - (time.monotonic() - started)))
    def step_progress(event):
        progress({"phase": "native", "message": "Checked the latest model tactic against all outstanding goals.",
                  "model_calls": event.get("actual_model_calls"), "tactic_attempts": event.get("step")})

    cycle_guard = wrap_factory(policy.provider_factory)
    outcome = run(theorem, native=native, provider_factory=cycle_guard,
                  prompt_renderer=policy.prompt_renderer, limits=limits, progress=step_progress)
    # A changed source or adapter invalidates the entire request, even after QED.
    accounting = policy.finalize()
    native.verify_sources()
    proved = outcome.get("proved") is True
    native_result = outcome.get("independent_replay") if proved else outcome.get("last_native_result")
    result = dict(native_result or {"theorem": theorem, "trace": [], "proof_nodes": None,
                  "goals": outcome.get("remaining_goals", outcome.get("initial_goals", [])),
                  "initial_goals": outcome.get("initial_goals", []), "classical": False})
    result.update(status="proved" if proved else "unknown", kernel_checked=proved,
                  kind="sequential", theorem=theorem, original_theorem=request["theorem"],
                  commands=outcome["actions"], kernel_source_commit=worker.SOURCE_COMMIT,
                  model_used=outcome["actual_model_calls"] > 0, vampire_used=False,
                  model=dict(policy.identity), proof_sources={"model": len(outcome["provenance"])} if proved else {},
                  proof_profile="sequential", native_admission=admission)
    result["search"] = {"model_calls": outcome["actual_model_calls"], "vampire_calls": 0,
        "states_expanded": len(outcome["steps"]), "tactic_attempts": len(outcome["actions"]),
        "model_loaded": accounting.get("model_loaded", policy.policy is not None),
        "generated_token_slots": outcome["actual_decision_tokens"],
        "forward_passes": accounting.get("forward_passes"),
        "wall_seconds": time.monotonic() - started, "stop_reason": outcome["status"],
        "error": outcome.get("error"), "limits": outcome["limits"],
        "independent_replay": proved, "replay_evidence": native.last_replay_evidence,
        "accepted_model_steps": len(outcome["provenance"]),
        "provenance": [{**row,
                        "reason": "Fresh model tactic accepted against the complete native goal state."}
                       for row in outcome["provenance"]],
        "provider_attempts": accounting.get("attempts", []),
        "tokenizer_runtime": accounting.get("tokenizer_runtime"),
        "repeated_state_guard": cycle_guard.report(),
        "native_identity": native.identity}
    return result
