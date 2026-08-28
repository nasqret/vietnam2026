"""Actual local checkpoint checks, canonical QR layout, and navigation audits.

The positive fixture calls both real verifiers. No stored receipt, patched
checker, library admission flag, or fabricated accepted proof supplies evidence.
"""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_constructive_bottom_layer_explorer as builder
import constructive_bottom_layer_checkpoints as checkpoints
import constructive_bottom_layer_explorer_renderer as render
from constructive_bottom_layer_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as DEFINITIONS
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names


FAMILIES = builder.FAMILIES
ROWS = tuple((family, row) for family in FAMILIES
             for row in checkpoints.load_rows(builder._checkpoint(family)))
EXPECTED = {"euler-units": (32, 91, 1203), "prime-fields": (87, 254, 3160),
            "mobius-values": (21, 64, 660), "signed-sums": (30, 73, 1410)}


@pytest.fixture(scope="module")
def files():
    # Fresh original HA checks of every node, plus the independently compiled
    # pinned Lean binary. No production verifier or factory is monkeypatched.
    immutable = [ROOT / "artifacts/peano-library/alpha/catalog-v30.json",
                 ROOT / "book/_static/constructive-gaussian-campaign/campaign.json",
                 ROOT / "book/_static/constructive-gaussian-campaign/definitions.json",
                 ROOT / "book/_static/constructive-gaussian-campaign/index.html"]
    before = {path: sha256(path.read_bytes()).hexdigest() for path in immutable}
    result = builder.build_files()
    assert {path: sha256(path.read_bytes()).hexdigest() for path in immutable} == before
    return result


@pytest.fixture(scope="module")
def corpora(files):
    return {family.slug: json.loads(files[f"{family.slug}/api/corpus.json"]) for family in FAMILIES}


class Document(HTMLParser):
    def __init__(self, payload):
        super().__init__(convert_charrefs=True)
        self.tags, self.ids, self.scripts, self.code = [], [], [], {}
        self.header_tags = []
        self._in_header = False
        self.select_options = {}
        self._select = None
        self._script = None
        self._code_depth = 0
        self._code_buffer = []
        self.codes = []
        self.feed(payload.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, pairs):
        attributes = dict(pairs)
        assert len(attributes) == len(pairs), ("duplicate HTML attribute", tag, pairs)
        self.tags.append((tag, attributes))
        if tag == "header":
            self._in_header = True
        if self._in_header:
            self.header_tags.append((tag, attributes))
        if "id" in attributes:
            self.ids.append(attributes["id"])
        if tag == "select":
            self._select = next((key for key in ("data-kind", "data-layer", "data-proof-status", "data-proof-layer")
                                 if key in attributes), None)
            if self._select is not None:
                self.select_options[self._select] = []
        if tag == "option" and self._select is not None:
            self.select_options[self._select].append(attributes.get("value", ""))
        if tag == "script":
            assert self._script is None
            self._script = [attributes, []]
        if tag == "code":
            assert self._code_depth == 0
            self._code_depth = 1
            self._code_buffer = []

    def handle_data(self, data):
        if self._script is not None:
            self._script[1].append(data)
        if self._code_depth:
            self._code_buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "header":
            self._in_header = False
        if tag == "select":
            self._select = None
        if tag == "script" and self._script is not None:
            self.scripts.append((self._script[0], "".join(self._script[1])))
            self._script = None
        if tag == "code" and self._code_depth:
            self.codes.append("".join(self._code_buffer))
            self._code_depth = 0

    @property
    def classes(self):
        return {name for _, attrs in self.tags for name in attrs.get("class", "").split()}


def _strict_json(payload):
    def pairs(values):
        result = {}
        for key, value in values:
            assert key not in result, key
            result[key] = value
        return result
    return json.loads(payload, object_pairs_hook=pairs)


def _graph_runtime(payload, target, focus, *, complete_family=False, visible_definitions=False):
    # Reuse the established actual-asset/hostile SVG DOM harness without
    # importing its historical Alpha generator and edition inventories.
    source = (ROOT / "peano-lab/py/tests/test_constructive_frontier_explorer.py").read_text()
    function = next(node for node in ast.parse(source).body
                    if isinstance(node, ast.FunctionDef) and node.name == "_canonical_graph_runtime")
    if visible_definitions:
        # Only change the harness's input URL, never the canonical asset.
        changed = 0
        for node in ast.walk(function):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and "&definitions=selected&edges=all" in node.value:
                node.value = node.value.replace("&definitions=selected&edges=all", "&definitions=visible&edges=all")
                changed += 1
        assert changed == 1
    namespace = {"json": json, "subprocess": subprocess,
                 "generator": SimpleNamespace(DEFINED_EXPLORER_SCRIPT=builder.ASSET_SOURCES["defined-explorer.js"])}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "<unchanged QR graph harness>", "exec"), namespace)
    return namespace[function.name](payload, target, focus, complete_family=complete_family)


