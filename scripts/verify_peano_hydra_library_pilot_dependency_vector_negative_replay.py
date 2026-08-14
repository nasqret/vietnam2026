#!/usr/bin/env python3
"""Describe, execute, or validate the independent Hydra A2.3c replay.

The default operation emits only the source-protocol receipt.  It performs no
proof replay and writes no file.  A real campaign requires both ``--execute``
and the exact confirmation token; even then output is canonical stdout unless
an absent explicit create-only destination is supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import tempfile
import time
import warnings


LEXICAL_CLI_PATH = Path(os.path.abspath(__file__))
ROOT = LEXICAL_CLI_PATH.parents[1]
EXPECTED_CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py"
)
PY_ROOT = ROOT / "peano-lab" / "py"
SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-dependency-vector-negative-replay-schema-v1.json"
)
REPLAYER_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_negative_replay.py"
)
REPLAYER_MODULE_NAME = "_peano_hydra_a23c_independent_negative_replayer"

SCHEMA_SOURCE_BYTES = 26_551
SCHEMA_SOURCE_SHA256 = (
    "be38f796e9d8923024514962f7cc5a5a4f19c828cf502e2912f1ea5094d12ce4"
)
SCHEMA_SEMANTIC_SHA256 = (
    "a0d84c3168a9b779bfb5fdc483a2ec847e4cc34f85bcf8aee4c7351a6363ccb0"
)
REPLAYER_SOURCE_BYTES = 91_304
REPLAYER_SOURCE_SHA256 = (
    "f5b5dd45c0ce4e2ed5587fd41b7ea206e92ee05526aebf7be96d80f5bb591aa4"
)
IMPLEMENTATION_SOURCE_ROOT_SHA256 = (
    "b37836ec81ab2f0af638427a937d92519b5b70579de86d38c9321514692f55c1"
)
EXPECTED_IMPLEMENTATION_SOURCE_COUNT = 39
MAX_SCHEMA_BYTES = 1_000_000
MAX_SOURCE_BYTES = 16_000_000
MAX_DOCUMENT_BYTES = 16_000_000
MAX_STDOUT_BYTES = 16_000_000
MAX_STDERR_BYTES = 1_048_576
MAX_WALL_SECONDS = 900
PYCACHE_PREFIX = "/proc/peano-hydra-a23c-disabled-pycache"
CONFIRMATION = "PEANO-HYDRA-A23C-NEGATIVE-REPLAY"
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_FORBIDDEN_ENVIRONMENT = (
    "PYTHONCASEOK",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTHONOPTIMIZE",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "PYTHONUSERBASE",
    "PYTHONWARNINGS",
)
_WORKER_ENVIRONMENT = "PEANO_HYDRA_A23C_CONTROLLED_WORKER"
_WORKER_CAPABILITY_FD = "PEANO_HYDRA_A23C_CAPABILITY_FD"
_WORKER_CAPABILITY_SHA256 = "PEANO_HYDRA_A23C_CAPABILITY_SHA256"
_REQUIRED_STDLIB_MODULES = (
    "argparse",
    "collections",
    "copy",
    "dataclasses",
    "functools",
    "hashlib",
    "importlib",
    "itertools",
    "json",
    "math",
    "os",
    "pathlib",
    "platform",
    "re",
    "selectors",
    "stat",
    "subprocess",
    "sys",
    "tempfile",
    "time",
    "types",
    "typing",
    "unicodedata",
    "uuid",
    "warnings",
)


class LibraryPilotDependencyVectorNegativeReplayCLIError(ValueError):
    """The A2.3c CLI boundary, input, execution, or output is invalid."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value: str) -> object:
    raise ValueError(f"unsupported JSON number {value!r}")


def _compact_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_bytes(value: object) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")


