#!/usr/bin/env python3
"""Canonical proof explorers for independently closed lower-layer targets.

This local deterministic publisher authenticates the immutable release before
rendering. Definitions and atlas annotations never supply theorem evidence.
The current Alpha edition and a theorem's first admission remain distinct.
"""

from __future__ import annotations

import argparse
from collections import Counter
from collections.abc import Mapping, Sequence
from importlib import import_module
import json
from pathlib import Path
import subprocess
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
if str(REPO / "peano-lab/py") not in sys.path:
    sys.path.insert(0, str(REPO / "peano-lab/py"))

from build_constructive_second_wave_explorer import (
    ASSET_SOURCES, INHERITED_REVISED_SOURCE_SHA256, Family, _compact_script,
    _digest, _json, _strict_json,
)
from constructive_formula_compactor import _FormulaCompactor
from constructive_frontier_exact_explorer import render_exact_index, render_exact_theorem
from constructive_proof_explorer_template import render_canonical_family_landing
from constructive_lower_layer_definition_graph import build_definition_graph, reviewed_registry
from constructive_lower_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME, LOWER_LAYER_REGISTRIES, definition_closure,
)
from constructive_checked_explorer_renderer import (
    ASSET_DIGESTS, _asset, _atlas_navigation, _defined_definition,
    _defined_graph, _defined_index, _defined_theorem, _e, _graph_payload, _status, _versioned,
)
from peano_lab.library import campaign_lower_layer_closure as closure
from peano_lab.library.defined_syntax import DefinitionSpec
from peano_lab.library.theorems import TheoremSpec


OUTPUT = REPO / "book/_static/constructive-lower-layer-explorer"
CATALOG = REPO / "artifacts/peano-library/alpha/catalog-v28.json"
CHANNELS = REPO / "artifacts/peano-library/channels-v28.json"
CAMPAIGN = REPO / "book/_static/constructive-grand-campaign/campaign.json"
GLOBAL_DEFINITIONS = CAMPAIGN.with_name("definitions.json")
SCHEMA = "peano-lab-constructive-lower-layer-explorer-v1"
EXPECTED_BUNDLE_PATH = "research/arithmetic-library/artifacts/alpha-v28-lower-layer-proof-bundle-v1.json"
PARENT_CATALOG_SHA256 = "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6"


class LowerLayerExplorerError(ValueError):
    """Exact proof evidence, conservative notation, or a release boundary changed."""


MILESTONE_ROOTS = {
    "G001": "foundation_division_exists_unique",
    "G002": "foundation_signed_bezout_canonical_gcd",
    "G003": "foundation_coprime_product_divisor",
    "G004": "foundation_prime_factor_list_exists",
    "G005": "prime_factor_lists_permutation_exists",
    "G021": "foundation_primes_above_every_bound",
    "G022": "first_primes_double_exponential_bound",
    "G081": "gaussian_euclidean_division_exists",
    "G084": "eisenstein_euclidean_division_exists",
}
THEOREM_MILESTONES = {name: goal for goal, name in MILESTONE_ROOTS.items()}

