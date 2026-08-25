"""Bounded verifier-guided search over Peano Lab's public tactic surface.

The policy used here is deliberately untrusted.  It sees only canonical goal
text and returns a ranked tuple of complete tactic lines.  This module does
not inspect or construct proof terms itself: every edge is replayed through
``run_surface`` with an explicit capability object, and a result is published
only after ``checked_surface_final`` checks the certificate against the
independently retained original theorem.

Search nodes retain immutable, authority-bound proof-prefix snapshots rather
than mutable sessions.  Each candidate restores its parent's persistent proof
state into a fresh ``ProofSession`` with a fresh branch-local ``TraceLogger``
and executes exactly one new public-surface edge.  Failed siblings therefore
remain transactional without repeatedly replaying an already accepted prefix.
The independent original-goal kernel finalization remains unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Literal, Protocol, runtime_checkable
import unicodedata

from peano_lab.engine.state import ProofState, proof_size, start
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
from peano_lab.kernel.terms import UNARY_NUMERAL_LIMIT
from peano_lab.ui.prove import (
    MAX_INPUT,
    MAX_NUMERAL,
    ProofSession,
    ReplayStep,
    SurfaceCapabilities,
    checked_surface_final,
    oversized_numeral,
    run_surface,
)


MAX_SEARCH_DEPTH = 32
MAX_DIAGNOSTIC_CHARS = 1_000
FROZEN_POLICY_SURFACES = frozenset({"model-v1", "model-v2", "model-v3"})
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
class _PrefixSnapshot:
    """One immutable proof prefix, bound to its exact execution authority.

    ``ProofState`` is persistent: its goals/history are tuples and its
    substitution map is copied into a read-only mapping proxy.  Replay steps
    and metavariable aliases are immutable tuples too.  In particular, this
    snapshot never retains a ``ProofSession`` or its mutable ``TraceLogger``;
    every edge receives a new branch-private logger upon restoration.
    """

    commands: tuple[str, ...]
    goals: tuple[str, ...]
    state: ProofState
    meta_names: tuple[tuple[int, str], ...]
    replay_steps: tuple[ReplayStep, ...]
    target: Formula
    names: tuple[str, ...]
    theorem_source: str
    classical: bool
    capabilities: SurfaceCapabilities

    @classmethod
    def capture(
        cls,
        owner: ProofSession,
        *,
        commands: tuple[str, ...],
        goals: tuple[str, ...],
        capabilities: SurfaceCapabilities,
    ) -> "_PrefixSnapshot":
        if type(owner) is not ProofSession:
            raise RuntimeError("proof-prefix owner is not an exact ProofSession")
        if owner.trace.record_count:
            raise RuntimeError("proof-prefix owner unexpectedly published trace records")
        if owner.state.target != owner.original_target:
            raise RuntimeError("proof-prefix state changed its original theorem")
        if _canonical_goals(owner) != goals:
            raise RuntimeError("proof-prefix state disagrees with its canonical goals")
        return cls(
            commands,
            goals,
            owner.state,
            owner.meta_names,
            owner.replay_steps,
            owner.original_target,
            owner.original_names,
            owner.target_source,
            owner.classical,
            capabilities,
        )

    def restore(
        self,
        *,
        commands: tuple[str, ...],
        goals: tuple[str, ...],
        target: Formula,
        names: tuple[str, ...],
        theorem_source: str,
        classical: bool,
        capabilities: SurfaceCapabilities,
        replay_id: int,
    ) -> ProofSession:
        if (
            self.commands != commands
            or self.goals != goals
            or self.target != target
            or self.state.target != target
            or self.names != names
            or self.theorem_source != theorem_source
            or self.classical != classical
            or self.capabilities != capabilities
        ):
            raise RuntimeError("cached proof prefix disagrees with its execution authority")
        owner = ProofSession(
            state=self.state,
            original_target=target,
            original_names=names,
            target_source=theorem_source,
            classical=classical,
            trace=TraceLogger(session_id=f"policy-search-replay-{replay_id}"),
            meta_names=self.meta_names,
            replay_steps=self.replay_steps,
        )
        if _canonical_goals(owner) != goals:
            raise RuntimeError("cached proof prefix changed its canonical goals")
        return owner


@dataclass(frozen=True, slots=True)
class _Node:
    commands: tuple[str, ...]
    goals: tuple[str, ...]
    state_sha256: str
    priority: tuple[object, ...]
    prefix: _PrefixSnapshot

    @property
    def depth(self) -> int:
        return len(self.commands)


def _one_line(value: BaseException | str) -> str:
    raw = " ".join(str(value).split()) or type(value).__name__
    return raw[:MAX_DIAGNOSTIC_CHARS]


def state_sha256(goals: tuple[str, ...]) -> str:
    """Hash one complete canonical goal tuple using the search v1 contract."""

    payload = json.dumps(
        list(goals),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


# Compatibility for repository tools which imported the original private
# helper while the public transcript/policy boundary was being introduced.
_state_sha256 = state_sha256


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


def numeral_limit_for_capabilities(capabilities: SurfaceCapabilities) -> int:
    """Preserve frozen model literal profiles without limiting modern goals."""

    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be an exact SurfaceCapabilities value")
    return (
        UNARY_NUMERAL_LIMIT
        if capabilities.label in FROZEN_POLICY_SURFACES
        else MAX_NUMERAL
    )


def _validate_candidate(
    value: object,
    *,
    numeral_limit: int = MAX_NUMERAL,
) -> tuple[str | None, str | None]:
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
    oversized = oversized_numeral(value, maximum=numeral_limit)
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
    prefix: _PrefixSnapshot | None = None,
    expected_goals: tuple[str, ...] | None = None,
) -> tuple[ProofSession | None, int | None, BaseException | None]:
    """Extend a persistent prefix, preserving exact failing-command indices.

    The optional root-replay path remains available to repository diagnostics.
    Production search always supplies its exact immutable parent snapshot and
    executes only the candidate edge under a fresh branch-local trace owner.
    """

    if prefix is None:
        owner = _new_owner(
            target,
            names,
            theorem_source,
            classical=classical,
            replay_id=replay_id,
        )
        first_index = 0
    else:
        if not commands or expected_goals is None:
            return None, 0, RuntimeError("cached proof prefix has no candidate edge")
        try:
            owner = prefix.restore(
                commands=commands[:-1],
                goals=expected_goals,
                target=target,
                names=names,
                theorem_source=theorem_source,
                classical=classical,
                capabilities=capabilities,
                replay_id=replay_id,
            )
        except Exception as exc:
            # A corrupted non-root prefix is a previously accepted command,
            # whereas a corrupted root has no earlier edge to name.
            return None, max(len(commands) - 2, 0), exc
        first_index = len(commands) - 1

    branch_trace = owner.trace
    for index in range(first_index, len(commands)):
        command = commands[index]
        try:
            owner = run_surface(
                owner,
                command,
                capabilities=capabilities,
                record_trace=False,
            )
            if (
                type(owner) is not ProofSession
                or owner.original_target != target
                or owner.state.target != target
                or owner.original_names != names
                or owner.target_source != theorem_source
                or owner.classical != classical
                or owner.trace is not branch_trace
                or branch_trace.record_count
            ):
                raise RuntimeError("proof edge changed its theorem or branch authority")
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
    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be an exact SurfaceCapabilities value")
    numeral_limit = numeral_limit_for_capabilities(capabilities)
    oversized = oversized_numeral(theorem, maximum=numeral_limit)
    if oversized is not None:
        raise ValueError(f"theorem contains resource-dangerous numeral {oversized}")
    if type(classical) is not bool:
        raise TypeError("classical must be a Boolean")
    if type(limits) is not SearchLimits:
        raise TypeError("limits must be an exact SearchLimits value")
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
    root_key = state_sha256(root_goals)
    root = _Node(
        (),
        root_goals,
        root_key,
        (len(root_goals), 0, 0, 0, ()),
        _PrefixSnapshot.capture(
            root_owner,
            commands=(),
            goals=root_goals,
            capabilities=capabilities,
        ),
    )

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

    def unsuccessful(status: SearchStatus) -> SearchResult:
        return SearchResult(
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

    for _ in range(limits.max_depth):
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
            try:
                proposed = policy.propose(
                    node.goals,
                    max_candidates=limits.candidates_per_state,
                )
            except Exception as exc:
                diagnostic("policy_error", node, exc)
                continue
            if type(proposed) is not tuple:
                diagnostic(
                    "policy_error",
                    node,
                    "policy result must be an exact tuple of tactic lines",
                )
                continue
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
                command, error = _validate_candidate(
                    raw_command,
                    numeral_limit=numeral_limit,
                )
                if command is None:
                    diagnostic(
                        "invalid_candidate",
                        node,
                        error or "invalid candidate",
                        depth=node.depth + 1,
                    )
                    continue
                if command in local_commands:
                    diagnostic(
                        "duplicate_candidate",
                        node,
                        "duplicate candidate at the same canonical state",
                        command,
                        depth=node.depth + 1,
                    )
                    continue
                local_commands.add(command)
                path = node.commands + (command,)
                candidates_executed += 1
                replay_id += 1
                owner, failed_index, replay_error = _replay(
                    target,
                    names,
                    theorem,
                    path,
                    classical=classical,
                    capabilities=capabilities,
                    replay_id=replay_id,
                    prefix=node.prefix,
                    expected_goals=node.goals,
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
                    continue

                depth_reached = max(depth_reached, len(path))
                if owner.state.is_done():
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
                        continue
                    return SearchResult(
                        "proof",
                        canonical_theorem,
                        path,
                        proof_size(certificate),
                        tuple(diagnostics),
                        model_calls,
                        states_expanded,
                        states_discovered,
                        candidates_executed,
                        frontier_peak,
                        depth_reached,
                    )

                goals = _canonical_goals(owner)
                key = state_sha256(goals)
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
                    _PrefixSnapshot.capture(
                        owner,
                        commands=path,
                        goals=goals,
                        capabilities=capabilities,
                    ),
                )
                if goals in seen:
                    existing = next_nodes.get(goals)
                    if existing is not None and successor.priority < existing.priority:
                        next_nodes[goals] = successor
                    diagnostic(
                        "duplicate_state",
                        node,
                        "successor is a canonical state already discovered",
                        command,
                        depth=node.depth + 1,
                    )
                    continue
                if states_discovered >= limits.max_states:
                    limited = True
                    diagnostic(
                        "state_limit",
                        node,
                        f"state limit reached ({limits.max_states})",
                        command,
                        depth=node.depth + 1,
                    )
                    continue
                seen.add(goals)
                states_discovered += 1
                next_nodes[goals] = successor

        ordered = sorted(next_nodes.values(), key=lambda item: item.priority)
        if len(ordered) > limits.beam_width:
            limited = True
            kept = ordered[: limits.beam_width]
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
    "FROZEN_POLICY_SURFACES",
    "CandidatePolicy",
    "SearchDiagnostic",
    "SearchLimits",
    "SearchResult",
    "SearchStatus",
    "numeral_limit_for_capabilities",
    "search",
    "state_sha256",
]
