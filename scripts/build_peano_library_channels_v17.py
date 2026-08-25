#!/usr/bin/env python3
"""Seal the actual 31-theorem constructive supplementary-law promotion.

Every generation and deterministic check decodes the complete self-contained
proof bundle and asks the unchanged intuitionistic kernel to check every
theorem body and the synthetic conjunction root. Historical Alpha releases and
the default Stable edition are never rewritten.
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
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v16.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v16.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v16.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v16.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v17.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v17.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v17.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v17.json"
SUPPLEMENTARY_BUNDLE = ROOT / (
    "research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json"
)
SUPPLEMENTARY_RECEIPT = (
    ROOT / "research/arithmetic-library/supplementary-laws-closure-receipt.md"
)

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as graph_builder  # noqa: E402
from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.kernel.formulas import And  # noqa: E402
from peano_lab.library import editions_v16 as v16  # noqa: E402
from peano_lab.library import editions_v17 as v17  # noqa: E402
from peano_lab.library import supplementary_laws_closure as supplement  # noqa: E402
from peano_lab.library.proof_bundle import encode_formula  # noqa: E402
from peano_lab.library.theorems import _closed_formula  # noqa: E402


SCHEMA = "peano-library-alpha-snapshot-v17"
METRICS_SCHEMA = "peano-library-alpha-metrics-v17"
CHANNEL_SCHEMA = "peano-library-channels-v17"
EXPECTED_PARENT_COUNT = 1_673
EXPECTED_ALPHA_COUNT = v17.EXPECTED_ALPHA_V17_COUNT
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = v17.EXPECTED_ALPHA_V17_CHECKED_USE_COUNT
EXPECTED_EDGE_COUNT = v17.EXPECTED_ALPHA_V17_EDGE_COUNT
EXPECTED_LAYER_COUNT = v17.EXPECTED_ALPHA_V17_LAYER_COUNT
EXPECTED_PARENT_ALPHA_SHA256 = (
    "58838161106b118b12f2a99c0de280ed223980dd92ec9b0f842358b9d5e43a09"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "da0b82e0a9c7c29c0b338d2bf7f7fd27e7843963a1a962a09ca9009eae6f0a7d"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "eb056011b0a46ad2cb17847aaaab99d4ab8246751e1639b78f3a3f59d92e0c28"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "833f08cbf42c41f7ed0feedf20bdaafcd52e7ddb171f62f68c44fc8d7741e403"
)
ADMISSION_RFC = (
    "research/arithmetic-library/alpha-v17-supplementary-laws-promotion-rfc-v1.md"
)
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v17_admission.py"
CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/editions_v17.py": (
        "Fail-closed Alpha-v17 actual-proof replay preserving Stable and Alpha v16."
    ),
    "peano-lab/py/peano_lab/library/supplementary_laws_closure.py": (
        "Sealed supplementary dependency slice and unchanged-kernel proof construction."
    ),
    "peano-lab/py/peano_lab/library/proof_bundle.py": (
        "Canonical constructive proof codec and unchanged-kernel local-body checker."
    ),
    "research/arithmetic-library/artifacts/supplementary-laws-proof-bundle-v1.json": (
        "All exact ordinary proof bodies and the synthetic constructive conjunction."
    ),
    "research/arithmetic-library/supplementary-laws-closure-receipt.md": (
        "Actual original-kernel root checks and independent Lean proof-bundle replay."
    ),
    ADMISSION_RFC: (
        "Immutable Alpha-v16 parent and exact dependency-closed promotion contract."
    ),
    ADMISSION_TEST: (
        "Executable Stable, immutable history, proof replay, and fail-closed audit."
    ),
}
EXPECTED_EVIDENCE_COUNTS = {
    "alpha_closed": 484,
    "body_checked": 757,
    "stable_closed": 432,
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
    payload = path.read_bytes()
    return {
        "bytes": len(payload),
        "path": _repository_path(path),
        "role": role,
        "sha256": _digest(payload),
    }


def _parent_binding() -> dict[str, object]:
    artifacts = {
        "catalog": (PARENT_ALPHA, EXPECTED_PARENT_ALPHA_SHA256),
        "channels": (PARENT_CHANNELS, EXPECTED_PARENT_CHANNELS_SHA256),
        "dependency_graph": (PARENT_ALPHA_GRAPH, EXPECTED_PARENT_GRAPH_SHA256),
        "metrics": (PARENT_ALPHA_METRICS, EXPECTED_PARENT_METRICS_SHA256),
    }
    return {
        "artifacts": {
            name: {"path": _repository_path(path), "sha256": digest}
            for name, (path, digest) in artifacts.items()
        },
        "edition_identity_sha256": v16.ALPHA_V16_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": v16.ALPHA_V16_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v16",
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
            raise ValueError(f"sealed Alpha-v16 parent artifact changed: {path}")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v16"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("checked_use_count") != 885
        or parent.get("ordered_enrollment_root_sha256")
        != v16.ALPHA_V16_ENROLLMENT_SHA256
        or parent.get("edition_identity_sha256") != v16.ALPHA_V16_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v16 parent catalog metadata changed")
    channels = _load(PARENT_CHANNELS)
    alpha = channels.get("channels", {}).get("alpha", {})
    if (
        channels.get("schema") != "peano-library-channels-v16"
        or channels.get("default_channel") != "stable"
        or alpha.get("theorem_count") != EXPECTED_PARENT_COUNT
        or alpha.get("checked_use_count") != 885
        or alpha.get("edition_identity_sha256") != v16.ALPHA_V16_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v16 parent channel metadata changed")


def _slice_names() -> tuple[str, ...]:
    selected: set[str] = set()
    pending = list(v17.SUPPLEMENTARY_ROOT_NAMES)
    while pending:
        name = pending.pop()
        if name not in selected:
            selected.add(name)
            pending.extend(v16.ALPHA_EDITION.by_name[name].spec.dependencies)
    return tuple(
        item.spec.name for item in v16.ALPHA_ENTRIES if item.spec.name in selected
    )


def _checked_bundle():
    bundle, receipt = supplement.checked_supplementary_proof_bundle()
    names = _slice_names()
    positions = {name: index for index, name in enumerate(names)}
    if (
        len(names) != v17.EXPECTED_ALPHA_V17_DEPENDENCY_CLOSURE_COUNT
        or len(bundle.nodes) != len(names) + 1
        or bundle.root != len(names)
        or receipt.node_count != len(bundle.nodes)
        or receipt.kernel_calls != len(bundle.nodes)
    ):
        raise ValueError("Alpha-v17 supplementary actual proof graph changed")
    for index, name in enumerate(names):
        node = bundle.nodes[index]
        spec = v16.ALPHA_EDITION.by_name[name].spec
        if (
            node.node_id != index
            or node.target != _closed_formula(spec.statement)
            or node.dependencies
            != tuple(positions[dependency] for dependency in spec.dependencies)
        ):
            raise ValueError(
                f"Alpha-v17 proof artifact changed frozen theorem node {name!r}"
            )
    roots = tuple(positions[name] for name in v17.SUPPLEMENTARY_ROOT_NAMES)
    expected_target = And(
        _closed_formula(v16.ALPHA_EDITION.by_name[v17.SUPPLEMENTARY_ROOT_NAMES[0]].spec.statement),
        _closed_formula(v16.ALPHA_EDITION.by_name[v17.SUPPLEMENTARY_ROOT_NAMES[1]].spec.statement),
    )
    if (
        bundle.nodes[-1].node_id != bundle.root
        or bundle.nodes[-1].dependencies != roots
        or bundle.nodes[-1].target != expected_target
        or receipt.target != expected_target
    ):
        raise ValueError("Alpha-v17 synthetic conjunction root changed")
    return bundle, receipt, positions


def _promotion_payload(bundle, receipt) -> dict[str, object]:
    artifact = SUPPLEMENTARY_BUNDLE.read_bytes()
    return {
        "body_proof_nodes": receipt.total_body_nodes,
        "bundle_bytes": len(artifact),
        "bundle_path": _repository_path(SUPPLEMENTARY_BUNDLE),
        "bundle_sha256": _digest(artifact),
        "dependency_edges": receipt.dependency_edges,
        "kernel_calls": receipt.kernel_calls,
        "node_count": receipt.node_count,
        "ordered_promoted_names_sha256": (
            v17.EXPECTED_ALPHA_V17_PROMOTION_NAMES_SHA256
        ),
        "promoted_count": v17.EXPECTED_ALPHA_V17_PROMOTION_COUNT,
        "root_names": list(v17.SUPPLEMENTARY_ROOT_NAMES),
        "root_statement_sha256": [
            _digest(v16.ALPHA_EDITION.by_name[name].spec.statement)
            for name in v17.SUPPLEMENTARY_ROOT_NAMES
        ],
        "synthetic_root_id": bundle.root,
        "synthetic_root_formula_sha256": _digest(
            _compact(encode_formula(bundle.nodes[bundle.root].target))
        ),
        "status": "kernel_checked_dependency_closed_graph",
    }


def _promote_row(
    parent: dict[str, Any],
    *,
    node_id: int,
    bundle,
    receipt,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    name = str(parent["name"])
    if (
        parent.get("membership") != "alpha_only"
        or parent.get("enrollment_origin") not in {"bertrand", "ha"}
        or parent.get("checked_use") is not False
        or parent.get("evidence_status") != "body_checked"
    ):
        raise ValueError(f"unauthorized Alpha-v17 evidence transition for {name!r}")
    bundle_path = _repository_path(SUPPLEMENTARY_BUNDLE)
    receipt_path = _repository_path(SUPPLEMENTARY_RECEIPT)
    bundle_digest = documents[bundle_path]["sha256"]
    body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
    row = deepcopy(parent)
    row.update(
        {
            "checked_use": True,
            "empty_context_closure": {
                "body_proof_depth": body_depth,
                "body_proof_nodes": body_nodes,
                "bundle_dependency_edge_count": receipt.dependency_edges,
                "bundle_node_count": receipt.node_count,
                "bundle_node_id": node_id,
                "bundle_path": bundle_path,
                "bundle_root_id": bundle.root,
                "certificate_representation": "peano-lab-bundle-v1",
                "certificate_sha256": bundle_digest,
                "closure_kind": "dependency_closed_bundle_node",
                "digest_kind": "self-contained-proof-bundle-sha256",
                "kernel_mode": "intuitionistic",
                "node_statement_sha256": parent["statement_sha256"],
                "status": "checked",
            },
            "evidence_status": "alpha_closed",
            "alpha_v17_promotion": {
                "bundle_node_id": node_id,
                "bundle_sha256": bundle_digest,
                "parent_catalog_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "parent_evidence_status": parent["evidence_status"],
                "parent_row_sha256": _digest(_compact(parent)),
            },
        }
    )
    row["evidence_links"] = [
        *deepcopy(parent["evidence_links"]),
        {
            "document_sha256": bundle_digest,
            "kind": "supplementary_self_contained_constructive_proof_bundle",
            "path": bundle_path,
            "role": "independently_kernel_checked_dependency_closed_proof",
            "selector": f"nodes[id={node_id}]",
        },
        {
            "document_sha256": documents[receipt_path]["sha256"],
            "kind": "supplementary_ordinary_empty_context_closure_receipt",
            "path": receipt_path,
            "role": "original_kernel_endpoint_and_independent_lean_verification",
            "selector": "document",
        },
        {
            "document_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v16_parent",
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
    return graph_builder._alpha_graph(rows, kept_edges, redundant_edges).replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v17.py; do not edit.",
        1,
    )


def build_payloads() -> tuple[str, str, str, str]:
    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("sealed Alpha-v16 parent rows changed")

    bundle, receipt, positions = _checked_bundle()
    promoted = frozenset(v17.SUPPLEMENTARY_PROMOTED_NAMES)
    documents = {
        path: _document(ROOT / path, role)
        for path, role in CONTROL_DOCUMENTS.items()
    }
    documents[_repository_path(PARENT_ALPHA)] = _document(
        PARENT_ALPHA,
        "Exact sealed Alpha-v16 parent retained as the immutable theorem ledger.",
    )
    rows = [
        _promote_row(
            row,
            node_id=positions[str(row["name"])],
            bundle=bundle,
            receipt=receipt,
            documents=documents,
        )
        if str(row["name"]) in promoted
        else row
        for row in parent_rows
    ]
    evidence_counts = Counter(row["evidence_status"] for row in rows)
    if (
        evidence_counts != Counter(EXPECTED_EVIDENCE_COUNTS)
        or sum(row["checked_use"] is True for row in rows)
        != EXPECTED_CHECKED_USE_COUNT
        or base._ordered_root(v17.ALPHA_ENTRIES, include_origin=True)
        != v17.ALPHA_V17_ENROLLMENT_SHA256
        or base._membership_root(rows) != parent["membership_root_sha256"]
    ):
        raise ValueError("Alpha-v17 evidence or immutable enrollment changed")
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    documents_by_path.update(documents)
    promotion = _promotion_payload(bundle, receipt)

    catalog = dict(parent)
    catalog.update(
        {
            "alpha_v17_supplementary_promotion": promotion,
            "canonical_order": [
                *parent["canonical_order"],
                "Supplementary-law dependency-closed Alpha-v17 promotion (31)",
            ],
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v17.ALPHA_V17_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "ordered_enrollment_root_sha256": v17.ALPHA_V17_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": base._ordered_root(
                v17.ALPHA_ENTRIES,
                include_origin=False,
            ),
            "parent_alpha_v16": _parent_binding(),
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
        raise ValueError("Alpha v17 changed its immutable dependency topology")
    graph = _alpha_graph(rows, kept_edges, redundant_edges)

    metrics = _load(PARENT_ALPHA_METRICS)
    metrics.update(
        {
            "alpha_v17_supplementary_promotion": promotion,
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": v17.ALPHA_V17_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": v17.ALPHA_V17_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": catalog["ordered_spec_root_sha256"],
            "parent_alpha_v16": catalog["parent_alpha_v16"],
            "schema": METRICS_SCHEMA,
        }
    )
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] = (
        v16.EXPECTED_ALPHA_V16_PROMOTION_COUNT
        + v17.EXPECTED_ALPHA_V17_PROMOTION_COUNT
    )
    accounting.update(
        {
            "metric_bearing_theorem_count": EXPECTED_CHECKED_USE_COUNT,
            "missing_empty_context_metric_count": (
                EXPECTED_ALPHA_COUNT - EXPECTED_CHECKED_USE_COUNT
            ),
            "supplementary_bundle_accounting": {
                "actual_body_proof_nodes": receipt.total_body_nodes,
                "actual_kernel_calls": receipt.kernel_calls,
                "bundle_count": 1,
                "dependency_edges": receipt.dependency_edges,
                "distinct_body_count": receipt.node_count,
                "promoted_checked_theorem_count": (
                    v17.EXPECTED_ALPHA_V17_PROMOTION_COUNT
                ),
                "reused_alpha_v16_checked_body_count": 406,
                "synthetic_conjunction_root_count": 1,
                "totals_policy": (
                    "Historical quadratic-reciprocity accounting is retained "
                    "unchanged; every supplementary artifact body is counted "
                    "once within this separately self-contained artifact."
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
    metrics["promotion_gates"]["quadratic_supplementary_laws_full_dependency_closure"] = {
        **promotion,
        "checked_use_after": EXPECTED_CHECKED_USE_COUNT,
        "checked_use_before": v16.EXPECTED_ALPHA_V16_CHECKED_USE_COUNT,
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
            "alpha_v17_supplementary_promoted_count": (
                v17.EXPECTED_ALPHA_V17_PROMOTION_COUNT
            ),
            "artifact_path": _repository_path(DEFAULT_ALPHA),
            "artifact_sha256": _digest(catalog_text),
            "artifacts": artifacts,
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v17.ALPHA_V17_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_root_sha256": catalog["evidence_root_sha256"],
            "parent_alpha_v16_sha256": EXPECTED_PARENT_ALPHA_SHA256,
        }
    )
    channels = {
        "channels": {
            "alpha": alpha,
            "stable": parent_channels["channels"]["stable"],
        },
        "default_channel": "stable",
        "parent_channels_v16": {
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
        f"{'verified' if arguments.check else 'wrote'} Alpha v17: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"supplementary-promoted={v17.EXPECTED_ALPHA_V17_PROMOTION_COUNT}, "
        "actual-kernel-calls=438"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
