"""Canonical H0.3 macro transport for Peano Hydra.

This module is deliberately an untrusted adapter.  A macro is neither a proof
term nor permission to mutate a proof state: it is a small, versioned JSON
message which compiles to documented Peano Lab surface commands, or (only for
``Dispatch``) to an explicitly untrusted bounded-solver request.  The caller
must execute the commands transactionally and reconstruct every solver result
through the ordinary proof engine before the independent kernel may report
QED.

Version 1 uses one flat JSON object.  ``format``, ``v``, and ``action`` are
common; every action then has exactly the fields shown by :func:`macro_object`.
Unknown and additional fields are rejected.  JSON serialization is compact,
UTF-8, sorted-key, and contains no trailing newline.

``Induct.motive`` is an assertion about the intended state-dependent motive.
The existing public command is only ``induction <variable>`` and derives its
actual motive from the focused goal.  A future transactional executor must
compare the assertion with that derived motive; this transport/compiler does
not pretend to have a proof state and therefore cannot perform that check.
"""

from __future__ import annotations

from collections.abc import Collection
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path
import re
from typing import TypeAlias
import unicodedata

from peano_lab.kernel.formulas import (
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.kernel.terms import parse_term_with_names, pretty_term
from peano_lab.ui.prove import (
    FULL_SURFACE_CAPABILITIES,
    MAX_INPUT,
    MAX_NUMERAL,
    SURFACE_THEOREM_NAMES,
    SurfaceCapabilities,
    oversized_numeral,
)


MACRO_FORMAT = "peano-hydra-macro"
MACRO_VERSION = 1
MACRO_PROTOCOL_FORMAT = "peano-hydra-macro-protocol"
MACRO_PROTOCOL_VERSION = 1
MACRO_PROTOCOL_ID = "peano-hydra-macro-v1"
MACRO_PROTOCOL_PATH = Path(__file__).with_name("macro-protocol-v1.json")
DISPATCH_CALL_FORMAT = "peano-hydra-dispatch-call"
DISPATCH_CALL_VERSION = 1
DISPATCH_RESPONSE_FORMAT = "peano-hydra-dispatch-response"
DISPATCH_RESPONSE_VERSION = 1
DISPATCH_RESPONSE_STATUSES = (
    "theorem",
    "unsat",
    "sat",
    "unknown",
    "resource-limit",
)
MACRO_PROTOCOL_DOCUMENT_SHA256 = (
    "6f6920d2d952251170733674a3af8da09926f4faf19215317a32bc0317d4a482"
)
MACRO_PROTOCOL_SEMANTIC_SHA256 = (
    "b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c"
)

# These are transport ceilings, not theoremhood or decision-procedure bounds.
MAX_MACRO_BYTES = 64 * 1024
MAX_NAME_CHARS = 128
MAX_SPECIALIZATIONS = 32
MAX_DISPATCH_PREMISES = 128

# Dispatch carries every generic resource field.  Wall/output/process controls
# are host-enforced, memory semantics are platform-qualified, and ``max_steps``
# constrains only the adapter's explicitly untrusted self-report.  An adapter
# may declare a lower value but never exceed these transport maxima.
MAX_DISPATCH_STEPS = 100_000_000
MAX_DISPATCH_WALL_TIME_MS = 600_000
MAX_DISPATCH_MEMORY_BYTES = 16 * 1024 * 1024 * 1024
# Successful raw subprocess output is retained byte-for-byte in the bounded
# audit trace.  A rejected host attempt may retain exactly one additional byte
# as a deterministic over-limit witness; that evidence byte never becomes a
# parsed response or gains proof authority.
MAX_DISPATCH_OUTPUT_BYTES = 2 * 1024 * 1024
MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES = MAX_DISPATCH_OUTPUT_BYTES + 1
MAX_DISPATCH_COMMANDS = 256
MAX_DISPATCH_CONFIGURATION_BYTES = 64 * 1024
MAX_DISPATCH_REQUEST_BYTES = 4 * 1024 * 1024
MAX_DISPATCH_CALL_BYTES = 4 * 1024 * 1024
MAX_DISPATCH_ARTIFACT_BYTES = 256 * 1024 * 1024
MAX_MACRO_TRACE_BYTES = 8 * 1024 * 1024
MAX_OWNER_REPLAY_STEPS = 10_000
MAX_DISPATCH_STATUS_CHARS = 128
MAX_ERROR_CHARS = 2_000
MAX_ERROR_UTF8_BYTES = 8_000
MAX_FINAL_ARTIFACT_BYTES = 64 * 1024 * 1024

_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})
_RESERVED_SURFACE_NAMES = frozenset({"S", "forall", "exists", "bot", "false"})
_SOLVER_RE = re.compile(r"[a-z][a-z0-9._-]*\Z", re.ASCII)


class MacroProtocolError(ValueError):
    """A macro wire message or typed action violates protocol v1."""


class MacroCompileError(MacroProtocolError):
    """A valid macro cannot compile in the declared public environment."""


def _safe_one_line(label: str, value: object, *, limit: int) -> str:
    if type(value) is not str or not value:
        raise MacroProtocolError(f"{label} must be non-empty text")
    if len(value) > limit:
        raise MacroProtocolError(f"{label} exceeds {limit} Unicode code points")
    if value != value.strip() or value.splitlines() != [value]:
        raise MacroProtocolError(
            f"{label} must be exactly one line with no outer whitespace"
        )
    if any(
        unicodedata.category(character) in _UNSAFE_CATEGORIES
        for character in value
    ):
        raise MacroProtocolError(f"{label} contains an unsafe Unicode character")
    return value


