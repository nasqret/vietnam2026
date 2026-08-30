"""Exact historical identities, hostile projections and same-live old44 UI.

Source-only tests grant no authority. During publication, the genuine live v31
child supplies fresh pages. Ordinary pytest uses the explicitly non-authorizing
PublishedReleaseView for static checks of actual generated files, not new proofs.
"""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import posixpath
import subprocess
import sys
from urllib.parse import urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_completed_lower_publication_v31 as publication
import upgrade_constructive_historical_publication_v31 as historical
from tests.test_constructive_completed_lower_explorer_v31 import FileTree, drivers, live_input


@pytest.fixture(scope="module")
def metadata():
    return historical.family_metadata()


@pytest.fixture(scope="module")
def source_rows(pytestconfig):
    supplied = getattr(pytestconfig, "_alpha_v31_publication", None)
    if hasattr(pytestconfig, "_alpha_v31_publication"):
        assert type(supplied) is dict, "an invalid live plugin cannot use static observations"
        return {row["name"]: row for row in supplied["context"].catalog["theorems"]}
    # Read real immutable data for conditional projection diagnostics only.
    raw = publication.read_pinned(ROOT / "artifacts/peano-library/alpha/catalog-v30.json", 66503303,
                                  publication.PARENT_CATALOG_SHA256)
    return {row["name"]: row for row in publication.strict_json(raw)["theorems"]}


def _source(slug):
    item = next(row for row in historical.SNAPSHOTS if not row.defined and slug in row.slugs)
    manifest = historical.source_manifest(item)
    pins = {row["path"]: row for row in manifest["files"]}
    corpus = publication.strict_json(historical.source_file(item, pins, historical._corpus_path(item, slug)))
    return item, manifest, pins, corpus


def test_exact_pinned_44_readers_distinguish_visible_and_admitted_counts(metadata):
    assert tuple(row["slug"] for row in metadata) == historical.FAMILY_ORDER
    assert len(metadata) == 44
    assert sum(row["theorem_count"] for row in metadata) == 3096
    assert sum(row["checked_use_count"] for row in metadata) == 3007
    assert 3096 - 3007 == 89
    assert len(historical.manifests()) == 15
    for version, expected in historical.FIRST_CATALOGS.items():
        assert sha256((ROOT / "artifacts/peano-library/alpha" / ("catalog-" + version + ".json")).read_bytes()).hexdigest() == expected