def _decode_object(raw: bytes, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_number,
            parse_float=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"{label} must be one object"
        )
    return value


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _require_directory_chain(path: Path, *, label: str) -> None:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    f"{label} contains a symlink or non-directory"
                )
    except LibraryPilotDependencyVectorNegativeReplayCLIError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"cannot inspect {label}"
        ) from exc


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_regular_with_identity(
    path: Path, *, label: str, limit: int
) -> tuple[bytes, tuple[int, int, int, int, int]]:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label=f"{label} ancestors")
    try:
        metadata = absolute.lstat()
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _stat_identity(metadata) != _stat_identity(before)
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"{label} is not the inspected bounded regular file"
            )
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        path_after = absolute.lstat()
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)
    if (
        len(raw) > limit
        or not stat.S_ISREG(path_after.st_mode)
        or _stat_identity(before) != _stat_identity(after)
        or _stat_identity(after) != _stat_identity(path_after)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"{label} changed or exceeded its bound while read"
        )
    return raw, _stat_identity(after)


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    raw, _identity = _read_regular_with_identity(
        path, label=label, limit=limit
    )
    return raw


def _require_exact_cli_source() -> None:
    if LEXICAL_CLI_PATH != EXPECTED_CLI_PATH:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "A2.3c CLI lexical path drifted"
        )
    _require_directory_chain(
        LEXICAL_CLI_PATH.parent, label="A2.3c CLI source ancestors"
    )
    try:
        metadata = LEXICAL_CLI_PATH.lstat()
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot inspect A2.3c CLI source"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "A2.3c CLI source must be the exact non-symlink regular file"
        )


def _safe_relative(value: object, *, label: str) -> Path:
    if type(value) is not str:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"{label} path is malformed"
        )
    path = Path(value)
    if (
        path.is_absolute()
        or not path.parts
        or any(part in ("", ".", "..") for part in path.parts)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"{label} path is unsafe"
        )
    return path


def _authenticate_schema_sources_and_inputs() -> tuple[
    dict[str, object],
    bytes,
    dict[str, tuple[int, int, int, int, int]],
]:
    """Authenticate every non-stdlib byte before loading Peano code."""

    schema_raw = _read_regular(
        SCHEMA_PATH, label="A2.3c schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        len(schema_raw) != SCHEMA_SOURCE_BYTES
        or hashlib.sha256(schema_raw).hexdigest() != SCHEMA_SOURCE_SHA256
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "A2.3c schema source identity drifted"
        )
    schema = _decode_object(schema_raw, label="A2.3c schema")
    if (
        _canonical_bytes(schema) != schema_raw
        or hashlib.sha256(_compact_bytes(schema)).hexdigest()
        != SCHEMA_SEMANTIC_SHA256
        or schema.get("format")
        != "peano-hydra-library-pilot-dependency-vector-negative-replay-schema"
        or schema.get("v") != 1
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "A2.3c schema canonical or semantic identity drifted"
        )
    rows = schema.get("implementation_sources")
    if type(rows) is not list or len(rows) != EXPECTED_IMPLEMENTATION_SOURCE_COUNT:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "implementation source vector count drifted"
        )
    if (
        schema.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or hashlib.sha256(_compact_bytes(rows)).hexdigest()
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "implementation source vector root drifted"
        )
    seen: set[Path] = set()
    source_identities: dict[str, tuple[int, int, int, int, int]] = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "implementation source row is malformed"
            )
        relative = _safe_relative(row.get("path"), label="implementation source")
        digest = row.get("sha256")
        if (
            relative in seen
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "implementation source identity is duplicated or malformed"
            )
        raw, source_identity = _read_regular_with_identity(
            ROOT / relative,
            label=f"implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if hashlib.sha256(raw).hexdigest() != digest:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"implementation source {relative.as_posix()!r} drifted"
        )
        seen.add(relative)
        source_identities[relative.as_posix()] = source_identity
    fixed = schema.get("fixed_inputs")
    if type(fixed) is not dict:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "fixed input vector is malformed"
        )
    for label, identity in fixed.items():
        if type(identity) is not dict:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"fixed input {label!r} is malformed"
            )
        relative = _safe_relative(identity.get("path"), label=f"fixed input {label}")
        expected_bytes = identity.get("bytes")
        digest = identity.get("artifact_sha256")
        if (
            type(expected_bytes) is not int
            or not 0 <= expected_bytes <= MAX_DOCUMENT_BYTES
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"fixed input identity {label!r} drifted"
            )
        raw = _read_regular(
            ROOT / relative,
            label=f"fixed input {label!r}",
            limit=MAX_DOCUMENT_BYTES,
        )
        if len(raw) != expected_bytes or hashlib.sha256(raw).hexdigest() != digest:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"fixed input {label!r} artifact identity drifted"
            )
    replayer_raw = _read_regular(
        REPLAYER_PATH, label="independent A2.3c replayer", limit=MAX_SOURCE_BYTES
    )
    if (
        len(replayer_raw) != REPLAYER_SOURCE_BYTES
        or hashlib.sha256(replayer_raw).hexdigest() != REPLAYER_SOURCE_SHA256
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "independent A2.3c replayer source identity drifted"
        )
    return schema, replayer_raw, source_identities


