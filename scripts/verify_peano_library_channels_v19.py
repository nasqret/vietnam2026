#!/usr/bin/env python3
"""Independently verify the completely checked constructive Alpha-v19 release."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

import build_peano_library_channels as base
import build_peano_library_channels_v19 as builder
from peano_lab.engine.state import proof_identity_metrics, proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.library import editions_v18 as v18
from peano_lab.library import editions_v19 as v19
from peano_lab.library.alpha_enrollment_v19 import (
    LINEAR_CONGRUENCE_ROOT_NAME,
    PRIMES_ONE_MOD_FOUR_ROOT_NAME,
    PRIME_TWO_SQUARE_ROOT_NAME,
    PYTHAGOREAN_V19_ROOT_NAMES,
    alpha_v19_enrollment,
)


FRONTIER_ROOT_NAMES = (
    *PYTHAGOREAN_V19_ROOT_NAMES,
    PRIME_TWO_SQUARE_ROOT_NAME,
    LINEAR_CONGRUENCE_ROOT_NAME,
    PRIMES_ONE_MOD_FOUR_ROOT_NAME,
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
        _fail("Alpha-v19 evidence-document inventory is missing")
    result: dict[str, dict[str, Any]] = {}
    for item in inventory:
        if type(item) is not dict or type(item.get("path")) is not str:
            _fail("Alpha-v19 evidence-document inventory is malformed")
        path = item["path"]
        if path in result:
            _fail(f"duplicate Alpha-v19 evidence document {path!r}")
        result[path] = item
    enrollment = alpha_v19_enrollment()
    required_paths = {
        *builder.CONTROL_DOCUMENTS,
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
        *enrollment.rfc_by_name.values(),
    }
    for path in required_paths:
        item = result.get(path)
        if item is None:
            _fail(f"missing Alpha-v19 actual-proof control document {path!r}")
        try:
            actual = (builder.ROOT / path).read_bytes()
        except OSError as error:
            _fail(f"missing Alpha-v19 actual-proof source {path!r}: {error}")
        if item.get("sha256") != sha256(actual).hexdigest():
            _fail(f"changed Alpha-v19 actual-proof control document {path!r}")
        if item.get("bytes") != len(actual):
            _fail(f"changed Alpha-v19 actual-proof byte count {path!r}")
    parent_path = builder._repository_path(builder.PARENT_ALPHA)
    if result.get(parent_path, {}).get("sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail("Alpha-v19 lost its immutable sealed Alpha-v18 parent document")
    return result


def _expected_closure(
    *,
    row: dict[str, Any],
    label: str,
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    artifact_path = str(builder.CAMPAIGNS[label]["artifact"])
    artifact_digest = documents[artifact_path]["sha256"]
    body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
    return {
        "body_proof_depth": body_depth,
        "body_proof_nodes": body_nodes,
        "bundle_campaign": label,
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count,
        "bundle_node_id": node_id,
        "bundle_path": artifact_path,
        "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": artifact_digest,
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": row["statement_sha256"],
        "status": "checked",
    }


def _verify_residual_row(
    row: dict[str, Any],
    parent: dict[str, Any],
    *,
    bundle: Any,
    receipt: Any,
    node_id: int,
    documents: dict[str, dict[str, Any]],
) -> None:
    name = str(parent.get("name"))
    mutable = {
        "alpha_v19_residual_promotion",
        "checked_use",
        "empty_context_closure",
        "evidence_links",
        "evidence_status",
    }
    if set(row) != set(parent) | {"alpha_v19_residual_promotion"}:
        _fail(f"residual theorem {name!r} changed its exact immutable field set")
    for key in set(parent).difference(mutable):
        if row.get(key) != parent[key]:
            _fail(f"residual theorem {name!r} changed immutable parent field {key!r}")
    if (
        parent.get("membership") != "alpha_only"
        or parent.get("checked_use") is not False
        or parent.get("evidence_status") != "body_checked"
        or row.get("checked_use") is not True
        or row.get("evidence_status") != "alpha_closed"
    ):
        _fail(f"residual theorem {name!r} crossed its allowed evidence boundary")

    artifact_path = str(builder.CAMPAIGNS["residual"]["artifact"])
    receipt_path = str(builder.CAMPAIGNS["residual"]["receipt"])
    digest = documents[artifact_path]["sha256"]
    expected_transition = {
        "bundle_campaign": "residual",
        "bundle_node_id": node_id,
        "bundle_sha256": digest,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "parent_evidence_status": parent["evidence_status"],
        "parent_row_sha256": builder._digest(builder._compact(parent)),
    }
    if row.get("alpha_v19_residual_promotion") != expected_transition:
        _fail(f"residual theorem {name!r} changed its immutable parent transition")
    if row.get("empty_context_closure") != _expected_closure(
        row=row,
        label="residual",
        node_id=node_id,
        bundle=bundle,
        receipt=receipt,
        documents=documents,
    ):
        _fail(f"residual theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    historical = parent.get("evidence_links")
    if (
        type(links) is not list
        or type(historical) is not list
        or links[: len(historical)] != historical
        or len(links) != len(historical) + 3
    ):
        _fail(f"residual theorem {name!r} changed its immutable historical links")
    expected_links = (
        {
            "document_sha256": digest,
            "kind": "alpha_v19_residual_self_contained_constructive_proof_bundle",
            "path": artifact_path,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[receipt_path]["sha256"],
            "kind": "alpha_v19_residual_ordinary_kernel_and_compiled_lean_receipt",
            "path": receipt_path,
            "role": "original_kernel_and_independent_compiled_lean_verification",
            "selector": "document",
        },
        {
            "document_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v18_parent",
            "path": builder._repository_path(builder.PARENT_ALPHA),
            "role": "exact_immutable_parent_catalog_bytes",
            "selector": f"theorems[name={name}]",
        },
    )
    if tuple(links[len(historical) :]) != expected_links:
        _fail(f"residual theorem {name!r} lost actual proof/receipt/parent links")


def _verify_frontier_row(
    row: dict[str, Any],
    *,
    index: int,
    bundle: Any,
    receipt: Any,
    node_id: int,
    documents: dict[str, dict[str, Any]],
) -> None:
    enrollment = alpha_v19_enrollment()
    offset = index - builder.EXPECTED_PARENT_COUNT
    spec = enrollment.frontier_specs[offset]
    name = spec.name
    if row.get("name") != name:
        _fail(f"frontier theorem changed its exact additive order at index {index}")
    campaign = enrollment.campaign_by_name[name].value
    source_path = enrollment.source_by_name[name]
    test_path = enrollment.test_by_name[name]
    rfc_path = enrollment.rfc_by_name[name]
    source_digest = documents[source_path]["sha256"]
    statement_digest = sha256(spec.statement.encode()).hexdigest()
    dependencies_digest = sha256(("\n".join(spec.dependencies) + "\n").encode()).hexdigest()
    script_digest = sha256(("\n".join(spec.script) + "\n").encode()).hexdigest()
    summary_digest = sha256(spec.summary.encode()).hexdigest()
    expected = {
        "body_checked": True,
        "checked_use": True,
        "dependencies": list(spec.dependencies),
        "dependencies_sha256": dependencies_digest,
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
        "script_sha256": script_digest,
        "source": {
            "kind": "candidate_module",
            "path": source_path,
            "sha256": source_digest,
        },
        "statement": spec.statement,
        "statement_sha256": statement_digest,
        "summary": spec.summary,
        "summary_sha256": summary_digest,
    }
    for key, value in expected.items():
        if row.get(key) != value:
            _fail(f"frontier theorem {name!r} changed exact source-bound field {key!r}")

    proof_nodes, proof_depth = proof_metrics(bundle.nodes[node_id].body)
    proof_objects, proof_edges, reused_objects = proof_identity_metrics(
        bundle.nodes[node_id].body
    )
    expected_body_receipt = {
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
    if row.get("body_receipt") != expected_body_receipt:
        _fail(f"frontier theorem {name!r} changed its independent original-kernel body receipt")

    artifact_path = str(builder.CAMPAIGNS["frontier"]["artifact"])
    artifact_digest = documents[artifact_path]["sha256"]
    transition = row.get("alpha_v19_frontier_enrollment")
    if type(transition) is not dict:
        _fail(f"frontier theorem {name!r} lacks exact source and proof provenance")
    expected_transition = {
        "body_receipt_sha256": builder._digest(builder._compact(expected_body_receipt)),
        "bundle_campaign": "frontier",
        "bundle_node_id": node_id,
        "bundle_sha256": artifact_digest,
        "campaign": campaign,
        "parent_catalog_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc_path]["sha256"],
        "source_sha256": source_digest,
        "test_sha256": documents[test_path]["sha256"],
    }
    if transition != expected_transition:
        _fail(f"frontier theorem {name!r} changed its exact source/proof enrollment")
    if row.get("empty_context_closure") != _expected_closure(
        row=row,
        label="frontier",
        node_id=node_id,
        bundle=bundle,
        receipt=receipt,
        documents=documents,
    ):
        _fail(f"frontier theorem {name!r} changed its actual checked proof binding")

    links = row.get("evidence_links")
    if type(links) is not list:
        _fail(f"frontier theorem {name!r} has malformed source/proof evidence links")
    required_paths = {
        source_path,
        test_path,
        rfc_path,
        artifact_path,
        str(builder.CAMPAIGNS["frontier"]["receipt"]),
        builder._repository_path(builder.PARENT_ALPHA),
    }
    if {item.get("path") for item in links if type(item) is dict} != required_paths:
        _fail(f"frontier theorem {name!r} lost a source/test/RFC/proof/parent link")
    if len(links) != len(required_paths):
        _fail(f"frontier theorem {name!r} duplicated a source/proof evidence link")
    for item in links:
        path = item["path"]
        if item.get("document_sha256") != documents[path]["sha256"]:
            _fail(f"frontier theorem {name!r} changed evidence-document digest {path!r}")
    bundle_links = [item for item in links if item["path"] == artifact_path]
    if bundle_links[0].get("selector") != f"nodes[id={node_id}]":
        _fail(f"frontier theorem {name!r} changed its exact proof-node selector")


def _verify_rows(
    rows: list[dict[str, Any]],
    parent_rows: list[dict[str, Any]],
    documents: dict[str, dict[str, Any]],
    bundles: dict[str, tuple[Any, Any, dict[str, int]]],
) -> None:
    if (
        type(rows) is not list
        or type(parent_rows) is not list
        or len(parent_rows) != builder.EXPECTED_PARENT_COUNT
        or len(rows) != builder.EXPECTED_ALPHA_COUNT
    ):
        _fail("Alpha-v19 changed its exact 1,673-row parent and 64-row additive frontier")
    if tuple(bundles) != v19.CAMPAIGN_BUNDLE_LABELS:
        _fail("Alpha-v19 changed its two independently checked proof-bundle families")

    residual_names = frozenset(v19.RESIDUAL_PROMOTED_NAMES)
    residual_bundle, residual_receipt, residual_positions = bundles["residual"]
    promoted: list[str] = []
    for index, parent in enumerate(parent_rows):
        row = rows[index]
        if type(row) is not dict or type(parent) is not dict:
            _fail(f"Alpha-v19 historical theorem row {index} is malformed")
        name = str(parent.get("name"))
        if row.get("name") != name:
            _fail(f"Alpha-v19 changed immutable theorem order at index {index}")
        if name not in residual_names:
            if row != parent:
                _fail(f"Alpha-v19 modified unrelated immutable parent row {name!r}")
            continue
        promoted.append(name)
        _verify_residual_row(
            row,
            parent,
            bundle=residual_bundle,
            receipt=residual_receipt,
            node_id=residual_positions[name],
            documents=documents,
        )
    if tuple(promoted) != v19.RESIDUAL_PROMOTED_NAMES:
        _fail("Alpha-v19 changed its exact ordered 84-theorem residual promotion scope")

    frontier_bundle, frontier_receipt, frontier_positions = bundles["frontier"]
    campaigns: Counter[str] = Counter()
    frontier: list[str] = []
    for index in range(builder.EXPECTED_PARENT_COUNT, builder.EXPECTED_ALPHA_COUNT):
        row = rows[index]
        if type(row) is not dict:
            _fail(f"Alpha-v19 additive theorem row {index} is malformed")
        name = str(row.get("name"))
        if name not in frontier_positions:
            _fail(f"frontier theorem {name!r} has no independently checked proof node")
        _verify_frontier_row(
            row,
            index=index,
            bundle=frontier_bundle,
            receipt=frontier_receipt,
            node_id=frontier_positions[name],
            documents=documents,
        )
        frontier.append(name)
        campaigns[str(row["frontier_campaign"])] += 1
    if tuple(frontier) != v19.FRONTIER_NEW_NAMES:
        _fail("Alpha-v19 changed its exact ordered 64-theorem additive frontier")
    if campaigns != Counter(
        {
            "pythagorean": 44,
            "prime_two_square": 1,
            "linear_congruence": 9,
            "primes_one_mod_four": 10,
        }
    ):
        _fail("Alpha-v19 changed its exact four constructive theorem-family counts")
    evidence = Counter(row.get("evidence_status") for row in rows)
    if evidence != Counter({"stable_closed": 432, "alpha_closed": 1_305}):
        _fail("Alpha-v19 changed its completely checked evidence partition")
    if any(row.get("checked_use") is not True for row in rows):
        _fail("Alpha-v19 retained an unchecked theorem in its completely checked edition")
    seen: set[str] = set()
    edges = 0
    for row in rows:
        name = row["name"]
        dependencies = row.get("dependencies")
        if type(dependencies) is not list or not set(dependencies) <= seen:
            _fail(f"checked theorem {name!r} has an unchecked or forward dependency")
        if name in seen:
            _fail(f"Alpha-v19 duplicated the checked theorem {name!r}")
        seen.add(name)
        edges += len(dependencies)
    if len(seen) != 1_737 or edges != 5_779:
        _fail("Alpha-v19 changed its complete 1,737-theorem/5,779-edge checked DAG")


def verify(*, verify_roots: bool = False) -> None:
    parent = _load(builder.PARENT_ALPHA)
    builder._validate_parent(parent)
    catalog = _load(builder.DEFAULT_ALPHA)
    metrics = _load(builder.DEFAULT_ALPHA_METRICS)
    channels = _load(builder.DEFAULT_CHANNELS)
    try:
        graph = builder.DEFAULT_ALPHA_GRAPH.read_text(encoding="utf-8")
    except OSError as error:
        _fail(f"cannot read sealed Alpha-v19 graph: {error}")
    if (
        catalog.get("schema") != builder.SCHEMA
        or metrics.get("schema") != builder.METRICS_SCHEMA
        or channels.get("schema") != builder.CHANNEL_SCHEMA
    ):
        _fail("versioned Alpha-v19 artifact schemas changed")
    rows = catalog.get("theorems")
    if (
        type(rows) is not list
        or catalog.get("theorem_count") != 1_737
        or metrics.get("theorem_count") != 1_737
        or catalog.get("stable_count") != 432
        or catalog.get("checked_use_count") != 1_737
        or metrics.get("checked_use_count") != 1_737
        or catalog.get("edge_count") != 5_779
        or catalog.get("layer_count") != 53
        or catalog.get("evidence_counts") != {"alpha_closed": 1_305, "stable_closed": 432}
    ):
        _fail("Alpha-v19 counts, Stable authority, complete closure, or topology changed")
    if (
        catalog.get("edition_identity_sha256") != v19.ALPHA_V19_IDENTITY_SHA256
        or catalog.get("ordered_enrollment_root_sha256") != v19.ALPHA_V19_ENROLLMENT_SHA256
        or catalog.get("ordered_spec_root_sha256")
        != base._ordered_root(v19.ALPHA_ENTRIES, include_origin=False)
        or catalog.get("membership_root_sha256") != base._membership_root(rows)
    ):
        _fail("Alpha-v19 changed exact additive enrollment, theorem, or membership roots")
    if catalog.get("parent_alpha_v18") != builder._parent_binding():
        _fail("Alpha-v19 lost exact sealed Alpha-v18 artifact provenance")

    documents = _documents(catalog)
    bundles = builder._checked_bundles()
    _verify_rows(rows, parent["theorems"], documents, bundles)
    promotion = builder._promotion_payload(bundles)
    if (
        catalog.get("alpha_v19_campaign_promotion") != promotion
        or metrics.get("alpha_v19_campaign_promotion") != promotion
        or catalog.get("evidence_root_sha256") != base._evidence_root(rows)
        or promotion.get("residual_promoted_count") != 84
        or promotion.get("frontier_new_count") != 64
        or promotion.get("checked_use_before") != 1_589
        or promotion.get("checked_use_after") != 1_737
        or tuple(promotion.get("campaign_order", ())) != ("residual", "frontier")
    ):
        _fail("Alpha-v19 changed its exact complete-closure/additive-frontier evidence")
    campaigns = promotion.get("campaigns")
    if type(campaigns) is not dict or set(campaigns) != {"residual", "frontier"}:
        _fail("Alpha-v19 lost one independently checked original-kernel proof family")
    for label, (bundle, receipt, positions) in bundles.items():
        record = campaigns[label]
        if (
            record.get("artifact_sha256")
            != documents[str(builder.CAMPAIGNS[label]["artifact"])]["sha256"]
            or record.get("node_count") != len(bundle.nodes)
            or record.get("kernel_calls") != receipt.kernel_calls
            or receipt.kernel_calls != len(bundle.nodes)
            or record.get("dependency_edges") != receipt.dependency_edges
            or record.get("body_proof_nodes") != receipt.total_body_nodes
        ):
            _fail(f"Alpha-v19 changed independently checked {label!r} proof metrics")
        for root in record.get("root_names", []):
            if root not in positions:
                _fail(f"Alpha-v19 {label!r} bundle lacks exact checked root {root!r}")

    gates = metrics.get("promotion_gates", {})
    full = gates.get("full_alpha_empty_context_compilation", {})
    if (
        full.get("status") != "passed"
        or full.get("checked") != 1_737
        or full.get("missing") != 0
        or full.get("required") != 1_737
    ):
        _fail("Alpha-v19 misrepresented its completely checked full-edition proof gate")
    accounting = metrics.get("checked_closure_metrics", {})
    if (
        accounting.get("metric_bearing_theorem_count") != 1_737
        or accounting.get("missing_empty_context_metric_count") != 0
        or accounting.get("certificate_digest_kinds", {}).get(
            "self-contained-proof-bundle-sha256"
        )
        != 1_167
    ):
        _fail("Alpha-v19 misstated its complete independently checked proof accounting")
    campaign_accounting = accounting.get("campaign_v19_bundle_accounting", {})
    if (
        campaign_accounting.get("campaign_count") != 2
        or campaign_accounting.get("promoted_checked_theorem_count") != 84
        or campaign_accounting.get("new_checked_theorem_count") != 64
        or campaign_accounting.get("campaigns") != campaigns
        or gates.get("complete_constructive_alpha_v19_campaign_closure")
        != {**promotion, "status": "passed"}
    ):
        _fail("Alpha-v19 changed exact residual/frontier proof-accounting gates")

    catalog_hash = sha256(builder.DEFAULT_ALPHA.read_bytes()).hexdigest()
    metrics_hash = sha256(builder.DEFAULT_ALPHA_METRICS.read_bytes()).hexdigest()
    graph_hash = sha256(builder.DEFAULT_ALPHA_GRAPH.read_bytes()).hexdigest()
    if (
        metrics.get("catalog_sha256") != catalog_hash
        or metrics.get("dependency_graph_sha256") != graph_hash
        or metrics.get("edition_identity_sha256") != v19.ALPHA_V19_IDENTITY_SHA256
        or "scripts/build_peano_library_channels_v19.py" not in graph
        or any(name not in graph for name in FRONTIER_ROOT_NAMES)
    ):
        _fail("Alpha-v19 catalog, dependency graph, or metrics artifact changed")

    historical = _load(builder.PARENT_CHANNELS)
    actual_channels = channels.get("channels")
    if (
        type(actual_channels) is not dict
        or channels.get("default_channel") != "stable"
        or actual_channels.get("stable") != historical["channels"]["stable"]
        or channels.get("channel_pointer_root_sha256")
        != builder._digest(builder._compact(actual_channels))
    ):
        _fail("Alpha-v19 changed immutable Stable pointer or default release channel")
    alpha = actual_channels.get("alpha")
    if (
        type(alpha) is not dict
        or alpha.get("artifact_sha256") != catalog_hash
        or alpha.get("theorem_count") != 1_737
        or alpha.get("checked_use_count") != 1_737
        or alpha.get("edition_identity_sha256") != v19.ALPHA_V19_IDENTITY_SHA256
        or alpha.get("parent_alpha_v18_sha256") != builder.EXPECTED_PARENT_ALPHA_SHA256
        or alpha.get("alpha_v19_residual_promoted_count") != 84
        or alpha.get("alpha_v19_frontier_new_count") != 64
    ):
        _fail("Alpha-v19 changed its completely checked additive Alpha channel pointer")
    for key, digest in (
        ("catalog", catalog_hash),
        ("metrics", metrics_hash),
        ("dependency_graph", graph_hash),
    ):
        if alpha.get("artifacts", {}).get(key, {}).get("sha256") != digest:
            _fail(f"Alpha-v19 changed exact {key} channel pointer digest")

    # Independently recheck one complete ordinary theorem from each real bundle.
    for name in (v19.RESIDUAL_PROMOTED_NAMES[0], v19.FRONTIER_NEW_NAMES[0]):
        actual = v19.replay(name, edition="alpha")
        if not check((), actual.certificate, actual.formula):
            _fail(f"unchanged kernel rejected actual empty-context theorem {name!r}")
    if verify_roots:
        for name in FRONTIER_ROOT_NAMES:
            actual = v19.replay(name, edition="alpha")
            if not check((), actual.certificate, actual.formula):
                _fail(f"unchanged kernel rejected exact new campaign root {name!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify-roots",
        action="store_true",
        help="also regenerate and independently check all five ordinary campaign roots",
    )
    arguments = parser.parse_args(argv)
    verify(verify_roots=arguments.verify_roots)
    print(
        "verified Alpha v19 independently: stable=432, alpha=1737, "
        "checked-use=1737, residual-promoted=84, frontier-new=64, "
        "remaining-body-only=0, proof-bundles=2"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
