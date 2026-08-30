"""Frozen syntax/template and hostile-input checks, without proof simulation.

These tests do not fabricate an accepting release context or emit an Alpha
snapshot. Actual publication tests separately require the live v31 verifier.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_completed_lower_publication_v31 as publication
import build_constructive_completed_lower_explorer_v31 as builder


@pytest.fixture(scope="module")
def source_inputs():
    manifests = publication.authenticate_snapshots()
    return manifests, publication.frozen_corpora(manifests)


def test_exact_five_reader_generations_and_nineteen_family_inventory(source_inputs):
    manifests, corpora = source_inputs
    assert tuple(sum(count for _, count in item.families) for item in publication.SNAPSHOTS) == (170, 126, 125, 113, 40)
    assert tuple(item.file_count for item in publication.SNAPSHOTS) == (493, 371, 395, 424, 173)
    assert sum(item.file_count for item in publication.SNAPSHOTS) == 1856
    assert tuple(corpora) == publication.FAMILY_ORDER and len(corpora) == 19
    assert sum(row["node_count"] for row in corpora.values()) == 574
    assert len({row["name"] for corpus in corpora.values() for row in corpus["nodes"]}) == 574
    assert publication.PARENT_COUNT + publication.PROMOTED_COUNT == publication.CURRENT_COUNT == 3796
    assert publication.STABLE_COUNT == 432
    assert all(item.manifest_sha256 == sha256((ROOT / "book/_static" / item.directory / "manifest.json").read_bytes()).hexdigest()
               for item in publication.SNAPSHOTS)
    assert set(manifests) == {item.directory for item in publication.SNAPSHOTS}


def test_all_372_definition_identities_and_787_edges_remain_exact(source_inputs):
    _, corpora = source_inputs
    assert publication.validate_definition_identities(corpora) == {
        "definition_count": 372, "definition_dependency_count": 787,
        "definition_inventory_sha256": "ca2b9e8d0c1ca92fc136ede8f5b08005f0ff47026ff1eca7ec6a000992a18e9d",
        "definitions_are_not_proof_evidence": True,
    }


def test_atlas_metadata_preserves_reserved_and_actual_principal_tags(source_inputs):
    _, corpora = source_inputs
    families = {row["slug"]: row for row in publication.family_metadata(corpora)}
    assert len(families) == 19
    assert families["euler-units"]["tags"]["euler_theorem_for_units"] == "EU0022"
    assert "EU0003" not in families["euler-units"]["tags"].values()
    assert "EU001C" not in families["euler-units"]["tags"].values()
    assert families["mobius-inversion"]["root_tags"]["mobius_inversion_iff"] == "MI0008"
    assert families["dirichlet-inverses"]["root_names"][-1] == "dirichlet_inverse_criterion"
    assert families["dirichlet-inverses"]["root_tags"]["dirichlet_inverse_criterion"] == "IV0013"
    assert families["dirichlet-inverses"]["root_tags"]["dirichlet_inverse_exists_positive_unique"] == "IV0015"
    assert "N=0" in families["dirichlet-inverses"]["caveat"]
    assert "multiplicative" in families["dirichlet-inverses"]["caveat"].lower()
    for slug in ("prime-fields", "prime-field-polynomials", "polynomial-products"):
        assert "G091" in families[slug]["goals"] and "G091" in families[slug]["caveat"]
    for slug, family in families.items():
        assert family["tags"] == corpora[slug]["tags"]
        assert family["root_names"] == corpora[slug]["root_names"]


def test_canonical_assets_are_literal_not_new_visual_implementations(source_inputs):
    manifests, _ = source_inputs
    files = builder._asset_files(manifests)
    assert len(files) == 5
    for name, expected in builder.ASSET_DIGESTS.items():
        assert sha256(files["assets/" + name]).hexdigest() == expected
        assert files["assets/" + name] == (ROOT / "book/_static/constructive-bottom-layer-explorer/assets" / name).read_bytes()


def test_actual_three_filter_enhancement_is_reused_from_pinned_reader(source_inputs):
    manifests, _ = source_inputs
    source = builder._dashboard_enhancement(manifests)
    assert source.startswith("<script data-local-dashboard-enhancement>")
    assert source.endswith("</script>")
    assert 'root.addEventListener("input"' in source
    original = publication.snapshot_file(publication.SNAPSHOTS[0], manifests[publication.SNAPSHOTS[0].directory],
                                         "euler-units/explorer/defined/index.html").decode()
    assert source in original


def test_current_controls_preserve_original_proof_fragments_and_all_definition_layers():
    raw = b'<!doctype html><html><head></head><body><main><select data-layer><option value="all">All layers</option><option value="0">0</option></select><li class="pd-proof-line" id="L1"><a class="pd-line-number" href="#L1">0001</a><code>L1 -&gt; L2</code></li></main></body></html>'
    text = builder._CurrentHTML("euler-units/explorer/defined/index.html", "a" * 12, layer_choices=(0, 1, 4)).finish(raw).decode()
    assert '<option value="4">4</option>' in text and '<option value="1">1</option>' in text
    assert 'id="proof-line-0001"' in text and 'href="#proof-line-0001"' in text
    assert '<code>L1 -&gt; L2</code>' in text


@pytest.mark.parametrize("snapshot", publication.SNAPSHOTS, ids=lambda row: row.directory)
def test_literal_manifest_bytes_reject_same_length_change(snapshot, tmp_path):
    path = ROOT / "book/_static" / snapshot.directory / "manifest.json"
    raw = publication.read_pinned(path, snapshot.manifest_bytes, snapshot.manifest_sha256)
    assert raw.endswith(b"\n")
    altered = tmp_path / "manifest.json"
    altered.write_bytes(raw[:-1] + b" ")  # Still valid JSON; only the exact pin rejects it.
    assert json.loads(altered.read_bytes()) == json.loads(raw)
    with pytest.raises(publication.PublicationError, match="changed"):
        publication.read_pinned(altered, snapshot.manifest_bytes, snapshot.manifest_sha256)


@pytest.mark.parametrize("failure", ("missing", "symlink", "directory", "short", "extra", "bool_size", "bad_digest"))
def test_pinned_reader_input_rejects_unsafe_or_unbounded_file_shapes(failure, tmp_path):
    payload = b"literal syntax input\n"
    path = tmp_path / "input"
    size, expected = len(payload), sha256(payload).hexdigest()
    if failure == "symlink":
        source = tmp_path / "target"
        source.write_bytes(payload)
        path.symlink_to(source)
    elif failure == "directory":
        path.mkdir()
    elif failure != "missing":
        path.write_bytes(payload[:-1] if failure == "short" else payload + b"x" if failure == "extra" else payload)
    if failure == "bool_size":
        size = True
    if failure == "bad_digest":
        expected = "not a sha256"
    with pytest.raises(publication.PublicationError):
        publication.read_pinned(path, size, expected)


def test_snapshot_rejects_symlink_ancestor_before_reading_manifest(tmp_path):
    (tmp_path / "book").symlink_to(ROOT / "book", target_is_directory=True)
    with pytest.raises(publication.PublicationError, match="directory"):
        publication.snapshot_manifest(publication.SNAPSHOTS[0], root=tmp_path)


@pytest.mark.parametrize("path", ("", "/absolute", "../escape", "a/../escape", "a//b", "a\\b", "./a"))
def test_snapshot_paths_are_strictly_relative(path):
    assert not publication.safe_relative(path)


@pytest.mark.parametrize("payload", (b'{"a":1,"a":2}', b'{"n":NaN}', b'{"n":Infinity}', b'{"n":-Infinity}'))
def test_metadata_json_rejects_duplicate_keys_and_nonfinite_numbers(payload):
    with pytest.raises(publication.PublicationError):
        publication.strict_json(payload)


@pytest.mark.parametrize("field", ("id", "parameters", "expanded_template", "dependencies", "dependency_names", "exact_ast_verified"))
def test_definition_projection_rejects_identity_or_expansion_drift(field, source_inputs):
    _, corpora = source_inputs
    changed = deepcopy(corpora["dirichlet-inverses"])
    row = next(value for value in changed["definitions"] if value["name"] == "DirichletInverse")
    row[field] = {"id": "ND9999", "parameters": ["F", "N", "G"], "expanded_template": "0=0",
                  "dependencies": [], "dependency_names": [], "exact_ast_verified": False}[field]
    with pytest.raises(publication.PublicationError, match="definition identity"):
        publication.validate_definition_identities({"dirichlet-inverses": changed})


@pytest.mark.parametrize("field", ("statement", "script", "dependencies", "summary", "defined", "id", "sources"))
def test_publication_identity_guard_rejects_changed_theorem_material(field, source_inputs):
    _, corpora = source_inputs
    original = corpora["dirichlet-signed-units"]
    changed = deepcopy(original)
    row = changed["nodes"][0]
    row[field] = {"statement": "0=0", "script": ["refl"], "dependencies": ["invented"],
                  "summary": "Different mathematics", "defined": {}, "id": "ZU9999", "sources": []}[field]
    with pytest.raises(publication.PublicationError, match="theorem or notation"):
        builder._definition_and_statement_identity(original, changed)


@pytest.mark.parametrize("field", ("definitions", "edges", "tags", "layers", "proof_adjacency", "proof_paths", "root_names"))
def test_publication_identity_guard_rejects_changed_graph_or_tag_material(field, source_inputs):
    _, corpora = source_inputs
    original = corpora["dirichlet-signed-units"]
    changed = deepcopy(original)
    changed[field] = {} if isinstance(changed[field], dict) else []
    with pytest.raises(publication.PublicationError, match="mathematical reader field"):
        builder._definition_and_statement_identity(original, changed)


def test_standalone_builder_calls_actual_release_verifier_before_any_snapshot(monkeypatch):
    class UnverifiedRelease(RuntimeError):
        pass

    called = []

    def refuse():
        called.append("live verifier")
        raise UnverifiedRelease("no verified release")

    def forbidden():
        raise AssertionError("no presentation input may be accepted first")

    # The only verifier replacement is rejecting, never an accepting proof mock.
    monkeypatch.setitem(sys.modules, "verify_peano_library_channels_v31", SimpleNamespace(verify_for_publication=refuse))
    monkeypatch.setattr(publication, "authenticate_snapshots", forbidden)
    with pytest.raises(UnverifiedRelease, match="no verified release"):
        builder.build_files()
    assert called == ["live verifier"]


def test_public_builder_has_no_saved_receipt_or_skip_verification_argument():
    assert tuple(inspect.signature(builder.build_files).parameters) == ()
    assert tuple(inspect.signature(builder.build_files_from_live).parameters) == ("context",)
    tree = ast.parse(inspect.getsource(builder.build_files_from_live))
    first = tree.body[0].body[0]
    assert isinstance(first, ast.Expr) and isinstance(first.value, ast.Call)
    assert ast.unparse(first.value.func) == "publication.require_live"
    source = inspect.getsource(publication.require_live)
    assert "type(context) is not LiveReleaseContext" in source
    assert "context.require_unchanged()" in source


@pytest.mark.parametrize("embedded", ('const sample="</body>";', 'const sample="<a href=bad>Alpha v30</a>";', 'const sample="</main>";'))
def test_html_metadata_and_marker_insertion_preserve_script_and_math_text(embedded):
    page = "transport-only/explorer/tag/ZZ0001.html"
    source = ('<!doctype html><html><head><title>Syntax-only transport fixture</title></head>'
              '<body class="pa-proof-site"><header class="pa-proof-header"><nav>'
              '<a href="../defined/graph.html?target=ZZ0001&amp;v=0123456789ab">Graph</a>'
              '</nav></header><main><pre><code>Alpha v30; 0 &lt; n; unchanged exact bytes</code></pre></main>'
              '<script>' + embedded + '</script></body></html>').encode()
    result = builder._CurrentHTML(page, "0123456789ab", portable_script="<!-- transport-only insertion -->").finish(source)
    assert embedded.encode() in result
    assert b'<pre><code>Alpha v30; 0 &lt; n; unchanged exact bytes</code></pre>' in result
    assert result.count(b"data-graph-navigation") == 1
    assert result.count(b"<!-- transport-only insertion -->") == 1
    assert result.index(b"<!-- transport-only insertion -->") > result.index(b"</script>")
    assert b'../defined/graph.html?target=ZZ0001&amp;v=0123456789ab' in result


@pytest.mark.parametrize("problem", ("duplicate_attribute", "missing_graph", "duplicate_graph", "unclosed", "wrong_canonical"))
def test_current_html_rejects_ambiguous_document_or_graph_boundaries(problem):
    anchor = '<a href="../defined/graph.html">Graph</a>'
    source = '<html><head></head><body class="pa-proof-site"><header class="pa-proof-header">' + anchor + '</header></body></html>'
    if problem == "duplicate_attribute":
        source = source.replace('class="pa-proof-site"', 'class="pa-proof-site" class="other"')
    elif problem == "missing_graph":
        source = source.replace(anchor, "")
    elif problem == "duplicate_graph":
        source = source.replace(anchor, anchor + anchor)
    elif problem == "unclosed":
        source = source.removesuffix("</html>")
    else:
        source = source.replace("<head>", '<head><link rel="canonical" href="https://example.invalid/">')
    with pytest.raises(publication.PublicationError):
        builder._CurrentHTML("transport-only/explorer/tag/ZZ0001.html", "0123456789ab").finish(source.encode())


def test_portable_navigation_is_actual_valid_javascript_with_no_svg_href_assignment():
    source = builder._portable_script({"prime-fields": publication.OUTPUT_NAME})
    program = "new (require('node:vm').Script)(require('node:fs').readFileSync(0,'utf8'));"
    subprocess.run(["node", "--max-old-space-size=128", "-e", program],
                   input=source.removeprefix("<script>").removesuffix("</script>\n"),
                   text=True, capture_output=True, check=True, timeout=15)
    assert 'link.setAttribute("href", target.href)' in source
    assert ".href =" not in source and ".href=" not in source


def test_syntax_validation_never_changes_any_old_snapshot_manifest(source_inputs):
    publication.validate_definition_identities(source_inputs[1])
    for item in publication.SNAPSHOTS:
        raw = (ROOT / "book/_static" / item.directory / "manifest.json").read_bytes()
        assert len(raw) == item.manifest_bytes and sha256(raw).hexdigest() == item.manifest_sha256
