#!/usr/bin/env python3
"""Create a genuinely checked additive Alpha-v34 research promotion."""

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
import build_peano_library_channels_v33 as previous_builder
import alpha_v31_historical_evidence as historical_evidence
import peano_catalog_shards as previous_codec
import peano_catalog_shards_v33 as parent_codec
import peano_catalog_shards_v34 as codec


SCHEMA = "peano-library-alpha-snapshot-v34"
METRICS_SCHEMA = "peano-library-alpha-metrics-v34"
CHANNEL_SCHEMA = "peano-library-channels-v34"
MAX_CATALOG_BYTES = 64*1024*1024
PARENT_ALPHA = ROOT / "artifacts/peano-library/alpha/catalog-v33.json"
PARENT_METRICS = ROOT / "artifacts/peano-library/alpha/metrics-v33.json"
PARENT_GRAPH = ROOT / "artifacts/peano-library/alpha/dependency-graph-v33.mmd"
PARENT_CHANNELS = ROOT / "artifacts/peano-library/channels-v33.json"
STABLE = ROOT / "artifacts/peano-library/catalog-v1.json"
DEFAULT_ALPHA = ROOT / "artifacts/peano-library/alpha/catalog-v34.json"
DEFAULT_DELTA = ROOT / "artifacts/peano-library/alpha/catalog-v34-delta.json"
DEFAULT_METRICS = ROOT / "artifacts/peano-library/alpha/metrics-v34.json"
DEFAULT_GRAPH = ROOT / "artifacts/peano-library/alpha/dependency-graph-v34.mmd"
DEFAULT_CHANNELS = ROOT / "artifacts/peano-library/channels-v34.json"
DEFAULT_RECEIPT = ROOT / "research/arithmetic-library/artifacts/alpha-v34-research-receipt-v1.json"
EXPECTED_PARENT_PINS = {
    "catalog": (PARENT_ALPHA, "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"),
    "catalog_delta": (PARENT_ALPHA.with_name("catalog-v33-delta.json"), "bf215f0a158b82dfb2e9e5e4a07fd7357d064b7f8a4e0230f3624b761775b1c4"),
    "catalog_base": (PARENT_ALPHA.with_name("catalog-v30.json"), "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"),
    "metrics": (PARENT_METRICS, "c0eef13d14b48ccf29f0effdbb1a882d62320025c93e32de516a383810eb295b"),
    "dependency_graph": (PARENT_GRAPH, "823afe0c40c4e12b51c0942075151fbcc6350308fcd904495363da50ee976a98"),
    "channels": (PARENT_CHANNELS, "d10d87694f813b86451bcccdde4dcd68e5d6fe73795b9610d98bea4f3e5de6bc"),
}
STABLE_SHA256 = previous_builder.STABLE_SHA256
ADMISSION_RFC = "research/arithmetic-library/alpha-v34-gcd-congruence-promotion-rfc-v1.md"
CONTROL_DOCUMENTS = {
    "scripts/check_alpha_v34_research.py": "Source-bound original-HA, same-byte Lean and separately bounded ordinary-principal release audit.",
    "scripts/build_peano_library_channels_v34.py": "Exact additive v34 release construction from a live proof invocation.",
    "scripts/verify_peano_library_channels_v34.py": "Independent exact admission, parent, provenance and channel verifier.",
    "scripts/peano_catalog_shards_v34.py": "Three-file nonrecursive cumulative catalogue transport; historical codecs unchanged.",
    "scripts/peano_catalog_capacity_v34.py": "Explicit logical catalogue8192 capacity; proof and byte limits unchanged.",
    "peano-lab/py/peano_lab/library/campaign_research_v34_closure.py": "Exact two-family complete original-HA proof provider.",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v34.py": "Exact registered additive ownership over the immutable v33 parent.",
    "peano-lab/py/peano_lab/library/editions_v34.py": "Fail-closed actual v34 checked-use runtime; Stable unchanged.",
    "peano-lab/py/peano_lab/library/research_source_plan_v34.py": "Exact canonical source-only artifact-order proof plan; original compiler and kernel unchanged.",
    "peano-lab/py/tests/test_research_source_plan_v34.py": "Independent source-plan identity, order, ownership and rejection regressions.",
    "peano-lab/py/tests/test_library_editions_v34_cold_import.py": "Independent bounded cold-import identity and unchanged Stable regression.",
    "peano-lab/py/tests/test_library_editions_v34_admission.py": "Exact parent and Stable identity, admission and hostile-input regressions.",
    "peano-lab/py/tests/test_campaign_research_v34_closure.py": "Actual complete provider and adversarial proof-source checks.",
    "scripts/test_check_alpha_v34_research.py": "Fresh worker binding, report and receipt-rejection regressions.",
    "scripts/test_peano_catalog_shards_v34.py": "Bounded cumulative transport and immutable v33-prefix adversarial audit.",
    "scripts/test_verify_peano_library_channels_v34.py": "Independent exact row, metadata, provenance and channel mutation audit.",
    ADMISSION_RFC: "Reviewed exact mathematical, admission and resource contract.",
}