def test_exact_frozen_frontier_and_four_scopes_are_not_a_new_alpha_edition():
    assert len(ROWS) == len({row.name for _, row in ROWS}) == 170
    assert len(FAMILIES) == len({family.prefix for family in FAMILIES}) == 4
    assert Counter(family.slug for family, _ in ROWS) == Counter({slug: values[0] for slug, values in EXPECTED.items()})
    assert {family.milestones for family in FAMILIES} == {("G014",), ("G091",), ("G007",)}
    assert builder.HTML_REVISION == "ac7111ec14ff"
    assert builder.OUTPUT == ROOT / "book/_static/constructive-bottom-layer-explorer"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_actual_ha_and_lean_receipts_are_complete_but_non_admitting(family, files, corpora):
    corpus = corpora[family.slug]
    checkpoint = builder._checkpoint(family)
    report = _strict_json(files[f"{family.slug}/api/checkpoint.json"])
    assert (corpus["node_count"], corpus["edge_count"], corpus["formal_line_count"]) == EXPECTED[family.slug]
    assert report == corpus["checkpoint_report"]
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert report["bundle"]["nodes_including_packaging_root"] == corpus["proof_bundle_node_count"]
    assert report["bundle"]["inherited_theorems"] + corpus["node_count"] + 1 == corpus["proof_bundle_node_count"]
    assert all(row["complete_ordinary_ha_checked"] is False for row in report["principal_roots"])
    payload = files["checkpoints/" + Path(checkpoint.artifact).name]
    assert payload == (ROOT / checkpoint.artifact).read_bytes()
    assert len(payload) == checkpoint.artifact_bytes
    assert sha256(payload).hexdigest() == checkpoint.artifact_sha256 == corpus["proof_bundle_sha256"]
    assert corpus["local_checkpoint_verified_node_count"] == corpus["node_count"]
    assert corpus["alpha_enrolled_node_count"] == corpus["alpha_checked_use_node_count"] == corpus["stable_admitted_node_count"] == 0
    assert corpus["parent_alpha_edition_version"] == "v30"
    assert corpus["parent_alpha_checked_use_count"] == 3222 and corpus["parent_stable_count"] == 432
    assert corpus["published_atlas_changed"] is False
    for record in (corpus, *corpus["nodes"]):
        assert render._status(record) == render.STATUS
        assert all(record[key] is False for key in render.FORBIDDEN_ADMISSION_FIELDS)
        assert "alpha_edition_version" not in record and "alpha_first_enrolled_version" not in record


@pytest.mark.parametrize("family,row", ROWS, ids=[row.name for _, row in ROWS])
def test_every_theorem_statement_script_and_all_local_propositions_are_exact(family, row, files, corpora):
    corpus = corpora[family.slug]
    node = next(node for node in corpus["nodes"] if node["name"] == row.name)
    assert node["statement"] == row.statement
    assert node["script"] == list(row.script) and node["dependencies"] == list(row.dependencies)
    assert node["statement_sha256"] == sha256(row.statement.encode()).hexdigest()
    assert node["sources"][0]["script_sha256"] == sha256(("\n".join(row.script) + "\n").encode()).hexdigest()
    exact = Document(files[f"{family.slug}/explorer/tag/{node['id']}.html"])
    assert exact.codes[0] == row.statement
    # Embedded tactic links and spans do not alter any source character.
    start = exact.codes.index(row.script[0])
    assert exact.codes[start:start + len(row.script)] == list(row.script)
    definitions = {record["name"]: DEFINITIONS[record["name"]] for record in corpus["definitions"]}
    parsed, names = parse_formula_with_names(row.statement)
    parser = _LocalDefinedParser(node["defined"]["defined_statement"], definitions)
    parser.free = list(names)
    assert parser.parse() == parsed and tuple(parser.free) == names
    assert node["defined"]["exact_ast_equivalence"] is True
    assert len(node["defined"]["script_parts"]) == len(row.script)
    for original, parts in zip(row.script, node["defined"]["script_parts"], strict=True):
        compact = "".join(part["text"] for part in parts)
        tactic = original.partition(" ")[0]
        if tactic not in {"have", "suffices"}:
            assert compact == original
            continue
        prefix, _, statement = original.partition(":")
        other_prefix, _, surface = compact.partition(":")
        assert prefix.strip() == other_prefix.strip()
        formula, names = parse_formula_with_names(statement.strip())
        parser = _LocalDefinedParser(surface.strip(), definitions)
        parser.free = list(names)
        assert parser.parse() == formula and tuple(parser.free) == names


