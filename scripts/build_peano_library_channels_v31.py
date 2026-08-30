#!/usr/bin/env python3
"""Create a genuinely checked additive Alpha-v31 parent-plus-delta release."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import gc
import json
from pathlib import Path
import resource
import signal
import sys


ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import build_peano_library_channels as base
import build_peano_library_channels_v13 as graph_builder
import check_alpha_v31_completed_lower as proof_audit
import alpha_v31_historical_evidence as historical_evidence


SCHEMA = "peano-library-alpha-snapshot-v31"
METRICS_SCHEMA = "peano-library-alpha-metrics-v31"
CHANNEL_SCHEMA = "peano-library-channels-v31"
MAX_CATALOG_BYTES = 64 * 1024 * 1024
PARENT_ALPHA = ROOT / proof_audit.PARENT_PATH
PARENT_METRICS = ROOT / "artifacts/peano-library/alpha/metrics-v30.json"
PARENT_GRAPH = ROOT / "artifacts/peano-library/alpha/dependency-graph-v30.mmd"
PARENT_CHANNELS = ROOT / "artifacts/peano-library/channels-v30.json"
STABLE = ROOT / "artifacts/peano-library/catalog-v1.json"
DEFAULT_ALPHA = ROOT / "artifacts/peano-library/alpha/catalog-v31.json"
DEFAULT_DELTA = ROOT / "artifacts/peano-library/alpha/catalog-v31-delta.json"
DEFAULT_METRICS = ROOT / "artifacts/peano-library/alpha/metrics-v31.json"
DEFAULT_GRAPH = ROOT / "artifacts/peano-library/alpha/dependency-graph-v31.mmd"
DEFAULT_CHANNELS = ROOT / "artifacts/peano-library/channels-v31.json"
DEFAULT_RECEIPT = ROOT / "research/arithmetic-library/artifacts/alpha-v31-completed-lower-receipt-v1.json"
EXPECTED_PARENT_PINS = {
    "catalog": (PARENT_ALPHA, proof_audit.PARENT_SHA256),
    "metrics": (PARENT_METRICS, "f27488e5613c94e03f04f6b1d5f17ddfd70fad91eb011c5dbf3f6c3b4ee4c87b"),
    "dependency_graph": (PARENT_GRAPH, "1c1d2fe13486046ad2ddcfac4cc01807a725cf488c39e001ac8ea399fa4465a2"),
    "channels": (PARENT_CHANNELS, "8eb084cb0675587892f1e1861738c31e217862db7562c1b6b833857149635e74"),
}
STABLE_SHA256 = "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"
ADMISSION_RFC = "research/arithmetic-library/alpha-v31-completed-lower-rfc-v1.md"
CONTROL_DOCUMENTS = {
    **{path: "Exact source-bound fresh completed-lower proof and release control."
       for path in proof_audit.CONTROL_SOURCES[:4]},
    "peano-lab/py/peano_lab/library/alpha_enrollment_v31.py": "Exact additive ownership and immutable Alpha-v30 parent.",
    "peano-lab/py/peano_lab/library/editions_v31.py": "Fail-closed independently checked Alpha-v31 runtime.",
    "peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py": "Complete original-HA proof provider for nineteen frozen bundles.",
    "peano-lab/py/tests/test_library_editions_v31_admission.py": "Adversarial parent, Stable and exact Alpha admission audit.",
    "peano-lab/py/tests/test_campaign_completed_lower_closure.py": "Actual complete proof-provider and hostile-input audit.",
    "scripts/test_peano_catalog_shards.py": "Bounded parent-plus-delta catalogue transport audit.",
    "scripts/test_verify_peano_library_channels_v31.py": "Independent source, proof, catalogue and authority regression audit.",
    "scripts/test_alpha_v31_release_metadata.py": "Independent exact historical metadata, channel and resource-boundary mutation audit.",
    "scripts/alpha_v31_historical_evidence.py": "Exact five-version historical evidence archive resolver; no general mismatch fallback.",
    "scripts/test_alpha_v31_historical_evidence.py": "Adversarial exact-byte historical archive, provenance and path-safety audit.",
    "scripts/constructive_completed_lower_publication_v31.py": "Literal historical reader inputs and exact new Alpha admission mapping.",
    "scripts/build_constructive_completed_lower_explorer_v31.py": "Canonical QR-template exact and defined readers for nineteen admitted families.",
    "scripts/upgrade_constructive_historical_publication_v31.py": "Additive current presentation preserving every historical first admission and non-admitted alias.",
    "scripts/constructive_alpha_v31_publication_process.py": "Bounded live-capability publication transport without saved-receipt authority.",
    "scripts/extend_constructive_completed_lower_campaign_v31.py": "Combined campaign and conservative-definition DAG with exact G007/G014 closure and honest G009 boundary.",
    "peano-lab/py/tests/test_constructive_completed_lower_publication_v31.py": "Exact current/historical theorem and definition identity audit.",
    "peano-lab/py/tests/test_constructive_completed_lower_explorer_v31.py": "Canonical presentation, actual graph interaction and authority regressions.",
    "peano-lab/py/tests/test_constructive_historical_publication_v31.py": "Historical first-admission and current presentation regressions.",
    "peano-lab/py/tests/test_constructive_alpha_v31_publication_process.py": "Adversarial bounded publication process audit.",
    "peano-lab/py/tests/test_constructive_completed_lower_campaign_v31.py": "Exact campaign closure, open-boundary and definition-DAG regressions.",
    ADMISSION_RFC: "Reviewed additive mathematical, evidence and resource contract.",
}


def digest(value):
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def compact(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, separators=(",", ":"))


def pretty(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode()


def relative(path):
    return path.relative_to(ROOT).as_posix()


def read_bytes(path, maximum=MAX_CATALOG_BYTES):
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= maximum:
        raise ValueError(f"release input is not an ordinary bounded file: {relative(path)}")
    with path.open("rb") as stream:
        value = stream.read(maximum + 1)
    if not 0 < len(value) <= maximum:
        raise ValueError("release input exceeded its unchanged byte bound")
    return value


def strict_json(payload):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("duplicate release JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ValueError("non-finite release JSON number")

    value = json.loads(payload, object_pairs_hook=pairs, parse_constant=constant)
    if type(value) is not dict:
        raise ValueError("release JSON is not an object")
    return value


def _document(path, role, *, payload=None):
    contents = read_bytes(path) if payload is None else payload
    return {"bytes": len(contents), "path": relative(path), "role": role, "sha256": digest(contents)}


def _parent_binding():
    from peano_lab.library import editions_v30 as parent
    return {"artifacts": {label: {"path": relative(path), "sha256": pin}
                           for label, (path, pin) in EXPECTED_PARENT_PINS.items()},
            "edition_identity_sha256": parent.ALPHA_V30_IDENTITY_SHA256,
            "ordered_enrollment_root_sha256": parent.ALPHA_V30_ENROLLMENT_SHA256,
            "schema": "peano-library-alpha-snapshot-v30", "theorem_count": 3222}


def _load_parent():
    from peano_lab.library import editions_v30 as parent
    for path, expected in EXPECTED_PARENT_PINS.values():
        if digest(read_bytes(path)) != expected:
            raise ValueError(f"immutable Alpha-v30 release input changed: {relative(path)}")
    if digest(read_bytes(STABLE)) != STABLE_SHA256:
        raise ValueError("the immutable default Stable artifact changed")
    catalog = strict_json(read_bytes(PARENT_ALPHA))
    if (catalog.get("schema") != "peano-library-alpha-snapshot-v30"
            or type(catalog.get("theorem_count")) is not int or catalog["theorem_count"] != 3222
            or catalog.get("checked_use_count") != 3222 or catalog.get("stable_count") != 432
            or len(catalog.get("theorems", ())) != 3222
            or catalog.get("edition_identity_sha256") != parent.ALPHA_V30_IDENTITY_SHA256
            or catalog.get("ordered_enrollment_root_sha256") != parent.ALPHA_V30_ENROLLMENT_SHA256
            or len(catalog.get("evidence_documents", ())) != 740):
        raise ValueError("the exact immutable Alpha-v30 parent partition changed")
    names = set()
    for row, entry in zip(catalog["theorems"], parent.ALPHA_ENTRIES, strict=True):
        spec = entry.spec
        if (row["name"] != spec.name or row["statement"] != spec.statement
                or row["dependencies"] != list(spec.dependencies) or row["script"] != list(spec.script)
                or row["summary"] != spec.summary or row["checked_use"] is not True
                or row["body_checked"] is not True or not set(row["dependencies"]) <= names):
            raise ValueError("immutable catalogue and actual Alpha-v30 runtime disagree")
        names.add(spec.name)
    _verify_parent_documents(catalog)
    channels = strict_json(read_bytes(PARENT_CHANNELS))
    if channels["default_channel"] != "stable" or channels["channels"]["alpha"]["checked_use_count"] != 3222:
        raise ValueError("the unchanged parent release default changed")
    return catalog


def _verify_parent_documents(catalog):
    # Literal historical records remain unchanged. Five reviewed historical
    # versions have exact-byte additive archives; all other records must still
    # match their current path. Never reinterpret a current log as old evidence.
    if type(catalog.get("evidence_documents")) is not list or len(catalog["evidence_documents"]) != 740:
        raise ValueError("the exact immutable evidence inventory changed")
    seen = set()
    for document in catalog["evidence_documents"]:
        if type(document) is not dict or set(document) != {"path", "bytes", "sha256", "role"}:
            raise ValueError("malformed immutable evidence document fields")
        path = document["path"]
        if (type(path) is not str or Path(path).is_absolute() or ".." in Path(path).parts
                or path in seen or type(document["bytes"]) is not int):
            raise ValueError("malformed or duplicate immutable evidence document")
        seen.add(path)
        historical_evidence.verify_inherited_document(document, root=ROOT)
    if not {record["original_path"] for record in historical_evidence.ARCHIVES} <= seen:
        raise ValueError("a reviewed historical version is absent from its immutable parent")


def preflight_inputs():
    """Fail early on missing or changed metadata, without granting authority.

    This intentionally does not import the large parent runtime before the
    fresh proof workers. Exact runtime/specification comparison still occurs
    in _load_parent after the actual proof checks.
    """
    for path, expected in EXPECTED_PARENT_PINS.values():
        if digest(read_bytes(path)) != expected:
            raise ValueError(f"immutable Alpha-v30 release input changed: {relative(path)}")
    if digest(read_bytes(STABLE)) != STABLE_SHA256:
        raise ValueError("the immutable default Stable artifact changed")
    parent = strict_json(read_bytes(PARENT_ALPHA))
    _verify_parent_documents(parent)
    historical_evidence.archive_evidence_documents(root=ROOT)
    for path in CONTROL_DOCUMENTS:
        read_bytes(ROOT / path)
    for family in proof_audit.registry():
        read_bytes(ROOT / family.rfc)
        for pin in family.modules:
            read_bytes(ROOT / ("peano-lab/py/tests/test_" + Path(pin.path).name))
    del parent
    gc.collect()
    proof_audit.authoring_rss_bytes()


def _frontier_row(entry, index, item, family, documents):
    spec = entry.spec
    metrics = next(row for row in family["rows"] if row["name"] == spec.name)
    bundle = family["bundle"]
    source = next(pin.path for pin in item.modules if pin.path == entry.source_module)
    test = "peano-lab/py/tests/test_" + Path(source).name
    rfc = item.rfc
    body_receipt = {
        "command_count": len(spec.script), "dependency_count": len(spec.dependencies),
        "dne_command_count": 0, "name": spec.name,
        **{key: metrics[key] for key in ("proof_depth", "proof_edges", "proof_nodes", "proof_objects", "reused_objects")},
        "status": "kernel_checked_dependency_curried_body",
    }
    statement_hash = digest(spec.statement)
    closure = {
        "body_proof_depth": metrics["proof_depth"], "body_proof_nodes": metrics["proof_nodes"],
        "bundle_campaign": item.slug, "bundle_dependency_edge_count": bundle["dependency_edges_including_packaging"],
        "bundle_node_count": bundle["nodes_including_packaging_root"], "bundle_node_id": metrics["node_id"],
        "bundle_path": item.artifact, "bundle_root_id": bundle["packaging_root_id"],
        "certificate_representation": "peano-lab-bundle-v1", "certificate_sha256": item.artifact_sha256,
        "closure_kind": "dependency_closed_bundle_node", "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic", "node_statement_sha256": statement_hash, "status": "checked",
    }
    receipt_path = relative(DEFAULT_RECEIPT)
    row = {
        "body_checked": True, "body_receipt": body_receipt, "checked_use": True,
        "dependencies": list(spec.dependencies), "dependencies_sha256": digest("\n".join(spec.dependencies) + "\n"),
        "enrollment_index": index, "enrollment_origin": entry.enrollment_origin.value,
        "evidence_status": "alpha_closed", "frontier_campaign": item.slug,
        "logical_spec_sha256": base._logical_spec_sha256(spec), "membership": "alpha_only",
        "name": spec.name, "proof_tag": None, "provenance": [entry.enrollment_origin.value],
        "script": list(spec.script), "script_sha256": digest("\n".join(spec.script) + "\n"),
        "source": {"kind": "candidate_module", "path": source, "sha256": documents[source]["sha256"]},
        "statement": spec.statement, "statement_sha256": statement_hash,
        "summary": spec.summary, "summary_sha256": digest(spec.summary), "empty_context_closure": closure,
        "alpha_v31_frontier_enrollment": {
            "first_enrolled_version": "v31", "campaign": item.slug,
            "parent_catalog_sha256": proof_audit.PARENT_SHA256,
            "source_sha256": documents[source]["sha256"], "test_sha256": documents[test]["sha256"],
            "rfc_sha256": documents[rfc]["sha256"], "body_receipt_sha256": digest(compact(body_receipt)),
            "bundle_campaign": item.slug, "bundle_node_id": metrics["node_id"], "bundle_sha256": item.artifact_sha256,
        },
        "evidence_links": [
            {"path": path, "document_sha256": documents[path]["sha256"], "kind": kind,
             "role": role, "selector": selector}
            for path, kind, role, selector in (
                (source, "alpha_v31_frontier_dependency_curried_body", "dependency_curried_body", "document"),
                (test, "alpha_v31_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
                (rfc, "alpha_v31_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
                (item.artifact, "alpha_v31_complete_constructive_proof_bundle", "independently_kernel_checked_dependency_closed_proof", f"nodes[id={metrics['node_id']}]"),
                (receipt_path, "alpha_v31_live_original_kernel_and_lean_receipt", "fresh_release_proof_verification", f"families[slug={item.slug}]"),
                (proof_audit.PARENT_PATH, "sealed_alpha_v30_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
            )
        ],
    }
    return row


def _topology(rows, parent_metrics):
    from peano_lab.library import editions_v31 as edition
    depths, closures, kept, redundant = base._dependency_analysis(rows)
    if (len(kept) + len(redundant) != edition.EXPECTED_ALPHA_V31_EDGE_COUNT
            or max(depths.values(), default=-1) + 1 != edition.EXPECTED_ALPHA_V31_LAYER_COUNT):
        raise ValueError("the sealed complete theorem DAG changed")
    reduced = {row["name"]: [] for row in rows}
    for dependency, theorem in kept:
        reduced[theorem].append(dependency)
    reduced_closures = {}
    for row in rows:
        name = row["name"]
        values = set(reduced[name])
        for dependency in reduced[name]:
            values.update(reduced_closures[dependency])
        reduced_closures[name] = frozenset(values)
    if reduced_closures != closures:
        raise ValueError("the display-only dependency reduction changed reachability")
    redundant_rows = [{"dependency": a, "theorem": b} for a, b in redundant]
    kept_rows = [{"dependency": a, "theorem": b} for a, b in kept]
    origins = {row["name"]: row["enrollment_origin"] for row in rows}
    metadata = {
        "declared_edge_count": edition.EXPECTED_ALPHA_V31_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": edition.EXPECTED_ALPHA_V31_LAYER_COUNT,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(sorted(Counter(origins[b] for _, b in redundant).items())),
        "reachability_redundant_direct_dependency_sha256": digest(compact(redundant_rows)),
        "reachability_reduction_scope": parent_metrics["dependency_graph"]["reachability_reduction_scope"],
        "theorems_by_depth": {str(depth): count for depth, count in sorted(Counter(depths.values()).items())},
        "transitive_reduction_edge_count": len(kept), "transitive_reduction_edge_sha256": digest(compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True,
    }
    graph = graph_builder._alpha_graph(rows, kept, redundant).replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v31.py; do not edit.", 1,
    ).encode()
    return metadata, graph


def build_payloads(audit=None):
    """Consume only a live, unchanged proof invocation; no receipt-file shortcut."""
    if audit is None:
        preflight_inputs()
        audit = proof_audit.verify_in_fresh_windows()
    if type(audit) is not proof_audit.FreshProofAudit:
        raise ValueError("a saved proof report cannot authorize Alpha admission")
    audit.require_unchanged()
    from peano_lab.library import editions_v31 as edition
    from peano_catalog_shards import encode_catalog
    parent = _load_parent()
    parent_metrics = strict_json(read_bytes(PARENT_METRICS))
    parent_channels = strict_json(read_bytes(PARENT_CHANNELS))
    report = audit.report
    receipt_bytes = pretty(report)
    families = {row["slug"]: row for row in report["families"]}
    if tuple(families) != tuple(slug for slug, _ in proof_audit.EXPECTED_INVENTORY):
        raise ValueError("live proof audit lost an exact completed family")
    documents = {row["path"]: row for row in parent["evidence_documents"]}

    def add(path, role, payload=None):
        record = _document(ROOT / path, role, payload=payload)
        if path in documents:
            old = documents[path]
            if old["bytes"] != record["bytes"] or old["sha256"] != record["sha256"]:
                raise ValueError(f"attempt to replace immutable evidence: {path}")
            return  # Preserve the old role and every literal old field too.
        documents[path] = record

    for path, role in CONTROL_DOCUMENTS.items():
        add(path, role)
    for record in historical_evidence.archive_evidence_documents(root=ROOT):
        add(record["path"], record["role"])
    add(proof_audit.PARENT_PATH, "Exact immutable fully checked Alpha-v30 parent catalogue.")
    add(relative(DEFAULT_RECEIPT), "Fresh complete original-HA, same-byte independent Lean and ordinary-principal release audit.", receipt_bytes)
    ownership = {}
    for item in proof_audit.registry():
        add(item.artifact, "Complete actual constructive proof data; historical checkpoint bytes retained unchanged.")
        add(item.rfc, "Exact reviewed constructive mathematical contract for " + item.slug + ".")
        for pin in item.modules:
            add(pin.path, "Exact constructive proof factory first admitted to Alpha v31.")
            add("peano-lab/py/tests/test_" + Path(pin.path).name, "Independent exact statement, proof and hostile-input regression audit.")
        for name in families[item.slug]["owned_node_ids"]:
            if name in ownership:
                raise ValueError("one theorem was counted as newly owned twice")
            ownership[name] = item
    rows = list(parent["theorems"])
    for index, entry in enumerate(edition.ALPHA_ENTRIES[3222:], 3222):
        item = ownership[entry.spec.name]
        rows.append(_frontier_row(entry, index, item, families[item.slug], documents))
    if rows[:3222] != parent["theorems"] or len(rows) != 3796:
        raise ValueError("the exact immutable parent/additive theorem partition changed")
    evidence = Counter(row["evidence_status"] for row in rows)
    memberships = Counter(row["membership"] for row in rows)
    origins = Counter(row["enrollment_origin"] for row in rows)
    if (evidence != Counter(stable_closed=432, alpha_closed=3364)
            or memberships != Counter(stable=432, alpha_only=3364)
            or not all(row["checked_use"] is True and row["body_checked"] is True for row in rows)):
        raise ValueError("the new edition contains unproved or incorrectly admitted records")
    topology, graph_bytes = _topology(rows, parent_metrics)
    names_hash = digest("\n".join(edition.FRONTIER_NEW_NAMES))
    campaign_counts = dict(proof_audit.EXPECTED_INVENTORY)
    promotion = {
        "status": "kernel_checked_complete_dependency_closed_additive_edition",
        "parent_theorem_count": 3222, "frontier_new_count": 574,
        "checked_use_before": 3222, "checked_use_after": 3796,
        "campaign_counts": campaign_counts, "frontier_ordered_names_sha256": names_hash,
        "proof_bundle_count": 19, "proof_bundles": [families[item.slug]["bundle"] for item in proof_audit.registry()],
        "independent_lean_bundle_verified": True,
        "ordinary_principal_count": report["ordinary_principal_count"],
        "remaining_body_checked_count": 0, "receipt_path": relative(DEFAULT_RECEIPT),
        "receipt_sha256": digest(receipt_bytes), "completed_named_targets": ["G007", "G014"],
        "open_named_targets": ["G009", "G091"],
        "historical_evidence_archives": historical_evidence.archive_bindings(),
    }
    catalog = {**parent, "schema": SCHEMA, "theorem_count": 3796, "checked_use_count": 3796,
               "stable_count": 432, "alpha_only_count": 3364,
               "edge_count": edition.EXPECTED_ALPHA_V31_EDGE_COUNT,
               "layer_count": edition.EXPECTED_ALPHA_V31_LAYER_COUNT,
               "edition_identity_sha256": edition.ALPHA_V31_IDENTITY_SHA256,
               "ordered_enrollment_root_sha256": base._ordered_root(edition.ALPHA_ENTRIES, include_origin=True),
               "ordered_spec_root_sha256": base._ordered_root(edition.ALPHA_ENTRIES, include_origin=False),
               "membership_root_sha256": base._membership_root(rows), "evidence_root_sha256": base._evidence_root(rows),
               "enrollment_origin_counts": dict(sorted(origins.items())), "evidence_counts": dict(sorted(evidence.items())),
               "membership_counts": dict(sorted(memberships.items())),
               "canonical_order": [*parent["canonical_order"], *(f"Constructive Alpha-v31 {slug} ({count})" for slug, count in proof_audit.EXPECTED_INVENTORY)],
               "evidence_documents": [documents[path] for path in sorted(documents)],
               "frontier_v31_campaign_counts": campaign_counts, "frontier_v31_ordered_names_sha256": names_hash,
               "parent_alpha_v30": _parent_binding(), "alpha_v31_completed_lower_promotion": promotion,
               "theorems": rows}
    if catalog["ordered_enrollment_root_sha256"] != edition.ALPHA_V31_ENROLLMENT_SHA256:
        raise ValueError("the exact additive enrollment identity changed")
    manifest_bytes, delta_bytes = encode_catalog({key: value for key, value in catalog.items() if key != "theorems"}, rows[3222:])
    metrics = deepcopy(parent_metrics)
    metrics.update(schema=METRICS_SCHEMA, catalog_path=relative(DEFAULT_ALPHA), catalog_sha256=digest(manifest_bytes),
                   theorem_count=3796, checked_use_count=3796, evidence_counts=catalog["evidence_counts"],
                   edition_identity_sha256=catalog["edition_identity_sha256"],
                   ordered_enrollment_root_sha256=catalog["ordered_enrollment_root_sha256"],
                   ordered_spec_root_sha256=catalog["ordered_spec_root_sha256"],
                   dependency_graph=topology, dependency_graph_path=relative(DEFAULT_GRAPH), dependency_graph_sha256=digest(graph_bytes),
                   parent_alpha_v30=catalog["parent_alpha_v30"], alpha_v31_completed_lower_promotion=promotion,
                   frontier_v31_campaign_counts=campaign_counts, frontier_v31_ordered_names_sha256=names_hash)
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] += 574
    accounting.update(metric_bearing_theorem_count=3796, missing_empty_context_metric_count=0,
                      campaign_v31_bundle_accounting={"campaign_count": 19, "campaign_counts": campaign_counts,
                                                     "new_checked_theorem_count": 574, "proof_bundles": promotion["proof_bundles"],
                                                     "totals_policy": "Nineteen complete checked artifacts; inherited bodies and packaging roots are never counted as new theorems."})
    gates = metrics["promotion_gates"]
    gates["canonical_topology"].update(theorem_count=3796, declared_edge_count=catalog["edge_count"])
    gates["dependency_link_analysis"]["reachability_redundant_direct_dependency_count"] = topology["reachability_redundant_direct_dependency_count"]
    gates["source_integrity"]["source_bound_theorem_count"] = 3796
    gates["full_alpha_empty_context_compilation"].update(checked=3796, missing=0, required=3796, status="passed")
    gates["complete_constructive_alpha_v31_completed_lower"] = {**promotion, "status": "passed"}
    metrics_bytes = pretty(metrics)
    artifacts = {
        "catalog": {"path": relative(DEFAULT_ALPHA), "sha256": digest(manifest_bytes)},
        "catalog_delta": {"path": relative(DEFAULT_DELTA), "sha256": digest(delta_bytes)},
        "dependency_graph": {"path": relative(DEFAULT_GRAPH), "sha256": digest(graph_bytes)},
        "metrics": {"path": relative(DEFAULT_METRICS), "sha256": digest(metrics_bytes)},
    }
    alpha = {**parent_channels["channels"]["alpha"],
             "artifact_path": relative(DEFAULT_ALPHA), "artifact_sha256": digest(manifest_bytes), "artifacts": artifacts,
             "alpha_v31_frontier_new_count": 574, "theorem_count": 3796, "checked_use_count": 3796,
             "edition_identity_sha256": catalog["edition_identity_sha256"], "evidence_counts": catalog["evidence_counts"],
             "evidence_root_sha256": catalog["evidence_root_sha256"], "membership_root_sha256": catalog["membership_root_sha256"],
             "ordered_enrollment_root_sha256": catalog["ordered_enrollment_root_sha256"],
             "ordered_spec_root_sha256": catalog["ordered_spec_root_sha256"],
             "frontier_v31_campaign_counts": campaign_counts, "parent_alpha_v30_sha256": proof_audit.PARENT_SHA256}
    channels = {"schema": CHANNEL_SCHEMA, "channels": {"alpha": alpha, "stable": parent_channels["channels"]["stable"]},
                "default_channel": "stable", "policy": parent_channels["policy"],
                "parent_channels_v30": {"path": relative(PARENT_CHANNELS), "sha256": EXPECTED_PARENT_PINS["channels"][1]}}
    channels["channel_pointer_root_sha256"] = digest(compact(channels["channels"]))
    audit.require_unchanged()
    proof_audit.authoring_rss_bytes()
    return {
        DEFAULT_ALPHA: manifest_bytes, DEFAULT_DELTA: delta_bytes, DEFAULT_METRICS: metrics_bytes,
        DEFAULT_GRAPH: graph_bytes, DEFAULT_CHANNELS: pretty(channels), DEFAULT_RECEIPT: receipt_bytes,
    }, audit


def check_or_write(payloads, *, check):
    # Validate all targets before creating any; never partially overwrite an
    # existing release or silently refresh an immutable success receipt.
    proof_audit.authoring_rss_bytes()
    for path, expected in payloads.items():
        if check:
            if read_bytes(path) != expected:
                raise ValueError(f"stale release artifact: {relative(path)}")
        elif path.exists() or path.is_symlink():
            raise ValueError(f"refusing to overwrite existing release artifact: {relative(path)}")
    if not check:
        proof_audit.authoring_rss_bytes()
        for path, payload in payloads.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(payload)
    proof_audit.authoring_rss_bytes()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--with-publication", action="store_true", help="publish canonical maps from this same live proof invocation")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)
    jobs = 1 + len(proof_audit.registry()) + sum(len(item.principal_roots) for item in proof_audit.registry())
    # A scheduling envelope, not a larger proof window: three independent
    # publication jobs plus the controller's own bounded bookkeeping window.
    signal.alarm(jobs * proof_audit.PARENT_TIMEOUT_SECONDS + 4 * proof_audit.WALL_SECONDS)
    payloads, audit = build_payloads()
    check_or_write(payloads, check=args.check)
    if args.with_publication:
        from verify_peano_library_channels_v31 import context_from_live_audit
        from build_constructive_completed_lower_explorer_v31 import publish_from_live_context
        publish_from_live_context(context_from_live_audit(audit), check=args.check)
    proof_audit.authoring_rss_bytes()
    print(f"{'Verified' if args.check else 'Created'} Alpha v31: 3796 checked-use; 574 new; 19 complete HA/Lean bundles; Stable432 unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
