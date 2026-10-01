"""Exact checked arithmetic leaves, conservative notation, and actual root edges.

This renderer never executes a proof producer. Displayed proof edges are read
from the accepted canonical bundles, not inferred from mathematical similarity.
Planning-parent links remain explicitly unproved support relations.
"""
from hashlib import sha256
from html import escape
import gzip
import json

from sqrt2_power_binary_dag import formula_sha256
from sqrt2_power_definitions import DEFINITIONS, parse_named
from sqrt2_power_signed_norm import signed_difference_definition
from sqrt2_power_quadratic_definitions import QUADRATIC_DEFINITIONS, quadratic_definition_manifest


def encoded(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False).encode()+b"\n"


def convolution_definition_graph(registry):
    positions = {"Le": (25, 10), "Lt": (385, 10), "BetaAt": (745, 10),
        "BetaZeroExtend": (385, 130), "Sum": (25, 250), "Repeat": (745, 250),
        "PolynomialDiagonalTerm": (385, 250), "PolynomialDiagonalPrefix": (385, 370)}
    if set(registry) != set(positions):
        raise ValueError("convolution definition layout differs from its exact inventory")
    svg = '<svg viewBox="0 0 1000 460" role="img" aria-label="Eight reused convolution definitions and their exact expansion dependencies">'
    for name, definition in registry.items():
        x, y = positions[name]
        for dependency in definition.conceptual_dependencies:
            sx, sy = positions[dependency]
            if name in {"Sum", "Repeat"}:
                lane_y = 86 if dependency == "Lt" else 98
                path = f"M {sx+115} {sy+56} V {lane_y} H {x+115} V {y}"
            elif name == "PolynomialDiagonalPrefix" and dependency in {"Lt", "BetaAt"}:
                lane_x = 290 if dependency == "Lt" else 710
                end_x = x if dependency == "Lt" else x+230
                path = f"M {sx+115} {sy+56} V 110 H {lane_x} V {y+28} H {end_x}"
            else:
                path = f"M {sx+115} {sy+56} L {x+115} {y}"
            svg += '<path class="definition-edge" d="'+path+'"><title>'+escape(dependency+' is used by '+name)+'</title></path>'
    for name, definition in registry.items():
        x, y = positions[name]
        svg += f'<a href="#{definition.stable_id}"><g class="definition-node" id="convolution-graph-{definition.stable_id}"><rect x="{x}" y="{y}" width="230" height="56" rx="8"/><text x="{x+115}" y="{y+22}" text-anchor="middle">{definition.stable_id}</text><text x="{x+115}" y="{y+41}" text-anchor="middle">{name}</text></g></a>'
    return '<div class="local-definition-graph">'+svg+'</svg></div>'


