#!/usr/bin/env python3
"""Seal the fully checked additive Alpha-v28 constructive lower layer."""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v27.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v27.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v27.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v27.json"
IMMUTABLE_QR_CORPUS = ROOT / "book" / "_static" / "pa-proof-explorer" / "api" / "corpus.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v28.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v28.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v28.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v28.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as graph_builder  # noqa: E402
from peano_lab.engine.state import proof_identity_metrics, proof_metrics  # noqa: E402
from peano_lab.library import editions_v27 as v27  # noqa: E402
from peano_lab.library import editions_v28 as v28  # noqa: E402
from peano_lab.library.alpha_enrollment_v28 import (  # noqa: E402
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V28_EXPECTED_COUNT,
    FRONTIER_V28_EXPECTED_NAMES_SHA256,
    alpha_v28_enrollment,
)


SCHEMA = "peano-library-alpha-snapshot-v28"
METRICS_SCHEMA = "peano-library-alpha-metrics-v28"
CHANNEL_SCHEMA = "peano-library-channels-v28"
EXPECTED_PARENT_COUNT = 2_560
EXPECTED_PARENT_CHECKED_USE_COUNT = 2_560
EXPECTED_STABLE_COUNT = 432
EXPECTED_PARENT_ALPHA_SHA256 = (
    "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "b63f72824dcceaf484bb44f32c85cce263bca101aac663d6266fcf2e3ea46ff8"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "6dace70f8fb07c3d5e29ecf95f2804d1e53d08e8ba1dd080df1bbeac3799daa0"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "87f28966431ca285dce738ad07386ce4c3baaf766ff7f70a4b6df988fc09de5e"
)
EXPECTED_IMMUTABLE_QR_CORPUS_BYTES = 17_229_311
EXPECTED_IMMUTABLE_QR_CORPUS_SHA256 = (
    "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
)
EXPECTED_FRONTIER_CAMPAIGN_COUNTS = {
    campaign.value: count for campaign, count in EXPECTED_CAMPAIGN_COUNTS.items()
}
CLOSURE_ARTIFACT = (
    "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
)
CLOSURE_MODULE = "peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py"
CLOSURE_TEST = "peano-lab/py/tests/test_campaign_lower_layer_closure.py"
CLOSURE_RECEIPT = "research/arithmetic-library/alpha-v28-lower-layer-receipt.md"
ADMISSION_RFC = "research/arithmetic-library/alpha-v28-lower-layer-rfc-v1.md"
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v28_admission.py"
DEFINITION_REGISTRY = "scripts/constructive_lower_layer_definitions.py"
DEFINITION_GRAPH_SOURCE = "scripts/constructive_lower_layer_definition_graph.py"
DEFINITION_TEST = "peano-lab/py/tests/test_constructive_lower_layer_definitions.py"
LOCAL_DISPLAY_ADAPTER = "scripts/constructive_lower_layer_defined_adapter.py"
LOCAL_DISPLAY_TEST = DEFINITION_TEST
FORMULA_COMPACTOR = "scripts/constructive_formula_compactor.py"
EXPLORER_BUILDER = "scripts/build_constructive_lower_layer_explorer.py"
EXPLORER_RENDERER = "scripts/constructive_checked_explorer_renderer.py"
EXPLORER_TEST = "peano-lab/py/tests/test_constructive_lower_layer_explorer.py"
CAMPAIGN_EXTENSION = "scripts/extend_constructive_lower_layer_campaign.py"
HISTORICAL_PRESENTATION_SUCCESSOR = "scripts/upgrade_constructive_second_wave_publication_v28.py"
HISTORICAL_PRESENTATION_TEST = "peano-lab/py/tests/test_constructive_second_wave_publication_v28.py"
HISTORICAL_PUBLICATION_FIXTURE = "peano-lab/py/tests/conftest.py"
HISTORICAL_CAMPAIGN_PROJECTION = (
    "research/arithmetic-library/artifacts/alpha-v27-campaign-projection-v1.json"
)
EXPECTED_HISTORICAL_CAMPAIGN_PROJECTION_SHA256 = (
    "e569978514ce1ae0e2e12c3195d65eb7db531c0f3d22cfb2550a7f55d88159c9"
)
CHANNEL_EXPORTER = "scripts/build_peano_library_channels_v28.py"
CHANNEL_VERIFIER = "scripts/verify_peano_library_channels_v28.py"
CHANNEL_VERIFIER_TEST = "scripts/test_verify_peano_library_channels_v28.py"
CONTROL_DOCUMENTS: dict[str, str] = {
    "peano-lab/py/peano_lab/library/editions_v28.py": (
        "Fail-closed independently checked additive Alpha-v28 theorem runtime."
    ),
    "peano-lab/py/peano_lab/library/alpha_enrollment_v28.py": (
        "Exact additive research-campaign inventory and immutable Alpha-v27 parent."
    ),
    ADMISSION_RFC: "Reviewed exact constructive Alpha-v28 admission contract.",
    ADMISSION_TEST: "Immutable-parent, exact-proof, and fail-closed admission audit.",
    CLOSURE_MODULE: "Original-kernel full dependency-closed proof reconstruction.",
    CLOSURE_TEST: "Independent proof-bundle and adversarial mutation audit.",
    CLOSURE_ARTIFACT: "Self-contained unchanged-kernel-checked complete proof bundle.",
    CLOSURE_RECEIPT: "Exact original-kernel full dependency-closure receipt.",
    DEFINITION_REGISTRY: (
        "Additive, hygienic conservative abbreviation registry with frozen definition identities."
    ),
    DEFINITION_GRAPH_SOURCE: (
        "Independent reviewed-definition DAG, signature alignment, and AST-equivalence audit."
    ),
    DEFINITION_TEST: "All lower-layer definition and local-formula exact AST round trips.",
    LOCAL_DISPLAY_ADAPTER: "Isolated lower-layer conservative theorem and local-proposition notation.",
    EXPLORER_BUILDER: "Exact QR-template lower-layer proof explorer publication.",
    EXPLORER_RENDERER: "Data-driven checked QR-template proof renderer preserving first-admission evidence.",
    EXPLORER_TEST: "Exact roots, conservative definition topology, and QR presentation regressions.",
    CAMPAIGN_EXTENSION: "Additive exact-evidence lower-layer milestone and definition-atlas integration.",
    HISTORICAL_PRESENTATION_SUCCESSOR: "Additive current-channel presentation for immutable v27 proof pages.",
    HISTORICAL_PRESENTATION_TEST: "Historical v27 evidence and current v28 presentation compatibility audit.",
    HISTORICAL_PUBLICATION_FIXTURE: "Exactly scoped historical v27 campaign projection without replacing proof authority.",
    HISTORICAL_CAMPAIGN_PROJECTION: "Byte-exact archived v27 campaign and definition projection for historical publication replay.",
    CHANNEL_EXPORTER: "Source-bound deterministic additive Alpha-v28 catalogue construction.",
    CHANNEL_VERIFIER: "Independent original-kernel, compiled-Lean, parent-provenance, and release audit.",
    CHANNEL_VERIFIER_TEST: "Adversarial source, statement, proof-receipt, and authority mutation regressions.",
}


