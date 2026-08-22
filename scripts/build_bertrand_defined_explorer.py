#!/usr/bin/env python3
"""Build the conservative, definition-aware edition of the Bertrand proof.

The immutable input is the already generated, complete 544-theorem Bertrand
proof explorer.  Statements and the propositions of ``have``/``suffices``
commands are compacted by a reviewed notation adapter, which verifies exact
expanded-AST equivalence.  Neither this script nor its output checks proofs,
changes theorem authority, or writes to the explicit explorer.

``peano_lab.library.bertrand_defined_edition`` supplies the campaign-specific
conservative definitions.  Its absence or an incomplete campaign registry is
a hard error: silently publishing a generic arithmetic edition would conceal
the very Bertrand concepts this reading surface is meant to expose.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
import importlib
import json
from pathlib import Path
import sys
from typing import Any

import build_pa_defined_explorer as shared


REPO = Path(__file__).resolve().parents[1]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))

EXPLICIT = REPO / "book" / "_static" / "bertrand-proof-explorer"
EXPLICIT_CORPUS = EXPLICIT / "api" / "corpus.json"
EXPLICIT_GRAPH = EXPLICIT / "api" / "graph.json"
OUTPUT = EXPLICIT / "defined"
ASSET_SOURCE = REPO / "book" / "_static" / "pa-proof-explorer" / "defined"
CAMPAIGN_ADAPTER = "peano_lab.library.bertrand_defined_edition"
ROOT_NAME = "bertrand_strict"
ROOT_TAG = "BT0127"
GITHUB_ROOT = (
    "https://github.com/nasqret/vietnam2026/blob/"
    "agent/new-theorems-tranche-01"
)

EXPECTED = {
    "corpus_schema": "peano-lab-bertrand-proof-corpus-v1",
    "graph_schema": "peano-lab-bertrand-proof-graph-v1",
    "corpus_sha256": (
        "dddbb6dbbc0d57611fb46c30711c335b430593740df830eb47e5c399e4239d9f"
    ),
    "graph_sha256": (
        "ccca81cee158faaeb338f6abe2034193b39ea8403bddc248f98048f31b705ba7"
    ),
    "theorem_count": 544,
    "proof_edge_count": 1917,
    "formal_line_count": 28410,
}

DefinedEditionError = shared.DefinedEditionError
REQUIRED_CAMPAIGN_DEFINITIONS = frozenset(
    {
        "Choose",
        "CentralBinom",
        "Primorial",
        "PowerValuation",
        "FactorialValuation",
        "LegendreSum",
        "FloorSqrt",
    }
)


def _adapter() -> Any:
    """Fail closed unless the reviewed Bertrand notation adapter is available."""

    try:
        module = importlib.import_module(CAMPAIGN_ADAPTER)
    except ModuleNotFoundError as error:
        if error.name == CAMPAIGN_ADAPTER:
            raise DefinedEditionError(
                f"missing required Bertrand campaign adapter {CAMPAIGN_ADAPTER}"
            ) from error
        raise
    required = (
        "definition_json_records",
        "compact_formula_source",
        "compact_tactic_command",
    )
    missing = [name for name in required if not callable(getattr(module, name, None))]
    if missing:
        raise DefinedEditionError(
            f"{CAMPAIGN_ADAPTER} is missing required functions: {', '.join(missing)}"
        )
    return module


def _definition_records(adapter: Any) -> list[dict[str, Any]]:
    """Return topologically ordered, conservatively expandable definitions."""

    factory = getattr(adapter, "definition_json_records", None)
    if not callable(factory):
        raise DefinedEditionError(f"{adapter.__name__} cannot expose definition records")
    records = factory()
    if not isinstance(records, list) or not records:
        raise DefinedEditionError("the Bertrand adapter returned no definition records")
    missing = REQUIRED_CAMPAIGN_DEFINITIONS.difference(
        str(record.get("name", "")) for record in records
    )
    if missing:
        raise DefinedEditionError(
            "the Bertrand adapter lacks campaign-specific definitions: "
            + ", ".join(sorted(missing))
        )
    return records


def _definition_counts(parts: Sequence[Mapping[str, Any]]) -> Counter[str]:
    return Counter(
        str(part["definition"])
        for part in parts
        if part.get("kind") == "definition"
    )


def _compact_theorem(row: Mapping[str, Any], adapter: Any) -> dict[str, Any]:
    """Compact display surfaces while attesting every immutable source byte."""

    statement = adapter.compact_formula_source(row["statement"])
    if not statement.receipt.exact_ast_equivalence:
        raise DefinedEditionError(f"theorem {row['name']} lacks exact AST equivalence")
    statement_sha256 = shared._digest(row["statement"])
    if statement_sha256 != row["statement_sha256"]:
        raise DefinedEditionError(f"explicit statement digest changed for {row['name']}")
    if statement.receipt.expanded_source_sha256 != statement_sha256:
        raise DefinedEditionError(f"adapter statement receipt changed for {row['name']}")

    statement_parts = [part.as_json() for part in statement.parts]
    script_lines: list[dict[str, Any]] = []
    for line in row["lines"]:
        number = line["number"]
        tactic = adapter.compact_tactic_command(line["text"], number)
        if tactic.line_number != number or tactic.expanded_command != line["text"]:
            raise DefinedEditionError(
                f"adapter changed explicit line {number} of {row['name']}"
            )
        if tactic.proposition is not None and not tactic.proposition.receipt.exact_ast_equivalence:
            raise DefinedEditionError(
                f"local proposition {number} of {row['name']} lacks exact AST equivalence"
            )
        script_lines.append(
            {
                "number": number,
                "defined_command": tactic.defined_command,
                "expanded_command_sha256": shared._digest(line["text"]),
                "command_parts": [part.as_json() for part in tactic.parts],
            }
        )

    statement_uses = _definition_counts(statement_parts)
    script_uses: Counter[str] = Counter()
    for line in script_lines:
        script_uses.update(_definition_counts(line["command_parts"]))
    total_uses = statement_uses + script_uses
    return {
        "name": row["name"],
        "defined_statement": statement.defined_source,
        "expanded_statement_sha256": statement_sha256,
        "statement_parts": statement_parts,
        "defined_script_lines": script_lines,
        "statement_definition_uses": dict(sorted(statement_uses.items())),
        "script_definition_uses": dict(sorted(script_uses.items())),
        "definition_uses": dict(sorted(total_uses.items())),
    }


def _select_definitions(
    theorem_rows: Sequence[Mapping[str, Any]],
    definition_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Keep exactly used definitions and their conceptual prerequisites."""

    definitions_by_id = {str(row["id"]): row for row in definition_rows}
    if len(definitions_by_id) != len(definition_rows):
        raise DefinedEditionError("the Bertrand adapter repeated a definition ID")
    selected = {
        definition_id
        for theorem in theorem_rows
        for definition_id in theorem["definition_uses"]
    }
    pending = list(selected)
    while pending:
        definition_id = pending.pop()
        definition = definitions_by_id.get(definition_id)
        if definition is None:
            raise DefinedEditionError(
                f"Bertrand notation uses unknown definition {definition_id!r}"
            )
        for dependency_id in definition["dependencies"]:
            if dependency_id not in selected:
                selected.add(dependency_id)
                pending.append(dependency_id)
    if not selected:
        raise DefinedEditionError("the complete Bertrand proof used no reviewed definitions")
    return [dict(row) for row in definition_rows if row["id"] in selected]


