"""Exact, checked evidence records for Peano Hydra H0.1b.

The public positive constructor in this module accepts an actual kernel
``Formula`` and ``Proof``.  It computes a bounded canonical ``peano-lab-v2``
artifact, checks the proof with the ordinary intuitionistic kernel against
that original formula, derives proof metrics, and only then emits ``proved``.
No Boolean, hash, solver status, or caller-authored evidence object can mint a
positive result.

The object validators remain transport validators, not proof authorities.
Use :func:`validate_checked_proved_result` with the original ``Formula`` and
``Proof`` whenever a positive record is admitted or replayed.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from pathlib import Path
import re
from typing import Literal

from peano_lab.kernel import checker as kernel_checker
from peano_lab.kernel.artifact_codec import encode_artifact_bounded
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Proof


RESULT_FORMAT = "peano-hydra-result"
RESULT_VERSION = 1
RESULT_SCHEMA_FORMAT = "peano-hydra-result-schema"
RESULT_SCHEMA_ID = "peano-hydra-result-v1"
RESULT_SCHEMA_VERSION = 1
RESULT_SCHEMA_PATH = Path(__file__).with_name("result-schema-v1.json")
RESULT_SCHEMA_SHA256 = (
    "cf1caf1c867ddfbe3c247e42a18b730ea6790269718170a51f9733d5a7a36b26"
)

RESULT_HASH_PREIMAGE_FORMAT = "peano-hydra-result-hash-preimage"
RESULT_HASH_PREIMAGE_VERSION = 1
CERTIFICATE_REPRESENTATION = "peano-lab-v2"
KERNEL_IDENTITY_FORMAT = "peano-hydra-kernel-identity"
REPLAY_EVIDENCE_FORMAT = "peano-hydra-replay-evidence"
RUN_EVIDENCE_FORMAT = "peano-hydra-run-evidence"
EVIDENCE_OBJECT_VERSION = 1
LOGIC = "intuitionistic"
EMPTY_CONTEXT = "empty"

MAX_RESULT_SCHEMA_BYTES = 1_000_000
MAX_RESULT_BYTES = 1_000_000
MAX_CERTIFICATE_BYTES = 64_000_000
MAX_HASH_PREIMAGE_BYTES = 64_000_000
MAX_JSON_DEPTH = 128
MAX_JSON_CONTAINER_ITEMS = 1_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
MAX_CERTIFICATE_NODES = 1_000_000
CERTIFICATE_FUEL_MULTIPLIER = 8
CERTIFICATE_FUEL_OFFSET = 16

ResultKind = Literal["proved", "unknown"]
UnknownReason = Literal[
    "cancelled",
    "component-failure",
    "internal-error",
    "replay-rejected",
    "resource-limit",
    "search-exhausted",
    "timeout",
]
ReplayOutcome = Literal["accepted", "not-run", "rejected"]

UNKNOWN_REASONS: tuple[UnknownReason, ...] = (
    "cancelled",
    "component-failure",
    "internal-error",
    "replay-rejected",
    "resource-limit",
    "search-exhausted",
    "timeout",
)
_REASON_STATUS: dict[str, str] = {
    "cancelled": "cancelled",
    "component-failure": "error",
    "internal-error": "error",
    "replay-rejected": "replay-rejected",
    "resource-limit": "limit",
    "search-exhausted": "exhausted",
    "timeout": "timeout",
}
_RUN_STATUSES = frozenset(
    {"cancelled", "error", "exhausted", "limit", "proof", "replay-rejected", "timeout"}
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,159}")
_FORBIDDEN_NEGATIVE_TEXT = (
    "negative_evidence",
    "negative_evidence_sha256",
    "not_theorem",
)
_FORBIDDEN_NEGATIVE_KEYS = frozenset(_FORBIDDEN_NEGATIVE_TEXT)

_KERNEL_SOURCE_PATHS = (
    "peano-lab/py/peano_lab/kernel/artifact_codec.py",
    "peano-lab/py/peano_lab/kernel/checker.py",
    "peano-lab/py/peano_lab/kernel/formulas.py",
    "peano-lab/py/peano_lab/kernel/proofs.py",
    "peano-lab/py/peano_lab/kernel/subst.py",
    "peano-lab/py/peano_lab/kernel/terms.py",
)
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

_COMMON_RESULT_FIELDS = frozenset(
    {
        "format",
        "v",
        "kind",
        "logic",
        "semantic_profile_sha256",
        "original_theorem",
        "original_theorem_sha256",
        "run_evidence_sha256",
    }
)
_PROVED_RESULT_FIELDS = _COMMON_RESULT_FIELDS | {
    "certificate_representation",
    "certificate_sha256",
    "certificate_nodes",
    "certificate_depth",
    "kernel_identity_sha256",
    "replay_evidence_sha256",
    "kernel_accepted",
    "replay_outcome",
}
_UNKNOWN_RESULT_FIELDS = _COMMON_RESULT_FIELDS | {"reason"}
_KERNEL_IDENTITY_FIELDS = frozenset(
    {"format", "v", "checker", "logic", "context", "artifact_format", "sources"}
)
_KERNEL_SOURCE_FIELDS = frozenset({"path", "sha256"})
_REPLAY_EVIDENCE_FIELDS = frozenset(
    {
        "format",
        "v",
        "outcome",
        "logic",
        "context",
        "semantic_profile_sha256",
        "original_theorem",
        "original_theorem_sha256",
        "certificate_representation",
        "certificate_sha256",
        "certificate_nodes",
        "certificate_depth",
        "kernel_identity_sha256",
        "kernel_accepted",
    }
)
_RUN_COMMON_FIELDS = frozenset(
    {
        "format",
        "v",
        "run_id",
        "kind",
        "status",
        "logic",
        "semantic_profile_sha256",
        "original_theorem",
        "original_theorem_sha256",
        "degraded",
        "eligible_for_comparison",
    }
)
_PROVED_RUN_EVIDENCE_FIELDS = _RUN_COMMON_FIELDS | {
    "certificate_representation",
    "certificate_sha256",
    "kernel_identity_sha256",
    "replay_evidence_sha256",
    "kernel_accepted",
    "replay_outcome",
}
_UNKNOWN_RUN_EVIDENCE_FIELDS = _RUN_COMMON_FIELDS | {"reason"}
_MISSING = object()


class HydraResultSchemaError(ValueError):
    """A schema, result, or evidence preimage violates the frozen contract."""


@dataclass(frozen=True, slots=True)
class HydraResultEvidence:
    """Closed retained preimages for one result record.

    Properties return fresh JSON containers so mutating a caller-owned value
    cannot rewrite the evidence already bound by the builder.
    """

    _result_json: bytes
    certificate_artifact: bytes | None
    _kernel_identity_json: bytes | None
    _replay_evidence_json: bytes | None
    _run_evidence_json: bytes

    @property
    def result(self) -> dict[str, object]:
        return _decode_canonical_object(self._result_json, "result")

    @property
    def kernel_identity(self) -> dict[str, object] | None:
        if self._kernel_identity_json is None:
            return None
        return _decode_canonical_object(self._kernel_identity_json, "kernel identity")

    @property
    def replay_evidence(self) -> dict[str, object] | None:
        if self._replay_evidence_json is None:
            return None
        return _decode_canonical_object(self._replay_evidence_json, "replay evidence")

    @property
    def run_evidence(self) -> dict[str, object]:
        return _decode_canonical_object(self._run_evidence_json, "run evidence")


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


def _validate_strict_json(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise HydraResultSchemaError(f"{path} exceeds the JSON nesting limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise HydraResultSchemaError(f"{path} is outside the JSON integer domain")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise HydraResultSchemaError(
                f"{path} contains a non-scalar Unicode surrogate"
            ) from None
        return
    if type(value) not in (list, dict):
        raise HydraResultSchemaError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise HydraResultSchemaError(f"{path} contains a cyclic container")
    if len(value) > MAX_JSON_CONTAINER_ITEMS:
        raise HydraResultSchemaError(f"{path} has too many container items")
    next_ancestors = ancestors | {marker}
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_strict_json(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=next_ancestors,
            )
        return
    for key, item in value.items():
        if type(key) is not str:
            raise HydraResultSchemaError(f"{path} has a non-string object key")
        _validate_strict_json(key, path=f"{path}.<key>", depth=depth + 1)
        _validate_strict_json(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=next_ancestors,
        )


def canonical_json_bytes(value: object, *, limit: int = MAX_HASH_PREIMAGE_BYTES) -> bytes:
    """Encode one portable strict JSON value with the frozen Hydra rules."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON byte limit must be a positive integer")
    _validate_strict_json(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise HydraResultSchemaError(
            f"value cannot be encoded as canonical JSON: {exc}"
        ) from None
    if len(encoded) > limit:
        raise HydraResultSchemaError(
            f"canonical JSON exceeds the {limit}-byte transport limit"
        )
    return encoded


def _canonical_document_bytes(value: object) -> bytes:
    _validate_strict_json(value)
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
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise HydraResultSchemaError(f"{label} is not strict JSON: {exc}") from None


def _detached_json(value: object, *, limit: int) -> object:
    return _decode_json(canonical_json_bytes(value, limit=limit), "canonical value")


def _decode_canonical_object(raw: bytes, label: str) -> dict[str, object]:
    value = _decode_json(raw, label)
    if type(value) is not dict or canonical_json_bytes(value) != raw:
        raise HydraResultSchemaError(f"{label} is not one canonical JSON object")
    return value


def _load_schema(
    path: Path,
    *,
    expected_digest: str,
    expected_id: str,
    expected_version: int,
) -> dict[str, object]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise HydraResultSchemaError("cannot read registered result schema") from exc
    if len(raw) > MAX_RESULT_SCHEMA_BYTES:
        raise HydraResultSchemaError("registered result schema exceeds its size limit")
    value = _decode_json(raw, "registered result schema")
    if type(value) is not dict:
        raise HydraResultSchemaError("result schema must be one exact JSON object")
    if raw != _canonical_document_bytes(value):
        raise HydraResultSchemaError("registered result schema is not canonical JSON")
    digest = hashlib.sha256(canonical_json_bytes(value)).hexdigest()
    if digest != expected_digest:
        raise HydraResultSchemaError("registered result schema digest drifted")
    if (
        value.get("format") != RESULT_SCHEMA_FORMAT
        or type(value.get("v")) is not int
        or value.get("v") != expected_version
        or value.get("id") != expected_id
    ):
        raise HydraResultSchemaError("registered result schema identity is malformed")
    return _decode_canonical_object(canonical_json_bytes(value), "result schema")


def result_schema() -> dict[str, object]:
    """Load the exact checked result schema v1."""

    value = _load_schema(
        RESULT_SCHEMA_PATH,
        expected_digest=RESULT_SCHEMA_SHA256,
        expected_id=RESULT_SCHEMA_ID,
        expected_version=RESULT_SCHEMA_VERSION,
    )
    if value.get("additional_fields_policy") != (
        "forbidden-at-every-schema-owned-object"
    ):
        raise HydraResultSchemaError("active schema lost its closed-object policy")
    inner = value.get("inner_objects")
    if type(inner) is not dict or set(inner) != {
        "kernel_identity",
        "replay_evidence",
        "run_evidence",
    }:
        raise HydraResultSchemaError("active schema lost its inner object schemas")
    result = value.get("result")
    if type(result) is not dict:
        raise HydraResultSchemaError("active result variants are malformed")
    if set(result["proved"]["required"]) != _PROVED_RESULT_FIELDS:
        raise HydraResultSchemaError("active proved field set drifted")
    if set(result["unknown"]["required"]) != _UNKNOWN_RESULT_FIELDS:
        raise HydraResultSchemaError("active unknown field set drifted")
    run = inner["run_evidence"]
    if (
        type(run) is not dict
        or set(run["proved"]["required"]) != _PROVED_RUN_EVIDENCE_FIELDS
        or set(run["unknown"]["required"]) != _UNKNOWN_RUN_EVIDENCE_FIELDS
    ):
        raise HydraResultSchemaError("active run-evidence field sets drifted")
    for variant in (run["proved"], run["unknown"]):
        run_id_schema = variant["properties"]["run_id"]
        if run_id_schema.get(
            "forbidden_casefolded_separator_insensitive_substrings"
        ) != list(_FORBIDDEN_NEGATIVE_TEXT):
            raise HydraResultSchemaError(
                "active run-id negative-claim policy drifted"
            )
    return value


def result_schema_sha256() -> str:
    result_schema()
    return RESULT_SCHEMA_SHA256


def result_schema_identity() -> dict[str, object]:
    return {
        "format": RESULT_SCHEMA_FORMAT,
        "v": RESULT_SCHEMA_VERSION,
        "id": RESULT_SCHEMA_ID,
        "sha256": result_schema_sha256(),
    }


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise HydraResultSchemaError(f"{label} must be one lowercase SHA-256")
    return value


def _positive_integer(label: str, value: object) -> int:
    if type(value) is not int or not 1 <= value <= MAX_SAFE_JSON_INTEGER:
        raise HydraResultSchemaError(
            f"{label} must be an integer in 1..{MAX_SAFE_JSON_INTEGER}"
        )
    return value


def _certificate_metrics(value: dict[str, object]) -> tuple[int, int]:
    nodes = _positive_integer("certificate_nodes", value.get("certificate_nodes"))
    depth = _positive_integer("certificate_depth", value.get("certificate_depth"))
    if nodes > MAX_CERTIFICATE_NODES:
        raise HydraResultSchemaError("certificate_nodes exceeds the result node limit")
    if depth > nodes:
        raise HydraResultSchemaError(
            "certificate_depth cannot exceed certificate_nodes"
        )
    return nodes, depth


def _bounded_proof_metrics(proof: object) -> tuple[int, int]:
    """Count proof occurrences/depth while rejecting cycles and overgrowth."""

    if not isinstance(proof, Proof):
        raise HydraResultSchemaError("certificate must be a real kernel Proof")
    total = 0
    maximum_depth = 0
    active: set[int] = set()
    pending: list[tuple[Proof, int, bool]] = [(proof, 1, False)]
    while pending:
        node, depth, leaving = pending.pop()
        identity = id(node)
        if leaving:
            active.remove(identity)
            continue
        if identity in active:
            raise HydraResultSchemaError("certificate contains a cyclic proof graph")
        active.add(identity)
        total += 1
        if total > MAX_CERTIFICATE_NODES:
            raise HydraResultSchemaError("certificate exceeds the result node limit")
        maximum_depth = max(maximum_depth, depth)
        pending.append((node, depth, True))
        try:
            children = [
                child
                for item in fields(node)
                if isinstance((child := getattr(node, item.name)), Proof)
            ]
        except (TypeError, AttributeError) as exc:
            raise HydraResultSchemaError(
                f"certificate metrics failed: {exc}"
            ) from None
        pending.extend((child, depth + 1, False) for child in reversed(children))
    return total, maximum_depth


def _safe_run_id(value: object) -> str:
    if type(value) is not str or _RUN_ID_RE.fullmatch(value) is None:
        raise HydraResultSchemaError("run_id is not one bounded safe identifier")
    if _contains_forbidden_negative_text(value):
        raise HydraResultSchemaError("run_id contains forbidden negative-claim text")
    return value


def _contains_forbidden_negative_text(value: str) -> bool:
    """Detect forbidden vocabulary across every run-id separator spelling."""

    lowered = value.casefold()
    separated = re.sub(r"[^a-z0-9]+", "_", lowered).strip("_")
    compact = re.sub(r"[^a-z0-9]+", "", lowered)
    return any(
        token in separated or token.replace("_", "") in compact
        for token in _FORBIDDEN_NEGATIVE_KEYS
    )


def _reject_negative_claim_material(value: object, path: str = "$") -> None:
    if type(value) is dict:
        for key, item in value.items():
            if _contains_forbidden_negative_text(key):
                raise HydraResultSchemaError(
                    f"{path} contains forbidden negative-theoremhood key {key!r}"
                )
            _reject_negative_claim_material(item, f"{path}.{key}")
    elif type(value) is list:
        for index, item in enumerate(value):
            _reject_negative_claim_material(item, f"{path}[{index}]")


def _profile_registration(digest: object) -> dict[str, object]:
    value = _require_sha256("semantic_profile_sha256", digest)
    from training.peano_hydra.profile import semantic_profile_registration

    try:
        registration = semantic_profile_registration(value)
    except ValueError as exc:
        raise HydraResultSchemaError(str(exc)) from None
    if type(registration) is not dict:
        raise HydraResultSchemaError("semantic profile registry returned malformed data")
    expected_fields = {
        "certificate_representation",
        "format",
        "id",
        "logic",
        "result_schema_sha256",
        "result_schema_version",
        "sha256",
        "theorem_canonicalizer",
        "v",
    }
    if (
        set(registration) != expected_fields
        or registration.get("sha256") != value
        or registration.get("format") != "peano-hydra-semantic-profile"
        or registration.get("logic") != LOGIC
        or type(registration.get("v")) is not int
        or type(registration.get("id")) is not str
        or type(registration.get("theorem_canonicalizer")) is not str
    ):
        raise HydraResultSchemaError("semantic profile registry returned malformed data")
    return registration


def _result_profile_registration(digest: object) -> dict[str, object]:
    registration = _profile_registration(digest)
    if (
        registration.get("result_schema_version") != RESULT_SCHEMA_VERSION
        or registration.get("result_schema_sha256") != RESULT_SCHEMA_SHA256
        or registration.get("certificate_representation")
        != CERTIFICATE_REPRESENTATION
    ):
        raise HydraResultSchemaError(
            "semantic profile does not register this exact result schema"
        )
    return registration


def _active_profile_digest(value: object | None) -> str:
    from training.peano_hydra.profile import semantic_profile_sha256

    active = semantic_profile_sha256()
    if value is None:
        return active
    digest = _require_sha256("semantic_profile_sha256", value)
    if digest != active:
        raise HydraResultSchemaError(
            "new results must use the active registered semantic profile"
        )
    return digest


def _canonical_theorem(
    source: object,
    *,
    semantic_profile_sha256: object,
    require_canonical: bool,
) -> str:
    if type(source) is not str:
        raise HydraResultSchemaError("original_theorem must be text")
    digest = _require_sha256("semantic_profile_sha256", semantic_profile_sha256)
    from training.peano_hydra.profile import canonical_registered_profile_theorem

    try:
        canonical = canonical_registered_profile_theorem(digest, source)
    except (TypeError, ValueError) as exc:
        raise HydraResultSchemaError(f"original_theorem is invalid: {exc}") from None
    if require_canonical and canonical != source:
        raise HydraResultSchemaError(
            "original_theorem is not in canonical semantic-profile form"
        )
    return canonical


def _canonical_original_formula(
    formula: object,
    *,
    semantic_profile_sha256: str,
) -> tuple[Formula, str]:
    if not isinstance(formula, Formula):
        raise HydraResultSchemaError("original target must be a real kernel Formula")
    from training.peano_hydra.profile import canonical_registered_profile_formula

    try:
        theorem = canonical_registered_profile_formula(
            semantic_profile_sha256,
            formula,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise HydraResultSchemaError(f"original target cannot be canonicalized: {exc}") from None
    if _canonical_theorem(
        theorem,
        semantic_profile_sha256=semantic_profile_sha256,
        require_canonical=True,
    ) != theorem:
        raise HydraResultSchemaError(
            "original target is not an exact canonical profile formula"
        )
    return formula, theorem


def _json_hash_preimage(field: str, payload: object) -> bytes:
    return canonical_json_bytes(
        {
            "format": RESULT_HASH_PREIMAGE_FORMAT,
            "v": RESULT_HASH_PREIMAGE_VERSION,
            "field": field,
            "payload": payload,
        }
    )


def original_theorem_sha256(
    original_theorem: str,
    *,
    semantic_profile_sha256: str | None = None,
) -> str:
    profile_digest = (
        _active_profile_digest(None)
        if semantic_profile_sha256 is None
        else _require_sha256("semantic_profile_sha256", semantic_profile_sha256)
    )
    _profile_registration(profile_digest)
    theorem = _canonical_theorem(
        original_theorem,
        semantic_profile_sha256=profile_digest,
        require_canonical=True,
    )
    return hashlib.sha256(
        _json_hash_preimage("original_theorem_sha256", theorem)
    ).hexdigest()


def _validate_certificate_artifact(value: object) -> bytes:
    if type(value) is not bytes or not value or len(value) > MAX_CERTIFICATE_BYTES:
        raise HydraResultSchemaError("certificate artifact must be bounded exact bytes")
    if not value.endswith(b"\n") or value.endswith(b"\n\n"):
        raise HydraResultSchemaError(
            "peano-lab-v2 certificate must end in exactly one LF"
        )
    core = value[:-1]
    decoded = _decode_json(core, "peano-lab-v2 certificate")
    if canonical_json_bytes(decoded, limit=MAX_CERTIFICATE_BYTES) != core:
        raise HydraResultSchemaError("peano-lab-v2 certificate is not canonical JSON")
    if (
        type(decoded) is not list
        or len(decoded) != 4
        or decoded[0] != CERTIFICATE_REPRESENTATION
        or type(decoded[1]) is not int
        or decoded[1] < 1
        or type(decoded[2]) is not list
        or type(decoded[3]) is not list
    ):
        raise HydraResultSchemaError("peano-lab-v2 certificate envelope is malformed")
    return bytes(value)


def certificate_sha256(certificate_artifact: bytes) -> str:
    """Hash the exact reconstructable artifact bytes, including terminal LF."""

    return hashlib.sha256(_validate_certificate_artifact(certificate_artifact)).hexdigest()


def _live_kernel_sources() -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for relative in _KERNEL_SOURCE_PATHS:
        try:
            data = (_REPOSITORY_ROOT / relative).read_bytes()
        except OSError as exc:
            raise HydraResultSchemaError(
                f"cannot identify kernel source {relative!r}"
            ) from exc
        records.append({"path": relative, "sha256": hashlib.sha256(data).hexdigest()})
    return records


def live_kernel_identity() -> dict[str, object]:
    """Derive the exact checker/codec identity used by the checked builder."""

    return {
        "format": KERNEL_IDENTITY_FORMAT,
        "v": EVIDENCE_OBJECT_VERSION,
        "checker": "peano_lab.kernel.checker.check",
        "logic": LOGIC,
        "context": EMPTY_CONTEXT,
        "artifact_format": CERTIFICATE_REPRESENTATION,
        "sources": _live_kernel_sources(),
    }


def _validate_kernel_identity(value: object, *, require_live: bool) -> dict[str, object]:
    detached = _detached_json(value, limit=MAX_HASH_PREIMAGE_BYTES)
    if type(detached) is not dict or set(detached) != _KERNEL_IDENTITY_FIELDS:
        raise HydraResultSchemaError("kernel identity has non-canonical fields")
    constants = {
        "format": KERNEL_IDENTITY_FORMAT,
        "v": EVIDENCE_OBJECT_VERSION,
        "checker": "peano_lab.kernel.checker.check",
        "logic": LOGIC,
        "context": EMPTY_CONTEXT,
        "artifact_format": CERTIFICATE_REPRESENTATION,
    }
    if any(detached.get(key) != expected for key, expected in constants.items()):
        raise HydraResultSchemaError("kernel identity constants are malformed")
    sources = detached.get("sources")
    if type(sources) is not list or len(sources) != len(_KERNEL_SOURCE_PATHS):
        raise HydraResultSchemaError("kernel identity source manifest is malformed")
    for expected_path, item in zip(_KERNEL_SOURCE_PATHS, sources):
        if (
            type(item) is not dict
            or set(item) != _KERNEL_SOURCE_FIELDS
            or item.get("path") != expected_path
        ):
            raise HydraResultSchemaError("kernel identity source row is malformed")
        _require_sha256("kernel source sha256", item.get("sha256"))
    if require_live and detached != live_kernel_identity():
        raise HydraResultSchemaError("kernel identity differs from the live checker")
    return detached


def kernel_identity_sha256(kernel_identity: object) -> str:
    checked = _validate_kernel_identity(kernel_identity, require_live=False)
    return hashlib.sha256(
        _json_hash_preimage("kernel_identity_sha256", checked)
    ).hexdigest()


def _validate_replay_evidence(value: object) -> dict[str, object]:
    detached = _detached_json(value, limit=MAX_HASH_PREIMAGE_BYTES)
    if type(detached) is not dict or set(detached) != _REPLAY_EVIDENCE_FIELDS:
        raise HydraResultSchemaError("replay evidence has non-canonical fields")
    constants = {
        "format": REPLAY_EVIDENCE_FORMAT,
        "v": EVIDENCE_OBJECT_VERSION,
        "outcome": "accepted",
        "logic": LOGIC,
        "context": EMPTY_CONTEXT,
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "kernel_accepted": True,
    }
    if any(detached.get(key) != expected for key, expected in constants.items()):
        raise HydraResultSchemaError("replay evidence constants are malformed")
    profile_digest = _require_sha256(
        "semantic_profile_sha256", detached.get("semantic_profile_sha256")
    )
    _result_profile_registration(profile_digest)
    theorem = _canonical_theorem(
        detached.get("original_theorem"),
        semantic_profile_sha256=profile_digest,
        require_canonical=True,
    )
    if detached.get("original_theorem_sha256") != original_theorem_sha256(
        theorem, semantic_profile_sha256=profile_digest
    ):
        raise HydraResultSchemaError("replay theorem hash/preimage mismatch")
    for field in (
        "certificate_sha256",
        "kernel_identity_sha256",
    ):
        _require_sha256(field, detached.get(field))
    _certificate_metrics(detached)
    return detached


def replay_evidence_sha256(replay_evidence: object) -> str:
    checked = _validate_replay_evidence(replay_evidence)
    return hashlib.sha256(
        _json_hash_preimage("replay_evidence_sha256", checked)
    ).hexdigest()


def _validate_run_evidence(value: object) -> dict[str, object]:
    detached = _detached_json(value, limit=MAX_HASH_PREIMAGE_BYTES)
    if type(detached) is not dict:
        raise HydraResultSchemaError("run evidence must be one exact object")
    kind = detached.get("kind")
    expected_fields = (
        _PROVED_RUN_EVIDENCE_FIELDS
        if kind == "proved"
        else _UNKNOWN_RUN_EVIDENCE_FIELDS
    )
    if kind not in {"proved", "unknown"} or set(detached) != expected_fields:
        raise HydraResultSchemaError("run evidence has non-canonical fields")
    if (
        detached.get("format") != RUN_EVIDENCE_FORMAT
        or type(detached.get("v")) is not int
        or detached.get("v") != EVIDENCE_OBJECT_VERSION
        or detached.get("logic") != LOGIC
    ):
        raise HydraResultSchemaError("run evidence constants are malformed")
    _safe_run_id(detached.get("run_id"))
    profile_digest = _require_sha256(
        "semantic_profile_sha256", detached.get("semantic_profile_sha256")
    )
    _result_profile_registration(profile_digest)
    theorem = _canonical_theorem(
        detached.get("original_theorem"),
        semantic_profile_sha256=profile_digest,
        require_canonical=True,
    )
    if detached.get("original_theorem_sha256") != original_theorem_sha256(
        theorem, semantic_profile_sha256=profile_digest
    ):
        raise HydraResultSchemaError("run theorem hash/preimage mismatch")
    if detached.get("status") not in _RUN_STATUSES:
        raise HydraResultSchemaError("run evidence status is unsupported")
    if type(detached.get("degraded")) is not bool or type(
        detached.get("eligible_for_comparison")
    ) is not bool:
        raise HydraResultSchemaError("run comparison flags must be Booleans")
    if detached["degraded"] and detached["eligible_for_comparison"]:
        raise HydraResultSchemaError("a degraded run cannot be comparison eligible")
    if kind == "proved":
        if (
            detached["status"] != "proof"
            or detached["certificate_representation"] != CERTIFICATE_REPRESENTATION
            or detached["kernel_accepted"] is not True
            or detached["replay_outcome"] != "accepted"
        ):
            raise HydraResultSchemaError("proved run evidence is inconsistent")
        for field in (
            "certificate_sha256",
            "kernel_identity_sha256",
            "replay_evidence_sha256",
        ):
            _require_sha256(field, detached.get(field))
    else:
        _reject_negative_claim_material(detached)
        reason = detached.get("reason")
        if type(reason) is not str or reason not in UNKNOWN_REASONS:
            raise HydraResultSchemaError("unknown run reason is unsupported")
        if detached["status"] != _REASON_STATUS[reason]:
            raise HydraResultSchemaError("unknown run evidence is inconsistent")
    return detached


def run_evidence_sha256(run_evidence: object) -> str:
    checked = _validate_run_evidence(run_evidence)
    return hashlib.sha256(
        _json_hash_preimage("run_evidence_sha256", checked)
    ).hexdigest()


def _validate_result_record(value: dict[str, object]) -> dict[str, object]:
    if value.get("format") != RESULT_FORMAT:
        raise HydraResultSchemaError("Hydra result format is unsupported")
    if type(value.get("v")) is not int or value.get("v") != RESULT_VERSION:
        raise HydraResultSchemaError("Hydra result v must be integer 1")
    profile_digest = _require_sha256(
        "semantic_profile_sha256", value.get("semantic_profile_sha256")
    )
    _result_profile_registration(profile_digest)
    kind = value.get("kind")
    expected = _PROVED_RESULT_FIELDS if kind == "proved" else _UNKNOWN_RESULT_FIELDS
    if kind not in {"proved", "unknown"} or set(value) != expected:
        raise HydraResultSchemaError("Hydra result has missing or additional fields")
    if value.get("logic") != LOGIC:
        raise HydraResultSchemaError("Hydra result must be intuitionistic")
    theorem = _canonical_theorem(
        value.get("original_theorem"),
        semantic_profile_sha256=profile_digest,
        require_canonical=True,
    )
    if value.get("original_theorem_sha256") != original_theorem_sha256(
        theorem, semantic_profile_sha256=profile_digest
    ):
        raise HydraResultSchemaError("original theorem hash/preimage mismatch")
    _require_sha256("run_evidence_sha256", value.get("run_evidence_sha256"))
    if kind == "proved":
        if (
            value.get("certificate_representation") != CERTIFICATE_REPRESENTATION
            or value.get("kernel_accepted") is not True
            or value.get("replay_outcome") != "accepted"
        ):
            raise HydraResultSchemaError("proved result constants are malformed")
        for field in (
            "certificate_sha256",
            "kernel_identity_sha256",
            "replay_evidence_sha256",
        ):
            _require_sha256(field, value.get(field))
        _certificate_metrics(value)
    else:
        _reject_negative_claim_material(value)
        reason = value.get("reason")
        if type(reason) is not str or reason not in UNKNOWN_REASONS:
            raise HydraResultSchemaError("unknown result is inconsistent")
    return value


def validate_result(
    value: object,
    *,
    expected_semantic_profile_sha256: str | None = None,
) -> dict[str, object]:
    """Validate result v1 against its registered profile, not merely active."""

    detached = _detached_json(value, limit=MAX_RESULT_BYTES)
    if type(detached) is not dict:
        raise HydraResultSchemaError("Hydra result must be one exact JSON object")
    if expected_semantic_profile_sha256 is not None and detached.get(
        "semantic_profile_sha256"
    ) != _require_sha256(
        "expected_semantic_profile_sha256", expected_semantic_profile_sha256
    ):
        raise HydraResultSchemaError("Hydra result has a different semantic profile")
    return _validate_result_record(detached)


def validate_result_preimages(
    value: object,
    *,
    run_evidence: object,
    certificate_artifact: object = _MISSING,
    kernel_identity: object = _MISSING,
    replay_evidence: object = _MISSING,
    expected_semantic_profile_sha256: str | None = None,
) -> dict[str, object]:
    """Recompute v1 transport hashes; this function is not proof authority."""

    result = validate_result(
        value,
        expected_semantic_profile_sha256=expected_semantic_profile_sha256,
    )
    run = _validate_run_evidence(run_evidence)
    if result["run_evidence_sha256"] != run_evidence_sha256(run):
        raise HydraResultSchemaError("run evidence hash/preimage mismatch")
    for field in (
        "kind",
        "logic",
        "semantic_profile_sha256",
        "original_theorem",
        "original_theorem_sha256",
    ):
        if run[field] != result[field]:
            raise HydraResultSchemaError(f"run/result binding mismatch at {field}")
    if result["kind"] == "unknown":
        if any(
            item is not _MISSING
            for item in (certificate_artifact, kernel_identity, replay_evidence)
        ):
            raise HydraResultSchemaError(
                "unknown result cannot carry positive-evidence preimages"
            )
        if run["reason"] != result["reason"]:
            raise HydraResultSchemaError("unknown run/result reason mismatch")
        return result
    for field in (
        "certificate_representation",
        "certificate_sha256",
        "kernel_identity_sha256",
        "replay_evidence_sha256",
        "kernel_accepted",
        "replay_outcome",
    ):
        if run[field] != result[field]:
            raise HydraResultSchemaError(f"run/result binding mismatch at {field}")
    if any(
        item is _MISSING
        for item in (certificate_artifact, kernel_identity, replay_evidence)
    ):
        raise HydraResultSchemaError(
            "proved result requires certificate, kernel, and replay preimages"
        )
    artifact = _validate_certificate_artifact(certificate_artifact)
    kernel = _validate_kernel_identity(kernel_identity, require_live=False)
    replay = _validate_replay_evidence(replay_evidence)
    if result["certificate_sha256"] != certificate_sha256(artifact):
        raise HydraResultSchemaError("certificate hash/preimage mismatch")
    if result["kernel_identity_sha256"] != kernel_identity_sha256(kernel):
        raise HydraResultSchemaError("kernel identity hash/preimage mismatch")
    if result["replay_evidence_sha256"] != replay_evidence_sha256(replay):
        raise HydraResultSchemaError("replay evidence hash/preimage mismatch")
    for field in (
        "logic",
        "semantic_profile_sha256",
        "original_theorem",
        "original_theorem_sha256",
        "certificate_representation",
        "certificate_sha256",
        "certificate_nodes",
        "certificate_depth",
        "kernel_identity_sha256",
        "kernel_accepted",
    ):
        if replay[field] != result[field]:
            raise HydraResultSchemaError(f"replay/result binding mismatch at {field}")
    return result


def _run_evidence_common(
    *,
    run_id: str,
    kind: ResultKind,
    status: str,
    semantic_profile_sha256: str,
    theorem: str,
    theorem_sha256: str,
    degraded: bool,
    eligible_for_comparison: bool,
) -> dict[str, object]:
    return {
        "format": RUN_EVIDENCE_FORMAT,
        "v": EVIDENCE_OBJECT_VERSION,
        "run_id": run_id,
        "kind": kind,
        "status": status,
        "logic": LOGIC,
        "semantic_profile_sha256": semantic_profile_sha256,
        "original_theorem": theorem,
        "original_theorem_sha256": theorem_sha256,
        "degraded": degraded,
        "eligible_for_comparison": eligible_for_comparison,
    }


def _proved_run_evidence(
    *,
    run_id: str,
    semantic_profile_sha256: str,
    theorem: str,
    theorem_sha256: str,
    certificate_sha256_value: str,
    kernel_identity_sha256_value: str,
    replay_evidence_sha256_value: str,
    degraded: bool,
    eligible_for_comparison: bool,
) -> dict[str, object]:
    value = _run_evidence_common(
        run_id=run_id,
        kind="proved",
        status="proof",
        semantic_profile_sha256=semantic_profile_sha256,
        theorem=theorem,
        theorem_sha256=theorem_sha256,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    )
    value.update(
        {
            "certificate_representation": CERTIFICATE_REPRESENTATION,
            "certificate_sha256": certificate_sha256_value,
            "kernel_identity_sha256": kernel_identity_sha256_value,
            "replay_evidence_sha256": replay_evidence_sha256_value,
            "kernel_accepted": True,
            "replay_outcome": "accepted",
        }
    )
    return _validate_run_evidence(value)


def _unknown_run_evidence(
    *,
    run_id: str,
    reason: UnknownReason,
    semantic_profile_sha256: str,
    theorem: str,
    theorem_sha256: str,
    degraded: bool,
    eligible_for_comparison: bool,
) -> dict[str, object]:
    value = _run_evidence_common(
        run_id=run_id,
        kind="unknown",
        status=_REASON_STATUS[reason],
        semantic_profile_sha256=semantic_profile_sha256,
        theorem=theorem,
        theorem_sha256=theorem_sha256,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    )
    value["reason"] = reason
    return _validate_run_evidence(value)


def _evidence_bundle(
    result: dict[str, object],
    *,
    certificate_artifact: bytes | None,
    kernel_identity: dict[str, object] | None,
    replay_evidence: dict[str, object] | None,
    run_evidence: dict[str, object],
) -> HydraResultEvidence:
    return HydraResultEvidence(
        _result_json=canonical_json_bytes(result, limit=MAX_RESULT_BYTES),
        certificate_artifact=(
            None if certificate_artifact is None else bytes(certificate_artifact)
        ),
        _kernel_identity_json=(
            None if kernel_identity is None else canonical_json_bytes(kernel_identity)
        ),
        _replay_evidence_json=(
            None if replay_evidence is None else canonical_json_bytes(replay_evidence)
        ),
        _run_evidence_json=canonical_json_bytes(run_evidence),
    )


def build_checked_proved_evidence(
    original_formula: Formula,
    proof: Proof,
    *,
    run_id: str,
    semantic_profile_sha256: str | None = None,
    degraded: bool = False,
    eligible_for_comparison: bool = False,
) -> HydraResultEvidence:
    """Kernel-check a real proof and retain every exact positive preimage."""

    if not isinstance(proof, Proof):
        raise HydraResultSchemaError("certificate must be a real kernel Proof")
    _safe_run_id(run_id)
    if type(degraded) is not bool or type(eligible_for_comparison) is not bool:
        raise HydraResultSchemaError("comparison flags must be Booleans")
    if degraded and eligible_for_comparison:
        raise HydraResultSchemaError("a degraded run cannot be comparison eligible")
    profile_digest = _active_profile_digest(semantic_profile_sha256)
    _result_profile_registration(profile_digest)
    target, theorem = _canonical_original_formula(
        original_formula,
        semantic_profile_sha256=profile_digest,
    )

    # Encode under a bound after deriving exact proof metrics.  The encoder
    # rejects subclasses, malformed fields, cycles, and non-canonical syntax
    # independently of result packaging.  The intuitionistic checker below,
    # not the inert encoder, rejects a well-formed classical DNE node.
    nodes, depth = _bounded_proof_metrics(proof)
    fuel = CERTIFICATE_FUEL_MULTIPLIER * nodes + CERTIFICATE_FUEL_OFFSET
    try:
        artifact = encode_artifact_bounded(
            fuel,
            target,
            proof,
            max_bytes=MAX_CERTIFICATE_BYTES,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise HydraResultSchemaError(f"certificate encoding failed: {exc}") from None
    if not kernel_checker.check((), proof, target):
        raise HydraResultSchemaError(
            "independent intuitionistic kernel rejected the original goal"
        )

    # A second metric/encoding pass detects mutation between check and binding.
    try:
        after_metrics = _bounded_proof_metrics(proof)
        after_artifact = encode_artifact_bounded(
            fuel,
            target,
            proof,
            max_bytes=MAX_CERTIFICATE_BYTES,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise HydraResultSchemaError(
            f"certificate changed during checked construction: {exc}"
        ) from None
    if (
        after_metrics != (nodes, depth)
        or after_artifact != artifact
        or not kernel_checker.check((), proof, target)
    ):
        raise HydraResultSchemaError("certificate changed during checked construction")

    theorem_digest = original_theorem_sha256(
        theorem, semantic_profile_sha256=profile_digest
    )
    certificate_digest = certificate_sha256(artifact)
    kernel_identity = _validate_kernel_identity(
        live_kernel_identity(), require_live=True
    )
    kernel_digest = kernel_identity_sha256(kernel_identity)
    replay_evidence = _validate_replay_evidence(
        {
            "format": REPLAY_EVIDENCE_FORMAT,
            "v": EVIDENCE_OBJECT_VERSION,
            "outcome": "accepted",
            "logic": LOGIC,
            "context": EMPTY_CONTEXT,
            "semantic_profile_sha256": profile_digest,
            "original_theorem": theorem,
            "original_theorem_sha256": theorem_digest,
            "certificate_representation": CERTIFICATE_REPRESENTATION,
            "certificate_sha256": certificate_digest,
            "certificate_nodes": nodes,
            "certificate_depth": depth,
            "kernel_identity_sha256": kernel_digest,
            "kernel_accepted": True,
        }
    )
    replay_digest = replay_evidence_sha256(replay_evidence)
    run_evidence = _proved_run_evidence(
        run_id=run_id,
        semantic_profile_sha256=profile_digest,
        theorem=theorem,
        theorem_sha256=theorem_digest,
        certificate_sha256_value=certificate_digest,
        kernel_identity_sha256_value=kernel_digest,
        replay_evidence_sha256_value=replay_digest,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    )
    result = _validate_result_record(
        {
            "format": RESULT_FORMAT,
            "v": RESULT_VERSION,
            "kind": "proved",
            "logic": LOGIC,
            "semantic_profile_sha256": profile_digest,
            "original_theorem": theorem,
            "original_theorem_sha256": theorem_digest,
            "run_evidence_sha256": run_evidence_sha256(run_evidence),
            "certificate_representation": CERTIFICATE_REPRESENTATION,
            "certificate_sha256": certificate_digest,
            "certificate_nodes": nodes,
            "certificate_depth": depth,
            "kernel_identity_sha256": kernel_digest,
            "replay_evidence_sha256": replay_digest,
            "kernel_accepted": True,
            "replay_outcome": "accepted",
        }
    )
    validate_result_preimages(
        result,
        run_evidence=run_evidence,
        certificate_artifact=artifact,
        kernel_identity=kernel_identity,
        replay_evidence=replay_evidence,
        expected_semantic_profile_sha256=profile_digest,
    )
    return _evidence_bundle(
        result,
        certificate_artifact=artifact,
        kernel_identity=kernel_identity,
        replay_evidence=replay_evidence,
        run_evidence=run_evidence,
    )


def build_checked_proved_result(
    original_formula: Formula,
    proof: Proof,
    *,
    run_id: str,
    semantic_profile_sha256: str | None = None,
    degraded: bool = False,
    eligible_for_comparison: bool = False,
) -> dict[str, object]:
    """Return only the publishable record from checked positive evidence."""

    return build_checked_proved_evidence(
        original_formula,
        proof,
        run_id=run_id,
        semantic_profile_sha256=semantic_profile_sha256,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    ).result


def validate_checked_proved_result(
    value: object,
    original_formula: Formula,
    proof: Proof,
    *,
    run_evidence: object,
    kernel_identity: object,
    replay_evidence: object,
) -> dict[str, object]:
    """Re-run the kernel and compare all derived proof data with a record."""

    result = validate_result(value)
    profile_digest = _require_sha256(
        "semantic_profile_sha256", result["semantic_profile_sha256"]
    )
    target, theorem = _canonical_original_formula(
        original_formula,
        semantic_profile_sha256=profile_digest,
    )
    if result["kind"] != "proved" or result["original_theorem"] != theorem:
        raise HydraResultSchemaError("checked replay original target mismatch")
    if not isinstance(proof, Proof) or not kernel_checker.check((), proof, target):
        raise HydraResultSchemaError("checked replay kernel rejection")
    nodes, depth = _bounded_proof_metrics(proof)
    fuel = CERTIFICATE_FUEL_MULTIPLIER * nodes + CERTIFICATE_FUEL_OFFSET
    artifact = encode_artifact_bounded(
        fuel,
        target,
        proof,
        max_bytes=MAX_CERTIFICATE_BYTES,
    )
    # Now invoke the transport comparison with the derived artifact.
    checked = validate_result_preimages(
        result,
        run_evidence=run_evidence,
        certificate_artifact=artifact,
        kernel_identity=kernel_identity,
        replay_evidence=replay_evidence,
    )
    if checked["certificate_nodes"] != nodes or checked["certificate_depth"] != depth:
        raise HydraResultSchemaError("checked replay certificate metrics mismatch")
    if _validate_kernel_identity(kernel_identity, require_live=True) != live_kernel_identity():
        raise HydraResultSchemaError("checked replay kernel identity mismatch")
    return checked


def build_unknown_evidence(
    original_theorem: str,
    *,
    reason: UnknownReason,
    run_id: str,
    semantic_profile_sha256: str | None = None,
    degraded: bool = False,
    eligible_for_comparison: bool = False,
) -> HydraResultEvidence:
    """Build unknown with no certificate and no negative-theoremhood channel."""

    if type(reason) is not str or reason not in UNKNOWN_REASONS:
        raise HydraResultSchemaError("unknown result reason is unsupported")
    profile_digest = _active_profile_digest(semantic_profile_sha256)
    _result_profile_registration(profile_digest)
    theorem = _canonical_theorem(
        original_theorem,
        semantic_profile_sha256=profile_digest,
        require_canonical=False,
    )
    _safe_run_id(run_id)
    if type(degraded) is not bool or type(eligible_for_comparison) is not bool:
        raise HydraResultSchemaError("comparison flags must be Booleans")
    theorem_digest = original_theorem_sha256(
        theorem, semantic_profile_sha256=profile_digest
    )
    run_evidence = _unknown_run_evidence(
        run_id=run_id,
        reason=reason,
        semantic_profile_sha256=profile_digest,
        theorem=theorem,
        theorem_sha256=theorem_digest,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    )
    result = _validate_result_record(
        {
            "format": RESULT_FORMAT,
            "v": RESULT_VERSION,
            "kind": "unknown",
            "logic": LOGIC,
            "semantic_profile_sha256": profile_digest,
            "original_theorem": theorem,
            "original_theorem_sha256": theorem_digest,
            "run_evidence_sha256": run_evidence_sha256(run_evidence),
            "reason": reason,
        }
    )
    validate_result_preimages(result, run_evidence=run_evidence)
    return _evidence_bundle(
        result,
        certificate_artifact=None,
        kernel_identity=None,
        replay_evidence=None,
        run_evidence=run_evidence,
    )


def build_unknown_result(
    original_theorem: str,
    *,
    reason: UnknownReason,
    run_id: str,
    semantic_profile_sha256: str | None = None,
    degraded: bool = False,
    eligible_for_comparison: bool = False,
) -> dict[str, object]:
    return build_unknown_evidence(
        original_theorem,
        reason=reason,
        run_id=run_id,
        semantic_profile_sha256=semantic_profile_sha256,
        degraded=degraded,
        eligible_for_comparison=eligible_for_comparison,
    ).result


__all__ = [
    "CERTIFICATE_FUEL_MULTIPLIER",
    "CERTIFICATE_FUEL_OFFSET",
    "CERTIFICATE_REPRESENTATION",
    "EMPTY_CONTEXT",
    "EVIDENCE_OBJECT_VERSION",
    "HydraResultEvidence",
    "HydraResultSchemaError",
    "KERNEL_IDENTITY_FORMAT",
    "LOGIC",
    "MAX_CERTIFICATE_BYTES",
    "MAX_CERTIFICATE_NODES",
    "MAX_HASH_PREIMAGE_BYTES",
    "MAX_RESULT_BYTES",
    "MAX_RESULT_SCHEMA_BYTES",
    "MAX_SAFE_JSON_INTEGER",
    "REPLAY_EVIDENCE_FORMAT",
    "RESULT_FORMAT",
    "RESULT_HASH_PREIMAGE_FORMAT",
    "RESULT_HASH_PREIMAGE_VERSION",
    "RESULT_SCHEMA_FORMAT",
    "RESULT_SCHEMA_ID",
    "RESULT_SCHEMA_PATH",
    "RESULT_SCHEMA_SHA256",
    "RESULT_SCHEMA_VERSION",
    "RESULT_VERSION",
    "RUN_EVIDENCE_FORMAT",
    "ReplayOutcome",
    "ResultKind",
    "UNKNOWN_REASONS",
    "UnknownReason",
    "build_checked_proved_evidence",
    "build_checked_proved_result",
    "build_unknown_evidence",
    "build_unknown_result",
    "canonical_json_bytes",
    "certificate_sha256",
    "kernel_identity_sha256",
    "live_kernel_identity",
    "original_theorem_sha256",
    "replay_evidence_sha256",
    "result_schema",
    "result_schema_identity",
    "result_schema_sha256",
    "run_evidence_sha256",
    "validate_checked_proved_result",
    "validate_result",
    "validate_result_preimages",
]