def _digest(value: bytes | str) -> str:
    return sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _compact(value: object) -> str:
    return json.dumps(
        value, ensure_ascii=False, allow_nan=False, separators=(",", ":"), sort_keys=True
    )


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain a JSON object")
    return value


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
        "edition_identity_sha256": v27.ALPHA_V27_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": v27.ALPHA_V27_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v27",
        "theorem_count": EXPECTED_PARENT_COUNT,
    }


def _validate_parent(parent: dict[str, Any]) -> None:
    from peano_lab.library.campaign_lower_layer_closure import validate_parent_provider_bytes

    # Every historical ordinary proof provider remains byte-exact, including
    # providers not needed in this checkpoint's actual dependency cone.
    if len(validate_parent_provider_bytes()) != 17:
        raise ValueError("the exact seventeen immutable Alpha-v27 proof providers changed")
    if len(parent.get("evidence_documents", ())) != 605:
        raise ValueError("the exact immutable Alpha-v27 document inventory changed")
    if _digest((ROOT / HISTORICAL_CAMPAIGN_PROJECTION).read_bytes()) != EXPECTED_HISTORICAL_CAMPAIGN_PROJECTION_SHA256:
        raise ValueError("the exact archived Alpha-v27 campaign projection changed")
    for path, expected in (
        (PARENT_ALPHA, EXPECTED_PARENT_ALPHA_SHA256),
        (PARENT_ALPHA_METRICS, EXPECTED_PARENT_METRICS_SHA256),
        (PARENT_ALPHA_GRAPH, EXPECTED_PARENT_GRAPH_SHA256),
        (PARENT_CHANNELS, EXPECTED_PARENT_CHANNELS_SHA256),
    ):
        if _digest(path.read_bytes()) != expected:
            raise ValueError(f"sealed Alpha-v27 parent artifact changed: {path}")
    immutable_qr = _repository_path(IMMUTABLE_QR_CORPUS)
    parent_qr_documents = [
        item
        for item in parent.get("evidence_documents", ())
        if isinstance(item, dict) and item.get("path") == immutable_qr
    ]
    if (
        len(parent_qr_documents) != 1
        or parent_qr_documents[0].get("sha256")
        != EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
        or parent_qr_documents[0].get("bytes") != EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
    ):
        raise ValueError("immutable Alpha-v27 quadratic-reciprocity evidence binding changed")
    try:
        immutable_qr_payload = IMMUTABLE_QR_CORPUS.read_bytes()
    except OSError as error:
        raise ValueError("immutable Alpha-v27 quadratic-reciprocity evidence unavailable") from error
    if (
        len(immutable_qr_payload) != EXPECTED_IMMUTABLE_QR_CORPUS_BYTES
        or _digest(immutable_qr_payload) != EXPECTED_IMMUTABLE_QR_CORPUS_SHA256
    ):
        raise ValueError("immutable Alpha-v27 quadratic-reciprocity evidence bytes changed")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v27"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("checked_use_count") != EXPECTED_PARENT_CHECKED_USE_COUNT
        or parent.get("edition_identity_sha256") != v27.ALPHA_V27_IDENTITY_SHA256
        or parent.get("ordered_enrollment_root_sha256") != v27.ALPHA_V27_ENROLLMENT_SHA256
        or parent.get("stable_count") != EXPECTED_STABLE_COUNT
    ):
        raise ValueError("the immutable completely checked Alpha-v27 parent changed")
    channels = _load(PARENT_CHANNELS)
    if (
        channels.get("schema") != "peano-library-channels-v27"
        or channels.get("default_channel") != "stable"
        or channels.get("channels", {}).get("alpha", {}).get("checked_use_count")
        != EXPECTED_PARENT_CHECKED_USE_COUNT
    ):
        raise ValueError("the immutable Alpha-v27 parent channels changed")


