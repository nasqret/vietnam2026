"""Transactional execution for the untrusted Peano Hydra macro protocol.

The objects in :mod:`training.peano_hydra.macros` are transport messages, not
proof rules.  This module is the equally untrusted bridge from those messages
to Peano Lab's documented surface.  Every ordinary action is executed through
``run_surface`` and every closed state is replayed from the owner-held original
goal before ``checked_surface_final`` invokes the independent kernel.

One call is one transaction.  All public commands first run against immutable
temporary owners with engine tracing disabled.  If parsing, contextual
validation, compilation, a solver adapter, one reconstructed command, or the
fresh final replay fails, :class:`MacroExecutionError.owner` is the *identical*
owner supplied by the caller.  In particular, neither its state/history nor
its mutable browser trace logger is touched.

``Dispatch`` is intentionally weak.  A registered adapter receives mandatory
typed bounds and canonical premises, but its status and transcript have no
proof authority.  It must return at least one complete public command.  Those
commands are bounded, capability-checked, executed normally, and—at closure—
freshly replayed through the original-goal kernel boundary.
"""

from __future__ import annotations

from base64 import b64decode, b64encode
import ctypes
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import NoReturn
import unicodedata

from peano_lab.engine.state import (
    Goal,
    apply_formula_subst,
    proof_metrics,
    start,
)
from peano_lab.engine.tactics import TacticError
from peano_lab.engine.trace import TraceLogger, render_goals
from peano_lab.kernel.artifact_codec import encode_artifact_bounded
from peano_lab.kernel.checker import axiom_formula, check
from peano_lab.kernel.formulas import ParseError, parse_formula_with_names, pretty_formula
from peano_lab.kernel.proofs import Proof
from peano_lab.kernel.terms import parse_term_with_names
from peano_lab.library.theorems import get as get_theorem
from peano_lab.ui.prove import (
    MAX_INPUT,
    FULL_SURFACE_CAPABILITIES,
    ProofSession,
    SURFACE_COMMAND_NAMES,
    SURFACE_THEOREM_NAMES,
    SurfaceCapabilities,
    checked_surface_final,
    oversized_numeral,
    run_surface,
    surface_transaction_name,
)
from training.peano_policy.search import state_sha256 as goal_state_sha256

from .macros import (
    DISPATCH_CALL_FORMAT,
    DISPATCH_CALL_VERSION,
    DISPATCH_RESPONSE_FORMAT,
    DISPATCH_RESPONSE_STATUSES,
    DISPATCH_RESPONSE_VERSION,
    MAX_MACRO_BYTES,
    MAX_DISPATCH_ARTIFACT_BYTES,
    MAX_DISPATCH_CALL_BYTES,
    MAX_DISPATCH_COMMANDS,
    MAX_DISPATCH_CONFIGURATION_BYTES,
    MAX_DISPATCH_MEMORY_BYTES,
    MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES,
    MAX_DISPATCH_OUTPUT_BYTES,
    MAX_DISPATCH_PREMISES,
    MAX_DISPATCH_REQUEST_BYTES,
    MAX_DISPATCH_STATUS_CHARS,
    MAX_DISPATCH_STEPS,
    MAX_DISPATCH_WALL_TIME_MS,
    MAX_ERROR_CHARS,
    MAX_ERROR_UTF8_BYTES,
    MAX_FINAL_ARTIFACT_BYTES,
    MAX_MACRO_TRACE_BYTES,
    MAX_OWNER_REPLAY_STEPS,
    CompiledMacro,
    Cut,
    Dispatch,
    DispatchBounds,
    DispatchRequest,
    Induct,
    Macro,
    MacroCompileError,
    MacroProtocolError,
    Rewrite,
    Split,
    Use,
    Witness,
    compile_macro,
    macro_object,
    macro_protocol_identity,
    macro_sha256,
    load_macro_protocol,
    parse_macro,
)
from .profile import canonical_profile_theorem, semantic_profile_identity


