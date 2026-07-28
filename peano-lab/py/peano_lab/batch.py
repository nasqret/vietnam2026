"""Headless, kernel-checked Peano Lab proof execution.

The browser and this module share the same parser, public tactic grammar,
engine, theorem library, and independent kernel.  The headless path omits
terminal panels and certificate pretty-printing.  Corpus/search execution
retains binding always-on traces; a separately named verification-only entry
may omit transition rendering.  This is an adapter, not a second prover.
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from dataclasses import dataclass
from typing import Callable, Literal, Mapping, Sequence, TextIO

from .engine.state import ProofState, proof_size, start
from .engine.tactics import InvalidProof, TACTIC_NAMES, TacticError, TacticLimit
from .engine.trace import (
    TRACE_VERSION,
    TraceLogger,
    render_goals,
    sanitize_trace_text,
)
from .kernel.formulas import (
    Formula,
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from .ui.prove import (
    FULL_SURFACE_CAPABILITIES,
    MAX_INPUT,
    MAX_NUMERAL,
    ProofSession,
    SURFACE_COMMAND_NAMES,
    SURFACE_THEOREM_NAMES,
    SurfaceCapabilities,
    checked_surface_final,
    oversized_numeral,
    run_surface,
    surface_failure_trace_tactics,
    surface_success_trace_tactic,
    surface_transaction_name,
    surface_trace_focus,
)


BATCH_VERSION = 1
MAX_BATCH_TACTICS = 1_024
MAX_BATCH_TEXT = 500_000
MAX_BATCH_TRACE_BYTES = 16_000_000
FULL_BATCH_COMMANDS = SURFACE_COMMAND_NAMES - {"undo"}
MODEL_V1_COMMANDS = frozenset(
    (set(TACTIC_NAMES) - {"undo"}) | {"compact_arith", "ring", "use"}
)
# One fixed, theorem-safe foundation for both policy training and held-out
# evaluation.  Keeping this preimage stable lets the compact prompt carry only
# its SHA-256 identity without asking the model to infer a novel allowlist.
MODEL_V1_THEOREMS: tuple[str, ...] = (
    "zero_add",
    "add_succ_left",
    "add_assoc",
    "no_succ_add_fixed",
    "drop_add_prefix_from_fixed",
    "antisymm_from_witnesses",
    "add_eq_zero_right",
)

BatchStatus = Literal[
    "proved",
    "open",
    "tactic_error",
    "tactic_limit",
    "kernel_rejection",
]

_SESSION_COMMANDS = {
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
}

_TRACE_STEP_FIELDS = (
    "v",
    "session",
    "step",
    "goals_before",
    "focus",
    "tactic",
    "goals_after",
    "status",
    "error",
)


class BatchRequestError(ValueError):
    """A headless request is malformed and has not started a proof."""


class BatchInvariantError(RuntimeError):
    """The untrusted surface crossed a session-owner authority boundary."""


class TraceSinkError(RuntimeError):
    """A trace could not be written completely; execution must fail stop."""


class _CheckedTraceSink:
    """Translate sink failures into a non-tactic exception and reject short writes."""

    __slots__ = ("_sink",)

    def __init__(self, sink: TextIO | Callable[[str], object]) -> None:
        self._sink = sink

    def __call__(self, text: str) -> None:
        try:
            writer = getattr(self._sink, "write", None)
            result = writer(text) if callable(writer) else self._sink(text)  # type: ignore[operator]
        except Exception as exc:
            raise TraceSinkError(f"trace sink failed: {_one_line(exc)}") from exc
        if result is not None and (type(result) is not int or result != len(text)):
            raise TraceSinkError(
                f"trace sink accepted {result!r} of {len(text)} characters"
            )


@dataclass(frozen=True, slots=True)
class BatchResult:
    """Compact outcome for one independently owned theorem attempt."""

    request_id: str
    session_id: str
    status: BatchStatus
    kernel_checked: bool
    theorem: str
    goals: tuple[str, ...]
    tactics_requested: int
    tactics_applied: int
    engine_steps: int
    failed_tactics: int
    proof_nodes: int | None
    failed_step: int | None
    error_type: str | None
    error: str | None
    mode: Literal["trace", "verify"]
    surface: str
    environment_sha256: str
    classical: bool
    on_error: Literal["stop", "continue"]
    trace: tuple[dict[str, object], ...] | None = None

    def to_dict(self, *, include_trace: bool = True) -> dict[str, object]:
        """Return the stable version-1 JSON object for this outcome."""

        return {
            "v": BATCH_VERSION,
            "id": self.request_id,
            "session": self.session_id,
            "status": self.status,
            "kernel_checked": self.kernel_checked,
            "theorem": self.theorem,
            "goals": list(self.goals),
            "tactics_requested": self.tactics_requested,
            "tactics_applied": self.tactics_applied,
            "engine_steps": self.engine_steps,
            "failed_tactics": self.failed_tactics,
            "proof_nodes": self.proof_nodes,
            "failed_step": self.failed_step,
            "error_type": self.error_type,
            "error": self.error,
            "mode": self.mode,
            "surface": self.surface,
            "environment_sha256": self.environment_sha256,
            "classical": self.classical,
            "on_error": self.on_error,
            "trace_v": TRACE_VERSION if self.trace is not None else None,
            "trace": (
                list(self.trace) if include_trace and self.trace is not None else None
            ),
        }


def _one_line(error: BaseException) -> str:
    raw = " ".join(str(error).split()) or type(error).__name__
    visible = "".join(
        char
        if unicodedata.category(char) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else f"\\u{ord(char):04x}"
        for char in raw
    )
    return visible[:1_000]


def _validate_request_id(request_id: object) -> str:
    if type(request_id) is not str or not request_id:
        raise BatchRequestError("id must be non-empty text")
    if len(request_id) > 256 or request_id != request_id.strip():
        raise BatchRequestError("id must be at most 256 characters with no outer space")
    if request_id.splitlines() != [request_id]:
        raise BatchRequestError("id must fit on one line")
    if any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in request_id
    ):
        raise BatchRequestError("id contains an unsafe control or format character")
    return request_id


def _validate_session_id(session_id: object) -> str:
    if type(session_id) is not str or not session_id:
        raise BatchRequestError("session_id must be non-empty text")
    if len(session_id) > 256 or session_id != session_id.strip():
        raise BatchRequestError(
            "session_id must be at most 256 characters with no outer space"
        )
    if session_id.splitlines() != [session_id] or any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in session_id
    ):
        raise BatchRequestError("session_id must be one control-free line")
    return session_id


def _validate_tactics(tactics: object) -> tuple[str, ...]:
    if type(tactics) not in {list, tuple}:
        raise BatchRequestError("tactics must be an array of complete tactic lines")
    commands = tuple(tactics)
    if not commands:
        raise BatchRequestError("tactics must contain at least one tactic line")
    if len(commands) > MAX_BATCH_TACTICS:
        raise BatchRequestError(
            f"tactics exceeds the {MAX_BATCH_TACTICS}-line batch limit"
        )
    total = 0
    for index, command in enumerate(commands, 1):
        if type(command) is not str or not command.strip():
            raise BatchRequestError(f"tactic {index} must be non-empty text")
        if command != command.strip() or command.splitlines() != [command]:
            raise BatchRequestError(
                f"tactic {index} must be one complete line with no outer space"
            )
        if any(
            unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
            for char in command
        ):
            raise BatchRequestError(
                f"tactic {index} contains an unsafe control or format character"
            )
        if len(command) > MAX_INPUT:
            raise BatchRequestError(
                f"tactic {index} exceeds the {MAX_INPUT}-character line limit"
            )
        oversized = oversized_numeral(command)
        if oversized is not None:
            raise BatchRequestError(
                f"tactic {index} contains numeral {oversized} above the "
                f"resource limit of {MAX_NUMERAL}"
            )
        head = command.split(maxsplit=1)[0]
        if head in _SESSION_COMMANDS or command.startswith("compact_arith?"):
            raise BatchRequestError(
                f"tactic {index} is a session command; pass only proof tactics"
            )
        total += len(command)
    if total > MAX_BATCH_TEXT:
        raise BatchRequestError(
            f"tactics exceed the {MAX_BATCH_TEXT}-character batch limit"
        )
    return commands


def _false_footer(
    trace: TraceLogger,
    state: ProofState,
    original_target: Formula,
    original_names: tuple[str, ...],
    *,
    emit_trace: bool,
) -> None:
    if emit_trace:
        trace.footer(
            qed=False,
            theorem=original_target,
            proof_size=proof_size(state.partial),
            names=original_names,
        )


TraceCheckpoint = tuple[int, int, tuple[str, ...] | None]


def _trace_snapshot(trace: TraceLogger) -> TraceCheckpoint:
    """Take an O(1) checkpoint of the logger's append-only public state."""

    count = trace.record_count
    previous_after: tuple[str, ...] | None = None
    if count:
        previous = trace.records_since(count - 1)[0]
        goals_after = previous.get("goals_after")
        if type(goals_after) is not list:
            raise BatchInvariantError("the existing trace prefix is malformed")
        previous_after = tuple(goals_after)
    return count, trace.tactic_count, previous_after