def _surface_name(label: str, value: object) -> str:
    name = _safe_one_line(label, value, limit=MAX_NAME_CHARS)
    if (
        name in _RESERVED_SURFACE_NAMES
        or not (name[0].isalpha() or name[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in name[1:])
    ):
        raise MacroProtocolError(
            f"{label} must be one Peano surface identifier"
        )
    return name


def _solver_name(value: object) -> str:
    solver = _safe_one_line("Dispatch.solver", value, limit=MAX_NAME_CHARS)
    if _SOLVER_RE.fullmatch(solver) is None:
        raise MacroProtocolError(
            "Dispatch.solver must use lowercase ASCII letters, digits, '.', '_', or '-'"
        )
    return solver


def _surface_source(label: str, value: object) -> str:
    source = _safe_one_line(label, value, limit=MAX_INPUT)
    if "#" in source:
        raise MacroProtocolError(
            f"{label} cannot contain explicit de Bruijn-index syntax"
        )
    dangerous = oversized_numeral(source)
    if dangerous is not None:
        raise MacroProtocolError(
            f"{label} contains decimal numeral {dangerous}, above the profile maximum "
            f"{MAX_NUMERAL}"
        )
    return source


def _canonical_term(label: str, value: object) -> str:
    source = _surface_source(label, value)
    try:
        term, names = parse_term_with_names(source)
        canonical = pretty_term(term, list(names))
        reparsed, reparsed_names = parse_term_with_names(canonical)
    except RecursionError:
        raise MacroProtocolError(f"{label} exceeded parser recursion") from None
    except (ParseError, TypeError, ValueError) as exc:
        raise MacroProtocolError(f"{label} is not a valid Peano term: {exc}") from None
    if canonical != source:
        raise MacroProtocolError(
            f"{label} is not canonical; expected {canonical!r}"
        )
    if reparsed != term or reparsed_names != names:
        raise MacroProtocolError(f"{label} failed canonical round-trip validation")
    return canonical


def _canonical_formula(label: str, value: object) -> str:
    source = _surface_source(label, value)
    try:
        formula, names = parse_formula_with_names(source)
        canonical = pretty_formula(formula, list(names))
        reparsed, reparsed_names = parse_formula_with_names(canonical)
    except RecursionError:
        raise MacroProtocolError(f"{label} exceeded parser recursion") from None
    except (ParseError, TypeError, ValueError) as exc:
        raise MacroProtocolError(
            f"{label} is not a valid Peano formula: {exc}"
        ) from None
    if canonical != source:
        raise MacroProtocolError(
            f"{label} is not canonical; expected {canonical!r}"
        )
    if reparsed != formula or reparsed_names != names:
        raise MacroProtocolError(f"{label} failed canonical round-trip validation")
    return canonical


def _tuple_of_terms(label: str, value: object, *, limit: int) -> tuple[str, ...]:
    # Never call ``tuple`` on an arbitrary model/provider-owned iterable: it
    # may be lazy, side-effecting, or infinite.  Protocol arrays arrive as a
    # built-in list and typed Python callers normally use a tuple; both have a
    # finite O(1) length before we inspect any element.
    if type(value) not in (tuple, list):
        raise MacroProtocolError(
            f"{label} must be an exact tuple or list of terms"
        )
    items = tuple(value)
    if len(items) > limit:
        raise MacroProtocolError(f"{label} contains more than {limit} terms")
    return tuple(
        _canonical_term(f"{label}[{index}]", item)
        for index, item in enumerate(items)
    )


def _tuple_of_names(label: str, value: object, *, limit: int) -> tuple[str, ...]:
    if type(value) not in (tuple, list):
        raise MacroProtocolError(
            f"{label} must be an exact tuple or list of names"
        )
    items = tuple(value)
    if len(items) > limit:
        raise MacroProtocolError(f"{label} contains more than {limit} names")
    names = tuple(
        _surface_name(f"{label}[{index}]", item)
        for index, item in enumerate(items)
    )
    if len(set(names)) != len(names):
        raise MacroProtocolError(f"{label} cannot contain duplicate names")
    return names


@dataclass(frozen=True, slots=True)
class Use:
    """Import one public theorem, then specialize its visible hypothesis."""

    name: str
    specializations: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _surface_name("Use.name", self.name))
        object.__setattr__(
            self,
            "specializations",
            _tuple_of_terms(
                "Use.specializations",
                self.specializations,
                limit=MAX_SPECIALIZATIONS,
            ),
        )


@dataclass(frozen=True, slots=True)
class Cut:
    """Schedule ordinary public ``have`` or ``suffices`` local reasoning."""

    kind: str
    name: str
    formula: str

    def __post_init__(self) -> None:
        if self.kind not in {"have", "suffices"}:
            raise MacroProtocolError("Cut.kind must be 'have' or 'suffices'")
        object.__setattr__(self, "name", _surface_name("Cut.name", self.name))
        object.__setattr__(
            self, "formula", _canonical_formula("Cut.formula", self.formula)
        )


@dataclass(frozen=True, slots=True)
class Witness:
    """Choose one concrete existential witness term."""

    term: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "term", _canonical_term("Witness.term", self.term))


@dataclass(frozen=True, slots=True)
class Induct:
    """Choose an induction variable and assert the intended open motive."""

    variable: str
    motive: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "variable", _surface_name("Induct.variable", self.variable)
        )
        object.__setattr__(
            self, "motive", _canonical_formula("Induct.motive", self.motive)
        )


@dataclass(frozen=True, slots=True)
class Rewrite:
    """Choose an equation source, orientation, and goal/local-hypothesis target."""

    source: str
    direction: str
    location: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "source", _surface_name("Rewrite.source", self.source))
        if self.direction not in {"forward", "backward"}:
            raise MacroProtocolError(
                "Rewrite.direction must be 'forward' or 'backward'"
            )
        if self.location is not None:
            object.__setattr__(
                self,
                "location",
                _surface_name("Rewrite.location", self.location),
            )


@dataclass(frozen=True, slots=True)
class Split:
    """Choose conjunction splitting or one disjunct introduction."""

    kind: str

    def __post_init__(self) -> None:
        if self.kind not in {"conjunction", "left", "right"}:
            raise MacroProtocolError(
                "Split.kind must be 'conjunction', 'left', or 'right'"
            )


def _bounded_integer(label: str, value: object, maximum: int) -> int:
    if type(value) is not int or not 1 <= value <= maximum:
        raise MacroProtocolError(
            f"{label} must be an exact integer from 1 through {maximum}"
        )
    return value


