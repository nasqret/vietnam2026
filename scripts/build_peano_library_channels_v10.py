#!/usr/bin/env python3
"""Build additive Alpha-v10 artifacts for nine Bertrand B4 candidates."""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v9.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v9.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v9.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v9.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v10.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v10.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v10.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v10.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels_v9 as v9_builder  # noqa: E402
import verify_peano_library_channels_v9 as v9_verifier  # noqa: E402
from peano_lab.library.alpha_enrollment_v10 import (  # noqa: E402
    BERTRAND_RFC_PATHS,
    BERTRAND_V10_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_V10_EXPECTED_COUNT,
    BERTRAND_V10_START_INDEX,
    alpha_v10_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v10 import (  # noqa: E402
    ALPHA_EDITION,
    ALPHA_ENTRIES,
    ALPHA_V10_ENROLLMENT_SHA256,
    ALPHA_V10_IDENTITY_SHA256,
    EXPECTED_ALPHA_V10_EDGE_COUNT,
    EXPECTED_ALPHA_V10_LAYER_COUNT,
)


SCHEMA = "peano-library-alpha-snapshot-v10"
METRICS_SCHEMA = "peano-library-alpha-metrics-v10"
CHANNEL_SCHEMA = "peano-library-channels-v10"
EXPECTED_PARENT_COUNT = 1076
EXPECTED_ALPHA_COUNT = 1085
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = 570
EXPECTED_EDGE_COUNT = EXPECTED_ALPHA_V10_EDGE_COUNT
EXPECTED_LAYER_COUNT = EXPECTED_ALPHA_V10_LAYER_COUNT
EXPECTED_PARENT_ALPHA_SHA256 = (
    "74ab887e9eef3e3fc583b103f392f4e06125cb14a561765373677eb57f830eda"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "7397959a4dad4e1d42e6a108156c84666b4cd4f95e07e573d1fcf402f83c2d65"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "03b803080cd082642adeb2a89b62ab369c7e69aca4c4dfe90b327ef94c389ab9"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "77fd0ba0ad1ba461432384c3330041a3dfc641dc84121982eb08456ee2de9a34"
)
EXPECTED_PARENT_ENROLLMENT_ROOT = (
    "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f"
)
EXPECTED_PARENT_IDENTITY = (
    "b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80"
)

CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/alpha_enrollment_v10.py": (
        "Code-owned Alpha-v10 append manifest and exact 1+8 row order."
    ),
    "peano-lab/py/peano_lab/library/editions_v10.py": (
        "Fail-closed Alpha-v10 runtime separating body evidence from checked use."
    ),
    **{
        path: "Binding Primorial tranche statement, trust boundary, and gates."
        for path in BERTRAND_RFC_PATHS
    },
    **{
        source.test_path: (
            "Executable statement, dependency, kernel replay, closure, and "
            f"mutation audit for {source.module}."
        )
        for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    },
}

BERTRAND_V10_EVIDENCE_BUNDLE_SCHEME = {
    "algorithm": "canonical-json-sha256",
    "fields": [
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
        "Cross-bind each Alpha-v10 theorem specification to exact source, "
        "executable audit, campaign RFC, and sealed Alpha-v9 parent bytes."
    ),
}


def _digest(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return sha256(payload).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


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


def _body_receipt(receipt: object) -> dict[str, object]:
    result = asdict(receipt)
    result["dne_command_count"] = 0
    result["status"] = "kernel_checked_dependency_curried_body"
    return result


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
        "edition_identity_sha256": EXPECTED_PARENT_IDENTITY,
        "ordered_enrollment_root_sha256": EXPECTED_PARENT_ENROLLMENT_ROOT,
        "schema": "peano-library-alpha-snapshot-v9",
        "theorem_count": EXPECTED_PARENT_COUNT,
    }


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    graph = v9_builder._alpha_graph(rows, kept_edges, redundant_edges)
    return graph.replace(
        "%% Generated by scripts/build_peano_library_channels_v9.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v10.py; do not edit.",
        1,
    )


