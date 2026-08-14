#!/usr/bin/env python3.12
"""Controlled independent verifier for the one-root A2.3d Cut-liveness pilot.

The default operation describes the verifier and writes nothing.  ``--verify``
runs in a fresh bounded Python worker and emits a narrow canonical receipt to
stdout.  A file can be created only at an explicit absent path with the exact
confirmation token.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
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
import time
import warnings


LEXICAL_CLI_PATH = Path(os.path.abspath(__file__))
ROOT = LEXICAL_CLI_PATH.parents[1]
EXPECTED_CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
)
SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-dependency-vector-cut-liveness-schema-v1.json"
)
VERIFIER_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_cut_liveness_verifier.py"
)
VERIFIER_MODULE_NAME = "_peano_hydra_a23d_cut_liveness_independent_verifier"

SCHEMA_SOURCE_BYTES = 12_566
SCHEMA_SOURCE_SHA256 = (
    "388190b4235b9892b38193714b0331a35b6c533c0605072c5d0663ad9cd9c0aa"
)
SCHEMA_SEMANTIC_SHA256 = (
    "9e8887072cc6051cf9cb9177609ab31aed35ca305a42c7d9c22d4ac339b6f5c5"
)
VERIFIER_SOURCE_BYTES = 81_450
VERIFIER_SOURCE_SHA256 = (
    "63ab7b96cee903f3ea2af4bda64d52409b656ea700a725332c0c569c9f3b3108"
)

MAX_SCHEMA_BYTES = 262_144
MAX_SOURCE_BYTES = 1_048_576
MAX_DOCUMENT_BYTES = 1_048_576
MAX_STDOUT_BYTES = 1_048_576
MAX_STDERR_BYTES = 65_536
MAX_WALL_SECONDS = 30
MAX_JSON_DEPTH = 64
MAX_JSON_ITEMS = 100_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
PYCACHE_PREFIX = "/proc/peano-hydra-a23d-verifier-disabled-pycache"
PYTHON_IMPLEMENTATION = "cpython"
PYTHON_VERSION = (3, 12)
CONFIRMATION = "PEANO-HYDRA-A23D-CUT-LIVENESS-VERIFICATION-CREATE"
SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/"
    "l0-pilot-dependency-vector-cut-liveness-independent-verification-v1.json"
)

_WORKER_ENVIRONMENT = "PEANO_HYDRA_A23D_VERIFIER_CONTROLLED_WORKER"
_WORKER_CAPABILITY_FD = "PEANO_HYDRA_A23D_VERIFIER_CAPABILITY_FD"
_WORKER_CAPABILITY_SHA256 = "PEANO_HYDRA_A23D_VERIFIER_CAPABILITY_SHA256"
_WORKER_ALLOWED_ENVIRONMENT = {
    "LC_ALL",
    "PYTHONHASHSEED",
    "PYTHONPYCACHEPREFIX",
    _WORKER_ENVIRONMENT,
    _WORKER_CAPABILITY_FD,
    _WORKER_CAPABILITY_SHA256,
    "__CF_USER_TEXT_ENCODING",
}
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
_REQUIRED_STDLIB_MODULES = (
    "argparse",
    "base64",
    "copy",
    "hashlib",
    "importlib",
    "json",
    "os",
    "pathlib",
    "re",
    "selectors",
    "stat",
    "subprocess",
    "sys",
    "time",
    "typing",
    "warnings",
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")


class DependencyVectorCutLivenessVerifierCLIError(ValueError):
    """The controlled verifier CLI boundary or execution is invalid."""


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_number(value: str) -> object:
    raise ValueError(f"unsupported JSON number {value!r}")


def _parse_integer(value: str) -> int:
    parsed = int(value)
    if abs(parsed) > MAX_SAFE_JSON_INTEGER:
        raise ValueError("JSON integer exceeds the exact safe range")
    return parsed


def _validate_json(value: object) -> None:
    pending: list[tuple[object, int]] = [(value, 1)]
    items = 0
    while pending:
        item, depth = pending.pop()
        items += 1
        if items > MAX_JSON_ITEMS or depth > MAX_JSON_DEPTH:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "JSON value exceeds the registered bound"
            )
        if item is None or type(item) in (bool, str):
            continue
        if type(item) is int:
            if abs(item) > MAX_SAFE_JSON_INTEGER:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    "JSON integer exceeds the exact safe range"
                )
            continue
        if type(item) is list:
            pending.extend((child, depth + 1) for child in item)
            continue
        if type(item) is dict and all(type(key) is str for key in item):
            pending.extend((child, depth + 1) for child in item.values())
            continue
        raise DependencyVectorCutLivenessVerifierCLIError(
            "JSON value contains an unsupported type"
        )


def _decode_object(raw: bytes, *, label: str) -> dict[str, object]:
    if not raw or len(raw) > MAX_DOCUMENT_BYTES:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"{label} is empty or exceeds its byte limit"
        )
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_int=_parse_integer,
            parse_float=_reject_number,
            parse_constant=_reject_number,
        )
    except (UnicodeDecodeError, ValueError, json.JSONDecodeError) as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"{label} must be one JSON object"
        )
    _validate_json(value)
    return value


def _compact_bytes(value: object) -> bytes:
    _validate_json(value)
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _canonical_bytes(value: object) -> bytes:
    _validate_json(value)
    raw = (
        json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            indent=2,
        )
        + "\n"
    ).encode("utf-8")
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "canonical output exceeds its byte limit"
        )
    return raw


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
                raise DependencyVectorCutLivenessVerifierCLIError(
                    f"{label} contains a symlink or non-directory"
                )
    except DependencyVectorCutLivenessVerifierCLIError:
        raise
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
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
        inspected = absolute.lstat()
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _stat_identity(before) != _stat_identity(inspected)
        ):
            raise DependencyVectorCutLivenessVerifierCLIError(
                f"{label} is not the inspected bounded regular file"
            )
        chunks: list[bytes] = []
        remaining = limit + 1
        while remaining:
            chunk = os.read(descriptor, min(65_536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        path_after = absolute.lstat()
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)
    if (
        len(raw) > limit
        or stat.S_ISLNK(path_after.st_mode)
        or not stat.S_ISREG(path_after.st_mode)
        or _stat_identity(inspected) != _stat_identity(before)
        or _stat_identity(before) != _stat_identity(after)
        or _stat_identity(after) != _stat_identity(path_after)
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"{label} changed or exceeded its bound while read"
        )
    return raw, _stat_identity(after)


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    raw, _identity = _read_regular_with_identity(path, label=label, limit=limit)
    return raw


def _require_exact_cli_source() -> None:
    if LEXICAL_CLI_PATH != EXPECTED_CLI_PATH:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier CLI lexical path drifted"
        )
    _require_directory_chain(
        LEXICAL_CLI_PATH.parent, label="controlled verifier CLI ancestors"
    )
    try:
        metadata = LEXICAL_CLI_PATH.lstat()
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot inspect controlled verifier CLI source"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier CLI must be a non-symlink regular file"
        )


def _require_runtime_version(*, role: str) -> None:
    if (
        sys.implementation.name != PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:2]) != PYTHON_VERSION
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            f"controlled verifier {role} requires CPython 3.12 exactly at "
            f"major/minor; observed {sys.implementation.name} "
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )


def _require_controlled_worker() -> None:
    _require_runtime_version(role="worker")
    if (
        os.environ.get(_WORKER_ENVIRONMENT) != "1"
        or set(os.environ) != _WORKER_ALLOWED_ENVIRONMENT
        or os.environ.get("LC_ALL") != "C"
        or type(os.environ.get("__CF_USER_TEXT_ENCODING")) is not str
        or os.environ.get("PYTHONHASHSEED") != "0"
        or any(name in os.environ for name in _FORBIDDEN_ENVIRONMENT)
        or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
        or sys.pycache_prefix != PYCACHE_PREFIX
        or getattr(sys.flags, "safe_path", False) is not True
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.flags.optimize != 0
        or sys.dont_write_bytecode is not True
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "verifier worker requires exact fresh -B -P -s -S execution"
        )
    try:
        cwd = Path.cwd().resolve(strict=True)
        expected = ROOT.resolve(strict=True)
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot resolve controlled verifier worker cwd"
        ) from exc
    if cwd != expected:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier worker cwd drifted"
        )
    try:
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot inspect disabled pycache prefix"
        ) from exc
    else:
        raise DependencyVectorCutLivenessVerifierCLIError(
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
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier capability is missing"
        )
    descriptor = int(descriptor_text)
    if descriptor < 3:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier capability descriptor is unsafe"
        )
    try:
        token = os.read(descriptor, 65)
        trailing = os.read(descriptor, 1)
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot consume controlled verifier capability"
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
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier capability did not authenticate"
        )


def _preflight_stdlib_and_import_state() -> dict[str, object]:
    wanted_meta_path = (
        importlib.machinery.BuiltinImporter,
        importlib.machinery.FrozenImporter,
        importlib.machinery.PathFinder,
    )
    if tuple(sys.meta_path) != wanted_meta_path:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier worker has a nonstandard meta path"
        )
    if any(
        name == "training"
        or name.startswith("training.")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
        or name.startswith("_peano_hydra_a23d_verifier_kernel_runtime")
        for name in sys.modules
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "controlled verifier worker is contaminated before direct load"
        )
    repository = ROOT.resolve(strict=True)
    for entry in sys.path:
        if not entry:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "controlled verifier import path contains the current directory"
            )
        try:
            resolved = Path(entry).resolve(strict=True)
        except OSError:
            continue
        if resolved == repository or repository in resolved.parents:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "controlled verifier import path enters the repository"
            )
    modules: dict[str, object] = {}
    for name in _REQUIRED_STDLIB_MODULES:
        module = importlib.import_module(name)
        source = getattr(module, "__file__", None)
        if type(source) is str:
            resolved = Path(source).resolve(strict=True)
            if resolved == repository or repository in resolved.parents:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    f"standard-library module {name!r} was shadowed"
                )
        modules[name] = module
    return modules


def _authenticate_schema_and_verifier() -> tuple[
    dict[str, object], bytes, tuple[int, int, int, int, int]
]:
    schema_raw = _read_regular(
        SCHEMA_PATH, label="cut-liveness schema", limit=MAX_SCHEMA_BYTES
    )
    if (
        len(schema_raw) != SCHEMA_SOURCE_BYTES
        or hashlib.sha256(schema_raw).hexdigest() != SCHEMA_SOURCE_SHA256
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cut-liveness schema source identity drifted"
        )
    schema = _decode_object(schema_raw, label="cut-liveness schema")
    if (
        hashlib.sha256(_compact_bytes(schema)).hexdigest()
        != SCHEMA_SEMANTIC_SHA256
        or schema.get("format")
        != "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema"
        or schema.get("id")
        != "peano-hydra-library-pilot-dependency-vector-cut-liveness-schema-v1"
        or schema.get("v") != 1
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cut-liveness schema semantic identity drifted"
        )
    verifier_raw, verifier_identity = _read_regular_with_identity(
        VERIFIER_PATH,
        label="independent cut-liveness verifier",
        limit=MAX_SOURCE_BYTES,
    )
    if (
        len(verifier_raw) != VERIFIER_SOURCE_BYTES
        or hashlib.sha256(verifier_raw).hexdigest() != VERIFIER_SOURCE_SHA256
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "independent verifier source identity drifted"
        )
    schema_identity = {
        "artifact_bytes": len(schema_raw),
        "artifact_sha256": hashlib.sha256(schema_raw).hexdigest(),
        "format": schema["format"],
        "id": schema["id"],
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": 1,
    }
    return schema_identity, verifier_raw, verifier_identity


def _load_verifier() -> tuple[object, dict[str, object]]:
    stdlib = _preflight_stdlib_and_import_state()
    _require_exact_cli_source()
    schema_identity, verifier_raw, verifier_identity = (
        _authenticate_schema_and_verifier()
    )
    if VERIFIER_MODULE_NAME in sys.modules:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "private verifier module name is already loaded"
        )
    specification = importlib.util.spec_from_file_location(
        VERIFIER_MODULE_NAME, VERIFIER_PATH
    )
    if (
        specification is None
        or type(specification.loader) is not importlib.machinery.SourceFileLoader
        or specification.origin != str(VERIFIER_PATH)
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "independent verifier source specification drifted"
        )
    module = importlib.util.module_from_spec(specification)
    sys.modules[VERIFIER_MODULE_NAME] = module
    try:
        warnings.filterwarnings("ignore", category=SyntaxWarning)
        code = specification.loader.source_to_code(
            verifier_raw, str(VERIFIER_PATH)
        )
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise
    try:
        current = VERIFIER_PATH.lstat()
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot re-attest independent verifier path identity"
        ) from exc
    if (
        stat.S_ISLNK(current.st_mode)
        or not stat.S_ISREG(current.st_mode)
        or _stat_identity(current) != verifier_identity
        or sys.modules.get(VERIFIER_MODULE_NAME) is not module
        or Path(str(getattr(module, "__file__", ""))).resolve(strict=True)
        != VERIFIER_PATH.resolve(strict=True)
        or any(sys.modules.get(name) is not value for name, value in stdlib.items())
        or tuple(sys.meta_path)
        != (
            importlib.machinery.BuiltinImporter,
            importlib.machinery.FrozenImporter,
            importlib.machinery.PathFinder,
        )
    ):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "independent verifier load closure drifted"
        )
    required = (
        "canonical_verification_bytes",
        "validate_dependency_vector_cut_liveness_verification",
        "verify_dependency_vector_cut_liveness",
    )
    if not all(callable(getattr(module, name, None)) for name in required):
        raise DependencyVectorCutLivenessVerifierCLIError(
            "independent verifier public API is incomplete"
        )
    identity = {
        "artifact_bytes": len(verifier_raw),
        "artifact_sha256": hashlib.sha256(verifier_raw).hexdigest(),
        "load_mode": "authenticated-source-bytes-source_to_code-exec",
        "module_name": VERIFIER_MODULE_NAME,
        "path": VERIFIER_PATH.relative_to(ROOT).as_posix(),
        "pycache_prefix": PYCACHE_PREFIX,
    }
    return module, {"schema": schema_identity, "verifier": identity}


def _attest_loaded_closure(module: object) -> None:
    if sys.modules.get(VERIFIER_MODULE_NAME) is not module:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "private verifier module was replaced"
        )
    forbidden = [
        name
        for name in sys.modules
        if name == "training"
        or name.startswith("training.")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
        or name.startswith("_peano_hydra_a23d_verifier_kernel_runtime")
    ]
    if forbidden:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "independent verifier leaked a forbidden project module"
        )
    repository = ROOT.resolve(strict=True)
    expected = {
        "__main__": LEXICAL_CLI_PATH.resolve(strict=True),
        VERIFIER_MODULE_NAME: VERIFIER_PATH.resolve(strict=True),
    }
    for name, loaded in tuple(sys.modules.items()):
        source = getattr(loaded, "__file__", None)
        if type(source) is not str:
            continue
        resolved = Path(source).resolve(strict=True)
        if resolved == repository or repository in resolved.parents:
            if expected.get(name) != resolved:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    f"unexpected repository module {name!r} was loaded"
                )


def _load_candidate(path: Path) -> dict[str, object]:
    raw = _read_regular(
        path, label="cut-liveness candidate", limit=MAX_DOCUMENT_BYTES
    )
    value = _decode_object(raw, label="cut-liveness candidate")
    if _canonical_bytes(value) != raw:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cut-liveness candidate is not canonical JSON"
        )
    return value


def _description(identity: dict[str, object]) -> dict[str, object]:
    return {
        "default_write": False,
        "expected_candidate": {
            "artifact_bytes": 11_958,
            "artifact_sha256": "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22",
            "derived_direct_dependencies": ["mul_add", "add_comm"],
            "proof_term_sha256": "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4",
        },
        "format": "peano-hydra-library-pilot-dependency-vector-cut-liveness-independent-verifier-source-protocol-v1",
        "independent_verification_executed": False,
        "producer_imported": False,
        "runtime": {
            "bounded_child": True,
            "hash_randomization": 0,
            "max_stderr_bytes": MAX_STDERR_BYTES,
            "max_stdout_bytes": MAX_STDOUT_BYTES,
            "max_wall_seconds": MAX_WALL_SECONDS,
            "pycache_prefix": PYCACHE_PREFIX,
            "python_flags": ["-B", "-P", "-s", "-S"],
            "python_hash_seed": "0",
            "python_implementation": PYTHON_IMPLEMENTATION,
            "python_major": PYTHON_VERSION[0],
            "python_minor": PYTHON_VERSION[1],
            "python_optimize": 0,
            "verifier_load_mode": (
                "authenticated-source-bytes-SourceFileLoader.source_to_code-exec"
            ),
        },
        "schema": identity["schema"],
        "status": "described-no-verification-no-write",
        "suggested_output": SUGGESTED_OUTPUT.as_posix(),
        "v": 1,
        "verifier_source": identity["verifier"],
    }


def _worker(arguments: argparse.Namespace) -> int:
    _require_controlled_worker()
    _consume_worker_capability()
    module, identity = _load_verifier()
    if arguments.verify is None:
        raw = _canonical_bytes(_description(identity))
    else:
        candidate = _load_candidate(arguments.verify)
        receipt = module.verify_dependency_vector_cut_liveness(
            candidate, arguments.repository_root
        )
        raw = module.canonical_verification_bytes(receipt)
        if len(raw) > MAX_STDOUT_BYTES:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "verification receipt exceeds the stdout bound"
            )
    _attest_loaded_closure(module)
    sys.stdout.buffer.write(raw)
    return 0


def _safe_output_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label="output parent")
    try:
        absolute.lstat()
    except FileNotFoundError:
        return absolute
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot inspect output destination"
        ) from exc
    raise DependencyVectorCutLivenessVerifierCLIError(
        "output destination already exists"
    )


def _publish_create_only(path: Path, raw: bytes) -> None:
    absolute = _safe_output_parent(path)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    created = False
    created_identity: tuple[int, int, int, int, int] | None = None
    try:
        descriptor = os.open(absolute, flags, 0o644)
        created = True
        written = 0
        while written < len(raw):
            count = os.write(descriptor, raw[written:])
            if count <= 0:
                raise OSError("short output write")
            written += count
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size != len(raw):
            raise DependencyVectorCutLivenessVerifierCLIError(
                "created output is not the exact regular file"
            )
        created_identity = _stat_identity(metadata)
    except FileExistsError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "output destination already exists"
        ) from exc
    except OSError as exc:
        raise DependencyVectorCutLivenessVerifierCLIError(
            "cannot create exact output"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        retained, retained_identity = _read_regular_with_identity(
            absolute, label="created output", limit=MAX_DOCUMENT_BYTES
        )
        if retained != raw or retained_identity != created_identity:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "created output bytes or inode identity differ from verified stdout"
            )
    except BaseException:
        if created and created_identity is not None:
            try:
                current = absolute.lstat()
                if (
                    not stat.S_ISLNK(current.st_mode)
                    and stat.S_ISREG(current.st_mode)
                    and _stat_identity(current) == created_identity
                ):
                    absolute.unlink()
            except OSError:
                pass
        raise


def _terminate(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=1)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=1)


def _run_bounded_worker(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    read_descriptor, write_descriptor = os.pipe()
    token = os.urandom(64)
    try:
        written = 0
        while written < len(token):
            count = os.write(write_descriptor, token[written:])
            if count <= 0:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    "cannot write the controlled worker capability"
                )
            written += count
    finally:
        os.close(write_descriptor)
    environment = {
        "LC_ALL": "C",
        "PYTHONHASHSEED": "0",
        "PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,
        _WORKER_ENVIRONMENT: "1",
        _WORKER_CAPABILITY_FD: str(read_descriptor),
        _WORKER_CAPABILITY_SHA256: hashlib.sha256(token).hexdigest(),
        "__CF_USER_TEXT_ENCODING": "0x0:0x0",
    }
    command = [
        str(Path(sys.executable).resolve(strict=True)),
        "-B",
        "-P",
        "-s",
        "-S",
        str(LEXICAL_CLI_PATH),
        "--_controlled-worker",
        *arguments,
    ]
    process: subprocess.Popen[bytes] | None = None
    selector = selectors.DefaultSelector()
    stdout = bytearray()
    stderr = bytearray()
    deadline = time.monotonic() + MAX_WALL_SECONDS
    try:
        process = subprocess.Popen(
            command,
            cwd=ROOT,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
            pass_fds=(read_descriptor,),
        )
        os.close(read_descriptor)
        read_descriptor = -1
        assert process.stdout is not None and process.stderr is not None
        selector.register(process.stdout, selectors.EVENT_READ, (stdout, MAX_STDOUT_BYTES))
        selector.register(process.stderr, selectors.EVENT_READ, (stderr, MAX_STDERR_BYTES))
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    "controlled verifier worker exceeded its wall-time bound"
                )
            events = selector.select(min(remaining, 0.25))
            if not events and process.poll() is not None:
                events = [(key, selectors.EVENT_READ) for key in selector.get_map().values()]
            for key, _mask in events:
                chunk = os.read(key.fileobj.fileno(), 65_536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                target, limit = key.data
                target.extend(chunk)
                if len(target) > limit:
                    raise DependencyVectorCutLivenessVerifierCLIError(
                        "controlled verifier worker exceeded an output bound"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "controlled verifier worker exceeded its wall-time bound"
            )
        returncode = process.wait(timeout=remaining)
        return subprocess.CompletedProcess(command, returncode, bytes(stdout), bytes(stderr))
    except BaseException:
        if process is not None:
            _terminate(process)
        raise
    finally:
        selector.close()
        if read_descriptor >= 0:
            os.close(read_descriptor)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled independent one-root Cut-liveness verifier."
    )
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--verify",
        type=Path,
        metavar="CANDIDATE",
        help="independently verify one canonical candidate document",
    )
    operation.add_argument(
        "--describe",
        action="store_true",
        help="describe the verifier source protocol (the default)",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="explicit root containing the pinned retained evidence",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="absent create-only receipt path; stdout is the default",
    )
    parser.add_argument(
        "--confirm-create",
        metavar="TOKEN",
        help="exact capability token required with --output",
    )
    parser.add_argument(
        "--_controlled-worker", action="store_true", help=argparse.SUPPRESS
    )
    return parser


def _worker_arguments(arguments: argparse.Namespace) -> list[str]:
    result: list[str] = []
    if arguments.verify is not None:
        result.extend(("--verify", str(_lexical_absolute(arguments.verify))))
    elif arguments.describe:
        result.append("--describe")
    if arguments.repository_root is not None:
        result.extend(
            ("--repository-root", str(_lexical_absolute(arguments.repository_root)))
        )
    return result


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments._controlled_worker:
            if arguments.output is not None or arguments.confirm_create is not None:
                raise DependencyVectorCutLivenessVerifierCLIError(
                    "controlled worker cannot publish a file"
                )
            return _worker(arguments)
        _require_runtime_version(role="parent")
        if arguments.output is not None and arguments.verify is None:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "--output requires --verify"
            )
        if arguments.output is not None and arguments.confirm_create != CONFIRMATION:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "--output requires the exact --confirm-create token"
            )
        if arguments.output is None and arguments.confirm_create is not None:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "--confirm-create is valid only with --output"
            )
        completed = _run_bounded_worker(_worker_arguments(arguments))
        if completed.returncode != 0:
            message = completed.stderr.decode("utf-8", errors="replace").strip()
            raise DependencyVectorCutLivenessVerifierCLIError(
                message or "controlled verifier worker failed"
            )
        if completed.stderr:
            raise DependencyVectorCutLivenessVerifierCLIError(
                "controlled verifier worker emitted unexpected stderr"
            )
        if arguments.output is None:
            sys.stdout.buffer.write(completed.stdout)
        else:
            _publish_create_only(arguments.output, completed.stdout)
        return 0
    except Exception as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        message = " ".join(str(exc).split()) or type(exc).__name__
        print(f"cut-liveness verifier CLI error: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
