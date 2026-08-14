"""Isolated, streaming replay of a candidate Peano Hydra library pack.

This module intentionally imports no theorem library, tactic engine, UI,
solver, or model code.  It treats every packed byte as untrusted, reconstructs
exact kernel syntax through the bounded ``peano-lab-v2`` decoder, binds the
decoded target to the packed catalog statement, and asks the independent
intuitionistic kernel to check the proof from the empty context.

The format is a candidate H1.1 transport, not a production ``L0`` freeze.
Current dependency vectors and Python object-sharing metrics are retained as
source-stage observations.  Dependency minimality, readable/optimized vectors,
documentation receipts, the independent owner deposit, and benchmark sealing
remain separate gates.
"""

from __future__ import annotations

from dataclasses import fields
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Callable, Mapping

from peano_lab.kernel.artifact_codec import (
    ArtifactDecodeError,
    MAX_DECODE_INTEGER_DIGITS,
    decode_artifact,
    encode_formula,
    encode_proof,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula, parse_formula_with_names, pretty_formula
from peano_lab.kernel.proofs import Cut, Proof


REPLAY_PACK_SCHEMA_FORMAT = "peano-hydra-library-replay-pack-schema"
REPLAY_PACK_SCHEMA_VERSION = 1
REPLAY_PACK_SCHEMA_ID = "peano-hydra-library-replay-pack-v1"
REPLAY_PACK_SCHEMA_PATH = Path(__file__).with_name(
    "library-replay-pack-schema-v1.json"
)
REPLAY_PACK_SCHEMA_SHA256 = (
    "d60b07fe68aa4ba023c9bb873e2df4190752f70252caca21da7e76dcd393f02d"
)

REPLAY_PACK_FORMAT = "peano-hydra-library-replay-pack-manifest"
REPLAY_PACK_VERSION = 1
REPLAY_PACK_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-replay-pack-root-preimage"
)
REPLAY_VERIFICATION_FORMAT = "peano-hydra-library-replay-verification"
REPLAY_VERIFICATION_VERSION = 1
REPLAY_WORKER_ISOLATION_FORMAT = "peano-hydra-replay-worker-isolation"
REPLAY_WORKER_ISOLATION_VERSION = 1
CERTIFICATE_REPRESENTATION = "peano-lab-v2"
SOURCE_CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"
LOGIC_MODE = "intuitionistic"
PACK_STATUS = "candidate"
FORBIDDEN_REPLAY_IMPORT_PREFIXES = (
    "peano_lab.library",
    "peano_lab.engine",
    "peano_lab.ui",
    "training",
    "torch",
    "transformers",
)

SCHEMA_FILE = "schema.json"
MANIFEST_FILE = "manifest.json"
CATALOG_FILE = "catalog.json"
PROFILE_FILE = "semantic-profile.json"
CERTIFICATE_DIRECTORY = "certificates"

MAX_SCHEMA_BYTES = 1_000_000
MAX_MANIFEST_BYTES = 8_000_000
MAX_CATALOG_BYTES = 4_000_000
MAX_PROFILE_BYTES = 1_000_000
MAX_ARTIFACT_BYTES = 8_000_000
MAX_TOTAL_ARTIFACT_BYTES = 128_000_000
MAX_ARTIFACT_NODES = 1_000_000
MAX_ARTIFACT_DEPTH = 512
MAX_ARTIFACT_INTEGER_DIGITS = MAX_DECODE_INTEGER_DIGITS
MAX_THEOREMS = 10_000
MAX_JSON_DEPTH = 160
MAX_JSON_ITEMS = 2_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16

SEMANTIC_PROFILE_FORMAT = "peano-hydra-semantic-profile"
SEMANTIC_PROFILE_VERSION = 2
SEMANTIC_PROFILE_ID = "peano-lab-ha-intuitionistic-v2"
SEMANTIC_PROFILE_SHA256 = (
    "4f2713e6a21e6261bbefe5991ef545e6356807e7042c6b2c7c07183e142c3b4b"
)
SEMANTIC_PROFILE_DOCUMENT_SHA256 = (
    "e19162d0e78779d34e5e02166eeb109c5a75091b4692fe37577a7fa47ff29287"
)

CATALOG_SCHEMA = "peano-library-snapshot-v3"
_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_THEOREM_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,127}")

_SCHEMA_IDENTITY_FIELDS = frozenset(
    {"artifact_sha256", "format", "id", "sha256", "v"}
)
_MANIFEST_FIELDS = frozenset(
    {
        "aggregate",
        "certificate_representation",
        "evaluation_eligible",
        "format",
        "id",
        "kernel_identity",
        "logic_mode",
        "replay_root_sha256",
        "root_preimage",
        "root_sha256",
        "schema",
        "semantic_profile",
        "source_catalog",
        "status",
        "theorem_count",
        "theorems",
        "v",
    }
)
_ROOT_PREIMAGE_FIELDS = frozenset({"format", "payload", "v"})
_AGGREGATE_FIELDS = frozenset(
    {
        "artifact_bytes_maximum",
        "artifact_bytes_total",
        "cut_nodes_total",
        "proof_depth_maximum",
        "proof_nodes_maximum",
        "proof_nodes_total",
    }
)
_PROFILE_IDENTITY_FIELDS = frozenset(
    {
        "artifact_path",
        "artifact_sha256",
        "certificate_representation",
        "format",
        "id",
        "logic",
        "sha256",
        "v",
    }
)
_CATALOG_IDENTITY_FIELDS = frozenset(
    {
        "artifact_path",
        "artifact_sha256",
        "catalog_sha256",
        "ordered_root_sha256",
        "schema",
        "source_root_sha256",
        "theorem_count",
    }
)
_THEOREM_FIELDS = frozenset(
    {
        "artifact",
        "construction_metrics",
        "declared_dependencies",
        "formula_sha256",
        "index",
        "layer",
        "name",
        "packed_tree_metrics",
        "proof_term_sha256",
        "script",
        "script_sha256",
        "statement_canonical",
        "statement_canonical_sha256",
        "statement_source",
        "statement_source_sha256",
        "summary",
    }
)
_ARTIFACT_FIELDS = frozenset({"bytes", "fuel", "path", "sha256"})
_TREE_METRIC_FIELDS = frozenset({"cut_nodes", "proof_depth", "proof_nodes"})
_CONSTRUCTION_METRIC_FIELDS = frozenset(
    {
        "cut_nodes",
        "distinct_proof_objects",
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "reused_proof_references",
        "source_certificate_representation",
        "source_certificate_sha256",
    }
)
_KERNEL_IDENTITY_FIELDS = frozenset(
    {
        "artifact_decoder",
        "artifact_format",
        "checker",
        "context",
        "logic",
        "source_root_sha256",
        "sources",
    }
)
_KERNEL_SOURCE_FIELDS = frozenset({"path", "sha256"})
_KERNEL_SOURCE_PATHS = (
    "peano-lab/py/peano_lab/__init__.py",
    "peano-lab/py/peano_lab/kernel/__init__.py",
    "peano-lab/py/peano_lab/kernel/terms.py",
    "peano-lab/py/peano_lab/kernel/formulas.py",
    "peano-lab/py/peano_lab/kernel/subst.py",
    "peano-lab/py/peano_lab/kernel/proofs.py",
    "peano-lab/py/peano_lab/kernel/checker.py",
    "peano-lab/py/peano_lab/kernel/artifact_codec.py",
    "training/peano_hydra/library_replay_pack.py",
    "scripts/build_peano_hydra_replay_pack.py",
)
_CATALOG_FIELDS = frozenset(
    {
        "certificate_policy",
        "certificate_representation",
        "ordered_root_sha256",
        "schema",
        "theorem_count",
        "theorem_source_root_sha256",
        "theorem_sources",
        "theorems",
    }
)
_CATALOG_SOURCE_FIELDS = frozenset({"path", "sha256"})
_CATALOG_ROW_FIELDS = frozenset(
    {
        "certificate_representation",
        "certificate_sha256",
        "cut_nodes",
        "dependencies",
        "distinct_proof_objects",
        "index",
        "layer",
        "name",
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "reused_proof_references",
        "script",
        "script_sha256",
        "statement",
        "statement_sha256",
        "summary",
    }
)