@dataclass(frozen=True, slots=True)
class DispatchBounds:
    """Mandatory typed resource declarations for one untrusted solver call."""

    max_steps: int
    max_wall_time_ms: int
    max_memory_bytes: int
    max_output_bytes: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_steps",
            _bounded_integer(
                "Dispatch.bounds.max_steps", self.max_steps, MAX_DISPATCH_STEPS
            ),
        )
        object.__setattr__(
            self,
            "max_wall_time_ms",
            _bounded_integer(
                "Dispatch.bounds.max_wall_time_ms",
                self.max_wall_time_ms,
                MAX_DISPATCH_WALL_TIME_MS,
            ),
        )
        object.__setattr__(
            self,
            "max_memory_bytes",
            _bounded_integer(
                "Dispatch.bounds.max_memory_bytes",
                self.max_memory_bytes,
                MAX_DISPATCH_MEMORY_BYTES,
            ),
        )
        object.__setattr__(
            self,
            "max_output_bytes",
            _bounded_integer(
                "Dispatch.bounds.max_output_bytes",
                self.max_output_bytes,
                MAX_DISPATCH_OUTPUT_BYTES,
            ),
        )


@dataclass(frozen=True, slots=True)
class Dispatch:
    """Request one registered untrusted solver over an ordered premise bundle."""

    solver: str
    premises: tuple[str, ...]
    bounds: DispatchBounds

    def __post_init__(self) -> None:
        object.__setattr__(self, "solver", _solver_name(self.solver))
        object.__setattr__(
            self,
            "premises",
            _tuple_of_names(
                "Dispatch.premises",
                self.premises,
                limit=MAX_DISPATCH_PREMISES,
            ),
        )
        if type(self.bounds) is not DispatchBounds:
            raise MacroProtocolError("Dispatch.bounds must be DispatchBounds")


Macro: TypeAlias = Use | Cut | Witness | Induct | Rewrite | Split | Dispatch


@dataclass(frozen=True, slots=True)
class DispatchRequest:
    """An explicitly untrusted call request; status alone has no proof authority."""

    solver: str
    premises: tuple[str, ...]
    bounds: DispatchBounds
    authority: str = field(
        default="untrusted-hints-reconstruction-required",
        init=False,
    )

    def __post_init__(self) -> None:
        checked = Dispatch(self.solver, self.premises, self.bounds)
        object.__setattr__(self, "solver", checked.solver)
        object.__setattr__(self, "premises", checked.premises)
        object.__setattr__(self, "bounds", checked.bounds)
        object.__setattr__(
            self, "authority", "untrusted-hints-reconstruction-required"
        )


@dataclass(frozen=True, slots=True)
class CompiledMacro:
    """Exactly one public command plan or one untrusted dispatch request."""

    action: Macro
    public_commands: tuple[str, ...]
    dispatch: DispatchRequest | None

    def __post_init__(self) -> None:
        action_types = {Use, Cut, Witness, Induct, Rewrite, Split, Dispatch}
        if type(self.action) not in action_types:
            raise MacroProtocolError("compiled macro lost its typed source action")
        macro_object(self.action)
        if type(self.public_commands) is not tuple or not all(
            type(command) is str and bool(command) for command in self.public_commands
        ):
            raise MacroProtocolError("compiled public commands must be an exact tuple")
        if bool(self.public_commands) == (self.dispatch is not None):
            raise MacroProtocolError(
                "compiled macro needs exactly one command or dispatch channel"
            )
        if self.dispatch is not None and type(self.dispatch) is not DispatchRequest:
            raise MacroProtocolError("compiled dispatch has the wrong type")


_COMMON_FIELDS = frozenset({"format", "v", "action"})
_ACTION_FIELDS: dict[str, frozenset[str]] = {
    "Use": _COMMON_FIELDS | {"name", "specializations"},
    "Cut": _COMMON_FIELDS | {"kind", "name", "formula"},
    "Witness": _COMMON_FIELDS | {"term"},
    "Induct": _COMMON_FIELDS | {"variable", "motive"},
    "Rewrite": _COMMON_FIELDS | {"source", "direction", "location"},
    "Split": _COMMON_FIELDS | {"kind"},
    "Dispatch": _COMMON_FIELDS | {"solver", "premises", "bounds"},
}
_BOUND_FIELDS = frozenset(
    {"max_steps", "max_wall_time_ms", "max_memory_bytes", "max_output_bytes"}
)


