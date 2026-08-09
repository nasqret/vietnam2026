#!/usr/bin/env python3
"""Build the additive Alpha-v2 channel artifacts for the frozen K3C tranche.

Alpha v2 is an append-only successor to the sealed 885-row Alpha v1 catalog.
The first 885 theorem objects are copied without modification and are bound to
the committed v1 catalog by its byte digest, count, and enrollment root.  The
seventeen appended K3C rows carry dependency-curried body evidence only; this
builder independently kernel-checks those bodies but never upgrades them to
empty-context/checked-use evidence.
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
PARENT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v1.json"
PARENT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics.json"
PARENT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph.mmd"
PARENT_CHANNELS = ARTIFACT_ROOT / "channels.json"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v2.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics-v2.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph-v2.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels-v2.json"
STABLE_CATALOG = ARTIFACT_ROOT / "catalog-v1.json"
STABLE_METRICS = ARTIFACT_ROOT / "metrics.json"
STABLE_GRAPH = ARTIFACT_ROOT / "dependency-graph.mmd"

for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels as v1  # noqa: E402
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v2 import (  # noqa: E402
    ALPHA_EDITION,
    ALPHA_ENTRIES,
    ALPHA_V2_ENROLLMENT_SHA256,
    ALPHA_V2_IDENTITY_SHA256,
    K3C_START_INDEX,
)


SCHEMA = "peano-library-alpha-snapshot-v2"
METRICS_SCHEMA = "peano-library-alpha-metrics-v2"
CHANNEL_SCHEMA = "peano-library-channels-v2"
EXPECTED_PARENT_COUNT = 885
EXPECTED_ALPHA_COUNT = 902
EXPECTED_STABLE_COUNT = 432
EXPECTED_CHECKED_USE_COUNT = 570
EXPECTED_EDGE_COUNT = 2674
EXPECTED_LAYER_COUNT = 45
EXPECTED_PARENT_ALPHA_SHA256 = (
    "ae751f4617b47b7c7871d802b87ae5b9bb9a77c931c283532547a2038d36000a"
)
EXPECTED_PARENT_ENROLLMENT_ROOT = (
    "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
)
EXPECTED_STABLE_ARTIFACT_SHA256 = (
    "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
)

CONTROL_DOCUMENTS = {
    "peano-lab/py/peano_lab/library/alpha_enrollment_v2.py": (
        "Code-owned append manifest binding the sealed v1 parent and exact K3C order."
    ),
    "peano-lab/py/peano_lab/library/editions_v2.py": (
        "Alpha v2 runtime separating enrollment, release membership, and evidence."
    ),
    "peano-lab/py/peano_lab/library/ha_cell_list_membership_surface_candidate.py": (
        "Conservative K3C CellListValid/ListMember definition surface; all predicates expand before kernel parsing."
    ),
    "research/arithmetic-library/ha-cell-list-validity-membership-rfc-v1.md": (
        "Reviewed K3C representation and dependency contract."
    ),
    "peano-lab/py/tests/test_ha_cell_list_membership_surface_candidate.py": (
        "Executable audit of conservative K3C definition expansion and hygiene."
    ),
    "peano-lab/py/tests/test_ha_cell_list_membership_candidate.py": (
        "Executable statement, dependency, body-replay, and mutation audit for all K3C rows."
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


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    graph = v1._alpha_graph(rows, kept_edges, redundant_edges)
    return graph.replace(
        "%% Generated by scripts/build_peano_library_channels.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v2.py; do not edit.",
        1,
    )


def _validate_parent(parent: dict[str, Any]) -> None:
    parent_bytes = PARENT_ALPHA.read_bytes()
    if _digest(parent_bytes) != EXPECTED_PARENT_ALPHA_SHA256:
        raise ValueError("Alpha v1 parent catalog bytes changed")
    if parent.get("schema") != "peano-library-alpha-snapshot-v1":
        raise ValueError("Alpha v1 parent schema changed")
    if parent.get("theorem_count") != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v1 parent count changed")
    if parent.get("ordered_enrollment_root_sha256") != EXPECTED_PARENT_ENROLLMENT_ROOT:
        raise ValueError("Alpha v1 parent enrollment root changed")
    generated = v1.build_payloads()
    committed = (
        PARENT_ALPHA.read_text(encoding="utf-8"),
        PARENT_ALPHA_METRICS.read_text(encoding="utf-8"),
        PARENT_ALPHA_GRAPH.read_text(encoding="utf-8"),
        PARENT_CHANNELS.read_text(encoding="utf-8"),
    )
    if generated != committed:
        raise ValueError("committed Alpha v1 artifact family is stale")


def _k3c_rows(parent_rows: list[dict[str, object]]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    k3c_entries = ALPHA_ENTRIES[K3C_START_INDEX:]
    core = {entry.spec.name: entry.spec for entry in ALPHA_ENTRIES[:K3C_START_INDEX]}
    receipts = replay_candidate_bodies(
        tuple(entry.spec for entry in k3c_entries),
        core=core,
    )
    receipt_by_name = {receipt.name: _body_receipt(receipt) for receipt in receipts}
    source_documents: dict[str, dict[str, object]] = {}
    rows: list[dict[str, object]] = []
    for offset, entry in enumerate(k3c_entries):
        spec = entry.spec
        source_path = ROOT / entry.source_module
        source_document = source_documents.setdefault(
            entry.source_module,
            _document(
                source_path,
                "K3C theorem factory source for dependency-curried body evidence.",
            ),
        )
        if "DNE" in spec.script:
            raise ValueError(f"K3C theorem {spec.name!r} is not intuitionistic")
        source = {
            "kind": "candidate_module",
            "path": entry.source_module,
            "sha256": source_document["sha256"],
        }
        rows.append(
            {
                "body_checked": True,
                "body_receipt": receipt_by_name[spec.name],
                "checked_use": False,
                "dependencies": list(spec.dependencies),
                "dependencies_sha256": _digest("\n".join(spec.dependencies) + "\n"),
                "empty_context_closure": None,
                "enrollment_origin": "k3c",
                "enrollment_index": EXPECTED_PARENT_COUNT + offset,
                "evidence_links": [
                    {
                        "document_sha256": source_document["sha256"],
                        "kind": "k3c_dependency_curried_body",
                        "path": source_document["path"],
                        "role": "dependency_curried_body",
                        "selector": "document",
                    }
                ],
                "evidence_status": "body_checked",
                "logical_spec_sha256": v1._logical_spec_sha256(spec),
                "membership": "alpha_only",
                "name": spec.name,
                "proof_tag": None,
                "provenance": ["k3c"],
                "script": list(spec.script),
                "script_sha256": _digest("\n".join(spec.script) + "\n"),
                "source": source,
                "statement": spec.statement,
                "statement_sha256": _digest(spec.statement),
                "summary": spec.summary,
                "summary_sha256": _digest(spec.summary),
            }
        )
    if len(rows) != 17:
        raise ValueError("K3C append count changed")
    return rows, list(source_documents.values())


def build_payloads() -> tuple[str, str, str, str]:
    """Return deterministic Alpha-v2 catalog, metrics, graph, and channels."""

    parent = _load(PARENT_ALPHA)
    _validate_parent(parent)
    parent_rows = parent.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != EXPECTED_PARENT_COUNT:
        raise ValueError("Alpha v1 parent theorem rows changed")
    appended, source_documents = _k3c_rows(parent_rows)
    rows = [dict(row) for row in parent_rows] + appended
    if len(rows) != EXPECTED_ALPHA_COUNT:
        raise ValueError("Alpha v2 theorem count changed")

    evidence_counts = Counter(str(row["evidence_status"]) for row in rows)
    membership_counts = Counter(str(row["membership"]) for row in rows)
    origin_counts = Counter(str(row["enrollment_origin"]) for row in rows)
    checked_count = sum(bool(row["checked_use"]) for row in rows)
    expected_evidence = Counter(
        stable_closed=432,
        alpha_closed=138,
        body_checked=331,
        pending_layered_closure=1,
    )
    expected_membership = Counter(stable=432, alpha_only=470)
    expected_origins = Counter(stable=432, qr=316, ha=120, k3b=17, k3c=17)
    if evidence_counts != expected_evidence:
        raise ValueError(f"Alpha v2 evidence counts changed: {evidence_counts!r}")
    if membership_counts != expected_membership:
        raise ValueError(f"Alpha v2 membership counts changed: {membership_counts!r}")
    if origin_counts != expected_origins:
        raise ValueError(f"Alpha v2 origin counts changed: {origin_counts!r}")
    if checked_count != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("Alpha v2 checked-use count changed")
    if (ALPHA_EDITION.edge_count, ALPHA_EDITION.layer_count) != (
        EXPECTED_EDGE_COUNT,
        EXPECTED_LAYER_COUNT,
    ):
        raise ValueError("Alpha v2 runtime topology changed")

    enrollment_root = v1._ordered_root(ALPHA_ENTRIES, include_origin=True)
    spec_root = v1._ordered_root(ALPHA_ENTRIES, include_origin=False)
    if enrollment_root != ALPHA_V2_ENROLLMENT_SHA256:
        raise ValueError("Alpha v2 runtime enrollment root mismatch")
    documents_by_path = {
        str(document["path"]): document for document in parent["evidence_documents"]
    }
    parent_document = _document(
        PARENT_ALPHA,
        "Sealed Alpha v1 parent catalog whose 885 theorem rows are preserved exactly.",
    )
    documents_by_path[str(parent_document["path"])] = parent_document
    for relative, role in CONTROL_DOCUMENTS.items():
        document = _document(
            ROOT / relative,
            role,
        )
        documents_by_path[str(document["path"])] = document
    for document in source_documents:
        documents_by_path[str(document["path"])] = document

    catalog = {
        "alpha_only_count": 470,
        "canonical_order": list(parent["canonical_order"])
        + ["K3C list validity, membership, and semantic interface (17)"],
        "channel": "alpha",
        "checked_use_count": checked_count,
        "edge_count": EXPECTED_EDGE_COUNT,
        "edition_identity_sha256": ALPHA_V2_IDENTITY_SHA256,
        "enrollment_origin_counts": dict(sorted(origin_counts.items())),
        "enrollment_policy": parent["enrollment_policy"],
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "evidence_documents": [
            documents_by_path[path] for path in sorted(documents_by_path)
        ],
        "evidence_policy": parent["evidence_policy"],
        "evidence_root_sha256": v1._evidence_root(rows),
        "layer_count": EXPECTED_LAYER_COUNT,
        "membership_counts": dict(sorted(membership_counts.items())),
        "membership_root_sha256": v1._membership_root(rows),
        "ordered_enrollment_root_scheme": v1.ORDERED_ENROLLMENT_ROOT_SCHEME,
        "ordered_enrollment_root_scheme_sha256": _digest(
            _compact(v1.ORDERED_ENROLLMENT_ROOT_SCHEME)
        ),
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_spec_root_sha256": spec_root,
        "parent_alpha_v1": {
            "artifact_sha256": EXPECTED_PARENT_ALPHA_SHA256,
            "ordered_enrollment_root_sha256": EXPECTED_PARENT_ENROLLMENT_ROOT,
            "path": _repository_path(PARENT_ALPHA),
            "schema": parent["schema"],
            "theorem_count": EXPECTED_PARENT_COUNT,
        },
        "promotion_model": parent["promotion_model"],
        "schema": SCHEMA,
        "stable_count": EXPECTED_STABLE_COUNT,
        "stable_snapshot": parent["stable_snapshot"],
        "theorem_count": len(rows),
        "theorems": rows,
    }
    catalog_text = _canonical_json(catalog)

    depths, closures, kept_edges, redundant_edges = v1._dependency_analysis(rows)
    if len(kept_edges) + len(redundant_edges) != EXPECTED_EDGE_COUNT:
        raise ValueError("Alpha v2 dependency analysis lost an edge")
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
        raise ValueError("Alpha v2 display reduction changed reachability")

    metrics = _load(PARENT_ALPHA_METRICS)
    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    origin_by_name = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_by_origin = Counter(origin_by_name[theorem] for _, theorem in redundant_edges)
    depth_counts = Counter(depths.values())
    topology = {
        "declared_edge_count": EXPECTED_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": max(depths.values(), default=-1) + 1,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant_edges),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(
            sorted(redundant_by_origin.items())
        ),
        "reachability_redundant_direct_dependency_sha256": _digest(_compact(redundant_rows)),
        "reachability_reduction_scope": metrics["dependency_graph"]["reachability_reduction_scope"],
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
            "edition_identity_sha256": ALPHA_V2_IDENTITY_SHA256,
            "evidence_counts": dict(sorted(evidence_counts.items())),
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v1": catalog["parent_alpha_v1"],
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
    metrics["promotion_gates"]["source_integrity"]["source_bound_theorem_count"] = len(rows)
    metrics_text = _canonical_json(metrics)

    parent_channels = _load(PARENT_CHANNELS)
    stable_channel = parent_channels["channels"]["stable"]
    alpha_artifacts = {
        "catalog": {"path": _repository_path(DEFAULT_ALPHA), "sha256": _digest(catalog_text)},
        "dependency_graph": {"path": _repository_path(DEFAULT_ALPHA_GRAPH), "sha256": _digest(graph)},
        "metrics": {"path": _repository_path(DEFAULT_ALPHA_METRICS), "sha256": _digest(metrics_text)},
    }
    channels = {
        "channels": {
            "alpha": {
                "artifacts": alpha_artifacts,
                "artifact_path": _repository_path(DEFAULT_ALPHA),
                "artifact_sha256": _digest(catalog_text),
                "checked_use_count": checked_count,
                "edition_identity_sha256": ALPHA_V2_IDENTITY_SHA256,
                "evidence_counts": dict(sorted(evidence_counts.items())),
                "evidence_root_sha256": catalog["evidence_root_sha256"],
                "membership_root_sha256": catalog["membership_root_sha256"],
                "ordered_enrollment_root_sha256": enrollment_root,
                "ordered_spec_root_sha256": spec_root,
                "parent_alpha_v1_sha256": EXPECTED_PARENT_ALPHA_SHA256,
                "theorem_count": len(rows),
            },
            "stable": stable_channel,
        },
        "default_channel": "stable",
        "parent_channels_v1": {
            "path": _repository_path(PARENT_CHANNELS),
            "sha256": _digest(PARENT_CHANNELS.read_bytes()),
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
        f"{'verified' if args.check else 'wrote'} Alpha v2: "
        f"stable={EXPECTED_STABLE_COUNT}, alpha={EXPECTED_ALPHA_COUNT}, "
        f"checked-use={EXPECTED_CHECKED_USE_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
