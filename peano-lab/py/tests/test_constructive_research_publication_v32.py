"""Canonical v32 presentation checks, distinct from proof admission authority.

The release controller passes an actual same-live capability. Standalone tests
only observe installed files: no saved receipt can authorize new publication.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import posixpath
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_research_publication_v32 as publication
import constructive_historical_graph_test_support as graph_support
from tests.test_constructive_completed_lower_explorer_v31 import (
    FileTree, PublishedReleaseView, _observed_bytes, _readonly, drivers,
)

RESEARCH = tuple(item[0] for item in publication.RESEARCH)
COMPLETED = publication.publication.FAMILY_ORDER
HISTORICAL = publication.historical.FAMILY_ORDER


def _published_input(config, phase):
    """Read-only UI observations; deliberately not a live release object."""
    from peano_catalog_shards_v32 import load_catalog
    context = getattr(config, "_v32_ui_observations", None)
    if context is None:
        path = ROOT / "artifacts/peano-library/alpha/catalog-v32.json"
        catalog_hash = sha256(_observed_bytes(path)).hexdigest()
        catalog = load_catalog(path, expected_sha256=catalog_hash)
        channels = publication.strict_json(_observed_bytes(ROOT / "artifacts/peano-library/channels-v32.json"))
        assert catalog["theorem_count"] == catalog["checked_use_count"] == 3971
        assert catalog["stable_count"] == 432 and channels["default_channel"] == "stable"
        assert channels["channels"]["alpha"]["artifact_sha256"] == catalog_hash
        relative = "research/arithmetic-library/artifacts/alpha-v32-research-receipt-v1.json"
        pins = {row["path"]: row for row in catalog["evidence_documents"]}
        pin = pins[relative]
        receipt = publication.strict_json(publication.read_pinned(ROOT / relative, pin["bytes"], pin["sha256"]))
        assert receipt["new_theorems"] == 175 and receipt["ordinary_principal_count"] == 12
        families = {row["slug"]: row for row in receipt["families"]}
        assert tuple(families) == RESEARCH and len(receipt["families"]) == 2
        context = PublishedReleaseView(_readonly(catalog), _readonly(channels), _readonly(families),
            catalog_hash, catalog_hash[:12], tuple(row["name"] for row in catalog["theorems"][3796:]),
            receipt["source_binding_sha256"])
        config._v32_ui_observations = context
    assert type(context) is PublishedReleaseView and not hasattr(context, "require_unchanged")
    directory = ROOT / "book/_static" / publication.OUTPUT_NAMES[phase]
    if phase == "atlas":
        pins = {}
        for name in ("campaign.json", "definitions.json", "dag-audit.json", "index.html"):
            raw = _observed_bytes(directory / name)
            pins[name] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    else:
        raw = _observed_bytes(directory / "manifest.json")
        manifest = publication.strict_json(raw)
        assert manifest["catalog_sha256"] == context.catalog_sha256
        pins = dict(manifest["files"])
        assert "manifest.json" not in pins
        pins["manifest.json"] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    assert {path.relative_to(directory).as_posix() for path in directory.rglob("*") if path.is_file()} == set(pins)
    return {"phase": phase, "context": context, "directory": directory,
        "inventory": {"files": pins, "file_count": len(pins),
            "html_count": sum(name.endswith(".html") for name in pins),
            "total_bytes": sum(pin["bytes"] for pin in pins.values())},
        "mode": "static_ui_observations_only_no_new_proof_authority"}


def _input(config, phase):
    if not hasattr(config, "_alpha_v32_publication"):
        return _published_input(config, phase)
    value = config._alpha_v32_publication
    assert type(value) is dict and value.get("phase") == phase, "invalid live publication plugin"
    publication.require_live(value["context"])
    return value


@pytest.fixture(scope="module")
def runtime():
    return drivers()


@pytest.fixture(scope="module")
def research(pytestconfig):
    return _input(pytestconfig, "research")


@pytest.fixture(scope="module")
def completed(pytestconfig):
    return _input(pytestconfig, "completed")


@pytest.fixture(scope="module")
def historical(pytestconfig):
    return _input(pytestconfig, "historical")


@pytest.fixture(scope="module")
def atlas(pytestconfig):
    return _input(pytestconfig, "atlas")


def _files(actual):
    return FileTree(actual["directory"], actual["inventory"]["files"])


def _corpus(files, slug):
    return publication.strict_json(files[slug + "/api/corpus.json"])


def _manifest(actual, slugs):
    files, context = _files(actual), actual["context"]
    manifest = publication.strict_json(files["manifest.json"])
    assert manifest["phase"] == actual["phase"]
    assert tuple(row["slug"] for row in manifest["families"]) == slugs
    assert manifest["alpha_edition_version"] == "v32"
    assert manifest["alpha_edition_checked_use_count"] == 3971 and manifest["stable_edition_count"] == 432
    assert manifest["catalog_sha256"] == context.catalog_sha256 and manifest["html_revision"] == context.revision
    assert manifest["edition_identity_sha256"] == context.catalog["edition_identity_sha256"]
    assert manifest["release_source_binding_sha256"] == context.source_binding_sha256
    assert manifest["current_G009_multiplicative_closure_proved"] is True
    assert manifest["current_G091_prime_power_fields_proved"] is False
    assert manifest["files"] == {name: pin for name, pin in actual["inventory"]["files"].items() if name != "manifest.json"}
    if hasattr(context, "render_source_binding_sha256"):
        assert manifest["render_source_binding_sha256"] == context.render_source_binding_sha256
    assert manifest["file_count_excluding_manifest"] == len(files) - 1
    for name, expected in publication.ASSET_DIGESTS.items():
        assert sha256(files["assets/" + name]).hexdigest() == expected
    assert not any(path.is_symlink() for path in actual["directory"].rglob("*"))


def test_research_phase_inventory_and_authority(research):
    _manifest(research, RESEARCH)
    manifest = publication.strict_json(_files(research)["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 175
    assert manifest["stable_count"] == 0 and manifest["alpha_first_enrolled_version"] == "v32"


@pytest.mark.parametrize("slug", RESEARCH)
def test_research_phase_exact_proofs_definitions_routes(slug, research, runtime):
    from constructive_polynomial_division_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
    from constructive_formula_compactor import _LocalDefinedParser
    from peano_lab.kernel.formulas import parse_formula_with_names
    from build_constructive_completed_lower_explorer_v31 import _definition_and_statement_identity
    files, context = _files(research), research["context"]
    corpus, report = _corpus(files, slug), context.families[slug]
    rows = {row["name"]: row for row in context.catalog["theorems"]}
    snapshot = next(item[1:] for item in publication.RESEARCH if item[0] == slug)
    root, manifest = publication._snapshot(*snapshot)
    original = publication.strict_json(publication._source(root, manifest, slug + "/api/corpus.json"))
    _definition_and_statement_identity(original, corpus)
    assert corpus["historical_checkpoint_report"] == original["checkpoint_report"]
    assert corpus["first_alpha_admission_report"] == publication.strict_json(files[slug + "/api/checkpoint.json"]) == report
    bundle = report["bundle"]
    raw = files["artifacts/" + Path(bundle["path"]).name]
    assert len(raw) == bundle["bytes"] and sha256(raw).hexdigest() == bundle["sha256"]
    assert raw == (ROOT / bundle["path"]).read_bytes()
    assert bundle["original_ha_checked"] is bundle["independent_lean_checked"] is True
    assert bundle["kernel_calls"] == bundle["nodes_including_packaging_root"]
    assert len(report["principal_roots"]) == 6 and all(row["complete_ordinary_ha_checked"] is True for row in report["principal_roots"])
    for node in corpus["nodes"]:
        publication._check_literal_row(node, rows[node["name"]])
        assert node["checked_use"] is node["alpha_checked_use"] is node["admitted_to_alpha"] is True
        assert node["stable_member"] is node["admitted_to_stable"] is False
        assert node["alpha_edition_version"] == node["alpha_first_enrolled_version"] == "v32"
        assert node["proof_bundle_node_id"] == report["owned_node_ids"][node["name"]]
        parser = _LocalDefinedParser(node["defined"]["defined_statement"], ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME)
        assert parser.parse() == parse_formula_with_names(node["statement"])[0] and not parser.free
        for prefix in ("explorer/tag/", "explorer/defined/tag/"):
            doc = runtime["Document"](files[slug + "/" + prefix + node["id"] + ".html"])
            line_ids = [attrs["id"] for _, attrs in doc.tags if "pd-proof-line" in attrs.get("class", "").split() or "pa-proof-line" in attrs.get("class", "").split()]
            assert line_ids == [f"proof-line-{i:04d}" for i in range(1, len(node["script"]) + 1)]
            assert node["statement"] in doc.codes
    for definition in corpus["definitions"]:
        assert slug + "/explorer/defined/definition/" + definition["id"] + ".html" in files
    graph = publication.strict_json(files[slug + "/api/graph.json"])
    assert graph["edges"] == original["edges"] and graph["path_policy"] == "proof_dependency_edges_only"
    assert {edge["kind"] for edge in graph["edges"]} <= {"proof_dependency", "uses_definition", "definition_uses_definition"}
    assert graph["alpha_checked_use_node_count"] == len(corpus["nodes"])


def _dashboard(slug, actual, runtime, family):
    files = _files(actual)
    corpus = _corpus(files, slug)
    reference = ROOT / "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html"
    assert runtime["_landing_structure"](files[slug + "/index.html"]) == runtime["_landing_structure"](reference.read_bytes())
    runtime["test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters"](family, "loading", True, files, {slug: corpus})
    runtime["test_actual_canonical_dashboard_and_local_addon_combine_all_three_filters"](family, "complete", False, files, {slug: corpus})
    runtime["test_actual_defined_reader_highlights_initial_fragment_and_focuses_hash_changes"](family, files, {slug: corpus})


@pytest.mark.parametrize("slug", RESEARCH)
def test_research_phase_qr_dashboard(slug, research, runtime):
    _dashboard(slug, research, runtime, next(row for row in publication._family_models() if row.slug == slug))


@pytest.mark.parametrize("slug", RESEARCH)
def test_research_phase_actual_graph_views(slug, research):
    graph_support.assert_graph_views(publication.strict_json(_files(research)[slug + "/explorer/defined/api/graph.json"]))


def test_completed_phase_inventory_and_authority(completed):
    _manifest(completed, COMPLETED)
    manifest = publication.strict_json(_files(completed)["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 574
    assert manifest["alpha_first_enrolled_version"] == "v31"


def _preserved(slug, actual):
    files, context = _files(actual), actual["context"]
    root, manifest = publication._snapshot(*publication.OLDER[actual["phase"]])
    relative = slug + "/api/corpus.json"
    old = publication.strict_json(publication._source(root, manifest, relative))
    new = publication.strict_json(files[relative])
    assert len(publication.historical._nodes(new)) == len(publication.historical._nodes(old))
    for before, after in zip(publication.historical._nodes(old), publication.historical._nodes(new), strict=True):
        for key in (*publication._MATHEMATICAL_FIELDS, *publication._AUTHORITY_FIELDS):
            assert before.get(key) == after.get(key) and (key in before) == (key in after)
    for key in ("definitions", "edges", "tags", "layers", "proof_adjacency", "proof_paths", "first_alpha_admission_report", "historical_checkpoint_report"):
        assert old.get(key) == new.get(key) and (key in old) == (key in new)
    for key in publication._CURRENT_FIELDS & new.keys():
        assert new[key] == publication._current_metadata(context)[key]
    exact_tags=[name for name in manifest["files"] if name.startswith(slug+"/explorer/tag/") and name.endswith(".html")]
    assert exact_tags
    for name in exact_tags:
        assert name in files
        assert name.replace("/explorer/tag/","/explorer/defined/tag/",1) in files
    sidecar = slug + "/api/first-admission.json"
    if sidecar in manifest["files"]:
        assert files[sidecar] == publication._source(root, manifest, sidecar)
    if actual["phase"] == "completed":
        assert new["alpha_first_enrolled_version"] == "v31"
        assert new["alpha_first_enrollment_catalog_sha256"] == old["alpha_first_enrollment_catalog_sha256"]


@pytest.mark.parametrize("slug", COMPLETED)
def test_completed_phase_preserved_mathematics_and_first_admissions(slug, completed):
    _preserved(slug, completed)


@pytest.mark.parametrize("slug", COMPLETED)
def test_completed_phase_qr_dashboard(slug, completed, runtime):
    _dashboard(slug, completed, runtime, next(row for row in publication.publication.family_models() if row.slug == slug))


@pytest.mark.parametrize("slug", COMPLETED)
def test_completed_phase_actual_graph_views(slug, completed):
    graph_support.assert_graph_views(publication.strict_json(_files(completed)[slug + "/api/graph.json"]))


def test_historical_phase_inventory_and_authority(historical):
    _manifest(historical, HISTORICAL)
    manifest = publication.strict_json(_files(historical)["manifest.json"])
    assert manifest["theorem_count"] == 3096 and manifest["checked_use_count"] == 3007
    assert manifest["alpha_first_enrolled_version"] == "mixed_preserved"
    assert 3096 - 3007 == 89  # Historical, non-admitted aliases stay non-admitted.


@pytest.mark.parametrize("slug", HISTORICAL)
def test_historical_phase_preserved_mathematics_and_first_admissions(slug, historical):
    _preserved(slug, historical)


@pytest.mark.parametrize("slug", HISTORICAL)
def test_historical_phase_actual_graph_views(slug, historical):
    graph_support.assert_graph_views(publication.strict_json(_files(historical)[slug + "/api/graph.json"]))


def _javascript_and_navigation(actual, runtime, expected_graphs):
    """Compile actual unique scripts, match graph APIs and check public routes."""
    files = _files(actual)
    scripts, graphs = {}, 0
    routes = set(files)
    for directory, size, expected in (*publication.OLDER.values(), *(row[1:] for row in publication.RESEARCH)):
        _, manifest = publication._snapshot(directory, size, expected)
        routes.update(manifest["files"])
    routes.update(("index.html", "grand-campaign/index.html", "grand-campaign/campaign.json",
                   "grand-campaign/definitions.json", "grand-campaign/dag-audit.json"))
    for route in publication.LEGACY_DOCUMENTATION_ROUTES:
        assert _observed_bytes(ROOT / "deploy/proofs" / route)
        routes.add(route)
    for name in files:
        if not name.endswith(".html"):
            continue
        raw = files[name]
        document = runtime["Document"](raw)
        assert raw.count(b'name="proof-publication-scope"') == 1
        assert raw.count(b'data-current-release="v32"') <= 1
        assert b'data-current-release="v31"' not in raw
        assert any(attrs.get("rel") == "canonical" for _, attrs in document.tags)
        for attrs, source in document.scripts:
            if attrs.get("type", "").lower() in {"application/json", "application/ld+json"}:
                publication.strict_json(source)
            elif "src" not in attrs:
                scripts.setdefault(sha256(source.encode()).hexdigest(), {"name": name, "source": source})
            if attrs.get("id") in publication._HistoricalHTML.GRAPH_IDS:
                prefix = "window." + publication._HistoricalHTML.GRAPH_IDS[attrs["id"]] + "="
                assert source.startswith(prefix) and source.endswith(";")
                assert publication.strict_json(source[len(prefix):-1]) == publication.strict_json(files[name.replace("graph.html", "api/graph.json")])
                graphs += 1
        for tag, attrs in document.tags:
            if tag != "a" or not attrs.get("href"):
                continue
            link = urlsplit(attrs["href"])
            own = link.scheme == "https" and link.netloc == "bnaskrecki.faculty.wmi.amu.edu.pl" and link.path.startswith("/proofs/")
            if (link.scheme or link.netloc) and not own:
                continue
            if not link.path:
                continue
            if link.path.startswith("/") and not link.path.startswith("/proofs/"):
                # Existing course-book and lab links are other applications,
                # not files inside this proof-site publication namespace.
                assert link.path.startswith(("/peano-lab/", "/vietnam2026/book/"))
                continue
            target = unquote(link.path)
            target = target.removeprefix("/proofs/") if own or target.startswith("/proofs/") else posixpath.normpath(posixpath.join(posixpath.dirname(name), target))
            if target in {"", "."} or link.path.endswith("/"):
                target = ("" if target in {"", "."} else target + "/") + "index.html"
            assert target in routes, (name, attrs["href"], target)
            if target.endswith(".html"):
                assert parse_qs(link.query).get("v") == [actual["context"].revision], (name, attrs["href"])
    assert graphs == expected_graphs
    program = 'const vm=require("node:vm"),r=JSON.parse(require("node:fs").readFileSync(0,"utf8"));r.forEach(x=>new vm.Script(x.source,{filename:x.name}));process.stdout.write(String(r.length));'
    result = subprocess.run(["node", "-e", program], input=json.dumps(list(scripts.values())), text=True, capture_output=True, check=True, timeout=20)
    assert int(result.stdout) == len(scripts)


def test_research_phase_javascript_navigation(research, runtime):
    _javascript_and_navigation(research, runtime, 2)


def test_completed_phase_javascript_navigation(completed, runtime):
    _javascript_and_navigation(completed, runtime, 19)


def test_historical_phase_javascript_navigation(historical, runtime):
    _javascript_and_navigation(historical, runtime, 46)


def test_atlas_phase_exact_goals_definitions_and_current_evidence(atlas):
    from tests.test_constructive_research_campaign_v32 import _assert_published_files
    _assert_published_files(dict(_files(atlas)), atlas["context"])


@pytest.mark.parametrize("bad", (None, {}, SimpleNamespace(catalog={})))
def test_publication_rejects_non_authorizing_observations(bad):
    with pytest.raises(publication.PublicationError):
        publication.require_live(bad)
    with pytest.raises(publication.PublicationError):
        publication.bind_live_context(bad)
    with pytest.raises(AssertionError, match="invalid live publication plugin"):
        _input(SimpleNamespace(_alpha_v32_publication=bad), "research")


@pytest.mark.parametrize("change", ("duplicate_attr", "unbalanced", "missing_graph_peer", "malformed_graph", "foreign_canonical"))
def test_new_html_projection_rejects_malformed_context(change):
    raw = '<!doctype html><html><head></head><body><main></main></body></html>'
    if change == "duplicate_attr": raw = raw.replace("<main>", '<main id="a" id="b">')
    elif change == "unbalanced": raw = raw.replace("</main>", "</aside>")
    elif change in {"missing_graph_peer", "malformed_graph"}:
        body = 'window.PA_DEFINED_GRAPH={};' if change == "missing_graph_peer" else 'window.PA_DEFINED_GRAPH={};alert(1);'
        raw = raw.replace("</body>", '<script id="pa-defined-graph-data">' + body + '</script></body>')
    else: raw = raw.replace("</head>", '<link rel="canonical" href="https://foreign.invalid/">' + "</head>")
    with pytest.raises(publication.PublicationError):
        publication._HistoricalHTML("kummer/index.html", "a" * 12, graph={} if change == "malformed_graph" else None, portable_script="").finish(raw.encode())


def test_new_html_projection_preserves_protected_math_and_single_current_scope(runtime):
    raw = ('<!doctype html><html><head><meta name="proof-publication-scope" content="old"></head><body><main>'
           '<p data-current-release="v31">Current Alpha v31</p><pre><code>Alpha v31 checked-use</code></pre>'
           '<a href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/lucas/?v=old#goal">Open</a></main>'
           '<script>var protectedText="Alpha v31 checked-use </main>";</script></body></html>').encode()
    revised = publication._HistoricalHTML("kummer/index.html", "a" * 12, graph=None, portable_script="").finish(raw)
    assert revised.count(b'data-current-release="v32"') == revised.count(b'name="proof-publication-scope"') == 1
    assert "Alpha v31 checked-use" in runtime["Document"](revised).codes
    assert b'var protectedText="Alpha v31 checked-use </main>";' in revised
    assert b'/proofs/lucas/?v=aaaaaaaaaaaa#goal' in revised
