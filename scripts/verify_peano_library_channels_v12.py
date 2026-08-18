#!/usr/bin/env python3
"""Fail-closed verifier for the additive 180-row Alpha-v12 family."""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict
from hashlib import sha256
import json
from pathlib import Path
import sys
from typing import Any, NoReturn


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
SCRIPTS_ROOT = ROOT / "scripts"
ARTIFACT_ROOT = ROOT / "artifacts" / "peano-library"
for path in (PY_ROOT, SCRIPTS_ROOT):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_peano_library_channels_v12 as builder  # noqa: E402
from peano_lab.library.alpha_enrollment_v12 import (  # noqa: E402
    BERTRAND_V12_EXPECTED_COUNT,
    BERTRAND_V12_START_INDEX,
    alpha_v12_enrollment,
)
from peano_lab.library.candidate_validation import replay_candidate_bodies  # noqa: E402
from peano_lab.library.editions_v12 import (  # noqa: E402
    ALPHA_ENTRIES,
    ALPHA_V12_ENROLLMENT_SHA256,
    ALPHA_V12_IDENTITY_SHA256,
)


SCHEMA = "peano-library-alpha-snapshot-v12"
METRICS_SCHEMA = "peano-library-alpha-metrics-v12"
CHANNEL_SCHEMA = "peano-library-channels-v12"
EXPECTED_ARTIFACT_SHA256 = {
    "alpha": "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109",
    "metrics": "64da675a3144f4bb0875c2e0650064e72d5d3eb613542d217719280addfaacb4",
    "graph": "583d18473200097997fa6b8ef0b57ebef9da95f136555d97b24220f1abb356b8",
    "channels": "0063b6d25f6f27869b00af0d7a31f53dda22d82e8d9c30779309939b46c60982",
}


class ChannelV12Error(ValueError):
    """A v12 artifact, byte binding, or evidence boundary is invalid."""


def _fail(location: str, message: str) -> NoReturn:
    raise ChannelV12Error(f"{location}: {message}")


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChannelV12Error(f"{path}: unreadable JSON: {exc}") from exc
    if type(value) is not dict:
        _fail(str(path), "must contain a JSON object")
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


def _repo_file(root: Path, raw: object, location: str) -> Path:
    if type(raw) is not str or not raw or raw.startswith("/"):
        _fail(location, "must be a non-empty repository-relative path")
    path = (root / raw).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        _fail(location, "escapes the repository root")
    if not path.is_file():
        _fail(location, "does not name a regular file")
    return path


def _verify_parent(
    root: Path,
    *,
    validate_parent: bool,
) -> tuple[dict[str, Any], dict[str, Any]]:
    artifact_root = root / "artifacts/peano-library"
    alpha = artifact_root / "alpha/catalog-v11.json"
    metrics = artifact_root / "alpha/metrics-v11.json"
    graph = artifact_root / "alpha/dependency-graph-v11.mmd"
    channels = artifact_root / "channels-v11.json"
    if validate_parent:
        parent_alpha = _load(alpha)
        parent_channels = _load(channels)
        alpha_channel = parent_channels.get("channels", {}).get("alpha", {})
        if (
            parent_alpha.get("schema") != "peano-library-alpha-snapshot-v11"
            or parent_alpha.get("theorem_count") != builder.EXPECTED_PARENT_COUNT
            or parent_alpha.get("ordered_enrollment_root_sha256")
            != builder.EXPECTED_PARENT_ENROLLMENT_ROOT
            or parent_alpha.get("edition_identity_sha256")
            != builder.EXPECTED_PARENT_IDENTITY
            or parent_channels.get("schema") != "peano-library-channels-v11"
            or alpha_channel.get("theorem_count")
            != builder.EXPECTED_PARENT_COUNT
        ):
            _fail("sealed Alpha v11 parent", "schema or identity seal changed")
    expected = {
        alpha: builder.EXPECTED_PARENT_ALPHA_SHA256,
        metrics: builder.EXPECTED_PARENT_METRICS_SHA256,
        graph: builder.EXPECTED_PARENT_GRAPH_SHA256,
        channels: builder.EXPECTED_PARENT_CHANNELS_SHA256,
    }
    for path, digest in expected.items():
        if _digest(path.read_bytes()) != digest:
            _fail(str(path), "sealed Alpha v11 parent byte digest changed")
    return _load(alpha), _load(channels)