def _render_with_trace_aliases(trace: TraceLogger, state: ProofState) -> tuple[str, ...]:
    aliases = getattr(trace, "_meta_names", None)
    if type(aliases) is not dict:  # pragma: no cover - TraceLogger invariant guard
        raise BatchInvariantError("the session trace lost its metavariable name table")
    return tuple(render_goals(state, meta_names=dict(aliases)))


def _checked_trace_delta(
    trace: TraceLogger,
    checkpoint: TraceCheckpoint,
) -> tuple[dict[str, object], ...]:
    prefix_count, prefix_tactics, _ = checkpoint
    delta = trace.records_since(prefix_count)
    if not delta:
        raise BatchInvariantError("the surface returned without a trace transition")
    for offset, record in enumerate(delta, prefix_count + 1):
        if type(record) is not dict or tuple(record) != _TRACE_STEP_FIELDS:
            raise BatchInvariantError("the surface emitted a malformed trace transition")
        if (
            record["v"] != TRACE_VERSION
            or record["session"] != trace.session_id
            or record["step"] != offset
        ):
            raise BatchInvariantError("the surface broke trace session/step continuity")
    if trace.tactic_count != prefix_tactics + len(delta):
        raise BatchInvariantError("the surface broke the trace tactic counter")
    return delta


