"""Bounded verifier-guided search over Peano Lab's public tactic surface.

The policy used here is deliberately untrusted.  It sees only canonical goal
text and returns a ranked tuple of complete tactic lines.  This module does
not inspect or construct proof terms itself: every edge is replayed through
``run_surface`` with an explicit capability object, and a result is published
only after ``checked_surface_final`` checks the certificate against the
independently retained original theorem.

Search nodes contain inert command tuples rather than mutable sessions.  Each
candidate edge is replayed from the root in a fresh ``ProofSession``.  Besides
making failed siblings transactional, this avoids sharing a ``TraceLogger``
or another branch-local owner across the frontier.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol, runtime_checkable
import unicodedata

from peano_lab.engine.state import proof_size, start
from peano_lab.engine.tactics import (
    InvalidProof,
    TacticError,
    TacticLimit,
    TacticSyntaxError,
)
from peano_lab.engine.trace import TraceLogger, render_goals
from peano_lab.kernel.formulas import (
    Formula,
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import (
    MAX_INPUT,
    ProofSession,
    SurfaceCapabilities,
    checked_surface_final,
    oversized_numeral,
    run_surface,
)

from .events import (
    EventSink,
    EventSinkError,
    canonical_state_sha256,
    emit_event,
)


MAX_SEARCH_DEPTH = 32
MAX_DIAGNOSTIC_CHARS = 1_000
SearchStatus = Literal["proof", "exhausted", "limit"]


@runtime_checkable
class CandidatePolicy(Protocol):
    """An untrusted ranked next-tactic policy.

    ``goals_before`` is the canonical, ANSI-free rendering of the complete
    proof state.  The result must be an exact tuple so the host can bound it
    without consuming a lazy or infinite model stream.  Earlier entries are
    preferred when the beam must discard otherwise valid successors.
    """

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        """Return ranked complete Peano Lab tactic lines for this state."""


@runtime_checkable
class EventfulCandidatePolicy(Protocol):
    """Optional extension that reports the exact physical model call.

    Keeping this separate from :class:`CandidatePolicy` preserves the public
    structural protocol for existing policies and model-free tests.
    """

    def propose_with_events(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
        on_event: EventSink,
    ) -> tuple[str, ...]:
        """Return ranked tactics while reporting prompt/decoder events."""


@dataclass(frozen=True, slots=True)
class SearchLimits:
    """Complete host-owned resource authority for one search."""

    max_depth: int = MAX_SEARCH_DEPTH
    beam_width: int = 16
    candidates_per_state: int = 8
    max_model_calls: int = 512
    max_states: int = 4_096

    def __post_init__(self) -> None:
        for field in (
            "max_depth",
            "beam_width",
            "candidates_per_state",
            "max_model_calls",
            "max_states",
        ):
            value = getattr(self, field)
            if type(value) is not int or value < 1:
                raise ValueError(f"{field} must be a positive integer")
        if self.max_depth > MAX_SEARCH_DEPTH:
            raise ValueError(
                f"max_depth may not exceed the sound search boundary of "
                f"{MAX_SEARCH_DEPTH}"
            )


@dataclass(frozen=True, slots=True)
class SearchDiagnostic:
    """One deterministic explanation for a rejected edge or exhausted bound."""

    kind: str
    depth: int
    state_sha256: str
    message: str
    command: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "depth": self.depth,
            "state_sha256": self.state_sha256,
            "command": self.command,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class SearchResult:
    """A checked proof or an exact account of a bounded unsuccessful search."""

    status: SearchStatus
    theorem: str
    commands: tuple[str, ...]
    certificate_nodes: int | None
    diagnostics: tuple[SearchDiagnostic, ...]
    model_calls: int
    states_expanded: int
    states_discovered: int
    candidates_executed: int
    frontier_peak: int
    depth_reached: int

    def __post_init__(self) -> None:
        if self.status == "proof":
            if not self.commands or self.certificate_nodes is None:
                raise ValueError("a proof result needs commands and certificate nodes")
        elif self.commands or self.certificate_nodes is not None:
            raise ValueError("an unsuccessful search cannot claim proof data")

    @property
    def proved(self) -> bool:
        return self.status == "proof"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "theorem": self.theorem,
            "commands": list(self.commands),
            "certificate_nodes": self.certificate_nodes,
            "diagnostics": [item.to_dict() for item in self.diagnostics],
            "model_calls": self.model_calls,
            "states_expanded": self.states_expanded,
            "states_discovered": self.states_discovered,
            "candidates_executed": self.candidates_executed,
            "frontier_peak": self.frontier_peak,
            "depth_reached": self.depth_reached,
        }


@dataclass(frozen=True, slots=True)
class _Node:
    commands: tuple[str, ...]
    goals: tuple[str, ...]
    state_sha256: str
    priority: tuple[object, ...]

    @property
    def depth(self) -> int:
        return len(self.commands)


def _one_line(value: BaseException | str) -> str:
    raw = " ".join(str(value).split()) or type(value).__name__
    return raw[:MAX_DIAGNOSTIC_CHARS]


def _state_sha256(goals: tuple[str, ...]) -> str:
    return canonical_state_sha256(goals)


def _canonical_goals(owner: ProofSession) -> tuple[str, ...]:
    # Passing no previous metavariable aliases deliberately canonicalizes each
    # independently replayed state by first occurrence rather than global IDs.
    return tuple(render_goals(owner.state))


def _node_priority(
    goals: tuple[str, ...],
    *,
    proposal_rank: int,
    parent_rank: int,
    commands: tuple[str, ...],
) -> tuple[object, ...]:
    """Prefer fewer/smaller obligations, then the policy's stable ranking."""

    return (
        len(goals),
        sum(len(goal) for goal in goals),
        proposal_rank,
        parent_rank,
        commands,
    )