def _live_macro_protocol() -> dict[str, object]:
    """Return the exact code-side H0.3 protocol manifest."""

    common_types = {
        "action": "registered-action-tag",
        "format": f"constant:{MACRO_FORMAT}",
        "v": f"exact-integer:{MACRO_VERSION}",
    }
    action_types: dict[str, dict[str, str]] = {
        "Use": {
            **common_types,
            "name": "public-theorem-name",
            "specializations": f"array[canonical-term,max={MAX_SPECIALIZATIONS}]",
        },
        "Cut": {
            **common_types,
            "kind": "enum:have|suffices",
            "name": "fresh-surface-identifier",
            "formula": "canonical-profile-formula",
        },
        "Witness": {**common_types, "term": "canonical-term"},
        "Induct": {
            **common_types,
            "variable": "surface-identifier",
            "motive": "canonical-profile-formula-engine-equality-required",
        },
        "Rewrite": {
            **common_types,
            "source": "visible-equation-or-pa-axiom-name",
            "direction": "enum:forward|backward",
            "location": "null-or-visible-hypothesis-name",
        },
        "Split": {
            **common_types,
            "kind": "enum:conjunction|left|right",
        },
        "Dispatch": {
            **common_types,
            "solver": "registered-adapter-name",
            "premises": f"array[unique-visible-premise-name,max={MAX_DISPATCH_PREMISES}]",
            "bounds": "exact-dispatch-bounds-object",
        },
    }
    compilation = {
        "Use": {
            "channel": "public-surface",
            "command_heads": ["use", "specialize"],
            "command_templates": [
                "use {name}",
                "specialize {name} {specialization}",
            ],
        },
        "Cut": {
            "channel": "public-surface",
            "command_heads": ["have", "suffices"],
            "command_templates": ["{kind} {name} : {formula}"],
        },
        "Witness": {
            "channel": "public-surface",
            "command_heads": ["exists"],
            "command_templates": ["exists {term}"],
        },
        "Induct": {
            "channel": "public-surface",
            "command_heads": ["induction"],
            "command_templates": ["induction {variable}"],
        },
        "Rewrite": {
            "channel": "public-surface",
            "command_heads": ["rewrite"],
            "command_templates": [
                "rewrite {source}",
                "rewrite <- {source}",
                "rewrite {source} at {location}",
                "rewrite <- {source} at {location}",
            ],
        },
        "Split": {
            "channel": "public-surface",
            "command_heads": ["split", "left", "right"],
            "kind_to_command": {
                "conjunction": "split",
                "left": "left",
                "right": "right",
            },
        },
        "Dispatch": {
            "channel": "untrusted-dispatch-reconstruction",
            "command_heads": [],
            "reconstruction_required": True,
            "status_authority": False,
        },
    }
    actions = {
        tag: {
            "exact_fields": sorted(_ACTION_FIELDS[tag]),
            "field_types": action_types[tag],
            "compilation": compilation[tag],
        }
        for tag in sorted(_ACTION_FIELDS)
    }
    return {
        "format": MACRO_PROTOCOL_FORMAT,
        "v": MACRO_PROTOCOL_VERSION,
        "id": MACRO_PROTOCOL_ID,
        "canonical_json": {
            "encoding": "utf-8",
            "key_order": "lexicographic",
            "separators": [",", ":"],
            "allow_nan": False,
            "wire_trailing_newline": False,
        },
        "transport": {
            "format": MACRO_FORMAT,
            "v": MACRO_VERSION,
            "max_bytes": MAX_MACRO_BYTES,
            "additional_fields": "forbidden",
            "actions": actions,
        },
        "limits": {
            "max_macro_bytes": MAX_MACRO_BYTES,
            "max_name_characters": MAX_NAME_CHARS,
            "max_specializations": MAX_SPECIALIZATIONS,
            "max_dispatch_premises": MAX_DISPATCH_PREMISES,
            "max_dispatch_steps": MAX_DISPATCH_STEPS,
            "max_dispatch_wall_time_ms": MAX_DISPATCH_WALL_TIME_MS,
            "max_dispatch_memory_bytes": MAX_DISPATCH_MEMORY_BYTES,
            "max_dispatch_output_bytes": MAX_DISPATCH_OUTPUT_BYTES,
            "max_dispatch_output_evidence_bytes": (
                MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES
            ),
            "max_dispatch_commands": MAX_DISPATCH_COMMANDS,
            "max_dispatch_configuration_bytes": MAX_DISPATCH_CONFIGURATION_BYTES,
            "max_dispatch_request_bytes": MAX_DISPATCH_REQUEST_BYTES,
            "max_dispatch_call_bytes": MAX_DISPATCH_CALL_BYTES,
            "max_dispatch_artifact_bytes": MAX_DISPATCH_ARTIFACT_BYTES,
            "max_macro_trace_bytes": MAX_MACRO_TRACE_BYTES,
            "max_owner_replay_steps": MAX_OWNER_REPLAY_STEPS,
            "max_dispatch_status_characters": MAX_DISPATCH_STATUS_CHARS,
            "max_error_characters": MAX_ERROR_CHARS,
            "max_error_utf8_bytes": MAX_ERROR_UTF8_BYTES,
            "max_final_artifact_bytes": MAX_FINAL_ARTIFACT_BYTES,
        },
        "dispatch_adapter_identity": {
            "format": "peano-hydra-dispatch-adapter",
            "v": 1,
            "additional_fields": "forbidden",
            "exact_fields": [
                "adapter",
                "artifact_kind",
                "artifact_sha256",
                "configuration_sha256",
                "format",
                "v",
            ],
            "field_types": {
                "adapter": "canonical-solver-token",
                "artifact_kind": "enum:binary|source",
                "artifact_sha256": "lowercase-sha256",
                "configuration_sha256": "lowercase-sha256",
                "format": "constant:peano-hydra-dispatch-adapter",
                "v": "exact-integer:1",
            },
        },
        "dispatch_subprocess": {
            "call": {
                "format": DISPATCH_CALL_FORMAT,
                "v": DISPATCH_CALL_VERSION,
                "additional_fields": "forbidden",
                "exact_fields": [
                    "adapter_identity",
                    "configuration",
                    "context",
                    "format",
                    "request",
                    "request_sha256",
                    "v",
                ],
                "request_bytes": (
                    "canonical compiled request bytes must equal canonical nested "
                    "invoked request bytes and both SHA-256 preimages"
                ),
            },
            "response": {
                "format": DISPATCH_RESPONSE_FORMAT,
                "v": DISPATCH_RESPONSE_VERSION,
                "additional_fields": "forbidden",
                "canonical_compact_json_required": True,
                "exact_fields": [
                    "format",
                    "public_commands",
                    "status",
                    "steps_used",
                    "v",
                ],
                "field_types": {
                    "format": f"constant:{DISPATCH_RESPONSE_FORMAT}",
                    "v": f"exact-integer:{DISPATCH_RESPONSE_VERSION}",
                    "status": "enum:theorem|unsat|sat|unknown|resource-limit",
                    "steps_used": (
                        "untrusted-adapter-reported-exact-nonnegative-integer"
                    ),
                    "public_commands": "bounded-array-of-canonical-public-command-lines",
                },
            },
            "host": {
                "authority": "none",
                "artifact_invocation": "copied-and-rehashed-direct-exec-without-shell",
                "input": "detached-canonical-json-on-stdin",
                "resource_semantics": {
                    "steps_used": {
                        "authority": "untrusted-adapter-self-report",
                        "host_enforced": False,
                        "accepted_relation": (
                            "not-less-than-public-command-count-and-"
                            "not-greater-than-request-max_steps"
                        ),
                        "campaign_usage_metric_eligible": False,
                    },
                    "memory_enforcement_modes": {
                        "linux-rlimit-as-data+sampled-leader-rss": {
                            "platform": "linux",
                            "hard_ceiling": True,
                            "campaign_host_eligible": True,
                            "reported_peak_semantics": (
                                "maximum-sampled-leader-rss-not-exact-peak"
                            ),
                            "campaign_peak_metric_eligible": False,
                        },
                        "darwin-sampled-leader-rss-only": {
                            "platform": "darwin",
                            "hard_ceiling": False,
                            "campaign_host_eligible": False,
                            "reported_peak_semantics": (
                                "maximum-sampled-leader-rss-not-exact-peak"
                            ),
                            "campaign_peak_metric_eligible": False,
                        },
                    },
                },
                "output": (
                    "bounded-raw-inert-stdout-bytes-plus-one-rejection-evidence-byte"
                ),
                "process_limit": 1,
                "privileged_uid_policy": "fail-closed",
                "stderr": "discarded",
                "limits_enforced_externally": [
                    "cpu",
                    "wall-time",
                    "address-space-linux",
                    "data-segment-linux",
                    "file-output",
                    "open-files",
                    "process-count-via-rlimit-nproc-one",
                ],
            },
        },
        "trace": {
            "format": "peano-hydra-macro-trace",
            "v": 1,
            "additional_fields": "forbidden-at-every-registered-object",
            "effective_capability_hash_preimage": (
                "compact-sorted-utf8-json-array-with-no-trailing-newline"
            ),
            "status_enums": {
                "compile": ["not-attempted", "error", "ok"],
                "dispatch_response": list(DISPATCH_RESPONSE_STATUSES),
                "final_replay": ["accepted", "rejected"],
                "logic": ["intuitionistic"],
                "outcome": ["accepted", "rejected"],
                "parse": ["not-attempted", "error", "ok"],
                "premise_kind": [
                    "hypothesis",
                    "pa-axiom",
                    "public-theorem",
                ],
                "raw_encoding": [
                    "utf-8",
                    "base64",
                    "utf-8-sha256-only-oversize",
                    "invalid-unicode-sha256-only-oversize",
                    "bytes-sha256-only-oversize",
                    "invalid-unicode-diagnostic",
                    "invalid-type-diagnostic",
                ],
            },
            "nullability": {
                "compile.dispatch": "object-iff-successful-Dispatch-else-null",
                "compile.dispatch_request_sha256": "digest-iff-dispatch-else-null",
                "compile.error": "text-iff-error-else-null",
                "final_replay": "object-iff-closure-was-freshly-checked-else-null",
                "parse.canonical": "object-iff-ok-else-null",
                "parse.canonical_sha256": "digest-iff-ok-else-null",
                "parse.error": "text-iff-error-else-null",
                "raw_proposal.text": "text-only-for-utf-8-else-null",
                "raw_proposal.base64": "text-only-for-retained-non-utf8-bytes-else-null",
                "solver": "object-iff-compiled-Dispatch-else-null",
                "solver.host_usage": "object-iff-process-launched-and-observed-else-null",
                "solver.dispatch_call_request_sha256": (
                    "digest-iff-canonical-dispatch-call-was-prepared-else-null"
                ),
                "solver.dispatch_call_sha256": (
                    "digest-iff-canonical-dispatch-call-was-prepared-else-null"
                ),
                "solver.raw_response_base64": "text-iff-stdout-observed-else-null",
                "solver.response_status": "enum-iff-raw-response-parsed-else-null",
            },
            "field_sets": {
                "adapter_identity": [
                    "adapter",
                    "artifact_kind",
                    "artifact_sha256",
                    "configuration_sha256",
                    "format",
                    "v",
                ],
                "compile": [
                    "dispatch",
                    "dispatch_request_sha256",
                    "error",
                    "public_commands",
                    "status",
                ],
                "dispatch_call": [
                    "adapter_identity",
                    "configuration",
                    "context",
                    "format",
                    "request",
                    "request_sha256",
                    "v",
                ],
                "dispatch_response": [
                    "format",
                    "public_commands",
                    "status",
                    "steps_used",
                    "v",
                ],
                "dispatch_bounds": sorted(_BOUND_FIELDS),
                "dispatch_request": ["authority", "bounds", "premises", "solver"],
                "effective_capability": ["count", "format", "sha256", "v"],
                "environment": [
                    "allowed_actions",
                    "allowed_commands",
                    "allowed_theorems",
                    "capability_label",
                    "classical",
                    "effective_command_capability",
                    "effective_theorem_capability",
                    "logic",
                    "macro_protocol_identity",
                    "original_theorem",
                    "original_theorem_sha256",
                    "owner_capability_identity",
                    "owner_capability_sha256",
                    "registered_adapter_identities",
                    "registered_solvers",
                    "semantic_profile_identity",
                ],
                "final_replay": [
                    "certificate_depth",
                    "certificate_nodes",
                    "certificate_representation",
                    "certificate_sha256",
                    "commands",
                    "error",
                    "fresh",
                    "kernel_accepted",
                    "original_theorem",
                    "status",
                ],
                "history_entry": ["args", "tactic"],
                "host_usage": [
                    "campaign_host_eligible",
                    "exit_code",
                    "max_observed_rss_bytes",
                    "memory_enforcement",
                    "memory_limit_bytes",
                    "output_bytes",
                    "output_limit_bytes",
                    "peak_processes",
                    "process_enforcement",
                    "process_limit",
                    "reconstructed_command_bytes",
                    "timed_out",
                    "wall_limit_ms",
                    "wall_time_ms",
                ],
                "intermediate_state": ["command", "command_index", "state_summary"],
                "macro_protocol_identity": [
                    "document_sha256",
                    "format",
                    "id",
                    "semantic_sha256",
                    "v",
                ],
                "outcome": ["error", "status"],
                "owner_capability": [
                    "declared_commands",
                    "declared_theorems",
                    "effective_command_capability",
                    "effective_theorem_capability",
                    "format",
                    "label",
                    "v",
                ],
                "parse": ["canonical", "canonical_sha256", "error", "status"],
                "premise": ["formula", "kind", "name"],
                "raw_proposal": ["base64", "bytes", "encoding", "sha256", "text"],
                "replay_entry": ["classical", "command"],
                "solver": [
                    "adapter_configuration",
                    "adapter_identity",
                    "adapter_identity_sha256",
                    "authority",
                    "context",
                    "dispatch_call_request_sha256",
                    "dispatch_call_sha256",
                    "error",
                    "host_usage",
                    "raw_response_base64",
                    "raw_response_bytes",
                    "raw_response_sha256",
                    "reconstructed_commands",
                    "request",
                    "request_sha256",
                    "response_status",
                    "response_steps_used",
                    "step_accounting",
                ],
                "solver_context": ["goals", "original_theorem", "premises"],
                "state": [
                    "closed",
                    "goals",
                    "goals_sha256",
                    "history",
                    "replay",
                    "state_sha256",
                ],
                "state_summary": [
                    "closed",
                    "goals",
                    "goals_sha256",
                    "history_length",
                    "replay_length",
                    "summary_sha256",
                ],
                "top_level": [
                    "compile",
                    "environment",
                    "final_replay",
                    "format",
                    "intermediate_states",
                    "outcome",
                    "parse",
                    "raw_proposal",
                    "solver",
                    "state_after",
                    "state_before",
                    "v",
                ],
            },
            "hash_preimages": {
                "dispatch_request_sha256": "canonical-compact-utf8-request-object",
                "dispatch_call_sha256": (
                    "canonical-compact-utf8-dispatch-call-reconstructed-from-retained-fields"
                ),
                "configuration_sha256": (
                    "canonical-compact-utf8-retained-adapter-configuration-object"
                ),
                "original_theorem_sha256": "canonical-theorem-utf8",
                "owner_capability_sha256": "canonical-compact-utf8-owner-capability-object",
                "raw_response_sha256": "exact-raw-subprocess-stdout-bytes",
                "state_sha256": "domain-NUL-canonical-compact-utf8-state-without-state_sha256",
                "summary_sha256": "domain-NUL-canonical-compact-utf8-summary-without-summary_sha256",
            },
            "validation_relations": [
                "semantic-profile-identity-equals-the-live-pinned-profile",
                "original-theorem-is-canonical-profile-text-and-hash-matches",
                "owner-capability-identity-hash-and-effective-set-hashes-match",
                "raw-proposal-bytes-count-and-hash-match-retained-payload",
                "parsed-action-is-reparsed-from-raw-proposal-and-hash-matches",
                "compiled-plan-equals-typed-compilation-under-owner-capabilities",
                "compiled-invoked-and-traced-request-bytes-and-hashes-are-equal",
                "retained-adapter-configuration-and-reconstructed-dispatch-call-hashes-match",
                "dispatch-context-is-resolved-from-replayed-owner-and-library-state",
                "adapter-identity-is-a-member-of-the-registered-environment",
                "raw-response-is-canonical-strict-json-and-fields-match-trace",
                "raw-response-rejection-evidence-is-bounded-by-one-global-sentinel-byte",
                "host-limit-snapshot-equals-request-bounds-and-usage-is-recomputed",
                "steps-used-is-an-untrusted-adapter-report-not-a-host-step-meter",
                "campaign-eligible-hard-memory-dispatch-is-linux-non-root-only",
                "reconstructed-commands-pass-the-current-public-surface-gate",
                "state-before-and-every-intermediate-replay-under-owner-capabilities",
                "rejected-outcomes-restore-state-before-exactly",
                "accepted-closed-outcomes-replay-from-the-original-target",
                "kernel-certificate-metrics-and-artifact-hash-are-recomputed",
            ],
        },
    }


