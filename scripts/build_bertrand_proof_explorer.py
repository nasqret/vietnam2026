#!/usr/bin/env python3
"""Build the replay-free interactive explorer for the full Bertrand proof.

The Alpha-v12 catalog is the byte-frozen statement/script/provenance input.
The independently sealed Alpha-v19 inventory supplies current release evidence
for the exact same dependency closure, while Alpha v18 remains the historical
proof-bearing release. This documentation builder never executes tactics,
changes historical enrollment, or grants theorem authority.
"""

from __future__ import annotations

import argparse
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
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from peano_lab.library import editions_v18 as proof_alpha  # noqa: E402
from peano_lab.library import editions_v19 as current_alpha  # noqa: E402

CATALOG = REPO / "artifacts" / "peano-library" / "alpha" / "catalog-v12.json"
OUTPUT = REPO / "book" / "_static" / "bertrand-proof-explorer"
ASSET_SOURCE = REPO / "book" / "_static" / "pa-proof-explorer" / "assets"
# The definition-aware edition is an independently generated, conservative
# presentation layer.  Keep it outside the frozen exact-edition manifest while
# allowing both surfaces to share one stable explorer URL.
RESERVED_SUBTREES = {"defined"}
GITHUB_ROOT = (
    "https://github.com/nasqret/vietnam2026/blob/"
    "agent/new-theorems-tranche-01"
)
ROOT_NAME = "bertrand_strict"
CAMPAIGN_HTML_REVISION = "f1c3d3fba013"
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXY"
PA_AXIOMS = {f"PA{i}" for i in range(1, 7)}
IDENT_RE = r"[A-Za-z_][A-Za-z0-9_']*"
EXPECTED = {
    "catalog_sha256": (
        "825909e057492de87ef08208451c3475396ca009179c513457b05b57f7e2f109"
    ),
    "catalog_schema": "peano-library-alpha-snapshot-v12",
    "catalog_theorem_count": 1303,
    "catalog_edge_count": 4302,
    "catalog_layer_count": 45,
    "closure_theorem_count": 544,
    "closure_checked_count": 544,
    "closure_stable_count": 202,
    "closure_alpha_closed_count": 342,
    "source_closure_checked_count": 203,
    "source_closure_body_only_count": 341,
    "closure_edge_count": 1917,
    "closure_layer_count": 45,
    "formal_line_count": 28410,
    "explicit_dependency_reference_count": 8786,
    "root_tag": "BT0127",
    "alpha_edition_version": "v19",
    "alpha_edition_identity_sha256": (
        "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7"
    ),
    "alpha_edition_checked_use_count": 1737,
    "proof_edition_version": "v18",
    "proof_edition_identity_sha256": (
        "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
    ),
    "proof_edition_checked_use_count": 1589,
}
PINNED_ASSETS = {
    "explorer.css": (
        "6dd0cf105c498dec70fe6a7fac04dcda397b40f947de677b36fc9c01962d84bc"
    ),
    "explorer.js": (
        "98f11fff5d34b5fa481c1dd6a6b39eef58fed28d00bb7d1f4ac7d1226b4d6606"
    ),
}


def _digest(payload: bytes | str) -> str:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return sha256(payload).hexdigest()


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def _base35(value: int) -> str:
    if value < 0 or value >= 35**4:
        raise ValueError("Bertrand proof-tag space exhausted")
    digits = []
    for _ in range(4):
        value, digit = divmod(value, 35)
        digits.append(ALPHABET[digit])
    return "".join(reversed(digits))


def _tag(row: dict[str, Any]) -> str:
    return "BT" + _base35(row["enrollment_index"])


def _javascript_assignment(name: str, value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )
    payload = payload.replace("&", r"\u0026")
    payload = payload.replace("<", r"\u003c")
    payload = payload.replace(">", r"\u003e")
    return f"window.{name}={payload};"


def _dependency_references(
    command: str,
    dependencies: set[str],
) -> tuple[str, list[dict[str, Any]]]:
    match = re.match(rf"\s*({IDENT_RE})", command)
    if match is None:
        raise ValueError(f"cannot parse tactic command {command!r}")
    tactic = match.group(1)
    references = []
    for dependency in sorted(dependencies, key=lambda value: (-len(value), value)):
        pattern = rf"(?<![A-Za-z0-9_']){re.escape(dependency)}(?![A-Za-z0-9_'])"
        for found in re.finditer(pattern, command):
            references.append(
                {
                    "kind": "theorem",
                    "name": dependency,
                    "start": found.start(),
                    "end": found.end(),
                }
            )
    for axiom in sorted(PA_AXIOMS):
        pattern = rf"(?<![A-Za-z0-9_']){axiom}(?![A-Za-z0-9_'])"
        for found in re.finditer(pattern, command):
            references.append(
                {
                    "kind": "axiom",
                    "name": axiom,
                    "start": found.start(),
                    "end": found.end(),
                }
            )
    references.sort(key=lambda row: (row["start"], row["end"], row["name"]))
    return tactic, references


