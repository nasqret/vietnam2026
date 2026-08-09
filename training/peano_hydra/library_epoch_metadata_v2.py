"""Candidate H1.1b2 metadata over the isolated 384-theorem reading API.

Version two is a full successor ledger.  It reads the exact retained v1
ledger as immutable predecessor evidence, but never imports or invokes the v1
builder.  The only fresh documentation authority it admits is the exact
five-file, replay-ordered documentation bundle.  Nothing in this module can
freeze an epoch or authorize training, retrieval, or evaluation.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Mapping


SCHEMA_FORMAT = "peano-hydra-library-epoch-metadata-schema"
SCHEMA_VERSION = 2
SCHEMA_ID = "peano-hydra-library-epoch-metadata-v2"
SCHEMA_PATH = Path(__file__).with_name("library-epoch-metadata-schema-v2.json")
SCHEMA_SHA256 = "498dde0a3b4f762197d8c371609dfac2eabf7edcfc37a6d3c5cdf6ca21efb38a"

METADATA_FORMAT = "peano-hydra-library-epoch-metadata"
METADATA_VERSION = 2
METADATA_ID = "authoring-library-epoch-metadata-candidate-v2"
METADATA_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-epoch-metadata-root-preimage"
)
THEOREM_RECORDS_PREIMAGE_FORMAT = (
    "peano-hydra-library-epoch-theorem-records-preimage"
)
DEFINITION_USE_PREIMAGE_FORMAT = (
    "peano-hydra-library-definition-use-receipt-preimage"
)
READINESS_FORMAT = "peano-hydra-library-epoch-metadata-readiness"

STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
THEOREM_COUNT = 384
DECLARED_DEPENDENCY_EDGES = 1_038
DEPLOYED_PAGE_COMPLETE_COUNT = 240
DEFINITION_OCCURRENCES = 2_027

PREDECESSOR_SCHEMA_ARTIFACT_SHA256 = (
    "9867378c8802501d2120ad4d94a86378815cf90b003eafc92b164685da61c956"
)
PREDECESSOR_SCHEMA_SEMANTIC_SHA256 = (
    "71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c"
)
PREDECESSOR_LEDGER_ARTIFACT_SHA256 = (
    "e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289"
)
PREDECESSOR_LEDGER_ROOT_SHA256 = (
    "b2f397cec26d5f22bf0806da1f6e219d26bb5e319a503395150d9278efae8279"
)
PREDECESSOR_READINESS_ARTIFACT_SHA256 = (
    "386be7eb475980a373122d769a496220319d34090463e0a3bc870cfece3e4c25"
)

BUNDLE_SCHEMA_SEMANTIC_SHA256 = (
    "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d"
)
BUNDLE_SCHEMA_ARTIFACT_SHA256 = (
    "a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c"
)
BUNDLE_EXPLICIT_ARTIFACT_SHA256 = (
    "f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936"
)
BUNDLE_EXPLICIT_ROOT_SHA256 = (
    "b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da"
)
BUNDLE_DEFINED_ARTIFACT_SHA256 = (
    "164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea"
)
BUNDLE_DEFINED_ROOT_SHA256 = (
    "897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f"
)
BUNDLE_ISOLATION_ARTIFACT_SHA256 = (
    "8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6"
)
BUNDLE_ISOLATION_ROOT_SHA256 = (
    "64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919"
)
BUNDLE_MANIFEST_ARTIFACT_SHA256 = (
    "5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf"
)
BUNDLE_MANIFEST_ROOT_SHA256 = (
    "8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4"
)

MAX_SCHEMA_BYTES = 1_000_000
MAX_METADATA_BYTES = 24_000_000
MAX_PREDECESSOR_LEDGER_BYTES = 16_000_000
MAX_PREDECESSOR_SCHEMA_BYTES = 1_000_000
MAX_PREDECESSOR_READINESS_BYTES = 1_000_000
MAX_BUNDLE_SCHEMA_BYTES = 1_000_000
MAX_BUNDLE_EXPLICIT_BYTES = 8_000_000
MAX_BUNDLE_DEFINED_BYTES = 16_000_000
MAX_BUNDLE_ISOLATION_BYTES = 1_000_000
MAX_BUNDLE_MANIFEST_BYTES = 1_000_000
MAX_JSON_DEPTH = 192
MAX_JSON_ITEMS = 3_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_PREDECESSOR_SCHEMA_RELATIVE = Path(
    "training/peano_hydra/library-epoch-metadata-schema-v1.json"
)
_PREDECESSOR_LEDGER_RELATIVE = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json"
)
_PREDECESSOR_READINESS_RELATIVE = Path(
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1-readiness.json"
)
_BUNDLE_RELATIVE = Path("artifacts/peano-hydra/l0-documentation-candidate-v1")

_BUNDLE_FILES = {
    "defined.json": (MAX_BUNDLE_DEFINED_BYTES, BUNDLE_DEFINED_ARTIFACT_SHA256),
    "explicit.json": (MAX_BUNDLE_EXPLICIT_BYTES, BUNDLE_EXPLICIT_ARTIFACT_SHA256),
    "isolation-receipt.json": (
        MAX_BUNDLE_ISOLATION_BYTES,
        BUNDLE_ISOLATION_ARTIFACT_SHA256,
    ),
    "manifest.json": (MAX_BUNDLE_MANIFEST_BYTES, BUNDLE_MANIFEST_ARTIFACT_SHA256),
    "schema.json": (MAX_BUNDLE_SCHEMA_BYTES, BUNDLE_SCHEMA_ARTIFACT_SHA256),
}

_METADATA_FIELDS = frozenset(
    {
        "aggregate",
        "documentation_sources",
        "evaluation_eligible",
        "format",
        "freeze_ready",
        "gaps",
        "id",
        "logic_mode",
        "predecessor",
        "replay_pack",
        "repository",
        "retrieval_eligible",
        "root_preimage",
        "root_sha256",
        "schema",
        "status",
        "supersession",
        "theorem_count",
        "theorem_records",
        "theorems",
        "training_eligible",
        "v",
    }
)
_THEOREM_FIELDS = frozenset(
    {
        "declaration_order",
        "definitions",
        "dependencies",
        "documentation",
        "explanation",
        "index",
        "layer",
        "lineage",
        "logic",
        "name",
        "optimized_construction",
        "predecessor",
        "presentation",
        "proof",
        "readable_proof",
        "record_sha256",
        "source",
        "statement",
    }
)
_PRESENTATION_STATUSES = frozenset({"missing", "present", "stale"})


class LibraryEpochMetadataV2Error(ValueError):
    """The successor metadata or one of its exact inputs is malformed."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryEpochMetadataV2Error(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise LibraryEpochMetadataV2Error(f"forbidden JSON constant {value!r}")


