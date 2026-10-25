"""Request-local repeated-state heuristic for the web sequential lane.

Wrap a provider factory once per request, never once per loaded model. Exact
ordered printed goals are the key: no renaming, whitespace normalization, or
dropping other branches. Equality of these strings is a conservative reason to
stop this search, not evidence that the theorem is false or hidden native state
cannot have changed. This module does not participate in matched comparisons.

The wrapped provider remains the sole source of model work and accounting.
On a repeated state, even constructing that provider is skipped. The sealed
runner consequently returns ``no_candidate``; ``guard.report()`` supplies the
more specific ``repeated_state`` telemetry without changing proof authority.
"""
from __future__ import annotations

import copy
import hashlib
import json


def _no_work():
    return {"actual_model_calls": 0, "generated_token_slots": 0,
            "forward_attempts": 0, "forward_passes": 0,
            "attempts": [], "kernel_checked": False}


def _state_key(goals):
    if type(goals) not in (tuple, list) or not goals or any(type(g) is not str or not g for g in goals):
        raise TypeError("The repeated-state guard requires all ordered, nonempty goal strings.")
    return tuple(goals)


class _GuardedStep:
    def __init__(self, guard, args, kwargs):
        self._guard, self._args, self._kwargs = guard, args, kwargs
        self._attempted = False
        self._provider = None
        self._repeat = None

    def propose(self, goals_before, *, max_candidates):
        if self._attempted:
            raise RuntimeError("A guarded one-step provider cannot be reused.")
        self._attempted = True
        key = _state_key(goals_before)
        guard = self._guard
        guard._visits += 1
        if key in guard._seen:
            self._repeat = {"stop_reason": "repeated_state",
                "first_visit": guard._seen[key], "repeated_visit": guard._visits,
                "goal_count": len(key),
                "ordered_goals_sha256": hashlib.sha256(json.dumps(
                    list(key), ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()}
            guard._repeats.append(copy.deepcopy(self._repeat))
            return ()
        guard._seen[key] = guard._visits
        guard._delegated += 1
        self._provider = guard._factory(*self._args, **self._kwargs)
        # Preserve the exact input object, options, candidate and report behavior
        # of the authenticated provider on every first visit.
        return self._provider.propose(goals_before, max_candidates=max_candidates)

    def report(self):
        if self._provider is not None:
            return self._provider.report()
        report = _no_work()
        if self._repeat is not None:
            report["stop_reason"] = "repeated_state"
            report["repeated_state_guard"] = copy.deepcopy(self._repeat)
        return report


class RepeatedStateFactory:
    """Single-request, single-thread factory; the caller still owns all limits."""
    def __init__(self, factory):
        if not callable(factory):
            raise TypeError("A callable provider factory is required.")
        self._factory = factory
        self._seen = {}
        self._visits = self._delegated = 0
        self._repeats = []

    def __call__(self, *args, **kwargs):
        # Provider construction can load or mutate accounting, so defer it until
        # we have the goals and know this request is not a repeated-state stop.
        return _GuardedStep(self, args, kwargs)

    def report(self):
        return {"schema": "hydra-web-repeated-state-guard-v1", "enabled": True,
            "scope": "one web request", "heuristic": "exact ordered printed goals",
            "is_disproof": False, "comparison_policy_changed": False,
            "visits": self._visits, "distinct_states": len(self._seen),
            "delegated_provider_requests": self._delegated,
            "blocked_provider_requests": len(self._repeats),
            "stop_reason": "repeated_state" if self._repeats else None,
            "repeats": copy.deepcopy(self._repeats)}


def wrap_factory(factory):
    """Return a fresh callable guard with report(); retain original finalizer."""
    return RepeatedStateFactory(factory)
