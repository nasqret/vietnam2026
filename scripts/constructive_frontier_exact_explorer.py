"""Canonical exact-reading pages for constructive candidate proof families.

These renderers deliberately consume already-built, evidence-labeled corpus
records. They never replay proofs, construct certificates, or change theorem
admission. Their HTML follows the pinned native-PA exact explorer so its
reviewed stylesheet and JavaScript can be reused without modification.
"""

from __future__ import annotations

from collections.abc import Mapping
from hashlib import sha256
import html
import re
from typing import Any


_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_']*")


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _layer(
    node: Mapping[str, Any],
    tags: Mapping[str, str],
    layers: Mapping[str, int],
) -> int:
    """Accept name-keyed layers, with tag-keyed maps as a harmless fallback."""

    name = str(node["name"])
    return int(layers.get(name, layers.get(tags[name], 0)))


def _candidate_label(node: Mapping[str, Any]) -> str:
    if node.get("enrolled_in_alpha"):
        edition = str(node.get("alpha_edition_version") or "Alpha")
        evidence = str(node.get("alpha_evidence") or "body_checked")
        return f"Alpha {edition} enrolled · {evidence}; no checked-use authority"
    return "Dependency-curried candidate body; not Alpha-enrolled; no checked-use authority"


def _external_label(row: Mapping[str, Any] | None) -> str:
    if row is None:
        return "external prerequisite; evidence not asserted"
    if row.get("admitted_to_stable"):
        return "Stable theorem; checked-use authorized"
    if row.get("alpha_checked_use"):
        return "Alpha theorem; checked-use authorized"
    if row.get("enrolled_in_alpha"):
        evidence = str(row.get("alpha_evidence") or "body_checked")
        return f"Alpha {evidence}; no checked-use authority"
    evidence = str(row.get("evidence") or "dependency-curried-candidate-body")
    return f"external {evidence}; no checked-use authority"


def _page(
    *,
    family: Any,
    title: str,
    page: str,
    body: str,
    stylesheet_href: str,
    script_href: str,
) -> bytes:
    document = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{_escape(title)}</title>
  <link rel="stylesheet" href="{_escape(stylesheet_href)}">
  <script defer src="{_escape(script_href)}"></script>
</head>
<body class="pa-proof-site" data-page="{_escape(page)}" data-family="{_escape(family.slug)}">{body}</body>
</html>
"""
    return document.encode("utf-8")


def render_exact_index(
    family: Any,
    corpus: Mapping[str, Any],
    tags: Mapping[str, str],
    layers: Mapping[str, int],
    *,
    stylesheet_href: str,
    script_href: str,
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
            f'data-status="candidate" data-layer="{layer}" '
            f'data-search="{_escape(searchable)}">'
            f'<a href="tag/{_escape(tag)}.html"><code>{_escape(tag)}</code> · '
            f'<strong>{_escape(name)}</strong></a>'
            f'<p>{_escape(node["summary"])}</p>'
            f'<small>layer {layer} · {len(node["script"])} lines · '
            f'{_escape(status)}</small></article>'
        )

    root = str(corpus["root_names"][-1])
    root_tag = tags[root]
    count = len(nodes)
    layer_count = len(layer_numbers)
    layer_links = "".join(
        f'<a href="?layer={number}">{number}</a>'
        for number in layer_numbers
    )
    body = f"""<header class="pa-proof-header pa-hero">
  <nav><a href="../">{_escape(family.title)}</a><a href="defined/">Defined notation</a><a href="defined/graph.html?target={_escape(root_tag)}">Dependency graph</a></nav>
  <h1>{_escape(family.title)} — Exact Proof Explorer</h1>
  <p>{_escape(family.description)}</p>
  <div class="pa-proof-stats"><b>{count}</b> theorem bodies · <b>{corpus['edge_count']}</b> proof edges · <b>{corpus['formal_line_count']}</b> tactic lines · <b>{layer_count}</b> layers</div>
  <p class="pa-status-candidate">{_escape(corpus['candidate_status'])}</p>
</header>
<main data-proof-dashboard data-pa-explorer-index>
  <section class="pa-proof-controls"><label>Search <input data-proof-search data-pa-search type="search"></label><label>Status <select data-proof-status data-pa-status><option value="all">All</option><option value="candidate">Body-checked candidates ({count})</option></select></label><label>Layer <select data-proof-layer data-pa-layer><option value="all">All {layer_count} layers</option>{layer_options}</select></label><button data-proof-clear data-pa-clear type="button">Clear</button><output data-proof-count data-pa-count>{count} theorems</output></section>
  <section class="pa-layer-map">{layer_links}</section>
  <section class="pa-proof-results">{"".join(cards)}</section>
  <p class="pa-callout">Every displayed theorem is a dependency-curried candidate body. Alpha enrollment never grants checked theorem use, empty-context closure, or Stable membership.</p>
