#!/usr/bin/env python3.12
"""Controlled no-default-write CLI for the A2.3e comparison producer."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types


ROOT = Path(__file__).resolve().parents[1]
LEXICAL_SELF = ROOT / "scripts/build_peano_hydra_library_pilot_optimized_construction_comparison.py"
PRODUCER_PATH = (
    ROOT
    / "training/peano_hydra/library_pilot_optimized_construction_comparison.py"
)
PRODUCER_BYTES = 33_466
PRODUCER_SHA256 = (
    "b7242039928552c1a38b23ac555d8998caa74bf4e9c7d68830cc53a8001acfd4"
)
CONFIRM_TOKEN = "PEANO-HYDRA-A23E-FIXED-COMPARISON"
MAX_SOURCE_BYTES = 131_072
MAX_OUTPUT_BYTES = 1_048_576
PYTHON_ENV_KEYS = (
    "PYTHONCASEOK",
    "PYTHONHOME",
    "PYTHONINSPECT",
    "PYTHONOPTIMIZE",
    "PYTHONPATH",
    "PYTHONSTARTUP",
    "PYTHONUSERBASE",
    "PYTHONWARNINGS",
)


class ComparisonCliError(RuntimeError):
    pass


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _lexical_absolute(path: Path) -> Path:
    value = Path(path)
    if not value.is_absolute():
        value = Path.cwd() / value
    return Path(os.path.abspath(os.fspath(value)))


def _identity(value: os.stat_result) -> tuple[int, int, int, int, int]:
    return (
        value.st_dev,
        value.st_ino,
        value.st_size,
        value.st_mtime_ns,
        value.st_ctime_ns,
    )


def _require_directory_chain(path: Path, *, label: str) -> None:
    absolute = _lexical_absolute(path)
    current = Path(absolute.anchor)
    try:
        for part in absolute.parts[1:]:
            current = current / part
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise ComparisonCliError(
                    f"{label} contains a symlink or non-directory"
                )
    except ComparisonCliError:
        raise
    except OSError as exc:
        raise ComparisonCliError(f"cannot inspect {label}") from exc


def _read_regular(path: Path, *, label: str, limit: int) -> bytes:
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label=f"{label} ancestors")
    try:
        inspected = absolute.lstat()
    except OSError as exc:
        raise ComparisonCliError(f"cannot inspect {label}") from exc
    if stat.S_ISLNK(inspected.st_mode) or not stat.S_ISREG(inspected.st_mode):
        raise ComparisonCliError(f"{label} must be a non-symlink regular file")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        descriptor = os.open(absolute, flags)
    except OSError as exc:
        raise ComparisonCliError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size > limit
            or _identity(inspected) != _identity(before)
        ):
            raise ComparisonCliError(
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
            raise ComparisonCliError(f"{label} changed while read")
        return raw
    except OSError as exc:
        raise ComparisonCliError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)


def _require_runtime() -> None:
    if sys.implementation.name != "cpython" or sys.version_info[:2] != (3, 12):
        raise ComparisonCliError("exact CPython 3.12 is required")
    flags = sys.flags
    if (
        flags.dont_write_bytecode != 1
        or flags.safe_path != 1
        or flags.no_user_site != 1
        or flags.no_site != 1
        or flags.optimize != 0
        or flags.hash_randomization != 0
    ):
        raise ComparisonCliError("use CPython with -B -P -s -S and hash seed 0")
    if os.environ.get("PYTHONHASHSEED") != "0":
        raise ComparisonCliError("PYTHONHASHSEED must be exactly 0")
    present = [key for key in PYTHON_ENV_KEYS if key in os.environ]
    if present:
        raise ComparisonCliError(
            "Python injection environment keys must be absent: " + ",".join(present)
        )
    if Path.cwd() != ROOT:
        raise ComparisonCliError("current working directory must be repository root")
    if _lexical_absolute(Path(__file__)) != LEXICAL_SELF:
        raise ComparisonCliError("CLI lexical path differs")
    self_meta = LEXICAL_SELF.lstat()
    if stat.S_ISLNK(self_meta.st_mode) or not stat.S_ISREG(self_meta.st_mode):
        raise ComparisonCliError("CLI must be a non-symlink regular file")
    _require_directory_chain(LEXICAL_SELF.parent, label="CLI ancestors")


def _load_producer() -> types.ModuleType:
    raw = _read_regular(PRODUCER_PATH, label="producer source", limit=MAX_SOURCE_BYTES)
    if len(raw) != PRODUCER_BYTES or _sha256(raw) != PRODUCER_SHA256:
        raise ComparisonCliError("producer source identity drifted")
    before_modules = set(sys.modules)
    module = types.ModuleType("_peano_hydra_a23e_comparison_producer")
    module.__file__ = str(PRODUCER_PATH)
    module.__package__ = ""
    sys.modules[module.__name__] = module
    try:
        code = compile(raw, str(PRODUCER_PATH), "exec", dont_inherit=True)
        exec(code, module.__dict__)
        after_raw = _read_regular(
            PRODUCER_PATH, label="producer source after load", limit=MAX_SOURCE_BYTES
        )
        if after_raw != raw:
            raise ComparisonCliError("producer source changed during load")
        unexpected = [
            name
            for name in set(sys.modules) - before_modules
            if name.startswith("training") or name.startswith("peano_lab")
        ]
        if unexpected:
            raise ComparisonCliError("producer imported a forbidden repository module")
        return module
    except Exception:
        sys.modules.pop(module.__name__, None)
        raise


def _write_all(descriptor: int, raw: bytes) -> None:
    offset = 0
    while offset < len(raw):
        written = os.write(descriptor, raw[offset:])
        if written <= 0:
            raise ComparisonCliError("short output write")
        offset += written


def _create_only(path: Path, raw: bytes) -> None:
    if len(raw) > MAX_OUTPUT_BYTES:
        raise ComparisonCliError("output exceeds its byte bound")
    absolute = _lexical_absolute(path)
    _require_directory_chain(absolute.parent, label="output ancestors")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor: int | None = None
    owned_identity: tuple[int, int, int, int, int] | None = None
    try:
        descriptor = os.open(absolute, flags, 0o600)
        os.fchmod(descriptor, 0o644)
        _write_all(descriptor, raw)
        os.fsync(descriptor)
        metadata = os.fstat(descriptor)
        owned_identity = _identity(metadata)
        if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != 0o644:
            raise ComparisonCliError("created output has wrong type or mode")
        path_meta = absolute.lstat()
        if _identity(path_meta) != owned_identity:
            raise ComparisonCliError("created output pathname identity differs")
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
            descriptor = None
        if owned_identity is not None:
            try:
                if _identity(absolute.lstat()) == owned_identity:
                    absolute.unlink()
            except OSError:
                pass
        raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
    reread = _read_regular(absolute, label="created output", limit=MAX_OUTPUT_BYTES)
    if reread != raw or _identity(absolute.lstat()) != owned_identity:
        try:
            if _identity(absolute.lstat()) == owned_identity:
                absolute.unlink()
        except OSError:
            pass
        raise ComparisonCliError("created output failed authenticated reread")


def _description(module: types.ModuleType) -> bytes:
    schema = module.optimized_construction_comparison_schema_identity()
    value = {
        "campaign_executed": False,
        "default_action": "describe-only-no-write",
        "format": "peano-hydra-a23e-comparison-cli-description-v1",
        "global_best_claim": False,
        "id": "peano-hydra-a23e-comparison-cli-description-v1",
        "result_retained": False,
        "schema": schema,
        "scope": "one-root-four-retained-candidate-fixed-set-only",
        "theorem_scoped_construction_vector_audit_complete": False,
        "v": 1,
    }
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8") + b"\n"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--confirm")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--repository-root", type=Path, default=ROOT)
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        _require_runtime()
        args = _parser().parse_args(argv)
        if args.confirm is not None and not args.build:
            raise ComparisonCliError("--confirm is valid only with --build")
        if args.output is not None and not args.build:
            raise ComparisonCliError("--output is valid only with --build")
        module = _load_producer()
        if not args.build:
            sys.stdout.buffer.write(_description(module))
            return 0
        if args.confirm != CONFIRM_TOKEN:
            raise ComparisonCliError(
                f"--build requires --confirm {CONFIRM_TOKEN}"
            )
        root = _lexical_absolute(args.repository_root)
        document = module.build_pilot_optimized_construction_comparison(root)
        module.validate_pilot_optimized_construction_comparison(
            document, repository_root=root
        )
        raw = module.canonical_document_bytes(document)
        if args.output is None:
            sys.stdout.buffer.write(raw)
        else:
            _create_only(args.output, raw)
        return 0
    except (ComparisonCliError, OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
