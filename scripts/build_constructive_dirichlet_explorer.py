#!/usr/bin/env python3
"""Canonical local explorers for actual Dirichlet convolution and Möbius inversion.

The rendering recipe follows the frozen lower-tier generator. Its original
QR-model local renderer and all five assets are reused without patching any
historical globals, renderer, source, registry, or generated snapshot. Actual
new proof checks precede every verified label; the three earlier non-admitted
generations remain separate from Alpha and from the new-theorem inventory.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import gc
from importlib import import_module
import json
import os
from pathlib import Path, PurePosixPath
import re
import resource
import secrets
import selectors
import signal
import sys
from tempfile import TemporaryDirectory
import time
from typing import Any

import build_constructive_bottom_layer_explorer as model
import build_constructive_lower_continuation_explorer as prior_model
import check_constructive_dirichlet as audit
import constructive_bottom_layer_checkpoints as bottom
import constructive_lower_tier_checkpoints as lower
import constructive_bottom_layer_explorer_renderer as render
import constructive_dirichlet_checkpoints as checkpoints
from constructive_dirichlet_definitions import DIRICHLET_REGISTRIES, definition_closure
from constructive_dirichlet_support import SupportSelection, previous_rows, select_support
from constructive_formula_compactor import _FormulaCompactor
from peano_lab.engine.state import proof_metrics
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.bertrand_defined_edition import ALL_BERTRAND_DEFINITIONS
from peano_lab.library.proof_bundle import ProofBundle, decode_proof_bundle
from peano_lab.library.theorems import TheoremSpec


ROOT = model.ROOT
OUTPUT = ROOT / "book/_static/constructive-dirichlet-explorer"
SCHEMA = "peano-lab-local-dirichlet-proof-explorers-v1"
HTML_REVISION = model.HTML_REVISION
ASSET_DIGESTS = model.ASSET_DIGESTS
ExplorerError, Family = model.BottomLayerExplorerError, model.Family
_digest, _json = model._digest, model._json
EXPECTED_FAMILIES = ("finite-support", "dirichlet-convolution", "dirichlet-fubini", "dirichlet-units", "mobius-inversion")
COMPANION_RFCS = {
    "dirichlet-convolution": ("research/arithmetic-library/dirichlet-commutativity-rfc-v1.md",),
}
RENDER_SCHEMA = "peano-lab-dirichlet-fresh-render-v1"
RENDER_WALL_SECONDS = audit.WALL_SECONDS
RENDER_TIMEOUT_SECONDS = audit.PARENT_TIMEOUT_SECONDS
MAX_RENDER_MESSAGE_BYTES = audit.MAX_STDERR_BYTES
MAX_RENDER_FILES = closure.DEFAULT_BUNDLE_LIMITS.max_nodes
CONTROLLER_WALL_SECONDS = audit.CONTROLLER_WALL_SECONDS + RENDER_TIMEOUT_SECONDS


class RenderProcessError(ExplorerError):
    """The fresh pure-render child or its bounded result failed closed."""


@dataclass(frozen=True, slots=True)
class _RenderResult:
    files: dict[str, bytes]
    peak_rss_bytes: int
RENDER_SOURCES = (
    "scripts/build_constructive_dirichlet_explorer.py",
    "scripts/constructive_dirichlet_definitions.py",
    "scripts/constructive_dirichlet_definition_graph.py",
    "scripts/constructive_dirichlet_defined_adapter.py",
    "scripts/build_constructive_bottom_layer_explorer.py",
    "scripts/constructive_bottom_layer_explorer_renderer.py",
    "scripts/build_constructive_lower_continuation_explorer.py",
    "scripts/constructive_formula_compactor.py",
)
IMMUTABLE_PRESENTATION_INPUTS = (
    "artifacts/peano-library/alpha/catalog-v30.json",
    "book/_static/constructive-bottom-layer-explorer/manifest.json",
    "book/_static/constructive-bottom-layer-publication/manifest.json",
    "book/_static/constructive-lower-tier-explorer/manifest.json",
    "book/_static/constructive-lower-tier-publication/manifest.json",
    "scripts/build_constructive_bottom_layer_explorer.py",
    "scripts/constructive_bottom_layer_explorer_renderer.py",
    "scripts/build_constructive_lower_tier_explorer.py",
    "scripts/build_constructive_lower_continuation_explorer.py",
    "book/_static/constructive-lower-continuation-explorer/manifest.json",
    "book/_static/constructive-gaussian-campaign/campaign.json",
    "book/_static/constructive-gaussian-campaign/definitions.json",
    "book/_static/constructive-gaussian-campaign/index.html",
)


@dataclass(frozen=True, slots=True)
class _FreshRenderEvidence:
    """Pure display projection of this build's authenticated fresh workers.

    This is deliberately not a CheckedProofBundle or a new kernel receipt.
    Its report came from the live nonce-bound audit; decoding the same pinned
    bytes supplies display syntax and metrics, not a second proof authority.
    """

    checkpoint: checkpoints.Checkpoint
    selection: SupportSelection
    bundle: ProofBundle
    report: dict[str, Any]

    @property
    def owned(self):
        return self.selection.owned

    @property
    def plan(self):
        return self.selection.plan


def _render_binding() -> str:
    sources = [(relative, _digest(model._bounded_source(ROOT / relative)))
               for relative in (*RENDER_SOURCES, *(item.rfc for item in checkpoints.CHECKPOINTS),
                                *(relative for paths in COMPANION_RFCS.values() for relative in paths))]
    assets = [(name, _digest(payload)) for name, payload in sorted(model._assets().items())]
    return _digest(audit._canonical({"proof_inputs": audit._binding(), "render_sources": sources, "assets": assets}))


def _fresh_projection(checkpoint, report, cached) -> _FreshRenderEvidence:
    """Project a fresh verified report; never load or accept a saved receipt."""
    if (type(cached) is not tuple or len(cached) != 2
            or type(cached[0]) is not SupportSelection or type(cached[1]) is not bytes):
        raise ExplorerError("a fresh audit syntax projection is missing")
    selected, expected_bytes = cached
    expected = audit._decode_message(expected_bytes)  # Original metadata, not acceptance.
    expected["principal_roots"] = [{**row, "complete_ordinary_ha_checked": True}
                                   for row in expected["principal_roots"]]
    audit._validate_report(report, expected, family=True)
    if (closure._specs_digest(selected.owned) != checkpoint.frontier_specs_sha256
            or closure._specs_digest(selected.frontier) != report["complete_non_alpha_specs_sha256"]
            or selected.plan.frontier_specs_sha256 != report["complete_non_alpha_specs_sha256"]):
        raise ExplorerError("the retained source-bound syntax changed before display")
    payload = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
    bundle, _ = decode_proof_bundle(payload.decode("utf-8"))
    return _FreshRenderEvidence(checkpoint, selected, bundle, json.loads(audit._canonical(report)))


def _validate_fresh_audit(report) -> None:
    if (type(report) is not dict or type(report.get("checkpoints")) is not list
            or report.get("full_G007_inversion_proved") is not True):
        raise ExplorerError("rendering requires the complete fresh audit and actual full G007 roots")
    try:
        expected = checkpoints._aggregate_reports(report["checkpoints"])
    except (KeyError, TypeError, ValueError) as error:
        raise ExplorerError("the fresh audit inventory is malformed") from error
    if audit._canonical(report) != audit._canonical(expected):
        raise ExplorerError("the fresh audit scope or inventory changed before rendering")


def _immutable_test_state():
    return ({relative: _digest((ROOT / relative).read_bytes()) for relative in IMMUTABLE_PRESENTATION_INPUTS},
            (model.OUTPUT, model.FAMILIES, prior_model.OUTPUT, bottom.CHECKPOINTS, lower.CHECKPOINTS))


def _assert_snapshot_binding(files) -> str:
    inventory = json.loads(files["checkpoints.json"])
    binding = inventory["render_source_binding_sha256"]
    if _render_binding() != binding:
        raise ExplorerError("proof or presentation sources changed after the fresh build")
    return binding


@dataclass(frozen=True, slots=True, eq=False)
class _FreshSnapshotTests:
    """Only an in-memory handoff from this process's completed fresh build."""

    files: dict[str, bytes]
    binding: str
    immutable_before: tuple

    def pytest_configure(self, config):
        config._dirichlet_fresh_snapshot = self


