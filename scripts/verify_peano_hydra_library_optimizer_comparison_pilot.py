#!/usr/bin/env python3
"""Independently verify a Hydra A2.3a comparison and emit its receipt."""

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


if (
    getattr(sys.flags, "safe_path", False) is not True
    or sys.flags.no_site != 1
    or sys.flags.no_user_site != 1
    or os.environ.get("PYTHONPATH") not in (None, "")
    or os.environ.get("PYTHONHOME") not in (None, "")
):
    raise RuntimeError(
        "independent verifier requires -P -s -S and an empty PYTHONPATH"
    )

ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
for import_root in (str(PY_ROOT), str(ROOT)):
    while import_root in sys.path:
        sys.path.remove(import_root)
# The standard-library paths installed by the isolated interpreter stay in
# front.  Only the otherwise-unavailable Peano package root is appended.
sys.path.append(str(PY_ROOT))


VERIFIER_PATH = (
    ROOT
    / "training"
    / "peano_hydra"
    / "library_optimizer_comparison_verifier.py"
)
_VERIFIER_MODULE_NAME = "_peano_hydra_a23a_independent_verifier"
_VERIFIER_SOURCE_BYTES = 78_295
_VERIFIER_SOURCE_SHA256 = (
    "683ee529ed4be0e93504846340eeddf47eae1cb3f84967168a971d422ade1dbe"
)
_PYCACHE_PREFIX = "/proc/peano-hydra-a23a-disabled-pycache"
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
_INITIALIZERS_PREFLIGHTED = False
_CACHE_POLICY_PREFLIGHTED = False


def _forbidden_runtime_modules() -> list[str]:
    return sorted(
        name
        for name in sys.modules
        if name.startswith("peano_lab.engine")
        or name.startswith("peano_lab.library")
        or name.startswith("peano_lab.tactics")
        or name == "training.peano_hydra"
        or name.startswith("training.peano_hydra.")
    )


def _preflight_cache_policy() -> None:
    """Force imports away from every adjacent ``__pycache__``/legacy pyc."""

    global _CACHE_POLICY_PREFLIGHTED
    if _CACHE_POLICY_PREFLIGHTED:
        raise RuntimeError("bytecode-cache preflight may run only once")
    if (
        os.environ.get("PYTHONPYCACHEPREFIX") != _PYCACHE_PREFIX
        or sys.pycache_prefix != _PYCACHE_PREFIX
        or sys.dont_write_bytecode is not True
    ):
        raise RuntimeError(
            "independent verifier requires -B and the fixed disabled pycache prefix"
        )
    prefix = Path(_PYCACHE_PREFIX)
    try:
        prefix.lstat()
    except FileNotFoundError:
        pass
    except OSError as exc:
        raise RuntimeError("cannot inspect the disabled pycache prefix") from exc
    else:
        raise RuntimeError("disabled pycache prefix unexpectedly exists")
    _CACHE_POLICY_PREFLIGHTED = True


def _require_directory_chain(root: Path, parent: Path, *, label: str) -> None:
    absolute_parent = Path(os.path.abspath(parent))
    current_absolute = Path(absolute_parent.anchor)
    for component in absolute_parent.parts[1:]:
        current_absolute = current_absolute / component
        try:
            absolute_metadata = current_absolute.lstat()
        except OSError as exc:
            raise RuntimeError(
                f"cannot inspect {label} absolute ancestor {current_absolute}"
            ) from exc
        if stat.S_ISLNK(absolute_metadata.st_mode) or not stat.S_ISDIR(
            absolute_metadata.st_mode
        ):
            raise RuntimeError(
                f"{label} absolute ancestor contains a symlink or non-directory"
            )
    try:
        relative = parent.relative_to(root)
    except ValueError as exc:
        raise RuntimeError(f"{label} escapes the lexical Python root") from exc
    current = root
    for component in (".", *relative.parts):
        if component != ".":
            current = current / component
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise RuntimeError(f"cannot inspect {label} ancestor {current}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise RuntimeError(
                f"{label} ancestor contains a symlink or non-directory"
            )