class LibraryReplayPackError(ValueError):
    """A candidate replay pack is malformed, unbound, or kernel-rejected."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryReplayPackError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise LibraryReplayPackError(f"forbidden JSON constant {value!r}")


def _reject_float(value: str) -> object:
    raise LibraryReplayPackError(f"floating-point JSON value {value!r} is forbidden")


def _validate_json_value(
    value: object,
    *,
    depth: int = 0,
    active: set[int] | None = None,
    counter: list[int] | None = None,
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise LibraryReplayPackError("JSON exceeds the nesting limit")
    if active is None:
        active = set()
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_JSON_ITEMS:
        raise LibraryReplayPackError("JSON exceeds the item limit")
    if value is None or type(value) in (bool, str):
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_JSON_INTEGER:
            raise LibraryReplayPackError("JSON integer exceeds the safe domain")
        return
    if type(value) not in (list, dict):
        raise LibraryReplayPackError("value is outside strict JSON")
    identity = id(value)
    if identity in active:
        raise LibraryReplayPackError("cyclic JSON value is forbidden")
    active.add(identity)
    try:
        if type(value) is list:
            for item in value:
                _validate_json_value(
                    item, depth=depth + 1, active=active, counter=counter
                )
        else:
            for key, item in value.items():
                if type(key) is not str:
                    raise LibraryReplayPackError("JSON object key must be text")
                _validate_json_value(
                    item, depth=depth + 1, active=active, counter=counter
                )
    finally:
        active.remove(identity)


def canonical_json_bytes(value: object, *, limit: int = MAX_MANIFEST_BYTES) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json_value(value)
    try:
        raw = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryReplayPackError(f"value is not canonical JSON: {exc}") from None
    if len(raw) > limit:
        raise LibraryReplayPackError(f"canonical JSON exceeds the {limit}-byte limit")
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_MANIFEST_BYTES
) -> bytes:
    _validate_json_value(value)
    try:
        raw = (
            json.dumps(
                value,
                ensure_ascii=False,
                allow_nan=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryReplayPackError(f"value is not canonical JSON: {exc}") from None
    if len(raw) > limit:
        raise LibraryReplayPackError(
            f"canonical JSON document exceeds the {limit}-byte limit"
        )
    return raw


def _decode_json(raw: bytes, label: str) -> object:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except LibraryReplayPackError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryReplayPackError(f"{label} is not strict JSON: {exc}") from None


def _decode_canonical_document(raw: bytes, label: str, *, limit: int) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryReplayPackError(f"{label} must be bounded exact bytes")
    value = _decode_json(raw, label)
    if type(value) is not dict:
        raise LibraryReplayPackError(f"{label} must be one JSON object")
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryReplayPackError(f"{label} is not a canonical JSON document")
    return value


def _detached_object(value: object, label: str) -> dict[str, object]:
    try:
        raw = canonical_json_bytes(value)
    except LibraryReplayPackError as exc:
        raise LibraryReplayPackError(f"{label} is malformed: {exc}") from None
    result = _decode_json(raw, label)
    if type(result) is not dict:
        raise LibraryReplayPackError(f"{label} must be one JSON object")
    return result


def _require_fields(
    label: str, value: object, expected: frozenset[str]
) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        raise LibraryReplayPackError(f"{label} has missing or additional fields")
    return value


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryReplayPackError(f"{label} must be one lowercase SHA-256")
    return value


def _require_version(label: str, value: object, expected: int) -> int:
    if type(value) is not int or value != expected:
        raise LibraryReplayPackError(f"{label} must be integer {expected}")
    return value


def _nonnegative_integer(label: str, value: object) -> int:
    if type(value) is not int or not 0 <= value <= MAX_SAFE_JSON_INTEGER:
        raise LibraryReplayPackError(f"{label} must be a nonnegative exact integer")
    return value


def _positive_integer(label: str, value: object) -> int:
    result = _nonnegative_integer(label, value)
    if result < 1:
        raise LibraryReplayPackError(f"{label} must be positive")
    return result


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_MANIFEST_BYTES) -> str:
    return _sha256_bytes(canonical_json_bytes(value, limit=limit))


def _safe_artifact_path(index: int, name: str, digest: str) -> str:
    expected = f"{CERTIFICATE_DIRECTORY}/{index:04d}-{name}-{digest}.pl2"
    if len(expected.encode("utf-8")) > 512:
        raise LibraryReplayPackError("artifact path exceeds its byte limit")
    return expected


def validate_replay_pack_id(value: object) -> str:
    if type(value) is not str or _SAFE_ID_RE.fullmatch(value) is None:
        raise LibraryReplayPackError("library replay-pack id is malformed")
    return value


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("bounded file limit must be a positive exact integer")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryReplayPackError(f"cannot read {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LibraryReplayPackError(f"{label} must be a regular file")
        if before.st_size > limit:
            raise LibraryReplayPackError(f"{label} exceeds the {limit}-byte limit")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
        stable = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) == (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if not stable:
            raise LibraryReplayPackError(f"{label} changed while it was read")
        if len(raw) > limit or len(raw) != before.st_size:
            raise LibraryReplayPackError(f"{label} exceeds or disagrees with its size")
        return raw
    except OSError as exc:
        raise LibraryReplayPackError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def replay_pack_schema() -> dict[str, object]:
    raw = _read_bounded_regular_file(
        REPLAY_PACK_SCHEMA_PATH,
        label="library replay-pack schema",
        limit=MAX_SCHEMA_BYTES,
    )
    schema = _decode_canonical_document(
        raw, "library replay-pack schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        schema.get("format") != REPLAY_PACK_SCHEMA_FORMAT
        or schema.get("id") != REPLAY_PACK_SCHEMA_ID
    ):
        raise LibraryReplayPackError("library replay-pack schema identity is malformed")
    _require_version(
        "library replay-pack schema version",
        schema.get("v"),
        REPLAY_PACK_SCHEMA_VERSION,
    )
    if _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != REPLAY_PACK_SCHEMA_SHA256:
        raise LibraryReplayPackError("library replay-pack schema digest drifted")
    if schema.get("limits") != {
        "artifact_bytes_each": MAX_ARTIFACT_BYTES,
        "artifact_bytes_total": MAX_TOTAL_ARTIFACT_BYTES,
        "artifact_depth_each": MAX_ARTIFACT_DEPTH,
        "artifact_integer_digits_each": MAX_ARTIFACT_INTEGER_DIGITS,
        "artifact_nodes_each": MAX_ARTIFACT_NODES,
        "catalog_bytes": MAX_CATALOG_BYTES,
        "manifest_bytes": MAX_MANIFEST_BYTES,
        "manifest_json_depth": MAX_JSON_DEPTH,
        "manifest_json_items": MAX_JSON_ITEMS,
        "schema_bytes": MAX_SCHEMA_BYTES,
        "semantic_profile_bytes": MAX_PROFILE_BYTES,
        "theorem_count": MAX_THEOREMS,
    }:
        raise LibraryReplayPackError("library replay-pack schema limits drifted")
    return _detached_object(schema, "library replay-pack schema")


def replay_pack_schema_identity() -> dict[str, object]:
    schema = replay_pack_schema()
    raw = canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
    return {
        "artifact_sha256": _sha256_bytes(raw),
        "format": REPLAY_PACK_SCHEMA_FORMAT,
        "id": REPLAY_PACK_SCHEMA_ID,
        "sha256": REPLAY_PACK_SCHEMA_SHA256,
        "v": REPLAY_PACK_SCHEMA_VERSION,
    }


def live_kernel_identity() -> dict[str, object]:
    sources: list[dict[str, str]] = []
    for relative in _KERNEL_SOURCE_PATHS:
        raw = _read_bounded_regular_file(
            _REPOSITORY_ROOT / relative,
            label=f"kernel source {relative!r}",
            limit=MAX_SCHEMA_BYTES,
        )
        sources.append({"path": relative, "sha256": _sha256_bytes(raw)})
    return {
        "artifact_decoder": "peano_lab.kernel.artifact_codec.decode_artifact",
        "artifact_format": CERTIFICATE_REPRESENTATION,
        "checker": "peano_lab.kernel.checker.check",
        "context": "empty",
        "logic": LOGIC_MODE,
        "source_root_sha256": _sha256_json(sources, limit=MAX_SCHEMA_BYTES),
        "sources": sources,
    }


def _validate_kernel_identity(value: object) -> dict[str, object]:
    identity = _require_fields("kernel identity", value, _KERNEL_IDENTITY_FIELDS)
    constants = {
        "artifact_decoder": "peano_lab.kernel.artifact_codec.decode_artifact",
        "artifact_format": CERTIFICATE_REPRESENTATION,
        "checker": "peano_lab.kernel.checker.check",
        "context": "empty",
        "logic": LOGIC_MODE,
    }
    if any(identity.get(key) != expected for key, expected in constants.items()):
        raise LibraryReplayPackError("kernel identity constants are malformed")
    sources = identity.get("sources")
    if type(sources) is not list or len(sources) != len(_KERNEL_SOURCE_PATHS):
        raise LibraryReplayPackError("kernel source manifest is malformed")
    for expected_path, row in zip(_KERNEL_SOURCE_PATHS, sources, strict=True):
        source = _require_fields("kernel source", row, _KERNEL_SOURCE_FIELDS)
        if source.get("path") != expected_path:
            raise LibraryReplayPackError("kernel source path is malformed")
        _require_sha256("kernel source hash", source.get("sha256"))
    if identity.get("source_root_sha256") != _sha256_json(
        sources, limit=MAX_SCHEMA_BYTES
    ):
        raise LibraryReplayPackError("kernel source root is malformed")
    detached = _detached_object(identity, "kernel identity")
    if detached != _IMPORTED_KERNEL_IDENTITY or detached != live_kernel_identity():
        raise LibraryReplayPackError("packed kernel identity differs from live verifier")
    return detached


def _profile_identity_from_bytes(raw: bytes) -> tuple[dict[str, object], dict[str, object]]:
    profile = _decode_canonical_document(
        raw, "packed semantic profile", limit=MAX_PROFILE_BYTES
    )
    calculus = profile.get("calculus")
    authority = profile.get("authority")
    if (
        _sha256_bytes(raw) != SEMANTIC_PROFILE_DOCUMENT_SHA256
        or _sha256_json(profile, limit=MAX_PROFILE_BYTES) != SEMANTIC_PROFILE_SHA256
        or profile.get("format") != SEMANTIC_PROFILE_FORMAT
        or profile.get("id") != SEMANTIC_PROFILE_ID
    ):
        raise LibraryReplayPackError("packed semantic profile identity is malformed")
    _require_version(
        "packed semantic profile version",
        profile.get("v"),
        SEMANTIC_PROFILE_VERSION,
    )
    if (
        type(calculus) is not dict
        or calculus.get("classical") is not False
        or calculus.get("dne") is not False
        or type(authority) is not dict
        or authority.get("classical_checker") != "forbidden"
        or authority.get("certificate_representation")
        != CERTIFICATE_REPRESENTATION
    ):
        raise LibraryReplayPackError("classical material contaminated the packed profile")
    identity = {
        "artifact_path": PROFILE_FILE,
        "artifact_sha256": SEMANTIC_PROFILE_DOCUMENT_SHA256,
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "format": SEMANTIC_PROFILE_FORMAT,
        "id": SEMANTIC_PROFILE_ID,
        "logic": LOGIC_MODE,
        "sha256": SEMANTIC_PROFILE_SHA256,
        "v": SEMANTIC_PROFILE_VERSION,
    }
    return identity, profile


def _catalog_from_bytes(raw: bytes) -> tuple[dict[str, object], list[dict[str, object]]]:
    catalog = _decode_canonical_document(raw, "packed catalog", limit=MAX_CATALOG_BYTES)
    _require_fields("packed catalog", catalog, _CATALOG_FIELDS)
    if (
        catalog.get("schema") != CATALOG_SCHEMA
        or catalog.get("certificate_representation")
        != SOURCE_CERTIFICATE_REPRESENTATION
        or type(catalog.get("certificate_policy")) is not str
        or not catalog.get("certificate_policy")
    ):
        raise LibraryReplayPackError("packed catalog identity is malformed")
    sources = catalog.get("theorem_sources")
    if type(sources) is not list or not sources:
        raise LibraryReplayPackError("packed catalog source manifest is malformed")
    source_paths: set[str] = set()
    for row in sources:
        source = _require_fields("packed catalog source", row, _CATALOG_SOURCE_FIELDS)
        path = source.get("path")
        if (
            type(path) is not str
            or not path.startswith("peano-lab/py/peano_lab/library/")
            or not path.endswith(".py")
            or "\\" in path
            or Path(path).is_absolute()
            or "." in Path(path).parts
            or ".." in Path(path).parts
            or path in source_paths
        ):
            raise LibraryReplayPackError("packed catalog source path is malformed")
        _require_sha256("packed catalog source hash", source.get("sha256"))
        source_paths.add(path)
    source_root = _sha256_bytes(
        canonical_document_bytes(sources, limit=MAX_CATALOG_BYTES)
    )
    if catalog.get("theorem_source_root_sha256") != source_root:
        raise LibraryReplayPackError("packed catalog source root is malformed")
    rows_value = catalog.get("theorems")
    if (
        type(rows_value) is not list
        or not rows_value
        or len(rows_value) > MAX_THEOREMS
        or type(catalog.get("theorem_count")) is not int
        or catalog.get("theorem_count") != len(rows_value)
        or catalog.get("ordered_root_sha256")
        != _sha256_json(rows_value, limit=MAX_CATALOG_BYTES)
    ):
        raise LibraryReplayPackError("packed catalog theorem root is malformed")
    rows: list[dict[str, object]] = []
    known: set[str] = set()
    for index, row_value in enumerate(rows_value):
        row = _require_fields("packed catalog theorem", row_value, _CATALOG_ROW_FIELDS)
        name = row.get("name")
        dependencies = row.get("dependencies")
        script = row.get("script")
        if (
            type(name) is not str
            or _THEOREM_NAME_RE.fullmatch(name) is None
            or name in known
            or type(row.get("index")) is not int
            or row.get("index") != index
            or type(dependencies) is not list
            or len(dependencies) != len(set(dependencies))
            or not all(type(item) is str and item in known for item in dependencies)
            or type(script) is not list
            or not script
            or not all(type(item) is str and item for item in script)
        ):
            raise LibraryReplayPackError("packed catalog theorem order is malformed")
        statement = row.get("statement")
        summary = row.get("summary")
        if type(statement) is not str or not statement or type(summary) is not str:
            raise LibraryReplayPackError("packed catalog theorem text is malformed")
        if row.get("statement_sha256") != _sha256_bytes(statement.encode("utf-8")):
            raise LibraryReplayPackError("packed catalog statement hash is malformed")
        if row.get("script_sha256") != _sha256_bytes(
            ("\n".join(script) + "\n").encode("utf-8")
        ):
            raise LibraryReplayPackError("packed catalog script hash is malformed")
        if row.get("certificate_representation") != SOURCE_CERTIFICATE_REPRESENTATION:
            raise LibraryReplayPackError("packed catalog certificate type is malformed")
        _require_sha256("packed catalog certificate hash", row.get("certificate_sha256"))
        for key in ("proof_nodes", "proof_depth", "distinct_proof_objects"):
            _positive_integer(f"packed catalog {key}", row.get(key))
        for key in ("cut_nodes", "proof_edges", "reused_proof_references"):
            _nonnegative_integer(f"packed catalog {key}", row.get(key))
        if type(row.get("layer")) is not str or not row["layer"]:
            raise LibraryReplayPackError("packed catalog theorem layer is malformed")
        rows.append(_detached_object(row, "packed catalog theorem"))
        known.add(name)
    identity = {
        "artifact_path": CATALOG_FILE,
        "artifact_sha256": _sha256_bytes(raw),
        "catalog_sha256": _sha256_json(catalog, limit=MAX_CATALOG_BYTES),
        "ordered_root_sha256": catalog["ordered_root_sha256"],
        "schema": CATALOG_SCHEMA,
        "source_root_sha256": source_root,
        "theorem_count": len(rows),
    }
    return identity, rows


def proof_tree_metrics(proof: Proof) -> dict[str, int]:
    if not isinstance(proof, Proof):
        raise TypeError("proof_tree_metrics expects a kernel Proof")
    nodes = 0
    maximum_depth = 0
    cut_nodes = 0
    pending = [(proof, 1)]
    while pending:
        node, depth = pending.pop()
        nodes += 1
        maximum_depth = max(maximum_depth, depth)
        if type(node) is Cut:
            cut_nodes += 1
        pending.extend(
            (child, depth + 1)
            for field in fields(node)
            if isinstance((child := getattr(node, field.name)), Proof)
        )
    return {
        "cut_nodes": cut_nodes,
        "proof_depth": maximum_depth,
        "proof_nodes": nodes,
    }


def replay_observation(row: Mapping[str, object]) -> dict[str, object]:
    return {
        "artifact_sha256": row["artifact"]["sha256"],
        "formula_sha256": row["formula_sha256"],
        "index": row["index"],
        "kernel_accepted": True,
        "name": row["name"],
        "packed_tree_metrics": row["packed_tree_metrics"],
        "proof_term_sha256": row["proof_term_sha256"],
    }


def replay_root_sha256(rows: list[dict[str, object]]) -> str:
    return _sha256_json([replay_observation(row) for row in rows])


def with_manifest_root(body: Mapping[str, object]) -> dict[str, object]:
    detached = _detached_object(dict(body), "replay-pack manifest body")
    if "root_preimage" in detached or "root_sha256" in detached:
        raise LibraryReplayPackError("replay-pack root body is recursive")
    preimage = {
        "format": REPLAY_PACK_ROOT_PREIMAGE_FORMAT,
        "payload": detached,
        "v": REPLAY_PACK_VERSION,
    }
    return {
        **detached,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def validate_replay_pack_manifest(
    value: object,
) -> dict[str, object]:
    replay_pack_schema()
    manifest = _detached_object(value, "library replay-pack manifest")
    _require_fields("library replay-pack manifest", manifest, _MANIFEST_FIELDS)
    if (
        manifest.get("format") != REPLAY_PACK_FORMAT
        or manifest.get("logic_mode") != LOGIC_MODE
        or manifest.get("status") != PACK_STATUS
        or manifest.get("evaluation_eligible") is not False
        or manifest.get("certificate_representation")
        != CERTIFICATE_REPRESENTATION
    ):
        raise LibraryReplayPackError("library replay-pack constants are malformed")
    _require_version(
        "library replay-pack version", manifest.get("v"), REPLAY_PACK_VERSION
    )
    validate_replay_pack_id(manifest.get("id"))
    schema = _require_fields(
        "library replay-pack schema identity",
        manifest.get("schema"),
        _SCHEMA_IDENTITY_FIELDS,
    )
    _require_version(
        "library replay-pack schema version",
        schema.get("v"),
        REPLAY_PACK_SCHEMA_VERSION,
    )
    if schema != replay_pack_schema_identity():
        raise LibraryReplayPackError("library replay-pack schema identity drifted")
    profile = _require_fields(
        "library replay-pack semantic profile",
        manifest.get("semantic_profile"),
        _PROFILE_IDENTITY_FIELDS,
    )
    _require_version(
        "library replay-pack profile version",
        profile.get("v"),
        SEMANTIC_PROFILE_VERSION,
    )
    expected_profile = {
        "artifact_path": PROFILE_FILE,
        "artifact_sha256": SEMANTIC_PROFILE_DOCUMENT_SHA256,
        "certificate_representation": CERTIFICATE_REPRESENTATION,
        "format": SEMANTIC_PROFILE_FORMAT,
        "id": SEMANTIC_PROFILE_ID,
        "logic": LOGIC_MODE,
        "sha256": SEMANTIC_PROFILE_SHA256,
        "v": SEMANTIC_PROFILE_VERSION,
    }
    if profile != expected_profile:
        raise LibraryReplayPackError("library replay-pack profile identity is malformed")
    catalog = _require_fields(
        "library replay-pack catalog identity",
        manifest.get("source_catalog"),
        _CATALOG_IDENTITY_FIELDS,
    )
    catalog_count = _positive_integer(
        "library replay-pack catalog theorem count",
        catalog.get("theorem_count"),
    )
    if (
        catalog.get("artifact_path") != CATALOG_FILE
        or catalog.get("schema") != CATALOG_SCHEMA
    ):
        raise LibraryReplayPackError("library replay-pack catalog identity is malformed")
    for key in (
        "artifact_sha256",
        "catalog_sha256",
        "ordered_root_sha256",
        "source_root_sha256",
    ):
        _require_sha256(f"library replay-pack catalog {key}", catalog.get(key))
    kernel_identity = _validate_kernel_identity(manifest.get("kernel_identity"))
    count = _positive_integer("library replay-pack theorem count", manifest.get("theorem_count"))
    if count > MAX_THEOREMS or catalog_count != count:
        raise LibraryReplayPackError("library replay-pack theorem count is malformed")
    rows_value = manifest.get("theorems")
    if type(rows_value) is not list or len(rows_value) != count:
        raise LibraryReplayPackError("library replay-pack theorem rows are malformed")
    rows: list[dict[str, object]] = []
    known: set[str] = set()
    folded: set[str] = set()
    artifact_paths: set[str] = set()
    for index, row_value in enumerate(rows_value):
        row = _require_fields("library replay-pack theorem", row_value, _THEOREM_FIELDS)
        name = row.get("name")
        dependencies = row.get("declared_dependencies")
        script = row.get("script")
        if (
            type(name) is not str
            or _THEOREM_NAME_RE.fullmatch(name) is None
            or name in known
            or name.casefold() in folded
            or type(row.get("index")) is not int
            or row.get("index") != index
            or type(dependencies) is not list
            or len(dependencies) != len(set(dependencies))
            or not all(type(item) is str and item in known for item in dependencies)
            or type(script) is not list
            or not script
            or not all(type(item) is str and item for item in script)
        ):
            raise LibraryReplayPackError("library replay-pack theorem order is malformed")
        statement_source = row.get("statement_source")
        statement_canonical = row.get("statement_canonical")
        summary = row.get("summary")
        layer = row.get("layer")
        if not all(
            type(item) is str and item
            for item in (statement_source, statement_canonical, summary, layer)
        ):
            raise LibraryReplayPackError("library replay-pack theorem text is malformed")
        hashes = {
            "statement_source_sha256": statement_source.encode("utf-8"),
            "statement_canonical_sha256": statement_canonical.encode("utf-8"),
            "script_sha256": ("\n".join(script) + "\n").encode("utf-8"),
        }
        for key, preimage in hashes.items():
            if row.get(key) != _sha256_bytes(preimage):
                raise LibraryReplayPackError(f"library replay-pack {key} is malformed")
        _require_sha256("library replay-pack formula hash", row.get("formula_sha256"))
        _require_sha256("library replay-pack proof hash", row.get("proof_term_sha256"))
        tree = _require_fields(
            "library replay-pack tree metrics",
            row.get("packed_tree_metrics"),
            _TREE_METRIC_FIELDS,
        )
        construction = _require_fields(
            "library replay-pack construction metrics",
            row.get("construction_metrics"),
            _CONSTRUCTION_METRIC_FIELDS,
        )
        for key in ("proof_nodes", "proof_depth"):
            _positive_integer(f"library replay-pack tree {key}", tree.get(key))
            _positive_integer(
                f"library replay-pack construction {key}", construction.get(key)
            )
        _nonnegative_integer("library replay-pack tree cuts", tree.get("cut_nodes"))
        if (
            tree["proof_nodes"] > MAX_ARTIFACT_NODES
            or tree["proof_depth"] > MAX_ARTIFACT_DEPTH
            or tree["proof_depth"] > tree["proof_nodes"]
            or tree["cut_nodes"] > tree["proof_nodes"]
        ):
            raise LibraryReplayPackError(
                "library replay-pack tree metrics exceed their limits"
            )
        for key in (
            "cut_nodes",
            "proof_edges",
            "reused_proof_references",
        ):
            _nonnegative_integer(
                f"library replay-pack construction {key}", construction.get(key)
            )
        _positive_integer(
            "library replay-pack construction distinct objects",
            construction.get("distinct_proof_objects"),
        )
        if any(
            construction[key] != tree[key]
            for key in ("cut_nodes", "proof_depth", "proof_nodes")
        ):
            raise LibraryReplayPackError(
                "construction structural metrics differ from packed tree metrics"
            )
        distinct = construction["distinct_proof_objects"]
        edges = construction["proof_edges"]
        reused = construction["reused_proof_references"]
        if (
            distinct > tree["proof_nodes"]
            or edges < distinct - 1
            or edges > tree["proof_nodes"] - 1
            or reused != edges - (distinct - 1)
        ):
            raise LibraryReplayPackError(
                "construction object-sharing metrics violate their invariants"
            )
        if (
            construction.get("source_certificate_representation")
            != SOURCE_CERTIFICATE_REPRESENTATION
        ):
            raise LibraryReplayPackError("construction certificate type is malformed")
        _require_sha256(
            "construction certificate hash",
            construction.get("source_certificate_sha256"),
        )
        artifact = _require_fields(
            "library replay-pack artifact", row.get("artifact"), _ARTIFACT_FIELDS
        )
        artifact_bytes = _positive_integer(
            "library replay-pack artifact bytes", artifact.get("bytes")
        )
        if artifact_bytes > MAX_ARTIFACT_BYTES:
            raise LibraryReplayPackError("library replay-pack artifact is too large")
        artifact_hash = _require_sha256(
            "library replay-pack artifact hash", artifact.get("sha256")
        )
        expected_path = _safe_artifact_path(index, name, artifact_hash)
        if artifact.get("path") != expected_path or expected_path in artifact_paths:
            raise LibraryReplayPackError("library replay-pack artifact path is malformed")
        fuel = _positive_integer("library replay-pack artifact fuel", artifact.get("fuel"))
        if fuel != FUEL_MULTIPLIER * tree["proof_nodes"] + FUEL_OFFSET:
            raise LibraryReplayPackError("library replay-pack artifact fuel is malformed")
        rows.append(_detached_object(row, "library replay-pack theorem"))
        known.add(name)
        folded.add(name.casefold())
        artifact_paths.add(expected_path)
    aggregate = _require_fields(
        "library replay-pack aggregate", manifest.get("aggregate"), _AGGREGATE_FIELDS
    )
    expected_aggregate = {
        "artifact_bytes_maximum": max(row["artifact"]["bytes"] for row in rows),
        "artifact_bytes_total": sum(row["artifact"]["bytes"] for row in rows),
        "cut_nodes_total": sum(row["packed_tree_metrics"]["cut_nodes"] for row in rows),
        "proof_depth_maximum": max(row["packed_tree_metrics"]["proof_depth"] for row in rows),
        "proof_nodes_maximum": max(row["packed_tree_metrics"]["proof_nodes"] for row in rows),
        "proof_nodes_total": sum(row["packed_tree_metrics"]["proof_nodes"] for row in rows),
    }
    if aggregate != expected_aggregate:
        raise LibraryReplayPackError("library replay-pack aggregate is malformed")
    if expected_aggregate["artifact_bytes_total"] > MAX_TOTAL_ARTIFACT_BYTES:
        raise LibraryReplayPackError("library replay-pack exceeds its aggregate byte limit")
    replay_root = _require_sha256(
        "library replay-pack replay root", manifest.get("replay_root_sha256")
    )
    if replay_root != replay_root_sha256(rows):
        raise LibraryReplayPackError("library replay-pack replay root is malformed")
    preimage = _require_fields(
        "library replay-pack root preimage",
        manifest.get("root_preimage"),
        _ROOT_PREIMAGE_FIELDS,
    )
    if preimage.get("format") != REPLAY_PACK_ROOT_PREIMAGE_FORMAT:
        raise LibraryReplayPackError("library replay-pack root preimage is malformed")
    _require_version(
        "library replay-pack root-preimage version",
        preimage.get("v"),
        REPLAY_PACK_VERSION,
    )
    body = {
        key: item
        for key, item in manifest.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    if canonical_json_bytes(preimage.get("payload")) != canonical_json_bytes(body):
        raise LibraryReplayPackError("library replay-pack root payload is malformed")
    root = _require_sha256("library replay-pack root", manifest.get("root_sha256"))
    if root != _sha256_json(preimage):
        raise LibraryReplayPackError("library replay-pack root is malformed")
    validated = with_manifest_root(
        {
            **body,
            "aggregate": expected_aggregate,
            "kernel_identity": kernel_identity,
            "theorems": rows,
        }
    )
    if validated["root_sha256"] != root:
        raise LibraryReplayPackError("library replay-pack validation changed its root")
    return validated


def _validate_manifest_sources(
    manifest: dict[str, object], *, catalog_raw: bytes, profile_raw: bytes
) -> list[dict[str, object]]:
    profile_identity, _ = _profile_identity_from_bytes(profile_raw)
    if profile_identity != manifest["semantic_profile"]:
        raise LibraryReplayPackError("packed profile differs from manifest")
    catalog_identity, catalog_rows = _catalog_from_bytes(catalog_raw)
    if catalog_identity != manifest["source_catalog"]:
        raise LibraryReplayPackError("packed catalog differs from manifest")
    if len(catalog_rows) != len(manifest["theorems"]):
        raise LibraryReplayPackError("packed catalog and replay rows differ in count")
    for packed, catalog in zip(manifest["theorems"], catalog_rows, strict=True):
        construction = packed["construction_metrics"]
        expected = {
            "declared_dependencies": catalog["dependencies"],
            "index": catalog["index"],
            "layer": catalog["layer"],
            "name": catalog["name"],
            "script": catalog["script"],
            "script_sha256": catalog["script_sha256"],
            "statement_source": catalog["statement"],
            "statement_source_sha256": catalog["statement_sha256"],
            "summary": catalog["summary"],
        }
        if any(packed.get(key) != value for key, value in expected.items()):
            raise LibraryReplayPackError("replay row differs from packed catalog")
        expected_construction = {
            "cut_nodes": catalog["cut_nodes"],
            "distinct_proof_objects": catalog["distinct_proof_objects"],
            "proof_depth": catalog["proof_depth"],
            "proof_edges": catalog["proof_edges"],
            "proof_nodes": catalog["proof_nodes"],
            "reused_proof_references": catalog["reused_proof_references"],
            "source_certificate_representation": catalog[
                "certificate_representation"
            ],
            "source_certificate_sha256": catalog["certificate_sha256"],
        }
        if construction != expected_construction:
            raise LibraryReplayPackError("construction metrics differ from packed catalog")
    return catalog_rows


def _verify_artifact_row(row: dict[str, object], raw: bytes) -> dict[str, object]:
    artifact = row["artifact"]
    if type(raw) is not bytes or len(raw) != artifact["bytes"]:
        raise LibraryReplayPackError(f"artifact bytes for {row['name']!r} are malformed")
    if _sha256_bytes(raw) != artifact["sha256"]:
        raise LibraryReplayPackError(f"artifact hash for {row['name']!r} is malformed")
    try:
        fuel, target, proof = decode_artifact(
            raw,
            max_bytes=MAX_ARTIFACT_BYTES,
            max_nodes=MAX_ARTIFACT_NODES,
            max_depth=MAX_ARTIFACT_DEPTH,
        )
    except ArtifactDecodeError as exc:
        raise LibraryReplayPackError(
            f"artifact for {row['name']!r} cannot be decoded: {exc}"
        ) from None
    metrics = proof_tree_metrics(proof)
    if metrics != row["packed_tree_metrics"]:
        raise LibraryReplayPackError(f"artifact metrics for {row['name']!r} drifted")
    if fuel != artifact["fuel"] or fuel != FUEL_MULTIPLIER * metrics["proof_nodes"] + FUEL_OFFSET:
        raise LibraryReplayPackError(f"artifact fuel for {row['name']!r} drifted")
    try:
        parsed, free_names = parse_formula_with_names(row["statement_source"])
    except (TypeError, ValueError, RecursionError) as exc:
        raise LibraryReplayPackError(
            f"statement for {row['name']!r} cannot be parsed: {exc}"
        ) from None
    if free_names or parsed != target:
        raise LibraryReplayPackError(
            f"artifact target for {row['name']!r} differs from its closed statement"
        )
    formula_hash = _sha256_bytes(encode_formula(target))
    proof_hash = _sha256_bytes(encode_proof(proof))
    canonical_statement = pretty_formula(target, [])
    if (
        formula_hash != row["formula_sha256"]
        or proof_hash != row["proof_term_sha256"]
        or canonical_statement != row["statement_canonical"]
        or _sha256_bytes(canonical_statement.encode("utf-8"))
        != row["statement_canonical_sha256"]
    ):
        raise LibraryReplayPackError(
            f"artifact structural identity for {row['name']!r} drifted"
        )
    if not check((), proof, target):
        raise LibraryReplayPackError(
            f"independent kernel rejected packed theorem {row['name']!r}"
        )
    return replay_observation(row)


def _verification_report(
    manifest: dict[str, object], observations: list[dict[str, object]]
) -> dict[str, object]:
    replay_root = _sha256_json(observations)
    if replay_root != manifest["replay_root_sha256"]:
        raise LibraryReplayPackError("fresh replay observations differ from manifest")
    return {
        "artifact_bytes_total": manifest["aggregate"]["artifact_bytes_total"],
        "format": REPLAY_VERIFICATION_FORMAT,
        "kernel_checked_count": len(observations),
        "logic_mode": LOGIC_MODE,
        "manifest_root_sha256": manifest["root_sha256"],
        "replay_root_sha256": replay_root,
        "status": "passed",
        "theorem_count": len(observations),
        "v": REPLAY_VERIFICATION_VERSION,
    }


def verify_replay_pack_files(
    manifest_value: object,
    *,
    schema_raw: bytes,
    catalog_raw: bytes,
    profile_raw: bytes,
    artifact_files: Mapping[str, bytes],
) -> dict[str, object]:
    """Verify an in-memory pack mapping; intended for bounded tests and adapters."""

    manifest = validate_replay_pack_manifest(manifest_value)
    if schema_raw != canonical_document_bytes(replay_pack_schema(), limit=MAX_SCHEMA_BYTES):
        raise LibraryReplayPackError("packed schema copy differs from verifier schema")
    _validate_manifest_sources(
        manifest, catalog_raw=catalog_raw, profile_raw=profile_raw
    )
    expected_paths = {row["artifact"]["path"] for row in manifest["theorems"]}
    if type(artifact_files) is not dict and not isinstance(artifact_files, Mapping):
        raise LibraryReplayPackError("artifact files must be one mapping")
    supplied = dict(artifact_files)
    if set(supplied) != expected_paths or not all(
        type(path) is str and type(raw) is bytes for path, raw in supplied.items()
    ):
        raise LibraryReplayPackError("artifact file mapping differs from manifest")
    observations = [
        _verify_artifact_row(row, supplied[row["artifact"]["path"]])
        for row in manifest["theorems"]
    ]
    return _verification_report(manifest, observations)


def _validated_pack_root(root: Path) -> Path:
    if not isinstance(root, Path):
        raise TypeError("replay pack root must be a pathlib.Path")
    root = Path(root)
    try:
        metadata = root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryReplayPackError("replay pack root must be a non-symlink directory")
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise LibraryReplayPackError("cannot resolve replay pack root") from exc
    return resolved


def _bounded_directory_entries(
    path: Path,
    *,
    label: str,
    maximum: int,
) -> dict[str, tuple[bool, bool]]:
    if type(maximum) is not int or maximum < 1:
        raise TypeError("directory-entry limit must be a positive exact integer")
    result: dict[str, tuple[bool, bool]] = {}
    try:
        with os.scandir(path) as entries:
            for entry in entries:
                if entry.name in result:
                    raise LibraryReplayPackError(
                        f"{label} contains a duplicate directory entry"
                    )
                if len(result) >= maximum:
                    raise LibraryReplayPackError(
                        f"{label} exceeds its {maximum}-entry limit"
                    )
                result[entry.name] = (
                    entry.is_file(follow_symlinks=False),
                    entry.is_dir(follow_symlinks=False),
                )
    except LibraryReplayPackError:
        raise
    except OSError as exc:
        raise LibraryReplayPackError(f"cannot enumerate {label}") from exc
    return result


def _validate_exact_pack_files(root: Path, artifact_paths: set[str]) -> None:
    expected_root_files = {CATALOG_FILE, MANIFEST_FILE, PROFILE_FILE, SCHEMA_FILE}
    root_entries = _bounded_directory_entries(
        root,
        label="replay pack root",
        maximum=len(expected_root_files) + 1,
    )
    if set(root_entries) != expected_root_files | {CERTIFICATE_DIRECTORY}:
        raise LibraryReplayPackError("replay pack root contains missing or extra files")
    for name in expected_root_files:
        if not root_entries[name][0]:
            raise LibraryReplayPackError(f"replay pack {name!r} is not a regular file")
    if not root_entries[CERTIFICATE_DIRECTORY][1]:
        raise LibraryReplayPackError("replay pack certificate directory is invalid")
    certificate_root = root / CERTIFICATE_DIRECTORY
    certificate_entries = _bounded_directory_entries(
        certificate_root,
        label="replay pack certificates",
        maximum=len(artifact_paths),
    )
    expected_names = {Path(path).name for path in artifact_paths}
    if set(certificate_entries) != expected_names or not all(
        kind[0] for kind in certificate_entries.values()
    ):
        raise LibraryReplayPackError(
            "replay pack certificate directory differs from manifest"
        )


def load_and_verify_replay_pack(
    root: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    """Load and stream-verify one exact directory pack without living-library imports."""

    pack_root = _validated_pack_root(root)
    manifest_raw = _read_bounded_regular_file(
        pack_root / MANIFEST_FILE,
        label="replay-pack manifest",
        limit=MAX_MANIFEST_BYTES,
    )
    manifest_value = _decode_canonical_document(
        manifest_raw, "replay-pack manifest", limit=MAX_MANIFEST_BYTES
    )
    # Validate all row counts, paths, declared byte totals, and roots before
    # performing even one theorem-artifact read.
    manifest = validate_replay_pack_manifest(manifest_value)
    artifact_paths = {row["artifact"]["path"] for row in manifest["theorems"]}
    _validate_exact_pack_files(pack_root, artifact_paths)
    schema_raw = _read_bounded_regular_file(
        pack_root / SCHEMA_FILE,
        label="replay-pack schema copy",
        limit=MAX_SCHEMA_BYTES,
    )
    if schema_raw != canonical_document_bytes(replay_pack_schema(), limit=MAX_SCHEMA_BYTES):
        raise LibraryReplayPackError("packed schema copy differs from verifier schema")
    catalog_raw = _read_bounded_regular_file(
        pack_root / CATALOG_FILE,
        label="replay-pack catalog",
        limit=MAX_CATALOG_BYTES,
    )
    profile_raw = _read_bounded_regular_file(
        pack_root / PROFILE_FILE,
        label="replay-pack semantic profile",
        limit=MAX_PROFILE_BYTES,
    )
    _validate_manifest_sources(
        manifest, catalog_raw=catalog_raw, profile_raw=profile_raw
    )
    observations: list[dict[str, object]] = []
    for row in manifest["theorems"]:
        path = pack_root / row["artifact"]["path"]
        raw = _read_bounded_regular_file(
            path,
            label=f"replay-pack artifact {row['name']!r}",
            limit=MAX_ARTIFACT_BYTES,
        )
        observations.append(_verify_artifact_row(row, raw))
    _validate_exact_pack_files(pack_root, artifact_paths)
    if manifest["kernel_identity"] != _IMPORTED_KERNEL_IDENTITY:
        raise LibraryReplayPackError("verifier identity changed during replay")
    if manifest["kernel_identity"] != live_kernel_identity():
        raise LibraryReplayPackError("verifier sources changed during replay")
    return manifest, _verification_report(manifest, observations)


# Capture the source identity immediately after this isolated verifier module
# has been imported.  Every authoritative replay compares the packed identity
# both with this import-time snapshot and with a fresh post-replay snapshot.
_IMPORTED_KERNEL_IDENTITY = live_kernel_identity()


__all__ = [
    "CATALOG_FILE",
    "CERTIFICATE_DIRECTORY",
    "CERTIFICATE_REPRESENTATION",
    "FUEL_MULTIPLIER",
    "FUEL_OFFSET",
    "FORBIDDEN_REPLAY_IMPORT_PREFIXES",
    "LibraryReplayPackError",
    "LOGIC_MODE",
    "MANIFEST_FILE",
    "MAX_ARTIFACT_BYTES",
    "MAX_ARTIFACT_DEPTH",
    "MAX_ARTIFACT_INTEGER_DIGITS",
    "MAX_ARTIFACT_NODES",
    "MAX_CATALOG_BYTES",
    "MAX_MANIFEST_BYTES",
    "MAX_PROFILE_BYTES",
    "MAX_SCHEMA_BYTES",
    "MAX_THEOREMS",
    "MAX_TOTAL_ARTIFACT_BYTES",
    "PACK_STATUS",
    "PROFILE_FILE",
    "REPLAY_PACK_FORMAT",
    "REPLAY_PACK_ROOT_PREIMAGE_FORMAT",
    "REPLAY_PACK_SCHEMA_FORMAT",
    "REPLAY_PACK_SCHEMA_ID",
    "REPLAY_PACK_SCHEMA_PATH",
    "REPLAY_PACK_SCHEMA_SHA256",
    "REPLAY_PACK_SCHEMA_VERSION",
    "REPLAY_PACK_VERSION",
    "REPLAY_VERIFICATION_FORMAT",
    "REPLAY_VERIFICATION_VERSION",
    "REPLAY_WORKER_ISOLATION_FORMAT",
    "REPLAY_WORKER_ISOLATION_VERSION",
    "SCHEMA_FILE",
    "SEMANTIC_PROFILE_DOCUMENT_SHA256",
    "SEMANTIC_PROFILE_FORMAT",
    "SEMANTIC_PROFILE_ID",
    "SEMANTIC_PROFILE_SHA256",
    "SEMANTIC_PROFILE_VERSION",
    "SOURCE_CERTIFICATE_REPRESENTATION",
    "canonical_document_bytes",
    "canonical_json_bytes",
    "live_kernel_identity",
    "load_and_verify_replay_pack",
    "proof_tree_metrics",
    "replay_observation",
    "replay_pack_schema",
    "replay_pack_schema_identity",
    "replay_root_sha256",
    "validate_replay_pack_manifest",
    "validate_replay_pack_id",
    "verify_replay_pack_files",
    "with_manifest_root",
]