FAMILIES = (
    Family(
        "arithmetic-foundations", "foundations", "AF",
        "Constructive arithmetic and unique factorization",
        "Unique division · canonical signed Bézout · unordered prime factors",
        "Expose exact foundation interfaces and construct an actual finite permutation between arbitrary prime factorizations, with no sorting or supplied canonicalization.",
        "n>0 ⇒ ∃ prime factor list; any two lists are related by a witnessed bijection",
        "D01", "F01", ("G001", "G002", "G003", "G004", "G005"),
        ("foundation_division_exists_unique", "foundation_signed_bezout_canonical_gcd",
         "foundation_coprime_product_divisor", "foundation_prime_factor_list_exists",
         "prime_factor_lists_permutation_exists", "prime_factorization_exists_unique_up_to_permutation"),
        ("arithmetic-foundations",), ("DivRem", "IsGCD", "Coprime", "Dvd"),
        "The original division, gcd, cancellation, and factor-existence foundations are exposed through checked wrappers. Unordered uniqueness adds an actual bounded, injective, surjective index map matching repeated prime occurrences. The empty factor list represents one, not zero.",
    ),
    Family(
        "prime-enumeration", "prime_enumeration", "PE",
        "The first primes with explicit constructive bounds",
        "Least-prime search · complete increasing lists · witnessed powers",
        "Construct the actual first k primes, prove that none is omitted, and bound the last prime by explicitly constructed powers of two.",
        "k>0 ⇒ ∃ first k primes p₁<⋯<pₖ with pₖ<2^(2^k)",
        "D02", "F03", ("G021", "G022"),
        ("foundation_primes_above_every_bound", "least_prime_above_exists_unique",
         "first_primes_list_exists", "prime_list_every_entry_is_prime",
         "prime_list_strictly_increasing", "prime_list_omits_no_smaller_prime",
         "first_primes_double_exponential_bound"),
        ("prime-enumeration",), ("PowTwo", "Prime", "Le", "Lt", "BetaAt"),
        "Every successor is the globally least prime above its predecessor. This is not a sparse Bertrand chain. The bound theorem constructs the list and both power witnesses from k≠0 alone; the separate total-list theorem includes k=0.",
    ),
    Family(
        "gaussian-integers", "gaussian_euclidean", "GI",
        "Constructive Gaussian Euclidean division",
        "Shared canonical integer codes · nearest square quotient · strict norm decrease",
        "Construct actual Gaussian quotient and remainder codes for every nonzero divisor, using witnessed signed rounding and the genuine norm a²+b².",
        "a,b∈ℤ[i], b≠0 ⇒ ∃q,r. a=bq+r ∧ N(r)<N(b)",
        "D02", "F09", ("G081",),
        ("gaussian_norm_exists_unique", "gaussian_add_exists", "gaussian_multiply_exists",
         "gaussian_norm_multiply", "gaussian_euclidean_division_exists"),
        ("gaussian-integers",), ("SignedAdd", "SignedMul", "SignedNegate"),
        "The natural-code carrier consists of genuine pairs of the existing signed integers; no new primitive arithmetic is trusted. The theorem constructs quotient, remainder, and actual norm witnesses. Gaussian gcd, unique factorization, and prime classification are separate targets.",
    ),
    Family(
        "eisenstein-integers", "eisenstein_euclidean", "EI",
        "Constructive Eisenstein Euclidean division",
        "Shared signed-pair carrier · explicit floor quotient · strict norm decrease",
        "Construct actual Eisenstein quotient and remainder codes in ℤ[ω], with ω²+ω+1=0 and the genuine norm a²−ab+b².",
        "a,b∈ℤ[ω], b≠0 ⇒ ∃q,r. a=bq+r ∧ N(r)<N(b)",
        "D02", "F09", ("G084",),
        ("eisenstein_norm_exists", "eisenstein_norm_functional", "eisenstein_add_exists",
         "eisenstein_multiply_exists", "eisenstein_norm_multiply", "eisenstein_euclidean_division_exists"),
        ("eisenstein-integers",), ("ZPairDecode", "ZPairRep", "ZPairValid", "SignedFloor", "SignedDifferenceSquare"),
        "A floor quotient in the fundamental parallelogram already gives the required strict norm decrease; global nearest-point optimality is not asserted. The shared carrier is identical to the Gaussian carrier, but the multiplication law and norm are different. Eisenstein gcd, factorization, and prime classification remain separate targets.",
    ),
)


def _factory_rows() -> tuple[tuple[closure.LowerLayerFactory, TheoremSpec], ...]:
    return tuple((owner, row) for owner in closure.FACTORIES
                 for row in getattr(import_module(f"peano_lab.library.{owner.module}"), owner.factory)(TheoremSpec))


