"""Bounded, proposal-only Qwen boundary for Peano Hydra.

The bridge shows one current Peano goal and an explicit list of retrieved
``name : statement`` pairs to an untrusted text model.  It accepts either one
strict JSON response or a deliberately tiny line format, validates every
selected premise and typed Hydra macro against caller-owned allow-lists, and
returns inert proposal data.  It never owns a proof session, executes a public
command, constructs a certificate, or claims QED.

The injected model transport is a host-owned invocation boundary.  This
module bounds the prompt and returned response bytes; it does not launch a
process or enforce execution time, memory, network, or process isolation.

JSON responses have exactly this shape::

    {"format":"peano-hydra-qwen-proposal","v":1,
     "premises":["add_comm"],
     "macros":[{"format":"peano-hydra-macro","v":1,
                "action":"Use","name":"add_comm",
                "specializations":[]}]}

The equivalent text transport is one ``premises:`` line followed by zero or
more ``macro:`` lines containing complete macro JSON objects.  Markdown,
session commands, free-form tactic text, extra fields, and silent repair are
intentionally unsupported.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
import json
import re
from typing import TypeAlias
import unicodedata

from peano_lab.kernel.formulas import (
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import SurfaceCapabilities

from .macros import (
    CompiledMacro,
    Dispatch,
    DispatchRequest,
    MacroCompileError,
    MacroProtocolError,
    Use,
    compile_macro,
    parse_macro,
    serialize_macro,
)


QWEN_HYDRA_PROPOSAL_FORMAT = "peano-hydra-qwen-proposal"
QWEN_HYDRA_PROPOSAL_VERSION = 1
QWEN_HYDRA_PROMPT_FORMAT = "peano-hydra-qwen-prompt"
QWEN_HYDRA_PROMPT_VERSION = 1

MAX_MODEL_RESPONSE_BYTES = 64 * 1024
MAX_PROMPT_BYTES = 256 * 1024
MAX_GOAL_BYTES = 64 * 1024
MAX_STATEMENT_BYTES = 16 * 1024
MAX_RETRIEVED_PREMISES = 128
MAX_PROPOSED_PREMISES = 128
MAX_PROPOSED_MACROS = 64
MAX_TEXT_LINES = MAX_PROPOSED_MACROS + 1

_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z", re.ASCII)
_SOLVER_RE = re.compile(r"[a-z][a-z0-9._-]{0,127}\Z", re.ASCII)
_ACTION_NAMES = frozenset(
    {"Use", "Cut", "Witness", "Induct", "Rewrite", "Split", "Dispatch"}
)
_UNSAFE_CATEGORIES = frozenset({"Cf", "Cs", "Zl", "Zp"})


class QwenHydraBridgeError(ValueError):
    """An untrusted prompt input or model proposal violated the bridge contract."""


def _utf8_bytes(label: str, value: object, *, maximum: int) -> bytes:
    if type(value) is not str or not value:
        raise QwenHydraBridgeError(f"{label} must be non-empty text")
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError:
        raise QwenHydraBridgeError(f"{label} is not UTF-8") from None
    if len(raw) > maximum:
        raise QwenHydraBridgeError(f"{label} exceeds its {maximum}-byte limit")
    return raw


def _safe_multiline(label: str, value: object, *, maximum: int) -> str:
    raw = _utf8_bytes(label, value, maximum=maximum)
    assert type(value) is str
    if b"\r" in raw or value != value.strip():
        raise QwenHydraBridgeError(
            f"{label} must use canonical LF text with no outer whitespace"
        )
    for character in value:
        category = unicodedata.category(character)
        if category in _UNSAFE_CATEGORIES or (
            category == "Cc" and character != "\n"
        ):
            raise QwenHydraBridgeError(f"{label} contains an unsafe character")
    return value


def _name(label: str, value: object) -> str:
    if type(value) is not str or _NAME_RE.fullmatch(value) is None:
        raise QwenHydraBridgeError(f"{label} must be one bounded Peano name")
    return value


def _name_tuple(
    label: str,
    value: object,
    *,
    maximum: int,
    sorted_required: bool,
) -> tuple[str, ...]:
    if type(value) not in {tuple, list}:
        raise QwenHydraBridgeError(f"{label} must be an exact tuple or array")
    if len(value) > maximum:
        raise QwenHydraBridgeError(f"{label} exceeds its {maximum}-name limit")
    result = tuple(_name(f"{label}[{index}]", item) for index, item in enumerate(value))
    if len(result) != len(set(result)):
        raise QwenHydraBridgeError(f"{label} contains duplicate names")
    if sorted_required and tuple(sorted(result)) != result:
        raise QwenHydraBridgeError(f"{label} must be sorted")
    return result


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _prompt_json(value: object) -> str:
    """Encode section content without leaving literal XML-like delimiters.

    JSON permits Unicode escapes inside strings.  Escaping the three markup
    characters after canonical serialization keeps the value lossless while
    ensuring provider-owned text cannot inject ``</goal>`` or another prompt
    section marker.
    """

    return (
        _canonical_json(value)
        .replace("&", "\\u0026")
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class RetrievedPremise:
    """One prompt-visible closed theorem statement; it grants no authority."""

    name: str
    statement: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _name("retrieved premise name", self.name))
        _utf8_bytes(
            f"statement for {self.name!r}",
            self.statement,
            maximum=MAX_STATEMENT_BYTES,
        )
        if self.statement.splitlines() != [self.statement]:
            raise QwenHydraBridgeError("retrieved premise statements must be one line")
        try:
            formula, free_names = parse_formula_with_names(self.statement)
        except (ParseError, TypeError, ValueError, RecursionError) as exc:
            raise QwenHydraBridgeError(
                f"statement for {self.name!r} is not a Peano formula: {exc}"
            ) from None
        if free_names:
            raise QwenHydraBridgeError(
                f"statement for {self.name!r} must be closed"
            )
        canonical = pretty_formula(formula, [])
        if canonical != self.statement:
            raise QwenHydraBridgeError(
                f"statement for {self.name!r} is not canonical; expected {canonical!r}"
            )

    def to_record(self) -> dict[str, str]:
        return {"name": self.name, "statement": self.statement}


@dataclass(frozen=True, slots=True)
class QwenHydraAuthority:
    """Complete finite authority against which model text is checked."""

    allowed_premises: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    allowed_commands: tuple[str, ...]
    allowed_theorems: tuple[str, ...]
    available_solvers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for field in (
            "allowed_premises",
            "allowed_commands",
            "allowed_theorems",
        ):
            object.__setattr__(
                self,
                field,
                _name_tuple(
                    field,
                    getattr(self, field),
                    maximum=MAX_RETRIEVED_PREMISES,
                    sorted_required=True,
                ),
            )
        actions = self.allowed_actions
        if (
            type(actions) is not tuple
            or not all(type(item) is str for item in actions)
            or tuple(sorted(actions)) != actions
        ):
            raise QwenHydraBridgeError("allowed_actions must be one sorted exact tuple")
        if len(actions) != len(set(actions)) or not set(actions).issubset(_ACTION_NAMES):
            raise QwenHydraBridgeError("allowed_actions contains duplicate or unknown tags")
        solvers = self.available_solvers
        if (
            type(solvers) is not tuple
            or not all(type(item) is str for item in solvers)
            or tuple(sorted(solvers)) != solvers
            or len(solvers) != len(set(solvers))
            or not all(_SOLVER_RE.fullmatch(item) for item in solvers)
        ):
            raise QwenHydraBridgeError(
                "available_solvers must be a sorted unique tuple of solver names"
            )
        if not set(self.allowed_theorems).issubset(self.allowed_premises):
            raise QwenHydraBridgeError(
                "allowed_theorems must be a subset of allowed_premises"
            )
        # This also rejects unknown public commands/theorems.  It is merely a
        # compiler capability, not a live proof-session authority.
        try:
            self.surface_capabilities
        except (TypeError, ValueError) as exc:
            raise QwenHydraBridgeError(
                f"surface capability allow-list is invalid: {exc}"
            ) from None

    @property
    def surface_capabilities(self) -> SurfaceCapabilities:
        return SurfaceCapabilities(
            label="hydra-qwen-proposal-v1",
            allowed_commands=frozenset(self.allowed_commands),
            allowed_theorems=frozenset(self.allowed_theorems),
        )

    def to_record(self) -> dict[str, object]:
        return {
            "allowed_actions": list(self.allowed_actions),
            "allowed_commands": list(self.allowed_commands),
            "allowed_premises": list(self.allowed_premises),
            "allowed_theorems": list(self.allowed_theorems),
            "available_solvers": list(self.available_solvers),
        }


@dataclass(frozen=True, slots=True)
class QwenHydraRequest:
    """A deterministic goal/retrieval observation plus explicit authority."""

    goal: str
    retrieved: tuple[RetrievedPremise, ...]
    authority: QwenHydraAuthority

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "goal",
            _safe_multiline("current Peano goal", self.goal, maximum=MAX_GOAL_BYTES),
        )
        if (
            type(self.retrieved) is not tuple
            or len(self.retrieved) > MAX_RETRIEVED_PREMISES
            or not all(type(item) is RetrievedPremise for item in self.retrieved)
        ):
            raise QwenHydraBridgeError(
                f"retrieved must contain at most {MAX_RETRIEVED_PREMISES} premises"
            )
        names = tuple(item.name for item in self.retrieved)
        if len(names) != len(set(names)):
            raise QwenHydraBridgeError("retrieved premises contain duplicate names")
        if type(self.authority) is not QwenHydraAuthority:
            raise QwenHydraBridgeError("authority must be QwenHydraAuthority")
        missing = sorted(set(self.authority.allowed_premises) - set(names))
        if missing:
            raise QwenHydraBridgeError(
                "premise allow-list contains names absent from retrieval: "
                + ", ".join(missing)
            )
        # Bound the final prompt during construction as well as each input.
        render_qwen_hydra_prompt(self)

    def to_record(self) -> dict[str, object]:
        return {
            "authority": self.authority.to_record(),
            "goal": self.goal,
            "retrieved": [item.to_record() for item in self.retrieved],
        }

    @property
    def sha256(self) -> str:
        return _sha256_text(_canonical_json(self.to_record()))


@dataclass(frozen=True, slots=True)
class QwenHydraProposal:
    """Validated but inert model output; no field is proof authority."""

    request_sha256: str
    prompt_sha256: str
    raw_sha256: str
    premises: tuple[str, ...]
    macro_lines: tuple[str, ...]
    public_commands: tuple[str, ...]
    dispatch_requests: tuple[DispatchRequest, ...]

    @property
    def session_mutated(self) -> bool:
        return False

    @property
    def qed_authority(self) -> bool:
        return False

    def to_record(self) -> dict[str, object]:
        return {
            "authority": "none",
            "dispatches": [
                {
                    "bounds": {
                        "max_memory_bytes": item.bounds.max_memory_bytes,
                        "max_output_bytes": item.bounds.max_output_bytes,
                        "max_steps": item.bounds.max_steps,
                        "max_wall_time_ms": item.bounds.max_wall_time_ms,
                    },
                    "premises": list(item.premises),
                    "solver": item.solver,
                }
                for item in self.dispatch_requests
            ],
            "format": QWEN_HYDRA_PROPOSAL_FORMAT,
            "macro_lines": list(self.macro_lines),
            "premises": list(self.premises),
            "prompt_sha256": self.prompt_sha256,
            "public_commands": list(self.public_commands),
            "qed_authority": False,
            "raw_sha256": self.raw_sha256,
            "request_sha256": self.request_sha256,
            "session_mutated": False,
            "status": "proposal-only",
            "v": QWEN_HYDRA_PROPOSAL_VERSION,
        }


def render_qwen_hydra_prompt(request: QwenHydraRequest) -> str:
    """Render the exact bounded prompt supplied to a model transport."""

    if type(request) is not QwenHydraRequest:
        raise QwenHydraBridgeError("request must be QwenHydraRequest")
    contract = {
        "additional_fields": "forbidden",
        "format": QWEN_HYDRA_PROPOSAL_FORMAT,
        "macros": "array of peano-hydra-macro-v1 JSON objects",
        "premises": "unique array selected from allowed_premises",
        "v": QWEN_HYDRA_PROPOSAL_VERSION,
    }
    goal_bytes = request.goal.encode("utf-8")
    goal_record = {
        "bytes": len(goal_bytes),
        "encoding": "utf-8",
        "sha256": hashlib.sha256(goal_bytes).hexdigest(),
        "text": request.goal,
    }
    prompt = "\n".join(
        (
            f"<format>{QWEN_HYDRA_PROMPT_FORMAT}:{QWEN_HYDRA_PROMPT_VERSION}</format>",
            "<task>Propose premises and typed Peano Hydra macros. Do not claim QED.</task>",
            "<goal>",
            _prompt_json(goal_record),
            "</goal>",
            "<retrieved>",
            _canonical_json([item.to_record() for item in request.retrieved]),
            "</retrieved>",
            "<authority>",
            _canonical_json(request.authority.to_record()),
            "</authority>",
            "<response-contract>",
            _canonical_json(contract),
            "</response-contract>",
            "<proposal>",
        )
    )
    if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
        raise QwenHydraBridgeError(
            f"rendered prompt exceeds its {MAX_PROMPT_BYTES}-byte limit"
        )
    return prompt


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise QwenHydraBridgeError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise QwenHydraBridgeError(f"non-finite JSON number {value!r}")


def _response_bytes(raw: object) -> tuple[bytes, str]:
    if type(raw) is str:
        if len(raw) > MAX_MODEL_RESPONSE_BYTES:
            raise QwenHydraBridgeError("model response exceeds its byte limit")
        try:
            encoded = raw.encode("utf-8")
        except UnicodeEncodeError:
            raise QwenHydraBridgeError("model response is not UTF-8") from None
    elif type(raw) is bytes:
        encoded = raw
    else:
        raise QwenHydraBridgeError("model response must be exact text or bytes")
    if not encoded:
        raise QwenHydraBridgeError("model response must not be empty")
    if len(encoded) > MAX_MODEL_RESPONSE_BYTES:
        raise QwenHydraBridgeError("model response exceeds its byte limit")
    try:
        text = encoded.decode("utf-8")
    except UnicodeDecodeError:
        raise QwenHydraBridgeError("model response is not UTF-8") from None
    if "\r" in text:
        raise QwenHydraBridgeError("model response must use LF line endings")
    return encoded, text


def _json_response(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    try:
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except QwenHydraBridgeError:
        raise
    except (json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise QwenHydraBridgeError(f"model response is not strict JSON: {exc}") from None
    expected = {"format", "v", "premises", "macros"}
    if type(value) is not dict or set(value) != expected:
        raise QwenHydraBridgeError("JSON proposal has missing or additional fields")
    if value["format"] != QWEN_HYDRA_PROPOSAL_FORMAT:
        raise QwenHydraBridgeError("JSON proposal has the wrong format")
    if type(value["v"]) is not int or value["v"] != QWEN_HYDRA_PROPOSAL_VERSION:
        raise QwenHydraBridgeError("JSON proposal has the wrong version")
    premises = _name_tuple(
        "proposal premises",
        value["premises"],
        maximum=MAX_PROPOSED_PREMISES,
        sorted_required=False,
    )
    macros = value["macros"]
    if type(macros) is not list or len(macros) > MAX_PROPOSED_MACROS:
        raise QwenHydraBridgeError(
            f"proposal macros must be an array of at most {MAX_PROPOSED_MACROS} objects"
        )
    lines: list[str] = []
    for index, item in enumerate(macros):
        if type(item) is not dict:
            raise QwenHydraBridgeError(f"proposal macros[{index}] must be an object")
        lines.append(_canonical_json(item))
    if not premises and not lines:
        raise QwenHydraBridgeError("proposal must select a premise or emit a macro")
    return premises, tuple(lines)


def _text_response(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if text.startswith("```") or text.endswith("```"):
        raise QwenHydraBridgeError("Markdown fences are not part of the text protocol")
    lines = text.splitlines()
    if len(lines) > MAX_TEXT_LINES or not lines or not lines[0].startswith("premises:"):
        raise QwenHydraBridgeError("text proposal must start with one premises: line")
    if any(not line or line != line.strip() for line in lines):
        raise QwenHydraBridgeError("text proposal lines must be non-empty and canonical")
    tail = lines[0][len("premises:") :]
    if tail and not tail.startswith(" "):
        raise QwenHydraBridgeError("premises: must be followed by a space or end of line")
    words = [] if not tail else tail[1:].split(" ")
    if any(not word for word in words):
        raise QwenHydraBridgeError("premises: uses single-space name separation")
    premises = _name_tuple(
        "proposal premises",
        words,
        maximum=MAX_PROPOSED_PREMISES,
        sorted_required=False,
    )
    macro_lines: list[str] = []
    for index, line in enumerate(lines[1:]):
        if not line.startswith("macro: "):
            raise QwenHydraBridgeError(
                f"text proposal line {index + 2} must start with 'macro: '"
            )
        macro_lines.append(line[len("macro: ") :])
    if not premises and not macro_lines:
        raise QwenHydraBridgeError("proposal must select a premise or emit a macro")
    return premises, tuple(macro_lines)


def _compile_lines(
    macro_lines: tuple[str, ...],
    premises: tuple[str, ...],
    request: QwenHydraRequest,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[DispatchRequest, ...]]:
    canonical: list[str] = []
    commands: list[str] = []
    dispatches: list[DispatchRequest] = []
    selected = frozenset(premises)
    retrieved = frozenset(item.name for item in request.retrieved)
    for index, line in enumerate(macro_lines):
        try:
            action = parse_macro(line)
        except MacroProtocolError as exc:
            raise QwenHydraBridgeError(f"macro {index + 1} is invalid: {exc}") from None
        tag = type(action).__name__
        if tag not in request.authority.allowed_actions:
            raise QwenHydraBridgeError(
                f"macro action {tag!r} is masked by the explicit allow-list"
            )
        if type(action) is Use and action.name not in selected:
            raise QwenHydraBridgeError(
                f"Use premise {action.name!r} was not selected by the proposal"
            )
        if type(action) is Dispatch:
            masked = tuple(name for name in action.premises if name not in selected)
            if masked:
                raise QwenHydraBridgeError(
                    "Dispatch uses unselected premise(s): " + ", ".join(masked)
                )
        # A retrieved theorem named by another macro must not evade premise
        # selection.  State-local hypotheses/PA axioms are intentionally left
        # for later transactional state validation.
        source = getattr(action, "source", None)
        if source in retrieved and source not in selected:
            raise QwenHydraBridgeError(
                f"macro source {source!r} was not selected by the proposal"
            )
        try:
            compiled: CompiledMacro = compile_macro(
                action,
                capabilities=request.authority.surface_capabilities,
                available_solvers=request.authority.available_solvers,
            )
        except (MacroCompileError, MacroProtocolError) as exc:
            raise QwenHydraBridgeError(f"macro {index + 1} is unavailable: {exc}") from None
        canonical.append(serialize_macro(action))
        commands.extend(compiled.public_commands)
        if compiled.dispatch is not None:
            dispatches.append(compiled.dispatch)
    return tuple(canonical), tuple(commands), tuple(dispatches)


def parse_qwen_hydra_response(
    raw: str | bytes,
    request: QwenHydraRequest,
) -> QwenHydraProposal:
    """Parse and capability-check model bytes without executing any proposal."""

    if type(request) is not QwenHydraRequest:
        raise QwenHydraBridgeError("request must be QwenHydraRequest")
    encoded, text = _response_bytes(raw)
    stripped = text.strip()
    if not stripped:
        raise QwenHydraBridgeError("model response must not be whitespace")
    if stripped.startswith("{"):
        premises, macro_lines = _json_response(stripped)
    else:
        premises, macro_lines = _text_response(stripped)
    masked = tuple(
        name for name in premises if name not in request.authority.allowed_premises
    )
    if masked:
        raise QwenHydraBridgeError(
            "proposal selected premise(s) outside the explicit allow-list: "
            + ", ".join(masked)
        )
    canonical, commands, dispatches = _compile_lines(macro_lines, premises, request)
    prompt = render_qwen_hydra_prompt(request)
    return QwenHydraProposal(
        request_sha256=request.sha256,
        prompt_sha256=_sha256_text(prompt),
        raw_sha256=hashlib.sha256(encoded).hexdigest(),
        premises=premises,
        macro_lines=canonical,
        public_commands=commands,
        dispatch_requests=dispatches,
    )


# A host owns invocation and resource isolation.  The bridge owns only the
# deterministic prompt and the bounded parsing of returned bytes.
ModelTransport: TypeAlias = Callable[[str], str | bytes]


def propose_with_transport(
    request: QwenHydraRequest,
    transport: ModelTransport,
) -> QwenHydraProposal:
    """Call one host-owned transport and return only a validated proposal.

    Prompt and response sizes are bounded here.  Wall time, memory, network,
    and process isolation must be enforced by the host which supplies
    ``transport``.
    """

    if type(request) is not QwenHydraRequest:
        raise QwenHydraBridgeError("request must be QwenHydraRequest")
    if not callable(transport):
        raise QwenHydraBridgeError("transport must be callable")
    prompt = render_qwen_hydra_prompt(request)
    try:
        raw = transport(prompt)
    except Exception as exc:
        # Do not echo provider error text: it may contain a partial response,
        # prompt content, or backend details.  No parse or proposal object has
        # been constructed at this point.
        raise QwenHydraBridgeError(
            f"model transport failed with {type(exc).__name__}"
        ) from None
    return parse_qwen_hydra_response(raw, request)


__all__ = [
    "MAX_MODEL_RESPONSE_BYTES",
    "MAX_PROMPT_BYTES",
    "QWEN_HYDRA_PROMPT_FORMAT",
    "QWEN_HYDRA_PROMPT_VERSION",
    "QWEN_HYDRA_PROPOSAL_FORMAT",
    "QWEN_HYDRA_PROPOSAL_VERSION",
    "ModelTransport",
    "QwenHydraAuthority",
    "QwenHydraBridgeError",
    "QwenHydraProposal",
    "QwenHydraRequest",
    "RetrievedPremise",
    "parse_qwen_hydra_response",
    "propose_with_transport",
    "render_qwen_hydra_prompt",
]
