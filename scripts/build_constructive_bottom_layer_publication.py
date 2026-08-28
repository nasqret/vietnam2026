#!/usr/bin/env python3
"""Publish four genuine research checkpoints without admitting a library row.

Build and --check both freshly execute the unchanged local builder's original
HA and independent compiled Lean verification. The subsequent public adapter
only changes delivery metadata, prose, and links. It never promotes a stored
receipt, changes a mathematical source, or modifies an old/local publication.
"""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path
import resource
import signal
import sys

import constructive_bottom_layer_publication_adapter as adapter


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "book/_static/constructive-bottom-layer-publication"
LOCAL_SOURCE_PINS = {
    "build_constructive_bottom_layer_explorer.py": "b643d93d0934dc624b6bc8dd7f83e29fb2daf96008d17a9acb7c39e05271a077",
    "constructive_bottom_layer_explorer_renderer.py": "1c3f07b6e7c9251dd16da8dc6cf30c3cbbcba8f40ffb0b2990ad8f5537c2b6f5",
}


def _local_builder():
    for name, expected in LOCAL_SOURCE_PINS.items():
        path = ROOT / "scripts" / name
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 1024 * 1024:
            raise adapter.PublicCheckpointError("unsafe frozen local rendering source")
        adapter.read_pinned(path, path.stat().st_size, expected)
    return import_module("build_constructive_bottom_layer_explorer")


def build_files() -> dict[str, bytes]:
    local = _local_builder()
    # Mandatory fresh real proof checks, including every inherited dependency.
    # Never substitute readback of the stored local checkpoint inventory.
    files = local.build_files()
    # Read-only exact validation also prevents accidental rewriting/drift of the
    # separately retained historical local snapshot during public packaging.
    local.write_or_check(files, check=True)
    return adapter.adapt_files(files)


def write_or_check(files: dict[str, bytes], *, output: Path = OUTPUT, check: bool = False) -> None:
    # The original writer bounds reads, rejects traversal/symlinks/unknown
    # files, and never silently removes anything. Only the new tree is passed.
    _local_builder().write_or_check(files, output=output, check=check)


def authoring_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    peak_bytes = peak if sys.platform == "darwin" else peak * 1024
    if peak_bytes > 1536 * 1024 * 1024:
        raise RuntimeError("the original 1536 MiB authoring RSS ceiling was exceeded")
    return peak_bytes


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fresh HA/Lean checks and exact public snapshot validation")
    args = parser.parse_args(argv)
    # Identical authoring ceilings to check_constructive_bottom_layers.py;
    # the kernel and the independent verifier retain all their own limits.
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    try:
        files = build_files()
        authoring_rss_bytes()  # refuse before writing an over-budget build
        write_or_check(files, check=args.check)
        peak_bytes = authoring_rss_bytes()
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Public research checkpoint publication refused: {error}", file=sys.stderr)
        return 1
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} public research-checkpoint files; "
          "170 original-HA/independent-Lean verified theorems; no Alpha/Stable admissions "
          "(Alpha v30 3222; Stable 432).")
    print(f"Authoring RSS ceiling PASS: {peak_bytes} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
