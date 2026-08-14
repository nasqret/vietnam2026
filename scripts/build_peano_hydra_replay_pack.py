#!/usr/bin/env python3
"""Build or isolated-replay the candidate Peano Hydra L0 artifact pack."""

from __future__ import annotations

import argparse
import importlib.abc
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"

DEFAULT_OUTPUT = ROOT / "artifacts" / "peano-hydra" / "l0-replay-candidate-v1"
DEFAULT_PACK_ID = "authoring-l0-replay-candidate-v1"
REPLAY_MODULE_PATH = ROOT / "training" / "peano_hydra" / "library_replay_pack.py"
FORBIDDEN_IMPORT_PREFIXES = (
    "peano_lab.library",
    "peano_lab.engine",
    "peano_lab.ui",
    "training",
    "torch",
    "transformers",
)
_REPO_PYCACHE_WAS_FRESH = False


class _ForbiddenReplayImport(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path, target=None):
        if any(
            fullname == prefix or fullname.startswith(prefix + ".")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        ):
            raise ModuleNotFoundError(
                f"isolated replay forbids importing {fullname!r}"
            )
        return None


def _progress(message: str) -> None:
    print(message, flush=True)


def _configure_build_paths() -> None:
    for path in (str(PY_ROOT), str(ROOT)):
        while path in sys.path:
            sys.path.remove(path)
    sys.path[:0] = [str(PY_ROOT), str(ROOT)]


def _configure_verify_paths() -> None:
    global _REPO_PYCACHE_WAS_FRESH
    if not sys.flags.isolated or not sys.flags.no_site or not sys.pycache_prefix:
        raise RuntimeError(
            "isolated replay requires python -I -S -X pycache_prefix=<fresh-dir>"
        )
    cache_root = Path(sys.pycache_prefix).resolve(strict=False)
    repository_cache = cache_root.joinpath(*ROOT.resolve().parts[1:])
    if repository_cache.exists():
        raise RuntimeError("isolated replay requires a fresh repository pycache")
    _REPO_PYCACHE_WAS_FRESH = True
    sys.dont_write_bytecode = True
    for path in (str(PY_ROOT), str(ROOT)):
        while path in sys.path:
            sys.path.remove(path)
    # Under -I -S, the existing entries are Python's standard-library paths.
    # The verifier needs only the exact Peano package root; the repository root
    # is intentionally absent so unrelated untracked modules cannot execute.
    sys.path.append(str(PY_ROOT))


def _portable_path_parts(path: Path) -> tuple[str, ...]:
    # Conservatively reject aliases on both case-sensitive and case-insensitive
    # hosts. APFS may also normalize Unicode names, so normalize each component
    # before case-folding it.
    return tuple(unicodedata.normalize("NFC", part).casefold() for part in path.parts)


def _same_or_descendant(candidate: Path, root: Path) -> bool:
    candidate_parts = _portable_path_parts(candidate)
    root_parts = _portable_path_parts(root)
    return (
        len(candidate_parts) >= len(root_parts)
        and candidate_parts[: len(root_parts)] == root_parts
    )


def _validate_report_destination(output: Path, report: Path | None) -> None:
    if report is None:
        return
    lexical_output = Path(os.path.abspath(output))
    lexical_report = Path(os.path.abspath(report))
    resolved_output = output.resolve(strict=False)
    resolved_report = report.resolve(strict=False)
    if _same_or_descendant(lexical_report, lexical_output) or _same_or_descendant(
        resolved_report, resolved_output
    ):
        raise RuntimeError("verification report must be outside the replay pack")