def _validate_parent(parent: dict[str, Any]) -> None:
    expected_files = {
        PARENT_ALPHA: EXPECTED_PARENT_ALPHA_SHA256,
        PARENT_ALPHA_METRICS: EXPECTED_PARENT_METRICS_SHA256,
        PARENT_ALPHA_GRAPH: EXPECTED_PARENT_GRAPH_SHA256,
        PARENT_CHANNELS: EXPECTED_PARENT_CHANNELS_SHA256,
    }
    for path, expected in expected_files.items():
        if _digest(path.read_bytes()) != expected:
            raise ValueError(
                f"Alpha v9 parent artifact changed: {_repository_path(path)}"
            )
    if parent.get("schema") != "peano-library-alpha-snapshot-v9":
        raise ValueError("Alpha v9 parent schema changed")
    if parent.get("theorem_count") != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v9 parent count changed")
    if parent.get("ordered_enrollment_root_sha256") != (
        EXPECTED_PARENT_ENROLLMENT_ROOT
    ):
        raise ValueError("Alpha v9 parent enrollment root changed")
    if parent.get("edition_identity_sha256") != EXPECTED_PARENT_IDENTITY:
        raise ValueError("Alpha v9 parent edition identity changed")
    result = v9_verifier.validate_channels_v9(
        ROOT,
        PARENT_ALPHA,
        PARENT_ALPHA_METRICS,
        PARENT_ALPHA_GRAPH,
        PARENT_CHANNELS,
        replay_bodies=False,
    )
    if result != {
        "alpha": 1076,
        "alpha_closed": 138,
        "bertrand_replayed": 0,
        "body_checked": 505,
        "checked_use": 570,
        "stable": 432,
    }:
        raise ValueError("sealed Alpha v9 parent validation changed")


def _bundle_payload(
    *,
    name: str,
    origin: str,
    statement_sha256: str,
    dependencies_sha256: str,
    logical_spec_sha256: str,
    source_sha256: str,
    test_sha256: str,
    rfc_sha256: str,
    parent_catalog_sha256: str,
) -> dict[str, str]:
    return {
        "dependencies_sha256": dependencies_sha256,
        "enrollment_origin": origin,
        "logical_spec_sha256": logical_spec_sha256,
        "name": name,
        "parent_catalog_sha256": parent_catalog_sha256,
        "rfc_sha256": rfc_sha256,
        "source_sha256": source_sha256,
        "statement_sha256": statement_sha256,
        "test_sha256": test_sha256,
    }


def _bertrand_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    enrollment = alpha_v10_enrollment()
    entries = ALPHA_ENTRIES[BERTRAND_V10_START_INDEX:]
    core = {
        entry.spec.name: entry.spec
        for entry in ALPHA_ENTRIES[:BERTRAND_V10_START_INDEX]
    }
    receipts = replay_candidate_bodies(
        tuple(entry.spec for entry in entries),
        core=core,
    )
    receipt_by_name = {
        receipt.name: _body_receipt(receipt) for receipt in receipts
    }
    source_documents: dict[str, dict[str, object]] = {}
    test_documents: dict[str, dict[str, object]] = {}
    rfc_documents = {
        path: _document(ROOT / path, CONTROL_DOCUMENTS[path])
        for path in BERTRAND_RFC_PATHS
    }
    parent_document = _document(
        PARENT_ALPHA,
        "Sealed Alpha-v9 catalog whose exact 1,076-row ledger is the v10 prefix.",
    )
    rows: list[dict[str, object]] = []
    base = (
        v9_builder.v8_builder.v7_builder.v6_builder.v5_builder.v4_builder
        .v3_builder.v2_builder.v1
    )
    for offset, entry in enumerate(entries):
        spec = entry.spec
        origin = entry.enrollment_origin.value
        source_path = enrollment.source_by_name[spec.name]
        test_path = enrollment.test_by_name[spec.name]
        rfc_path = enrollment.rfc_by_name[spec.name]
        rfc_document = rfc_documents[rfc_path]
        source_document = source_documents.setdefault(
            source_path,
            _document(
                ROOT / source_path,
                "Theorem factory source for a reviewed Bertrand-v10 body block.",
            ),
        )
        test_document = test_documents.setdefault(
            test_path,
            _document(ROOT / test_path, CONTROL_DOCUMENTS[test_path]),
        )
        dependencies_sha256 = _digest("\n".join(spec.dependencies) + "\n")
        logical_spec_sha256 = base._logical_spec_sha256(spec)
        statement_sha256 = _digest(spec.statement)
        bundle = _bundle_payload(
            name=spec.name,
            origin=origin,
            statement_sha256=statement_sha256,
            dependencies_sha256=dependencies_sha256,
            logical_spec_sha256=logical_spec_sha256,
            source_sha256=str(source_document["sha256"]),
            test_sha256=str(test_document["sha256"]),
            rfc_sha256=str(rfc_document["sha256"]),
            parent_catalog_sha256=str(parent_document["sha256"]),
        )
        rows.append(
            {
                "bertrand_v10_evidence_bundle_sha256": _digest(_compact(bundle)),
                "body_checked": True,
                "body_receipt": receipt_by_name[spec.name],
                "checked_use": False,
                "dependencies": list(spec.dependencies),
                "dependencies_sha256": dependencies_sha256,
                "empty_context_closure": None,
                "enrollment_origin": origin,
                "enrollment_index": EXPECTED_PARENT_COUNT + offset,
                "evidence_links": [
                    {
                        "document_sha256": source_document["sha256"],
                        "kind": "bertrand_dependency_curried_body",
                        "path": source_path,
                        "role": "dependency_curried_body",
                        "selector": "document",
                    },
                    {
                        "document_sha256": test_document["sha256"],
                        "kind": "bertrand_executable_audit",
                        "path": test_path,
                        "role": "statement_dependency_replay_mutation_audit",
                        "selector": "document",
                    },
                    {
                        "document_sha256": rfc_document["sha256"],
                        "kind": "bertrand_campaign_rfc",
                        "path": rfc_path,
                        "role": "reviewed_campaign_contract",
                        "selector": "document",
                    },
                    {
                        "document_sha256": parent_document["sha256"],
                        "kind": "sealed_alpha_v9_parent",
                        "path": _repository_path(PARENT_ALPHA),
                        "role": "exact_parent_catalog_bytes",
                        "selector": "document",
                    },
                ],
                "evidence_status": "body_checked",
                "logical_spec_sha256": logical_spec_sha256,
                "membership": "alpha_only",
                "name": spec.name,
                "proof_tag": None,
                "provenance": [origin],
                "script": list(spec.script),
                "script_sha256": _digest("\n".join(spec.script) + "\n"),
                "source": {
                    "kind": "candidate_module",
                    "path": source_path,
                    "sha256": source_document["sha256"],
                },
                "statement": spec.statement,
                "statement_sha256": statement_sha256,
                "summary": spec.summary,
                "summary_sha256": _digest(spec.summary),
            }
        )
    if len(rows) != BERTRAND_V10_EXPECTED_COUNT:
        raise ValueError("Bertrand v10 append count changed")
    documents = [
        *source_documents.values(),
        *test_documents.values(),
        *rfc_documents.values(),
        parent_document,
    ]
    return rows, documents


