"""Strict native-PA authoring records for the Peano Hydra workbench.

The records in this module are inert, content-addressed authoring data.  They
do not add a proof language and they do not let prose, a model response, or a
serialized Boolean grant theorem authority.  In particular, a checked theorem
proposal can be built or loaded only by supplying a real kernel ``Formula``
and ``Proof`` which pass a fresh empty-context check against the original
formula through :mod:`training.peano_hydra.result_schema`.

All loaders accept only compact canonical JSON bytes.  Duplicate keys,
floating-point values, extra fields, unsafe text, stale document revisions,
and mismatched source excerpts fail closed.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from typing import Literal, TypeVar

from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Formula,
    Imp,
    Or,
    parse_formula,
    pretty_formula,
)
from peano_lab.kernel.proofs import Cut, Proof
from peano_lab.kernel.terms import Add, Mul, Succ, Var, Zero
from peano_lab.engine.state import proof_resource_metrics
from peano_lab.library.defined_syntax import (
    ALL_DEFINITIONS_BY_NAME,
    DEFINED_SYNTAX_REGISTRY_ID,
    DEFINED_SYNTAX_REGISTRY_SHA256,
    DEFINED_SYNTAX_VERSION,
    parse_defined_formula_with_names,
)

from .profile import (
    canonical_registered_profile_formula,
    canonical_registered_profile_theorem,
    semantic_profile_registration,
    semantic_profile_sha256,
)
from .result_schema import (
    CERTIFICATE_REPRESENTATION,
    HydraResultSchemaError,
    build_checked_proved_evidence,
)


AUTHORING_SCHEMA_FORMAT = "peano-hydra-authoring-schema"
AUTHORING_SCHEMA_VERSION = 1
AUTHORING_SCHEMA_ID = "peano-hydra-native-pa-authoring-core-v1"
AUTHORING_SCHEMA_PATH = Path(__file__).with_name("authoring-schema-v1.json")
AUTHORING_SCHEMA_SHA256 = (
    "31a344bbc0b22cfacf5803c85d25a80a0234cf7387395283c5e1ab25ada80553"
)

# The authoring contract is versioned independently of the library module that
# implements readable defined syntax.  Pin that external semantic dependency so
# a registry edit cannot silently change what authoring-schema-v1 accepts.
PINNED_DEFINED_SYNTAX_REGISTRY_ID = "peano-lab.defined-predicates"
PINNED_DEFINED_SYNTAX_VERSION = 2
PINNED_DEFINED_SYNTAX_REGISTRY_SHA256 = (
    "924c8bc220f23ce772b72991b8234c3499be7698dc086d90509d39760a1ed0fe"
)

DOCUMENT_FORMAT = "peano-hydra-authoring-document"
BINDING_FORMAT = "peano-hydra-authoring-binding"
LIBRARY_EPOCH_FORMAT = "peano-hydra-library-epoch"
SOURCE_EXCERPT_FORMAT = "peano-hydra-source-excerpt"
UNIT_FORMAT = "peano-hydra-authoring-unit"
PROVENANCE_FORMAT = "peano-hydra-authoring-provenance"
CANDIDATE_FORMAT = "peano-hydra-formalization-candidate"
DIAGNOSTIC_FORMAT = "peano-hydra-authoring-diagnostic"
KERNEL_DIAGNOSTIC_EVIDENCE_FORMAT = "peano-hydra-kernel-diagnostic-evidence"
PROOF_ATTEMPT_FORMAT = "peano-hydra-proof-attempt"
PROPOSAL_FORMAT = "peano-hydra-theorem-proposal"
LIFECYCLE_EVENT_FORMAT = "peano-hydra-authoring-lifecycle-event"
EXPORT_EVENT_FORMAT = "peano-hydra-authoring-export-event"
RECORD_VERSION = 1

MAX_SCHEMA_BYTES = 1_000_000
MAX_RECORD_BYTES = 2_000_000
MAX_DOCUMENT_BYTES = 1_000_000
MAX_EXCERPT_BYTES = 65_536
MAX_MESSAGE_BYTES = 8_000
MAX_SUMMARY_BYTES = 32_000
MAX_SCRIPT_BYTES = 1_000_000
MAX_STATEMENT_BYTES = 65_536
MAX_JSON_DEPTH = 64
MAX_JSON_ITEMS = 100_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

DocumentLogic = Literal["intuitionistic", "classical"]
TrainingConsent = Literal["deny", "allow-anonymized", "allow-exact"]
UnitKind = Literal["claim", "definition", "proof_step", "exposition", "question"]
ProvenanceKind = Literal["human", "model", "rule"]
SurfaceKind = Literal["native-pa", "defined-pa"]
DiagnosticSeverity = Literal["info", "warning", "error"]
DiagnosticAuthority = Literal[
    "kernel",
    "parser",
    "definition-expander",
    "library-graph",
    "bounded-evaluator",
    "untrusted-solver",
    "untrusted-model",
    "human-reviewer",
]
AttemptEngine = Literal["symbolic", "vampire", "model", "human", "hybrid"]
AttemptOutcome = Literal[
    "draft", "candidate-proof", "search-exhausted", "timeout", "error"
]
LifecycleState = Literal[
    "prose_only",
    "ambiguous",
    "formalized_unproved",
    "proved",
    "reviewed",
    "admitted",
]

TRAINING_CONSENTS = ("deny", "allow-anonymized", "allow-exact")
UNIT_KINDS = ("claim", "definition", "proof_step", "exposition", "question")
PROVENANCE_KINDS = ("human", "model", "rule")
DIAGNOSTIC_SEVERITIES = ("info", "warning", "error")
DIAGNOSTIC_AUTHORITIES = (
    "kernel",
    "parser",
    "definition-expander",
    "library-graph",
    "bounded-evaluator",
    "untrusted-solver",
    "untrusted-model",
    "human-reviewer",
)
UNTRUSTED_DIAGNOSTIC_AUTHORITIES = (
    "untrusted-solver",
    "untrusted-model",
)
ATTEMPT_ENGINES = ("symbolic", "vampire", "model", "human", "hybrid")
ATTEMPT_OUTCOMES = (
    "draft",
    "candidate-proof",
    "search-exhausted",
    "timeout",
    "error",
)
LIFECYCLE_STATES = (
    "prose_only",
    "ambiguous",
    "formalized_unproved",
    "proved",
    "reviewed",
    "admitted",
)
LIFECYCLE_AUTHORITIES = (
    "authoring-core",
    "kernel",
    "human-reviewer",
    "catalog-administrator",
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_RECORD_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\Z")
_THEOREM_NAME_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")
_CODE_RE = re.compile(r"[a-z][a-z0-9._-]{0,127}\Z")

_LIBRARY_EPOCH_FIELDS = frozenset({"format", "v", "id", "root_sha256"})
_DOCUMENT_FIELDS = frozenset(
    {
        "format",
        "v",
        "document_id",
        "revision",
        "logic",
        "semantic_profile_sha256",
        "library_epoch",
        "source_text",
        "source_utf8_bytes",
        "source_sha256",
        "training_consent",
    }
)
_BINDING_FIELDS = frozenset(
    {
        "format",
        "v",
        "document_id",
        "document_revision",
        "document_sha256",
        "logic",
        "semantic_profile_sha256",
        "library_epoch",
        "training_consent",
    }
)
_SOURCE_FIELDS = frozenset(
    {"format", "v", "start_utf8", "end_utf8", "text", "sha256"}
)
_UNIT_FIELDS = frozenset(
    {"format", "v", "binding", "unit_id", "kind", "source"}
)
_PROVENANCE_FIELDS = frozenset(
    {"format", "v", "kind", "id", "request_sha256", "response_sha256"}
)
_CONTENT_RECEIPT_FIELDS = frozenset({"id", "sha256"})
_DOC_RECEIPT_FIELDS = frozenset({"target", "sha256"})
_BINDER_FIELDS = frozenset({"index", "path", "quantifier", "name", "depth"})
_ASSUMPTION_FIELDS = frozenset({"index", "path", "readable_formula", "primitive_formula", "sha256"})
_ALTERNATIVE_FIELDS = frozenset(
    {"index", "readable_formula", "primitive_formula", "sha256"}
)
_CANDIDATE_FIELDS = frozenset(
    {
        "format",
        "v",
        "binding",
        "unit_id",
        "unit_sha256",
        "candidate_id",
        "source",
        "surface_kind",
        "readable_formula",
        "expanded_formula",
        "expanded_formula_sha256",
        "primitive_formula",
        "primitive_formula_sha256",
        "binder_table",
        "free_variables",
        "assumptions",
        "alternative_readings",
        "definition_receipts",
        "provenance",
        "ambiguities",
    }
)
_DIAGNOSTIC_FIELDS = frozenset(
    {
        "format",
        "v",
        "binding",
        "unit_id",
        "unit_sha256",
        "diagnostic_id",
        "code",
        "severity",
        "authority",
        "message",
        "source",
        "evidence_sha256",
        "suggested_statement",
    }
)
_KERNEL_DIAGNOSTIC_EVIDENCE_FIELDS = frozenset(
    {
        "format",
        "v",
        "unit_sha256",
        "diagnostic_id",
        "code",
        "severity",
        "message",
        "source",
        "suggested_statement",
        "checked_result",
    }
)
_LINEAGE_FIELDS = frozenset(
    {"lineage_id", "candidate_sha256", "parent_attempt_sha256"}
)
_ATTEMPT_FIELDS = frozenset(
    {
        "format",
        "v",
        "binding",
        "source",
        "candidate_sha256",
        "attempt_id",
        "lineage",
        "engine",
        "outcome",
        "readable_script",
        "readable_script_sha256",
        "provenance",
        "transcript_receipts",
        "diagnostic_receipts",
    }
)
_PROOF_METRICS_FIELDS = frozenset(
    {
        "claim",
        "certificate_sha256",
        "certificate_nodes",
        "distinct_proof_objects",
        "cut_nodes",
        "certificate_bytes",
        "max_depth",
        "replay_observation",
        "readable_script_utf8_bytes",
    }
)
_LIFECYCLE_EVENT_FIELDS = frozenset(
    {
        "format",
        "v",
        "event_id",
        "sequence",
        "proposal_sha256",
        "previous_event_sha256",
        "from_state",
        "to_state",
        "authority",
        "actor_id",
        "session_owner_id",
        "evidence_sha256",
        "registry_sha256",
    }
)
_EXPORT_EVENT_FIELDS = frozenset(
    {
        "format",
        "v",
        "export_id",
        "sequence",
        "proposal_sha256",
        "admitted_event_sha256",
        "actor_id",
        "session_owner_id",
        "patch_root_sha256",
        "destination",
        "mode",
        "evidence_sha256",
        "registry_sha256",
    }
)
_PROPOSAL_COMMON_FIELDS = frozenset(
    {
        "format",
        "v",
        "binding",
        "source",
        "proposal_id",
        "name",
        "candidate_sha256",
        "lineage",
        "primitive_formula",
        "primitive_formula_sha256",
        "readable_dependencies",
        "optimized_dependencies",
        "publication_dependencies",
        "readable_source_proof",
        "readable_source_proof_sha256",
        "mutation_result_receipts",
        "transcript_receipts",
        "documentation_receipts",
        "explanation",
        "human_acceptance",
        "human_review",
        "proof_status",
    }
)
_PROPOSAL_CHECKED_FIELDS = _PROPOSAL_COMMON_FIELDS | {
    "checked_result",
    "proof_metrics",
}


class AuthoringContractError(ValueError):
    """An authoring record violates the native-PA A0 contract."""


@dataclass(frozen=True, slots=True)
class LibraryEpochIdentity:
    """One content-addressed theorem-library view."""

    id: str
    root_sha256: str

    def to_record(self) -> dict[str, object]:
        return {
            "format": LIBRARY_EPOCH_FORMAT,
            "v": RECORD_VERSION,
            "id": self.id,
            "root_sha256": self.root_sha256,
        }


class _CanonicalCarrier:
    """A canonical record minted only by this module's checked boundaries."""

    __slots__ = ("_json",)
    _label = "authoring record"

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise AuthoringContractError(
            f"{type(self).__name__} values come only from checked builders/loaders"
        )

    def __setattr__(self, _name: str, _value: object) -> None:
        raise AttributeError(f"{type(self).__name__} is immutable")

    @property
    def record(self) -> dict[str, object]:
        return _decode_canonical_object(self._json, self._label)

    @property
    def canonical_bytes(self) -> bytes:
        return bytes(self._json)

    @property
    def sha256(self) -> str:
        return _record_sha256(self._json)


class AuthoringDocument(_CanonicalCarrier):
    """Detached canonical bytes for one exact manuscript revision."""

    __slots__ = ()
    _label = "authoring document"