def _require_controlled_worker() -> None:
    seed = os.environ.get("PYTHONHASHSEED")
    if (
        os.environ.get(_WORKER_ENVIRONMENT) != "1"
        or getattr(sys.flags, "safe_path", False) is not True
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.flags.optimize != 0
        or sys.dont_write_bytecode is not True
        or type(seed) is not str
        or not seed.isdecimal()
        or any(name in os.environ for name in _FORBIDDEN_ENVIRONMENT)
        or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
        or sys.pycache_prefix != PYCACHE_PREFIX
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "A2.3c worker requires fresh controlled -B -P -s -S execution"
        )
    try:
        cwd = Path.cwd().resolve(strict=True)
        wanted = ROOT.resolve(strict=True)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot resolve controlled worker cwd"
        ) from exc
    if cwd != wanted:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled worker cwd differs from repository root"
        )
    try:
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot inspect disabled pycache prefix"
        ) from exc
    else:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "disabled pycache prefix unexpectedly exists"
        )


def _consume_worker_capability() -> None:
    descriptor_text = os.environ.pop(_WORKER_CAPABILITY_FD, None)
    expected = os.environ.pop(_WORKER_CAPABILITY_SHA256, None)
    if (
        type(descriptor_text) is not str
        or not descriptor_text.isdecimal()
        or type(expected) is not str
        or _SHA256_RE.fullmatch(expected) is None
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled worker capability is absent or malformed"
        )
    descriptor = int(descriptor_text)
    if descriptor < 3:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled worker capability descriptor is unsafe"
        )
    try:
        token = os.read(descriptor, 65)
        trailing = os.read(descriptor, 1)
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot consume controlled worker capability"
        ) from exc
    finally:
        try:
            os.close(descriptor)
        except OSError:
            pass
    if (
        len(token) != 64
        or trailing != b""
        or hashlib.sha256(token).hexdigest() != expected
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled worker capability did not authenticate"
        )


def _require_clean_preimport_state() -> None:
    forbidden = sorted(
        name
        for name in sys.modules
        if name == "training"
        or name.startswith("training.")
        or name.startswith("peano_lab")
    )
    if forbidden:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled A2.3c worker is contaminated before direct load"
        )
    root_text = str(ROOT.resolve(strict=True))
    for name in (
        "argparse",
        "hashlib",
        "importlib",
        "json",
        "pathlib",
        "subprocess",
        "warnings",
    ):
        module = sys.modules.get(name)
        source = None if module is None else getattr(module, "__file__", None)
        if type(source) is str and str(Path(source).resolve()).startswith(root_text + os.sep):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"standard-library module {name!r} was shadowed by the repository"
            )


def _preflight_stdlib_and_import_path() -> None:
    wanted_meta_path = (
        importlib.machinery.BuiltinImporter,
        importlib.machinery.FrozenImporter,
        importlib.machinery.PathFinder,
    )
    if tuple(sys.meta_path) != wanted_meta_path:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "controlled worker has a nonstandard meta-path importer"
        )
    root = ROOT.resolve(strict=True)
    for entry in sys.path:
        if not entry:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "controlled worker import path contains the current directory"
            )
        try:
            resolved = Path(entry).resolve(strict=True)
        except OSError:
            continue
        if resolved == root or root in resolved.parents:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "controlled worker import path enters the repository before preflight"
            )
    for name in _REQUIRED_STDLIB_MODULES:
        module = importlib.import_module(name)
        source = getattr(module, "__file__", None)
        if type(source) is str:
            try:
                resolved = Path(source).resolve(strict=True)
            except OSError as exc:
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    f"cannot resolve standard-library module {name!r}"
                ) from exc
            if resolved == root or root in resolved.parents:
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    f"standard-library module {name!r} was shadowed"
                )