def _run_snapshot_tests(files, immutable_before) -> int:
    import pytest
    binding = _assert_snapshot_binding(files)
    plugin = _FreshSnapshotTests(files, binding, immutable_before)
    return int(pytest.main(["-q", str(ROOT / "peano-lab/py/tests/test_constructive_dirichlet_explorer.py")], plugins=[plugin]))


def families() -> tuple[Family, ...]:
    by_slug = {item.slug: item for item in checkpoints.CHECKPOINTS}
    if (tuple((item.slug, item.frontier_count) for item in checkpoints.CHECKPOINTS) != checkpoints.EXPECTED_INVENTORY
            or tuple(by_slug) != EXPECTED_FAMILIES):
        raise ExplorerError("all five exact Dirichlet checkpoints must be frozen before rendering")
    def family(slug, prefix, title, subtitle, description, statement, goals, definitions, caveat, scope):
        return Family(slug, prefix, title, subtitle, description, statement, "D01", "F01", goals,
                      by_slug[slug].principal_roots, slug, definitions, caveat, scope)
    return (
        family("finite-support", "ZS", "Actual signed finite support",
            "Half-open zero windows · constructed folds · exact padding",
            "Prove that a genuine zero tail does not alter an actual finite signed sum.",
            "Le(k,l) ∧ SignedZeroWindow(F,k,l) ∧ SignedPrefixSum(F,k,a) ∧ SignedPrefixSum(F,l,b) ⇒ a=b",
            ("G007",), ("ArithTable", "SignedPrefixSum", "SignedAdd"),
            "The zero window is half-open and its order hypothesis is essential. All folds retain actual beta-coded traces. These are support lemmas for the separately verified full inversion endpoint.",
            "actual_finite_support_foundation_for_G007"),
        family("dirichlet-convolution", "DC", "Constructed Dirichlet convolution",
            "Actual quotients · finite product tables · commutativity",
            "Construct finite signed convolution tables and prove positive-value uniqueness, commutativity and zero padding.",
            "ArithTable(N,F) ∧ ArithTable(N,G) ⇒ ∃H. DirichletTable(N,F,G,H)",
            ("G009",), ("ArithTableEqual", "ArithPositiveEqual", "DivisorComplementPrefix", "PermutationPrefix", "ArithReindex", "SignedZeroWindow"),
            "Each retained summand has a witnessed n=d*q and actual signed multiplication. Zero and nondivisors contribute zero. Input and output zero values remain unrestricted; only positive represented values are unique. Full G009 also requires the general inverse criterion and multiplicative-function closure.",
            "actual_convolution_construction_and_commutativity_full_G009_open"),
        family("dirichlet-fubini", "DF", "Finite convolution associativity",
            "Constructed factor grids · row and column sums · true Fubini",
            "Build actual first/last-factor grids and prove that both convolution parenthesizations agree.",
            "DirichletTable(N,F,G,A) ∧ DirichletTable(N,G,H,B) ∧ DirichletTable(N,A,H,L) ∧ DirichletTable(N,F,B,R) ⇒ ArithPositiveEqual(L,R,N)",
            ("G009", "G007"), ("DirichletPrefix", "DirichletSum", "DirichletTable", "SignedZeroWindow", "ArithSlice", "SignedSliceSum", "ArithRowSums", "SignedRectangularSum", "ArithScale", "ArithPositiveEqual"),
            "Every grid, slice, row sum and intermediate table is constructed. Retained cells have witnessed n=(a*e)*c and value F(a)*(H(e)*G(c)). The flat endpoint is unused. Table associativity includes N=0 and compares only positive values, not encodings. Full G009 remains broader.",
            "actual_constructive_finite_associativity_full_G009_open"),
        family("dirichlet-units", "DU", "One and delta convolution tables",
            "Arbitrary zeroth values · actual constructors · divisor sums",
            "Construct one and delta tables and prove the actual two-sided unit and divisor-sum identities.",
            "ArithTable(N,F) ∧ KroneckerDeltaTable(N,E) ⇒ DirichletTable(N,F,E,F) ∧ DirichletTable(N,E,F,F)",
            ("G009", "G007"), ("DirichletEntry", "DirichletPrefix", "DirichletSum", "DirichletTable", "DivisorMask", "DivisorSum", "ArithPositiveEqual", "SignedZeroWindow"),
            "Signed one is canonical code 2. Positive-only table graphs preserve arbitrary zeroth values, including N=0. The unit and divisor-sum identities are proved separately, never embedded as assumptions in the definitions. The arbitrary-unit inverse criterion of G009 remains open.",
            "actual_one_delta_constructions_and_unit_laws_full_G009_open"),
        family("mobius-inversion", "MI", "Full finite signed Möbius inversion",
            "Constructed Möbius witnesses · weighted divisor folds · forward and reverse",
            "Recover every original positive value from its divisor transform using actual finite Möbius-weighted sums.",
            "ArithTable(N,F) ∧ ArithTable(N,G) ∧ DivisorTransform(N,F,G) ⇒ ∃M H. MobiusTable(N,M) ∧ DirichletTable(N,M,G,H) ∧ ArithPositiveEqual(H,F,N)",
            ("G007",), ("MobiusTable", "ConstantOneTable", "KroneckerDeltaTable", "DirichletSum", "DirichletTable", "ArithPositiveEqual"),
            "Full finite signed G007 is proved locally, including the reverse equivalence and actual witnesses at N=0. The transform hypothesis covers every required positive quotient. F(0), G(0) and H(0) are unrestricted; only the historical Möbius witness keeps its separate zero convention. Alpha/Stable membership and the published atlas are unchanged. Full G009 and G091 remain open.",
            "full_G007_finite_signed_mobius_inversion_locally_proved"),
    )


