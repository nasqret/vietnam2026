"""Canonical-family local evidence pages; no admission or proof authority."""
from hashlib import sha256
from html import escape
import json
import re

from sqrt2_power_definitions import DEFINITIONS, definition_manifest
from sqrt2_power_rational_foundations import FOUNDATIONS, foundation_target
from sqrt2_power_binary_dag import formula_sha256
from sqrt2_power_wave_results import wave_results


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode()+b"\n"


def label(case):
    if case in {r[0] for r in FOUNDATIONS}:
        row = next(r for r in FOUNDATIONS if r[0] == case)
        return row[1].removeprefix("irat_eq_").replace("_", " ").capitalize()
    if re.fullmatch(r"P04-C[0-9]{2}", case):
        return "Finite composition trace · piece " + case[-2:]
    return {"P10": "Exact large-number inequality", "P08-eprover": "Reciprocal cancellation · E hint",
        "P08-vampire": "Reciprocal cancellation · Vampire hint", "P04-ground": "Full finite composition trace",
        "P04-soundness": "Constant-coefficient trace soundness", "IR016": "Twice-square zero theorem",
        "SN001": "Signed quadratic-norm zero criterion", "NG001": "Constructive natural strict gap",
        "SN002": "Witnessed integer norm separation", "SN003": "Signed quadratic norm multiplicativity",
        "CV001": "Universal natural convolution vanishing", "RN001": "Rational norm representative independence",
        "RN002": "Rational quadratic norm multiplication", "SI001": "Nonzero signed-integer products",
        "QN001": "Nonzero quadratic-integer products", "QF001": "Nonvanishing finite quadratic product traces"}[case]


def parent(case):
    return "IR001" if case.startswith("RF") else "IR079" if case.startswith("P04") else {
        "P10": "IR064", "P08-eprover": "IR055", "P08-vampire": "IR055", "IR016": "IR016",
        "SN001": "IR032", "NG001": "IR003", "SN002": "IR032", "SN003": "IR031", "CV001": "IR079",
        "RN001": "IR031", "RN002": "IR031", "SI001": "IR046", "QN001": "IR046", "QF001": "IR046"}[case]


def definition_graph():
    positions = {"IRatValid": (320, 25), "IRatEq": (320, 110), "IRatLt": (590, 110),
                 "IRatAdd": (80, 210), "IRatMul": (320, 210), "IRatNeg": (560, 210)}
    edges, nodes = [], []
    for name, definition in DEFINITIONS.items():
        x, y = positions[name]
        for dependency in definition.conceptual_dependencies:
            sx, sy = positions[dependency]
            edges.append(f'<path d="M {sx+85} {sy+48} L {x+85} {y}" class="definition-edge"/>')
        nodes.append(f'<a href="#{definition.stable_id}"><g class="definition-node" id="graph-{definition.stable_id}"><rect x="{x}" y="{y}" width="170" height="48" rx="8"/><text x="{x+85}" y="{y+20}" text-anchor="middle">{definition.stable_id}</text><text x="{x+85}" y="{y+37}" text-anchor="middle">{name}</text></g></a>')
    return '<div class="local-definition-graph"><svg viewBox="0 0 850 290" role="img" aria-label="Six local conservative rational definitions and their expansion dependencies">'+''.join(edges+nodes)+'</svg></div>'