def _preflight_kernel_sources() -> None:
    """Pin all imported kernel sources before the first ``peano_lab`` import."""

    global _INITIALIZERS_PREFLIGHTED
    if _INITIALIZERS_PREFLIGHTED:
        raise RuntimeError("kernel source preflight may run only once")
    for relative, expected_bytes, expected_sha256 in _KERNEL_IMPORT_SOURCES:
        path = PY_ROOT / relative
        _require_directory_chain(
            PY_ROOT, path.parent, label=f"kernel import source {relative}"
        )
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise RuntimeError(f"cannot inspect kernel import source {relative}") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise RuntimeError(f"kernel import source {relative} is not a regular file")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError as exc:
            raise RuntimeError(f"cannot open kernel import source {relative}") from exc
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode) or before.st_size != expected_bytes:
                raise RuntimeError(f"kernel import source {relative} byte size drifted")
            raw = os.read(descriptor, expected_bytes + 1)
            after = os.fstat(descriptor)
        except OSError as exc:
            raise RuntimeError(f"cannot read kernel import source {relative}") from exc
        finally:
            os.close(descriptor)
        before_identity = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_identity = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if (
            before_identity != after_identity
            or len(raw) != expected_bytes
            or hashlib.sha256(raw).hexdigest() != expected_sha256
        ):
            raise RuntimeError(f"kernel import source {relative} hash drifted")
    _INITIALIZERS_PREFLIGHTED = True


# Retain the reviewed private spelling for adversarial tests and older wrappers.
_preflight_kernel_initializers = _preflight_kernel_sources


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
            or not specification.cached.startswith(_PYCACHE_PREFIX + "/")
        ):
            raise RuntimeError(f"kernel import specification for {fullname} drifted")
        locations = specification.submodule_search_locations
        if expected_package_root is None:
            if locations is not None:
                raise RuntimeError(f"kernel leaf {fullname} became a package")
        elif locations is None or list(locations) != [str(expected_package_root)]:
            raise RuntimeError(f"kernel package path for {fullname} drifted")


def _load_verifier_source():
    """Load the verifier file without executing ``training.peano_hydra`` init."""

    if _forbidden_runtime_modules():
        raise RuntimeError("independent verifier process is contaminated before load")
    _preflight_cache_policy()
    _preflight_kernel_sources()
    _preflight_kernel_specs()
    _require_directory_chain(
        ROOT, VERIFIER_PATH.parent, label="independent verifier source"
    )
    try:
        verifier_metadata = VERIFIER_PATH.lstat()
    except OSError as exc:
        raise RuntimeError("cannot inspect independent verifier source") from exc
    if stat.S_ISLNK(verifier_metadata.st_mode) or not stat.S_ISREG(
        verifier_metadata.st_mode
    ):
        raise RuntimeError("independent verifier source is not a regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(VERIFIER_PATH, flags)
    except OSError as exc:
        raise RuntimeError("cannot open independent verifier source") from exc
    try:
        verifier_before = os.fstat(descriptor)
        verifier_raw = os.read(descriptor, _VERIFIER_SOURCE_BYTES + 1)
        verifier_after = os.fstat(descriptor)
    except OSError as exc:
        raise RuntimeError("cannot read independent verifier source") from exc
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(verifier_before.st_mode)
        or verifier_before.st_size != _VERIFIER_SOURCE_BYTES
        or (
            verifier_before.st_dev,
            verifier_before.st_ino,
            verifier_before.st_size,
            verifier_before.st_mtime_ns,
            verifier_before.st_ctime_ns,
        )
        != (
            verifier_after.st_dev,
            verifier_after.st_ino,
            verifier_after.st_size,
            verifier_after.st_mtime_ns,
            verifier_after.st_ctime_ns,
        )
        or len(verifier_raw) != _VERIFIER_SOURCE_BYTES
        or hashlib.sha256(verifier_raw).hexdigest() != _VERIFIER_SOURCE_SHA256
    ):
        raise RuntimeError("independent verifier source identity drifted")
    if _VERIFIER_MODULE_NAME in sys.modules:
        raise RuntimeError("independent verifier private module name is already loaded")
    specification = importlib.util.spec_from_file_location(
        _VERIFIER_MODULE_NAME, VERIFIER_PATH
    )
    if (
        specification is None
        or type(specification.loader) is not importlib.machinery.SourceFileLoader
        or specification.origin is None
        or Path(specification.origin).resolve(strict=True)
        != VERIFIER_PATH.resolve(strict=True)
        or specification.cached is None
        or not specification.cached.startswith(_PYCACHE_PREFIX + "/")
    ):
        raise RuntimeError("cannot create the independent verifier source loader")
    module = importlib.util.module_from_spec(specification)
    sys.modules[_VERIFIER_MODULE_NAME] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(_VERIFIER_MODULE_NAME, None)
        raise
    if _forbidden_runtime_modules():
        sys.modules.pop(_VERIFIER_MODULE_NAME, None)
        raise RuntimeError("independent verifier source load crossed its import boundary")
    return module


