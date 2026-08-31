"""V31 route/cache boundaries, not new theorem proof authority.

Isolated fixtures retain the real literal v30 parent and use the codec's
explicitly false, proof-free delta rows.  They test only file authentication
and navigation policy; no proof checker, live release capability, compiler,
socket, or worker is mocked into success.  Actual publication tests are
read-only and require the final genuinely generated current snapshots.
"""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import time
from types import SimpleNamespace

import pytest

from test_lean_strand_service import ROOT, non_listening_review_server, service
import peano_catalog_shards as codec
from test_peano_catalog_shards import model, transport_directory  # Real-parent, non-authorizing fixtures.
import constructive_completed_lower_publication_v31 as publication
import upgrade_constructive_historical_publication_v31 as historical


CURRENT_ATLAS = "constructive-completed-lower-campaign-v31"
COMPLETED = "constructive-completed-lower-explorer-v31"
HISTORICAL = "constructive-historical-explorers-v31"
OLD_ATLAS = "constructive-gaussian-campaign"
PARENT_SHA = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
EXPECTED_COMPLETED = {
    "euler-units": 32, "prime-fields": 87, "mobius-values": 21, "signed-sums": 30,
    "divisor-sums": 37, "signed-weighted-sums": 40, "prime-field-polynomials": 49,
    "divisor-involutions": 12, "mobius-divisor-cancellation": 28, "rectangular-sums": 32,
    "polynomial-products": 53, "finite-support": 8, "dirichlet-convolution": 40,
    "dirichlet-fubini": 32, "dirichlet-units": 25, "mobius-inversion": 8,
    "dirichlet-signed-units": 9, "dirichlet-triangular": 10, "dirichlet-inverses": 21,
}
EXPECTED_HISTORICAL = frozenset((
    "quadratic-reciprocity", "bertrand-postulate", "supplementary-laws", "kummer",
    "two-squares", "four-squares", "lucas", "pythagorean-fermat-four",
    "polynomial-horner", "matrix-dot-product", "bertrand-prime-chains", "continued-fractions",
    "matrix-coded-products", "euclidean-complexity", "binary-modular-exponentiation",
    "binary-length", "euclidean-gcd-transport", "binary-modular-execution",
    "euclidean-logarithmic-bound", "binary-digit-extraction", "primes-three-mod-four",
    "matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold",
    "matrix-cofactor-expansion", "polynomial-taylor-hensel", "generalized-crt-compatibility",
    "integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer",
    "prime-count-chebyshev", "cornacchia", "cauchy-davenport", "arithmetic-foundations",
    "prime-enumeration", "gaussian-integers", "eisenstein-integers", "prime-valuation-support",
    "best-approximation", "totient-products", "squarefree-kernels", "exponent-lifting",
    "gaussian-factorization",
))
RSS_LIMIT = 1536 * 1024 * 1024


