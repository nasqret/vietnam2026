"""Canonical Quadratic Reciprocity-style reading and graph page renderers.

Extracted from the established next-layer renderer without importing any Alpha
edition. Callers must supply authenticated corpus data; this module grants no
proof authority and keeps the original graph CSS/JS assets unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
import html
import json
import re
from typing import Any


Family = Any
SCHEMA = "peano-lab-constructive-second-wave-explorer-v1"
STATUS = "Alpha v27 checked-use · first admitted v27 · independently kernel and Lean verified; not Stable"
ASSET_DIGESTS = {
    "defined-explorer.css": "eb26033797a96d83d62b36d9562ffa37afe7443e2a54bd1d693fc9d5da5ad220",
    "defined-explorer.js": "1b95ce2289502ba87f76708096aa76c07961be733d37dd56f64711b04621d982",
    "exact-explorer.css": "6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc",
    "exact-explorer.js": "98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606",
}


class DefinedExplorerRenderError(ValueError):
    """An authenticated corpus violates the original reading-page contract."""


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _versioned(path: str, revision: str) -> str:
    if path.startswith("#"):
        return _e(path)
    destination, marker, fragment = path.partition("#")
    separator = "&" if "?" in destination else "?"
    result = f"{destination}{separator}v={revision}"
    return _e(result + (f"#{fragment}" if marker else ""))


def _asset(name: str, prefix: str) -> str:
    return _versioned(f"{prefix}assets/{name}", ASSET_DIGESTS[name][:12])


def _atlas_navigation(
    family: Family, *, prefix: str, revision: str, goal: str | None = None
) -> str:
    labels = (
        ("global", "Full campaign map", ""),
        ("domain", "Campaign domain", f"?view=domain&focus={family.domain}"),
        ("family", "Campaign family", f"?view=family&focus={family.family_id}"),
    )
    parts = [
        f'<a data-campaign-link="{kind}" '
        f'href="{_versioned(f"{prefix}grand-campaign/{suffix}", revision)}">'
        f"{_e(label)}</a>"
        for kind, label, suffix in labels
    ]
    for milestone in ((goal,) if goal is not None else family.milestones):
        parts.append(
            f'<a data-campaign-link="goal" data-campaign-goal="{_e(milestone)}" '
            f'href="{_versioned(f"{prefix}grand-campaign/?view=goal&focus={milestone}", revision)}">'
            f"{_e(milestone)} milestone</a>"
        )
    return "".join(parts)


def _document(
    family: Family,
    *,
    title: str,
    body: str,
    prefix: str,
    defined: bool = True,
    extra_script: str = "",
) -> bytes:
    style = "defined-explorer.css" if defined else "proofs.css"
    script = (
        f'<script defer src="{_asset("defined-explorer.js", prefix)}"></script>'
        if defined else ""
    )
    classes = "pa-defined-proof-site" if defined else "proof-library-site"
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_e(title)}</title>
  <link rel="stylesheet" href="{_asset(style, prefix)}">
  {script}{extra_script}
</head>
<body class="{classes}" data-family="{_e(family.slug)}">{body}</body>
</html>
""".encode("utf-8")


def _defined_statement(node: Mapping[str, Any], *, revision: str) -> str:
    rendered: list[str] = []
    for part in node["defined"]["statement_parts"]:
        text = _e(part["text"])
        if part["kind"] == "definition":
            text = (
                f'<a class="pd-definition-ref" data-definition="{_e(part["definition"])}" '
                f'href="{_versioned("../definition/" + part["definition"] + ".html", revision)}">'
                f"{text}</a>"
            )
        rendered.append(text)
    return "".join(rendered)