def arithmetic_contracts(cases):
    """Named source and frozen proof source meet only by exact AST equality."""
    square = signed_difference_definition()
    registry = {square.name: square, **QUADRATIC_DEFINITIONS, **DEFINITIONS}
    result = {}
    if "NG001" in cases:
        from sqrt2_power_norm_separation import NATURAL_GAP_SOURCE, frozen_natural_gap_target
        result["NG001"] = dict(title="Constructive natural strict gap", parent="IR003",
            named=NATURAL_GAP_SOURCE, source=NATURAL_GAP_SOURCE, target=frozen_natural_gap_target(), uses=[],
            explanation="Unequal natural numbers have a positive additive gap, witnessed in one of the two directions. The proof uses the actual trichotomy body and checked addition commutativity. Z3 is an independent conjecture check, not the source of HA authority.")
    if "SN002" in cases:
        from sqrt2_power_norm_separation import NORM_SEPARATION_SOURCE, frozen_norm_separation_target
        result["SN002"] = dict(title="Witnessed integer norm separation", parent="IR032",
            named=(r"forall ap an bp bn s t. SignedDifferenceSquare(ap,an,s) -> "
                   r"SignedDifferenceSquare(bp,bn,t) -> ~(ap=an /\ bp=bn) -> "
                   r"exists k. (s+S k=(S(S 0))*t \/ (S(S 0))*t+S k=s)"),
            source=NORM_SEPARATION_SOURCE, target=frozen_norm_separation_target(), uses=[square.name],
            explanation="For a nonzero signed coefficient pair, the two natural norm contributions differ by a witnessed positive integer. The complete SN001 and NG001 proofs are included. This is the integer gap, not yet the rational-denominator or real-algebraic lower bound required by IR032.")
    if "SN003" in cases:
        from sqrt2_power_quadratic_norm_product import QUADRATIC_NORM_PRODUCT_SOURCE, frozen_quadratic_norm_product_target
        result["SN003"] = dict(title="Signed quadratic norm multiplicativity", parent="IR031",
            named=("forall ap an bp bn cp cn dp dn rp rn sp sn a b c d r t. "
                   "SignedDifferenceSquare(ap,an,a) -> SignedDifferenceSquare(bp,bn,b) -> "
                   "SignedDifferenceSquare(cp,cn,c) -> SignedDifferenceSquare(dp,dn,d) -> "
                   "SignedDifferenceSquare(rp,rn,r) -> SignedDifferenceSquare(sp,sn,t) -> "
                   "IQuadProductReal(ap,an,bp,bn,cp,cn,dp,dn,rp,rn) -> "
                   "IQuadProductRadical(ap,an,bp,bn,cp,cn,dp,dn,sp,sn) -> "
                   "r+2*(a*d+b*c)=(a*c+(2*2)*(b*d))+2*t"),
            source=QUADRATIC_NORM_PRODUCT_SOURCE, target=frozen_quadratic_norm_product_target(),
            uses=[square.name, *QUADRATIC_DEFINITIONS],
            explanation="This proves N(xy)=N(x)N(y) in Z[√2], including transport to arbitrary signed output representatives. It rechecks actual signed-square product, scaling, sum, and cross-interchange proof bodies. Three small deterministic ring helpers replace normalization of the entire eighteen-variable formula. No rational denominator or real-number interpretation is claimed.")
    if "CV001" in cases:
        from sqrt2_power_convolution_vanishing import (CONVOLUTION_VANISHING_NAMED_SOURCE,
            frozen_convolution_vanishing_target, convolution_definitions)
        from peano_lab.kernel.formulas import pretty_formula
        reused = convolution_definitions()
        registry.update(reused)
        target = frozen_convolution_vanishing_target()
        result["CV001"] = dict(title="Universal convolution vanishing", parent="IR079",
            named=CONVOLUTION_VANISHING_NAMED_SOURCE, source=pretty_formula(target, []), target=target,
            uses=[name for name in reused if name+"(" in CONVOLUTION_VANISHING_NAMED_SOURCE],
            explanation="If two natural coefficient tables vanish below indices r and s, an actually executed antidiagonal convolution below r+s sums to zero. The table, diagonal, and summation witnesses are explicit. This is not yet an ascending rational-series power theorem, formal exp composition, or an analytic tail estimate.")
    if "RN001" in cases:
        from sqrt2_power_rational_norm_transport import (RATIONAL_NORM_TRANSPORT_NAMED_SOURCE,
            RATIONAL_NORM_TRANSPORT_SOURCE, frozen_rational_norm_transport_target)
        result["RN001"] = dict(title="Rational norm representative independence", parent="IR031",
            named=RATIONAL_NORM_TRANSPORT_NAMED_SOURCE, source=RATIONAL_NORM_TRANSPORT_SOURCE,
            target=frozen_rational_norm_transport_target(), uses=["IRatEq", square.name],
            explanation="Equivalent rational quadratic coordinate pairs give equivalent rational norms, including negative norms and overlapping signed representatives. The two IRatEq premises explicitly include nonzero denominators; their squares are proved nonzero. Actual signed-square scaling, transport and uniqueness proofs supply the result. No new definition, rational quotient object or real-number interpretation is assumed.")
    if "RN002" in cases:
        from sqrt2_power_rational_norm_product import NAMED_SOURCE, frozen_rational_norm_product_target
        from peano_lab.kernel.formulas import pretty_formula
        target = frozen_rational_norm_product_target()
        result["RN002"] = dict(title="Rational quadratic norm multiplication", parent="IR031",
            named=NAMED_SOURCE, source=pretty_formula(target, []), target=target,
            uses=[square.name, *QUADRATIC_DEFINITIONS, "IRatMul"],
            explanation="The exact signed integer norm identity now yields the existing rational multiplication relation. Both input denominators are explicitly nonzero; the output denominator is (uv)², not uv. Arbitrary signed output coordinate representatives are allowed. This does not identify the represented element with a real number or prove the full IR031 norm/conjugate statement.")
    if "SI001" in cases:
        from sqrt2_power_signed_product_nonzero import SIGNED_PRODUCT_NONZERO_SOURCE, frozen_signed_product_nonzero_target
        result["SI001"] = dict(title="Nonzero signed-integer products", parent="IR046",
            named=SIGNED_PRODUCT_NONZERO_SOURCE, source=SIGNED_PRODUCT_NONZERO_SOURCE,
            target=frozen_signed_product_nonzero_target(), uses=[],
            explanation="Two nonzero signed integers have a nonzero product, even with overlapping, noncanonical input and output pairs. The output balance is explicit. Actual square-existence, square-product, square-zero and natural no-zero-divisor proof bodies supply the constructive argument. This is a binary integer lemma, not quadratic-field or finite-product closure.")
    if "QN001" in cases:
        from sqrt2_power_quadratic_nonzero import NAMED_SOURCE, frozen_quadratic_nonzero_target
        from peano_lab.kernel.formulas import pretty_formula
        target = frozen_quadratic_nonzero_target()
        result["QN001"] = dict(title="Nonzero quadratic-integer products", parent="IR046",
            named=NAMED_SOURCE, source=pretty_formula(target, []), target=target,
            uses=list(QUADRATIC_DEFINITIONS),
            explanation="The product of two nonzero elements of Z[√2] is nonzero, with all four signed input pairs and both output pairs arbitrary. Both component equations are explicit premises. Complete SN001, SN003 and SI001 proof bodies are shared and rechecked; metadata is never a theorem premise. This is a binary algebraic statement, not yet finite trace existence or real-number interpretation.")
    if "QF001" in cases:
        from sqrt2_power_quadratic_product_trace import (NAMED_SOURCE,
            frozen_quadratic_product_trace_target, definition_registry)
        from peano_lab.kernel.formulas import pretty_formula
        registry.update(definition_registry())
        target = frozen_quadratic_product_trace_target()
        result["QF001"] = dict(title="Nonvanishing finite quadratic product traces", parent="IR046",
            named=NAMED_SOURCE, source=pretty_formula(target, []), target=target,
            uses=["IQuadProductTrace", "IQuadNonzeroFactors", "IQuadAt"],
            explanation="For every finite length, a supplied β-table product trace beginning at one has a nonzero terminal value if every decoded factor is nonzero. Each executed step supplies actual factor, predecessor and successor coordinates and both multiplication equations. Induction, exact β-decoding uniqueness and QN001 prove the claim. The execution definition contains no nonvanishing conclusion. Trace existence, rational denominators and real interpretation remain separate open obligations.")
    for case, row in result.items():
        if parse_named(row["named"], registry=registry) != row["target"]:
            raise ValueError("named arithmetic target differs from exact frozen formula: "+case)
    return result, registry