digest = previous_builder.digest
compact = previous_builder.compact
pretty = previous_builder.pretty
strict_json = previous_builder.strict_json


def _audit_module():
    import check_alpha_v34_research
    return check_alpha_v34_research


def require_scope():
    """No provisional count can authorize a release or a proof invocation."""
    codec.require_registration()
    audit = _audit_module()
    inventory = audit.EXPECTED_INVENTORY
    if (type(inventory) is not tuple or len(inventory) != 2
            or any(type(row) is not tuple or len(row) != 2
                   or type(row[0]) is not str or type(row[1]) is not int for row in inventory)
            or inventory[0] != ("polynomial-gcd-bezout", 119)
            or inventory[1][0] != "congruence-arithmetic" or inventory[1][1] <= 0
            or tuple(codec.EXPECTED_CAMPAIGNS.items()) != inventory
            or sum(count for _, count in inventory) != codec.NEW_ROW_COUNT):
        raise ValueError("the exact ordered two-campaign v34 scope is not registered")
    registered = audit.registry()
    if (tuple(item.slug for item in registered) != tuple(slug for slug, _ in inventory)
            or len(registered[0].principal_roots) != 14
            or not registered[1].principal_roots
            or audit.EXPECTED_JOB_COUNT != 1 + len(registered) + sum(len(item.principal_roots) for item in registered)):
        raise ValueError("the exact separately checked v34 principal/job inventory changed")
    return inventory


def relative(path):
    return Path(path).relative_to(ROOT).as_posix()


def read_bytes(path, maximum=MAX_CATALOG_BYTES):
    return previous_builder.read_bytes(Path(path), maximum)


def _ordered_root(entries, *, include_origin):
    """The original ordered-root bytes, streamed without a whole-source join."""
    result = sha256()
    for index, entry in enumerate(entries):
        if index:
            result.update(b"\x1c")
        spec = entry.spec
        if include_origin:
            result.update(entry.enrollment_origin.value.encode("utf-8"))
            result.update(b"\x1f")
        result.update(spec.name.encode("utf-8"))
        result.update(b"\x1f")
        result.update(spec.statement.encode("utf-8"))
        result.update(b"\x1f")
        for position, dependency in enumerate(spec.dependencies):
            if position:
                result.update(b"\x1e")
            result.update(dependency.encode("utf-8"))
        result.update(b"\x1f")
        for position, command in enumerate(spec.script):
            if position:
                result.update(b"\x1e")
            result.update(command.encode("utf-8"))
    return result.hexdigest()


def _parent_binding():
    from peano_lab.library import editions_v33 as parent
    return {"artifacts": {label: {"path": relative(path), "sha256": pin}
                           for label, (path, pin) in EXPECTED_PARENT_PINS.items()},
            "edition_identity_sha256": parent.ALPHA_V33_IDENTITY_SHA256,
            "ordered_enrollment_root_sha256": parent.ALPHA_V33_ENROLLMENT_SHA256,
            "schema": "peano-library-alpha-snapshot-v33", "theorem_count": 4092}


