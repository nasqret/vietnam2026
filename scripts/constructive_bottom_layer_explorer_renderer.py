"""Local-only Quadratic Reciprocity model for checked bottom-layer proofs.

The canonical published renderers require Alpha admission. This additive
adaptation keeps their HTML structure and immutable CSS/JS but substitutes
explicit local-checkpoint validation, labels, and relative navigation.
No renderer grants authority; the publisher must first run the actual HA
and independent compiled Lean verifiers. Historical renderers stay unchanged.
"""
from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import json
import re
from typing import Any

from constructive_checked_explorer_renderer import (
    ASSET_DIGESTS, _asset, _defined_command,
    _defined_statement, _document, _e,
    _versioned,
)
from constructive_frontier_exact_explorer import (
    _escape, _layer, _navigation_href, _page,
    _relation, _render_command,
)
from constructive_proof_explorer_template import (
    _DOMAIN, _FAMILY, _MILESTONE, _REVISION, _SHA256, _SLUG, _TAG,
    _Family, _href, _html, _number, _text,
)


class LocalExplorerRenderError(ValueError):
    """A local checkpoint was mislabeled as a library admission."""


ProofExplorerTemplateError = LocalExplorerRenderError
DefinedExplorerRenderError = LocalExplorerRenderError
HTML_REVISION = "ac7111ec14ff"
Family = Any
STATUS = ("Local checkpoint: original HA and independently compiled Lean verified; "
          "not Alpha-enrolled, no Alpha checked-use authority; not Stable")
FORBIDDEN_ADMISSION_FIELDS = (
    "enrolled_in_alpha", "admitted_to_alpha", "alpha_checked_use",
    "checked_use", "stable_member", "admitted_to_stable",
)


def _status(value: Mapping[str, Any]) -> str:
    if any(value.get(key) is not False for key in FORBIDDEN_ADMISSION_FIELDS):
        raise LocalExplorerRenderError("a local row has invalid or missing non-admission metadata")
    if (value.get("local_checkpoint_verified") is not True
            or value.get("original_ha_bundle_verified") is not True
            or value.get("independent_lean_bundle_verified") is not True):
        raise LocalExplorerRenderError("a local row has no complete HA/Lean checkpoint evidence")
    if any(value.get(key) is not None for key in (
        "alpha_first_enrolled_version", "alpha_edition_version",
        "alpha_evidence", "first_admitted_version",
    )):
        raise LocalExplorerRenderError("a local row impersonates an Alpha admission")
    return STATUS


_candidate_label = _status


# The frozen canonical asset owns search/kind handlers on each control. This
# local-only enhancement runs at the dashboard root, after those handlers have
# bubbled, so the three predicates are always combined regardless of load order.
# Neither the historical asset nor any published page is modified.
LOCAL_DASHBOARD_ENHANCEMENT = '''<script data-local-dashboard-enhancement>
(function () {
  "use strict";
  function initializeLocalDashboard() {
    document.querySelectorAll("[data-defined-dashboard]").forEach(function (root) {
      var search = root.querySelector("[data-search]");
      var kind = root.querySelector("[data-kind]");
      var layer = root.querySelector("[data-layer]");
      var clear = root.querySelector("[data-clear]");
      var count = root.querySelector("[data-count]");
      var cards = Array.from(root.querySelectorAll("[data-entry]"));
      if (!search || !kind || !layer || !clear || !count) return;
      function update() {
        var query = String(search.value || "").trim().toLowerCase();
        var visible = 0;
        cards.forEach(function (card) {
          var matches = (!query || String(card.dataset.search || "").toLowerCase().indexOf(query) !== -1) &&
            (kind.value === "all" || kind.value === card.dataset.kind) &&
            (layer.value === "all" || layer.value === card.dataset.layer);
          card.hidden = !matches;
          if (matches) visible += 1;
        });
        count.textContent = visible + (visible === 1 ? " entry" : " entries");
      }
      root.addEventListener("input", function (event) {
        if (event.target === search) update();
      });
      root.addEventListener("change", function (event) {
        if (event.target === kind || event.target === layer) update();
      });
      root.addEventListener("click", function (event) {
        if (event.target !== clear) return;
        search.value = "";
        kind.value = "all";
        layer.value = "all";
        update();
        search.focus();
      });
      update();
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initializeLocalDashboard, {once: true});
  } else {
    initializeLocalDashboard();
  }
})();
</script>'''


def _atlas_navigation(family: Any, *, prefix: str, revision: str, goal: str | None = None) -> str:
    links = (("global", "Local checkpoint map", ""),
             ("domain", "Checkpoint domain", f"?view=domain&focus={family.domain}"),
             ("family", "Checkpoint family", f"?view=family&focus={family.family_id}"))
    result = [f'<a data-campaign-link="{kind}" href="{_versioned(prefix + "grand-campaign/" + suffix, revision)}">{label}</a>'
              for kind, label, suffix in links]
    for milestone in ((goal,) if goal is not None else family.milestones):
        result.append(f'<a data-campaign-link="goal" data-campaign-goal="{_e(milestone)}" href="{_versioned(prefix + "grand-campaign/?view=goal&focus=" + milestone, revision)}">{_e(milestone)} milestone</a>')
    return "".join(result)


def _campaign_navigation(corpus: Mapping[str, Any], *, prefix: str, revision: str) -> str:
    return (f'<a data-campaign-link="family" href="{_versioned(prefix + "grand-campaign/?view=family&focus=" + corpus["campaign_family_id"], revision)}">Checkpoint family</a>'
            f'<a data-campaign-link="global" href="{_versioned(prefix + "grand-campaign/", revision)}">Local checkpoint map</a>')


