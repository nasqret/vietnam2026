"""A small interactive Peano Hydra session.

This module is the first functional join of the three deliberately separate
parts of Hydra:

* a human-owned Peano Lab proof session;
* an untrusted Qwen proposal boundary; and
* a bounded direct-child Vampire resolution attempt.

The join does not add a proof rule.  Manual tactics and accepted Qwen macros
run through Peano Lab's public surface.  Qwen may also select an explicit
premise list for Vampire.  Vampire's status remains inert until its tiny
reconstructor produces public commands.  A closed successor is returned only
after a fresh replay from the original theorem passes the independent kernel.

All operations are functional and transactional.  A rejected operation
returns the identical :class:`HydraAssistantSession` object supplied by the
caller.  Merely asking Qwen records pending proposal data but does not mutate
the proof owner.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
from typing import TypeAlias

from peano_lab.engine.trace import render_goals
from peano_lab.kernel.checker import axiom_formula, check
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.kernel.proofs import Proof
from peano_lab.library.theorems import get as get_theorem
from peano_lab.ui.prove import run_surface

from .macro_runner import (
    MacroExecutionError,
    MacroOwner,
    _fresh_final_replay,
    _state_record,
    execute_macro,
    start_macro_session,
)
from .macros import Rewrite, parse_macro
from .qwen_hydra_bridge import (
    ModelTransport,
    QwenHydraAuthority,
    QwenHydraBridgeError,
    QwenHydraProposal,
    QwenHydraRequest,
    RetrievedPremise,
    parse_qwen_hydra_response,
    propose_with_transport,
    render_qwen_hydra_prompt,
)
from .vampire_live import (
    VampireLiveAccepted,
    VampireLiveFailure,
    VampireLiveSolver,
    run_vampire_live,
)


HYDRA_ASSISTANT_FORMAT = "peano-hydra-interactive-assistant"
HYDRA_ASSISTANT_VERSION = 1
MAX_ASSISTANT_PREMISES = 128
MAX_ASSISTANT_COMMAND_BYTES = 64 * 1024

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z", re.ASCII)
_DIGEST = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
_QWEN_ACTIONS = ("Cut", "Induct", "Rewrite", "Split", "Use", "Witness")
_QWEN_COMMANDS = (
    "exists",
    "have",
    "induction",
    "left",
    "rewrite",
    "right",
    "specialize",
    "split",
    "suffices",
    "use",
)


class HydraAssistantError(ValueError):
    """A caller supplied an invalid interactive-assistant value."""


def _error_text(value: object) -> str:
    text = " ".join(str(value).split())
    return text[:2_000] or type(value).__name__


def _premise_names(value: object) -> tuple[str, ...]:
    if type(value) is not tuple or len(value) > MAX_ASSISTANT_PREMISES:
        raise HydraAssistantError(
            f"premise names must be an exact tuple of at most {MAX_ASSISTANT_PREMISES} names"
        )
    if not all(type(name) is str and _NAME.fullmatch(name) for name in value):
        raise HydraAssistantError("premise names must be bounded Peano identifiers")
    if len(value) != len(set(value)):
        raise HydraAssistantError("premise names must be unique")
    return value


def _canonical_command(value: object) -> str:
    if type(value) is not str or not value:
        raise HydraAssistantError("manual tactic must be non-empty text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        raise HydraAssistantError("manual tactic must be UTF-8") from None
    if len(encoded) > MAX_ASSISTANT_COMMAND_BYTES:
        raise HydraAssistantError("manual tactic exceeds its byte bound")
    if value != value.strip() or value.splitlines() != [value]:
        raise HydraAssistantError("manual tactic must be one canonical physical line")
    return value


def _owner_binding_sha256(owner: MacroOwner) -> str:
    payload = {
        "capability_sha256": owner.capability_sha256,
        "original_theorem": pretty_formula(owner.original_target, []),
        "profile_identity": owner.profile_identity,
        "state": _state_record(owner),
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(b"peano-hydra-assistant-owner-v1\0" + encoded).hexdigest()


def _response_bytes(raw: str | bytes) -> bytes:
    if type(raw) is bytes:
        return raw
    if type(raw) is str:
        try:
            return raw.encode("utf-8")
        except UnicodeEncodeError:
            raise HydraAssistantError("Qwen response is not UTF-8") from None
    raise HydraAssistantError("Qwen response must be exact text or bytes")


@dataclass(frozen=True, slots=True)
class PendingQwenProposal:
    """One request and optional inert response bound to the current owner."""

    request: QwenHydraRequest
    owner_binding_sha256: str
    proposal: QwenHydraProposal | None = None
    response_bytes: bytes | None = None

    def __post_init__(self) -> None:
        if type(self.request) is not QwenHydraRequest:
            raise TypeError("pending Qwen request must be exact QwenHydraRequest")
        if (
            type(self.owner_binding_sha256) is not str
            or _DIGEST.fullmatch(self.owner_binding_sha256) is None
        ):
            raise ValueError("pending Qwen owner binding is malformed")
        if self.proposal is None:
            if self.response_bytes is not None:
                raise ValueError("pending Qwen response bytes lack a parsed proposal")
            return
        if type(self.proposal) is not QwenHydraProposal:
            raise TypeError("pending Qwen proposal must be exact QwenHydraProposal")
        if type(self.response_bytes) is not bytes:
            raise TypeError("parsed Qwen proposal must retain its exact response bytes")
        try:
            rebuilt = parse_qwen_hydra_response(self.response_bytes, self.request)
        except QwenHydraBridgeError as exc:
            raise ValueError(f"retained Qwen response no longer validates: {exc}") from None
        if rebuilt != self.proposal:
            raise ValueError("pending Qwen proposal differs from its exact response bytes")


@dataclass(frozen=True, slots=True)
class HydraAssistantSession:
    """The immutable proof owner plus optional inert Qwen proposal data."""

    owner: MacroOwner
    pending_qwen: PendingQwenProposal | None = None
    checked_certificate: Proof | None = None

    def __post_init__(self) -> None:
        if type(self.owner) is not MacroOwner:
            raise TypeError("Hydra assistant session needs an exact MacroOwner")
        if self.pending_qwen is not None and type(self.pending_qwen) is not PendingQwenProposal:
            raise TypeError("pending_qwen must be exact PendingQwenProposal or null")
        if self.pending_qwen is not None and (
            self.pending_qwen.owner_binding_sha256 != _owner_binding_sha256(self.owner)
        ):
            raise ValueError("pending Qwen data belongs to another proof owner")
        if self.checked_certificate is not None:
            if (
                not isinstance(self.checked_certificate, Proof)
                or not self.owner.state.is_done()
                or not check((), self.checked_certificate, self.owner.original_target)
            ):
                raise ValueError("assistant checked-certificate receipt is invalid")
        if self.pending_qwen is not None and self.checked_certificate is not None:
            raise ValueError("closed checked session cannot carry pending Qwen data")

    @property
    def is_done(self) -> bool:
        return self.owner.state.is_done()

    @property
    def kernel_accepted(self) -> bool:
        return self.is_done and self.checked_certificate is not None


@dataclass(frozen=True, slots=True)
class HydraAssistantAccepted:
    """A committed manual, Qwen-macro, or Vampire transition."""

    session: HydraAssistantSession
    channel: str
    public_commands: tuple[str, ...]
    certificate: Proof | None
    proposal_sha256: str | None = None
    solver_trace_sha256: str | None = None

    @property
    def closed(self) -> bool:
        return self.session.is_done

    @property
    def kernel_accepted(self) -> bool:
        return (
            self.closed
            and self.certificate is not None
            and self.session.checked_certificate == self.certificate
        )

    def __post_init__(self) -> None:
        if type(self.session) is not HydraAssistantSession:
            raise TypeError("accepted transition needs an exact assistant session")
        if self.channel not in {"manual", "qwen-macros", "qwen-vampire", "vampire"}:
            raise ValueError("accepted transition channel is unsupported")
        if type(self.public_commands) is not tuple or not self.public_commands or not all(
            type(command) is str and bool(command) for command in self.public_commands
        ):
            raise TypeError("accepted transition needs non-empty public commands")
        if self.session.is_done:
            if not isinstance(self.certificate, Proof) or not check(
                (), self.certificate, self.session.owner.original_target
            ):
                raise ValueError("closed assistant successor lacks a checked certificate")
            if self.session.checked_certificate != self.certificate:
                raise ValueError("closed assistant successor lost its checked-QED receipt")
        elif self.certificate is not None:
            raise ValueError("open assistant successor cannot carry a final certificate")
        for label, digest in (
            ("proposal", self.proposal_sha256),
            ("solver trace", self.solver_trace_sha256),
        ):
            if digest is not None and (
                type(digest) is not str or _DIGEST.fullmatch(digest) is None
            ):
                raise ValueError(f"accepted {label} SHA-256 is malformed")


@dataclass(frozen=True, slots=True)
class HydraAssistantRejected:
    """A discarded attempt; ``session`` is the caller's identical object."""

    session: HydraAssistantSession
    channel: str
    error: str
    proposal_sha256: str | None = None
    solver_trace_sha256: str | None = None

    def __post_init__(self) -> None:
        if type(self.session) is not HydraAssistantSession:
            raise TypeError("rejected transition needs an exact assistant session")
        if self.channel not in {"manual", "qwen", "qwen-macros", "qwen-vampire", "vampire"}:
            raise ValueError("rejected transition channel is unsupported")
        if type(self.error) is not str or not self.error:
            raise ValueError("rejected transition needs one final error")
        for label, digest in (
            ("proposal", self.proposal_sha256),
            ("solver trace", self.solver_trace_sha256),
        ):
            if digest is not None and (
                type(digest) is not str or _DIGEST.fullmatch(digest) is None
            ):
                raise ValueError(f"rejected {label} SHA-256 is malformed")