def _json(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def _write(path, raw):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _release_documents(root, *, version, digest, identity, count, atlas):
    channel = root / "artifacts/peano-library" / f"channels-{version}.json"
    _write(channel, _json({
        "schema": f"peano-library-channels-{version}", "fixture_notice": "navigation transport only",
        "channels": {"alpha": {"artifact_path": f"artifacts/peano-library/alpha/catalog-{version}.json",
            "artifact_sha256": digest, "edition_identity_sha256": identity,
            "theorem_count": count, "checked_use_count": count}},
    }))
    campaign = root / "book/_static" / atlas / "campaign.json"
    _write(campaign, _json({
        "schema": "constructive-grand-campaign-v1", "fixture_notice": "NOT PROOF EVIDENCE",
        "meta": {"current_alpha_version": version, "current_alpha_checked_use_count": count},
        "ambitious_boundaries": {f"alpha_{version}_edition": {
            "role": "current_immutable_release", "catalog_sha256": digest,
            "identity_sha256": identity, "theorem_count": count, "checked_use_count": count}},
    }))
    return channel, campaign


@pytest.fixture
def release(tmp_path, model, transport_directory, monkeypatch):
    """A private metadata-only route fixture; its delta is deliberately false."""
    root = tmp_path.resolve()
    directory = root / "artifacts/peano-library/alpha"
    directory.mkdir(parents=True)
    # This link is to the codec fixture's OWNED COPY, never the repository
    # parent. Any mutation below replaces the link rather than its content.
    os.link(transport_directory / "catalog-v30.json", directory / "catalog-v30.json")
    for name in ("catalog-v31.json", "catalog-v31-delta.json"):
        shutil.copyfile(transport_directory / name, directory / name)
    digest = sha256((directory / "catalog-v31.json").read_bytes()).hexdigest()
    identity = model[1]["edition_identity_sha256"]
    channel, campaign = _release_documents(root, version="v31", digest=digest, identity=identity,
                                          count=3796, atlas=CURRENT_ATLAS)
    _release_documents(root, version="v30", digest=PARENT_SHA,
                       identity=model[0]["edition_identity_sha256"], count=3222, atlas=OLD_ATLAS)
    static = root / "book/_static"
    manifest = {
        "schema": "peano-lab-constructive-completed-lower-explorer-v31-manifest",
        "alpha_edition_version": "v31", "alpha_first_enrolled_version": "v31",
        "catalog_sha256": digest, "edition_identity_sha256": identity,
        "first_enrollment_catalog_sha256": digest,
        "theorem_count": 574, "checked_use_count": 574, "stable_count": 0,
        "fixture_notice": "Route fixture only; the paired delta is intentionally NOT a proof.",
        "families": [{"slug": slug, "theorem_count": count, "alpha_edition_version": "v31"}
                     for slug, count in EXPECTED_COMPLETED.items()],
    }
    _write(static / COMPLETED / "manifest.json", _json(manifest))
    # An actually consistent historical release remains available to expose
    # any unintended fallback from a present-but-broken newest atlas.
    _write(static / "constructive-gaussian-factorization-explorer/manifest.json", _json({
        "schema": "peano-lab-constructive-gaussian-factorization-explorer-v1-manifest",
        "alpha_edition_version": "v30", "alpha_first_enrolled_version": "v30",
        "catalog_sha256": PARENT_SHA, "first_enrollment_catalog_sha256": PARENT_SHA,
        "edition_identity_sha256": model[0]["edition_identity_sha256"],
        "families": [{"slug": "gaussian-factorization", "theorem_count": 180}],
    }))
    # Keep every test self-contained even after the real v31 output appears.
    monkeypatch.setattr(service, "ROOT", root)
    return SimpleNamespace(root=root, static=static, directory=directory, digest=digest,
                           identity=identity, channel=channel, campaign=campaign,
                           manifest=static / COMPLETED / "manifest.json",
                           server=non_listening_review_server(root))


@pytest.fixture(scope="module")
def historical_inputs():
    """Real byte-pinned old corpora and their exact provenance, not admission."""
    metadata = historical.family_metadata()
    rows, sidecars, originals = {}, {}, {}
    for item in historical.SNAPSHOTS:
        if item.defined:
            continue
        manifest = historical.source_manifest(item)
        pins = {pin["path"]: pin for pin in manifest["files"]}
        for slug in item.slugs:
            corpus = publication.strict_json(historical.source_file(item, pins, historical._corpus_path(item, slug)))
            tags = historical._tags(item, slug, corpus, pins)
            record = historical.first_admission_records(item, slug, manifest, corpus, tags)
            rows[slug] = record
            sidecars[slug + "/api/first-admission.json"] = publication.json_bytes(record)
            originals[slug] = corpus.get("nodes", corpus.get("theorems"))
    assert set(rows) == EXPECTED_HISTORICAL and len(metadata) == 44
    for family in metadata:
        descriptor = family["first_admission"]
        assert sha256(historical.canonical_bytes(descriptor)).hexdigest() == service.HISTORICAL_V31_FIRST_ADMISSIONS[family["slug"]]
        pin = descriptor["per_theorem_records"]
        raw = sidecars[pin["path"]]
        assert len(raw) == pin["bytes"] and sha256(raw).hexdigest() == pin["sha256"]
    return SimpleNamespace(metadata=metadata, rows=rows, sidecars=sidecars, originals=originals)


@pytest.fixture
def historical_release(release, historical_inputs):
    directory = release.static / HISTORICAL
    for name, payload in historical_inputs.sidecars.items():
        _write(directory / name, payload)
    _write(directory / "manifest.json", _json({
        "schema": "peano-lab-constructive-historical-publication-v31-manifest",
        "alpha_edition_version": "v31", "alpha_first_enrolled_version": "mixed_preserved",
        "catalog_sha256": release.digest, "edition_identity_sha256": release.identity,
        "families": [{key: family[key] for key in ("slug", "theorem_count", "checked_use_count",
                                                   "stable_count", "first_admission", "first_admission_sha256")}
                     for family in historical_inputs.metadata],
        "fixture_notice": "Read-only historical provenance plus non-authorizing transport fixture.",
    }))
    release.historical_directory = directory
    release.historical_manifest = directory / "manifest.json"
    return release


def _current(release):
    return release.server._current_constructive_release(release.static, owner=os.getuid())


def _review(release, slug="euler-units", *, historical_family=False):
    directory = release.static / (HISTORICAL if historical_family else COMPLETED)
    return release.server.reviewed_constructive_family(directory, slug)


def _mutate_json(path, transform, *, same_size_mtime=False):
    before, raw = path.stat(), path.read_bytes()
    document = json.loads(raw)
    transform(document)
    replacement = _json(document)
    if same_size_mtime:
        assert len(replacement) == len(raw)
    path.write_bytes(replacement)
    if same_size_mtime:
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
        after = path.stat()
        assert after.st_ino == before.st_ino and after.st_size == before.st_size
        assert after.st_mtime_ns == before.st_mtime_ns


def test_exact_19_and_44_reviewed_policies_preserve_original_limits():
    assert service.COMPLETED_LOWER_V31_FAMILIES == EXPECTED_COMPLETED
    assert len(EXPECTED_COMPLETED) == 19 and sum(EXPECTED_COMPLETED.values()) == 574
    assert set(service.HISTORICAL_V31_FIRST_ADMISSIONS) == EXPECTED_HISTORICAL
    assert len(EXPECTED_HISTORICAL) == 44
    assert service.CONSTRUCTIVE_CAMPAIGN_SUCCESSORS == (CURRENT_ATLAS, OLD_ATLAS,
        "constructive-priority-campaign", "constructive-grand-campaign")
    assert service.MAX_EXPLORER_CATALOG_BYTES == 64 * 1024 * 1024
    assert service.MAX_EXPLORER_MANIFEST_BYTES == 2 * 1024 * 1024
    assert service.MAX_EXPLORER_CAMPAIGN_BYTES == 8 * 1024 * 1024
    assert service.CONSTRUCTIVE_PUBLICATIONS[COMPLETED].first_enrolled_version == "v31"
    assert service.CONSTRUCTIVE_PUBLICATIONS[HISTORICAL].first_enrolled_version == "mixed_preserved"


def test_all_19_families_authorize_only_navigation_not_the_false_fixture_delta(release):
    assert _current(release) == ("v31", release.digest, release.identity)
    for slug in EXPECTED_COMPLETED:
        assert _review(release, slug), slug
    assert not _review(release, "invented-family")
    delta = json.loads((release.directory / "catalog-v31-delta.json").read_bytes())
    assert delta["theorems"][0]["statement"] == "0 = 1"
    assert delta["theorems"][0]["script"] == ["THIS IS NOT A PROOF"]
    assert all(type(value) is tuple and len(value) == 3 for value in release.server._constructive_release_cache.values())


def test_all_44_families_use_exact_mixed_descriptors_and_literal_full_sidecars(historical_release):
    for slug in EXPECTED_HISTORICAL:
        assert _review(historical_release, slug, historical_family=True), slug
    assert not _review(historical_release, "invented-family", historical_family=True)


def test_exact_provenance_does_not_infer_first_admission_or_promote_old_aliases(historical_inputs):
    unchecked = not_recorded = 0
    families = {row["slug"]: row for row in historical_inputs.metadata}
    for slug, records in historical_inputs.rows.items():
        original = {row["name"]: row for row in historical_inputs.originals[slug]}
        descriptor = families[slug]["first_admission"]
        assert descriptor["theorem_count"] == len(records["per_theorem"])
        assert descriptor["recorded_first_version_counts"] == dict(Counter(
            row["recorded_first_version"] for row in records["per_theorem"]))
        for row in records["per_theorem"]:
            source = original[row["name"]]
            first = source.get("alpha_first_enrolled_version", source.get("alpha_admission_version"))
            assert row["recorded_first_version"] == (first if first is not None else "not_recorded")
            not_recorded += first is None
            if source.get("alpha_checked_use") is not True:
                unchecked += 1
            for field, value in row["recorded_authority"].items():
                assert field in source and value == source[field]
        assert records["policy"] == "preserve_recorded_first_admission_without_inferring_it_from_current_or_proof_editions"
    assert unchecked == 89 and not_recorded > 0


@pytest.mark.parametrize("field,value", (
    ("schema", "unreviewed-manifest"), ("alpha_edition_version", "v30"),
    ("alpha_first_enrolled_version", "v30"), ("catalog_sha256", "0" * 64),
    ("edition_identity_sha256", "0" * 64), ("first_enrollment_catalog_sha256", PARENT_SHA),
))
def test_warm_completed_manifest_rejects_wrong_current_or_first_admission(release, field, value):
    assert _review(release)
    _mutate_json(release.manifest, lambda value_: value_.update({field: value}))
    assert not _review(release)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "foreign", "wrong_count", "bool_count", "wrong_family_version"))