def _selected(family: Family, frontier) -> list:
    # Euclid unboundedness belongs to the prime family in the presentation,
    # while its immutable authoring/admission origin remains foundations.
    unbounded = MILESTONE_ROOTS["G021"]
    return [(owner, row) for owner, row in frontier
            if (row.name == unbounded and family.campaign == "prime_enumeration")
            or (row.name != unbounded and owner.campaign == family.campaign)]


def _load_release_inputs() -> dict[str, Any]:
    # The release verifier checks exact rows, historical prefixes, body and
    # closure receipts, source bytes, topology, and both unchanged verifiers.
    # Do not replace it with a presentation cache or an atlas-derived status.
    from verify_peano_library_channels_v28 import verify

    verify()
    raw, channel_raw = CATALOG.read_bytes(), CHANNELS.read_bytes()
    catalog, channels = _strict_json(raw), _strict_json(channel_raw)
    parent_raw = (REPO / closure.PARENT_CATALOG).read_bytes()
    if _digest(parent_raw) != PARENT_CATALOG_SHA256:
        raise LowerLayerExplorerError("the immutable v27 parent catalog changed")
    parent = _strict_json(parent_raw)
    rows, frontier = catalog["theorems"], _factory_rows()
    channel = channels["channels"]["alpha"]
    if (catalog["schema"] != "peano-library-alpha-snapshot-v28"
        or catalog["checked_use_count"] != len(rows)
        or len(rows) != len(parent["theorems"]) + len(frontier)
        or _json(rows[:len(parent["theorems"])]) != _json(parent["theorems"])
        or channel["artifact_sha256"] != _digest(raw)
        or channel["artifact_path"] != CATALOG.relative_to(REPO).as_posix()
        or channels["default_channel"] != "stable" or catalog["stable_count"] != 432):
        raise LowerLayerExplorerError("current authority or exact historical admission changed")
    promotion = catalog["alpha_v28_lower_layer_promotion"]
    bundle = promotion["proof_bundle"]
    if (promotion["independent_lean_bundle_verified"] is not True
        or bundle["independent_lean_bundle_verified"] is not True
        or bundle["artifact_path"] != EXPECTED_BUNDLE_PATH):
        raise LowerLayerExplorerError("the lower layer lacks its complete independent closure")
    revised = []
    parent_documents = {row["path"] for row in parent["evidence_documents"]}
    for document in catalog["evidence_documents"]:
        data = (REPO / document["path"]).read_bytes()
        if len(data) != document["bytes"] or _digest(data) != document["sha256"]:
            if document["path"] not in parent_documents or INHERITED_REVISED_SOURCE_SHA256.get(document["path"]) != _digest(data):
                raise LowerLayerExplorerError("a sealed source changed after release verification")
            revised.append({"path": document["path"], "historical_sha256": document["sha256"],
                            "later_checked_in_sha256": _digest(data), "proof_authority": False,
                            "changed_by_lower_layer": False})
    return {"catalog": catalog, "catalog_sha256": _digest(raw), "revision": _digest(raw)[:12],
            "by_name": {row["name"]: row for row in rows}, "frontier": frontier,
            "bundle": bundle, "first_version": "v28", "first_catalog_sha256": _digest(raw),
            "schema": SCHEMA, "current_edition_identity_sha256": catalog["edition_identity_sha256"],
            "inherited_revised_audit_sources": revised}


def _load_inputs() -> dict[str, Any]:
    inputs = _load_release_inputs()
    campaign, graph = _strict_json(CAMPAIGN.read_bytes()), _strict_json(GLOBAL_DEFINITIONS.read_bytes())
    _audit_current_campaign(campaign, graph, inputs)
    return {**inputs, "campaign": campaign, "global_graph": graph}


