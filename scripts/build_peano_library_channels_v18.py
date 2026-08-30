#!/usr/bin/env python3
"""Seal five genuinely constructive flagship proof campaigns into Alpha v18.

Each generation decodes all five independently checked, self-contained proof
bundles and submits every ordinary local body to the unchanged intuitionistic
kernel. Alpha v17, all older releases, and Stable are immutable inputs.
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
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v17.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v17.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v17.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v17.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v18.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v18.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v18.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v18.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v13 as graph_builder  # noqa: E402
from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.library import editions_v17 as v17  # noqa: E402
from peano_lab.library import editions_v18 as v18  # noqa: E402


SCHEMA = "peano-library-alpha-snapshot-v18"
METRICS_SCHEMA = "peano-library-alpha-metrics-v18"
CHANNEL_SCHEMA = "peano-library-channels-v18"
EXPECTED_PARENT_COUNT = 1_673
EXPECTED_ALPHA_COUNT = v18.EXPECTED_ALPHA_V18_COUNT
EXPECTED_STABLE_COUNT = 432
EXPECTED_PARENT_CHECKED_USE_COUNT = 916
EXPECTED_CHECKED_USE_COUNT = v18.EXPECTED_ALPHA_V18_CHECKED_USE_COUNT
EXPECTED_EDGE_COUNT = v18.EXPECTED_ALPHA_V18_EDGE_COUNT
EXPECTED_LAYER_COUNT = v18.EXPECTED_ALPHA_V18_LAYER_COUNT
EXPECTED_PARENT_ALPHA_SHA256 = (
    "32acaae2a4dff14862469cf441e527ec1e1efbfff57974c246d603cd7a2e68d9"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "26c892fd040b72df05fc4a673ed6cd89a0d3b89dec65f7d0fb3751ed84d2e245"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "3aaae0b85b1a4f43d55967906678b8b406a6b8be374ee27ae1abf8e749b69962"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "b43c622de353f22743c06ddacb9ff85f3ad8c6e40d81dbe296f8cd928377e6cb"
)
EXPECTED_EVIDENCE_COUNTS = {
    "alpha_closed": 1_157,
    "body_checked": 84,
    "stable_closed": 432,
}
EXPECTED_OWNER_COUNTS = {
    "lucas": 74,
    "kummer": 73,
    "bertrand": 241,
    "four_square": 196,
    "two_square": 89,
}
ADMISSION_RFC = "research/arithmetic-library/alpha-v18-flagship-promotion-rfc-v1.md"
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v18_admission.py"

CAMPAIGNS: dict[str, dict[str, object]] = {
    "lucas": {
        "artifact": "research/arithmetic-library/artifacts/lucas-proof-bundle-v1.json",
        "module": "peano-lab/py/peano_lab/library/lucas_complete_closure.py",
        "receipt": "research/arithmetic-library/lucas-complete-closure-receipt.md",
        "roots": ("lucas_theorem",),
    },
    "kummer": {
        "artifact": "research/arithmetic-library/artifacts/kummer-proof-bundle-v1.json",
        "module": "peano-lab/py/peano_lab/library/kummer_complete_closure.py",
        "receipt": "research/arithmetic-library/kummer-complete-closure-receipt.md",
        "roots": (
            "kummer_binomial_carry_bit_count",
            "kummer_carry_free_iff_not_divides",
        ),
    },
    "bertrand": {
        "artifact": "research/arithmetic-library/artifacts/bertrand-proof-bundle-v1.json",
        "module": "peano-lab/py/peano_lab/library/bertrand_complete_closure.py",
        "receipt": "research/arithmetic-library/bertrand-complete-closure-receipt.md",
        "roots": ("bertrand_strict",),
    },
    "four_square": {
        "artifact": "research/arithmetic-library/artifacts/four-square-proof-bundle-v1.json",
        "module": "peano-lab/py/peano_lab/library/four_square_complete_closure.py",
        "receipt": "research/arithmetic-library/four-square-complete-closure-receipt.md",
        "roots": ("four_square_lagrange",),
    },
    "two_square": {
        "artifact": "research/arithmetic-library/artifacts/two-square-proof-bundle-v1.json",
        "module": "peano-lab/py/peano_lab/library/two_square_complete_closure.py",
        "receipt": "research/arithmetic-library/two-square-complete-closure-receipt.md",
        "roots": (
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
        ),
    },
}
CONTROL_DOCUMENTS: dict[str, str] = {
    "peano-lab/py/peano_lab/library/editions_v18.py": (
        "Fail-closed five-bundle checked-use runtime preserving Stable and Alpha v17."
    ),
    "peano-lab/py/peano_lab/library/proof_bundle.py": (
        "Canonical constructive proof codec and unchanged-kernel body checker."
    ),
    ADMISSION_RFC: "Immutable Alpha-v17 parent and exact 673-row flagship promotion.",
    ADMISSION_TEST: "Executable Stable, immutable history, proof replay, and fail-closed audit.",
}
for label, campaign in CAMPAIGNS.items():
    CONTROL_DOCUMENTS[str(campaign["artifact"])] = (
        f"Complete independently kernel-checked ordinary {label} proof bundle."
    )
    CONTROL_DOCUMENTS[str(campaign["module"])] = (
        f"Sealed {label} exact theorem graph and unchanged-kernel proof construction."
    )
    CONTROL_DOCUMENTS[str(campaign["receipt"])] = (
        f"Original-kernel and independently compiled Lean {label} verification receipt."
    )


def _digest(value: bytes | str) -> str:
    return sha256(value if isinstance(value, bytes) else value.encode("utf-8")).hexdigest()


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
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"{path} must contain a JSON object")
    return value


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
            label: {"path": _repository_path(path), "sha256": digest}
            for label, (path, digest) in artifacts.items()
        },
        "edition_identity_sha256": v17.ALPHA_V17_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": v17.ALPHA_V17_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v17",
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
            raise ValueError(f"sealed Alpha-v17 parent artifact changed: {path}")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v17"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("checked_use_count") != EXPECTED_PARENT_CHECKED_USE_COUNT
        or parent.get("ordered_enrollment_root_sha256")
        != v17.ALPHA_V17_ENROLLMENT_SHA256
        or parent.get("edition_identity_sha256") != v17.ALPHA_V17_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v17 parent catalog metadata changed")
    channels = _load(PARENT_CHANNELS)
    alpha = channels.get("channels", {}).get("alpha", {})
    if (
        channels.get("schema") != "peano-library-channels-v17"
        or channels.get("default_channel") != "stable"
        or alpha.get("checked_use_count") != EXPECTED_PARENT_CHECKED_USE_COUNT
        or alpha.get("edition_identity_sha256") != v17.ALPHA_V17_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v17 parent channels changed")


def _checked_bundles() -> dict[str, tuple[Any, Any, dict[str, int]]]:
    expected = tuple(CAMPAIGNS)
    if tuple(v18.FLAGSHIP_BUNDLE_LABELS) != expected:
        raise ValueError("Alpha-v18 canonical flagship ownership order changed")
    checked: dict[str, tuple[Any, Any, dict[str, int]]] = {}
    for label in expected:
        bundle, receipt, positions = v18._checked_flagship_bundle(label)
        for name in CAMPAIGNS[label]["roots"]:
            if name not in positions:
                raise ValueError(f"actual {label} proof bundle lacks exact root {name!r}")
        checked[label] = (bundle, receipt, positions)
    return checked


def _promotion_payload(
    bundles: dict[str, tuple[Any, Any, dict[str, int]]],
) -> dict[str, object]:
    campaigns: dict[str, dict[str, object]] = {}
    for label in v18.FLAGSHIP_BUNDLE_LABELS:
        bundle, receipt, positions = bundles[label]
        campaign = CAMPAIGNS[label]
        artifact = ROOT / str(campaign["artifact"])
        payload = artifact.read_bytes()
        campaigns[label] = {
            "artifact_bytes": len(payload),
            "artifact_path": str(campaign["artifact"]),
            "artifact_sha256": _digest(payload),
            "body_proof_nodes": receipt.total_body_nodes,
            "dependency_edges": receipt.dependency_edges,
            "kernel_calls": receipt.kernel_calls,
            "node_count": receipt.node_count,
            "promoted_count": EXPECTED_OWNER_COUNTS[label],
            "root_names": list(campaign["roots"]),
            "root_node_ids": [positions[name] for name in campaign["roots"]],
            "bundle_root_id": bundle.root,
        }
    return {
        "campaigns": campaigns,
        "campaign_order": list(v18.FLAGSHIP_BUNDLE_LABELS),
        "checked_use_after": EXPECTED_CHECKED_USE_COUNT,
        "checked_use_before": EXPECTED_PARENT_CHECKED_USE_COUNT,
        "joint_dependency_node_count": 1_113,
        "ordered_promoted_names_sha256": (
            v18.EXPECTED_ALPHA_V18_PROMOTION_NAMES_SHA256
        ),
        "promoted_count": v18.EXPECTED_ALPHA_V18_PROMOTION_COUNT,
        "root_names": list(v18.FLAGSHIP_ROOT_NAMES),
        "status": "kernel_checked_dependency_closed_graphs",
        "total_bundle_kernel_calls": sum(
            receipt.kernel_calls for _bundle, receipt, _positions in bundles.values()
        ),
    }


def _promote_row(
    parent: dict[str, Any],
    *,
    label: str,
    node_id: int,
    bundle: Any,
    receipt: Any,
    documents: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    name = str(parent["name"])
    if (
        parent.get("membership") != "alpha_only"
        or parent.get("checked_use") is not False
        or parent.get("evidence_status") != "body_checked"
    ):
        raise ValueError(f"unauthorized Alpha-v18 evidence transition for {name!r}")
    campaign = CAMPAIGNS[label]
    bundle_path = str(campaign["artifact"])
    receipt_path = str(campaign["receipt"])
    bundle_digest = documents[bundle_path]["sha256"]
    body_nodes, body_depth = proof_metrics(bundle.nodes[node_id].body)
    row = deepcopy(parent)
    row.update(
        {
            "checked_use": True,
            "empty_context_closure": {
                "body_proof_depth": body_depth,
                "body_proof_nodes": body_nodes,
                "bundle_campaign": label,
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
            "alpha_v18_promotion": {
                "bundle_campaign": label,
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
            "kind": f"{label}_self_contained_constructive_proof_bundle",
            "path": bundle_path,
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
            "document_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "kind": "sealed_alpha_v17_parent",
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
        "%% Generated by scripts/build_peano_library_channels_v18.py; do not edit.",
        1,
    )


def build_payloads() -> tuple[str, str, str, str]:
    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("sealed Alpha-v17 parent rows changed")

    bundles = _checked_bundles()
    documents = {
        path: _document(ROOT / path, role)
        for path, role in CONTROL_DOCUMENTS.items()
    }
    parent_path = _repository_path(PARENT_ALPHA)
    documents[parent_path] = _document(
        PARENT_ALPHA,
        "Exact sealed Alpha-v17 parent retained as the immutable complete theorem ledger.",
    )
    promoted = frozenset(v18.FLAGSHIP_PROMOTED_NAMES)
    observed_owners: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    for row in parent_rows:
        name = str(row["name"])
        if name not in promoted:
            rows.append(row)
            continue
        label = v18._flagship_owner(name)
        bundle, receipt, positions = bundles[label]
        rows.append(
            _promote_row(
                row,
                label=label,
                node_id=positions[name],
                bundle=bundle,
                receipt=receipt,
                documents=documents,
            )
        )
        observed_owners[label] += 1
    if observed_owners != Counter(EXPECTED_OWNER_COUNTS):
        raise ValueError(f"Alpha-v18 flagship bundle ownership changed: {observed_owners!r}")
    evidence_counts = Counter(row["evidence_status"] for row in rows)
    if (
        evidence_counts != Counter(EXPECTED_EVIDENCE_COUNTS)
        or sum(row["checked_use"] is True for row in rows)
        != EXPECTED_CHECKED_USE_COUNT
        or base._ordered_root(v18.ALPHA_ENTRIES, include_origin=True)
        != v18.ALPHA_V18_ENROLLMENT_SHA256
        or base._membership_root(rows) != parent["membership_root_sha256"]
    ):
        raise ValueError("Alpha-v18 evidence or immutable enrollment changed")
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    documents_by_path.update(documents)
    promotion = _promotion_payload(bundles)

    catalog = dict(parent)
    catalog.update(
        {
            "alpha_v18_flagship_promotion": promotion,
            "canonical_order": [
                *parent["canonical_order"],
                "Five independently closed constructive flagship Alpha-v18 campaigns (673)",
            ],
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v18.ALPHA_V18_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "ordered_enrollment_root_sha256": v18.ALPHA_V18_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": base._ordered_root(
                v18.ALPHA_ENTRIES,
                include_origin=False,
            ),
            "parent_alpha_v17": _parent_binding(),
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
        raise ValueError("Alpha-v18 changed its immutable dependency topology")
    graph = _alpha_graph(rows, kept_edges, redundant_edges)

    metrics = _load(PARENT_ALPHA_METRICS)
    metrics.update(
        {
            "alpha_v18_flagship_promotion": promotion,
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": v18.ALPHA_V18_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": v18.ALPHA_V18_ENROLLMENT_SHA256,
            "ordered_spec_root_sha256": catalog["ordered_spec_root_sha256"],
            "parent_alpha_v17": catalog["parent_alpha_v17"],
            "schema": METRICS_SCHEMA,
        }
    )
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] = (
        346 + v18.EXPECTED_ALPHA_V18_PROMOTION_COUNT
    )
    accounting.update(
        {
            "metric_bearing_theorem_count": EXPECTED_CHECKED_USE_COUNT,
            "missing_empty_context_metric_count": (
                EXPECTED_ALPHA_COUNT - EXPECTED_CHECKED_USE_COUNT
            ),
            "flagship_bundle_accounting": {
                "campaigns": promotion["campaigns"],
                "campaign_count": len(v18.FLAGSHIP_BUNDLE_LABELS),
                "promoted_checked_theorem_count": (
                    v18.EXPECTED_ALPHA_V18_PROMOTION_COUNT
                ),
                "totals_policy": (
                    "Each separately self-contained flagship artifact is checked "
                    "once; overlapping historical proof bodies remain explicitly "
                    "accounted for per artifact, never counted as distinct theorems."
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
    metrics["promotion_gates"]["five_constructive_flagships_full_dependency_closure"] = {
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
            "alpha_v18_flagship_promoted_count": v18.EXPECTED_ALPHA_V18_PROMOTION_COUNT,
            "artifact_path": _repository_path(DEFAULT_ALPHA),
            "artifact_sha256": _digest(catalog_text),
            "artifacts": artifacts,
            "checked_use_count": EXPECTED_CHECKED_USE_COUNT,
            "edition_identity_sha256": v18.ALPHA_V18_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_root_sha256": catalog["evidence_root_sha256"],
            "parent_alpha_v17_sha256": EXPECTED_PARENT_ALPHA_SHA256,
        }
    )
    channels = {
        "channels": {
            "alpha": alpha,
            "stable": parent_channels["channels"]["stable"],
        },
        "default_channel": "stable",
        "parent_channels_v17": {
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
        f"{'verified' if arguments.check else 'wrote'} Alpha v18: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"flagship-promoted={v18.EXPECTED_ALPHA_V18_PROMOTION_COUNT}, "
        f"proof-bundles={len(v18.FLAGSHIP_BUNDLE_LABELS)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