def _defined_index(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> bytes:
    cards: list[str] = []
    for node in corpus["nodes"]:
        tag = corpus["tags"][node["name"]]
        cards.append(
            '<article class="pd-result pd-result-theorem" '
            f'data-entry data-kind="theorem" data-status="alpha_closed" '
            f'data-layer="{corpus["layers"][node["name"]]}" '
            f'data-search="{_e((tag + " " + node["name"] + " " + node["summary"]).lower())}">'
            f'<a href="{_versioned(f"tag/{tag}.html", revision)}">'
            f'<code>{_e(tag)}</code> <strong>{_e(node["name"])}</strong></a>'
            f'<p>{_e(node["summary"])}</p><small>{_e(STATUS)}</small></article>'
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
  <div class="pd-stats"><b>{corpus['node_count']}</b> kernel- and Lean-verified Alpha-closed theorems ·
    <b>{corpus['definition_count']}</b> conservative definitions ·
    <b>{corpus['definition_dependency_count']}</b> notation dependencies</div>
  <p class="pd-status">{_e(STATUS)}</p>
</header>
<main data-defined-dashboard><section class="pd-controls">
  <label>Search <input data-search type="search"></label>
  <label>Kind <select data-kind><option value="all">All</option><option value="theorem">Checked theorems</option><option value="definition">Definitions</option></select></label>
  <label>Layer <select data-layer><option value="all">All layers</option>{''.join(f'<option value="{layer}">{layer}</option>' for layer in sorted(set(corpus['layers'].values())))}</select></label>
  <button data-clear type="button">Clear</button><output data-count>{len(cards)} items</output>
</section><section class="pd-results">{''.join(cards)}</section>
<p class="pd-callout">Only proof arrows are theorem dependencies. Definition arrows are hygienic abbreviations of exact first-order formulas and introduce no axiom or kernel symbol.</p>
</main>"""
    return _document(
        family, title=f"{family.title} — Defined Proof Explorer", body=body, prefix="../../../"
    )


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _formal_command(
    line: str,
    *,
    tags: Mapping[str, str],
    dependencies: set[str],
    revision: str,
) -> str:
    parts: list[str] = []
    end = 0
    for match in _IDENTIFIER.finditer(line):
        parts.append(_e(line[end:match.start()]))
        token = match.group()
        if token in dependencies and token in tags:
            parts.append(
                f'<a class="pd-theorem-ref" '
                f'href="{_versioned(f"{tags[token]}.html", revision)}">{_e(token)}</a>'
            )
        else:
            parts.append(_e(token))
        end = match.end()
    parts.append(_e(line[end:]))
    return "".join(parts)


def _defined_command(
    parts: list[dict[str, str]], *, tags: Mapping[str, str],
    dependencies: set[str], revision: str,
) -> str:
    """Link conservative local propositions without changing the exact script."""
    result = []
    for part in parts:
        if part["kind"] == "definition":
            identifier = part["definition"]
            result.append(
                f'<a class="pd-definition-ref" data-definition="{_e(identifier)}" '
                f'href="{_versioned("../definition/" + identifier + ".html", revision)}">'
                f'{_e(part["text"])}</a>'
            )
        else:
            result.append(_formal_command(part["text"], tags=tags, dependencies=dependencies, revision=revision))
    return "".join(result)


def _defined_theorem(
    family: Family, corpus: Mapping[str, Any], node: Mapping[str, Any], *, revision: str
) -> bytes:
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
            f'<span class="pd-chip pd-external">{_e(dependency)} · checked external prerequisite</span>'
        )
        for dependency in node["dependencies"]
    ) or '<span class="pd-empty">none</span>'
    proof_lines = "".join(
        f'<li class="pd-proof-line" id="L{index}" data-line="{index}">'
        f'<a class="pd-line-number" href="#L{index}">{index:04d}</a>'
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
  <p>{_e(node['summary'])}</p><p class="pd-status">{_e(STATUS)}</p>
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
  <dl><dt>Authority</dt><dd>Alpha v27 checked use</dd><dt>First admission</dt><dd>Alpha v27</dd><dt>Stable membership</dt><dd>none</dd>
      <dt>Proof-bundle node</dt><dd>{node['proof_bundle_node_id']} / {corpus['proof_bundle_node_count']}</dd>
      <dt>Kernel mode</dt><dd>unchanged intuitionistic Heyting arithmetic</dd>
      <dt>Independent Lean verifier</dt><dd>compiled verifier accepted all {corpus['proof_bundle_node_count']} exact bundle nodes</dd>
      <dt>Body proof nodes / depth</dt><dd>{node['body_proof_nodes']} / {node['body_proof_depth']}</dd>
      <dt>Statement SHA-256</dt><dd><code>{_e(node['statement_sha256'])}</code></dd>
      <dt>Script SHA-256</dt><dd><code>{_e(node['sources'][0]['script_sha256'])}</code></dd>
      <dt>Proof bundle SHA-256</dt><dd><code>{_e(node['proof_bundle_sha256'])}</code></dd>
      <dt>Exact source module</dt><dd><code>{_e(node['source_module'])}</code></dd></dl>
</aside></main>"""
    return _document(family, title=f"{tag} — {name} — Defined Proof", body=body, prefix="../../../../")


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


def _graph_payload(
    family: Family, corpus: Mapping[str, Any], *, revision: str
) -> dict[str, Any]:
    theorem_nodes = [
        {
            "id": corpus["tags"][node["name"]],
            "name": node["name"],
            "kind": "theorem",
            "scope": "candidate",
            "summary": node["summary"],
            "layer": corpus["layers"][node["name"]],
            "href": _versioned(f"tag/{corpus['tags'][node['name']]}.html", revision),
            "alpha_checked_use": True,
            "alpha_edition_version": "v27",
            "alpha_first_enrolled_version": "v27",
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
        "schema": f"{SCHEMA}-graph",
        "family_slug": family.slug,
        "nodes": theorem_nodes + definition_nodes,
        "edges": corpus["edges"],
        "proof_adjacency": adjacency,
        "root_ids": [corpus["tags"][name] for name in family.roots],
        "path_policy": "proof_dependency_edges_only",
        "alpha_edition_version": "v27",
        "alpha_first_enrolled_version": "v27",
        "independent_lean_bundle_verified": True,
        "alpha_checked_use_node_count": corpus["node_count"],
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
    if (row && row.kind === "theorem" && row.alpha_checked_use) {
      kind.textContent = "Alpha v27 checked-use theorem — first admitted v27; independently kernel and Lean verified; not Stable";
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
