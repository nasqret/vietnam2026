#!/usr/bin/env python3
"""Independently verify the additive, body-only Lagrange/Lucas Alpha-v13 release.

The default audit checks every sealed source/RFC/test binding and all 240 real
recorded body receipts, then independently replays both flagship bodies.
``--replay-bodies`` additionally refreshes every receipt in 25 bounded,
isolated per-factory subprocesses.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as builder  # noqa: E402
from peano_lab.library import editions_v12 as v12  # noqa: E402
from peano_lab.library import editions_v13 as v13  # noqa: E402
from peano_lab.library.alpha_enrollment_v13 import (  # noqa: E402
    FOUR_SQUARE_V13_EXPECTED_COUNT,
    FRONTIER_V13_BODY_ENROLLMENT_MANIFEST,
    FRONTIER_V13_EXPECTED_COUNT,
    FRONTIER_V13_EXPECTED_NAMES,
    FRONTIER_V13_EXPECTED_NAMES_SHA256,
    FRONTIER_V13_ROOT_NAMES,
    FRONTIER_V13_ROOT_STATEMENT_SHA256,
    LUCAS_V13_EXPECTED_COUNT,
    alpha_v13_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402


def _fail(message: str) -> None:
    raise ValueError(f"Alpha-v13 verification failed: {message}")


def _load(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"cannot read {path}: {error}")
    if type(payload) is not dict:
        _fail(f"{path} must contain a JSON object")
    return payload


@lru_cache(maxsize=None)
def _document_digest(path: str) -> str:
    try:
        payload = (ROOT / path).read_bytes()
    except OSError as error:
        _fail(f"cannot read evidence source {path}: {error}")
    return sha256(payload).hexdigest()


def _receipt_ok(receipt: object, spec: object, *, name: str) -> dict[str, object]:
    if type(receipt) is not dict:
        _fail(f"theorem {name!r} has no actual dependency-curried receipt")
    expected = {
        "name": name,
        "dependency_count": len(spec.dependencies),
        "command_count": len(spec.script),
        "dne_command_count": 0,
        "status": "kernel_checked_dependency_curried_body",
    }
    if any(receipt.get(key) != value for key, value in expected.items()):
        _fail(f"theorem {name!r} has an inconsistent body receipt")
    for key in ("proof_nodes", "proof_depth", "proof_objects", "proof_edges"):
        if not isinstance(receipt.get(key), int):
            _fail(f"theorem {name!r} has nonnumeric proof metric {key!r}")
    if receipt["proof_nodes"] <= 0 or receipt["proof_objects"] <= 0:
        _fail(f"theorem {name!r} has no actual proof object")
    return receipt


def _verify_frontier_rows(
    rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
) -> dict[str, dict[str, object]]:
    enrollment = alpha_v13_enrollment()
    specs = {spec.name: spec for spec in enrollment.frontier_specs}
    receipts: dict[str, dict[str, object]] = {}
    available = {entry.spec.name for entry in v12.ALPHA_ENTRIES}
    if tuple(row.get("name") for row in rows) != FRONTIER_V13_EXPECTED_NAMES:
        _fail("exact minimal topological frontier order changed")
    for offset, row in enumerate(rows):
        name = str(row.get("name"))
        spec = specs[name]
        if (
            row.get("enrollment_index") != builder.EXPECTED_PARENT_COUNT + offset
            or row.get("body_checked") is not True
            or row.get("checked_use") is not False
            or row.get("empty_context_closure") is not None
            or row.get("evidence_status") != "body_checked"
            or row.get("membership") != "alpha_only"
            or row.get("enrollment_origin") != "ha"
            or row.get("provenance") != ["ha"]
            or row.get("proof_tag") is not None
        ):
            _fail(f"theorem {name!r} crossed the body-only evidence boundary")
        if (
            row.get("statement") != spec.statement
            or row.get("dependencies") != list(spec.dependencies)
            or row.get("script") != list(spec.script)
            or row.get("summary") != spec.summary
            or row.get("statement_sha256") != builder._digest(spec.statement)
            or row.get("dependencies_sha256")
            != builder._digest("\n".join(spec.dependencies) + "\n")
            or row.get("script_sha256")
            != builder._digest("\n".join(spec.script) + "\n")
            or row.get("summary_sha256") != builder._digest(spec.summary)
            or row.get("logical_spec_sha256") != base._logical_spec_sha256(spec)
        ):
            _fail(f"theorem {name!r} changed its exact source specification")
        if not set(spec.dependencies) <= available:
            _fail(f"theorem {name!r} has a missing or forward dependency")
        if any("DNE" in command for command in spec.script):
            _fail(f"theorem {name!r} introduced a nonconstructive DNE command")
        available.add(name)

        campaign = enrollment.campaign_by_name[name].value
        if row.get("frontier_campaign") != campaign:
            _fail(f"theorem {name!r} changed its campaign partition")
        source_path = enrollment.source_by_name[name]
        test_path = enrollment.test_by_name[name]
        rfc_path = enrollment.rfc_by_name[name]
        source = row.get("source")
        if (
            type(source) is not dict
            or source.get("kind") != "candidate_module"
            or source.get("path") != source_path
            or source.get("sha256") != _document_digest(source_path)
        ):
            _fail(f"theorem {name!r} changed its exact candidate source binding")
        links = row.get("evidence_links")
        if type(links) is not list or len(links) != 4:
            _fail(f"theorem {name!r} lost its source/test/RFC/parent evidence links")
        expected_links = (source_path, test_path, rfc_path, builder._repository_path(builder.PARENT_ALPHA))
        for link, expected_path in zip(links, expected_links, strict=True):
            if (
                type(link) is not dict
                or link.get("path") != expected_path
                or link.get("document_sha256") != _document_digest(expected_path)
                or expected_path not in documents
                or documents[expected_path].get("sha256") != link.get("document_sha256")
            ):
                _fail(f"theorem {name!r} has an invalid evidence link {expected_path!r}")

        receipt = _receipt_ok(row.get("body_receipt"), spec, name=name)
        receipts[name] = receipt
        bundle = {
            "body_receipt_sha256": builder._digest(builder._compact(receipt)),
            "campaign": campaign,
            "dependencies_sha256": row["dependencies_sha256"],
            "enrollment_origin": "ha",
            "logical_spec_sha256": row["logical_spec_sha256"],
            "name": name,
            "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
            "rfc_sha256": _document_digest(rfc_path),
            "source_sha256": _document_digest(source_path),
            "statement_sha256": row["statement_sha256"],
            "test_sha256": _document_digest(test_path),
        }
        if row.get("frontier_v13_evidence_bundle_sha256") != builder._digest(
            builder._compact(bundle)
        ):
            _fail(f"theorem {name!r} has an invalid actual-proof evidence bundle")
    return receipts


def verify(*, replay_bodies: bool = False) -> None:
    """Audit v13 parent preservation, all body receipts, metadata, and roots."""

    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v13 artifact schemas changed")
    rows = catalog.get("theorems")
    if (
        type(rows) is not list
        or len(rows) != builder.EXPECTED_ALPHA_COUNT
        or catalog.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or metrics.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v13 theorem count changed")
    if rows[: builder.EXPECTED_PARENT_COUNT] != parent.get("theorems"):
        _fail("Alpha-v13 no longer preserves the exact 1,303-row v12 ledger")
    if (
        catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or catalog.get("edge_count") != builder.EXPECTED_EDGE_COUNT
        or catalog.get("layer_count") != builder.EXPECTED_LAYER_COUNT
        or catalog.get("edition_identity_sha256") != v13.ALPHA_V13_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != v13.ALPHA_V13_ENROLLMENT_SHA256
    ):
        _fail("Alpha-v13 runtime counts, Stable authority, or topology changed")
    if catalog.get("frontier_v13_campaign_counts") != {
        "four_square": FOUR_SQUARE_V13_EXPECTED_COUNT,
        "lucas": LUCAS_V13_EXPECTED_COUNT,
    }:
        _fail("Alpha-v13 exact 196+44 campaign partition changed")
    if catalog.get("frontier_v13_ordered_names_sha256") != FRONTIER_V13_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v13 ordered minimal-closure hash changed")
    if catalog.get("frontier_v13_roots") != dict(FRONTIER_V13_ROOT_STATEMENT_SHA256):
        _fail("Alpha-v13 flagship theorem identities changed")
    if Counter(row.get("evidence_status") for row in rows) != Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=972,
        pending_layered_closure=1,
    ):
        _fail("Alpha-v13 evidence counts changed")
    if (
        catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
        or catalog.get("ordered_enrollment_root_sha256")
        != base._ordered_root(v13.ALPHA_ENTRIES, include_origin=True)
        or catalog.get("ordered_spec_root_sha256")
        != base._ordered_root(v13.ALPHA_ENTRIES, include_origin=False)
    ):
        _fail("Alpha-v13 ordered evidence, membership, or theorem roots changed")

    document_rows = catalog.get("evidence_documents")
    if type(document_rows) is not list:
        _fail("Alpha-v13 evidence-document inventory is missing")
    documents = {
        str(document.get("path")): document
        for document in document_rows
        if type(document) is dict
    }
    for path in builder.CONTROL_DOCUMENTS:
        document = documents.get(path)
        if document is None or document.get("sha256") != _document_digest(path):
            _fail(f"Alpha-v13 control document changed: {path}")
    receipts = _verify_frontier_rows(rows[builder.EXPECTED_PARENT_COUNT :], documents)

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v13.ALPHA_V13_IDENTITY_SHA256
        or metrics.get("ordered_enrollment_root_sha256")
        != v13.ALPHA_V13_ENROLLMENT_SHA256
        or metrics.get("dependency_graph", {}).get("declared_edge_count")
        != builder.EXPECTED_EDGE_COUNT
        or metrics.get("dependency_graph", {}).get("layer_count")
        != builder.EXPECTED_LAYER_COUNT
    ):
        _fail("Alpha-v13 metric, graph, or catalog digest changed")
    if (
        "scripts/build_peano_library_channels_v13.py" not in graph
        or any(name not in graph for name in FRONTIER_V13_ROOT_NAMES)
    ):
        _fail("Alpha-v13 dependency graph lost generator or flagship nodes")

    parent_channels = _load(builder.PARENT_CHANNELS)
    actual_channels = channels.get("channels")
    if type(actual_channels) is not dict:
        _fail("Alpha-v13 channel pointers are missing")
    if (
        channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != parent_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
    ):
        _fail("Alpha-v13 modified the sealed Stable pointer or default channel")
    alpha_channel = actual_channels.get("alpha")
    if (
        type(alpha_channel) is not dict
        or alpha_channel.get("artifact_sha256") != catalog_hash
        or alpha_channel.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or alpha_channel.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or alpha_channel.get("edition_identity_sha256") != v13.ALPHA_V13_IDENTITY_SHA256
    ):
        _fail("Alpha-v13 alpha channel pointer changed")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha_channel.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v13 alpha-channel {key} pointer digest changed")

    core = {spec.name: spec for spec in v13.ALPHA_SPECS}
    for name in FRONTIER_V13_ROOT_NAMES:
        actual, = replay_candidate_bodies((core[name],), core=core)
        recorded = receipts[name]
        if any(recorded.get(key) != value for key, value in asdict(actual).items()):
            _fail(f"Alpha-v13 actual independently replayed root receipt changed: {name}")
    if replay_bodies:
        actual_receipts = builder._fresh_receipts()
        if actual_receipts != receipts:
            _fail("Alpha-v13 fresh isolated kernel-body receipts changed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replay-bodies",
        action="store_true",
        help="independently refresh all 240 receipts in 25 isolated factory processes",
    )
    arguments = parser.parse_args(argv)
    verify(replay_bodies=arguments.replay_bodies)
    print(
        "verified independent Alpha v13: "
        f"stable={builder.EXPECTED_STABLE_COUNT}, "
        f"alpha={builder.EXPECTED_ALPHA_COUNT}, "
        f"checked-use={builder.EXPECTED_CHECKED_USE_COUNT}, "
        f"body-receipts={FRONTIER_V13_EXPECTED_COUNT}, "
        f"sources={len(FRONTIER_V13_BODY_ENROLLMENT_MANIFEST)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
