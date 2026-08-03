"""Contracts for the parallel, definition-aware PA Proof Explorer."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
PY_ROOT = REPO / "peano-lab" / "py"
sys.path.insert(0, str(PY_ROOT))
sys.path.insert(0, str(REPO / "scripts"))

DEFINED = REPO / "book" / "_static" / "pa-proof-explorer" / "defined"
EXPLICIT = REPO / "book" / "_static" / "pa-proof-explorer"
THEOREM_COUNT = 557
DEFINITION_COUNT = 40
PD_PATTERN = re.compile(r"^PD[0-9A-Y]{4}$")


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


@pytest.fixture(scope="module")
def built() -> tuple[dict[str, bytes], dict, dict]:
    import build_pa_defined_explorer as generator
    from peano_lab.library.defined_edition import build_defined_edition

    raw = build_defined_edition()
    files, manifest = generator.build_files(raw)
    return files, manifest, raw


class _Text(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.text: list[str] = []
        self.starts: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        self.starts.append((tag, dict(attrs)))

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def test_adapter_validation_covers_exact_corpus_and_rejects_script_drift(built) -> None:
    import build_pa_defined_explorer as generator

    _files, _manifest, raw = built
    explicit = _load(EXPLICIT / "api" / "corpus.json")["theorems"]
    normalized = generator.validate_edition(raw, explicit)
    assert len(normalized["theorems"]) == THEOREM_COUNT
    assert len(normalized["definitions"]) == DEFINITION_COUNT
    assert [row["name"] for row in normalized["theorems"]] == [
        row["name"] for row in explicit
    ]
    definition_ids = [row["id"] for row in normalized["definitions"]]
    assert len(definition_ids) == len(set(definition_ids)) == DEFINITION_COUNT
    assert all(PD_PATTERN.fullmatch(item) for item in definition_ids)

    corrupted = deepcopy(raw)
    corrupted["theorems"][0]["defined_script_lines"][0][
        "expanded_command_sha256"
    ] = "0" * 64
    with pytest.raises(generator.DefinedEditionError, match="explicit tactic command"):
        generator.validate_edition(corrupted, explicit)


def test_generated_pages_cover_all_theorems_and_definitions(built) -> None:
    files, manifest, _raw = built
    tags = [path for path in files if path.startswith("tag/")]
    names = [path for path in files if path.startswith("name/")]
    definitions = [path for path in files if path.startswith("definition/")]
    assert len(tags) == len(names) == THEOREM_COUNT
    assert len(definitions) == DEFINITION_COUNT
    assert len(set(definitions)) == DEFINITION_COUNT
    assert all(
        PD_PATTERN.fullmatch(Path(path).stem)
        for path in definitions
    )
    assert manifest["theorem_count"] == THEOREM_COUNT
    assert manifest["definition_count"] == DEFINITION_COUNT
    assert manifest["generated_file_count"] == len(files)
    for path in definitions:
        page = files[path].decode("utf-8")
        assert "conservative definition" in page
        assert "not a theorem, axiom, predicate constant, or kernel rule" in page


def test_mixed_graph_has_typed_edges_and_theorem_only_paths(built) -> None:
    files, manifest, _raw = built
    graph = json.loads(files["api/graph.json"])
    explicit_graph = _load(EXPLICIT / "api" / "graph.json")
    assert graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["proof_adjacency"] == explicit_graph["adjacency"]
    assert graph["proof_edge_count"] == len(explicit_graph["edges"])
    assert graph["notation_edge_count"] == manifest["notation_edge_count"]
    kinds = {edge["kind"] for edge in graph["edges"]}
    assert kinds == {
        "proof_dependency",
        "uses_definition",
        "definition_uses_definition",
    }
    for tag, adjacency in graph["proof_adjacency"].items():
        assert tag.startswith("PA")
        assert all(
            value.startswith("PA")
            for key in ("dependencies", "dependents", "critical_root_path")
            for value in adjacency[key]
        )
    for edge in graph["edges"]:
        if edge["kind"] == "uses_definition":
            assert edge["source"].startswith("PA")
            assert PD_PATTERN.fullmatch(edge["target"])
            assert edge["occurrence_count"] == (
                edge["statement_occurrences"]
                + edge["local_proposition_occurrences"]
            )

    script = files["assets/explorer.js"].decode("utf-8")
    critical = script[script.index("function criticalPath"):script.index("function addDefinitionClosure")]
    assert "proof_adjacency" in critical
    assert "notation" not in critical
    assert 'svgElement("polygon"' in script


def test_mixed_graph_ui_defaults_to_selected_definitions_and_focused_arrows(built) -> None:
    files, _manifest, _raw = built
    graph = json.loads(files["api/graph.json"])
    target = "PA00FW"
    proof = graph["proof_adjacency"][target]
    theorem_ids = {target, *proof["dependencies"], *proof["dependents"]}
    ids = set(theorem_ids)
    pending = [target]
    while pending:
        source = pending.pop()
        for definition_id in graph["notation_adjacency"][source]["uses"]:
            if definition_id not in ids:
                ids.add(definition_id)
                pending.append(definition_id)
    available = [
        edge for edge in graph["edges"]
        if edge["source"] in ids and edge["target"] in ids
    ]
    route = set(zip(proof["critical_root_path"], proof["critical_root_path"][1:]))
    displayed = [
        edge for edge in available
        if edge["source"] == target
        or edge["target"] == target
        or (
            edge["kind"] == "proof_dependency"
            and (edge["source"], edge["target"]) in route
        )
    ]
    assert len(theorem_ids) == 4
    assert len(ids - theorem_ids) == 7
    assert len(available) == 26
    assert len(displayed) == 10

    page = files["graph.html"].decode("utf-8")
    assert '<option value="neighborhood" selected>' in page
    assert '<option value="selected" selected>Selected node only</option>' in page
    assert '<option value="focus" selected>Focused: path + selected node</option>' in page
    assert "Sparse modes suppress visual objects only" in page
    assert 'data-graph-title tabindex="-1"' in page
    for label in ("Zoom in", "Zoom out", "Fit graph"):
        assert f'aria-label="{label}"' in page

    script = files["assets/explorer.js"].decode("utf-8")
    assert 'function displayedEdges(state, selection)' in script
    assert 'definitionMode = "selected"' in script
    assert 'edgeMode = ["focus", "none", "all"]' in script
    assert ': "neighborhood"' in script
    assert 'visible.length > 160' in script
    assert 'selection.displayedEdges.length + " of " + selection.edges.length' in script


def test_assets_are_pinned_local_scoped_and_avoid_unsafe_sinks(built) -> None:
    import build_pa_defined_explorer as generator

    files, _manifest, _raw = built
    for relative, expected in generator.PINNED_ASSETS.items():
        payload = files[relative]
        assert sha256(payload).hexdigest() == expected
        assert not re.search(rb"https?://", payload)
    javascript = files["assets/explorer.js"].decode("utf-8")
    assert "innerHTML" not in javascript
    assert "outerHTML" not in javascript
    assert "document.write" not in javascript
    assert "eval(" not in javascript

    css = files["assets/explorer.css"].decode("utf-8")
    # Every selector list begins at a scoped body selector; declaration,
    # at-rule, keyframe-percentage, and continuation lines are excluded.
    selector_starts = [
        line.strip()
        for line in css.splitlines()
        if line and not line[0].isspace() and line.rstrip().endswith("{")
        and not line.lstrip().startswith("@")
        and not re.match(r"^(from|to|[0-9]+%)\s*\{$", line.strip())
    ]
    assert selector_starts
    assert all(line.startswith("body.pa-defined-proof-site") for line in selector_starts)


def test_compacted_have_or_suffices_lines_link_definition_and_reveal_exact_line(built) -> None:
    files, _manifest, _raw = built
    corpus = json.loads(files["api/corpus.json"])
    explicit_by_tag = {
        row["tag"]: row
        for row in _load(EXPLICIT / "api" / "corpus.json")["theorems"]
    }
    changed = None
    for theorem in corpus["theorems"]:
        explicit_row = explicit_by_tag[theorem["tag"]]
        for explicit_line, defined_line in zip(
            explicit_row["lines"], theorem["defined"]["defined_script_lines"], strict=True
        ):
            if defined_line["defined_command"] != explicit_line["text"]:
                changed = theorem, explicit_line, defined_line
                break
        if changed:
            break
    assert changed is not None, "the defined edition must compact at least one local proposition"
    theorem, explicit_line, defined_line = changed
    assert explicit_line["tactic"] in {"have", "suffices"}
    definition_parts = [
        part for part in defined_line["command_parts"] if part["kind"] == "definition"
    ]
    assert definition_parts

    page = files[f'tag/{theorem["tag"]}.html'].decode("utf-8")
    parser = _Text()
    parser.feed(page)
    text = "".join(parser.text)
    assert defined_line["defined_command"] in text
    assert explicit_line["text"] in text
    assert "Exact native replay line" in text
    assert any(
        tag == "a"
        and attrs.get("class") == "pd-definition-ref"
        and attrs.get("href")
        == f'../definition/{definition_parts[0]["definition"]}.html'
        for tag, attrs in parser.starts
    )
    assert f'data-line="{explicit_line["number"]}"' in page
    assert 'data-defined-changed="true"' in page


def test_manifest_is_byte_current_and_check_prune_are_deterministic(built, tmp_path) -> None:
    import build_pa_defined_explorer as generator

    files, manifest, _raw = built
    assert generator._check(files, DEFINED)
    committed_manifest = _load(DEFINED / "manifest.json")
    assert committed_manifest == manifest
    assert files["manifest.json"] == (DEFINED / "manifest.json").read_bytes()

    generated_rows = manifest["files"]
    assert {
        row["path"]: row["sha256"] for row in generated_rows
    } == {
        path: sha256(payload).hexdigest()
        for path, payload in files.items()
        if path != "manifest.json"
    }
    extra = tmp_path / "assets" / "unexpected.js"
    extra.parent.mkdir(parents=True)
    extra.write_text("unexpected\n", encoding="utf-8")
    assert not generator._check(files, tmp_path)
    generator._write(files, tmp_path)
    assert generator._check(files, tmp_path)
    assert not extra.exists()
