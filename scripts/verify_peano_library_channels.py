#!/usr/bin/env python3
"""Verify committed Alpha/Stable Peano-library channel artifacts.

This verifier is structural and replay-free.  It checks canonical ordering,
hashes, evidence-document bindings, selectors, dependency topology, and the
stable-prefix contract.  Proof replay remains the responsibility of the
evidence-producing gates named by the artifacts and, for stable promotion, a
separate cold WMI run.
"""

from __future__ import annotations

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import sys
from typing import Any, NoReturn


SCHEMA = "peano-library-alpha-snapshot-v1"
CHANNEL_SCHEMA = "peano-library-channels-v1"
METRICS_SCHEMA = "peano-library-alpha-metrics-v1"
EVIDENCE_STATUSES = {
    "stable_closed",
    "alpha_closed",
    "body_checked",
    "pending_layered_closure",
}
MEMBERSHIPS = {"stable", "alpha_only"}
ENROLLMENT_ORIGINS = {"stable", "qr", "ha", "k3b"}
HEX_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
EXPECTED_ENROLLMENT_ROOT = (
    "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
)
EXPECTED_STABLE_ARTIFACT_SHA256 = (
    "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
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
PROMOTION_MODEL = {
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
}


class ChannelError(ValueError):
    """A channel artifact violates the deterministic contract."""


def _fail(location: str, message: str) -> NoReturn:
    raise ChannelError(f"{location}: {message}")


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ChannelError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_pairs)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChannelError(f"{path}: cannot read strict UTF-8 JSON: {exc}") from exc
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
        _fail(location, "escapes the repository root")
    if not result.is_file():
        _fail(location, f"missing file {raw!r}")
    return result


def _ordered_root(rows: list[dict[str, Any]], *, include_origin: bool) -> str:
    material: list[str] = []
    for row in rows:
        fields = [
            row["name"],
            row["statement"],
            "\x1e".join(row["dependencies"]),
            "\x1e".join(row["script"]),
        ]
        if include_origin:
            fields.insert(0, row["enrollment_origin"])
        material.append("\x1f".join(fields))
    return _digest("\x1c".join(material))


def _membership_root(rows: list[dict[str, Any]]) -> str:
    return _digest(
        "\x1c".join(
            "\x1f".join(
                (
                    row["name"],
                    row["membership"],
                    row["enrollment_origin"],
                    "\x1e".join(row["provenance"]),
                )
            )
            for row in rows
        )
    )


def _evidence_root(rows: list[dict[str, Any]]) -> str:
    return _digest(
        "\x1c".join(
            "\x1f".join(
                (
                    row["name"],
                    row["evidence_status"],
                    "1" if row["checked_use"] else "0",
                    _compact(row["evidence_links"]),
                    _compact(row["empty_context_closure"]),
                )
            )
            for row in rows
        )
    )


def _logical_spec_sha256(row: dict[str, Any]) -> str:
    return _digest(
        _compact(
            {
                "dependencies": row["dependencies"],
                "name": row["name"],
                "script": row["script"],
                "statement": row["statement"],
            }
        )
    )


def _resolve_selector(
    document: dict[str, Any], selector: str, location: str
) -> dict[str, Any]:
    if type(selector) is not str:
        _fail(location, "must be a string")
    if selector == "document":
        return document
    list_match = re.fullmatch(r"(.+)\[name=([a-z][a-z0-9_]*)\]", selector)
    if list_match:
        current: object = document
        for part in list_match.group(1).split("."):
            if type(current) is not dict or part not in current:
                _fail(location, f"selector path component {part!r} is missing")
            current = current[part]
        if type(current) is not list:
            _fail(location, "selector does not address a list")
        matches = [
            item
            for item in current
            if type(item) is dict and item.get("name") == list_match.group(2)
        ]
        if len(matches) != 1:
            _fail(location, f"selector resolves to {len(matches)} rows")
        return matches[0]
    dict_match = re.fullmatch(r"results\.([a-z][a-z0-9_]*)", selector)
    if dict_match:
        results = document.get("results")
        if type(results) is not dict or dict_match.group(1) not in results:
            _fail(location, "result selector is missing")
        selected = results[dict_match.group(1)]
        if type(selected) is not dict:
            _fail(location, "result selector does not address an object")
        return selected
    _fail(location, f"unsupported evidence selector {selector!r}")


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


def _ha_closure(row: dict[str, Any]) -> dict[str, object]:
    receipt = row["receipt"]
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


def _dependency_analysis(
    rows: list[dict[str, Any]],
) -> tuple[
    dict[str, int],
    dict[str, frozenset[str]],
    list[tuple[str, str]],
    list[tuple[str, str]],
]:
    depths: dict[str, int] = {}
    closures: dict[str, frozenset[str]] = {}
    kept: list[tuple[str, str]] = []
    reachability_redundant: list[tuple[str, str]] = []
    for row in rows:
        name = row["name"]
        dependencies = tuple(row["dependencies"])
        depths[name] = (
            0
            if not dependencies
            else 1 + max(depths[dependency] for dependency in dependencies)
        )
        dependency_set = set(dependencies)
        for dependency in dependencies:
            alternatives = dependency_set.difference({dependency})
            if any(dependency in closures[alternative] for alternative in alternatives):
                reachability_redundant.append((dependency, name))
            else:
                kept.append((dependency, name))
        closure = set(dependencies)
        for dependency in dependencies:
            closure.update(closures[dependency])
        closures[name] = frozenset(closure)
    return depths, closures, kept, reachability_redundant


