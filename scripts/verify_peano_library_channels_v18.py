#!/usr/bin/env python3
"""Independently verify all five genuine Alpha-v18 flagship proof campaigns."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v18 as builder
from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v17 as v17
from peano_lab.library import editions_v18 as v18


def _fail(message: str) -> None:
    raise ValueError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        result = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"cannot read {path}: {error}")
    if type(result) is not dict:
        _fail(f"{path} must contain a JSON object")
    return result


def _documents(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inventory = catalog.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v18 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if type(item) is not dict or type(item.get("path")) is not str:
            _fail("Alpha-v18 evidence-document inventory is malformed")
        if item["path"] in result:
            _fail(f"duplicate Alpha-v18 evidence document {item['path']!r}")
        result[item["path"]] = item
    for path in builder.CONTROL_DOCUMENTS:
        item = result.get(path)
        if item is None:
            _fail(f"missing Alpha-v18 actual-proof control document {path!r}")
        try:
            actual = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v18 actual-proof source {path!r}: {error}")
        if item.get("sha256") != sha256(actual).hexdigest():
            _fail(f"changed Alpha-v18 actual-proof control document {path!r}")
        if item.get("bytes") != len(actual):
            _fail(f"changed Alpha-v18 actual-proof byte count {path!r}")
    parent = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v18 lost its immutable sealed Alpha-v17 parent document")
    return result


def _verify_promotion(
    row: dict[str, Any],
    parent: dict[str, Any],
    *,
    label: str,
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> None:
    name = str(parent.get("name"))
    mutable = {
        "alpha_v18_promotion",
        "checked_use",
        "empty_context_closure",
        "evidence_links",
        "evidence_status",
    }
    if set(row) != set(parent) | {"alpha_v18_promotion"}:
        _fail(f"promoted theorem {name!r} changed its exact immutable field set")
    for key in set(parent).difference(mutable):
        if row.get(key) != parent[key]:
            _fail(f"promoted theorem {name!r} changed immutable parent field {key!r}")
    if (
        parent.get("membership") != "alpha_only"
        or parent.get("checked_use") is not False
        or parent.get("evidence_status") != "body_checked"
        or row.get("checked_use") is not True
        or row.get("evidence_status") != "alpha_closed"
    ):
        _fail(f"promoted theorem {name!r} crossed its allowed evidence boundary")

    campaign = builder.CAMPAIGNS[label]
    artifact_path = str(campaign["artifact"])
    receipt_path = str(campaign["receipt"])
    digest = documents[artifact_path]["sha256"]
    expected_transition = {
        "bundle_campaign": label,
        "bundle_node_id": node_id,
        "bundle_sha256": digest,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "parent_evidence_status": parent["evidence_status"],
        "parent_row_sha256": builder._digest(builder._compact(parent)),
    }
    if row.get("alpha_v18_promotion") != expected_transition:
        _fail(f"promoted theorem {name!r} changed its immutable parent transition")

    body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
    expected_closure = {
        "body_proof_depth": body_depth,
        "body_proof_nodes": body_nodes,
        "bundle_campaign": label,
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count,
        "bundle_node_id": node_id,
        "bundle_path": artifact_path,
        "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": digest,
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": parent["statement_sha256"],
        "status": "checked",
    }
    if row.get("empty_context_closure") != expected_closure:
        _fail(f"promoted theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    historical = parent.get("evidence_links")
    if (
        type(links) is not list
        or type(historical) is not list
        or links[: len(historical)] != historical
        or len(links) != len(historical) + 3
    ):
        _fail(f"promoted theorem {name!r} changed its immutable historical links")
    expected_links = (
        {
            "document_sha256": digest,
            "kind": f"{label}_self_contained_constructive_proof_bundle",
            "path": artifact_path,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[receipt_path]["sha256"],
            "kind": f"{label}_ordinary_kernel_and_compiled_lean_receipt",
            "path": receipt_path,
            "role": "original_kernel_and_independent_compiled_lean_verification",
            "selector": "document",
        },
        {
            "document_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v17_parent",
            "path": builder._repository_path(builder.PARENT_ALPHA),
            "role": "exact_immutable_pre_promotion_catalog_bytes",
            "selector": f"theorems[name={name}]",
        },
    )
    if tuple(links[len(historical) :]) != expected_links:
        _fail(f"promoted theorem {name!r} lost actual proof/receipt/parent links")


def _verify_rows(
    rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    bundles: dict[str, tuple[Any, Any, dict[str, int]]],
) -> None:
    if (
        type(rows) is not list
        or type(parent_rows) is not list
        or len(rows) != len(parent_rows)
        or len(rows) != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v18 changed its immutable complete 1,673-row parent ledger")
    promoted = frozenset(v18.FLAGSHIP_PROMOTED_NAMES)
    changed: list[str] = []
    owners: Counter[str] = Counter()
    for index, (row, parent) in enumerate(zip(rows, parent_rows, strict=True)):
        if type(row) is not dict or type(parent) is not dict:
            _fail(f"Alpha-v18 ledger row {index} is malformed")
        name = str(parent.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v18 changed immutable theorem order at index {index}")
        if name not in promoted:
            if row != parent:
                _fail(f"Alpha-v18 modified unrelated immutable parent row {name!r}")
            continue
        changed.append(name)
        label = v18._flagship_owner(name)
        bundle, receipt, positions = bundles[label]
        _verify_promotion(
            row,
            parent,
            label=label,
            node_id=positions[name],
            bundle=bundle,
            receipt=receipt,
            documents=documents,
        )
        owners[label] += 1
    if tuple(changed) != v18.FLAGSHIP_PROMOTED_NAMES:
        _fail("Alpha-v18 changed its exact ordered 673-theorem promotion scope")
    if owners != Counter(builder.EXPECTED_OWNER_COUNTS):
        _fail("Alpha-v18 changed exact five-bundle constructive ownership")
    if Counter(row.get("evidence_status") for row in rows) != Counter(
        builder.EXPECTED_EVIDENCE_COUNTS
    ):
        _fail("Alpha-v18 changed its checked/body-only evidence partition")
    checked = {str(row["name"]) for row in rows if row.get("checked_use") is True}
    if len(checked) != builder.EXPECTED_CHECKED_USE_COUNT:
        _fail("Alpha-v18 changed its exact checked-use authority count")
    for row in rows:
        if row["name"] in checked and not set(row["dependencies"]) <= checked:
            _fail(f"checked theorem {row['name']!r} has an unchecked dependency")
    if sum(len(row["dependencies"]) for row in rows if row["name"] in checked) != (
        v18.EXPECTED_ALPHA_V18_CHECKED_EDGE_COUNT
    ):
        _fail("Alpha-v18 changed its dependency-closed checked-use edge count")


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v18 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v18 artifact schemas changed")
    rows = catalog.get("theorems")
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or metrics.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or catalog.get("stable_count") != builder.EXPECTED_STABLE_COUNT
        or catalog.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or metrics.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or catalog.get("edge_count") != builder.EXPECTED_EDGE_COUNT
        or catalog.get("layer_count") != builder.EXPECTED_LAYER_COUNT
    ):
        _fail("Alpha-v18 counts, Stable authority, or frozen topology changed")
    if (
        catalog.get("edition_identity_sha256") != v18.ALPHA_V18_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != v18.ALPHA_V18_ENROLLMENT_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != parent.get("ordered_enrollment_root_sha256")
        or catalog.get("ordered_spec_root_sha256")
        != parent.get("ordered_spec_root_sha256")
        or catalog.get("membership_root_sha256")
        != parent.get("membership_root_sha256")
    ):
        _fail("Alpha-v18 changed immutable enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v17") != builder._parent_binding():
        _fail("Alpha-v18 lost exact sealed Alpha-v17 artifact provenance")

    documents = _documents(catalog)
    bundles = builder._checked_bundles()
    _verify_rows(rows, parent["theorems"], documents, bundles)
    promotion = builder._promotion_payload(bundles)
    if (
        catalog.get("alpha_v18_flagship_promotion") != promotion
        or metrics.get("alpha_v18_flagship_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
    ):
        _fail("Alpha-v18 changed its actual checked flagship promotion evidence")
    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    flagship = gates.get("five_constructive_flagships_full_dependency_closure", {})
    if (
        full.get("status") != "blocked"
        or full.get("checked") != 1_589
        or full.get("missing") != 84
        or full.get("required") != 1_673
        or flagship.get("status") != "passed"
        or flagship.get("promoted_count") != 673
        or tuple(flagship.get("campaign_order", [])) != v18.FLAGSHIP_BUNDLE_LABELS
    ):
        _fail("Alpha-v18 misrepresented its flagship or full-Alpha proof gates")
    accounting = metrics.get("checked_closure_metrics", {})
    shared = accounting.get("flagship_bundle_accounting", {})
    if (
        accounting.get("metric_bearing_theorem_count") != 1_589
        or accounting.get("missing_empty_context_metric_count") != 84
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        )
        != 1_019
        or shared.get("campaign_count") != 5
        or shared.get("promoted_checked_theorem_count") != 673
        or shared.get("campaigns") != promotion["campaigns"]
    ):
        _fail("Alpha-v18 misstated actual shared constructive proof evidence")

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v18.ALPHA_V18_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v18.py" not in graph
        or any(name not in graph for name in v18.FLAGSHIP_ROOT_NAMES)
    ):
        _fail("Alpha-v18 catalog, dependency graph, or metrics artifact changed")

    actual_channels = channels.get("channels")
    historical = _load(builder.PARENT_CHANNELS)
    if (
        type(actual_channels) is not dict
        or channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != historical["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
    ):
        _fail("Alpha-v18 changed immutable Stable pointer or default release channel")
    alpha = actual_channels.get("alpha")
    if (
        type(alpha) is not dict
        or alpha.get("artifact_sha256") != catalog_hash
        or alpha.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or alpha.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v18.ALPHA_V18_IDENTITY_SHA256
        or alpha.get("parent_alpha_v17_sha256")
        != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v18_flagship_promoted_count") != 673
    ):
        _fail("Alpha-v18 changed its exact promoted Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v18 changed exact {key} channel pointer digest")

    # One actual empty-context proof, beyond all independently checked bodies.
    first = v18.replay(v18.FLAGSHIP_PROMOTED_NAMES[0], edition="alpha")
    if not check((), first.certificate, first.formula):
        _fail("unchanged kernel rejected an actual promoted empty-context theorem")
    if verify_roots:
        for name in v18.FLAGSHIP_ROOT_NAMES:
            root = v18.replay(name, edition="alpha")
            if not check((), root.certificate, root.formula):
                _fail(f"unchanged kernel rejected exact promoted flagship root {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-roots",
        action="store_true",
        help="also regenerate and independently check all six ordinary flagship roots",
    )
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v18 independently: stable=432, alpha=1673, "
        "checked-use=1589, flagship-promoted=673, proof-bundles=5"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