def test_independent_principal_contracts_and_guarded_scope(corpora):
    contracts = {
        "euler-units": ("euler_theorem_for_units", "forall a m t. Lt(1,m) /\\ (Unit(a,m) /\\ Phi(m,t)) -> exists w. Pow(a,t,w) /\\ ModEq(m,w,1)",
                        "fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d"),
        "prime-fields": ("prime_field_of_prime_order_exists", "forall p. Prime(p) -> exists ab ac mb mc nb nc ib ic eb ec. FpFiniteStructure(p,ab,ac,mb,mc,nb,nc,ib,ic,eb,ec)",
                         "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7"),
        "mobius-values": ("mobius_value_exists_unique", "forall n. ~(n=0) -> exists z. Mobius(n,z) /\\ forall w. Mobius(n,w) -> w=z", None),
    }
    for slug, (name, contract, digest) in contracts.items():
        corpus = corpora[slug]
        node = next(node for node in corpus["nodes"] if node["name"] == name)
        parser = _LocalDefinedParser(contract, {row["name"]: DEFINITIONS[row["name"]] for row in corpus["definitions"]})
        assert parser.parse() == parse_formula_with_names(node["statement"])[0]
        if digest is not None:
            assert node["statement_sha256"] == digest
    euler = corpora["euler-units"]
    endpoint = next(node for node in euler["nodes"] if node["name"] == "euler_theorem_for_units")
    count = next(node for node in euler["nodes"] if node["name"] == "euler_unit_count_product_balance")
    assert "Unit(a,m)" in endpoint["defined"]["defined_statement"]
    assert "Phi(m,t)" in endpoint["defined"]["defined_statement"]
    assert "UnitCount(m,l,t)" in count["defined"]["defined_statement"]
    assert "UnitResidue" not in endpoint["defined"]["defined_statement"]
    assert corpora["prime-fields"]["campaign_goal_scope"] == "prime_order_subgoal_only_full_G091_open"
    assert "full_G007_open" in corpora["mobius-values"]["campaign_goal_scope"]
    assert "full_G007_open" in corpora["signed-sums"]["campaign_goal_scope"]


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_definition_identity_exactness_and_acyclic_three_kind_dag(family, corpora, files):
    corpus = corpora[family.slug]
    graph = _strict_json(files[f"{family.slug}/explorer/defined/api/graph.json"])
    assert graph == _strict_json(files[f"{family.slug}/api/graph.json"])
    theorem_ids = {row["id"] for row in corpus["nodes"]}
    definition_ids = {row["id"] for row in corpus["definitions"]}
    assert theorem_ids.isdisjoint(definition_ids)
    assert {edge["kind"] for edge in graph["edges"]} == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["edges"] == corpus["edges"]
    assert graph["path_policy"] == corpus["path_policy"] == "proof_dependency_edges_only"
    seen = set()
    for definition in corpus["definitions"]:
        spec = DEFINITIONS[definition["name"]]
        assert definition["id"] == spec.stable_id
        assert definition["parameters"] == list(spec.parameters)
        assert definition["expanded_template"] == spec.template_source
        assert definition["expansion_sha256"] == sha256(spec.template_source.encode()).hexdigest()
        assert definition["dependencies"] == [DEFINITIONS[name].stable_id for name in spec.conceptual_dependencies]
        assert set(definition["dependencies"]) <= seen
        assert definition["global_definition"] is None
        seen.add(spec.stable_id)
    assert list(seen) or corpus["definition_count"] == 0
    proof = set()
    for edge in corpus["edges"]:
        if edge["kind"] == "proof_dependency":
            assert edge["source"] in theorem_ids and edge["target"] in theorem_ids
            proof.add((edge["source"], edge["target"]))
        elif edge["kind"] == "uses_definition":
            assert edge["source"] in theorem_ids and edge["target"] in definition_ids
            assert edge["occurrence_count"] == edge["statement_occurrences"] + edge["local_proposition_occurrences"]
        else:
            assert edge["source"] in definition_ids and edge["target"] in definition_ids
    for path in corpus["proof_paths"].values():
        assert set(path) <= theorem_ids
        assert all(pair in proof for pair in zip(path, path[1:]))


def test_historical_aliases_are_reused_without_relabeling_or_false_concepts(corpora):
    prime = {row["name"]: row for row in corpora["prime-fields"]["definitions"]}
    signed = {row["name"]: row for row in corpora["signed-sums"]["definitions"]}
    assert prime["CanonicalModularResidue"]["id"] == "ND0023"
    assert prime["IdentityMatrixSelector"]["id"] == "ND0141"
    assert signed["MatrixMinorFourCode"]["id"] == "ND0058"
    assert "FiniteField" not in prime and "FpResidue" not in prime
    assert "ArithTableRep" not in signed


@pytest.mark.parametrize("name,digest", tuple(builder.ASSET_DIGESTS.items()))
def test_all_original_qr_assets_are_byte_identical(name, digest, files):
    payload = files["assets/" + name]
    assert payload == builder.ASSET_SOURCES[name].read_bytes()
    assert sha256(payload).hexdigest() == digest


def _landing_structure(payload):
    markers = {"family-hero", "shell", "crumbs", "eyebrow", "formula", "lede", "hero-actions",
               "family-main", "view-grid", "view-card", "featured", "card-kicker", "release-note"}
    return [(tag, tuple(name for name in attrs.get("class", "").split() if name in markers))
            for tag, attrs in Document(payload).tags if markers & set(attrs.get("class", "").split())]


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_canonical_three_card_landing_and_exact_defined_topology(family, files, corpora):
    reference = ROOT / "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html"
    assert _landing_structure(files[f"{family.slug}/index.html"]) == _landing_structure(reference.read_bytes())
    landing = Document(files[f"{family.slug}/index.html"])
    assert sum("view-card" in attrs.get("class", "").split() for _, attrs in landing.tags) == 3
    assert any(attrs.get("name") == "robots" and attrs.get("content") == "noindex" for _, attrs in landing.tags)
    assert not any(attrs.get("rel") == "canonical" for _, attrs in landing.tags)
    for node in corpora[family.slug]["nodes"]:
        for mode in ("explorer/tag", "explorer/defined/tag"):
            assert f"{family.slug}/{mode}/{node['id']}.html" in files
    for definition in corpora[family.slug]["definitions"]:
        assert f"{family.slug}/explorer/defined/definition/{definition['id']}.html" in files


