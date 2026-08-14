"""Candidate-only H1.1 metadata for the retained Peano library replay pack.

This module joins immutable replay evidence to source and documentation
receipts.  It deliberately cannot freeze a library epoch: every document it
builds has ``status = candidate``, ``freeze_ready = false``, and
``evaluation_eligible = false``.  Missing review, lineage, dependency, and
minimality evidence is represented as data rather than inferred away.
"""

from __future__ import annotations

import ast
import hashlib
import html
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping
import warnings

from training.peano_hydra.library_replay_pack import (
    LibraryReplayPackError,
    validate_replay_pack_manifest,
)


EPOCH_METADATA_SCHEMA_FORMAT = "peano-hydra-library-epoch-metadata-schema"
EPOCH_METADATA_SCHEMA_VERSION = 1
EPOCH_METADATA_SCHEMA_ID = "peano-hydra-library-epoch-metadata-v1"
EPOCH_METADATA_SCHEMA_PATH = Path(__file__).with_name(
    "library-epoch-metadata-schema-v1.json"
)
EPOCH_METADATA_SCHEMA_SHA256 = (
    "71995b59d4f5592a08a90dc354a91888f5f1f6f89ec4428be291aea19e76062c"
)

EPOCH_METADATA_FORMAT = "peano-hydra-library-epoch-metadata"
EPOCH_METADATA_VERSION = 1
EPOCH_METADATA_ID = "authoring-library-epoch-metadata-candidate-v1"
EPOCH_METADATA_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-epoch-metadata-root-preimage"
)
READINESS_REPORT_FORMAT = "peano-hydra-library-epoch-metadata-readiness"

STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
SOURCE_COMMIT = "32803924d7def862ccf0b738cd1ed494a3165f7e"
SOURCE_TREE = "e945e4963ad53b1c07008fd8356980bdacc3bafe"
REPOSITORY_URL = "https://github.com/nasqret/vietnam2026"
REPLAY_MANIFEST_ARTIFACT_SHA256 = (
    "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
)
REPLAY_MANIFEST_ROOT_SHA256 = (
    "fe6718465fbb5e89154ccfce5c511b51ee296b21568d1759a00dda8a21f8a25d"
)
REPLAY_ROOT_SHA256 = (
    "88e39a886949e2ef31220397e529871bc907f9cd9311c27dc97710d12ef1e3ba"
)
REPLAY_REPORT_ARTIFACT_SHA256 = (
    "35f5547978a4d58c5af30c33d253c92af494b94f6d6500a866a13f2fd1fa7f10"
)
REPLAY_CATALOG_ARTIFACT_SHA256 = (
    "326ffe660da6e34a3aa12e0aa13096078a0bf20c45c440049aaf5d5bed1f1be7"
)
EXPLICIT_EXPLORER_SCHEMA = "peano-lab-pa-proof-corpus-v1"
EXPLICIT_EXPLORER_SOURCE_SHA256 = (
    "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1"
)
EXPLICIT_EXPLORER_GRAPH_SHA256 = (
    "98a36450cfe1de29c20be67a1c5f65c8064e9f9eec5368ab769065f910008698"
)
DEFINED_EXPLORER_SCHEMA = "peano-lab-pa-defined-corpus-v1"
DEFINED_EXPLORER_EDITION_SHA256 = (
    "9b7c7928ddd3e1930fb5eca6e6b6c4b5ce6978633f6f187525d8813c90f3ddd6"
)

MAX_SCHEMA_BYTES = 1_000_000
MAX_METADATA_BYTES = 16_000_000
MAX_REPLAY_MANIFEST_BYTES = 8_000_000
MAX_REPLAY_REPORT_BYTES = 1_000_000
MAX_SOURCE_FILE_BYTES = 8_000_000
MAX_ATLAS_BYTES = 8_000_000
MAX_DOCUMENTATION_CORPUS_BYTES = 64_000_000
MAX_VAULT_FILE_BYTES = 2_000_000
MAX_THEOREMS = 10_000
MAX_JSON_DEPTH = 192
MAX_JSON_ITEMS = 3_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_REPLAY_PACK_RELATIVE = Path("artifacts/peano-hydra/l0-replay-candidate-v1")
_REPLAY_REPORT_RELATIVE = Path(
    "artifacts/peano-hydra/l0-replay-candidate-v1-report.json"
)
_ATLAS_RELATIVE = Path("book/arithmetic-library/theorem-atlas.md")
_VAULT_RELATIVE = Path("vault/lemmas")
_EXPLICIT_EXPLORER_RELATIVE = Path(
    "book/_static/pa-proof-explorer/api/corpus.json"
)
_DEFINED_EXPLORER_RELATIVE = Path(
    "book/_static/pa-proof-explorer/defined/api/corpus.json"
)

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_THEOREM_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,127}")
_VAULT_DEPENDENCY_RE = re.compile(r"^- \[\[([a-z][a-z0-9_]{0,127})\]\]$", re.M)
_ATLAS_COMMIT_RE = re.compile(
    r"https://github\.com/nasqret/vietnam2026/blob/([0-9a-f]{40})/"
)