def _write_report_atomic(path: Path, report: dict[str, object]) -> None:
    raw = (
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    parent = path.parent
    if not parent.is_dir():
        raise RuntimeError("verification report parent must be an existing directory")
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=parent,
            delete=False,
        ) as stream:
            temporary_name = stream.name
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary_name, 0o644)
        os.replace(temporary_name, path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def _assert_kernel_module_origins() -> None:
    expected = {
        "peano_lab": PY_ROOT / "peano_lab/__init__.py",
        "peano_lab.kernel": PY_ROOT / "peano_lab/kernel/__init__.py",
        "peano_lab.kernel.artifact_codec": (
            PY_ROOT / "peano_lab/kernel/artifact_codec.py"
        ),
        "peano_lab.kernel.checker": PY_ROOT / "peano_lab/kernel/checker.py",
        "peano_lab.kernel.formulas": PY_ROOT / "peano_lab/kernel/formulas.py",
        "peano_lab.kernel.proofs": PY_ROOT / "peano_lab/kernel/proofs.py",
        "peano_lab.kernel.subst": PY_ROOT / "peano_lab/kernel/subst.py",
        "peano_lab.kernel.terms": PY_ROOT / "peano_lab/kernel/terms.py",
    }
    for name, path in expected.items():
        module = sys.modules.get(name)
        source = None if module is None else getattr(module, "__file__", None)
        if source is None or Path(source).resolve(strict=False) != path.resolve():
            raise RuntimeError(f"isolated replay loaded {name!r} from the wrong path")


def _isolated_replay_module():
    already_loaded = sorted(
        name
        for name in sys.modules
        if any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        )
    )
    if already_loaded:
        raise RuntimeError(
            "isolated replay began with forbidden modules loaded: "
            + ", ".join(already_loaded)
        )
    guard = _ForbiddenReplayImport()
    sys.meta_path.insert(0, guard)
    spec = importlib.util.spec_from_file_location(
        "peano_hydra_library_replay_pack_isolated", REPLAY_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load the isolated replay-pack verifier")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _assert_kernel_module_origins()
    if tuple(module.FORBIDDEN_REPLAY_IMPORT_PREFIXES) != FORBIDDEN_IMPORT_PREFIXES:
        raise RuntimeError("replay worker and verifier import policies differ")
    return module


def _worker_isolation_receipt(replay) -> dict[str, object]:
    forbidden_loaded = sorted(
        name
        for name in sys.modules
        if any(
            name == prefix or name.startswith(prefix + ".")
            for prefix in FORBIDDEN_IMPORT_PREFIXES
        )
    )
    if forbidden_loaded:
        raise RuntimeError(
            "isolated replay loaded forbidden modules: "
            + ", ".join(forbidden_loaded)
        )
    return {
        "forbidden_import_prefixes": list(FORBIDDEN_IMPORT_PREFIXES),
        "forbidden_modules_loaded": forbidden_loaded,
        "format": replay.REPLAY_WORKER_ISOLATION_FORMAT,
        "fresh_repo_pycache": _REPO_PYCACHE_WAS_FRESH,
        "guard": "meta-path-reject",
        "python_isolated_mode": bool(sys.flags.isolated),
        "python_no_site": bool(sys.flags.no_site),
        "v": replay.REPLAY_WORKER_ISOLATION_VERSION,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--pack-id", default=DEFAULT_PACK_ID)
    parser.add_argument(
        "--verify",
        action="store_true",
        help="stream-verify an existing pack without importing the living builder",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="optionally write the canonical verification report as JSON",
    )
    args = parser.parse_args()
    _validate_report_destination(args.output, args.report)

    if args.verify:
        _configure_verify_paths()
        replay = _isolated_replay_module()
        manifest, report = replay.load_and_verify_replay_pack(args.output)
        report = {**report, "worker_isolation": _worker_isolation_receipt(replay)}
    else:
        _configure_build_paths()
        from training.peano_hydra.library_replay_pack_builder import (
            build_live_replay_pack,
        )

        manifest, report = build_live_replay_pack(
            args.output,
            pack_id=args.pack_id,
            progress=_progress,
        )
    if args.report is not None:
        # Recheck after building or replaying: build mode publishes the output
        # directory during the operation, and path aliases must remain outside.
        _validate_report_destination(args.output, args.report)
        _write_report_atomic(args.report, report)
    print(
        f"{report['status']}: {report['kernel_checked_count']} theorems, "
        f"root {manifest['root_sha256']}",
        flush=True,
    )


if __name__ == "__main__":
    main()