def render_local_family_landing(
    family: _Family,
    corpus: Mapping[str, Any],
    *,
    revision: str,
    bundle_node_count: int,
) -> bytes:
    """Render the same three-card QR structure with local-only authority."""
    _status(corpus)

    slug = _text(family.slug, name="slug")
    if _SLUG.fullmatch(slug) is None:
        raise ProofExplorerTemplateError("the proof family has an unsafe URL slug")
    if _REVISION.fullmatch(revision) is None:
        raise ProofExplorerTemplateError("the sealed catalog revision is not 12 hexadecimal digits")
    if _DOMAIN.fullmatch(family.domain) is None or _FAMILY.fullmatch(family.family_id) is None:
        raise ProofExplorerTemplateError("the proof family has invalid campaign coordinates")
    if type(bundle_node_count) is not int or bundle_node_count <= 0:
        raise ProofExplorerTemplateError("the independently checked bundle has no nodes")

    milestones = tuple(family.milestones)
    roots = tuple(family.roots)
    if not milestones or any(_MILESTONE.fullmatch(value) is None for value in milestones):
        raise ProofExplorerTemplateError("the proof family has no exact campaign milestone")
    if not roots or len(set(roots)) != len(roots):
        raise ProofExplorerTemplateError("the proof family has no distinct checked theorem roots")
    tags = corpus.get("tags")
    if not isinstance(tags, Mapping):
        raise ProofExplorerTemplateError("the proof family has no authenticated theorem tags")
    for name in roots:
        tag = tags.get(name)
        if not isinstance(tag, str) or _TAG.fullmatch(tag) is None:
            raise ProofExplorerTemplateError(f"the proof family root has no stable tag: {name!r}")

    theorem_count = _number(corpus, "node_count", positive=True)
    checked_count = _number(corpus, "local_checkpoint_verified_node_count", positive=True)
    if (checked_count != theorem_count or corpus.get("alpha_checked_use_node_count") != 0
            or corpus.get("alpha_enrolled_node_count") != 0
            or corpus.get("stable_admitted_node_count") != 0):
        raise ProofExplorerTemplateError("local checkpoint and library admission counts were conflated")
    definition_count = _number(corpus, "definition_count")
    definition_edges = _number(corpus, "definition_dependency_count")
    proof_edges = _number(corpus, "edge_count")
    tactic_lines = _number(corpus, "formal_line_count")
    bundle_sha256 = corpus.get("proof_bundle_sha256")
    if not isinstance(bundle_sha256, str) or _SHA256.fullmatch(bundle_sha256) is None:
        raise ProofExplorerTemplateError("the independently checked proof bundle has no SHA-256")
    if corpus.get("independent_lean_bundle_verified") is not True:
        raise ProofExplorerTemplateError("the proof family lacks independent Lean evidence")

    title = _html(_text(family.title, name="title"))
    description = _html(_text(family.description, name="description"))
    kicker = _html(_text(family.kicker, name="mathematical classification"))
    formula = _html(_text(family.formula, name="mathematical formula"))
    caveat = _html(_text(family.caveat, name="mathematical evidence boundary"))
    root_name = roots[-1]
    root_tag = str(tags[root_name])
    goal = milestones[-1]

    graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=neighborhood&definitions=selected&edges=focus",
        revision,
    )
    visible_graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=neighborhood&definitions=visible&edges=focus",
        revision,
    )
    prerequisite_graph = _href(
        f"explorer/defined/graph.html?target={root_tag}"
        "&view=prerequisites&definitions=selected&edges=focus",
        revision,
    )
    atlas = _href("../grand-campaign/", revision)
    domain_atlas = _href(
        f"../grand-campaign/?view=domain&focus={family.domain}", revision
    )
    family_atlas = _href(
        f"../grand-campaign/?view=family&focus={family.family_id}", revision
    )
    goal_atlas = _href(f"../grand-campaign/?view=goal&focus={goal}", revision)
    goal_links = " · ".join(
        f'<a data-campaign-link="goal" data-campaign-goal="{_html(milestone)}" '
        f'href="{_href(f"../grand-campaign/?view=goal&focus={milestone}", revision)}">'
        f"{_html(milestone)} milestone</a>"
        for milestone in milestones
    )
    roots_html = " · ".join(
        f'<a href="{_href(f"explorer/defined/tag/{tags[name]}.html", revision)}">'
        f"<code>{_html(tags[name])}</code> {_html(name)}</a>"
        for name in roots
    )

    page = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Proof Explorer</title>
  <meta name="description" content="{description}">
  <meta property="og:title" content="{title} — Proof Explorer">
  <meta property="og:description" content="{description}">
  <meta property="og:type" content="website">
  <meta name="robots" content="noindex">
  <meta name="proof-publication-scope" content="local-only-checkpoint">
  <link rel="stylesheet" href="{_href('../assets/proofs.css', revision)}">