@pytest.mark.parametrize("slug", historical.FAMILY_ORDER)
def test_exact_original_first_records_and_compact_sidecar_pins(slug, metadata):
    item, manifest, pins, corpus = _source(slug)
    family = next(row for row in metadata if row["slug"] == slug)
    tags = historical._tags(item, slug, corpus, pins)
    records = historical.first_admission_records(item, slug, manifest, corpus, tags)
    descriptor = family["first_admission"]
    raw = publication.json_bytes(records)
    assert descriptor == historical.first_admission_descriptor(item, slug, manifest, corpus, tags)
    assert descriptor["per_theorem_records"] == {"path": slug + "/api/first-admission.json", "bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    assert family["first_admission_sha256"] == sha256(historical.canonical_bytes(descriptor)).hexdigest()
    assert Counter(row["recorded_first_version"] for row in records["per_theorem"]) == descriptor["recorded_first_version_counts"]
    assert [row["name"] for row in records["per_theorem"]] == [row["name"] for row in historical._nodes(corpus)]
    if slug in {"quadratic-reciprocity", "bertrand-postulate"}:
        assert set(descriptor["recorded_first_version_counts"]) == {"not_recorded"}
        assert descriptor["source_manifest_fields"]["proof_edition_version"] == ("v16" if slug == "quadratic-reciprocity" else "v18")
        assert not descriptor["catalog_sha256_by_recorded_version"]


@pytest.mark.parametrize("slug,count", (("kummer", 2), ("supplementary-laws", 2), ("two-squares", 26), ("four-squares", 39), ("lucas", 20)))
def test_source_only_projection_never_upgrades_real_nonadmitted_aliases(slug, count, source_rows, metadata):
    _, _, _, corpus = _source(slug)
    values = {key: "syntax-only-unissued" for key in historical._CURRENT_FIELDS}
    projected = historical._refresh_document(corpus, source_rows, values)
    aliases = [node for node in corpus["nodes"] if node.get("alpha_checked_use") is not True]
    assert len(aliases) == count
    after = {row["name"]: row for row in projected["nodes"]}
    for old in aliases:
        new = after[old["name"]]
        assert {key: new[key] for key in historical._AUTHORITY_FIELDS if key in new} == {key: old[key] for key in historical._AUTHORITY_FIELDS if key in old}
        assert new["alpha_checked_use"] is False
        assert new["statement"] == old["statement"] and new["script"] == old["script"]
    routes = historical.theorem_routes(metadata)
    for node in aliases:
        if not any(node["name"] in family["checked_names"] for family in metadata):
            assert node["name"] not in routes


@pytest.mark.parametrize("change", ("missing", "checked", "body", "statement", "statement_sha", "stable"))
def test_actual_old_checked_row_requires_exact_current_catalogue_evidence(change, source_rows):
    _, _, _, corpus = _source("polynomial-horner")
    name = corpus["nodes"][0]["name"]
    rows = dict(source_rows)
    row = deepcopy(rows[name])
    if change == "missing": rows.pop(name)
    elif change == "checked": row["checked_use"] = False
    elif change == "body": row["body_checked"] = False
    elif change == "statement": row["statement"] = "0=1"
    elif change == "statement_sha": row["statement_sha256"] = "0" * 64
    else: row["membership"] = "stable"
    if change != "missing": rows[name] = row
    with pytest.raises(publication.PublicationError):
        historical._refresh_document(corpus, rows, {key: "syntax-only-unissued" for key in historical._CURRENT_FIELDS})


def test_historical_canonical_name_alias_still_targets_its_real_tag():
    raw = (ROOT / "book/_static/pa-proof-explorer/name/zero_add.html").read_bytes()
    rendered = historical._HistoricalHTML("quadratic-reciprocity/explorer/name/zero_add.html", "a" * 12,
                                          graph=None, portable_script="").finish(raw).decode()
    assert 'rel="canonical" href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/quadratic-reciprocity/explorer/tag/PA0001.html"' in rendered
    assert 'location.replace("../tag/PA0001.html"+location.search+location.hash)' in rendered
    assert 'href="../tag/PA0001.html?v=aaaaaaaaaaaa"' in rendered


def test_typed_graph_projection_preserves_protected_data_and_real_main_boundary():
    graph = {"nodes": [{"summary": 'Alpha v30 checked-use </main> <a x="quoted">'}], "edges": []}
    raw = ('<!doctype html><html><head></head><body><main><pre><code>Alpha v30 checked-use &lt;/main&gt;</code></pre></main>'
           '<script id="pa-defined-graph-data">window.PA_DEFINED_GRAPH={"nodes":[],"edges":[]};</script>'
           '<script>var protectedText="Alpha v30 checked-use </main>";</script></body></html>').encode()
    rendered = historical._HistoricalHTML("kummer/explorer/defined/graph.html", "a" * 12, graph=graph, portable_script="").finish(raw)
    document = drivers()["Document"](rendered)
    assert "Alpha v30 checked-use </main>" in document.codes
    assert 'var protectedText="Alpha v30 checked-use </main>";' in rendered.decode()
    source = next(body for attrs, body in document.scripts if attrs.get("id") == "pa-defined-graph-data")
    assert publication.strict_json(source[len("window.PA_DEFINED_GRAPH="):-1]) == graph
    assert "\\u003c/main>" in source
    assert rendered.count(b'data-current-release="v31"') == 1


@pytest.mark.parametrize("change", ("duplicate_attr", "unbalanced", "missing_graph_peer", "malformed_graph", "foreign_canonical"))
def test_html_context_faults_fail_closed(change):
    raw = '<!doctype html><html><head></head><body><main></main></body></html>'
    if change == "duplicate_attr": raw = raw.replace("<main>", '<main id="a" id="b">')
    elif change == "unbalanced": raw = raw.replace("</main>", "</aside>")
    elif change in {"missing_graph_peer", "malformed_graph"}:
        body = 'window.PA_DEFINED_GRAPH={};' if change == "missing_graph_peer" else 'window.PA_DEFINED_GRAPH={};alert(1);'
        raw = raw.replace("</body>", '<script id="pa-defined-graph-data">' + body + '</script></body>')
    else: raw = raw.replace("</head>", '<link rel="canonical" href="https://foreign.invalid/">' + "</head>")
    with pytest.raises(publication.PublicationError):
        historical._HistoricalHTML("kummer/index.html", "a" * 12, graph={} if change == "malformed_graph" else None, portable_script="").finish(raw.encode())


def test_only_current_graph_schema_constraint_changes_not_proof_edition():
    path = ROOT / "book/_static/pa-proof-explorer/api/graph.schema.json"
    before = publication.strict_json(path.read_bytes())
    after = historical._refresh_graph_schema(before)
    assert before["properties"]["alpha_edition_version"]["const"] == "v25"
    assert after["properties"]["alpha_edition_version"]["const"] == "v31"
    assert after["properties"]["proof_edition_version"] == before["properties"]["proof_edition_version"]
    assert after["additionalProperties"] is False


@pytest.fixture(scope="module")
def actual(pytestconfig):
    return live_input(pytestconfig, "historical")


@pytest.fixture(scope="module")
def files(actual):
    return FileTree(actual["directory"], actual["inventory"]["files"])


def test_live_manifest_stays_bounded_and_authenticates_all44_exact_sidecars(files, metadata, actual):
    raw = files["manifest.json"]
    assert len(raw) <= 2 * 1024 * 1024
    manifest = publication.strict_json(raw)
    assert raw == historical.canonical_bytes(manifest) + b"\n"
    assert manifest["schema"] == historical.SCHEMA
    assert manifest["alpha_edition_version"] == "v31" and manifest["alpha_first_enrolled_version"] == "mixed_preserved"
    assert "first_enrollment_catalog_sha256" not in manifest
    assert manifest["catalog_sha256"] == actual["context"].catalog_sha256
    assert manifest["families"] == [historical._manifest_family(row) for row in metadata]
    assert manifest["files"] == {name: actual["inventory"]["files"][name] for name in files if name != "manifest.json"}
    for family in manifest["families"]:
        sidecar = family["first_admission"]["per_theorem_records"]
        payload = files[sidecar["path"]]
        assert len(payload) == sidecar["bytes"] and sha256(payload).hexdigest() == sidecar["sha256"]
        assert len(publication.strict_json(payload)["per_theorem"]) == family["theorem_count"]


@pytest.mark.parametrize("slug", historical.FAMILY_ORDER)
def test_live_all_historical_theorem_first_and_source_records_remain_literal(slug, files, actual, metadata):
    item, _, _, original = _source(slug)
    after = publication.strict_json(files[slug + "/api/corpus.json"])
    expected = historical._refresh_document(original, {row["name"]: row for row in actual["context"].catalog["theorems"]},
                                            historical._current_metadata(actual["context"]))
    assert after == expected
    assert after["schema"] == original["schema"]
    for before, now in zip(historical._nodes(original), historical._nodes(after), strict=True):
        for field in (*historical._MATHEMATICAL_FIELDS, *historical._AUTHORITY_FIELDS):
            assert before.get(field) == now.get(field) and (field in before) == (field in now)
    assert after.get("definitions") == original.get("definitions")
    family = next(row for row in metadata if row["slug"] == slug)
    for tag in family["tags"].values():
        assert slug + "/explorer/tag/" + tag + ".html" in files
        assert slug + "/explorer/defined/tag/" + tag + ".html" in files


@pytest.mark.parametrize("slug", historical.FAMILY_ORDER)
def test_live_all44_actual_mixed_graphs_keep_getter_only_svg_hrefs(slug, files):
    graph = publication.strict_json(files[slug + "/api/graph.json"])
    theorem = next(row["id"] for row in reversed(graph["nodes"]) if row["kind"] == "theorem")
    definition = next(row["id"] for row in graph["nodes"] if row["kind"] == "definition")
    actual = drivers()["_graph_runtime"](graph, theorem, definition, complete_family=True, visible_definitions=True)
    assert actual["svgHrefIsGetterOnly"] is actual["allSvgHrefsAreGetterOnly"] is actual["viewportRendered"] is True
    assert actual["selectedNodeIds"] == [definition]
    assert {row["id"] for row in graph["nodes"] if row["kind"] == "theorem"} <= set(actual["renderedNodeIds"])


def test_live_all_actual_inline_javascript_and_graph_api_pairs(files):
    Document = drivers()["Document"]
    scripts, graph_count = {}, 0
    for name in files:
        if not name.endswith(".html"):
            continue
        for attrs, source in Document(files[name]).scripts:
            if attrs.get("type", "").lower() in {"application/json", "application/ld+json"}:
                publication.strict_json(source)
            elif "src" not in attrs:
                scripts.setdefault(sha256(source.encode()).hexdigest(), {"name": name, "source": source})
            if attrs.get("id") in historical._HistoricalHTML.GRAPH_IDS:
                prefix = "window." + historical._HistoricalHTML.GRAPH_IDS[attrs["id"]] + "="
                assert source.startswith(prefix) and source.endswith(";")
                assert publication.strict_json(source[len(prefix):-1]) == publication.strict_json(files[name.replace("graph.html", "api/graph.json")])
                graph_count += 1
    assert graph_count == 46  # two exact flagship maps plus forty-four mixed maps.
    program = 'const vm=require("node:vm"),r=JSON.parse(require("node:fs").readFileSync(0,"utf8"));r.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(r.length));'
    result = subprocess.run(["node", "-e", program], input=json.dumps(list(scripts.values())), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(scripts)


def test_live_original_alpha_v21_prerequisite_summaries_and_all_frozen_inputs_unchanged(files):
    _, _, _, old = _source("euclidean-gcd-transport")
    for name in ("euclidean_execution_output_unique", "euclidean_execution_terminal_identified"):
        node = next(row for row in old["nodes"] if row["name"] == name)
        assert "Alpha-v21" in node["summary"]
        tag = old["tags"][name]
        for relative in ("explorer/index.html", "explorer/defined/index.html", "explorer/tag/" + tag + ".html", "explorer/defined/tag/" + tag + ".html"):
            assert node["summary"] in files["euclidean-gcd-transport/" + relative].decode()
    manifest = publication.strict_json(files["manifest.json"])
    assert historical.authenticate_inputs(historical.manifests()) == manifest["historical_input_binding_sha256"]