def build_arithmetic_files(by_case, downloads, page, revision, evidence_section):
    contracts, registry = arithmetic_contracts(by_case)
    files = {}
    def definition_href(name, prefix="../"):
        if name == "SignedDifferenceSquare":
            return prefix+"reused-definitions/ND0157.html"
        if name in DEFINITIONS:
            return prefix+"local-definitions.html#"+DEFINITIONS[name].stable_id
        if registry[name].stable_id in {"ND0390", "ND0391", "ND0392", "ND0393"}:
            return prefix+"quadratic-trace-definitions.html#"+registry[name].stable_id
        return prefix+("quadratic-definitions.html" if name in QUADRATIC_DEFINITIONS else "convolution-definitions.html")+"#"+registry[name].stable_id
    for case, contract in contracts.items():
        row = by_case[case]
        if formula_sha256(contract["target"]) != row["target_ast_sha256"]:
            raise ValueError("arithmetic page evidence targets another statement: "+case)
        displayed = contract["named"].replace(". ", ".\n  ", 1).replace(" -> ", " ->\n  ")
        if parse_named(displayed, registry=registry) != contract["target"]:
            raise ValueError("display whitespace changed a named arithmetic formula")
        notation = escape(displayed)
        for name in contract["uses"]:
            notation = notation.replace(name+"(", '<a href="'+definition_href(name)+'">'+name+'</a>(')
        body = '<section class="release-note"><h2>Named statement</h2><pre class="contract"><code>'+notation+'</code></pre><p>'+escape(contract["explanation"])+'</p><details><summary>Exact original expanded HA target</summary><pre class="contract"><code>'+escape(contract["source"])+'</code></pre></details></section>'
        body += evidence_section(row, prefix="../")
        body += '<section class="release-note"><p><a href="../arithmetic-frontier.html">Checked arithmetic DAG</a> · <a href="../local-definitions.html">Definition network</a> · <a href="../map.html?target='+contract["parent"]+'&amp;view=prerequisites">Larger '+contract["parent"]+' planning cone</a> · <a href="../wave-results.html">All current evidence</a>.</p><p>IR072 remains open. This local exact certificate is not an Alpha/Stable admission or a completed irrationality proof.</p></section>'
        files[f"checked/{case}.html"] = page(case+" — "+contract["title"], body, revision, depth=1,
            eyebrow="Universal arithmetic lemma · Local exact evidence")
    if "SN003" in contracts:
        data = quadratic_definition_manifest()
        data["theorem_uses"] = [dict(definition=registry[name].stable_id, theorem=case, kind="theorem_uses_definition")
                                for case, contract in contracts.items() for name in contract["uses"]
                                if name in {"SignedDifferenceSquare", *QUADRATIC_DEFINITIONS}]
        files["api/local-quadratic-definitions.json"] = encoded(data)
        body = '<section class="release-note"><h2>Two separate component equations</h2><p>These local conservative aliases abbreviate the real and radical coordinate balances in Z[√2]. They do not assert multiplication totality or norm multiplicativity. Each is a primitive equation, with no definition prerequisite and no global registry mutation. Six existing rational aliases and ND0157 are unchanged.</p><p>The separate relations preserve the exact two implication premises of the checked theorem; they are not silently replaced by a single conjunction premise.</p></section>'
        for definition in QUADRATIC_DEFINITIONS.values():
            users = ' · '.join('<a href="checked/'+case+'.html">'+case+'</a>' for case, contract in contracts.items() if definition.name in contract["uses"])
            body += '<section class="release-note" id="'+definition.stable_id+'"><h2>'+definition.stable_id+' — '+definition.name+'</h2><p>'+escape(definition.summary)+'</p><p>Parameters: '+escape(', '.join(definition.parameters))+'.</p><pre class="contract"><code>'+escape(definition.template_source)+'</code></pre><p>Checked theorems using this exact expansion: '+users+'.</p></section>'
        body += '<section class="release-note"><p><a href="local-definitions.html">Full local definition network</a> · <a href="arithmetic-frontier.html">Checked arithmetic DAG</a> · <a href="api/local-quadratic-definitions.json">Exact definitions and typed uses</a>.</p></section>'
        files["quadratic-definitions.html"] = page("Quadratic-integer component definitions", body, revision,
            eyebrow="Conservative local notation · No new kernel symbols")
    if "CV001" in contracts:
        from sqrt2_power_convolution_vanishing import convolution_definitions
        from peano_lab.library.proof_bundle import encode_formula
        reused = convolution_definitions()
        if any(name not in reused for d in reused.values() for name in d.conceptual_dependencies):
            raise ValueError("reused convolution definition DAG has an omitted prerequisite")
        data = dict(authority="same_existing_definitions_reused_not_new_admission",
            nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters), source=d.template_source,
                        ast=encode_formula(d.template_formula)) for d in reused.values()],
            edges=[dict(source=reused[name].stable_id, target=d.stable_id, kind="definition_uses_definition")
                   for d in reused.values() for name in d.conceptual_dependencies if name in reused],
            theorem_uses=[dict(definition=registry[name].stable_id, theorem="CV001", kind="theorem_uses_definition")
                          for name in contracts["CV001"]["uses"]])
        files["api/reused-convolution-definitions.json"] = encoded(data)
        body = '<section class="release-note"><h2>Actual finite-table definitions, reused unchanged</h2><p>CV001 uses the existing natural table, zero-extension, diagonal, repeat and sum relations. No real functions or rational-series ordering are supplied by these definitions. Their exact reviewed identities and argument order are preserved.</p><p><a href="checked/CV001.html">Universal checked convolution lemma</a> · <a href="local-definitions.html">Definition network</a> · <a href="api/reused-convolution-definitions.json">Exact expansion DAG data</a>.</p></section>'
        body += '<section class="release-note"><h2>Conservative expansion DAG</h2><p>Edges run from a prerequisite definition to a definition using it. They are notation dependencies, not theorem proofs. Click any node to inspect its exact parameters and expansion.</p>'+convolution_definition_graph(reused)+'</section>'
        for definition in reused.values():
            dependencies = ' · '.join('<a href="#'+reused[name].stable_id+'">'+escape(name)+'</a>'
                                     for name in definition.conceptual_dependencies) or 'No definition prerequisite'
            body += '<section class="release-note" id="'+definition.stable_id+'"><h2>'+definition.stable_id+' — '+definition.name+'</h2><p>Parameters: '+escape(', '.join(definition.parameters))+'. '+dependencies+'.</p><details><summary>Exact expanded HA definition</summary><pre class="contract"><code>'+escape(definition.template_source)+'</code></pre></details></section>'
        files["convolution-definitions.html"] = page("Reused convolution definition DAG", body, revision,
            eyebrow="Exact historical identities · No duplicate registrations")
    if "QF001" in contracts:
        files.update(trace_definition_files(contracts["QF001"], page, revision))
    if contracts:
        files.update(frontier_files(by_case, contracts, downloads, page, revision))
    return files