def _verify_parent_documents(metadata):
    records = metadata.get("evidence_documents")
    if type(records) is not list or len(records) != 1020:
        raise ValueError("the exact 1020-document immutable v33 evidence inventory changed")
    checked = previous_codec._documents(records, "literal v33")
    for document in checked.values():
        if set(document) != {"path", "bytes", "sha256", "role"}:
            raise ValueError("unreviewed inherited evidence fields")
        historical_evidence.verify_inherited_document(document, root=ROOT)


def preflight_inputs():
    """Hash-only parent checks before large proof workers; no admission."""
    require_scope()
    for path, expected in EXPECTED_PARENT_PINS.values():
        if digest(read_bytes(path)) != expected:
            raise ValueError("immutable parent artifact changed: " + relative(path))
    if digest(read_bytes(STABLE)) != STABLE_SHA256:
        raise ValueError("the immutable Stable default changed")
    manifest = strict_json(read_bytes(PARENT_ALPHA))
    _verify_parent_documents(manifest["metadata"])
    for path in CONTROL_DOCUMENTS:
        read_bytes(ROOT / path)
    audit = _audit_module()
    for item in audit.registry():
        read_bytes(ROOT / item.rfc)
        for pin in item.modules:
            read_bytes(ROOT / audit.module_test_path(pin.module))
    del manifest
    gc.collect()
    audit.authoring_rss_bytes()


def _load_parent():
    from peano_lab.library import editions_v33 as parent
    parent.require_research_seal()
    for path, expected in EXPECTED_PARENT_PINS.values():
        if digest(read_bytes(path)) != expected:
            raise ValueError("immutable parent artifact changed: " + relative(path))
    if digest(read_bytes(STABLE)) != STABLE_SHA256:
        raise ValueError("the immutable Stable artifact changed")
    catalog = parent_codec.load_catalog(PARENT_ALPHA,
        expected_sha256=EXPECTED_PARENT_PINS["catalog"][1])
    if (catalog["schema"] != parent_codec.LOGICAL_SCHEMA or catalog["theorem_count"] != 4092
            or catalog["checked_use_count"] != 4092 or catalog["stable_count"] != 432
            or catalog["edition_identity_sha256"] != parent.ALPHA_V33_IDENTITY_SHA256
            or catalog["ordered_enrollment_root_sha256"] != parent.ALPHA_V33_ENROLLMENT_SHA256):
        raise ValueError("the exact immutable parent catalogue/runtime partition changed")
    names = set()
    for row, entry in zip(catalog["theorems"], parent.ALPHA_ENTRIES, strict=True):
        spec = entry.spec
        if (row["name"] != spec.name or row["statement"] != spec.statement
                or row["dependencies"] != list(spec.dependencies) or row["script"] != list(spec.script)
                or row["summary"] != spec.summary or row["checked_use"] is not True
                or row["body_checked"] is not True or not set(row["dependencies"]) <= names):
            raise ValueError("actual v33 runtime and immutable catalogue disagree")
        names.add(spec.name)
    _verify_parent_documents(catalog)
    return catalog


def _document(path, role, *, payload=None):
    raw = read_bytes(path) if payload is None else payload
    return {"bytes": len(raw), "path": relative(path), "role": role, "sha256": digest(raw)}


