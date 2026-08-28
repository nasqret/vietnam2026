"""Real proof checks and public-delivery-only QR checkpoint contracts."""

from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
from html import unescape
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
import build_constructive_bottom_layer_publication as builder
import constructive_bottom_layer_publication_adapter as adapter


# Reuse the existing actual canonical-JS DOM drivers without importing the old
# test module or modifying any production checker. The selected functions have
# their decorators removed solely to call them with this public byte inventory.
def _drivers():
    local = builder._local_builder()
    path = ROOT / "peano-lab/py/tests/test_constructive_bottom_layer_explorer.py"
    names = {
        "Document", "_strict_json", "_graph_runtime", "_landing_structure",
        "test_actual_html_scripts_all_compile_and_graph_payloads_equal_json_apis",
        "test_every_exact_page_prevents_the_original_asset_from_injecting_a_missing_graph_link",
        "test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters",
        "test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes",
    }
    nodes = [node for node in ast.parse(path.read_text()).body
             if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in names]
    assert {node.name for node in nodes} == names
    for node in nodes:
        node.decorator_list = []
    namespace = {"ROOT": ROOT, "builder": local, "HTMLParser": HTMLParser, "json": json,
                 "ast": ast, "Path": Path, "subprocess": subprocess, "SimpleNamespace": SimpleNamespace}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), "exec"), namespace)
    return namespace


@pytest.fixture(scope="module")
def drivers():
    return _drivers()


@pytest.fixture(scope="module")
def local_files():
    output = ROOT / "book/_static/constructive-bottom-layer-explorer"
    files = {path.relative_to(output).as_posix(): path.read_bytes()
             for path in output.rglob("*") if path.is_file()}
    adapter.validate_local_files(files)
    return files