_SCHEMA_IDENTITY_FIELDS = frozenset(
    {"artifact_sha256", "format", "id", "sha256", "v"}
)
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
        "replay_pack",
        "repository",
        "root_preimage",
        "root_sha256",
        "schema",
        "status",
        "theorem_count",
        "theorems",
        "v",
    }
)
_ROOT_PREIMAGE_FIELDS = frozenset({"format", "payload", "v"})
_AGGREGATE_FIELDS = frozenset(
    {
        "declared_dependency_edges",
        "documentation_complete_count",
        "source_locator_count",
        "theorem_count",
    }
)
_GAP_FIELDS = frozenset(
    {
        "atlas_missing_count",
        "atlas_stale_count",
        "defined_explorer_missing_count",
        "defined_explorer_stale_count",
        "definition_receipt_missing_count",
        "definition_receipt_stale_count",
        "explicit_explorer_missing_count",
        "explicit_explorer_stale_count",
        "human_review_pending_count",
        "lineage_pending_count",
        "optimized_best_known_pending_count",
        "optimized_dependency_vectors_pending_count",
        "publication_union_pending_count",
        "readable_dependency_vectors_unverified_count",
        "source_locator_missing_count",
        "vault_missing_count",
        "vault_stale_count",
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
        "proof",
        "readable_proof",
        "source",
        "statement",
    }
)
_RECEIPT_STATUSES = frozenset({"missing", "present", "stale"})

_GENERATED_SMALL_MODULI = {
    "lt__cases": ("lt_five_cases", "lt_seven_cases"),
    "bounded_square_mod_classify": (
        "bounded_square_mod3_classify",
        "bounded_square_mod5_classify",
        "bounded_square_mod7_classify",
    ),
    "qres_mod_": (
        "qres_mod3_zero",
        "qres_mod3_one",
        "qres_mod5_zero",
        "qres_mod5_one",
        "qres_mod5_four",
        "qres_mod7_zero",
        "qres_mod7_one",
        "qres_mod7_two",
        "qres_mod7_four",
    ),
    "qres_mod_canonical_iff": (
        "qres_mod3_canonical_iff",
        "qres_mod5_canonical_iff",
        "qres_mod7_canonical_iff",
    ),
    "not_qres_mod_": (
        "not_qres_mod3_two",
        "not_qres_mod5_two",
        "not_qres_mod5_three",
        "not_qres_mod7_three",
        "not_qres_mod7_five",
        "not_qres_mod7_six",
    ),
}


