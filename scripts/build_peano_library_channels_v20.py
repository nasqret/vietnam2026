#!/usr/bin/env python3
"""Seal the next immutable, completely proved constructive Alpha-v20 layer.

All 1,737 Alpha-v19 theorem rows are preserved byte-for-byte as JSON values.
Exactly 39 new Horner, matrix-dot-product, strict-Bertrand, and continued-
fraction specifications are appended only after their single self-contained
ordinary proof bundle has been accepted by the unchanged intuitionistic
kernel. Stable and every historical release remain immutable inputs.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v19.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v19.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v19.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v19.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v20.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v20.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v20.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v20.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as graph_builder  # noqa: E402
from peano_lab.engine.state import proof_identity_metrics, proof_metrics  # noqa: E402
from peano_lab.library import editions_v19 as v19  # noqa: E402
from peano_lab.library import editions_v20 as v20  # noqa: E402
from peano_lab.library.alpha_enrollment_v20 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V20_EXPECTED_COUNT,
    FRONTIER_V20_EXPECTED_NAMES_SHA256,
    alpha_v20_enrollment,
)


SCHEMA = "peano-library-alpha-snapshot-v20"
METRICS_SCHEMA = "peano-library-alpha-metrics-v20"
CHANNEL_SCHEMA = "peano-library-channels-v20"
EXPECTED_PARENT_COUNT = 1_737
EXPECTED_PARENT_CHECKED_USE_COUNT = 1_737
EXPECTED_ALPHA_COUNT = 1_776
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = 1_776
EXPECTED_EDGE_COUNT = 5_882
EXPECTED_LAYER_COUNT = 53
EXPECTED_PARENT_ALPHA_SHA256 = (
    "f1c3d3fba013ca3a5b62a4103dd00bd5b7e39b1f785ed9023099704ad033004b"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "e9990f647d5e75a9a1fa2c817627c66c91f528fa3c3c0617059401c196af656a"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "a1a967629e0a87684f99da0bcedb0248f91e3c72bc5a4bb5dfc067e1e7dc243d"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "5f221a45ee69b45196e0816652f5d6ee734f2f2f9d802a2527d1ab6dcad50cb7"
)
EXPECTED_EVIDENCE_COUNTS = {"alpha_closed": 1_344, "stable_closed": 432}
EXPECTED_FRONTIER_CAMPAIGN_COUNTS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
CLOSURE_ARTIFACT = (
    "research/arithmetic-library/artifacts/"
    "alpha-v20-next-layer-proof-bundle-v1.json"
)
CLOSURE_MODULE = "peano-lab/py/peano_lab/library/campaign_next_layer_closure.py"
CLOSURE_TEST = "peano-lab/py/tests/test_campaign_next_layer_closure.py"
CLOSURE_RECEIPT = (
    "research/arithmetic-library/alpha-v20-next-layer-closure-receipt.md"
)
ADMISSION_RFC = "research/arithmetic-library/alpha-v20-next-layer-rfc-v1.md"
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v20_admission.py"
CONTROL_DOCUMENTS: dict[str, str] = {
    "peano-lab/py/peano_lab/library/editions_v20.py": (
        "Fail-closed completely checked additive Alpha-v20 runtime."
    ),
    "peano-lab/py/peano_lab/library/alpha_enrollment_v20.py": (
        "Exact 39-row additive campaign inventory and immutable Alpha-v19 parent."
    ),
    ADMISSION_RFC: (
        "Reviewed exact Alpha-v20 four-campaign constructive admission contract."
    ),
    ADMISSION_TEST: (
        "Executable immutable-parent, exact-proof, and fail-closed admission audit."
    ),
    CLOSURE_MODULE: (
        "Exact dependency-closed constructive next-layer proof reconstruction."
    ),
    CLOSURE_TEST: (
        "Independent original-kernel proof-bundle and adversarial mutation audit."
    ),
    CLOSURE_ARTIFACT: (
        "Self-contained unchanged-kernel-checked constructive next-layer proof bundle."
    ),
    CLOSURE_RECEIPT: (
        "Exact original-kernel constructive next-layer dependency-closure receipt."
    ),
}


def _digest(value: bytes | str) -> str:
    return sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _load(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if type(result) is not dict:
        raise ValueError(f"{path} must contain a JSON object")
    return result


def _repository_path(path: Path) -> str:
    return path.resolve().relative_to(ROOT.resolve()).as_posix()


def _document(path: Path, role: str) -> dict[str, object]:
    contents = path.read_bytes()
    return {
        "bytes": len(contents),
        "path": _repository_path(path),
        "role": role,
        "sha256": _digest(contents),
    }


def _parent_binding() -> dict[str, object]:
    paths = {
        "catalog": (PARENT_ALPHA, EXPECTED_PARENT_ALPHA_SHA256),
        "channels": (PARENT_CHANNELS, EXPECTED_PARENT_CHANNELS_SHA256),
        "dependency_graph": (PARENT_ALPHA_GRAPH, EXPECTED_PARENT_GRAPH_SHA256),
        "metrics": (PARENT_ALPHA_METRICS, EXPECTED_PARENT_METRICS_SHA256),
    }
    return {
        "artifacts": {
            label: {"path": _repository_path(path), "sha256": digest}
            for label, (path, digest) in paths.items()
        },
        "edition_identity_sha256": v19.ALPHA_V19_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": v19.ALPHA_V19_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v19",
        "theorem_count": EXPECTED_PARENT_COUNT,
    }


def _validate_parent(parent: dict[str, Any]) -> None:
    for path, expected in (
        (PARENT_ALPHA, EXPECTED_PARENT_ALPHA_SHA256),
        (PARENT_ALPHA_METRICS, EXPECTED_PARENT_METRICS_SHA256),
        (PARENT_ALPHA_GRAPH, EXPECTED_PARENT_GRAPH_SHA256),
        (PARENT_CHANNELS, EXPECTED_PARENT_CHANNELS_SHA256),
    ):
        if _digest(path.read_bytes()) != expected:
            raise ValueError(f"sealed Alpha-v19 parent artifact changed: {path}")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v19"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("checked_use_count") != EXPECTED_PARENT_CHECKED_USE_COUNT
        or parent.get("edition_identity_sha256") != v19.ALPHA_V19_IDENTITY_SHA256
        or parent.get("ordered_enrollment_root_sha256")
        != v19.ALPHA_V19_ENROLLMENT_SHA256
        or parent.get("stable_count") != EXPECTED_STABLE_COUNT
    ):
        raise ValueError("immutable completely checked Alpha-v19 parent metadata changed")
    channels = _load(PARENT_CHANNELS)
    if (
        channels.get("schema") != "peano-library-channels-v19"
        or channels.get("default_channel") != "stable"
        or channels.get("channels", {}).get("alpha", {}).get("checked_use_count")
        != EXPECTED_PARENT_CHECKED_USE_COUNT
    ):
        raise ValueError("immutable Alpha-v19 parent channels changed")


def _checked_bundle() -> tuple[Any, Any, dict[str, int]]:
    bundle, receipt, positions = v20.checked_next_layer_bundle()
    if not set(v20.FRONTIER_NEW_NAMES) <= positions.keys():
        raise ValueError("actual Alpha-v20 proof bundle omits an additive theorem")
    if receipt.kernel_calls != len(bundle.nodes):
        raise ValueError("not every Alpha-v20 ordinary proof body reached the kernel")
    return bundle, receipt, positions


def _promotion_payload(
    checked: tuple[Any, Any, dict[str, int]],
) -> dict[str, object]:
    from peano_lab.library.campaign_next_layer_closure import (
        next_layer_closure_plan,
    )

    bundle, receipt, positions = checked
    plan = next_layer_closure_plan()
    roots = tuple(plan.root_names)
    artifact = ROOT / CLOSURE_ARTIFACT
    record = {
        "artifact_bytes": artifact.stat().st_size,
        "artifact_path": CLOSURE_ARTIFACT,
        "artifact_sha256": _digest(artifact.read_bytes()),
        "body_proof_nodes": receipt.total_body_nodes,
        "bundle_root_id": bundle.root,
        "dependency_edges": receipt.dependency_edges,
        "frontier_count": FRONTIER_V20_EXPECTED_COUNT,
        "inherited_dependency_count": len(plan.rows) - FRONTIER_V20_EXPECTED_COUNT,
        "kernel_calls": receipt.kernel_calls,
        "node_count": receipt.node_count,
        "root_names": list(roots),
        "root_node_ids": [positions[name] for name in roots],
    }
    return {
        "campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
        "checked_use_after": EXPECTED_CHECKED_USE_COUNT,
        "checked_use_before": EXPECTED_PARENT_CHECKED_USE_COUNT,
        "frontier_new_count": FRONTIER_V20_EXPECTED_COUNT,
        "frontier_ordered_names_sha256": FRONTIER_V20_EXPECTED_NAMES_SHA256,
        "parent_theorem_count": EXPECTED_PARENT_COUNT,
        "proof_bundle": record,
        "remaining_body_checked_count": 0,
        "status": "kernel_checked_complete_dependency_closed_additive_edition",
    }


def _closure(
    *,
    row: dict[str, Any],
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, object]:
    nodes, depth = proof_metrics(bundle.nodes[node_id].body)
    return {
        "body_proof_depth": depth,
        "body_proof_nodes": nodes,
        "bundle_campaign": "next_layer",
        "bundle_dependency_edge_count": receipt.dependency_edges,
        "bundle_node_count": receipt.node_count,
        "bundle_node_id": node_id,
        "bundle_path": CLOSURE_ARTIFACT,
        "bundle_root_id": bundle.root,
        "certificate_representation": "peano-lab-bundle-v1",
        "certificate_sha256": documents[CLOSURE_ARTIFACT]["sha256"],
        "closure_kind": "dependency_closed_bundle_node",
        "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic",
        "node_statement_sha256": row["statement_sha256"],
        "status": "checked",
    }


def _frontier_row(
    entry: Any,
    *,
    enrollment_index: int,
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    enrollment = alpha_v20_enrollment()
    spec = entry.spec
    name = spec.name
    source = enrollment.source_by_name[name]
    test = enrollment.test_by_name[name]
    rfc = enrollment.rfc_by_name[name]
    campaign = enrollment.campaign_by_name[name].value
    body = bundle.nodes[node_id].body
    proof_nodes, proof_depth = proof_metrics(body)
    proof_objects, proof_edges, reused_objects = proof_identity_metrics(body)
    body_receipt = {
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
    row: dict[str, Any] = {
        "body_checked": True,
        "body_receipt": body_receipt,
        "checked_use": True,
        "dependencies": list(spec.dependencies),
        "dependencies_sha256": _digest("\n".join(spec.dependencies) + "\n"),
        "enrollment_index": enrollment_index,
        "enrollment_origin": entry.enrollment_origin.value,
        "evidence_status": "alpha_closed",
        "frontier_campaign": campaign,
        "logical_spec_sha256": base._logical_spec_sha256(spec),
        "membership": "alpha_only",
        "name": name,
        "proof_tag": None,
        "provenance": [entry.enrollment_origin.value],
        "script": list(spec.script),
        "script_sha256": _digest("\n".join(spec.script) + "\n"),
        "source": {
            "kind": "candidate_module",
            "path": source,
            "sha256": documents[source]["sha256"],
        },
        "statement": spec.statement,
        "statement_sha256": _digest(spec.statement),
        "summary": spec.summary,
        "summary_sha256": _digest(spec.summary),
    }
    closure = _closure(
        row=row,
        node_id=node_id,
        bundle=bundle,
        receipt=receipt,
        documents=documents,
    )
    row["empty_context_closure"] = closure
    row["alpha_v20_frontier_enrollment"] = {
        "body_receipt_sha256": _digest(_compact(body_receipt)),
        "bundle_campaign": "next_layer",
        "bundle_node_id": node_id,
        "bundle_sha256": closure["certificate_sha256"],
        "campaign": campaign,
        "parent_catalog_sha256": EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    parent_path = _repository_path(PARENT_ALPHA)
    row["evidence_links"] = [
        {
            "document_sha256": documents[source]["sha256"],
            "kind": "alpha_v20_frontier_dependency_curried_body",
            "path": source,
            "role": "dependency_curried_body",
            "selector": "document",
        },
        {
            "document_sha256": documents[test]["sha256"],
            "kind": "alpha_v20_frontier_executable_audit",
            "path": test,
            "role": "statement_dependency_replay_mutation_audit",
            "selector": "document",
        },
        {
            "document_sha256": documents[rfc]["sha256"],
            "kind": "alpha_v20_frontier_campaign_rfc",
            "path": rfc,
            "role": "reviewed_constructive_campaign_contract",
            "selector": "document",
        },
        {
            "document_sha256": documents[CLOSURE_ARTIFACT]["sha256"],
            "kind": "alpha_v20_next_layer_self_contained_constructive_proof_bundle",
            "path": CLOSURE_ARTIFACT,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[CLOSURE_RECEIPT]["sha256"],
            "kind": "alpha_v20_next_layer_original_kernel_receipt",
            "path": CLOSURE_RECEIPT,
            "role": "original_kernel_independent_dependency_closure_verification",
            "selector": "document",
        },
        {
            "document_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v19_parent",
            "path": parent_path,
            "role": "exact_immutable_parent_catalog_bytes",
            "selector": "catalog",
        },
    ]
    return row


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    return graph_builder._alpha_graph(rows, kept_edges, redundant_edges).replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v20.py; do not edit.",
        1,
    )


def _topology(
    rows: list[dict[str, Any]],
    parent_metrics: dict[str, Any],
) -> tuple[dict[str, object], str]:
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    if (
        len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT
        or max(depths.values(), default=-1) + 1 != EXPECTED_LAYER_COUNT
    ):
        raise ValueError("Alpha-v20 constructive dependency topology changed")
    reduced_dependencies: dict[str, list[str]] = {
        str(row["name"]): [] for row in rows
    }
    for dependency, theorem in kept_edges:
        reduced_dependencies[theorem].append(dependency)
    reduced_closures: dict[str, frozenset[str]] = {}
    for row in rows:
        name = str(row["name"])
        closure = set(reduced_dependencies[name])
        for dependency in reduced_dependencies[name]:
            closure.update(reduced_closures[dependency])
        reduced_closures[name] = frozenset(closure)
    if reduced_closures != closures:
        raise ValueError("Alpha-v20 display reduction changed exact theorem reachability")

    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    origins = {
        str(row["name"]): str(row["enrollment_origin"]) for row in rows
    }
    redundant_by_origin = Counter(
        origins[theorem] for _dependency, theorem in redundant_edges
    )
    counts = Counter(depths.values())
    topology = {
        "declared_edge_count": EXPECTED_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": EXPECTED_LAYER_COUNT,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant_edges),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(
            sorted(redundant_by_origin.items())
        ),
        "reachability_redundant_direct_dependency_sha256": _digest(
            _compact(redundant_rows)
        ),
        "reachability_reduction_scope": parent_metrics["dependency_graph"][
            "reachability_reduction_scope"
        ],
        "theorems_by_depth": {
            str(depth): count for depth, count in sorted(counts.items())
        },
        "transitive_reduction_edge_count": len(kept_edges),
        "transitive_reduction_edge_sha256": _digest(_compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True,
    }
    return topology, _alpha_graph(rows, kept_edges, redundant_edges)


def build_payloads() -> tuple[str, str, str, str]:
    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("immutable Alpha-v19 parent theorem rows changed")
    checked = _checked_bundle()
    bundle, receipt, positions = checked
    enrollment = alpha_v20_enrollment()
    documents = {
        path: _document(ROOT / path, role)
        for path, role in CONTROL_DOCUMENTS.items()
    }
    parent_path = _repository_path(PARENT_ALPHA)
    documents[parent_path] = _document(
        PARENT_ALPHA,
        "Exact sealed Alpha-v19 parent retained as the complete immutable theorem prefix.",
    )
    for spec in enrollment.frontier_specs:
        campaign = enrollment.campaign_by_name[spec.name].value
        for path, role in (
            (
                enrollment.source_by_name[spec.name],
                f"Exact constructive {campaign} Alpha-v20 proof factory.",
            ),
            (
                enrollment.test_by_name[spec.name],
                f"Independent constructive {campaign} proof and mutation audit.",
            ),
            (
                enrollment.rfc_by_name[spec.name],
                f"Reviewed constructive {campaign} mathematical campaign contract.",
            ),
        ):
            if path not in documents:
                documents[path] = _document(ROOT / path, role)

    rows: list[dict[str, Any]] = list(parent_rows)
    for index, entry in enumerate(v20.ALPHA_ENTRIES[EXPECTED_PARENT_COUNT:]):
        rows.append(
            _frontier_row(
                entry,
                enrollment_index=EXPECTED_PARENT_COUNT + index,
                node_id=positions[entry.spec.name],
                bundle=bundle,
                receipt=receipt,
                documents=documents,
            )
        )
    if rows[:EXPECTED_PARENT_COUNT] != parent_rows:
        raise ValueError("Alpha-v20 modified an immutable Alpha-v19 theorem row")

    evidence = Counter(str(row["evidence_status"]) for row in rows)
    memberships = Counter(str(row["membership"]) for row in rows)
    origins = Counter(str(row["enrollment_origin"]) for row in rows)
    campaigns = Counter(
        enrollment.campaign_by_name[spec.name].value
        for spec in enrollment.frontier_specs
    )
    if (
        len(rows) != EXPECTED_ALPHA_COUNT
        or evidence != Counter(EXPECTED_EVIDENCE_COUNTS)
        or memberships != Counter(stable=432, alpha_only=1_344)
        or campaigns != Counter(EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
        or sum(row["checked_use"] is True for row in rows)
        != EXPECTED_CHECKED_USE_COUNT
    ):
        raise ValueError("Alpha-v20 exact complete additive evidence partition changed")
    parent_origins = Counter(parent["enrollment_origin_counts"])
    parent_origins["ha"] += FRONTIER_V20_EXPECTED_COUNT
    if origins != parent_origins:
        raise ValueError("Alpha-v20 original immutable enrollment provenance changed")
    enrollment_root = base._ordered_root(v20.ALPHA_ENTRIES, include_origin=True)
    specification_root = base._ordered_root(v20.ALPHA_ENTRIES, include_origin=False)
    if enrollment_root != v20.ALPHA_V20_ENROLLMENT_SHA256:
        raise ValueError("Alpha-v20 exact additive enrollment identity changed")

    promotion = _promotion_payload(checked)
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    documents_by_path.update(documents)
    membership_root = base._membership_root(rows)
    catalog = dict(parent)
    catalog.update(
        {
            "alpha_only_count": 1_344,
            "alpha_v20_next_layer_promotion": promotion,
            "canonical_order": [
                *parent["canonical_order"],
                "Constructive Alpha-v20 beta-coded Horner evaluation (7)",
                "Constructive Alpha-v20 beta-coded matrix dot products (10)",
                "Constructive Alpha-v20 Bertrand multiplicity and prime chains (13)",
                "Constructive Alpha-v20 Euclidean continued fractions (9)",
            ],
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edge_count": EXPECTED_EDGE_COUNT,
            "edition_identity_sha256": v20.ALPHA_V20_IDENTITY_SHA256,
            "enrollment_origin_counts": dict(sorted(origins.items())),
            "evidence_counts": dict(sorted(evidence.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "frontier_v20_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "frontier_v20_ordered_names_sha256": FRONTIER_V20_EXPECTED_NAMES_SHA256,
            "layer_count": EXPECTED_LAYER_COUNT,
            "membership_counts": dict(sorted(memberships.items())),
            "membership_root_sha256": membership_root,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v19": _parent_binding(),
            "schema": SCHEMA,
            "stable_count": EXPECTED_STABLE_COUNT,
            "theorem_count": EXPECTED_ALPHA_COUNT,
            "theorems": rows,
        }
    )
    catalog_text = _canonical_json(catalog)

    metrics = _load(PARENT_ALPHA_METRICS)
    topology, graph = _topology(rows, metrics)
    metrics.update(
        {
            "alpha_v20_next_layer_promotion": promotion,
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "dependency_graph": topology,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": v20.ALPHA_V20_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence.items())),
            "frontier_v20_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "frontier_v20_ordered_names_sha256": FRONTIER_V20_EXPECTED_NAMES_SHA256,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v19": catalog["parent_alpha_v19"],
            "schema": METRICS_SCHEMA,
            "theorem_count": EXPECTED_ALPHA_COUNT,
        }
    )
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] += (
        FRONTIER_V20_EXPECTED_COUNT
    )
    accounting.update(
        {
            "campaign_v20_bundle_accounting": {
                "campaign_count": len(EXPECTED_FRONTIER_CAMPAIGN_COUNTS),
                "campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
                "new_checked_theorem_count": FRONTIER_V20_EXPECTED_COUNT,
                "proof_bundle": promotion["proof_bundle"],
                "totals_policy": (
                    "The independently self-contained constructive proof artifact "
                    "is kernel checked once; historical dependency bodies are never "
                    "counted as new theorems."
                ),
            },
            "metric_bearing_theorem_count": EXPECTED_CHECKED_USE_COUNT,
            "missing_empty_context_metric_count": 0,
        }
    )
    gates = metrics["promotion_gates"]
    gates["canonical_topology"].update(
        theorem_count=EXPECTED_ALPHA_COUNT,
        declared_edge_count=EXPECTED_EDGE_COUNT,
    )
    gates["dependency_link_analysis"][
        "reachability_redundant_direct_dependency_count"
    ] = topology["reachability_redundant_direct_dependency_count"]
    gates["source_integrity"]["source_bound_theorem_count"] = EXPECTED_ALPHA_COUNT
    gates["full_alpha_empty_context_compilation"].update(
        checked=EXPECTED_CHECKED_USE_COUNT,
        missing=0,
        required=EXPECTED_ALPHA_COUNT,
        status="passed",
    )
    gates["complete_constructive_alpha_v20_next_layer_closure"] = {
        **promotion,
        "status": "passed",
    }
    metrics_text = _canonical_json(metrics)

    parent_channels = _load(PARENT_CHANNELS)
    artifacts = {
        "catalog": {
            "path": _repository_path(DEFAULT_ALPHA),
            "sha256": _digest(catalog_text),
        },
        "dependency_graph": {
            "path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "sha256": _digest(graph),
        },
        "metrics": {
            "path": _repository_path(DEFAULT_ALPHA_METRICS),
            "sha256": _digest(metrics_text),
        },
    }
    alpha = dict(parent_channels["channels"]["alpha"])
    alpha.update(
        {
            "alpha_v20_frontier_new_count": FRONTIER_V20_EXPECTED_COUNT,
            "artifact_path": _repository_path(DEFAULT_ALPHA),
            "artifact_sha256": _digest(catalog_text),
            "artifacts": artifacts,
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v20.ALPHA_V20_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence.items())),
            "evidence_root_sha256": catalog["evidence_root_sha256"],
            "frontier_v20_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "membership_root_sha256": membership_root,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v19_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "theorem_count": EXPECTED_ALPHA_COUNT,
        }
    )
    channels = {
        "channels": {
            "alpha": alpha,
            "stable": parent_channels["channels"]["stable"],
        },
        "default_channel": "stable",
        "parent_channels_v19": {
            "path": _repository_path(PARENT_CHANNELS),
            "sha256": EXPECTED_PARENT_CHANNELS_SHA256,
        },
        "policy": parent_channels["policy"],
        "schema": CHANNEL_SCHEMA,
    }
    channels["channel_pointer_root_sha256"] = _digest(
        _compact(channels["channels"])
    )
    return catalog_text, metrics_text, graph, _canonical_json(channels)


def _check_or_write(path: Path, expected: str, *, check: bool) -> None:
    if check:
        if not path.is_file():
            raise SystemExit(f"missing {path.relative_to(ROOT)}")
        if path.read_text(encoding="utf-8") != expected:
            raise SystemExit(f"stale {path.relative_to(ROOT)}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(expected, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--alpha-output", type=Path, default=DEFAULT_ALPHA)
    parser.add_argument("--alpha-metrics-output", type=Path, default=DEFAULT_ALPHA_METRICS)
    parser.add_argument("--alpha-graph-output", type=Path, default=DEFAULT_ALPHA_GRAPH)
    parser.add_argument("--channels-output", type=Path, default=DEFAULT_CHANNELS)
    arguments = parser.parse_args(argv)
    for path, payload in zip(
        (
            arguments.alpha_output,
            arguments.alpha_metrics_output,
            arguments.alpha_graph_output,
            arguments.channels_output,
        ),
        build_payloads(),
        strict=True,
    ):
        _check_or_write(path.resolve(), payload, check=arguments.check)
    print(
        f"{'verified' if arguments.check else 'wrote'} Alpha v20: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, new-constructive-theorems=39, "
        "unchecked=0, campaigns=4, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