def _checkpoint(family: Family) -> checkpoints.Checkpoint:
    return next(item for item in checkpoints.CHECKPOINTS if item.slug == family.slug)


def _definition_records(specs) -> list[dict[str, Any]]:
    by_name, by_id, records = {item.name: item for item in specs}, {}, []
    for item in specs:
        dependencies = [by_name[name].stable_id for name in item.conceptual_dependencies]
        if not set(dependencies) <= by_id.keys():
            raise ExplorerError("definition dependencies are not a genuine acyclic prefix")
        transitive = set(dependencies)
        for identifier in dependencies:
            transitive.update(by_id[identifier]["transitive_dependencies"])
        expansion = _FormulaCompactor(definition_closure(item.conceptual_dependencies)).compact(item.template_source)
        record = {
            "id": item.stable_id, "name": item.name, "parameters": list(item.parameters),
            "arity": item.arity, "signature": f"{item.name}({','.join(item.parameters)})",
            "summary": item.summary, "expanded_template": item.template_source,
            "expansion_sha256": _digest(item.template_source),
            "defined_template": expansion["defined_statement"], "defined_template_parts": expansion["statement_parts"],
            "dependencies": dependencies, "dependency_names": list(item.conceptual_dependencies),
            "topological_layer": max((by_id[name]["topological_layer"] + 1 for name in dependencies), default=0),
            "transitive_dependencies": sorted(transitive),
            "origin": "shared-hygienic-conservative-definition-not-proof-authority",
            "reviewed_definition_id": item.stable_id, "shared_definition_identity": item.stable_id,
            "global_definition": None, "global_argument_positions": None,
            "exact_ast_verified": True, "kernel_signature_unchanged": True,
        }
        records.append(record)
        by_id[item.stable_id] = record
    return records


def theorem_routes() -> dict[str, str]:
    """Preserve exact tags and published/local provenance of prior families."""
    routes = {}
    for family in families():
        rows = checkpoints.load_rows(_checkpoint(family))
        routes.update({name: f"{family.slug}/explorer/defined/tag/{tag}.html"
                       for name, tag in model._tags(family, rows).items()})
    for name, route in prior_model.theorem_routes().items():
        routes[name] = route if route.startswith("../") else "../constructive-lower-continuation-explorer/" + route
    return routes


