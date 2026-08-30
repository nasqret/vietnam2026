#!/usr/bin/env python3
"""Build additive Alpha-v13 artifacts for exact Lagrange and Lucas closures.

Initial generation obtains genuine dependency-curried kernel receipts in 25
isolated factory subprocesses; no process replays the entire 240-row tranche.
Subsequent ``--check`` runs reuse those source-bound receipts unless explicitly
asked to repeat them with ``--replay-bodies``.  Stable and Alpha-v12 artifacts
are read-only sealed parents.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
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
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v12.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v12.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v12.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v12.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v13.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v13.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v13.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v13.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as base  # noqa: E402
import build_peano_library_channels_v12 as v12_builder  # noqa: E402
from peano_lab.library.alpha_enrollment_v13 import (  # noqa: E402
    FOUR_SQUARE_V13_EXPECTED_COUNT,
    FRONTIER_V13_BODY_ENROLLMENT_MANIFEST,
    FRONTIER_V13_EXPECTED_COUNT,
    FRONTIER_V13_EXPECTED_NAMES,
    FRONTIER_V13_EXPECTED_NAMES_SHA256,
    FRONTIER_V13_RFC_PATHS,
    FRONTIER_V13_ROOT_NAMES,
    FRONTIER_V13_ROOT_STATEMENT_SHA256,
    FRONTIER_V13_START_INDEX,
    LUCAS_V13_EXPECTED_COUNT,
    PARENT_ALPHA_V12_ENROLLMENT_SHA256,
    PARENT_ALPHA_V12_IDENTITY_SHA256,
    alpha_v13_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v13 import (  # noqa: E402
    ALPHA_EDITION,
    ALPHA_ENTRIES,
    ALPHA_SPECS,
    ALPHA_V13_ENROLLMENT_SHA256,
    ALPHA_V13_IDENTITY_SHA256,
    EXPECTED_ALPHA_V13_COUNT,
    EXPECTED_ALPHA_V13_EDGE_COUNT,
    EXPECTED_ALPHA_V13_LAYER_COUNT,
)


SCHEMA = "peano-library-alpha-snapshot-v13"
METRICS_SCHEMA = "peano-library-alpha-metrics-v13"
CHANNEL_SCHEMA = "peano-library-channels-v13"
EXPECTED_PARENT_COUNT = 1_303
EXPECTED_ALPHA_COUNT = EXPECTED_ALPHA_V13_COUNT
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = 570
EXPECTED_EDGE_COUNT = EXPECTED_ALPHA_V13_EDGE_COUNT
EXPECTED_LAYER_COUNT = EXPECTED_ALPHA_V13_LAYER_COUNT
EXPECTED_PARENT_ALPHA_SHA256 = (
    "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982"
)

ADMISSION_RFC = "research/arithmetic-library/alpha-v13-frontier-admission-rfc-v1.md"
ADMISSION_TEST = "peano-lab/py/tests/test_library_editions_v13_admission.py"
CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/alpha_enrollment_v13.py": (
        "Code-owned exact minimal 196+44 dependency-topological Alpha-v13 manifest."
    ),
    "peano-lab/py/peano_lab/library/editions_v13.py": (
        "Fail-closed Alpha-v13 runtime preserving Stable and checked-use boundaries."
    ),
    ADMISSION_RFC: (
        "Binding Alpha-v13 frontier scope, exact root closures, and evidence boundary."
    ),
    ADMISSION_TEST: (
        "Independent executable Alpha-v13 parent, minimal-closure, receipt, and nonpromotion audit."
    ),
    **{
        path: "Reviewed constructive campaign statement and dependency-curried trust boundary."
        for path in FRONTIER_V13_RFC_PATHS
    },
    **{
        source.test_path: (
            "Executable constructive statement, dependency, kernel-body replay, "
            f"and mutation audit for {source.module}."
        )
        for source in FRONTIER_V13_BODY_ENROLLMENT_MANIFEST
    },
}

FRONTIER_V13_EVIDENCE_BUNDLE_SCHEME = {
    "algorithm": "canonical-json-sha256",
    "fields": [
        "body_receipt_sha256",
        "campaign",
        "dependencies_sha256",
        "enrollment_origin",
        "logical_spec_sha256",
        "name",
        "parent_catalog_sha256",
        "rfc_sha256",
        "source_sha256",
        "statement_sha256",
        "test_sha256",
    ],
    "purpose": (
        "Bind every minimal Alpha-v13 frontier theorem to an actual "
        "dependency-curried kernel receipt, source, executable audit, campaign "
        "RFC, and unchanged sealed Alpha-v12 parent bytes."
    ),
}


def _digest(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return sha256(payload).hexdigest()


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
        "edition_identity_sha256": PARENT_ALPHA_V12_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": PARENT_ALPHA_V12_ENROLLMENT_SHA256,
        "schema": "peano-library-alpha-snapshot-v12",
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
            raise ValueError(f"sealed Alpha-v12 parent artifact changed: {path}")
    if (
        parent.get("schema") != "peano-library-alpha-snapshot-v12"
        or parent.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent.get("ordered_enrollment_root_sha256")
        != PARENT_ALPHA_V12_ENROLLMENT_SHA256
        or parent.get("edition_identity_sha256") != PARENT_ALPHA_V12_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v12 parent catalog metadata changed")
    channels = _load(PARENT_CHANNELS)
    parent_alpha = channels.get("channels", {}).get("alpha", {})
    if (
        channels.get("schema") != "peano-library-channels-v12"
        or parent_alpha.get("theorem_count") != EXPECTED_PARENT_COUNT
        or parent_alpha.get("ordered_enrollment_root_sha256")
        != PARENT_ALPHA_V12_ENROLLMENT_SHA256
        or parent_alpha.get("edition_identity_sha256")
        != PARENT_ALPHA_V12_IDENTITY_SHA256
    ):
        raise ValueError("sealed Alpha-v12 parent channel metadata changed")


def _receipt_payload(receipt: object) -> dict[str, object]:
    result = asdict(receipt)
    result["dne_command_count"] = 0
    result["status"] = "kernel_checked_dependency_curried_body"
    return result


def _receipt_worker(module: str) -> int:
    source = next(
        (row for row in FRONTIER_V13_BODY_ENROLLMENT_MANIFEST if row.module == module),
        None,
    )
    if source is None:
        raise SystemExit(f"unknown isolated Alpha-v13 receipt source {module!r}")
    by_name = {spec.name: spec for spec in ALPHA_SPECS}
    rows = tuple(by_name[name] for name in source.names)
    receipts = replay_candidate_bodies(rows, core=by_name)
    if tuple(receipt.name for receipt in receipts) != source.names:
        raise SystemExit(f"isolated Alpha-v13 receipt order changed for {module!r}")
    print(_compact([_receipt_payload(receipt) for receipt in receipts]))
    return 0


def _fresh_receipts() -> dict[str, dict[str, object]]:
    receipts: dict[str, dict[str, object]] = {}
    total = len(FRONTIER_V13_BODY_ENROLLMENT_MANIFEST)
    for index, source in enumerate(FRONTIER_V13_BODY_ENROLLMENT_MANIFEST, start=1):
        print(
            f"kernel-checking isolated Alpha-v13 source {index:02d}/{total}: "
            f"{source.module} ({len(source.names)} bodies)",
            file=sys.stderr,
            flush=True,
        )
        result = subprocess.run(
            [sys.executable, str(Path(__file__).resolve()), "--receipt-source", source.module],
            cwd=str(ROOT),
            capture_output=True,
            check=False,
            text=True,
        )
        if result.returncode:
            raise ValueError(
                f"isolated Alpha-v13 proof replay failed for {source.module}: "
                f"{result.stderr.strip() or result.stdout.strip()}"
            )
        payload = json.loads(result.stdout)
        if type(payload) is not list or len(payload) != len(source.names):
            raise ValueError(f"invalid isolated Alpha-v13 receipts for {source.module}")
        for receipt in payload:
            name = str(receipt.get("name"))
            if name in receipts:
                raise ValueError(f"duplicate Alpha-v13 body receipt {name!r}")
            receipts[name] = receipt
    if set(receipts) != set(FRONTIER_V13_EXPECTED_NAMES):
        raise ValueError("isolated Alpha-v13 body receipts do not cover exact closure")
    return receipts


def _cached_receipts(path: Path) -> dict[str, dict[str, object]]:
    payload = _load(path)
    rows = payload.get("theorems")
    if type(rows) is not list or len(rows) != EXPECTED_ALPHA_COUNT:
        raise ValueError("cached Alpha-v13 body receipts have wrong theorem count")
    receipts: dict[str, dict[str, object]] = {}
    specs = {spec.name: spec for spec in alpha_v13_enrollment().frontier_specs}
    for row in rows[EXPECTED_PARENT_COUNT:]:
        if type(row) is not dict:
            raise ValueError("cached Alpha-v13 theorem row is not an object")
        name = str(row.get("name"))
        spec = specs.get(name)
        receipt = row.get("body_receipt")
        if spec is None or type(receipt) is not dict:
            raise ValueError(f"cached Alpha-v13 receipt missing for {name!r}")
        if (
            receipt.get("name") != name
            or receipt.get("dependency_count") != len(spec.dependencies)
            or receipt.get("command_count") != len(spec.script)
            or receipt.get("dne_command_count") != 0
            or receipt.get("status") != "kernel_checked_dependency_curried_body"
            or not isinstance(receipt.get("proof_nodes"), int)
            or int(receipt["proof_nodes"]) <= 0
            or not isinstance(receipt.get("proof_objects"), int)
            or int(receipt["proof_objects"]) <= 0
        ):
            raise ValueError(f"cached Alpha-v13 body receipt is invalid for {name!r}")
        receipts[name] = receipt
    if set(receipts) != set(FRONTIER_V13_EXPECTED_NAMES):
        raise ValueError("cached Alpha-v13 receipts do not cover exact minimal closure")
    return receipts


def _frontier_rows(
    receipts: dict[str, dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    enrollment = alpha_v13_enrollment()
    entries = ALPHA_ENTRIES[FRONTIER_V13_START_INDEX:]
    source_documents: dict[str, dict[str, object]] = {}
    test_documents: dict[str, dict[str, object]] = {}
    rfc_documents = {
        path: _document(ROOT / path, CONTROL_DOCUMENTS[path])
        for path in FRONTIER_V13_RFC_PATHS
    }
    parent_document = _document(
        PARENT_ALPHA,
        "Exact sealed Alpha-v12 parent catalog retained as the 1,303-row prefix.",
    )
    rows: list[dict[str, object]] = []
    for offset, entry in enumerate(entries):
        spec = entry.spec
        campaign = enrollment.campaign_by_name[spec.name].value
        source_path = enrollment.source_by_name[spec.name]
        test_path = enrollment.test_by_name[spec.name]
        rfc_path = enrollment.rfc_by_name[spec.name]
        source = source_documents.setdefault(
            source_path,
            _document(
                ROOT / source_path,
                f"Constructive {campaign} Alpha-v13 candidate theorem factory.",
            ),
        )
        test = test_documents.setdefault(
            test_path,
            _document(ROOT / test_path, CONTROL_DOCUMENTS[test_path]),
        )
        rfc = rfc_documents[rfc_path]
        receipt = receipts[spec.name]
        statement_sha256 = _digest(spec.statement)
        dependencies_sha256 = _digest("\n".join(spec.dependencies) + "\n")
        logical_spec_sha256 = base._logical_spec_sha256(spec)
        bundle = {
            "body_receipt_sha256": _digest(_compact(receipt)),
            "campaign": campaign,
            "dependencies_sha256": dependencies_sha256,
            "enrollment_origin": entry.enrollment_origin.value,
            "logical_spec_sha256": logical_spec_sha256,
            "name": spec.name,
            "parent_catalog_sha256": str(parent_document["sha256"]),
            "rfc_sha256": str(rfc["sha256"]),
            "source_sha256": str(source["sha256"]),
            "statement_sha256": statement_sha256,
            "test_sha256": str(test["sha256"]),
        }
        rows.append(
            {
                "body_checked": True,
                "body_receipt": receipt,
                "checked_use": False,
                "dependencies": list(spec.dependencies),
                "dependencies_sha256": dependencies_sha256,
                "empty_context_closure": None,
                "enrollment_index": EXPECTED_PARENT_COUNT + offset,
                "enrollment_origin": entry.enrollment_origin.value,
                "evidence_links": [
                    {
                        "document_sha256": source["sha256"],
                        "kind": "frontier_dependency_curried_body",
                        "path": source_path,
                        "role": "dependency_curried_body",
                        "selector": "document",
                    },
                    {
                        "document_sha256": test["sha256"],
                        "kind": "frontier_executable_audit",
                        "path": test_path,
                        "role": "statement_dependency_replay_mutation_audit",
                        "selector": "document",
                    },
                    {
                        "document_sha256": rfc["sha256"],
                        "kind": "frontier_campaign_rfc",
                        "path": rfc_path,
                        "role": "reviewed_constructive_campaign_contract",
                        "selector": "document",
                    },
                    {
                        "document_sha256": parent_document["sha256"],
                        "kind": "sealed_alpha_v12_parent",
                        "path": _repository_path(PARENT_ALPHA),
                        "role": "exact_parent_catalog_bytes",
                        "selector": "document",
                    },
                ],
                "evidence_status": "body_checked",
                "frontier_campaign": campaign,
                "frontier_v13_evidence_bundle_sha256": _digest(_compact(bundle)),
                "logical_spec_sha256": logical_spec_sha256,
                "membership": "alpha_only",
                "name": spec.name,
                "proof_tag": None,
                "provenance": [entry.enrollment_origin.value],
                "script": list(spec.script),
                "script_sha256": _digest("\n".join(spec.script) + "\n"),
                "source": {
                    "kind": "candidate_module",
                    "path": source_path,
                    "sha256": source["sha256"],
                },
                "statement": spec.statement,
                "statement_sha256": statement_sha256,
                "summary": spec.summary,
                "summary_sha256": _digest(spec.summary),
            }
        )
    documents = [
        *source_documents.values(),
        *test_documents.values(),
        *rfc_documents.values(),
        parent_document,
    ]
    return rows, documents


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    graph = v12_builder._alpha_graph(rows, kept_edges, redundant_edges)
    return graph.replace(
        "%% Generated by scripts/build_peano_library_channels_v12.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        1,
    )


def build_payloads(
    *,
    receipt_cache: Path | None = None,
    replay_bodies: bool = False,
) -> tuple[str, str, str, str]:
    """Return exact Alpha-v13 catalog, metrics, graph, and channel payloads."""

    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("sealed Alpha-v12 parent rows changed")
    receipts = (
        _fresh_receipts()
        if replay_bodies or receipt_cache is None
        else _cached_receipts(receipt_cache)
    )
    frontier_rows, documents = _frontier_rows(receipts)
    rows = [dict(row) for row in parent_rows] + frontier_rows
    if len(rows) != EXPECTED_ALPHA_COUNT:
        raise ValueError("Alpha-v13 theorem count changed")

    evidence_counts = Counter(str(row["evidence_status"]) for row in rows)
    membership_counts = Counter(str(row["membership"]) for row in rows)
    origin_counts = Counter(str(row["enrollment_origin"]) for row in rows)
    checked_count = sum(bool(row["checked_use"]) for row in rows)
    if evidence_counts != Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=972,
        pending_layered_closure=1,
    ):
        raise ValueError(f"Alpha-v13 evidence counts changed: {evidence_counts!r}")
    if membership_counts != Counter(stable=432, alpha_only=1_111):
        raise ValueError(f"Alpha-v13 membership counts changed: {membership_counts!r}")
    expected_origins = Counter(parent["enrollment_origin_counts"])
    expected_origins["ha"] += FRONTIER_V13_EXPECTED_COUNT
    if origin_counts != expected_origins or checked_count != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("Alpha-v13 origin or checked-use boundary changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_EDGE_COUNT,
        EXPECTED_LAYER_COUNT,
    ):
        raise ValueError("Alpha-v13 runtime dependency topology changed")

    enrollment_root = base._ordered_root(ALPHA_ENTRIES, include_origin=True)
    spec_root = base._ordered_root(ALPHA_ENTRIES, include_origin=False)
    if enrollment_root != ALPHA_V13_ENROLLMENT_SHA256:
        raise ValueError("Alpha-v13 ordered runtime enrollment identity mismatch")
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    for relative, role in CONTROL_DOCUMENTS.items():
        document = _document(ROOT / relative, role)
        documents_by_path[str(document["path"])] = document
    for document in documents:
        documents_by_path[str(document["path"])] = document

    catalog = dict(parent)
    catalog.update(
        {
            "alpha_only_count": 1_111,
            "canonical_order": list(parent["canonical_order"])
            + [
                f"Lagrange minimal constructive Alpha-v13 closure ({FOUR_SQUARE_V13_EXPECTED_COUNT})",
                f"Lucas minimal constructive Alpha-v13 closure ({LUCAS_V13_EXPECTED_COUNT})",
            ],
            "checked_use_count": checked_count,
            "edge_count": EXPECTED_EDGE_COUNT,
            "edition_identity_sha256": ALPHA_V13_IDENTITY_SHA256,
            "enrollment_origin_counts": dict(sorted(origin_counts.items())),
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "evidence_documents": [
                documents_by_path[path] for path in sorted(documents_by_path)
            ],
            "evidence_root_sha256": base._evidence_root(rows),
            "frontier_v13_campaign_counts": {
                "four_square": FOUR_SQUARE_V13_EXPECTED_COUNT,
                "lucas": LUCAS_V13_EXPECTED_COUNT,
            },
            "frontier_v13_evidence_bundle_scheme": FRONTIER_V13_EVIDENCE_BUNDLE_SCHEME,
            "frontier_v13_evidence_bundle_scheme_sha256": _digest(
                _compact(FRONTIER_V13_EVIDENCE_BUNDLE_SCHEME)
            ),
            "frontier_v13_ordered_names_sha256": FRONTIER_V13_EXPECTED_NAMES_SHA256,
            "frontier_v13_roots": {
                name: FRONTIER_V13_ROOT_STATEMENT_SHA256[name]
                for name in FRONTIER_V13_ROOT_NAMES
            },
            "layer_count": EXPECTED_LAYER_COUNT,
            "membership_counts": dict(sorted(membership_counts.items())),
            "membership_root_sha256": base._membership_root(rows),
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v12": _parent_binding(),
            "schema": SCHEMA,
            "stable_count": EXPECTED_STABLE_COUNT,
            "theorem_count": len(rows),
            "theorems": rows,
        }
    )
    catalog_text = _canonical_json(catalog)

    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    if len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT:
        raise ValueError("Alpha-v13 dependency reduction lost an edge")
    if max(depths.values(), default=-1) + 1 != EXPECTED_LAYER_COUNT:
        raise ValueError("Alpha-v13 dependency layers changed")
    graph = _alpha_graph(rows, kept_edges, redundant_edges)
    reduced_dependencies = {str(row["name"]): [] for row in rows}
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
        raise ValueError("Alpha-v13 display reduction changed dependency reachability")

    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    origin_by_name = {
        str(row["name"]): str(row["enrollment_origin"]) for row in rows
    }
    redundant_by_origin = Counter(
        origin_by_name[theorem] for _dependency, theorem in redundant_edges
    )
    depth_counts = Counter(depths.values())
    metrics = _load(PARENT_ALPHA_METRICS)
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
        "reachability_reduction_scope": metrics["dependency_graph"][
            "reachability_reduction_scope"
        ],
        "theorems_by_depth": {
            str(depth): count for depth, count in sorted(depth_counts.items())
        },
        "transitive_reduction_edge_count": len(kept_edges),
        "transitive_reduction_edge_sha256": _digest(_compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True,
    }
    metrics.update(
        {
            "catalog_path": _repository_path(DEFAULT_ALPHA),
            "catalog_sha256": _digest(catalog_text),
            "checked_use_count": checked_count,
            "dependency_graph": topology,
            "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
            "dependency_graph_sha256": _digest(graph),
            "edition_identity_sha256": ALPHA_V13_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "frontier_v13_campaign_counts": catalog["frontier_v13_campaign_counts"],
            "frontier_v13_ordered_names_sha256": FRONTIER_V13_EXPECTED_NAMES_SHA256,
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v12": catalog["parent_alpha_v12"],
            "schema": METRICS_SCHEMA,
            "theorem_count": len(rows),
        }
    )
    metrics["checked_closure_metrics"]["missing_empty_context_metric_count"] = (
        len(rows) - checked_count
    )
    metrics["promotion_gates"]["canonical_topology"].update(
        theorem_count=len(rows), declared_edge_count=EXPECTED_EDGE_COUNT
    )
    metrics["promotion_gates"]["dependency_link_analysis"][
        "reachability_redundant_direct_dependency_count"
    ] = len(redundant_edges)
    metrics["promotion_gates"]["full_alpha_empty_context_compilation"].update(
        checked=checked_count,
        required=len(rows),
        missing=len(rows) - checked_count,
    )
    metrics["promotion_gates"]["source_integrity"][
        "source_bound_theorem_count"
    ] = len(rows)
    metrics_text = _canonical_json(metrics)

    parent_channels = _load(PARENT_CHANNELS)
    stable_channel = parent_channels["channels"]["stable"]
    alpha_artifacts = {
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
    channels = {
        "channels": {
            "alpha": {
                "artifact_path": _repository_path(DEFAULT_ALPHA),
                "artifact_sha256": _digest(catalog_text),
                "artifacts": alpha_artifacts,
                "checked_use_count": checked_count,
                "edition_identity_sha256": ALPHA_V13_IDENTITY_SHA256,
                "evidence_counts": dict(sorted(evidence_counts.items())),
                "evidence_root_sha256": catalog["evidence_root_sha256"],
                "frontier_v13_campaign_counts": catalog["frontier_v13_campaign_counts"],
                "membership_root_sha256": catalog["membership_root_sha256"],
                "ordered_enrollment_root_sha256": enrollment_root,
                "ordered_spec_root_sha256": spec_root,
                "parent_alpha_v12_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "theorem_count": len(rows),
            },
            "stable": stable_channel,
        },
        "default_channel": "stable",
        "parent_channels_v12": {
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
    parser.add_argument(
        "--replay-bodies",
        action="store_true",
        help="refresh genuine receipts using one isolated process per source factory",
    )
    parser.add_argument("--receipt-source", help=argparse.SUPPRESS)
    parser.add_argument("--alpha-output", type=Path, default=DEFAULT_ALPHA)
    parser.add_argument("--alpha-metrics-output", type=Path, default=DEFAULT_ALPHA_METRICS)
    parser.add_argument("--alpha-graph-output", type=Path, default=DEFAULT_ALPHA_GRAPH)
    parser.add_argument("--channels-output", type=Path, default=DEFAULT_CHANNELS)
    args = parser.parse_args(argv)
    if args.receipt_source is not None:
        return _receipt_worker(args.receipt_source)
    receipt_cache = args.alpha_output.resolve() if args.check else None
    payloads = build_payloads(
        receipt_cache=receipt_cache,
        replay_bodies=args.replay_bodies,
    )
    for path, payload in zip(
        (
            args.alpha_output,
            args.alpha_metrics_output,
            args.alpha_graph_output,
            args.channels_output,
        ),
        payloads,
        strict=True,
    ):
        _check_or_write(path.resolve(), payload, check=args.check)
    print(
        f"{'verified' if args.check else 'wrote'} Alpha v13: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"lagrange-body={FOUR_SQUARE_V13_EXPECTED_COUNT}, "
        f"lucas-body={LUCAS_V13_EXPECTED_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
