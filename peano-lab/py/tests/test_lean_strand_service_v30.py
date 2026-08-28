"""Current v30 publication authority, exact first admission, and fail-closed atlas succession.

Isolated fixtures are tiny owned files; actual publication tests are read-only
and start neither proof workers nor sockets. Historical artifacts stay exact.
"""

from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path

import pytest

from test_lean_strand_service import (
    ROOT, install_test_release, non_listening_review_server, service,
)


PUBLICATIONS = {
    "constructive-second-wave-explorer-v30": ("v27", "integer-linear-algebra", 422, 7),
    "constructive-lower-layer-explorer-v30": ("v28", "arithmetic-foundations", 204, 4),
    "constructive-priority-layer-explorer-v30": ("v29", "best-approximation", 278, 5),
    "constructive-gaussian-factorization-explorer": ("v30", "gaussian-factorization", 180, 1),
}


@pytest.fixture()
def current_release(tmp_path):
    install_test_release(tmp_path, version="v28")
    old_path = tmp_path / "book/_static/constructive-grand-campaign/campaign.json"
    old = old_path.read_bytes()
    digest, identity = install_test_release(tmp_path, version="v30")
    current = old_path.parent.with_name("constructive-gaussian-campaign")
    old_path.parent.rename(current)
    old_path.parent.mkdir()
    old_path.write_bytes(old)
    for segment, (first, slug, _, _) in PUBLICATIONS.items():
        policy = service.CONSTRUCTIVE_PUBLICATIONS[segment]
        directory = current.parent / segment
        directory.mkdir()
        (directory / "manifest.json").write_text(json.dumps({
            "schema": policy.schema, "alpha_edition_version": "v30",
            "catalog_sha256": digest, "edition_identity_sha256": identity,
            "alpha_first_enrolled_version": first,
            "first_enrollment_catalog_sha256": policy.first_catalog_sha256 or digest,
            "families": [{"slug": slug, "theorem_count": 1}],
        }))
    return tmp_path, digest, identity


@pytest.mark.parametrize("segment", PUBLICATIONS)
def test_exact_current_and_first_admission_are_both_required(current_release, segment):
    root, digest, identity = current_release
    server = non_listening_review_server(root)
    directory = root / "book/_static" / segment
    first, slug, _, _ = PUBLICATIONS[segment]
    assert server._current_constructive_release(directory.parent, owner=os.getuid()) == ("v30", digest, identity)
    assert server.reviewed_constructive_family(directory, slug)
    assert service.CONSTRUCTIVE_PUBLICATIONS[segment].first_enrolled_version == first


@pytest.mark.parametrize("segment", PUBLICATIONS)
@pytest.mark.parametrize("field,forged", (
    ("schema", "peano-lab-constructive-invented-explorer-v1-manifest"),
    ("alpha_edition_version", "v29"),
    ("catalog_sha256", "0" * 64),
    ("edition_identity_sha256", "0" * 64),
    ("alpha_first_enrolled_version", "v1"),
    ("first_enrollment_catalog_sha256", "0" * 64),
))
def test_cached_current_publication_rejects_forged_history_or_authority(current_release, segment, field, forged):
    root, _, _ = current_release
    server = non_listening_review_server(root)
    directory = root / "book/_static" / segment
    slug = PUBLICATIONS[segment][1]
    assert server.reviewed_constructive_family(directory, slug)
    path = directory / "manifest.json"
    manifest = json.loads(path.read_bytes())
    manifest[field] = forged
    path.write_text(json.dumps(manifest))
    assert not server.reviewed_constructive_family(directory, slug)