def test_completed_family_set_and_each_exact_count_are_required(release, mutation):
    assert _review(release)

    def change(manifest):
        rows = manifest["families"]
        if mutation == "missing":
            rows.pop()
        elif mutation == "duplicate":
            rows[-1] = deepcopy(rows[0])
        elif mutation == "foreign":
            rows[-1]["slug"] = "foreign-family"
        elif mutation == "wrong_count":
            rows[0]["theorem_count"] += 1
        elif mutation == "bool_count":
            rows[0]["theorem_count"] = True
        else:
            rows[0]["alpha_edition_version"] = "v30"

    _mutate_json(release.manifest, change)
    assert not _review(release)


@pytest.mark.parametrize("segment", ("constructive-completed-lower-explorer-v031",
    "constructive-completed-lower-explorer-v31-extra", "constructive-completed-lower-explorer-V31",
    "constructive-historical-explorers-v031", "constructive-historical-explorers-v31-extra"))
def test_unreviewed_successor_spellings_cannot_borrow_the_valid_manifest(release, segment):
    directory = release.static / segment
    # A case-insensitive filesystem can resolve V31 to the already-created
    # owned v31 directory. Authorization must still reject the requested name.
    directory.mkdir(exist_ok=True)
    (directory / "manifest.json").write_bytes(release.manifest.read_bytes())
    assert not release.server.reviewed_constructive_family(directory, "euler-units")