def family_corpus(family: Family, evidence: _FreshRenderEvidence, *, table=None, routes=None) -> dict[str, Any]:
    if (type(evidence) is not _FreshRenderEvidence
            or evidence.checkpoint != _checkpoint(family)
            or evidence.report.get("membership") != "local_non_admitting_checkpoint"
            or any(evidence.report.get(key) is not False for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"))
            or evidence.report.get("bundle", {}).get("original_ha_checked") is not True
            or evidence.report.get("bundle", {}).get("independent_lean_checked") is not True):
        raise ExplorerError("the renderer received no genuine Dirichlet proof-check result")
    checkpoint = evidence.checkpoint
    roots = evidence.report.get("principal_roots", [])
    if ([row.get("name") for row in roots] != list(checkpoint.principal_roots)
            or any(row.get("complete_ordinary_ha_checked") is not True
                   or type(row.get("ordinary_certificate_nodes")) is not int
                   or not 1 < row["ordinary_certificate_nodes"] <= closure.DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences
                   for row in roots)):
        raise ExplorerError("display requires every actual ordinary principal certificate, including full G007")
    owned_rows = [(pin, row) for pin in checkpoint.modules
                  for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec)]
    if tuple(row for _, row in owned_rows) != evidence.owned:
        raise ExplorerError("source factories changed after the complete proof checks")
    tags = model._tags(family, evidence.owned)
    if not set(family.roots) <= tags.keys():
        raise ExplorerError("a principal root is not a genuinely new owned theorem")
    positions = {row.name: row.node_id for row in evidence.plan.rows}
    vocabulary = tuple(item.name for route, items in DIRICHLET_REGISTRIES
                       if route == family.definition_route for item in items)
    definitions = definition_closure(tuple(dict.fromkeys((
        *(item.name for item in ALL_BERTRAND_DEFINITIONS), *family.extra_definitions, *vocabulary,
    ))))
    compactor, nodes = _FormulaCompactor(definitions), []
    for owner, row in owned_rows:
        reading = compactor.compact(row.statement)
        model._compact_script(row, compactor, reading)
        body_nodes, body_depth = proof_metrics(evidence.bundle.nodes[positions[row.name]].body)
        source = {"source_module": "peano_lab.library." + owner.module, "factory": owner.factory,
                  "source_sha256": owner.sha256, "statement_sha256": _digest(row.statement),
                  "script_sha256": _digest("\n".join(row.script) + "\n"), "selected": True}
        nodes.append({
            "id": tags[row.name], "name": row.name, "summary": row.summary,
            "statement": row.statement, "statement_sha256": source["statement_sha256"],
            "script": list(row.script), "dependencies": list(row.dependencies),
            "source_module": source["source_module"], "source_filename": owner.module + ".py",
            "factory": owner.factory, "sources": [source], "inventory_role": "new_owned_theorem",
            "status": render.STATUS, **model._local_flags(),
            "proof_bundle_node_id": positions[row.name], "proof_bundle_sha256": checkpoint.artifact_sha256,
            "body_proof_nodes": body_nodes, "body_proof_depth": body_depth,
            "campaign_milestone": family.milestones[-1], "defined": reading,
        })
    used_ids = {identifier for node in nodes for identifier in node["defined"]["definition_uses"]}
    displayed = definition_closure(tuple(item.name for item in definitions
                                         if item.stable_id in used_ids or item.name in (*vocabulary, *family.extra_definitions)))
    records = _definition_records(displayed)
    if table is None:
        table = {row.name: row for row in (*closure.parent_snapshot().specs, *previous_rows(), *checkpoints.all_new_rows())}
    if routes is None:
        routes = theorem_routes()
    external, external_routes = [], {}
    for name in sorted({name for row in evidence.owned for name in row.dependencies if name not in tags}):
        if name not in table or name not in positions:
            raise ExplorerError("an external prerequisite is absent from the actual closed cone")
        row, role = table[name], evidence.selection.role(name)
        admitted = role == "inherited_alpha_v30"
        external_routes[name] = routes.get(name, f"{family.slug}/checkpoint.html#theorem-{name}")
        external.append({
            "name": name, "inventory_role": role, "counted_as_new_owned_theorem": False,
            "evidence": "actual_inherited_body_freshly_checked_in_complete_bundle",
            "statement": row.statement, "statement_sha256": _digest(row.statement),
            "proof_bundle_node_id": positions[name], "parent_alpha_version": "v30" if admitted else None,
            "alpha_checked_use": admitted, "enrolled_in_alpha": admitted, "admitted_to_alpha": admitted,
            "reference_route": external_routes[name],
        })
    layers, paths, adjacency = {}, {}, {}
    for node in nodes:
        internal = [name for name in node["dependencies"] if name in tags]
        if not set(internal) <= layers.keys():
            raise ExplorerError("a theorem dependency is cyclic or forward")
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
    definition_edges = [{"kind": "definition_uses_definition", "source": row["id"], "target": dependency}
                        for row in records for dependency in row["dependencies"]]
    return {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", **model._local_flags(),
        "family_slug": family.slug, "family_title": family.title,
        "campaign_domain_id": family.domain, "campaign_family_id": family.family_id,
        "campaign_goal_id": family.milestones[-1], "campaign_milestone_ids": list(family.milestones),
        "campaign_goal_scope": family.goal_scope, "published_atlas_changed": False,
        "root_names": list(family.roots), "nodes": nodes, "definitions": records,
        "external_dependencies": external, "external_theorem_routes": external_routes,
        "edges": proof_edges + usage_edges + definition_edges,
        "node_count": len(nodes), "new_theorem_count": len(nodes),
        "edge_count": sum(len(node["dependencies"]) for node in nodes),
        "internal_edge_count": len(proof_edges), "external_dependency_count": len(external),
        "definition_count": len(records), "definition_dependency_count": len(definition_edges),
        "definition_layer_count": max((row["topological_layer"] + 1 for row in records), default=0),
        "definition_topological_order": [row["id"] for row in records],
        "formal_line_count": sum(len(node["script"]) for node in nodes), "candidate_status": render.STATUS,
        "proof_bundle_sha256": checkpoint.artifact_sha256,
        "proof_bundle_node_count": evidence.report["bundle"]["nodes_including_packaging_root"],
        "render_evidence_provenance": "projection_of_fresh_nonce_authenticated_workers_and_exact_pinned_proof_data",
        "checkpoint_report": evidence.report,
        "local_checkpoint_verified_node_count": len(nodes), "alpha_enrolled_node_count": 0,
        "alpha_checked_use_node_count": 0, "stable_admitted_node_count": 0,
        "parent_alpha_edition_version": "v30", "parent_alpha_checked_use_count": 3222,
        "parent_stable_count": 432, "parent_alpha_catalog_sha256": closure.PARENT_CATALOG_SHA256,
        "previous_research_generations": [170, 126, 125],
        "navigation_revision": HTML_REVISION, "reserved_tag_slots": {},
        "tags": tags, "layers": layers, "proof_adjacency": adjacency,
        "proof_paths": {tags[name]: path for name, path in paths.items()},
        "path_policy": "proof_dependency_edges_only",
    }