def _render_command(line: dict[str, Any]) -> str:
    command = line["text"]
    tactic_end = len(line["tactic"])
    spans = [(0, tactic_end, "tactic", line["tactic"], "")]
    spans.extend(
        (
            item["start"],
            item["end"],
            item["kind"],
            item["name"],
            item.get("tag", ""),
        )
        for item in line["references"]
    )
    pieces = []
    cursor = 0
    for left, right, kind, name, reference_tag in sorted(spans):
        if left < cursor:
            continue
        pieces.append(_escape(command[cursor:left]))
        if kind == "tactic":
            pieces.append(f'<span class="pa-tactic-ref">{_escape(name)}</span>')
        elif kind == "theorem":
            pieces.append(
                '<a class="pa-theorem-ref" '
                f'href="{_escape(reference_tag)}.html">'
                f'{_escape(name)}</a>'
            )
        else:
            pieces.append(
                '<span class="pa-axiom-ref" '
                f'title="Peano arithmetic axiom">{_escape(name)}</span>'
            )
        cursor = right
    pieces.append(_escape(command[cursor:]))
    return "".join(pieces)


def _page(title: str, page: str, body: str, prefix: str = "") -> bytes:
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{_escape(title)}</title>
<link rel="stylesheet" href="{prefix}assets/explorer.css">
<script defer src="{prefix}assets/explorer.js"></script></head>
<body class="pa-proof-site" data-page="{page}">{body}</body></html>
""".encode("utf-8")


def _campaign_navigation(prefix: str) -> str:
    """Return deployed atlas links without changing any proof or evidence data."""

    return (
        f'<a href="{prefix}grand-campaign/?v={CAMPAIGN_HTML_REVISION}">'
        "Grand campaign</a>"
        f'<a href="{prefix}grand-campaign/?view=domain&amp;focus=D02'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Research domain</a>'
        f'<a href="{prefix}grand-campaign/?view=family&amp;focus=F03'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Prime-distribution family</a>'
        f'<a href="{prefix}grand-campaign/?view=goal&amp;focus=A02'
        f'&amp;v={CAMPAIGN_HTML_REVISION}">Campaign milestone</a>'
    )


def _load_catalog() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    payload = CATALOG.read_bytes()
    if _digest(payload) != EXPECTED["catalog_sha256"]:
        raise ValueError("Alpha-v12 catalog bytes changed")
    catalog = json.loads(payload)
    if catalog.get("schema") != EXPECTED["catalog_schema"]:
        raise ValueError("unexpected Alpha-v12 catalog schema")
    if catalog.get("theorem_count") != EXPECTED["catalog_theorem_count"]:
        raise ValueError("Alpha-v12 theorem count changed")
    if catalog.get("edge_count") != EXPECTED["catalog_edge_count"]:
        raise ValueError("Alpha-v12 edge count changed")
    rows = catalog.get("theorems")
    if not isinstance(rows, list) or len(rows) != catalog["theorem_count"]:
        raise ValueError("invalid Alpha-v12 theorem ledger")
    names = [row.get("name") for row in rows]
    if len(names) != len(set(names)) or ROOT_NAME not in names:
        raise ValueError("invalid Alpha-v12 theorem names")
    by_name = {row["name"]: row for row in rows}
    for index, row in enumerate(rows):
        if row.get("enrollment_index") != index:
            raise ValueError("Alpha-v12 enrollment indices changed")
        dependencies = row.get("dependencies")
        if not isinstance(dependencies, list):
            raise ValueError(f"invalid dependencies for {row['name']}")
        if any(name not in by_name for name in dependencies):
            raise ValueError(f"unknown dependency for {row['name']}")
        if any(by_name[name]["enrollment_index"] >= index for name in dependencies):
            raise ValueError(f"non-topological dependency for {row['name']}")
    selected = set()

    def visit(name: str) -> None:
        if name in selected:
            return
        selected.add(name)
        for dependency in by_name[name]["dependencies"]:
            visit(dependency)

    visit(ROOT_NAME)
    closure = [row for row in rows if row["name"] in selected]
    return catalog, closure


def _records(
    catalog: dict[str, Any],
    closure: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    if (
        current_alpha.ALPHA_V19_IDENTITY_SHA256
        != EXPECTED["alpha_edition_identity_sha256"]
        or len(current_alpha.ALPHA_CHECKED_SPECS)
        != EXPECTED["alpha_edition_checked_use_count"]
    ):
        raise ValueError("sealed Alpha-v19 Bertrand release evidence changed")
    if (
        proof_alpha.ALPHA_V18_IDENTITY_SHA256
        != EXPECTED["proof_edition_identity_sha256"]
        or len(proof_alpha.ALPHA_CHECKED_SPECS)
        != EXPECTED["proof_edition_checked_use_count"]
    ):
        raise ValueError("historical Alpha-v18 Bertrand proof evidence changed")
    by_name = {row["name"]: row for row in closure}
    tags = {row["name"]: _tag(row) for row in closure}
    layers: dict[str, int] = {}
    dependents: dict[str, list[str]] = defaultdict(list)
    for row in closure:
        name = row["name"]
        layers[name] = (
            0
            if not row["dependencies"]
            else 1 + max(layers[item] for item in row["dependencies"])
        )
        for dependency in row["dependencies"]:
            dependents[dependency].append(name)

    records = []
    reference_counts: Counter[tuple[str, str]] = Counter()
    all_tactics = set()
    for source in closure:
        release_entry = current_alpha.ALPHA_EDITION.by_name.get(source["name"])
        if (
            release_entry is None
            or release_entry.spec.statement != source["statement"]
            or tuple(release_entry.spec.script) != tuple(source["script"])
            or tuple(release_entry.spec.dependencies)
            != tuple(source["dependencies"])
            or release_entry.enrollment_origin.value != source["enrollment_origin"]
            or not release_entry.checked_use
        ):
            raise ValueError(
                f"sealed Alpha-v19 theorem differs from frozen Bertrand source "
                f"or lacks checked-use evidence: {source['name']!r}"
            )
        proof_entry = proof_alpha.ALPHA_EDITION.by_name.get(source["name"])
        if (
            proof_entry is None
            or proof_entry.spec != release_entry.spec
            or proof_entry.membership is not release_entry.membership
            or proof_entry.evidence is not release_entry.evidence
            or not proof_entry.checked_use
        ):
            raise ValueError(
                f"historical Alpha-v18 proof-bearing theorem differs from "
                f"current Alpha-v19 release: {source['name']!r}"
            )
        stable_member = release_entry.membership is current_alpha.Membership.STABLE
        expected_evidence = (
            current_alpha.EvidenceStatus.STABLE_CLOSED
            if stable_member
            else current_alpha.EvidenceStatus.ALPHA_CLOSED
        )
        if release_entry.evidence is not expected_evidence:
            raise ValueError(
                f"Bertrand theorem {source['name']!r} has inconsistent "
                "sealed Alpha-v19 evidence and Stable membership"
            )
        source_path = REPO / source["source"]["path"]
        if not source_path.is_file():
            raise ValueError(f"missing source for {source['name']}")
        if _digest(source_path.read_bytes()) != source["source"]["sha256"]:
            raise ValueError(f"source bytes changed for {source['name']}")
        lines = []
        dependencies = set(source["dependencies"])
        for number, command in enumerate(source["script"], 1):
            tactic, references = _dependency_references(command, dependencies)
            all_tactics.add(tactic)
            for item in references:
                if item["kind"] == "theorem":
                    item["tag"] = tags[item["name"]]
                    reference_counts[(source["name"], item["name"])] += 1
            lines.append(
                {
                    "number": number,
                    "id": f"proof-line-{number:04d}",
                    "stable_id": _digest(
                        f'{source["name"]}\0{number}\0{command}'
                    )[:16],
                    "text": command,
                    "tactic": tactic,
                    "references": references,
                }
            )
        scope = "public" if stable_member else "candidate"
        status_label = (
            "Stable checked-use theorem · independently kernel verified"
            if stable_member
            else "Alpha v19 checked-use theorem · independently kernel and "
            "Lean verified; not Stable"
        )
        records.append(
            {
                "tag": tags[source["name"]],
                "name": source["name"],
                "scope": scope,
                "status": "public" if stable_member else "alpha_closed",
                "status_label": status_label,
                "alpha_edition_version": EXPECTED["alpha_edition_version"],
                "proof_edition_version": EXPECTED["proof_edition_version"],
                "alpha_evidence": release_entry.evidence.value,
                "alpha_checked_use": release_entry.checked_use,
                "stable_member": stable_member,
                "layer": layers[source["name"]],
                "summary": source["summary"],
                "statement": source["statement"],
                "statement_sha256": source["statement_sha256"],
                "script_sha256": source["script_sha256"],
                "logical_spec_sha256": source["logical_spec_sha256"],
                "enrollment_index": source["enrollment_index"],
                "enrollment_origin": source["enrollment_origin"],
                "evidence_status": release_entry.evidence.value,
                "checked_use": release_entry.checked_use,
                "source_edition_version": "v12",
                "source_evidence_status": source["evidence_status"],
                "source_checked_use": source["checked_use"],
                "body_receipt": source.get("body_receipt"),
                "source": source["source"],
                "lines": lines,
                "dependencies": [],
                "dependents": [],
            }
        )

    edges = []
    record_by_name = {row["name"]: row for row in records}
    for row in records:
        source = by_name[row["name"]]
        row["dependencies"] = [
            {
                "name": name,
                "tag": tags[name],
                "body_reference": reference_counts[(row["name"], name)] > 0,
                "explicit_reference_count": reference_counts[(row["name"], name)],
            }
            for name in source["dependencies"]
        ]
        row["dependents"] = [
            {
                "name": name,
                "tag": tags[name],
                "body_reference": reference_counts[(name, row["name"])] > 0,
                "explicit_reference_count": reference_counts[(name, row["name"])],
            }
            for name in dependents[row["name"]]
        ]
        for dependency in row["dependencies"]:
            edges.append(
                {
                    "dependency": dependency["tag"],
                    "dependency_name": dependency["name"],
                    "dependent": row["tag"],
                    "dependent_name": row["name"],
                    "body_reference": dependency["body_reference"],
                    "explicit_reference_count": dependency[
                        "explicit_reference_count"
                    ],
                }
            )

    receipt = {
        "theorem_count": len(records),
        "public_count": sum(row["scope"] == "public" for row in records),
        "candidate_count": sum(row["scope"] == "candidate" for row in records),
        "alpha_edition_version": EXPECTED["alpha_edition_version"],
        "alpha_edition_identity_sha256": current_alpha.ALPHA_V19_IDENTITY_SHA256,
        "alpha_edition_checked_use_count": len(current_alpha.ALPHA_CHECKED_SPECS),
        "proof_edition_version": EXPECTED["proof_edition_version"],
        "proof_edition_identity_sha256": proof_alpha.ALPHA_V18_IDENTITY_SHA256,
        "proof_edition_checked_use_count": len(proof_alpha.ALPHA_CHECKED_SPECS),
        "graph_checked_use_count": sum(row["alpha_checked_use"] for row in records),
        "graph_stable_closed_count": sum(row["stable_member"] for row in records),
        "graph_alpha_closed_count": sum(
            row["alpha_evidence"] == "alpha_closed" for row in records
        ),
        "graph_newly_promoted_count": sum(
            row["name"] in proof_alpha.FLAGSHIP_PROMOTED_NAMES
            for row in records
        ),
        "source_scope_policy": "historical_origin_not_current_release_authority",
        "source_edition_version": "v12",
        "source_checked_use_count": sum(row["source_checked_use"] for row in records),
        "source_body_checked_count": sum(
            row["source_evidence_status"] == "body_checked" for row in records
        ),
        "edge_count": len(edges),
        "layer_count": max(row["layer"] for row in records) + 1,
        "formal_line_count": sum(len(row["lines"]) for row in records),
        "explicit_dependency_reference_count": sum(
            edge["explicit_reference_count"] for edge in edges
        ),
        "catalog_sha256": EXPECTED["catalog_sha256"],
        "ordered_enrollment_root_sha256": catalog[
            "ordered_enrollment_root_sha256"
        ],
        "edition_identity_sha256": current_alpha.ALPHA_V19_IDENTITY_SHA256,
        "source_edition_identity_sha256": catalog["edition_identity_sha256"],
        "root_name": ROOT_NAME,
        "root_tag": tags[ROOT_NAME],
    }
    actual = {
        "closure_theorem_count": receipt["theorem_count"],
        "closure_checked_count": receipt["graph_checked_use_count"],
        "closure_stable_count": receipt["public_count"],
        "closure_alpha_closed_count": receipt["candidate_count"],
        "source_closure_checked_count": receipt["source_checked_use_count"],
        "source_closure_body_only_count": receipt["source_body_checked_count"],
        "closure_edge_count": receipt["edge_count"],
        "closure_layer_count": receipt["layer_count"],
        "formal_line_count": receipt["formal_line_count"],
        "explicit_dependency_reference_count": receipt[
            "explicit_dependency_reference_count"
        ],
        "root_tag": receipt["root_tag"],
    }
    for key, value in actual.items():
        if value != EXPECTED[key]:
            raise ValueError(f"Bertrand explorer receipt changed at {key}: {value!r}")
    if ROOT_NAME not in record_by_name:
        raise ValueError("Bertrand root missing from explorer")
    receipt["tactics"] = sorted(all_tactics)
    return records, edges, receipt


def _graph_payload(
    records: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    receipt: dict[str, Any],
) -> dict[str, Any]:
    tags = [row["tag"] for row in records]
    rank = {tag: index for index, tag in enumerate(tags)}
    dependencies = {
        row["tag"]: [item["tag"] for item in row["dependencies"]]
        for row in records
    }
    dependents = {
        row["tag"]: [item["tag"] for item in row["dependents"]]
        for row in records
    }
    ancestors: dict[str, set[str]] = {}
    shortest: dict[str, list[str]] = {}
    critical: dict[str, list[str]] = {}
    path_counts: dict[str, int] = {}
    for tag in tags:
        closure = set()
        for dependency in dependencies[tag]:
            closure.add(dependency)
            closure.update(ancestors[dependency])
        ancestors[tag] = closure
        if dependencies[tag]:
            short_candidates = [shortest[item] + [tag] for item in dependencies[tag]]
            shortest[tag] = min(
                short_candidates,
                key=lambda path: (len(path), tuple(rank[item] for item in path)),
            )
            critical_candidates = [critical[item] + [tag] for item in dependencies[tag]]
            critical[tag] = min(
                critical_candidates,
                key=lambda path: (-len(path), tuple(rank[item] for item in path)),
            )
            path_counts[tag] = sum(path_counts[item] for item in dependencies[tag])
        else:
            shortest[tag] = [tag]
            critical[tag] = [tag]
            path_counts[tag] = 1
    descendants: dict[str, set[str]] = {}
    for tag in reversed(tags):
        closure = set()
        for dependent in dependents[tag]:
            closure.add(dependent)
            closure.update(descendants[dependent])
        descendants[tag] = closure
    layers: dict[int, list[str]] = defaultdict(list)
    for row in records:
        layers[row["layer"]].append(row["tag"])
    adjacency = {
        tag: {
            "dependencies": dependencies[tag],
            "dependents": dependents[tag],
            "ancestors": sorted(ancestors[tag], key=rank.__getitem__),
            "descendants": sorted(descendants[tag], key=rank.__getitem__),
            "foundation_path": shortest[tag],
            "shortest_root_path": shortest[tag],
            "critical_root_path": critical[tag],
            "root_path_count": path_counts[tag],
        }
        for tag in tags
    }
    graph_identity = _digest(
        "\n".join(
            f'{edge["dependency"]}\0{edge["dependent"]}' for edge in edges
        )
    )
    return {
        "schema": "peano-lab-bertrand-proof-graph-v1",
        **{key: value for key, value in receipt.items() if key != "tactics"},
        "graph_sha256": graph_identity,
        "orientation": "dependency_to_dependent",
        "path_policy": {
            "foundation_path_alias": "shortest_root_path",
            "shortest_root_path": "fewest_edges_from_any_foundation",
            "critical_root_path": "dependency_depth_witness",
            "tie_break": "enrollment_order_lexicographic",
            "includes_endpoints": True,
        },
        "foundations": [tag for tag in tags if not dependencies[tag]],
        "terminals": [tag for tag in tags if not dependents[tag]],
        "layers": [
            {"index": index, "nodes": layers[index]}
            for index in range(receipt["layer_count"])
        ],
        "nodes": [
            {
                "tag": row["tag"],
                "name": row["name"],
                "scope": row["scope"],
                "status": row["status"],
                "alpha_edition_version": row["alpha_edition_version"],
                "proof_edition_version": row["proof_edition_version"],
                "alpha_evidence": row["alpha_evidence"],
                "alpha_checked_use": row["alpha_checked_use"],
                "stable_member": row["stable_member"],
                "source_evidence_status": row["source_evidence_status"],
                "layer": row["layer"],
                "summary": row["summary"],
                "href": f'../tag/{row["tag"]}.html',
            }
            for row in records
        ],
        "edges": edges,
        "adjacency": adjacency,
    }


def _render_index(records: list[dict[str, Any]], receipt: dict[str, Any]) -> bytes:
    layers = "".join(
        f'<option value="{index}">Layer {index}</option>'
        for index in range(receipt["layer_count"])
    )
    cards = []
    for row in records:
        search = " ".join(
            [
                row["name"],
                row["tag"],
                row["summary"],
                row["status_label"],
                *(item["name"] for item in row["dependencies"]),
            ]
        ).lower()
        cards.append(
            f'''<article class="pa-proof-result pa-status-{row["scope"]}"
data-pa-theorem data-name="{_escape(row["name"])}" data-tag="{row["tag"]}"
data-status="{row["scope"]}" data-layer="{row["layer"]}"
data-search="{_escape(search)}"><a href="tag/{row["tag"]}.html">
<code>{row["tag"]}</code> · <strong>{_escape(row["name"])}</strong></a>
<p>{_escape(row["summary"])}</p><small>layer {row["layer"]} ·
{len(row["lines"])} lines · {_escape(row["status_label"])}</small></article>'''
        )
    graph_href = (
        f'graph.html?target={receipt["root_tag"]}'
        "&amp;view=prerequisites&amp;edges=focus"
    )
    layer_links = "".join(
        f'<a href="?layer={index}">{index}</a>'
        for index in range(receipt["layer_count"])
    )
    atlas = _campaign_navigation("../../")
    body = f'''<header class="pa-proof-header pa-hero">
<p><a href="../../arithmetic-library/bertrand-campaign.html">Jupyter Book</a></p>
<h1>Bertrand Proof Explorer</h1>
<p>The complete replay-free reading surface for the transitive dependency
closure of <code>bertrand_strict</code>.</p>
<div class="pa-proof-stats"><b>{receipt["graph_checked_use_count"]}</b> checked-use theorems ·
<b>{receipt["edge_count"]}</b> edges ·
<b>{receipt["formal_line_count"]:,}</b> tactic lines ·
<b>{receipt["layer_count"]}</b> layers</div>
<p>Alpha v19 preserves the independently closed entire graph: {receipt["graph_stable_closed_count"]}
Stable theorems and {receipt["graph_alpha_closed_count"]} Alpha-only theorems.
The source-origin filter preserves release membership; Alpha-only checked use
does not grant Stable membership.</p>
<nav><a href="{graph_href}">
Open the complete interactive proof map</a>
<a href="defined/index.html?v={CAMPAIGN_HTML_REVISION}">Definition-aware edition</a>{atlas}</nav></header>
<main data-proof-dashboard data-pa-explorer-index>
<section class="pa-proof-controls"><label>Search
<input data-proof-search type="search"></label><label>Release membership
<select data-proof-status><option value="all">All</option>
<option value="public">Stable checked-use ({receipt["public_count"]})</option>
<option value="candidate">Alpha-only checked-use ({receipt["candidate_count"]})</option>
</select></label><label>Layer <select data-proof-layer>
<option value="all">All {receipt["layer_count"]} layers</option>{layers}</select>
</label><button data-proof-clear type="button">Clear</button>
<output data-proof-count>{receipt["graph_checked_use_count"]} checked-use theorems</output></section>
<section class="pa-layer-map">{layer_links}</section>
<section class="pa-proof-results">{''.join(cards)}</section></main>'''
    return _page("Bertrand Proof Explorer", "index", body)


def _render_graph(graph: dict[str, Any]) -> bytes:
    data = _javascript_assignment("PA_PROOF_GRAPH", graph)
    root = graph["root_tag"]
    atlas = _campaign_navigation("../../")
    evidence_overlay = r'''<script id="pa-bertrand-release-evidence">
(function () {
  "use strict";
  function install() {
    var root = document.querySelector("[data-dependency-graph]");
    var payload = window.PA_PROOF_GRAPH;
    if (!root || !payload || !Array.isArray(payload.nodes)) return;
    var title = root.querySelector("[data-graph-title]");
    var status = root.querySelector("[data-graph-status]");
    if (!title || !status || typeof MutationObserver !== "function") return;
    var nodes = new Map(payload.nodes.map(function (node) {
      return [node.tag, node];
    }));
    function showEvidence() {
      var tag = title.textContent.split(" · ", 1)[0].trim();
      var node = nodes.get(tag);
      if (!node || node.alpha_checked_use !== true) return;
      status.className = "pa-status-public";
      status.textContent = node.stable_member ?
        "Stable checked-use theorem; independently closed" :
        "Alpha v19 checked-use theorem; independently kernel and Lean verified; not Stable";
    }
    new MutationObserver(showEvidence).observe(title, {
      childList: true, characterData: true, subtree: true
    });
    showEvidence();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", install, { once: true });
  } else {
    install();
  }
})();
</script>'''
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Complete Bertrand dependency map</title>
<link rel="stylesheet" href="assets/explorer.css">
<script id="pa-proof-graph-data">{data}</script>
<script defer src="assets/explorer.js"></script></head>
<body class="pa-proof-site" data-page="graph">
<header class="pa-proof-header pa-graph-heading"><nav aria-label="Proof Explorer">
<a href="index.html">Theorem index</a>
<a href="defined/graph.html?target={root}&amp;view=neighborhood&amp;definitions=visible&amp;edges=focus&amp;v={CAMPAIGN_HTML_REVISION}">Definition-aware graph</a>
<a href="../../arithmetic-library/bertrand-campaign.html">Jupyter Book</a>
{atlas}
</nav><p class="pa-kicker">Interactive proof map</p>
<h1>The complete Bertrand proof</h1>
<p>Explore every dependency of <code>bertrand_strict</code>, from native
arithmetic foundations through the central-binomial argument and finite
covering.</p></header>
<main class="pa-graph-page" data-dependency-graph data-graph-json="api/graph.json">
<section class="pa-graph-controls" aria-labelledby="graph-controls-title">
<h2 id="graph-controls-title">Choose a path</h2><form data-graph-form>
<label>Optional start theorem <input data-graph-source type="search"
list="pa-graph-theorems" autocomplete="off" placeholder="Automatic root"></label>
<label>Target theorem <input data-graph-target type="search"
list="pa-graph-theorems" autocomplete="off" required value="{root}"></label>
<label>View <select data-graph-view>
<option value="critical">Critical/deepest premise chain</option>
<option value="shortest">Short premise chain</option>
<option value="corridor">All routes from start to target</option>
<option value="prerequisites" selected>Complete prerequisite cone</option>
<option value="neighborhood">Direct neighborhood</option>
<option value="dependents">Complete dependent cone</option>
<option value="corpus">Entire Bertrand proof corpus</option></select></label>
<label>Arrows <select data-graph-edges>
<option value="focus" selected>Focused: path + target</option>
<option value="none">Hide arrows</option>
<option value="all">All direct arrows (heavy)</option></select></label>
<button type="submit">Draw path</button></form>
<datalist id="pa-graph-theorems"></datalist>
<p class="pa-graph-control-note">The complete cone contains all 544 theorem
nodes. Focused arrows keep the initial view readable; choose all arrows for
the literal 1,917-edge graph.</p></section>
<div class="pa-graph-layout"><section class="pa-graph-canvas-panel"
aria-labelledby="graph-canvas-title"><div class="pa-graph-toolbar"><div>
<h2 id="graph-canvas-title">Layered dependency graph</h2>
<p data-graph-summary aria-live="polite">Loading theorem graph…</p></div>
<div class="pa-graph-zoom" aria-label="Graph viewport controls">
<button type="button" data-graph-zoom="in" aria-label="Zoom in">+</button>
<button type="button" data-graph-zoom="out" aria-label="Zoom out">−</button>
<button type="button" data-graph-center>Center target</button>
<button type="button" data-graph-fit>Fit view</button></div></div>
<div class="pa-graph-stage" data-graph-stage><svg data-graph-svg tabindex="0"
role="group" aria-labelledby="graph-canvas-title graph-instructions">
<text x="24" y="42">Loading theorem graph…</text></svg></div>
<p id="graph-instructions" class="pa-graph-instructions">Arrows run from
prerequisite to dependent. Click a mark to select it, use the proof link for
the exact statement and tactic body, drag to pan, and zoom with the controls.</p>
<div class="pa-graph-legend" aria-label="Graph legend">
<span><i class="pa-legend-node pa-legend-selected"></i> target</span>
<span><i class="pa-legend-node pa-legend-critical"></i> chosen chain</span>
<span><i class="pa-legend-node pa-legend-public"></i> Stable checked-use theorem</span>
<span><i class="pa-legend-node pa-legend-candidate"></i> Alpha-only checked-use theorem; not Stable</span>
<span><i class="pa-legend-edge pa-legend-declared"></i> declared edge</span>
</div></section>
<aside class="pa-graph-details" aria-labelledby="graph-details-title">
<p class="pa-eyebrow">Selected theorem</p>
<h2 id="graph-details-title" data-graph-title tabindex="-1">Loading…</h2>
<p data-graph-status></p><p data-graph-description></p>
<dl data-graph-metadata></dl>
<p><a class="pa-graph-proof-link" data-graph-proof href="index.html">
Open exact theorem page →</a></p>
<h3>Direct prerequisites</h3><ul class="pa-graph-relation-list"
data-graph-dependencies></ul><h3>Direct dependents</h3>
<ul class="pa-graph-relation-list" data-graph-dependents></ul></aside></div>
<section class="pa-graph-path-fallback" aria-labelledby="graph-path-title">
<p class="pa-eyebrow">Text alternative</p><h2 id="graph-path-title">
Ordered premise chain</h2><p data-graph-path-note></p>
<ol data-graph-path-list><li>Loading path…</li></ol></section></main>
{evidence_overlay}</body></html>
'''.encode("utf-8")


def _relation(items: list[dict[str, Any]]) -> str:
    if not items:
        return "none"
    return " ".join(
        f'<a class="pa-theorem-ref" href="{item["tag"]}.html">'
        f'<code>{item["tag"]}</code> {_escape(item["name"])}</a>'
        for item in items
    )


def _render_theorem(
    row: dict[str, Any],
    previous: dict[str, Any] | None,
    following: dict[str, Any] | None,
) -> bytes:
    counts = Counter(line["tactic"] for line in row["lines"])
    moves = [
        f"{label} ({counts[tactic]})"
        for tactic, label in (
            ("induction", "structural induction"),
            ("cases", "case analysis"),
            ("have", "intermediate claims"),
            ("rewrite", "equality transport"),
            ("norm_num", "closed numeral normalization"),
        )
        if counts[tactic]
    ]
    guide = ", ".join(moves) if moves else "direct introduction and elimination"
    lines = "".join(
        f'<li class="pa-proof-line" id="{line["id"]}" '
        f'data-line="{line["number"]}" data-tactic="{_escape(line["tactic"])}" '
        f'data-line-id="{line["stable_id"]}"><a class="pa-line-number" '
        f'href="#{line["id"]}">{line["number"]:04d}</a>'
        f'<code>{_render_command(line)}</code></li>'
        for line in row["lines"]
    )
    previous_link = (
        f'<a href="{previous["tag"]}.html">← {_escape(previous["name"])}</a>'
        if previous
        else ""
    )
    following_link = (
        f'<a href="{following["tag"]}.html">{_escape(following["name"])} →</a>'
        if following
        else ""
    )
    source_href = f'{GITHUB_ROOT}/{row["source"]["path"]}'
    receipt = row["body_receipt"] or {}
    atlas = _campaign_navigation("../../../")
    body = f'''<header class="pa-proof-header pa-theorem-heading"><nav>
<a href="../index.html">Explorer</a>
<a href="../defined/tag/{_escape(row["tag"])}.html">Definition-aware theorem</a>
<a href="../defined/graph.html?target={_escape(row["tag"])}&amp;view=neighborhood&amp;definitions=visible&amp;edges=focus">Theorem and definition graph</a>
{atlas}{previous_link}{following_link}</nav>
<p class="pa-tag">{row["tag"]}</p><h1>{_escape(row["name"])}</h1>
<p class="pa-status-{row["scope"]}">{_escape(row["status_label"])}</p>
<p>{_escape(row["summary"])}</p></header>
<main class="pa-theorem-layout"><div class="pa-proof-panel">
<section class="pa-statement"><h2>Exact expanded PA statement</h2>
<button data-copy-target="statement" type="button">Copy</button>
<pre id="statement"><code>{_escape(row["statement"])}</code></pre></section>
<section class="pa-informal-proof"><h2>Structural proof guide</h2>
<p>{_escape(row["summary"])}</p><p>Direct prerequisites:
{_escape(', '.join(item['name'] for item in row['dependencies']) or 'none')}.
The authored body proceeds by {_escape(guide)}.</p></section>
<section><h2>Proof neighborhood</h2><h3>Direct dependencies</h3>
<div class="pa-chip-row">{_relation(row["dependencies"])}</div>
<h3>Direct dependents</h3><div class="pa-chip-row">
{_relation(row["dependents"])}</div></section>
<section><h2>Formal native tactic body</h2>
<p>Dependencies are hypotheses of the historical Alpha-v12 body receipt.
The complete historical Alpha-v18 proof bundle independently checks every
dependency; current Alpha v19 preserves that checked theorem use without
changing Stable membership.</p>
<ol class="pa-formal-proof">{lines}</ol></section></div>
<aside class="pa-proof-sidebar pa-trust-panel"><h2>Receipt and provenance</h2>
<dl><dt>Enrollment index</dt><dd>{row["enrollment_index"]}</dd>
<dt>Layer</dt><dd>{row["layer"]}</dd><dt>Lines</dt><dd>{len(row["lines"])}</dd>
<dt>Current Alpha edition</dt><dd>{_escape(row["alpha_edition_version"])}</dd>
<dt>Proof-bearing Alpha edition</dt><dd>{_escape(row["proof_edition_version"])}</dd>
<dt>Current release evidence</dt><dd>{_escape(row["alpha_evidence"])}</dd>
<dt>Checked theorem use</dt><dd>{"yes" if row["alpha_checked_use"] else "no"}</dd>
<dt>Stable membership</dt><dd>{"yes" if row["stable_member"] else "no"}</dd>
<dt>Historical Alpha-v12 evidence</dt><dd>{_escape(row["source_evidence_status"])}</dd>
<dt>Body proof nodes</dt><dd>{receipt.get('proof_nodes', 'n/a')}</dd>
<dt>Statement SHA-256</dt><dd><code>{row["statement_sha256"]}</code></dd>
<dt>Script SHA-256</dt><dd><code>{row["script_sha256"]}</code></dd>
<dt>Source</dt><dd><a href="{_escape(source_href)}">
{_escape(row["source"]["path"])}</a></dd>
<dt>Source SHA-256</dt><dd><code>{row["source"]["sha256"]}</code></dd>
</dl></aside></main>'''
    return _page(f'{row["tag"]} — {row["name"]}', "theorem", body, "../")


def _files() -> tuple[dict[str, bytes], dict[str, Any]]:
    catalog, closure = _load_catalog()
    records, edges, receipt = _records(catalog, closure)
    graph = _graph_payload(records, edges, receipt)
    corpus = {
        "schema": "peano-lab-bertrand-proof-corpus-v1",
        **{key: value for key, value in receipt.items() if key != "tactics"},
        "theorems": records,
    }
    files: dict[str, bytes] = {
        "index.html": _render_index(records, receipt),
        "graph.html": _render_graph(graph),
        "api/corpus.json": _json_bytes(corpus),
        "api/graph.json": _json_bytes(graph),
    }
    for name, expected_sha256 in PINNED_ASSETS.items():
        payload = (ASSET_SOURCE / name).read_bytes()
        if _digest(payload) != expected_sha256:
            raise ValueError(f"shared explorer asset changed: {name}")
        files[f"assets/{name}"] = payload
    for index, row in enumerate(records):
        files[f'tag/{row["tag"]}.html'] = _render_theorem(
            row,
            records[index - 1] if index else None,
            records[index + 1] if index + 1 < len(records) else None,
        )
        target = f'../tag/{row["tag"]}.html'
        files[f'name/{row["name"]}.html'] = (
            '<!doctype html><html><head><meta charset="utf-8">'
            f'<meta http-equiv="refresh" content="0; url={target}">'
            f'<link rel="canonical" href="{target}">'
            f'<script>location.replace({json.dumps(target)}+'
            'location.search+location.hash)</script></head><body>'
            f'<a href="{target}">{_escape(row["name"])}</a></body></html>\n'
        ).encode("utf-8")
    manifest_files = [
        {"path": path, "bytes": len(payload), "sha256": _digest(payload)}
        for path, payload in sorted(files.items())
    ]
    aggregate = _digest(
        "\n".join(f'{item["path"]}\0{item["sha256"]}' for item in manifest_files)
    )
    manifest = {
        "schema": "peano-lab-bertrand-proof-explorer-manifest-v1",
        **{key: value for key, value in receipt.items() if key != "tactics"},
        "generated_file_count": len(files) + 1,
        "canonical_tag_page_count": len(records),
        "name_alias_page_count": len(records),
        "aggregate_sha256": aggregate,
        "required_assets": sorted(PINNED_ASSETS),
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
        for path in sorted(OUTPUT.rglob("*"), reverse=True):
            relative = path.relative_to(OUTPUT)
            if (
                path.is_file()
                and relative.parts[0] not in RESERVED_SUBTREES
                and str(relative) not in expected
            ):
                path.unlink()
        for path in sorted(OUTPUT.rglob("*"), reverse=True):
            if path.is_dir() and not any(path.iterdir()):
                path.rmdir()


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
            and path.relative_to(OUTPUT).parts[0] not in RESERVED_SUBTREES
            and str(path.relative_to(OUTPUT)) not in expected
        )
    if drift:
        print(
            "Bertrand proof explorer drift: "
            + ", ".join(sorted(set(drift))[:20]),
            file=sys.stderr,
        )
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files, manifest = _files()
    if args.check:
        if not _check(files):
            return 1
        print(
            "verified Bertrand proof explorer: "
            f'{manifest["generated_file_count"]} files, '
            f'{manifest["aggregate_sha256"]}'
        )
        return 0
    _write(files)
    print(
        "wrote Bertrand proof explorer: "
        f'{manifest["generated_file_count"]} files, '
        f'{manifest["aggregate_sha256"]}'
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