def _check_success_trace(
    trace: TraceLogger,
    checkpoint: TraceCheckpoint,
    before_owner: ProofSession,
    after_owner: ProofSession,
    command: str,
) -> None:
    before = before_owner.state
    after = after_owner.state
    delta = _checked_trace_delta(trace, checkpoint)
    if after.history[: len(before.history)] != before.history:
        raise BatchInvariantError("the surface replaced earlier proof history")
    expected_tactic = surface_success_trace_tactic(command)
    is_top_level_auto = expected_tactic is None
    if is_top_level_auto:
        added_history = after.history[len(before.history) :]
        if len(delta) != len(added_history) or not added_history:
            raise BatchInvariantError(
                "auto's trace does not match its surviving primitive history"
            )
        expected_commands = tuple(
            f"{step.tactic} {step.args}".strip() for step in added_history
        )
        if tuple(record["tactic"] for record in delta) != expected_commands:
            raise BatchInvariantError(
                "auto's trace commands do not match its surviving proof history"
            )
    elif len(delta) != 1:
        raise BatchInvariantError(
            "one submitted surface command emitted multiple trace transitions"
        )
    else:
        if delta[0]["tactic"] != expected_tactic:
            raise BatchInvariantError(
                "the surface trace tactic does not match the submitted command"
            )
    if any(record["status"] != "ok" or record["error"] is not None for record in delta):
        raise BatchInvariantError("a successful surface command emitted an error trace")
    expected_before = (
        checkpoint[2] if checkpoint[2] is not None else tuple(render_goals(before))
    )
    if tuple(delta[0]["goals_before"]) != expected_before:
        raise BatchInvariantError("the surface trace does not start from its input state")
    for left, right in zip(delta, delta[1:]):
        if left["goals_after"] != right["goals_before"]:
            raise BatchInvariantError("the surface broke trace goal-state continuity")
    if tuple(delta[-1]["goals_after"]) != _render_with_trace_aliases(trace, after):
        raise BatchInvariantError("the surface trace does not end in its returned state")
    expected_focus = surface_trace_focus(command, before)
    if delta[0]["focus"] != expected_focus:
        raise BatchInvariantError("the surface trace focus does not match the submitted command")