</head>
<body class="family-page {_html(slug)}-page">
  <header class="family-hero">
    <div class="shell">
      <nav class="crumbs"><a href="{_href('../', revision)}">Proof explorers</a><span>/</span><a data-campaign-link="global" href="{atlas}">Local checkpoint map</a><span>/</span><a data-campaign-link="family" href="{family_atlas}">Checkpoint family</a><span>/</span><span>{title}</span></nav>
      <p class="eyebrow">{kicker} · Constructive arithmetic</p>
      <h1>{title}</h1>
      <p class="formula">{formula}</p>
      <p class="lede">{description}</p>
      <div class="hero-actions">
        <a class="primary-action" href="{graph}">Open the definition-aware map</a>
        <a class="secondary-action" href="{_href(f'explorer/defined/tag/{root_tag}.html', revision)}">Read the final theorem</a>
        <a class="secondary-action" data-campaign-link="milestone" href="{goal_atlas}">See campaign milestone {_html(goal)}</a>
      </div>
    </div>
  </header>
  <main class="shell family-main">
    <section class="view-grid">
      <article class="view-card featured">
        <p class="card-kicker">Recommended</p>
        <h2>Defined mathematical notation</h2>
        <p>Browse {definition_count} linked conservative definitions and {theorem_count} independently checked theorems without losing their exact first-order expansions.</p>
        <a href="{_href('explorer/defined/', revision)}">Browse definitions and theorems →</a>
        <p><a href="{visible_graph}">Inspect the local definition DAG →</a></p>
      </article>
      <article class="view-card">
        <p class="card-kicker">Exact certificate</p>
        <h2>Fully expanded arithmetic</h2>
        <p>Inspect all {tactic_lines} native tactic lines and {proof_edges} actual proof prerequisites with every definition fully expanded.</p>
        <a href="{_href('explorer/', revision)}">Open the exact edition →</a>
      </article>
      <article class="view-card">
        <p class="card-kicker">Focused route</p>
        <h2>Final dependency cone</h2>
        <p>Start at theorem <code>{_html(root_tag)}</code> and follow only the lemmas and conservative definitions supporting {_html(root_name)}.</p>
        <a href="{prerequisite_graph}">Trace prerequisites →</a>
      </article>
    </section>
    <section class="release-note"><strong>Zoom between mathematical scales:</strong> <a data-campaign-link="global" href="{atlas}">local checkpoint map</a> → <a data-campaign-link="domain" href="{domain_atlas}">research domain</a> → <a data-campaign-link="family" href="{family_atlas}">proof family</a> → {goal_links} → <a href="{visible_graph}">theorem and definition dependencies</a>.</section>
    <section class="release-note"><strong>Major independently established statements:</strong> {roots_html}.</section>
    <section class="release-note"><strong>Local-only independently verified checkpoint:</strong> {theorem_count} theorems in a complete dependency-closed HA bundle · {proof_edges} proof prerequisites · {definition_count} linked definitions · {definition_edges} definition-dependency arrows · {tactic_lines} exact tactic lines. Not Alpha-enrolled; no Alpha checked-use authority; not Stable. Alpha v30 remains 3222 theorems and Stable remains 432. The unchanged intuitionistic kernel and separately compiled Lean verifier independently accept all {bundle_node_count} bundle nodes; SHA-256 <code>{_html(bundle_sha256)}</code>. <a href="{_href('checkpoint.html', revision)}">Inspect the checkpoint receipt, literal bundle, and source files →</a></section>
    <section class="release-note"><strong>Exact mathematical boundary:</strong> {caveat}</section>
  </main>
</body>
</html>
"""
    return page.encode("utf-8")


def _defined_index(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> bytes:
    cards: list[str] = []
    for node in corpus["nodes"]:
        tag = corpus["tags"][node["name"]]
        cards.append(
            '<article class="pd-result pd-result-theorem" '
            f'data-entry data-kind="theorem" data-status="local_verified" '
            f'data-layer="{corpus["layers"][node["name"]]}" '
            f'data-search="{_e((tag + " " + node["name"] + " " + node["summary"]).lower())}">'
            f'<a href="{_versioned(f"tag/{tag}.html", revision)}">'
            f'<code>{_e(tag)}</code> <strong>{_e(node["name"])}</strong></a>'
            f'<p>{_e(node["summary"])}</p><small>{_e(_status(node))}</small></article>'
        )
    for definition in corpus["definitions"]:
        cards.append(
            '<article class="pd-result pd-result-definition" '
            f'data-entry data-kind="definition" data-status="definition" '
            f'data-layer="{definition["topological_layer"]}" '
            f'data-search="{_e((definition["id"] + " " + definition["signature"] + " " + definition["summary"]).lower())}">'
            f'<a href="{_versioned("definition/" + definition["id"] + ".html", revision)}">'
            f'<code>{_e(definition["id"])}</code> <strong>{_e(definition["signature"])}</strong></a>'
            f'<p>{_e(definition["summary"])}</p><small>Conservative definition · '
            f'notation layer {definition["topological_layer"]}</small></article>'
        )
    root = corpus["tags"][family.roots[-1]]
    body = f"""<header class="pd-header pd-hero">
  <nav><a href="{_versioned('../../', revision)}">{_e(family.title)}</a>
       <a href="{_versioned('../', revision)}">Exact proof explorer</a>
       <a href="{_versioned(f'graph.html?target={root}', revision)}">Interactive dependency graph</a>
       {_atlas_navigation(family, prefix='../../../', revision=revision)}</nav>
  <p class="pd-kicker">{_e(family.kicker)}</p><h1>{_e(family.title)}</h1>
  <p>{_e(family.description)}</p>
  <div class="pd-stats"><b>{corpus['node_count']}</b> locally kernel- and Lean-verified theorems ·
    <b>{corpus['definition_count']}</b> conservative definitions ·
    <b>{corpus['definition_dependency_count']}</b> notation dependencies</div>
  <p class="pd-status">{_e(_status(corpus))}</p>