HydraAssistantTransition: TypeAlias = HydraAssistantAccepted | HydraAssistantRejected


def start_hydra_assistant(theorem: str) -> HydraAssistantSession:
    """Start one closed intuitionistic theorem under the ordinary macro profile."""

    return HydraAssistantSession(start_macro_session(theorem))


def render_hydra_state(session: HydraAssistantSession) -> str:
    """Render the current goals using Peano Lab's canonical goal renderer."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("render_hydra_state needs an exact assistant session")
    goals = render_goals(session.owner.state)
    if not goals:
        if session.kernel_accepted:
            return "QED — fresh original-goal kernel replay accepted."
        return "No open goals — no attached fresh-kernel QED receipt."
    return "\n".join(
        f"Goal {index}/{len(goals)}\n  {goal}" for index, goal in enumerate(goals, 1)
    )


def current_script(session: HydraAssistantSession) -> tuple[str, ...]:
    """Return the committed public commands, excluding any inert proposal."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("current_script needs an exact assistant session")
    return tuple(step.command for step in session.owner.replay_steps)


def _certificate_if_closed(owner: MacroOwner) -> Proof | None:
    if not owner.state.is_done():
        return None
    certificate, _ = _fresh_final_replay(owner)
    if not check((), certificate, owner.original_target):
        raise HydraAssistantError("fresh original-goal kernel replay rejected")
    return certificate


