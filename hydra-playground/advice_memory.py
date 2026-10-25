"""Bounded exact-goal memory for suppressing redundant model decoding.

This ledger stores no tactics or proof certificates. It is local to one search
with one fixed model provider. All goals, their literal names, and their order
are part of the key; no alpha renaming, context pruning or digest-only equality
is used. A hit is a finite-search scheduling choice, never a proof or refutation.
"""
from __future__ import annotations

import hashlib
import json


MODEL_ADVICE_MEMORY_POLICY = "hydra-exact-model-goals-memory-v1"
MAX_ENTRIES = 128
MAX_TOTAL_BYTES = 512 * 1024
MAX_ENTRY_BYTES = 64 * 1024
MAX_EVENTS = 64


def _encoded(goals):
    if type(goals) is not tuple or not goals or any(type(goal) is not str for goal in goals):
        raise ValueError("Model advice memory requires the complete native goal tuple.")
    return json.dumps(goals, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


class ModelAdviceMemory:
    def __init__(self):
        self._decoded = {}
        self._bytes = 0
        self.checks = 0
        self.hits = 0
        self.declined = 0
        self.events = []

    def previously_decoded(self, goals):
        # A cache key is always the exact tuple itself, not its displayed hash.
        _encoded(goals)
        self.checks += 1
        call = self._decoded.get(goals)
        if call is not None:
            self.hits += 1
            if len(self.events) < MAX_EVENTS:
                raw = _encoded(goals)
                self.events.append({"previous_model_call": call,
                                    "goals_sha256": hashlib.sha256(raw).hexdigest(),
                                    "action": "skip_repeated_decode",
                                    "tactics_reused": False})
        return call

    def remember_decoded(self, goals, model_call):
        if type(model_call) is not int or model_call < 1:
            raise ValueError("Only an actual earlier model call may enter advice memory.")
        raw = _encoded(goals)
        if goals in self._decoded:
            return
        if len(self._decoded) >= MAX_ENTRIES or len(raw) > MAX_ENTRY_BYTES \
                or self._bytes + len(raw) > MAX_TOTAL_BYTES:
            self.declined += 1
            return
        self._decoded[goals] = model_call
        self._bytes += len(raw)

    def report(self):
        return {"policy": MODEL_ADVICE_MEMORY_POLICY,
                "scope": "One search; exact full ordered goal tuple; one fixed model provider.",
                "checks": self.checks, "repeated_prompts_skipped": self.hits,
                "retained_prompts": len(self._decoded), "retained_bytes": self._bytes,
                "retained_bytes_unit": "UTF-8 JSON goal payload; excludes Python object overhead.",
                "previous_model_call_unit": "One-based actual forward-pass batch count, not provider decode-attempt ordinal.",
                "retention_declines": self.declined,
                "limits": {"entries": MAX_ENTRIES, "total_bytes": MAX_TOTAL_BYTES,
                           "entry_bytes": MAX_ENTRY_BYTES, "events": MAX_EVENTS},
                "events": list(self.events), "events_omitted": self.hits - len(self.events),
                "tactics_reused": False, "kernel_authority_changed": False}