</header>
<main data-defined-dashboard><section class="pd-controls">
  <label>Search <input data-search type="search"></label>
  <label>Kind <select data-kind><option value="all">All</option><option value="theorem">Checked theorems</option><option value="definition">Definitions</option></select></label>
  <label>Layer <select data-layer><option value="all">All layers</option>{''.join(f'<option value="{layer}">{layer}</option>' for layer in sorted(set(corpus['layers'].values()) | {item['topological_layer'] for item in corpus['definitions']}))}</select></label>
  <button data-clear type="button">Clear</button><output data-count>{len(cards)} items</output>
</section><section class="pd-results">{''.join(cards)}</section>
<p class="pd-callout">Only proof arrows are theorem dependencies. Definition arrows are hygienic abbreviations of exact first-order formulas and introduce no axiom or kernel symbol.</p>
</main>"""
    return _document(
        family, title=f"{family.title} — Defined Proof Explorer", body=body, prefix="../../../",
        extra_script=LOCAL_DASHBOARD_ENHANCEMENT,
    )


def _defined_theorem(
    family: Family, corpus: Mapping[str, Any], node: Mapping[str, Any], *, revision: str
) -> bytes:
    _status(node)
    name = node["name"]
    tag = corpus["tags"][name]
    definitions = {item["id"]: item for item in corpus["definitions"]}
    uses = node["defined"]["definition_uses"]
    chips = "".join(
        f'<a class="pd-chip" href="{_versioned(f"../definition/{identifier}.html", revision)}">'
        f"{_e(definitions[identifier]['signature'])} · {count}</a>"
        for identifier, count in uses.items()
    ) or '<span class="pd-empty">none</span>'
    dependencies = "".join(
        (
            f'<a class="pd-chip" href="{_versioned(corpus["tags"][dependency] + ".html", revision)}">'
            f"{_e(dependency)}</a>"
            if dependency in corpus["tags"] else
            f'<a class="pd-chip pd-external" href="{_versioned("../../../../" + corpus["external_theorem_routes"][dependency], revision)}">'
            f"{_e(dependency)} · checked external prerequisite</a>"
            if dependency in corpus.get("external_theorem_routes", {}) else
            f'<span class="pd-chip pd-external">{_e(dependency)} · checked external prerequisite</span>'
        )
        for dependency in node["dependencies"]
    ) or '<span class="pd-empty">none</span>'
    proof_lines = "".join(
        f'<li class="pd-proof-line" id="proof-line-{index:04d}" data-line="{index}">'
        f'<a class="pd-line-number" href="#proof-line-{index:04d}">{index:04d}</a>'
        f'<code>{_defined_command(parts, tags=corpus["tags"], dependencies=set(node["dependencies"]), revision=revision)}</code></li>'
        for index, parts in enumerate(node["defined"]["script_parts"], 1)
    )
    milestone_note = f'<p class="pd-callout">{_e(family.caveat)}</p>'
    body = f"""<header class="pd-header pd-theorem-heading">
  <nav><a href="{_versioned('../', revision)}">Definitions and proofs</a>
       <a href="{_versioned(f'../../tag/{tag}.html', revision)}">Exact original proof</a>
       <a href="{_versioned(f'../graph.html?target={tag}', revision)}">Interactive proof graph</a>
       {_atlas_navigation(family, prefix='../../../../', revision=revision, goal=node['campaign_milestone'])}</nav>
  <p class="pd-tag">{_e(tag)}</p><h1>{_e(name)}</h1>
  <p>{_e(node['summary'])}</p><p class="pd-status">{_e(_status(corpus))}</p>
</header>
<main class="pd-theorem-layout"><div class="pd-proof-panel">
  {milestone_note}
  <section class="pd-statement"><h2>Exact theorem in conservative defined notation</h2>
    <pre><code>{_defined_statement(node, revision=revision)}</code></pre>
    <p>Every linked abbreviation expands hygienically to the identical original native formula.</p></section>
  <section><h2>Definition DAG</h2><div class="pd-chip-row">{chips}</div></section>
  <section><h2>Actual proof prerequisites</h2><div class="pd-chip-row">{dependencies}</div></section>
  <details class="pd-expanded"><summary>Original expanded first-order statement</summary>
    <pre><code>{_e(node['statement'])}</code></pre></details>
  <section><h2>Complete tactic proof in conservative notation</h2>
    <p>All {len(node['script'])} original proof lines are preserved. Only local proposition formulas are abbreviated; every abbreviation has an exact binder-safe expansion check. The linked exact edition contains the unchanged replay script.</p>
    <ol class="pd-formal-proof">{proof_lines}</ol></section>
</div><aside class="pd-proof-sidebar pd-trust-panel"><h2>Independent closure receipt</h2>
  <dl><dt>Authority</dt><dd>Local original-HA + independent Lean checkpoint only</dd><dt>Alpha admission / checked use</dt><dd>none</dd><dt>Stable membership</dt><dd>none</dd>
      <dt>Proof-bundle node</dt><dd>{node['proof_bundle_node_id']} / {corpus['proof_bundle_node_count']}</dd>
      <dt>Kernel mode</dt><dd>unchanged intuitionistic Heyting arithmetic</dd>
      <dt>Independent Lean verifier</dt><dd>compiled verifier accepted all {corpus['proof_bundle_node_count']} exact bundle nodes</dd>
      <dt>Body proof nodes / depth</dt><dd>{node['body_proof_nodes']} / {node['body_proof_depth']}</dd>
      <dt>Statement SHA-256</dt><dd><code>{_e(node['statement_sha256'])}</code></dd>
      <dt>Script SHA-256</dt><dd><code>{_e(node['sources'][0]['script_sha256'])}</code></dd>
      <dt>Proof bundle SHA-256</dt><dd><code>{_e(node['proof_bundle_sha256'])}</code></dd>
      <dt>Exact source module</dt><dd><a href="{_versioned('../../../../sources/' + node['source_filename'], revision)}"><code>{_e(node['source_module'])}</code></a></dd>
      <dt>Literal bundle and checkpoint receipt</dt><dd><a href="{_versioned('../../../checkpoint.html#theorem-' + name, revision)}">Inspect exact evidence</a></dd></dl>