def test_every_actual_html_link_and_fragment_has_a_correct_local_target(files):
    documents = {name: Document(payload) for name, payload in files.items() if name.endswith(".html")}
    external = set()
    for name, document in documents.items():
        assert len(document.ids) == len(set(document.ids)), name
        for tag, attrs in document.tags:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                href = attrs[key]
                url = urlsplit(href)
                assert not url.scheme and not url.netloc, (name, href)
                assert not url.path.startswith("/"), (name, href)
                target = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(url.path))) if url.path else name
                if url.path.endswith("/"):
                    target = posixpath.normpath(target + "/index.html")
                if target.startswith("../"):
                    assert target == "../constructive-gaussian-campaign/index.html", (name, href)
                    assert (builder.OUTPUT / target).is_file()
                    external.add((target, parse_qs(url.query).get("focus", [None])[0]))
                else:
                    assert target in files, (name, href, target)
                    if url.fragment:
                        assert unquote(url.fragment) in documents[target].ids, (name, href)
                if url.path:
                    assert parse_qs(url.query).get("v") == [
                        builder.ASSET_DIGESTS[Path(url.path).name][:12]
                        if tag in {"script", "link"} and Path(url.path).name in render.ASSET_DIGESTS
                        else builder.HTML_REVISION
                    ], (name, href)
    assert {focus for _, focus in external} == {None, "G014", "G091", "G007"}


def test_actual_html_scripts_all_compile_and_graph_payloads_equal_json_apis(files):
    scripts = []
    for name, payload in files.items():
        if not name.endswith(".html"):
            continue
        for attrs, source in Document(payload).scripts:
            if attrs.get("type", "").lower() in {"application/json", "application/ld+json"}:
                _strict_json(source)
            elif "src" not in attrs:
                scripts.append({"name": name, "source": source})
            if attrs.get("id") == "pa-defined-graph-data":
                assert source.startswith("window.PA_DEFINED_GRAPH=") and source.endswith(";")
                data = _strict_json(source[len("window.PA_DEFINED_GRAPH="):-1])
                assert data == _strict_json(files[name.replace("graph.html", "api/graph.json")])
    program = 'const vm=require("node:vm"); const rows=JSON.parse(require("node:fs").readFileSync(0,"utf8")); rows.forEach(x=>new vm.Script(x.source,{filename:x.name})); process.stdout.write(String(rows.length));'
    completed = subprocess.run(["node", "-e", program], input=json.dumps(scripts), text=True,
                               capture_output=True, timeout=20, check=True)
    assert int(completed.stdout) == len(scripts) == 14


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
@pytest.mark.parametrize("focus_kind", ("theorem", "definition"))
def test_real_canonical_graph_with_getter_only_svg_hrefs(family, focus_kind, files):
    graph = _strict_json(files[f"{family.slug}/api/graph.json"])
    target = graph["root_ids"][-1]
    focus = target if focus_kind == "theorem" else next(node["id"] for node in graph["nodes"] if node["kind"] == "definition")
    result = _graph_runtime(graph, target, focus, complete_family=True)
    assert result["svgHrefIsGetterOnly"] is result["allSvgHrefsAreGetterOnly"] is True
    assert result["viewportRendered"] is True
    assert result["sidebarHref"] == next(node["href"] for node in graph["nodes"] if node["id"] == focus)
    assert result["selectedNodeIds"] == [focus]
    assert {node["id"] for node in graph["nodes"] if node["kind"] == "theorem"} <= set(result["renderedNodeIds"])
    assert result["renderedArrowCount"] > 0


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_full_family_graph_displays_every_used_definition_and_only_typed_edges(family, files):
    graph = _strict_json(files[f"{family.slug}/api/graph.json"])
    target = graph["root_ids"][-1]
    expected = {row["id"] for row in graph["nodes"] if row["kind"] == "theorem"}
    while True:
        additional = {edge["target"] for edge in graph["edges"]
                      if edge["kind"] != "proof_dependency" and edge["source"] in expected}
        if additional <= expected:
            break
        expected.update(additional)
    result = _graph_runtime(graph, target, target, complete_family=True, visible_definitions=True)
    assert set(result["renderedNodeIds"]) == expected
    assert result["renderedArrowCount"] == sum(edge["source"] in expected and edge["target"] in expected for edge in graph["edges"])
    assert result["allSvgHrefsAreGetterOnly"] is True