class SentenceUnit(_CanonicalCarrier):
    """One exact source span classified for authoring."""

    __slots__ = ()
    _label = "sentence unit"


class FormalizationCandidate(_CanonicalCarrier):
    """A profile-canonical native-PA reading of one source unit."""

    __slots__ = ()
    _label = "formalization candidate"


class AuthoringDiagnostic(_CanonicalCarrier):
    """Evidence-labeled feedback over one exact source excerpt."""

    __slots__ = ()
    _label = "authoring diagnostic"


class ProofAttempt(_CanonicalCarrier):
    """An untrusted, revision-bound attempt; it never grants checked status."""

    __slots__ = ()
    _label = "proof attempt"


class LifecycleEvent(_CanonicalCarrier):
    """Registry-authenticated append-only authoring lifecycle transport."""

    __slots__ = ()
    _label = "authoring lifecycle event"


class ExportEvent(_CanonicalCarrier):
    """Reviewed inert receipt for an explicit patch-only export action."""

    __slots__ = ()
    _label = "authoring export event"


class TheoremProposal(_CanonicalCarrier):
    """A draft or freshly replayed checked theorem proposal."""

    __slots__ = ("_certificate_artifact",)
    _label = "theorem proposal"

    @property
    def certificate_artifact(self) -> bytes | None:
        artifact = self._certificate_artifact
        return None if artifact is None else bytes(artifact)


_CarrierT = TypeVar("_CarrierT", bound=_CanonicalCarrier)


def _mint_carrier(
    carrier: type[_CarrierT],
    raw: bytes,
    *,
    certificate_artifact: bytes | None = None,
) -> _CarrierT:
    value = object.__new__(carrier)
    object.__setattr__(value, "_json", bytes(raw))
    if carrier is TheoremProposal:
        object.__setattr__(
            value,
            "_certificate_artifact",
            None if certificate_artifact is None else bytes(certificate_artifact),
        )
    return value


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _reject_float(value: str) -> object:
    raise ValueError(f"JSON floating-point number {value!r}")


def _validate_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise AuthoringContractError(f"{path} exceeds the JSON nesting limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise AuthoringContractError(f"{path} is outside the JSON integer domain")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise AuthoringContractError(
                f"{path} contains a non-scalar Unicode surrogate"
            ) from None
        return
    if type(value) not in (list, dict):
        raise AuthoringContractError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise AuthoringContractError(f"{path} contains a cyclic container")
    if len(value) > MAX_JSON_ITEMS:
        raise AuthoringContractError(f"{path} has too many items")
    next_ancestors = ancestors | {marker}
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=next_ancestors,
            )
        return
    for key, item in value.items():
        if type(key) is not str:
            raise AuthoringContractError(f"{path} has a non-string key")
        _validate_json(key, path=f"{path}.<key>", depth=depth + 1)
        _validate_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=next_ancestors,
        )


def canonical_json_bytes(value: object, *, limit: int = MAX_RECORD_BYTES) -> bytes:
    """Encode one strict authoring value as compact sorted-key UTF-8 JSON."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive integer")
    _validate_json(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise AuthoringContractError(
            f"value cannot be encoded as canonical JSON: {exc}"
        ) from None
    if len(encoded) > limit:
        raise AuthoringContractError(
            f"canonical JSON exceeds the {limit}-byte record limit"
        )
    return encoded


def _canonical_document_bytes(value: object) -> bytes:
    _validate_json(value)
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _decode_json(raw: bytes, label: str) -> object:
    if type(raw) is not bytes:
        raise AuthoringContractError(f"{label} must be exact bytes")
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise AuthoringContractError(f"{label} is not strict JSON: {exc}") from None


def _decode_canonical_object(raw: bytes, label: str) -> dict[str, object]:
    if len(raw) > MAX_RECORD_BYTES:
        raise AuthoringContractError(f"{label} exceeds the record limit")
    value = _decode_json(raw, label)
    if type(value) is not dict or canonical_json_bytes(value) != raw:
        raise AuthoringContractError(f"{label} is not one canonical JSON object")
    return value


def _record_sha256(raw: bytes) -> str:
    return hashlib.sha256(b"peano-hydra-authoring-record-v1\0" + raw).hexdigest()


def _require_version(label: str, value: object, expected: int) -> int:
    """Require a JSON integer version without Python's bool/int aliasing."""

    if type(value) is not int or value != expected:
        raise AuthoringContractError(f"{label} must be integer {expected}")
    return value


def authoring_schema() -> dict[str, object]:
    """Load and verify the immutable machine-readable A0 schema."""

    try:
        raw = AUTHORING_SCHEMA_PATH.read_bytes()
    except OSError as exc:
        raise AuthoringContractError("cannot read the authoring schema") from exc
    if len(raw) > MAX_SCHEMA_BYTES:
        raise AuthoringContractError("authoring schema exceeds its byte limit")
    value = _decode_json(raw, "authoring schema")
    if type(value) is not dict or raw != _canonical_document_bytes(value):
        raise AuthoringContractError("authoring schema is not canonical pretty JSON")
    semantic = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    if semantic != AUTHORING_SCHEMA_SHA256:
        raise AuthoringContractError("authoring schema semantic digest drifted")
    if (
        value.get("format") != AUTHORING_SCHEMA_FORMAT
        or value.get("id") != AUTHORING_SCHEMA_ID
        or value.get("phase") != "authoring-core"
        or value.get("additional_fields_policy")
        != "forbidden-at-every-schema-owned-object"
    ):
        raise AuthoringContractError("authoring schema identity is malformed")
    _require_version(
        "authoring schema version", value.get("v"), AUTHORING_SCHEMA_VERSION
    )
    pinned_defined_syntax = {
        "id": PINNED_DEFINED_SYNTAX_REGISTRY_ID,
        "version": PINNED_DEFINED_SYNTAX_VERSION,
        "sha256": PINNED_DEFINED_SYNTAX_REGISTRY_SHA256,
    }
    if value.get("defined_syntax") != pinned_defined_syntax:
        raise AuthoringContractError(
            "authoring schema defined-syntax registration drifted"
        )
    if (
        DEFINED_SYNTAX_REGISTRY_ID,
        DEFINED_SYNTAX_VERSION,
        DEFINED_SYNTAX_REGISTRY_SHA256,
    ) != (
        PINNED_DEFINED_SYNTAX_REGISTRY_ID,
        PINNED_DEFINED_SYNTAX_VERSION,
        PINNED_DEFINED_SYNTAX_REGISTRY_SHA256,
    ):
        raise AuthoringContractError(
            "runtime defined-syntax registry differs from the authoring schema pin"
        )
    objects = value.get("objects")
    expected = {
        "binding": _BINDING_FIELDS,
        "binder_entry": _BINDER_FIELDS,
        "assumption_entry": _ASSUMPTION_FIELDS,
        "alternative_reading": _ALTERNATIVE_FIELDS,
        "content_receipt": _CONTENT_RECEIPT_FIELDS,
        "diagnostic": _DIAGNOSTIC_FIELDS,
        "kernel_diagnostic_evidence": _KERNEL_DIAGNOSTIC_EVIDENCE_FIELDS,
        "document": _DOCUMENT_FIELDS,
        "documentation_receipt": _DOC_RECEIPT_FIELDS,
        "export_event": _EXPORT_EVENT_FIELDS,
        "formalization_candidate": _CANDIDATE_FIELDS,
        "library_epoch": _LIBRARY_EPOCH_FIELDS,
        "lifecycle_event": _LIFECYCLE_EVENT_FIELDS,
        "lineage": _LINEAGE_FIELDS,
        "proof_attempt": _ATTEMPT_FIELDS,
        "proof_metrics": _PROOF_METRICS_FIELDS,
        "provenance": _PROVENANCE_FIELDS,
        "sentence_unit": _UNIT_FIELDS,
        "source_excerpt": _SOURCE_FIELDS,
        "theorem_proposal_checked": _PROPOSAL_CHECKED_FIELDS,
        "theorem_proposal_draft": _PROPOSAL_COMMON_FIELDS,
    }
    if type(objects) is not dict or set(objects) != set(expected):
        raise AuthoringContractError("authoring schema object inventory drifted")
    for name, fields in expected.items():
        item = objects[name]
        if (
            type(item) is not dict
            or item.get("additional_fields") != "forbidden"
            or set(item.get("exact_fields", ())) != fields
        ):
            raise AuthoringContractError(f"authoring schema {name} fields drifted")
    return _decode_canonical_object(canonical_json_bytes(value), "authoring schema")


def authoring_schema_identity() -> dict[str, object]:
    authoring_schema()
    return {
        "format": AUTHORING_SCHEMA_FORMAT,
        "v": AUTHORING_SCHEMA_VERSION,
        "id": AUTHORING_SCHEMA_ID,
        "sha256": AUTHORING_SCHEMA_SHA256,
    }


def _safe_text(
    label: str,
    value: object,
    *,
    max_bytes: int,
    multiline: bool = False,
    nonempty: bool = True,
) -> str:
    if type(value) is not str or (nonempty and not value):
        raise AuthoringContractError(f"{label} must be {'nonempty ' if nonempty else ''}text")
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        raise AuthoringContractError(f"{label} contains a Unicode surrogate") from None
    if len(encoded) > max_bytes:
        raise AuthoringContractError(f"{label} exceeds its {max_bytes}-byte limit")
    for character in value:
        category = unicodedata.category(character)
        if multiline and character == "\n":
            continue
        if category in {"Cc", "Cf", "Cs", "Zl", "Zp"}:
            raise AuthoringContractError(f"{label} contains an unsafe character")
    return value


def _safe_identifier(label: str, value: object) -> str:
    if type(value) is not str or _RECORD_ID_RE.fullmatch(value) is None:
        raise AuthoringContractError(f"{label} is not one bounded safe identifier")
    return value


def _safe_theorem_name(label: str, value: object) -> str:
    if type(value) is not str or _THEOREM_NAME_RE.fullmatch(value) is None:
        raise AuthoringContractError(f"{label} is not one native theorem name")
    return value


def _safe_code(label: str, value: object) -> str:
    if type(value) is not str or _CODE_RE.fullmatch(value) is None:
        raise AuthoringContractError(f"{label} is not one diagnostic code")
    return value


def _sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise AuthoringContractError(f"{label} must be one lowercase SHA-256")
    return value


def _positive_revision(value: object) -> int:
    if type(value) is not int or not 1 <= value <= MAX_SAFE_JSON_INTEGER:
        raise AuthoringContractError("document revision must be a positive integer")
    return value


def _profile_binding(digest: object | None) -> tuple[str, DocumentLogic]:
    profile_digest = semantic_profile_sha256() if digest is None else _sha256(
        "semantic_profile_sha256", digest
    )
    try:
        registration = semantic_profile_registration(profile_digest)
    except ValueError as exc:
        raise AuthoringContractError(str(exc)) from None
    logic = registration.get("logic")
    if logic not in {"intuitionistic", "classical"}:
        raise AuthoringContractError("semantic profile has unsupported authoring logic")
    return profile_digest, logic  # type: ignore[return-value]