def run_manual_tactic(
    session: HydraAssistantSession,
    command: str,
) -> HydraAssistantTransition:
    """Run one ordinary Peano tactic transactionally and clear stale proposals."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("run_manual_tactic needs an exact assistant session")
    try:
        line = _canonical_command(command)
        successor = run_surface(
            session.owner.session,
            line,
            capabilities=session.owner.capabilities,
            record_trace=False,
        )
        owner = session.owner.with_session(successor)
        certificate = _certificate_if_closed(owner)
    except Exception as exc:
        return HydraAssistantRejected(session, "manual", _error_text(exc))
    return HydraAssistantAccepted(
        HydraAssistantSession(owner, checked_certificate=certificate),
        "manual",
        (line,),
        certificate,
    )


def _retrieved_premises(
    session: HydraAssistantSession,
    names: tuple[str, ...],
) -> tuple[RetrievedPremise, ...]:
    result: list[RetrievedPremise] = []
    for name in names:
        axiom = axiom_formula(name)
        if axiom is not None:
            result.append(RetrievedPremise(name, pretty_formula(axiom, [])))
            continue
        theorem = get_theorem(name)
        if theorem is None or theorem.name != name:
            raise HydraAssistantError(f"unknown public premise {name!r}")
        allowed = session.owner.capabilities.allowed_theorems
        if allowed is not None and name not in allowed:
            raise HydraAssistantError(
                f"premise {name!r} is masked by capability environment "
                f"{session.owner.capabilities.label!r}"
            )
        try:
            formula, free_names = parse_formula_with_names(theorem.statement)
        except Exception as exc:
            raise HydraAssistantError(
                f"public premise {name!r} has a malformed statement: {_error_text(exc)}"
            ) from None
        if free_names:
            raise HydraAssistantError(f"public premise {name!r} is unexpectedly open")
        result.append(RetrievedPremise(name, pretty_formula(formula, [])))
    return tuple(result)


def prepare_qwen_request(
    session: HydraAssistantSession,
    premise_names: tuple[str, ...],
) -> HydraAssistantSession:
    """Prepare a prompt-bound request without invoking a model or changing proof state."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("prepare_qwen_request needs an exact assistant session")
    if session.is_done:
        raise HydraAssistantError("there is no open goal for Qwen")
    names = _premise_names(premise_names)
    retrieved = _retrieved_premises(session, names)
    public = tuple(sorted(item.name for item in retrieved if axiom_formula(item.name) is None))
    authority = QwenHydraAuthority(
        allowed_premises=tuple(sorted(names)),
        allowed_actions=_QWEN_ACTIONS,
        allowed_commands=_QWEN_COMMANDS,
        allowed_theorems=public,
        available_solvers=(),
    )
    request = QwenHydraRequest(
        goal=render_hydra_state(session),
        retrieved=retrieved,
        authority=authority,
    )
    return HydraAssistantSession(
        session.owner,
        PendingQwenProposal(request, _owner_binding_sha256(session.owner)),
    )