def build_wave_files(revision, page, index_path, expected_hash):
    raw = index_path.read_bytes()
    if sha256(raw).hexdigest() != expected_hash:
        raise ValueError("pinned wave index changed")
    view, files = wave_results(json.loads(raw))
    files["api/wave-results.json"] = encoded(view)
    files["api/wave-index.json"] = raw
    definitions = definition_manifest()
    files["api/local-rational-definitions.json"] = encoded(definitions)
    successful = [r for r in view["rows"] if r["status"] == "fresh_ordinary_HA_checked"]
    by_case = {r["case"]: r for r in successful}
    definitions["theorem_uses"] = [dict(definition=DEFINITIONS[name].stable_id, theorem=case, kind="theorem_uses_definition")
        for case,name in (("RN001","IRatEq"),("RN002","IRatMul")) if case in by_case]
    files["api/local-rational-definitions.json"] = encoded(definitions)
    if "SN001" in by_case:
        signed_users = tuple(case for case in ("SN001", "SN002", "SN003", "RN001", "RN002") if case in by_case)
        files.update(signed_norm_files(by_case["SN001"], page, revision, users=signed_users))
    if set(by_case) & {"NG001", "SN002", "SN003", "CV001", "RN001", "RN002", "SI001", "QN001", "QF001"}:
        from sqrt2_power_arithmetic_page import build_arithmetic_files
        files.update(build_arithmetic_files(by_case, files, page, revision, evidence_section))
    foundation_sections = []
    for identifier, name, named_source, used_definitions, _ in FOUNDATIONS:
        row = by_case.get(identifier)
        if row and formula_sha256(foundation_target(name)) != row["target_ast_sha256"]:
            raise ValueError("named foundation differs from the recorded expanded formula")
        if row:
            notation = escape(named_source)
            for definition in used_definitions:
                notation = notation.replace(definition+"(",
                    f'<a href="../local-definitions.html#{DEFINITIONS[definition].stable_id}">{definition}</a>(')
            foundation_sections.append(f'<li><a href="checked/{identifier}.html">{identifier} — {escape(label(identifier))}</a></li>')
            body = f'<section class="release-note"><h2>Named statement</h2><pre class="contract"><code>{notation}</code></pre><p>Every named predicate expands conservatively to the existing HA syntax. These definitions contain no accuracy promises or theorem assumptions.</p></section>'
            body += evidence_section(row, prefix="../")
            body += f'<section class="release-note"><p><a href="../wave-results.html">Current checked leaves</a> · <a href="../map.html?target={parent(identifier)}&amp;view=prerequisites">Larger planning cone</a> · <a href="../local-definitions.html">Local definition DAG</a>.</p><p>This is local exact-certificate evidence, not an Alpha/Stable admission or a completed irrationality proof.</p></section>'
            files[f"checked/{identifier}.html"] = page(identifier+" — "+label(identifier), body, revision, depth=1,
                eyebrow="Local named theorem · HA and independent Lean evidence")
    for row in definitions["nodes"]:
        dependencies = " · ".join(f'<a href="#{DEFINITIONS[n].stable_id}">{escape(n)}</a>' for n in row["dependencies"]) or "No definition prerequisite"
        foundation_sections.append(f'<section class="release-note" id="{row["id"]}"><h2>{row["id"]} — {row["name"]}</h2><p>Parameters: {escape(", ".join(row["parameters"]))}. {dependencies}.</p><details><summary>Exact expanded HA definition</summary><pre class="contract"><code>{escape(row["source"])}</code></pre></details></section>')
    intro = '<section class="release-note"><h2>Conservative local notation</h2><p>Six capture-safe rational templates, with explicit nonzero denominators. No new kernel symbol or axiom; no global registry change. These are local expansions, not Alpha/Stable admissions. Arrows below are definition-expansion dependencies, not theorem proofs.</p>'+definition_graph()+'</section>'
    if "SN001" in by_case:
        intro += '<section class="release-note"><h2>Reused signed-square notation</h2><p>The signed norm bridge reuses the existing <a href="reused-definitions/ND0157.html">ND0157 — SignedDifferenceSquare</a>, with the same reviewed expansion and identity. It is not a seventh new rational definition. <a href="checked/SN001.html">Open the checked signed quadratic-norm zero criterion</a>.</p></section>'
    if "SN003" in by_case:
        intro += '<section class="release-note"><h2>Quadratic-integer components</h2><p><a href="quadratic-definitions.html#ND0388">ND0388 — IQuadProductReal</a> and <a href="quadratic-definitions.html#ND0389">ND0389 — IQuadProductRadical</a> are two separate primitive balance equations, without hidden norm claims. <a href="checked/SN003.html">The checked multiplicativity theorem</a> uses both and the exact ND0157 square definition. These two aliases are local and unpromoted.</p></section>'
    if "CV001" in by_case:
        intro += '<section class="release-note"><h2>Finite convolution</h2><p><a href="convolution-definitions.html">Eight historical table, order, and summation definitions</a> are reused with the same identities and argument order. <a href="checked/CV001.html">CV001</a> proves a universal vanishing statement for the actual natural diagonal execution, not a rational exp-composition theorem.</p></section>'
    if "RN001" in by_case and "RN002" in by_case:
        intro += '<section class="release-note"><h2>Rational quadratic norms</h2><p><a href="checked/RN001.html">RN001: norm independence from representatives and denominators</a> and <a href="checked/RN002.html">RN002: denominator-aware norm multiplication</a> reuse IRatEq, IRatMul and the existing signed-square and coordinate definitions without adding a new alias or axiom. Real interpretation and analytic separation remain open.</p></section>'
    if "QN001" in by_case:
        intro += '<section class="release-note"><h2>Nonzero quadratic products</h2><p><a href="checked/QN001.html">QN001: products of two nonzero signed quadratic integers are nonzero</a> uses the actual norm and signed-integer proof bodies, with no canonical-representative restriction.</p>'
        if "QF001" in by_case:
            intro += '<p><a href="checked/QF001.html">QF001: finite product traces preserve nonvanishing</a> adds genuine induction over decoded tables. <a href="quadratic-trace-definitions.html">Four conservative trace definitions</a> keep executed multiplication separate from the nonzero-factor assumption. Existence of traces and interpretation in the real numbers remain open.</p>'
        intro += '</section>'
    if "arithmetic-frontier.html" in files:
        intro += '<section class="release-note"><p><a href="arithmetic-frontier.html">Navigate the checked arithmetic DAG and its open planning parents</a>. Proof dependencies and definition-use links are kept distinct.</p></section>'
    # The first six entries are theorem links; keep them in a proper list.
    links = ''.join(s for s in foundation_sections if s.startswith('<li>'))
    sections = ''.join(s for s in foundation_sections if not s.startswith('<li>'))
    files["local-definitions.html"] = page("Local rational definitions and their uses", intro+
        '<section class="release-note"><h2>Theorems using this notation</h2><ul>'+links+'</ul><p><a href="wave-results.html">Checked results</a> · <a href="map.html?target=IR001&amp;view=prerequisites">IR001 planning cone</a> · <a href="api/local-rational-definitions.json">Exact definition DAG data</a>.</p></section>'+sections,
        revision, eyebrow="Conservative expansion DAG · Local, unpromoted")
    rows = []
    for i, row in enumerate(view["rows"]):
        checked = row["status"] == "fresh_ordinary_HA_checked"
        badge = "HA + freshly compiled Lean" if row["independent_lean_checked"] else "HA only" if checked else "Open / attempt failed"
        download = f'<a href="{row["proof_download"]}" download>Exact certificate</a>' if checked else "No accepted certificate"
        rows.append(f'<tr id="attempt-{i}"><th>{escape(row["case"])}</th><td>{escape(label(row["case"]))}</td><td>{badge}</td><td>{download}<br><a href="{row["report_download"]}" download>Full run record</a></td><td><a href="map.html?target={parent(row["case"])}&amp;view=prerequisites">{parent(row["case"])}</a></td></tr>')
    chunks = [r for r in successful if re.fullmatch(r"P04-C[0-9]{2}", r["case"])]
    counts = view["counts"]
    content = f'<section class="release-note"><h2>Irrationality remains open</h2><p>The endpoint IR072 is not proved. These are exact local subproofs, with solver hints, native HA checking and independent Lean checking kept separate. No campaign parent admission, Alpha promotion or deployment is claimed.</p><p>{counts["unique_HA_statements"]} distinct checked statements in this wave; duplicate E/V demonstrations are counted once. Six are named rational foundations. Trace pieces are finite instances, not variable-degree theorems.</p><p><a href="local-definitions.html">Explore the local definition DAG</a> · <a href="pilot-results.html">Original pilot baseline and its historical failures</a>.</p></section>'
    content += '<section class="release-note"><h2>What changed</h2><p>P10 now has a shared, 1,486-node HA proof DAG and an independent Lean check. E and Vampire each selected two original premises for the narrow P08 native reconstruction; this is premise-guided reconstruction, not a TSTP proof translator. Z3 separately checked the six rational conjectures, without supplying trusted axioms.</p>'
    content += f'<p>The composition trace has {len(chunks)}/16 exact pieces HA-checked. Its complete assembly remains open; the separate universal constant-coefficient soundness lemma does not replace the missing execution pieces. Size-limited attempts remain visible below.</p></section>'
    if "IR016" in by_case:
        content += '<section class="release-note"><h2>A critical reuse: the twice-square lemma</h2><p>For natural A,B, A²=2B² implies A=B=0. The proof reduces to the existing Fermat fourth-power theorem and rechecks its complete dependency cone. This is a prerequisite for quadratic norm separation, not irrationality of (√2)^(√2).</p>'+evidence_section(by_case["IR016"])+ '</section>'
    if "SN001" in by_case:
        content += '<section class="release-note"><h2>From natural squares to signed coefficients</h2><p>SN001 proves that (ap−an)²=2(bp−bn)² forces ap=an and bp=bn, with explicit natural square witnesses and no normalization assumption on the signed pairs. It reuses the exact existing SignedDifferenceSquare definition and the checked IR016 dependency cone.</p><p><a href="checked/SN001.html">Named theorem, original formula and exact proof</a> · <a href="reused-definitions/ND0157.html">Reused definition ND0157</a>. The rational/real quantitative lower bound and quadratic interpretation in IR032 remain open.</p></section>'
    additions = [case for case in ("NG001", "SN002", "SN003", "CV001") if case in by_case]
    if additions:
        content += '<section class="release-note"><h2>New universal arithmetic lemmas</h2><ul>'+''.join('<li><a href="checked/'+case+'.html">'+case+' — '+escape(label(case))+'</a></li>' for case in additions)+'</ul><p>The integer separation witness is distinct from the still-open rational/real lower bound. The convolution result concerns actual natural coefficient tables, not completed rational exp composition. Z3 separately checked the natural-gap conjecture; deterministic HA generation and fresh Lean checks provide the proof evidence.</p><p><a href="arithmetic-frontier.html">Actual proof DAG and open planning parents</a> · <a href="local-definitions.html">Exact definitions and theorem uses</a>.</p></section>'
    content += '<section class="release-note"><h2>Exact execution evidence</h2><div class="pilot-results-scroll"><table class="pilot-results-table"><thead><tr><th>Case</th><th>Statement / scope</th><th>Checking</th><th>Reproducible bytes</th><th>Planning parent</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table></div></section>'
    content += '<section class="release-note"><h2>Next mathematical bottlenecks</h2><p>Variable-degree formal composition and its recurrence; quantitative log–exp composition tails; confluent interpolation; and the positive precision-to-certificate bridge. A finite trace or a solver hit cannot close these.</p><p>Workers use one process at a time and fixed resource caps. They make no model calls; agents wrote/reviewed the specifications and generators, and that engineering cost is not measured as zero.</p><p><a href="api/wave-results.json">Machine-readable observations</a> · <a href="map.html?target=IR072&amp;view=prerequisites">Full planned dependency cone</a>.</p></section>'
    files["wave-results.html"] = page("Solver-backed proof campaign — current evidence", content, revision,
        eyebrow="Checked local leaves · Full irrationality still open")
    return files