def _alpha_graph(
    rows: list[dict[str, Any]],
    kept_edges: list[tuple[str, str]],
    reachability_redundant: list[tuple[str, str]],
) -> str:
    lines = [
        "%% Generated by scripts/build_peano_library_channels.py; do not edit.",
        "%% Alpha review view: declared dependency edges are transitively reduced.",
        f"%% Declared edges: {len(kept_edges) + len(reachability_redundant)}; visible edges: {len(kept_edges)}; hidden reachability-redundant edges: {len(reachability_redundant)}.",
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
        name = row["name"]
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
    for dependency, theorem in kept_edges:
        lines.append(f"  {dependency} --> {theorem}")
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
            lines.append(
                f"  class {','.join(names[offset:offset + 40])} {class_name};"
            )
    for class_name, names in evidence_classes.items():
        for offset in range(0, len(names), 40):
            lines.append(
                f"  class {','.join(names[offset:offset + 40])} {class_name};"
            )
    return "\n".join(lines) + "\n"


def _edition_identity(rows: list[dict[str, Any]]) -> str:
    entries = [
        {
            "dependencies": row["dependencies"],
            "enrollment_origin": row["enrollment_origin"],
            "evidence": row["evidence_status"],
            "membership": row["membership"],
            "name": row["name"],
            "provenance": row["provenance"],
            "script": row["script"],
            "source_module": row["source"]["path"],
            "statement": row["statement"],
            "summary": row["summary"],
        }
        for row in rows
    ]
    return _digest(_compact({"edition": "alpha", "entries": entries}))


def validate_channels(
    repository_root: Path,
    alpha_path: Path,
    alpha_metrics_path: Path,
    alpha_graph_path: Path,
    channels_path: Path,
    stable_path: Path,
    stable_metrics_path: Path,
    stable_graph_path: Path,
) -> dict[str, int]:
    repository_root = repository_root.resolve()
    alpha = _load(alpha_path)
    alpha_metrics = _load(alpha_metrics_path)
    channels = _load(channels_path)
    stable = _load(stable_path)
    try:
        alpha_graph = alpha_graph_path.read_text(encoding="utf-8")
        stable_graph = stable_graph_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ChannelError(f"cannot read dependency graph as UTF-8: {exc}") from exc
    stable_metrics = _load(stable_metrics_path)

    if alpha.get("schema") != SCHEMA or alpha.get("channel") != "alpha":
        _fail(str(alpha_path), f"expected {SCHEMA!r} Alpha artifact")
    if channels.get("schema") != CHANNEL_SCHEMA:
        _fail(str(channels_path), f"expected {CHANNEL_SCHEMA!r}")
    if channels.get("default_channel") != "stable":
        _fail(f"{channels_path}.default_channel", "must remain stable")
    if stable.get("schema") != "peano-library-snapshot-v3":
        _fail(str(stable_path), "stable snapshot schema changed")
    if alpha_metrics.get("schema") != METRICS_SCHEMA:
        _fail(str(alpha_metrics_path), f"expected {METRICS_SCHEMA!r}")
    if stable_metrics.get("schema") != "peano-library-metrics-v3":
        _fail(str(stable_metrics_path), "stable metrics schema changed")
    if _digest(stable_path.read_bytes()) != EXPECTED_STABLE_ARTIFACT_SHA256:
        _fail(str(stable_path), "stable catalog bytes changed")

    rows = alpha.get("theorems")
    if type(rows) is not list or len(rows) != 885:
        _fail(f"{alpha_path}.theorems", "must contain exactly 885 rows")
    names: set[str] = set()
    positions: dict[str, int] = {}
    evidence_counts: Counter[str] = Counter()
    membership_counts: Counter[str] = Counter()
    origin_counts: Counter[str] = Counter()
    checked_count = 0
    document_cache: dict[str, dict[str, Any]] = {}
    source_digest_cache: dict[str, str] = {}

    evidence_documents = alpha.get("evidence_documents")
    if type(evidence_documents) is not list or not evidence_documents:
        _fail(f"{alpha_path}.evidence_documents", "must be a non-empty list")
    documented: dict[str, dict[str, Any]] = {}
    for index, descriptor in enumerate(evidence_documents):
        location = f"{alpha_path}.evidence_documents[{index}]"
        if type(descriptor) is not dict:
            _fail(location, "must be an object")
        path = _repo_file(repository_root, descriptor.get("path"), f"{location}.path")
        expected = _sha(descriptor.get("sha256"), f"{location}.sha256")
        payload = path.read_bytes()
        if _digest(payload) != expected:
            _fail(f"{location}.sha256", "does not match evidence document bytes")
        if descriptor.get("bytes") != len(payload):
            _fail(f"{location}.bytes", "does not match evidence document bytes")
        if descriptor["path"] in documented:
            _fail(location, "duplicates an evidence document path")
        documented[descriptor["path"]] = descriptor

    for index, raw in enumerate(rows):
        location = f"{alpha_path}.theorems[{index}]"
        if type(raw) is not dict:
            _fail(location, "must be an object")
        row: dict[str, Any] = raw
        name = row.get("name")
        if type(name) is not str or re.fullmatch(r"[a-z][a-z0-9_]*", name) is None:
            _fail(f"{location}.name", "must be a lowercase theorem identifier")
        if name in names:
            _fail(f"{location}.name", f"duplicate theorem {name!r}")
        if row.get("enrollment_index") != index:
            _fail(f"{location}.enrollment_index", "must equal list position")
        for text_field in ("statement", "summary"):
            if type(row.get(text_field)) is not str:
                _fail(f"{location}.{text_field}", "must be a string")
        for list_field in ("dependencies", "script", "provenance", "evidence_links"):
            if type(row.get(list_field)) is not list:
                _fail(f"{location}.{list_field}", "must be a list")
        dependencies = row["dependencies"]
        script = row["script"]
        if any(type(item) is not str for item in dependencies):
            _fail(f"{location}.dependencies", "must contain only theorem names")
        if any(type(item) is not str for item in script):
            _fail(f"{location}.script", "must contain only tactic strings")
        if len(dependencies) != len(set(dependencies)):
            _fail(f"{location}.dependencies", "must not contain duplicates")
        for dependency in dependencies:
            if dependency not in positions:
                _fail(
                    f"{location}.dependencies",
                    f"dependency {dependency!r} is missing or not earlier",
                )
        names.add(name)
        positions[name] = index

        membership = row.get("membership")
        enrollment_origin = row.get("enrollment_origin")
        evidence = row.get("evidence_status")
        if membership not in MEMBERSHIPS:
            _fail(f"{location}.membership", f"unknown membership {membership!r}")
        if enrollment_origin not in ENROLLMENT_ORIGINS:
            _fail(
                f"{location}.enrollment_origin",
                f"unknown enrollment origin {enrollment_origin!r}",
            )
        if evidence not in EVIDENCE_STATUSES:
            _fail(f"{location}.evidence_status", f"unknown evidence {evidence!r}")
        membership_counts[membership] += 1
        origin_counts[enrollment_origin] += 1
        evidence_counts[evidence] += 1
        checked_use = row.get("checked_use")
        if type(checked_use) is not bool:
            _fail(f"{location}.checked_use", "must be Boolean")
        if checked_use != (evidence in {"stable_closed", "alpha_closed"}):
            _fail(f"{location}.checked_use", "does not agree with closure evidence")
        checked_count += checked_use
        if row.get("body_checked") is not True:
            _fail(f"{location}.body_checked", "must record the checked body")
        closure = row.get("empty_context_closure")
        if checked_use and (type(closure) is not dict or closure.get("status") != "checked"):
            _fail(f"{location}.empty_context_closure", "checked-use row needs checked closure")
        if evidence == "body_checked" and closure is not None:
            _fail(f"{location}.empty_context_closure", "body-only row must use null closure")
        if evidence == "pending_layered_closure" and closure != {
            "status": "pending_layered_closure"
        }:
            _fail(f"{location}.empty_context_closure", "pending row must remain explicit")

        provenance = row["provenance"]
        if not provenance or any(item not in ENROLLMENT_ORIGINS for item in provenance):
            _fail(f"{location}.provenance", "contains an unknown origin")
        if provenance[0] != enrollment_origin:
            _fail(f"{location}.provenance", "primary origin must equal enrollment_origin")
        if len(provenance) != len(set(provenance)):
            _fail(f"{location}.provenance", "must not contain duplicates")

        source = row.get("source")
        if type(source) is not dict:
            _fail(f"{location}.source", "must be a non-null source object")
        source_path = _repo_file(
            repository_root, source.get("path"), f"{location}.source.path"
        )
        source_sha = _sha(source.get("sha256"), f"{location}.source.sha256")
        source_key = source_path.as_posix()
        actual_source_sha = source_digest_cache.get(source_key)
        if actual_source_sha is None:
            actual_source_sha = _digest(source_path.read_bytes())
            source_digest_cache[source_key] = actual_source_sha
        if actual_source_sha != source_sha:
            _fail(f"{location}.source.sha256", "does not match source bytes")
        expected_source_kinds = {
            "stable": {"stable_registry"},
            "qr": {"declaration", "generated_factory"},
            "ha": {"candidate_module"},
            "k3b": {"candidate_module"},
        }[enrollment_origin]
        if source.get("kind") not in expected_source_kinds:
            _fail(
                f"{location}.source.kind",
                f"must be one of {sorted(expected_source_kinds)!r} for this enrollment origin",
            )
        if enrollment_origin == "stable" and source.get("path") != (
            "peano-lab/py/peano_lab/library/theorems.py"
        ):
            _fail(f"{location}.source.path", "stable row must bind the registry source")

        for field, expected in (
            ("statement_sha256", _digest(row["statement"])),
            ("script_sha256", _digest("\n".join(row["script"]) + "\n")),
            ("dependencies_sha256", _digest("\n".join(dependencies) + "\n")),
            ("summary_sha256", _digest(row["summary"])),
            ("logical_spec_sha256", _logical_spec_sha256(row)),
        ):
            if row.get(field) != expected:
                _fail(f"{location}.{field}", "digest mismatch")

        links = row["evidence_links"]
        if not links:
            _fail(f"{location}.evidence_links", "must not be empty")
        selected_by_kind: dict[str, dict[str, Any] | None] = {}
        for link_index, link in enumerate(links):
            link_location = f"{location}.evidence_links[{link_index}]"
            if type(link) is not dict:
                _fail(link_location, "must be an object")
            path = link.get("path")
            if type(path) is not str:
                _fail(f"{link_location}.path", "must be a string")
            descriptor = documented.get(path)
            if descriptor is None:
                _fail(f"{link_location}.path", "is not a declared evidence document")
            if link.get("document_sha256") != descriptor["sha256"]:
                _fail(f"{link_location}.document_sha256", "does not match document table")
            kind = link.get("kind")
            if type(kind) is not str or not kind:
                _fail(f"{link_location}.kind", "must be a non-empty string")
            if kind in selected_by_kind:
                _fail(f"{link_location}.kind", "duplicates an evidence-link kind")
            if path not in document_cache and str(path).endswith(".json"):
                document_cache[path] = _load(repository_root / path)
            if str(path).endswith(".json"):
                selected_by_kind[kind] = _resolve_selector(
                    document_cache[path],
                    link.get("selector"),
                    f"{link_location}.selector",
                )
            elif link.get("selector") != "document":
                _fail(f"{link_location}.selector", "non-JSON document uses document selector")
            else:
                selected_by_kind[kind] = None

        if evidence == "stable_closed":
            if set(selected_by_kind) != {"stable_closed_snapshot"}:
                _fail(f"{location}.evidence_links", "stable row needs its snapshot row only")
            selected = selected_by_kind["stable_closed_snapshot"]
            if type(selected) is not dict:
                _fail(f"{location}.evidence_links", "stable selector did not resolve")
            for field in ("name", "statement", "dependencies", "script", "summary"):
                if selected.get(field) != row[field]:
                    _fail(f"{location}.{field}", "does not match stable evidence row")
            if closure != _stable_closure(selected):
                _fail(
                    f"{location}.empty_context_closure",
                    "does not match stable closure metrics",
                )
        elif evidence == "alpha_closed":
            kinds = set(selected_by_kind)
            if kinds in (
                {"ha_campaign_closure"},
                {"ha_campaign_closure", "qr_spec_inventory"},
            ):
                selected = selected_by_kind["ha_campaign_closure"]
                if type(selected) is not dict:
                    _fail(f"{location}.evidence_links", "HA selector did not resolve")
                if (
                    selected.get("name") != name
                    or selected.get("statement_sha256") != row["statement_sha256"]
                    or selected.get("status") != "closed_checked_candidate"
                ):
                    _fail(f"{location}.evidence_links", "HA evidence does not bind this spec")
                if enrollment_origin == "ha" and selected.get("source_module") != source.get(
                    "path"
                ):
                    _fail(f"{location}.source.path", "does not match HA evidence")
                if closure != _ha_closure(selected):
                    _fail(
                        f"{location}.empty_context_closure",
                        "does not match HA closure receipt",
                    )
                if "qr_spec_inventory" in kinds:
                    if provenance != ["qr", "ha"]:
                        _fail(
                            f"{location}.provenance",
                            "QR inventory on a closed row is reserved for the QR/HA overlap",
                        )
                    qr_selected = selected_by_kind["qr_spec_inventory"]
                    if type(qr_selected) is not dict:
                        _fail(f"{location}.evidence_links", "QR selector did not resolve")
                    for field in ("name", "statement", "summary"):
                        if qr_selected.get(field) != row[field]:
                            _fail(
                                f"{location}.{field}",
                                "does not match QR overlap inventory",
                            )
                    qr_dependencies = qr_selected.get("dependencies")
                    if (
                        type(qr_dependencies) is not list
                        or [
                            dependency.get("name")
                            if type(dependency) is dict
                            else None
                            for dependency in qr_dependencies
                        ]
                        != dependencies
                    ):
                        _fail(
                            f"{location}.dependencies",
                            "does not match QR overlap inventory",
                        )
                    qr_lines = qr_selected.get("lines")
                    if (
                        type(qr_lines) is not list
                        or [
                            line.get("text") if type(line) is dict else None
                            for line in qr_lines
                        ]
                        != script
                    ):
                        _fail(f"{location}.script", "does not match QR overlap inventory")
                    qr_source = qr_selected.get("source")
                    if (
                        type(qr_source) is not dict
                        or qr_source.get("path") != source.get("path")
                        or qr_source.get("sha256") != source.get("sha256")
                    ):
                        _fail(f"{location}.source", "does not match QR overlap inventory")
                elif provenance == ["qr", "ha"]:
                    _fail(
                        f"{location}.evidence_links",
                        "QR/HA overlap must bind its historical QR inventory",
                    )
            elif kinds == {"k3b_wmi_closure"}:
                selected = selected_by_kind["k3b_wmi_closure"]
                if type(selected) is not dict:
                    _fail(f"{location}.evidence_links", "K3B selector did not resolve")
                if (
                    selected.get("statement_sha256") != row["statement_sha256"]
                    or selected.get("direct_dependencies") != dependencies
                ):
                    _fail(f"{location}.evidence_links", "K3B evidence does not bind this spec")
                if closure != _k3b_closure(selected):
                    _fail(
                        f"{location}.empty_context_closure",
                        "does not match K3B closure receipt",
                    )
            else:
                _fail(
                    f"{location}.evidence_links",
                    "alpha-closed row needs exactly one HA or K3B closure receipt",
                )
        else:
            if set(selected_by_kind) != {"qr_body_inventory", "qr_full_audit_status"}:
                _fail(
                    f"{location}.evidence_links",
                    "QR body row needs inventory and promotion-blocker links",
                )
            selected = selected_by_kind["qr_body_inventory"]
            if type(selected) is not dict:
                _fail(f"{location}.evidence_links", "QR selector did not resolve")
            for field in ("name", "statement", "summary"):
                if selected.get(field) != row[field]:
                    _fail(f"{location}.{field}", "does not match QR body inventory")
            selected_dependencies = selected.get("dependencies")
            if (
                type(selected_dependencies) is not list
                or [
                    dependency.get("name") if type(dependency) is dict else None
                    for dependency in selected_dependencies
                ]
                != dependencies
            ):
                _fail(f"{location}.dependencies", "does not match QR body inventory")
            selected_lines = selected.get("lines")
            if (
                type(selected_lines) is not list
                or [
                    line.get("text") if type(line) is dict else None
                    for line in selected_lines
                ]
                != script
            ):
                _fail(f"{location}.script", "does not match QR body inventory")
            expected_qr_status = (
                "pending_layered_closure"
                if evidence == "pending_layered_closure"
                else "candidate_body_checked"
            )
            if selected.get("status") != expected_qr_status:
                _fail(f"{location}.evidence_status", "does not match QR body inventory")
            qr_source = selected.get("source")
            if (
                type(qr_source) is not dict
                or qr_source.get("path") != source.get("path")
                or qr_source.get("sha256") != source.get("sha256")
            ):
                _fail(f"{location}.source", "does not match QR body inventory")

    expected_evidence = Counter(
        {
            "stable_closed": 432,
            "alpha_closed": 138,
            "body_checked": 314,
            "pending_layered_closure": 1,
        }
    )
    expected_membership = Counter({"stable": 432, "alpha_only": 453})
    expected_origins = Counter({"stable": 432, "qr": 316, "ha": 120, "k3b": 17})
    if evidence_counts != expected_evidence:
        _fail(f"{alpha_path}.evidence_counts", f"observed {dict(evidence_counts)!r}")
    if membership_counts != expected_membership:
        _fail(f"{alpha_path}.membership_counts", f"observed {dict(membership_counts)!r}")
    if origin_counts != expected_origins:
        _fail(
            f"{alpha_path}.enrollment_origin_counts",
            f"observed {dict(origin_counts)!r}",
        )
    if alpha.get("evidence_counts") != dict(sorted(expected_evidence.items())):
        _fail(f"{alpha_path}.evidence_counts", "summary mismatch")
    if alpha.get("membership_counts") != dict(sorted(expected_membership.items())):
        _fail(f"{alpha_path}.membership_counts", "summary mismatch")
    if alpha.get("enrollment_origin_counts") != dict(sorted(expected_origins.items())):
        _fail(f"{alpha_path}.enrollment_origin_counts", "summary mismatch")
    if checked_count != 570 or alpha.get("checked_use_count") != checked_count:
        _fail(f"{alpha_path}.checked_use_count", "must be exactly 570")
    if alpha.get("theorem_count") != 885 or alpha.get("stable_count") != 432:
        _fail(str(alpha_path), "channel counts drifted")
    if alpha.get("ordered_enrollment_root_scheme") != ORDERED_ENROLLMENT_ROOT_SCHEME:
        _fail(
            f"{alpha_path}.ordered_enrollment_root_scheme",
            "canonical separator/field scheme changed",
        )
    if alpha.get("ordered_enrollment_root_scheme_sha256") != _digest(
        _compact(ORDERED_ENROLLMENT_ROOT_SCHEME)
    ):
        _fail(f"{alpha_path}.ordered_enrollment_root_scheme_sha256", "digest mismatch")
    if alpha.get("promotion_model") != PROMOTION_MODEL:
        _fail(
            f"{alpha_path}.promotion_model",
            "must preserve immutable enrollment and Stable-subset semantics",
        )

    for key, actual in (
        ("ordered_enrollment_root_sha256", _ordered_root(rows, include_origin=True)),
        ("ordered_spec_root_sha256", _ordered_root(rows, include_origin=False)),
        ("membership_root_sha256", _membership_root(rows)),
        ("evidence_root_sha256", _evidence_root(rows)),
    ):
        if alpha.get(key) != actual:
            _fail(f"{alpha_path}.{key}", "root digest mismatch")
    if alpha.get("ordered_enrollment_root_sha256") != EXPECTED_ENROLLMENT_ROOT:
        _fail(
            f"{alpha_path}.ordered_enrollment_root_sha256",
            "canonical 885-row enrollment identity changed",
        )
    if alpha.get("edition_identity_sha256") != _edition_identity(rows):
        _fail(f"{alpha_path}.edition_identity_sha256", "status-bearing identity mismatch")

    stable_rows = stable.get("theorems")
    if type(stable_rows) is not list or len(stable_rows) != 432:
        _fail(f"{stable_path}.theorems", "must contain 432 stable rows")
    alpha_stable_rows = [row for row in rows if row["membership"] == "stable"]
    alpha_stable_by_name = {row["name"]: row for row in alpha_stable_rows}
    if len(alpha_stable_by_name) != len(stable_rows):
        _fail(
            str(alpha_path),
            "current Stable catalog must be an exact specification subset of Alpha",
        )
    for index, stable_row in enumerate(stable_rows):
        alpha_row = alpha_stable_by_name.get(stable_row["name"])
        if alpha_row is None:
            _fail(
                f"{stable_path}.theorems[{index}]",
                "is absent from Stable membership in Alpha",
            )
        for field in ("name", "statement", "dependencies", "script", "summary"):
            if alpha_row[field] != stable_row[field]:
                _fail(
                    f"{alpha_path}.theorems[name={stable_row['name']}].{field}",
                    "does not match the Stable subset row",
                )
    expected_stable_metrics = {
        "certificate_representation": stable["certificate_representation"],
        "live_use_limits": {
            "proof_depth": 256,
            "proof_nodes": 500000,
            "proof_objects": 100000,
        },
        "maximum_cut_nodes": max(row["cut_nodes"] for row in stable_rows),
        "maximum_distinct_proof_objects": max(
            row["distinct_proof_objects"] for row in stable_rows
        ),
        "maximum_proof_depth": max(row["proof_depth"] for row in stable_rows),
        "maximum_proof_nodes": max(row["proof_nodes"] for row in stable_rows),
        "ordered_root_sha256": stable["ordered_root_sha256"],
        "schema": "peano-library-metrics-v3",
        "theorem_count": len(stable_rows),
        "theorems_by_layer": dict(
            Counter(row["layer"] for row in stable_rows)
        ),
        "theorems_with_cut_nodes": sum(row["cut_nodes"] > 0 for row in stable_rows),
        "total_cut_nodes": sum(row["cut_nodes"] for row in stable_rows),
        "total_distinct_proof_objects": sum(
            row["distinct_proof_objects"] for row in stable_rows
        ),
        "total_proof_nodes": sum(row["proof_nodes"] for row in stable_rows),
    }
    if stable_metrics != expected_stable_metrics:
        _fail(str(stable_metrics_path), "does not match the sealed Stable catalog")
    stable_graph_lines = [
        "%% Generated by scripts/build_peano_library_snapshot.py; do not edit.",
        "flowchart TD",
    ]
    for row in stable_rows:
        stable_graph_lines.append(f"  {row['name']}[{row['name']}]")
    for row in stable_rows:
        for dependency in row["dependencies"]:
            stable_graph_lines.append(f"  {dependency} --> {row['name']}")
    if stable_graph != "\n".join(stable_graph_lines) + "\n":
        _fail(str(stable_graph_path), "does not match the sealed Stable catalog")

    overlap = [row for row in rows if row["provenance"] == ["qr", "ha"]]
    if len(overlap) != 1 or overlap[0]["name"] != "mod_eq_add_cancel_left":
        _fail(str(alpha_path), "QR/HA overlap identity drifted")
    if rows[-1]["name"] != "cell_list_extensional":
        _fail(str(alpha_path), "canonical final K3B row drifted")

    depths, closures, kept_edges, reachability_redundant = _dependency_analysis(rows)
    declared_edge_count = len(kept_edges) + len(reachability_redundant)
    layer_count = max(depths.values(), default=-1) + 1
    if alpha.get("edge_count") != declared_edge_count or declared_edge_count != 2641:
        _fail(f"{alpha_path}.edge_count", "must be the exact declared DAG edge count")
    if alpha.get("layer_count") != layer_count or layer_count != 45:
        _fail(f"{alpha_path}.layer_count", "must be the exact dependency depth count")
    reduced_dependencies: dict[str, list[str]] = {row["name"]: [] for row in rows}
    for dependency, theorem in kept_edges:
        reduced_dependencies[theorem].append(dependency)
    reduced_closures: dict[str, frozenset[str]] = {}
    for row in rows:
        name = row["name"]
        closure = set(reduced_dependencies[name])
        for dependency in reduced_dependencies[name]:
            closure.update(reduced_closures[dependency])
        reduced_closures[name] = frozenset(closure)
    if reduced_closures != closures:
        _fail(str(alpha_graph_path), "transitive reduction changed reachability")
    expected_graph = _alpha_graph(rows, kept_edges, reachability_redundant)
    if alpha_graph != expected_graph:
        _fail(str(alpha_graph_path), "does not match the canonical reduced Alpha graph")

    checked_metric_rows = [
        row["empty_context_closure"] for row in rows if row["checked_use"]
    ]
    if any(type(closure) is not dict for closure in checked_metric_rows):
        _fail(str(alpha_metrics_path), "checked closure metrics are missing")
    metric_fields = (
        "cut_nodes",
        "proof_depth",
        "proof_edges",
        "proof_nodes",
        "proof_objects",
        "reused_objects",
    )
    for index, closure in enumerate(checked_metric_rows):
        assert isinstance(closure, dict)
        for field in metric_fields:
            value = closure.get(field)
            if type(value) is not int or value < 0:
                _fail(
                    f"{alpha_metrics_path}.checked_closure_metrics",
                    f"closure {index} has invalid {field}",
                )
    checked_metric_dicts: list[dict[str, Any]] = [
        closure for closure in checked_metric_rows if isinstance(closure, dict)
    ]
    expected_checked_metrics = {
        "certificate_digest_kinds": dict(
            sorted(
                Counter(
                    str(closure["digest_kind"])
                    for closure in checked_metric_dicts
                ).items()
            )
        ),
        "maximum_cut_nodes": max(
            int(closure["cut_nodes"]) for closure in checked_metric_dicts
        ),
        "maximum_proof_depth": max(
            int(closure["proof_depth"]) for closure in checked_metric_dicts
        ),
        "maximum_proof_edges": max(
            int(closure["proof_edges"]) for closure in checked_metric_dicts
        ),
        "maximum_proof_nodes": max(
            int(closure["proof_nodes"]) for closure in checked_metric_dicts
        ),
        "maximum_proof_objects": max(
            int(closure["proof_objects"]) for closure in checked_metric_dicts
        ),
        "metric_bearing_theorem_count": len(checked_metric_dicts),
        "missing_empty_context_metric_count": len(rows) - len(checked_metric_dicts),
        "total_cut_nodes": sum(
            int(closure["cut_nodes"]) for closure in checked_metric_dicts
        ),
        "total_proof_edges": sum(
            int(closure["proof_edges"]) for closure in checked_metric_dicts
        ),
        "total_proof_nodes": sum(
            int(closure["proof_nodes"]) for closure in checked_metric_dicts
        ),
        "total_proof_objects": sum(
            int(closure["proof_objects"]) for closure in checked_metric_dicts
        ),
        "total_reused_objects": sum(
            int(closure["reused_objects"]) for closure in checked_metric_dicts
        ),
    }
    if alpha_metrics.get("checked_closure_metrics") != expected_checked_metrics:
        _fail(
            f"{alpha_metrics_path}.checked_closure_metrics",
            "does not match the 570 exact closure receipts",
        )
    if alpha_metrics.get("promotion_model") != PROMOTION_MODEL:
        _fail(
            f"{alpha_metrics_path}.promotion_model",
            "does not match the catalog promotion model",
        )
    origin_by_name = {row["name"]: row["enrollment_origin"] for row in rows}
    redundant_by_origin = Counter(
        origin_by_name[theorem] for _, theorem in reachability_redundant
    )
    redundant_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in reachability_redundant
    ]
    kept_rows = [
        {"dependency": dependency, "theorem": theorem}
        for dependency, theorem in kept_edges
    ]
    depth_counts = Counter(depths.values())
    expected_dependency_metrics = {
        "declared_edge_count": declared_edge_count,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": layer_count,
        "maximum_direct_dependency_count": max(
            len(row["dependencies"]) for row in rows
        ),
        "maximum_transitive_dependency_count": max(
            map(len, closures.values()), default=0
        ),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(
            reachability_redundant
        ),
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
    }
    if alpha_metrics.get("dependency_graph") != expected_dependency_metrics:
        _fail(
            f"{alpha_metrics_path}.dependency_graph",
            "does not match the canonical Alpha topology analysis",
        )
    expected_alpha_path = alpha_path.resolve().relative_to(repository_root).as_posix()
    expected_graph_path = alpha_graph_path.resolve().relative_to(repository_root).as_posix()
    for field, expected in (
        ("catalog_path", expected_alpha_path),
        ("catalog_sha256", _digest(alpha_path.read_bytes())),
        ("channel", "alpha"),
        ("checked_use_count", checked_count),
        ("dependency_graph_path", expected_graph_path),
        ("dependency_graph_sha256", _digest(alpha_graph_path.read_bytes())),
        ("edition_identity_sha256", alpha["edition_identity_sha256"]),
        ("evidence_counts", alpha["evidence_counts"]),
        ("ordered_enrollment_root_sha256", alpha["ordered_enrollment_root_sha256"]),
        ("ordered_spec_root_sha256", alpha["ordered_spec_root_sha256"]),
        ("theorem_count", len(rows)),
    ):
        if alpha_metrics.get(field) != expected:
            _fail(f"{alpha_metrics_path}.{field}", "catalog/graph binding mismatch")
    promotion = alpha_metrics.get("promotion_gates")
    if type(promotion) is not dict:
        _fail(f"{alpha_metrics_path}.promotion_gates", "must be an object")
    expected_gate_values = {
        "canonical_topology": {
            "status": "passed",
            "theorem_count": 885,
            "declared_edge_count": 2641,
        },
        "dependency_link_analysis": {
            "status": "review_required",
            "reachability_redundant_direct_dependency_count": len(
                reachability_redundant
            ),
        },
        "full_alpha_empty_context_compilation": {
            "status": "blocked",
            "checked": 570,
            "required": 885,
            "missing": 315,
        },
        "source_integrity": {
            "status": "passed",
            "source_bound_theorem_count": 885,
        },
    }
    for gate, required in expected_gate_values.items():
        actual = promotion.get(gate)
        if type(actual) is not dict or any(
            actual.get(field) != value for field, value in required.items()
        ):
            _fail(f"{alpha_metrics_path}.promotion_gates.{gate}", "gate status drifted")

    channel_table = channels.get("channels")
    if type(channel_table) is not dict or set(channel_table) != {"stable", "alpha"}:
        _fail(f"{channels_path}.channels", "must define stable and alpha exactly")
    artifact_families = {
        "stable": {
            "catalog": stable_path,
            "metrics": stable_metrics_path,
            "dependency_graph": stable_graph_path,
        },
        "alpha": {
            "catalog": alpha_path,
            "metrics": alpha_metrics_path,
            "dependency_graph": alpha_graph_path,
        },
    }
    for name, family in artifact_families.items():
        location = f"{channels_path}.channels.{name}"
        channel = channel_table[name]
        if type(channel) is not dict:
            _fail(location, "must be an object")
        artifact_path = family["catalog"]
        expected_path = artifact_path.resolve().relative_to(repository_root).as_posix()
        if channel.get("artifact_path") != expected_path:
            _fail(f"{location}.artifact_path", "does not name the selected artifact")
        if channel.get("artifact_sha256") != _digest(artifact_path.read_bytes()):
            _fail(f"{location}.artifact_sha256", "does not match artifact bytes")
        pointers = channel.get("artifacts")
        if type(pointers) is not dict or set(pointers) != set(family):
            _fail(
                f"{location}.artifacts",
                "must define catalog, metrics, and dependency_graph exactly",
            )
        for artifact_name, selected_path in family.items():
            pointer_location = f"{location}.artifacts.{artifact_name}"
            pointer = pointers[artifact_name]
            if type(pointer) is not dict or set(pointer) != {"path", "sha256"}:
                _fail(pointer_location, "must be an exact path/SHA object")
            expected_selected_path = (
                selected_path.resolve().relative_to(repository_root).as_posix()
            )
            if pointer.get("path") != expected_selected_path:
                _fail(f"{pointer_location}.path", "does not name the selected artifact")
            if pointer.get("sha256") != _digest(selected_path.read_bytes()):
                _fail(f"{pointer_location}.sha256", "does not match artifact bytes")
    if channel_table["stable"].get("legacy_ordered_root_sha256") != stable.get(
        "ordered_root_sha256"
    ):
        _fail(f"{channels_path}.channels.stable", "legacy stable root mismatch")
    for field in (
        "theorem_count",
        "checked_use_count",
        "edition_identity_sha256",
        "evidence_counts",
        "ordered_enrollment_root_sha256",
        "ordered_spec_root_sha256",
        "membership_root_sha256",
        "evidence_root_sha256",
    ):
        if channel_table["alpha"].get(field) != alpha.get(field):
            _fail(f"{channels_path}.channels.alpha.{field}", "does not match alpha catalog")
    expected_pointer_root = _digest(_compact(channel_table))
    if channels.get("channel_pointer_root_sha256") != expected_pointer_root:
        _fail(f"{channels_path}.channel_pointer_root_sha256", "digest mismatch")

    return {
        "alpha": len(rows),
        "alpha_closed": evidence_counts["alpha_closed"],
        "body_checked": evidence_counts["body_checked"],
        "checked_use": checked_count,
        "stable": len(stable_rows),
    }


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository-root", type=Path, default=root)
    parser.add_argument(
        "--alpha-catalog",
        type=Path,
        default=root / "artifacts" / "peano-library" / "alpha" / "catalog-v1.json",
    )
    parser.add_argument(
        "--alpha-metrics",
        type=Path,
        default=root / "artifacts" / "peano-library" / "alpha" / "metrics.json",
    )
    parser.add_argument(
        "--alpha-graph",
        type=Path,
        default=root
        / "artifacts"
        / "peano-library"
        / "alpha"
        / "dependency-graph.mmd",
    )
    parser.add_argument(
        "--channels",
        type=Path,
        default=root / "artifacts" / "peano-library" / "channels.json",
    )
    parser.add_argument(
        "--stable-catalog",
        type=Path,
        default=root / "artifacts" / "peano-library" / "catalog-v1.json",
    )
    parser.add_argument(
        "--stable-metrics",
        type=Path,
        default=root / "artifacts" / "peano-library" / "metrics.json",
    )
    parser.add_argument(
        "--stable-graph",
        type=Path,
        default=root / "artifacts" / "peano-library" / "dependency-graph.mmd",
    )
    args = parser.parse_args(argv)
    try:
        counts = validate_channels(
            args.repository_root,
            args.alpha_catalog,
            args.alpha_metrics,
            args.alpha_graph,
            args.channels,
            args.stable_catalog,
            args.stable_metrics,
            args.stable_graph,
        )
    except ChannelError as exc:
        print(f"Peano library channel validation failed: {exc}", file=sys.stderr)
        return 1
    print(
        "validated Peano library channels: "
        f"stable={counts['stable']}, alpha={counts['alpha']}, "
        f"checked-use={counts['checked_use']}, "
        f"alpha-closed={counts['alpha_closed']}, "
        f"body-only={counts['body_checked']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
