"""Deterministically partition the Peano Lab pytest suite for CI.

The partitioner greedily balances source bytes.  File size is not a perfect
runtime model, but it is stable, dependency-free, and substantially better
than putting the alphabetically adjacent proof-candidate modules on the same
runner.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Sequence


def discover_test_files(root: Path) -> tuple[Path, ...]:
    """Return every pytest module below *root* in stable path order."""

    files = {
        path
        for pattern in ("test_*.py", "*_test.py")
        for path in root.rglob(pattern)
        if path.is_file()
    }
    return tuple(sorted(files))


def partition_test_files(
    files: Sequence[Path], shard_count: int
) -> tuple[tuple[Path, ...], ...]:
    """Place each test file in exactly one deterministic, byte-balanced shard."""

    if shard_count <= 0:
        raise ValueError("shard_count must be positive")

    buckets: list[list[Path]] = [[] for _ in range(shard_count)]
    loads = [0] * shard_count
    ranked = sorted(files, key=lambda path: (-path.stat().st_size, path.as_posix()))
    for path in ranked:
        index = min(
            range(shard_count),
            key=lambda candidate: (
                loads[candidate],
                len(buckets[candidate]),
                candidate,
            ),
        )
        buckets[index].append(path)
        loads[index] += path.stat().st_size

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
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args, pytest_args = parser.parse_known_args(argv)
    if not 0 <= args.index < args.count:
        parser.error("--index must satisfy 0 <= index < count")
    if pytest_args[:1] == ["--"]:
        pytest_args = pytest_args[1:]

    files = discover_test_files(args.tests_root)
    selected = partition_test_files(files, args.count)[args.index]
    if not selected:
        parser.error("selected shard contains no test files")

    total_bytes = sum(path.stat().st_size for path in selected)
    print(
        f"Peano pytest shard {args.index + 1}/{args.count}: "
        f"{len(selected)} files, {total_bytes} source bytes",
        flush=True,
    )
    for path in selected:
        print(f"  {path}", flush=True)

    import pytest

    options = list(pytest_args) if pytest_args else ["-q", "--durations=20"]
    return int(pytest.main([*options, *(str(path) for path in selected)]))


if __name__ == "__main__":
    raise SystemExit(main())