def _validate_candidate(value: object) -> tuple[str | None, str | None]:
    if type(value) is not str:
        return None, "candidate is not tactic text"
    if not value:
        return None, "candidate is blank"
    if len(value) > MAX_INPUT:
        return None, f"candidate exceeds {MAX_INPUT} characters"
    if value != value.strip():
        return None, "candidate has outer whitespace"
    if value.splitlines() != [value]:
        return None, "candidate must be exactly one complete tactic line"
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        return None, "candidate contains an unsafe control or format character"
    oversized = oversized_numeral(value)
    if oversized is not None:
        return None, f"candidate contains resource-dangerous numeral {oversized}"
    head = value.split(maxsplit=1)[0]
    if head in {
        "?",
        "abort",
        "classical",
        "done",
        "exit",
        "finish",
        "help",
        "hint",
        "pa",
        "q",
        "qed",
        "quit",
        "script",
        "t",
        "tactics",
        "undo",
    } or value.startswith("compact_arith?"):
        return None, "candidate is a session command, not a proof tactic"
    return value, None


def _new_owner(
    target: Formula,
    names: tuple[str, ...],
    theorem_source: str,
    *,
    classical: bool,
    replay_id: int,
) -> ProofSession:
    return ProofSession(
        state=start(target, names),
        original_target=target,
        original_names=names,
        target_source=theorem_source,
        classical=classical,
        trace=TraceLogger(session_id=f"policy-search-replay-{replay_id}"),
    )


def _replay(
    target: Formula,
    names: tuple[str, ...],
    theorem_source: str,
    commands: tuple[str, ...],
    *,
    classical: bool,
    capabilities: SurfaceCapabilities,
    replay_id: int,
) -> tuple[ProofSession | None, int | None, BaseException | None]:
    """Replay one edge from the root; report the exact failing command index."""

    owner = _new_owner(
        target,
        names,
        theorem_source,
        classical=classical,
        replay_id=replay_id,
    )
    for index, command in enumerate(commands):
        try:
            owner = run_surface(
                owner,
                command,
                capabilities=capabilities,
                record_trace=False,
            )
        except Exception as exc:
            return None, index, exc
    return owner, None, None