def _check_success_replay(
    before: ProofSession,
    after: ProofSession,
    command: str,
    capabilities: SurfaceCapabilities,
) -> None:
    """Bind the returned undo/replay journal to the submitted surface action."""

    replay_prefix = len(before.replay_steps)
    history_prefix = len(before.state.history)
    if after.replay_steps[:replay_prefix] != before.replay_steps:
        raise BatchInvariantError("the surface replaced earlier replay history")
    if after.state.history[:history_prefix] != before.state.history:
        raise BatchInvariantError("the surface replaced earlier proof history")
    added_replay = after.replay_steps[replay_prefix:]
    added_history = after.state.history[history_prefix:]
    if len(added_replay) != len(added_history) or not added_replay:
        raise BatchInvariantError(
            "the surface returned mismatched replay and proof-history steps"
        )
    expected_tactic = surface_success_trace_tactic(command)
    if expected_tactic is None:
        expected_commands = tuple(
            f"{step.tactic} {step.args}".strip() for step in added_history
        )
    else:
        expected_commands = (" ".join(command.split()),)
    if tuple(step.command for step in added_replay) != expected_commands:
        raise BatchInvariantError(
            "the surface replay journal does not match the submitted command"
        )
    if any(step.classical is not before.classical for step in added_replay):
        raise BatchInvariantError("the surface replay journal changed logic mode")
    expected_transaction = surface_transaction_name(
        command,
        before.classical,
        capabilities,
    )
    if expected_transaction is not None and (
        len(added_history) != 1 or added_history[0].tactic != expected_transaction
    ):
        raise BatchInvariantError(
            "the surface proof history does not match the submitted command"
        )


def _check_failure_trace(
    trace: TraceLogger,
    checkpoint: TraceCheckpoint,
    before: ProofState,
    command: str,
    error: TacticError,
) -> None:
    delta = _checked_trace_delta(trace, checkpoint)
    if len(delta) != 1:
        raise BatchInvariantError(
            "a failed surface command must emit exactly one trace transition"
        )
    record = delta[0]
    expected = (
        checkpoint[2] if checkpoint[2] is not None else tuple(render_goals(before))
    )
    accepted_tactics = surface_failure_trace_tactics(command)
    if (
        record["status"] != "error"
        or record["error"] != sanitize_trace_text(str(error))
        or record["tactic"] not in accepted_tactics
        or record["focus"] != surface_trace_focus(command, before)
        or tuple(record["goals_before"]) != expected
        or tuple(record["goals_after"]) != expected
    ):
        raise BatchInvariantError(
            "a failed surface command emitted a non-transactional trace"
        )


def _checked_returned_owner(
    candidate: object,
    *,
    original_target: Formula,
    original_names: tuple[str, ...],
    target_source: str,
    classical: bool,
    trace: TraceLogger,
) -> ProofSession:
    """Reject any tactic-layer attempt to replace owner-held authority."""

    if type(candidate) is not ProofSession:
        raise BatchInvariantError("the surface returned a malformed proof-session owner")
    if candidate.original_target != original_target:
        raise BatchInvariantError("the surface replaced the owner-held original theorem")
    if candidate.original_names != original_names:
        raise BatchInvariantError("the surface replaced the original theorem name table")
    if candidate.target_source != target_source:
        raise BatchInvariantError("the surface replaced the original theorem source")
    if candidate.classical is not classical:
        raise BatchInvariantError("the surface replaced the owner-held logic mode")
    if candidate.trace is not trace:
        raise BatchInvariantError("the surface replaced the session trace owner")
    if candidate.state.target != original_target:
        raise BatchInvariantError("the surface replaced the proof state's original target")
    if candidate.state.variables != original_names:
        raise BatchInvariantError("the surface replaced the proof state's name table")
    return candidate


