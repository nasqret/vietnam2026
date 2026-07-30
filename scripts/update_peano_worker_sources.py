#!/usr/bin/env python3
"""Regenerate or verify Peano Lab's explicit browser Python-source list."""

from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / "peano-lab"
WORKER = LAB / "worker.js"
BEGIN = "const PY_FILES = [\n"
END = "];\n"


def _inventory() -> tuple[str, ...]:
    package_root = LAB / "py" / "peano_lab"
    paths = sorted(
        path.relative_to(LAB).as_posix()
        for path in package_root.rglob("*.py")
        if path.is_file()
    )
    driver = LAB / "py" / "driver.py"
    if not driver.is_file():
        raise SystemExit(f"missing browser driver: {driver}")
    paths.append(driver.relative_to(LAB).as_posix())
    return tuple(paths)


def _expected_block() -> str:
    rows = [BEGIN]
    rows.extend(f'  "{path}",\n' for path in _inventory())
    rows.append(END)
    return "".join(rows)


def _replace_block(source: str, replacement: str) -> tuple[str, str]:
    start = source.find(BEGIN)
    if start < 0:
        raise SystemExit("worker.js has no canonical PY_FILES block")
    finish = source.find(END, start + len(BEGIN))
    if finish < 0:
        raise SystemExit("worker.js has an unterminated PY_FILES block")
    finish += len(END)
    if source.find(BEGIN, finish) >= 0:
        raise SystemExit("worker.js has multiple PY_FILES blocks")
    return source[start:finish], source[:start] + replacement + source[finish:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if worker.js does not contain the exact sorted inventory",
    )
    args = parser.parse_args()

    source = WORKER.read_text(encoding="utf-8")
    expected = _expected_block()
    observed, updated = _replace_block(source, expected)
    if observed == expected:
        print(f"Peano worker source inventory verified: {len(_inventory())} files")
        return 0
    if args.check:
        print(
            "Peano worker source inventory is stale; regenerate it with "
            "scripts/update_peano_worker_sources.py"
        )
        return 1
    WORKER.write_text(updated, encoding="utf-8")
    print(f"Peano worker source inventory updated: {len(_inventory())} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
