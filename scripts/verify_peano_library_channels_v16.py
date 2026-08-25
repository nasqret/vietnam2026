#!/usr/bin/env python3
"""Independently audit the actual constructive Alpha-v16 QR proof promotion."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v16 as builder
from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v15 as v15
from peano_lab.library import editions_v16 as v16
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)


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
        _fail("Alpha-v16 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for row in inventory:
        if type(row) is not dict or type(row.get("path")) is not str:
            _fail("Alpha-v16 evidence-document inventory is malformed")
        if row["path"] in result:
            _fail(f"duplicate Alpha-v16 evidence document {row['path']!r}")
        result[row["path"]] = row
    for path in builder.CONTROL_DOCUMENTS:
        document = result.get(path)
        if document is None:
            _fail(f"missing Alpha-v16 actual-proof control document {path!r}")
        try:
            actual = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v16 actual-proof source {path!r}: {error}")
        if document.get("sha256") != sha256(actual).hexdigest():
            _fail(f"changed Alpha-v16 actual-proof control document {path!r}")
        if document.get("bytes") != len(actual):
            _fail(f"changed Alpha-v16 actual-proof control byte count {path!r}")
    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != (
        builder.EXPECTED_PARENT_ALPHA_SHA256
    ):
        _fail("Alpha-v16 lost its immutable sealed Alpha-v15 parent document")
    return result


def _verify_promotion(
    row: dict[str, Any],
    parent: dict[str, Any],
    *,
    node_id: int,
    bundle: object,
    documents: dict[str, dict[str, Any]],
) -> None:
    name = str(parent.get("name"))
    mutable = {
        "alpha_v16_promotion",
        "checked_use",
        "empty_context_closure",
        "evidence_links",
        "evidence_status",
    }
    if set(row) != set(parent) | {"alpha_v16_promotion"}:
        _fail(f"promoted theorem {name!r} changed its exact immutable field set")
    for key in set(parent).difference(mutable):
        if row.get(key) != parent[key]:
            _fail(f"promoted theorem {name!r} changed immutable parent field {key!r}")
    if (
        parent.get("enrollment_origin") != "qr"
        or parent.get("membership") != "alpha_only"
        or parent.get("checked_use") is not False
        or parent.get("evidence_status")
        not in {"body_checked", "pending_layered_closure"}
        or row.get("checked_use") is not True
        or row.get("evidence_status") != "alpha_closed"
    ):
        _fail(f"promoted theorem {name!r} crossed its allowed evidence boundary")

    transition = row.get("alpha_v16_promotion")
    expected_transition = {
        "bundle_node_id": node_id,
        "bundle_sha256": v16.EXPECTED_QR_BUNDLE_SHA256,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "parent_evidence_status": parent["evidence_status"],
        "parent_row_sha256": builder._digest(builder._compact(parent)),
    }
    if transition != expected_transition:
        _fail(f"promoted theorem {name!r} changed its immutable parent transition")

    body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
    closure = row.get("empty_context_closure")
    expected_closure = {
        "body_proof_depth": body_depth,
        "body_proof_nodes": body_nodes,
        "bundle_dependency_edge_count": v16.EXPECTED_QR_BUNDLE_EDGE_COUNT,
        "bundle_node_count": v16.EXPECTED_QR_BUNDLE_NODE_COUNT,
        "bundle_node_id": node_id,
        "bundle_path": builder._repository_path(builder.QR_BUNDLE),
        "bundle_root_id": v16.EXPECTED_QR_BUNDLE_NODE_COUNT - 1,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": v16.EXPECTED_QR_BUNDLE_SHA256,
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": parent["statement_sha256"],
        "status": "checked",
    }
    if closure != expected_closure:
        _fail(f"promoted theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    old_links = parent.get("evidence_links")
    if (
        type(links) is not list
        or type(old_links) is not list
        or links[: len(old_links)] != old_links
        or len(links) != len(old_links) + 3
    ):
        _fail(f"promoted theorem {name!r} changed its immutable historical links")
    bundle_path = builder._repository_path(builder.QR_BUNDLE)
    receipt_path = builder._repository_path(builder.QR_RECEIPT)
    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    expected_links = (
        {
            "document_sha256": documents[bundle_path]["sha256"],
            "kind": "qr_self_contained_constructive_proof_bundle",
            "path": bundle_path,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[receipt_path]["sha256"],
            "kind": "qr_ordinary_empty_context_closure_receipt",
            "path": receipt_path,
            "role": "original_kernel_full_root_and_independent_lean_verification",
            "selector": "document",
        },
        {
            "document_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v15_parent",
            "path": parent_path,
            "role": "exact_immutable_pre_promotion_catalog_bytes",
            "selector": f"theorems[name={name}]",
        },
    )
    if tuple(links[len(old_links) :]) != expected_links:
        _fail(f"promoted theorem {name!r} lost actual bundle/receipt/parent links")


def _verify_rows(
    rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    bundle: object,
) -> None:
    if (
        type(rows) is not list
        or type(parent_rows) is not list
        or len(rows) != len(parent_rows)
        or len(rows) != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v16 changed its immutable complete 1,673-row parent ledger")
    stack = quadratic_reciprocity_stack()
    positions = {spec.name: index for index, spec in enumerate(stack.admission_order)}
    promoted = frozenset(v16.QR_PROMOTED_NAMES)
    changed: list[str] = []
    for index, (row, parent) in enumerate(zip(rows, parent_rows, strict=True)):
        if type(row) is not dict or type(parent) is not dict:
            _fail(f"Alpha-v16 ledger row {index} is malformed")
        name = str(parent.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v16 changed immutable theorem order at index {index}")
        if name not in promoted:
            if row != parent:
                _fail(f"Alpha-v16 modified unrelated immutable parent row {name!r}")
            continue
        changed.append(name)
        _verify_promotion(
            row,
            parent,
            node_id=positions[name],
            bundle=bundle,
            documents=documents,
        )
    if tuple(changed) != v16.QR_PROMOTED_NAMES:
        _fail("Alpha-v16 changed its exact ordered 315-theorem promotion scope")
    if Counter(row.get("evidence_status") for row in rows) != Counter(
        builder.EXPECTED_EVIDENCE_COUNTS
    ):
        _fail("Alpha-v16 changed its checked/body-only evidence partition")
    checked = {
        str(row["name"])
        for row in rows
        if row.get("checked_use") is True
    }
    if len(checked) != builder.EXPECTED_CHECKED_USE_COUNT:
        _fail("Alpha-v16 changed its exact checked-use authority count")
    for row in rows:
        if row["name"] in checked and not set(row["dependencies"]) <= checked:
            _fail(f"checked theorem {row['name']!r} has an unchecked dependency")
    if sum(len(row["dependencies"]) for row in rows if row["name"] in checked) != (
        v16.EXPECTED_ALPHA_V16_CHECKED_EDGE_COUNT
    ):
        _fail("Alpha-v16 changed its dependency-closed checked-use edge count")


def verify(*, verify_root: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v16 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v16 artifact schemas changed")
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
        _fail("Alpha-v16 counts, Stable authority, or frozen topology changed")
    if (
        catalog.get("edition_identity_sha256") != v16.ALPHA_V16_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != v16.ALPHA_V16_ENROLLMENT_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != parent.get("ordered_enrollment_root_sha256")
        or catalog.get("ordered_spec_root_sha256")
        != parent.get("ordered_spec_root_sha256")
        or catalog.get("membership_root_sha256")
        != parent.get("membership_root_sha256")
    ):
        _fail("Alpha-v16 changed immutable enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v15") != builder._parent_binding():
        _fail("Alpha-v16 lost exact sealed Alpha-v15 artifact provenance")

    documents = _documents(catalog)
    # This is actual proof checking, not hash-authority verification: every
    # frozen formula, dependency edge, and ordinary body is kernel checked.
    bundle, receipt = v16._checked_qr_bundle()
    _verify_rows(rows, parent["theorems"], documents, bundle)
    expected_promotion = builder._promotion_payload(receipt)
    if (
        catalog.get("alpha_v16_qr_promotion") != expected_promotion
        or metrics.get("alpha_v16_qr_promotion") != expected_promotion
        or catalog.get("evidence_counts") != builder.EXPECTED_EVIDENCE_COUNTS
        or metrics.get("evidence_counts") != builder.EXPECTED_EVIDENCE_COUNTS
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v16 exact promotion proof/evidence roots changed")
    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    qr = gates.get("quadratic_reciprocity_full_dependency_closure", {})
    if (
        full.get("status") != "blocked"
        or full.get("checked") != 885
        or full.get("missing") != 788
        or full.get("required") != 1_673
        or qr.get("status") != "passed"
        or qr.get("promoted_count") != 315
        or qr.get("kernel_calls") != 557
    ):
        _fail("Alpha-v16 misrepresented its QR or full-Alpha proof promotion gates")
    accounting = metrics.get("checked_closure_metrics", {})
    if (
        accounting.get("metric_bearing_theorem_count") != 885
        or accounting.get("missing_empty_context_metric_count") != 788
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        )
        != 315
        or accounting.get("shared_bundle_accounting", {}).get("actual_kernel_calls")
        != 557
        or accounting.get("shared_bundle_accounting", {}).get("actual_body_proof_nodes")
        != 41_722
    ):
        _fail("Alpha-v16 double-counted or misstated shared actual proof evidence")

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v16.ALPHA_V16_IDENTITY_SHA256
        or metrics.get("dependency_graph", {}).get("declared_edge_count")
        != builder.EXPECTED_EDGE_COUNT
        or metrics.get("dependency_graph", {}).get("layer_count")
        != builder.EXPECTED_LAYER_COUNT
        or "scripts/build_peano_library_channels_v16.py" not in graph
        or QR_ROOT_NAME not in graph
    ):
        _fail("Alpha-v16 catalog, dependency graph, or metrics artifact changed")

    actual_channels = channels.get("channels")
    parent_channels = _load(builder.PARENT_CHANNELS)
    if (
        type(actual_channels) is not dict
        or channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != parent_channels["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
    ):
        _fail("Alpha-v16 changed immutable Stable pointer or default release channel")
    alpha = actual_channels.get("alpha")
    if (
        type(alpha) is not dict
        or alpha.get("artifact_sha256") != catalog_hash
        or alpha.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or alpha.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v16.ALPHA_V16_IDENTITY_SHA256
        or alpha.get("parent_alpha_v15_sha256")
        != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v16_qr_promoted_count") != 315
    ):
        _fail("Alpha-v16 changed its exact promoted Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v16 changed exact {key} channel pointer digest")

    first = v16.replay(v16.QR_PROMOTED_NAMES[0], edition="alpha")
    if not check((), first.certificate, first.formula):
        _fail("unchanged kernel rejected an actual promoted empty-context theorem")
    if verify_root:
        root = v16.replay(QR_ROOT_NAME, edition="alpha")
        if not check((), root.certificate, root.formula):
            _fail("unchanged kernel rejected the exact ordinary QR root certificate")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-root",
        action="store_true",
        help="also regenerate and recheck the complete ordinary 54,870-node QR root",
    )
    arguments = parser.parse_args(argv)
    verify(verify_root=arguments.verify_root)
    print(
        "verified Alpha v16 independently: stable=432, alpha=1673, "
        "checked-use=885, qr-promoted=315, actual-kernel-calls=557"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
