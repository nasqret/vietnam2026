#!/usr/bin/env python3
"""Build the deterministic Alpha/Stable Peano-library channel artifacts.

The stable artifact remains owned by ``build_peano_library_snapshot.py`` and
is never rewritten here.  Alpha is an ordered specification library with
heterogeneous evidence: stable and selected HA/K3B entries have checked
empty-context closures, while most of the quadratic-reciprocity campaign has
only a checked dependency-curried body.  Channel membership therefore never
silently upgrades proof evidence.
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
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
DEFAULT_ALPHA = ARTIFACT_ROOT / "alpha" / "catalog-v1.json"
DEFAULT_ALPHA_METRICS = ARTIFACT_ROOT / "alpha" / "metrics.json"
DEFAULT_ALPHA_GRAPH = ARTIFACT_ROOT / "alpha" / "dependency-graph.mmd"
DEFAULT_CHANNELS = ARTIFACT_ROOT / "channels.json"
STABLE_CATALOG = ARTIFACT_ROOT / "catalog-v1.json"
STABLE_METRICS = ARTIFACT_ROOT / "metrics.json"
STABLE_GRAPH = ARTIFACT_ROOT / "dependency-graph.mmd"
QR_CORPUS = ROOT / "book" / "_static" / "pa-proof-explorer" / "api" / "corpus.json"
QR_AUDIT = ROOT / "research" / "arithmetic-library" / "wmi-qr-replay.md"
HA_CAMPAIGN = ROOT / "research" / "arithmetic-library" / "ha-number-theory-campaign.json"
K3B_RECEIPT = ARTIFACT_ROOT / "ha-k3b-listat-full-closure-219217.json"
TAG_REGISTRY = ROOT / "research" / "arithmetic-library" / "pa-proof-tags.json"
EDITIONS_SOURCE = PY_ROOT / "peano_lab" / "library" / "editions.py"

if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.library.editions import (  # noqa: E402
    ALPHA_EDITION,
    ALPHA_ENROLLMENT_SHA256,
    EnrollmentOrigin,
    EvidenceStatus,
    Membership,
    STABLE_EDITION,
)


SCHEMA = "peano-library-alpha-snapshot-v1"
CHANNEL_SCHEMA = "peano-library-channels-v1"
EXPECTED_STABLE_COUNT = 432
EXPECTED_ALPHA_COUNT = 885
EXPECTED_CHECKED_USE_COUNT = 570
EXPECTED_ALPHA_ONLY_COUNT = 453
EXPECTED_ENROLLMENT_ROOT = (
    "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
)
EXPECTED_STABLE_ARTIFACT_SHA256 = (
    "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
)
EXPECTED_STABLE_ORDERED_ROOT = (
    "4d02dc439d53533e8992a471b26ee34059fb6001f822041e42c56b2cc0a7a079"
)
ORDERED_ENROLLMENT_ROOT_SCHEME = {
    "encoding": "UTF-8",
    "field_order": [
        "enrollment_origin",
        "name",
        "statement",
        "dependencies",
        "script",
    ],
    "field_separator": "U+001F",
    "hash": "SHA-256",
    "list_separator": "U+001E",
    "row_separator": "U+001C",
    "version": 1,
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
    if not isinstance(value, dict):
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


def _logical_spec(spec: object) -> dict[str, object]:
    return {
        "dependencies": list(spec.dependencies),
        "name": spec.name,
        "script": list(spec.script),
        "statement": spec.statement,
    }


def _logical_spec_sha256(spec: object) -> str:
    return _digest(_compact(_logical_spec(spec)))


def _ordered_root(
    entries: tuple[object, ...],
    *,
    include_origin: bool,
) -> str:
    rows: list[str] = []
    for item in entries:
        spec = item.spec
        fields = [spec.name, spec.statement, "\x1e".join(spec.dependencies), "\x1e".join(spec.script)]
        if include_origin:
            fields.insert(0, item.enrollment_origin.value)
        rows.append("\x1f".join(fields))
    return _digest("\x1c".join(rows))


def _membership_root(rows: list[dict[str, object]]) -> str:
    return _digest(
        "\x1c".join(
            "\x1f".join(
                (
                    str(row["name"]),
                    str(row["membership"]),
                    str(row["enrollment_origin"]),
                    "\x1e".join(row["provenance"]),
                )
            )
            for row in rows
        )
    )


def _evidence_root(rows: list[dict[str, object]]) -> str:
    return _digest(
        "\x1c".join(
            "\x1f".join(
                (
                    str(row["name"]),
                    str(row["evidence_status"]),
                    "1" if row["checked_use"] else "0",
                    _compact(row["evidence_links"]),
                    _compact(row["empty_context_closure"]),
                )
            )
            for row in rows
        )
    )


def _dependency_analysis(
    rows: list[dict[str, object]],
) -> tuple[
    dict[str, int],
    dict[str, frozenset[str]],
    list[tuple[str, str]],
    list[tuple[str, str]],
]:
    """Return depths, closures, kept edges, and reachability-redundant edges.

    A direct dependency ``d -> theorem`` is reachability-redundant precisely
    when another direct dependency of ``theorem`` already reaches ``d``.
    Removing all such edges from this topologically ordered DAG preserves its
    reachability relation.  This is *not* a claim of proof-semantic or global
    minimality: tactic bodies may still refer to a direct dependency.  The
    theorem specifications remain byte-for-byte unchanged; the reduction is
    used only for the review graph and link-quality metrics.
    """

    depths: dict[str, int] = {}
    closures: dict[str, frozenset[str]] = {}
    kept: list[tuple[str, str]] = []
    redundant: list[tuple[str, str]] = []
    for row in rows:
        name = str(row["name"])
        dependencies = tuple(str(item) for item in row["dependencies"])
        depths[name] = (
            0
            if not dependencies
            else 1 + max(depths[dependency] for dependency in dependencies)
        )
        dependency_set = set(dependencies)
        for dependency in dependencies:
            alternatives = dependency_set.difference({dependency})
            if any(
                dependency == alternative
                or dependency in closures[alternative]
                for alternative in alternatives
            ):
                redundant.append((dependency, name))
            else:
                kept.append((dependency, name))
        closure = set(dependencies)
        for dependency in dependencies:
            closure.update(closures[dependency])
        closures[name] = frozenset(closure)
    return depths, closures, kept, redundant


def _alpha_graph(
    rows: list[dict[str, object]],
    kept_edges: list[tuple[str, str]],
    redundant_edges: list[tuple[str, str]],
) -> str:
    """Build a reachability-equivalent, transitive-reduced review graph."""

    lines = [
        "%% Generated by scripts/build_peano_library_channels.py; do not edit.",
        "%% Alpha review view: declared dependency edges are transitively reduced.",
        f"%% Declared edges: {len(kept_edges) + len(redundant_edges)}; visible edges: {len(kept_edges)}; hidden reachability-redundant edges: {len(redundant_edges)}.",
        "%% Reachability reduction is a display optimization, not a proof-semantic or global-minimality claim.",
        "flowchart TD",
    ]
    release_classes: dict[str, list[str]] = {
        "stableMembership": [],
        "alphaMembership": [],
    }
    evidence_classes: dict[str, list[str]] = {
        "bodyEvidence": [],
        "pendingEvidence": [],
    }
    for row in rows:
        name = str(row["name"])
        if row["membership"] == "stable":
            lines.append(f"  {name}[{name}]")
            release_classes["stableMembership"].append(name)
        else:
            lines.append(f"  {name}({name})")
            release_classes["alphaMembership"].append(name)
        if row["evidence_status"] == "body_checked":
            evidence_classes["bodyEvidence"].append(name)
        elif row["evidence_status"] == "pending_layered_closure":
            evidence_classes["pendingEvidence"].append(name)
    for dependency, name in kept_edges:
        lines.append(f"  {dependency} --> {name}")
    lines.extend(
        (
            "  classDef stableMembership fill:#e8f5e9,stroke:#2e7d32,color:#17351a;",
            "  classDef alphaMembership fill:#e3f2fd,stroke:#1565c0,color:#102f4a;",
            "  classDef bodyEvidence stroke-dasharray:6 3;",
            "  classDef pendingEvidence stroke:#c62828,stroke-width:3px,stroke-dasharray:6 3;",
        )
    )
    for class_name, names in release_classes.items():
        for offset in range(0, len(names), 40):
            lines.append(f"  class {','.join(names[offset:offset + 40])} {class_name};")
    for class_name, names in evidence_classes.items():
        if not names:
            continue
        for offset in range(0, len(names), 40):
            lines.append(f"  class {','.join(names[offset:offset + 40])} {class_name};")
    return "\n".join(lines) + "\n"


def _evidence_link(
    document: dict[str, object],
    *,
    kind: str,
    selector: str,
    role: str,
) -> dict[str, object]:
    return {
        "document_sha256": document["sha256"],
        "kind": kind,
        "path": document["path"],
        "role": role,
        "selector": selector,
    }


def _stable_closure(row: dict[str, Any]) -> dict[str, object]:
    return {
        "certificate_representation": row["certificate_representation"],
        "certificate_sha256": row["certificate_sha256"],
        "cut_nodes": row["cut_nodes"],
        "digest_kind": "python-dataclass-repr-sha256",
        "proof_depth": row["proof_depth"],
        "proof_edges": row["proof_edges"],
        "proof_nodes": row["proof_nodes"],
        "proof_objects": row["distinct_proof_objects"],
        "reused_objects": row["reused_proof_references"],
        "status": "checked",
    }


def _ha_closure(item: dict[str, Any]) -> dict[str, object]:
    receipt = item["receipt"]
    return {
        "certificate_sha256": receipt["certificate_sha256"],
        "cut_nodes": receipt["cuts"],
        "digest_kind": "content-proof-dag-sha256",
        "proof_depth": receipt["depth"],
        "proof_edges": receipt["edges"],
        "proof_nodes": receipt["nodes"],
        "proof_objects": receipt["objects"],
        "reused_objects": receipt["reused"],
        "status": "checked",
    }


def _k3b_closure(result: dict[str, Any]) -> dict[str, object]:
    return {
        "certificate_sha256": result["proof_dag_sha256"],
        "cut_nodes": result["cuts"],
        "dependency_closure_count": result["dependency_closure_count"],
        "dependency_closure_sha256": result["dependency_closure_sha256"],
        "digest_kind": "content-proof-dag-sha256",
        "dne_objects": result["dne_objects"],
        "proof_depth": result["proof_depth"],
        "proof_edges": result["proof_edges"],
        "proof_nodes": result["proof_nodes"],
        "proof_objects": result["proof_objects"],
        "reused_objects": result["reused_objects"],
        "status": "checked",
    }


def build_payloads() -> tuple[str, str, str, str]:
    """Return deterministic Alpha catalog, metrics, graph, and channel index."""

    stable = _load(STABLE_CATALOG)
    qr = _load(QR_CORPUS)
    campaign = _load(HA_CAMPAIGN)
    k3b = _load(K3B_RECEIPT)
    tags = _load(TAG_REGISTRY)["assignments"]

    if _digest(STABLE_CATALOG.read_bytes()) != EXPECTED_STABLE_ARTIFACT_SHA256:
        raise ValueError("stable catalog bytes changed; Alpha generation is fail-closed")
    if stable.get("ordered_root_sha256") != EXPECTED_STABLE_ORDERED_ROOT:
        raise ValueError("stable ordered root changed; Alpha generation is fail-closed")

    stable_by_name = {row["name"]: row for row in stable["theorems"]}
    qr_by_name = {row["name"]: row for row in qr["theorems"]}
    campaign_by_name = {
        row["name"]: row for row in campaign["theorem_evidence"]["theorems"]
    }
    k3b_by_name = k3b["results"]

    documents = {
        "stable": _document(
            STABLE_CATALOG,
            "Stable closed-certificate snapshot; generated only after kernel replay.",
        ),
        "qr": _document(
            QR_CORPUS,
            "QR specification, tactic-body, source, and status inventory; not a closure receipt.",
        ),
        "qr_audit": _document(
            QR_AUDIT,
            "QR WMI audit history, including the absence of a complete current 136-gate seal.",
        ),
        "ha": _document(
            HA_CAMPAIGN,
            "Strict-HA campaign evidence with exact empty-context closure receipts.",
        ),
        "k3b": _document(
            K3B_RECEIPT,
            "Two-pass WMI empty-context closure receipt for all seventeen K3B targets.",
        ),
        "tags": _document(
            TAG_REGISTRY,
            "Persistent theorem-tag assignments for the QR dependency view.",
        ),
        "editions": _document(
            EDITIONS_SOURCE,
            "Canonical Alpha/Stable enrollment and evidence-status API.",
        ),
    }

    if len(STABLE_EDITION.entries) != EXPECTED_STABLE_COUNT:
        raise ValueError("stable edition count drifted")
    if len(ALPHA_EDITION.entries) != EXPECTED_ALPHA_COUNT:
        raise ValueError("alpha edition count drifted")
    alpha_stable_entries = tuple(
        item for item in ALPHA_EDITION.entries if item.membership is Membership.STABLE
    )
    if (
        len(alpha_stable_entries) != len(STABLE_EDITION.entries)
        or {item.spec.name: item.spec for item in alpha_stable_entries}
        != {item.spec.name: item.spec for item in STABLE_EDITION.entries}
    ):
        raise ValueError("Stable is not an exact specification subset of Alpha")

    rows: list[dict[str, object]] = []
    for index, item in enumerate(ALPHA_EDITION.entries):
        spec = item.spec
        evidence_links: list[dict[str, object]] = []
        closure: dict[str, object] | None

        stable_row = stable_by_name.get(spec.name)
        qr_row = qr_by_name.get(spec.name)
        campaign_row = campaign_by_name.get(spec.name)
        k3b_row = k3b_by_name.get(spec.name)

        if item.evidence is EvidenceStatus.STABLE_CLOSED:
            if stable_row is None:
                raise ValueError(f"stable evidence is missing for {spec.name!r}")
            evidence_links.append(
                _evidence_link(
                    documents["stable"],
                    kind="stable_closed_snapshot",
                    selector=f"theorems[name={spec.name}]",
                    role="empty_context_closure",
                )
            )
            closure = _stable_closure(stable_row)
        elif item.evidence is EvidenceStatus.ALPHA_CLOSED:
            if campaign_row is not None and campaign_row["status"] == "closed_checked_candidate":
                evidence_links.append(
                    _evidence_link(
                        documents["ha"],
                        kind="ha_campaign_closure",
                        selector=f"theorem_evidence.theorems[name={spec.name}]",
                        role="empty_context_closure",
                    )
                )
                closure = _ha_closure(campaign_row)
            elif k3b_row is not None:
                evidence_links.append(
                    _evidence_link(
                        documents["k3b"],
                        kind="k3b_wmi_closure",
                        selector=f"results.{spec.name}",
                        role="empty_context_closure",
                    )
                )
                closure = _k3b_closure(k3b_row)
            else:
                raise ValueError(f"alpha closure evidence is missing for {spec.name!r}")
        elif item.evidence in {
            EvidenceStatus.BODY_CHECKED,
            EvidenceStatus.PENDING_LAYERED_CLOSURE,
        }:
            if qr_row is None:
                raise ValueError(f"QR body inventory is missing for {spec.name!r}")
            expected_qr_status = (
                "pending_layered_closure"
                if item.evidence is EvidenceStatus.PENDING_LAYERED_CLOSURE
                else "candidate_body_checked"
            )
            if qr_row["status"] != expected_qr_status:
                raise ValueError(
                    f"QR status mismatch for {spec.name!r}: {qr_row['status']!r}"
                )
            evidence_links.extend(
                (
                    _evidence_link(
                        documents["qr"],
                        kind="qr_body_inventory",
                        selector=f"theorems[name={spec.name}]",
                        role="dependency_curried_body",
                    ),
                    _evidence_link(
                        documents["qr_audit"],
                        kind="qr_full_audit_status",
                        selector="document",
                        role="promotion_blocker",
                    ),
                )
            )
            closure = (
                {"status": "pending_layered_closure"}
                if item.evidence is EvidenceStatus.PENDING_LAYERED_CLOSURE
                else None
            )
        else:  # pragma: no cover - enum exhaustiveness guard
            raise ValueError(f"unsupported evidence status {item.evidence!r}")

        # The compatible QR/HA overlap remains at its historic QR position,
        # while its later HA receipt strengthens the evidence to alpha-closed.
        if (
            EnrollmentOrigin.QR in item.provenance
            and EnrollmentOrigin.HA in item.provenance
            and campaign_row is not None
        ):
            if not any(link["kind"] == "ha_campaign_closure" for link in evidence_links):
                evidence_links.append(
                    _evidence_link(
                        documents["ha"],
                        kind="ha_campaign_closure",
                        selector=f"theorem_evidence.theorems[name={spec.name}]",
                        role="empty_context_closure",
                    )
                )
            if qr_row is None:
                raise ValueError(f"QR overlap inventory is missing for {spec.name!r}")
            evidence_links.append(
                _evidence_link(
                    documents["qr"],
                    kind="qr_spec_inventory",
                    selector=f"theorems[name={spec.name}]",
                    role="historical_enrollment_and_source",
                )
            )

        source_path = ROOT / item.source_module
        if not source_path.is_file():
            raise ValueError(
                f"primary source is missing for {spec.name!r}: {item.source_module}"
            )
        source = {
            "kind": "stable_registry"
            if item.enrollment_origin is EnrollmentOrigin.STABLE
            else "candidate_module",
            "path": item.source_module,
            "sha256": _digest(source_path.read_bytes()),
        }
        if item.enrollment_origin is EnrollmentOrigin.QR:
            if qr_row is None:
                raise ValueError(
                    f"QR enrollment is absent from the explorer corpus: {spec.name!r}"
                )
            qr_source = qr_row.get("source")
            if (
                not isinstance(qr_source, dict)
                or qr_source.get("path") != item.source_module
                or qr_source.get("sha256") != source["sha256"]
            ):
                raise ValueError(f"QR source binding drifted for {spec.name!r}")
            # Preserve useful declaration-line and browser-link metadata while
            # binding it to the code-owned primary source from Editions.
            source = dict(qr_source)
        if (
            item.enrollment_origin is EnrollmentOrigin.HA
            and campaign_row is not None
            and campaign_row.get("source_module") != item.source_module
        ):
            raise ValueError(f"HA source binding drifted for {spec.name!r}")

        row: dict[str, object] = {
            "body_checked": True,
            "checked_use": item.checked_use,
            "dependencies": list(spec.dependencies),
            "dependencies_sha256": _digest("\n".join(spec.dependencies) + "\n"),
            "empty_context_closure": closure,
            "enrollment_origin": item.enrollment_origin.value,
            "enrollment_index": index,
            "evidence_links": evidence_links,
            "evidence_status": item.evidence.value,
            "logical_spec_sha256": _logical_spec_sha256(spec),
            "membership": item.membership.value,
            "name": spec.name,
            "proof_tag": tags.get(spec.name),
            "provenance": [origin.value for origin in item.provenance],
            "script": list(spec.script),
            "script_sha256": _digest("\n".join(spec.script) + "\n"),
            "source": source,
            "statement": spec.statement,
            "statement_sha256": _digest(spec.statement),
            "summary": spec.summary,
            "summary_sha256": _digest(spec.summary),
        }
        rows.append(row)

    enrollment_root = _ordered_root(ALPHA_EDITION.entries, include_origin=True)
    if enrollment_root != ALPHA_ENROLLMENT_SHA256:
        raise ValueError("generator and canonical editions API disagree on enrollment root")
    if enrollment_root != EXPECTED_ENROLLMENT_ROOT:
        raise ValueError(
            "canonical alpha enrollment root drifted: "
            f"{enrollment_root} != {EXPECTED_ENROLLMENT_ROOT}"
        )
    spec_root = _ordered_root(ALPHA_EDITION.entries, include_origin=False)
    evidence_counts = Counter(row["evidence_status"] for row in rows)
    membership_counts = Counter(row["membership"] for row in rows)
    origin_counts = Counter(row["enrollment_origin"] for row in rows)
    checked_count = sum(bool(row["checked_use"]) for row in rows)
    if checked_count != EXPECTED_CHECKED_USE_COUNT:
        raise ValueError("alpha checked-use count drifted")
    if evidence_counts != Counter(
        {
            "stable_closed": 432,
            "alpha_closed": 138,
            "body_checked": 314,
            "pending_layered_closure": 1,
        }
    ):
        raise ValueError(f"alpha evidence counts drifted: {dict(evidence_counts)!r}")
    if membership_counts != Counter({"stable": 432, "alpha_only": 453}):
        raise ValueError(f"alpha membership counts drifted: {dict(membership_counts)!r}")
    if origin_counts != Counter({"stable": 432, "qr": 316, "ha": 120, "k3b": 17}):
        raise ValueError(f"alpha enrollment-origin counts drifted: {dict(origin_counts)!r}")

    alpha_catalog = {
        "alpha_only_count": EXPECTED_ALPHA_ONLY_COUNT,
        "canonical_order": [
            "legacy Stable enrollment origin (432)",
            "quadratic-reciprocity candidate order (316)",
            "strict-HA unique additions (120)",
            "K3B CellHistory/ListAt targets (17)",
        ],
        "channel": "alpha",
        "checked_use_count": checked_count,
        "edge_count": ALPHA_EDITION.edge_count,
        "edition_identity_sha256": ALPHA_EDITION.identity_sha256,
        "enrollment_policy": (
            "Alpha contains every reviewed building-library specification. "
            "Membership is independent of evidence and does not make a theorem "
            "available as an empty-context fact. Enrollment origin is immutable; "
            "promotion changes release membership and evidence, never origin or "
            "canonical Alpha position. Stable is a subset, not a permanent prefix."
        ),
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "evidence_documents": [documents[name] for name in sorted(documents)],
        "evidence_policy": (
            "stable_closed and alpha_closed are checked-use evidence; body_checked "
            "records only a dependency-curried body; pending_layered_closure records "
            "a checked body whose full layered closure is not sealed. JSON hashes are "
            "provenance, never kernel authority."
        ),
        "evidence_root_sha256": _evidence_root(rows),
        "enrollment_origin_counts": dict(sorted(origin_counts.items())),
        "layer_count": ALPHA_EDITION.layer_count,
        "membership_counts": dict(sorted(membership_counts.items())),
        "membership_root_sha256": _membership_root(rows),
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_enrollment_root_scheme": ORDERED_ENROLLMENT_ROOT_SCHEME,
        "ordered_enrollment_root_scheme_sha256": _digest(
            _compact(ORDERED_ENROLLMENT_ROOT_SCHEME)
        ),
        "ordered_spec_root_sha256": spec_root,
        "promotion_model": {
            "alpha_order": "frozen_canonical_enrollment_ledger",
            "current_v1_layout": (
                "The 432 legacy Stable rows happen to be the current prefix; "
                "this is a v1 seal, not a permanent membership-origin axiom."
            ),
            "immutable_across_promotion": [
                "canonical_alpha_position",
                "enrollment_origin",
                "logical_specification",
                "primary_source",
                "provenance",
            ],
            "new_snapshot_required": True,
            "stable_relation": (
                "keyed exact subset of Alpha with its own append-only, "
                "dependency-topological release order"
            ),
        },
        "schema": SCHEMA,
        "stable_count": EXPECTED_STABLE_COUNT,
        "stable_snapshot": {
            "artifact_sha256": documents["stable"]["sha256"],
            "ordered_root_sha256": stable["ordered_root_sha256"],
            "path": documents["stable"]["path"],
            "schema": stable["schema"],
            "theorem_count": stable["theorem_count"],
        },
        "theorem_count": len(rows),
        "theorems": rows,
    }
    alpha_text = _canonical_json(alpha_catalog)

    depths, closures, kept_edges, redundant_edges = _dependency_analysis(rows)
    if len(kept_edges) + len(redundant_edges) != ALPHA_EDITION.edge_count:
        raise ValueError("Alpha dependency analysis lost a declared edge")
    reduced_dependencies: dict[str, list[str]] = {str(row["name"]): [] for row in rows}
    for dependency, theorem in kept_edges:
        reduced_dependencies[theorem].append(dependency)
    reduced_closures: dict[str, frozenset[str]] = {}
    for row in rows:
        name = str(row["name"])
        closure: set[str] = set(reduced_dependencies[name])
        for dependency in reduced_dependencies[name]:
            closure.update(reduced_closures[dependency])
        reduced_closures[name] = frozenset(closure)
    if reduced_closures != closures:
        raise ValueError("transitive reduction did not preserve Alpha reachability")

    alpha_graph = _alpha_graph(rows, kept_edges, redundant_edges)
    checked_closures = [
        row["empty_context_closure"]
        for row in rows
        if row["checked_use"]
    ]
    if any(type(closure) is not dict for closure in checked_closures):
        raise ValueError("a checked-use Alpha row has no metric-bearing closure")
    checked_metric_rows: list[dict[str, object]] = [
        closure for closure in checked_closures if isinstance(closure, dict)
    ]
    metric_fields = (
        "cut_nodes",
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "proof_objects",
        "reused_objects",
    )
    if any(
        type(closure.get(field)) is not int
        for closure in checked_metric_rows
        for field in metric_fields
    ):
        raise ValueError("a checked-use Alpha closure is missing exact proof metrics")
    origin_by_name = {str(row["name"]): str(row["enrollment_origin"]) for row in rows}
    redundant_by_origin = Counter(origin_by_name[theorem] for _, theorem in redundant_edges)
    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    depth_counts = Counter(depths.values())
    alpha_metrics = {
        "catalog_path": _repository_path(DEFAULT_ALPHA),
        "catalog_sha256": _digest(alpha_text),
        "channel": "alpha",
        "checked_closure_metrics": {
            "certificate_digest_kinds": dict(
                sorted(
                    Counter(
                        str(closure["digest_kind"])
                        for closure in checked_metric_rows
                    ).items()
                )
            ),
            "maximum_cut_nodes": max(
                int(closure["cut_nodes"]) for closure in checked_metric_rows
            ),
            "maximum_proof_depth": max(
                int(closure["proof_depth"]) for closure in checked_metric_rows
            ),
            "maximum_proof_edges": max(
                int(closure["proof_edges"]) for closure in checked_metric_rows
            ),
            "maximum_proof_nodes": max(
                int(closure["proof_nodes"]) for closure in checked_metric_rows
            ),
            "maximum_proof_objects": max(
                int(closure["proof_objects"]) for closure in checked_metric_rows
            ),
            "metric_bearing_theorem_count": len(checked_metric_rows),
            "missing_empty_context_metric_count": len(rows) - len(checked_metric_rows),
            "total_cut_nodes": sum(
                int(closure["cut_nodes"]) for closure in checked_metric_rows
            ),
            "total_proof_edges": sum(
                int(closure["proof_edges"]) for closure in checked_metric_rows
            ),
            "total_proof_nodes": sum(
                int(closure["proof_nodes"]) for closure in checked_metric_rows
            ),
            "total_proof_objects": sum(
                int(closure["proof_objects"]) for closure in checked_metric_rows
            ),
            "total_reused_objects": sum(
                int(closure["reused_objects"]) for closure in checked_metric_rows
            ),
        },
        "checked_use_count": checked_count,
        "dependency_graph": {
            "declared_edge_count": len(kept_edges) + len(redundant_edges),
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
            "reachability_reduction_scope": (
                "Display-only transitive reduction; this is not proof-semantic "
                "or global dependency minimality."
            ),
            "theorems_by_depth": {
                str(depth): count for depth, count in sorted(depth_counts.items())
            },
            "transitive_reduction_edge_count": len(kept_edges),
            "transitive_reduction_edge_sha256": _digest(_compact(kept_rows)),
            "transitive_reduction_preserves_reachability": True,
        },
        "dependency_graph_path": _repository_path(DEFAULT_ALPHA_GRAPH),
        "dependency_graph_sha256": _digest(alpha_graph),
        "edition_identity_sha256": ALPHA_EDITION.identity_sha256,
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_spec_root_sha256": spec_root,
        "promotion_model": alpha_catalog["promotion_model"],
        "promotion_gates": {
            "canonical_topology": {
                "status": "passed",
                "theorem_count": len(rows),
                "declared_edge_count": len(kept_edges) + len(redundant_edges),
            },
            "dependency_link_analysis": {
                "status": "review_required",
                "reachability_redundant_direct_dependency_count": len(redundant_edges),
                "policy": (
                    "Every reachability-redundant direct link must be reviewed "
                    "before promotion. It need not be removed when the tactic body "
                    "uses it directly; this gate makes no proof-semantic or global-"
                    "minimality claim."
                ),
            },
            "full_alpha_empty_context_compilation": {
                "status": "blocked",
                "checked": checked_count,
                "required": len(rows),
                "missing": len(rows) - checked_count,
                "policy": (
                    "The missing closures block promotion of Alpha as one whole "
                    "edition. Stable may still accept a selected dependency-closed "
                    "batch after fresh isolated closure and kernel checks for that "
                    "batch and its complete dependency closure."
                ),
            },
            "source_integrity": {
                "status": "passed",
                "source_bound_theorem_count": sum(
                    isinstance(row["source"], dict) for row in rows
                ),
            },
        },
        "schema": "peano-library-alpha-metrics-v1",
        "theorem_count": len(rows),
    }
    alpha_metrics_text = _canonical_json(alpha_metrics)

    stable_entries = STABLE_EDITION.entries
    alpha_row_by_name = {str(row["name"]): row for row in rows}
    stable_rows = [alpha_row_by_name[item.spec.name] for item in stable_entries]
    stable_metrics_bytes = STABLE_METRICS.read_bytes()
    stable_graph_bytes = STABLE_GRAPH.read_bytes()
    artifact_family = {
        "alpha": {
            "catalog": {
                "path": _repository_path(DEFAULT_ALPHA),
                "sha256": _digest(alpha_text),
            },
            "dependency_graph": {
                "path": _repository_path(DEFAULT_ALPHA_GRAPH),
                "sha256": _digest(alpha_graph),
            },
            "metrics": {
                "path": _repository_path(DEFAULT_ALPHA_METRICS),
                "sha256": _digest(alpha_metrics_text),
            },
        },
        "stable": {
            "catalog": {
                "path": _repository_path(STABLE_CATALOG),
                "sha256": documents["stable"]["sha256"],
            },
            "dependency_graph": {
                "path": _repository_path(STABLE_GRAPH),
                "sha256": _digest(stable_graph_bytes),
            },
            "metrics": {
                "path": _repository_path(STABLE_METRICS),
                "sha256": _digest(stable_metrics_bytes),
            },
        },
    }
    channels = {
        "channels": {
            "alpha": {
                "artifacts": artifact_family["alpha"],
                "artifact_path": _repository_path(DEFAULT_ALPHA),
                "artifact_sha256": _digest(alpha_text),
                "checked_use_count": checked_count,
                "edition_identity_sha256": ALPHA_EDITION.identity_sha256,
                "evidence_counts": dict(sorted(evidence_counts.items())),
                "evidence_root_sha256": alpha_catalog["evidence_root_sha256"],
                "membership_root_sha256": alpha_catalog["membership_root_sha256"],
                "ordered_enrollment_root_sha256": enrollment_root,
                "ordered_spec_root_sha256": spec_root,
                "theorem_count": len(rows),
            },
            "stable": {
                "artifacts": artifact_family["stable"],
                "artifact_path": _repository_path(STABLE_CATALOG),
                "artifact_sha256": documents["stable"]["sha256"],
                "checked_use_count": EXPECTED_STABLE_COUNT,
                "evidence_counts": {"stable_closed": EXPECTED_STABLE_COUNT},
                "evidence_root_sha256": _evidence_root(stable_rows),
                "legacy_ordered_root_sha256": stable["ordered_root_sha256"],
                "membership_root_sha256": _membership_root(stable_rows),
                "ordered_enrollment_root_sha256": _ordered_root(
                    stable_entries, include_origin=True
                ),
                "ordered_spec_root_sha256": _ordered_root(
                    stable_entries, include_origin=False
                ),
                "theorem_count": EXPECTED_STABLE_COUNT,
            },
        },
        "default_channel": "stable",
        "policy": (
            "Stable is the official checked library. Alpha is the cumulative "
            "building library and contains mixed evidence; checked_use is explicit. "
            "Stable is a keyed exact subset of Alpha with its own append-only, "
            "dependency-topological release order. A future promotion publishes a "
            "new snapshot while retaining Alpha enrollment origin, provenance, "
            "source, and canonical position."
        ),
        "schema": CHANNEL_SCHEMA,
    }
    channels["channel_pointer_root_sha256"] = _digest(_compact(channels["channels"]))
    return alpha_text, alpha_metrics_text, alpha_graph, _canonical_json(channels)


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
    parser.add_argument("--check", action="store_true", help="fail if committed artifacts drift")
    parser.add_argument("--alpha-output", type=Path, default=DEFAULT_ALPHA)
    parser.add_argument("--alpha-metrics-output", type=Path, default=DEFAULT_ALPHA_METRICS)
    parser.add_argument("--alpha-graph-output", type=Path, default=DEFAULT_ALPHA_GRAPH)
    parser.add_argument("--channels-output", type=Path, default=DEFAULT_CHANNELS)
    args = parser.parse_args(argv)
    alpha_text, alpha_metrics_text, alpha_graph, channels_text = build_payloads()
    _check_or_write(args.alpha_output.resolve(), alpha_text, check=args.check)
    _check_or_write(
        args.alpha_metrics_output.resolve(), alpha_metrics_text, check=args.check
    )
    _check_or_write(args.alpha_graph_output.resolve(), alpha_graph, check=args.check)
    _check_or_write(args.channels_output.resolve(), channels_text, check=args.check)
    action = "verified" if args.check else "wrote"
    print(
        f"{action} Stable/Alpha channels: stable={EXPECTED_STABLE_COUNT}, "
        f"alpha={EXPECTED_ALPHA_COUNT}, checked-use={EXPECTED_CHECKED_USE_COUNT}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
