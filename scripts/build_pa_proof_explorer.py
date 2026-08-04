#!/usr/bin/env python3
"""Generate the replay-free, Stacks-style native PA proof explorer.

The exact quadratic-reciprocity stack supplies immutable theorem data and a
topological admission order.  This documentation builder never runs tactics,
constructs certificates, or changes the public theorem registry.
"""

from __future__ import annotations

import argparse
import ast
from collections import Counter, defaultdict
from hashlib import sha256
import html
import json
from pathlib import Path
import re
import sys
from typing import Any


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))

from peano_lab.kernel.checker import axiom_formula  # noqa: E402
from peano_lab.kernel.formulas import pretty_formula  # noqa: E402
from peano_lab.kernel import proofs as kernel_proofs  # noqa: E402
from peano_lab.library.quadratic_reciprocity_stack_runtime import (  # noqa: E402
    quadratic_reciprocity_stack,
)


OUTPUT = REPO / "book" / "_static" / "pa-proof-explorer"
TAGS = REPO / "research" / "arithmetic-library" / "pa-proof-tags.json"
INFORMAL = REPO / "research" / "arithmetic-library" / "pa-proof-informal.json"
LIBRARY = PY_ROOT / "peano_lab" / "library"
GITHUB_ROOT = "https://github.com/nasqret/vietnam2026/blob/peano-lab"
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXY"
TAG_RE = re.compile(r"^PA[0-9A-Y]{4}$")
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_']*"
PA_AXIOMS = {f"PA{i}" for i in range(1, 7)}
PINNED_UI_ASSETS = {
    "assets/explorer.css": "6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc",
    "assets/explorer.js": "98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606",
}
# Separate documentation surfaces own the conservative defined-notation
# reading edition and the private K3B CellHistory/ListAt microsite.  Keeping
# both subtrees outside this frozen explicit manifest preserves every explicit
# page and receipt byte-for-byte while allowing the three editions to share
# one stable static URL.  Neither reserved subtree enters the 557-node graph.
RESERVED_SUBTREES = {"defined", "k3b"}

EXPECTED = {
    "theorem_count": 557,
    "public_count": 241,
    "candidate_count": 316,
    "edge_count": 1787,
    "layer_count": 45,
    "formal_line_count": 27491,
    "explicit_dependency_reference_count": 8553,
    "graph_sha256": "26017364ea943c4ed51a4a83f63ff0cd56b0de3686f0e0b458e7548ee84b1253",
    "source_sha256": "23fd18aaff26e2c6b428949c35ab3658252c9a4c6fd3b4825a6ccd547f454db1",
}


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def _digest(value: bytes | str) -> str:
    return sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _javascript_assignment(name: str, value: Any) -> str:
    """Return a deterministic assignment safe inside an HTML script element."""

    if not re.fullmatch(r"[A-Z][A-Z0-9_]*", name):
        raise ValueError(f"unsafe JavaScript data name: {name!r}")
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    # JSON is valid JavaScript here.  Escaping the three HTML-sensitive ASCII
    # characters prevents any theorem metadata from ending the script element
    # or becoming markup; ensure_ascii already protects U+2028 and U+2029.
    payload = (
        payload
        .replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
    )
    return f"window.{name}={payload};"


def _pinned_ui_assets() -> dict[str, bytes]:
    """Load hand-authored UI assets only when their reviewed bytes match."""

    files = {}
    for relative, expected_sha256 in PINNED_UI_ASSETS.items():
        path = OUTPUT / relative
        if not path.is_file():
            raise ValueError(f"missing PA proof explorer UI asset: {relative}")
        payload = path.read_bytes()
        actual_sha256 = _digest(payload)
        if actual_sha256 != expected_sha256:
            raise ValueError(
                f"PA proof explorer UI asset drift for {relative}: "
                f"expected {expected_sha256}, found {actual_sha256}"
            )
        files[relative] = payload
    return files


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _base35(value: int) -> str:
    if not 0 <= value < 35**4:
        raise ValueError("PA proof-tag space exhausted")
    chars = []
    for _ in range(4):
        value, digit = divmod(value, 35)
        chars.append(ALPHABET[digit])
    return "".join(reversed(chars))


def _load_tags() -> dict[str, Any]:
    data = json.loads(TAGS.read_text(encoding="utf-8"))
    if data.get("schema") != "peano-lab-proof-tags-v1":
        raise ValueError("unknown PA proof-tag registry schema")
    assignments = data.get("assignments")
    if not isinstance(assignments, dict):
        raise ValueError("proof-tag assignments must be an object")
    values = list(assignments.values())
    if any(not isinstance(name, str) or not TAG_RE.fullmatch(tag or "") for name, tag in assignments.items()):
        raise ValueError("invalid theorem name or PA proof tag")
    if len(values) != len(set(values)):
        raise ValueError("PA proof tags must be unique")
    if data.get("alphabet") != ALPHABET or data.get("tag_pattern") != "PA[0-9A-Y]{4}":
        raise ValueError("PA proof-tag format changed")
    if type(data.get("next_value")) is not int or data["next_value"] < 1:
        raise ValueError("invalid PA proof-tag allocation cursor")
    exposed = data.get("tags")
    if exposed is not None and exposed != assignments:
        raise ValueError("exposed PA proof tags disagree with assignments")
    return data


def _update_tags(names: list[str]) -> dict[str, Any]:
    data = _load_tags()
    assignments = data["assignments"]
    used = set(assignments.values())
    cursor = data["next_value"]
    for name in names:
        if name in assignments:
            continue
        while f"PA{_base35(cursor)}" in used:
            cursor += 1
        tag = f"PA{_base35(cursor)}"
        assignments[name] = tag
        used.add(tag)
        cursor += 1
    data["next_value"] = cursor
    data["tags"] = dict(assignments)
    TAGS.write_bytes(_json_bytes(data))
    return data


