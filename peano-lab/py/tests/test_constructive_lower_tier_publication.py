"""Fresh proof gates, literal preservation and real canonical-JS public tests."""

from hashlib import sha256
import json
from pathlib import Path
import posixpath
import re
import sys
from urllib.parse import parse_qs, unquote, urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_constructive_lower_tier_publication as builder
import constructive_lower_tier_publication_adapter as adapter
import test_constructive_lower_tier_explorer as source_tests


@pytest.fixture(scope="module")
def drivers():
    return source_tests._drivers()


@pytest.fixture(scope="module")
def local_files():
    output = ROOT / "book/_static/constructive-lower-tier-explorer"
    result = {path.relative_to(output).as_posix(): path.read_bytes()
              for path in output.rglob("*") if path.is_file()}
    adapter.validate_local_files(result)
    return result


@pytest.fixture(scope="module")
def files(local_files):
    # Positive checks really execute both original HA and the pinned compiled
    # Lean binary. A stored receipt or monkeypatched verifier cannot supply it.
    result = builder.build_files()
    builder.write_or_check(result, check=True)
    output = builder._local_builder().OUTPUT
    assert {path.relative_to(output).as_posix(): path.read_bytes()
            for path in output.rglob("*") if path.is_file()} == local_files
    return result


@pytest.fixture(scope="module")
def corpora(files):
    return {slug: adapter.strict_json(files[slug + "/api/corpus.json"]) for slug in adapter.FAMILY_COUNTS}


@pytest.fixture(scope="module")
def families():
    return {family.slug: family for family in builder._local_builder().families()}


def test_publication_is_exactly_126_new_proofs_not_an_alpha_release(files):
    inventory = adapter.strict_json(files["checkpoints.json"])
    assert len(files) == 373
    assert inventory["schema"] == adapter.SCHEMA
    assert inventory["publication_scope"] == adapter.SCOPE
    assert inventory["public_base_path"] == "/proofs/checkpoints/lower-tier/"
    assert inventory["new_theorem_count"] == 126
    assert inventory["previous_research_theorems"] == 170
    assert inventory["inherited_support_counted_as_new"] is False
    assert inventory["alpha_admission_performed"] is inventory["stable_admission_performed"] is False
    assert inventory["on_demand_alpha_lean_service_exposes_frontier"] is False
    assert inventory["parent"]["alpha_checked_use_count"] == 3222
    assert inventory["parent"]["stable_count"] == 432
    assert inventory["checkpoint_digest"] == adapter.LOCAL_CHECKPOINT_DIGEST
    assert "published" not in inventory


