"""Deterministic contracts for the generated native-PA Proof Explorer."""

from __future__ import annotations

from collections import Counter
from dataclasses import fields
from hashlib import sha256
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import parse_qs, unquote, urljoin, urlsplit


REPO = Path(__file__).resolve().parents[3]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(REPO / "scripts"))
EXPLORER = REPO / "book" / "_static" / "pa-proof-explorer"
MANIFEST = EXPLORER / "manifest.json"
IMMUTABLE_EVIDENCE_CORPUS = EXPLORER / "api" / "corpus.json"
CORPUS = EXPLORER / "api" / "current-corpus.json"
IMMUTABLE_EVIDENCE_CORPUS_SHA256 = (
    "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
)
IMMUTABLE_EVIDENCE_CORPUS_BYTES = 17_229_311
GRAPH = EXPLORER / "api" / "graph.json"
GRAPH_SCHEMA = EXPLORER / "api" / "graph.schema.json"
TAGS = REPO / "research" / "arithmetic-library" / "pa-proof-tags.json"
INFORMAL = REPO / "research" / "arithmetic-library" / "pa-proof-informal.json"
GENERATOR = REPO / "scripts" / "build_pa_proof_explorer.py"

THEOREM_COUNT = 557
EDGE_COUNT = 1_787
LAYER_COUNT = 45
FORMAL_LINE_COUNT = 27_491
PUBLIC_COUNT = 241
CANDIDATE_COUNT = 316
EXPLICIT_EDGE_COUNT = 1_780
IMPLICIT_EDGE_COUNT = 7
EXPLICIT_REFERENCE_COUNT = 8_553
TAG_PATTERN = re.compile(r"^PA[0-9A-Y]{4}$")
ID_PATTERN = re.compile(r'\bid="([^"]+)"')


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict), path
    return value


def _records() -> list[dict]:
    rows = _load(CORPUS).get("theorems")
    assert isinstance(rows, list)
    assert all(isinstance(row, dict) for row in rows)
    return rows


def _metric(manifest: dict, *names: str) -> int:
    counts = manifest.get("counts", {})
    assert isinstance(counts, dict)
    for name in names:
        value = manifest.get(name, counts.get(name))
        if type(value) is int:
            return value
    raise AssertionError(f"manifest is missing integer metric {names!r}")


def _tag(item: object) -> str:
    if isinstance(item, str):
        return item
    assert isinstance(item, dict)
    value = item.get("tag") or item.get("target_tag")
    assert isinstance(value, str)
    return value


def _name(item: object) -> str:
    if isinstance(item, str):
        return item
    assert isinstance(item, dict)
    value = item.get("name") or item.get("target_name")
    assert isinstance(value, str)
    return value


def _href(item: dict) -> str:
    value = item.get("href")
    assert isinstance(value, str) and value
    return value


def _resolve(page: Path, raw: str) -> tuple[Path, str]:
    parsed = urlsplit(raw)
    assert not parsed.scheme and not parsed.netloc
    assert not raw.startswith(("/", "//"))
    path_text = unquote(parsed.path)
    target = page if not path_text else (page.parent / path_text).resolve()
    target.relative_to(EXPLORER.resolve())
    assert target.is_file(), (page, raw)
    return target, unquote(parsed.fragment)