def _audit_current_campaign(campaign: dict[str, Any], graph: dict[str, Any], inputs: dict[str, Any]) -> None:
    from extend_constructive_lower_layer_campaign import extend_campaign

    if campaign.get("meta", {}).get("current_alpha_version") != "v28" or _json(graph) != _json(build_definition_graph(campaign)):
        raise LowerLayerExplorerError("the current campaign or conservative definition atlas is stale")
    if _json(campaign) != _json(extend_campaign(campaign, inputs)):
        raise LowerLayerExplorerError("the atlas differs from the exact lower-layer closure contract")
    goals = {row["id"]: row for row in campaign["nodes"]}
    for identifier, name in MILESTONE_ROOTS.items():
        evidence = goals[identifier].get("evidence", {})
        if (goals[identifier]["status"] != "alpha_closed" or evidence.get("checked_use") is not True
            or evidence.get("stable_member") is not False or evidence.get("theorem_name") != name
            or inputs["by_name"][name].get("checked_use") is not True):
            raise LowerLayerExplorerError(f"the exact target is not independently closed: {identifier}")


def _family_definitions(family: Family) -> tuple[DefinitionSpec, ...]:
    from constructive_second_wave_definitions import SECOND_WAVE_REGISTRIES

    names = tuple(item.name for route, definitions in (*SECOND_WAVE_REGISTRIES, *LOWER_LAYER_REGISTRIES)
                  if route in family.definition_routes for item in definitions)
    if not names:
        raise LowerLayerExplorerError(f"the family has no reviewed definition registry: {family.slug}")
    return definition_closure(tuple(dict.fromkeys((*names, *family.extra_definitions))))


def _definition_records(family: Family, inputs: Mapping[str, Any]) -> tuple[tuple[DefinitionSpec, ...], list[dict[str, Any]]]:
    specs = _family_definitions(family)
    reviewed, _, _ = reviewed_registry()
    links = {row["reviewed_name"]: row for row in inputs["global_graph"]["compatible_reviewed_matches"]}
    by_name, by_id, records = {item.name: item for item in specs}, {}, []
    for definition in specs:
        direct = [by_name[name].stable_id for name in definition.conceptual_dependencies]
        ancestors = set(direct)
        for identifier in direct:
            ancestors.update(by_id[identifier]["transitive_dependencies"])
        identity = reviewed[definition.name]
        if identity["id"] != definition.stable_id or identity["expansion_sha256"] != _digest(definition.template_source):
            raise LowerLayerExplorerError("a historical or new reviewed definition identity changed")
        link = links.get(definition.name)
        if link is not None and (link["reviewed_id"] != definition.stable_id or tuple(link["reviewed_parameters"]) != definition.parameters):
            raise LowerLayerExplorerError("a blueprint alias changed its exact reviewed signature")
        expansion = _FormulaCompactor(definition_closure(definition.conceptual_dependencies)).compact(definition.template_source)
        record = {
            "id": definition.stable_id, "name": definition.name, "parameters": list(definition.parameters),
            "arity": definition.arity, "signature": f"{definition.name}({','.join(definition.parameters)})",
            "summary": definition.summary, "expanded_template": definition.template_source,
            "expansion_sha256": _digest(definition.template_source),
            "defined_template": expansion["defined_statement"], "defined_template_parts": expansion["statement_parts"],
            "dependencies": direct, "dependency_names": list(definition.conceptual_dependencies),
            "topological_layer": max((by_id[value]["topological_layer"] + 1 for value in direct), default=0),
            "transitive_dependencies": sorted(ancestors), "origin": "shared-reviewed-hygienic-conservative-definition",
            "reviewed_definition_id": definition.stable_id, "reviewed_definition_route": identity["route"],
            "shared_definition_identity": definition.stable_id,
            "global_definition": None if link is None else link["blueprint_name"],
            "global_argument_positions": None if link is None else list(link["reviewed_argument_blueprint_positions"]),
            "exact_ast_verified": True, "kernel_signature_unchanged": True,
        }
        by_id[definition.stable_id] = record
        records.append(record)
    return specs, records


