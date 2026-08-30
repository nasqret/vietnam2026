#!/usr/bin/env python3
"""Independently verify the complete, immutable additive Alpha-v20 release."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v20 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v19 as v19
from peano_lab.library import editions_v20 as v20
from peano_lab.library.alpha_enrollment_v20 import (
    BERTRAND_CHAIN_ROOT_NAME,
    BERTRAND_MULTIPLICITY_ROOT_NAME,
    CONTINUED_FRACTION_ROOT_NAME,
    FRONTIER_V20_EXPECTED_COUNT,
    FRONTIER_V20_EXPECTED_NAMES_SHA256,
    MATRIX_DOT_PRODUCT_ROOT_NAME,
    POLYNOMIAL_HORNER_ROOT_NAME,
    alpha_v20_enrollment,
)


FRONTIER_ROOT_NAMES = (
    POLYNOMIAL_HORNER_ROOT_NAME,
    MATRIX_DOT_PRODUCT_ROOT_NAME,
    BERTRAND_MULTIPLICITY_ROOT_NAME,
    BERTRAND_CHAIN_ROOT_NAME,
    CONTINUED_FRACTION_ROOT_NAME,
)


def _fail(message: str) -> None:
    raise ValueError(message)


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        _fail(f"cannot read {path}: {error}")
    if type(value) is not dict:
        _fail(f"{path} must contain a JSON object")
    return value


def _documents(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    inventory = catalog.get("evidence_documents")
    if type(inventory) is not list:
        _fail("Alpha-v20 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if type(item) is not dict or type(item.get("path")) is not str:
            _fail("Alpha-v20 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v20 evidence document {path!r}")
        result[path] = item

    enrollment = alpha_v20_enrollment()
    required = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required:
        item = result.get(path)
        if item is None:
            _fail(f"missing Alpha-v20 actual-proof control document {path!r}")
        try:
            actual = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v20 actual-proof source {path!r}: {error}")
        if item.get("sha256") != sha256(actual).hexdigest():
            _fail(f"changed Alpha-v20 actual-proof control document {path!r}")
        if item.get("bytes") != len(actual):
            _fail(f"changed Alpha-v20 actual-proof byte count {path!r}")

    parent = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v20 lost its immutable sealed Alpha-v19 parent document")
    return result


def _expected_closure(
    *,
    row: dict[str, Any],
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    nodes, depth = proof_metrics(bundle.nodes[node_id].body)
    return {
        "body_proof_depth": depth,
        "body_proof_nodes": nodes,
        "bundle_campaign": "next_layer",
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count,
        "bundle_node_id": node_id,
        "bundle_path": builder.CLOSURE_ARTIFACT,
        "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": documents[builder.CLOSURE_ARTIFACT]["sha256"],
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": row["statement_sha256"],
        "status": "checked",
    }


def _verify_frontier_row(
    row: dict[str, Any],
    *,
    index: int,
    bundle: Any,
    receipt: Any,
    node_id: int,
    documents: dict[str, dict[str, Any]],
) -> None:
    enrollment = alpha_v20_enrollment()
    spec = enrollment.frontier_specs[index - builder.EXPECTED_PARENT_COUNT]
    name = spec.name
    if row.get("name") != name:
        _fail(f"frontier theorem changed its exact additive order at index {index}")
    campaign = enrollment.campaign_by_name[name].value
    source = enrollment.source_by_name[name]
    test = enrollment.test_by_name[name]
    rfc = enrollment.rfc_by_name[name]
    expected = {
        "body_checked": True,
        "checked_use": True,
        "dependencies": list(spec.dependencies),
        "dependencies_sha256": sha256(
            ("\n".join(spec.dependencies) + "\n").encode()
        ).hexdigest(),
        "enrollment_index": index,
        "enrollment_origin": "ha",
        "evidence_status": "alpha_closed",
        "frontier_campaign": campaign,
        "logical_spec_sha256": base._logical_spec_sha256(spec),
        "membership": "alpha_only",
        "name": name,
        "proof_tag": None,
        "provenance": ["ha"],
        "script": list(spec.script),
        "script_sha256": sha256(
            ("\n".join(spec.script) + "\n").encode()
        ).hexdigest(),
        "source": {
            "kind": "candidate_module",
            "path": source,
            "sha256": documents[source]["sha256"],
        },
        "statement": spec.statement,
        "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
        "summary": spec.summary,
        "summary_sha256": sha256(spec.summary.encode()).hexdigest(),
    }
    expected_keys = {
        *expected,
        "body_receipt",
        "empty_context_closure",
        "alpha_v20_frontier_enrollment",
        "evidence_links",
    }
    if set(row) != expected_keys:
        _fail(f"frontier theorem {name!r} changed its exact immutable field set")
    for key, value in expected.items():
        if row.get(key) != value:
            _fail(f"frontier theorem {name!r} changed exact source-bound field {key!r}")

    body = bundle.nodes[node_id].body
    proof_nodes, proof_depth = proof_metrics(body)
    proof_objects, proof_edges, reused_objects = proof_identity_metrics(body)
    expected_receipt = {
        "command_count": len(spec.script),
        "dependency_count": len(spec.dependencies),
        "dne_command_count": 0,
        "name": name,
        "proof_depth": proof_depth,
        "proof_edges": proof_edges,
        "proof_nodes": proof_nodes,
        "proof_objects": proof_objects,
        "reused_objects": reused_objects,
        "status": "kernel_checked_dependency_curried_body",
    }
    if row.get("body_receipt") != expected_receipt:
        _fail(f"frontier theorem {name!r} changed its independent original-kernel body receipt")
    artifact_digest = documents[builder.CLOSURE_ARTIFACT]["sha256"]
    expected_transition = {
        "body_receipt_sha256": builder._digest(builder._compact(expected_receipt)),
        "bundle_campaign": "next_layer",
        "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest,
        "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    if row.get("alpha_v20_frontier_enrollment") != expected_transition:
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    if row.get("empty_context_closure") != _expected_closure(
        row=row,
        node_id=node_id,
        bundle=bundle,
        receipt=receipt,
        documents=documents,
    ):
        _fail(f"frontier theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    if type(links) is not list:
        _fail(f"frontier theorem {name!r} has malformed source/proof evidence links")
    required = {
        source,
        test,
        rfc,
        builder.CLOSURE_ARTIFACT,
        builder.CLOSURE_RECEIPT,
        builder._repository_path(builder.PARENT_ALPHA),
    }
    if {item.get("path") for item in links if type(item) is dict} != required:
        _fail(f"frontier theorem {name!r} lost a source/test/RFC/proof/parent link")
    if len(links) != len(required):
        _fail(f"frontier theorem {name!r} duplicated a source/proof evidence link")
    for link in links:
        path = link["path"]
        if link.get("document_sha256") != documents[path]["sha256"]:
            _fail(f"frontier theorem {name!r} changed evidence-document digest {path!r}")
    proof_link = next(item for item in links if item["path"] == builder.CLOSURE_ARTIFACT)
    if proof_link.get("selector") != f"nodes[id={node_id}]":
        _fail(f"frontier theorem {name!r} changed its exact proof-node selector")


def _verify_rows(
    rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    checked: tuple[Any, Any, dict[str, int]],
) -> None:
    if (
        type(rows) is not list
        or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v20 changed its exact 1,737-row parent and 39-row additive frontier")
    if type(checked) is not tuple or len(checked) != 3:
        _fail("Alpha-v20 lacks its independently checked next-layer proof bundle")
    bundle, receipt, positions = checked
    if not isinstance(positions, dict):
        _fail("Alpha-v20 lacks exact independently checked proof-node positions")

    for index, parent in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(parent) is not dict:
            _fail(f"Alpha-v20 historical theorem row {index} is malformed")
        name = str(parent.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v20 changed immutable theorem order at index {index}")
        if row != parent:
            _fail(f"Alpha-v20 modified immutable Alpha-v19 parent row {name!r}")

    frontier: list[str] = []
    campaigns: Counter[str] = Counter()
    for index in range(builder.EXPECTED_PARENT_COUNT, builder.EXPECTED_ALPHA_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v20 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row,
            index=index,
            bundle=bundle,
            receipt=receipt,
            node_id=positions[name],
            documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v20.FRONTIER_NEW_NAMES:
        _fail("Alpha-v20 changed its exact ordered 39-theorem additive frontier")
    if sha256("\n".join(frontier).encode()).hexdigest() != FRONTIER_V20_EXPECTED_NAMES_SHA256:
        _fail("Alpha-v20 changed its sealed additive theorem-name digest")
    if campaigns != Counter(builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS):
        _fail("Alpha-v20 changed its exact four constructive theorem-family counts")
    if Counter(row.get("evidence_status") for row in rows) != Counter(
        builder.EXPECTED_EVIDENCE_COUNTS
    ):
        _fail("Alpha-v20 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v20 retained an unchecked theorem in its completely checked edition")
    seen: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= seen:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in seen:
            _fail(f"Alpha-v20 duplicated the checked theorem {name!r}")
        seen.add(name)
        edges += len(dependencies)
    if len(seen) != builder.EXPECTED_ALPHA_COUNT or edges != builder.EXPECTED_EDGE_COUNT:
        _fail("Alpha-v20 changed its complete 1,776-theorem/5,882-edge checked DAG")


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v20 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v20 artifact schemas changed")
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
        or catalog.get("evidence_counts") != builder.EXPECTED_EVIDENCE_COUNTS
    ):
        _fail("Alpha-v20 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v20.ALPHA_V20_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256")
        != v20.ALPHA_V20_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256")
        != base._ordered_root(v20.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v20 changed exact additive enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v19") != builder._parent_binding():
        _fail("Alpha-v20 lost exact sealed Alpha-v19 artifact provenance")

    documents = _documents(catalog)
    checked = builder._checked_bundle()
    bundle, receipt, positions = checked
    _verify_rows(rows, parent["theorems"], documents, checked)
    promotion = builder._promotion_payload(checked)
    if (
        catalog.get("alpha_v20_next_layer_promotion") != promotion
        or metrics.get("alpha_v20_next_layer_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("frontier_new_count") != FRONTIER_V20_EXPECTED_COUNT
        or promotion.get("checked_use_before") != builder.EXPECTED_PARENT_COUNT
        or promotion.get("checked_use_after") != builder.EXPECTED_ALPHA_COUNT
        or promotion.get("campaign_counts") != builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS
    ):
        _fail("Alpha-v20 changed its exact next-layer additive proof evidence")
    proof_record = promotion.get("proof_bundle")
    if (
        type(proof_record) is not dict
        or proof_record.get("artifact_sha256")
        != documents[builder.CLOSURE_ARTIFACT]["sha256"]
        or proof_record.get("node_count") != len(bundle.nodes)
        or proof_record.get("kernel_calls") != receipt.kernel_calls
        or receipt.kernel_calls != len(bundle.nodes)
        or proof_record.get("dependency_edges") != receipt.dependency_edges
        or proof_record.get("body_proof_nodes") != receipt.total_body_nodes
    ):
        _fail("Alpha-v20 changed independently checked next-layer proof metrics")
    for name in FRONTIER_ROOT_NAMES:
        if name not in positions:
            _fail(f"Alpha-v20 proof bundle lacks exact checked root {name!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed"
        or full.get("checked") != builder.EXPECTED_ALPHA_COUNT
        or full.get("missing") != 0
        or full.get("required") != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v20 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    if (
        accounting.get("metric_bearing_theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        )
        != 1_206
    ):
        _fail("Alpha-v20 misstated its complete independently checked proof accounting")
    campaign_accounting = accounting.get("campaign_v20_bundle_accounting", {})
    if (
        campaign_accounting.get("campaign_count") != 4
        or campaign_accounting.get("new_checked_theorem_count")
        != FRONTIER_V20_EXPECTED_COUNT
        or campaign_accounting.get("campaign_counts")
        != builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS
        or campaign_accounting.get("proof_bundle") != proof_record
        or gates.get("complete_constructive_alpha_v20_next_layer_closure")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v20 changed exact next-layer proof-accounting gates")

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v20.ALPHA_V20_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v20.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v20 catalog, dependency graph, or metrics artifact changed")

    historical = _load(builder.PARENT_CHANNELS)
    actual_channels = channels.get("channels")
    if (
        type(actual_channels) is not dict
        or channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != historical["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
        or channels.get("parent_channels_v19")
        != {
            "path": builder._repository_path(builder.PARENT_CHANNELS),
            "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
        }
    ):
        _fail("Alpha-v20 changed immutable Stable pointer or default release channel")
    alpha = actual_channels.get("alpha")
    if (
        type(alpha) is not dict
        or alpha.get("artifact_sha256") != catalog_hash
        or alpha.get("theorem_count") != builder.EXPECTED_ALPHA_COUNT
        or alpha.get("checked_use_count") != builder.EXPECTED_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v20.ALPHA_V20_IDENTITY_SHA256
        or alpha.get("parent_alpha_v19_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v20_frontier_new_count") != FRONTIER_V20_EXPECTED_COUNT
        or alpha.get("frontier_v20_campaign_counts")
        != builder.EXPECTED_FRONTIER_CAMPAIGN_COUNTS
    ):
        _fail("Alpha-v20 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v20 changed exact {key} channel pointer digest")

    first = v20.replay(v20.FRONTIER_NEW_NAMES[0], edition="alpha")
    if not check((), first.certificate, first.formula):
        _fail("unchanged kernel rejected the first actual empty-context v20 theorem")
    if verify_roots:
        for name in FRONTIER_ROOT_NAMES:
            result = v20.replay(name, edition="alpha")
            if not check((), result.certificate, result.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-roots",
        action="store_true",
        help="also compile and independently check all five ordinary campaign roots",
    )
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v20 independently: stable=432, alpha=1776, "
        "checked-use=1776, frontier-new=39, campaigns=4, "
        "remaining-body-only=0, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
