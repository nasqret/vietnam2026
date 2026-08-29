#!/usr/bin/env python3
"""Freshly verify and publish 126 research proofs without library promotion."""

from __future__ import annotations

import argparse
from importlib import import_module
from pathlib import Path
import resource
import signal
import sys

import constructive_lower_tier_publication_adapter as adapter
from build_constructive_bottom_layer_publication import authoring_rss_bytes


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "book/_static/constructive-lower-tier-publication"
LOCAL_SOURCE_PINS = {
    "build_constructive_lower_tier_explorer.py": "05c34365a53f5ae9d6bd32a1fe052cf260d6b85931a95a20cc2ca72c74945367",
    "constructive_bottom_layer_explorer_renderer.py": "1c3f07b6e7c9251dd16da8dc6cf30c3cbbcba8f40ffb0b2990ad8f5537c2b6f5",
    "constructive_lower_tier_defined_adapter.py": "14f0cd07bd41768b2cb12417b1e774aa34002af88ff5d5e8c902ae9081384615",
}


def _local_builder():
    for name, expected in LOCAL_SOURCE_PINS.items():
        path = ROOT / "scripts" / name
        if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size < 1024 * 1024:
            raise adapter.PublicCheckpointError("unsafe frozen lower-tier rendering source")
        adapter.read_pinned(path, path.stat().st_size, expected)
    return import_module("build_constructive_lower_tier_explorer")


def build_files():
    local = _local_builder()
    files = local.build_files()  # actual original-HA and compiled Lean checks
    local.model.write_or_check(files, output=local.OUTPUT, check=True)  # frozen local copy is read-only
    return adapter.adapt_files(files)


def write_or_check(files, *, output: Path = OUTPUT, check: bool = False):
    _local_builder().model.write_or_check(files, output=output, check=check)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    try:
        files = build_files()
        authoring_rss_bytes()
        write_or_check(files, check=args.check)
        peak = authoring_rss_bytes()
    except (ValueError, OSError, RuntimeError) as error:
        print(f"Lower-tier publication refused: {error}", file=sys.stderr)
        return 1
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} public files; "
          "126 HA/independent-Lean verified theorems; no Alpha/Stable admission.")
    print(f"Authoring RSS ceiling PASS: {peak} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
