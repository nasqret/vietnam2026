#!/usr/bin/env python3
"""Independently verify a Hydra A2.3b vector audit and emit its receipt."""

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


PYCACHE_PREFIX = "/proc/peano-hydra-a23b-disabled-pycache"
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
    or any(name in os.environ for name in _FORBIDDEN_ENVIRONMENT)
    or type(_seed) is not str
    or not _seed.isdecimal()
    or os.environ.get("PYTHONPYCACHEPREFIX") != PYCACHE_PREFIX
    or sys.pycache_prefix != PYCACHE_PREFIX
):
    raise RuntimeError(
        "independent A2.3b verifier requires controlled -B -P -s -S, "
        "optimize=0, absent Python injection variables, an explicit decimal "
        "hash seed, and the fixed disabled pycache prefix"
    )

LEXICAL_CLI_PATH = Path(os.path.abspath(__file__))
ROOT = LEXICAL_CLI_PATH.parents[1]
EXPECTED_CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_audit.py"
)
try:
    _cli_metadata = LEXICAL_CLI_PATH.lstat()
except OSError as exc:
    raise RuntimeError("cannot inspect independent verifier CLI source") from exc
if (
    LEXICAL_CLI_PATH != EXPECTED_CLI_PATH
    or stat.S_ISLNK(_cli_metadata.st_mode)
    or not stat.S_ISREG(_cli_metadata.st_mode)
):
    raise RuntimeError(
        "independent verifier CLI must be the exact lexical non-symlink source"
    )
PY_ROOT = ROOT / "peano-lab" / "py"
for import_root in (str(PY_ROOT), str(ROOT)):
    while import_root in sys.path:
        sys.path.remove(import_root)
# Standard-library paths remain first.  Only the otherwise unavailable Peano
# package root is appended.
sys.path.append(str(PY_ROOT))