def test_every_exact_page_prevents_the_original_asset_from_injecting_a_missing_graph_link(files):
    cases = []
    for name, payload in files.items():
        if "/explorer/" not in name or "/defined/" in name or not name.endswith(".html"):
            continue
        document = Document(payload)
        links = [attrs["href"] for tag, attrs in document.header_tags if tag == "a" and "data-graph-navigation" in attrs]
        assert len(links) == 1 and "defined/graph.html" in links[0], name
        page = next(attrs["data-page"] for tag, attrs in document.tags if tag == "body")
        assert any(tag == "header" and "pa-proof-header" in attrs.get("class", "").split()
                   for tag, attrs in document.header_tags)
        cases.append({"name": name, "page": page, "href": links[0]})
    source = builder.ASSET_SOURCES["exact-explorer.js"].read_text()
    start = source.index("  function initializeGraphNavigation()")
    end = source.index("\n  function ", start + 1)
    program = '''const vm=require("node:vm"), input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
input.cases.forEach(row=>{
 const anchor={getAttribute(){return row.href;}};
 const header={querySelector(selector){if(selector==="[data-graph-navigation]")return anchor;throw Error("unexpected selector "+selector);}};
 const document={body:{dataset:{page:row.page}},querySelector(selector){if(selector===".pa-proof-header")return header;throw Error("unexpected document selector "+selector);},createElement(){throw Error("bad graph injection in "+row.name);}};
 vm.runInNewContext(input.source+"\\ninitializeGraphNavigation();",{document});
}); process.stdout.write(String(input.cases.length));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"cases": cases, "source": source[start:end]}),
                            text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == 174


@pytest.mark.parametrize("query,visible", (
    ("", ("euler-units", "prime-fields", "mobius-values", "signed-sums")),
    ("?view=goal&focus=G014", ("euler-units",)),
    ("?view=goal&focus=G091", ("prime-fields",)),
    ("?view=goal&focus=G007", ("mobius-values", "signed-sums")),
    ("?view=family&focus=F01", ("mobius-values", "signed-sums")),
    ("?view=domain&focus=D01", ("euler-units", "mobius-values", "signed-sums")),
    ("?view=domain&focus=D04", ("prime-fields",)),
    ("?view=goal&focus=G999", ("euler-units", "prime-fields", "mobius-values", "signed-sums")),
    ("?view=unknown&focus=G007", ("euler-units", "prime-fields", "mobius-values", "signed-sums")),
))
def test_actual_local_dispatch_filters_only_the_requested_known_scale(query, visible, files):
    document = Document(files["grand-campaign/index.html"])
    cards = [attrs for tag, attrs in document.tags if "data-local-family" in attrs]
    source = document.scripts[-1][1]
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const cards=input.cards.map(attrs=>({attrs,hidden:false,getAttribute(key){return this.attrs[key];}}));
vm.runInNewContext(input.source,{URL,window:{location:{href:"file:///repo/book/_static/constructive-bottom-layer-explorer/grand-campaign/"+input.query}},document:{querySelectorAll(selector){if(selector!=="[data-local-family]")throw Error(selector);return cards;}}});
process.stdout.write(JSON.stringify(cards.filter(card=>!card.hidden).map(card=>card.attrs.id)));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"source": source, "cards": cards, "query": query}),
                            text=True, capture_output=True, timeout=20, check=True)
    assert json.loads(result.stdout) == list(visible)


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_actual_graph_detail_overlay_never_calls_a_local_theorem_alpha_checked(family, files):
    graph = _strict_json(files[f"{family.slug}/api/graph.json"])
    document = Document(files[f"{family.slug}/explorer/defined/graph.html"])
    source = next(source for attrs, source in document.scripts if "MutationObserver" in source)
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const node=input.graph.nodes.find(row=>row.id===input.graph.root_ids.at(-1)),title={textContent:node.id+" · "+node.name},kind={textContent:"Body-checked theorem candidate"};
let callback;class MutationObserver{constructor(fn){callback=fn;}observe(target){if(target!==title)throw Error("wrong observer target");}}
const document={querySelector(selector){return selector==="[data-graph-title]"?title:selector==="[data-graph-kind]"?kind:null;},addEventListener(event,fn){if(event!=="DOMContentLoaded")throw Error(event);fn();}};
vm.runInNewContext(input.source,{document,MutationObserver,window:{PA_DEFINED_GRAPH:input.graph}});
const theoremLabel=kind.textContent; const definition=input.graph.nodes.find(row=>row.kind==="definition");title.textContent=definition.id+" · "+definition.name;kind.textContent="Conservative definition";callback();
process.stdout.write(JSON.stringify({theoremLabel,definitionLabel:kind.textContent}));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({"source": source, "graph": graph}),
                            text=True, capture_output=True, timeout=20, check=True)
    data = json.loads(result.stdout)
    assert data["theoremLabel"] == "Local HA + independent Lean checkpoint — not Alpha-enrolled; no checked-use authority; not Stable"
    assert data["definitionLabel"] == "Conservative definition"


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
@pytest.mark.parametrize("ready_state", ("loading", "complete"))
@pytest.mark.parametrize("canonical_first", (False, True))
def test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters(
    family, ready_state, canonical_first, files, corpora
):
    document = Document(files[f"{family.slug}/explorer/defined/index.html"])
    corpus = corpora[family.slug]
    cards = [attrs for tag, attrs in document.tags if "data-entry" in attrs]
    layers = sorted({int(row["data-layer"]) for row in cards})
    assert document.select_options["data-layer"] == ["all", *map(str, layers)]
    assert set(layers) == set(corpus["layers"].values()) | {row["topological_layer"] for row in corpus["definitions"]}
    addon = next(source for attrs, source in document.scripts if "data-local-dashboard-enhancement" in attrs)
    root_name = family.roots[-1]
    root_id = corpus["tags"][root_name]
    root_layer = str(corpus["layers"][root_name])
    definition_layer = str(max(row["topological_layer"] for row in corpus["definitions"]))
    steps = [("layer", root_layer, "change"), ("kind", "theorem", "change"),
             ("search", root_id, "input"), ("kind", "definition", "change"),
             ("search", "", "input"), ("layer", definition_layer, "change"),
             ("clear", "", "click")]
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const events={},ready=[],cards=input.cards.map((attrs,i)=>({i,hidden:false,dataset:{kind:attrs["data-kind"],layer:attrs["data-layer"],search:attrs["data-search"]}}));
class Element{constructor(value=""){this.value=value;this.textContent="";this.events={};this.focusCount=0;}addEventListener(name,fn){(this.events[name]??=[]).push(fn);}focus(){this.focusCount++;}}
const controls={search:new Element(),kind:new Element("all"),layer:new Element("all"),clear:new Element(),count:new Element()};
const root=new Element();root.querySelector=function(selector){const key={"[data-search]":"search","[data-kind]":"kind","[data-layer]":"layer","[data-clear]":"clear","[data-count]":"count"}[selector];if(!key)throw Error(selector);return controls[key];};
root.querySelectorAll=function(selector){if(selector!=="[data-entry]")throw Error(selector);return cards;};
const document={readyState:input.readyState,body:{classList:{contains(value){return value==="pa-defined-proof-site";}}},querySelectorAll(selector){if(selector==="[data-defined-dashboard]")return [root];if(["[data-defined-graph]","[data-copy-target]",".pd-proof-line.pd-line-target"].includes(selector))return [];throw Error(selector);},getElementById(){return null;},addEventListener(event,fn){if(event!=="DOMContentLoaded")throw Error(event);ready.push(fn);}};
const window={location:{hash:""},addEventListener(event,fn){(events[event]??=[]).push(fn);}};
const context=vm.createContext({document,window});
(input.canonicalFirst?[input.canonical,input.addon]:[input.addon,input.canonical]).forEach(source=>vm.runInContext(source,context));
ready.forEach(fn=>fn());
function state(){return {visible:cards.filter(x=>!x.hidden).map(x=>x.i),count:controls.count.textContent,search:controls.search.value,kind:controls.kind.value,layer:controls.layer.value};}
const states=[state()];input.steps.forEach(([key,value,type])=>{const target=controls[key];target.value=value;const event={target};(target.events[type]||[]).forEach(fn=>fn(event));(root.events[type]||[]).forEach(fn=>fn(event));states.push(state());});
process.stdout.write(JSON.stringify({states,focused:controls.search.focusCount}));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({
        "canonical": builder.ASSET_SOURCES["defined-explorer.js"].read_text(),
        "addon": addon, "cards": cards, "steps": steps,
        "readyState": ready_state, "canonicalFirst": canonical_first,
    }), text=True, capture_output=True, timeout=20, check=True)
    actual = json.loads(result.stdout)
    search, kind, layer = "", "all", "all"
    for index, state in enumerate(actual["states"]):
        if index:
            key, value, _ = steps[index - 1]
            if key == "search":
                search = value
            elif key == "kind":
                kind = value
            elif key == "layer":
                layer = value
            else:
                search, kind, layer = "", "all", "all"
        visible = [i for i, attrs in enumerate(cards)
                   if (not search or search.lower() in attrs["data-search"].lower())
                   and (kind == "all" or kind == attrs["data-kind"])
                   and (layer == "all" or layer == attrs["data-layer"])]
        assert state == {"visible": visible, "count": str(len(visible)) + (" entry" if len(visible) == 1 else " entries"),
                         "search": search, "kind": kind, "layer": layer}
    assert len(actual["states"][3]["visible"]) == 1
    assert actual["states"][4]["visible"] == []
    assert actual["focused"] >= 1


@pytest.mark.parametrize("family", FAMILIES, ids=lambda family: family.slug)
def test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes(family, files, corpora):
    corpus = corpora[family.slug]
    root_id = corpus["tags"][family.roots[-1]]
    document = Document(files[f"{family.slug}/explorer/defined/tag/{root_id}.html"])
    lines = [attrs for tag, attrs in document.tags if "pd-proof-line" in attrs.get("class", "").split()]
    assert len(lines) >= 2
    assert [row["id"] for row in lines] == [f"proof-line-{i:04d}" for i in range(1, len(lines) + 1)]
    links = [attrs["href"] for _, attrs in document.tags if "pd-line-number" in attrs.get("class", "").split()]
    assert links == ["#" + row["id"] for row in lines]
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const callbacks={},lines=input.lines.map(attrs=>{const classes=new Set(attrs.class.split(" "));return {id:attrs.id,focusCalls:[],classList:{contains(name){return classes.has(name);},add(name){classes.add(name);},remove(name){classes.delete(name);}},focus(options){this.focusCalls.push(options);}};});
const document={readyState:"complete",body:{classList:{contains(name){return name==="pa-defined-proof-site";}}},getElementById(id){return lines.find(x=>x.id===id)||null;},querySelectorAll(selector){if(selector===".pd-proof-line.pd-line-target")return lines.filter(x=>x.classList.contains("pd-line-target"));if(["[data-defined-dashboard]","[data-defined-graph]","[data-copy-target]"].includes(selector))return [];throw Error(selector);}};
const window={location:{hash:"#"+lines[0].id},addEventListener(event,fn){(callbacks[event]??=[]).push(fn);}};
vm.runInNewContext(input.canonical,{document,window});
function state(){return {marked:lines.filter(x=>x.classList.contains("pd-line-target")).map(x=>x.id),focusCalls:lines.map(x=>x.focusCalls.slice()),tabIndex:lines.slice(0,2).map(x=>x.tabIndex??null)};}
const initial=state();window.location.hash="#"+lines[1].id;callbacks.hashchange.forEach(fn=>fn());const changed=state();window.location.hash="#unrelated-fragment";callbacks.hashchange.forEach(fn=>fn());process.stdout.write(JSON.stringify({initial,changed,unrelated:state()}));'''
    result = subprocess.run(["node", "-e", program], input=json.dumps({
        "lines": lines, "canonical": builder.ASSET_SOURCES["defined-explorer.js"].read_text(),
    }), text=True, capture_output=True, timeout=20, check=True)
    data = json.loads(result.stdout)
    assert data["initial"]["marked"] == ["proof-line-0001"]
    assert not any(data["initial"]["focusCalls"])
    assert data["initial"]["tabIndex"] == [-1, None]
    assert data["changed"]["marked"] == ["proof-line-0002"]
    assert data["changed"]["focusCalls"][0] == []
    assert data["changed"]["focusCalls"][1] == [{"preventScroll": False}]
    assert data["changed"]["tabIndex"] == [-1, -1]
    assert data["unrelated"]["marked"] == []
    assert data["unrelated"]["focusCalls"] == data["changed"]["focusCalls"]


