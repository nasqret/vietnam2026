"""Current v28 presentation must not rewrite v27 admission or historical checks."""

from __future__ import annotations

import base64
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import zlib

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_constructive_second_wave_explorer as old_builder
import build_constructive_lower_layer_explorer as current
import upgrade_constructive_second_wave_publication_v28 as successor
from constructive_checked_explorer_renderer import DefinedExplorerRenderError, _edition_labels, _status


def test_archived_projection_recovers_the_two_exact_original_byte_streams():
    files = successor.historical_projection_bytes()
    assert files.keys() == successor.PROJECTION_FILES.keys()
    for name, payload in files.items():
        size, digest = successor.PROJECTION_FILES[name]
        assert len(payload) == size and sha256(payload).hexdigest() == digest
    campaign, definitions = (json.loads(files[name]) for name in ("campaign.json", "definitions.json"))
    assert campaign["meta"]["current_alpha_version"] == "v27"
    assert campaign["meta"]["current_alpha_checked_use_count"] == 2560
    assert definitions == old_builder.build_definition_graph(campaign)
    assert successor.OUTPUT != old_builder.OUTPUT
    assert old_builder.OUTPUT.name == "constructive-second-wave-explorer"
    assert successor.OUTPUT.name == "constructive-second-wave-explorer-v28"


def test_historical_context_changes_only_two_input_paths_and_restores_them():
    before = (old_builder.CAMPAIGN, old_builder.GLOBAL_DEFINITIONS, old_builder.OUTPUT,
              old_builder._load_release_inputs, old_builder.closure.check_second_wave_proof_bundle)
    with pytest.raises(RuntimeError, match="fixture exit"):
        with successor.historical_presentation_context():
            assert (old_builder.CAMPAIGN, old_builder.GLOBAL_DEFINITIONS) != before[:2]
            assert (old_builder.OUTPUT, old_builder._load_release_inputs,
                    old_builder.closure.check_second_wave_proof_bundle) == before[2:]
            assert old_builder.CAMPAIGN.read_bytes() == successor.historical_projection_bytes()["campaign.json"]
            raise RuntimeError("fixture exit")
    assert (old_builder.CAMPAIGN, old_builder.GLOBAL_DEFINITIONS, old_builder.OUTPUT,
            old_builder._load_release_inputs, old_builder.closure.check_second_wave_proof_bundle) == before


@pytest.mark.parametrize("mutation", (
    "outer_digest", "schema", "version", "commit", "catalog", "duplicate_file", "path", "size", "digest",
    "invalid_base64", "truncated_gzip", "trailing_gzip", "oversized_expansion",
))
def test_historical_projection_rejects_forgery_truncation_and_expansion_bombs(mutation, tmp_path, monkeypatch):
    archive = json.loads(successor.PROJECTION.read_bytes())
    row = archive["files"][0]
    if mutation == "schema":
        archive["schema"] = "other"
    elif mutation == "version":
        archive["alpha_version"] = "v28"
    elif mutation == "commit":
        archive["source_commit"] = "0" * 40
    elif mutation == "catalog":
        archive["catalog_sha256"] = "0" * 64
    elif mutation == "duplicate_file":
        archive["files"][1] = dict(row)
    elif mutation == "path":
        row["source_path"] = "../campaign.json"
    elif mutation == "size":
        row["bytes"] += 1
    elif mutation == "digest":
        row["sha256"] = "0" * 64
    elif mutation == "invalid_base64":
        row["gzip_base64"] = "not base64!!!"
    elif mutation == "truncated_gzip":
        row["gzip_base64"] = base64.b64encode(base64.b64decode(row["gzip_base64"])[:-8]).decode()
    elif mutation == "trailing_gzip":
        row["gzip_base64"] = base64.b64encode(base64.b64decode(row["gzip_base64"]) + b"trailing").decode()
    elif mutation == "oversized_expansion":
        compressor = zlib.compressobj(wbits=16 + zlib.MAX_WBITS)
        row["gzip_base64"] = base64.b64encode(compressor.compress(b"x" * (row["bytes"] * 4)) + compressor.flush()).decode()
    else:
        archive["extra"] = True
    data = current._json(archive)
    path = tmp_path / "projection.json"
    path.write_bytes(data)
    monkeypatch.setattr(successor, "PROJECTION", path)
    if mutation != "outer_digest":
        # Exercise the inner independent size/provenance/hash guards as well
        # as the outer literal byte pin tested in the separate case.
        monkeypatch.setattr(successor, "PROJECTION_SHA256", sha256(data).hexdigest())
    with pytest.raises(ValueError):
        successor.historical_projection_bytes()