</main>"""
    return _page(
        family=family,
        title=f"{family.title} — Exact Proof Explorer",
        page="index",
        body=body,
        stylesheet_href=stylesheet_href,
        script_href=script_href,
    )


def _relation(
    names: tuple[str, ...],
    *,
    tags: Mapping[str, str],
    external: Mapping[str, Mapping[str, Any]],
) -> str:
    if not names:
        return '<span class="pa-empty">none</span>'
    parts: list[str] = []
    for name in names:
        if name in tags:
            tag = tags[name]
            parts.append(
                f'<a class="pa-theorem-ref" href="{_escape(tag)}.html">'
                f'<code>{_escape(tag)}</code> {_escape(name)}</a>'
            )
            continue
        evidence = _external_label(external.get(name))
        parts.append(
            '<span class="pa-external-dependency" '
            f'data-external-name="{_escape(name)}" '
            f'data-evidence="{_escape(str((external.get(name) or {}).get("evidence", "unknown")))}">'
            f'<code>{_escape(name)}</code> '
            f'<small>{_escape(evidence)}</small></span>'
        )
    return " ".join(parts)


def _render_command(
    command: str,
    *,
    tags: Mapping[str, str],
    dependencies: set[str],
) -> tuple[str, str]:
    """Link actual local prerequisite tokens without rewriting proof text."""

    pieces: list[str] = []
    cursor = 0
    tactic = ""
    for match in _IDENTIFIER.finditer(command):
        pieces.append(_escape(command[cursor:match.start()]))
        token = match.group()
        if not tactic:
            tactic = token
            pieces.append(f'<span class="pa-tactic-ref">{_escape(token)}</span>')
        elif token in dependencies and token in tags:
            pieces.append(
                f'<a class="pa-theorem-ref" href="{_escape(tags[token])}.html">'
                f'{_escape(token)}</a>'
            )
        elif token in dependencies:
            pieces.append(f'<span class="pa-external-ref">{_escape(token)}</span>')
        else:
            pieces.append(_escape(token))
        cursor = match.end()
    pieces.append(_escape(command[cursor:]))
    return "".join(pieces), tactic


def render_exact_theorem(
    family: Any,
    corpus: Mapping[str, Any],
    node: Mapping[str, Any],
    tags: Mapping[str, str],
    layers: Mapping[str, int],
    *,
    stylesheet_href: str,
    script_href: str,
) -> bytes:
    """Render one lightweight, canonical, evidence-honest exact proof page."""

    name = str(node["name"])
    tag = tags[name]
    node_names = tuple(str(item["name"]) for item in corpus["nodes"])
    index = node_names.index(name)
    previous = node_names[index - 1] if index else None
    following = node_names[index + 1] if index + 1 < len(node_names) else None
    previous_link = (
        f'<a href="{_escape(tags[previous])}.html">← {_escape(previous)}</a>'
        if previous is not None
        else ""
    )
    following_link = (
        f'<a href="{_escape(tags[following])}.html">{_escape(following)} →</a>'
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
            command, tags=tags, dependencies=dependency_names
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
    alpha_evidence = (
        str(node.get("alpha_evidence") or "body_checked")
        if node.get("enrolled_in_alpha")
        else "not enrolled"
    )
    experiment = (
        '<p class="pa-callout">Historical empty-context replay experiment only; '
        'no persisted certificate, checked-use authority, or Stable promotion.</p>'
        if node.get("experimental_closure_verified")
        else ""
    )
    layer = _layer(node, tags, layers)
    body = f"""<header class="pa-proof-header pa-theorem-heading">
  <nav><a href="../index.html">Explorer</a><a href="../defined/tag/{_escape(tag)}.html">Defined notation</a><a href="../defined/graph.html?target={_escape(tag)}">Dependency graph</a>{previous_link}{following_link}</nav>
  <p class="pa-tag">{_escape(tag)}</p><h1>{_escape(name)}</h1>
  <p class="pa-status-candidate">{_escape(_candidate_label(node))}</p>
  <p>{_escape(node['summary'])}</p>
</header>
<main class="pa-theorem-layout">
  <div class="pa-proof-panel">
    <section class="pa-statement"><h2>Exact expanded first-order arithmetic statement</h2><button data-copy-target="statement" type="button">Copy</button><pre id="statement"><code>{_escape(node['statement'])}</code></pre></section>
    <section class="pa-informal-proof" data-informal-kind="structural" data-informal-review="generated"><h2>Constructive proof overview</h2><p><strong>Generated structural guide</strong></p><p>{_escape(node['summary'])}</p><p>The unchanged tactic script uses {len(dependencies)} declared prerequisite{'s' if len(dependencies) != 1 else ''} and contains {len(lines)} exact native proof lines.</p><p>{_escape(corpus['candidate_status'])}</p>{experiment}</section>
    <section><h2>Proof neighborhood</h2><h3>Direct dependencies</h3><div class="pa-chip-row">{_relation(dependencies, tags=tags, external=external)}</div><h3>Direct dependents</h3><div class="pa-chip-row">{_relation(dependents, tags=tags, external=external)}</div></section>
    <section><h2>Formal native tactic body</h2><p>Dependencies are introduced as named hypotheses before line 1. Local theorem links identify exact declared prerequisites. This dependency-curried candidate body does not grant checked theorem use or Stable membership.</p><ol class="pa-formal-proof">{"".join(lines)}</ol></section>
  </div>
  <aside class="pa-proof-sidebar pa-trust-panel"><h2>Receipt and source provenance</h2><dl><dt>Proof layer</dt><dd>{layer}</dd><dt>Tactic lines</dt><dd>{len(lines)}</dd><dt>Alpha evidence</dt><dd>{_escape(alpha_evidence)}</dd><dt>Checked-use authority</dt><dd>none</dd><dt>Stable membership</dt><dd>none</dd><dt>Exact statement SHA-256</dt><dd><code>{_escape(node['statement_sha256'])}</code></dd><dt>Exact script SHA-256</dt><dd><code>{_escape(source.get('script_sha256', 'not recorded'))}</code></dd><dt>Source module</dt><dd><code>{_escape(source.get('source_module', node.get('source_module', 'not recorded')))}</code></dd><dt>Factory</dt><dd><code>{_escape(source.get('factory', node.get('factory', 'not recorded')))}</code></dd></dl></aside>
</main>"""
    return _page(
        family=family,
        title=f"{tag} — {name} — Exact Proof",
        page="theorem",
        body=body,
        stylesheet_href=stylesheet_href,
        script_href=script_href,
    )
