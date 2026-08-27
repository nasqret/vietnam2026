#!/usr/bin/env python3
"""Publish the unchanged v27 proofs with separately authenticated v28 authority.

The original v27 publisher, tests, assets, and output remain byte-for-byte
historical artifacts. A bounded, hash-authenticated projection lets those
original tests replay against their original atlas, without mocking either
kernel. This successor writes a distinct current-publication directory.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
from pathlib import Path
import subprocess
import tempfile
from typing import Any, Iterator, Sequence
import zlib

import build_constructive_second_wave_explorer as historical
import build_constructive_lower_layer_explorer as current


REPO = Path(__file__).resolve().parents[1]
OUTPUT = REPO / "book/_static/constructive-second-wave-explorer-v28"
PROJECTION = REPO / "research/arithmetic-library/artifacts/alpha-v27-campaign-projection-v1.json"
PROJECTION_SHA256 = "e569978514ce1ae0e2e12c3195d65eb7db531c0f3d22cfb2550a7f55d88159c9"
PROJECTION_FILES = {
    "campaign.json": (336823, "c8d781f420f52cedf5959e1240b7db183759de271819103accece8c7b4113ef4"),
    "definitions.json": (804139, "767a7af4649cc15f3927cfcc4db6183446722b0ef8192fb4af4fe8ae49d593e1"),
}
MAX_PROJECTION_BYTES = 256 * 1024


def historical_projection_bytes() -> dict[str, bytes]:
    """Recover only the two exact original files, with bounded decompression."""
    if PROJECTION.is_symlink() or not PROJECTION.is_file() or PROJECTION.stat().st_size > MAX_PROJECTION_BYTES:
        raise current.LowerLayerExplorerError("unsafe historical presentation projection")
    raw = PROJECTION.read_bytes()
    if len(raw) > MAX_PROJECTION_BYTES or current._digest(raw) != PROJECTION_SHA256:
        raise current.LowerLayerExplorerError("the exact historical presentation projection changed")
    archive = current._strict_json(raw)
    if (archive.get("schema") != "constructive-campaign-historical-projection-v1"
        or archive.get("alpha_version") != "v27"
        or archive.get("source_commit") != "ea90d1080a4ef59c4bd399c21097e9643aa786df"
        or archive.get("catalog_sha256") != current.PARENT_CATALOG_SHA256
        or len(archive.get("files", ())) != 2):
        raise current.LowerLayerExplorerError("historical projection provenance changed")
    result = {}
    for record in archive["files"]:
        name = record["name"]
        if name not in PROJECTION_FILES or name in result:
            raise current.LowerLayerExplorerError("unexpected or repeated historical projection file")
        size, digest = PROJECTION_FILES[name]
        if (record["bytes"] != size or record["sha256"] != digest
            or record["source_path"] != "book/_static/constructive-grand-campaign/" + name):
            raise current.LowerLayerExplorerError("historical projection identity changed")
        compressed = base64.b64decode(record["gzip_base64"], validate=True)
        decoder = zlib.decompressobj(16 + zlib.MAX_WBITS)
        data = decoder.decompress(compressed, size + 1)
        if (len(data) != size or not decoder.eof or decoder.unconsumed_tail or decoder.unused_data
            or current._digest(data) != digest):
            raise current.LowerLayerExplorerError("historical projection bytes or size changed")
        result[name] = data
    if result.keys() != PROJECTION_FILES.keys():
        raise current.LowerLayerExplorerError("historical projection is incomplete")
    return result


def historical_campaign() -> dict[str, Any]:
    return current._strict_json(historical_projection_bytes()["campaign.json"])


@contextmanager
def historical_presentation_context() -> Iterator[None]:
    """Select authenticated v27 atlas inputs, leaving all proof checks intact.

    This is solely an input fixture for the frozen publisher. It does not
    replace any proof, receipt, expected value, checker, output, or authority.
    All globals are restored even after a failed historical mutation test.
    """
    files = historical_projection_bytes()
    old_campaign, old_graph = historical.CAMPAIGN, historical.GLOBAL_DEFINITIONS
    with tempfile.TemporaryDirectory(prefix="peano-v27-atlas-") as directory:
        root = Path(directory)
        for name, data in files.items():
            (root / name).write_bytes(data)
        try:
            historical.CAMPAIGN = root / "campaign.json"
            historical.GLOBAL_DEFINITIONS = root / "definitions.json"
            yield
        finally:
            historical.CAMPAIGN, historical.GLOBAL_DEFINITIONS = old_campaign, old_graph


def _load_historical_inputs() -> dict[str, Any]:
    with historical_presentation_context():
        return historical._load_inputs()


def _audit_preserved_second_wave(current_inputs: dict[str, Any], old_inputs: dict[str, Any]) -> None:
    if old_inputs["catalog_sha256"] != current.PARENT_CATALOG_SHA256:
        raise current.LowerLayerExplorerError("the first-admission v27 catalog changed")
    for name, row in old_inputs["by_name"].items():
        if current._json(current_inputs["by_name"].get(name)) != current._json(row):
            raise current.LowerLayerExplorerError("current authority rewrote a historical theorem record")
    old_goals = {row["id"]: row for row in old_inputs["campaign"]["nodes"]}
    new_goals = {row["id"]: row for row in current_inputs["campaign"]["nodes"]}
    for family in historical.FAMILIES:
        for identifier in family.milestones:
            if current._json(new_goals[identifier]) != current._json(old_goals[identifier]):
                raise current.LowerLayerExplorerError("a historical second-wave milestone or receipt changed")


def build_files() -> dict[str, bytes]:
    inputs, old = current._load_inputs(), _load_historical_inputs()
    _audit_preserved_second_wave(inputs, old)
    view = {**inputs, "frontier": old["frontier"], "first_version": "v27",
            "first_catalog_sha256": old["catalog_sha256"], "bundle": old["bundle"],
            "schema": historical.SCHEMA}
    return current.render_files(
        view, historical.FAMILIES, package_slug="constructive-second-wave-explorer-v28",
        title="Seven completed second-wave targets",
        lede="The same 422 exact v27 proofs, now displayed under independently authenticated v28 checked-use authority. First admission remains v27.",
        scope="The seven named second-wave targets remain complete, with their original exact scope limits. Separate lower-layer Gaussian and Eisenstein division proofs are linked through the full campaign atlas; further factorization, prime-classification, Pell, and lattice targets remain distinct.",
        receipt_name="alpha-v27-second-wave-receipt.md",
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--check-historical", action="store_true",
                        help="replay the frozen v27 generator against its exact archived atlas and original output")
    arguments = parser.parse_args(argv)
    try:
        if arguments.check_historical:
            with historical_presentation_context():
                return historical.main(["--check"])
        files = build_files()
        current.write_or_check(files, arguments.output, check=arguments.check)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"second-wave v28 publication: FAIL: {error}")
        return 1
    print(f"second-wave v28 publication: PASS ({len(files)} files; unchanged v27 first admission)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