@pytest.mark.parametrize("field", render.FORBIDDEN_ADMISSION_FIELDS)
@pytest.mark.parametrize("value", (True, 1, None))
def test_local_labels_reject_admission_or_ambiguous_boolean(field, value, corpora):
    record = {**corpora["euler-units"], field: value}
    with pytest.raises(render.LocalExplorerRenderError):
        render.render_local_family_landing(FAMILIES[0], record, revision=builder.HTML_REVISION,
                                          bundle_node_count=corpora["euler-units"]["proof_bundle_node_count"])


@pytest.mark.parametrize("field", ("local_checkpoint_verified", "original_ha_bundle_verified", "independent_lean_bundle_verified"))
def test_missing_actual_check_labels_are_not_rendered_as_verified(field, corpora):
    with pytest.raises(render.LocalExplorerRenderError):
        render._status({**corpora["euler-units"], field: False})


@pytest.mark.parametrize("field", ("alpha_first_enrolled_version", "alpha_edition_version", "alpha_evidence", "first_admitted_version"))
def test_local_rows_cannot_impersonate_a_new_alpha_version(field, corpora):
    with pytest.raises(render.LocalExplorerRenderError):
        render._status({**corpora["euler-units"], field: "v31"})


def test_a_verifier_refusal_cannot_write_verified_pages(monkeypatch, capsys):
    def refuse(*args, **kwargs):
        raise checkpoints.CheckpointError("actual checker refused")
    def should_not_write(*args, **kwargs):
        pytest.fail("a failed proof verification reached the publication writer")
    monkeypatch.setattr(checkpoints, "verify_checkpoint", refuse)
    monkeypatch.setattr(builder, "write_or_check", should_not_write)
    assert builder.main([]) == 1
    assert "actual checker refused" in capsys.readouterr().err


