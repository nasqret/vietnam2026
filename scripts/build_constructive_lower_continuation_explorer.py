#!/usr/bin/env python3
"""Canonical local explorers for four new, non-admitted proof checkpoints.

The rendering recipe follows the frozen lower-tier generator. Its original
QR-model local renderer and all five assets are reused without patching any
historical globals, renderer, source, registry, or generated snapshot. Actual
new proof checks precede every verified label; the two earlier non-admitted
generations remain separate from Alpha and from the new-theorem inventory.
"""

from __future__ import annotations

from collections.abc import Mapping
import gc
from importlib import import_module
from pathlib import Path
import resource
import signal
from typing import Any

import build_constructive_bottom_layer_explorer as model
import build_constructive_lower_tier_explorer as prior_model
import constructive_bottom_layer_checkpoints as bottom
import constructive_lower_tier_checkpoints as lower
import constructive_bottom_layer_explorer_renderer as render
import constructive_lower_continuation_checkpoints as checkpoints
from constructive_lower_continuation_definitions import CONTINUATION_REGISTRIES, definition_closure
from constructive_lower_continuation_support import previous_rows, statement_duplicates
from constructive_formula_compactor import _FormulaCompactor
from peano_lab.engine.state import proof_metrics
from peano_lab.library import campaign_bottom_layer_closure as closure
from peano_lab.library.bertrand_defined_edition import ALL_BERTRAND_DEFINITIONS
from peano_lab.library.theorems import TheoremSpec


ROOT = model.ROOT
OUTPUT = ROOT / "book/_static/constructive-lower-continuation-explorer"
SCHEMA = "peano-lab-local-lower-continuation-proof-explorers-v1"
HTML_REVISION = model.HTML_REVISION
ASSET_DIGESTS = model.ASSET_DIGESTS
ExplorerError, Family = model.BottomLayerExplorerError, model.Family
_digest, _json = model._digest, model._json
EXPECTED_FAMILIES = ("divisor-involutions", "mobius-divisor-cancellation", "rectangular-sums", "polynomial-products")