</aside></main>"""
    return _document(family, title=f"{tag} — {name} — Defined Proof", body=body, prefix="../../../../")


def _graph_payload(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> dict[str, Any]:
    _status(corpus)
    for node in corpus["nodes"]:
        _status(node)
    theorem_nodes = [
        {
            "id": corpus["tags"][node["name"]],
            "name": node["name"],
            "kind": "theorem",
            "scope": "candidate",
            "summary": node["summary"],
            "layer": corpus["layers"][node["name"]],
            "href": _versioned(f"tag/{corpus['tags'][node['name']]}.html", revision),
            **{key: False for key in FORBIDDEN_ADMISSION_FIELDS},
            "local_checkpoint_verified": True,
            "original_ha_bundle_verified": True,
            "independent_lean_bundle_verified": True,
            "stable_member": False,
            "proof_bundle_node_id": node["proof_bundle_node_id"],
        }
        for node in corpus["nodes"]
    ]
    definition_nodes = [
        {
            "id": item["id"],
            "name": item["name"],
            "kind": "definition",
            "signature": item["signature"],
            "summary": item["summary"],
            "layer": item["topological_layer"],
            "href": _versioned(f"definition/{item['id']}.html", revision),
            "global_definition": item["global_definition"],
        }
        for item in corpus["definitions"]
    ]
    adjacency = {
        corpus["tags"][name]: {
            "dependencies": [corpus["tags"][value] for value in row["dependencies"]],
            "dependents": [corpus["tags"][value] for value in row["dependents"]],
            "critical_root_path": row["critical_root_path"],
        }
        for name, row in corpus["proof_adjacency"].items()
    }
    return {
        "schema": f"{corpus['schema']}-graph",
        "family_slug": family.slug,
        "nodes": theorem_nodes + definition_nodes,
        "edges": corpus["edges"],
        "proof_adjacency": adjacency,
        "root_ids": [corpus["tags"][name] for name in family.roots],
        "path_policy": "proof_dependency_edges_only",
        "parent_alpha_edition_version": "v30",
        "publication_scope": "local-only-checkpoint",
        **{key: False for key in FORBIDDEN_ADMISSION_FIELDS},
        "local_checkpoint_verified": True,
        "original_ha_bundle_verified": True,
        "independent_lean_bundle_verified": True,
        "alpha_checked_use_node_count": 0,
        "alpha_enrolled_node_count": 0,
        "local_checkpoint_verified_node_count": corpus["node_count"],
        "stable_admitted_node_count": 0,
        "definition_topological_order": corpus["definition_topological_order"],
    }


def _defined_graph(
    family: Family,
    corpus: Mapping[str, Any],
    graph: Mapping[str, Any],
    *,
    revision: str,
) -> bytes:
    serialized = json.dumps(graph, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    if "</script" in serialized.lower():
        raise DefinedExplorerRenderError("graph payload contains an unsafe script boundary")
    overlay = """<script>
document.addEventListener("DOMContentLoaded", function () {
  var title = document.querySelector("[data-graph-title]");
  var kind = document.querySelector("[data-graph-kind]");
  if (!title || !kind || typeof MutationObserver === "undefined") return;
  function label() {
    var id = String(title.textContent || "").split(" · ")[0];
    var row = (window.PA_DEFINED_GRAPH.nodes || []).find(function (node) { return node.id === id; });
    if (row && row.kind === "theorem" && row.local_checkpoint_verified) {
      kind.textContent = "Local HA + independent Lean checkpoint — not Alpha-enrolled; no checked-use authority; not Stable";
    }
  }
  new MutationObserver(label).observe(title, { childList: true, characterData: true, subtree: true });
  label();
});
</script>"""
    body = f"""<header class="pd-header pd-graph-heading">
 <nav><a href="{_versioned('./', revision)}">Definitions and proofs</a>
      <a href="{_versioned('../', revision)}">Exact original proof explorer</a>
      {_atlas_navigation(family, prefix='../../../', revision=revision)}</nav>
 <h1>{_e(family.title)} — interactive proof and definition DAG</h1>
 <p>Solid arrows are independently checked theorem prerequisites. Dashed arrows are conservative notation dependencies, never proof steps.</p>
 <p class="pd-status">{_e(_status(corpus))}</p>
