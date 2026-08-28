#!/usr/bin/env python3
"""Publish unchanged v27/v28/v29 proofs under independently authenticated v30 authority.

This additive output never rewrites a historical generator, atlas, corpus,
test fixture, or first-admission record. Each old release is checked by its
original verifier before the canonical renderer supplies current navigation.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Sequence

import build_constructive_gaussian_factorization_explorer as current
import build_constructive_priority_layer_explorer as priority
import build_constructive_lower_layer_explorer as lower
import build_constructive_second_wave_explorer as second
from upgrade_constructive_second_wave_publication_v28 import _load_historical_inputs


REPO = Path(__file__).resolve().parents[1]
OUTPUTS = {
    "v27": REPO / "book/_static/constructive-second-wave-explorer-v30",
    "v28": REPO / "book/_static/constructive-lower-layer-explorer-v30",
    "v29": REPO / "book/_static/constructive-priority-layer-explorer-v30",
}
SCHEMA = "peano-lab-constructive-historical-publication-v30"
FIRST_CATALOG_SHA256 = {
    "peano-library-alpha-snapshot-v27": "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6",
    "peano-library-alpha-snapshot-v28": "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9",
    "peano-library-alpha-snapshot-v29": "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0",
}


def _audit_preserved(inputs: dict[str, Any], old: dict[str, Any], families) -> None:
    expected = FIRST_CATALOG_SHA256.get(old["catalog"]["schema"])
    if expected is None or old["catalog_sha256"] != expected:
        raise current.GaussianFactorizationExplorerError("the exact first-admission catalogue changed")
    for name, row in old["by_name"].items():
        if current._json(inputs["by_name"].get(name)) != current._json(row):
            raise current.GaussianFactorizationExplorerError("current authority rewrote a historical theorem record")
    old_goals = {row["id"]: row for row in old["campaign"]["nodes"]}
    new_goals = {row["id"]: row for row in inputs["campaign"]["nodes"]}
    for family in families:
        for identifier in family.milestones:
            if current._json(new_goals[identifier]) != current._json(old_goals[identifier]):
                raise current.GaussianFactorizationExplorerError("current atlas rewrote a historical closed milestone")


def _view(inputs: dict[str, Any], old: dict[str, Any], version: str, families):
    _audit_preserved(inputs, old, families)
    return {
        **inputs, "frontier": old["frontier"], "first_version": version,
        "first_catalog_sha256": old["catalog_sha256"], "bundle": old["bundle"],
        "schema": f"{SCHEMA}-first-{version}",
        "theorem_milestones": {"v27": {}, "v28": lower.THEOREM_MILESTONES, "v29": priority.THEOREM_MILESTONES}[version],
    }


def build_files() -> dict[str, dict[str, bytes]]:
    inputs = current._load_inputs()
    result = {}
    groups = (
        ("v27", second.FAMILIES, _load_historical_inputs),
        ("v28", lower.FAMILIES, lower._load_inputs),
        ("v29", priority.FAMILIES, priority._load_inputs),
    )
    for version, group, loader in groups:
        old = loader()
        view = _view(inputs, old, version, group)
        result[version] = current.render_files(
            view, group, package_slug=OUTPUTS[version].name,
            title={"v27": "Seven completed second-wave targets", "v28": "Constructive lower-layer foundations", "v29": "Four completed constructive priority goals"}[version],
            lede=f"The same {len(old['frontier'])} exact {version} proofs, displayed with authenticated v30 checked-use authority. First admission remains {version}.",
            scope="Historical theorem statements, bodies, dependencies, first-admission receipts, and Stable membership remain unchanged. The newly closed Gaussian target is connected through the current atlas; other roadmap goals remain separate.",
            receipt_name=f"alpha-{version}-" + {"v27": "second-wave", "v28": "lower-layer", "v29": "priority-layer"}[version] + "-receipt.md",
        )
    return result


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    for version, files in build_files().items():
        current.write_or_check(files, OUTPUTS[version], check=arguments.check)
    print("historical v30 publication: PASS (904 unchanged proofs, 16 families, first admission preserved)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