@pytest.mark.parametrize("mutation", ("missing", "invalid", "duplicate", "symlink", "file", "wrong_owner"))
def test_broken_present_current_atlas_never_falls_back_to_valid_history(current_release, monkeypatch, mutation):
    root, _, _ = current_release
    server = non_listening_review_server(root)
    static = root / "book/_static"
    directory = static / "constructive-gaussian-campaign"
    path = directory / "campaign.json"
    assert server._current_constructive_release(static, owner=os.getuid())[0] == "v30"
    if mutation == "missing":
        path.rename(directory / "campaign-unavailable.json")
    elif mutation == "invalid":
        path.write_text("[]")
    elif mutation == "duplicate":
        path.write_text('{"schema":"one","schema":"two"}')
    elif mutation in {"symlink", "file"}:
        destination = directory.with_name("saved-current-campaign")
        directory.rename(destination)
        if mutation == "symlink":
            directory.symlink_to(destination, target_is_directory=True)
        else:
            directory.write_text("not a directory")
    else:
        original = Path.stat
        def different_owner(candidate, *args, **kwargs):
            value = original(candidate, *args, **kwargs)
            if candidate == directory:
                fields = list(value)
                fields[4] = value.st_uid + 1
                return os.stat_result(fields)
            return value
        monkeypatch.setattr(Path, "stat", different_owner)
    with pytest.raises((ValueError, OSError)):
        server._current_constructive_release(static, owner=os.getuid())
    assert not server.reviewed_constructive_family(static / "constructive-gaussian-factorization-explorer", "gaussian-factorization")


def test_invalid_historical_atlas_does_not_override_valid_current_release(current_release):
    root, digest, identity = current_release
    static = root / "book/_static"
    (static / "constructive-grand-campaign/campaign.json").write_text("not JSON")
    server = non_listening_review_server(root)
    assert server._current_constructive_release(static, owner=os.getuid()) == ("v30", digest, identity)


def test_current_catalog_corruption_invalidates_warm_cache_without_fallback(current_release):
    root, _, _ = current_release
    static = root / "book/_static"
    server = non_listening_review_server(root)
    assert server._current_constructive_release(static, owner=os.getuid())[0] == "v30"
    path = root / "artifacts/peano-library/alpha/catalog-v30.json"
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="sealed digest"):
        server._current_constructive_release(static, owner=os.getuid())


@pytest.mark.parametrize("segment", (
    "constructive-priority-layer-explorer-v030", "constructive-priority-layer-explorer-v30-extra",
    "constructive-gaussian-factorization-explorer-v30", "constructive-lower-layer-explorer-V30",
))
def test_unreviewed_version_suffix_cannot_borrow_a_valid_manifest(current_release, segment):
    root, _, _ = current_release
    static = root / "book/_static"
    directory = static / segment
    directory.mkdir(exist_ok=True)
    (directory / "manifest.json").write_bytes((static / "constructive-priority-layer-explorer-v30/manifest.json").read_bytes())
    assert not non_listening_review_server(root).reviewed_constructive_family(directory, "best-approximation")


@pytest.mark.parametrize("segment", PUBLICATIONS)
def test_actual_current_publications_and_every_principal_panel_pass_read_only_review(segment):
    server = non_listening_review_server(ROOT)
    handler = object.__new__(service.LeanStrandHandler)
    handler.server = server
    directory = ROOT / "book/_static" / segment
    manifest_path = directory / "manifest.json"
    original_manifest = manifest_path.read_bytes()
    manifest = json.loads(original_manifest)
    first, _, count, families = PUBLICATIONS[segment]
    assert manifest["alpha_edition_version"] == "v30"
    assert manifest["alpha_first_enrolled_version"] == first
    assert manifest["theorem_count"] == manifest["checked_use_count"] == count
    assert len(manifest["families"]) == families
    for family in manifest["families"]:
        assert server.reviewed_constructive_family(directory, family["slug"])
        suffixes = ["explorer/defined/graph.html"]
        for tag in family["root_tags"].values():
            suffixes.extend((f"explorer/tag/{tag}.html", f"explorer/defined/tag/{tag}.html"))
        for suffix in suffixes:
            path = directory / family["slug"] / suffix
            original = path.read_bytes()
            enhanced = handler._inject_selector(path, path.relative_to(ROOT).parts)
            assert enhanced is not None and b"lean-selector.js" in enhanced
            assert b"lean-selector.css" in enhanced and path.read_bytes() == original
    assert manifest_path.read_bytes() == original_manifest


def test_actual_current_catalog_keeps_original_streaming_size_limit():
    catalog = ROOT / "artifacts/peano-library/alpha/catalog-v30.json"
    assert service.MAX_EXPLORER_CATALOG_BYTES == 64 * 1024 * 1024
    assert catalog.stat().st_size <= service.MAX_EXPLORER_CATALOG_BYTES
    channel = json.loads((ROOT / "artifacts/peano-library/channels-v30.json").read_bytes())
    assert sha256(catalog.read_bytes()).hexdigest() == channel["channels"]["alpha"]["artifact_sha256"]