def _protocol_canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def load_macro_protocol() -> dict[str, object]:
    """Load the exact checked protocol document and fail closed on drift."""

    try:
        raw = MACRO_PROTOCOL_PATH.read_bytes()
    except OSError as exc:
        raise MacroProtocolError(f"cannot read macro protocol document: {exc}") from None
    document_sha256 = hashlib.sha256(raw).hexdigest()
    if document_sha256 != MACRO_PROTOCOL_DOCUMENT_SHA256:
        raise MacroProtocolError("macro protocol document SHA-256 drift")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise MacroProtocolError(f"macro protocol document is invalid: {exc}") from None
    expected = _live_macro_protocol()
    if value != expected:
        raise MacroProtocolError("macro protocol document disagrees with live v1 contract")
    canonical = _protocol_canonical_json(value)
    semantic_sha256 = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    if semantic_sha256 != MACRO_PROTOCOL_SEMANTIC_SHA256:
        raise MacroProtocolError("macro protocol semantic SHA-256 drift")
    canonical_document = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2,
    ).encode("utf-8") + b"\n"
    if raw != canonical_document:
        raise MacroProtocolError("macro protocol document is not canonical pretty JSON")
    return json.loads(canonical)


def macro_protocol_identity() -> dict[str, object]:
    """Return the frozen semantic and byte identities after validating the file."""

    load_macro_protocol()
    return {
        "format": MACRO_PROTOCOL_FORMAT,
        "v": MACRO_PROTOCOL_VERSION,
        "id": MACRO_PROTOCOL_ID,
        "semantic_sha256": MACRO_PROTOCOL_SEMANTIC_SHA256,
        "document_sha256": MACRO_PROTOCOL_DOCUMENT_SHA256,
    }