def _build_edition(explicit_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    adapter = _adapter()
    reviewed_definitions = _definition_records(adapter)
    theorem_rows = [_compact_theorem(row, adapter) for row in explicit_rows]
    definitions = _select_definitions(theorem_rows, reviewed_definitions)
    identity_payload = {
        "schema": "peano-lab-defined-edition-v1",
        "definitions": definitions,
        "theorems": theorem_rows,
    }
    identity = shared._digest(
        json.dumps(
            identity_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return {**identity_payload, "identity_sha256": identity}


def _load_explicit() -> tuple[dict[str, Any], dict[str, Any], Sequence[Mapping[str, Any]]]:
    corpus = shared._json_object(EXPLICIT_CORPUS, "explicit Bertrand proof corpus")
    graph = shared._json_object(EXPLICIT_GRAPH, "explicit Bertrand theorem graph")
    if shared._digest(EXPLICIT_CORPUS.read_bytes()) != EXPECTED["corpus_sha256"]:
        raise DefinedEditionError("immutable Bertrand proof-corpus bytes changed")
    if shared._digest(EXPLICIT_GRAPH.read_bytes()) != EXPECTED["graph_sha256"]:
        raise DefinedEditionError("immutable Bertrand proof-graph bytes changed")
    if corpus.get("schema") != EXPECTED["corpus_schema"]:
        raise DefinedEditionError("unexpected explicit Bertrand proof-corpus schema")
    if graph.get("schema") != EXPECTED["graph_schema"]:
        raise DefinedEditionError("unexpected explicit Bertrand proof-graph schema")
    for document in (corpus, graph):
        if document.get("root_name") != ROOT_NAME or document.get("root_tag") != ROOT_TAG:
            raise DefinedEditionError("the immutable Bertrand root theorem changed")
        if document.get("theorem_count") != EXPECTED["theorem_count"]:
            raise DefinedEditionError("the immutable Bertrand theorem count changed")
        if document.get("edge_count") != EXPECTED["proof_edge_count"]:
            raise DefinedEditionError("the immutable Bertrand proof-edge count changed")
        if document.get("formal_line_count") != EXPECTED["formal_line_count"]:
            raise DefinedEditionError("the immutable Bertrand proof-line count changed")
    rows = shared._sequence(corpus.get("theorems"), "explicit Bertrand corpus.theorems")
    if len(rows) != EXPECTED["theorem_count"]:
        raise DefinedEditionError("the immutable Bertrand theorem ledger is incomplete")
    if [row["tag"] for row in rows] != [node["tag"] for node in graph["nodes"]]:
        raise DefinedEditionError("explicit Bertrand corpus and graph theorem order disagree")
    return corpus, graph, rows


def _pinned_assets() -> dict[str, bytes]:
    files = {}
    for relative, expected in shared.PINNED_ASSETS.items():
        path = ASSET_SOURCE / relative
        if not path.is_file():
            raise DefinedEditionError(f"missing reviewed defined-explorer asset: {relative}")
        payload = path.read_bytes()
        actual = shared._digest(payload)
        if actual != expected:
            raise DefinedEditionError(
                f"reviewed defined-explorer asset drift for {relative}: "
                f"expected {expected}, found {actual}"
            )
        files[relative] = payload
    return files


def _render_command(line: Mapping[str, Any]) -> str:
    text = str(line["text"])
    tactic = str(line["tactic"])
    spans: list[tuple[int, int, str, Mapping[str, Any] | None]] = [
        (0, len(tactic), "tactic", None)
    ]
    spans.extend(
        (int(reference["start"]), int(reference["end"]), str(reference["kind"]), reference)
        for reference in line.get("references", [])
    )
    pieces: list[str] = []
    cursor = 0
    for start, end, kind, reference in sorted(spans):
        if start < cursor:
            continue
        pieces.append(shared._e(text[cursor:start]))
        token = shared._e(text[start:end])
        if kind == "tactic":
            pieces.append(f'<span class="pd-tactic-ref">{token}</span>')
        elif kind == "theorem" and reference is not None:
            pieces.append(
                f'<a class="pd-theorem-ref" href="{shared._e(reference["tag"])}.html">'
                f"{token}</a>"
            )
        elif kind == "axiom":
            pieces.append(
                f'<span class="pd-axiom-ref" title="Peano arithmetic axiom">{token}</span>'
            )
        else:
            pieces.append(token)
        cursor = end
    pieces.append(shared._e(text[cursor:]))
    return "".join(pieces)


def _render_parts(parts: Sequence[Mapping[str, Any]], tactic: str | None = None) -> str:
    pieces: list[str] = []
    pending_tactic = tactic
    for part in parts:
        text = str(part["text"])
        if part["kind"] == "definition":
            pieces.append(
                '<a class="pd-definition-ref" '
                f'href="../definition/{shared._e(part["definition"])}.html">'
                f"{shared._e(text)}</a>"
            )
        elif pending_tactic and text.startswith(pending_tactic):
            pieces.append(
                f'<span class="pd-tactic-ref">{shared._e(pending_tactic)}</span>'
                f"{shared._e(text[len(pending_tactic):])}"
            )
            pending_tactic = None
        else:
            pieces.append(shared._e(text))
    return "".join(pieces)


def _source_link(source: Mapping[str, Any]) -> str:
    path = shared._e(source["path"])
    line = source.get("line")
    suffix = f":{line}" if isinstance(line, int) else ""
    href = source.get("href") or f"{GITHUB_ROOT}/{source['path']}"
    return f'<a href="{shared._e(href)}">{path}{suffix}</a>'


def _render_theorem(
    row: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
    previous: Mapping[str, Any] | None,
    following: Mapping[str, Any] | None,
) -> bytes:
    defined = row["defined"]
    statement_uses = list(defined["statement_definition_uses"])
    script_uses = list(defined["script_definition_uses"])
    line_rows: list[str] = []
    changed_count = 0
    for explicit, compact in zip(row["lines"], defined["defined_script_lines"], strict=True):
        number = int(explicit["number"])
        changed = compact["defined_command"] != explicit["text"]
        changed_count += changed
        classes = "pd-proof-line pd-proof-line-defined" if changed else "pd-proof-line"
        body = (
            _render_parts(compact["command_parts"], str(explicit["tactic"]))
            if changed
            else _render_command(explicit)
        )
        exact = (
            '<details class="pd-exact-line"><summary>Exact native replay line</summary>'
            f'<code>{_render_command(explicit)}</code></details>'
            if changed
            else ""
        )
        line_rows.append(
            f'<li class="{classes}" id="proof-line-{number:04d}" data-line="{number}" '
            f'data-defined-changed="{str(changed).lower()}">'
            f'<a class="pd-line-number" href="#proof-line-{number:04d}">{number:04d}</a>'
            f'<code class="pd-defined-command">{body}</code>{exact}</li>'
        )
    before = (
        f'<a href="{shared._e(previous["tag"])}.html">← {shared._e(previous["name"])}</a>'
        if previous
        else ""
    )
    after = (
        f'<a href="{shared._e(following["tag"])}.html">{shared._e(following["name"])} →</a>'
        if following
        else ""
    )
    body = f'''<header class="pd-header"><nav><a href="../index.html">Defined Bertrand edition</a><a href="../../tag/{shared._e(row["tag"])}.html">Explicit edition</a><a href="../graph.html?target={shared._e(row["tag"])}">Mixed graph</a>{before}{after}</nav><p class="pd-kicker">{shared._e(row["tag"])} · Bertrand theorem</p><h1>{shared._e(row["name"])}</h1><p class="pd-status pd-status-{shared._e(row["scope"])}">{shared._e(row["status_label"])}</p><p>{shared._e(row["summary"])}</p></header>
<main class="pd-theorem-layout"><div><section><h2>Statement with defined notation</h2><button type="button" data-copy-target="defined-statement">Copy text</button><pre id="defined-statement"><code>{_render_parts(defined["statement_parts"])}</code></pre><p class="pd-callout">Every purple notation token opens its conservative definition. Expanding the displayed statement recovers the exact first-order Peano-arithmetic formula checked by the unchanged kernel.</p></section><section><h2>Definitions used by this theorem</h2><h3>In the theorem statement</h3><div class="pd-chip-row">{shared._definition_chips(statement_uses, definitions)}</div><p>{sum(defined["statement_definition_uses"].values())} occurrences</p><h3>In local proof propositions</h3><div class="pd-chip-row">{shared._definition_chips(script_uses, definitions)}</div><p>{sum(defined["script_definition_uses"].values())} occurrences</p></section><details><summary>Exact expanded native-PA statement</summary><button type="button" data-copy-target="expanded-statement">Copy expansion</button><pre id="expanded-statement"><code>{shared._e(row["statement"])}</code></pre></details><section><h2>Proof neighborhood</h2><h3>Direct theorem prerequisites</h3><div class="pd-chip-row">{shared._relation(row["dependencies"])}</div><h3>Direct theorem dependents</h3><div class="pd-chip-row">{shared._relation(row["dependents"])}</div></section><section><h2>Definition-aware tactic body</h2><p>Only local propositions introduced by <code>have</code> or <code>suffices</code> are compacted. Every changed line has an exact-AST conservative-expansion receipt; the kernel still receives the immutable original tactic script.</p><ol class="pd-formal-proof">{"".join(line_rows)}</ol></section></div><aside><h2>Display receipt</h2><dl><dt>Proof layer</dt><dd>{row["layer"]}</dd><dt>Defined-notation uses</dt><dd>{sum(defined["definition_uses"].values())}</dd><dt>Statement definitions</dt><dd>{len(statement_uses)}</dd><dt>Local-proof definitions</dt><dd>{len(script_uses)}</dd><dt>Compacted local lines</dt><dd>{changed_count}</dd><dt>Exact statement SHA-256</dt><dd><code>{shared._e(row["statement_sha256"])}</code></dd><dt>Explicit proof</dt><dd><a href="../../tag/{shared._e(row["tag"])}.html">open immutable explicit page</a></dd><dt>Native source</dt><dd>{_source_link(row["source"])}</dd></dl></aside></main>'''
    return shared._page(
        f'{row["tag"]} — {row["name"]} — defined Bertrand notation',
        "theorem",
        body,
        "../",
    )


def _render_definition(
    definition: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, Any]],
    theorem_users: Sequence[Mapping[str, Any]],
    definition_users: Sequence[Mapping[str, Any]],
) -> bytes:
    source = definition["source"]
    dependent_definitions = " ".join(
        f'<a class="pd-chip pd-definition-chip" href="{shared._e(item["id"])}.html">'
        f'<code>{shared._e(item["id"])}</code> {shared._e(item["name"])}</a>'
        for item in definition_users
    ) or '<span class="pd-empty">none</span>'
    used_theorems = " ".join(
        f'<a class="pd-chip pd-theorem-chip" href="../tag/{shared._e(item["tag"])}.html">'
        f'<code>{shared._e(item["tag"])}</code> {shared._e(item["name"])}</a>'
        for item in theorem_users
    ) or '<span class="pd-empty">none</span>'
    body = f'''<header class="pd-header pd-definition-header"><nav><a href="../index.html">Defined Bertrand edition</a><a href="../graph.html?target={ROOT_TAG}&amp;focus={shared._e(definition["id"])}">Mixed graph</a><a href="../../index.html">Exact explicit proof</a></nav><p class="pd-kicker">{shared._e(definition["id"])} · conservative definition</p><h1>{shared._e(definition["name"])}</h1><p>{shared._e(definition["summary"])}</p></header><main class="pd-definition-page"><section><h2>Readable signature</h2><pre><code>{shared._e(definition["signature"])}</code></pre></section><section><h2>Exact expansion</h2><button type="button" data-copy-target="definition-expansion">Copy expansion</button><pre id="definition-expansion"><code>{shared._e(definition["expansion"])}</code></pre><p class="pd-callout">This node is conservative notation, not a theorem, new axiom, predicate constant, or kernel rule. Its expansion is checked for exact first-order AST equivalence.</p></section><section><h2>Definition neighborhood</h2><h3>Expands using</h3><div class="pd-chip-row">{shared._definition_chips(definition["dependencies"], definitions, "")}</div><h3>Used by definitions</h3><div class="pd-chip-row">{dependent_definitions}</div><h3>Used by theorem statements or local proof propositions</h3><div class="pd-chip-row">{used_theorems}</div></section><aside><h2>Definition receipt</h2><dl><dt>Expansion SHA-256</dt><dd><code>{shared._e(definition["expansion_sha256"])}</code></dd><dt>Source</dt><dd>{shared._e(source["path"])}:{source["line"]}</dd><dt>Source SHA-256</dt><dd><code>{shared._e(source["sha256"])}</code></dd></dl></aside></main>'''
    return shared._page(
        f'{definition["id"]} — {definition["name"]} — Bertrand definition',
        "definition",
        body,
        "../",
    )


def _render_index(
    theorems: Sequence[Mapping[str, Any]],
    definitions: Sequence[Mapping[str, Any]],
) -> bytes:
    theorem_cards = "".join(
        f'<article class="pd-result" data-entry data-kind="theorem" '
        f'data-search="{shared._e(" ".join((row["name"], row["tag"], row["summary"], row["defined"]["defined_statement"])).lower())}">'
        f'<a href="tag/{shared._e(row["tag"])}.html"><code>{shared._e(row["tag"])}</code> · '
        f'<strong>{shared._e(row["name"])}</strong></a><p>{shared._e(row["summary"])}</p>'
        f'<small>theorem · proof layer {row["layer"]} · '
        f'{len(row["defined"]["definition_uses"])} definitions</small></article>'
        for row in theorems
    )
    definition_cards = "".join(
        f'<article class="pd-result pd-result-definition" data-entry data-kind="definition" '
        f'data-search="{shared._e(" ".join((row["name"], row["id"], row["signature"], row["summary"])).lower())}">'
        f'<a href="definition/{shared._e(row["id"])}.html"><code>{shared._e(row["id"])}</code> · '
        f'<strong>{shared._e(row["name"])}</strong></a><p>{shared._e(row["summary"])}</p>'
        '<small>conservative definition · not a theorem</small></article>'
        for row in definitions
    )
    body = f'''<header class="pd-header pd-hero"><nav><a href="../index.html">Exact explicit edition</a><a href="graph.html?target={ROOT_TAG}&amp;view=neighborhood&amp;definitions=selected&amp;edges=focus">Mixed dependency graph</a><a href="tag/{ROOT_TAG}.html">Bertrand’s postulate</a></nav><p class="pd-kicker">Complete Bertrand proof · parallel reading edition</p><h1>Bertrand’s postulate with defined notation</h1><p>Explore every theorem in the complete native-PA proof together with genuine conservative definitions for binomial and central binomial coefficients, primorials, prime-power valuations, Legendre sums, factorials, and integer square-root bounds.</p><div class="pd-stats"><b>{len(theorems)}</b> theorems · <b>{len(definitions)}</b> definitions · <b>{EXPECTED["proof_edge_count"]}</b> proof edges</div></header><main data-defined-dashboard><section class="pd-controls"><label>Search <input data-search type="search"></label><label>Kind <select data-kind><option value="all">Theorems and definitions</option><option value="theorem">Theorems</option><option value="definition">Definitions</option></select></label><button data-clear type="button">Clear</button><output data-count>{len(theorems) + len(definitions)} entries</output></section><section class="pd-results">{definition_cards}{theorem_cards}</section></main>'''
    return shared._page("Bertrand’s postulate with defined notation", "index", body)


def _render_graph(graph: Mapping[str, Any]) -> bytes:
    inline = shared._javascript_assignment("PA_DEFINED_GRAPH", graph)
    body = f'''<header class="pd-header"><nav><a href="index.html">Defined Bertrand edition</a><a href="../graph.html?target={ROOT_TAG}">Exact theorem graph</a><a href="tag/{ROOT_TAG}.html">Bertrand’s postulate</a></nav><p class="pd-kicker">Complete Bertrand proof · typed mixed graph</p><h1>Bertrand theorems and conservative definitions</h1><p>Proof arrows and notation arrows are different relations. Only theorem-proof arrows participate in the exact prerequisite path to Bertrand’s postulate.</p></header><main class="pd-graph-page" data-defined-graph><form class="pd-graph-controls" data-graph-form><label>Target theorem <input data-graph-target list="pd-graph-theorems" value="{ROOT_TAG}" required></label><datalist id="pd-graph-theorems"></datalist><label>View <select data-graph-view><option value="critical">Critical theorem path</option><option value="prerequisites">Complete theorem prerequisite cone</option><option value="neighborhood" selected>Direct theorem neighborhood</option><option value="corpus">Entire theorem corpus</option></select></label><label>Definitions <select data-graph-definitions><option value="selected" selected>Selected node only</option><option value="off">Hide definitions</option><option value="visible">All visible theorem definitions (heavy)</option></select></label><label>Arrows <select data-graph-edges><option value="focus" selected>Focused: path + selected node</option><option value="none">Hide arrows</option><option value="all">All direct arrows (heavy)</option></select></label><button type="submit">Draw</button></form><p class="pd-graph-note">Sparse modes suppress visual objects only. Every exact proof and notation relation remains in the selected-node panel and graph data; large views use compact clickable marks.</p><div class="pd-graph-layout"><section><div class="pd-graph-toolbar"><p data-graph-summary aria-live="polite">Loading graph…</p><div><button type="button" data-graph-zoom="in" aria-label="Zoom in">+</button><button type="button" data-graph-zoom="out" aria-label="Zoom out">−</button><button type="button" data-graph-fit aria-label="Fit graph">Fit</button></div></div><div class="pd-graph-stage"><svg data-graph-svg tabindex="0" role="group" aria-labelledby="pd-graph-instructions"><text x="20" y="35">Loading…</text></svg></div><p id="pd-graph-instructions" class="pd-graph-note">Proof arrows run from prerequisite to dependent; notation arrows run from a theorem or definition to the definition it uses. Select any node to inspect every direct relation.</p><div class="pd-legend"><span><i class="pd-legend-theorem"></i> theorem</span><span><i class="pd-legend-definition"></i> definition</span><span><i class="pd-legend-proof"></i> proof dependency</span><span><i class="pd-legend-notation"></i> uses definition</span></div></section><aside class="pd-graph-details"><p class="pd-kicker">Selected node</p><h2 data-graph-title tabindex="-1">Loading…</h2><p data-graph-kind></p><p data-graph-description></p><dl data-graph-metadata></dl><p><a data-graph-open href="index.html">Open node →</a></p><h3>Outgoing relations</h3><ul data-graph-outgoing></ul><h3>Incoming relations</h3><ul data-graph-incoming></ul></aside></div><noscript><p class="pd-callout">The graph requires JavaScript. Every theorem and definition remains available from the index.</p></noscript></main><script id="pa-defined-graph-data">{inline}</script>'''
    return shared._page("Bertrand theorems and definitions", "graph", body)


def _mixed_graph(
    theorem_rows: Sequence[Mapping[str, Any]],
    definitions: Sequence[Mapping[str, Any]],
    explicit_graph: Mapping[str, Any],
    edition_identity: str,
) -> dict[str, Any]:
    graph = shared._mixed_graph(theorem_rows, definitions, explicit_graph, edition_identity)
    graph.update(
        {
            "schema": "peano-lab-bertrand-defined-graph-v1",
            "root_name": ROOT_NAME,
            "root_tag": ROOT_TAG,
            "explicit_graph_sha256": EXPECTED["graph_sha256"],
            "catalog_sha256": explicit_graph["catalog_sha256"],
            "formal_line_count": explicit_graph["formal_line_count"],
        }
    )
    return graph


def _graph_schema() -> dict[str, Any]:
    schema = shared._graph_schema()
    schema["$id"] = "urn:peano-lab:bertrand-defined-graph-v1"
    schema["title"] = "Bertrand proof theorem and conservative-definition graph"
    schema["properties"]["schema"]["const"] = "peano-lab-bertrand-defined-graph-v1"
    schema["required"].extend(["root_name", "root_tag", "explicit_graph_sha256"])
    return schema


def build_files(
    raw_edition: Mapping[str, Any] | None = None,
) -> tuple[dict[str, bytes], dict[str, Any]]:
    explicit_corpus, explicit_graph, explicit_rows = _load_explicit()
    edition = shared.validate_edition(raw_edition or _build_edition(explicit_rows), explicit_rows)
    edition_by_name = {row["name"]: row for row in edition["theorems"]}
    theorem_rows = [
        {**row, "defined": edition_by_name[row["name"]]}
        for row in explicit_rows
    ]
    definitions = edition["definitions"]
    definitions_by_id = {row["id"]: row for row in definitions}
    theorem_users: dict[str, list[dict[str, Any]]] = defaultdict(list)
    definition_users: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for theorem in theorem_rows:
        for definition_id in theorem["defined"]["definition_uses"]:
            theorem_users[definition_id].append(theorem)
    for definition in definitions:
        for dependency_id in definition["dependencies"]:
            definition_users[dependency_id].append(definition)

    graph = _mixed_graph(
        theorem_rows,
        definitions,
        explicit_graph,
        edition["identity_sha256"],
    )
    corpus = {
        "schema": "peano-lab-bertrand-defined-corpus-v1",
        "edition_identity_sha256": edition["identity_sha256"],
        "explicit_corpus_sha256": EXPECTED["corpus_sha256"],
        "catalog_sha256": explicit_corpus["catalog_sha256"],
        "root_name": ROOT_NAME,
        "root_tag": ROOT_TAG,
        "theorem_count": len(theorem_rows),
        "definition_count": len(definitions),
        "proof_edge_count": graph["proof_edge_count"],
        "formal_line_count": explicit_corpus["formal_line_count"],
        "public_count": explicit_corpus["public_count"],
        "candidate_count": explicit_corpus["candidate_count"],
        "theorems": [
            {
                "tag": row["tag"],
                "name": row["name"],
                "scope": row["scope"],
                "status": row["status"],
                "layer": row["layer"],
                "summary": row["summary"],
                "defined": row["defined"],
                "explicit_statement": row["statement"],
                "explicit_statement_sha256": row["statement_sha256"],
                "dependencies": row["dependencies"],
                "dependents": row["dependents"],
            }
            for row in theorem_rows
        ],
        "definitions": definitions,
    }
    files: dict[str, bytes] = {
        "index.html": _render_index(theorem_rows, definitions),
        "graph.html": _render_graph(graph),
        "api/corpus.json": shared._json_bytes(corpus),
        "api/graph.json": shared._json_bytes(graph),
        "api/graph.schema.json": shared._json_bytes(_graph_schema()),
        **_pinned_assets(),
    }
    for index, row in enumerate(theorem_rows):
        files[f'tag/{row["tag"]}.html'] = _render_theorem(
            row,
            definitions_by_id,
            theorem_rows[index - 1] if index else None,
            theorem_rows[index + 1] if index + 1 < len(theorem_rows) else None,
        )
        target = f'../tag/{row["tag"]}.html'
        files[f'name/{row["name"]}.html'] = (
            '<!doctype html><html><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}">'
            f'<script>location.replace({json.dumps(target)}+location.search+location.hash)</script>'
            f'</head><body><a href="{target}">{shared._e(row["name"])}</a></body></html>\n'
        ).encode("utf-8")
    for definition in definitions:
        files[f'definition/{definition["id"]}.html'] = _render_definition(
            definition,
            definitions_by_id,
            theorem_users[definition["id"]],
            definition_users[definition["id"]],
        )

    manifest_files = [
        {"path": path, "bytes": len(payload), "sha256": shared._digest(payload)}
        for path, payload in sorted(files.items())
    ]
    aggregate = shared._digest(
        "\n".join(f'{row["path"]}\0{row["sha256"]}' for row in manifest_files)
    )
    manifest = {
        "schema": "peano-lab-bertrand-defined-explorer-manifest-v1",
        "edition_identity_sha256": edition["identity_sha256"],
        "explicit_corpus_sha256": EXPECTED["corpus_sha256"],
        "explicit_graph_sha256": EXPECTED["graph_sha256"],
        "catalog_sha256": explicit_corpus["catalog_sha256"],
        "root_name": ROOT_NAME,
        "root_tag": ROOT_TAG,
        "theorem_count": len(theorem_rows),
        "definition_count": len(definitions),
        "proof_edge_count": graph["proof_edge_count"],
        "notation_edge_count": graph["notation_edge_count"],
        "formal_line_count": explicit_corpus["formal_line_count"],
        "generated_file_count": len(files) + 1,
        "aggregate_sha256": aggregate,
        "required_assets": sorted(shared.PINNED_ASSETS),
        "files": manifest_files,
    }
    files["manifest.json"] = shared._json_bytes(manifest)
    return files, manifest


def _safe_output(path: Path) -> Path:
    resolved = path.resolve(strict=False)
    unsafe = {REPO.resolve(), REPO.parent.resolve(), EXPLICIT.resolve(), Path("/")}
    if resolved in unsafe:
        raise DefinedEditionError("refusing a broad defined-Bertrand output directory")
    return resolved


def _write(files: Mapping[str, bytes], output: Path) -> None:
    output = _safe_output(output)
    for relative, payload in files.items():
        path = output / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    expected = set(files)
    if output.is_dir():
        for path in output.rglob("*"):
            if path.is_file() and str(path.relative_to(output)) not in expected:
                path.unlink()


def _check(files: Mapping[str, bytes], output: Path) -> bool:
    output = _safe_output(output)
    drift = [
        relative
        for relative, payload in files.items()
        if not (output / relative).is_file() or (output / relative).read_bytes() != payload
    ]
    expected = set(files)
    if output.is_dir():
        drift.extend(
            str(path.relative_to(output))
            for path in output.rglob("*")
            if path.is_file() and str(path.relative_to(output)) not in expected
        )
    if drift:
        print(
            "defined Bertrand explorer drift: " + ", ".join(sorted(set(drift))[:20]),
            file=sys.stderr,
        )
        return False
    return True


def main(argv: Sequence[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files drift")
    parser.add_argument("--output", type=Path, default=OUTPUT, help="defined-edition output")
    args = parser.parse_args(argv)
    try:
        files, manifest = build_files()
        if args.check:
            if not _check(files, args.output):
                return 1
            print(
                f'verified defined Bertrand explorer: {manifest["generated_file_count"]} files, '
                f'{manifest["aggregate_sha256"]}'
            )
            return 0
        _write(files, args.output)
    except (DefinedEditionError, ValueError, OSError) as error:
        print(f"defined Bertrand explorer: {error}", file=sys.stderr)
        return 2
    print(
        f'wrote defined Bertrand explorer: {manifest["generated_file_count"]} files, '
        f'{manifest["theorem_count"]} theorems, {manifest["definition_count"]} definitions, '
        f'{manifest["aggregate_sha256"]}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