def checkpoint_page(family: Family, corpus: Mapping[str, Any]) -> bytes:
    report = corpus["checkpoint_report"]
    sources = "".join(
        f'<li><a href="{render._versioned("../sources/" + Path(row["path"]).name, HTML_REVISION)}">{render._e(row["path"])}</a> · <code>{row["sha256"]}</code></li>'
        for row in report["sources"])
    theorem_rows = []
    for node in (*corpus["nodes"], *corpus["external_dependencies"]):
        own = node["name"] in corpus["tags"]
        route = ("explorer/defined/tag/" + corpus["tags"][node["name"]] + ".html"
                 if own else "../" + node["reference_route"])
        label = node["inventory_role"].replace("_", " ")
        theorem_rows.append(
            f'<article class="view-card" id="theorem-{node["name"]}"><h3>{render._e(node["name"])}</h3>'
            f'<p>{render._e(label)} · <a href="{render._versioned(route, HTML_REVISION)}">read exact theorem evidence</a></p>'
            f'<p>Bundle node {node["proof_bundle_node_id"]}; exact statement SHA-256 <code>{node["statement_sha256"]}</code></p>'
            f'<details><summary>Exact first-order statement</summary><pre>{render._e(node["statement"])}</pre></details></article>')
    bundle_href = render._versioned("../checkpoints/" + Path(report["bundle"]["path"]).name, HTML_REVISION)
    support = report["support"]
    companion_links = "".join(
        f'<p><a href="{render._versioned("../sources/" + Path(relative).name, HTML_REVISION)}">Companion commutativity and padding RFC</a></p>'
        for relative in COMPANION_RFCS.get(family.slug, ()))
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned('./', HTML_REVISION)}">{render._e(family.title)}</a><span>/</span><a href="{render._versioned('../grand-campaign/', HTML_REVISION)}">Local checkpoint map</a></nav><h1>Exact local checkpoint receipt</h1><p class="lede">{render._e(render._status(corpus))}</p></div></header>
<main class="shell family-main"><section class="release-note"><strong>Actual complete proof evidence:</strong> {report['bundle']['nodes_including_packaging_root']} original-HA and independently compiled Lean-checked nodes. <a href="{bundle_href}">Download literal proof bundle</a>; {report['bundle']['bytes']} bytes; SHA-256 <code>{report['bundle']['sha256']}</code>.</section>
<section class="release-note"><strong>Exact inventory roles:</strong> {report['new_theorem_count']} new owned theorems, {support['prior_bottom_layer_count']} inherited prerequisites from the first 170 research theorems, {support['prior_lower_tier_count']} from the later published 126, {support['prior_lower_continuation_count']} from the previous local 125, {support['current_cross_track_count']} current cross-track prerequisites and {support['alpha_v30_count']} inherited Alpha theorems. Support rows are not recounted as new. Source-helper imports are not proof premises. Alpha v30 remains 3222; Stable remains 432. This page claims complete bundle checks, not ordinary-certificate replay for every theorem. <a href="{render._versioned('api/checkpoint.json', HTML_REVISION)}">Machine-readable report</a>.</section>
<section class="release-note"><strong>Mathematical boundary:</strong> {render._e(family.caveat)}</section>
<section><h2>Frozen authoring sources</h2><ul>{sources}</ul><p><a href="{render._versioned('../sources/' + Path(report['rfc']).name, HTML_REVISION)}">Exact campaign RFC</a></p>{companion_links}</section>
<section><h2>New results and actual inherited prerequisites</h2>{''.join(theorem_rows)}</section></main>'''
    return model._simple_document("Exact local checkpoint — " + family.title, body, prefix="../")


def dispatch(corpora: list[dict[str, Any]], *, atlas: bool) -> bytes:
    prefix, historical_prefix = ("../", "../../") if atlas else ("", "../")
    cards = []
    for family, corpus in zip(families(), corpora, strict=True):
        goal = family.milestones[-1]
        href = render._versioned(prefix + family.slug + "/", HTML_REVISION)
        graph = render._versioned(prefix + family.slug + "/explorer/defined/graph.html?target=" + corpus["tags"][family.roots[-1]] + "&view=prerequisites&definitions=selected&edges=focus", HTML_REVISION)
        roadmap = render._versioned(historical_prefix + "constructive-gaussian-campaign/?view=goal&focus=" + goal, HTML_REVISION)
        cards.append(f'''<article class="view-card" id="{family.slug}" data-local-family="{family.family_id}" data-local-domain="{family.domain}" data-local-goal="{goal}" data-local-goals="{render._e(" ".join(family.milestones))}"><p class="card-kicker">{goal} · {family.family_id}</p><h2>{render._e(family.title)}</h2><p>{render._e(family.description)}</p><p>{corpus['node_count']} genuinely new local theorems · {corpus['definition_count']} conservative definitions</p><a href="{href}">Enter proof family →</a><p><a href="{graph}">Explore actual proof and definition dependencies →</a></p><p><a href="{roadmap}">View unchanged {goal} campaign roadmap →</a></p><p>{render._e(family.caveat)}</p></article>''')
    bottom_href = render._versioned(historical_prefix + "constructive-bottom-layer-explorer/", HTML_REVISION)
    lower_href = render._versioned(historical_prefix + "constructive-lower-tier-explorer/", HTML_REVISION)
    continuation_href = render._versioned(historical_prefix + "constructive-lower-continuation-explorer/", HTML_REVISION)
    atlas_href = render._versioned(historical_prefix + "constructive-gaussian-campaign/", HTML_REVISION)
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned(prefix or './', HTML_REVISION)}">Local Dirichlet checkpoints</a><span>/</span><a href="{bottom_href}">First 170 research proofs</a><span>/</span><a href="{lower_href}">Next 126 research proofs</a><span>/</span><a href="{continuation_href}">Previous 125 local proofs</a><span>/</span><a href="{atlas_href}">Full campaign blueprint</a></nav><p class="eyebrow">Constructive arithmetic · local development</p><h1>Dirichlet convolution and Möbius inversion</h1><p class="lede">Five actual proof checkpoints, connected to all three earlier research generations and the larger campaign. This local map neither changes the published atlas nor grants Alpha membership.</p></div></header><main class="shell family-main"><section class="view-grid">{''.join(cards)}</section><section class="release-note"><strong>Evidence boundary:</strong> {sum(corpus['node_count'] for corpus in corpora)} distinct new theorems, excluding inherited research and Alpha support. The earlier research generations contain 170 and 126 published theorems, followed by 125 local theorems. Alpha v30 remains 3222; Stable remains 432. Full finite signed G007 inversion is proved locally. The full G009 inverse criterion and general G091 prime-power fields remain open. <a href="{render._versioned(prefix + 'checkpoints.json', HTML_REVISION)}">Exact checkpoint inventory</a>.</section></main>'''
    body += '''<script>
(function () {
  "use strict";
  var query = new URL(window.location.href).searchParams;
  var field = {family: "data-local-family", domain: "data-local-domain", goal: "data-local-goal"}[query.get("view")];
  var focus = query.get("focus");
  var cards = Array.from(document.querySelectorAll("[data-local-family]"));
  function matches(card) {
    var values = field === "data-local-goal" ? card.getAttribute("data-local-goals").split(" ") : [card.getAttribute(field)];
    return values.indexOf(focus) !== -1;
  }
  if (!field || !focus || !cards.some(matches)) return;
  cards.forEach(function (card) { card.hidden = !matches(card); });
})();
</script>'''
    return model._simple_document("Local Dirichlet proof checkpoints", body, prefix=prefix)


