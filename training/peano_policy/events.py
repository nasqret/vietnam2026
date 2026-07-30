"""Deterministic, observational events for live Peano policy search.

The event stream is deliberately separate from proof authority.  Records
contain only inert text, counters, and digests; they never expose a mutable
proof session, a model tensor, or a certificate.  Event sinks are synchronous
so a terminal can display model generation and verifier feedback in the order
in which they happen.

Every record has ``v=1`` and one of the following exact payload schemas::

    search_started
      theorem, root_state_sha256, goals, limits
    state_selected
      model_call, depth, frontier_size, frontier_rank, state_sha256,
      path, goals_before, max_candidates
    model_prompt
      model_call, state_sha256, goals_before, prompt, prompt_chars,
      call_seed, requested_candidates, decoding
    model_output
      model_call, state_sha256, raw_candidates, candidates, rejections
    model_error
      model_call, state_sha256, error_type, message
    proposal_received
      model_call, depth, state_sha256, candidates, returned, authorized,
      truncated
    policy_error
      model_call, depth, state_sha256, message
    candidate_started
      model_call, depth, state_sha256, candidate_rank, command, path,
      goals_before, replay_commands
    candidate_result
      model_call, depth, state_sha256, candidate_rank, command, path,
      goals_before, status, error_kind, message, failed_index, goals_after,
      successor_state_sha256, disposition
    frontier_updated
      depth, frontier_size, frontier_peak, beam_width, pruned,
      state_sha256s
    kernel_check_started
      depth, state_sha256, command, path
    kernel_check_finished
      depth, state_sha256, command, path, status, certificate_nodes, message
    independent_replay_started
      theorem, path
    independent_replay_finished
      status, kernel_checked, proof_nodes, message
    search_finished
      status, commands, certificate_nodes, model_calls, states_expanded,
      states_discovered, candidates_executed, frontier_peak, depth_reached

Candidate and frontier ranks are zero-based.  ``model_call`` is one-based.
``failed_index`` is a zero-based index into ``path`` or ``None``.  Tuples are
used for ordered collections so a sink cannot mutate search-owned containers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
import hashlib
import json
from typing import Literal, TypeAlias


EVENT_VERSION = 1
PolicyEventKind = Literal[
    "search_started",
    "state_selected",
    "model_prompt",
    "model_output",
    "model_error",
    "proposal_received",
    "policy_error",
    "candidate_started",
    "candidate_result",
    "frontier_updated",
    "kernel_check_started",
    "kernel_check_finished",
    "independent_replay_started",
    "independent_replay_finished",
    "search_finished",
]
PolicyEvent: TypeAlias = Mapping[str, object]
EventSink: TypeAlias = Callable[[PolicyEvent], object]


class EventSinkError(RuntimeError):
    """An observational sink failed while consuming a live event."""


EVENT_FIELDS: Mapping[PolicyEventKind, tuple[str, ...]] = {
    "search_started": (
        "theorem",
        "root_state_sha256",
        "goals",
        "limits",
    ),
    "state_selected": (
        "model_call",
        "depth",
        "frontier_size",
        "frontier_rank",
        "state_sha256",
        "path",
        "goals_before",
        "max_candidates",
    ),
    "model_prompt": (
        "model_call",
        "state_sha256",
        "goals_before",
        "prompt",
        "prompt_chars",
        "call_seed",
        "requested_candidates",
        "decoding",
    ),
    "model_output": (
        "model_call",
        "state_sha256",
        "raw_candidates",
        "candidates",
        "rejections",
    ),
    "model_error": (
        "model_call",
        "state_sha256",
        "error_type",
        "message",
    ),
    "proposal_received": (
        "model_call",
        "depth",
        "state_sha256",
        "candidates",
        "returned",
        "authorized",
        "truncated",
    ),
    "policy_error": (
        "model_call",
        "depth",
        "state_sha256",
        "message",
    ),
    "candidate_started": (
        "model_call",
        "depth",
        "state_sha256",
        "candidate_rank",
        "command",
        "path",
        "goals_before",
        "replay_commands",
    ),
    "candidate_result": (
        "model_call",
        "depth",
        "state_sha256",
        "candidate_rank",
        "command",
        "path",
        "goals_before",
        "status",
        "error_kind",
        "message",
        "failed_index",
        "goals_after",
        "successor_state_sha256",
        "disposition",
    ),
    "frontier_updated": (
        "depth",
        "frontier_size",
        "frontier_peak",
        "beam_width",
        "pruned",
        "state_sha256s",
    ),
    "kernel_check_started": (
        "depth",
        "state_sha256",
        "command",
        "path",
    ),
    "kernel_check_finished": (
        "depth",
        "state_sha256",
        "command",
        "path",
        "status",
        "certificate_nodes",
        "message",
    ),
    "independent_replay_started": (
        "theorem",
        "path",
    ),
    "independent_replay_finished": (
        "status",
        "kernel_checked",
        "proof_nodes",
        "message",
    ),
    "search_finished": (
        "status",
        "commands",
        "certificate_nodes",
        "model_calls",
        "states_expanded",
        "states_discovered",
        "candidates_executed",
        "frontier_peak",
        "depth_reached",
    ),
}


def canonical_state_sha256(goals: Sequence[str]) -> str:
    """Hash the exact canonical goal tuple used by search diagnostics."""

    canonical = tuple(goals)
    if not canonical or not all(type(goal) is str for goal in canonical):
        raise ValueError("canonical goals must be a non-empty text sequence")
    payload = json.dumps(
        list(canonical),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def emit_event(
    sink: EventSink | None,
    kind: PolicyEventKind,
    /,
    **payload: object,
) -> None:
    """Emit one exact-schema record, wrapping ordinary sink failures.

    ``KeyboardInterrupt`` and other ``BaseException`` subclasses deliberately
    pass through.  An ordinary sink exception is wrapped so policy-search
    error handling cannot mistake a broken observer for a model failure.
    """

    if sink is None:
        return
    expected = EVENT_FIELDS[kind]
    if tuple(payload) != expected:
        raise RuntimeError(
            f"event {kind!r} needs fields {expected!r}, got {tuple(payload)!r}"
        )
    record: dict[str, object] = {"v": EVENT_VERSION, "kind": kind}
    record.update(payload)
    try:
        sink(record)
    except EventSinkError:
        raise
    except Exception as exc:
        raise EventSinkError(f"event sink failed while handling {kind}") from exc


__all__ = [
    "EVENT_FIELDS",
    "EVENT_VERSION",
    "EventSink",
    "EventSinkError",
    "PolicyEvent",
    "PolicyEventKind",
    "canonical_state_sha256",
    "emit_event",
]
