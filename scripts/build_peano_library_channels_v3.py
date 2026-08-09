#!/usr/bin/env python3
"""Build the additive Alpha-v3 artifacts for the first Bertrand tranche.

The committed Alpha-v2 family is an exact parent.  Its 902 theorem rows are
copied unchanged, then twenty-one reviewed Bertrand rows are appended in the
order B0 interval, B1 power order, B1 power growth, B2 bounded valuation.
Every appended row is independently replayed as a dependency-curried body
and remains unavailable for checked theorem use.
"""

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
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v2.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v2.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v2.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels-v2.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v3.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v3.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v3.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v3.json"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels_v2 as v2_builder  # noqa: E402
from peano_lab.library.alpha_enrollment_v3 import (  # noqa: E402
    BERTRAND_BODY_ENROLLMENT_MANIFEST,
    BERTRAND_EXPECTED_COUNT,
    BERTRAND_RFC_PATH,
    BERTRAND_START_INDEX,
    alpha_v3_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v3 import (  # noqa: E402
    ALPHA_EDITION,
    ALPHA_ENTRIES,
    ALPHA_V3_ENROLLMENT_SHA256,
    ALPHA_V3_IDENTITY_SHA256,
)


SCHEMA = "peano-library-alpha-snapshot-v3"
METRICS_SCHEMA = "peano-library-alpha-metrics-v3"
CHANNEL_SCHEMA = "peano-library-channels-v3"
EXPECTED_PARENT_COUNT = 902
EXPECTED_ALPHA_COUNT = 923
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = 570
EXPECTED_EDGE_COUNT = 2730
EXPECTED_LAYER_COUNT = 45
EXPECTED_PARENT_ALPHA_SHA256 = (
    "90ac4942df043e59ade7a62a87627ef3b29d9b1d7d251c8fa6aadefe77590bd7"
)
EXPECTED_PARENT_METRICS_SHA256 = (
    "85907aea9e6fece33c8f4d0d40d167945f3118190654a32423dc815df8fc69eb"
)
EXPECTED_PARENT_GRAPH_SHA256 = (
    "01ca3e6b58e55cfefd4a0df3f8ce229f5382c26a02f4960ceb7773205c9177a3"
)
EXPECTED_PARENT_CHANNELS_SHA256 = (
    "c2af6774ea7c787532d79a5f8fd41087ae5f31a0e828e25571adaed2853aa968"
)
EXPECTED_PARENT_ENROLLMENT_ROOT = (
    "00f1a70a0911c44acd6b784f2b121b2c351ae626a0f18bb08b5a829496ad40fe"
)
EXPECTED_PARENT_IDENTITY = (
    "aadf99c0e411fcefe34285c8396ff0652f590e6990f0d55c3e6c7b728f9b43a4"
)

CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/alpha_enrollment_v3.py": (
        "Code-owned Alpha-v3 append manifest and exact Bertrand tranche order."
    ),
    "peano-lab/py/peano_lab/library/editions_v3.py": (
        "Fail-closed Alpha-v3 runtime separating body evidence from checked use."
    ),
    BERTRAND_RFC_PATH: (
        "Binding native Bertrand campaign statement, trust boundary, and tranche gates."
    ),
    **{
        source.test_path: (
            f"Executable statement, dependency, kernel replay, and mutation audit for {source.origin.value}."
        )
        for source in BERTRAND_BODY_ENROLLMENT_MANIFEST
    },
}