</header>
<main class="pd-graph-page" data-defined-graph>
 <form class="pd-graph-controls" data-graph-form>
   <label>Target theorem <input list="pd-graph-theorems" data-graph-target><datalist id="pd-graph-theorems"></datalist></label>
   <label>Proof view <select data-graph-view><option value="critical">Critical proof path</option><option value="prerequisites">All proof prerequisites</option><option value="neighborhood">Immediate neighborhood</option><option value="corpus">Complete family</option></select></label>
   <label>Definitions <select data-graph-definitions><option value="selected">Selected theorem</option><option value="visible">All displayed theorems</option><option value="off">Hide notation</option></select></label>
   <label>Arrows <select data-graph-edges><option value="focus">Focused arrows</option><option value="all">All arrows</option><option value="none">Hide arrows</option></select></label>
   <button type="submit">Show proof</button>
 </form>
 <div class="pd-graph-workspace"><section class="pd-graph-canvas">
   <div class="pd-graph-toolbar"><button type="button" data-graph-zoom="in">+</button>
     <button type="button" data-graph-zoom="out">−</button>
     <button type="button" data-graph-fit>Fit proof</button>
     <output data-graph-summary>Loading checked constructive graph…</output></div>
   <div class="pd-graph-svg-wrap"><svg data-graph-svg tabindex="0" role="img" aria-label="Interactive checked theorem and conservative definition dependency graph"></svg></div>
 </section><aside class="pd-graph-details"><h2 data-graph-title tabindex="-1">Selected node</h2>
   <p data-graph-kind></p><p data-graph-description></p><dl data-graph-metadata></dl>
   <a data-graph-open href="#">Open node →</a><h3>Outgoing relations</h3>
   <ul data-graph-outgoing></ul><h3>Incoming relations</h3><ul data-graph-incoming></ul>
 </aside></div>
</main><script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={serialized};</script>{overlay}"""
    return _document(
        family, title=f"{family.title} — Interactive Checked Proof Graph", body=body,
        prefix="../../../",
    )


def render_exact_index(
    family: Any,
    corpus: Mapping[str, Any],
    tags: Mapping[str, str],
    layers: Mapping[str, int],
    *,
    stylesheet_href: str,
    script_href: str,
    html_revision: str = HTML_REVISION,
) -> bytes:
    """Render the searchable original native-PA theorem-index interface."""

    nodes = tuple(corpus["nodes"])
    layer_numbers = sorted({_layer(node, tags, layers) for node in nodes})
    layer_options = "".join(
        f'<option value="{number}">Layer {number}</option>'
        for number in layer_numbers
    )
    cards: list[str] = []
    for node in nodes:
        name = str(node["name"])
        tag = tags[name]
        layer = _layer(node, tags, layers)
        status = _candidate_label(node)
        searchable = " ".join(
            (
                name,
                tag,
                str(node["summary"]),
                status,
                *(str(dependency) for dependency in node["dependencies"]),
            )
        ).lower()
        cards.append(
            '<article class="pa-proof-result pa-status-candidate" '
            'data-pa-theorem '
            f'data-name="{_escape(name)}" data-tag="{_escape(tag)}" '
            f'data-status="local_verified" '
            f'data-layer="{layer}" '
            f'data-search="{_escape(searchable)}">'
            f'<a href="{_navigation_href(f"tag/{tag}.html", html_revision)}">'
            f'<code>{_escape(tag)}</code> · '
            f'<strong>{_escape(name)}</strong></a>'
            f'<p>{_escape(node["summary"])}</p>'
            f'<small>layer {layer} · {len(node["script"])} lines · '
            f'{_escape(status)}</small></article>'
        )

    root = str(corpus["root_names"][-1])
    root_tag = tags[root]
    count = len(nodes)
    status_options = f'<option value="local_verified">Locally HA/Lean verified ({count})</option>'
    boundary = STATUS + ". All prerequisite bodies are checked in the literal complete bundle."
    layer_count = len(layer_numbers)
    layer_links = "".join(
        f'<a href="{_navigation_href(f"?layer={number}", html_revision)}">'
        f'{number}</a>'
        for number in layer_numbers
    )
    family_href = _navigation_href("../", html_revision)
    defined_href = _navigation_href("defined/", html_revision)
    graph_href = _navigation_href(
        f"defined/graph.html?target={root_tag}", html_revision
    )
    graph_navigation = " data-graph-navigation"
    campaign_navigation = _campaign_navigation(
        corpus, prefix="../../", revision=html_revision
    )
    body = f"""<header class="pa-proof-header pa-hero">
  <nav><a href="{family_href}">{_escape(family.title)}</a><a href="{defined_href}">Defined notation</a><a href="{graph_href}"{graph_navigation}>Dependency graph</a>{campaign_navigation}</nav>
  <h1>{_escape(family.title)} — Exact Proof Explorer</h1>
  <p>{_escape(family.description)}</p>
  <div class="pa-proof-stats"><b>{count}</b> theorem bodies · <b>{corpus['edge_count']}</b> proof edges · <b>{corpus['formal_line_count']}</b> tactic lines · <b>{layer_count}</b> layers</div>
  <p class="pa-status-candidate">{_escape(corpus['candidate_status'])}</p>
</header>
<main data-proof-dashboard data-pa-explorer-index>
  <section class="pa-proof-controls"><label>Search <input data-proof-search data-pa-search type="search"></label><label>Status <select data-proof-status data-pa-status><option value="all">All</option>{status_options}</select></label><label>Layer <select data-proof-layer data-pa-layer><option value="all">All {layer_count} layers</option>{layer_options}</select></label><button data-proof-clear data-pa-clear type="button">Clear</button><output data-proof-count data-pa-count>{count} theorems</output></section>
  <section class="pa-layer-map">{layer_links}</section>
  <section class="pa-proof-results">{"".join(cards)}</section>
  <p class="pa-callout">{_escape(boundary)}</p>