def _reject_float(value: str) -> object:
    raise LibraryEpochMetadataV2Error(
        f"floating-point JSON value {value!r} is forbidden"
    )


def _validate_json_value(
    value: object,
    *,
    depth: int = 0,
    active: set[int] | None = None,
    counter: list[int] | None = None,
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise LibraryEpochMetadataV2Error("JSON exceeds the nesting limit")
    if active is None:
        active = set()
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_JSON_ITEMS:
        raise LibraryEpochMetadataV2Error("JSON exceeds the item limit")
    if value is None or type(value) in (bool, str):
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_JSON_INTEGER:
            raise LibraryEpochMetadataV2Error("JSON integer exceeds the safe domain")
        return
    if type(value) not in (list, dict):
        raise LibraryEpochMetadataV2Error("value is outside strict JSON")
    identity = id(value)
    if identity in active:
        raise LibraryEpochMetadataV2Error("cyclic JSON value is forbidden")
    active.add(identity)
    try:
        values = value.values() if type(value) is dict else value
        if type(value) is dict and not all(type(key) is str for key in value):
            raise LibraryEpochMetadataV2Error("JSON object keys must be text")
        for item in values:
            _validate_json_value(
                item, depth=depth + 1, active=active, counter=counter
            )
    finally:
        active.remove(identity)


def _canonical_json_bytes(
    value: object, *, limit: int = MAX_METADATA_BYTES
) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json_value(value)
    try:
        raw = json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryEpochMetadataV2Error(
            f"value is not canonical JSON: {exc}"
        ) from None
    if len(raw) > limit:
        raise LibraryEpochMetadataV2Error(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_METADATA_BYTES
) -> bytes:
    """Return the unique retained UTF-8 JSON representation."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json_value(value)
    try:
        raw = (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryEpochMetadataV2Error(
            f"value is not canonical JSON: {exc}"
        ) from None
    if len(raw) > limit:
        raise LibraryEpochMetadataV2Error(
            f"canonical JSON document exceeds the {limit}-byte limit"
        )
    return raw


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_METADATA_BYTES) -> str:
    return _sha256_bytes(_canonical_json_bytes(value, limit=limit))


def _decode_json(raw: bytes, label: str) -> object:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except LibraryEpochMetadataV2Error:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryEpochMetadataV2Error(
            f"{label} is not strict JSON: {exc}"
        ) from None


def _decode_canonical_document(
    raw: bytes, label: str, *, limit: int
) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryEpochMetadataV2Error(f"{label} must be bounded exact bytes")
    value = _decode_json(raw, label)
    if type(value) is not dict:
        raise LibraryEpochMetadataV2Error(f"{label} must be one JSON object")
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryEpochMetadataV2Error(
            f"{label} is not a canonical JSON document"
        )
    return value


def _detached(value: object, label: str) -> object:
    return _decode_json(_canonical_json_bytes(value), label)


def _detached_object(value: object, label: str) -> dict[str, object]:
    detached = _detached(value, label)
    if type(detached) is not dict:
        raise LibraryEpochMetadataV2Error(f"{label} must be one JSON object")
    return detached


def _require_fields(
    label: str, value: object, fields: frozenset[str] | set[str]
) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(fields):
        raise LibraryEpochMetadataV2Error(
            f"{label} has missing or additional fields"
        )
    return value


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository root must be a pathlib.Path")
    try:
        metadata = root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryEpochMetadataV2Error(
                "repository root must be a non-symlink directory"
            )
        return root.resolve(strict=True)
    except OSError as exc:
        raise LibraryEpochMetadataV2Error("cannot resolve repository root") from exc


def _fixed_path(root: Path, relative: Path, *, directory: bool = False) -> Path:
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise LibraryEpochMetadataV2Error("fixed input path escapes repository")
    current = root
    try:
        for part in relative.parts:
            current = current / part
            metadata = current.lstat()
            is_last = current == root / relative
            if stat.S_ISLNK(metadata.st_mode):
                raise LibraryEpochMetadataV2Error(
                    "fixed input path contains a symbolic link"
                )
            if not is_last and not stat.S_ISDIR(metadata.st_mode):
                raise LibraryEpochMetadataV2Error(
                    "fixed input parent is not a directory"
                )
        final_mode = current.lstat().st_mode
        if directory != stat.S_ISDIR(final_mode):
            expected = "directory" if directory else "regular file"
            raise LibraryEpochMetadataV2Error(f"fixed input is not a {expected}")
        if not directory and not stat.S_ISREG(final_mode):
            raise LibraryEpochMetadataV2Error("fixed input is not a regular file")
    except FileNotFoundError as exc:
        raise LibraryEpochMetadataV2Error("fixed input is missing") from exc
    except OSError as exc:
        raise LibraryEpochMetadataV2Error("cannot inspect fixed input path") from exc
    return current


def _safe_external_file(path: Path) -> Path:
    """Accept a caller path only when every lexical component is non-link."""

    try:
        absolute = Path(os.path.abspath(path))
        parts = absolute.parts
        if not absolute.is_absolute() or len(parts) < 2:
            raise LibraryEpochMetadataV2Error("metadata-v2 path is malformed")
        current = Path(parts[0])
        for index, part in enumerate(parts[1:], 1):
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise LibraryEpochMetadataV2Error(
                    "metadata-v2 path contains a symbolic link"
                )
            if index < len(parts) - 1 and not stat.S_ISDIR(metadata.st_mode):
                raise LibraryEpochMetadataV2Error(
                    "metadata-v2 path parent is not a directory"
                )
        if not stat.S_ISREG(current.lstat().st_mode):
            raise LibraryEpochMetadataV2Error(
                "metadata-v2 path is not a regular file"
            )
        return current
    except LibraryEpochMetadataV2Error:
        raise
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(
            "cannot inspect metadata-v2 path"
        ) from exc


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("bounded file limit must be a positive exact integer")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size < 1
            or before.st_size > limit
        ):
            raise LibraryEpochMetadataV2Error(
                f"{label} must be a bounded nonempty regular file"
            )
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise LibraryEpochMetadataV2Error(f"{label} changed while read")
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)
    if len(raw) != before.st_size:
        raise LibraryEpochMetadataV2Error(f"{label} changed size while read")
    return raw


def _exact_document(
    root: Path,
    relative: Path,
    *,
    label: str,
    limit: int,
    expected_sha256: str,
) -> tuple[bytes, dict[str, object]]:
    path = _fixed_path(root, relative)
    raw = _read_bounded_regular_file(path, label=label, limit=limit)
    if _sha256_bytes(raw) != expected_sha256:
        raise LibraryEpochMetadataV2Error(f"{label} exact bytes drifted")
    return raw, _decode_canonical_document(raw, label, limit=limit)


def epoch_metadata_v2_schema() -> dict[str, object]:
    """Load and verify the closed binding schema for metadata v2."""

    raw = _read_bounded_regular_file(
        SCHEMA_PATH, label="library epoch metadata-v2 schema", limit=MAX_SCHEMA_BYTES
    )
    schema = _decode_canonical_document(
        raw, "library epoch metadata-v2 schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        schema.get("format") != SCHEMA_FORMAT
        or schema.get("id") != SCHEMA_ID
        or schema.get("v") != SCHEMA_VERSION
        or schema.get("limits", {}).get("theorem_count") != THEOREM_COUNT
    ):
        raise LibraryEpochMetadataV2Error("metadata-v2 schema identity drifted")
    if _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != SCHEMA_SHA256:
        raise LibraryEpochMetadataV2Error("metadata-v2 schema digest drifted")
    return _detached_object(schema, "metadata-v2 schema")


def epoch_metadata_v2_schema_identity() -> dict[str, object]:
    """Return semantic and exact-file identities of the v2 schema."""

    schema = epoch_metadata_v2_schema()
    return {
        "artifact_sha256": _sha256_bytes(
            canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
        ),
        "format": SCHEMA_FORMAT,
        "id": SCHEMA_ID,
        "sha256": SCHEMA_SHA256,
        "v": SCHEMA_VERSION,
    }


def _validate_predecessor_root(ledger: dict[str, object]) -> None:
    if (
        ledger.get("format") != METADATA_FORMAT
        or ledger.get("id") != "authoring-library-epoch-metadata-candidate-v1"
        or ledger.get("v") != 1
        or ledger.get("status") != STATUS
        or ledger.get("logic_mode") != LOGIC_MODE
        or ledger.get("freeze_ready") is not False
        or ledger.get("evaluation_eligible") is not False
        or ledger.get("theorem_count") != THEOREM_COUNT
        or ledger.get("root_sha256") != PREDECESSOR_LEDGER_ROOT_SHA256
    ):
        raise LibraryEpochMetadataV2Error("predecessor ledger constants drifted")
    preimage = ledger.get("root_preimage")
    body = {
        key: value
        for key, value in ledger.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    expected = {
        "format": METADATA_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    if preimage != expected or _sha256_json(preimage) != PREDECESSOR_LEDGER_ROOT_SHA256:
        raise LibraryEpochMetadataV2Error("predecessor ledger root is malformed")


def _load_predecessor(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    schema_raw, schema = _exact_document(
        root,
        _PREDECESSOR_SCHEMA_RELATIVE,
        label="predecessor schema",
        limit=MAX_PREDECESSOR_SCHEMA_BYTES,
        expected_sha256=PREDECESSOR_SCHEMA_ARTIFACT_SHA256,
    )
    if (
        schema.get("format") != SCHEMA_FORMAT
        or schema.get("id") != "peano-hydra-library-epoch-metadata-v1"
        or schema.get("v") != 1
        or _sha256_json(schema, limit=MAX_PREDECESSOR_SCHEMA_BYTES)
        != PREDECESSOR_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryEpochMetadataV2Error("predecessor schema identity drifted")
    ledger_raw, ledger = _exact_document(
        root,
        _PREDECESSOR_LEDGER_RELATIVE,
        label="predecessor ledger",
        limit=MAX_PREDECESSOR_LEDGER_BYTES,
        expected_sha256=PREDECESSOR_LEDGER_ARTIFACT_SHA256,
    )
    _validate_predecessor_root(ledger)
    if ledger.get("schema") != {
        "artifact_sha256": _sha256_bytes(schema_raw),
        "format": SCHEMA_FORMAT,
        "id": "peano-hydra-library-epoch-metadata-v1",
        "sha256": PREDECESSOR_SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }:
        raise LibraryEpochMetadataV2Error("predecessor ledger/schema join drifted")
    _, readiness = _exact_document(
        root,
        _PREDECESSOR_READINESS_RELATIVE,
        label="predecessor readiness",
        limit=MAX_PREDECESSOR_READINESS_BYTES,
        expected_sha256=PREDECESSOR_READINESS_ARTIFACT_SHA256,
    )
    if (
        readiness.get("format") != READINESS_FORMAT
        or readiness.get("v") != 1
        or readiness.get("status") != STATUS
        or readiness.get("freeze_ready") is not False
        or readiness.get("evaluation_eligible") is not False
        or readiness.get("metadata_root_sha256") != ledger["root_sha256"]
        or readiness.get("theorem_count") != THEOREM_COUNT
    ):
        raise LibraryEpochMetadataV2Error("predecessor readiness join drifted")
    rows = ledger.get("theorems")
    if type(rows) is not list or len(rows) != THEOREM_COUNT:
        raise LibraryEpochMetadataV2Error("predecessor theorem rows drifted")
    names: set[str] = set()
    edge_count = 0
    for index, row in enumerate(rows):
        if (
            type(row) is not dict
            or row.get("index") != index
            or row.get("declaration_order") != index
            or type(row.get("name")) is not str
            or row["name"] in names
        ):
            raise LibraryEpochMetadataV2Error("predecessor theorem order drifted")
        names.add(row["name"])
        dependencies = row.get("dependencies")
        declared = (
            dependencies.get("declared_publication_dependencies")
            if type(dependencies) is dict
            else None
        )
        if type(declared) is not list:
            raise LibraryEpochMetadataV2Error(
                "predecessor dependency receipt drifted"
            )
        edge_count += len(declared)
    if edge_count != DECLARED_DEPENDENCY_EDGES:
        raise LibraryEpochMetadataV2Error("predecessor dependency graph drifted")
    return ledger, readiness


def _bundle_module(root: Path):
    try:
        import training.peano_hydra.library_documentation_bundle as module
    except ImportError as exc:
        raise LibraryEpochMetadataV2Error(
            f"cannot import selected documentation validator: {exc}"
        ) from None
    source = getattr(module, "__file__", None)
    if type(source) is not str:
        raise LibraryEpochMetadataV2Error(
            "cannot identify selected documentation validator"
        )
    try:
        expected = (
            root / "training/peano_hydra/library_documentation_bundle.py"
        ).resolve(strict=True)
        actual = Path(source).resolve(strict=True)
    except OSError as exc:
        raise LibraryEpochMetadataV2Error(
            "cannot resolve selected documentation validator"
        ) from exc
    if actual != expected:
        raise LibraryEpochMetadataV2Error(
            "selected documentation validator import origin drifted"
        )
    return module


def _load_selected_bundle(root: Path) -> dict[str, dict[str, object]]:
    directory = _fixed_path(root, _BUNDLE_RELATIVE, directory=True)
    module = _bundle_module(root)
    try:
        loaded = module.load_documentation_bundle(directory, repository_root=root)
    except module.LibraryDocumentationBundleError as exc:
        raise LibraryEpochMetadataV2Error(
            f"selected documentation bundle is invalid: {exc}"
        ) from None
    if type(loaded) is not dict or set(loaded) != set(_BUNDLE_FILES):
        raise LibraryEpochMetadataV2Error("selected documentation layout drifted")
    for filename, (limit, digest) in _BUNDLE_FILES.items():
        raw = _read_bounded_regular_file(
            _fixed_path(root, _BUNDLE_RELATIVE / filename),
            label=f"selected documentation member {filename!r}",
            limit=limit,
        )
        if _sha256_bytes(raw) != digest:
            raise LibraryEpochMetadataV2Error(
                f"selected documentation member {filename!r} drifted"
            )
        decoded = _decode_canonical_document(
            raw, f"selected documentation member {filename!r}", limit=limit
        )
        if _canonical_json_bytes(decoded, limit=limit) != _canonical_json_bytes(
            loaded[filename], limit=limit
        ):
            raise LibraryEpochMetadataV2Error(
                f"selected documentation member {filename!r} changed after load"
            )
    schema = loaded["schema.json"]
    explicit = loaded["explicit.json"]
    defined = loaded["defined.json"]
    isolation = loaded["isolation-receipt.json"]
    manifest = loaded["manifest.json"]
    if (
        _sha256_json(schema, limit=MAX_BUNDLE_SCHEMA_BYTES)
        != BUNDLE_SCHEMA_SEMANTIC_SHA256
        or explicit.get("root_sha256") != BUNDLE_EXPLICIT_ROOT_SHA256
        or defined.get("root_sha256") != BUNDLE_DEFINED_ROOT_SHA256
        or isolation.get("root_sha256") != BUNDLE_ISOLATION_ROOT_SHA256
        or manifest.get("root_sha256") != BUNDLE_MANIFEST_ROOT_SHA256
        or explicit.get("theorem_count") != THEOREM_COUNT
        or defined.get("theorem_count") != THEOREM_COUNT
        or manifest.get("aggregate", {}).get("declared_dependency_edges")
        != DECLARED_DEPENDENCY_EDGES
    ):
        raise LibraryEpochMetadataV2Error("selected documentation pins drifted")
    return loaded


def _bundle_identity(bundle: Mapping[str, dict[str, object]]) -> dict[str, object]:
    explicit = bundle["explicit.json"]
    defined = bundle["defined.json"]
    isolation = bundle["isolation-receipt.json"]
    manifest = bundle["manifest.json"]
    schema = bundle["schema.json"]
    return {
        "artifact_path": _BUNDLE_RELATIVE.as_posix(),
        "defined": {
            "artifact_path": (_BUNDLE_RELATIVE / "defined.json").as_posix(),
            "artifact_sha256": BUNDLE_DEFINED_ARTIFACT_SHA256,
            "definition_count": defined["aggregate"]["definition_count"],
            "ordered_record_root_sha256": defined["aggregate"][
                "ordered_record_root_sha256"
            ],
            "record_count": defined["theorem_count"],
            "root_sha256": defined["root_sha256"],
        },
        "explicit": {
            "artifact_path": (_BUNDLE_RELATIVE / "explicit.json").as_posix(),
            "artifact_sha256": BUNDLE_EXPLICIT_ARTIFACT_SHA256,
            "ordered_record_root_sha256": explicit["dependency_receipt"][
                "ordered_record_root_sha256"
            ],
            "record_count": explicit["theorem_count"],
            "root_sha256": explicit["root_sha256"],
        },
        "isolation": {
            "artifact_path": (
                _BUNDLE_RELATIVE / "isolation-receipt.json"
            ).as_posix(),
            "artifact_sha256": BUNDLE_ISOLATION_ARTIFACT_SHA256,
            "root_sha256": isolation["root_sha256"],
        },
        "manifest": {
            "artifact_path": (_BUNDLE_RELATIVE / "manifest.json").as_posix(),
            "artifact_sha256": BUNDLE_MANIFEST_ARTIFACT_SHA256,
            "root_sha256": manifest["root_sha256"],
        },
        "registry": _detached_object(defined["registry"], "definition registry"),
        "schema": {
            "artifact_path": (_BUNDLE_RELATIVE / "schema.json").as_posix(),
            "artifact_sha256": BUNDLE_SCHEMA_ARTIFACT_SHA256,
            "format": schema["format"],
            "id": schema["id"],
            "sha256": BUNDLE_SCHEMA_SEMANTIC_SHA256,
            "v": schema["v"],
        },
    }


def _selected_api_receipt(
    *, filename: str, artifact_sha256: str, document: Mapping[str, object], row: Mapping[str, object]
) -> dict[str, object]:
    return {
        "artifact_path": (_BUNDLE_RELATIVE / filename).as_posix(),
        "artifact_sha256": artifact_sha256,
        "document_root_sha256": document["root_sha256"],
        "record_sha256": row["record_sha256"],
        "status": "present",
    }


def _record_hash(row: Mapping[str, object]) -> str:
    return _sha256_json(
        {key: value for key, value in row.items() if key != "record_sha256"}
    )


def _add_record_hash(row: dict[str, object]) -> dict[str, object]:
    if "record_sha256" in row:
        raise LibraryEpochMetadataV2Error("theorem record hash is duplicated")
    result = {**row, "record_sha256": "0" * 64}
    result["record_sha256"] = _record_hash(result)
    return result


def _candidate_body(
    root: Path,
) -> tuple[dict[str, object], list[dict[str, object]]]:
    predecessor, _readiness = _load_predecessor(root)
    bundle = _load_selected_bundle(root)
    explicit = bundle["explicit.json"]
    defined = bundle["defined.json"]
    explicit_rows = explicit["theorems"]
    defined_rows = defined["theorems"]
    old_rows = predecessor["theorems"]
    if not all(type(rows) is list and len(rows) == THEOREM_COUNT for rows in (
        old_rows,
        explicit_rows,
        defined_rows,
    )):
        raise LibraryEpochMetadataV2Error("selected theorem arrays drifted")
    definitions = defined.get("definitions")
    if type(definitions) is not list or len(definitions) != 40:
        raise LibraryEpochMetadataV2Error("selected definition records drifted")
    definition_records: dict[str, tuple[str, int]] = {}
    for definition_index, definition in enumerate(definitions):
        if (
            type(definition) is not dict
            or definition.get("index") != definition_index
            or type(definition.get("id")) is not str
            or type(definition.get("name")) is not str
            or definition["id"] in definition_records
        ):
            raise LibraryEpochMetadataV2Error(
                "selected definition identities drifted"
            )
        definition_records[definition["id"]] = (
            definition["name"],
            definition_index,
        )
    registry = _detached_object(defined["registry"], "selected definition registry")

    theorem_rows: list[dict[str, object]] = []
    explicit_page_present = 0
    defined_page_present = 0
    deployed_page_complete = 0
    source_present = 0
    edge_count = 0
    definition_occurrences = 0
    for index, (old, explicit_row, defined_row) in enumerate(
        zip(old_rows, explicit_rows, defined_rows, strict=True)
    ):
        if not all(type(row) is dict for row in (old, explicit_row, defined_row)):
            raise LibraryEpochMetadataV2Error("selected theorem row is malformed")
        name = old.get("name")
        if not (
            old.get("index") == old.get("declaration_order") == index
            and explicit_row.get("index") == index
            and defined_row.get("index") == index
            and explicit_row.get("name") == defined_row.get("name") == name
            and defined_row.get("explicit_record_sha256")
            == explicit_row.get("record_sha256")
        ):
            raise LibraryEpochMetadataV2Error(
                f"predecessor/selected theorem join drifted at row {index}"
            )
        old_statement = old.get("statement")
        old_readable = old.get("readable_proof")
        old_explanation = old.get("explanation")
        old_source = old.get("source")
        command_lines = explicit_row.get("command_lines")
        defined_script = defined_row.get("script")
        defined_statement = defined_row.get("statement")
        expected_source = (
            {key: value for key, value in old_source.items() if key != "status"}
            if type(old_source) is dict
            else None
        )
        if not all(
            (
                type(old_statement) is dict,
                type(old_readable) is dict,
                type(old_explanation) is dict,
                type(old_source) is dict,
                old_source.get("status") == "present",
                explicit_row.get("catalog_layer") == old.get("layer"),
                explicit_row.get("formula_sha256")
                == old_statement.get("formula_sha256"),
                explicit_row.get("statement_source") == old_statement.get("source"),
                explicit_row.get("statement_source_sha256")
                == old_statement.get("source_sha256"),
                explicit_row.get("statement_canonical")
                == old_statement.get("canonical"),
                explicit_row.get("statement_canonical_sha256")
                == old_statement.get("canonical_sha256"),
                explicit_row.get("script_sha256")
                == old_readable.get("script_sha256"),
                type(command_lines) is list,
                type(command_lines) is list
                and [line.get("text") for line in command_lines]
                == old_readable.get("script"),
                explicit_row.get("summary") == old_explanation.get("text"),
                explicit_row.get("summary_sha256") == old_explanation.get("sha256"),
                explicit_row.get("source") == expected_source,
                type(defined_statement) is dict,
                type(defined_statement) is dict
                and defined_statement.get("expanded_source")
                == old_statement.get("source"),
                type(defined_statement) is dict
                and defined_statement.get("receipt", {}).get(
                    "expanded_source_sha256"
                )
                == old_statement.get("source_sha256"),
                type(defined_statement) is dict
                and defined_statement.get("receipt", {}).get(
                    "canonical_expansion_sha256"
                )
                == old_statement.get("canonical_sha256"),
                type(defined_script) is list,
                type(defined_script) is list
                and [line.get("expanded_command") for line in defined_script]
                == old_readable.get("script"),
            )
        ):
            raise LibraryEpochMetadataV2Error(
                f"predecessor/selected semantic join drifted at row {index}"
            )
        dependencies = old.get("dependencies")
        declared = (
            dependencies.get("declared_publication_dependencies")
            if type(dependencies) is dict
            else None
        )
        if (
            type(declared) is not list
            or explicit_row.get("declared_dependencies") != declared
            or explicit_row.get("minimality_claim")
            != dependencies.get("minimality_claim")
        ):
            raise LibraryEpochMetadataV2Error(
                f"selected dependency join drifted at row {index}"
            )
        edge_count += len(declared)
        uses = defined_row.get("definition_uses")
        if type(uses) is not list:
            raise LibraryEpochMetadataV2Error(
                f"definition-use receipt drifted at row {index}"
            )
        previous_definition_index = -1
        seen_use_ids: set[str] = set()
        for use in uses:
            definition_id = use.get("definition") if type(use) is dict else None
            definition_identity = definition_records.get(definition_id)
            if (
                type(use) is not dict
                or set(use) != {"definition", "name", "occurrences"}
                or definition_identity is None
                or use.get("name") != definition_identity[0]
                or definition_id in seen_use_ids
                or definition_identity[1] <= previous_definition_index
                or type(use.get("occurrences")) is not int
                or use["occurrences"] < 1
            ):
                raise LibraryEpochMetadataV2Error(
                    f"definition-use entry drifted at row {index}"
                )
            seen_use_ids.add(definition_id)
            previous_definition_index = definition_identity[1]
        use_preimage = {
            "format": DEFINITION_USE_PREIMAGE_FORMAT,
            "uses": _detached(uses, "selected definition uses"),
            "v": METADATA_VERSION,
        }
        definition_occurrences += sum(use["occurrences"] for use in uses)
        old_documentation = old.get("documentation")
        if type(old_documentation) is not dict:
            raise LibraryEpochMetadataV2Error(
                f"predecessor documentation drifted at row {index}"
            )
        explicit_page_status = old_documentation.get("explicit_explorer", {}).get(
            "status"
        )
        defined_page_status = old_documentation.get("defined_explorer", {}).get(
            "status"
        )
        if (
            explicit_page_status not in _PRESENTATION_STATUSES
            or defined_page_status not in _PRESENTATION_STATUSES
        ):
            raise LibraryEpochMetadataV2Error(
                f"predecessor presentation status drifted at row {index}"
            )
        explicit_page_present += explicit_page_status == "present"
        defined_page_present += defined_page_status == "present"
        deployed_page_complete += (
            explicit_page_status == "present" and defined_page_status == "present"
        )
        source_present += old.get("source", {}).get("status") == "present"
        preserved = {
            key: _detached(old[key], f"predecessor theorem {key}")
            for key in (
                "declaration_order",
                "dependencies",
                "explanation",
                "index",
                "layer",
                "lineage",
                "logic",
                "name",
                "optimized_construction",
                "proof",
                "readable_proof",
                "source",
                "statement",
            )
        }
        theorem_rows.append(
            _add_record_hash(
                {
                    **preserved,
                    "definitions": {
                        "artifact_path": (
                            _BUNDLE_RELATIVE / "defined.json"
                        ).as_posix(),
                        "artifact_sha256": BUNDLE_DEFINED_ARTIFACT_SHA256,
                        "definition_use_count": sum(
                            use["occurrences"] for use in uses
                        ),
                        "definition_use_preimage": use_preimage,
                        "definition_use_receipt_sha256": _sha256_json(use_preimage),
                        "document_root_sha256": defined["root_sha256"],
                        "record_sha256": defined_row["record_sha256"],
                        "registry": registry,
                        "status": "present",
                    },
                    "documentation": {
                        "atlas": _detached_object(
                            old_documentation["atlas"], "predecessor atlas receipt"
                        ),
                        "selected_defined_api": _selected_api_receipt(
                            filename="defined.json",
                            artifact_sha256=BUNDLE_DEFINED_ARTIFACT_SHA256,
                            document=defined,
                            row=defined_row,
                        ),
                        "selected_explicit_api": _selected_api_receipt(
                            filename="explicit.json",
                            artifact_sha256=BUNDLE_EXPLICIT_ARTIFACT_SHA256,
                            document=explicit,
                            row=explicit_row,
                        ),
                        "vault": _detached_object(
                            old_documentation["vault"], "predecessor vault receipt"
                        ),
                    },
                    "predecessor": {"record_sha256": _sha256_json(old)},
                    "presentation": {
                        "authority": "historical-non-authoritative",
                        "deployed_defined_page_status": defined_page_status,
                        "deployed_explicit_page_status": explicit_page_status,
                    },
                }
            )
        )

    if (
        edge_count != DECLARED_DEPENDENCY_EDGES
        or explicit_page_present != DEPLOYED_PAGE_COMPLETE_COUNT
        or defined_page_present != DEPLOYED_PAGE_COMPLETE_COUNT
        or deployed_page_complete != DEPLOYED_PAGE_COMPLETE_COUNT
        or source_present != THEOREM_COUNT
        or definition_occurrences
        != defined.get("aggregate", {}).get("definition_occurrences")
        or definition_occurrences != DEFINITION_OCCURRENCES
    ):
        raise LibraryEpochMetadataV2Error("candidate coverage aggregate drifted")
    identities = [
        {
            "index": row["index"],
            "name": row["name"],
            "record_sha256": row["record_sha256"],
        }
        for row in theorem_rows
    ]
    theorem_preimage = {
        "format": THEOREM_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": METADATA_VERSION,
    }
    theorem_records = {
        "count": THEOREM_COUNT,
        "preimage": theorem_preimage,
        "root_sha256": _sha256_json(theorem_preimage),
    }
    count = THEOREM_COUNT
    gaps = {
        "atlas_missing_count": 0,
        "atlas_stale_count": 0,
        "deployed_defined_page_pending_count": count - defined_page_present,
        "deployed_explicit_page_pending_count": count - explicit_page_present,
        "human_review_pending_count": count,
        "lineage_pending_count": count,
        "optimized_best_known_pending_count": count,
        "optimized_dependency_vectors_pending_count": count,
        "publication_union_pending_count": count,
        "readable_dependency_vectors_unverified_count": count,
        "selected_defined_api_missing_count": 0,
        "selected_defined_api_stale_count": 0,
        "selected_definition_receipt_missing_count": 0,
        "selected_definition_receipt_stale_count": 0,
        "selected_explicit_api_missing_count": 0,
        "selected_explicit_api_stale_count": 0,
        "source_locator_missing_count": 0,
        "vault_missing_count": 0,
        "vault_stale_count": 0,
    }
    body = {
        "aggregate": {
            "declared_dependency_edges": edge_count,
            "deployed_page_documentation_complete_count": deployed_page_complete,
            "selected_api_documentation_complete_count": count,
            "source_locator_count": source_present,
            "theorem_count": count,
        },
        "documentation_sources": {
            "atlas": _detached_object(
                predecessor["documentation_sources"]["atlas"],
                "predecessor atlas source",
            ),
            "selected_bundle": _bundle_identity(bundle),
            "vault": _detached_object(
                predecessor["documentation_sources"]["vault"],
                "predecessor vault source",
            ),
        },
        "evaluation_eligible": False,
        "format": METADATA_FORMAT,
        "freeze_ready": False,
        "gaps": gaps,
        "id": METADATA_ID,
        "logic_mode": LOGIC_MODE,
        "predecessor": {
            "ledger": {
                "artifact_path": _PREDECESSOR_LEDGER_RELATIVE.as_posix(),
                "artifact_sha256": PREDECESSOR_LEDGER_ARTIFACT_SHA256,
                "id": predecessor["id"],
                "root_sha256": predecessor["root_sha256"],
                "v": predecessor["v"],
            },
            "readiness": {
                "artifact_path": _PREDECESSOR_READINESS_RELATIVE.as_posix(),
                "artifact_sha256": PREDECESSOR_READINESS_ARTIFACT_SHA256,
                "metadata_root_sha256": predecessor["root_sha256"],
                "v": 1,
            },
            "schema": {
                "artifact_path": _PREDECESSOR_SCHEMA_RELATIVE.as_posix(),
                "artifact_sha256": PREDECESSOR_SCHEMA_ARTIFACT_SHA256,
                "format": SCHEMA_FORMAT,
                "id": "peano-hydra-library-epoch-metadata-v1",
                "sha256": PREDECESSOR_SCHEMA_SEMANTIC_SHA256,
                "v": 1,
            },
        },
        "replay_pack": _detached_object(
            predecessor["replay_pack"], "predecessor replay pack"
        ),
        "repository": _detached_object(
            predecessor["repository"], "predecessor repository"
        ),
        "retrieval_eligible": False,
        "schema": epoch_metadata_v2_schema_identity(),
        "status": STATUS,
        "supersession": {
            "added_receipts": [
                "selected_explicit_api",
                "selected_defined_api",
                "selected_definition_use",
            ],
            "kind": "full-candidate-successor-ledger",
            "predecessor_id": predecessor["id"],
            "preserved_evidence": [
                "replay_pack",
                "repository",
                "theorem_semantics",
                "proofs",
                "source_locators",
                "atlas_receipts",
                "vault_receipts",
                "deployed_page_statuses",
                "unresolved_authority_gaps",
            ],
            "status": "candidate-successor",
        },
        "theorem_count": count,
        "theorem_records": theorem_records,
        "training_eligible": False,
        "v": METADATA_VERSION,
    }
    return body, theorem_rows


def _with_root(
    body: Mapping[str, object], theorem_rows: list[dict[str, object]]
) -> dict[str, object]:
    detached_body = _detached_object(body, "metadata-v2 body")
    theorem_root = detached_body["theorem_records"]["root_sha256"]
    preimage = {
        "format": METADATA_ROOT_PREIMAGE_FORMAT,
        "payload": {
            "body": detached_body,
            "theorem_record_root_sha256": theorem_root,
        },
        "v": METADATA_VERSION,
    }
    return {
        **detached_body,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "theorems": _detached(theorem_rows, "metadata-v2 theorem rows"),
    }


def _validate_shape(value: object) -> dict[str, object]:
    metadata = _detached_object(value, "library epoch metadata-v2")
    _require_fields("library epoch metadata-v2", metadata, _METADATA_FIELDS)
    if not all(
        (
            metadata.get("format") == METADATA_FORMAT,
            metadata.get("id") == METADATA_ID,
            metadata.get("v") == METADATA_VERSION,
            metadata.get("status") == STATUS,
            metadata.get("logic_mode") == LOGIC_MODE,
            metadata.get("freeze_ready") is False,
            metadata.get("training_eligible") is False,
            metadata.get("retrieval_eligible") is False,
            metadata.get("evaluation_eligible") is False,
            metadata.get("theorem_count") == THEOREM_COUNT,
        )
    ):
        raise LibraryEpochMetadataV2Error("metadata-v2 constants are malformed")
    rows = metadata.get("theorems")
    if type(rows) is not list or len(rows) != THEOREM_COUNT:
        raise LibraryEpochMetadataV2Error("metadata-v2 theorem rows are malformed")
    identities = []
    for index, row in enumerate(rows):
        theorem = _require_fields("metadata-v2 theorem", row, _THEOREM_FIELDS)
        if (
            theorem.get("index") != theorem.get("declaration_order")
            or theorem.get("index") != index
            or theorem.get("record_sha256") != _record_hash(theorem)
        ):
            raise LibraryEpochMetadataV2Error("metadata-v2 theorem identity is malformed")
        presentation = theorem.get("presentation")
        if (
            type(presentation) is not dict
            or presentation.get("authority") != "historical-non-authoritative"
            or presentation.get("deployed_defined_page_status")
            not in _PRESENTATION_STATUSES
            or presentation.get("deployed_explicit_page_status")
            not in _PRESENTATION_STATUSES
        ):
            raise LibraryEpochMetadataV2Error("presentation status is malformed")
        definitions = theorem.get("definitions")
        if type(definitions) is not dict:
            raise LibraryEpochMetadataV2Error("definition receipt is malformed")
        use_preimage = definitions.get("definition_use_preimage")
        if (
            type(use_preimage) is not dict
            or set(use_preimage) != {"format", "uses", "v"}
            or use_preimage.get("format") != DEFINITION_USE_PREIMAGE_FORMAT
            or use_preimage.get("v") != METADATA_VERSION
            or definitions.get("definition_use_receipt_sha256")
            != _sha256_json(use_preimage)
        ):
            raise LibraryEpochMetadataV2Error("definition-use receipt is malformed")
        identities.append(
            {
                "index": index,
                "name": theorem["name"],
                "record_sha256": theorem["record_sha256"],
            }
        )
    theorem_preimage = {
        "format": THEOREM_RECORDS_PREIMAGE_FORMAT,
        "records": identities,
        "v": METADATA_VERSION,
    }
    expected_theorem_records = {
        "count": THEOREM_COUNT,
        "preimage": theorem_preimage,
        "root_sha256": _sha256_json(theorem_preimage),
    }
    if metadata.get("theorem_records") != expected_theorem_records:
        raise LibraryEpochMetadataV2Error("theorem record root is malformed")
    body = {
        key: item
        for key, item in metadata.items()
        if key not in {"root_preimage", "root_sha256", "theorems"}
    }
    expected_root_preimage = {
        "format": METADATA_ROOT_PREIMAGE_FORMAT,
        "payload": {
            "body": body,
            "theorem_record_root_sha256": expected_theorem_records["root_sha256"],
        },
        "v": METADATA_VERSION,
    }
    if (
        metadata.get("root_preimage") != expected_root_preimage
        or metadata.get("root_sha256") != _sha256_json(expected_root_preimage)
    ):
        raise LibraryEpochMetadataV2Error("metadata-v2 root is malformed")
    return metadata


def _build_candidate_epoch_metadata_v2(
    *, repository_root: Path | None = None
) -> dict[str, object]:
    """Perform one complete fixed-source construction and root validation."""

    root = _repository_root(repository_root)
    body, rows = _candidate_body(root)
    return _validate_shape(_with_root(body, rows))


def build_candidate_epoch_metadata_v2(
    *, repository_root: Path | None = None
) -> dict[str, object]:
    """Build, but do not retain, the exact candidate successor ledger."""

    return _build_candidate_epoch_metadata_v2(repository_root=repository_root)


def validate_epoch_metadata_v2(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate shape, all roots, and exact deterministic reconstruction."""

    actual = _validate_shape(value)
    expected = _build_candidate_epoch_metadata_v2(repository_root=repository_root)
    if _canonical_json_bytes(actual) != _canonical_json_bytes(expected):
        raise LibraryEpochMetadataV2Error(
            "metadata-v2 differs from exact predecessor and selected bundle"
        )
    return actual


def load_epoch_metadata_v2(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one bounded canonical no-follow ledger and validate it."""

    if not isinstance(path, Path):
        raise TypeError("metadata-v2 path must be a pathlib.Path")
    safe_path = _safe_external_file(path)
    raw = _read_bounded_regular_file(
        safe_path, label="library epoch metadata-v2", limit=MAX_METADATA_BYTES
    )
    value = _decode_canonical_document(
        raw, "library epoch metadata-v2", limit=MAX_METADATA_BYTES
    )
    return validate_epoch_metadata_v2(value, repository_root=repository_root)


def _readiness_projection_from_validated_v2(
    value: Mapping[str, object],
) -> dict[str, object]:
    """Project bytes only from complete construction or fixed-source validation."""

    return {
        "declared_dependency_edges": value["aggregate"][
            "declared_dependency_edges"
        ],
        "deployed_page_documentation_complete_count": value["aggregate"][
            "deployed_page_documentation_complete_count"
        ],
        "evaluation_eligible": False,
        "format": READINESS_FORMAT,
        "freeze_ready": False,
        "gaps": value["gaps"],
        "manifest_root_sha256": value["replay_pack"]["manifest_root_sha256"],
        "metadata_artifact_sha256": _sha256_bytes(
            canonical_document_bytes(value)
        ),
        "metadata_root_sha256": value["root_sha256"],
        "predecessor_metadata_root_sha256": value["predecessor"]["ledger"][
            "root_sha256"
        ],
        "replay_root_sha256": value["replay_pack"]["replay_root_sha256"],
        "retrieval_eligible": False,
        "selected_api_documentation_complete_count": value["aggregate"][
            "selected_api_documentation_complete_count"
        ],
        "selected_bundle_root_sha256": value["documentation_sources"][
            "selected_bundle"
        ]["manifest"]["root_sha256"],
        "status": STATUS,
        "theorem_count": value["theorem_count"],
        "theorem_record_root_sha256": value["theorem_records"]["root_sha256"],
        "training_eligible": False,
        "v": METADATA_VERSION,
    }


def _build_candidate_epoch_metadata_v2_with_readiness(
    *, repository_root: Path | None = None
) -> tuple[dict[str, object], dict[str, object]]:
    """Build exact pinned evidence once and return its readiness projection."""

    metadata = _build_candidate_epoch_metadata_v2(
        repository_root=repository_root
    )
    return metadata, _readiness_projection_from_validated_v2(metadata)


def readiness_report_v2(
    metadata: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Return readiness only after complete fixed-source reconstruction."""

    value = validate_epoch_metadata_v2(metadata, repository_root=repository_root)
    return _readiness_projection_from_validated_v2(value)


__all__ = [
    "LibraryEpochMetadataV2Error",
    "epoch_metadata_v2_schema",
    "epoch_metadata_v2_schema_identity",
    "canonical_document_bytes",
    "build_candidate_epoch_metadata_v2",
    "validate_epoch_metadata_v2",
    "load_epoch_metadata_v2",
    "readiness_report_v2",
]