def _frontier_row(entry, index, item, family, documents):
    spec = entry.spec
    metrics = next(row for row in family["rows"] if row["name"] == spec.name)
    source = next(pin.path for pin in item.modules if pin.path == entry.source_module)
    pin = next(pin for pin in item.modules if pin.path == source)
    test = _audit_module().module_test_path(pin.module)
    body = {"name": spec.name, "command_count": len(spec.script),
            "dependency_count": len(spec.dependencies), "dne_command_count": 0,
            "status": "kernel_checked_dependency_curried_body",
            **{key: metrics[key] for key in ("proof_depth", "proof_edges", "proof_nodes", "proof_objects", "reused_objects")}}
    bundle = family["bundle"]
    closure = {"body_proof_depth": metrics["proof_depth"], "body_proof_nodes": metrics["proof_nodes"],
        "bundle_campaign": item.slug, "bundle_dependency_edge_count": bundle["dependency_edges_including_packaging"],
        "bundle_node_count": bundle["nodes_including_packaging_root"], "bundle_node_id": metrics["node_id"],
        "bundle_path": item.artifact, "bundle_root_id": bundle["packaging_root_id"],
        "certificate_representation": "peano-lab-bundle-v1", "certificate_sha256": item.artifact_sha256,
        "closure_kind": "dependency_closed_bundle_node", "digest_kind": "self-contained-proof-bundle-sha256",
        "kernel_mode": "intuitionistic", "node_statement_sha256": digest(spec.statement), "status": "checked"}
    transition = {"first_enrolled_version": "v34", "campaign": item.slug,
        "parent_catalog_sha256": EXPECTED_PARENT_PINS["catalog"][1],
        "source_sha256": documents[source]["sha256"], "test_sha256": documents[test]["sha256"],
        "rfc_sha256": documents[item.rfc]["sha256"], "body_receipt_sha256": digest(compact(body)),
        "bundle_campaign": item.slug, "bundle_node_id": metrics["node_id"], "bundle_sha256": item.artifact_sha256}
    links = [{"path": path, "document_sha256": documents[path]["sha256"], "kind": kind,
              "role": role, "selector": selector}
        for path, kind, role, selector in (
            (source, "alpha_v34_frontier_dependency_curried_body", "dependency_curried_body", "document"),
            (test, "alpha_v34_frontier_executable_audit", "statement_dependency_replay_mutation_audit", "document"),
            (item.rfc, "alpha_v34_frontier_campaign_rfc", "reviewed_constructive_campaign_contract", "document"),
            (item.artifact, "alpha_v34_complete_constructive_proof_bundle", "independently_kernel_checked_dependency_closed_proof", f"nodes[id={metrics['node_id']}]"),
            (relative(DEFAULT_RECEIPT), "alpha_v34_live_original_kernel_and_lean_receipt", "fresh_release_proof_verification", f"families[slug={item.slug}]"),
            (relative(PARENT_ALPHA), "sealed_alpha_v33_parent", "exact_immutable_parent_catalog_bytes", "catalog"))]
    return {"body_checked": True, "body_receipt": body, "checked_use": True,
        "dependencies": list(spec.dependencies), "dependencies_sha256": digest("\n".join(spec.dependencies)+"\n"),
        "enrollment_index": index, "enrollment_origin": entry.enrollment_origin.value,
        "evidence_status": "alpha_closed", "frontier_campaign": item.slug,
        "logical_spec_sha256": base._logical_spec_sha256(spec), "membership": "alpha_only",
        "name": spec.name, "proof_tag": None, "provenance": [entry.enrollment_origin.value],
        "script": list(spec.script), "script_sha256": digest("\n".join(spec.script)+"\n"),
        "source": {"kind": "candidate_module", "path": source, "sha256": documents[source]["sha256"]},
        "statement": spec.statement, "statement_sha256": digest(spec.statement),
        "summary": spec.summary, "summary_sha256": digest(spec.summary),
        "empty_context_closure": closure, "alpha_v34_frontier_enrollment": transition, "evidence_links": links}


