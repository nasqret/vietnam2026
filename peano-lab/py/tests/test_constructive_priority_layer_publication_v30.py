"""Current navigation must preserve the exact v27, v28 and v29 proof admissions."""

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import build_constructive_gaussian_factorization_explorer as current
import upgrade_constructive_priority_layer_publication_v30 as successor
from build_peano_library_channels_v30 import HISTORICAL_ATLAS_INPUTS
from constructive_checked_explorer_renderer import DefinedExplorerRenderError, _edition_labels, _status


@pytest.mark.parametrize("path,digest", tuple(HISTORICAL_ATLAS_INPUTS.items()))
def test_v29_atlas_bytes_remain_exact_and_separate(path, digest):
    assert sha256((ROOT / path).read_bytes()).hexdigest() == digest
    assert current.CAMPAIGN.parent != (ROOT / path).parent
    assert all(path not in (successor.lower.OUTPUT, successor.second.OUTPUT, successor.priority.OUTPUT) for path in successor.OUTPUTS.values())


@pytest.mark.parametrize("first", ("v27", "v28", "v29", "v30"))
def test_current_authority_and_first_admission_are_distinct(first):
    labels = {"alpha_edition_version": "v30", "alpha_first_enrolled_version": first}
    assert _edition_labels(labels) == ("v30", first)
    assert "Alpha v30 checked-use" in _status(labels)
    assert f"first admitted {first}" in _status(labels)


@pytest.mark.parametrize("current_version,first", (("v29", "v30"), ("v030", "v28"), ("v30", "v0"), (30, "v27")))
def test_unsafe_or_reversed_versions_are_rejected(current_version, first):
    with pytest.raises(DefinedExplorerRenderError):
        _edition_labels({"alpha_edition_version": current_version, "alpha_first_enrolled_version": first})


@pytest.fixture(scope="module")
def authority():
    # Each original release and the current release execute their actual
    # unmodified kernels and independently compiled Lean bundle verifier.
    now = current._load_inputs()
    old = {"v27": successor._load_historical_inputs(), "v28": successor.lower._load_inputs(), "v29": successor.priority._load_inputs()}
    for version, families in (("v27", successor.second.FAMILIES), ("v28", successor.lower.FAMILIES), ("v29", successor.priority.FAMILIES)):
        successor._audit_preserved(now, old[version], families)
    return now, old


@pytest.fixture(scope="module")
def files(authority):
    return successor.build_files()


@pytest.mark.parametrize("version", ("v27", "v28", "v29"))
@pytest.mark.parametrize("mutation", ("theorem", "milestone", "first_catalog"))
def test_historical_first_admission_cannot_be_rewritten(version, mutation, authority):
    now, old = authority
    selected = old[version]
    families = {"v27": successor.second.FAMILIES, "v28": successor.lower.FAMILIES, "v29": successor.priority.FAMILIES}[version]
    if mutation == "theorem":
        now = {**now, "by_name": dict(now["by_name"])}
        name = families[0].roots[-1]
        now["by_name"][name] = {**now["by_name"][name], "checked_use": False}
    elif mutation == "milestone":
        now = {**now, "campaign": deepcopy(now["campaign"])}
        next(row for row in now["campaign"]["nodes"] if row["id"] == families[0].milestones[-1])["status"] = "open"
    else:
        selected = {**selected, "catalog_sha256": "0" * 64}
    with pytest.raises(ValueError):
        successor._audit_preserved(now, selected, families)


HISTORICAL_FAMILIES = tuple(("v27", family) for family in successor.second.FAMILIES) + tuple(
    ("v28", family) for family in successor.lower.FAMILIES
) + tuple(("v29", family) for family in successor.priority.FAMILIES)


@pytest.mark.parametrize("version,family", HISTORICAL_FAMILIES, ids=[family.slug for _, family in HISTORICAL_FAMILIES])
def test_every_historical_body_and_definition_keeps_its_original_receipt(version, family, files, authority):
    now, old = authority
    files = files[version]
    corpus = json.loads(files[f"{family.slug}/api/corpus.json"])
    parent = {"v27": successor.second, "v28": successor.lower, "v29": successor.priority}[version]
    original = json.loads((parent.OUTPUT / family.slug / "api/corpus.json").read_bytes())
    assert corpus["alpha_edition_version"] == "v30"
    assert corpus["alpha_first_enrolled_version"] == version
    assert corpus["alpha_catalog_sha256"] == now["catalog_sha256"]
    assert corpus["alpha_first_enrollment_catalog_sha256"] == old[version]["catalog_sha256"]
    assert corpus["alpha_proof_bundle_sha256"] == old[version]["bundle"]["artifact_sha256"]
    assert corpus["tags"] == original["tags"]
    for node, previous in zip(corpus["nodes"], original["nodes"], strict=True):
        for key in ("id", "name", "statement", "statement_sha256", "script", "dependencies", "sources",
                    "proof_bundle_node_id", "proof_bundle_sha256", "body_proof_nodes", "body_proof_depth", "defined"):
            assert node[key] == previous[key]
        assert node["alpha_edition_version"] == "v30" and node["alpha_first_enrolled_version"] == version
    for definition, previous in zip(corpus["definitions"], original["definitions"], strict=True):
        for key in ("id", "name", "parameters", "expanded_template", "expansion_sha256", "dependencies"):
            assert definition[key] == previous[key]
    graph = json.loads(files[f"{family.slug}/explorer/defined/api/graph.json"])
    assert graph["alpha_edition_version"] == "v30" and graph["alpha_first_enrolled_version"] == version
    for node in graph["nodes"]:
        if node["kind"] == "theorem":
            assert node["alpha_edition_version"] == "v30" and node["alpha_first_enrolled_version"] == version
    root = corpus["tags"][family.roots[-1]]
    page = files[f"{family.slug}/explorer/defined/tag/{root}.html"]
    assert b"Alpha v30 checked use" in page and f"<dd>Alpha {version}</dd>".encode() in page


@pytest.mark.parametrize("version,count", (("v27", 422), ("v28", 204), ("v29", 278)))
def test_every_manifest_and_output_is_exact_and_separately_published(version, count, files, authority):
    now, old = authority
    files = files[version]
    manifest = json.loads(files["manifest.json"])
    assert manifest["catalog_sha256"] == now["catalog_sha256"]
    assert manifest["first_enrollment_catalog_sha256"] == old[version]["catalog_sha256"]
    assert manifest["alpha_edition_version"] == "v30"
    assert manifest["alpha_first_enrolled_version"] == version
    assert manifest["theorem_count"] == manifest["checked_use_count"] == count
    assert manifest["file_count"] == len(manifest["files"]) == len(files) - 1
    for record in manifest["files"]:
        payload = files[record["path"]]
        assert len(payload) == record["bytes"] and sha256(payload).hexdigest() == record["sha256"]
        assert (successor.OUTPUTS[version] / record["path"]).read_bytes() == payload
    assert manifest["inventory_sha256"] == sha256(current._json(manifest["files"])).hexdigest()
    assert (successor.OUTPUTS[version] / "manifest.json").read_bytes() == files["manifest.json"]