def qwen_prompt(session: HydraAssistantSession) -> str:
    """Return the exact prompt for a prepared request."""

    if type(session) is not HydraAssistantSession or session.pending_qwen is None:
        raise HydraAssistantError("prepare a Qwen request first")
    return render_qwen_hydra_prompt(session.pending_qwen.request)


def _pending_qwen_is_current(session: HydraAssistantSession) -> bool:
    """Rebind inert proposal data to the exact current goal and retrieval."""

    pending = session.pending_qwen
    if pending is None:
        return False
    try:
        checked_pending = PendingQwenProposal(
            pending.request,
            pending.owner_binding_sha256,
            pending.proposal,
            pending.response_bytes,
        )
    except (TypeError, ValueError):
        return False
    if (
        checked_pending != pending
        or pending.owner_binding_sha256 != _owner_binding_sha256(session.owner)
    ):
        return False
    names = tuple(item.name for item in pending.request.retrieved)
    try:
        current = _retrieved_premises(session, names)
        public = tuple(
            sorted(item.name for item in current if axiom_formula(item.name) is None)
        )
        expected = QwenHydraRequest(
            goal=render_hydra_state(session),
            retrieved=current,
            authority=QwenHydraAuthority(
                allowed_premises=tuple(sorted(names)),
                allowed_actions=_QWEN_ACTIONS,
                allowed_commands=_QWEN_COMMANDS,
                allowed_theorems=public,
                available_solvers=(),
            ),
        )
    except (HydraAssistantError, QwenHydraBridgeError):
        return False
    return expected == pending.request