MACRO_TRACE_FORMAT = "peano-hydra-macro-trace"
MACRO_TRACE_VERSION = 1
DISPATCH_ADAPTER_IDENTITY_FORMAT = "peano-hydra-dispatch-adapter"
DISPATCH_ADAPTER_IDENTITY_VERSION = 1
DISPATCH_STEP_ACCOUNTING = "untrusted-adapter-reported-not-host-enforced"
LINUX_MEMORY_ENFORCEMENT = "linux-rlimit-as-data+sampled-leader-rss"
DARWIN_MEMORY_ENFORCEMENT = "darwin-sampled-leader-rss-only"
_DISPATCH_RESOURCE_SEMANTICS = {
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
        LINUX_MEMORY_ENFORCEMENT: {
            "platform": "linux",
            "hard_ceiling": True,
            "campaign_host_eligible": True,
            "reported_peak_semantics": "maximum-sampled-leader-rss-not-exact-peak",
            "campaign_peak_metric_eligible": False,
        },
        DARWIN_MEMORY_ENFORCEMENT: {
            "platform": "darwin",
            "hard_ceiling": False,
            "campaign_host_eligible": False,
            "reported_peak_semantics": "maximum-sampled-leader-rss-not-exact-peak",
            "campaign_peak_metric_eligible": False,
        },
    },
}
_ACTION_NAMES = ("Use", "Cut", "Witness", "Induct", "Rewrite", "Split", "Dispatch")
_UNSAFE_CATEGORIES = frozenset({"Cc", "Cf", "Cs", "Zl", "Zp"})
_SESSION_COMMANDS = frozenset(
    {
        "?",
        ":t",
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
)
_SOLVER_NAME = re.compile(r"[a-z][a-z0-9._-]*\Z", re.ASCII)
_TRACE_FIELDS = frozenset(
    {
        "format",
        "v",
        "environment",
        "raw_proposal",
        "parse",
        "compile",
        "state_before",
        "intermediate_states",
        "solver",
        "state_after",
        "outcome",
        "final_replay",
    }
)
_ENVIRONMENT_FIELDS = frozenset(
    {
        "classical",
        "logic",
        "semantic_profile_identity",
        "original_theorem",
        "original_theorem_sha256",
        "owner_capability_identity",
        "owner_capability_sha256",
        "capability_label",
        "allowed_actions",
        "allowed_commands",
        "allowed_theorems",
        "registered_solvers",
        "registered_adapter_identities",
        "effective_command_capability",
        "effective_theorem_capability",
        "macro_protocol_identity",
    }
)
_RAW_FIELDS = frozenset({"encoding", "text", "base64", "bytes", "sha256"})
_PARSE_FIELDS = frozenset(
    {"status", "canonical", "canonical_sha256", "error"}
)
_COMPILE_FIELDS = frozenset(
    {"status", "public_commands", "dispatch", "dispatch_request_sha256", "error"}
)
_STATE_FIELDS = frozenset(
    {
        "closed",
        "goals",
        "goals_sha256",
        "history",
        "replay",
        "state_sha256",
    }
)
_STATE_SUMMARY_FIELDS = frozenset(
    {
        "closed",
        "goals",
        "goals_sha256",
        "history_length",
        "replay_length",
        "summary_sha256",
    }
)
_INTERMEDIATE_FIELDS = frozenset({"command_index", "command", "state_summary"})
_REQUEST_FIELDS = frozenset(
    {"solver", "premises", "bounds", "authority"}
)
_BOUNDS_FIELDS = frozenset(
    {"max_steps", "max_wall_time_ms", "max_memory_bytes", "max_output_bytes"}
)
_SOLVER_FIELDS = frozenset(
    {
        "request",
        "request_sha256",
        "dispatch_call_request_sha256",
        "context",
        "response_status",
        "response_steps_used",
        "raw_response_base64",
        "raw_response_bytes",
        "raw_response_sha256",
        "host_usage",
        "reconstructed_commands",
        "error",
        "authority",
        "adapter_identity",
        "adapter_identity_sha256",
        "adapter_configuration",
        "dispatch_call_sha256",
        "step_accounting",
    }
)
_SOLVER_CONTEXT_FIELDS = frozenset({"original_theorem", "goals", "premises"})
_PREMISE_FIELDS = frozenset({"name", "kind", "formula"})
_HOST_USAGE_FIELDS = frozenset(
    {
        "campaign_host_eligible",
        "wall_time_ms",
        "output_bytes",
        "reconstructed_command_bytes",
        "max_observed_rss_bytes",
        "peak_processes",
        "exit_code",
        "timed_out",
        "wall_limit_ms",
        "memory_limit_bytes",
        "output_limit_bytes",
        "process_limit",
        "memory_enforcement",
        "process_enforcement",
    }
)
_OUTCOME_FIELDS = frozenset({"status", "error"})
_FINAL_REPLAY_FIELDS = frozenset(
    {
        "status",
        "fresh",
        "original_theorem",
        "commands",
        "kernel_accepted",
        "certificate_representation",
        "certificate_sha256",
        "certificate_nodes",
        "certificate_depth",
        "error",
    }
)
_ADAPTER_IDENTITY_FIELDS = frozenset(
    {
        "format",
        "v",
        "adapter",
        "artifact_kind",
        "artifact_sha256",
        "configuration_sha256",
    }
)
_EFFECTIVE_CAPABILITY_FIELDS = frozenset({"format", "v", "count", "sha256"})
_MACRO_PROTOCOL_IDENTITY_FIELDS = frozenset(
    {"format", "v", "id", "semantic_sha256", "document_sha256"}
)
_OWNER_CAPABILITY_FIELDS = frozenset(
    {
        "format",
        "v",
        "label",
        "declared_commands",
        "declared_theorems",
        "effective_command_capability",
        "effective_theorem_capability",
    }
)
_DISPATCH_CALL_FIELDS = frozenset(
    {
        "format",
        "v",
        "adapter_identity",
        "configuration",
        "request",
        "request_sha256",
        "context",
    }
)
_DISPATCH_RESPONSE_FIELDS = frozenset(
    {"format", "v", "status", "steps_used", "public_commands"}
)


class MacroRunnerError(RuntimeError):
    """A contextual macro execution is malformed or cannot be authorized."""


class DispatchProtocolError(MacroRunnerError):
    """An untrusted dispatch adapter violated its reconstruction contract."""


def _sha256_text(label: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise DispatchProtocolError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise DispatchProtocolError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise DispatchProtocolError(f"non-finite JSON number {value!r}")


def _file_sha256_bounded(path: Path, maximum: int) -> str:
    try:
        metadata = path.stat()
        if not stat.S_ISREG(metadata.st_mode) or not 1 <= metadata.st_size <= maximum:
            raise DispatchProtocolError("dispatch artifact is not one bounded regular file")
        digest = hashlib.sha256()
        observed = 0
        with path.open("rb") as source:
            while True:
                chunk = source.read(1024 * 1024)
                if not chunk:
                    break
                observed += len(chunk)
                if observed > maximum:
                    raise DispatchProtocolError("dispatch artifact exceeds its byte limit")
                digest.update(chunk)
    except OSError as exc:
        raise DispatchProtocolError(f"cannot hash dispatch artifact: {exc}") from None
    if observed != metadata.st_size:
        raise DispatchProtocolError("dispatch artifact changed while being hashed")
    return digest.hexdigest()


@dataclass(frozen=True, slots=True)
class DispatchAdapterIdentity:
    """Pinned executable/source and configuration identity for one adapter.

    ``artifact_kind`` distinguishes a native executable hash from a source
    bundle hash.  The identity does not assert that either artifact is sound;
    it makes the exact untrusted component reproducible and prevents a trace
    from silently referring to a different program under the same solver name.
    """

    adapter: str
    artifact_kind: str
    artifact_sha256: str
    configuration_sha256: str
    format: str = DISPATCH_ADAPTER_IDENTITY_FORMAT
    v: int = DISPATCH_ADAPTER_IDENTITY_VERSION

    def __post_init__(self) -> None:
        if (
            type(self.format) is not str
            or self.format != DISPATCH_ADAPTER_IDENTITY_FORMAT
            or type(self.v) is not int
            or self.v != DISPATCH_ADAPTER_IDENTITY_VERSION
        ):
            raise DispatchProtocolError("unsupported dispatch adapter identity")
        if (
            type(self.adapter) is not str
            or len(self.adapter) > 128
            or _SOLVER_NAME.fullmatch(self.adapter) is None
        ):
            raise DispatchProtocolError("adapter must be one canonical solver token")
        if type(self.artifact_kind) is not str or self.artifact_kind not in {
            "binary",
            "source",
        }:
            raise DispatchProtocolError(
                "artifact_kind must be exactly 'binary' or 'source'"
            )
        _sha256_text("artifact_sha256", self.artifact_sha256)
        _sha256_text("configuration_sha256", self.configuration_sha256)

    def to_dict(self) -> dict[str, object]:
        # Reconstruct to reject a forged dataclass instance before publication.
        checked = DispatchAdapterIdentity(
            self.adapter,
            self.artifact_kind,
            self.artifact_sha256,
            self.configuration_sha256,
            self.format,
            self.v,
        )
        return {
            "format": checked.format,
            "v": checked.v,
            "adapter": checked.adapter,
            "artifact_kind": checked.artifact_kind,
            "artifact_sha256": checked.artifact_sha256,
            "configuration_sha256": checked.configuration_sha256,
        }

    @classmethod
    def from_object(cls, value: object) -> "DispatchAdapterIdentity":
        fields = _exact_object(
            "dispatch adapter identity", value, _ADAPTER_IDENTITY_FIELDS
        )
        return cls(
            adapter=fields["adapter"],  # type: ignore[arg-type]
            artifact_kind=fields["artifact_kind"],  # type: ignore[arg-type]
            artifact_sha256=fields["artifact_sha256"],  # type: ignore[arg-type]
            configuration_sha256=fields["configuration_sha256"],  # type: ignore[arg-type]
            format=fields["format"],  # type: ignore[arg-type]
            v=fields["v"],  # type: ignore[arg-type]
        )

    @property
    def canonical_json(self) -> str:
        return _canonical_json(self.to_dict())

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class DispatchHostUsage:
    """Host-observed process evidence; it grants no logical authority."""

    wall_time_ms: int
    output_bytes: int
    reconstructed_command_bytes: int
    max_observed_rss_bytes: int
    peak_processes: int
    exit_code: int | None
    timed_out: bool
    wall_limit_ms: int
    memory_limit_bytes: int
    output_limit_bytes: int
    process_limit: int
    memory_enforcement: str
    process_enforcement: str
    campaign_host_eligible: bool

    def __post_init__(self) -> None:
        for label, value in (
            ("wall_time_ms", self.wall_time_ms),
            ("output_bytes", self.output_bytes),
            ("reconstructed_command_bytes", self.reconstructed_command_bytes),
            ("max_observed_rss_bytes", self.max_observed_rss_bytes),
            ("peak_processes", self.peak_processes),
            ("wall_limit_ms", self.wall_limit_ms),
            ("memory_limit_bytes", self.memory_limit_bytes),
            ("output_limit_bytes", self.output_limit_bytes),
            ("process_limit", self.process_limit),
        ):
            if type(value) is not int or value < 0:
                raise DispatchProtocolError(
                    f"dispatch host {label} must be a non-negative exact integer"
                )
        if self.process_limit != 1:
            raise DispatchProtocolError("dispatch host process_limit must be exactly 1")
        if self.exit_code is not None and type(self.exit_code) is not int:
            raise DispatchProtocolError("dispatch host exit_code must be an integer or null")
        if type(self.timed_out) is not bool:
            raise DispatchProtocolError("dispatch host timed_out must be a Boolean")
        if self.memory_enforcement not in {
            LINUX_MEMORY_ENFORCEMENT,
            DARWIN_MEMORY_ENFORCEMENT,
        }:
            raise DispatchProtocolError("dispatch host memory enforcement is unsupported")
        if self.process_enforcement != "rlimit-nproc-one":
            raise DispatchProtocolError("dispatch host process enforcement is unsupported")
        if type(self.campaign_host_eligible) is not bool:
            raise DispatchProtocolError(
                "dispatch host campaign_host_eligible must be a Boolean"
            )
        expected_eligibility = (
            self.memory_enforcement == LINUX_MEMORY_ENFORCEMENT
        )
        if self.campaign_host_eligible is not expected_eligibility:
            raise DispatchProtocolError(
                "dispatch host campaign eligibility disagrees with memory enforcement"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "wall_time_ms": self.wall_time_ms,
            "output_bytes": self.output_bytes,
            "reconstructed_command_bytes": self.reconstructed_command_bytes,
            "max_observed_rss_bytes": self.max_observed_rss_bytes,
            "peak_processes": self.peak_processes,
            "exit_code": self.exit_code,
            "timed_out": self.timed_out,
            "wall_limit_ms": self.wall_limit_ms,
            "memory_limit_bytes": self.memory_limit_bytes,
            "output_limit_bytes": self.output_limit_bytes,
            "process_limit": self.process_limit,
            "memory_enforcement": self.memory_enforcement,
            "process_enforcement": self.process_enforcement,
            "campaign_host_eligible": self.campaign_host_eligible,
        }


@dataclass(frozen=True, slots=True)
class DispatchResponse:
    """Parsed inert subprocess response; status remains wholly untrusted."""

    status: str
    steps_used: int
    public_commands: tuple[str, ...]
    raw_response: bytes
    host_usage: DispatchHostUsage

    def __post_init__(self) -> None:
        if type(self.status) is not str or not self.status:
            raise DispatchProtocolError("dispatch status must be non-empty text")
        if self.status not in DISPATCH_RESPONSE_STATUSES:
            raise DispatchProtocolError("dispatch status is not a registered v1 enum value")
        if (
            len(self.status) > MAX_DISPATCH_STATUS_CHARS
            or self.status != self.status.strip()
            or self.status.splitlines() != [self.status]
            or any(
                unicodedata.category(character) in _UNSAFE_CATEGORIES
                for character in self.status
            )
        ):
            raise DispatchProtocolError("dispatch status must be one safe bounded line")
        if type(self.steps_used) is not int or self.steps_used < 0:
            raise DispatchProtocolError("dispatch steps_used must be a non-negative integer")
        if type(self.public_commands) is not tuple or not all(
            type(command) is str for command in self.public_commands
        ):
            raise DispatchProtocolError("dispatch public_commands must be an exact text tuple")
        if len(self.public_commands) > MAX_DISPATCH_COMMANDS:
            raise DispatchProtocolError(
                f"dispatch returned more than {MAX_DISPATCH_COMMANDS} commands"
            )
        if type(self.raw_response) is not bytes:
            raise DispatchProtocolError("dispatch raw_response must be exact bytes")
        if type(self.host_usage) is not DispatchHostUsage:
            raise DispatchProtocolError("dispatch host_usage must be DispatchHostUsage")
        if self.host_usage.output_bytes != len(self.raw_response):
            raise DispatchProtocolError("host output byte accounting is inconsistent")


@dataclass(frozen=True, slots=True)
class DispatchPremise:
    """One canonical premise disclosed to an untrusted solver adapter."""

    name: str
    kind: str
    formula: str

    def __post_init__(self) -> None:
        if (
            type(self.name) is not str
            or not self.name
            or len(self.name) > 128
            or self.name != self.name.strip()
        ):
            raise DispatchProtocolError("dispatch premise name is malformed")
        if type(self.kind) is not str or self.kind not in {
            "hypothesis",
            "pa-axiom",
            "public-theorem",
        }:
            raise DispatchProtocolError("dispatch premise kind is unsupported")
        if type(self.formula) is not str or not self.formula:
            raise DispatchProtocolError("dispatch premise formula is malformed")

    def to_dict(self) -> dict[str, str]:
        return {"name": self.name, "kind": self.kind, "formula": self.formula}


@dataclass(frozen=True, slots=True)
class DispatchContext:
    """The exact canonical state projection supplied to an adapter."""

    original_theorem: str
    goals: tuple[str, ...]
    premises: tuple[DispatchPremise, ...]

    def __post_init__(self) -> None:
        if type(self.original_theorem) is not str or not self.original_theorem:
            raise DispatchProtocolError("dispatch context original theorem is malformed")
        if type(self.goals) is not tuple or not all(
            type(goal) is str and bool(goal) for goal in self.goals
        ):
            raise DispatchProtocolError("dispatch context goals must be an exact text tuple")
        if type(self.premises) is not tuple or not all(
            type(premise) is DispatchPremise for premise in self.premises
        ):
            raise DispatchProtocolError(
                "dispatch context premises must be exact DispatchPremise values"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "original_theorem": self.original_theorem,
            "goals": list(self.goals),
            "premises": [premise.to_dict() for premise in self.premises],
        }


@dataclass(frozen=True, slots=True)
class DispatchAdapterRegistration:
    """A verified executable/source artifact and canonical configuration.

    No callback is accepted.  Invocation always occurs in a fresh bounded
    subprocess receiving detached JSON, so adapter code cannot obtain a
    ``ProofSession`` reference or mutate its trace logger.
    """

    identity: DispatchAdapterIdentity
    artifact_path: str
    configuration_json: str

    def __post_init__(self) -> None:
        if type(self.identity) is not DispatchAdapterIdentity:
            raise DispatchProtocolError(
                "dispatch registration identity must be DispatchAdapterIdentity"
            )
        DispatchAdapterIdentity.from_object(self.identity.to_dict())
        if type(self.artifact_path) is not str or not self.artifact_path:
            raise DispatchProtocolError(
                "dispatch registration needs an absolute artifact path"
            )
        path = Path(self.artifact_path)
        if not path.is_absolute():
            raise DispatchProtocolError("dispatch artifact path must be absolute")
        try:
            resolved = path.resolve(strict=True)
            metadata = resolved.stat()
        except OSError as exc:
            raise DispatchProtocolError(f"cannot inspect dispatch artifact: {exc}") from None
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_DISPATCH_ARTIFACT_BYTES:
            raise DispatchProtocolError("dispatch artifact is not one bounded regular file")
        if metadata.st_size < 1 or not os.access(resolved, os.X_OK):
            raise DispatchProtocolError("dispatch artifact must be non-empty and executable")
        object.__setattr__(self, "artifact_path", str(resolved))
        if type(self.configuration_json) is not str:
            raise DispatchProtocolError("dispatch configuration must be canonical JSON text")
        try:
            config_bytes = self.configuration_json.encode("utf-8")
            config = json.loads(
                self.configuration_json,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_json_constant,
            )
        except (UnicodeEncodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
            raise DispatchProtocolError(f"invalid dispatch configuration: {exc}") from None
        if type(config) is not dict or len(config_bytes) > MAX_DISPATCH_CONFIGURATION_BYTES:
            raise DispatchProtocolError("dispatch configuration must be one bounded JSON object")
        if _canonical_json(config) != self.configuration_json:
            raise DispatchProtocolError("dispatch configuration JSON is not canonical")
        self.verify_identity()

    def verify_identity(self) -> None:
        artifact_sha256 = _file_sha256_bounded(
            Path(self.artifact_path), MAX_DISPATCH_ARTIFACT_BYTES
        )
        configuration_sha256 = hashlib.sha256(
            self.configuration_json.encode("utf-8")
        ).hexdigest()
        if artifact_sha256 != self.identity.artifact_sha256:
            raise DispatchProtocolError("dispatch artifact identity mismatch")
        if configuration_sha256 != self.identity.configuration_sha256:
            raise DispatchProtocolError("dispatch configuration identity mismatch")

    @property
    def configuration(self) -> dict[str, object]:
        value = json.loads(self.configuration_json)
        if type(value) is not dict:  # pragma: no cover - constructor invariant
            raise RuntimeError("dispatch configuration lost its object shape")
        return value


def register_dispatch_subprocess(
    adapter: str,
    *,
    artifact_kind: str,
    artifact_path: str | Path,
    configuration: dict[str, object],
) -> DispatchAdapterRegistration:
    """Derive, verify, and bind one subprocess adapter registration."""

    if type(configuration) is not dict:
        raise DispatchProtocolError("dispatch configuration must be an exact dict")
    configuration_json = _canonical_json(configuration)
    path = Path(artifact_path).resolve(strict=True)
    identity = DispatchAdapterIdentity(
        adapter=adapter,
        artifact_kind=artifact_kind,
        artifact_sha256=_file_sha256_bounded(path, MAX_DISPATCH_ARTIFACT_BYTES),
        configuration_sha256=hashlib.sha256(
            configuration_json.encode("utf-8")
        ).hexdigest(),
    )
    return DispatchAdapterRegistration(identity, str(path), configuration_json)


@dataclass(frozen=True, slots=True)
class MacroOwner:
    """Stable proof owner plus immutable profile/capability authority."""

    session: ProofSession
    capabilities: SurfaceCapabilities
    capability_identity_json: str
    semantic_profile_identity_json: str

    def __post_init__(self) -> None:
        if type(self.session) is not ProofSession:
            raise TypeError("macro owner needs an exact ProofSession")
        if type(self.capabilities) is not SurfaceCapabilities:
            raise TypeError("macro owner needs exact SurfaceCapabilities")
        expected_capability = _canonical_json(_capability_identity(self.capabilities))
        if self.capability_identity_json != expected_capability:
            raise MacroRunnerError("macro owner capability identity mismatch")
        expected_profile = _canonical_json(semantic_profile_identity())
        if self.semantic_profile_identity_json != expected_profile:
            raise MacroRunnerError("macro owner semantic profile identity mismatch")
        if self.session.classical:
            raise MacroRunnerError("macro owners cannot carry classical authority")

    @property
    def state(self):
        return self.session.state

    @property
    def replay_steps(self):
        return self.session.replay_steps

    @property
    def trace(self):
        return self.session.trace

    @property
    def original_target(self):
        return self.session.original_target

    @property
    def original_names(self):
        return self.session.original_names

    @property
    def classical(self) -> bool:
        return self.session.classical

    @property
    def capability_identity(self) -> dict[str, object]:
        value = json.loads(self.capability_identity_json)
        if type(value) is not dict:  # pragma: no cover
            raise RuntimeError("macro owner capability identity lost object shape")
        return value

    @property
    def capability_sha256(self) -> str:
        return hashlib.sha256(self.capability_identity_json.encode("utf-8")).hexdigest()

    @property
    def profile_identity(self) -> dict[str, object]:
        value = json.loads(self.semantic_profile_identity_json)
        if type(value) is not dict:  # pragma: no cover
            raise RuntimeError("macro owner profile identity lost object shape")
        return value

    def with_session(self, session: ProofSession) -> "MacroOwner":
        if type(session) is not ProofSession:
            raise TypeError("macro owner successor needs an exact ProofSession")
        if (
            session.original_target != self.session.original_target
            or session.original_names != self.session.original_names
            or session.classical
        ):
            raise MacroRunnerError("macro successor changed owner-held authority")
        return MacroOwner(
            session,
            self.capabilities,
            self.capability_identity_json,
            self.semantic_profile_identity_json,
        )


@dataclass(frozen=True, slots=True)
class MacroTrace:
    """Canonical exact-field record for one accepted or rejected proposal."""

    canonical_json: str

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "MacroTrace":
        _validate_trace_shape(record)
        encoded = _canonical_json(record)
        return cls(encoded)

    def __post_init__(self) -> None:
        if type(self.canonical_json) is not str:
            raise TypeError("macro trace canonical_json must be text")
        if len(self.canonical_json.encode("utf-8")) > MAX_MACRO_TRACE_BYTES:
            raise ValueError("macro trace exceeds its cumulative byte limit")
        try:
            value = json.loads(
                self.canonical_json,
                object_pairs_hook=_strict_json_object,
                parse_constant=_reject_json_constant,
            )
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise TypeError(f"macro trace is not strict JSON: {exc}") from None
        canonical = _canonical_json(value)
        if canonical != self.canonical_json:
            raise ValueError("macro trace is not in canonical JSON form")
        _validate_trace_shape(value)

    def to_dict(self) -> dict[str, object]:
        value = json.loads(self.canonical_json)
        if type(value) is not dict:  # pragma: no cover - constructor invariant
            raise RuntimeError("macro trace lost its object shape")
        return value

    def jsonl(self) -> str:
        """Return this one-attempt trace as a newline-terminated JSONL row."""

        return self.canonical_json + "\n"

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class MacroExecution:
    """One committed macro transition and any freshly checked certificate."""

    owner: MacroOwner
    action: Macro
    public_commands: tuple[str, ...]
    trace: MacroTrace
    certificate: Proof | None

    def __post_init__(self) -> None:
        if type(self.owner) is not MacroOwner:
            raise TypeError("macro execution owner must be an exact MacroOwner")
        MacroOwner(
            self.owner.session,
            self.owner.capabilities,
            self.owner.capability_identity_json,
            self.owner.semantic_profile_identity_json,
        )
        canonical_action = macro_object(self.action)
        if type(self.public_commands) is not tuple or not all(
            type(command) is str and bool(command) for command in self.public_commands
        ):
            raise TypeError("macro execution commands must be one exact text tuple")
        if type(self.trace) is not MacroTrace:
            raise TypeError("macro execution trace must be an exact MacroTrace")
        record = self.trace.to_dict()
        if record["outcome"] != {"status": "accepted", "error": None}:
            raise ValueError("macro execution cannot carry a rejected trace")
        if record["parse"]["canonical"] != canonical_action:
            raise ValueError("macro execution action differs from its trace")
        traced_commands = (
            record["compile"]["public_commands"]
            if record["solver"] is None
            else record["solver"]["reconstructed_commands"]
        )
        if list(self.public_commands) != traced_commands:
            raise ValueError("macro execution commands differ from its trace")
        if record["state_after"] != _state_record(self.owner):
            raise ValueError("macro execution owner differs from traced state_after")
        if self.owner.state.is_done():
            if not isinstance(self.certificate, Proof) or not check(
                (), self.certificate, self.owner.original_target
            ):
                raise ValueError(
                    "closed macro execution needs an original-target kernel certificate"
                )
            final = record["final_replay"]
            nodes, depth = proof_metrics(self.certificate)
            artifact = encode_artifact_bounded(
                8 * nodes + 16,
                self.owner.original_target,
                self.certificate,
                max_bytes=MAX_FINAL_ARTIFACT_BYTES,
            )
            if (
                final is None
                or final["status"] != "accepted"
                or final["certificate_nodes"] != nodes
                or final["certificate_depth"] != depth
                or final["certificate_sha256"]
                != hashlib.sha256(artifact).hexdigest()
            ):
                raise ValueError(
                    "macro execution certificate differs from fresh replay evidence"
                )
        elif self.certificate is not None or record["final_replay"] is not None:
            raise ValueError("open macro execution cannot carry a certificate")

    @property
    def closed(self) -> bool:
        return self.owner.state.is_done()


class MacroExecutionError(MacroRunnerError):
    """Rejected transaction carrying the untouched owner and complete trace."""

    def __init__(self, message: str, *, owner: MacroOwner, trace: MacroTrace) -> None:
        _require_error("macro execution error message", message)
        if type(owner) is not MacroOwner or type(trace) is not MacroTrace:
            raise TypeError("macro execution error needs exact owner and trace values")
        record = trace.to_dict()
        if record["outcome"]["status"] != "rejected":
            raise ValueError("macro execution error cannot carry an accepted trace")
        if record["state_before"] != record["state_after"]:
            raise ValueError("macro execution error trace is not transactional")
        if record["environment"]["original_theorem"] != pretty_formula(
            owner.original_target, []
        ):
            raise ValueError("macro execution error owner differs from trace theorem")
        if record["environment"]["owner_capability_sha256"] != owner.capability_sha256:
            raise ValueError("macro execution error owner differs from trace capability")
        super().__init__(message)
        self.owner = owner
        self.trace = trace


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise TypeError(f"value is not finite canonical JSON: {exc}") from None


def _exact_object(
    label: str,
    value: object,
    fields: frozenset[str],
) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise TypeError(f"{label} must have exactly the registered v1 fields")
    return value


def _require_digest(label: str, value: object) -> str:
    if (
        type(value) is not str
        or len(value) != 64
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise TypeError(f"{label} must be one lowercase SHA-256 digest")
    return value


def _require_text(label: str, value: object, *, empty: bool = False) -> str:
    if type(value) is not str or (not empty and not value):
        raise TypeError(f"{label} must be exact{' possibly empty' if empty else ' non-empty'} text")
    return value


def _require_error(label: str, value: object) -> str:
    text = _require_text(label, value)
    try:
        encoded = text.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise TypeError(f"{label} must be valid UTF-8 text") from exc
    if len(text) > MAX_ERROR_CHARS or len(encoded) > MAX_ERROR_UTF8_BYTES:
        raise ValueError(
            f"{label} exceeds the frozen error-text character/UTF-8 byte limits"
        )
    if text != " ".join(text.split()) or any(
        unicodedata.category(character) in _UNSAFE_CATEGORIES
        for character in text
    ):
        raise ValueError(f"{label} is not canonical safe one-line text")
    return text


def _require_int(
    label: str,
    value: object,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if (
        type(value) is not int
        or value < minimum
        or (maximum is not None and value > maximum)
    ):
        upper = "" if maximum is None else f" through {maximum}"
        raise TypeError(f"{label} must be an exact integer from {minimum}{upper}")
    return value


def _validate_state_shape(label: str, value: object) -> dict[str, object]:
    state = _exact_object(label, value, _STATE_FIELDS)
    if type(state["closed"]) is not bool:
        raise TypeError(f"{label}.closed must be a Boolean")
    goals = state["goals"]
    if type(goals) is not list or not all(type(goal) is str for goal in goals):
        raise TypeError(f"{label}.goals must be an exact text array")
    if state["closed"] != (len(goals) == 0):
        raise ValueError(f"{label}.closed disagrees with its goals")
    if state["goals_sha256"] != goal_state_sha256(tuple(goals)):
        raise ValueError(f"{label}.goals_sha256 is inconsistent")
    history = state["history"]
    if type(history) is not list or len(history) > MAX_OWNER_REPLAY_STEPS:
        raise TypeError(f"{label}.history must be one bounded exact array")
    for entry in history:
        item = _exact_object(
            f"{label}.history entry", entry, frozenset({"tactic", "args"})
        )
        _require_text(f"{label}.history.tactic", item["tactic"])
        _require_text(f"{label}.history.args", item["args"], empty=True)
    replay = state["replay"]
    if type(replay) is not list or len(replay) > MAX_OWNER_REPLAY_STEPS:
        raise TypeError(f"{label}.replay must be one bounded exact array")
    for entry in replay:
        item = _exact_object(
            f"{label}.replay entry", entry, frozenset({"command", "classical"})
        )
        _require_text(f"{label}.replay.command", item["command"])
        if item["classical"] is not False:
            raise ValueError(f"{label}.replay contains non-intuitionistic authority")
    if len(history) != len(replay):
        raise ValueError(f"{label}.history and replay lengths disagree")
    payload = {key: state[key] for key in _STATE_FIELDS if key != "state_sha256"}
    _require_digest(f"{label}.state_sha256", state["state_sha256"])
    if state["state_sha256"] != _json_sha256(
        "peano-hydra-macro-state-v1", payload
    ):
        raise ValueError(f"{label}.state_sha256 is inconsistent")
    return state


def _validate_state_summary(label: str, value: object) -> dict[str, object]:
    summary = _exact_object(label, value, _STATE_SUMMARY_FIELDS)
    if type(summary["closed"]) is not bool:
        raise TypeError(f"{label}.closed must be a Boolean")
    goals = summary["goals"]
    if type(goals) is not list or not all(type(goal) is str for goal in goals):
        raise TypeError(f"{label}.goals must be an exact text array")
    if summary["closed"] != (len(goals) == 0):
        raise ValueError(f"{label}.closed disagrees with its goals")
    if summary["goals_sha256"] != goal_state_sha256(tuple(goals)):
        raise ValueError(f"{label}.goals_sha256 is inconsistent")
    _require_int(
        f"{label}.history_length",
        summary["history_length"],
        maximum=MAX_OWNER_REPLAY_STEPS,
    )
    _require_int(
        f"{label}.replay_length",
        summary["replay_length"],
        maximum=MAX_OWNER_REPLAY_STEPS,
    )
    if summary["history_length"] != summary["replay_length"]:
        raise ValueError(f"{label} history/replay lengths disagree")
    payload = {
        key: summary[key] for key in _STATE_SUMMARY_FIELDS if key != "summary_sha256"
    }
    _require_digest(f"{label}.summary_sha256", summary["summary_sha256"])
    if summary["summary_sha256"] != _json_sha256(
        "peano-hydra-macro-state-summary-v1", payload
    ):
        raise ValueError(f"{label}.summary_sha256 is inconsistent")
    return summary


def _validate_request_shape(label: str, value: object) -> dict[str, object]:
    request = _exact_object(label, value, _REQUEST_FIELDS)
    solver = _require_text(f"{label}.solver", request["solver"])
    if len(solver) > 128 or _SOLVER_NAME.fullmatch(solver) is None:
        raise ValueError(f"{label}.solver is not canonical")
    premises = request["premises"]
    if (
        type(premises) is not list
        or len(premises) > MAX_DISPATCH_PREMISES
        or not all(type(name) is str and bool(name) for name in premises)
        or len(set(premises)) != len(premises)
    ):
        raise TypeError(f"{label}.premises is malformed")
    bounds = _exact_object(f"{label}.bounds", request["bounds"], _BOUNDS_FIELDS)
    for field, maximum in (
        ("max_steps", MAX_DISPATCH_STEPS),
        ("max_wall_time_ms", MAX_DISPATCH_WALL_TIME_MS),
        ("max_memory_bytes", MAX_DISPATCH_MEMORY_BYTES),
        ("max_output_bytes", MAX_DISPATCH_OUTPUT_BYTES),
    ):
        _require_int(f"{label}.bounds.{field}", bounds[field], minimum=1, maximum=maximum)
    if request["authority"] != "untrusted-hints-reconstruction-required":
        raise ValueError(f"{label}.authority is unsupported")
    return request


def _validate_raw_record(value: object) -> tuple[str, bytes | None]:
    raw = _exact_object("macro trace raw proposal", value, _RAW_FIELDS)
    encoding = raw["encoding"]
    allowed = {
        "utf-8",
        "base64",
        "utf-8-sha256-only-oversize",
        "invalid-unicode-sha256-only-oversize",
        "bytes-sha256-only-oversize",
        "invalid-unicode-diagnostic",
        "invalid-type-diagnostic",
    }
    if type(encoding) is not str or encoding not in allowed:
        raise ValueError("macro trace raw encoding is unsupported")
    byte_count = _require_int("macro trace raw bytes", raw["bytes"])
    digest = _require_digest("macro trace raw sha256", raw["sha256"])
    text_value = raw["text"]
    base64_value = raw["base64"]
    if encoding == "utf-8":
        if type(text_value) is not str or base64_value is not None:
            raise TypeError("UTF-8 raw evidence has invalid nullability")
        payload = text_value.encode("utf-8")
    elif encoding in {
        "base64",
        "invalid-unicode-diagnostic",
        "invalid-type-diagnostic",
    }:
        if text_value is not None or type(base64_value) is not str:
            raise TypeError("base64 raw evidence has invalid nullability")
        try:
            payload = b64decode(base64_value, validate=True)
        except ValueError as exc:
            raise ValueError("macro trace raw base64 is invalid") from exc
    else:
        if text_value is not None or base64_value is not None or byte_count <= MAX_MACRO_BYTES:
            raise ValueError("oversize raw evidence has invalid nullability or byte count")
        payload = None
    if payload is not None and (
        len(payload) != byte_count or hashlib.sha256(payload).hexdigest() != digest
    ):
        raise ValueError("macro trace raw payload digest/count is inconsistent")
    return encoding, payload


def _declared_names(label: str, value: object) -> frozenset[str] | None:
    if value is None:
        return None
    if (
        type(value) is not list
        or value != sorted(value)
        or len(set(value)) != len(value)
        or not all(type(name) is str and bool(name) for name in value)
    ):
        raise TypeError(f"{label} must be null or one sorted unique text array")
    return frozenset(value)


def _validate_trace_shape(value: object) -> None:
    """Fully validate exact v1 evidence, recomputed hashes, and cross-field relations."""

    if len(_canonical_json(value).encode("utf-8")) > MAX_MACRO_TRACE_BYTES:
        raise ValueError("macro trace exceeds its cumulative byte limit")
    trace = _exact_object("macro trace", value, _TRACE_FIELDS)
    if (
        trace["format"] != MACRO_TRACE_FORMAT
        or type(trace["v"]) is not int
        or trace["v"] != MACRO_TRACE_VERSION
    ):
        raise ValueError("macro trace has an unsupported identity")

    environment = _exact_object(
        "macro trace environment", trace["environment"], _ENVIRONMENT_FIELDS
    )
    if environment["classical"] is not False or environment["logic"] != "intuitionistic":
        raise ValueError("macro trace logic authority is not intuitionistic")
    if environment["semantic_profile_identity"] != semantic_profile_identity():
        raise ValueError("macro trace semantic profile identity is malformed")
    theorem = _require_text("macro trace original theorem", environment["original_theorem"])
    if canonical_profile_theorem(theorem) != theorem:
        raise ValueError("macro trace original theorem is not canonical profile text")
    if environment["original_theorem_sha256"] != hashlib.sha256(
        theorem.encode("utf-8")
    ).hexdigest():
        raise ValueError("macro trace original theorem digest is inconsistent")
    declared_commands = _declared_names(
        "macro trace allowed_commands", environment["allowed_commands"]
    )
    declared_theorems = _declared_names(
        "macro trace allowed_theorems", environment["allowed_theorems"]
    )
    label = _require_text("macro trace capability_label", environment["capability_label"])
    capabilities = SurfaceCapabilities(label, declared_commands, declared_theorems)
    expected_capability = _capability_identity(capabilities)
    owner_capability = _exact_object(
        "macro trace owner capability identity",
        environment["owner_capability_identity"],
        _OWNER_CAPABILITY_FIELDS,
    )
    if owner_capability != expected_capability:
        raise ValueError("macro trace owner capability identity is inconsistent")
    if environment["owner_capability_sha256"] != hashlib.sha256(
        _canonical_json(owner_capability).encode("utf-8")
    ).hexdigest():
        raise ValueError("macro trace owner capability digest is inconsistent")
    effective_commands = SURFACE_COMMAND_NAMES if declared_commands is None else declared_commands
    effective_theorems = SURFACE_THEOREM_NAMES if declared_theorems is None else declared_theorems
    for field, names in (
        ("effective_command_capability", effective_commands),
        ("effective_theorem_capability", effective_theorems),
    ):
        _exact_object(f"macro trace {field}", environment[field], _EFFECTIVE_CAPABILITY_FIELDS)
        if environment[field] != _effective_capability_record(names):
            raise ValueError(f"macro trace {field} is inconsistent")
    if environment["allowed_actions"] != list(_ACTION_NAMES):
        raise ValueError("macro trace action capability is inconsistent")
    registered = environment["registered_solvers"]
    identities = environment["registered_adapter_identities"]
    if (
        type(registered) is not list
        or registered != sorted(registered)
        or len(set(registered)) != len(registered)
        or not all(type(name) is str and _SOLVER_NAME.fullmatch(name) for name in registered)
        or type(identities) is not list
    ):
        raise TypeError("macro trace registered adapter environment is malformed")
    checked_identities = [DispatchAdapterIdentity.from_object(item) for item in identities]
    if [item.adapter for item in checked_identities] != registered:
        raise ValueError("macro trace solver names and adapter identities disagree")
    _exact_object(
        "macro trace protocol identity",
        environment["macro_protocol_identity"],
        _MACRO_PROTOCOL_IDENTITY_FIELDS,
    )
    if environment["macro_protocol_identity"] != macro_protocol_identity():
        raise ValueError("macro trace protocol identity is malformed")

    raw_encoding, raw_payload = _validate_raw_record(trace["raw_proposal"])
    parse_record = _exact_object("macro trace parse", trace["parse"], _PARSE_FIELDS)
    parse_status = parse_record["status"]
    if parse_status not in {"not-attempted", "error", "ok"}:
        raise ValueError("macro trace parse status is unsupported")
    parsed_action: Macro | None = None
    if parse_status == "ok":
        if parse_record["error"] is not None or type(parse_record["canonical"]) is not dict:
            raise ValueError("successful parse evidence has invalid nullability")
        parsed_action = parse_macro(_canonical_json(parse_record["canonical"]))
        if macro_object(parsed_action) != parse_record["canonical"]:
            raise ValueError("macro trace parsed action is not canonical")
        if parse_record["canonical_sha256"] != macro_sha256(parsed_action):
            raise ValueError("macro trace parsed action digest is inconsistent")
    else:
        if parse_record["canonical"] is not None or parse_record["canonical_sha256"] is not None:
            raise ValueError("unsuccessful parse evidence has invalid nullability")
        if parse_status == "error":
            _require_error("macro trace parse error", parse_record["error"])
        elif parse_record["error"] is not None:
            raise ValueError("unattempted parse cannot carry an error")
    if raw_encoding in {"utf-8", "base64"} and raw_payload is not None:
        try:
            expected_parsed_action = parse_macro(raw_payload)
        except (MacroProtocolError, TypeError, ValueError, RecursionError):
            if parse_status != "error":
                raise ValueError("macro trace parse status disagrees with raw proposal")
        else:
            if (
                parse_status != "ok"
                or parsed_action is None
                or macro_object(parsed_action) != macro_object(expected_parsed_action)
            ):
                raise ValueError("macro trace parsed action disagrees with raw proposal")
    elif parse_status != "error":
        raise ValueError("non-parseable diagnostic/oversize proposal must be rejected")

    compile_record = _exact_object("macro trace compile", trace["compile"], _COMPILE_FIELDS)
    compile_status = compile_record["status"]
    if compile_status not in {"not-attempted", "error", "ok"}:
        raise ValueError("macro trace compile status is unsupported")
    if type(compile_record["public_commands"]) is not list or not all(
        type(command) is str for command in compile_record["public_commands"]
    ):
        raise TypeError("macro trace compiled commands are malformed")
    compiled_dispatch = compile_record["dispatch"]
    if compiled_dispatch is not None:
        _validate_request_shape("macro trace compiled dispatch", compiled_dispatch)
        expected_request_digest = hashlib.sha256(
            _canonical_json(compiled_dispatch).encode("utf-8")
        ).hexdigest()
        if compile_record["dispatch_request_sha256"] != expected_request_digest:
            raise ValueError("macro trace compiled request digest is inconsistent")
    elif compile_record["dispatch_request_sha256"] is not None:
        raise ValueError("non-dispatch compile cannot carry a request digest")
    if compile_status == "ok":
        if parsed_action is None or compile_record["error"] is not None:
            raise ValueError("successful compile evidence has invalid dependencies")
        expected = compile_macro(
            parsed_action,
            capabilities=capabilities,
            available_solvers=tuple(registered),
        )
        expected_dispatch = (
            None if expected.dispatch is None else _dispatch_request_record(expected.dispatch)
        )
        if compile_record["public_commands"] != list(expected.public_commands) or compiled_dispatch != expected_dispatch:
            raise ValueError("macro trace compile result is inconsistent with typed compilation")
    else:
        if compile_record["public_commands"] != [] or compiled_dispatch is not None:
            raise ValueError("unsuccessful compile evidence carries a command plan")
        if compile_status == "error":
            if parsed_action is None:
                raise ValueError("compile error requires a successful parse")
            _require_error("macro trace compile error", compile_record["error"])
        elif compile_record["error"] is not None or parse_status != "error":
            raise ValueError("unattempted compile has inconsistent dependencies")

    before = _validate_state_shape("macro trace state_before", trace["state_before"])
    after = _validate_state_shape("macro trace state_after", trace["state_after"])
    intermediates = trace["intermediate_states"]
    if type(intermediates) is not list or len(intermediates) > MAX_DISPATCH_COMMANDS:
        raise TypeError("macro trace intermediate_states must be one bounded exact array")

    solver = trace["solver"]
    solver_commands: list[str] | None = None
    typed_request: DispatchRequest | None = None
    traced_context: dict[str, object] | None = None
    traced_host_usage: dict[str, object] | None = None
    prepared_dispatch_call = False
    solver_enforcement_error: Exception | None = None
    if solver is not None:
        solver_record = _exact_object("macro trace solver", solver, _SOLVER_FIELDS)
        request = _validate_request_shape("macro trace solver request", solver_record["request"])
        bounds_record = request["bounds"]
        typed_request = DispatchRequest(
            request["solver"],  # type: ignore[arg-type]
            tuple(request["premises"]),  # type: ignore[arg-type]
            DispatchBounds(
                bounds_record["max_steps"],  # type: ignore[index,arg-type]
                bounds_record["max_wall_time_ms"],  # type: ignore[index,arg-type]
                bounds_record["max_memory_bytes"],  # type: ignore[index,arg-type]
                bounds_record["max_output_bytes"],  # type: ignore[index,arg-type]
            ),
        )
        if compiled_dispatch != request:
            raise ValueError("macro trace compiled and traced dispatch requests differ")
        request_digest = hashlib.sha256(_canonical_json(request).encode("utf-8")).hexdigest()
        if solver_record["request_sha256"] != request_digest:
            raise ValueError("macro trace solver request_sha256 is inconsistent")
        solver_identity = DispatchAdapterIdentity.from_object(solver_record["adapter_identity"])
        if solver_record["adapter_identity_sha256"] != solver_identity.sha256:
            raise ValueError("macro trace solver adapter identity digest is malformed")
        if solver_identity.adapter != request["solver"] or solver_identity.to_dict() not in identities:
            raise ValueError("macro trace request and adapter environment disagree")
        context = _exact_object("macro trace solver context", solver_record["context"], _SOLVER_CONTEXT_FIELDS)
        traced_context = context
        if context["original_theorem"] != theorem or type(context["goals"]) is not list or not all(
            type(goal) is str for goal in context["goals"]
        ) or context["goals"] != before["goals"]:
            raise ValueError("macro trace solver context is inconsistent")
        premises = context["premises"]
        if type(premises) is not list:
            raise TypeError("macro trace solver premises must be an exact array")
        for premise in premises:
            item = _exact_object("macro trace solver premise", premise, _PREMISE_FIELDS)
            DispatchPremise(item["name"], item["kind"], item["formula"])  # type: ignore[arg-type]
        adapter_configuration = solver_record["adapter_configuration"]
        if type(adapter_configuration) is not dict:
            raise TypeError(
                "macro trace adapter configuration must be one exact JSON object"
            )
        configuration_bytes = _canonical_json(adapter_configuration).encode("utf-8")
        if len(configuration_bytes) > MAX_DISPATCH_CONFIGURATION_BYTES:
            raise ValueError("macro trace adapter configuration exceeds its byte limit")
        if hashlib.sha256(configuration_bytes).hexdigest() != solver_identity.configuration_sha256:
            raise ValueError(
                "macro trace adapter configuration digest is inconsistent"
            )
        call_request_digest = solver_record["dispatch_call_request_sha256"]
        call_digest = solver_record["dispatch_call_sha256"]
        if (call_request_digest is None) != (call_digest is None):
            raise ValueError("macro trace dispatch call digests have invalid nullability")
        if call_digest is not None:
            _require_digest(
                "macro trace dispatch call request digest", call_request_digest
            )
            _require_digest("macro trace dispatch call digest", call_digest)
            if call_request_digest != request_digest:
                raise ValueError(
                    "macro trace dispatch call request digest is inconsistent"
                )
            call_record = _dispatch_call_record(
                adapter_identity=solver_identity.to_dict(),
                configuration=adapter_configuration,
                request=request,
                request_sha256=request_digest,
                context=context,
            )
            call_bytes = _canonical_json(call_record).encode("utf-8")
            if len(call_bytes) > MAX_DISPATCH_CALL_BYTES:
                raise ValueError("macro trace dispatch call exceeds its byte limit")
            if hashlib.sha256(call_bytes).hexdigest() != call_digest:
                raise ValueError("macro trace dispatch call digest is inconsistent")
            prepared_dispatch_call = True
        if solver_record["step_accounting"] != DISPATCH_STEP_ACCOUNTING:
            raise ValueError("macro trace dispatch step-accounting authority is unsupported")
        raw_bytes = solver_record["raw_response_bytes"]
        raw_b64 = solver_record["raw_response_base64"]
        raw_digest = solver_record["raw_response_sha256"]
        response_payload: bytes | None = None
        raw_over_limit = False
        if raw_bytes is None:
            if raw_b64 is not None or raw_digest is not None:
                raise ValueError("absent raw solver response has invalid nullability")
        else:
            _require_int(
                "macro trace raw response bytes",
                raw_bytes,
                maximum=MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES,
            )
            raw_over_limit = raw_bytes > bounds_record["max_output_bytes"]
            if raw_over_limit and raw_bytes != bounds_record["max_output_bytes"] + 1:
                raise ValueError(
                    "macro trace over-limit raw response is not the one-byte rejection sentinel"
                )
            _require_digest("macro trace raw response digest", raw_digest)
            if type(raw_b64) is not str:
                raise TypeError("macro trace raw response base64 is malformed")
            try:
                response_payload = b64decode(raw_b64, validate=True)
            except ValueError as exc:
                raise ValueError("macro trace raw response base64 is invalid") from exc
            if len(response_payload) != raw_bytes or hashlib.sha256(response_payload).hexdigest() != raw_digest:
                raise ValueError("macro trace raw response digest/count is inconsistent")
        usage = solver_record["host_usage"]
        if usage is not None:
            usage_record = _exact_object("macro trace dispatch host usage", usage, _HOST_USAGE_FIELDS)
            traced_host_usage = usage_record
            DispatchHostUsage(**usage_record)  # type: ignore[arg-type]
            if usage_record["output_bytes"] != (0 if raw_bytes is None else raw_bytes):
                raise ValueError("macro trace host output accounting is inconsistent")
            bounds = request["bounds"]
            if usage_record["memory_limit_bytes"] != bounds["max_memory_bytes"]:
                raise ValueError("macro trace host memory bound was mutated")
            if usage_record["wall_limit_ms"] != bounds["max_wall_time_ms"]:
                raise ValueError("macro trace host wall-time bound was mutated")
            if usage_record["output_limit_bytes"] != bounds["max_output_bytes"]:
                raise ValueError("macro trace host output bound was mutated")
            if usage_record["process_limit"] != 1:
                raise ValueError("macro trace host process bound was mutated")
        elif response_payload is not None:
            raise ValueError("raw solver response lacks host-observed usage evidence")
        response_status = solver_record["response_status"]
        response_steps = solver_record["response_steps_used"]
        solver_commands = solver_record["reconstructed_commands"]
        if type(solver_commands) is not list or not all(type(command) is str for command in solver_commands):
            raise TypeError("macro trace reconstructed commands are malformed")
        if (
            usage is not None
            or response_payload is not None
            or response_status is not None
            or solver_commands
        ) and not prepared_dispatch_call:
            raise ValueError(
                "dispatch process/response evidence lacks one prepared canonical call"
            )
        if response_status is None:
            if response_steps is not None or solver_commands:
                raise ValueError("unparsed dispatch response has invalid nullability")
            if raw_over_limit and (
                usage is None
                or usage["reconstructed_command_bytes"] != 0  # type: ignore[index]
                or solver_record["error"] is None
            ):
                raise ValueError(
                    "over-limit dispatch evidence is not one rejected unparsed response"
                )
        else:
            if raw_over_limit:
                raise ValueError("over-limit dispatch evidence cannot be a parsed response")
            if response_payload is None or usage is None:
                raise ValueError("parsed dispatch response lacks raw/host evidence")
            checked_response = DispatchResponse(
                response_status,
                _require_int("macro trace response steps", response_steps),
                tuple(solver_commands),
                response_payload,
                DispatchHostUsage(**usage),  # type: ignore[arg-type]
            )
            try:
                response_object = json.loads(
                    response_payload.decode("utf-8"),
                    object_pairs_hook=_strict_json_object,
                    parse_constant=_reject_json_constant,
                )
            except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
                raise ValueError("macro trace parsed response is not strict JSON") from exc
            response_object = _exact_object(
                "macro trace parsed dispatch response",
                response_object,
                _DISPATCH_RESPONSE_FIELDS,
            )
            expected_response_object = {
                "format": DISPATCH_RESPONSE_FORMAT,
                "v": DISPATCH_RESPONSE_VERSION,
                "status": response_status,
                "steps_used": response_steps,
                "public_commands": solver_commands,
            }
            if (
                response_object != expected_response_object
                or _canonical_json(response_object).encode("utf-8") != response_payload
            ):
                raise ValueError("macro trace parsed response fields differ from raw bytes")
            expected_command_bytes = sum(len(command.encode("utf-8")) for command in solver_commands)
            if usage["reconstructed_command_bytes"] != expected_command_bytes:  # type: ignore[index]
                raise ValueError("macro trace reconstructed command byte count is inconsistent")
            if usage["exit_code"] != 0 or usage["timed_out"] is not False:  # type: ignore[index]
                raise ValueError("parsed dispatch response lacks a successful host exit")
            if [item["name"] for item in premises] != request["premises"]:
                raise ValueError("invoked dispatch context differs from requested premises")
            try:
                checked_commands = _enforce_dispatch_response(
                    typed_request,
                    checked_response,
                    capabilities=capabilities,
                )
                if list(checked_commands) != solver_commands:
                    raise ValueError(
                        "validated dispatch command plan differs from trace"
                    )
            except Exception as exc:
                solver_enforcement_error = exc
        if solver_record["authority"] != "untrusted-status-reconstruction-required":
            raise ValueError("macro trace dispatch authority is unsupported")
        if solver_record["error"] is not None:
            _require_error("macro trace solver error", solver_record["error"])
    elif compiled_dispatch is not None:
        raise ValueError("compiled dispatch is missing solver evidence")

    plan = solver_commands if solver_commands is not None else compile_record["public_commands"]
    for index, entry in enumerate(intermediates):
        item = _exact_object("macro trace intermediate state", entry, _INTERMEDIATE_FIELDS)
        if item["command_index"] != index or type(item["command_index"]) is not int:
            raise ValueError("macro trace intermediate command indexes are not contiguous")
        if index >= len(plan) or item["command"] != plan[index]:
            raise ValueError("macro trace intermediate command differs from its compiled plan")
        summary = _validate_state_summary(
            "macro trace intermediate state summary", item["state_summary"]
        )
        if summary["history_length"] != len(before["history"]) + index + 1:
            raise ValueError("macro trace intermediate history length is inconsistent")

    # Reconstruct the owner prefix and every claimed successful intermediate
    # through the same capability-checked public surface.  This independently
    # validates state hashes and prevents a well-shaped trace from inventing a
    # transition that the current capability environment cannot replay.
    replay_target, replay_names = parse_formula_with_names(theorem)
    replay_session = ProofSession(
        state=start(replay_target, replay_names),
        original_target=replay_target,
        original_names=replay_names,
        target_source=theorem,
        classical=False,
        trace=TraceLogger(session_id="peano-hydra-macro-trace-validation"),
    )
    try:
        for step in before["replay"]:
            replay_session = run_surface(
                replay_session,
                step["command"],
                capabilities=capabilities,
                record_trace=False,
            )
    except Exception as exc:
        raise ValueError(
            f"macro trace owner prefix does not replay: {_error_text(exc)}"
        ) from None
    replay_owner = MacroOwner(
        replay_session,
        capabilities,
        _canonical_json(owner_capability),
        _canonical_json(environment["semantic_profile_identity"]),
    )
    if _state_record(replay_owner) != before:
        raise ValueError("macro trace state_before differs from its replay")
    if typed_request is not None:
        try:
            expected_context = _resolve_dispatch_context(replay_owner, typed_request)
        except (DispatchProtocolError, TypeError, ValueError, RecursionError):
            fallback_context = {
                "original_theorem": theorem,
                "goals": before["goals"],
                "premises": [],
            }
            if (
                traced_context != fallback_context
                or traced_host_usage is not None
                or solver_record["raw_response_bytes"] is not None
                or solver_record["response_status"] is not None
                or solver_record["dispatch_call_sha256"] is not None
                or solver_record["dispatch_call_request_sha256"] is not None
            ):
                raise ValueError(
                    "macro trace claims dispatch invocation despite unresolved context"
                )
        else:
            if traced_context != expected_context.to_dict():
                raise ValueError(
                    "macro trace dispatch context differs from owner/library state"
                )
    for index, entry in enumerate(intermediates):
        try:
            replay_session = run_surface(
                replay_session,
                entry["command"],
                capabilities=capabilities,
                record_trace=False,
            )
        except Exception as exc:
            raise ValueError(
                f"macro trace intermediate command does not replay: {_error_text(exc)}"
            ) from None
        replay_owner = replay_owner.with_session(replay_session)
        if _state_summary(replay_owner) != entry["state_summary"]:
            raise ValueError("macro trace intermediate state differs from public replay")

    outcome = _exact_object("macro trace outcome", trace["outcome"], _OUTCOME_FIELDS)
    if outcome["status"] not in {"accepted", "rejected"}:
        raise ValueError("macro trace outcome status is unsupported")
    accepted = outcome["status"] == "accepted"
    if accepted:
        if outcome["error"] is not None or compile_status != "ok" or len(intermediates) != len(plan):
            raise ValueError("accepted macro trace has inconsistent completion evidence")
        if solver is not None and (
            solver_record["response_status"] is None
            or solver_record["error"] is not None
            or solver_enforcement_error is not None
        ):
            raise ValueError(
                "accepted dispatch trace lacks one enforceable reconstructed response"
            )
        if intermediates:
            last = intermediates[-1]["state_summary"]
            for field in ("closed", "goals", "goals_sha256", "history_length", "replay_length"):
                expected_value = len(after["history"]) if field in {"history_length", "replay_length"} else after[field]
                if last[field] != expected_value:
                    raise ValueError("accepted macro trace final state summary is inconsistent")
        if _state_record(replay_owner) != after:
            raise ValueError("accepted macro trace state_after differs from public replay")
    else:
        _require_error("macro trace outcome error", outcome["error"])
        if after != before:
            raise ValueError("rejected macro trace did not roll back exactly")

    replay = trace["final_replay"]
    if replay is None:
        if accepted and after["closed"]:
            raise ValueError("closed accepted macro trace lacks fresh final replay")
    else:
        final = _exact_object("macro trace final replay", replay, _FINAL_REPLAY_FIELDS)
        if final["fresh"] is not True or final["original_theorem"] != theorem:
            raise ValueError("macro trace final replay authority is inconsistent")
        if type(final["commands"]) is not list or not all(type(command) is str for command in final["commands"]):
            raise TypeError("macro trace final replay commands are malformed")
        expected_commands = [item["command"] for item in before["replay"]] + [
            item["command"] for item in intermediates
        ]
        if final["commands"] != expected_commands:
            raise ValueError("macro trace final replay commands are inconsistent")
        if final["status"] == "accepted":
            if not accepted or final["kernel_accepted"] is not True or final["error"] is not None:
                raise ValueError("accepted final replay has inconsistent outcome")
            if final["certificate_representation"] != "peano-lab-v2":
                raise ValueError("macro trace certificate representation is unsupported")
            _require_digest("macro trace certificate digest", final["certificate_sha256"])
            _require_int("macro trace certificate nodes", final["certificate_nodes"], minimum=1)
            _require_int("macro trace certificate depth", final["certificate_depth"], minimum=1)
            if not after["closed"]:
                raise ValueError("accepted final replay did not close the committed state")
        elif final["status"] == "rejected":
            if accepted or final["kernel_accepted"] is not False:
                raise ValueError("rejected final replay has inconsistent outcome")
            for field in (
                "certificate_representation",
                "certificate_sha256",
                "certificate_nodes",
                "certificate_depth",
            ):
                if final[field] is not None:
                    raise ValueError("rejected final replay carries certificate claims")
            _require_error("macro trace final replay error", final["error"])
        else:
            raise ValueError("macro trace final replay status is unsupported")

        replay_error: Exception | None = None
        replay_certificate: Proof | None = None
        replay_nodes: int | None = None
        replay_depth: int | None = None
        replay_artifact: bytes | None = None
        try:
            checked_session = ProofSession(
                state=start(replay_target, replay_names),
                original_target=replay_target,
                original_names=replay_names,
                target_source=theorem,
                classical=False,
                trace=TraceLogger(
                    session_id="peano-hydra-macro-trace-final-validation"
                ),
            )
            for command in final["commands"]:
                checked_session = run_surface(
                    checked_session,
                    command,
                    capabilities=capabilities,
                    record_trace=False,
                )
            replay_certificate = checked_surface_final(
                checked_session.state,
                replay_target,
                classical=False,
            )
            replay_nodes, replay_depth = proof_metrics(replay_certificate)
            replay_artifact = encode_artifact_bounded(
                8 * replay_nodes + 16,
                replay_target,
                replay_certificate,
                max_bytes=MAX_FINAL_ARTIFACT_BYTES,
            )
        except Exception as exc:
            replay_error = exc
        if final["status"] == "accepted":
            if replay_error is not None or replay_artifact is None:
                raise ValueError(
                    f"accepted macro trace does not independently replay: {_error_text(replay_error)}"
                )
            if (
                final["certificate_nodes"] != replay_nodes
                or final["certificate_depth"] != replay_depth
                or final["certificate_sha256"]
                != hashlib.sha256(replay_artifact).hexdigest()
            ):
                raise ValueError(
                    "macro trace certificate metrics/digest differ from fresh kernel replay"
                )
        elif replay_error is None:
            raise ValueError("rejected final replay succeeds under current kernel authority")


def _json_sha256(domain: str, value: object) -> str:
    preimage = domain.encode("ascii") + b"\x00" + _canonical_json(value).encode("utf-8")
    return hashlib.sha256(preimage).hexdigest()


def _error_text(value: object) -> str:
    decoded = str(value).encode("utf-8", errors="replace").decode("utf-8")
    raw = "".join(
        character
        if unicodedata.category(character) not in _UNSAFE_CATEGORIES
        else f"\\u{ord(character):04x}"
        for character in decoded
    )
    text = " ".join(raw.split()) or type(value).__name__
    pieces: list[str] = []
    byte_count = 0
    for character in text[:MAX_ERROR_CHARS]:
        encoded = character.encode("utf-8")
        if byte_count + len(encoded) > MAX_ERROR_UTF8_BYTES:
            break
        pieces.append(character)
        byte_count += len(encoded)
    return "".join(pieces) or type(value).__name__


def _stream_text_digest(source: str, *, errors: str) -> tuple[int, str]:
    digest = hashlib.sha256()
    byte_count = 0
    for offset in range(0, len(source), 4_096):
        chunk = source[offset : offset + 4_096].encode("utf-8", errors=errors)
        byte_count += len(chunk)
        digest.update(chunk)
    return byte_count, digest.hexdigest()


def _raw_proposal_record(source: str | bytes) -> dict[str, object]:
    if type(source) is str:
        if len(source) > MAX_MACRO_BYTES:
            try:
                byte_count, digest = _stream_text_digest(source, errors="strict")
                encoding = "utf-8-sha256-only-oversize"
            except UnicodeEncodeError:
                byte_count, digest = _stream_text_digest(
                    source, errors="backslashreplace"
                )
                encoding = "invalid-unicode-sha256-only-oversize"
            return {
                "encoding": encoding,
                "text": None,
                "base64": None,
                "bytes": byte_count,
                "sha256": digest,
            }
        try:
            raw = source.encode("utf-8")
        except UnicodeEncodeError:
            # ``backslashreplace`` is an inert diagnostic projection.  The
            # parser still receives the original and rejects it independently.
            diagnostic = source.encode("utf-8", errors="backslashreplace")
            return {
                "encoding": "invalid-unicode-diagnostic",
                "text": None,
                "base64": b64encode(diagnostic).decode("ascii"),
                "bytes": len(diagnostic),
                "sha256": hashlib.sha256(diagnostic).hexdigest(),
            }
        if len(raw) > MAX_MACRO_BYTES:
            return {
                "encoding": "utf-8-sha256-only-oversize",
                "text": None,
                "base64": None,
                "bytes": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
            }
        return {
            "encoding": "utf-8",
            "text": source,
            "base64": None,
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
    if type(source) is bytes:
        if len(source) > MAX_MACRO_BYTES:
            return {
                "encoding": "bytes-sha256-only-oversize",
                "text": None,
                "base64": None,
                "bytes": len(source),
                "sha256": hashlib.sha256(source).hexdigest(),
            }
        try:
            text = source.decode("utf-8")
        except UnicodeDecodeError:
            text = None
        return {
            "encoding": "utf-8" if text is not None else "base64",
            "text": text,
            "base64": None if text is not None else b64encode(source).decode("ascii"),
            "bytes": len(source),
            "sha256": hashlib.sha256(source).hexdigest(),
        }
    diagnostic = (
        f"{type(source).__module__}.{type(source).__qualname__}"
    ).encode("utf-8", errors="backslashreplace")
    return {
        "encoding": "invalid-type-diagnostic",
        "text": None,
        "base64": b64encode(diagnostic).decode("ascii"),
        "bytes": len(diagnostic),
        "sha256": hashlib.sha256(diagnostic).hexdigest(),
    }


def _validate_registered_trace_contract() -> None:
    protocol = load_macro_protocol()
    try:
        trace_contract = protocol["trace"]  # type: ignore[index]
        adapter_contract = protocol["dispatch_adapter_identity"]  # type: ignore[index]
        subprocess_contract = protocol["dispatch_subprocess"]  # type: ignore[index]
        call_contract = subprocess_contract["call"]  # type: ignore[index]
        response_contract = subprocess_contract["response"]  # type: ignore[index]
        host_contract = subprocess_contract["host"]  # type: ignore[index]
        limits_contract = protocol["limits"]  # type: ignore[index]
        registered = trace_contract["field_sets"]  # type: ignore[index]
    except (KeyError, TypeError):
        raise MacroRunnerError("macro protocol trace contract is malformed") from None
    identities = (
        (
            "macro trace",
            trace_contract,
            MACRO_TRACE_FORMAT,
            MACRO_TRACE_VERSION,
        ),
        (
            "dispatch adapter",
            adapter_contract,
            DISPATCH_ADAPTER_IDENTITY_FORMAT,
            DISPATCH_ADAPTER_IDENTITY_VERSION,
        ),
        (
            "dispatch call",
            call_contract,
            DISPATCH_CALL_FORMAT,
            DISPATCH_CALL_VERSION,
        ),
        (
            "dispatch response",
            response_contract,
            DISPATCH_RESPONSE_FORMAT,
            DISPATCH_RESPONSE_VERSION,
        ),
    )
    for label, registered_identity, live_format, live_version in identities:
        if (
            type(registered_identity) is not dict
            or registered_identity.get("format") != live_format
            or type(registered_identity.get("v")) is not int
            or registered_identity.get("v") != live_version
        ):
            raise MacroRunnerError(
                f"live {label} identity drifted from macro-protocol-v1.json"
            )
    if (
        type(host_contract) is not dict
        or host_contract.get("resource_semantics") != _DISPATCH_RESOURCE_SEMANTICS
    ):
        raise MacroRunnerError(
            "live dispatch resource semantics drifted from macro-protocol-v1.json"
        )
    if (
        type(limits_contract) is not dict
        or limits_contract.get("max_dispatch_call_bytes") != MAX_DISPATCH_CALL_BYTES
        or limits_contract.get("max_dispatch_output_evidence_bytes")
        != MAX_DISPATCH_OUTPUT_EVIDENCE_BYTES
    ):
        raise MacroRunnerError(
            "live dispatch evidence limits drifted from macro-protocol-v1.json"
        )
    live = {
        "adapter_identity": sorted(_ADAPTER_IDENTITY_FIELDS),
        "compile": sorted(_COMPILE_FIELDS),
        "dispatch_bounds": sorted(_BOUNDS_FIELDS),
        "dispatch_request": sorted(_REQUEST_FIELDS),
        "effective_capability": sorted(_EFFECTIVE_CAPABILITY_FIELDS),
        "environment": sorted(_ENVIRONMENT_FIELDS),
        "final_replay": sorted(_FINAL_REPLAY_FIELDS),
        "history_entry": ["args", "tactic"],
        "dispatch_call": sorted(_DISPATCH_CALL_FIELDS),
        "dispatch_response": sorted(_DISPATCH_RESPONSE_FIELDS),
        "intermediate_state": sorted(_INTERMEDIATE_FIELDS),
        "macro_protocol_identity": sorted(_MACRO_PROTOCOL_IDENTITY_FIELDS),
        "outcome": sorted(_OUTCOME_FIELDS),
        "parse": sorted(_PARSE_FIELDS),
        "premise": sorted(_PREMISE_FIELDS),
        "raw_proposal": sorted(_RAW_FIELDS),
        "replay_entry": ["classical", "command"],
        "solver": sorted(_SOLVER_FIELDS),
        "solver_context": sorted(_SOLVER_CONTEXT_FIELDS),
        "state": sorted(_STATE_FIELDS),
        "state_summary": sorted(_STATE_SUMMARY_FIELDS),
        "top_level": sorted(_TRACE_FIELDS),
        "host_usage": sorted(_HOST_USAGE_FIELDS),
        "owner_capability": sorted(_OWNER_CAPABILITY_FIELDS),
    }
    if registered != live:
        raise MacroRunnerError(
            "live macro trace fields drifted from macro-protocol-v1.json"
        )


def _effective_capability_record(names: frozenset[str]) -> dict[str, object]:
    ordered = sorted(names)
    preimage = json.dumps(
        ordered,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "format": "peano-hydra-effective-capability-set",
        "v": 1,
        "count": len(ordered),
        "sha256": hashlib.sha256(preimage).hexdigest(),
    }


def _capability_identity(capabilities: SurfaceCapabilities) -> dict[str, object]:
    effective_commands = (
        SURFACE_COMMAND_NAMES
        if capabilities.allowed_commands is None
        else capabilities.allowed_commands
    )
    effective_theorems = (
        SURFACE_THEOREM_NAMES
        if capabilities.allowed_theorems is None
        else capabilities.allowed_theorems
    )
    return {
        "format": "peano-hydra-owner-capability",
        "v": 1,
        "label": capabilities.label,
        "declared_commands": (
            None
            if capabilities.allowed_commands is None
            else sorted(capabilities.allowed_commands)
        ),
        "declared_theorems": (
            None
            if capabilities.allowed_theorems is None
            else sorted(capabilities.allowed_theorems)
        ),
        "effective_command_capability": _effective_capability_record(
            effective_commands
        ),
        "effective_theorem_capability": _effective_capability_record(
            effective_theorems
        ),
    }


def _environment_record(
    owner: MacroOwner,
    adapters: dict[str, DispatchAdapterRegistration],
) -> dict[str, object]:
    _validate_registered_trace_contract()
    capabilities = owner.capabilities
    effective_commands = (
        SURFACE_COMMAND_NAMES
        if capabilities.allowed_commands is None
        else capabilities.allowed_commands
    )
    effective_theorems = (
        SURFACE_THEOREM_NAMES
        if capabilities.allowed_theorems is None
        else capabilities.allowed_theorems
    )
    original_theorem = pretty_formula(owner.original_target, [])
    return {
        "classical": False,
        "logic": "intuitionistic",
        "semantic_profile_identity": owner.profile_identity,
        "original_theorem": original_theorem,
        "original_theorem_sha256": hashlib.sha256(
            original_theorem.encode("utf-8")
        ).hexdigest(),
        "owner_capability_identity": owner.capability_identity,
        "owner_capability_sha256": owner.capability_sha256,
        "capability_label": capabilities.label,
        "allowed_actions": list(_ACTION_NAMES),
        "allowed_commands": (
            None
            if capabilities.allowed_commands is None
            else sorted(capabilities.allowed_commands)
        ),
        "allowed_theorems": (
            None
            if capabilities.allowed_theorems is None
            else sorted(capabilities.allowed_theorems)
        ),
        "registered_solvers": sorted(adapters),
        "registered_adapter_identities": [
            adapters[name].identity.to_dict() for name in sorted(adapters)
        ],
        "effective_command_capability": _effective_capability_record(
            effective_commands
        ),
        "effective_theorem_capability": _effective_capability_record(
            effective_theorems
        ),
        "macro_protocol_identity": macro_protocol_identity(),
    }


def _state_record(owner: MacroOwner) -> dict[str, object]:
    goals = tuple(render_goals(owner.state))
    history = [
        {"tactic": step.tactic, "args": step.args}
        for step in owner.state.history
    ]
    replay = [
        {"command": step.command, "classical": step.classical}
        for step in owner.replay_steps
    ]
    payload: dict[str, object] = {
        "closed": owner.state.is_done(),
        "goals": list(goals),
        "goals_sha256": goal_state_sha256(goals),
        "history": history,
        "replay": replay,
    }
    return {**payload, "state_sha256": _json_sha256("peano-hydra-macro-state-v1", payload)}


def _state_summary(owner: MacroOwner) -> dict[str, object]:
    """Compact per-command evidence, avoiding quadratic history duplication."""

    goals = tuple(render_goals(owner.state))
    payload: dict[str, object] = {
        "closed": owner.state.is_done(),
        "goals": list(goals),
        "goals_sha256": goal_state_sha256(goals),
        "history_length": len(owner.state.history),
        "replay_length": len(owner.replay_steps),
    }
    return {
        **payload,
        "summary_sha256": _json_sha256(
            "peano-hydra-macro-state-summary-v1", payload
        ),
    }


def _verify_owner_prefix(owner: MacroOwner) -> None:
    theorem = pretty_formula(owner.original_target, [])
    fresh_session = ProofSession(
        state=start(owner.original_target, owner.original_names),
        original_target=owner.original_target,
        original_names=owner.original_names,
        target_source=theorem,
        classical=False,
        trace=TraceLogger(session_id="peano-hydra-owner-prefix-replay"),
    )
    for step in owner.replay_steps:
        if step.classical:
            raise MacroRunnerError("owner replay contains forbidden classical authority")
        try:
            fresh_session = run_surface(
                fresh_session,
                step.command,
                capabilities=owner.capabilities,
                record_trace=False,
            )
        except Exception as exc:
            raise MacroRunnerError(
                f"owner replay is incompatible with its capability identity: {_error_text(exc)}"
            ) from None
    fresh_owner = owner.with_session(fresh_session)
    if _state_record(fresh_owner) != _state_record(owner):
        raise MacroRunnerError(
            "owner state does not equal replay under its stable capability identity"
        )


def _parse_record(action: Macro | None, error: str | None) -> dict[str, object]:
    return {
        "status": "ok" if action is not None else ("error" if error else "not-attempted"),
        "canonical": None if action is None else macro_object(action),
        "canonical_sha256": None if action is None else macro_sha256(action),
        "error": error,
    }


def _dispatch_request_record(request: DispatchRequest) -> dict[str, object]:
    return {
        "solver": request.solver,
        "premises": list(request.premises),
        "bounds": {
            "max_steps": request.bounds.max_steps,
            "max_wall_time_ms": request.bounds.max_wall_time_ms,
            "max_memory_bytes": request.bounds.max_memory_bytes,
            "max_output_bytes": request.bounds.max_output_bytes,
        },
        "authority": request.authority,
    }


def _dispatch_call_record(
    *,
    adapter_identity: dict[str, object],
    configuration: dict[str, object],
    request: dict[str, object],
    request_sha256: str,
    context: dict[str, object],
) -> dict[str, object]:
    """Build the sole canonical child-stdin preimage from retained fields."""

    call: dict[str, object] = {
        "format": DISPATCH_CALL_FORMAT,
        "v": DISPATCH_CALL_VERSION,
        "adapter_identity": adapter_identity,
        "configuration": configuration,
        "request": request,
        "request_sha256": request_sha256,
        "context": context,
    }
    _exact_object("dispatch call", call, _DISPATCH_CALL_FIELDS)
    return call


def _prepare_dispatch_call(
    registration: DispatchAdapterRegistration,
    request: DispatchRequest,
    context: DispatchContext,
) -> bytes:
    """Construct and pin the exact canonical bytes later written to child stdin."""

    registration.verify_identity()
    request_record = _dispatch_request_record(request)
    request_bytes = _canonical_json(request_record).encode("utf-8")
    if len(request_bytes) > MAX_DISPATCH_REQUEST_BYTES:
        raise _DispatchHostFailure("canonical dispatch request exceeds its byte limit")
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    configuration = registration.configuration
    configuration_bytes = _canonical_json(configuration).encode("utf-8")
    if len(configuration_bytes) > MAX_DISPATCH_CONFIGURATION_BYTES:
        raise _DispatchHostFailure(
            "canonical dispatch configuration exceeds its byte limit"
        )
    if hashlib.sha256(configuration_bytes).hexdigest() != registration.identity.configuration_sha256:
        raise _DispatchHostFailure("dispatch configuration identity mismatch")
    call_record = _dispatch_call_record(
        adapter_identity=registration.identity.to_dict(),
        configuration=configuration,
        request=request_record,
        request_sha256=request_sha256,
        context=context.to_dict(),
    )
    call_bytes = _canonical_json(call_record).encode("utf-8")
    if len(call_bytes) > MAX_DISPATCH_CALL_BYTES:
        raise _DispatchHostFailure("canonical dispatch call exceeds its byte limit")
    return call_bytes


def _compile_record(
    compiled: CompiledMacro | None,
    error: str | None,
) -> dict[str, object]:
    dispatch = (
        None
        if compiled is None or compiled.dispatch is None
        else _dispatch_request_record(compiled.dispatch)
    )
    return {
        "status": "ok" if compiled is not None else ("error" if error else "not-attempted"),
        "public_commands": [] if compiled is None else list(compiled.public_commands),
        "dispatch": dispatch,
        "dispatch_request_sha256": (
            None
            if dispatch is None
            else hashlib.sha256(_canonical_json(dispatch).encode("utf-8")).hexdigest()
        ),
        "error": error,
    }


def _solver_record(
    request: DispatchRequest,
    context: DispatchContext,
    registration: DispatchAdapterRegistration,
    response: DispatchResponse | None,
    error: str | None,
    *,
    dispatch_call: bytes | None = None,
    raw_response: bytes | None = None,
    host_usage: DispatchHostUsage | None = None,
) -> dict[str, object]:
    request_record = _dispatch_request_record(request)
    request_sha256 = hashlib.sha256(
        _canonical_json(request_record).encode("utf-8")
    ).hexdigest()
    adapter_configuration = registration.configuration
    if response is not None:
        raw_response = response.raw_response
        host_usage = response.host_usage
    return {
        "request": request_record,
        "request_sha256": request_sha256,
        "dispatch_call_request_sha256": (
            None if dispatch_call is None else request_sha256
        ),
        "adapter_configuration": adapter_configuration,
        "dispatch_call_sha256": (
            None
            if dispatch_call is None
            else hashlib.sha256(dispatch_call).hexdigest()
        ),
        "context": context.to_dict(),
        "response_status": None if response is None else response.status,
        "response_steps_used": None if response is None else response.steps_used,
        "raw_response_base64": (
            None if raw_response is None else b64encode(raw_response).decode("ascii")
        ),
        "raw_response_bytes": None if raw_response is None else len(raw_response),
        "raw_response_sha256": (
            None if raw_response is None else hashlib.sha256(raw_response).hexdigest()
        ),
        "host_usage": None if host_usage is None else host_usage.to_dict(),
        "reconstructed_commands": (
            [] if response is None else list(response.public_commands)
        ),
        "error": error,
        "authority": "untrusted-status-reconstruction-required",
        "step_accounting": DISPATCH_STEP_ACCOUNTING,
        "adapter_identity": registration.identity.to_dict(),
        "adapter_identity_sha256": registration.identity.sha256,
    }


def _trace(
    *,
    environment: dict[str, object],
    raw_proposal: dict[str, object],
    parse: dict[str, object],
    compile: dict[str, object],
    state_before: dict[str, object],
    intermediate_states: list[dict[str, object]],
    solver: dict[str, object] | None,
    state_after: dict[str, object],
    accepted: bool,
    error: str | None,
    final_replay: dict[str, object] | None,
) -> MacroTrace:
    return MacroTrace.from_record(
        {
            "format": MACRO_TRACE_FORMAT,
            "v": MACRO_TRACE_VERSION,
            "environment": environment,
            "raw_proposal": raw_proposal,
            "parse": parse,
            "compile": compile,
            "state_before": state_before,
            "intermediate_states": intermediate_states,
            "solver": solver,
            "state_after": state_after,
            "outcome": {
                "status": "accepted" if accepted else "rejected",
                "error": error,
            },
            "final_replay": final_replay,
        }
    )


def _validate_adapters(
    value: dict[str, DispatchAdapterRegistration] | None,
) -> dict[str, DispatchAdapterRegistration]:
    if value is None:
        return {}
    if type(value) is not dict:
        raise TypeError("dispatch_adapters must be an exact dict")
    result: dict[str, DispatchAdapterRegistration] = {}
    for name, registration in value.items():
        if (
            type(name) is not str
            or len(name) > 128
            or _SOLVER_NAME.fullmatch(name) is None
        ):
            raise TypeError("dispatch adapter names must be canonical solver tokens")
        if type(registration) is not DispatchAdapterRegistration:
            raise DispatchProtocolError(
                f"dispatch adapter {name!r} needs an exact provenance registration"
            )
        checked_identity = DispatchAdapterIdentity.from_object(
            registration.identity.to_dict()
        )
        if checked_identity.adapter != name:
            raise DispatchProtocolError(
                f"dispatch registry key {name!r} disagrees with adapter identity "
                f"{checked_identity.adapter!r}"
            )
        # Exact type checks do not protect against ``object.__new__`` followed
        # by forged slot assignment.  Reconstruct every externally supplied
        # registration so canonical configuration, absolute/resolved regular
        # executable path, size bounds, and both identity hashes are checked
        # together.  Only this detached checked copy enters the live registry.
        checked_registration = DispatchAdapterRegistration(
            checked_identity,
            registration.artifact_path,
            registration.configuration_json,
        )
        result[name] = checked_registration
    return result


def start_macro_session(
    theorem: str,
    *,
    capabilities: SurfaceCapabilities = FULL_SURFACE_CAPABILITIES,
) -> MacroOwner:
    """Create one intuitionistic owner for a canonicalized closed profile goal."""

    canonical = canonical_profile_theorem(theorem)
    target, names = parse_formula_with_names(canonical)
    if names:  # pragma: no cover - guaranteed by profile admission
        raise MacroRunnerError("macro theorem unexpectedly retained free variables")
    if type(capabilities) is not SurfaceCapabilities:
        raise TypeError("capabilities must be exact SurfaceCapabilities")
    session = ProofSession(
        state=start(target, names),
        original_target=target,
        original_names=names,
        target_source=canonical,
        classical=False,
        trace=TraceLogger(session_id="peano-hydra-macro-owner"),
    )
    return MacroOwner(
        session,
        capabilities,
        _canonical_json(_capability_identity(capabilities)),
        _canonical_json(semantic_profile_identity()),
    )


def _validate_owner(owner: MacroOwner) -> None:
    if type(owner) is not MacroOwner:
        raise TypeError("macro execution needs an exact MacroOwner")
    MacroOwner(
        owner.session,
        owner.capabilities,
        owner.capability_identity_json,
        owner.semantic_profile_identity_json,
    )
    if owner.classical:
        raise MacroRunnerError("Hydra macro execution is intuitionistic; classical mode is forbidden")
    if owner.original_names:
        raise MacroRunnerError("Hydra macro execution requires a closed original theorem")
    if owner.state.target != owner.original_target:
        raise MacroRunnerError("proof state no longer carries the owner-held original target")
    canonical = pretty_formula(owner.original_target, [])
    if canonical_profile_theorem(canonical) != canonical:
        raise MacroRunnerError("owner theorem is outside the registered semantic profile")
    if owner.state.is_done():
        raise MacroRunnerError("there is no open goal for a macro action")
    if len(owner.replay_steps) > MAX_OWNER_REPLAY_STEPS:
        raise MacroRunnerError("macro owner replay exceeds its cumulative step limit")
    _verify_owner_prefix(owner)


def _free_term_names(source: str) -> tuple[str, ...]:
    try:
        _, names = parse_term_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise MacroRunnerError(f"invalid contextual term: {_error_text(exc)}") from None
    return names


def _free_formula_names(source: str) -> tuple[str, ...]:
    try:
        _, names = parse_formula_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise MacroRunnerError(f"invalid contextual formula: {_error_text(exc)}") from None
    return names


def _require_names_in_scope(label: str, names: tuple[str, ...], allowed: set[str]) -> None:
    unknown = tuple(name for name in names if name not in allowed)
    if unknown:
        raise MacroRunnerError(
            f"{label} uses out-of-context variable(s): {', '.join(unknown)}"
        )


def _contextually_validate(action: Macro, goal: Goal) -> None:
    variables = set(goal.variables)
    context_names = {name for name, _ in goal.context}
    if type(action) is Use:
        for index, term in enumerate(action.specializations):
            _require_names_in_scope(
                f"Use.specializations[{index}]",
                _free_term_names(term),
                variables,
            )
    elif type(action) is Cut:
        _require_names_in_scope(
            "Cut.formula", _free_formula_names(action.formula), variables
        )
        if action.name in variables | context_names:
            raise MacroRunnerError(f"Cut.name {action.name!r} is already in use")
    elif type(action) is Witness:
        _require_names_in_scope("Witness.term", _free_term_names(action.term), variables)
    elif type(action) is Induct:
        allowed = variables | {action.variable}
        _require_names_in_scope(
            "Induct.motive", _free_formula_names(action.motive), allowed
        )
    elif type(action) is Rewrite:
        if action.source not in context_names and axiom_formula(action.source) is None:
            raise MacroRunnerError(
                f"Rewrite.source {action.source!r} is not a visible equation or PA axiom"
            )
        if action.location is not None and action.location not in context_names:
            raise MacroRunnerError(
                f"Rewrite.location {action.location!r} is not a visible hypothesis"
            )
    elif type(action) in (Split, Dispatch):
        return
    else:  # pragma: no cover - parser is exhaustive
        raise MacroRunnerError("unsupported typed macro action")


def _derived_induction_motive(after: MacroOwner) -> str:
    if len(after.state.goals) < 2:
        raise MacroRunnerError("induction did not produce its base and step goals")
    step = after.state.goals[1]
    if not step.context:
        raise MacroRunnerError("induction step did not expose an induction hypothesis")
    motive = step.context[0][1]
    return pretty_formula(motive, list(step.variables))


def _resolve_dispatch_context(
    owner: MacroOwner,
    request: DispatchRequest,
) -> DispatchContext:
    goal = owner.state.current()
    if goal is None:
        raise DispatchProtocolError("dispatch requires a focused open goal")
    contextual = {name: formula for name, formula in goal.context}
    premises: list[DispatchPremise] = []
    for name in request.premises:
        if name in contextual:
            formula = apply_formula_subst(contextual[name], owner.state.subst)
            premises.append(
                DispatchPremise(
                    name,
                    "hypothesis",
                    pretty_formula(formula, list(goal.variables)),
                )
            )
            continue
        axiom = axiom_formula(name)
        if axiom is not None:
            premises.append(DispatchPremise(name, "pa-axiom", pretty_formula(axiom, [])))
            continue
        theorem = get_theorem(name)
        if theorem is None or theorem.name != name:
            raise DispatchProtocolError(f"dispatch premise {name!r} is unavailable")
        allowed = owner.capabilities.allowed_theorems
        if allowed is not None and theorem.name not in allowed:
            raise DispatchProtocolError(
                f"dispatch premise {name!r} is masked by capability environment {owner.capabilities.label!r}"
            )
        premises.append(
            DispatchPremise(
                theorem.name,
                "public-theorem",
                canonical_profile_theorem(theorem.statement),
            )
        )
    theorem_text = pretty_formula(owner.original_target, [])
    return DispatchContext(
        theorem_text,
        tuple(render_goals(owner.state)),
        tuple(premises),
    )


class _DispatchHostFailure(DispatchProtocolError):
    """Internal failure carrying only inert, host-observed process evidence."""

    def __init__(
        self,
        message: str,
        *,
        raw_response: bytes | None = None,
        host_usage: DispatchHostUsage | None = None,
    ) -> None:
        super().__init__(message)
        self.raw_response = raw_response
        self.host_usage = host_usage


def _dispatch_preexec(bounds) -> None:
    """Install hard POSIX limits in the child immediately before ``exec``."""

    resource.setrlimit(
        resource.RLIMIT_CPU,
        (max(1, math.ceil(bounds.max_wall_time_ms / 1_000)),) * 2,
    )
    # Darwin exposes RLIMIT_AS/RLIMIT_DATA constants but rejects useful finite
    # values in ``preexec_fn``.  Linux therefore supplies the campaign-eligible
    # hard ceiling; the parent's sampled leader RSS is diagnostic on Darwin and
    # defense-in-depth observation on Linux, never an exact peak measurement.
    if sys.platform.startswith("linux"):
        for limit_name in ("RLIMIT_AS", "RLIMIT_DATA"):
            limit = getattr(resource, limit_name, None)
            if limit is not None:
                resource.setrlimit(limit, (bounds.max_memory_bytes,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (bounds.max_output_bytes,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    nofile = getattr(resource, "RLIMIT_NOFILE", None)
    if nofile is not None:
        resource.setrlimit(nofile, (64, 64))
    nproc = getattr(resource, "RLIMIT_NPROC", None)
    if nproc is None:
        raise RuntimeError("this host cannot enforce a one-process dispatch limit")
    resource.setrlimit(nproc, (1, 1))


def _parse_dispatch_response(
    raw: bytes,
    usage: DispatchHostUsage,
) -> DispatchResponse:
    try:
        text = raw.decode("utf-8")
        value = json.loads(
            text,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise _DispatchHostFailure(
            f"dispatch response is not strict UTF-8 JSON: {_error_text(exc)}",
            raw_response=raw,
            host_usage=usage,
        ) from None
    evidence_usage = usage
    try:
        response = _exact_object(
            "dispatch subprocess response", value, _DISPATCH_RESPONSE_FIELDS
        )
        if (
            response["format"] != DISPATCH_RESPONSE_FORMAT
            or type(response["v"]) is not int
            or response["v"] != DISPATCH_RESPONSE_VERSION
        ):
            raise DispatchProtocolError(
                "dispatch response has an unsupported identity"
            )
        if _canonical_json(response).encode("utf-8") != raw:
            raise DispatchProtocolError(
                "dispatch response is not canonical compact JSON"
            )
        commands = response["public_commands"]
        if type(commands) is not list:
            raise DispatchProtocolError(
                "dispatch public_commands must be an exact JSON array"
            )
        command_tuple = tuple(commands)
        reconstructed_bytes = sum(
            len(command.encode("utf-8")) if type(command) is str else 0
            for command in command_tuple
        )
        evidence_usage = DispatchHostUsage(
            wall_time_ms=usage.wall_time_ms,
            output_bytes=usage.output_bytes,
            reconstructed_command_bytes=reconstructed_bytes,
            max_observed_rss_bytes=usage.max_observed_rss_bytes,
            peak_processes=usage.peak_processes,
            exit_code=usage.exit_code,
            timed_out=usage.timed_out,
            wall_limit_ms=usage.wall_limit_ms,
            memory_limit_bytes=usage.memory_limit_bytes,
            output_limit_bytes=usage.output_limit_bytes,
            process_limit=usage.process_limit,
            memory_enforcement=usage.memory_enforcement,
            process_enforcement=usage.process_enforcement,
            campaign_host_eligible=usage.campaign_host_eligible,
        )
        return DispatchResponse(
            response["status"],  # type: ignore[arg-type]
            response["steps_used"],  # type: ignore[arg-type]
            command_tuple,  # type: ignore[arg-type]
            raw,
            evidence_usage,
        )
    except (
        DispatchProtocolError,
        TypeError,
        ValueError,
        UnicodeEncodeError,
        RecursionError,
        OverflowError,
    ) as exc:
        raise _DispatchHostFailure(
            _error_text(exc), raw_response=raw, host_usage=evidence_usage
        ) from None


def _process_group_usage(process_group: int) -> tuple[int, int]:
    """Return live direct-child count/RSS without spawning another program.

    ``RLIMIT_NPROC=1`` is installed before exec, so the adapter cannot create a
    second process.  Linux RSS comes from procfs; Darwin RSS comes from the
    stable ``proc_pid_rusage`` ABI.  Unsupported hosts fail closed.
    """

    if sys.platform.startswith("linux"):
        status = Path(f"/proc/{process_group}/status")
        try:
            lines = status.read_text(encoding="ascii").splitlines()
        except FileNotFoundError:
            return 0, 0
        except OSError as exc:
            raise _DispatchHostFailure(
                f"dispatch host procfs monitor failed: {_error_text(exc)}"
            ) from None
        for line in lines:
            if line.startswith("VmRSS:"):
                columns = line.split()
                if len(columns) >= 2:
                    return 1, int(columns[1]) * 1_024
        return 1, 0
    if sys.platform == "darwin":
        try:
            libproc = ctypes.CDLL("/usr/lib/libproc.dylib", use_errno=True)
            proc_pid_rusage = libproc.proc_pid_rusage
            proc_pid_rusage.argtypes = [
                ctypes.c_int,
                ctypes.c_int,
                ctypes.c_void_p,
            ]
            proc_pid_rusage.restype = ctypes.c_int
            # The ABI writes the complete rusage_info_v2 structure.  Reserve
            # generous storage rather than a dangerous truncated ctypes
            # prefix; ``ri_resident_size`` is the uint64 at byte offset 64.
            info = ctypes.create_string_buffer(512)
            result = proc_pid_rusage(process_group, 2, ctypes.byref(info))
        except (OSError, AttributeError, TypeError) as exc:
            raise _DispatchHostFailure(
                f"dispatch host Darwin monitor failed: {_error_text(exc)}"
            ) from None
        if result == 0:
            resident = ctypes.c_uint64.from_buffer(info, 64).value
            return 1, int(resident)
        error_number = ctypes.get_errno()
        if error_number in {3, 22}:  # ESRCH or an already-reaped process
            return 0, 0
        raise _DispatchHostFailure(
            f"dispatch host Darwin monitor failed with errno {error_number}"
        )
    raise _DispatchHostFailure(
        f"dispatch host cannot enforce live memory bounds on {sys.platform!r}"
    )


def _kill_process_group(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            process.kill()
        except ProcessLookupError:
            pass


def _invoke_dispatch_subprocess(
    registration: DispatchAdapterRegistration,
    request: DispatchRequest,
    context: DispatchContext,
    call_bytes: bytes,
) -> DispatchResponse:
    """Invoke one detached executable through the trusted bounded host.

    The executable receives only canonical JSON over stdin.  Its stdout remains
    inert bytes until the process has exited within all host bounds; even a
    syntactically valid response gains authority only after its commands pass
    public-surface reconstruction.
    """

    if type(call_bytes) is not bytes:
        raise _DispatchHostFailure("prepared dispatch call must be exact bytes")
    expected_call_bytes = _prepare_dispatch_call(registration, request, context)
    if call_bytes != expected_call_bytes:
        raise _DispatchHostFailure("prepared and invoked dispatch call bytes differ")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise _DispatchHostFailure(
            "dispatch host refuses privileged execution because RLIMIT_NPROC "
            "cannot enforce the one-process bound for uid 0"
        )
    detached_call = json.loads(call_bytes)
    request_record = _dispatch_request_record(request)
    request_bytes = _canonical_json(request_record).encode("utf-8")
    request_sha256 = hashlib.sha256(request_bytes).hexdigest()
    invoked_request_bytes = _canonical_json(detached_call["request"]).encode("utf-8")
    if invoked_request_bytes != request_bytes or hashlib.sha256(invoked_request_bytes).hexdigest() != request_sha256:
        raise _DispatchHostFailure("compiled and invoked dispatch request bytes differ")

    bounds = request.bounds
    raw: bytes | None = None
    usage: DispatchHostUsage | None = None
    try:
        with tempfile.TemporaryDirectory(prefix="peano-hydra-dispatch-") as directory:
            root = Path(directory)
            executable = root / "adapter"
            shutil.copyfile(registration.artifact_path, executable)
            executable.chmod(0o500)
            if _file_sha256_bounded(executable, MAX_DISPATCH_ARTIFACT_BYTES) != registration.identity.artifact_sha256:
                raise _DispatchHostFailure("copied dispatch artifact identity mismatch")
            input_path = root / "request.json"
            input_path.write_bytes(call_bytes)
            output_path = root / "response.bin"
            with input_path.open("rb") as detached_input, output_path.open("w+b") as output:
                started = time.monotonic()
                try:
                    process = subprocess.Popen(
                        [str(executable)],
                        stdin=detached_input,
                        stdout=output,
                        stderr=subprocess.DEVNULL,
                        cwd=root,
                        env={"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C"},
                        close_fds=True,
                        start_new_session=True,
                        preexec_fn=lambda: _dispatch_preexec(bounds),
                    )
                except (OSError, subprocess.SubprocessError) as exc:
                    raise _DispatchHostFailure(
                        f"cannot launch bounded dispatch subprocess: {_error_text(exc)}"
                    ) from None
                timed_out = False
                memory_exceeded = False
                process_exceeded = False
                output_exceeded = False
                max_observed_rss_bytes = 0
                peak_processes = 0
                while True:
                    observed_processes, observed_memory = _process_group_usage(process.pid)
                    peak_processes = max(peak_processes, observed_processes)
                    max_observed_rss_bytes = max(
                        max_observed_rss_bytes, observed_memory
                    )
                    elapsed_ms = math.ceil((time.monotonic() - started) * 1_000)
                    try:
                        observed_output = output_path.stat().st_size
                    except OSError as exc:
                        _kill_process_group(process)
                        process.wait()
                        raise _DispatchHostFailure(
                            f"cannot inspect dispatch output: {_error_text(exc)}"
                        ) from None
                    timed_out = elapsed_ms > bounds.max_wall_time_ms
                    memory_exceeded = observed_memory > bounds.max_memory_bytes
                    process_exceeded = observed_processes > 1
                    output_exceeded = observed_output > bounds.max_output_bytes
                    if timed_out or memory_exceeded or process_exceeded or output_exceeded:
                        _kill_process_group(process)
                        process.wait()
                        break
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)
                wall_time_ms = math.ceil((time.monotonic() - started) * 1_000)
                timed_out = timed_out or wall_time_ms > bounds.max_wall_time_ms
                output.flush()
                size = output_path.stat().st_size
                output.seek(0)
                raw = output.read(bounds.max_output_bytes + 1)
                usage = DispatchHostUsage(
                    wall_time_ms=wall_time_ms,
                    output_bytes=size,
                    reconstructed_command_bytes=0,
                    max_observed_rss_bytes=max_observed_rss_bytes,
                    peak_processes=peak_processes,
                    exit_code=process.returncode,
                    timed_out=timed_out,
                    wall_limit_ms=bounds.max_wall_time_ms,
                    memory_limit_bytes=bounds.max_memory_bytes,
                    output_limit_bytes=bounds.max_output_bytes,
                    process_limit=1,
                    memory_enforcement=(
                        LINUX_MEMORY_ENFORCEMENT
                        if sys.platform.startswith("linux")
                        else DARWIN_MEMORY_ENFORCEMENT
                    ),
                    process_enforcement="rlimit-nproc-one",
                    campaign_host_eligible=sys.platform.startswith("linux"),
                )
    except _DispatchHostFailure:
        raise
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        raise _DispatchHostFailure(
            f"dispatch host failed closed: {_error_text(exc)}",
            raw_response=raw,
            host_usage=usage,
        ) from None

    if usage is None or raw is None:  # pragma: no cover - structured scope invariant
        raise _DispatchHostFailure("dispatch host produced no process evidence")
    if usage.timed_out:
        raise _DispatchHostFailure(
            "dispatch subprocess exceeded its wall-time bound",
            raw_response=raw,
            host_usage=usage,
        )
    if memory_exceeded:
        raise _DispatchHostFailure(
            "dispatch subprocess exceeded its memory bound",
            raw_response=raw,
            host_usage=usage,
        )
    if process_exceeded:
        raise _DispatchHostFailure(
            "dispatch subprocess exceeded its one-process bound",
            raw_response=raw,
            host_usage=usage,
        )
    if output_exceeded:
        raise _DispatchHostFailure(
            "dispatch subprocess exceeded its output bound",
            raw_response=raw,
            host_usage=usage,
        )
    if usage.output_bytes > bounds.max_output_bytes or len(raw) != usage.output_bytes:
        raise _DispatchHostFailure(
            "dispatch subprocess exceeded its output bound",
            raw_response=raw,
            host_usage=usage,
        )
    if usage.exit_code != 0:
        raise _DispatchHostFailure(
            f"dispatch subprocess exited unsuccessfully with status {usage.exit_code}",
            raw_response=raw,
            host_usage=usage,
        )
    return _parse_dispatch_response(raw, usage)


def _enforce_dispatch_response(
    request: DispatchRequest,
    response: DispatchResponse,
    *,
    capabilities: SurfaceCapabilities,
) -> tuple[str, ...]:
    if type(response) is not DispatchResponse:
        raise DispatchProtocolError("adapter must return an exact DispatchResponse")
    bounds = request.bounds
    usage = response.host_usage
    if usage.timed_out or usage.exit_code != 0:
        raise DispatchProtocolError("dispatch host did not observe one successful process")
    if usage.wall_limit_ms != bounds.max_wall_time_ms:
        raise DispatchProtocolError("dispatch wall-time bound changed after compilation")
    if usage.wall_time_ms > bounds.max_wall_time_ms:
        raise DispatchProtocolError("dispatch host observed wall time above its bound")
    if usage.memory_limit_bytes != bounds.max_memory_bytes:
        raise DispatchProtocolError("dispatch memory bound changed after compilation")
    if usage.output_limit_bytes != bounds.max_output_bytes:
        raise DispatchProtocolError("dispatch output bound changed after compilation")
    if usage.max_observed_rss_bytes > bounds.max_memory_bytes:
        raise DispatchProtocolError("dispatch host observed memory above its bound")
    if usage.peak_processes > usage.process_limit:
        raise DispatchProtocolError("dispatch host observed more than one adapter process")
    if usage.output_bytes + usage.reconstructed_command_bytes > bounds.max_output_bytes:
        raise DispatchProtocolError(
            "dispatch raw response plus reconstructed commands exceeds max_output_bytes"
        )
    if response.steps_used > bounds.max_steps:
        raise DispatchProtocolError(
            f"dispatch steps_used {response.steps_used} exceeds bound {bounds.max_steps}"
        )
    if len(response.public_commands) > bounds.max_steps:
        raise DispatchProtocolError(
            "dispatch reconstructed command count exceeds max_steps"
        )
    if not response.public_commands:
        raise DispatchProtocolError(
            "solver status alone has no authority; dispatch returned no reconstruction commands"
        )
    if response.steps_used < len(response.public_commands):
        raise DispatchProtocolError(
            "dispatch step accounting is smaller than its reconstructed command count"
        )
    checked: list[str] = []
    for index, command in enumerate(response.public_commands):
        if (
            not command
            or len(command) > MAX_INPUT
            or command != command.strip()
            or command.splitlines() != [command]
            or command != " ".join(command.split())
            or "#" in command
            or any(
                unicodedata.category(character) in _UNSAFE_CATEGORIES
                for character in command
            )
        ):
            raise DispatchProtocolError(
                f"dispatch command {index} is not one bounded canonical physical line"
            )
        dangerous = oversized_numeral(command)
        if dangerous is not None:
            raise DispatchProtocolError(
                f"dispatch command {index} contains out-of-profile numeral {dangerous}"
            )
        head = command.split(maxsplit=1)[0]
        if head in _SESSION_COMMANDS:
            raise DispatchProtocolError(
                f"dispatch command {index} is a hidden/session command"
            )
        try:
            surface_transaction_name(command, False, capabilities)
        except (TacticError, TypeError, ValueError, RecursionError) as exc:
            raise DispatchProtocolError(
                f"dispatch command {index} is not reconstructable on the public surface: "
                f"{_error_text(exc)}"
            ) from None
        checked.append(command)
    return tuple(checked)


def _fresh_final_replay(
    owner: MacroOwner,
) -> tuple[Proof, dict[str, object]]:
    theorem = pretty_formula(owner.original_target, [])
    fresh = ProofSession(
        state=start(owner.original_target, owner.original_names),
        original_target=owner.original_target,
        original_names=owner.original_names,
        target_source=theorem,
        classical=False,
        trace=TraceLogger(session_id="peano-hydra-macro-final-replay"),
    )
    commands: list[str] = []
    try:
        for step in owner.replay_steps:
            if step.classical:
                raise MacroRunnerError("fresh replay encountered forbidden classical authority")
            commands.append(step.command)
            fresh = run_surface(
                fresh,
                step.command,
                capabilities=owner.capabilities,
                record_trace=False,
            )
        certificate = checked_surface_final(
            fresh.state,
            owner.original_target,
            classical=False,
        )
        nodes, depth = proof_metrics(certificate)
        fuel = 8 * nodes + 16
        artifact = encode_artifact_bounded(
            fuel,
            owner.original_target,
            certificate,
            max_bytes=MAX_FINAL_ARTIFACT_BYTES,
        )
    except Exception as exc:
        record = {
            "status": "rejected",
            "fresh": True,
            "original_theorem": theorem,
            "commands": commands,
            "kernel_accepted": False,
            "certificate_representation": None,
            "certificate_sha256": None,
            "certificate_nodes": None,
            "certificate_depth": None,
            "error": _error_text(exc),
        }
        raise _FinalReplayFailure(_error_text(exc), record) from None
    return certificate, {
        "status": "accepted",
        "fresh": True,
        "original_theorem": theorem,
        "commands": commands,
        "kernel_accepted": True,
        "certificate_representation": "peano-lab-v2",
        "certificate_sha256": hashlib.sha256(artifact).hexdigest(),
        "certificate_nodes": nodes,
        "certificate_depth": depth,
        "error": None,
    }


class _FinalReplayFailure(RuntimeError):
    def __init__(self, message: str, record: dict[str, object]) -> None:
        super().__init__(message)
        self.record = record


def execute_macro(
    owner: MacroOwner,
    raw_proposal: str | bytes,
    *,
    dispatch_adapters: dict[str, DispatchAdapterRegistration] | None = None,
) -> MacroExecution:
    """Parse, compile, and execute one H0.3 macro as an atomic transaction.

    On failure this function raises :class:`MacroExecutionError`.  Its
    ``owner`` attribute is the caller's identical immutable owner, while its
    canonical trace describes any discarded intermediate states.  On success
    the returned owner is the committed successor.  A closed successor always
    carries a certificate accepted by a fresh original-goal replay.
    """

    _validate_owner(owner)
    adapters = _validate_adapters(dispatch_adapters)
    environment = _environment_record(owner, adapters)
    raw_record = _raw_proposal_record(raw_proposal)
    before_record = _state_record(owner)
    parse_record = _parse_record(None, None)
    compile_record = _compile_record(None, None)
    intermediates: list[dict[str, object]] = []
    solver_record: dict[str, object] | None = None
    final_replay: dict[str, object] | None = None

    def reject(message: object) -> "NoReturn":
        error = _error_text(message)
        trace = _trace(
            environment=environment,
            raw_proposal=raw_record,
            parse=parse_record,
            compile=compile_record,
            state_before=before_record,
            intermediate_states=intermediates,
            solver=solver_record,
            state_after=before_record,
            accepted=False,
            error=error,
            final_replay=final_replay,
        )
        raise MacroExecutionError(error, owner=owner, trace=trace)

    try:
        action = parse_macro(raw_proposal)
    except (MacroProtocolError, TypeError, ValueError, RecursionError) as exc:
        parse_record = _parse_record(None, _error_text(exc))
        reject(exc)
    parse_record = _parse_record(action, None)

    goal = owner.state.current()
    if goal is None:  # guarded by _validate_owner
        reject("there is no focused goal")
    try:
        _contextually_validate(action, goal)
        compiled = compile_macro(
            action,
            capabilities=owner.capabilities,
            available_solvers=tuple(sorted(adapters)),
        )
    except (MacroRunnerError, MacroCompileError, TacticError, TypeError, ValueError, RecursionError) as exc:
        compile_record = _compile_record(None, _error_text(exc))
        reject(exc)
    compile_record = _compile_record(compiled, None)

    commands = compiled.public_commands
    context: DispatchContext | None = None
    response: DispatchResponse | None = None
    dispatch_call: bytes | None = None
    if compiled.dispatch is not None:
        request = compiled.dispatch
        registration = adapters[request.solver]
        try:
            context = _resolve_dispatch_context(owner, request)
        except (DispatchProtocolError, TypeError, ValueError, RecursionError) as exc:
            # A context exists syntactically even if premise resolution failed;
            # retain the exact request and error without inventing statements.
            context = DispatchContext(
                pretty_formula(owner.original_target, []),
                tuple(render_goals(owner.state)),
                (),
            )
            solver_record = _solver_record(
                request, context, registration, None, _error_text(exc)
            )
            reject(exc)
        try:
            dispatch_call = _prepare_dispatch_call(registration, request, context)
            response = _invoke_dispatch_subprocess(
                registration, request, context, dispatch_call
            )
            solver_record = _solver_record(
                request,
                context,
                registration,
                response,
                None,
                dispatch_call=dispatch_call,
            )
            commands = _enforce_dispatch_response(
                request,
                response,
                capabilities=owner.capabilities,
            )
        except _DispatchHostFailure as exc:
            solver_record = _solver_record(
                request,
                context,
                registration,
                None,
                _error_text(exc),
                dispatch_call=dispatch_call,
                raw_response=exc.raw_response,
                host_usage=exc.host_usage,
            )
            reject(exc)
        except Exception as exc:
            solver_record = _solver_record(
                request,
                context,
                registration,
                response,
                _error_text(exc),
                dispatch_call=dispatch_call,
            )
            reject(exc)

    if len(owner.replay_steps) + len(commands) > MAX_OWNER_REPLAY_STEPS:
        reject("macro execution exceeds the owner cumulative replay-step limit")
    temporary = owner
    for index, command in enumerate(commands):
        try:
            next_session = run_surface(
                temporary.session,
                command,
                capabilities=owner.capabilities,
                record_trace=False,
            )
            temporary = temporary.with_session(next_session)
            intermediates.append(
                {
                    "command_index": index,
                    "command": command,
                    "state_summary": _state_summary(temporary),
                }
            )
            if type(action) is Induct:
                derived = _derived_induction_motive(temporary)
                if derived != action.motive:
                    raise MacroRunnerError(
                        "Induct.motive does not equal the motive derived by the proof engine; "
                        f"expected {derived!r}"
                    )
        except Exception as exc:
            reject(exc)

    certificate: Proof | None = None
    if temporary.state.is_done():
        try:
            certificate, final_replay = _fresh_final_replay(temporary)
        except _FinalReplayFailure as exc:
            final_replay = exc.record
            reject(f"fresh original-goal kernel replay failed: {exc}")

    after_record = _state_record(temporary)
    trace = _trace(
        environment=environment,
        raw_proposal=raw_record,
        parse=parse_record,
        compile=compile_record,
        state_before=before_record,
        intermediate_states=intermediates,
        solver=solver_record,
        state_after=after_record,
        accepted=True,
        error=None,
        final_replay=final_replay,
    )
    return MacroExecution(temporary, action, tuple(commands), trace, certificate)


__all__ = [
    "MACRO_TRACE_FORMAT",
    "MACRO_TRACE_VERSION",
    "DISPATCH_ADAPTER_IDENTITY_FORMAT",
    "DISPATCH_ADAPTER_IDENTITY_VERSION",
    "DISPATCH_CALL_FORMAT",
    "DISPATCH_CALL_VERSION",
    "DISPATCH_RESPONSE_FORMAT",
    "DISPATCH_RESPONSE_VERSION",
    "MAX_DISPATCH_COMMANDS",
    "MAX_DISPATCH_CONFIGURATION_BYTES",
    "MAX_DISPATCH_REQUEST_BYTES",
    "MAX_DISPATCH_ARTIFACT_BYTES",
    "MAX_MACRO_TRACE_BYTES",
    "MAX_OWNER_REPLAY_STEPS",
    "MAX_FINAL_ARTIFACT_BYTES",
    "MacroRunnerError",
    "DispatchProtocolError",
    "DispatchAdapterIdentity",
    "DispatchHostUsage",
    "DispatchResponse",
    "DispatchPremise",
    "DispatchContext",
    "DispatchAdapterRegistration",
    "MacroOwner",
    "MacroTrace",
    "MacroExecution",
    "MacroExecutionError",
    "register_dispatch_subprocess",
    "start_macro_session",
    "execute_macro",
]