def _expect_fields(
    label: str,
    value: object,
    expected: frozenset[str],
) -> dict[str, object]:
    if type(value) is not dict:
        raise MacroProtocolError(f"{label} must be one exact JSON object")
    actual = set(value)
    missing = sorted(expected - actual)
    additional = sorted(actual - expected)
    if missing or additional:
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(repr(item) for item in missing))
        if additional:
            details.append("additional " + ", ".join(repr(item) for item in additional))
        raise MacroProtocolError(f"{label} has " + "; ".join(details))
    return value


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise MacroProtocolError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise MacroProtocolError(f"non-finite JSON number {value!r}")


def _dispatch_bounds_object(bounds: DispatchBounds) -> dict[str, int]:
    checked = DispatchBounds(
        bounds.max_steps,
        bounds.max_wall_time_ms,
        bounds.max_memory_bytes,
        bounds.max_output_bytes,
    )
    return {
        "max_steps": checked.max_steps,
        "max_wall_time_ms": checked.max_wall_time_ms,
        "max_memory_bytes": checked.max_memory_bytes,
        "max_output_bytes": checked.max_output_bytes,
    }


def macro_object(action: Macro) -> dict[str, object]:
    """Return the detached, exact v1 JSON object for one typed action."""

    common: dict[str, object] = {
        "format": MACRO_FORMAT,
        "v": MACRO_VERSION,
    }
    if type(action) is Use:
        checked = Use(action.name, action.specializations)
        return {
            **common,
            "action": "Use",
            "name": checked.name,
            "specializations": list(checked.specializations),
        }
    if type(action) is Cut:
        checked = Cut(action.kind, action.name, action.formula)
        return {
            **common,
            "action": "Cut",
            "kind": checked.kind,
            "name": checked.name,
            "formula": checked.formula,
        }
    if type(action) is Witness:
        checked = Witness(action.term)
        return {**common, "action": "Witness", "term": checked.term}
    if type(action) is Induct:
        checked = Induct(action.variable, action.motive)
        return {
            **common,
            "action": "Induct",
            "variable": checked.variable,
            "motive": checked.motive,
        }
    if type(action) is Rewrite:
        checked = Rewrite(action.source, action.direction, action.location)
        return {
            **common,
            "action": "Rewrite",
            "source": checked.source,
            "direction": checked.direction,
            "location": checked.location,
        }
    if type(action) is Split:
        checked = Split(action.kind)
        return {**common, "action": "Split", "kind": checked.kind}
    if type(action) is Dispatch:
        checked = Dispatch(action.solver, action.premises, action.bounds)
        return {
            **common,
            "action": "Dispatch",
            "solver": checked.solver,
            "premises": list(checked.premises),
            "bounds": _dispatch_bounds_object(checked.bounds),
        }
    raise MacroProtocolError("expected one exact Peano Hydra macro action")


