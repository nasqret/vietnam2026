"""Exact polynomial reader contracts, with no stored-report proof authority.

Collected cases below use source syntax, literal installed metadata observations,
or always-rejecting guards.  The root publication phase calls the content
assertions on its genuine same-live files; ordinary installed-page observations
may call the private content-only seam, but can never authorize a new reader build.
"""

from __future__ import annotations

import ast
from collections import Counter
from collections.abc import Mapping
from copy import deepcopy
from dataclasses import fields, is_dataclass
from hashlib import sha256
from html import unescape
from html.parser import HTMLParser
import inspect
import json
from pathlib import Path
import posixpath
import re
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

import build_constructive_polynomial_euclidean_explorer_v33 as builder
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names


ROOT = Path(__file__).resolve().parents[3]
ALL = builder.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
ROWS = builder.specs()
SLUG = "polynomial-euclidean-division"
EXPECTED_ROOTS = (
    "prime_field_polynomial_division_execution_functional",
    "prime_field_polynomial_division_execution_exists_unique",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent",
    "prime_field_polynomial_convolution_both_left_paddings_exists",
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
ACTUAL_EVIDENCE_MUTATIONS = (
    "alpha_count", "stable_count", "default_channel", "catalog_hash", "revision",
    "promoted_order", "family_scope", "new_count", "new_count_bool", "spec_hash",
    "missing_body", "body_order", "owned_id", "body_metric", "body_statement_hash",
    "bundle_path", "bundle_bytes", "bundle_sha", "bundle_nodes", "bundle_edges",
    "bundle_body_nodes", "packaging_root", "kernel_calls", "ha_false", "lean_false",
    "principal_missing", "principal_order", "principal_false", "principal_node",
    "principal_nodes_bool", "principal_statement", "source_path", "source_hash",
    "first_admission", "stable_promotion", "script_changed", "dependency_changed",
    "statement_changed", "closure_bundle", "closure_mode",
)


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


def _literal_context(context):
    """One-way plain observation for reject-only mutation probes."""
    catalog = dict(context.catalog)
    catalog["theorems"] = list(catalog["theorems"])
    return SimpleNamespace(catalog=catalog, channels=deepcopy(dict(context.channels)),
        families=deepcopy(dict(context.families)), catalog_sha256=context.catalog_sha256,
        revision=context.revision, promoted_names=tuple(context.promoted_names),
        source_binding_sha256=context.source_binding_sha256,
        observation_only=True)


def _mutated(context, attack):
    value = _literal_context(context)
    report = value.families[SLUG]
    if attack == "alpha_count": value.catalog["checked_use_count"] = 4091
    elif attack == "stable_count": value.catalog["stable_count"] = 433
    elif attack == "default_channel": value.channels["default_channel"] = "alpha"
    elif attack == "catalog_hash": value.catalog_sha256 = "0" * 64
    elif attack == "revision": value.revision = "bad"
    elif attack == "promoted_order": value.promoted_names = tuple(reversed(value.promoted_names))
    elif attack == "family_scope": value.families["unregistered"] = {}
    elif attack == "new_count": report["new_theorem_count"] = 120
    elif attack == "new_count_bool": report["new_theorem_count"] = True
    elif attack == "spec_hash": report["specs_sha256"] = "0" * 64
    elif attack == "missing_body": report["rows"].pop()
    elif attack == "body_order": report["rows"].reverse()
    elif attack == "owned_id": report["owned_node_ids"][ROWS[-1].name] = 0
    elif attack == "body_metric": report["rows"][-1]["proof_depth"] += 1
    elif attack == "body_statement_hash": report["rows"][-1]["statement_sha256"] = "0" * 64
    elif attack.startswith("bundle_") or attack in {"packaging_root", "kernel_calls", "ha_false", "lean_false"}:
        changes = {"bundle_path": ("path", "../foreign.json"), "bundle_bytes": ("bytes", 1),
            "bundle_sha": ("sha256", "0" * 64), "bundle_nodes": ("nodes_including_packaging_root", 376),
            "bundle_edges": ("dependency_edges_including_packaging", 1070),
            "bundle_body_nodes": ("body_proof_nodes", 30526), "packaging_root": ("packaging_root_id", 375),
            "kernel_calls": ("kernel_calls", 376), "ha_false": ("original_ha_checked", False),
            "lean_false": ("independent_lean_checked", False)}
        key, replacement = changes[attack]
        report["bundle"][key] = replacement
    elif attack == "principal_missing": report["principal_roots"].pop()
    elif attack == "principal_order": report["principal_roots"].reverse()
    elif attack == "principal_false": report["principal_roots"][0]["complete_ordinary_ha_checked"] = False
    elif attack == "principal_node": report["principal_roots"][0]["node_id"] = 0
    elif attack == "principal_nodes_bool": report["principal_roots"][0]["ordinary_certificate_nodes"] = True
    elif attack == "principal_statement": report["principal_roots"][0]["statement_sha256"] = "0" * 64
    else:
        row = deepcopy(dict(value.catalog["theorems"][-1]))
        value.catalog["theorems"][-1] = row
        if attack == "source_path": row["source"]["path"] = "scripts/foreign.py"
        elif attack == "source_hash": row["source"]["sha256"] = "0" * 64
        elif attack == "first_admission": row["alpha_v33_frontier_enrollment"]["first_enrolled_version"] = "v32"
        elif attack == "stable_promotion": row["membership"] = "stable"
        elif attack == "script_changed": row["script"][0] += " changed"
        elif attack == "dependency_changed": row["dependencies"].append("unregistered_polynomial_parent")
        elif attack == "statement_changed": row["statement"] = "0=S 0"
        elif attack == "closure_bundle": row["empty_context_closure"]["certificate_sha256"] = "0" * 64
        elif attack == "closure_mode": row["empty_context_closure"]["kernel_mode"] = "classical"
        else: raise AssertionError("unregistered negative observation: " + attack)
    return value


def _assert_actual_evidence_mutations_rejected(context):
    """Only corrupt genuine observed data, never supply positive proof mocks."""
    original = builder.json_bytes(context.families)
    for attack in ACTUAL_EVIDENCE_MUTATIONS:
        value = _mutated(context, attack)
        assert type(value) is SimpleNamespace and not hasattr(value, "require_unchanged")
        with pytest.raises(builder.ExplorerError):
            builder._validate_data(value)
    assert builder.json_bytes(context.families) == original


def _assert_published_content(files, context):
    """Private assertions on actual bytes; no live capability is minted."""
    assert type(files) is dict and files
    assert all(type(name) is str and builder.transport.safe_relative(name)
               and type(raw) is bytes and raw for name, raw in files.items())
    manifest = builder.strict_json(files["manifest.json"])
    assert manifest["schema"] == "peano-lab-alpha-v33-canonical-publication-v1-manifest"
    assert manifest["phase"] == "polynomial"
    assert manifest["publication_scope"] == "alpha_checked_use_publication"
    assert manifest["alpha_edition_version"] == manifest["alpha_first_enrolled_version"] == "v33"
    assert manifest["alpha_edition_checked_use_count"] == 4092 and manifest["stable_edition_count"] == 432
    assert manifest["theorem_count"] == manifest["checked_use_count"] == manifest["new_theorem_count"] == 121
    assert manifest["stable_count"] == 0 and manifest["inherited_support_count"] == 255
    assert manifest["ordinary_principal_count"] == 8
    assert manifest["families"] == [builder.family_metadata()]
    assert manifest["catalog_sha256"] == context.catalog_sha256
    assert manifest["edition_identity_sha256"] == context.catalog["edition_identity_sha256"]
    assert manifest["html_revision"] == context.revision == context.catalog_sha256[:12]
    assert manifest["release_source_binding_sha256"] == context.source_binding_sha256
    if hasattr(context, "render_source_binding_sha256"):
        assert manifest["render_source_binding_sha256"] == context.render_source_binding_sha256
    assert manifest["current_G009_multiplicative_closure_proved"] is True
    assert manifest["current_G091_prime_power_fields_proved"] is False
    assert manifest["files"] == {name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
                                 for name, raw in sorted(files.items()) if name != "manifest.json"}
    assert manifest["file_count_excluding_manifest"] == len(files) - 1
    for name, expected in {**builder.render.ASSET_DIGESTS,
                          "proofs.css": "44ac9983416435ac33efada9eaa3ff914588845fe55932f5e8c54623b28c9285"}.items():
        assert sha256(files["assets/" + name]).hexdigest() == expected
    base = SLUG + "/"
    corpus = builder.strict_json(files[base + "api/corpus.json"])
    graph = builder.strict_json(files[base + "api/graph.json"])
    assert files[base + "api/graph.json"] == files[base + "explorer/defined/api/graph.json"]
    report = context.families[SLUG]
    assert corpus["checkpoint_report"] == corpus["first_alpha_admission_report"] == report
    assert builder.strict_json(files[base + "api/checkpoint.json"]) == report
    assert builder.strict_json(files[base + "api/first-admission.json"]) == context.catalog["theorems"][3971:]
    assert report["new_theorem_count"] == 121 and report["specs_sha256"] == builder.SPECS_SHA256
    assert tuple(row["name"] for row in report["principal_roots"]) == EXPECTED_ROOTS
    assert tuple(row["node_id"] for row in report["principal_roots"]) == (343, 344, 366, 367, 368, 371, 372, 375)
    assert all(row["complete_ordinary_ha_checked"] is True
               and type(row["ordinary_certificate_nodes"]) is int and row["ordinary_certificate_nodes"] > 0
               for row in report["principal_roots"])
    bundle = report["bundle"]
    assert bundle["original_ha_checked"] is bundle["independent_lean_checked"] is True
    assert bundle["kernel_calls"] == bundle["nodes_including_packaging_root"] == 377
    assert bundle["packaging_root_id"] == 376
    assert bundle["dependency_edges_including_packaging"] == 1071 and bundle["body_proof_nodes"] == 30527
    payload = files["artifacts/" + Path(bundle["path"]).name]
    assert len(payload) == bundle["bytes"] == 2449379
    assert sha256(payload).hexdigest() == bundle["sha256"] == builder.BUNDLE_SHA256
    tags = {row.name: f"PX{index:04X}" for index, row in enumerate(ROWS, 1)}
    assert corpus["tags"] == tags and tuple(row["name"] for row in corpus["nodes"]) == tuple(tags)
    assert corpus["node_count"] == corpus["new_theorem_count"] == 121
    assert corpus["alpha_checked_use_node_count"] == corpus["alpha_enrolled_node_count"] == 121
    assert corpus["inherited_support_count"] == 255 and corpus["complete_theorem_count"] == 376
    assert corpus["stable_admitted_node_count"] == 0
    assert corpus["edge_count"] == 461 and corpus["formal_line_count"] == 9068
    assert corpus["alpha_edition_version"] == corpus["alpha_first_enrolled_version"] == "v33"
    assert corpus["alpha_catalog_sha256"] == corpus["alpha_first_enrollment_catalog_sha256"] == context.catalog_sha256
    assert corpus["root_names"] == list(EXPECTED_ROOTS) and corpus["reserved_tag_slots"] == {}
    for field in ("current_G091_prime_power_fields_proved", "arbitrary_formal_identity_quotient_uniqueness_proved",
                  "convolution_associativity_proved", "polynomial_gcd_bezout_proved"):
        assert corpus[field] is False
    by_name = {row["name"]: row for row in context.catalog["theorems"]}
    body_by_name = {row["name"]: row for row in report["rows"]}
    definitions = {row["id"]: row for row in corpus["definitions"]}
    assert corpus["definition_count"] == len(definitions) == len(corpus["definitions"])
    assert {f"ND{index:04d}" for index in range(334, 341)} <= definitions.keys()
    assert not any(row["name"] == "PolynomialShift" for row in definitions.values())
    all_used = set()
    for spec, node in zip(ROWS, corpus["nodes"], strict=True):
        actual, measured = by_name[spec.name], body_by_name[spec.name]
        assert node["id"] == tags[spec.name] and node["summary"] == spec.summary == actual["summary"]
        assert node["statement"] == spec.statement == actual["statement"]
        assert node["script"] == list(spec.script) == actual["script"]
        assert node["dependencies"] == list(spec.dependencies) == actual["dependencies"]
        assert node["statement_sha256"] == sha256(spec.statement.encode()).hexdigest() == actual["statement_sha256"]
        assert node["script_sha256"] == sha256(("\n".join(spec.script) + "\n").encode()).hexdigest() == actual["script_sha256"]
        assert node["checked_use"] is node["alpha_checked_use"] is node["enrolled_in_alpha"] is node["admitted_to_alpha"] is True
        assert node["stable_member"] is node["admitted_to_stable"] is False
        assert node["alpha_edition_version"] == node["alpha_first_enrolled_version"] == "v33"
        assert node["proof_bundle_node_id"] == report["owned_node_ids"][spec.name] == measured["node_id"]
        assert node["body_proof_nodes"] == measured["proof_nodes"] and node["body_proof_depth"] == measured["proof_depth"]
        assert node["proof_bundle_sha256"] == builder.BUNDLE_SHA256
        assert node["sources"][0]["source_sha256"] == actual["source"]["sha256"]
        assert node["sources"][0]["selected"] is True and len(node["sources"]) == 1
        assert actual["source"]["path"] == "peano-lab/py/peano_lab/library/" + node["source_filename"]
        _assert_reading(spec, node["defined"])
        all_used.update(node["defined"]["definition_uses"])
        for prefix, commands in (("explorer/tag/", spec.script), ("explorer/defined/tag/", node["defined"]["defined_script"])):
            raw = files[base + prefix + node["id"] + ".html"]
            page = _Page(raw)
            assert tuple(page.lines) == tuple(range(1, len(commands) + 1))
            assert ["".join(page.lines[index]) for index in page.lines] == list(commands)
            assert {f"proof-line-{index:04d}" for index in page.lines} <= page.ids
            pattern = (r'<details class="pd-expanded">.*?<pre><code>(.*?)</code></pre>'
                       if "defined/" in prefix else r'<pre id="statement"><code>(.*?)</code></pre>')
            assert unescape(re.search(pattern, raw.decode(), re.S).group(1)) == spec.statement
    assert {item.stable_id for item in builder.EUCLIDEAN_DEFINITIONS} <= all_used <= definitions.keys()
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
        assert row["global_definition"] is None and row["global_argument_positions"] is None
        assert base + "explorer/defined/definition/" + row["id"] + ".html" in files
        seen.add(row["id"])
    assert corpus["definition_topological_order"] == list(definitions)
    internal = [{"kind": "proof_dependency", "source": tags[parent], "target": tags[row.name]}
                for row in ROWS for parent in row.dependencies if parent in tags]
    notation = [{"kind": "definition_uses_definition", "source": row["id"], "target": parent}
                for row in corpus["definitions"] for parent in row["dependencies"]]
    uses = [{"kind": "uses_definition", "source": node["id"], "target": identifier,
        "occurrence_count": count, "statement_occurrences": node["defined"]["statement_definition_uses"].get(identifier, 0),
        "local_proposition_occurrences": node["defined"]["script_definition_uses"].get(identifier, 0)}
        for node in corpus["nodes"] for identifier, count in node["defined"]["definition_uses"].items()]
    assert corpus["edges"] == graph["edges"] == internal + uses + notation
    assert corpus["internal_edge_count"] == len(internal)
    assert corpus["definition_dependency_count"] == len(notation)
    assert corpus["path_policy"] == graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["root_ids"] == [tags[name] for name in EXPECTED_ROOTS]
    assert len(graph["nodes"]) == 121 + len(definitions)
    assert {row["id"] for row in graph["nodes"]} == set(tags.values()) | definitions.keys()
    edges = {(row["source"], row["target"]) for row in internal}
    for name, adjacency in corpus["proof_adjacency"].items():
        assert adjacency["dependencies"] == [parent for parent in by_name[name]["dependencies"] if parent in tags]
        assert adjacency["dependents"] == [row.name for row in ROWS if name in row.dependencies]
        path = adjacency["critical_root_path"]
        assert path and path[-1] == tags[name] and set(path) <= set(tags.values())
        assert all(pair in edges for pair in zip(path, path[1:]))
        assert graph["proof_adjacency"][tags[name]] == {"dependencies": [tags[parent] for parent in adjacency["dependencies"]],
            "dependents": [tags[child] for child in adjacency["dependents"]], "critical_root_path": path}
    support = corpus["external_dependencies"]
    assert len(support) == len({row["name"] for row in support}) == 255
    checkpoint = _Page(files[base + "checkpoint.html"])
    for row in support:
        actual = by_name[row["name"]]
        assert row["name"] not in tags and row["counted_as_new_owned_theorem"] is False
        assert row["inventory_role"] == "inherited_alpha_v32" and row["first_admission_reclassified"] is False
        assert row["statement"] == actual["statement"] and row["script"] == actual["script"]
        assert row["dependencies"] == actual["dependencies"] and row["source"] == actual["source"]
        assert row["stable_member"] is (actual["membership"] == "stable")
        assert "theorem-" + row["name"] in checkpoint.ids
        assert corpus["external_theorem_routes"][row["name"]] == base + "checkpoint.html#theorem-" + row["name"]
    for module, _count, size, expected in builder.FACTORIES:
        source = files["sources/" + module + ".py"]
        assert len(source) == size and sha256(source).hexdigest() == expected
    for name, raw in files.items():
        if not name.endswith(".html"):
            continue
        page = _Page(raw)
        canonical = [attrs["href"] for tag, attrs in page.tags if tag == "link" and attrs.get("rel") == "canonical"]
        assert canonical == ["https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + name.removesuffix("index.html")]
        assert raw.count(b'name="proof-publication-scope"') == 1
        assert raw.count(b'data-current-release="v33"') == 1
        for tag, attrs in page.tags:
            if tag != "a" or not attrs.get("href"):
                continue
            target = urlsplit(attrs["href"])
            if target.scheme or target.netloc or not target.path:
                continue
            relative = posixpath.normpath(posixpath.join(posixpath.dirname(name), unquote(target.path)))
            if target.path.endswith("/"):
                relative = relative.rstrip("/") + "/index.html"
            if relative == "./index.html": relative = "index.html"
            if relative.startswith("grand-campaign/"):
                assert parse_qs(target.query).get("v") == [context.revision]
                continue
            assert relative in files, (name, attrs["href"], relative)
            if relative.endswith(".html"):
                assert parse_qs(target.query).get("v") == [context.revision]
    _assert_actual_evidence_mutations_rejected(context)


def _assert_published_files(files, context):
    """Genuine live wrapper; content assertions alone never authorize output."""
    publication = builder._publication()
    publication.require_live(context)
    _assert_published_content(files, context)
    publication.require_live(context)


@pytest.fixture(scope="module")
def syntax():
    # Source ASTs only: no report, bundle, live context or checked-use claim.
    return builder._source_only_syntax()


def test_exact_source_only_family_inventory_and_alias_scope():
    metadata = builder.family_metadata()
    assert metadata == {"slug": SLUG, "title": "Prime-Field Polynomial Euclidean Division",
        "theorem_count": 121, "checked_use_count": 121, "stable_count": 0,
        "first_admitted_version": "v33", "tags": {row.name: f"PX{index:04X}" for index, row in enumerate(ROWS, 1)},
        "package": "constructive-polynomial-euclidean-explorer-v33"}
    assert builder._specs_digest(ROWS) == "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
    assert sha256("\n".join(row.name for row in ROWS).encode()).hexdigest() == "80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc"
    assert sum(len(row.dependencies) for row in ROWS) == 461
    assert sum(len(row.script) for row in ROWS) == 9068
    assert tuple(builder.PRINCIPAL_ROOTS) == EXPECTED_ROOTS
    assert len(ALL) == 397 and "PolynomialShift" not in ALL


@pytest.mark.parametrize("owner", builder.FACTORIES, ids=lambda row: row[0])
def test_each_canonical_source_is_the_exact_frozen_copy(owner):
    module, _count, size, expected = owner
    raw = builder._source("peano-lab/py/peano_lab/library/" + module + ".py", size=size, expected=expected)
    assert len(raw) == size and sha256(raw).hexdigest() == expected


@pytest.mark.parametrize("spec", ROWS, ids=lambda row: row.name)
def test_every_actual_statement_and_local_proposition_reexpands_exactly(spec, syntax):
    index = ROWS.index(spec)
    _assert_reading(spec, syntax[0][index])


@pytest.mark.parametrize("item", builder.EUCLIDEAN_DEFINITIONS, ids=lambda row: row.name)
def test_new_display_definitions_preserve_exact_reviewed_expansions(item, syntax):
    records = {row["id"]: row for row in syntax[1]}
    actual = records[item.stable_id]
    assert actual["parameters"] == list(item.parameters) and actual["expanded_template"] == item.template_source
    assert actual["dependency_names"] == list(item.conceptual_dependencies)
    _same_ast(_parse_defined(actual["defined_template"], item.parameters), item.template_formula)
    assert actual["global_definition"] is None
    assert item.stable_id in set().union(*(set(row["definition_uses"]) for row in syntax[0]))


def test_source_syntax_dag_has_only_actual_notation_edges(syntax):
    readings, definitions = syntax
    assert len(readings) == 121 and len(definitions) == 35
    assert sum(len(row["dependencies"]) for row in definitions) == 71
    assert 121 + len(definitions) == 156
    seen = set()
    for row in definitions:
        assert set(row["dependencies"]) <= seen
        assert row["id"] not in seen and row["name"] in ALL
        seen.add(row["id"])
    assert {f"ND{index:04d}" for index in range(334, 341)} <= seen


@pytest.mark.parametrize("name,node_id", tuple(zip(EXPECTED_ROOTS, (343, 344, 366, 367, 368, 371, 372, 375), strict=True)))
def test_eight_principal_tags_follow_the_actual_owned_prefix(name, node_id):
    index = next(index for index, row in enumerate(ROWS) if row.name == name)
    assert index + 255 == node_id
    assert builder.family_metadata()["tags"][name] == f"PX{index + 1:04X}"


@pytest.fixture(scope="module")
def installed_family_observation():
    """Read literal installed evidence, not a live context or a proof result."""
    raw = builder.transport.read_pinned(
        ROOT / "research/arithmetic-library/artifacts/alpha-v33-research-receipt-v1.json",
        55856, "cea85e5c595a021061fb50997df7ad489c8905ab563695209dadc8235f6762cb")
    report = builder.strict_json(raw)
    assert report["alpha_theorem_count"] == 4092 and report["stable_theorem_count"] == 432
    assert report["new_theorems"] == 121 and report["ordinary_principal_count"] == 8
    assert len(report["families"]) == 1 and report["families"][0]["slug"] == SLUG
    return report["families"][0]


def _principal_observation_inputs(report):
    # Exact source-only expectations; do not decode a bundle or load an edition.
    positions = {row.name: 255 + index for index, row in enumerate(ROWS)}
    by_name = {row.name: {"statement_sha256": sha256(row.statement.encode()).hexdigest()}
               for row in ROWS}
    return deepcopy(report["principal_roots"]), positions, by_name


def test_actual_installed_normalized_principals_match_source_without_authority(installed_family_observation):
    before = set(sys.modules)
    report = installed_family_observation
    original = builder.json_bytes(report)
    principals, positions, by_name = _principal_observation_inputs(report)
    assert all(set(row) == {"name", "node_id", "statement_sha256",
        "complete_ordinary_ha_checked", "ordinary_certificate_nodes"} for row in principals)
    assert tuple(row["name"] for row in principals) == EXPECTED_ROOTS
    assert tuple(row["ordinary_certificate_nodes"] for row in principals) == (
        8744, 19739, 16447, 16811, 8711, 10075, 10163, 17731)
    assert report["slug"] == SLUG and all("slug" not in row for row in principals)
    assert builder._validate_principal_records(principals, positions, by_name) is None
    assert builder.json_bytes(report) == original
    assert set(sys.modules) == before


@pytest.mark.parametrize("attack", (
    "none", "tuple", "missing_principal", "extra_principal", "reversed", "foreign_name",
    "nonrecord", "missing_field", "extra_field", "worker_slug_not_normalized",
    "node_changed", "node_bool", "source_position_changed", "statement_changed",
    "source_statement_changed", "unchecked", "checked_integer", "nodes_zero",
    "nodes_negative", "nodes_bool", "nodes_string",
))
def test_actual_normalized_principal_mutations_reject(installed_family_observation, attack):
    principals, positions, by_name = _principal_observation_inputs(installed_family_observation)
    first = EXPECTED_ROOTS[0]
    if attack == "none": principals = None
    elif attack == "tuple": principals = tuple(principals)
    elif attack == "missing_principal": principals.pop()
    elif attack == "extra_principal": principals.append(deepcopy(principals[0]))
    elif attack == "reversed": principals.reverse()
    elif attack == "foreign_name": principals[0]["name"] = "unverified_polynomial_root"
    elif attack == "nonrecord": principals[0] = None
    elif attack == "missing_field": del principals[0]["complete_ordinary_ha_checked"]
    elif attack == "extra_field": principals[0]["accepted"] = True
    elif attack == "worker_slug_not_normalized": principals[0]["slug"] = SLUG
    elif attack == "node_changed": principals[0]["node_id"] += 1
    elif attack == "node_bool": principals[0]["node_id"] = True
    elif attack == "source_position_changed": positions[first] += 1
    elif attack == "statement_changed": principals[0]["statement_sha256"] = "0" * 64
    elif attack == "source_statement_changed": by_name[first]["statement_sha256"] = "0" * 64
    elif attack == "unchecked": principals[0]["complete_ordinary_ha_checked"] = False
    elif attack == "checked_integer": principals[0]["complete_ordinary_ha_checked"] = 1
    elif attack == "nodes_zero": principals[0]["ordinary_certificate_nodes"] = 0
    elif attack == "nodes_negative": principals[0]["ordinary_certificate_nodes"] = -1
    elif attack == "nodes_bool": principals[0]["ordinary_certificate_nodes"] = True
    elif attack == "nodes_string": principals[0]["ordinary_certificate_nodes"] = "8744"
    else: raise AssertionError("unregistered principal observation mutation")
    with pytest.raises(builder.ExplorerError):
        builder._validate_principal_records(principals, positions, by_name)


def test_normalized_principal_check_is_used_inside_strict_enclosing_family_validation():
    tree = ast.parse(inspect.getsource(builder._validate_data))
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "_validate_principal_records"]
    assert len(calls) == 1
    assert ast.unparse(calls[0]) == "_validate_principal_records(principals, positions, by_name)"
    assert 'report.get("slug") != SLUG' in inspect.getsource(builder._validate_data)
    helper = inspect.getsource(builder._validate_principal_records)
    assert "require_live(" not in helper and "LiveReleaseContext(" not in helper
    assert "verify_in_fresh_windows" not in helper and "decode_proof_bundle" not in helper


@pytest.mark.parametrize("relative,expected", builder.TEMPLATE_PINS.items())
def test_canonical_qr_renderers_are_literal_unchanged_inputs(relative, expected):
    assert sha256(builder._source(relative, expected=expected)).hexdigest() == expected


@pytest.mark.parametrize("phrase", (
    "highest-degree-first", "Empty quotients and remainders", "never arbitrary beta codes",
    "not evaluations on a finite field", "not assumed by the execution graph",
    "Arbitrary quotient/remainder-pair uniqueness", "multiplication associativity",
    "gcd/Bezout", "full G091 prime-power-field goal remain open",
))
def test_mathematical_scope_does_not_overclaim_future_algebra(phrase):
    assert phrase in builder.family().caveat


def test_family_formula_uses_only_actual_conservative_names():
    raw = builder.family().formula.replace("⇒", "->")
    parser = _LocalDefinedParser(raw, ALL)
    formula = parser.parse()
    assert formula is not None
    assert set(re.findall(r"\b([A-Z][A-Za-z0-9_]*)\(", raw)) <= set(ALL)
    assert "FpPolynomialDivisionExecution" in raw and "Prime(p)" in raw


def test_transitive_source_binding_includes_new_and_executed_implementation_inputs():
    paths = builder.source_paths()
    assert tuple(sorted(set(paths))) == paths
    assert all(builder.transport.safe_relative(path) and (ROOT / path).is_file() for path in paths)
    assert {"scripts/constructive_polynomial_euclidean_definitions.py",
        "scripts/constructive_polynomial_euclidean_definition_graph.py",
        "scripts/constructive_polynomial_division_definitions.py",
        "scripts/constructive_g009_definitions.py", "scripts/constructive_definition_graph.py",
        "scripts/constructive_formula_compactor.py", "scripts/constructive_historical_graph_test_support.py",
        "scripts/build_constructive_completed_lower_explorer_v31.py",
        "peano-lab/py/peano_lab/library/defined_syntax.py",
        "peano-lab/py/peano_lab/library/defined_edition.py",
        "peano-lab/py/peano_lab/library/bertrand_defined_edition.py",
        "peano-lab/py/tests/test_constructive_frontier_explorer.py",
        "peano-lab/py/tests/test_constructive_historical_publication_v31.py",
        "book/_static/pa-proof-explorer/defined/assets/explorer.js",
        "book/_static/constructive-gaussian-factorization-explorer/gaussian-factorization/index.html",
        "conftest.py", "pytest.ini", "peano-lab/py/tests/conftest.py"} <= set(paths)
    assert not any("/working/" in path for path in paths)


@pytest.mark.parametrize("relative", ("/absolute.py", "../foreign.py", "scripts/../foreign.py", "scripts//foreign.py", "", "./scripts/x.py"))
def test_source_reader_rejects_unsafe_paths(relative):
    with pytest.raises(builder.ExplorerError):
        builder._source(relative)


@pytest.mark.parametrize("mutation", ("symlink_leaf", "symlink_parent", "directory", "hardlink", "empty", "too_large", "wrong_size", "wrong_hash"))
def test_source_reader_rejects_nonliteral_or_unowned_inputs(tmp_path, monkeypatch, mutation):
    root = tmp_path.resolve()
    source = root / "source.py"
    source.write_bytes(b"ordinary source\n")
    request, kwargs = "source.py", {}
    if mutation == "symlink_leaf":
        (root / "link.py").symlink_to(source)
        request = "link.py"
    elif mutation == "symlink_parent":
        (root / "link").symlink_to(root, target_is_directory=True)
        request = "link/source.py"
    elif mutation == "directory":
        (root / "directory").mkdir()
        request = "directory"
    elif mutation == "hardlink":
        (root / "second.py").hardlink_to(source)
    elif mutation == "empty": source.write_bytes(b"")
    elif mutation == "too_large": monkeypatch.setattr(builder, "MAX_SOURCE_BYTES", 3)
    elif mutation == "wrong_size": kwargs["size"] = 1
    elif mutation == "wrong_hash": kwargs["expected"] = "0" * 64
    monkeypatch.setattr(builder, "ROOT", root)
    with pytest.raises(builder.ExplorerError):
        builder._source(request, **kwargs)


@pytest.mark.parametrize("value", (None, {}, {"accepted": True}, SimpleNamespace(), b"saved report", True))
def test_public_builder_fails_at_the_original_capability_boundary(value, monkeypatch):
    reached = []
    def reject(actual):
        assert actual is value
        reached.append(actual)
        raise builder.ExplorerError("always-rejecting original-capability probe")
    monkeypatch.setattr(builder, "_publication", lambda: SimpleNamespace(require_live=reject))
    monkeypatch.setattr(builder, "_corpus", lambda *_: pytest.fail("rejecting guard reached presentation"))
    with pytest.raises(builder.ExplorerError, match="always-rejecting"):
        builder.build_files_from_live(value)
    assert len(reached) == 1


def test_live_assertion_wrapper_rejects_before_private_content(monkeypatch):
    def reject(_context):
        raise builder.ExplorerError("always-rejecting assertion boundary")
    monkeypatch.setattr(builder, "_publication", lambda: SimpleNamespace(require_live=reject))
    with pytest.raises(builder.ExplorerError, match="always-rejecting"):
        _assert_published_files({"not an output": b"not proof"}, object())


def test_public_flow_keeps_guard_before_and_after_without_writer_or_receipt_input():
    tree = ast.parse(inspect.getsource(builder.build_files_from_live))
    function = tree.body[0]
    assert [arg.arg for arg in function.args.args] == ["context"]
    assert not function.args.defaults and function.args.kwarg is None
    calls = [node for node in function.body if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call)]
    assert [ast.unparse(node.value) for node in calls] == ["publication.require_live(context)", "publication.require_live(context)"]
    assert ast.unparse(function.body[1]) == "publication = _publication()"
    assert ast.unparse(function.body[2]) == "publication.require_live(context)"
    assert ast.unparse(function.body[-2]) == "publication.require_live(context)"
    assert ast.unparse(function.body[-1]) == "return files"
    source = Path(builder.__file__).read_text()
    assert "argparse" not in source and "write_bytes(" not in source and "write_text(" not in source
    assert "decode_proof_bundle" not in source and "verify_in_fresh_windows" not in source
    assert "temporary_representation_alias" not in source and "module_from_spec" not in source