def trace_definition_files(contract, page, revision):
    from sqrt2_power_quadratic_product_trace import definition_registry, trace_definitions, DEFINITION_ROWS
    from peano_lab.library.proof_bundle import encode_formula
    registry, local = definition_registry(), trace_definitions()
    named_sources = {row[1]: row[3] for row in DEFINITION_ROWS}
    for name, source in named_sources.items():
        if parse_named(source, registry[name].parameters, registry=registry) != registry[name].template_formula:
            raise ValueError("displayed trace definition differs from its exact expansion")
    selected = set(local)
    pending = list(selected)
    while pending:
        for name in registry[pending.pop()].conceptual_dependencies:
            if name not in selected:
                selected.add(name)
                pending.append(name)
    ordered = {name: d for name, d in registry.items() if name in selected}
    data = dict(authority="local_conservative_templates_not_Alpha_admissions",
        nodes=[dict(id=d.stable_id, name=d.name, parameters=list(d.parameters), source=d.template_source,
                    named_source=named_sources.get(name, d.template_source),
                    ast=encode_formula(d.template_formula), new_local=name in local)
               for name, d in ordered.items()],
        edges=[dict(source=registry[name].stable_id, target=d.stable_id, kind="definition_uses_definition")
               for d in ordered.values() for name in d.conceptual_dependencies],
        theorem_uses=[dict(definition=registry[name].stable_id, theorem="QF001", kind="theorem_uses_definition")
                      for name in contract["uses"]])
    # Every edge below is an actual conservative-expansion dependency, not
    # a guessed mathematical prerequisite or theorem-proof edge.
    positions = {"BetaAt": (30, 25), "IQuadAt": (30, 165),
                 "IQuadProductReal": (315, 25), "IQuadProductRadical": (600, 25),
                 "IQuadProductStep": (315, 310), "Lt": (885, 25),
                 "IQuadProductTrace": (315, 470), "IQuadNonzeroFactors": (885, 470)}
    if set(ordered) != set(positions):
        raise ValueError("trace definition layout differs from exact dependency inventory")
    svg = '<svg viewBox="0 0 1165 565" role="img" aria-label="Conservative quadratic product trace definition DAG">'
    for d in ordered.values():
        x, y = positions[d.name]
        for parent in d.conceptual_dependencies:
            sx, sy = positions[parent]
            path = f"M {sx+125} {sy+60} L {x+125} {y}"
            if parent == "IQuadAt" and d.name == "IQuadProductTrace":
                path = f"M {sx+125} {sy+60} V 445 H {x+125} V {y}"
            elif parent == "IQuadAt" and d.name == "IQuadNonzeroFactors":
                path = f"M {sx+250} {sy+30} H 1160 V 435 H {x+125} V {y}"
            svg += '<path class="definition-edge" d="'+path+'"><title>'+escape(parent+' is used by '+d.name)+'</title></path>'
    for name, d in ordered.items():
        x, y = positions[name]
        svg += f'<a href="#{d.stable_id}"><g class="definition-node" id="trace-graph-{d.stable_id}"><rect x="{x}" y="{y}" width="250" height="60" rx="8"/><text x="{x+125}" y="{y+23}" text-anchor="middle">{d.stable_id}</text><text x="{x+125}" y="{y+44}" text-anchor="middle">{escape(name)}</text></g></a>'
    body = '<section class="release-note"><h2>Execution and mathematical hypotheses stay separate</h2><p>Four new local aliases describe decoded coordinates, actual multiplication steps, a trace starting at one, and its separate nonzero-factor hypothesis. The trace does not assume that its outputs are nonzero. Every finite step includes actual decoding witnesses; no table-existence theorem is silently assumed.</p><p><a href="checked/QF001.html">Exact checked induction theorem</a> · <a href="local-definitions.html">Definition network</a> · <a href="arithmetic-frontier.html">Checked arithmetic DAG</a> · <a href="api/quadratic-trace-definitions.json">Typed expansion DAG</a>.</p></section>'
    body += '<section class="release-note"><h2>Conservative expansion DAG</h2><p>Arrows run from an unchanged prerequisite to the definition using it. They are notation dependencies, not proof certificates.</p><div class="local-definition-graph">'+svg+'</svg></div></section>'
    for name, d in ordered.items():
        deps = ' · '.join('<a href="#'+registry[p].stable_id+'">'+escape(p)+'</a>' for p in d.conceptual_dependencies) or 'No definition prerequisite'
        notation = escape(named_sources.get(name, d.template_source).replace(" /\\ ", " /\\\n  "))
        for parent in d.conceptual_dependencies:
            notation = notation.replace(parent+"(", '<a href="#'+registry[parent].stable_id+'">'+parent+'</a>(')
        body += '<section class="release-note" id="'+d.stable_id+'"><h2>'+d.stable_id+' — '+escape(name)+'</h2><p>'+('New local conservative alias.' if name in local else 'Existing definition, unchanged.')+' Parameters: '+escape(', '.join(d.parameters))+'.</p><p>'+escape(d.summary)+'</p><p>'+deps+'</p><pre class="contract"><code>'+notation+'</code></pre><details><summary>Exact expanded HA definition</summary><pre class="contract"><code>'+escape(d.template_source)+'</code></pre></details></section>'
    return {"quadratic-trace-definitions.html": page("Quadratic product trace definitions", body, revision,
                eyebrow="Finite execution · Conservative definition DAG"),
            "api/quadratic-trace-definitions.json": encoded(data)}


