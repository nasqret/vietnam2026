#!/usr/bin/env python3
"""Build or check the bounded candidate-only Hydra A2.3b audit protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
import types
from typing import Mapping


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCHEMA_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library-pilot-dependency-vector-audit-schema-v1.json"
)
PRODUCER_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library_pilot_dependency_vector_audit.py"
)
PRODUCER_MODULE_NAME = (
    "training.peano_hydra.library_pilot_dependency_vector_audit"
)
SCHEMA_SOURCE_BYTES = 21_875
SCHEMA_SOURCE_SHA256 = (
    "c4af0d2f850ad16fa7d4a3c086ad13356020a4ccb9a15e0d612babb8db690283"
)
SCHEMA_SEMANTIC_SHA256 = (
    "6782197c9925f5552aab030a11b996c157e2d06344a2d136d8babc1ee1fdc3df"
)
IMPLEMENTATION_SOURCE_ROOT_SHA256 = (
    "4260928ce3d4243c548e3beda3d6bf823aa9f480dbf58367cab64cad8bf3cdb0"
)
EXPECTED_IMPLEMENTATION_SOURCE_COUNT = 44
MAX_SCHEMA_BYTES = 1_000_000
MAX_SOURCE_BYTES = 16_000_000
MAX_DOCUMENT_BYTES = 16_000_000
DISABLED_PYCACHE_PREFIX = "/proc/peano-hydra-a23b-disabled-pycache"
SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/l0-pilot-dependency-vector-audit-candidate-v1.json"
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_GIT_SHA1_RE = re.compile(r"[0-9a-f]{40}")
_PRODUCER_SOURCE_FILES = (
    Path(
        "training/peano_hydra/"
        "library-pilot-dependency-vector-audit-schema-v1.json"
    ),
    Path("training/peano_hydra/library_pilot_dependency_vector_audit.py"),
    Path("scripts/build_peano_hydra_library_pilot_dependency_vector_audit.py"),
    Path(
        "peano-lab/py/tests/"
        "test_peano_hydra_library_pilot_dependency_vector_audit.py"
    ),
)


class LibraryPilotDependencyVectorAuditError(ValueError):
    """The controlled CLI input, source boundary, or output is invalid."""


_loaded_producer = None


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
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot decode {label} as strict JSON"
        ) from exc
    if type(value) is not dict:
        raise LibraryPilotDependencyVectorAuditError(f"{label} must be one object")
    return value


def _lexical_absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorAuditError(
                    "output parent contains a link or non-directory component"
                )
    except LibraryPilotDependencyVectorAuditError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "cannot inspect output parent"
        ) from exc
    return current


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    _safe_parent(absolute)
    try:
        metadata = absolute.lstat()
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot inspect {label}"
        ) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise LibraryPilotDependencyVectorAuditError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot open {label}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} is not a bounded regular file"
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
        if (
            len(raw) > limit
            or (
                before.st_dev,
                before.st_ino,
                before.st_size,
                before.st_mtime_ns,
                before.st_ctime_ns,
            )
            != (
                after.st_dev,
                after.st_ino,
                after.st_size,
                after.st_mtime_ns,
                after.st_ctime_ns,
            )
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"{label} changed or exceeded its bound while read"
            )
        return raw
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            f"cannot read {label}"
        ) from exc
    finally:
        os.close(descriptor)


def _safe_relative(text: object, *, label: str) -> Path:
    if type(text) is not str:
        raise LibraryPilotDependencyVectorAuditError(f"{label} path is malformed")
    relative = Path(text)
    if (
        relative.is_absolute()
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise LibraryPilotDependencyVectorAuditError(f"{label} path is unsafe")
    return relative


def _authenticate_schema_and_sources() -> dict[str, object]:
    """Authenticate schema and all 44 implementation files before imports."""

    raw = _read_regular(SCHEMA_PATH, label="A2.3b schema", limit=MAX_SCHEMA_BYTES)
    if (
        len(raw) != SCHEMA_SOURCE_BYTES
        or hashlib.sha256(raw).hexdigest() != SCHEMA_SOURCE_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "A2.3b schema source identity drifted"
        )
    schema = _decode_object(raw, label="A2.3b schema")
    if (
        _canonical_bytes(schema) != raw
        or hashlib.sha256(_compact_bytes(schema)).hexdigest()
        != SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "A2.3b schema canonical/semantic identity drifted"
        )
    rows = schema.get("implementation_sources")
    if type(rows) is not list or len(rows) != EXPECTED_IMPLEMENTATION_SOURCE_COUNT:
        raise LibraryPilotDependencyVectorAuditError(
            "implementation source vector count drifted"
        )
    if (
        schema.get("implementation_source_root_sha256")
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
        or hashlib.sha256(_compact_bytes(rows)).hexdigest()
        != IMPLEMENTATION_SOURCE_ROOT_SHA256
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "implementation source vector root drifted"
        )
    seen: set[Path] = set()
    for row in rows:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise LibraryPilotDependencyVectorAuditError(
                "implementation source row is malformed"
            )
        relative = _safe_relative(row.get("path"), label="implementation source")
        digest = row.get("sha256")
        if (
            relative in seen
            or type(digest) is not str
            or _SHA256_RE.fullmatch(digest) is None
        ):
            raise LibraryPilotDependencyVectorAuditError(
                "implementation source identity is malformed or duplicated"
            )
        seen.add(relative)
        source = _read_regular(
            ROOT / relative,
            label=f"implementation source {relative.as_posix()!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if hashlib.sha256(source).hexdigest() != digest:
            raise LibraryPilotDependencyVectorAuditError(
                f"implementation source {relative.as_posix()!r} drifted"
            )
    return schema


def _read_producer_source_state(path: Path) -> tuple[dict[str, object], bytes]:
    """Authenticate all four producer-tranche files before producer execution."""

    raw = _read_regular(path, label="producer source state", limit=MAX_SCHEMA_BYTES)
    value = _decode_object(raw, label="producer source state")
    if _canonical_bytes(value) != raw or set(value) != {
        "commit_sha1",
        "files",
        "format",
        "git_verified",
        "root_preimage",
        "root_sha256",
        "tree_sha1",
        "v",
    }:
        raise LibraryPilotDependencyVectorAuditError(
            "producer source state is noncanonical or malformed"
        )
    if (
        value.get("format") != "peano-hydra-producer-source-state"
        or value.get("v") != 1
        or value.get("git_verified") is not False
        or type(value.get("commit_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(value["commit_sha1"]) is None
        or type(value.get("tree_sha1")) is not str
        or _GIT_SHA1_RE.fullmatch(value["tree_sha1"]) is None
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source-state identity is malformed"
        )
    files = value.get("files")
    if type(files) is not list or len(files) != len(_PRODUCER_SOURCE_FILES):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source-state file vector is malformed"
        )
    producer_raw: bytes | None = None
    for relative, row in zip(_PRODUCER_SOURCE_FILES, files, strict=True):
        if type(row) is not dict or set(row) != {"bytes", "path", "sha256"}:
            raise LibraryPilotDependencyVectorAuditError(
                "producer source-state file row is malformed"
            )
        source = _read_regular(
            ROOT / relative,
            label=f"producer source {relative.as_posix()!r}",
            limit=MAX_SOURCE_BYTES,
        )
        if (
            row.get("path") != relative.as_posix()
            or type(row.get("bytes")) is not int
            or row["bytes"] != len(source)
            or type(row.get("sha256")) is not str
            or hashlib.sha256(source).hexdigest() != row["sha256"]
        ):
            raise LibraryPilotDependencyVectorAuditError(
                f"producer source {relative.as_posix()!r} drifted"
            )
        if relative == Path(
            "training/peano_hydra/library_pilot_dependency_vector_audit.py"
        ):
            producer_raw = source
    payload = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    preimage = {
        "format": "peano-hydra-producer-source-state-root-preimage",
        "payload": payload,
        "v": 1,
    }
    if (
        value.get("root_preimage") != preimage
        or value.get("root_sha256")
        != hashlib.sha256(_compact_bytes(preimage)).hexdigest()
        or producer_raw is None
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "producer source-state root is malformed"
        )
    return value, producer_raw


def _require_controlled_worker() -> None:
    forbidden = (
        "PYTHONCASEOK",
        "PYTHONHOME",
        "PYTHONSTARTUP",
        "PYTHONINSPECT",
        "PYTHONUSERBASE",
        "PYTHONWARNINGS",
    )
    seed = os.environ.get("PYTHONHASHSEED")
    if (
        getattr(sys.flags, "safe_path", False) is not True
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.flags.optimize != 0
        or sys.dont_write_bytecode is not True
        or "PYTHONPATH" in os.environ
        or "PYTHONOPTIMIZE" in os.environ
        or any(name in os.environ for name in forbidden)
        or type(seed) is not str
        or not seed.isdecimal()
        or os.environ.get("PYTHONPYCACHEPREFIX") != DISABLED_PYCACHE_PREFIX
        or sys.pycache_prefix != DISABLED_PYCACHE_PREFIX
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "build requires controlled python -B -P -s -S, sanitized env, "
            "an explicit hash seed, and the fixed disabled pycache prefix"
        )
    try:
        if Path.cwd().resolve(strict=True) != ROOT.resolve(strict=True):
            raise LibraryPilotDependencyVectorAuditError(
                "controlled worker cwd differs from the repository snapshot"
            )
        Path(DISABLED_PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        return
    except LibraryPilotDependencyVectorAuditError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "cannot inspect controlled worker paths"
        ) from exc
    raise LibraryPilotDependencyVectorAuditError(
        "disabled pycache prefix unexpectedly exists"
    )


def _install_private_packages() -> None:
    if any(
        name == "training" or name.startswith("training.peano_hydra")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
        for name in sys.modules
    ):
        raise LibraryPilotDependencyVectorAuditError(
            "controlled worker is contaminated before private package install"
        )
    training = types.ModuleType("training")
    training.__path__ = [str(ROOT / "training")]
    training.__package__ = "training"
    hydra = types.ModuleType("training.peano_hydra")
    hydra.__path__ = [str(ROOT / "training" / "peano_hydra")]
    hydra.__package__ = "training.peano_hydra"
    training.peano_hydra = hydra
    sys.modules["training"] = training
    sys.modules["training.peano_hydra"] = hydra


def _cleanup_private_modules(previous_modules: set[str]) -> None:
    for name in tuple(sys.modules):
        if name not in previous_modules and (
            name == "training"
            or name.startswith("training.")
            or name == "peano_lab"
            or name.startswith("peano_lab.")
        ):
            sys.modules.pop(name, None)
    while str(PY_ROOT) in sys.path:
        sys.path.remove(str(PY_ROOT))


def _load_producer_after_preflight(producer_raw: bytes):
    """Execute authenticated producer bytes without the Hydra initializer."""

    if _loaded_producer is not None:
        raise LibraryPilotDependencyVectorAuditError(
            "producer may be loaded only once in a controlled worker"
        )
    previous_modules = set(sys.modules)
    module = None
    try:
        _install_private_packages()
        while str(PY_ROOT) in sys.path:
            sys.path.remove(str(PY_ROOT))
        sys.path.append(str(PY_ROOT))
        module = types.ModuleType(PRODUCER_MODULE_NAME)
        module.__file__ = str(PRODUCER_PATH)
        module.__package__ = "training.peano_hydra"
        sys.modules[PRODUCER_MODULE_NAME] = module
        code = compile(
            producer_raw,
            str(PRODUCER_PATH),
            "exec",
            dont_inherit=True,
        )
        exec(code, module.__dict__)
        forbidden = sorted(
            name
            for name in sys.modules
            if name.startswith("training.peano_hydra.")
            and name
            not in {
                PRODUCER_MODULE_NAME,
                "training.peano_hydra.library_construction_rebuild_core",
                "training.peano_hydra.library_optimizer_comparison_pilot",
                "training.peano_hydra.library_replay_pack",
            }
        )
        if forbidden:
            raise LibraryPilotDependencyVectorAuditError(
                "producer crossed its private package initializer/import boundary"
            )
        module._require_implementation(ROOT)
    except BaseException as exc:
        _cleanup_private_modules(previous_modules)
        producer_error = (
            None
            if module is None
            else getattr(
                module, "LibraryPilotDependencyVectorAuditError", None
            )
        )
        if type(producer_error) is type and isinstance(exc, producer_error):
            raise LibraryPilotDependencyVectorAuditError(str(exc)) from exc
        raise
    return module


def _controlled_load(path: Path):
    """Preflight schema, 44 implementation files, and four producer files."""

    global _loaded_producer
    previous_modules = set(sys.modules)
    module = None
    try:
        _require_controlled_worker()
        _authenticate_schema_and_sources()
        state, producer_raw = _read_producer_source_state(path)
        module = _load_producer_after_preflight(producer_raw)
        module._validate_producer_source_state(state, root=ROOT)
    except BaseException as exc:
        _cleanup_private_modules(previous_modules)
        if module is not None and isinstance(
            exc, module.LibraryPilotDependencyVectorAuditError
        ):
            raise LibraryPilotDependencyVectorAuditError(str(exc)) from exc
        raise
    _loaded_producer = module
    return module, state


def build_candidate_pilot_dependency_vector_audit(**kwargs: object):
    if _loaded_producer is None:
        raise LibraryPilotDependencyVectorAuditError(
            "producer is not authenticated and loaded"
        )
    try:
        return _loaded_producer.build_candidate_pilot_dependency_vector_audit(
            **kwargs
        )
    except _loaded_producer.LibraryPilotDependencyVectorAuditError as exc:
        raise LibraryPilotDependencyVectorAuditError(str(exc)) from exc


def canonical_document_bytes(value: Mapping[str, object]) -> bytes:
    if _loaded_producer is None:
        raise LibraryPilotDependencyVectorAuditError(
            "producer is not authenticated and loaded"
        )
    try:
        return _loaded_producer.canonical_document_bytes(value)
    except _loaded_producer.LibraryPilotDependencyVectorAuditError as exc:
        raise LibraryPilotDependencyVectorAuditError(str(exc)) from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditError(
            "cannot inspect output destination"
        ) from exc
    raise LibraryPilotDependencyVectorAuditError(
        "output destination already exists; output is create-only"
    )


def _publish(path: Path, raw: bytes) -> None:
    destination = _lexical_absolute(path)
    parent = _safe_parent(destination)
    _require_absent(destination)
    temporary_name: str | None = None
    published_identity: tuple[int, int] | None = None
    try:
        descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{destination.name}.", suffix=".tmp", dir=parent
        )
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o644)
        temporary = Path(temporary_name)
        _require_absent(destination)
        before = temporary.lstat()
        os.link(temporary, destination, follow_symlinks=False)
        published_identity = (before.st_dev, before.st_ino)
        after = destination.lstat()
        if (
            stat.S_ISLNK(after.st_mode)
            or not stat.S_ISREG(after.st_mode)
            or (after.st_dev, after.st_ino) != published_identity
        ):
            raise LibraryPilotDependencyVectorAuditError(
                "published output identity differs"
            )
        temporary.unlink()
        temporary_name = None
        parent_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except (LibraryPilotDependencyVectorAuditError, OSError) as exc:
        if published_identity is not None:
            try:
                identity = destination.lstat()
                if (
                    stat.S_ISREG(identity.st_mode)
                    and not stat.S_ISLNK(identity.st_mode)
                    and (identity.st_dev, identity.st_ino) == published_identity
                ):
                    destination.unlink()
            except OSError:
                pass
        if isinstance(exc, LibraryPilotDependencyVectorAuditError):
            raise
        raise LibraryPilotDependencyVectorAuditError(
            "cannot atomically publish output"
        ) from exc
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except (FileNotFoundError, OSError):
                pass


def _read_exact(path: Path, expected: bytes) -> None:
    actual = _read_regular(
        path,
        label="pilot dependency-vector audit for --check",
        limit=MAX_DOCUMENT_BYTES,
    )
    if actual != expected:
        raise LibraryPilotDependencyVectorAuditError(
            "pilot dependency-vector audit differs from deterministic build"
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No proof build or retained write occurs by default. Suggested "
            f"candidate path: {SUGGESTED_OUTPUT}"
        ),
    )
    parser.add_argument(
        "--producer-source-state",
        type=Path,
        help="canonical explicit four-file source state from an external wrapper",
    )
    parser.add_argument(
        "--output", type=Path, help="create one new canonical candidate result"
    )
    parser.add_argument(
        "--check", action="store_true", help="compare an existing --output"
    )
    args = parser.parse_args()
    if args.check and args.output is None:
        parser.error("--check requires --output")
    if args.producer_source_state is None:
        if args.output is not None or args.check:
            parser.error("a build/check requires --producer-source-state")
        print(
            "A2.3b candidate protocol ready; no build or retained write requested",
            flush=True,
        )
        return

    module, state = _controlled_load(args.producer_source_state)
    try:
        document = module.build_candidate_pilot_dependency_vector_audit(
            repository_root=ROOT,
            producer_source_state=state,
        )
        raw = module.canonical_document_bytes(document)
    except module.LibraryPilotDependencyVectorAuditError as exc:
        raise LibraryPilotDependencyVectorAuditError(str(exc)) from exc
    if args.check:
        _read_exact(args.output, raw)
        action = "checked"
    elif args.output is not None:
        _publish(args.output, raw)
        action = "published"
    else:
        sys.stdout.buffer.write(raw)
        sys.stdout.buffer.flush()
        return
    print(
        f"A2.3b candidate {action}: {document['theorem_count']} roots, "
        f"{document['aggregate']['single_omission_terminal_count']} terminal "
        f"attempts, root {document['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryPilotDependencyVectorAuditError as exc:
        raise SystemExit(str(exc)) from None
