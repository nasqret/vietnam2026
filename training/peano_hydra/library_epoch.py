"""Strict H1.1 library-epoch protocol slice for Peano Hydra.

An epoch record is provenance, never theorem authority.  Candidate records
identify the live authoring catalog at one Git commit and are categorically
ineligible for research evaluation.  A frozen record can be constructed only
from a candidate, a content-addressed three-file pack, and a separately
supplied owner receipt whose exact digest is in the reviewed deposit registry.
The registry is deliberately empty in v1: this module can prepare a candidate
pack and exercise the transition protocol, but cannot currently mint a frozen
L0 epoch.  The three-file pack is provenance evidence, not yet the
replay-complete research pack required to finish H1.1.

The active H0 intuitionistic profile remains immutable.  Every catalog row is
checked against the live tracked catalog, including a fresh ordinary-kernel
replay of its self-contained certificate.  The retained H0 validation report
is bound as historical independent-replay evidence; it is not reissued here.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import fields
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
from types import MappingProxyType
from typing import Literal, Mapping

from peano_lab.engine.state import proof_resource_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import Cut, Proof
from peano_lab.library import theorems as theorem_library

from .profile import (
    SEMANTIC_PROFILE_FORMAT,
    SEMANTIC_PROFILE_ID,
    SEMANTIC_PROFILE_PATH,
    SEMANTIC_PROFILE_V2_DOCUMENT_SHA256,
    SEMANTIC_PROFILE_V2_SHA256,
    SEMANTIC_PROFILE_VERSION,
    semantic_profile_identity,
    semantic_profile_registration,
)


LIBRARY_EPOCH_SCHEMA_FORMAT = "peano-hydra-library-epoch-schema"
LIBRARY_EPOCH_SCHEMA_VERSION = 1
LIBRARY_EPOCH_SCHEMA_ID = "peano-hydra-library-epoch-v1"
LIBRARY_EPOCH_SCHEMA_PATH = Path(__file__).with_name(
    "library-epoch-schema-v1.json"
)
# Filled from the canonical schema artifact; registry users must never trust a
# digest recomputed from a silently changed local file.
LIBRARY_EPOCH_SCHEMA_SHA256 = (
    "f4695013ee4aeb660abf3a1e57a6334d86c990a8904c4435d94628694a2e875b"
)

LIBRARY_EPOCH_FORMAT = "peano-hydra-library-epoch"
LIBRARY_EPOCH_VERSION = 1
LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT = (
    "peano-hydra-library-epoch-root-preimage"
)
OWNER_RECEIPT_FORMAT = "peano-hydra-library-epoch-owner-receipt"
OWNER_RECEIPT_VERSION = 1
EPOCH_PACK_FORMAT = "peano-hydra-library-epoch-pack"
EPOCH_PACK_VERSION = 1
EPOCH_PACK_ROOT_PREIMAGE_FORMAT = "peano-hydra-library-epoch-pack-root-preimage"

CANDIDATE_STATUS = "candidate"
FROZEN_STATUS = "frozen"
AUTHORING_SCOPE = "living-authoring-head"
FROZEN_SCOPE = "immutable-research-epoch"
AUTHORING_REPOSITORY_SOURCE = "git-head"
FROZEN_REPOSITORY_SOURCE = "git-commit"
LOGIC_MODE = "intuitionistic"
OWNER_ROLE = "independent-evaluation-owner"

CATALOG_ID = "peano-lab-public-runtime"
CATALOG_PATH_TEXT = "artifacts/peano-library/catalog-v1.json"
CATALOG_SCHEMA = "peano-library-snapshot-v3"
CATALOG_CERTIFICATE_REPRESENTATION = "python-dataclass-repr-with-cut-v2"
H0_REPORT_PATH_TEXT = "artifacts/peano-hydra/h0-validation-v2.json"
H0_REPORT_SHA256 = (
    "55c60502b2229f4420bd4557058842bebb582f491739e82a6dae06de5b803fdb"
)
PROFILE_PATH_TEXT = "training/peano_hydra/semantic-profile-v2.json"

# An independent evaluator must deposit a receipt outside the authoring
# process, after which a reviewed source change registers the exact receipt
# digest, deposit ID, and owner ID.  Keeping this empty is an intentional H1.1
# no-freeze state.  Structural receipt bytes alone never confer authority.
_REGISTERED_OWNER_RECEIPTS: Mapping[str, tuple[str, str]] = MappingProxyType({})

MAX_SCHEMA_BYTES = 1_000_000
MAX_EPOCH_BYTES = 4_000_000
MAX_CATALOG_BYTES = 4_000_000
MAX_H0_REPORT_BYTES = 8_000_000
MAX_JSON_DEPTH = 128
MAX_JSON_ITEMS = 1_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991

EpochStatus = Literal["candidate", "frozen"]

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_CATALOG_PATH = _REPOSITORY_ROOT / CATALOG_PATH_TEXT
_H0_REPORT_PATH = _REPOSITORY_ROOT / H0_REPORT_PATH_TEXT
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_SAFE_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_OWNER_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@-]{0,159}")

_EPOCH_FIELDS = frozenset(
    {
        "benchmark",
        "catalog",
        "evaluation_eligible",
        "format",
        "h0_replay",
        "id",
        "independent_commitment",
        "logic_mode",
        "pack",
        "repository",
        "root_preimage",
        "root_sha256",
        "scope",
        "semantic_profile",
        "status",
        "v",
    }
)
_PROFILE_FIELDS = frozenset(
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
_REPOSITORY_FIELDS = frozenset({"commit", "relevant_dirty", "source"})
_CATALOG_IDENTITY_FIELDS = frozenset(
    {
        "artifact_path",
        "artifact_sha256",
        "catalog_sha256",
        "certificate_representation",
        "evaluation_certificate_representation",
        "id",
        "ordered_root_sha256",
        "schema",
        "source_root_sha256",
        "theorem_count",
    }
)
_H0_FIELDS = frozenset(
    {
        "artifact_case_count",
        "campaign_eligible",
        "lean_source_commit",
        "lean_source_root_sha256",
        "lean_verifier_sha256",
        "library_count",
        "profile_sha256",
        "replay_pass_count",
        "replay_root_sha256",
        "report_format",
        "report_path",
        "report_sha256",
        "report_v",
        "source_commit",
        "validation_passed",
    }
)
_BENCHMARK_FIELDS = frozenset({"commitment_sha256", "status"})
_COMMITMENT_FIELDS = frozenset(
    {
        "candidate_root_sha256",
        "deposit_id",
        "owner_id",
        "owner_role",
        "pack_root_sha256",
        "receipt_format",
        "receipt_sha256",
        "receipt_v",
    }
)
_ROOT_PREIMAGE_FIELDS = frozenset({"format", "payload", "v"})
_OWNER_RECEIPT_FIELDS = frozenset(
    {
        "benchmark",
        "candidate_root_sha256",
        "catalog_sha256",
        "deposit_id",
        "epoch_id",
        "format",
        "owner_id",
        "owner_role",
        "pack_root_sha256",
        "repository_commit",
        "semantic_profile_sha256",
        "v",
    }
)
_PACK_FIELDS = frozenset({"files", "format", "root_preimage", "root_sha256", "v"})
_PACK_FILE_FIELDS = frozenset({"bytes", "path", "role", "sha256"})
_PACK_ROOT_PREIMAGE_FIELDS = frozenset({"files", "format", "v"})
_PACK_ROLES = ("catalog", "semantic-profile", "h0-replay")
_PACK_ROLE_BYTE_LIMITS = {
    "catalog": MAX_CATALOG_BYTES,
    "semantic-profile": MAX_SCHEMA_BYTES,
    "h0-replay": MAX_H0_REPORT_BYTES,
}
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


class LibraryEpochError(ValueError):
    """An epoch, schema, catalog, or independent receipt is invalid."""


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


def _validate_json_value(
    value: object,
    *,
    path: str = "$",
    depth: int = 0,
    ancestors: frozenset[int] = frozenset(),
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise LibraryEpochError(f"{path} exceeds the JSON nesting limit")
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        if not -MAX_SAFE_JSON_INTEGER <= value <= MAX_SAFE_JSON_INTEGER:
            raise LibraryEpochError(f"{path} is outside the JSON integer domain")
        return
    if type(value) is str:
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise LibraryEpochError(
                f"{path} contains a non-scalar Unicode surrogate"
            ) from None
        return
    if type(value) not in (list, dict):
        raise LibraryEpochError(
            f"{path} has unsupported JSON type {type(value).__name__}"
        )
    marker = id(value)
    if marker in ancestors:
        raise LibraryEpochError(f"{path} contains a cyclic container")
    if len(value) > MAX_JSON_ITEMS:
        raise LibraryEpochError(f"{path} has too many container items")
    next_ancestors = ancestors | {marker}
    if type(value) is list:
        for index, item in enumerate(value):
            _validate_json_value(
                item,
                path=f"{path}[{index}]",
                depth=depth + 1,
                ancestors=next_ancestors,
            )
        return
    for key, item in value.items():
        if type(key) is not str:
            raise LibraryEpochError(f"{path} has a non-string object key")
        _validate_json_value(key, path=f"{path}.<key>", depth=depth + 1)
        _validate_json_value(
            item,
            path=f"{path}.{key}",
            depth=depth + 1,
            ancestors=next_ancestors,
        )


def canonical_json_bytes(value: object, *, limit: int = MAX_EPOCH_BYTES) -> bytes:
    """Encode one exact compact JSON hash preimage."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive integer")
    _validate_json_value(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryEpochError(f"value is not canonical JSON: {exc}") from None
    if len(encoded) > limit:
        raise LibraryEpochError(f"canonical JSON exceeds the {limit}-byte limit")
    return encoded


def canonical_document_bytes(
    value: object, *, limit: int = MAX_EPOCH_BYTES
) -> bytes:
    """Encode one canonical retained JSON document."""

    _validate_json_value(value)
    try:
        encoded = (
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
        raise LibraryEpochError(f"value is not canonical JSON: {exc}") from None
    if len(encoded) > limit:
        raise LibraryEpochError(f"canonical document exceeds the {limit}-byte limit")
    return encoded


def _decode_json(raw: bytes, label: str) -> object:
    try:
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryEpochError(f"{label} is not strict JSON: {exc}") from None


def _decode_canonical_document(
    raw: bytes, label: str, *, limit: int
) -> dict[str, object]:
    if type(raw) is not bytes or not raw or len(raw) > limit:
        raise LibraryEpochError(f"{label} must be bounded nonempty bytes")
    value = _decode_json(raw, label)
    if type(value) is not dict or canonical_document_bytes(value, limit=limit) != raw:
        raise LibraryEpochError(f"{label} is not one canonical JSON document")
    return value


def _detached_object(value: object, label: str) -> dict[str, object]:
    raw = canonical_json_bytes(value)
    decoded = _decode_json(raw, label)
    if type(decoded) is not dict:  # pragma: no cover - checked by callers
        raise LibraryEpochError(f"{label} must be one object")
    return decoded


def _require_fields(label: str, value: object, expected: frozenset[str]) -> dict[str, object]:
    if type(value) is not dict or set(value) != expected:
        raise LibraryEpochError(f"{label} has non-canonical fields")
    return value


def _require_sha256(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryEpochError(f"{label} must be one lowercase SHA-256")
    return value


def _require_commit(label: str, value: object) -> str:
    if type(value) is not str or _COMMIT_RE.fullmatch(value) is None:
        raise LibraryEpochError(f"{label} must be one lowercase Git commit")
    return value


def _require_version(label: str, value: object, expected: int) -> int:
    """Require an integer version without Python's ``True == 1`` alias."""

    if type(value) is not int or value != expected:
        raise LibraryEpochError(f"{label} must be integer {expected}")
    return value


def _positive_integer(label: str, value: object) -> int:
    if type(value) is not int or not 1 <= value <= MAX_SAFE_JSON_INTEGER:
        raise LibraryEpochError(f"{label} must be a positive integer")
    return value


def _safe_relative_path(label: str, value: object, *, prefix: str) -> str:
    """Validate repository-shaped path text without consulting the live tree."""

    if type(value) is not str or not value or "\\" in value:
        raise LibraryEpochError(f"{label} is not a safe repository path")
    path = Path(value)
    if (
        path.is_absolute()
        or path.as_posix() != value
        or "." in path.parts
        or ".." in path.parts
        or not value.startswith(prefix)
    ):
        raise LibraryEpochError(f"{label} is not a safe repository path")
    return value


def _safe_repository_path(label: str, value: object, *, prefix: str) -> str:
    """Validate and resolve a path that intentionally names living HEAD."""

    value = _safe_relative_path(label, value, prefix=prefix)
    path = Path(value)
    try:
        (_REPOSITORY_ROOT / path).resolve().relative_to(_REPOSITORY_ROOT.resolve())
    except (OSError, RuntimeError, ValueError):
        raise LibraryEpochError(f"{label} escapes the repository") from None
    return value


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    """Read at most ``limit`` bytes from one non-symlink regular file."""

    if type(limit) is not int or limit < 1:
        raise TypeError("bounded file limit must be a positive integer")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryEpochError(f"cannot read {label}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise LibraryEpochError(f"{label} must be a regular file")
        if metadata.st_size > limit:
            raise LibraryEpochError(f"{label} exceeds the {limit}-byte limit")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise LibraryEpochError(f"{label} exceeds the {limit}-byte limit")
        return raw
    except OSError as exc:
        raise LibraryEpochError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_json(value: object, *, limit: int = MAX_CATALOG_BYTES) -> str:
    return _sha256_bytes(canonical_json_bytes(value, limit=limit))


def _same_canonical_json(
    left: object, right: object, *, limit: int = MAX_EPOCH_BYTES
) -> bool:
    """Compare JSON values with exact JSON types, including bool versus int."""

    return canonical_json_bytes(left, limit=limit) == canonical_json_bytes(
        right, limit=limit
    )


def library_epoch_schema() -> dict[str, object]:
    """Load the exact canonical H1.1 schema artifact."""

    raw = _read_bounded_regular_file(
        LIBRARY_EPOCH_SCHEMA_PATH,
        label="the library-epoch schema",
        limit=MAX_SCHEMA_BYTES,
    )
    value = _decode_canonical_document(
        raw, "library-epoch schema", limit=MAX_SCHEMA_BYTES
    )
    if _sha256_json(value, limit=MAX_SCHEMA_BYTES) != LIBRARY_EPOCH_SCHEMA_SHA256:
        raise LibraryEpochError("library-epoch schema semantic digest drifted")
    if (
        value.get("format") != LIBRARY_EPOCH_SCHEMA_FORMAT
        or value.get("id") != LIBRARY_EPOCH_SCHEMA_ID
        or value.get("additional_fields_policy")
        != "forbidden-at-every-schema-owned-object"
    ):
        raise LibraryEpochError("library-epoch schema identity is malformed")
    _require_version(
        "library-epoch schema version",
        value.get("v"),
        LIBRARY_EPOCH_SCHEMA_VERSION,
    )
    freeze_authority = value.get("freeze_authority")
    if type(freeze_authority) is not dict:
        raise LibraryEpochError("library-epoch freeze authority is malformed")
    registered = len(_REGISTERED_OWNER_RECEIPTS)
    if (
        freeze_authority.get("current_registered_receipts") != registered
        or type(freeze_authority.get("current_registered_receipts")) is not int
        or freeze_authority.get("v1_can_publish_frozen_epoch") is not bool(registered)
    ):
        raise LibraryEpochError(
            "library-epoch schema disagrees with the reviewed receipt registry"
        )
    return _detached_object(value, "library-epoch schema")


def library_epoch_schema_identity() -> dict[str, object]:
    library_epoch_schema()
    return {
        "format": LIBRARY_EPOCH_SCHEMA_FORMAT,
        "v": LIBRARY_EPOCH_SCHEMA_VERSION,
        "id": LIBRARY_EPOCH_SCHEMA_ID,
        "sha256": LIBRARY_EPOCH_SCHEMA_SHA256,
    }


def _git_head_commit() -> str:
    try:
        completed = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=_REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LibraryEpochError("cannot identify the repository source commit") from exc
    if completed.returncode != 0 or completed.stderr:
        raise LibraryEpochError("cannot identify the repository source commit")
    return _require_commit("repository source commit", completed.stdout.strip())


def _git_relevant_dirty() -> bool:
    paths = (
        "artifacts/peano-library/catalog-v1.json",
        "artifacts/peano-hydra/h0-validation-v2.json",
        "training/peano_hydra",
        "peano-lab/py/peano_lab/library",
        "peano-lab/py/peano_lab/kernel",
        "peano-lab/py/peano_lab/engine",
    )
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "--untracked-files=all", "--", *paths],
            cwd=_REPOSITORY_ROOT,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise LibraryEpochError("cannot identify relevant repository dirtiness") from exc
    if completed.returncode != 0 or completed.stderr:
        raise LibraryEpochError("cannot identify relevant repository dirtiness")
    return bool(completed.stdout)


def _live_catalog_cache_key() -> str:
    """Fingerprint every local input that can affect live catalog replay.

    The key is intentionally content based rather than a one-entry process
    cache.  A checkout, commit, or in-place edit therefore cannot silently
    reuse an identity derived from an earlier revision.
    """

    roots = (
        _REPOSITORY_ROOT / "training/peano_hydra",
        _REPOSITORY_ROOT / "peano-lab/py/peano_lab/engine",
        _REPOSITORY_ROOT / "peano-lab/py/peano_lab/kernel",
        _REPOSITORY_ROOT / "peano-lab/py/peano_lab/library",
    )
    paths = [
        _CATALOG_PATH,
        _H0_REPORT_PATH,
        LIBRARY_EPOCH_SCHEMA_PATH,
        SEMANTIC_PROFILE_PATH,
    ]
    for root in roots:
        try:
            paths.extend(sorted(path for path in root.rglob("*.py") if path.is_file()))
        except OSError as exc:
            raise LibraryEpochError("cannot fingerprint live catalog sources") from exc
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for path in sorted(paths, key=lambda item: item.as_posix()):
        try:
            relative = path.resolve().relative_to(_REPOSITORY_ROOT.resolve()).as_posix()
        except (OSError, RuntimeError, ValueError):
            raise LibraryEpochError("live catalog source escapes the repository") from None
        if relative in seen:
            continue
        raw = _read_bounded_regular_file(
            path,
            label=f"live catalog source {relative!r}",
            limit=MAX_CATALOG_BYTES,
        )
        rows.append({"path": relative, "sha256": _sha256_bytes(raw)})
        seen.add(relative)
    return _sha256_json(rows, limit=MAX_CATALOG_BYTES)


# Imported Python objects cannot be safely refreshed by merely hashing changed
# source files.  Capture the exact inputs during module import and fail closed
# if a long-lived authoring process observes another checkout or in-place
# source revision.  The host must restart, which gives the replay a fresh
# interpreter and fresh theorem-library objects.
_IMPORTED_LIVE_CONTENT_KEY = _live_catalog_cache_key()


def _cut_nodes(proof: Proof) -> int:
    count = 0
    pending = [proof]
    while pending:
        node = pending.pop()
        if type(node) is Cut:
            count += 1
        for item in fields(node):
            child = getattr(node, item.name)
            if isinstance(child, Proof):
                pending.append(child)
    return count


def _validate_catalog_source_manifest(
    catalog: dict[str, object], *, require_live: bool
) -> None:
    sources = catalog.get("theorem_sources")
    if type(sources) is not list or not sources:
        raise LibraryEpochError("tracked catalog source manifest is malformed")
    seen: set[str] = set()
    for index, row in enumerate(sources):
        source = _require_fields(
            f"tracked catalog source {index}", row, _CATALOG_SOURCE_FIELDS
        )
        path_validator = _safe_repository_path if require_live else _safe_relative_path
        path = path_validator(
            f"tracked catalog source path {index}",
            source.get("path"),
            prefix="peano-lab/py/peano_lab/library/",
        )
        if not path.endswith(".py") or path in seen:
            raise LibraryEpochError("tracked catalog source path is duplicated or invalid")
        expected = _require_sha256(
            f"tracked catalog source hash for {path!r}", source.get("sha256")
        )
        if require_live:
            actual = _sha256_bytes(
                _read_bounded_regular_file(
                    _REPOSITORY_ROOT / path,
                    label=f"tracked source {path!r}",
                    limit=MAX_CATALOG_BYTES,
                )
            )
            if actual != expected:
                raise LibraryEpochError(f"tracked catalog source {path!r} drifted")
        seen.add(path)
    source_root = _require_sha256(
        "tracked catalog source root", catalog.get("theorem_source_root_sha256")
    )
    expected_root = _sha256_bytes(
        canonical_document_bytes(sources, limit=MAX_CATALOG_BYTES)
    )
    if source_root != expected_root:
        raise LibraryEpochError("tracked catalog source root is invalid")


def _validate_catalog_rows(
    catalog: dict[str, object], *, require_live: bool
) -> None:
    rows = catalog.get("theorems")
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != len(rows)
        or not rows
    ):
        raise LibraryEpochError("tracked catalog theorem count is malformed")
    if catalog.get("ordered_root_sha256") != _sha256_json(
        rows, limit=MAX_CATALOG_BYTES
    ):
        raise LibraryEpochError("tracked catalog ordered root is invalid")

    known: set[str] = set()
    specifications = theorem_library.THEOREMS if require_live else ()
    if require_live and len(rows) != len(specifications):
        raise LibraryEpochError("tracked catalog count differs from the live library")
    for index, row_value in enumerate(rows):
        row = _require_fields(
            f"tracked catalog theorem {index}", row_value, _CATALOG_ROW_FIELDS
        )
        name = row.get("name")
        dependencies = row.get("dependencies")
        script = row.get("script")
        if (
            type(name) is not str
            or not name
            or name != name.strip()
            or any(character.isspace() for character in name)
            or name in known
            or type(dependencies) is not list
            or not all(type(item) is str and item in known for item in dependencies)
            or type(script) is not list
            or not script
            or not all(type(item) is str and item for item in script)
        ):
            raise LibraryEpochError("tracked catalog theorem order is malformed")
        if row.get("index") != index:
            raise LibraryEpochError("tracked catalog theorem index is malformed")
        statement = row.get("statement")
        summary = row.get("summary")
        if type(statement) is not str or not statement or type(summary) is not str:
            raise LibraryEpochError(f"tracked catalog text for {name!r} is malformed")
        if row.get("statement_sha256") != _sha256_bytes(statement.encode("utf-8")):
            raise LibraryEpochError(f"tracked catalog statement hash for {name!r} is invalid")
        if row.get("script_sha256") != _sha256_bytes(
            ("\n".join(script) + "\n").encode("utf-8")
        ):
            raise LibraryEpochError(f"tracked catalog script hash for {name!r} is invalid")
        for field_name in ("statement_sha256", "script_sha256", "certificate_sha256"):
            _require_sha256(f"tracked catalog {field_name}", row.get(field_name))
        if row.get("certificate_representation") != CATALOG_CERTIFICATE_REPRESENTATION:
            raise LibraryEpochError(
                f"tracked catalog certificate representation for {name!r} is malformed"
            )
        for field_name in ("proof_nodes", "proof_depth", "distinct_proof_objects"):
            _positive_integer(f"tracked catalog {field_name}", row.get(field_name))
        for field_name in ("cut_nodes", "proof_edges", "reused_proof_references"):
            field_value = row.get(field_name)
            if type(field_value) is not int or field_value < 0:
                raise LibraryEpochError(
                    f"tracked catalog {field_name} for {name!r} is malformed"
                )
        if row["proof_depth"] > row["proof_nodes"]:
            raise LibraryEpochError(f"tracked catalog proof shape for {name!r} is malformed")
        if type(row.get("layer")) is not str or not str(row["layer"]).strip():
            raise LibraryEpochError(f"tracked catalog layer for {name!r} is invalid")
        known.add(name)

        if not require_live:
            continue
        spec = specifications[index]
        if spec.name != name or list(spec.dependencies) != dependencies:
            raise LibraryEpochError("live theorem dependency order is invalid")
        expected_source = {
            "certificate_representation": CATALOG_CERTIFICATE_REPRESENTATION,
            "dependencies": list(spec.dependencies),
            "index": index,
            "name": spec.name,
            "script": list(spec.script),
            "script_sha256": _sha256_bytes(
                ("\n".join(spec.script) + "\n").encode("utf-8")
            ),
            "statement": spec.statement,
            "statement_sha256": _sha256_bytes(spec.statement.encode("utf-8")),
            "summary": spec.summary,
        }
        for field_name, expected in expected_source.items():
            if row.get(field_name) != expected:
                raise LibraryEpochError(
                    f"tracked catalog/live source drift at {spec.name!r}: {field_name}"
                )
        checked = theorem_library.replay(spec.name)
        if checked.spec != spec or not check((), checked.certificate, checked.formula):
            raise LibraryEpochError(
                f"independent kernel rejected tracked theorem {spec.name!r}"
            )
        nodes, depth, objects, edges, reused = proof_resource_metrics(
            checked.certificate
        )
        expected_replay = {
            "certificate_sha256": _sha256_bytes(
                repr(checked.certificate).encode("utf-8")
            ),
            "cut_nodes": _cut_nodes(checked.certificate),
            "distinct_proof_objects": objects,
            "proof_depth": depth,
            "proof_edges": edges,
            "proof_nodes": nodes,
            "reused_proof_references": reused,
        }
        for field_name, expected in expected_replay.items():
            if row.get(field_name) != expected:
                raise LibraryEpochError(
                    f"tracked catalog/live replay drift at {spec.name!r}: {field_name}"
                )


def _catalog_identity_from_bytes(
    raw: bytes,
    *,
    artifact_path: str,
    require_live: bool,
    evaluation_certificate_representation: str,
) -> dict[str, object]:
    catalog = _decode_canonical_document(
        raw, "tracked public catalog", limit=MAX_CATALOG_BYTES
    )
    if set(catalog) != _CATALOG_FIELDS:
        raise LibraryEpochError("tracked catalog has non-canonical fields")
    if (
        catalog.get("schema") != CATALOG_SCHEMA
        or catalog.get("certificate_representation")
        != CATALOG_CERTIFICATE_REPRESENTATION
    ):
        raise LibraryEpochError("tracked catalog identity is malformed")
    if type(catalog.get("certificate_policy")) is not str or not str(
        catalog["certificate_policy"]
    ).strip():
        raise LibraryEpochError("tracked catalog certificate policy is malformed")
    _validate_catalog_source_manifest(catalog, require_live=require_live)
    _validate_catalog_rows(catalog, require_live=require_live)
    return {
        "artifact_path": artifact_path,
        "artifact_sha256": _sha256_bytes(raw),
        "catalog_sha256": _sha256_json(catalog, limit=MAX_CATALOG_BYTES),
        "certificate_representation": CATALOG_CERTIFICATE_REPRESENTATION,
        "evaluation_certificate_representation": evaluation_certificate_representation,
        "id": CATALOG_ID,
        "ordered_root_sha256": _require_sha256(
            "tracked catalog ordered root", catalog.get("ordered_root_sha256")
        ),
        "schema": CATALOG_SCHEMA,
        "source_root_sha256": _require_sha256(
            "tracked catalog source root", catalog.get("theorem_source_root_sha256")
        ),
        "theorem_count": _positive_integer(
            "tracked catalog theorem count", catalog.get("theorem_count")
        ),
    }


def _derive_live_catalog_identity() -> dict[str, object]:
    raw = _read_bounded_regular_file(
        _CATALOG_PATH,
        label="the tracked public catalog",
        limit=MAX_CATALOG_BYTES,
    )
    registration = semantic_profile_registration(
        semantic_profile_identity()["sha256"]
    )
    representation = registration.get("certificate_representation")
    if type(representation) is not str or not representation:
        raise LibraryEpochError("semantic profile certificate representation is invalid")
    return _catalog_identity_from_bytes(
        raw,
        artifact_path=CATALOG_PATH_TEXT,
        require_live=True,
        evaluation_certificate_representation=representation,
    )


@lru_cache(maxsize=8)
def _cached_live_catalog_identity_json(_content_key: str) -> bytes:
    return canonical_json_bytes(_derive_live_catalog_identity())


def live_tracked_catalog_identity() -> dict[str, object]:
    """Replay and identify the complete current public theorem catalog."""

    content_key = _live_catalog_cache_key()
    if content_key != _IMPORTED_LIVE_CONTENT_KEY:
        raise LibraryEpochError(
            "live catalog inputs changed after import; restart the authoring process"
        )
    value = _decode_json(
        _cached_live_catalog_identity_json(content_key),
        "catalog identity",
    )
    if type(value) is not dict:  # pragma: no cover - construction invariant
        raise RuntimeError("cached catalog identity is not an object")
    return value


def _h0_identity_from_bytes(
    raw: bytes, *, report_path: str, expected_profile_sha256: str
) -> dict[str, object]:
    if _sha256_bytes(raw) != H0_REPORT_SHA256:
        raise LibraryEpochError("retained H0 replay report bytes drifted")
    report = _decode_canonical_document(
        raw, "retained H0 replay report", limit=MAX_H0_REPORT_BYTES
    )
    repository = report.get("repository")
    cold = report.get("cold_replay")
    conformance = report.get("conformance")
    coverage = report.get("external_envelopes", {}).get("coverage") if type(
        report.get("external_envelopes")
    ) is dict else None
    reference = report.get("reference_identity")
    lean = reference.get("lean") if type(reference) is dict else None
    lean_source = reference.get("lean_source") if type(reference) is dict else None
    manifest = lean_source.get("manifest") if type(lean_source) is dict else None
    lean_coverage = coverage.get("lean") if type(coverage) is dict else None
    if (
        type(repository) is not dict
        or repository.get("clean") is not True
        or type(cold) is not dict
        or cold.get("identical") is not True
        or type(conformance) is not dict
        or type(lean) is not dict
        or type(lean_source) is not dict
        or lean_source.get("clean") is not True
        or type(manifest) is not dict
        or type(lean_coverage) is not dict
        or lean_coverage.get("out_of_envelope") != 0
        or lean_coverage.get("portable") != conformance.get("artifact_case_count")
        or report.get("validation_passed") is not True
        or report.get("campaign_eligible") is not True
    ):
        raise LibraryEpochError("retained H0 replay evidence is not independently green")
    if report.get("profile_sha256") != expected_profile_sha256:
        raise LibraryEpochError("retained H0 replay uses a different semantic profile")
    identity = {
        "artifact_case_count": _positive_integer(
            "H0 artifact case count", conformance.get("artifact_case_count")
        ),
        "campaign_eligible": True,
        "lean_source_commit": _require_commit(
            "H0 Lean source commit", lean_source.get("commit")
        ),
        "lean_source_root_sha256": _require_sha256(
            "H0 Lean source root", manifest.get("root_sha256")
        ),
        "lean_verifier_sha256": _require_sha256(
            "H0 Lean verifier hash", lean.get("sha256")
        ),
        "library_count": _positive_integer(
            "H0 library count", cold.get("library_count")
        ),
        "profile_sha256": expected_profile_sha256,
        "replay_pass_count": _positive_integer(
            "H0 replay pass count", cold.get("pass_count")
        ),
        "replay_root_sha256": _require_sha256(
            "H0 replay root", cold.get("root_sha256")
        ),
        "report_format": report.get("format"),
        "report_path": report_path,
        "report_sha256": H0_REPORT_SHA256,
        "report_v": report.get("v"),
        "source_commit": _require_commit(
            "H0 source commit", repository.get("commit")
        ),
        "validation_passed": True,
    }
    if type(identity["report_format"]) is not str or type(identity["report_v"]) is not int:
        raise LibraryEpochError("retained H0 report identity is malformed")
    return identity


@lru_cache(maxsize=1)
def _h0_replay_identity_json() -> bytes:
    raw = _read_bounded_regular_file(
        _H0_REPORT_PATH,
        label="retained H0 replay evidence",
        limit=MAX_H0_REPORT_BYTES,
    )
    identity = _h0_identity_from_bytes(
        raw,
        report_path=H0_REPORT_PATH_TEXT,
        expected_profile_sha256=SEMANTIC_PROFILE_V2_SHA256,
    )
    return canonical_json_bytes(identity)


def h0_replay_identity() -> dict[str, object]:
    value = _decode_json(_h0_replay_identity_json(), "H0 replay identity")
    if type(value) is not dict:  # pragma: no cover - construction invariant
        raise RuntimeError("cached H0 replay identity is not an object")
    return value


def _active_profile_epoch_identity() -> dict[str, object]:
    identity = semantic_profile_identity()
    registration = semantic_profile_registration(identity["sha256"])
    if (
        registration.get("format") != SEMANTIC_PROFILE_FORMAT
        or registration.get("logic") != LOGIC_MODE
        or registration.get("id") != identity["id"]
        or registration.get("v") != identity["v"]
    ):
        raise LibraryEpochError("active semantic profile is not the H0 HA profile")
    representation = registration.get("certificate_representation")
    if type(representation) is not str or not representation:
        raise LibraryEpochError("active profile certificate representation is malformed")
    return {
        **identity,
        "artifact_path": PROFILE_PATH_TEXT,
        "artifact_sha256": SEMANTIC_PROFILE_V2_DOCUMENT_SHA256,
        "logic": LOGIC_MODE,
        "certificate_representation": representation,
    }


def _profile_identity_from_bytes(
    raw: bytes, *, artifact_path: str
) -> dict[str, object]:
    profile = _decode_canonical_document(
        raw, "packed semantic profile", limit=MAX_SCHEMA_BYTES
    )
    calculus = profile.get("calculus")
    authority = profile.get("authority")
    if (
        type(calculus) is dict
        and (calculus.get("classical") is True or calculus.get("dne") is True)
    ) or (
        type(authority) is dict
        and authority.get("classical_checker") != "forbidden"
    ):
        raise LibraryEpochError("classical material contaminated the packed HA profile")
    if (
        _sha256_bytes(raw) != SEMANTIC_PROFILE_V2_DOCUMENT_SHA256
        or _sha256_json(profile, limit=MAX_SCHEMA_BYTES)
        != SEMANTIC_PROFILE_V2_SHA256
        or profile.get("format") != SEMANTIC_PROFILE_FORMAT
        or profile.get("id") != SEMANTIC_PROFILE_ID
    ):
        raise LibraryEpochError("packed semantic profile identity is malformed")
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
        or authority.get("certificate_representation") != "peano-lab-v2"
    ):
        raise LibraryEpochError("classical material contaminated the packed HA profile")
    return {
        "artifact_path": artifact_path,
        "artifact_sha256": SEMANTIC_PROFILE_V2_DOCUMENT_SHA256,
        "certificate_representation": "peano-lab-v2",
        "format": SEMANTIC_PROFILE_FORMAT,
        "id": SEMANTIC_PROFILE_ID,
        "logic": LOGIC_MODE,
        "sha256": SEMANTIC_PROFILE_V2_SHA256,
        "v": SEMANTIC_PROFILE_VERSION,
    }


def _pack_path(role: str, digest: str) -> str:
    if role not in _PACK_ROLES:
        raise LibraryEpochError("epoch pack role is unsupported")
    _require_sha256("epoch pack content hash", digest)
    return f"pack/{role}-{digest}.json"


def _pack_manifest(files: Mapping[str, bytes]) -> dict[str, object]:
    if not isinstance(files, Mapping):
        raise LibraryEpochError("epoch pack files must be one mapping")
    try:
        supplied_files = dict(files.items())
    except (AttributeError, TypeError, ValueError) as exc:
        raise LibraryEpochError("epoch pack files mapping is malformed") from exc
    if len(supplied_files) != len(_PACK_ROLES):
        raise LibraryEpochError("epoch pack must contain exactly three files")
    if any(type(path) is not str for path in supplied_files):
        raise LibraryEpochError("epoch pack paths must be text")
    if any(type(raw) is not bytes or not raw for raw in supplied_files.values()):
        raise LibraryEpochError("epoch pack values must be nonempty exact bytes")
    rows: list[dict[str, object]] = []
    for role in _PACK_ROLES:
        matches = [
            (path, raw)
            for path, raw in supplied_files.items()
            if f"/{role}-" in path
        ]
        if len(matches) != 1:
            raise LibraryEpochError(f"epoch pack must contain exactly one {role} file")
        path, raw = matches[0]
        _safe_relative_path("epoch pack path", path, prefix="pack/")
        digest = _sha256_bytes(raw)
        if path != _pack_path(role, digest):
            raise LibraryEpochError("epoch pack path is not content addressed")
        rows.append(
            {"bytes": len(raw), "path": path, "role": role, "sha256": digest}
        )
    preimage = {
        "files": rows,
        "format": EPOCH_PACK_ROOT_PREIMAGE_FORMAT,
        "v": EPOCH_PACK_VERSION,
    }
    return {
        "files": rows,
        "format": EPOCH_PACK_FORMAT,
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
        "v": EPOCH_PACK_VERSION,
    }


def _validate_pack(
    value: object,
    files: Mapping[str, bytes] | None,
) -> tuple[dict[str, object], dict[str, bytes]]:
    pack = _require_fields("epoch pack", value, _PACK_FIELDS)
    if pack.get("format") != EPOCH_PACK_FORMAT:
        raise LibraryEpochError("epoch pack identity is malformed")
    _require_version("epoch pack version", pack.get("v"), EPOCH_PACK_VERSION)
    preimage = _require_fields(
        "epoch pack root preimage",
        pack.get("root_preimage"),
        _PACK_ROOT_PREIMAGE_FIELDS,
    )
    rows = pack.get("files")
    expected_preimage = {
        "files": rows,
        "format": EPOCH_PACK_ROOT_PREIMAGE_FORMAT,
        "v": EPOCH_PACK_VERSION,
    }
    if type(rows) is not list or len(rows) != len(_PACK_ROLES):
        raise LibraryEpochError("epoch pack root preimage is malformed")
    _require_version(
        "epoch pack root-preimage version",
        preimage.get("v"),
        EPOCH_PACK_VERSION,
    )
    if not _same_canonical_json(preimage, expected_preimage):
        raise LibraryEpochError("epoch pack root preimage is malformed")
    if pack.get("root_sha256") != _sha256_json(preimage):
        raise LibraryEpochError("epoch pack root does not match its preimage")
    if files is None or not isinstance(files, Mapping):
        raise LibraryEpochError("frozen epoch requires all supplied pack bytes")
    try:
        supplied_files = dict(files.items())
    except (AttributeError, TypeError, ValueError) as exc:
        raise LibraryEpochError("supplied epoch pack mapping is malformed") from exc
    detached_files: dict[str, bytes] = {}
    seen_roles: set[str] = set()
    manifest_paths: set[str] = set()
    for index, row_value in enumerate(rows):
        row = _require_fields(f"epoch pack file {index}", row_value, _PACK_FILE_FIELDS)
        role = row.get("role")
        path = row.get("path")
        if type(role) is not str or role not in _PACK_ROLES or role in seen_roles:
            raise LibraryEpochError("epoch pack roles are malformed")
        if type(path) is not str:
            raise LibraryEpochError("epoch pack path is malformed")
        _safe_relative_path("epoch pack path", path, prefix="pack/")
        if path in manifest_paths:
            raise LibraryEpochError("epoch pack paths are duplicated")
        manifest_paths.add(path)
        raw = supplied_files.get(path)
        if type(raw) is not bytes or not raw:
            raise LibraryEpochError("epoch pack file must be exact nonempty bytes")
        digest = _require_sha256("epoch pack file hash", row.get("sha256"))
        byte_count = _positive_integer("epoch pack file byte count", row.get("bytes"))
        if (
            byte_count != len(raw)
            or digest != _sha256_bytes(raw)
            or path != _pack_path(role, digest)
        ):
            raise LibraryEpochError("epoch pack file identity is malformed")
        detached_files[path] = bytes(raw)
        seen_roles.add(role)
    if set(supplied_files) != manifest_paths:
        raise LibraryEpochError("supplied epoch pack file set is incomplete or extra")
    if tuple(row["role"] for row in rows) != _PACK_ROLES:
        raise LibraryEpochError("epoch pack file order is malformed")
    return _detached_object(pack, "epoch pack"), detached_files


def build_candidate_library_epoch_pack(
    candidate: object,
) -> dict[str, bytes]:
    """Copy the live candidate inputs into an in-memory content-addressed pack."""

    checked = validate_library_epoch(candidate, require_live=True)
    if checked["status"] != CANDIDATE_STATUS:
        raise LibraryEpochError("only a candidate can prepare an epoch pack")
    raw_by_role = {
        "catalog": _read_bounded_regular_file(
            _CATALOG_PATH,
            label="candidate catalog pack input",
            limit=MAX_CATALOG_BYTES,
        ),
        "semantic-profile": _read_bounded_regular_file(
            SEMANTIC_PROFILE_PATH,
            label="candidate semantic-profile pack input",
            limit=MAX_SCHEMA_BYTES,
        ),
        "h0-replay": _read_bounded_regular_file(
            _H0_REPORT_PATH,
            label="candidate H0 replay pack input",
            limit=MAX_H0_REPORT_BYTES,
        ),
    }
    files = {
        _pack_path(role, _sha256_bytes(raw)): bytes(raw)
        for role, raw in raw_by_role.items()
    }
    _validate_pack(_pack_manifest(files), files)
    return files


def _benchmark(value: object) -> dict[str, object]:
    benchmark = _require_fields("benchmark", value, _BENCHMARK_FIELDS)
    status = benchmark.get("status")
    commitment = benchmark.get("commitment_sha256")
    if status == "not-sealed" and commitment is None:
        return {"commitment_sha256": None, "status": "not-sealed"}
    if status == "sealed":
        return {
            "commitment_sha256": _require_sha256(
                "benchmark commitment", commitment
            ),
            "status": "sealed",
        }
    raise LibraryEpochError("benchmark status/commitment is malformed")


def _root_preimage(body: dict[str, object]) -> dict[str, object]:
    if "root_preimage" in body or "root_sha256" in body:
        raise LibraryEpochError("epoch root preimage cannot contain itself")
    return {
        "format": LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT,
        "v": LIBRARY_EPOCH_VERSION,
        "payload": deepcopy(body),
    }


def _with_root(body: dict[str, object]) -> dict[str, object]:
    preimage = _root_preimage(body)
    return {
        **deepcopy(body),
        "root_preimage": preimage,
        "root_sha256": _sha256_json(preimage),
    }


def _validate_live_profile(value: object) -> dict[str, object]:
    profile = _require_fields("semantic profile identity", value, _PROFILE_FIELDS)
    expected = _active_profile_epoch_identity()
    if profile != expected:
        if profile.get("logic") == "classical" or "classical" in str(profile).casefold():
            raise LibraryEpochError("classical material cannot contaminate an HA epoch")
        raise LibraryEpochError("epoch semantic profile differs from active H0 profile")
    return deepcopy(expected)


def _validate_repository(
    value: object, *, require_live: bool, expected_source: str
) -> dict[str, object]:
    repository = _require_fields("repository identity", value, _REPOSITORY_FIELDS)
    commit = _require_commit("repository source commit", repository.get("commit"))
    if repository.get("source") != expected_source:
        raise LibraryEpochError("repository source identity is malformed")
    dirty = repository.get("relevant_dirty")
    if type(dirty) is not bool:
        raise LibraryEpochError("repository relevant_dirty must be Boolean")
    if require_live and commit != _git_head_commit():
        raise LibraryEpochError("epoch repository source commit drifted from HEAD")
    if require_live and dirty is not _git_relevant_dirty():
        raise LibraryEpochError("epoch relevant source dirtiness drifted")
    return {"commit": commit, "relevant_dirty": dirty, "source": expected_source}


def _validate_live_catalog_identity(
    value: object, *, require_live: bool
) -> dict[str, object]:
    catalog = _require_fields(
        "catalog identity", value, _CATALOG_IDENTITY_FIELDS
    )
    expected_constants = {
        "artifact_path": CATALOG_PATH_TEXT,
        "certificate_representation": CATALOG_CERTIFICATE_REPRESENTATION,
        "id": CATALOG_ID,
        "schema": CATALOG_SCHEMA,
    }
    for field_name, expected in expected_constants.items():
        if catalog.get(field_name) != expected:
            if field_name == "artifact_path":
                raise LibraryEpochError("catalog artifact path is unsafe or unregistered")
            raise LibraryEpochError(f"catalog {field_name} is malformed")
    _safe_repository_path(
        "catalog artifact path", catalog.get("artifact_path"), prefix="artifacts/"
    )
    for field_name in (
        "artifact_sha256",
        "catalog_sha256",
        "ordered_root_sha256",
        "source_root_sha256",
    ):
        _require_sha256(f"catalog {field_name}", catalog.get(field_name))
    _positive_integer("catalog theorem count", catalog.get("theorem_count"))
    profile = _active_profile_epoch_identity()
    if catalog.get("evaluation_certificate_representation") != profile.get(
        "certificate_representation"
    ):
        raise LibraryEpochError("catalog evaluation certificate representation drifted")
    detached = _detached_object(catalog, "catalog identity")
    if require_live and detached != live_tracked_catalog_identity():
        raise LibraryEpochError("epoch catalog identity drifted from the live catalog")
    return detached


def _validate_live_h0(value: object) -> dict[str, object]:
    h0 = _require_fields("H0 replay identity", value, _H0_FIELDS)
    if h0.get("report_path") != H0_REPORT_PATH_TEXT:
        raise LibraryEpochError("H0 replay report path is unsafe or unregistered")
    _safe_repository_path(
        "H0 replay report path", h0.get("report_path"), prefix="artifacts/"
    )
    if h0 != h0_replay_identity():
        raise LibraryEpochError("epoch H0 independent replay evidence drifted")
    return deepcopy(h0)


def _pack_bytes_for_role(
    pack: dict[str, object], files: Mapping[str, bytes], role: str
) -> tuple[str, bytes]:
    for row in pack["files"]:
        if row["role"] == role:
            path = row["path"]
            return path, files[path]
    raise LibraryEpochError(f"epoch pack is missing role {role!r}")


def _validate_frozen_inputs(
    *,
    profile_value: object,
    catalog_value: object,
    h0_value: object,
    pack_value: object,
    pack_files: Mapping[str, bytes] | None,
) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    pack, files = _validate_pack(pack_value, pack_files)
    profile_path, profile_raw = _pack_bytes_for_role(pack, files, "semantic-profile")
    catalog_path, catalog_raw = _pack_bytes_for_role(pack, files, "catalog")
    h0_path, h0_raw = _pack_bytes_for_role(pack, files, "h0-replay")
    profile = _profile_identity_from_bytes(profile_raw, artifact_path=profile_path)
    catalog = _catalog_identity_from_bytes(
        catalog_raw,
        artifact_path=catalog_path,
        require_live=False,
        evaluation_certificate_representation=profile["certificate_representation"],
    )
    h0 = _h0_identity_from_bytes(
        h0_raw,
        report_path=h0_path,
        expected_profile_sha256=profile["sha256"],
    )
    if profile_value != profile:
        raise LibraryEpochError("frozen epoch profile differs from supplied pack bytes")
    if catalog_value != catalog:
        raise LibraryEpochError("frozen epoch catalog differs from supplied pack bytes")
    if h0_value != h0:
        raise LibraryEpochError("frozen epoch H0 evidence differs from supplied pack bytes")
    return profile, catalog, h0, pack


def _validate_receipt_bytes(
    raw: bytes,
    *,
    expected_candidate_root_sha256: str,
    expected_epoch_id: str,
    expected_catalog_sha256: str,
    expected_repository_commit: str,
    expected_semantic_profile_sha256: str,
    expected_pack_root_sha256: str,
) -> tuple[dict[str, object], str]:
    if type(raw) is not bytes or not raw:
        raise LibraryEpochError("independent owner receipt must be nonempty bytes")
    receipt_sha256 = _sha256_bytes(raw)
    registration = _REGISTERED_OWNER_RECEIPTS.get(receipt_sha256)
    if registration is None:
        raise LibraryEpochError(
            "owner receipt is not in the reviewed independent deposit registry"
        )
    receipt = _decode_canonical_document(
        raw, "independent owner receipt", limit=MAX_EPOCH_BYTES
    )
    _require_fields("independent owner receipt", receipt, _OWNER_RECEIPT_FIELDS)
    if (
        receipt.get("format") != OWNER_RECEIPT_FORMAT
        or receipt.get("owner_role") != OWNER_ROLE
    ):
        raise LibraryEpochError("independent owner receipt identity is malformed")
    _require_version(
        "independent owner receipt version",
        receipt.get("v"),
        OWNER_RECEIPT_VERSION,
    )
    owner_id = receipt.get("owner_id")
    if type(owner_id) is not str or _OWNER_ID_RE.fullmatch(owner_id) is None:
        raise LibraryEpochError("independent owner id is malformed")
    deposit_id = receipt.get("deposit_id")
    if type(deposit_id) is not str or _SAFE_ID_RE.fullmatch(deposit_id) is None:
        raise LibraryEpochError("independent deposit id is malformed")
    if registration != (deposit_id, owner_id):
        raise LibraryEpochError("owner receipt disagrees with its reviewed registration")
    expected = {
        "candidate_root_sha256": expected_candidate_root_sha256,
        "catalog_sha256": expected_catalog_sha256,
        "epoch_id": expected_epoch_id,
        "pack_root_sha256": expected_pack_root_sha256,
        "repository_commit": expected_repository_commit,
        "semantic_profile_sha256": expected_semantic_profile_sha256,
    }
    for field_name, expected_value in expected.items():
        if receipt.get(field_name) != expected_value:
            raise LibraryEpochError(
                f"independent owner receipt does not bind candidate {field_name}"
            )
    _benchmark(receipt.get("benchmark"))
    return receipt, receipt_sha256


def build_candidate_library_epoch(
    epoch_id: str = "authoring-head",
) -> dict[str, object]:
    """Build a non-sealed identity for the current living authoring catalog."""

    library_epoch_schema()
    if type(epoch_id) is not str or _SAFE_ID_RE.fullmatch(epoch_id) is None:
        raise LibraryEpochError("epoch id is not one bounded lowercase identifier")
    profile = _active_profile_epoch_identity()
    catalog = live_tracked_catalog_identity()
    if catalog["evaluation_certificate_representation"] != profile[
        "certificate_representation"
    ]:
        raise LibraryEpochError("catalog and semantic profile representations disagree")
    body: dict[str, object] = {
        "benchmark": {"commitment_sha256": None, "status": "not-sealed"},
        "catalog": catalog,
        "evaluation_eligible": False,
        "format": LIBRARY_EPOCH_FORMAT,
        "h0_replay": h0_replay_identity(),
        "id": epoch_id,
        "independent_commitment": None,
        "logic_mode": LOGIC_MODE,
        "pack": None,
        "repository": {
            "commit": _git_head_commit(),
            "relevant_dirty": _git_relevant_dirty(),
            "source": AUTHORING_REPOSITORY_SOURCE,
        },
        "scope": AUTHORING_SCOPE,
        "semantic_profile": profile,
        "status": CANDIDATE_STATUS,
        "v": LIBRARY_EPOCH_VERSION,
    }
    return validate_library_epoch(_with_root(body), require_live=True)


def build_frozen_library_epoch(
    candidate: object,
    *,
    independent_owner_receipt: bytes,
    pack_files: Mapping[str, bytes],
) -> dict[str, object]:
    """Freeze only through a clean candidate and reviewed external deposit.

    The v1 deposit registry is empty, so production calls fail closed.  This
    function exists to pin the eventual transition protocol and test it with a
    deliberately injected review registration; it does not publish L0.
    """

    checked = validate_library_epoch(candidate, require_live=True)
    if checked["status"] != CANDIDATE_STATUS:
        raise LibraryEpochError("only a candidate epoch can be frozen")
    if checked["repository"]["relevant_dirty"] is not False:
        raise LibraryEpochError("a dirty relevant source tree cannot be frozen")
    pack = _pack_manifest(pack_files)
    pack, supplied = _validate_pack(pack, pack_files)
    profile_path, profile_raw = _pack_bytes_for_role(pack, supplied, "semantic-profile")
    catalog_path, catalog_raw = _pack_bytes_for_role(pack, supplied, "catalog")
    h0_path, h0_raw = _pack_bytes_for_role(pack, supplied, "h0-replay")
    packed_profile = _profile_identity_from_bytes(profile_raw, artifact_path=profile_path)
    packed_catalog = _catalog_identity_from_bytes(
        catalog_raw,
        artifact_path=catalog_path,
        require_live=False,
        evaluation_certificate_representation=packed_profile[
            "certificate_representation"
        ],
    )
    packed_h0 = _h0_identity_from_bytes(
        h0_raw,
        report_path=h0_path,
        expected_profile_sha256=packed_profile["sha256"],
    )
    for packed, live, path_field in (
        (packed_profile, checked["semantic_profile"], "artifact_path"),
        (packed_catalog, checked["catalog"], "artifact_path"),
        (packed_h0, checked["h0_replay"], "report_path"),
    ):
        if {
            key: value for key, value in packed.items() if key != path_field
        } != {
            key: value for key, value in live.items() if key != path_field
        }:
            raise LibraryEpochError("candidate pack content differs from live candidate")
    receipt, receipt_sha256 = _validate_receipt_bytes(
        independent_owner_receipt,
        expected_candidate_root_sha256=checked["root_sha256"],
        expected_epoch_id=checked["id"],
        expected_catalog_sha256=checked["catalog"]["catalog_sha256"],
        expected_repository_commit=checked["repository"]["commit"],
        expected_semantic_profile_sha256=checked["semantic_profile"]["sha256"],
        expected_pack_root_sha256=pack["root_sha256"],
    )
    benchmark = _benchmark(receipt["benchmark"])
    body = {
        key: deepcopy(value)
        for key, value in checked.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    body.update(
        {
            "benchmark": benchmark,
            "evaluation_eligible": benchmark["status"] == "sealed",
            "independent_commitment": {
                "candidate_root_sha256": checked["root_sha256"],
                "deposit_id": receipt["deposit_id"],
                "owner_id": receipt["owner_id"],
                "owner_role": OWNER_ROLE,
                "pack_root_sha256": pack["root_sha256"],
                "receipt_format": OWNER_RECEIPT_FORMAT,
                "receipt_sha256": receipt_sha256,
                "receipt_v": OWNER_RECEIPT_VERSION,
            },
            "catalog": packed_catalog,
            "h0_replay": packed_h0,
            "pack": pack,
            "repository": {
                **checked["repository"],
                "source": FROZEN_REPOSITORY_SOURCE,
            },
            "scope": FROZEN_SCOPE,
            "semantic_profile": packed_profile,
            "status": FROZEN_STATUS,
        }
    )
    return validate_library_epoch(
        _with_root(body),
        independent_owner_receipt=independent_owner_receipt,
        pack_files=pack_files,
    )


def validate_library_epoch(
    value: object,
    *,
    require_live: bool = False,
    independent_owner_receipt: bytes | None = None,
    pack_files: Mapping[str, bytes] | None = None,
) -> dict[str, object]:
    """Validate one exact candidate or externally receipted frozen epoch."""

    epoch = _detached_object(value, "library epoch")
    _require_fields("library epoch", epoch, _EPOCH_FIELDS)
    if (
        epoch.get("format") != LIBRARY_EPOCH_FORMAT
    ):
        raise LibraryEpochError("library epoch identity is malformed")
    _require_version("library epoch version", epoch.get("v"), LIBRARY_EPOCH_VERSION)
    epoch_id = epoch.get("id")
    if type(epoch_id) is not str or _SAFE_ID_RE.fullmatch(epoch_id) is None:
        raise LibraryEpochError("epoch id is malformed")
    if epoch.get("logic_mode") != LOGIC_MODE:
        if epoch.get("logic_mode") == "classical":
            raise LibraryEpochError("classical material cannot contaminate an HA epoch")
        raise LibraryEpochError("library epoch logic mode is malformed")

    benchmark = _benchmark(epoch.get("benchmark"))
    status = epoch.get("status")
    if status == CANDIDATE_STATUS:
        repository = _validate_repository(
            epoch.get("repository"),
            require_live=True,
            expected_source=AUTHORING_REPOSITORY_SOURCE,
        )
        profile = _validate_live_profile(epoch.get("semantic_profile"))
        catalog = _validate_live_catalog_identity(
            epoch.get("catalog"), require_live=True
        )
        h0 = _validate_live_h0(epoch.get("h0_replay"))
        pack = None
        if (
            epoch.get("scope") != AUTHORING_SCOPE
            or epoch.get("evaluation_eligible") is not False
            or epoch.get("independent_commitment") is not None
            or epoch.get("pack") is not None
            or benchmark != {"commitment_sha256": None, "status": "not-sealed"}
        ):
            raise LibraryEpochError(
                "candidate authoring HEAD cannot claim a freeze or sealed benchmark"
            )
        if independent_owner_receipt is not None or pack_files is not None:
            raise LibraryEpochError("candidate epoch must not consume frozen-pack evidence")
    elif status == FROZEN_STATUS:
        if require_live:
            raise LibraryEpochError("frozen validation must not resolve living HEAD")
        if epoch.get("scope") != FROZEN_SCOPE:
            raise LibraryEpochError("frozen epoch has the wrong immutable scope")
        repository = _validate_repository(
            epoch.get("repository"),
            require_live=False,
            expected_source=FROZEN_REPOSITORY_SOURCE,
        )
        if repository["relevant_dirty"] is not False:
            raise LibraryEpochError("frozen epoch cannot claim a dirty source commit")
        profile, catalog, h0, pack = _validate_frozen_inputs(
            profile_value=epoch.get("semantic_profile"),
            catalog_value=epoch.get("catalog"),
            h0_value=epoch.get("h0_replay"),
            pack_value=epoch.get("pack"),
            pack_files=pack_files,
        )
        commitment = _require_fields(
            "independent commitment",
            epoch.get("independent_commitment"),
            _COMMITMENT_FIELDS,
        )
        _require_version(
            "independent commitment receipt version",
            commitment.get("receipt_v"),
            OWNER_RECEIPT_VERSION,
        )
        if independent_owner_receipt is None:
            raise LibraryEpochError(
                "frozen epoch requires the separate independent owner receipt"
            )
        candidate_root = _require_sha256(
            "committed candidate root", commitment.get("candidate_root_sha256")
        )
        receipt, receipt_sha256 = _validate_receipt_bytes(
            independent_owner_receipt,
            expected_candidate_root_sha256=candidate_root,
            expected_epoch_id=epoch["id"],
            expected_catalog_sha256=catalog["catalog_sha256"],
            expected_repository_commit=repository["commit"],
            expected_semantic_profile_sha256=profile["sha256"],
            expected_pack_root_sha256=pack["root_sha256"],
        )
        expected_commitment = {
            "candidate_root_sha256": candidate_root,
            "deposit_id": receipt["deposit_id"],
            "owner_id": receipt["owner_id"],
            "owner_role": OWNER_ROLE,
            "pack_root_sha256": pack["root_sha256"],
            "receipt_format": OWNER_RECEIPT_FORMAT,
            "receipt_sha256": receipt_sha256,
            "receipt_v": OWNER_RECEIPT_VERSION,
        }
        if commitment != expected_commitment:
            raise LibraryEpochError("frozen epoch owner receipt reference is forged")
        if benchmark != _benchmark(receipt["benchmark"]):
            raise LibraryEpochError("frozen epoch benchmark differs from owner receipt")
        if epoch.get("evaluation_eligible") is not (benchmark["status"] == "sealed"):
            raise LibraryEpochError("frozen epoch evaluation eligibility is forged")
    else:
        raise LibraryEpochError("library epoch status is unsupported or forged")

    if h0["profile_sha256"] != profile["sha256"]:
        raise LibraryEpochError("H0 replay and epoch semantic profiles differ")

    preimage = _require_fields(
        "library epoch root preimage", epoch.get("root_preimage"), _ROOT_PREIMAGE_FIELDS
    )
    if (
        preimage.get("format") != LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT
    ):
        raise LibraryEpochError("library epoch root preimage identity is malformed")
    _require_version(
        "library epoch root-preimage version",
        preimage.get("v"),
        LIBRARY_EPOCH_VERSION,
    )
    body = {
        key: deepcopy(item)
        for key, item in epoch.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    if not _same_canonical_json(preimage.get("payload"), body):
        raise LibraryEpochError("library epoch root preimage does not match its payload")
    root = _require_sha256("library epoch root", epoch.get("root_sha256"))
    if root != _sha256_json(preimage):
        raise LibraryEpochError("library epoch root does not match its explicit preimage")

    # Reassemble validated components so subclasses or caller-owned containers
    # cannot survive validation.
    body.update(
        {
            "benchmark": benchmark,
            "catalog": catalog,
            "h0_replay": h0,
            "pack": pack,
            "repository": repository,
            "semantic_profile": profile,
        }
    )
    validated = _with_root(body)
    if not _same_canonical_json(validated.get("root_preimage"), preimage):
        raise LibraryEpochError("library epoch validation changed the committed preimage")
    if validated.get("root_sha256") != root:
        raise LibraryEpochError("library epoch validation changed the committed root")
    return _detached_object(validated, "validated library epoch")


def load_library_epoch(
    path: Path,
    *,
    require_live: bool = False,
    independent_owner_receipt_path: Path | None = None,
    pack_root: Path | None = None,
) -> dict[str, object]:
    """Load a canonical epoch document and, for frozen epochs, its receipt."""

    raw = _read_bounded_regular_file(
        path,
        label="library epoch document",
        limit=MAX_EPOCH_BYTES,
    )
    value = _decode_canonical_document(raw, "library epoch", limit=MAX_EPOCH_BYTES)
    receipt: bytes | None = None
    if independent_owner_receipt_path is not None:
        receipt = _read_bounded_regular_file(
            independent_owner_receipt_path,
            label="independent owner receipt",
            limit=MAX_EPOCH_BYTES,
        )
    pack_files: dict[str, bytes] | None = None
    if pack_root is not None:
        pack_value = value.get("pack")
        if type(pack_value) is not dict or type(pack_value.get("files")) is not list:
            raise LibraryEpochError("epoch document has no pack manifest")
        pack_files = {}
        try:
            root = pack_root.resolve(strict=True)
            if not root.is_dir():
                raise LibraryEpochError("supplied epoch pack root is not a directory")
        except (OSError, RuntimeError) as exc:
            raise LibraryEpochError("cannot resolve supplied epoch pack root") from exc
        for row in pack_value["files"]:
            if type(row) is not dict:
                raise LibraryEpochError("epoch pack file row is malformed")
            role = row.get("role")
            if type(role) is not str or role not in _PACK_ROLE_BYTE_LIMITS:
                raise LibraryEpochError("epoch pack role is malformed")
            path_text = _safe_relative_path(
                "epoch pack path", row.get("path"), prefix="pack/"
            )
            try:
                unresolved = root / path_text
                parent = unresolved.parent.resolve(strict=True)
                parent.relative_to(root)
                supplied_path = parent / unresolved.name
            except (OSError, RuntimeError, ValueError) as exc:
                raise LibraryEpochError("cannot read supplied epoch pack") from exc
            pack_files[path_text] = _read_bounded_regular_file(
                supplied_path,
                label=f"supplied epoch pack {role!r} file",
                limit=_PACK_ROLE_BYTE_LIMITS[role],
            )
    return validate_library_epoch(
        value,
        require_live=require_live,
        independent_owner_receipt=receipt,
        pack_files=pack_files,
    )


__all__ = [
    "AUTHORING_SCOPE",
    "AUTHORING_REPOSITORY_SOURCE",
    "CANDIDATE_STATUS",
    "CATALOG_CERTIFICATE_REPRESENTATION",
    "CATALOG_ID",
    "CATALOG_PATH_TEXT",
    "FROZEN_SCOPE",
    "FROZEN_STATUS",
    "FROZEN_REPOSITORY_SOURCE",
    "H0_REPORT_PATH_TEXT",
    "H0_REPORT_SHA256",
    "LIBRARY_EPOCH_FORMAT",
    "LIBRARY_EPOCH_ROOT_PREIMAGE_FORMAT",
    "LIBRARY_EPOCH_SCHEMA_FORMAT",
    "LIBRARY_EPOCH_SCHEMA_ID",
    "LIBRARY_EPOCH_SCHEMA_PATH",
    "LIBRARY_EPOCH_SCHEMA_SHA256",
    "LIBRARY_EPOCH_SCHEMA_VERSION",
    "LIBRARY_EPOCH_VERSION",
    "LOGIC_MODE",
    "LibraryEpochError",
    "OWNER_RECEIPT_FORMAT",
    "OWNER_RECEIPT_VERSION",
    "OWNER_ROLE",
    "EPOCH_PACK_FORMAT",
    "EPOCH_PACK_ROOT_PREIMAGE_FORMAT",
    "EPOCH_PACK_VERSION",
    "build_candidate_library_epoch",
    "build_candidate_library_epoch_pack",
    "build_frozen_library_epoch",
    "canonical_document_bytes",
    "canonical_json_bytes",
    "h0_replay_identity",
    "library_epoch_schema",
    "library_epoch_schema_identity",
    "live_tracked_catalog_identity",
    "load_library_epoch",
    "validate_library_epoch",
]