def _render_files(fresh_report, syntax, binding) -> dict[str, bytes]:
    """Pure formatting of this live run's reports and retained theorem syntax."""
    selected_families = families()  # Incomplete registries never reach a proof label.
    _validate_fresh_audit(fresh_report)
    if type(syntax) is not dict or tuple(syntax) != EXPECTED_FAMILIES:
        raise ExplorerError("all five freshly retained syntax projections are required")
    if _render_binding() != binding:
        raise ExplorerError("proof or presentation sources changed during the fresh audit")
    reports = {item["slug"]: item for item in fresh_report["checkpoints"]}
    files, corpora = model._assets(), []
    table = {row.name: row for row in (*closure.parent_snapshot().specs, *previous_rows(), *checkpoints.all_new_rows())}
    routes = theorem_routes()
    for family in selected_families:
        checkpoint = _checkpoint(family)
        evidence = _fresh_projection(checkpoint, reports[family.slug], syntax[family.slug])
        corpus = family_corpus(family, evidence, table=table, routes=routes)
        corpora.append(corpus)
        graph = render.graph_payload(family, corpus, revision=HTML_REVISION)
        base = family.slug + "/"
        files[base + "index.html"] = render.render_local_family_landing(family, corpus, revision=HTML_REVISION,
            bundle_node_count=evidence.report["bundle"]["nodes_including_packaging_root"])
        files[base + "checkpoint.html"] = checkpoint_page(family, corpus)
        files[base + "api/corpus.json"] = _json(corpus)
        files[base + "api/graph.json"] = files[base + "explorer/defined/api/graph.json"] = _json(graph)
        files[base + "api/checkpoint.json"] = _json(evidence.report)
        files[base + "explorer/index.html"] = render.render_exact_index(
            family, corpus, corpus["tags"], corpus["layers"],
            stylesheet_href="../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
            script_href="../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=HTML_REVISION)
        files[base + "explorer/defined/index.html"] = render.render_defined_index(family, corpus, revision=HTML_REVISION)
        files[base + "explorer/defined/graph.html"] = render.render_defined_graph(family, corpus, graph, revision=HTML_REVISION)
        for node in corpus["nodes"]:
            tag = corpus["tags"][node["name"]]
            files[base + f"explorer/tag/{tag}.html"] = render.render_exact_theorem(
                family, corpus, node, corpus["tags"], corpus["layers"],
                stylesheet_href="../../../assets/exact-explorer.css?v=" + ASSET_DIGESTS["exact-explorer.css"][:12],
                script_href="../../../assets/exact-explorer.js?v=" + ASSET_DIGESTS["exact-explorer.js"][:12], html_revision=HTML_REVISION)
            files[base + f"explorer/defined/tag/{tag}.html"] = render.render_defined_theorem(family, corpus, node, revision=HTML_REVISION)
        for definition in corpus["definitions"]:
            files[base + f"explorer/defined/definition/{definition['id']}.html"] = render.render_defined_definition(family, corpus, definition, revision=HTML_REVISION)
        files["checkpoints/" + Path(checkpoint.artifact).name] = closure._read_pinned(ROOT / checkpoint.artifact, checkpoint.artifact_bytes, checkpoint.artifact_sha256)
        for pin in checkpoint.modules:
            files["sources/" + Path(pin.path).name] = bottom._source_bytes(pin)
        files["sources/" + Path(checkpoint.rfc).name] = model._bounded_source(ROOT / checkpoint.rfc)
        for relative in COMPANION_RFCS.get(family.slug, ()):
            files["sources/" + Path(relative).name] = model._bounded_source(ROOT / relative)
        del evidence
        gc.collect()
    inventory = {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "navigation_revision": HTML_REVISION, "new_theorems": sum(corpus["node_count"] for corpus in corpora),
        "previous_research_theorems": 421, "previous_research_generations": [170, 126, 125],
        "prior_theorem_count_for_exact_ast_novelty_check": 3643,
        "inherited_support_counted_as_new": False,
        "statement_asts_distinct_from_all_3643_prior_and_each_other": True,
        "render_source_binding_sha256": binding,
        "full_G007_inversion_proved": True, "full_G009_dirichlet_convolution_theory_proved": False, "general_G091_prime_power_fields_proved": False,
        "parent": {"alpha_version": "v30", "alpha_checked_use_count": 3222, "stable_count": 432,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256},
        "independent_checker": {"binary_sha256": checkpoints.LEAN_BINARY_SHA256},
        "checkpoints": [corpus["checkpoint_report"] for corpus in corpora],
    }
    inventory["checkpoint_digest"] = _digest(_json(inventory))
    files["checkpoints.json"] = _json(inventory)
    files["proof-audit.json"] = audit.canonical_report(fresh_report).encode("utf-8")
    files["index.html"], files["grand-campaign/index.html"] = dispatch(corpora, atlas=False), dispatch(corpora, atlas=True)
    files["manifest.json"] = _json({
        "schema": SCHEMA + "-manifest", "publication_scope": "local-only-checkpoint",
        "checkpoint_digest": inventory["checkpoint_digest"], "navigation_revision": HTML_REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {path: {"bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())},
    })
    if _render_binding() != binding:
        raise ExplorerError("proof or presentation sources changed while formatting the snapshot")
    return files


def _validate_render_message(payload, *, nonce, binding, report, check, test, write_audit):
    if (any(type(flag) is not bool for flag in (check, test, write_audit))
            or type(nonce) is not str or re.fullmatch(r"[0-9a-f]{64}", nonce) is None
            or type(binding) is not str or re.fullmatch(r"[0-9a-f]{64}", binding) is None):
        raise RenderProcessError("invalid expected render identity or options")
    if type(payload) is not bytes or not 0 < len(payload) <= MAX_RENDER_MESSAGE_BYTES:
        raise RenderProcessError("render result is missing or exceeds its unchanged message bound")
    value = audit._decode_message(payload)
    keys = {"schema", "nonce", "binding_sha256", "limits", "peak_rss_bytes", "manifest", "proof_audit",
            "file_count", "check", "test", "write_audit", "pytest_status"}
    if set(value) != keys:
        raise RenderProcessError("render result fields changed")
    wanted = {"schema": RENDER_SCHEMA, "nonce": nonce, "binding_sha256": binding,
              "limits": {"cpu": list(audit.CPU_LIMITS), "wall_seconds": RENDER_WALL_SECONDS,
                         "max_rss_bytes": audit.MAX_RSS_BYTES},
              "check": check, "test": test, "write_audit": write_audit, "pytest_status": 0 if test else None}
    if audit._canonical({key: value[key] for key in wanted}) != audit._canonical(wanted):
        raise RenderProcessError("stale, foreign, or incorrectly limited render result")
    if type(value["peak_rss_bytes"]) is not int or not 0 < value["peak_rss_bytes"] <= audit.MAX_RSS_BYTES:
        raise RenderProcessError("render child exceeded the original RSS ceiling")
    if type(value["file_count"]) is not int or not 1 < value["file_count"] <= MAX_RENDER_FILES:
        raise RenderProcessError("render file count is not bounded")
    for key in ("manifest", "proof_audit"):
        item = value[key]
        if (type(item) is not dict or set(item) != {"bytes", "sha256"}
                or type(item["bytes"]) is not int or not 0 < item["bytes"] <= model.MAX_PRESENTATION_SOURCE_BYTES
                or type(item["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise RenderProcessError("render metadata size or digest changed")
    expected_audit = audit.canonical_report(report).encode("utf-8")
    if value["proof_audit"] != {"bytes": len(expected_audit), "sha256": _digest(expected_audit)}:
        raise RenderProcessError("render child did not return this live run's actual audit")
    return value


def _read_rendered_files(output, message):
    """Read literal fresh page bytes, never use them as mathematical authority."""
    from check_constructive_bottom_layers import authoring_rss_bytes
    output = Path(output)
    if output.is_symlink() or not output.is_dir():
        raise RenderProcessError("render destination is not a regular directory")
    if (output / "manifest.json").is_symlink():
        raise RenderProcessError("render manifest must not be a symlink")
    manifest_pin = message["manifest"]
    raw = closure._read_pinned(output / "manifest.json", manifest_pin["bytes"], manifest_pin["sha256"])
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise RenderProcessError("duplicate render manifest key")
            value[key] = item
        return value
    def constant(value):
        raise RenderProcessError("non-finite render manifest value")
    manifest = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    if raw != _json(manifest):
        raise RenderProcessError("render manifest is not in its exact canonical format")
    expected_keys = {"schema", "publication_scope", "checkpoint_digest", "navigation_revision", "file_count_excluding_manifest", "files"}
    if (type(manifest) is not dict or set(manifest) != expected_keys or manifest["schema"] != SCHEMA + "-manifest"
            or manifest["publication_scope"] != "local-only-checkpoint" or manifest["navigation_revision"] != HTML_REVISION
            or type(manifest["files"]) is not dict
            or type(manifest["file_count_excluding_manifest"]) is not int
            or manifest["file_count_excluding_manifest"] != len(manifest["files"])
            or len(manifest["files"]) + 1 != message["file_count"]):
        raise RenderProcessError("render manifest does not describe the exact fresh inventory")
    files, total = {"manifest.json": raw}, len(raw)
    for name, item in manifest["files"].items():
        path = PurePosixPath(name) if isinstance(name, str) else None
        if (path is None or not name or "\\" in name or "\x00" in name or path.is_absolute()
                or any(part in ("", ".", "..") for part in name.split("/")) or name == "manifest.json"
                or type(item) is not dict or set(item) != {"bytes", "sha256"}
                or type(item["bytes"]) is not int or not 0 <= item["bytes"] <= closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                or type(item["sha256"]) is not str or re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) is None):
            raise RenderProcessError("unsafe or unbounded render manifest entry")
        destination = output
        for part in path.parts:
            destination /= part
            if destination.is_symlink():
                raise RenderProcessError("rendered paths must not contain symlinks")
        total += item["bytes"]
        if total > audit.MAX_RSS_BYTES:
            raise RenderProcessError("rendered byte inventory exceeds the existing RSS ceiling")
        files[name] = closure._read_pinned(destination, item["bytes"], item["sha256"])
        authoring_rss_bytes()
    actual = set()
    for path in output.rglob("*"):
        if path.is_symlink() or not (path.is_dir() or path.is_file()):
            raise RenderProcessError("render directory contains a foreign filesystem entry")
        if path.is_file():
            actual.add(path.relative_to(output).as_posix())
            if len(actual) > MAX_RENDER_FILES:
                raise RenderProcessError("render directory exceeds the bounded file inventory")
    if actual != set(files):
        raise RenderProcessError("render directory differs from its fresh manifest")
    if "proof-audit.json" not in files or message["proof_audit"] != {
            "bytes": len(files["proof-audit.json"]), "sha256": _digest(files["proof-audit.json"])}:
        raise RenderProcessError("fresh rendered audit bytes changed")
    return files


def _render_child(report, syntax, binding, *, output, check, test, write_audit, immutable_before, nonce, write_fd):
    """Fork-only target: its actual report and syntax are inherited live RAM."""
    from check_constructive_bottom_layers import authoring_rss_bytes
    files = _render_files(report, syntax, binding)
    authoring_rss_bytes()
    model.write_or_check(files, output=output, check=check)
    authoring_rss_bytes()
    status = _run_snapshot_tests(files, immutable_before) if test else None
    if test and status != 0:
        raise RenderProcessError(f"the actual snapshot tests failed with status {status}")
    _assert_snapshot_binding(files)
    value = {"schema": RENDER_SCHEMA, "nonce": nonce, "binding_sha256": binding,
             "limits": {"cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": RENDER_WALL_SECONDS,
                        "max_rss_bytes": audit.MAX_RSS_BYTES},
             "peak_rss_bytes": authoring_rss_bytes(), "file_count": len(files),
             "manifest": {"bytes": len(files["manifest.json"]), "sha256": _digest(files["manifest.json"])},
             "proof_audit": {"bytes": len(files["proof-audit.json"]), "sha256": _digest(files["proof-audit.json"])},
             "check": check, "test": test, "write_audit": write_audit, "pytest_status": status}
    payload = audit._canonical(value)
    if len(payload) > MAX_RENDER_MESSAGE_BYTES:
        raise RenderProcessError("render result exceeds its bounded pipe")
    authoring_rss_bytes()
    with os.fdopen(write_fd, "wb", closefd=False) as stream:
        stream.write(payload)
        stream.flush()
    authoring_rss_bytes()


def _fork_render_phase(report, syntax, binding, *, output, check, test, write_audit, immutable_before):
    """One fresh pure-render window, without any receipt-file or render CLI."""
    if any(type(flag) is not bool for flag in (check, test, write_audit)):
        raise RenderProcessError("render options must be explicit Booleans")
    nonce = secrets.token_hex(32)
    read_fd, write_fd = os.pipe()
    sys.stdout.flush(); sys.stderr.flush()
    try:
        pid = os.fork()
    except BaseException:
        os.close(read_fd); os.close(write_fd)
        raise
    if pid == 0:
        status = 1
        os.close(read_fd)
        try:
            os.setsid()
            resource.setrlimit(resource.RLIMIT_CPU, audit.CPU_LIMITS)
            signal.alarm(RENDER_WALL_SECONDS)
            _render_child(report, syntax, binding, output=output, check=check, test=test, write_audit=write_audit,
                          immutable_before=immutable_before, nonce=nonce, write_fd=write_fd)
            status = 0
        except BaseException as error:
            print(f"Pure-render child failed: {type(error).__name__}: {str(error)[:1024]}", file=sys.stderr, flush=True)
        finally:
            os.close(write_fd)
            sys.stdout.flush(); sys.stderr.flush()
            os._exit(status)
    os.close(write_fd)
    output_bytes, child_status, eof, group_cleanup_attempted = bytearray(), None, False, False
    started = time.monotonic()
    deadline = started + RENDER_WALL_SECONDS
    overall_deadline = started + RENDER_TIMEOUT_SECONDS
    try:
        os.set_blocking(read_fd, False)
        with selectors.DefaultSelector() as selector:
            selector.register(read_fd, selectors.EVENT_READ)
            while not (child_status is not None and eof):
                if time.monotonic() >= deadline:
                    raise RenderProcessError("pure-render child exceeded its original bounded window")
                if selector.select(min(0.1, max(0, deadline - time.monotonic()))):
                    chunk = os.read(read_fd, MAX_RENDER_MESSAGE_BYTES - len(output_bytes) + 1)
                    if chunk:
                        output_bytes.extend(chunk)
                        if len(output_bytes) > MAX_RENDER_MESSAGE_BYTES:
                            raise RenderProcessError("pure-render child emitted an oversized result")
                    else:
                        eof = True
                        selector.unregister(read_fd)
                if child_status is None:
                    waited, status = os.waitpid(pid, os.WNOHANG)
                    if waited:
                        child_status = status
                        # macOS Python has no waitid/WNOWAIT API. Clean the
                        # owned group immediately on observing/reaping exit,
                        # before any parsing, file IO, or expensive binding.
                        group_cleanup_attempted = True
                        try: os.killpg(pid, signal.SIGKILL)
                        except ProcessLookupError: pass
                        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
                            raise RenderProcessError("pure-render child did not exit successfully")
        if time.monotonic() >= deadline:
            raise RenderProcessError("pure-render child finished after its original bounded window")
        message = _validate_render_message(bytes(output_bytes), nonce=nonce, binding=binding, report=report,
                                           check=check, test=test, write_audit=write_audit)
        files = _read_rendered_files(output, message)
        if _render_binding() != binding:
            raise RenderProcessError("sources changed across the fresh pure-render window")
        return _RenderResult(files, message["peak_rss_bytes"])
    finally:
        os.close(read_fd)
        # The child and all of its Node/test descendants own this group. Even
        # malformed output, timeout, signal, and early exit must clean it up.
        try:
            if not group_cleanup_attempted:
                if child_status is None:
                    # An unreaped PID is still ours. Kill it before the group so
                    # it cannot establish a fresh session after an ESRCH race.
                    try: os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError: pass
                group_cleanup_attempted = True
                try:
                    os.killpg(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        finally:
            # A denied group signal remains a failure; never retry or ignore
            # it. Still reap our exact leader after a successful PID stop.
            if child_status is None:
                cleanup_deadline = min(overall_deadline,
                    time.monotonic() + (RENDER_TIMEOUT_SECONDS - RENDER_WALL_SECONDS))
                while not os.waitpid(pid, os.WNOHANG)[0]:
                    if time.monotonic() >= cleanup_deadline:
                        raise RenderProcessError("the stopped render child could not be reaped within the cleanup bound")
                    time.sleep(0.01)


def _build_verified(*, output, check=False, test=False, write_audit=False):
    from check_constructive_bottom_layers import authoring_rss_bytes
    families()
    binding, syntax = _render_binding(), {}
    before = _immutable_test_state()
    def collect(checkpoint, selection, expected_bytes):
        if checkpoint.slug in syntax:
            raise ExplorerError("duplicate freshly retained syntax projection")
        syntax[checkpoint.slug] = (selection, expected_bytes)
    report, worker_peak = audit.verify_in_fresh_windows(syntax_collector=collect)
    _validate_fresh_audit(report)
    if type(worker_peak) is not int or not 0 < worker_peak <= audit.MAX_RSS_BYTES:
        raise ExplorerError("fresh proof workers exceeded the unchanged RSS ceiling")
    result = _fork_render_phase(report, syntax, binding, output=output, check=check, test=test,
                                write_audit=write_audit, immutable_before=before)
    authoring_rss_bytes()
    if write_audit:
        payload = audit.canonical_report(report).encode("utf-8")
        if result.files["proof-audit.json"] != payload:
            raise RenderProcessError("rendered audit differs from this actual live verification")
        audit.RECEIPT.parent.mkdir(parents=True, exist_ok=True)
        authoring_rss_bytes()
        with audit.RECEIPT.open("xb") as stream:
            stream.write(payload)
        authoring_rss_bytes()
    return result.files, worker_peak, result.peak_rss_bytes


def build_files() -> dict[str, bytes]:
    """Fresh checks and a private render window; never modify a saved snapshot."""
    with TemporaryDirectory(prefix="peano-dirichlet-render-") as directory:
        files, _, _ = _build_verified(output=Path(directory), check=False)
        return files


def main(argv: list[str] | None = None) -> int:
    import argparse
    from check_constructive_bottom_layers import authoring_rss_bytes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fresh HA/Lean checks and exact snapshot comparison")
    parser.add_argument("--test", action="store_true", help="test this same fresh in-memory snapshot, without repeating proof jobs")
    parser.add_argument("--write-audit", action="store_true", help="exclusively save this build's actual fresh audit at the fixed checkpoint receipt path")
    args = parser.parse_args(argv)
    if args.write_audit and (audit.RECEIPT.exists() or audit.RECEIPT.is_symlink()):
        parser.error("refusing to overwrite an existing checkpoint audit")
    resource.setrlimit(resource.RLIMIT_CPU, audit.CPU_LIMITS)
    signal.alarm(CONTROLLER_WALL_SECONDS)
    started = time.monotonic()
    files, worker_peak, render_peak = _build_verified(output=OUTPUT, check=args.check, test=args.test, write_audit=args.write_audit)
    peak = authoring_rss_bytes()
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} canonical local files; {sum(item.frontier_count for item in checkpoints.CHECKPOINTS)} genuinely new theorems; elapsed {time.monotonic()-started:.3f}s.")
    print(f"Peak RSS: proof workers {worker_peak}; pure-render child {render_peak}; controller {peak} bytes.")
    print("No Alpha/Stable admission or publication; all previous snapshots and the published atlas unchanged.")
    return 0


if __name__ == "__main__":
    # The optional pytest session must import this same module and its live
    # in-memory projection, not a second copy masquerading as a fresh build.
    sys.modules.setdefault("build_constructive_dirichlet_explorer", sys.modules[__name__])
    raise SystemExit(main())