def _family_corpus(family: Family, inputs: Mapping[str, Any]) -> dict[str, Any]:
    selected = _selected(family, inputs["frontier"])
    labels = {"alpha_edition_version": "v28", "alpha_first_enrolled_version": inputs["first_version"]}
    status = _status(labels)
    specs, definitions = _definition_records(family, inputs)
    compactor = _FormulaCompactor(specs)
    tags = {spec.name: f"{family.prefix}{index:04X}" for index, (_, spec) in enumerate(selected, 1)}
    nodes = []
    for owner, spec in selected:
        row = inputs["by_name"][spec.name]
        receipt = row["empty_context_closure"]
        if (row.get("statement") != spec.statement or row.get("script") != list(spec.script)
            or row.get("dependencies") != list(spec.dependencies) or row.get("summary") != spec.summary
            or row.get("statement_sha256") != _digest(spec.statement)
            or row.get("script_sha256") != _digest("\n".join(spec.script) + "\n")
            or row.get("checked_use") is not True or row.get("body_checked") is not True
            or row.get("membership") != "alpha_only" or row.get("evidence_status") != "alpha_closed"
            or row.get("frontier_campaign") != owner.campaign
            or receipt.get("status") != "checked" or receipt.get("kernel_mode") != "intuitionistic"
            or receipt.get("certificate_sha256") != inputs["bundle"]["artifact_sha256"]):
            raise LowerLayerExplorerError(f"a displayed row differs from its exact checked proof: {spec.name}")
        reading = compactor.compact(spec.statement)
        _compact_script(spec, compactor, reading)
        nodes.append({
            "id": tags[spec.name], "name": spec.name, "summary": spec.summary,
            "statement": spec.statement, "statement_sha256": row["statement_sha256"],
            "script": list(spec.script), "dependencies": list(spec.dependencies),
            "source_module": f"peano_lab.library.{owner.module}", "factory": owner.factory,
            "sources": [{"source_module": f"peano_lab.library.{owner.module}", "factory": owner.factory,
                         "selected": True, "statement_sha256": row["statement_sha256"], "script_sha256": row["script_sha256"]}],
            "status": status, "enrolled_in_alpha": True, "alpha_evidence": "alpha_closed",
            "alpha_checked_use": True, "alpha_edition_version": "v28", "alpha_first_enrolled_version": inputs["first_version"],
            "stable_member": False, "admitted_to_alpha": True, "admitted_to_stable": False, "checked_use": True,
            "independent_lean_bundle_verified": True, "proof_bundle_node_id": receipt["bundle_node_id"],
            "proof_bundle_sha256": receipt["certificate_sha256"],
            "body_proof_nodes": receipt["body_proof_nodes"], "body_proof_depth": receipt["body_proof_depth"],
            "campaign_milestone": THEOREM_MILESTONES.get(spec.name, family.milestones[-1]), "defined": reading,
        })
    if not selected or not set(family.roots) <= tags.keys():
        raise LowerLayerExplorerError(f"missing actual proof family or endpoint: {family.slug}")
    external = []
    for name in sorted({dependency for node in nodes for dependency in node["dependencies"] if dependency not in tags}):
        row = inputs["by_name"][name]
        if row.get("checked_use") is not True:
            raise LowerLayerExplorerError("an unproved premise entered a public graph")
        external.append({"name": name, "evidence": row["evidence_status"], "alpha_evidence": row["evidence_status"],
                         "alpha_checked_use": True, "enrolled_in_alpha": True, "admitted_to_alpha": True,
                         "admitted_to_stable": row["membership"] == "stable", "statement_sha256": row["statement_sha256"]})
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if any(name not in layers for name in internal):
            raise LowerLayerExplorerError("a proof dependency is circular or points forward")
        name = node["name"]
        layers[name] = max((layers[dependency] + 1 for dependency in internal), default=0)
        predecessor = max(internal, key=lambda dependency: len(paths[dependency]), default=None)
        paths[name] = ([] if predecessor is None else paths[predecessor]) + [tags[name]]
        adjacency[name] = {"dependencies": internal,
                           "dependents": [other["name"] for other in nodes if name in other["dependencies"]],
                           "critical_root_path": paths[name]}
    proof_edges = [{"kind": "proof_dependency", "source": tags[name], "target": node["id"]}
                   for node in nodes for name in node["dependencies"] if name in tags]
    usage_edges = [{"kind": "uses_definition", "source": node["id"], "target": identifier,
                    "occurrence_count": count,
                    "statement_occurrences": node["defined"]["statement_definition_uses"].get(identifier, 0),
                    "local_proposition_occurrences": node["defined"]["script_definition_uses"].get(identifier, 0)}
                   for node in nodes for identifier, count in node["defined"]["definition_uses"].items()]
    definition_edges = [{"kind": "definition_uses_definition", "source": item["id"], "target": dependency}
                        for item in definitions for dependency in item["dependencies"]]
    return {
        "schema": inputs["schema"], "family_slug": family.slug, "family_title": family.title,
        "campaign_domain_id": family.domain, "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1], "campaign_milestone_ids": list(family.milestones),
        "root_names": list(family.roots), "nodes": nodes, "definitions": definitions,
        "external_dependencies": external, "external_theorem_routes": {name: route for name, route in inputs.get("theorem_routes", {}).items() if name not in tags}, "edges": proof_edges + usage_edges + definition_edges,
        "node_count": len(nodes), "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges), "external_dependency_count": len(external),
        "definition_count": len(definitions), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((item["topological_layer"] + 1 for item in definitions), default=0),
        "definition_topological_order": [item["id"] for item in definitions],
        "statement_definition_use_count": sum(bool(edge["statement_occurrences"]) for edge in usage_edges),
        "local_proposition_definition_use_count": sum(bool(edge["local_proposition_occurrences"]) for edge in usage_edges),
        "formal_line_count": sum(len(node["script"]) for node in nodes), "candidate_status": status,
        "alpha_edition_version": "v28", "alpha_first_enrolled_version": inputs["first_version"],
        "alpha_edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_catalog_sha256": inputs["catalog_sha256"], "alpha_first_enrollment_catalog_sha256": inputs["first_catalog_sha256"],
        "alpha_proof_bundle_sha256": inputs["bundle"]["artifact_sha256"],
        "proof_bundle_node_count": inputs["bundle"]["node_count"], "independent_lean_bundle_verified": True,
        "alpha_enrolled_node_count": len(nodes), "alpha_checked_use_node_count": len(nodes),
        "stable_admitted_node_count": 0, "tags": tags, "layers": layers, "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in paths.items()}, "path_policy": "proof_dependency_edges_only",
    }