def _attest_stdlib_modules(authenticated: dict[str, object]) -> None:
    if type(authenticated) is not dict or set(authenticated) != set(
        _REQUIRED_STDLIB_MODULES
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "authenticated standard-library closure is malformed"
        )
    for name, module in authenticated.items():
        if sys.modules.get(name) is not module:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"standard-library module {name!r} changed during direct load"
            )


def _attest_authenticated_implementation_bytes(
    schema: dict[str, object],
    authenticated: dict[str, tuple[int, int, int, int, int]],
) -> None:
    rows = schema.get("implementation_sources")
    if type(rows) is not list:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "implementation source vector is malformed after direct load"
        )
    paths = {
        row.get("path")
        for row in rows
        if type(row) is dict and type(row.get("path")) is str
    }
    if (
        len(paths) != EXPECTED_IMPLEMENTATION_SOURCE_COUNT
        or type(authenticated) is not dict
        or set(authenticated) != paths
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "authenticated implementation source receipt vector drifted"
        )
    for row in rows:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "implementation source row drifted after direct load"
            )
        relative = _safe_relative(row["path"], label="implementation source")
        registered_digest = row["sha256"]
        prior_identity = authenticated.get(relative.as_posix())
        if (
            type(prior_identity) is not tuple
            or len(prior_identity) != 5
            or not all(type(item) is int for item in prior_identity)
            or type(registered_digest) is not str
            or _SHA256_RE.fullmatch(registered_digest) is None
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "authenticated implementation source receipt is malformed"
            )
        raw, current_identity = _read_regular_with_identity(
            ROOT / relative,
            label=f"post-load implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if (
            current_identity != prior_identity
            or hashlib.sha256(raw).hexdigest() != registered_digest
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"implementation source {relative.as_posix()!r} changed during load"
            )


def _implementation_module_map(
    schema: dict[str, object],
) -> dict[str, tuple[Path, bool]]:
    result: dict[str, tuple[Path, bool]] = {}
    for row in schema["implementation_sources"]:
        relative = Path(row["path"])
        try:
            module_relative = relative.relative_to("peano-lab/py")
        except ValueError as exc:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "implementation source escaped the Peano package root"
            ) from exc
        parts = list(module_relative.parts)
        is_package = parts[-1] == "__init__.py"
        if is_package:
            parts.pop()
        else:
            parts[-1] = Path(parts[-1]).stem
        name = ".".join(parts)
        if not name or name in result:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "implementation module map is duplicated or malformed"
            )
        result[name] = (ROOT / relative, is_package)
    return result


def _preflight_peano_source_specs(schema: dict[str, object]) -> None:
    module_map = _implementation_module_map(schema)
    top_source, _ = module_map["peano_lab"]
    top_specification = importlib.machinery.PathFinder.find_spec(
        "peano_lab", sys.path
    )
    if (
        top_specification is None
        or type(top_specification.loader)
        is not importlib.machinery.SourceFileLoader
        or top_specification.origin is None
        or Path(top_specification.origin).resolve(strict=True)
        != top_source.resolve(strict=True)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "global Peano package preference drifted"
        )
    for name, (source, is_package) in module_map.items():
        search_root = source.parent.parent if is_package else source.parent
        specification = importlib.machinery.PathFinder.find_spec(
            name, [str(search_root)]
        )
        expected_locations = [str(source.parent)] if is_package else None
        if (
            specification is None
            or type(specification.loader)
            is not importlib.machinery.SourceFileLoader
            or specification.origin is None
            or Path(specification.origin).resolve(strict=True)
            != source.resolve(strict=True)
            or specification.cached is None
            or not specification.cached.startswith(PYCACHE_PREFIX + "/")
            or (
                expected_locations is None
                and specification.submodule_search_locations is not None
            )
            or (
                expected_locations is not None
                and (
                    specification.submodule_search_locations is None
                    or list(specification.submodule_search_locations)
                    != expected_locations
                )
            )
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"Peano source specification {name!r} drifted"
            )


