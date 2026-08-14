#!/usr/bin/env python3.12
"""Describe, build, or validate the one-root Hydra Cut-liveness candidate.

The default operation authenticates the frozen sources and emits only a small
protocol receipt.  ``--build`` performs the proof-producing transformation and
emits canonical JSON to stdout.  A file is written only when an explicit,
absent create-only path and the exact confirmation token are both supplied.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import time
from types import ModuleType


LEXICAL_CLI_PATH = Path(os.path.abspath(__file__))
ROOT = LEXICAL_CLI_PATH.parents[1]
EXPECTED_CLI_PATH = (
    ROOT
    / "scripts/build_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
)
PY_ROOT = ROOT / "peano-lab/py"
SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-dependency-vector-cut-liveness-schema-v1.json"
)
PRODUCER_PATH = (
    ROOT
    / "training/peano_hydra/library_pilot_dependency_vector_cut_liveness.py"
)
PRODUCER_MODULE_NAME = "_peano_hydra_a23d_cut_liveness_producer"

SCHEMA_SOURCE_BYTES = 12_566
SCHEMA_SOURCE_SHA256 = (
    "388190b4235b9892b38193714b0331a35b6c533c0605072c5d0663ad9cd9c0aa"
)
PRODUCER_SOURCE_BYTES = 55_485
PRODUCER_SOURCE_SHA256 = (
    "9d657c7698faf89bc83d43aff9116493492eed4d854a8ef21968d10b91574abe"
)
MAX_SCHEMA_BYTES = 262_144
MAX_SOURCE_BYTES = 1_048_576
MAX_DOCUMENT_BYTES = 1_048_576
MAX_STDOUT_BYTES = 1_048_576
MAX_STDERR_BYTES = 65_536
MAX_WALL_SECONDS = 30.0
PYTHON_HASH_SEED = "0"
PYTHON_IMPLEMENTATION = "cpython"
PYTHON_VERSION = (3, 12)
PYTHON_RUNTIME_TAG = "cpython-3.12"
PYCACHE_PREFIX = "/proc/peano-hydra-a23d-cut-liveness-disabled-pycache"
_WORKER_ENVIRONMENT = "PEANO_HYDRA_A23D_CUT_LIVENESS_WORKER"
_WORKER_PARENT_RUNTIME = "PEANO_HYDRA_A23D_CUT_LIVENESS_PARENT_RUNTIME"
_WORKER_CAPABILITY_FD = "PEANO_HYDRA_A23D_CUT_LIVENESS_CAPABILITY_FD"
_WORKER_CAPABILITY_SHA256 = (
    "PEANO_HYDRA_A23D_CUT_LIVENESS_CAPABILITY_SHA256"
)
CONFIRMATION = "PEANO-HYDRA-A23D-CUT-LIVENESS-CREATE"
SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/"
    "l0-pilot-dependency-vector-cut-liveness-candidate-v1.json"
)

_CAPTURED_SOURCE_ROWS = (
    (
        "peano_lab",
        Path("peano-lab/py/peano_lab/__init__.py"),
        257,
        "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a",
        True,
    ),
    (
        "peano_lab.kernel",
        Path("peano-lab/py/peano_lab/kernel/__init__.py"),
        263,
        "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
        True,
    ),
    (
        "peano_lab.kernel.terms",
        Path("peano-lab/py/peano_lab/kernel/terms.py"),
        9_133,
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
        False,
    ),
    (
        "peano_lab.kernel.formulas",
        Path("peano-lab/py/peano_lab/kernel/formulas.py"),
        10_950,
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
        False,
    ),
    (
        "peano_lab.kernel.proofs",
        Path("peano-lab/py/peano_lab/kernel/proofs.py"),
        5_015,
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
        False,
    ),
    (
        "peano_lab.kernel.subst",
        Path("peano-lab/py/peano_lab/kernel/subst.py"),
        5_165,
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
        False,
    ),
    (
        "peano_lab.kernel.checker",
        Path("peano-lab/py/peano_lab/kernel/checker.py"),
        10_738,
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
        False,
    ),
    (
        "peano_lab.kernel.artifact_codec",
        Path("peano-lab/py/peano_lab/kernel/artifact_codec.py"),
        27_892,
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
        False,
    ),
)


class CutLivenessCLIError(ValueError):
    """The controlled CLI source, arguments, input, or output is invalid."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _canonical_bytes(value: object) -> bytes:
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
        raise CutLivenessCLIError("CLI output exceeds its byte limit")
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
                raise CutLivenessCLIError(
                    f"{label} contains a symlink or non-directory"
                )
    except CutLivenessCLIError:
        raise
    except OSError as exc:
        raise CutLivenessCLIError(f"cannot inspect {label}") from exc