_verifier = _load_verifier_source()
LibraryOptimizerComparisonVerificationError = (
    _verifier.LibraryOptimizerComparisonVerificationError
)
canonical_verification_receipt_bytes = (
    _verifier.canonical_verification_receipt_bytes
)
load_and_verify_optimizer_comparison_pilot = (
    _verifier.load_and_verify_optimizer_comparison_pilot
)


SUGGESTED_OUTPUT = Path(
    "artifacts/peano-hydra/"
    "l0-optimizer-comparison-pilot-independent-verification-v1.json"
)


def _absolute(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("output path must be pathlib.Path")
    return Path(os.path.abspath(path))


def _safe_parent(path: Path) -> Path:
    absolute = _absolute(path)
    current = Path(absolute.anchor)
    try:
        for component in absolute.parent.parts[1:]:
            current = current / component
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise LibraryOptimizerComparisonVerificationError(
                    "receipt parent contains a link or non-directory component"
                )
        return current
    except LibraryOptimizerComparisonVerificationError:
        raise
    except OSError as exc:
        raise LibraryOptimizerComparisonVerificationError(
            "cannot inspect receipt parent"
        ) from exc


def _require_absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    except OSError as exc:
        raise LibraryOptimizerComparisonVerificationError(
            "cannot inspect receipt destination"
        ) from exc
    raise LibraryOptimizerComparisonVerificationError(
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
            raise LibraryOptimizerComparisonVerificationError(
                "published receipt identity differs"
            )
        temporary.unlink()
        temporary_name = None
        parent_descriptor = os.open(parent, os.O_RDONLY)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
    except (LibraryOptimizerComparisonVerificationError, OSError) as exc:
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
        if isinstance(exc, LibraryOptimizerComparisonVerificationError):
            raise
        raise LibraryOptimizerComparisonVerificationError(
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
            "independent A2.3a verifier ready; no verification or retained write "
            "requested",
            flush=True,
        )
        return
    receipt = load_and_verify_optimizer_comparison_pilot(
        args.candidate,
        args.producer_source_state,
        repository_root=ROOT,
    )
    raw = canonical_verification_receipt_bytes(receipt)
    _publish_create_only(args.output, raw)
    print(
        f"independent candidate verification: {receipt['theorem_count']} roots, "
        f"{receipt['aggregate']['kernel_accepted_artifact_count']} kernel-accepted "
        f"artifacts, root {receipt['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        main()
    except LibraryOptimizerComparisonVerificationError as exc:
        raise SystemExit(str(exc)) from None