</main>"""
    return _page(
        family=family,
        title=f"{family.title} — Exact Proof Explorer",
        page="index",
        body=body,
        stylesheet_href=stylesheet_href,
        script_href=script_href,
    )


def render_exact_theorem(
    family: Any,
    corpus: Mapping[str, Any],
    node: Mapping[str, Any],
    tags: Mapping[str, str],
    layers: Mapping[str, int],
    *,
    stylesheet_href: str,
    script_href: str,
    html_revision: str = HTML_REVISION,
) -> bytes:
    """Render one lightweight, canonical, evidence-honest exact proof page."""

    name = str(node["name"])
    tag = tags[name]
    node_names = tuple(str(item["name"]) for item in corpus["nodes"])
    index = node_names.index(name)
    previous = node_names[index - 1] if index else None
    following = node_names[index + 1] if index + 1 < len(node_names) else None
    previous_link = (
        '<a '
        f'href="{_navigation_href(f"{tags[previous]}.html", html_revision)}">'
        f'← {_escape(previous)}</a>'
        if previous is not None
        else ""
    )
    following_link = (
        '<a '
        f'href="{_navigation_href(f"{tags[following]}.html", html_revision)}">'
        f'{_escape(following)} →</a>'
        if following is not None
        else ""
    )
    dependencies = tuple(str(value) for value in node["dependencies"])
    dependency_names = set(dependencies)
    dependents = tuple(
        str(other["name"])
        for other in corpus["nodes"]
        if name in other["dependencies"]
    )
    external = {
        str(item["name"]): item
        for item in corpus["external_dependencies"]
    }
    lines: list[str] = []
    for number, item in enumerate(node["script"], start=1):
        command = str(item)
        rendered, tactic = _render_command(
            command,
            tags=tags,
            dependencies=dependency_names,
            html_revision=html_revision,
        )
        stable_id = sha256(
            f"{tag}\0{number}\0{command}".encode("utf-8")
        ).hexdigest()[:16]
        line_id = f"proof-line-{number:04d}"
        lines.append(
            f'<li class="pa-proof-line" id="{line_id}" data-line="{number}" '
            f'data-tactic="{_escape(tactic)}" data-line-id="{stable_id}">'
            f'<a class="pa-line-number" href="#{line_id}">{number:04d}</a>'
            f'<code>{rendered}</code></li>'
        )

    sources = tuple(node.get("sources", ()))
    source = next((item for item in sources if item.get("selected")), None)
    if source is None:
        source = sources[0] if sources else {}
    _status(node)
    alpha_evidence = "not enrolled"
    authority = "none — local checkpoint only"
    proof_boundary = ("The literal dependency-closed bundle is checked by original HA and "
                      "the independently compiled Lean verifier. This local "
                      "checkpoint grants no Alpha checked-use authority or Stable membership.")
    experiment = ""
    layer = _layer(node, tags, layers)
    explorer_href = _navigation_href("../index.html", html_revision)
    defined_href = _navigation_href(
        f"../defined/tag/{tag}.html", html_revision
    )
    graph_href = _navigation_href(
        f"../defined/graph.html?target={tag}", html_revision
    )
    graph_navigation = " data-graph-navigation"
    campaign_navigation = _campaign_navigation(
        corpus, prefix="../../../", revision=html_revision
    )
    body = f"""<header class="pa-proof-header pa-theorem-heading">
  <nav><a href="{explorer_href}">Explorer</a><a href="{defined_href}">Defined notation</a><a href="{graph_href}"{graph_navigation}>Dependency graph</a>{campaign_navigation}{previous_link}{following_link}</nav>
  <p class="pa-tag">{_escape(tag)}</p><h1>{_escape(name)}</h1>
  <p class="pa-status-candidate">{_escape(_candidate_label(node))}</p>
  <p>{_escape(node['summary'])}</p>
</header>
<main class="pa-theorem-layout">
  <div class="pa-proof-panel">
    <section class="pa-statement"><h2>Exact expanded first-order arithmetic statement</h2><button data-copy-target="statement" type="button">Copy</button><pre id="statement"><code>{_escape(node['statement'])}</code></pre></section>
    <section class="pa-informal-proof" data-informal-kind="structural" data-informal-review="generated"><h2>Constructive proof overview</h2><p><strong>Generated structural guide</strong></p><p>{_escape(node['summary'])}</p><p>The unchanged tactic script uses {len(dependencies)} declared prerequisite{'s' if len(dependencies) != 1 else ''} and contains {len(lines)} exact native proof lines.</p><p>{_escape(corpus['candidate_status'])}</p>{experiment}</section>
    <section><h2>Proof neighborhood</h2><h3>Direct dependencies</h3><div class="pa-chip-row">{_relation(dependencies, tags=tags, external=external, html_revision=html_revision)}</div><h3>Direct dependents</h3><div class="pa-chip-row">{_relation(dependents, tags=tags, external=external, html_revision=html_revision)}</div></section>
    <section><h2>Formal native tactic body</h2><p>Dependencies are introduced as named hypotheses before line 1. Local theorem links identify exact declared prerequisites. {_escape(proof_boundary)}</p><ol class="pa-formal-proof">{"".join(lines)}</ol></section>
  </div>
  <aside class="pa-proof-sidebar pa-trust-panel"><h2>Receipt and source provenance</h2><dl><dt>Proof layer</dt><dd>{layer}</dd><dt>Tactic lines</dt><dd>{len(lines)}</dd><dt>Alpha evidence</dt><dd>{_escape(alpha_evidence)}</dd><dt>Checked-use authority</dt><dd>{_escape(authority)}</dd><dt>Stable membership</dt><dd>none</dd><dt>Exact statement SHA-256</dt><dd><code>{_escape(node['statement_sha256'])}</code></dd><dt>Exact script SHA-256</dt><dd><code>{_escape(source.get('script_sha256', 'not recorded'))}</code></dd><dt>Source module</dt><dd><a href="{_navigation_href('../../../sources/' + node['source_filename'], html_revision)}"><code>{_escape(node['source_module'])}</code></a></dd><dt>Literal bundle and local receipt</dt><dd><a href="{_navigation_href('../../checkpoint.html#theorem-' + name, html_revision)}">Inspect exact evidence</a></dd><dt>Factory</dt><dd><code>{_escape(source.get('factory', node.get('factory', 'not recorded')))}</code></dd></dl></aside>