def _topology(rows, parent_metrics):
    from peano_lab.library import editions_v34 as edition
    depths, closures, kept, redundant = base._dependency_analysis(rows)
    if (len(kept)+len(redundant) != edition.EXPECTED_ALPHA_V34_EDGE_COUNT
            or max(depths.values(), default=-1)+1 != edition.EXPECTED_ALPHA_V34_LAYER_COUNT):
        raise ValueError("the exact complete v34 theorem DAG changed")
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
        raise ValueError("display reduction changed mathematical reachability")
    kept_rows = [{"dependency": a, "theorem": b} for a, b in kept]
    redundant_rows = [{"dependency": a, "theorem": b} for a, b in redundant]
    origins = {row["name"]: row["enrollment_origin"] for row in rows}
    metadata = {"declared_edge_count": edition.EXPECTED_ALPHA_V34_EDGE_COUNT,
        "dependency_free_theorem_count": sum(not row["dependencies"] for row in rows),
        "layer_count": edition.EXPECTED_ALPHA_V34_LAYER_COUNT,
        "maximum_direct_dependency_count": max(len(row["dependencies"]) for row in rows),
        "maximum_transitive_dependency_count": max(map(len, closures.values()), default=0),
        "reachability_redundant_direct_dependencies": redundant_rows,
        "reachability_redundant_direct_dependency_count": len(redundant),
        "reachability_redundant_direct_dependency_count_by_enrollment_origin": dict(sorted(Counter(origins[b] for _, b in redundant).items())),
        "reachability_redundant_direct_dependency_sha256": digest(compact(redundant_rows)),
        "reachability_reduction_scope": parent_metrics["dependency_graph"]["reachability_reduction_scope"],
        "theorems_by_depth": {str(depth): count for depth, count in sorted(Counter(depths.values()).items())},
        "transitive_reduction_edge_count": len(kept), "transitive_reduction_edge_sha256": digest(compact(kept_rows)),
        "transitive_reduction_preserves_reachability": True}
    graph = graph_builder._alpha_graph(rows, kept, redundant).replace(
        "%% Generated by scripts/build_peano_library_channels_v13.py; do not edit.",
        "%% Generated by scripts/build_peano_library_channels_v34.py; do not edit.", 1).encode()
    return metadata, graph


def _promotion(report, families):
    from peano_lab.library import editions_v34 as edition
    return {"status": "kernel_checked_complete_dependency_closed_additive_edition",
        "parent_theorem_count": 4092, "frontier_new_count": codec.NEW_ROW_COUNT,
        "checked_use_before": 4092, "checked_use_after": codec.ROW_COUNT,
        "campaign_counts": dict(_audit_module().EXPECTED_INVENTORY),
        "frontier_ordered_names_sha256": digest("\n".join(edition.FRONTIER_NEW_NAMES)),
        "proof_bundle_count": 2, "proof_bundles": [families[item.slug]["bundle"] for item in _audit_module().registry()],
        "independent_lean_bundle_verified": True, "ordinary_principal_count": report["ordinary_principal_count"],
        "remaining_body_checked_count": 0, "receipt_path": relative(DEFAULT_RECEIPT),
        "receipt_sha256": digest(pretty(report)), "completed_named_targets": [], "inherited_completed_named_targets": ["G009"],
        "open_named_targets": ["G091"], "freshly_checked_new_theorems": codec.NEW_ROW_COUNT,
        "inherited_checked_theorems": 4092, "all_parent_admissions_freshly_replayed_here": False,
        "historical_evidence_archives": historical_evidence.archive_bindings()}