def _identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label=f"{label} ancestors")
    try:
        inspected = absolute.lstat()
    except OSError as exc:
        raise CutLivenessCLIError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise CutLivenessCLIError(
            f"{label} must be a non-symlink regular file"
        )
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise CutLivenessCLIError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _identity(before) != _identity(inspected)
        ):
            raise CutLivenessCLIError(
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
        if (
            len(raw) > limit
            or _identity(before) != _identity(after)
            or stat.S_ISLNK(path_after.st_mode)
            or not stat.S_ISREG(path_after.st_mode)
            or _identity(after) != _identity(path_after)
        ):
            raise CutLivenessCLIError(
                f"{label} changed or exceeded its bound while read"
            )
        return raw
    except OSError as exc:
        raise CutLivenessCLIError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def _require_cli_location() -> None:
    if _lexical_absolute(LEXICAL_CLI_PATH) != _lexical_absolute(EXPECTED_CLI_PATH):
        raise CutLivenessCLIError("controlled CLI lexical path is unexpected")
    _require_directory_chain(EXPECTED_CLI_PATH.parent, label="CLI ancestors")
    try:
        cli_metadata = EXPECTED_CLI_PATH.lstat()
        lexical_physical = LEXICAL_CLI_PATH.resolve(strict=True)
        expected_physical = EXPECTED_CLI_PATH.resolve(strict=True)
    except OSError as exc:
        raise CutLivenessCLIError("cannot inspect controlled CLI location") from exc
    if (
        stat.S_ISLNK(cli_metadata.st_mode)
        or not stat.S_ISREG(cli_metadata.st_mode)
        or lexical_physical != expected_physical
    ):
        raise CutLivenessCLIError(
            "controlled CLI must be the exact physical non-link regular file"
        )


def _require_runtime_version(*, role: str) -> None:
    if (
        sys.implementation.name != PYTHON_IMPLEMENTATION
        or tuple(sys.version_info[:2]) != PYTHON_VERSION
    ):
        raise CutLivenessCLIError(
            f"controlled {role} requires CPython 3.12 exactly at major/minor; "
            f"observed {sys.implementation.name} "
            f"{sys.version_info.major}.{sys.version_info.minor}"
        )


def _require_controlled_worker() -> None:
    _require_runtime_version(role="worker")
    _require_cli_location()
    python_environment = {
        name: value
        for name, value in os.environ.items()
        if name.startswith("PYTHON")
    }
    expected_python_environment = {
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": PYTHON_HASH_SEED,
        "PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,
    }
    expected_meta_path = (
        importlib.machinery.BuiltinImporter,
        importlib.machinery.FrozenImporter,
        importlib.machinery.PathFinder,
    )
    if (
        os.environ.get(_WORKER_ENVIRONMENT) != "1"
        or os.environ.get(_WORKER_PARENT_RUNTIME) != PYTHON_RUNTIME_TAG
        or getattr(sys.flags, "safe_path", 0) != 1
        or sys.flags.no_site != 1
        or sys.flags.no_user_site != 1
        or sys.flags.optimize != 0
        or sys.flags.hash_randomization != 0
        or sys.dont_write_bytecode is not True
        or python_environment != expected_python_environment
        or sys.pycache_prefix != PYCACHE_PREFIX
        or tuple(sys.meta_path) != expected_meta_path
        or any(
            name == "peano_lab"
            or name.startswith("peano_lab.")
            or name == "training"
            or name.startswith("training.")
            for name in sys.modules
        )
    ):
        raise CutLivenessCLIError(
            "worker requires fresh controlled Python -B -P -s -S, optimize 0, "
            "hash randomization disabled by seed 0, a sanitized environment, "
            "the fixed disabled pycache prefix, and a clean import state"
        )
    try:
        cwd = Path.cwd()
        if (
            _lexical_absolute(cwd) != _lexical_absolute(ROOT)
            or cwd.resolve(strict=True) != ROOT.resolve(strict=True)
        ):
            raise CutLivenessCLIError(
                "controlled worker cwd differs from the repository snapshot"
            )
        _require_directory_chain(ROOT, label="repository root")
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except CutLivenessCLIError:
        raise
    except OSError as exc:
        raise CutLivenessCLIError("cannot inspect controlled worker paths") from exc
    else:
        raise CutLivenessCLIError(
            "disabled pycache prefix unexpectedly exists"
        )
    root_physical = ROOT.resolve(strict=True)
    for entry in sys.path:
        if type(entry) is not str or not entry:
            raise CutLivenessCLIError("controlled worker import path is unsafe")
        try:
            physical = Path(entry).resolve(strict=False)
        except OSError as exc:
            raise CutLivenessCLIError(
                "cannot inspect controlled worker import path"
            ) from exc
        if physical == root_physical or root_physical in physical.parents:
            raise CutLivenessCLIError(
                "repository path leaked into controlled worker import search"
            )


def _consume_worker_capability() -> None:
    descriptor_text = os.environ.pop(_WORKER_CAPABILITY_FD, None)
    expected = os.environ.pop(_WORKER_CAPABILITY_SHA256, None)
    if (
        type(descriptor_text) is not str
        or not descriptor_text.isdecimal()
        or type(expected) is not str
        or len(expected) != 64
    ):
        raise CutLivenessCLIError(
            "controlled worker capability is absent or malformed"
        )
    descriptor = int(descriptor_text)
    if descriptor < 3:
        raise CutLivenessCLIError(
            "controlled worker capability descriptor is unsafe"
        )
    try:
        token = os.read(descriptor, 65)
        trailing = os.read(descriptor, 1)
    except OSError as exc:
        raise CutLivenessCLIError(
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
        or _sha256(token) != expected
    ):
        raise CutLivenessCLIError(
            "controlled worker capability did not authenticate"
        )


def _authenticate_sources() -> tuple[
    bytes,
    bytes,
    dict[str, tuple[Path, bytes, bool]],
]:
    _require_cli_location()
    schema_raw = _read_regular(
        SCHEMA_PATH, label="cut-liveness schema", limit=MAX_SCHEMA_BYTES
    )
    producer_raw = _read_regular(
        PRODUCER_PATH, label="cut-liveness producer", limit=MAX_SOURCE_BYTES
    )
    if (
        len(schema_raw) != SCHEMA_SOURCE_BYTES
        or _sha256(schema_raw) != SCHEMA_SOURCE_SHA256
    ):
        raise CutLivenessCLIError("cut-liveness schema source identity drifted")
    if (
        len(producer_raw) != PRODUCER_SOURCE_BYTES
        or _sha256(producer_raw) != PRODUCER_SOURCE_SHA256
    ):
        raise CutLivenessCLIError("cut-liveness producer source identity drifted")
    captured: dict[str, tuple[Path, bytes, bool]] = {}
    for name, relative, expected_bytes, expected_sha, is_package in (
        _CAPTURED_SOURCE_ROWS
    ):
        path = ROOT / relative
        raw = _read_regular(
            path,
            label=f"implementation source {relative.as_posix()}",
            limit=MAX_SOURCE_BYTES,
        )
        if len(raw) != expected_bytes or _sha256(raw) != expected_sha:
            raise CutLivenessCLIError(
                f"implementation source drifted: {relative.as_posix()}"
            )
        captured[name] = (path, raw, is_package)
    try:
        schema = json.loads(schema_raw.decode("utf-8"))
        runtime = schema["producer_contract"]["controlled_runtime"]
    except (KeyError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CutLivenessCLIError(
            "cut-liveness controlled runtime schema is malformed"
        ) from exc
    expected_rows = sorted(
        (
            {
                "bytes": expected_bytes,
                "path": relative.as_posix(),
                "sha256": expected_sha,
            }
            for _name, relative, expected_bytes, expected_sha, _package in (
                _CAPTURED_SOURCE_ROWS
            )
        ),
        key=lambda row: str(row["path"]),
    )
    if (
        runtime.get("implementation_source_closure") != expected_rows
        or runtime.get("python_flags") != ["-B", "-P", "-s", "-S"]
        or runtime.get("python_hash_seed") != PYTHON_HASH_SEED
        or runtime.get("python_implementation") != PYTHON_IMPLEMENTATION
        or runtime.get("python_major") != PYTHON_VERSION[0]
        or runtime.get("python_minor") != PYTHON_VERSION[1]
        or runtime.get("hash_randomization") != 0
        or runtime.get("python_optimize") != 0
        or runtime.get("pycache_prefix") != PYCACHE_PREFIX
        or schema.get("limits", {}).get("max_cli_stdout_bytes")
        != MAX_STDOUT_BYTES
        or schema.get("limits", {}).get("max_cli_stderr_bytes")
        != MAX_STDERR_BYTES
        or schema.get("limits", {}).get("max_cli_wall_seconds")
        != int(MAX_WALL_SECONDS)
    ):
        raise CutLivenessCLIError(
            "cut-liveness controlled runtime contract drifted"
        )
    return schema_raw, producer_raw, captured


def _execute_captured_module(
    name: str, path: Path, raw: bytes, *, is_package: bool
) -> ModuleType:
    if name in sys.modules:
        raise CutLivenessCLIError(
            f"captured source module was preloaded: {name}"
        )
    loader = importlib.machinery.SourceFileLoader(name, str(path))
    specification = importlib.util.spec_from_file_location(
        name,
        path,
        loader=loader,
        submodule_search_locations=[str(path.parent)] if is_package else None,
    )
    if (
        specification is None
        or specification.loader is not loader
        or specification.origin != str(path)
        or specification.cached is None
        or not specification.cached.startswith(PYCACHE_PREFIX + "/")
    ):
        raise CutLivenessCLIError(
            f"cannot create exact captured source specification: {name}"
        )
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        code = loader.source_to_code(raw, str(path))
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    if "." in name:
        parent_name, attribute = name.rsplit(".", 1)
        parent = sys.modules.get(parent_name)
        if parent is None:
            sys.modules.pop(name, None)
            raise CutLivenessCLIError(
                f"captured source parent is absent: {parent_name}"
            )
        setattr(parent, attribute, module)
    return module


def _attest_loaded_source_closure(
    module: ModuleType,
    schema_raw: bytes,
    producer_raw: bytes,
    captured: dict[str, tuple[Path, bytes, bool]],
    *,
    prior_meta_path: tuple[object, ...],
    prior_sys_path: tuple[str, ...],
) -> None:
    expected = {
        name: (path, is_package)
        for name, (path, _raw, is_package) in captured.items()
    }
    expected[PRODUCER_MODULE_NAME] = (PRODUCER_PATH, False)
    if tuple(sys.meta_path) != prior_meta_path or tuple(sys.path) != prior_sys_path:
        raise CutLivenessCLIError(
            "producer changed the controlled import machinery"
        )
    for name, (path, is_package) in expected.items():
        loaded = sys.modules.get(name)
        specification = None if loaded is None else getattr(loaded, "__spec__", None)
        locations = [str(path.parent)] if is_package else None
        if (
            loaded is None
            or specification is None
            or type(specification.loader)
            is not importlib.machinery.SourceFileLoader
            or getattr(loaded, "__file__", None) != str(path)
            or specification.origin != str(path)
            or specification.cached is None
            or not specification.cached.startswith(PYCACHE_PREFIX + "/")
            or (
                locations is None
                and specification.submodule_search_locations is not None
            )
            or (
                locations is not None
                and list(specification.submodule_search_locations or [])
                != locations
            )
            or path.resolve(strict=True)
            != Path(str(loaded.__file__)).resolve(strict=True)
        ):
            raise CutLivenessCLIError(
                f"loaded source identity drifted: {name}"
            )
    root_physical = ROOT.resolve(strict=True)
    expected_project_modules = {
        "__main__": EXPECTED_CLI_PATH.resolve(strict=True),
        **{
            name: path.resolve(strict=True)
            for name, (path, _package) in expected.items()
        },
    }
    observed_project_modules: set[str] = set()
    for name, loaded in tuple(sys.modules.items()):
        source = getattr(loaded, "__file__", None)
        if type(source) is not str:
            continue
        try:
            physical = Path(source).resolve(strict=True)
        except OSError as exc:
            raise CutLivenessCLIError(
                f"cannot resolve loaded module origin: {name}"
            ) from exc
        if physical == root_physical or root_physical in physical.parents:
            if expected_project_modules.get(name) != physical:
                raise CutLivenessCLIError(
                    f"unexpected repository module loaded: {name}"
                )
            observed_project_modules.add(name)
    if observed_project_modules != set(expected_project_modules):
        raise CutLivenessCLIError(
            "loaded repository source closure is incomplete"
        )
    if _read_regular(
        SCHEMA_PATH, label="post-load schema", limit=MAX_SCHEMA_BYTES
    ) != schema_raw:
        raise CutLivenessCLIError("schema changed during controlled load")
    if _read_regular(
        PRODUCER_PATH, label="post-load producer", limit=MAX_SOURCE_BYTES
    ) != producer_raw:
        raise CutLivenessCLIError("producer changed during controlled load")
    for name, (path, raw, _package) in captured.items():
        if _read_regular(
            path, label=f"post-load source {name}", limit=MAX_SOURCE_BYTES
        ) != raw:
            raise CutLivenessCLIError(
                f"implementation source changed during controlled load: {name}"
            )
    if sys.modules.get(PRODUCER_MODULE_NAME) is not module:
        raise CutLivenessCLIError("controlled producer registration drifted")


def _load_producer() -> ModuleType:
    schema_raw, producer_raw, captured = _authenticate_sources()
    prior_meta_path = tuple(sys.meta_path)
    prior_sys_path = tuple(sys.path)
    for name, _relative, _bytes, _sha, _package in _CAPTURED_SOURCE_ROWS:
        path, raw, is_package = captured[name]
        _execute_captured_module(name, path, raw, is_package=is_package)
    module = _execute_captured_module(
        PRODUCER_MODULE_NAME,
        PRODUCER_PATH,
        producer_raw,
        is_package=False,
    )
    required = (
        "build_candidate_dependency_vector_cut_liveness",
        "canonical_document_bytes",
        "cut_liveness_schema_identity",
        "load_dependency_vector_cut_liveness",
    )
    if not all(callable(getattr(module, name, None)) for name in required):
        raise CutLivenessCLIError("controlled producer API is incomplete")
    _attest_loaded_source_closure(
        module,
        schema_raw,
        producer_raw,
        captured,
        prior_meta_path=prior_meta_path,
        prior_sys_path=prior_sys_path,
    )
    return module


def _create_only(path: Path, raw: bytes) -> None:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label="output parent")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    created_inode: tuple[int, int] | None = None
    created_identity: tuple[int, int, int, int, int] | None = None

    def unlink_only_created_inode() -> None:
        if created_inode is None:
            return
        try:
            current = absolute.lstat()
            if (
                not stat.S_ISLNK(current.st_mode)
                and stat.S_ISREG(current.st_mode)
                and (current.st_dev, current.st_ino) == created_inode
            ):
                absolute.unlink()
        except OSError:
            pass

    try:
        descriptor = os.open(absolute, flags, 0o644)
        opened = os.fstat(descriptor)
        if not stat.S_ISREG(opened.st_mode):
            raise CutLivenessCLIError("created output is not a regular file")
        created_inode = (opened.st_dev, opened.st_ino)
        try:
            written = 0
            while written < len(raw):
                count = os.write(descriptor, raw[written:])
                if count <= 0:
                    raise OSError("short write")
                written += count
            os.fsync(descriptor)
            metadata = os.fstat(descriptor)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size != len(raw)
                or (metadata.st_dev, metadata.st_ino) != created_inode
            ):
                raise CutLivenessCLIError(
                    "created output is not the exact regular file"
                )
            created_identity = _identity(metadata)
        finally:
            os.close(descriptor)
            descriptor = None
        path_after_write = absolute.lstat()
        if (
            created_identity is None
            or stat.S_ISLNK(path_after_write.st_mode)
            or not stat.S_ISREG(path_after_write.st_mode)
            or _identity(path_after_write) != created_identity
        ):
            raise CutLivenessCLIError(
                "created output pathname identity changed after write"
            )
        retained = _read_regular(
            absolute, label="created output", limit=MAX_DOCUMENT_BYTES
        )
        path_after_read = absolute.lstat()
        if (
            retained != raw
            or stat.S_ISLNK(path_after_read.st_mode)
            or not stat.S_ISREG(path_after_read.st_mode)
            or _identity(path_after_read) != created_identity
        ):
            raise CutLivenessCLIError(
                "created output bytes or pathname identity differ"
            )
    except FileExistsError as exc:
        raise CutLivenessCLIError("output path already exists") from exc
    except CutLivenessCLIError:
        unlink_only_created_inode()
        raise
    except OSError as exc:
        unlink_only_created_inode()
        raise CutLivenessCLIError("cannot create exact output") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _description(module: ModuleType) -> dict[str, object]:
    return {
        "build_executed": False,
        "candidate_artifact_created": False,
        "confirmation_for_create_only_output": CONFIRMATION,
        "default_write": False,
        "expected_candidate": {
            "artifact_bytes": 11_958,
            "artifact_sha256": "c606af87e62b2e4d94303a0c8313efa9033d91c26321f7392351f471927ddc22",
            "derived_direct_dependencies": ["mul_add", "add_comm"],
            "proof_term_sha256": "5c480eb51b7bd0f1f0f8b3485cc071dc1f78aea2baace449533cad27d6dcf6b4",
        },
        "format": "peano-hydra-library-pilot-dependency-vector-cut-liveness-source-protocol-v1",
        "runtime": {
            "bounded_child": True,
            "hash_randomization": 0,
            "max_stderr_bytes": MAX_STDERR_BYTES,
            "max_stdout_bytes": MAX_STDOUT_BYTES,
            "max_wall_seconds": int(MAX_WALL_SECONDS),
            "producer_load_mode": (
                "authenticated-source-bytes-"
                "SourceFileLoader.source_to_code-exec"
            ),
            "pycache_prefix": PYCACHE_PREFIX,
            "python_flags": ["-B", "-P", "-s", "-S"],
            "python_hash_seed": PYTHON_HASH_SEED,
            "python_implementation": PYTHON_IMPLEMENTATION,
            "python_major": PYTHON_VERSION[0],
            "python_minor": PYTHON_VERSION[1],
            "python_optimize": 0,
        },
        "producer_source": {
            "artifact_bytes": PRODUCER_SOURCE_BYTES,
            "artifact_sha256": PRODUCER_SOURCE_SHA256,
            "path": PRODUCER_PATH.relative_to(ROOT).as_posix(),
        },
        "schema": module.cut_liveness_schema_identity(),
        "status": "described-no-build-no-write",
        "suggested_output": SUGGESTED_OUTPUT.as_posix(),
        "v": 1,
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Controlled one-root proof-producing Cut-liveness builder."
    )
    operation = parser.add_mutually_exclusive_group()
    operation.add_argument(
        "--build",
        action="store_true",
        help="execute the exact transform and emit its canonical candidate",
    )
    operation.add_argument(
        "--validate",
        type=Path,
        metavar="PATH",
        help="load and exactly reconstruct one canonical candidate",
    )
    operation.add_argument(
        "--describe",
        action="store_true",
        help="emit the source-protocol receipt (the default operation)",
    )
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="explicit repository root for fixed input reconstruction",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="absent create-only destination; stdout is the default",
    )
    parser.add_argument(
        "--confirm-create",
        metavar="TOKEN",
        help="exact capability token required with --output",
    )
    parser.add_argument(
        "--_controlled-worker",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser


def _exact_repository_root(value: Path | None) -> Path:
    candidate = ROOT if value is None else _lexical_absolute(value)
    _require_directory_chain(candidate, label="repository root")
    try:
        if (
            _lexical_absolute(candidate) != _lexical_absolute(ROOT)
            or candidate.resolve(strict=True) != ROOT.resolve(strict=True)
        ):
            raise CutLivenessCLIError(
                "--repository-root must identify the controlled source snapshot"
            )
    except OSError as exc:
        raise CutLivenessCLIError("cannot inspect repository root") from exc
    return ROOT


def _controlled_environment(
    *, capability_fd: int, capability_sha256: str
) -> dict[str, str]:
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
            "PYTHONHASHSEED": PYTHON_HASH_SEED,
            "PYTHONPYCACHEPREFIX": PYCACHE_PREFIX,
            _WORKER_ENVIRONMENT: "1",
            _WORKER_PARENT_RUNTIME: PYTHON_RUNTIME_TAG,
            _WORKER_CAPABILITY_FD: str(capability_fd),
            _WORKER_CAPABILITY_SHA256: capability_sha256,
        }
    )
    return allowed