def _attest_loaded_source_closure(
    schema: dict[str, object], replayer: object
) -> None:
    expected = _implementation_module_map(schema)
    replayer_specification = getattr(replayer, "__spec__", None)
    replayer_loader = getattr(replayer, "__loader__", None)
    if (
        sys.modules.get(REPLAYER_MODULE_NAME) is not replayer
        or getattr(replayer, "__name__", None) != REPLAYER_MODULE_NAME
        or getattr(replayer, "__package__", None) != ""
        or getattr(replayer, "__file__", None) is None
        or Path(replayer.__file__).resolve(strict=True)
        != REPLAYER_PATH.resolve(strict=True)
        or replayer_specification is None
        or replayer_specification.name != REPLAYER_MODULE_NAME
        or replayer_specification.origin is None
        or Path(replayer_specification.origin).resolve(strict=True)
        != REPLAYER_PATH.resolve(strict=True)
        or replayer_specification.cached is None
        or not replayer_specification.cached.startswith(PYCACHE_PREFIX + "/")
        or replayer_specification.submodule_search_locations is not None
        or type(replayer_specification.loader)
        is not importlib.machinery.SourceFileLoader
        or replayer_loader is not replayer_specification.loader
        or getattr(replayer_loader, "path", None) != str(REPLAYER_PATH)
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "independent replayer module identity drifted after direct load"
        )
    loaded_names = {
        name for name in sys.modules if name == "peano_lab" or name.startswith("peano_lab.")
    }
    if loaded_names != set(expected):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "loaded Peano module closure differs from the 39-source registration"
        )
    for name, (source, is_package) in expected.items():
        module = sys.modules.get(name)
        specification = None if module is None else getattr(module, "__spec__", None)
        expected_locations = [str(source.parent)] if is_package else None
        if (
            module is None
            or specification is None
            or type(specification.loader)
            is not importlib.machinery.SourceFileLoader
            or getattr(module, "__file__", None) is None
            or Path(module.__file__).resolve(strict=True) != source.resolve(strict=True)
            or specification.origin is None
            or Path(specification.origin).resolve(strict=True)
            != source.resolve(strict=True)
            or specification.cached is None
            or not specification.cached.startswith(PYCACHE_PREFIX + "/")
            or (
                expected_locations is None
                and specification.submodule_search_locations is not None
            )
            or (
                expected_locations is not None
                and (
                    specification.submodule_search_locations is None
                    or list(specification.submodule_search_locations)
                    != expected_locations
                )
            )
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"loaded Peano module identity {name!r} drifted"
            )
    if any(name == "training" or name.startswith("training.") for name in sys.modules):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "training package contaminated the independent replayer"
        )
    expected_project_modules = {
        __name__: LEXICAL_CLI_PATH.resolve(strict=True),
        REPLAYER_MODULE_NAME: REPLAYER_PATH.resolve(strict=True),
        **{
            name: source.resolve(strict=True)
            for name, (source, _is_package) in expected.items()
        },
    }
    root = ROOT.resolve(strict=True)
    for name, module in tuple(sys.modules.items()):
        source = getattr(module, "__file__", None)
        if type(source) is not str:
            continue
        try:
            resolved = Path(source).resolve(strict=True)
        except OSError as exc:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                f"cannot resolve loaded module origin {name!r}"
            ) from exc
        if resolved == root or root in resolved.parents:
            if expected_project_modules.get(name) != resolved:
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    f"unexpected repository module {name!r} loaded during replay"
                )
    if set(expected_project_modules) - set(sys.modules):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "registered repository module closure is incomplete"
        )