def _verify_document_table(
    root: Path,
    alpha_path: Path,
    alpha: dict[str, Any],
) -> dict[str, dict[str, Any]]:
    raw_documents = alpha.get("evidence_documents")
    if type(raw_documents) is not list or not raw_documents:
        _fail(f"{alpha_path}.evidence_documents", "must be a non-empty list")
    documented: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(raw_documents):
        location = f"{alpha_path}.evidence_documents[{index}]"
        if type(raw) is not dict:
            _fail(location, "must be an object")
        path = _repo_file(root, raw.get("path"), f"{location}.path")
        payload = path.read_bytes()
        if raw.get("sha256") != _digest(payload) or raw.get("bytes") != len(payload):
            _fail(location, "document byte binding does not match repository")
        relative = str(raw["path"])
        if relative in documented:
            _fail(location, "duplicates a document path")
        if type(raw.get("role")) is not str or not raw["role"]:
            _fail(f"{location}.role", "must be a non-empty string")
        documented[relative] = raw

    enrollment = alpha_v12_enrollment()
    required = {
        "peano-lab/py/peano_lab/library/alpha_enrollment_v12.py",
        "peano-lab/py/peano_lab/library/editions_v12.py",
        "artifacts/peano-library/alpha/catalog-v11.json",
        *enrollment.rfc_by_name.values(),
        *enrollment.source_by_name.values(),
        *enrollment.test_by_name.values(),
    }
    missing = sorted(required - set(documented))
    if missing:
        _fail(
            f"{alpha_path}.evidence_documents",
            f"missing v12 control/source/test/RFC/parent documents {missing!r}",
        )
    return documented


def _expected_receipt(receipt: object) -> dict[str, object]:
    result = asdict(receipt)
    result["dne_command_count"] = 0
    result["status"] = "kernel_checked_dependency_curried_body"
    return result