@pytest.mark.parametrize("current_version,first", (("v28", "v27"), ("v28", "v28")))
def test_shared_renderer_separates_current_authority_from_first_admission(current_version, first):
    value = {"alpha_edition_version": current_version, "alpha_first_enrolled_version": first}
    assert _edition_labels(value) == (current_version, first)
    assert f"Alpha {current_version} checked-use" in _status(value)
    assert f"first admitted {first}" in _status(value)


@pytest.mark.parametrize("current_version,first", (("v27", "v28"), ("v028", "v27"), ("v28", "v0"), (28, "v27"), ("<script>", "v27")))
def test_shared_renderer_rejects_unsafe_or_reversed_edition_labels(current_version, first):
    with pytest.raises(DefinedExplorerRenderError):
        _edition_labels({"alpha_edition_version": current_version, "alpha_first_enrolled_version": first})


@pytest.fixture(scope="module")
def authority():
    # Both are independently checked by the unchanged HA and compiled Lean
    # verifiers. The archived atlas never supplies mathematical authority.
    now, old = current._load_inputs(), successor._load_historical_inputs()
    successor._audit_preserved_second_wave(now, old)
    return now, old


@pytest.fixture(scope="module")
def files(authority):
    return successor.build_files()


@pytest.mark.parametrize("mutation", ("theorem", "milestone", "first_catalog"))
def test_current_publication_rejects_rewritten_first_admission(mutation, authority):
    now, old = authority
    if mutation == "theorem":
        now = {**now, "by_name": dict(now["by_name"])}
        name = "prime_count_chebyshev_bounds"
        now["by_name"][name] = {**now["by_name"][name], "checked_use": False}
    elif mutation == "milestone":
        now = {**now, "campaign": deepcopy(now["campaign"])}
        next(row for row in now["campaign"]["nodes"] if row["id"] == "G095")["evidence"]["alpha_version"] = "v28"
    else:
        old = {**old, "catalog_sha256": "0" * 64}
    with pytest.raises(ValueError):
        successor._audit_preserved_second_wave(now, old)


@pytest.mark.parametrize("family", old_builder.FAMILIES, ids=lambda family: family.slug)
def test_all_historical_theorem_rows_keep_v27_receipts_under_current_v28_authority(family, files, authority):
    now, old = authority
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    assert corpus["alpha_edition_version"] == "v28" and corpus["alpha_first_enrolled_version"] == "v27"
    assert corpus["alpha_catalog_sha256"] == now["catalog_sha256"]
    assert corpus["alpha_first_enrollment_catalog_sha256"] == old["catalog_sha256"]
    assert corpus["alpha_proof_bundle_sha256"] == old["bundle"]["artifact_sha256"]
    original = json.loads((old_builder.OUTPUT / family.slug / "api/corpus.json").read_bytes())
    assert corpus["tags"] == original["tags"]
    for node, previous in zip(corpus["nodes"], original["nodes"], strict=True):
        for key in ("id", "name", "statement", "statement_sha256", "script", "dependencies", "sources",
                    "proof_bundle_node_id", "proof_bundle_sha256", "body_proof_nodes", "body_proof_depth", "defined"):
            assert node[key] == previous[key]
        assert node["alpha_edition_version"] == "v28" and node["alpha_first_enrolled_version"] == "v27"
    graph = json.loads(files[f"{family.slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v28" and graph["alpha_first_enrolled_version"] == "v27"
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            assert node["alpha_edition_version"] == "v28" and node["alpha_first_enrolled_version"] == "v27"
    root = corpus["tags"][family.roots[-1]]
    page = files[f"{family.slug}/explorer/defined/tag/{root}.html"]
    assert b"Alpha v28 checked use" in page and b"<dd>Alpha v27</dd>" in page


def test_current_manifest_and_outputs_are_distinct_and_fully_reproducible(files, authority):
    now, old = authority
    manifest = json.loads(files["manifest.json"])
    assert manifest["theorem_count"] == manifest["checked_use_count"] == 422
    assert manifest["catalog_sha256"] == now["catalog_sha256"]
    assert manifest["first_enrollment_catalog_sha256"] == old["catalog_sha256"]
    assert manifest["alpha_edition_version"] == "v28" and manifest["alpha_first_enrolled_version"] == "v27"
    assert manifest["proof_bundle_sha256"] == old["bundle"]["artifact_sha256"]
    for record in manifest["files"]:
        payload = files[record["path"]]
        assert len(payload) == record["bytes"] and sha256(payload).hexdigest() == record["sha256"]
        assert (successor.OUTPUT / record["path"]).read_bytes() == payload
    assert manifest["inventory_sha256"] == sha256(current._json(manifest["files"])).hexdigest()
    assert (successor.OUTPUT / "manifest.json").read_bytes() == files["manifest.json"]