VERIFIER_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library_pilot_dependency_vector_audit_verifier.py"
)
VERIFIER_MODULE_NAME = "_peano_hydra_a23b_independent_verifier"
VERIFIER_SOURCE_BYTES = 109_448
VERIFIER_SOURCE_SHA256 = (
    "b5f5cf39ea7b12d3ed52ee176ed733b28fa2e9224640e89dac77df87b14dfab1"
)
_KERNEL_IMPORT_SOURCES = (
    (
        Path("peano_lab/__init__.py"),
        257,
        "3ec676b9d149f999cbdd15012c9e3a131428602718aa4695b9b4f9542beb3d9a",
    ),
    (
        Path("peano_lab/kernel/__init__.py"),
        263,
        "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    ),
    (
        Path("peano_lab/kernel/artifact_codec.py"),
        27_892,
        "c9c4d3847c2c5fa7af683fb84f9e93341782e4b82f2579a675b97602aba39110",
    ),
    (
        Path("peano_lab/kernel/checker.py"),
        10_738,
        "396c593f0d734d1c5cb728610a95f17c5f8a0c2076ef173203f9265d030f6a19",
    ),
    (
        Path("peano_lab/kernel/formulas.py"),
        10_950,
        "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    ),
    (
        Path("peano_lab/kernel/proofs.py"),
        5_015,
        "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    ),
    (
        Path("peano_lab/kernel/terms.py"),
        9_133,
        "e44a937d0660651f08fa57b7ff867c608ff134ac01b48c588206d641132f3185",
    ),
    (
        Path("peano_lab/kernel/subst.py"),
        5_165,
        "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    ),
)
_CACHE_PREFLIGHTED = False
_KERNEL_PREFLIGHTED = False


def _forbidden_runtime_modules() -> list[str]:
    return sorted(
        name
        for name in sys.modules
        if name.startswith("peano_lab.engine")
        or name.startswith("peano_lab.library")
        or name.startswith("peano_lab.tactics")
        or name == "training"
        or name.startswith("training.")
    )


def _require_directory_chain(root: Path, parent: Path, *, label: str) -> None:
    absolute_parent = Path(os.path.abspath(parent))
    current_absolute = Path(absolute_parent.anchor)
    for component in absolute_parent.parts[1:]:
        current_absolute = current_absolute / component
        try:
            metadata = current_absolute.lstat()
        except OSError as exc:
            raise RuntimeError(
                f"cannot inspect {label} absolute ancestor"
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(
                f"{label} absolute ancestor contains a symlink or non-directory"
            )
    try:
        relative = parent.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes its lexical root") from exc
    current = root
    for component in relative.parts:
        current = current / component
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise RuntimeError(f"cannot inspect {label} ancestor") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(
                f"{label} ancestor contains a symlink or non-directory"
            )


def _read_exact_source(
    path: Path,
    *,
    root: Path,
    label: str,
    expected_bytes: int,
    expected_sha256: str,
) -> bytes:
    _require_directory_chain(root, path.parent, label=label)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise RuntimeError(f"{label} is not a non-symlink regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RuntimeError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        raw = os.read(descriptor, expected_bytes + 1)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise RuntimeError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(before.st_mode)
        or before.st_size != expected_bytes
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
        or len(raw) != expected_bytes
        or hashlib.sha256(raw).hexdigest() != expected_sha256
    ):
        raise RuntimeError(f"{label} source identity drifted")
    return raw


def _preflight_cache_policy() -> None:
    global _CACHE_PREFLIGHTED
    if _CACHE_PREFLIGHTED:
        raise RuntimeError("bytecode-cache preflight may run only once")
    _require_directory_chain(
        ROOT,
        LEXICAL_CLI_PATH.parent,
        label="independent verifier CLI source",
    )
    try:
        Path(PYCACHE_PREFIX).lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise RuntimeError("cannot inspect disabled pycache prefix") from exc
    else:
        raise RuntimeError("disabled pycache prefix unexpectedly exists")
    try:
        cwd = Path.cwd().resolve(strict=True)
        wanted = ROOT.resolve(strict=True)
    except OSError as exc:
        raise RuntimeError("cannot resolve controlled verifier cwd") from exc
    if cwd != wanted:
        raise RuntimeError("controlled verifier cwd differs from repository root")
    _CACHE_PREFLIGHTED = True


def _preflight_kernel_sources() -> None:
    global _KERNEL_PREFLIGHTED
    if _KERNEL_PREFLIGHTED:
        raise RuntimeError("kernel source preflight may run only once")
    for relative, expected_bytes, expected_sha256 in _KERNEL_IMPORT_SOURCES:
        _read_exact_source(
            PY_ROOT / relative,
            root=PY_ROOT,
            label=f"kernel import source {relative.as_posix()!r}",
            expected_bytes=expected_bytes,
            expected_sha256=expected_sha256,
        )
    _KERNEL_PREFLIGHTED = True


def _preflight_kernel_specs() -> None:
    package_root = PY_ROOT / "peano_lab"
    kernel_root = package_root / "kernel"
    targets = (
        ("peano_lab", PY_ROOT, package_root / "__init__.py", package_root),
        (
            "peano_lab.kernel",
            package_root,
            kernel_root / "__init__.py",
            kernel_root,
        ),
        *(
            (
                f"peano_lab.kernel.{name}",
                kernel_root,
                kernel_root / f"{name}.py",
                None,
            )
            for name in (
                "artifact_codec",
                "checker",
                "formulas",
                "proofs",
                "terms",
                "subst",
            )
        ),
    )
    for fullname, search_root, expected_source, expected_package_root in targets:
        specification = importlib.machinery.PathFinder.find_spec(
            fullname, [str(search_root)]
        )
        if (
            specification is None
            or type(specification.loader)
            is not importlib.machinery.SourceFileLoader
            or specification.origin is None
            or Path(specification.origin).resolve(strict=True)
            != expected_source.resolve(strict=True)
            or specification.cached is None
            or not specification.cached.startswith(PYCACHE_PREFIX + "/")
        ):
            raise RuntimeError(f"kernel import specification for {fullname} drifted")
        locations = specification.submodule_search_locations
        if expected_package_root is None:
            if locations is not None:
                raise RuntimeError(f"kernel leaf {fullname} became a package")
        elif locations is None or list(locations) != [str(expected_package_root)]:
            raise RuntimeError(f"kernel package path for {fullname} drifted")


def _load_verifier_source():
    if _forbidden_runtime_modules():
        raise RuntimeError("independent verifier process is contaminated before load")
    _preflight_cache_policy()
    _preflight_kernel_sources()
    _preflight_kernel_specs()
    verifier_raw = _read_exact_source(
        VERIFIER_PATH,
        root=ROOT,
        label="independent A2.3b verifier",
        expected_bytes=VERIFIER_SOURCE_BYTES,
        expected_sha256=VERIFIER_SOURCE_SHA256,
    )
    if VERIFIER_MODULE_NAME in sys.modules:
        raise RuntimeError("independent verifier private name is already loaded")
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
        raise RuntimeError("cannot create exact independent verifier loader")
    module = importlib.util.module_from_spec(specification)
    sys.modules[VERIFIER_MODULE_NAME] = module
    try:
        # Compile the authenticated bytes through the exact SourceFileLoader,
        # avoiding a second path read between authentication and execution.
        code = specification.loader.source_to_code(
            verifier_raw, str(VERIFIER_PATH)
        )
        exec(code, module.__dict__)
    except BaseException:
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise
    if _forbidden_runtime_modules():
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise RuntimeError("verifier source load crossed its import boundary")
    if (
        getattr(module, "PYCACHE_PREFIX", None) != PYCACHE_PREFIX
        or getattr(module, "_REPOSITORY_ROOT", None) != ROOT
        or hashlib.sha256(verifier_raw).hexdigest() != VERIFIER_SOURCE_SHA256
    ):
        sys.modules.pop(VERIFIER_MODULE_NAME, None)
        raise RuntimeError("loaded verifier identity differs after source execution")
    return module


_verifier = _load_verifier_source()
LibraryPilotDependencyVectorAuditVerificationError = (
    _verifier.LibraryPilotDependencyVectorAuditVerificationError
)
canonical_verification_receipt_bytes = (
    _verifier.canonical_verification_receipt_bytes
)
load_and_verify_pilot_dependency_vector_audit = (
    _verifier.load_and_verify_pilot_dependency_vector_audit
)

SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/"
    "l0-pilot-dependency-vector-audit-independent-verification-v1.json"
)


def _absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("receipt path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryPilotDependencyVectorAuditVerificationError(
                    "receipt parent contains a link or non-directory component"
                )
        return current
    except LibraryPilotDependencyVectorAuditVerificationError:
        raise
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot inspect receipt parent"
        ) from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot inspect receipt destination"
        ) from exc
    raise LibraryPilotDependencyVectorAuditVerificationError(
        "receipt destination already exists; verifier output is create-only"
    )


def _publish_create_only(path: Path, raw: bytes) -> None:
    destination = _absolute(path)
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
            raise LibraryPilotDependencyVectorAuditVerificationError(
                "published receipt identity differs"
            )
        temporary.unlink()
        temporary_name = None
        parent_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except (LibraryPilotDependencyVectorAuditVerificationError, OSError) as exc:
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
        if isinstance(exc, LibraryPilotDependencyVectorAuditVerificationError):
            raise
        raise LibraryPilotDependencyVectorAuditVerificationError(
            "cannot atomically publish verification receipt"
        ) from exc
    finally:
        if temporary_name is not None:
            try:
                Path(temporary_name).unlink()
            except (FileNotFoundError, OSError):
                pass


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "No candidate is verified and no file is written by default. "
            f"Suggested explicit receipt path: {SUGGESTED_OUTPUT}"
        ),
    )
    parser.add_argument("--candidate", type=Path, help="canonical producer result")
    parser.add_argument(
        "--producer-source-state",
        type=Path,
        help="canonical explicit four-source producer state used for the build",
    )
    parser.add_argument(
        "--output", type=Path, help="create one new canonical verification receipt"
    )
    args = parser.parse_args()
    supplied = (
        args.candidate is not None,
        args.producer_source_state is not None,
        args.output is not None,
    )
    if any(supplied) and not all(supplied):
        parser.error(
            "--candidate, --producer-source-state, and --output are required together"
        )
    if not any(supplied):
        print(
            "independent A2.3b verifier ready; no verification or retained write "
            "requested",
            flush=True,
        )
        return
    receipt = load_and_verify_pilot_dependency_vector_audit(
        args.candidate,
        args.producer_source_state,
        repository_root=ROOT,
    )
    raw = canonical_verification_receipt_bytes(receipt)
    _publish_create_only(args.output, raw)
    print(
        f"independent A2.3b verification: {receipt['theorem_count']} roots, "
        f"{receipt['aggregate']['kernel_accepted_baseline_artifact_count']} "
        f"kernel-accepted baseline artifacts, 44 routed producer observations/"
        f"22 shared inputs, root {receipt['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryPilotDependencyVectorAuditVerificationError as exc:
        raise SystemExit(str(exc)) from None