def test_private_assertions_are_explicitly_non_authorizing_and_mutations_only_reject():
    source = inspect.getsource(_assert_published_content)
    assert "require_live(" not in source and "LiveReleaseContext(" not in source
    assert len(ACTUAL_EVIDENCE_MUTATIONS) == len(set(ACTUAL_EVIDENCE_MUTATIONS)) == 40
    source = inspect.getsource(_assert_actual_evidence_mutations_rejected)
    assert "pytest.raises(builder.ExplorerError)" in source
    assert "builder._validate_data(value)" in source
    assert "builder.build_files_from_live" not in source


def test_source_only_paths_do_not_import_alpha_admission_or_working_alias_loaders():
    before = {name: module for name, module in sys.modules.items()
              if name.startswith(("peano_lab.library.editions", "check_alpha_", "verify_peano_library"))}
    tree = ast.parse(Path(builder.__file__).read_text())
    top = [node for node in tree.body if isinstance(node, (ast.Import, ast.ImportFrom))]
    names = [node.module for node in top if isinstance(node, ast.ImportFrom)]
    names.extend(alias.name for node in top if isinstance(node, ast.Import) for alias in node.names)
    assert not any(value and ("editions" in value or "check_alpha_" in value
                             or "working_" in value or "verify_peano" in value) for value in names)
    builder.family(), builder.specs(), builder.source_paths()
    assert {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_", "verify_peano_library"))} == before