class LibraryEpochMetadataError(ValueError):
    """The candidate epoch metadata or one of its inputs is malformed."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryEpochMetadataError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise LibraryEpochMetadataError(f"forbidden JSON constant {value!r}")


def _reject_float(value: str) -> object:
    raise LibraryEpochMetadataError(
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
        raise LibraryEpochMetadataError("JSON exceeds the nesting limit")
    if active is None:
        active = set()
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_JSON_ITEMS:
        raise LibraryEpochMetadataError("JSON exceeds the item limit")
    if value is None or type(value) in (bool, str):
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_JSON_INTEGER:
            raise LibraryEpochMetadataError("JSON integer exceeds the safe domain")
        return
    if type(value) not in (list, dict):
        raise LibraryEpochMetadataError("value is outside strict JSON")
    identity = id(value)
    if identity in active:
        raise LibraryEpochMetadataError("cyclic JSON value is forbidden")
    active.add(identity)
    try:
        values = value if type(value) is list else value.values()
        if type(value) is dict and not all(type(key) is str for key in value):
            raise LibraryEpochMetadataError("JSON object key must be text")
        for item in values:
            _validate_json_value(
                item, depth=depth + 1, active=active, counter=counter
            )
    finally:
        active.remove(identity)


def _canonical_json_bytes(value: object, *, limit: int = MAX_METADATA_BYTES) -> bytes:
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
        raise LibraryEpochMetadataError(f"value is not canonical JSON: {exc}") from None
    if len(raw) > limit:
        raise LibraryEpochMetadataError(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def canonical_document_bytes(
    value: object, *, limit: int = MAX_METADATA_BYTES
) -> bytes:
    """Return the unique retained UTF-8 representation of a JSON value."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
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
        raise LibraryEpochMetadataError(f"value is not canonical JSON: {exc}") from None
    if len(raw) > limit:
        raise LibraryEpochMetadataError(
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
    except LibraryEpochMetadataError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryEpochMetadataError(f"{label} is not strict JSON: {exc}") from None


def _decode_canonical_document(
    raw: bytes, label: str, *, limit: int
) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryEpochMetadataError(f"{label} must be bounded exact bytes")
    value = _decode_json(raw, label)
    if type(value) is not dict:
        raise LibraryEpochMetadataError(f"{label} must be one JSON object")
    if canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryEpochMetadataError(f"{label} is not a canonical JSON document")
    return value


def _detached_object(value: object, label: str) -> dict[str, object]:
    raw = _canonical_json_bytes(value)
    result = _decode_json(raw, label)
    if type(result) is not dict:
        raise LibraryEpochMetadataError(f"{label} must be one JSON object")
    return result


def _require_fields(
    label: str, value: object, expected: frozenset[str]
) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        raise LibraryEpochMetadataError(f"{label} has missing or additional fields")
    return value


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryEpochMetadataError(f"{label} must be one lowercase SHA-256")
    return value


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("bounded file limit must be a positive exact integer")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryEpochMetadataError(f"cannot read {label}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise LibraryEpochMetadataError(f"{label} must be a regular file")
        if before.st_size > limit:
            raise LibraryEpochMetadataError(f"{label} exceeds the {limit}-byte limit")
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
            raise LibraryEpochMetadataError(f"{label} changed while it was read")
        if len(raw) > limit or len(raw) != before.st_size:
            raise LibraryEpochMetadataError(f"{label} exceeds or disagrees with its size")
        return raw
    except OSError as exc:
        raise LibraryEpochMetadataError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def epoch_metadata_schema() -> dict[str, object]:
    """Load and pin the canonical H1.1a metadata schema."""

    raw = _read_bounded_regular_file(
        EPOCH_METADATA_SCHEMA_PATH,
        label="library epoch metadata schema",
        limit=MAX_SCHEMA_BYTES,
    )
    schema = _decode_canonical_document(
        raw, "library epoch metadata schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        schema.get("format") != EPOCH_METADATA_SCHEMA_FORMAT
        or schema.get("id") != EPOCH_METADATA_SCHEMA_ID
        or schema.get("v") != EPOCH_METADATA_SCHEMA_VERSION
    ):
        raise LibraryEpochMetadataError("library epoch metadata schema identity drifted")
    if _sha256_json(schema, limit=MAX_SCHEMA_BYTES) != EPOCH_METADATA_SCHEMA_SHA256:
        raise LibraryEpochMetadataError("library epoch metadata schema digest drifted")
    expected_limits = {
        "atlas_bytes": MAX_ATLAS_BYTES,
        "documentation_corpus_bytes": MAX_DOCUMENTATION_CORPUS_BYTES,
        "metadata_bytes": MAX_METADATA_BYTES,
        "metadata_json_depth": MAX_JSON_DEPTH,
        "metadata_json_items": MAX_JSON_ITEMS,
        "replay_manifest_bytes": MAX_REPLAY_MANIFEST_BYTES,
        "replay_report_bytes": MAX_REPLAY_REPORT_BYTES,
        "schema_bytes": MAX_SCHEMA_BYTES,
        "source_file_bytes": MAX_SOURCE_FILE_BYTES,
        "theorem_count": MAX_THEOREMS,
        "vault_file_bytes": MAX_VAULT_FILE_BYTES,
    }
    if schema.get("limits") != expected_limits:
        raise LibraryEpochMetadataError("library epoch metadata schema limits drifted")
    return _detached_object(schema, "library epoch metadata schema")


def epoch_metadata_schema_identity() -> dict[str, object]:
    """Return both the semantic and exact-file identities of the schema."""

    schema = epoch_metadata_schema()
    return {
        "artifact_sha256": _sha256_bytes(
            canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
        ),
        "format": EPOCH_METADATA_SCHEMA_FORMAT,
        "id": EPOCH_METADATA_SCHEMA_ID,
        "sha256": EPOCH_METADATA_SCHEMA_SHA256,
        "v": EPOCH_METADATA_SCHEMA_VERSION,
    }


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository root must be a pathlib.Path")
    try:
        metadata = root.lstat()
        if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            raise LibraryEpochMetadataError(
                "repository root must be a non-symlink directory"
            )
        return root.resolve(strict=True)
    except OSError as exc:
        raise LibraryEpochMetadataError("cannot resolve repository root") from exc


def _load_document(path: Path, label: str, limit: int) -> tuple[bytes, dict[str, object]]:
    raw = _read_bounded_regular_file(path, label=label, limit=limit)
    return raw, _decode_canonical_document(raw, label, limit=limit)


def _source_locators(
    root: Path, catalog: Mapping[str, object], theorem_names: set[str]
) -> dict[str, dict[str, object]]:
    source_rows = catalog.get("theorem_sources")
    if type(source_rows) is not list:
        raise LibraryEpochMetadataError("packed catalog source manifest is malformed")
    result: dict[str, dict[str, object]] = {}
    for source_row in source_rows:
        if type(source_row) is not dict or set(source_row) != {"path", "sha256"}:
            raise LibraryEpochMetadataError("packed catalog source row is malformed")
        relative = source_row.get("path")
        expected_sha = source_row.get("sha256")
        if type(relative) is not str:
            raise LibraryEpochMetadataError("packed catalog source path is malformed")
        _require_sha256("packed catalog source hash", expected_sha)
        path = root / relative
        raw = _read_bounded_regular_file(
            path, label=f"theorem source {relative!r}", limit=MAX_SOURCE_FILE_BYTES
        )
        if _sha256_bytes(raw) != expected_sha:
            raise LibraryEpochMetadataError(
                f"theorem source {relative!r} differs from the replay snapshot"
            )
        try:
            # Several exact historical theorem strings contain ``\/`` in
            # ordinary Python literals.  Python warns while compiling those
            # pinned bytes even though the AST and runtime text are stable;
            # the warning is not a metadata defect and must not leak into
            # warning-as-error validation runs.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(raw.decode("utf-8"), filename=relative)
        except (UnicodeDecodeError, SyntaxError) as exc:
            raise LibraryEpochMetadataError(
                f"theorem source {relative!r} is not valid pinned Python"
            ) from exc
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not isinstance(node.func, ast.Name) or node.func.id not in {
                "TheoremSpec",
                "spec",
            }:
                continue
            name_node: ast.expr | None = node.args[0] if node.args else None
            if name_node is None:
                name_node = next(
                    (item.value for item in node.keywords if item.arg == "name"),
                    None,
                )
            names: tuple[str, ...]
            kind = "declaration"
            if isinstance(name_node, ast.Constant) and isinstance(name_node.value, str):
                names = (name_node.value,)
            else:
                fragments = "".join(
                    item.value
                    for item in getattr(name_node, "values", ())
                    if isinstance(item, ast.Constant) and isinstance(item.value, str)
                )
                if (
                    path.name == "qr_small_moduli.py"
                    and isinstance(name_node, ast.JoinedStr)
                    and fragments in _GENERATED_SMALL_MODULI
                ):
                    names = _GENERATED_SMALL_MODULI[fragments]
                    kind = "generated-factory"
                else:
                    raise LibraryEpochMetadataError(
                        f"TheoremSpec in {relative!r} at line {node.lineno} "
                        "has no reviewed literal or finite generated name"
                    )
            for name in names:
                if name in theorem_names and name not in result:
                    result[name] = {
                        "file_sha256": expected_sha,
                        "kind": kind,
                        "line": node.lineno,
                        "path": relative,
                        "status": "present",
                    }
    return result


def _rows_by_name(value: object, label: str) -> dict[str, list[dict[str, object]]]:
    if type(value) is not list:
        raise LibraryEpochMetadataError(f"{label} theorem rows are malformed")
    result: dict[str, list[dict[str, object]]] = {}
    for row in value:
        if type(row) is not dict or type(row.get("name")) is not str:
            raise LibraryEpochMetadataError(f"{label} theorem row is malformed")
        result.setdefault(row["name"], []).append(row)
    return result


def _explorer_row(
    grouped: Mapping[str, list[dict[str, object]]], name: str
) -> tuple[str, dict[str, object] | None]:
    rows = grouped.get(name, [])
    if not rows:
        return "missing", None
    public = [
        row
        for row in rows
        if row.get("scope") == "public" and row.get("status") == "public"
    ]
    if len(public) == 1:
        return "present", public[0]
    # A named authoring row is evidence that the explorer has a record but not
    # an admissible public receipt.  Keep that distinct from physical absence.
    return "stale", None if not public else public[0]


def _receipt(
    *,
    artifact_path: str,
    artifact_sha256: str,
    status: str,
    record: object | None,
) -> dict[str, object]:
    if status not in _RECEIPT_STATUSES:
        raise LibraryEpochMetadataError("receipt status is malformed")
    return {
        "artifact_path": artifact_path,
        "artifact_sha256": artifact_sha256,
        "record_sha256": None if record is None else _sha256_json(record),
        "status": status,
    }


def _atlas_records(raw: bytes) -> tuple[str, dict[str, str]]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise LibraryEpochMetadataError("theorem atlas is not UTF-8") from exc
    commits = set(_ATLAS_COMMIT_RE.findall(text))
    source_commit = next(iter(commits)) if len(commits) == 1 else "mixed-or-absent"
    records: dict[str, str] = {}
    marker = '<article class="pa-theorem-card" id="theorem-'
    position = 0
    while True:
        start = text.find(marker, position)
        if start < 0:
            break
        name_start = start + len(marker)
        name_end = text.find('"', name_start)
        end = text.find("</article>", name_end)
        if name_end < 0 or end < 0:
            raise LibraryEpochMetadataError("theorem atlas card is unterminated")
        name = text[name_start:name_end]
        if _THEOREM_NAME_RE.fullmatch(name) is None or name in records:
            raise LibraryEpochMetadataError("theorem atlas card name is malformed")
        records[name] = text[start : end + len("</article>")]
        position = end + len("</article>")
    return source_commit, records


def _atlas_receipt(
    row: Mapping[str, object],
    source: Mapping[str, object],
    *,
    atlas_sha: str,
    atlas_commit: str,
    records: Mapping[str, str],
) -> dict[str, object]:
    name = row["name"]
    record = records.get(name)
    status = "missing" if record is None else "present"
    if record is not None:
        expected_fragments = (
            f'data-name="{html.escape(name, quote=True)}"',
            html.escape(row["statement_source"], quote=True),
            html.escape(row["summary"], quote=True),
            f'/{source["path"]}#L{source["line"]}">',
        )
        if atlas_commit != SOURCE_COMMIT or not all(
            fragment in record for fragment in expected_fragments
        ):
            status = "stale"
    joined = None
    if record is not None:
        joined = {
            "article_sha256": _sha256_bytes(record.encode("utf-8")),
            "name": name,
            "source_commit": atlas_commit,
            "source_line": source["line"],
            "source_path": source["path"],
        }
    return _receipt(
        artifact_path=str(_ATLAS_RELATIVE),
        artifact_sha256=atlas_sha,
        status=status,
        record=joined,
    )


def _vault_receipt(
    root: Path, row: Mapping[str, object]
) -> tuple[dict[str, object], dict[str, object]]:
    relative = _VAULT_RELATIVE / f"{row['name']}.md"
    path = root / relative
    try:
        raw = _read_bounded_regular_file(
            path, label=f"vault note {row['name']!r}", limit=MAX_VAULT_FILE_BYTES
        )
    except LibraryEpochMetadataError:
        receipt = _receipt(
            artifact_path=str(relative),
            artifact_sha256="0" * 64,
            status="missing",
            record=None,
        )
        return receipt, {"name": row["name"], "sha256": None, "status": "missing"}
    digest = _sha256_bytes(raw)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = ""
    dependencies_section = ""
    match = re.search(r"^## Dependencies\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if match is not None:
        dependencies_section = match.group(1)
    found_dependencies = _VAULT_DEPENDENCY_RE.findall(dependencies_section)
    expected_dependencies = row["declared_dependencies"]
    status = "present"
    if not all(
        (
            f"# `{row['name']}`" in text,
            row["summary"] in text,
            f"```text\n{row['statement_source']}\n```" in text,
            found_dependencies == expected_dependencies,
        )
    ):
        status = "stale"
    joined = {
        "declared_dependencies": found_dependencies,
        "name": row["name"],
        "statement_source_sha256": row["statement_source_sha256"],
        "summary_sha256": _sha256_bytes(row["summary"].encode("utf-8")),
        "vault_file_sha256": digest,
    }
    receipt = _receipt(
        artifact_path=str(relative),
        artifact_sha256=digest,
        status=status,
        record=joined,
    )
    return receipt, {"name": row["name"], "sha256": digest, "status": status}


def _explicit_receipt(
    row: Mapping[str, object],
    grouped: Mapping[str, list[dict[str, object]]],
    *,
    artifact_sha: str,
) -> dict[str, object]:
    status, record = _explorer_row(grouped, row["name"])
    if record is not None and status == "present":
        script = [item.get("text") for item in record.get("lines", [])]
        dependencies = [
            item.get("name") if type(item) is dict else item
            for item in record.get("dependencies", [])
        ]
        if not all(
            (
                record.get("statement") == row["statement_source"],
                record.get("statement_sha256") == row["statement_source_sha256"],
                dependencies == row["declared_dependencies"],
                record.get("summary") == row["summary"],
                script == row["script"],
            )
        ):
            status = "stale"
    return _receipt(
        artifact_path=str(_EXPLICIT_EXPLORER_RELATIVE),
        artifact_sha256=artifact_sha,
        status=status,
        record=record,
    )


def _defined_receipt(
    row: Mapping[str, object],
    grouped: Mapping[str, list[dict[str, object]]],
    *,
    artifact_sha: str,
    edition_identity: str,
) -> tuple[dict[str, object], dict[str, object]]:
    status, record = _explorer_row(grouped, row["name"])
    if record is not None and status == "present":
        defined = record.get("defined")
        dependencies = [
            item.get("name") if type(item) is dict else item
            for item in record.get("dependencies", [])
        ]
        if not all(
            (
                record.get("explicit_statement") == row["statement_source"],
                record.get("explicit_statement_sha256")
                == row["statement_source_sha256"],
                dependencies == row["declared_dependencies"],
                record.get("summary") == row["summary"],
                type(defined) is dict,
                type(defined) is dict
                and defined.get("expanded_statement_sha256")
                == row["statement_source_sha256"],
                type(defined) is dict and defined.get("name") == row["name"],
            )
        ):
            status = "stale"
    receipt = _receipt(
        artifact_path=str(_DEFINED_EXPLORER_RELATIVE),
        artifact_sha256=artifact_sha,
        status=status,
        record=record,
    )
    definition = {
        "edition_identity_sha256": edition_identity,
        "record_sha256": receipt["record_sha256"],
        "status": status,
    }
    return receipt, definition


def _validate_replay_report(
    report: Mapping[str, object], manifest: Mapping[str, object]
) -> None:
    expected_fields = {
        "artifact_bytes_total",
        "format",
        "kernel_checked_count",
        "logic_mode",
        "manifest_root_sha256",
        "replay_root_sha256",
        "status",
        "theorem_count",
        "v",
        "worker_isolation",
    }
    if set(report) != expected_fields:
        raise LibraryEpochMetadataError("retained replay report fields are malformed")
    if not all(
        (
            report.get("format") == "peano-hydra-library-replay-verification",
            report.get("v") == 1,
            report.get("status") == "passed",
            report.get("logic_mode") == LOGIC_MODE,
            report.get("manifest_root_sha256") == manifest["root_sha256"],
            report.get("replay_root_sha256") == manifest["replay_root_sha256"],
            report.get("theorem_count") == manifest["theorem_count"],
            report.get("kernel_checked_count") == manifest["theorem_count"],
            report.get("artifact_bytes_total")
            == manifest["aggregate"]["artifact_bytes_total"],
        )
    ):
        raise LibraryEpochMetadataError("retained replay report is not bound to the pack")
    isolation = report.get("worker_isolation")
    if (
        type(isolation) is not dict
        or isolation.get("fresh_repo_pycache") is not True
        or isolation.get("python_isolated_mode") is not True
        or isolation.get("python_no_site") is not True
        or isolation.get("forbidden_modules_loaded") != []
    ):
        raise LibraryEpochMetadataError("retained replay report lacks isolation evidence")


def _candidate_body(root: Path) -> dict[str, object]:
    schema_identity = epoch_metadata_schema_identity()
    replay_root = root / _REPLAY_PACK_RELATIVE
    manifest_raw, manifest_value = _load_document(
        replay_root / "manifest.json",
        "retained replay manifest",
        MAX_REPLAY_MANIFEST_BYTES,
    )
    try:
        manifest = validate_replay_pack_manifest(manifest_value)
    except LibraryReplayPackError as exc:
        raise LibraryEpochMetadataError(f"retained replay manifest is invalid: {exc}") from None
    if (
        _sha256_bytes(manifest_raw) != REPLAY_MANIFEST_ARTIFACT_SHA256
        or manifest.get("root_sha256") != REPLAY_MANIFEST_ROOT_SHA256
        or manifest.get("replay_root_sha256") != REPLAY_ROOT_SHA256
    ):
        raise LibraryEpochMetadataError(
            "retained replay manifest differs from the pinned source snapshot"
        )
    report_raw, report = _load_document(
        root / _REPLAY_REPORT_RELATIVE,
        "retained replay verification report",
        MAX_REPLAY_REPORT_BYTES,
    )
    if _sha256_bytes(report_raw) != REPLAY_REPORT_ARTIFACT_SHA256:
        raise LibraryEpochMetadataError(
            "retained replay report differs from the pinned source snapshot"
        )
    _validate_replay_report(report, manifest)
    catalog_raw, catalog = _load_document(
        replay_root / "catalog.json", "packed source catalog", MAX_REPLAY_MANIFEST_BYTES
    )
    if (
        _sha256_bytes(catalog_raw) != REPLAY_CATALOG_ARTIFACT_SHA256
        or manifest["source_catalog"]["artifact_sha256"]
        != REPLAY_CATALOG_ARTIFACT_SHA256
    ):
        raise LibraryEpochMetadataError("packed source catalog digest differs from manifest")
    rows = manifest["theorems"]
    if type(rows) is not list or len(rows) != 384:
        raise LibraryEpochMetadataError("H1.1a expects the exact 384-theorem replay pack")
    theorem_names = {row["name"] for row in rows}
    locators = _source_locators(root, catalog, theorem_names)

    atlas_raw = _read_bounded_regular_file(
        root / _ATLAS_RELATIVE, label="theorem atlas", limit=MAX_ATLAS_BYTES
    )
    atlas_sha = _sha256_bytes(atlas_raw)
    atlas_commit, atlas_records = _atlas_records(atlas_raw)

    explicit_raw, explicit = _load_document(
        root / _EXPLICIT_EXPLORER_RELATIVE,
        "explicit proof explorer corpus",
        MAX_DOCUMENTATION_CORPUS_BYTES,
    )
    defined_raw, defined = _load_document(
        root / _DEFINED_EXPLORER_RELATIVE,
        "defined proof explorer corpus",
        MAX_DOCUMENTATION_CORPUS_BYTES,
    )
    explicit_sha = _sha256_bytes(explicit_raw)
    defined_sha = _sha256_bytes(defined_raw)
    if (
        explicit.get("schema") != EXPLICIT_EXPLORER_SCHEMA
        or explicit.get("source_sha256") != EXPLICIT_EXPLORER_SOURCE_SHA256
        or explicit.get("graph_sha256") != EXPLICIT_EXPLORER_GRAPH_SHA256
        or explicit.get("theorem_count") != 557
        or explicit.get("public_count") != 240
        or type(explicit.get("theorems")) is not list
        or len(explicit["theorems"]) != 557
    ):
        raise LibraryEpochMetadataError(
            "explicit explorer corpus identity is malformed"
        )
    if (
        defined.get("schema") != DEFINED_EXPLORER_SCHEMA
        or defined.get("edition_identity_sha256")
        != DEFINED_EXPLORER_EDITION_SHA256
        or defined.get("explicit_corpus_sha256") != explicit_sha
        or defined.get("theorem_count") != 557
        or type(defined.get("theorems")) is not list
        or len(defined["theorems"]) != 557
    ):
        raise LibraryEpochMetadataError("defined explorer corpus identity is malformed")
    explicit_grouped = _rows_by_name(explicit.get("theorems"), "explicit explorer")
    defined_grouped = _rows_by_name(defined.get("theorems"), "defined explorer")
    edition_identity = _require_sha256(
        "defined explorer edition identity", defined.get("edition_identity_sha256")
    )

    theorem_records: list[dict[str, object]] = []
    vault_root_rows: list[dict[str, object]] = []
    for index, replay_row in enumerate(rows):
        name = replay_row["name"]
        source = locators.get(name)
        if source is None:
            source = {
                "file_sha256": "0" * 64,
                "kind": "unresolved",
                "line": 0,
                "path": "",
                "status": "missing",
            }
        atlas_receipt = _atlas_receipt(
            replay_row,
            source,
            atlas_sha=atlas_sha,
            atlas_commit=atlas_commit,
            records=atlas_records,
        )
        vault_receipt, vault_root_row = _vault_receipt(root, replay_row)
        vault_root_rows.append(vault_root_row)
        explicit_receipt = _explicit_receipt(
            replay_row, explicit_grouped, artifact_sha=explicit_sha
        )
        defined_receipt, definition = _defined_receipt(
            replay_row,
            defined_grouped,
            artifact_sha=defined_sha,
            edition_identity=edition_identity,
        )
        explanation = replay_row["summary"]
        theorem_records.append(
            {
                "declaration_order": index,
                "definitions": definition,
                "dependencies": {
                    "declared_publication_dependencies": replay_row[
                        "declared_dependencies"
                    ],
                    "minimality_claim": False,
                    "optimized_dependencies": None,
                    "optimized_leave_one_out_receipt_sha256": None,
                    "publication_union": None,
                    "readable_dependencies": None,
                    "readable_leave_one_out_receipt_sha256": None,
                    "status": "declared-publication-only",
                },
                "documentation": {
                    "atlas": atlas_receipt,
                    "defined_explorer": defined_receipt,
                    "explicit_explorer": explicit_receipt,
                    "vault": vault_receipt,
                },
                "explanation": {
                    "review_status": "pending-human-review",
                    "sha256": _sha256_bytes(explanation.encode("utf-8")),
                    "text": explanation,
                },
                "index": index,
                "layer": replay_row["layer"],
                "lineage": {"id": None, "status": "pending"},
                "logic": {
                    "mode": LOGIC_MODE,
                    "semantic_profile_id": manifest["semantic_profile"]["id"],
                    "semantic_profile_sha256": manifest["semantic_profile"]["sha256"],
                },
                "name": name,
                "optimized_construction": {
                    "artifact_sha256": replay_row["artifact"]["sha256"],
                    "claim": "submitted-not-best-known",
                    "proof_term_sha256": replay_row["proof_term_sha256"],
                },
                "proof": {
                    "artifact": replay_row["artifact"],
                    "construction_metrics": replay_row["construction_metrics"],
                    "formula_sha256": replay_row["formula_sha256"],
                    "packed_tree_metrics": replay_row["packed_tree_metrics"],
                    "proof_term_sha256": replay_row["proof_term_sha256"],
                    "replay_status": "kernel-accepted-retained-report",
                },
                "readable_proof": {
                    "script": replay_row["script"],
                    "script_sha256": replay_row["script_sha256"],
                },
                "source": source,
                "statement": {
                    "canonical": replay_row["statement_canonical"],
                    "canonical_sha256": replay_row["statement_canonical_sha256"],
                    "formula_sha256": replay_row["formula_sha256"],
                    "source": replay_row["statement_source"],
                    "source_sha256": replay_row["statement_source_sha256"],
                },
            }
        )

    statuses = lambda path, status: sum(
        1 for row in theorem_records if row["documentation"][path]["status"] == status
    )
    definition_statuses = lambda status: sum(
        1 for row in theorem_records if row["definitions"]["status"] == status
    )
    source_count = sum(row["source"]["status"] == "present" for row in theorem_records)
    complete_count = sum(
        row["source"]["status"] == "present"
        and row["definitions"]["status"] == "present"
        and all(
            receipt["status"] == "present"
            for receipt in row["documentation"].values()
        )
        for row in theorem_records
    )
    count = len(theorem_records)
    gaps = {
        "atlas_missing_count": statuses("atlas", "missing"),
        "atlas_stale_count": statuses("atlas", "stale"),
        "defined_explorer_missing_count": statuses("defined_explorer", "missing"),
        "defined_explorer_stale_count": statuses("defined_explorer", "stale"),
        "definition_receipt_missing_count": definition_statuses("missing"),
        "definition_receipt_stale_count": definition_statuses("stale"),
        "explicit_explorer_missing_count": statuses("explicit_explorer", "missing"),
        "explicit_explorer_stale_count": statuses("explicit_explorer", "stale"),
        "human_review_pending_count": count,
        "lineage_pending_count": count,
        "optimized_best_known_pending_count": count,
        "optimized_dependency_vectors_pending_count": count,
        "publication_union_pending_count": count,
        "readable_dependency_vectors_unverified_count": count,
        "source_locator_missing_count": count - source_count,
        "vault_missing_count": statuses("vault", "missing"),
        "vault_stale_count": statuses("vault", "stale"),
    }
    edge_count = sum(len(row["declared_dependencies"]) for row in rows)
    return {
        "aggregate": {
            "declared_dependency_edges": edge_count,
            "documentation_complete_count": complete_count,
            "source_locator_count": source_count,
            "theorem_count": count,
        },
        "documentation_sources": {
            "atlas": {
                "artifact_path": str(_ATLAS_RELATIVE),
                "artifact_sha256": atlas_sha,
                "record_count": len(atlas_records),
                "source_commit": atlas_commit,
            },
            "defined_explorer": {
                "artifact_path": str(_DEFINED_EXPLORER_RELATIVE),
                "artifact_sha256": defined_sha,
                "edition_identity_sha256": edition_identity,
                "record_count": len(defined_grouped),
                "schema": defined.get("schema"),
            },
            "explicit_explorer": {
                "artifact_path": str(_EXPLICIT_EXPLORER_RELATIVE),
                "artifact_sha256": explicit_sha,
                "record_count": len(explicit_grouped),
                "schema": explicit.get("schema"),
            },
            "vault": {
                "artifact_path": str(_VAULT_RELATIVE),
                "ordered_root_sha256": _sha256_json(vault_root_rows),
                "record_count": len(vault_root_rows),
            },
        },
        "evaluation_eligible": False,
        "format": EPOCH_METADATA_FORMAT,
        "freeze_ready": False,
        "gaps": gaps,
        "id": EPOCH_METADATA_ID,
        "logic_mode": LOGIC_MODE,
        "replay_pack": {
            "artifact_path": str(_REPLAY_PACK_RELATIVE / "manifest.json"),
            "manifest_artifact_sha256": _sha256_bytes(manifest_raw),
            "manifest_root_sha256": manifest["root_sha256"],
            "replay_root_sha256": manifest["replay_root_sha256"],
            "verification_report_artifact_sha256": _sha256_bytes(report_raw),
            "verification_report_path": str(_REPLAY_REPORT_RELATIVE),
            "verification_status": report["status"],
        },
        "repository": {
            "commit": SOURCE_COMMIT,
            "source": "retained-replay-pack-snapshot",
            "tree": SOURCE_TREE,
            "url": REPOSITORY_URL,
        },
        "schema": schema_identity,
        "status": STATUS,
        "theorem_count": count,
        "theorems": theorem_records,
        "v": EPOCH_METADATA_VERSION,
    }


def _with_root(body: Mapping[str, object]) -> dict[str, object]:
    detached = _detached_object(dict(body), "library epoch metadata body")
    if "root_preimage" in detached or "root_sha256" in detached:
        raise LibraryEpochMetadataError("library epoch metadata root body is recursive")
    preimage = {
        "format": EPOCH_METADATA_ROOT_PREIMAGE_FORMAT,
        "payload": detached,
        "v": EPOCH_METADATA_VERSION,
    }
    return {
        **detached,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def _validate_shape(value: object) -> dict[str, object]:
    metadata = _detached_object(value, "library epoch metadata")
    _require_fields("library epoch metadata", metadata, _METADATA_FIELDS)
    if not all(
        (
            metadata.get("format") == EPOCH_METADATA_FORMAT,
            metadata.get("id") == EPOCH_METADATA_ID,
            metadata.get("v") == EPOCH_METADATA_VERSION,
            metadata.get("status") == STATUS,
            metadata.get("logic_mode") == LOGIC_MODE,
            metadata.get("freeze_ready") is False,
            metadata.get("evaluation_eligible") is False,
        )
    ):
        raise LibraryEpochMetadataError("library epoch metadata constants are malformed")
    _require_fields("library epoch metadata schema", metadata["schema"], _SCHEMA_IDENTITY_FIELDS)
    if metadata["schema"] != epoch_metadata_schema_identity():
        raise LibraryEpochMetadataError("library epoch metadata schema identity drifted")
    _require_fields("library epoch aggregate", metadata["aggregate"], _AGGREGATE_FIELDS)
    _require_fields("library epoch gaps", metadata["gaps"], _GAP_FIELDS)
    count = metadata.get("theorem_count")
    rows = metadata.get("theorems")
    if type(count) is not int or not 0 < count <= MAX_THEOREMS:
        raise LibraryEpochMetadataError("library epoch theorem count is malformed")
    if type(rows) is not list or len(rows) != count:
        raise LibraryEpochMetadataError("library epoch theorem rows are malformed")
    for index, row in enumerate(rows):
        theorem = _require_fields("library epoch theorem", row, _THEOREM_FIELDS)
        if theorem.get("index") != index or theorem.get("declaration_order") != index:
            raise LibraryEpochMetadataError("library epoch theorem order is malformed")
        if theorem["optimized_construction"].get("claim") != "submitted-not-best-known":
            raise LibraryEpochMetadataError("optimized proof claim exceeds candidate evidence")
        dependencies = theorem["dependencies"]
        if (
            dependencies.get("minimality_claim") is not False
            or dependencies.get("status") != "declared-publication-only"
            or any(
                dependencies.get(key) is not None
                for key in (
                    "optimized_dependencies",
                    "optimized_leave_one_out_receipt_sha256",
                    "publication_union",
                    "readable_dependencies",
                    "readable_leave_one_out_receipt_sha256",
                )
            )
        ):
            raise LibraryEpochMetadataError("dependency evidence exceeds candidate receipts")
        if theorem["explanation"].get("review_status") != "pending-human-review":
            raise LibraryEpochMetadataError("human review is not independently receipted")
        if theorem["lineage"] != {"id": None, "status": "pending"}:
            raise LibraryEpochMetadataError("lineage is not independently receipted")
        for receipt in theorem["documentation"].values():
            if receipt.get("status") not in _RECEIPT_STATUSES:
                raise LibraryEpochMetadataError("documentation receipt status is malformed")
        if theorem["definitions"].get("status") not in _RECEIPT_STATUSES:
            raise LibraryEpochMetadataError("definition receipt status is malformed")
    preimage = _require_fields(
        "library epoch metadata root preimage",
        metadata["root_preimage"],
        _ROOT_PREIMAGE_FIELDS,
    )
    body = {key: item for key, item in metadata.items() if key not in {"root_preimage", "root_sha256"}}
    if preimage != {
        "format": EPOCH_METADATA_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": EPOCH_METADATA_VERSION,
    }:
        raise LibraryEpochMetadataError("library epoch metadata root preimage is malformed")
    if metadata["root_sha256"] != _sha256_json(preimage):
        raise LibraryEpochMetadataError("library epoch metadata root digest is malformed")
    return metadata


def build_candidate_epoch_metadata(
    *, repository_root: Path | None = None
) -> dict[str, object]:
    """Build, but do not retain, the exact candidate H1.1a metadata ledger."""

    root = _repository_root(repository_root)
    candidate = _with_root(_candidate_body(root))
    _validate_shape(candidate)
    return candidate


def validate_epoch_metadata(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Strictly validate a ledger against all exact retained source inputs."""

    actual = _validate_shape(value)
    expected = build_candidate_epoch_metadata(repository_root=repository_root)
    if actual != expected:
        raise LibraryEpochMetadataError(
            "library epoch metadata differs from exact retained candidate inputs"
        )
    return actual


def load_epoch_metadata(
    path: Path, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Load one bounded canonical ledger and validate every bound receipt."""

    if not isinstance(path, Path):
        raise TypeError("library epoch metadata path must be a pathlib.Path")
    raw = _read_bounded_regular_file(
        path, label="library epoch metadata", limit=MAX_METADATA_BYTES
    )
    value = _decode_canonical_document(
        raw, "library epoch metadata", limit=MAX_METADATA_BYTES
    )
    return validate_epoch_metadata(value, repository_root=repository_root)


def readiness_report(
    metadata: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Return the deterministic candidate-readiness summary used by the CLI."""

    value = validate_epoch_metadata(metadata, repository_root=repository_root)
    return {
        "declared_dependency_edges": value["aggregate"]["declared_dependency_edges"],
        "evaluation_eligible": False,
        "format": READINESS_REPORT_FORMAT,
        "freeze_ready": False,
        "gaps": value["gaps"],
        "manifest_root_sha256": value["replay_pack"]["manifest_root_sha256"],
        "metadata_root_sha256": value["root_sha256"],
        "replay_root_sha256": value["replay_pack"]["replay_root_sha256"],
        "status": STATUS,
        "theorem_count": value["theorem_count"],
        "v": EPOCH_METADATA_VERSION,
    }