def serialize_macro(action: Macro) -> str:
    """Serialize one action as its sole canonical compact JSON spelling."""

    try:
        encoded = json.dumps(
            macro_object(action),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        size = len(encoded.encode("utf-8"))
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise MacroProtocolError(f"macro is not strict JSON: {exc}") from None
    if size > MAX_MACRO_BYTES:
        raise MacroProtocolError(
            f"canonical macro exceeds the {MAX_MACRO_BYTES}-byte transport limit"
        )
    return encoded


def macro_sha256(action: Macro) -> str:
    """Hash the exact UTF-8 canonical serialization, without a line feed."""

    return hashlib.sha256(serialize_macro(action).encode("utf-8")).hexdigest()


def _parse_bounds(value: object) -> DispatchBounds:
    fields = _expect_fields("Dispatch.bounds", value, _BOUND_FIELDS)
    return DispatchBounds(
        max_steps=fields["max_steps"],  # type: ignore[arg-type]
        max_wall_time_ms=fields["max_wall_time_ms"],  # type: ignore[arg-type]
        max_memory_bytes=fields["max_memory_bytes"],  # type: ignore[arg-type]
        max_output_bytes=fields["max_output_bytes"],  # type: ignore[arg-type]
    )


def parse_macro(source: str | bytes) -> Macro:
    """Parse strict JSON and return one immutable, canonical typed action.

    JSON layout whitespace and key order are accepted because a proposal trace
    must retain the model's raw text separately.  Embedded PA terms and
    formulas, however, must already use the profile's canonical surface form.
    :func:`serialize_macro` supplies the unique canonical wire spelling.
    """

    if type(source) is str:
        # UTF-8 uses at least one byte per code point.  This cheap preflight
        # rejects arbitrarily large text before making an equally large byte
        # copy; the byte-precise check below remains authoritative.
        if len(source) > MAX_MACRO_BYTES:
            raise MacroProtocolError(
                f"macro source exceeds the {MAX_MACRO_BYTES}-byte transport limit"
            )
        try:
            raw = source.encode("utf-8")
        except UnicodeEncodeError:
            raise MacroProtocolError("macro text is not valid UTF-8") from None
    elif type(source) is bytes:
        raw = source
    else:
        raise MacroProtocolError("macro source must be text or UTF-8 bytes")
    if not raw:
        raise MacroProtocolError("macro source must not be empty")
    if len(raw) > MAX_MACRO_BYTES:
        raise MacroProtocolError(
            f"macro source exceeds the {MAX_MACRO_BYTES}-byte transport limit"
        )
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except MacroProtocolError:
        raise
    except (
        UnicodeDecodeError,
        json.JSONDecodeError,
        ValueError,
        RecursionError,
    ) as exc:
        raise MacroProtocolError(f"macro source is not strict JSON: {exc}") from None
    if type(value) is not dict:
        raise MacroProtocolError("macro must be one exact JSON object")
    if value.get("format") != MACRO_FORMAT:
        raise MacroProtocolError(f"unsupported macro format {value.get('format')!r}")
    version = value.get("v")
    if type(version) is not int or version != MACRO_VERSION:
        raise MacroProtocolError(f"unsupported macro version {version!r}")
    tag = value.get("action")
    if type(tag) is not str or tag not in _ACTION_FIELDS:
        raise MacroProtocolError(f"unsupported macro action {tag!r}")
    fields = _expect_fields(f"{tag} macro", value, _ACTION_FIELDS[tag])

    if tag == "Use":
        if type(fields["specializations"]) is not list:
            raise MacroProtocolError("Use.specializations must be a JSON array")
        return Use(  # type: ignore[arg-type]
            fields["name"], tuple(fields["specializations"])
        )
    if tag == "Cut":
        return Cut(  # type: ignore[arg-type]
            fields["kind"], fields["name"], fields["formula"]
        )
    if tag == "Witness":
        return Witness(fields["term"])  # type: ignore[arg-type]
    if tag == "Induct":
        return Induct(fields["variable"], fields["motive"])  # type: ignore[arg-type]
    if tag == "Rewrite":
        location = fields["location"]
        if location is not None and type(location) is not str:
            raise MacroProtocolError("Rewrite.location must be null or a name")
        return Rewrite(
            fields["source"],  # type: ignore[arg-type]
            fields["direction"],  # type: ignore[arg-type]
            location,
        )
    if tag == "Split":
        return Split(fields["kind"])  # type: ignore[arg-type]
    if type(fields["premises"]) is not list:
        raise MacroProtocolError("Dispatch.premises must be a JSON array")
    return Dispatch(
        fields["solver"],  # type: ignore[arg-type]
        tuple(fields["premises"]),
        _parse_bounds(fields["bounds"]),
    )


def _available_solver_set(value: Collection[str]) -> frozenset[str]:
    if type(value) not in (tuple, list, set, frozenset):
        raise MacroCompileError(
            "available_solvers must be an exact tuple, list, set, or frozenset"
        )
    solvers = frozenset(value)
    try:
        return frozenset(_solver_name(solver) for solver in solvers)
    except MacroProtocolError as exc:
        raise MacroCompileError(f"available_solvers is malformed: {exc}") from None


def _require_command(capabilities: SurfaceCapabilities, name: str) -> None:
    allowed = capabilities.allowed_commands
    if allowed is not None and name not in allowed:
        raise MacroCompileError(
            f"public command {name!r} is unavailable in capability environment "
            f"{capabilities.label!r}"
        )


def _compiled_line(line: str) -> str:
    if len(line) > MAX_INPUT:
        raise MacroCompileError(
            f"compiled public command exceeds the {MAX_INPUT}-character surface limit"
        )
    if line != line.strip() or line.splitlines() != [line]:
        raise MacroCompileError("compiler produced a non-canonical physical command")
    dangerous = oversized_numeral(line)
    if dangerous is not None:
        raise MacroCompileError(
            f"compiler produced resource-dangerous numeral {dangerous}"
        )
    return line


def compile_macro(
    action: Macro,
    *,
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
    available_solvers: Collection[str] = (),
) -> CompiledMacro:
    """Compile an action without executing tactics or constructing evidence.

    ``available_solvers`` is an explicit registry owned by the caller.  It is
    empty by default, so an unregistered external process can never be selected
    merely by naming it in model output.
    """

    if type(capabilities) is not SurfaceCapabilities:
        raise MacroCompileError(
            "capabilities must be one exact SurfaceCapabilities value"
        )
    # Revalidate even an action forged by bypassing a dataclass constructor.
    action = parse_macro(serialize_macro(action))

    commands: tuple[str, ...]
    if type(action) is Use:
        _require_command(capabilities, "use")
        if action.name not in SURFACE_THEOREM_NAMES:
            raise MacroCompileError(
                f"no checked public theorem {action.name!r} is available"
            )
        allowed_theorems = capabilities.allowed_theorems
        if allowed_theorems is not None and action.name not in allowed_theorems:
            raise MacroCompileError(
                f"public theorem {action.name!r} is unavailable in capability "
                f"environment {capabilities.label!r}"
            )
        if action.specializations:
            _require_command(capabilities, "specialize")
        commands = (f"use {action.name}",) + tuple(
            f"specialize {action.name} {term}"
            for term in action.specializations
        )
    elif type(action) is Cut:
        _require_command(capabilities, action.kind)
        commands = (f"{action.kind} {action.name} : {action.formula}",)
    elif type(action) is Witness:
        _require_command(capabilities, "exists")
        commands = (f"exists {action.term}",)
    elif type(action) is Induct:
        _require_command(capabilities, "induction")
        commands = (f"induction {action.variable}",)
    elif type(action) is Rewrite:
        _require_command(capabilities, "rewrite")
        arrow = "<- " if action.direction == "backward" else ""
        location = f" at {action.location}" if action.location is not None else ""
        commands = (f"rewrite {arrow}{action.source}{location}",)
    elif type(action) is Split:
        command = {
            "conjunction": "split",
            "left": "left",
            "right": "right",
        }[action.kind]
        _require_command(capabilities, command)
        commands = (command,)
    elif type(action) is Dispatch:
        if action.solver not in _available_solver_set(available_solvers):
            raise MacroCompileError(
                f"untrusted solver {action.solver!r} is not registered"
            )
        request = DispatchRequest(action.solver, action.premises, action.bounds)
        return CompiledMacro(action, (), request)
    else:  # pragma: no cover - parse/serialize has already made this exhaustive
        raise MacroCompileError("unsupported typed macro action")

    return CompiledMacro(
        action,
        tuple(_compiled_line(command) for command in commands),
        None,
    )


__all__ = [
    "MACRO_FORMAT",
    "MACRO_VERSION",
    "MACRO_PROTOCOL_FORMAT",
    "MACRO_PROTOCOL_VERSION",
    "MACRO_PROTOCOL_ID",
    "MACRO_PROTOCOL_PATH",
    "MACRO_PROTOCOL_DOCUMENT_SHA256",
    "MACRO_PROTOCOL_SEMANTIC_SHA256",
    "DISPATCH_CALL_FORMAT",
    "DISPATCH_CALL_VERSION",
    "DISPATCH_RESPONSE_FORMAT",
    "DISPATCH_RESPONSE_VERSION",
    "DISPATCH_RESPONSE_STATUSES",
    "MAX_MACRO_BYTES",
    "MAX_NAME_CHARS",
    "MAX_SPECIALIZATIONS",
    "MAX_DISPATCH_PREMISES",
    "MAX_DISPATCH_STEPS",
    "MAX_DISPATCH_WALL_TIME_MS",
    "MAX_DISPATCH_MEMORY_BYTES",
    "MAX_DISPATCH_OUTPUT_BYTES",
    "MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES",
    "MAX_DISPATCH_COMMANDS",
    "MAX_DISPATCH_CONFIGURATION_BYTES",
    "MAX_DISPATCH_REQUEST_BYTES",
    "MAX_DISPATCH_CALL_BYTES",
    "MAX_DISPATCH_ARTIFACT_BYTES",
    "MAX_MACRO_TRACE_BYTES",
    "MAX_OWNER_REPLAY_STEPS",
    "MAX_DISPATCH_STATUS_CHARS",
    "MAX_ERROR_CHARS",
    "MAX_ERROR_UTF8_BYTES",
    "MAX_FINAL_ARTIFACT_BYTES",
    "MacroProtocolError",
    "MacroCompileError",
    "Use",
    "Cut",
    "Witness",
    "Induct",
    "Rewrite",
    "Split",
    "DispatchBounds",
    "Dispatch",
    "Macro",
    "DispatchRequest",
    "CompiledMacro",
    "macro_object",
    "serialize_macro",
    "macro_sha256",
    "parse_macro",
    "compile_macro",
    "load_macro_protocol",
    "macro_protocol_identity",
]