def _checked_bundle() -> tuple[Any, Any, dict[str, int]]:
    bundle, receipt, positions = v28.checked_lower_layer_bundle()
    if not set(v28.FRONTIER_NEW_NAMES) <= positions.keys():
        raise ValueError("the actual Alpha-v28 proof bundle omits a new theorem")
    if receipt.kernel_calls != len(bundle.nodes):
        raise ValueError("not every Alpha-v28 ordinary proof body reached the kernel")
    verifier = (
        ROOT.parent / "peano-lab-lean" / ".lake" / "build" / "bin" / "peano_lab_bundle_verify"
    )
    try:
        result = subprocess.run(
            [str(verifier), str(ROOT / CLOSURE_ARTIFACT)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("the independently compiled Lean proof verifier is unavailable") from error
    expected = f"nodes={len(bundle.nodes)}\troot={bundle.root}"
    if (
        result.returncode != 0
        or not result.stdout.startswith("ACCEPT\t")
        or not result.stdout.rstrip().endswith(expected)
    ):
        raise ValueError("the independently compiled Lean verifier rejected Alpha-v28 proof")
    return bundle, receipt, positions


def _promotion_payload(checked: tuple[Any, Any, dict[str, int]]) -> dict[str, object]:
    from peano_lab.library.campaign_lower_layer_closure import lower_layer_plan

    bundle, receipt, positions = checked
    plan = lower_layer_plan(parent_specs=v27.ALPHA_CHECKED_SPECS)
    artifact = ROOT / CLOSURE_ARTIFACT
    return {
        "campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
        "checked_use_after": v28.EXPECTED_ALPHA_V28_CHECKED_USE_COUNT,
        "checked_use_before": EXPECTED_PARENT_CHECKED_USE_COUNT,
        "frontier_new_count": FRONTIER_V28_EXPECTED_COUNT,
        "frontier_ordered_names_sha256": FRONTIER_V28_EXPECTED_NAMES_SHA256,
        "independent_lean_bundle_verified": True,
        "parent_theorem_count": EXPECTED_PARENT_COUNT,
        "proof_bundle": {
            "artifact_bytes": artifact.stat().st_size,
            "artifact_path": CLOSURE_ARTIFACT,
            "artifact_sha256": _digest(artifact.read_bytes()),
            "body_proof_nodes": receipt.total_body_nodes,
            "bundle_root_id": bundle.root,
            "dependency_edges": receipt.dependency_edges,
            "frontier_count": FRONTIER_V28_EXPECTED_COUNT,
            "inherited_dependency_count": len(plan.rows) - FRONTIER_V28_EXPECTED_COUNT,
            "independent_lean_bundle_verified": True,
            "kernel_calls": receipt.kernel_calls,
            "node_count": receipt.node_count,
            "root_names": list(plan.root_names),
            "root_node_ids": [positions[name] for name in plan.root_names],
        },
        "remaining_body_checked_count": 0,
        "status": "kernel_checked_complete_dependency_closed_additive_edition",
    }


def _closure(
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
        "bundle_campaign": "lower_layer",
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
    enrollment = alpha_v28_enrollment()
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
    closure = _closure(row, node_id, bundle, receipt, documents)
    row["empty_context_closure"] = closure
    row["alpha_v28_frontier_enrollment"] = {
        "body_receipt_sha256": _digest(_compact(body_receipt)),
        "bundle_campaign": "lower_layer",
        "bundle_node_id": node_id,
        "bundle_sha256": closure["certificate_sha256"],
        "campaign": campaign,
        "parent_catalog_sha256": EXPECTED_PARENT_ALPHA_SHA256,
        "rfc_sha256": documents[rfc]["sha256"],
        "source_sha256": documents[source]["sha256"],
        "test_sha256": documents[test]["sha256"],
    }
    row["evidence_links"] = [
        {
            "document_sha256": documents[source]["sha256"],
            "kind": "alpha_v28_frontier_dependency_curried_body",
            "path": source,
            "role": "dependency_curried_body",
            "selector": "document",
        },
        {
            "document_sha256": documents[test]["sha256"],
            "kind": "alpha_v28_frontier_executable_audit",
            "path": test,
            "role": "statement_dependency_replay_mutation_audit",
            "selector": "document",
        },
        {
            "document_sha256": documents[rfc]["sha256"],
            "kind": "alpha_v28_frontier_campaign_rfc",
            "path": rfc,
            "role": "reviewed_constructive_campaign_contract",
            "selector": "document",
        },
        {
            "document_sha256": documents[CLOSURE_ARTIFACT]["sha256"],
            "kind": "alpha_v28_lower_layer_self_contained_constructive_proof_bundle",
            "path": CLOSURE_ARTIFACT,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[CLOSURE_RECEIPT]["sha256"],
            "kind": "alpha_v28_lower_layer_original_kernel_receipt",
            "path": CLOSURE_RECEIPT,
            "role": "original_kernel_independent_dependency_closure_verification",
            "selector": "document",
        },
        {
            "document_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v27_parent",
            "path": _repository_path(PARENT_ALPHA),
            "role": "exact_immutable_parent_catalog_bytes",
            "selector": "catalog",
        },
    ]
    return row


def _topology(
    rows: list[dict[str, Any]], parent_metrics: dict[str, Any]
) -> tuple[dict[str, Any], str]:
    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    if (
        len(kept_edges) + len(redundant_edges) != v28.EXPECTED_ALPHA_V28_EDGE_COUNT
        or max(depths.values(), default=-1) + 1 != v28.EXPECTED_ALPHA_V28_LAYER_COUNT
    ):
        raise ValueError("the frozen Alpha-v28 dependency topology changed")
    reduced_dependencies: dict[str, list[str]] = {str(row["name"]): [] for row in rows}
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
        raise ValueError("the Alpha-v28 display reduction changed theorem reachability")
    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem} for dependency, theorem in kept_edges
    ]
    origins = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_by_origin = Counter(origins[theorem] for _dependency, theorem in redundant_edges)
    counts = Counter(depths.values())
    topology = {
        "declared_edge_count": v28.EXPECTED_ALPHA_V28_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": v28.EXPECTED_ALPHA_V28_LAYER_COUNT,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant_edges),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(
            sorted(redundant_by_origin.items())
        ),
        "reachability_redundant_direct_dependency_sha256": _digest(_compact(redundant_rows)),
        "reachability_reduction_scope": parent_metrics["dependency_graph"][
            "reachability_reduction_scope"
        ],
        "theorems_by_depth": {str(depth): count for depth, count in sorted(counts.items())},
        "transitive_reduction_edge_count": len(kept_edges),
        "transitive_reduction_edge_sha256": _digest(_compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True,
    }
    graph = graph_builder._alpha_graph(rows, kept_edges, redundant_edges).replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v28.py; do not edit.",
        1,
    )
    return topology, graph