def validate_channels_v12(
    root: Path,
    alpha_path: Path,
    metrics_path: Path,
    graph_path: Path,
    channels_path: Path,
    *,
    replay_bodies: bool = True,
    replay_offsets: tuple[int, ...] | None = None,
    validate_parent: bool = True,
    regenerate_payloads: bool = False,
) -> dict[str, int]:
    """Validate the exact v11 prefix, v12 append, and artifact family."""

    root = root.resolve()
    parent, parent_channels = _verify_parent(
        root,
        validate_parent=validate_parent,
    )
    alpha = _load(alpha_path)
    metrics = _load(metrics_path)
    channels = _load(channels_path)
    try:
        graph = graph_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ChannelV12Error(f"{graph_path}: unreadable UTF-8 graph: {exc}") from exc

    if alpha.get("schema") != SCHEMA:
        _fail(str(alpha_path), "Alpha-v12 schema changed")
    if metrics.get("schema") != METRICS_SCHEMA:
        _fail(str(metrics_path), "Alpha-v12 metrics schema changed")
    if channels.get("schema") != CHANNEL_SCHEMA:
        _fail(str(channels_path), "Alpha-v12 channels schema changed")

    parent_rows = parent.get("theorems")
    rows = alpha.get("theorems")
    if type(parent_rows) is not list or len(parent_rows) != 1123:
        _fail("Alpha v11 parent", "must contain exactly 1123 rows")
    if type(rows) is not list or len(rows) != 1303:
        _fail(f"{alpha_path}.theorems", "must contain exactly 1303 rows")
    if rows[:1123] != parent_rows:
        _fail(
            f"{alpha_path}.theorems",
            "first 1123 rows differ from exact v11 parent",
        )
    if alpha.get("parent_alpha_v11") != builder._parent_binding():
        _fail(f"{alpha_path}.parent_alpha_v11", "complete sealed v11 binding changed")

    documented = _verify_document_table(root, alpha_path, alpha)
    enrollment = alpha_v12_enrollment()
    entries = ALPHA_ENTRIES[BERTRAND_V12_START_INDEX:]
    appended = rows[BERTRAND_V12_START_INDEX:]
    if len(appended) != BERTRAND_V12_EXPECTED_COUNT:
        _fail(f"{alpha_path}.theorems", "Bertrand-v12 append count changed")
    positions = {str(row["name"]): index for index, row in enumerate(parent_rows)}
    parent_document = documented["artifacts/peano-library/alpha/catalog-v11.json"]
    base = (
        builder.v11_builder.v10_builder.v9_builder.v8_builder.v7_builder
        .v6_builder.v5_builder.v4_builder.v3_builder.v2_builder.v1
    )
    for offset, (entry, row) in enumerate(zip(entries, appended, strict=True)):
        index = BERTRAND_V12_START_INDEX + offset
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
                _fail(f"{location}.dependencies", f"{dependency!r} is not earlier")

        source_path = enrollment.source_by_name[spec.name]
        test_path = enrollment.test_by_name[spec.name]
        rfc_path = enrollment.rfc_by_name[spec.name]
        exact = (
            row.get("statement"),
            tuple(dependencies),
            tuple(script),
            row.get("summary"),
            row.get("enrollment_origin"),
            row.get("provenance"),
        )
        if exact != (
            spec.statement,
            spec.dependencies,
            spec.script,
            spec.summary,
            "bertrand",
            ["bertrand"],
        ):
            _fail(location, "does not match frozen Bertrand-v12 runtime specification")

        statement_sha = _digest(spec.statement)
        dependencies_sha = _digest("\n".join(spec.dependencies) + "\n")
        logical_sha = base._logical_spec_sha256(spec)
        hash_expectations = {
            "statement_sha256": statement_sha,
            "dependencies_sha256": dependencies_sha,
            "script_sha256": _digest("\n".join(spec.script) + "\n"),
            "logical_spec_sha256": logical_sha,
            "summary_sha256": _digest(spec.summary),
        }
        for field, expected in hash_expectations.items():
            if row.get(field) != expected:
                _fail(f"{location}.{field}", "does not bind exact content")

        source_document = documented[source_path]
        test_document = documented[test_path]
        rfc_document = documented[rfc_path]
        if row.get("source") != {
            "kind": "candidate_module",
            "path": source_path,
            "sha256": source_document["sha256"],
        }:
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
                "path": rfc_path,
                "role": "reviewed_campaign_contract",
                "selector": "document",
            },
            {
                "document_sha256": parent_document["sha256"],
                "kind": "sealed_alpha_v11_parent",
                "path": "artifacts/peano-library/alpha/catalog-v11.json",
                "role": "exact_parent_catalog_bytes",
                "selector": "document",
            },
        ]
        if row.get("evidence_links") != expected_links:
            _fail(f"{location}.evidence_links", "evidence byte links changed")
        bundle = builder._bundle_payload(
            name=spec.name,
            origin="bertrand",
            statement_sha256=statement_sha,
            dependencies_sha256=dependencies_sha,
            logical_spec_sha256=logical_sha,
            source_sha256=str(source_document["sha256"]),
            test_sha256=str(test_document["sha256"]),
            rfc_sha256=str(rfc_document["sha256"]),
            parent_catalog_sha256=str(parent_document["sha256"]),
        )
        if row.get("bertrand_v12_evidence_bundle_sha256") != _digest(
            _compact(bundle)
        ):
            _fail(
                f"{location}.bertrand_v12_evidence_bundle_sha256",
                "does not cross-bind source/test/RFC/parent bytes",
            )
        if row.get("proof_tag") is not None:
            _fail(f"{location}.proof_tag", "body-only rows must be untagged")
        if (
            row.get("membership") != "alpha_only"
            or row.get("evidence_status") != "body_checked"
            or row.get("body_checked") is not True
            or row.get("checked_use") is not False
            or row.get("empty_context_closure") is not None
        ):
            _fail(location, "fabricated closure or checked-use upgrade")
        positions[spec.name] = index

    expected_counts = {
        "evidence_counts": {
            "alpha_closed": 138,
            "body_checked": 732,
            "pending_layered_closure": 1,
            "stable_closed": 432,
        },
        "membership_counts": {"alpha_only": 871, "stable": 432},
    }
    for field, expected in expected_counts.items():
        if alpha.get(field) != expected:
            _fail(f"{alpha_path}.{field}", "does not match theorem rows")
    if Counter(str(row["evidence_status"]) for row in rows) != Counter(
        expected_counts["evidence_counts"]
    ):
        _fail(str(alpha_path), "evidence counts changed")
    if Counter(str(row["membership"]) for row in rows) != Counter(
        expected_counts["membership_counts"]
    ):
        _fail(str(alpha_path), "membership counts changed")
    origins = Counter(str(row["enrollment_origin"]) for row in rows)
    expected_origins = Counter(parent["enrollment_origin_counts"])
    expected_origins["bertrand"] += BERTRAND_V12_EXPECTED_COUNT
    if origins != expected_origins or alpha.get("enrollment_origin_counts") != dict(
        sorted(expected_origins.items())
    ):
        _fail(str(alpha_path), "enrollment-origin counts changed")

    scalar_expectations = {
        "theorem_count": 1303,
        "stable_count": 432,
        "alpha_only_count": 871,
        "checked_use_count": 570,
        "edge_count": builder.EXPECTED_EDGE_COUNT,
        "layer_count": builder.EXPECTED_LAYER_COUNT,
        "edition_identity_sha256": ALPHA_V12_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": ALPHA_V12_ENROLLMENT_SHA256,
        "ordered_spec_root_sha256": base._ordered_root(
            ALPHA_ENTRIES, include_origin=False
        ),
        "membership_root_sha256": base._membership_root(rows),
        "evidence_root_sha256": base._evidence_root(rows),
    }
    for field, expected in scalar_expectations.items():
        if alpha.get(field) != expected:
            _fail(f"{alpha_path}.{field}", "does not match runtime/row seal")

    replayed_count = 0
    if replay_bodies and replay_offsets is None:
        core = {
            entry.spec.name: entry.spec
            for entry in ALPHA_ENTRIES[:BERTRAND_V12_START_INDEX]
        }
        receipts = replay_candidate_bodies(
            tuple(entry.spec for entry in entries),
            core=core,
        )
        for row, receipt in zip(appended, receipts, strict=True):
            if row.get("body_receipt") != _expected_receipt(receipt):
                _fail(
                    f"{alpha_path}.theorems[{row['enrollment_index']}].body_receipt",
                    "does not match independent kernel body replay",
                )
        replayed_count = BERTRAND_V12_EXPECTED_COUNT
    elif replay_bodies:
        if len(set(replay_offsets)) != len(replay_offsets) or any(
            offset < 0 or offset >= BERTRAND_V12_EXPECTED_COUNT
            for offset in replay_offsets
        ):
            _fail("replay_offsets", "must be distinct valid v12 append offsets")
        for offset in replay_offsets:
            core = {
                entry.spec.name: entry.spec
                for entry in ALPHA_ENTRIES[: BERTRAND_V12_START_INDEX + offset]
            }
            receipt = replay_candidate_bodies(
                (entries[offset].spec,),
                core=core,
            )[0]
            row = appended[offset]
            if row.get("body_receipt") != _expected_receipt(receipt):
                _fail(
                    f"{alpha_path}.theorems[{row['enrollment_index']}].body_receipt",
                    "does not match independent kernel body replay",
                )
        replayed_count = len(replay_offsets)

    if channels.get("default_channel") != "stable":
        _fail(f"{channels_path}.default_channel", "must remain Stable")
    if channels.get("policy") != parent_channels.get("policy"):
        _fail(f"{channels_path}.policy", "channel policy changed")
    if channels.get("channels", {}).get("stable") != parent_channels["channels"][
        "stable"
    ]:
        _fail(f"{channels_path}.channels.stable", "exact Stable pointers changed")

    artifact_paths = {
        "alpha": alpha_path,
        "metrics": metrics_path,
        "graph": graph_path,
        "channels": channels_path,
    }
    for name, path in artifact_paths.items():
        if _digest(path.read_bytes()) != EXPECTED_ARTIFACT_SHA256[name]:
            _fail(str(path), "artifact bytes are not byte-canonical")

    if regenerate_payloads:
        generated = builder.build_payloads()
        committed = (
            alpha_path.read_text(encoding="utf-8"),
            metrics_path.read_text(encoding="utf-8"),
            graph,
            channels_path.read_text(encoding="utf-8"),
        )
        if committed != generated:
            _fail("Alpha v12 artifact family", "is not byte-canonical")

    return {
        "alpha": 1303,
        "alpha_closed": 138,
        "bertrand_replayed": replayed_count,
        "body_checked": 732,
        "checked_use": 570,
        "stable": 432,
    }


def main() -> int:
    result = validate_channels_v12(
        ROOT,
        ARTIFACT_ROOT / "alpha/catalog-v12.json",
        ARTIFACT_ROOT / "alpha/metrics-v12.json",
        ARTIFACT_ROOT / "alpha/dependency-graph-v12.mmd",
        ARTIFACT_ROOT / "channels-v12.json",
        replay_bodies=True,
    )
    print(
        "verified Alpha v12: "
        f"stable={result['stable']}, alpha={result['alpha']}, "
        f"checked-use={result['checked_use']}, "
        f"Bertrand-replayed={result['bertrand_replayed']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