def frontier_files(by_case, contracts, downloads, page, revision):
    selected = {case: row for case, row in by_case.items()
                if case in {"IR016", "SN001", *contracts}}
    hashes = {row["target_ast_sha256"]: case for case, row in selected.items()}
    edges = []
    for case, row in selected.items():
        raw = gzip.decompress(downloads[row["proof_download"]])
        if sha256(raw).hexdigest() != row["bundle_sha256"]:
            raise ValueError("checked DAG certificate changed")
        tree = json.loads(raw)
        for dependency in tree[3][tree[1]][2]:
            target = tree[3][dependency][1]
            digest = sha256(json.dumps(target, separators=(",", ":")).encode()).hexdigest()
            if digest in hashes:
                edges.append(dict(source=hashes[digest], target=case, kind="proof_dependency"))
        del tree, raw
    nodes = [dict(id=case, kind="checked_theorem", target_ast_sha256=row["target_ast_sha256"],
                  bundle_sha256=row["bundle_sha256"], independent_lean_checked=row["independent_lean_checked"])
             for case, row in selected.items()]
    for case, contract in contracts.items():
        nodes.append(dict(id=contract["parent"], kind="open_planning_parent"))
        edges.append(dict(source=case, target=contract["parent"], kind="planned_support_not_closure"))
    # Deduplicate shared planning parents, never theorem evidence.
    nodes = list({node["id"]: node for node in nodes}.values())
    data = dict(authority="local_exact_evidence_and_separate_open_plan", nodes=nodes, edges=edges,
                omitted_historical_dependencies="Complete bodies remain in downloadable bundles.", IR_parents_closed=0)
    positions = {"IR016": (20, 30), "SN001": (225, 30), "SN002": (440, 30), "IR032": (1100, 30),
                 "NG001": (225, 135), "IR003": (1100, 135), "SN003": (225, 250), "IR031": (1100, 250),
                 "RN002": (440, 250), "RN001": (440, 355), "SI001": (440, 460), "IR046": (1100, 460),
                 "QN001": (655, 460), "QF001": (870, 460), "CV001": (440, 595), "IR079": (1100, 595)}
    svg = '<svg viewBox="0 0 1300 680" role="img" aria-label="Actual checked root dependencies and explicitly open planning support"><defs><marker id="arithmetic-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#496779"/></marker></defs>'
    for edge in edges:
        x, y = positions[edge["source"]]
        X, Y = positions[edge["target"]]
        dash = ' stroke-dasharray="6 5"' if edge["kind"] != "proof_dependency" else ""
        path = f"M {x+165} {y+28} L {X} {Y+28}"
        if edge["source"] == "SN003" and edge["target"] == "IR031":
            path = f"M {x+165} {y+28} V {y-20} H {X+82} V {Y}"
        elif edge["target"] == "QN001" and edge["source"] in {"SN001", "SN003"}:
            lane = 410 if edge["source"] == "SN001" else 420
            height = 425 if edge["source"] == "SN001" else 440
            path = f"M {x+165} {y+28} H {lane} V {height} H {X+82} V {Y}"
        elif edge["target"] == "IR046" and edge["source"] in {"SI001", "QN001"}:
            height = 550 if edge["source"] == "SI001" else 565
            path = f"M {x+82} {y+56} V {height} H {X+82} V {Y+56}"
        svg += f'<path d="{path}" fill="none" stroke="#496779" stroke-width="2"{dash} marker-end="url(#arithmetic-arrow)"><title>{edge["kind"]}</title></path>'
    for node in nodes:
        name = node["id"]
        x, y = positions[name]
        checked = node["kind"] == "checked_theorem"
        href = ("wave-results.html" if name == "IR016" else f"checked/{name}.html") if checked else f"map.html?target={name}&amp;view=prerequisites"
        status = "Checked local lemma" if checked else "Open planning parent"
        svg += f'<a href="{href}"><g class="definition-node" id="frontier-{name}"><rect x="{x}" y="{y}" width="165" height="56" rx="8"/><text x="{x+82}" y="{y+22}" text-anchor="middle">{name}</text><text x="{x+82}" y="{y+41}" text-anchor="middle">{status}</text></g></a>'
    svg += '</svg>'
    body = '<section class="release-note"><h2>Checked arithmetic, open analytic frontier</h2><p>Solid arrows are actual direct root dependencies extracted from the accepted proof bundles. Dashed arrows show intended support for an unproved campaign parent. Shared notation is not a proof dependency. Historical ancestors omitted from this small view remain fully present in the downloadable certificates.</p><div class="local-definition-graph">'+svg+'</div></section>'
    body += '<section class="release-note"><h2>Exact statements</h2><ul>'+''.join('<li><a href="checked/'+case+'.html">'+case+' — '+escape(row["title"])+'</a></li>' for case, row in contracts.items())+'</ul><p><a href="local-definitions.html">Conservative definition network</a> · <a href="wave-results.html">All execution evidence</a> · <a href="map.html?target=IR072&amp;view=prerequisites">Full irrationality planning cone</a> · <a href="api/checked-arithmetic-dag.json">Typed DAG data</a>.</p><p>IR072 is still open; no Alpha/Stable admission is implied.</p></section>'
    return {"arithmetic-frontier.html": page("Checked arithmetic frontier", body, revision,
                eyebrow="Actual proof edges · Open planning parents"),
            "api/checked-arithmetic-dag.json": encoded(data)}
