#!/usr/bin/env python3
"""Independently audit exact Alpha-v31 admission and its live proof evidence."""

from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
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
import build_peano_library_channels_v31 as builder
import check_alpha_v31_completed_lower as proof_audit


class ReleaseError(ValueError):
    """Actual proof, source, topology or release authority is inconsistent."""


_LIVE_RELEASE = object()
PRESENTATION_INPUT_SOURCES = (
    "scripts/build_constructive_bottom_layer_explorer.py",
    "scripts/build_constructive_lower_tier_explorer.py",
    "scripts/build_constructive_lower_continuation_explorer.py",
    "scripts/build_constructive_dirichlet_explorer.py",
    "scripts/build_constructive_dirichlet_inverse_explorer.py",
    "scripts/constructive_proof_explorer_template.py",
    "scripts/constructive_checked_explorer_renderer.py",
    "scripts/constructive_frontier_exact_explorer.py",
    "scripts/constructive_dirichlet_inverse_definitions.py",
    "scripts/constructive_dirichlet_inverse_definition_graph.py",
    "scripts/constructive_dirichlet_inverse_defined_adapter.py",
)


def _same(left, right):
    return builder.compact(left) == builder.compact(right)


def _content_digest(value):
    """Hash logical JSON without allocating another complete large catalogue."""
    result = sha256()
    for piece in json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                                  separators=(",", ":")).iterencode(value):
        result.update(piece.encode())
    return result.hexdigest()


def _require(condition, message):
    if not condition:
        raise ReleaseError(message)


def _documents(catalog, parent, audit):
    records = catalog.get("evidence_documents")
    _require(type(records) is list, "missing exact release evidence inventory")
    documents = {}
    for record in records:
        _require(type(record) is dict and set(record) == {"path", "bytes", "sha256", "role"},
                 "malformed evidence document")
        path = record["path"]
        _require(type(path) is str and path not in documents and not Path(path).is_absolute()
                 and ".." not in Path(path).parts and "\\" not in path,
                 "duplicate or unsafe evidence path")
        _require(type(record["bytes"]) is int and record["bytes"] > 0
                 and type(record["sha256"]) is str and len(record["sha256"]) == 64
                 and type(record["role"]) is str and bool(record["role"]), "invalid evidence identity")
        documents[path] = record
    for old in parent["evidence_documents"]:
        _require(_same(documents.get(old["path"]), old), "historical evidence or first-admission provenance changed")
    roles = {row["path"]: row["role"] for row in parent["evidence_documents"]}
    for path, role in builder.CONTROL_DOCUMENTS.items():
        roles.setdefault(path, role)
    roles.setdefault(proof_audit.PARENT_PATH, "Exact immutable fully checked Alpha-v30 parent catalogue.")
    roles.setdefault(builder.relative(builder.DEFAULT_RECEIPT),
                     "Fresh complete original-HA, same-byte independent Lean and ordinary-principal release audit.")
    required = {*builder.CONTROL_DOCUMENTS, proof_audit.PARENT_PATH, builder.relative(builder.DEFAULT_RECEIPT)}
    for record in builder.historical_evidence.archive_evidence_documents(root=ROOT):
        required.add(record["path"])
        roles[record["path"]] = record["role"]
    for family in proof_audit.registry():
        required.update((family.artifact, family.rfc))
        roles.setdefault(family.artifact, "Complete actual constructive proof data; historical checkpoint bytes retained unchanged.")
        roles.setdefault(family.rfc, "Exact reviewed constructive mathematical contract for " + family.slug + ".")
        for pin in family.modules:
            required.update((pin.path, "peano-lab/py/tests/test_" + Path(pin.path).name))
            roles.setdefault(pin.path, "Exact constructive proof factory first admitted to Alpha v31.")
            roles.setdefault("peano-lab/py/tests/test_" + Path(pin.path).name,
                             "Independent exact statement, proof and hostile-input regression audit.")
    _require(set(documents) == required | {row["path"] for row in parent["evidence_documents"]},
             "missing or unreviewed release evidence documents")
    for path in required:
        record = documents[path]
        _require(record["role"] == roles[path], "an exact release evidence role changed")
        payload = builder.read_bytes(ROOT / path)
        _require(len(payload) == record["bytes"] and builder.digest(payload) == record["sha256"],
                 f"actual release source/evidence bytes changed: {path}")
    _require(builder.read_bytes(builder.DEFAULT_RECEIPT) == builder.pretty(audit.report),
             "the saved release receipt differs from this invocation's real proof results")
    return documents