def test_literal_source_and_asset_tampering_fails_closed(tmp_path):
    source = tmp_path / "changed.css"
    source.write_bytes(b"changed source")
    with pytest.raises(builder.BottomLayerExplorerError):
        builder._bounded_source(source, builder.ASSET_DIGESTS["proofs.css"])
    link = tmp_path / "link.css"
    link.symlink_to(source)
    with pytest.raises(builder.BottomLayerExplorerError):
        builder._bounded_source(link)


def test_snapshot_is_exact_deterministic_and_never_rewrites_unknown_files(files, tmp_path):
    builder.write_or_check(files, check=True)
    manifest = _strict_json(files["manifest.json"])
    assert manifest["file_count_excluding_manifest"] == len(files) - 1
    assert set(manifest["files"]) == files.keys() - {"manifest.json"}
    for path, data in manifest["files"].items():
        assert data == {"bytes": len(files[path]), "sha256": sha256(files[path]).hexdigest()}
    inventory = _strict_json(files["checkpoints.json"])
    digest = inventory.pop("checkpoint_digest")
    assert sha256(builder._json(inventory)).hexdigest() == digest == manifest["checkpoint_digest"]
    assert digest != builder.closure.PARENT_CATALOG_SHA256
    assert inventory["alpha_admission_performed"] is inventory["stable_admission_performed"] is inventory["published"] is False
    assert "lean_version" not in inventory["independent_checker"]
    assert inventory["independent_checker"]["binary_sha256"] == "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
    unknown = tmp_path / "keep.txt"
    unknown.write_bytes(b"unrelated user data")
    with pytest.raises(builder.BottomLayerExplorerError, match="unexpected"):
        builder.write_or_check({"index.html": b"page"}, output=tmp_path)
    assert unknown.read_bytes() == b"unrelated user data"
    assert not (tmp_path / "index.html").exists()


@pytest.mark.parametrize("path", ("../escape.html", "/absolute.html", "a/../b", "a//b", "a\\b", ""))
def test_snapshot_paths_cannot_escape_the_owned_new_tree(path, tmp_path):
    with pytest.raises(builder.BottomLayerExplorerError):
        builder.write_or_check({path: b"not written"}, output=tmp_path)
    assert not list(tmp_path.iterdir())


