"""Bounded, non-recursive transport for the additive Alpha-v31 catalogue.

The manifest references exactly two data documents: the literal, unmodified
v30 parent and one same-directory v31 delta.  Each of the three files remains
subject to the existing 64 MiB catalogue limit.  No combined oversized JSON
file is written or accepted, and no older parent reference is followed.

These functions authenticate *transport*, not mathematics.  In particular,
``checked_use`` and proof receipts in a returned dictionary remain claims for
the independent release verifier to check with the original HA/Lean gates.
Neither a digest, this loader, nor its stat-only cache key can admit a theorem.
There are intentionally no proof-library imports or process-wide caches here.
"""

from __future__ import annotations

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import stat
from typing import Iterator


TRANSPORT_SCHEMA = "peano-library-alpha-shards-v31"
LOGICAL_SCHEMA = "peano-library-alpha-snapshot-v31"
DELTA_SCHEMA = "peano-library-alpha-delta-v31"
PARENT_SCHEMA = "peano-library-alpha-snapshot-v30"
PARENT_BASENAME = "catalog-v30.json"
DELTA_BASENAME = "catalog-v31-delta.json"
PARENT_BYTES = 66_503_303
PARENT_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
PARENT_ROW_COUNT = 3_222
DELTA_ROW_COUNT = 574
ROW_COUNT = PARENT_ROW_COUNT + DELTA_ROW_COUNT
STABLE_COUNT = 432
MAX_REFERENCED_DOCUMENTS = 2
MAX_CATALOG_BYTES = 64 * 1024 * 1024
# These are the existing proof-bundle topology budgets, not enlarged limits.
MAX_ROWS = 4_096
MAX_DEPENDENCIES_PER_ROW = 256
MAX_EDGES = 65_536
MAX_JSON_CONTAINERS = MAX_EDGES
MAX_JSON_DEPTH = 256
MAX_JSON_VALUES = 5_000_000
READ_CHUNK_BYTES = 1024 * 1024
DEFAULT_PARENT = Path(__file__).absolute().parents[1] / "artifacts/peano-library/alpha" / PARENT_BASENAME

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']*\Z")
# This lexer is only an allocation preflight. json.loads remains the actual
# syntax decoder, including escape validation and duplicate-key rejection.
_JSON_TOKEN = re.compile(rb'"[^"\\]*(?:\\.[^"\\]*)*"|[{}\[\],:]|[^"\s{}\[\],:]+')
_BINDING_FIELDS = frozenset(("path", "bytes", "sha256", "schema", "row_count"))
_CURRENT_FIELDS = frozenset((
    "alpha_only_count", "canonical_order", "checked_use_count", "edge_count",
    "edition_identity_sha256", "enrollment_origin_counts", "evidence_counts",
    "evidence_documents", "evidence_root_sha256", "layer_count",
    "membership_counts", "membership_root_sha256", "ordered_enrollment_root_sha256",
    "ordered_spec_root_sha256", "schema", "stable_count", "theorem_count",
))
_NEW_FIELDS = frozenset((
    "alpha_v31_completed_lower_promotion", "frontier_v31_campaign_counts",
    "frontier_v31_ordered_names_sha256", "parent_alpha_v30",
))
_IDENTITY_FIELDS = (
    "edition_identity_sha256", "evidence_root_sha256", "membership_root_sha256",
    "ordered_enrollment_root_sha256", "ordered_spec_root_sha256",
    "frontier_v31_ordered_names_sha256",
)


class CatalogError(ValueError):
    """Invalid, unbound, unsafe, oversized, or inconsistent catalogue data."""


@dataclass(frozen=True, slots=True)
class FileFingerprint:
    path: str
    device: int
    inode: int
    mode: int
    uid: int
    size: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True, slots=True)
class CatalogFileBinding:
    role: str
    path: Path
    bytes: int
    sha256: str
    schema: str
    row_count: int
    fingerprint: FileFingerprint