def _exact_navigation(document: bytes, family: Family, *, prefix: str, revision: str) -> bytes:
    if document.count(b"</nav>") != 1:
        raise LowerLayerExplorerError("the original exact renderer changed its navigation contract")
    extra = _atlas_navigation(family, prefix=prefix, revision=revision).encode()
    return document.replace(b"</nav>", extra + b"</nav>", 1)


def _portable_navigation(document: bytes, package_slug: str) -> bytes:
    """Keep deployed links and raw repository snapshots navigable."""
    if document.count(b"</body>") != 1:
        raise LowerLayerExplorerError("a canonical page lost its document boundary")
    script = r'''<script>
(function () {
  "use strict";
  var marker = __PACKAGE_MARKER__;
  var offset = location.pathname.indexOf(marker);
  if (offset < 0) return;
  var staticRoot = location.pathname.slice(0, offset);
  var repository = staticRoot.replace(/\/book\/_static$/, "");
  document.querySelectorAll("a[href]").forEach(function (link) {
    var original = link.getAttribute("href");
    if (!original || /^(?:https?:|mailto:|#)/.test(original)) return;
    var destination = new URL(original, location.href);
    if (destination.pathname.indexOf("/grand-campaign/") >= 0) {
      destination.pathname = staticRoot + "/constructive-grand-campaign/";
    } else if (/\/artifacts\/alpha-v[0-9]+-[a-z0-9-]+\.(?:json|md)$/.test(destination.pathname)) {
      var filename = destination.pathname.slice(destination.pathname.lastIndexOf("/") + 1);
      destination.pathname = repository + "/research/arithmetic-library/" +
        (filename.endsWith(".json") ? "artifacts/" : "") + filename;
    } else return;
    link.setAttribute("href", destination.href);
  });
})();
</script>'''.replace("__PACKAGE_MARKER__", json.dumps("/" + package_slug + "/"))
    return document.replace(b"</body>", script.encode() + b"\n</body>", 1)