def families() -> tuple[Family, ...]:
    by_slug = {item.slug: item for item in checkpoints.CHECKPOINTS}
    if len(by_slug) != len(checkpoints.CHECKPOINTS) or set(by_slug) != set(EXPECTED_FAMILIES):
        raise ExplorerError("all four exact continuation checkpoints must be frozen before rendering")
    return (
        Family(
            "divisor-involutions", "DI", "Complementary divisors and finite involutions",
            "Actual quotient witnesses · finite beta maps · reversible divisors",
            "Construct complementary positive divisors and their actual finite permutation, fixing zero and every nondivisor in the surrounding interval.",
            "n≠0 ⇒ ∃b c. DivisorComplementPrefix(n,b,c,S n) ∧ PermutationPrefix(b,c,S n)",
            "D01", "F01", ("G007",), by_slug["divisor-involutions"].principal_roots,
            "divisor-involutions", ("PermutationPrefix",),
            "The complementary quotient is witnessed by n=d*q at positive divisors. The actual permutation covers indices 0 through n, with zero and nondivisors fixed. This is an involution foundation, not Möbius inversion; full G007 remains open.",
            "actual_divisor_involution_subgoal_only_full_G007_open",
        ),
        Family(
            "mobius-divisor-cancellation", "MC", "Möbius divisor cancellation",
            "Constructed prime toggles · signed anti-invariance · the unit boundary",
            "Construct a prime-factor toggle and prove cancellation of the actual Möbius divisor sum, including the separate value at one and unrestricted input-table value at zero.",
            "n≠0 ⇒ ∃M z. MobiusTable(n,M) ∧ DivisorSum(M,n,z) ∧ ((n=1 ∧ z=2) ∨ (n≠1 ∧ z=0))",
            "D01", "F01", ("G007",), by_slug["mobius-divisor-cancellation"].principal_roots,
            "mobius-divisor-cancellation", ("MobiusTable", "DivisorSum", "DivisorMask", "PermutationPrefix", "ArithReindex", "ArithPositiveEqual"),
            "The input n is positive. Canonical signed code 2 denotes +1, so the sum is +1 at n=1 and zero for n>1. The positive-values theorem permits arbitrary F(0); the genuine divisor mask excludes it. Prime-square multiples contribute zero. This proves divisor cancellation, not the full Möbius inversion or convolution equivalence; full G007 remains open.",
            "actual_mobius_divisor_cancellation_only_full_G007_inversion_open",
        ),
        Family(
            "rectangular-sums", "RS", "Actual rectangular sums and finite Fubini",
            "Constructed slices · row and column tables · zero dimensions",
            "Construct actual signed affine slices and row-sum tables, then prove equality of row-first and column-first totals by ordinary finite induction.",
            "SignedRectangularSum(F,o,s,t,m,n,a) ∧ SignedRectangularSum(F,o,t,s,n,m,b) ⇒ a=b",
            "D01", "F01", ("G007",), by_slug["rectangular-sums"].principal_roots,
            "rectangular-sums", ("ArithTableEqual", "ArithAdd", "ArithExtend"),
            "Every slice, row table, column table and signed sum is an actual beta-coded witness. The grid entry is F((o+s*i)+t*j), for i<m and j<n. Both zero dimensions and zero strides are allowed; separately certified endpoints are unused. Table uniqueness concerns represented values, not encodings. This is finite signed Fubini, not an infinite-sum theorem or full G007 inversion.",
            "actual_finite_signed_fubini_only_full_G007_inversion_open",
        ),
        Family(
            "polynomial-products", "PC", "Canonical polynomial products and represented degree",
            "Actual antidiagonal sums · canonical residues · nonzero leading terms",
            "Construct highest-degree-first coefficient convolution, prove its finite support, and establish degree addition for genuinely nonzero-leading prime-field representations.",
            "Prime(p) ∧ FpRepresentedDegree(p,ab,ac,L,d) ∧ FpRepresentedDegree(p,bb,bc,M,e) ∧ FpPolyProduct(p,ab,ac,L,bb,bc,M,cb,cc,N) ⇒ FpRepresentedDegree(p,cb,cc,N,d+e)",
            "D04", "F10", ("G091",), by_slug["polynomial-products"].principal_roots,
            "polynomial-products", ("BetaPrefixEqual", "FpMul"),
            "Coefficients are highest-degree-first and every representation carries its explicit length. Empty inputs give an empty product; zero extension does not constrain unrelated beta entries past the prefix. Represented degree requires a decoded nonzero leading coefficient and does not assign a degree to zero. This checkpoint claims coefficient convolution and degree addition, not polynomial division, gcd, irreducible search, an evaluation-product identity, or general prime-power extension fields; full G091 remains open.",
            "canonical_polynomial_product_and_degree_subgoals_only_full_G091_open",
        ),
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
    """Preserve exact tags and all three separate research generations."""
    routes = {}
    for family in families():
        rows = checkpoints.load_rows(_checkpoint(family))
        routes.update({name: f"{family.slug}/explorer/defined/tag/{tag}.html"
                       for name, tag in model._tags(family, rows).items()})
    for family in prior_model.families():
        checkpoint = next(item for item in lower.CHECKPOINTS if item.slug == family.slug)
        routes.update({name: f"../constructive-lower-tier-explorer/{family.slug}/explorer/defined/tag/{tag}.html"
                       for name, tag in model._tags(family, lower.load_rows(checkpoint)).items()})
    for family in model.FAMILIES:
        checkpoint = next(item for item in bottom.CHECKPOINTS if item.slug == family.slug)
        routes.update({name: f"../constructive-bottom-layer-explorer/{family.slug}/explorer/defined/tag/{tag}.html"
                       for name, tag in model._tags(family, bottom.load_rows(checkpoint)).items()})
    return routes


def family_corpus(family: Family, evidence: checkpoints.ContinuationEvidence) -> dict[str, Any]:
    if (type(evidence) is not checkpoints.ContinuationEvidence
            or evidence.checkpoint != _checkpoint(family)
            or evidence.report.get("membership") != "local_non_admitting_checkpoint"
            or any(evidence.report.get(key) is not False for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"))
            or evidence.report.get("bundle", {}).get("original_ha_checked") is not True
            or evidence.report.get("bundle", {}).get("independent_lean_checked") is not True):
        raise ExplorerError("the renderer received no genuine continuation proof-check result")
    checkpoint = evidence.checkpoint
    owned_rows = [(pin, row) for pin in checkpoint.modules
                  for row in getattr(import_module("peano_lab.library." + pin.module), pin.factory)(TheoremSpec)]
    if tuple(row for _, row in owned_rows) != evidence.owned:
        raise ExplorerError("source factories changed after the complete proof checks")
    tags = model._tags(family, evidence.owned)
    if not set(family.roots) <= tags.keys():
        raise ExplorerError("a principal root is not a genuinely new owned theorem")
    positions = {row.name: row.node_id for row in evidence.plan.rows}
    vocabulary = tuple(item.name for route, items in CONTINUATION_REGISTRIES
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
    table = {row.name: row for row in (*closure.parent_snapshot().specs, *previous_rows(), *checkpoints.all_new_rows())}
    routes, external, external_routes = theorem_routes(), [], {}
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
        "proof_bundle_sha256": checkpoint.artifact_sha256, "proof_bundle_node_count": evidence.receipt.node_count,
        "checkpoint_report": evidence.report,
        "local_checkpoint_verified_node_count": len(nodes), "alpha_enrolled_node_count": 0,
        "alpha_checked_use_node_count": 0, "stable_admitted_node_count": 0,
        "parent_alpha_edition_version": "v30", "parent_alpha_checked_use_count": 3222,
        "parent_stable_count": 432, "parent_alpha_catalog_sha256": closure.PARENT_CATALOG_SHA256,
        "previous_research_generations": [170, 126],
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
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned('./', HTML_REVISION)}">{render._e(family.title)}</a><span>/</span><a href="{render._versioned('../grand-campaign/', HTML_REVISION)}">Local checkpoint map</a></nav><h1>Exact local checkpoint receipt</h1><p class="lede">{render._e(render._status(corpus))}</p></div></header>
<main class="shell family-main"><section class="release-note"><strong>Actual complete proof evidence:</strong> {report['bundle']['nodes_including_packaging_root']} original-HA and independently compiled Lean-checked nodes. <a href="{bundle_href}">Download literal proof bundle</a>; {report['bundle']['bytes']} bytes; SHA-256 <code>{report['bundle']['sha256']}</code>.</section>
<section class="release-note"><strong>Exact inventory roles:</strong> {report['new_theorem_count']} new owned theorems, {support['prior_bottom_layer_count']} inherited prerequisites from the first 170 research theorems, {support['prior_lower_tier_count']} from the later 126, {support['current_cross_track_count']} current cross-track prerequisites and {support['alpha_v30_count']} inherited Alpha theorems. Support rows are not recounted as new. Source-helper imports are not proof premises. Alpha v30 remains 3222; Stable remains 432. This page claims complete bundle checks, not ordinary-certificate replay for every theorem. <a href="{render._versioned('api/checkpoint.json', HTML_REVISION)}">Machine-readable report</a>.</section>
<section class="release-note"><strong>Mathematical boundary:</strong> {render._e(family.caveat)}</section>
<section><h2>Frozen authoring sources</h2><ul>{sources}</ul><p><a href="{render._versioned('../sources/' + Path(report['rfc']).name, HTML_REVISION)}">Exact campaign RFC</a></p></section>
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
        cards.append(f'''<article class="view-card" id="{family.slug}" data-local-family="{family.family_id}" data-local-domain="{family.domain}" data-local-goal="{goal}"><p class="card-kicker">{goal} · {family.family_id}</p><h2>{render._e(family.title)}</h2><p>{render._e(family.description)}</p><p>{corpus['node_count']} genuinely new local theorems · {corpus['definition_count']} conservative definitions</p><a href="{href}">Enter proof family →</a><p><a href="{graph}">Explore actual proof and definition dependencies →</a></p><p><a href="{roadmap}">View unchanged {goal} campaign roadmap →</a></p><p>{render._e(family.caveat)}</p></article>''')
    bottom_href = render._versioned(historical_prefix + "constructive-bottom-layer-explorer/", HTML_REVISION)
    lower_href = render._versioned(historical_prefix + "constructive-lower-tier-explorer/", HTML_REVISION)
    atlas_href = render._versioned(historical_prefix + "constructive-gaussian-campaign/", HTML_REVISION)
    body = f'''<header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{render._versioned(prefix or './', HTML_REVISION)}">Local continuation checkpoints</a><span>/</span><a href="{bottom_href}">First 170 research proofs</a><span>/</span><a href="{lower_href}">Next 126 research proofs</a><span>/</span><a href="{atlas_href}">Full campaign blueprint</a></nav><p class="eyebrow">Constructive arithmetic · local development</p><h1>Divisor cancellation, finite Fubini and polynomial products</h1><p class="lede">Four actual proof checkpoints, connected to both earlier research generations and the larger campaign. This local map neither changes the published atlas nor grants Alpha membership.</p></div></header><main class="shell family-main"><section class="view-grid">{''.join(cards)}</section><section class="release-note"><strong>Evidence boundary:</strong> {sum(corpus['node_count'] for corpus in corpora)} distinct new theorems, excluding inherited research and Alpha support. The earlier research generations contain 170 and 126 theorems. Alpha v30 remains 3222; Stable remains 432. Full G007 inversion and general G091 prime-power fields remain open. <a href="{render._versioned(prefix + 'checkpoints.json', HTML_REVISION)}">Exact checkpoint inventory</a>.</section></main>'''
    body += '''<script>
(function () {
  "use strict";
  var query = new URL(window.location.href).searchParams;
  var field = {family: "data-local-family", domain: "data-local-domain", goal: "data-local-goal"}[query.get("view")];
  var focus = query.get("focus");
  var cards = Array.from(document.querySelectorAll("[data-local-family]"));
  if (!field || !focus || !cards.some(function (card) { return card.getAttribute(field) === focus; })) return;
  cards.forEach(function (card) { card.hidden = card.getAttribute(field) !== focus; });
})();
</script>'''
    return model._simple_document("Local continuation proof checkpoints", body, prefix=prefix)


def build_files() -> dict[str, bytes]:
    selected_families = families()  # Incomplete registries never reach a proof label.
    if statement_duplicates(checkpoints.all_new_rows()):
        raise ExplorerError("new theorem counts include an exact old or cross-track duplicate")
    files, corpora = model._assets(), []
    for family in selected_families:
        checkpoint = _checkpoint(family)
        evidence = checkpoints.verify_checkpoint(checkpoint, ordinary_roots=False)
        corpus = family_corpus(family, evidence)
        corpora.append(corpus)
        graph = render.graph_payload(family, corpus, revision=HTML_REVISION)
        base = family.slug + "/"
        files[base + "index.html"] = render.render_local_family_landing(family, corpus, revision=HTML_REVISION, bundle_node_count=evidence.receipt.node_count)
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
        del evidence
        gc.collect()
    inventory = {
        "schema": SCHEMA, "publication_scope": "local-only-checkpoint", "published": False,
        "alpha_admission_performed": False, "stable_admission_performed": False,
        "navigation_revision": HTML_REVISION, "new_theorems": sum(corpus["node_count"] for corpus in corpora),
        "previous_research_theorems": 296, "previous_research_generations": [170, 126],
        "prior_theorem_count_for_exact_ast_novelty_check": 3518,
        "inherited_support_counted_as_new": False,
        "statement_asts_distinct_from_all_3518_prior_and_each_other": True,
        "full_G007_inversion_proved": False, "general_G091_prime_power_fields_proved": False,
        "parent": {"alpha_version": "v30", "alpha_checked_use_count": 3222, "stable_count": 432,
                   "catalog_sha256": closure.PARENT_CATALOG_SHA256},
        "independent_checker": {"binary_sha256": checkpoints.LEAN_BINARY_SHA256},
        "checkpoints": [corpus["checkpoint_report"] for corpus in corpora],
    }
    inventory["checkpoint_digest"] = _digest(_json(inventory))
    files["checkpoints.json"] = _json(inventory)
    files["index.html"], files["grand-campaign/index.html"] = dispatch(corpora, atlas=False), dispatch(corpora, atlas=True)
    files["manifest.json"] = _json({
        "schema": SCHEMA + "-manifest", "publication_scope": "local-only-checkpoint",
        "checkpoint_digest": inventory["checkpoint_digest"], "navigation_revision": HTML_REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {path: {"bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())},
    })
    return files


def main(argv: list[str] | None = None) -> int:
    import argparse
    from check_constructive_bottom_layers import authoring_rss_bytes

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fresh HA/Lean checks and exact snapshot comparison")
    args = parser.parse_args(argv)
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    files = build_files()
    authoring_rss_bytes()
    model.write_or_check(files, output=OUTPUT, check=args.check)
    peak = authoring_rss_bytes()
    print(f"{'Checked' if args.check else 'Generated'} {len(files)} canonical local files; {sum(item.frontier_count for item in checkpoints.CHECKPOINTS)} genuinely new theorems; peak RSS {peak} bytes.")
    print("No Alpha/Stable admission or publication; all previous snapshots and the published atlas unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