def _load_replayer():
    _require_clean_preimport_state()
    _require_exact_cli_source()
    _preflight_stdlib_and_import_path()
    authenticated_stdlib = {
        name: sys.modules[name] for name in _REQUIRED_STDLIB_MODULES
    }
    schema, replayer_raw, source_identities = (
        _authenticate_schema_sources_and_inputs()
    )
    for import_root in (str(ROOT), str(PY_ROOT)):
        while import_root in sys.path:
            sys.path.remove(import_root)
    sys.path.append(str(PY_ROOT))
    _preflight_peano_source_specs(schema)
    if REPLAYER_MODULE_NAME in sys.modules:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "private replayer module name is already loaded"
        )
    specification = importlib.util.spec_from_file_location(
        REPLAYER_MODULE_NAME, REPLAYER_PATH
    )
    if (
        specification is None
        or type(specification.loader) is not importlib.machinery.SourceFileLoader
        or specification.origin is None
        or Path(specification.origin).resolve(strict=True)
        != REPLAYER_PATH.resolve(strict=True)
        or specification.cached is None
        or not specification.cached.startswith(PYCACHE_PREFIX + "/")
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "independent replayer source specification drifted"
        )
    module = importlib.util.module_from_spec(specification)
    sys.modules[REPLAYER_MODULE_NAME] = module
    try:
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        code = specification.loader.source_to_code(
            replayer_raw, str(REPLAYER_PATH)
        )
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(REPLAYER_MODULE_NAME, None)
        raise
    if Path(module.__file__).resolve(strict=True) != REPLAYER_PATH.resolve(strict=True):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "independent replayer origin drifted after load"
        )
    _attest_loaded_source_closure(schema, module)
    _attest_authenticated_implementation_bytes(schema, source_identities)
    _attest_stdlib_modules(authenticated_stdlib)
    identity = {
        "bytes": len(replayer_raw),
        "load_mode": "authenticated-source-bytes-source_to_code-exec",
        "module_name": REPLAYER_MODULE_NAME,
        "path": REPLAYER_PATH.relative_to(ROOT).as_posix(),
        "pycache_prefix": PYCACHE_PREFIX,
        "sha256": hashlib.sha256(replayer_raw).hexdigest(),
        "source_loader": "importlib.machinery.SourceFileLoader",
    }
    return module, identity


def _safe_output_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label="output parent")
    try:
        absolute.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot inspect output destination"
        ) from exc
    else:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "output destination already exists"
        )
    return absolute


def _publish_create_only(path: Path, raw: bytes) -> None:
    destination = _safe_output_parent(path)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".a23c-negative-replay-", suffix=".tmp", dir=destination.parent
    )
    temporary = Path(temporary_name)
    published = False
    temporary_identity: tuple[int, int] | None = None
    published_identity: tuple[int, int] | None = None
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(raw)
            handle.flush()
            os.fchmod(handle.fileno(), 0o644)
            os.fsync(handle.fileno())
            temporary_metadata = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(temporary_metadata.st_mode)
                or temporary_metadata.st_size != len(raw)
                or stat.S_IMODE(temporary_metadata.st_mode) != 0o644
            ):
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    "staged output descriptor identity or mode drifted"
                )
            temporary_identity = (
                temporary_metadata.st_dev,
                temporary_metadata.st_ino,
            )
        staged_path_metadata = temporary.lstat()
        if (
            stat.S_ISLNK(staged_path_metadata.st_mode)
            or not stat.S_ISREG(staged_path_metadata.st_mode)
            or (staged_path_metadata.st_dev, staged_path_metadata.st_ino)
            != temporary_identity
            or staged_path_metadata.st_size != len(raw)
            or stat.S_IMODE(staged_path_metadata.st_mode) != 0o644
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "staged output path no longer names its authenticated descriptor"
            )
        os.link(temporary, destination, follow_symlinks=False)
        published = True
        destination_metadata = destination.lstat()
        published_identity = (
            destination_metadata.st_dev,
            destination_metadata.st_ino,
        )
        if (
            stat.S_ISLNK(destination_metadata.st_mode)
            or not stat.S_ISREG(destination_metadata.st_mode)
            or published_identity != temporary_identity
            or destination_metadata.st_size != len(raw)
            or stat.S_IMODE(destination_metadata.st_mode) != 0o644
        ):
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "published output identity or mode drifted"
            )
        temporary.unlink()
        directory = os.open(
            destination.parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0),
        )
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except FileExistsError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "output destination raced or already exists"
        ) from exc
    except OSError as exc:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "cannot publish create-only output"
        ) from exc
    finally:
        if published and published_identity is not None:
            try:
                metadata = destination.lstat()
            except FileNotFoundError:
                published = False
            except OSError:
                pass
            else:
                if (
                    not stat.S_ISLNK(metadata.st_mode)
                    and stat.S_ISREG(metadata.st_mode)
                    and (metadata.st_dev, metadata.st_ino)
                    == published_identity
                ):
                    # Keep the destination only when the entire publish path,
                    # including the parent-directory fsync, completed.
                    if sys.exc_info()[0] is not None:
                        try:
                            destination.unlink()
                        except OSError:
                            pass
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            if not published:
                raise


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independent source-only A2.3c negative replay protocol"
    )
    action = parser.add_mutually_exclusive_group()
    action.add_argument(
        "--execute",
        action="store_true",
        help="run the real bounded campaign (requires --confirm)",
    )
    action.add_argument(
        "--validate-result",
        type=Path,
        help="deeply validate one existing result without rerunning tactics",
    )
    parser.add_argument(
        "--confirm",
        help="exact execution confirmation token",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="optional absent create-only canonical output path",
    )
    parser.add_argument(
        "--hash-seed",
        default="0",
        help="explicit decimal worker hash seed (default: 0)",
    )
    parser.add_argument("--_controlled-worker", action="store_true", help=argparse.SUPPRESS)
    return parser