def _command_spans(command: str, dependencies: set[str]) -> tuple[str, list[dict[str, Any]]]:
    match = re.match(rf"\s*({IDENT_RE})", command)
    if match is None:
        raise ValueError(f"cannot parse tactic command {command!r}")
    tactic = match.group(1)
    start = match.end()
    args = command[start:]
    spans: list[tuple[int, int]] = []
    if tactic in {"apply", "exact", "cases"}:
        found = re.fullmatch(rf"\s*({IDENT_RE})\s*", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic in {"specialize", "forall_elim"}:
        found = re.match(rf"\s*({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic == "rewrite":
        found = re.match(rf"\s*(?:(?:<-|←)\s*)?({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    elif tactic == "simp":
        stripped = args.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            offset = start + args.index("[") + 1
            body = stripped[1:-1]
            for found in re.finditer(IDENT_RE, body):
                spans.append((offset + found.start(), offset + found.end()))
    elif tactic == "use":
        found = re.match(rf"\s*({IDENT_RE})(?:\s|$)", args)
        if found:
            spans.append((start + found.start(1), start + found.end(1)))
    references = []
    for left, right in spans:
        name = command[left:right]
        kind = "theorem" if name in dependencies else "axiom" if name in PA_AXIOMS else None
        if kind:
            references.append({"kind": kind, "name": name, "start": left, "end": right})
    return tactic, references


def _literal_locations() -> dict[str, list[tuple[str, int]]]:
    found: dict[str, list[tuple[str, int]]] = defaultdict(list)
    paths = [LIBRARY / "theorems.py"] + sorted(
        path for path in LIBRARY.glob("*.py") if path.name != "theorems.py"
    )
    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        calls = sorted((node for node in ast.walk(tree) if isinstance(node, ast.Call)), key=lambda node: node.lineno)
        for node in calls:
            if not isinstance(node.func, ast.Name) or node.func.id not in {"spec", "TheoremSpec"}:
                continue
            value = node.args[0] if node.args else next((item.value for item in node.keywords if item.arg == "name"), None)
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                relative = str(path.relative_to(REPO))
                found[value.value].append((relative, node.lineno))
    return found


def _source_record(name: str, scope: str, stack: Any, locations: dict[str, list[tuple[str, int]]]) -> dict[str, Any]:
    choices = locations.get(name, [])
    owner = stack.owner_by_name.get(name) if scope == "candidate" else None
    if owner:
        owned = [row for row in choices if Path(row[0]).stem == owner]
        choices = owned or choices
    if choices:
        path, line = choices[0]
        kind = "declaration"
    else:
        entry = next(item for item in stack.source_rows if item[0] == owner)
        path = f"peano-lab/py/peano_lab/library/{owner}.py"
        line = next(item.builder.__code__.co_firstlineno for item in __import__(
            "peano_lab.library.quadratic_reciprocity_stack", fromlist=["QR_CANDIDATE_FACTORY_MANIFEST"]
        ).QR_CANDIDATE_FACTORY_MANIFEST if item.module_name == owner)
        kind = "generated_factory"
    payload = (REPO / path).read_bytes()
    return {
        "path": path,
        "line": line,
        "kind": kind,
        "owner_module": owner,
        "sha256": _digest(payload),
        "href": f"{GITHUB_ROOT}/{path}#L{line}",
    }


def _shape_guide(spec: Any, counts: Counter[str]) -> dict[str, Any]:
    if spec.dependencies:
        opening = "Use the direct prerequisites " + ", ".join(spec.dependencies) + " as previously established PA formulas."
    else:
        opening = "This root lemma is proved directly from the PA rules and the hypotheses introduced by its statement."
    moves = []
    for tactic, label in (("induction", "structural induction"), ("cases", "case analysis"), ("have", "intermediate claims"), ("rewrite", "equality transport"), ("simp", "certified simplification"), ("norm_num", "closed numeral normalization")):
        if counts[tactic]:
            moves.append(f"{label} ({counts[tactic]})")
    middle = "The proof proceeds by " + (", ".join(moves) if moves else "direct introduction and elimination") + "."
    return {
        "kind": "generated_structural_guide",
        "review": "generated",
        "title": "Structural proof guide",
        "paragraphs": [spec.summary, opening, middle],
        "reference_names": list(spec.dependencies),
    }


def _render_command(line: dict[str, Any]) -> str:
    text = line["text"]
    pieces = []
    tactic_end = len(line["tactic"])
    spans = [(0, tactic_end, "tactic", line["tactic"], None)] + [
        (ref["start"], ref["end"], ref["kind"], ref["name"], ref)
        for ref in line["references"] + line.get("axiom_references", [])
    ]
    cursor = 0
    for left, right, kind, name, reference in sorted(spans, key=lambda row: (row[0], row[1])):
        if left < cursor:
            continue
        pieces.append(_e(text[cursor:left]))
        if kind == "tactic":
            pieces.append(f'<a class="pa-tactic-ref" href="../foundations.html#tactic-{_e(name)}">{_e(name)}</a>')
        elif kind == "theorem":
            assert reference is not None
            pieces.append(f'<a class="pa-theorem-ref" href="{_e(reference["href"])}">{_e(name)}</a>')
        else:
            pieces.append(f'<a class="pa-axiom-ref" href="../foundations.html#axiom-{_e(name).lower()}">{_e(name)}</a>')
        cursor = right
    pieces.append(_e(text[cursor:]))
    return "".join(pieces)


def _page(title: str, page: str, body: str, asset_prefix: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_e(title)}</title><link rel="stylesheet" href="{asset_prefix}assets/explorer.css"><script defer src="{asset_prefix}assets/explorer.js"></script></head>
<body class="pa-proof-site" data-page="{page}">{body}</body></html>
""".encode()


def _render_index(records: list[dict[str, Any]], stack: Any) -> bytes:
    layers = "".join(f'<option value="{n}">Layer {n}</option>' for n in range(EXPECTED["layer_count"]))
    cards = []
    for row in records:
        search = " ".join((row["name"], row["tag"], row["summary"], row["status"], *[item["name"] for item in row["dependencies"]])).lower()
        cards.append(f'''<article class="pa-proof-result pa-status-{row["scope"]}" data-pa-theorem data-name="{_e(row["name"])}" data-tag="{row["tag"]}" data-status="{row["scope"]}" data-layer="{row["layer"]}" data-search="{_e(search)}"><a href="tag/{row["tag"]}.html"><code>{row["tag"]}</code> · <strong>{_e(row["name"])}</strong></a><p>{_e(row["summary"])}</p><small>layer {row["layer"]} · {len(row["lines"])} lines · {row["status_label"]}</small></article>''')
    body = f'''<header class="pa-proof-header pa-hero"><p><a href="../../arithmetic-library/quadratic-reciprocity.html">Jupyter Book</a></p><h1>Native PA Proof Explorer</h1><p>The complete replay-free reading surface for the exact quadratic-reciprocity dependency closure.</p><div class="pa-proof-stats"><b>557</b> lemmas · <b>1,787</b> edges · <b>27,491</b> tactic lines · <b>45</b> layers</div><nav><a href="foundations.html">PA language, axioms, and rules</a></nav></header>
<main data-proof-dashboard data-pa-explorer-index><section class="pa-proof-controls"><label>Search <input data-proof-search data-pa-search type="search"></label><label>Status <select data-proof-status data-pa-status><option value="all">All</option><option value="public">Public (241)</option><option value="candidate">Body-checked candidates (316)</option></select></label><label>Layer <select data-proof-layer data-pa-layer><option value="all">All 45 layers</option>{layers}</select></label><button data-proof-clear data-pa-clear type="button">Clear</button><output data-proof-count data-pa-count>557 lemmas</output></section><section class="pa-layer-map">{''.join(f'<a href="?layer={n}">{n}</a>' for n in range(45))}</section><section class="pa-proof-results">{"".join(cards)}</section></main>'''
    return _page("Native PA Proof Explorer", "index", body)


def _render_foundations(tactics: list[str]) -> bytes:
    axioms = []
    for name in sorted(PA_AXIOMS):
        formula = axiom_formula(name)
        axioms.append(f'<article id="axiom-{name.lower()}"><h3>{name}</h3><pre><code>{_e(pretty_formula(formula, []))}</code></pre></article>')
    tactic_rows = "".join(f'<li id="tactic-{_e(name)}"><a href="../../peano/tactics.html"><code>{_e(name)}</code></a></li>' for name in tactics)
    constructors = "".join(
        f"<li><code>{_e(name)}</code></li>"
        for name in kernel_proofs.__all__
        if name != "Proof"
    )
    body = f'''<header class="pa-proof-header pa-foundations-heading"><p><a href="index.html">← Proof Explorer</a></p><h1>Native PA foundations</h1><p>These are language and kernel facts, not extra number-theory lemmas; tactics are untrusted proof builders.</p></header><main><section class="pa-foundation-card" id="grammar-terms"><h2>Terms</h2><p>Terms are variables, <code>0</code>, <code>S t</code>, <code>t + u</code>, and <code>t * u</code>. Numerals are surface expansions.</p></section><section class="pa-foundation-card" id="grammar-formulas"><h2>Formulas</h2><p>Formulas use equality, bottom, implication, conjunction, disjunction, universal quantification, and existential quantification. Negation and ≤ are conservative surface expansions.</p><p>Read the <a href="../../peano/language-reference.html">full language reference</a>.</p></section><section class="pa-foundation-card"><h2>Arithmetic axioms PA1–PA6</h2>{''.join(axioms)}<article id="proof-induction"><h3>Induction</h3><p>Induction is checked for each concrete first-order motive.</p></article><article id="proof-cut"><h3>Cut</h3><p><code>Cut</code> shares a checked proof but is not an arithmetic axiom.</p></article><article id="proof-dne"><h3>DNE</h3><p><code>DNE</code> belongs only to separately labelled classical mode and is not authority for this QR stack.</p></article><p>Read <a href="../../peano/axioms-and-rules.html">axioms and proof rules in full</a>.</p></section><section class="pa-foundation-card"><h2>All native proof constructors</h2><ul>{constructors}</ul></section><section class="pa-foundation-card"><h2>Tactics occurring in this corpus</h2><ul>{tactic_rows}</ul></section></main>'''
    return _page("Native PA foundations", "foundations", body)


def _render_graph(graph: dict[str, Any]) -> bytes:
    inline_data = _javascript_assignment("PA_PROOF_GRAPH", graph)
    return ('''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Theorem dependency paths — Native PA Proof Explorer</title>
  <link rel="stylesheet" href="assets/explorer.css">
  <script id="pa-proof-graph-data">''' + inline_data + '''</script>
  <script defer src="assets/explorer.js"></script>
</head>
<body class="pa-proof-site" data-page="graph">
  <header class="pa-proof-header pa-graph-heading">
    <nav aria-label="Proof Explorer">
      <a href="index.html">Theorem index</a>
      <a href="foundations.html">PA foundations</a>
      <a href="../../arithmetic-library/quadratic-reciprocity.html">Jupyter Book</a>
    </nav>
    <p class="pa-kicker">Interactive proof map</p>
    <h1>Theorem dependency paths</h1>
    <p>Follow a premise chain into any theorem, inspect its complete prerequisite cone, or open a node’s exact native-PA proof.</p>
  </header>

  <main class="pa-graph-page" data-dependency-graph data-graph-json="api/graph.json">
    <section class="pa-graph-controls" aria-labelledby="graph-controls-title">
      <h2 id="graph-controls-title">Choose a path</h2>
      <form data-graph-form>
        <label>
          Optional start theorem
          <input data-graph-source type="search" list="pa-graph-theorems" autocomplete="off" placeholder="Automatic theorem root">
        </label>
        <label>
          Target theorem
          <input data-graph-target type="search" list="pa-graph-theorems" autocomplete="off" required placeholder="PA00FW or theorem name">
        </label>
        <label>
          View
          <select data-graph-view>
            <option value="critical">Critical/deepest premise chain</option>
            <option value="shortest">Short premise chain</option>
            <option value="corridor">All routes from start to target</option>
            <option value="prerequisites">Complete prerequisite cone</option>
            <option value="neighborhood" selected>Direct neighborhood</option>
            <option value="dependents">Complete dependent cone</option>
            <option value="corpus">Entire theorem corpus</option>
          </select>
        </label>
        <label>
          Arrows
          <select data-graph-edges>
            <option value="focus" selected>Focused: path + target</option>
            <option value="none">Hide arrows</option>
            <option value="all">All direct arrows (heavy)</option>
          </select>
        </label>
        <button type="submit">Draw path</button>
      </form>
      <datalist id="pa-graph-theorems"></datalist>
      <p class="pa-graph-control-note">The sparse view suppresses arrows visually only: exact direct relations remain in the details panel and graph data. Large views use compact clickable theorem marks. A theorem root has no <em>theorem</em> prerequisites; it is not an axiom.</p>
    </section>

    <div class="pa-graph-layout">
      <section class="pa-graph-canvas-panel" aria-labelledby="graph-canvas-title">
        <div class="pa-graph-toolbar">
          <div>
            <h2 id="graph-canvas-title">Layered dependency graph</h2>
            <p data-graph-summary aria-live="polite">Loading theorem graph…</p>
          </div>
          <div class="pa-graph-zoom" aria-label="Graph viewport controls">
            <button type="button" data-graph-zoom="in" aria-label="Zoom in">+</button>
            <button type="button" data-graph-zoom="out" aria-label="Zoom out">−</button>
            <button type="button" data-graph-center>Center target</button>
            <button type="button" data-graph-fit>Fit view</button>
          </div>
        </div>
        <div class="pa-graph-stage" data-graph-stage>
          <svg data-graph-svg tabindex="0" role="group" aria-labelledby="graph-canvas-title graph-instructions">
            <text x="24" y="42">Loading theorem graph…</text>
          </svg>
        </div>
        <p id="graph-instructions" class="pa-graph-instructions">Shown arrows run from prerequisite to dependent. Click a node or compact mark to make it the target; use its ↗ link, when shown, or the details-panel proof link to open the formal proof. Drag the background to pan. Use the buttons or Control/Command + wheel to zoom.</p>
        <div class="pa-graph-legend" aria-label="Graph legend">
          <span><i class="pa-legend-node pa-legend-selected"></i> target</span>
          <span><i class="pa-legend-node pa-legend-critical"></i> chosen chain</span>
          <span><i class="pa-legend-node pa-legend-public"></i> public theorem</span>
          <span><i class="pa-legend-node pa-legend-candidate"></i> body-checked candidate</span>
          <span><i class="pa-legend-node pa-legend-pending"></i> pending layered closure</span>
          <span><i class="pa-legend-edge pa-legend-declared"></i> declared but not cited in tactic body</span>
        </div>
      </section>

      <aside class="pa-graph-details" aria-labelledby="graph-details-title">
        <p class="pa-eyebrow">Selected theorem</p>
        <h2 id="graph-details-title" data-graph-title tabindex="-1">Loading…</h2>
        <p data-graph-status></p>
        <p data-graph-description></p>
        <dl data-graph-metadata></dl>
        <p><a class="pa-graph-proof-link" data-graph-proof href="index.html">Open the formal proof →</a></p>
        <h3>Direct prerequisites</h3>
        <ul class="pa-graph-relation-list" data-graph-dependencies></ul>
        <h3>Direct dependents</h3>
        <ul class="pa-graph-relation-list" data-graph-dependents></ul>
      </aside>
    </div>

    <section class="pa-graph-path-fallback" aria-labelledby="graph-path-title">
      <p class="pa-eyebrow">Text alternative</p>
      <h2 id="graph-path-title">Ordered premise chain</h2>
      <p data-graph-path-note>The same selected route is listed here as ordinary links.</p>
      <ol data-graph-path-list>
        <li><a href="foundations.html">PA language, arithmetic axioms, and proof rules</a> <small>foundations prelude; not a theorem node</small></li>
      </ol>
    </section>

    <noscript>
      <p class="pa-callout">The interactive graph requires JavaScript. The <a href="index.html">theorem index</a> and every formal proof remain available without it.</p>
    </noscript>
  </main>
</body>
</html>
''').encode("utf-8")


def _render_theorem(row: dict[str, Any], previous: dict[str, Any] | None, following: dict[str, Any] | None) -> bytes:
    relation = lambda items: " ".join(f'<a class="pa-theorem-ref" href="{item["tag"]}.html"><code>{item["tag"]}</code> { _e(item["name"])}</a>' for item in items) or "none"
    paragraphs = "".join(f"<p>{_e(text)}</p>" for text in row["informal"]["paragraphs"])
    ingredients = " ".join(
        f'<a class="pa-informal-ref" href="{_e(item["href"])}"><code>{_e(item["tag"])}</code> {_e(item["name"])}</a>'
        for item in row["informal"]["references"]
    ) or "none"
    lines = []
    for line in row["lines"]:
        lines.append(f'<li class="pa-proof-line" id="{line["id"]}" data-line="{line["number"]}" data-tactic="{_e(line["tactic"])}" data-line-id="{line["stable_id"]}"><a class="pa-line-number" href="#{line["id"]}">{line["number"]:04d}</a><code>{_render_command(line)}</code></li>')
    prev_link = f'<a href="{previous["tag"]}.html">← { _e(previous["name"])}</a>' if previous else ""
    next_link = f'<a href="{following["tag"]}.html">{ _e(following["name"])} →</a>' if following else ""
    body = f'''<header class="pa-proof-header pa-theorem-heading"><nav><a href="../index.html">Explorer</a> · <a href="../foundations.html">Foundations</a> {prev_link} {next_link}</nav><p class="pa-tag">{row["tag"]}</p><h1>{_e(row["name"])}</h1><p class="pa-status-{row["scope"]}">{_e(row["status_label"])}</p><p>{_e(row["summary"])}</p></header><main class="pa-theorem-layout"><div class="pa-proof-panel"><section class="pa-statement"><h2>Exact expanded PA statement</h2><button data-copy-target="statement" type="button">Copy</button><pre id="statement"><code>{_e(row["statement"])}</code></pre></section><section class="pa-informal-proof" data-informal-kind="{_e(row["informal"]["kind"])}" data-informal-review="{_e(row["informal"]["review"])}"><h2>{_e(row["informal"]["title"])}</h2><p><strong>{"Curated informal proof" if row["informal"]["review"] == "curated_reviewed" else "Generated structural guide"}</strong></p>{paragraphs}<h3>Referenced ingredients</h3><div class="pa-chip-row">{ingredients}</div></section><section><h2>Proof neighborhood</h2><h3>Direct dependencies</h3><div class="pa-chip-row">{relation(row["dependencies"])}</div><h3>Direct dependents</h3><div class="pa-chip-row">{relation(row["dependents"])}</div></section><section><h2>Formal native tactic body</h2><p>Dependencies are introduced as named hypotheses before line 1. Linked names are exact direct references. This {"body-checked candidate is not publicly admitted" if row["scope"] == "candidate" else "public theorem is independently kernel-checked when replayed"}.</p><ol class="pa-formal-proof">{"".join(lines)}</ol></section></div><aside class="pa-proof-sidebar pa-trust-panel"><h2>Receipt and source provenance</h2><dl><dt>Layer</dt><dd>{row["layer"]}</dd><dt>Lines</dt><dd>{len(row["lines"])}</dd><dt>Specification SHA-256</dt><dd><code>{row["spec_sha256"]}</code></dd><dt>Source</dt><dd><a href="{_e(row["source"]["href"])}">{_e(row["source"]["path"])}:{row["source"]["line"]}</a> ({row["source"]["kind"]})</dd><dt>Source SHA-256</dt><dd><code>{row["source"]["sha256"]}</code></dd></dl></aside></main>'''
    return _page(f'{row["tag"]} — {row["name"]}', "theorem", body, "../")


def _dependency_graph_payload(
    records: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    """Build the deterministic query model consumed by the graph explorer.

    Every edge is directed from a prerequisite to a theorem which uses it.
    The admission order is already a topological order.  We use that same
    stable order for every tag array, including transitive closures and the
    tie-break between equally short foundation paths.
    """

    tags = [row["tag"] for row in records]
    rank = {tag: index for index, tag in enumerate(tags)}
    layer_by_tag = {row["tag"]: row["layer"] for row in records}
    if len(rank) != len(tags):
        raise ValueError("dependency graph tags must be unique")

    dependencies: dict[str, list[str]] = {}
    dependents: dict[str, list[str]] = {tag: [] for tag in tags}
    for row in records:
        tag = row["tag"]
        direct = sorted(
            (dependency["tag"] for dependency in row["dependencies"]),
            key=rank.__getitem__,
        )
        if len(direct) != len(set(direct)):
            raise ValueError(f"duplicate dependency for {tag}")
        if any(rank[dependency] >= rank[tag] for dependency in direct):
            raise ValueError(f"dependency graph is not topologically ordered at {tag}")
        dependencies[tag] = direct
        for dependency in direct:
            dependents[dependency].append(tag)

    edge_pairs = {
        (edge["dependency"], edge["dependent"])
        for edge in edges
    }
    adjacency_pairs = {
        (dependency, tag)
        for tag, direct in dependencies.items()
        for dependency in direct
    }
    if len(edge_pairs) != len(edges) or edge_pairs != adjacency_pairs:
        raise ValueError("edge list and direct adjacency disagree")

    ancestors: dict[str, set[str]] = {}
    shortest_root_paths: dict[str, list[str]] = {}
    critical_root_paths: dict[str, list[str]] = {}
    root_path_counts: dict[str, int] = {}
    for tag in tags:
        closure: set[str] = set()
        for dependency in dependencies[tag]:
            closure.add(dependency)
            closure.update(ancestors[dependency])
        ancestors[tag] = closure
        if dependencies[tag]:
            shortest_candidates = [
                [*shortest_root_paths[dependency], tag]
                for dependency in dependencies[tag]
            ]
            shortest_root_paths[tag] = min(
                shortest_candidates,
                key=lambda path: (len(path), tuple(rank[item] for item in path)),
            )
            critical_candidates = [
                [*critical_root_paths[dependency], tag]
                for dependency in dependencies[tag]
            ]
            critical_root_paths[tag] = min(
                critical_candidates,
                key=lambda path: (-len(path), tuple(rank[item] for item in path)),
            )
            root_path_counts[tag] = sum(
                root_path_counts[dependency]
                for dependency in dependencies[tag]
            )
        else:
            shortest_root_paths[tag] = [tag]
            critical_root_paths[tag] = [tag]
            root_path_counts[tag] = 1
        if len(critical_root_paths[tag]) != layer_by_tag[tag] + 1:
            raise ValueError(f"critical root path does not witness layer depth at {tag}")

    descendants: dict[str, set[str]] = {}
    for tag in reversed(tags):
        closure = set()
        for dependent in dependents[tag]:
            closure.add(dependent)
            closure.update(descendants[dependent])
        descendants[tag] = closure

    layers_by_index: dict[int, list[str]] = defaultdict(list)
    for row in records:
        layers_by_index[row["layer"]].append(row["tag"])
    expected_layers = list(range(receipt["layer_count"]))
    if sorted(layers_by_index) != expected_layers:
        raise ValueError("dependency graph layers are not contiguous")

    foundations = [tag for tag in tags if not dependencies[tag]]
    terminals = [tag for tag in tags if not dependents[tag]]
    adjacency = {
        tag: {
            "dependencies": dependencies[tag],
            "dependents": dependents[tag],
            "ancestors": sorted(ancestors[tag], key=rank.__getitem__),
            "descendants": sorted(descendants[tag], key=rank.__getitem__),
            # Compatibility alias for the first graph UI prototype.
            "foundation_path": shortest_root_paths[tag],
            "shortest_root_path": shortest_root_paths[tag],
            "critical_root_path": critical_root_paths[tag],
            "root_path_count": root_path_counts[tag],
        }
        for tag in tags
    }
    return {
        "schema": "peano-lab-pa-proof-graph-v2",
        **receipt,
        "orientation": "dependency_to_dependent",
        "path_policy": {
            "foundation_path_alias": "shortest_root_path",
            "shortest_root_path": "fewest_edges_from_any_foundation",
            "critical_root_path": "dependency_depth_witness",
            "tie_break": "admission_order_lexicographic",
            "includes_endpoints": True,
        },
        "foundations": foundations,
        "terminals": terminals,
        "layers": [
            {"index": index, "nodes": layers_by_index[index]}
            for index in expected_layers
        ],
        "nodes": [
            {
                key: row[key]
                for key in ("tag", "name", "scope", "status", "layer", "summary")
            }
            | {"href": f'../tag/{row["tag"]}.html'}
            for row in records
        ],
        "edges": edges,
        "adjacency": adjacency,
    }


def _dependency_graph_schema() -> dict[str, Any]:
    """JSON Schema for the public v2 dependency-graph payload."""

    tag = {"type": "string", "pattern": r"^PA[0-9A-Y]{4}$"}
    tag_array = {
        "type": "array",
        "items": {"$ref": "#/$defs/tag"},
        "uniqueItems": True,
    }
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "urn:peano-lab:pa-proof-graph-v2",
        "title": "Peano Lab native-PA proof dependency graph",
        "type": "object",
        "additionalProperties": False,
        "required": [
            "schema", "theorem_count", "public_count", "candidate_count",
            "edge_count", "layer_count", "formal_line_count",
            "explicit_dependency_reference_count", "graph_sha256",
            "source_sha256", "orientation", "path_policy", "foundations",
            "terminals", "layers", "nodes", "edges", "adjacency",
        ],
        "properties": {
            "schema": {"const": "peano-lab-pa-proof-graph-v2"},
            "theorem_count": {"type": "integer", "minimum": 0},
            "public_count": {"type": "integer", "minimum": 0},
            "candidate_count": {"type": "integer", "minimum": 0},
            "edge_count": {"type": "integer", "minimum": 0},
            "layer_count": {"type": "integer", "minimum": 0},
            "formal_line_count": {"type": "integer", "minimum": 0},
            "explicit_dependency_reference_count": {"type": "integer", "minimum": 0},
            "graph_sha256": {"$ref": "#/$defs/sha256"},
            "source_sha256": {"$ref": "#/$defs/sha256"},
            "orientation": {"const": "dependency_to_dependent"},
            "path_policy": {"$ref": "#/$defs/path_policy"},
            "foundations": {"$ref": "#/$defs/tag_array"},
            "terminals": {"$ref": "#/$defs/tag_array"},
            "layers": {
                "type": "array",
                "items": {"$ref": "#/$defs/layer"},
            },
            "nodes": {
                "type": "array",
                "items": {"$ref": "#/$defs/node"},
            },
            "edges": {
                "type": "array",
                "items": {"$ref": "#/$defs/edge"},
            },
            "adjacency": {
                "type": "object",
                "patternProperties": {
                    r"^PA[0-9A-Y]{4}$": {"$ref": "#/$defs/neighborhood"},
                },
                "additionalProperties": False,
            },
        },
        "$defs": {
            "tag": tag,
            "tag_array": tag_array,
            "sha256": {"type": "string", "pattern": r"^[0-9a-f]{64}$"},
            "path_policy": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "foundation_path_alias", "shortest_root_path",
                    "critical_root_path", "tie_break", "includes_endpoints",
                ],
                "properties": {
                    "foundation_path_alias": {"const": "shortest_root_path"},
                    "shortest_root_path": {"const": "fewest_edges_from_any_foundation"},
                    "critical_root_path": {"const": "dependency_depth_witness"},
                    "tie_break": {"const": "admission_order_lexicographic"},
                    "includes_endpoints": {"const": True},
                },
            },
            "layer": {
                "type": "object",
                "additionalProperties": False,
                "required": ["index", "nodes"],
                "properties": {
                    "index": {"type": "integer", "minimum": 0},
                    "nodes": {"$ref": "#/$defs/tag_array"},
                },
            },
            "node": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "tag", "name", "scope", "status", "layer", "summary", "href",
                ],
                "properties": {
                    "tag": {"$ref": "#/$defs/tag"},
                    "name": {"type": "string", "minLength": 1},
                    "scope": {"enum": ["public", "candidate"]},
                    "status": {
                        "enum": [
                            "public", "candidate_body_checked", "pending_layered_closure",
                        ],
                    },
                    "layer": {"type": "integer", "minimum": 0},
                    "summary": {"type": "string", "minLength": 1},
                    "href": {"type": "string", "pattern": r"^\.\./tag/PA[0-9A-Y]{4}\.html$"},
                },
            },
            "edge": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dependency", "dependency_name", "dependent", "dependent_name",
                    "body_reference", "explicit_reference_count",
                ],
                "properties": {
                    "dependency": {"$ref": "#/$defs/tag"},
                    "dependency_name": {"type": "string", "minLength": 1},
                    "dependent": {"$ref": "#/$defs/tag"},
                    "dependent_name": {"type": "string", "minLength": 1},
                    "body_reference": {"type": "boolean"},
                    "explicit_reference_count": {"type": "integer", "minimum": 0},
                },
            },
            "neighborhood": {
                "type": "object",
                "additionalProperties": False,
                "required": [
                    "dependencies", "dependents", "ancestors", "descendants",
                    "foundation_path", "shortest_root_path", "critical_root_path",
                    "root_path_count",
                ],
                "properties": {
                    "dependencies": {"$ref": "#/$defs/tag_array"},
                    "dependents": {"$ref": "#/$defs/tag_array"},
                    "ancestors": {"$ref": "#/$defs/tag_array"},
                    "descendants": {"$ref": "#/$defs/tag_array"},
                    "foundation_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "shortest_root_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "critical_root_path": {
                        "allOf": [
                            {"$ref": "#/$defs/tag_array"},
                            {"minItems": 1},
                        ],
                    },
                    "root_path_count": {"type": "integer", "minimum": 1},
                },
            },
        },
    }


def build() -> tuple[dict[str, bytes], dict[str, Any]]:
    stack = quadratic_reciprocity_stack()
    specs = list(stack.admission_order)
    names = [spec.name for spec in specs]
    tags_data = _load_tags()
    missing = [name for name in names if name not in tags_data["assignments"]]
    if missing:
        raise ValueError(f"missing {len(missing)} persistent proof tags; run --update-tags")
    tags = tags_data["assignments"]
    overrides = json.loads(INFORMAL.read_text(encoding="utf-8"))["overrides"]
    public = {spec.name for spec in stack.public_order}
    candidate = {spec.name for spec in stack.candidate_order}
    by_name = {spec.name: spec for spec in specs}
    dependents: dict[str, list[str]] = {name: [] for name in names}
    for spec in specs:
        for dependency in spec.dependencies:
            dependents[dependency].append(spec.name)
    locations = _literal_locations()
    edge_reference_counts: Counter[tuple[str, str]] = Counter()
    records = []
    all_tactics: Counter[str] = Counter()
    total_lines = 0
    total_refs = 0
    for index, spec in enumerate(specs):
        scope = "public" if spec.name in public else "candidate"
        counts: Counter[str] = Counter()
        occurrence: Counter[str] = Counter()
        lines = []
        for number, command in enumerate(spec.script, 1):
            tactic, references = _command_spans(command, set(spec.dependencies))
            counts[tactic] += 1
            all_tactics[tactic] += 1
            occurrence[command] += 1
            theorem_references = []
            axiom_references = []
            for reference in references:
                if reference["kind"] == "theorem":
                    reference["tag"] = tags[reference["name"]]
                    reference["href"] = f'{tags[reference["name"]]}.html'
                    edge_reference_counts[(spec.name, reference["name"])] += 1
                    total_refs += 1
                    theorem_references.append(reference)
                else:
                    reference["href"] = f'../foundations.html#axiom-{reference["name"].lower()}'
                    axiom_references.append(reference)
            lines.append({
                "id": f"proof-line-{number:04d}",
                "number": number,
                "text": command,
                "tactic": tactic,
                "tactic_href": f"../foundations.html#tactic-{tactic}",
                "stable_id": _digest(f"{spec.name}\x1f{command}\x1f{occurrence[command]}")[:16],
                "references": theorem_references,
                "axiom_references": axiom_references,
            })
        total_lines += len(lines)
        informal = overrides.get(spec.name) or _shape_guide(spec, counts)
        if spec.name in overrides:
            informal = {
                "kind": "curated_override",
                "review": "curated_reviewed",
                **informal,
                "reference_names": list(informal.get("references", ())),
            }
            informal.pop("references", None)
        reference_names = informal.pop("reference_names")
        if len(reference_names) != len(set(reference_names)):
            raise ValueError(f"duplicate informal reference for {spec.name}")
        unknown_informal = [name for name in reference_names if name not in by_name]
        if unknown_informal:
            raise ValueError(
                f"unknown informal reference(s) for {spec.name}: {unknown_informal!r}"
            )
        informal["references"] = [
            {"name": name, "tag": tags[name], "href": f"{tags[name]}.html"}
            for name in reference_names
        ]
        payload = "\x1f".join((scope, spec.name, spec.statement, "\x1e".join(spec.script), "\x1e".join(spec.dependencies)))
        records.append({
            "index": index,
            "tag": tags[spec.name],
            "name": spec.name,
            "scope": scope,
            "status": (
                "public"
                if scope == "public"
                else "pending_layered_closure"
                if spec.name == "quadratic_reciprocity_combined"
                else "candidate_body_checked"
            ),
            "status_label": (
                "public native theorem"
                if scope == "public"
                else "pending layered closure — body-checked candidate; not publicly admitted"
                if spec.name == "quadratic_reciprocity_combined"
                else "body-checked candidate; not publicly admitted"
            ),
            "layer": stack.dependency_depth_by_name[spec.name],
            "summary": spec.summary,
            "statement": spec.statement,
            "statement_sha256": _digest(spec.statement),
            "script_sha256": _digest("\n".join(spec.script)),
            "spec_sha256": _digest(payload),
            "dependencies": [],
            "dependents": [],
            "lines": lines,
            "informal": informal,
            "source": _source_record(spec.name, scope, stack, locations),
        })
    edges = []
    for row in records:
        spec = by_name[row["name"]]
        row["dependencies"] = [{
            "name": name, "tag": tags[name], "href": f'{tags[name]}.html',
            "body_reference": edge_reference_counts[(row["name"], name)] > 0,
            "explicit_reference_count": edge_reference_counts[(row["name"], name)],
        } for name in spec.dependencies]
        row["dependents"] = [{
            "name": name, "tag": tags[name], "href": f'{tags[name]}.html',
            "body_reference": edge_reference_counts[(name, row["name"])] > 0,
            "explicit_reference_count": edge_reference_counts[(name, row["name"])],
        } for name in dependents[row["name"]]]
        for dependency in row["dependencies"]:
            edges.append({
                "dependency": dependency["tag"], "dependency_name": dependency["name"],
                "dependent": row["tag"], "dependent_name": row["name"],
                "body_reference": dependency["body_reference"],
                "explicit_reference_count": dependency["explicit_reference_count"],
            })
    actual = {
        "theorem_count": len(records), "public_count": len(public), "candidate_count": len(candidate),
        "edge_count": len(edges), "layer_count": len(stack.dependency_layers), "formal_line_count": total_lines,
        "explicit_dependency_reference_count": total_refs, "graph_sha256": stack.graph_sha256,
        "source_sha256": stack.source_sha256,
    }
    if actual != EXPECTED:
        raise ValueError(f"QR proof explorer receipt changed: {actual!r}")
    corpus = {"schema": "peano-lab-pa-proof-corpus-v1", **actual, "theorems": records}
    graph = _dependency_graph_payload(records, edges, actual)
    graph_schema = _dependency_graph_schema()
    files: dict[str, bytes] = {
        "index.html": _render_index(records, stack),
        "foundations.html": _render_foundations(sorted(all_tactics)),
        "graph.html": _render_graph(graph),
        "api/corpus.json": _json_bytes(corpus),
        "api/graph.json": _json_bytes(graph),
        "api/graph.schema.json": _json_bytes(graph_schema),
        **_pinned_ui_assets(),
    }
    for index, row in enumerate(records):
        files[f'tag/{row["tag"]}.html'] = _render_theorem(row, records[index - 1] if index else None, records[index + 1] if index + 1 < len(records) else None)
        target = f'../tag/{row["tag"]}.html'
        files[f'name/{row["name"]}.html'] = f'''<!doctype html><html><head><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={target}"><link rel="canonical" href="{target}"><script>location.replace({json.dumps(target)}+location.search+location.hash)</script></head><body><a href="{target}">{_e(row["name"])}</a></body></html>\n'''.encode()
    manifest_files = [{"path": path, "bytes": len(payload), "sha256": _digest(payload)} for path, payload in sorted(files.items())]
    aggregate = _digest("\n".join(f'{item["path"]}\0{item["sha256"]}' for item in manifest_files))
    manifest = {
        "schema": "peano-lab-pa-proof-explorer-manifest-v1", **actual,
        "generated_file_count": len(files) + 1,
        "canonical_tag_page_count": len(records), "name_alias_page_count": len(records),
        "aggregate_sha256": aggregate,
        "tag_registry_sha256": _digest(TAGS.read_bytes()),
        "informal_overrides_sha256": _digest(INFORMAL.read_bytes()),
        "required_assets": ["assets/explorer.css", "assets/explorer.js"],
        "files": manifest_files,
    }
    files["manifest.json"] = _json_bytes(manifest)
    return files, manifest


def _write(files: dict[str, bytes]) -> None:
    for relative, payload in files.items():
        path = OUTPUT / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    expected = set(files)
    if OUTPUT.exists():
        for path in OUTPUT.rglob("*"):
            relative = path.relative_to(OUTPUT)
            if (
                path.is_file()
                and (not relative.parts or relative.parts[0] not in RESERVED_SUBTREES)
                and str(relative) not in expected
            ):
                path.unlink()


def _check(files: dict[str, bytes]) -> bool:
    drift = []
    for relative, payload in files.items():
        path = OUTPUT / relative
        if not path.is_file() or path.read_bytes() != payload:
            drift.append(relative)
    expected = set(files)
    if OUTPUT.exists():
        drift.extend(
            str(path.relative_to(OUTPUT))
            for path in OUTPUT.rglob("*")
            if path.is_file()
            and (
                not path.relative_to(OUTPUT).parts
                or path.relative_to(OUTPUT).parts[0] not in RESERVED_SUBTREES
            )
            and str(path.relative_to(OUTPUT)) not in expected
        )
    if drift:
        print("PA proof explorer drift: " + ", ".join(sorted(set(drift))[:20]), file=sys.stderr)
        return False
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--check", action="store_true")
    modes.add_argument("--update-tags", action="store_true")
    args = parser.parse_args(argv)
    stack = quadratic_reciprocity_stack()
    if args.update_tags:
        _update_tags([spec.name for spec in stack.admission_order])
    files, manifest = build()
    if args.check:
        if not _check(files):
            return 1
        print(f'verified PA proof explorer: {manifest["generated_file_count"]} files, {manifest["aggregate_sha256"]}')
        return 0
    _write(files)
    print(f'wrote PA proof explorer: {manifest["generated_file_count"]} files, {manifest["aggregate_sha256"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