def attach_qwen_response(
    session: HydraAssistantSession,
    raw: str | bytes,
) -> HydraAssistantSession:
    """Attach one validated inert model response to a prepared request."""

    if type(session) is not HydraAssistantSession or session.pending_qwen is None:
        raise HydraAssistantError("prepare a Qwen request before attaching a response")
    if not _pending_qwen_is_current(session):
        raise HydraAssistantError("prepared Qwen request is stale for the current owner")
    try:
        proposal = parse_qwen_hydra_response(raw, session.pending_qwen.request)
    except QwenHydraBridgeError as exc:
        raise HydraAssistantError(_error_text(exc)) from None
    return HydraAssistantSession(
        session.owner,
        PendingQwenProposal(
            session.pending_qwen.request,
            session.pending_qwen.owner_binding_sha256,
            proposal,
            _response_bytes(raw),
        ),
    )


def ask_qwen(
    session: HydraAssistantSession,
    premise_names: tuple[str, ...],
    transport: ModelTransport,
) -> HydraAssistantSession:
    """Prepare, invoke, and attach one bounded untrusted model proposal.

    ``transport`` is host-owned: this function bounds its prompt and response
    bytes but cannot preempt an arbitrary in-process callable.  A browser or
    remote service must supply its own wall-time/process containment before it
    enters this API.
    """

    prepared = prepare_qwen_request(session, premise_names)
    assert prepared.pending_qwen is not None
    captured: list[str | bytes] = []

    def retaining_transport(prompt: str) -> str | bytes:
        raw = transport(prompt)
        captured.append(raw)
        return raw

    try:
        proposal = propose_with_transport(
            prepared.pending_qwen.request,
            retaining_transport,
        )
    except QwenHydraBridgeError as exc:
        raise HydraAssistantError(_error_text(exc)) from None
    if len(captured) != 1:
        raise HydraAssistantError("Qwen transport did not produce exactly one response")
    return HydraAssistantSession(
        prepared.owner,
        PendingQwenProposal(
            prepared.pending_qwen.request,
            prepared.pending_qwen.owner_binding_sha256,
            proposal,
            _response_bytes(captured[0]),
        ),
    )


def discard_qwen(session: HydraAssistantSession) -> HydraAssistantSession:
    """Discard proposal data without changing the proof owner."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("discard_qwen needs an exact assistant session")
    return (
        session
        if session.pending_qwen is None
        else HydraAssistantSession(
            session.owner,
            checked_certificate=session.checked_certificate,
        )
    )


def apply_qwen_macros(session: HydraAssistantSession) -> HydraAssistantTransition:
    """Execute all pending typed macros as one outer transaction."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("apply_qwen_macros needs an exact assistant session")
    pending = session.pending_qwen
    if pending is None or pending.proposal is None:
        return HydraAssistantRejected(session, "qwen", "there is no validated Qwen proposal")
    if not _pending_qwen_is_current(session):
        return HydraAssistantRejected(
            session,
            "qwen-macros",
            "Qwen proposal is stale for the current owner",
            proposal_sha256=pending.proposal.raw_sha256,
        )
    if not pending.proposal.macro_lines:
        return HydraAssistantRejected(
            session,
            "qwen-macros",
            "Qwen selected premises but proposed no typed macros",
            proposal_sha256=pending.proposal.raw_sha256,
        )
    temporary = session.owner
    commands: list[str] = []
    certificate: Proof | None = None
    try:
        for line in pending.proposal.macro_lines:
            action = parse_macro(line)
            if (
                type(action) is Rewrite
                and axiom_formula(action.source) is not None
                and action.source not in pending.proposal.premises
            ):
                raise HydraAssistantError(
                    f"Qwen rewrite axiom {action.source!r} was not selected as a premise"
                )
            execution = execute_macro(temporary, line)
            temporary = execution.owner
            commands.extend(execution.public_commands)
            certificate = execution.certificate
        if temporary.state.is_done() and certificate is None:
            certificate = _certificate_if_closed(temporary)
    except MacroExecutionError as exc:
        return HydraAssistantRejected(
            session,
            "qwen-macros",
            _error_text(exc),
            proposal_sha256=pending.proposal.raw_sha256,
        )
    except Exception as exc:
        return HydraAssistantRejected(
            session,
            "qwen-macros",
            _error_text(exc),
            proposal_sha256=pending.proposal.raw_sha256,
        )
    return HydraAssistantAccepted(
        HydraAssistantSession(temporary, checked_certificate=certificate),
        "qwen-macros",
        tuple(commands),
        certificate,
        proposal_sha256=pending.proposal.raw_sha256,
    )