def evidence_section(row, prefix=""):
    badge = "Fresh HA and independently compiled Lean checks" if row["independent_lean_checked"] else "Fresh HA check; independent Lean not recorded"
    return f'<section class="release-note"><h2>{badge}</h2><p><a href="{prefix+row["proof_download"]}" download>Download the exact canonical proof bundle (gzip)</a> · <a href="{prefix+row["report_download"]}" download>Original run record</a>.</p><p>{row["local_nodes"]:,} local nodes; {row["proof_nodes"]:,} ordinary proof-body nodes. No receipt is substituted for a proof body.</p><p class="contract">Target AST SHA-256: {row["target_ast_sha256"]}<br>Certificate SHA-256: {row["bundle_sha256"]}</p></section>'


def signed_norm_files(row, page, revision, *, users=("SN001",)):
    from sqrt2_power_definitions import parse_named, PARENT_SHA256
    from sqrt2_power_signed_norm import (
        SIGNED_NORM_SOURCE, frozen_signed_norm_target, signed_difference_definition,
    )
    from peano_lab.library.proof_bundle import encode_formula

    definition = signed_difference_definition()
    if not users or len(users) != len(set(users)) or not set(users) <= {"SN001", "SN002", "SN003", "RN001", "RN002"}:
        raise ValueError("unknown or duplicate signed-definition theorem use")
    named = (r"forall ap an bp bn s t. SignedDifferenceSquare(ap,an,s) -> "
        r"SignedDifferenceSquare(bp,bn,t) -> s=(S(S 0))*t -> (ap=an /\ bp=bn)")
    target = parse_named(named, registry={definition.name: definition})
    if target != frozen_signed_norm_target() or formula_sha256(target) != row["target_ast_sha256"]:
        raise ValueError("named signed norm bridge differs from the checked exact formula")
    notation = escape(named).replace("SignedDifferenceSquare(",
        '<a href="../reused-definitions/ND0157.html">SignedDifferenceSquare</a>(')
    body = '<section class="release-note"><h2>Named statement</h2><pre class="contract"><code>'+notation+'</code></pre><p>The square witnesses s,t are natural numbers. The coefficient pairs ap,an and bp,bn may be arbitrary, including negative and nonnormalized integer representatives. No real-number sort or new axiom is introduced.</p><details><summary>Exact original expanded HA target</summary><pre class="contract"><code>'+escape(SIGNED_NORM_SOURCE)+'</code></pre></details></section>'
    body += evidence_section(row, prefix="../")
    body += '<section class="release-note"><h2>Checked reuse and remaining scope</h2><p>The certificate includes the natural twice-square proof, together with the actual absolute-difference existence, absolute-square balance and signed-square functionality proof bodies. Their complete ancestor cones are checked again; historical receipts are not imported as axioms.</p><p>This proves the signed zero-norm criterion only. The rational/real quantitative lower bound, rational-denominator interpretation and the full irrationality argument remain open.</p><p><a href="../local-definitions.html">Definition network</a> · <a href="../map.html?target=IR032&amp;view=prerequisites">Larger IR032 planning cone</a> · <a href="../wave-results.html">All current evidence</a>.</p></section>'
    definition_data = dict(id=definition.stable_id, name=definition.name,
        parameters=list(definition.parameters), source=definition.template_source,
        ast=encode_formula(definition.template_formula), historical_parent_sha256=PARENT_SHA256,
        authority="same_existing_definition_reused_not_new_admission", used_by=list(users))
    theorem_links = ' · '.join('<a href="../checked/'+case+'.html">'+case+'</a>' for case in users)
    definition_body = '<section class="release-note"><h2>Existing conservative definition, reused unchanged</h2><p>Parameters: '+escape(', '.join(definition.parameters))+'. This is the existing ND0157 identity, not a duplicate registration.</p><pre class="contract"><code>'+escape(definition.template_source)+'</code></pre><p>The equality says that s is the natural square of the integer represented by p−n. It contains no irrationality or norm-separation claim.</p><p>Checked theorem uses: '+theorem_links+'.</p><p><a href="../local-definitions.html">Local definition network</a> · <a href="../api/reused-signed-square-definition.json">Exact expansion data</a>.</p></section>'
    return {
        "checked/SN001.html": page("SN001 — Signed quadratic-norm zero criterion", body, revision, depth=1,
            eyebrow="Universal signed-pair lemma · Local exact evidence"),
        "reused-definitions/ND0157.html": page("ND0157 — SignedDifferenceSquare", definition_body, revision, depth=1,
            eyebrow="Reused existing definition · No registry mutation"),
        "api/reused-signed-square-definition.json": encoded(definition_data),
    }