</main>"""
    return _page(
        family=family,
        title=f"{tag} — {name} — Exact Proof",
        page="theorem",
        body=body,
        stylesheet_href=stylesheet_href,
        script_href=script_href,
    )



def _defined_definition(
    family: Family,
    corpus: Mapping[str, Any],
    definition: Mapping[str, Any],
    *,
    revision: str,
) -> bytes:
    identifier = definition["id"]
    definitions = {item["id"]: item for item in corpus["definitions"]}
    dependencies = "".join(
        f'<a class="pd-chip" href="{_versioned(dependency + ".html", revision)}">'
        f"{_e(definitions[dependency]['signature'])}</a>"
        for dependency in definition["dependencies"]
    ) or '<span class="pd-empty">none — first-order arithmetic only</span>'
    consumers = [
        node for node in corpus["nodes"] if identifier in node["defined"]["definition_uses"]
    ]
    users = "".join(
        f'<a class="pd-chip" '
        f'href="{_versioned("../tag/" + corpus["tags"][node["name"]] + ".html", revision)}">'
        f"{_e(corpus['tags'][node['name']])} · {_e(node['name'])}</a>"
        for node in consumers
    ) or '<span class="pd-empty">none directly; see definition consumers</span>'
    notation_users = "".join(
        f'<a class="pd-chip" href="{_versioned(item["id"] + ".html", revision)}">'
        f"{_e(item['signature'])}</a>"
        for item in corpus["definitions"] if identifier in item["dependencies"]
    ) or '<span class="pd-empty">none</span>'
    global_link = (
        f'<a data-campaign-link="definition" '
        f'href="{_versioned("../../../../grand-campaign/?view=definition&focus=" + definition["global_definition"], revision)}">'
        f"Global definition: {_e(definition['global_definition'])}</a>"
        if definition["global_definition"] is not None else
        "<span>No signature-compatible global blueprint alias is asserted.</span>"
    )
    reviewed = (
        f"Exact reviewed registry identity {_e(definition['reviewed_definition_id'])}."
        if definition["reviewed_definition_id"] is not None else
        "Family-local hygienic display abbreviation."
    )
    prerequisite_reading = "".join(
        (
            f'<a class="pd-definition-ref" data-definition="{_e(part["definition"])}" '
            f'href="{_versioned(part["definition"] + ".html", revision)}">{_e(part["text"])}</a>'
            if part["kind"] == "definition" else _e(part["text"])
        )
        for part in definition["defined_template_parts"]
    )
    body = f"""<header class="pd-header pd-definition-heading">
  <nav><a href="{_versioned('../', revision)}">Definitions and proofs</a>
       <a href="{_versioned('../graph.html', revision)}">Interactive dependency graph</a>
       {global_link}{_atlas_navigation(family, prefix='../../../../', revision=revision)}</nav>
  <p class="pd-tag">{_e(identifier)}</p><h1>{_e(definition['signature'])}</h1>
  <p>{_e(definition['summary'])}</p><p class="pd-status">Conservative notation; not a theorem, primitive, or axiom.</p>
</header><main class="pd-theorem-layout"><div class="pd-proof-panel">
  <section><h2>Definition in prerequisite notation</h2>
    <pre><code>{prerequisite_reading}</code></pre>
    <p>Only definitions earlier in this acyclic notation graph are used here.</p></section>
  <details><summary>Hygienic expanded first-order definition</summary>
    <pre><code>{_e(definition['expanded_template'])}</code></pre>
    <p>The unchanged native kernel never receives this surface symbol. Binder-safe expansion produces only its existing first-order syntax.</p></details>
  <section><h2>Direct definition dependencies</h2><div class="pd-chip-row">{dependencies}</div></section>
  <section><h2>Definitions depending on this notation</h2><div class="pd-chip-row">{notation_users}</div></section>
  <section><h2>Checked theorems using this definition</h2><div class="pd-chip-row">{users}</div></section>
</div><aside class="pd-proof-sidebar"><h2>Definition identity</h2><dl>
  <dt>Arity</dt><dd>{definition['arity']}</dd>
  <dt>Topological notation layer</dt><dd>{definition['topological_layer']}</dd>
  <dt>Transitive prerequisites</dt><dd>{len(definition['transitive_dependencies'])}</dd>
  <dt>Origin</dt><dd>{_e(definition['origin'])}</dd>
  <dt>Reviewed identity</dt><dd>{reviewed}</dd>
  <dt>Expanded formula SHA-256</dt><dd><code>{_e(definition['expansion_sha256'])}</code></dd>
</dl></aside></main>"""
    return _document(
        family, title=f"{identifier} — {definition['signature']} — Definition", body=body,
        prefix="../../../../",
    )



render_defined_index = _defined_index
render_defined_theorem = _defined_theorem
render_defined_definition = _defined_definition
render_defined_graph = _defined_graph
graph_payload = _graph_payload
