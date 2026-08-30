#!/usr/bin/env python3
"""Fail-closed verifier for the additive Alpha-v2 K3C artifact family.

The verifier first validates the complete v1 parent family with the v1
verifier, then checks exact prefix preservation, source and control-file byte
bindings, all roots/topology/pointers, checked-use separation, and finally
replays all seventeen K3C dependency-curried bodies through the kernel.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels_v2 as builder  # noqa: E402
import verify_peano_library_channels as v1_verifier  # noqa: E402
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v2 import (  # noqa: E402
    ALPHA_ENTRIES,
    ALPHA_V2_ENROLLMENT_SHA256,
    ALPHA_V2_IDENTITY_SHA256,
    K3C_START_INDEX,
)


SCHEMA = "peano-library-alpha-snapshot-v2"
METRICS_SCHEMA = "peano-library-alpha-metrics-v2"
CHANNEL_SCHEMA = "peano-library-channels-v2"
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EVIDENCE_STATUSES = {
    "stable_closed",
    "alpha_closed",
    "body_checked",
    "pending_layered_closure",
}
CLOSED_EVIDENCE = {"stable_closed", "alpha_closed"}
ORIGINS = {"stable", "qr", "ha", "k3b", "k3c"}
MEMBERSHIPS = {"stable", "alpha_only"}


class ChannelV2Error(ValueError):
    """An Alpha-v2 artifact violates the sealed additive contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise ChannelV2Error(f"{location}: {message}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ChannelV2Error(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChannelV2Error(f"{path}: invalid strict UTF-8 JSON: {exc}") from exc
    if type(value) is not dict:
        _fail(str(path), "top-level value must be an object")
    return value


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


def _sha(value: object, location: str) -> str:
    if type(value) is not str or HEX_SHA256.fullmatch(value) is None:
        _fail(location, "must be a lowercase SHA-256")
    return value


def _repo_file(root: Path, raw: object, location: str) -> Path:
    if type(raw) is not str or not raw:
        _fail(location, "must be a non-empty repository-relative path")
    posix = PurePosixPath(raw)
    if posix.is_absolute() or "." in posix.parts or ".." in posix.parts:
        _fail(location, "must be a normalized repository-relative path")
    result = (root / Path(*posix.parts)).resolve()
    try:
        result.relative_to(root.resolve())
    except ValueError:
        _fail(location, "escapes repository root")
    if not result.is_file():
        _fail(location, f"missing file {raw!r}")
    return result


def _logical_spec(row: dict[str, Any]) -> dict[str, object]:
    return {
        "dependencies": row["dependencies"],
        "name": row["name"],
        "script": row["script"],
        "statement": row["statement"],
    }


def _expected_receipt(receipt: object) -> dict[str, object]:
    result = asdict(receipt)
    result["dne_command_count"] = 0
    result["status"] = "kernel_checked_dependency_curried_body"
    return result


def _verify_v1_parent(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    parent_alpha = root / "artifacts/peano-library/alpha/catalog-v1.json"
    parent_metrics = root / "artifacts/peano-library/alpha/metrics.json"
    parent_graph = root / "artifacts/peano-library/alpha/dependency-graph.mmd"
    parent_channels_path = root / "artifacts/peano-library/channels.json"
    stable = root / "artifacts/peano-library/catalog-v1.json"
    stable_metrics = root / "artifacts/peano-library/metrics.json"
    stable_graph = root / "artifacts/peano-library/dependency-graph.mmd"
    try:
        v1_verifier.validate_channels(
            root,
            parent_alpha,
            parent_metrics,
            parent_graph,
            parent_channels_path,
            stable,
            stable_metrics,
            stable_graph,
        )
    except Exception as exc:
        raise ChannelV2Error(f"sealed Alpha v1 parent failed validation: {exc}") from exc
    if _digest(parent_alpha.read_bytes()) != builder.EXPECTED_PARENT_ALPHA_SHA256:
        _fail(str(parent_alpha), "parent Alpha v1 byte digest changed")
    return _load(parent_alpha), _load(parent_channels_path)


def validate_channels_v2(
    repository_root: Path,
    alpha_path: Path,
    metrics_path: Path,
    graph_path: Path,
    channels_path: Path,
    *,
    replay_bodies: bool = True,
) -> dict[str, int]:
    """Validate one complete v2 family rooted at ``repository_root``."""

    root = repository_root.resolve()
    parent, parent_channels = _verify_v1_parent(root)
    alpha = _load(alpha_path)
    metrics = _load(metrics_path)
    channels = _load(channels_path)
    try:
        graph = graph_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ChannelV2Error(f"{graph_path}: cannot read UTF-8 graph: {exc}") from exc

    if alpha.get("schema") != SCHEMA or alpha.get("channel") != "alpha":
        _fail(str(alpha_path), f"expected {SCHEMA!r} Alpha catalog")
    if metrics.get("schema") != METRICS_SCHEMA or metrics.get("channel") != "alpha":
        _fail(str(metrics_path), f"expected {METRICS_SCHEMA!r} Alpha metrics")
    if channels.get("schema") != CHANNEL_SCHEMA:
        _fail(str(channels_path), f"expected {CHANNEL_SCHEMA!r}")
    if channels.get("default_channel") != "stable":
        _fail(f"{channels_path}.default_channel", "must remain stable")

    parent_binding = alpha.get("parent_alpha_v1")
    expected_parent_binding = {
        "artifact_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "ordered_enrollment_root_sha256": builder.EXPECTED_PARENT_ENROLLMENT_ROOT,
        "path": "artifacts/peano-library/alpha/catalog-v1.json",
        "schema": "peano-library-alpha-snapshot-v1",
        "theorem_count": builder.EXPECTED_PARENT_COUNT,
    }
    if parent_binding != expected_parent_binding:
        _fail(f"{alpha_path}.parent_alpha_v1", "does not exactly bind sealed v1 parent")

    rows = alpha.get("theorems")
    parent_rows = parent.get("theorems")
    if type(rows) is not list or len(rows) != builder.EXPECTED_ALPHA_COUNT:
        _fail(f"{alpha_path}.theorems", "must contain exactly 902 rows")
    if type(parent_rows) is not list or rows[:builder.EXPECTED_PARENT_COUNT] != parent_rows:
        _fail(f"{alpha_path}.theorems", "first 885 rows do not exactly preserve Alpha v1")

    documents = alpha.get("evidence_documents")
    if type(documents) is not list or not documents:
        _fail(f"{alpha_path}.evidence_documents", "must be a non-empty list")
    documented: dict[str, dict[str, Any]] = {}
    for index, descriptor in enumerate(documents):
        location = f"{alpha_path}.evidence_documents[{index}]"
        if type(descriptor) is not dict:
            _fail(location, "must be an object")
        path = _repo_file(root, descriptor.get("path"), f"{location}.path")
        expected = _sha(descriptor.get("sha256"), f"{location}.sha256")
        payload = path.read_bytes()
        if _digest(payload) != expected or descriptor.get("bytes") != len(payload):
            _fail(location, "document byte binding does not match repository")
        raw_path = descriptor["path"]
        if raw_path in documented:
            _fail(location, "duplicates a document path")
        documented[raw_path] = descriptor
    required_documents = {
        "artifacts/peano-library/alpha/catalog-v1.json",
        *builder.CONTROL_DOCUMENTS,
        *(entry.source_module for entry in ALPHA_ENTRIES[K3C_START_INDEX:]),
    }
    if not required_documents <= set(documented):
        _fail(f"{alpha_path}.evidence_documents", "missing a v2 control/source binding")
    for path, role in builder.CONTROL_DOCUMENTS.items():
        if documented[path].get("role") != role:
            _fail(
                f"{alpha_path}.evidence_documents[{path!r}].role",
                "does not match the sealed control/audit-document role",
            )

    names: set[str] = set()
    positions: dict[str, int] = {}
    evidence_counts: Counter[str] = Counter()
    membership_counts: Counter[str] = Counter()
    origin_counts: Counter[str] = Counter()
    for index, raw in enumerate(rows):
        location = f"{alpha_path}.theorems[{index}]"
        if type(raw) is not dict:
            _fail(location, "must be an object")
        row: dict[str, Any] = raw
        name = row.get("name")
        if type(name) is not str or re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
            _fail(f"{location}.name", "must be a theorem identifier")
        if name in names:
            _fail(f"{location}.name", "duplicates an earlier theorem")
        if row.get("enrollment_index") != index:
            _fail(f"{location}.enrollment_index", "must equal list position")
        for field in ("statement", "summary"):
            if type(row.get(field)) is not str:
                _fail(f"{location}.{field}", "must be a string")
        for field in ("dependencies", "script", "provenance", "evidence_links"):
            value = row.get(field)
            if type(value) is not list or any(type(item) is not str for item in value if field != "evidence_links"):
                _fail(f"{location}.{field}", "has invalid list shape")
        dependencies = row["dependencies"]
        if len(set(dependencies)) != len(dependencies):
            _fail(f"{location}.dependencies", "contains duplicates")
        for dependency in dependencies:
            if dependency not in positions or positions[dependency] >= index:
                _fail(f"{location}.dependencies", f"{dependency!r} is missing or not earlier")
        evidence = row.get("evidence_status")
        membership = row.get("membership")
        origin = row.get("enrollment_origin")
        if evidence not in EVIDENCE_STATUSES:
            _fail(f"{location}.evidence_status", "unknown evidence status")
        if membership not in MEMBERSHIPS:
            _fail(f"{location}.membership", "unknown membership")
        if origin not in ORIGINS:
            _fail(f"{location}.enrollment_origin", "unknown enrollment origin")
        checked_use = row.get("checked_use")
        if type(checked_use) is not bool or checked_use != (evidence in CLOSED_EVIDENCE):
            _fail(f"{location}.checked_use", "does not fail closed from evidence status")
        closure = row.get("empty_context_closure")
        if checked_use and (type(closure) is not dict or closure.get("status") != "checked"):
            _fail(f"{location}.empty_context_closure", "checked-use row lacks checked closure")
        if evidence == "body_checked" and closure is not None:
            _fail(f"{location}.empty_context_closure", "body-only row cannot claim closure")
        if row.get("body_checked") is not True:
            _fail(f"{location}.body_checked", "must be true")
        hash_expectations = {
            "statement_sha256": _digest(row["statement"]),
            "summary_sha256": _digest(row["summary"]),
            "dependencies_sha256": _digest("\n".join(dependencies) + "\n"),
            "script_sha256": _digest("\n".join(row["script"]) + "\n"),
            "logical_spec_sha256": _digest(_compact(_logical_spec(row))),
        }
        for field, expected in hash_expectations.items():
            if row.get(field) != expected:
                _fail(f"{location}.{field}", "does not bind its exact content")
        source = row.get("source")
        if type(source) is not dict:
            _fail(f"{location}.source", "must be an object")
        source_path = _repo_file(root, source.get("path"), f"{location}.source.path")
        if source.get("sha256") != _digest(source_path.read_bytes()):
            _fail(f"{location}.source.sha256", "does not match source bytes")
        for link_index, link in enumerate(row["evidence_links"]):
            link_location = f"{location}.evidence_links[{link_index}]"
            if type(link) is not dict or link.get("path") not in documented:
                _fail(link_location, "does not address a documented file")
            if link.get("document_sha256") != documented[link["path"]]["sha256"]:
                _fail(link_location, "document digest does not match descriptor")
        names.add(name)
        positions[name] = index
        evidence_counts[evidence] += 1
        membership_counts[membership] += 1
        origin_counts[origin] += 1

    k3c_rows = rows[K3C_START_INDEX:]
    k3c_entries = ALPHA_ENTRIES[K3C_START_INDEX:]
    for offset, (row, entry) in enumerate(zip(k3c_rows, k3c_entries, strict=True)):
        location = f"{alpha_path}.theorems[{K3C_START_INDEX + offset}]"
        spec = entry.spec
        exact = (
            row["name"],
            row["statement"],
            tuple(row["dependencies"]),
            tuple(row["script"]),
            row["summary"],
            row["source"]["path"],
        )
        expected = (
            spec.name,
            spec.statement,
            spec.dependencies,
            spec.script,
            spec.summary,
            entry.source_module,
        )
        if exact != expected:
            _fail(location, "does not match frozen K3C runtime specification/source")
        source_document = documented[entry.source_module]
        expected_source = {
            "kind": "candidate_module",
            "path": entry.source_module,
            "sha256": source_document["sha256"],
        }
        if row["source"] != expected_source:
            _fail(
                f"{location}.source",
                "K3C source kind/path/digest semantics changed",
            )
        expected_evidence_links = [
            {
                "document_sha256": source_document["sha256"],
                "kind": "k3c_dependency_curried_body",
                "path": entry.source_module,
                "role": "dependency_curried_body",
                "selector": "document",
            }
        ]
        if row["evidence_links"] != expected_evidence_links:
            _fail(
                f"{location}.evidence_links",
                "K3C evidence-link kind/role/selector semantics changed",
            )
        if row.get("proof_tag") is not None:
            _fail(
                f"{location}.proof_tag",
                "K3C rows are untagged until a separately reviewed tag-registry edition",
            )
        if (
            row["membership"] != "alpha_only"
            or row["evidence_status"] != "body_checked"
            or row["enrollment_origin"] != "k3c"
            or row["provenance"] != ["k3c"]
            or row["checked_use"] is not False
            or row["empty_context_closure"] is not None
        ):
            _fail(location, "K3C release/evidence separation changed")

    expected_counts = {
        "evidence_counts": {
            "alpha_closed": 138,
            "body_checked": 331,
            "pending_layered_closure": 1,
            "stable_closed": 432,
        },
        "membership_counts": {"alpha_only": 470, "stable": 432},
        "enrollment_origin_counts": {
            "ha": 120,
            "k3b": 17,
            "k3c": 17,
            "qr": 316,
            "stable": 432,
        },
    }
    actual_counts = {
        "evidence_counts": dict(sorted(evidence_counts.items())),
        "membership_counts": dict(sorted(membership_counts.items())),
        "enrollment_origin_counts": dict(sorted(origin_counts.items())),
    }
    if actual_counts != expected_counts:
        _fail(str(alpha_path), f"channel counts changed: {actual_counts!r}")
    for field, expected in expected_counts.items():
        if alpha.get(field) != expected:
            _fail(f"{alpha_path}.{field}", "does not match theorem rows")
    if alpha.get("theorem_count") != 902 or alpha.get("stable_count") != 432:
        _fail(str(alpha_path), "theorem/stable counts changed")
    if alpha.get("alpha_only_count") != 470 or alpha.get("checked_use_count") != 570:
        _fail(str(alpha_path), "alpha-only/checked-use counts changed")
    if alpha.get("edge_count") != 2674 or alpha.get("layer_count") != 45:
        _fail(str(alpha_path), "topology count seal changed")
    if alpha.get("edition_identity_sha256") != ALPHA_V2_IDENTITY_SHA256:
        _fail(f"{alpha_path}.edition_identity_sha256", "runtime identity changed")
    if alpha.get("ordered_enrollment_root_sha256") != ALPHA_V2_ENROLLMENT_SHA256:
        _fail(f"{alpha_path}.ordered_enrollment_root_sha256", "runtime enrollment root changed")
    if alpha.get("ordered_enrollment_root_scheme") != builder.v1.ORDERED_ENROLLMENT_ROOT_SCHEME:
        _fail(f"{alpha_path}.ordered_enrollment_root_scheme", "scheme changed")
    if alpha.get("ordered_enrollment_root_scheme_sha256") != _digest(
        _compact(builder.v1.ORDERED_ENROLLMENT_ROOT_SCHEME)
    ):
        _fail(f"{alpha_path}.ordered_enrollment_root_scheme_sha256", "scheme digest changed")
    if alpha.get("ordered_spec_root_sha256") != builder.v1._ordered_root(
        ALPHA_ENTRIES, include_origin=False
    ):
        _fail(f"{alpha_path}.ordered_spec_root_sha256", "specification root changed")
    if alpha.get("membership_root_sha256") != builder.v1._membership_root(rows):
        _fail(f"{alpha_path}.membership_root_sha256", "membership root changed")
    if alpha.get("evidence_root_sha256") != builder.v1._evidence_root(rows):
        _fail(f"{alpha_path}.evidence_root_sha256", "evidence root changed")

    depths, closures, kept_edges, redundant_edges = builder.v1._dependency_analysis(rows)
    if len(kept_edges) + len(redundant_edges) != 2674 or max(depths.values()) + 1 != 45:
        _fail(str(alpha_path), "recomputed topology disagrees with seal")
    expected_graph = builder._alpha_graph(rows, kept_edges, redundant_edges)
    if graph != expected_graph:
        _fail(str(graph_path), "is not the canonical reduced Alpha-v2 graph")

    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in redundant_edges
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    origin_by_name = {row["name"]: row["enrollment_origin"] for row in rows}
    redundant_by_origin = Counter(origin_by_name[theorem] for _, theorem in redundant_edges)
    depth_counts = Counter(depths.values())
    topology = metrics.get("dependency_graph")
    expected_topology = {
        "declared_edge_count": 2674,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": 45,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values())),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant_edges),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(
            sorted(redundant_by_origin.items())
        ),
        "reachability_redundant_direct_dependency_sha256": _digest(_compact(redundant_rows)),
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
    }
    if topology != expected_topology:
        _fail(f"{metrics_path}.dependency_graph", "is not canonical topology analysis")
    metric_expectations = {
        "catalog_path": "artifacts/peano-library/alpha/catalog-v2.json",
        "catalog_sha256": _digest(alpha_path.read_bytes()),
        "checked_use_count": 570,
        "dependency_graph_path": "artifacts/peano-library/alpha/dependency-graph-v2.mmd",
        "dependency_graph_sha256": _digest(graph_path.read_bytes()),
        "edition_identity_sha256": ALPHA_V2_IDENTITY_SHA256,
        "evidence_counts": expected_counts["evidence_counts"],
        "ordered_enrollment_root_sha256": ALPHA_V2_ENROLLMENT_SHA256,
        "ordered_spec_root_sha256": alpha["ordered_spec_root_sha256"],
        "parent_alpha_v1": expected_parent_binding,
        "theorem_count": 902,
    }
    for field, expected in metric_expectations.items():
        if metrics.get(field) != expected:
            _fail(f"{metrics_path}.{field}", "does not match catalog/graph/runtime")
    if metrics.get("checked_closure_metrics", {}).get(
        "missing_empty_context_metric_count"
    ) != 332:
        _fail(f"{metrics_path}.checked_closure_metrics", "missing-closure count changed")
    closure_gate = metrics.get("promotion_gates", {}).get(
        "full_alpha_empty_context_compilation", {}
    )
    if (closure_gate.get("checked"), closure_gate.get("required"), closure_gate.get("missing")) != (
        570,
        902,
        332,
    ):
        _fail(f"{metrics_path}.promotion_gates", "closure gate is not fail-closed")

    parent_pointer = channels.get("parent_channels_v1")
    expected_parent_pointer = {
        "path": "artifacts/peano-library/channels.json",
        "sha256": _digest((root / "artifacts/peano-library/channels.json").read_bytes()),
    }
    if parent_pointer != expected_parent_pointer:
        _fail(f"{channels_path}.parent_channels_v1", "does not bind v1 channels")
    channel_rows = channels.get("channels")
    if type(channel_rows) is not dict or set(channel_rows) != {"alpha", "stable"}:
        _fail(f"{channels_path}.channels", "must contain exactly Alpha and Stable")
    if channel_rows["stable"] != parent_channels["channels"]["stable"]:
        _fail(f"{channels_path}.channels.stable", "must preserve exact Stable pointers")
    expected_artifacts = {
        "catalog": {
            "path": "artifacts/peano-library/alpha/catalog-v2.json",
            "sha256": _digest(alpha_path.read_bytes()),
        },
        "dependency_graph": {
            "path": "artifacts/peano-library/alpha/dependency-graph-v2.mmd",
            "sha256": _digest(graph_path.read_bytes()),
        },
        "metrics": {
            "path": "artifacts/peano-library/alpha/metrics-v2.json",
            "sha256": _digest(metrics_path.read_bytes()),
        },
    }
    alpha_channel = channel_rows["alpha"]
    if alpha_channel.get("artifacts") != expected_artifacts:
        _fail(f"{channels_path}.channels.alpha.artifacts", "artifact family pointers changed")
    alpha_channel_expectations = {
        "artifact_path": expected_artifacts["catalog"]["path"],
        "artifact_sha256": expected_artifacts["catalog"]["sha256"],
        "checked_use_count": 570,
        "edition_identity_sha256": ALPHA_V2_IDENTITY_SHA256,
        "evidence_counts": expected_counts["evidence_counts"],
        "evidence_root_sha256": alpha["evidence_root_sha256"],
        "membership_root_sha256": alpha["membership_root_sha256"],
        "ordered_enrollment_root_sha256": ALPHA_V2_ENROLLMENT_SHA256,
        "ordered_spec_root_sha256": alpha["ordered_spec_root_sha256"],
        "parent_alpha_v1_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "theorem_count": 902,
    }
    for field, expected in alpha_channel_expectations.items():
        if alpha_channel.get(field) != expected:
            _fail(f"{channels_path}.channels.alpha.{field}", "does not mirror catalog")
    for channel_name, channel in channel_rows.items():
        for artifact_name, pointer in channel["artifacts"].items():
            path = _repo_file(
                root,
                pointer.get("path"),
                f"{channels_path}.channels.{channel_name}.artifacts.{artifact_name}.path",
            )
            if pointer.get("sha256") != _digest(path.read_bytes()):
                _fail(
                    f"{channels_path}.channels.{channel_name}.artifacts.{artifact_name}.sha256",
                    "does not match artifact bytes",
                )
    if channels.get("channel_pointer_root_sha256") != _digest(_compact(channel_rows)):
        _fail(f"{channels_path}.channel_pointer_root_sha256", "pointer root changed")

    if replay_bodies:
        core = {entry.spec.name: entry.spec for entry in ALPHA_ENTRIES[:K3C_START_INDEX]}
        receipts = replay_candidate_bodies(
            tuple(entry.spec for entry in k3c_entries),
            core=core,
        )
        for row, receipt in zip(k3c_rows, receipts, strict=True):
            if row.get("body_receipt") != _expected_receipt(receipt):
                _fail(
                    f"{alpha_path}.theorems[{row['enrollment_index']}].body_receipt",
                    "does not match independent kernel body replay",
                )

    return {
        "alpha": 902,
        "alpha_closed": 138,
        "body_checked": 331,
        "checked_use": 570,
        "k3c_replayed": 17 if replay_bodies else 0,
        "stable": 432,
    }


def main() -> int:
    result = validate_channels_v2(
        ROOT,
        ARTIFACT_ROOT / "alpha" / "catalog-v2.json",
        ARTIFACT_ROOT / "alpha" / "metrics-v2.json",
        ARTIFACT_ROOT / "alpha" / "dependency-graph-v2.mmd",
        ARTIFACT_ROOT / "channels-v2.json",
    )
    print(
        "verified Alpha v2: "
        f"stable={result['stable']}, alpha={result['alpha']}, "
        f"checked-use={result['checked_use']}, K3C-replayed={result['k3c_replayed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