@pytest.fixture(scope="module")
def files(local_files):
    # Mandatory positive gate: fresh original HA checks and the actual pinned,
    # independently compiled Lean binary, not a patched checker or receipt.
    output = ROOT / "book/_static/constructive-bottom-layer-explorer"
    result = builder.build_files()
    assert {path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*") if path.is_file()} == local_files
    builder.write_or_check(result, check=True)
    return result


@pytest.fixture(scope="module")
def corpora(files):
    return {slug: adapter.strict_json(files[slug + "/api/corpus.json"]) for slug in adapter.FAMILY_COUNTS}


def test_real_four_checkpoint_publication_is_not_an_alpha_release(files):
    inventory = adapter.strict_json(files["checkpoints.json"])
    assert inventory["schema"] == adapter.SCHEMA
    assert inventory["publication_scope"] == "public_research_checkpoint"
    assert inventory["delivery_metadata_only"] is True
    assert inventory["alpha_admission_performed"] is inventory["stable_admission_performed"] is False
    assert inventory["on_demand_alpha_lean_service_exposes_frontier"] is False
    assert inventory["parent"]["alpha_checked_use_count"] == 3222
    assert inventory["parent"]["stable_count"] == 432
    assert inventory["parent"]["alpha_version"] == "v30"
    assert inventory["new_theorem_count"] == 170
    assert "published" not in inventory
    assert inventory["navigation_revision"] == "ac7111ec14ff"
    assert inventory["checkpoint_digest"] == adapter.LOCAL_CHECKPOINT_DIGEST
    assert len(files) == 495


@pytest.mark.parametrize("slug,count", tuple(adapter.FAMILY_COUNTS.items()))
def test_all_exact_math_and_definition_dag_bytes_are_preserved(slug, count, files, local_files):
    old = adapter.strict_json(local_files[slug + "/api/corpus.json"])
    new = adapter.strict_json(files[slug + "/api/corpus.json"])
    assert len(new["nodes"]) == count
    assert new["publication_scope"] == adapter.SCOPE
    assert new["candidate_status"] == adapter.STATUS
    changed_keys = {"schema", "publication_scope", "candidate_status", "campaign_goal_scope", "nodes",
                    "external_theorem_routes", "external_route_boundary", "on_demand_alpha_lean_service_exposes_frontier"}
    assert {key: value for key, value in old.items() if key not in changed_keys} == {
        key: value for key, value in new.items() if key not in changed_keys}
    for before, after in zip(old["nodes"], new["nodes"], strict=True):
        assert before | {"status": adapter.STATUS} == after
        assert all(after[key] is False for key in adapter.ADMISSION_FLAGS)
        assert all(after[key] is True for key in ("local_checkpoint_verified", "original_ha_bundle_verified", "independent_lean_bundle_verified"))
        assert "alpha_first_enrolled_version" not in after and "alpha_edition_version" not in after
    assert all(new[key] is False for key in adapter.ADMISSION_FLAGS)
    assert new["alpha_checked_use_node_count"] == new["stable_admitted_node_count"] == 0
    assert new["checkpoint_report"] == adapter.strict_json(files[slug + "/api/checkpoint.json"])
    graph = adapter.strict_json(files[slug + "/api/graph.json"])
    old_graph = adapter.strict_json(local_files[slug + "/api/graph.json"])
    assert old_graph | {"schema": adapter.SCHEMA + "-graph", "publication_scope": adapter.SCOPE} == graph
    assert files[slug + "/api/graph.json"] == files[slug + "/explorer/defined/api/graph.json"]
    assert {edge["kind"] for edge in graph["edges"]} == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["path_policy"] == "proof_dependency_edges_only"


def test_receipts_bundles_sources_and_original_assets_remain_literal(files, local_files):
    pinned = [name for name in local_files if name.startswith(("assets/", "sources/", "checkpoints/"))
              or name.endswith("/api/checkpoint.json")]
    assert len(pinned) == 27
    assert {name: files[name] for name in pinned} == {name: local_files[name] for name in pinned}
    assert files["receipts/local-checkpoints.json"] == local_files["checkpoints.json"]
    historical = adapter.strict_json(files["receipts/local-checkpoints.json"])
    assert historical["publication_scope"] == "local-only-checkpoint"
    assert historical["published"] is False
    assert len(historical["checkpoints"]) == 4
    assert all(report["bundle"]["original_ha_checked"] is True and report["bundle"]["independent_lean_checked"] is True
               for report in historical["checkpoints"])
    assert all(report["membership"] == "local_non_admitting_checkpoint" for report in historical["checkpoints"])


def test_every_actual_html_preserves_proofs_and_has_public_metadata(files, local_files, drivers):
    Document = drivers["Document"]
    pages = {name: payload for name, payload in files.items() if name.endswith(".html")}
    assert len(pages) == 452
    for name, payload in pages.items():
        before, after = Document(local_files[name]), Document(payload)
        assert before.codes == after.codes, name
        # Include expanded receipt statements and definitions without <code>.
        assert re.findall(rb"<pre\b.*?</pre>", local_files[name], re.DOTALL) == re.findall(rb"<pre\b.*?</pre>", payload, re.DOTALL), name
        assert before.ids == after.ids
        assert len(after.ids) == len(set(after.ids))
        canonical = adapter.ORIGIN + adapter.PUBLIC_BASE + name.removesuffix("index.html")
        assert [attrs["href"] for tag, attrs in after.tags if tag == "link" and attrs.get("rel") == "canonical"] == [canonical]
        assert [attrs["content"] for tag, attrs in after.tags if attrs.get("property") == "og:url"] == [canonical]
        assert [attrs["content"] for tag, attrs in after.tags if attrs.get("property") == "og:image"] == [adapter.ORIGIN + "/proofs/assets/proofs-og.png"]
        assert [attrs["content"] for tag, attrs in after.tags if attrs.get("name") == "proof-publication-scope"] == [adapter.SCOPE]
        assert not any(attrs.get("name") == "robots" for _, attrs in after.tags)
        assert sum("data-public-checkpoint-notice" in attrs for _, attrs in after.tags) == 1
        assert sum("data-public-proof-library" in attrs for _, attrs in after.tags) == 1
        assert adapter.SERVICE_NOTE in payload.decode()
        assert not any("data-lean" in key for _, attrs in after.tags for key in attrs)
        prose = re.sub(r"<(script|pre|code)\b.*?</\1>", "", payload.decode(), flags=re.DOTALL)
        prose = re.sub(r"<[^>]*>", "", prose)
        assert "local-only" not in prose and "unpublished" not in prose, name
        assert "Local checkpoint" not in prose and "locally verified" not in prose, name


@pytest.mark.parametrize("slug", tuple(adapter.FAMILY_COUNTS))
def test_canonical_three_card_structure_and_dashboard_addon_are_unchanged(slug, files, local_files, drivers):
    shape = drivers["_landing_structure"]
    assert shape(files[slug + "/index.html"]) == shape(local_files[slug + "/index.html"])
    Document = drivers["Document"]
    before = Document(local_files[slug + "/explorer/defined/index.html"])
    after = Document(files[slug + "/explorer/defined/index.html"])
    assert [(attrs, source) for attrs, source in before.scripts if "data-local-dashboard-enhancement" in attrs] == [
        (attrs, source) for attrs, source in after.scripts if "data-local-dashboard-enhancement" in attrs]
    assert before.select_options == after.select_options


def test_exact_107_inherited_routes_and_every_public_html_target_exist(files, local_files, drivers):
    Document = drivers["Document"]
    documents = {adapter.PUBLIC_BASE + name: Document(payload) for name, payload in files.items() if name.endswith(".html")}
    routes = adapter.strict_json(files["historical-prerequisites.json"])["routes"]
    assert len(routes) == 107
    assert {name for name, row in routes.items() if not row["standalone_page"]} == adapter.NO_STANDALONE_PAGE
    assert sum(row["standalone_page"] for row in routes.values()) == 92
    external = {"/proofs/index.html": ROOT / "deploy/proofs/index.html",
                "/proofs/grand-campaign/index.html": ROOT / "book/_static/constructive-gaussian-campaign/index.html"}
    expected = {}
    for slug in adapter.FAMILY_COUNTS:
        corpus = adapter.strict_json(local_files[slug + "/api/corpus.json"])
        expected.update({row["name"]: row for row in corpus["external_dependencies"]})
    for name, row in routes.items():
        assert row["statement_sha256"] == expected[name]["statement_sha256"]
        if row["standalone_page"]:
            path = ROOT / row["source_page"]
            page = path.read_bytes()
            assert re.search(r"<h1[^>]*>" + re.escape(name) + r"</h1>", page.decode())
            assert expected[name]["statement"] in Document(page).codes, name
            external[row["public_path"]] = path
        else:
            assert row["note"].startswith("Inherited Alpha proof; no standalone historical explorer page")
    visited_external = set()
    for source, document in documents.items():
        for tag, attrs in document.tags:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                url = urlsplit(attrs[key])
                if url.scheme or url.netloc:
                    assert tag == "link" and attrs.get("rel") == "canonical"
                    assert attrs[key].startswith(adapter.ORIGIN + adapter.PUBLIC_BASE)
                    continue
                target = posixpath.normpath(posixpath.join(posixpath.dirname(source), unquote(url.path))) if url.path else source
                if url.path.endswith("/"):
                    target += "/index.html"
                if target.startswith(adapter.PUBLIC_BASE):
                    assert target[len(adapter.PUBLIC_BASE):] in files, (source, attrs[key], target)
                    if url.fragment:
                        assert unquote(url.fragment) in documents[target].ids, (source, attrs[key])
                else:
                    assert target in external and external[target].is_file(), (source, attrs[key], target)
                    assert not url.fragment
                    visited_external.add(target)
                if url.path and Path(url.path).suffix not in {".js", ".css"}:
                    assert parse_qs(url.query).get("v") == [adapter.REVISION], (source, attrs[key])
    assert set(row["public_path"] for row in routes.values() if row["standalone_page"]) <= visited_external
    assert "/proofs/grand-campaign/index.html" in visited_external
    assert "/proofs/index.html" in visited_external
    for slug in adapter.FAMILY_COUNTS:
        receipt = files[slug + "/checkpoint.html"].decode()
        for name in expected:
            if name in adapter.NO_STANDALONE_PAGE and 'id="theorem-' + name + '"' in receipt:
                assert "no standalone historical explorer page" in receipt


def test_actual_all_inline_scripts_and_exact_navigation(files, drivers):
    drivers["test_actual_html_scripts_all_compile_and_graph_payloads_equal_json_apis"](files)
    drivers["test_every_exact_page_prevents_the_original_asset_from_injecting_a_missing_graph_link"](files)


@pytest.mark.parametrize("slug", tuple(adapter.FAMILY_COUNTS))
@pytest.mark.parametrize("focus_kind", ("theorem", "definition"))
def test_actual_public_graph_runs_with_getter_only_svg_hrefs(slug, focus_kind, files, drivers):
    graph = adapter.strict_json(files[slug + "/api/graph.json"])
    target = graph["root_ids"][-1]
    focus = target if focus_kind == "theorem" else next(row["id"] for row in graph["nodes"] if row["kind"] == "definition")
    result = drivers["_graph_runtime"](graph, target, focus, complete_family=True, visible_definitions=True)
    assert result["svgHrefIsGetterOnly"] is result["allSvgHrefsAreGetterOnly"] is True
    assert result["viewportRendered"] is True
    assert result["selectedNodeIds"] == [focus]
    assert result["sidebarHref"] == next(row["href"] for row in graph["nodes"] if row["id"] == focus)


@pytest.mark.parametrize("slug", tuple(adapter.FAMILY_COUNTS))
def test_actual_public_graph_overlay_labels_theorems_not_definitions(slug, files, drivers):
    graph = adapter.strict_json(files[slug + "/api/graph.json"])
    document = drivers["Document"](files[slug + "/explorer/defined/graph.html"])
    source = next(source for attrs, source in document.scripts if "MutationObserver" in source)
    program = '''const vm=require("node:vm"),input=JSON.parse(require("node:fs").readFileSync(0,"utf8"));
const node=input.graph.nodes.find(row=>row.id===input.graph.root_ids.at(-1)),title={textContent:node.id+" · "+node.name},kind={textContent:"candidate"};
let callback;class MutationObserver{constructor(fn){callback=fn;}observe(target){if(target!==title)throw Error("wrong observer");}}
const document={querySelector(selector){return selector==="[data-graph-title]"?title:selector==="[data-graph-kind]"?kind:null;},addEventListener(event,fn){if(event!=="DOMContentLoaded")throw Error(event);fn();}};
vm.runInNewContext(input.source,{document,MutationObserver,window:{PA_DEFINED_GRAPH:input.graph}});
const theorem=kind.textContent;title.textContent=input.graph.nodes.find(x=>x.kind==="definition").id+" · definition";kind.textContent="Conservative definition";callback();
process.stdout.write(JSON.stringify({theorem,definition:kind.textContent}));'''
    completed = subprocess.run(["node", "-e", program], input=json.dumps({"source": source, "graph": graph}),
                               text=True, capture_output=True, check=True, timeout=20)
    assert json.loads(completed.stdout) == {"theorem": adapter.GRAPH_LABEL, "definition": "Conservative definition"}


@pytest.mark.parametrize("slug", tuple(adapter.FAMILY_COUNTS))
@pytest.mark.parametrize("ready,canonical_first", (("loading", True), ("complete", False)))
def test_actual_public_three_filters_and_proof_fragment_highlighting(slug, ready, canonical_first, files, corpora, drivers):
    family = next(row for row in builder._local_builder().FAMILIES if row.slug == slug)
    drivers["test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters"](
        family, ready, canonical_first, files, corpora)
    drivers["test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes"](family, files, corpora)


def test_euler_reserved_slots_and_root_tags_are_preserved(corpora, files):
    euler = corpora["euler-units"]
    assert euler["tags"]["euler_theorem_for_units"] == "EU0022"
    assert set(euler["reserved_tag_slots"]) == {"EU0003", "EU001C"}
    assert sha256(json.dumps(euler["tags"], sort_keys=True, separators=(",", ":")).encode()).hexdigest() == "5ce5feb11b98873f8eed312548e9bdbf8573fb5fe967da43746135a993762bd5"
    assert not any("/EU0003.html" in name or "/EU001C.html" in name for name in files)
    assert corpora["prime-fields"]["tags"]["prime_field_of_prime_order_exists"] == "FP0057"
    assert corpora["mobius-values"]["tags"]["mobius_fresh_prime_negates"] == "MV0015"
    assert corpora["signed-sums"]["tags"]["divisor_signed_sum_permutation_invariant"] == "SS001E"


@pytest.mark.parametrize("mutation", ("missing", "extra", "proof", "bundle", "receipt", "manifest"))
def test_changed_local_evidence_is_rejected_before_any_delivery_transform(mutation, local_files):
    bad = dict(local_files)
    if mutation == "missing":
        bad.pop("index.html")
    elif mutation == "extra":
        bad["surprise.html"] = b"x"
    else:
        name = {"proof": "euler-units/explorer/tag/EU0022.html",
                "bundle": "checkpoints/bottom-layer-euler-units-proof-bundle-v2.json",
                "receipt": "euler-units/api/checkpoint.json", "manifest": "manifest.json"}[mutation]
        bad[name] += b" "
    with pytest.raises(adapter.PublicCheckpointError):
        adapter.adapt_files(bad)


@pytest.mark.parametrize("flag", adapter.ADMISSION_FLAGS)
def test_public_corpus_rejects_any_new_admission_flag(flag, local_files):
    corpus = adapter.strict_json(local_files["euler-units/api/corpus.json"])
    corpus["nodes"][0][flag] = True
    with pytest.raises(adapter.PublicCheckpointError, match="cannot confer"):
        adapter.public_corpus(corpus, {})


def test_context_transform_never_rewrites_proof_code_or_unrelated_script():
    phrase = "Local checkpoint map"
    source = ('<!doctype html><html><head><title>' + phrase + '</title></head><body>'
              '<nav></nav><h1>' + phrase + '</h1><pre id="statement"><code>' + phrase + '</code></pre>'
              '<script>const value="' + phrase + '";</script><p>' + phrase + '</p></body></html>').encode()
    rendered = adapter.PublicHTML("index.html", {}).finish(source)
    assert b'<pre id="statement"><code>Local checkpoint map</code></pre>' in rendered
    assert b'<script>const value="Local checkpoint map";</script>' in rendered
    assert b"<title>Research checkpoint map</title>" in rendered
    assert b"<h1>Research checkpoint map</h1>" in rendered
    assert b"<p>Research checkpoint map</p>" in rendered


@pytest.mark.parametrize("mutation", ("duplicate", "nan", "graph", "unsafe_graph", "html", "duplicate_attribute"))
def test_malformed_json_or_html_fails_closed(mutation):
    if mutation in {"duplicate", "nan"}:
        with pytest.raises(adapter.PublicCheckpointError):
            adapter.strict_json('{"x":1,"x":2}' if mutation == "duplicate" else '{"x":NaN}')
        return
    graph = {"x": 1}
    actual = '{"x":2}' if mutation == "graph" else '{"x":1}'
    target = {"x": "</script>"} if mutation == "unsafe_graph" else graph
    source = ('<!doctype html><html><head></head><body><nav></nav><h1>Proof</h1>'
              '<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH=' + actual + ';</script></body></html>')
    if mutation == "html":
        source = source.replace("</h1>", "</h2>")
    if mutation == "duplicate_attribute":
        source = source.replace('<script id=', '<script id="duplicate" id=')
    with pytest.raises(adapter.PublicCheckpointError):
        adapter.PublicHTML("index.html", {}, target, graph).finish(source.encode())


def test_builder_really_calls_fresh_verifiers_before_adapter(monkeypatch):
    local = builder._local_builder()
    reached = []
    def reject():
        reached.append("real-build-entry")
        raise ValueError("proof checker rejected")
    monkeypatch.setattr(local, "build_files", reject)
    monkeypatch.setattr(adapter, "adapt_files", lambda *_: pytest.fail("delivery ran after failed proof check"))
    with pytest.raises(ValueError, match="proof checker rejected"):
        builder.build_files()
    assert reached == ["real-build-entry"]


@pytest.mark.parametrize("platform,peak", (("darwin", 1536 * 1024 * 1024 + 1), ("linux", 1536 * 1024 + 1)))
def test_original_rss_ceiling_refuses_before_success(platform, peak, monkeypatch):
    monkeypatch.setattr(builder.sys, "platform", platform)
    monkeypatch.setattr(builder.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=peak))
    with pytest.raises(RuntimeError, match="1536 MiB"):
        builder.authoring_rss_bytes()