def run_vampire_assistance(
    session: HydraAssistantSession,
    premise_names: tuple[str, ...],
    solver: VampireLiveSolver,
    *,
    channel: str = "vampire",
) -> HydraAssistantTransition:
    """Resolve with explicit premises and commit only a checked public replay."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("run_vampire_assistance needs an exact assistant session")
    if channel not in {"vampire", "qwen-vampire"}:
        raise HydraAssistantError("Vampire assistant channel is unsupported")
    names = _premise_names(premise_names)
    result = run_vampire_live(session.owner, names, solver)
    if type(result) is VampireLiveFailure:
        if result.owner is not session.owner:
            raise RuntimeError("failed Vampire preview changed proof ownership")
        return HydraAssistantRejected(
            session,
            channel,
            result.error,
            solver_trace_sha256=result.trace.sha256,
        )
    if type(result) is not VampireLiveAccepted:
        raise RuntimeError("Vampire live returned an unknown result type")
    return HydraAssistantAccepted(
        HydraAssistantSession(result.owner, checked_certificate=result.certificate),
        channel,
        result.public_commands,
        result.certificate,
        solver_trace_sha256=result.trace.sha256,
    )


def resolve_qwen_premises(
    session: HydraAssistantSession,
    solver: VampireLiveSolver,
) -> HydraAssistantTransition:
    """Hand Qwen's checked finite premise selection to bounded Vampire."""

    if type(session) is not HydraAssistantSession:
        raise TypeError("resolve_qwen_premises needs an exact assistant session")
    pending = session.pending_qwen
    if pending is None or pending.proposal is None:
        return HydraAssistantRejected(session, "qwen", "there is no validated Qwen proposal")
    if not _pending_qwen_is_current(session):
        return HydraAssistantRejected(
            session,
            "qwen-vampire",
            "Qwen proposal is stale for the current owner",
            proposal_sha256=pending.proposal.raw_sha256,
        )
    if not pending.proposal.premises:
        return HydraAssistantRejected(
            session,
            "qwen-vampire",
            "Qwen selected no premises for Vampire",
            proposal_sha256=pending.proposal.raw_sha256,
        )
    result = run_vampire_assistance(
        session,
        pending.proposal.premises,
        solver,
        channel="qwen-vampire",
    )
    if type(result) is HydraAssistantAccepted:
        return HydraAssistantAccepted(
            result.session,
            result.channel,
            result.public_commands,
            result.certificate,
            proposal_sha256=pending.proposal.raw_sha256,
            solver_trace_sha256=result.solver_trace_sha256,
        )
    return HydraAssistantRejected(
        result.session,
        result.channel,
        result.error,
        proposal_sha256=pending.proposal.raw_sha256,
        solver_trace_sha256=result.solver_trace_sha256,
    )


__all__ = [
    "HYDRA_ASSISTANT_FORMAT",
    "HYDRA_ASSISTANT_VERSION",
    "HydraAssistantError",
    "PendingQwenProposal",
    "HydraAssistantSession",
    "HydraAssistantAccepted",
    "HydraAssistantRejected",
    "HydraAssistantTransition",
    "start_hydra_assistant",
    "render_hydra_state",
    "current_script",
    "run_manual_tactic",
    "prepare_qwen_request",
    "qwen_prompt",
    "attach_qwen_response",
    "ask_qwen",
    "discard_qwen",
    "apply_qwen_macros",
    "run_vampire_assistance",
    "resolve_qwen_premises",
]
