"""Bounded exact-goal memory for attempted polynomial decompositions.

This is finite-search heuristic pruning, not a completeness claim, proof, or
refutation. A key is the complete ordered native goal tuple, with all context
and literal names intact. Tactics and certificates are never stored or reused.

The caller must call remember_attempt only after validating a plan, checking
that it fits the remaining depth, and deciding to attempt it. Looking up a
state does not reserve or record an attempt. A shallower prefix remains eligible
until a valid attempt at that smaller depth is actually remembered.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json


DECOMPOSITION_MEMORY_POLICY = "hydra-exact-decomposition-attempt-memory-v1"
MAX_ENTRIES = 6
MAX_KEY_BYTES = 64 * 1024
MAX_TOTAL_BYTES = 512 * 1024
MAX_EVENTS = 64
MAX_ORDINAL = 2**63 - 1


def _ordinal(value, label):
    if type(value) is not int or not 0 <= value <= MAX_ORDINAL:
        raise ValueError(f"{label} must be a nonnegative bounded integer.")


def _encoded_key(goals):
    if type(goals) is not tuple or not goals:
        raise ValueError("Decomposition memory requires the complete nonempty native goal tuple.")
    # Reject an obviously oversized key before allocating its JSON encoding.
    # JSON needs two brackets, two quotes per goal and commas between goals.
    minimum_bytes = 1 + 3 * len(goals)
    if minimum_bytes > MAX_KEY_BYTES:
        return None
    for goal in goals:
        if type(goal) is not str:
            raise ValueError("Decomposition memory requires the complete nonempty native goal tuple.")
        minimum_bytes += len(goal)
        if minimum_bytes > MAX_KEY_BYTES:
            return None
    encoded = json.dumps(goals, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return encoded if len(encoded) <= MAX_KEY_BYTES else None


@dataclass(frozen=True, slots=True)
class AttemptReference:
    plan_id: int
    depth: int

    def to_dict(self):
        return {"plan_id": self.plan_id, "depth": self.depth}


@dataclass(frozen=True, slots=True)
class _Entry:
    reference: AttemptReference
    payload_bytes: int
    diagnostic_sha256: str


class DecompositionAttemptMemory:
    """One bounded ledger per search; no global or cross-search reuse."""
    def __init__(self):
        self._entries = {}
        self._bytes = 0
        self._events = []
        self._event_count = 0
        self._checks = 0
        self._hits = 0
        self._shallower_allowed = 0
        self._uncacheable_checks = 0
        self._remember_requests = 0
        self._recorded = 0
        self._shallower_replacements = 0
        self._redundant_remembers = 0
        self._declines = {"key_bytes": 0, "entries": 0, "total_bytes": 0}

    def _event(self, action, **details):
        self._event_count += 1
        if len(self._events) < MAX_EVENTS:
            self._events.append({"action": action, **details})

    def previously_attempted(self, goals, depth):
        """Return an earlier equal/shallower attempt, or None without recording."""
        _ordinal(depth, "Prefix depth")
        encoded = _encoded_key(goals)
        self._checks += 1
        if encoded is None:
            self._uncacheable_checks += 1
            return None
        # The actual dict key is the entire ordered tuple. Python resolves hash
        # collisions by exact tuple equality; the diagnostic SHA is never a key.
        entry = self._entries.get(goals)
        if entry is None:
            return None
        reference = entry.reference
        if depth < reference.depth:
            self._shallower_allowed += 1
            self._event("allow_shallower_prefix", previous_plan_id=reference.plan_id,
                        previous_depth=reference.depth, requested_depth=depth,
                        goals_sha256=entry.diagnostic_sha256)
            return None
        self._hits += 1
        self._event("skip_repeated_decomposition", previous_plan_id=reference.plan_id,
                    previous_depth=reference.depth, requested_depth=depth,
                    goals_sha256=entry.diagnostic_sha256)
        return reference

    def remember_attempt(self, goals, depth, plan_id):
        """Remember a validated, depth-fitting plan at the attempt boundary.

        Return True on insertion or a shallower replacement, False if already
        covered or a fixed retention bound declines it. This result is not a
        proof verdict and must not determine whether an otherwise valid new
        plan is executed. Full memory declines new entries without eviction.
        """
        _ordinal(depth, "Prefix depth")
        _ordinal(plan_id, "Plan ID")
        encoded = _encoded_key(goals)
        self._remember_requests += 1
        if encoded is None:
            self._declines["key_bytes"] += 1
            self._event("retention_declined", reason="key_bytes", plan_id=plan_id, depth=depth)
            return False
        entry = self._entries.get(goals)
        if entry is not None:
            if depth >= entry.reference.depth:
                self._redundant_remembers += 1
                return False
            previous = entry.reference
            reference = AttemptReference(plan_id, depth)
            self._entries[goals] = _Entry(reference, entry.payload_bytes, entry.diagnostic_sha256)
            self._recorded += 1
            self._shallower_replacements += 1
            self._event("remember_shallower_attempt", plan_id=plan_id, depth=depth,
                        previous_plan_id=previous.plan_id, previous_depth=previous.depth,
                        goals_sha256=entry.diagnostic_sha256)
            return True
        reason = "entries" if len(self._entries) >= MAX_ENTRIES else (
            "total_bytes" if self._bytes + len(encoded) > MAX_TOTAL_BYTES else None)
        if reason is not None:
            self._declines[reason] += 1
            self._event("retention_declined", reason=reason, plan_id=plan_id, depth=depth)
            return False
        diagnostic = hashlib.sha256(encoded).hexdigest()
        self._entries[goals] = _Entry(AttemptReference(plan_id, depth), len(encoded), diagnostic)
        self._bytes += len(encoded)
        self._recorded += 1
        self._event("remember_attempt", plan_id=plan_id, depth=depth, goals_sha256=diagnostic)
        return True

    def report(self):
        """Bounded metadata only; do not expose or duplicate cached goal text."""
        return {
            "policy": DECOMPOSITION_MEMORY_POLICY,
            "scope": "One search; exact full ordered goal tuple, including all context and names.",
            "pruning": "Heuristic; repeated equal/deeper prefixes may be skipped. No completeness claim.",
            "checks": self._checks,
            "repeated_decompositions_skipped": self._hits,
            "shallower_prefixes_allowed": self._shallower_allowed,
            "uncacheable_checks": self._uncacheable_checks,
            "remember_requests": self._remember_requests,
            "attempts_recorded": self._recorded,
            "shallower_replacements": self._shallower_replacements,
            "redundant_remembers_ignored": self._redundant_remembers,
            "retained_goal_states": len(self._entries),
            "retained_payload_bytes": self._bytes,
            "retained_bytes_unit": "UTF-8 JSON goal payload; excludes Python object overhead and small metadata.",
            "retention_declines": dict(self._declines),
            "limits": {"entries": MAX_ENTRIES, "key_bytes": MAX_KEY_BYTES,
                       "total_bytes": MAX_TOTAL_BYTES, "events": MAX_EVENTS},
            "events": [dict(event) for event in self._events],
            "events_omitted": self._event_count - len(self._events),
            "tactics_cached": False,
            "proofs_cached": False,
            "kernel_authority_changed": False,
        }
