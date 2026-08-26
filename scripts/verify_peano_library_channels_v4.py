#!/usr/bin/env python3
"""Fail-closed verifier for additive Alpha-v4 Bertrand artifacts."""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
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

import build_peano_library_channels_v4 as builder  # noqa: E402
import verify_peano_library_channels_v3 as v3_verifier  # noqa: E402
from peano_lab.library.alpha_enrollment_v4 import (  # noqa: E402
    BERTRAND_RFC_PATH,
    BERTRAND_V4_EXPECTED_COUNT,
    BERTRAND_V4_START_INDEX,
    alpha_v4_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v4 import (  # noqa: E402
    ALPHA_ENTRIES,
    ALPHA_V4_ENROLLMENT_SHA256,
    ALPHA_V4_IDENTITY_SHA256,
)


SCHEMA = "peano-library-alpha-snapshot-v4"
METRICS_SCHEMA = "peano-library-alpha-metrics-v4"
CHANNEL_SCHEMA = "peano-library-channels-v4"
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")


class ChannelV4Error(ValueError):
    """An Alpha-v4 artifact violates the sealed additive contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise ChannelV4Error(f"{location}: {message}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ChannelV4Error(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(
            path.read_text(encoding="utf-8"), object_pairs_hook=_pairs
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChannelV4Error(
            f"{path}: invalid strict UTF-8 JSON: {exc}"
        ) from exc
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


def _expected_receipt(receipt: object) -> dict[str, object]:
    result = asdict(receipt)
    result["dne_command_count"] = 0
    result["status"] = "kernel_checked_dependency_curried_body"
    return result


def _verify_parent(root: Path) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    artifact_root = root / "artifacts/peano-library"
    alpha = artifact_root / "alpha/catalog-v3.json"
    metrics = artifact_root / "alpha/metrics-v3.json"
    graph = artifact_root / "alpha/dependency-graph-v3.mmd"
    channels = artifact_root / "channels-v3.json"
    try:
        v3_verifier.validate_channels_v3(
            root,
            alpha,
            metrics,
            graph,
            channels,
            replay_bodies=False,
        )
    except Exception as exc:
        raise ChannelV4Error(
            f"sealed Alpha v3 parent failed validation: {exc}"
        ) from exc
    expected = {
        alpha: builder.EXPECTED_PARENT_ALPHA_SHA256,
        metrics: builder.EXPECTED_PARENT_METRICS_SHA256,
        graph: builder.EXPECTED_PARENT_GRAPH_SHA256,
        channels: builder.EXPECTED_PARENT_CHANNELS_SHA256,
    }
    for path, digest in expected.items():
        if _digest(path.read_bytes()) != digest:
            _fail(str(path), "parent Alpha v3 byte digest changed")
    return _load(alpha), _load(metrics), _load(channels)


def _verify_document_table(
    root: Path,
    alpha_path: Path,
    alpha: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    documents = alpha.get("evidence_documents")
    if type(documents) is not list or not documents:
        _fail(f"{alpha_path}.evidence_documents", "must be a non-empty list")
    documented: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(documents):
        location = f"{alpha_path}.evidence_documents[{index}]"
        if type(raw) is not dict:
            _fail(location, "must be an object")
        descriptor: dict[str, Any] = raw
        path = _repo_file(root, descriptor.get("path"), f"{location}.path")
        expected = _sha(descriptor.get("sha256"), f"{location}.sha256")
        payload = path.read_bytes()
        if _digest(payload) != expected or descriptor.get("bytes") != len(payload):
            _fail(location, "document byte binding does not match repository")
        raw_path = descriptor["path"]
        if raw_path in documented:
            _fail(location, "duplicates a document path")
        if type(descriptor.get("role")) is not str or not descriptor["role"]:
            _fail(f"{location}.role", "must be a non-empty string")
        documented[raw_path] = descriptor

    enrollment = alpha_v4_enrollment()
    required = {
        "peano-lab/py/peano_lab/library/alpha_enrollment_v4.py",
        "peano-lab/py/peano_lab/library/editions_v4.py",
        BERTRAND_RFC_PATH,
        "artifacts/peano-library/alpha/catalog-v3.json",
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
    }
    missing = sorted(required - set(documented))
    if missing:
        _fail(
            f"{alpha_path}.evidence_documents",
            f"missing exact v4 control/source/test/RFC/parent documents {missing!r}",
        )
    return documented


def _expected_topology(
    rows: list[dict[str, Any]],
    parent_metrics: dict[str, Any],
) -> tuple[dict[str, object], str]:
    depths, closures, kept_edges, redundant_edges = (
        builder.v3_builder.v2_builder.v1._dependency_analysis(rows)
    )
    if (
        len(kept_edges) + len(redundant_edges) != builder.EXPECTED_EDGE_COUNT
        or max(depths.values(), default=-1) + 1 != builder.EXPECTED_LAYER_COUNT
    ):
        _fail("Alpha v4 topology", "runtime edge/layer seal changed")
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
        _fail("Alpha v4 topology", "display reduction changed reachability")
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
    topology: dict[str, object] = {
        "declared_edge_count": builder.EXPECTED_EDGE_COUNT,
        "dependency_free_theorem_count": sum(
            not row["dependencies"] for row in rows
        ),
        "layer_count": builder.EXPECTED_LAYER_COUNT,
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
        "reachability_reduction_scope": parent_metrics["dependency_graph"][
            "reachability_reduction_scope"
        ],
        "theorems_by_depth": {
            str(depth): count for depth, count in sorted(depth_counts.items())
        },
        "transitive_reduction_edge_count": len(kept_edges),
        "transitive_reduction_edge_sha256": _digest(_compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True,
    }
    return topology, builder._alpha_graph(rows, kept_edges, redundant_edges)


def validate_channels_v4(
    root: Path,
    alpha_path: Path,
    metrics_path: Path,
    graph_path: Path,
    channels_path: Path,
    *,
    replay_bodies: bool = False,
) -> dict[str, int]:
    """Validate the exact v3 prefix, v4 append, and complete artifact family."""

    root = root.resolve()
    parent, parent_metrics, parent_channels = _verify_parent(root)
    alpha = _load(alpha_path)
    metrics = _load(metrics_path)
    channels = _load(channels_path)
    try:
        graph = graph_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ChannelV4Error(f"{graph_path}: unreadable UTF-8 graph: {exc}") from exc

    if alpha.get("schema") != SCHEMA:
        _fail(str(alpha_path), "Alpha-v4 schema changed")
    if metrics.get("schema") != METRICS_SCHEMA:
        _fail(str(metrics_path), "Alpha-v4 metrics schema changed")
    if channels.get("schema") != CHANNEL_SCHEMA:
        _fail(str(channels_path), "Alpha-v4 channels schema changed")

    parent_rows = parent.get("theorems")
    rows = alpha.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != 923:
        _fail("Alpha v3 parent", "must contain exactly 923 rows")
    if type(rows) is not list or len(rows) != 965:
        _fail(f"{alpha_path}.theorems", "must contain exactly 965 rows")
    if rows[:923] != parent_rows:
        _fail(f"{alpha_path}.theorems", "first 923 rows differ from exact v3 parent")
    if alpha.get("parent_alpha_v3") != builder._parent_binding():
        _fail(f"{alpha_path}.parent_alpha_v3", "complete sealed v3 binding changed")

    documented = _verify_document_table(root, alpha_path, alpha)
    enrollment = alpha_v4_enrollment()
    appended_entries = ALPHA_ENTRIES[BERTRAND_V4_START_INDEX:]
    appended_rows = rows[BERTRAND_V4_START_INDEX:]
    if len(appended_rows) != BERTRAND_V4_EXPECTED_COUNT:
        _fail(f"{alpha_path}.theorems", "Round-2 append count changed")
    positions = {str(row["name"]): index for index, row in enumerate(parent_rows)}
    parent_document = documented["artifacts/peano-library/alpha/catalog-v3.json"]
    for offset, (entry, row) in enumerate(
        zip(appended_entries, appended_rows, strict=True)
    ):
        index = BERTRAND_V4_START_INDEX + offset
        location = f"{alpha_path}.theorems[{index}]"
        spec = entry.spec
        if row.get("enrollment_index") != index or row.get("name") != spec.name:
            _fail(location, "index or theorem order changed")
        dependencies = row.get("dependencies")
        script = row.get("script")
        if type(dependencies) is not list or not all(
            type(item) is str for item in dependencies
        ):
            _fail(f"{location}.dependencies", "must be a string list")
        if type(script) is not list or not all(type(item) is str for item in script):
            _fail(f"{location}.script", "must be a string list")
        if len(set(dependencies)) != len(dependencies):
            _fail(f"{location}.dependencies", "contains duplicates")
        for dependency in dependencies:
            if dependency not in positions or positions[dependency] >= index:
                _fail(
                    f"{location}.dependencies",
                    f"{dependency!r} is missing or not earlier",
                )

        origin = entry.enrollment_origin.value
        source_path = enrollment.source_by_name[spec.name]
        test_path = enrollment.test_by_name[spec.name]
        exact = (
            row.get("statement"),
            tuple(dependencies),
            tuple(script),
            row.get("summary"),
            row.get("enrollment_origin"),
            row.get("provenance"),
        )
        expected_exact = (
            spec.statement,
            spec.dependencies,
            spec.script,
            spec.summary,
            origin,
            [origin],
        )
        if exact != expected_exact:
            _fail(location, "does not match frozen Round-2 runtime specification")

        statement_sha = _digest(spec.statement)
        dependencies_sha = _digest("\n".join(spec.dependencies) + "\n")
        script_sha = _digest("\n".join(spec.script) + "\n")
        logical_sha = builder.v3_builder.v2_builder.v1._logical_spec_sha256(spec)
        hash_expectations = {
            "statement_sha256": statement_sha,
            "dependencies_sha256": dependencies_sha,
            "script_sha256": script_sha,
            "logical_spec_sha256": logical_sha,
            "summary_sha256": _digest(spec.summary),
        }
        for field, expected in hash_expectations.items():
            if row.get(field) != expected:
                _fail(f"{location}.{field}", "does not bind exact content")

        source_document = documented[source_path]
        test_document = documented[test_path]
        rfc_document = documented[BERTRAND_RFC_PATH]
        expected_source = {
            "kind": "candidate_module",
            "path": source_path,
            "sha256": source_document["sha256"],
        }
        if row.get("source") != expected_source:
            _fail(f"{location}.source", "source path/digest semantics changed")
        expected_links = [
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
            {
                "document_sha256": parent_document["sha256"],
                "kind": "sealed_alpha_v3_parent",
                "path": "artifacts/peano-library/alpha/catalog-v3.json",
                "role": "exact_parent_catalog_bytes",
                "selector": "document",
            },
        ]
        if row.get("evidence_links") != expected_links:
            _fail(f"{location}.evidence_links", "evidence byte links changed")
        bundle = builder._bundle_payload(
            name=spec.name,
            origin=origin,
            statement_sha256=statement_sha,
            dependencies_sha256=dependencies_sha,
            logical_spec_sha256=logical_sha,
            source_sha256=str(source_document["sha256"]),
            test_sha256=str(test_document["sha256"]),
            rfc_sha256=str(rfc_document["sha256"]),
            parent_catalog_sha256=str(parent_document["sha256"]),
        )
        if row.get("bertrand_v4_evidence_bundle_sha256") != _digest(
            _compact(bundle)
        ):
            _fail(
                f"{location}.bertrand_v4_evidence_bundle_sha256",
                "does not cross-bind source/test/RFC/parent bytes",
            )
        if row.get("proof_tag") is not None:
            _fail(f"{location}.proof_tag", "body-only Round-2 rows are untagged")
        if (
            row.get("membership") != "alpha_only"
            or row.get("evidence_status") != "body_checked"
            or row.get("body_checked") is not True
            or row.get("checked_use") is not False
            or row.get("empty_context_closure") is not None
        ):
            _fail(location, "fabricated closure or checked-use upgrade")
        positions[spec.name] = index

    evidence_counts = Counter(str(row["evidence_status"]) for row in rows)
    membership_counts = Counter(str(row["membership"]) for row in rows)
    origin_counts = Counter(str(row["enrollment_origin"]) for row in rows)
    expected_counts = {
        "evidence_counts": {
            "alpha_closed": 138,
            "body_checked": 394,
            "pending_layered_closure": 1,
            "stable_closed": 432,
        },
        "membership_counts": {"alpha_only": 533, "stable": 432},
        "enrollment_origin_counts": {
            "bertrand_b0_interval": 4,
            "bertrand_b1_power_growth": 3,
            "bertrand_b1_power_order": 4,
            "bertrand_b2_bounded_valuation": 10,
            "bertrand_b2_valuation_laws": 6,
            "bertrand_b2_valuation_multiplication": 11,
            "bertrand_b6_ceil_sqrt": 9,
            "bertrand_b6_floor_sqrt_total": 4,
            "bertrand_b6_integer_envelope": 5,
            "bertrand_b6_quotient_budget": 7,
            "ha": 120,
            "k3b": 17,
            "k3c": 17,
            "qr": 316,
            "stable": 432,
        },
    }
    if dict(sorted(evidence_counts.items())) != expected_counts["evidence_counts"]:
        _fail(str(alpha_path), "evidence counts changed")
    if dict(sorted(membership_counts.items())) != expected_counts["membership_counts"]:
        _fail(str(alpha_path), "membership counts changed")
    if dict(sorted(origin_counts.items())) != expected_counts["enrollment_origin_counts"]:
        _fail(str(alpha_path), "enrollment-origin counts changed")
    for field, expected in expected_counts.items():
        if alpha.get(field) != expected:
            _fail(f"{alpha_path}.{field}", "does not match theorem rows")

    enrollment_root = builder.v3_builder.v2_builder.v1._ordered_root(
        ALPHA_ENTRIES, include_origin=True
    )
    spec_root = builder.v3_builder.v2_builder.v1._ordered_root(
        ALPHA_ENTRIES, include_origin=False
    )
    scalar_expectations = {
        "theorem_count": 965,
        "stable_count": 432,
        "alpha_only_count": 533,
        "checked_use_count": 570,
        "edge_count": 2891,
        "layer_count": 45,
        "edition_identity_sha256": ALPHA_V4_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": ALPHA_V4_ENROLLMENT_SHA256,
        "ordered_spec_root_sha256": spec_root,
        "membership_root_sha256": builder.v3_builder.v2_builder.v1._membership_root(rows),
        "evidence_root_sha256": builder.v3_builder.v2_builder.v1._evidence_root(rows),
        "bertrand_v4_evidence_bundle_scheme": (
            builder.BERTRAND_V4_EVIDENCE_BUNDLE_SCHEME
        ),
        "bertrand_v4_evidence_bundle_scheme_sha256": _digest(
            _compact(builder.BERTRAND_V4_EVIDENCE_BUNDLE_SCHEME)
        ),
    }
    for field, expected in scalar_expectations.items():
        if alpha.get(field) != expected:
            _fail(f"{alpha_path}.{field}", "does not match runtime/row seal")

    topology, expected_graph = _expected_topology(rows, parent_metrics)
    if graph != expected_graph:
        _fail(str(graph_path), "is not the canonical reduced Alpha-v4 graph")
    expected_metrics = deepcopy(parent_metrics)
    expected_metrics.update(
        {
            "catalog_path": "artifacts/peano-library/alpha/catalog-v4.json",
            "catalog_sha256": _digest(alpha_path.read_bytes()),
            "checked_use_count": 570,
            "dependency_graph": topology,
            "dependency_graph_path": (
                "artifacts/peano-library/alpha/dependency-graph-v4.mmd"
            ),
            "dependency_graph_sha256": _digest(graph_path.read_bytes()),
            "edition_identity_sha256": ALPHA_V4_IDENTITY_SHA256,
            "evidence_counts": expected_counts["evidence_counts"],
            "ordered_enrollment_root_sha256": enrollment_root,
            "ordered_spec_root_sha256": spec_root,
            "parent_alpha_v3": builder._parent_binding(),
            "schema": METRICS_SCHEMA,
            "theorem_count": 965,
        }
    )
    expected_metrics["checked_closure_metrics"][
        "missing_empty_context_metric_count"
    ] = 395
    expected_metrics["promotion_gates"]["canonical_topology"].update(
        theorem_count=965, declared_edge_count=2891
    )
    expected_metrics["promotion_gates"]["dependency_link_analysis"][
        "reachability_redundant_direct_dependency_count"
    ] = topology["reachability_redundant_direct_dependency_count"]
    expected_metrics["promotion_gates"]["full_alpha_empty_context_compilation"].update(
        checked=570, required=965, missing=395
    )
    expected_metrics["promotion_gates"]["source_integrity"][
        "source_bound_theorem_count"
    ] = 965
    if metrics != expected_metrics:
        _fail(str(metrics_path), "does not match canonical Alpha-v4 metrics")

    channel_rows = channels.get("channels")
    if type(channel_rows) is not dict or set(channel_rows) != {"stable", "alpha"}:
        _fail(f"{channels_path}.channels", "must contain Stable and Alpha")
    if channel_rows["stable"] != parent_channels["channels"]["stable"]:
        _fail(f"{channels_path}.channels.stable", "exact Stable pointers changed")
    expected_artifacts = {
        "catalog": {
            "path": "artifacts/peano-library/alpha/catalog-v4.json",
            "sha256": _digest(alpha_path.read_bytes()),
        },
        "dependency_graph": {
            "path": "artifacts/peano-library/alpha/dependency-graph-v4.mmd",
            "sha256": _digest(graph_path.read_bytes()),
        },
        "metrics": {
            "path": "artifacts/peano-library/alpha/metrics-v4.json",
            "sha256": _digest(metrics_path.read_bytes()),
        },
    }
    alpha_channel = channel_rows["alpha"]
    if alpha_channel.get("artifacts") != expected_artifacts:
        _fail(f"{channels_path}.channels.alpha.artifacts", "artifact pointers changed")
    channel_expectations = {
        "artifact_path": expected_artifacts["catalog"]["path"],
        "artifact_sha256": expected_artifacts["catalog"]["sha256"],
        "checked_use_count": 570,
        "edition_identity_sha256": ALPHA_V4_IDENTITY_SHA256,
        "evidence_counts": expected_counts["evidence_counts"],
        "evidence_root_sha256": alpha["evidence_root_sha256"],
        "membership_root_sha256": alpha["membership_root_sha256"],
        "ordered_enrollment_root_sha256": enrollment_root,
        "ordered_spec_root_sha256": spec_root,
        "parent_alpha_v3_sha256": builder.EXPECTED_PARENT_ALPHA_SHA256,
        "theorem_count": 965,
    }
    for field, expected in channel_expectations.items():
        if alpha_channel.get(field) != expected:
            _fail(f"{channels_path}.channels.alpha.{field}", "does not mirror catalog")
    if channels.get("default_channel") != "stable":
        _fail(f"{channels_path}.default_channel", "must remain Stable")
    if channels.get("policy") != parent_channels.get("policy"):
        _fail(f"{channels_path}.policy", "channel policy changed")
    expected_parent_channels = {
        "path": "artifacts/peano-library/channels-v3.json",
        "sha256": builder.EXPECTED_PARENT_CHANNELS_SHA256,
    }
    if channels.get("parent_channels_v3") != expected_parent_channels:
        _fail(f"{channels_path}.parent_channels_v3", "parent channel binding changed")
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
        core = {
            entry.spec.name: entry.spec
            for entry in ALPHA_ENTRIES[:BERTRAND_V4_START_INDEX]
        }
        receipts = replay_candidate_bodies(
            tuple(entry.spec for entry in appended_entries),
            core=core,
        )
        for row, receipt in zip(appended_rows, receipts, strict=True):
            if row.get("body_receipt") != _expected_receipt(receipt):
                _fail(
                    f"{alpha_path}.theorems[{row['enrollment_index']}].body_receipt",
                    "does not match independent kernel body replay",
                )

    return {
        "alpha": 965,
        "alpha_closed": 138,
        "body_checked": 394,
        "checked_use": 570,
        "round2_replayed": 42 if replay_bodies else 0,
        "stable": 432,
    }


def main() -> int:
    result = validate_channels_v4(
        ROOT,
        ARTIFACT_ROOT / "alpha/catalog-v4.json",
        ARTIFACT_ROOT / "alpha/metrics-v4.json",
        ARTIFACT_ROOT / "alpha/dependency-graph-v4.mmd",
        ARTIFACT_ROOT / "channels-v4.json",
    )
    print(
        "verified Alpha v4: "
        f"stable={result['stable']}, alpha={result['alpha']}, "
        f"checked-use={result['checked_use']}, "
        f"Round-2-replayed={result['round2_replayed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
