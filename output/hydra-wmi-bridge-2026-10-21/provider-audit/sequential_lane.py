"""Isolated next-tactic loop. Not installed in Hydra; no model/native imports.

The host authenticates a loaded provider and the unchanged native runtime. It
must run each case in a process with a 300-second external watchdog; cooperative
checks here do not interrupt a blocked numerical/native call.
"""
from dataclasses import asdict, dataclass
import copy
import hashlib
import json
import math
import time

CURRENT_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
NO_IMPORT_ENVIRONMENTS = {
    "ac5efc6260bd7aa706ee02f943c30c8fa4acc413a1be246722b2163a21688a87",
    "8edaaffa8edf1f6d8b187ba3ada5e87c8219374ef556031afbc103948619b69f",
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def compact_prompt(goals):
    return "HA model-v3 library-prefix=247/247\n" + json.dumps(
        {"focus": 0, "goals": list(goals)}, ensure_ascii=False, separators=(",", ":")) + "\nTactic:"


@dataclass(frozen=True)
class Limits:
    max_actions: int = 128
    max_new_tokens: int = 128
    max_total_decision_tokens: int = 16384
    max_context_tokens: int = 6144
    wall_seconds: float = 300.0

    def __post_init__(self):
        for name, cap in (("max_actions", 128), ("max_new_tokens", 128),
                          ("max_total_decision_tokens", 16384), ("max_context_tokens", 6144)):
            require(type(getattr(self, name)) is int and 0 < getattr(self, name) <= cap, "Invalid " + name)
        require(type(self.wall_seconds) in (int, float) and math.isfinite(self.wall_seconds)
                and 0 < self.wall_seconds <= 300, "Invalid wall budget")


def _goals(value):
    require(type(value) in (list, tuple) and len(value) <= 64
            and all(type(g) is str and g.strip() for g in value)
            and sum(len(g.encode()) for g in value) <= 128 * 1024, "Invalid all-goal state")
    return tuple(value)


def provider_factory_from_loaded(loaded):
    """Reuse one authenticated loaded CandidatePolicy's model, not its counters.

    Works with the Oct20 Torch/MLX CandidatePolicy interface. Authentication and
    final source-custody checks remain with its existing host loader/finalizer.
    """
    require(loaded.kind == "latent_compact_v3", "Expected exact latent conditioning")

    def factory(*, deadline, max_new_tokens, max_context_tokens):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Sequential provider deadline")
        provider_limits = type(loaded.limits)(max_calls=1, max_new_tokens=max_new_tokens,
            max_total_decision_tokens=max_new_tokens, max_context_tokens=max_context_tokens,
            provider_seconds=min(30.0, remaining))
        fresh = type(loaded)(backend=loaded.backend, tokenizer=loaded.tokenizer,
            kind=loaded.kind, environment=loaded.environment, provenance=loaded.provenance,
            render_prompt=loaded.render_prompt, strict_generation=loaded.strict_generation,
            check_prompt_binding=loaded.check_prompt_binding, validate_tactic=loaded.validate_tactic,
            constraint_factory=loaded.constraint_factory, limits=provider_limits,
            should_stop=loaded.should_stop, deadline_monotonic=deadline)
        fresh.evaluation_identity.update(copy.deepcopy(loaded.evaluation_identity))
        fresh.evaluation_identity["limits"] = asdict(provider_limits)
        return fresh

    return factory


def validate_native_receipt(receipt, *, theorem, actions, expected_before, previous, identity, success_label,
                            expected_proof_nodes=None):
    """Pure receipt validation; session/request IDs are not proof transitions."""
    require(type(receipt) is dict and receipt.get("theorem") == theorem
            and receipt.get("classical") is False
            and receipt.get("environment_sha256") == identity["environment_sha256"], "Native binding differs")
    require(type(receipt.get("trace")) is list, "Missing native trace")
    trace = [row for row in receipt["trace"] if "v" in row]
    require(len(trace) == len(actions) and receipt.get("tactics_requested") == len(actions), "Native action accounting differs")
    fields = ("step", "goals_before", "focus", "tactic", "goals_after", "status", "error")
    require(len(previous) in (len(actions) - 1, len(actions)), "Invalid previously accepted prefix length")
    require(all(all(new.get(k) == old.get(k) for k in fields) for new, old in zip(trace, previous)),
            "A previously accepted native transition changed")
    last = trace[-1]
    require(_goals(last["goals_before"]) == expected_before and last.get("focus") == 0
            and last.get("step") == len(actions), "Native action did not consume the exact all-goal input")
    goals = _goals(receipt["goals"])
    require(goals == _goals(last["goals_after"]), "Remaining native goals differ")
    if last.get("status") != "ok":
        require(receipt.get("kernel_checked") is False, "Failed action claims a proof")
        return trace, goals, False
    require(all(row.get("tactic") == success_label(action) and row.get("status") == "ok"
                and row.get("error") is None for row, action in zip(trace, actions))
            and receipt.get("tactics_applied") == len(actions) and receipt.get("failed_tactics") == 0,
            "Successful native actions are not bound to literal dispatch")
    completed = receipt.get("status") == "proved"
    require(receipt.get("kernel_checked") is completed, "Native kernel/status mismatch")
    if completed:
        footer = receipt["trace"][-1]
        require(not goals and footer.get("qed") is True and footer.get("theorem") == theorem
                and footer.get("tactic_count") == len(actions)
                and receipt.get("error") is None and receipt.get("failed_step") is None
                and type(receipt.get("proof_nodes")) is int and receipt["proof_nodes"] > 0
                and footer.get("proof_size") == receipt["proof_nodes"], "Missing exact original-goal native QED/counters")
        if expected_proof_nodes is not None:
            require(receipt["proof_nodes"] == expected_proof_nodes, "Independent certificate node count differs")
    else:
        require(receipt.get("status") in {"open", "kernel_rejection"} and goals, "Invalid open native result")
    return trace, goals, completed


def run(theorem, *, native, provider_factory, limits=Limits(), saved_fixture=False, clock=time.monotonic):
    """Follow one model trajectory from the original root without heuristics.

    native.identity binds source_commit, environment_sha256, allowed_theorems,
    and classical. native.initial(theorem, deadline=...) returns all goal strings.
    native.run_prefix(theorem, actions, deadline=...) returns an unchanged native
    batch result dict. native.independent_replay(...) uses a fresh native process
    and returns the same shape. Both must enforce the host's admission/trace cap.
    native.success_label(action) is the current authenticated surface function.

    provider_factory(deadline=..., max_new_tokens=..., max_context_tokens=...)
    returns one fresh CandidatePolicy sharing the already loaded model. This
    keeps its existing <=30s per-provider bound while the lane owns global work.
    No gold actions/state are passed to a real provider.

    saved_fixture=True is exclusively a file-only wiring fixture: it can never
    return proved=True, never claims new model work and never calls native replay.
    """
    require(type(theorem) is str and theorem.strip(), "Missing original theorem")
    require(type(saved_fixture) is bool, "Invalid fixture flag")
    identity = copy.deepcopy(native.identity)
    if not saved_fixture:
        require(identity.get("source_commit") == CURRENT_COMMIT
                and identity.get("environment_sha256") in NO_IMPORT_ENVIRONMENTS
                and identity.get("allowed_theorems") == [] and identity.get("classical") is False,
                "Current unchanged native no-import authority required")
    started = clock()
    deadline = started + limits.wall_seconds
    result = {"schema": "hydra-isolated-sequential-lane-v1", "status": "started", "proved": False,
              "evidence_kind": "saved_prediction_and_transition_fixture" if saved_fixture else "fresh_inference",
              "native_identity": identity, "theorem": theorem, "limits": asdict(limits),
              "actions": [], "steps": [], "actual_model_calls": 0, "actual_decision_tokens": 0,
              "saved_fixture_decision_tokens": 0, "search_branches": 1, "heuristic_actions": 0}
    previous = []
    consumed = 0

    def deadline_check():
        if clock() >= deadline:
            raise TimeoutError("Sequential case deadline")

    def validate_native(receipt, actions, expected_before):
        return validate_native_receipt(receipt, theorem=theorem, actions=actions, expected_before=expected_before,
            previous=previous, identity=identity, success_label=native.success_label)

    try:
        deadline_check()
        goals = _goals(native.initial(theorem, deadline=deadline))
        require(goals, "Initial state is unexpectedly empty")
        result["initial_goals"] = list(goals)
        for _index in range(limits.max_actions):
            deadline_check()
            remaining = limits.max_total_decision_tokens - consumed
            if remaining <= 0:
                result["status"] = "token_budget"
                break
            cap = min(limits.max_new_tokens, remaining)
            prompt = compact_prompt(goals)
            prompt_sha = hashlib.sha256(prompt.encode()).hexdigest()
            step = {"index": len(result["steps"]) + 1, "goals_before": list(goals), "prompt_sha256": prompt_sha}
            result["steps"].append(step)
            policy = provider_factory(deadline=deadline, max_new_tokens=cap, max_context_tokens=limits.max_context_tokens)
            try:
                candidates = policy.propose(goals, max_candidates=1)
            finally:
                report = policy.report()
                step["provider"] = report
                calls, tokens = report["actual_model_calls"], report["generated_token_slots"]
                require(type(calls) is int and calls in (0, 1) and type(tokens) is int and 0 <= tokens <= cap,
                        "Provider work exceeded its one-call budget")
                result["actual_model_calls"] += calls
                result["actual_decision_tokens"] += tokens
            deadline_check()
            require(type(candidates) is tuple and len(candidates) <= 1, "Expected at most one literal next tactic")
            if saved_fixture:
                require(calls == tokens == 0 and report.get("fixture") is True, "Fixture invented fresh inference")
                used = report["saved_fixture_decision_tokens"]
                require(type(used) is int and 0 < used <= cap, "Invalid retained fixture decisions")
                result["saved_fixture_decision_tokens"] += used
            else:
                used = tokens
                if candidates:
                    require(calls == 1 and tokens > 0, "Candidate has no actual inference")
            consumed += used
            if not candidates:
                result["status"] = "no_candidate"
                break
            action = candidates[0]
            require(type(action) is str and action and action == action.strip() and len(action.encode()) <= 512
                    and not any(ord(c) < 32 for c in action) and action.split()[0] != "use", "Invalid literal tactic")
            attempts = report["attempts"]
            require(len(attempts) == 1 and attempts[0]["prompt_sha256"] == prompt_sha, "Provider prompt differs")
            result["actions"].append(action)
            step["action"] = action
            receipt = native.run_prefix(theorem, tuple(result["actions"]), deadline=deadline)
            trace, next_goals, completed = validate_native(receipt, result["actions"], goals)
            step.update(native_status=receipt["status"], goals_after=list(next_goals))
            deadline_check()
            if trace[-1]["status"] != "ok" or receipt["status"] == "kernel_rejection":
                result["status"] = receipt["status"]
                break
            previous, goals = copy.deepcopy(trace), next_goals
            if completed:
                if saved_fixture:
                    result["status"] = "saved_fixture_complete"
                else:
                    replay = native.independent_replay(theorem, tuple(result["actions"]), deadline=deadline)
                    _trace, _goals_after, replay_complete = validate_native_receipt(replay,
                        theorem=theorem, actions=result["actions"], expected_before=tuple(trace[-1]["goals_before"]),
                        previous=previous, identity=identity, success_label=native.success_label,
                        expected_proof_nodes=receipt["proof_nodes"])
                    deadline_check()
                    # validate_native already checks every transition against
                    # previous. Separate processes may have different session IDs.
                    require(replay_complete, "Independent native replay differs")
                    result.update(status="proved", proved=True, independent_replay=replay)
                break
        else:
            result["status"] = "action_budget"
        result["remaining_goals"] = list(goals)
    except TimeoutError as error:
        result.update(status="deadline", error=str(error), proved=False)
    except Exception as error:
        result.update(status="error", error_type=type(error).__name__, error=str(error), proved=False)
    finally:
        result["wall_seconds"] = clock() - started
    return result
