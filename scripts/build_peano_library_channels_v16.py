#!/usr/bin/env python3
"""Seal the actual 315-theorem dependency-closed quadratic-reciprocity promotion.

Every generation and deterministic check decodes every real proof body and
invokes the unchanged intuitionistic kernel 557 times. Immutable Alpha-v15 and
Stable artifacts are never rewritten.
"""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v15.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v15.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v15.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v15.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v16.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v16.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v16.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v16.json"
QR_BUNDLE = ROOT / (
    "research/arithmetic-library/artifacts/"
    "quadratic-reciprocity-proof-bundle-v1.json"
)
QR_RECEIPT = ROOT / "research/arithmetic-library/quadratic-reciprocity-closure-receipt.md"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as graph_builder  # noqa: E402
from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.library import editions_v15 as v15  # noqa: E402
from peano_lab.library import editions_v16 as v16  # noqa: E402
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME  # noqa: E402
from peano_lab.library.quadratic_reciprocity_stack_runtime import (  # noqa: E402
    quadratic_reciprocity_stack,
)


SCHEMA = "peano-library-alpha-snapshot-v16"
METRICS_SCHEMA = "peano-library-alpha-metrics-v16"
CHANNEL_SCHEMA = "peano-library-channels-v16"
EXPECTED_PARENT_COUNT = 1_673
EXPECTED_ALPHA_COUNT = v16.EXPECTED_ALPHA_V16_COUNT
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = v16.EXPECTED_ALPHA_V16_CHECKED_USE_COUNT
EXPECTED_EDGE_COUNT = v16.EXPECTED_ALPHA_V16_EDGE_COUNT
EXPECTED_LAYER_COUNT = v16.EXPECTED_ALPHA_V16_LAYER_COUNT
EXPECTED_PARENT_ALPHA_SHA256 = (
    "0123e5938f43cf67833751e2a6102d6598ac24c9be6db9a0d353ec3f55e5f32c"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "583378f0d05c38707dc755b594871b356e4665ec09b9f5cc69ea72501656e77b"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "b6e7028f5b24bde498fec5ac44c228a063062096080b1dd3bf2a52aca61aeb92"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "77fed3c5f32c28cdd91f7095086af1a551e28758d599e8b4ee73ee66aa8905ba"
)
ADMISSION_RFC = (
    "research/arithmetic-library/alpha-v16-quadratic-reciprocity-promotion-rfc-v1.md"
)
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v16_admission.py"
CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/editions_v16.py": (
        "Fail-closed Alpha-v16 actual-proof runtime preserving Stable and Alpha-v15."
    ),
    "peano-lab/py/peano_lab/library/proof_bundle.py": (
        "Canonical self-contained constructive proof codec and unchanged-kernel checker."
    ),
    "research/arithmetic-library/artifacts/quadratic-reciprocity-proof-bundle-v1.json": (
        "All 557 actual complete dependency-curried intuitionistic proof bodies."
    ),
    "research/arithmetic-library/quadratic-reciprocity-closure-receipt.md": (
        "Original empty-context root kernel check and independent compiled Lean replay."
    ),
    ADMISSION_RFC: "Immutable Alpha-v15 parent and exact 315-proof promotion contract.",
    ADMISSION_TEST: "Executable Stable, parent, proof replay, and fail-closed audit.",
}
EXPECTED_EVIDENCE_COUNTS = {
    "alpha_closed": 453,
    "body_checked": 788,
    "stable_closed": 432,
}


def _digest(value: bytes | str) -> str:
    if isinstance(value, str):
        value = value.encode("utf-8")
    return sha256(value).hexdigest()


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
    payload = path.read_bytes()
    return {
        "bytes": len(payload),
        "path": _repository_path(path),
        "role": role,
        "sha256": _digest(payload),
    }


