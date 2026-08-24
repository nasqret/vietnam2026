"""Contracts for the conservative, definition-aware Bertrand proof edition."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "peano-lab" / "py"))
sys.path.insert(0, str(REPO / "scripts"))

EXPLICIT = REPO / "book" / "_static" / "bertrand-proof-explorer"
DEFINED = EXPLICIT / "defined"
QR_DEFINED = REPO / "book" / "_static" / "pa-proof-explorer" / "defined"
ROOT_TAG = "BT0127"
CAMPAIGN_DEFINITIONS = {
    "PD0041": "Choose",
    "PD0042": "CentralBinom",
    "PD0043": "Primorial",
    "PD0044": "PowerDivides",
    "PD0045": "BoundedPowerValuation",
    "PD0046": "PowerValuation",
    "PD0047": "PrimePowerValuation",
    "PD0048": "FactorialValuation",
    "PD0049": "PowerQuotPrefix",
    "PD0050": "LegendreSum",
    "PD0051": "FloorSqrt",
    "PD0052": "CeilDivSix",
}
USED_CAMPAIGN_DEFINITIONS = {
    identifier: name
    for identifier, name in CAMPAIGN_DEFINITIONS.items()
    if identifier != "PD0047"
}


def _load(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(value, dict)
    return value


def _digest(value: str | bytes) -> str:
    return sha256(value.encode("utf-8") if isinstance(value, str) else value).hexdigest()


@pytest.fixture(scope="module")
def documents() -> dict[str, dict]:
    """Read generated artifacts once; never rebuild the complete proof in tests."""

    return {
        "manifest": _load(DEFINED / "manifest.json"),
        "corpus": _load(DEFINED / "api" / "corpus.json"),
        "graph": _load(DEFINED / "api" / "graph.json"),
        "explicit_corpus": _load(EXPLICIT / "api" / "corpus.json"),
        "explicit_graph": _load(EXPLICIT / "api" / "graph.json"),
    }


def test_campaign_registry_extends_without_mutating_quadratic_reciprocity() -> None:
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.kernel.terms import ParseError
    from peano_lab.library.bertrand_defined_edition import (
        ALL_BERTRAND_DEFINITIONS,
        BERTRAND_DEFINITIONS,
        definition_json_records,
    )
    from peano_lab.library.defined_syntax import (
        DEFINITIONS,
        DEFINITIONS_BY_NAME,
        parse_defined_formula_in_context,
    )

    assert len(DEFINITIONS) == 40
    assert len(BERTRAND_DEFINITIONS) == 12
    assert len(ALL_BERTRAND_DEFINITIONS) == 52
    assert len(definition_json_records()) == 52
    assert {
        definition.stable_id: definition.name for definition in BERTRAND_DEFINITIONS
    } == CAMPAIGN_DEFINITIONS
    assert not set(CAMPAIGN_DEFINITIONS.values()) & set(DEFINITIONS_BY_NAME)

    with pytest.raises(ParseError):
        parse_formula_in_context("Choose(n,k,z)", ["n", "k", "z"])
    with pytest.raises(ParseError):
        parse_defined_formula_in_context("Choose(n,k,z)", ["n", "k", "z"])

    qr_manifest = _load(QR_DEFINED / "manifest.json")
    assert qr_manifest["theorem_count"] == 557
    assert qr_manifest["definition_count"] == 40
    assert qr_manifest["aggregate_sha256"] == (
        "0ea4fd59926f5f2c12231e7c4f7f7f3d0ef900fe61bdf7bee5c81170086a894f"
    )


@pytest.mark.parametrize(("identifier", "name"), CAMPAIGN_DEFINITIONS.items())
def test_every_campaign_alias_is_an_exact_ast_preserving_abbreviation(
    identifier: str, name: str
) -> None:
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.library.bertrand_defined_edition import (
        BERTRAND_DEFINITIONS_BY_NAME,
        compact_formula_source,
        parse_bertrand_defined_formula_in_context,
    )

    definition = BERTRAND_DEFINITIONS_BY_NAME[name]
    signature = f"{name}({','.join(definition.parameters)})"
    compact = compact_formula_source(definition.template_source)

    assert definition.stable_id == identifier
    assert compact.defined_source == signature
    assert compact.receipt.exact_ast_equivalence
    assert compact.receipt.expanded_source_sha256 == _digest(definition.template_source)
    assert compact.receipt.defined_source_sha256 == _digest(signature)
    assert [(part.kind, part.text, part.definition_id) for part in compact.parts] == [
        ("definition", signature, identifier)
    ]
    assert parse_bertrand_defined_formula_in_context(
        signature, list(definition.parameters)
    ) == parse_formula_in_context(definition.template_source, list(definition.parameters))


def test_campaign_parser_rejects_unknown_calls_arity_and_context_leaks() -> None:
    from peano_lab.kernel.formulas import parse_formula_in_context
    from peano_lab.kernel.terms import ParseError
    from peano_lab.library.bertrand_defined_edition import (
        BERTRAND_DEFINITIONS_BY_NAME,
        parse_bertrand_defined_formula_in_context,
    )

    with pytest.raises(ParseError, match="unknown Bertrand defined predicate"):
        parse_bertrand_defined_formula_in_context("InventedPredicate(n)", ["n"])
    with pytest.raises(ParseError, match="expects 3 arguments, got 2"):
        parse_bertrand_defined_formula_in_context("Choose(n,k)", ["n", "k"])
    with pytest.raises(ParseError, match=r"unknown term variable\(s\): z"):
        parse_bertrand_defined_formula_in_context("Choose(n,k,z)", ["n", "k"])

    template = BERTRAND_DEFINITIONS_BY_NAME["Choose"].template_source
    assert parse_bertrand_defined_formula_in_context(
        "forall n. Choose(n,k,z)", ["k", "z"]
    ) == parse_formula_in_context(f"forall n. {template}", ["k", "z"])


def test_campaign_tactic_compaction_preserves_exact_replay_line() -> None:
    from peano_lab.library.bertrand_defined_edition import (
        BERTRAND_DEFINITIONS_BY_NAME,
        compact_tactic_command,
    )

    definition = BERTRAND_DEFINITIONS_BY_NAME["CentralBinom"]
    exact = f"have central : {definition.template_source}"
    compact = compact_tactic_command(exact, 19)

    assert compact.line_number == 19
    assert compact.tactic == "have"
    assert compact.local_name == "central"
    assert compact.expanded_command == exact
    assert compact.defined_command == "have central : CentralBinom(n,z)"
    assert compact.proposition is not None
    assert compact.proposition.receipt.exact_ast_equivalence
    assert [part.definition_id for part in compact.parts if part.kind == "definition"] == [
        "PD0042"
    ]

    untouched = compact_tactic_command("apply bertrand_closed_upper", 20)
    assert untouched.defined_command == untouched.expanded_command
    assert untouched.proposition is None


def test_generator_rejects_missing_campaign_adapter(monkeypatch) -> None:
    import build_bertrand_defined_explorer as generator

    def missing_adapter(name: str):
        raise ModuleNotFoundError(f"No module named {name!r}", name=name)

    monkeypatch.setattr(generator.importlib, "import_module", missing_adapter)
    with pytest.raises(generator.DefinedEditionError, match="missing required Bertrand"):
        generator._adapter()


def test_manifest_freezes_exact_bertrand_sources_and_complete_file_inventory(
    documents: dict[str, dict]
) -> None:
    manifest = documents["manifest"]

    assert manifest["schema"] == "peano-lab-bertrand-defined-explorer-manifest-v1"
    assert manifest["root_name"] == "bertrand_strict"
    assert manifest["root_tag"] == ROOT_TAG
    assert manifest["theorem_count"] == 544
    assert manifest["definition_count"] == 28
    assert manifest["proof_edge_count"] == 1917
    assert manifest["notation_edge_count"] == 1510
    assert manifest["formal_line_count"] == 28410
    assert manifest["generated_file_count"] == 1124
    assert manifest["explicit_corpus_sha256"] == _digest(
        (EXPLICIT / "api" / "corpus.json").read_bytes()
    )
    assert manifest["explicit_graph_sha256"] == _digest(
        (EXPLICIT / "api" / "graph.json").read_bytes()
    )

    rows = manifest["files"]
    paths = [row["path"] for row in rows]
    assert paths == sorted(paths)
    assert len(paths) + 1 == manifest["generated_file_count"]
    assert set(paths) | {"manifest.json"} == {
        path.relative_to(DEFINED).as_posix()
        for path in DEFINED.rglob("*")
        if path.is_file()
    }
    for row in rows:
        payload = (DEFINED / row["path"]).read_bytes()
        assert len(payload) == row["bytes"]
        assert _digest(payload) == row["sha256"]
    aggregate = "\n".join(f'{row["path"]}\0{row["sha256"]}' for row in rows)
    assert _digest(aggregate) == manifest["aggregate_sha256"]


def test_selected_definitions_are_genuinely_used_with_exact_source_provenance(
    documents: dict[str, dict]
) -> None:
    corpus = documents["corpus"]
    definitions = corpus["definitions"]
    selected = {definition["id"]: definition for definition in definitions}
    all_used = {
        identifier
        for theorem in corpus["theorems"]
        for identifier in theorem["defined"]["definition_uses"]
    }

    assert len(definitions) == 28
    assert {
        identifier: selected[identifier]["name"]
        for identifier in USED_CAMPAIGN_DEFINITIONS
    } == USED_CAMPAIGN_DEFINITIONS
    assert set(USED_CAMPAIGN_DEFINITIONS) <= all_used
    assert "PD0047" not in selected
    assert "PrimePowerValuation" not in {
        definition["name"] for definition in definitions
    }
    assert selected["PD0043"]["summary"] == (
        "z is the finite product of the primes at most n."
    )
    assert {"Le", "Lt", "Dvd", "Prime", "Pow", "Factorial"} <= {
        definition["name"] for definition in definitions
    }

    preceding: set[str] = set()
    source_hashes: dict[Path, str] = {}
    for definition in definitions:
        assert re.fullmatch(r"PD[0-9A-Y]{4}", definition["id"])
        assert set(definition["dependencies"]) <= preceding
        assert _digest(definition["expansion"]) == definition["expansion_sha256"]
        source = REPO / definition["source"]["path"]
        actual = source_hashes.setdefault(source, _digest(source.read_bytes()))
        assert actual == definition["source"]["sha256"]
        assert definition["source"]["line"] > 0
        preceding.add(definition["id"])

    campaign_theorems = [
        theorem
        for theorem in corpus["theorems"]
        if set(theorem["defined"]["definition_uses"]) & set(USED_CAMPAIGN_DEFINITIONS)
    ]
    assert len(campaign_theorems) == 174


def test_all_theorems_and_tactic_lines_preserve_immutable_explicit_sources(
    documents: dict[str, dict]
) -> None:
    corpus = documents["corpus"]
    explicit = documents["explicit_corpus"]
    exact_characters = 0
    compact_characters = 0
    compacted_statements = 0
    compacted_lines = 0
    line_count = 0

    assert corpus["schema"] == "peano-lab-bertrand-defined-corpus-v1"
    assert corpus["theorem_count"] == len(corpus["theorems"]) == 544
    assert corpus["root_tag"] == ROOT_TAG
    assert corpus["public_count"] == explicit["public_count"] == 203
    assert corpus["candidate_count"] == explicit["candidate_count"] == 341

    for readable, exact in zip(corpus["theorems"], explicit["theorems"], strict=True):
        defined = readable["defined"]
        assert readable["tag"] == exact["tag"]
        assert readable["name"] == exact["name"]
        assert readable["scope"] == exact["scope"]
        assert readable["status"] == exact["status"]
        assert readable["layer"] == exact["layer"]
        assert readable["dependencies"] == exact["dependencies"]
        assert readable["dependents"] == exact["dependents"]
        assert readable["explicit_statement"] == exact["statement"]
        assert (
            readable["explicit_statement_sha256"]
            == defined["expanded_statement_sha256"]
            == exact["statement_sha256"]
            == _digest(exact["statement"])
        )
        assert "".join(part["text"] for part in defined["statement_parts"]) == (
            defined["defined_statement"]
        )

        statement_uses = Counter(
            part["definition"]
            for part in defined["statement_parts"]
            if part["kind"] == "definition"
        )
        script_uses: Counter[str] = Counter()
        for readable_line, exact_line in zip(
            defined["defined_script_lines"], exact["lines"], strict=True
        ):
            line_count += 1
            assert readable_line["number"] == exact_line["number"]
            assert readable_line["expanded_command_sha256"] == _digest(
                exact_line["text"]
            )
            assert "".join(part["text"] for part in readable_line["command_parts"]) == (
                readable_line["defined_command"]
            )
            line_uses = Counter(
                part["definition"]
                for part in readable_line["command_parts"]
                if part["kind"] == "definition"
            )
            script_uses.update(line_uses)
            if readable_line["defined_command"] != exact_line["text"]:
                compacted_lines += 1
                assert exact_line["tactic"] in {"have", "suffices"}
                assert line_uses

        assert dict(sorted(statement_uses.items())) == defined["statement_definition_uses"]
        assert dict(sorted(script_uses.items())) == defined["script_definition_uses"]
        assert dict(sorted((statement_uses + script_uses).items())) == (
            defined["definition_uses"]
        )
        exact_characters += len(exact["statement"])
        compact_characters += len(defined["defined_statement"])
        compacted_statements += defined["defined_statement"] != exact["statement"]

    assert line_count == 28410
    assert compacted_statements == 496
    assert compacted_lines == 1464
    assert exact_characters == 3_450_710
    assert compact_characters == 55_835
    assert compact_characters * 50 < exact_characters


def test_used_campaign_definitions_expand_exactly_inside_real_theorems(
    documents: dict[str, dict]
) -> None:
    from peano_lab.kernel.formulas import parse_formula_with_names
    from peano_lab.library.bertrand_defined_edition import (
        parse_bertrand_defined_formula_with_names,
    )

    corpus = documents["corpus"]
    for identifier in USED_CAMPAIGN_DEFINITIONS:
        candidates = [
            theorem
            for theorem in corpus["theorems"]
            if identifier in theorem["defined"]["statement_definition_uses"]
        ]
        assert candidates, f"campaign definition {identifier} has no real statement use"
        theorem = min(candidates, key=lambda item: len(item["explicit_statement"]))
        exact_formula, exact_names = parse_formula_with_names(
            theorem["explicit_statement"]
        )
        readable_formula, readable_names = parse_bertrand_defined_formula_with_names(
            theorem["defined"]["defined_statement"]
        )

        assert readable_names == exact_names
        assert readable_formula == exact_formula
        assert USED_CAMPAIGN_DEFINITIONS[identifier] + "(" in (
            theorem["defined"]["defined_statement"]
        )


def test_mixed_graph_keeps_proof_paths_distinct_from_notation_edges(
    documents: dict[str, dict]
) -> None:
    graph = documents["graph"]
    explicit_graph = documents["explicit_graph"]
    manifest = documents["manifest"]
    edges_by_kind = Counter(edge["kind"] for edge in graph["edges"])
    nodes_by_kind = Counter(node["kind"] for node in graph["nodes"])

    assert graph["schema"] == "peano-lab-bertrand-defined-graph-v1"
    assert graph["root_tag"] == ROOT_TAG
    assert graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["proof_adjacency"] == explicit_graph["adjacency"]
    assert nodes_by_kind == {"theorem": 544, "definition": 28}
    assert edges_by_kind == {
        "proof_dependency": 1917,
        "uses_definition": 1468,
        "definition_uses_definition": 42,
    }
    assert graph["proof_edge_count"] == manifest["proof_edge_count"]
    assert graph["notation_edge_count"] == manifest["notation_edge_count"]
    assert graph["notation_edge_count"] == (
        edges_by_kind["uses_definition"] + edges_by_kind["definition_uses_definition"]
    )

    proof = graph["proof_adjacency"][ROOT_TAG]
    assert len(proof["ancestors"]) == 543
    assert len(proof["critical_root_path"]) == 45
    assert proof["root_path_count"] == 441608
    assert all(tag.startswith("BT") for tag in proof["critical_root_path"])
    assert "PD0047" not in graph["notation_adjacency"]

    exact_edges = {
        (edge["dependency"], edge["dependent"])
        for edge in explicit_graph["edges"]
    }
    mixed_proof_edges = {
        (edge["source"], edge["target"])
        for edge in graph["edges"]
        if edge["kind"] == "proof_dependency"
    }
    assert mixed_proof_edges == exact_edges

    for edge in graph["edges"]:
        if edge["kind"] == "uses_definition":
            assert edge["source"].startswith("BT")
            assert edge["target"].startswith("PD")
            assert edge["occurrence_count"] == (
                edge["statement_occurrences"]
                + edge["local_proposition_occurrences"]
            )
        elif edge["kind"] == "definition_uses_definition":
            assert edge["source"].startswith("PD")
            assert edge["target"].startswith("PD")


def test_every_theorem_and_selected_definition_has_linked_reading_pages(
    documents: dict[str, dict]
) -> None:
    corpus = documents["corpus"]
    manifest = documents["manifest"]
    manifest_paths = {record["path"] for record in manifest["files"]}

    for theorem in corpus["theorems"]:
        assert f'tag/{theorem["tag"]}.html' in manifest_paths
        assert f'name/{theorem["name"]}.html' in manifest_paths
    for definition in corpus["definitions"]:
        relative = f'definition/{definition["id"]}.html'
        assert relative in manifest_paths
        page = (DEFINED / relative).read_text(encoding="utf-8")
        assert f'<h1>{definition["name"]}</h1>' in page
        assert "conservative definition" in page
        assert "not a theorem, new axiom, predicate constant, or kernel rule" in page
        assert definition["expansion_sha256"] in page
        assert definition["source"]["sha256"] in page
        for dependency in definition["dependencies"]:
            assert f'href="{dependency}.html"' in page


def test_capstone_is_readable_preserves_the_exact_statement_and_proof_lines(
    documents: dict[str, dict]
) -> None:
    corpus = documents["corpus"]
    capstone = next(theorem for theorem in corpus["theorems"] if theorem["tag"] == ROOT_TAG)
    page = (DEFINED / "tag" / f"{ROOT_TAG}.html").read_text(encoding="utf-8")

    assert capstone["name"] == "bertrand_strict"
    assert capstone["defined"]["defined_statement"] == (
        "∀ n. Lt(1,n) → ∃ x. Prime(x) ∧ (Lt(n,x) ∧ Lt(x,n + n))"
    )
    assert len(capstone["defined"]["defined_script_lines"]) == 39
    assert capstone["explicit_statement_sha256"] in page
    assert 'href="../definition/PD0002.html">Lt(' in page
    assert 'href="../definition/PD0004.html">Prime(' in page
    assert 'href="../../tag/BT0127.html"' in page
    assert "Exact native replay line" in page
    assert 'id="proof-line-0014"' in page
    assert 'id="proof-line-0039"' in page
    assert "bertrand_bp02_candidate.py" in page


def test_interactive_surface_defaults_to_the_capstone_and_local_pinned_assets() -> None:
    import build_pa_defined_explorer as shared

    index = (DEFINED / "index.html").read_text(encoding="utf-8")
    graph = (DEFINED / "graph.html").read_text(encoding="utf-8")

    assert "544" in index
    assert "28" in index
    for name in (
        "Choose",
        "CentralBinom",
        "Primorial",
        "PowerValuation",
        "FactorialValuation",
        "LegendreSum",
        "FloorSqrt",
    ):
        assert name in index
    assert 'value="BT0127"' in graph
    assert '<option value="neighborhood" selected>' in graph
    assert '<option value="selected" selected>Selected node only</option>' in graph
    assert '<option value="focus" selected>Focused: path + selected node</option>' in graph
    assert "Proof arrows and notation arrows are different relations" in graph

    for relative, digest in shared.PINNED_ASSETS.items():
        payload = (DEFINED / relative).read_bytes()
        assert _digest(payload) == digest
        assert not re.search(rb"https?://", payload)