def build_payloads() -> tuple[str, str, str, str]:
    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("the immutable Alpha-v27 parent theorem rows changed")
    checked = _checked_bundle()
    bundle, receipt, positions = checked
    enrollment = alpha_v28_enrollment()
    documents = {
        path: _document(ROOT / path, role) for path, role in CONTROL_DOCUMENTS.items()
    }
    parent_path = _repository_path(PARENT_ALPHA)
    documents[parent_path] = _document(
        PARENT_ALPHA, "Exact immutable fully checked Alpha-v27 parent catalog."
    )
    for spec in enrollment.frontier_specs:
        campaign = enrollment.campaign_by_name[spec.name].value
        for path, role in (
            (
                enrollment.source_by_name[spec.name],
                f"Exact constructive {campaign} Alpha-v28 proof factory.",
            ),
            (
                enrollment.test_by_name[spec.name],
                f"Independent constructive {campaign} proof and mutation audit.",
            ),
            (
                enrollment.rfc_by_name[spec.name],
                f"Reviewed constructive {campaign} mathematical contract.",
            ),
        ):
            if path not in documents:
                documents[path] = _document(ROOT / path, role)
    rows: list[dict[str, Any]] = list(parent_rows)
    for offset, item in enumerate(v28.ALPHA_ENTRIES[EXPECTED_PARENT_COUNT:]):
        rows.append(
            _frontier_row(
                item,
                enrollment_index=EXPECTED_PARENT_COUNT + offset,
                node_id=positions[item.spec.name],
                bundle=bundle,
                receipt=receipt,
                documents=documents,
            )
        )
    if rows[:EXPECTED_PARENT_COUNT] != parent_rows:
        raise ValueError("Alpha-v28 modified an immutable Alpha-v27 theorem row")
    evidence = Counter(str(row["evidence_status"]) for row in rows)
    memberships = Counter(str(row["membership"]) for row in rows)
    origins = Counter(str(row["enrollment_origin"]) for row in rows)
    campaigns = Counter(
        enrollment.campaign_by_name[spec.name].value for spec in enrollment.frontier_specs
    )
    alpha_count = v28.EXPECTED_ALPHA_V28_COUNT
    alpha_only_count = alpha_count - EXPECTED_STABLE_COUNT
    if (
        len(rows) != alpha_count
        or evidence != Counter(alpha_closed=alpha_only_count, stable_closed=EXPECTED_STABLE_COUNT)
        or memberships != Counter(stable=EXPECTED_STABLE_COUNT, alpha_only=alpha_only_count)
        or campaigns != Counter(EXPECTED_FRONTIER_CAMPAIGN_COUNTS)
        or sum(row["checked_use"] is True for row in rows) != alpha_count
    ):
        raise ValueError("the exact complete Alpha-v28 evidence partition changed")
    parent_origins = Counter(parent["enrollment_origin_counts"])
    parent_origins["ha"] += FRONTIER_V28_EXPECTED_COUNT
    if origins != parent_origins:
        raise ValueError("the immutable enrollment origin changed")
    enrollment_root = base._ordered_root(v28.ALPHA_ENTRIES, include_origin=True)
    specification_root = base._ordered_root(v28.ALPHA_ENTRIES, include_origin=False)
    if enrollment_root != v28.ALPHA_V28_ENROLLMENT_SHA256:
        raise ValueError("the exact additive Alpha-v28 enrollment identity changed")
    promotion = _promotion_payload(checked)
    documents_by_path = {str(item["path"]): item for item in parent["evidence_documents"]}
    for path, document in documents.items():
        if path in documents_by_path and documents_by_path[path] != document:
            raise ValueError(f"Alpha-v28 attempted to replace immutable historical evidence {path!r}")
        documents_by_path[path] = document
    membership_root = base._membership_root(rows)
    catalog = dict(parent)
    descriptions = {
        "foundations": (
            "unique division, canonical signed Bezout, Euclid cancellation, actual prime-factor lists and witnessed permutation uniqueness, and prime infinitude"
        ),
        "gaussian_euclidean": (
            "constructive signed and Gaussian integer Euclidean division with strictly smaller remainder norm"
        ),
        "eisenstein_euclidean": (
            "constructive Eisenstein integer Euclidean division with strictly smaller remainder norm"
        ),
        "prime_enumeration": (
            "actual exhaustive first-prime lists with constructed effective double-exponential bounds"
        ),
    }
    catalog.update(
        {
            "alpha_only_count": alpha_only_count,
            "alpha_v28_lower_layer_promotion": promotion,
            "canonical_order": [
                *parent["canonical_order"],
                *(
                    f"Constructive Alpha-v28 {descriptions[campaign]} ({count})"
                    for campaign, count in EXPECTED_FRONTIER_CAMPAIGN_COUNTS.items()
                ),
            ],
            "checked_use_count": alpha_count,
            "edge_count": v28.EXPECTED_ALPHA_V28_EDGE_COUNT,
            "edition_identity_sha256": v28.ALPHA_V28_IDENTITY_SHA256,
            "enrollment_origin_counts": dict(sorted(origins.items())),
            "evidence_counts": dict(sorted(evidence.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "frontier_v28_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "frontier_v28_ordered_names_sha256": FRONTIER_V28_EXPECTED_NAMES_SHA256,
            "layer_count": v28.EXPECTED_ALPHA_V28_LAYER_COUNT,
            "membership_counts": dict(sorted(memberships.items())),
            "membership_root_sha256": membership_root,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v27": _parent_binding(),
            "schema": SCHEMA,
            "stable_count": EXPECTED_STABLE_COUNT,
            "theorem_count": alpha_count,
            "theorems": rows,
        }
    )
    catalog_text = _canonical_json(catalog)
    metrics = _load(PARENT_ALPHA_METRICS)
    topology, graph = _topology(rows, metrics)
    metrics.update(
        {
            "alpha_v28_lower_layer_promotion": promotion,
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": alpha_count,
            "dependency_graph": topology,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": v28.ALPHA_V28_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence.items())),
            "frontier_v28_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "frontier_v28_ordered_names_sha256": FRONTIER_V28_EXPECTED_NAMES_SHA256,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v27": catalog["parent_alpha_v27"],
            "schema": METRICS_SCHEMA,
            "theorem_count": alpha_count,
        }
    )
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] += (
        FRONTIER_V28_EXPECTED_COUNT
    )
    accounting.update(
        {
            "campaign_v28_bundle_accounting": {
                "campaign_count": len(EXPECTED_FRONTIER_CAMPAIGN_COUNTS),
                "campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
                "new_checked_theorem_count": FRONTIER_V28_EXPECTED_COUNT,
                "proof_bundle": promotion["proof_bundle"],
                "totals_policy": (
                    "One independently self-contained artifact; historical bodies "
                    "are never counted as new theorems."
                ),
            },
            "metric_bearing_theorem_count": alpha_count,
            "missing_empty_context_metric_count": 0,
        }
    )
    gates = metrics["promotion_gates"]
    gates["canonical_topology"].update(
        theorem_count=alpha_count,
        declared_edge_count=v28.EXPECTED_ALPHA_V28_EDGE_COUNT,
    )
    gates["dependency_link_analysis"]["reachability_redundant_direct_dependency_count"] = (
        topology["reachability_redundant_direct_dependency_count"]
    )
    gates["source_integrity"]["source_bound_theorem_count"] = alpha_count
    gates["full_alpha_empty_context_compilation"].update(
        checked=alpha_count,
        missing=0,
        required=alpha_count,
        status="passed",
    )
    gates["complete_constructive_alpha_v28_lower_layer"] = {
        **promotion,
        "status": "passed",
    }
    metrics_text = _canonical_json(metrics)
    parent_channels = _load(PARENT_CHANNELS)
    artifacts = {
        "catalog": {"path": _repository_path(DEFAULT_ALPHA), "sha256": _digest(catalog_text)},
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
            "alpha_v28_frontier_new_count": FRONTIER_V28_EXPECTED_COUNT,
            "artifact_path": _repository_path(DEFAULT_ALPHA),
            "artifact_sha256": _digest(catalog_text),
            "artifacts": artifacts,
            "checked_use_count": alpha_count,
            "edition_identity_sha256": v28.ALPHA_V28_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence.items())),
            "evidence_root_sha256": catalog["evidence_root_sha256"],
            "frontier_v28_campaign_counts": EXPECTED_FRONTIER_CAMPAIGN_COUNTS,
            "membership_root_sha256": membership_root,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": specification_root,
            "parent_alpha_v27_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "theorem_count": alpha_count,
        }
    )
    channels = {
        "channels": {"alpha": alpha, "stable": parent_channels["channels"]["stable"]},
        "default_channel": "stable",
        "parent_channels_v27": {
            "path": _repository_path(PARENT_CHANNELS),
            "sha256": EXPECTED_PARENT_CHANNELS_SHA256,
        },
        "policy": parent_channels["policy"],
        "schema": CHANNEL_SCHEMA,
    }
    channels["channel_pointer_root_sha256"] = _digest(_compact(channels["channels"]))
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
    args = parser.parse_args(argv)
    for path, payload in zip(
        (
            args.alpha_output,
            args.alpha_metrics_output,
            args.alpha_graph_output,
            args.channels_output,
        ),
        build_payloads(),
        strict=True,
    ):
        _check_or_write(path.resolve(), payload, check=args.check)
    print(
        f"{'verified' if args.check else 'wrote'} Alpha v28: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={v28.EXPECTED_ALPHA_V28_COUNT}, "
        f"checked-use={v28.EXPECTED_ALPHA_V28_COUNT}, "
        f"new-constructive-theorems={FRONTIER_V28_EXPECTED_COUNT}, "
        f"unchecked=0, campaigns={len(EXPECTED_FRONTIER_CAMPAIGN_COUNTS)}, proof-bundles=1"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