def _parent_binding() -> dict[str, object]:
    return {
        "artifacts": {
            "catalog": {
                "path": _repository_path(PARENT_ALPHA),
                "sha256": EXPECTED_PARENT_ALPHA_SHA256,
            },
            "channels": {
                "path": _repository_path(PARENT_CHANNELS),
                "sha256": EXPECTED_PARENT_CHANNELS_SHA256,
            },
            "dependency_graph": {
                "path": _repository_path(PARENT_ALPHA_GRAPH),
                "sha256": EXPECTED_PARENT_GRAPH_SHA256,
            },
            "metrics": {
                "path": _repository_path(PARENT_ALPHA_METRICS),
                "sha256": EXPECTED_PARENT_METRICS_SHA256,
            },
        },
        "edition_identity_sha256": v15.ALPHA_V15_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": v15.ALPHA_V15_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v15",
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
            raise ValueError(f"sealed Alpha-v15 parent artifact changed: {path}")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v15"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("ordered_enrollment_root_sha256")
        != v15.ALPHA_V15_ENROLLMENT_SHA256
        or parent.get("edition_identity_sha256") != v15.ALPHA_V15_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v15 parent catalog metadata changed")
    channels = _load(PARENT_CHANNELS)
    alpha = channels.get("channels", {}).get("alpha", {})
    if (
        channels.get("schema") != "peano-library-channels-v15"
        or channels.get("default_channel") != "stable"
        or alpha.get("theorem_count") != EXPECTED_PARENT_COUNT
        or alpha.get("checked_use_count") != 570
        or alpha.get("edition_identity_sha256") != v15.ALPHA_V15_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v15 parent channel metadata changed")


def _promotion_payload(receipt: object) -> dict[str, object]:
    return {
        "body_proof_nodes": receipt.total_body_nodes,
        "bundle_bytes": v16.EXPECTED_QR_BUNDLE_BYTES,
        "bundle_path": _repository_path(QR_BUNDLE),
        "bundle_sha256": v16.EXPECTED_QR_BUNDLE_SHA256,
        "dependency_edges": receipt.dependency_edges,
        "kernel_calls": receipt.kernel_calls,
        "node_count": receipt.node_count,
        "ordered_promoted_names_sha256": (
            v16.EXPECTED_ALPHA_V16_PROMOTION_NAMES_SHA256
        ),
        "promoted_count": v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT,
        "root_name": QR_ROOT_NAME,
        "root_node_id": receipt.root,
        "root_statement_sha256": (
            "2a95f83a5a21a5e21e482d5de8a19d55ee1843f676f086438f8a9853b6a97070"
        ),
        "status": "kernel_checked_dependency_closed_graph",
    }


def _promote_row(
    parent: dict[str, Any],
    *,
    node_id: int,
    body_nodes: int,
    body_depth: int,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    name = str(parent["name"])
    if (
        parent.get("enrollment_origin") != "qr"
        or parent.get("membership") != "alpha_only"
        or parent.get("checked_use") is not False
        or parent.get("evidence_status")
        not in {"body_checked", "pending_layered_closure"}
    ):
        raise ValueError(f"unauthorized Alpha-v16 evidence transition for {name!r}")
    bundle_path = _repository_path(QR_BUNDLE)
    receipt_path = _repository_path(QR_RECEIPT)
    row = deepcopy(parent)
    row.update(
        {
            "checked_use": True,
            "empty_context_closure": {
                "body_proof_depth": body_depth,
                "body_proof_nodes": body_nodes,
                "bundle_dependency_edge_count": v16.EXPECTED_QR_BUNDLE_EDGE_COUNT,
                "bundle_node_count": v16.EXPECTED_QR_BUNDLE_NODE_COUNT,
                "bundle_node_id": node_id,
                "bundle_path": bundle_path,
                "bundle_root_id": v16.EXPECTED_QR_BUNDLE_NODE_COUNT - 1,
                "certificate_representation": "peano-lab-bundle-v1",
                "certificate_sha256": v16.EXPECTED_QR_BUNDLE_SHA256,
                "closure_kind": "dependency_closed_bundle_node",
                "digest_kind": "self-contained-proof-bundle-sha256",
                "kernel_mode": "intuitionistic",
                "node_statement_sha256": parent["statement_sha256"],
                "status": "checked",
            },
            "evidence_status": "alpha_closed",
            "alpha_v16_promotion": {
                "bundle_node_id": node_id,
                "bundle_sha256": v16.EXPECTED_QR_BUNDLE_SHA256,
                "parent_catalog_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "parent_evidence_status": parent["evidence_status"],
                "parent_row_sha256": _digest(_compact(parent)),
            },
        }
    )
    row["evidence_links"] = [
        *deepcopy(parent["evidence_links"]),
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
            "document_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v15_parent",
            "path": _repository_path(PARENT_ALPHA),
            "role": "exact_immutable_pre_promotion_catalog_bytes",
            "selector": f"theorems[name={name}]",
        },
    ]
    return row


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    graph = graph_builder._alpha_graph(rows, kept_edges, redundant_edges)
    return graph.replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v16.py; do not edit.",
        1,
    )


def build_payloads() -> tuple[str, str, str, str]:
    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("sealed Alpha-v15 parent rows changed")

    # This decodes every complete proof, validates each formula and exact edge,
    # and invokes the unchanged intuitionistic kernel once per actual body.
    bundle, receipt = v16._checked_qr_bundle()
    stack = quadratic_reciprocity_stack()
    positions = {spec.name: index for index, spec in enumerate(stack.admission_order)}
    promoted_names = frozenset(v16.QR_PROMOTED_NAMES)
    documents = {
        path: _document(ROOT / path, role)
        for path, role in CONTROL_DOCUMENTS.items()
    }
    documents[_repository_path(PARENT_ALPHA)] = _document(
        PARENT_ALPHA,
        "Exact sealed Alpha-v15 parent retained as the immutable full theorem ledger.",
    )
    rows: list[dict[str, Any]] = []
    for row in parent_rows:
        name = str(row["name"])
        if name not in promoted_names:
            rows.append(row)
            continue
        node_id = positions[name]
        body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
        rows.append(
            _promote_row(
                row,
                node_id=node_id,
                body_nodes=body_nodes,
                body_depth=body_depth,
                documents=documents,
            )
        )
    evidence_counts = Counter(row["evidence_status"] for row in rows)
    if evidence_counts != Counter(EXPECTED_EVIDENCE_COUNTS):
        raise ValueError(f"Alpha-v16 evidence partition changed: {evidence_counts!r}")
    if sum(row["checked_use"] is True for row in rows) != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("Alpha-v16 checked-use authority changed")
    if base._ordered_root(v16.ALPHA_ENTRIES, include_origin=True) != (
        v16.ALPHA_V16_ENROLLMENT_SHA256
    ):
        raise ValueError("Alpha-v16 immutable enrollment identity changed")
    if base._membership_root(rows) != parent["membership_root_sha256"]:
        raise ValueError("Alpha-v16 immutable release memberships changed")
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    documents_by_path.update(documents)
    promotion = _promotion_payload(receipt)

    catalog = dict(parent)
    catalog.update(
        {
            "alpha_v16_qr_promotion": promotion,
            "canonical_order": [
                *parent["canonical_order"],
                "Quadratic-reciprocity dependency-closed Alpha-v16 promotion (315)",
            ],
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v16.ALPHA_V16_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "ordered_enrollment_root_sha256": v16.ALPHA_V16_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": base._ordered_root(
                v16.ALPHA_ENTRIES,
                include_origin=False,
            ),
            "parent_alpha_v15": _parent_binding(),
            "schema": SCHEMA,
            "theorems": rows,
        }
    )
    catalog_text = _canonical_json(catalog)

    depths, _closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    if (
        len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT
        or max(depths.values(), default=-1) + 1 != EXPECTED_LAYER_COUNT
    ):
        raise ValueError("Alpha-v16 changed the immutable dependency topology")
    graph = _alpha_graph(rows, kept_edges, redundant_edges)

    metrics = _load(PARENT_ALPHA_METRICS)
    metrics.update(
        {
            "alpha_v16_qr_promotion": promotion,
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": v16.ALPHA_V16_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": v16.ALPHA_V16_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": catalog["ordered_spec_root_sha256"],
            "parent_alpha_v15": catalog["parent_alpha_v15"],
            "schema": METRICS_SCHEMA,
        }
    )
    closure_metrics = metrics["checked_closure_metrics"]
    closure_metrics["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] = (
        v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT
    )
    closure_metrics.update(
        {
            "metric_bearing_theorem_count": EXPECTED_CHECKED_USE_COUNT,
            "missing_empty_context_metric_count": (
                EXPECTED_ALPHA_COUNT - EXPECTED_CHECKED_USE_COUNT
            ),
            "shared_bundle_accounting": {
                "actual_body_proof_nodes": receipt.total_body_nodes,
                "actual_kernel_calls": receipt.kernel_calls,
                "bundle_count": 1,
                "dependency_edges": receipt.dependency_edges,
                "distinct_body_count": receipt.node_count,
                "ordinary_root_proof_depth": 129,
                "ordinary_root_proof_nodes": 54_870,
                "ordinary_root_proof_objects": 35_052,
                "promoted_checked_theorem_count": (
                    v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT
                ),
                "totals_policy": (
                    "Historical individual-certificate totals remain unchanged; "
                    "557 shared actual proof bodies are counted exactly once here."
                ),
            },
        }
    )
    metrics["promotion_gates"]["full_alpha_empty_context_compilation"].update(
        checked=EXPECTED_CHECKED_USE_COUNT,
        missing=EXPECTED_ALPHA_COUNT - EXPECTED_CHECKED_USE_COUNT,
        required=EXPECTED_ALPHA_COUNT,
        status="blocked",
    )
    metrics["promotion_gates"]["quadratic_reciprocity_full_dependency_closure"] = {
        **promotion,
        "checked_use_after": EXPECTED_CHECKED_USE_COUNT,
        "checked_use_before": 570,
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
            "alpha_v16_qr_promoted_count": v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT,
            "artifact_path": _repository_path(DEFAULT_ALPHA),
            "artifact_sha256": _digest(catalog_text),
            "artifacts": artifacts,
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v16.ALPHA_V16_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_root_sha256": catalog["evidence_root_sha256"],
            "parent_alpha_v15_sha256": EXPECTED_PARENT_ALPHA_SHA256,
        }
    )
    channels = {
        "channels": {
            "alpha": alpha,
            "stable": parent_channels["channels"]["stable"],
        },
        "default_channel": "stable",
        "parent_channels_v15": {
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
    arguments = parser.parse_args(argv)
    payloads = build_payloads()
    for path, payload in zip(
        (
            arguments.alpha_output,
            arguments.alpha_metrics_output,
            arguments.alpha_graph_output,
            arguments.channels_output,
        ),
        payloads,
        strict=True,
    ):
        _check_or_write(path.resolve(), payload, check=arguments.check)
    print(
        f"{'verified' if arguments.check else 'wrote'} Alpha v16: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"qr-promoted={v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT}, "
        f"actual-kernel-calls={v16.EXPECTED_QR_BUNDLE_NODE_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