@pytest.mark.parametrize("slug", adapter.FAMILY_COUNTS)
def test_exact_proofs_tactics_definitions_roles_and_paths_are_unchanged(slug, files, local_files):
    old = adapter.strict_json(local_files[slug + "/api/corpus.json"])
    new = adapter.strict_json(files[slug + "/api/corpus.json"])
    changed = {"schema", "publication_scope", "candidate_status", "nodes", "external_dependencies",
               "external_theorem_routes", "external_route_boundary", "on_demand_alpha_lean_service_exposes_frontier"}
    assert {k: v for k, v in old.items() if k not in changed} == {k: v for k, v in new.items() if k not in changed}
    for before, after in zip(old["nodes"], new["nodes"], strict=True):
        assert before | {"status": adapter.STATUS} == after
        assert all(after[flag] is False for flag in adapter.ADMISSION_FLAGS)
    for before, after in zip(old["external_dependencies"], new["external_dependencies"], strict=True):
        assert before | {"reference_route": new["external_theorem_routes"][before["name"]]} == after
        assert after["counted_as_new_owned_theorem"] is False
        assert after["alpha_checked_use"] == (after["inventory_role"] == adapter.ALPHA_ROLE)
    graph = adapter.strict_json(files[slug + "/api/graph.json"])
    assert adapter.strict_json(local_files[slug + "/api/graph.json"]) | {
        "schema": adapter.SCHEMA + "-graph", "publication_scope": adapter.SCOPE} == graph
    assert files[slug + "/api/graph.json"] == files[slug + "/explorer/defined/api/graph.json"]
    assert {edge["kind"] for edge in graph["edges"]} == {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["path_policy"] == "proof_dependency_edges_only"


def test_all_sources_bundles_assets_and_historical_receipts_are_literal(files, local_files):
    for name, payload in local_files.items():
        if name.startswith(("assets/", "sources/", "checkpoints/")) or name.endswith("/api/checkpoint.json"):
            assert files[name] == payload, name
    assert files["receipts/local-checkpoints.json"] == local_files["checkpoints.json"]
    assert adapter.strict_json(files["receipts/local-checkpoints.json"])["published"] is False


def test_every_html_preserves_protected_math_and_has_truthful_public_metadata(files, local_files, drivers):
    Document = drivers["Document"]
    pages = {name: payload for name, payload in files.items() if name.endswith(".html")}
    assert len(pages) == 338
    for name, payload in pages.items():
        before, after = Document(local_files[name]), Document(payload)
        assert before.codes == after.codes, name
        assert re.findall(rb"<pre\b.*?</pre>", local_files[name], re.DOTALL) == re.findall(rb"<pre\b.*?</pre>", payload, re.DOTALL), name
        assert before.ids == after.ids and len(after.ids) == len(set(after.ids))
        canonical = adapter.ORIGIN + adapter.PUBLIC_BASE + name.removesuffix("index.html")
        assert [attrs["href"] for tag, attrs in after.tags if tag == "link" and attrs.get("rel") == "canonical"] == [canonical]
        assert [attrs["content"] for _, attrs in after.tags if attrs.get("property") == "og:url"] == [canonical]
        assert [attrs["content"] for _, attrs in after.tags if attrs.get("name") == "proof-publication-scope"] == [adapter.SCOPE]
        assert not any(attrs.get("name") == "robots" for _, attrs in after.tags)
        assert sum("data-public-checkpoint-notice" in attrs for _, attrs in after.tags) == 1
        assert sum("data-public-proof-library" in attrs for _, attrs in after.tags) == 1
        assert not any("data-lean" in key for _, attrs in after.tags for key in attrs)
        prose = re.sub(r"<(script|pre|code)\b.*?</\1>", "", payload.decode(), flags=re.DOTALL)
        prose = re.sub(r"<[^>]*>", "", prose)
        assert not any(word in prose for word in ("Local checkpoint", "local-only", "new local theorems", "local development")), name
        assert not re.search(rb"[ \t]+\r?$", payload, re.MULTILINE), name


@pytest.mark.parametrize("slug", adapter.FAMILY_COUNTS)
def test_canonical_qr_landings_match_frozen_model(slug, files, local_files, drivers):
    shape = drivers["_landing_structure"]
    assert shape(files[slug + "/index.html"]) == shape(local_files[slug + "/index.html"])
    actual = shape(files[slug + "/index.html"])
    reference = shape((ROOT / "deploy/proofs/quadratic-reciprocity.html").read_bytes())
    # Identical hero, navigation, actions and three cards. Research proofs add
    # two explicit evidence/scope notes to the original two release notes.
    assert [item for item in actual if "release-note" not in item[1]] == [
        item for item in reference if "release-note" not in item[1]]
    assert sum("release-note" in classes for _, classes in actual) == 4


def test_all_public_links_fragments_and_exact_inherited_routes_resolve(files, local_files, drivers):
    Document = drivers["Document"]
    documents = {adapter.PUBLIC_BASE + name: Document(payload) for name, payload in files.items() if name.endswith(".html")}
    routes = adapter.strict_json(files["historical-prerequisites.json"])["routes"]
    assert len(routes) == 84
    assert sum(row["standalone_page"] for row in routes.values()) == 72
    wanted = {row["name"]: row for slug in adapter.FAMILY_COUNTS
              for row in adapter.strict_json(local_files[slug + "/api/corpus.json"])["external_dependencies"]}
    assert set(routes) == set(wanted)
    assert {row["inventory_role"] for row in routes.values()} == {adapter.ALPHA_ROLE, adapter.PREVIOUS_ROLE, adapter.CROSS_ROLE}
    external = {"/proofs/index.html": ROOT / "deploy/proofs/index.html",
                "/proofs/grand-campaign/index.html": ROOT / "book/_static/constructive-gaussian-campaign/index.html",
                "/proofs/checkpoints/index.html": ROOT / "book/_static/constructive-bottom-layer-publication/index.html"}
    for name, route in routes.items():
        assert route["statement_sha256"] == wanted[name]["statement_sha256"]
        assert route["inventory_role"] == wanted[name]["inventory_role"]
        if route["standalone_page"]:
            path = ROOT / route["source_page"]
            assert wanted[name]["statement"] in Document(path.read_bytes()).codes, name
            external[route["public_path"]] = path
        else:
            assert route["inventory_role"] == adapter.ALPHA_ROLE
    for source, document in documents.items():
        for tag, attrs in document.tags:
            for key in ("href", "src"):
                if key not in attrs:
                    continue
                url = urlsplit(attrs[key])
                if url.scheme or url.netloc:
                    assert tag == "link" and attrs.get("rel") == "canonical"
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
                if url.path and Path(url.path).suffix not in {".js", ".css"}:
                    assert parse_qs(url.query).get("v") == [adapter.REVISION], (source, attrs[key])


def test_actual_inline_javascript_and_129_exact_reader_navigation_cases(files, corpora, drivers):
    source_tests.test_every_inline_script_parses_and_graph_payload_matches_its_api(files, drivers)
    source_tests.test_actual_exact_graph_navigation_never_injects_a_missing_link(files, corpora, drivers)


@pytest.mark.parametrize("slug", adapter.FAMILY_COUNTS)
@pytest.mark.parametrize("focus_kind", ("theorem", "definition"))
def test_actual_graphs_with_getter_only_svg_href(slug, focus_kind, files, drivers):
    source_tests.test_actual_canonical_mixed_graph_with_getter_only_svg_hrefs(slug, focus_kind, files, drivers)


@pytest.mark.parametrize("slug", adapter.FAMILY_COUNTS)
@pytest.mark.parametrize("ready", ("loading", "complete"))
@pytest.mark.parametrize("canonical_first", (False, True))
def test_actual_dashboard_filters_and_reader_hashes(slug, ready, canonical_first, files, corpora, families, drivers):
    source_tests.test_actual_three_filters_and_hash_highlighting(slug, ready, canonical_first, files, corpora, families, drivers)


@pytest.mark.parametrize("query,visible", (("", tuple(adapter.FAMILY_COUNTS)),
    ("?view=goal&focus=G007", ("divisor-sums", "signed-weighted-sums")),
    ("?view=goal&focus=G091", ("prime-field-polynomials",)),
    ("?view=unknown&focus=G007", tuple(adapter.FAMILY_COUNTS))))
def test_actual_public_dispatch(query, visible, files, drivers):
    source_tests.test_actual_dispatch_respects_only_known_scales(query, visible, files, drivers)


@pytest.mark.parametrize("mutation", ("missing", "extra", "proof", "bundle", "receipt", "manifest"))
def test_changed_local_evidence_is_refused(mutation, local_files):
    bad = dict(local_files)
    if mutation == "missing":
        bad.pop("index.html")
    elif mutation == "extra":
        bad["surprise.html"] = b"x"
    else:
        name = {"proof": "divisor-sums/explorer/tag/DV0022.html",
                "bundle": "checkpoints/lower-tier-divisor-sums-proof-bundle-v1.json",
                "receipt": "divisor-sums/api/checkpoint.json", "manifest": "manifest.json"}[mutation]
        bad[name] += b" "
    with pytest.raises(adapter.PublicCheckpointError):
        adapter.adapt_files(bad)


@pytest.mark.parametrize("flag", adapter.ADMISSION_FLAGS)
def test_presentation_cannot_promote_owned_theorem(flag, local_files):
    corpus = adapter.strict_json(local_files["divisor-sums/api/corpus.json"])
    corpus["nodes"][0][flag] = True
    with pytest.raises(adapter.PublicCheckpointError, match="cannot confer"):
        adapter.public_corpus(corpus, {})


@pytest.mark.parametrize("mutation", ("statement", "role"))
def test_same_name_cannot_link_a_different_theorem_or_admission_role(mutation, local_files):
    corpora = {slug: adapter.strict_json(local_files[slug + "/api/corpus.json"]) for slug in adapter.FAMILY_COUNTS}
    for corpus in corpora.values():
        for row in corpus["external_dependencies"]:
            if row["name"] == "divisor_signed_table_lookup":
                row["statement" if mutation == "statement" else "inventory_role"] = "false theorem or role"
    with pytest.raises(adapter.PublicCheckpointError):
        adapter.inherited_routes(corpora)


def test_context_transform_protects_proof_script_and_head_whitespace():
    source = (b'<!doctype html><html><head>\n  <meta name="robots" content="noindex">\n  \n'
              b'<script>const value="Local checkpoint map";\n  \n</script></head>'
              b'<body><nav></nav><h1>Local checkpoint map</h1>'
              b'<pre><code>Local checkpoint map  \n  \n</code></pre></body></html>')
    rendered = adapter.PublicHTML("index.html", {}).finish(source)
    assert b'<script>const value="Local checkpoint map";\n  \n</script>' in rendered
    assert b'<pre><code>Local checkpoint map  \n  \n</code></pre>' in rendered
    assert b'<h1>Research checkpoint map</h1>' in rendered


@pytest.mark.parametrize("mutation", ("duplicate", "nan", "graph", "unsafe_graph", "html", "duplicate_attribute"))
def test_malformed_delivery_data_fails_closed(mutation):
    if mutation in {"duplicate", "nan"}:
        with pytest.raises(adapter.PublicCheckpointError):
            adapter.strict_json('{"x":1,"x":2}' if mutation == "duplicate" else '{"x":NaN}')
        return
    original = {"x": 1}
    actual = '{"x":2}' if mutation == "graph" else '{"x":1}'
    graph = {"x": "</script>"} if mutation == "unsafe_graph" else original
    source = ('<!doctype html><html><head></head><body><nav></nav><h1>Proof</h1>'
              '<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH=' + actual + ';</script></body></html>')
    if mutation == "html":
        source = source.replace("</h1>", "</h2>")
    if mutation == "duplicate_attribute":
        source = source.replace('<script id=', '<script id="duplicate" id=')
    with pytest.raises(adapter.PublicCheckpointError):
        adapter.PublicHTML("index.html", {}, graph, original).finish(source.encode())


def test_failed_real_proof_check_never_reaches_public_adapter(monkeypatch):
    def reject():
        raise ValueError("actual proof check rejected")
    monkeypatch.setattr(builder._local_builder(), "build_files", reject)
    monkeypatch.setattr(adapter, "adapt_files", lambda *_: pytest.fail("rendered rejected proof"))
    with pytest.raises(ValueError, match="proof check rejected"):
        builder.build_files()


def test_original_resource_limits_and_no_write_over_budget(monkeypatch):
    limits = []
    monkeypatch.setattr(builder.resource, "setrlimit", lambda key, value: limits.append((key, value)))
    monkeypatch.setattr(builder.signal, "alarm", lambda value: limits.append(("wall", value)))
    monkeypatch.setattr(builder, "build_files", lambda: {})
    monkeypatch.setattr(builder, "authoring_rss_bytes", lambda: (_ for _ in ()).throw(RuntimeError("over budget")))
    monkeypatch.setattr(builder, "write_or_check", lambda *_a, **_k: pytest.fail("over-budget write"))
    assert builder.main([]) == 1
    assert limits == [(builder.resource.RLIMIT_CPU, (170, 175)), ("wall", 180)]


def test_manifest_authenticates_all_public_bytes(files):
    manifest = adapter.strict_json(files["manifest.json"])
    assert manifest["file_count_excluding_manifest"] == len(files) - 1 == 372
    assert manifest["checkpoint_digest"] == adapter.LOCAL_CHECKPOINT_DIGEST
    assert manifest["files"] == {name: {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}
                                 for name, payload in files.items() if name != "manifest.json"}
