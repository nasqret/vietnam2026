"""Deterministically partition the Peano Lab pytest suite for CI.

The command-line interface uses a checked-in runtime profile.  The public
``partition_test_files`` API keeps its historical source-byte model when no
profile is supplied, which is useful for callers that do not have timing data.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence


RUNTIME_PROFILE_FORMAT = "peano-pytest-runtime-weights"
RUNTIME_PROFILE_VERSION = 1
RUNTIME_PROFILE_UNIT = "ms"
DEFAULT_RUNTIME_PROFILE = Path(__file__).with_name("ci_runtime_weights_v1.json")


class RuntimeProfileError(ValueError):
    """A runtime-weight profile is malformed or does not match the test tree."""


@dataclass(frozen=True)
class RuntimeProfile:
    """Measured weights for selected files plus a conservative fallback."""

    weights_ms: Mapping[Path, int]
    fallback_ms: int

    def weight_ms(self, path: Path) -> int:
        return self.weights_ms.get(path, self.fallback_ms)


def discover_test_files(root: Path) -> tuple[Path, ...]:
    """Return every pytest module below *root* in stable path order."""

    files = {
        path
        for pattern in ("test_*.py", "*_test.py")
        for path in root.rglob(pattern)
        if path.is_file()
    }
    return tuple(sorted(files))


def _object_without_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise RuntimeProfileError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def _require_exact_keys(
    value: object, expected: set[str], description: str
) -> dict[str, object]:
    if not isinstance(value, dict):
        raise RuntimeProfileError(f"{description} must be a JSON object")
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        extra = sorted(actual - expected)
        raise RuntimeProfileError(
            f"{description} has wrong keys (missing={missing}, extra={extra})"
        )
    return value


def _positive_integer(value: object, description: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise RuntimeProfileError(f"{description} must be a positive integer")
    return value


def _canonical_relative_path(value: object, description: str) -> PurePosixPath:
    if not isinstance(value, str) or not value:
        raise RuntimeProfileError(f"{description} must be a non-empty string")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value != path.as_posix()
        or any(part in ("", ".", "..") for part in path.parts)
        or "\\" in value
    ):
        raise RuntimeProfileError(
            f"{description} must be a canonical relative POSIX path: {value!r}"
        )
    name = path.name
    if path.suffix != ".py" or not (
        name.startswith("test_") or name.endswith("_test.py")
    ):
        raise RuntimeProfileError(f"{description} is not a pytest module: {value!r}")
    return path


def load_runtime_profile(
    profile_path: Path,
    tests_root: Path,
    files: Sequence[Path] | None = None,
) -> RuntimeProfile:
    """Load and validate a v1 profile against the current discovered test tree.

    Paths in the profile are canonical POSIX paths relative to ``tests_root``.
    A profile may omit files, which receive its positive fallback weight, but it
    may not retain entries for files that no longer exist.
    """

    try:
        payload = json.loads(
            profile_path.read_text(encoding="utf-8"),
            object_pairs_hook=_object_without_duplicate_keys,
        )
    except RuntimeProfileError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise RuntimeProfileError(
            f"cannot read runtime profile {profile_path}: {error}"
        ) from error

    document = _require_exact_keys(
        payload,
        {"format", "version", "unit", "fallback", "weights"},
        "runtime profile",
    )
    if document["format"] != RUNTIME_PROFILE_FORMAT:
        raise RuntimeProfileError(
            f"runtime profile format must be {RUNTIME_PROFILE_FORMAT!r}"
        )
    if (
        type(document["version"]) is not int
        or document["version"] != RUNTIME_PROFILE_VERSION
    ):
        raise RuntimeProfileError(
            f"runtime profile version must be {RUNTIME_PROFILE_VERSION}"
        )
    if document["unit"] != RUNTIME_PROFILE_UNIT:
        raise RuntimeProfileError(
            f"runtime profile unit must be {RUNTIME_PROFILE_UNIT!r}"
        )
    fallback_ms = _positive_integer(document["fallback"], "fallback")
    entries = document["weights"]
    if not isinstance(entries, list):
        raise RuntimeProfileError("weights must be a JSON array")

    discovered = tuple(files) if files is not None else discover_test_files(tests_root)
    root = tests_root.resolve()
    by_relative_path: dict[str, Path] = {}
    for file_path in discovered:
        try:
            relative = file_path.resolve().relative_to(root).as_posix()
        except ValueError as error:
            raise RuntimeProfileError(
                f"discovered test is outside tests root: {file_path}"
            ) from error
        if relative in by_relative_path:
            raise RuntimeProfileError(f"duplicate discovered test path: {relative!r}")
        by_relative_path[relative] = file_path

    weights_ms: dict[Path, int] = {}
    seen: set[str] = set()
    for index, raw_entry in enumerate(entries):
        entry = _require_exact_keys(
            raw_entry, {"path", "weight"}, f"weights[{index}]"
        )
        relative = _canonical_relative_path(
            entry["path"], f"weights[{index}].path"
        ).as_posix()
        if relative in seen:
            raise RuntimeProfileError(f"duplicate runtime-weight path: {relative!r}")
        seen.add(relative)
        if relative not in by_relative_path:
            raise RuntimeProfileError(f"stale runtime-weight path: {relative!r}")
        weights_ms[by_relative_path[relative]] = _positive_integer(
            entry["weight"], f"weight for {relative!r}"
        )

    return RuntimeProfile(weights_ms=weights_ms, fallback_ms=fallback_ms)


def partition_test_files(
    files: Sequence[Path],
    shard_count: int,
    runtime_profile: RuntimeProfile | None = None,
) -> tuple[tuple[Path, ...], ...]:
    """Place each test file in exactly one deterministic, balanced shard.

    Runtime profiles use deterministic longest-processing-time-first (LPT)
    scheduling.  Without a profile, source bytes remain the scheduling weight
    for backward compatibility.
    """

    if shard_count <= 0:
        raise ValueError("shard_count must be positive")

    def weight(path: Path) -> int:
        if runtime_profile is None:
            return path.stat().st_size
        return runtime_profile.weight_ms(path)

    buckets: list[list[Path]] = [[] for _ in range(shard_count)]
    modeled_loads = [0] * shard_count
    source_loads = [0] * shard_count
    ranked = sorted(files, key=lambda path: (-weight(path), path.as_posix()))
    for path in ranked:
        index = min(
            range(shard_count),
            key=lambda candidate: (
                modeled_loads[candidate],
                source_loads[candidate],
                len(buckets[candidate]),
                candidate,
            ),
        )
        buckets[index].append(path)
        modeled_loads[index] += weight(path)
        source_loads[index] += path.stat().st_size

    return tuple(tuple(sorted(bucket)) for bucket in buckets)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, required=True, help="total shard count")
    parser.add_argument("--index", type=int, required=True, help="zero-based shard index")
    parser.add_argument(
        "--tests-root",
        type=Path,
        default=Path("tests"),
        help="pytest module root (default: tests)",
    )
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument(
        "--runtime-profile",
        type=Path,
        default=DEFAULT_RUNTIME_PROFILE,
        help=f"runtime profile (default: {DEFAULT_RUNTIME_PROFILE.name})",
    )
    profiles.add_argument(
        "--no-runtime-profile",
        action="store_const",
        const=None,
        dest="runtime_profile",
        help="balance by source bytes instead of modeled runtime",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args, pytest_args = parser.parse_known_args(argv)
    if not 0 <= args.index < args.count:
        parser.error("--index must satisfy 0 <= index < count")
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]

    files = discover_test_files(args.tests_root)
    try:
        runtime_profile = (
            None
            if args.runtime_profile is None
            else load_runtime_profile(args.runtime_profile, args.tests_root, files)
        )
    except RuntimeProfileError as error:
        parser.error(str(error))
    selected = partition_test_files(files, args.count, runtime_profile)[args.index]
    if not selected:
        parser.error("selected shard contains no test files")

    total_bytes = sum(path.stat().st_size for path in selected)
    if runtime_profile is None:
        load_description = "source-byte model"
    else:
        total_modeled_ms = sum(runtime_profile.weight_ms(path) for path in selected)
        load_description = f"{total_modeled_ms} modeled ms"
    print(
        f"Peano pytest shard {args.index + 1}/{args.count}: "
        f"{len(selected)} files, {load_description}, {total_bytes} source bytes",
        flush=True,
    )
    for path in selected:
        print(f"  {path}", flush=True)

    import pytest

    options = list(pytest_args) if pytest_args else ["-q", "--durations=20"]
    return int(pytest.main([*options, *(str(path) for path in selected)]))


if __name__ == "__main__":
    raise SystemExit(main())