def _metrics(catalog, parent_metrics, topology, graph_bytes, manifest_bytes, promotion):
    metrics = deepcopy(parent_metrics)
    shared = ("theorem_count", "checked_use_count", "evidence_counts", "edition_identity_sha256",
              "ordered_enrollment_root_sha256", "ordered_spec_root_sha256",
              "frontier_v34_campaign_counts", "frontier_v34_ordered_names_sha256", "parent_alpha_v33", "catalogue_capacity_v34")
    metrics.update({key: catalog[key] for key in shared})
    metrics.update(schema=METRICS_SCHEMA, catalog_path=relative(DEFAULT_ALPHA), catalog_sha256=digest(manifest_bytes),
        dependency_graph=topology, dependency_graph_path=relative(DEFAULT_GRAPH), dependency_graph_sha256=digest(graph_bytes),
        alpha_v34_research_promotion=promotion)
    accounting = metrics["checked_closure_metrics"]
    accounting["certificate_digest_kinds"]["self-contained-proof-bundle-sha256"] += codec.NEW_ROW_COUNT
    accounting.update(metric_bearing_theorem_count=codec.ROW_COUNT, missing_empty_context_metric_count=0,
        campaign_v34_bundle_accounting={"campaign_count": 2, "campaign_counts": dict(_audit_module().EXPECTED_INVENTORY),
            "new_checked_theorem_count": codec.NEW_ROW_COUNT, "proof_bundles": promotion["proof_bundles"],
            "totals_policy": "Two complete checked artifacts; inherited support rows and packaging roots are not new admissions; only the exact registered owned rows are newly admitted."})
    gates = metrics["promotion_gates"]
    gates["canonical_topology"].update(theorem_count=codec.ROW_COUNT, declared_edge_count=catalog["edge_count"])
    gates["dependency_link_analysis"]["reachability_redundant_direct_dependency_count"] = topology["reachability_redundant_direct_dependency_count"]
    gates["source_integrity"]["source_bound_theorem_count"] = codec.ROW_COUNT
    gates["full_alpha_empty_context_compilation"].update(checked=codec.ROW_COUNT, missing=0, required=codec.ROW_COUNT, status="passed")
    gates["complete_constructive_alpha_v34_research"] = {**promotion, "status": "passed"}
    return metrics


def _channels(catalog, parent_channels, manifest_bytes, delta_bytes, metrics_bytes, graph_bytes):
    artifacts = {key: {"path": relative(path), "sha256": digest(raw)} for key, path, raw in (
        ("catalog", DEFAULT_ALPHA, manifest_bytes), ("catalog_delta", DEFAULT_DELTA, delta_bytes),
        ("dependency_graph", DEFAULT_GRAPH, graph_bytes), ("metrics", DEFAULT_METRICS, metrics_bytes))}
    alpha = {**parent_channels["channels"]["alpha"],
        "artifact_path": relative(DEFAULT_ALPHA), "artifact_sha256": digest(manifest_bytes), "artifacts": artifacts,
        "alpha_v34_frontier_new_count": codec.NEW_ROW_COUNT, "parent_alpha_v33_sha256": EXPECTED_PARENT_PINS["catalog"][1],
        "catalogue_capacity_v34": dict(codec.CAPACITY_METADATA),
        **{key: catalog[key] for key in ("theorem_count", "checked_use_count", "edition_identity_sha256",
            "evidence_counts", "evidence_root_sha256", "membership_root_sha256", "ordered_enrollment_root_sha256",
            "ordered_spec_root_sha256", "frontier_v34_campaign_counts")}}
    channels = {"schema": CHANNEL_SCHEMA, "channels": {"alpha": alpha, "stable": parent_channels["channels"]["stable"]},
        "default_channel": "stable", "policy": parent_channels["policy"],
        "parent_channels_v33": {"path": relative(PARENT_CHANNELS), "sha256": EXPECTED_PARENT_PINS["channels"][1]}}
    channels["channel_pointer_root_sha256"] = digest(compact(channels["channels"]))
    return channels