def _row(row, entry, index, family, item, documents):
    spec = entry.spec
    required = {
        "body_checked", "body_receipt", "checked_use", "dependencies", "dependencies_sha256",
        "empty_context_closure", "enrollment_index", "enrollment_origin", "evidence_links", "evidence_status",
        "frontier_campaign", "logical_spec_sha256", "membership", "name", "proof_tag", "provenance", "script",
        "script_sha256", "source", "statement", "statement_sha256", "summary", "summary_sha256",
        "alpha_v31_frontier_enrollment",
    }
    _require(type(row) is dict and set(row) == required, "missing or unreviewed new theorem fields")
    scalar = {
        "name": spec.name, "statement": spec.statement, "summary": spec.summary,
        "dependencies": list(spec.dependencies), "script": list(spec.script),
        "statement_sha256": builder.digest(spec.statement), "summary_sha256": builder.digest(spec.summary),
        "dependencies_sha256": builder.digest("\n".join(spec.dependencies) + "\n"),
        "script_sha256": builder.digest("\n".join(spec.script) + "\n"),
        "logical_spec_sha256": base._logical_spec_sha256(spec), "enrollment_index": index,
        "enrollment_origin": "ha", "provenance": ["ha"], "membership": "alpha_only",
        "body_checked": True, "checked_use": True, "evidence_status": "alpha_closed",
        "frontier_campaign": item.slug, "proof_tag": None,
    }
    _require(_same({key: row[key] for key in scalar}, scalar),
             f"exact specification or admission changed for {spec.name}")
    source = entry.source_module
    test = "peano-lab/py/tests/test_" + Path(source).name
    _require(source in {pin.path for pin in item.modules}, "the new theorem has a foreign proof factory")
    _require(_same(row["source"], {"kind": "candidate_module", "path": source, "sha256": documents[source]["sha256"]}),
             "the actual theorem source binding changed")
    observed = next(value for value in family["rows"] if value["name"] == spec.name)
    body = {"name": spec.name, "command_count": len(spec.script), "dependency_count": len(spec.dependencies),
            "dne_command_count": 0, "status": "kernel_checked_dependency_curried_body",
            **{key: observed[key] for key in ("proof_depth", "proof_edges", "proof_nodes", "proof_objects", "reused_objects")}}
    _require(_same(row["body_receipt"], body), "the body receipt differs from the actual checked proof")
    bundle = family["bundle"]
    closure = {
        "body_proof_depth": observed["proof_depth"], "body_proof_nodes": observed["proof_nodes"],
        "bundle_campaign": item.slug, "bundle_dependency_edge_count": bundle["dependency_edges_including_packaging"],
        "bundle_node_count": bundle["nodes_including_packaging_root"], "bundle_node_id": observed["node_id"],
        "bundle_path": item.artifact, "bundle_root_id": bundle["packaging_root_id"],
        "certificate_representation": "peano-lab-bundle-v1", "certificate_sha256": item.artifact_sha256,
        "closure_kind": "dependency_closed_bundle_node", "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic", "node_statement_sha256": builder.digest(spec.statement), "status": "checked",
    }
    _require(_same(row["empty_context_closure"], closure), "the complete closure is not the actually checked exact bundle node")
    transition = {
        "first_enrolled_version": "v31", "campaign": item.slug,
        "parent_catalog_sha256": proof_audit.PARENT_SHA256,
        "source_sha256": documents[source]["sha256"], "test_sha256": documents[test]["sha256"],
        "rfc_sha256": documents[item.rfc]["sha256"], "body_receipt_sha256": builder.digest(builder.compact(body)),
        "bundle_campaign": item.slug, "bundle_node_id": observed["node_id"], "bundle_sha256": item.artifact_sha256,
    }
    _require(_same(row["alpha_v31_frontier_enrollment"], transition), "first admission or original proof provenance changed")
    receipt = builder.relative(builder.DEFAULT_RECEIPT)
    links = [
        {"path": path, "document_sha256": documents[path]["sha256"], "kind": kind, "role": role, "selector": selector}
        for path, kind, role, selector in (
            (source, "alpha_v31_frontier_dependency_curried_body", "dependency_curried_body", "document"),
            (test, "alpha_v31_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
            (item.rfc, "alpha_v31_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
            (item.artifact, "alpha_v31_complete_constructive_proof_bundle", "independently_kernel_checked_dependency_closed_proof", f"nodes[id={observed['node_id']}]"),
            (receipt, "alpha_v31_live_original_kernel_and_lean_receipt", "fresh_release_proof_verification", f"families[slug={item.slug}]"),
            (proof_audit.PARENT_PATH, "sealed_alpha_v30_parent", "exact_immutable_parent_catalog_bytes", "catalog"),
        )
    ]
    _require(_same(row["evidence_links"], links), "actual theorem evidence paths, roles or selectors changed")


def _verify_rows(catalog, parent, audit, documents):
    from peano_lab.library import editions_v31 as edition
    rows = catalog.get("theorems")
    _require(type(rows) is list and len(rows) == 3796, "wrong complete checked theorem inventory")
    _require(all(_same(new, old) for new, old in zip(rows[:3222], parent["theorems"], strict=True)),
             "one immutable historical theorem record changed")
    families = {row["slug"]: row for row in audit.report["families"]}
    _require(tuple(families) == tuple(name for name, _ in proof_audit.EXPECTED_INVENTORY), "incomplete live family inventory")
    ownership = {}
    for item in proof_audit.registry():
        family = families[item.slug]
        proof_audit._validate_family_report({**family, "principal_roots": []}, item)
        principals = family["principal_roots"]
        _require(type(principals) is list and tuple(row["name"] for row in principals) == item.principal_roots,
                 "missing, duplicate or invented ordinary principal certificates")
        for principal in principals:
            proof_audit._validate_report({"slug": item.slug, **principal}, kind="root", item=item,
                                        name=principal["name"], family=family)
        for name in family["owned_node_ids"]:
            _require(name not in ownership, "a proof was counted twice as newly admitted")
            ownership[name] = item
    _require(set(ownership) == set(edition.FRONTIER_NEW_NAMES), "wrong exact admitted frontier")
    available = set()
    for index, (row, entry) in enumerate(zip(rows, edition.ALPHA_ENTRIES, strict=True)):
        _require(row["name"] == entry.spec.name and row["name"] not in available
                 and set(row["dependencies"]) <= available, "changed ordered theorem DAG")
        available.add(row["name"])
        if index >= 3222:
            item = ownership[row["name"]]
            _row(row, entry, index, families[item.slug], item, documents)
    _require(Counter(row["evidence_status"] for row in rows) == Counter(stable_closed=432, alpha_closed=3364),
             "wrong Alpha/Stable evidence partition")
    _require(Counter(row["membership"] for row in rows) == Counter(stable=432, alpha_only=3364),
             "Alpha admission changed Stable membership")
    _require(all(row["checked_use"] is True and row["body_checked"] is True for row in rows), "an unchecked row was admitted")
    return rows, families


def _verify_metadata(catalog, metrics, channels, parent, families, audit, manifest_hash):
    from peano_lab.library import editions_v31 as edition
    expected_counts = {"theorem_count": 3796, "checked_use_count": 3796, "stable_count": 432,
                       "alpha_only_count": 3364, "edge_count": edition.EXPECTED_ALPHA_V31_EDGE_COUNT,
                       "layer_count": edition.EXPECTED_ALPHA_V31_LAYER_COUNT}
    _require(catalog["schema"] == builder.SCHEMA
             and _same({key: catalog.get(key) for key in expected_counts}, expected_counts), "wrong current complete-release scope")
    expected_roots = {
        "edition_identity_sha256": edition.ALPHA_V31_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": base._ordered_root(edition.ALPHA_ENTRIES, include_origin=True),
        "ordered_spec_root_sha256": base._ordered_root(edition.ALPHA_ENTRIES, include_origin=False),
        "membership_root_sha256": base._membership_root(catalog["theorems"]),
        "evidence_root_sha256": base._evidence_root(catalog["theorems"]),
    }
    _require(_same({key: catalog.get(key) for key in expected_roots}, expected_roots), "changed exact current-release identities")
    for field, expected in (
        ("evidence_counts", {"alpha_closed": 3364, "stable_closed": 432}),
        ("membership_counts", {"alpha_only": 3364, "stable": 432}),
        ("frontier_v31_campaign_counts", dict(proof_audit.EXPECTED_INVENTORY)),
        ("frontier_v31_ordered_names_sha256", builder.digest("\n".join(edition.FRONTIER_NEW_NAMES))),
        ("parent_alpha_v30", builder._parent_binding()),
    ):
        _require(_same(catalog.get(field), expected), f"changed exact {field}")
    origins = Counter(parent["enrollment_origin_counts"])
    origins["ha"] += 574
    _require(_same(catalog.get("enrollment_origin_counts"), dict(sorted(origins.items()))), "historical enrollment origins changed")
    expected_order = [*parent["canonical_order"], *(f"Constructive Alpha-v31 {slug} ({count})" for slug, count in proof_audit.EXPECTED_INVENTORY)]
    _require(_same(catalog.get("canonical_order"), expected_order), "canonical authoring order changed")
    promotion = {
        "status": "kernel_checked_complete_dependency_closed_additive_edition",
        "parent_theorem_count": 3222, "frontier_new_count": 574,
        "checked_use_before": 3222, "checked_use_after": 3796,
        "campaign_counts": dict(proof_audit.EXPECTED_INVENTORY),
        "frontier_ordered_names_sha256": builder.digest("\n".join(edition.FRONTIER_NEW_NAMES)),
        "proof_bundle_count": 19, "proof_bundles": [families[item.slug]["bundle"] for item in proof_audit.registry()],
        "independent_lean_bundle_verified": True, "ordinary_principal_count": audit.report["ordinary_principal_count"],
        "remaining_body_checked_count": 0, "receipt_path": builder.relative(builder.DEFAULT_RECEIPT),
        "receipt_sha256": builder.digest(builder.pretty(audit.report)),
        "completed_named_targets": ["G007", "G014"], "open_named_targets": ["G009", "G091"],
        "historical_evidence_archives": builder.historical_evidence.archive_bindings(),
    }
    _require(_same(catalog.get("alpha_v31_completed_lower_promotion"), promotion),
             "actual proof evidence or still-open ambitious boundaries changed")
    mutable = {*expected_counts, *expected_roots, "schema", "theorems", "enrollment_origin_counts",
               "evidence_counts", "membership_counts", "canonical_order", "evidence_documents"}
    additions = {"frontier_v31_campaign_counts", "frontier_v31_ordered_names_sha256", "parent_alpha_v30", "alpha_v31_completed_lower_promotion"}
    _require(set(catalog) == set(parent) | additions, "unreviewed current catalogue fields")
    for key in set(parent) - mutable:
        _require(_same(catalog[key], parent[key]), f"historical admission metadata changed: {key}")
    parent_metrics = builder.strict_json(builder.read_bytes(builder.PARENT_METRICS))
    topology, expected_graph = builder._topology(catalog["theorems"], parent_metrics)
    graph = builder.read_bytes(builder.DEFAULT_GRAPH)
    _require(graph == expected_graph, "the generated dependency DAG or its reduction changed")
    _require(metrics.get("schema") == builder.METRICS_SCHEMA
             and _same(metrics.get("dependency_graph"), topology)
             and metrics.get("catalog_path") == builder.relative(builder.DEFAULT_ALPHA)
             and metrics.get("catalog_sha256") == manifest_hash
             and metrics.get("dependency_graph_sha256") == builder.digest(graph)
             and metrics.get("dependency_graph_path") == builder.relative(builder.DEFAULT_GRAPH)
             and _same(metrics.get("alpha_v31_completed_lower_promotion"), promotion), "inconsistent independently derived release metrics")
    for key in ("theorem_count", "checked_use_count", "evidence_counts", "edition_identity_sha256",
                "ordered_enrollment_root_sha256", "ordered_spec_root_sha256", "frontier_v31_campaign_counts",
                "frontier_v31_ordered_names_sha256", "parent_alpha_v30"):
        _require(_same(metrics.get(key), catalog[key]), f"wrong release metrics field: {key}")
    gates = metrics.get("promotion_gates", {})
    _require(_same(gates.get("complete_constructive_alpha_v31_completed_lower"), {**promotion, "status": "passed"}),
             "the complete original-HA/Lean release gate is missing")
    full = gates.get("full_alpha_empty_context_compilation", {})
    _require(_same({key: full.get(key) for key in ("status", "checked", "required", "missing")},
                   {"status": "passed", "checked": 3796, "required": 3796, "missing": 0}), "incomplete checked-use coverage")
    accounting = metrics.get("checked_closure_metrics", {})
    _require(type(accounting.get("metric_bearing_theorem_count")) is int
             and accounting["metric_bearing_theorem_count"] == 3796
             and type(accounting.get("missing_empty_context_metric_count")) is int
             and accounting["missing_empty_context_metric_count"] == 0,
             "the catalogue omits actual closure metrics")
    expected_digest_kinds = dict(parent_metrics["checked_closure_metrics"]["certificate_digest_kinds"])
    expected_digest_kinds["self-contained-proof-bundle-sha256"] += 574
    _require(_same(accounting.get("certificate_digest_kinds"), expected_digest_kinds), "incorrect complete certificate accounting")
    expected_accounting = deepcopy(parent_metrics["checked_closure_metrics"])
    expected_accounting.update(
        certificate_digest_kinds=expected_digest_kinds,
        metric_bearing_theorem_count=3796, missing_empty_context_metric_count=0,
        campaign_v31_bundle_accounting={
            "campaign_count": 19, "campaign_counts": dict(proof_audit.EXPECTED_INVENTORY),
            "new_checked_theorem_count": 574, "proof_bundles": promotion["proof_bundles"],
            "totals_policy": "Nineteen complete checked artifacts; inherited bodies and packaging roots are never counted as new theorems.",
        },
    )
    _require(_same(accounting, expected_accounting), "new or historical proof accounting was changed")
    expected_gates = deepcopy(parent_metrics["promotion_gates"])
    expected_gates["canonical_topology"].update(theorem_count=3796, declared_edge_count=catalog["edge_count"])
    expected_gates["dependency_link_analysis"]["reachability_redundant_direct_dependency_count"] = topology["reachability_redundant_direct_dependency_count"]
    expected_gates["source_integrity"]["source_bound_theorem_count"] = 3796
    expected_gates["full_alpha_empty_context_compilation"].update(checked=3796, missing=0, required=3796, status="passed")
    expected_gates["complete_constructive_alpha_v31_completed_lower"] = {**promotion, "status": "passed"}
    _require(_same(gates, expected_gates), "new or historical promotion gates were changed")
    metrics_changes = {
        "schema", "catalog_path", "catalog_sha256", "theorem_count", "checked_use_count", "evidence_counts",
        "edition_identity_sha256", "ordered_enrollment_root_sha256", "ordered_spec_root_sha256",
        "dependency_graph", "dependency_graph_path", "dependency_graph_sha256", "checked_closure_metrics", "promotion_gates",
    }
    metrics_additions = {"parent_alpha_v30", "alpha_v31_completed_lower_promotion",
                         "frontier_v31_campaign_counts", "frontier_v31_ordered_names_sha256"}
    _require(set(metrics) == set(parent_metrics) | metrics_additions, "unknown or missing metrics fields")
    for key in set(parent_metrics) - metrics_changes:
        _require(_same(metrics[key], parent_metrics[key]), f"historical metrics metadata changed: {key}")
    parent_channels = builder.strict_json(builder.read_bytes(builder.PARENT_CHANNELS))
    _require(set(channels) == {"schema", "channels", "default_channel", "policy", "parent_channels_v30", "channel_pointer_root_sha256"}
             and type(channels.get("channels")) is dict and set(channels["channels"]) == {"alpha", "stable"},
             "unknown channel, missing pointer or unreviewed release fields")
    _require(channels.get("schema") == builder.CHANNEL_SCHEMA and channels.get("default_channel") == "stable"
             and _same(channels.get("channels", {}).get("stable"), parent_channels["channels"]["stable"])
             and _same(channels.get("policy"), parent_channels["policy"]), "Stable pointer, policy or default changed")
    alpha = channels["channels"].get("alpha", {})
    parent_alpha = parent_channels["channels"]["alpha"]
    alpha_changes = {"artifact_path", "artifact_sha256", "artifacts", "theorem_count", "checked_use_count",
                     "edition_identity_sha256", "evidence_counts", "evidence_root_sha256", "membership_root_sha256",
                     "ordered_enrollment_root_sha256", "ordered_spec_root_sha256"}
    alpha_additions = {"alpha_v31_frontier_new_count", "frontier_v31_campaign_counts", "parent_alpha_v30_sha256"}
    _require(set(alpha) == set(parent_alpha) | alpha_additions, "unknown or missing Alpha channel fields")
    for key in set(parent_alpha) - alpha_changes:
        _require(_same(alpha[key], parent_alpha[key]), f"historical Alpha channel metadata changed: {key}")
    _require(alpha["parent_alpha_v30_sha256"] == proof_audit.PARENT_SHA256
             and _same(channels["parent_channels_v30"], {"path": builder.relative(builder.PARENT_CHANNELS),
                                                        "sha256": builder.EXPECTED_PARENT_PINS["channels"][1]}),
             "exact parent channel provenance changed")
    _require(alpha.get("artifact_path") == builder.relative(builder.DEFAULT_ALPHA)
             and alpha.get("artifact_sha256") == manifest_hash
             and type(alpha.get("alpha_v31_frontier_new_count")) is int and alpha["alpha_v31_frontier_new_count"] == 574,
             "wrong actual additive Alpha channel pointer")
    for key in ("theorem_count", "checked_use_count", "evidence_counts", *expected_roots, "frontier_v31_campaign_counts"):
        _require(_same(alpha.get(key), catalog[key]), f"changed current Alpha channel identity: {key}")
    for key, path in (("catalog", builder.DEFAULT_ALPHA), ("catalog_delta", builder.DEFAULT_DELTA),
                      ("metrics", builder.DEFAULT_METRICS), ("dependency_graph", builder.DEFAULT_GRAPH)):
        _require(_same(alpha.get("artifacts", {}).get(key), {"path": builder.relative(path), "sha256": builder.digest(builder.read_bytes(path))}),
                 "the current channel does not bind every actual release component")
    _require(set(alpha["artifacts"]) == {"catalog", "catalog_delta", "metrics", "dependency_graph"}, "unreviewed channel artifacts")
    _require(channels.get("channel_pointer_root_sha256") == builder.digest(builder.compact(channels["channels"])), "channel pointer root changed")


class LiveReleaseContext:
    """A source- and artifact-bound publication capability, never a receipt."""

    __slots__ = ("_token", "_audit", "_catalog", "_channels", "_families", "_files", "_logical_digest", "_channel_digest", "catalog_sha256", "revision",
                 "promoted_names", "source_binding_sha256")

    def __init__(self, token, audit, catalog, channels, families, files):
        if token is not _LIVE_RELEASE or type(audit) is not proof_audit.FreshProofAudit:
            raise ReleaseError("saved metadata cannot authorize a checked Alpha publication")
        self._token, self._audit = token, audit
        self._catalog, self._channels, self._families = catalog, channels, families
        self._logical_digest, self._channel_digest = _content_digest(catalog), _content_digest(channels)
        self._files = tuple(files)
        self.catalog_sha256 = builder.digest(builder.read_bytes(builder.DEFAULT_ALPHA))
        self.revision = self.catalog_sha256[:12]
        self.promoted_names = tuple(row["name"] for row in catalog["theorems"][3222:])
        self.source_binding_sha256 = audit.binding

    @property
    def catalog(self):
        return self._catalog

    @property
    def channels(self):
        return self._channels

    @property
    def families(self):
        return self._families

    def require_unchanged(self):
        _require(type(self) is LiveReleaseContext and self._token is _LIVE_RELEASE, "no live current-release capability")
        self._audit.require_unchanged()
        for path, length, expected in self._files:
            contents = builder.read_bytes(path)
            _require(len(contents) == length and builder.digest(contents) == expected, "a release artifact changed after actual verification")
        # Detect in-process presentation mutation as well as changed files.
        _require(builder.digest(builder.compact(self._families)) == builder.digest(builder.compact({row["slug"]: row for row in self._audit.report["families"]})),
                 "live proof metadata was modified by a presentation consumer")
        _require(_content_digest(self._catalog) == self._logical_digest
                 and _content_digest(self._channels) == self._channel_digest,
                 "a publication consumer changed exact logical release data")


def context_from_live_audit(audit):
    """Audit current files using actual proof results from the same process chain."""
    _require(type(audit) is proof_audit.FreshProofAudit, "release verification requires actual fresh proof jobs")
    audit.require_unchanged()
    from peano_catalog_shards import load_catalog
    from peano_lab.library import editions_v31 as edition
    edition.require_completed_lower_seal()
    parent = builder._load_parent()
    channels = builder.strict_json(builder.read_bytes(builder.DEFAULT_CHANNELS))
    manifest_bytes = builder.read_bytes(builder.DEFAULT_ALPHA)
    manifest_hash = sha256(manifest_bytes).hexdigest()
    catalog = load_catalog(builder.DEFAULT_ALPHA, expected_sha256=manifest_hash)
    documents = _documents(catalog, parent, audit)
    _, families = _verify_rows(catalog, parent, audit, documents)
    metrics = builder.strict_json(builder.read_bytes(builder.DEFAULT_METRICS))
    _verify_metadata(catalog, metrics, channels, parent, families, audit, manifest_hash)
    # Independent default Stable replay remains ordinary HA, never Alpha.
    result = edition.replay("zero_add", edition="stable")
    from peano_lab.kernel.checker import check
    _require(check((), result.certificate, result.formula), "unchanged Stable replay failed")
    paths = (builder.DEFAULT_ALPHA, builder.DEFAULT_DELTA, builder.DEFAULT_METRICS,
             builder.DEFAULT_GRAPH, builder.DEFAULT_CHANNELS, builder.DEFAULT_RECEIPT, builder.PARENT_ALPHA)
    paths = tuple(dict.fromkeys((*paths, *(ROOT / path for path in builder.CONTROL_DOCUMENTS),
                                *(ROOT / path for path in builder.historical_evidence.archive_paths()),
                                *(ROOT / path for path in PRESENTATION_INPUT_SOURCES))))
    files = []
    for path in paths:
        contents = builder.read_bytes(path)
        files.append((path, len(contents), builder.digest(contents)))
    audit.require_unchanged()
    context = LiveReleaseContext(_LIVE_RELEASE, audit, catalog, channels, families, files)
    proof_audit.authoring_rss_bytes()
    return context


def verify_for_publication():
    """No cached receipt or skip option: every call runs all actual proof gates."""
    builder.preflight_inputs()
    return context_from_live_audit(proof_audit.verify_in_fresh_windows())


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)
    jobs = 1 + len(proof_audit.registry()) + sum(len(item.principal_roots) for item in proof_audit.registry())
    signal.alarm(jobs * proof_audit.PARENT_TIMEOUT_SECONDS + proof_audit.WALL_SECONDS)
    context = verify_for_publication()
    context.require_unchanged()
    proof_audit.authoring_rss_bytes()
    print("Independently verified Alpha v31: 3796 checked-use, 574 additive theorems, "
          "19 complete original-HA/compiled-Lean bundles; Stable432 unchanged; G009 multiplicativity still open.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