def _run_bounded_child(
    command: list[str],
    *,
    environment: dict[str, str],
) -> subprocess.CompletedProcess[bytes]:
    if (
        type(command) is not list
        or not command
        or not all(type(item) is str and item for item in command)
        or type(environment) is not dict
        or not all(
            type(name) is str and type(value) is str
            for name, value in environment.items()
        )
    ):
        raise CutLivenessCLIError("controlled child configuration is malformed")
    process: subprocess.Popen[bytes] | None = None
    selector = selectors.DefaultSelector()
    streams: list[object] = []
    stdout = bytearray()
    stderr = bytearray()
    capability_fd = int(environment[_WORKER_CAPABILITY_FD])
    try:
        try:
            process = subprocess.Popen(
                command,
                cwd=ROOT,
                env=environment,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                close_fds=True,
                pass_fds=(capability_fd,),
            )
        except OSError as exc:
            raise CutLivenessCLIError(
                "cannot start controlled cut-liveness worker"
            ) from exc
        if process.stdout is None or process.stderr is None:
            raise CutLivenessCLIError("controlled worker pipes are unavailable")
        streams = [process.stdout, process.stderr]
        selector.register(process.stdout, selectors.EVENT_READ, "stdout")
        selector.register(process.stderr, selectors.EVENT_READ, "stderr")
        deadline = time.monotonic() + MAX_WALL_SECONDS
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise CutLivenessCLIError(
                    "controlled worker exceeded its wall-time cap"
                )
            for key, _mask in selector.select(min(remaining, 1.0)):
                buffer = stdout if key.data == "stdout" else stderr
                limit = (
                    MAX_STDOUT_BYTES
                    if key.data == "stdout"
                    else MAX_STDERR_BYTES
                )
                try:
                    chunk = os.read(
                        key.fileobj.fileno(),
                        min(65_536, limit - len(buffer) + 1),
                    )
                except OSError as exc:
                    raise CutLivenessCLIError(
                        "cannot read controlled worker output"
                    ) from exc
                if not chunk:
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                buffer.extend(chunk)
                if len(buffer) > limit:
                    raise CutLivenessCLIError(
                        f"controlled worker {key.data} exceeded its hard byte cap"
                    )
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise CutLivenessCLIError(
                "controlled worker exceeded its wall-time cap"
            )
        try:
            returncode = process.wait(timeout=remaining)
        except subprocess.TimeoutExpired as exc:
            raise CutLivenessCLIError(
                "controlled worker exceeded its wall-time cap"
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


def _validate_argument_contract(
    arguments: argparse.Namespace, *, worker: bool
) -> Path:
    repository_root = _exact_repository_root(arguments.repository_root)
    if worker:
        if arguments.output is not None or arguments.confirm_create is not None:
            raise CutLivenessCLIError(
                "controlled worker cannot publish an output path"
            )
    else:
        if arguments.output is not None and not (
            arguments.build or arguments.validate is not None
        ):
            raise CutLivenessCLIError("--output requires --build or --validate")
        if (
            arguments.output is not None
            and arguments.confirm_create != CONFIRMATION
        ):
            raise CutLivenessCLIError(
                "--output requires the exact --confirm-create token"
            )
        if arguments.output is None and arguments.confirm_create is not None:
            raise CutLivenessCLIError(
                "--confirm-create is valid only with --output"
            )
    return repository_root


def _worker(arguments: argparse.Namespace) -> int:
    _require_controlled_worker()
    _consume_worker_capability()
    repository_root = _validate_argument_contract(arguments, worker=True)
    module = _load_producer()
    if arguments.build:
        value = module.build_candidate_dependency_vector_cut_liveness(
            repository_root
        )
        raw = module.canonical_document_bytes(value)
    elif arguments.validate is not None:
        value = module.load_dependency_vector_cut_liveness(
            arguments.validate, repository_root
        )
        raw = module.canonical_document_bytes(value)
    else:
        raw = _canonical_bytes(_description(module))
    if len(raw) > MAX_STDOUT_BYTES:
        raise CutLivenessCLIError("controlled result exceeds its stdout cap")
    sys.stdout.buffer.write(raw)
    sys.stdout.buffer.flush()
    return 0


def _parent(arguments: argparse.Namespace) -> int:
    _require_runtime_version(role="parent")
    _require_cli_location()
    repository_root = _validate_argument_contract(arguments, worker=False)
    child = [
        sys.executable,
        "-B",
        "-P",
        "-s",
        "-S",
        str(EXPECTED_CLI_PATH),
        "--_controlled-worker",
        "--repository-root",
        str(repository_root),
    ]
    if arguments.build:
        child.append("--build")
    elif arguments.validate is not None:
        child.extend(
            ("--validate", str(_lexical_absolute(arguments.validate)))
        )
    else:
        child.append("--describe")
    read_descriptor, write_descriptor = os.pipe()
    capability = os.urandom(32).hex().encode("ascii")
    capability_sha256 = _sha256(capability)
    try:
        os.write(write_descriptor, capability)
    finally:
        os.close(write_descriptor)
    try:
        completed = _run_bounded_child(
            child,
            environment=_controlled_environment(
                capability_fd=read_descriptor,
                capability_sha256=capability_sha256,
            ),
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
        raise CutLivenessCLIError(
            f"controlled worker exited {completed.returncode}"
        )
    if completed.stderr:
        sys.stderr.buffer.write(completed.stderr)
        sys.stderr.buffer.flush()
        raise CutLivenessCLIError(
            "controlled worker emitted unexpected stderr"
        )
    if arguments.output is None:
        sys.stdout.buffer.write(completed.stdout)
        sys.stdout.buffer.flush()
    else:
        _create_only(arguments.output, completed.stdout)
    return 0


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments._controlled_worker:
            return _worker(arguments)
        return _parent(arguments)
    except Exception as exc:
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            raise
        message = " ".join(str(exc).split()) or type(exc).__name__
        print(f"cut-liveness CLI error: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
