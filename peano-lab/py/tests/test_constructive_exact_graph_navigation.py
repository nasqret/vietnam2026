"""Presentation-only navigation regression; no proof or release authority.

The small inert corpus follows the actual v30 Gaussian corpus schema. Keeping
it local makes the historical byte checks independent of generated snapshots,
Git availability, catalogue loading, and proof-provider imports.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

import pytest


SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import constructive_frontier_exact_explorer as exact  # noqa: E402


ABSENT = object()
DEFAULT_REVISION = object()
REVISION = "012345abcdef"
MARKER = b" data-graph-navigation"
FAMILY = SimpleNamespace(
    slug="gaussian-factorization",
    title="Gaussian factorization",
    description="Signed-coordinate navigation — an inert rendering fixture.",
)
TAGS = {
    "fixture_seed": "GF0001",
    "fixture_middle": "GF0002",
    "fixture_root": "GF00B4",
}
LAYERS = {"fixture_seed": 0, "fixture_middle": 1, "fixture_root": 2}

# Full rendered-byte SHA-256 values from the original, unmodified helper
# (source SHA b250e268c2f0376768284963e8f44a2a2ac32fc1f4476015af45937cd2969baa).
# These are presentation snapshots, never evidence for theorem admission.
ORIGINAL_HTML_SHA256 = {
    ("index", "v27"): "3dbac0e73f931a38280e35ea9d67983abbc88fb533cd04381210766af5b9f556",
    ("index", "v28"): "ee82610850416a81d8ddc2499485aa69ad1b7ced98a616dbe77a5e8eaec1b6bf",
    ("index", "v29"): "569ab49c102910c17a40fd092cde08781c83469ff2839a8a1d56b40aae13f9a0",
    ("index", "absent"): "39a333924f148125e9bcc5edc9eda9b2cae0efd8a48029fd44bca830b28969a1",
    ("index", "v30"): "199c48e7091354d3f6232ecb2caa1770c463d966d84346c16d54a22beaefcada",
    ("theorem", "v27"): "a6bd0e4ae68bfe8b72f1b08a5bd3e6b57a119d9c228a00b1259a2f77a07d686c",
    ("theorem", "v28"): "1be1affc9b71c7a953259ee8fadfff66167cec958bdd5f7ba0b8bdf58ae8d1ac",
    ("theorem", "v29"): "2253183cb91159adbff2f009389d945584304b81f25ca41b4af1013509acca18",
    ("theorem", "absent"): "652280fd4edab4b2029d0da296f55875b0e7ce8c379f26dc05f595482d0bed47",
    ("theorem", "v30"): "027fe8a6df9fb8ab7514a4551555aac2345134d50a7a21f702b28bcfbc50b574",
}


def _corpus(version=ABSENT):
    rows = (
        ("fixture_seed", (), ("intro n", "refl")),
        (
            "fixture_middle",
            ("fixture_seed", "add_assoc"),
            ("intro n", "specialize fixture_seed (n)", "exact fixture_seed"),
        ),
        (
            "fixture_root",
            ("fixture_middle",),
            ("intro n", "specialize fixture_middle (n)", "exact fixture_middle"),
        ),
    )
    nodes = []
    for name, dependencies, script in rows:
        statement = "forall n. n=n"
        node = {
            "name": name,
            "summary": f"{name}: exact <coordinate> & dependency navigation.",
            "dependencies": list(dependencies),
            "script": list(script),
            "statement": statement,
            "statement_sha256": sha256(statement.encode()).hexdigest(),
            "enrolled_in_alpha": True,
            "alpha_checked_use": True,
            "alpha_evidence": "alpha_closed",
            "sources": [
                {
                    "selected": True,
                    "source_module": "navigation_fixture_only",
                    "factory": "make_navigation_fixture_only",
                    "script_sha256": sha256("\n".join(script).encode()).hexdigest(),
                }
            ],
        }
        if version is not ABSENT:
            node["alpha_edition_version"] = version
        nodes.append(node)
    corpus = {
        "campaign_family_id": "F09",
        "candidate_status": "Rendering fixture only; not proof admission evidence.",
        "nodes": nodes,
        # The index must select the last root; a theorem must use its own tag.
        "root_names": ["fixture_seed", "fixture_root"],
        "edge_count": 3,
        "formal_line_count": 8,
        "external_dependencies": [{"name": "add_assoc", "admitted_to_stable": True}],
    }
    if version is not ABSENT:
        corpus["alpha_edition_version"] = version
    return corpus


def _render(page, corpus, revision=REVISION):
    prefix = "../../" if page == "index" else "../../../"
    kwargs = {
        "stylesheet_href": f"{prefix}assets/explorer.css?v=style-fixture",
        "script_href": f"{prefix}assets/explorer.js?v=script-fixture",
    }
    if revision is not DEFAULT_REVISION:
        kwargs["html_revision"] = revision
    if page == "index":
        return exact.render_exact_index(FAMILY, corpus, TAGS, LAYERS, **kwargs)
    return exact.render_exact_theorem(
        FAMILY, corpus, corpus["nodes"][1], TAGS, LAYERS, **kwargs
    )


class _Navigation(HTMLParser):
    def __init__(self, rendered):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.elements = []
        self.current_anchor = None
        self.header_depth = 0
        self.nav_depth = 0
        self.feed(rendered.decode("utf-8"))
        self.close()

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        self.elements.append((tag, attributes))
        if tag == "header":
            self.header_depth += 1
        if tag == "nav":
            self.nav_depth += 1
        if tag == "a":
            self.current_anchor = SimpleNamespace(
                attributes=attributes,
                text="",
                in_header_nav=bool(self.header_depth and self.nav_depth),
            )
            self.anchors.append(self.current_anchor)

    def handle_endtag(self, tag):
        if tag == "a":
            self.current_anchor = None
        if tag == "header":
            self.header_depth -= 1
        if tag == "nav":
            self.nav_depth -= 1

    def handle_data(self, data):
        if self.current_anchor is not None:
            self.current_anchor.text += data


@pytest.mark.parametrize("page", ("index", "theorem"))
@pytest.mark.parametrize(
    "revision", (REVISION, "", 'fixture"revision', DEFAULT_REVISION),
    ids=("explicit", "unversioned", "escaped", "historical-default"),
)
def test_v30_marks_only_the_existing_correct_header_graph_link(page, revision):
    rendered = _render(page, _corpus("v30"), revision)
    document = _Navigation(rendered)
    marked = [a for a in document.anchors if "data-graph-navigation" in a.attributes]
    assert len(marked) == rendered.count(MARKER) == 1
    graph = marked[0]
    assert graph.in_header_nav
    assert graph.text == "Dependency graph"
    assert [a for a in document.anchors if a.text == "Dependency graph"] == marked
    target = "GF00B4" if page == "index" else "GF0002"
    expected_path = "defined/graph.html" if page == "index" else "../defined/graph.html"
    expected_revision = exact.HTML_REVISION if revision is DEFAULT_REVISION else revision
    expected_query = {"target": [target]}
    if expected_revision:
        expected_query["v"] = [expected_revision]
    href = urlsplit(graph.attributes["href"])
    assert (href.scheme, href.netloc, href.path, href.fragment) == ("", "", expected_path, "")
    assert parse_qs(href.query) == expected_query
    assert set(graph.attributes) == {"href", "data-graph-navigation"}
    assert graph.attributes["data-graph-navigation"] is None
    # No unversioned, nonexistent exact-graph destination is introduced.
    assert not any(
        urlsplit(a.attributes.get("href", "")).path in {"graph.html", "../graph.html"}
        for a in document.anchors
    )
    body = next(attrs for tag, attrs in document.elements if tag == "body")
    assert body["data-page"] == page
    assert body["data-family"] == "gaussian-factorization"
    prefix = "../../" if page == "index" else "../../../"
    script = next(attrs for tag, attrs in document.elements if tag == "script")
    stylesheet = next(attrs for tag, attrs in document.elements if tag == "link")
    assert script["src"] == f"{prefix}assets/explorer.js?v=script-fixture"
    assert stylesheet["href"] == f"{prefix}assets/explorer.css?v=style-fixture"


@pytest.mark.parametrize("page", ("index", "theorem"))
@pytest.mark.parametrize("version", ("v27", "v28", "v29", ABSENT), ids=("v27", "v28", "v29", "absent"))
def test_prior_and_unversioned_html_is_byte_identical_to_original(page, version):
    rendered = _render(page, _corpus(version))
    key = "absent" if version is ABSENT else version
    assert MARKER not in rendered
    assert sha256(rendered).hexdigest() == ORIGINAL_HTML_SHA256[(page, key)]


@pytest.mark.parametrize("page", ("index", "theorem"))
def test_v30_differs_from_original_html_by_the_single_marker_only(page):
    rendered = _render(page, _corpus("v30"))
    assert rendered.count(MARKER) == 1
    original = rendered.replace(MARKER, b"", 1)
    assert sha256(original).hexdigest() == ORIGINAL_HTML_SHA256[(page, "v30")]


@pytest.mark.parametrize("page", ("index", "theorem"))
@pytest.mark.parametrize(
    "version", (ABSENT, None, "", "v29", "v31", "V30", "v30 ", "30", 30, False),
    ids=("absent", "null", "empty", "prior", "future", "case", "space", "numeric-string", "integer", "false"),
)
def test_only_exact_corpus_v30_enables_marker_not_node_metadata(page, version):
    corpus = _corpus("v30")
    del corpus["alpha_edition_version"]
    original = _render(page, corpus)
    if version is not ABSENT:
        corpus["alpha_edition_version"] = version
    rendered = _render(page, corpus)
    assert MARKER not in rendered
    assert rendered == original


@pytest.mark.parametrize("page", ("index", "theorem"))
@pytest.mark.parametrize(
    "enrolled,checked,node_version",
    ((True, True, "v28"), (True, False, "v29"), (False, False, None)),
    ids=("historical-node", "body-only", "not-enrolled"),
)
def test_navigation_marker_does_not_change_or_depend_on_proof_authority(
    page, enrolled, checked, node_version
):
    corpus = _corpus("v30")
    for node in corpus["nodes"]:
        node.update(
            enrolled_in_alpha=enrolled,
            alpha_checked_use=checked,
            alpha_edition_version=node_version,
            alpha_evidence="alpha_closed" if checked else "body_checked",
        )
    rendered = _render(page, corpus)
    corpus["alpha_edition_version"] = "v29"
    historical = _render(page, corpus)
    assert rendered.count(MARKER) == 1
    assert rendered.replace(MARKER, b"", 1) == historical
    assert b"Stable" in rendered
    if not checked:
        assert b"no checked-use authority" in rendered


@pytest.mark.parametrize("page", ("index", "theorem"))
@pytest.mark.parametrize("version", ("v30", "v29", ABSENT), ids=("current", "historical", "absent"))
def test_navigation_rendering_does_not_mutate_inputs(page, version):
    corpus = _corpus(version)
    before = deepcopy(corpus)
    tags_before, layers_before = dict(TAGS), dict(LAYERS)
    _render(page, corpus)
    assert corpus == before
    assert TAGS == tags_before
    assert LAYERS == layers_before
