#!/usr/bin/env python3
"""Build a planning-only campaign, without modifying any sealed release.

All outputs are deterministic. This script cannot admit or certify a theorem.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html import escape
import json
from pathlib import Path
import re

from constructive_proof_explorer_template import render_canonical_campaign_plan
from sqrt2_power_campaign_spec import PARENT, SCHEMA, campaign_plan

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "book/_static/constructive-sqrt2-power-campaign"
DOSSIER = ROOT / "PLAN/32_sqrt2_power_irrationality_campaign.md"
PINS = {
    "campaign.json": "ed62081e992ca40e7e7788e0fbb8500a34bf94bbe0c75854616edce47811065f",
    "index.html": "08ac27a37e94458e9b19d4134691170c37519e88f3753cdd35479402a5d69839",
    "definitions.json": "32da2185fd21fb1d0b400404f9b832425a4c35e75be392a3f5b5f73f8464aebf",
}
SAFE_ID = re.compile(r"(?:IRD[0-9]{2}|IR[0-9]{3}|TR[0-9]{3}|ENG[0-9]{3})\Z")
PILOT_MANIFEST_SHA256 = "5e2e17f5c1183833dc99de299662d5f095a418306415a99a022f3b7d79816da5"
WAVE_INDEX = ROOT / "research/arithmetic-library/sqrt2-power/observations/shared-wave-index-v5.json"
WAVE_INDEX_SHA256 = "d09ade0906b3dc2c9fc1a1659ceee004cd35db264ff329cbc2cbbcbde6c8ab3a"


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False,
                       allow_nan=False) + "\n").encode()


def digest(value):
    return sha256(value).hexdigest()


def validate_plan(plan):
    """Fail closed on fake authority, missing obligations, cycles and bad types."""
    if plan.get("schema") != SCHEMA or plan.get("authority") != "planning_only":
        raise ValueError("not a planning-only campaign")
    for field in ("verified_new_theorem_count", "admitted_new_definition_count"):
        if type(plan.get(field)) is not int or plan[field] != 0:
            raise ValueError("a plan cannot confer proof or definition authority")
    by_id = {}
    for row in plan["nodes"]:
        name = row.get("id", "")
        if not SAFE_ID.fullmatch(name) or name in by_id:
            raise ValueError("invalid or duplicate node id")
        if row.get("authority") != "planning_only":
            raise ValueError("non-planning authority")
        kind = row.get("kind")
        if kind not in {"definition", "lemma", "engineering"}:
            raise ValueError("invalid planning node kind")
        if row.get("status") != ("proposed" if kind == "definition" else "planned"):
            raise ValueError("unproved node presented as completed")
        if not row.get("title") or not row.get("contract"):
            raise ValueError("empty mathematical contract")
        if type(row.get("phase")) is not int or row["phase"] not in {0, 1, 2}:
            raise ValueError("invalid execution phase")
        if kind == "definition":
            if row.get("kernel_definition_id") is not None or row.get("expansion_ast_sha256") is not None:
                raise ValueError("proposed definition masquerades as reviewed")
            params = row["parameters"]
            if row["arity"] != len(params) or len(params) != len(set(params)):
                raise ValueError("invalid definition parameters")
        else:
            for field in ("statement_ast_sha256", "native_ha_receipt", "independent_lean_receipt"):
                if row.get(field) is not None:
                    raise ValueError("planning contract carries fake proof evidence")
            if row.get("method") not in plan["methods"] or not row.get("induction"):
                raise ValueError("missing automation/induction contract")
        by_id[name] = row
    edges = []
    for name, row in by_id.items():
        deps = row.get("deps")
        if not isinstance(deps, list) or len(deps) != len(set(deps)):
            raise ValueError("repeated or malformed prerequisite")
        definitions = row.get("definitions", [])
        if not isinstance(definitions, list) or len(definitions) != len(set(definitions)):
            raise ValueError("repeated or malformed definition use")
        for dep in deps:
            if dep not in by_id or dep == name:
                raise ValueError("missing or self prerequisite")
            if row["kind"] == "definition" and by_id[dep]["kind"] != "definition":
                raise ValueError("definition assumes a theorem")
            if row["phase"] == 1 and by_id[dep]["phase"] == 2:
                raise ValueError("irrationality depends on future transcendence")
            if row["kind"] == "lemma" and by_id[dep]["kind"] == "engineering":
                raise ValueError("engineering is not a mathematical premise")
            edges.append(dict(source=dep, target=name, kind=(
                "proposed_definition_dependency" if row["kind"] == "definition"
                else "engineering_prerequisite" if row["kind"] == "engineering"
                else "planned_prerequisite")))
        for dep in definitions:
            if dep not in by_id or by_id[dep]["kind"] != "definition":
                raise ValueError("unknown proposed definition")
            edges.append(dict(source=dep, target=name, kind="proposed_definition_use"))
    order, visiting, ranks = [], set(), {}

    def visit(name):
        if name in visiting:
            raise ValueError("cyclic planning DAG")
        if name in ranks:
            return ranks[name]
        visiting.add(name)
        row = by_id[name]
        parents = row["deps"] + row.get("definitions", [])
        ranks[name] = max((visit(dep) + 1 for dep in parents), default=0)
        visiting.remove(name)
        order.append(name)
        return ranks[name]

    for name in by_id:
        visit(name)
    if plan["active_target"] not in by_id or plan["next_target"] not in by_id:
        raise ValueError("missing endpoint")
    pilot_ids = set()
    if len(plan.get("pilot", [])) != plan["budget"]["pilot_lemma_limit"]:
        raise ValueError("the pilot must have its fixed twelve-child scope")
    for child in plan["pilot"]:
        identifier = child.get("id", "")
        if not re.fullmatch(r"P(?:0[1-9]|1[0-2])", identifier) or identifier in pilot_ids:
            raise ValueError("invalid or duplicate pilot child")
        pilot_ids.add(identifier)
        parent = by_id.get(child.get("parent"))
        if not parent or parent["kind"] != "lemma" or parent["phase"] != 1:
            raise ValueError("pilot must belong to an irrationality lemma")
        if (child.get("closes_parent") is not False or
            child.get("statement_ast_sha256") is not None or
            child.get("status") != "blocked_on_contract_and_premise_elaboration"):
            raise ValueError("pilot contract masquerades as proof evidence")
        if (child.get("method") not in plan["methods"] or
            not child.get("contract") or not child.get("required_negative_test")):
            raise ValueError("incomplete pilot contract")
    return dict(order=order, ranks=ranks, edges=edges,
                counts=dict(Counter(row["kind"] for row in by_id.values())),
                semantics="Planned dependencies, never verified proof edges")


def parent_bytes():
    result = {}
    for name, expected in PINS.items():
        path = ROOT / PARENT / name
        if path.is_symlink():
            raise ValueError("parent snapshot must not be a symlink")
        data = path.read_bytes()
        if digest(data) != expected:
            raise ValueError("immutable parent snapshot changed: " + name)
        result[name] = data
    return result


def extend_atlas(parent, plan):
    """Append only two open milestones and one family; preserve old rows exactly."""
    result = deepcopy(parent)
    if len(parent["nodes"]) != 144 or len(parent["families"]) != 12:
        raise ValueError("unexpected parent blueprint")
    result["families"].append(dict(id="F13", slug="effective-transcendence",
        title="Effective irrationality and transcendence", color="#8e5c32",
        summary="First positive HA irrationality of (sqrt2)^(sqrt2); then full polynomial apartness. Planning only.",
        goal_ids=["G121", "G122"]))
    result["nodes"].extend([
        dict(id="G121", family="F13", kind="goal", layer=6, difficulty="research",
             status="open", title="Positive irrationality of (sqrt2)^(sqrt2)",
             statement="forall a in Z, b>0. exists n. |b*u_n-a|>2*b*2^(-n), with certified |u_n-c|<=2^(-n).",
             deps=["T04", "T05", "T11", "T12", "T15"],
             conceptual_refs=["G072", "G081", "T13"], definition_refs=[],
             why="Active priority. Exact quadratic norms, integer pigeonhole and finite confluent interpolation; solver-first search with native reconstruction. The attached detailed planning DAG is not proof evidence.",
             planning_route="../map.html?target=IR072", native_ha_proved=False),
        dict(id="G122", family="F13", kind="goal", layer=7, difficulty="summit",
             status="open", title="Positive transcendence of (sqrt2)^(sqrt2)",
             statement="forall nonzero integer polynomial codes P. exists n,w. |P(u_n)|>2*M_P*2^(-n), witnessed by exact finite arithmetic.",
             deps=["G121", "T12"], conceptual_refs=["G091"], definition_refs=[],
             why="Phase two after irrationality. General algebraic presentations, norm bounds and a positive polynomial-certificate bridge remain open. No claim that the classical Lean development is already an HA proof.",
             planning_route="../map.html?target=TR006", native_ha_proved=False),
    ])
    result["meta"].update(node_count=146, goal_count=122,
        planning_extension="sqrt2-power-ha-campaign-plan-v1",
        historical_120_goal_snapshot_unchanged=True,
        new_extension_ha_verified_count=0)
    result["subtitle"] = "122 milestones: immutable 120-goal parent plus two open transcendence-campaign targets"
    result["sources"].append(dict(id="SRC_SQRT2_PLAN", kind="campaign_plan",
        label="Non-LLM-first irrationality planning dossier (not proof evidence)",
        path="PLAN/32_sqrt2_power_irrationality_campaign.md"))
    # Only the milestone DAG is audited here; never claim a new theorem-catalog audit.
    from sync_constructive_grand_campaign import _milestone_dag
    _milestone_dag(result)
    if result["nodes"][:144] != parent["nodes"] or result["definitions"] != parent["definitions"]:
        raise ValueError("historical evidence or vocabulary was altered")
    return result


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError("atlas/template extension point changed: " + old[:75])
    return source.replace(old, new, 1)


def atlas_html(source, atlas):
    source = source.decode()
    revision = atlas["meta"]["current_alpha_catalog_sha256"][:12]
    # Presentation-only adjustments are made before replacing the inline JSON,
    # so no historical record or source reference in that snapshot is rewritten.
    source = source.replace("120 major campaign milestones", "122 major campaign milestones")
    source = source.replace("five mathematical domains to twelve families", "six mathematical domains to thirteen families")
    source = source.replace("underlying 144-node proof graph", "underlying 146-node milestone graph")
    source = source.replace("between five mathematical domains", "between six mathematical domains")
    source = re.sub(r"\bv=[0-9a-f]{12}\b", "v=" + revision, source)
    source = re.sub(r'href="[^"]+" data-proof-home',
        'href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/?v=' + revision + '" data-proof-home', source)
    opening = '<script type="application/json" id="campaign-data">'
    start = source.index(opening) + len(opening)
    end = source.index("</script>", start)
    inline = json.dumps(atlas, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    source = source[:start] + inline + source[end:]
    source = once(source, '          families: ["F12"], color: "#327f91"\n        }',
        '          families: ["F12"], color: "#327f91"\n        },\n'
        '        {id: "D06", title: "Effective transcendence", summary: "Positive finite certificates; irrationality first, transcendence next. Open planning extension.", families: ["F13"], color: "#8e5c32"}')
    source = source.replace("The five research domains do not cover", "The research domains do not cover")
    source = once(source, '          D05: { x: 797, y: 240 }',
        '          D05: { x: 797, y: 240 },\n          D06: { x: 797, y: 55 }')
    source = once(source, "      function explorerBase(route) {\n",
        "      function explorerBase(route) {\n")  # assert the extension point
    source = once(source, '        if (deployed) return "../" + route + "/explorer/defined/";\n'
        '        return "../" + currentFamilies[route] + "/" + route + "/explorer/defined/";',
        '        return "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + route + "/explorer/defined/";')
    source = once(source, '        document.querySelector("[data-proof-home]").setAttribute("href", proofHref(\n'
        '          /\\/proofs\\/grand-campaign(?:\\/|$)/.test(window.location.pathname || "") ? "../index.html" :\n'
        '          "../constructive-research-explorer-v34/index.html"));',
        '        document.querySelector("[data-proof-home]").setAttribute("href", proofHref(\n'
        '          "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/"));')
    source = once(source, '<p class="notice" data-node-caveat></p>',
        '<p class="notice" data-node-caveat></p><p data-plan-navigation hidden><a data-plan-link>Open the detailed planned lemma DAG (not a proof)</a></p>')
    source = once(source, '        ui.rationale.textContent = node.why || "This node supplies a constructive arithmetic ingredient for later goals.";',
        '        ui.rationale.textContent = node.why || "This node supplies a constructive arithmetic ingredient for later goals.";\n'
        '        document.querySelector("[data-plan-navigation]").hidden = !node.planning_route;\n'
        '        if (node.planning_route) document.querySelector("[data-plan-link]").setAttribute("href", node.planning_route);')
    source = once(source, "<body>", '<body><aside class="notice" style="margin:1rem;padding:1rem">'
        '<strong>Active planning extension: F13 / G121 / G122.</strong> '
        '<a href="../index.html">Irrationality first, transcendence next</a>. '
        '122 goals; 0 new proved theorems. The 120-goal parent and all sealed proof evidence are unchanged. '
        '<a href="../map.html?target=IR072">Open the detailed planning DAG</a>.</aside>')
    return source.encode()


def page(title, content, revision, *, depth=0, eyebrow="Unproved contract · No Alpha or Stable authority"):
    prefix = "../" * depth
    esc = escape
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)} — HA campaign plan</title><link rel="stylesheet" href="{prefix}assets/proofs.css?v={revision}"><link rel="stylesheet" href="{prefix}assets/campaign-plan.css?v={revision}"></head><body class="family-page sqrt2-power-page"><header class="family-hero"><div class="shell"><nav class="crumbs"><a href="{prefix}index.html?v={revision}">Irrationality campaign</a><span>/</span><a href="{prefix}map.html?v={revision}">Planning DAG</a><span>/</span><a href="{prefix}grand-campaign/index.html?view=family&amp;focus=F13&amp;v={revision}">Grand campaign</a></nav><p class="eyebrow">{esc(eyebrow)}</p><h1>{esc(title)}</h1></div></header><main class="shell family-main">{content}</main></body></html>'''.encode()


def pilot_results_files(revision):
    from sqrt2_power_pilot_results import ARCHIVE, observation_results
    if digest((ARCHIVE / "manifest.json").read_bytes()) != PILOT_MANIFEST_SHA256:
        raise ValueError("recorded pilot manifest changed; no silent evidence update")
    result, files = observation_results()
    counts = result["counts"]
    rows, details = [], []
    coverage = {"full_pilot_contract": "Full pilot contract",
                "supporting_subleaf_only": "Supporting subleaf only",
                "unelaborated": "Not dispatched"}
    def solver_text(value):
        if not value:
            return "—"
        if value["status"] in {"unsat", "Theorem", "Unsatisfiable"}:
            return "Classical hit"
        return "Limit / unresolved" if (value.get("reason") or "").endswith("limit") else "Unresolved"
    for row in result["rows"]:
        identifier = row["pilot_id"]
        checked = row["status"] == "fresh_ordinary_HA_checked"
        label = coverage[row["coverage"]] + (" · HA checked" if checked else "")
        statuses = "".join("<td>" + escape(solver_text(row["solvers"].get(s))) + "</td>"
                           for s in ("z3", "eprover", "vampire"))
        rows.append(f'<tr><th scope="row"><a href="#{identifier}">{identifier}</a></th><td>{escape(label)}</td>{statuses}</tr>')
        body = f'<p>{escape(row["interpretation"])}</p>'
        if row["source"]:
            body += '<details><summary>Exact expanded HA formula</summary><pre class="contract"><code>' + escape(row["source"]) + '</code></pre></details>'
        if checked:
            body += f'<p><a href="{row["certificate_path"]}" download>Download the actual canonical certificate (gzip)</a> · {row["proof_nodes"]:,} proof-body nodes.</p><p class="contract">Uncompressed SHA-256: {row["certificate_sha256"]}</p>'
        details.append(f'<section class="release-note" id="{identifier}"><h2>{identifier} · {escape(label)}</h2>{body}<p>Planning parent: <a href="lemmas/{row["parent"]}.html">{row["parent"]}</a> · <a href="map.html?target={row["parent"]}&amp;view=prerequisites">Open its prerequisite cone</a>. This parent remains unproved.</p></section>')
    content = f'''<section class="release-note"><h2>Historical pilot baseline</h2><p>This page preserves the original run, including its P10 failure and its then-missing Lean checks. <a href="wave-results.html">Current shared-proof wave: checked P10, rational foundations, composition pieces and independent Lean checks</a>.</p></section><section class="release-note"><h2>What actually passed</h2><p>{counts['native_checked_leaves']} local arithmetic leaves passed fresh ordinary-HA replay: {counts['fully_checked_pilot_contracts']} full pilot instances and {counts['checked_supporting_subleaves']} supporting subleaves. <strong>0 irrationality parent obligations closed; 0 library admissions.</strong> P07 covers signed-integer frequencies only; its quadratic-field lift remains open. No independent Lean rebuild was performed in this baseline.</p><p>All 15 exported arithmetic premises were regenerated and freshly replayed first. Modified certificate bodies and false original targets were rejected. Contract-specific mathematical mutation witnesses are a separate remaining validation task.</p></section>
<section class="release-note"><h2>Native proofs and untrusted solver outcomes</h2><p>Two CPU seconds per solver call. A classical hit is not an HA certificate. The two experimental arms use the same native proof factory: solver hits gate an independent native reproof, not a proof-log translation. This measures an integration baseline, not solver acceleration.</p><div class="pilot-results-scroll"><table class="pilot-results-table"><thead><tr><th>Child</th><th>Native HA coverage</th><th>Z3</th><th>E</th><th>Vampire</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div><p>Recorded run: {result['wall_seconds']:.2f} wall seconds. Native-only child CPU: {result['native_arm_cpu_seconds']:.2f} s; solver-gated native replay: {result['solver_gated_native_cpu_seconds']:.2f} s; solver/version probes: {result['external_cpu_seconds']:.2f} s; checked basis setup: {result['setup_cpu_seconds']:.2f} s. One proof/solver worker at a time.</p><p>Proof workers made no model calls. Agents wrote and reviewed contracts, generators and infrastructure; that engineering cost is not measured as zero.</p></section>
<section class="release-note"><h2>The large-number boundary is still open</h2><p>{escape(result['large_numeral_status'])}</p><p>{escape(result['pending'])}</p><p>Next: assemble bounded per-operation proof DAGs, then the finite-composition and approximation traces. No larger search or memory allowance is implied.</p></section>
<section class="release-note"><h2>Reproducible local evidence</h2><p><a href="api/pilot-results.json">Machine-readable results</a> · <a href="evidence/report.json.gz" download>Complete original run report (gzip)</a> · <a href="pilot.html">Original twelve planning contracts</a>. Certificates use the existing canonical bundle codec. Gzip is storage only; hashes bind the exact decompressed bytes. These observations are local, not promoted or deployed.</p></section>{''.join(details)}'''
    files["pilot-results.html"] = page("Bounded automation pilot — actual results", content, revision,
        eyebrow="Local execution evidence · No Alpha or Stable admission")
    files["api/pilot-results.json"] = json_bytes(result)
    return files


def node_path(row):
    return ("definitions/" if row["kind"] == "definition" else "lemmas/") + row["id"] + ".html"


def generated_files():
    plan = campaign_plan()
    audit = validate_plan(plan)
    plan["dag"] = audit
    by_id = {row["id"]: row for row in plan["nodes"]}
    parent = parent_bytes()
    atlas_parent = json.loads(parent["campaign.json"])
    revision = atlas_parent["meta"]["current_alpha_catalog_sha256"][:12]
    plan["parent_snapshots"] = PINS
    plan["current_catalog_revision"] = revision
    atlas = extend_atlas(atlas_parent, plan)
    files = {
        "index.html": render_canonical_campaign_plan(plan, revision=revision),
        "api/plan.json": json_bytes(plan),
        "plan.md": DOSSIER.read_bytes(),
        "grand-campaign/campaign.json": json_bytes(atlas),
        "grand-campaign/index.html": atlas_html(parent["index.html"], atlas),
        "grand-campaign/definitions.json": parent["definitions.json"],
        "assets/proofs.css": (ROOT / "deploy/proofs/proofs.css").read_bytes(),
    }
    for name in ("campaign-plan.css", "campaign-plan.js"):
        files["assets/" + name] = (ROOT / "scripts/assets" / name).read_bytes()
    for row in plan["nodes"]:
        refs = "".join(f'<li><a href="../{node_path(by_id[d])}?v={revision}">{escape(d)} — {escape(by_id[d]["title"])}</a></li>'
                       for d in row["deps"] + row.get("definitions", []))
        meta = (f'<p>Method: {escape(row["method"])}. Induction: {escape(row["induction"])}. Risk: {escape(row["risk"])}.</p>'
                if row["kind"] != "definition" else
                f'<p>Proposed arity: {row["arity"]}. Parameters: {escape(" ".join(row["parameters"]))}. No reviewed kernel definition exists yet.</p>')
        content = f'<section class="release-note"><strong>{row["id"]} · {row["status"]}</strong><p class="contract">{escape(row["contract"])}</p>{meta}<p>This is a human-readable planning contract, not a parsed kernel formula or accepted proof.</p></section><section class="release-note"><h2>Planned prerequisites and notation</h2><ul>{refs or "<li>No new campaign prerequisites; exact existing-premise audit still required.</li>"}</ul><a href="../map.html?target={row["id"]}&amp;view=prerequisites&amp;v={revision}">Open this dependency cone</a></section>'
        files[node_path(row)] = page(row["id"] + " — " + row["title"], content, revision, depth=1)
    for kind, folder in (("definition", "definitions"), ("lemma", "lemmas")):
        selected = [r for r in plan["nodes"] if (r["kind"] == "definition") == (kind == "definition")]
        entries = "".join(f'<li><a href="{row["id"]}.html?v={revision}">{row["id"]} — {escape(row["title"])}</a> ({row["status"]})</li>' for row in selected)
        files[folder + "/index.html"] = page("Proposed definitions" if kind == "definition" else "Planned lemmas and engineering gates", '<section class="release-note"><ol>' + entries + '</ol></section>', revision, depth=1)
    pilot_rows = []
    for child in plan["pilot"]:
        parent = by_id[child["parent"]]
        pilot_rows.append('<section class="release-note"><h2>' + escape(child["id"]) +
            ' · <a href="' + node_path(parent) + '">' + escape(parent["id"]) + '</a></h2>' +
            '<p class="contract">' + escape(child["contract"]) + '</p><p>Method: ' + escape(child["method"]) +
            '.</p><p>Required hostile check: ' + escape(child["required_negative_test"]) +
            '</p><p>This is the original planning contract. <a href="pilot-results.html#' + escape(child["id"]) + '">See actual bounded execution and exact coverage</a>. A successful child does not close its universal parent.</p></section>')
    files["pilot.html"] = page("Twelve bounded pilot contracts",
        '<section class="release-note"><p>ENG001/002 must freeze the exact formulas and authenticated premises first. '
        'Compare native-only and solver-hint runs on identical inputs; both share 60 CPU seconds / 90 wall seconds per child, '
        '768 MiB RSS and 8 MiB output, with a 1,200-second aggregate ceiling and one local worker. '
        'No unchanged retries; a single changed-strategy repair uses the original reservation. '
        'External solver success counts only after reconstruction of the original HA target.</p></section>' +
        ''.join(pilot_rows), revision)
    controls = '''<section class="release-note"><p>All arrows below are <strong>planned</strong>, not checked proof dependencies. Blue: proposed definition expansion; gray: notation use; amber: mathematical prerequisite; purple: engineering gate. Overview arrows may summarize longer planned paths.</p><form id="plan-controls"><label>View <select id="plan-view"><option value="overview">Milestone overview</option><option value="prerequisites">Selected prerequisite cone</option><option value="neighborhood">Selected neighborhood</option><option value="all">All obligations</option></select></label><label>Target <select id="plan-target"></select></label><label><input type="checkbox" id="plan-definitions"> Include proposed definitions</label><button type="button" id="plan-print">Print</button></form><p id="plan-summary" role="status"></p></section><section class="plan-graph-scroll"><svg id="plan-graph" role="img" aria-label="Planned lemma and definition dependency DAG"></svg></section><section class="release-note" id="plan-details" aria-live="polite"></section><noscript><p>The full contracts remain available in the <a href="lemmas/index.html">lemma directory</a> and <a href="definitions/index.html">definition directory</a>.</p></noscript>'''
    inline = json.dumps(plan, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    map_page = page("Planned proof and definition DAG", controls, revision).decode()
    files["map.html"] = map_page.replace("</body>", f'<script type="application/json" id="plan-data">{inline}</script><script src="assets/campaign-plan.js?v={revision}" defer></script></body>').encode()
    files.update(pilot_results_files(revision))
    from sqrt2_power_wave_page import build_wave_files
    files.update(build_wave_files(revision, page, WAVE_INDEX, WAVE_INDEX_SHA256))
    if "arithmetic-frontier.html" in files:
        # Bidirectional navigation without changing the frozen planning graph
        # or pretending that a checked supporting leaf closes its parent.
        from sqrt2_power_wave_page import label, parent
        evidence = json.loads(files["api/wave-results.json"])
        children = {}
        for row in evidence["rows"]:
            case = row["case"]
            if row["status"] == "fresh_ordinary_HA_checked" and f"checked/{case}.html" in files:
                children.setdefault(parent(case), set()).add(case)
        for goal, cases in children.items():
            name = f"lemmas/{goal}.html"
            links = ''.join(f'<li><a href="../checked/{case}.html">{case} — {escape(label(case))}</a></li>'
                            for case in sorted(cases))
            section = '<section class="release-note"><h2>Checked supporting leaves, not parent closure</h2><ul>'+links+'</ul><p>The planning contract above remains open. <a href="../arithmetic-frontier.html">Checked arithmetic DAG</a> · <a href="../wave-results.html">Complete execution evidence</a>.</p></section>'
            files[name] = once(files[name].decode(), '</main>', section+'</main>').encode()
        navigation = '<section class="release-note"><h2>From the plan to checked proofs</h2><p><a href="arithmetic-frontier.html">Open the checked arithmetic DAG</a> · <a href="local-definitions.html">Conservative definitions and theorem uses</a> · <a href="wave-results.html">All exact local evidence</a>. These are supporting results; the full irrationality target remains open.</p></section>'
        files["map.html"] = once(files["map.html"].decode(), '</main>', navigation+'</main>').encode()
    manifest = dict(schema="sqrt2-power-planning-build-v1", authority="planning_only",
                    new_ha_proofs=0, files={name: dict(bytes=len(data), sha256=digest(data)) for name, data in sorted(files.items())})
    files["api/manifest.json"] = json_bytes(manifest)
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = generated_files()
    if args.check:
        stale = [name for name, data in files.items() if not (OUTPUT / name).is_file() or (OUTPUT / name).read_bytes() != data]
        extra = [str(path.relative_to(OUTPUT)) for path in OUTPUT.rglob("*") if path.is_file() and str(path.relative_to(OUTPUT)) not in files]
        if stale or extra:
            raise SystemExit("stale/missing: " + repr(stale) + "; unregistered outputs: " + repr(extra))
    else:
        for name, data in files.items():
            target = OUTPUT / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    print(json.dumps(dict(status="planning_snapshots_match" if args.check else "planning_snapshots_generated", files=len(files), new_ha_proofs=0)))


if __name__ == "__main__":
    main()