def _worker(args: argparse.Namespace) -> int:
    _consume_worker_capability()
    _require_controlled_worker()
    module, replayer_identity = _load_replayer()
    if args.execute:
        if args.confirm != CONFIRMATION:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "real execution requires the exact confirmation token"
            )
        value = module.build_pilot_dependency_vector_negative_replay(
            ROOT, replayer_identity=replayer_identity
        )
    elif args.validate_result is not None:
        if args.confirm is not None:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "--confirm is valid only with --execute"
            )
        raw_input = _read_regular(
            args.validate_result,
            label="negative-replay result",
            limit=MAX_DOCUMENT_BYTES,
        )
        value = module._decode_document(
            raw_input, label="negative-replay result", limit=MAX_DOCUMENT_BYTES
        )
        if module.canonical_negative_replay_bytes(value) != raw_input:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "negative-replay result is noncanonical"
            )
        value = module.validate_pilot_dependency_vector_negative_replay(value, ROOT)
    else:
        if args.confirm is not None:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "--confirm is valid only with --execute"
            )
        value = module.pilot_dependency_vector_negative_replay_source_protocol(ROOT)
    raw = module.canonical_negative_replay_bytes(value)
    if args.output is not None:
        _publish_create_only(args.output, raw)
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return 0


def _controlled_environment(
    seed: str, *, capability_fd: int, capability_sha256: str
) -> dict[str, str]:
    if (
        type(seed) is not str
        or not seed.isdecimal()
        or len(seed) > 10
        or not 0 <= int(seed) <= 4_294_967_295
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "--hash-seed must be decimal text"
        )
    allowed = {
        name: value
        for name, value in os.environ.items()
        if name
        in {
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "PATH",
            "SYSTEMROOT",
            "TMPDIR",
            "TZ",
        }
    }
    allowed.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": seed,
            "PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,
            _WORKER_ENVIRONMENT: "1",
            _WORKER_CAPABILITY_FD: str(capability_fd),
            _WORKER_CAPABILITY_SHA256: capability_sha256,
        }
    )
    return allowed