def test_snapshot_size_mismatch_is_rejected_before_any_content_read(tmp_path, monkeypatch):
    path = tmp_path / "index.html"
    path.write_bytes(b"larger than the expected four bytes")
    original = Path.open
    def guarded(self, *args, **kwargs):
        if self == path:
            pytest.fail("size mismatch reached a snapshot content read")
        return original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(builder.BottomLayerExplorerError, match="unexpected file size"):
        builder.write_or_check({"index.html": b"page"}, output=tmp_path, check=True)


def test_snapshot_comparison_bounds_even_a_file_growing_after_stat(tmp_path, monkeypatch):
    path = tmp_path / "index.html"
    path.write_bytes(b"page")
    requests = []
    original = Path.open
    class GrowingReader:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, limit):
            requests.append(limit)
            assert limit == 5
            return b"page!"
    def guarded(self, *args, **kwargs):
        return GrowingReader() if self == path else original(self, *args, **kwargs)
    monkeypatch.setattr(Path, "open", guarded)
    with pytest.raises(builder.BottomLayerExplorerError, match="stale or incomplete"):
        builder.write_or_check({"index.html": b"page"}, output=tmp_path, check=True)
    assert requests == [5]


def test_human_headlines_preserve_prime_and_positive_guards_and_actual_arities():
    by_slug = {family.slug: family for family in FAMILIES}
    assert "Prime(p) ∧ n>0 ∧ p∤n" in by_slug["mobius-values"].formula
    assert "FpFiniteStructure(p,ab,ac,mb,mc,nb,nc,ib,ic,eb,ec)" in by_slug["prime-fields"].formula
    assert "SignedPrefixSum(F,l,u) ∧ SignedPrefixSum(G,l,v)" in by_slug["signed-sums"].formula
    assert "m>1 ∧ Unit(a,m) ∧ Phi(m,t)" in by_slug["euler-units"].formula


def test_verifier_identity_not_unauthenticated_toolchain_version_is_displayed(files):
    for name, payload in files.items():
        if name.endswith(".html") or name == "checkpoints.json":
            assert b"4.28.0" not in payload and b"4.31" not in payload, name
    inventory = _strict_json(files["checkpoints.json"])
    assert inventory["independent_checker"] == {"binary_sha256": checkpoints.LEAN_BINARY_SHA256}


def test_euler_deduplication_preserves_all_surviving_tags_and_reserves_old_slots(files, corpora):
    corpus = corpora["euler-units"]
    assert corpus["reserved_tag_slots"] == {
        "EU0003": "euler_modulus_above_one_nonzero",
        "EU001C": "euler_product_scale_shuffle",
    }
    # Golden over every surviving v1 name/tag pair, not just the final root.
    assert sha256(json.dumps(corpus["tags"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == "5ce5feb11b98873f8eed312548e9bdbf8573fb5fe967da43746135a993762bd5"
    assert corpus["tags"]["euler_theorem_for_units"] == "EU0022"
    assert set(corpus["reserved_tag_slots"]).isdisjoint(corpus["tags"].values())
    assert set(corpus["reserved_tag_slots"].values()).isdisjoint(corpus["tags"])
    for tag in corpus["reserved_tag_slots"]:
        assert f"euler-units/explorer/tag/{tag}.html" not in files
        assert f"euler-units/explorer/defined/tag/{tag}.html" not in files
    external = {row["name"] for row in corpus["external_dependencies"]}
    assert {"binary_modulus_nontrivial_nonzero", "mul_shuffle_four"} <= external


def test_superseded_euler_v1_archive_preserves_exact_old_sources_and_is_non_admitting():
    archive = ROOT / "research/arithmetic-library/artifacts/bottom-layer-euler-units-v1-sources"
    manifest = _strict_json((archive / "manifest.json").read_bytes())
    assert manifest["status"] == "superseded_non_admitting_checkpoint"
    assert manifest["alpha_admission_performed"] is manifest["stable_admission_performed"] is False
    assert manifest["frontier_count"] == 34 and manifest["successor_distinct_frontier_count"] == 32
    pins = {
        "euler_units_residue_candidate.py": "8062c334d6654ccc856cec62f1e8ae6e22f4aeea86944ebd4f611bda87af6476",
        "euler_units_product_candidate.py": "dfbbc7dd69672992eb99a4eb99f64fb8273c28838aa6e1e749eb5b8a075ef8b9",
        "euler_units_candidate.py": "87554674bae4815b9837a14791314350dd43c38b73cf2de1c107560ce4c94aa2",
        "euler-units-rfc-v1.md": "436ee2e3ab872b3d5ae0cacdb9121b3f389168eb6981a01d42f1a52c892b7f40",
    }
    assert set(manifest["files"]) == pins.keys()
    for name, digest in pins.items():
        payload = (archive / name).read_bytes()
        assert not (archive / name).is_symlink()
        assert manifest["files"][name] == {"bytes": len(payload), "sha256": digest}
        assert sha256(payload).hexdigest() == digest
    bundle = (ROOT / manifest["bundle"]["path"]).read_bytes()
    assert len(bundle) == manifest["bundle"]["bytes"] == 572243
    assert sha256(bundle).hexdigest() == manifest["bundle"]["sha256"] == "a21c22cbe23e48e540ec637ee75bed906ba6030b794b5b57a72c7bc5ec970949"
    assert (ROOT / "research/arithmetic-library/artifacts/bottom-layer-checkpoints-v1.json").is_file()