def _project_payloads(report):
    """Private in-memory formatting only; report bytes confer no authority.

    This pure projection is also used by explicitly non-authorizing UI/metadata
    preflights. It cannot create an audit, a live release, or write any output.
    Public admission must independently require the original live proof audit.
    """
    require_scope()
    proof_audit = _audit_module()
    from peano_lab.library import editions_v34 as edition
    edition.require_research_seal()
    parent = _load_parent()
    parent_metrics = strict_json(read_bytes(PARENT_METRICS))
    parent_channels = strict_json(read_bytes(PARENT_CHANNELS))
    receipt_bytes = pretty(report)
    records = report.get("families") if type(report) is dict else None
    if (type(records) is not list or len(records) != 2
            or any(type(row) is not dict for row in records)
            or tuple(row.get("slug") for row in records) != tuple(slug for slug, _ in proof_audit.EXPECTED_INVENTORY)
            or type(report.get("ordinary_principal_count")) is not int
            or report["ordinary_principal_count"] != sum(len(item.principal_roots) for item in proof_audit.registry())):
        raise ValueError("the live audit lost the exact ordered two-family/registered-principal inventory")
    families = {row["slug"]: row for row in records}
    documents = {row["path"]: row for row in parent["evidence_documents"]}

    def add(path, role, payload=None):
        record = _document(ROOT/path, role, payload=payload)
        if path in documents:
            old = documents[path]
            if old["bytes"] != record["bytes"] or old["sha256"] != record["sha256"]:
                raise ValueError("attempt to overwrite immutable evidence: " + path)
            return
        documents[path] = record

    for path, role in CONTROL_DOCUMENTS.items():
        add(path, role)
    for path, _size, _digest in proof_audit.WORKING_HISTORY_PINS:
        add(path, "Immutable non-admitted working-history document; preserved bytes, never admission authority.")
    for label, (path, _pin) in EXPECTED_PARENT_PINS.items():
        add(relative(path), "Exact immutable Alpha-v33 parent release component: " + label + ".")
    add(relative(DEFAULT_RECEIPT), "Fresh original-HA, same-byte compiled-Lean and registered ordinary-principal release audit.", receipt_bytes)
    ownership = {}
    for item in proof_audit.registry():
        add(item.artifact, "Complete actual constructive proof data; original research artifact unchanged.")
        add(item.rfc, "Exact reviewed constructive mathematical contract for " + item.slug + ".")
        for pin in item.modules:
            add(pin.path, "Exact constructive proof factory first admitted to Alpha v34.")
            add(proof_audit.module_test_path(pin.module), "Independent exact statement, proof and hostile-input regression audit.")
        for name in families[item.slug]["owned_node_ids"]:
            if name in ownership:
                raise ValueError("one theorem was counted as newly admitted twice")
            ownership[name] = item
    rows = list(parent["theorems"])
    for index, entry in enumerate(edition.ALPHA_ENTRIES[4092:], 4092):
        item = ownership[entry.spec.name]
        rows.append(_frontier_row(entry, index, item, families[item.slug], documents))
    if rows[:4092] != parent["theorems"] or len(rows) != codec.ROW_COUNT:
        raise ValueError("the exact unchanged-parent/additive partition changed")
    evidence = Counter(row["evidence_status"] for row in rows)
    memberships = Counter(row["membership"] for row in rows)
    origins = Counter(row["enrollment_origin"] for row in rows)
    if (evidence != Counter(stable_closed=432, alpha_closed=(codec.ROW_COUNT - 432))
            or memberships != Counter(stable=432, alpha_only=(codec.ROW_COUNT - 432))
            or not all(row["checked_use"] is True and row["body_checked"] is True for row in rows)):
        raise ValueError("unchecked or incorrectly partitioned admission records")
    topology, graph_bytes = _topology(rows, parent_metrics)
    promotion = _promotion(report, families)
    catalog = {**parent, "schema": SCHEMA, "theorem_count": codec.ROW_COUNT, "checked_use_count": codec.ROW_COUNT,
        "stable_count": 432, "alpha_only_count": (codec.ROW_COUNT - 432), "edge_count": edition.EXPECTED_ALPHA_V34_EDGE_COUNT,
        "layer_count": edition.EXPECTED_ALPHA_V34_LAYER_COUNT, "edition_identity_sha256": edition.ALPHA_V34_IDENTITY_SHA256,
        "ordered_enrollment_root_sha256": _ordered_root(edition.ALPHA_ENTRIES, include_origin=True),
        "ordered_spec_root_sha256": _ordered_root(edition.ALPHA_ENTRIES, include_origin=False),
        "membership_root_sha256": base._membership_root(rows), "evidence_root_sha256": base._evidence_root(rows),
        "enrollment_origin_counts": dict(sorted(origins.items())), "evidence_counts": dict(sorted(evidence.items())),
        "membership_counts": dict(sorted(memberships.items())),
        "canonical_order": [*parent["canonical_order"], *(f"Constructive Alpha-v34 {slug} ({count})" for slug, count in proof_audit.EXPECTED_INVENTORY)],
        "evidence_documents": [documents[path] for path in sorted(documents)],
        "frontier_v34_campaign_counts": dict(proof_audit.EXPECTED_INVENTORY),
        "frontier_v34_ordered_names_sha256": digest("\n".join(edition.FRONTIER_NEW_NAMES)),
        "parent_alpha_v33": _parent_binding(), "alpha_v34_research_promotion": promotion,
        "catalogue_capacity_v34": dict(codec.CAPACITY_METADATA), "theorems": rows}
    if catalog["ordered_enrollment_root_sha256"] != edition.ALPHA_V34_ENROLLMENT_SHA256:
        raise ValueError("the exact additive enrollment identity changed")
    manifest_bytes, delta_bytes = codec.encode_catalog({key: value for key, value in catalog.items() if key != "theorems"}, rows[3222:])
    metrics = _metrics(catalog, parent_metrics, topology, graph_bytes, manifest_bytes, promotion)
    metrics_bytes = pretty(metrics)
    channels = _channels(catalog, parent_channels, manifest_bytes, delta_bytes, metrics_bytes, graph_bytes)
    return {DEFAULT_ALPHA: manifest_bytes, DEFAULT_DELTA: delta_bytes, DEFAULT_METRICS: metrics_bytes,
            DEFAULT_GRAPH: graph_bytes, DEFAULT_CHANNELS: pretty(channels), DEFAULT_RECEIPT: receipt_bytes}