@dataclass(frozen=True, slots=True)
class CatalogBindings:
    """Three freshly byte-authenticated files; NOT a proof-checking receipt."""

    manifest: CatalogFileBinding
    parent: CatalogFileBinding
    delta: CatalogFileBinding

    @property
    def files(self) -> tuple[CatalogFileBinding, ...]:
        return self.manifest, self.parent, self.delta

    @property
    def fingerprint(self) -> tuple[FileFingerprint, ...]:
        return tuple(item.fingerprint for item in self.files)


def _integer(value: object, label: str, *, minimum: int = 0, maximum: int | None = None) -> int:
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        raise CatalogError(f"{label} must be an exact bounded integer")
    return value


def _digest(value: object, label: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise CatalogError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _owner(owner_uid: int | None) -> int:
    return os.getuid() if owner_uid is None else _integer(owner_uid, "owner_uid")


def _absolute_path(path: Path | str) -> Path:
    if not isinstance(path, (str, Path)):
        raise CatalogError("catalogue path must be a filesystem path")
    raw = os.fspath(path)
    if (not raw or any(char in raw for char in ("\x00", "\\", "*", "?", "[", "]", ":"))
            or ".." in raw.split("/")):
        raise CatalogError("catalogue paths may not contain URLs, globs, or traversal")
    # Do not resolve(): it would conceal a symlink before the no-follow walk.
    return Path(os.path.abspath(raw))


def _fingerprint(path: Path, info: os.stat_result) -> FileFingerprint:
    return FileFingerprint(str(path), info.st_dev, info.st_ino, info.st_mode,
                           info.st_uid, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


@contextmanager
def _opened(path: Path, owner_uid: int, expected_bytes: int | None = None) -> Iterator[tuple[int, FileFingerprint]]:
    """Open every component without following links; reject FIFOs before reads."""
    directory_fd = file_fd = None
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
        directory_fd = os.open(path.anchor, flags | os.O_DIRECTORY)
        for component in path.parts[1:-1]:
            next_fd = os.open(component, flags | os.O_DIRECTORY, dir_fd=directory_fd)
            os.close(directory_fd)
            directory_fd = next_fd
        file_fd = os.open(path.name, flags | os.O_NONBLOCK, dir_fd=directory_fd)
        info = os.fstat(file_fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != owner_uid:
            raise CatalogError(f"catalogue file has unsafe type or owner: {path}")
        if not 0 < info.st_size <= MAX_CATALOG_BYTES:
            raise CatalogError(f"catalogue file exceeds the unchanged 64 MiB bound or is empty: {path}")
        if expected_bytes is not None and info.st_size != expected_bytes:
            raise CatalogError(f"catalogue file size differs from its binding: {path}")
        yield file_fd, _fingerprint(path, info)
    except OSError as error:
        raise CatalogError(f"cannot safely open/read catalogue file {path}: {error}") from error
    finally:
        if file_fd is not None:
            os.close(file_fd)
        if directory_fd is not None:
            os.close(directory_fd)


def _stat_file(path: Path, owner_uid: int, expected_bytes: int | None = None) -> FileFingerprint:
    with _opened(path, owner_uid, expected_bytes) as (_fd, fingerprint):
        return fingerprint


def _read_file(path: Path, *, owner_uid: int, expected_sha256: str,
               expected_bytes: int | None = None, capture: bool = True) -> tuple[bytes | None, FileFingerprint]:
    """Size-first bounded read; hash-only callers never retain parent/delta bytes."""
    digest = _digest(expected_sha256, "expected file digest")
    chunks = [] if capture else None
    hasher = sha256()
    with _opened(path, owner_uid, expected_bytes) as (fd, before):
        observed = 0
        while True:
            # At most one byte beyond the *initial exact size*, not an unbounded
            # read followed by a check. A growing file fails before a large copy.
            block = os.read(fd, min(READ_CHUNK_BYTES, before.size + 1 - observed))
            if not block:
                break
            observed += len(block)
            if observed > before.size:
                raise CatalogError(f"catalogue file grew during its bounded read: {path}")
            hasher.update(block)
            if chunks is not None:
                chunks.append(block)
        if observed != before.size or _fingerprint(path, os.fstat(fd)) != before:
            raise CatalogError(f"catalogue file changed during its read: {path}")
        if hasher.hexdigest() != digest:
            raise CatalogError(f"catalogue file SHA-256 differs from its binding: {path}")
    if _stat_file(path, owner_uid, before.size) != before:
        raise CatalogError(f"catalogue path changed during its read: {path}")
    return (b"".join(chunks) if chunks is not None else None), before


def _object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError(f"duplicate JSON object key: {key!r}")
        result[key] = value
    return result


def _constant(value: str) -> None:
    raise CatalogError(f"non-finite JSON number: {value}")


def _float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        _constant(value)
    return result


def _preflight_json(payload: bytes, label: str) -> None:
    """Bound decoded container/value allocation *before* constructing objects.

    The limits reuse the existing edge, depth, and total-body-node budgets.
    The literal v30 parent has 45,407 containers and maximum JSON depth five.
    Quoted formulas/scripts are single tokens, not parsed as JSON structure.
    """
    stack = []
    containers = values = 0
    for token in _JSON_TOKEN.finditer(payload):
        first = payload[token.start()]
        if first in (ord("{"), ord("[")):
            containers += 1
            stack.append(first)
            if containers > MAX_JSON_CONTAINERS or len(stack) > MAX_JSON_DEPTH:
                raise CatalogError(f"{label} exceeds the existing JSON container/depth allocation budget")
        elif first in (ord("}"), ord("]")):
            opening = ord("{") if first == ord("}") else ord("[")
            if not stack or stack.pop() != opening:
                raise CatalogError(f"{label} has mismatched JSON containers")
        if first not in (ord("}"), ord("]"), ord(","), ord(":")):
            values += 1
            if values > MAX_JSON_VALUES:
                raise CatalogError(f"{label} exceeds the existing JSON value allocation budget")
    if stack:
        raise CatalogError(f"{label} has an unclosed JSON container")


def _decode(payload: bytes, label: str) -> dict:
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_CATALOG_BYTES:
        raise CatalogError(f"{label} is not bounded literal bytes")
    _preflight_json(payload, label)
    try:
        result = json.loads(payload.decode("utf-8"), object_pairs_hook=_object,
                            parse_constant=_constant, parse_float=_float)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise CatalogError(f"invalid {label} JSON: {error}") from error
    if type(result) is not dict:
        raise CatalogError(f"{label} must be a JSON object")
    return result


def _json_bytes(value: object) -> bytes:
    """Canonical output with a bound during encoding, not only after joining."""
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                               separators=(",", ":"))
    chunks = []
    size = 1  # The canonical trailing newline is part of the binding.
    try:
        for chunk in encoder.iterencode(value):
            encoded = chunk.encode("utf-8")
            size += len(encoded)
            if size > MAX_CATALOG_BYTES:
                raise CatalogError("encoded catalogue document exceeds the unchanged 64 MiB bound")
            chunks.append(encoded)
    except (TypeError, ValueError, RecursionError, UnicodeError) as error:
        raise CatalogError(f"invalid or oversized catalogue JSON value: {error}") from error
    return b"".join(chunks) + b"\n"


def _same(left: object, right: object) -> bool:
    # JSON byte equality retains nested integer/boolean distinctions which
    # ordinary Python dictionary equality would silently erase.
    return _json_bytes(left) == _json_bytes(right)


def _parent_binding() -> dict:
    return {"path": PARENT_BASENAME, "bytes": PARENT_BYTES, "sha256": PARENT_SHA256,
            "schema": PARENT_SCHEMA, "row_count": PARENT_ROW_COUNT}


def _validate_binding(value: object, *, parent: bool) -> dict:
    if type(value) is not dict or set(value) != _BINDING_FIELDS:
        raise CatalogError("catalogue binding must have the exact five fields")
    expected_name = PARENT_BASENAME if parent else DELTA_BASENAME
    expected_schema = PARENT_SCHEMA if parent else DELTA_SCHEMA
    expected_count = PARENT_ROW_COUNT if parent else DELTA_ROW_COUNT
    if value["path"] != expected_name or type(value["path"]) is not str:
        raise CatalogError("only the fixed same-directory parent and delta basenames are allowed")
    if type(value["schema"]) is not str or value["schema"] != expected_schema:
        raise CatalogError("catalogue binding schema is not the exact non-recursive v31 contract")
    if _integer(value["row_count"], "binding row_count", maximum=MAX_ROWS) != expected_count:
        raise CatalogError("catalogue binding row count changed")
    _integer(value["bytes"], "binding bytes", minimum=1, maximum=MAX_CATALOG_BYTES)
    _digest(value["sha256"], "binding sha256")
    if parent and not _same(value, _parent_binding()):
        raise CatalogError("the literal immutable v30 parent binding changed")
    return value


def _counts(value: object, label: str) -> dict:
    if type(value) is not dict or not value or len(value) > MAX_ROWS:
        raise CatalogError(f"{label} must be a nonempty bounded count object")
    for key, number in value.items():
        if type(key) is not str or not key:
            raise CatalogError(f"{label} contains an invalid key")
        _integer(number, label, maximum=MAX_ROWS)
    if sum(value.values()) > MAX_ROWS:
        raise CatalogError(f"{label} exceeds the existing row budget")
    return value


def _metadata_header(metadata: object) -> dict:
    if (type(metadata) is not dict or "theorems" in metadata
            or not (_CURRENT_FIELDS | _NEW_FIELDS) <= set(metadata)):
        raise CatalogError("manifest metadata must contain the complete logical metadata without theorem rows")
    if metadata["schema"] != LOGICAL_SCHEMA:
        raise CatalogError("manifest logical schema is not Alpha v31")
    for key, expected in (("theorem_count", ROW_COUNT), ("checked_use_count", ROW_COUNT),
                          ("stable_count", STABLE_COUNT), ("alpha_only_count", ROW_COUNT - STABLE_COUNT)):
        if _integer(metadata[key], key, maximum=MAX_ROWS) != expected:
            raise CatalogError(f"exact v31 metadata count changed: {key}")
    _integer(metadata["edge_count"], "edge_count", maximum=MAX_EDGES)
    _integer(metadata["layer_count"], "layer_count", minimum=1, maximum=MAX_ROWS)
    for key in _IDENTITY_FIELDS:
        _digest(metadata[key], key)
    for key in ("membership_counts", "evidence_counts", "enrollment_origin_counts", "frontier_v31_campaign_counts"):
        _counts(metadata[key], key)
    for key in ("alpha_v31_completed_lower_promotion", "parent_alpha_v30"):
        if type(metadata[key]) is not dict or not metadata[key]:
            raise CatalogError(f"new v31 metadata object is absent: {key}")
    return metadata


def _manifest(path: Path | str, expected_sha256: str, owner_uid: int | None) -> tuple[dict, CatalogBindings, int]:
    path = _absolute_path(path)
    owner = _owner(owner_uid)
    raw, fingerprint = _read_file(path, owner_uid=owner, expected_sha256=expected_sha256)
    value = _decode(raw, "v31 manifest")
    if set(value) != {"schema", "metadata", "parent", "delta"} or value["schema"] != TRANSPORT_SCHEMA:
        raise CatalogError("catalogue must use the exact v31 manifest and exactly two data bindings")
    _metadata_header(value["metadata"])
    parent = _validate_binding(value["parent"], parent=True)
    delta = _validate_binding(value["delta"], parent=False)
    files = [CatalogFileBinding("manifest", path, fingerprint.size, expected_sha256,
                                TRANSPORT_SCHEMA, ROW_COUNT, fingerprint)]
    for role, binding in (("parent", parent), ("delta", delta)):
        target = path.parent / binding["path"]
        info = _stat_file(target, owner, binding["bytes"])
        files.append(CatalogFileBinding(role, target, binding["bytes"], binding["sha256"],
                                        binding["schema"], binding["row_count"], info))
    if len({(item.fingerprint.device, item.fingerprint.inode) for item in files}) != 3:
        raise CatalogError("manifest, parent and delta must be distinct files, not hard-linked aliases")
    return value, CatalogBindings(*files), owner


def _unchanged(bindings: CatalogBindings, owner_uid: int) -> None:
    for item in bindings.files:
        if _stat_file(item.path, owner_uid, item.bytes) != item.fingerprint:
            raise CatalogError(f"catalogue input changed before completion: {item.role}")


def catalog_input_fingerprint(path: Path | str, *, expected_sha256: str,
                              owner_uid: int | None = None) -> tuple[FileFingerprint, ...]:
    """Cache key covering all three files; NOT hash/proof authorization.

    The small manifest is authenticated and structurally validated to obtain
    the exact bindings. Parent/delta are only safely statted here. A cache miss
    must call ``verify_catalog_bindings`` (or the stronger ``load_catalog``).
    """
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    _unchanged(bindings, owner)
    return bindings.fingerprint


def verify_catalog_bindings(path: Path | str, *, expected_sha256: str,
                            owner_uid: int | None = None) -> CatalogBindings:
    """Authenticate all literal files without parsing parent/delta or proofs."""
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    for item in (bindings.parent, bindings.delta):
        _raw, fingerprint = _read_file(item.path, owner_uid=owner, expected_bytes=item.bytes,
                                       expected_sha256=item.sha256, capture=False)
        if fingerprint != item.fingerprint:
            raise CatalogError(f"catalogue file changed after its binding was read: {item.role}")
    _unchanged(bindings, owner)
    return bindings


def _documents(value: object, label: str) -> dict:
    if type(value) is not list or len(value) > MAX_EDGES:
        raise CatalogError(f"{label} must be a bounded evidence-document list")
    records = {}
    for record in value:
        if type(record) is not dict or not {"path", "bytes", "sha256", "role"} <= set(record):
            raise CatalogError(f"{label} has an incomplete evidence-document record")
        path = record["path"]
        if (type(path) is not str or not path or path.startswith("/")
                or any(c in path for c in ("\\", ":", "*", "?", "[", "]", "\x00"))
                or any(part in ("", ".", "..") for part in path.split("/"))):
            raise CatalogError(f"{label} contains an unsafe evidence-document path")
        if path in records:
            raise CatalogError(f"{label} contains duplicate evidence-document paths")
        _integer(record["bytes"], "evidence-document bytes")
        _digest(record["sha256"], "evidence-document digest")
        if type(record["role"]) is not str or not record["role"]:
            raise CatalogError(f"{label} contains an invalid evidence-document role")
        records[path] = record
    if list(records) != sorted(records):
        raise CatalogError(f"{label} evidence documents are not in canonical path order")
    return records


def _rows(rows: object, expected_count: int) -> tuple[int, int, dict[str, Counter]]:
    if type(rows) is not list or len(rows) != expected_count or len(rows) > MAX_ROWS:
        raise CatalogError("catalogue has the wrong exact bounded row count")
    layers = {}
    edges = 0
    counters = {key: Counter() for key in ("membership", "evidence_status", "enrollment_origin")}
    for index, row in enumerate(rows):
        if type(row) is not dict:
            raise CatalogError("every theorem row must be a JSON object")
        name = row.get("name")
        if type(name) is not str or _NAME.fullmatch(name) is None or name in layers:
            raise CatalogError("catalogue theorem names must be unique identifiers")
        if _integer(row.get("enrollment_index"), "enrollment_index", maximum=MAX_ROWS - 1) != index:
            raise CatalogError("catalogue enrollment indices are not in exact canonical order")
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or len(dependencies) > MAX_DEPENDENCIES_PER_ROW:
            raise CatalogError("theorem dependencies exceed the existing per-row budget or are not a list")
        if any(type(dep) is not str for dep in dependencies) or len(set(dependencies)) != len(dependencies):
            raise CatalogError("theorem dependencies must be distinct names")
        if any(dep not in layers for dep in dependencies):
            raise CatalogError("missing, self, forward, or cyclic theorem dependency")
        edges += len(dependencies)
        if edges > MAX_EDGES:
            raise CatalogError("catalogue exceeds the existing dependency-edge budget")
        layers[name] = max((layers[dep] for dep in dependencies), default=-1) + 1
        if row.get("checked_use") is not True or row.get("body_checked") is not True:
            raise CatalogError("catalogue checked-use flags disagree with the declared fully checked release")
        for key, counter in counters.items():
            value = row.get(key)
            if type(value) is not str or not value:
                raise CatalogError(f"theorem row has invalid {key}")
            counter[value] += 1
    return edges, max(layers.values(), default=-1) + 1, counters


def _combine(parent: dict, metadata: dict, new_rows: list) -> dict:
    """Pure structural check; callers must separately authenticate input bytes."""
    if (type(parent) is not dict or parent.get("schema") != PARENT_SCHEMA
            or type(parent.get("theorem_count")) is not int
            or parent["theorem_count"] != PARENT_ROW_COUNT
            or type(parent.get("theorems")) is not list
            or len(parent["theorems"]) != PARENT_ROW_COUNT):
        raise CatalogError("the parent is not the exact non-recursive v30 logical catalogue")
    _metadata_header(metadata)
    inherited = set(parent) - {"theorems"}
    if set(metadata) != inherited | _NEW_FIELDS:
        raise CatalogError("logical metadata dropped historical fields or added unknown v31 fields")
    for key in inherited - _CURRENT_FIELDS:
        if not _same(metadata[key], parent[key]):
            raise CatalogError(f"immutable historical metadata changed: {key}")
    old_order, current_order = parent.get("canonical_order"), metadata["canonical_order"]
    if (type(old_order) is not list or type(current_order) is not list
            or any(type(item) is not str or not item for item in current_order)
            or len(current_order) <= len(old_order)
            or current_order[:len(old_order)] != old_order
            or len(set(current_order)) != len(current_order)):
        raise CatalogError("canonical_order must append to the unchanged historical order")
    old_documents = _documents(parent.get("evidence_documents"), "parent")
    current_documents = _documents(metadata["evidence_documents"], "current")
    for path, old in old_documents.items():
        if path not in current_documents or not _same(old, current_documents[path]):
            raise CatalogError(f"immutable historical evidence-document record changed: {path}")
    if type(new_rows) is not list or len(new_rows) != DELTA_ROW_COUNT:
        raise CatalogError("delta must contain exactly 574 new theorem rows")
    rows = [*parent["theorems"], *new_rows]
    edges, layer_count, counts = _rows(rows, ROW_COUNT)
    expected_counts = {
        "membership_counts": {"stable": STABLE_COUNT, "alpha_only": ROW_COUNT - STABLE_COUNT},
        "evidence_counts": {"stable_closed": STABLE_COUNT, "alpha_closed": ROW_COUNT - STABLE_COUNT},
        "enrollment_origin_counts": dict(Counter(parent["enrollment_origin_counts"]) + Counter(ha=DELTA_ROW_COUNT)),
    }
    for key, row_key in (("membership_counts", "membership"), ("evidence_counts", "evidence_status"),
                         ("enrollment_origin_counts", "enrollment_origin")):
        if not _same(metadata[key], expected_counts[key]) or counts[row_key] != expected_counts[key]:
            raise CatalogError(f"additive catalogue counts disagree with the actual rows: {key}")
    if metadata["edge_count"] != edges or metadata["layer_count"] != layer_count:
        raise CatalogError("catalogue topology counts disagree with the actual ordered dependencies")
    campaigns = Counter()
    for row in new_rows:
        campaign = row.get("frontier_campaign")
        if (type(campaign) is not str or not campaign
                or row["membership"] != "alpha_only" or row["evidence_status"] != "alpha_closed"
                or row["enrollment_origin"] != "ha"):
            raise CatalogError("new rows do not have the exact additive v31 membership/origin partition")
        campaigns[campaign] += 1
    if not _same(metadata["frontier_v31_campaign_counts"], dict(campaigns)):
        raise CatalogError("v31 campaign counts disagree with the exact delta")
    names_digest = sha256("\n".join(row["name"] for row in new_rows).encode()).hexdigest()
    if metadata["frontier_v31_ordered_names_sha256"] != names_digest:
        raise CatalogError("v31 ordered theorem-name digest disagrees with the exact delta")
    return {**metadata, "theorems": rows}


def load_catalog(path: Path | str, *, expected_sha256: str, owner_uid: int | None = None) -> dict:
    """Load the ordinary v31 logical dictionary, preserving every parent row.

    This authenticates bytes, immutable provenance, and bounded topology. It
    deliberately does not check a proof or issue an admission/Lean receipt.
    """
    manifest, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    documents = []
    for item in (bindings.parent, bindings.delta):
        raw, fingerprint = _read_file(item.path, owner_uid=owner, expected_bytes=item.bytes,
                                      expected_sha256=item.sha256)
        if fingerprint != item.fingerprint:
            raise CatalogError(f"catalogue file changed after its binding was read: {item.role}")
        documents.append(_decode(raw, item.role))
        del raw
    parent, delta = documents
    if (set(delta) != {"schema", "row_count", "theorems"} or delta["schema"] != DELTA_SCHEMA
            or _integer(delta.get("row_count"), "delta row_count", maximum=MAX_ROWS) != DELTA_ROW_COUNT):
        raise CatalogError("delta is not the exact non-recursive v31 row document")
    result = _combine(parent, manifest["metadata"], delta["theorems"])
    _unchanged(bindings, owner)
    return result


def encode_catalog(metadata: dict, new_rows: list) -> tuple[bytes, bytes]:
    """Build manifest/delta bytes after a literal-parent structural audit.

    The parent is read from its fixed repository path, never written or
    reserialized. No output file is created by this function. The caller must
    have obtained actual HA/Lean evidence before making checked-use claims.
    """
    raw, fingerprint = _read_file(_absolute_path(DEFAULT_PARENT), owner_uid=_owner(None),
                                  expected_bytes=PARENT_BYTES, expected_sha256=PARENT_SHA256)
    parent = _decode(raw, "literal v30 parent")
    del raw
    _combine(parent, metadata, new_rows)
    delta = _json_bytes({"schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT, "theorems": new_rows})
    manifest = _json_bytes({
        "schema": TRANSPORT_SCHEMA,
        "metadata": metadata,
        "parent": _parent_binding(),
        "delta": {"path": DELTA_BASENAME, "bytes": len(delta), "sha256": sha256(delta).hexdigest(),
                  "schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT},
    })
    if _stat_file(_absolute_path(DEFAULT_PARENT), _owner(None), PARENT_BYTES) != fingerprint:
        raise CatalogError("literal v30 parent changed during catalogue encoding")
    return manifest, delta


__all__ = [
    "CatalogError", "CatalogBindings", "CatalogFileBinding", "FileFingerprint",
    "TRANSPORT_SCHEMA", "LOGICAL_SCHEMA", "DELTA_SCHEMA", "PARENT_SCHEMA",
    "PARENT_BASENAME", "DELTA_BASENAME", "PARENT_BYTES", "PARENT_SHA256",
    "PARENT_ROW_COUNT", "DELTA_ROW_COUNT", "ROW_COUNT", "STABLE_COUNT",
    "MAX_REFERENCED_DOCUMENTS", "MAX_CATALOG_BYTES", "MAX_ROWS",
    "MAX_DEPENDENCIES_PER_ROW", "MAX_EDGES", "MAX_JSON_CONTAINERS",
    "MAX_JSON_DEPTH", "MAX_JSON_VALUES", "DEFAULT_PARENT",
    "load_catalog", "verify_catalog_bindings", "catalog_input_fingerprint", "encode_catalog",
]