def test_all_three_catalog_files_participate_in_cache_without_loading_proof_rows(release, monkeypatch):
    actual_decode, actual_auth = codec._decode, codec.verify_catalog_bindings
    decoded, authenticated = [], []

    def decode(raw, label):
        decoded.append(label)
        assert label == "v31 manifest"
        return actual_decode(raw, label)

    def authenticate(*args, **kwargs):
        authenticated.append(args[0])
        return actual_auth(*args, **kwargs)

    monkeypatch.setattr(codec, "_decode", decode)
    monkeypatch.setattr(codec, "verify_catalog_bindings", authenticate)
    monkeypatch.setattr(codec, "load_catalog", lambda *args, **kwargs: pytest.fail("route review parsed theorem rows"))
    assert _current(release) == _current(release) == ("v31", release.digest, release.identity)
    assert authenticated == [release.directory / "catalog-v31.json"]
    key = next(iter(release.server._constructive_release_cache))
    assert tuple(Path(pin.path).name for pin in key[-1]) == (
        "catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json")
    assert decoded and set(decoded) == {"v31 manifest"}


@pytest.mark.parametrize("name", ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json"))
def test_every_catalog_input_invalidates_warm_cache_after_same_size_same_mtime_replacement(release, name):
    assert _current(release)[0] == "v31"
    source = release.directory / name
    before = source.stat()
    replacement = release.directory / "owned-replacement.json"
    shutil.copyfile(source, replacement)
    with replacement.open("r+b") as stream:
        first = stream.read(1)
        stream.seek(0)
        stream.write(bytes([first[0] ^ 1]))
    os.utime(replacement, ns=(before.st_atime_ns, before.st_mtime_ns))
    replacement.replace(source)
    assert source.stat().st_size == before.st_size and source.stat().st_mtime_ns == before.st_mtime_ns
    with pytest.raises(ValueError):
        _current(release)
    assert not _review(release)


@pytest.mark.parametrize("name", ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json"))
@pytest.mark.parametrize("mutation", ("missing", "symlink", "oversized"))
def test_each_catalog_input_stays_bounded_regular_and_present_even_when_cached(release, name, mutation):
    assert _current(release)[0] == "v31"
    source = release.directory / name
    saved = release.directory / "saved-owned-copy"
    source.rename(saved)
    if mutation == "symlink":
        source.symlink_to(saved)
    elif mutation == "oversized":
        with source.open("xb") as stream:
            stream.truncate(64 * 1024 * 1024 + 1)  # Sparse owned file; no oversized read.
    with pytest.raises(ValueError):
        _current(release)
    assert not _review(release)


@pytest.mark.parametrize("which", ("campaign", "channel", "manifest"))
def test_warm_metadata_cache_cannot_be_preserved_by_restoring_size_and_mtime(release, which):
    assert _review(release)
    if which == "campaign":
        path = release.campaign
        change = lambda value: value["ambitious_boundaries"]["alpha_v31_edition"].update(identity_sha256="f" * 64)
    elif which == "channel":
        path = release.channel
        change = lambda value: value["channels"]["alpha"].update(edition_identity_sha256="f" * 64)
    else:
        path = release.manifest
        change = lambda value: value.update(alpha_edition_version="v30")
    _mutate_json(path, change, same_size_mtime=True)
    assert not _review(release)


@pytest.mark.parametrize("field", ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns", "st_mode", "st_uid"))
def test_navigation_cache_fingerprints_include_every_security_relevant_stat_field(field):
    fields = dict(st_dev=1, st_ino=2, st_size=3, st_mtime_ns=4, st_ctime_ns=5, st_mode=6, st_uid=7)
    before = service.LeanStrandServer._fingerprint(Path("owned-file"), SimpleNamespace(**fields))
    fields[field] += 1
    after = service.LeanStrandServer._fingerprint(Path("owned-file"), SimpleNamespace(**fields))
    assert before != after


@pytest.mark.parametrize("mutation", ("missing", "invalid", "duplicate", "symlink", "file", "old_release", "wrong_owner"))
def test_present_broken_newest_atlas_never_falls_back_to_valid_v30(release, monkeypatch, mutation):
    assert _current(release)[0] == "v31"
    directory = release.campaign.parent
    if mutation == "missing":
        release.campaign.rename(directory / "unavailable.json")
    elif mutation == "invalid":
        release.campaign.write_bytes(b"[]")
    elif mutation == "duplicate":
        release.campaign.write_bytes(b'{"schema":"one","schema":"two"}')
    elif mutation in ("symlink", "file"):
        saved = release.static / "owned-saved-atlas"
        directory.rename(saved)
        if mutation == "symlink":
            directory.symlink_to(saved, target_is_directory=True)
        else:
            directory.write_bytes(b"not a directory")
    elif mutation == "old_release":
        release.campaign.write_bytes((release.static / OLD_ATLAS / "campaign.json").read_bytes())
    else:
        actual_stat = Path.stat

        def wrong_owner(path, *args, **kwargs):
            value = actual_stat(path, *args, **kwargs)
            if path == directory:
                fields = list(value)
                fields[4] = value.st_uid + 1
                return os.stat_result(fields)
            return value

        monkeypatch.setattr(Path, "stat", wrong_owner)
    with pytest.raises((ValueError, OSError)):
        _current(release)
    assert not release.server.reviewed_constructive_family(
        release.static / "constructive-gaussian-factorization-explorer", "gaussian-factorization")


def test_an_actually_absent_successor_still_allows_an_isolated_valid_historical_deployment(release):
    release.campaign.parent.rename(release.root / "private-unpublished-atlas")
    assert _current(release)[0] == "v30"
    assert release.server.reviewed_constructive_family(
        release.static / "constructive-gaussian-factorization-explorer", "gaussian-factorization")


@pytest.mark.parametrize("mutation", ("descriptor", "missing", "duplicate", "foreign", "scalar_first"))
def test_warm_historical_cache_requires_all_exact_mixed_descriptors(historical_release, mutation):
    release = historical_release
    assert _review(release, "quadratic-reciprocity", historical_family=True)

    def change(manifest):
        families = manifest["families"]
        if mutation == "descriptor":
            families[0]["first_admission"]["policy"] = "infer_current_version"
        elif mutation == "missing":
            families.pop()
        elif mutation == "duplicate":
            families[-1] = deepcopy(families[0])
        elif mutation == "foreign":
            families[-1]["slug"] = "invented-family"
        else:
            manifest["first_enrollment_catalog_sha256"] = release.digest

    _mutate_json(release.historical_manifest, change)
    assert not _review(release, "quadratic-reciprocity", historical_family=True)


@pytest.mark.parametrize("mutation", ("same_size_mtime", "missing", "extra_bytes", "leaf_symlink", "api_symlink", "family_symlink", "wrong_owner"))
def test_literal_first_admission_sidecars_are_rechecked_even_on_warm_family_cache(historical_release, monkeypatch, mutation):
    release = historical_release
    assert _review(release, "quadratic-reciprocity", historical_family=True)
    path = release.historical_directory / "gaussian-factorization/api/first-admission.json"
    before = path.stat()
    if mutation == "same_size_mtime":
        raw = path.read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
        os.utime(path, ns=(before.st_atime_ns, before.st_mtime_ns))
    elif mutation == "missing":
        path.unlink()
    elif mutation == "extra_bytes":
        path.write_bytes(path.read_bytes() + b" ")
    elif mutation.endswith("symlink"):
        target = path if mutation == "leaf_symlink" else path.parent if mutation == "api_symlink" else path.parent.parent
        moved = release.root / "owned-moved-sidecar-component"
        target.rename(moved)
        target.symlink_to(moved, target_is_directory=mutation != "leaf_symlink")
    else:
        actual_stat = Path.stat

        def wrong_owner(candidate, *args, **kwargs):
            value = actual_stat(candidate, *args, **kwargs)
            if candidate == path:
                fields = list(value)
                fields[4] = value.st_uid + 1
                return os.stat_result(fields)
            return value

        monkeypatch.setattr(Path, "stat", wrong_owner)
    # Corrupting an unrelated family's literal sidecar invalidates the whole
    # aggregate, not merely requests for that one family.
    assert not _review(release, "quadratic-reciprocity", historical_family=True)


@pytest.mark.parametrize("segment", (COMPLETED, HISTORICAL))
def test_actual_current_v31_publications_and_principal_panels_pass_read_only_service_review(segment):
    # The original first-v31 snapshots remain literal historical inputs.  The
    # live selector follows their independently published current-v33 copies.
    original_directory = ROOT / "book/_static" / segment
    original_manifest_bytes = (original_directory / "manifest.json").read_bytes()
    original_manifest = json.loads(original_manifest_bytes)
    directory = ROOT / "book/_static" / segment.replace("-v31", "-v33")
    manifest_path = directory / "manifest.json"
    assert manifest_path.is_file(), "requires the genuine freshly verified v33 publication, never a fixture receipt"
    raw_manifest = manifest_path.read_bytes()
    manifest = json.loads(raw_manifest)
    server = non_listening_review_server(ROOT)
    assert server._current_constructive_release(directory.parent, owner=os.getuid())[0] == "v33"
    assert manifest["alpha_edition_version"] == "v33" and original_manifest["alpha_edition_version"] == "v31"
    expected = set(EXPECTED_COMPLETED) if segment == COMPLETED else EXPECTED_HISTORICAL
    assert {row["slug"] for row in manifest["families"]} == expected
    assert len(manifest["families"]) == len(expected)
    if segment == COMPLETED:
        assert manifest["alpha_first_enrolled_version"] == "v31"
        assert manifest["theorem_count"] == manifest["checked_use_count"] == 574
        assert original_manifest["first_enrollment_catalog_sha256"] == original_manifest["catalog_sha256"]
        assert "first_enrollment_catalog_sha256" not in manifest
    else:
        assert manifest["alpha_first_enrolled_version"] == "mixed_preserved"
        assert "first_enrollment_catalog_sha256" not in manifest
    handler = object.__new__(service.LeanStrandHandler)
    handler.server = server
    for family in manifest["families"]:
        slug = family["slug"]
        assert server.reviewed_constructive_family(directory, slug), slug
        suffixes = {"explorer/defined/graph.html"}
        if segment == COMPLETED:
            tags = family["root_tags"].values()
        else:
            descriptor = family["first_admission"]
            path = directory / descriptor["per_theorem_records"]["path"]
            sidecar = json.loads(path.read_bytes())
            tags = [row["tag"] for row in sidecar["per_theorem"]
                    if row["recorded_authority"].get("alpha_checked_use") is True][:1]
        for tag in tags:
            suffixes.update((f"explorer/tag/{tag}.html", f"explorer/defined/tag/{tag}.html"))
        for suffix in suffixes:
            path = directory / slug / suffix
            original = path.read_bytes()
            enhanced = handler._inject_selector(path, path.relative_to(ROOT).parts)
            assert enhanced is not None and b"lean-selector.js" in enhanced, str(path)
            assert b"lean-selector.css" in enhanced and path.read_bytes() == original
    assert manifest_path.read_bytes() == raw_manifest
    assert (original_directory / "manifest.json").read_bytes() == original_manifest_bytes
    assert not server.reviewed_constructive_family(original_directory, next(iter(expected)))


def test_actual_current_v31_uses_three_unchanged_bound_documents_and_preserves_old_catalog():
    alpha = ROOT / "artifacts/peano-library/alpha"
    manifest_path = alpha / "catalog-v31.json"
    assert manifest_path.is_file(), "the fresh v31 release must exist before this actual-output check"
    channels = json.loads((ROOT / "artifacts/peano-library/channels-v31.json").read_bytes())
    expected = channels["channels"]["alpha"]["artifact_sha256"]
    bindings = codec.verify_catalog_bindings(manifest_path, expected_sha256=expected)
    assert tuple(row.role for row in bindings.files) == ("manifest", "parent", "delta")
    assert bindings.parent.bytes == 66_503_303 and bindings.parent.sha256 == PARENT_SHA
    assert bindings.parent.row_count == 3222 and bindings.delta.row_count == 574
    assert all(0 < row.bytes <= 64 * 1024 * 1024 for row in bindings.files)
    # The exact historical three-file check above still runs.  Only current
    # discovery moves to the separately sealed v33 manifest/base/delta set.
    import peano_catalog_shards_v33 as current_codec
    current_channels = json.loads((ROOT / "artifacts/peano-library/channels-v33.json").read_bytes())
    current_digest = current_channels["channels"]["alpha"]["artifact_sha256"]
    current = current_codec.verify_catalog_bindings(alpha / "catalog-v33.json", expected_sha256=current_digest)
    assert tuple(row.role for row in current.files) == ("manifest", "parent", "delta")
    assert current.parent.bytes == bindings.parent.bytes and current.parent.sha256 == PARENT_SHA
    assert current.parent.row_count == 3222 and current.delta.row_count == 870
    assert all(0 < row.bytes <= 64 * 1024 * 1024 for row in current.files)
    server = non_listening_review_server(ROOT)
    assert server._current_constructive_release(ROOT / "book/_static", owner=os.getuid()) == (
        "v33", current_digest, current_channels["channels"]["alpha"]["edition_identity_sha256"])
    for segment, slug in (("constructive-gaussian-factorization-explorer", "gaussian-factorization"),
                          ("constructive-priority-layer-explorer-v30", "best-approximation")):
        assert not server.reviewed_constructive_family(ROOT / "book/_static" / segment, slug)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Original-bounded read-only v31 service regressions; no proof workers.")
    parser.add_argument("--pytest-select", default="")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    status = pytest.main(["-q", "--tb=short", "-x", __file__, "-k", args.pytest_select])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    print(json.dumps({"status": int(status), "seconds": time.monotonic() - started,
                      "peak_rss_bytes": peak, "rss_limit_passed": peak <= RSS_LIMIT,
                      "proof_workers_started": False}), flush=True)
    assert peak <= RSS_LIMIT
    raise SystemExit(status)