def _run_bounded_child(
    command: list[str],
    *,
    cwd: Path,
    environment: dict[str, str],
    pass_fds: tuple[int, ...] = (),
    max_stdout_bytes: int = MAX_STDOUT_BYTES,
    max_stderr_bytes: int = MAX_STDERR_BYTES,
    timeout_seconds: float = MAX_WALL_SECONDS,
) -> subprocess.CompletedProcess[bytes]:
    """Run one child while hard-capping both captured byte streams in flight."""

    if (
        type(command) is not list
        or not command
        or not all(type(item) is str and item for item in command)
        or not isinstance(cwd, Path)
        or type(environment) is not dict
        or not all(
            type(name) is str and type(value) is str
            for name, value in environment.items()
        )
        or type(pass_fds) is not tuple
        or not all(type(item) is int and item >= 0 for item in pass_fds)
        or type(max_stdout_bytes) is not int
        or max_stdout_bytes < 0
        or type(max_stderr_bytes) is not int
        or max_stderr_bytes < 0
        or type(timeout_seconds) not in (int, float)
        or timeout_seconds <= 0
    ):
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "bounded child configuration is malformed"
        )
    process: subprocess.Popen[bytes] | None = None
    selector = selectors.DefaultSelector()
    streams: list[object] = []
    stdout = bytearray()
    stderr = bytearray()
    try:
        try:
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
                pass_fds=pass_fds,
            )
        except OSError as exc:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "cannot start controlled A2.3c worker"
            ) from exc
        if process.stdout is None or process.stderr is None:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "controlled worker pipes are unavailable"
            )
        streams = [process.stdout, process.stderr]
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        deadline = time.monotonic() + float(timeout_seconds)
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                    "controlled A2.3c worker timed out; outcome is unknown"
                )
            for key, _mask in selector.select(min(remaining, 1.0)):
                buffer = stdout if key.data == "stdout" else stderr
                limit = (
                    max_stdout_bytes
                    if key.data == "stdout"
                    else max_stderr_bytes
                )
                try:
                    chunk = os.read(
                        key.fileobj.fileno(),
                        min(65_536, limit - len(buffer) + 1),
                    )
                except OSError as exc:
                    raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                        "cannot read controlled worker output"
                    ) from exc
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                        f"controlled worker {key.data} exceeded its hard byte cap; "
                        "outcome is unknown"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "controlled A2.3c worker timed out; outcome is unknown"
            )
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise LibraryPilotDependencyVectorNegativeReplayCLIError(
                "controlled A2.3c worker timed out; outcome is unknown"
            ) from exc
        return subprocess.CompletedProcess(
            command,
            returncode,
            stdout=bytes(stdout),
            stderr=bytes(stderr),
        )
    finally:
        selector.close()
        if process is not None and process.poll() is None:
            try:
                process.kill()
            except OSError:
                pass
        for stream in streams:
            try:
                stream.close()
            except OSError:
                pass
        if process is not None:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                try:
                    process.kill()
                except OSError:
                    pass
                process.wait()


def _parent(args: argparse.Namespace) -> int:
    if not args.execute and args.confirm is not None:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "--confirm is valid only with --execute"
        )
    if args.execute and args.confirm != CONFIRMATION:
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            "real execution requires the exact confirmation token"
        )
    child = [
        sys.executable,
        "-B",
        "-P",
        "-s",
        "-S",
        str(LEXICAL_CLI_PATH),
        "--_controlled-worker",
        "--hash-seed",
        args.hash_seed,
    ]
    if args.execute:
        child.extend(("--execute", "--confirm", args.confirm))
    elif args.validate_result is not None:
        child.extend(("--validate-result", str(_lexical_absolute(args.validate_result))))
    if args.output is not None:
        child.extend(("--output", str(_lexical_absolute(args.output))))
    read_descriptor, write_descriptor = os.pipe()
    capability = os.urandom(32).hex().encode("ascii")
    capability_sha256 = hashlib.sha256(capability).hexdigest()
    try:
        os.write(write_descriptor, capability)
    finally:
        os.close(write_descriptor)
    try:
        completed = _run_bounded_child(
            child,
            cwd=ROOT,
            environment=_controlled_environment(
                args.hash_seed,
                capability_fd=read_descriptor,
                capability_sha256=capability_sha256,
            ),
            pass_fds=(read_descriptor,),
            max_stdout_bytes=MAX_STDOUT_BYTES,
            max_stderr_bytes=MAX_STDERR_BYTES,
            timeout_seconds=MAX_WALL_SECONDS,
        )
    finally:
        try:
            os.close(read_descriptor)
        except OSError:
            pass
    if completed.returncode != 0:
        if completed.stderr:
            sys.stderr.buffer.write(completed.stderr)
            sys.stderr.buffer.flush()
        raise LibraryPilotDependencyVectorNegativeReplayCLIError(
            f"controlled A2.3c worker exited {completed.returncode}"
        )
    if completed.stderr:
        sys.stderr.buffer.write(completed.stderr)
        sys.stderr.buffer.flush()
    sys.stdout.buffer.write(completed.stdout)
    sys.stdout.buffer.flush()
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args._controlled_worker:
        return _worker(args)
    return _parent(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LibraryPilotDependencyVectorNegativeReplayCLIError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2) from None
