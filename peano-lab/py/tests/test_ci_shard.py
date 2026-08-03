from pathlib import Path

import pytest

from ci_shard import discover_test_files, partition_test_files


def _sized_file(root: Path, name: str, size: int) -> Path:
    path = root / name
    path.write_bytes(b"x" * size)
    return path


def test_discovery_is_recursive_filtered_and_sorted(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    expected = (
        _sized_file(tmp_path, "test_a.py", 1),
        _sized_file(tmp_path, "suffix_test.py", 1),
        _sized_file(nested, "test_b.py", 1),
        _sized_file(nested, "test_double_test.py", 1),
    )
    _sized_file(tmp_path, "helper.py", 1)

    assert discover_test_files(tmp_path) == tuple(sorted(expected))


def test_partition_is_total_disjoint_deterministic_and_balanced(tmp_path: Path) -> None:
    files = tuple(
        _sized_file(tmp_path, f"test_{index}.py", size)
        for index, size in enumerate((101, 89, 61, 43, 31, 23, 17, 11, 7))
    )

    first = partition_test_files(files, 3)
    second = partition_test_files(tuple(reversed(files)), 3)

    assert first == second
    assert set().union(*(set(shard) for shard in first)) == set(files)
    assert sum(len(shard) for shard in first) == len(files)
    loads = [sum(path.stat().st_size for path in shard) for shard in first]
    assert max(loads) - min(loads) <= max(path.stat().st_size for path in files)


@pytest.mark.parametrize("shard_count", (0, -1))
def test_partition_rejects_nonpositive_shard_count(
    tmp_path: Path, shard_count: int
) -> None:
    with pytest.raises(ValueError, match="positive"):
        partition_test_files((_sized_file(tmp_path, "test_a.py", 1),), shard_count)