def test_cli_installs_original_limits_and_never_writes_over_budget(monkeypatch):
    limits = []
    monkeypatch.setattr(builder.resource, "setrlimit", lambda key, value: limits.append((key, value)))
    monkeypatch.setattr(builder.signal, "alarm", lambda seconds: limits.append(("wall", seconds)))
    monkeypatch.setattr(builder, "build_files", lambda: {})
    monkeypatch.setattr(builder, "authoring_rss_bytes", lambda: (_ for _ in ()).throw(RuntimeError("over budget")))
    monkeypatch.setattr(builder, "write_or_check", lambda *_a, **_k: pytest.fail("over-budget output was written"))
    assert builder.main([]) == 1
    assert limits == [(builder.resource.RLIMIT_CPU, (170, 175)), ("wall", 180)]


def test_public_snapshot_manifest_authenticates_all_literal_bytes(files):
    manifest = adapter.strict_json(files["manifest.json"])
    assert manifest["schema"] == adapter.SCHEMA + "-manifest"
    assert manifest["publication_scope"] == adapter.SCOPE
    assert manifest["checkpoint_digest"] == adapter.LOCAL_CHECKPOINT_DIGEST
    assert manifest["file_count_excluding_manifest"] == len(files) - 1 == 494
    assert manifest["files"] == {name: {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}
                                 for name, payload in files.items() if name != "manifest.json"}


def test_public_html_has_no_trailing_whitespace(files):
    for name, payload in files.items():
        if name.endswith(".html"):
            assert not re.search(rb"[ \t]+\r?$", payload, re.MULTILINE), name


def test_head_whitespace_cleanup_preserves_whitespace_inside_protected_text():
    source = (b'<!doctype html><html><head>\n  \n  <meta name="robots" content="noindex">\n  \n'
              b'<script>const value="  ";\n  \n</script></head><body><nav></nav><h1>Proof</h1>'
              b'<pre><code>proof  \n  \n</code></pre></body></html>')
    rendered = adapter.PublicHTML("index.html", {}).finish(source)
    assert b'<script>const value="  ";\n  \n</script>' in rendered
    assert b'<pre><code>proof  \n  \n</code></pre>' in rendered
    assert b'<head>\n\n\n\n<script>' in rendered
    retained = (b'<!doctype html><html><head>\n  <meta charset="utf-8">\n  <title>Proof</title>'
                b'</head><body><nav></nav><h1>Proof</h1></body></html>')
    assert b'<head>\n  <meta charset="utf-8">\n  <title>Proof</title>' in adapter.PublicHTML("index.html", {}).finish(retained)
