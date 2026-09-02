"""Canonical v34 presentation checks, distinct from proof admission authority.

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
from collections import Counter
from dataclasses import fields, is_dataclass
from html import unescape
from html.parser import HTMLParser
import re

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_research_publication_v34 as publication
import constructive_historical_graph_test_support as graph_support
import build_constructive_gcd_congruence_explorer_v34 as builder
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names
ALL = builder.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
from tests.test_constructive_completed_lower_explorer_v31 import (
    FileTree, PublishedReleaseView, _observed_bytes, _readonly, drivers,
)

POLYNOMIAL = ("polynomial-euclidean-division",)
GCD_CONGRUENCE = ("polynomial-gcd-bezout", "congruence-arithmetic")
RESEARCH = publication.RESEARCH_SLUGS
COMPLETED = publication.publication.FAMILY_ORDER
HISTORICAL = publication.historical.FAMILY_ORDER


def _published_input(config, phase):
    """Read-only UI observations; deliberately not a live release object."""
    from peano_catalog_shards_v34 import load_catalog
    context = getattr(config, "_v34_ui_observations", None)
    if context is None:
        path = ROOT / "artifacts/peano-library/alpha/catalog-v34.json"
        catalog_hash = sha256(_observed_bytes(path)).hexdigest()
        catalog = load_catalog(path, expected_sha256=catalog_hash)
        channels = publication.strict_json(_observed_bytes(ROOT / "artifacts/peano-library/channels-v34.json"))
        assert catalog["theorem_count"] == catalog["checked_use_count"] == 4223
        assert catalog["stable_count"] == 432 and channels["default_channel"] == "stable"
        assert channels["channels"]["alpha"]["artifact_sha256"] == catalog_hash
        relative = "research/arithmetic-library/artifacts/alpha-v34-research-receipt-v1.json"
        pins = {row["path"]: row for row in catalog["evidence_documents"]}
        pin = pins[relative]
        receipt = publication.strict_json(publication.read_pinned(ROOT / relative, pin["bytes"], pin["sha256"]))
        assert receipt["new_theorems"] == 131 and receipt["ordinary_principal_count"] == 19
        families = {row["slug"]: row for row in receipt["families"]}
        assert tuple(families) == GCD_CONGRUENCE and len(receipt["families"]) == 2
        context = PublishedReleaseView(_readonly(catalog), _readonly(channels), _readonly(families),
            catalog_hash, catalog_hash[:12], tuple(row["name"] for row in catalog["theorems"][4092:]),
            receipt["source_binding_sha256"])
        config._v34_ui_observations = context
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
    if not hasattr(config, "_alpha_v34_publication"):
        return _published_input(config, phase)
    value = config._alpha_v34_publication
    assert type(value) is dict and value.get("phase") == phase, "invalid live publication plugin"
    publication.require_live(value["context"])
    return value


@pytest.fixture(scope="module")
def runtime():
    return drivers()


@pytest.fixture(scope="module")
def gcd_congruence(pytestconfig):
    return _input(pytestconfig, "gcd-congruence")


@pytest.fixture(scope="module")
def polynomial(pytestconfig):
    return _input(pytestconfig, "polynomial")


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
    assert manifest["alpha_edition_version"] == "v34"
    assert manifest["alpha_edition_checked_use_count"] == 4223 and manifest["stable_edition_count"] == 432
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
def test_research_phase_preserved_mathematics_and_first_admissions(slug, research):
    _preserved(slug, research)
    corpus = _corpus(_files(research), slug)
    assert corpus["alpha_first_enrolled_version"] == "v32"
    assert corpus["first_alpha_admission_report"]["slug"] == slug


def _dashboard(slug, actual, runtime, family, *, files=None):
    files = _files(actual) if files is None else files
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


def _javascript_and_navigation(actual, runtime, expected_graphs, *, files=None):
    """Compile actual unique scripts, match graph APIs and check public routes."""
    files = _files(actual) if files is None else files
    scripts, graphs = {}, 0
    routes = set(files)
    for directory, size, expected in publication.OLDER.values():
        _, manifest = publication._snapshot(directory, size, expected)
        routes.update(manifest["files"])
    routes.update(publication._routes().values())
    for family in publication._new_family_metadata():
        slug = family["slug"]
        routes.update(slug + "/" + name for name in ("index.html", "checkpoint.html", "explorer/index.html",
            "explorer/defined/index.html", "explorer/defined/graph.html"))
        routes.update(slug + "/explorer/tag/" + tag + ".html" for tag in family["tags"].values())
        routes.update(slug + "/explorer/defined/definition/" + row.stable_id + ".html" for row in ALL.values())
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
        assert raw.count(b'data-current-release="v34"') <= 1
        assert b'data-current-release="v31"' not in raw
        assert b'data-current-release="v32"' not in raw
        assert b'data-current-release="v33"' not in raw
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


def test_polynomial_phase_inventory_and_authority(polynomial):
    _manifest(polynomial, POLYNOMIAL)
    manifest = publication.strict_json(_files(polynomial)["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 121
    assert manifest["stable_count"] == 0 and manifest["alpha_first_enrolled_version"] == "v33"


def test_polynomial_phase_exact_proofs_definitions_routes(polynomial):
    # The complete old121 mathematical/first-admission payload stays literal;
    # only current authority/navigation is projected to the new release.
    _preserved(POLYNOMIAL[0], polynomial)
    _exact_family_content(polynomial, POLYNOMIAL[0], first_version="v33")


def test_polynomial_phase_qr_dashboard(polynomial, runtime):
    from build_constructive_polynomial_euclidean_explorer_v33 import family
    _dashboard(POLYNOMIAL[0], polynomial, runtime, family())


def test_polynomial_phase_actual_graph_views(polynomial):
    graph_support.assert_graph_views(publication.strict_json(
        _files(polynomial)[POLYNOMIAL[0] + "/api/graph.json"]))


def test_polynomial_phase_javascript_navigation(polynomial, runtime):
    _javascript_and_navigation(polynomial, runtime, 1)


def test_atlas_phase_exact_goals_definitions_and_current_evidence(atlas):
    from tests.test_constructive_research_campaign_v34 import _assert_published_content
    if not isinstance(atlas["context"], PublishedReleaseView):
        publication.require_live(atlas["context"])
    _assert_published_content(atlas["context"], dict(_files(atlas)))


@pytest.mark.parametrize("bad", (None, {}, SimpleNamespace(catalog={})))
def test_publication_rejects_non_authorizing_observations(bad):
    with pytest.raises(publication.PublicationError):
        publication.require_live(bad)
    with pytest.raises(publication.PublicationError):
        publication.bind_live_context(bad)
    with pytest.raises(AssertionError, match="invalid live publication plugin"):
        _input(SimpleNamespace(_alpha_v34_publication=bad), "research")


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
    assert revised.count(b'data-current-release="v34"') == revised.count(b'name="proof-publication-scope"') == 1
    assert "Alpha v31 checked-use" in runtime["Document"](revised).codes
    assert b'var protectedText="Alpha v31 checked-use </main>";' in revised
    assert b'/proofs/lucas/?v=aaaaaaaaaaaa#goal' in revised


def _same_ast(left, right):
    pending, seen = [(left, right)], set()
    while pending:
        a, b = pending.pop()
        assert type(a) is type(b)
        if (id(a), id(b)) in seen:
            continue
        seen.add((id(a), id(b)))
        if is_dataclass(a):
            pending.extend((getattr(a, field.name), getattr(b, field.name)) for field in fields(a))
        else:
            assert a == b


def _parse_defined(source, names=()):
    parser = _LocalDefinedParser(source, ALL)
    parser.free = list(names)
    formula = parser.parse()
    assert tuple(parser.free) == tuple(names)
    return formula


def _assert_reading(spec, reading):
    assert reading["exact_ast_equivalence"] is True
    explicit, names = parse_formula_with_names(spec.statement)
    assert not names and not reading["free_names"]
    _same_ast(_parse_defined(reading["defined_statement"]), explicit)
    assert reading["defined_statement"] == "".join(part["text"] for part in reading["statement_parts"])
    assert len(reading["script_parts"]) == len(reading["defined_script"]) == len(spec.script)
    assert Counter(part["definition"] for part in reading["statement_parts"] if part["kind"] == "definition") == reading["statement_definition_uses"]
    uses = Counter()
    for command, compact, parts in zip(spec.script, reading["defined_script"], reading["script_parts"], strict=True):
        assert compact == "".join(part["text"] for part in parts)
        uses.update(part["definition"] for part in parts if part["kind"] == "definition")
        if command.startswith(("have ", "suffices ")):
            original_head, original_formula = command.split(":", 1)
            shown_head, shown_formula = compact.split(":", 1)
            assert original_head.strip() == shown_head.strip()
            formula, free = parse_formula_with_names(original_formula.strip())
            _same_ast(_parse_defined(shown_formula.strip(), free), formula)
        else:
            assert compact == command and parts == [{"kind": "text", "text": command}]
    assert dict(sorted(uses.items())) == reading["script_definition_uses"]
    assert dict(sorted((uses + Counter(reading["statement_definition_uses"])).items())) == reading["definition_uses"]


class _Page(HTMLParser):
    """Small independent literal-code observer, not a proof interpreter."""
    def __init__(self, raw):
        super().__init__(convert_charrefs=True)
        self.tags, self.ids, self.lines, self.stack = [], set(), {}, []
        self.current_line = None
        self.feed(raw.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        assert len(values) == len(attrs)
        self.tags.append((tag, values))
        if "id" in values:
            assert values["id"] not in self.ids
            self.ids.add(values["id"])
        if tag == "li" and "data-line" in values:
            assert self.current_line is None
            self.current_line = int(values["data-line"])
            assert self.current_line not in self.lines
            self.lines[self.current_line] = []
        if tag not in {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        assert self.stack and self.stack[-1] == tag
        self.stack.pop()
        if tag == "li" and self.current_line is not None:
            self.current_line = None

    def handle_data(self, data):
        if self.current_line is not None and "code" in self.stack:
            self.lines[self.current_line].append(data)



def _exact_family_content(actual, slug, *, first_version, files=None):
    """Independently inspect actual formula ASTs, scripts, pages and typed edges."""
    files, context = _files(actual) if files is None else files, actual["context"]
    corpus = _corpus(files, slug)
    graph = publication.strict_json(files[slug + "/api/graph.json"])
    assert files[slug + "/api/graph.json"] == files[slug + "/explorer/defined/api/graph.json"]
    catalog = {row["name"]: row for row in context.catalog["theorems"]}
    tags = corpus["tags"]
    assert len(tags) == len(set(tags.values())) == len(corpus["nodes"])
    assert corpus["alpha_first_enrolled_version"] == first_version
    assert corpus["alpha_edition_version"] == "v34"
    definitions = {row["id"]: row for row in corpus["definitions"]}
    assert len(definitions) == len(corpus["definitions"]) == corpus["definition_count"]
    for node in corpus["nodes"]:
        row = catalog[node["name"]]
        spec = SimpleNamespace(statement=row["statement"], script=tuple(row["script"]))
        assert node["id"] == tags[node["name"]]
        for field in ("statement", "script", "dependencies", "summary", "statement_sha256", "script_sha256"):
            assert node[field] == row[field]
        assert node["alpha_first_enrolled_version"] == first_version
        assert node["alpha_edition_version"] == "v34"
        assert node["checked_use"] is node["alpha_checked_use"] is node["admitted_to_alpha"] is True
        assert node["stable_member"] is node["admitted_to_stable"] is False
        assert node["statement_sha256"] == sha256(spec.statement.encode()).hexdigest()
        assert node["script_sha256"] == sha256(("\n".join(spec.script) + "\n").encode()).hexdigest()
        _assert_reading(spec, node["defined"])
        for prefix, commands in (("explorer/tag/", spec.script), ("explorer/defined/tag/", node["defined"]["defined_script"])):
            raw = files[slug + "/" + prefix + node["id"] + ".html"]
            page = _Page(raw)
            assert tuple(page.lines) == tuple(range(1, len(commands) + 1))
            assert ["".join(page.lines[index]) for index in page.lines] == list(commands)
            assert {f"proof-line-{index:04d}" for index in page.lines} <= page.ids
            pattern = (r'<details class="pd-expanded">.*?<pre><code>(.*?)</code></pre>'
                       if "defined/" in prefix else r'<pre id="statement"><code>(.*?)</code></pre>')
            assert unescape(re.search(pattern, raw.decode(), re.S).group(1)) == spec.statement
    seen = set()
    for row in corpus["definitions"]:
        expected = ALL[row["name"]]
        assert row["id"] == expected.stable_id
        assert row["parameters"] == list(expected.parameters) and row["arity"] == expected.arity
        assert row["expanded_template"] == expected.template_source
        assert row["expansion_sha256"] == sha256(expected.template_source.encode()).hexdigest()
        assert row["dependency_names"] == list(expected.conceptual_dependencies)
        assert row["dependencies"] == [ALL[name].stable_id for name in expected.conceptual_dependencies]
        assert set(row["dependencies"]) <= seen
        _same_ast(_parse_defined(row["defined_template"], expected.parameters), expected.template_formula)
        assert row["exact_ast_verified"] is row["kernel_signature_unchanged"] is True
        assert slug + "/explorer/defined/definition/" + row["id"] + ".html" in files
        seen.add(row["id"])
    assert corpus["definition_topological_order"] == list(definitions)
    proof = [{"kind": "proof_dependency", "source": tags[parent], "target": node["id"]}
             for node in corpus["nodes"] for parent in node["dependencies"] if parent in tags]
    uses = [{"kind": "uses_definition", "source": node["id"], "target": identifier,
             "occurrence_count": count,
             "statement_occurrences": node["defined"]["statement_definition_uses"].get(identifier, 0),
             "local_proposition_occurrences": node["defined"]["script_definition_uses"].get(identifier, 0)}
            for node in corpus["nodes"] for identifier, count in node["defined"]["definition_uses"].items()]
    notation = [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                for row in corpus["definitions"] for parent in row["dependencies"]]
    assert corpus["edges"] == graph["edges"] == proof + uses + notation
    assert corpus["path_policy"] == graph["path_policy"] == "proof_dependency_edges_only"
    assert {row["id"] for row in graph["nodes"]} == set(tags.values()) | definitions.keys()
    assert graph["root_ids"] == [tags[name] for name in corpus["root_names"]]
    edges = {(row["source"], row["target"]) for row in proof}
    for name, adjacency in corpus["proof_adjacency"].items():
        assert adjacency["dependencies"] == [parent for parent in catalog[name]["dependencies"] if parent in tags]
        assert adjacency["dependents"] == [node["name"] for node in corpus["nodes"] if name in node["dependencies"]]
        path = adjacency["critical_root_path"]
        assert path and path[-1] == tags[name] and set(path) <= set(tags.values())
        assert all(pair in edges for pair in zip(path, path[1:]))
    checkpoint = _Page(files[slug + "/checkpoint.html"])
    for row in corpus["external_dependencies"]:
        actual_row = catalog[row["name"]]
        assert row["name"] not in tags
        assert row["counted_as_new_owned_theorem"] is row["first_admission_reclassified"] is False
        for key in ("statement", "script", "dependencies", "source"):
            assert row[key] == actual_row[key]
        assert "theorem-" + row["name"] in checkpoint.ids


def test_gcd_congruence_phase_inventory_and_authority(gcd_congruence):
    _manifest(gcd_congruence, GCD_CONGRUENCE)
    files, context = _files(gcd_congruence), gcd_congruence["context"]
    manifest = publication.strict_json(files["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == manifest["new_theorem_count"] == 131
    assert manifest["stable_count"] == 0 and manifest["alpha_first_enrolled_version"] == "v34"
    assert manifest["ordinary_principal_count"] == 19
    # The installed-only view uses read-only container subclasses. Materialize
    # literal content for strict private data checks; this object deliberately
    # has neither a live token nor require_unchanged and cannot publish.
    content = context
    if isinstance(context, PublishedReleaseView):
        content = SimpleNamespace(catalog=deepcopy(dict(context.catalog)),
            channels=deepcopy(dict(context.channels)), families=deepcopy(dict(context.families)),
            catalog_sha256=context.catalog_sha256, revision=context.revision,
            promoted_names=context.promoted_names, source_binding_sha256=context.source_binding_sha256,
            observation_only=True)
    builder._assert_published_content(dict(files), content)


@pytest.mark.parametrize("slug", GCD_CONGRUENCE)
def test_gcd_congruence_phase_exact_proofs_definitions_routes(slug, gcd_congruence):
    files, context = _files(gcd_congruence), gcd_congruence["context"]
    _exact_family_content(gcd_congruence, slug, first_version="v34")
    corpus = _corpus(files, slug)
    report = context.families[slug]
    assert corpus["checkpoint_report"] == corpus["first_alpha_admission_report"] == report
    assert publication.strict_json(files[slug + "/api/checkpoint.json"]) == report
    actual_rows = [row for row in context.catalog["theorems"] if row["name"] in corpus["tags"]]
    assert publication.strict_json(files[slug + "/api/first-admission.json"]) == actual_rows
    record = builder.registration(slug)
    assert tuple(row["name"] for row in report["principal_roots"]) == record.principal_roots
    assert len(report["principal_roots"]) == (14 if slug == GCD_CONGRUENCE[0] else 5)
    assert all(row["complete_ordinary_ha_checked"] is True and type(row["ordinary_certificate_nodes"]) is int
               and row["ordinary_certificate_nodes"] > 0 for row in report["principal_roots"])
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert corpus["tags"] == builder.family_metadata(slug)["tags"]
    assert len(corpus["nodes"]) == (119 if slug == GCD_CONGRUENCE[0] else 12)
    for node, measured in zip(corpus["nodes"], report["rows"], strict=True):
        assert node["name"] == measured["name"]
        assert node["proof_bundle_node_id"] == report["owned_node_ids"][node["name"]] == measured["node_id"]
        assert node["body_proof_nodes"] == measured["proof_nodes"] and node["body_proof_depth"] == measured["proof_depth"]
    bundle = files["artifacts/" + Path(record.artifact).name]
    assert len(bundle) == record.artifact_bytes and sha256(bundle).hexdigest() == record.artifact_sha256
    for module, _, size, digest in builder.factories(slug):
        raw = files["sources/" + module + ".py"]
        assert len(raw) == size and sha256(raw).hexdigest() == digest
    assert corpus["current_G091_prime_power_fields_proved"] is False


@pytest.mark.parametrize("slug", GCD_CONGRUENCE)
def test_gcd_congruence_phase_qr_dashboard(slug, gcd_congruence, runtime):
    _dashboard(slug, gcd_congruence, runtime, builder.family(slug))


@pytest.mark.parametrize("slug", GCD_CONGRUENCE)
def test_gcd_congruence_phase_actual_graph_views(slug, gcd_congruence):
    graph_support.assert_graph_views(publication.strict_json(_files(gcd_congruence)[slug + "/api/graph.json"]))


def test_gcd_congruence_phase_javascript_navigation(gcd_congruence, runtime):
    _javascript_and_navigation(gcd_congruence, runtime, 2)