def build_payloads() -> tuple[str, str, str, str]:
    """Return deterministic Alpha-v10 catalog, metrics, graph, and channels."""

    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v9 parent theorem rows changed")
    appended, tranche_documents = _bertrand_rows()
    rows = [dict(row) for row in parent_rows] + appended
    if len(rows) != EXPECTED_ALPHA_COUNT:
        raise ValueError("Alpha v10 theorem count changed")

    evidence_counts = Counter(str(row["evidence_status"]) for row in rows)
    membership_counts = Counter(str(row["membership"]) for row in rows)
    origin_counts = Counter(str(row["enrollment_origin"]) for row in rows)
    checked_count = sum(bool(row["checked_use"]) for row in rows)
    if evidence_counts != Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=514,
        pending_layered_closure=1,
    ):
        raise ValueError(f"Alpha v10 evidence counts changed: {evidence_counts!r}")
    if membership_counts != Counter(stable=432, alpha_only=653):
        raise ValueError(f"Alpha v10 membership counts changed: {membership_counts!r}")
    expected_origins = Counter(parent["enrollment_origin_counts"])
    expected_origins["bertrand"] += BERTRAND_V10_EXPECTED_COUNT
    if origin_counts != expected_origins:
        raise ValueError(f"Alpha v10 origin counts changed: {origin_counts!r}")
    if checked_count != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("Alpha v10 checked-use count changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_EDGE_COUNT,
        EXPECTED_LAYER_COUNT,
    ):
        raise ValueError("Alpha v10 runtime topology changed")

    base = (
        v9_builder.v8_builder.v7_builder.v6_builder.v5_builder.v4_builder
        .v3_builder.v2_builder.v1
    )
    enrollment_root = base._ordered_root(ALPHA_ENTRIES, include_origin=True)
    spec_root = base._ordered_root(ALPHA_ENTRIES, include_origin=False)
    if enrollment_root != ALPHA_V10_ENROLLMENT_SHA256:
        raise ValueError("Alpha v10 runtime enrollment root mismatch")

    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    for relative, role in CONTROL_DOCUMENTS.items():
        document = _document(ROOT / relative, role)
        documents_by_path[str(document["path"])] = document
    for document in tranche_documents:
        documents_by_path[str(document["path"])] = document

    catalog = {
        "alpha_only_count": 653,
        "bertrand_v10_evidence_bundle_scheme": BERTRAND_V10_EVIDENCE_BUNDLE_SCHEME,
        "bertrand_v10_evidence_bundle_scheme_sha256": _digest(
            _compact(BERTRAND_V10_EVIDENCE_BUNDLE_SCHEME)
        ),
        "canonical_order": list(parent["canonical_order"])
        + [
            "Bertrand B4 Primorial interval splitting (1+8)",
        ],
        "channel": "alpha",
        "checked_use_count": checked_count,
        "edge_count": EXPECTED_EDGE_COUNT,
        "edition_identity_sha256": ALPHA_V10_IDENTITY_SHA256,
        "enrollment_origin_counts": dict(sorted(origin_counts.items())),
        "enrollment_policy": parent["enrollment_policy"],
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "evidence_documents": [
            documents_by_path[path] for path in sorted(documents_by_path)
        ],
        "evidence_policy": parent["evidence_policy"],
        "evidence_root_sha256": base._evidence_root(rows),
        "layer_count": EXPECTED_LAYER_COUNT,
        "membership_counts": dict(sorted(membership_counts.items())),
        "membership_root_sha256": base._membership_root(rows),
        "ordered_enrollment_root_scheme": base.ORDERED_ENROLLMENT_ROOT_SCHEME,
        "ordered_enrollment_root_scheme_sha256": _digest(
            _compact(base.ORDERED_ENROLLMENT_ROOT_SCHEME)
        ),
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_spec_root_sha256": spec_root,
        "parent_alpha_v9": _parent_binding(),
        "promotion_model": parent["promotion_model"],
        "schema": SCHEMA,
        "stable_count": EXPECTED_STABLE_COUNT,
        "stable_snapshot": parent["stable_snapshot"],
        "theorem_count": len(rows),
        "theorems": rows,
    }
    catalog_text = _canonical_json(catalog)

    depths, closures, kept_edges, redundant_edges = base._dependency_analysis(rows)
    if len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT:
        raise ValueError("Alpha v10 dependency analysis lost an edge")
    if max(depths.values(), default=-1) + 1 != EXPECTED_LAYER_COUNT:
        raise ValueError("Alpha v10 dependency layer count changed")
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
        raise ValueError("Alpha v10 display reduction changed reachability")

    metrics = _load(PARENT_ALPHA_METRICS)
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
        origin_by_name[theorem] for _, theorem in redundant_edges
    )
    depth_counts = Counter(depths.values())
    topology = {
        "declared_edge_count": EXPECTED_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": EXPECTED_LAYER_COUNT,
        "maximum_direct_dependency_count": max(
            len(row["dependencies"]) for row in rows
        ),
        "maximum_transitive_dependency_count": max(
            map(len, closures.values()), default=0
        ),
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
            "edition_identity_sha256": ALPHA_V10_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v9": catalog["parent_alpha_v9"],
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
                "artifacts": alpha_artifacts,
                "artifact_path": _repository_path(DEFAULT_ALPHA),
                "artifact_sha256": _digest(catalog_text),
                "checked_use_count": checked_count,
                "edition_identity_sha256": ALPHA_V10_IDENTITY_SHA256,
                "evidence_counts": dict(sorted(evidence_counts.items())),
                "evidence_root_sha256": catalog["evidence_root_sha256"],
                "membership_root_sha256": catalog["membership_root_sha256"],
                "ordered_enrollment_root_sha256": enrollment_root,
                "ordered_spec_root_sha256": spec_root,
                "parent_alpha_v9_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "theorem_count": len(rows),
            },
            "stable": stable_channel,
        },
        "default_channel": "stable",
        "parent_channels_v9": {
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
    parser.add_argument(
        "--alpha-metrics-output", type=Path, default=DEFAULT_ALPHA_METRICS
    )
    parser.add_argument("--alpha-graph-output", type=Path, default=DEFAULT_ALPHA_GRAPH)
    parser.add_argument("--channels-output", type=Path, default=DEFAULT_CHANNELS)
    args = parser.parse_args(argv)
    payloads = build_payloads()
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
        f"{'verified' if args.check else 'wrote'} Alpha v10: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"Bertrand-body={BERTRAND_V10_EXPECTED_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
