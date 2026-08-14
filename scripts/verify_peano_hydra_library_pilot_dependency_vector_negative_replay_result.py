#!/usr/bin/env python3
"""Structurally verify a completed Hydra A2.3c negative-replay result.

The controlled verifier is tactic-free.  It authenticates and direct-loads
the independent standard-library-only verifier source, emits no result by
default, and publishes an explicitly requested receipt create-only.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.machinery
import importlib.util
import os
from pathlib import Path
import stat
import sys
import tempfile


PYCACHE_PREFIX = "/proc/peano-hydra-a23c-disabled-pycache"
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
_seed = os.environ.get("PYTHONHASHSEED")
if (
    getattr(sys.flags, "safe_path", False) is not True
    or sys.flags.no_site != 1
    or sys.flags.no_user_site != 1
    or sys.flags.optimize != 0
    or sys.dont_write_bytecode is not True
    or type(_seed) is not str
    or not _seed.isdecimal()
    or any(name in os.environ for name in _FORBIDDEN_ENVIRONMENT)
    or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
    or sys.pycache_prefix != PYCACHE_PREFIX
):
    raise RuntimeError(
        "A2.3c structural verifier requires controlled -B -P -s -S, "
        "optimize=0, an explicit decimal hash seed, no Python injection "
        "variables, and the fixed disabled pycache prefix"
    )

LEXICAL_CLI_PATH = Path(os.path.abspath(__file__))
ROOT = LEXICAL_CLI_PATH.parents[1]
EXPECTED_CLI_PATH = (
    ROOT
    / "scripts/"
    "verify_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py"
)
VERIFIER_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_negative_replay_verifier.py"
)
VERIFIER_MODULE_NAME = "_peano_hydra_a23c_tactic_free_structural_verifier"
VERIFIER_SOURCE_BYTES = 85_510
VERIFIER_SOURCE_SHA256 = (
    "33f197045cabe95bda3b7ae0ff871b08cb1b186a861827ea08ad0f76cf7908d8"
)
MAX_SOURCE_BYTES = 16_000_000


def _forbidden_modules() -> list[str]:
    return sorted(
        name
        for name in sys.modules
        if name == "training"
        or name.startswith("training.")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
    )


def _require_directory_chain(path: Path, *, label: str) -> None:
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    try:
        for component in absolute.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise RuntimeError(f"{label} contains a symlink or non-directory")
    except RuntimeError:
        raise
    except OSError as exc:
        raise RuntimeError(f"cannot inspect {label}") from exc


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _read_exact_source(
    path: Path, *, label: str, expected_bytes: int, expected_sha256: str
) -> bytes:
    _require_directory_chain(path.parent, label=f"{label} ancestors")
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} must be a non-symlink regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        chunks: list[bytes] = []
        remaining = expected_bytes + 1
        while remaining:
            chunk = os.read(descriptor, min(1_048_576, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(descriptor)
        path_after = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_size != expected_bytes
        or _stat_identity(metadata) != _stat_identity(before)
        or _stat_identity(before) != _stat_identity(after)
        or _stat_identity(after) != _stat_identity(path_after)
        or len(raw) != expected_bytes
        or hashlib.sha256(raw).hexdigest() != expected_sha256
    ):
        raise RuntimeError(f"{label} source identity drifted")
    return raw


def _preflight() -> None:
    if LEXICAL_CLI_PATH != EXPECTED_CLI_PATH:
        raise RuntimeError("A2.3c verifier CLI lexical path drifted")
    _require_directory_chain(LEXICAL_CLI_PATH.parent, label="verifier CLI ancestors")
    try:
        cli_metadata = LEXICAL_CLI_PATH.lstat()
        cwd = Path.cwd().resolve(strict=True)
        wanted = ROOT.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("cannot inspect controlled verifier process") from exc
    if (
        stat.S_ISLNK(cli_metadata.st_mode)
        or not stat.S_ISREG(cli_metadata.st_mode)
        or cwd != wanted
        or _forbidden_modules()
    ):
        raise RuntimeError("A2.3c verifier process source, cwd, or imports drifted")
    try:
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise RuntimeError("cannot inspect disabled verifier pycache prefix") from exc
    else:
        raise RuntimeError("disabled verifier pycache prefix unexpectedly exists")
    expected_meta_path = (
        ("_frozen_importlib", "BuiltinImporter"),
        ("_frozen_importlib", "FrozenImporter"),
        ("_frozen_importlib_external", "PathFinder"),
    )
    actual_meta_path = tuple(
        (getattr(finder, "__module__", None), getattr(finder, "__qualname__", None))
        for finder in sys.meta_path
    )
    if actual_meta_path != expected_meta_path:
        raise RuntimeError("A2.3c verifier import machinery is contaminated")
    resolved_root = ROOT.resolve(strict=True)
    for entry in sys.path:
        if type(entry) is not str or not entry:
            raise RuntimeError("A2.3c verifier sys.path contains an unsafe entry")
        try:
            resolved = Path(entry).resolve(strict=False)
        except OSError as exc:
            raise RuntimeError("cannot inspect verifier sys.path") from exc
        if resolved == resolved_root or resolved_root in resolved.parents:
            raise RuntimeError("repository path precedes controlled source loader")


def _load_verifier():
    _preflight()
    raw = _read_exact_source(
        VERIFIER_PATH,
        label="A2.3c tactic-free structural verifier",
        expected_bytes=VERIFIER_SOURCE_BYTES,
        expected_sha256=VERIFIER_SOURCE_SHA256,
    )
    if VERIFIER_MODULE_NAME in sys.modules:
        raise RuntimeError("A2.3c private verifier name is already loaded")
    specification = importlib.util.spec_from_file_location(
        VERIFIER_MODULE_NAME, VERIFIER_PATH
    )
    if (
        specification is None
        or type(specification.loader) is not importlib.machinery.SourceFileLoader
        or specification.origin is None
        or Path(specification.origin).resolve(strict=True)
        != VERIFIER_PATH.resolve(strict=True)
        or specification.cached is None
        or not specification.cached.startswith(PYCACHE_PREFIX + "/")
    ):
        raise RuntimeError("cannot create exact A2.3c verifier source loader")
    before = set(sys.modules)
    module = importlib.util.module_from_spec(specification)
    sys.modules[VERIFIER_MODULE_NAME] = module
    try:
        code = specification.loader.source_to_code(raw, str(VERIFIER_PATH))
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise
    introduced = set(sys.modules) - before
    if (
        _forbidden_modules()
        or getattr(module, "PYCACHE_PREFIX", None) != PYCACHE_PREFIX
        or getattr(module, "_REPOSITORY_ROOT", None) != ROOT
        or hashlib.sha256(raw).hexdigest() != VERIFIER_SOURCE_SHA256
    ):
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise RuntimeError("loaded A2.3c verifier identity or boundary drifted")
    for name in introduced:
        if name == VERIFIER_MODULE_NAME:
            continue
        loaded = sys.modules.get(name)
        source = getattr(loaded, "__file__", None)
        if type(source) is str:
            try:
                resolved = Path(source).resolve(strict=False)
            except OSError as exc:
                raise RuntimeError("cannot inspect verifier import closure") from exc
            if resolved == ROOT or ROOT in resolved.parents:
                sys.modules.pop(VERIFIER_MODULE_NAME, None)
                raise RuntimeError("verifier loaded repository code outside its source")
    return module


_verifier = _load_verifier()
VerificationError = (
    _verifier.LibraryPilotDependencyVectorNegativeReplayVerificationError
)
canonical_receipt_bytes = (
    _verifier.canonical_negative_replay_verification_receipt_bytes
)
load_and_verify_result = (
    _verifier.load_and_verify_pilot_dependency_vector_negative_replay_result
)


def _absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("receipt path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _absolute(path)
    _require_directory_chain(absolute.parent, label="receipt parent")
    return absolute.parent


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise VerificationError("cannot inspect receipt destination") from exc
    raise VerificationError("receipt destination already exists; output is create-only")


def _publish_create_only(path: Path, raw: bytes) -> None:
    destination = _absolute(path)
    parent = _safe_parent(destination)
    _require_absent(destination)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.", suffix=".tmp", dir=parent
    )
    temporary = Path(temporary_name)
    completed = False
    temporary_identity: tuple[int, int] | None = None
    published_identity: tuple[int, int] | None = None
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(raw)
            stream.flush()
            os.fchmod(stream.fileno(), 0o644)
            os.fsync(stream.fileno())
            metadata = os.fstat(stream.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_size != len(raw)
                or stat.S_IMODE(metadata.st_mode) != 0o644
            ):
                raise VerificationError(
                    "staged receipt descriptor identity or mode drifted"
                )
            temporary_identity = (metadata.st_dev, metadata.st_ino)
        staged = temporary.lstat()
        if (
            stat.S_ISLNK(staged.st_mode)
            or not stat.S_ISREG(staged.st_mode)
            or (staged.st_dev, staged.st_ino) != temporary_identity
            or staged.st_size != len(raw)
            or stat.S_IMODE(staged.st_mode) != 0o644
        ):
            raise VerificationError(
                "staged receipt path no longer names its authenticated descriptor"
            )
        _require_absent(destination)
        os.link(temporary, destination, follow_symlinks=False)
        published = destination.lstat()
        published_identity = (published.st_dev, published.st_ino)
        if (
            stat.S_ISLNK(published.st_mode)
            or not stat.S_ISREG(published.st_mode)
            or published_identity != temporary_identity
            or published.st_size != len(raw)
            or stat.S_IMODE(published.st_mode) != 0o644
        ):
            raise VerificationError("published receipt identity, size, or mode differs")
        temporary.unlink()
        parent_descriptor = os.open(
            parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        )
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        completed = True
    except FileExistsError as exc:
        raise VerificationError("receipt destination raced or already exists") from exc
    except (VerificationError, OSError) as exc:
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
        if isinstance(exc, VerificationError):
            raise
        raise VerificationError("cannot atomically publish verification receipt") from exc
    finally:
        if not completed and published_identity is not None:
            try:
                identity = destination.lstat()
            except (FileNotFoundError, OSError):
                pass
            else:
                if (
                    not stat.S_ISLNK(identity.st_mode)
                    and stat.S_ISREG(identity.st_mode)
                    and (identity.st_dev, identity.st_ino) == published_identity
                ):
                    try:
                        destination.unlink()
                    except OSError:
                        pass
        try:
            staged = temporary.lstat()
        except (FileNotFoundError, OSError):
            pass
        else:
            if (
                temporary_identity is not None
                and not stat.S_ISLNK(staged.st_mode)
                and stat.S_ISREG(staged.st_mode)
                and (staged.st_dev, staged.st_ino) == temporary_identity
            ):
                try:
                    temporary.unlink()
                except OSError:
                    pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, help="canonical A2.3c result")
    parser.add_argument("--output", type=Path, help="absent create-only receipt path")
    parser.add_argument(
        "--repository-root",
        type=Path,
        help="exact repository root (must resolve to this verifier snapshot)",
    )
    args = parser.parse_args()
    supplied = (
        args.candidate is not None,
        args.output is not None,
        args.repository_root is not None,
    )
    if any(supplied) and not all(supplied):
        parser.error("--candidate, --output, and --repository-root are required together")
    if not any(supplied):
        print(
            "independent A2.3c tactic-free structural verifier ready; "
            "no candidate verified and no file written",
            flush=True,
        )
        return
    try:
        supplied_root = args.repository_root.resolve(strict=True)
        exact_root = ROOT.resolve(strict=True)
    except OSError as exc:
        raise VerificationError("cannot resolve supplied repository root") from exc
    if supplied_root != exact_root:
        raise VerificationError("supplied repository root differs from verifier snapshot")
    receipt = load_and_verify_result(
        args.candidate, repository_root=ROOT
    )
    raw = canonical_receipt_bytes(receipt)
    _publish_create_only(args.output, raw)
    print(
        "independent A2.3c structural verification: 3 baselines, "
        "22 negative records, 44 retained route labels; no tactic replay or "
        f"execution binding; root {receipt['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except VerificationError as exc:
        raise SystemExit(str(exc)) from None