def _validate_library_epoch(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != _LIBRARY_EPOCH_FIELDS:
        raise AuthoringContractError("library epoch has missing or additional fields")
    if value.get("format") != LIBRARY_EPOCH_FORMAT:
        raise AuthoringContractError("library epoch identity is malformed")
    _require_version("library epoch version", value.get("v"), RECORD_VERSION)
    _safe_identifier("library epoch id", value.get("id"))
    _sha256("library epoch root", value.get("root_sha256"))
    return value


def library_epoch_identity(epoch_id: str, root_sha256: str) -> LibraryEpochIdentity:
    authoring_schema()
    identity = LibraryEpochIdentity(
        _safe_identifier("library epoch id", epoch_id),
        _sha256("library epoch root", root_sha256),
    )
    _validate_library_epoch(identity.to_record())
    return identity


def _validate_document_record(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != _DOCUMENT_FIELDS:
        raise AuthoringContractError("document has missing or additional fields")
    if value.get("format") != DOCUMENT_FORMAT:
        raise AuthoringContractError("document identity is malformed")
    _require_version("document version", value.get("v"), RECORD_VERSION)
    _safe_identifier("document_id", value.get("document_id"))
    _positive_revision(value.get("revision"))
    profile_digest, logic = _profile_binding(value.get("semantic_profile_sha256"))
    if value.get("logic") != logic:
        raise AuthoringContractError("document logic does not match its semantic profile")
    if value.get("semantic_profile_sha256") != profile_digest:
        raise AuthoringContractError("document semantic profile is malformed")
    _validate_library_epoch(value.get("library_epoch"))
    consent = value.get("training_consent")
    if consent not in TRAINING_CONSENTS:
        raise AuthoringContractError("document training consent is unsupported")
    source = _safe_text(
        "document source",
        value.get("source_text"),
        max_bytes=MAX_DOCUMENT_BYTES,
        multiline=True,
    )
    source_bytes = source.encode("utf-8")
    if value.get("source_utf8_bytes") != len(source_bytes):
        raise AuthoringContractError("document source byte count is inconsistent")
    if value.get("source_sha256") != hashlib.sha256(source_bytes).hexdigest():
        raise AuthoringContractError("document source hash is inconsistent")
    return value


def build_document(
    source_text: str,
    *,
    document_id: str,
    revision: int,
    library_epoch: LibraryEpochIdentity,
    semantic_profile_sha256_value: str | None = None,
    training_consent: TrainingConsent = "deny",
) -> AuthoringDocument:
    """Create one exact manuscript revision; corpus use is denied by default."""

    authoring_schema()
    if type(library_epoch) is not LibraryEpochIdentity:
        raise AuthoringContractError("document needs a LibraryEpochIdentity")
    profile_digest, logic = _profile_binding(semantic_profile_sha256_value)
    source = _safe_text(
        "document source", source_text, max_bytes=MAX_DOCUMENT_BYTES, multiline=True
    )
    source_bytes = source.encode("utf-8")
    record = {
        "format": DOCUMENT_FORMAT,
        "v": RECORD_VERSION,
        "document_id": _safe_identifier("document_id", document_id),
        "revision": _positive_revision(revision),
        "logic": logic,
        "semantic_profile_sha256": profile_digest,
        "library_epoch": library_epoch.to_record(),
        "source_text": source,
        "source_utf8_bytes": len(source_bytes),
        "source_sha256": hashlib.sha256(source_bytes).hexdigest(),
        "training_consent": training_consent,
    }
    checked = _validate_document_record(record)
    return _mint_carrier(AuthoringDocument, canonical_json_bytes(checked))


def load_document(raw: bytes) -> AuthoringDocument:
    authoring_schema()
    checked = _validate_document_record(_decode_canonical_object(raw, "authoring document"))
    return _mint_carrier(AuthoringDocument, canonical_json_bytes(checked))


def _document_binding(document: AuthoringDocument) -> dict[str, object]:
    if type(document) is not AuthoringDocument:
        raise AuthoringContractError("operation needs a validated AuthoringDocument")
    value = _validate_document_record(document.record)
    return {
        "format": BINDING_FORMAT,
        "v": RECORD_VERSION,
        "document_id": value["document_id"],
        "document_revision": value["revision"],
        "document_sha256": document.sha256,
        "logic": value["logic"],
        "semantic_profile_sha256": value["semantic_profile_sha256"],
        "library_epoch": value["library_epoch"],
        "training_consent": value["training_consent"],
    }


def _validate_binding(value: object, document: AuthoringDocument) -> dict[str, object]:
    if type(value) is not dict or set(value) != _BINDING_FIELDS:
        raise AuthoringContractError("authoring binding has missing or additional fields")
    if value.get("format") != BINDING_FORMAT:
        raise AuthoringContractError("authoring binding identity is malformed")
    _require_version("authoring binding version", value.get("v"), RECORD_VERSION)
    _safe_identifier("binding document_id", value.get("document_id"))
    _positive_revision(value.get("document_revision"))
    _sha256("binding document_sha256", value.get("document_sha256"))
    _validate_library_epoch(value.get("library_epoch"))
    if value != _document_binding(document):
        raise AuthoringContractError("authoring record is stale or bound to another document")
    return value


def _excerpt_from_document(
    document: AuthoringDocument,
    start_utf8: int,
    end_utf8: int,
    *,
    allow_empty: bool,
) -> dict[str, object]:
    value = _validate_document_record(document.record)
    raw = value["source_text"].encode("utf-8")  # type: ignore[union-attr]
    if (
        type(start_utf8) is not int
        or type(end_utf8) is not int
        or start_utf8 < 0
        or end_utf8 < start_utf8
        or end_utf8 > len(raw)
        or (not allow_empty and start_utf8 == end_utf8)
    ):
        raise AuthoringContractError("source span is outside the document")
    try:
        text = raw[start_utf8:end_utf8].decode("utf-8")
    except UnicodeDecodeError:
        raise AuthoringContractError("source span splits a UTF-8 code point") from None
    _safe_text(
        "source excerpt",
        text,
        max_bytes=MAX_EXCERPT_BYTES,
        multiline=True,
        nonempty=not allow_empty,
    )
    return {
        "format": SOURCE_EXCERPT_FORMAT,
        "v": RECORD_VERSION,
        "start_utf8": start_utf8,
        "end_utf8": end_utf8,
        "text": text,
        "sha256": hashlib.sha256(raw[start_utf8:end_utf8]).hexdigest(),
    }


def _validate_excerpt(
    value: object,
    document: AuthoringDocument,
    *,
    allow_empty: bool,
) -> dict[str, object]:
    if type(value) is not dict or set(value) != _SOURCE_FIELDS:
        raise AuthoringContractError("source excerpt has missing or additional fields")
    if value.get("format") != SOURCE_EXCERPT_FORMAT:
        raise AuthoringContractError("source excerpt identity is malformed")
    _require_version("source excerpt version", value.get("v"), RECORD_VERSION)
    expected = _excerpt_from_document(
        document,
        value.get("start_utf8"),  # type: ignore[arg-type]
        value.get("end_utf8"),  # type: ignore[arg-type]
        allow_empty=allow_empty,
    )
    if value != expected:
        raise AuthoringContractError("source excerpt text or hash is inconsistent")
    return value


def _validate_unit_record(value: object, document: AuthoringDocument) -> dict[str, object]:
    if type(value) is not dict or set(value) != _UNIT_FIELDS:
        raise AuthoringContractError("sentence unit has missing or additional fields")
    if value.get("format") != UNIT_FORMAT:
        raise AuthoringContractError("sentence unit identity is malformed")
    _require_version("sentence unit version", value.get("v"), RECORD_VERSION)
    _validate_binding(value.get("binding"), document)
    _safe_identifier("unit_id", value.get("unit_id"))
    if value.get("kind") not in UNIT_KINDS:
        raise AuthoringContractError("sentence unit kind is unsupported")
    _validate_excerpt(value.get("source"), document, allow_empty=False)
    return value


def build_sentence_unit(
    document: AuthoringDocument,
    *,
    unit_id: str,
    kind: UnitKind,
    start_utf8: int,
    end_utf8: int,
) -> SentenceUnit:
    authoring_schema()
    record = {
        "format": UNIT_FORMAT,
        "v": RECORD_VERSION,
        "binding": _document_binding(document),
        "unit_id": _safe_identifier("unit_id", unit_id),
        "kind": kind,
        "source": _excerpt_from_document(
            document, start_utf8, end_utf8, allow_empty=False
        ),
    }
    checked = _validate_unit_record(record, document)
    return _mint_carrier(SentenceUnit, canonical_json_bytes(checked))


def load_sentence_unit(raw: bytes, *, document: AuthoringDocument) -> SentenceUnit:
    authoring_schema()
    checked = _validate_unit_record(
        _decode_canonical_object(raw, "sentence unit"), document
    )
    return _mint_carrier(SentenceUnit, canonical_json_bytes(checked))


def _validate_provenance(value: object) -> dict[str, object]:
    if type(value) is not dict or set(value) != _PROVENANCE_FIELDS:
        raise AuthoringContractError("candidate provenance has missing or additional fields")
    if value.get("format") != PROVENANCE_FORMAT:
        raise AuthoringContractError("candidate provenance identity is malformed")
    _require_version("candidate provenance version", value.get("v"), RECORD_VERSION)
    kind = value.get("kind")
    if kind not in PROVENANCE_KINDS:
        raise AuthoringContractError("candidate provenance kind is unsupported")
    _safe_identifier("provenance id", value.get("id"))
    request = value.get("request_sha256")
    response = value.get("response_sha256")
    if kind == "model":
        _sha256("model request_sha256", request)
        _sha256("model response_sha256", response)
    elif request is not None or response is not None:
        raise AuthoringContractError(
            "only model provenance may carry request/response hashes"
        )
    return value


def _canonical_statement(source: object, profile_digest: str) -> str:
    statement = _safe_text(
        "formalization statement", source, max_bytes=MAX_STATEMENT_BYTES
    )
    try:
        return canonical_registered_profile_theorem(profile_digest, statement)
    except (TypeError, ValueError, RecursionError) as exc:
        raise AuthoringContractError(f"formalization is not native PA: {exc}") from None


def _formula_statement(formula: object, profile_digest: str) -> str:
    if not isinstance(formula, Formula):
        raise AuthoringContractError("original theorem must be a real kernel Formula")
    try:
        return canonical_registered_profile_formula(profile_digest, formula)
    except (TypeError, ValueError, RecursionError) as exc:
        raise AuthoringContractError(f"original theorem is outside native PA: {exc}") from None


def _statement_sha256(statement: str, profile_digest: str) -> str:
    payload = (
        b"peano-hydra-authoring-statement-v1\0"
        + profile_digest.encode("ascii")
        + b"\0"
        + statement.encode("utf-8")
    )
    return hashlib.sha256(payload).hexdigest()


def _definition_receipts_for_surface(source: str) -> list[dict[str, object]]:
    used = [
        definition
        for name, definition in ALL_DEFINITIONS_BY_NAME.items()
        if re.search(rf"(?<![A-Za-z0-9_']){re.escape(name)}\s*\(", source)
    ]
    if not used:
        raise AuthoringContractError(
            "defined-pa surface must use at least one registered definition"
        )
    rows = [
        {
            "id": (
                f"{PINNED_DEFINED_SYNTAX_REGISTRY_ID}:"
                f"v{PINNED_DEFINED_SYNTAX_VERSION}"
            ),
            "sha256": PINNED_DEFINED_SYNTAX_REGISTRY_SHA256,
        }
    ]
    for definition in sorted(used, key=lambda item: item.stable_id):
        payload = {
            "conceptual_dependencies": list(definition.conceptual_dependencies),
            "name": definition.name,
            "parameters": list(definition.parameters),
            "registry_sha256": PINNED_DEFINED_SYNTAX_REGISTRY_SHA256,
            "stable_id": definition.stable_id,
            "template_source": definition.template_source,
        }
        rows.append(
            {
                "id": definition.stable_id,
                "sha256": hashlib.sha256(canonical_json_bytes(payload)).hexdigest(),
            }
        )
    return rows


def _candidate_formula_components(
    statement: object,
    profile_digest: str,
    surface_kind: object,
) -> tuple[str, str, Formula, list[dict[str, object]]]:
    if surface_kind == "native-pa":
        readable = _canonical_statement(statement, profile_digest)
        formula = _parsed_canonical_statement(readable)
        return readable, readable, formula, []
    if surface_kind != "defined-pa":
        raise AuthoringContractError("candidate surface_kind is unsupported")
    readable = _safe_text(
        "defined-PA readable formula", statement, max_bytes=MAX_STATEMENT_BYTES
    )
    if readable != readable.strip() or readable.splitlines() != [readable]:
        raise AuthoringContractError(
            "defined-PA readable formula must be one exact line without outer whitespace"
        )
    try:
        formula, free_names = parse_defined_formula_with_names(readable)
    except (TypeError, ValueError, RecursionError) as exc:
        raise AuthoringContractError(f"invalid registered defined-PA formula: {exc}") from None
    if free_names:
        raise AuthoringContractError(
            "defined-PA theorem must be closed; quantify free variables explicitly"
        )
    expanded = _formula_statement(formula, profile_digest)
    receipts = _definition_receipts_for_surface(readable)
    return readable, expanded, formula, receipts


def _parsed_canonical_statement(statement: str) -> Formula:
    try:
        return parse_formula(statement)
    except (TypeError, ValueError, RecursionError) as exc:  # pragma: no cover - canonical
        raise AuthoringContractError(
            f"canonical native-PA statement failed structural parsing: {exc}"
        ) from None


def _primitive_term(term: object) -> str:
    if type(term) is Var:
        return f"var({term.index})"
    if type(term) is Zero:
        return "zero"
    if type(term) is Succ:
        return f"succ({_primitive_term(term.term)})"
    if type(term) is Add:
        return f"add({_primitive_term(term.left)},{_primitive_term(term.right)})"
    if type(term) is Mul:
        return f"mul({_primitive_term(term.left)},{_primitive_term(term.right)})"
    raise AuthoringContractError("native-PA term has an unknown primitive constructor")


def _primitive_formula(formula: object) -> str:
    if type(formula) is Eq:
        return f"eq({_primitive_term(formula.left)},{_primitive_term(formula.right)})"
    if type(formula) is Bot:
        return "bot"
    if type(formula) is Imp:
        return (
            f"imp({_primitive_formula(formula.antecedent)},"
            f"{_primitive_formula(formula.consequent)})"
        )
    if type(formula) is And:
        return f"and({_primitive_formula(formula.left)},{_primitive_formula(formula.right)})"
    if type(formula) is Or:
        return f"or({_primitive_formula(formula.left)},{_primitive_formula(formula.right)})"
    if type(formula) is Forall:
        return f"forall({_primitive_formula(formula.body)})"
    if type(formula) is Exists:
        return f"exists({_primitive_formula(formula.body)})"
    raise AuthoringContractError("native-PA formula has an unknown primitive constructor")


_BINDER_NAMES = ("x", "y", "z", "n", "m", "k", "i", "j", "u", "v", "w")


def _fresh_binder(active: tuple[str, ...]) -> str:
    used = set(active)
    for candidate in _BINDER_NAMES:
        if candidate not in used:
            return candidate
    index = 0
    while f"x{index}" in used:
        index += 1
    return f"x{index}"


def _binder_table(formula: Formula) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []

    def visit(node: Formula, path: str, active: tuple[str, ...]) -> None:
        if type(node) in (Forall, Exists):
            name = _fresh_binder(active)
            rows.append(
                {
                    "index": len(rows),
                    "path": path,
                    "quantifier": "forall" if type(node) is Forall else "exists",
                    "name": name,
                    "depth": len(active),
                }
            )
            visit(node.body, path + ".body", (name,) + active)
        elif type(node) in (Imp, And, Or):
            visit(node.left, path + ".left", active)
            visit(node.right, path + ".right", active)

    visit(formula, "$", ())
    return rows


def _assumption_table(formula: Formula) -> list[dict[str, object]]:
    active: tuple[str, ...] = ()
    path = "$"
    node = formula
    while type(node) in (Forall, Exists):
        active = (_fresh_binder(active),) + active
        node = node.body
        path += ".body"
    rows: list[dict[str, object]] = []
    while type(node) is Imp:
        primitive = _primitive_formula(node.antecedent)
        try:
            readable = pretty_formula(node.antecedent, list(active))
        except (TypeError, ValueError, RecursionError) as exc:
            raise AuthoringContractError(
                f"cannot render a candidate assumption: {exc}"
            ) from None
        rows.append(
            {
                "index": len(rows),
                "path": path + ".left",
                "readable_formula": readable,
                "primitive_formula": primitive,
                "sha256": hashlib.sha256(
                    b"peano-hydra-authoring-assumption-v1\0"
                    + primitive.encode("utf-8")
                ).hexdigest(),
            }
        )
        node = node.consequent
        path += ".right"
    return rows


def _derived_primitive_formula(formula: Formula) -> str:
    try:
        return _primitive_formula(formula)
    except RecursionError:
        raise AuthoringContractError(
            "native-PA structural derivation exceeds the recursion limit"
        ) from None


def _derived_formula_structure(
    formula: Formula,
) -> tuple[str, list[dict[str, object]], list[dict[str, object]]]:
    """Derive bounded presentation data with one stable contract error surface."""

    try:
        return (
            _derived_primitive_formula(formula),
            _binder_table(formula),
            _assumption_table(formula),
        )
    except RecursionError:
        raise AuthoringContractError(
            "native-PA structural derivation exceeds the recursion limit"
        ) from None


def _alternative_rows(
    values: tuple[str, ...], profile_digest: str
) -> list[dict[str, object]]:
    if type(values) is not tuple:
        raise AuthoringContractError("alternative_readings must be a tuple")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for index, source in enumerate(values):
        readable = _canonical_statement(source, profile_digest)
        primitive = _derived_primitive_formula(_parsed_canonical_statement(readable))
        digest = _statement_sha256(primitive, profile_digest)
        if digest in seen:
            raise AuthoringContractError("alternative_readings contains a duplicate")
        seen.add(digest)
        rows.append(
            {
                "index": index,
                "readable_formula": readable,
                "primitive_formula": primitive,
                "sha256": digest,
            }
        )
    return rows


def _content_receipts(
    label: str, values: tuple[tuple[str, str], ...]
) -> list[dict[str, object]]:
    if type(values) is not tuple:
        raise AuthoringContractError(f"{label} must be a tuple")
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for value in values:
        if type(value) is not tuple or len(value) != 2:
            raise AuthoringContractError(f"{label} entries must be (id, sha256) tuples")
        receipt_id = _safe_identifier(f"{label} id", value[0])
        if receipt_id in seen:
            raise AuthoringContractError(f"{label} contains a duplicate id")
        seen.add(receipt_id)
        rows.append({"id": receipt_id, "sha256": _sha256(label, value[1])})
    return rows


def _validate_content_receipts(label: str, value: object) -> list[dict[str, object]]:
    if type(value) is not list:
        raise AuthoringContractError(f"{label} must be an array")
    rebuilt: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != _CONTENT_RECEIPT_FIELDS:
            raise AuthoringContractError(f"{label} receipt is malformed")
        receipt_id = _safe_identifier(f"{label} id", item.get("id"))
        if receipt_id in seen:
            raise AuthoringContractError(f"{label} contains a duplicate id")
        seen.add(receipt_id)
        rebuilt.append(
            {"id": receipt_id, "sha256": _sha256(label, item.get("sha256"))}
        )
    if value != rebuilt:
        raise AuthoringContractError(f"{label} receipts are noncanonical")
    return value


def _validated_unit(unit: SentenceUnit) -> dict[str, object]:
    if type(unit) is not SentenceUnit:
        raise AuthoringContractError("operation needs a validated SentenceUnit")
    # The unit was checked against its document when built or loaded.  Its own
    # canonical bytes remain the exact revision binding for downstream data.
    value = unit.record
    if type(value) is not dict or set(value) != _UNIT_FIELDS:
        raise AuthoringContractError("sentence unit carrier is malformed")
    return value


def _validate_candidate_record(
    value: object, unit: SentenceUnit
) -> dict[str, object]:
    unit_record = _validated_unit(unit)
    if type(value) is not dict or set(value) != _CANDIDATE_FIELDS:
        raise AuthoringContractError("candidate has missing or additional fields")
    if value.get("format") != CANDIDATE_FORMAT:
        raise AuthoringContractError("candidate identity is malformed")
    _require_version("candidate version", value.get("v"), RECORD_VERSION)
    if value.get("binding") != unit_record["binding"]:
        raise AuthoringContractError("candidate is bound to another document revision")
    if value.get("unit_id") != unit_record["unit_id"] or value.get(
        "unit_sha256"
    ) != unit.sha256:
        raise AuthoringContractError("candidate is bound to another sentence unit")
    if value.get("source") != unit_record["source"]:
        raise AuthoringContractError("candidate does not retain its exact source span")
    _safe_identifier("candidate_id", value.get("candidate_id"))
    profile_digest = value["binding"]["semantic_profile_sha256"]  # type: ignore[index]
    readable, expanded, parsed, definition_receipts = _candidate_formula_components(
        value.get("readable_formula"),
        profile_digest,
        value.get("surface_kind"),
    )
    if readable != value.get("readable_formula"):
        raise AuthoringContractError("candidate readable formula is noncanonical")
    if value.get("expanded_formula") != expanded or value.get(
        "expanded_formula_sha256"
    ) != _statement_sha256(expanded, profile_digest):
        raise AuthoringContractError("candidate registered expansion is inconsistent")
    primitive, expected_binders, expected_assumptions = _derived_formula_structure(parsed)
    if value.get("primitive_formula") != primitive:
        raise AuthoringContractError("candidate primitive expansion is inconsistent")
    if value.get("primitive_formula_sha256") != _statement_sha256(
        primitive, profile_digest
    ):
        raise AuthoringContractError("candidate primitive formula hash is inconsistent")
    binders = value.get("binder_table")
    if type(binders) is not list or any(
        type(item) is not dict or set(item) != _BINDER_FIELDS for item in binders
    ):
        raise AuthoringContractError("candidate binder table is malformed")
    if binders != expected_binders:
        raise AuthoringContractError("candidate binder table is inconsistent")
    if value.get("free_variables") != []:
        raise AuthoringContractError("native-PA theorem candidates must have no free variables")
    assumptions = value.get("assumptions")
    if type(assumptions) is not list or any(
        type(item) is not dict or set(item) != _ASSUMPTION_FIELDS
        for item in assumptions
    ):
        raise AuthoringContractError("candidate assumption table is malformed")
    if assumptions != expected_assumptions:
        raise AuthoringContractError("candidate assumption table is inconsistent")
    alternatives = value.get("alternative_readings")
    if type(alternatives) is not list or any(
        type(item) is not dict or set(item) != _ALTERNATIVE_FIELDS
        for item in alternatives
    ):
        raise AuthoringContractError("candidate alternative readings are malformed")
    sources = tuple(item["readable_formula"] for item in alternatives)
    if alternatives != _alternative_rows(sources, profile_digest):  # type: ignore[arg-type]
        raise AuthoringContractError("candidate alternative readings are inconsistent")
    if readable in sources:
        raise AuthoringContractError("primary reading is duplicated as an alternative")
    checked_receipts = _validate_content_receipts(
        "definition_receipts", value.get("definition_receipts")
    )
    if checked_receipts != definition_receipts:
        raise AuthoringContractError("candidate definition receipts are inconsistent")
    _validate_provenance(value.get("provenance"))
    ambiguities = value.get("ambiguities")
    if type(ambiguities) is not list:
        raise AuthoringContractError("candidate ambiguities must be an array")
    checked_codes = tuple(_safe_code("ambiguity", item) for item in ambiguities)
    if tuple(sorted(checked_codes)) != checked_codes or len(set(checked_codes)) != len(
        checked_codes
    ):
        raise AuthoringContractError("candidate ambiguities must be sorted and unique")
    return value


def build_formalization_candidate(
    unit: SentenceUnit,
    *,
    candidate_id: str,
    statement: str,
    provenance_kind: ProvenanceKind,
    provenance_id: str,
    request_sha256: str | None = None,
    response_sha256: str | None = None,
    ambiguities: tuple[str, ...] = (),
    alternative_readings: tuple[str, ...] = (),
    surface_kind: SurfaceKind = "native-pa",
) -> FormalizationCandidate:
    """Parse one untrusted reading and retain only canonical native PA."""

    authoring_schema()
    unit_record = _validated_unit(unit)
    binding = unit_record["binding"]
    profile_digest = binding["semantic_profile_sha256"]  # type: ignore[index]
    readable, expanded, parsed, definition_receipts = _candidate_formula_components(
        statement, profile_digest, surface_kind
    )
    primitive, binders, assumptions = _derived_formula_structure(parsed)
    alternatives = _alternative_rows(alternative_readings, profile_digest)
    if any(item["readable_formula"] == readable for item in alternatives):
        raise AuthoringContractError("primary reading is duplicated as an alternative")
    ambiguity_values = tuple(_safe_code("ambiguity", item) for item in ambiguities)
    if tuple(sorted(ambiguity_values)) != ambiguity_values or len(
        set(ambiguity_values)
    ) != len(ambiguity_values):
        raise AuthoringContractError("candidate ambiguities must be sorted and unique")
    provenance = {
        "format": PROVENANCE_FORMAT,
        "v": RECORD_VERSION,
        "kind": provenance_kind,
        "id": _safe_identifier("provenance id", provenance_id),
        "request_sha256": request_sha256,
        "response_sha256": response_sha256,
    }
    _validate_provenance(provenance)
    record = {
        "format": CANDIDATE_FORMAT,
        "v": RECORD_VERSION,
        "binding": binding,
        "unit_id": unit_record["unit_id"],
        "unit_sha256": unit.sha256,
        "candidate_id": _safe_identifier("candidate_id", candidate_id),
        "source": unit_record["source"],
        "surface_kind": surface_kind,
        "readable_formula": readable,
        "expanded_formula": expanded,
        "expanded_formula_sha256": _statement_sha256(expanded, profile_digest),
        "primitive_formula": primitive,
        "primitive_formula_sha256": _statement_sha256(primitive, profile_digest),
        "binder_table": binders,
        "free_variables": [],
        "assumptions": assumptions,
        "alternative_readings": alternatives,
        "definition_receipts": definition_receipts,
        "provenance": provenance,
        "ambiguities": list(ambiguity_values),
    }
    checked = _validate_candidate_record(record, unit)
    return _mint_carrier(FormalizationCandidate, canonical_json_bytes(checked))


def load_formalization_candidate(
    raw: bytes, *, unit: SentenceUnit
) -> FormalizationCandidate:
    authoring_schema()
    checked = _validate_candidate_record(
        _decode_canonical_object(raw, "formalization candidate"), unit
    )
    return _mint_carrier(FormalizationCandidate, canonical_json_bytes(checked))


def _diagnostic_excerpt(
    unit: SentenceUnit, start_utf8: int, end_utf8: int
) -> dict[str, object]:
    unit_record = _validated_unit(unit)
    source = unit_record["source"]
    unit_start = source["start_utf8"]  # type: ignore[index]
    unit_end = source["end_utf8"]  # type: ignore[index]
    if (
        type(start_utf8) is not int
        or type(end_utf8) is not int
        or start_utf8 < unit_start
        or end_utf8 < start_utf8
        or end_utf8 > unit_end
    ):
        raise AuthoringContractError("diagnostic span is outside its sentence unit")
    unit_bytes = source["text"].encode("utf-8")  # type: ignore[index,union-attr]
    relative_start = start_utf8 - unit_start
    relative_end = end_utf8 - unit_start
    try:
        text = unit_bytes[relative_start:relative_end].decode("utf-8")
    except UnicodeDecodeError:
        raise AuthoringContractError("diagnostic span splits a UTF-8 code point") from None
    _safe_text(
        "diagnostic excerpt",
        text,
        max_bytes=MAX_EXCERPT_BYTES,
        multiline=True,
        nonempty=False,
    )
    return {
        "format": SOURCE_EXCERPT_FORMAT,
        "v": RECORD_VERSION,
        "start_utf8": start_utf8,
        "end_utf8": end_utf8,
        "text": text,
        "sha256": hashlib.sha256(unit_bytes[relative_start:relative_end]).hexdigest(),
    }


def _validate_diagnostic_record(
    value: object, unit: SentenceUnit
) -> dict[str, object]:
    unit_record = _validated_unit(unit)
    if type(value) is not dict or set(value) != _DIAGNOSTIC_FIELDS:
        raise AuthoringContractError("diagnostic has missing or additional fields")
    if value.get("format") != DIAGNOSTIC_FORMAT:
        raise AuthoringContractError("diagnostic identity is malformed")
    _require_version("diagnostic version", value.get("v"), RECORD_VERSION)
    if value.get("binding") != unit_record["binding"]:
        raise AuthoringContractError("diagnostic is bound to another document revision")
    if value.get("unit_id") != unit_record["unit_id"] or value.get(
        "unit_sha256"
    ) != unit.sha256:
        raise AuthoringContractError("diagnostic is bound to another sentence unit")
    _safe_identifier("diagnostic_id", value.get("diagnostic_id"))
    _safe_code("diagnostic code", value.get("code"))
    if value.get("severity") not in DIAGNOSTIC_SEVERITIES:
        raise AuthoringContractError("diagnostic severity is unsupported")
    authority = value.get("authority")
    if authority not in DIAGNOSTIC_AUTHORITIES:
        raise AuthoringContractError("diagnostic authority is unsupported")
    _safe_text(
        "diagnostic message", value.get("message"), max_bytes=MAX_MESSAGE_BYTES
    )
    source = value.get("source")
    if type(source) is not dict or set(source) != _SOURCE_FIELDS:
        raise AuthoringContractError("diagnostic source excerpt is malformed")
    expected_source = _diagnostic_excerpt(
        unit,
        source.get("start_utf8"),  # type: ignore[arg-type]
        source.get("end_utf8"),  # type: ignore[arg-type]
    )
    if value.get("source") != expected_source:
        raise AuthoringContractError("diagnostic source excerpt is inconsistent")
    evidence = value.get("evidence_sha256")
    if evidence is not None:
        _sha256("diagnostic evidence_sha256", evidence)
    if authority == "kernel" and evidence is None:
        raise AuthoringContractError("kernel diagnostics require an evidence hash")
    suggested = value.get("suggested_statement")
    if suggested is not None:
        profile_digest = value["binding"]["semantic_profile_sha256"]  # type: ignore[index]
        if _canonical_statement(suggested, profile_digest) != suggested:
            raise AuthoringContractError(
                "diagnostic suggestion is not canonical native PA"
            )
    return value


def build_diagnostic(
    unit: SentenceUnit,
    *,
    diagnostic_id: str,
    code: str,
    severity: DiagnosticSeverity,
    authority: DiagnosticAuthority,
    message: str,
    start_utf8: int,
    end_utf8: int,
    evidence_sha256: str | None = None,
    suggested_statement: str | None = None,
) -> AuthoringDiagnostic:
    authoring_schema()
    if authority not in UNTRUSTED_DIAGNOSTIC_AUTHORITIES:
        raise AuthoringContractError(
            f"{authority} diagnostics require a dedicated authenticated builder"
        )
    unit_record = _validated_unit(unit)
    profile_digest = unit_record["binding"]["semantic_profile_sha256"]  # type: ignore[index]
    suggestion = (
        None
        if suggested_statement is None
        else _canonical_statement(suggested_statement, profile_digest)
    )
    record = {
        "format": DIAGNOSTIC_FORMAT,
        "v": RECORD_VERSION,
        "binding": unit_record["binding"],
        "unit_id": unit_record["unit_id"],
        "unit_sha256": unit.sha256,
        "diagnostic_id": _safe_identifier("diagnostic_id", diagnostic_id),
        "code": _safe_code("diagnostic code", code),
        "severity": severity,
        "authority": authority,
        "message": _safe_text(
            "diagnostic message", message, max_bytes=MAX_MESSAGE_BYTES
        ),
        "source": _diagnostic_excerpt(unit, start_utf8, end_utf8),
        "evidence_sha256": evidence_sha256,
        "suggested_statement": suggestion,
    }
    checked = _validate_diagnostic_record(record, unit)
    return _mint_carrier(AuthoringDiagnostic, canonical_json_bytes(checked))


def _kernel_diagnostic_evidence(
    unit: SentenceUnit,
    diagnostic_id: str,
    suggested_statement: str,
    original_formula: Formula,
    proof: Proof,
    *,
    start_utf8: int,
    end_utf8: int,
) -> tuple[dict[str, object], str]:
    unit_record = _validated_unit(unit)
    profile_digest = unit_record["binding"]["semantic_profile_sha256"]  # type: ignore[index]
    canonical = _canonical_statement(suggested_statement, profile_digest)
    if _formula_statement(original_formula, profile_digest) != canonical:
        raise AuthoringContractError(
            "kernel diagnostic formula differs from its suggested statement"
        )
    if not isinstance(proof, Proof):
        raise AuthoringContractError("kernel diagnostic needs a real kernel Proof")
    try:
        evidence = build_checked_proved_evidence(
            original_formula,
            proof,
            run_id=f"authoring-diagnostic:{diagnostic_id}",
            semantic_profile_sha256=profile_digest,
            degraded=False,
            eligible_for_comparison=False,
        )
    except HydraResultSchemaError as exc:
        raise AuthoringContractError(
            f"kernel diagnostic replay failed: {exc}"
        ) from None
    fields: dict[str, object] = {
        "diagnostic_id": _safe_identifier("diagnostic_id", diagnostic_id),
        "code": "kernel-verified-statement",
        "severity": "info",
        "message": (
            "Kernel replay verified only the suggested PA statement attached to "
            "this diagnostic; it does not verify that the source prose has this meaning."
        ),
        "source": _diagnostic_excerpt(unit, start_utf8, end_utf8),
        "suggested_statement": canonical,
    }
    evidence_record = {
        "format": KERNEL_DIAGNOSTIC_EVIDENCE_FORMAT,
        "v": RECORD_VERSION,
        "unit_sha256": unit.sha256,
        **fields,
        "checked_result": evidence.result,
    }
    evidence_sha256 = hashlib.sha256(
        b"peano-hydra-kernel-diagnostic-evidence-v1\0"
        + canonical_json_bytes(evidence_record)
    ).hexdigest()
    return fields, evidence_sha256


def build_kernel_diagnostic(
    unit: SentenceUnit,
    original_formula: Formula,
    proof: Proof,
    *,
    diagnostic_id: str,
    start_utf8: int,
    end_utf8: int,
    suggested_statement: str,
) -> AuthoringDiagnostic:
    """Report one proved suggestion with fixed, evidence-bound semantics."""

    authoring_schema()
    fields, evidence_sha256 = _kernel_diagnostic_evidence(
        unit,
        diagnostic_id,
        suggested_statement,
        original_formula,
        proof,
        start_utf8=start_utf8,
        end_utf8=end_utf8,
    )
    unit_record = _validated_unit(unit)
    record = {
        "format": DIAGNOSTIC_FORMAT,
        "v": RECORD_VERSION,
        "binding": unit_record["binding"],
        "unit_id": unit_record["unit_id"],
        "unit_sha256": unit.sha256,
        "authority": "kernel",
        "evidence_sha256": evidence_sha256,
        **fields,
    }
    checked = _validate_diagnostic_record(record, unit)
    return _mint_carrier(AuthoringDiagnostic, canonical_json_bytes(checked))


def load_diagnostic(
    raw: bytes,
    *,
    unit: SentenceUnit,
    original_formula: Formula | None = None,
    proof: Proof | None = None,
) -> AuthoringDiagnostic:
    authoring_schema()
    checked = _validate_diagnostic_record(
        _decode_canonical_object(raw, "authoring diagnostic"), unit
    )
    if checked["authority"] == "human-reviewer":
        raise AuthoringContractError(
            "human-reviewer diagnostics require host-authenticated review evidence"
        )
    if checked["authority"] == "kernel":
        if original_formula is None or proof is None:
            raise AuthoringContractError(
                "kernel diagnostic loading requires the original Formula and Proof"
            )
        source = checked["source"]
        fixed_fields, expected = _kernel_diagnostic_evidence(
            unit,
            checked["diagnostic_id"],  # type: ignore[arg-type]
            checked["suggested_statement"],  # type: ignore[arg-type]
            original_formula,
            proof,
            start_utf8=source["start_utf8"],  # type: ignore[index]
            end_utf8=source["end_utf8"],  # type: ignore[index]
        )
        if checked["evidence_sha256"] != expected or any(
            checked[field_name] != expected_value
            for field_name, expected_value in fixed_fields.items()
        ):
            raise AuthoringContractError(
                "serialized kernel diagnostic differs from fresh kernel evidence"
            )
    else:
        if checked["authority"] not in UNTRUSTED_DIAGNOSTIC_AUTHORITIES:
            raise AuthoringContractError(
                f"{checked['authority']} diagnostics require a dedicated "
                "authenticated builder"
            )
        if original_formula is not None or proof is not None:
            raise AuthoringContractError(
                "non-kernel diagnostic cannot carry proof authority"
            )
    return _mint_carrier(AuthoringDiagnostic, canonical_json_bytes(checked))


def _validated_candidate(candidate: FormalizationCandidate) -> dict[str, object]:
    if type(candidate) is not FormalizationCandidate:
        raise AuthoringContractError(
            "operation needs a validated FormalizationCandidate"
        )
    value = candidate.record
    if type(value) is not dict or set(value) != _CANDIDATE_FIELDS:
        raise AuthoringContractError("formalization candidate carrier is malformed")
    return value


def _lineage_record(
    candidate: FormalizationCandidate,
    lineage_id: str,
    parent_attempt: ProofAttempt | None,
) -> dict[str, object]:
    if parent_attempt is not None:
        if type(parent_attempt) is not ProofAttempt:
            raise AuthoringContractError("lineage parent must be a validated ProofAttempt")
        parent = _validate_attempt_record(
            parent_attempt.record, candidate, _allow_unresolved_parent=True
        )
        if parent["lineage"]["lineage_id"] != lineage_id:  # type: ignore[index]
            raise AuthoringContractError("parent proof attempt belongs to another lineage")
    return {
        "lineage_id": _safe_identifier("lineage_id", lineage_id),
        "candidate_sha256": candidate.sha256,
        "parent_attempt_sha256": (
            None if parent_attempt is None else parent_attempt.sha256
        ),
    }


def _validate_lineage(
    value: object,
    candidate: FormalizationCandidate,
    parent_attempt: ProofAttempt | None,
    *,
    allow_unresolved_parent: bool = False,
) -> dict[str, object]:
    if type(value) is not dict or set(value) != _LINEAGE_FIELDS:
        raise AuthoringContractError("authoring lineage is malformed")
    lineage_id = _safe_identifier("lineage_id", value.get("lineage_id"))
    if value.get("candidate_sha256") != candidate.sha256:
        raise AuthoringContractError("lineage is bound to another candidate")
    parent_hash = value.get("parent_attempt_sha256")
    if parent_attempt is None:
        if parent_hash is not None:
            if not allow_unresolved_parent:
                raise AuthoringContractError("lineage parent proof attempt was not supplied")
            _sha256("lineage parent_attempt_sha256", parent_hash)
    else:
        if type(parent_attempt) is not ProofAttempt:
            raise AuthoringContractError("lineage parent must be a validated ProofAttempt")
        parent = _validate_attempt_record(
            parent_attempt.record, candidate, _allow_unresolved_parent=True
        )
        if (
            parent_hash != parent_attempt.sha256
            or parent["lineage"]["lineage_id"] != lineage_id  # type: ignore[index]
        ):
            raise AuthoringContractError("lineage parent proof attempt is stale")
    return value


def _validate_attempt_record(
    value: object,
    candidate: FormalizationCandidate,
    parent_attempt: ProofAttempt | None = None,
    *,
    _allow_unresolved_parent: bool = False,
) -> dict[str, object]:
    candidate_record = _validated_candidate(candidate)
    if type(value) is not dict or set(value) != _ATTEMPT_FIELDS:
        raise AuthoringContractError("proof attempt has missing or additional fields")
    if value.get("format") != PROOF_ATTEMPT_FORMAT:
        raise AuthoringContractError("proof attempt identity is malformed")
    _require_version("proof attempt version", value.get("v"), RECORD_VERSION)
    if value.get("binding") != candidate_record["binding"]:
        raise AuthoringContractError("proof attempt is bound to another document revision")
    if value.get("source") != candidate_record["source"]:
        raise AuthoringContractError("proof attempt does not retain its exact source span")
    if value.get("candidate_sha256") != candidate.sha256:
        raise AuthoringContractError("proof attempt is bound to another candidate")
    _safe_identifier("attempt_id", value.get("attempt_id"))
    _validate_lineage(
        value.get("lineage"),
        candidate,
        parent_attempt,
        allow_unresolved_parent=_allow_unresolved_parent,
    )
    if value.get("engine") not in ATTEMPT_ENGINES:
        raise AuthoringContractError("proof attempt engine is unsupported")
    if value.get("outcome") not in ATTEMPT_OUTCOMES:
        raise AuthoringContractError("proof attempt outcome is unsupported")
    script = _safe_text(
        "proof attempt readable script",
        value.get("readable_script"),
        max_bytes=MAX_SCRIPT_BYTES,
        multiline=True,
        nonempty=False,
    )
    if value.get("readable_script_sha256") != hashlib.sha256(
        script.encode("utf-8")
    ).hexdigest():
        raise AuthoringContractError("proof attempt script hash is inconsistent")
    _validate_provenance(value.get("provenance"))
    _validate_content_receipts(
        "transcript_receipts", value.get("transcript_receipts")
    )
    _validate_content_receipts(
        "diagnostic_receipts", value.get("diagnostic_receipts")
    )
    return value


def build_proof_attempt(
    candidate: FormalizationCandidate,
    *,
    attempt_id: str,
    lineage_id: str,
    engine: AttemptEngine,
    outcome: AttemptOutcome,
    readable_script: str,
    provenance_kind: ProvenanceKind,
    provenance_id: str,
    parent_attempt: ProofAttempt | None = None,
    request_sha256: str | None = None,
    response_sha256: str | None = None,
    transcript_receipts: tuple[tuple[str, str], ...] = (),
    diagnostic_receipts: tuple[tuple[str, str], ...] = (),
) -> ProofAttempt:
    """Retain an untrusted proof/search attempt without a checked authority bit."""

    authoring_schema()
    candidate_record = _validated_candidate(candidate)
    script = _safe_text(
        "proof attempt readable script",
        readable_script,
        max_bytes=MAX_SCRIPT_BYTES,
        multiline=True,
        nonempty=False,
    )
    provenance = {
        "format": PROVENANCE_FORMAT,
        "v": RECORD_VERSION,
        "kind": provenance_kind,
        "id": _safe_identifier("provenance id", provenance_id),
        "request_sha256": request_sha256,
        "response_sha256": response_sha256,
    }
    _validate_provenance(provenance)
    record = {
        "format": PROOF_ATTEMPT_FORMAT,
        "v": RECORD_VERSION,
        "binding": candidate_record["binding"],
        "source": candidate_record["source"],
        "candidate_sha256": candidate.sha256,
        "attempt_id": _safe_identifier("attempt_id", attempt_id),
        "lineage": _lineage_record(candidate, lineage_id, parent_attempt),
        "engine": engine,
        "outcome": outcome,
        "readable_script": script,
        "readable_script_sha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
        "provenance": provenance,
        "transcript_receipts": _content_receipts(
            "transcript_receipts", transcript_receipts
        ),
        "diagnostic_receipts": _content_receipts(
            "diagnostic_receipts", diagnostic_receipts
        ),
    }
    checked = _validate_attempt_record(record, candidate, parent_attempt)
    return _mint_carrier(ProofAttempt, canonical_json_bytes(checked))


def load_proof_attempt(
    raw: bytes,
    *,
    candidate: FormalizationCandidate,
    parent_attempt: ProofAttempt | None = None,
) -> ProofAttempt:
    authoring_schema()
    checked = _validate_attempt_record(
        _decode_canonical_object(raw, "proof attempt"), candidate, parent_attempt
    )
    return _mint_carrier(ProofAttempt, canonical_json_bytes(checked))


def _direct_dependencies(name: str, values: tuple[str, ...]) -> list[str]:
    if type(values) is not tuple:
        raise AuthoringContractError("direct_dependencies must be a tuple")
    checked = tuple(_safe_theorem_name("direct dependency", item) for item in values)
    if len(set(checked)) != len(checked):
        raise AuthoringContractError("direct_dependencies contains a duplicate")
    if name in checked:
        raise AuthoringContractError("a theorem cannot depend directly on itself")
    return list(checked)


def _publication_dependencies(
    readable: list[str], optimized: list[str]
) -> list[str]:
    return list(dict.fromkeys((*readable, *optimized)))


def _documentation_receipts(
    values: tuple[tuple[str, str], ...]
) -> list[dict[str, object]]:
    if type(values) is not tuple:
        raise AuthoringContractError("documentation_receipts must be a tuple")
    order = {"book": 0, "vault": 1, "explorer": 2}
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in values:
        if type(item) is not tuple or len(item) != 2 or item[0] not in order:
            raise AuthoringContractError(
                "documentation receipt must be (book|vault|explorer, sha256)"
            )
        if item[0] in seen:
            raise AuthoringContractError("documentation_receipts contains a duplicate target")
        seen.add(item[0])
        rows.append({"target": item[0], "sha256": _sha256("documentation", item[1])})
    rows.sort(key=lambda row: order[row["target"]])  # type: ignore[index]
    return rows


def _validate_documentation_receipts(value: object) -> list[dict[str, object]]:
    if type(value) is not list:
        raise AuthoringContractError("documentation_receipts must be an array")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if type(item) is not dict or set(item) != _DOC_RECEIPT_FIELDS:
            raise AuthoringContractError("documentation receipt is malformed")
        target = item.get("target")
        digest = item.get("sha256")
        if type(target) is not str or type(digest) is not str:
            raise AuthoringContractError("documentation receipt values are malformed")
        pairs.append((target, digest))
    rebuilt = _documentation_receipts(tuple(pairs))
    if value != rebuilt:
        raise AuthoringContractError("documentation receipts are noncanonical")
    return value


def _proposal_common(
    candidate: FormalizationCandidate,
    *,
    proposal_id: str,
    name: str,
    readable_dependencies: tuple[str, ...],
    optimized_dependencies: tuple[str, ...],
    lineage_id: str,
    proof_attempt: ProofAttempt | None,
    readable_source_proof: str,
    mutation_result_receipts: tuple[tuple[str, str], ...],
    transcript_receipts: tuple[tuple[str, str], ...],
    documentation_receipts: tuple[tuple[str, str], ...],
    explanation: str,
    proof_status: str,
) -> dict[str, object]:
    candidate_record = _validated_candidate(candidate)
    theorem_name = _safe_theorem_name("proposal theorem name", name)
    readable_deps = _direct_dependencies(theorem_name, readable_dependencies)
    optimized_deps = _direct_dependencies(theorem_name, optimized_dependencies)
    source_proof = _safe_text(
        "proposal readable source proof",
        readable_source_proof,
        max_bytes=MAX_SCRIPT_BYTES,
        multiline=True,
        nonempty=False,
    )
    return {
        "format": PROPOSAL_FORMAT,
        "v": RECORD_VERSION,
        "binding": candidate_record["binding"],
        "source": candidate_record["source"],
        "proposal_id": _safe_identifier("proposal_id", proposal_id),
        "name": theorem_name,
        "candidate_sha256": candidate.sha256,
        "lineage": _lineage_record(candidate, lineage_id, proof_attempt),
        "primitive_formula": candidate_record["primitive_formula"],
        "primitive_formula_sha256": candidate_record["primitive_formula_sha256"],
        "readable_dependencies": readable_deps,
        "optimized_dependencies": optimized_deps,
        "publication_dependencies": _publication_dependencies(
            readable_deps, optimized_deps
        ),
        "readable_source_proof": source_proof,
        "readable_source_proof_sha256": hashlib.sha256(
            source_proof.encode("utf-8")
        ).hexdigest(),
        "mutation_result_receipts": _content_receipts(
            "mutation_result_receipts", mutation_result_receipts
        ),
        "transcript_receipts": _content_receipts(
            "transcript_receipts", transcript_receipts
        ),
        "documentation_receipts": _documentation_receipts(documentation_receipts),
        "explanation": _safe_text(
            "proposal explanation",
            explanation,
            max_bytes=MAX_SUMMARY_BYTES,
            multiline=True,
        ),
        "human_acceptance": None,
        "human_review": None,
        "proof_status": proof_status,
    }


def _cut_nodes(proof: Proof) -> int:
    total = 0
    pending = [proof]
    while pending:
        node = pending.pop()
        if type(node) is Cut:
            total += 1
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
    return total


def _proof_metrics_record(
    result: dict[str, object],
    certificate_artifact: bytes,
    proof: Proof,
    readable_source_proof: str,
) -> dict[str, object]:
    nodes, depth, distinct, _edges, _reused = proof_resource_metrics(proof)
    if result.get("certificate_nodes") != nodes or result.get("certificate_depth") != depth:
        raise AuthoringContractError("fresh result and submitted proof metrics disagree")
    return {
        "claim": "submitted",
        "certificate_sha256": result["certificate_sha256"],
        "certificate_nodes": nodes,
        "distinct_proof_objects": distinct,
        "cut_nodes": _cut_nodes(proof),
        "certificate_bytes": len(certificate_artifact),
        "max_depth": depth,
        "replay_observation": "accepted",
        "readable_script_utf8_bytes": len(readable_source_proof.encode("utf-8")),
    }


def _validate_proposal_common(
    value: dict[str, object],
    candidate: FormalizationCandidate,
    proof_attempt: ProofAttempt | None,
) -> None:
    candidate_record = _validated_candidate(candidate)
    if value.get("format") != PROPOSAL_FORMAT:
        raise AuthoringContractError("theorem proposal identity is malformed")
    _require_version("theorem proposal version", value.get("v"), RECORD_VERSION)
    if value.get("binding") != candidate_record["binding"]:
        raise AuthoringContractError("proposal is bound to another document revision")
    if value.get("candidate_sha256") != candidate.sha256:
        raise AuthoringContractError("proposal is bound to another candidate")
    if (
        value.get("source") != candidate_record["source"]
        or value.get("primitive_formula") != candidate_record["primitive_formula"]
        or value.get("primitive_formula_sha256")
        != candidate_record["primitive_formula_sha256"]
    ):
        raise AuthoringContractError("proposal source or formula differs from its candidate")
    _safe_identifier("proposal_id", value.get("proposal_id"))
    _validate_lineage(value.get("lineage"), candidate, proof_attempt)
    name = _safe_theorem_name("proposal theorem name", value.get("name"))
    readable_dependencies = value.get("readable_dependencies")
    optimized_dependencies = value.get("optimized_dependencies")
    publication_dependencies = value.get("publication_dependencies")
    if type(readable_dependencies) is not list or type(optimized_dependencies) is not list:
        raise AuthoringContractError("proposal dependency vectors must be arrays")
    readable_deps = _direct_dependencies(name, tuple(readable_dependencies))
    optimized_deps = _direct_dependencies(name, tuple(optimized_dependencies))
    if publication_dependencies != _publication_dependencies(
        readable_deps, optimized_deps
    ):
        raise AuthoringContractError(
            "publication dependencies are not the deterministic dependency union"
        )
    source_proof = _safe_text(
        "proposal readable source proof",
        value.get("readable_source_proof"),
        max_bytes=MAX_SCRIPT_BYTES,
        multiline=True,
        nonempty=False,
    )
    if value.get("readable_source_proof_sha256") != hashlib.sha256(
        source_proof.encode("utf-8")
    ).hexdigest():
        raise AuthoringContractError("proposal readable proof hash is inconsistent")
    _validate_content_receipts(
        "mutation_result_receipts", value.get("mutation_result_receipts")
    )
    _validate_content_receipts(
        "transcript_receipts", value.get("transcript_receipts")
    )
    _validate_documentation_receipts(value.get("documentation_receipts"))
    _safe_text(
        "proposal explanation",
        value.get("explanation"),
        max_bytes=MAX_SUMMARY_BYTES,
        multiline=True,
    )
    if value.get("human_acceptance") is not None or value.get("human_review") is not None:
        raise AuthoringContractError(
            "human acceptance/review require separate host-authenticated events"
        )


def _validate_proposal_record(
    value: object,
    candidate: FormalizationCandidate,
    proof_attempt: ProofAttempt | None = None,
) -> dict[str, object]:
    if type(value) is not dict:
        raise AuthoringContractError("theorem proposal must be one object")
    status = value.get("proof_status")
    expected = (
        _PROPOSAL_COMMON_FIELDS
        if status == "draft"
        else _PROPOSAL_CHECKED_FIELDS
    )
    if status not in {"draft", "checked"} or set(value) != expected:
        raise AuthoringContractError(
            "theorem proposal has missing or additional fields"
        )
    _validate_proposal_common(value, candidate, proof_attempt)
    if status == "checked":
        result = value.get("checked_result")
        if type(result) is not dict or result.get("kind") != "proved":
            raise AuthoringContractError("checked proposal result is malformed")
        candidate_record = candidate.record
        if (
            result.get("logic") != candidate_record["binding"]["logic"]  # type: ignore[index]
            or result.get("semantic_profile_sha256")
            != candidate_record["binding"]["semantic_profile_sha256"]  # type: ignore[index]
            or result.get("original_theorem") != candidate_record["expanded_formula"]
            or result.get("kernel_accepted") is not True
            or result.get("certificate_representation")
            != CERTIFICATE_REPRESENTATION
        ):
            raise AuthoringContractError("checked proposal result bindings are malformed")
        metrics = value.get("proof_metrics")
        if (
            type(metrics) is not dict
            or set(metrics) != _PROOF_METRICS_FIELDS
        ):
            raise AuthoringContractError("checked proposal proof metrics are malformed")
        if (
            metrics.get("claim") != "submitted"
            or metrics.get("certificate_sha256") != result.get("certificate_sha256")
            or metrics.get("certificate_nodes") != result.get("certificate_nodes")
            or metrics.get("max_depth") != result.get("certificate_depth")
            or metrics.get("replay_observation") != "accepted"
        ):
            raise AuthoringContractError("checked proposal proof metrics are inconsistent")
        for field_name in (
            "certificate_nodes",
            "distinct_proof_objects",
            "certificate_bytes",
            "max_depth",
        ):
            if type(metrics.get(field_name)) is not int or metrics[field_name] < 1:
                raise AuthoringContractError(f"proof metric {field_name} must be positive")
        for field_name in ("cut_nodes", "readable_script_utf8_bytes"):
            if type(metrics.get(field_name)) is not int or metrics[field_name] < 0:
                raise AuthoringContractError(
                    f"proof metric {field_name} must be non-negative"
                )
        if metrics.get("readable_script_utf8_bytes") != len(
            value["readable_source_proof"].encode("utf-8")  # type: ignore[union-attr]
        ):
            raise AuthoringContractError("readable proof length metric is inconsistent")
    return value


def build_draft_theorem_proposal(
    candidate: FormalizationCandidate,
    *,
    proposal_id: str,
    name: str,
    readable_dependencies: tuple[str, ...],
    optimized_dependencies: tuple[str, ...],
    readable_source_proof: str,
    explanation: str,
    lineage_id: str | None = None,
    proof_attempt: ProofAttempt | None = None,
    mutation_result_receipts: tuple[tuple[str, str], ...] = (),
    transcript_receipts: tuple[tuple[str, str], ...] = (),
    documentation_receipts: tuple[tuple[str, str], ...] = (),
) -> TheoremProposal:
    """Build an explicitly unproved proposal with no certificate fields."""

    authoring_schema()
    lineage_key = (
        _validated_candidate(candidate)["candidate_id"]
        if lineage_id is None
        else lineage_id
    )
    record = _proposal_common(
        candidate,
        proposal_id=proposal_id,
        name=name,
        readable_dependencies=readable_dependencies,
        optimized_dependencies=optimized_dependencies,
        lineage_id=lineage_key,  # type: ignore[arg-type]
        proof_attempt=proof_attempt,
        readable_source_proof=readable_source_proof,
        mutation_result_receipts=mutation_result_receipts,
        transcript_receipts=transcript_receipts,
        documentation_receipts=documentation_receipts,
        explanation=explanation,
        proof_status="draft",
    )
    checked = _validate_proposal_record(record, candidate, proof_attempt)
    return _mint_carrier(TheoremProposal, canonical_json_bytes(checked))


def _fresh_checked_evidence(
    candidate: FormalizationCandidate,
    proposal_id: str,
    original_formula: Formula,
    proof: Proof,
):
    candidate_record = _validated_candidate(candidate)
    profile_digest = candidate_record["binding"]["semantic_profile_sha256"]  # type: ignore[index]
    theorem = _formula_statement(original_formula, profile_digest)
    if theorem != candidate_record["expanded_formula"]:
        raise AuthoringContractError(
            "checked proposal original formula differs from its formalization candidate"
        )
    if not isinstance(proof, Proof):
        raise AuthoringContractError("checked proposal needs a real kernel Proof")
    try:
        return build_checked_proved_evidence(
            original_formula,
            proof,
            run_id=f"authoring:{proposal_id}",
            semantic_profile_sha256=profile_digest,
            degraded=False,
            eligible_for_comparison=False,
        )
    except HydraResultSchemaError as exc:
        raise AuthoringContractError(
            f"fresh original-goal kernel check failed: {exc}"
        ) from None


def build_checked_theorem_proposal(
    candidate: FormalizationCandidate,
    original_formula: Formula,
    proof: Proof,
    *,
    proposal_id: str,
    name: str,
    readable_dependencies: tuple[str, ...],
    optimized_dependencies: tuple[str, ...],
    readable_source_proof: str,
    explanation: str,
    lineage_id: str | None = None,
    proof_attempt: ProofAttempt | None = None,
    mutation_result_receipts: tuple[tuple[str, str], ...] = (),
    transcript_receipts: tuple[tuple[str, str], ...] = (),
    documentation_receipts: tuple[tuple[str, str], ...] = (),
) -> TheoremProposal:
    """Build checked status only after a fresh original-goal kernel replay."""

    authoring_schema()
    proposal_key = _safe_identifier("proposal_id", proposal_id)
    evidence = _fresh_checked_evidence(
        candidate, proposal_key, original_formula, proof
    )
    lineage_key = (
        _validated_candidate(candidate)["candidate_id"]
        if lineage_id is None
        else lineage_id
    )
    record = _proposal_common(
        candidate,
        proposal_id=proposal_key,
        name=name,
        readable_dependencies=readable_dependencies,
        optimized_dependencies=optimized_dependencies,
        lineage_id=lineage_key,  # type: ignore[arg-type]
        proof_attempt=proof_attempt,
        readable_source_proof=_safe_text(
            "proposal readable source proof",
            readable_source_proof,
            max_bytes=MAX_SCRIPT_BYTES,
            multiline=True,
        ),
        mutation_result_receipts=mutation_result_receipts,
        transcript_receipts=transcript_receipts,
        documentation_receipts=documentation_receipts,
        explanation=explanation,
        proof_status="checked",
    )
    record["checked_result"] = evidence.result
    if evidence.certificate_artifact is None:  # pragma: no cover - proved invariant
        raise AuthoringContractError("checked result omitted its certificate artifact")
    record["proof_metrics"] = _proof_metrics_record(
        evidence.result,
        evidence.certificate_artifact,
        proof,
        record["readable_source_proof"],  # type: ignore[arg-type]
    )
    checked = _validate_proposal_record(record, candidate, proof_attempt)
    return _mint_carrier(
        TheoremProposal,
        canonical_json_bytes(checked),
        certificate_artifact=evidence.certificate_artifact,
    )


def load_theorem_proposal(
    raw: bytes,
    *,
    candidate: FormalizationCandidate,
    proof_attempt: ProofAttempt | None = None,
    original_formula: Formula | None = None,
    proof: Proof | None = None,
) -> TheoremProposal:
    """Load draft data, or freshly re-authorize checked data with a real proof."""

    authoring_schema()
    checked = _validate_proposal_record(
        _decode_canonical_object(raw, "theorem proposal"), candidate, proof_attempt
    )
    if checked["proof_status"] == "draft":
        if original_formula is not None or proof is not None:
            raise AuthoringContractError("draft proposal cannot carry proof authority")
        return _mint_carrier(TheoremProposal, canonical_json_bytes(checked))
    if original_formula is None or proof is None:
        raise AuthoringContractError(
            "checked proposal loading requires the original Formula and Proof"
        )
    evidence = _fresh_checked_evidence(
        candidate,
        checked["proposal_id"],  # type: ignore[arg-type]
        original_formula,
        proof,
    )
    if checked["checked_result"] != evidence.result:
        raise AuthoringContractError(
            "serialized checked result differs from fresh kernel evidence"
        )
    if evidence.certificate_artifact is None:  # pragma: no cover - proved invariant
        raise AuthoringContractError("checked result omitted its certificate artifact")
    expected_metrics = _proof_metrics_record(
        evidence.result,
        evidence.certificate_artifact,
        proof,
        checked["readable_source_proof"],  # type: ignore[arg-type]
    )
    if checked["proof_metrics"] != expected_metrics:
        raise AuthoringContractError(
            "serialized Pareto metrics differ from fresh proof evidence"
        )
    return _mint_carrier(
        TheoremProposal,
        canonical_json_bytes(checked),
        certificate_artifact=evidence.certificate_artifact,
    )


_LIFECYCLE_TRANSITIONS = {
    ("prose_only", "ambiguous"): "authoring-core",
    ("prose_only", "formalized_unproved"): "human-reviewer",
    ("ambiguous", "formalized_unproved"): "human-reviewer",
    ("formalized_unproved", "proved"): "kernel",
    ("proved", "reviewed"): "human-reviewer",
    ("reviewed", "admitted"): "catalog-administrator",
}

# Reviewed deposits are intentionally empty in the authoring core.  A production
# addition is a source-reviewed tuple of exact canonical event bytes, never caller
# input.  Each event stores the rolling root of the prefix ending at that event:
# later appends therefore preserve all earlier event bytes and record hashes.
# Python private names are an implementation boundary, not a security sandbox;
# arbitrary same-process access to private state is outside this module's threat
# model.  Public bytes still cross only the checked loaders below.
_REVIEWED_EVENT_REGISTRIES: dict[str, tuple[bytes, ...]] = {}
_REVIEWED_EXPORT_REGISTRIES: dict[str, tuple[bytes, ...]] = {}

RegistryKind = Literal["lifecycle", "export"]
_REGISTRY_ROOT_DOMAIN = b"peano-hydra-authoring-reviewed-registry-v1\0"


def _nonnegative_sequence(label: str, value: object) -> int:
    if type(value) is not int or not 0 <= value <= MAX_SAFE_JSON_INTEGER:
        raise AuthoringContractError(f"{label} must be a nonnegative integer")
    return value


def _registry_step_sha256(
    kind: RegistryKind,
    previous_registry_sha256: str | None,
    record: dict[str, object],
) -> str:
    """Derive an append-only prefix root without hashing its embedded root."""

    if kind not in {"lifecycle", "export"}:  # pragma: no cover - internal type guard
        raise AuthoringContractError("reviewed registry kind is unsupported")
    if type(record) is not dict or "registry_sha256" not in record:
        raise AuthoringContractError("reviewed registry event is malformed")
    previous = (
        b"genesis"
        if previous_registry_sha256 is None
        else bytes.fromhex(
            _sha256("previous reviewed registry root", previous_registry_sha256)
        )
    )
    payload = dict(record)
    del payload["registry_sha256"]
    return hashlib.sha256(
        _REGISTRY_ROOT_DOMAIN
        + kind.encode("ascii")
        + b"\0"
        + previous
        + b"\0"
        + canonical_json_bytes(payload)
    ).hexdigest()


def _validate_lifecycle_registry_member(
    value: dict[str, object],
    *,
    sequence: int,
    previous_value: dict[str, object] | None,
    previous_raw: bytes | None,
) -> None:
    if set(value) != _LIFECYCLE_EVENT_FIELDS:
        raise AuthoringContractError("lifecycle event has missing or additional fields")
    if value.get("format") != LIFECYCLE_EVENT_FORMAT:
        raise AuthoringContractError("lifecycle event identity is malformed")
    _require_version("lifecycle event version", value.get("v"), RECORD_VERSION)
    _safe_identifier("lifecycle event_id", value.get("event_id"))
    if _nonnegative_sequence("lifecycle sequence", value.get("sequence")) != sequence:
        raise AuthoringContractError("lifecycle registry sequence is discontinuous")
    _sha256("lifecycle proposal_sha256", value.get("proposal_sha256"))
    _safe_identifier("lifecycle actor_id", value.get("actor_id"))
    _safe_identifier("lifecycle session_owner_id", value.get("session_owner_id"))
    _sha256("lifecycle evidence_sha256", value.get("evidence_sha256"))
    from_state = value.get("from_state")
    to_state = value.get("to_state")
    authority = value.get("authority")
    if from_state not in LIFECYCLE_STATES or to_state not in LIFECYCLE_STATES:
        raise AuthoringContractError("lifecycle state is unsupported")
    expected_authority = _LIFECYCLE_TRANSITIONS.get((from_state, to_state))
    if expected_authority is None or authority != expected_authority:
        raise AuthoringContractError("lifecycle transition or authority is invalid")
    if previous_value is None:
        if value.get("previous_event_sha256") is not None or from_state != "prose_only":
            raise AuthoringContractError("first lifecycle event must start at prose_only")
        return
    if previous_raw is None:  # pragma: no cover - paired internal arguments
        raise AuthoringContractError("lifecycle registry predecessor is missing")
    if (
        value.get("previous_event_sha256") != _record_sha256(previous_raw)
        or previous_value.get("proposal_sha256") != value.get("proposal_sha256")
        or previous_value.get("to_state") != from_state
        or previous_value.get("session_owner_id") != value.get("session_owner_id")
    ):
        raise AuthoringContractError("lifecycle registry contains a fork or discontinuity")


def _validate_export_registry_member(value: dict[str, object], *, sequence: int) -> None:
    if set(value) != _EXPORT_EVENT_FIELDS:
        raise AuthoringContractError("export event has missing or additional fields")
    if value.get("format") != EXPORT_EVENT_FORMAT:
        raise AuthoringContractError("export event identity is malformed")
    _require_version("export event version", value.get("v"), RECORD_VERSION)
    _safe_identifier("export_id", value.get("export_id"))
    if _nonnegative_sequence("export sequence", value.get("sequence")) != sequence:
        raise AuthoringContractError("export registry sequence is discontinuous")
    _sha256("export proposal_sha256", value.get("proposal_sha256"))
    _sha256("export admitted_event_sha256", value.get("admitted_event_sha256"))
    _safe_identifier("export actor_id", value.get("actor_id"))
    _safe_identifier("export session_owner_id", value.get("session_owner_id"))
    _sha256("export patch_root_sha256", value.get("patch_root_sha256"))
    _sha256("export evidence_sha256", value.get("evidence_sha256"))
    destination = _safe_text(
        "export destination", value.get("destination"), max_bytes=MAX_MESSAGE_BYTES
    )
    if destination != destination.strip() or destination.splitlines() != [destination]:
        raise AuthoringContractError("export destination must be one exact line")
    if value.get("mode") != "patch-only":
        raise AuthoringContractError("export mode must be patch-only")


def _registry_deposit(
    kind: RegistryKind, expected_registry_sha256: str
) -> tuple[tuple[bytes, ...], tuple[dict[str, object], ...]]:
    """Validate one exact source-reviewed append-only registry prefix."""

    registry = _sha256("reviewed registry root", expected_registry_sha256)
    deposits = (
        _REVIEWED_EVENT_REGISTRIES
        if kind == "lifecycle"
        else _REVIEWED_EXPORT_REGISTRIES
    )
    members = deposits.get(registry)
    if type(members) is not tuple or not members:
        raise AuthoringContractError(f"{kind} event is absent from a reviewed registry")
    if len(members) > MAX_JSON_ITEMS:
        raise AuthoringContractError(f"{kind} registry has too many events")
    records: list[dict[str, object]] = []
    member_hashes: set[str] = set()
    member_ids: set[str] = set()
    previous_root: str | None = None
    for sequence, raw in enumerate(members):
        value = _decode_canonical_object(raw, f"reviewed {kind} registry event")
        if kind == "lifecycle":
            _validate_lifecycle_registry_member(
                value,
                sequence=sequence,
                previous_value=records[-1] if records else None,
                previous_raw=members[sequence - 1] if sequence else None,
            )
            identifier = value["event_id"]
        else:
            _validate_export_registry_member(value, sequence=sequence)
            identifier = value["export_id"]
        record_hash = _record_sha256(raw)
        if record_hash in member_hashes or identifier in member_ids:
            raise AuthoringContractError(f"{kind} registry contains a duplicate event")
        member_hashes.add(record_hash)
        member_ids.add(identifier)  # type: ignore[arg-type]
        prefix_root = _registry_step_sha256(kind, previous_root, value)
        if value.get("registry_sha256") != prefix_root:
            raise AuthoringContractError(
                f"{kind} event does not bind its exact ordered registry prefix"
            )
        previous_root = prefix_root
        records.append(value)
    if previous_root != registry:
        raise AuthoringContractError(f"{kind} registry key is not its derived root")
    _reject_registry_forks(kind, members, records, deposits)
    return members, tuple(records)


def _reject_registry_forks(
    kind: RegistryKind,
    members: tuple[bytes, ...],
    records: list[dict[str, object]],
    deposits: dict[str, tuple[bytes, ...]],
) -> None:
    """Reject two reviewed heads that branch from one logical event history."""

    proposal_sha256 = records[0].get("proposal_sha256") if kind == "lifecycle" else None
    for other_members in deposits.values():
        if other_members is members or type(other_members) is not tuple or not other_members:
            continue
        if kind == "lifecycle":
            other_first = _decode_canonical_object(
                other_members[0], "reviewed lifecycle registry event"
            )
            if other_first.get("proposal_sha256") != proposal_sha256:
                continue
        common = min(len(members), len(other_members))
        if members[:common] != other_members[:common]:
            raise AuthoringContractError(f"reviewed {kind} registries contain a fork")


def load_lifecycle_event(
    raw: bytes,
    *,
    proposal: TheoremProposal,
    expected_registry_sha256: str,
    expected_actor_id: str,
    expected_session_owner_id: str,
    previous_event: LifecycleEvent | None = None,
) -> LifecycleEvent:
    """Validate one event already authenticated by the host event registry.

    This module intentionally exposes no lifecycle-event builder. The trusted
    host registry must append and authenticate the event bytes first; this
    loader then enforces the exact proposal binding and state transition.
    """

    authoring_schema()
    if type(proposal) is not TheoremProposal:
        raise AuthoringContractError("lifecycle event needs a validated theorem proposal")
    registry = _sha256("authenticated lifecycle registry", expected_registry_sha256)
    actor = _safe_identifier("authenticated lifecycle actor", expected_actor_id)
    session_owner = _safe_identifier(
        "authenticated lifecycle session owner", expected_session_owner_id
    )
    members, records = _registry_deposit("lifecycle", registry)
    value = _decode_canonical_object(raw, "authoring lifecycle event")
    if raw != members[-1] or value != records[-1]:
        raise AuthoringContractError(
            "lifecycle event is not the unique head of the reviewed registry"
        )
    if value.get("proposal_sha256") != proposal.sha256:
        raise AuthoringContractError("lifecycle event is bound to another proposal")
    if (
        value.get("actor_id") != actor
        or value.get("session_owner_id") != session_owner
    ):
        raise AuthoringContractError(
            "lifecycle event actor or single-session owner is unauthenticated"
        )
    from_state = value.get("from_state")
    to_state = value.get("to_state")
    if previous_event is None:
        if value.get("sequence") != 0:
            raise AuthoringContractError("noninitial lifecycle event needs its predecessor")
        if value.get("previous_event_sha256") is not None or from_state != "prose_only":
            raise AuthoringContractError("first lifecycle event must start at prose_only")
    else:
        if type(previous_event) is not LifecycleEvent:
            raise AuthoringContractError("previous event must be a validated LifecycleEvent")
        if len(members) < 2:
            raise AuthoringContractError("first lifecycle event cannot have a predecessor")
        previous = previous_event.record
        previous_sequence = _nonnegative_sequence(
            "previous lifecycle sequence", previous.get("sequence")
        )
        if (
            value.get("sequence") != previous_sequence + 1
            or value.get("previous_event_sha256") != previous_event.sha256
            or previous.get("proposal_sha256") != proposal.sha256
            or previous.get("to_state") != from_state
            or previous.get("session_owner_id") != session_owner
            or previous_event.canonical_bytes != members[-2]
        ):
            raise AuthoringContractError("lifecycle event chain is stale or discontinuous")
    proposal_status = proposal.record.get("proof_status")
    if to_state in {"proved", "reviewed", "admitted"} and proposal_status != "checked":
        raise AuthoringContractError("proved/reviewed/admitted state needs a checked proposal")
    if to_state == "proved" and value.get("evidence_sha256") != proposal.record[
        "checked_result"
    ]["replay_evidence_sha256"]:
        raise AuthoringContractError(
            "proved lifecycle event differs from the proposal's kernel evidence"
        )
    return _mint_carrier(LifecycleEvent, canonical_json_bytes(value))


def load_export_event(
    raw: bytes,
    *,
    proposal: TheoremProposal,
    admitted_event: LifecycleEvent,
    expected_registry_sha256: str,
    expected_actor_id: str,
    expected_session_owner_id: str,
) -> ExportEvent:
    """Load an inert explicit export receipt from a reviewed deposit.

    This function does not write a patch, mutate Git, contact a destination,
    or export anything. It only validates an already deposited event.
    """

    authoring_schema()
    if type(proposal) is not TheoremProposal or type(admitted_event) is not LifecycleEvent:
        raise AuthoringContractError(
            "export event needs a validated proposal and admitted lifecycle event"
        )
    admitted = admitted_event.record
    if (
        admitted.get("proposal_sha256") != proposal.sha256
        or admitted.get("to_state") != "admitted"
        or admitted.get("authority") != "catalog-administrator"
    ):
        raise AuthoringContractError("export requires the exact admitted proposal event")
    registry = _sha256("reviewed export registry", expected_registry_sha256)
    actor = _safe_identifier("authenticated export actor", expected_actor_id)
    session_owner = _safe_identifier(
        "authenticated export session owner", expected_session_owner_id
    )
    members, records = _registry_deposit("export", registry)
    value = _decode_canonical_object(raw, "authoring export event")
    if raw != members[-1] or value != records[-1]:
        raise AuthoringContractError(
            "export event is not the unique head of the reviewed registry"
        )
    if (
        value.get("proposal_sha256") != proposal.sha256
        or value.get("admitted_event_sha256") != admitted_event.sha256
        or value.get("actor_id") != actor
        or value.get("session_owner_id") != session_owner
        or admitted.get("session_owner_id") != session_owner
    ):
        raise AuthoringContractError("export event binding is inconsistent")
    return _mint_carrier(ExportEvent, canonical_json_bytes(value))


__all__ = [
    "AUTHORING_SCHEMA_FORMAT",
    "AUTHORING_SCHEMA_ID",
    "AUTHORING_SCHEMA_PATH",
    "AUTHORING_SCHEMA_SHA256",
    "AUTHORING_SCHEMA_VERSION",
    "DIAGNOSTIC_AUTHORITIES",
    "LIFECYCLE_AUTHORITIES",
    "LIFECYCLE_STATES",
    "TRAINING_CONSENTS",
    "UNIT_KINDS",
    "AuthoringContractError",
    "AuthoringDiagnostic",
    "AuthoringDocument",
    "ExportEvent",
    "FormalizationCandidate",
    "LifecycleEvent",
    "LibraryEpochIdentity",
    "ProofAttempt",
    "SentenceUnit",
    "TheoremProposal",
    "authoring_schema",
    "authoring_schema_identity",
    "build_checked_theorem_proposal",
    "build_diagnostic",
    "build_document",
    "build_draft_theorem_proposal",
    "build_formalization_candidate",
    "build_kernel_diagnostic",
    "build_proof_attempt",
    "build_sentence_unit",
    "canonical_json_bytes",
    "library_epoch_identity",
    "load_diagnostic",
    "load_document",
    "load_export_event",
    "load_formalization_candidate",
    "load_lifecycle_event",
    "load_proof_attempt",
    "load_sentence_unit",
    "load_theorem_proposal",
]