BERTRAND_EVIDENCE_BUNDLE_SCHEME = {
    "algorithm": "canonical-json-sha256",
    "fields": [
        "dependencies_sha256",
        "enrollment_origin",
        "logical_spec_sha256",
        "name",
        "rfc_sha256",
        "source_sha256",
        "statement_sha256",
        "test_sha256",
    ],
    "purpose": (
        "Cross-bind each Bertrand theorem specification to exact factory, "
        "executable audit, and campaign RFC bytes."
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
        "schema": "peano-library-alpha-snapshot-v2",
        "theorem_count": EXPECTED_PARENT_COUNT,
    }


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    graph = v2_builder.v1._alpha_graph(rows, kept_edges, redundant_edges)
    return graph.replace(
        "%% Generated by scripts/build_peano_library_channels.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v3.py; do not edit.",
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
            raise ValueError(f"Alpha v2 parent artifact changed: {_repository_path(path)}")
    if parent.get("schema") != "peano-library-alpha-snapshot-v2":
        raise ValueError("Alpha v2 parent schema changed")
    if parent.get("theorem_count") != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v2 parent count changed")
    if parent.get("ordered_enrollment_root_sha256") != EXPECTED_PARENT_ENROLLMENT_ROOT:
        raise ValueError("Alpha v2 parent enrollment root changed")
    if parent.get("edition_identity_sha256") != EXPECTED_PARENT_IDENTITY:
        raise ValueError("Alpha v2 parent edition identity changed")
    generated = v2_builder.build_payloads()
    committed = tuple(
        path.read_text(encoding="utf-8")
        for path in (
            PARENT_ALPHA,
            PARENT_ALPHA_METRICS,
            PARENT_ALPHA_GRAPH,
            PARENT_CHANNELS,
        )
    )
    if generated != committed:
        raise ValueError("committed Alpha v2 artifact family is stale")


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
) -> dict[str, str]:
    return {
        "dependencies_sha256": dependencies_sha256,
        "enrollment_origin": origin,
        "logical_spec_sha256": logical_spec_sha256,
        "name": name,
        "rfc_sha256": rfc_sha256,
        "source_sha256": source_sha256,
        "statement_sha256": statement_sha256,
        "test_sha256": test_sha256,
    }


def _bertrand_rows() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    enrollment = alpha_v3_enrollment()
    entries = ALPHA_ENTRIES[BERTRAND_START_INDEX:]
    core = {
        entry.spec.name: entry.spec
        for entry in ALPHA_ENTRIES[:BERTRAND_START_INDEX]
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
    rfc_document = _document(
        ROOT / BERTRAND_RFC_PATH,
        CONTROL_DOCUMENTS[BERTRAND_RFC_PATH],
    )
    rows: list[dict[str, object]] = []
    for offset, entry in enumerate(entries):
        spec = entry.spec
        origin = entry.enrollment_origin.value
        source_path = enrollment.source_by_name[spec.name]
        test_path = enrollment.test_by_name[spec.name]
        source_document = source_documents.setdefault(
            source_path,
            _document(
                ROOT / source_path,
                f"Theorem factory source for {origin} dependency-curried bodies.",
            ),
        )
        test_document = test_documents.setdefault(
            test_path,
            _document(ROOT / test_path, CONTROL_DOCUMENTS[test_path]),
        )
        dependencies_sha256 = _digest("\n".join(spec.dependencies) + "\n")
        logical_spec_sha256 = v2_builder.v1._logical_spec_sha256(spec)
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
        )
        rows.append(
            {
                "bertrand_evidence_bundle_sha256": _digest(_compact(bundle)),
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
                        "path": BERTRAND_RFC_PATH,
                        "role": "reviewed_campaign_contract",
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
    if len(rows) != BERTRAND_EXPECTED_COUNT:
        raise ValueError("Bertrand append count changed")
    documents = [
        *source_documents.values(),
        *test_documents.values(),
        rfc_document,
    ]
    return rows, documents


def build_payloads() -> tuple[str, str, str, str]:
    """Return deterministic Alpha-v3 catalog, metrics, graph, and channels."""

    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v2 parent theorem rows changed")
    appended, tranche_documents = _bertrand_rows()
    rows = [dict(row) for row in parent_rows] + appended
    if len(rows) != EXPECTED_ALPHA_COUNT:
        raise ValueError("Alpha v3 theorem count changed")

    evidence_counts = Counter(str(row["evidence_status"]) for row in rows)
    membership_counts = Counter(str(row["membership"]) for row in rows)
    origin_counts = Counter(str(row["enrollment_origin"]) for row in rows)
    checked_count = sum(bool(row["checked_use"]) for row in rows)
    expected_evidence = Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=352,
        pending_layered_closure=1,
    )
    expected_membership = Counter(stable=432, alpha_only=491)
    expected_origins = Counter(
        stable=432,
        qr=316,
        ha=120,
        k3b=17,
        k3c=17,
        bertrand_b0_interval=4,
        bertrand_b1_power_order=4,
        bertrand_b1_power_growth=3,
        bertrand_b2_bounded_valuation=10,
    )
    if evidence_counts != expected_evidence:
        raise ValueError(f"Alpha v3 evidence counts changed: {evidence_counts!r}")
    if membership_counts != expected_membership:
        raise ValueError(f"Alpha v3 membership counts changed: {membership_counts!r}")
    if origin_counts != expected_origins:
        raise ValueError(f"Alpha v3 origin counts changed: {origin_counts!r}")
    if checked_count != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("Alpha v3 checked-use count changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_EDGE_COUNT,
        EXPECTED_LAYER_COUNT,
    ):
        raise ValueError("Alpha v3 runtime topology changed")

    enrollment_root = v2_builder.v1._ordered_root(
        ALPHA_ENTRIES, include_origin=True
    )
    spec_root = v2_builder.v1._ordered_root(
        ALPHA_ENTRIES, include_origin=False
    )
    if enrollment_root != ALPHA_V3_ENROLLMENT_SHA256:
        raise ValueError("Alpha v3 runtime enrollment root mismatch")

    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    parent_document = _document(
        PARENT_ALPHA,
        "Sealed Alpha v2 parent catalog whose 902 theorem rows are preserved exactly.",
    )
    documents_by_path[str(parent_document["path"])] = parent_document
    for relative, role in CONTROL_DOCUMENTS.items():
        document = _document(ROOT / relative, role)
        documents_by_path[str(document["path"])] = document
    for document in tranche_documents:
        documents_by_path[str(document["path"])] = document

    catalog = {
        "alpha_only_count": 491,
        "bertrand_evidence_bundle_scheme": BERTRAND_EVIDENCE_BUNDLE_SCHEME,
        "bertrand_evidence_bundle_scheme_sha256": _digest(
            _compact(BERTRAND_EVIDENCE_BUNDLE_SCHEME)
        ),
        "canonical_order": list(parent["canonical_order"])
        + [
            "Bertrand B0 interval search (4)",
            "Bertrand B1 power order (4)",
            "Bertrand B1 power growth (3)",
            "Bertrand B2 bounded valuation (10)",
        ],
        "channel": "alpha",
        "checked_use_count": checked_count,
        "edge_count": EXPECTED_EDGE_COUNT,
        "edition_identity_sha256": ALPHA_V3_IDENTITY_SHA256,
        "enrollment_origin_counts": dict(sorted(origin_counts.items())),
        "enrollment_policy": parent["enrollment_policy"],
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "evidence_documents": [
            documents_by_path[path] for path in sorted(documents_by_path)
        ],
        "evidence_policy": parent["evidence_policy"],
        "evidence_root_sha256": v2_builder.v1._evidence_root(rows),
        "layer_count": EXPECTED_LAYER_COUNT,
        "membership_counts": dict(sorted(membership_counts.items())),
        "membership_root_sha256": v2_builder.v1._membership_root(rows),
        "ordered_enrollment_root_scheme": v2_builder.v1.ORDERED_ENROLLMENT_ROOT_SCHEME,
        "ordered_enrollment_root_scheme_sha256": _digest(
            _compact(v2_builder.v1.ORDERED_ENROLLMENT_ROOT_SCHEME)
        ),
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_spec_root_sha256": spec_root,
        "parent_alpha_v2": _parent_binding(),
        "promotion_model": parent["promotion_model"],
        "schema": SCHEMA,
        "stable_count": EXPECTED_STABLE_COUNT,
        "stable_snapshot": parent["stable_snapshot"],
        "theorem_count": len(rows),
        "theorems": rows,
    }
    catalog_text = _canonical_json(catalog)

    depths, closures, kept_edges, redundant_edges = (
        v2_builder.v1._dependency_analysis(rows)
    )
    if len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT:
        raise ValueError("Alpha v3 dependency analysis lost an edge")
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
        raise ValueError("Alpha v3 display reduction changed reachability")

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
        "dependency_free_theorem_count": sum(
            not row["dependencies"] for row in rows
        ),
        "layer_count": max(depths.values(), default=-1) + 1,
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
            "edition_identity_sha256": ALPHA_V3_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v2": catalog["parent_alpha_v2"],
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
                "edition_identity_sha256": ALPHA_V3_IDENTITY_SHA256,
                "evidence_counts": dict(sorted(evidence_counts.items())),
                "evidence_root_sha256": catalog["evidence_root_sha256"],
                "membership_root_sha256": catalog["membership_root_sha256"],
                "ordered_enrollment_root_sha256": enrollment_root,
                "ordered_spec_root_sha256": spec_root,
                "parent_alpha_v2_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "theorem_count": len(rows),
            },
            "stable": stable_channel,
        },
        "default_channel": "stable",
        "parent_channels_v2": {
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
        f"{'verified' if args.check else 'wrote'} Alpha v3: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}, "
        f"Bertrand-body={BERTRAND_EXPECTED_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