class _Assets(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.assets: list[tuple[str, str]] = []
        self.links: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if attributes.get("href"):
            self.links.append(attributes["href"])
        if tag == "link" and attributes.get("href"):
            self.assets.append((tag, attributes["href"]))
        elif tag in {"audio", "embed", "iframe", "img", "object", "script", "source", "video"}:
            if attributes.get("src"):
                self.assets.append((tag, attributes["src"]))


class _FoundationsGuide(HTMLParser):
    """Collect semantic guide entries without coupling tests to HTML layout."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids: list[str] = []
        self.links: list[str] = []
        self.entries: list[dict] = []
        self._entry: dict | None = None
        self._inside_code = False

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        if tag == "article" and (
            "data-constructor" in attributes or "data-tactic" in attributes
        ):
            assert self._entry is None, "native guide entries must not be nested"
            self._entry = {
                "attributes": attributes,
                "text": [],
                "code": [],
                "links": [],
            }
            self.entries.append(self._entry)
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])
            if self._entry is not None:
                self._entry["links"].append(attributes["href"])
        if tag == "code" and self._entry is not None:
            assert not self._inside_code
            self._inside_code = True
            self._entry["code"].append([])

    def handle_endtag(self, tag: str) -> None:
        if tag == "code":
            self._inside_code = False
        elif tag == "article" and self._entry is not None:
            self._entry = None

    def handle_data(self, data: str) -> None:
        if self._entry is None:
            return
        self._entry["text"].append(data)
        if self._inside_code:
            self._entry["code"][-1].append(data)


def _foundations_guide() -> _FoundationsGuide:
    parser = _FoundationsGuide()
    parser.feed((EXPLORER / "foundations.html").read_text(encoding="utf-8"))
    parser.close()
    return parser


def _normalized_guide_text(parts: str | list[str]) -> str:
    source = parts if isinstance(parts, str) else " ".join(parts)
    return " ".join(source.split())


class _InformalSection(HTMLParser):
    """Observe only the explicitly marked informal-proof section."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.attributes: dict[str, str | None] | None = None
        self.depth = 0
        self.links: list[dict[str, str | None]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        classes = set((attributes.get("class") or "").split())
        if tag == "section" and "pa-informal-proof" in classes:
            assert self.attributes is None and self.depth == 0
            self.attributes = attributes
            self.depth = 1
            return
        if self.depth:
            self.depth += 1
            if tag == "a":
                self.links.append(attributes)

    def handle_endtag(self, tag: str) -> None:
        if self.depth:
            self.depth -= 1

    def handle_data(self, data: str) -> None:
        if self.depth:
            self.text.append(data)


def _registry_rows() -> list[dict]:
    payload = _load(TAGS)
    rows = payload.get("assignments", payload.get("tags"))
    if isinstance(rows, list):
        assert all(isinstance(row, dict) for row in rows)
        return rows
    # A name-to-tag object is also a deterministic registry representation.
    if isinstance(rows, dict):
        return [
            {"name": name, "tag": value if isinstance(value, str) else value["tag"]}
            for name, value in sorted(rows.items())
        ]
    raise AssertionError("tag registry must expose an assignments list or mapping")


def _edge_pair(edge: dict) -> tuple[str, str]:
    source = edge.get("source") or edge.get("dependency") or edge.get("dependency_tag")
    target = edge.get("target") or edge.get("dependent") or edge.get("dependent_tag")
    assert isinstance(source, str) and isinstance(target, str)
    return source, target


def test_proof_explorer_generator_is_byte_current() -> None:
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_generator_rejects_and_prunes_unmanifested_files(tmp_path, monkeypatch) -> None:
    import build_pa_proof_explorer as generator

    monkeypatch.setattr(generator, "OUTPUT", tmp_path)
    files = {"index.html": b"owned\n", "manifest.json": b"{}\n"}
    extra = tmp_path / "assets" / "evil.js"
    extra.parent.mkdir(parents=True)
    extra.write_bytes(b"unexpected\n")
    defined = tmp_path / "defined" / "manifest.json"
    defined.parent.mkdir(parents=True)
    defined.write_bytes(b'{"owned_by":"defined-generator"}\n')
    k3b = tmp_path / "k3b" / "index.html"
    k3b.parent.mkdir(parents=True)
    k3b.write_bytes(b"private K3B microsite\n")
    assert not generator._check(files)

    generator._write(files)
    assert {
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == set(files) | {"defined/manifest.json", "k3b/index.html"}
    assert defined.read_bytes() == b'{"owned_by":"defined-generator"}\n'
    assert k3b.read_bytes() == b"private K3B microsite\n"
    assert generator._check(files)


def test_generator_preserves_and_authenticates_immutable_parent_evidence(
    tmp_path, monkeypatch
) -> None:
    import build_pa_proof_explorer as generator

    frozen_payload = b"catalog-bound historical corpus\n"
    frozen = tmp_path / generator.IMMUTABLE_EVIDENCE_CORPUS_PATH
    frozen.parent.mkdir(parents=True)
    frozen.write_bytes(frozen_payload)
    monkeypatch.setattr(generator, "OUTPUT", tmp_path)
    monkeypatch.setattr(generator, "IMMUTABLE_EVIDENCE_CORPUS_BYTES", len(frozen_payload))
    monkeypatch.setattr(
        generator, "IMMUTABLE_EVIDENCE_CORPUS_SHA256", sha256(frozen_payload).hexdigest()
    )
    original_inode = frozen.stat().st_ino
    original_timestamp = frozen.stat().st_mtime_ns
    files = {
        generator.IMMUTABLE_EVIDENCE_CORPUS_PATH: frozen_payload,
        generator.CURRENT_CORPUS_PATH: b"current v25 view\n",
        "manifest.json": b"{}\n",
    }

    generator._write(files)

    assert frozen.read_bytes() == frozen_payload
    assert frozen.stat().st_ino == original_inode
    assert frozen.stat().st_mtime_ns == original_timestamp
    assert (tmp_path / generator.CURRENT_CORPUS_PATH).read_bytes() == b"current v25 view\n"
    assert generator._check(files)

    malicious = dict(files)
    malicious[generator.IMMUTABLE_EVIDENCE_CORPUS_PATH] = b"replacement\n"
    try:
        generator._write(malicious)
    except ValueError as error:
        assert "refusing to replace" in str(error)
    else:
        raise AssertionError("immutable parent evidence must never be replaceable")
    assert frozen.read_bytes() == frozen_payload

    frozen.write_bytes(b"tampered parent evidence\n")
    try:
        generator._write(files)
    except ValueError as error:
        assert "immutable Alpha-parent" in str(error)
    else:
        raise AssertionError("tampered immutable parent evidence must fail closed")


def test_manifest_pins_the_exact_qr_closure_and_truthful_partition() -> None:
    from peano_lab.library import editions_v16 as alpha_v16
    from peano_lab.library import editions_v25 as current_alpha

    manifest = _load(MANIFEST)
    records = _records()
    immutable_bytes = IMMUTABLE_EVIDENCE_CORPUS.read_bytes()
    immutable = _load(IMMUTABLE_EVIDENCE_CORPUS)
    assert len(immutable_bytes) == IMMUTABLE_EVIDENCE_CORPUS_BYTES
    assert sha256(immutable_bytes).hexdigest() == IMMUTABLE_EVIDENCE_CORPUS_SHA256
    assert manifest["immutable_evidence_corpus_path"] == "api/corpus.json"
    assert manifest["immutable_evidence_corpus_sha256"] == (
        IMMUTABLE_EVIDENCE_CORPUS_SHA256
    )
    assert manifest["immutable_evidence_corpus_bytes"] == (
        IMMUTABLE_EVIDENCE_CORPUS_BYTES
    )
    assert manifest["current_corpus_path"] == "api/current-corpus.json"
    assert manifest["current_corpus_sha256"] == sha256(CORPUS.read_bytes()).hexdigest()
    assert "alpha_edition_version" not in immutable
    assert [row["name"] for row in immutable["theorems"]] == [
        row["name"] for row in records
    ]
    assert _metric(manifest, "theorem_count", "node_count") == THEOREM_COUNT
    assert _metric(manifest, "edge_count") == EDGE_COUNT
    assert _metric(manifest, "layer_count") == LAYER_COUNT
    assert _metric(manifest, "formal_line_count", "proof_line_count") == FORMAL_LINE_COUNT
    assert _metric(manifest, "public_count") == PUBLIC_COUNT
    assert _metric(manifest, "candidate_count") == CANDIDATE_COUNT
    assert len(records) == THEOREM_COUNT

    scopes = [row["scope"] for row in records]
    assert scopes.count("public") == PUBLIC_COUNT
    assert scopes.count("candidate") == CANDIDATE_COUNT
    assert manifest["alpha_edition_version"] == "v25"
    assert manifest["alpha_edition_identity_sha256"] == (
        current_alpha.ALPHA_V25_IDENTITY_SHA256
    )
    assert manifest["alpha_edition_checked_use_count"] == 2080
    assert manifest["proof_edition_version"] == "v16"
    assert manifest["proof_edition_identity_sha256"] == (
        alpha_v16.ALPHA_V16_IDENTITY_SHA256
    )
    assert manifest["proof_edition_checked_use_count"] == 885
    assert manifest["graph_checked_use_count"] == THEOREM_COUNT
    assert manifest["graph_stable_closed_count"] == PUBLIC_COUNT
    assert manifest["graph_alpha_closed_count"] == CANDIDATE_COUNT
    assert manifest["graph_newly_promoted_count"] == 315
    assert manifest["source_scope_policy"] == (
        "historical_origin_not_current_release_authority"
    )
    assert Counter(
        (row["scope"], row["alpha_evidence"], row["stable_member"])
        for row in records
    ) == {
        ("public", "stable_closed", True): PUBLIC_COUNT,
        ("candidate", "alpha_closed", False): CANDIDATE_COUNT,
    }
    assert all(row["alpha_checked_use"] is True for row in records)
    assert all(row["alpha_edition_version"] == "v25" for row in records)
    assert all(row["proof_edition_version"] == "v16" for row in records)
    root = next(row for row in records if row["name"] == "quadratic_reciprocity_combined")
    assert root["scope"] == "candidate"
    assert root["status"] == "alpha_closed"
    assert root["alpha_evidence"] == "alpha_closed"
    assert root["alpha_checked_use"] is True
    assert root["stable_member"] is False
    root_page = (EXPLORER / "tag" / f"{root['tag']}.html").read_text(encoding="utf-8")
    assert "pa-status-public" in root_page
    assert "Alpha v25 checked-use theorem" in root_page
    assert "<dt>Current Alpha edition</dt><dd>v25</dd>" in root_page
    assert "<dt>Proof-bearing Alpha edition</dt><dd>v16</dd>" in root_page
    assert "historical candidate-factory source; Alpha-only" in root_page
    assert "<dt>Stable membership</dt><dd>no</dd>" in root_page
    assert "pending layered closure" not in root_page
    assert "not publicly admitted" not in root_page


def test_graph_preserves_source_origin_and_publishes_independent_release_evidence() -> None:
    graph = _load(GRAPH)
    manifest = _load(MANIFEST)
    nodes = {row["name"]: row for row in graph["nodes"]}
    root = nodes["quadratic_reciprocity_combined"]

    assert root["scope"] == "candidate"
    assert root["status"] == "alpha_closed"
    assert root["alpha_edition_version"] == "v25"
    assert root["alpha_evidence"] == "alpha_closed"
    assert root["alpha_checked_use"] is True
    assert root["stable_member"] is False
    assert graph["alpha_edition_identity_sha256"] == (
        manifest["alpha_edition_identity_sha256"]
    )
    assert graph["graph_checked_use_count"] == THEOREM_COUNT
    assert Counter(row["scope"] for row in nodes.values()) == {
        "public": PUBLIC_COUNT,
        "candidate": CANDIDATE_COUNT,
    }

    graph_page = (EXPLORER / "graph.html").read_text(encoding="utf-8")
    assert 'id="pa-proof-release-evidence"' in graph_page
    assert "Alpha v25 checked-use theorem; independently closed; not Stable" in graph_page
    assert "historical candidate-factory source" in graph_page
    assert "pending layered closure" not in graph_page


def test_graph_release_overlay_updates_selected_alpha_and_stable_nodes() -> None:
    graph = _load(GRAPH)
    root = next(
        row for row in graph["nodes"]
        if row["name"] == "quadratic_reciprocity_combined"
    )
    stable = next(row for row in graph["nodes"] if row["stable_member"])
    page = (EXPLORER / "graph.html").read_text(encoding="utf-8")
    match = re.search(
        r'<script id="pa-proof-release-evidence">(.*?)</script>',
        page,
        flags=re.DOTALL,
    )
    assert match is not None
    harness = """
"use strict";
const payload = __PAYLOAD__;
const rootNode = payload.nodes[0];
const stableNode = payload.nodes[1];
const title = {textContent: rootNode.tag + " · " + rootNode.name};
const status = {className: "pa-status-candidate", textContent: "obsolete"};
let ready;
let observe;
global.window = {PA_PROOF_GRAPH: payload};
global.document = {
  readyState: "loading",
  addEventListener(_event, callback) { ready = callback; },
  querySelector(selector) {
    if (selector !== "[data-dependency-graph]") return null;
    return {querySelector(item) {
      if (item === "[data-graph-title]") return title;
      if (item === "[data-graph-status]") return status;
      return null;
    }};
  }
};
global.MutationObserver = class {
  constructor(callback) { observe = callback; }
  observe() {}
};
__SCRIPT__
if (typeof ready !== "function") throw Error("DOMContentLoaded was not observed");
ready();
if (status.textContent !==
    "Alpha v25 checked-use theorem; independently closed; not Stable") {
  throw Error("Alpha-only evidence was not shown: " + status.textContent);
}
if (status.className !== "pa-status-public") throw Error("checked-use style missing");
title.textContent = stableNode.tag + " · " + stableNode.name;
status.textContent = "stale legacy text";
observe();
if (status.textContent !== "Stable checked-use theorem; independently closed") {
  throw Error("Stable evidence was not refreshed: " + status.textContent);
}
""".replace("__PAYLOAD__", json.dumps({"nodes": [root, stable]})).replace(
        "__SCRIPT__", match.group(1)
    )
    result = subprocess.run(
        ["node", "--input-type=commonjs", "-"],
        input=harness,
        capture_output=True,
        check=False,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_persistent_tags_are_unique_complete_and_not_derived_at_build_time() -> None:
    records = _records()
    registry = _registry_rows()
    tags = [row["tag"] for row in records]
    names = [row["name"] for row in records]
    assert len(tags) == len(set(tags)) == THEOREM_COUNT
    assert len(names) == len(set(names)) == THEOREM_COUNT
    assert all(TAG_PATTERN.fullmatch(tag) for tag in tags)
    assert {(row["name"], row["tag"]) for row in registry} == set(zip(names, tags))
    assert INFORMAL.is_file()
    assert len(tuple((EXPLORER / "tag").glob("*.html"))) == THEOREM_COUNT
    assert len(tuple((EXPLORER / "name").glob("*.html"))) == THEOREM_COUNT


def test_every_informal_proof_declares_provenance_and_clickable_references() -> None:
    records = _records()
    by_name = {row["name"]: row for row in records}
    expected_review = {
        "generated_structural_guide": "generated",
        "curated_override": "curated_reviewed",
    }
    observed_kinds: set[str] = set()

    for row in records:
        informal = row["informal"]
        assert isinstance(informal, dict)
        kind = informal["kind"]
        review = informal["review"]
        observed_kinds.add(kind)
        assert review == expected_review[kind]
        assert isinstance(informal["title"], str) and informal["title"].strip()
        assert (
            isinstance(informal["paragraphs"], list)
            and informal["paragraphs"]
            and all(isinstance(text, str) and text.strip() for text in informal["paragraphs"])
        )
        references = informal["references"]
        assert isinstance(references, list)
        assert len({_name(reference) for reference in references}) == len(references)

        page = EXPLORER / "tag" / f"{row['tag']}.html"
        section = _InformalSection()
        section.feed(page.read_text(encoding="utf-8"))
        assert section.attributes is not None
        assert section.attributes.get("data-informal-kind") == kind
        assert section.attributes.get("data-informal-review") == review
        prose = " ".join(" ".join(section.text).split()).lower()
        label = "generated structural guide" if review == "generated" else "curated informal proof"
        assert label in prose

        rendered = [
            attributes["href"]
            for attributes in section.links
            if "pa-informal-ref" in (attributes.get("class") or "").split()
        ]
        assert len(rendered) == len(references)
        assert set(rendered) == {_href(reference) for reference in references}
        for reference in references:
            target_row = by_name[_name(reference)]
            assert _tag(reference) == target_row["tag"]
            target, fragment = _resolve(page, _href(reference))
            assert target == EXPLORER / "tag" / f"{target_row['tag']}.html"
            assert not fragment

    # The corpus must visibly distinguish machine-generated scaffolding from
    # the small set of human-curated mathematical explanations.
    assert observed_kinds == set(expected_review)


def test_graph_and_record_reverse_edges_are_exact_inverses() -> None:
    records = _records()
    by_tag = {row["tag"]: row for row in records}
    expected = {
        (_tag(dependency), row["tag"])
        for row in records
        for dependency in row["dependencies"]
    }
    reverse = {
        (row["tag"], _tag(dependent))
        for row in records
        for dependent in row["dependents"]
    }
    assert len(expected) == EDGE_COUNT
    assert reverse == expected
    assert all(source in by_tag and target in by_tag for source, target in expected)
    assert all(by_tag[source]["layer"] < by_tag[target]["layer"] for source, target in expected)
    assert len({row["layer"] for row in records}) == LAYER_COUNT

    graph = _load(GRAPH)
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    assert isinstance(nodes, list) and isinstance(edges, list)
    assert {_tag(node) for node in nodes} == set(by_tag)
    assert {_edge_pair(edge) for edge in edges} == expected


def test_graph_v2_exposes_layers_closures_and_canonical_foundation_paths() -> None:
    graph = _load(GRAPH)
    records = _records()
    tags = [row["tag"] for row in records]
    rank = {tag: index for index, tag in enumerate(tags)}
    by_tag = {row["tag"]: row for row in records}
    edge_pairs = {_edge_pair(edge) for edge in graph["edges"]}

    assert graph["schema"] == "peano-lab-pa-proof-graph-v2"
    assert graph["orientation"] == "dependency_to_dependent"
    assert graph["path_policy"] == {
        "foundation_path_alias": "shortest_root_path",
        "shortest_root_path": "fewest_edges_from_any_foundation",
        "critical_root_path": "dependency_depth_witness",
        "tie_break": "admission_order_lexicographic",
        "includes_endpoints": True,
    }
    assert [_tag(node) for node in graph["nodes"]] == tags

    adjacency = graph["adjacency"]
    assert isinstance(adjacency, dict)
    assert set(adjacency) == set(tags)
    direct_dependencies = {
        tag: sorted(
            (_tag(item) for item in by_tag[tag]["dependencies"]),
            key=rank.__getitem__,
        )
        for tag in tags
    }
    direct_dependents = {tag: [] for tag in tags}
    for tag in tags:
        for dependency in direct_dependencies[tag]:
            direct_dependents[dependency].append(tag)

    foundations = [tag for tag in tags if not direct_dependencies[tag]]
    terminals = [tag for tag in tags if not direct_dependents[tag]]
    assert graph["foundations"] == foundations
    assert graph["terminals"] == terminals
    assert len(foundations) == 48
    assert terminals == [
        next(row["tag"] for row in records if row["name"] == "quadratic_reciprocity_combined")
    ]

    layers = graph["layers"]
    assert [layer["index"] for layer in layers] == list(range(LAYER_COUNT))
    assert [tag for layer in layers for tag in layer["nodes"]] == [
        row["tag"]
        for layer in layers
        for row in records
        if row["layer"] == layer["index"]
    ]
    assert {
        tag: layer["index"]
        for layer in layers
        for tag in layer["nodes"]
    } == {row["tag"]: row["layer"] for row in records}

    expected_ancestors: dict[str, set[str]] = {}
    expected_shortest_paths: dict[str, list[str]] = {}
    expected_critical_paths: dict[str, list[str]] = {}
    expected_root_path_counts: dict[str, int] = {}
    for tag in tags:
        closure: set[str] = set()
        for dependency in direct_dependencies[tag]:
            closure |= {dependency} | expected_ancestors[dependency]
        expected_ancestors[tag] = closure
        if direct_dependencies[tag]:
            shortest_candidates = [
                [*expected_shortest_paths[dependency], tag]
                for dependency in direct_dependencies[tag]
            ]
            expected_shortest_paths[tag] = min(
                shortest_candidates,
                key=lambda path: (len(path), tuple(rank[item] for item in path)),
            )
            critical_candidates = [
                [*expected_critical_paths[dependency], tag]
                for dependency in direct_dependencies[tag]
            ]
            expected_critical_paths[tag] = min(
                critical_candidates,
                key=lambda path: (-len(path), tuple(rank[item] for item in path)),
            )
            expected_root_path_counts[tag] = sum(
                expected_root_path_counts[dependency]
                for dependency in direct_dependencies[tag]
            )
        else:
            expected_shortest_paths[tag] = [tag]
            expected_critical_paths[tag] = [tag]
            expected_root_path_counts[tag] = 1

    expected_descendants: dict[str, set[str]] = {}
    for tag in reversed(tags):
        closure = set()
        for dependent in direct_dependents[tag]:
            closure |= {dependent} | expected_descendants[dependent]
        expected_descendants[tag] = closure

    for tag in tags:
        neighborhood = adjacency[tag]
        assert neighborhood["dependencies"] == direct_dependencies[tag]
        assert neighborhood["dependents"] == direct_dependents[tag]
        assert neighborhood["ancestors"] == sorted(
            expected_ancestors[tag], key=rank.__getitem__
        )
        assert neighborhood["descendants"] == sorted(
            expected_descendants[tag], key=rank.__getitem__
        )
        assert neighborhood["foundation_path"] == expected_shortest_paths[tag]
        assert neighborhood["shortest_root_path"] == expected_shortest_paths[tag]
        assert neighborhood["critical_root_path"] == expected_critical_paths[tag]
        assert neighborhood["root_path_count"] == expected_root_path_counts[tag]
        assert tag not in neighborhood["ancestors"]
        assert tag not in neighborhood["descendants"]

        path = neighborhood["foundation_path"]
        assert path[0] in foundations and path[-1] == tag
        assert all((left, right) in edge_pairs for left, right in zip(path, path[1:]))
        critical_path = neighborhood["critical_root_path"]
        assert critical_path[0] in foundations and critical_path[-1] == tag
        assert len(critical_path) == by_tag[tag]["layer"] + 1
        assert all(
            (left, right) in edge_pairs
            for left, right in zip(critical_path, critical_path[1:])
        )

    # The two closures are exact relational inverses, not independent hints.
    assert all(
        (source in expected_ancestors[target])
        == (target in expected_descendants[source])
        for source in tags
        for target in tags
    )
    qr_tag = next(
        row["tag"] for row in records
        if row["name"] == "quadratic_reciprocity_combined"
    )
    assert adjacency[qr_tag]["root_path_count"] == 101_278


def test_graph_schema_and_inline_file_protocol_payload_are_exact_and_deterministic() -> None:
    graph = _load(GRAPH)
    schema = _load(GRAPH_SCHEMA)
    assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
    assert schema["$id"] == "urn:peano-lab:pa-proof-graph-v2"
    assert schema["properties"]["schema"]["const"] == graph["schema"]
    assert schema["properties"]["orientation"]["const"] == graph["orientation"]
    assert set(schema["required"]) == set(graph)
    assert schema["properties"]["adjacency"]["additionalProperties"] is False
    assert set(schema["$defs"]["neighborhood"]["required"]) == {
        "dependencies", "dependents", "ancestors", "descendants", "foundation_path",
        "shortest_root_path", "critical_root_path", "root_path_count",
    }

    graph_page = EXPLORER / "graph.html"
    source = graph_page.read_text(encoding="utf-8")
    match = re.search(
        r'<script id="pa-proof-graph-data">([^<]*)</script>',
        source,
    )
    assert match is not None
    assignment = match.group(1)
    prefix = "window.PA_PROOF_GRAPH="
    assert assignment.startswith(prefix) and assignment.endswith(";")
    assert json.loads(assignment[len(prefix):-1]) == graph
    assert not ({"<", ">", "&"} & set(assignment))
    assert "graph-data.js" not in source
    assert not (EXPLORER / "api" / "graph-data.js").exists()
    explorer_js = (EXPLORER / "assets" / "explorer.js").read_text(encoding="utf-8")
    assert explorer_js.index("window.PA_PROOF_GRAPH") < explorer_js.index("window.fetch")

    manifest = _load(MANIFEST)
    manifest_files = {item["path"]: item for item in manifest["files"]}
    pinned = {
        "graph.html", "api/corpus.json", "api/current-corpus.json",
        "api/graph.json", "api/graph.schema.json",
        "assets/explorer.css", "assets/explorer.js",
    }
    assert pinned <= set(manifest_files)
    assert "api/graph-data.js" not in manifest_files
    for relative in pinned:
        payload = (EXPLORER / relative).read_bytes()
        assert manifest_files[relative]["bytes"] == len(payload)
        assert manifest_files[relative]["sha256"] == sha256(payload).hexdigest()
    on_disk = {
        str(path.relative_to(EXPLORER))
        for path in EXPLORER.rglob("*")
        if path.is_file()
        and path.relative_to(EXPLORER).parts[0] not in {"defined", "k3b"}
    }
    assert on_disk == set(manifest_files) | {"manifest.json"}


def test_graph_ui_has_sparse_defaults_and_keeps_full_direct_graph_available() -> None:
    graph = _load(GRAPH)
    target = "PA00FW"
    neighborhood = graph["adjacency"][target]
    visible = {
        target,
        *neighborhood["dependencies"],
        *neighborhood["dependents"],
    }
    induced = [
        edge for edge in graph["edges"]
        if edge["dependency"] in visible and edge["dependent"] in visible
    ]
    assert len(visible) == 4
    assert len(induced) == 3
    assert len(graph["nodes"]) == THEOREM_COUNT
    assert len(graph["edges"]) == EDGE_COUNT

    page = (EXPLORER / "graph.html").read_text(encoding="utf-8")
    assert '<option value="neighborhood" selected>' in page
    assert '<option value="focus" selected>Focused: path + target</option>' in page
    assert '<option value="all">All direct arrows (heavy)</option>' in page
    assert "suppresses arrows visually only" in page

    script = (EXPLORER / "assets" / "explorer.js").read_text(encoding="utf-8")
    assert 'function graphDisplayedEdges(state, selection)' in script
    assert 'state.edgeMode === "none"' in script
    assert 'state.edgeMode === "all"' in script
    assert ': "neighborhood";' in script
    assert 'visible.length > 160' in script
    assert 'selection.displayedEdges.length + " of " + selection.edges.length' in script
    # Autocomplete no longer doubles 557 persistent option elements merely to
    # expose theorem names; graphResolve still accepts typed exact names.
    datalist_block = script[script.index('var datalist = root.querySelector("#pa-graph-theorems")'):]
    datalist_block = datalist_block[:datalist_block.index('state.form.addEventListener("submit"')]
    assert datalist_block.count('document.createElement("option")') == 1


def test_all_formal_lines_have_stable_clickable_anchors_and_safe_references() -> None:
    records = _records()
    total_lines = 0
    explicit_occurrences = 0
    referenced_edges: set[tuple[str, str]] = set()
    implicit_edges: set[tuple[str, str]] = set()

    for row in records:
        page = EXPLORER / "tag" / f"{row['tag']}.html"
        source = page.read_text(encoding="utf-8")
        dependencies = {_tag(item): item for item in row["dependencies"]}
        lines = row["lines"]
        assert isinstance(lines, list)
        for number, line in enumerate(lines, start=1):
            assert line["number"] == number
            assert line["id"] == f"proof-line-{number:04d}"
            assert source.count(f'id="{line["id"]}"') == 1
            assert f'href="#{line["id"]}"' in source
            assert isinstance(line["text"], str) and line["text"]
            assert isinstance(line["tactic"], str) and line["tactic"]
            tactic_href = line.get("tactic_href")
            if tactic_href is not None:
                target, fragment = _resolve(page, tactic_href)
                assert target == EXPLORER / "foundations.html"
                assert fragment == f"tactic-{line['tactic']}"
            previous_end = 0
            for reference in line["references"]:
                assert reference["kind"] in {"dependency", "theorem"}
                start = reference["start"]
                end = reference["end"]
                assert type(start) is int and type(end) is int
                assert previous_end <= start < end <= len(line["text"])
                previous_end = end
                target_tag = _tag(reference)
                assert target_tag in dependencies
                token = line["text"][start:end]
                assert token == _name(reference)
                target, fragment = _resolve(page, _href(reference))
                assert target == EXPLORER / "tag" / f"{target_tag}.html"
                assert not fragment
                assert html.escape(token, quote=True) in source
                referenced_edges.add((target_tag, row["tag"]))
                explicit_occurrences += 1
        total_lines += len(lines)

        for dependency_tag, dependency in dependencies.items():
            assert isinstance(dependency, dict)
            href = _href(dependency)
            target, fragment = _resolve(page, href)
            assert target == EXPLORER / "tag" / f"{dependency_tag}.html"
            assert not fragment
            assert f'href="{html.escape(href, quote=True)}"' in source
            count = dependency["explicit_reference_count"]
            body_reference = dependency["body_reference"]
            assert type(count) is int and count >= 0
            assert type(body_reference) is bool and body_reference == (count > 0)
            if not body_reference:
                implicit_edges.add((dependency_tag, row["tag"]))

    assert total_lines == FORMAL_LINE_COUNT
    assert explicit_occurrences == EXPLICIT_REFERENCE_COUNT
    assert len(referenced_edges) == EXPLICIT_EDGE_COUNT
    assert len(implicit_edges) == IMPLICIT_EDGE_COUNT
    assert referenced_edges.isdisjoint(implicit_edges)
    assert len(referenced_edges | implicit_edges) == EDGE_COUNT


def test_foundations_cover_native_grammar_axioms_tactics_and_all_constructors() -> None:
    foundations = (EXPLORER / "foundations.html").read_text(encoding="utf-8")
    ids = set(ID_PATTERN.findall(foundations))
    for axiom in range(1, 7):
        assert f"axiom-pa{axiom}" in ids
        assert f"PA{axiom}" in foundations
    for anchor in (
        "grammar-terms",
        "grammar-formulas",
        "proof-induction",
        "proof-cut",
        "proof-dne",
    ):
        assert anchor in ids

    from peano_lab.kernel import proofs

    constructors = tuple(name for name in proofs.__all__ if name != "Proof")
    assert len(constructors) == 25
    for constructor in constructors:
        assert constructor in foundations

    used_tactics = {
        line["tactic"] for row in _records() for line in row["lines"]
    }
    assert used_tactics
    assert {f"tactic-{name}" for name in used_tactics} <= ids
    lower = foundations.lower()
    for phrase in ("terms", "formulas", "induction", "kernel", "untrusted"):
        assert phrase in lower


def test_foundations_explain_every_native_kernel_constructor() -> None:
    from peano_lab.kernel import proofs

    guide = _foundations_guide()
    expected = tuple(name for name in proofs.__all__ if name != "Proof")
    entries = {
        entry["attributes"]["data-constructor"]: entry
        for entry in guide.entries
        if "data-constructor" in entry["attributes"]
    }

    assert len(expected) == 25
    assert set(entries) == set(expected)
    assert len(entries) == sum(
        "data-constructor" in entry["attributes"] for entry in guide.entries
    )
    for name in expected:
        entry = entries[name]
        text = _normalized_guide_text(entry["text"])
        field_names = ", ".join(
            field.name for field in fields(getattr(proofs, name))
        )
        assert entry["attributes"]["id"] == f"constructor-{name.lower()}"
        assert f"{name}({field_names})" in text
        assert len(text.split()) >= 12, (name, text)
        assert len(entry["code"]) >= 2, (name, entry["code"])
        assert any(
            urlsplit(href).path
            in {
                "/vietnam2026/book/peano/axioms-and-rules.html",
                "/vietnam2026/book/peano/kernel.html",
                "/vietnam2026/book/arithmetic-library/proof-sharing.html",
            }
            for href in entry["links"]
        ), (name, entry["links"])

    dne = _normalized_guide_text(entries["DNE"]["text"]).lower()
    cut = _normalized_guide_text(entries["Cut"]["text"]).lower()
    substitution = _normalized_guide_text(entries["EqSubst"]["text"]).lower()
    induction = _normalized_guide_text(entries["Ind"]["text"]).lower()
    assert "classical" in dne
    assert "shar" in cut and ("axiom" in cut or "assumption" in cut)
    assert "motive" in substitution and (
        "transport" in substitution or "substitut" in substitution
    )
    assert "motive" in induction and "induction" in induction


def test_foundations_document_all_native_tactics_tacticals_and_automation() -> None:
    from peano_lab.ui.data_tactics import TACTIC_CARDS

    guide = _foundations_guide()
    cards = {card.name: card for card in TACTIC_CARDS}
    entries = {
        entry["attributes"]["data-tactic"]: entry
        for entry in guide.entries
        if "data-tactic" in entry["attributes"]
    }
    used_tactics = {
        line["tactic"] for row in _records() for line in row["lines"]
    }

    assert len(cards) == 34
    assert set(entries) == set(cards)
    assert len(entries) == sum(
        "data-tactic" in entry["attributes"] for entry in guide.entries
    )
    assert len(used_tactics) == 19
    assert used_tactics <= set(cards)
    assert Counter(card.kind for card in TACTIC_CARDS) == {
        "primitive": 23,
        "tactical": 6,
        "automation": 5,
    }

    for name, card in cards.items():
        entry = entries[name]
        attributes = entry["attributes"]
        expected_slug = {";": "then", "<|>": "orelse"}.get(name, name)
        assert attributes["id"] == f"tactic-{expected_slug}"
        assert attributes["data-tactic-kind"] == card.kind
        assert attributes["data-corpus-used"] == str(name in used_tactics).lower()

        text = _normalized_guide_text(entry["text"])
        for value in (
            card.syntax,
            card.summary,
            card.goal_effect,
            card.certificate_effect,
            card.example_theorem,
            *card.example_commands,
            *card.common_errors,
        ):
            assert _normalized_guide_text(value) in text, (name, value)
        lower = text.lower()
        assert "goal effect" in lower and "kernel evidence" in lower
        assert entry["code"], name
        assert any(
            urlsplit(href).path.startswith("/vietnam2026/book/")
            for href in entry["links"]
        ), (name, entry["links"])
        live_cards = [
            href
            for href in entry["links"]
            if urlsplit(href).path == "/peano-lab/"
        ]
        assert len(live_cards) == 1, (name, live_cards)
        assert parse_qs(urlsplit(live_cards[0]).query, strict_parsing=True) == {
            "cmd": [f"pa tactic {name}"]
        }


def test_foundations_links_resolve_under_public_and_jupyter_book_mounts() -> None:
    guide = _foundations_guide()
    ids = set(guide.ids)
    assert len(ids) == len(guide.ids), "foundation anchors must be unique"

    public_book_root = "/vietnam2026/book/"
    public_mount = (
        "https://bnaskrecki.faculty.wmi.amu.edu.pl/"
        "proofs/quadratic-reciprocity/explorer/foundations.html"
    )
    jupyter_book_mount = (
        "https://bnaskrecki.faculty.wmi.amu.edu.pl/"
        "vietnam2026/book/_static/pa-proof-explorer/foundations.html"
    )
    built_book = (REPO / "book" / "_build" / "html").resolve()
    explorer_root = EXPLORER.resolve()
    toc = (REPO / "book" / "_toc.yml").read_text(encoding="utf-8")
    chapter_anchors: dict[Path, set[str]] = {}
    chapters: set[str] = set()

    for raw in guide.links:
        parsed = urlsplit(raw)
        assert parsed.scheme not in {"javascript", "data", "vbscript"}, raw
        if not parsed.path and parsed.fragment:
            assert unquote(parsed.fragment) in ids, raw
            continue

        if "/peano/" in parsed.path or "/arithmetic-library/" in parsed.path:
            assert not parsed.scheme and not parsed.netloc, raw
            assert parsed.path.startswith(public_book_root), raw

        if not parsed.path.startswith(public_book_root):
            if not parsed.scheme and not parsed.netloc and not parsed.path.startswith("/"):
                target = (explorer_root / unquote(parsed.path)).resolve()
                try:
                    target.relative_to(explorer_root)
                except ValueError:
                    assert urlsplit(urljoin(public_mount, raw)).path == (
                        "/proofs/grand-campaign/"
                    ), raw
                    target = (
                        REPO / "book" / "_static" / "constructive-grand-campaign"
                    )
                if target.is_dir():
                    target = target / "index.html"
                assert target.is_file(), (raw, target)
                if parsed.fragment:
                    assert unquote(parsed.fragment) in set(
                        ID_PATTERN.findall(target.read_text(encoding="utf-8"))
                    ), raw
            elif parsed.path.startswith("/peano-lab/"):
                assert (REPO / "peano-lab" / "index.html").is_file(), raw
            continue

        relative = unquote(parsed.path.removeprefix(public_book_root))
        source = REPO / "book" / Path(relative).with_suffix(".md")
        assert source.is_file(), (raw, source)
        target = (built_book / relative).resolve()
        target.relative_to(built_book)
        chapter = Path(relative).with_suffix("").as_posix()
        assert re.search(
            rf"^\s*-\s*file:\s*{re.escape(chapter)}\s*$", toc, re.MULTILINE
        ), (raw, chapter)
        chapters.add(relative)

        if parsed.fragment:
            available = chapter_anchors.get(target)
            if available is None:
                if target.is_file():
                    available = set(
                        ID_PATTERN.findall(target.read_text(encoding="utf-8"))
                    )
                else:
                    markdown = source.read_text(encoding="utf-8")
                    available = set(
                        re.findall(
                            r"^\(([^)\s]+)\)=\s*$", markdown, re.MULTILINE
                        )
                    )
                    for heading in re.findall(
                        r"^\s{0,3}#{1,6}\s+(.+?)\s*$", markdown, re.MULTILINE
                    ):
                        heading = re.sub(r"[`*_]", "", heading)
                        available.add(
                            re.sub(r"[^a-z0-9]+", "-", heading.lower()).strip("-")
                        )
                chapter_anchors[target] = available
            assert unquote(parsed.fragment) in available, raw

        assert urlsplit(urljoin(public_mount, raw)).path == parsed.path
        assert urlsplit(urljoin(jupyter_book_mount, raw)).path == parsed.path
        assert "/proofs/peano/" not in urljoin(public_mount, raw)

    assert {
        "peano/language-reference.html",
        "peano/axioms-and-rules.html",
        "peano/kernel.html",
        "peano/tactics.html",
        "peano/tacticals.html",
        "peano/induction-ladder.html",
        "peano/arithmetic-automation.html",
        "arithmetic-library/language-and-trust.html",
        "arithmetic-library/proof-sharing.html",
    } <= chapters


def test_explorer_has_only_local_runtime_assets_and_no_html_injection_sinks() -> None:
    pages = tuple(EXPLORER.glob("*.html")) + tuple((EXPLORER / "tag").glob("*.html"))
    assert len(pages) == THEOREM_COUNT + 3
    for page in pages:
        parser = _Assets()
        parser.feed(page.read_text(encoding="utf-8"))
        asset_names = [Path(urlsplit(raw).path).name for _, raw in parser.assets]
        assert asset_names.count("explorer.css") == 1
        assert asset_names.count("explorer.js") == 1
        assert all(
            urlsplit(raw).scheme.lower() not in {"data", "javascript", "vbscript"}
            for raw in parser.links
        )
        for _, raw in parser.assets:
            parsed = urlsplit(raw)
            assert not parsed.scheme and not parsed.netloc and not raw.startswith("//")
            _resolve(page, raw)

    css = (EXPLORER / "assets" / "explorer.css").read_text(encoding="utf-8")
    js = (EXPLORER / "assets" / "explorer.js").read_text(encoding="utf-8")
    assert ":root" not in css
    assert "--pa-" not in css

    from check_wmi_book_build import _qualified_css_selectors

    selectors = _qualified_css_selectors(css)
    assert selectors
    assert all(selector.startswith("body.pa-proof-site") for selector in selectors)

    assert "http://" not in css + js
    assert "https://" not in css + js
    assert re.search(r"(?:url\s*\(\s*['\"]?|@import\s+['\"]?)//", css, re.IGNORECASE) is None
    for sink in ("eval(", "innerHTML", "insertAdjacentHTML", "document.write", "new Function"):
        assert sink not in js
    assert "textContent" in js
    assert 'addEventListener("dblclick"' not in js
    graph_page = (EXPLORER / "graph.html").read_text(encoding="utf-8")
    assert "double-click" not in graph_page.lower()
    assert "details-panel proof link" in graph_page
    assert '<svg data-graph-svg tabindex="0" role="group"' in graph_page
    assert '<svg data-graph-svg tabindex="0" role="img"' not in graph_page
    graph_keydown = js[js.index('state.svg.addEventListener("keydown"'):]
    graph_keydown = graph_keydown[:graph_keydown.index("  function initializeDependencyGraph")]
    assert graph_keydown.index('[data-graph-open]') < graph_keydown.index('[data-graph-node]')
    ready = js.index("whenReady(function () {")
    guard = js.index('document.body.classList.contains("pa-proof-site")', ready)
    first_install = min(
        js.index(token, ready)
        for token in (
            'document.querySelectorAll("[data-proof-dashboard]")',
            'window.addEventListener("hashchange"',
        )
    )
    assert ready < guard < first_install
    assert re.search(
        r'if \((?:!document\.body \|\| )?'
        r'!document\.body\.classList\.contains\("pa-proof-site"\)\) return;',
        js[ready:first_install],
    )


def test_every_quadratic_reciprocity_proof_page_navigates_all_campaign_scales() -> None:
    revision = "75fa146ac19b"
    root_pages = ("index.html", "foundations.html", "graph.html")
    for relative in root_pages:
        page = (EXPLORER / relative).read_text(encoding="utf-8")
        assert f'href="../../grand-campaign/?v={revision}"' in page
        assert f'view=domain&amp;focus=D02&amp;v={revision}' in page
        assert f'view=family&amp;focus=F05&amp;v={revision}' in page
        assert f'view=goal&amp;focus=G043&amp;v={revision}' in page

    for theorem in _records():
        tag = theorem["tag"]
        page = (EXPLORER / "tag" / f"{tag}.html").read_text(encoding="utf-8")
        assert f'href="../../../grand-campaign/?v={revision}"' in page
        assert f'view=family&amp;focus=F05&amp;v={revision}' in page
        assert f'view=goal&amp;focus=G043&amp;v={revision}' in page
        assert f'href="../defined/tag/{tag}.html"' in page
        assert f'href="../defined/graph.html?target={tag}&amp;view=neighborhood' in page
