"""Deterministic contracts for the generated native-PA Proof Explorer."""

from __future__ import annotations

from hashlib import sha256
from html.parser import HTMLParser
import html
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit


REPO = Path(__file__).resolve().parents[3]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(REPO / "scripts"))
EXPLORER = REPO / "book" / "_static" / "pa-proof-explorer"
MANIFEST = EXPLORER / "manifest.json"
CORPUS = EXPLORER / "api" / "corpus.json"
GRAPH = EXPLORER / "api" / "graph.json"
GRAPH_SCHEMA = EXPLORER / "api" / "graph.schema.json"
TAGS = REPO / "research" / "arithmetic-library" / "pa-proof-tags.json"
INFORMAL = REPO / "research" / "arithmetic-library" / "pa-proof-informal.json"
GENERATOR = REPO / "scripts" / "build_pa_proof_explorer.py"

THEOREM_COUNT = 557
EDGE_COUNT = 1_791
LAYER_COUNT = 45
FORMAL_LINE_COUNT = 27_491
PUBLIC_COUNT = 240
CANDIDATE_COUNT = 317
EXPLICIT_EDGE_COUNT = 1_784
IMPLICIT_EDGE_COUNT = 7
EXPLICIT_REFERENCE_COUNT = 8_557
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
    assert not generator._check(files)

    generator._write(files)
    assert {
        str(path.relative_to(tmp_path))
        for path in tmp_path.rglob("*")
        if path.is_file()
    } == set(files) | {"defined/manifest.json"}
    assert defined.read_bytes() == b'{"owned_by":"defined-generator"}\n'
    assert generator._check(files)


def test_manifest_pins_the_exact_qr_closure_and_truthful_partition() -> None:
    manifest = _load(MANIFEST)
    records = _records()
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
    root = next(row for row in records if row["name"] == "quadratic_reciprocity_combined")
    assert root["status"] == "pending_layered_closure"
    root_page = (EXPLORER / "tag" / f"{root['tag']}.html").read_text(encoding="utf-8")
    assert "pa-status-candidate" in root_page
    assert "pending" in root_page.lower()
    assert "not publicly admitted" in root_page.lower()
    assert "pa-status-public" not in root_page


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
    assert adjacency[qr_tag]["root_path_count"] == 101_293


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
        "graph.html", "api/graph.json", "api/graph.schema.json",
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
        and path.relative_to(EXPLORER).parts[0] not in {"defined"}
    }
    assert on_disk == set(manifest_files) | {"manifest.json"}


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