def search(
    theorem: str,
    policy: CandidatePolicy,
    *,
    capabilities: SurfaceCapabilities,
    classical: bool = False,
    limits: SearchLimits = SearchLimits(),
    on_event: EventSink | None = None,
) -> SearchResult:
    """Search for and independently check one closed PA theorem.

    Depth counts policy-returned physical lines, not the number of primitive
    engine history entries hidden inside a tactical.  ``max_states`` counts
    the canonical root plus unique open successor states admitted before beam
    pruning; a terminal checked proof is not a frontier state.
    """

    if type(theorem) is not str or not theorem.strip():
        raise ValueError("theorem must be non-empty text")
    if theorem != theorem.strip() or theorem.splitlines() != [theorem]:
        raise ValueError("theorem must be exactly one line with no outer whitespace")
    if len(theorem) > MAX_INPUT:
        raise ValueError(f"theorem exceeds {MAX_INPUT} characters")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in theorem
    ):
        raise ValueError("theorem contains an unsafe control or format character")
    oversized = oversized_numeral(theorem)
    if oversized is not None:
        raise ValueError(f"theorem contains resource-dangerous numeral {oversized}")
    if type(classical) is not bool:
        raise TypeError("classical must be a Boolean")
    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be an exact SurfaceCapabilities value")
    if type(limits) is not SearchLimits:
        raise TypeError("limits must be an exact SearchLimits value")
    if on_event is not None and not callable(on_event):
        raise TypeError("on_event must be callable or None")
    if not isinstance(policy, CandidatePolicy):
        raise TypeError("policy must provide propose(goals_before, max_candidates=...)")

    try:
        target, names = parse_formula_with_names(theorem)
    except RecursionError:
        raise ValueError("theorem exceeded the parser recursion boundary") from None
    except (ParseError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid theorem: {_one_line(exc)}") from None
    if names:
        raise ValueError(
            "theorem must be closed; quantify free variables explicitly: "
            + ", ".join(names)
        )
    canonical_theorem = pretty_formula(target, list(names))

    root_owner = _new_owner(
        target,
        names,
        theorem,
        classical=classical,
        replay_id=0,
    )
    root_goals = _canonical_goals(root_owner)
    root_key = _state_sha256(root_goals)
    root = _Node((), root_goals, root_key, (len(root_goals), 0, 0, 0, ()))

    frontier = (root,)
    # The digest is diagnostic only.  Deduplication compares the complete
    # canonical render, so even a hypothetical hash collision loses no path.
    seen = {root_goals}
    diagnostics: list[SearchDiagnostic] = []
    model_calls = 0
    states_expanded = 0
    states_discovered = 1
    candidates_executed = 0
    frontier_peak = 1
    depth_reached = 0
    replay_id = 0
    limited = False

    emit_event(
        on_event,
        "search_started",
        theorem=canonical_theorem,
        root_state_sha256=root_key,
        goals=root_goals,
        limits={
            "max_depth": limits.max_depth,
            "beam_width": limits.beam_width,
            "candidates_per_state": limits.candidates_per_state,
            "max_model_calls": limits.max_model_calls,
            "max_states": limits.max_states,
        },
    )

    def diagnostic(
        kind: str,
        node: _Node,
        message: BaseException | str,
        command: str | None = None,
        *,
        depth: int | None = None,
    ) -> None:
        diagnostics.append(
            SearchDiagnostic(
                kind,
                node.depth if depth is None else depth,
                node.state_sha256,
                _one_line(message),
                command,
            )
        )

    def finished(result: SearchResult) -> SearchResult:
        emit_event(
            on_event,
            "search_finished",
            status=result.status,
            commands=result.commands,
            certificate_nodes=result.certificate_nodes,
            model_calls=result.model_calls,
            states_expanded=result.states_expanded,
            states_discovered=result.states_discovered,
            candidates_executed=result.candidates_executed,
            frontier_peak=result.frontier_peak,
            depth_reached=result.depth_reached,
        )
        return result

    def unsuccessful(status: SearchStatus) -> SearchResult:
        return finished(
            SearchResult(
                status,
                canonical_theorem,
                (),
                None,
                tuple(diagnostics),
                model_calls,
                states_expanded,
                states_discovered,
                candidates_executed,
                frontier_peak,
                depth_reached,
            )
        )

    for layer_index in range(limits.max_depth):
        next_nodes: dict[tuple[str, ...], _Node] = {}

        for parent_rank, node in enumerate(frontier):
            if model_calls >= limits.max_model_calls:
                limited = True
                diagnostic(
                    "model_call_limit",
                    node,
                    f"model-call limit reached ({limits.max_model_calls})",
                )
                return unsuccessful("limit")

            model_calls += 1
            states_expanded += 1
            emit_event(
                on_event,
                "state_selected",
                model_call=model_calls,
                depth=node.depth,
                frontier_size=len(frontier),
                frontier_rank=parent_rank,
                state_sha256=node.state_sha256,
                path=node.commands,
                goals_before=node.goals,
                max_candidates=limits.candidates_per_state,
            )
            try:
                if on_event is not None and isinstance(
                    policy, EventfulCandidatePolicy
                ):
                    proposed = policy.propose_with_events(
                        node.goals,
                        max_candidates=limits.candidates_per_state,
                        on_event=on_event,
                    )
                else:
                    proposed = policy.propose(
                        node.goals,
                        max_candidates=limits.candidates_per_state,
                    )
            except EventSinkError:
                raise
            except Exception as exc:
                # A decoder/runtime failure is not a mathematical exhaustion
                # of the authorized tactic frontier.  Classify the bounded
                # attempt as limited so the UI cannot imply that the model
                # successfully returned an empty search space.
                limited = True
                diagnostic("policy_error", node, exc)
                emit_event(
                    on_event,
                    "policy_error",
                    model_call=model_calls,
                    depth=node.depth,
                    state_sha256=node.state_sha256,
                    message=_one_line(exc),
                )
                continue
            if type(proposed) is not tuple:
                limited = True
                message = "policy result must be an exact tuple of tactic lines"
                diagnostic(
                    "policy_error",
                    node,
                    message,
                )
                emit_event(
                    on_event,
                    "policy_error",
                    model_call=model_calls,
                    depth=node.depth,
                    state_sha256=node.state_sha256,
                    message=message,
                )
                continue
            authorized = min(len(proposed), limits.candidates_per_state)
            emit_event(
                on_event,
                "proposal_received",
                model_call=model_calls,
                depth=node.depth,
                state_sha256=node.state_sha256,
                candidates=proposed[:authorized],
                returned=len(proposed),
                authorized=authorized,
                truncated=max(0, len(proposed) - authorized),
            )
            if len(proposed) > limits.candidates_per_state:
                limited = True
                diagnostic(
                    "candidate_limit",
                    node,
                    "policy returned "
                    f"{len(proposed)} candidates; only the first "
                    f"{limits.candidates_per_state} are authorized",
                )

            local_commands: set[str] = set()
            for proposal_rank, raw_command in enumerate(
                proposed[: limits.candidates_per_state]
            ):
                command, error = _validate_candidate(raw_command)
                if command is None:
                    message = error or "invalid candidate"
                    diagnostic(
                        "invalid_candidate",
                        node,
                        message,
                        depth=node.depth + 1,
                    )
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=raw_command if type(raw_command) is str else None,
                        path=node.commands,
                        goals_before=node.goals,
                        status="error",
                        error_kind="invalid_candidate",
                        message=message,
                        failed_index=None,
                        goals_after=node.goals,
                        successor_state_sha256=None,
                        disposition="rejected",
                    )
                    continue
                if command in local_commands:
                    message = "duplicate candidate at the same canonical state"
                    diagnostic(
                        "duplicate_candidate",
                        node,
                        message,
                        command,
                        depth=node.depth + 1,
                    )
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=command,
                        path=node.commands + (command,),
                        goals_before=node.goals,
                        status="error",
                        error_kind="duplicate_candidate",
                        message=message,
                        failed_index=None,
                        goals_after=node.goals,
                        successor_state_sha256=None,
                        disposition="rejected",
                    )
                    continue
                local_commands.add(command)
                path = node.commands + (command,)
                candidates_executed += 1
                replay_id += 1
                emit_event(
                    on_event,
                    "candidate_started",
                    model_call=model_calls,
                    depth=node.depth + 1,
                    state_sha256=node.state_sha256,
                    candidate_rank=proposal_rank,
                    command=command,
                    path=path,
                    goals_before=node.goals,
                    replay_commands=path,
                )
                owner, failed_index, replay_error = _replay(
                    target,
                    names,
                    theorem,
                    path,
                    classical=classical,
                    capabilities=capabilities,
                    replay_id=replay_id,
                )
                if owner is None:
                    assert failed_index is not None and replay_error is not None
                    prefix_failed = failed_index < len(path) - 1
                    if prefix_failed:
                        kind = "replay_error"
                        message = (
                            f"accepted prefix changed on fresh replay at command "
                            f"{failed_index + 1}: {_one_line(replay_error)}"
                        )
                    elif isinstance(replay_error, TacticLimit):
                        limited = True
                        kind = "tactic_limit"
                        message = replay_error
                    elif isinstance(replay_error, TacticSyntaxError):
                        kind = "surface_error"
                        message = replay_error
                    elif isinstance(replay_error, TacticError):
                        kind = "tactic_error"
                        message = replay_error
                    else:
                        kind = "surface_error"
                        message = replay_error
                    diagnostic(
                        kind,
                        node,
                        message,
                        command,
                        depth=node.depth + 1,
                    )
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=command,
                        path=path,
                        goals_before=node.goals,
                        status="error",
                        error_kind=kind,
                        message=_one_line(message),
                        failed_index=failed_index,
                        goals_after=node.goals,
                        successor_state_sha256=None,
                        disposition="rejected",
                    )
                    continue

                depth_reached = max(depth_reached, len(path))
                if owner.state.is_done():
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=command,
                        path=path,
                        goals_before=node.goals,
                        status="ok",
                        error_kind=None,
                        message=None,
                        failed_index=None,
                        goals_after=(),
                        successor_state_sha256=None,
                        disposition="closed_pending_kernel",
                    )
                    emit_event(
                        on_event,
                        "kernel_check_started",
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        command=command,
                        path=path,
                    )
                    try:
                        certificate = checked_surface_final(
                            owner.state,
                            target,
                            classical=classical,
                            trace=None,
                        )
                    except InvalidProof as exc:
                        diagnostic(
                            "kernel_rejection",
                            node,
                            exc,
                            command,
                            depth=node.depth + 1,
                        )
                        emit_event(
                            on_event,
                            "kernel_check_finished",
                            depth=node.depth + 1,
                            state_sha256=node.state_sha256,
                            command=command,
                            path=path,
                            status="rejected",
                            certificate_nodes=None,
                            message=_one_line(exc),
                        )
                        continue
                    certificate_nodes = proof_size(certificate)
                    emit_event(
                        on_event,
                        "kernel_check_finished",
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        command=command,
                        path=path,
                        status="accepted",
                        certificate_nodes=certificate_nodes,
                        message=None,
                    )
                    return finished(
                        SearchResult(
                            "proof",
                            canonical_theorem,
                            path,
                            certificate_nodes,
                            tuple(diagnostics),
                            model_calls,
                            states_expanded,
                            states_discovered,
                            candidates_executed,
                            frontier_peak,
                            depth_reached,
                        )
                    )

                goals = _canonical_goals(owner)
                key = _state_sha256(goals)
                successor = _Node(
                    path,
                    goals,
                    key,
                    _node_priority(
                        goals,
                        proposal_rank=proposal_rank,
                        parent_rank=parent_rank,
                        commands=path,
                    ),
                )
                if goals in seen:
                    existing = next_nodes.get(goals)
                    replaced = False
                    if existing is not None and successor.priority < existing.priority:
                        next_nodes[goals] = successor
                        replaced = True
                    message = "successor is a canonical state already discovered"
                    diagnostic(
                        "duplicate_state",
                        node,
                        message,
                        command,
                        depth=node.depth + 1,
                    )
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=command,
                        path=path,
                        goals_before=node.goals,
                        status="ok",
                        error_kind="duplicate_state",
                        message=message,
                        failed_index=None,
                        goals_after=goals,
                        successor_state_sha256=key,
                        disposition=(
                            "duplicate_replaced" if replaced else "duplicate_ignored"
                        ),
                    )
                    continue
                if states_discovered >= limits.max_states:
                    limited = True
                    message = f"state limit reached ({limits.max_states})"
                    diagnostic(
                        "state_limit",
                        node,
                        message,
                        command,
                        depth=node.depth + 1,
                    )
                    emit_event(
                        on_event,
                        "candidate_result",
                        model_call=model_calls,
                        depth=node.depth + 1,
                        state_sha256=node.state_sha256,
                        candidate_rank=proposal_rank,
                        command=command,
                        path=path,
                        goals_before=node.goals,
                        status="ok",
                        error_kind="state_limit",
                        message=message,
                        failed_index=None,
                        goals_after=goals,
                        successor_state_sha256=key,
                        disposition="state_limit",
                    )
                    continue
                seen.add(goals)
                states_discovered += 1
                next_nodes[goals] = successor
                emit_event(
                    on_event,
                    "candidate_result",
                    model_call=model_calls,
                    depth=node.depth + 1,
                    state_sha256=node.state_sha256,
                    candidate_rank=proposal_rank,
                    command=command,
                    path=path,
                    goals_before=node.goals,
                    status="ok",
                    error_kind=None,
                    message=None,
                    failed_index=None,
                    goals_after=goals,
                    successor_state_sha256=key,
                    disposition="admitted",
                )

        ordered = sorted(next_nodes.values(), key=lambda item: item.priority)
        pruned_count = 0
        if len(ordered) > limits.beam_width:
            limited = True
            kept = ordered[: limits.beam_width]
            pruned_count = len(ordered) - len(kept)
            for pruned in ordered[limits.beam_width :]:
                diagnostics.append(
                    SearchDiagnostic(
                        "beam_limit",
                        pruned.depth,
                        pruned.state_sha256,
                        _one_line(
                            f"successor pruned by beam width {limits.beam_width}"
                        ),
                        pruned.commands[-1],
                    )
                )
            ordered = kept
        frontier = tuple(ordered)
        frontier_peak = max(frontier_peak, len(frontier))
        emit_event(
            on_event,
            "frontier_updated",
            depth=layer_index + 1,
            frontier_size=len(frontier),
            frontier_peak=frontier_peak,
            beam_width=limits.beam_width,
            pruned=pruned_count,
            state_sha256s=tuple(node.state_sha256 for node in frontier),
        )
        if not frontier:
            return unsuccessful("limit" if limited else "exhausted")

    limited = True
    for node in frontier:
        diagnostic(
            "depth_limit",
            node,
            f"depth limit reached ({limits.max_depth})",
        )
    return unsuccessful("limit")


__all__ = [
    "MAX_SEARCH_DEPTH",
    "CandidatePolicy",
    "EventfulCandidatePolicy",
    "SearchDiagnostic",
    "SearchLimits",
    "SearchResult",
    "SearchStatus",
    "search",
]