def build_payloads(audit=None):
    """A live unchanged proof invocation is mandatory; JSON receipts cannot enter."""
    require_scope()
    proof_audit = _audit_module()
    if audit is None:
        preflight_inputs()
        audit = proof_audit.verify_in_fresh_windows()
    if type(audit) is not proof_audit.FreshProofAudit:
        raise ValueError("a stored report cannot authorize Alpha v34 admission")
    audit.require_unchanged()
    payloads = _project_payloads(audit.report)
    audit.require_unchanged()
    proof_audit.authoring_rss_bytes()
    return payloads, audit


def check_or_write(payloads, *, check):
    expected_paths = {DEFAULT_ALPHA, DEFAULT_DELTA, DEFAULT_METRICS, DEFAULT_GRAPH, DEFAULT_CHANNELS, DEFAULT_RECEIPT}
    if type(payloads) is not dict or set(payloads) != expected_paths:
        raise ValueError("a v34 release must have exactly its six dedicated output files")
    for path, raw in payloads.items():
        if type(raw) is not bytes or not 0 < len(raw) <= MAX_CATALOG_BYTES:
            raise ValueError("a release output exceeds its original document limit")
        if check:
            if read_bytes(path) != raw:
                raise ValueError("stale v34 release artifact: " + relative(path))
        elif path.exists() or path.is_symlink():
            raise ValueError("refusing to overwrite a release artifact: " + relative(path))
    if not check:
        for path, raw in payloads.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(raw)
    _audit_module().authoring_rss_bytes()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--with-publication", action="store_true")
    args = parser.parse_args(argv)
    proof_audit = _audit_module()
    resource.setrlimit(resource.RLIMIT_CPU, proof_audit.CPU_LIMITS)
    signal.alarm(proof_audit.EXPECTED_JOB_COUNT*proof_audit.PARENT_TIMEOUT_SECONDS + 4*proof_audit.WALL_SECONDS)
    payloads, audit = build_payloads()
    from verify_peano_library_channels_v34 import context_from_live_audit, verify_candidate_payloads
    verify_candidate_payloads(payloads, audit)
    check_or_write(payloads, check=args.check)
    context = context_from_live_audit(audit)
    if args.with_publication:
        from publish_constructive_research_v34 import publish_from_live_context
        publish_from_live_context(context, check=args.check)
    context.require_unchanged()
    print(f"{'Verified' if args.check else 'Created'} Alpha v34: {codec.ROW_COUNT} checked-use; {codec.NEW_ROW_COUNT} new; 2 original-HA/compiled-Lean bundles; Stable432 unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