def render_files(
    inputs: dict[str, Any], families: Sequence[Family], *, package_slug: str,
    title: str, lede: str, scope: str, receipt_name: str,
) -> dict[str, bytes]:
    """Render only the caller's independently authenticated exact release slice."""
    inputs = dict(inputs)
    routes = {
        spec.name: f"{family.slug}/explorer/defined/tag/{family.prefix}{index:04X}.html"
        for family in families for index, (_, spec) in enumerate(_selected(family, inputs["frontier"]), 1)
    }
    if set(routes) != {spec.name for _, spec in inputs["frontier"]}:
        raise LowerLayerExplorerError("the presentation omitted or invented a frontier theorem")
    if len(routes) != sum(len(_selected(family, inputs["frontier"])) for family in families):
        raise LowerLayerExplorerError("a theorem was duplicated across presentation families")
    inputs["theorem_routes"] = routes
    revision, files, built = inputs["revision"], {}, []
    for name, path in ASSET_SOURCES.items():
        payload = path.read_bytes()
        if name in ASSET_DIGESTS and _digest(payload) != ASSET_DIGESTS[name]:
            raise LowerLayerExplorerError(f"a canonical QR graph asset changed: {name}")
        files[f"assets/{name}"] = payload
    for family in families:
        corpus = _family_corpus(family, inputs)
        graph = _graph_payload(family, corpus, revision=revision)
        slug = family.slug
        files[f"{slug}/index.html"] = render_canonical_family_landing(
            family, corpus, revision=revision, current_alpha_version="v28",
            first_admitted_version=inputs["first_version"], bundle_node_count=inputs["bundle"]["node_count"],
        )
        files[f"{slug}/api/corpus.json"] = _json(corpus)
        files[f"{slug}/explorer/index.html"] = _exact_navigation(render_exact_index(
            family, corpus, corpus["tags"], corpus["layers"], stylesheet_href=_asset("exact-explorer.css", "../../"),
            script_href=_asset("exact-explorer.js", "../../"), html_revision=revision,
        ), family, prefix="../../", revision=revision)
        files[f"{slug}/explorer/defined/index.html"] = _defined_index(family, corpus, revision=revision)
        files[f"{slug}/explorer/defined/graph.html"] = _defined_graph(family, corpus, graph, revision=revision)
        files[f"{slug}/explorer/defined/api/graph.json"] = _json(graph)
        for node in corpus["nodes"]:
            tag = node["id"]
            files[f"{slug}/explorer/tag/{tag}.html"] = _exact_navigation(render_exact_theorem(
                family, corpus, node, corpus["tags"], corpus["layers"], stylesheet_href=_asset("exact-explorer.css", "../../../"),
                script_href=_asset("exact-explorer.js", "../../../"), html_revision=revision,
            ), family, prefix="../../../", revision=revision)
            files[f"{slug}/explorer/defined/tag/{tag}.html"] = _defined_theorem(family, corpus, node, revision=revision)
        for definition in corpus["definitions"]:
            files[f"{slug}/explorer/defined/definition/{definition['id']}.html"] = _defined_definition(family, corpus, definition, revision=revision)
        built.append((family, corpus))
    cards = "".join(
        f'<article class="family-card"><p class="card-kicker">{_e(family.kicker)}</p><h2>{_e(family.title)}</h2>'
        f'<p>{_e(family.description)}</p><dl class="stats"><div><dt>{corpus["node_count"]}</dt><dd>checked theorems</dd></div>'
        f'<div><dt>{corpus["definition_count"]}</dt><dd>definitions</dd></div><div><dt>{corpus["edge_count"]}</dt><dd>proof edges</dd></div></dl>'
        f'<a class="primary-action" href="{_versioned(family.slug + "/", revision)}">Explore the proofs <span aria-hidden="true">→</span></a></article>'
        for family, corpus in built
    )
    files["index.html"] = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{_e(title)} — Proof library</title><link rel="stylesheet" href="{_versioned('assets/proofs.css',revision)}"></head><body><header class="hero"><div class="shell"><p class="eyebrow">Alpha v28 · unchanged intuitionistic HA · independently checked in Lean</p><h1>{_e(title)}</h1><p class="lede">{_e(lede)} Stable remains the separate unchanged 432-theorem edition.</p><nav class="hero-actions"><a class="secondary-action" href="{_versioned('../grand-campaign/',revision)}">Full campaign atlas</a><a class="secondary-action" href="{_versioned('../artifacts/' + receipt_name,revision)}">Verification receipt</a></nav></div></header><main class="shell"><section class="family-grid" aria-label="Checked constructive proof families">{cards}</section><section class="release-note"><p>{_e(scope)}</p></section></main></body></html>'''.encode()
    for name, payload in tuple(files.items()):
        if name.endswith(".html"):
            files[name] = _portable_navigation(payload, package_slug)
    inventory = [{"path": name, "bytes": len(payload), "sha256": _digest(payload)} for name, payload in sorted(files.items())]
    files["manifest.json"] = _json({
        "schema": f"{inputs['schema']}-manifest", "catalog_sha256": inputs["catalog_sha256"],
        "first_enrollment_catalog_sha256": inputs["first_catalog_sha256"], "html_revision": revision,
        "edition_identity_sha256": inputs["current_edition_identity_sha256"],
        "alpha_edition_version": "v28", "alpha_first_enrolled_version": inputs["first_version"],
        "proof_bundle_sha256": inputs["bundle"]["artifact_sha256"], "independent_lean_bundle_verified": True,
        "inherited_revised_audit_sources": inputs["inherited_revised_audit_sources"],
        "theorem_count": sum(corpus["node_count"] for _, corpus in built),
        "checked_use_count": sum(corpus["node_count"] for _, corpus in built), "stable_count": 0,
        "families": [{"slug": family.slug, "campaign": family.campaign, "domain": family.domain,
                      "family": family.family_id, "milestones": list(family.milestones),
                      "theorem_count": corpus["node_count"], "definition_count": corpus["definition_count"],
                      "root_tags": {name: corpus["tags"][name] for name in family.roots}}
                     for family, corpus in built],
        "file_count": len(inventory), "inventory_sha256": _digest(_json(inventory)), "files": inventory,
    })
    return files


def build_files() -> dict[str, bytes]:
    inputs = _load_inputs()
    return render_files(
        inputs, FAMILIES, package_slug="constructive-lower-layer-explorer",
        title="Constructive lower-layer foundations",
        lede=f"{len(inputs['frontier'])} independently closed theorems connecting arithmetic, prime enumeration, and two quadratic integer rings.",
        scope="Nine exact blueprint targets have checked endpoints. The broad blueprint remains a research program: totient products, finite-field factorization, quadratic-ring gcd and prime classification, and stronger lattice theorems are not automatically closed.",
        receipt_name="alpha-v28-lower-layer-receipt.md",
    )


def write_or_check(files: dict[str, bytes], output: Path, *, check: bool) -> None:
    if check:
        actual = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        if actual != set(files) or any((output / name).read_bytes() != data for name, data in files.items()):
            raise LowerLayerExplorerError("the deterministic explorer snapshot is stale")
    else:
        for name, data in files.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            if not path.exists() or path.read_bytes() != data:
                path.write_bytes(data)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        files = build_files()
        write_or_check(files, arguments.output, check=arguments.check)
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as error:
        print(f"lower-layer explorer: FAIL: {error}", file=sys.stderr)
        return 1
    print(f"lower-layer explorer: PASS ({len(files)} deterministic files; no publication)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