def _stable_session_id(
    request_id: str,
    canonical: str,
    commands: tuple[str, ...],
    *,
    classical: bool,
    on_error: Literal["stop", "continue"],
    capabilities: SurfaceCapabilities,
) -> str:
    payload = json.dumps(
        {
            "v": BATCH_VERSION,
            "id": request_id,
            "theorem": canonical,
            "tactics": commands,
            "classical": classical,
            "on_error": on_error,
            "environment_sha256": capability_sha256(capabilities),
        },
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "peano-batch-" + hashlib.sha256(payload).hexdigest()[:24]


def capability_sha256(capabilities: SurfaceCapabilities) -> str:
    """Fingerprint the complete tactic/theorem authority, not only its label."""

    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be a SurfaceCapabilities value")
    # Materialize unrestricted fields as the complete current inventory. This
    # both changes the digest when production grows and gives data manifests a
    # closed preimage that the training prompt can verify without importing an
    # implicit wildcard authority.
    authority: dict[str, object] = {
        "label": capabilities.label,
        "allowed_commands": sorted(
            FULL_BATCH_COMMANDS
            if capabilities.allowed_commands is None
            else capabilities.allowed_commands
        ),
        "allowed_theorems": sorted(
            SURFACE_THEOREM_NAMES
            if capabilities.allowed_theorems is None
            else capabilities.allowed_theorems
        ),
    }
    payload = json.dumps(
        authority,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _execute_proof(
    theorem: str,
    tactics: Sequence[str],
    *,
    request_id: str = "proof",
    classical: bool = False,
    on_error: Literal["stop", "continue"] = "stop",
    emit_trace: bool,
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
    trace_sink: TextIO | Callable[[str], object] | None = None,
    session_id: str | None = None,
) -> BatchResult:
    """Shared implementation for traced generation and quiet verification.

    A returned ``proved`` is the only success status and is issued only after
    ``checked_surface_final`` checks the completed certificate against the
    separately retained original theorem.  Every other status claims no
    theorem.  A failing tactic is checked to leave its input state unchanged.
    """

    request_id = _validate_request_id(request_id)
    if type(theorem) is not str or not theorem.strip():
        raise BatchRequestError("theorem must be non-empty text")
    if theorem != theorem.strip() or len(theorem) > MAX_INPUT:
        raise BatchRequestError(
            f"theorem must have no outer space and at most {MAX_INPUT} characters"
        )
    if theorem.splitlines() != [theorem]:
        raise BatchRequestError("theorem must fit on one line")
    if any(
        unicodedata.category(char) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for char in theorem
    ):
        raise BatchRequestError(
            "theorem contains an unsafe control or format character"
        )
    oversized = oversized_numeral(theorem)
    if oversized is not None:
        raise BatchRequestError(
            f"theorem contains numeral {oversized} above the resource limit "
            f"of {MAX_NUMERAL}"
        )
    commands = _validate_tactics(tactics)
    if type(classical) is not bool:
        raise BatchRequestError("classical must be a Boolean")
    if type(on_error) is not str or on_error not in {"stop", "continue"}:
        raise BatchRequestError("on_error must be exactly 'stop' or 'continue'")
    if type(emit_trace) is not bool:
        raise BatchRequestError("trace must be a Boolean")
    if type(capabilities) is not SurfaceCapabilities:
        raise BatchRequestError("capabilities must be a SurfaceCapabilities value")
    environment_sha256 = capability_sha256(capabilities)
    if not emit_trace and trace_sink is not None:
        raise BatchRequestError("verification-only execution cannot receive a trace sink")

    try:
        target, names = parse_formula_with_names(theorem)
    except RecursionError:
        raise BatchRequestError(
            "invalid theorem: formula nesting exceeded the parser resource limit"
        ) from None
    except (ParseError, TypeError, ValueError) as exc:
        raise BatchRequestError(f"invalid theorem: {_one_line(exc)}") from None
    if names:
        raise BatchRequestError(
            "theorem must be closed; quantify free variables explicitly: "
            + ", ".join(names)
        )
    canonical = pretty_formula(target, list(names))
    if session_id is None:
        session_id = _stable_session_id(
            request_id,
            canonical,
            commands,
            classical=classical,
            on_error=on_error,
            capabilities=capabilities,
        )
    else:
        session_id = _validate_session_id(session_id)
    checked_sink = _CheckedTraceSink(trace_sink) if trace_sink is not None else None
    trace = TraceLogger(
        checked_sink,
        session_id=session_id,
        max_bytes=MAX_BATCH_TRACE_BYTES if emit_trace else None,
    )
    owner = ProofSession(
        state=start(target, names),
        original_target=target,
        original_names=names,
        target_source=theorem,
        classical=classical,
        trace=trace,
    )
    mode: Literal["trace", "verify"] = "trace" if emit_trace else "verify"

    applied = 0
    failed_tactics = 0
    last_failed_step: int | None = None
    last_error_type: str | None = None
    last_error: str | None = None
    for index, command in enumerate(commands, 1):
        if owner.state.is_done():
            exc = TacticError(
                f"proof closed before tactic {index}; trailing tactics are not allowed."
            )
            if emit_trace:
                owner.trace.failure(owner.state, 0, command, exc)
            failed_tactics += 1
            _false_footer(
                trace,
                owner.state,
                target,
                names,
                emit_trace=emit_trace,
            )
            return BatchResult(
                request_id=request_id,
                session_id=owner.trace.session_id,
                status="tactic_error",
                kernel_checked=False,
                theorem=canonical,
                goals=(),
                tactics_requested=len(commands),
                tactics_applied=applied,
                engine_steps=len(owner.state.history),
                failed_tactics=failed_tactics,
                proof_nodes=None,
                failed_step=index,
                error_type=type(exc).__name__,
                error=_one_line(exc),
                mode=mode,
                surface=capabilities.label,
                environment_sha256=environment_sha256,
                classical=classical,
                on_error=on_error,
                trace=owner.trace.records if emit_trace else None,
            )
        before_owner = owner
        before = owner.state
        trace_prefix = _trace_snapshot(trace) if emit_trace else ()
        try:
            owner = _checked_returned_owner(
                run_surface(
                    owner,
                    command,
                    capabilities=capabilities,
                    record_trace=emit_trace,
                ),
                original_target=target,
                original_names=names,
                target_source=theorem,
                classical=classical,
                trace=trace,
            )
            _check_success_replay(before_owner, owner, command, capabilities)
            if emit_trace:
                _check_success_trace(
                    trace,
                    trace_prefix,
                    before_owner,
                    owner,
                    command,
                )
        except TacticError as exc:
            if owner.state != before:
                raise RuntimeError("a failed tactic mutated the headless proof state")
            if emit_trace:
                _check_failure_trace(trace, trace_prefix, before, command, exc)
            failed_tactics += 1
            last_failed_step = index
            last_error_type = type(exc).__name__
            last_error = _one_line(exc)
            if on_error == "continue" and not isinstance(exc, TacticLimit):
                continue
            _false_footer(
                trace,
                owner.state,
                target,
                names,
                emit_trace=emit_trace,
            )
            status: BatchStatus = (
                "tactic_limit" if isinstance(exc, TacticLimit) else "tactic_error"
            )
            return BatchResult(
                request_id=request_id,
                session_id=owner.trace.session_id,
                status=status,
                kernel_checked=False,
                theorem=canonical,
                goals=(
                    _render_with_trace_aliases(trace, owner.state)
                    if emit_trace
                    else tuple(render_goals(owner.state))
                ),
                tactics_requested=len(commands),
                tactics_applied=applied,
                engine_steps=len(owner.state.history),
                failed_tactics=failed_tactics,
                proof_nodes=None,
                failed_step=index,
                error_type=type(exc).__name__,
                error=_one_line(exc),
                mode=mode,
                surface=capabilities.label,
                environment_sha256=environment_sha256,
                classical=classical,
                on_error=on_error,
                trace=owner.trace.records if emit_trace else None,
            )
        applied += 1

    if not owner.state.is_done():
        _false_footer(
            trace,
            owner.state,
            target,
            names,
            emit_trace=emit_trace,
        )
        return BatchResult(
            request_id=request_id,
            session_id=owner.trace.session_id,
            status="open",
            kernel_checked=False,
            theorem=canonical,
            goals=(
                _render_with_trace_aliases(trace, owner.state)
                if emit_trace
                else tuple(render_goals(owner.state))
            ),
            tactics_requested=len(commands),
            tactics_applied=applied,
            engine_steps=len(owner.state.history),
            failed_tactics=failed_tactics,
            proof_nodes=None,
            failed_step=last_failed_step,
            error_type=last_error_type,
            error=last_error,
            mode=mode,
            surface=capabilities.label,
            environment_sha256=environment_sha256,
            classical=classical,
            on_error=on_error,
            trace=owner.trace.records if emit_trace else None,
        )

    if emit_trace:
        if trace.tactic_count < 1 or trace.record_count != trace.tactic_count:
            raise BatchInvariantError(
                "a checked QED needs at least one complete trace transition"
            )
        last_transition = trace.last_record
        if last_transition is None or last_transition["goals_after"] != []:
            raise BatchInvariantError(
                "the final trace transition does not close every proof goal"
            )

    try:
        certificate = checked_surface_final(
            owner.state,
            target,
            classical=classical,
            trace=trace if emit_trace else None,
        )
    except InvalidProof as exc:
        _false_footer(
            trace,
            owner.state,
            target,
            names,
            emit_trace=emit_trace,
        )
        return BatchResult(
            request_id=request_id,
            session_id=owner.trace.session_id,
            status="kernel_rejection",
            kernel_checked=False,
            theorem=canonical,
            goals=(),
            tactics_requested=len(commands),
            tactics_applied=applied,
            engine_steps=len(owner.state.history),
            failed_tactics=failed_tactics,
            proof_nodes=None,
            failed_step=None,
            error_type=type(exc).__name__,
            error=_one_line(exc),
            mode=mode,
            surface=capabilities.label,
            environment_sha256=environment_sha256,
            classical=classical,
            on_error=on_error,
            trace=owner.trace.records if emit_trace else None,
        )

    if emit_trace:
        footer = owner.trace.last_record
        if footer is None or footer.get("qed") is not True:
            raise BatchInvariantError("the checked QED trace has no true footer")
        checked_nodes = footer.get("proof_size")
    else:
        checked_nodes = proof_size(certificate)
    if type(checked_nodes) is not int:
        raise RuntimeError("checked trace footer has a malformed proof size")
    return BatchResult(
        request_id=request_id,
        session_id=owner.trace.session_id,
        status="proved",
        kernel_checked=True,
        theorem=canonical,
        goals=(),
        tactics_requested=len(commands),
        tactics_applied=applied,
        engine_steps=len(owner.state.history),
        failed_tactics=failed_tactics,
        proof_nodes=checked_nodes,
        failed_step=None,
        error_type=None,
        error=None,
        mode=mode,
        surface=capabilities.label,
        environment_sha256=environment_sha256,
        classical=classical,
        on_error=on_error,
        trace=owner.trace.records if emit_trace else None,
    )


_REQUEST_FIELDS = frozenset(
    {
        "v",
        "id",
        "theorem",
        "tactics",
        "classical",
        "on_error",
    }
)


def run_proof(
    theorem: str,
    tactics: Sequence[str],
    *,
    request_id: str = "proof",
    classical: bool = False,
    on_error: Literal["stop", "continue"] = "stop",
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
    trace_sink: TextIO | Callable[[str], object] | None = None,
    session_id: str | None = None,
) -> BatchResult:
    """Run one corpus/search proof with binding always-on v1 tracing."""

    return _execute_proof(
        theorem,
        tactics,
        request_id=request_id,
        classical=classical,
        on_error=on_error,
        emit_trace=True,
        capabilities=capabilities,
        trace_sink=trace_sink,
        session_id=session_id,
    )


def verify_proof(
    theorem: str,
    tactics: Sequence[str],
    *,
    request_id: str = "proof",
    classical: bool = False,
    on_error: Literal["stop", "continue"] = "stop",
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
    session_id: str | None = None,
) -> BatchResult:
    """Check an already-authored script without retaining transition data.

    This verification-only path is for fast filtering and regression checks.
    Synthetic generation and automated search must use :func:`run_proof`, for
    which the binding design requires every success and failure to be traced.
    The independent final kernel check is identical in both modes.
    """

    return _execute_proof(
        theorem,
        tactics,
        request_id=request_id,
        classical=classical,
        on_error=on_error,
        emit_trace=False,
        capabilities=capabilities,
        session_id=session_id,
    )


def execute_request(
    request: Mapping[str, object],
    *,
    mode: Literal["trace", "verify"] = "trace",
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
    trace_sink: TextIO | Callable[[str], object] | None = None,
    session_id: str | None = None,
) -> BatchResult:
    """Execute one request under a runner-owned mode and capability set."""

    if type(request) is not dict:
        raise BatchRequestError("each JSONL request must be an object")
    unknown = set(request) - _REQUEST_FIELDS
    if unknown:
        raise BatchRequestError("unknown request field(s): " + ", ".join(sorted(unknown)))
    missing = {"v", "id", "theorem", "tactics"} - set(request)
    if missing:
        raise BatchRequestError("missing request field(s): " + ", ".join(sorted(missing)))
    if request["v"] != BATCH_VERSION or type(request["v"]) is not int:
        raise BatchRequestError(f"v must be exactly {BATCH_VERSION}")
    if type(mode) is not str or mode not in {"trace", "verify"}:
        raise BatchRequestError("mode must be exactly 'trace' or 'verify'")
    if type(capabilities) is not SurfaceCapabilities:
        raise BatchRequestError("capabilities must be a SurfaceCapabilities value")
    if mode == "verify" and trace_sink is not None:
        raise BatchRequestError("verification-only execution cannot receive a trace sink")
    runner = run_proof if mode == "trace" else verify_proof
    return runner(
        request["theorem"],  # type: ignore[arg-type]
        request["tactics"],  # type: ignore[arg-type]
        request_id=request["id"],  # type: ignore[arg-type]
        classical=request.get("classical", False),  # type: ignore[arg-type]
        on_error=request.get("on_error", "stop"),  # type: ignore[arg-type]
        capabilities=capabilities,
        **(
            {"trace_sink": trace_sink, "session_id": session_id}
            if mode == "trace"
            else {"session_id": session_id}
        ),
    )


def request_error(
    request_id: object,
    error: BaseException,
    *,
    mode: Literal["trace", "verify"] | None = None,
    surface: str | None = None,
    environment_sha256: str | None = None,
) -> dict[str, object]:
    """Return a compact non-executed response for one malformed request."""

    try:
        visible_id = _validate_request_id(request_id)
    except BatchRequestError:
        visible_id = ""
    return {
        "v": BATCH_VERSION,
        "id": visible_id,
        "session": None,
        "status": "request_error",
        "kernel_checked": False,
        "theorem": None,
        "goals": [],
        "tactics_requested": 0,
        "tactics_applied": 0,
        "engine_steps": 0,
        "failed_tactics": 0,
        "proof_nodes": None,
        "failed_step": None,
        "error_type": type(error).__name__,
        "error": _one_line(error),
        "mode": mode,
        "surface": surface,
        "environment_sha256": environment_sha256,
        "classical": None,
        "on_error": None,
        "trace_v": None,
        "trace": None,
    }


__all__ = [
    "BATCH_VERSION",
    "MAX_BATCH_TACTICS",
    "MAX_BATCH_TEXT",
    "MAX_BATCH_TRACE_BYTES",
    "FULL_BATCH_COMMANDS",
    "MODEL_V1_COMMANDS",
    "MODEL_V1_THEOREMS",
    "BatchRequestError",
    "BatchInvariantError",
    "TraceSinkError",
    "capability_sha256",
    "BatchResult",
    "execute_request",
    "request_error",
    "run_proof",
    "verify_proof",
]
